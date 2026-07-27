"""R-120 persistent excitation/filter state over the unified MFC1 field.

SFT1 separates a continuous fractional-lag pitch law from a stable reflection-
coefficient vocal-tract law. The independently decoded Innovation is an MFC1
stream, so all band-local primary modes remain available without stacking a
second complete transform stream.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import struct

import numpy as np

from .codec import _quality_report
from .lapped_oracle import _band_edges, analyze_lapped_source
from .maf_cell_oracle import (
    _BitReader,
    _BitWriter,
    _distortion_q20,
    _stochastic_direction,
    decode_maf_cell_stream,
    encode_maf_cell_analysis,
)
from .pvq_envelope_oracle import (
    _gain_code_to_qlog,
    _materialize_band,
    _maximum_gain_code,
    _projected_gain,
    _pulse_shape,
    _pvq_codebook_size,
    _quantize_gain_code,
    _rank_pvq,
    _unrank_pvq,
)
from .rsc1 import SECTION_CRITICAL, RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAGIC = b"SFT1"
VERSION = 2
HEADER = struct.Struct("<4sBBBBIIIIII")
MAX_SAMPLE_COUNT = (1 << 31) - 1
MAX_BLOCK_COUNT = 1 << 20
MAX_FILTER_ORDER = 16
MAX_FILTER_BASIS_COUNT = 64
MAX_REFLECTION_Q7 = 115
MAX_PITCH_GAIN_Q7 = 115
MIN_PITCH_HZ = 60
MAX_PITCH_HZ = 400
MAX_RESIDUAL_BYTES = 512 << 20
EXCITATION_MAGIC = b"EPV1"
EXCITATION_VERSION = 2
EXCITATION_HEADER = struct.Struct("<4sBHHIII")
EXCITATION_GAIN_FRACTION_BITS = 4
MAX_EXCITATION_SUBFRAME = 512
MAX_EXCITATION_PULSES = 64


@dataclass(frozen=True)
class PitchLaw:
    """One block-end target for a linearly interpolated fractional delay."""

    lag_q8: int
    gain_q7: int


@dataclass(frozen=True)
class FilterLaw:
    """Stable lattice reflection coefficients held until an update event."""

    reflection_q7: tuple[int, ...]


@dataclass(frozen=True)
class MafSourceFilterAnalysis:
    """Selected persistent laws and exact pre-quantization Innovation."""

    sample_rate: int
    source: np.ndarray
    block_size: int
    filter_order: int
    pitch_laws: tuple[PitchLaw, ...]
    filter_laws: tuple[FilterLaw, ...]
    filter_bases: tuple[FilterLaw, ...]
    innovation: np.ndarray
    lapped_analysis: object
    parameter_report: dict


@dataclass(frozen=True)
class MafSourceFilterResult:
    """Complete SFT1 stream, actual decode, and exact rate ledger."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


@dataclass(frozen=True)
class _ExcitationResult:
    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _round_divide_signed(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("signed division requires a positive denominator")
    magnitude = abs(numerator)
    quotient, remainder = divmod(magnitude, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return -quotient if numerator < 0 else quotient


def _signed_exp_golomb_bits(value: int) -> int:
    mapped = 2 * value if value >= 0 else -2 * value - 1
    return 2 * (mapped + 1).bit_length() - 1


def _unsigned_exp_golomb_bits(value: int) -> int:
    if value < 0:
        raise ValueError("Exp-Golomb value must be nonnegative")
    return 2 * (value + 1).bit_length() - 1


def _pitch_bounds_q8(sample_rate: int) -> tuple[int, int]:
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("SFT1 sample rate exceeds the profile")
    minimum = max(1, (sample_rate + MAX_PITCH_HZ - 1) // MAX_PITCH_HZ)
    maximum = sample_rate // MIN_PITCH_HZ
    return minimum << 8, maximum << 8


def _fit_pitch_law(
    source: np.ndarray,
    sample_rate: int,
    start: int,
    stop: int,
) -> PitchLaw:
    minimum_q8, maximum_q8 = _pitch_bounds_q8(sample_rate)
    minimum_lag = minimum_q8 >> 8
    maximum_lag = min(maximum_q8 >> 8, start)
    if maximum_lag < minimum_lag or stop <= start:
        return PitchLaw(0, 0)
    current = source[start:stop].astype(np.float64)
    current -= np.mean(current)
    current_energy = float(current @ current)
    if current_energy < 64.0 * 64.0 * current.size:
        return PitchLaw(0, 0)

    best_lag = 0
    best_correlation = 0.0
    best_dot = 0.0
    best_past_energy = 0.0
    for lag in range(minimum_lag, maximum_lag + 1):
        past = source[start - lag : stop - lag].astype(np.float64)
        past -= np.mean(past)
        past_energy = float(past @ past)
        if past_energy <= 0.0:
            continue
        dot = float(current @ past)
        correlation = dot / math.sqrt(current_energy * past_energy)
        if correlation > best_correlation:
            best_lag = lag
            best_correlation = correlation
            best_dot = dot
            best_past_energy = past_energy
    if best_correlation < 0.42 or best_dot <= 0.0:
        return PitchLaw(0, 0)

    # A three-point parabolic refinement supplies a continuous Q8 delay law
    # without making floating-point fitting normative.
    lag_fraction = 0.0
    if minimum_lag < best_lag < maximum_lag:
        correlations = []
        for lag in (best_lag - 1, best_lag, best_lag + 1):
            past = source[start - lag : stop - lag].astype(np.float64)
            past -= np.mean(past)
            denominator = math.sqrt(float(past @ past) * current_energy)
            correlations.append(
                0.0 if denominator == 0.0 else float(current @ past) / denominator
            )
        left, center, right = correlations
        curvature = left - 2.0 * center + right
        if curvature < -1.0e-9:
            lag_fraction = max(
                -0.5,
                min(0.5, 0.5 * (left - right) / curvature),
            )
    lag_q8 = int(round((best_lag + lag_fraction) * 256.0))
    gain = min(
        MAX_PITCH_GAIN_Q7 / 128.0,
        best_dot / max(best_past_energy, 1.0),
    )
    gain_q7 = max(1, min(MAX_PITCH_GAIN_Q7, int(round(gain * 128.0))))
    return PitchLaw(lag_q8, gain_q7)


def _interpolated_pitch(
    start_law: PitchLaw,
    end_law: PitchLaw,
    offset: int,
    length: int,
) -> PitchLaw:
    if length <= 1:
        return end_law
    denominator = length - 1
    lag_q8 = _round_divide_signed(
        start_law.lag_q8 * (denominator - offset)
        + end_law.lag_q8 * offset,
        denominator,
    )
    gain_q7 = _round_divide_signed(
        start_law.gain_q7 * (denominator - offset)
        + end_law.gain_q7 * offset,
        denominator,
    )
    if lag_q8 <= 0 or gain_q7 <= 0:
        return PitchLaw(0, 0)
    return PitchLaw(lag_q8, gain_q7)


def _fractional_delayed_sample(
    history: np.ndarray,
    index: int,
    lag_q8: int,
) -> int:
    if lag_q8 <= 0:
        return 0
    whole = lag_q8 >> 8
    fraction = lag_q8 & 0xFF
    newer = index - whole
    older = newer - 1
    if older < 0 or newer >= index:
        return 0
    return _round_divide_signed(
        (256 - fraction) * int(history[newer])
        + fraction * int(history[older]),
        256,
    )


def _fit_reflection_law(
    pitch_residual: np.ndarray,
    order: int,
) -> FilterLaw:
    centered = pitch_residual.astype(np.float64)
    centered -= np.mean(centered)
    correlation = np.asarray(
        [
            float(centered[lag:] @ centered[: centered.size - lag])
            for lag in range(order + 1)
        ],
        dtype=np.float64,
    )
    if correlation[0] <= 1.0:
        return FilterLaw((0,) * order)
    coefficients = np.zeros(order + 1, dtype=np.float64)
    coefficients[0] = 1.0
    error = correlation[0]
    reflection = []
    for stage in range(1, order + 1):
        numerator = correlation[stage]
        for index in range(1, stage):
            numerator += coefficients[index] * correlation[stage - index]
        value = -numerator / max(error, 1.0)
        value = max(-0.8984375, min(0.8984375, value))
        previous = coefficients.copy()
        for index in range(1, stage):
            coefficients[index] = (
                previous[index] + value * previous[stage - index]
            )
        coefficients[stage] = value
        reflection.append(
            max(
                -MAX_REFLECTION_Q7,
                min(MAX_REFLECTION_Q7, int(round(value * 128.0))),
            )
        )
        error *= max(1.0e-6, 1.0 - value * value)
    return FilterLaw(tuple(reflection))


def _lpc_q14(law: FilterLaw) -> tuple[int, ...]:
    """Step up stable quantized reflection coefficients to Q14 LPC."""

    coefficients: list[int] = []
    for reflection_q7 in law.reflection_q7:
        reflection_q14 = reflection_q7 << 7
        previous = coefficients
        updated = [0] * (len(previous) + 1)
        for index in range(len(previous)):
            updated[index] = previous[index] + _round_divide_signed(
                reflection_q14 * previous[-1 - index],
                1 << 14,
            )
        updated[-1] = reflection_q14
        coefficients = updated
    return tuple(coefficients)


def _analyze_candidate_block(
    source: np.ndarray,
    accepted_excitation: np.ndarray,
    start: int,
    stop: int,
    start_pitch: PitchLaw,
    end_pitch: PitchLaw,
    filter_law: FilterLaw,
) -> tuple[np.ndarray, np.ndarray] | None:
    lpc = _lpc_q14(filter_law)
    innovation = np.empty(stop - start, dtype=np.int64)
    excitation = np.empty(stop, dtype=np.int64)
    excitation[:start] = accepted_excitation[:start]
    for local, index in enumerate(range(start, stop)):
        short_accumulator = 0
        for order_index, coefficient in enumerate(lpc, start=1):
            past_index = index - order_index
            if past_index >= 0:
                short_accumulator += coefficient * int(
                    source[past_index]
                )
        short_prediction = -_round_divide_signed(
            short_accumulator,
            1 << 14,
        )
        current_excitation = int(source[index]) - short_prediction
        pitch = _interpolated_pitch(
            start_pitch,
            end_pitch,
            local,
            stop - start,
        )
        delayed = _fractional_delayed_sample(
            excitation,
            index,
            pitch.lag_q8,
        )
        long_prediction = _round_divide_signed(
            pitch.gain_q7 * delayed,
            128,
        )
        value = current_excitation - long_prediction
        if value < -32768 or value > 32767:
            return None
        innovation[local] = value
        excitation[index] = current_excitation
    return excitation[start:stop], innovation


def _parameter_bits(
    previous_pitch: PitchLaw,
    pitch: PitchLaw,
    previous_filter: FilterLaw,
    filter_law: FilterLaw,
) -> int:
    bits = 0
    if pitch != previous_pitch:
        bits += 2 + _unsigned_exp_golomb_bits(pitch.lag_q8) + 7
    if filter_law != previous_filter:
        bits += 2
        bits += sum(
            _signed_exp_golomb_bits(current - previous)
            for current, previous in zip(
                filter_law.reflection_q7,
                previous_filter.reflection_q7,
                strict=True,
            )
        )
    return bits


def _residual_proxy_bits(innovation: np.ndarray) -> float:
    magnitude = np.abs(innovation.astype(np.float64))
    return float(np.sum(np.log2(1.0 + magnitude)))


def _learn_filter_bases(
    laws: tuple[FilterLaw, ...],
    *,
    requested_count: int,
    iterations: int,
) -> tuple[FilterLaw, ...]:
    """Build a deterministic immutable codebook for vocal-tract state."""

    if not 1 <= requested_count <= MAX_FILTER_BASIS_COUNT:
        raise ValueError("SFT1 filter Basis count exceeds the profile")
    if not 1 <= iterations <= 64:
        raise ValueError("SFT1 filter Basis iterations exceed the profile")
    order = len(laws[0].reflection_q7)
    vectors = np.asarray(
        [law.reflection_q7 for law in laws],
        dtype=np.int16,
    )
    unique, counts = np.unique(vectors, axis=0, return_counts=True)
    zero = np.zeros(order, dtype=np.int16)
    zero_rows = np.flatnonzero(np.all(unique == zero, axis=1))
    if zero_rows.size == 0:
        unique = np.concatenate((zero[None, :], unique), axis=0)
        counts = np.concatenate((np.zeros(1, dtype=counts.dtype), counts))
    elif zero_rows[0] != 0:
        zero_index = int(zero_rows[0])
        order_indices = np.concatenate(
            (
                np.asarray([zero_index]),
                np.delete(np.arange(unique.shape[0]), zero_index),
            )
        )
        unique = unique[order_indices]
        counts = counts[order_indices]

    center_count = min(requested_count, unique.shape[0])
    centers = [zero.astype(np.int64)]
    while len(centers) < center_count:
        center_array = np.stack(centers)
        delta = unique[:, None, :].astype(np.int64) - center_array[None, :, :]
        nearest = np.min(np.sum(delta * delta, axis=2), axis=1)
        score = nearest * np.maximum(1, counts.astype(np.int64))
        selected = int(np.argmax(score))
        if nearest[selected] == 0:
            break
        centers.append(unique[selected].astype(np.int64))

    center_array = np.stack(centers)
    for _ in range(iterations):
        delta = unique[:, None, :].astype(np.int64) - center_array[None, :, :]
        assignments = np.argmin(np.sum(delta * delta, axis=2), axis=1)
        updated = center_array.copy()
        updated[0] = 0
        for center_index in range(1, center_array.shape[0]):
            members = assignments == center_index
            if not np.any(members):
                continue
            weights = counts[members].astype(np.int64)
            numerator = np.sum(
                unique[members].astype(np.int64) * weights[:, None],
                axis=0,
            )
            updated[center_index] = np.rint(
                numerator / max(1, int(np.sum(weights)))
            ).astype(np.int64)
        updated = np.clip(updated, -MAX_REFLECTION_Q7, MAX_REFLECTION_Q7)
        if np.array_equal(updated, center_array):
            break
        center_array = updated

    bases = []
    seen = set()
    for center in center_array:
        law = FilterLaw(tuple(int(value) for value in center))
        if law not in seen:
            seen.add(law)
            bases.append(law)
    return tuple(bases)


def _requantize_filter_path(
    source: np.ndarray,
    block_size: int,
    pitch_laws: tuple[PitchLaw, ...],
    proposed_filters: tuple[FilterLaw, ...],
    bases: tuple[FilterLaw, ...],
) -> tuple[tuple[FilterLaw, ...], np.ndarray]:
    """Select a bounded cached filter Basis and recompute exact Innovation."""

    pitch_residual = np.zeros(source.size, dtype=np.int64)
    innovation = np.empty(source.size, dtype=np.int16)
    selected_filters = []
    previous_pitch = PitchLaw(0, 0)
    basis_vectors = np.asarray(
        [basis.reflection_q7 for basis in bases],
        dtype=np.int16,
    )
    for block_index, (pitch, proposed) in enumerate(
        zip(pitch_laws, proposed_filters, strict=True)
    ):
        start = block_index * block_size
        stop = min(source.size, start + block_size)
        proposed_vector = np.asarray(proposed.reflection_q7, dtype=np.int16)
        delta = basis_vectors.astype(np.int64) - proposed_vector.astype(np.int64)
        order = np.argsort(np.sum(delta * delta, axis=1), kind="stable")
        selected = None
        for basis_index in order:
            filter_law = bases[int(basis_index)]
            analyzed = _analyze_candidate_block(
                source,
                pitch_residual,
                start,
                stop,
                previous_pitch,
                pitch,
                filter_law,
            )
            if analyzed is not None:
                selected = (filter_law, *analyzed)
                break
        if selected is None:
            raise RuntimeError("SFT1 cached filter Basis has no bounded state")
        filter_law, local_pitch_residual, local_innovation = selected
        pitch_residual[start:stop] = local_pitch_residual
        innovation[start:stop] = local_innovation.astype(np.int16)
        selected_filters.append(filter_law)
        previous_pitch = pitch
    return tuple(selected_filters), innovation


def analyze_maf_source_filter_source(
    samples: np.ndarray,
    sample_rate: int,
    *,
    block_size: int = 512,
    filter_order: int = 10,
    parameter_lambda: float = 4.0,
    filter_basis_count: int = 16,
    filter_basis_iterations: int = 8,
    half_window: int = 512,
    band_count: int = 24,
    native_analyzer=None,
) -> MafSourceFilterAnalysis:
    """Select independently lived pitch/filter laws before MFC1 RDO."""

    source_view = np.asarray(samples)
    if source_view.dtype != np.int16 or source_view.ndim != 1:
        raise TypeError("SFT1 input must be mono int16 PCM")
    if source_view.size > MAX_SAMPLE_COUNT:
        raise ValueError("SFT1 sample count exceeds the profile")
    if not 64 <= block_size <= 8192:
        raise ValueError("SFT1 block size exceeds the profile")
    if not 1 <= filter_order <= MAX_FILTER_ORDER:
        raise ValueError("SFT1 filter order exceeds the profile")
    if not 0.0 <= parameter_lambda <= 1024.0:
        raise ValueError("SFT1 parameter lambda exceeds the profile")
    _pitch_bounds_q8(sample_rate)

    source = np.array(source_view, dtype=np.int16, copy=True)
    block_count = (source.size + block_size - 1) // block_size
    if block_count > MAX_BLOCK_COUNT:
        raise ValueError("SFT1 block count exceeds the profile")
    zero_pitch = PitchLaw(0, 0)
    zero_filter = FilterLaw((0,) * filter_order)
    accepted_pitch = zero_pitch
    accepted_filter = zero_filter
    pitch_laws = []
    filter_laws = []
    pitch_residual = np.zeros(source.size, dtype=np.int64)
    innovation = np.empty(source.size, dtype=np.int16)
    pitch_updates = 0
    filter_updates = 0

    for block_index in range(block_count):
        start = block_index * block_size
        stop = min(source.size, start + block_size)
        proposed_filter = _fit_reflection_law(
            source[start:stop],
            filter_order,
        )
        filter_candidates = tuple(
            dict.fromkeys((accepted_filter, proposed_filter, zero_filter))
        )
        candidates = []
        for filter_law in filter_candidates:
            excitation_probe = _analyze_candidate_block(
                source,
                pitch_residual,
                start,
                stop,
                zero_pitch,
                zero_pitch,
                filter_law,
            )
            if excitation_probe is None:
                continue
            local_excitation, _unused = excitation_probe
            excitation_history = np.empty(stop, dtype=np.int64)
            excitation_history[:start] = pitch_residual[:start]
            excitation_history[start:stop] = local_excitation
            proposed_pitch = _fit_pitch_law(
                excitation_history,
                sample_rate,
                start,
                stop,
            )
            pitch_candidates = tuple(
                dict.fromkeys((accepted_pitch, proposed_pitch, zero_pitch))
            )
            for pitch in pitch_candidates:
                analyzed = _analyze_candidate_block(
                    source,
                    pitch_residual,
                    start,
                    stop,
                    accepted_pitch,
                    pitch,
                    filter_law,
                )
                if analyzed is None:
                    continue
                local_pitch_residual, local_innovation = analyzed
                parameter_bits = _parameter_bits(
                    accepted_pitch,
                    pitch,
                    accepted_filter,
                    filter_law,
                )
                cost = (
                    _residual_proxy_bits(local_innovation)
                    + parameter_lambda * parameter_bits
                )
                candidates.append(
                    (
                        cost,
                        parameter_bits,
                        _residual_proxy_bits(local_innovation),
                        pitch,
                        filter_law,
                        local_pitch_residual,
                        local_innovation,
                    )
                )
        if not candidates:
            raise RuntimeError("SFT1 has no bounded block candidate")
        (
            _cost,
            _bits,
            _residual_bits,
            selected_pitch,
            selected_filter,
            local_pitch_residual,
            local_innovation,
        ) = min(
            candidates,
            key=lambda item: (
                item[0],
                item[1],
                item[2],
                item[3].lag_q8,
                item[4].reflection_q7,
            ),
        )
        pitch_updates += selected_pitch != accepted_pitch
        filter_updates += selected_filter != accepted_filter
        accepted_pitch = selected_pitch
        accepted_filter = selected_filter
        pitch_laws.append(selected_pitch)
        filter_laws.append(selected_filter)
        pitch_residual[start:stop] = local_pitch_residual
        innovation[start:stop] = local_innovation.astype(np.int16)

    pitch_path = tuple(pitch_laws)
    proposed_filter_path = tuple(filter_laws)
    filter_bases = _learn_filter_bases(
        proposed_filter_path,
        requested_count=filter_basis_count,
        iterations=filter_basis_iterations,
    )
    filter_path, innovation = _requantize_filter_path(
        source,
        block_size,
        pitch_path,
        proposed_filter_path,
        filter_bases,
    )
    used_filter_bases = {FilterLaw((0,) * filter_order)}
    used_filter_bases.update(filter_path)
    filter_bases = tuple(
        basis for basis in filter_bases if basis in used_filter_bases
    )
    if not filter_bases or any(law not in filter_bases for law in filter_path):
        raise RuntimeError("SFT1 filter path escaped its immutable Basis bank")
    filter_updates = sum(
        current != previous
        for current, previous in zip(
            filter_path,
            (FilterLaw((0,) * filter_order), *filter_path[:-1]),
            strict=True,
        )
    )

    exact = _synthesize_source_filter(
        innovation,
        block_size,
        pitch_path,
        filter_path,
    )
    if not np.array_equal(exact, source):
        raise RuntimeError("SFT1 exact analysis/synthesis invariant failed")
    lapped_analysis = analyze_lapped_source(
        innovation[:, None],
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_analyzer,
    )
    source.flags.writeable = False
    innovation.flags.writeable = False
    return MafSourceFilterAnalysis(
        sample_rate,
        source,
        block_size,
        filter_order,
        pitch_path,
        filter_path,
        filter_bases,
        innovation,
        lapped_analysis,
        {
            "block_count": block_count,
            "pitch_update_count": pitch_updates,
            "filter_update_count": filter_updates,
            "pitch_hold_count": block_count - pitch_updates,
            "filter_hold_count": block_count - filter_updates,
            "parameter_lambda": parameter_lambda,
            "filter_basis_count": len(filter_bases),
            "filter_basis_iterations": filter_basis_iterations,
        },
    )


def _pack_parameter_events(
    analysis: MafSourceFilterAnalysis,
) -> tuple[bytes, int, int]:
    writer = _BitWriter()
    writer.write_unsigned_exp_golomb(len(analysis.filter_bases))
    filter_width = max(1, (len(analysis.filter_bases) - 1).bit_length())
    filter_ids = {
        filter_law: index
        for index, filter_law in enumerate(analysis.filter_bases)
    }
    for filter_law in analysis.filter_bases:
        for coefficient in filter_law.reflection_q7:
            writer.write_bits(coefficient & 0xFF, 8)
    events = []
    previous_pitch = PitchLaw(0, 0)
    previous_filter = FilterLaw((0,) * analysis.filter_order)
    for block_index, (pitch, filter_law) in enumerate(
        zip(analysis.pitch_laws, analysis.filter_laws, strict=True)
    ):
        pitch_changed = pitch != previous_pitch
        filter_changed = filter_law != previous_filter
        if pitch_changed or filter_changed:
            events.append(
                (
                    block_index,
                    pitch_changed,
                    filter_changed,
                    pitch,
                    filter_law,
                )
            )
        previous_pitch = pitch
        previous_filter = filter_law

    writer.write_unsigned_exp_golomb(len(events))
    previous_block = -1
    previous_pitch = PitchLaw(0, 0)
    previous_filter = FilterLaw((0,) * analysis.filter_order)
    for block_index, pitch_changed, filter_changed, pitch, filter_law in events:
        writer.write_unsigned_exp_golomb(block_index - previous_block - 1)
        flags = int(pitch_changed) | (int(filter_changed) << 1)
        writer.write_bits(flags, 2)
        if pitch_changed:
            writer.write_unsigned_exp_golomb(pitch.lag_q8)
            writer.write_bits(pitch.gain_q7, 7)
            previous_pitch = pitch
        if filter_changed:
            writer.write_bits(filter_ids[filter_law], filter_width)
            previous_filter = filter_law
        previous_block = block_index
    return writer.finish(), writer.bit_count, len(events)


def _unpack_parameter_events(
    payload: bytes,
    bit_count: int,
    *,
    block_count: int,
    filter_order: int,
    sample_rate: int,
) -> tuple[tuple[PitchLaw, ...], tuple[FilterLaw, ...]]:
    reader = _BitReader(payload, bit_count)
    filter_basis_count = reader.read_unsigned_exp_golomb(
        MAX_FILTER_BASIS_COUNT
    )
    if filter_basis_count == 0:
        raise ValueError("SFT1 requires a cached filter Basis")
    filter_bases = []
    for _ in range(filter_basis_count):
        coefficients = []
        for _ in range(filter_order):
            value = reader.read_bits(8)
            value = value - 256 if value & 0x80 else value
            if abs(value) > MAX_REFLECTION_Q7:
                raise ValueError("SFT1 filter Basis exceeds the profile")
            coefficients.append(value)
        filter_bases.append(FilterLaw(tuple(coefficients)))
    if filter_bases[0] != FilterLaw((0,) * filter_order):
        raise ValueError("SFT1 filter Basis zero state is not canonical")
    if len(set(filter_bases)) != len(filter_bases):
        raise ValueError("SFT1 filter Basis bank contains duplicates")
    filter_width = max(1, (filter_basis_count - 1).bit_length())
    event_count = reader.read_unsigned_exp_golomb(block_count)
    events = {}
    previous_block = -1
    previous_pitch = PitchLaw(0, 0)
    previous_filter = FilterLaw((0,) * filter_order)
    minimum_lag_q8, maximum_lag_q8 = _pitch_bounds_q8(sample_rate)
    for _ in range(event_count):
        gap = reader.read_unsigned_exp_golomb(block_count)
        block_index = previous_block + 1 + gap
        if block_index >= block_count:
            raise ValueError("SFT1 event index exceeds the stream")
        flags = reader.read_bits(2)
        if flags == 0:
            raise ValueError("SFT1 empty parameter event")
        pitch = previous_pitch
        filter_law = previous_filter
        if flags & 1:
            lag_q8 = reader.read_unsigned_exp_golomb(maximum_lag_q8)
            gain_q7 = reader.read_bits(7)
            if (lag_q8 == 0) != (gain_q7 == 0):
                raise ValueError("SFT1 zero pitch law is non-canonical")
            if lag_q8 and (
                not minimum_lag_q8 <= lag_q8 <= maximum_lag_q8
                or gain_q7 > MAX_PITCH_GAIN_Q7
            ):
                raise ValueError("SFT1 pitch law exceeds the profile")
            pitch = PitchLaw(lag_q8, gain_q7)
            previous_pitch = pitch
        if flags & 2:
            filter_id = reader.read_bits(filter_width)
            if filter_id >= filter_basis_count:
                raise ValueError("SFT1 filter Basis reference exceeds the bank")
            filter_law = filter_bases[filter_id]
            previous_filter = filter_law
        events[block_index] = (pitch, filter_law)
        previous_block = block_index
    reader.require_canonical_end()

    pitch_laws = []
    filter_laws = []
    pitch = PitchLaw(0, 0)
    filter_law = FilterLaw((0,) * filter_order)
    for block_index in range(block_count):
        if block_index in events:
            pitch, filter_law = events[block_index]
        pitch_laws.append(pitch)
        filter_laws.append(filter_law)
    return tuple(pitch_laws), tuple(filter_laws)


def _synthesize_source_filter(
    innovation: np.ndarray,
    block_size: int,
    pitch_laws: tuple[PitchLaw, ...],
    filter_laws: tuple[FilterLaw, ...],
) -> np.ndarray:
    innovation64 = np.asarray(innovation, dtype=np.int64)
    output = np.empty(innovation64.size, dtype=np.int64)
    excitation = np.empty(innovation64.size, dtype=np.int64)
    previous_pitch = PitchLaw(0, 0)
    for block_index, (pitch, filter_law) in enumerate(
        zip(pitch_laws, filter_laws, strict=True)
    ):
        start = block_index * block_size
        stop = min(output.size, start + block_size)
        lpc = _lpc_q14(filter_law)
        for local, index in enumerate(range(start, stop)):
            law = _interpolated_pitch(
                previous_pitch,
                pitch,
                local,
                stop - start,
            )
            delayed = _fractional_delayed_sample(
                excitation,
                index,
                law.lag_q8,
            )
            long_prediction = _round_divide_signed(
                law.gain_q7 * delayed,
                128,
            )
            excitation[index] = int(innovation64[index]) + long_prediction

            short_accumulator = 0
            for order_index, coefficient in enumerate(lpc, start=1):
                past_index = index - order_index
                if past_index >= 0:
                    short_accumulator += coefficient * int(output[past_index])
            short_prediction = -_round_divide_signed(
                short_accumulator,
                1 << 14,
            )
            output[index] = np.clip(
                excitation[index] + short_prediction,
                -32768,
                32767,
            )
        previous_pitch = pitch
    return output.astype(np.int16)


def _synthesis_distortion_weights_q8(
    analysis: MafSourceFilterAnalysis,
) -> np.ndarray:
    """Approximate decoded-error amplification of pitch and vocal tract."""

    lapped = analysis.lapped_analysis
    edges = _band_edges(lapped.half_window, lapped.band_count)
    weights = np.empty(
        (1, lapped.frame_count, lapped.band_count),
        dtype=np.uint16,
    )
    for frame in range(lapped.frame_count):
        sample = min(
            max(0, analysis.source.size - 1),
            frame * lapped.half_window,
        )
        block = min(
            len(analysis.pitch_laws) - 1,
            sample // analysis.block_size,
        )
        pitch = analysis.pitch_laws[block]
        lpc = np.asarray(
            _lpc_q14(analysis.filter_laws[block]),
            dtype=np.float64,
        ) / float(1 << 14)
        raw = np.empty(lapped.band_count, dtype=np.float64)
        for band in range(lapped.band_count):
            center_bin = 0.5 * (edges[band] + edges[band + 1] - 1)
            omega = math.pi * (center_bin + 0.5) / lapped.half_window
            denominator = 1.0 + 0.0j
            for order_index, coefficient in enumerate(lpc, start=1):
                denominator += coefficient * np.exp(
                    -1j * omega * order_index
                )
            short_gain = 1.0 / max(
                1.0e-4,
                abs(denominator) ** 2,
            )
            long_gain = 1.0
            if pitch.gain_q7 and pitch.lag_q8:
                lag = pitch.lag_q8 / 256.0
                gain = pitch.gain_q7 / 128.0
                pitch_denominator = 1.0 - gain * np.exp(
                    -1j * omega * lag
                )
                long_gain = 1.0 / max(
                    1.0e-4,
                    abs(pitch_denominator) ** 2,
                )
            raw[band] = min(16.0, max(0.125, short_gain * long_gain))
        raw /= max(1.0e-6, float(np.mean(raw)))
        raw = np.clip(raw, 0.25, 8.0)
        weights[0, frame] = np.clip(
            np.rint(raw * 256.0),
            1,
            4096,
        ).astype(np.uint16)
    return weights


def _desired_short_excitation_target(
    analysis: MafSourceFilterAnalysis,
    start: int,
    stop: int,
) -> np.ndarray:
    target = np.empty(stop - start, dtype=np.int64)
    for local, index in enumerate(range(start, stop)):
        block = min(
            len(analysis.filter_laws) - 1,
            index // analysis.block_size,
        )
        lpc = _lpc_q14(analysis.filter_laws[block])
        accumulator = 0
        for order_index, coefficient in enumerate(lpc, start=1):
            past_index = index - order_index
            if past_index >= 0:
                accumulator += coefficient * int(
                    analysis.source[past_index]
                )
        short_prediction = -_round_divide_signed(
            accumulator,
            1 << 14,
        )
        target[local] = int(analysis.source[index]) - short_prediction
    return target


def _adaptive_vector(
    history: np.ndarray,
    start: int,
    stop: int,
    lag: int,
    gain_q7: int,
) -> np.ndarray:
    if lag <= 0 or gain_q7 <= 0:
        return np.zeros(stop - start, dtype=np.int64)
    past = history[start - lag : stop - lag].astype(np.int64)
    scaled = past * gain_q7
    return np.where(
        scaled >= 0,
        (scaled + 64) // 128,
        -((-scaled + 64) // 128),
    ).astype(np.int64)


def _search_adaptive_state(
    target: np.ndarray,
    history: np.ndarray,
    *,
    start: int,
    stop: int,
    sample_rate: int,
    previous_lag: int,
    previous_gain_q7: int,
    quality_guard_q12: int,
) -> tuple[int, int, np.ndarray]:
    candidates = [(0, 0)]
    if previous_lag and previous_lag <= start:
        candidates.append((previous_lag, previous_gain_q7))
    minimum_lag = max(target.size, (sample_rate + MAX_PITCH_HZ - 1) // MAX_PITCH_HZ)
    maximum_lag = min(start, sample_rate // MIN_PITCH_HZ)
    best = None
    target_energy = int(target @ target)
    if maximum_lag >= minimum_lag and target_energy > 0:
        for lag in range(minimum_lag, maximum_lag + 1):
            past = history[start - lag : stop - lag].astype(np.int64)
            energy = int(past @ past)
            dot = int(target @ past)
            if energy <= 0 or dot <= 0:
                continue
            gain_q7 = min(
                MAX_PITCH_GAIN_Q7,
                max(1, _round_divide_signed(dot * 128, energy)),
            )
            score = dot * dot // energy
            if best is None or (score, -abs(lag - previous_lag), -lag) > best[0]:
                best = ((score, -abs(lag - previous_lag), -lag), lag, gain_q7)
        if best is not None and best[0][0] * 10 >= target_energy:
            candidates.append((best[1], best[2]))

    evaluated = []
    for lag, gain_q7 in tuple(dict.fromkeys(candidates)):
        vector = _adaptive_vector(
            history,
            start,
            stop,
            lag,
            gain_q7,
        )
        changed = (lag, gain_q7) != (previous_lag, previous_gain_q7)
        signal_bits = 1
        if changed:
            signal_bits += 1
            if lag:
                signal_bits += _signed_exp_golomb_bits(
                    lag - previous_lag
                )
                signal_bits += _signed_exp_golomb_bits(
                    gain_q7 - previous_gain_q7
                )
        evaluated.append(
            (
                _distortion_q20(target, vector),
                signal_bits,
                lag,
                gain_q7,
                vector,
            )
        )
    minimum_distortion = min(item[0] for item in evaluated)
    maximum_distortion = (
        minimum_distortion * quality_guard_q12 + 2048
    ) >> 12
    return min(
        (
            item
            for item in evaluated
            if item[0] <= maximum_distortion
        ),
        key=lambda item: (item[1], item[0], item[2], item[3]),
    )[2:]


def _encode_excitation_pvq(
    innovation: np.ndarray,
    *,
    subframe_size: int,
    pulses: int,
    rate_lambda_q20: int,
    quality_guard_q12: int | None,
    stream_seed: int,
    source_filter_analysis: MafSourceFilterAnalysis | None = None,
    adaptive_quality_guard_q12: int = 4608,
) -> _ExcitationResult:
    """Encode bounded adaptive/stochastic excitation without an MDCT layer."""

    if not 16 <= subframe_size <= MAX_EXCITATION_SUBFRAME:
        raise ValueError("EPV1 subframe size exceeds the profile")
    if not 1 <= pulses <= MAX_EXCITATION_PULSES:
        raise ValueError("EPV1 pulse count exceeds the profile")
    if rate_lambda_q20 < 0:
        raise ValueError("EPV1 rate lambda must be nonnegative")
    if quality_guard_q12 is not None and not 4096 <= quality_guard_q12 <= 8192:
        raise ValueError("EPV1 quality guard exceeds the profile")
    if not 4096 <= adaptive_quality_guard_q12 <= 8192:
        raise ValueError("EPV1 adaptive quality guard exceeds the profile")

    source = np.asarray(innovation, dtype=np.int16)
    writer = _BitWriter()
    reconstruction = np.zeros(source.size, dtype=np.int16)
    decoded_excitation = np.zeros(source.size, dtype=np.int64)
    previous_gain = 0
    previous_pitch_lag = 0
    previous_pitch_gain_q7 = 0
    pitch_updates = 0
    mode_counts = {"PVQ": 0, "STOCHASTIC": 0, "ZERO": 0}
    subframe_count = (source.size + subframe_size - 1) // subframe_size
    for subframe in range(subframe_count):
        start = subframe * subframe_size
        stop = min(source.size, start + subframe_size)
        if source_filter_analysis is not None:
            desired_excitation = _desired_short_excitation_target(
                source_filter_analysis,
                start,
                stop,
            )
            (
                pitch_lag,
                pitch_gain_q7,
                adaptive,
            ) = _search_adaptive_state(
                desired_excitation,
                decoded_excitation,
                start=start,
                stop=stop,
                sample_rate=source_filter_analysis.sample_rate,
                previous_lag=previous_pitch_lag,
                previous_gain_q7=previous_pitch_gain_q7,
                quality_guard_q12=adaptive_quality_guard_q12,
            )
            target = desired_excitation - adaptive
        else:
            pitch_lag = 0
            pitch_gain_q7 = 0
            adaptive = np.zeros(stop - start, dtype=np.int64)
            target = source[start:stop].astype(np.int64)
        pitch_changed = (
            pitch_lag != previous_pitch_lag
            or pitch_gain_q7 != previous_pitch_gain_q7
        )
        writer.write_bit(int(pitch_changed))
        if pitch_changed:
            writer.write_bit(int(pitch_lag != 0))
            if pitch_lag:
                writer.write_signed_exp_golomb(
                    pitch_lag - previous_pitch_lag
                )
                writer.write_signed_exp_golomb(
                    pitch_gain_q7 - previous_pitch_gain_q7
                )
            previous_pitch_lag = pitch_lag
            previous_pitch_gain_q7 = pitch_gain_q7
            pitch_updates += 1
        dimension = target.size
        active_pulses = min(pulses, dimension)
        candidates = []
        if np.any(target):
            shape = _pulse_shape(target, active_pulses)
            gain_code = _quantize_gain_code(
                _projected_gain(target, shape),
                EXCITATION_GAIN_FRACTION_BITS,
            )
            if gain_code:
                rank, actual_pulses = _rank_pvq(shape)
                if actual_pulses != active_pulses:
                    raise RuntimeError("EPV1 pulse search changed its budget")
                codebook = _pvq_codebook_size(dimension, active_pulses)
                width = (codebook - 1).bit_length()
                decoded = _materialize_band(
                    shape,
                    _gain_code_to_qlog(
                        gain_code,
                        EXCITATION_GAIN_FRACTION_BITS,
                    ),
                )
                candidates.append(
                    (
                        _distortion_q20(target, decoded),
                        1
                        + _signed_exp_golomb_bits(gain_code - previous_gain)
                        + width,
                        "PVQ",
                        decoded,
                        (gain_code, rank, width),
                    )
                )

            for seed in range(8):
                direction = _stochastic_direction(
                    dimension,
                    stream_seed,
                    0,
                    0,
                    seed,
                    subframe,
                )
                gain_code = _quantize_gain_code(
                    _projected_gain(target, direction),
                    EXCITATION_GAIN_FRACTION_BITS,
                )
                if gain_code == 0:
                    continue
                decoded = _materialize_band(
                    direction,
                    _gain_code_to_qlog(
                        gain_code,
                        EXCITATION_GAIN_FRACTION_BITS,
                    ),
                )
                candidates.append(
                    (
                        _distortion_q20(target, decoded),
                        2
                        + 3
                        + _signed_exp_golomb_bits(
                            gain_code - previous_gain
                        ),
                        "STOCHASTIC",
                        decoded,
                        (seed, gain_code),
                    )
                )
        zero = np.zeros(dimension, dtype=np.int64)
        candidates.append(
            (
                _distortion_q20(target, zero),
                2,
                "ZERO",
                zero,
                (),
            )
        )
        pvq = next(
            (candidate for candidate in candidates if candidate[2] == "PVQ"),
            None,
        )
        if quality_guard_q12 is not None and pvq is not None:
            maximum_distortion = (
                pvq[0] * quality_guard_q12 + 2048
            ) >> 12
            eligible = [
                candidate
                for candidate in candidates
                if candidate[0] <= maximum_distortion
            ]
            winner = min(eligible, key=lambda item: (item[1], item[0], item[2]))
        else:
            winner = min(
                candidates,
                key=lambda item: (
                    item[0] + rate_lambda_q20 * item[1],
                    item[0],
                    item[1],
                    item[2],
                ),
            )
        _distortion, _bits, mode, decoded, fields = winner
        if mode == "PVQ":
            writer.write_bit(0)
            gain_code, rank, width = fields
            writer.write_signed_exp_golomb(gain_code - previous_gain)
            writer.write_bits(rank, width)
            previous_gain = gain_code
        elif mode == "STOCHASTIC":
            writer.write_bits(0b10, 2)
            seed, gain_code = fields
            writer.write_bits(seed, 3)
            writer.write_signed_exp_golomb(gain_code - previous_gain)
            previous_gain = gain_code
        else:
            writer.write_bits(0b11, 2)
        reconstruction[start:stop] = np.clip(
            adaptive + decoded,
            -32768,
            32767,
        ).astype(np.int16)
        decoded_excitation[start:stop] = reconstruction[start:stop]
        mode_counts[mode] += 1

    logical_bits = writer.bit_count
    event_payload = writer.finish()
    payload = EXCITATION_HEADER.pack(
        EXCITATION_MAGIC,
        EXCITATION_VERSION,
        subframe_size,
        pulses,
        source.size,
        logical_bits,
        stream_seed & 0xFFFF_FFFF,
    ) + event_payload
    decoded = _decode_excitation_pvq(payload)
    if not np.array_equal(decoded, reconstruction):
        raise RuntimeError("EPV1 encoder and independent decoder disagree")
    return _ExcitationResult(
        payload,
        reconstruction,
        {
            "stream_bytes": len(payload),
            "logical_bits": logical_bits,
            "padding_bits": len(event_payload) * 8 - logical_bits,
            "subframe_size": subframe_size,
            "subframe_count": subframe_count,
            "pulses": pulses,
            "mode_counts": mode_counts,
            "pitch_update_count": pitch_updates,
            "quality_guard_q12": quality_guard_q12,
            "adaptive_quality_guard_q12": adaptive_quality_guard_q12,
        },
    )


def _decode_excitation_pvq(
    payload: bytes,
) -> np.ndarray:
    if len(payload) < EXCITATION_HEADER.size:
        raise ValueError("truncated EPV1 stream")
    (
        magic,
        version,
        subframe_size,
        pulses,
        sample_count,
        logical_bits,
        stream_seed,
    ) = EXCITATION_HEADER.unpack_from(payload)
    if (
        magic != EXCITATION_MAGIC
        or version != EXCITATION_VERSION
        or not 16 <= subframe_size <= MAX_EXCITATION_SUBFRAME
        or not 1 <= pulses <= MAX_EXCITATION_PULSES
        or sample_count > MAX_SAMPLE_COUNT
        or (logical_bits + 7) // 8 != len(payload) - EXCITATION_HEADER.size
    ):
        raise ValueError("EPV1 header exceeds the profile")
    reader = _BitReader(payload[EXCITATION_HEADER.size :], logical_bits)
    reconstruction = np.zeros(sample_count, dtype=np.int16)
    previous_gain = 0
    pitch_lag = 0
    pitch_gain_q7 = 0
    maximum_gain = _maximum_gain_code(EXCITATION_GAIN_FRACTION_BITS)
    subframe_count = (sample_count + subframe_size - 1) // subframe_size
    for subframe in range(subframe_count):
        start = subframe * subframe_size
        stop = min(sample_count, start + subframe_size)
        dimension = stop - start
        if reader.read_bit():
            if reader.read_bit():
                pitch_lag += reader.read_signed_exp_golomb(sample_count)
                pitch_gain_q7 += reader.read_signed_exp_golomb(
                    MAX_PITCH_GAIN_Q7
                )
                if (
                    pitch_lag < dimension
                    or pitch_lag > start
                    or not 1 <= pitch_gain_q7 <= MAX_PITCH_GAIN_Q7
                ):
                    raise ValueError("EPV1 adaptive state exceeds the profile")
            else:
                pitch_lag = 0
                pitch_gain_q7 = 0
        adaptive = _adaptive_vector(
            reconstruction,
            start,
            stop,
            pitch_lag,
            pitch_gain_q7,
        )
        if reader.read_bit() == 0:
            mode = "PVQ"
        elif reader.read_bit() == 0:
            mode = "STOCHASTIC"
        else:
            mode = "ZERO"
        if mode == "PVQ":
            gain_code = previous_gain + reader.read_signed_exp_golomb(
                maximum_gain
            )
            if not 1 <= gain_code <= maximum_gain:
                raise ValueError("EPV1 gain exceeds the profile")
            active_pulses = min(pulses, dimension)
            codebook = _pvq_codebook_size(dimension, active_pulses)
            rank = reader.read_bits((codebook - 1).bit_length())
            if rank >= codebook:
                raise ValueError("EPV1 PVQ rank exceeds its codebook")
            direction = _unrank_pvq(dimension, active_pulses, rank)
            previous_gain = gain_code
        elif mode == "STOCHASTIC":
            seed = reader.read_bits(3)
            gain_code = previous_gain + reader.read_signed_exp_golomb(
                maximum_gain
            )
            if not 1 <= gain_code <= maximum_gain:
                raise ValueError("EPV1 stochastic gain exceeds the profile")
            direction = _stochastic_direction(
                dimension,
                stream_seed,
                0,
                0,
                seed,
                subframe,
            )
            previous_gain = gain_code
        else:
            decoded = np.zeros(dimension, dtype=np.int64)
        if mode != "ZERO":
            decoded = _materialize_band(
                direction,
                _gain_code_to_qlog(
                    gain_code,
                    EXCITATION_GAIN_FRACTION_BITS,
                ),
            )
        reconstruction[start:stop] = np.clip(
            adaptive + decoded,
            -32768,
            32767,
        ).astype(np.int16)
    reader.require_canonical_end()
    reconstruction.flags.writeable = False
    return reconstruction


def encode_maf_source_filter_analysis(
    analysis: MafSourceFilterAnalysis,
    *,
    maximum_pulses_per_frame: int,
    rate_lambda_q20: int,
    stream_seed: int = 0x5245_534F,
    basis_search_limit: int = 16,
    dictionary_bases_per_band: int = 0,
    dictionary_pulses_per_basis: int = 24,
    synthesis_aware_rdo: bool = False,
    pvq_guard_q12: int | None = None,
    excitation_backend: str = "mfc1",
    excitation_subframe_size: int = 64,
    excitation_pulses: int = 8,
    excitation_quality_guard_q12: int | None = 4096,
    adaptive_quality_guard_q12: int = 4608,
) -> MafSourceFilterResult:
    """Encode one complete source-filter plus unified MFC1 candidate."""

    distortion_weights = (
        _synthesis_distortion_weights_q8(analysis)
        if synthesis_aware_rdo
        else None
    )
    coded_analysis = analysis
    if excitation_backend == "mfc1":
        residual = encode_maf_cell_analysis(
            analysis.lapped_analysis,
            maximum_pulses_per_frame=maximum_pulses_per_frame,
            rate_lambda_q20=rate_lambda_q20,
            stream_seed=stream_seed,
            basis_search_limit=basis_search_limit,
            dictionary_bases_per_band=dictionary_bases_per_band,
            dictionary_pulses_per_basis=dictionary_pulses_per_basis,
            distortion_weights_q8=distortion_weights,
            pvq_guard_q12=pvq_guard_q12,
        )
        residual_kind = 0
    elif excitation_backend == "epvq":
        coded_analysis = replace(
            analysis,
            pitch_laws=tuple(
                PitchLaw(0, 0) for _ in analysis.pitch_laws
            ),
        )
        residual = _encode_excitation_pvq(
            coded_analysis.innovation,
            subframe_size=excitation_subframe_size,
            pulses=excitation_pulses,
            rate_lambda_q20=rate_lambda_q20,
            quality_guard_q12=excitation_quality_guard_q12,
            stream_seed=stream_seed,
            source_filter_analysis=coded_analysis,
            adaptive_quality_guard_q12=adaptive_quality_guard_q12,
        )
        residual_kind = 1
    else:
        raise ValueError("unknown SFT1 excitation backend")
    event_payload, event_bits, event_count = _pack_parameter_events(
        coded_analysis
    )
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            analysis.filter_order,
            residual_kind,
            0,
            analysis.sample_rate,
            int(analysis.source.size),
            analysis.block_size,
            len(analysis.pitch_laws),
            event_bits,
            len(residual.payload),
        )
        + event_payload
        + residual.payload
    )
    payload = pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(
                    StreamConfig(
                        int(analysis.source.size),
                        1,
                        1,
                    )
                ),
            ),
            RSC1Section("SFT1", body),
        ],
        profile=0,
        level=5,
        timebase_hz=analysis.sample_rate,
    )
    sample_rate, reconstruction = decode_maf_source_filter_stream(payload)
    if sample_rate != analysis.sample_rate:
        raise RuntimeError("SFT1 decoder sample rate differs")
    report = {
        **_quality_report(analysis.source, reconstruction),
        "status": "R-120 persistent source-filter over MFC1; non-normative",
        "format_profile": "prospective-SFT1-RSC1-level-5",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "parameter_event_bits": event_bits,
        "parameter_event_count": event_count,
        "parameter_envelope_bytes": len(payload) - len(residual.payload),
        "residual_stream_bytes": len(residual.payload),
        "block_size": analysis.block_size,
        "block_count": len(analysis.pitch_laws),
        "filter_order": analysis.filter_order,
        "source_filter": analysis.parameter_report,
        "synthesis_aware_rdo": synthesis_aware_rdo,
        "pvq_guard_q12": pvq_guard_q12,
        "excitation_backend": excitation_backend,
        "maf_cell": residual.report,
        "reconstruction_backend": (
            "independent Python integer SFT1 plus "
            f"{'MFC1' if residual_kind == 0 else 'EPV1'} decoder"
        ),
    }
    return MafSourceFilterResult(payload, reconstruction, report)


def decode_maf_source_filter_stream(
    payload: bytes,
) -> tuple[int, np.ndarray]:
    """Validate and independently decode one complete SFT1 stream."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 5):
        raise ValueError("unsupported SFT1 research profile")
    config_sections = []
    source_filter_sections = []
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code == b"CONF":
            config_sections.append(section)
        elif type_code == b"SFT1":
            source_filter_sections.append(section)
        elif section.flags & SECTION_CRITICAL:
            raise ValueError("unknown critical SFT1 section")
    if len(config_sections) != 1 or len(source_filter_sections) != 1:
        raise ValueError("non-canonical SFT1 sections")
    config = unpack_conf(config_sections[0].payload)
    body = source_filter_sections[0].payload
    if len(body) < HEADER.size:
        raise ValueError("truncated SFT1 section")
    (
        magic,
        version,
        filter_order,
        flags,
        reserved,
        sample_rate,
        sample_count,
        block_size,
        block_count,
        event_bits,
        residual_bytes,
    ) = HEADER.unpack_from(body)
    event_bytes = (event_bits + 7) // 8
    if (
        magic != MAGIC
        or version != VERSION
        or flags not in {0, 1}
        or reserved != 0
        or not 1 <= filter_order <= MAX_FILTER_ORDER
        or not 64 <= block_size <= 8192
        or block_count != (sample_count + block_size - 1) // block_size
        or block_count > MAX_BLOCK_COUNT
        or sample_count > MAX_SAMPLE_COUNT
        or residual_bytes > MAX_RESIDUAL_BYTES
        or HEADER.size + event_bytes + residual_bytes != len(body)
        or sample_rate != info.timebase_hz
        or sample_count != config.sample_count
        or config.output_channels != 1
        or config.innovation_step != 1
    ):
        raise ValueError("SFT1 header exceeds the profile")
    event_payload = body[HEADER.size : HEADER.size + event_bytes]
    residual_payload = body[HEADER.size + event_bytes :]
    pitch_laws, filter_laws = _unpack_parameter_events(
        event_payload,
        event_bits,
        block_count=block_count,
        filter_order=filter_order,
        sample_rate=sample_rate,
    )
    if flags == 0:
        residual = decode_maf_cell_stream(residual_payload)
        if (
            residual.sample_rate != sample_rate
            or residual.samples.shape != (sample_count, 1)
        ):
            raise ValueError("SFT1 residual configuration mismatch")
        innovation = residual.samples[:, 0]
    else:
        innovation = _decode_excitation_pvq(
            residual_payload,
        )
        if innovation.shape != (sample_count,):
            raise ValueError("SFT1 excitation configuration mismatch")
    reconstruction = _synthesize_source_filter(
        innovation,
        block_size,
        pitch_laws,
        filter_laws,
    )
    reconstruction.flags.writeable = False
    return sample_rate, reconstruction
