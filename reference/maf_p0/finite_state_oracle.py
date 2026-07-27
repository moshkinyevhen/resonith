"""Bounded adaptive integer entropy oracle for existing LSE2 fields."""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np

from .residual import (
    _BitReader,
    _BitWriter,
    _decode_entropy,
    _encode_entropy,
)
from .sparse_entropy import (
    MAX_PAYLOAD_BYTES,
    MAX_SYMBOLS,
    _checked_symbol_count,
)


MAGIC = b"LAF1"
RICE_VALUE_MAGIC = b"LAR1"
VERSION = 1
HEADER = struct.Struct("<4s5BHIHH6I")
COMPACT_HEADER = struct.Struct("<BBH6I")
RICE_VALUE_HEADER = struct.Struct("<4s7BHIHH6I")
RICE_VALUE_COMPACT_HEADER = struct.Struct("<BBBBH6I")
_TOP = (1 << 32) - 1
_HALF = 1 << 31
_QUARTER = 1 << 30
_THREE_QUARTERS = 3 << 30
_MODEL_LIMIT = 1 << 14
_GAP_THRESHOLDS = (16, 32, 64, 128, 256)


@dataclass(frozen=True)
class FiniteStateSparseFields:
    """Exact LSE2-equivalent fields decoded by the adaptive oracle."""

    scales: np.ndarray
    counts: np.ndarray
    positions: np.ndarray
    values: np.ndarray
    gap_threshold: int


def compact_finite_state_lapped(payload: bytes) -> bytes:
    """Remove LAF1 fields inherited from an authenticated packet envelope."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid LAF1 payload for compact transport")
    fields = HEADER.unpack_from(payload)
    (
        magic,
        version,
        flags,
        count_entropy,
        count_parameter,
        reserved,
        gap_threshold,
        _frame_count,
        _channels,
        _band_count,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = fields
    if magic != MAGIC or version != VERSION or flags != 0 or reserved != 0:
        raise ValueError("unsupported LAF1 compact source")
    compact = (
        COMPACT_HEADER.pack(
            count_entropy,
            count_parameter,
            gap_threshold,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + payload[HEADER.size :]
    )
    if compact_finite_state_lapped_size(compact) != len(compact):
        raise ValueError("LAF1 entropy fields are not exactly framed")
    return compact


def compact_finite_state_lapped_size(payload: bytes) -> int:
    """Return one compact LAF1 record length from local entropy bit counts."""

    if not isinstance(payload, bytes) or len(payload) < COMPACT_HEADER.size:
        raise ValueError("truncated compact LAF1 descriptor")
    fields = COMPACT_HEADER.unpack_from(payload)
    bit_counts = fields[-5:]
    payload_bytes = sum((int(bits) + 7) // 8 for bits in bit_counts)
    total = COMPACT_HEADER.size + payload_bytes
    if total > MAX_PAYLOAD_BYTES or total > len(payload):
        raise ValueError("truncated compact LAF1 fields")
    return total


def expand_compact_finite_state_lapped(
    payload: bytes,
    *,
    frame_count: int,
    channels: int,
    band_count: int,
) -> bytes:
    """Restore one canonical LAF1 header from authenticated inherited shape."""

    size = compact_finite_state_lapped_size(payload)
    if size != len(payload):
        raise ValueError("trailing compact LAF1 bytes")
    (
        count_entropy,
        count_parameter,
        gap_threshold,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = COMPACT_HEADER.unpack_from(payload)
    if (
        frame_count <= 0
        or channels <= 0
        or channels > 0xFFFF
        or band_count <= 0
        or band_count > 0xFFFF
    ):
        raise ValueError("compact LAF1 inherited shape is invalid")
    return (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            count_entropy,
            count_parameter,
            0,
            gap_threshold,
            frame_count,
            channels,
            band_count,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + payload[COMPACT_HEADER.size :]
    )


def compact_rice_value_lapped(payload: bytes) -> bytes:
    """Remove LAR1 shape fields inherited from an authenticated LPS6 packet."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < RICE_VALUE_HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid LAR1 payload for compact transport")
    (
        magic,
        version,
        flags,
        count_entropy,
        count_parameter,
        value_entropy,
        value_parameter,
        reserved,
        gap_threshold,
        _frame_count,
        _channels,
        _band_count,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = RICE_VALUE_HEADER.unpack_from(payload)
    if (
        magic != RICE_VALUE_MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
    ):
        raise ValueError("unsupported LAR1 compact source")
    compact = (
        RICE_VALUE_COMPACT_HEADER.pack(
            count_entropy,
            count_parameter,
            value_entropy,
            value_parameter,
            gap_threshold,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + payload[RICE_VALUE_HEADER.size :]
    )
    if compact_rice_value_lapped_size(compact) != len(compact):
        raise ValueError("LAR1 entropy fields are not exactly framed")
    return compact


def compact_rice_value_lapped_size(payload: bytes) -> int:
    """Return one compact LAR1 record length from local entropy bit counts."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < RICE_VALUE_COMPACT_HEADER.size
    ):
        raise ValueError("truncated compact LAR1 descriptor")
    fields = RICE_VALUE_COMPACT_HEADER.unpack_from(payload)
    bit_counts = fields[-5:]
    payload_bytes = sum((int(bits) + 7) // 8 for bits in bit_counts)
    total = RICE_VALUE_COMPACT_HEADER.size + payload_bytes
    if total > MAX_PAYLOAD_BYTES or total > len(payload):
        raise ValueError("truncated compact LAR1 fields")
    return total


def expand_compact_rice_value_lapped(
    payload: bytes,
    *,
    frame_count: int,
    channels: int,
    band_count: int,
) -> bytes:
    """Restore one canonical LAR1 header from authenticated inherited shape."""

    size = compact_rice_value_lapped_size(payload)
    if size != len(payload):
        raise ValueError("trailing compact LAR1 bytes")
    (
        count_entropy,
        count_parameter,
        value_entropy,
        value_parameter,
        gap_threshold,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = RICE_VALUE_COMPACT_HEADER.unpack_from(payload)
    if (
        frame_count <= 0
        or channels <= 0
        or channels > 0xFFFF
        or band_count <= 0
        or band_count > 0xFFFF
    ):
        raise ValueError("compact LAR1 inherited shape is invalid")
    return (
        RICE_VALUE_HEADER.pack(
            RICE_VALUE_MAGIC,
            VERSION,
            0,
            count_entropy,
            count_parameter,
            value_entropy,
            value_parameter,
            0,
            gap_threshold,
            frame_count,
            channels,
            band_count,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + payload[RICE_VALUE_COMPACT_HEADER.size :]
    )


class _AdaptiveModel:
    """Small deterministic Laplace model with bounded integer frequencies."""

    def __init__(self, alphabet_size: int) -> None:
        if not 2 <= alphabet_size <= 512:
            raise ValueError("adaptive alphabet exceeds the oracle bound")
        self.counts = [1] * alphabet_size
        self.total = alphabet_size

    def interval(self, symbol: int) -> tuple[int, int, int]:
        if not 0 <= symbol < len(self.counts):
            raise ValueError("adaptive symbol exceeds its alphabet")
        low = sum(self.counts[:symbol])
        return low, low + self.counts[symbol], self.total

    def symbol(self, scaled: int) -> tuple[int, int, int, int]:
        cumulative = 0
        for symbol, count in enumerate(self.counts):
            following = cumulative + count
            if scaled < following:
                return symbol, cumulative, following, self.total
            cumulative = following
        raise ValueError("adaptive cumulative frequency exceeds the model")

    def update(self, symbol: int) -> None:
        self.counts[symbol] += 1
        self.total += 1
        if self.total >= _MODEL_LIMIT:
            self.counts = [max(1, (count + 1) // 2) for count in self.counts]
            self.total = sum(self.counts)


def _emit_with_pending(
    writer: _BitWriter,
    bit: int,
    pending: int,
) -> None:
    writer.write_bit(bit)
    for _ in range(pending):
        writer.write_bit(1 - bit)


def _encode_adaptive(
    symbols: np.ndarray,
    alphabet_size: int,
) -> tuple[bytes, int]:
    """Encode a known symbol sequence with a bounded 32-bit arithmetic state."""

    symbol_array = np.asarray(symbols)
    if symbol_array.ndim != 1 or not np.issubdtype(
        symbol_array.dtype,
        np.integer,
    ):
        raise TypeError("adaptive symbols must be one-dimensional integers")
    if symbol_array.size == 0:
        return b"", 0
    model = _AdaptiveModel(alphabet_size)
    writer = _BitWriter()
    low = 0
    high = _TOP
    pending = 0
    for item in symbol_array:
        symbol = int(item)
        cumulative_low, cumulative_high, total = model.interval(symbol)
        width = high - low + 1
        high = low + width * cumulative_high // total - 1
        low = low + width * cumulative_low // total
        while True:
            if high < _HALF:
                _emit_with_pending(writer, 0, pending)
                pending = 0
            elif low >= _HALF:
                _emit_with_pending(writer, 1, pending)
                pending = 0
                low -= _HALF
                high -= _HALF
            elif low >= _QUARTER and high < _THREE_QUARTERS:
                pending += 1
                low -= _QUARTER
                high -= _QUARTER
            else:
                break
            low = (low << 1) & _TOP
            high = ((high << 1) | 1) & _TOP
        model.update(symbol)
    pending += 1
    _emit_with_pending(writer, 0 if low < _QUARTER else 1, pending)
    return writer.finish(), writer.bit_count


def _decode_adaptive_unchecked(
    payload: bytes,
    bit_count: int,
    symbol_count: int,
    alphabet_size: int,
) -> np.ndarray:
    """Decode arithmetic symbols; canonical verification is performed outside."""

    if symbol_count == 0:
        if bit_count or payload:
            raise ValueError("nonempty adaptive field has no symbols")
        return np.empty(0, dtype=np.int64)
    if bit_count <= 0 or len(payload) != (bit_count + 7) // 8:
        raise ValueError("invalid adaptive field length")
    reader = _BitReader(payload, bit_count)

    def read_or_zero() -> int:
        if reader.position == bit_count:
            return 0
        return reader.read_bit()

    code = 0
    for _ in range(32):
        code = ((code << 1) | read_or_zero()) & _TOP
    low = 0
    high = _TOP
    model = _AdaptiveModel(alphabet_size)
    output = np.empty(symbol_count, dtype=np.int64)
    for index in range(symbol_count):
        width = high - low + 1
        scaled = ((code - low + 1) * model.total - 1) // width
        symbol, cumulative_low, cumulative_high, total = model.symbol(scaled)
        high = low + width * cumulative_high // total - 1
        low = low + width * cumulative_low // total
        while True:
            if high < _HALF:
                pass
            elif low >= _HALF:
                low -= _HALF
                high -= _HALF
                code -= _HALF
            elif low >= _QUARTER and high < _THREE_QUARTERS:
                low -= _QUARTER
                high -= _QUARTER
                code -= _QUARTER
            else:
                break
            low = (low << 1) & _TOP
            high = ((high << 1) | 1) & _TOP
            code = ((code << 1) | read_or_zero()) & _TOP
        output[index] = symbol
        model.update(symbol)
    return output


def _decode_adaptive(
    payload: bytes,
    bit_count: int,
    symbol_count: int,
    alphabet_size: int,
) -> np.ndarray:
    """Decode and reject any noncanonical arithmetic representation."""

    output = _decode_adaptive_unchecked(
        payload,
        bit_count,
        symbol_count,
        alphabet_size,
    )
    canonical_payload, canonical_bits = _encode_adaptive(output, alphabet_size)
    if canonical_bits != bit_count or canonical_payload != payload:
        raise ValueError("noncanonical adaptive arithmetic field")
    return output


def _field_bytes(payload: bytes, bit_count: int) -> bytes:
    if len(payload) != (bit_count + 7) // 8:
        raise RuntimeError("internal adaptive bit count mismatch")
    return payload


def _gap_categories(
    gaps: np.ndarray,
    threshold: int,
    half_window: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    if threshold < half_window:
        categories = np.minimum(gaps, threshold).astype(np.int64)
        escaped = gaps[gaps >= threshold].astype(np.uint64)
        alphabet_size = threshold + 1
    else:
        categories = gaps.astype(np.int64)
        escaped = np.empty(0, dtype=np.uint64)
        alphabet_size = half_window
    return categories, escaped, alphabet_size


def _encode_raw_gaps(
    escaped: np.ndarray,
    position_width: int,
) -> tuple[bytes, int]:
    writer = _BitWriter()
    for item in escaped:
        writer.write_bits(int(item), position_width)
    return writer.finish(), writer.bit_count


def encode_finite_state_lapped(
    scales: np.ndarray,
    counts: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    half_window: int,
    native_encoder=None,
) -> bytes:
    """Encode existing sparse fields with adaptive integer entropy only."""

    scale_grid = np.asarray(scales)
    count_grid = np.asarray(counts)
    position_array = np.asarray(positions)
    value_array = np.asarray(values)
    if (
        scale_grid.dtype != np.uint8
        or scale_grid.ndim != 3
        or count_grid.dtype != np.uint16
        or count_grid.shape != scale_grid.shape[:2]
        or position_array.dtype != np.uint16
        or position_array.ndim != 1
        or value_array.dtype != np.int8
        or value_array.shape != position_array.shape
    ):
        raise TypeError("invalid finite-state sparse fields")
    channels, frame_count, band_count = scale_grid.shape
    _checked_symbol_count(channels, frame_count, band_count)
    if (
        half_window <= 1
        or half_window > 65535
        or np.any(scale_grid > 31)
        or np.any(count_grid > half_window)
    ):
        raise ValueError("finite-state sparse field exceeds the profile")
    total_coefficients = int(np.sum(count_grid, dtype=np.uint64))
    if (
        total_coefficients != position_array.size
        or total_coefficients > MAX_SYMBOLS
        or np.any(position_array >= half_window)
    ):
        raise ValueError("finite-state sparse coefficient count mismatch")

    gaps = np.empty(total_coefficients, dtype=np.uint64)
    cursor = 0
    for count in count_grid.reshape(-1):
        count_value = int(count)
        frame_positions = position_array[cursor : cursor + count_value]
        if (
            count_value > 1
            and np.any(np.diff(frame_positions.astype(np.int64)) <= 0)
        ):
            raise ValueError("finite-state positions must be strictly ordered")
        if count_value:
            gaps[cursor] = frame_positions[0]
            if count_value > 1:
                gaps[cursor + 1 : cursor + count_value] = (
                    frame_positions[1:].astype(np.int64)
                    - frame_positions[:-1].astype(np.int64)
                    - 1
                ).astype(np.uint64)
        cursor += count_value

    scale_delta = scale_grid.astype(np.int64)
    count_delta = count_grid.astype(np.int64)
    if frame_count > 1:
        scale_delta[:, 1:, :] -= scale_grid[:, :-1, :].astype(np.int64)
        count_delta[:, 1:] -= count_grid[:, :-1].astype(np.int64)
    adaptive_encode = (
        _encode_adaptive
        if native_encoder is None
        else native_encoder.encode_lapped_adaptive
    )
    scale_payload, scale_bits = adaptive_encode(
        scale_delta.reshape(-1) + 31,
        63,
    )
    count_entropy, count_parameter, count_payload, count_bits = _encode_entropy(
        count_delta.reshape(-1)
    )
    value_payload, value_bits = adaptive_encode(
        value_array.astype(np.int64) + 128,
        256,
    )

    position_width = max(1, (half_window - 1).bit_length())
    thresholds = tuple(
        threshold
        for threshold in _GAP_THRESHOLDS
        if threshold < half_window
    ) + (half_window,)
    gap_candidates = []
    for threshold in thresholds:
        categories, escaped, alphabet_size = _gap_categories(
            gaps,
            threshold,
            half_window,
        )
        category_payload, category_bits = adaptive_encode(
            categories,
            alphabet_size,
        )
        raw_payload, raw_bits = _encode_raw_gaps(escaped, position_width)
        gap_candidates.append(
            (
                len(category_payload) + len(raw_payload),
                threshold,
                category_payload,
                category_bits,
                raw_payload,
                raw_bits,
            )
        )
    (
        _gap_bytes,
        gap_threshold,
        gap_payload,
        gap_bits,
        raw_gap_payload,
        raw_gap_bits,
    ) = min(gap_candidates, key=lambda item: (item[0], item[1]))
    payload = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            count_entropy,
            count_parameter,
            0,
            gap_threshold,
            frame_count,
            channels,
            band_count,
            total_coefficients,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + _field_bytes(scale_payload, scale_bits)
        + count_payload
        + _field_bytes(gap_payload, gap_bits)
        + _field_bytes(raw_gap_payload, raw_gap_bits)
        + _field_bytes(value_payload, value_bits)
    )
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("finite-state sparse payload exceeds the byte bound")
    return payload


def encode_rice_value_lapped(
    scales: np.ndarray,
    counts: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    half_window: int,
    native_encoder=None,
) -> bytes:
    """Encode LAF1 fields while selecting bounded Rice/packed value entropy."""

    adaptive = encode_finite_state_lapped(
        scales,
        counts,
        positions,
        values,
        half_window=half_window,
        native_encoder=native_encoder,
    )
    (
        _magic,
        _version,
        _flags,
        count_entropy,
        count_parameter,
        _reserved,
        gap_threshold,
        frame_count,
        channels,
        band_count,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        adaptive_value_bits,
    ) = HEADER.unpack_from(adaptive)
    old_sizes = [
        (int(bits) + 7) // 8
        for bits in (
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            adaptive_value_bits,
        )
    ]
    common_end = HEADER.size + sum(old_sizes[:-1])
    common_payload = adaptive[HEADER.size:common_end]
    value_array = np.asarray(values)
    if np.any(value_array == 0):
        raise ValueError("LAR1 sparse values must be nonzero")
    bounded_encode = (
        _encode_entropy
        if native_encoder is None
        else native_encoder.encode_lapped_bounded
    )
    (
        value_entropy,
        value_parameter,
        value_payload,
        value_bits,
    ) = bounded_encode(value_array.astype(np.int64))
    payload = (
        RICE_VALUE_HEADER.pack(
            RICE_VALUE_MAGIC,
            VERSION,
            0,
            count_entropy,
            count_parameter,
            value_entropy,
            value_parameter,
            0,
            gap_threshold,
            frame_count,
            channels,
            band_count,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
        + common_payload
        + value_payload
    )
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("rice-value lapped payload exceeds the byte bound")
    return payload


def decode_rice_value_lapped(
    payload: bytes,
    *,
    half_window: int,
    expected_channels: int,
    expected_frames: int,
    expected_bands: int,
) -> FiniteStateSparseFields:
    """Independently validate and decode one complete LAR1 sparse field."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < RICE_VALUE_HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid rice-value lapped payload length")
    (
        magic,
        version,
        flags,
        count_entropy,
        count_parameter,
        value_entropy,
        value_parameter,
        reserved,
        gap_threshold,
        frame_count,
        channels,
        band_count,
        coefficient_count,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = RICE_VALUE_HEADER.unpack_from(payload)
    if (
        magic != RICE_VALUE_MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
        or frame_count != expected_frames
        or channels != expected_channels
        or band_count != expected_bands
    ):
        raise ValueError("unsupported rice-value lapped header")
    sizes = [
        (int(bits) + 7) // 8
        for bits in (
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            value_bits,
        )
    ]
    if RICE_VALUE_HEADER.size + sum(sizes) != len(payload):
        raise ValueError("rice-value lapped entropy length mismatch")
    common_bytes = sum(sizes[:-1])
    common_payload = payload[
        RICE_VALUE_HEADER.size : RICE_VALUE_HEADER.size + common_bytes
    ]
    value_payload = payload[-sizes[-1] :] if sizes[-1] else b""
    decoded_values = _decode_entropy(
        value_payload,
        value_bits,
        coefficient_count,
        value_entropy,
        value_parameter,
    )
    if (
        np.any(decoded_values < -128)
        or np.any(decoded_values > 127)
        or np.any(decoded_values == 0)
    ):
        raise ValueError("decoded LAR1 value exceeds the sparse profile")

    dummy_payload, dummy_bits = _encode_adaptive(
        np.full(coefficient_count, 129, dtype=np.uint16),
        256,
    )
    laf1 = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            count_entropy,
            count_parameter,
            0,
            gap_threshold,
            frame_count,
            channels,
            band_count,
            coefficient_count,
            scale_bits,
            count_bits,
            gap_bits,
            raw_gap_bits,
            dummy_bits,
        )
        + common_payload
        + dummy_payload
    )
    common = decode_finite_state_lapped(
        laf1,
        half_window=half_window,
        expected_channels=expected_channels,
        expected_frames=expected_frames,
        expected_bands=expected_bands,
    )
    values8 = decoded_values.astype(np.int8)
    values8.flags.writeable = False
    return FiniteStateSparseFields(
        common.scales,
        common.counts,
        common.positions,
        values8,
        common.gap_threshold,
    )


def decode_finite_state_lapped(
    payload: bytes,
    *,
    half_window: int,
    expected_channels: int,
    expected_frames: int,
    expected_bands: int,
) -> FiniteStateSparseFields:
    """Decode one exact independently reset adaptive sparse field."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid finite-state sparse payload length")
    (
        magic,
        version,
        flags,
        count_entropy,
        count_parameter,
        reserved,
        gap_threshold,
        frame_count,
        channels,
        band_count,
        total_coefficients,
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    ) = HEADER.unpack_from(payload)
    if (
        magic != MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
        or frame_count != expected_frames
        or channels != expected_channels
        or band_count != expected_bands
        or total_coefficients > MAX_SYMBOLS
        or gap_threshold <= 0
        or gap_threshold > half_window
    ):
        raise ValueError("finite-state sparse header mismatch")
    scale_count = _checked_symbol_count(channels, frame_count, band_count)
    frame_symbol_count = _checked_symbol_count(channels, frame_count)
    bit_counts = (
        scale_bits,
        count_bits,
        gap_bits,
        raw_gap_bits,
        value_bits,
    )
    byte_counts = tuple((int(bits) + 7) // 8 for bits in bit_counts)
    if sum(byte_counts) != len(payload) - HEADER.size:
        raise ValueError("finite-state sparse entropy length mismatch")
    cursor = HEADER.size
    fields: list[bytes] = []
    for byte_count in byte_counts:
        fields.append(payload[cursor : cursor + byte_count])
        cursor += byte_count

    scale_symbols = _decode_adaptive(fields[0], scale_bits, scale_count, 63)
    scale_delta = (scale_symbols - 31).reshape(
        channels,
        frame_count,
        band_count,
    )
    scales64 = scale_delta.copy()
    for frame in range(1, frame_count):
        scales64[:, frame, :] += scales64[:, frame - 1, :]
    if np.any(scales64 < 0) or np.any(scales64 > 31):
        raise ValueError("decoded finite-state scale exceeds the profile")
    scales = scales64.astype(np.uint8)

    count_delta = _decode_entropy(
        fields[1],
        count_bits,
        frame_symbol_count,
        count_entropy,
        count_parameter,
    ).reshape(channels, frame_count)
    counts64 = count_delta.copy()
    for frame in range(1, frame_count):
        counts64[:, frame] += counts64[:, frame - 1]
    if (
        np.any(counts64 < 0)
        or np.any(counts64 > half_window)
        or int(np.sum(counts64, dtype=np.int64)) != total_coefficients
    ):
        raise ValueError("decoded finite-state count exceeds the profile")
    counts = counts64.astype(np.uint16)

    gap_alphabet = (
        gap_threshold + 1
        if gap_threshold < half_window
        else half_window
    )
    gap_categories = _decode_adaptive(
        fields[2],
        gap_bits,
        total_coefficients,
        gap_alphabet,
    )
    escape_count = (
        int(np.count_nonzero(gap_categories == gap_threshold))
        if gap_threshold < half_window
        else 0
    )
    position_width = max(1, (half_window - 1).bit_length())
    if raw_gap_bits != escape_count * position_width:
        raise ValueError("finite-state raw gap count mismatch")
    raw_reader = _BitReader(fields[3], raw_gap_bits)
    gaps = gap_categories.astype(np.uint16)
    if gap_threshold < half_window:
        for index in np.flatnonzero(gap_categories == gap_threshold):
            gap = raw_reader.read_bits(position_width)
            if gap < gap_threshold or gap >= half_window:
                raise ValueError("finite-state escaped gap exceeds the profile")
            gaps[index] = gap
    if raw_reader.position != raw_gap_bits:
        raise ValueError("trailing finite-state raw gap bits")

    positions = np.empty(total_coefficients, dtype=np.uint16)
    gap_cursor = 0
    for count in counts.reshape(-1):
        previous = -1
        for _ in range(int(count)):
            position = previous + 1 + int(gaps[gap_cursor])
            if position >= half_window:
                raise ValueError("decoded finite-state position exceeds the window")
            positions[gap_cursor] = position
            previous = position
            gap_cursor += 1
    value_symbols = _decode_adaptive(
        fields[4],
        value_bits,
        total_coefficients,
        256,
    )
    values64 = value_symbols - 128
    if np.any(values64 == 0):
        raise ValueError("finite-state sparse value must be nonzero")
    values = values64.astype(np.int8)
    for array in (scales, counts, positions, values):
        array.flags.writeable = False
    return FiniteStateSparseFields(
        scales,
        counts,
        positions,
        values,
        gap_threshold,
    )
