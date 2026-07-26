"""Measure six-point RDO with Python versus native analysis/reconstruction."""

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

from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


def _frontier(analysis, budgets, native_decoder=None):
    return [
        encode_lapped_analysis(
            analysis,
            coefficients_per_frame=budget,
            entropy_backend="bounded",
            density_backend="adaptive",
            native_decoder=native_decoder,
        )
        for budget in budgets
    ]


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
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=(16, 24, 32, 48, 64, 96),
    )
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_native_frontier_timing"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.native_library is None:
        raise ValueError(
            "provide --native-library or set RESONITH_NATIVE_CORE"
        )
    if args.maximum_seconds <= 0.0 or args.iterations <= 0:
        raise ValueError("timing bounds must be positive")
    budgets = tuple(sorted(set(args.budgets)))
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
        python_times = []
        native_times = []
        for _iteration in range(args.iterations):
            started = time.perf_counter()
            python_analysis = analyze_lapped_source(
                samples,
                sample_rate,
                transform_backend="fixed",
            )
            python_candidates = _frontier(python_analysis, budgets)
            python_times.append(time.perf_counter() - started)

            started = time.perf_counter()
            native_analysis = analyze_lapped_source(
                samples,
                sample_rate,
                transform_backend="fixed",
                native_analyzer=core,
            )
            native_candidates = _frontier(
                native_analysis,
                budgets,
                native_decoder=core,
            )
            native_times.append(time.perf_counter() - started)
            for python, native in zip(
                python_candidates,
                native_candidates,
                strict=True,
            ):
                if python.payload != native.payload:
                    raise RuntimeError("native RDO changed a candidate stream")
                np.testing.assert_array_equal(
                    python.reconstruction,
                    native.reconstruction,
                )
        python_median = statistics.median(python_times)
        native_median = statistics.median(native_times)
        reports[record["id"]] = {
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "exact_stream_and_pcm_parity": True,
            "python_frontier_seconds_median": python_median,
            "native_frontier_seconds_median": native_median,
            "speedup": python_median / native_median,
        }
    report = {
        "status": "native encoder RDO frontier timing complete",
        "research_only": True,
        "platform": {
            "sys_platform": sys.platform,
            "python": sys.version,
            "machine": os.environ.get("RUNNER_ARCH", "unknown"),
        },
        "native_library": str(args.native_library),
        "iterations": args.iterations,
        "budgets": budgets,
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
