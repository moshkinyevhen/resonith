"""Run the R-095 bounded adaptive entropy oracle on licensed music."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.finite_state_oracle import (  # noqa: E402
    decode_finite_state_lapped,
    encode_finite_state_lapped,
)
from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
    pack_lapped_selected_payload,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402
from temporal_support_oracle_benchmark import R084_BUDGETS  # noqa: E402


def _flatten_selected(
    coefficients: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = np.count_nonzero(coefficients, axis=2).astype(np.uint16)
    position_parts: list[np.ndarray] = []
    value_parts: list[np.ndarray] = []
    for channel in range(coefficients.shape[0]):
        for frame in range(coefficients.shape[1]):
            positions = np.flatnonzero(
                coefficients[channel, frame]
            ).astype(np.uint16)
            position_parts.append(positions)
            value_parts.append(
                coefficients[channel, frame, positions].astype(np.int8)
            )
    return counts, np.concatenate(position_parts), np.concatenate(value_parts)


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
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "finite_state_oracle",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)

    clips: dict[str, dict] = {}
    reductions: list[float] = []
    every_clip_won = True
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        sample_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + sample_count].copy()
        analysis = analyze_lapped_source(
            samples,
            sample_rate,
            half_window=512,
            band_count=24,
            transform_backend="fixed",
        )
        selected = encode_lapped_analysis(
            analysis,
            coefficients_per_frame=R084_BUDGETS[record["id"]],
            entropy_backend="bounded",
            density_backend="adaptive",
        )
        counts, positions, values = _flatten_selected(
            selected.selected_coefficients
        )
        baseline_entropy = pack_lapped_selected_payload(
            selected.selected_scales,
            selected.selected_coefficients,
            half_window=512,
        )
        adaptive_entropy = encode_finite_state_lapped(
            selected.selected_scales,
            counts,
            positions,
            values,
            half_window=512,
        )
        decoded = decode_finite_state_lapped(
            adaptive_entropy,
            half_window=512,
            expected_channels=samples.shape[1],
            expected_frames=analysis.frame_count,
            expected_bands=24,
        )
        np.testing.assert_array_equal(decoded.scales, selected.selected_scales)
        np.testing.assert_array_equal(decoded.counts, counts)
        np.testing.assert_array_equal(decoded.positions, positions)
        np.testing.assert_array_equal(decoded.values, values)

        baseline_complete = len(selected.payload)
        adaptive_complete = (
            baseline_complete - len(baseline_entropy) + len(adaptive_entropy)
        )
        reduction = 1.0 - adaptive_complete / baseline_complete
        reductions.append(reduction)
        every_clip_won = every_clip_won and adaptive_complete < baseline_complete
        clips[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "r084_coefficients_per_frame": R084_BUDGETS[record["id"]],
            "baseline_entropy_bytes": len(baseline_entropy),
            "adaptive_entropy_bytes": len(adaptive_entropy),
            "baseline_complete_stream_bytes": baseline_complete,
            "adaptive_complete_stream_bytes": adaptive_complete,
            "complete_byte_reduction": reduction,
            "selected_gap_threshold": decoded.gap_threshold,
            "reconstruction_is_identical": True,
        }

    mean_reduction = float(np.mean(reductions))
    gate_passed = every_clip_won and all(item >= 0.05 for item in reductions)
    report = {
        "status": (
            "compression gate passed; native finite-state work is justified"
            if gate_passed
            else "compression gate failed; finite-state syntax is closed"
        ),
        "research_only": True,
        "gate_rule": (
            "complete bytes must decrease by at least 5% on every R-084 clip"
        ),
        "gate_passed": gate_passed,
        "every_clip_won": every_clip_won,
        "mean_complete_byte_reduction": mean_reduction,
        "identical_reconstruction": True,
        "maximum_seconds_per_clip": args.maximum_seconds,
        "clips": clips,
    }
    report_path = args.output_directory / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
