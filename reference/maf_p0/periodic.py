"""Encoder-side periodic analysis and normative-style integer rendering."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


PHASE_SCALE = 1 << 32
GAIN_SHIFT = 15


@dataclass(frozen=True)
class PeriodicAnalysis:
    period_samples: int
    phase_increment_q32: int
    basis: np.ndarray


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
