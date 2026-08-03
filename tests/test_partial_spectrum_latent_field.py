from __future__ import annotations

import numpy as np

from reference.maf_p0.latent_source_field import LatentSourceLanguage
from reference.maf_p0.partial_spectrum_latent_field import (
    infer_partial_spectrum_latent_field,
)


def test_partial_spectrum_field_finds_reuse_hidden_by_high_frequency_changes() -> None:
    rng = np.random.default_rng(160)
    samples = np.zeros((8192, 1), dtype=np.int16)
    phase = np.arange(256)
    basis = np.rint(
        7000.0 * np.sin(2.0 * np.pi * 3.0 * phase / 256.0)
    ).astype(np.int16)
    for occurrence, start in enumerate((256, 1280, 2304, 3328, 4352, 5376)):
        gain_q15 = 24576 + 2048 * occurrence
        rendered_basis = np.rint(
            basis.astype(np.float64) * gain_q15 / 32768.0
        ).astype(np.int16)
        contamination = rng.integers(
            -1800,
            1801,
            size=128,
            dtype=np.int16,
        )
        alternating = np.empty(256, dtype=np.int16)
        alternating[0::2] = contamination
        alternating[1::2] = -contamination
        samples[start : start + 256, 0] = np.clip(
            rendered_basis.astype(np.int32) + alternating.astype(np.int32),
            -32768,
            32767,
        ).astype(np.int16)

    result = infer_partial_spectrum_latent_field(
        samples,
        levels=2,
        language=LatentSourceLanguage(
            scales=(256,),
            origin_hop=64,
            minimum_occurrences=4,
            maximum_components=2,
            maximum_lag=4,
            minimum_spectral_similarity=0.98,
            maximum_normalized_correction=0.08,
        ),
    )

    assert result.report["active_band_count"] >= 1
    assert result.report["latent_occurrence_count"] >= 4
    assert result.report["one_final_time_domain_truth"]
    assert result.report["exact_integer_reconstruction"]
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )
