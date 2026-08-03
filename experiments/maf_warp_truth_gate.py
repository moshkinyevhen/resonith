"""Encode one complete R-155 warp-dictionary plus lapped-Truth candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from active_band_selection_gate import _diagnostics  # noqa: E402
from maf_typed_truth_fast_gate import _quality_guard  # noqa: E402
from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
)
from maf_p0.maf_typed_candidate import (  # noqa: E402
    decode_maf_typed_truth_candidate,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.rsc1 import RSC1Section, pack_rsc1  # noqa: E402
from maf_p0.stream_sections import StreamConfig, pack_conf  # noqa: E402
from maf_p0.warp_dictionary import (  # noqa: E402
    fit_warp_dictionary_prediction,
)
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _candidate_payload(
    *,
    prediction: bytes,
    residual: bytes,
    frames: int,
    channels: int,
    sample_rate: int,
) -> bytes:
    return pack_rsc1(
        (
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(frames, 1, channels)),
            ),
            RSC1Section("MFT1", prediction),
            RSC1Section("MRI1", residual),
        ),
        profile=0,
        level=6,
        timebase_hz=sample_rate,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--block-samples", type=int, default=4096)
    parser.add_argument("--maximum-bases", type=int, default=64)
    parser.add_argument("--maximum-instances", type=int, default=4096)
    parser.add_argument("--maximum-normalized-error", type=float, default=0.02)
    parser.add_argument(
        "--residual-budget",
        type=int,
        action="append",
        default=None,
    )
    args = parser.parse_args()

    started = time.perf_counter()
    sample_rate, source = read_pcm16_channels(args.source)
    native = NativeMain0Decoder(args.native_core)
    baseline_payload = args.baseline.read_bytes()
    baseline_pcm = native.decode_lapped_compact_packets(
        baseline_payload
    ).samples
    if baseline_pcm.shape != source.shape:
        raise ValueError("R-155 baseline layout differs from the source")

    discovery_started = time.perf_counter()
    prediction = fit_warp_dictionary_prediction(
        source,
        sample_rate,
        native_decoder=native,
        block_samples=args.block_samples,
        maximum_bases=args.maximum_bases,
        maximum_instances=args.maximum_instances,
        maximum_normalized_error=args.maximum_normalized_error,
    )
    discovery_seconds = time.perf_counter() - discovery_started
    difference = (
        source.astype(np.int32)
        - prediction.reconstruction.astype(np.int32)
    )
    clipped_residual = np.clip(
        difference,
        -32768,
        32767,
    ).astype(np.int16)
    analysis_started = time.perf_counter()
    residual_analysis = analyze_lapped_source(
        clipped_residual,
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
        native_analyzer=native,
    )
    analysis_seconds = time.perf_counter() - analysis_started

    baseline_metrics = _diagnostics(
        source,
        baseline_pcm,
        sample_rate,
        "music",
    )
    budgets = sorted(set(args.residual_budget or (48, 56, 64, 68, 72)))
    options = []
    for budget in budgets:
        option_started = time.perf_counter()
        residual = encode_lapped_analysis(
            residual_analysis,
            coefficients_per_frame=budget,
            entropy_backend="bounded",
            density_backend="adaptive",
            selection_backend="energy",
            native_decoder=native,
        )
        payload = _candidate_payload(
            prediction=prediction.payload,
            residual=residual.payload,
            frames=source.shape[0],
            channels=source.shape[1],
            sample_rate=sample_rate,
        )
        decoded_rate, reconstruction = decode_maf_typed_truth_candidate(
            payload,
            native_decoder=native,
        )
        if decoded_rate != sample_rate:
            raise RuntimeError("R-155 candidate changed its sample rate")
        metrics = _diagnostics(source, reconstruction, sample_rate, "music")
        guard = _quality_guard(metrics, baseline_metrics)
        options.append(
            {
                "budget": budget,
                "payload": payload,
                "reconstruction": reconstruction,
                "metrics": metrics,
                "guard": guard,
                "bytes": len(payload),
                "residual_bytes": len(residual.payload),
                "seconds": time.perf_counter() - option_started,
            }
        )

    quality_options = [item for item in options if item["guard"]["passed"]]
    candidate = min(
        quality_options or options,
        key=lambda item: (
            item["bytes"] if quality_options else -item["budget"],
            item["budget"],
        ),
    )
    eligible = (
        candidate["guard"]["passed"]
        and candidate["bytes"] <= len(baseline_payload)
    )
    selected_payload = candidate["payload"] if eligible else baseline_payload
    selected_pcm = (
        candidate["reconstruction"] if eligible else baseline_pcm
    )

    args.output_directory.mkdir(parents=True, exist_ok=True)
    candidate_path = args.output_directory / "mozart-r155-candidate.resonith"
    candidate_wav = args.output_directory / "mozart-r155-candidate-decoded.wav"
    selected_path = args.output_directory / "mozart-r155-selected.resonith"
    selected_wav = args.output_directory / "mozart-r155-selected-decoded.wav"
    candidate_path.write_bytes(candidate["payload"])
    selected_path.write_bytes(selected_payload)
    write_pcm16_channels(
        candidate_wav,
        sample_rate,
        candidate["reconstruction"],
    )
    write_pcm16_channels(selected_wav, sample_rate, selected_pcm)

    report = {
        "schema": "resonith-r155-warp-truth-gate-1",
        "status": (
            "R-155 selected"
            if eligible
            else "R-155 candidate rejected; stable baseline selected"
        ),
        "source": {
            "path": str(args.source),
            "frames": int(source.shape[0]),
            "channels": int(source.shape[1]),
            "sample_rate": sample_rate,
            "bytes": args.source.stat().st_size,
        },
        "baseline": {
            "path": str(args.baseline),
            "bytes": len(baseline_payload),
            "sha256": _sha256(baseline_payload),
            "metrics": baseline_metrics,
        },
        "prediction": prediction.report,
        "candidate": {
            "path": str(candidate_path),
            "decoded_path": str(candidate_wav),
            "bytes": candidate["bytes"],
            "sha256": _sha256(candidate["payload"]),
            "budget": candidate["budget"],
            "residual_bytes": candidate["residual_bytes"],
            "metrics": candidate["metrics"],
            "guard": candidate["guard"],
            "byte_delta_vs_baseline": (
                candidate["bytes"] - len(baseline_payload)
            ),
        },
        "selected": {
            "kind": "r155-warp-truth" if eligible else "stable-fallback",
            "path": str(selected_path),
            "decoded_path": str(selected_wav),
            "bytes": len(selected_payload),
            "sha256": _sha256(selected_payload),
        },
        "frontier": [
            {
                key: value
                for key, value in item.items()
                if key not in {"payload", "reconstruction"}
            }
            for item in options
        ],
        "timing_seconds": {
            "discovery": discovery_seconds,
            "residual_analysis": analysis_seconds,
            "total": time.perf_counter() - started,
        },
    }
    (args.output_directory / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "candidate": report["candidate"],
        "selected": report["selected"],
        "prediction": prediction.report,
        "timing_seconds": report["timing_seconds"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
