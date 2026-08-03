"""Candidate-rich exact supplement for the R-203 path admission gate.

Authority A is the existing arbitrary-precision Python oracle. Authority B is
the separate graph checker in ``r203_graph_checker``. Corpus generation fails
closed unless both authorities and every closed-form invariant agree.
"""

from __future__ import annotations

import ctypes
import hashlib
import itertools
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Sequence

from .partial_graph_fixed import (
    LOCALLY_RESOLVABLE,
    PATH_FAMILY_PROTECTED_WEAK,
    PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT,
    PATH_FLAG_PHASE_EVIDENCE,
    PHASE_USABLE,
    PROTECTED_WEAK,
    PartialObservation,
    build_paths_fixed,
    enumerate_edges_fixed,
    make_manifest,
    make_observation,
    make_path_manifest,
    make_resolution,
    upgrade_path_manifest_v3,
)
from .r197_case_generator import (
    _ctypes_value,
    _path_semantics,
    emit_jsonl,
    input_fingerprint_v1,
)
from .r203_graph_checker import (
    GraphEdgeIdentity,
    GraphPathIdentity,
    check_graph,
    judge_exact_selection,
    path_identity_dict,
)


GENERATOR_ID = "R203-CANDIDATE-RICH-EXACT-1"
SCHEMA = "resonith-r203-candidate-rich-exact-jsonl-1"
INVENTORY_SCHEMA = "resonith-r203-candidate-rich-inventory-1"
CONTRACT_SHA256 = (
    "572db682e345bef4f448f049674d2edd62cfe972fc58a1a2ab36c2dd2459dd73"
)
SAMPLE_RATE = 48_000
Q20 = 1 << 20
RESOLUTION = make_resolution(0, 128, 64)
OWNERSHIP_PROFILES = ("U", "C")
PHASE_PROFILES = ("N", "Z", "P")


TOPOLOGIES = {
    "T0": {
        "centers": (0, 64, 128),
        "frequencies_hz": (440, 440, 440),
        "gaps": (1,),
        "cycles": (-1, 0, 1),
        "neighbors": 1,
        "jump_hz": 0,
        "slope_hz_per_sample": 0,
        "expected_edges": 6,
        "expected_paths": 15,
    },
    "T1": {
        "centers": (0, 64, 64, 128),
        "frequencies_hz": (440, 439, 441, 440),
        "gaps": (1,),
        "cycles": (0,),
        "neighbors": 2,
        "jump_hz": 1,
        "slope_hz_per_sample": 0,
        "expected_edges": 4,
        "expected_paths": 6,
    },
    "T2": {
        "centers": (0, 192, 384),
        "frequencies_hz": (440, 999, 1558),
        "gaps": (3,),
        "cycles": (0,),
        "neighbors": 1,
        "jump_hz": 368,
        "slope_hz_per_sample": 1,
        "expected_edges": 2,
        "expected_paths": 3,
    },
    "T3": {
        "centers": (0, 192, 384),
        "frequencies_hz": (440, 1000, 1560),
        "gaps": (3,),
        "cycles": (0,),
        "neighbors": 1,
        "jump_hz": 368,
        "slope_hz_per_sample": 1,
        "expected_edges": 2,
        "expected_paths": 3,
    },
    "T4": {
        "centers": (0, 192, 384),
        "frequencies_hz": (440, 1001, 1562),
        "gaps": (3,),
        "cycles": (0,),
        "neighbors": 1,
        "jump_hz": 368,
        "slope_hz_per_sample": 1,
        "expected_edges": 0,
        "expected_paths": 0,
    },
}


def verify_contract(path: Path) -> str:
    """Bind the generator to the independently audited written contract."""

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != CONTRACT_SHA256:
        raise RuntimeError(
            "R-203 candidate-rich contract hash mismatch: "
            f"expected {CONTRACT_SHA256}, got {digest}"
        )
    return digest


def _ownerships(profile: str, count: int) -> tuple[int, ...]:
    if profile == "U":
        return tuple(range(count))
    if profile != "C":
        raise ValueError(f"unknown ownership profile {profile}")
    return (0, 0, 1, 0) if count == 4 else (0, 0, 1)


def _phase_fields(
    profile: str,
    count: int,
) -> tuple[int, tuple[int, ...]]:
    if profile == "N":
        return LOCALLY_RESOLVABLE, (0,) * count
    if profile == "Z":
        return LOCALLY_RESOLVABLE | PHASE_USABLE, (0,) * count
    if profile == "P":
        return (
            LOCALLY_RESOLVABLE | PHASE_USABLE | PROTECTED_WEAK,
            tuple((index * 0x40000000) & 0xFFFFFFFF for index in range(count)),
        )
    raise ValueError(f"unknown phase profile {profile}")


def make_case_inputs(
    topology_name: str,
    ownership_profile: str,
    phase_profile: str,
) -> tuple[
    tuple[PartialObservation, ...],
    object,
    object,
]:
    """Construct one canonical candidate-rich input without native code."""

    topology = TOPOLOGIES[topology_name]
    centers = tuple(topology["centers"])
    frequencies = tuple(topology["frequencies_hz"])
    ownerships = _ownerships(ownership_profile, len(centers))
    flags, turns = _phase_fields(phase_profile, len(centers))

    observations: list[PartialObservation] = []
    for index, (center, frequency_hz) in enumerate(
        zip(centers, frequencies, strict=True)
    ):
        observation = make_observation(
            observation_id=index,
            frame_index=int(center) // 64,
            resolution_id=0,
            hop_samples=64,
            frequency_hz_q20=int(frequency_hz) * Q20,
            phase_turn_u32=turns[index],
            phase_step_u32=0,
            normalized_amplitude_q16=1 << 16,
            ownership_component=ownerships[index],
            detector_id=0,
            frequency_uncertainty_hz_q20=Q20,
            phase_uncertainty_u31=1 << 20,
            flags=flags,
            neighbor_priority_q8=512,
            potential_node_value_q8=4096,
            uncertainty_leakage_penalty_q8=64,
        )
        observation.band_id = 0
        observation.protected_rank_q8 = 256
        observations.append(observation)

    graph = make_manifest(
        sample_rate=SAMPLE_RATE,
        resolution_count=1,
        gaps=tuple(topology["gaps"]),
        neighbors_per_gap=int(topology["neighbors"]),
        cycle_offsets=tuple(topology["cycles"]),
        maximum_frequency_jump_hz_q20=int(topology["jump_hz"]) * Q20,
        maximum_frequency_slope_hz_per_sample_q20=(
            int(topology["slope_hz_per_sample"]) * Q20
        ),
        maximum_edge_records=64,
    )
    graph.minimum_track_observations = 2
    graph.continuation_base_bits_q8 = 256
    graph.continuation_reward_q8 = 256
    graph.score_saturation = (1 << 62) - 1
    graph.maximum_path_hypotheses = 64
    graph.exact_set_candidate_limit = 20

    legacy_path = make_path_manifest(
        protected_band_upper_hz_q20=(),
        minimum_path_observations=2,
        maximum_path_observations=4,
        k_value_per_state=16,
        k_continuity_per_state=16,
        top_k_value=20,
        top_k_continuity=20,
        top_k_protected=20,
        protected_paths_per_band=2,
        exact_set_candidate_limit=20,
        maximum_path_records=64,
        maximum_total_entries=256,
        maximum_frontier_states=64,
        maximum_state_records=128,
        maximum_work_units=10_000_000,
        maximum_managed_bytes=1 << 20,
    )
    path = upgrade_path_manifest_v3(
        legacy_path,
        maximum_device_bytes=0,
    )
    return tuple(observations), graph, path


def _authority_a_edge_identities(edges: Sequence[object]) -> tuple[
    GraphEdgeIdentity,
    ...,
]:
    return tuple(
        GraphEdgeIdentity(
            candidate_id=int(edge.candidate_id),
            source_observation_id=int(edge.source_observation_id),
            target_observation_id=int(edge.target_observation_id),
            gap_hops=int(edge.gap_hops),
            cycle_offset=int(edge.cycle_offset),
        )
        for edge in edges
    )


def _authority_a_path_identities(result: object) -> tuple[
    GraphPathIdentity,
    ...,
]:
    return tuple(
        sorted(
            GraphPathIdentity(
                observation_ids=tuple(
                    int(entry.observation_id) for entry in path.entries
                ),
                incoming_edge_ids=tuple(
                    int(entry.incoming_edge_candidate_id)
                    for entry in path.entries
                ),
            )
            for path in result.paths
        )
    )


def _validate_invariants(
    topology_name: str,
    ownership_profile: str,
    phase_profile: str,
    oracle: object,
    checker: object,
    edges: Sequence[object],
    observations: Sequence[PartialObservation],
    graph_manifest: object,
    path_manifest: object,
) -> None:
    topology = TOPOLOGIES[topology_name]
    expected_edges = int(topology["expected_edges"])
    expected_paths = int(topology["expected_paths"])
    if len(edges) != expected_edges or len(checker.edges) != expected_edges:
        raise RuntimeError(f"{topology_name}: closed edge count differs")
    if (
        len(oracle.paths) != expected_paths
        or len(checker.paths) != expected_paths
    ):
        raise RuntimeError(f"{topology_name}: closed path count differs")
    if _authority_a_edge_identities(edges) != checker.edges:
        raise RuntimeError(f"{topology_name}: Authority A/B edges differ")
    if _authority_a_path_identities(oracle) != checker.paths:
        raise RuntimeError(f"{topology_name}: Authority A/B paths differ")
    selection = judge_exact_selection(
        [_ctypes_value(item) for item in observations],
        _ctypes_value(graph_manifest),
        _ctypes_value(path_manifest),
        checker,
    )
    authority_a_ordered = tuple(
        GraphPathIdentity(
            observation_ids=tuple(
                int(entry.observation_id) for entry in path.entries
            ),
            incoming_edge_ids=tuple(
                int(entry.incoming_edge_candidate_id)
                for entry in path.entries
            ),
        )
        for path in oracle.paths
    )
    if authority_a_ordered != selection.ordered_paths:
        raise RuntimeError(
            f"{topology_name}: Authority B path ordering differs"
        )
    if tuple(
        int(path.selection_score_q8) for path in oracle.paths
    ) != selection.selection_scores_q8:
        raise RuntimeError(
            f"{topology_name}: Authority B selection scores differ"
        )
    if tuple(
        int(path.ownership_conflict_count) for path in oracle.paths
    ) != selection.internal_conflict_counts:
        raise RuntimeError(
            f"{topology_name}: Authority B internal conflicts differ"
        )
    if (
        int(oracle.report["cross_path_conflict_count"])
        != len(selection.cross_path_conflicts)
    ):
        raise RuntimeError(
            f"{topology_name}: Authority B cross conflicts differ"
        )
    if (
        int(oracle.report["selected_candidate_count"])
        != selection.selectable_candidate_count
    ):
        raise RuntimeError(
            f"{topology_name}: Authority B candidate count differs"
        )
    if (
        tuple(int(item) for item in oracle.selected_path_ids)
        != selection.selected_path_ids
    ):
        raise RuntimeError(
            f"{topology_name}: Authority B selected optimum differs"
        )

    internal_paths = tuple(
        path
        for path in oracle.paths
        if path.flags & PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT
    )
    if ownership_profile == "U":
        if internal_paths or checker.internal_conflict_paths:
            raise RuntimeError(f"{topology_name}: unique ownership conflicts")
        if expected_paths and not checker.cross_path_conflicts:
            raise RuntimeError(
                f"{topology_name}: missing unique cross-path conflict"
            )
    elif expected_paths and (
        not internal_paths or not checker.internal_conflict_paths
    ):
        raise RuntimeError(
            f"{topology_name}: collision ownership lacks internal conflict"
        )

    if phase_profile == "N":
        if any(
            path.flags & PATH_FLAG_PHASE_EVIDENCE
            or path.phase_error_count
            or path.phase_error_sum_u64
            for path in oracle.paths
        ):
            raise RuntimeError(f"{topology_name}: phase-off evidence exists")
    elif phase_profile == "Z":
        if any(
            not path.flags & PATH_FLAG_PHASE_EVIDENCE
            or path.phase_error_count == 0
            or path.phase_error_sum_u64 != 0
            for path in oracle.paths
        ):
            raise RuntimeError(f"{topology_name}: zero-phase invariant differs")
    elif expected_paths:
        if any(
            not path.flags & PATH_FLAG_PHASE_EVIDENCE
            or path.phase_error_count == 0
            or path.phase_error_sum_u64 == 0
            for path in oracle.paths
        ):
            raise RuntimeError(
                f"{topology_name}: protected phase invariant differs"
            )
        if not any(
            path.family_flags & PATH_FAMILY_PROTECTED_WEAK
            for path in oracle.paths
        ):
            raise RuntimeError(
                f"{topology_name}: protected path family is absent"
            )

    selected_candidates = int(
        oracle.report["selected_candidate_count"]
    )
    if expected_paths and not 1 <= selected_candidates <= 20:
        raise RuntimeError(
            f"{topology_name}: candidate count is outside exact solver"
        )
    if (
        oracle.report["solver"] != "exact-small-disjoint-heuristic"
        or oracle.report["predictor_integrated"]
        or oracle.report["actual_byte_rdo"]
    ):
        raise RuntimeError(f"{topology_name}: exact analyzer mode differs")


def _checker_semantics(checker: object) -> dict[str, object]:
    subset_digest = hashlib.sha256()
    for subset in checker.conflict_free_subsets:
        for record in path_identity_dict(subset):
            subset_digest.update(repr(record).encode("ascii"))
        subset_digest.update(b"\n")
    return {
        "edges": [asdict(edge) for edge in checker.edges],
        "paths": list(path_identity_dict(checker.paths)),
        "internal_conflict_paths": list(
            path_identity_dict(checker.internal_conflict_paths)
        ),
        "cross_path_conflict_count": len(checker.cross_path_conflicts),
        "conflict_free_subset_count": len(checker.conflict_free_subsets),
        "conflict_free_subset_sha256": subset_digest.hexdigest(),
    }


def candidate_rich_cases() -> Iterator[dict[str, object]]:
    """Yield all 288 audited candidate-rich presentations."""

    case_index = 0
    for topology_name, topology in TOPOLOGIES.items():
        count = len(tuple(topology["centers"]))
        for ownership_profile in OWNERSHIP_PROFILES:
            for phase_profile in PHASE_PROFILES:
                canonical, graph, path = make_case_inputs(
                    topology_name,
                    ownership_profile,
                    phase_profile,
                )
                for permutation in itertools.permutations(range(count)):
                    presented = tuple(
                        canonical[index] for index in permutation
                    )
                    edges = enumerate_edges_fixed(
                        (RESOLUTION,),
                        presented,
                        graph,
                    )
                    oracle = build_paths_fixed(
                        presented,
                        edges,
                        graph,
                        path,
                    )
                    checker = check_graph(
                        [_ctypes_value(RESOLUTION)],
                        [_ctypes_value(item) for item in presented],
                        _ctypes_value(graph),
                        maximum_path_observations=4,
                    )
                    _validate_invariants(
                        topology_name,
                        ownership_profile,
                        phase_profile,
                        oracle,
                        checker,
                        edges,
                        presented,
                        graph,
                        path,
                    )
                    input_fingerprint, input_bytes = input_fingerprint_v1(
                        (RESOLUTION,),
                        presented,
                        edges,
                        graph,
                        path,
                    )
                    yield {
                        "schema": SCHEMA,
                        "generator_id": GENERATOR_ID,
                        "contract_sha256": CONTRACT_SHA256,
                        "campaign": "candidate-rich-exact-valid",
                        "case_index": case_index,
                        "topology": topology_name,
                        "ownership_profile": ownership_profile,
                        "phase_profile": phase_profile,
                        "observation_permutation": list(permutation),
                        "expected_first_status": "OK",
                        "resolutions": [_ctypes_value(RESOLUTION)],
                        "observations": [
                            _ctypes_value(item) for item in presented
                        ],
                        "canonical_edges": [
                            asdict(item) for item in edges
                        ],
                        "graph_manifest": _ctypes_value(graph),
                        "path_manifest": _ctypes_value(path),
                        "authority_b": _checker_semantics(checker),
                        "expected": _path_semantics(
                            oracle,
                            input_fingerprint,
                            input_bytes,
                        ),
                    }
                    case_index += 1
    if case_index != 288:
        raise RuntimeError(
            f"candidate-rich finite domain is {case_index}, expected 288"
        )


def emit_candidate_rich_jsonl(
    destination: Path,
) -> dict[str, object]:
    """Emit the supplement with an independently named inventory."""

    inventory = emit_jsonl(destination, candidate_rich_cases())
    return {
        **inventory,
        "schema": INVENTORY_SCHEMA,
        "generator_id": GENERATOR_ID,
        "contract_sha256": CONTRACT_SHA256,
    }
