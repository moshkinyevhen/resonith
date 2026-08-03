from __future__ import annotations

from reference.maf_p0.sparse_motif_grammar import (
    ComponentTokenObservation,
    SparseMotifLanguage,
    SparsePathLanguage,
    decode_sparse_motif_events,
    discover_and_pack_sparse_pair_motifs,
    discover_and_pack_sparse_path_motifs,
)


def _key(
    item: ComponentTokenObservation,
) -> tuple[int, int, int, int, int, int, int, int]:
    return (
        item.layer_hypothesis_id,
        item.token_id,
        item.onset_frame,
        item.support_frames,
        item.channel,
        item.gain_q15,
        item.phase_q16,
        item.source_step_q16,
    )


def test_discontiguous_cross_channel_pair_uses_affine_gap_law() -> None:
    observations = []
    observation_id = 0
    for occurrence in range(24):
        anchor = 1000 * occurrence + 17
        base_gain = 18000 + 37 * occurrence
        observations.append(
            ComponentTokenObservation(
                observation_id,
                3,
                0,
                anchor,
                160,
                occurrence % 2,
                base_gain,
                211 * occurrence,
                65536 + 8 * occurrence,
            )
        )
        observation_id += 1
        # This unrelated event lies between the two motif steps and must not
        # prevent A -> gap -> B from becoming one sparse definition.
        observations.append(
            ComponentTokenObservation(
                observation_id,
                3,
                99,
                anchor + 71,
                23,
                1,
                -9000 + occurrence,
            )
        )
        observation_id += 1
        observations.append(
            ComponentTokenObservation(
                observation_id,
                3,
                7,
                anchor + 200 + 2 * occurrence,
                96,
                1 - occurrence % 2,
                base_gain + 512,
                211 * occurrence + 1024,
                65536 + 8 * occurrence + 16,
            )
        )
        observation_id += 1

    result = discover_and_pack_sparse_pair_motifs(
        observations,
        language=SparseMotifLanguage(
            minimum_occurrences=8,
            maximum_gap_frames=512,
            gap_bucket_frames=256,
        ),
    )

    assert result.selected_kind == "sparse-pair-motif"
    assert result.report["selected_pair_count"] == 24
    assert result.report["saving_percent"] > 15.0
    assert result.report["exact_event_roundtrip"]
    assert result.definitions[0].first_token_id == 0
    assert result.definitions[0].second_token_id == 7
    assert "affine" in result.definitions[0].law_kinds
    assert [_key(item) for item in decode_sparse_motif_events(
        result.packed_stream
    )] == sorted(_key(item) for item in observations)


def test_sparse_motif_falls_back_when_definition_cannot_amortize() -> None:
    observations = [
        ComponentTokenObservation(0, 0, 2, 13, 32, 0, 32768),
        ComponentTokenObservation(1, 0, 8, 101, 48, 0, 31900),
    ]

    result = discover_and_pack_sparse_pair_motifs(
        observations,
        language=SparseMotifLanguage(minimum_occurrences=2),
    )

    assert result.selected_kind == "flat-events"
    assert not result.definitions
    assert result.report["saving_percent"] == 0.0
    assert [_key(item) for item in result.decoded_observations] == sorted(
        _key(item) for item in observations
    )


def test_long_sparse_path_skips_unrelated_events_between_every_step() -> None:
    observations = []
    observation_id = 0
    for occurrence in range(18):
        anchor = 2000 * occurrence + 23
        for token, onset, support, channel, gain, phase in (
            (4, anchor, 192, occurrence % 2, 17000 + 23 * occurrence, 0),
            (91, anchor + 37, 29, 0, -7300 + occurrence, 17),
            (
                8,
                anchor + 200 + occurrence,
                144,
                1 - occurrence % 2,
                17512 + 23 * occurrence,
                1024,
            ),
            (92, anchor + 311, 31, 1, 5300 - occurrence, 19),
            (
                15,
                anchor + 460 + 2 * occurrence,
                96,
                occurrence % 2,
                18024 + 23 * occurrence,
                2048,
            ),
        ):
            observations.append(
                ComponentTokenObservation(
                    observation_id,
                    5,
                    token,
                    onset,
                    support,
                    channel,
                    gain,
                    phase,
                    65536 + 4 * occurrence,
                )
            )
            observation_id += 1

    result = discover_and_pack_sparse_path_motifs(
        observations,
        language=SparsePathLanguage(
            minimum_occurrences=8,
            minimum_steps=3,
            maximum_steps=3,
            maximum_gap_frames=600,
            gap_bucket_frames=128,
            maximum_successors_per_step=8,
        ),
    )

    assert result.selected_kind == "sparse-path-motif"
    assert result.report["selected_path_count"] == 18
    assert result.report["selected_step_count"] == 3
    assert result.report["saving_percent"] > 15.0
    assert result.report["exact_event_roundtrip"]
    assert result.definitions[0].token_ids == (4, 8, 15)
    assert "affine" in result.definitions[0].law_kinds
    assert [_key(item) for item in result.decoded_observations] == sorted(
        _key(item) for item in observations
    )
