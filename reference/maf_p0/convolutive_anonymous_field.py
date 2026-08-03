"""R-161 finite convolutive anonymous-field proposer.

This encoder-only oracle extends stationary NMF with a bounded temporal kernel.
It preserves mixture phase and channel relationships through shared soft masks.
Only later decoder-verifiable Basis/law candidates and one final Truth may enter
the bitstream; the factorizer itself is never normative.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class ConvolutiveAnonymousLanguage:
    """Finite NMFD/CNMF proposer language declared by an evidence run."""

    fft_samples: int = 1024
    hop_samples: int = 256
    factor_count: int = 6
    kernel_frames: int = 8
    iterations: int = 48
    seed: int = 161

    def __post_init__(self) -> None:
        if (
            self.fft_samples < 64
            or self.fft_samples & (self.fft_samples - 1)
        ):
            raise ValueError("convolutive field FFT must be a power of two")
        if not 1 <= self.hop_samples <= self.fft_samples // 2:
            raise ValueError("convolutive field hop exceeds overlap bound")
        if not 2 <= self.factor_count <= 32:
            raise ValueError("convolutive field factor count exceeds bounds")
        if not 2 <= self.kernel_frames <= 64:
            raise ValueError("convolutive field kernel depth exceeds bounds")
        if not 1 <= self.iterations <= 512:
            raise ValueError("convolutive field iteration count exceeds bounds")


@dataclass(frozen=True)
class ConvolutiveAnonymousField:
    """Anonymous additive proposals plus one exact mixture-domain Truth."""

    factors: tuple[np.ndarray, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    spectral_kernels: np.ndarray
    activation_field: np.ndarray
    report: dict


def _shift_activation(
    activations: np.ndarray,
    lag: int,
) -> np.ndarray:
    """Delay finite activations without wrapping the end into the beginning."""

    shifted = np.zeros_like(activations)
    if lag == 0:
        shifted[...] = activations
    elif lag < activations.shape[1]:
        shifted[:, lag:] = activations[:, :-lag]
    return shifted


def reconstruct_convolutive_magnitude(
    kernels: np.ndarray,
    activations: np.ndarray,
) -> np.ndarray:
    """Render `sum_l W_l @ shift(H, l)` for one finite CNMF state."""

    if (
        kernels.ndim != 3
        or activations.ndim != 2
        or kernels.shape[1] != activations.shape[0]
    ):
        raise ValueError("convolutive field geometry is inconsistent")
    rendered = np.zeros(
        (kernels.shape[0], activations.shape[1]),
        dtype=np.float64,
    )
    for lag in range(kernels.shape[2]):
        rendered += (
            kernels[:, :, lag] @ _shift_activation(activations, lag)
        )
    return rendered


def factor_convolutive_magnitude(
    magnitude: np.ndarray,
    *,
    factor_count: int,
    kernel_frames: int,
    iterations: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Fit a deterministic bounded Euclidean CNMF proposal."""

    source = np.asarray(magnitude, dtype=np.float64)
    if (
        source.ndim != 2
        or source.shape[0] == 0
        or source.shape[1] < kernel_frames
        or np.any(source < 0.0)
    ):
        raise ValueError("convolutive magnitude source is invalid")
    epsilon = 1.0e-9
    rng = np.random.default_rng(seed)
    scale = max(float(np.mean(source)), epsilon)
    kernels = rng.uniform(
        0.5,
        1.5,
        (source.shape[0], factor_count, kernel_frames),
    )
    kernels *= scale / kernel_frames
    activations = rng.uniform(
        0.5,
        1.5,
        (factor_count, source.shape[1]),
    )

    for _ in range(iterations):
        # H[k, q] contributes through every W[:, k, l] to column q + l.
        rendered = reconstruct_convolutive_magnitude(kernels, activations)
        numerator_h = np.zeros_like(activations)
        denominator_h = np.zeros_like(activations)
        for lag in range(kernel_frames):
            width = source.shape[1] - lag
            if width <= 0:
                break
            numerator_h[:, :width] += (
                kernels[:, :, lag].T @ source[:, lag:]
            )
            denominator_h[:, :width] += (
                kernels[:, :, lag].T @ rendered[:, lag:]
            )
        activations *= numerator_h / np.maximum(denominator_h, epsilon)

        # Every temporal kernel slice uses the identical finite support as the
        # renderer, avoiding the circular match defect rejected by R-160.
        rendered = reconstruct_convolutive_magnitude(kernels, activations)
        for lag in range(kernel_frames):
            width = source.shape[1] - lag
            if width <= 0:
                break
            active = activations[:, :width]
            kernels[:, :, lag] *= (
                source[:, lag:] @ active.T
            ) / np.maximum(
                rendered[:, lag:] @ active.T,
                epsilon,
            )

        # Remove scale ambiguity once per iteration for stable evidence.
        norms = np.maximum(
            np.sum(kernels, axis=(0, 2)),
            epsilon,
        )
        kernels /= norms[None, :, None]
        activations *= norms[:, None]

    rendered = reconstruct_convolutive_magnitude(kernels, activations)
    relative_error = float(
        np.linalg.norm(source - rendered)
        / max(np.linalg.norm(source), epsilon)
    )
    return kernels, activations, relative_error


def infer_convolutive_anonymous_fields(
    samples: np.ndarray,
    *,
    sample_rate: int,
    language: ConvolutiveAnonymousLanguage,
) -> ConvolutiveAnonymousField:
    """Infer phase-preserving cross-channel fields and retain exact Truth."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("convolutive fields require frame-major PCM16")
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
    kernels, activations, relative_error = factor_convolutive_magnitude(
        magnitude,
        factor_count=language.factor_count,
        kernel_frames=language.kernel_frames,
        iterations=language.iterations,
        seed=language.seed,
    )

    contributions = np.zeros(
        (
            language.factor_count,
            magnitude.shape[0],
            magnitude.shape[1],
        ),
        dtype=np.float64,
    )
    for factor_index in range(language.factor_count):
        for lag in range(language.kernel_frames):
            shifted = _shift_activation(
                activations[factor_index : factor_index + 1],
                lag,
            )[0]
            contributions[factor_index] += (
                kernels[:, factor_index, lag, None] * shifted[None, :]
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
        raise RuntimeError("convolutive anonymous-field identity failed")
    kernels.flags.writeable = False
    activations.flags.writeable = False
    return ConvolutiveAnonymousField(
        tuple(factors),
        prediction,
        truth,
        reconstruction,
        kernels,
        activations,
        {
            "schema": "resonith-r161-convolutive-anonymous-field-1",
            "status": "encoder-side proposer; no convolutive syntax admitted",
            "semantic_labels": False,
            "shared_cross_channel_masks": True,
            "mixture_phase_preserved": True,
            "finite_non_circular_kernel": True,
            "factor_count": language.factor_count,
            "kernel_frames": language.kernel_frames,
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
