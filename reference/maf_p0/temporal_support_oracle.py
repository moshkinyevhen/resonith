"""Bounded temporal support-state entropy oracle for selected lapped fields."""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np

from .residual import _decode_entropy, _encode_entropy
from .sparse_entropy import (
    MAX_PAYLOAD_BYTES,
    MAX_RICE_PARAMETER,
    MAX_SYMBOLS,
    _checked_symbol_count,
    _decode_unsigned_rice,
    _encode_unsigned_rice,
    _unsigned_rice_bit_count,
)


MAGIC = b"LST1"
VERSION = 1
HEADER = struct.Struct("<4s10BIHH6I")


@dataclass(frozen=True)
class TemporalSupportFields:
    """Exact selected fields reconstructed from one reset support trajectory."""

    scales: np.ndarray
    coefficients: np.ndarray
    position_parameter: int


def _validated_fields(
    scales: np.ndarray,
    coefficients: np.ndarray,
    half_window: int,
) -> tuple[np.ndarray, np.ndarray, int, int, int]:
    scale_grid = np.asarray(scales)
    coefficient_grid = np.asarray(coefficients)
    if (
        scale_grid.dtype != np.uint8
        or scale_grid.ndim != 3
        or coefficient_grid.dtype != np.int8
        or coefficient_grid.ndim != 3
        or scale_grid.shape[:2] != coefficient_grid.shape[:2]
        or coefficient_grid.shape[2] != half_window
    ):
        raise TypeError("invalid temporal support fields")
    channels, frame_count, band_count = scale_grid.shape
    _checked_symbol_count(channels, frame_count, band_count)
    _checked_symbol_count(channels, frame_count, half_window)
    if (
        half_window <= 0
        or half_window > 65535
        or np.any(scale_grid > 31)
    ):
        raise ValueError("temporal support field exceeds the profile")
    return scale_grid, coefficient_grid, channels, frame_count, band_count


def encode_temporal_support_lapped(
    scales: np.ndarray,
    coefficients: np.ndarray,
    *,
    half_window: int,
) -> bytes:
    """Encode sparse positions as bounded changes to a reset support field."""

    (
        scale_grid,
        coefficient_grid,
        channels,
        frame_count,
        band_count,
    ) = _validated_fields(scales, coefficients, half_window)

    toggle_counts = np.empty((channels, frame_count), dtype=np.uint16)
    toggle_parts: list[np.ndarray] = []
    value_parts: list[np.ndarray] = []
    for channel in range(channels):
        previous = np.zeros(half_window, dtype=np.bool_)
        for frame in range(frame_count):
            current = coefficient_grid[channel, frame] != 0
            toggles = np.flatnonzero(previous ^ current).astype(np.uint16)
            values = coefficient_grid[channel, frame, current].astype(np.int8)
            toggle_counts[channel, frame] = toggles.size
            toggle_parts.append(toggles)
            value_parts.append(values)
            previous = current
    toggle_positions = np.concatenate(toggle_parts)
    values = np.concatenate(value_parts)
    total_toggles = int(toggle_positions.size)
    total_values = int(values.size)
    if total_toggles > MAX_SYMBOLS or total_values > MAX_SYMBOLS:
        raise ValueError("temporal support field exceeds the symbol bound")

    scale_delta = scale_grid.astype(np.int64)
    toggle_count_delta = toggle_counts.astype(np.int64)
    if frame_count > 1:
        scale_delta[:, 1:, :] -= scale_grid[:, :-1, :].astype(np.int64)
        toggle_count_delta[:, 1:] -= toggle_counts[:, :-1].astype(np.int64)
    scale_entropy, scale_parameter, scale_payload, scale_bits = _encode_entropy(
        scale_delta.reshape(-1)
    )
    (
        toggle_count_entropy,
        toggle_count_parameter,
        toggle_count_payload,
        toggle_count_bits,
    ) = _encode_entropy(toggle_count_delta.reshape(-1))

    toggle_gaps = np.empty(total_toggles, dtype=np.uint64)
    cursor = 0
    for count in toggle_counts.reshape(-1):
        count_value = int(count)
        positions = toggle_positions[cursor : cursor + count_value]
        if count_value:
            toggle_gaps[cursor] = positions[0]
            if count_value > 1:
                toggle_gaps[cursor + 1 : cursor + count_value] = (
                    positions[1:].astype(np.int64)
                    - positions[:-1].astype(np.int64)
                    - 1
                ).astype(np.uint64)
        cursor += count_value
    position_width = max(1, (half_window - 1).bit_length())
    position_parameter = min(
        range(min(MAX_RICE_PARAMETER, position_width) + 1),
        key=lambda item: (
            _unsigned_rice_bit_count(toggle_gaps, item, position_width),
            item,
        ),
    )
    position_payload, position_bits = _encode_unsigned_rice(
        toggle_gaps,
        position_parameter,
        position_width,
    )
    value_entropy, value_parameter, value_payload, value_bits = _encode_entropy(
        values.astype(np.int64)
    )
    payload = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            scale_entropy,
            scale_parameter,
            toggle_count_entropy,
            toggle_count_parameter,
            position_parameter,
            value_entropy,
            value_parameter,
            0,
            frame_count,
            channels,
            band_count,
            total_toggles,
            total_values,
            scale_bits,
            toggle_count_bits,
            position_bits,
            value_bits,
        )
        + scale_payload
        + toggle_count_payload
        + position_payload
        + value_payload
    )
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("temporal support payload exceeds the byte bound")
    return payload


def decode_temporal_support_lapped(
    payload: bytes,
    *,
    half_window: int,
    expected_channels: int,
    expected_frames: int,
    expected_bands: int,
) -> TemporalSupportFields:
    """Decode one independent support trajectory with strict exact framing."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < HEADER.size
        or len(payload) > MAX_PAYLOAD_BYTES
    ):
        raise ValueError("invalid temporal support payload length")
    (
        magic,
        version,
        flags,
        scale_entropy,
        scale_parameter,
        toggle_count_entropy,
        toggle_count_parameter,
        position_parameter,
        value_entropy,
        value_parameter,
        reserved,
        frame_count,
        channels,
        band_count,
        total_toggles,
        total_values,
        scale_bits,
        toggle_count_bits,
        position_bits,
        value_bits,
    ) = HEADER.unpack_from(payload)
    if (
        magic != MAGIC
        or version != VERSION
        or flags != 0
        or reserved != 0
        or channels != expected_channels
        or frame_count != expected_frames
        or band_count != expected_bands
        or total_toggles > MAX_SYMBOLS
        or total_values > MAX_SYMBOLS
        or half_window <= 0
        or half_window > 65535
    ):
        raise ValueError("temporal support header mismatch")
    scale_count = _checked_symbol_count(channels, frame_count, band_count)
    state_count = _checked_symbol_count(channels, frame_count)
    bit_counts = (scale_bits, toggle_count_bits, position_bits, value_bits)
    byte_counts = tuple((int(bits) + 7) // 8 for bits in bit_counts)
    if sum(byte_counts) != len(payload) - HEADER.size:
        raise ValueError("temporal support entropy length mismatch")
    cursor = HEADER.size
    fields: list[bytes] = []
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
        raise ValueError("decoded temporal scale exceeds the profile")
    scales = scales64.astype(np.uint8)

    count_delta = _decode_entropy(
        fields[1],
        toggle_count_bits,
        state_count,
        toggle_count_entropy,
        toggle_count_parameter,
    ).reshape(channels, frame_count)
    counts64 = count_delta.copy()
    for frame in range(1, frame_count):
        counts64[:, frame] += counts64[:, frame - 1]
    if (
        np.any(counts64 < 0)
        or np.any(counts64 > half_window)
        or int(np.sum(counts64, dtype=np.int64)) != total_toggles
    ):
        raise ValueError("decoded temporal toggle count exceeds the profile")
    toggle_counts = counts64.astype(np.uint16)
    gaps = _decode_unsigned_rice(
        fields[2],
        position_bits,
        total_toggles,
        position_parameter,
        max(1, (half_window - 1).bit_length()),
        half_window - 1,
    )
    values64 = _decode_entropy(
        fields[3],
        value_bits,
        total_values,
        value_entropy,
        value_parameter,
    )
    if np.any(values64 < -128) or np.any(values64 > 127):
        raise ValueError("decoded temporal value exceeds int8")
    values = values64.astype(np.int8)

    coefficients = np.zeros(
        (channels, frame_count, half_window),
        dtype=np.int8,
    )
    toggle_cursor = 0
    value_cursor = 0
    for channel in range(channels):
        support = np.zeros(half_window, dtype=np.bool_)
        for frame in range(frame_count):
            previous_position = -1
            for _ in range(int(toggle_counts[channel, frame])):
                position = (
                    previous_position + 1 + int(gaps[toggle_cursor])
                )
                if position >= half_window:
                    raise ValueError("decoded temporal toggle exceeds the window")
                support[position] = not support[position]
                previous_position = position
                toggle_cursor += 1
            active_count = int(np.count_nonzero(support))
            if value_cursor + active_count > total_values:
                raise ValueError("temporal support value count mismatch")
            coefficients[channel, frame, support] = values[
                value_cursor : value_cursor + active_count
            ]
            value_cursor += active_count
    if toggle_cursor != total_toggles or value_cursor != total_values:
        raise ValueError("temporal support field count mismatch")
    for array in (scales, coefficients):
        array.flags.writeable = False
    return TemporalSupportFields(scales, coefficients, position_parameter)
