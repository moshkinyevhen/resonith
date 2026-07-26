"""Bounded transient detection and reversible integer-lifting transport."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, order=True)
class TransientEvent:
    """Half-open sample interval owned by the transient path."""

    start: int
    length: int

    @property
    def end(self) -> int:
        return self.start + self.length


@dataclass(frozen=True)
class TransientPacket:
    """Flat transport representation for independently bounded events."""

    event_table: np.ndarray
    quantized_coefficients: np.ndarray
    quantization_step: int


def _next_power_of_two(value: int) -> int:
    if value <= 0:
        raise ValueError("transform length must be positive")
    return 1 << (value - 1).bit_length()


def _validate_events(events: list[TransientEvent], sample_count: int) -> None:
    previous_end = 0
    for event in sorted(events):
        if event.start < previous_end:
            raise ValueError("transient events overlap")
        if event.start < 0 or event.length <= 0 or event.end > sample_count:
            raise ValueError("transient event is outside the signal")
        previous_end = event.end


def detect_transients(
    samples: np.ndarray,
    *,
    window_size: int = 256,
    pre_roll: int = 32,
    absolute_difference_floor: int = 2048,
    robust_multiplier: float = 10.0,
) -> list[TransientEvent]:
    """Detect sparse attacks without creating a decoder-side classifier.

    Detection is encoder-only. A declared event remains objective because its
    bounded transform coefficients and any remaining Truth residual are coded.
    """

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if samples.size < 2:
        return []
    if window_size < 16 or window_size > 4096:
        raise ValueError("window_size is outside the P1 bound")
    if pre_roll < 0 or pre_roll >= window_size:
        raise ValueError("pre_roll is outside the transient window")

    difference = np.abs(np.diff(samples.astype(np.int64)))
    median = float(np.median(difference))
    deviation = float(np.median(np.abs(difference - median)))
    threshold = max(
        float(absolute_difference_floor),
        median + robust_multiplier * max(deviation, 1.0),
    )
    candidates = np.flatnonzero(difference >= threshold) + 1
    if candidates.size == 0:
        return []

    # Highest-energy attacks claim their bounded support first. This produces
    # deterministic non-overlapping events without decoder-side heuristics.
    ranked = sorted(
        (int(index) for index in candidates),
        key=lambda index: (-int(difference[index - 1]), index),
    )
    selected: list[TransientEvent] = []
    for peak in ranked:
        start = max(0, peak - pre_roll)
        end = min(samples.size, start + window_size)
        start = max(0, end - window_size)
        candidate = TransientEvent(start, end - start)
        if any(candidate.start < item.end and item.start < candidate.end for item in selected):
            continue
        selected.append(candidate)
    selected.sort()
    return selected


def haar_lift_forward(samples: np.ndarray) -> np.ndarray:
    """Reversible Haar lifting with floor division for negative differences."""

    source = np.asarray(samples)
    if source.ndim != 1 or source.size == 0:
        raise ValueError("Haar input must be a non-empty vector")
    if source.size & (source.size - 1):
        raise ValueError("Haar input length must be a power of two")

    output = source.astype(np.int64, copy=True)
    scratch = np.empty_like(output)
    active = output.size
    while active > 1:
        half = active // 2
        even = output[:active:2]
        odd = output[1:active:2]
        difference = odd - even
        low = even + np.floor_divide(difference, 2)
        scratch[:half] = low
        scratch[half:active] = difference
        output[:active] = scratch[:active]
        active = half
    return output


def haar_lift_inverse(coefficients: np.ndarray) -> np.ndarray:
    """Exact inverse of :func:`haar_lift_forward`."""

    source = np.asarray(coefficients)
    if source.ndim != 1 or source.size == 0:
        raise ValueError("Haar coefficients must be a non-empty vector")
    if source.size & (source.size - 1):
        raise ValueError("Haar coefficient count must be a power of two")

    output = source.astype(np.int64, copy=True)
    scratch = np.empty_like(output)
    active = 1
    while active < output.size:
        low = output[:active]
        difference = output[active : 2 * active]
        even = low - np.floor_divide(difference, 2)
        odd = difference + even
        scratch[: 2 * active : 2] = even
        scratch[1 : 2 * active : 2] = odd
        output[: 2 * active] = scratch[: 2 * active]
        active *= 2
    return output


def _quantize_signed(values: np.ndarray, step: int) -> np.ndarray:
    if step < 1:
        raise ValueError("transient quantization step must be positive")
    signed = values.astype(np.int64)
    magnitude = np.abs(signed)
    quantized = (magnitude + step // 2) // step
    return np.where(signed < 0, -quantized, quantized).astype(np.int64)


def encode_transient_events(
    samples: np.ndarray,
    events: list[TransientEvent],
    *,
    quantization_step: int = 1,
) -> TransientPacket:
    """Encode independent event windows into a flat bounded coefficient bank."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    ordered = sorted(events)
    _validate_events(ordered, samples.size)

    rows: list[tuple[int, int, int, int]] = []
    coefficient_groups: list[np.ndarray] = []
    offset = 0
    for event in ordered:
        transform_length = _next_power_of_two(event.length)
        padded = np.zeros(transform_length, dtype=np.int64)
        padded[: event.length] = samples[event.start : event.end]
        quantized = _quantize_signed(
            haar_lift_forward(padded),
            quantization_step,
        )
        rows.append((event.start, event.length, offset, transform_length))
        coefficient_groups.append(quantized)
        offset += transform_length

    table = (
        np.asarray(rows, dtype=np.int64).reshape(-1, 4)
        if rows
        else np.empty((0, 4), dtype=np.int64)
    )
    coefficients64 = (
        np.concatenate(coefficient_groups)
        if coefficient_groups
        else np.empty(0, dtype=np.int64)
    )
    minimum = int(coefficients64.min()) if coefficients64.size else 0
    maximum = int(coefficients64.max()) if coefficients64.size else 0
    dtype = np.int16 if -32768 <= minimum and maximum <= 32767 else np.int32
    return TransientPacket(
        event_table=table,
        quantized_coefficients=coefficients64.astype(dtype),
        quantization_step=quantization_step,
    )


def decode_transient_events(
    packet: TransientPacket,
    sample_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Decode events and return `(prediction, coverage)` for exact replacement."""

    if sample_count < 0:
        raise ValueError("sample_count must be non-negative")
    table = np.asarray(packet.event_table)
    coefficients = np.asarray(packet.quantized_coefficients)
    if table.ndim != 2 or table.shape[1:] != (4,):
        raise ValueError("transient event table must have four columns")
    if coefficients.ndim != 1:
        raise ValueError("transient coefficients must be one-dimensional")
    if not np.issubdtype(table.dtype, np.integer):
        raise ValueError("transient event table must contain integers")
    if not np.issubdtype(coefficients.dtype, np.signedinteger):
        raise ValueError("transient coefficients must be signed integers")
    if packet.quantization_step < 1:
        raise ValueError("invalid transient quantization step")

    events = [
        TransientEvent(int(row[0]), int(row[1]))
        for row in table
    ]
    _validate_events(events, sample_count)
    prediction = np.zeros(sample_count, dtype=np.int16)
    coverage = np.zeros(sample_count, dtype=np.bool_)

    expected_offset = 0
    for row, event in zip(table, events, strict=True):
        offset = int(row[2])
        transform_length = int(row[3])
        if offset != expected_offset:
            raise ValueError("transient coefficient offsets are not canonical")
        if transform_length < event.length or transform_length & (transform_length - 1):
            raise ValueError("invalid transient transform length")
        end = offset + transform_length
        if end > coefficients.size:
            raise ValueError("truncated transient coefficient bank")

        dequantized = (
            coefficients[offset:end].astype(np.int64)
            * int(packet.quantization_step)
        )
        restored = haar_lift_inverse(dequantized)[: event.length]
        prediction[event.start : event.end] = np.clip(
            restored,
            -32768,
            32767,
        ).astype(np.int16)
        coverage[event.start : event.end] = True
        expected_offset = end
    if expected_offset != coefficients.size:
        raise ValueError("trailing transient coefficients")
    return prediction, coverage
