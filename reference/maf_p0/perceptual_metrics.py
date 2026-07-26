"""Deterministic diagnostic metrics for lapped-codec research gates."""

from __future__ import annotations

import numpy as np


def _validate_pair(
    source: np.ndarray,
    reconstruction: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    reference = np.asarray(source)
    candidate = np.asarray(reconstruction)
    if (
        reference.dtype != np.int16
        or candidate.dtype != np.int16
        or reference.ndim != 2
        or candidate.shape != reference.shape
        or reference.shape[0] == 0
    ):
        raise TypeError("metric inputs must be equal frame-major PCM16 arrays")
    return (
        reference.astype(np.float64) / 32768.0,
        candidate.astype(np.float64) / 32768.0,
    )


def multiresolution_spectral_error_db(
    source: np.ndarray,
    reconstruction: np.ndarray,
    *,
    window_sizes: tuple[int, ...] = (256, 1024, 4096),
) -> dict:
    """Return lower-is-better magnitude error over deterministic Hann STFTs."""

    reference, candidate = _validate_pair(source, reconstruction)
    per_window = {}
    ratios = []
    for window_size in window_sizes:
        if (
            window_size < 32
            or window_size & (window_size - 1)
            or window_size > 8192
        ):
            raise ValueError("metric window must be a power of two, 32-8192")
        hop = window_size // 2
        padding = (-max(0, reference.shape[0] - window_size)) % hop
        padded_frames = max(window_size, reference.shape[0] + padding)
        reference_padded = np.pad(
            reference,
            ((0, padded_frames - reference.shape[0]), (0, 0)),
        )
        candidate_padded = np.pad(
            candidate,
            ((0, padded_frames - candidate.shape[0]), (0, 0)),
        )
        frame_starts = range(0, padded_frames - window_size + 1, hop)
        window = np.hanning(window_size).reshape(-1, 1)
        source_magnitudes = []
        error_energy = 0.0
        source_energy = 0.0
        for start in frame_starts:
            source_spectrum = np.fft.rfft(
                reference_padded[start : start + window_size] * window,
                axis=0,
            )
            candidate_spectrum = np.fft.rfft(
                candidate_padded[start : start + window_size] * window,
                axis=0,
            )
            source_magnitude = np.abs(source_spectrum)
            difference = source_magnitude - np.abs(candidate_spectrum)
            error_energy += float(np.sum(np.square(difference)))
            source_energy += float(np.sum(np.square(source_magnitude)))
            source_magnitudes.append(float(np.mean(source_magnitude)))
        ratio = np.sqrt(error_energy / max(source_energy, 1e-30))
        ratios.append(ratio)
        per_window[str(window_size)] = {
            "spectral_convergence_db": 20.0 * np.log10(max(ratio, 1e-15)),
            "mean_source_magnitude": float(np.mean(source_magnitudes)),
        }
    mean_ratio = float(np.mean(ratios))
    return {
        "mean_spectral_convergence_db": (
            20.0 * np.log10(max(mean_ratio, 1e-15))
        ),
        "per_window": per_window,
    }


def transient_pre_echo_error_db(
    source: np.ndarray,
    reconstruction: np.ndarray,
    sample_rate: int,
    *,
    maximum_onsets: int = 8,
) -> dict:
    """Measure reconstruction error immediately before strong source onsets."""

    reference, candidate = _validate_pair(source, reconstruction)
    if sample_rate <= 0 or maximum_onsets <= 0:
        raise ValueError("transient metric configuration is invalid")
    mono_energy = np.mean(np.square(reference), axis=1)
    analysis_window = max(32, int(round(sample_rate * 0.003)))
    hop = max(16, analysis_window // 2)
    cumulative = np.concatenate(([0.0], np.cumsum(mono_energy)))
    starts = np.arange(
        0,
        max(1, mono_energy.size - analysis_window + 1),
        hop,
        dtype=np.int64,
    )
    energies = (
        cumulative[starts + analysis_window] - cumulative[starts]
    ) / analysis_window
    flux = np.maximum(energies[1:] - energies[:-1], 0.0)
    candidate_indices = [
        index
        for index in range(1, flux.size - 1)
        if flux[index] > 0.0
        and flux[index] >= flux[index - 1]
        and flux[index] >= flux[index + 1]
    ]
    ranked = sorted(
        candidate_indices,
        key=lambda index: (-float(flux[index]), index),
    )
    region = max(1, int(round(sample_rate * 0.010)))
    minimum_spacing = max(region, int(round(sample_rate * 0.020)))
    selected = []
    for index in ranked:
        coarse = int(starts[index + 1])
        search_end = min(
            mono_energy.size,
            coarse + 2 * analysis_window,
        )
        onset = coarse + int(np.argmax(mono_energy[coarse:search_end]))
        if onset < region or onset + region > reference.shape[0]:
            continue
        if any(abs(onset - previous) < minimum_spacing for previous in selected):
            continue
        selected.append(onset)
        if len(selected) == maximum_onsets:
            break
    error = candidate - reference
    ratios_db = []
    for onset in selected:
        pre_error = float(
            np.mean(np.square(error[onset - region : onset]))
        )
        attack_truth = float(
            np.mean(np.square(reference[onset : onset + region]))
        )
        ratios_db.append(
            10.0
            * np.log10(max(pre_error, 1e-30) / max(attack_truth, 1e-30))
        )
    return {
        "onset_count": len(selected),
        "onset_samples": selected,
        "mean_pre_echo_error_db": (
            float(np.mean(ratios_db)) if ratios_db else None
        ),
        "worst_pre_echo_error_db": (
            float(np.max(ratios_db)) if ratios_db else None
        ),
    }
