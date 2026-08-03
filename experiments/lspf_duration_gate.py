#!/usr/bin/env python3
"""Run the R-161--R-165 long-first convolutive LSPF structural gate.

This is an exact lossless structural proxy, not a complete Resonith or Opus
comparison. It writes the long result before starting short diagnostics so an
interrupted run cannot erase the frozen long evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import zlib

import numpy as np

from reference.maf_p0.convolutive_anonymous_field import (
    ConvolutiveAnonymousLanguage,
)
from reference.maf_p0.convolutive_factorized_latent_field import (
    infer_convolutive_factorized_latent_field,
)
from reference.maf_p0.latent_source_field import LatentSourceLanguage
from reference.maf_p0.lspf_analysis_policy import (
    LspfPolicyRequest,
    choose_lspf_analysis_plan,
)
from reference.maf_p0.lspf_duration_rdo import (
    LspfDurationCandidate,
    select_lspf_duration_candidate,
)
from reference.maf_p0.wav_io import read_pcm16_channels


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LONG = (
    Path("G:/Orkela/comparison/public-benchmark-2026-07-26")
    / "mozart-original.wav"
)
DEFAULT_SHORT = (
    ROOT / "artifacts/corpus/prepared-r111/ebu-female-speech-en.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-dense-orchestra.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-pink-noise.wav",
)
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/results/lspf_r165_long_first_2026-07-27.json"
)


def _sha256_pcm(values: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(values, dtype="<i2").tobytes()
    ).hexdigest()


def _compressed_integer_bytes(values: np.ndarray) -> tuple[int, str]:
    minimum = int(np.min(values)) if values.size else 0
    maximum = int(np.max(values)) if values.size else 0
    if -32768 <= minimum and maximum <= 32767:
        storage = "signed-s16le"
        payload = np.ascontiguousarray(values, dtype="<i2").tobytes()
    else:
        storage = "signed-s32le"
        payload = np.ascontiguousarray(values, dtype="<i4").tobytes()
    return len(zlib.compress(payload, 9)), storage


def _analysis_plan(
    *,
    frame_count: int,
    sample_rate: int,
    channels: int,
) -> dict:
    return choose_lspf_analysis_plan(
        LspfPolicyRequest(
            duration_frames=frame_count,
            sample_rate=sample_rate,
            channels=channels,
            latency_target_ms=500,
            encoder_time_budget_x=30.0,
            encoder_memory_bytes=16 << 30,
            gpu_memory_bytes=8 << 30,
            lossless=True,
        )
    ).to_manifest()


def _diagnostic_language(
    duration_class: str,
) -> tuple[ConvolutiveAnonymousLanguage, LatentSourceLanguage]:
    if duration_class == "long":
        return (
            ConvolutiveAnonymousLanguage(
                fft_samples=1024,
                hop_samples=256,
                factor_count=2,
                kernel_frames=4,
                iterations=8,
            ),
            LatentSourceLanguage(
                scales=(512, 2048, 8192),
                origin_hop=8192,
                minimum_occurrences=3,
                maximum_components=1,
                maximum_cluster_members=40,
                maximum_lag=12,
                minimum_spectral_similarity=0.92,
                maximum_normalized_correction=0.45,
                consensus_iterations=2,
                similarity_batch_rows=128,
            ),
        )
    return (
        ConvolutiveAnonymousLanguage(
            fft_samples=1024,
            hop_samples=256,
            factor_count=4,
            kernel_frames=8,
            iterations=24,
        ),
        LatentSourceLanguage(
            scales=(512, 2048, 8192),
            origin_hop=512,
            minimum_occurrences=3,
            maximum_components=1,
            maximum_cluster_members=40,
            maximum_lag=12,
            minimum_spectral_similarity=0.92,
            maximum_normalized_correction=0.45,
            consensus_iterations=3,
            similarity_batch_rows=256,
        ),
    )


def _analyze(
    path: Path,
    *,
    maximum_seconds: float,
) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_limit = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_limit].copy()
    policy = _analysis_plan(
        frame_count=source.shape[0],
        sample_rate=sample_rate,
        channels=source.shape[1],
    )
    factor_language, field_language = _diagnostic_language(
        policy["duration_class"]
    )
    started = time.perf_counter()
    field = infer_convolutive_factorized_latent_field(
        source,
        sample_rate=sample_rate,
        factor_language=factor_language,
        field_language=field_language,
    )
    elapsed = time.perf_counter() - started

    source_payload = np.ascontiguousarray(source, dtype="<i2").tobytes()
    independent_bytes = len(zlib.compress(source_payload, 9))
    basis_bytes = sum(
        len(
            zlib.compress(
                np.ascontiguousarray(component.basis, dtype="<i2").tobytes(),
                9,
            )
        )
        for latent in field.fields
        for component in latent.components
    )
    event_bytes = sum(
        len(component.event_map)
        for latent in field.fields
        for component in latent.components
    )
    correction_bytes, correction_storage = _compressed_integer_bytes(
        field.truth_correction
    )
    component_count = field.report["latent_component_count"]
    proxy_header_bytes = 64 + 16 * len(field.fields) + 16 * component_count
    structured_bytes = (
        proxy_header_bytes + basis_bytes + event_bytes + correction_bytes
    )
    selection = select_lspf_duration_candidate(
        duration_class=policy["duration_class"],
        candidates=(
            LspfDurationCandidate(
                "independent-truth",
                independent_bytes,
                True,
                1.0,
                True,
            ),
            LspfDurationCandidate(
                "convolutive-lspf",
                structured_bytes,
                True,
                1.0,
                True,
            ),
        ),
        incumbent_candidate_id="independent-truth",
        fallback_candidate_id="independent-truth",
        matched_byte_tolerance=max(1, independent_bytes // 1000),
        minimum_quality_delta=0.0,
        dual_axis_refinement_completed=True,
    )
    source_energy = float(
        np.sum(source.astype(np.float64) ** 2)
    )
    correction_energy = float(
        np.sum(field.truth_correction.astype(np.float64) ** 2)
    )
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / exact lossless structural proxy / "
            "not complete Resonith or Opus comparable"
        ),
        "duration_class": policy["duration_class"],
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_pcm_bytes": len(source_payload),
        "source_sha256": _sha256_pcm(source),
        "reconstruction_sha256": _sha256_pcm(field.reconstruction),
        "exact_reconstruction": bool(
            np.array_equal(field.reconstruction, source.astype(np.int64))
        ),
        "automatic_plan": policy,
        "diagnostic_execution_plan": {
            "factor_language": {
                "fft_samples": factor_language.fft_samples,
                "hop_samples": factor_language.hop_samples,
                "factor_count": factor_language.factor_count,
                "kernel_frames": factor_language.kernel_frames,
                "iterations": factor_language.iterations,
            },
            "field_language": {
                "scales": list(field_language.scales),
                "origin_hop": field_language.origin_hop,
                "maximum_components_per_factor": (
                    field_language.maximum_components
                ),
            },
            "scope": (
                "bounded CPU fast diagnostic; complete every-origin C++23/CUDA "
                "Foundry remains an R-161 milestone"
            ),
        },
        "factor_count": field.report["factor_count"],
        "active_factor_count": field.report["active_factor_count"],
        "latent_component_count": component_count,
        "latent_occurrence_count": field.report["latent_occurrence_count"],
        "explained_energy_fraction": (
            1.0 - correction_energy / source_energy
            if source_energy
            else 1.0
        ),
        "independent_zlib_proxy_bytes": independent_bytes,
        "basis_zlib_bytes": basis_bytes,
        "event_bytes": event_bytes,
        "correction_zlib_bytes": correction_bytes,
        "correction_storage": correction_storage,
        "proxy_header_bytes": proxy_header_bytes,
        "structured_zlib_proxy_bytes": structured_bytes,
        "structured_saving_bytes": independent_bytes - structured_bytes,
        "structured_saving_percent": (
            100.0 * (independent_bytes - structured_bytes) / independent_bytes
            if independent_bytes
            else 0.0
        ),
        "selection": selection.report,
        "oracle": field.report,
        "wall_seconds": elapsed,
        "realtime_factor": (
            elapsed / (source.shape[0] / sample_rate)
            if source.shape[0]
            else 0.0
        ),
    }


def _write(payload: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--long-input", type=Path, default=DEFAULT_LONG)
    parser.add_argument(
        "--short-inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_SHORT),
    )
    parser.add_argument("--long-seconds", type=float, default=120.0)
    parser.add_argument("--short-seconds", type=float, default=12.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    payload = {
        "schema": "resonith-r165-long-first-duration-gate-1",
        "status": "running-long",
        "test_order": ["long", "freeze-long", "short", "select"],
        "long_results": [],
        "short_results": [],
    }
    _write(payload, arguments.output)

    long_path = arguments.long_input.resolve()
    print(f"R-165 long-first: {long_path.name}", flush=True)
    long_result = _analyze(
        long_path,
        maximum_seconds=arguments.long_seconds,
    )
    payload["long_results"].append(long_result)
    payload["status"] = "long-frozen-short-running"
    payload["long_frontier_frozen"] = True
    _write(payload, arguments.output)
    print(
        "  long frozen "
        f"saving={long_result['structured_saving_percent']:.3f}% "
        f"wall={long_result['wall_seconds']:.3f}s",
        flush=True,
    )

    for short_input in arguments.short_inputs:
        short_path = short_input.resolve()
        print(f"R-165 short-second: {short_path.name}", flush=True)
        result = _analyze(
            short_path,
            maximum_seconds=arguments.short_seconds,
        )
        payload["short_results"].append(result)
        _write(payload, arguments.output)
        print(
            "  short "
            f"saving={result['structured_saving_percent']:.3f}% "
            f"wall={result['wall_seconds']:.3f}s",
            flush=True,
        )

    payload["status"] = "complete-fast-diagnostic"
    payload["long_frontier_frozen"] = True
    payload["generation_fixation"] = (
        "not applicable: proxy diagnostic, no codec generation"
    )
    _write(payload, arguments.output)
    print(f"Wrote {arguments.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
