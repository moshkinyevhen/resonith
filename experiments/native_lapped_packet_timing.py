"""Gate release native LPS1 pull decode on the pinned real-music corpus."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import time

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    decode_lapped_packet_stream,
    encode_lapped_packet_stream,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from packet_loss_benchmark import (  # noqa: E402
    pcm_sha256,
    read_bounded_pcm16,
)
from real_music_benchmark import fetch_source  # noqa: E402


SELECTED_AVERAGE_BUDGETS = {
    "corelli-sonata-realization": 61,
    "emotional-piano-cc0": 66,
    "patro-de-bateria": 46,
}


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
        "--native-library",
        type=Path,
        default=(
            Path(os.environ["RESONITH_NATIVE_CORE"])
            if "RESONITH_NATIVE_CORE" in os.environ
            else None
        ),
    )
    parser.add_argument("--maximum-seconds", type=float, default=3.0)
    parser.add_argument("--packet-seconds", type=float, default=1.0)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument("--minimum-realtime-speed", type=float, default=4.0)
    parser.add_argument(
        "--maximum-workspace-bytes",
        type=int,
        default=2 * 1024 * 1024,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_native_packet_timing"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.native_library is None:
        raise ValueError(
            "provide --native-library or set RESONITH_NATIVE_CORE"
        )
    if (
        args.maximum_seconds <= 0.0
        or args.packet_seconds <= 0.0
        or args.iterations <= 0
        or args.warmups < 0
        or args.minimum_realtime_speed <= 0.0
        or args.maximum_workspace_bytes <= 0
    ):
        raise ValueError("native packet timing bounds are invalid")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    decoder = NativeMain0Decoder(
        args.native_library,
        max_workspace_bytes=args.maximum_workspace_bytes,
    )
    reports = {}
    passing_clips = 0
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + frame_count].copy()
        duration_seconds = samples.shape[0] / sample_rate
        packet_frames = max(
            args.half_window,
            int(args.packet_seconds * sample_rate)
            // args.half_window
            * args.half_window,
        )
        budget = SELECTED_AVERAGE_BUDGETS.get(record["id"], 64)
        encoded = encode_lapped_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
            density_backend="adaptive",
        )
        python = decode_lapped_packet_stream(encoded.payload)
        native = decoder.decode_lapped_packets(encoded.payload)
        np.testing.assert_array_equal(native.samples, python.samples)

        for _ in range(args.warmups):
            decoder.decode_lapped_packets(encoded.payload)
        durations = []
        for _ in range(args.iterations):
            started = time.perf_counter()
            repeated = decoder.decode_lapped_packets(encoded.payload)
            durations.append(time.perf_counter() - started)
            np.testing.assert_array_equal(repeated.samples, native.samples)

        median_seconds = statistics.median(durations)
        realtime_speed = duration_seconds / median_seconds
        gate_passed = (
            realtime_speed >= args.minimum_realtime_speed
            and native.workspace_bytes <= args.maximum_workspace_bytes
        )
        passing_clips += int(gate_passed)
        reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "duration_seconds": duration_seconds,
            "source_pcm16_sha256": pcm_sha256(samples),
            "decoded_pcm16_sha256": pcm_sha256(native.samples),
            "average_coefficients": budget,
            "packet_frames": native.packet_frames,
            "packet_count": native.packet_count,
            "stream_bytes": len(encoded.payload),
            "workspace_bytes": native.workspace_bytes,
            "decode_wall_seconds_min": min(durations),
            "decode_wall_seconds_median": median_seconds,
            "decode_wall_seconds_max": max(durations),
            "decode_realtime_factor_median": (
                median_seconds / duration_seconds
            ),
            "decode_realtime_speed_median": realtime_speed,
            "exact_python_native_pcm": True,
            "gate_passed": gate_passed,
            "timing_scope": (
                "ctypes call plus complete-sequence preflight, per-packet "
                "authentication and child inspection, caller-array "
                "allocation, entropy decode, synthesis, context trim, "
                "interleave, and NumPy copy"
            ),
        }

    gate_passed = passing_clips == len(reports)
    report = {
        "status": (
            "native packet resource gate passed"
            if gate_passed
            else "native packet resource gate failed"
        ),
        "platform": {
            "sys_platform": sys.platform,
            "python": sys.version,
            "machine": os.environ.get("RUNNER_ARCH", "unknown"),
        },
        "native_library": str(args.native_library),
        "iterations": args.iterations,
        "warmups": args.warmups,
        "gate": {
            "minimum_realtime_speed": args.minimum_realtime_speed,
            "maximum_workspace_bytes": args.maximum_workspace_bytes,
            "exact_python_native_pcm": True,
            "passing_clips": passing_clips,
            "clip_count": len(reports),
        },
        "clips": reports,
        "measurement_limit": (
            "hosted x64 wall time and caller-owned storage only; physical "
            "device energy, thermal behavior, and transport I/O are pending"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not gate_passed:
        raise SystemExit("native packet resource gate failed")


if __name__ == "__main__":
    main()
