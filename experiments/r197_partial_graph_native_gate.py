from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from reference.maf_p0.partial_graph_fixed import (
    EdgeRecord,
    NativePartialGraph,
    PartialGraphManifest,
    PartialObservation,
    PartialPathManifest,
    PartialPathManifestV3,
    PartialPathEntryV3,
    PartialPathV3,
    PartialResolution,
)
from reference.maf_p0.r197_case_generator import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = (
    ROOT
    / "artifacts"
    / "r197"
    / "r197-exact-small-valid-v1.jsonl"
)
MEMORY_PAGE_EVENT_INDEX = 17
RESOURCE_REPORT_FIELDS = {
    "work_units",
    "work_event_counts",
    "reserved_host_bytes",
    "committed_host_bytes",
    "peak_live_host_bytes",
    "peak_live_managed_bytes",
    "reserved_device_bytes",
    "committed_device_bytes",
    "peak_live_device_bytes",
}


def _struct_from_dict(struct_type, values):
    result = struct_type()
    for name, field_type, *_ in struct_type._fields_:
        value = values[name]
        if isinstance(field_type, type) and issubclass(
            field_type,
            ctypes.Array,
        ):
            target = getattr(result, name)
            for index, item in enumerate(value):
                target[index] = item
        else:
            setattr(result, name, value)
    return result


def _legacy_path_manifest(
    manifest: PartialPathManifestV3,
) -> PartialPathManifest:
    result = PartialPathManifest()
    result.struct_size = ctypes.sizeof(result)
    result.abi_version = 2
    for name, *_ in PartialPathManifest._fields_:
        if name in {
            "struct_size",
            "abi_version",
            "reserved_alignment",
        }:
            continue
        source = getattr(manifest, name)
        target = getattr(result, name)
        if isinstance(target, ctypes.Array):
            for index in range(len(target)):
                target[index] = source[index]
        else:
            setattr(result, name, source)
    return result


def _load_case(line: bytes):
    value = json.loads(line)
    resolutions = tuple(
        _struct_from_dict(PartialResolution, item)
        for item in value["resolutions"]
    )
    observations = tuple(
        _struct_from_dict(PartialObservation, item)
        for item in value["observations"]
    )
    graph_manifest = _struct_from_dict(
        PartialGraphManifest,
        value["graph_manifest"],
    )
    path_manifest_v3 = _struct_from_dict(
        PartialPathManifestV3,
        value["path_manifest"],
    )
    edges = tuple(EdgeRecord(**item) for item in value["canonical_edges"])
    return (
        value,
        resolutions,
        observations,
        edges,
        graph_manifest,
        _legacy_path_manifest(path_manifest_v3),
    )


def _semantic_result(result) -> dict[str, object]:
    paths = json.loads(
        canonical_json_bytes([asdict(path) for path in result.paths])
    )
    return {
        "paths": paths,
        "selected_path_ids": list(result.selected_path_ids),
        "report": result.report,
    }


def _expected_typed_payload(expected: dict[str, object]) -> dict[str, object]:
    typed_paths: list[dict[str, object]] = []
    typed_entries: list[dict[str, object]] = []
    entry_offset = 0
    for path in expected["paths"]:
        entries = path["entries"]
        typed_paths.append(
            {
                "struct_size": ctypes.sizeof(PartialPathV3),
                "abi_version": 3,
                "path_id": path["path_id"],
                "entry_offset": entry_offset,
                "entry_count": len(entries),
                "family_flags": path["family_flags"],
                "terminal_observation_id": path[
                    "terminal_observation_id"
                ],
                "continuity_score_q8": path["continuity_score_q8"],
                "potential_node_value_q8": path[
                    "potential_node_value_q8"
                ],
                "uncertainty_leakage_penalty_q8": path[
                    "uncertainty_leakage_penalty_q8"
                ],
                "provisional_program_cost_q8": path[
                    "provisional_program_cost_q8"
                ],
                "selection_score_q8": path["selection_score_q8"],
                "phase_error_sum_u64": path["phase_error_sum_u64"],
                "phase_error_count": path["phase_error_count"],
                "ownership_conflict_count": path[
                    "ownership_conflict_count"
                ],
                "protected_band_id": path["protected_band_id"],
                "value_rank": path["value_rank"],
                "continuity_rank": path["continuity_rank"],
                "protected_rank": path["protected_rank"],
                "flags": path["flags"],
                "reserved": [0] * 5,
            }
        )
        for entry in entries:
            typed_entries.append(
                {
                    "struct_size": ctypes.sizeof(PartialPathEntryV3),
                    "abi_version": 3,
                    "observation_id": entry["observation_id"],
                    "incoming_edge_candidate_id": entry[
                        "incoming_edge_candidate_id"
                    ],
                    "ownership_component": entry["ownership_component"],
                    "second_order_cost_q8": entry[
                        "second_order_cost_q8"
                    ],
                    "flags": entry["flags"],
                    "reserved": [0] * 3,
                }
            )
        entry_offset += len(entries)
    return {"paths": typed_paths, "entries": typed_entries}


def _report_without_resource_telemetry(
    report: dict[str, object],
) -> dict[str, object]:
    return {
        name: value
        for name, value in report.items()
        if name not in RESOURCE_REPORT_FIELDS
    }


def _class_a_evidence(evidence: dict[str, object]) -> dict[str, object]:
    return {
        "preflight_manifest": evidence["preflight_manifest"],
        "fill_manifest": evidence["fill_manifest"],
        "paths": evidence["paths"],
        "entries": evidence["entries"],
        "path_payload_bytes": evidence["path_payload_bytes"],
        "path_payload_sha256": evidence["path_payload_sha256"],
        "entry_payload_bytes": evidence["entry_payload_bytes"],
        "entry_payload_sha256": evidence["entry_payload_sha256"],
        "preflight_report": _report_without_resource_telemetry(
            evidence["preflight_report"]
        ),
        "fill_report": _report_without_resource_telemetry(
            evidence["fill_report"]
        ),
    }


def _non_memory_ledger(report: dict[str, object]) -> dict[str, object]:
    counts = list(report["work_event_counts"])
    if len(counts) != 22 or sum(counts) != report["work_units"]:
        raise RuntimeError("work ledger total does not equal its event vector")
    non_memory_counts = (
        counts[:MEMORY_PAGE_EVENT_INDEX]
        + counts[MEMORY_PAGE_EVENT_INDEX + 1 :]
    )
    return {
        "event_counts": non_memory_counts,
        "work_units": sum(non_memory_counts),
    }


def _resource_telemetry(report: dict[str, object]) -> dict[str, object]:
    counts = list(report["work_event_counts"])
    return {
        "memory_page_events": counts[MEMORY_PAGE_EVENT_INDEX],
        "work_units": report["work_units"],
        "reserved_host_bytes": report["reserved_host_bytes"],
        "committed_host_bytes": report["committed_host_bytes"],
        "peak_live_host_bytes": report["peak_live_host_bytes"],
        "peak_live_managed_bytes": report["peak_live_managed_bytes"],
        "reserved_device_bytes": report["reserved_device_bytes"],
        "committed_device_bytes": report["committed_device_bytes"],
        "peak_live_device_bytes": report["peak_live_device_bytes"],
    }


def _validate_complete_evidence(
    case_index: int,
    evidence: dict[str, object],
    expected: dict[str, object],
) -> None:
    typed = _expected_typed_payload(expected)
    if evidence["paths"] != typed["paths"]:
        raise RuntimeError(f"case {case_index}: raw typed paths differ")
    if evidence["entries"] != typed["entries"]:
        raise RuntimeError(f"case {case_index}: raw typed entries differ")

    preflight = evidence["preflight_report"]
    fill = evidence["fill_report"]
    if (
        preflight["struct_size"] != fill["struct_size"]
        or preflight["abi_version"] != 3
        or fill["abi_version"] != 3
        or preflight["termination"] != fill["termination"]
        or preflight["solver"] != fill["solver"]
        or preflight["required_path_count"] != len(typed["paths"])
        or fill["required_path_count"] != len(typed["paths"])
        or preflight["required_entry_count"] != len(typed["entries"])
        or fill["required_entry_count"] != len(typed["entries"])
        or preflight["written_path_count"] != 0
        or preflight["written_entry_count"] != 0
        or fill["written_path_count"] != len(typed["paths"])
        or fill["written_entry_count"] != len(typed["entries"])
        or any(preflight["reserved"])
        or any(fill["reserved"])
    ):
        raise RuntimeError(
            f"case {case_index}: report header/count parity differs"
        )
    for report_name, report in (("preflight", preflight), ("fill", fill)):
        if (
            len(report["work_event_counts"]) != 22
            or sum(report["work_event_counts"]) != report["work_units"]
            or report["reserved_host_bytes"]
            < report["committed_host_bytes"]
            or report["committed_host_bytes"]
            < report["peak_live_host_bytes"]
            or report["reserved_device_bytes"] != 0
            or report["committed_device_bytes"] != 0
            or report["peak_live_device_bytes"] != 0
        ):
            raise RuntimeError(
                f"case {case_index}: {report_name} ledger/resource law differs"
            )
    if (
        preflight["input_fingerprint"] != fill["input_fingerprint"]
        or preflight["output_fingerprint"] != fill["output_fingerprint"]
        or fill["input_fingerprint"] != expected["input_fingerprint"]
        or fill["output_fingerprint"] != expected["output_fingerprint"]
    ):
        raise RuntimeError(
            f"case {case_index}: complete fingerprint parity differs"
        )
    preflight_manifest = evidence["preflight_manifest"]
    fill_manifest = evidence["fill_manifest"]
    if (
        any(preflight_manifest["expected_input_fingerprint"])
        or fill_manifest["expected_input_fingerprint"]
        != expected["input_fingerprint"]
        or any(preflight_manifest["reserved"])
        or any(fill_manifest["reserved"])
    ):
        raise RuntimeError(
            f"case {case_index}: two-pass manifest identity differs"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay an R-197 JSONL corpus through the public native ABI.",
    )
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    arguments = parser.parse_args()

    inventory = json.loads(arguments.inventory.read_text(encoding="utf-8"))
    required_inventory_fields = {
        "schema",
        "generator_id",
        "contract_sha256",
        "case_count",
        "bytes",
        "sha256",
    }
    if not required_inventory_fields <= inventory.keys():
        raise RuntimeError("evidence inventory is incomplete")
    corpus_bytes = arguments.corpus.read_bytes()
    corpus_sha256 = hashlib.sha256(corpus_bytes).hexdigest()
    if (
        len(corpus_bytes) != inventory["bytes"]
        or corpus_sha256 != inventory["sha256"]
    ):
        raise RuntimeError("corpus bytes do not match the frozen inventory")
    for source in inventory.get("evidence_sources", {}).values():
        source_path = ROOT / source["path"]
        if (
            not source_path.is_file()
            or hashlib.sha256(source_path.read_bytes()).hexdigest()
            != source["sha256"]
        ):
            raise RuntimeError(
                f"evidence source hash differs: {source['path']}"
            )

    native = NativePartialGraph(arguments.native_core)
    semantic_digest = hashlib.sha256()
    typed_semantic_digest = hashlib.sha256()
    packed_semantic_digest = hashlib.sha256()
    class_a_semantic_digest = hashlib.sha256()
    class_a_packed_output_digest = hashlib.sha256()
    class_b_non_memory_digest = hashlib.sha256()
    resource_telemetry_digest = hashlib.sha256()
    expected_semantic_digest = hashlib.sha256()
    source_digest = hashlib.sha256()
    started = time.perf_counter()
    cases = 0
    ordinary_class_ab_cases = 0
    total_paths = 0
    total_entries = 0
    maximum_work_units = 0
    maximum_non_memory_work_units = 0
    maximum_reserved_host_bytes = 0
    maximum_committed_host_bytes = 0
    maximum_peak_live_host_bytes = 0
    non_memory_event_totals = [0] * 21
    memory_page_event_total = 0
    with arguments.corpus.open("rb") as stream:
        for line in stream:
            source_digest.update(line)
            (
                expected_case,
                resolutions,
                observations,
                edges,
                graph_manifest,
                path_manifest,
            ) = _load_case(line)
            if (
                expected_case["generator_id"] != inventory["generator_id"]
                or expected_case["contract_sha256"]
                != inventory["contract_sha256"]
                or (
                    inventory["generator_id"]
                    == "R203-CANDIDATE-RICH-EXACT-1"
                    and (
                        expected_case.get("case_index") != cases
                        or expected_case.get("campaign")
                        != "candidate-rich-exact-valid"
                        or expected_case.get("expected_first_status") != "OK"
                    )
                )
                or (
                    "case_schema" in inventory
                    and expected_case["schema"] != inventory["case_schema"]
                )
            ):
                raise RuntimeError(
                    f"case {cases}: generator/contract identity differs"
                )
            if inventory["generator_id"] == "R203-CANDIDATE-RICH-EXACT-1":
                ordinary_class_ab_cases += 1
            first = native.paths(
                resolutions,
                observations,
                edges,
                graph_manifest,
                path_manifest,
            )
            first_evidence = native.last_path_evidence
            second = native.paths(
                resolutions,
                observations,
                edges,
                graph_manifest,
                path_manifest,
            )
            second_evidence = native.last_path_evidence
            first_semantics = _semantic_result(first)
            if first_semantics != _semantic_result(second):
                raise RuntimeError(
                    f"case {cases}: repeated native result differs"
                )
            if first_evidence != second_evidence:
                raise RuntimeError(
                    f"case {cases}: repeated typed evidence differs"
                )
            expected = expected_case["expected"]
            expected_semantic_digest.update(
                canonical_json_bytes(
                    {
                        "authority_b": expected_case.get("authority_b"),
                        "expected": expected,
                    }
                )
            )
            expected_semantic_digest.update(b"\n")
            _validate_complete_evidence(cases, first_evidence, expected)
            for report_name in ("preflight_report", "fill_report"):
                report_evidence = first_evidence[report_name]
                if (
                    report_evidence["work_units"]
                    > path_manifest.maximum_work_units
                    or report_evidence["reserved_host_bytes"]
                    > path_manifest.maximum_managed_bytes
                    or report_evidence["committed_host_bytes"]
                    > path_manifest.maximum_managed_bytes
                    or report_evidence["peak_live_host_bytes"]
                    > path_manifest.maximum_managed_bytes
                ):
                    raise RuntimeError(
                        f"case {cases}: {report_name} exceeds a manifest ceiling"
                    )
            if first_semantics["paths"] != expected["paths"]:
                raise RuntimeError(f"case {cases}: path union differs")
            if (
                first_semantics["selected_path_ids"]
                != expected["selected_path_ids"]
            ):
                raise RuntimeError(f"case {cases}: selected set differs")
            report = first_semantics["report"]
            semantic_report_fields = (
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
                "predictor_integrated",
                "actual_byte_rdo",
            )
            for name in semantic_report_fields:
                value = expected["algorithm_report"][name]
                if report[name] != value:
                    raise RuntimeError(
                        f"case {cases}: report field {name} differs"
                    )
            if (
                list(report["input_fingerprint"])
                != expected["input_fingerprint"]
            ):
                raise RuntimeError(
                    f"case {cases}: input fingerprint differs"
                )
            if (
                list(report["output_fingerprint"])
                != expected["output_fingerprint"]
            ):
                raise RuntimeError(
                    f"case {cases}: output fingerprint differs"
                )
            if (
                report["work_event_counts"][20]
                != expected["fill_fingerprint_event_count"]
            ):
                raise RuntimeError(
                    f"case {cases}: fingerprint ledger differs"
                )
            semantic_digest.update(canonical_json_bytes(first_semantics))
            semantic_digest.update(b"\n")
            typed_semantic_digest.update(
                canonical_json_bytes(first_evidence)
            )
            typed_semantic_digest.update(b"\n")
            packed_semantic_digest.update(
                bytes.fromhex(first_evidence["case_payload_sha256"])
            )
            class_a_semantic_digest.update(
                canonical_json_bytes(_class_a_evidence(first_evidence))
            )
            class_a_semantic_digest.update(b"\n")
            class_a_packed_output_digest.update(
                bytes.fromhex(first_evidence["path_payload_sha256"])
            )
            class_a_packed_output_digest.update(
                bytes.fromhex(first_evidence["entry_payload_sha256"])
            )
            case_non_memory = {
                "preflight": _non_memory_ledger(
                    first_evidence["preflight_report"]
                ),
                "fill": _non_memory_ledger(first_evidence["fill_report"]),
            }
            class_b_non_memory_digest.update(
                canonical_json_bytes(case_non_memory)
            )
            class_b_non_memory_digest.update(b"\n")
            case_telemetry = {
                "preflight": _resource_telemetry(
                    first_evidence["preflight_report"]
                ),
                "fill": _resource_telemetry(first_evidence["fill_report"]),
            }
            resource_telemetry_digest.update(
                canonical_json_bytes(case_telemetry)
            )
            resource_telemetry_digest.update(b"\n")
            for phase in ("preflight", "fill"):
                ledger = case_non_memory[phase]
                maximum_non_memory_work_units = max(
                    maximum_non_memory_work_units,
                    ledger["work_units"],
                )
                for index, count in enumerate(ledger["event_counts"]):
                    non_memory_event_totals[index] += count
                memory_page_event_total += case_telemetry[phase][
                    "memory_page_events"
                ]
            total_paths += report["path_count"]
            total_entries += report["entry_count"]
            maximum_work_units = max(
                maximum_work_units,
                report["work_units"],
            )
            maximum_reserved_host_bytes = max(
                maximum_reserved_host_bytes,
                report["reserved_host_bytes"],
            )
            maximum_committed_host_bytes = max(
                maximum_committed_host_bytes,
                report["committed_host_bytes"],
            )
            maximum_peak_live_host_bytes = max(
                maximum_peak_live_host_bytes,
                report["peak_live_host_bytes"],
            )
            cases += 1

    if (
        cases != inventory["case_count"]
        or source_digest.hexdigest() != inventory["sha256"]
        or (
            "expected_semantic_sha256" in inventory
            and expected_semantic_digest.hexdigest()
            != inventory["expected_semantic_sha256"]
        )
    ):
        raise RuntimeError("replayed corpus is truncated or substituted")
    native_core_bytes = arguments.native_core.read_bytes()
    result = {
        "schema": "resonith-r203-native-jsonl-replay-2",
        "corpus": arguments.corpus.resolve().as_posix(),
        "inventory": arguments.inventory.resolve().as_posix(),
        "inventory_sha256": hashlib.sha256(
            arguments.inventory.read_bytes()
        ).hexdigest(),
        "consumed_corpus_sha256": source_digest.hexdigest(),
        "native_core": arguments.native_core.resolve().as_posix(),
        "native_core_sha256": hashlib.sha256(native_core_bytes).hexdigest(),
        "case_count": cases,
        "ordinary_class_ab_case_count": ordinary_class_ab_cases,
        "total_path_records": total_paths,
        "total_entry_records": total_entries,
        "maximum_work_units": maximum_work_units,
        "maximum_non_memory_work_units": maximum_non_memory_work_units,
        "non_memory_event_totals": non_memory_event_totals,
        "memory_page_event_total": memory_page_event_total,
        "maximum_reserved_host_bytes": maximum_reserved_host_bytes,
        "maximum_committed_host_bytes": maximum_committed_host_bytes,
        "maximum_peak_live_host_bytes": maximum_peak_live_host_bytes,
        "semantic_sha256": semantic_digest.hexdigest(),
        "typed_semantic_sha256": typed_semantic_digest.hexdigest(),
        "packed_semantic_sha256": packed_semantic_digest.hexdigest(),
        "class_a_semantic_sha256": class_a_semantic_digest.hexdigest(),
        "class_a_packed_output_sha256": (
            class_a_packed_output_digest.hexdigest()
        ),
        "class_b_non_memory_sha256": class_b_non_memory_digest.hexdigest(),
        "resource_telemetry_sha256": resource_telemetry_digest.hexdigest(),
        "resource_telemetry_locally_valid": True,
        "twice_replayed": True,
        "wall_seconds": time.perf_counter() - started,
    }
    print(
        json.dumps(
            result,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
