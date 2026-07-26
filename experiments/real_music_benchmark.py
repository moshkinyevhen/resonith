"""Fetch licensed PCM sources and run isolated Resonith/Opus ablations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import wave

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.opus_anchor import run_opus_anchor  # noqa: E402
from maf_p0.stateful import (  # noqa: E402
    decode_stateful_bytes,
    encode_stateful_rdo_samples,
    encode_stateful_samples,
)


USER_AGENT = "ResonithResearch/0.1 (https://github.com/moshkinyevhen/resonith)"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_source(record: dict, cache_directory: Path) -> Path:
    """Fetch one immutable source and reject any provenance drift."""

    cache_directory.mkdir(parents=True, exist_ok=True)
    destination = cache_directory / record["cache_name"]
    if not destination.exists():
        temporary = destination.with_suffix(destination.suffix + ".partial")
        request = urllib.request.Request(
            record["download_url"],
            headers={"User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=120) as source:
            expected_bytes = int(record["bytes"])
            payload = source.read(expected_bytes + 1)
        if len(payload) != expected_bytes:
            raise ValueError(f"download byte count changed: {record['id']}")
        temporary.write_bytes(payload)
        temporary.replace(destination)
    if destination.stat().st_size != int(record["bytes"]):
        raise ValueError(f"source byte count changed: {record['id']}")
    if _sha256(destination) != record["sha256"]:
        raise ValueError(f"source SHA-256 changed: {record['id']}")
    return destination


def _round_divide_signed(values: np.ndarray, denominator: int) -> np.ndarray:
    magnitude = np.abs(values)
    rounded = (magnitude + denominator // 2) // denominator
    return np.where(values < 0, -rounded, rounded)


def read_pcm_as_mono16(path: Path) -> tuple[int, np.ndarray, dict]:
    """Decode bounded 16/24-bit integer WAV and downmix deterministically."""

    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        frame_count = source.getnframes()
        compression = source.getcomptype()
        payload = source.readframes(frame_count)
    if compression != "NONE" or not 1 <= channels <= 8:
        raise ValueError("corpus source must be bounded uncompressed PCM")
    if sample_width == 2:
        interleaved = np.frombuffer(payload, dtype="<i2").astype(np.int64)
    elif sample_width == 3:
        octets = np.frombuffer(payload, dtype=np.uint8).reshape(-1, 3)
        unsigned = (
            octets[:, 0].astype(np.int32)
            | (octets[:, 1].astype(np.int32) << 8)
            | (octets[:, 2].astype(np.int32) << 16)
        )
        interleaved = np.where(
            unsigned & 0x800000,
            unsigned - (1 << 24),
            unsigned,
        ).astype(np.int64)
    else:
        raise ValueError("corpus source must use 16-bit or 24-bit integer PCM")
    if interleaved.size != frame_count * channels:
        raise ValueError("truncated corpus PCM payload")

    channel_matrix = interleaved.reshape(frame_count, channels)
    mono = _round_divide_signed(
        np.sum(channel_matrix, axis=1, dtype=np.int64),
        channels,
    )
    if sample_width == 3:
        mono = _round_divide_signed(mono, 256)
    mono16 = np.clip(mono, -32768, 32767).astype(np.int16)
    return sample_rate, mono16, {
        "source_channels": channels,
        "source_sample_width_bits": sample_width * 8,
        "downmix": "signed nearest, ties away from zero",
    }


def crop_source(
    samples: np.ndarray,
    sample_rate: int,
    record: dict,
) -> np.ndarray:
    start = int(round(float(record["start_seconds"]) * sample_rate))
    count = int(round(float(record["duration_seconds"]) * sample_rate))
    end = min(samples.size, start + count)
    if start < 0 or end <= start:
        raise ValueError(f"invalid corpus crop: {record['id']}")
    return samples[start:end].copy()


def _codec_report(result, sample_rate: int) -> dict:
    decoded = decode_stateful_bytes(result.payload)
    np.testing.assert_array_equal(decoded.samples, result.reconstructed)
    report = dict(result.report)
    report["effective_bitrate_kbps"] = (
        8.0 * len(result.payload) * sample_rate / result.reconstructed.size / 1000.0
    )
    return report


def benchmark_clip(
    samples: np.ndarray,
    sample_rate: int,
    opus_tools: str | None,
) -> dict:
    common = {
        "basis_mode": "raw",
        "basis_length": 256,
        "pitch_knot_samples": 4096,
        "gain_block_size": 1024,
        "basis_correction_step": 1,
        "residual_step": 64,
        "residual_block_size": 1024,
        "transient_mode": "off",
    }
    configurations = {
        "fixed_zlib_q64": {
            "segment_mode": "fixed",
            "segment_samples": sample_rate,
            "residual_codec": "zlib",
        },
        "fixed_liftpack_q64": {
            "segment_mode": "fixed",
            "segment_samples": sample_rate,
            "residual_codec": "liftpack",
        },
        "adaptive_zlib_q64": {
            "segment_mode": "adaptive",
            "segmentation_hop_samples": 1024,
            "minimum_segment_samples": 4096,
            "maximum_segment_samples": 2 * sample_rate,
            "segmentation_change_penalty": 200.0,
            "residual_codec": "zlib",
        },
        "adaptive_liftpack_q64": {
            "segment_mode": "adaptive",
            "segmentation_hop_samples": 1024,
            "minimum_segment_samples": 4096,
            "maximum_segment_samples": 2 * sample_rate,
            "segmentation_change_penalty": 200.0,
            "residual_codec": "liftpack",
        },
    }
    maf = {}
    for name, configuration in configurations.items():
        result = encode_stateful_samples(
            samples,
            sample_rate,
            **common,
            **configuration,
        )
        maf[name] = _codec_report(result, sample_rate)
    rdo = encode_stateful_rdo_samples(
        samples,
        sample_rate,
        fixed_durations_seconds=(0.5, 1.0, 2.0),
        adaptive_change_penalties=(100.0, 200.0, 400.0, 800.0),
        segmentation_hop_samples=1024,
        minimum_segment_samples=4096,
        maximum_segment_samples=2 * sample_rate,
        **common,
        residual_codec="liftpack",
    )
    maf["rdo_liftpack_q64"] = _codec_report(rdo, sample_rate)

    opus = {}
    for bitrate in (48.0, 96.0):
        result = run_opus_anchor(
            samples,
            sample_rate,
            bitrate_kbps=bitrate,
            mode="vbr",
            application="music",
            tools_directory=opus_tools,
        )
        opus[f"{int(bitrate)}k_vbr_music"] = result.report
    return {"maf": maf, "opus": opus}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "real_music_corpus.json",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "real_music_source",
    )
    parser.add_argument("--opus-tools")
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "experiments"
            / "results"
            / "maf_p2_real_music_2026-07-26.json"
        ),
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clips = {}
    for record in manifest["sources"]:
        path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_pcm_as_mono16(path)
        samples = crop_source(full_samples, sample_rate, record)
        pcm_sha256 = hashlib.sha256(
            samples.astype("<i2", copy=False).tobytes()
        ).hexdigest()
        clips[record["id"]] = {
            "provenance": record,
            "sample_rate": sample_rate,
            "sample_count": int(samples.size),
            "duration_seconds": samples.size / sample_rate,
            "mono_pcm_sha256": pcm_sha256,
            "conversion": conversion,
            "results": benchmark_clip(samples, sample_rate, args.opus_tools),
        }
    report = {
        "status": "diagnostic real-music ablation, not a codec victory claim",
        "corpus_schema": manifest["schema"],
        "codec_scope": "mono downmix, waveform SNR; no MUSHRA",
        "clips": clips,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
