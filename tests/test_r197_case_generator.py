from __future__ import annotations

import hashlib
import itertools
import os
from pathlib import Path

import pytest

from reference.maf_p0.partial_graph_fixed import (
    NativePartialGraph,
    build_paths_fixed,
    enumerate_edges_fixed,
    make_resolution,
    upgrade_path_manifest_v3,
)
from reference.maf_p0.r197_case_generator import (
    FingerprintV1,
    FROZEN_CONTRACT_SHA256,
    GENERATOR_ID,
    SplitMix64,
    canonical_json_bytes,
    exact_permutations,
    exact_small_cases,
    fisher_yates,
    input_fingerprint_v1,
    output_fingerprint_v1,
    verify_contract,
)
from tests.test_partial_graph_fixed import _path_fixture


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "reviews"
    / "R197_CASE_GENERATOR_V1_2026-07-29.md"
)


def test_frozen_contract_hash_is_unchanged() -> None:
    assert verify_contract(CONTRACT) == FROZEN_CONTRACT_SHA256


def test_splitmix64_matches_frozen_unsigned_law() -> None:
    generator = SplitMix64(0)
    assert [generator.next() for _ in range(5)] == [
        0xE220A8397B1DCDAF,
        0x6E789E6AA1B965F4,
        0x06C45D188009454F,
        0xF88BB8A8724C81EC,
        0x1B39896A51A8749B,
    ]


@pytest.mark.parametrize(
    ("byte", "expected"),
    (
        (
            0,
            (
                12638153115695167455,
                15243998063910056217,
                16668787273265776859,
                18187008130203222372,
            ),
        ),
        (
            96,
            (
                12638188300067270207,
                15243892510793745849,
                16668611351405254779,
                18187113683319542916,
            ),
        ),
        (
            97,
            (
                12638187200555641996,
                15243893610305374082,
                16668610251893626516,
                18187156564273048137,
            ),
        ),
        (
            149,
            (
                12638305947811488784,
                15243818843514654238,
                16668658630405270088,
                18187178554505614917,
            ),
        ),
        (
            150,
            (
                12638309246346373417,
                15243819943026282471,
                16668675123079694033,
                18187177454993986578,
            ),
        ),
        (
            202,
            (
                12638375217044066077,
                15243797952793717811,
                16668723501591337605,
                18187269813970767054,
            ),
        ),
        (
            203,
            (
                12638374117532437866,
                15244018954630992644,
                16668722402079709342,
                18187268714459138715,
            ),
        ),
        (
            255,
            (
                12638352127299873646,
                15243996964398427984,
                16668788372777405122,
                18187009229714850711,
            ),
        ),
    ),
)
def test_fingerprint_lane_modulo_boundaries(
    byte: int,
    expected: tuple[int, int, int, int],
) -> None:
    fingerprint = FingerprintV1.begin()
    fingerprint.raw(bytes((byte,)))
    assert fingerprint.result() == expected


def test_fisher_yates_consumes_exactly_n_minus_one_draws() -> None:
    left = SplitMix64(0x123456789ABCDEF0)
    right = SplitMix64(0x123456789ABCDEF0)
    permutation = fisher_yates(tuple(range(7)), left)
    for _ in range(6):
        right.next()
    assert sorted(permutation) == list(range(7))
    assert left.state == right.state


def test_exact_small_permutation_law_is_complete_and_distinct() -> None:
    for count in range(6):
        expected = tuple(itertools.permutations(range(count)))
        assert exact_permutations(count, 0, 0) == expected
    for count in (6, 7):
        permutations = exact_permutations(count, 3, 2)
        assert len(permutations) == 64
        assert len(set(permutations)) == 64
        assert all(
            sorted(permutation) == list(range(count))
            for permutation in permutations
        )
        assert permutations == exact_permutations(count, 3, 2)


def test_exact_small_case_count_and_canonical_smoke_digest() -> None:
    count = 0
    digest = hashlib.sha256()
    first = None
    last = None
    for case in exact_small_cases():
        if first is None:
            first = case
        last = case
        count += 1
        if count <= 4 or count > 9020:
            digest.update(canonical_json_bytes(case))
    assert count == 9024
    assert first is not None and last is not None
    assert first["generator_id"] == GENERATOR_ID
    assert first["case_index"] == 0
    assert last["case_index"] == 9023
    assert digest.hexdigest() == (
        "b2e199669f36b4a2250f16780a7bed8e494cfc96116c0fe8a48b6a2539e8ee16"
    )


def test_empty_case_has_frozen_field_serialized_fingerprint_vectors() -> None:
    first = next(exact_small_cases())
    assert first["expected"]["input_fingerprint"] == [
        2296392527128820706,
        3711867056755863561,
        14930584647164826604,
        5571170623147096222,
    ]
    assert first["expected"]["output_fingerprint"] == [
        3906290112812874035,
        7134806953932114106,
        5040910877964447481,
        9808954102653200941,
    ]
    assert first["expected"]["preflight_fingerprint_event_count"] == 1504
    assert first["expected"]["fill_fingerprint_event_count"] == 1552


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared C++23 library",
)
@pytest.mark.parametrize("boundary_byte", (0, 96, 97, 149, 150, 202, 203, 255))
def test_native_fingerprint_matches_independent_boundary_oracle(
    boundary_byte: int,
) -> None:
    observations, _, graph_manifest, path_manifest = _path_fixture()
    graph_manifest.continuation_base_bits_q8 = boundary_byte
    resolution = make_resolution(7, 1024, 128)
    edges = enumerate_edges_fixed(
        (resolution,),
        observations,
        graph_manifest,
    )
    path_manifest_v3 = upgrade_path_manifest_v3(path_manifest)
    oracle = build_paths_fixed(
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    expected_input, _ = input_fingerprint_v1(
        (resolution,),
        observations,
        edges,
        graph_manifest,
        path_manifest_v3,
    )
    expected_output, _ = output_fingerprint_v1(oracle)
    actual = NativePartialGraph(
        os.environ["RESONITH_NATIVE_CORE"]
    ).paths(
        (resolution,),
        observations,
        edges,
        graph_manifest,
        path_manifest,
    )
    assert actual.report["input_fingerprint"] == expected_input
    assert actual.report["output_fingerprint"] == expected_output
    _, input_bytes = input_fingerprint_v1(
        (resolution,),
        observations,
        edges,
        graph_manifest,
        path_manifest_v3,
    )
    _, output_bytes = output_fingerprint_v1(oracle)
    assert actual.report["work_event_counts"][20] == (
        input_bytes + 3 * output_bytes
    )
