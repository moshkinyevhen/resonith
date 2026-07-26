"""Run the R-105 nonrecursive harmonic excitation Basis speech fast gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from active_band_selection_gate import (  # noqa: E402
    _diagnostics,
    _opus_diagnostics,
)
from maf_p0.harmonic_basis_oracle import (  # noqa: E402
    analyze_harmonic_basis_source,
    encode_harmonic_basis_analysis,
)
from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
)
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--opus", type=Path, required=True)
    parser.add_argument("--opus-decoded", type=Path, required=True)
    parser.add_argument("--opus-decoder-version", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    sample_rate, channels = read_pcm16_channels(args.source)
    if channels.shape[1] != 1:
        raise ValueError("R-105 fast gate requires mono speech")
    source = channels[:, 0]
    started = time.perf_counter()
    baseline_analysis = analyze_lapped_source(
        channels,
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    baseline = encode_lapped_analysis(
        baseline_analysis,
        coefficients_per_frame=64,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    target_bytes = len(baseline.payload)

    shortlists = []
    for block_size in (1024, 2048, 4096):
        for harmonic_count in (2, 4, 6):
            analysis = analyze_harmonic_basis_source(
                source,
                sample_rate,
                block_size=block_size,
                harmonic_count=harmonic_count,
            )
            candidates = {
                budget: encode_harmonic_basis_analysis(
                    analysis,
                    coefficients_per_frame=budget,
                )
                for budget in range(48, 69, 2)
            }
            coarse = min(
                candidates.values(),
                key=lambda candidate: (
                    abs(len(candidate.payload) - target_bytes),
                    len(candidate.payload) > target_bytes,
                ),
            )
            coarse_budget = coarse.report["coefficients_per_frame"]
            for budget in (coarse_budget - 1, coarse_budget + 1):
                if 1 <= budget <= 512 and budget not in candidates:
                    candidates[budget] = encode_harmonic_basis_analysis(
                        analysis,
                        coefficients_per_frame=budget,
                    )
            nearest = min(
                candidates.values(),
                key=lambda candidate: (
                    abs(len(candidate.payload) - target_bytes),
                    len(candidate.payload) > target_bytes,
                    candidate.report["coefficients_per_frame"],
                ),
            )
            metrics = _diagnostics(
                source.reshape(-1, 1),
                nearest.reconstruction.reshape(-1, 1),
                sample_rate,
                "speech",
            )
            shortlists.append(
                {
                    "block_size": block_size,
                    "harmonic_count": harmonic_count,
                    "candidate": nearest,
                    "metrics": metrics,
                    "byte_delta_fraction": (
                        len(nearest.payload) / target_bytes - 1.0
                    ),
                }
            )

    rate_matched = [
        record
        for record in shortlists
        if abs(record["byte_delta_fraction"]) <= 0.005
    ]
    selection_pool = rate_matched or shortlists
    selected = max(
        selection_pool,
        key=lambda record: (
            record["metrics"]["speech"]["stoi"]
            + record["metrics"]["speech"]["estoi"],
            record["metrics"]["waveform"]["snr_db"],
            -abs(record["byte_delta_fraction"]),
        ),
    )
    baseline_metrics = _diagnostics(
        channels,
        baseline.reconstruction,
        sample_rate,
        "speech",
    )
    opus_metrics = _opus_diagnostics(
        args.source,
        args.opus_decoded,
        "speech",
    )
    candidate = selected["candidate"]
    metrics = selected["metrics"]
    snr_delta = (
        metrics["waveform"]["snr_db"]
        - baseline_metrics["waveform"]["snr_db"]
    )
    log_mel_ratio = (
        metrics["spectral"]["log_mel_rmse"]
        / baseline_metrics["spectral"]["log_mel_rmse"]
    )
    gate_passed = bool(
        abs(selected["byte_delta_fraction"]) <= 0.005
        and metrics["speech"]["stoi"]
            > baseline_metrics["speech"]["stoi"]
        and metrics["speech"]["estoi"]
            > baseline_metrics["speech"]["estoi"]
        and snr_delta >= -0.5
        and log_mel_ratio <= 1.05
    )

    (args.output_directory / "energy.lpf1").write_bytes(baseline.payload)
    (args.output_directory / "harmonic-basis.hbr1").write_bytes(
        candidate.payload
    )
    write_pcm16_channels(
        args.output_directory / "energy-decoded.wav",
        sample_rate,
        baseline.reconstruction,
    )
    write_pcm16_channels(
        args.output_directory / "harmonic-basis-decoded.wav",
        sample_rate,
        candidate.reconstruction.reshape(-1, 1),
    )
    report = {
        "schema": "resonith-harmonic-basis-gate-1",
        "decision": "R-105",
        "status": (
            "speech fast gate passed; run false-positive music gate"
            if gate_passed
            else "speech fast gate failed; do not add decoder syntax"
        ),
        "fast_gate_passed": gate_passed,
        "wall_seconds": time.perf_counter() - started,
        "source": {
            "path": args.source.name,
            "bytes": args.source.stat().st_size,
            "sha256": _sha256(args.source.read_bytes()),
            "sample_rate": sample_rate,
            "frames": int(source.size),
        },
        "energy": {
            "bytes": len(baseline.payload),
            "sha256": _sha256(baseline.payload),
            "coefficients_per_frame": 64,
            "metrics": baseline_metrics,
        },
        "harmonic_basis": {
            "bytes": len(candidate.payload),
            "sha256": _sha256(candidate.payload),
            "byte_delta_fraction": selected["byte_delta_fraction"],
            "snr_delta_db": snr_delta,
            "log_mel_ratio": log_mel_ratio,
            "metrics": metrics,
            **candidate.report,
        },
        "opus": {
            "bytes": args.opus.stat().st_size,
            "sha256": _sha256(args.opus.read_bytes()),
            "decoded_sha256": _sha256(args.opus_decoded.read_bytes()),
            "decoder_version": args.opus_decoder_version,
            "metrics": opus_metrics,
        },
        "shortlist": [
            {
                "block_size": record["block_size"],
                "harmonic_count": record["harmonic_count"],
                "bytes": len(record["candidate"].payload),
                "coefficients_per_frame": record["candidate"].report[
                    "coefficients_per_frame"
                ],
                "active_block_fraction": record["candidate"].report[
                    "active_block_fraction"
                ],
                "byte_delta_fraction": record["byte_delta_fraction"],
                "snr_db": record["metrics"]["waveform"]["snr_db"],
                "stoi": record["metrics"]["speech"]["stoi"],
                "estoi": record["metrics"]["speech"]["estoi"],
                "log_mel_rmse": record["metrics"]["spectral"][
                    "log_mel_rmse"
                ],
            }
            for record in shortlists
        ],
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
