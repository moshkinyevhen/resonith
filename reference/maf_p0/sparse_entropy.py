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
VERSION = 1
HEADER = struct.Struct("<4sBBBBBBBBIHHHIII")
MAX_SYMBOLS = 64 << 20
MAX_PAYLOAD_BYTES = 512 << 20


@dataclass(frozen=True)
class SparseLappedFields:
    """Exact decoded scale, position, and signed-value fields."""

    scales: np.ndarray
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
