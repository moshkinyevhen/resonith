"""Execute the isolated R-203 dynamic charge-site mutation campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.r203_dynamic_charge_sites import (
    apply_isolated_mutant,
    evaluate_declared_bound,
    sha256_file,
)


SCHEMA = "resonith-r203-dynamic-charge-mutation-campaign-1"
REPLAY_CLASS_A_FIELDS = (
    "case_count",
    "ordinary_class_ab_case_count",
    "consumed_corpus_sha256",
    "total_path_records",
    "total_entry_records",
    "class_a_semantic_sha256",
    "class_a_packed_output_sha256",
    "twice_replayed",
)
REPLAY_REBUILD_EXCLUDED_FIELDS = frozenset(
    {"native_core", "native_core_sha256", "wall_seconds"}
)
def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def run_command(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    allow_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if process.returncode != 0 and not allow_failure:
        raise RuntimeError(
            "command failed: "
            + json.dumps(command)
            + f"\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process


def parsed_json_stdout(process: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in process.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("command emitted no JSON result")
    value = json.loads(lines[-1])
    if not isinstance(value, dict):
        raise RuntimeError("command JSON result is not an object")
    return value


def _source_line_starts(source: bytes) -> list[int]:
    starts = [0]
    for index, value in enumerate(source):
        if value == 0x0A:
            starts.append(index + 1)
    return starts


def source_line_for_offset(starts: list[int], offset: int) -> int:
    low = 0
    high = len(starts)
    while low < high:
        middle = (low + high) // 2
        if starts[middle] <= offset:
            low = middle + 1
        else:
            high = middle
    return low


def source_position_for_offset(
    starts: list[int],
    offset: int,
) -> tuple[int, int]:
    line = source_line_for_offset(starts, offset)
    return line, offset - starts[line - 1] + 1


def _region_count_at(
    coverage: dict[str, object],
    position: tuple[int, int],
) -> int | None:
    evidence = _region_evidence_at(coverage, position)
    return None if evidence is None else int(evidence["count"])


def _region_evidence_at(
    coverage: dict[str, object],
    position: tuple[int, int],
) -> dict[str, object] | None:
    segments = coverage.get("segments")
    if not isinstance(segments, list):
        raise RuntimeError("coverage export has no source regions")
    grouped: dict[tuple[int, int], list[list[object]]] = {}
    for segment in segments:
        if (
            not isinstance(segment, list)
            or len(segment) < 6
            or not isinstance(segment[0], int)
            or not isinstance(segment[1], int)
        ):
            raise RuntimeError("coverage export contains an invalid segment")
        coordinate = (int(segment[0]), int(segment[1]))
        grouped.setdefault(coordinate, []).append(segment)
    normalized: list[list[object]] = []
    for coordinate in sorted(grouped):
        rows = grouped[coordinate]
        counted = [row for row in rows if row[3] is True]
        if len(counted) > 1:
            raise RuntimeError(
                "coverage export contains duplicate counted segments"
            )
        normalized.append(counted[0] if counted else rows[-1])

    selected_index: int | None = None
    for index, segment in enumerate(normalized):
        coordinate = (int(segment[0]), int(segment[1]))
        if coordinate > position:
            break
        selected_index = index
    if selected_index is None:
        return None
    selected = normalized[selected_index]
    if selected[3] is not True:
        return None
    next_position = (
        [
            int(normalized[selected_index + 1][0]),
            int(normalized[selected_index + 1][1]),
        ]
        if selected_index + 1 < len(normalized)
        else None
    )
    return {
        "count": int(selected[2]),
        "region_begin": [int(selected[0]), int(selected[1])],
        "region_end": next_position,
        "is_region_entry": bool(selected[4]),
        "is_gap_region": bool(selected[5]),
    }


def validate_reachability(
    manifest: dict[str, object],
    source: bytes,
    ordinary_coverage: dict[str, object],
    hostile_coverage: dict[str, object],
    legacy_coverage: dict[str, object],
    contributor_coverage: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    starts = _source_line_starts(source)
    coverage = {
        "ordinary": ordinary_coverage,
        "hostile": hostile_coverage,
        "legacy": legacy_coverage,
    }
    contributors = contributor_coverage or {}
    site_rows = []
    for site in manifest["sites"]:
        position = source_position_for_offset(starts, int(site["offset"]))
        ordinary = _region_count_at(coverage["ordinary"], position)
        hostile = _region_count_at(coverage["hostile"], position)
        if ordinary is None or ordinary <= 0 or hostile is None or hostile <= 0:
            raise RuntimeError(
                f"accounting anchor is not reached by both suites: "
                f"{site['site_id']}"
            )
        site_rows.append(
            {
                "site_id": site["site_id"],
                "event_position": list(position),
                "ordinary_count": ordinary,
                "hostile_count": hostile,
            }
        )

    helper_rows = []
    helper_invocations = manifest.get("validated_helper_invocations")
    if not isinstance(helper_invocations, list):
        raise RuntimeError("validated helper invocation evidence is missing")
    reachability = manifest.get("helper_reachability")
    if not isinstance(reachability, dict):
        raise RuntimeError("helper reachability commitment is missing")
    reachable_records = reachability.get("reachable_helper_invocations")
    unreachable_records = reachability.get(
        "proven_unreachable_helper_invocations"
    )
    if not isinstance(reachable_records, list) or not isinstance(
        unreachable_records,
        list,
    ):
        raise RuntimeError("helper reachability partition is invalid")
    reachable_by_id = {
        str(row["invocation_id"]): row
        for row in reachable_records
        if isinstance(row, dict) and isinstance(row.get("invocation_id"), str)
    }
    unreachable_by_id = {
        str(row["invocation_id"]): row
        for row in unreachable_records
        if isinstance(row, dict) and isinstance(row.get("invocation_id"), str)
    }
    expected_contributors = {
        "ordinary-native",
        "ordinary-greedy",
        "hostile-allocation",
        "hostile-state-arena",
        "hostile-greedy",
    }
    if contributor_coverage is not None and set(contributors) != expected_contributors:
        raise RuntimeError("coverage contributor set differs")
    for helper in helper_invocations:
        position = source_position_for_offset(
            starts,
            int(helper["call_begin"]),
        )
        invocation_id = str(helper["invocation_id"])
        if invocation_id in unreachable_by_id:
            end_position = source_position_for_offset(
                starts,
                int(helper["call_end"]) - 1,
            )
            if contributor_coverage is None:
                witness_counts = {
                    "ordinary": _region_count_at(
                        coverage["ordinary"],
                        position,
                    ),
                    "hostile": _region_count_at(
                        coverage["hostile"],
                        position,
                    ),
                }
                region_spans = {}
            else:
                region_spans = {}
                witness_counts = {}
                for name, value in contributors.items():
                    begin_evidence = _region_evidence_at(value, position)
                    end_evidence = _region_evidence_at(value, end_position)
                    if (
                        begin_evidence is None
                        or end_evidence is None
                        or begin_evidence["region_begin"]
                        != end_evidence["region_begin"]
                        or begin_evidence["region_end"]
                        != end_evidence["region_end"]
                    ):
                        raise RuntimeError(
                            "unreachable helper has no unique exact region: "
                            f"{invocation_id}:{name}"
                        )
                    witness_counts[name] = begin_evidence["count"]
                    region_spans[name] = {
                        "call_begin": list(position),
                        "call_end_inclusive": list(end_position),
                        **begin_evidence,
                    }
            if not all(value == 0 for value in witness_counts.values()):
                raise RuntimeError(
                    "proven-unreachable helper has nonzero or missing coverage: "
                    f"{invocation_id}"
                )
            classification = "proven-unreachable"
        else:
            record = reachable_by_id.get(invocation_id)
            if record is None:
                raise RuntimeError("helper invocation is absent from partition")
            witness_ids = record.get("witness_ids")
            if witness_ids == ["reachability:r203-legacy-exact-noop-v1"]:
                witness_counts = {
                    "legacy": _region_count_at(coverage["legacy"], position)
                }
            else:
                witness_counts = {
                    "ordinary": _region_count_at(
                        coverage["ordinary"],
                        position,
                    ),
                    "hostile": _region_count_at(
                        coverage["hostile"],
                        position,
                    ),
                }
            if not all(
                value is not None and value > 0
                for value in witness_counts.values()
            ):
                raise RuntimeError(
                    f"helper invocation has no reachable witness: {invocation_id}"
                )
            classification = "reachable"
        helper_rows.append(
            {
                "invocation_id": invocation_id,
                "classification": classification,
                "call_position": list(position),
                "witness_counts": witness_counts,
                **(
                    {"exact_region_evidence": region_spans}
                    if classification == "proven-unreachable"
                    else {}
                ),
            }
        )
    if {
        row["invocation_id"] for row in helper_rows
    } != set(reachable_by_id).union(unreachable_by_id):
        raise RuntimeError("coverage helper partition differs")

    release_site = next(
        (
            row
            for row in site_rows
            if row["site_id"] == "arena.reference.consume-release"
        ),
        None,
    )
    reachable_release = next(
        (
            row
            for row in helper_rows
            if row["invocation_id"] == "bounded_state_arena::release@141958"
        ),
        None,
    )
    release_anchor_proof = None
    if manifest.get("expected_site_count") == 36:
        if release_site is None or reachable_release is None:
            raise RuntimeError("release accounting-anchor proof is missing")
        release_position = source_position_for_offset(starts, 137711)
        hostile_state_count = (
            _region_count_at(
                contributors["hostile-state-arena"],
                release_position,
            )
            if contributor_coverage is not None
            else release_site["hostile_count"]
        )
        if (
            release_site["ordinary_count"] <= 0
            or release_site["hostile_count"] <= 0
            or hostile_state_count is None
            or hostile_state_count <= 0
            or reachable_release["classification"] != "reachable"
        ):
            raise RuntimeError(
                "release accounting anchor lacks independent coverage"
            )
        release_anchor_proof = {
            "site_id": "arena.reference.consume-release",
            "site_call_span": [137643, 137760],
            "site_call_ast_sha256":
                "f5ae7a372fac8454f95139f28d466d8e3aa877ec7ba6fe2d8c3ea7d6538497d4",
            "reachable_release_invocation":
                "bounded_state_arena::release@141958",
            "ordinary_count": release_site["ordinary_count"],
            "hostile_count": release_site["hostile_count"],
            "hostile_state_arena_count": hostile_state_count,
        }
    return {
        "site_count": len(site_rows),
        "helper_invocation_count": len(helper_rows),
        "sites": site_rows,
        "helper_invocations": helper_rows,
        "release_anchor_proof": release_anchor_proof,
        "coverage_exports_sha256": {
            name: hashlib.sha256(canonical_json_bytes(value)).hexdigest()
            for name, value in coverage.items()
        },
        "sha256": hashlib.sha256(
            canonical_json_bytes([site_rows, helper_rows])
        ).hexdigest(),
    }


def compare_emit_replay(
    baseline: dict[str, object],
    mutant: dict[str, object],
) -> dict[str, object]:
    if any(baseline[name] != mutant[name] for name in REPLAY_CLASS_A_FIELDS):
        raise RuntimeError("direct-emission mutant changed Class-A evidence")
    if (
        baseline["class_b_non_memory_sha256"]
        == mutant["class_b_non_memory_sha256"]
        or baseline["non_memory_event_totals"]
        == mutant["non_memory_event_totals"]
    ):
        raise RuntimeError("direct-emission mutant survived Class-B evidence")
    return {
        "class_a_preserved": True,
        "class_b_rejected": True,
        "baseline_class_b_sha256": baseline[
            "class_b_non_memory_sha256"
        ],
        "mutant_class_b_sha256": mutant["class_b_non_memory_sha256"],
    }


def compare_restored_replay(
    baseline: dict[str, object],
    restored: dict[str, object],
) -> None:
    baseline_fields = {
        key: value
        for key, value in baseline.items()
        if key not in REPLAY_REBUILD_EXCLUDED_FIELDS
    }
    restored_fields = {
        key: value
        for key, value in restored.items()
        if key not in REPLAY_REBUILD_EXCLUDED_FIELDS
    }
    if baseline_fields != restored_fields:
        raise RuntimeError("restored temporary build changed replay evidence")


def compare_greedy_replay(
    baseline: dict[str, object],
    mutant: dict[str, object],
) -> dict[str, object]:
    for field in ("solver", "candidate_count", "path_count", "class_a_sha256"):
        if baseline.get(field) != mutant.get(field):
            raise RuntimeError("greedy mutant changed Class-A evidence")
    if baseline.get("class_b_sha256") == mutant.get("class_b_sha256"):
        raise RuntimeError("greedy mutant survived Class-B evidence")
    return {
        "class_a_preserved": True,
        "class_b_rejected": True,
        "baseline_class_b_sha256": baseline["class_b_sha256"],
        "mutant_class_b_sha256": mutant["class_b_sha256"],
    }


def validate_witness_files(
    repo: Path,
    manifest: dict[str, object],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for witness in manifest["witnesses"]:
        path_fields = {
            field
            for field in witness
            if not field.endswith("_sha256")
            and field not in {"witness_id", "kind"}
        }
        hash_bases = {
            field[: -len("_sha256")]
            for field in witness
            if field.endswith("_sha256")
        }
        if path_fields != hash_bases:
            raise RuntimeError("witness path and hash fields are not bijective")
        for field in sorted(path_fields):
            value = witness[field]
            if not isinstance(value, str) or not value:
                raise RuntimeError("witness artifact path is invalid")
            expected = witness.get(field + "_sha256")
            path = (repo / value).resolve()
            try:
                path.relative_to(repo)
            except ValueError as error:
                raise RuntimeError(
                    "witness artifact escapes the repository"
                ) from error
            if (
                not path.is_file()
                or not isinstance(expected, str)
                or sha256_file(path) != expected
            ):
                raise RuntimeError(f"witness artifact hash differs: {value}")
            if value in hashes:
                if hashes[value] != expected:
                    raise RuntimeError("witness artifact hash is inconsistent")
                continue
            hashes[value] = expected
    return hashes


def validate_helper_reachability_proof(
    *,
    repo: Path,
    python: Path,
    compile_database: Path,
    manifest: dict[str, object],
) -> dict[str, object]:
    reachability = manifest.get("helper_reachability")
    if not isinstance(reachability, dict):
        raise RuntimeError("helper reachability commitment is missing")
    proof = reachability.get("proof")
    if not isinstance(proof, dict):
        raise RuntimeError("helper reachability proof commitment is missing")
    amendment_relative = reachability.get("amendment_path")
    amendment_sha256 = reachability.get("amendment_sha256")
    if (
        not isinstance(amendment_relative, str)
        or not isinstance(amendment_sha256, str)
    ):
        raise RuntimeError("helper reachability amendment identity is missing")
    amendment = (repo / amendment_relative).resolve()
    try:
        amendment.relative_to(repo.resolve())
    except ValueError as error:
        raise RuntimeError(
            "helper reachability amendment path escapes repository"
        ) from error
    if not amendment.is_file() or sha256_file(amendment) != amendment_sha256:
        raise RuntimeError("helper reachability amendment hash differs")
    required = {
        "verifier_path",
        "verifier_sha256",
        "artifact_path",
        "artifact_sha256",
        "proof_payload_sha256",
    }
    if set(proof) != required:
        raise RuntimeError("helper reachability proof fields differ")

    def committed_file(path_field: str, hash_field: str) -> Path:
        relative = proof.get(path_field)
        expected = proof.get(hash_field)
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(expected, str)
            or len(expected) != 64
        ):
            raise RuntimeError("helper reachability proof identity is invalid")
        path = (repo / relative).resolve()
        try:
            path.relative_to(repo.resolve())
        except ValueError as error:
            raise RuntimeError(
                "helper reachability proof path escapes repository"
            ) from error
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError("helper reachability proof file hash differs")
        return path

    verifier = committed_file("verifier_path", "verifier_sha256")
    artifact = committed_file("artifact_path", "artifact_sha256")
    expected_artifact = json.loads(artifact.read_text(encoding="utf-8"))
    if not isinstance(expected_artifact, dict):
        raise RuntimeError("helper reachability proof artifact is invalid")
    completed = run_command(
        [
            str(python),
            str(verifier),
            "--repo",
            str(repo),
            "--compile-database",
            str(compile_database),
        ],
        cwd=repo,
    )
    actual_artifact = parsed_json_stdout(completed)
    if actual_artifact != expected_artifact:
        raise RuntimeError("helper reachability executable proof differs")
    expected_payload = proof.get("proof_payload_sha256")
    if (
        actual_artifact.get("proof_payload_sha256") != expected_payload
        or actual_artifact.get("status") != "proved-unreachable"
    ):
        raise RuntimeError("helper reachability proof result differs")
    unreachable = reachability.get("proven_unreachable_helper_invocations")
    if (
        not isinstance(unreachable, list)
        or len(unreachable) != 1
        or unreachable[0].get("proof_payload_sha256") != expected_payload
        or unreachable[0].get("invocation_id")
        != actual_artifact.get("invocation", {}).get("invocation_id")
    ):
        raise RuntimeError("unreachable helper proof binding differs")
    return {
        "verifier_path": str(verifier),
        "verifier_sha256": sha256_file(verifier),
        "artifact_path": str(artifact),
        "artifact_sha256": sha256_file(artifact),
        "proof_payload_sha256": expected_payload,
        "amendment_path": str(amendment),
        "amendment_sha256": amendment_sha256,
        "normalized_cfg_sha256": actual_artifact["cfg"][
            "normalized_cfg_sha256"
        ],
        "ast_normalization_configuration_sha256": actual_artifact[
            "ast_normalization"
        ]["configuration_sha256"],
    }


def independent_bound_variables(
    *,
    observation_count: int,
    edge_count: int,
    managed_state_limit: int,
    path_record_limit: int,
    maximum_total_entries: int,
    maximum_path_observations: int,
    exact_candidate_count: int,
) -> dict[str, dict[str, int]]:
    merge_item_budget = (
        4 * observation_count
        + 2 * edge_count
        + managed_state_limit
        + path_record_limit
        + maximum_total_entries
    )
    lookup_query_limit = (
        observation_count
        + managed_state_limit
        + maximum_total_entries
        + path_record_limit * path_record_limit
        + path_record_limit
            * managed_state_limit
            * max(1, maximum_path_observations)
    )
    table_entry_limit = max(
        1,
        observation_count,
        edge_count,
        managed_state_limit,
        path_record_limit,
    )
    return {
        "merge-sort-local": {"item_count": merge_item_budget},
        "binary-search-local": {
            "lookup_queries": lookup_query_limit,
            "table_entries": table_entry_limit,
        },
        "reference-ledger-local": {
            "managed_state_limit": managed_state_limit,
            "maximum_path_observations": maximum_path_observations,
        },
        "state-expansion-local": {
            "observation_count": observation_count,
            "edge_count": edge_count,
            "managed_state_limit": managed_state_limit,
        },
        "selection-pair-local": {
            "candidate_count": path_record_limit,
        },
        "exact-set-local": {
            "exact_candidate_count": exact_candidate_count,
        },
        "backpointer-local": {
            "path_count": path_record_limit,
            "maximum_path_observations": maximum_path_observations,
        },
        "dynamic-aggregate": {
            "observation_count": observation_count,
            "edge_count": edge_count,
            "managed_state_limit": managed_state_limit,
            "path_record_limit": path_record_limit,
            "maximum_path_observations": maximum_path_observations,
            "exact_candidate_count": exact_candidate_count,
        },
    }


def run_independent_bound_campaign(
    *,
    manifest: dict[str, object],
    core: Path,
    corpora: list[tuple[str, Path]],
) -> dict[str, object]:
    from experiments.r197_partial_graph_native_gate import _load_case
    from reference.maf_p0.partial_graph_fixed import (
        NativePartialGraph,
        PATH_WORK_EVENT_NAMES,
    )

    event_index = {
        name: PATH_WORK_EVENT_NAMES.index(name)
        for name in (
            "MERGE_COMPARE",
            "MERGE_MOVE",
            "LOOKUP",
            "STATE",
            "REFERENCE",
            "SELECT",
            "RECONSTRUCT",
        )
    }
    event_names = {
        "RESONITH_PARTIAL_WORK_MERGE_COMPARE": "MERGE_COMPARE",
        "RESONITH_PARTIAL_WORK_MERGE_MOVE": "MERGE_MOVE",
        "RESONITH_PARTIAL_WORK_LOOKUP": "LOOKUP",
        "RESONITH_PARTIAL_WORK_STATE": "STATE",
        "RESONITH_PARTIAL_WORK_REFERENCE": "REFERENCE",
        "RESONITH_PARTIAL_WORK_SELECT": "SELECT",
        "RESONITH_PARTIAL_WORK_RECONSTRUCT": "RECONSTRUCT",
    }
    bounds = {
        str(row["bound_id"]): row
        for row in manifest["bounds"]
    }
    event_bounds: dict[str, set[str]] = {
        name: set() for name in event_index
    }
    for site in manifest["sites"]:
        name = event_names[str(site["event"])]
        event_bounds[name].update(
            value
            for value in site["bound_ids"]
            if value != "dynamic-aggregate"
        )

    native = NativePartialGraph(str(core))
    cases = 0
    phases = 0
    maximum_dynamic = 0
    minimum_aggregate_margin: int | None = None
    minimum_event_margins = {
        name: None for name in event_index
    }
    corpus_rows: list[dict[str, object]] = []
    for corpus_id, corpus in corpora:
        corpus_cases = 0
        corpus_phases = 0
        with corpus.open("rb") as stream:
            for line in stream:
                (
                    _,
                    resolutions,
                    observations,
                    edges,
                    graph,
                    path,
                ) = _load_case(line)
                native.paths(
                    resolutions,
                    observations,
                    edges,
                    graph,
                    path,
                )
                evidence = native.last_path_evidence
                variables = independent_bound_variables(
                    observation_count=len(observations),
                    edge_count=len(edges),
                    managed_state_limit=int(path.maximum_state_records),
                    path_record_limit=int(path.maximum_path_records),
                    maximum_total_entries=int(path.maximum_total_entries),
                    maximum_path_observations=int(
                        path.maximum_path_observations
                    ),
                    exact_candidate_count=int(path.exact_set_candidate_limit),
                )
                values = {
                    bound_id: evaluate_declared_bound(
                        bound,
                        variables[bound_id],
                    )
                    for bound_id, bound in bounds.items()
                }
                for phase in ("preflight_report", "fill_report"):
                    counts = evidence[phase]["work_event_counts"]
                    phase_multiplier = 1 if phase == "preflight_report" else 2
                    dynamic_total = sum(
                        int(counts[index]) for index in event_index.values()
                    )
                    aggregate_margin = (
                        phase_multiplier * values["dynamic-aggregate"]
                        - dynamic_total
                    )
                    if aggregate_margin < 0:
                        raise RuntimeError(
                            f"{corpus_id} case {corpus_cases} {phase} "
                            "exceeds dynamic aggregate bound"
                        )
                    maximum_dynamic = max(maximum_dynamic, dynamic_total)
                    minimum_aggregate_margin = (
                        aggregate_margin
                        if minimum_aggregate_margin is None
                        else min(minimum_aggregate_margin, aggregate_margin)
                    )
                    for name, index in event_index.items():
                        limit = phase_multiplier * sum(
                            values[bound_id]
                            for bound_id in event_bounds[name]
                        )
                        margin = limit - int(counts[index])
                        if margin < 0:
                            raise RuntimeError(
                                f"{corpus_id} case {corpus_cases} {phase} "
                                f"exceeds {name} bound"
                            )
                        current = minimum_event_margins[name]
                        minimum_event_margins[name] = (
                            margin if current is None else min(current, margin)
                        )
                    phases += 1
                    corpus_phases += 1
                cases += 1
                corpus_cases += 1
        if corpus_cases == 0 or corpus_phases != 2 * corpus_cases:
            raise RuntimeError(
                f"independent bound corpus consumed no cases: {corpus_id}"
            )
        corpus_rows.append(
            {
                "corpus_id": corpus_id,
                "path": corpus.name,
                "sha256": sha256_file(corpus),
                "case_count": corpus_cases,
                "phase_count": corpus_phases,
            }
        )
    if cases == 0 or phases != 2 * cases:
        raise RuntimeError("independent bound campaign consumed no cases")
    result = {
        "case_count": cases,
        "phase_count": phases,
        "corpora": corpus_rows,
        "maximum_dynamic_event_units": maximum_dynamic,
        "minimum_aggregate_margin": minimum_aggregate_margin,
        "minimum_event_margins": minimum_event_margins,
        "event_bound_ids": {
            name: sorted(values)
            for name, values in event_bounds.items()
        },
    }
    result["sha256"] = hashlib.sha256(
        canonical_json_bytes(result)
    ).hexdigest()
    return result


def _configure(
    *,
    cmake: Path,
    ninja: Path,
    clang: Path,
    clang_c: Path,
    source: Path,
    build: Path,
    coverage: bool,
    cwd: Path,
) -> None:
    flags = "-fprofile-instr-generate -fcoverage-mapping" if coverage else ""
    linker = "-fprofile-instr-generate" if coverage else ""
    command = [
        str(cmake),
        "-S",
        str(source),
        "-B",
        str(build),
        "-G",
        "Ninja",
        f"-DCMAKE_C_COMPILER={clang_c}",
        f"-DCMAKE_CXX_COMPILER={clang}",
        f"-DCMAKE_MAKE_PROGRAM={ninja}",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_C_FLAGS={flags}",
        f"-DCMAKE_CXX_FLAGS={flags}",
        f"-DCMAKE_EXE_LINKER_FLAGS={linker}",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DRESONITH_BUILD_SHARED=ON",
        "-DRESONITH_BUILD_TOOLS=OFF",
        "-DBUILD_TESTING=ON",
    ]
    run_command(command, cwd=cwd)


def _build(
    cmake: Path,
    build: Path,
    targets: list[str],
    cwd: Path,
) -> None:
    run_command(
        [
            str(cmake),
            "--build",
            str(build),
            "--target",
            *targets,
            "-j",
            str(max(1, min(os.cpu_count() or 1, 16))),
        ],
        cwd=cwd,
    )


def _profile_environment(
    clang: Path,
    pattern: Path,
    base: dict[str, str],
) -> dict[str, str]:
    environment = base.copy()
    environment["PATH"] = str(clang.parent) + os.pathsep + environment["PATH"]
    environment["LLVM_PROFILE_FILE"] = str(pattern)
    return environment


def _merge_profiles(
    llvm_profdata: Path,
    patterns: list[str],
    destination: Path,
    cwd: Path,
) -> None:
    raw = sorted(
        path
        for pattern in patterns
        for path in destination.parent.glob(pattern)
    )
    if not raw:
        raise RuntimeError("coverage witness emitted no raw profile")
    run_command(
        [
            str(llvm_profdata),
            "merge",
            "-sparse",
            *(str(path) for path in raw),
            "-o",
            str(destination),
        ],
        cwd=cwd,
    )


def _coverage_show(
    llvm_cov: Path,
    primary: Path,
    objects: list[Path],
    profile: Path,
    source: Path,
    cwd: Path,
) -> str:
    process = run_command(
        [
            str(llvm_cov),
            "show",
            str(primary),
            *(item for path in objects for item in ("-object", str(path))),
            f"-instr-profile={profile}",
            str(source),
            "-show-line-counts-or-regions",
            "-format=text",
        ],
        cwd=cwd,
    )
    return process.stdout


def _coverage_export(
    llvm_cov: Path,
    primary: Path,
    objects: list[Path],
    profile: Path,
    source: Path,
    cwd: Path,
) -> dict[str, object]:
    process = run_command(
        [
            str(llvm_cov),
            "export",
            str(primary),
            *(item for path in objects for item in ("-object", str(path))),
            f"-instr-profile={profile}",
        ],
        cwd=cwd,
    )
    payload = json.loads(process.stdout)
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1:
        raise RuntimeError("LLVM coverage export has invalid data roots")
    files = data[0].get("files")
    if not isinstance(files, list):
        raise RuntimeError("LLVM coverage export has no file table")
    suffix = source.resolve().as_posix().split("/native/src/", 1)[-1]
    matches = [
        row
        for row in files
        if isinstance(row, dict)
        and str(row.get("filename", ""))
        .replace("\\", "/")
        .endswith("/native/src/" + suffix)
    ]
    if len(matches) != 1:
        raise RuntimeError("LLVM coverage export source identity is ambiguous")
    row = matches[0]
    return {
        "schema": "resonith-r203-llvm-region-export-1",
        "source_suffix": "native/src/" + suffix,
        "segments": row.get("segments"),
        "branches": row.get("branches"),
    }


def _run_candidate_replay(
    *,
    python: Path,
    repo: Path,
    corpus: Path,
    inventory: Path,
    core: Path,
    environment: dict[str, str],
) -> dict[str, object]:
    process = run_command(
        [
            str(python),
            str(repo / "experiments" / "r197_partial_graph_native_gate.py"),
            "--corpus",
            str(corpus),
            "--inventory",
            str(inventory),
            "--native-core",
            str(core),
        ],
        cwd=repo,
        environment=environment,
    )
    return parsed_json_stdout(process)


def _run_greedy_witness(
    *,
    python: Path,
    repo: Path,
    corpus: Path,
    core: Path,
    environment: dict[str, str],
) -> dict[str, object]:
    process = run_command(
        [
            str(python),
            str(repo / "experiments" / "r203_dynamic_charge_witness.py"),
            "--core",
            str(core),
            "--corpus",
            str(corpus),
        ],
        cwd=repo,
        environment=environment,
    )
    return parsed_json_stdout(process)


def _runtime_failure_evidence(
    executables: list[Path],
    *,
    cwd: Path,
    environment: dict[str, str],
    required_typed_executable: str,
    required_marker: str,
) -> dict[str, object]:
    rows = []
    for executable in executables:
        process = run_command(
            [str(executable)],
            cwd=cwd,
            environment=environment,
            allow_failure=True,
        )
        rows.append(
            {
                "executable": executable.name,
                "returncode": process.returncode,
                "stdout_sha256": hashlib.sha256(
                    process.stdout.encode("utf-8")
                ).hexdigest(),
                "stderr_sha256": hashlib.sha256(
                    process.stderr.encode("utf-8")
                ).hexdigest(),
                "typed_marker_present": required_marker
                in (process.stdout + process.stderr),
            }
        )
    if any(row["returncode"] not in {0, 1} for row in rows):
        raise RuntimeError("runtime witness crashed instead of typed rejection")
    typed = next(
        (
            row
            for row in rows
            if row["executable"] == required_typed_executable
        ),
        None,
    )
    if (
        typed is None
        or typed["returncode"] != 1
        or not typed["typed_marker_present"]
    ):
        raise RuntimeError("mutant lacks the required typed rejection marker")
    return {
        "runtime_rejected": True,
        "rejection_channel": required_marker,
        "witnesses": rows,
    }


def _coverage_campaign(
    *,
    arguments: argparse.Namespace,
    manifest: dict[str, object],
    source_root: Path,
    coverage_build: Path,
    artifacts: Path,
    environment: dict[str, str],
) -> dict[str, object]:
    _configure(
        cmake=arguments.cmake,
        ninja=arguments.ninja,
        clang=arguments.clang,
        clang_c=arguments.clang_c,
        source=source_root,
        build=coverage_build,
        coverage=True,
        cwd=arguments.repo,
    )
    _build(
        arguments.cmake,
        coverage_build,
        [
            "resonith_core_shared",
            "resonith_partial_graph_test",
            "resonith_partial_graph_allocation_ordinal_test",
            "resonith_r203_state_arena_hostile_witness",
        ],
        arguments.repo,
    )
    shared = coverage_build / "libresonith_core_shared.dll"
    ordinary = coverage_build / "resonith_partial_graph_test.exe"
    hostile = (
        coverage_build
        / "resonith_partial_graph_allocation_ordinal_test.exe"
    )
    state_hostile = (
        coverage_build
        / "resonith_r203_state_arena_hostile_witness.exe"
    )

    ordinary_environment = _profile_environment(
        arguments.clang,
        artifacts / "ordinary-native-%p.profraw",
        environment,
    )
    run_command([str(ordinary)], cwd=arguments.repo, environment=ordinary_environment)
    greedy_environment = _profile_environment(
        arguments.clang,
        artifacts / "ordinary-greedy-%p.profraw",
        environment,
    )
    _run_greedy_witness(
        python=arguments.python,
        repo=arguments.repo,
        corpus=arguments.corpus,
        core=shared,
        environment=greedy_environment,
    )

    hostile_environment = _profile_environment(
        arguments.clang,
        artifacts / "hostile-allocation-%p.profraw",
        environment,
    )
    run_command([str(hostile)], cwd=arguments.repo, environment=hostile_environment)
    state_hostile_environment = _profile_environment(
        arguments.clang,
        artifacts / "hostile-state-arena-%p.profraw",
        environment,
    )
    run_command(
        [str(state_hostile)],
        cwd=arguments.repo,
        environment=state_hostile_environment,
    )
    hostile_greedy_environment = _profile_environment(
        arguments.clang,
        artifacts / "hostile-greedy-%p.profraw",
        environment,
    )
    _run_greedy_witness(
        python=arguments.python,
        repo=arguments.repo,
        corpus=arguments.corpus,
        core=shared,
        environment=hostile_greedy_environment,
    )

    legacy = coverage_build / "r203_legacy_exact_helper_witness.exe"
    run_command(
        [
            str(arguments.clang),
            "-std=c++23",
            "-O2",
            "-fprofile-instr-generate",
            "-fcoverage-mapping",
            "-I",
            str(source_root / "include"),
            "-I",
            str(source_root / "src"),
            str(
                source_root
                / "tests"
                / "r203_legacy_exact_helper_witness.cpp"
            ),
            "-o",
            str(legacy),
        ],
        cwd=arguments.repo,
        environment=environment,
    )
    legacy_environment = _profile_environment(
        arguments.clang,
        artifacts / "legacy-native-%p.profraw",
        environment,
    )
    run_command([str(legacy)], cwd=arguments.repo, environment=legacy_environment)

    ordinary_profile = artifacts / "ordinary.profdata"
    hostile_profile = artifacts / "hostile.profdata"
    legacy_profile = artifacts / "legacy.profdata"
    _merge_profiles(
        arguments.llvm_profdata,
        ["ordinary-native-*.profraw", "ordinary-greedy-*.profraw"],
        ordinary_profile,
        arguments.repo,
    )
    _merge_profiles(
        arguments.llvm_profdata,
        [
            "hostile-allocation-*.profraw",
            "hostile-state-arena-*.profraw",
            "hostile-greedy-*.profraw",
        ],
        hostile_profile,
        arguments.repo,
    )
    _merge_profiles(
        arguments.llvm_profdata,
        ["legacy-native-*.profraw"],
        legacy_profile,
        arguments.repo,
    )
    contributor_specs = {
        "ordinary-native": (
            ["ordinary-native-*.profraw"],
            ordinary,
            [shared],
        ),
        "ordinary-greedy": (
            ["ordinary-greedy-*.profraw"],
            shared,
            [],
        ),
        "hostile-allocation": (
            ["hostile-allocation-*.profraw"],
            hostile,
            [shared],
        ),
        "hostile-state-arena": (
            ["hostile-state-arena-*.profraw"],
            state_hostile,
            [shared],
        ),
        "hostile-greedy": (
            ["hostile-greedy-*.profraw"],
            shared,
            [],
        ),
    }
    contributor_profiles: dict[str, Path] = {}
    for name, (patterns, _, _) in contributor_specs.items():
        profile = artifacts / f"{name}.profdata"
        _merge_profiles(
            arguments.llvm_profdata,
            patterns,
            profile,
            arguments.repo,
        )
        contributor_profiles[name] = profile

    source = source_root / "src" / "partial_graph.cpp"
    ordinary_text = _coverage_show(
        arguments.llvm_cov,
        ordinary,
        [shared],
        ordinary_profile,
        source,
        arguments.repo,
    )
    hostile_text = _coverage_show(
        arguments.llvm_cov,
        hostile,
        [state_hostile, shared],
        hostile_profile,
        source,
        arguments.repo,
    )
    legacy_text = _coverage_show(
        arguments.llvm_cov,
        legacy,
        [],
        legacy_profile,
        source,
        arguments.repo,
    )
    ordinary_regions = _coverage_export(
        arguments.llvm_cov,
        ordinary,
        [shared],
        ordinary_profile,
        source,
        arguments.repo,
    )
    hostile_regions = _coverage_export(
        arguments.llvm_cov,
        hostile,
        [state_hostile, shared],
        hostile_profile,
        source,
        arguments.repo,
    )
    legacy_regions = _coverage_export(
        arguments.llvm_cov,
        legacy,
        [],
        legacy_profile,
        source,
        arguments.repo,
    )
    contributor_regions = {
        name: _coverage_export(
            arguments.llvm_cov,
            executable,
            objects,
            contributor_profiles[name],
            source,
            arguments.repo,
        )
        for name, (_, executable, objects) in contributor_specs.items()
    }
    (artifacts / "ordinary-coverage.txt").write_text(
        ordinary_text,
        encoding="utf-8",
    )
    (artifacts / "hostile-coverage.txt").write_text(
        hostile_text,
        encoding="utf-8",
    )
    (artifacts / "legacy-coverage.txt").write_text(
        legacy_text,
        encoding="utf-8",
    )
    for name, value in (
        ("ordinary-regions.json", ordinary_regions),
        ("hostile-regions.json", hostile_regions),
        ("legacy-regions.json", legacy_regions),
        *(
            (f"{contributor_name}-regions.json", contributor_value)
            for contributor_name, contributor_value in contributor_regions.items()
        ),
    ):
        (artifacts / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    result = validate_reachability(
        manifest,
        source.read_bytes(),
        ordinary_regions,
        hostile_regions,
        legacy_regions,
        contributor_regions,
    )
    raw_profile_hashes = {
        name: [
            {
                "path": path.name,
                "sha256": sha256_file(path),
            }
            for pattern in patterns
            for path in sorted(artifacts.glob(pattern))
        ]
        for name, (patterns, _, _) in contributor_specs.items()
    }
    result["coverage_provenance"] = {
        "llvm_cov_path": str(arguments.llvm_cov),
        "llvm_cov_sha256": sha256_file(arguments.llvm_cov),
        "llvm_cov_version": run_command(
            [str(arguments.llvm_cov), "--version"],
            cwd=arguments.repo,
        ).stdout.strip(),
        "llvm_profdata_path": str(arguments.llvm_profdata),
        "llvm_profdata_sha256": sha256_file(arguments.llvm_profdata),
        "llvm_profdata_version": run_command(
            [str(arguments.llvm_profdata), "--version"],
            cwd=arguments.repo,
        ).stdout.strip(),
        "coverage_compile_database_sha256": sha256_file(
            coverage_build / "compile_commands.json"
        ),
        "instrumented_objects": {
            path.name: sha256_file(path)
            for path in (shared, ordinary, hostile, state_hostile)
        },
        "raw_profiles": raw_profile_hashes,
        "merged_profiles": {
            path.name: sha256_file(path)
            for path in (
                ordinary_profile,
                hostile_profile,
                legacy_profile,
                *contributor_profiles.values(),
            )
        },
        "coverage_json_schema": "llvm-cov-export-data-2.0.1",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the isolated R-203 charge-site mutation gate.",
    )
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--compile-database", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--production-core", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--cmake", type=Path, required=True)
    parser.add_argument("--ninja", type=Path, required=True)
    parser.add_argument("--clang", type=Path, required=True)
    parser.add_argument("--clang-c", type=Path, required=True)
    parser.add_argument("--llvm-profdata", type=Path, required=True)
    parser.add_argument("--llvm-cov", type=Path, required=True)
    parser.add_argument(
        "--development-mutant",
        help="Run one non-admissible mutant while developing the gate.",
    )
    arguments = parser.parse_args()
    arguments.repo = arguments.repo.resolve()
    arguments.run_root = arguments.run_root.resolve()
    arguments.production_core = arguments.production_core.resolve()
    if arguments.run_root.exists():
        raise RuntimeError("mutation run root already exists")

    started = time.perf_counter()
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    production_core = manifest.get("production_core")
    if not isinstance(production_core, dict):
        raise RuntimeError("audited production-core identity is missing")
    expected_core_path = (
        arguments.repo / str(production_core.get("path", ""))
    ).resolve()
    expected_core_sha256 = production_core.get("sha256")
    if (
        arguments.production_core != expected_core_path
        or not expected_core_path.is_file()
        or not isinstance(expected_core_sha256, str)
        or sha256_file(expected_core_path) != expected_core_sha256
    ):
        raise RuntimeError("production-core path or audited hash differs")
    source_before = arguments.repo / "native" / "src" / "partial_graph.cpp"
    header_before = (
        arguments.repo
        / "native"
        / "include"
        / "resonith"
        / "partial_graph.h"
    )
    frozen_source_sha256 = sha256_file(source_before)
    frozen_header_sha256 = sha256_file(header_before)
    production_core_sha256 = sha256_file(arguments.production_core)
    harness_commitment = manifest.get("harness")
    if not isinstance(harness_commitment, dict):
        raise RuntimeError("audited harness identity is missing")
    expected_harness_paths = {
        "dynamic_charge_sites": "experiments/r203_dynamic_charge_sites.py",
        "mutation_gate": "experiments/r203_dynamic_charge_mutation_gate.py",
        "greedy_witness": "experiments/r203_dynamic_charge_witness.py",
        "helper_reachability_tests":
            "tests/test_r203_helper_reachability_proof.py",
    }
    if set(harness_commitment) != set(expected_harness_paths):
        raise RuntimeError("audited harness component set differs")
    harness_sha256: dict[str, str] = {}
    for name, expected_relative in expected_harness_paths.items():
        row = harness_commitment.get(name)
        if (
            not isinstance(row, dict)
            or row.get("path") != expected_relative
            or not isinstance(row.get("sha256"), str)
        ):
            raise RuntimeError("audited harness row differs")
        path = (arguments.repo / expected_relative).resolve()
        actual_sha256 = sha256_file(path)
        if actual_sha256 != row["sha256"]:
            raise RuntimeError("audited harness hash differs")
        harness_sha256[name] = actual_sha256
    witness_file_hashes = validate_witness_files(arguments.repo, manifest)
    helper_reachability_proof = validate_helper_reachability_proof(
        repo=arguments.repo,
        python=arguments.python,
        compile_database=arguments.compile_database,
        manifest=manifest,
    )
    ordinary_witness = next(
        row for row in manifest["witnesses"] if row["kind"] == "ordinary"
    )
    hostile_witness = next(
        row for row in manifest["witnesses"] if row["kind"] == "hostile"
    )
    audited_corpus = (
        arguments.repo / str(ordinary_witness["candidate_corpus"])
    ).resolve()
    audited_inventory = (
        arguments.repo / str(ordinary_witness["candidate_inventory"])
    ).resolve()
    exact_small_corpus = (
        arguments.repo / str(hostile_witness["exact_small_corpus"])
    ).resolve()
    if (
        arguments.corpus.resolve() != audited_corpus
        or arguments.inventory.resolve() != audited_inventory
    ):
        raise RuntimeError("candidate corpus CLI path differs from manifest")

    validation = run_command(
        [
            str(arguments.python),
            str(arguments.repo / "experiments" / "r203_dynamic_charge_sites.py"),
            "validate",
            "--repo",
            str(arguments.repo),
            "--compile-database",
            str(arguments.compile_database),
            "--manifest",
            str(arguments.manifest),
        ],
        cwd=arguments.repo,
    )
    ast_validation = parsed_json_stdout(validation)
    manifest["validated_helper_invocations"] = ast_validation[
        "helper_invocations"
    ]

    source_tree = arguments.run_root / "source" / "native"
    artifacts = arguments.run_root / "artifacts"
    baseline_build = arguments.run_root / "build"
    coverage_build = arguments.run_root / "coverage-build"
    source_tree.parent.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    shutil.copytree(arguments.repo / "native", source_tree)
    environment = os.environ.copy()
    environment["PATH"] = (
        str(arguments.clang.parent) + os.pathsep + environment["PATH"]
    )
    environment["PYTHONPATH"] = os.pathsep.join(
        [
            str(arguments.repo),
            str(arguments.repo / "reference"),
            environment.get("PYTHONPATH", ""),
        ]
    )

    reachability = _coverage_campaign(
        arguments=arguments,
        manifest=manifest,
        source_root=source_tree,
        coverage_build=coverage_build,
        artifacts=artifacts,
        environment=environment,
    )

    _configure(
        cmake=arguments.cmake,
        ninja=arguments.ninja,
        clang=arguments.clang,
        clang_c=arguments.clang_c,
        source=source_tree,
        build=baseline_build,
        coverage=False,
        cwd=arguments.repo,
    )
    _build(
        arguments.cmake,
        baseline_build,
        [
            "resonith_core_shared",
            "resonith_partial_graph_test",
            "resonith_partial_graph_allocation_ordinal_test",
            "resonith_r203_state_arena_hostile_witness",
        ],
        arguments.repo,
    )
    shared = baseline_build / "libresonith_core_shared.dll"
    ordinary_test = baseline_build / "resonith_partial_graph_test.exe"
    hostile_test = (
        baseline_build
        / "resonith_partial_graph_allocation_ordinal_test.exe"
    )
    state_hostile_test = (
        baseline_build
        / "resonith_r203_state_arena_hostile_witness.exe"
    )
    run_command([str(ordinary_test)], cwd=arguments.repo, environment=environment)
    run_command([str(hostile_test)], cwd=arguments.repo, environment=environment)
    run_command(
        [str(state_hostile_test)],
        cwd=arguments.repo,
        environment=environment,
    )
    baseline_shared_sha256 = sha256_file(shared)
    shutil.copy2(shared, artifacts / "baseline-shared.dll")
    baseline_replay = _run_candidate_replay(
        python=arguments.python,
        repo=arguments.repo,
        corpus=arguments.corpus,
        inventory=arguments.inventory,
        core=shared,
        environment=environment,
    )
    baseline_greedy = _run_greedy_witness(
        python=arguments.python,
        repo=arguments.repo,
        corpus=arguments.corpus,
        core=shared,
        environment=environment,
    )
    bound_campaign = run_independent_bound_campaign(
        manifest=manifest,
        core=shared,
        corpora=[
            ("ordinary:candidate-rich", audited_corpus),
            ("hostile:exact-small", exact_small_corpus),
        ],
    )

    sites_by_mutant: dict[str, tuple[dict[str, object], str]] = {}
    for site in manifest["sites"]:
        sites_by_mutant[str(site["remove_mutant_id"])] = (site, "remove")
        sites_by_mutant[str(site["reclassify_mutant_id"])] = (
            site,
            "reclassify",
        )
    if arguments.development_mutant:
        selected = [arguments.development_mutant]
        if selected[0] not in sites_by_mutant:
            raise RuntimeError("development mutant ID is not in the manifest")
        complete = False
    else:
        selected = sorted(sites_by_mutant)
        complete = True

    isolated_source = source_tree / "src" / "partial_graph.cpp"
    pristine_source = isolated_source.read_bytes()
    mutant_rows = []
    for mutant_id in selected:
        site, kind = sites_by_mutant[mutant_id]
        mutated, mutation_evidence = apply_isolated_mutant(
            pristine_source,
            site,
            kind,
        )
        isolated_source.write_bytes(mutated)
        try:
            if site["operation"] == "emit":
                _build(
                    arguments.cmake,
                    baseline_build,
                    ["resonith_core_shared"],
                    arguments.repo,
                )
                if site["site_id"] == "bounded.greedy-incumbent":
                    mutant_greedy = _run_greedy_witness(
                        python=arguments.python,
                        repo=arguments.repo,
                        corpus=arguments.corpus,
                        core=shared,
                        environment=environment,
                    )
                    rejection = compare_greedy_replay(
                        baseline_greedy,
                        mutant_greedy,
                    )
                else:
                    mutant_replay = _run_candidate_replay(
                        python=arguments.python,
                        repo=arguments.repo,
                        corpus=arguments.corpus,
                        inventory=arguments.inventory,
                        core=shared,
                        environment=environment,
                    )
                    rejection = compare_emit_replay(
                        baseline_replay,
                        mutant_replay,
                    )
            else:
                _build(
                    arguments.cmake,
                    baseline_build,
                    [
                        "resonith_partial_graph_test",
                        "resonith_partial_graph_allocation_ordinal_test",
                        "resonith_r203_state_arena_hostile_witness",
                    ],
                    arguments.repo,
                )
                rejection = _runtime_failure_evidence(
                    [state_hostile_test, ordinary_test, hostile_test],
                    cwd=arguments.repo,
                    environment=environment,
                    required_typed_executable=state_hostile_test.name,
                    required_marker=(
                        "R203_TYPED_REJECTION:state-arena-transaction"
                    ),
                )
            mutant_rows.append(
                {
                    "mutant_id": mutant_id,
                    "site_id": site["site_id"],
                    "operation": site["operation"],
                    "mutation": mutation_evidence,
                    "rejection": rejection,
                }
            )
        finally:
            isolated_source.write_bytes(pristine_source)

    _build(
        arguments.cmake,
        baseline_build,
        [
            "resonith_core_shared",
            "resonith_partial_graph_test",
            "resonith_partial_graph_allocation_ordinal_test",
            "resonith_r203_state_arena_hostile_witness",
        ],
        arguments.repo,
    )
    restored_shared_sha256 = sha256_file(shared)
    run_command([str(ordinary_test)], cwd=arguments.repo, environment=environment)
    run_command([str(hostile_test)], cwd=arguments.repo, environment=environment)
    run_command(
        [str(state_hostile_test)],
        cwd=arguments.repo,
        environment=environment,
    )
    restored_replay = _run_candidate_replay(
        python=arguments.python,
        repo=arguments.repo,
        corpus=arguments.corpus,
        inventory=arguments.inventory,
        core=shared,
        environment=environment,
    )
    compare_restored_replay(baseline_replay, restored_replay)
    if (
        sha256_file(source_before) != frozen_source_sha256
        or sha256_file(header_before) != frozen_header_sha256
        or sha256_file(arguments.production_core) != production_core_sha256
    ):
        raise RuntimeError(
            "production source or object changed during mutation"
        )

    result = {
        "schema": SCHEMA,
        "status": "passed" if complete else "development-partial-passed",
        "complete": complete,
        "manifest_sha256": sha256_file(arguments.manifest),
        "ast_validation": ast_validation,
        "helper_reachability_proof": helper_reachability_proof,
        "reachability": reachability,
        "independent_bounds": bound_campaign,
        "expected_mutant_count": manifest["expected_mutant_count"],
        "executed_mutant_count": len(mutant_rows),
        "baseline_shared_sha256": baseline_shared_sha256,
        "restored_shared_sha256": restored_shared_sha256,
        "temporary_relink_byte_identical":
            restored_shared_sha256 == baseline_shared_sha256,
        "production_source_sha256": frozen_source_sha256,
        "production_header_sha256": frozen_header_sha256,
        "production_core_sha256": production_core_sha256,
        "production_core_path": str(
            arguments.production_core.relative_to(arguments.repo)
        ).replace("\\", "/"),
        "harness_sha256": harness_sha256,
        "witness_file_hashes": witness_file_hashes,
        "mutants": mutant_rows,
        "wall_seconds": time.perf_counter() - started,
    }
    result["campaign_sha256"] = hashlib.sha256(
        canonical_json_bytes(result)
    ).hexdigest()
    result_path = artifacts / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
