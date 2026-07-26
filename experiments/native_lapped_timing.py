"""Measure release native LPF1 decode on the pinned real-music corpus."""

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

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
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
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_native_timing"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.native_library is None:
        raise ValueError(
            "provide --native-library or set RESONITH_NATIVE_CORE"
        )
    if args.iterations <= 0 or args.warmups < 0:
        raise ValueError("timing iteration counts are invalid")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    decoder = NativeMain0Decoder(args.native_library)
    reports = {}
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
        budget = SELECTED_AVERAGE_BUDGETS.get(record["id"], 64)

        encode_started = time.perf_counter()
        encoded = encode_lapped_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            half_window=args.half_window,
            band_count=args.band_count,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="adaptive",
        )
        encode_seconds = time.perf_counter() - encode_started
        native = decoder.decode_lapped(encoded.payload)
        np.testing.assert_array_equal(
            native.samples,
            encoded.reconstruction,
        )
        for _ in range(args.warmups):
            decoder.decode_lapped(encoded.payload)
        durations = []
        for _ in range(args.iterations):
            started = time.perf_counter()
            repeated = decoder.decode_lapped(encoded.payload)
            durations.append(time.perf_counter() - started)
            np.testing.assert_array_equal(repeated.samples, native.samples)
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
            "selected_count_min": encoded.report["selected_count_min"],
            "selected_count_max": encoded.report["selected_count_max"],
            "stream_bytes": encoded.report["stream_bytes"],
            "workspace_bytes": native.requirements.workspace_bytes,
            "encode_wall_seconds_python_research": encode_seconds,
            "decode_wall_seconds_min": min(durations),
            "decode_wall_seconds_median": statistics.median(durations),
            "decode_wall_seconds_max": max(durations),
            "decode_realtime_factor_median": (
                statistics.median(durations) / duration_seconds
            ),
            "timing_scope": (
                "ctypes call plus caller-array allocation, inspect, verify, "
                "entropy decode, synthesis, interleave, and NumPy copy"
            ),
        }
    report = {
        "status": "native host timing complete; physical devices pending",
        "platform": {
            "sys_platform": sys.platform,
            "python": sys.version,
            "machine": os.environ.get("RUNNER_ARCH", "unknown"),
        },
        "native_library": str(args.native_library),
        "iterations": args.iterations,
        "warmups": args.warmups,
        "clips": reports,
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
