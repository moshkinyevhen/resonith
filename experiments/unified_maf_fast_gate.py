"""Run a labeled fast diagnostic for the R-120 unified MAF cell stream.

This gate deliberately evaluates one clip at a time.  It is useful while
changing the prospective syntax, but it cannot satisfy the mandatory R-118
architecture gate or support a general codec claim.
"""

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
from maf_p0.lapped_oracle import analyze_lapped_source  # noqa: E402
from maf_p0.maf_cell_oracle import encode_maf_cell_analysis  # noqa: E402
from maf_p0.maf_source_filter_oracle import (  # noqa: E402
    analyze_maf_source_filter_source,
    encode_maf_source_filter_analysis,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mode", choices=("music", "speech"), required=True)
    parser.add_argument("--opus-stream", type=Path)
    parser.add_argument("--opus-decoded", type=Path)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--stem", default="unified-maf")
    parser.add_argument("--maximum-pulses-per-frame", type=int, default=192)
    parser.add_argument("--rate-lambda-q20", type=int, default=8192)
    parser.add_argument("--pvq-guard-q12", type=int)
    parser.add_argument("--basis-search-limit", type=int, default=4)
    parser.add_argument("--source-filter", action="store_true")
    parser.add_argument("--source-filter-block-size", type=int, default=256)
    parser.add_argument("--source-filter-order", type=int, default=10)
    parser.add_argument("--source-filter-parameter-lambda", type=float, default=0.5)
    parser.add_argument("--filter-basis-count", type=int, default=16)
    parser.add_argument(
        "--excitation-backend",
        choices=("mfc1", "epvq"),
        default="mfc1",
    )
    parser.add_argument("--excitation-subframe-size", type=int, default=64)
    parser.add_argument("--excitation-pulses", type=int, default=8)
    parser.add_argument("--excitation-quality-guard-q12", type=int, default=4096)
    parser.add_argument("--adaptive-quality-guard-q12", type=int, default=4608)
    parser.add_argument("--excitation-basis-count", type=int, default=0)
    parser.add_argument("--excitation-basis-pulses", type=int, default=16)
    parser.add_argument("--excitation-basis-iterations", type=int, default=4)
    parser.add_argument("--excitation-basis-search-limit", type=int, default=8)
    parser.add_argument(
        "--excitation-basis-correction-pulses",
        type=int,
        default=0,
    )
    args = parser.parse_args()
    if (args.opus_stream is None) != (args.opus_decoded is None):
        raise ValueError("the Opus stream and decode must be supplied together")

    sample_rate, samples = read_pcm16_channels(args.source)
    native_core = NativeMain0Decoder(args.native_core)
    analysis_started = time.perf_counter()
    if args.source_filter:
        if samples.shape[1] != 1:
            raise ValueError("the SFT1 diagnostic currently requires mono PCM")
        analysis = analyze_maf_source_filter_source(
            samples[:, 0],
            sample_rate,
            block_size=args.source_filter_block_size,
            filter_order=args.source_filter_order,
            parameter_lambda=args.source_filter_parameter_lambda,
            filter_basis_count=args.filter_basis_count,
            half_window=512,
            band_count=24,
            native_analyzer=native_core,
        )
    else:
        analysis = analyze_lapped_source(
            samples,
            sample_rate,
            half_window=512,
            band_count=24,
            native_analyzer=native_core,
        )
    analysis_seconds = time.perf_counter() - analysis_started

    encode_started = time.perf_counter()
    if args.source_filter:
        encoded = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=args.maximum_pulses_per_frame,
            rate_lambda_q20=args.rate_lambda_q20,
            pvq_guard_q12=args.pvq_guard_q12,
            basis_search_limit=args.basis_search_limit,
            excitation_backend=args.excitation_backend,
            excitation_subframe_size=args.excitation_subframe_size,
            excitation_pulses=args.excitation_pulses,
            excitation_quality_guard_q12=(
                args.excitation_quality_guard_q12
            ),
            adaptive_quality_guard_q12=args.adaptive_quality_guard_q12,
            excitation_basis_count=args.excitation_basis_count,
            excitation_basis_pulses=args.excitation_basis_pulses,
            excitation_basis_iterations=args.excitation_basis_iterations,
            excitation_basis_search_limit=(
                args.excitation_basis_search_limit
            ),
            excitation_basis_correction_pulses=(
                args.excitation_basis_correction_pulses
            ),
        )
    else:
        encoded = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=args.maximum_pulses_per_frame,
            rate_lambda_q20=args.rate_lambda_q20,
            pvq_guard_q12=args.pvq_guard_q12,
            basis_search_limit=args.basis_search_limit,
        )
    encode_seconds = time.perf_counter() - encode_started

    args.output_directory.mkdir(parents=True, exist_ok=True)
    stream_path = args.output_directory / f"{args.stem}.resonith"
    decoded_path = args.output_directory / f"{args.stem}-decoded.wav"
    stream_path.write_bytes(encoded.payload)
    reconstruction = encoded.reconstruction
    if reconstruction.ndim == 1:
        reconstruction = reconstruction[:, None]
    write_pcm16_channels(decoded_path, sample_rate, reconstruction)
    metrics = _diagnostics(
        samples,
        reconstruction,
        sample_rate,
        args.mode,
    )

    opus = None
    if args.opus_stream is not None:
        opus_rate, opus_samples = read_pcm16_channels(args.opus_decoded)
        if opus_rate != sample_rate or opus_samples.shape != samples.shape:
            raise ValueError("the Opus decode differs from the source layout")
        opus = {
            "bytes": args.opus_stream.stat().st_size,
            "stream_sha256": _sha256(args.opus_stream),
            "decoded_sha256": _sha256(args.opus_decoded),
            "metrics": _diagnostics(
                samples,
                opus_samples,
                sample_rate,
                args.mode,
            ),
        }

    report = {
        "schema": "resonith-unified-maf-fast-diagnostic-1",
        "decision": "R-121",
        "status": (
            "fast diagnostic only; not an R-118 architecture gate or "
            "general codec claim"
        ),
        "source": {
            "path": args.source.name,
            "bytes": args.source.stat().st_size,
            "sha256": _sha256(args.source),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "candidate": {
            "source_filter_enabled": args.source_filter,
            "bytes": len(encoded.payload),
            "stream_sha256": _sha256(stream_path),
            "decoded_sha256": _sha256(decoded_path),
            "analysis_wall_seconds": analysis_seconds,
            "encode_wall_seconds": encode_seconds,
            "metrics": metrics,
            "encoder_report": encoded.report,
        },
        "opus": opus,
    }
    report_path = args.output_directory / f"{args.stem}.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{stream_path}: {len(encoded.payload)} bytes, "
        f"SNR {metrics['waveform']['snr_db']:.6f} dB, "
        f"log-mel {metrics['spectral']['log_mel_rmse']:.6f}",
        flush=True,
    )
    if args.mode == "speech":
        print(
            f"STOI {metrics['speech']['stoi']:.6f}, "
            f"ESTOI {metrics['speech']['estoi']:.6f}",
            flush=True,
        )
    print(f"Wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
