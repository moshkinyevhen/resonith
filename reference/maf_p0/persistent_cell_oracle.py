"""Independent scalar oracle for the bounded SFC2 research envelope.

The product decoder remains native.  This module deliberately implements only
the fixed integer contract needed to falsify native/parser drift in R-268.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np


HEADER = struct.Struct("<4sBBHIIQIIIIII")
CELL = struct.Struct("<HHIIHHIIhh10h")
EVENT = struct.Struct("<HHIIIhhI")
REFRESH = struct.Struct("<HHII10h")
SEED_MULTIPLIER = 0x9E3779B97F4A7C15
MASK64 = (1 << 64) - 1


@dataclass(frozen=True)
class CellLaw:
    cell_id: int
    start: int
    duration: int
    fade_in: int
    fade_out: int
    phase_q32: int
    step_q32: int
    pulse_gain_q15: int
    noise_gain_q15: int
    reflection_q15: tuple[int, ...]


@dataclass(frozen=True)
class ExcitationLaw:
    cell_id: int
    flags: int
    offset: int
    duration: int
    end_step_q32: int
    end_pulse_q15: int
    end_noise_q15: int


def pack_stream(
    sample_count: int,
    seed: int,
    cells: tuple[CellLaw, ...],
    events: tuple[ExcitationLaw, ...],
    refreshes: tuple[tuple[int, int, int, tuple[int, ...]], ...] = (),
    truth: bytes = b"",
) -> bytes:
    """Serialize one canonical fixed-record SFC2 stream."""

    header = HEADER.pack(
        b"SFC2", 2, 0, 0, 16000, sample_count, seed & MASK64,
        len(cells), len(events), len(refreshes), len(truth), HEADER.size, 0,
    )
    cell_bytes = b"".join(
        CELL.pack(
            c.cell_id, 0, c.start, c.duration, c.fade_in, c.fade_out,
            c.phase_q32, c.step_q32, c.pulse_gain_q15, c.noise_gain_q15,
            *c.reflection_q15,
        )
        for c in sorted(cells, key=lambda c: (c.start, c.cell_id))
    )
    by_id = {c.cell_id: c for c in cells}
    ordered_events = sorted(
        events, key=lambda e: (by_id[e.cell_id].start + e.offset, e.cell_id, e.offset)
    )
    event_bytes = b"".join(
        EVENT.pack(
            e.cell_id, e.flags, e.offset, e.duration, e.end_step_q32,
            e.end_pulse_q15, e.end_noise_q15, 0,
        )
        for e in ordered_events
    )
    ordered_refreshes = sorted(
        refreshes, key=lambda r: (by_id[r[0]].start + r[1], r[0], r[1])
    )
    refresh_bytes = b"".join(
        REFRESH.pack(cell_id, 0, offset, duration, *reflection)
        for cell_id, offset, duration, reflection in ordered_refreshes
    )
    return header + cell_bytes + event_bytes + refresh_bytes + truth


def _round_shift_q15(value: int) -> int:
    quotient = abs(value) // 32768
    remainder = abs(value) % 32768
    if remainder >= 16384:
        quotient += 1
    return -quotient if value < 0 else quotient


def _sat16(value: int) -> int:
    return max(-32768, min(32767, value))


def _scale(sample: int, gain: int) -> int:
    return _sat16(_round_shift_q15(sample * gain))


def _round_divide(value: int, denominator: int) -> int:
    quotient = (abs(value) + denominator // 2) // denominator
    return -quotient if value < 0 else quotient


def _phase_advance(length: int, start: int, end: int) -> int:
    curve = (end - start) * length * (length - 1)
    return (length * start + _round_divide(curve, 2 * length)) & 0xFFFFFFFF


def _phase_at(origin: int, start: int, end: int, local: int, length: int) -> int:
    curve = (end - start) * local * (local - 1)
    return (origin + local * start + _round_divide(curve, 2 * length)) & 0xFFFFFFFF


def _impulse_sample(phase: int) -> int:
    position = phase * 64
    left = position >> 32
    right = 0 if left == 63 else left + 1
    fraction = (position >> 16) & 0xFFFF
    weighted = (32767 if left == 0 else 0) * (65536 - fraction)
    weighted += (32767 if right == 0 else 0) * fraction + 32768
    return weighted // 65536


def _lpc(reflection: tuple[int, ...]) -> list[int]:
    current = [0] * len(reflection)
    for stage, coefficient in enumerate(reflection):
        nxt = [0] * len(reflection)
        for index in range(stage):
            nxt[index] = current[index] + _round_shift_q15(
                coefficient * current[stage - 1 - index]
            )
        nxt[stage] = coefficient
        current = nxt
    return current


def _fade(cell: CellLaw, absolute: int) -> int:
    if cell.fade_in and absolute < cell.start + cell.fade_in:
        p, d = absolute - cell.start, cell.fade_in
        return (32767 * p + (d - 1) // 2) // (d - 1)
    if cell.fade_out and absolute >= cell.start + cell.duration - cell.fade_out:
        p, d = absolute - (cell.start + cell.duration - cell.fade_out), cell.fade_out
        return 32767 - (32767 * p + (d - 1) // 2) // (d - 1)
    return 32767


def scalar_render(payload: bytes) -> np.ndarray:
    """Render deterministic Cell PCM without calling the native library."""

    fields = HEADER.unpack_from(payload)
    if fields[:6] != (b"SFC2", 2, 0, 0, 16000, fields[5]) or fields[-2:] != (48, 0):
        raise ValueError("invalid SFC2 header")
    sample_count, seed, cell_count, event_count, refresh_count, truth_bytes = fields[5:11]
    offset = HEADER.size
    cells = []
    for _ in range(cell_count):
        record = CELL.unpack_from(payload, offset); offset += CELL.size
        cells.append(CellLaw(record[0], record[2], record[3], record[4], record[5],
            record[6], record[7], record[8], record[9], tuple(record[10:])))
    events: dict[int, list[ExcitationLaw]] = {c.cell_id: [] for c in cells}
    for _ in range(event_count):
        record = EVENT.unpack_from(payload, offset); offset += EVENT.size
        events[record[0]].append(ExcitationLaw(record[0], record[1], record[2],
            record[3], record[4], record[5], record[6]))
    offset += refresh_count * REFRESH.size
    if offset + truth_bytes != len(payload):
        raise ValueError("SFC2 size mismatch")
    accumulator = np.zeros(sample_count, dtype=np.int64)
    for cell in cells:
        if cell.noise_gain_q15 or any(e.end_noise_q15 for e in events[cell.cell_id]):
            raise NotImplementedError("R-268 scalar parity currently exercises deterministic excitation")
        coefficients = _lpc(cell.reflection_q15)
        history = [0] * len(coefficients)
        phase = cell.phase_q32
        start_step, start_gain = cell.step_q32, cell.pulse_gain_q15
        rendered = np.zeros(cell.duration, dtype=np.int16)
        for event in events[cell.cell_id]:
            for local in range(event.duration):
                position = event.offset + local
                step = start_step
                if event.flags & 1:
                    step = start_step + _round_divide(
                        (event.end_step_q32 - start_step) * local, event.duration
                    )
                gain = start_gain
                if event.flags & 2:
                    control = local - local % 80
                    gain = start_gain + _round_divide(
                        (event.end_pulse_q15 - start_gain) * control, event.duration
                    )
                excitation = _scale(_impulse_sample(
                    _phase_at(phase, start_step, event.end_step_q32 if event.flags & 1 else start_step,
                              local, event.duration)), gain)
                excitation = _scale(excitation, 32767)
                value = _sat16(excitation - _round_shift_q15(
                    sum(a * h for a, h in zip(coefficients, history, strict=True))
                ))
                history[1:] = history[:-1]
                history[0] = value
                rendered[position] = value
            phase = (phase + _phase_advance(
                event.duration, start_step,
                event.end_step_q32 if event.flags & 1 else start_step,
            )) & 0xFFFFFFFF
            start_step, start_gain = event.end_step_q32, event.end_pulse_q15
        start, stop = cell.start, cell.start + cell.duration
        for index, value in enumerate(rendered):
            accumulator[start + index] += int(value) * _fade(cell, start + index)
    model = np.asarray([_sat16(_round_shift_q15(int(value))) for value in accumulator], dtype=np.int16)
    model.flags.writeable = False
    return model
