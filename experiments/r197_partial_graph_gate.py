from __future__ import annotations

import argparse
import json
from pathlib import Path

from reference.maf_p0.r197_case_generator import (
    emit_jsonl,
    exact_small_cases,
    verify_contract,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT
    / "docs"
    / "reviews"
    / "R197_CASE_GENERATOR_V1_2026-07-29.md"
)
DEFAULT_OUTPUT = (
    ROOT
    / "artifacts"
    / "r197"
    / "r197-exact-small-valid-v1.jsonl"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the frozen independent R-197 exact-small corpus.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    arguments = parser.parse_args()

    contract_sha256 = verify_contract(arguments.contract)
    inventory = emit_jsonl(arguments.output, exact_small_cases())
    inventory["contract_sha256"] = contract_sha256
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
