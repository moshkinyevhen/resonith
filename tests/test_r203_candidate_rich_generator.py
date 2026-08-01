from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from reference.maf_p0.r197_case_generator import canonical_json_bytes
from reference.maf_p0.r203_candidate_rich_generator import (
    CONTRACT_SHA256,
    candidate_rich_cases,
    verify_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "reviews"
    / "R203_CANDIDATE_RICH_EXACT_SUPPLEMENT_2026-07-29.md"
)
CHECKER = ROOT / "reference" / "maf_p0" / "r203_graph_checker.py"
EXPECTED_CORPUS_SHA256 = (
    "fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7"
)


def test_candidate_rich_contract_is_frozen() -> None:
    assert verify_contract(CONTRACT) == CONTRACT_SHA256


def test_graph_checker_has_no_forbidden_dependency() -> None:
    tree = ast.parse(CHECKER.read_text(encoding="utf-8"))
    imports: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    assert not any(
        name.startswith("reference.maf_p0.partial_graph_fixed")
        or name.startswith("resonith")
        for name in imports
    )
    assert "enumerate_edges_fixed" not in names
    assert "build_paths_fixed" not in names
    assert "NativePartialGraph" not in names


def test_complete_candidate_rich_domain_and_digest() -> None:
    cases = tuple(candidate_rich_cases())
    assert len(cases) == 288
    assert {case["topology"] for case in cases} == {
        "T0",
        "T1",
        "T2",
        "T3",
        "T4",
    }
    assert {case["ownership_profile"] for case in cases} == {"U", "C"}
    assert {case["phase_profile"] for case in cases} == {"N", "Z", "P"}

    digest = hashlib.sha256()
    for case in cases:
        digest.update(canonical_json_bytes(case))
        digest.update(b"\n")
    assert digest.hexdigest() == EXPECTED_CORPUS_SHA256


def test_all_permutations_have_one_canonical_semantic_result() -> None:
    groups: dict[
        tuple[str, str, str],
        set[bytes],
    ] = {}
    for case in candidate_rich_cases():
        key = (
            str(case["topology"]),
            str(case["ownership_profile"]),
            str(case["phase_profile"]),
        )
        semantic = {
            "canonical_edges": case["canonical_edges"],
            "authority_b": case["authority_b"],
            "expected": case["expected"],
        }
        groups.setdefault(key, set()).add(canonical_json_bytes(semantic))
    assert len(groups) == 30
    assert all(len(rows) == 1 for rows in groups.values())
