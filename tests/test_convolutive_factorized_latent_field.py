from __future__ import annotations

import numpy as np

from reference.maf_p0.convolutive_anonymous_field import (
    ConvolutiveAnonymousLanguage,
)
from reference.maf_p0.convolutive_factorized_latent_field import (
    infer_convolutive_factorized_latent_field,
)
from reference.maf_p0.latent_source_field import LatentSourceLanguage


def test_convolutive_factorized_lspf_has_one_final_truth() -> None:
    sample_rate = 8000
    frame = np.arange(sample_rate * 2)
    phrase = np.sin(2.0 * np.pi * 191.0 * frame / sample_rate)
    delayed = np.concatenate((np.zeros(73), phrase[:-73]))
    envelope = 0.65 + 0.25 * np.sin(
        2.0 * np.pi * 1.7 * frame / sample_rate
    )
    samples = np.clip(
        np.rint(7600.0 * envelope * phrase + 2600.0 * delayed),
        -32768,
        32767,
    ).astype(np.int16)[:, None]

    result = infer_convolutive_factorized_latent_field(
        samples,
        sample_rate=sample_rate,
        factor_language=ConvolutiveAnonymousLanguage(
            fft_samples=256,
            hop_samples=64,
            factor_count=2,
            kernel_frames=4,
            iterations=12,
        ),
        field_language=LatentSourceLanguage(
            scales=(128, 256),
            origin_hop=128,
            minimum_occurrences=3,
            maximum_components=1,
            maximum_cluster_members=24,
            maximum_lag=4,
            minimum_spectral_similarity=0.92,
            maximum_normalized_correction=0.40,
        ),
    )

    assert result.report["semantic_labels"] is False
    assert result.report["factor_count"] == 2
    assert result.report["one_final_mixture_truth"]
    assert result.report["exact_integer_reconstruction"]
    assert result.proposer.report["finite_non_circular_kernel"]
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )
