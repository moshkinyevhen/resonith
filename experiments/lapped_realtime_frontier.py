"""Sweep LPS3 transform and packet durations for a Realtime candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_compact_packet_stream,
)
from maf_p0.perceptual_metrics import (  # noqa: E402
    multiresolution_spectral_error_db,
    transient_pre_echo_error_db,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


BASE_BUDGETS_512 = {
    "corelli-sonata-realization": 61,
    "emotional-piano-cc0": 66,
    "patro-de-bateria": 46,
}
BAND_COUNTS = {128: 12, 256: 16, 512: 24}


def _quality(samples, reconstruction, sample_rate: int) -> dict:
    return {
        "spectral": multiresolution_spectral_error_db(
            samples,
            reconstruction,
        ),
        "pre_echo": transient_pre_echo_error_db(
            samples,
            reconstruction,
            sample_rate,
        ),
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
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument(
        "--half-windows",
        type=int,
        nargs="+",
        default=(128, 256, 512),
    )
    parser.add_argument(
        "--packet-milliseconds",
        type=float,
        nargs="+",
        default=(20.0, 40.0, 80.0),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "lapped_realtime_frontier"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("Realtime frontier duration must be positive")
    if any(
        half_window not in BAND_COUNTS
        for half_window in args.half_windows
    ):
        raise ValueError("Realtime half-window lacks a declared band count")
    if any(value <= 0.0 for value in args.packet_milliseconds):
        raise ValueError("Realtime packet durations must be positive")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clips = {}
    configuration_passes: dict[str, int] = {}
    configuration_rate_ratios: dict[str, list[float]] = {}
    configuration_latencies: dict[str, float] = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + frame_count].copy()
        base_budget = BASE_BUDGETS_512[record["id"]]
        anchor = encode_lapped_stream(
            samples,
            sample_rate,
            coefficients_per_frame=base_budget,
            half_window=512,
            band_count=24,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="adaptive",
        )
        anchor_quality = _quality(
            samples,
            anchor.reconstruction,
            sample_rate,
        )
        anchor_spectral = anchor_quality["spectral"][
            "mean_spectral_convergence_db"
        ]
        candidates = {}
        for half_window in args.half_windows:
            budget = max(
                1,
                int(round(base_budget * half_window / 512.0)),
            )
            for requested_ms in args.packet_milliseconds:
                packet_units = max(
                    1,
                    int(
                        round(
                            requested_ms
                            * sample_rate
                            / 1000.0
                            / half_window
                        )
                    ),
                )
                packet_frames = packet_units * half_window
                encoded = encode_lapped_compact_packet_stream(
                    samples,
                    sample_rate,
                    coefficients_per_frame=budget,
                    packet_frames=packet_frames,
                    half_window=half_window,
                    band_count=BAND_COUNTS[half_window],
                )
                quality = _quality(
                    samples,
                    encoded.reconstruction,
                    sample_rate,
                )
                actual_packet_ms = packet_frames * 1000.0 / sample_rate
                estimated_latency_ms = (
                    (packet_frames + half_window) * 1000.0 / sample_rate
                )
                complete_rate_ratio = len(encoded.payload) / len(anchor.payload)
                snr_delta = encoded.report["snr_db"] - anchor.report["snr_db"]
                spectral_delta = (
                    quality["spectral"]["mean_spectral_convergence_db"]
                    - anchor_spectral
                )
                gate_passed = bool(
                    estimated_latency_ms <= 50.0
                    and complete_rate_ratio <= 1.15
                    and snr_delta >= -1.0
                    and spectral_delta <= 1.0
                )
                key = f"h{half_window}_p{requested_ms:g}"
                configuration_passes[key] = (
                    configuration_passes.get(key, 0) + int(gate_passed)
                )
                configuration_rate_ratios.setdefault(key, []).append(
                    complete_rate_ratio
                )
                configuration_latencies[key] = estimated_latency_ms
                candidates[key] = {
                    "half_window": half_window,
                    "band_count": BAND_COUNTS[half_window],
                    "coefficients_per_frame": budget,
                    "requested_packet_milliseconds": requested_ms,
                    "packet_frames": packet_frames,
                    "actual_packet_milliseconds": actual_packet_ms,
                    "estimated_algorithmic_latency_milliseconds": (
                        estimated_latency_ms
                    ),
                    "stream_bytes": len(encoded.payload),
                    "packet_format": "LPS4 compact transport-framed",
                    "packet_overhead_fraction_vs_same_transform": (
                        encoded.report["packet_byte_overhead_fraction"]
                    ),
                    "complete_rate_ratio_vs_anchor": complete_rate_ratio,
                    "snr_db_diagnostic": encoded.report["snr_db"],
                    "snr_delta_vs_anchor_db_diagnostic": snr_delta,
                    "spectral_delta_vs_anchor_db_diagnostic": spectral_delta,
                    "quality_diagnostics": quality,
                    "gate_passed": gate_passed,
                }
        clips[record["id"]] = {
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "anchor": {
                "half_window": 512,
                "band_count": 24,
                "coefficients_per_frame": base_budget,
                "stream_bytes": len(anchor.payload),
                "snr_db_diagnostic": anchor.report["snr_db"],
                "quality_diagnostics": anchor_quality,
            },
            "candidates": candidates,
        }

    clip_count = len(clips)
    common_passes = [
        key
        for key, count in configuration_passes.items()
        if count == clip_count
    ]
    recommended = None
    if common_passes:
        recommended = min(
            common_passes,
            key=lambda key: (
                configuration_latencies[key],
                sum(configuration_rate_ratios[key])
                / len(configuration_rate_ratios[key]),
                key,
            ),
        )
    report = {
        "status": (
            "Realtime frontier found a common diagnostic candidate"
            if recommended is not None
            else "Realtime frontier found no common diagnostic candidate"
        ),
        "research_only": True,
        "metric_warning": (
            "waveform, spectral, and pre-echo values are diagnostics, not "
            "perceptual equivalence or a listening result"
        ),
        "gate_rule": (
            "at most 50 ms packet-plus-half-window latency, 15% complete-byte "
            "increase, 1 dB waveform-SNR loss, and 1 dB mean spectral-error "
            "loss versus the H512 monolithic anchor on every clip"
        ),
        "recommended_configuration": recommended,
        "common_passing_configurations": common_passes,
        "configuration_pass_counts": configuration_passes,
        "clip_count": clip_count,
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
