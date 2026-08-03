from __future__ import annotations

import numpy as np

from reference.maf_p0.causal_sequence_atlas import (
    CausalAtlasLanguage,
    CausalEvent,
    build_causal_sequence_atlas,
    build_multilane_causal_sequence_atlas,
    causal_events_from_lane_observations,
    causal_events_from_partial_bases,
)
from reference.maf_p0.coherent_partial_bundle import (
    CausalLaneObservation,
    CoherentPartialBasis,
    PartialBundleObservation,
)


def _motif(
    start: int,
    *,
    pitch_offset: int,
    gain_offset: int,
    phase_offset: int,
) -> list[CausalEvent]:
    return [
        CausalEvent(
            start,
            0,
            100 + pitch_offset,
            1000 + phase_offset,
            20 + gain_offset,
            5,
            3,
            (8, -2),
        ),
        CausalEvent(
            start + 7,
            7,
            112 + pitch_offset,
            1300 + phase_offset,
            24 + gain_offset,
            6,
            4,
            (9, -1),
        ),
        CausalEvent(
            start + 19,
            2,
            109 + pitch_offset,
            1700 + phase_offset,
            18 + gain_offset,
            4,
            5,
            (7, 0),
        ),
        CausalEvent(
            start + 31,
            5,
            121 + pitch_offset,
            2200 + phase_offset,
            21 + gain_offset,
            8,
            5,
            (6, 1),
        ),
    ]


def test_atlas_finds_transposed_and_regained_sequence_without_length_sampling() -> None:
    events = tuple(
        _motif(0, pitch_offset=0, gain_offset=0, phase_offset=0)
        + _motif(80, pitch_offset=17, gain_offset=9, phase_offset=7000)
        + _motif(170, pitch_offset=-11, gain_offset=-4, phase_offset=15000)
    )
    atlas = build_causal_sequence_atlas(
        events,
        language=CausalAtlasLanguage(
            minimum_sequence_events=3,
            minimum_occurrences=3,
        ),
    )

    transformed = [
        candidate
        for candidate in atlas.candidates
        if candidate.mode == "constant-offset/first-difference"
    ]
    assert transformed
    assert max(candidate.maximum_event_count for candidate in transformed) >= 4
    assert max(candidate.occurrence_count for candidate in transformed) >= 3
    assert atlas.report["every_event_origin_indexed"]
    assert not atlas.report["preferred_length_sampling"]
    assert atlas.report["covered_repeated_candidate_length_count"] > 0


def test_literal_stream_does_not_fake_absolute_transposition_identity() -> None:
    events = tuple(
        _motif(0, pitch_offset=0, gain_offset=0, phase_offset=0)
        + _motif(80, pitch_offset=17, gain_offset=9, phase_offset=7000)
    )
    atlas = build_causal_sequence_atlas(
        events,
        language=CausalAtlasLanguage(
            minimum_sequence_events=3,
            minimum_occurrences=2,
        ),
    )

    literal = [
        candidate
        for candidate in atlas.candidates
        if candidate.mode == "literal"
    ]
    transformed = [
        candidate
        for candidate in atlas.candidates
        if candidate.mode == "constant-offset/first-difference"
    ]
    assert not literal
    assert transformed


def test_partial_observations_become_sample_timed_causal_events() -> None:
    basis = CoherentPartialBasis(
        amplitude_ratios=np.ones(3),
        relative_phases=np.zeros(3),
        observations=(
            PartialBundleObservation(2, 220.0, 10.0, 0.25, 0.8),
            PartialBundleObservation(5, 440.0, 20.0, 0.50, 0.7),
        ),
    )

    events = causal_events_from_partial_bases(
        (basis,),
        hop_samples=64,
    )

    assert [event.time for event in events] == [128, 320]
    assert events[1].pitch_q - events[0].pitch_q == 1200


def test_all_lane_atlas_keeps_simultaneous_events_separate() -> None:
    def row(
        frame_index: int,
        lane: str,
        centroid: float,
        gain: float,
    ) -> CausalLaneObservation:
        return CausalLaneObservation(
            frame_index=frame_index,
            lane=lane,
            gain=gain,
            spectral_centroid_hz=centroid,
            spectral_spread_hz=centroid / 3.0,
            spectral_flatness=0.25,
            phase_anchor=0.1,
            route_gain_db=(0.0, -3.0),
            route_phase=(0.0, 0.5),
        )

    observations = {
        "coherent_harmonic": tuple(
            row(frame, "coherent_harmonic", centroid, gain)
            for frame, centroid, gain in (
                (0, 220.0, 10.0),
                (2, 330.0, 12.0),
                (5, 440.0, 8.0),
                (10, 440.0, 20.0),
                (12, 660.0, 24.0),
                (15, 880.0, 16.0),
            )
        ),
        "stochastic": tuple(
            row(frame, "stochastic", centroid, gain)
            for frame, centroid, gain in (
                (0, 1000.0, 4.0),
                (2, 1200.0, 5.0),
                (5, 900.0, 3.0),
                (10, 1000.0, 8.0),
                (12, 1200.0, 10.0),
                (15, 900.0, 6.0),
            )
        ),
    }
    lane_events = causal_events_from_lane_observations(
        observations,
        hop_samples=64,
    )
    atlas = build_multilane_causal_sequence_atlas(
        lane_events,
        language=CausalAtlasLanguage(
            minimum_sequence_events=3,
            minimum_occurrences=2,
        ),
    )

    assert set(atlas.lanes) == {"coherent_harmonic", "stochastic"}
    assert atlas.report["simultaneous_lane_events_preserved"]
    assert atlas.report["event_count"] == 12
    assert atlas.lanes["coherent_harmonic"].candidates
    assert atlas.lanes["stochastic"].candidates
    assert atlas.factorized_laws["coherent_harmonic/pitch"].candidates
    assert atlas.factorized_laws["stochastic/gain"].candidates


def test_mono_identity_route_is_canonical_empty_state() -> None:
    observation = CausalLaneObservation(
        frame_index=0,
        lane="coherent_harmonic",
        gain=10.0,
        spectral_centroid_hz=220.0,
        spectral_spread_hz=40.0,
        spectral_flatness=0.1,
        phase_anchor=0.2,
        route_gain_db=(0.0,),
        route_phase=(0.0,),
    )

    event = causal_events_from_lane_observations(
        {"coherent_harmonic": (observation,)},
        hop_samples=64,
    )["coherent_harmonic"][0]

    assert event.route_q == ()
