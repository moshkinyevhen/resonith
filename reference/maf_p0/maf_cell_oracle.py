"""R-120 event-driven Memory-oriented Acoustic Field research stream.

MFC1 is an independently decodable experiment, not proposed Main syntax. It
tests the defining MAF invariant: unchanged acoustic state costs no per-band
event, while every changed cell selects one primary representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import hashlib
import math
import struct

import numpy as np

from .codec import _quality_report
from .lapped_oracle import (
    MAX_BANDS,
    MAX_CHANNELS,
    MAX_HALF_WINDOW,
    LappedAnalysis,
    _band_edges,
    _synthesize,
)
from .pvq_envelope_oracle import (
    _BitReader,
    _BitWriter,
    _gain_code_to_qlog,
    _decoded_log_gain,
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


MAGIC = b"MFC1"
VERSION = 3
GAIN_FRACTION_BITS = 4
HEADER = struct.Struct("<4sBBHIIHHIII")
DICTIONARY_MAGIC = b"MBD1"
DICTIONARY_VERSION = 1
DICTIONARY_HEADER = struct.Struct("<4sBHI")
MAX_PAYLOAD_BYTES = 512 << 20
MAX_PULSES_PER_BAND = 255
MAX_BASIS_COUNT = 256
MAX_STOCHASTIC_SEEDS = 32
MAX_TRANSIENT_COEFFICIENTS = 8
MAX_BASIS_CORRECTIONS = 6
MAX_CORRECTION_ABSOLUTE = (1 << 23) - 1
MAX_SHIFT = 7
MAX_TILT = 7


class CellMode(IntEnum):
    """Explicit mutations; an omitted band is the zero-bit HOLD event."""

    CLEAR = 0
    BASIS_SET = 1
    BASIS_REF = 2
    BASIS_UPDATE = 3
    STOCHASTIC_SET = 4
    TRANSIENT = 5
    PVQ = 6
    TRUTH = 7
    CHANNEL_SET = 8
    BASIS_CORRECTED = 9


@dataclass(frozen=True)
class MafCellDecodeResult:
    """Independently decoded PCM and the materialized coefficient field."""

    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    frame_count: int
    coefficient_grid: np.ndarray


@dataclass(frozen=True)
class MafCellEncodeResult:
    """Complete MFC1 payload, independent reconstruction, and bit ledger."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


@dataclass
class _BandState:
    kind: str = "zero"
    basis_id: int = -1
    shift: int = 0
    tilt: int = 0
    gain_code: int = 0
    stochastic_seed: int = 0
    origin_frame: int = 0
    source_channel: int = -1
    channel_gain_q7: int = 0


@dataclass(frozen=True)
class _Candidate:
    mode: CellMode | None
    reconstruction: np.ndarray
    payload_bits: int
    distortion_q20: int
    fields: tuple


def _unsigned_exp_golomb_bits(value: int) -> int:
    if value < 0:
        raise ValueError("Exp-Golomb value must be nonnegative")
    return 2 * (value + 1).bit_length() - 1


def _signed_exp_golomb_bits(value: int) -> int:
    mapped = 2 * value if value >= 0 else -2 * value - 1
    return _unsigned_exp_golomb_bits(mapped)


def _round_divide_signed(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("signed division requires a positive denominator")
    magnitude = abs(numerator)
    quotient, remainder = divmod(magnitude, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return -quotient if numerator < 0 else quotient


def _distortion_q20(target: np.ndarray, candidate: np.ndarray) -> int:
    target64 = target.astype(np.int64)
    error = target64 - candidate.astype(np.int64)
    energy = int(target64 @ target64)
    squared_error = int(error @ error)
    return (squared_error << 20) // max(1, energy)


def _shift_shape(shape: np.ndarray, shift: int) -> np.ndarray:
    output = np.zeros(shape.size, dtype=np.int16)
    if shift >= 0:
        if shift < shape.size:
            output[shift:] = shape[: shape.size - shift]
    elif -shift < shape.size:
        output[:shift] = shape[-shift:]
    return output


def _filter_shape(shape: np.ndarray, tilt: int) -> np.ndarray:
    """Apply a bounded linear spectral envelope to immutable excitation."""

    if shape.size <= 1 or tilt == 0:
        return np.array(shape, dtype=np.int16, copy=True)
    output = np.empty(shape.size, dtype=np.int16)
    denominator = shape.size - 1
    for index, value in enumerate(shape):
        centered = 2 * index - denominator
        factor_q8 = 256 + _round_divide_signed(
            tilt * centered * 24,
            denominator,
        )
        output[index] = np.clip(
            _round_divide_signed(int(value) * factor_q8, 256),
            -32768,
            32767,
        )
    if not np.any(output):
        return np.array(shape, dtype=np.int16, copy=True)
    return output


def _basis_direction(
    basis: np.ndarray,
    shift: int,
    tilt: int,
) -> np.ndarray:
    return _filter_shape(_shift_shape(basis, shift), tilt)


def _materialize_band_vectorized(
    direction: np.ndarray,
    qlog: int,
) -> np.ndarray:
    """Match the scalar decoder while keeping encoder candidate search fast."""

    direction64 = direction.astype(np.int64)
    norm_squared = int(direction64 @ direction64)
    gain = _decoded_log_gain(qlog)
    if gain == 0 or norm_squared == 0:
        return np.zeros(direction.size, dtype=np.int64)
    denominator = math.isqrt(norm_squared << 30)
    numerator = direction64 * gain * (1 << 15)
    magnitude = (np.abs(numerator) + denominator // 2) // denominator
    return np.where(numerator < 0, -magnitude, magnitude).astype(np.int64)


def _counter_word(key: int) -> int:
    value = key & 0xFFFF_FFFF
    value ^= value >> 16
    value = (value * 0x7FEB_352D) & 0xFFFF_FFFF
    value ^= value >> 15
    value = (value * 0x846C_A68B) & 0xFFFF_FFFF
    value ^= value >> 16
    return value & 0xFFFF_FFFF


def _stochastic_direction(
    dimension: int,
    stream_seed: int,
    channel: int,
    band: int,
    seed: int,
    age: int,
) -> np.ndarray:
    """Materialize counter-addressable noise without recursive PRNG state."""

    output = np.empty(dimension, dtype=np.int16)
    base = (
        stream_seed
        ^ (channel * 0x9E37_79B9)
        ^ (band * 0x85EB_CA6B)
        ^ (seed * 0xC2B2_AE35)
        ^ (age * 0x27D4_EB2F)
    )
    for index in range(dimension):
        word = _counter_word(base ^ (index * 0x1656_67B1))
        magnitude = 1 + ((word >> 1) & 1)
        output[index] = -magnitude if word & 1 else magnitude
    return output


def _channel_projection_gain(target: np.ndarray, source: np.ndarray) -> int:
    source64 = source.astype(np.int64)
    target64 = target.astype(np.int64)
    denominator = int(source64 @ source64)
    if denominator == 0:
        return 0
    gain = _round_divide_signed(int(target64 @ source64) * 128, denominator)
    return max(-127, min(127, gain))


def _apply_channel_gain(source: np.ndarray, gain_q7: int) -> np.ndarray:
    output = np.empty(source.size, dtype=np.int64)
    for index, value in enumerate(source):
        output[index] = _round_divide_signed(int(value) * gain_q7, 128)
    return output


def _source_row(
    analysis: LappedAnalysis,
    channel: int,
    frame: int,
    edges: tuple[int, ...],
) -> np.ndarray:
    output = np.empty(analysis.half_window, dtype=np.int64)
    for band, (start, end) in enumerate(
        zip(edges[:-1], edges[1:], strict=True)
    ):
        output[start:end] = (
            analysis.quantized_grid[channel, frame, start:end].astype(np.int64)
            << int(analysis.scales[channel, frame, band])
        )
    return output


def _allocate_pulses(
    row: np.ndarray,
    edges: tuple[int, ...],
    maximum_pulses: int,
) -> np.ndarray:
    """Allocate at least one pulse to the strongest bounded active bands."""

    gains = np.asarray(
        [
            math.isqrt(
                int(
                    row[start:end].astype(np.int64)
                    @ row[start:end].astype(np.int64)
                )
            )
            for start, end in zip(edges[:-1], edges[1:], strict=True)
        ],
        dtype=np.int64,
    )
    counts = np.zeros(gains.size, dtype=np.uint16)
    active = np.flatnonzero(gains)
    if active.size == 0:
        return counts
    if active.size > maximum_pulses:
        active = active[
            np.argpartition(gains[active], -maximum_pulses)[-maximum_pulses:]
        ]
    counts[active] = 1
    remaining = maximum_pulses - active.size
    if remaining <= 0:
        return counts
    total = int(np.sum(gains[active], dtype=np.int64))
    additions = gains[active] * remaining // max(1, total)
    counts[active] += additions.astype(np.uint16)
    left = remaining - int(np.sum(additions, dtype=np.int64))
    if left:
        remainders = gains[active] * remaining - additions * total
        winners = active[np.argsort(remainders, kind="stable")[-left:]]
        counts[winners] += 1
    return counts


def _state_gain_predictor(state: _BandState) -> int:
    return state.gain_code if state.kind in {"basis", "stochastic"} else 0


def _event_gain_predictor(
    previous_frame: np.ndarray,
    current_frame: np.ndarray,
    band: int,
) -> int:
    temporal = int(previous_frame[band])
    if band == 0:
        return temporal
    spectral = int(current_frame[band - 1])
    return (3 * temporal + spectral + 2) // 4


def _candidate_gain_code(candidate: _Candidate) -> int | None:
    mode = candidate.mode
    if mode == CellMode.CLEAR:
        return 0
    if mode in {CellMode.BASIS_SET, CellMode.PVQ}:
        return int(candidate.fields[1])
    if mode == CellMode.BASIS_REF:
        return int(candidate.fields[3])
    if mode == CellMode.BASIS_UPDATE:
        return int(candidate.fields[2])
    if mode == CellMode.BASIS_CORRECTED:
        return int(candidate.fields[3])
    if mode == CellMode.STOCHASTIC_SET:
        return int(candidate.fields[1])
    return None


def _mode_bits(mode: CellMode) -> int:
    if mode == CellMode.PVQ:
        return 1
    if mode == CellMode.BASIS_SET:
        return 2
    return 6


def _exception_mode_bits(mode: CellMode | None) -> int:
    if mode is None:
        return 1
    if mode == CellMode.BASIS_SET:
        return 2
    if mode == CellMode.PVQ:
        raise ValueError("PVQ is not an exception to a PVQ-default map")
    return 6


def _map_payload_bits(count: int, band_count: int, index_width: int) -> int:
    sparse = _unsigned_exp_golomb_bits(count) + count * index_width
    return min(band_count, sparse)


def _write_index_map(
    writer: _BitWriter,
    indices: list[int],
    *,
    band_count: int,
    index_width: int,
) -> int:
    sparse_bits = _unsigned_exp_golomb_bits(len(indices)) + (
        len(indices) * index_width
    )
    dense = band_count < sparse_bits
    writer.write_bit(int(dense))
    if dense:
        selected = set(indices)
        for band in range(band_count):
            writer.write_bit(int(band in selected))
    else:
        writer.write_unsigned_exp_golomb(len(indices))
        for band in indices:
            writer.write_bits(band, index_width)
    return 1 + min(band_count, sparse_bits)


def _read_index_map(
    reader: _BitReader,
    *,
    band_count: int,
    index_width: int,
) -> list[int]:
    dense = bool(reader.read_bit())
    if dense:
        indices = [
            band
            for band in range(band_count)
            if reader.read_bit()
        ]
        sparse_bits = _unsigned_exp_golomb_bits(len(indices)) + (
            len(indices) * index_width
        )
        if band_count >= sparse_bits:
            raise ValueError("non-canonical MFC1 dense index map")
        return indices

    count = reader.read_unsigned_exp_golomb(band_count)
    indices = []
    previous = -1
    for _ in range(count):
        band = reader.read_bits(index_width)
        if band <= previous or band >= band_count:
            raise ValueError("non-canonical MFC1 index order")
        indices.append(band)
        previous = band
    if band_count < (
        _unsigned_exp_golomb_bits(count) + count * index_width
    ):
        raise ValueError("non-canonical MFC1 sparse index map")
    return indices


def _render_state(
    state: _BandState,
    bases: list[np.ndarray],
    coefficient_grid: np.ndarray,
    *,
    stream_seed: int,
    channel: int,
    frame: int,
    band: int,
    start: int,
    end: int,
) -> np.ndarray:
    dimension = end - start
    if state.kind == "basis":
        if not 0 <= state.basis_id < len(bases):
            raise ValueError("MFC1 state references an unavailable Basis")
        basis = bases[state.basis_id]
        if basis.size != dimension:
            raise ValueError("MFC1 Basis dimension differs from its band")
        direction = _basis_direction(basis, state.shift, state.tilt)
        return _materialize_band(
            direction,
            _gain_code_to_qlog(state.gain_code, GAIN_FRACTION_BITS),
        )
    if state.kind == "stochastic":
        direction = _stochastic_direction(
            dimension,
            stream_seed,
            channel,
            band,
            state.stochastic_seed,
            frame - state.origin_frame,
        )
        return _materialize_band(
            direction,
            _gain_code_to_qlog(state.gain_code, GAIN_FRACTION_BITS),
        )
    if state.kind == "channel":
        if not 0 <= state.source_channel < channel:
            raise ValueError("MFC1 channel state is non-causal")
        return _apply_channel_gain(
            coefficient_grid[state.source_channel, frame, start:end],
            state.channel_gain_q7,
        )
    return np.zeros(dimension, dtype=np.int64)


def _sparse_fields(
    qvalues: np.ndarray,
    scale: int,
    *,
    maximum_count: int | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    positions = np.flatnonzero(qvalues).astype(np.uint16)
    if maximum_count is not None and positions.size > maximum_count:
        magnitudes = np.abs(qvalues[positions].astype(np.int64))
        positions = np.sort(
            positions[
                np.argpartition(magnitudes, -maximum_count)[-maximum_count:]
            ]
        )
    values = qvalues[positions].astype(np.int8)
    reconstruction = np.zeros(qvalues.size, dtype=np.int64)
    reconstruction[positions] = values.astype(np.int64) << scale
    return positions, values, reconstruction


def _candidate_cost(
    candidate: _Candidate,
    *,
    rate_lambda_q20: int,
    change_overhead_bits: int,
    distortion_weight_q8: int,
) -> int:
    weighted_distortion = (
        candidate.distortion_q20 * distortion_weight_q8 + 128
    ) >> 8
    if candidate.mode is None:
        return weighted_distortion
    return weighted_distortion + rate_lambda_q20 * (
        change_overhead_bits + candidate.payload_bits
    )


def _pvq_candidate(
    mode: CellMode,
    target: np.ndarray,
    pulses: int,
    predictor: int,
) -> _Candidate | None:
    if pulses <= 0 or not np.any(target):
        return None
    shape = _pulse_shape(target, pulses)
    gain_code = _quantize_gain_code(
        _projected_gain(target, shape),
        GAIN_FRACTION_BITS,
    )
    if gain_code == 0:
        return None
    rank, actual_pulses = _rank_pvq(shape)
    if actual_pulses != pulses:
        raise RuntimeError("MFC1 PVQ search changed the pulse count")
    codebook = _pvq_codebook_size(target.size, pulses)
    width = (codebook - 1).bit_length()
    reconstruction = _materialize_band_vectorized(
        shape,
        _gain_code_to_qlog(gain_code, GAIN_FRACTION_BITS),
    )
    bits = (
        _unsigned_exp_golomb_bits(pulses)
        + _signed_exp_golomb_bits(gain_code - predictor)
        + width
    )
    return _Candidate(
        mode,
        reconstruction,
        bits,
        _distortion_q20(target, reconstruction),
        (pulses, gain_code, rank),
    )


def _basis_reuse_candidates(
    target: np.ndarray,
    state: _BandState,
    bases: list[np.ndarray],
    basis_bands: list[int],
    *,
    band: int,
    gain_predictor: int,
    basis_search_limit: int,
    direction_cache: dict[
        int,
        tuple[tuple[int, int, np.ndarray, int], ...],
    ],
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    predictor = gain_predictor
    basis_indices = [
        index
        for index, basis in enumerate(bases)
        if basis.size == target.size and basis_bands[index] == band
    ][-basis_search_limit:]
    for basis_id in basis_indices:
        basis = bases[basis_id]
        cached = direction_cache.get(basis_id)
        if cached is None:
            generated = []
            for shift in range(-2, 3):
                for tilt in range(-3, 4):
                    direction = _basis_direction(basis, shift, tilt)
                    norm_squared = int(
                        direction.astype(np.int64)
                        @ direction.astype(np.int64)
                    )
                    if norm_squared:
                        direction.flags.writeable = False
                        generated.append(
                            (shift, tilt, direction, norm_squared)
                        )
            cached = tuple(generated)
            direction_cache[basis_id] = cached
        target64 = target.astype(np.int64)
        scored = []
        for shift, tilt, direction, norm_squared in cached:
            correlation = int(target64 @ direction.astype(np.int64))
            if correlation > 0:
                scored.append(
                    (
                        -(correlation * correlation // norm_squared),
                        abs(shift) + abs(tilt),
                        shift,
                        tilt,
                        direction,
                    )
                )
        if not scored:
            continue
        _score, _movement, shift, tilt, direction = min(scored)
        gain_code = _quantize_gain_code(
            _projected_gain(target, direction),
            GAIN_FRACTION_BITS,
        )
        if gain_code == 0:
            continue
        reconstruction = _materialize_band_vectorized(
            direction,
            _gain_code_to_qlog(gain_code, GAIN_FRACTION_BITS),
        )
        residual = gain_code - predictor
        if state.kind == "basis" and basis_id == state.basis_id:
            mode = CellMode.BASIS_UPDATE
            bits = 4 + 4 + _signed_exp_golomb_bits(residual)
            fields = (shift, tilt, gain_code)
        else:
            mode = CellMode.BASIS_REF
            bits = 8 + 4 + 4 + _signed_exp_golomb_bits(residual)
            fields = (basis_id, shift, tilt, gain_code)
        candidates.append(
            _Candidate(
                mode,
                reconstruction,
                bits,
                _distortion_q20(target, reconstruction),
                fields,
            )
        )
        error = target.astype(np.int64) - reconstruction.astype(np.int64)
        nonzero = np.flatnonzero(error)
        if nonzero.size:
            correction_count = min(
                MAX_BASIS_CORRECTIONS,
                int(nonzero.size),
            )
            strongest = nonzero[
                np.argpartition(
                    np.abs(error[nonzero]),
                    -correction_count,
                )[-correction_count:]
            ]
            positions = np.sort(strongest).astype(np.uint16)
            corrections = error[positions].astype(np.int64)
            if np.all(np.abs(corrections) <= MAX_CORRECTION_ABSOLUTE):
                corrected = reconstruction.astype(np.int64, copy=True)
                corrected[positions] += corrections
                position_width = max(
                    1,
                    (target.size - 1).bit_length(),
                )
                correction_bits = (
                    8
                    + 4
                    + 4
                    + _signed_exp_golomb_bits(residual)
                    + _unsigned_exp_golomb_bits(correction_count)
                    + correction_count * position_width
                    + sum(
                        _signed_exp_golomb_bits(int(value))
                        for value in corrections
                    )
                )
                candidates.append(
                    _Candidate(
                        CellMode.BASIS_CORRECTED,
                        corrected,
                        correction_bits,
                        _distortion_q20(target, corrected),
                        (
                            basis_id,
                            shift,
                            tilt,
                            gain_code,
                            positions,
                            corrections,
                        ),
                    )
                )
    return candidates


def _learn_basis_dictionary(
    analysis: LappedAnalysis,
    edges: tuple[int, ...],
    *,
    bases_per_band: int,
    pulses_per_basis: int,
    iterations: int,
) -> tuple[list[np.ndarray], list[int]]:
    """Learn a bounded deterministic spherical Basis bank before events."""

    if bases_per_band == 0:
        return [], []
    learned: list[np.ndarray] = []
    learned_bands: list[int] = []
    for band, (start, end) in enumerate(
        zip(edges[:-1], edges[1:], strict=True)
    ):
        vectors = []
        for channel in range(analysis.samples.shape[1]):
            for frame in range(analysis.frame_count):
                values = analysis.quantized_grid[
                    channel,
                    frame,
                    start:end,
                ].astype(np.float64)
                norm = float(np.linalg.norm(values))
                if norm > 0.0:
                    vectors.append(values / norm)
        if not vectors:
            continue
        matrix = np.asarray(vectors, dtype=np.float64)
        if matrix.shape[0] > 2048:
            indices = np.linspace(
                0,
                matrix.shape[0] - 1,
                2048,
                dtype=np.int64,
            )
            matrix = matrix[indices]
        cluster_count = min(
            bases_per_band,
            matrix.shape[0],
            MAX_BASIS_COUNT - len(learned),
        )
        if cluster_count <= 0:
            break

        # Farthest-first initialization retains opposite MDCT phase
        # directions instead of collapsing them into one weak centroid.
        centroid_indices = [0]
        best_similarity = matrix @ matrix[0]
        for _ in range(1, cluster_count):
            next_index = int(np.argmin(best_similarity))
            centroid_indices.append(next_index)
            best_similarity = np.maximum(
                best_similarity,
                matrix @ matrix[next_index],
            )
        centroids = matrix[np.asarray(centroid_indices)].copy()
        for _ in range(iterations):
            assignment = np.argmax(matrix @ centroids.T, axis=1)
            updated = centroids.copy()
            for cluster in range(cluster_count):
                members = matrix[assignment == cluster]
                if members.size == 0:
                    continue
                centroid = np.sum(members, axis=0)
                norm = float(np.linalg.norm(centroid))
                if norm > 0.0:
                    updated[cluster] = centroid / norm
            centroids = updated

        for centroid in centroids:
            fixed_target = np.rint(centroid * (1 << 20)).astype(np.int64)
            shape = _pulse_shape(fixed_target, pulses_per_basis)
            shape.flags.writeable = False
            learned.append(shape)
            learned_bands.append(band)
    return learned, learned_bands


def _pack_basis_dictionary(
    bases: list[np.ndarray],
    basis_bands: list[int],
    *,
    band_count: int,
) -> bytes:
    writer = _BitWriter()
    band_width = max(1, (band_count - 1).bit_length())
    for basis, band in zip(bases, basis_bands, strict=True):
        rank, pulses = _rank_pvq(basis)
        writer.write_bits(band, band_width)
        writer.write_unsigned_exp_golomb(pulses)
        codebook = _pvq_codebook_size(basis.size, pulses)
        writer.write_bits(rank, (codebook - 1).bit_length())
    bit_count = writer.bit_count
    return (
        DICTIONARY_HEADER.pack(
            DICTIONARY_MAGIC,
            DICTIONARY_VERSION,
            len(bases),
            bit_count,
        )
        + writer.finish()
    )


def _unpack_basis_dictionary(
    payload: bytes,
    *,
    edges: tuple[int, ...],
) -> tuple[list[np.ndarray], list[int]]:
    if len(payload) < DICTIONARY_HEADER.size:
        raise ValueError("truncated MFC1 Basis dictionary")
    magic, version, basis_count, bit_count = DICTIONARY_HEADER.unpack_from(
        payload
    )
    if (
        magic != DICTIONARY_MAGIC
        or version != DICTIONARY_VERSION
        or basis_count > MAX_BASIS_COUNT
    ):
        raise ValueError("MFC1 Basis dictionary exceeds the profile")
    reader = _BitReader(payload[DICTIONARY_HEADER.size :], bit_count)
    band_count = len(edges) - 1
    band_width = max(1, (band_count - 1).bit_length())
    bases = []
    basis_bands = []
    for _ in range(basis_count):
        band = reader.read_bits(band_width)
        if band >= band_count:
            raise ValueError("MFC1 Basis dictionary band exceeds profile")
        dimension = edges[band + 1] - edges[band]
        pulses = reader.read_unsigned_exp_golomb(MAX_PULSES_PER_BAND)
        if pulses == 0:
            raise ValueError("MFC1 Basis dictionary has zero pulses")
        codebook = _pvq_codebook_size(dimension, pulses)
        rank = reader.read_bits((codebook - 1).bit_length())
        if rank >= codebook:
            raise ValueError("MFC1 Basis dictionary rank exceeds codebook")
        bases.append(_unrank_pvq(dimension, pulses, rank))
        basis_bands.append(band)
    reader.require_canonical_end()
    return bases, basis_bands


def _stochastic_candidate(
    target: np.ndarray,
    state: _BandState,
    *,
    stream_seed: int,
    channel: int,
    frame: int,
    band: int,
    gain_predictor: int,
) -> _Candidate | None:
    predictor = gain_predictor
    best_seed = -1
    best_direction: np.ndarray | None = None
    best_score = -1
    target64 = target.astype(np.int64)
    for seed in range(MAX_STOCHASTIC_SEEDS):
        direction = _stochastic_direction(
            target.size,
            stream_seed,
            channel,
            band,
            seed,
            0,
        )
        direction64 = direction.astype(np.int64)
        correlation = int(target64 @ direction64)
        norm_squared = int(direction64 @ direction64)
        score = (
            correlation * correlation // norm_squared
            if correlation > 0 and norm_squared
            else -1
        )
        if score > best_score:
            best_score = score
            best_seed = seed
            best_direction = direction
    if best_direction is None:
        return None
    gain_code = _quantize_gain_code(
        _projected_gain(target, best_direction),
        GAIN_FRACTION_BITS,
    )
    if gain_code == 0:
        return None
    reconstruction = _materialize_band_vectorized(
        best_direction,
        _gain_code_to_qlog(gain_code, GAIN_FRACTION_BITS),
    )
    return _Candidate(
        CellMode.STOCHASTIC_SET,
        reconstruction,
        5 + _signed_exp_golomb_bits(gain_code - predictor),
        _distortion_q20(target, reconstruction),
        (best_seed, gain_code),
    )


def _channel_candidate(
    target: np.ndarray,
    coefficient_grid: np.ndarray,
    *,
    channel: int,
    frame: int,
    start: int,
    end: int,
) -> _Candidate | None:
    best: _Candidate | None = None
    for source_channel in range(channel):
        source = coefficient_grid[source_channel, frame, start:end]
        gain_q7 = _channel_projection_gain(target, source)
        if gain_q7 == 0:
            continue
        reconstruction = _apply_channel_gain(source, gain_q7)
        candidate = _Candidate(
            CellMode.CHANNEL_SET,
            reconstruction,
            3 + 8,
            _distortion_q20(target, reconstruction),
            (source_channel, gain_q7),
        )
        if best is None or (
            candidate.distortion_q20,
            abs(gain_q7),
            source_channel,
        ) < (
            best.distortion_q20,
            abs(best.fields[1]),
            best.fields[0],
        ):
            best = candidate
    return best


def _write_signed_byte(writer: _BitWriter, value: int) -> None:
    if not -128 <= value <= 127:
        raise ValueError("signed byte exceeds MFC1 range")
    writer.write_bits(value & 0xFF, 8)


def _read_signed_byte(reader: _BitReader) -> int:
    value = reader.read_bits(8)
    return value - 256 if value & 0x80 else value


def _write_sparse(
    writer: _BitWriter,
    scale: int,
    positions: np.ndarray,
    values: np.ndarray,
    dimension: int,
) -> None:
    writer.write_bits(scale, 5)
    writer.write_unsigned_exp_golomb(int(positions.size))
    position_width = max(1, (dimension - 1).bit_length())
    for position, value in zip(positions, values, strict=True):
        writer.write_bits(int(position), position_width)
        _write_signed_byte(writer, int(value))


def _read_sparse(
    reader: _BitReader,
    dimension: int,
    *,
    maximum_count: int,
) -> np.ndarray:
    scale = reader.read_bits(5)
    count = reader.read_unsigned_exp_golomb(maximum_count)
    position_width = max(1, (dimension - 1).bit_length())
    output = np.zeros(dimension, dtype=np.int64)
    previous = -1
    for _ in range(count):
        position = reader.read_bits(position_width)
        value = _read_signed_byte(reader)
        if position <= previous or position >= dimension or value == 0:
            raise ValueError("non-canonical MFC1 sparse coefficients")
        output[position] = value << scale
        previous = position
    return output


def _write_command(
    writer: _BitWriter,
    candidate: _Candidate,
    state: _BandState,
    bases: list[np.ndarray],
    *,
    dimension: int,
    gain_predictor: int,
    write_mode: bool = True,
) -> None:
    if candidate.mode is None:
        raise ValueError("HOLD has no explicit MFC1 command")
    mode = candidate.mode
    if write_mode:
        if mode == CellMode.PVQ:
            writer.write_bit(0)
        elif mode == CellMode.BASIS_SET:
            writer.write_bits(0b10, 2)
        else:
            writer.write_bits(0b11, 2)
            writer.write_bits(int(mode), 4)
    if mode == CellMode.CLEAR:
        return
    if mode in {CellMode.BASIS_SET, CellMode.PVQ}:
        pulses, gain_code, rank = candidate.fields
        writer.write_unsigned_exp_golomb(pulses)
        writer.write_signed_exp_golomb(
            gain_code - gain_predictor
        )
        width = (_pvq_codebook_size(dimension, pulses) - 1).bit_length()
        writer.write_bits(rank, width)
        return
    if mode == CellMode.BASIS_REF:
        basis_id, shift, tilt, gain_code = candidate.fields
        writer.write_bits(basis_id, 8)
        writer.write_bits(shift + MAX_SHIFT, 4)
        writer.write_bits(tilt + MAX_TILT, 4)
        writer.write_signed_exp_golomb(
            gain_code - gain_predictor
        )
        return
    if mode == CellMode.BASIS_UPDATE:
        shift, tilt, gain_code = candidate.fields
        writer.write_bits(shift + MAX_SHIFT, 4)
        writer.write_bits(tilt + MAX_TILT, 4)
        writer.write_signed_exp_golomb(
            gain_code - gain_predictor
        )
        return
    if mode == CellMode.BASIS_CORRECTED:
        (
            basis_id,
            shift,
            tilt,
            gain_code,
            positions,
            corrections,
        ) = candidate.fields
        writer.write_bits(basis_id, 8)
        writer.write_bits(shift + MAX_SHIFT, 4)
        writer.write_bits(tilt + MAX_TILT, 4)
        writer.write_signed_exp_golomb(
            gain_code - gain_predictor
        )
        writer.write_unsigned_exp_golomb(int(positions.size))
        position_width = max(1, (dimension - 1).bit_length())
        for position, correction in zip(
            positions,
            corrections,
            strict=True,
        ):
            writer.write_bits(int(position), position_width)
            writer.write_signed_exp_golomb(int(correction))
        return
    if mode == CellMode.STOCHASTIC_SET:
        seed, gain_code = candidate.fields
        writer.write_bits(seed, 5)
        writer.write_signed_exp_golomb(
            gain_code - gain_predictor
        )
        return
    if mode in {CellMode.TRANSIENT, CellMode.TRUTH}:
        scale, positions, values = candidate.fields
        _write_sparse(writer, scale, positions, values, dimension)
        return
    if mode == CellMode.CHANNEL_SET:
        source_channel, gain_q7 = candidate.fields
        writer.write_bits(source_channel, 3)
        _write_signed_byte(writer, gain_q7)
        return
    raise ValueError("unsupported MFC1 mode")


def _read_mode(reader: _BitReader) -> CellMode:
    if reader.read_bit() == 0:
        return CellMode.PVQ
    if reader.read_bit() == 0:
        return CellMode.BASIS_SET
    try:
        return CellMode(reader.read_bits(4))
    except ValueError as error:
        raise ValueError("unsupported MFC1 cell mode") from error


def _write_exception_mode(
    writer: _BitWriter,
    mode: CellMode | None,
) -> None:
    if mode is None:
        writer.write_bit(0)
    elif mode == CellMode.BASIS_SET:
        writer.write_bits(0b10, 2)
    elif mode == CellMode.PVQ:
        raise ValueError("PVQ cannot be explicit in a PVQ-default map")
    else:
        writer.write_bits(0b11, 2)
        writer.write_bits(int(mode), 4)


def _read_exception_mode(reader: _BitReader) -> CellMode | None:
    if reader.read_bit() == 0:
        return None
    if reader.read_bit() == 0:
        return CellMode.BASIS_SET
    try:
        mode = CellMode(reader.read_bits(4))
    except ValueError as error:
        raise ValueError("unsupported MFC1 exception mode") from error
    if mode == CellMode.PVQ:
        raise ValueError("non-canonical PVQ exception")
    return mode


def _apply_candidate_state(
    candidate: _Candidate,
    state: _BandState,
    bases: list[np.ndarray],
    *,
    frame: int,
    dimension: int,
) -> None:
    mode = candidate.mode
    if mode == CellMode.CLEAR:
        state.__dict__.update(_BandState().__dict__)
    elif mode == CellMode.BASIS_SET:
        pulses, gain_code, rank = candidate.fields
        shape = _unrank_pvq(dimension, pulses, rank)
        if len(bases) >= MAX_BASIS_COUNT:
            raise ValueError("MFC1 Basis bank exceeds the profile")
        bases.append(shape)
        state.kind = "basis"
        state.basis_id = len(bases) - 1
        state.shift = 0
        state.tilt = 0
        state.gain_code = gain_code
    elif mode in {CellMode.BASIS_REF, CellMode.BASIS_CORRECTED}:
        basis_id, shift, tilt, gain_code = candidate.fields[:4]
        state.kind = "basis"
        state.basis_id = basis_id
        state.shift = shift
        state.tilt = tilt
        state.gain_code = gain_code
    elif mode == CellMode.BASIS_UPDATE:
        shift, tilt, gain_code = candidate.fields
        state.shift = shift
        state.tilt = tilt
        state.gain_code = gain_code
    elif mode == CellMode.STOCHASTIC_SET:
        seed, gain_code = candidate.fields
        state.kind = "stochastic"
        state.stochastic_seed = seed
        state.gain_code = gain_code
        state.origin_frame = frame
    elif mode == CellMode.CHANNEL_SET:
        source_channel, gain_q7 = candidate.fields
        state.kind = "channel"
        state.source_channel = source_channel
        state.channel_gain_q7 = gain_q7


def encode_maf_cell_analysis(
    analysis: LappedAnalysis,
    *,
    maximum_pulses_per_frame: int,
    rate_lambda_q20: int,
    stream_seed: int = 0x5245_534F,
    basis_search_limit: int = 16,
    dictionary_bases_per_band: int = 0,
    dictionary_pulses_per_basis: int = 24,
    dictionary_iterations: int = 4,
    transient_onset_ratio_q8: int = 640,
    distortion_weights_q8: np.ndarray | None = None,
    pvq_guard_q12: int | None = None,
) -> MafCellEncodeResult:
    """Compile one actual MFC1 stream and verify independent decode.

    `rate_lambda_q20` trades normalized band error against complete logical
    event bits. File-level quality gates still decide admission.
    """

    if not isinstance(analysis, LappedAnalysis) or not analysis.fixed_transform:
        raise TypeError("MFC1 requires one fixed-integer LappedAnalysis")
    if not 1 <= maximum_pulses_per_frame <= analysis.half_window:
        raise ValueError("MFC1 pulse budget exceeds the transform window")
    if not 0 <= rate_lambda_q20 <= (1 << 24):
        raise ValueError("MFC1 rate lambda exceeds the profile")
    if not 1 <= basis_search_limit <= MAX_BASIS_COUNT:
        raise ValueError("MFC1 Basis search limit exceeds the profile")
    if not 0 <= dictionary_bases_per_band <= 16:
        raise ValueError("MFC1 dictionary size exceeds the profile")
    if not 1 <= dictionary_pulses_per_basis <= MAX_PULSES_PER_BAND:
        raise ValueError("MFC1 dictionary pulse count exceeds the profile")
    if not 1 <= dictionary_iterations <= 16:
        raise ValueError("MFC1 dictionary iteration count exceeds profile")
    if not 0 <= transient_onset_ratio_q8 <= (1 << 16):
        raise ValueError("MFC1 transient onset ratio exceeds the profile")
    if pvq_guard_q12 is not None and not 4096 <= pvq_guard_q12 <= 8192:
        raise ValueError("MFC1 PVQ guard exceeds the profile")
    if distortion_weights_q8 is None:
        weights = np.full(
            (
                analysis.samples.shape[1],
                analysis.frame_count,
                analysis.band_count,
            ),
            256,
            dtype=np.uint16,
        )
    else:
        weights = np.asarray(distortion_weights_q8)
        if (
            weights.dtype != np.uint16
            or weights.shape
            != (
                analysis.samples.shape[1],
                analysis.frame_count,
                analysis.band_count,
            )
            or np.any(weights == 0)
            or np.any(weights > 4096)
        ):
            raise ValueError("MFC1 distortion weights exceed the profile")

    channels = analysis.samples.shape[1]
    edges = _band_edges(analysis.half_window, analysis.band_count)
    band_index_width = max(1, (analysis.band_count - 1).bit_length())
    coefficient_grid = np.zeros(
        (channels, analysis.frame_count, analysis.half_window),
        dtype=np.int64,
    )
    states = [
        [_BandState() for _ in range(analysis.band_count)]
        for _ in range(channels)
    ]
    bases, basis_bands = _learn_basis_dictionary(
        analysis,
        edges,
        bases_per_band=dictionary_bases_per_band,
        pulses_per_basis=dictionary_pulses_per_basis,
        iterations=dictionary_iterations,
    )
    dictionary_basis_count = len(bases)
    basis_direction_cache: dict[
        int,
        tuple[tuple[int, int, np.ndarray, int], ...],
    ] = {}
    writer = _BitWriter()
    mode_counts = {mode.name: 0 for mode in CellMode}
    hold_cells = 0
    changed_cells = 0
    default_pvq_frames = 0
    regular_event_frames = 0
    map_bits = 0
    mode_bits = 0
    command_payload_bits = 0
    source_rows = [
        [
            _source_row(analysis, channel, frame, edges)
            for frame in range(analysis.frame_count)
        ]
        for channel in range(channels)
    ]
    previous_energy = np.zeros((channels, analysis.band_count), dtype=np.int64)
    previous_gain_code = np.zeros(
        (channels, analysis.band_count),
        dtype=np.int16,
    )

    for frame in range(analysis.frame_count):
        for channel in range(channels):
            current_gain_code = previous_gain_code[channel].copy()
            row = source_rows[channel][frame]
            counts = _allocate_pulses(
                row,
                edges,
                maximum_pulses_per_frame,
            )
            decisions: list[tuple[int, _Candidate, int]] = []
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                target = row[start:end]
                state = states[channel][band]
                gain_predictor = _event_gain_predictor(
                    previous_gain_code[channel],
                    current_gain_code,
                    band,
                )
                hold = _render_state(
                    state,
                    bases,
                    coefficient_grid,
                    stream_seed=stream_seed,
                    channel=channel,
                    frame=frame,
                    band=band,
                    start=start,
                    end=end,
                )
                candidates = [
                    _Candidate(
                        None,
                        hold,
                        0,
                        _distortion_q20(target, hold),
                        (),
                    )
                ]
                if state.kind != "zero":
                    zero = np.zeros(end - start, dtype=np.int64)
                    candidates.append(
                        _Candidate(
                            CellMode.CLEAR,
                            zero,
                            0,
                            _distortion_q20(target, zero),
                            (),
                        )
                    )

                pulse_count = int(counts[band])
                pvq = _pvq_candidate(
                    CellMode.PVQ,
                    target,
                    min(MAX_PULSES_PER_BAND, pulse_count),
                    gain_predictor,
                )
                if pvq is not None:
                    candidates.append(pvq)
                    pending_basis_sets = sum(
                        candidate.mode == CellMode.BASIS_SET
                        for _selected_band, candidate, _predictor in decisions
                    )
                    if len(bases) + pending_basis_sets < MAX_BASIS_COUNT:
                        candidates.append(
                            _Candidate(
                                CellMode.BASIS_SET,
                                pvq.reconstruction,
                                pvq.payload_bits,
                                pvq.distortion_q20,
                                pvq.fields,
                            )
                        )

                candidates.extend(
                    _basis_reuse_candidates(
                        target,
                        state,
                        bases,
                        basis_bands,
                        band=band,
                        gain_predictor=gain_predictor,
                        basis_search_limit=basis_search_limit,
                        direction_cache=basis_direction_cache,
                    )
                )
                stochastic = _stochastic_candidate(
                    target,
                    state,
                    stream_seed=stream_seed,
                    channel=channel,
                    frame=frame,
                    band=band,
                    gain_predictor=gain_predictor,
                )
                if stochastic is not None:
                    candidates.append(stochastic)
                channel_candidate = _channel_candidate(
                    target,
                    coefficient_grid,
                    channel=channel,
                    frame=frame,
                    start=start,
                    end=end,
                )
                if channel_candidate is not None:
                    candidates.append(channel_candidate)

                qvalues = analysis.quantized_grid[
                    channel,
                    frame,
                    start:end,
                ]
                scale = int(analysis.scales[channel, frame, band])
                positions, values, truth_reconstruction = _sparse_fields(
                    qvalues,
                    scale,
                    maximum_count=None,
                )
                position_width = max(1, (end - start - 1).bit_length())
                truth_bits = (
                    5
                    + _unsigned_exp_golomb_bits(int(positions.size))
                    + int(positions.size) * (position_width + 8)
                )
                candidates.append(
                    _Candidate(
                        CellMode.TRUTH,
                        truth_reconstruction,
                        truth_bits,
                        _distortion_q20(target, truth_reconstruction),
                        (scale, positions, values),
                    )
                )

                energy = int(target.astype(np.int64) @ target.astype(np.int64))
                onset = (
                    energy * 256
                    >= int(previous_energy[channel, band])
                    * transient_onset_ratio_q8
                    and energy > 0
                )
                if onset:
                    (
                        transient_positions,
                        transient_values,
                        transient_reconstruction,
                    ) = _sparse_fields(
                        qvalues,
                        scale,
                        maximum_count=MAX_TRANSIENT_COEFFICIENTS,
                    )
                    transient_bits = (
                        5
                        + _unsigned_exp_golomb_bits(
                            int(transient_positions.size)
                        )
                        + int(transient_positions.size)
                        * (position_width + 8)
                    )
                    candidates.append(
                        _Candidate(
                            CellMode.TRANSIENT,
                            transient_reconstruction,
                            transient_bits,
                            _distortion_q20(
                                target,
                                transient_reconstruction,
                            ),
                            (
                                scale,
                                transient_positions,
                                transient_values,
                            ),
                        )
                    )
                previous_energy[channel, band] = energy

                change_overhead = band_index_width + 4
                distortion_weight_q8 = int(weights[channel, frame, band])
                if pvq_guard_q12 is not None and pvq is not None:
                    maximum_distortion = (
                        pvq.distortion_q20 * pvq_guard_q12 + 2048
                    ) >> 12
                    eligible = [
                        item
                        for item in candidates
                        if item.distortion_q20 <= maximum_distortion
                    ]
                    winner = min(
                        eligible,
                        key=lambda item: (
                            0
                            if item.mode is None
                            else change_overhead + item.payload_bits,
                            item.distortion_q20,
                            item.payload_bits,
                            -1 if item.mode is None else int(item.mode),
                        ),
                    )
                else:
                    winner = min(
                        candidates,
                        key=lambda item: (
                            _candidate_cost(
                                item,
                                rate_lambda_q20=rate_lambda_q20,
                                change_overhead_bits=change_overhead,
                                distortion_weight_q8=distortion_weight_q8,
                            ),
                            item.distortion_q20,
                            item.payload_bits,
                            -1 if item.mode is None else int(item.mode),
                        ),
                    )
                coefficient_grid[channel, frame, start:end] = (
                    winner.reconstruction
                )
                if winner.mode is None:
                    hold_cells += 1
                else:
                    selected_gain = _candidate_gain_code(winner)
                    if selected_gain is not None:
                        current_gain_code[band] = selected_gain
                decisions.append((band, winner, gain_predictor))

            changed = [
                decision
                for decision in decisions
                if decision[1].mode is not None
            ]
            exceptions = [
                decision
                for decision in decisions
                if decision[1].mode != CellMode.PVQ
            ]
            regular_framing_bits = (
                2
                + _map_payload_bits(
                    len(changed),
                    analysis.band_count,
                    band_index_width,
                )
                + sum(_mode_bits(candidate.mode) for _, candidate, _ in changed)
            )
            default_framing_bits = (
                2
                + _map_payload_bits(
                    len(exceptions),
                    analysis.band_count,
                    band_index_width,
                )
                + sum(
                    _exception_mode_bits(candidate.mode)
                    for _, candidate, _ in exceptions
                )
            )
            use_default_pvq = default_framing_bits < regular_framing_bits
            writer.write_bit(int(not use_default_pvq))
            if use_default_pvq:
                default_pvq_frames += 1
                map_bits += 1 + _write_index_map(
                    writer,
                    [band for band, _candidate, _predictor in exceptions],
                    band_count=analysis.band_count,
                    index_width=band_index_width,
                )
                for band, candidate, gain_predictor in decisions:
                    if candidate.mode != CellMode.PVQ:
                        _write_exception_mode(writer, candidate.mode)
                        mode_bits += _exception_mode_bits(candidate.mode)
                        if candidate.mode is None:
                            continue
                    state = states[channel][band]
                    start, end = edges[band], edges[band + 1]
                    _write_command(
                        writer,
                        candidate,
                        state,
                        bases,
                        dimension=end - start,
                        gain_predictor=gain_predictor,
                        write_mode=False,
                    )
                    command_payload_bits += candidate.payload_bits
            else:
                regular_event_frames += 1
                map_bits += 1 + _write_index_map(
                    writer,
                    [band for band, _candidate, _predictor in changed],
                    band_count=analysis.band_count,
                    index_width=band_index_width,
                )
                for band, candidate, gain_predictor in changed:
                    mode_bits += _mode_bits(candidate.mode)
                    state = states[channel][band]
                    start, end = edges[band], edges[band + 1]
                    _write_command(
                        writer,
                        candidate,
                        state,
                        bases,
                        dimension=end - start,
                        gain_predictor=gain_predictor,
                    )
                    command_payload_bits += candidate.payload_bits

            for band, candidate, _gain_predictor in changed:
                state = states[channel][band]
                start, end = edges[band], edges[band + 1]
                _apply_candidate_state(
                    candidate,
                    state,
                    bases,
                    frame=frame,
                    dimension=end - start,
                )
                if candidate.mode == CellMode.BASIS_SET:
                    basis_bands.append(band)
                mode_counts[candidate.mode.name] += 1
                changed_cells += 1
            previous_gain_code[channel] = current_gain_code

    logical_bits = writer.bit_count
    event_payload = writer.finish()
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            GAIN_FRACTION_BITS,
            channels,
            analysis.sample_rate,
            analysis.samples.shape[0],
            analysis.half_window,
            analysis.band_count,
            analysis.frame_count,
            logical_bits,
            stream_seed & 0xFFFF_FFFF,
        )
        + event_payload
    )
    sections = [
        RSC1Section(
            "CONF",
            pack_conf(
                StreamConfig(
                    analysis.samples.shape[0],
                    1,
                    channels,
                )
            ),
        )
    ]
    dictionary_payload = b""
    if dictionary_basis_count:
        dictionary_payload = _pack_basis_dictionary(
            bases[:dictionary_basis_count],
            basis_bands[:dictionary_basis_count],
            band_count=analysis.band_count,
        )
        sections.append(RSC1Section("MBAS", dictionary_payload))
    sections.append(RSC1Section("MFC1", body))
    payload = pack_rsc1(
        sections,
        profile=0,
        level=5,
        timebase_hz=analysis.sample_rate,
    )
    decoded = decode_maf_cell_stream(payload)
    if not np.array_equal(decoded.coefficient_grid, coefficient_grid):
        raise RuntimeError("MFC1 encoder and independent decoder disagree")
    quality = _quality_report(
        analysis.samples.reshape(-1),
        decoded.samples.reshape(-1),
    )
    report = {
        **quality,
        "status": "R-120 prospective unified MAF cell; non-normative",
        "format_profile": "prospective-MFC1-RSC1-level-5",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_event_bits": logical_bits,
        "map_bits": map_bits,
        "mode_bits": mode_bits,
        "command_payload_bits": command_payload_bits,
        "unclassified_event_bits": (
            logical_bits - map_bits - mode_bits - command_payload_bits
        ),
        "padding_bits": len(event_payload) * 8 - logical_bits,
        "sample_rate": analysis.sample_rate,
        "sample_count": int(analysis.samples.shape[0]),
        "channel_count": channels,
        "transform_frame_count": analysis.frame_count,
        "half_window": analysis.half_window,
        "band_count": analysis.band_count,
        "maximum_pulses_per_frame": maximum_pulses_per_frame,
        "rate_lambda_q20": rate_lambda_q20,
        "pvq_guard_q12": pvq_guard_q12,
        "basis_search_limit": basis_search_limit,
        "basis_count": len(bases),
        "dictionary_basis_count": dictionary_basis_count,
        "dictionary_section_bytes": len(dictionary_payload),
        "online_basis_count": len(bases) - dictionary_basis_count,
        "hold_cells": hold_cells,
        "changed_cells": changed_cells,
        "default_pvq_frames": default_pvq_frames,
        "regular_event_frames": regular_event_frames,
        "hold_fraction": hold_cells
        / max(1, hold_cells + changed_cells),
        "mode_counts": mode_counts,
        "distortion_weight_q8_min": int(np.min(weights)),
        "distortion_weight_q8_max": int(np.max(weights)),
        "analysis_backend": analysis.analysis_backend,
        "reconstruction_backend": "independent Python integer MFC1 decoder",
    }
    return MafCellEncodeResult(payload, decoded.samples, report)


def decode_maf_cell_stream(payload: bytes) -> MafCellDecodeResult:
    """Validate, bound, and independently decode one MFC1 stream."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 5):
        raise ValueError("unsupported MFC1 research profile")
    config_sections = []
    dictionary_sections = []
    cell_sections = []
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code == b"CONF":
            config_sections.append(section)
        elif type_code == b"MBAS":
            dictionary_sections.append(section)
        elif type_code == b"MFC1":
            cell_sections.append(section)
        elif section.flags & SECTION_CRITICAL:
            raise ValueError("unknown critical MFC1 section")
    if (
        len(config_sections) != 1
        or len(dictionary_sections) > 1
        or len(cell_sections) != 1
    ):
        raise ValueError("non-canonical MFC1 sections")
    config = unpack_conf(config_sections[0].payload)
    body = cell_sections[0].payload
    if len(body) < HEADER.size or len(body) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid MFC1 section size")
    (
        magic,
        version,
        gain_fraction_bits,
        channels,
        sample_rate,
        sample_count,
        half_window,
        band_count,
        frame_count,
        logical_bits,
        stream_seed,
    ) = HEADER.unpack_from(body)
    if (
        magic != MAGIC
        or version != VERSION
        or gain_fraction_bits != GAIN_FRACTION_BITS
        or not 1 <= channels <= MAX_CHANNELS
        or not 32 <= half_window <= MAX_HALF_WINDOW
        or half_window & (half_window - 1)
        or not 1 <= band_count <= min(MAX_BANDS, half_window)
        or frame_count != sample_count // half_window + 1
        or sample_rate != info.timebase_hz
        or sample_count != config.sample_count
        or channels != config.output_channels
        or config.innovation_step != 1
    ):
        raise ValueError("MFC1 header exceeds the research profile")

    edges = _band_edges(half_window, band_count)
    band_index_width = max(1, (band_count - 1).bit_length())
    reader = _BitReader(body[HEADER.size:], logical_bits)
    coefficient_grid = np.zeros(
        (channels, frame_count, half_window),
        dtype=np.int64,
    )
    states = [
        [_BandState() for _ in range(band_count)]
        for _ in range(channels)
    ]
    if dictionary_sections:
        bases, basis_bands = _unpack_basis_dictionary(
            dictionary_sections[0].payload,
            edges=edges,
        )
    else:
        bases, basis_bands = [], []
    maximum_gain_code = _maximum_gain_code(GAIN_FRACTION_BITS)
    previous_gain_code = np.zeros(
        (channels, band_count),
        dtype=np.int16,
    )

    for frame in range(frame_count):
        for channel in range(channels):
            current_gain_code = previous_gain_code[channel].copy()
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                coefficient_grid[channel, frame, start:end] = _render_state(
                    states[channel][band],
                    bases,
                    coefficient_grid,
                    stream_seed=stream_seed,
                    channel=channel,
                    frame=frame,
                    band=band,
                    start=start,
                    end=end,
                )

            default_pvq = reader.read_bit() == 0
            mapped_bands = _read_index_map(
                reader,
                band_count=band_count,
                index_width=band_index_width,
            )
            mapped = set(mapped_bands)
            command_bands = (
                range(band_count)
                if default_pvq
                else mapped_bands
            )
            for band in command_bands:
                start, end = edges[band], edges[band + 1]
                dimension = end - start
                state = states[channel][band]
                gain_predictor = _event_gain_predictor(
                    previous_gain_code[channel],
                    current_gain_code,
                    band,
                )
                if default_pvq:
                    mode = (
                        _read_exception_mode(reader)
                        if band in mapped
                        else CellMode.PVQ
                    )
                    if mode is None:
                        continue
                else:
                    mode = _read_mode(reader)

                if mode == CellMode.CLEAR:
                    reconstruction = np.zeros(dimension, dtype=np.int64)
                    candidate = _Candidate(mode, reconstruction, 0, 0, ())
                elif mode in {CellMode.BASIS_SET, CellMode.PVQ}:
                    pulses = reader.read_unsigned_exp_golomb(
                        min(MAX_PULSES_PER_BAND, half_window)
                    )
                    if pulses == 0:
                        raise ValueError("MFC1 PVQ mode has zero pulses")
                    residual = reader.read_signed_exp_golomb(
                        maximum_gain_code
                    )
                    gain_code = gain_predictor + residual
                    if not 1 <= gain_code <= maximum_gain_code:
                        raise ValueError("MFC1 gain exceeds the profile")
                    codebook = _pvq_codebook_size(dimension, pulses)
                    rank = reader.read_bits((codebook - 1).bit_length())
                    if rank >= codebook:
                        raise ValueError("MFC1 PVQ rank exceeds the codebook")
                    shape = _unrank_pvq(dimension, pulses, rank)
                    reconstruction = _materialize_band(
                        shape,
                        _gain_code_to_qlog(
                            gain_code,
                            GAIN_FRACTION_BITS,
                        ),
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (pulses, gain_code, rank),
                    )
                elif mode == CellMode.BASIS_REF:
                    basis_id = reader.read_bits(8)
                    shift = reader.read_bits(4) - MAX_SHIFT
                    tilt = reader.read_bits(4) - MAX_TILT
                    gain_code = gain_predictor + reader.read_signed_exp_golomb(
                        maximum_gain_code
                    )
                    if (
                        not 0 <= basis_id < len(bases)
                        or bases[basis_id].size != dimension
                        or not -MAX_SHIFT <= shift <= MAX_SHIFT
                        or not -MAX_TILT <= tilt <= MAX_TILT
                        or not 1 <= gain_code <= maximum_gain_code
                    ):
                        raise ValueError("MFC1 Basis reference exceeds profile")
                    reconstruction = _materialize_band(
                        _basis_direction(bases[basis_id], shift, tilt),
                        _gain_code_to_qlog(
                            gain_code,
                            GAIN_FRACTION_BITS,
                        ),
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (basis_id, shift, tilt, gain_code),
                    )
                elif mode == CellMode.BASIS_CORRECTED:
                    basis_id = reader.read_bits(8)
                    shift = reader.read_bits(4) - MAX_SHIFT
                    tilt = reader.read_bits(4) - MAX_TILT
                    gain_code = gain_predictor + reader.read_signed_exp_golomb(
                        maximum_gain_code
                    )
                    if (
                        not 0 <= basis_id < len(bases)
                        or bases[basis_id].size != dimension
                        or not -MAX_SHIFT <= shift <= MAX_SHIFT
                        or not -MAX_TILT <= tilt <= MAX_TILT
                        or not 1 <= gain_code <= maximum_gain_code
                    ):
                        raise ValueError(
                            "MFC1 corrected Basis exceeds profile"
                        )
                    reconstruction = _materialize_band(
                        _basis_direction(bases[basis_id], shift, tilt),
                        _gain_code_to_qlog(
                            gain_code,
                            GAIN_FRACTION_BITS,
                        ),
                    )
                    correction_count = reader.read_unsigned_exp_golomb(
                        min(MAX_BASIS_CORRECTIONS, dimension)
                    )
                    if correction_count == 0:
                        raise ValueError("MFC1 empty Basis correction")
                    position_width = max(
                        1,
                        (dimension - 1).bit_length(),
                    )
                    positions = np.empty(
                        correction_count,
                        dtype=np.uint16,
                    )
                    corrections = np.empty(
                        correction_count,
                        dtype=np.int64,
                    )
                    previous_position = -1
                    for correction_index in range(correction_count):
                        position = reader.read_bits(position_width)
                        correction = reader.read_signed_exp_golomb(
                            MAX_CORRECTION_ABSOLUTE
                        )
                        if (
                            position <= previous_position
                            or position >= dimension
                            or correction == 0
                        ):
                            raise ValueError(
                                "non-canonical MFC1 Basis correction"
                            )
                        reconstruction[position] += correction
                        positions[correction_index] = position
                        corrections[correction_index] = correction
                        previous_position = position
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (
                            basis_id,
                            shift,
                            tilt,
                            gain_code,
                            positions,
                            corrections,
                        ),
                    )
                elif mode == CellMode.BASIS_UPDATE:
                    if state.kind != "basis":
                        raise ValueError("MFC1 updates an absent Basis state")
                    shift = reader.read_bits(4) - MAX_SHIFT
                    tilt = reader.read_bits(4) - MAX_TILT
                    gain_code = gain_predictor + reader.read_signed_exp_golomb(
                        maximum_gain_code
                    )
                    if (
                        not -MAX_SHIFT <= shift <= MAX_SHIFT
                        or not -MAX_TILT <= tilt <= MAX_TILT
                        or not 1 <= gain_code <= maximum_gain_code
                    ):
                        raise ValueError("MFC1 Basis update exceeds profile")
                    reconstruction = _materialize_band(
                        _basis_direction(
                            bases[state.basis_id],
                            shift,
                            tilt,
                        ),
                        _gain_code_to_qlog(
                            gain_code,
                            GAIN_FRACTION_BITS,
                        ),
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (shift, tilt, gain_code),
                    )
                elif mode == CellMode.STOCHASTIC_SET:
                    seed = reader.read_bits(5)
                    gain_code = gain_predictor + reader.read_signed_exp_golomb(
                        maximum_gain_code
                    )
                    if not 1 <= gain_code <= maximum_gain_code:
                        raise ValueError("MFC1 stochastic gain exceeds profile")
                    direction = _stochastic_direction(
                        dimension,
                        stream_seed,
                        channel,
                        band,
                        seed,
                        0,
                    )
                    reconstruction = _materialize_band(
                        direction,
                        _gain_code_to_qlog(
                            gain_code,
                            GAIN_FRACTION_BITS,
                        ),
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (seed, gain_code),
                    )
                elif mode in {CellMode.TRANSIENT, CellMode.TRUTH}:
                    maximum_count = (
                        min(MAX_TRANSIENT_COEFFICIENTS, dimension)
                        if mode == CellMode.TRANSIENT
                        else dimension
                    )
                    reconstruction = _read_sparse(
                        reader,
                        dimension,
                        maximum_count=maximum_count,
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (),
                    )
                elif mode == CellMode.CHANNEL_SET:
                    source_channel = reader.read_bits(3)
                    gain_q7 = _read_signed_byte(reader)
                    if (
                        source_channel >= channel
                        or gain_q7 == 0
                    ):
                        raise ValueError("MFC1 channel reference is non-causal")
                    reconstruction = _apply_channel_gain(
                        coefficient_grid[
                            source_channel,
                            frame,
                            start:end,
                        ],
                        gain_q7,
                    )
                    candidate = _Candidate(
                        mode,
                        reconstruction,
                        0,
                        0,
                        (source_channel, gain_q7),
                    )
                else:
                    raise ValueError("unsupported MFC1 cell mode")

                coefficient_grid[channel, frame, start:end] = reconstruction
                _apply_candidate_state(
                    candidate,
                    state,
                    bases,
                    frame=frame,
                    dimension=dimension,
                )
                if mode == CellMode.BASIS_SET:
                    basis_bands.append(band)
                decoded_gain = _candidate_gain_code(candidate)
                if decoded_gain is not None:
                    current_gain_code[band] = decoded_gain
            previous_gain_code[channel] = current_gain_code

    reader.require_canonical_end()
    coefficient_grid.flags.writeable = False
    scale_grid = np.zeros(
        (channels, frame_count, band_count),
        dtype=np.uint8,
    )
    reconstruction = _synthesize(
        coefficient_grid,
        scale_grid,
        sample_count=sample_count,
        half_window=half_window,
        edges=edges,
        fixed_transform=True,
    )
    reconstruction.flags.writeable = False
    return MafCellDecodeResult(
        sample_rate,
        reconstruction,
        half_window,
        band_count,
        frame_count,
        coefficient_grid,
    )
