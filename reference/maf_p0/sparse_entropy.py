"""Bounded sparse entropy prototype for lapped Innovation."""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np

from .residual import (
    ENTROPY_PACKED,
    ENTROPY_RICE,
    MAX_RICE_PARAMETER,
    RICE_ESCAPE_QUOTIENT,
    _BitReader,
    _BitWriter,
    _decode_entropy,
    _encode_entropy,
)


MAGIC = b"LSE1"
VARIABLE_MAGIC = b"LSE2"
VERSION = 1
HEADER = struct.Struct("<4sBBBBBBBBIHHHIII")
VARIABLE_HEADER = struct.Struct("<4sBBBBBBBBBBIHHIIIII")
COMPACT_VARIABLE_HEADER = struct.Struct("<BBBBBBBIIIII")
MAX_SYMBOLS = 64 << 20
MAX_PAYLOAD_BYTES = 512 << 20


def compact_variable_sparse_lapped(payload: bytes) -> bytes:
    """Remove LSE2 fields inherited from a transport-framed sequence."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < VARIABLE_HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid LSE2 payload for compact transport")
    (
        magic,
        version,
        flags,
        scale_entropy,
        scale_parameter,
        count_entropy,
        count_parameter,
        position_parameter,
        value_entropy,
        value_parameter,
        reserved,
        _frame_count,
        _channels,
        _band_count,
        coefficient_count,
        scale_bits,
        count_bits,
        position_bits,
        value_bits,
    ) = VARIABLE_HEADER.unpack_from(payload)
    if (
        magic != VARIABLE_MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
    ):
        raise ValueError("unsupported LSE2 compact source")
    return (
        COMPACT_VARIABLE_HEADER.pack(
            scale_entropy,
            scale_parameter,
            count_entropy,
            count_parameter,
            position_parameter,
            value_entropy,
            value_parameter,
            coefficient_count,
            scale_bits,
            count_bits,
            position_bits,
            value_bits,
        )
        + payload[VARIABLE_HEADER.size:]
    )


def compact_variable_sparse_lapped_size(payload: bytes) -> int:
    """Return one compact record length from its local entropy bit counts."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < COMPACT_VARIABLE_HEADER.size
    ):
        raise ValueError("truncated compact LSE2 descriptor")
    fields = COMPACT_VARIABLE_HEADER.unpack_from(payload)
    bit_counts = fields[-4:]
    payload_bytes = sum((int(bits) + 7) // 8 for bits in bit_counts)
    total = COMPACT_VARIABLE_HEADER.size + payload_bytes
    if total > MAX_PAYLOAD_BYTES or total > len(payload):
        raise ValueError("truncated compact LSE2 fields")
    return total


def expand_compact_variable_sparse_lapped(
    payload: bytes,
    *,
    frame_count: int,
    channels: int,
    band_count: int,
) -> bytes:
    """Restore a canonical LSE2 header from authenticated sequence fields."""

    size = compact_variable_sparse_lapped_size(payload)
    if size != len(payload):
        raise ValueError("trailing compact LSE2 bytes")
    (
        scale_entropy,
        scale_parameter,
        count_entropy,
        count_parameter,
        position_parameter,
        value_entropy,
        value_parameter,
        coefficient_count,
        scale_bits,
        count_bits,
        position_bits,
        value_bits,
    ) = COMPACT_VARIABLE_HEADER.unpack_from(payload)
    if (
        frame_count <= 0
        or channels <= 0
        or channels > 0xFFFF
        or band_count <= 0
        or band_count > 0xFFFF
    ):
        raise ValueError("compact LSE2 inherited shape is invalid")
    return (
        VARIABLE_HEADER.pack(
            VARIABLE_MAGIC,
            VERSION,
            0,
            scale_entropy,
            scale_parameter,
            count_entropy,
            count_parameter,
            position_parameter,
            value_entropy,
            value_parameter,
            0,
            frame_count,
            channels,
            band_count,
            coefficient_count,
            scale_bits,
            count_bits,
            position_bits,
            value_bits,
        )
        + payload[COMPACT_VARIABLE_HEADER.size:]
    )


@dataclass(frozen=True)
class SparseLappedFields:
    """Exact decoded scale, position, and signed-value fields."""

    scales: np.ndarray
    positions: np.ndarray
    values: np.ndarray
    position_parameter: int


@dataclass(frozen=True)
class VariableSparseLappedFields:
    """Decoded variable-density fields in channel/frame traversal order."""

    scales: np.ndarray
    counts: np.ndarray
    positions: np.ndarray
    values: np.ndarray
    position_parameter: int


def _unsigned_rice_bit_count(
    values: np.ndarray,
    parameter: int,
    position_bits: int,
) -> int:
    """Measure bounded Rice positions with a local fixed-width escape."""

    if values.ndim != 1 or values.dtype != np.uint64:
        raise TypeError("position gaps must be a one-dimensional uint64 array")
    quotient = np.right_shift(values, np.uint64(parameter))
    costs = np.where(
        quotient < RICE_ESCAPE_QUOTIENT,
        quotient + np.uint64(1 + parameter),
        np.uint64(RICE_ESCAPE_QUOTIENT + 1 + position_bits),
    )
    return int(np.sum(costs, dtype=np.uint64))


def _encode_unsigned_rice(
    values: np.ndarray,
    parameter: int,
    position_bits: int,
) -> tuple[bytes, int]:
    """Serialize unsigned gaps with bounded unary and fixed-width escape."""

    writer = _BitWriter()
    for item in values:
        value = int(item)
        quotient = value >> parameter
        if quotient < RICE_ESCAPE_QUOTIENT:
            for _ in range(quotient):
                writer.write_bit(1)
            writer.write_bit(0)
            writer.write_bits(value & ((1 << parameter) - 1), parameter)
        else:
            for _ in range(RICE_ESCAPE_QUOTIENT):
                writer.write_bit(1)
            writer.write_bit(0)
            writer.write_bits(value, position_bits)
    return writer.finish(), writer.bit_count


def _decode_unsigned_rice(
    payload: bytes,
    bit_count: int,
    count: int,
    parameter: int,
    position_bits: int,
    maximum_gap: int,
) -> np.ndarray:
    """Decode exactly ``count`` bounded unsigned coefficient gaps."""

    if not 0 <= parameter <= MAX_RICE_PARAMETER:
        raise ValueError("sparse position Rice parameter exceeds the bound")
    reader = _BitReader(payload, bit_count)
    output = np.empty(count, dtype=np.uint16)
    for index in range(count):
        quotient = 0
        while reader.read_bit():
            quotient += 1
            if quotient > RICE_ESCAPE_QUOTIENT:
                raise ValueError("sparse position unary prefix exceeds the bound")
        if quotient == RICE_ESCAPE_QUOTIENT:
            value = reader.read_bits(position_bits)
        else:
            value = (quotient << parameter) | reader.read_bits(parameter)
        if value > maximum_gap:
            raise ValueError("sparse coefficient gap exceeds the window")
        output[index] = value
    if reader.position != bit_count:
        raise ValueError("trailing sparse position bits")
    return output


def _checked_symbol_count(*dimensions: int) -> int:
    """Multiply positive dimensions under the research allocation ceiling."""

    count = 1
    for dimension in dimensions:
        if dimension <= 0 or count > MAX_SYMBOLS // dimension:
            raise ValueError("sparse lapped field exceeds the symbol bound")
        count *= dimension
    return count


def encode_sparse_lapped(
    scales: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    half_window: int,
) -> bytes:
    """Encode explicit sparse lapped fields without a general compressor."""

    scale_array = np.asarray(scales)
    position_array = np.asarray(positions)
    value_array = np.asarray(values)
    if (
        scale_array.dtype != np.uint8
        or scale_array.ndim != 3
        or position_array.dtype != np.uint16
        or position_array.ndim != 3
        or value_array.dtype != np.int8
        or value_array.shape != position_array.shape
        or scale_array.shape[:2] != position_array.shape[:2]
    ):
        raise TypeError("invalid sparse lapped field arrays")
    channels, frame_count, band_count = scale_array.shape
    coefficients_per_frame = position_array.shape[2]
    _checked_symbol_count(channels, frame_count, band_count)
    _checked_symbol_count(channels, frame_count, coefficients_per_frame)
    if half_window <= 0 or half_window > 65535:
        raise ValueError("sparse lapped half-window exceeds the field bound")
    if np.any(scale_array > 31):
        raise ValueError("sparse lapped scale exceeds the profile")
    if np.any(position_array >= half_window):
        raise ValueError("sparse coefficient position exceeds the window")
    if np.any(np.diff(position_array.astype(np.int64), axis=2) <= 0):
        raise ValueError("sparse coefficient positions must be strictly ordered")

    scale_delta = scale_array.astype(np.int64)
    if frame_count > 1:
        scale_delta[:, 1:, :] -= scale_array[:, :-1, :].astype(np.int64)
    scale_values = scale_delta.reshape(-1)
    scale_entropy, scale_parameter, scale_payload, scale_bits = _encode_entropy(
        scale_values
    )

    gaps = position_array.astype(np.int64)
    if coefficients_per_frame > 1:
        gaps[:, :, 1:] -= position_array[:, :, :-1].astype(np.int64) + 1
    gap_values = gaps.reshape(-1).astype(np.uint64)
    position_bits = max(1, (half_window - 1).bit_length())
    position_parameter = min(
        range(min(MAX_RICE_PARAMETER, position_bits) + 1),
        key=lambda item: (
            _unsigned_rice_bit_count(
                gap_values,
                item,
                position_bits,
            ),
            item,
        ),
    )
    position_payload, position_bit_count = _encode_unsigned_rice(
        gap_values,
        position_parameter,
        position_bits,
    )

    value_entropy, value_parameter, value_payload, value_bits = _encode_entropy(
        value_array.astype(np.int64).reshape(-1)
    )
    payload = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            scale_entropy,
            scale_parameter,
            position_parameter,
            value_entropy,
            value_parameter,
            0,
            frame_count,
            channels,
            band_count,
            coefficients_per_frame,
            scale_bits,
            position_bit_count,
            value_bits,
        )
        + scale_payload
        + position_payload
        + value_payload
    )
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("sparse lapped payload exceeds the byte bound")
    return payload


def decode_sparse_lapped(
    payload: bytes,
    *,
    half_window: int,
    expected_channels: int,
    expected_frames: int,
    expected_bands: int,
) -> SparseLappedFields:
    """Independently validate and decode the bounded sparse field payload."""

    if len(payload) < HEADER.size or len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid sparse lapped payload length")
    (
        magic,
        version,
        flags,
        scale_entropy,
        scale_parameter,
        position_parameter,
        value_entropy,
        value_parameter,
        reserved,
        frame_count,
        channels,
        band_count,
        coefficients_per_frame,
        scale_bits,
        position_bits,
        value_bits,
    ) = HEADER.unpack_from(payload)
    if magic != MAGIC or version != VERSION or flags != 0 or reserved != 0:
        raise ValueError("unsupported sparse lapped payload")
    if (
        channels != expected_channels
        or frame_count != expected_frames
        or band_count != expected_bands
        or not 1 <= coefficients_per_frame <= half_window
    ):
        raise ValueError("sparse lapped payload shape mismatch")
    scale_count = _checked_symbol_count(channels, frame_count, band_count)
    coefficient_count = _checked_symbol_count(
        channels,
        frame_count,
        coefficients_per_frame,
    )
    byte_counts = (
        (scale_bits + 7) // 8,
        (position_bits + 7) // 8,
        (value_bits + 7) // 8,
    )
    if sum(byte_counts) != len(payload) - HEADER.size:
        raise ValueError("sparse lapped entropy length mismatch")
    cursor = HEADER.size
    scale_payload = payload[cursor : cursor + byte_counts[0]]
    cursor += byte_counts[0]
    position_payload = payload[cursor : cursor + byte_counts[1]]
    cursor += byte_counts[1]
    value_payload = payload[cursor : cursor + byte_counts[2]]

    scale_delta = _decode_entropy(
        scale_payload,
        scale_bits,
        scale_count,
        scale_entropy,
        scale_parameter,
    ).reshape(channels, frame_count, band_count)
    scales64 = scale_delta.copy()
    for frame in range(1, frame_count):
        scales64[:, frame, :] += scales64[:, frame - 1, :]
    if np.any(scales64 < 0) or np.any(scales64 > 31):
        raise ValueError("decoded sparse scale exceeds the profile")
    scales = scales64.astype(np.uint8)

    gap_values = _decode_unsigned_rice(
        position_payload,
        position_bits,
        coefficient_count,
        position_parameter,
        max(1, (half_window - 1).bit_length()),
        half_window - 1,
    ).astype(np.int64).reshape(
        channels,
        frame_count,
        coefficients_per_frame,
    )
    positions64 = gap_values.copy()
    for index in range(1, coefficients_per_frame):
        positions64[:, :, index] += positions64[:, :, index - 1] + 1
    if np.any(positions64 >= half_window):
        raise ValueError("decoded sparse position exceeds the window")
    positions = positions64.astype(np.uint16)
    values = _decode_entropy(
        value_payload,
        value_bits,
        coefficient_count,
        value_entropy,
        value_parameter,
    )
    if np.any(values < -128) or np.any(values > 127):
        raise ValueError("decoded sparse value exceeds int8")
    values8 = values.astype(np.int8).reshape(
        channels,
        frame_count,
        coefficients_per_frame,
    )
    for array in (scales, positions, values8):
        array.flags.writeable = False
    return SparseLappedFields(
        scales,
        positions,
        values8,
        position_parameter,
    )


def encode_variable_sparse_lapped(
    scales: np.ndarray,
    counts: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    half_window: int,
) -> bytes:
    """Encode one bounded variable-density sparse coefficient trajectory."""

    scale_array = np.asarray(scales)
    count_array = np.asarray(counts)
    position_array = np.asarray(positions)
    value_array = np.asarray(values)
    if (
        scale_array.dtype != np.uint8
        or scale_array.ndim != 3
        or count_array.dtype != np.uint16
        or count_array.shape != scale_array.shape[:2]
        or position_array.dtype != np.uint16
        or position_array.ndim != 1
        or value_array.dtype != np.int8
        or value_array.shape != position_array.shape
    ):
        raise TypeError("invalid variable sparse lapped fields")
    channels, frame_count, band_count = scale_array.shape
    _checked_symbol_count(channels, frame_count, band_count)
    _checked_symbol_count(channels, frame_count)
    if (
        half_window <= 0
        or half_window > 65535
        or np.any(scale_array > 31)
        or np.any(count_array > half_window)
    ):
        raise ValueError("variable sparse lapped field exceeds the profile")
    total_coefficients = int(np.sum(count_array, dtype=np.uint64))
    if (
        total_coefficients != position_array.size
        or total_coefficients > MAX_SYMBOLS
        or np.any(position_array >= half_window)
    ):
        raise ValueError("variable sparse coefficient count mismatch")

    scale_delta = scale_array.astype(np.int64)
    count_delta = count_array.astype(np.int64)
    if frame_count > 1:
        scale_delta[:, 1:, :] -= scale_array[:, :-1, :].astype(np.int64)
        count_delta[:, 1:] -= count_array[:, :-1].astype(np.int64)
    scale_entropy, scale_parameter, scale_payload, scale_bits = _encode_entropy(
        scale_delta.reshape(-1)
    )
    count_entropy, count_parameter, count_payload, count_bits = _encode_entropy(
        count_delta.reshape(-1)
    )

    gap_values = np.empty(total_coefficients, dtype=np.uint64)
    cursor = 0
    for count in count_array.reshape(-1):
        frame_count_value = int(count)
        frame_positions = position_array[cursor : cursor + frame_count_value]
        if (
            frame_count_value > 1
            and np.any(np.diff(frame_positions.astype(np.int64)) <= 0)
        ):
            raise ValueError(
                "variable sparse positions must be strictly ordered"
            )
        if frame_count_value:
            gap_values[cursor] = frame_positions[0]
            if frame_count_value > 1:
                gap_values[cursor + 1 : cursor + frame_count_value] = (
                    frame_positions[1:].astype(np.int64)
                    - frame_positions[:-1].astype(np.int64)
                    - 1
                ).astype(np.uint64)
        cursor += frame_count_value
    position_width = max(1, (half_window - 1).bit_length())
    position_parameter = min(
        range(min(MAX_RICE_PARAMETER, position_width) + 1),
        key=lambda item: (
            _unsigned_rice_bit_count(
                gap_values,
                item,
                position_width,
            ),
            item,
        ),
    )
    position_payload, position_bits = _encode_unsigned_rice(
        gap_values,
        position_parameter,
        position_width,
    )
    value_entropy, value_parameter, value_payload, value_bits = _encode_entropy(
        value_array.astype(np.int64)
    )
    payload = (
        VARIABLE_HEADER.pack(
            VARIABLE_MAGIC,
            VERSION,
            0,
            scale_entropy,
            scale_parameter,
            count_entropy,
            count_parameter,
            position_parameter,
            value_entropy,
            value_parameter,
            0,
            frame_count,
            channels,
            band_count,
            total_coefficients,
            scale_bits,
            count_bits,
            position_bits,
            value_bits,
        )
        + scale_payload
        + count_payload
        + position_payload
        + value_payload
    )
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("variable sparse payload exceeds the byte bound")
    return payload


def decode_variable_sparse_lapped(
    payload: bytes,
    *,
    half_window: int,
    expected_channels: int,
    expected_frames: int,
    expected_bands: int,
) -> VariableSparseLappedFields:
    """Independently decode one bounded variable-density coefficient field."""

    if len(payload) < VARIABLE_HEADER.size or len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid variable sparse payload length")
    (
        magic,
        version,
        flags,
        scale_entropy,
        scale_parameter,
        count_entropy,
        count_parameter,
        position_parameter,
        value_entropy,
        value_parameter,
        reserved,
        frame_count,
        channels,
        band_count,
        total_coefficients,
        scale_bits,
        count_bits,
        position_bits,
        value_bits,
    ) = VARIABLE_HEADER.unpack_from(payload)
    if (
        magic != VARIABLE_MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
        or channels != expected_channels
        or frame_count != expected_frames
        or band_count != expected_bands
        or total_coefficients > MAX_SYMBOLS
    ):
        raise ValueError("variable sparse lapped header mismatch")
    scale_count = _checked_symbol_count(channels, frame_count, band_count)
    frame_symbol_count = _checked_symbol_count(channels, frame_count)
    bit_counts = (scale_bits, count_bits, position_bits, value_bits)
    byte_counts = tuple((item + 7) // 8 for item in bit_counts)
    if sum(byte_counts) != len(payload) - VARIABLE_HEADER.size:
        raise ValueError("variable sparse entropy length mismatch")
    cursor = VARIABLE_HEADER.size
    fields = []
    for byte_count in byte_counts:
        fields.append(payload[cursor : cursor + byte_count])
        cursor += byte_count

    scale_delta = _decode_entropy(
        fields[0],
        scale_bits,
        scale_count,
        scale_entropy,
        scale_parameter,
    ).reshape(channels, frame_count, band_count)
    scales64 = scale_delta.copy()
    for frame in range(1, frame_count):
        scales64[:, frame, :] += scales64[:, frame - 1, :]
    if np.any(scales64 < 0) or np.any(scales64 > 31):
        raise ValueError("decoded variable sparse scale exceeds the profile")
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
        raise ValueError("decoded variable sparse count exceeds the profile")
    counts = counts64.astype(np.uint16)

    gaps = _decode_unsigned_rice(
        fields[2],
        position_bits,
        total_coefficients,
        position_parameter,
        max(1, (half_window - 1).bit_length()),
        half_window - 1,
    )
    positions = np.empty(total_coefficients, dtype=np.uint16)
    cursor = 0
    for count in counts.reshape(-1):
        previous = -1
        for _ in range(int(count)):
            position = previous + 1 + int(gaps[cursor])
            if position >= half_window:
                raise ValueError(
                    "decoded variable sparse position exceeds the window"
                )
            positions[cursor] = position
            previous = position
            cursor += 1
    values = _decode_entropy(
        fields[3],
        value_bits,
        total_coefficients,
        value_entropy,
        value_parameter,
    )
    if np.any(values < -128) or np.any(values > 127):
        raise ValueError("decoded variable sparse value exceeds int8")
    values8 = values.astype(np.int8)
    for array in (scales, counts, positions, values8):
        array.flags.writeable = False
    return VariableSparseLappedFields(
        scales,
        counts,
        positions,
        values8,
        position_parameter,
    )
