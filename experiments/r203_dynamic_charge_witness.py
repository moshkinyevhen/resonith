"""Run the frozen R-203 bounded-greedy charge-site witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.r197_partial_graph_native_gate import (
    _class_a_evidence,
    _load_case,
    _non_memory_ledger,
    canonical_json_bytes,
)
from reference.maf_p0.partial_graph_fixed import NativePartialGraph


SCHEMA = "resonith-r203-dynamic-charge-greedy-witness-1"
CANDIDATE_CORPUS_SHA256 = (
    "fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reach the bounded-greedy R-203 accounting lane.",
    )
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    arguments = parser.parse_args()

    if sha256_file(arguments.corpus) != CANDIDATE_CORPUS_SHA256:
        raise RuntimeError("bounded-greedy witness corpus hash differs")
    with arguments.corpus.open("rb") as stream:
        line = next(stream)
    _, resolutions, observations, edges, graph, path = _load_case(line)
    greedy_path = copy.copy(path)
    greedy_path.exact_set_candidate_limit = 1

    native = NativePartialGraph(str(arguments.core))
    result = native.paths(
        resolutions,
        observations,
        edges,
        graph,
        greedy_path,
    )
    if (
        result.report["solver"]
        != "deterministic-bounded-disjoint-heuristic"
        or result.report["selected_candidate_count"] <= 1
        or not result.paths
    ):
        raise RuntimeError("bounded-greedy witness did not reach its lane")
    evidence = native.last_path_evidence
    class_a_sha256 = hashlib.sha256(
        canonical_json_bytes(_class_a_evidence(evidence))
    ).hexdigest()
    class_b_sha256 = hashlib.sha256(
        canonical_json_bytes(
            {
                "preflight": _non_memory_ledger(
                    evidence["preflight_report"]
                ),
                "fill": _non_memory_ledger(evidence["fill_report"]),
            }
        )
    ).hexdigest()

    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "solver": result.report["solver"],
                "candidate_count": result.report[
                    "selected_candidate_count"
                ],
                "path_count": len(result.paths),
                "class_a_sha256": class_a_sha256,
                "class_b_sha256": class_b_sha256,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
