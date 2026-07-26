"""Measure bounded independent-context LPF1 packet overhead on real music."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.lapped_streaming import encode_lapped_packet_stream  # noqa: E402
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


SELECTED_AVERAGE_BUDGETS = {
    "corelli-sonata-realization": 61,
    "emotional-piano-cc0": 66,
    "patro-de-bateria": 46,
}


def _boundary_error_ratio_db(
    source: np.ndarray,
    reconstruction: np.ndarray,
    packet_frames: int,
    radius: int,
) -> float | None:
    error = reconstruction.astype(np.float64) - source.astype(np.float64)
    mask = np.zeros(source.shape[0], dtype=np.bool_)
    for boundary in range(packet_frames, source.shape[0], packet_frames):
        mask[max(0, boundary - radius) : boundary + radius] = True
    if not np.any(mask) or np.all(mask):
        return None
    boundary_mse = float(np.mean(np.square(error[mask])))
    interior_mse = float(np.mean(np.square(error[~mask])))
    return 10.0 * np.log10(
        max(boundary_mse, 1e-30) / max(interior_mse, 1e-30)
    )


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
    parser.add_argument("--packet-seconds", type=float, default=1.0)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_streaming_gate"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0 or args.packet_seconds <= 0.0:
        raise ValueError("streaming timing bounds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    reports = {}
    passes = 0
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
        packeted = encode_lapped_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
            density_backend="adaptive",
        )
        byte_overhead = (
            packeted.report["stream_bytes"]
            / monolithic.report["stream_bytes"]
            - 1.0
        )
        snr_delta = (
            packeted.report["snr_db"] - monolithic.report["snr_db"]
        )
        gate_passed = byte_overhead <= 0.08 and snr_delta >= -0.5
        passes += int(gate_passed)
        reports[record["id"]] = {
            "conversion": conversion,
            "frame_count": int(samples.shape[0]),
            "sample_rate": sample_rate,
            "average_coefficients": budget,
            "packet_frames": packet_frames,
            "packet_count": packeted.report["packet_count"],
            "monolithic_stream_bytes": monolithic.report["stream_bytes"],
            "packet_stream_bytes": packeted.report["stream_bytes"],
            "byte_overhead_fraction": byte_overhead,
            "monolithic_snr_db_diagnostic": monolithic.report["snr_db"],
            "packet_snr_db_diagnostic": packeted.report["snr_db"],
            "snr_delta_db_diagnostic": snr_delta,
            "boundary_vs_interior_error_db": _boundary_error_ratio_db(
                samples,
                packeted.reconstruction,
                packet_frames,
                args.half_window,
            ),
            "gate_passed": gate_passed,
        }
    report = {
        "status": (
            "bounded packet gate passed"
            if passes == len(reports)
            else "bounded packet gate failed"
        ),
        "research_only": True,
        "metric_warning": (
            "waveform and boundary-error values are diagnostics, not "
            "perceptual equivalence"
        ),
        "gate_rule": (
            "no more than 8% complete-byte overhead and no more than 0.5 dB "
            "waveform-SNR loss on every clip"
        ),
        "passing_clips": passes,
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


if __name__ == "__main__":
    main()
