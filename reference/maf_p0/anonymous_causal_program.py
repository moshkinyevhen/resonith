"""R-179 minimum-description compiler for anonymous causal MAF programs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools

import numpy as np

from .causal_basis_field import (
    encode_causal_basis_field_from_mft1,
    parse_causal_basis_field,
)
from .coherent_partial_bundle import (
    CausalLaneField,
    CoherentPartialLanguage,
    infer_causal_lane_field,
)
from .lapped_oracle import (
    LappedEncodeResult,
    analyze_lapped_source,
    encode_lapped_analysis,
    encode_lapped_stream,
)
from .maf_typed import (
    PERIODIC_BASIS_EXCITATION,
    STOCHASTIC_EXCITATION,
    MafBasisInstance,
    MafBasisWarpInstance,
    MafMix,
    MafSourceFilter,
    MafStochastic,
    MafTransient,
    pack_maf_typed,
    parse_maf_typed,
)
from .maf_typed_candidate import fit_maf_typed_prediction
from .morphing_partial_field import (
    MorphingPartialLanguage,
    fit_morphing_partial_prediction,
)
from .partial_basis_trajectory import (
    PartialBasisTrajectoryPrediction,
    fit_partial_basis_trajectory_prediction,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf
from .warp_dictionary import (
    WarpDictionaryPrediction,
    fit_warp_dictionary_prediction,
)


@dataclass(frozen=True)
class AnonymousCausalProgramLanguage:
    """Finite R-179 column union and exact-subset search bounds."""

    partial_language: CoherentPartialLanguage = CoherentPartialLanguage()
    morphing_language: MorphingPartialLanguage = MorphingPartialLanguage()
    maximum_trajectory_observations: int = 256
    minimum_hold_frames: int = 3
    phase_candidates: int = 16
    maximum_normalized_error: float = 0.65
    dictionary_block_samples: int = 512
    dictionary_maximum_bases: int = 32
    dictionary_maximum_instances: int = 1024
    stochastic_segment_milliseconds: float = 240.0
    maximum_exact_columns: int = 8
    residual_budget_divisors: tuple[int, ...] = (1, 2)
    enabled_families: tuple[str, ...] = (
        "coherent",
        "inharmonic",
        "transient",
        "stochastic",
    )

    def __post_init__(self) -> None:
        allowed = {"coherent", "inharmonic", "transient", "stochastic"}
        if (
            not set(self.enabled_families) <= allowed
            or len(set(self.enabled_families)) != len(self.enabled_families)
            or not 2 <= self.maximum_trajectory_observations <= 256
            or not 1 <= self.minimum_hold_frames <= 64
            or not 4 <= self.phase_candidates <= 256
            or not 0.0 < self.maximum_normalized_error <= 4.0
            or not 64 <= self.dictionary_block_samples <= 16384
            or not 1 <= self.dictionary_maximum_bases <= 256
            or not 1 <= self.dictionary_maximum_instances <= 4096
            or not 20.0 <= self.stochastic_segment_milliseconds <= 5000.0
            or not 1 <= self.maximum_exact_columns <= 12
            or not self.residual_budget_divisors
            or any(value <= 0 for value in self.residual_budget_divisors)
        ):
            raise ValueError("invalid anonymous causal program language")


@dataclass(frozen=True)
class AnonymousProgramColumn:
    """One decoder-verified anonymous causal column with owned support."""

    family: str
    ownership: str
    payload: bytes
    reconstruction: np.ndarray
    report: dict


@dataclass(frozen=True)
class AnonymousCausalProgramCandidate:
    """One complete selected program, one final Truth, and direct fallback."""

    payload: bytes
    reconstruction: np.ndarray
    selected_payload: bytes
    selected_reconstruction: np.ndarray
    selected_kind: str
    baseline: LappedEncodeResult
    columns: tuple[AnonymousProgramColumn, ...]
    causal_field: CausalLaneField
    report: dict


def _sum_static_mixes(
    sources,
) -> MafMix:
    output_channels = sources[0].output_channels
    emitter_count = sum(item.emitter_count for item in sources)
    rows = []
    for output in range(output_channels):
        row = [0] * emitter_count
        offset = 0
        for item in sources:
            if (
                len(item.mixes) != 1
                or item.mixes[0].start != 0
                or item.mixes[0].end != item.total_frames
            ):
                raise ValueError(
                    "anonymous columns require one full-lifetime static mix"
                )
            source_row = item.mixes[0].matrix_q15[output]
            row[offset : offset + item.emitter_count] = source_row
            offset += item.emitter_count
        rows.append(tuple(row))
    return MafMix(0, 0, tuple(rows))


def _merge_mft1_payloads(payloads: tuple[bytes, ...]) -> bytes:
    """Merge independent anonymous predictors into one additive MFT1 program."""

    if not payloads:
        raise ValueError("an anonymous program requires at least one column")
    sources = tuple(parse_maf_typed(payload) for payload in payloads)
    first = sources[0]
    if any(
        (
            item.sample_rate,
            item.total_frames,
            item.output_channels,
        )
        != (
            first.sample_rate,
            first.total_frames,
            first.output_channels,
        )
        for item in sources[1:]
    ):
        raise ValueError("anonymous program columns have incompatible layouts")
    emitter_count = sum(item.emitter_count for item in sources)
    if emitter_count > 64:
        raise ValueError("anonymous program exceeds the MFT1 emitter bound")

    filters = []
    stochastic = []
    bases = []
    source_filters = []
    transients = []
    basis_instances = []
    basis_warp_instances = []
    emitter_offset = 0
    filter_offset = 0
    stochastic_offset = 0
    basis_offset = 0
    for item in sources:
        filters.extend(item.filters)
        stochastic.extend(
            MafStochastic(
                (
                    None
                    if field.emitter_id is None
                    else field.emitter_id + emitter_offset
                ),
                field.start,
                field.end,
                field.gain_q15,
            )
            for field in item.stochastic
        )
        bases.extend(item.bases)
        for source in item.sources:
            filter_id = source.filter_id
            if filter_id != 0xFFFF:
                filter_id += filter_offset
            reference_id = source.reference_id
            if reference_id is not None:
                if source.excitation == STOCHASTIC_EXCITATION:
                    reference_id += stochastic_offset
                elif source.excitation == PERIODIC_BASIS_EXCITATION:
                    reference_id += basis_offset
            source_filters.append(
                MafSourceFilter(
                    emitter_id=source.emitter_id + emitter_offset,
                    filter_id=filter_id,
                    excitation=source.excitation,
                    reference_id=reference_id,
                    start=source.start,
                    end=source.end,
                    gain_q15=source.gain_q15,
                    phase_origin_q32=source.phase_origin_q32,
                    phase_increment_q32=source.phase_increment_q32,
                )
            )
        transients.extend(
            MafTransient(
                emitter_id=item_transient.emitter_id + emitter_offset,
                onset=item_transient.onset,
                gain_q15=item_transient.gain_q15,
                samples=item_transient.samples,
            )
            for item_transient in item.transients
        )
        basis_instances.extend(
            MafBasisInstance(
                emitter_id=instance.emitter_id + emitter_offset,
                basis_id=instance.basis_id + basis_offset,
                start=instance.start,
                gain_q15=instance.gain_q15,
                source_offset=instance.source_offset,
                sample_count=instance.sample_count,
                circular=instance.circular,
                end_gain_q15=instance.end_gain_q15,
                reverse=instance.reverse,
            )
            for instance in item.basis_instances
        )
        basis_warp_instances.extend(
            MafBasisWarpInstance(
                emitter_id=instance.emitter_id + emitter_offset,
                basis_id=instance.basis_id + basis_offset,
                start=instance.start,
                sample_count=instance.sample_count,
                source_position_q16=instance.source_position_q16,
                source_step_q16=instance.source_step_q16,
                gain_q15=instance.gain_q15,
                circular=instance.circular,
                end_source_step_q16=instance.end_source_step_q16,
                end_gain_q15=instance.end_gain_q15,
            )
            for instance in item.basis_warp_instances
        )
        emitter_offset += item.emitter_count
        filter_offset += len(item.filters)
        stochastic_offset += len(item.stochastic)
        basis_offset += len(item.bases)

    mix = _sum_static_mixes(sources)
    mix = MafMix(0, first.total_frames, mix.matrix_q15)
    return pack_maf_typed(
        sample_rate=first.sample_rate,
        total_frames=first.total_frames,
        render_quantum=min(item.render_quantum for item in sources),
        output_channels=first.output_channels,
        emitter_count=emitter_count,
        stream_seed=0,
        filters=tuple(filters),
        stochastic=tuple(stochastic),
        sources=tuple(source_filters),
        transients=tuple(transients),
        mixes=(mix,),
        bases=tuple(bases),
        basis_instances=tuple(basis_instances),
        basis_warp_instances=tuple(basis_warp_instances),
        declared_operations_per_frame=min(
            0xFFFF_FFFF,
            sum(item.declared_operations_per_frame for item in sources)
            + first.output_channels * (2 * emitter_count + 2),
        ),
    )


def _pack_complete(
    *,
    source_shape: tuple[int, int],
    sample_rate: int,
    predictor_type: str,
    predictor_payload: bytes,
    truth_payload: bytes,
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
            RSC1Section("MRI1", truth_payload),
        ),
        profile=0,
        level=8,
        timebase_hz=sample_rate,
    )


def decode_anonymous_causal_program(
    payload: bytes,
    *,
    native_decoder,
) -> tuple[int, np.ndarray]:
    """Independently decode one R-179 research program and final Truth."""

    info = parse_rsc1(payload)
    if info.profile != 0 or info.level != 8:
        raise ValueError("unsupported anonymous causal program profile")
    sections = {
        bytes(section.type_code): section.payload
        for section in info.sections
    }
    predictor_types = set(sections) & {b"CBF1", b"MFT1"}
    if (
        set(sections) - predictor_types != {b"CONF", b"MRI1"}
        or len(predictor_types) != 1
    ):
        raise ValueError("non-canonical anonymous causal program sections")
    config = unpack_conf(sections[b"CONF"])
    predictor_type = next(iter(predictor_types))
    predictor_payload = sections[predictor_type]
    if predictor_type == b"CBF1":
        predictor_payload = parse_causal_basis_field(
            predictor_payload
        ).mft1_payload
    prediction = native_decoder.decode_maf_typed(predictor_payload)
    truth = native_decoder.decode_lapped(sections[b"MRI1"])
    if (
        prediction.sample_rate != info.timebase_hz
        or truth.sample_rate != info.timebase_hz
        or prediction.samples.shape != truth.samples.shape
        or prediction.samples.shape
        != (config.sample_count, config.output_channels)
    ):
        raise ValueError("anonymous causal program layout mismatch")
    output = np.clip(
        prediction.samples.astype(np.int32)
        + truth.samples.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    output.flags.writeable = False
    return info.timebase_hz, output


def _lane_pcm(lane: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(
        np.clip(lane, -32768, 32767).astype(np.int16)
    )


def _build_columns(
    source: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    causal_field: CausalLaneField,
    language: AnonymousCausalProgramLanguage,
) -> tuple[AnonymousProgramColumn, ...]:
    columns = []
    if "coherent" in language.enabled_families:
        morphing_prediction = fit_morphing_partial_prediction(
            source,
            sample_rate,
            native_decoder=native_decoder,
            partial_language=language.partial_language,
            language=language.morphing_language,
        )
        if morphing_prediction.report["partial_instance_count"]:
            columns.append(
                AnonymousProgramColumn(
                    "coherent-morphing-partials",
                    "coherent",
                    morphing_prediction.payload,
                    morphing_prediction.reconstruction,
                    morphing_prediction.report,
                )
            )
        for basis_mode, phase_tracking in itertools.product(
            ("observed", "analytic"),
            (False, True),
        ):
            prediction: PartialBasisTrajectoryPrediction = (
                fit_partial_basis_trajectory_prediction(
                    source,
                    sample_rate,
                    native_decoder=native_decoder,
                    language=language.partial_language,
                    maximum_trajectory_observations=(
                        language.maximum_trajectory_observations
                    ),
                    minimum_hold_frames=language.minimum_hold_frames,
                    phase_candidates=language.phase_candidates,
                    taper_boundaries=True,
                    piecewise_laws=True,
                    track_observation_phase=phase_tracking,
                    basis_waveform_mode=basis_mode,
                    maximum_normalized_error=(
                        language.maximum_normalized_error
                    ),
                )
            )
            if prediction.report["selected_instance_count"]:
                columns.append(
                    AnonymousProgramColumn(
                        (
                            f"coherent-{basis_mode}-phase-locked"
                            if phase_tracking
                            else f"coherent-{basis_mode}-continuous"
                        ),
                        "coherent",
                        prediction.payload,
                        prediction.reconstruction,
                        prediction.report,
                    )
                )

    dictionary_lanes = (
        ("inharmonic", causal_field.deterministic_inharmonic),
        ("transient", causal_field.sparse_transient),
    )
    for family, lane in dictionary_lanes:
        if family not in language.enabled_families:
            continue
        prediction: WarpDictionaryPrediction = (
            fit_warp_dictionary_prediction(
                _lane_pcm(lane),
                sample_rate,
                native_decoder=native_decoder,
                block_samples=language.dictionary_block_samples,
                maximum_bases=language.dictionary_maximum_bases,
                maximum_instances=language.dictionary_maximum_instances,
                maximum_normalized_error=(
                    language.maximum_normalized_error
                ),
            )
        )
        if prediction.report["instance_count"]:
            columns.append(
                AnonymousProgramColumn(
                    family,
                    family,
                    prediction.payload,
                    prediction.reconstruction,
                    prediction.report,
                )
            )

    if "stochastic" in language.enabled_families:
        prediction = fit_maf_typed_prediction(
            _lane_pcm(causal_field.stochastic),
            sample_rate,
            native_decoder=native_decoder,
            segment_milliseconds=(
                language.stochastic_segment_milliseconds
            ),
            rate_coefficients_per_frame=64,
            allowed_modes=(STOCHASTIC_EXCITATION,),
        )
        if prediction.report["source_lifetime_count"]:
            columns.append(
                AnonymousProgramColumn(
                    "stochastic",
                    "stochastic",
                    prediction.payload,
                    prediction.reconstruction,
                    prediction.report,
                )
            )
    return tuple(columns)


def _pareto_rows(rows: list[dict]) -> list[dict]:
    frontier = []
    for row in sorted(rows, key=lambda item: (item["bytes"], item["sse"])):
        if any(
            other["bytes"] <= row["bytes"]
            and other["sse"] <= row["sse"]
            and (
                other["bytes"] < row["bytes"]
                or other["sse"] < row["sse"]
            )
            for other in rows
        ):
            continue
        frontier.append(row)
    return frontier


def compile_anonymous_causal_program(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    coefficients_per_frame: int,
    half_window: int = 512,
    band_count: int = 24,
    language: AnonymousCausalProgramLanguage = (
        AnonymousCausalProgramLanguage()
    ),
) -> AnonymousCausalProgramCandidate:
    """Compile and exact-subset RDO one multi-mechanism anonymous program."""

    source = np.ascontiguousarray(samples, dtype=np.int16)
    if (
        source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("anonymous causal program requires frame-major PCM16")
    causal_field = infer_causal_lane_field(
        source,
        sample_rate=sample_rate,
        language=language.partial_language,
    )
    columns = _build_columns(
        source,
        sample_rate,
        native_decoder=native_decoder,
        causal_field=causal_field,
        language=language,
    )
    if len(columns) > language.maximum_exact_columns:
        raise ValueError("anonymous causal program exceeds exact column bound")

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
        source.astype(np.int64)
        - baseline.reconstruction.astype(np.int64)
    )
    baseline_sse = int(np.sum(baseline_error * baseline_error))
    tested_rows = []
    complete_options = []
    budgets = sorted({
        max(1, coefficients_per_frame // divisor)
        for divisor in language.residual_budget_divisors
    } | {coefficients_per_frame})

    for subset_size in range(1, len(columns) + 1):
        for indices in itertools.combinations(range(len(columns)), subset_size):
            subset = tuple(columns[index] for index in indices)
            if len({item.ownership for item in subset}) != len(subset):
                continue
            mft1_payload = _merge_mft1_payloads(
                tuple(item.payload for item in subset)
            )
            predictor = native_decoder.decode_maf_typed(
                mft1_payload
            ).samples
            predictor_type = "MFT1"
            predictor_payload = mft1_payload
            try:
                transport = encode_causal_basis_field_from_mft1(
                    mft1_payload
                )
            except ValueError:
                transport = None
            if (
                transport is not None
                and len(transport.cbf_payload) < len(predictor_payload)
            ):
                predictor_type = "CBF1"
                predictor_payload = transport.cbf_payload
            difference = source.astype(np.int32) - predictor.astype(np.int32)
            residual_pcm = np.clip(
                difference,
                -32768,
                32767,
            ).astype(np.int16)
            residual_analysis = analyze_lapped_source(
                residual_pcm,
                sample_rate,
                half_window=half_window,
                band_count=band_count,
                transform_backend="fixed",
                native_analyzer=native_decoder,
            )
            for budget in budgets:
                residual = encode_lapped_analysis(
                    residual_analysis,
                    coefficients_per_frame=budget,
                    entropy_backend="bounded",
                    density_backend="adaptive",
                    selection_backend="energy",
                    native_decoder=native_decoder,
                )
                reconstruction = np.clip(
                    predictor.astype(np.int32)
                    + residual.reconstruction.astype(np.int32),
                    -32768,
                    32767,
                ).astype(np.int16)
                error = (
                    source.astype(np.int64)
                    - reconstruction.astype(np.int64)
                )
                sse = int(np.sum(error * error))
                payload = _pack_complete(
                    source_shape=source.shape,
                    sample_rate=sample_rate,
                    predictor_type=predictor_type,
                    predictor_payload=predictor_payload,
                    truth_payload=residual.payload,
                )
                row = {
                    "families": [item.family for item in subset],
                    "residual_budget": budget,
                    "predictor_type": predictor_type.lower(),
                    "program_bytes": len(predictor_payload),
                    "truth_bytes": len(residual.payload),
                    "bytes": len(payload),
                    "sse": sse,
                    "sse_ratio": (
                        sse / baseline_sse if baseline_sse else 0.0
                    ),
                    "residual_clip_count": int(np.count_nonzero(
                        (difference < -32768) | (difference > 32767)
                    )),
                }
                tested_rows.append(row)
                complete_options.append(
                    (row, payload, reconstruction)
                )

    quality_options = [
        item
        for item in complete_options
        if item[0]["sse"] <= baseline_sse
    ]
    best_program = min(
        quality_options or complete_options,
        key=lambda item: (
            item[0]["bytes"] if quality_options else item[0]["sse"],
            item[0]["sse"],
            tuple(item[0]["families"]),
        ),
        default=None,
    )
    admitted = bool(
        best_program is not None
        and best_program[0]["bytes"] < len(baseline.payload)
        and best_program[0]["sse"] <= baseline_sse
    )
    if admitted:
        selected_row, selected_payload, selected_reconstruction = best_program
        selected_kind = "anonymous-causal-program"
    else:
        selected_row = None if best_program is None else best_program[0]
        selected_payload = baseline.payload
        selected_reconstruction = baseline.reconstruction
        selected_kind = "truth-fallback"

    if best_program is not None:
        decoded_rate, decoded = decode_anonymous_causal_program(
            best_program[1],
            native_decoder=native_decoder,
        )
        if (
            decoded_rate != sample_rate
            or not np.array_equal(decoded, best_program[2])
        ):
            raise RuntimeError(
                "anonymous causal program independent decode failed"
            )
        program_payload = best_program[1]
        program_reconstruction = best_program[2]
    else:
        program_payload = b""
        program_reconstruction = np.zeros_like(source)

    program_reconstruction.flags.writeable = False
    selected_reconstruction.flags.writeable = False
    return AnonymousCausalProgramCandidate(
        payload=program_payload,
        reconstruction=program_reconstruction,
        selected_payload=selected_payload,
        selected_reconstruction=selected_reconstruction,
        selected_kind=selected_kind,
        baseline=baseline,
        columns=columns,
        causal_field=causal_field,
        report={
            "schema": "resonith-r179-anonymous-causal-program-1",
            "status": "decoder-in-loop exact-subset fast gate; R-118 pending",
            "semantic_source_classes": False,
            "objective": (
                "complete program plus one final Truth bytes and decoded SSE"
            ),
            "column_families": [item.family for item in columns],
            "column_ownership": [item.ownership for item in columns],
            "column_count": len(columns),
            "tested_subset_count": len({
                tuple(row["families"])
                for row in tested_rows
            }),
            "tested_candidate_count": len(tested_rows),
            "baseline_bytes": len(baseline.payload),
            "baseline_sse": baseline_sse,
            "best_program": selected_row,
            "selected_kind": selected_kind,
            "selected_bytes": len(selected_payload),
            "selected_sha256": hashlib.sha256(
                selected_payload
            ).hexdigest(),
            "pareto_frontier": _pareto_rows(tested_rows),
            "tested_candidates": tested_rows,
            "one_final_mixture_truth": True,
            "independent_decode": best_program is not None,
            "causal_field": causal_field.report,
        },
    )
