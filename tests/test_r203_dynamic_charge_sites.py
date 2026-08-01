from __future__ import annotations

import copy

import pytest

from experiments.r203_dynamic_charge_mutation_gate import (
    _profile_environment,
    compare_emit_replay,
    compare_greedy_replay,
    compare_restored_replay,
    independent_bound_variables,
    source_line_for_offset,
    validate_reachability,
    validate_witness_files,
)
from experiments.r203_dynamic_charge_sites import (
    AST_FILTERS,
    AstSite,
    HelperInvocation,
    HELPER_REACHABILITY_PARENT_PREFLIGHT_SHA256,
    HELPER_REACHABILITY_AMENDMENT_PATH,
    HELPER_REACHABILITY_AMENDMENT_SHA256,
    HELPER_REACHABILITY_SCHEMA,
    PARENT_AMENDMENT,
    PARENT_SHA256,
    SCHEMA,
    TokenReference,
    _canonical_json,
    _json_documents,
    _normalized_ast,
    _sha256_bytes,
    apply_isolated_mutant,
    evaluate_bound_expression,
    evaluate_declared_bound,
    extractor_configuration_sha256,
    validate_manifest_evidence,
)


def _site() -> AstSite:
    return AstSite(
        event="RESONITH_PARTIAL_WORK_SELECT",
        operation="emit",
        helper="stable_merge_sort_v1",
        offset=100,
        call_begin=90,
        call_end=140,
        call_ast_sha256="a" * 64,
        ast_filter="compute_paths_bounded",
    )


def _helper() -> HelperInvocation:
    return HelperInvocation(
        helper="stable_merge_sort_v1",
        offset=200,
        call_begin=200,
        call_end=280,
        call_ast_sha256="b" * 64,
        ast_filter="compute_paths_bounded",
    )


def _token() -> TokenReference:
    return TokenReference(
        event="RESONITH_PARTIAL_WORK_SELECT",
        path="partial_graph.cpp",
        line=10,
        column=5,
        offset=100,
    )


def _manifest() -> dict[str, object]:
    site = _site()
    helper = _helper()
    helper_invocation_id = "stable_merge_sort_v1@200"
    helper_partition = [
        {
            "invocation_id": helper_invocation_id,
            **{
                key: helper.evidence()[key]
                for key in (
                    "helper",
                    "call_begin",
                    "call_end",
                    "call_ast_sha256",
                )
            },
            "classification": "reachable",
            "witness_ids": ["ordinary:example", "hostile:example"],
        }
    ]
    return {
        "schema": SCHEMA,
        "parent_amendment": PARENT_AMENDMENT,
        "parent_sha256": PARENT_SHA256,
        "frozen_inputs": {
            "source_sha256": "1" * 64,
            "header_sha256": "2" * 64,
            "clang_sha256": "3" * 64,
            "clang_version": "clang version test",
            "compile_command_sha256": "4" * 64,
            "token_stream_sha256": "5" * 64,
        },
        "extractor": {
            "schema": "resonith-r203-clang-ast-extractor-1",
            "configuration_sha256":
                extractor_configuration_sha256(),
        },
        "expected_site_count": 1,
        "site_inventory_sha256": _sha256_bytes(
            _canonical_json([site.evidence()])
        ),
        "expected_helper_invocation_count": 1,
        "helper_inventory_sha256": _sha256_bytes(
            _canonical_json([helper.evidence()])
        ),
        "helper_reachability": {
            "schema": HELPER_REACHABILITY_SCHEMA,
            "parent_preflight_sha256":
                HELPER_REACHABILITY_PARENT_PREFLIGHT_SHA256,
            "amendment_path": HELPER_REACHABILITY_AMENDMENT_PATH,
            "amendment_sha256": HELPER_REACHABILITY_AMENDMENT_SHA256,
            "helper_inventory_sha256": _sha256_bytes(
                _canonical_json([helper.evidence()])
            ),
            "expected_reachable_count": 1,
            "expected_proven_unreachable_count": 0,
            "partition_sha256": _sha256_bytes(
                _canonical_json(helper_partition)
            ),
            "reachable_helper_invocations": [
                {
                    "invocation_id": helper_invocation_id,
                    "witness_ids": ["ordinary:example", "hostile:example"],
                }
            ],
            "proven_unreachable_helper_invocations": [],
        },
        "expected_mutant_count": 2,
        "required_operations": ["emit"],
        "ast_filters": list(AST_FILTERS),
        "witnesses": [
            {
                "witness_id": "ordinary:example",
                "kind": "ordinary",
                "source_fixture_sha256": "6" * 64,
            },
            {
                "witness_id": "hostile:example",
                "kind": "hostile",
                "source_fixture_sha256": "7" * 64,
            },
        ],
        "helper_groups": [
            {
                "group_id": "group:example",
                "helper": "stable_merge_sort_v1",
                "witness_ids": ["ordinary:example", "hostile:example"],
                "bound_ids": ["select-loop", "dynamic-aggregate"],
            }
        ],
        "sites": [
            {
                "site_id": "select.example",
                "enclosing": "compute_paths_bounded",
                **site.evidence(),
                "reclassify_event": "RESONITH_PARTIAL_WORK_RECONSTRUCT",
                "remove_mutant_id": "REMOVE:select.example",
                "reclassify_mutant_id": "RECLASSIFY:select.example",
                "witness_ids": ["ordinary:example", "hostile:example"],
                "bound_ids": ["select-loop", "dynamic-aggregate"],
                "expected_runtime_rejection": "class-b-ledger-difference",
            }
        ],
        "site_helper_bindings": [
            {
                "site_id": "select.example",
                "group_id": "group:example",
            }
        ],
        "helper_invocations": [
            {
                "invocation_id": "merge.example",
                **helper.evidence(),
                "witness_ids": ["ordinary:example", "hostile:example"],
                "bound_ids": ["select-loop", "dynamic-aggregate"],
            }
        ],
        "validated_helper_invocations": [
            {
                "invocation_id": "stable_merge_sort_v1@200",
                **helper.evidence(),
            }
        ],
        "legacy_reachability_invocations": [],
        "bounds": [
            {
                "bound_id": "select-loop",
                "expression": "candidate_count * candidate_count",
                "variables": ["candidate_count"],
            },
            {
                "bound_id": "dynamic-aggregate",
                "expression": "candidate_count * candidate_count + 1",
                "variables": ["candidate_count"],
            },
        ],
    }


def _validate(manifest: dict[str, object]) -> dict[str, object]:
    return validate_manifest_evidence(
        manifest,
        source_sha256="1" * 64,
        header_sha256="2" * 64,
        clang_sha256="3" * 64,
        clang_version="clang version test",
        compile_command_sha256="4" * 64,
        token_stream_sha256="5" * 64,
        token_references=[_token()],
        sites=[_site()],
        helpers=[_helper()],
    )


def test_validates_exact_manifest_bijection() -> None:
    result = _validate(_manifest())
    assert result["site_count"] == 1
    assert result["helper_invocation_count"] == 1
    assert result["remove_mutant_count"] == 1
    assert result["reclassify_mutant_count"] == 1


def test_rejects_missing_helper_reachability_partition_row() -> None:
    manifest = _manifest()
    manifest["helper_reachability"]["reachable_helper_invocations"] = []
    with pytest.raises(RuntimeError, match="class sizes"):
        _validate(manifest)


def test_rejects_helper_reachability_partition_digest_drift() -> None:
    manifest = _manifest()
    manifest["helper_reachability"]["partition_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="partition digest"):
        _validate(manifest)


def test_rejects_unreachable_helper_ast_identity_drift() -> None:
    manifest = _manifest()
    reachability = manifest["helper_reachability"]
    reachable = reachability["reachable_helper_invocations"].pop()
    reachability["expected_reachable_count"] = 0
    reachability["expected_proven_unreachable_count"] = 1
    reachability["proven_unreachable_helper_invocations"] = [
        {
            "invocation_id": reachable["invocation_id"],
            "helper": "stable_merge_sort_v1",
            "call_begin": 200,
            "call_end": 280,
            "call_ast_sha256": "0" * 64,
            "zero_witness_ids": ["ordinary:example", "hostile:example"],
        }
    ]
    with pytest.raises(RuntimeError, match="unreachable helper AST identity"):
        _validate(manifest)


@pytest.mark.parametrize(
    "field",
    [
        "source_sha256",
        "header_sha256",
        "clang_sha256",
        "compile_command_sha256",
        "token_stream_sha256",
    ],
)
def test_rejects_frozen_input_mismatch(field: str) -> None:
    manifest = _manifest()
    manifest["frozen_inputs"][field] = "f" * 64
    with pytest.raises(RuntimeError, match="frozen input hash differs"):
        _validate(manifest)


def test_rejects_token_ast_inventory_difference() -> None:
    manifest = _manifest()
    with pytest.raises(RuntimeError, match="token and AST"):
        validate_manifest_evidence(
            manifest,
            source_sha256="1" * 64,
            header_sha256="2" * 64,
            clang_sha256="3" * 64,
            clang_version="clang version test",
            compile_command_sha256="4" * 64,
            token_stream_sha256="5" * 64,
            token_references=[
                TokenReference(
                    event="RESONITH_PARTIAL_WORK_LOOKUP",
                    path="partial_graph.cpp",
                    line=10,
                    column=5,
                    offset=100,
                )
            ],
            sites=[_site()],
            helpers=[_helper()],
        )


def test_rejects_missing_ast_anchor() -> None:
    manifest = _manifest()
    manifest["sites"] = []
    with pytest.raises(RuntimeError, match="accounting-anchor sets differ"):
        _validate(manifest)


def test_rejects_changed_ast_subtree() -> None:
    manifest = _manifest()
    manifest["sites"][0]["call_ast_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="call_ast_sha256"):
        _validate(manifest)


def test_rejects_wrong_reclassification_cycle() -> None:
    manifest = _manifest()
    manifest["sites"][0]["reclassify_event"] = (
        "RESONITH_PARTIAL_WORK_REFERENCE"
    )
    with pytest.raises(RuntimeError, match="reclassification cycle"):
        _validate(manifest)


def test_rejects_site_without_witness() -> None:
    manifest = _manifest()
    manifest["sites"][0]["witness_ids"] = []
    with pytest.raises(RuntimeError, match="no immutable witness"):
        _validate(manifest)


def test_rejects_helper_without_witness() -> None:
    manifest = _manifest()
    manifest["helper_groups"][0]["witness_ids"] = []
    with pytest.raises(RuntimeError, match="helper group identity differs"):
        _validate(manifest)


def test_rejects_trivial_global_bound() -> None:
    manifest = _manifest()
    manifest["bounds"][0]["expression"] = "maximum_work_units"
    with pytest.raises(RuntimeError, match="bound is missing or trivial"):
        _validate(manifest)


def test_rejects_missing_hostile_witness_coverage() -> None:
    manifest = _manifest()
    manifest["sites"][0]["witness_ids"] = ["ordinary:example"]
    with pytest.raises(RuntimeError, match="witness coverage differs"):
        _validate(manifest)


def test_rejects_unbound_helper_group() -> None:
    manifest = _manifest()
    manifest["site_helper_bindings"][0]["group_id"] = "group:missing"
    with pytest.raises(RuntimeError, match="helper binding differs"):
        _validate(manifest)


def test_rejects_wrong_mutant_identity() -> None:
    manifest = _manifest()
    manifest["sites"][0]["remove_mutant_id"] = "REMOVE:wrong"
    with pytest.raises(RuntimeError, match="mutant ID differs"):
        _validate(manifest)


def test_rejects_wrong_runtime_rejection_channel() -> None:
    manifest = _manifest()
    manifest["sites"][0]["expected_runtime_rejection"] = "compile-failure"
    with pytest.raises(RuntimeError, match="rejection channel differs"):
        _validate(manifest)


def test_rejects_ast_extractor_identity_change() -> None:
    manifest = _manifest()
    manifest["extractor"]["configuration_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="extractor identity differs"):
        _validate(manifest)


def test_rejects_operation_family_count_drift() -> None:
    manifest = _manifest()
    manifest["required_operations"] = ["emit", "reserve"]
    with pytest.raises(RuntimeError, match="operation-family coverage differs"):
        _validate(manifest)


def test_validation_does_not_mutate_manifest() -> None:
    manifest = _manifest()
    before = copy.deepcopy(manifest)
    _validate(manifest)
    assert manifest == before


def test_json_document_stream_accepts_concatenated_ast_roots() -> None:
    assert list(_json_documents('{"kind":"A"}\n{"kind":"B"}')) == [
        {"kind": "A"},
        {"kind": "B"},
    ]


def test_json_document_stream_rejects_non_object_root() -> None:
    with pytest.raises(RuntimeError, match="not an object"):
        list(_json_documents("[]"))


def test_normalized_ast_drops_ids_offsets_and_types() -> None:
    left = {
        "id": "0x1",
        "kind": "CallExpr",
        "range": {"begin": {"offset": 10}},
        "type": {"qualType": "int"},
        "inner": [
            {
                "id": "0x2",
                "kind": "DeclRefExpr",
                "referencedDecl": {
                    "id": "0x3",
                    "kind": "FunctionDecl",
                    "name": "charge",
                    "type": {"qualType": "void()"},
                },
            }
        ],
    }
    right = copy.deepcopy(left)
    right["id"] = "0xff"
    right["range"]["begin"]["offset"] = 99
    right["type"]["qualType"] = "long"
    assert _normalized_ast(left) == _normalized_ast(right)
    assert _sha256_bytes(
        str(_normalized_ast(left)).encode()
    ) == _sha256_bytes(
        str(_normalized_ast(right)).encode()
    )


def _mutation_site(
    *,
    event: str = "RESONITH_PARTIAL_WORK_SELECT",
    operation: str = "emit",
) -> tuple[bytes, dict[str, object]]:
    call = f"work.charge(1U, {event})".encode()
    source = b"before;" + call + b";after"
    offset = source.index(event.encode())
    begin = source.index(call)
    return source, {
        "site_id": "select.example",
        "event": event,
        "operation": operation,
        "offset": offset,
        "call_begin": begin,
        "call_end": begin + len(call),
    }


def test_reclassify_mutant_changes_only_event_token() -> None:
    source, site = _mutation_site()
    mutated, evidence = apply_isolated_mutant(
        source,
        site,
        "reclassify",
    )
    assert mutated == source.replace(
        b"RESONITH_PARTIAL_WORK_SELECT",
        b"RESONITH_PARTIAL_WORK_RECONSTRUCT",
    )
    assert evidence["event_after"] == "RESONITH_PARTIAL_WORK_RECONSTRUCT"
    assert evidence["source_before_sha256"] == _sha256_bytes(source)
    assert evidence["source_after_sha256"] == _sha256_bytes(mutated)


@pytest.mark.parametrize("operation", ["emit", "reserve"])
def test_statement_remove_mutant_uses_side_effect_free_void_expression(
    operation: str,
) -> None:
    source, site = _mutation_site(operation=operation)
    mutated, evidence = apply_isolated_mutant(source, site, "remove")
    assert mutated == b"before;static_cast<void>(0);after"
    assert evidence["event_after"] is None


@pytest.mark.parametrize("operation", ["cancel", "consume"])
def test_boolean_remove_mutant_keeps_control_flow_reachable(
    operation: str,
) -> None:
    source, site = _mutation_site(operation=operation)
    mutated, _ = apply_isolated_mutant(source, site, "remove")
    assert mutated == b"before;true;after"


def test_mutant_rejects_stale_offset() -> None:
    source, site = _mutation_site()
    site["offset"] = int(site["offset"]) + 1
    with pytest.raises(RuntimeError, match="does not match source"):
        apply_isolated_mutant(source, site, "remove")


def test_mutant_does_not_modify_input_bytes() -> None:
    source, site = _mutation_site()
    before = bytes(source)
    apply_isolated_mutant(source, site, "remove")
    assert source == before


def test_bound_expression_uses_arbitrary_precision_integer_laws() -> None:
    result = evaluate_bound_expression(
        "items * (ceil_log2(items) + 1) + pow2(exact_limit)",
        {"items": 1 << 80, "exact_limit": 20},
    )
    assert result == (1 << 80) * 81 + (1 << 20)


def test_declared_bound_requires_exact_variable_set() -> None:
    bound = {
        "expression": "items * ceil_log2(items)",
        "variables": ["items"],
    }
    assert evaluate_declared_bound(bound, {"items": 8}) == 24
    with pytest.raises(RuntimeError, match="variables differ"):
        evaluate_declared_bound(bound, {"items": 8, "extra": 1})


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "items ** 2",
        "items << 1",
        "-1",
        "pow2(257)",
        "items / 2",
    ],
)
def test_bound_expression_rejects_unsafe_or_unbounded_syntax(
    expression: str,
) -> None:
    with pytest.raises(RuntimeError):
        evaluate_bound_expression(expression, {"items": 8})


def test_bound_expression_rejects_negative_subtraction() -> None:
    with pytest.raises(RuntimeError, match="became negative"):
        evaluate_bound_expression("left - right", {"left": 1, "right": 2})


def test_source_offset_maps_to_one_based_line() -> None:
    starts = [0, 6, 12]
    assert source_line_for_offset(starts, 0) == 1
    assert source_line_for_offset(starts, 5) == 1
    assert source_line_for_offset(starts, 6) == 2
    assert source_line_for_offset(starts, 12) == 3


def test_reachability_requires_both_site_suites_and_helper_witness() -> None:
    manifest = _manifest()
    source = b"site();\nhelper();\n"
    manifest["sites"][0]["offset"] = 0
    manifest["helper_invocations"][0]["call_begin"] = 8
    ordinary = {
        "segments": [
            [1, 1, 2, True, True, False],
            [2, 1, 3, True, True, False],
        ]
    }
    hostile = {
        "segments": [
            [1, 1, 4, True, True, False],
            [2, 1, 5, True, True, False],
        ]
    }
    empty = {"segments": []}
    result = validate_reachability(
        manifest,
        source,
        ordinary,
        hostile,
        empty,
    )
    assert result["site_count"] == 1
    assert result["helper_invocation_count"] == 1

    with pytest.raises(RuntimeError, match="both suites"):
        hostile_zero = copy.deepcopy(hostile)
        hostile_zero["segments"][0][2] = 0
        validate_reachability(
            manifest,
            source,
            ordinary,
            hostile_zero,
            empty,
        )


def test_emit_mutant_requires_class_a_identity_and_class_b_difference() -> None:
    baseline = {
        **{field: field for field in (
            "consumed_corpus_sha256",
            "class_a_semantic_sha256",
            "class_a_packed_output_sha256",
        )},
        "case_count": 1,
        "ordinary_class_ab_case_count": 1,
        "total_path_records": 2,
        "total_entry_records": 3,
        "twice_replayed": True,
        "class_b_non_memory_sha256": "a",
        "non_memory_event_totals": [1, 2],
    }
    mutant = copy.deepcopy(baseline)
    mutant["class_b_non_memory_sha256"] = "b"
    mutant["non_memory_event_totals"] = [0, 3]
    assert compare_emit_replay(baseline, mutant)["class_a_preserved"]

    survivor = copy.deepcopy(baseline)
    with pytest.raises(RuntimeError, match="survived"):
        compare_emit_replay(baseline, survivor)

    class_a_change = copy.deepcopy(mutant)
    class_a_change["total_path_records"] = 4
    with pytest.raises(RuntimeError, match="Class-A"):
        compare_emit_replay(baseline, class_a_change)


def test_restored_replay_ignores_only_binary_path_hash_and_time() -> None:
    baseline = {
        "schema": "replay",
        "class_a_semantic_sha256": "a",
        "class_b_non_memory_sha256": "b",
        "native_core": "baseline.dll",
        "native_core_sha256": "1",
        "wall_seconds": 1.0,
    }
    restored = {
        **baseline,
        "native_core": "restored.dll",
        "native_core_sha256": "2",
        "wall_seconds": 2.0,
    }
    compare_restored_replay(baseline, restored)
    restored["class_b_non_memory_sha256"] = "changed"
    with pytest.raises(RuntimeError, match="replay evidence"):
        compare_restored_replay(baseline, restored)


def test_greedy_mutant_requires_class_a_identity_and_class_b_difference() -> None:
    baseline = {
        "solver": "greedy",
        "candidate_count": 15,
        "path_count": 15,
        "class_a_sha256": "a",
        "class_b_sha256": "b",
    }
    mutant = {**baseline, "class_b_sha256": "c"}
    assert compare_greedy_replay(baseline, mutant)["class_a_preserved"]
    with pytest.raises(RuntimeError, match="survived"):
        compare_greedy_replay(baseline, baseline)


def test_witness_file_validation_is_hash_bound(tmp_path) -> None:
    fixture = tmp_path / "fixture.cpp"
    fixture.write_bytes(b"int main() {}\n")
    digest = _sha256_bytes(fixture.read_bytes())
    manifest = {
        "witnesses": [
            {
                "witness_id": "ordinary:test",
                "kind": "ordinary",
                "source_fixture": "fixture.cpp",
                "source_fixture_sha256": digest,
            }
        ]
    }
    assert validate_witness_files(tmp_path, manifest) == {
        "fixture.cpp": digest
    }
    manifest["witnesses"][0]["source_fixture_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="artifact hash differs"):
        validate_witness_files(tmp_path, manifest)


def test_profile_environment_preserves_frozen_python_path(tmp_path) -> None:
    base = {"PATH": "tools", "PYTHONPATH": "repo;reference"}
    result = _profile_environment(
        tmp_path / "clang++.exe",
        tmp_path / "witness-%p.profraw",
        base,
    )
    assert result["PYTHONPATH"] == "repo;reference"
    assert result["LLVM_PROFILE_FILE"].endswith("witness-%p.profraw")
    assert base == {"PATH": "tools", "PYTHONPATH": "repo;reference"}


def test_independent_bound_variables_use_only_inputs_and_ceilings() -> None:
    values = independent_bound_variables(
        observation_count=10,
        edge_count=20,
        managed_state_limit=30,
        path_record_limit=4,
        maximum_total_entries=40,
        maximum_path_observations=5,
        exact_candidate_count=3,
    )
    assert values["merge-sort-local"] == {"item_count": 154}
    assert values["selection-pair-local"] == {"candidate_count": 4}
    assert values["exact-set-local"] == {"exact_candidate_count": 3}
    assert values["dynamic-aggregate"]["managed_state_limit"] == 30
