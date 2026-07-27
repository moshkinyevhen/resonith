"""R-106 continuous, nonrecursive harmonic trajectory oracle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .analytic_oracle import SINE_ROM
from .harmonic_basis_oracle import (
    MAX_HARMONICS,
    MAX_SAMPLE_COUNT,
    MAX_BLOCK_COUNT,
    _pack_coefficient_pairs,
    _pitch_increment,
    _round_shift,
    _unpack_coefficient_pairs,
)
from .lapped_oracle import (
    LappedAnalysis,
    analyze_lapped_source,
    decode_lapped_stream,
    encode_lapped_analysis,
)
from .periodic import PHASE_SCALE, PhaseTrajectory, phase_values_q32


MAGIC = b"CHT1"
FIELD_MAGIC = b"CHF1"
VERSION = 1
HEADER = struct.Struct("<4sBIHIBI")
FIELD_HEADER = struct.Struct("<4sBIHIBBI")
CHANNEL_HEADER = struct.Struct("<BH")
RUN_HEADER = struct.Struct("<HH")
LAG = struct.Struct("<H")
CHECKSUM = struct.Struct("<I")
MIN_HARMONIC_COEFFICIENT = -2048
MAX_HARMONIC_COEFFICIENT = 2047
ROM_INDEX_SHIFT = 22
ROM_QUARTER = len(SINE_ROM) // 4
MAX_RUN_STATES = 16


@dataclass(frozen=True)
class TrajectoryKnot:
    """One bounded pitch and complex-amplitude knot."""

    lag: int
    coefficients: np.ndarray


@dataclass(frozen=True)
class HarmonicRun:
    """A contiguous voiced lifetime with continuous absolute phase."""

    start_state: int
    knots: tuple[TrajectoryKnot, ...]


@dataclass(frozen=True)
class ContinuousHarmonicAnalysis:
    """Integer trajectory model and lapped analysis of its Innovation."""

    sample_rate: int
    source: np.ndarray
    state_size: int
    harmonic_count: int
    runs: tuple[HarmonicRun, ...]
    prediction: np.ndarray
    innovation: np.ndarray
    lapped_analysis: LappedAnalysis


@dataclass(frozen=True)
class ContinuousHarmonicResult:
    """Complete prospective stream and independently decoded PCM."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


@dataclass(frozen=True)
class ContinuousHarmonicFieldAnalysis:
    """Per-channel trajectory banks with one joint Innovation analysis."""

    sample_rate: int
    source: np.ndarray
    state_size: int
    harmonic_count: int
    channel_runs: tuple[tuple[HarmonicRun, ...], ...]
    prediction: np.ndarray
    innovation: np.ndarray
    lapped_analysis: LappedAnalysis


@dataclass(frozen=True)
class ContinuousHarmonicFieldResult:
    """Complete multichannel field stream and decoded PCM."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _rounded_ratio(numerator: np.ndarray, denominator: int) -> np.ndarray:
    """Round signed integer ratios to nearest, with ties away from zero."""

    if denominator <= 0:
        raise ValueError("trajectory interpolation span must be positive")
    magnitude = np.abs(numerator)
    rounded = (magnitude + denominator // 2) // denominator
    return np.where(numerator < 0, -rounded, rounded)


def _rom_values(phases_q32: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic Q15 sine and cosine for Q32 phases."""

    indices = phases_q32.astype(np.uint64) >> np.uint64(ROM_INDEX_SHIFT)
    sine = SINE_ROM[indices.astype(np.int64)].astype(np.int64)
    cosine = SINE_ROM[
        (indices.astype(np.int64) + ROM_QUARTER) % len(SINE_ROM)
    ].astype(np.int64)
    return sine, cosine


def _run_positions(
    sample_count: int,
    state_size: int,
    start_state: int,
    state_count: int,
) -> np.ndarray:
    stream_start = start_state * state_size
    positions = [0]
    for state_offset in range(state_count):
        absolute_stop = min(
            sample_count,
            (start_state + state_offset + 1) * state_size,
        )
        positions.append(absolute_stop - stream_start)
    return np.asarray(positions, dtype=np.int64)


def _run_trajectory(
    sample_count: int,
    state_size: int,
    run: HarmonicRun,
) -> PhaseTrajectory:
    positions = _run_positions(
        sample_count,
        state_size,
        run.start_state,
        len(run.knots),
    )
    increments = [
        max(1, min(0xFFFF_FFFF, int(round(PHASE_SCALE / knot.lag))))
        for knot in run.knots
    ]
    increments.append(increments[-1])
    return PhaseTrajectory(
        positions,
        np.asarray(increments, dtype=np.uint32),
        phase_origin_q32=0,
    )


def _interpolated_coefficients(
    start: np.ndarray,
    end: np.ndarray,
    sample_count: int,
) -> np.ndarray:
    local = np.arange(sample_count, dtype=np.int64)
    delta = end.astype(np.int64) - start.astype(np.int64)
    numerator = local[:, None, None] * delta[None, :, :]
    return (
        start.astype(np.int64)[None, :, :]
        + _rounded_ratio(numerator, sample_count)
    )


def _render_run(
    sample_count: int,
    state_size: int,
    run: HarmonicRun,
) -> np.ndarray:
    """Render a run solely from its absolute knots and frozen ROM."""

    trajectory = _run_trajectory(
        sample_count,
        state_size,
        run,
    )
    phase = phase_values_q32(trajectory)
    positions = trajectory.positions
    output = np.empty(phase.size, dtype=np.int16)
    for state_offset, knot in enumerate(run.knots):
        start = int(positions[state_offset])
        stop = int(positions[state_offset + 1])
        length = stop - start
        next_coefficients = (
            run.knots[state_offset + 1].coefficients
            if state_offset + 1 < len(run.knots)
            else knot.coefficients
        )
        amplitudes = _interpolated_coefficients(
            knot.coefficients,
            next_coefficients,
            length,
        )
        accumulator = np.zeros(length, dtype=np.int64)
        state_phase = phase[start:stop].astype(np.uint64)
        for harmonic in range(1, amplitudes.shape[1] + 1):
            harmonic_phase = (
                state_phase * np.uint64(harmonic)
            ) & np.uint64(0xFFFF_FFFF)
            sine, cosine = _rom_values(harmonic_phase)
            accumulator += (
                amplitudes[:, harmonic - 1, 0] * sine
                + amplitudes[:, harmonic - 1, 1] * cosine
            )
        rounded = np.fromiter(
            (_round_shift(int(value), 15) for value in accumulator),
            dtype=np.int64,
            count=length,
        )
        output[start:stop] = np.clip(
            rounded,
            -32768,
            32767,
        ).astype(np.int16)
    return output


def _active_state_runs(increments: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(increments):
        if increments[index] == 0:
            index += 1
            continue
        start = index
        while index < len(increments) and increments[index] != 0:
            index += 1
        while start < index:
            stop = min(index, start + MAX_RUN_STATES)
            runs.append((start, stop))
            start = stop
    return runs


def _fit_run(
    samples: np.ndarray,
    sample_count: int,
    sample_rate: int,
    state_size: int,
    start_state: int,
    increments: list[int],
    harmonic_count: int,
) -> tuple[HarmonicRun, np.ndarray]:
    """Jointly fit amplitude knots under one continuous phase trajectory."""

    zero_coefficients = np.zeros(
        (harmonic_count, 2),
        dtype=np.int16,
    )
    provisional = HarmonicRun(
        start_state,
        tuple(
            TrajectoryKnot(
                max(1, int(round(PHASE_SCALE / increment))),
                zero_coefficients,
            )
            for increment in increments
        ),
    )
    trajectory = _run_trajectory(
        sample_count,
        state_size,
        provisional,
    )
    phase = phase_values_q32(trajectory)
    positions = trajectory.positions
    knot_count = len(increments)
    design = np.zeros(
        (samples.size, knot_count * harmonic_count * 2),
        dtype=np.float64,
    )
    for state_offset in range(knot_count):
        start = int(positions[state_offset])
        stop = int(positions[state_offset + 1])
        length = stop - start
        local = np.arange(length, dtype=np.float64)
        current_weight = 1.0 - local / length
        next_weight = local / length
        state_phase = phase[start:stop].astype(np.uint64)
        for harmonic in range(1, harmonic_count + 1):
            harmonic_phase = (
                state_phase * np.uint64(harmonic)
            ) & np.uint64(0xFFFF_FFFF)
            sine, cosine = _rom_values(harmonic_phase)
            basis = (sine, cosine)
            for component in range(2):
                current_column = (
                    (state_offset * harmonic_count + harmonic - 1) * 2
                    + component
                )
                design[start:stop, current_column] += (
                    basis[component] / 32768.0
                ) * current_weight
                if state_offset + 1 < knot_count:
                    next_column = (
                        (
                            (state_offset + 1) * harmonic_count
                            + harmonic
                            - 1
                        )
                        * 2
                        + component
                    )
                    design[start:stop, next_column] += (
                        basis[component] / 32768.0
                    ) * next_weight
                else:
                    design[start:stop, current_column] += (
                        basis[component] / 32768.0
                    ) * next_weight
    fitted, _residuals, _rank, _singular = np.linalg.lstsq(
        design,
        samples.astype(np.float64),
        rcond=None,
    )
    fitted = np.clip(
        np.rint(fitted),
        MIN_HARMONIC_COEFFICIENT,
        MAX_HARMONIC_COEFFICIENT,
    ).astype(np.int16).reshape(knot_count, harmonic_count, 2)
    knots = []
    for state_offset, increment in enumerate(increments):
        coefficients = fitted[state_offset].copy()
        coefficients.flags.writeable = False
        knots.append(
            TrajectoryKnot(
                max(1, int(round(PHASE_SCALE / increment))),
                coefficients,
            )
        )
    run = HarmonicRun(start_state, tuple(knots))
    return run, _render_run(sample_count, state_size, run)


def _fit_continuous_channel(
    source: np.ndarray,
    sample_rate: int,
    state_size: int,
    harmonic_count: int,
) -> tuple[tuple[HarmonicRun, ...], np.ndarray, np.ndarray]:
    """Fit one channel without constructing a redundant residual transform."""

    increments = []
    for start in range(0, source.size, state_size):
        stop = min(source.size, start + state_size)
        increments.append(_pitch_increment(source[start:stop], sample_rate))
    prediction = np.zeros(source.size, dtype=np.int16)
    runs = []
    for start_state, stop_state in _active_state_runs(increments):
        stream_start = start_state * state_size
        stream_stop = min(source.size, stop_state * state_size)
        run, run_prediction = _fit_run(
            source[stream_start:stream_stop],
            int(source.size),
            sample_rate,
            state_size,
            start_state,
            increments[start_state:stop_state],
            harmonic_count,
        )
        source_energy = float(
            source[stream_start:stream_stop].astype(np.float64)
            @ source[stream_start:stream_stop].astype(np.float64)
        )
        residual = (
            source[stream_start:stream_stop].astype(np.int64)
            - run_prediction.astype(np.int64)
        )
        residual_energy = float(residual.astype(np.float64) @ residual)
        predicted_rms = float(
            np.sqrt(
                np.mean(run_prediction.astype(np.float64) ** 2)
            )
        )
        if (
            source_energy <= 0.0
            or residual_energy >= 0.99 * source_energy
            or predicted_rms < 64.0
            or (residual.size and int(np.max(np.abs(residual))) > 32767)
        ):
            continue
        runs.append(run)
        prediction[stream_start:stream_stop] = run_prediction
    innovation64 = source.astype(np.int64) - prediction.astype(np.int64)
    if innovation64.size and int(np.max(np.abs(innovation64))) > 32767:
        raise RuntimeError("continuous harmonic Innovation exceeds int16")
    innovation = innovation64.astype(np.int16)
    prediction.flags.writeable = False
    innovation.flags.writeable = False
    return tuple(runs), prediction, innovation


def analyze_continuous_harmonic_source(
    samples: np.ndarray,
    sample_rate: int,
    *,
    state_size: int,
    harmonic_count: int,
) -> ContinuousHarmonicAnalysis:
    """Fit continuous voiced runs and analyze their exact Innovation."""

    source_view = np.asarray(samples)
    if source_view.dtype != np.int16 or source_view.ndim != 1:
        raise TypeError("continuous harmonic input must be mono int16 PCM")
    if not 512 <= state_size <= 8192:
        raise ValueError("continuous harmonic state size exceeds the bound")
    if not 1 <= harmonic_count <= MAX_HARMONICS:
        raise ValueError("continuous harmonic count exceeds the bound")
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("continuous harmonic sample rate exceeds the bound")
    if source_view.size > MAX_SAMPLE_COUNT:
        raise ValueError("continuous harmonic sample count exceeds the bound")
    source = np.array(source_view, dtype=np.int16, copy=True)
    runs, prediction, innovation = _fit_continuous_channel(
        source,
        sample_rate,
        state_size,
        harmonic_count,
    )
    lapped_analysis = analyze_lapped_source(
        innovation.reshape(-1, 1),
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    source.flags.writeable = False
    return ContinuousHarmonicAnalysis(
        sample_rate,
        source,
        state_size,
        harmonic_count,
        runs,
        prediction,
        innovation,
        lapped_analysis,
    )


def analyze_continuous_harmonic_field(
    samples: np.ndarray,
    sample_rate: int,
    *,
    state_size: int,
    harmonic_count: int,
) -> ContinuousHarmonicFieldAnalysis:
    """Fit bounded trajectory banks while retaining one joint Innovation."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or not 1 <= source_view.shape[1] <= 8
    ):
        raise TypeError(
            "continuous harmonic field input must be 1-8 channel int16 PCM"
        )
    if not 512 <= state_size <= 8192:
        raise ValueError("continuous harmonic state size exceeds the bound")
    if not 1 <= harmonic_count <= MAX_HARMONICS:
        raise ValueError("continuous harmonic count exceeds the bound")
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("continuous harmonic sample rate exceeds the bound")
    if source_view.shape[0] > MAX_SAMPLE_COUNT:
        raise ValueError("continuous harmonic sample count exceeds the bound")
    source = np.array(source_view, dtype=np.int16, copy=True)
    predictions = []
    innovations = []
    channel_runs = []
    for channel in range(source.shape[1]):
        runs, prediction, innovation = _fit_continuous_channel(
            source[:, channel],
            sample_rate,
            state_size,
            harmonic_count,
        )
        channel_runs.append(runs)
        predictions.append(prediction)
        innovations.append(innovation)
    prediction = np.column_stack(predictions).astype(np.int16, copy=False)
    innovation = np.column_stack(innovations).astype(np.int16, copy=False)
    lapped_analysis = analyze_lapped_source(
        innovation,
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    source.flags.writeable = False
    prediction.flags.writeable = False
    innovation.flags.writeable = False
    return ContinuousHarmonicFieldAnalysis(
        sample_rate,
        source,
        state_size,
        harmonic_count,
        tuple(channel_runs),
        prediction,
        innovation,
        lapped_analysis,
    )


def _pack(
    analysis: ContinuousHarmonicAnalysis,
    residual_payload: bytes,
) -> bytes:
    parameters = bytearray()
    for run in analysis.runs:
        parameters += RUN_HEADER.pack(run.start_state, len(run.knots))
        for knot in run.knots:
            parameters += LAG.pack(knot.lag)
            parameters += _pack_coefficient_pairs(knot.coefficients)
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            analysis.sample_rate,
            analysis.state_size,
            int(analysis.source.size),
            analysis.harmonic_count,
            len(residual_payload),
        )
        + parameters
        + residual_payload
    )
    return body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)


def _parse(
    payload: bytes,
) -> tuple[int, int, int, int, tuple[HarmonicRun, ...], bytes]:
    if len(payload) < HEADER.size + CHECKSUM.size:
        raise ValueError("truncated continuous harmonic stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("continuous harmonic checksum mismatch")
    (
        magic,
        version,
        sample_rate,
        state_size,
        sample_count,
        harmonic_count,
        residual_bytes,
    ) = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported continuous harmonic stream")
    if (
        not 8000 <= sample_rate <= 192000
        or not 512 <= state_size <= 8192
        or sample_count > MAX_SAMPLE_COUNT
        or not 1 <= harmonic_count <= MAX_HARMONICS
    ):
        raise ValueError("continuous harmonic header exceeds the bound")
    state_count = (sample_count + state_size - 1) // state_size
    if state_count > MAX_BLOCK_COUNT or residual_bytes > len(body):
        raise ValueError("continuous harmonic state count exceeds the bound")
    residual_start = len(body) - residual_bytes
    if residual_start < HEADER.size:
        raise ValueError("continuous harmonic stream length mismatch")
    cursor = HEADER.size
    previous_stop = 0
    knot_bytes = LAG.size + 3 * harmonic_count
    runs = []
    while cursor < residual_start:
        if cursor + RUN_HEADER.size > residual_start:
            raise ValueError("truncated continuous harmonic run")
        start_state, run_state_count = RUN_HEADER.unpack_from(body, cursor)
        cursor += RUN_HEADER.size
        stop_state = start_state + run_state_count
        if (
            run_state_count == 0
            or run_state_count > MAX_RUN_STATES
            or start_state < previous_stop
            or stop_state > state_count
        ):
            raise ValueError("non-canonical continuous harmonic run")
        required = run_state_count * knot_bytes
        if cursor + required > residual_start:
            raise ValueError("truncated continuous harmonic knots")
        knots = []
        for _state in range(run_state_count):
            lag = LAG.unpack_from(body, cursor)[0]
            cursor += LAG.size
            if lag == 0:
                raise ValueError("continuous harmonic lag is zero")
            coefficients = _unpack_coefficient_pairs(
                body[cursor : cursor + 3 * harmonic_count],
                harmonic_count,
            )
            cursor += 3 * harmonic_count
            knots.append(TrajectoryKnot(lag, coefficients))
        runs.append(HarmonicRun(start_state, tuple(knots)))
        previous_stop = stop_state
    if cursor != residual_start:
        raise ValueError("continuous harmonic parameter length mismatch")
    return (
        sample_rate,
        state_size,
        sample_count,
        harmonic_count,
        tuple(runs),
        body[residual_start:],
    )


def _synthesize(
    residual: np.ndarray,
    state_size: int,
    runs: tuple[HarmonicRun, ...],
) -> np.ndarray:
    output = residual.astype(np.int64, copy=True)
    for run in runs:
        start = run.start_state * state_size
        prediction = _render_run(
            residual.size,
            state_size,
            run,
        )
        stop = start + prediction.size
        output[start:stop] = np.clip(
            output[start:stop] + prediction.astype(np.int64),
            -32768,
            32767,
        )
    return output.astype(np.int16)


def decode_continuous_harmonic_stream(
    payload: bytes,
) -> tuple[int, np.ndarray]:
    """Independently parse and reconstruct one prospective CHT1 stream."""

    (
        sample_rate,
        state_size,
        sample_count,
        _harmonic_count,
        runs,
        residual_payload,
    ) = _parse(payload)
    residual = decode_lapped_stream(residual_payload)
    if (
        residual.sample_rate != sample_rate
        or residual.samples.shape != (sample_count, 1)
    ):
        raise ValueError("continuous harmonic residual configuration mismatch")
    reconstruction = _synthesize(
        residual.samples[:, 0],
        state_size,
        runs,
    )
    reconstruction.flags.writeable = False
    return sample_rate, reconstruction


def encode_continuous_harmonic_analysis(
    analysis: ContinuousHarmonicAnalysis,
    *,
    coefficients_per_frame: int,
) -> ContinuousHarmonicResult:
    """Encode, independently decode, and report one complete CHT1 candidate."""

    residual = encode_lapped_analysis(
        analysis.lapped_analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    payload = _pack(analysis, residual.payload)
    sample_rate, reconstruction = decode_continuous_harmonic_stream(payload)
    if sample_rate != analysis.sample_rate:
        raise RuntimeError("continuous harmonic decoder sample rate differs")
    active_states = sum(len(run.knots) for run in analysis.runs)
    state_count = (
        analysis.source.size + analysis.state_size - 1
    ) // analysis.state_size
    report = {
        "status": "R-106 research oracle; no Main syntax assigned",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "residual_stream_bytes": len(residual.payload),
        "basis_envelope_bytes": len(payload) - len(residual.payload),
        "state_size": analysis.state_size,
        "state_count": state_count,
        "harmonic_count": analysis.harmonic_count,
        "run_count": len(analysis.runs),
        "active_state_count": active_states,
        "active_state_fraction": active_states / max(1, state_count),
        "coefficients_per_frame": coefficients_per_frame,
        "decoder_change": True,
        "bitstream_status": "prospective research CHT1",
    }
    return ContinuousHarmonicResult(payload, reconstruction, report)


def _pack_field(
    analysis: ContinuousHarmonicFieldAnalysis,
    residual_payload: bytes,
) -> bytes:
    parameters = bytearray()
    for channel, runs in enumerate(analysis.channel_runs):
        parameters += CHANNEL_HEADER.pack(channel, len(runs))
        for run in runs:
            parameters += RUN_HEADER.pack(run.start_state, len(run.knots))
            for knot in run.knots:
                parameters += LAG.pack(knot.lag)
                parameters += _pack_coefficient_pairs(knot.coefficients)
    body = (
        FIELD_HEADER.pack(
            FIELD_MAGIC,
            VERSION,
            analysis.sample_rate,
            analysis.state_size,
            int(analysis.source.shape[0]),
            analysis.harmonic_count,
            analysis.source.shape[1],
            len(residual_payload),
        )
        + parameters
        + residual_payload
    )
    return body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)


def _parse_field(
    payload: bytes,
) -> tuple[
    int,
    int,
    int,
    int,
    tuple[tuple[HarmonicRun, ...], ...],
    bytes,
]:
    if len(payload) < FIELD_HEADER.size + CHECKSUM.size:
        raise ValueError("truncated continuous harmonic field stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("continuous harmonic field checksum mismatch")
    (
        magic,
        version,
        sample_rate,
        state_size,
        sample_count,
        harmonic_count,
        channel_count,
        residual_bytes,
    ) = FIELD_HEADER.unpack_from(body)
    if magic != FIELD_MAGIC or version != VERSION:
        raise ValueError("unsupported continuous harmonic field stream")
    if (
        not 8000 <= sample_rate <= 192000
        or not 512 <= state_size <= 8192
        or sample_count > MAX_SAMPLE_COUNT
        or not 1 <= harmonic_count <= MAX_HARMONICS
        or not 1 <= channel_count <= 8
    ):
        raise ValueError("continuous harmonic field header exceeds the bound")
    state_count = (sample_count + state_size - 1) // state_size
    if state_count > MAX_BLOCK_COUNT or residual_bytes > len(body):
        raise ValueError(
            "continuous harmonic field state count exceeds the bound"
        )
    residual_start = len(body) - residual_bytes
    if residual_start < FIELD_HEADER.size:
        raise ValueError("continuous harmonic field length mismatch")
    cursor = FIELD_HEADER.size
    knot_bytes = LAG.size + 3 * harmonic_count
    channel_runs: list[tuple[HarmonicRun, ...]] = []
    for expected_channel in range(channel_count):
        if cursor + CHANNEL_HEADER.size > residual_start:
            raise ValueError("truncated continuous harmonic channel")
        channel, run_count = CHANNEL_HEADER.unpack_from(body, cursor)
        cursor += CHANNEL_HEADER.size
        if channel != expected_channel:
            raise ValueError("non-canonical continuous harmonic channel")
        runs = []
        previous_stop = 0
        for _run_index in range(run_count):
            if cursor + RUN_HEADER.size > residual_start:
                raise ValueError("truncated continuous harmonic field run")
            start_state, run_state_count = RUN_HEADER.unpack_from(body, cursor)
            cursor += RUN_HEADER.size
            stop_state = start_state + run_state_count
            if (
                run_state_count == 0
                or run_state_count > MAX_RUN_STATES
                or start_state < previous_stop
                or stop_state > state_count
            ):
                raise ValueError("non-canonical continuous harmonic field run")
            required = run_state_count * knot_bytes
            if cursor + required > residual_start:
                raise ValueError("truncated continuous harmonic field knots")
            knots = []
            for _state in range(run_state_count):
                lag = LAG.unpack_from(body, cursor)[0]
                cursor += LAG.size
                if lag == 0:
                    raise ValueError("continuous harmonic field lag is zero")
                coefficients = _unpack_coefficient_pairs(
                    body[cursor : cursor + 3 * harmonic_count],
                    harmonic_count,
                )
                cursor += 3 * harmonic_count
                knots.append(TrajectoryKnot(lag, coefficients))
            runs.append(HarmonicRun(start_state, tuple(knots)))
            previous_stop = stop_state
        channel_runs.append(tuple(runs))
    if cursor != residual_start:
        raise ValueError("continuous harmonic field parameter mismatch")
    return (
        sample_rate,
        state_size,
        sample_count,
        harmonic_count,
        tuple(channel_runs),
        body[residual_start:],
    )


def decode_continuous_harmonic_field(
    payload: bytes,
) -> tuple[int, np.ndarray]:
    """Independently parse and reconstruct one prospective CHF1 stream."""

    (
        sample_rate,
        state_size,
        sample_count,
        _harmonic_count,
        channel_runs,
        residual_payload,
    ) = _parse_field(payload)
    residual = decode_lapped_stream(residual_payload)
    if (
        residual.sample_rate != sample_rate
        or residual.samples.shape
        != (sample_count, len(channel_runs))
    ):
        raise ValueError(
            "continuous harmonic field residual configuration mismatch"
        )
    output = residual.samples.astype(np.int64, copy=True)
    for channel, runs in enumerate(channel_runs):
        for run in runs:
            start = run.start_state * state_size
            prediction = _render_run(
                sample_count,
                state_size,
                run,
            )
            stop = start + prediction.size
            output[start:stop, channel] = np.clip(
                output[start:stop, channel]
                + prediction.astype(np.int64),
                -32768,
                32767,
            )
    reconstruction = output.astype(np.int16)
    reconstruction.flags.writeable = False
    return sample_rate, reconstruction


def encode_continuous_harmonic_field_analysis(
    analysis: ContinuousHarmonicFieldAnalysis,
    *,
    coefficients_per_frame: int,
) -> ContinuousHarmonicFieldResult:
    """Encode and independently decode one complete CHF1 candidate."""

    residual = encode_lapped_analysis(
        analysis.lapped_analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    payload = _pack_field(analysis, residual.payload)
    sample_rate, reconstruction = decode_continuous_harmonic_field(payload)
    if sample_rate != analysis.sample_rate:
        raise RuntimeError(
            "continuous harmonic field decoder sample rate differs"
        )
    active_states = sum(
        len(run.knots)
        for runs in analysis.channel_runs
        for run in runs
    )
    state_count = (
        analysis.source.shape[0] + analysis.state_size - 1
    ) // analysis.state_size
    report = {
        "status": "R-106 research oracle; no Main syntax assigned",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "residual_stream_bytes": len(residual.payload),
        "basis_envelope_bytes": len(payload) - len(residual.payload),
        "state_size": analysis.state_size,
        "state_count": state_count,
        "channel_count": analysis.source.shape[1],
        "harmonic_count": analysis.harmonic_count,
        "run_count": sum(len(runs) for runs in analysis.channel_runs),
        "active_state_count": active_states,
        "active_state_fraction": (
            active_states
            / max(1, state_count * analysis.source.shape[1])
        ),
        "coefficients_per_frame": coefficients_per_frame,
        "decoder_change": True,
        "bitstream_status": "prospective research CHF1",
    }
    return ContinuousHarmonicFieldResult(
        payload,
        reconstruction,
        report,
    )
