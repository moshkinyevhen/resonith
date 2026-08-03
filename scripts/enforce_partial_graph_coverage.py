#!/usr/bin/env python3
"""Enforce the audited R-202 semantic coverage contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "resonith-r202-semantic-coverage-1"


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(f"cannot read JSON {path}: {error}")


def parse_function_report(path: Path, required: tuple[str, ...]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in required:
            continue
        if len(fields) != 10:
            fail(f"unexpected llvm-cov function row: {line}")
        rows[fields[0]] = {
            "regions": int(fields[1]),
            "missed_regions": int(fields[2]),
            "lines": int(fields[4]),
            "missed_lines": int(fields[5]),
            "branches": int(fields[7]),
            "missed_branches": int(fields[8]),
        }
    missing = sorted(set(required) - set(rows))
    if missing:
        fail("coverage functions missing: " + ", ".join(missing))
    return rows


def parse_uncovered_lines(
    path: Path, required: tuple[str, ...]
) -> set[tuple[str, int]]:
    current: str | None = None
    result: set[tuple[str, int]] = set()
    header = re.compile(r"^([^:]+):$")
    source_line = re.compile(r"^\s*(\d+)\|\s*([^|]*)\|")
    for text in path.read_text(encoding="utf-8").splitlines():
        match = header.match(text)
        if match:
            current = match.group(1) if match.group(1) in required else None
            continue
        if current is None:
            continue
        match = source_line.match(text)
        if match and match.group(2).strip() == "0":
            result.add((current, int(match.group(1))))
    return result


def branch_key(
    function: str, branch: list[int], outcome: str
) -> tuple[str, int, int, int, int, str]:
    return (
        function,
        int(branch[0]),
        int(branch[1]),
        int(branch[2]),
        int(branch[3]),
        outcome,
    )


def parse_branch_outcomes(
    path: Path, required: tuple[str, ...]
) -> tuple[set[tuple[Any, ...]], dict[tuple[Any, ...], int]]:
    document = read_json(path)
    try:
        functions = document["data"][0]["functions"]
    except (KeyError, IndexError, TypeError):
        fail("unexpected llvm-cov export schema")

    selected = {item["name"]: item for item in functions if item["name"] in required}
    missing = sorted(set(required) - set(selected))
    if missing:
        fail("coverage export functions missing: " + ", ".join(missing))

    uncovered: set[tuple[Any, ...]] = set()
    counts: dict[tuple[Any, ...], int] = {}
    for function in required:
        for branch in selected[function]["branches"]:
            if len(branch) < 6:
                fail(f"unexpected branch row for {function}: {branch}")
            for outcome, index in (("true", 4), ("false", 5)):
                key = branch_key(function, branch, outcome)
                if key in counts:
                    fail(f"duplicate branch outcome in llvm-cov export: {key}")
                counts[key] = int(branch[index])
                if counts[key] == 0:
                    uncovered.add(key)
    return uncovered, counts


def expand_line_contract(contract: dict[str, Any]) -> tuple[
    set[tuple[str, int]], set[tuple[str, int]]
]:
    declared: set[tuple[str, int]] = set()
    excluded: set[tuple[str, int]] = set()
    for entry in contract.get("uncovered_line_ranges", []):
        function = entry["function"]
        start = int(entry["start"])
        end = int(entry["end"])
        disposition = entry["disposition"]
        if start <= 0 or end < start or not entry.get("reason"):
            fail(f"invalid uncovered line range: {entry}")
        if disposition not in ("tracked-gap", "exclude-unreachable"):
            fail(f"invalid line disposition: {entry}")
        for line in range(start, end + 1):
            key = (function, line)
            if key in declared:
                fail(f"duplicate contracted line: {key}")
            declared.add(key)
            if disposition == "exclude-unreachable":
                excluded.add(key)
    return declared, excluded


def expand_branch_contract(contract: dict[str, Any]) -> tuple[
    set[tuple[Any, ...]], set[tuple[Any, ...]]
]:
    declared: set[tuple[Any, ...]] = set()
    excluded: set[tuple[Any, ...]] = set()
    for entry in contract.get("uncovered_branch_outcomes", []):
        key = (
            entry["function"],
            int(entry["line_start"]),
            int(entry["column_start"]),
            int(entry["line_end"]),
            int(entry["column_end"]),
            entry["outcome"],
        )
        disposition = entry["disposition"]
        if entry["outcome"] not in ("true", "false") or not entry.get("reason"):
            fail(f"invalid uncovered branch outcome: {entry}")
        if disposition not in ("tracked-gap", "exclude-unreachable"):
            fail(f"invalid branch disposition: {entry}")
        if key in declared:
            fail(f"duplicate contracted branch outcome: {key}")
        declared.add(key)
        if disposition == "exclude-unreachable":
            excluded.add(key)
    return declared, excluded


def validate_proof_guards(contract: dict[str, Any], source: bytes) -> None:
    lines = source.splitlines(keepends=True)
    for guard in contract.get("proof_guards", []):
        start = int(guard["start"])
        end = int(guard["end"])
        if start <= 0 or end < start or end > len(lines):
            fail(f"invalid proof-guard range: {guard}")
        actual = sha256(b"".join(lines[start - 1 : end]))
        expected = guard["sha256"].upper()
        if actual != expected:
            fail(
                f"stale proof guard {guard['id']}: "
                f"expected {expected}, got {actual}"
            )


def validate_bound_files(contract: dict[str, Any]) -> None:
    for entry in contract.get("bound_files", []):
        path = Path(entry["path"])
        if path.is_absolute() or ".." in path.parts:
            fail(f"bound file must be repository-relative: {path}")
        try:
            actual = sha256(path.read_bytes())
        except OSError as error:
            fail(f"cannot read bound file {path}: {error}")
        expected = entry["sha256"].upper()
        if actual != expected:
            fail(
                f"bound file hash is stale for {path}: "
                f"expected {expected}, got {actual}"
            )


def percent(covered: int, total: int) -> float:
    return 100.0 if total == 0 else 100.0 * covered / total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--annotated", type=Path, required=True)
    parser.add_argument("--export", dest="export_path", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--llvm-cov-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    contract = read_json(arguments.contract)
    if contract.get("schema") != SCHEMA:
        fail(f"unsupported coverage contract schema: {contract.get('schema')}")
    toolchain = contract.get("admission_toolchain", {})
    toolchain_pattern = toolchain.get("llvm_cov_version_pattern", "")
    if (
        not toolchain.get("id")
        or not toolchain_pattern
        or re.fullmatch(toolchain_pattern, arguments.llvm_cov_version) is None
    ):
        fail(
            "coverage admission toolchain mismatch: "
            f"{arguments.llvm_cov_version!r}"
        )
    required = tuple(contract.get("functions", []))
    if not required or len(set(required)) != len(required):
        fail("coverage contract requires unique target functions")

    source = arguments.source.read_bytes()
    contracted_source = Path(contract.get("source", "")).as_posix()
    actual_source_path = arguments.source.resolve().as_posix()
    if (
        not contracted_source
        or Path(contracted_source).is_absolute()
        or ".." in Path(contracted_source).parts
        or not actual_source_path.endswith("/" + contracted_source)
    ):
        fail(
            "coverage contract source path mismatch: "
            f"{contracted_source} != {actual_source_path}"
        )
    actual_source_hash = sha256(source)
    expected_source_hash = contract.get("source_sha256", "").upper()
    if actual_source_hash != expected_source_hash:
        fail(
            "coverage contract source hash is stale: "
            f"expected {expected_source_hash}, got {actual_source_hash}"
        )
    validate_proof_guards(contract, source)
    validate_bound_files(contract)

    rows = parse_function_report(arguments.report, required)
    actual_lines = parse_uncovered_lines(arguments.annotated, required)
    declared_lines, excluded_lines = expand_line_contract(contract)
    if actual_lines != declared_lines:
        fail(
            "uncovered line set drifted: "
            f"new={sorted(actual_lines - declared_lines)}, "
            f"stale={sorted(declared_lines - actual_lines)}"
        )

    actual_branches, branch_counts = parse_branch_outcomes(
        arguments.export_path, required
    )
    declared_branches, excluded_branches = expand_branch_contract(contract)
    if actual_branches != declared_branches:
        fail(
            "uncovered branch set drifted: "
            f"new={sorted(actual_branches - declared_branches)}, "
            f"stale={sorted(declared_branches - actual_branches)}"
        )
    if any(branch_counts[key] != 0 for key in excluded_branches):
        fail("an excluded branch outcome unexpectedly became covered")

    line_total = sum(row["lines"] for row in rows.values())
    line_missed = sum(row["missed_lines"] for row in rows.values())
    branch_total = sum(row["branches"] for row in rows.values())
    branch_missed = sum(row["missed_branches"] for row in rows.values())
    if line_missed != len(actual_lines):
        fail(
            f"llvm-cov line summary mismatch: {line_missed} != {len(actual_lines)}"
        )
    if branch_missed != len(actual_branches):
        fail(
            "llvm-cov branch summary mismatch: "
            f"{branch_missed} != {len(actual_branches)}"
        )

    adjusted_line_total = line_total - len(excluded_lines)
    adjusted_line_missed = line_missed - len(excluded_lines)
    adjusted_branch_total = branch_total - len(excluded_branches)
    adjusted_branch_missed = branch_missed - len(excluded_branches)
    raw_line_percent = percent(line_total - line_missed, line_total)
    raw_branch_percent = percent(branch_total - branch_missed, branch_total)
    adjusted_line_percent = percent(
        adjusted_line_total - adjusted_line_missed, adjusted_line_total
    )
    adjusted_branch_percent = percent(
        adjusted_branch_total - adjusted_branch_missed, adjusted_branch_total
    )
    line_floor = float(contract["line_floor"])
    branch_floor = float(contract["branch_floor"])

    result = {
        "schema": SCHEMA,
        "admission_toolchain": {
            "id": toolchain["id"],
            "llvm_cov_version": arguments.llvm_cov_version,
        },
        "source_sha256": actual_source_hash,
        "functions": rows,
        "raw": {
            "lines": line_total,
            "missed_lines": line_missed,
            "line_percent": raw_line_percent,
            "branches": branch_total,
            "missed_branches": branch_missed,
            "branch_percent": raw_branch_percent,
        },
        "excluded_unreachable": {
            "lines": len(excluded_lines),
            "branch_outcomes": len(excluded_branches),
        },
        "adjusted": {
            "lines": adjusted_line_total,
            "missed_lines": adjusted_line_missed,
            "line_percent": adjusted_line_percent,
            "line_floor": line_floor,
            "branches": adjusted_branch_total,
            "missed_branches": adjusted_branch_missed,
            "branch_percent": adjusted_branch_percent,
            "branch_floor": branch_floor,
        },
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if adjusted_line_percent < line_floor or adjusted_branch_percent < branch_floor:
        fail(
            "coverage floor missed: "
            f"lines={adjusted_line_percent:.2f}, "
            f"branches={adjusted_branch_percent:.2f}"
        )


if __name__ == "__main__":
    main()
