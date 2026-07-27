"""Run the R-131 complete MFT1 plus Truth fast diagnostic."""

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

from active_band_selection_gate import _diagnostics  # noqa: E402
from maf_p0.maf_typed_candidate import (  # noqa: E402
    encode_maf_typed_truth_candidate,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import read_pcm16_channels, write_pcm16_channels  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _quality_guard(candidate: dict, baseline: dict) -> dict:
    """Reject a byte win when declared waveform or spectral metrics regress."""

    checks = {
        "snr_non_regression": (
            candidate["waveform"]["snr_db"]
            >= baseline["waveform"]["snr_db"] - 0.10
        ),
        "si_sdr_non_regression": (
            candidate["waveform"]["si_sdr_db"]
            >= baseline["waveform"]["si_sdr_db"] - 0.10
        ),
        "log_mel_within_3_percent": (
            candidate["spectral"]["log_mel_rmse"]
            <= baseline["spectral"]["log_mel_rmse"] * 1.03 + 1.0e-12
        ),
        "magnitude_cosine_non_regression": (
            candidate["spectral"]["magnitude_cosine_similarity"]
            >= baseline["spectral"]["magnitude_cosine_similarity"] - 1.0e-5
        ),
    }
    candidate_stft = candidate["spectral"]["multiresolution_stft"]
    baseline_stft = baseline["spectral"]["multiresolution_stft"]
    for size in sorted(baseline_stft, key=int):
        checks[f"stft_{size}_within_5_percent"] = (
            candidate_stft[size]["spectral_convergence"]
            <= baseline_stft[size]["spectral_convergence"] * 1.05 + 1.0e-12
        )
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "policy": (
            "R-135 fast non-regression guard; listening and complete R-118 "
            "admission remain pending"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mode", choices=("speech", "music"), required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--stem", default="mft1-truth")
    parser.add_argument("--coefficients-per-frame", type=int, default=64)
    parser.add_argument("--segment-milliseconds", type=float, default=120.0)
    parser.add_argument("--filter-order", type=int, default=10)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    args = parser.parse_args()

    sample_rate, samples = read_pcm16_channels(args.source)
    decoder = NativeMain0Decoder(args.native_core)
    started = time.perf_counter()
    candidate = encode_maf_typed_truth_candidate(
        samples,
        sample_rate,
        native_decoder=decoder,
        coefficients_per_frame=args.coefficients_per_frame,
        segment_milliseconds=args.segment_milliseconds,
        filter_order=args.filter_order,
        half_window=args.half_window,
        band_count=args.band_count,
    )
    wall_seconds = time.perf_counter() - started
    candidate_metrics = _diagnostics(
        samples,
        candidate.reconstruction,
        sample_rate,
        args.mode,
    )
    baseline_metrics = _diagnostics(
        samples,
        candidate.baseline.reconstruction,
        sample_rate,
        args.mode,
    )
    quality_guard = _quality_guard(candidate_metrics, baseline_metrics)
    admitted = (
        candidate.selected_kind == "mft1-truth"
        and quality_guard["passed"]
    )
    selected_payload = (
        candidate.payload if admitted else candidate.baseline.payload
    )
    selected_reconstruction = (
        candidate.reconstruction
        if admitted
        else candidate.baseline.reconstruction
    )
    selected_metrics = candidate_metrics if admitted else baseline_metrics
    selected_kind = (
        "mft1-truth"
        if admitted
        else (
            "truth-fallback-quality-guard"
            if candidate.selected_kind == "mft1-truth"
            else "truth-fallback-rate-distortion"
        )
    )

    args.output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "candidate": args.output_directory / f"{args.stem}.resonith",
        "candidate_decoded": (
            args.output_directory / f"{args.stem}-decoded.wav"
        ),
        "baseline": args.output_directory / f"{args.stem}-baseline.resonith",
        "baseline_decoded": (
            args.output_directory / f"{args.stem}-baseline-decoded.wav"
        ),
        "selected": args.output_directory / f"{args.stem}-selected.resonith",
        "selected_decoded": (
            args.output_directory / f"{args.stem}-selected-decoded.wav"
        ),
    }
    paths["candidate"].write_bytes(candidate.payload)
    paths["baseline"].write_bytes(candidate.baseline.payload)
    paths["selected"].write_bytes(selected_payload)
    write_pcm16_channels(
        paths["candidate_decoded"],
        sample_rate,
        candidate.reconstruction,
    )
    write_pcm16_channels(
        paths["baseline_decoded"],
        sample_rate,
        candidate.baseline.reconstruction,
    )
    write_pcm16_channels(
        paths["selected_decoded"],
        sample_rate,
        selected_reconstruction,
    )

    report = {
        "schema": "resonith-maf-typed-truth-fast-gate-1",
        "decision": "R-131/R-132",
        "status": (
            "fast diagnostic only; complete R-118 architecture gate pending"
        ),
        "source": {
            "path": args.source.name,
            "bytes": args.source.stat().st_size,
            "sha256": _sha256(args.source),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "configuration": {
            "coefficients_per_frame": args.coefficients_per_frame,
            "segment_milliseconds": args.segment_milliseconds,
            "filter_order": args.filter_order,
            "half_window": args.half_window,
            "band_count": args.band_count,
        },
        "wall_seconds": wall_seconds,
        "candidate": {
            "bytes": len(candidate.payload),
            "sha256": _sha256(paths["candidate"]),
            "metrics": candidate_metrics,
        },
        "baseline": {
            "bytes": len(candidate.baseline.payload),
            "sha256": _sha256(paths["baseline"]),
            "metrics": baseline_metrics,
        },
        "selected": {
            "kind": selected_kind,
            "bytes": len(selected_payload),
            "sha256": _sha256(paths["selected"]),
            "metrics": selected_metrics,
        },
        "quality_guard": quality_guard,
        "encoder_report": candidate.report,
        "artifacts": {
            key: {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for key, path in paths.items()
        },
    }
    report_path = args.output_directory / f"{args.stem}.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"MFT1+Truth {len(candidate.payload)} bytes; "
        f"Truth baseline {len(candidate.baseline.payload)} bytes; "
        f"selected {selected_kind}; {wall_seconds:.3f} s",
        flush=True,
    )
    print(f"Wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
