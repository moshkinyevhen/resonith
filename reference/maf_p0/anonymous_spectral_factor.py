"""Deterministic anonymous spectral factor proposer for R-159/R-160."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class AnonymousSpectralLanguage:
    """Finite phase-preserving NMF proposer language."""

    fft_samples: int = 1024
    hop_samples: int = 256
    factor_count: int = 6
    iterations: int = 48
    seed: int = 160

    def __post_init__(self) -> None:
        if (
            self.fft_samples < 64
            or self.fft_samples & (self.fft_samples - 1)
        ):
            raise ValueError("anonymous factor FFT must be a power of two")
        if not 1 <= self.hop_samples <= self.fft_samples // 2:
            raise ValueError("anonymous factor hop exceeds overlap bound")
        if not 2 <= self.factor_count <= 32:
            raise ValueError("anonymous factor count exceeds bounds")
        if not 1 <= self.iterations <= 512:
            raise ValueError("anonymous factor iteration count exceeds bounds")


@dataclass(frozen=True)
class AnonymousSpectralFactorization:
    """Unnamed additive proposer fields plus one exact final Truth."""

    factors: tuple[np.ndarray, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    spectral_dictionary: np.ndarray
    activation_field: np.ndarray
    report: dict


def _nmf(
    magnitude: np.ndarray,
    rank: int,
    iterations: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    epsilon = 1.0e-9
    rng = np.random.default_rng(seed)
    scale = max(float(np.mean(magnitude)), epsilon)
    dictionary = rng.uniform(0.5, 1.5, (magnitude.shape[0], rank)) * scale
    activations = rng.uniform(0.5, 1.5, (rank, magnitude.shape[1]))
    for _ in range(iterations):
        activations *= (
            dictionary.T @ magnitude
        ) / (
            dictionary.T @ dictionary @ activations + epsilon
        )
        dictionary *= (
            magnitude @ activations.T
        ) / (
            dictionary @ (activations @ activations.T) + epsilon
        )
        norms = np.maximum(np.sum(dictionary, axis=0), epsilon)
        dictionary /= norms[None, :]
        activations *= norms[:, None]
    approximation = dictionary @ activations
    error = float(
        np.linalg.norm(magnitude - approximation)
        / max(np.linalg.norm(magnitude), epsilon)
    )
    return dictionary, activations, error


def infer_anonymous_spectral_factors(
    samples: np.ndarray,
    *,
    sample_rate: int,
    language: AnonymousSpectralLanguage,
) -> AnonymousSpectralFactorization:
    """Infer anonymous cross-channel fields without semantic source labels."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("anonymous factorization requires frame-major PCM16")
    overlap = language.fft_samples - language.hop_samples
    spectra = []
    for channel in range(source.shape[1]):
        _frequencies, _times, spectrum = signal.stft(
            source[:, channel].astype(np.float64),
            fs=sample_rate,
            window="hann",
            nperseg=language.fft_samples,
            noverlap=overlap,
            boundary="zeros",
            padded=True,
        )
        spectra.append(spectrum)
    spectrum_field = np.stack(spectra, axis=0)
    magnitude = np.sqrt(
        np.sum(np.abs(spectrum_field) ** 2, axis=0)
    )
    dictionary, activations, relative_error = _nmf(
        magnitude,
        language.factor_count,
        language.iterations,
        language.seed,
    )
    contributions = (
        dictionary.T[:, :, None] * activations[:, None, :]
    )
    denominator = np.maximum(np.sum(contributions, axis=0), 1.0e-12)
    masks = contributions / denominator[None, :, :]

    factors = []
    for factor_index in range(language.factor_count):
        factor = np.empty(source.shape, dtype=np.int16)
        for channel in range(source.shape[1]):
            _times, rendered = signal.istft(
                spectrum_field[channel] * masks[factor_index],
                fs=sample_rate,
                window="hann",
                nperseg=language.fft_samples,
                noverlap=overlap,
                input_onesided=True,
                boundary=True,
            )
            rendered = rendered[: source.shape[0]]
            if rendered.size < source.shape[0]:
                rendered = np.pad(
                    rendered,
                    (0, source.shape[0] - rendered.size),
                )
            factor[:, channel] = np.clip(
                np.rint(rendered),
                -32768,
                32767,
            ).astype(np.int16)
        factor.flags.writeable = False
        factors.append(factor)

    prediction = sum(
        (factor.astype(np.int64) for factor in factors),
        start=np.zeros(source.shape, dtype=np.int64),
    )
    source64 = source.astype(np.int64)
    truth = source64 - prediction
    reconstruction = prediction + truth
    source_hash = hashlib.sha256(
        np.ascontiguousarray(source, dtype="<i2").tobytes()
    ).hexdigest()
    reconstruction_hash = hashlib.sha256(
        np.ascontiguousarray(reconstruction, dtype="<i2").tobytes()
    ).hexdigest()
    if source_hash != reconstruction_hash:
        raise RuntimeError("anonymous factorization exact identity failed")
    dictionary.flags.writeable = False
    activations.flags.writeable = False
    return AnonymousSpectralFactorization(
        tuple(factors),
        prediction,
        truth,
        reconstruction,
        dictionary,
        activations,
        {
            "schema": "resonith-r160-anonymous-spectral-factor-1",
            "status": (
                "encoder-side proposer; dictionary/activation transport "
                "not admitted"
            ),
            "semantic_labels": False,
            "shared_cross_channel_masks": True,
            "mixture_phase_preserved": True,
            "factor_count": language.factor_count,
            "fft_samples": language.fft_samples,
            "hop_samples": language.hop_samples,
            "iterations": language.iterations,
            "relative_magnitude_factorization_error": relative_error,
            "exact_integer_reconstruction": True,
            "one_final_time_domain_truth": True,
            "source_sha256": source_hash,
            "reconstruction_sha256": reconstruction_hash,
        },
    )
