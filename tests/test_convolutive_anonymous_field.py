from __future__ import annotations

import numpy as np

from reference.maf_p0.convolutive_anonymous_field import (
    ConvolutiveAnonymousLanguage,
    factor_convolutive_magnitude,
    infer_convolutive_anonymous_fields,
    reconstruct_convolutive_magnitude,
)


def test_convolutive_magnitude_uses_finite_non_wrapping_support() -> None:
    kernels = np.zeros((1, 1, 3), dtype=np.float64)
    kernels[0, 0, 2] = 2.0
    activations = np.zeros((1, 6), dtype=np.float64)
    activations[0, 5] = 7.0

    rendered = reconstruct_convolutive_magnitude(kernels, activations)

    np.testing.assert_array_equal(rendered, np.zeros((1, 6)))


def test_convolutive_factor_fits_a_known_temporal_dictionary() -> None:
    rng = np.random.default_rng(161)
    true_kernels = rng.uniform(0.1, 1.0, (10, 2, 3))
    true_activations = np.zeros((2, 48), dtype=np.float64)
    true_activations[0, (2, 13, 29, 41)] = (1.0, 0.8, 1.2, 0.7)
    true_activations[1, (7, 19, 35)] = (0.9, 1.1, 0.6)
    magnitude = reconstruct_convolutive_magnitude(
        true_kernels,
        true_activations,
    )

    kernels, activations, error = factor_convolutive_magnitude(
        magnitude,
        factor_count=2,
        kernel_frames=3,
        iterations=120,
        seed=161,
    )

    assert kernels.shape == true_kernels.shape
    assert activations.shape == true_activations.shape
    assert error < 0.20


def test_convolutive_audio_proposer_preserves_phase_channels_and_truth() -> None:
    sample_rate = 8000
    frames = np.arange(sample_rate, dtype=np.float64)
    first = 7500.0 * np.sin(2.0 * np.pi * 211.0 * frames / sample_rate)
    second = (
        4200.0
        * (1.0 + 0.4 * np.sin(2.0 * np.pi * 2.0 * frames / sample_rate))
        * np.sin(2.0 * np.pi * 691.0 * frames / sample_rate + 0.53)
    )
    samples = np.stack(
        (first + second, 0.72 * first - 0.48 * second),
        axis=1,
    )
    samples = np.clip(
        np.rint(samples),
        -32768,
        32767,
    ).astype(np.int16)

    result = infer_convolutive_anonymous_fields(
        samples,
        sample_rate=sample_rate,
        language=ConvolutiveAnonymousLanguage(
            fft_samples=256,
            hop_samples=64,
            factor_count=2,
            kernel_frames=4,
            iterations=16,
        ),
    )

    assert len(result.factors) == 2
    assert result.report["semantic_labels"] is False
    assert result.report["shared_cross_channel_masks"]
    assert result.report["mixture_phase_preserved"]
    assert result.report["finite_non_circular_kernel"]
    assert result.report["one_final_time_domain_truth"]
    assert result.report["exact_integer_reconstruction"]
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )
