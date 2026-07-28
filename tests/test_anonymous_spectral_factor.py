from __future__ import annotations

import numpy as np

from reference.maf_p0.anonymous_spectral_factor import (
    AnonymousSpectralLanguage,
    infer_anonymous_spectral_factors,
)


def test_anonymous_spectral_factor_preserves_phase_channels_and_exact_truth() -> None:
    sample_rate = 16000
    frames = np.arange(sample_rate, dtype=np.float64)
    first = 8000.0 * np.sin(2.0 * np.pi * 211.0 * frames / sample_rate)
    second = (
        5000.0
        * (1.0 + 0.35 * np.sin(2.0 * np.pi * 3.0 * frames / sample_rate))
        * np.sin(2.0 * np.pi * 733.0 * frames / sample_rate + 0.7)
    )
    samples = np.stack(
        (
            first + second,
            0.7 * first - 0.45 * second,
        ),
        axis=1,
    )
    samples = np.clip(
        np.rint(samples),
        -32768,
        32767,
    ).astype(np.int16)

    result = infer_anonymous_spectral_factors(
        samples,
        sample_rate=sample_rate,
        language=AnonymousSpectralLanguage(
            fft_samples=512,
            hop_samples=128,
            factor_count=3,
            iterations=24,
        ),
    )

    assert len(result.factors) == 3
    assert all(factor.shape == samples.shape for factor in result.factors)
    assert result.report["semantic_labels"] is False
    assert result.report["shared_cross_channel_masks"]
    assert result.report["mixture_phase_preserved"]
    assert result.report["one_final_time_domain_truth"]
    assert result.report["exact_integer_reconstruction"]
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )
