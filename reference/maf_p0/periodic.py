"""Encoder-side periodic analysis and normative-style integer rendering."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


PHASE_SCALE = 1 << 32
GAIN_SHIFT = 15
MAX_PHASE_KNOT_SPAN = 32768


@dataclass(frozen=True)
class PeriodicAnalysis:
    period_samples: int
    phase_increment_q32: int
    basis: np.ndarray


@dataclass(frozen=True)
class PhaseTrajectory:
    """Absolute piecewise-linear Q32 phase law.

    Contract:
    - positions are local sample indices and include both 0 and sample_count;
    - increments are unsigned Q0.32 cycles/sample at the corresponding knots;
    - phase is evaluated from an absolute polynomial, never from a previous
      render block, so slicing and random access are bit-exact.
    """

    positions: np.ndarray
    increments_q32: np.ndarray
    phase_origin_q32: int = 0

    def __post_init__(self) -> None:
        positions = np.asarray(self.positions, dtype=np.int64).copy()
        increments = np.asarray(self.increments_q32, dtype=np.uint32).copy()
        if positions.ndim != 1 or increments.ndim != 1:
            raise TypeError("trajectory arrays must be one-dimensional")
        if positions.size < 2 or positions.size != increments.size:
            raise ValueError("trajectory requires matching endpoint knots")
        if int(positions[0]) != 0 or np.any(np.diff(positions) <= 0):
            raise ValueError("trajectory positions must start at zero and increase")
        if np.any(np.diff(positions) > MAX_PHASE_KNOT_SPAN):
            raise ValueError("trajectory knot span exceeds the P1 arithmetic bound")
        if not 0 <= int(self.phase_origin_q32) <= 0xFFFFFFFF:
            raise ValueError("phase origin is outside Q32 range")
        positions.setflags(write=False)
        increments.setflags(write=False)
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "increments_q32", increments)

    @property
    def sample_count(self) -> int:
        return int(self.positions[-1])


def _round_divide_signed_array(
    numerator: np.ndarray,
    denominator: int,
) -> np.ndarray:
    """Round signed int64 values to nearest, with ties away from zero."""

    if denominator <= 0:
        raise ValueError("denominator must be positive")
    magnitude = np.abs(numerator)
    rounded = (magnitude + denominator // 2) // denominator
    return np.where(numerator < 0, -rounded, rounded)


def _phase_advance_q32(length: int, start_increment: int, end_increment: int) -> int:
    """Return the exact discrete phase advance of one linear-law interval."""

    if length <= 0 or length > MAX_PHASE_KNOT_SPAN:
        raise ValueError("phase interval length is outside the P1 bound")
    delta = int(end_increment) - int(start_increment)
    curve = delta * length * (length - 1)
    magnitude = abs(curve)
    rounded = (magnitude + length) // (2 * length)
    if curve < 0:
        rounded = -rounded
    return length * int(start_increment) + rounded


def _trajectory_phase_origins(trajectory: PhaseTrajectory) -> np.ndarray:
    """Materialize Q32 phase at every knot for bounded random access."""

    origins = np.empty(trajectory.positions.size, dtype=np.uint32)
    phase = int(trajectory.phase_origin_q32)
    origins[0] = np.uint32(phase)
    for index in range(trajectory.positions.size - 1):
        length = int(trajectory.positions[index + 1] - trajectory.positions[index])
        phase = (
            phase
            + _phase_advance_q32(
                length,
                int(trajectory.increments_q32[index]),
                int(trajectory.increments_q32[index + 1]),
            )
        ) & 0xFFFFFFFF
        origins[index + 1] = np.uint32(phase)
    return origins


def phase_values_q32(
    trajectory: PhaseTrajectory,
    *,
    output_start: int = 0,
    output_count: int | None = None,
) -> np.ndarray:
    """Evaluate absolute Q32 phases for an arbitrary output slice."""

    if output_start < 0 or output_start > trajectory.sample_count:
        raise ValueError("output_start is outside the trajectory")
    count = (
        trajectory.sample_count - output_start
        if output_count is None
        else int(output_count)
    )
    if count < 0 or output_start + count > trajectory.sample_count:
        raise ValueError("requested phase slice is outside the trajectory")
    if count == 0:
        return np.empty(0, dtype=np.uint32)

    output = np.empty(count, dtype=np.uint32)
    absolute_end = output_start + count
    knot_origins = _trajectory_phase_origins(trajectory)

    # Each interval is evaluated from its stored knot phase. No previous output
    # sample or caller block size participates in the result.
    for interval in range(trajectory.positions.size - 1):
        interval_start = int(trajectory.positions[interval])
        interval_end = int(trajectory.positions[interval + 1])
        start = max(output_start, interval_start)
        end = min(absolute_end, interval_end)
        if start >= end:
            continue
        local = np.arange(start - interval_start, end - interval_start, dtype=np.int64)
        length = interval_end - interval_start
        increment0 = int(trajectory.increments_q32[interval])
        delta = int(trajectory.increments_q32[interval + 1]) - increment0
        curve_numerator = delta * local * (local - 1)
        curve = _round_divide_signed_array(curve_numerator, 2 * length)
        phase = (
            np.int64(int(knot_origins[interval]))
            + local * np.int64(increment0)
            + curve
        ) & np.int64(0xFFFFFFFF)
        destination = slice(start - output_start, end - output_start)
        output[destination] = phase.astype(np.uint32)
    return output


def render_basis_trajectory(
    basis: np.ndarray,
    trajectory: PhaseTrajectory,
    *,
    output_start: int = 0,
    output_count: int | None = None,
) -> np.ndarray:
    """Render one immutable Basis under an absolute continuous phase law."""

    if basis.dtype != np.int16 or basis.ndim != 1:
        raise TypeError("basis must be an int16 vector")
    if basis.size < 2:
        raise ValueError("basis must contain at least two samples")
    phases = phase_values_q32(
        trajectory,
        output_start=output_start,
        output_count=output_count,
    ).astype(np.uint64)
    positions = phases * np.uint64(basis.size)
    base_index = (positions >> np.uint64(32)).astype(np.int64)
    fraction_q16 = ((positions >> np.uint64(16)) & 0xFFFF).astype(np.int64)
    next_index = (base_index + 1) % basis.size
    left = basis[base_index].astype(np.int64)
    right = basis[next_index].astype(np.int64)
    interpolated = (
        left * (65536 - fraction_q16) + right * fraction_q16 + 32768
    ) >> 16
    return np.clip(interpolated, -32768, 32767).astype(np.int16)


def constant_phase_trajectory(
    sample_count: int,
    phase_increment_q32: int,
    *,
    phase_origin_q32: int = 0,
) -> PhaseTrajectory:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if sample_count > MAX_PHASE_KNOT_SPAN:
        positions = list(range(0, sample_count, MAX_PHASE_KNOT_SPAN))
        positions.append(sample_count)
    else:
        positions = [0, sample_count]
    increments = np.full(len(positions), phase_increment_q32, dtype=np.uint32)
    return PhaseTrajectory(
        np.asarray(positions, dtype=np.int64),
        increments,
        phase_origin_q32,
    )


def estimate_phase_trajectory(
    samples: np.ndarray,
    sample_rate: int,
    *,
    knot_interval: int = 4096,
    minimum_frequency: float = 50.0,
    maximum_frequency: float = 2000.0,
) -> PhaseTrajectory:
    """Estimate a bounded pitch law; all floating-point work is encoder-only."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if samples.size < 64:
        raise ValueError("not enough samples for pitch trajectory analysis")
    if knot_interval < 64 or knot_interval > MAX_PHASE_KNOT_SPAN:
        raise ValueError("knot_interval is outside the P1 bound")

    positions = list(range(0, samples.size, knot_interval))
    if positions[-1] != samples.size:
        positions.append(samples.size)
    increments: list[int] = []
    half_window = max(2048, knot_interval)
    fallback_period = estimate_period(
        samples,
        sample_rate,
        minimum_frequency=minimum_frequency,
        maximum_frequency=maximum_frequency,
    )
    previous_period = fallback_period
    for position in positions:
        start = max(0, position - half_window)
        end = min(samples.size, position + half_window)
        window = samples[start:end]
        try:
            period = estimate_period(
                window,
                sample_rate,
                minimum_frequency=minimum_frequency,
                maximum_frequency=maximum_frequency,
                analysis_samples=min(window.size, 16384),
            )
        except ValueError:
            period = previous_period
        previous_period = period
        increments.append(int(round(PHASE_SCALE / period)) & 0xFFFFFFFF)
    return PhaseTrajectory(
        np.asarray(positions, dtype=np.int64),
        np.asarray(increments, dtype=np.uint32),
    )


def estimate_period(
    samples: np.ndarray,
    sample_rate: int,
    *,
    minimum_frequency: float = 50.0,
    maximum_frequency: float = 2000.0,
    analysis_samples: int = 32768,
) -> int:
    """Estimate one integer pitch period with FFT autocorrelation."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if samples.size < 64:
        raise ValueError("not enough samples for periodic analysis")

    count = min(samples.size, analysis_samples)
    signal = samples[:count].astype(np.float64)
    signal -= signal.mean()
    peak = float(np.max(np.abs(signal)))
    if peak < 1.0:
        raise ValueError("signal is silent")
    signal *= np.hanning(count)

    minimum_lag = max(2, int(sample_rate / maximum_frequency))
    maximum_lag = min(count // 2, int(sample_rate / minimum_frequency))
    if minimum_lag >= maximum_lag:
        raise ValueError("invalid frequency search interval")

    fft_size = 1 << ((2 * count - 1).bit_length())
    spectrum = np.fft.rfft(signal, fft_size)
    correlation = np.fft.irfft(spectrum * np.conj(spectrum), fft_size)[:count]

    energy = np.cumsum(signal * signal)
    lag_values = np.arange(minimum_lag, maximum_lag + 1)
    left_energy = energy[count - lag_values - 1]
    total_energy = energy[-1]
    right_energy = total_energy - np.concatenate(
        ([0.0], energy[lag_values[:-1] - 1])
    )
    normalization = np.sqrt(np.maximum(left_energy * right_energy, 1.0))
    score = correlation[lag_values] / normalization

    best_index = int(np.argmax(score))
    best_lag = int(lag_values[best_index])
    if not math.isfinite(float(score[best_index])):
        raise ValueError("period estimation failed")
    return best_lag


def _resample_cycle(cycle: np.ndarray, output_length: int) -> np.ndarray:
    if output_length < 8:
        raise ValueError("basis length is too small")
    source_position = np.arange(cycle.size + 1, dtype=np.float64)
    source = np.concatenate((cycle.astype(np.float64), cycle[:1]))
    target_position = np.arange(output_length, dtype=np.float64)
    target_position *= cycle.size / output_length
    resampled = np.interp(target_position, source_position, source)
    return np.clip(np.rint(resampled), -32768, 32767).astype(np.int16)


def analyze_periodic_basis(
    samples: np.ndarray,
    sample_rate: int,
    *,
    basis_length: int = 256,
    period_samples: int | None = None,
) -> PeriodicAnalysis:
    period = period_samples or estimate_period(samples, sample_rate)
    if samples.size < period:
        raise ValueError("input is shorter than one period")

    # Average several aligned cycles. This is deliberately simple P0 analysis.
    cycle_count = min(samples.size // period, 64)
    cycles = samples[: cycle_count * period].reshape(cycle_count, period)
    mean_cycle = np.mean(cycles.astype(np.float64), axis=0)
    basis = _resample_cycle(mean_cycle, basis_length)
    phase_increment = int(round(PHASE_SCALE / period)) & 0xFFFFFFFF
    return PeriodicAnalysis(period, phase_increment, basis)


def render_unity_basis(
    basis: np.ndarray,
    sample_count: int,
    phase_increment_q32: int,
    *,
    phase_origin_q32: int = 0,
) -> np.ndarray:
    """Render periodic Basis with canonical Q32 phase and Q16 interpolation."""

    if basis.dtype != np.int16 or basis.ndim != 1:
        raise TypeError("basis must be int16 vector")
    if sample_count < 0:
        raise ValueError("sample_count must be non-negative")
    if not 0 <= phase_increment_q32 <= 0xFFFFFFFF:
        raise ValueError("phase increment out of range")

    indices = np.arange(sample_count, dtype=np.uint64)
    phases = (
        np.uint64(phase_origin_q32)
        + indices * np.uint64(phase_increment_q32)
    ) & np.uint64(0xFFFFFFFF)
    positions = phases * np.uint64(basis.size)
    base_index = (positions >> np.uint64(32)).astype(np.int64)
    fraction_q16 = ((positions >> np.uint64(16)) & 0xFFFF).astype(np.int64)
    next_index = (base_index + 1) % basis.size

    left = basis[base_index].astype(np.int64)
    right = basis[next_index].astype(np.int64)
    interpolated = (
        left * (65536 - fraction_q16) + right * fraction_q16 + 32768
    ) >> 16
    return np.clip(interpolated, -32768, 32767).astype(np.int16)


def fit_block_gains(
    samples: np.ndarray,
    unity_prediction: np.ndarray,
    block_size: int,
) -> np.ndarray:
    """Fit a Q15 constant amplitude law independently for each block."""

    if samples.shape != unity_prediction.shape:
        raise ValueError("prediction shape mismatch")
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    block_count = (samples.size + block_size - 1) // block_size
    gains = np.empty(block_count, dtype=np.int32)

    source64 = samples.astype(np.int64)
    prediction64 = unity_prediction.astype(np.int64)
    for block in range(block_count):
        start = block * block_size
        end = min(samples.size, start + block_size)
        reference = prediction64[start:end]
        denominator = int(reference @ reference)
        if denominator == 0:
            gains[block] = 0
            continue
        numerator = int(source64[start:end] @ reference)
        gain = int(round((numerator * (1 << GAIN_SHIFT)) / denominator))
        gains[block] = np.int32(np.clip(gain, -131072, 131071))
    return gains


def apply_block_gains(
    unity_prediction: np.ndarray,
    gains_q15: np.ndarray,
    block_size: int,
) -> np.ndarray:
    if unity_prediction.dtype != np.int16 or unity_prediction.ndim != 1:
        raise TypeError("unity_prediction must be mono int16")
    if gains_q15.dtype != np.int32 or gains_q15.ndim != 1:
        raise TypeError("gains_q15 must be int32 vector")
    expected = (unity_prediction.size + block_size - 1) // block_size
    if gains_q15.size != expected:
        raise ValueError("gain count mismatch")

    output = np.empty(unity_prediction.size, dtype=np.int16)
    source64 = unity_prediction.astype(np.int64)
    for block, gain in enumerate(gains_q15.astype(np.int64)):
        start = block * block_size
        end = min(unity_prediction.size, start + block_size)
        scaled = (source64[start:end] * gain + (1 << (GAIN_SHIFT - 1))) >> GAIN_SHIFT
        output[start:end] = np.clip(scaled, -32768, 32767).astype(np.int16)
    return output
