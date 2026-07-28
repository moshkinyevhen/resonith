"""R-187 bounded multi-objective complex-partial path proposals.

The scores in this module are deterministic analyzer heuristics. They are not
entropy estimates, Truth-byte estimates, or codec admission decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

from .complex_partial_analyzer import (
    ComplexPartialObservation,
    ComplexPartialObservationSet,
)


_FAMILY_CONTINUITY = "continuity"
_FAMILY_VALUE = "local-potential"
_FAMILY_WEAK = "protected-weak-line"
_FAMILY_ORDER = {
    _FAMILY_VALUE: 0,
    _FAMILY_CONTINUITY: 1,
    _FAMILY_WEAK: 2,
}


@dataclass(frozen=True)
class ComplexPartialTrackerManifest:
    """Finite R-187 graph, fixed-point score, and top-K bounds."""

    resolution_id: int = 0
    detector_channel: int = -1
    gap_hypotheses: tuple[int, ...] = (1, 2, 4, 8)
    neighbors_per_gap: int = 4
    cycle_offsets: tuple[int, ...] = (-2, -1, 0, 1, 2)
    k_best_per_state_per_family: int = 8
    top_k_per_family: int = 128
    protected_frequency_bands: int = 24
    protected_paths_per_band: int = 2
    minimum_track_observations: int = 4
    maximum_frequency_slope_hz_per_second: float = 5000.0
    maximum_frequency_jump_hz: float = 80.0
    birth_bits: float = 48.0
    death_bits: float = 8.0
    continuation_base_bits: float = 12.0
    score_fraction_bits: int = 8
    score_saturation: int = (1 << 31) - 1
    continuation_reward_units: float = 12.0
    maximum_path_hypotheses: int = 65_536
    exact_set_candidate_limit: int = 20

    def __post_init__(self) -> None:
        if (
            self.resolution_id < 0
            or self.detector_channel < -1
            or not self.gap_hypotheses
            or tuple(sorted(set(self.gap_hypotheses)))
            != self.gap_hypotheses
            or any(gap <= 0 for gap in self.gap_hypotheses)
            or not 1 <= self.neighbors_per_gap <= 16
            or not self.cycle_offsets
            or 0 not in self.cycle_offsets
            or not 1 <= self.k_best_per_state_per_family <= 64
            or not 1 <= self.top_k_per_family <= 4096
            or not 4 <= self.protected_frequency_bands <= 128
            or not 1 <= self.protected_paths_per_band <= 16
            or not 2 <= self.minimum_track_observations <= 65535
            or not 0.0 < self.maximum_frequency_slope_hz_per_second
            or not 0.0 < self.maximum_frequency_jump_hz
            or not 0.0 <= self.birth_bits <= 1024.0
            or not 0.0 <= self.death_bits <= 1024.0
            or not 0.0 <= self.continuation_base_bits <= 1024.0
            or not 0 <= self.score_fraction_bits <= 20
            or not 1024 <= self.score_saturation <= (1 << 62) - 1
            or not 0.0 < self.continuation_reward_units <= 1024.0
            or not 1 <= self.maximum_path_hypotheses <= 1_000_000
            or not 1 <= self.exact_set_candidate_limit <= 24
        ):
            raise ValueError("invalid complex-partial tracker manifest")


@dataclass(frozen=True)
class PartialContinuationHypothesis:
    """One bounded `CONTINUE(m)` alternative against an implicit restart."""

    source_observation: int
    target_observation: int
    gap_hops: int
    cycle_count: int | None
    phase_error_radians: float | None
    frequency_delta_hz: float
    continuity_cost_q: int
    program_cost_bits: float


@dataclass(frozen=True)
class PartialPathHypothesis:
    """One R-187 trajectory proposal with explicitly separated scores."""

    observation_ids: tuple[int, ...]
    cycle_counts: tuple[int | None, ...]
    families: tuple[str, ...]
    continuity_score_q: int
    potential_node_value_q: int
    uncertainty_leakage_penalty_q: int
    program_cost_bits: float
    ownership_conflict_count: int
    mean_phase_error_radians: float | None

    @property
    def local_potential_score_q(self) -> int:
        """Return the dimensionless value-family score, never a bit count."""

        return (
            self.potential_node_value_q
            - self.uncertainty_leakage_penalty_q
            + self.continuity_score_q // 2
        )


@dataclass(frozen=True)
class PartialTrackSet:
    """One disjoint set selected by a bounded analyzer heuristic."""

    paths: tuple[PartialPathHypothesis, ...]
    heuristic_score_q: int
    solver: str
    report: dict


@dataclass(frozen=True)
class ComplexPartialTracking:
    """Finite continuation union and independent top-K path families."""

    observations: tuple[ComplexPartialObservation, ...]
    continuations: tuple[PartialContinuationHypothesis, ...]
    paths: tuple[PartialPathHypothesis, ...]
    selected_set: PartialTrackSet
    report: dict


@dataclass(frozen=True)
class _PathState:
    observation_ids: tuple[int, ...]
    cycle_counts: tuple[int | None, ...]
    continuity_cost_q: int
    potential_node_value_q: int
    uncertainty_leakage_penalty_q: int
    program_cost_bits_without_death: float
    phase_errors: tuple[float, ...]


def _quantize_score(
    value: float,
    manifest: ComplexPartialTrackerManifest,
) -> int:
    if not math.isfinite(value):
        return manifest.score_saturation if value > 0.0 else -manifest.score_saturation
    scaled = int(round(value * (1 << manifest.score_fraction_bits)))
    return max(-manifest.score_saturation, min(manifest.score_saturation, scaled))


def _saturating_sum(
    *values: int,
    manifest: ComplexPartialTrackerManifest,
) -> int:
    return max(
        -manifest.score_saturation,
        min(manifest.score_saturation, sum(values)),
    )


def _observation_scores(
    observation: ComplexPartialObservation,
    manifest: ComplexPartialTrackerManifest,
) -> tuple[int, int]:
    """Return raw local potential and its uncertainty/leakage penalty."""

    if observation.amplitude_lower_confidence <= 0.0:
        return 0, 0
    noise_floor = max(observation.local_noise_floor, 1.0e-15)
    lower_ratio = observation.amplitude_lower_confidence / noise_floor
    raw_units = min(48.0, 4.0 * math.log2(1.0 + lower_ratio))

    amplitude_ratio = min(
        1.0,
        observation.amplitude_uncertainty
        / max(observation.normalized_detector_amplitude, 1.0e-15),
    )
    frequency_ratio = min(
        1.0,
        observation.frequency_uncertainty_hz
        / max(observation.resolution_hz, 1.0e-15),
    )
    phase_ratio = (
        min(1.0, observation.phase_uncertainty_radians / math.pi)
        if observation.phase_usable
        else 1.0
    )
    leakage_ratio = max(
        0.0,
        min(1.0, (12.0 - observation.peak_prominence_db) / 12.0),
    )
    penalty_units = (
        8.0 * amplitude_ratio
        + 6.0 * frequency_ratio
        + 2.0 * phase_ratio
        + 12.0 * leakage_ratio
    )
    return (
        _quantize_score(raw_units, manifest),
        _quantize_score(penalty_units, manifest),
    )


def _phase_for_edge(
    source: ComplexPartialObservation,
    target: ComplexPartialObservation,
) -> tuple[float, float] | None:
    if not source.phase_usable or not target.phase_usable:
        return None
    channel = int(np.argmax(
        np.asarray(source.channel_amplitudes)
        * np.asarray(target.channel_amplitudes)
    ))
    return (
        source.channel_phases[channel],
        target.channel_phases[channel],
    )


def _continuation_candidates(
    observations: tuple[ComplexPartialObservation, ...],
    sample_rate: int,
    manifest: ComplexPartialTrackerManifest,
) -> tuple[PartialContinuationHypothesis, ...]:
    by_frame: dict[int, list[ComplexPartialObservation]] = {}
    for observation in observations:
        by_frame.setdefault(observation.frame_index, []).append(observation)
    rows = []
    for source in observations:
        for gap in manifest.gap_hypotheses:
            targets = by_frame.get(source.frame_index + gap, ())
            duration_seconds = gap * source.hop_samples / sample_rate
            maximum_jump = (
                manifest.maximum_frequency_jump_hz
                + manifest.maximum_frequency_slope_hz_per_second
                * duration_seconds
            )
            ranked_targets = sorted(
                (
                    target
                    for target in targets
                    if abs(target.frequency_hz - source.frequency_hz)
                    <= maximum_jump
                ),
                key=lambda target: (
                    abs(target.frequency_hz - source.frequency_hz)
                    / max(
                        source.frequency_uncertainty_hz
                        + target.frequency_uncertainty_hz,
                        1.0e-9,
                    ),
                    -target.peak_prominence_db,
                    target.observation_id,
                ),
            )[: manifest.neighbors_per_gap]
            for target in ranked_targets:
                frequency_delta = target.frequency_hz - source.frequency_hz
                frequency_sigma = max(
                    source.frequency_uncertainty_hz
                    + target.frequency_uncertainty_hz,
                    0.25,
                )
                frequency_cost = math.log2(
                    1.0 + abs(frequency_delta) / frequency_sigma
                )
                amplitude_cost = math.log2(
                    1.0
                    + 8.0
                    * abs(math.log2(
                        max(target.normalized_detector_amplitude, 1.0e-12)
                        / max(source.normalized_detector_amplitude, 1.0e-12)
                    ))
                )
                phase_pair = _phase_for_edge(source, target)
                if phase_pair is None:
                    cycle_rows = ((None, None, 0.0),)
                else:
                    source_phase, target_phase = phase_pair
                    predicted_delta = (
                        2.0
                        * math.pi
                        * 0.5
                        * (source.frequency_hz + target.frequency_hz)
                        * duration_seconds
                    )
                    nearest_cycle = int(round(
                        (
                            predicted_delta
                            - (target_phase - source_phase)
                        )
                        / (2.0 * math.pi)
                    ))
                    phase_sigma = max(
                        source.phase_uncertainty_radians
                        + target.phase_uncertainty_radians,
                        0.01,
                    )
                    cycle_rows = []
                    for cycle_offset in manifest.cycle_offsets:
                        cycle_count = nearest_cycle + cycle_offset
                        unwrapped_delta = (
                            target_phase
                            - source_phase
                            + 2.0 * math.pi * cycle_count
                        )
                        phase_error = abs(unwrapped_delta - predicted_delta)
                        phase_cost = math.log2(
                            1.0 + phase_error / phase_sigma
                        )
                        cycle_rows.append(
                            (cycle_count, phase_error, phase_cost)
                        )
                for cycle_count, phase_error, phase_cost in cycle_rows:
                    proxy_cost = (
                        math.log2(1.0 + gap)
                        + frequency_cost
                        + amplitude_cost
                        + phase_cost
                    )
                    program_cost_bits = (
                        manifest.continuation_base_bits + proxy_cost
                    )
                    rows.append(
                        PartialContinuationHypothesis(
                            source_observation=source.observation_id,
                            target_observation=target.observation_id,
                            gap_hops=gap,
                            cycle_count=cycle_count,
                            phase_error_radians=phase_error,
                            frequency_delta_hz=frequency_delta,
                            continuity_cost_q=_quantize_score(
                                proxy_cost,
                                manifest,
                            ),
                            program_cost_bits=program_cost_bits,
                        )
                    )
    rows.sort(
        key=lambda row: (
            row.source_observation,
            row.target_observation,
            row.continuity_cost_q,
            -1 if row.cycle_count is None else row.cycle_count,
        )
    )
    return tuple(rows)


def _second_order_cost_q(
    previous: ComplexPartialObservation,
    current: ComplexPartialObservation,
    target: ComplexPartialObservation,
    sample_rate: int,
    manifest: ComplexPartialTrackerManifest,
) -> int:
    first_duration = (
        current.center_sample - previous.center_sample
    ) / sample_rate
    next_duration = (
        target.center_sample - current.center_sample
    ) / sample_rate
    if first_duration <= 0.0 or next_duration <= 0.0:
        return manifest.score_saturation
    slope = (
        current.frequency_hz - previous.frequency_hz
    ) / first_duration
    predicted_frequency = current.frequency_hz + slope * next_duration
    frequency_sigma = max(
        previous.frequency_uncertainty_hz
        + current.frequency_uncertainty_hz
        + target.frequency_uncertainty_hz,
        0.5,
    )
    acceleration_residual = abs(target.frequency_hz - predicted_frequency)
    amplitude_slope = math.log2(
        max(current.normalized_detector_amplitude, 1.0e-12)
        / max(previous.normalized_detector_amplitude, 1.0e-12)
    )
    predicted_log_amplitude = (
        math.log2(max(current.normalized_detector_amplitude, 1.0e-12))
        + amplitude_slope * next_duration / first_duration
    )
    amplitude_residual = abs(
        math.log2(max(target.normalized_detector_amplitude, 1.0e-12))
        - predicted_log_amplitude
    )
    return _quantize_score(
        math.log2(1.0 + acceleration_residual / frequency_sigma)
        + math.log2(1.0 + 4.0 * amplitude_residual),
        manifest,
    )


def _state_continuity_score_q(
    state: _PathState,
    manifest: ComplexPartialTrackerManifest,
) -> int:
    reward = _quantize_score(
        manifest.continuation_reward_units
        * max(0, len(state.observation_ids) - 1),
        manifest,
    )
    return _saturating_sum(
        reward,
        -state.continuity_cost_q,
        manifest=manifest,
    )


def _state_value_score_q(
    state: _PathState,
    manifest: ComplexPartialTrackerManifest,
) -> int:
    return _saturating_sum(
        state.potential_node_value_q,
        -state.uncertainty_leakage_penalty_q,
        _state_continuity_score_q(state, manifest) // 2,
        manifest=manifest,
    )


def _state_sort_key(
    state: _PathState,
    family: str,
    manifest: ComplexPartialTrackerManifest,
) -> tuple:
    if family == _FAMILY_CONTINUITY:
        score = _state_continuity_score_q(state, manifest)
    else:
        score = _state_value_score_q(state, manifest)
    return (
        -score,
        -len(state.observation_ids),
        state.observation_ids,
        tuple(-1 if value is None else value for value in state.cycle_counts),
    )


def _retain_state_union(
    states: list[_PathState],
    manifest: ComplexPartialTrackerManifest,
) -> list[_PathState]:
    unique = {
        (state.observation_ids, state.cycle_counts): state
        for state in states
    }
    retained = {}
    for family in (_FAMILY_VALUE, _FAMILY_CONTINUITY):
        ranked = sorted(
            unique.values(),
            key=lambda state: _state_sort_key(state, family, manifest),
        )
        for state in ranked[: manifest.k_best_per_state_per_family]:
            retained[(state.observation_ids, state.cycle_counts)] = state
    return sorted(
        retained.values(),
        key=lambda state: _state_sort_key(state, _FAMILY_VALUE, manifest),
    )


def _path_frequency_band(
    path: PartialPathHypothesis,
    by_id: dict[int, ComplexPartialObservation],
    sample_rate: int,
    band_count: int,
) -> int:
    median_frequency = float(np.median([
        by_id[observation_id].frequency_hz
        for observation_id in path.observation_ids
    ]))
    minimum_hz = 20.0
    maximum_hz = max(minimum_hz * 2.0, sample_rate / 2.0)
    position = math.log(
        max(minimum_hz, min(maximum_hz, median_frequency)) / minimum_hz
    ) / math.log(maximum_hz / minimum_hz)
    return min(band_count - 1, max(0, int(position * band_count)))


def _k_best_paths(
    observations: tuple[ComplexPartialObservation, ...],
    continuations: tuple[PartialContinuationHypothesis, ...],
    sample_rate: int,
    manifest: ComplexPartialTrackerManifest,
) -> tuple[PartialPathHypothesis, ...]:
    by_id = {
        observation.observation_id: observation
        for observation in observations
    }
    node_scores = {
        observation.observation_id: _observation_scores(
            observation,
            manifest,
        )
        for observation in observations
    }
    incoming: dict[int, list[PartialContinuationHypothesis]] = {}
    for continuation in continuations:
        incoming.setdefault(
            continuation.target_observation,
            [],
        ).append(continuation)

    states: dict[tuple[int, int], list[_PathState]] = {}
    for target in sorted(
        observations,
        key=lambda item: (item.frame_index, item.observation_id),
    ):
        pending_states: dict[tuple[int, int], list[_PathState]] = {}
        for continuation in incoming.get(target.observation_id, ()):
            source_id = continuation.source_observation
            source_value, source_penalty = node_scores[source_id]
            target_value, target_penalty = node_scores[target.observation_id]
            state_key = (source_id, target.observation_id)
            candidates = [
                _PathState(
                    observation_ids=(source_id, target.observation_id),
                    cycle_counts=(continuation.cycle_count,),
                    continuity_cost_q=continuation.continuity_cost_q,
                    potential_node_value_q=_saturating_sum(
                        source_value,
                        target_value,
                        manifest=manifest,
                    ),
                    uncertainty_leakage_penalty_q=_saturating_sum(
                        source_penalty,
                        target_penalty,
                        manifest=manifest,
                    ),
                    program_cost_bits_without_death=(
                        manifest.birth_bits
                        + continuation.program_cost_bits
                    ),
                    phase_errors=(
                        ()
                        if continuation.phase_error_radians is None
                        else (continuation.phase_error_radians,)
                    ),
                )
            ]
            for (previous_id, current_id), prior_states in tuple(states.items()):
                if current_id != source_id:
                    continue
                second_order_cost_q = _second_order_cost_q(
                    by_id[previous_id],
                    by_id[current_id],
                    target,
                    sample_rate,
                    manifest,
                )
                for prior_state in prior_states:
                    candidates.append(
                        _PathState(
                            observation_ids=(
                                *prior_state.observation_ids,
                                target.observation_id,
                            ),
                            cycle_counts=(
                                *prior_state.cycle_counts,
                                continuation.cycle_count,
                            ),
                            continuity_cost_q=_saturating_sum(
                                prior_state.continuity_cost_q,
                                continuation.continuity_cost_q,
                                second_order_cost_q,
                                manifest=manifest,
                            ),
                            potential_node_value_q=_saturating_sum(
                                prior_state.potential_node_value_q,
                                target_value,
                                manifest=manifest,
                            ),
                            uncertainty_leakage_penalty_q=_saturating_sum(
                                prior_state.uncertainty_leakage_penalty_q,
                                target_penalty,
                                manifest=manifest,
                            ),
                            program_cost_bits_without_death=(
                                prior_state.program_cost_bits_without_death
                                + continuation.program_cost_bits
                                + second_order_cost_q
                                / (1 << manifest.score_fraction_bits)
                            ),
                            phase_errors=(
                                prior_state.phase_errors
                                + (
                                    ()
                                    if continuation.phase_error_radians is None
                                    else (continuation.phase_error_radians,)
                                )
                            ),
                        )
                    )
            pending_states.setdefault(state_key, []).extend(candidates)
        for state_key, candidates in pending_states.items():
            states[state_key] = _retain_state_union(candidates, manifest)

    raw_paths = {}
    for state_rows in states.values():
        for state in state_rows:
            if len(state.observation_ids) < manifest.minimum_track_observations:
                continue
            conflict_groups = [
                by_id[observation_id].conflict_group
                for observation_id in state.observation_ids
            ]
            key = (state.observation_ids, state.cycle_counts)
            raw_paths[key] = PartialPathHypothesis(
                observation_ids=state.observation_ids,
                cycle_counts=state.cycle_counts,
                families=(),
                continuity_score_q=_state_continuity_score_q(
                    state,
                    manifest,
                ),
                potential_node_value_q=state.potential_node_value_q,
                uncertainty_leakage_penalty_q=(
                    state.uncertainty_leakage_penalty_q
                ),
                program_cost_bits=(
                    state.program_cost_bits_without_death
                    + manifest.death_bits
                ),
                ownership_conflict_count=(
                    len(conflict_groups) - len(set(conflict_groups))
                ),
                mean_phase_error_radians=(
                    float(np.mean(state.phase_errors))
                    if state.phase_errors
                    else None
                ),
            )

    family_members: dict[
        tuple[tuple[int, ...], tuple[int | None, ...]],
        set[str],
    ] = {}
    value_ranked = sorted(
        raw_paths.values(),
        key=lambda path: (
            -path.local_potential_score_q,
            path.ownership_conflict_count,
            -len(path.observation_ids),
            path.observation_ids,
            tuple(-1 if value is None else value for value in path.cycle_counts),
        ),
    )
    continuity_ranked = sorted(
        raw_paths.values(),
        key=lambda path: (
            -path.continuity_score_q,
            path.ownership_conflict_count,
            -len(path.observation_ids),
            path.observation_ids,
            tuple(-1 if value is None else value for value in path.cycle_counts),
        ),
    )
    for family, ranked in (
        (_FAMILY_VALUE, value_ranked),
        (_FAMILY_CONTINUITY, continuity_ranked),
    ):
        for path in ranked[: manifest.top_k_per_family]:
            family_members.setdefault(
                (path.observation_ids, path.cycle_counts),
                set(),
            ).add(family)

    protected_by_band: dict[int, list[PartialPathHypothesis]] = {}
    for path in raw_paths.values():
        protected_by_band.setdefault(
            _path_frequency_band(
                path,
                by_id,
                sample_rate,
                manifest.protected_frequency_bands,
            ),
            [],
        ).append(path)
    for paths in protected_by_band.values():
        paths.sort(
            key=lambda path: (
                -path.continuity_score_q,
                -(
                    path.potential_node_value_q
                    - path.uncertainty_leakage_penalty_q
                ),
                path.ownership_conflict_count,
                path.observation_ids,
            )
        )
        for path in paths[: manifest.protected_paths_per_band]:
            family_members.setdefault(
                (path.observation_ids, path.cycle_counts),
                set(),
            ).add(_FAMILY_WEAK)

    union = [
        replace(
            raw_paths[key],
            families=tuple(sorted(
                families,
                key=lambda family: _FAMILY_ORDER[family],
            )),
        )
        for key, families in family_members.items()
    ]
    union.sort(
        key=lambda path: (
            -path.local_potential_score_q,
            -path.continuity_score_q,
            path.ownership_conflict_count,
            path.observation_ids,
            tuple(-1 if value is None else value for value in path.cycle_counts),
        )
    )
    return tuple(union[: manifest.maximum_path_hypotheses])


def _paths_conflict(
    first: PartialPathHypothesis,
    second: PartialPathHypothesis,
    by_id: dict[int, ComplexPartialObservation],
) -> bool:
    first_groups = {
        by_id[observation_id].conflict_group
        for observation_id in first.observation_ids
    }
    second_groups = {
        by_id[observation_id].conflict_group
        for observation_id in second.observation_ids
    }
    return bool(first_groups & second_groups)


def _path_selection_score_q(path: PartialPathHypothesis) -> int:
    return max(0, path.local_potential_score_q, path.continuity_score_q)


def _select_path_set(
    observations: tuple[ComplexPartialObservation, ...],
    paths: tuple[PartialPathHypothesis, ...],
    manifest: ComplexPartialTrackerManifest,
) -> PartialTrackSet:
    by_id = {
        observation.observation_id: observation
        for observation in observations
    }
    candidates = tuple(
        path
        for path in paths
        if path.ownership_conflict_count == 0
        and _path_selection_score_q(path) > 0
    )
    if len(candidates) <= manifest.exact_set_candidate_limit:
        conflict_masks = []
        for index, path in enumerate(candidates):
            mask = 0
            for other_index, other in enumerate(candidates):
                if index != other_index and _paths_conflict(
                    path,
                    other,
                    by_id,
                ):
                    mask |= 1 << other_index
            conflict_masks.append(mask)
        best_mask = 0
        best_score = 0
        for mask in range(1, 1 << len(candidates)):
            score = 0
            valid = True
            remaining = mask
            while remaining:
                bit = remaining & -remaining
                index = bit.bit_length() - 1
                if conflict_masks[index] & (mask ^ bit):
                    valid = False
                    break
                score += _path_selection_score_q(candidates[index])
                remaining ^= bit
            if valid and (
                score > best_score
                or (score == best_score and mask < best_mask)
            ):
                best_mask = mask
                best_score = score
        selected = tuple(
            path
            for index, path in enumerate(candidates)
            if best_mask & (1 << index)
        )
        solver = "exact-small-disjoint-heuristic"
    else:
        ranked = sorted(
            candidates,
            key=lambda path: (
                -_path_selection_score_q(path),
                path.observation_ids,
            ),
        )
        selected_rows = []
        for path in ranked:
            if any(
                _paths_conflict(path, incumbent, by_id)
                for incumbent in selected_rows
            ):
                continue
            selected_rows.append(path)
        selected = tuple(selected_rows)
        best_score = sum(_path_selection_score_q(path) for path in selected)
        solver = "deterministic-bounded-disjoint-heuristic"
    return PartialTrackSet(
        paths=selected,
        heuristic_score_q=int(best_score),
        solver=solver,
        report={
            "schema": "resonith-r187-partial-track-set-1",
            "status": "dimensionless analyzer heuristic; no byte admission",
            "path_count": len(selected),
            "heuristic_score_q": int(best_score),
            "solver": solver,
        },
    )


def track_complex_partials(
    observation_set: ComplexPartialObservationSet,
    sample_rate: int,
    *,
    manifest: ComplexPartialTrackerManifest = (
        ComplexPartialTrackerManifest()
    ),
) -> ComplexPartialTracking:
    """Create the R-187 path-family union without synthesis or byte claims."""

    if sample_rate <= 0:
        raise ValueError("invalid tracker sample rate")
    observations = tuple(
        observation
        for observation in observation_set.observations
        if (
            observation.resolution_id == manifest.resolution_id
            and observation.detector_channel == manifest.detector_channel
            and observation.locally_resolvable
        )
    )
    continuations = _continuation_candidates(
        observations,
        sample_rate,
        manifest,
    )
    paths = _k_best_paths(
        observations,
        continuations,
        sample_rate,
        manifest,
    )
    selected_set = _select_path_set(
        observations,
        paths,
        manifest,
    )
    retained_observation_ids = {
        observation_id
        for path in paths
        for observation_id in path.observation_ids
    }
    family_counts = {
        family: sum(family in path.families for path in paths)
        for family in (
            _FAMILY_VALUE,
            _FAMILY_CONTINUITY,
            _FAMILY_WEAK,
        )
    }
    return ComplexPartialTracking(
        observations=observations,
        continuations=continuations,
        paths=paths,
        selected_set=selected_set,
        report={
            "schema": "resonith-r187-complex-partial-tracking-1",
            "status": "path hypotheses only; no predictor or codec claim",
            "phase_evidence_only": True,
            "observation_count": len(observations),
            "continuation_hypothesis_count": len(continuations),
            "path_hypothesis_count": len(paths),
            "retained_track_observation_count": len(
                retained_observation_ids
            ),
            "selected_path_count": len(selected_set.paths),
            "selected_set_solver": selected_set.solver,
            "path_family_counts": family_counts,
            "score_fraction_bits": manifest.score_fraction_bits,
            "score_saturation": manifest.score_saturation,
            "node_value_unit": "dimensionless fixed-point heuristic",
            "program_cost_unit": "provisional bits, reported separately",
            "semantic_source_classes": False,
            "predictor_integrated": False,
            "actual_byte_rdo": False,
        },
    )
