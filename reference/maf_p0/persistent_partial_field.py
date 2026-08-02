"""R-215 anonymous persistent multi-partial predictor and complete Truth RDO.

The module is an encoder-side research implementation. It consumes the
admitted R-191 path identity, lowers independent channel lanes through the
existing MFT1 type-8 decoder language, and lets actual packed bytes plus the
one final decoded Truth decide whether any lane survives.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import itertools
import math
import time

import numpy as np

from .causal_basis_field import encode_causal_basis_field_from_mft1
from .causal_basis_truth_candidate import (
    _pack_complete,
    decode_causal_basis_truth_candidate,
)
from .complex_partial_analyzer import (
    ComplexPartialAnalyzerManifest,
    ComplexPartialObservation,
    ComplexPartialObservationSet,
    observe_complex_partials,
)
from .lapped_oracle import encode_lapped_stream
from .maf_typed import (
    MAX_WARP_INSTANCE_SAMPLES,
    MAX_WARP_STEP_Q16,
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    _warp_source_position_q16,
    pack_maf_typed,
    parse_maf_typed,
)
from .partial_graph_fixed import (
    LOCALLY_RESOLVABLE,
    PHASE_USABLE,
    NativePartialGraph,
    PathRecord,
    make_manifest,
    make_observation,
    make_path_manifest,
    make_resolution,
)


COSINE_BASIS_LENGTHS = (16, 32, 64, 128, 256)
COSINE_BASIS_PCM16LE_SHA256 = {
    16: "11989292026ed130c52b9b3be058460c2de11eece611e5639d410f93a2e96396",
    32: "6ed6af33dae59d32fa8bfc18e41131071c68bf2107dc7074255d20b8e5a7fa10",
    64: "efb3f430e8eaa5f72eaca0ab2ab1b364c8b3cb44574c574f0e75a530fdf3adc7",
    128: "d56f0330e8f280bc5e2efe5f7d27fb304fd45a9e4abd7270d86a2ef87fd65136",
    256: "da8b1b6cfbb6840806397707bec13084a272d2746628f0e61acd96cd4c372e7c",
}


def _frozen_cosine_basis(length: int) -> tuple[int, ...]:
    samples = tuple(
        max(
            -32767,
            min(
                32767,
                round(math.cos(2.0 * math.pi * index / length) * 32767),
            ),
        )
        for index in range(length)
    )
    payload = np.asarray(samples, dtype="<i2").tobytes()
    if hashlib.sha256(payload).hexdigest() != COSINE_BASIS_PCM16LE_SHA256[length]:
        raise RuntimeError("frozen S11 cosine table identity mismatch")
    return samples


COSINE_BASES = {
    length: _frozen_cosine_basis(length)
    for length in COSINE_BASIS_LENGTHS
}
_U32 = 1 << 32


@dataclass(frozen=True)
class PersistentPartialLanguage:
    """Finite encoder search and lowering bounds for the frozen S11 field."""

    analyzer: ComplexPartialAnalyzerManifest = ComplexPartialAnalyzerManifest()
    protected_band_upper_hz: tuple[int, ...] = (250, 1000, 4000, 12000)
    maximum_edge_records: int = 1_000_000
    maximum_path_records: int = 256
    maximum_path_entries: int = 500_000
    maximum_path_work_units: int = 250_000_000
    maximum_lane_observations: int = 128
    maximum_channel_lanes: int = 64
    maximum_placements: int = 4096
    maximum_rdo_lanes: int = 6
    exact_subset_lane_limit: int = 4
    frequency_error_floor_hz: float = 2.0
    frequency_uncertainty_scale: float = 3.0
    phase_error_floor_radians: float = 0.20
    phase_uncertainty_scale: float = 3.0
    phase_fit_weight_floor_radians: float = 0.01
    phase_fit_regularization_weight: int = 1
    phase_fit_condition_shift: int = 20
    phase_fit_accumulator_bits: int = 512
    gain_relative_error: float = 0.18
    gain_error_floor: float = 8.0
    gain_uncertainty_scale: float = 3.0

    def __post_init__(self) -> None:
        if (
            not 1 <= self.maximum_path_records <= 1024
            or not 3 <= self.maximum_lane_observations <= 4096
            or not 1 <= self.maximum_channel_lanes <= 64
            or not 1 <= self.maximum_placements <= 4096
            or not 1 <= self.maximum_rdo_lanes <= self.maximum_channel_lanes
            or not 1 <= self.exact_subset_lane_limit <= 20
            or self.frequency_error_floor_hz <= 0.0
            or not 0.0 < self.phase_error_floor_radians <= math.pi
            or not 0.0 < self.phase_fit_weight_floor_radians <= 0.25
            or not 1 <= self.phase_fit_regularization_weight <= 16
            or not 8 <= self.phase_fit_condition_shift <= 30
            or not 128 <= self.phase_fit_accumulator_bits <= 1024
            or not 0.0 < self.gain_relative_error <= 1.0
        ):
            raise ValueError("invalid R-215 persistent-partial language")


@dataclass(frozen=True)
class PersistentPartialLane:
    """One independently paid channel rendering of one native path identity."""

    path_id: int
    channel: int
    basis_length: int
    native_observation_ids: tuple[int, ...]
    support_native_observation_ids: tuple[int, ...]
    retained_native_observation_ids: tuple[int, ...]
    instances: tuple[MafBasisWarpInstance, ...]
    span_fit_kinds: tuple[str, ...]
    estimated_energy: float
    maximum_phase_error_radians: float
    pruned_observation_count: int
    placement_count_before_tail_fusion: int
    tail_fused: bool
    tail_boundary_phase_identity: bool


@dataclass(frozen=True)
class PersistentPartialCandidate:
    """Complete selected payload, alternatives, and deterministic evidence."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    selected_kind: str
    baseline_payload: bytes
    baseline_reconstruction: np.ndarray
    lanes: tuple[PersistentPartialLane, ...]
    report: dict


@dataclass(frozen=True)
class _SubsetResult:
    lane_keys: tuple[tuple[int, int], ...]
    cbf_complete: bytes
    mft1_complete: bytes
    reconstruction: np.ndarray
    sse: int
    residual_bytes: int
    predictor_bytes: int
    selected_transport: str
    selected_payload: bytes
    residual_clip_count: int
    predictor_transport_pcm_identity: bool
    complete_decode_identity: bool
    parsed_record_type_counts: tuple[tuple[str, int], ...]
    s11_record_language_only: bool


@dataclass(frozen=True)
class _SpanLaw:
    """One uninterrupted type-8 law proposed from frozen path evidence."""

    start_step_q16: int
    end_step_q16: int
    fit_kind: str


def _round_ratio_even(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("rounding denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(int(numerator)), int(denominator))
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient & 1):
        quotient += 1
    return sign * quotient


def _phase_turn_u32(phase_radians: float) -> int:
    turns = (float(phase_radians) / (2.0 * math.pi)) % 1.0
    return int(round(turns * _U32)) & 0xFFFF_FFFF


def _phase_position_q16(phase_radians: float, basis_length: int) -> int:
    phase = _phase_turn_u32(phase_radians)
    return _round_ratio_even(
        phase * basis_length * WARP_ONE_Q16,
        _U32,
    ) % (basis_length * WARP_ONE_Q16)


def _frequency_step_q16(
    frequency_hz: float,
    sample_rate: int,
    basis_length: int,
) -> int:
    frequency_hz_q20 = int(round(float(frequency_hz) * (1 << 20)))
    step = _round_ratio_even(
        frequency_hz_q20 * basis_length * WARP_ONE_Q16,
        sample_rate * (1 << 20),
    )
    if not -MAX_WARP_STEP_Q16 <= step <= MAX_WARP_STEP_Q16:
        raise ValueError("partial frequency exceeds the type-8 step domain")
    return step


def _gain_q15(amplitude: float) -> int:
    value = int(round(max(0.0, float(amplitude))))
    if not 0 <= value <= 32768:
        raise ValueError("partial amplitude exceeds the signed Q15 domain")
    return value


def _phase_distance_radians(
    left_q16: int,
    right_q16: int,
    basis_length: int,
) -> float:
    period = basis_length * WARP_ONE_Q16
    raw = (int(left_q16) - int(right_q16)) % period
    wrapped = raw if raw <= period // 2 else raw - period
    return abs(wrapped) * 2.0 * math.pi / period


def _one_past_position(
    position_q16: int,
    start_step_q16: int,
    end_step_q16: int,
    sample_count: int,
    basis_length: int,
) -> int:
    period = basis_length * WARP_ONE_Q16
    if start_step_q16 == end_step_q16:
        return (position_q16 + sample_count * start_step_q16) % period
    last = _warp_source_position_q16(
        position_q16,
        start_step_q16,
        end_step_q16,
        True,
        sample_count - 1,
        sample_count,
    )
    return (last + end_step_q16) % period


def _phase_corrected_steps(
    start_position_q16: int,
    target_position_q16: int,
    sample_count: int,
    start_step_q16: int,
    end_step_q16: int,
    basis_length: int,
) -> tuple[int, int, int]:
    """Apply the smallest common frequency correction that closes phase.

    Adding the same integer delta to both type-8 endpoints advances the
    one-past position by exactly ``sample_count * delta``. This adjusts a
    frequency law from measured complex phase without transmitting a phase
    reset or an S13 anchor.
    """

    period = basis_length * WARP_ONE_Q16
    predicted = _one_past_position(
        start_position_q16,
        start_step_q16,
        end_step_q16,
        sample_count,
        basis_length,
    )
    raw = (target_position_q16 - predicted) % period
    signed = raw if raw <= period // 2 else raw - period
    center = _round_ratio_even(signed, sample_count)
    choices = []
    for delta in (center - 1, center, center + 1):
        corrected_start = start_step_q16 + delta
        corrected_end = end_step_q16 + delta
        if (
            -MAX_WARP_STEP_Q16 <= corrected_start <= MAX_WARP_STEP_Q16
            and -MAX_WARP_STEP_Q16 <= corrected_end <= MAX_WARP_STEP_Q16
        ):
            endpoint = _one_past_position(
                start_position_q16,
                corrected_start,
                corrected_end,
                sample_count,
                basis_length,
            )
            choices.append((
                _phase_distance_radians(
                    endpoint,
                    target_position_q16,
                    basis_length,
                ),
                abs(delta),
                delta,
                corrected_start,
                corrected_end,
            ))
    if not choices:
        raise ValueError("phase correction exceeds the type-8 step domain")
    _error, _magnitude, delta, corrected_start, corrected_end = min(choices)
    return corrected_start, corrected_end, delta


def _checked_accumulator(value: int, language: PersistentPartialLanguage) -> int:
    if abs(int(value)).bit_length() > language.phase_fit_accumulator_bits:
        raise ValueError("phase-fit accumulator bound reached")
    return int(value)


def _phase_uncertainty_position_q16(
    row: ComplexPartialObservation,
    basis_length: int,
) -> int:
    period = basis_length * WARP_ONE_Q16
    uncertainty_q30 = max(
        1,
        int(round(float(row.phase_uncertainty_radians) * (1 << 30))),
    )
    two_pi_q30 = int(round(2.0 * math.pi * (1 << 30)))
    return _round_ratio_even(uncertainty_q30 * period, two_pi_q30)


def _unwrap_phase_positions(
    rows: tuple[ComplexPartialObservation, ...],
    channel: int,
    sample_rate: int,
    basis_length: int,
) -> tuple[int, ...]:
    """Unwrap modulo positions without changing the native observation path.

    Quantized measured frequency predicts only the integer cycle.  A tied or
    uncertainty-overlapped alias is rejected instead of guessed.
    """

    period = basis_length * WARP_ONE_Q16
    unwrapped = [_phase_position_q16(rows[0].channel_phases[channel], basis_length)]
    previous = rows[0]
    for row in rows[1:]:
        delta_samples = row.center_sample - previous.center_sample
        if delta_samples <= 0:
            raise ValueError("phase unwrap requires strictly ordered observations")
        previous_frequency_q20 = int(round(previous.frequency_hz * (1 << 20)))
        frequency_q20 = int(round(row.frequency_hz * (1 << 20)))
        predicted_increment = _round_ratio_even(
            (previous_frequency_q20 + frequency_q20)
            * basis_length
            * WARP_ONE_Q16
            * delta_samples,
            2 * sample_rate * (1 << 20),
        )
        expected = unwrapped[-1] + predicted_increment
        observed = _phase_position_q16(row.channel_phases[channel], basis_length)
        center_cycle = _round_ratio_even(expected - observed, period)
        aliases = sorted(
            (
                abs(observed + cycle * period - expected),
                abs(cycle),
                cycle,
                observed + cycle * period,
            )
            for cycle in (center_cycle - 1, center_cycle, center_cycle + 1)
        )
        if len(aliases) < 2 or aliases[0][0] == aliases[1][0]:
            raise ValueError("phase unwrap has an equal-distance cycle alias")
        previous_uncertainty_q20 = max(
            1,
            int(round(previous.frequency_uncertainty_hz * (1 << 20))),
        )
        frequency_uncertainty_q20 = max(
            1,
            int(round(row.frequency_uncertainty_hz * (1 << 20))),
        )
        frequency_uncertainty = _round_ratio_even(
            (previous_uncertainty_q20 + frequency_uncertainty_q20)
            * basis_length
            * WARP_ONE_Q16
            * delta_samples,
            2 * sample_rate * (1 << 20),
        )
        position_uncertainty = (
            _phase_uncertainty_position_q16(previous, basis_length)
            + _phase_uncertainty_position_q16(row, basis_length)
            + frequency_uncertainty
        )
        alias_margin = aliases[1][0] - aliases[0][0]
        if alias_margin <= 2 * position_uncertainty:
            raise ValueError("phase unwrap cycle is not identifiable within uncertainty")
        unwrapped.append(aliases[0][3])
        previous = row
    return tuple(unwrapped)


def _phase_weight_q12(
    row: ComplexPartialObservation,
    language: PersistentPartialLanguage,
) -> int:
    floor_q20 = max(
        1,
        int(round(language.phase_fit_weight_floor_radians * (1 << 20))),
    )
    uncertainty_q20 = max(
        floor_q20,
        int(round(row.phase_uncertainty_radians * (1 << 20))),
    )
    return max(
        1,
        min(
            1 << 12,
            _round_ratio_even(
                (1 << 12) * floor_q20 * floor_q20,
                uncertainty_q20 * uncertainty_q20,
            ),
        ),
    )


def _fit_phase_steps(
    rows: tuple[ComplexPartialObservation, ...],
    unwrapped_positions: tuple[int, ...],
    begin: int,
    end: int,
    sample_rate: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> tuple[int, int]:
    """Fit type-8 endpoints with bounded exact integer normal equations.

    The rational model proposes two integer steps.  Admission still uses the
    actual half-away-rounded decoder coordinates in `_span_is_feasible`.
    """

    first_sample = rows[begin].center_sample
    sample_count = rows[end].center_sample - first_sample
    if sample_count <= 2 or end - begin < 2:
        raise ValueError("phase fit needs three distinct times and N > 2")
    denominator = 2 * (sample_count - 2)
    origin = unwrapped_positions[begin]
    normal_11 = normal_12 = normal_22 = 0
    target_1 = target_2 = 0
    for index in range(begin, end + 1):
        offset = rows[index].center_sample - first_sample
        if offset < 0 or offset > sample_count:
            raise ValueError("phase-fit observation lies outside its span")
        x1 = denominator * offset
        x2 = offset * (offset - 1)
        target = denominator * (unwrapped_positions[index] - origin)
        weight = _phase_weight_q12(rows[index], language)
        normal_11 += weight * x1 * x1
        normal_12 += weight * x1 * x2
        normal_22 += weight * x2 * x2
        target_1 += weight * x1 * target
        target_2 += weight * x2 * target

    # Two frozen weak priors prevent an otherwise nearly singular phase-only
    # fit from inventing extreme endpoint frequencies.  Their weight is one
    # against Q12 observation weights and therefore remains subordinate.
    prior_scale = denominator * sample_count
    raw_start = _frequency_step_q16(
        rows[begin].frequency_hz, sample_rate, basis_length
    )
    raw_end = _frequency_step_q16(
        rows[end].frequency_hz, sample_rate, basis_length
    )
    regularization = language.phase_fit_regularization_weight
    normal_11 += regularization * prior_scale * prior_scale
    target_1 += regularization * prior_scale * prior_scale * raw_start
    normal_11 += regularization * prior_scale * prior_scale
    normal_12 += regularization * prior_scale * prior_scale
    normal_22 += regularization * prior_scale * prior_scale
    target_1 += regularization * prior_scale * prior_scale * raw_end
    target_2 += regularization * prior_scale * prior_scale * raw_end

    for value in (normal_11, normal_12, normal_22, target_1, target_2):
        _checked_accumulator(value, language)
    determinant = normal_11 * normal_22 - normal_12 * normal_12
    scale = normal_11 * normal_22
    _checked_accumulator(determinant, language)
    _checked_accumulator(scale, language)
    if determinant <= 0 or determinant << language.phase_fit_condition_shift < scale:
        raise ValueError("phase-fit normal equation is ill-conditioned")
    start_numerator = target_1 * normal_22 - target_2 * normal_12
    delta_numerator = normal_11 * target_2 - normal_12 * target_1
    _checked_accumulator(start_numerator, language)
    _checked_accumulator(delta_numerator, language)
    start_step = _round_ratio_even(start_numerator, determinant)
    end_step = start_step + _round_ratio_even(delta_numerator, determinant)
    if (
        not -MAX_WARP_STEP_Q16 <= start_step <= MAX_WARP_STEP_Q16
        or not -MAX_WARP_STEP_Q16 <= end_step <= MAX_WARP_STEP_Q16
    ):
        raise ValueError("phase-fit step exceeds the type-8 domain")
    return start_step, end_step


def _span_law(
    rows: tuple[ComplexPartialObservation, ...],
    unwrapped_positions: tuple[int, ...] | None,
    channel: int,
    begin: int,
    end: int,
    sample_rate: int,
    basis_length: int,
    start_position_q16: int,
    language: PersistentPartialLanguage,
) -> _SpanLaw:
    count = rows[end].center_sample - rows[begin].center_sample
    target = _phase_position_q16(rows[end].channel_phases[channel], basis_length)
    fit_kind = "endpoint"
    if unwrapped_positions is not None:
        try:
            start_step, end_step = _fit_phase_steps(
                rows,
                unwrapped_positions,
                begin,
                end,
                sample_rate,
                basis_length,
                language,
            )
            fit_kind = "decoder-coordinate-phase-fit"
        except ValueError:
            start_step = _frequency_step_q16(
                rows[begin].frequency_hz, sample_rate, basis_length
            )
            end_step = _frequency_step_q16(
                rows[end].frequency_hz, sample_rate, basis_length
            )
    else:
        start_step = _frequency_step_q16(
            rows[begin].frequency_hz, sample_rate, basis_length
        )
        end_step = _frequency_step_q16(
            rows[end].frequency_hz, sample_rate, basis_length
        )
    start_step, end_step, _correction = _phase_corrected_steps(
        start_position_q16,
        target,
        count,
        start_step,
        end_step,
        basis_length,
    )
    return _SpanLaw(start_step, end_step, fit_kind)


def _fixed_graph_inputs(
    observations: ComplexPartialObservationSet,
    sample_rate: int,
    total_frames: int,
) -> tuple[tuple, tuple, dict[int, ComplexPartialObservation], dict]:
    candidates = tuple(
        sorted(
            (
                row
                for row in observations.observations
                if row.detector_channel == -1
                and row.phase_usable
                and row.locally_resolvable
                and 0 <= row.center_sample < total_frames
            ),
            key=lambda row: (
                row.center_sample,
                row.resolution_id,
                row.frequency_hz,
                row.provenance,
            ),
        )
    )
    resolutions = tuple(
        make_resolution(
            index,
            int(row["fft_samples"]),
            int(row["hop_samples"]),
        )
        for index, row in enumerate(observations.report["resolution_manifest"])
    )
    fixed = []
    evidence: dict[int, ComplexPartialObservation] = {}
    for identifier, row in enumerate(candidates):
        amplitude_q16 = int(round(row.normalized_detector_amplitude * (1 << 16)))
        if not 0 < amplitude_q16 <= 0xFFFF_FFFF:
            continue
        frequency_q20 = int(round(row.frequency_hz * (1 << 20)))
        frequency_uncertainty_q20 = max(
            1,
            int(round(row.frequency_uncertainty_hz * (1 << 20))),
        )
        phase_step = _round_ratio_even(frequency_q20 * _U32, sample_rate << 20)
        phase_uncertainty = min(
            (1 << 31) - 1,
            max(
                1,
                int(round(
                    row.phase_uncertainty_radians * (1 << 31) / math.pi
                )),
            ),
        )
        ownership = (
            row.conflict_group
            if row.conflict_group >= 0
            else len(observations.observations) + identifier
        )
        node_value = max(
            1,
            min(
                (1 << 31) - 1,
                int(round(math.log2(1.0 + row.amplitude_lower_confidence) * 256)),
            ),
        )
        fixed_id = len(fixed)
        fixed.append(make_observation(
            observation_id=fixed_id,
            frame_index=row.frame_index,
            resolution_id=row.resolution_id,
            hop_samples=row.hop_samples,
            frequency_hz_q20=frequency_q20,
            phase_turn_u32=_phase_turn_u32(row.aggregate_phase),
            phase_step_u32=phase_step,
            normalized_amplitude_q16=amplitude_q16,
            ownership_component=ownership,
            detector_id=-1,
            frequency_uncertainty_hz_q20=frequency_uncertainty_q20,
            phase_uncertainty_u31=phase_uncertainty,
            flags=PHASE_USABLE | LOCALLY_RESOLVABLE,
            potential_node_value_q8=node_value,
        ))
        evidence[fixed_id] = row
    return (
        resolutions,
        tuple(fixed),
        evidence,
        {
            "high_level_observations": len(observations.observations),
            "aggregate_phase_usable_resolvable": len(candidates),
            "fixed_observations": len(fixed),
        },
    )


def _ordered_path_rows(
    path: PathRecord,
    evidence: dict[int, ComplexPartialObservation],
) -> tuple[tuple[ComplexPartialObservation, ...], tuple[int, ...]]:
    paired = tuple(
        sorted(
            (
                (evidence[entry.observation_id], entry.observation_id)
                for entry in path.entries
            ),
            key=lambda pair: pair[0].center_sample,
        )
    )
    rows = tuple(row for row, _identifier in paired)
    identifiers = tuple(identifier for _row, identifier in paired)
    return rows, identifiers


def _bounded_rows(
    rows: tuple[ComplexPartialObservation, ...],
    identifiers: tuple[int, ...],
    maximum: int,
) -> tuple[tuple[ComplexPartialObservation, ...], tuple[int, ...], int]:
    if len(rows) <= maximum:
        return rows, identifiers, 0
    indexes = {
        _round_ratio_even(index * (len(rows) - 1), maximum - 1)
        for index in range(maximum)
    }
    ordered = tuple(sorted(indexes))
    retained = tuple(rows[index] for index in ordered)
    retained_identifiers = tuple(identifiers[index] for index in ordered)
    return retained, retained_identifiers, len(rows) - len(retained)


def _boundary_valid_support(
    rows: tuple[ComplexPartialObservation, ...],
    identifiers: tuple[int, ...],
    total_frames: int,
) -> tuple[
    tuple[ComplexPartialObservation, ...],
    tuple[int, ...],
    int,
]:
    """Select one geometry-valid paid lifetime without rebuilding R-191."""

    runs: list[tuple[int, int]] = []
    begin = None
    for index, row in enumerate(rows):
        half = row.fft_samples // 2
        eligible = (
            row.center_sample >= half
            and row.center_sample + half <= total_frames
        )
        if eligible and begin is None:
            begin = index
        elif not eligible and begin is not None:
            runs.append((begin, index))
            begin = None
    if begin is not None:
        runs.append((begin, len(rows)))
    eligible_runs = [run for run in runs if run[1] - run[0] >= 2]
    if not eligible_runs:
        raise ValueError("native path has no boundary-valid S11 support")

    def rank(run: tuple[int, int]) -> tuple:
        left, right = run
        covered = rows[right - 1].center_sample - rows[left].center_sample
        return (
            -covered,
            -(right - left),
            rows[left].center_sample,
            identifiers[left:right],
        )

    left, right = min(eligible_runs, key=rank)
    return (
        rows[left:right],
        identifiers[left:right],
        len(rows) - (right - left),
    )


def _span_is_feasible(
    rows: tuple[ComplexPartialObservation, ...],
    unwrapped_positions: tuple[int, ...] | None,
    channel: int,
    begin: int,
    end: int,
    sample_rate: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> tuple[bool, float]:
    start = rows[begin]
    finish = rows[end]
    count = finish.center_sample - start.center_sample
    if count <= 0:
        return False, math.inf
    start_position = _phase_position_q16(
        start.channel_phases[channel], basis_length
    )
    law = _span_law(
        rows,
        unwrapped_positions,
        channel,
        begin,
        end,
        sample_rate,
        basis_length,
        start_position,
        language,
    )
    start_step = law.start_step_q16
    end_step = law.end_step_q16
    if start_step != end_step and count < 3:
        return False, math.inf
    start_gain = _gain_q15(start.channel_amplitudes[channel])
    end_gain = _gain_q15(finish.channel_amplitudes[channel])
    worst = 0.0
    for row in rows[begin : end + 1]:
        offset = row.center_sample - start.center_sample
        fraction = offset / count
        if offset >= count - 1:
            instantaneous_step = end_step
        else:
            here = _warp_source_position_q16(
                0,
                start_step,
                end_step,
                start_step != end_step,
                offset,
                count,
            )
            following = _warp_source_position_q16(
                0,
                start_step,
                end_step,
                start_step != end_step,
                offset + 1,
                count,
            )
            instantaneous_step = following - here
        expected_frequency = (
            instantaneous_step
            * sample_rate
            / (basis_length * WARP_ONE_Q16)
        )
        frequency_limit = max(
            language.frequency_error_floor_hz,
            language.frequency_uncertainty_scale * row.frequency_uncertainty_hz,
        )
        frequency_error = abs(row.frequency_hz - expected_frequency)
        if frequency_error > frequency_limit:
            return False, math.inf
        expected_gain = start_gain + fraction * (end_gain - start_gain)
        actual_gain = row.channel_amplitudes[channel]
        gain_limit = max(
            language.gain_error_floor,
            language.gain_relative_error * max(actual_gain, expected_gain, 1.0),
            language.gain_uncertainty_scale * row.amplitude_uncertainty,
        )
        gain_error = abs(actual_gain - expected_gain)
        if gain_error > gain_limit:
            return False, math.inf
        if offset == count:
            expected_position = _one_past_position(
                start_position,
                start_step,
                end_step,
                count,
                basis_length,
            )
        else:
            expected_position = _warp_source_position_q16(
                start_position,
                start_step,
                end_step,
                start_step != end_step,
                offset,
                count,
            )
        phase_error = _phase_distance_radians(
            expected_position,
            _phase_position_q16(row.channel_phases[channel], basis_length),
            basis_length,
        )
        phase_limit = max(
            language.phase_error_floor_radians,
            language.phase_uncertainty_scale * row.phase_uncertainty_radians,
        )
        if phase_error > phase_limit:
            return False, math.inf
        worst = max(
            worst,
            frequency_error / frequency_limit,
            gain_error / gain_limit,
            phase_error / phase_limit,
        )
    return True, worst


def _thin_knots(
    rows: tuple[ComplexPartialObservation, ...],
    unwrapped_positions: tuple[int, ...] | None,
    channel: int,
    sample_rate: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> tuple[int, ...]:
    # Dynamic programming minimizes the actual number of charged type-8
    # placements implied by each feasible span; normalized fit error breaks
    # ties without replacing the later complete-byte RDO.
    count = len(rows)
    best: list[tuple[int, float, int] | None] = [None] * count
    best[0] = (0, 0.0, -1)
    for end in range(1, count):
        choice = None
        for begin in range(end):
            if best[begin] is None:
                continue
            feasible, error = _span_is_feasible(
                rows,
                unwrapped_positions,
                channel,
                begin,
                end,
                sample_rate,
                basis_length,
                language,
            )
            if not feasible:
                continue
            frames = rows[end].center_sample - rows[begin].center_sample
            charged = math.ceil(frames / MAX_WARP_INSTANCE_SAMPLES)
            candidate = (
                best[begin][0] + charged,
                best[begin][1] + error,
                begin,
            )
            if choice is None or candidate < choice:
                choice = candidate
        best[end] = choice
    if best[-1] is None:
        raise ValueError("native path has no phase-continuous S11 lowering")
    indexes = [count - 1]
    cursor = count - 1
    while cursor:
        cursor = best[cursor][2]
        indexes.append(cursor)
    return tuple(reversed(indexes))


def _interpolate_integer(start: int, end: int, offset: int, length: int) -> int:
    return start + _round_ratio_even((end - start) * offset, length)


def _round_ratio_away(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("rounding denominator must be positive")
    magnitude, remainder = divmod(abs(int(numerator)), int(denominator))
    if 2 * remainder >= denominator:
        magnitude += 1
    return -magnitude if numerator < 0 else magnitude


def _validate_emitted_span(
    rows: tuple[ComplexPartialObservation, ...],
    channel: int,
    left_index: int,
    right_index: int,
    instances: tuple[MafBasisWarpInstance, ...],
    final_position_q16: int,
    sample_rate: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> float:
    """Rescore split laws through the exact decoder coordinate equations."""

    right_sample = rows[right_index].center_sample
    maximum_phase_error = 0.0
    for row in rows[left_index : right_index + 1]:
        if row.center_sample == right_sample:
            position = final_position_q16
            step = instances[-1].end_source_step_q16
            if step is None:
                step = instances[-1].source_step_q16
            gain = instances[-1].end_gain_q15
            if gain is None:
                gain = instances[-1].gain_q15
        else:
            instance = next(
                (
                    item
                    for item in instances
                    if item.start
                    <= row.center_sample
                    < item.start + item.sample_count
                ),
                None,
            )
            if instance is None:
                raise ValueError("split law does not cover a retained observation")
            local = row.center_sample - instance.start
            end_step = instance.end_source_step_q16
            if end_step is None:
                end_step = instance.source_step_q16
            position = _warp_source_position_q16(
                instance.source_position_q16,
                instance.source_step_q16,
                end_step,
                instance.end_source_step_q16 is not None,
                local,
                instance.sample_count,
            )
            if local + 1 >= instance.sample_count:
                step = end_step
            else:
                following = _warp_source_position_q16(
                    instance.source_position_q16,
                    instance.source_step_q16,
                    end_step,
                    instance.end_source_step_q16 is not None,
                    local + 1,
                    instance.sample_count,
                )
                step = following - position
            if instance.end_gain_q15 is None:
                gain = instance.gain_q15
            elif local + 1 == instance.sample_count:
                gain = instance.end_gain_q15
            else:
                gain = instance.gain_q15 + _round_ratio_away(
                    (instance.end_gain_q15 - instance.gain_q15) * local,
                    instance.sample_count - 1,
                )

        expected_frequency = (
            step * sample_rate / (basis_length * WARP_ONE_Q16)
        )
        frequency_limit = max(
            language.frequency_error_floor_hz,
            language.frequency_uncertainty_scale * row.frequency_uncertainty_hz,
        )
        if abs(row.frequency_hz - expected_frequency) > frequency_limit:
            raise ValueError("split law frequency exceeds its frozen bound")
        gain_limit = max(
            language.gain_error_floor,
            language.gain_relative_error
            * max(row.channel_amplitudes[channel], gain, 1.0),
            language.gain_uncertainty_scale * row.amplitude_uncertainty,
        )
        if abs(row.channel_amplitudes[channel] - gain) > gain_limit:
            raise ValueError("split law gain exceeds its frozen bound")
        phase_error = _phase_distance_radians(
            position,
            _phase_position_q16(row.channel_phases[channel], basis_length),
            basis_length,
        )
        phase_limit = max(
            language.phase_error_floor_radians,
            language.phase_uncertainty_scale * row.phase_uncertainty_radians,
        )
        if phase_error > phase_limit:
            raise ValueError("split law phase exceeds its frozen bound")
        maximum_phase_error = max(maximum_phase_error, phase_error)
    return maximum_phase_error


def _fuse_constant_tail(
    instances: tuple[MafBasisWarpInstance, ...],
    tail: MafBasisWarpInstance,
    last: ComplexPartialObservation,
    sample_rate: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> tuple[tuple[MafBasisWarpInstance, ...], bool, bool]:
    """Fuse an adjacent bounded tail only when the frozen S11 proof closes."""

    if not instances:
        return (tail,), False, False
    previous = instances[-1]
    combined_count = previous.sample_count + tail.sample_count
    if (
        previous.start + previous.sample_count != tail.start
        or previous.emitter_id != tail.emitter_id
        or previous.basis_id != tail.basis_id
        or previous.circular != tail.circular
        or previous.end_source_step_q16 is not None
        or previous.end_gain_q15 is not None
        or tail.end_source_step_q16 is not None
        or tail.end_gain_q15 is not None
        or previous.gain_q15 != tail.gain_q15
        or combined_count > MAX_WARP_INSTANCE_SAMPLES
        or abs(previous.source_step_q16) > MAX_WARP_STEP_Q16
    ):
        return instances + (tail,), False, False
    old_boundary_position = _one_past_position(
        previous.source_position_q16,
        previous.source_step_q16,
        previous.source_step_q16,
        previous.sample_count,
        basis_length,
    )
    boundary_identity = old_boundary_position == tail.source_position_q16
    if not boundary_identity:
        return instances + (tail,), False, False
    expected_frequency = (
        previous.source_step_q16
        * sample_rate
        / (basis_length * WARP_ONE_Q16)
    )
    frequency_limit = max(
        language.frequency_error_floor_hz,
        language.frequency_uncertainty_scale * last.frequency_uncertainty_hz,
    )
    if abs(last.frequency_hz - expected_frequency) > frequency_limit:
        return instances + (tail,), False, True
    fused = replace(previous, sample_count=combined_count)
    return instances[:-1] + (fused,), True, True


def _lower_lane_for_basis(
    path: PathRecord,
    rows: tuple[ComplexPartialObservation, ...],
    row_identifiers: tuple[int, ...],
    channel: int,
    sample_rate: int,
    total_frames: int,
    pruned_observations: int,
    basis_length: int,
    language: PersistentPartialLanguage,
) -> PersistentPartialLane:
    try:
        unwrapped_positions = _unwrap_phase_positions(
            rows,
            channel,
            sample_rate,
            basis_length,
        )
    except ValueError:
        unwrapped_positions = None
    knot_indexes = _thin_knots(
        rows,
        unwrapped_positions,
        channel,
        sample_rate,
        basis_length,
        language,
    )
    instances = []
    span_fit_kinds = []
    position = _phase_position_q16(
        rows[0].channel_phases[channel], basis_length
    )
    maximum_phase_error = 0.0
    for left_index, right_index in zip(knot_indexes, knot_indexes[1:]):
        left = rows[left_index]
        right = rows[right_index]
        span = right.center_sample - left.center_sample
        law = _span_law(
            rows,
            unwrapped_positions,
            channel,
            left_index,
            right_index,
            sample_rate,
            basis_length,
            position,
            language,
        )
        start_step = law.start_step_q16
        end_step = law.end_step_q16
        span_fit_kinds.append(law.fit_kind)
        start_gain = _gain_q15(left.channel_amplitudes[channel])
        end_gain = _gain_q15(right.channel_amplitudes[channel])
        first_instance = len(instances)
        consumed = 0
        while consumed < span:
            piece = min(MAX_WARP_INSTANCE_SAMPLES, span - consumed)
            piece_start_step = _interpolate_integer(
                start_step, end_step, consumed, span
            )
            piece_end_step = _interpolate_integer(
                start_step, end_step, consumed + piece, span
            )
            piece_start_gain = _interpolate_integer(
                start_gain, end_gain, consumed, span
            )
            piece_end_gain = _interpolate_integer(
                start_gain, end_gain, consumed + piece, span
            )
            instances.append(MafBasisWarpInstance(
                emitter_id=0,
                basis_id=0,
                start=left.center_sample + consumed,
                sample_count=piece,
                source_position_q16=position,
                source_step_q16=piece_start_step,
                gain_q15=piece_start_gain,
                circular=True,
                end_source_step_q16=(
                    piece_end_step
                    if piece_end_step != piece_start_step and piece >= 3
                    else None
                ),
                end_gain_q15=(
                    piece_end_gain
                    if piece_end_gain != piece_start_gain and piece >= 2
                    else None
                ),
            ))
            position = _one_past_position(
                position,
                piece_start_step,
                piece_end_step if piece >= 3 else piece_start_step,
                piece,
                basis_length,
            )
            consumed += piece
        maximum_phase_error = max(
            maximum_phase_error,
            _validate_emitted_span(
                rows,
                channel,
                left_index,
                right_index,
                tuple(instances[first_instance:]),
                position,
                sample_rate,
                basis_length,
                language,
            ),
        )
        phase_error = _phase_distance_radians(
            position,
            _phase_position_q16(right.channel_phases[channel], basis_length),
            basis_length,
        )
        maximum_phase_error = max(maximum_phase_error, phase_error)
        phase_limit = max(
            language.phase_error_floor_radians,
            language.phase_uncertainty_scale * right.phase_uncertainty_radians,
        )
        if phase_error > phase_limit:
            raise ValueError("continuous path phase exceeds its frozen bound")

    last = rows[knot_indexes[-1]]
    placement_count_before_tail_fusion = len(instances)
    tail_fused = False
    tail_boundary_phase_identity = False
    tail = min(last.hop_samples, total_frames - last.center_sample)
    if tail > 0:
        step = _frequency_step_q16(
            last.frequency_hz, sample_rate, basis_length
        )
        tail_instance = MafBasisWarpInstance(
            emitter_id=0,
            basis_id=0,
            start=last.center_sample,
            sample_count=tail,
            source_position_q16=position,
            source_step_q16=step,
            gain_q15=_gain_q15(last.channel_amplitudes[channel]),
            circular=True,
        )
        placement_count_before_tail_fusion += 1
        fused_instances, tail_fused, tail_boundary_phase_identity = (
            _fuse_constant_tail(
                tuple(instances),
                tail_instance,
                last,
                sample_rate,
                basis_length,
                language,
            )
        )
        instances = list(fused_instances)
    energy = sum(
        row.channel_amplitudes[channel] ** 2
        for row in rows
    ) * max(1, rows[-1].center_sample - rows[0].center_sample)
    return PersistentPartialLane(
        path_id=path.path_id,
        channel=channel,
        basis_length=basis_length,
        native_observation_ids=tuple(entry.observation_id for entry in path.entries),
        support_native_observation_ids=tuple(row_identifiers),
        retained_native_observation_ids=tuple(
            row_identifiers[index] for index in knot_indexes
        ),
        instances=tuple(instances),
        span_fit_kinds=tuple(span_fit_kinds),
        estimated_energy=float(energy),
        maximum_phase_error_radians=maximum_phase_error,
        pruned_observation_count=pruned_observations,
        placement_count_before_tail_fusion=placement_count_before_tail_fusion,
        tail_fused=tail_fused,
        tail_boundary_phase_identity=tail_boundary_phase_identity,
    )


def _lower_lane(
    path: PathRecord,
    rows: tuple[ComplexPartialObservation, ...],
    row_identifiers: tuple[int, ...],
    channel: int,
    sample_rate: int,
    total_frames: int,
    pruned_observations: int,
    language: PersistentPartialLanguage,
) -> PersistentPartialLane:
    failures = []
    for basis_length in reversed(COSINE_BASIS_LENGTHS):
        try:
            return _lower_lane_for_basis(
                path,
                rows,
                row_identifiers,
                channel,
                sample_rate,
                total_frames,
                pruned_observations,
                basis_length,
                language,
            )
        except ValueError as error:
            failures.append(f"L={basis_length}: {error}")
    raise ValueError("; ".join(failures))


def _pack_lane_subset(
    lanes: tuple[PersistentPartialLane, ...],
    sample_rate: int,
    total_frames: int,
    output_channels: int,
) -> bytes:
    used_lengths = tuple(sorted({lane.basis_length for lane in lanes}))
    basis_ids = {
        length: identifier for identifier, length in enumerate(used_lengths)
    }
    instances = []
    for emitter, lane in enumerate(lanes):
        instances.extend(
            replace(
                instance,
                emitter_id=emitter,
                basis_id=basis_ids[lane.basis_length],
            )
            for instance in lane.instances
        )
    if len(instances) > 4096:
        raise ValueError("S11 lane subset exceeds the placement bound")
    matrix = tuple(
        tuple(
            32767 if lane.channel == output else 0
            for lane in lanes
        )
        for output in range(output_channels)
    )
    return pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=total_frames,
        render_quantum=256,
        output_channels=output_channels,
        emitter_count=len(lanes),
        mixes=(MafMix(0, total_frames, matrix),),
        bases=tuple(MafBasis(COSINE_BASES[length]) for length in used_lengths),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=256,
    )


def _evaluate_subset(
    source: np.ndarray,
    sample_rate: int,
    lanes: tuple[PersistentPartialLane, ...],
    *,
    native_decoder,
    coefficients_per_frame: int,
    half_window: int,
    band_count: int,
) -> _SubsetResult:
    mft1 = _pack_lane_subset(
        lanes,
        sample_rate,
        source.shape[0],
        source.shape[1],
    )
    parsed = parse_maf_typed(mft1)
    parsed_record_type_counts = (
        ("filter", len(parsed.filters)),
        ("stochastic", len(parsed.stochastic)),
        ("source_filter", len(parsed.sources)),
        ("transient", len(parsed.transients)),
        ("mix", len(parsed.mixes)),
        ("basis", len(parsed.bases)),
        ("basis_instance", len(parsed.basis_instances)),
        ("basis_warp_instance", len(parsed.basis_warp_instances)),
    )
    s11_record_language_only = (
        not parsed.filters
        and not parsed.stochastic
        and not parsed.sources
        and not parsed.transients
        and not parsed.basis_instances
        and len(parsed.mixes) == 1
        and bool(parsed.bases)
        and bool(parsed.basis_warp_instances)
    )
    if not s11_record_language_only:
        raise RuntimeError("S11 emitted records outside its frozen language")
    mft_prediction = native_decoder.decode_maf_typed(mft1).samples
    transport = encode_causal_basis_field_from_mft1(mft1)
    cbf_prediction = native_decoder.decode_maf_typed(
        transport.info.mft1_payload
    ).samples
    if not np.array_equal(mft_prediction, cbf_prediction):
        raise RuntimeError("S11 CBF1 and MFT1 predictor PCM differ")
    difference = source.astype(np.int32) - cbf_prediction.astype(np.int32)
    clipped = np.clip(difference, -32768, 32767).astype(np.int16)
    residual = encode_lapped_stream(
        clipped,
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
    reconstruction = np.clip(
        cbf_prediction.astype(np.int32)
        + residual.reconstruction.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    error = source.astype(np.int64) - reconstruction.astype(np.int64)
    cbf_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=sample_rate,
        predictor_type="CBF1",
        predictor_payload=transport.cbf_payload,
        residual_payload=residual.payload,
    )
    mft_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=sample_rate,
        predictor_type="MFT1",
        predictor_payload=mft1,
        residual_payload=residual.payload,
    )
    selected_transport, selected_payload = min(
        (("cbf1", cbf_complete), ("mft1", mft_complete)),
        key=lambda row: (len(row[1]), row[0]),
    )
    decoded_rate, decoded = decode_causal_basis_truth_candidate(
        selected_payload,
        native_decoder=native_decoder,
    )
    if decoded_rate != sample_rate or not np.array_equal(decoded, reconstruction):
        raise RuntimeError("S11 complete independent decode differs")
    reconstruction.flags.writeable = False
    return _SubsetResult(
        lane_keys=tuple((lane.path_id, lane.channel) for lane in lanes),
        cbf_complete=cbf_complete,
        mft1_complete=mft_complete,
        reconstruction=reconstruction,
        sse=int(np.sum(error * error)),
        residual_bytes=len(residual.payload),
        predictor_bytes=(
            len(transport.cbf_payload)
            if selected_transport == "cbf1"
            else len(mft1)
        ),
        selected_transport=selected_transport,
        selected_payload=selected_payload,
        residual_clip_count=int(np.count_nonzero(
            (difference < -32768) | (difference > 32767)
        )),
        predictor_transport_pcm_identity=True,
        complete_decode_identity=True,
        parsed_record_type_counts=parsed_record_type_counts,
        s11_record_language_only=s11_record_language_only,
    )


def encode_persistent_partial_truth_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_graph: NativePartialGraph,
    native_decoder,
    coefficients_per_frame: int,
    half_window: int = 512,
    band_count: int = 24,
    language: PersistentPartialLanguage = PersistentPartialLanguage(),
) -> PersistentPartialCandidate:
    """Analyze, lower, decode, and byte-select the frozen S11 generation."""

    started = time.perf_counter()
    source = np.ascontiguousarray(samples, dtype=np.int16)
    if (
        source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("S11 requires non-empty frame-major PCM16")
    for length in COSINE_BASIS_LENGTHS:
        payload = np.asarray(COSINE_BASES[length], dtype="<i2").tobytes()
        if (
            hashlib.sha256(payload).hexdigest()
            != COSINE_BASIS_PCM16LE_SHA256[length]
        ):
            raise RuntimeError("frozen S11 Basis-family identity mismatch")

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
    baseline_error = source.astype(np.int64) - baseline.reconstruction.astype(np.int64)
    baseline_sse = int(np.sum(baseline_error * baseline_error))
    observed = observe_complex_partials(
        source,
        sample_rate,
        manifest=language.analyzer,
    )
    resolutions, fixed, evidence, conversion_report = _fixed_graph_inputs(
        observed,
        sample_rate,
        source.shape[0],
    )
    graph_report: dict = {"status": "no fixed observations"}
    native_paths = ()
    selected_path_ids: tuple[int, ...] = ()
    if fixed:
        graph_manifest = make_manifest(
            sample_rate=sample_rate,
            resolution_count=len(resolutions),
            cycle_offsets=(0,),
            maximum_edge_records=language.maximum_edge_records,
        )
        try:
            edges = native_graph.edges(resolutions, fixed, graph_manifest)
            family_cap = max(1, min(128, language.maximum_path_records // 3))
            path_manifest = make_path_manifest(
                protected_band_upper_hz_q20=tuple(
                    value << 20
                    for value in language.protected_band_upper_hz
                    if 0 < value < sample_rate // 2
                ),
                maximum_path_records=language.maximum_path_records,
                top_k_value=family_cap,
                top_k_continuity=family_cap,
                top_k_protected=family_cap,
                maximum_total_entries=language.maximum_path_entries,
                maximum_work_units=language.maximum_path_work_units,
            )
            path_result = native_graph.paths(
                resolutions,
                fixed,
                edges,
                graph_manifest,
                path_manifest,
            )
        except RuntimeError as error:
            if not str(error).endswith(": 6"):
                raise
            graph_report = {
                "status": "native profile bound; explicit direct-Truth fallback",
                "reason": str(error),
                "maximum_path_work_units": language.maximum_path_work_units,
            }
        else:
            selected_path_ids = path_result.selected_path_ids
            selected = set(selected_path_ids)
            native_paths = tuple(
                path for path in path_result.paths if path.path_id in selected
            )
            graph_report = {
                **path_result.report,
                "edge_count": len(edges),
                "selected_path_ids": list(selected_path_ids),
            }

    lane_failures = []
    lane_proposals = []
    for path in native_paths:
        rows, row_identifiers = _ordered_path_rows(
            path,
            evidence,
        )
        try:
            rows, row_identifiers, boundary_pruned = _boundary_valid_support(
                rows,
                row_identifiers,
                source.shape[0],
            )
        except ValueError as error:
            lane_failures.append({
                "path_id": path.path_id,
                "reason": str(error),
            })
            continue
        rows, row_identifiers, bounded_pruned = _bounded_rows(
            rows,
            row_identifiers,
            language.maximum_lane_observations,
        )
        pruned = boundary_pruned + bounded_pruned
        for channel in range(source.shape[1]):
            try:
                lane = _lower_lane(
                    path,
                    rows,
                    row_identifiers,
                    channel,
                    sample_rate,
                    source.shape[0],
                    pruned,
                    language,
                )
            except ValueError as error:
                lane_failures.append({
                    "path_id": path.path_id,
                    "channel": channel,
                    "reason": str(error),
                })
                continue
            if not lane.instances:
                continue
            lane_proposals.append(lane)
    lane_proposals.sort(
        key=lambda lane: (
            -lane.estimated_energy,
            lane.path_id,
            lane.channel,
        )
    )
    bounded_lanes = tuple(
        lane_proposals[
            : min(language.maximum_channel_lanes, language.maximum_rdo_lanes)
        ]
    )

    evaluated: list[_SubsetResult] = []
    if len(bounded_lanes) <= language.exact_subset_lane_limit:
        subsets = (
            tuple(bounded_lanes[index] for index in indexes)
            for count in range(1, len(bounded_lanes) + 1)
            for indexes in itertools.combinations(range(len(bounded_lanes)), count)
        )
        solver = "exact-small-subset"
    else:
        subsets = (
            bounded_lanes[:count]
            for count in range(1, len(bounded_lanes) + 1)
        )
        solver = "deterministic-energy-prefix"
    for subset in subsets:
        try:
            evaluated.append(_evaluate_subset(
                source,
                sample_rate,
                subset,
                native_decoder=native_decoder,
                coefficients_per_frame=coefficients_per_frame,
                half_window=half_window,
                band_count=band_count,
            ))
        except ValueError as error:
            lane_failures.append({
                "lane_keys": [
                    [lane.path_id, lane.channel] for lane in subset
                ],
                "reason": str(error),
            })

    eligible = tuple(row for row in evaluated if row.sse <= baseline_sse)
    if eligible:
        best = min(
            eligible,
            key=lambda row: (len(row.selected_payload), row.sse, row.lane_keys),
        )
    else:
        best = None
    if best is not None and len(best.selected_payload) < len(baseline.payload):
        selected_payload = best.selected_payload
        selected_reconstruction = best.reconstruction
        selected_kind = f"{best.selected_transport}-truth"
        retained_keys = set(best.lane_keys)
        retained_lanes = tuple(
            lane
            for lane in bounded_lanes
            if (lane.path_id, lane.channel) in retained_keys
        )
    else:
        selected_payload = baseline.payload
        selected_reconstruction = baseline.reconstruction
        selected_kind = "truth-fallback"
        retained_lanes = ()
    selected_reconstruction.flags.writeable = False
    return PersistentPartialCandidate(
        selected_payload=selected_payload,
        selected_reconstruction=selected_reconstruction,
        selected_kind=selected_kind,
        baseline_payload=baseline.payload,
        baseline_reconstruction=baseline.reconstruction,
        lanes=retained_lanes,
        report={
            "schema": "resonith-r215-persistent-partial-candidate-1",
            "status": "frozen S11 research generation; S12 pending",
            "semantic_source_classes": False,
            "public_syntax_changed": False,
            "basis_family_lengths": list(COSINE_BASIS_LENGTHS),
            "basis_family_pcm16le_sha256": {
                str(length): COSINE_BASIS_PCM16LE_SHA256[length]
                for length in COSINE_BASIS_LENGTHS
            },
            "conversion": conversion_report,
            "graph": graph_report,
            "native_selected_path_ids": list(selected_path_ids),
            "lane_proposal_count": len(lane_proposals),
            "lane_proposals": [
                {
                    "path_id": lane.path_id,
                    "channel": lane.channel,
                    "basis_length": lane.basis_length,
                    "full_native_observation_ids": list(
                        lane.native_observation_ids
                    ),
                    "support_native_observation_ids": list(
                        lane.support_native_observation_ids
                    ),
                    "knot_native_observation_ids": list(
                        lane.retained_native_observation_ids
                    ),
                    "placement_count": len(lane.instances),
                    "placement_count_before_tail_fusion": (
                        lane.placement_count_before_tail_fusion
                    ),
                    "tail_fused": lane.tail_fused,
                    "tail_boundary_phase_identity": (
                        lane.tail_boundary_phase_identity
                    ),
                    "instances": [
                        {
                            "emitter_id": item.emitter_id,
                            "basis_id": item.basis_id,
                            "start": item.start,
                            "sample_count": item.sample_count,
                            "source_position_q16": item.source_position_q16,
                            "source_step_q16": item.source_step_q16,
                            "end_source_step_q16": item.end_source_step_q16,
                            "gain_q15": item.gain_q15,
                            "end_gain_q15": item.end_gain_q15,
                            "circular": item.circular,
                        }
                        for item in lane.instances
                    ],
                    "span_fit_kinds": list(lane.span_fit_kinds),
                    "birth_sample": lane.instances[0].start,
                    "death_sample": max(
                        item.start + item.sample_count for item in lane.instances
                    ),
                    "maximum_phase_error_radians": (
                        lane.maximum_phase_error_radians
                    ),
                    "pruned_observation_count": lane.pruned_observation_count,
                }
                for lane in lane_proposals
            ],
            "bounded_rdo_lane_count": len(bounded_lanes),
            "lane_failure_count": len(lane_failures),
            "lane_failures": lane_failures,
            "solver": solver,
            "evaluated_subset_count": len(evaluated),
            "evaluated_subsets": [
                {
                    "lane_keys": [list(key) for key in row.lane_keys],
                    "basis_lengths": [
                        lane.basis_length
                        for lane in bounded_lanes
                        if (lane.path_id, lane.channel) in set(row.lane_keys)
                    ],
                    "placement_counts": [
                        len(lane.instances)
                        for lane in bounded_lanes
                        if (lane.path_id, lane.channel) in set(row.lane_keys)
                    ],
                    "predictor_transport_pcm_identity": (
                        row.predictor_transport_pcm_identity
                    ),
                    "complete_decode_identity": row.complete_decode_identity,
                    "parsed_record_type_counts": {
                        name: count for name, count in row.parsed_record_type_counts
                    },
                    "s11_record_language_only": row.s11_record_language_only,
                    "complete_bytes": len(row.selected_payload),
                    "predictor_bytes": row.predictor_bytes,
                    "residual_bytes": row.residual_bytes,
                    "sse": row.sse,
                    "residual_clip_count": row.residual_clip_count,
                    "transport": row.selected_transport,
                }
                for row in evaluated
            ],
            "truth_fallback_bytes": len(baseline.payload),
            "truth_fallback_sse": baseline_sse,
            "selected_kind": selected_kind,
            "selected_bytes": len(selected_payload),
            "selected_sha256": hashlib.sha256(selected_payload).hexdigest(),
            "retained_lane_keys": [
                [lane.path_id, lane.channel] for lane in retained_lanes
            ],
            "retained_lane_basis_lengths": [
                lane.basis_length for lane in retained_lanes
            ],
            "elapsed_seconds": time.perf_counter() - started,
            "independent_decoder_loop": True,
        },
    )
