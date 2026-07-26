"""Gate single-owner LPS3 transform packets on pinned real music."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    decode_lapped_chained_packet_view,
    encode_lapped_chained_packet_stream,
    encode_lapped_transform_packet_stream,
    index_lapped_packet_stream,
)
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
            / "lapped_chained_packet"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0 or args.packet_seconds <= 0.0:
        raise ValueError("chained-packet timing bounds must be positive")

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
        independent = encode_lapped_transform_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
        )
        chained = encode_lapped_chained_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
        )
        info = index_lapped_packet_stream(chained.payload)
        lost_packet = min(
            len(info.packets) - 2,
            max(1, len(info.packets) // 3),
        )
        recovery_packet = lost_packet + 1
        recovery = decode_lapped_chained_packet_view(
            info,
            recovery_packet,
        )
        recovery_record = info.packets[recovery_packet]
        recovery_exact = bool(
            np.array_equal(
                recovery,
                chained.reconstruction[
                    recovery_record.logical_start : (
                        recovery_record.logical_start
                        + recovery_record.logical_count
                    )
                ],
            )
        )
        overhead = chained.report["packet_byte_overhead_fraction"]
        gate_passed = bool(
            chained.report["exact_monolithic_reconstruction"]
            and recovery_exact
            and overhead <= 0.04
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
            "packet_count": len(info.packets),
            "monolithic_stream_bytes": (
                chained.report["monolithic_stream_bytes"]
            ),
            "independent_transform_packet_bytes": len(independent.payload),
            "independent_transform_overhead_fraction": (
                independent.report["packet_byte_overhead_fraction"]
            ),
            "single_owner_packet_bytes": len(chained.payload),
            "single_owner_overhead_fraction": overhead,
            "exact_monolithic_reconstruction": (
                chained.report["exact_monolithic_reconstruction"]
            ),
            "simulated_lost_packet": lost_packet,
            "first_later_packet": recovery_packet,
            "first_later_packet_exact_without_lost_packet": recovery_exact,
            "maximum_loss_extension_frames": args.half_window,
            "gate_passed": gate_passed,
        }

    gate_passed = passing_clips == len(reports)
    report = {
        "status": (
            "LPS3 single-owner packet gate passed"
            if gate_passed
            else "LPS3 single-owner packet gate failed"
        ),
        "research_only": True,
        "gate_rule": (
            "exact monolithic reconstruction, exact first packet after a "
            "simulated missing packet, and no more than 4% complete-byte "
            "overhead on every clip"
        ),
        "loss_scope": (
            "a missing packet can additionally withhold only the preceding "
            "half-window that awaited its first transform frame"
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
        raise SystemExit("LPS3 single-owner packet gate failed")


if __name__ == "__main__":
    main()
