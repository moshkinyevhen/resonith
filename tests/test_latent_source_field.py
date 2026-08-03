from __future__ import annotations

import numpy as np

from reference.maf_p0.latent_source_field import (
    LatentSourceLanguage,
    _fit_basis,
    infer_latent_source_pattern_field,
)
from reference.maf_p0.sparse_motif_grammar import (
    SparseMotifLanguage,
    SparsePathLanguage,
    pack_latent_field_event_ledger,
)


def test_short_layer_is_found_but_rejected_when_metadata_cannot_amortize() -> None:
    rng = np.random.default_rng(159)
    basis = np.rint(
        9000.0 * np.sin(
            2.0 * np.pi * (
                0.031 * np.arange(64)
                + 0.00031 * np.arange(64) ** 2
            )
        )
    ).astype(np.int16)
    samples = rng.integers(-23, 24, size=(640, 1), dtype=np.int16)
    starts = (17, 109, 203, 301, 397, 509)
    for occurrence, start in enumerate(starts):
        samples[start : start + basis.size, 0] = np.clip(
            samples[start : start + basis.size, 0].astype(np.int32)
                + basis,
            -32768,
            32767,
        ).astype(np.int16)
        # Every complete mixed observation is different, while fewer than
        # half of the observations contaminate any one Basis coordinate.
        contaminated = (
            np.arange(occurrence * 9, occurrence * 9 + 13) % basis.size
        )
        samples[start + contaminated, 0] = np.clip(
            samples[start + contaminated, 0].astype(np.int32)
                + rng.integers(-1700, 1701, size=contaminated.size),
            -32768,
            32767,
        ).astype(np.int16)

    result = infer_latent_source_pattern_field(
        samples,
        language=LatentSourceLanguage(
            scales=(64,),
            origin_hop=1,
            minimum_occurrences=4,
            maximum_components=2,
            maximum_cluster_members=32,
            maximum_lag=4,
            minimum_spectral_similarity=0.96,
            maximum_normalized_correction=0.20,
        ),
    )

    assert result.report["direct_exact_group_count"] == 0
    assert result.report["fitted_candidate_count"] >= 1
    assert result.report["best_candidate_byte_delta"] > 0
    assert result.report["latent_component_count"] == 0
    assert result.report["exact_integer_reconstruction"]
    assert np.array_equal(result.reconstruction, samples.astype(np.int64))


def test_long_transformed_layer_amortizes_basis_and_sparse_gap_map() -> None:
    rng = np.random.default_rng(160)
    index = np.arange(128)
    basis = np.rint(
        7000.0 * np.sin(
            2.0 * np.pi * (
                0.021 * index + 0.000037 * index**2
            )
        )
        + 2200.0 * np.sin(2.0 * np.pi * 0.113 * index)
    ).astype(np.int16)
    samples = rng.integers(-19, 20, size=(1760, 1), dtype=np.int16)
    starts = tuple(16 + 168 * occurrence for occurrence in range(10))
    gains_q15 = (
        19000,
        23000,
        27000,
        31000,
        35000,
        39000,
        43000,
        37000,
        29000,
        25000,
    )
    for occurrence, (start, gain_q15) in enumerate(
        zip(starts, gains_q15)
    ):
        product = basis.astype(np.int64) * gain_q15
        rendered = np.where(
            product >= 0,
            (product + 16384) // 32768,
            -((-product + 16384) // 32768),
        ).astype(np.int16)
        samples[start : start + basis.size, 0] = np.clip(
            samples[start : start + basis.size, 0].astype(np.int32)
                + rendered,
            -32768,
            32767,
        ).astype(np.int16)
        contaminated = (
            np.arange(occurrence * 11, occurrence * 11 + 11)
            % basis.size
        )
        samples[start + contaminated, 0] = np.clip(
            samples[start + contaminated, 0].astype(np.int32)
                + rng.integers(-140, 141, size=contaminated.size),
            -32768,
            32767,
        ).astype(np.int16)

    result = infer_latent_source_pattern_field(
        samples,
        language=LatentSourceLanguage(
            scales=(128,),
            origin_hop=4,
            minimum_occurrences=6,
            maximum_components=2,
            maximum_cluster_members=12,
            maximum_lag=3,
            minimum_spectral_similarity=0.92,
            maximum_normalized_correction=0.08,
        ),
    )

    assert result.report["direct_exact_group_count"] == 0
    assert result.report["latent_component_count"] == 1
    assert result.report["latent_occurrence_count"] == len(starts)
    assert result.report["event_map_bytes"] <= 6 * len(starts)
    assert result.report["structured_proxy_bytes"] < (
        result.report["direct_proxy_bytes"] * 3 // 4
    )
    assert result.report["exact_integer_reconstruction"]
    assert np.array_equal(result.reconstruction, samples.astype(np.int64))

    ledger = pack_latent_field_event_ledger(
        result,
        pair_language=SparseMotifLanguage(minimum_occurrences=3),
        path_language=SparsePathLanguage(
            minimum_occurrences=3,
            minimum_steps=3,
            maximum_steps=4,
        ),
    )
    assert ledger.report["exact_event_roundtrip"]
    assert ledger.report["observation_count"] == 10
    assert ledger.report["selected_event_bytes"] <= (
        ledger.report["legacy_component_event_map_bytes"]
    )


def test_cross_channel_occurrences_share_one_unnamed_basis() -> None:
    basis = np.asarray(
        [((index * 977 + 331) % 12001) - 6000 for index in range(48)],
        dtype=np.int16,
    )
    samples = np.zeros((360, 2), dtype=np.int16)
    placements = ((0, 11, 1), (1, 79, -1), (0, 151, 1), (1, 227, 1))
    for channel, start, polarity in placements:
        samples[start : start + basis.size, channel] = basis * polarity

    result = infer_latent_source_pattern_field(
        samples,
        language=LatentSourceLanguage(
            scales=(48,),
            origin_hop=1,
            minimum_occurrences=4,
            maximum_components=1,
            maximum_lag=2,
            minimum_spectral_similarity=0.999,
            maximum_normalized_correction=0.001,
        ),
    )

    assert result.report["latent_component_count"] == 1
    channels = {
        occurrence.channel
        for occurrence in result.components[0].occurrences
    }
    assert channels == {0, 1}
    assert np.array_equal(result.reconstruction, samples.astype(np.int64))


def test_latent_alignment_never_wraps_basis_tail_into_its_head() -> None:
    basis = np.asarray([1000, 2000, 3000, 4000, 5000, 6000], dtype=np.int16)
    target = np.asarray([0, 0, 1000, 2000, 3000, 4000], dtype=np.int16)

    lag, gain_q15, rendered, squared_error = _fit_basis(
        basis,
        target,
        maximum_lag=2,
    )

    assert lag == 2
    assert gain_q15 == 32768
    np.testing.assert_array_equal(rendered, target)
    assert squared_error == 0
