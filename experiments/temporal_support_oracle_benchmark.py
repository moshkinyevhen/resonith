"""Run the R-091 temporal support-state oracle on licensed music."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
    pack_lapped_selected_payload,
)
from maf_p0.temporal_support_oracle import (  # noqa: E402
    decode_temporal_support_lapped,
    encode_temporal_support_lapped,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


R084_BUDGETS = {
    "corelli-sonata-realization": 54,
    "emotional-piano-cc0": 68,
    "patro-de-bateria": 44,
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
    parser.add_argument("--maximum-seconds", type=float, default=3.0)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "temporal_support_oracle",
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
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + frame_count].copy()
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
        baseline_entropy = pack_lapped_selected_payload(
            selected.selected_scales,
            selected.selected_coefficients,
            half_window=512,
        )
        temporal_entropy = encode_temporal_support_lapped(
            selected.selected_scales,
            selected.selected_coefficients,
            half_window=512,
        )
        decoded = decode_temporal_support_lapped(
            temporal_entropy,
            half_window=512,
            expected_channels=samples.shape[1],
            expected_frames=analysis.frame_count,
            expected_bands=24,
        )
        np.testing.assert_array_equal(
            decoded.scales,
            selected.selected_scales,
        )
        np.testing.assert_array_equal(
            decoded.coefficients,
            selected.selected_coefficients,
        )

        baseline_complete = len(selected.payload)
        temporal_complete = (
            baseline_complete - len(baseline_entropy) + len(temporal_entropy)
        )
        reduction = 1.0 - temporal_complete / baseline_complete
        reductions.append(reduction)
        every_clip_won = every_clip_won and temporal_complete < baseline_complete
        clips[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "r084_coefficients_per_frame": R084_BUDGETS[record["id"]],
            "baseline_entropy_bytes": len(baseline_entropy),
            "temporal_entropy_bytes": len(temporal_entropy),
            "baseline_complete_stream_bytes": baseline_complete,
            "temporal_complete_stream_bytes": temporal_complete,
            "complete_byte_reduction": reduction,
            "reconstruction_is_identical": True,
        }

    mean_reduction = float(np.mean(reductions))
    gate_passed = every_clip_won and mean_reduction >= 0.05
    report = {
        "status": (
            "compression gate passed; temporal support syntax is eligible"
            if gate_passed
            else "compression gate failed; temporal support syntax is closed"
        ),
        "research_only": True,
        "gate_rule": (
            "complete bytes must decrease on all three R-084 clips and the "
            "arithmetic-mean reduction must be at least 5%"
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
