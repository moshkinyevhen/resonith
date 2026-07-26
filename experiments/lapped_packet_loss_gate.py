"""Prove exact LPS1 Truth recovery after one missing transport packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_packet_stream,
    encode_lapped_transform_packet_stream,
)
from maf_p0.packet_loss import simulate_lapped_packet_loss  # noqa: E402
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
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
    parser.add_argument("--maximum-seconds", type=float, default=3.0)
    parser.add_argument("--packet-seconds", type=float, default=0.25)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_packet_loss"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0 or args.packet_seconds <= 0.0:
        raise ValueError("packet-loss timing bounds must be positive")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
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
        packet_frames = max(
            args.half_window,
            int(args.packet_seconds * sample_rate)
            // args.half_window
            * args.half_window,
        )
        budget = SELECTED_AVERAGE_BUDGETS.get(record["id"], 64)
        monolithic = encode_lapped_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            half_window=args.half_window,
            band_count=args.band_count,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="adaptive",
        )
        contextual = encode_lapped_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
            density_backend="adaptive",
        )
        packeted = encode_lapped_transform_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
        )
        packet_count = int(packeted.report["packet_count"])
        lost_packet = min(packet_count - 2, max(1, packet_count // 3))
        simulation = simulate_lapped_packet_loss(
            packeted.payload,
            lost_packets=(lost_packet,),
        )
        gate_passed = bool(
            simulation.report["exact_outside_loss"]
            and simulation.report["all_recoverable_next_packets_exact"]
            and not simulation.report["truth_reference_uses_concealment"]
            and packeted.report["exact_monolithic_reconstruction"]
            and packeted.report["packet_byte_overhead_fraction"] <= 0.10
        )
        passing_clips += int(gate_passed)
        reports[record["id"]] = {
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "average_coefficients": budget,
            "packet_frames": packet_frames,
            "packet_interval_milliseconds": (
                packet_frames * 1000.0 / sample_rate
            ),
            "packet_count": packet_count,
            "lost_packet": lost_packet,
            "monolithic_stream_bytes": len(monolithic.payload),
            "source_context_packet_stream_bytes": len(contextual.payload),
            "source_context_packet_byte_overhead_fraction": (
                len(contextual.payload) / len(monolithic.payload) - 1.0
            ),
            "transform_packet_stream_bytes": len(packeted.payload),
            "transform_packet_byte_overhead_fraction": (
                packeted.report["packet_byte_overhead_fraction"]
            ),
            "exact_monolithic_reconstruction": (
                packeted.report["exact_monolithic_reconstruction"]
            ),
            "containment_gate_passed": gate_passed,
            "simulation": simulation.report,
        }

    gate_passed = passing_clips == len(reports)
    report = {
        "status": (
            "LPS2 transform-packet gate passed"
            if gate_passed
            else "LPS2 transform-packet gate failed"
        ),
        "research_only": True,
        "gate_rule": (
            "every non-lost frame and the first later available packet must "
            "equal uninterrupted Truth exactly; concealment must not enter "
            "Truth reference state; transform-boundary packet reconstruction "
            "must equal monolithic LPF1 exactly and add no more than 10% bytes"
        ),
        "metric_warning": (
            "concealed-interval waveform values are diagnostics, not a "
            "perceptual loss-concealment claim"
        ),
        "passing_clips": passing_clips,
        "clip_count": len(reports),
        "clips": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not gate_passed:
        raise SystemExit("LPS2 transform-packet gate failed")


if __name__ == "__main__":
    main()
