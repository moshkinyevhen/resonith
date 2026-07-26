"""Measure exact-byte frontier search with and without shared analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
    encode_lapped_stream,
)
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
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=(16, 24, 32, 48, 64, 96),
    )
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_frontier_timing"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0 or args.iterations <= 0:
        raise ValueError("timing bounds must be positive")
    budgets = tuple(sorted(set(args.budgets)))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clips = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[start : start + frame_count].copy()
        direct_times = []
        reused_times = []
        analysis_times = []
        for _iteration in range(args.iterations):
            started = time.perf_counter()
            direct = [
                encode_lapped_stream(
                    samples,
                    sample_rate,
                    coefficients_per_frame=budget,
                    entropy_backend="bounded",
                    transform_backend="fixed",
                    density_backend="adaptive",
                )
                for budget in budgets
            ]
            direct_times.append(time.perf_counter() - started)

            analysis_started = time.perf_counter()
            analysis = analyze_lapped_source(
                samples,
                sample_rate,
                transform_backend="fixed",
            )
            analysis_times.append(time.perf_counter() - analysis_started)
            reused = [
                encode_lapped_analysis(
                    analysis,
                    coefficients_per_frame=budget,
                    entropy_backend="bounded",
                    density_backend="adaptive",
                )
                for budget in budgets
            ]
            reused_times.append(
                time.perf_counter() - analysis_started
            )
            if [item.payload for item in direct] != [
                item.payload for item in reused
            ]:
                raise RuntimeError("shared analysis changed an exact stream")
        direct_median = statistics.median(direct_times)
        reused_median = statistics.median(reused_times)
        clips[record["id"]] = {
            "conversion": conversion,
            "frame_count": int(samples.shape[0]),
            "sample_rate": sample_rate,
            "direct_frontier_seconds_median": direct_median,
            "shared_analysis_seconds_median": statistics.median(
                analysis_times
            ),
            "shared_frontier_seconds_median": reused_median,
            "speedup": direct_median / reused_median,
            "exact_stream_parity": True,
        }
    report = {
        "status": "shared transform-analysis timing complete",
        "research_only": True,
        "platform": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "iterations": args.iterations,
        "budgets": budgets,
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
