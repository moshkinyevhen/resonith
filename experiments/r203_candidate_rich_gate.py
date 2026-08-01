"""Emit the independently audited R-203 candidate-rich exact corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference.maf_p0.r203_candidate_rich_generator import (
    SCHEMA,
    emit_candidate_rich_jsonl,
    verify_contract,
)
from reference.maf_p0.r197_case_generator import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT
    / "docs"
    / "reviews"
    / "R203_CANDIDATE_RICH_EXACT_SUPPLEMENT_2026-07-29.md"
)
DEFAULT_OUTPUT = (
    ROOT
    / "artifacts"
    / "r203"
    / "r203-candidate-rich-exact-v1.jsonl"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the complete R-203 candidate-rich supplement.",
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    verify_contract(arguments.contract.resolve())
    inventory = emit_candidate_rich_jsonl(arguments.output)
    expected_digest = hashlib.sha256()
    with arguments.output.open("rb") as stream:
        for line in stream:
            case = json.loads(line)
            expected_digest.update(
                canonical_json_bytes(
                    {
                        "authority_b": case["authority_b"],
                        "expected": case["expected"],
                    }
                )
            )
            expected_digest.update(b"\n")
    source_paths = {
        "generator": (
            ROOT
            / "reference"
            / "maf_p0"
            / "r203_candidate_rich_generator.py"
        ),
        "authority_a": (
            ROOT / "reference" / "maf_p0" / "partial_graph_fixed.py"
        ),
        "authority_b": (
            ROOT / "reference" / "maf_p0" / "r203_graph_checker.py"
        ),
        "generator_cli": Path(__file__).resolve(),
        "native_replay": (
            ROOT / "experiments" / "r197_partial_graph_native_gate.py"
        ),
        "cross_toolchain_comparator": (
            ROOT / "experiments" / "r203_compare_replays.py"
        ),
        "native_candidate_replay": (
            ROOT / "native" / "tests" / "partial_graph_test.cpp"
        ),
        "github_workflow": ROOT / ".github" / "workflows" / "tests.yml",
        "mobile_workflow": ROOT / ".github" / "workflows" / "mobile.yml",
        "r197_contract": (
            ROOT
            / "docs"
            / "reviews"
            / "R197_CASE_GENERATOR_V1_2026-07-29.md"
        ),
        "supplement_contract": arguments.contract.resolve(),
    }
    inventory["expected_semantic_sha256"] = expected_digest.hexdigest()
    inventory["case_schema"] = SCHEMA
    inventory["evidence_sources"] = {
        name: {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for name, path in source_paths.items()
    }
    print(
        json.dumps(
            inventory,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
