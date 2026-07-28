#!/usr/bin/env python3
"""Run the R-159/R-160 exact structural proxy on heterogeneous real PCM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import zlib

import numpy as np

from reference.maf_p0.latent_source_field import (
    LatentSourceLanguage,
    infer_latent_source_pattern_field,
)
from reference.maf_p0.sparse_motif_grammar import (
    SparseMotifLanguage,
    SparsePathLanguage,
    pack_latent_field_event_ledger,
)
from reference.maf_p0.partial_spectrum_latent_field import (
    infer_partial_spectrum_latent_field,
)
from reference.maf_p0.anonymous_spectral_factor import (
    AnonymousSpectralLanguage,
)
from reference.maf_p0.factorized_latent_field import (
    infer_factorized_latent_field,
)
from reference.maf_p0.wav_io import read_pcm16_channels


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = (
    ROOT / "artifacts/corpus/prepared-r111/ebu-female-speech-en.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-dense-orchestra.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-pink-noise.wav",
)
DEFAULT_JSON = (
    ROOT
    / "experiments/results/latent_source_pattern_field_r160_2026-07-27.json"
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _exact_compressed_array(values: np.ndarray) -> tuple[int, str]:
    minimum = int(np.min(values)) if values.size else 0
    maximum = int(np.max(values)) if values.size else 0
    if -32768 <= minimum and maximum <= 32767:
        kind = "pcm-s16le"
        payload = np.ascontiguousarray(values, dtype="<i2").tobytes()
    else:
        kind = "signed-s32le"
        payload = np.ascontiguousarray(values, dtype="<i4").tobytes()
    return len(zlib.compress(payload, 9)), kind


def _analyze(path: Path, maximum_seconds: float) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_limit = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_limit].copy()
    language = LatentSourceLanguage(
        scales=(512, 2048, 8192),
        origin_hop=512,
        minimum_occurrences=3,
        maximum_components=3,
        maximum_cluster_members=48,
        maximum_lag=12,
        minimum_spectral_similarity=0.94,
        maximum_normalized_correction=0.40,
        consensus_iterations=3,
        similarity_batch_rows=256,
    )
    started = time.perf_counter()
    field = infer_latent_source_pattern_field(source, language=language)
    ledger = pack_latent_field_event_ledger(
        field,
        pair_language=SparseMotifLanguage(
            minimum_occurrences=3,
            maximum_gap_frames=sample_rate * 4,
            gap_bucket_frames=max(1, sample_rate // 100),
        ),
        path_language=SparsePathLanguage(
            minimum_occurrences=3,
            minimum_steps=3,
            maximum_steps=5,
            maximum_gap_frames=sample_rate * 4,
            gap_bucket_frames=max(1, sample_rate // 100),
            maximum_successors_per_step=12,
            maximum_path_candidates=1 << 17,
        ),
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
        for component in field.components
    )
    correction_bytes, correction_storage = _exact_compressed_array(
        field.truth_correction
    )
    # This deliberately small explicit envelope is a proxy record header, not
    # a claim about the final Resonith container.
    proxy_header_bytes = 32 + 16 * len(field.components)
    structured_bytes = (
        proxy_header_bytes
        + basis_bytes
        + ledger.report["selected_event_bytes"]
        + correction_bytes
    )
    selected_bytes = min(independent_bytes, structured_bytes)
    selected_kind = (
        "latent-structured"
        if structured_bytes < independent_bytes
        else "independent-truth"
    )
    source64 = source.astype(np.int64)
    prediction64 = field.prediction.astype(np.int64)
    correction64 = field.truth_correction.astype(np.int64)
    source_energy = float(np.sum(source64.astype(np.float64) ** 2))
    correction_energy = float(
        np.sum(correction64.astype(np.float64) ** 2)
    )
    prediction_energy = float(
        np.sum(prediction64.astype(np.float64) ** 2)
    )
    exact = np.array_equal(field.reconstruction, source64)
    return {
        "id": path.stem,
        "path": str(path),
        "status": "Real PCM / exact structural proxy; not full codec",
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_pcm_bytes": len(source_payload),
        "source_sha256": _sha256_bytes(source_payload),
        "reconstruction_sha256": _sha256_bytes(
            np.ascontiguousarray(field.reconstruction, dtype="<i2").tobytes()
        ),
        "exact_reconstruction": exact,
        "latent_component_count": len(field.components),
        "latent_occurrence_count": sum(
            len(component.occurrences) for component in field.components
        ),
        "explained_energy_fraction": (
            1.0 - correction_energy / source_energy
            if source_energy
            else 1.0
        ),
        "prediction_energy_fraction": (
            prediction_energy / source_energy if source_energy else 0.0
        ),
        "independent_zlib_proxy_bytes": independent_bytes,
        "basis_zlib_bytes": basis_bytes,
        "event_ledger_bytes": ledger.report["selected_event_bytes"],
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
        "selected_kind": selected_kind,
        "selected_proxy_bytes": selected_bytes,
        "selected_saving_percent": (
            100.0 * (independent_bytes - selected_bytes) / independent_bytes
            if independent_bytes
            else 0.0
        ),
        "event_ledger": ledger.report,
        "oracle": field.report,
        "wall_seconds": elapsed,
        "realtime_factor": (
            elapsed / (source.shape[0] / sample_rate)
            if source.shape[0]
            else 0.0
        ),
    }


def _analyze_partial(path: Path, maximum_seconds: float) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_limit = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_limit].copy()
    language = LatentSourceLanguage(
        scales=(512, 2048, 8192),
        origin_hop=512,
        minimum_occurrences=3,
        maximum_components=2,
        maximum_cluster_members=48,
        maximum_lag=12,
        minimum_spectral_similarity=0.94,
        maximum_normalized_correction=0.40,
        consensus_iterations=3,
        similarity_batch_rows=256,
    )
    started = time.perf_counter()
    field = infer_partial_spectrum_latent_field(
        source,
        levels=3,
        language=language,
    )
    event_bytes = 0
    ledger_reports = []
    basis_bytes = 0
    for band in field.bands:
        ledger = pack_latent_field_event_ledger(
            band.field,
            pair_language=SparseMotifLanguage(
                minimum_occurrences=3,
                maximum_gap_frames=max(1, sample_rate * 4 // band.decimation),
                gap_bucket_frames=max(
                    1,
                    sample_rate // 100 // band.decimation,
                ),
            ),
            path_language=SparsePathLanguage(
                minimum_occurrences=3,
                minimum_steps=3,
                maximum_steps=5,
                maximum_gap_frames=max(1, sample_rate * 4 // band.decimation),
                gap_bucket_frames=max(
                    1,
                    sample_rate // 100 // band.decimation,
                ),
                maximum_successors_per_step=12,
                maximum_path_candidates=1 << 17,
            ),
        )
        event_bytes += ledger.report["selected_event_bytes"]
        ledger_reports.append(
            {
                "band_index": band.band_index,
                "decimation": band.decimation,
                **ledger.report,
            }
        )
        basis_bytes += sum(
            len(
                zlib.compress(
                    np.ascontiguousarray(
                        component.basis,
                        dtype="<i2",
                    ).tobytes(),
                    9,
                )
            )
            for component in band.field.components
        )
    elapsed = time.perf_counter() - started
    source_payload = np.ascontiguousarray(source, dtype="<i2").tobytes()
    independent_bytes = len(zlib.compress(source_payload, 9))
    correction_bytes, correction_storage = _exact_compressed_array(
        field.truth_correction
    )
    component_count = field.report["latent_component_count"]
    proxy_header_bytes = 48 + 16 * component_count + 8 * len(field.bands)
    structured_bytes = (
        proxy_header_bytes + basis_bytes + event_bytes + correction_bytes
    )
    selected_bytes = min(independent_bytes, structured_bytes)
    selected_kind = (
        "partial-spectrum-latent"
        if structured_bytes < independent_bytes
        else "independent-truth"
    )
    source64 = source.astype(np.int64)
    source_energy = float(np.sum(source64.astype(np.float64) ** 2))
    correction_energy = float(
        np.sum(field.truth_correction.astype(np.float64) ** 2)
    )
    prediction_energy = float(
        np.sum(field.prediction.astype(np.float64) ** 2)
    )
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / exact partial-spectrum structural proxy; "
            "not full codec"
        ),
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_pcm_bytes": len(source_payload),
        "source_sha256": _sha256_bytes(source_payload),
        "reconstruction_sha256": _sha256_bytes(
            np.ascontiguousarray(field.reconstruction, dtype="<i2").tobytes()
        ),
        "exact_reconstruction": bool(
            np.array_equal(field.reconstruction, source64)
        ),
        "latent_component_count": component_count,
        "latent_occurrence_count": field.report["latent_occurrence_count"],
        "active_band_count": field.report["active_band_count"],
        "explained_energy_fraction": (
            1.0 - correction_energy / source_energy
            if source_energy
            else 1.0
        ),
        "prediction_energy_fraction": (
            prediction_energy / source_energy if source_energy else 0.0
        ),
        "independent_zlib_proxy_bytes": independent_bytes,
        "basis_zlib_bytes": basis_bytes,
        "event_ledger_bytes": event_bytes,
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
        "selected_kind": selected_kind,
        "selected_proxy_bytes": selected_bytes,
        "selected_saving_percent": (
            100.0 * (independent_bytes - selected_bytes) / independent_bytes
            if independent_bytes
            else 0.0
        ),
        "event_ledgers": ledger_reports,
        "oracle": field.report,
        "wall_seconds": elapsed,
        "realtime_factor": (
            elapsed / (source.shape[0] / sample_rate)
            if source.shape[0]
            else 0.0
        ),
    }


def _analyze_factorized(path: Path, maximum_seconds: float) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_limit = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_limit].copy()
    field_language = LatentSourceLanguage(
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
    )
    started = time.perf_counter()
    field = infer_factorized_latent_field(
        source,
        sample_rate=sample_rate,
        factor_language=AnonymousSpectralLanguage(
            fft_samples=1024,
            hop_samples=256,
            factor_count=4,
            iterations=32,
        ),
        field_language=field_language,
    )
    event_bytes = 0
    ledger_reports = []
    basis_bytes = 0
    for factor_index, latent in enumerate(field.fields):
        ledger = pack_latent_field_event_ledger(
            latent,
            pair_language=SparseMotifLanguage(
                minimum_occurrences=3,
                maximum_gap_frames=sample_rate * 4,
                gap_bucket_frames=max(1, sample_rate // 100),
            ),
            path_language=SparsePathLanguage(
                minimum_occurrences=3,
                minimum_steps=3,
                maximum_steps=5,
                maximum_gap_frames=sample_rate * 4,
                gap_bucket_frames=max(1, sample_rate // 100),
                maximum_successors_per_step=12,
                maximum_path_candidates=1 << 17,
            ),
        )
        event_bytes += ledger.report["selected_event_bytes"]
        ledger_reports.append(
            {"factor_index": factor_index, **ledger.report}
        )
        basis_bytes += sum(
            len(
                zlib.compress(
                    np.ascontiguousarray(
                        component.basis,
                        dtype="<i2",
                    ).tobytes(),
                    9,
                )
            )
            for component in latent.components
        )
    elapsed = time.perf_counter() - started
    source_payload = np.ascontiguousarray(source, dtype="<i2").tobytes()
    independent_bytes = len(zlib.compress(source_payload, 9))
    correction_bytes, correction_storage = _exact_compressed_array(
        field.truth_correction
    )
    component_count = field.report["latent_component_count"]
    proxy_header_bytes = 48 + 16 * component_count + 8 * len(field.fields)
    structured_bytes = (
        proxy_header_bytes + basis_bytes + event_bytes + correction_bytes
    )
    selected_bytes = min(independent_bytes, structured_bytes)
    selected_kind = (
        "factorized-latent"
        if structured_bytes < independent_bytes
        else "independent-truth"
    )
    source64 = source.astype(np.int64)
    source_energy = float(np.sum(source64.astype(np.float64) ** 2))
    correction_energy = float(
        np.sum(field.truth_correction.astype(np.float64) ** 2)
    )
    prediction_energy = float(
        np.sum(field.prediction.astype(np.float64) ** 2)
    )
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / anonymous NMF proposer plus exact structural proxy; "
            "not full codec"
        ),
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_pcm_bytes": len(source_payload),
        "source_sha256": _sha256_bytes(source_payload),
        "reconstruction_sha256": _sha256_bytes(
            np.ascontiguousarray(field.reconstruction, dtype="<i2").tobytes()
        ),
        "exact_reconstruction": bool(
            np.array_equal(field.reconstruction, source64)
        ),
        "latent_component_count": component_count,
        "latent_occurrence_count": field.report["latent_occurrence_count"],
        "active_factor_count": field.report["active_factor_count"],
        "explained_energy_fraction": (
            1.0 - correction_energy / source_energy
            if source_energy
            else 1.0
        ),
        "prediction_energy_fraction": (
            prediction_energy / source_energy if source_energy else 0.0
        ),
        "independent_zlib_proxy_bytes": independent_bytes,
        "basis_zlib_bytes": basis_bytes,
        "event_ledger_bytes": event_bytes,
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
        "selected_kind": selected_kind,
        "selected_proxy_bytes": selected_bytes,
        "selected_saving_percent": (
            100.0 * (independent_bytes - selected_bytes) / independent_bytes
            if independent_bytes
            else 0.0
        ),
        "event_ledgers": ledger_reports,
        "oracle": field.report,
        "wall_seconds": elapsed,
        "realtime_factor": (
            elapsed / (source.shape[0] / sample_rate)
            if source.shape[0]
            else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
    )
    parser.add_argument("--maximum-seconds", type=float, default=12.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument(
        "--mode",
        choices=("whole", "partial", "factorized", "both"),
        default="both",
    )
    arguments = parser.parse_args()

    results = []
    for path in arguments.inputs:
        print(f"R-160 analyzing {path.name}", flush=True)
        modes = (
            ("whole", _analyze),
            ("partial", _analyze_partial),
            ("factorized", _analyze_factorized),
        )
        for mode, analyzer in modes:
            if arguments.mode not in (mode, "both"):
                continue
            result = analyzer(path.resolve(), arguments.maximum_seconds)
            result["analysis_mode"] = mode
            results.append(result)
            print(
                f"  mode={mode} "
                f"components={result['latent_component_count']} "
                f"occurrences={result['latent_occurrence_count']} "
                f"proxy_saving={result['structured_saving_percent']:.3f}% "
                f"wall={result['wall_seconds']:.3f}s",
                flush=True,
            )
    payload = {
        "schema": "resonith-r160-real-structural-proxy-1",
        "status": "Real PCM / Fast diagnostic / Proxy / not Opus-comparable",
        "language": {
            "scales": [512, 2048, 8192],
            "origin_hop": 512,
            "origin_policy": (
                "overlapping diagnostic lattice; not exhaustive every-sample "
                "Foundry search"
            ),
        },
        "results": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {arguments.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
