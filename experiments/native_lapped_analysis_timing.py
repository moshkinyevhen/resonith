"""Measure native LPF1 forward analysis against the Python fixed oracle."""

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

from maf_p0.lapped_oracle import analyze_lapped_source  # noqa: E402
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


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
    parser.add_argument("--native-iterations", type=int, default=10)
    parser.add_argument("--python-iterations", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_native_analysis_timing"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.native_library is None:
        raise ValueError(
            "provide --native-library or set RESONITH_NATIVE_CORE"
        )
    if (
        args.native_iterations <= 0
        or args.python_iterations <= 0
        or args.warmups < 0
    ):
        raise ValueError("timing iteration counts are invalid")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    core = NativeMain0Decoder(args.native_library)
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

        python_durations = []
        reference = None
        for _ in range(args.python_iterations):
            started = time.perf_counter()
            reference = analyze_lapped_source(
                samples,
                sample_rate,
                half_window=args.half_window,
                band_count=args.band_count,
                transform_backend="fixed",
            )
            python_durations.append(time.perf_counter() - started)
        assert reference is not None
        for _ in range(args.warmups):
            core.analyze_lapped(
                samples,
                half_window=args.half_window,
                band_count=args.band_count,
            )
        native_durations = []
        native = None
        for _ in range(args.native_iterations):
            started = time.perf_counter()
            native = core.analyze_lapped(
                samples,
                half_window=args.half_window,
                band_count=args.band_count,
            )
            native_durations.append(time.perf_counter() - started)
        assert native is not None
        np.testing.assert_array_equal(native.scales, reference.scales)
        np.testing.assert_array_equal(
            native.quantized_grid,
            reference.quantized_grid,
        )
        np.testing.assert_array_equal(
            native.score_grid,
            reference.score_grid.astype(np.uint64),
        )
        python_median = statistics.median(python_durations)
        native_median = statistics.median(native_durations)
        reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "duration_seconds": duration_seconds,
            "transform_frame_count": native.transform_frame_count,
            "exact_array_parity": True,
            "analysis_output_bytes": (
                native.scales.nbytes
                + native.quantized_grid.nbytes
                + native.score_grid.nbytes
            ),
            "python_wall_seconds_median": python_median,
            "native_wall_seconds_min": min(native_durations),
            "native_wall_seconds_median": native_median,
            "native_wall_seconds_max": max(native_durations),
            "native_realtime_factor_median": (
                native_median / duration_seconds
            ),
            "speedup_vs_python_median": python_median / native_median,
            "timing_scope": (
                "ctypes call, caller-array allocation, scalar forward "
                "transform, quantization, score generation, and NumPy reshape"
            ),
        }
    report = {
        "status": "native scalar forward-analysis timing complete",
        "research_only": True,
        "platform": {
            "sys_platform": sys.platform,
            "python": sys.version,
            "machine": os.environ.get("RUNNER_ARCH", "unknown"),
        },
        "native_library": str(args.native_library),
        "native_iterations": args.native_iterations,
        "python_iterations": args.python_iterations,
        "warmups": args.warmups,
        "half_window": args.half_window,
        "band_count": args.band_count,
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
