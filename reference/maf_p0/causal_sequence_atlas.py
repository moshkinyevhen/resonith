"""R-171 exact suffix-automaton atlas for canonical causal event streams."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from .coherent_partial_bundle import (
    CausalLaneObservation,
    CoherentPartialBasis,
)


@dataclass(frozen=True, order=True)
class CausalEvent:
    """One anonymous causal-state observation on the continuous timeline."""

    time: int
    basis_state: int
    pitch_q: int
    phase_q: int
    gain_q: int
    envelope_q: int
    resonator_q: int
    route_q: tuple[int, ...] = ()


@dataclass(frozen=True)
class CausalAtlasLanguage:
    """Finite exact event grammar declared by an evidence generation."""

    minimum_sequence_events: int = 3
    minimum_occurrences: int = 2
    phase_modulus: int = 1 << 16
    maximum_reported_occurrence_positions: int = 128

    def __post_init__(self) -> None:
        if (
            not 2 <= self.minimum_sequence_events <= 4096
            or not 2 <= self.minimum_occurrences <= 65535
            or self.phase_modulus <= 1
            or not 2
            <= self.maximum_reported_occurrence_positions
            <= 65535
        ):
            raise ValueError("invalid causal sequence atlas language")


@dataclass(frozen=True)
class CanonicalCausalStream:
    """One exact finite canonicalization of the same event ledger."""

    mode: str
    event_origin_offset: int
    tokens: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class CausalSequenceCandidate:
    """One suffix-automaton end-position class and all its motif lengths."""

    mode: str
    minimum_event_count: int
    maximum_event_count: int
    occurrence_count: int
    maximum_length_occurrence_event_starts: tuple[int, ...]


@dataclass(frozen=True)
class CausalSequenceAtlas:
    """All exact canonical streams and compressed repeated-sequence classes."""

    streams: tuple[CanonicalCausalStream, ...]
    candidates: tuple[CausalSequenceCandidate, ...]
    report: dict


@dataclass(frozen=True)
class MultiLaneCausalSequenceAtlas:
    """Independent exact atlases for every separately owned causal lane."""

    lanes: dict[str, CausalSequenceAtlas]
    factorized_laws: dict[str, CausalSequenceAtlas]
    report: dict


def causal_events_from_partial_bases(
    bases: tuple[CoherentPartialBasis, ...],
    *,
    hop_samples: int,
    phase_modulus: int = 1 << 16,
    pitch_step_cents: float = 1.0,
    gain_step_db: float = 1.0 / 256.0,
    envelope_bins: int = 32768,
) -> tuple[CausalEvent, ...]:
    """Convert analytic partial observations into canonical causal events."""

    if (
        hop_samples <= 0
        or phase_modulus <= 1
        or pitch_step_cents <= 0.0
        or gain_step_db <= 0.0
        or envelope_bins <= 1
    ):
        raise ValueError("invalid partial-to-event timeline")
    events = []
    for basis_state, basis in enumerate(bases):
        for observation in basis.observations:
            events.append(
                CausalEvent(
                    time=observation.frame_index * hop_samples,
                    basis_state=basis_state,
                    pitch_q=int(round(
                        1200.0
                        * math.log2(max(observation.fundamental_hz, 1.0e-9))
                        / pitch_step_cents
                    )),
                    phase_q=int(round(
                        (
                            observation.phase_anchor / (2.0 * math.pi)
                            % 1.0
                        )
                        * phase_modulus
                    ))
                    % phase_modulus,
                    gain_q=int(round(
                        20.0
                        * math.log10(max(observation.gain, 1.0e-12))
                        / gain_step_db
                    )),
                    envelope_q=int(round(
                        observation.harmonic_fraction * envelope_bins
                    )),
                    resonator_q=basis_state,
                    route_q=(),
                )
            )
    events.sort()
    # Multiple analytic hypotheses may share one frame. The R-171 first layer
    # retains the strongest deterministic ordering while later multi-lane
    # ledgers use explicit same-time subevents.
    unique = []
    occupied_times = set()
    for event in events:
        if event.time in occupied_times:
            continue
        occupied_times.add(event.time)
        unique.append(event)
    return tuple(unique)


def causal_events_from_lane_observations(
    observations: dict[str, tuple[CausalLaneObservation, ...]],
    *,
    hop_samples: int,
    phase_modulus: int = 1 << 16,
    pitch_step_cents: float = 5.0,
    gain_step_db: float = 0.25,
    envelope_bins: int = 256,
    resonator_step_cents: float = 25.0,
    route_gain_step_db: float = 0.25,
) -> dict[str, tuple[CausalEvent, ...]]:
    """Quantize every causal lane into its own exact finite event language."""

    if (
        hop_samples <= 0
        or phase_modulus <= 1
        or pitch_step_cents <= 0.0
        or gain_step_db <= 0.0
        or envelope_bins <= 1
        or resonator_step_cents <= 0.0
        or route_gain_step_db <= 0.0
    ):
        raise ValueError("invalid all-lane causal event quantization")
    lane_events = {}
    for lane_index, (lane_name, lane_rows) in enumerate(
        sorted(observations.items())
    ):
        events = []
        for row in lane_rows:
            route = []
            if len(row.route_gain_db) > 1:
                for route_gain, route_phase in zip(
                    row.route_gain_db,
                    row.route_phase,
                    strict=True,
                ):
                    route.extend(
                        (
                            int(round(route_gain / route_gain_step_db)),
                            int(round(
                                (
                                    route_phase / (2.0 * math.pi)
                                    % 1.0
                                )
                                * phase_modulus
                            ))
                            % phase_modulus,
                        )
                    )
            events.append(
                CausalEvent(
                    time=row.frame_index * hop_samples,
                    basis_state=lane_index,
                    pitch_q=int(round(
                        1200.0
                        * math.log2(
                            max(row.spectral_centroid_hz, 1.0e-9)
                        )
                        / pitch_step_cents
                    )),
                    phase_q=int(round(
                        (
                            row.phase_anchor / (2.0 * math.pi)
                            % 1.0
                        )
                        * phase_modulus
                    ))
                    % phase_modulus,
                    gain_q=int(round(
                        20.0
                        * math.log10(max(row.gain, 1.0e-12))
                        / gain_step_db
                    )),
                    envelope_q=int(round(
                        min(max(row.spectral_flatness, 0.0), 1.0)
                        * envelope_bins
                    )),
                    resonator_q=int(round(
                        1200.0
                        * math.log2(
                            max(row.spectral_spread_hz, 1.0e-9)
                        )
                        / resonator_step_cents
                    )),
                    route_q=tuple(route),
                )
            )
        lane_events[lane_name] = tuple(events)
    return lane_events


def project_causal_events(
    events: tuple[CausalEvent, ...],
    law: str,
) -> tuple[CausalEvent, ...]:
    """Keep one causal law and timeline while neutralizing unrelated state."""

    if law not in {
        "timing",
        "pitch",
        "phase",
        "gain",
        "envelope",
        "resonator",
        "route",
    }:
        raise ValueError(f"unsupported causal law projection: {law}")
    return tuple(
        CausalEvent(
            time=event.time,
            basis_state=0,
            pitch_q=event.pitch_q if law == "pitch" else 0,
            phase_q=event.phase_q if law == "phase" else 0,
            gain_q=event.gain_q if law == "gain" else 0,
            envelope_q=event.envelope_q if law == "envelope" else 0,
            resonator_q=(
                event.resonator_q if law == "resonator" else 0
            ),
            route_q=event.route_q if law == "route" else (),
        )
        for event in events
    )


def factorized_causal_event_laws(
    lane_events: dict[str, tuple[CausalEvent, ...]],
) -> dict[str, tuple[CausalEvent, ...]]:
    """Return all independent R-173 causal-law event projections."""

    result = {}
    for lane_name, events in sorted(lane_events.items()):
        for law in (
            "timing",
            "pitch",
            "phase",
            "gain",
            "envelope",
            "resonator",
            "route",
        ):
            if lane_name == "stochastic" and law == "phase":
                continue
            result[f"{lane_name}/{law}"] = project_causal_events(
                events,
                law,
            )
    return result


@dataclass
class _SuffixState:
    maximum_length: int = 0
    suffix_link: int = -1
    transitions: dict[tuple[int, ...], int] = field(default_factory=dict)
    occurrence_count: int = 0
    end_positions: list[int] = field(default_factory=list)


def _phase_delta(current: int, previous: int, modulus: int) -> int:
    delta = (int(current) - int(previous)) % modulus
    half = modulus // 2
    if delta > half:
        delta -= modulus
    return delta


def _route_delta(
    current: tuple[int, ...],
    previous: tuple[int, ...],
) -> tuple[int, ...]:
    width = max(len(current), len(previous))
    return tuple(
        (current[index] if index < len(current) else 0)
        - (previous[index] if index < len(previous) else 0)
        for index in range(width)
    )


def canonicalize_causal_events(
    events: tuple[CausalEvent, ...],
    *,
    phase_modulus: int,
) -> tuple[CanonicalCausalStream, ...]:
    """Build literal, offset-invariant, and affine-invariant exact streams."""

    if not events:
        return ()
    if any(
        event.time < 0
        or (index and event.time <= events[index - 1].time)
        for index, event in enumerate(events)
    ):
        raise ValueError("causal events must have strictly increasing time")

    literal = tuple(
        (
            event.time,
            event.basis_state,
            event.pitch_q,
            event.phase_q % phase_modulus,
            event.gain_q,
            event.envelope_q,
            event.resonator_q,
            len(event.route_q),
            *event.route_q,
        )
        for event in events
    )
    offset_tokens = []
    first_differences = []
    for previous, current in zip(events, events[1:]):
        delta = (
            current.time - previous.time,
            previous.basis_state,
            current.basis_state,
            current.pitch_q - previous.pitch_q,
            _phase_delta(current.phase_q, previous.phase_q, phase_modulus),
            current.gain_q - previous.gain_q,
            current.envelope_q - previous.envelope_q,
            current.resonator_q - previous.resonator_q,
            *_route_delta(current.route_q, previous.route_q),
        )
        offset_tokens.append(delta)
        first_differences.append(delta)

    affine_tokens = []
    for previous, current in zip(
        first_differences,
        first_differences[1:],
    ):
        width = max(len(previous), len(current))
        padded_previous = previous + (0,) * (width - len(previous))
        padded_current = current + (0,) * (width - len(current))
        affine_tokens.append(
            (
                padded_current[1],
                padded_current[2],
                *(
                    padded_current[index] - padded_previous[index]
                    for index in range(width)
                    if index not in (1, 2)
                ),
            )
        )
    return (
        CanonicalCausalStream("literal", 0, literal),
        CanonicalCausalStream(
            "constant-offset/first-difference",
            1,
            tuple(offset_tokens),
        ),
        CanonicalCausalStream(
            "bounded-second-difference",
            2,
            tuple(affine_tokens),
        ),
    )


def _suffix_automaton(
    tokens: tuple[tuple[int, ...], ...],
    *,
    maximum_positions: int,
) -> tuple[list[_SuffixState], int]:
    states = [_SuffixState()]
    last = 0
    prefix_states: list[int] = []
    for position, token in enumerate(tokens):
        current = len(states)
        states.append(
            _SuffixState(
                maximum_length=states[last].maximum_length + 1,
                occurrence_count=1,
                end_positions=[position],
            )
        )
        prefix_states.append(current)
        predecessor = last
        while (
            predecessor >= 0
            and token not in states[predecessor].transitions
        ):
            states[predecessor].transitions[token] = current
            predecessor = states[predecessor].suffix_link
        if predecessor < 0:
            states[current].suffix_link = 0
        else:
            target = states[predecessor].transitions[token]
            if (
                states[predecessor].maximum_length + 1
                == states[target].maximum_length
            ):
                states[current].suffix_link = target
            else:
                clone = len(states)
                states.append(
                    _SuffixState(
                        maximum_length=(
                            states[predecessor].maximum_length + 1
                        ),
                        suffix_link=states[target].suffix_link,
                        transitions=dict(states[target].transitions),
                    )
                )
                while (
                    predecessor >= 0
                    and states[predecessor].transitions.get(token) == target
                ):
                    states[predecessor].transitions[token] = clone
                    predecessor = states[predecessor].suffix_link
                states[target].suffix_link = clone
                states[current].suffix_link = clone
        last = current

    # Prefix states retain exact end positions. Propagation along suffix links
    # computes end-position equivalence classes without enumerating substrings.
    ordered = sorted(
        range(1, len(states)),
        key=lambda index: states[index].maximum_length,
        reverse=True,
    )
    for state_index in ordered:
        state = states[state_index]
        link = state.suffix_link
        if link < 0:
            continue
        states[link].occurrence_count += state.occurrence_count
        if len(states[link].end_positions) < maximum_positions:
            merged = sorted(
                set(
                    states[link].end_positions
                    + state.end_positions[
                        : maximum_positions
                        - len(states[link].end_positions)
                    ]
                )
            )
            states[link].end_positions = merged[:maximum_positions]
    transition_count = sum(len(state.transitions) for state in states)
    return states, transition_count


def build_causal_sequence_atlas(
    events: tuple[CausalEvent, ...],
    *,
    language: CausalAtlasLanguage = CausalAtlasLanguage(),
) -> CausalSequenceAtlas:
    """Index all repeated substrings of every declared canonical stream."""

    streams = canonicalize_causal_events(
        events,
        phase_modulus=language.phase_modulus,
    )
    candidates: list[CausalSequenceCandidate] = []
    stream_reports = []
    covered_length_intervals = 0
    covered_candidate_lengths = 0
    for stream in streams:
        states, transition_count = _suffix_automaton(
            stream.tokens,
            maximum_positions=(
                language.maximum_reported_occurrence_positions
            ),
        )
        stream_candidate_count = 0
        for state_index in range(1, len(states)):
            state = states[state_index]
            if state.occurrence_count < language.minimum_occurrences:
                continue
            minimum_token_count = (
                states[state.suffix_link].maximum_length + 1
            )
            maximum_token_count = state.maximum_length
            minimum_event_count = (
                minimum_token_count + stream.event_origin_offset
            )
            maximum_event_count = (
                maximum_token_count + stream.event_origin_offset
            )
            minimum_event_count = max(
                minimum_event_count,
                language.minimum_sequence_events,
            )
            if maximum_event_count < minimum_event_count:
                continue
            starts = tuple(
                sorted(
                    {
                        end
                        - maximum_token_count
                        + 1
                        for end in state.end_positions
                        if end - maximum_token_count + 1 >= 0
                    }
                )
            )
            candidates.append(
                CausalSequenceCandidate(
                    mode=stream.mode,
                    minimum_event_count=minimum_event_count,
                    maximum_event_count=maximum_event_count,
                    occurrence_count=state.occurrence_count,
                    maximum_length_occurrence_event_starts=starts,
                )
            )
            stream_candidate_count += 1
            covered_length_intervals += 1
            covered_candidate_lengths += (
                maximum_event_count - minimum_event_count + 1
            )
        stream_reports.append(
            {
                "mode": stream.mode,
                "event_origin_offset": stream.event_origin_offset,
                "token_count": len(stream.tokens),
                "suffix_state_count": len(states),
                "suffix_transition_count": transition_count,
                "repeated_end_position_class_count": (
                    stream_candidate_count
                ),
            }
        )
    candidates.sort(
        key=lambda candidate: (
            candidate.mode,
            -candidate.maximum_event_count,
            -candidate.occurrence_count,
            candidate.maximum_length_occurrence_event_starts,
        )
    )
    return CausalSequenceAtlas(
        streams=streams,
        candidates=tuple(candidates),
        report={
            "schema": "resonith-r171-causal-sequence-atlas-1",
            "status": (
                "exact declared canonical event-language index; "
                "complete stream RDO pending"
            ),
            "event_count": len(events),
            "every_event_origin_indexed": True,
            "preferred_length_sampling": False,
            "covered_repeated_length_interval_count": (
                covered_length_intervals
            ),
            "covered_repeated_candidate_length_count": (
                covered_candidate_lengths
            ),
            "candidate_class_count": len(candidates),
            "streams": stream_reports,
        },
    )


def build_multilane_causal_sequence_atlas(
    lane_events: dict[str, tuple[CausalEvent, ...]],
    *,
    language: CausalAtlasLanguage = CausalAtlasLanguage(),
) -> MultiLaneCausalSequenceAtlas:
    """Index each causal lane independently and preserve simultaneous events."""

    joint_atlases = {
        lane_name: build_causal_sequence_atlas(
            events,
            language=language,
        )
        for lane_name, events in sorted(lane_events.items())
    }
    factorized_laws = {
        law_name: build_causal_sequence_atlas(
            events,
            language=language,
        )
        for law_name, events in factorized_causal_event_laws(
            lane_events
        ).items()
    }
    return MultiLaneCausalSequenceAtlas(
        lanes=joint_atlases,
        factorized_laws=factorized_laws,
        report={
            "schema": "resonith-r173-factorized-law-atlas-1",
            "status": (
                "exact per-lane/per-law sequence discovery; synchronized "
                "grammar and complete stream RDO pending"
            ),
            "single_primary_lane_ownership": True,
            "simultaneous_lane_events_preserved": True,
            "unrelated_laws_do_not_prune_candidates": True,
            "stochastic_realization_phase_is_not_predictive_state": True,
            "one_final_mixture_truth": True,
            "lane_count": len(joint_atlases),
            "factorized_law_count": len(factorized_laws),
            "event_count": sum(
                atlas.report["event_count"]
                for atlas in joint_atlases.values()
            ),
            "joint_candidate_class_count": sum(
                atlas.report["candidate_class_count"]
                for atlas in joint_atlases.values()
            ),
            "factorized_candidate_class_count": sum(
                atlas.report["candidate_class_count"]
                for atlas in factorized_laws.values()
            ),
            "candidate_class_count": sum(
                atlas.report["candidate_class_count"]
                for atlas in factorized_laws.values()
            ),
            "lanes": {
                lane_name: {
                    "event_count": atlas.report["event_count"],
                    "candidate_class_count": (
                        atlas.report["candidate_class_count"]
                    ),
                    "covered_repeated_candidate_length_count": (
                        atlas.report[
                            "covered_repeated_candidate_length_count"
                        ]
                    ),
                }
                for lane_name, atlas in joint_atlases.items()
            },
            "factorized_laws": {
                law_name: {
                    "event_count": atlas.report["event_count"],
                    "candidate_class_count": (
                        atlas.report["candidate_class_count"]
                    ),
                    "covered_repeated_candidate_length_count": (
                        atlas.report[
                            "covered_repeated_candidate_length_count"
                        ]
                    ),
                }
                for law_name, atlas in factorized_laws.items()
            },
        },
    )
