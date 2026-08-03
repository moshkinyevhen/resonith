from __future__ import annotations

import copy

import pytest

from experiments.r203_compare_replays import compare_replay_rows
from experiments.r197_partial_graph_native_gate import (
    _non_memory_ledger,
    _report_without_resource_telemetry,
)


def _row(index: int) -> dict[str, object]:
    return {
        "schema": "resonith-r203-native-jsonl-replay-2",
        "case_count": 288,
        "ordinary_class_ab_case_count": 288,
        "consumed_corpus_sha256": "a" * 64,
        "total_path_records": 1620,
        "total_entry_records": 3924,
        "maximum_non_memory_work_units": 575000,
        "non_memory_event_totals": [index_value for index_value in range(21)],
        "class_a_semantic_sha256": "b" * 64,
        "class_a_packed_output_sha256": "c" * 64,
        "class_b_non_memory_sha256": "d" * 64,
        "twice_replayed": True,
        "memory_page_event_total": 1000 + index,
        "maximum_work_units": 576000 + index,
        "maximum_reserved_host_bytes": 26000 + index,
        "maximum_committed_host_bytes": 25000 + index,
        "maximum_peak_live_host_bytes": 24000 + index,
        "resource_telemetry_sha256": f"{index + 1:064x}",
        "resource_telemetry_locally_valid": True,
        "native_core_sha256": f"{index + 101:064x}",
    }


def test_accepts_distinct_locally_valid_resource_telemetry() -> None:
    rows = [_row(index) for index in range(4)]
    result = compare_replay_rows(rows)
    assert result["schema"] == "resonith-r203-cross-toolchain-comparison-2"
    assert result["evidence_amendment"] == "R203-EVIDENCE-SPLIT-1"
    assert result["resource_ranges"]["memory_page_event_total"] == {
        "minimum": 1000,
        "maximum": 1003,
    }
    assert len(result["resource_telemetry"]) == 4


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("class_a_semantic_sha256", "e" * 64),
        ("class_a_packed_output_sha256", "f" * 64),
        ("class_b_non_memory_sha256", "1" * 64),
        ("maximum_non_memory_work_units", 575001),
        ("non_memory_event_totals", [99] + list(range(1, 21))),
    ],
)
def test_rejects_semantic_or_non_memory_identity_mismatch(
    field: str,
    replacement: object,
) -> None:
    rows = [_row(index) for index in range(4)]
    rows[2][field] = replacement
    with pytest.raises(
        RuntimeError,
        match="semantic or non-memory replay identity differs",
    ):
        compare_replay_rows(rows)


def test_rejects_locally_invalid_resource_telemetry() -> None:
    rows = [_row(index) for index in range(4)]
    rows[1]["resource_telemetry_locally_valid"] = False
    with pytest.raises(RuntimeError, match="not locally valid"):
        compare_replay_rows(rows)


def test_rejects_invalid_resource_ordering() -> None:
    rows = [_row(index) for index in range(4)]
    rows[3]["maximum_committed_host_bytes"] = (
        rows[3]["maximum_reserved_host_bytes"] + 1
    )
    with pytest.raises(RuntimeError, match="ordering is invalid"):
        compare_replay_rows(rows)


def test_rejects_duplicate_native_binaries() -> None:
    rows = [_row(index) for index in range(4)]
    rows[3]["native_core_sha256"] = rows[2]["native_core_sha256"]
    with pytest.raises(RuntimeError, match="distinct native binaries"):
        compare_replay_rows(rows)


def test_does_not_mutate_replay_rows() -> None:
    rows = [_row(index) for index in range(4)]
    before = copy.deepcopy(rows)
    compare_replay_rows(rows)
    assert rows == before


def test_rejects_unchecked_work_ledger_sum() -> None:
    report = {
        "work_event_counts": [0] * 22,
        "work_units": 1,
    }
    with pytest.raises(RuntimeError, match="does not equal"):
        _non_memory_ledger(report)


def test_class_a_keeps_every_report_header_and_control_field() -> None:
    report = {
        "struct_size": 560,
        "abi_version": 3,
        "termination": 0,
        "solver": 2,
        "flags": 7,
        "reserved": [0] * 7,
        "work_units": 100,
        "work_event_counts": [0] * 22,
        "peak_live_managed_bytes": 10,
        "reserved_host_bytes": 10,
        "committed_host_bytes": 10,
        "peak_live_host_bytes": 10,
        "reserved_device_bytes": 0,
        "committed_device_bytes": 0,
        "peak_live_device_bytes": 0,
    }
    class_a = _report_without_resource_telemetry(report)
    assert class_a == {
        "struct_size": 560,
        "abi_version": 3,
        "termination": 0,
        "solver": 2,
        "flags": 7,
        "reserved": [0] * 7,
    }
