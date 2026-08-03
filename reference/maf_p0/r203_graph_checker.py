"""Independent finite graph checker for the R-203 exact supplement.

This module intentionally has no dependency on the Resonith native ABI or on
the arbitrary-precision R-190/R-191 oracle. It derives canonical edges, paths,
ownership conflicts, and every conflict-free path subset directly from plain
input dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence


PATH_ENTRY_BIRTH_EDGE = (1 << 64) - 1
LOCALLY_RESOLVABLE = 2


@dataclass(frozen=True, order=True)
class GraphEdgeIdentity:
    """Canonical identity of one independently derived graph edge."""

    candidate_id: int
    source_observation_id: int
    target_observation_id: int
    gap_hops: int
    cycle_offset: int


@dataclass(frozen=True, order=True)
class GraphPathIdentity:
    """One complete directed observation/edge sequence."""

    observation_ids: tuple[int, ...]
    incoming_edge_ids: tuple[int, ...]


@dataclass(frozen=True)
class GraphCheckResult:
    """Closed finite result emitted by Authority B."""

    edges: tuple[GraphEdgeIdentity, ...]
    paths: tuple[GraphPathIdentity, ...]
    internal_conflict_paths: tuple[GraphPathIdentity, ...]
    cross_path_conflicts: tuple[
        tuple[GraphPathIdentity, GraphPathIdentity],
        ...,
    ]
    conflict_free_subsets: tuple[tuple[GraphPathIdentity, ...], ...]


@dataclass(frozen=True)
class GraphSelectionResult:
    """Independent score, conflict and exact-subset selection result."""

    ordered_paths: tuple[GraphPathIdentity, ...]
    selection_scores_q8: tuple[int, ...]
    internal_conflict_counts: tuple[int, ...]
    cross_path_conflicts: tuple[tuple[int, int], ...]
    selectable_candidate_count: int
    selected_path_ids: tuple[int, ...]


def _canonical_observations(
    observations: Sequence[Mapping[str, int]],
) -> tuple[Mapping[str, int], ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item["center_sample"],
                item["resolution_id"],
                item["detector_id"],
                item["frequency_hz_q20"],
                item["observation_id"],
            ),
        )
    )


def _resolution_table(
    resolutions: Sequence[Mapping[str, int]],
) -> dict[int, Mapping[str, int]]:
    result = {item["resolution_id"]: item for item in resolutions}
    if len(result) != len(resolutions):
        raise ValueError("duplicate resolution ID")
    return result


def enumerate_graph_edges(
    resolutions: Sequence[Mapping[str, int]],
    observations: Sequence[Mapping[str, int]],
    graph_manifest: Mapping[str, object],
) -> tuple[GraphEdgeIdentity, ...]:
    """Derive the complete canonical edge set directly from input fields."""

    resolution_by_id = _resolution_table(resolutions)
    canonical = _canonical_observations(observations)
    gap_count = int(graph_manifest["gap_count"])
    cycle_count = int(graph_manifest["cycle_offset_count"])
    gaps = tuple(int(item) for item in graph_manifest["gaps"])
    cycles = tuple(int(item) for item in graph_manifest["cycle_offsets"])
    neighbours = int(graph_manifest["neighbors_per_gap"])
    jump = int(graph_manifest["maximum_frequency_jump_hz_q20"])
    slope = int(
        graph_manifest["maximum_frequency_slope_hz_per_sample_q20"]
    )
    maximum_edges = int(graph_manifest["maximum_edge_records"])

    edges: list[GraphEdgeIdentity] = []
    candidate_id = 0
    for source in canonical:
        if not int(source["flags"]) & LOCALLY_RESOLVABLE:
            continue
        resolution = resolution_by_id[int(source["resolution_id"])]
        for gap in gaps[:gap_count]:
            center_delta = gap * int(resolution["hop_samples"])
            target_center = int(source["center_sample"]) + center_delta
            maximum_distance = min(
                (1 << 63) - 1,
                jump + slope * center_delta,
            )
            targets: list[tuple[int, int, int, Mapping[str, int]]] = []
            for target in canonical:
                if (
                    int(target["resolution_id"])
                    != int(source["resolution_id"])
                    or int(target["detector_id"])
                    != int(source["detector_id"])
                    or int(target["center_sample"]) != target_center
                    or not int(target["flags"]) & LOCALLY_RESOLVABLE
                ):
                    continue
                frequency_delta = (
                    int(target["frequency_hz_q20"])
                    - int(source["frequency_hz_q20"])
                )
                if abs(frequency_delta) > maximum_distance:
                    continue
                uncertainty = min(
                    (1 << 64) - 1,
                    int(source["frequency_uncertainty_hz_q20"])
                    + int(target["frequency_uncertainty_hz_q20"]),
                )
                distance = _log2_one_plus_ratio_q8(
                    abs(frequency_delta),
                    max(1, uncertainty),
                )
                targets.append(
                    (
                        distance,
                        -int(target["neighbor_priority_q8"]),
                        int(target["observation_id"]),
                        target,
                    )
                )
            targets.sort(key=lambda row: row[:3])
            for _distance, _priority, _identifier, target in targets[
                :neighbours
            ]:
                for cycle in cycles[:cycle_count]:
                    if candidate_id >= maximum_edges:
                        raise OverflowError("R-203 edge bound reached")
                    edges.append(
                        GraphEdgeIdentity(
                            candidate_id=candidate_id,
                            source_observation_id=int(
                                source["observation_id"]
                            ),
                            target_observation_id=int(
                                target["observation_id"]
                            ),
                            gap_hops=gap,
                            cycle_offset=cycle,
                        )
                    )
                    candidate_id += 1
    return tuple(edges)


def enumerate_graph_paths(
    edges: Sequence[GraphEdgeIdentity],
    maximum_path_observations: int,
) -> tuple[GraphPathIdentity, ...]:
    """Enumerate every directed simple path and incoming-edge sequence."""

    if maximum_path_observations < 2:
        raise ValueError("maximum path length must be at least two")
    outgoing: dict[int, list[GraphEdgeIdentity]] = {}
    for edge in edges:
        outgoing.setdefault(edge.source_observation_id, []).append(edge)
    for rows in outgoing.values():
        rows.sort()

    paths: set[GraphPathIdentity] = set()

    def visit(path: GraphPathIdentity) -> None:
        paths.add(path)
        if len(path.observation_ids) >= maximum_path_observations:
            return
        terminal = path.observation_ids[-1]
        for edge in outgoing.get(terminal, ()):
            if edge.target_observation_id in path.observation_ids:
                continue
            visit(
                GraphPathIdentity(
                    observation_ids=(
                        *path.observation_ids,
                        edge.target_observation_id,
                    ),
                    incoming_edge_ids=(
                        *path.incoming_edge_ids,
                        edge.candidate_id,
                    ),
                )
            )

    for edge in sorted(edges):
        visit(
            GraphPathIdentity(
                observation_ids=(
                    edge.source_observation_id,
                    edge.target_observation_id,
                ),
                incoming_edge_ids=(
                    PATH_ENTRY_BIRTH_EDGE,
                    edge.candidate_id,
                ),
            )
        )
    return tuple(sorted(paths))


def _ownership_components(
    path: GraphPathIdentity,
    observations_by_id: Mapping[int, Mapping[str, int]],
) -> tuple[int, ...]:
    return tuple(
        int(observations_by_id[item]["ownership_component"])
        for item in path.observation_ids
    )


def _paths_conflict(
    first: GraphPathIdentity,
    second: GraphPathIdentity,
    observations_by_id: Mapping[int, Mapping[str, int]],
) -> bool:
    first_components = set(_ownership_components(first, observations_by_id))
    return any(
        component in first_components
        for component in _ownership_components(second, observations_by_id)
    )


def enumerate_conflict_free_subsets(
    paths: Sequence[GraphPathIdentity],
    observations: Sequence[Mapping[str, int]],
) -> tuple[
    tuple[GraphPathIdentity, ...],
    tuple[GraphPathIdentity, ...],
    tuple[tuple[GraphPathIdentity, GraphPathIdentity], ...],
]:
    """Return every legal subset and the independently derived conflicts."""

    observations_by_id = {
        int(item["observation_id"]): item for item in observations
    }
    if len(observations_by_id) != len(observations):
        raise ValueError("duplicate observation ID")

    internal = tuple(
        path
        for path in paths
        if len(
            set(_ownership_components(path, observations_by_id))
        )
        != len(path.observation_ids)
    )
    internal_set = set(internal)
    selectable = tuple(path for path in paths if path not in internal_set)
    cross = tuple(
        (selectable[left], selectable[right])
        for left, right in combinations(range(len(selectable)), 2)
        if _paths_conflict(
            selectable[left],
            selectable[right],
            observations_by_id,
        )
    )
    cross_set = {
        frozenset((first, second)) for first, second in cross
    }

    subsets: list[tuple[GraphPathIdentity, ...]] = []
    for size in range(len(selectable) + 1):
        for subset in combinations(selectable, size):
            if any(
                frozenset((subset[left], subset[right])) in cross_set
                for left, right in combinations(range(len(subset)), 2)
            ):
                continue
            subsets.append(subset)
    return tuple(subsets), internal, cross


def check_graph(
    resolutions: Sequence[Mapping[str, int]],
    observations: Sequence[Mapping[str, int]],
    graph_manifest: Mapping[str, object],
    maximum_path_observations: int,
) -> GraphCheckResult:
    """Run the complete independent finite graph check."""

    edges = enumerate_graph_edges(
        resolutions,
        observations,
        graph_manifest,
    )
    paths = enumerate_graph_paths(edges, maximum_path_observations)
    subsets, internal, cross = enumerate_conflict_free_subsets(
        paths,
        observations,
    )
    return GraphCheckResult(
        edges=edges,
        paths=paths,
        internal_conflict_paths=internal,
        cross_path_conflicts=cross,
        conflict_free_subsets=subsets,
    )


def judge_exact_selection(
    observations: Sequence[Mapping[str, int]],
    graph_manifest: Mapping[str, object],
    path_manifest: Mapping[str, object],
    checker: GraphCheckResult,
) -> GraphSelectionResult:
    """Independently score every path and exhaust the exact subset law."""

    observations_by_id = {
        int(item["observation_id"]): item for item in observations
    }
    edges_by_id = {
        edge.candidate_id: edge for edge in checker.edges
    }
    edge_costs = _independent_edge_costs(
        observations_by_id,
        graph_manifest,
        checker.edges,
    )
    score_saturation = int(path_manifest["score_saturation"])
    continuation_reward = int(graph_manifest["continuation_reward_q8"])

    scores_by_path: dict[GraphPathIdentity, tuple[int, int, int]] = {}
    internal_by_path: dict[GraphPathIdentity, int] = {}
    for path in checker.paths:
        continuity_cost = 0
        potential = 0
        leakage = 0
        for observation_id in path.observation_ids:
            observation = observations_by_id[observation_id]
            potential = _bounded_sum(
                potential,
                int(observation["potential_node_value_q8"]),
                score_saturation,
            )
            leakage = _bounded_sum(
                leakage,
                int(observation["uncertainty_leakage_penalty_q8"]),
                score_saturation,
            )
        for edge_id in path.incoming_edge_ids[1:]:
            continuity_cost = _bounded_sum(
                continuity_cost,
                edge_costs[edge_id],
                score_saturation,
            )
        for index in range(2, len(path.observation_ids)):
            second_order = _second_order_cost_q8(
                observations_by_id[path.observation_ids[index - 2]],
                observations_by_id[path.observation_ids[index - 1]],
                observations_by_id[path.observation_ids[index]],
                path_manifest,
            )
            continuity_cost = _bounded_sum(
                continuity_cost,
                second_order,
                score_saturation,
            )
        continuity = max(
            -score_saturation,
            min(
                score_saturation,
                continuation_reward * (len(path.observation_ids) - 1)
                - continuity_cost,
            ),
        )
        value = max(
            -score_saturation,
            min(
                score_saturation,
                potential - leakage + continuity // 2,
            ),
        )
        scores_by_path[path] = (
            value,
            continuity,
            max(0, value, continuity),
        )
        components = _ownership_components(path, observations_by_id)
        internal_by_path[path] = len(components) - len(set(components))

    ordered_paths = tuple(
        sorted(
            checker.paths,
            key=lambda path: (
                -scores_by_path[path][0],
                -scores_by_path[path][1],
                path,
            ),
        )
    )
    selectable = tuple(
        path
        for path in ordered_paths
        if internal_by_path[path] == 0
        and scores_by_path[path][2] > 0
    )
    selectable_index = {
        path: index for index, path in enumerate(selectable)
    }
    cross = tuple(
        (
            selectable_index[first],
            selectable_index[second],
        )
        for first, second in checker.cross_path_conflicts
        if first in selectable_index and second in selectable_index
    )
    cross_set = {frozenset(pair) for pair in cross}
    path_ids = {
        path: index for index, path in enumerate(ordered_paths)
    }
    best_score = 0
    best_ids: tuple[int, ...] = ()
    for subset in checker.conflict_free_subsets:
        if any(path not in selectable_index for path in subset):
            continue
        indices = tuple(selectable_index[path] for path in subset)
        if any(
            frozenset((indices[left], indices[right])) in cross_set
            for left, right in combinations(range(len(indices)), 2)
        ):
            continue
        ids = tuple(sorted(path_ids[path] for path in subset))
        score = sum(scores_by_path[path][2] for path in subset)
        if score > best_score or (score == best_score and ids < best_ids):
            best_score = score
            best_ids = ids

    return GraphSelectionResult(
        ordered_paths=ordered_paths,
        selection_scores_q8=tuple(
            scores_by_path[path][2] for path in ordered_paths
        ),
        internal_conflict_counts=tuple(
            internal_by_path[path] for path in ordered_paths
        ),
        cross_path_conflicts=tuple(sorted(cross)),
        selectable_candidate_count=len(selectable),
        selected_path_ids=best_ids,
    )


def _independent_edge_costs(
    observations_by_id: Mapping[int, Mapping[str, int]],
    graph_manifest: Mapping[str, object],
    edges: Sequence[GraphEdgeIdentity],
) -> dict[int, int]:
    result: dict[int, int] = {}
    saturation = int(graph_manifest["score_saturation"])
    for edge in edges:
        source = observations_by_id[edge.source_observation_id]
        target = observations_by_id[edge.target_observation_id]
        frequency_delta = (
            int(target["frequency_hz_q20"])
            - int(source["frequency_hz_q20"])
        )
        uncertainty = min(
            (1 << 64) - 1,
            int(source["frequency_uncertainty_hz_q20"])
            + int(target["frequency_uncertainty_hz_q20"]),
        )
        amplitude_log = _signed_log_amplitude_ratio_q8(
            int(target["normalized_amplitude_q16"]),
            int(source["normalized_amplitude_q16"]),
        )
        phase_usable = (
            int(source["flags"]) & 1 and int(target["flags"]) & 1
        )
        phase_error = (
            _phase_error_u31(source, target) if phase_usable else 0
        )
        phase_uncertainty = (
            int(source["phase_uncertainty_u31"])
            + int(target["phase_uncertainty_u31"])
        )
        components = (
            _log2_one_plus_ratio_q8(
                abs(frequency_delta),
                max(1, uncertainty),
            ),
            _log2_one_plus_ratio_q8(abs(amplitude_log) * 8, 256),
            (
                _log2_one_plus_ratio_q8(
                    phase_error,
                    max(1, phase_uncertainty),
                )
                if phase_usable
                else 0
            ),
            _log2_one_plus_ratio_q8(edge.gap_hops, 1),
            _log2_one_plus_ratio_q8(abs(edge.cycle_offset), 1),
        )
        continuity = 0
        for component in components:
            continuity = _bounded_sum(
                continuity,
                component,
                saturation,
            )
        result[edge.candidate_id] = continuity
    return result


def _second_order_cost_q8(
    previous: Mapping[str, int],
    current: Mapping[str, int],
    target: Mapping[str, int],
    path_manifest: Mapping[str, object],
) -> int:
    saturation = int(path_manifest["score_saturation"])
    dt01 = int(current["center_sample"]) - int(previous["center_sample"])
    dt12 = int(target["center_sample"]) - int(current["center_sample"])
    if dt01 <= 0 or dt12 <= 0:
        return saturation
    predicted_frequency_delta = _scale_nearest_even(
        int(current["frequency_hz_q20"])
        - int(previous["frequency_hz_q20"]),
        dt12,
        dt01,
        saturation,
    )
    actual_frequency_delta = (
        int(target["frequency_hz_q20"])
        - int(current["frequency_hz_q20"])
    )
    frequency_residual = abs(
        actual_frequency_delta - predicted_frequency_delta
    )
    pair_uncertainty = min(
        (1 << 64) - 1,
        int(previous["frequency_uncertainty_hz_q20"])
        + int(current["frequency_uncertainty_hz_q20"]),
    )
    scaled_pair_uncertainty = min(
        (1 << 64) - 1,
        (pair_uncertainty * dt12 + dt01 - 1) // dt01,
    )
    frequency_sigma = max(
        int(path_manifest["frequency_sigma_floor_hz_q20"]),
        min(
            (1 << 64) - 1,
            int(target["frequency_uncertainty_hz_q20"])
            + int(current["frequency_uncertainty_hz_q20"])
            + scaled_pair_uncertainty,
        ),
    )
    frequency_cost = _log2_one_plus_ratio_q8(
        frequency_residual,
        frequency_sigma,
    )
    amplitude_floor = int(path_manifest["amplitude_floor_q16"])
    previous_amplitude = max(
        amplitude_floor,
        int(previous["normalized_amplitude_q16"]),
    )
    current_amplitude = max(
        amplitude_floor,
        int(current["normalized_amplitude_q16"]),
    )
    target_amplitude = max(
        amplitude_floor,
        int(target["normalized_amplitude_q16"]),
    )
    first_log_delta = _signed_log_amplitude_ratio_q8(
        current_amplitude,
        previous_amplitude,
    )
    actual_log_delta = _signed_log_amplitude_ratio_q8(
        target_amplitude,
        current_amplitude,
    )
    predicted_log_delta = _scale_nearest_even(
        first_log_delta,
        dt12,
        dt01,
        saturation,
    )
    amplitude_residual = abs(actual_log_delta - predicted_log_delta)
    weighted_amplitude = min(
        (1 << 64) - 1,
        amplitude_residual
        * int(path_manifest["amplitude_residual_weight_q8"]),
    )
    amplitude_cost = _log2_one_plus_ratio_q8(
        weighted_amplitude,
        1 << 16,
    )
    return min(saturation, frequency_cost + amplitude_cost)


def _scale_nearest_even(
    value: int,
    numerator: int,
    denominator: int,
    saturation: int,
) -> int:
    magnitude = abs(value)
    quotient, remainder = divmod(magnitude * numerator, denominator)
    complement = denominator - remainder
    if remainder > complement or (
        remainder == complement and quotient & 1
    ):
        quotient += 1
    quotient = min(quotient, saturation)
    return -quotient if value < 0 else quotient


def _signed_log_amplitude_ratio_q8(target: int, source: int) -> int:
    if target == source:
        return 0
    if source == 0:
        return 0 if target == 0 else ((1 << 31) - 1) // 4
    if target == 0:
        return -(1 << 31) // 4
    if target > source:
        return _log2_one_plus_ratio_q8(target - source, source)
    return -_log2_one_plus_ratio_q8(source - target, target)


def _phase_error_u31(
    source: Mapping[str, int],
    target: Mapping[str, int],
) -> int:
    center_delta = (
        int(target["center_sample"]) - int(source["center_sample"])
    )
    source_step = int(source["phase_step_u32"])
    target_step = int(target["phase_step_u32"])
    step_sum = source_step + target_step
    product = ((step_sum >> 1) & 0xFFFFFFFF) * (
        center_delta & 0xFFFFFFFF
    )
    advance = product & 0xFFFFFFFF
    if step_sum & 1:
        advance = (
            advance + ((center_delta >> 1) + (center_delta & 1))
        ) & 0xFFFFFFFF
    expected = (int(source["phase_turn_u32"]) + advance) & 0xFFFFFFFF
    raw = (int(target["phase_turn_u32"]) - expected) & 0xFFFFFFFF
    wrapped = raw if raw < 1 << 31 else raw - (1 << 32)
    return abs(wrapped)


def _bounded_sum(left: int, right: int, limit: int) -> int:
    return max(-limit, min(limit, left + right))


def _ratio_q16(numerator: int, denominator: int) -> int:
    if denominator == 0:
        return (65535 << 16) | 0xFFFF
    integer, remainder = divmod(numerator, denominator)
    if integer >= 65535:
        return (65535 << 16) | 0xFFFF
    fraction = 0
    for _bit in range(16):
        fraction <<= 1
        if remainder >= denominator - remainder:
            remainder -= denominator - remainder
            fraction |= 1
        else:
            remainder *= 2
    return (integer << 16) | fraction


def _log2_one_plus_ratio_q8(numerator: int, denominator: int) -> int:
    value_q16 = (1 << 16) + _ratio_q16(numerator, denominator)
    most_significant = value_q16.bit_length() - 1
    integer_part = most_significant - 16
    normalized = value_q16 << (31 - most_significant)
    fraction = 0
    for _bit in range(8):
        normalized = (normalized * normalized) >> 31
        fraction <<= 1
        if normalized >= 1 << 32:
            normalized >>= 1
            fraction |= 1
    return (integer_part << 8) | fraction


def path_identity_dict(
    paths: Iterable[GraphPathIdentity],
) -> tuple[dict[str, list[int]], ...]:
    """Convert Authority-B identities to stable JSON-compatible records."""

    return tuple(
        {
            "observation_ids": list(path.observation_ids),
            "incoming_edge_ids": list(path.incoming_edge_ids),
        }
        for path in sorted(paths)
    )
