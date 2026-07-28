"""R-176 decoder-in-loop CBF1 predictor plus one final lapped Truth."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np

from .causal_basis_field import (
    CausalBasisFieldCandidate,
    encode_causal_basis_field_from_mft1,
    parse_causal_basis_field,
)
from .causal_law_grammar import CausalLawGrammarLanguage
from .lapped_oracle import (
    LappedEncodeResult,
    analyze_lapped_source,
    encode_lapped_analysis,
    encode_lapped_stream,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf
from .warp_dictionary import (
    WarpDictionaryPrediction,
    fit_warp_dictionary_prediction,
)
from .coherent_partial_bundle import CoherentPartialLanguage
from .partial_basis_trajectory import (
    PartialBasisTrajectoryPrediction,
    fit_partial_basis_trajectory_prediction,
)


@dataclass(frozen=True)
class CausalBasisTruthCandidate:
    """Complete CBF1/MFT1 plus Truth candidates and direct fallback."""

    cbf_payload: bytes
    mft1_payload: bytes
    reconstruction: np.ndarray
    selected_payload: bytes
    selected_reconstruction: np.ndarray
    selected_kind: str
    predictor: WarpDictionaryPrediction | PartialBasisTrajectoryPrediction
    transport: CausalBasisFieldCandidate
    residual: LappedEncodeResult
    baseline: LappedEncodeResult
    report: dict


def _pack_complete(
    *,
    source_shape: tuple[int, int],
    sample_rate: int,
    predictor_type: str,
    predictor_payload: bytes,
    residual_payload: bytes,
) -> bytes:
    return pack_rsc1(
        (
            RSC1Section(
                "CONF",
                pack_conf(
                    StreamConfig(
                        source_shape[0],
                        1,
                        source_shape[1],
                    )
                ),
            ),
            RSC1Section(predictor_type, predictor_payload),
            RSC1Section("MRI1", residual_payload),
        ),
        profile=0,
        level=7,
        timebase_hz=sample_rate,
    )


def _decode_predictor(
    predictor_type: bytes,
    predictor_payload: bytes,
    *,
    native_decoder,
) -> np.ndarray:
    if predictor_type == b"CBF1":
        info = parse_causal_basis_field(predictor_payload)
        return native_decoder.decode_maf_typed(info.mft1_payload).samples
    if predictor_type == b"MFT1":
        return native_decoder.decode_maf_typed(predictor_payload).samples
    raise ValueError("unknown causal Basis predictor section")


def decode_causal_basis_truth_candidate(
    payload: bytes,
    *,
    native_decoder,
) -> tuple[int, np.ndarray]:
    """Independently decode CBF1 or MFT1 prediction plus one lapped Truth."""

    info = parse_rsc1(payload)
    if info.profile != 0 or info.level != 7:
        raise ValueError("unsupported Causal Basis Truth profile")
    sections = {
        bytes(section.type_code): section.payload
        for section in info.sections
    }
    predictor_types = set(sections) & {b"CBF1", b"MFT1"}
    if (
        set(sections) - predictor_types != {b"CONF", b"MRI1"}
        or len(predictor_types) != 1
    ):
        raise ValueError("non-canonical Causal Basis Truth sections")
    config = unpack_conf(sections[b"CONF"])
    predictor_type = next(iter(predictor_types))
    prediction = _decode_predictor(
        predictor_type,
        sections[predictor_type],
        native_decoder=native_decoder,
    )
    residual = native_decoder.decode_lapped(sections[b"MRI1"])
    if (
        prediction.shape != residual.samples.shape
        or prediction.shape
        != (config.sample_count, config.output_channels)
        or residual.sample_rate != info.timebase_hz
    ):
        raise ValueError("Causal Basis Truth section layout mismatch")
    output = np.clip(
        prediction.astype(np.int32)
        + residual.samples.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    output.flags.writeable = False
    return info.timebase_hz, output


def encode_causal_basis_truth_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    coefficients_per_frame: int,
    half_window: int = 512,
    band_count: int = 24,
    block_samples: int = 1024,
    maximum_bases: int = 64,
    maximum_instances: int = 4096,
    maximum_normalized_error: float = 8.0e-2,
    predictor_backend: str = "warp-dictionary",
    partial_language: CoherentPartialLanguage | None = None,
    maximum_trajectory_observations: int = 32,
    minimum_hold_frames: int = 4,
    phase_candidates: int = 16,
    boundary_taper_samples: int = 32,
    piecewise_laws: bool = True,
    track_observation_phase: bool = False,
    basis_waveform_mode: str = "observed",
    grammar_language: CausalLawGrammarLanguage = (
        CausalLawGrammarLanguage(
            maximum_rules=32,
            maximum_candidate_pairs_per_round=8,
        )
    ),
) -> CausalBasisTruthCandidate:
    """Fit, transport, decode, and byte-select CBF1 plus one final Truth."""

    source = np.ascontiguousarray(samples, dtype=np.int16)
    if source.ndim != 2 or source.shape[0] == 0:
        raise TypeError("Causal Basis Truth requires frame-major PCM16")
    if predictor_backend == "warp-dictionary":
        predictor = fit_warp_dictionary_prediction(
            source,
            sample_rate,
            native_decoder=native_decoder,
            block_samples=block_samples,
            maximum_bases=maximum_bases,
            maximum_instances=maximum_instances,
            maximum_normalized_error=maximum_normalized_error,
        )
    elif predictor_backend == "partial-basis":
        predictor = fit_partial_basis_trajectory_prediction(
            source,
            sample_rate,
            native_decoder=native_decoder,
            language=(
                partial_language
                if partial_language is not None
                else CoherentPartialLanguage()
            ),
            maximum_trajectory_observations=(
                maximum_trajectory_observations
            ),
            minimum_hold_frames=minimum_hold_frames,
            phase_candidates=phase_candidates,
            boundary_taper_samples=boundary_taper_samples,
            piecewise_laws=piecewise_laws,
            track_observation_phase=track_observation_phase,
            basis_waveform_mode=basis_waveform_mode,
            maximum_instances=maximum_instances,
            maximum_normalized_error=maximum_normalized_error,
        )
    else:
        raise ValueError("unknown Causal Basis predictor backend")
    transport = encode_causal_basis_field_from_mft1(
        predictor.payload,
        grammar_language=grammar_language,
    )
    cbf_prediction = _decode_predictor(
        b"CBF1",
        transport.cbf_payload,
        native_decoder=native_decoder,
    )
    if not np.array_equal(cbf_prediction, predictor.reconstruction):
        raise RuntimeError("CBF1 and native MFT1 predictions differ")

    difference = (
        source.astype(np.int32) - cbf_prediction.astype(np.int32)
    )
    clipped_residual = np.clip(
        difference,
        -32768,
        32767,
    ).astype(np.int16)
    baseline = encode_lapped_stream(
        source,
        sample_rate,
        coefficients_per_frame=coefficients_per_frame,
        half_window=half_window,
        band_count=band_count,
        entropy_backend="bounded",
        transform_backend="fixed",
        density_backend="adaptive",
        native_analyzer=native_decoder,
        native_decoder=native_decoder,
    )
    baseline_error = (
        source.astype(np.int64) - baseline.reconstruction.astype(np.int64)
    )
    baseline_sse = int(np.sum(baseline_error * baseline_error))
    residual_analysis = analyze_lapped_source(
        clipped_residual,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_decoder,
    )
    residual = encode_lapped_analysis(
        residual_analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
        native_decoder=native_decoder,
    )
    reconstruction = np.clip(
        cbf_prediction.astype(np.int32)
        + residual.reconstruction.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    candidate_error = (
        source.astype(np.int64) - reconstruction.astype(np.int64)
    )
    candidate_sse = int(np.sum(candidate_error * candidate_error))
    cbf_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=sample_rate,
        predictor_type="CBF1",
        predictor_payload=transport.cbf_payload,
        residual_payload=residual.payload,
    )
    mft1_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=sample_rate,
        predictor_type="MFT1",
        predictor_payload=predictor.payload,
        residual_payload=residual.payload,
    )
    decoded_rate, decoded = decode_causal_basis_truth_candidate(
        cbf_complete,
        native_decoder=native_decoder,
    )
    if (
        decoded_rate != sample_rate
        or not np.array_equal(decoded, reconstruction)
    ):
        raise RuntimeError("CBF1 plus Truth independent decode failed")

    eligible = []
    if candidate_sse <= baseline_sse:
        eligible.extend(
            (
                ("cbf1-truth", cbf_complete, reconstruction),
                ("mft1-truth", mft1_complete, reconstruction),
            )
        )
    eligible.append(
        ("truth-fallback", baseline.payload, baseline.reconstruction)
    )
    selected_kind, selected_payload, selected_reconstruction = min(
        eligible,
        key=lambda item: (len(item[1]), item[0]),
    )
    reconstruction.flags.writeable = False
    selected_reconstruction.flags.writeable = False
    return CausalBasisTruthCandidate(
        cbf_payload=cbf_complete,
        mft1_payload=mft1_complete,
        reconstruction=reconstruction,
        selected_payload=selected_payload,
        selected_reconstruction=selected_reconstruction,
        selected_kind=selected_kind,
        predictor=predictor,
        transport=transport,
        residual=residual,
        baseline=baseline,
        report={
            "schema": "resonith-r176-causal-basis-truth-candidate-1",
            "status": "complete-byte fast candidate; full R-118 pending",
            "semantic_source_classes": False,
            "predictor_backend": predictor_backend,
            "cbf1_truth_bytes": len(cbf_complete),
            "mft1_truth_bytes": len(mft1_complete),
            "truth_fallback_bytes": len(baseline.payload),
            "candidate_sse": candidate_sse,
            "truth_fallback_sse": baseline_sse,
            "selected_kind": selected_kind,
            "selected_bytes": len(selected_payload),
            "selected_sha256": hashlib.sha256(
                selected_payload
            ).hexdigest(),
            "residual_bytes": len(residual.payload),
            "residual_clip_count": int(np.count_nonzero(
                (difference < -32768) | (difference > 32767)
            )),
            "predictor": predictor.report,
            "transport": transport.report,
            "independent_decode": True,
        },
    )
