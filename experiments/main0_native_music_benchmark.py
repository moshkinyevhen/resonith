"""Run native-decoder-gated typed Main-0 on pinned licensed music."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from listening_set import create_blinded_listening_set  # noqa: E402
from real_music_benchmark import (  # noqa: E402
    crop_source,
    fetch_source,
    read_pcm_as_mono16,
)
from maf_p0.main0 import encode_main0_state_rdo  # noqa: E402
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.opus_anchor import run_opus_anchor  # noqa: E402
from maf_p0.wav_io import write_pcm16_mono  # noqa: E402


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()


def _effective_bitrate_kbps(
    byte_count: int,
    sample_count: int,
    sample_rate: int,
) -> float:
    return 8.0 * byte_count * sample_rate / sample_count / 1000.0


def benchmark_clip(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder: NativeMain0Decoder,
    opus_tools: str | None,
    output_directory: Path,
) -> tuple[dict, dict[str, Path]]:
    output_directory.mkdir(parents=True, exist_ok=True)
    source_path = output_directory / "source.wav"
    write_pcm16_mono(source_path, sample_rate, samples)

    encode_start = time.perf_counter()
    resonith = encode_main0_state_rdo(
        samples,
        sample_rate,
        native_decoder=native_decoder,
        basis_length=256,
        gain_block_sizes=(4096,),
        innovation_step=64,
        fixed_state_durations_seconds=(0.5, 1.0, 2.0),
        adaptive_change_penalties=(100.0, 400.0, 800.0),
        segmentation_hop_samples=1024,
        minimum_state_samples=4096,
    )
    encode_seconds = time.perf_counter() - encode_start
    decode_start = time.perf_counter()
    native = native_decoder.decode(resonith.payload)
    decode_seconds = time.perf_counter() - decode_start
    np.testing.assert_array_equal(native.samples, resonith.reconstructed)
    stream_decode_seconds = None
    if native.requirements.atom_count == 0:
        stream_decode_start = time.perf_counter()
        streamed = native_decoder.decode_streaming(resonith.payload)
        stream_decode_seconds = time.perf_counter() - stream_decode_start
        np.testing.assert_array_equal(streamed.samples, native.samples)
    resonith_path = output_directory / "resonith-main0-q64.wav"
    write_pcm16_mono(resonith_path, sample_rate, native.samples)
    resonith_report = {
        **resonith.report,
        "effective_bitrate_kbps": _effective_bitrate_kbps(
            len(resonith.payload),
            samples.size,
            sample_rate,
        ),
        "encode_wall_seconds": encode_seconds,
        "native_decode_wall_seconds": decode_seconds,
        "native_stream_decode_wall_seconds": stream_decode_seconds,
        "native_workspace_bytes": native.requirements.workspace_bytes,
        "decoded_pcm_sha256": _pcm_sha256(native.samples),
    }

    opus_reports = {}
    listening_paths = {
        "hidden-reference": source_path,
        "resonith-main0-q64": resonith_path,
    }
    for bitrate in (48.0, 96.0):
        anchor = run_opus_anchor(
            samples,
            sample_rate,
            bitrate_kbps=bitrate,
            mode="vbr",
            application="music",
            tools_directory=opus_tools,
        )
        key = f"opus-{int(bitrate)}k-vbr"
        path = output_directory / f"{key}.wav"
        write_pcm16_mono(path, sample_rate, anchor.reconstructed)
        opus_reports[key] = anchor.report
        listening_paths[key] = path
    return {
        "resonith": resonith_report,
        "opus": opus_reports,
    }, listening_paths


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
    parser.add_argument(
        "--native-core",
        default=os.environ.get("RESONITH_NATIVE_CORE"),
    )
    parser.add_argument("--opus-tools")
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "main0_native_music"
            / "report.json"
        ),
    )
    parser.add_argument(
        "--decoded-directory",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "main0_native_music"
            / "decoded"
        ),
    )
    parser.add_argument(
        "--listening-directory",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "main0_native_music"
            / "listening"
        ),
    )
    args = parser.parse_args()
    if args.native_core is None:
        raise ValueError("--native-core or RESONITH_NATIVE_CORE is required")
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")

    decoder = NativeMain0Decoder(args.native_core)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clip_reports = {}
    listening_inputs: dict[str, dict[str, Path]] = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_pcm_as_mono16(source_path)
        samples = crop_source(full_samples, sample_rate, record)
        maximum_samples = int(round(args.maximum_seconds * sample_rate))
        samples = samples[:maximum_samples].copy()
        results, candidates = benchmark_clip(
            samples,
            sample_rate,
            native_decoder=decoder,
            opus_tools=args.opus_tools,
            output_directory=args.decoded_directory / record["id"],
        )
        clip_reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.size),
            "duration_seconds": samples.size / sample_rate,
            "mono_pcm_sha256": _pcm_sha256(samples),
            "results": results,
        }
        listening_inputs[record["id"]] = candidates

    listening_manifest, _ = create_blinded_listening_set(
        listening_inputs,
        args.listening_directory,
        seed="resonith-main0-20260726",
    )
    report = {
        "status": (
            "diagnostic native typed-stream run; no perceptually matched "
            "codec-victory claim"
        ),
        "corpus_schema": manifest["schema"],
        "codec_scope": (
            "mono bounded crops, q64 waveform metric, explicit native decoder"
        ),
        "maximum_seconds_per_clip": args.maximum_seconds,
        "listening_manifest_schema": listening_manifest["schema"],
        "clips": clip_reports,
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
