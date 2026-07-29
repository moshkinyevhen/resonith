from __future__ import annotations

import ctypes
import os
import random
from dataclasses import replace

import pytest

from reference.maf_p0.partial_graph_fixed import (
    ABI_VERSION,
    LOCALLY_RESOLVABLE,
    MAX_PROTECTED_BANDS,
    PATH_ABI_VERSION,
    PATH_V3_ABI_VERSION,
    PATH_V3_WORK_EVENT_COUNT,
    PATH_WORK_EVENT_NAMES,
    PATH_FAMILY_PROTECTED_WEAK,
    PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT,
    PATH_FLAG_SELECTED,
    PHASE_USABLE,
    PROTECTED_WEAK,
    NativePartialGraph,
    PartialEdge,
    PartialGraphManifest,
    PartialObservation,
    PartialPath,
    PartialPathEntry,
    PartialPathManifest,
    PartialPathReport,
    PartialPathEntryV3,
    PartialPathManifestV3,
    PartialPathReportV3,
    PartialPathV3,
    PartialResolution,
    build_paths_fixed,
    enumerate_edges_fixed,
    half_score_floor,
    log2_one_plus_ratio_q8,
    make_manifest,
    make_observation,
    make_path_manifest,
    make_resolution,
    upgrade_path_manifest_v3,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (-833, -417),
        (-1, -1),
        (0, 0),
        (1, 0),
        (833, 416),
        (-(1 << 62) + 1, -(1 << 61)),
        ((1 << 62) - 1, (1 << 61) - 1),
    ),
)
def test_half_score_floor_has_language_independent_negative_ties(
    value: int,
    expected: int,
) -> None:
    assert half_score_floor(value) == expected


def _fixture():
    sample_rate = 8000
    resolution = make_resolution(7, 1024, 128)
    manifest = make_manifest(
        sample_rate=sample_rate,
        resolution_count=1,
        gaps=(1, 2),
        neighbors_per_gap=2,
        cycle_offsets=(-1, 0, 1),
        maximum_frequency_slope_hz_per_sample_q20=1 << 16,
        maximum_edge_records=1024,
    )
    step_440 = (440 << 32) // sample_rate
    step_442 = (442 << 32) // sample_rate
    observations = (
        make_observation(
            observation_id=10,
            frame_index=0,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=440 << 20,
            phase_turn_u32=0x10000000,
            phase_step_u32=step_440,
            normalized_amplitude_q16=12000 << 16,
            ownership_component=0,
        ),
        make_observation(
            observation_id=11,
            frame_index=1,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=441 << 20,
            phase_turn_u32=0x1CCCCCCD,
            phase_step_u32=step_440,
            normalized_amplitude_q16=11800 << 16,
            ownership_component=1,
        ),
        make_observation(
            observation_id=12,
            frame_index=1,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=900 << 20,
            phase_turn_u32=0x20000000,
            phase_step_u32=0x1CCCCCCD,
            normalized_amplitude_q16=4000 << 16,
            ownership_component=2,
        ),
        make_observation(
            observation_id=13,
            frame_index=2,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=442 << 20,
            phase_turn_u32=0x2999999A,
            phase_step_u32=step_442,
            normalized_amplitude_q16=11600 << 16,
            ownership_component=3,
        ),
        make_observation(
            observation_id=14,
            frame_index=2,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=1500 << 20,
            phase_turn_u32=0x30000000,
            phase_step_u32=0x4CCCCCCD,
            normalized_amplitude_q16=2000 << 16,
            ownership_component=4,
        ),
    )
    return (resolution,), observations, manifest


def test_fixed_abi_sizes_and_integer_log_law() -> None:
    assert ABI_VERSION == 1
    assert ctypes.sizeof(PartialResolution) == 32
    assert ctypes.sizeof(PartialGraphManifest) == 180
    assert ctypes.sizeof(PartialObservation) == 128
    assert ctypes.sizeof(PartialEdge) == 80
    assert log2_one_plus_ratio_q8(0, 1) == 0
    assert log2_one_plus_ratio_q8(1, 1) == 256


def test_transactional_path_v3_abi_layout() -> None:
    assert PATH_V3_ABI_VERSION == 3
    assert PATH_V3_WORK_EVENT_COUNT == 22
    assert ctypes.sizeof(PartialPathManifestV3) == 1232
    assert ctypes.sizeof(PartialPathV3) == 136
    assert ctypes.sizeof(PartialPathEntryV3) == 48
    assert ctypes.sizeof(PartialPathReportV3) == 560
    assert PartialPathManifestV3.work_ledger_version.offset == 60
    assert PartialPathManifestV3.maximum_device_bytes.offset == 144
    assert PartialPathManifestV3.expected_input_fingerprint.offset == 152
    assert PartialPathReportV3.work_event_counts.offset == 304
    assert PartialPathReportV3.reserved_host_bytes.offset == 480
    assert PartialPathReportV3.reserved_device_bytes.offset == 504
    assert PartialPathReportV3.flags.offset == 528

    legacy = make_path_manifest(
        protected_band_upper_hz_q20=(500 << 20,),
    )
    upgraded = upgrade_path_manifest_v3(
        legacy,
        maximum_device_bytes=123456,
    )
    assert upgraded.struct_size == 1232
    assert upgraded.abi_version == PATH_V3_ABI_VERSION
    assert upgraded.maximum_device_bytes == 123456
    assert upgraded.maximum_managed_bytes == legacy.maximum_managed_bytes
    assert upgraded.protected_band_upper_hz_q20[0] == 500 << 20
    assert log2_one_plus_ratio_q8(3, 1) == 512
    assert (
        log2_one_plus_ratio_q8(1, 2)
        < log2_one_plus_ratio_q8(2, 2)
        < log2_one_plus_ratio_q8(4, 2)
    )


def test_python_fixed_oracle_has_canonical_edges_and_separate_costs() -> None:
    resolutions, observations, manifest = _fixture()
    edges = enumerate_edges_fixed(resolutions, observations, manifest)

    assert len(edges) == 9
    assert [edge.candidate_id for edge in edges] == list(range(9))
    assert [edge.cycle_offset for edge in edges[:3]] == [-1, 0, 1]
    assert edges[0].source_observation_id == 10
    assert edges[0].target_observation_id == 11
    assert all(
        edge.provisional_program_cost_q8
        == edge.continuity_cost_q8
        + manifest.continuation_base_bits_q8
        for edge in edges
    )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_cpp23_edge_array_is_bit_exact_to_python_oracle() -> None:
    resolutions, observations, manifest = _fixture()
    expected = enumerate_edges_fixed(
        resolutions,
        observations,
        manifest,
    )
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).edges(
        resolutions,
        observations,
        manifest,
    )

    assert actual == expected


def test_low_confidence_phase_survives_without_phase_cost() -> None:
    resolutions, observations, manifest = _fixture()
    observations = list(observations)
    observations[1].flags = LOCALLY_RESOLVABLE
    edges = enumerate_edges_fixed(
        resolutions,
        tuple(observations),
        manifest,
    )

    assert edges[0].flags == 0
    assert edges[0].phase_error_u31 == 0


def test_edge_candidate_ids_ignore_caller_observation_order() -> None:
    resolutions, observations, manifest = _fixture()
    expected = enumerate_edges_fixed(resolutions, observations, manifest)
    permuted = (
        observations[3],
        observations[0],
        observations[4],
        observations[2],
        observations[1],
    )

    assert enumerate_edges_fixed(resolutions, permuted, manifest) == expected


def _path_fixture(*, repeated_ownership: bool = False):
    resolutions, observations, manifest = _fixture()
    for observation in observations:
        if observation.observation_id in (10, 11, 13):
            observation.flags |= PROTECTED_WEAK
    if repeated_ownership:
        observations[3].ownership_component = (
            observations[0].ownership_component
        )
    edges = enumerate_edges_fixed(resolutions, observations, manifest)
    path_manifest = make_path_manifest(
        protected_band_upper_hz_q20=(
            500 << 20,
            1000 << 20,
            2000 << 20,
        ),
        minimum_path_observations=3,
        top_k_value=8,
        top_k_continuity=8,
        top_k_protected=8,
        maximum_path_records=24,
    )
    return observations, edges, manifest, path_manifest


def test_r191_path_abi_sizes_and_manifest_bounds() -> None:
    assert PATH_ABI_VERSION == 2
    assert MAX_PROTECTED_BANDS == 128
    assert ctypes.sizeof(PartialPathManifest) == 1224
    assert ctypes.sizeof(PartialPath) == 136
    assert ctypes.sizeof(PartialPathEntry) == 48
    assert ctypes.sizeof(PartialPathReport) == 336


def test_fixed_path_oracle_preserves_three_families_and_exact_set() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    result = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert result.report["path_count"] == 8
    assert result.report["entry_count"] == 24
    assert result.report["protected_family_count"] == 2
    assert result.report["solver"] == "exact-small-disjoint-heuristic"
    assert result.selected_path_ids == (0,)
    assert result.paths[0].family_flags & PATH_FAMILY_PROTECTED_WEAK
    assert result.paths[0].flags & PATH_FLAG_SELECTED
    assert all(
        entry.second_order_cost_q8 == 0
        for path in result.paths
        for entry in path.entries
    )


def test_internal_ownership_conflict_never_enters_selected_set() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture(
        repeated_ownership=True,
    )
    result = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert result.report["internal_conflict_count"] == len(result.paths)
    assert not result.selected_path_ids
    assert all(
        path.flags & PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT
        for path in result.paths
    )


def test_lower_median_exact_boundary_belongs_to_upper_band() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    observations[0].frequency_hz_q20 = 450 << 20
    observations[1].frequency_hz_q20 = 500 << 20
    observations[3].frequency_hz_q20 = 550 << 20
    edges = enumerate_edges_fixed(
        (make_resolution(7, 1024, 128),),
        observations,
        graph_manifest,
    )
    result = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert result.paths
    assert all(path.protected_band_id == 1 for path in result.paths)


def test_path_entry_bound_is_explicit_not_silent_pruning() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    path_manifest.maximum_total_entries = 1

    with pytest.raises(OverflowError, match="path-entry bound"):
        build_paths_fixed(
            observations,
            edges,
            graph_manifest,
            path_manifest,
        )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_cpp23_path_union_is_bit_exact_to_python_oracle() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    expected = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        (make_resolution(7, 1024, 128),),
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    permuted = (
        observations[3],
        observations[0],
        observations[4],
        observations[2],
        observations[1],
    )
    permuted_actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        (make_resolution(7, 1024, 128),),
        permuted,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert actual.paths == expected.paths
    assert actual.selected_path_ids == expected.selected_path_ids
    assert permuted_actual.paths == expected.paths
    assert permuted_actual.selected_path_ids == expected.selected_path_ids
    for field in (
        "raw_state_count",
        "path_count",
        "entry_count",
        "selected_candidate_count",
        "selected_path_count",
        "internal_conflict_count",
        "cross_path_conflict_count",
        "score_saturation_count",
        "value_family_count",
        "continuity_family_count",
        "protected_family_count",
        "solver",
    ):
        assert actual.report[field] == expected.report[field]
    assert 0 < actual.report["frontier_peak"] <= expected.report["frontier_peak"]
    assert actual.report["work_units"] > expected.report["work_units"]
    assert actual.report["peak_live_managed_bytes"] > (
        actual.report["path_count"] * ctypes.sizeof(PartialPath)
        + actual.report["entry_count"] * ctypes.sizeof(PartialPathEntry)
    )
    assert actual.report["state_arena_peak"] <= actual.report["raw_state_count"]
    assert (
        actual.report["value_family_presented_count"]
        == actual.report["value_family_count"]
        + actual.report["value_family_discarded_count"]
    )
    assert (
        actual.report["continuity_family_presented_count"]
        == actual.report["continuity_family_count"]
        + actual.report["continuity_family_discarded_count"]
    )
    assert (
        actual.report["protected_family_presented_count"]
        == actual.report["protected_family_count"]
        + actual.report["protected_family_discarded_count"]
    )
    assert actual.report["output_deduplicated_count"] > 0
    assert actual.report["bound_rejected_count"] == 0
    assert actual.report["flags"] & 2
    assert actual.report["input_fingerprint"] == (
        14681656237124231420,
        14217794624446866229,
        3318052838151244206,
        15337156228999464508,
    )
    assert actual.report["output_fingerprint"] == (
        533898623865692396,
        9232259795300133137,
        5802264844233550618,
        5931678949044348120,
    )
    assert (
        actual.report["input_fingerprint"]
        == permuted_actual.report["input_fingerprint"]
    )
    assert (
        actual.report["output_fingerprint"]
        == permuted_actual.report["output_fingerprint"]
    )
    assert actual.report["work_units"] == permuted_actual.report["work_units"]
    assert (
        actual.report["work_event_counts"]
        == permuted_actual.report["work_event_counts"]
    )
    assert (
        actual.report["peak_live_managed_bytes"]
        == permuted_actual.report["peak_live_managed_bytes"]
    )
    assert (
        actual.report["reserved_host_bytes"]
        >= actual.report["committed_host_bytes"]
        >= actual.report["peak_live_host_bytes"]
        > 0
    )
    assert actual.report["reserved_device_bytes"] == 0
    assert actual.report["committed_device_bytes"] == 0
    assert actual.report["peak_live_device_bytes"] == 0
    event_counts = dict(zip(
        PATH_WORK_EVENT_NAMES,
        actual.report["work_event_counts"],
        strict=True,
    ))
    assert actual.report["work_units"] == sum(event_counts.values())
    assert event_counts == {
        "VALIDATE_RECORD": 60,
        "SNAPSHOT_BYTE": 12760,
        "RADIX_BUCKET": 36 * 2 * 256,
        "RADIX_CLASSIFY": 4 + 5 * 32,
        "RADIX_SCATTER": 4 + 5 * 32,
        "MERGE_COMPARE": 298,
        "MERGE_MOVE": 636,
        "GRAPH_SOURCE": 15,
        "GRAPH_GAP": 30,
        "GRAPH_TARGET": 150,
        "GRAPH_CYCLE": 27,
        "EDGE_FIELD": 405,
        "LOOKUP": 2312,
        "STATE": 438,
        "REFERENCE": 710,
        "SELECT": 3538,
        "RECONSTRUCT": 190,
        "MEMORY_PAGE": 1839,
        "STAGE_RECORD": 129,
        "COMMIT_RECORD": 33,
        "FINGERPRINT_BYTE": 9632,
        "CUDA_ITEM": 0,
    }


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_v3_managed_memory_work_and_state_limits_are_exact() -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    resolutions = (make_resolution(7, 1024, 128),)
    native = NativePartialGraph(os.environ["RESONITH_NATIVE_CORE"])
    baseline = native.paths(
        resolutions,
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    for field, measured in (
        (
            "maximum_managed_bytes",
            baseline.report["peak_live_managed_bytes"],
        ),
        ("maximum_work_units", baseline.report["work_units"]),
        ("maximum_state_records", baseline.report["state_arena_peak"]),
        ("maximum_frontier_states", baseline.report["frontier_peak"]),
        ("maximum_total_entries", baseline.report["entry_count"]),
    ):
        rejected = PartialPathManifest.from_buffer_copy(bytes(path_manifest))
        setattr(rejected, field, measured - 1)
        failure_stage = (
            "fill"
            if field in ("maximum_managed_bytes", "maximum_work_units")
            else "preflight"
        )
        with pytest.raises(
            RuntimeError,
            match=rf"{failure_stage} failed: 6",
        ):
            native.paths(
                resolutions,
                observations,
                edges,
                graph_manifest,
                rejected,
            )

        for accepted_limit in (measured, measured + 1):
            accepted = PartialPathManifest.from_buffer_copy(
                bytes(path_manifest)
            )
            setattr(accepted, field, accepted_limit)
            result = native.paths(
                resolutions,
                observations,
                edges,
                graph_manifest,
                accepted,
            )
            assert result.paths == baseline.paths


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
@pytest.mark.parametrize(
    "mutation",
    (
        "missing",
        "extra",
        "permuted",
        "duplicate",
        "center_delta_samples",
        "frequency_delta_hz_q20",
        "gap_hops",
        "cycle_offset",
        "phase_error_u31",
        "continuity_cost_q8",
        "provisional_program_cost_q8",
        "flags",
        "source_observation_id",
        "target_observation_id",
    ),
)
def test_v2_rejects_every_noncanonical_or_forged_edge_stream(
    mutation: str,
) -> None:
    observations, edges, graph_manifest, path_manifest = _path_fixture()
    resolutions = (make_resolution(7, 1024, 128),)
    if mutation == "missing":
        changed = edges[:-1]
    elif mutation == "extra":
        changed = (*edges, replace(edges[-1], candidate_id=len(edges)))
    elif mutation == "permuted":
        changed = (edges[1], edges[0], *edges[2:])
    elif mutation == "duplicate":
        changed = (edges[0], edges[0], *edges[2:])
    elif mutation == "source_observation_id":
        changed = (
            replace(
                edges[0],
                source_observation_id=edges[0].target_observation_id,
            ),
            *edges[1:],
        )
    elif mutation == "target_observation_id":
        changed = (
            replace(
                edges[0],
                target_observation_id=edges[0].source_observation_id,
            ),
            *edges[1:],
        )
    else:
        changed = (
            replace(
                edges[0],
                **{mutation: getattr(edges[0], mutation) ^ 1},
            ),
            *edges[1:],
        )

    with pytest.raises(RuntimeError, match="native path preflight failed"):
        NativePartialGraph(
            os.environ["RESONITH_NATIVE_CORE"]
        ).paths(
            resolutions,
            observations,
            changed,
            graph_manifest,
            path_manifest,
        )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_irregular_time_linear_law_has_zero_second_order_cost() -> None:
    resolution = make_resolution(9, 1024, 128)
    graph_manifest = make_manifest(
        sample_rate=8000,
        resolution_count=1,
        gaps=(1, 2),
        neighbors_per_gap=2,
        cycle_offsets=(-1, 0, 1),
        maximum_frequency_slope_hz_per_sample_q20=1 << 16,
        maximum_edge_records=128,
    )
    observations = tuple(
        make_observation(
            observation_id=identifier,
            frame_index=frame,
            resolution_id=9,
            hop_samples=128,
            frequency_hz_q20=frequency << 20,
            phase_turn_u32=0,
            phase_step_u32=0,
            normalized_amplitude_q16=10000 << 16,
            ownership_component=index,
            flags=LOCALLY_RESOLVABLE | PROTECTED_WEAK,
        )
        for index, (identifier, frame, frequency) in enumerate((
            (20, 0, 440),
            (21, 1, 441),
            (22, 3, 443),
        ))
    )
    edges = enumerate_edges_fixed(
        (resolution,),
        observations,
        graph_manifest,
    )
    path_manifest = make_path_manifest(
        protected_band_upper_hz_q20=(500 << 20,),
        minimum_path_observations=3,
        top_k_value=3,
        top_k_continuity=3,
        top_k_protected=3,
        maximum_path_records=9,
    )
    expected = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        (resolution,),
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert expected.paths
    assert all(
        entry.second_order_cost_q8 == 0
        for path in expected.paths
        for entry in path.entries
    )
    assert actual.paths == expected.paths
    assert actual.report["work_units"] > expected.report["work_units"]


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_randomized_second_order_integer_law_matches_cpp23() -> None:
    generator = random.Random(0x5191)
    native = NativePartialGraph(os.environ["RESONITH_NATIVE_CORE"])
    for case in range(32):
        first_gap = generator.choice((1, 2, 4, 8))
        second_gap = generator.choice((1, 2, 4, 8))
        gaps = tuple(sorted({first_gap, second_gap}))
        resolution = make_resolution(17, 1024, 64)
        graph_manifest = make_manifest(
            sample_rate=16000,
            resolution_count=1,
            gaps=gaps,
            neighbors_per_gap=1,
            cycle_offsets=(0,),
            maximum_frequency_jump_hz_q20=8000 << 20,
            maximum_frequency_slope_hz_per_sample_q20=1 << 20,
            maximum_edge_records=32,
        )
        frames = (0, first_gap, first_gap + second_gap)
        frequencies = (
            generator.randrange(200, 3000),
            generator.randrange(200, 3000),
            generator.randrange(200, 3000),
        )
        amplitudes = (
            generator.randrange(1, 60000),
            generator.randrange(1, 60000),
            generator.randrange(1, 60000),
        )
        observations = tuple(
            make_observation(
                observation_id=case * 10 + index,
                frame_index=frames[index],
                resolution_id=17,
                hop_samples=64,
                frequency_hz_q20=frequencies[index] << 20,
                phase_turn_u32=0,
                phase_step_u32=0,
                normalized_amplitude_q16=amplitudes[index] << 16,
                ownership_component=index,
                flags=LOCALLY_RESOLVABLE | PROTECTED_WEAK,
            )
            for index in range(3)
        )
        edges = enumerate_edges_fixed(
            (resolution,),
            observations,
            graph_manifest,
        )
        path_manifest = make_path_manifest(
            protected_band_upper_hz_q20=(4000 << 20,),
            minimum_path_observations=3,
            k_value_per_state=1,
            k_continuity_per_state=1,
            top_k_value=1,
            top_k_continuity=1,
            top_k_protected=1,
            protected_paths_per_band=1,
            exact_set_candidate_limit=3,
            maximum_path_records=3,
        )
        expected = build_paths_fixed(
            observations,
            edges,
            graph_manifest,
            path_manifest,
        )
        actual = native.paths(
            (resolution,),
            observations,
            edges,
            graph_manifest,
            path_manifest,
        )

        assert actual.paths == expected.paths
        assert actual.selected_path_ids == expected.selected_path_ids


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_deep_backpointer_chain_reclaims_states_without_losing_identity() -> None:
    sample_rate = 8000
    hop_samples = 64
    observation_count = 96
    resolution = make_resolution(23, 1024, hop_samples)
    graph_manifest = make_manifest(
        sample_rate=sample_rate,
        resolution_count=1,
        gaps=(1,),
        neighbors_per_gap=1,
        cycle_offsets=(0,),
        maximum_frequency_jump_hz_q20=1 << 20,
        maximum_frequency_slope_hz_per_sample_q20=1 << 8,
        maximum_edge_records=observation_count,
    )
    phase_step = (440 << 32) // sample_rate
    observations = tuple(
        make_observation(
            observation_id=10_000 + index,
            frame_index=index,
            resolution_id=23,
            hop_samples=hop_samples,
            frequency_hz_q20=440 << 20,
            phase_turn_u32=(phase_step * index * hop_samples) & 0xFFFFFFFF,
            phase_step_u32=phase_step,
            normalized_amplitude_q16=12000 << 16,
            ownership_component=index,
            flags=PHASE_USABLE | LOCALLY_RESOLVABLE | PROTECTED_WEAK,
        )
        for index in range(observation_count)
    )
    edges = enumerate_edges_fixed(
        (resolution,),
        observations,
        graph_manifest,
    )
    path_manifest = make_path_manifest(
        protected_band_upper_hz_q20=(3999 << 20,),
        k_value_per_state=1,
        k_continuity_per_state=1,
        top_k_value=1,
        top_k_continuity=1,
        top_k_protected=1,
        protected_paths_per_band=1,
        minimum_path_observations=3,
        maximum_path_observations=observation_count,
        exact_set_candidate_limit=3,
        maximum_path_records=3,
        maximum_total_entries=3 * observation_count,
        maximum_frontier_states=4 * observation_count,
        maximum_state_records=4 * observation_count,
        maximum_work_units=20_000_000,
        maximum_managed_bytes=64 << 20,
    )
    expected = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        (resolution,),
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )

    assert actual.paths == expected.paths
    assert actual.selected_path_ids == expected.selected_path_ids
    assert max(len(path.entries) for path in actual.paths) == observation_count
    assert actual.report["state_arena_peak"] < actual.report["raw_state_count"]


def _independent_exact_small_selection(paths) -> tuple[int, ...]:
    candidates = tuple(
        path
        for path in paths
        if path.ownership_conflict_count == 0
        and path.selection_score_q8 > 0
    )
    best_score = -1
    best_identity_set = None
    best_ids: tuple[int, ...] = ()
    for mask in range(1 << len(candidates)):
        ownership: set[int] = set()
        chosen = []
        score = 0
        valid = True
        for index, path in enumerate(candidates):
            if mask & (1 << index) == 0:
                continue
            components = {
                entry.ownership_component
                for entry in path.entries
            }
            if ownership.intersection(components):
                valid = False
                break
            ownership.update(components)
            chosen.append(path)
            score += path.selection_score_q8
        if not valid:
            continue
        identity_set = tuple(sorted(
            (
                tuple(entry.observation_id for entry in path.entries),
                tuple(
                    entry.incoming_edge_candidate_id
                    for entry in path.entries
                ),
            )
            for path in chosen
        ))
        if (
            score > best_score
            or (
                score == best_score
                and (
                    best_identity_set is None
                    or identity_set < best_identity_set
                )
            )
        ):
            best_score = score
            best_identity_set = identity_set
            best_ids = tuple(sorted(path.path_id for path in chosen))
    return best_ids


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_randomized_exact_small_matches_independent_bruteforce() -> None:
    base_observations, _, graph_manifest, path_manifest = _path_fixture()
    resolutions = (make_resolution(7, 1024, 128),)
    native = NativePartialGraph(os.environ["RESONITH_NATIVE_CORE"])
    generator = random.Random(0x191B17)

    for _ in range(64):
        observations = []
        for item in base_observations:
            changed = PartialObservation.from_buffer_copy(bytes(item))
            changed.ownership_component = generator.randrange(5)
            changed.potential_node_value_q8 = generator.randrange(
                256,
                1 << 16,
            )
            changed.uncertainty_leakage_penalty_q8 = generator.randrange(
                0,
                512,
            )
            observations.append(changed)
        observations = tuple(observations)
        edges = enumerate_edges_fixed(
            resolutions,
            observations,
            graph_manifest,
        )
        actual = native.paths(
            resolutions,
            observations,
            edges,
            graph_manifest,
            path_manifest,
        )
        assert actual.report["solver"] == "exact-small-disjoint-heuristic"
        assert (
            actual.selected_path_ids
            == _independent_exact_small_selection(actual.paths)
        )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_resolution_and_observation_permutations_are_semantically_exact() -> None:
    resolutions = (
        make_resolution(7, 1024, 128),
        make_resolution(9, 512, 64),
    )
    graph_manifest = make_manifest(
        sample_rate=16000,
        resolution_count=2,
        gaps=(1, 2),
        neighbors_per_gap=2,
        cycle_offsets=(-1, 0, 1),
        maximum_frequency_jump_hz_q20=2000 << 20,
        maximum_frequency_slope_hz_per_sample_q20=1 << 20,
        maximum_edge_records=1024,
    )
    observations = (
        make_observation(
            observation_id=70,
            frame_index=0,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=440 << 20,
            phase_turn_u32=0,
            phase_step_u32=0,
            normalized_amplitude_q16=10000 << 16,
            ownership_component=0,
        ),
        make_observation(
            observation_id=71,
            frame_index=1,
            resolution_id=7,
            hop_samples=128,
            frequency_hz_q20=441 << 20,
            phase_turn_u32=1,
            phase_step_u32=1,
            normalized_amplitude_q16=9000 << 16,
            ownership_component=1,
        ),
        make_observation(
            observation_id=90,
            frame_index=0,
            resolution_id=9,
            hop_samples=64,
            frequency_hz_q20=880 << 20,
            phase_turn_u32=2,
            phase_step_u32=2,
            normalized_amplitude_q16=8000 << 16,
            ownership_component=2,
        ),
        make_observation(
            observation_id=91,
            frame_index=1,
            resolution_id=9,
            hop_samples=64,
            frequency_hz_q20=881 << 20,
            phase_turn_u32=3,
            phase_step_u32=3,
            normalized_amplitude_q16=7000 << 16,
            ownership_component=3,
        ),
    )
    native = NativePartialGraph(os.environ["RESONITH_NATIVE_CORE"])
    canonical_edges = native.edges(
        resolutions,
        observations,
        graph_manifest,
    )
    reversed_edges = native.edges(
        tuple(reversed(resolutions)),
        tuple(reversed(observations)),
        graph_manifest,
    )
    assert reversed_edges == canonical_edges

    path_manifest = make_path_manifest(
        protected_band_upper_hz_q20=(1000 << 20,),
        minimum_path_observations=2,
        top_k_value=4,
        top_k_continuity=4,
        top_k_protected=4,
        maximum_path_records=24,
    )
    canonical = native.paths(
        resolutions,
        observations,
        canonical_edges,
        graph_manifest,
        path_manifest,
    )
    permuted = native.paths(
        tuple(reversed(resolutions)),
        tuple(reversed(observations)),
        canonical_edges,
        graph_manifest,
        path_manifest,
    )
    assert permuted.paths == canonical.paths
    assert permuted.selected_path_ids == canonical.selected_path_ids
    assert (
        permuted.report["input_fingerprint"]
        == canonical.report["input_fingerprint"]
    )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
def test_scalar_extrema_remain_bit_exact_and_bounded() -> None:
    observations, _, graph_manifest, path_manifest = _path_fixture()
    resolutions = (make_resolution(7, 1024, 128),)
    changed = []
    extrema = (
        (-(1 << 31), (1 << 31) - 1, 1, 0, 0),
        ((1 << 31) - 1, 0, (1 << 32) - 1, (1 << 32) - 1, 1 << 31),
    )
    for index, item in enumerate(observations):
        clone = PartialObservation.from_buffer_copy(bytes(item))
        (
            clone.protected_rank_q8,
            clone.neighbor_priority_q8,
            clone.normalized_amplitude_q16,
            clone.phase_turn_u32,
            clone.phase_uncertainty_u31,
        ) = extrema[index % len(extrema)]
        clone.potential_node_value_q8 = (
            (1 << 31) - 1 if index % 2 else -(1 << 31)
        )
        clone.uncertainty_leakage_penalty_q8 = (
            (1 << 31) - 1 if index % 2 else -(1 << 31)
        )
        changed.append(clone)
    observations = tuple(changed)
    edges = enumerate_edges_fixed(
        resolutions,
        observations,
        graph_manifest,
    )
    expected = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        resolutions,
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    assert actual.paths == expected.paths
    assert actual.selected_path_ids == expected.selected_path_ids
    assert actual.report["work_units"] <= path_manifest.maximum_work_units
