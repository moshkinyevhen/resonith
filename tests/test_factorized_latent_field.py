from __future__ import annotations

import numpy as np

from reference.maf_p0.anonymous_spectral_factor import (
    AnonymousSpectralLanguage,
)
from reference.maf_p0.factorized_latent_field import (
    infer_factorized_latent_field,
)
from reference.maf_p0.latent_source_field import LatentSourceLanguage


def test_factorized_lspf_uses_one_final_mixture_truth() -> None:
    sample_rate = 8000
    frame = np.arange(sample_rate * 2)
    carrier = np.sin(2.0 * np.pi * 173.0 * frame / sample_rate)
    modulation = 0.55 + 0.35 * np.sin(
        2.0 * np.pi * 2.0 * frame / sample_rate
    )
    interference = np.sin(
        2.0 * np.pi * 911.0 * frame / sample_rate + 0.31
    )
    samples = np.clip(
        np.rint(8500.0 * modulation * carrier + 2400.0 * interference),
        -32768,
        32767,
    ).astype(np.int16)[:, None]

    result = infer_factorized_latent_field(
        samples,
        sample_rate=sample_rate,
        factor_language=AnonymousSpectralLanguage(
            fft_samples=256,
            hop_samples=64,
            factor_count=2,
            iterations=16,
        ),
        field_language=LatentSourceLanguage(
            scales=(128, 256),
            origin_hop=128,
            minimum_occurrences=3,
            maximum_components=1,
            maximum_cluster_members=24,
            maximum_lag=4,
            minimum_spectral_similarity=0.94,
            maximum_normalized_correction=0.35,
        ),
    )

    assert result.report["semantic_labels"] is False
    assert result.report["factor_count"] == 2
    assert result.report["one_final_mixture_truth"]
    assert result.report["exact_integer_reconstruction"]
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )
