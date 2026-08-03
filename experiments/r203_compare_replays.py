"""Fail-closed comparison of R-203 replay artifacts across toolchains."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IDENTITY_FIELDS = (
    "case_count",
    "ordinary_class_ab_case_count",
    "consumed_corpus_sha256",
    "total_path_records",
    "total_entry_records",
    "maximum_non_memory_work_units",
    "non_memory_event_totals",
    "class_a_semantic_sha256",
    "class_a_packed_output_sha256",
    "class_b_non_memory_sha256",
    "twice_replayed",
)
TELEMETRY_FIELDS = (
    "memory_page_event_total",
    "maximum_work_units",
    "maximum_reserved_host_bytes",
    "maximum_committed_host_bytes",
    "maximum_peak_live_host_bytes",
    "resource_telemetry_sha256",
)


def compare_replay_rows(
    rows: list[dict[str, object]],
    *,
    minimum_replays: int = 4,
    minimum_binaries: int = 4,
) -> dict[str, object]:
    if len(rows) < minimum_replays:
        raise RuntimeError(
            f"at least {minimum_replays} independent replays are required"
        )
    for row in rows:
        if row.get("schema") != "resonith-r203-native-jsonl-replay-2":
            raise RuntimeError("replay schema does not implement evidence split")
        if not row.get("resource_telemetry_locally_valid"):
            raise RuntimeError("replay resource telemetry is not locally valid")
        if row.get("twice_replayed") is not True:
            raise RuntimeError("replay was not executed twice")
        if len(row["non_memory_event_totals"]) != 21:
            raise RuntimeError("non-memory event vector must contain 21 counts")
        if (
            any(int(value) < 0 for value in row["non_memory_event_totals"])
            or int(row["maximum_non_memory_work_units"]) < 0
            or int(row["memory_page_event_total"]) < 0
            or int(row["maximum_non_memory_work_units"])
            > int(row["maximum_work_units"])
        ):
            raise RuntimeError("replay work evidence is invalid")
        if (
            row["maximum_reserved_host_bytes"]
            < row["maximum_committed_host_bytes"]
            or row["maximum_committed_host_bytes"]
            < row["maximum_peak_live_host_bytes"]
        ):
            raise RuntimeError("replay resource ordering is invalid")

    expected = {name: rows[0][name] for name in IDENTITY_FIELDS}
    for row in rows:
        actual = {name: row[name] for name in IDENTITY_FIELDS}
        if actual != expected:
            raise RuntimeError("semantic or non-memory replay identity differs")
    native_hashes = {str(row["native_core_sha256"]) for row in rows}
    if len(native_hashes) < minimum_binaries:
        raise RuntimeError(
            f"replays do not bind {minimum_binaries} distinct native binaries"
        )

    telemetry = [
        {
            "native_core_sha256": row["native_core_sha256"],
            **{name: row[name] for name in TELEMETRY_FIELDS},
        }
        for row in rows
    ]
    result = {
        "schema": "resonith-r203-cross-toolchain-comparison-2",
        "evidence_amendment": "R203-EVIDENCE-SPLIT-1",
        "replay_count": len(rows),
        "identity_fields": list(IDENTITY_FIELDS),
        "shared": expected,
        "native_core_sha256": sorted(native_hashes),
        "resource_telemetry": telemetry,
        "resource_ranges": {
            name: {
                "minimum": min(int(row[name]) for row in rows),
                "maximum": max(int(row[name]) for row in rows),
            }
            for name in TELEMETRY_FIELDS
            if name != "resource_telemetry_sha256"
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare complete R-203 replay results.",
    )
    parser.add_argument("replays", type=Path, nargs="+")
    arguments = parser.parse_args()
    rows = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in arguments.replays
    ]
    result = compare_replay_rows(rows)
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
