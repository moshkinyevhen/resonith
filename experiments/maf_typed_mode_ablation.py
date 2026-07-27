"""Ablate R-137 full-band MAF families under one exact residual budget."""

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
from maf_typed_truth_fast_gate import _quality_guard  # noqa: E402
from maf_p0.maf_typed import (  # noqa: E402
    IMPULSE_EXCITATION,
    PERIODIC_BASIS_EXCITATION,
    STOCHASTIC_EXCITATION,
)
from maf_p0.maf_typed_candidate import (  # noqa: E402
    encode_maf_typed_truth_candidate,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


MODE_MASKS = {
    "none": (),
    "periodic": (PERIODIC_BASIS_EXCITATION,),
    "impulse": (IMPULSE_EXCITATION,),
    "stochastic": (STOCHASTIC_EXCITATION,),
    "periodic-impulse": (
        PERIODIC_BASIS_EXCITATION,
        IMPULSE_EXCITATION,
    ),
    "periodic-stochastic": (
        PERIODIC_BASIS_EXCITATION,
        STOCHASTIC_EXCITATION,
    ),
    "impulse-stochastic": (
        IMPULSE_EXCITATION,
        STOCHASTIC_EXCITATION,
    ),
    "all": (
        IMPULSE_EXCITATION,
        STOCHASTIC_EXCITATION,
        PERIODIC_BASIS_EXCITATION,
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--preceding-stream", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--maximum-budget", type=int, required=True)
    parser.add_argument("--residual-budget", type=int, required=True)
    parser.add_argument("--segment-milliseconds", type=float, default=240.0)
    parser.add_argument("--filter-order", type=int, default=10)
    parser.add_argument(
        "--residual-selection-backend",
        choices=("energy", "gain-shape"),
        default="energy",
    )
    parser.add_argument("--residual-frame-whitening", type=float, default=0.0)
    parser.add_argument("--residual-band-whitening", type=float, default=0.0)
    parser.add_argument("--mask", action="append", choices=tuple(MODE_MASKS))
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    sample_rate, samples = read_pcm16_channels(args.source)
    decoder = NativeMain0Decoder(args.native_core)
    preceding_payload = args.preceding_stream.read_bytes()
    preceding_decoded = decoder.decode_lapped_compact_packets(
        preceding_payload
    ).samples
    if preceding_decoded.shape != samples.shape:
        raise ValueError("preceding stream shape mismatch")
    preceding_metrics = _diagnostics(
        samples,
        preceding_decoded,
        sample_rate,
        "music",
    )
    args.output_directory.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    masks: dict[str, dict] = {}
    selected_masks = args.mask or list(MODE_MASKS)
    for name in selected_masks:
        allowed_modes = MODE_MASKS[name]
        mask_started = time.perf_counter()
        candidate = encode_maf_typed_truth_candidate(
            samples,
            sample_rate,
            native_decoder=decoder,
            coefficients_per_frame=args.maximum_budget,
            segment_milliseconds=args.segment_milliseconds,
            filter_order=args.filter_order,
            half_window=512,
            band_count=24,
            residual_budget_override=args.residual_budget,
            allowed_modes=allowed_modes,
            residual_selection_backend=args.residual_selection_backend,
            residual_frame_whitening=args.residual_frame_whitening,
            residual_band_whitening=args.residual_band_whitening,
        )
        metrics = _diagnostics(
            samples,
            candidate.reconstruction,
            sample_rate,
            "music",
        )
        guard = _quality_guard(metrics, preceding_metrics)
        stream_path = args.output_directory / f"{name}.resonith"
        decoded_path = args.output_directory / f"{name}-decoded.wav"
        stream_path.write_bytes(candidate.payload)
        write_pcm16_channels(
            decoded_path,
            sample_rate,
            candidate.reconstruction,
        )
        eligible = bool(
            len(candidate.payload) <= len(preceding_payload)
            and guard["passed"]
        )
        masks[name] = {
            "allowed_modes": list(allowed_modes),
            "bytes": len(candidate.payload),
            "sha256": _sha256_file(stream_path),
            "stream_file": stream_path.name,
            "decoded_file": decoded_path.name,
            "decoded_sha256": _sha256_file(decoded_path),
            "metrics": metrics,
            "quality_guard": guard,
            "byte_non_regression": len(candidate.payload) <= len(preceding_payload),
            "eligible": eligible,
            "predictor": candidate.report["predictor"],
            "wall_seconds": time.perf_counter() - mask_started,
        }
        print(
            f"{name}: {len(candidate.payload)} bytes, "
            f"log-mel {metrics['spectral']['log_mel_rmse']:.6f}, "
            f"{'eligible' if eligible else 'rejected'}",
            flush=True,
        )

    eligible_masks = [
        (name, record) for name, record in masks.items() if record["eligible"]
    ]
    selected = min(
        eligible_masks,
        key=lambda item: (item[1]["bytes"], item[0]),
        default=None,
    )
    report = {
        "schema": "resonith-maf-typed-mode-ablation-1",
        "decision": "R-137",
        "status": (
            f"{selected[0]} admitted"
            if selected is not None
            else "no family mask admitted"
        ),
        "source_revision": args.source_revision,
        "source": {
            "file": args.source.name,
            "sha256": _sha256_file(args.source),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "preceding": {
            "file": args.preceding_stream.name,
            "bytes": len(preceding_payload),
            "sha256": _sha256_file(args.preceding_stream),
            "metrics": preceding_metrics,
        },
        "configuration": {
            "maximum_budget": args.maximum_budget,
            "residual_budget": args.residual_budget,
            "segment_milliseconds": args.segment_milliseconds,
            "filter_order": args.filter_order,
            "residual_selection_backend": args.residual_selection_backend,
            "residual_frame_whitening": args.residual_frame_whitening,
            "residual_band_whitening": args.residual_band_whitening,
        },
        "masks": masks,
        "selected": selected[0] if selected is not None else "preceding-fallback",
        "total_wall_seconds": time.perf_counter() - started,
    }
    report_path = args.output_directory / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
