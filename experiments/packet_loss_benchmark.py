"""Run the R-054 aligned block-loss containment test on pinned music."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import wave

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.multichannel import encode_main0_independent_rdo  # noqa: E402
from maf_p0.packet_loss import simulate_aligned_packet_loss  # noqa: E402
from maf_p0.wav_io import write_pcm16_channels  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


def _read_bounded_pcm16(path: Path) -> tuple[int, np.ndarray, dict]:
    """Convert little-endian integer PCM WAV to frame-major PCM16."""

    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        sample_rate = source.getframerate()
        frame_count = source.getnframes()
        compression = source.getcomptype()
        data = source.readframes(frame_count)
    if not 1 <= channels <= 8 or compression != "NONE":
        raise ValueError("packet-loss corpus requires 1-8 channel PCM WAV")
    if width == 2:
        samples = np.frombuffer(data, dtype="<i2").astype(
            np.int16,
            copy=True,
        )
        conversion = "pcm16-identity"
    elif width == 3:
        octets = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3)
        values = (
            octets[:, 0].astype(np.int32)
            | (octets[:, 1].astype(np.int32) << 8)
            | (octets[:, 2].astype(np.int32) << 16)
        )
        values = np.where(values & 0x0080_0000, values - 0x0100_0000, values)
        samples = np.right_shift(values, 8).astype(np.int16)
        conversion = "pcm24-drop-low-8"
    elif width == 4:
        values = np.frombuffer(data, dtype="<i4").astype(np.int64)
        samples = np.right_shift(values, 16).astype(np.int16)
        conversion = "pcm32-drop-low-16"
    else:
        raise ValueError("packet-loss corpus requires 16/24/32-bit PCM")
    if samples.size != frame_count * channels:
        raise ValueError("truncated packet-loss corpus WAV")
    return (
        sample_rate,
        samples.reshape(frame_count, channels),
        {
            "source_sample_width_bytes": width,
            "conversion": conversion,
        },
    )


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()


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
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument("--innovation-step", type=int, default=64)
    parser.add_argument(
        "--residual-blocks",
        type=int,
        nargs="+",
        default=(1024, 2048, 4096),
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "packet_loss",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)

    clips: dict[str, dict] = {}
    all_contained = True
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = _read_bounded_pcm16(
            source_path
        )
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        crop_frames = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + crop_frames].copy()
        started = time.perf_counter()
        encoded = encode_main0_independent_rdo(
            samples,
            sample_rate,
            innovation_step=args.innovation_step,
            residual_block_sizes=tuple(args.residual_blocks),
        )
        block_count = int(
            np.ceil(
                samples.shape[0]
                / encoded.report["residual_block_size"]
            )
        )
        lost_block = min(
            block_count - 2,
            max(1, block_count // 3),
        )
        simulation = simulate_aligned_packet_loss(
            encoded.payload,
            lost_blocks=(lost_block,),
        )
        elapsed = time.perf_counter() - started
        contained = bool(
            simulation.report["exact_outside_loss"]
            and simulation.report["all_recoverable_next_blocks_exact"]
        )
        all_contained &= contained

        clip_directory = args.output_directory / record["id"]
        clip_directory.mkdir(parents=True, exist_ok=True)
        write_pcm16_channels(
            clip_directory / "concealed.wav",
            sample_rate,
            simulation.reconstruction,
        )
        clips[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "pcm16_sha256": _pcm_sha256(samples),
            "stream_bytes": len(encoded.payload),
            "stream_sha256": encoded.report["stream_sha256"],
            "residual_block_size": encoded.report["residual_block_size"],
            "lost_block": lost_block,
            "lost_interval_milliseconds": (
                simulation.report["affected_frames"] * 1000.0 / sample_rate
            ),
            "encode_and_simulate_wall_seconds": elapsed,
            "containment_passed": contained,
            "simulation": simulation.report,
        }

    report = {
        "status": (
            "block-local packet-loss containment passed"
            if all_contained
            else "block-local packet-loss containment failed"
        ),
        "research_only": True,
        "all_clips_contained": all_contained,
        "clip_count": len(clips),
        "maximum_seconds_per_clip": args.maximum_seconds,
        "innovation_step": args.innovation_step,
        "residual_block_candidates": list(args.residual_blocks),
        "clips": clips,
    }
    (args.output_directory / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
