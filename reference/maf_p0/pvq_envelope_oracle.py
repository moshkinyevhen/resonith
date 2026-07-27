"""R-108 bounded integer PVQ with a predictive log-gain envelope."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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
from .rsc1 import SECTION_CRITICAL, RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAGIC = b"PVE1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIIHHIHI")
MAX_PAYLOAD_BYTES = 512 << 20
MAX_PULSES_PER_BAND = 255
MAX_LOG_GAIN_Q8 = 256 * 47 + 255 + 1
LOG_GAIN_FRACTION_BITS = 8
LOG2_FRACTION_MULTIPLIERS_Q31 = (
    3037000500,
    2553802834,
    2341847524,
    2242560872,
    2194507417,
    2170868212,
    2159144272,
    2153306067,
)


@dataclass(frozen=True)
class PvqEnvelopeDecodeResult:
    """Independently decoded PCM and prospective PVE1 parameters."""

    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    frame_count: int
    maximum_pulses_per_frame: int
    coefficient_grid: np.ndarray
    scale_grid: np.ndarray


@dataclass(frozen=True)
class PvqEnvelopeEncodeResult:
    """Complete PVE1 stream, actual decode, and exact bit accounting."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


class _BitWriter:
    """MSB-first bit writer with an explicit logical bit count."""

    def __init__(self) -> None:
        self._bytes = bytearray()
        self._current = 0
        self._used = 0
        self.bit_count = 0

    def write_bit(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("bit value must be zero or one")
        self._current = (self._current << 1) | value
        self._used += 1
        self.bit_count += 1
        if self._used == 8:
            self._bytes.append(self._current)
            self._current = 0
            self._used = 0

    def write_bits(self, value: int, width: int) -> None:
        if width < 0 or value < 0 or value >= (1 << width):
            raise ValueError("fixed-width value exceeds its field")
        for shift in range(width - 1, -1, -1):
            self.write_bit((value >> shift) & 1)

    def write_unsigned_exp_golomb(self, value: int) -> None:
        if value < 0:
            raise ValueError("Exp-Golomb value must be nonnegative")
        code = value + 1
        prefix = code.bit_length() - 1
        for _ in range(prefix):
            self.write_bit(0)
        self.write_bits(code, prefix + 1)

    def write_signed_exp_golomb(self, value: int) -> None:
        mapped = 2 * value if value >= 0 else -2 * value - 1
        self.write_unsigned_exp_golomb(mapped)

    def finish(self) -> bytes:
        if self._used:
            self._bytes.append(self._current << (8 - self._used))
            self._current = 0
            self._used = 0
        return bytes(self._bytes)


class _BitReader:
    """Bounded reader that rejects over-read and nonzero padding."""

    def __init__(self, payload: bytes, bit_count: int) -> None:
        if bit_count < 0 or bit_count > len(payload) * 8:
            raise ValueError("invalid PVE1 logical bit count")
        self._payload = payload
        self.bit_count = bit_count
        self.position = 0

    def read_bit(self) -> int:
        if self.position >= self.bit_count:
            raise ValueError("truncated PVE1 bitstream")
        byte = self._payload[self.position >> 3]
        value = (byte >> (7 - (self.position & 7))) & 1
        self.position += 1
        return value

    def read_bits(self, width: int) -> int:
        if width < 0 or self.position + width > self.bit_count:
            raise ValueError("truncated PVE1 fixed-width field")
        value = 0
        for _ in range(width):
            value = (value << 1) | self.read_bit()
        return value

    def read_unsigned_exp_golomb(self, maximum: int) -> int:
        prefix = 0
        while self.read_bit() == 0:
            prefix += 1
            if prefix > 30:
                raise ValueError("PVE1 Exp-Golomb prefix exceeds the bound")
        suffix = self.read_bits(prefix)
        value = (1 << prefix) - 1 + suffix
        if value > maximum:
            raise ValueError("PVE1 Exp-Golomb value exceeds the bound")
        return value

    def read_signed_exp_golomb(self, maximum_absolute: int) -> int:
        mapped = self.read_unsigned_exp_golomb(2 * maximum_absolute)
        value = mapped // 2 if mapped & 1 == 0 else -(mapped // 2) - 1
        if abs(value) > maximum_absolute:
            raise ValueError("PVE1 signed value exceeds the bound")
        return value

    def require_canonical_end(self) -> None:
        if self.position != self.bit_count:
            raise ValueError("trailing logical PVE1 bits")
        for position in range(self.bit_count, len(self._payload) * 8):
            byte = self._payload[position >> 3]
            if (byte >> (7 - (position & 7))) & 1:
                raise ValueError("nonzero PVE1 padding bits")


@lru_cache(maxsize=8192)
def _pvq_codebook_size(dimension: int, pulses: int) -> int:
    """Count signed integer vectors with exact L1 norm."""

    if dimension <= 0 or pulses < 0:
        raise ValueError("invalid PVQ codebook dimensions")
    if pulses == 0:
        return 1
    if dimension == 1:
        return 2
    total = _pvq_codebook_size(dimension - 1, pulses)
    for magnitude in range(1, pulses + 1):
        total += 2 * _pvq_codebook_size(
            dimension - 1,
            pulses - magnitude,
        )
    return total


def _rank_pvq(vector: np.ndarray) -> tuple[int, int]:
    """Rank one pulse vector in a deterministic lexicographic codebook."""

    values = np.asarray(vector)
    if values.ndim != 1 or not np.issubdtype(values.dtype, np.signedinteger):
        raise TypeError("PVQ vector must be one-dimensional signed integers")
    pulses = int(np.sum(np.abs(values), dtype=np.int64))
    remaining = pulses
    rank = 0
    for index, item in enumerate(values[:-1]):
        value = int(item)
        dimension = values.size - index - 1
        for candidate in range(-remaining, value):
            magnitude = abs(candidate)
            if magnitude <= remaining:
                rank += _pvq_codebook_size(
                    dimension,
                    remaining - magnitude,
                )
        remaining -= abs(value)
    if remaining < 0 or abs(int(values[-1])) != remaining:
        raise ValueError("PVQ vector L1 norm is inconsistent")
    if remaining and int(values[-1]) > 0:
        rank += 1
    codebook = _pvq_codebook_size(values.size, pulses)
    if not 0 <= rank < codebook:
        raise RuntimeError("PVQ rank escaped its codebook")
    return rank, pulses


def _unrank_pvq(dimension: int, pulses: int, rank: int) -> np.ndarray:
    """Invert `_rank_pvq` without allocating the full codebook."""

    codebook = _pvq_codebook_size(dimension, pulses)
    if not 0 <= rank < codebook:
        raise ValueError("PVQ index exceeds its codebook")
    output = np.zeros(dimension, dtype=np.int16)
    remaining = pulses
    for index in range(dimension - 1):
        tail_dimension = dimension - index - 1
        chosen = None
        for candidate in range(-remaining, remaining + 1):
            count = _pvq_codebook_size(
                tail_dimension,
                remaining - abs(candidate),
            )
            if rank < count:
                chosen = candidate
                break
            rank -= count
        if chosen is None:
            raise RuntimeError("PVQ unrank failed to select a coordinate")
        output[index] = chosen
        remaining -= abs(chosen)
    if remaining:
        output[-1] = -remaining if rank == 0 else remaining
    if _rank_pvq(output)[0] >= codebook:
        raise RuntimeError("PVQ unrank produced an invalid vector")
    return output


def _decoded_log_gain(qlog: int) -> int:
    """Materialize one Q8 log2 gain through eight frozen Q31 products."""

    if qlog == 0:
        return 0
    if not 1 <= qlog <= MAX_LOG_GAIN_Q8:
        raise ValueError("PVE1 log gain exceeds the profile")
    code = qlog - 1
    exponent = code >> LOG_GAIN_FRACTION_BITS
    fraction = code & ((1 << LOG_GAIN_FRACTION_BITS) - 1)
    mantissa_q31 = 1 << 31
    for index, multiplier in enumerate(
        LOG2_FRACTION_MULTIPLIERS_Q31
    ):
        if fraction & (1 << (7 - index)):
            mantissa_q31 = (
                mantissa_q31 * multiplier + (1 << 30)
            ) >> 31
    if exponent >= 31:
        return mantissa_q31 << (exponent - 31)
    shift = 31 - exponent
    return (mantissa_q31 + (1 << (shift - 1))) >> shift


def _quantize_log_gain(gain: int) -> int:
    """Select the nearest frozen Q8 gain by monotonic integer search."""

    if gain <= 0:
        return 0
    low = 1
    high = MAX_LOG_GAIN_Q8
    while low < high:
        middle = (low + high) // 2
        if _decoded_log_gain(middle) < gain:
            low = middle + 1
        else:
            high = middle
    candidates = {low}
    if low > 1:
        candidates.add(low - 1)
    return min(
        candidates,
        key=lambda qlog: (abs(_decoded_log_gain(qlog) - gain), qlog),
    )


def _round_divide_signed(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("signed division requires a positive denominator")
    magnitude = abs(numerator)
    quotient, remainder = divmod(magnitude, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return -quotient if numerator < 0 else quotient


def _predict_log_gain(
    previous_frame: np.ndarray,
    current_frame: np.ndarray,
    frame: int,
    band: int,
) -> int:
    temporal = int(previous_frame[band]) if frame else 0
    spectral = int(current_frame[band - 1]) if band else 0
    if frame and band:
        return (3 * temporal + spectral + 2) // 4
    return temporal if frame else spectral


def _allocate_band_pulses(
    coefficient_row: np.ndarray,
    edges: tuple[int, ...],
    maximum_pulses: int,
    minimum_active_power_ratio_q20: int,
) -> np.ndarray:
    """Allocate a bounded frame budget by integer band L2 energy."""

    gains = []
    for start, end in zip(edges[:-1], edges[1:], strict=True):
        band = coefficient_row[start:end].astype(np.int64)
        gains.append(math.isqrt(int(band @ band)))
    gains_array = np.asarray(gains, dtype=np.int64)
    counts = np.zeros(len(gains), dtype=np.uint16)
    peak = int(np.max(gains_array, initial=0))
    if peak == 0 or maximum_pulses == 0:
        return counts
    active = np.asarray(
        [
            index
            for index, gain in enumerate(gains)
            if gain * gain * (1 << 20)
            >= peak * peak * minimum_active_power_ratio_q20
        ],
        dtype=np.int64,
    )
    if active.size > maximum_pulses:
        active = active[
            np.argpartition(gains_array[active], -maximum_pulses)[
                -maximum_pulses:
            ]
        ]
    counts[active] = 1
    remaining = maximum_pulses - int(active.size)
    if remaining == 0:
        return counts
    total = int(np.sum(gains_array[active], dtype=np.int64))
    numerators = gains_array[active] * remaining
    additions = numerators // total
    counts[active] += additions.astype(np.uint16)
    unassigned = remaining - int(np.sum(additions, dtype=np.int64))
    if unassigned:
        remainders = numerators - additions * total
        winners = active[
            np.argsort(remainders, kind="stable")[-unassigned:]
        ]
        counts[winners] += 1
    return counts


def _pulse_shape(target: np.ndarray, pulses: int) -> np.ndarray:
    """Greedily maximize squared target correlation per pulse-vector energy."""

    values = target.astype(np.int64)
    output = np.zeros(values.size, dtype=np.int16)
    if pulses == 0:
        return output
    magnitudes = np.abs(values)
    if not np.any(magnitudes):
        raise ValueError("nonzero pulse count requires a nonzero target")
    counts = np.zeros(values.size, dtype=np.int64)
    correlation = 0
    energy = 0
    for _ in range(pulses):
        best_index = 0
        best_correlation = -1
        best_energy = 1
        for index, magnitude in enumerate(magnitudes):
            candidate_correlation = correlation + int(magnitude)
            candidate_energy = energy + 2 * int(counts[index]) + 1
            if (
                best_correlation < 0
                or candidate_correlation
                * candidate_correlation
                * best_energy
                > best_correlation
                * best_correlation
                * candidate_energy
            ):
                best_index = index
                best_correlation = candidate_correlation
                best_energy = candidate_energy
        counts[best_index] += 1
        correlation = best_correlation
        energy = best_energy
    signed = np.where(values < 0, -counts, counts)
    return signed.astype(np.int16)


def _projected_gain(target: np.ndarray, pulses: np.ndarray) -> int:
    """Return the least-squares gain for the decoder's integer direction."""

    target64 = target.astype(np.int64)
    pulses64 = pulses.astype(np.int64)
    norm_squared = int(pulses64 @ pulses64)
    correlation = int(target64 @ pulses64)
    if norm_squared == 0 or correlation <= 0:
        return 0
    norm_q15 = math.isqrt(norm_squared << 30)
    return _round_divide_signed(
        correlation * norm_q15,
        norm_squared << 15,
    )


def _materialize_band(pulses: np.ndarray, qlog: int) -> np.ndarray:
    """Convert a pulse direction and quantized gain to integer coefficients."""

    gain = _decoded_log_gain(qlog)
    norm_squared = int(
        pulses.astype(np.int64) @ pulses.astype(np.int64)
    )
    if gain == 0 or norm_squared == 0:
        return np.zeros(pulses.size, dtype=np.int64)
    norm_q15 = math.isqrt(norm_squared << 30)
    output = np.empty(pulses.size, dtype=np.int64)
    for index, pulse in enumerate(pulses):
        output[index] = _round_divide_signed(
            gain * int(pulse) * (1 << 15),
            norm_q15,
        )
    return output


def _source_coefficient_row(
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


def encode_pvq_envelope_analysis(
    analysis: LappedAnalysis,
    *,
    maximum_pulses_per_frame: int,
    minimum_active_power_ratio_q20: int = 10,
) -> PvqEnvelopeEncodeResult:
    """Serialize and independently decode one complete prospective PVE1."""

    if not isinstance(analysis, LappedAnalysis) or not analysis.fixed_transform:
        raise TypeError("PVE1 requires one fixed-integer LappedAnalysis")
    if not 1 <= maximum_pulses_per_frame <= analysis.half_window:
        raise ValueError("PVE1 pulse budget exceeds the transform window")
    if not 0 <= minimum_active_power_ratio_q20 <= (1 << 20):
        raise ValueError("PVE1 active-power ratio exceeds Q20")
    edges = _band_edges(analysis.half_window, analysis.band_count)
    writer = _BitWriter()
    count_bits = 0
    gain_bits = 0
    shape_bits = 0
    active_band_count = 0

    previous_qlog = np.zeros(
        (analysis.samples.shape[1], analysis.band_count),
        dtype=np.int16,
    )
    for channel in range(analysis.samples.shape[1]):
        for frame in range(analysis.frame_count):
            row = _source_coefficient_row(
                analysis,
                channel,
                frame,
                edges,
            )
            counts = _allocate_band_pulses(
                row,
                edges,
                maximum_pulses_per_frame,
                minimum_active_power_ratio_q20,
            )
            current_qlog = np.zeros(analysis.band_count, dtype=np.int16)
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                pulses = int(counts[band])
                before = writer.bit_count
                writer.write_unsigned_exp_golomb(pulses)
                count_bits += writer.bit_count - before
                if pulses == 0:
                    continue
                active_band_count += 1
                target = row[start:end]
                shape = _pulse_shape(target, pulses)
                gain = _projected_gain(target, shape)
                qlog = _quantize_log_gain(gain)
                predictor = _predict_log_gain(
                    previous_qlog[channel],
                    current_qlog,
                    frame,
                    band,
                )
                before = writer.bit_count
                writer.write_signed_exp_golomb(qlog - predictor)
                gain_bits += writer.bit_count - before
                current_qlog[band] = qlog

                rank, actual_pulses = _rank_pvq(shape)
                if actual_pulses != pulses:
                    raise RuntimeError("PVQ pulse quantizer changed the budget")
                codebook = _pvq_codebook_size(end - start, pulses)
                width = (codebook - 1).bit_length()
                before = writer.bit_count
                writer.write_bits(rank, width)
                shape_bits += writer.bit_count - before
            previous_qlog[channel] = current_qlog

    bit_count = writer.bit_count
    bit_payload = writer.finish()
    if len(bit_payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("PVE1 payload exceeds the research profile")
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            analysis.samples.shape[1],
            analysis.sample_rate,
            analysis.samples.shape[0],
            analysis.half_window,
            analysis.band_count,
            analysis.frame_count,
            maximum_pulses_per_frame,
            bit_count,
        )
        + bit_payload
    )
    payload = pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(
                    StreamConfig(
                        analysis.samples.shape[0],
                        1,
                        analysis.samples.shape[1],
                    )
                ),
            ),
            RSC1Section("PVE1", body),
        ],
        profile=0,
        level=5,
        timebase_hz=analysis.sample_rate,
    )
    decoded = decode_pvq_envelope_stream(payload)
    quality = _quality_report(
        analysis.samples.reshape(-1),
        decoded.samples.reshape(-1),
    )
    report = {
        **quality,
        "status": "R-108 prospective integer PVQ; non-normative",
        "format_profile": "prospective-PVE1-RSC1-level-5",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": analysis.sample_rate,
        "frame_count": int(analysis.samples.shape[0]),
        "channel_count": int(analysis.samples.shape[1]),
        "transform_frame_count": analysis.frame_count,
        "half_window": analysis.half_window,
        "band_count": analysis.band_count,
        "maximum_pulses_per_frame": maximum_pulses_per_frame,
        "minimum_active_power_ratio_q20": (
            minimum_active_power_ratio_q20
        ),
        "logical_bits": bit_count,
        "count_bits": count_bits,
        "gain_bits": gain_bits,
        "shape_bits": shape_bits,
        "padding_bits": len(bit_payload) * 8 - bit_count,
        "active_band_count": active_band_count,
        "analysis_backend": analysis.analysis_backend,
        "reconstruction_backend": "independent Python integer PVE1 decoder",
        "fixed_log2_fraction_multipliers_q31": list(
            LOG2_FRACTION_MULTIPLIERS_Q31
        ),
    }
    return PvqEnvelopeEncodeResult(payload, decoded.samples, report)


def decode_pvq_envelope_stream(payload: bytes) -> PvqEnvelopeDecodeResult:
    """Validate, bound, and decode one prospective PVE1 stream."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 5):
        raise ValueError("unsupported PVE1 research profile")
    config_sections = []
    pvq_sections = []
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code == b"CONF":
            config_sections.append(section)
        elif type_code == b"PVE1":
            pvq_sections.append(section)
        elif section.flags & SECTION_CRITICAL:
            raise ValueError("unknown critical PVE1 section")
    if (
        len(config_sections) != 1
        or len(pvq_sections) != 1
        or config_sections[0].instance_id != 0
        or pvq_sections[0].instance_id != 0
        or config_sections[0].start_tick != 0
        or pvq_sections[0].start_tick != 0
    ):
        raise ValueError("non-canonical PVE1 sections")
    config = unpack_conf(config_sections[0].payload)
    body = pvq_sections[0].payload
    if len(body) < HEADER.size or len(body) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid PVE1 section size")
    (
        magic,
        version,
        flags,
        channels,
        sample_rate,
        sample_count,
        half_window,
        band_count,
        frame_count,
        maximum_pulses_per_frame,
        bit_count,
    ) = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION or flags != 0:
        raise ValueError("unsupported PVE1 stream")
    if (
        not 1 <= channels <= MAX_CHANNELS
        or not 32 <= half_window <= MAX_HALF_WINDOW
        or half_window & (half_window - 1)
        or not 1 <= band_count <= min(MAX_BANDS, half_window)
        or not 1 <= maximum_pulses_per_frame <= half_window
    ):
        raise ValueError("PVE1 header exceeds the profile")
    if (
        sample_rate != info.timebase_hz
        or sample_count != config.sample_count
        or channels != config.output_channels
        or config.innovation_step != 1
        or frame_count != sample_count // half_window + 1
    ):
        raise ValueError("PVE1 cross-section mismatch")
    edges = _band_edges(half_window, band_count)
    bit_payload = body[HEADER.size:]
    reader = _BitReader(bit_payload, bit_count)
    coefficient_grid = np.zeros(
        (channels, frame_count, half_window),
        dtype=np.int64,
    )
    scale_grid = np.zeros(
        (channels, frame_count, band_count),
        dtype=np.uint8,
    )
    previous_qlog = np.zeros((channels, band_count), dtype=np.int16)
    for channel in range(channels):
        for frame in range(frame_count):
            current_qlog = np.zeros(band_count, dtype=np.int16)
            frame_pulses = 0
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                pulses = reader.read_unsigned_exp_golomb(
                    min(MAX_PULSES_PER_BAND, maximum_pulses_per_frame)
                )
                frame_pulses += pulses
                if frame_pulses > maximum_pulses_per_frame:
                    raise ValueError("PVE1 frame pulse budget exceeded")
                if pulses == 0:
                    continue
                predictor = _predict_log_gain(
                    previous_qlog[channel],
                    current_qlog,
                    frame,
                    band,
                )
                residual = reader.read_signed_exp_golomb(MAX_LOG_GAIN_Q8)
                qlog = predictor + residual
                if not 1 <= qlog <= MAX_LOG_GAIN_Q8:
                    raise ValueError("PVE1 predicted gain exceeds the profile")
                current_qlog[band] = qlog
                codebook = _pvq_codebook_size(end - start, pulses)
                width = (codebook - 1).bit_length()
                rank = reader.read_bits(width)
                if rank >= codebook:
                    raise ValueError("PVE1 PVQ index exceeds the codebook")
                shape = _unrank_pvq(end - start, pulses, rank)
                coefficient_grid[channel, frame, start:end] = (
                    _materialize_band(shape, qlog)
                )
            previous_qlog[channel] = current_qlog
    reader.require_canonical_end()
    coefficient_grid.flags.writeable = False
    scale_grid.flags.writeable = False
    reconstruction = _synthesize(
        coefficient_grid,
        scale_grid,
        sample_count=sample_count,
        half_window=half_window,
        edges=edges,
        fixed_transform=True,
    )
    return PvqEnvelopeDecodeResult(
        sample_rate,
        reconstruction,
        half_window,
        band_count,
        frame_count,
        maximum_pulses_per_frame,
        coefficient_grid,
        scale_grid,
    )
