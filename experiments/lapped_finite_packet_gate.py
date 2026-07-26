"""Run the R-097 independently reset LPS5 transport gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_compact_packet_stream,
    encode_lapped_finite_packet_stream,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402
from temporal_support_oracle_benchmark import R084_BUDGETS  # noqa: E402


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
    parser.add_argument("--maximum-seconds", type=float, default=3.0)
    parser.add_argument("--packet-frames", type=int, default=12288)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "lapped_finite_packet_gate",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)

    clips: dict[str, dict] = {}
    reductions: list[float] = []
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        sample_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + sample_count].copy()
        common = {
            "coefficients_per_frame": R084_BUDGETS[record["id"]],
            "packet_frames": args.packet_frames,
            "half_window": 512,
            "band_count": 24,
        }
        baseline = encode_lapped_compact_packet_stream(
            samples,
            sample_rate,
            **common,
        )
        finite = encode_lapped_finite_packet_stream(
            samples,
            sample_rate,
            **common,
        )
        np.testing.assert_array_equal(
            finite.reconstruction,
            baseline.reconstruction,
        )
        reduction = 1.0 - len(finite.payload) / len(baseline.payload)
        reductions.append(reduction)
        clips[record["id"]] = {
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "lps4_bytes": len(baseline.payload),
            "lps5_bytes": len(finite.payload),
            "complete_byte_reduction": reduction,
            "packet_count": finite.report["packet_count"],
            "packet_duration_milliseconds": (
                1000.0 * args.packet_frames / sample_rate
            ),
            "exact_reconstruction": True,
        }
    gate_passed = all(reduction >= 0.03 for reduction in reductions)
    report = {
        "status": (
            "transport gate passed; prospective LPS5 is justified"
            if gate_passed
            else "transport gate failed; prospective LPS5 is closed"
        ),
        "research_only": True,
        "gate_rule": (
            "LPS5 must reduce complete bytes by at least 3% on every R-084 "
            "clip at no more than 278.6 ms nominal record duration"
        ),
        "gate_passed": gate_passed,
        "mean_complete_byte_reduction": float(np.mean(reductions)),
        "maximum_seconds_per_clip": args.maximum_seconds,
        "packet_frames": args.packet_frames,
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
