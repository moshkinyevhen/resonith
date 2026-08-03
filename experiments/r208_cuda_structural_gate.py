"""Run the finite R-208 CPU/CUDA structural parity gate.

This is an evidence harness, not a codec or decoder dependency. It deliberately
batches independent frozen cases before CUDA so NVRTC compilation cost does not
become a false coverage metric.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from reference.maf_p0.partial_graph_fixed import (
    ABI_VERSION,
    EdgeRecord,
    NativePartialGraph,
    PartialEdge,
    PartialGraphManifest,
    PartialObservation,
    PartialResolution,
)


ROOT = Path(__file__).resolve().parents[1]
THREADS = (1, 31, 32, 255, 256, 1024)
OK = 0
INVALID_ARGUMENT = 1
OUTPUT_TOO_SMALL = 2


class FoundryEvidence(ctypes.Structure):
    _fields_ = [
        ("nvrtc_major", ctypes.c_uint32),
        ("nvrtc_minor", ctypes.c_uint32),
        ("compute_major", ctypes.c_uint32),
        ("compute_minor", ctypes.c_uint32),
        ("device_memory_bytes", ctypes.c_uint64),
        ("input_bytes", ctypes.c_uint64),
        ("output_bytes", ctypes.c_uint64),
        ("first_candidate", ctypes.c_uint64),
        ("candidate_count", ctypes.c_uint64),
        ("device_name", ctypes.c_char * 128),
    ]


def struct_from_dict(struct_type, values):
    result = struct_type()
    for name, field_type, *_ in struct_type._fields_:
        value = values[name]
        if isinstance(field_type, type) and issubclass(field_type, ctypes.Array):
            target = getattr(result, name)
            for index, item in enumerate(value):
                target[index] = item
        else:
            setattr(result, name, value)
    return result


def native_edge(record: EdgeRecord) -> PartialEdge:
    result = PartialEdge()
    result.struct_size = ctypes.sizeof(result)
    result.abi_version = ABI_VERSION
    for name, value in asdict(record).items():
        setattr(result, name, value)
    return result


def edge_without_id(record: EdgeRecord) -> tuple[int, ...]:
    return (
        record.source_observation_id,
        record.target_observation_id,
        record.center_delta_samples,
        record.frequency_delta_hz_q20,
        record.gap_hops,
        record.cycle_offset,
        record.phase_error_u31,
        record.continuity_cost_q8,
        record.provisional_program_cost_q8,
        record.flags,
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_bytes(value) -> bytes:
    return ctypes.string_at(ctypes.addressof(value), ctypes.sizeof(value))


class FoundryPartialCuda:
    def __init__(self, library: Path, nvrtc_directory: Path):
        self.nvrtc_directory = str(nvrtc_directory).encode("utf-8")
        dll = ctypes.CDLL(str(library))
        self.function = dll.resonith_foundry_partial_edge_cuda
        self.function.argtypes = [
            ctypes.POINTER(PartialObservation),
            ctypes.c_size_t,
            ctypes.POINTER(PartialEdge),
            ctypes.c_size_t,
            ctypes.POINTER(PartialGraphManifest),
            ctypes.POINTER(PartialEdge),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.c_char_p,
            ctypes.POINTER(FoundryEvidence),
            ctypes.POINTER(ctypes.c_char),
            ctypes.c_size_t,
        ]
        self.function.restype = ctypes.c_int

    def run(
        self,
        observations: tuple[PartialObservation, ...],
        edges: tuple[EdgeRecord, ...],
        manifest: PartialGraphManifest,
        threads: int,
        *,
        output_capacity: int | None = None,
        reverse_candidates: bool = False,
        corrupt_first_observation: bool = False,
    ) -> dict[str, object]:
        observation_array = (PartialObservation * max(1, len(observations)))()
        for index, value in enumerate(observations):
            observation_array[index] = value
        if corrupt_first_observation and observations:
            observation_array[0].struct_size = 0

        ordered = tuple(native_edge(edge) for edge in edges)
        if reverse_candidates:
            ordered = tuple(reversed(ordered))
        candidate_array = (PartialEdge * max(1, len(ordered)))()
        for index, value in enumerate(ordered):
            candidate_array[index] = value

        capacity = len(edges) if output_capacity is None else output_capacity
        output_array = (PartialEdge * max(1, len(edges)))()
        ctypes.memset(ctypes.addressof(output_array), 0xA5, ctypes.sizeof(output_array))
        output_before = array_bytes(output_array)
        evidence = FoundryEvidence()
        ctypes.memset(ctypes.addressof(evidence), 0x5A, ctypes.sizeof(evidence))
        evidence_before = bytes(evidence)
        error = ctypes.create_string_buffer(4096)
        ctypes.memset(ctypes.addressof(error), 0xCC, ctypes.sizeof(error))

        status = self.function(
            observation_array,
            len(observations),
            candidate_array,
            len(edges),
            ctypes.byref(manifest),
            output_array,
            capacity,
            threads,
            self.nvrtc_directory,
            ctypes.byref(evidence),
            error,
            len(error),
        )
        output_after = array_bytes(output_array)
        evidence_after = bytes(evidence)
        return {
            "status": status,
            "output": output_after[: len(edges) * ctypes.sizeof(PartialEdge)],
            "output_unchanged": output_after == output_before,
            "evidence": evidence_after,
            "evidence_unchanged": evidence_after == evidence_before,
            "error": error.value.decode("utf-8", errors="replace"),
        }


def load_and_verify(arguments) -> tuple[dict, list[dict]]:
    inventory = json.loads(arguments.inventory.read_text(encoding="utf-8"))
    corpus_bytes = arguments.corpus.read_bytes()
    if (
        len(corpus_bytes) != inventory["bytes"]
        or sha256_bytes(corpus_bytes) != inventory["sha256"]
        or inventory["case_count"] != 288
    ):
        raise RuntimeError("candidate-rich corpus identity differs")
    cases = [json.loads(line) for line in corpus_bytes.splitlines()]
    if len(cases) != 288:
        raise RuntimeError("candidate-rich case cardinality differs")
    return inventory, cases


def load_case(case: dict):
    resolutions = tuple(
        struct_from_dict(PartialResolution, item) for item in case["resolutions"]
    )
    observations = tuple(
        struct_from_dict(PartialObservation, item)
        for item in case["observations"]
    )
    manifest = struct_from_dict(PartialGraphManifest, case["graph_manifest"])
    frozen = tuple(EdgeRecord(**item) for item in case["canonical_edges"])
    return resolutions, observations, manifest, frozen


def group_key(case: dict) -> str:
    return json.dumps(
        {
            "resolutions": case["resolutions"],
            "graph_manifest": case["graph_manifest"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def aggregate_group(native: NativePartialGraph, members: list[dict]):
    resolutions, _, manifest, _ = load_case(members[0])
    observations: list[PartialObservation] = []
    owner_by_id: dict[int, tuple[int, int]] = {}
    frozen_by_case: dict[int, tuple[EdgeRecord, ...]] = {}

    for case in members:
        case_index = case["case_index"]
        _, original, _, frozen = load_case(case)
        frozen_by_case[case_index] = frozen
        observation_offset = (case_index + 1) * 1_000_000
        detector_offset = (case_index + 1) * 1_000
        for source in original:
            value = PartialObservation.from_buffer_copy(bytes(source))
            original_id = int(value.observation_id)
            value.observation_id = observation_offset + original_id
            value.detector_id = detector_offset + value.detector_id
            owner_by_id[int(value.observation_id)] = (case_index, original_id)
            observations.append(value)

    manifest.maximum_edge_records = sum(
        len(edges) for edges in frozen_by_case.values()
    )
    aggregate = native.edges(resolutions, tuple(observations), manifest)
    projected: dict[int, list[EdgeRecord]] = defaultdict(list)
    for edge in aggregate:
        source_owner = owner_by_id[edge.source_observation_id]
        target_owner = owner_by_id[edge.target_observation_id]
        if source_owner[0] != target_owner[0]:
            raise RuntimeError("aggregate produced a cross-case edge")
        projected[source_owner[0]].append(
            EdgeRecord(
                candidate_id=len(projected[source_owner[0]]),
                source_observation_id=source_owner[1],
                target_observation_id=target_owner[1],
                center_delta_samples=edge.center_delta_samples,
                frequency_delta_hz_q20=edge.frequency_delta_hz_q20,
                gap_hops=edge.gap_hops,
                cycle_offset=edge.cycle_offset,
                phase_error_u31=edge.phase_error_u31,
                continuity_cost_q8=edge.continuity_cost_q8,
                provisional_program_cost_q8=edge.provisional_program_cost_q8,
                flags=edge.flags,
            )
        )
    for case_index, frozen in frozen_by_case.items():
        actual = tuple(projected[case_index])
        if tuple(map(edge_without_id, actual)) != tuple(map(edge_without_id, frozen)):
            raise RuntimeError(f"aggregate projection differs for case {case_index}")
    return tuple(observations), manifest, aggregate


def boundary_graph(native: NativePartialGraph, template: dict, count: int):
    resolutions, template_observations, manifest, _ = load_case(template)
    if count <= 0:
        raise ValueError("positive boundary count required")
    resolution = PartialResolution.from_buffer_copy(bytes(resolutions[0]))
    resolution.resolution_id = 777
    resolution.hop_samples = 64
    resolution.fft_samples = 256

    manifest.resolution_count = 1
    manifest.gap_count = 1
    manifest.neighbors_per_gap = 16
    manifest.cycle_offset_count = 1
    manifest.maximum_edge_records = count
    manifest.gaps[0] = 1
    manifest.cycle_offsets[0] = 0
    for index in range(1, len(manifest.gaps)):
        manifest.gaps[index] = 0
    for index in range(1, len(manifest.cycle_offsets)):
        manifest.cycle_offsets[index] = 0

    base = template_observations[0]
    observations: list[PartialObservation] = []
    next_id = 1

    def add(center: int, detector: int) -> None:
        nonlocal next_id
        value = PartialObservation.from_buffer_copy(bytes(base))
        value.observation_id = next_id
        next_id += 1
        value.center_sample = center
        value.frame_index = 0 if center == 0 else 1
        value.resolution_id = resolution.resolution_id
        value.detector_id = detector
        value.frequency_hz_q20 = 440 << 20
        value.frequency_uncertainty_hz_q20 = 1 << 20
        value.reserved[:] = (0,) * len(value.reserved)
        observations.append(value)

    quotient, remainder = divmod(count, 16)
    for _ in range(quotient):
        add(0, 0)
    for _ in range(16 if quotient else 0):
        add(resolution.hop_samples, 0)
    if remainder:
        add(0, 1)
        for _ in range(remainder):
            add(resolution.hop_samples, 1)

    edges = native.edges((resolution,), tuple(observations), manifest)
    if len(edges) != count:
        raise RuntimeError(f"boundary graph requested {count}, produced {len(edges)}")
    return tuple(observations), manifest, edges


def require_failure(result: dict, status: int, label: str) -> None:
    if (
        result["status"] != status
        or not result["output_unchanged"]
        or not result["evidence_unchanged"]
    ):
        raise RuntimeError(f"{label}: failure status/mutation law differs")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--foundry-cuda", type=Path, required=True)
    parser.add_argument("--nvrtc-directory", type=Path, required=True)
    arguments = parser.parse_args()
    inventory, cases = load_and_verify(arguments)
    native = NativePartialGraph(arguments.native_core)
    foundry = FoundryPartialCuda(arguments.foundry_cuda, arguments.nvrtc_directory)
    started = time.perf_counter()

    cpu_digest = hashlib.sha256()
    zero_cases = 0
    nonzero_cases = 0
    for case in cases:
        resolutions, observations, manifest, frozen = load_case(case)
        first = native.edges(resolutions, observations, manifest)
        second = native.edges(resolutions, observations, manifest)
        if first != frozen or second != frozen:
            raise RuntimeError(f"case {case['case_index']}: CPU/frozen union differs")
        cpu_digest.update(json.dumps([asdict(edge) for edge in first], sort_keys=True).encode())
        if frozen:
            nonzero_cases += 1
        else:
            zero_cases += 1
            for threads in THREADS:
                for pass_index in range(2):
                    result = foundry.run(observations, frozen, manifest, threads)
                    require_failure(
                        result,
                        INVALID_ARGUMENT,
                        f"zero case {case['case_index']}/{threads}/{pass_index}",
                    )

    if (nonzero_cases, zero_cases) != (252, 36):
        raise RuntimeError("candidate-rich nonzero/zero partition differs")

    groups: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        if case["canonical_edges"]:
            groups[group_key(case)].append(case)
    aggregate_hashes: dict[str, dict[str, str | int]] = {}
    for group_index, members in enumerate(groups.values()):
        observations, manifest, edges = aggregate_group(native, members)
        expected = array_bytes(
            (PartialEdge * len(edges))(*(native_edge(edge) for edge in edges))
        )
        group_hashes: list[str] = []
        for threads in THREADS:
            pass_hashes = []
            for _ in range(2):
                result = foundry.run(observations, edges, manifest, threads)
                if result["status"] != OK or result["output"] != expected:
                    raise RuntimeError(f"aggregate group {group_index}/{threads} differs")
                pass_hashes.append(sha256_bytes(result["output"] + result["evidence"]))
            if pass_hashes[0] != pass_hashes[1]:
                raise RuntimeError("aggregate CUDA replay is not stable")
            group_hashes.append(pass_hashes[0])
        aggregate_hashes[str(group_index)] = {
            "cases": len(members),
            "edges": len(edges),
            "sha256": sha256_bytes("".join(group_hashes).encode()),
        }

    boundary_hashes: dict[str, str] = {}
    boundary_cache: dict[int, tuple] = {}
    for threads in THREADS:
        counts = {
            value
            for value in (
                threads - 1,
                threads,
                threads + 1,
                2 * threads - 1,
                2 * threads,
                2 * threads + 1,
            )
            if 0 < value <= 2049
        }
        for count in sorted(counts):
            if count not in boundary_cache:
                boundary_cache[count] = boundary_graph(native, cases[0], count)
            observations, manifest, edges = boundary_cache[count]
            expected = array_bytes(
                (PartialEdge * len(edges))(*(native_edge(edge) for edge in edges))
            )
            hashes = []
            for _ in range(2):
                result = foundry.run(observations, edges, manifest, threads)
                if result["status"] != OK or result["output"] != expected:
                    raise RuntimeError(f"boundary {threads}/{count} differs")
                hashes.append(sha256_bytes(result["output"] + result["evidence"]))
            if hashes[0] != hashes[1]:
                raise RuntimeError(f"boundary {threads}/{count} is not stable")
            boundary_hashes[f"{threads}:{count}"] = hashes[0]

    observations, manifest, edges = boundary_cache[31]
    require_failure(foundry.run(observations, edges, manifest, 0), INVALID_ARGUMENT, "threads=0")
    require_failure(foundry.run(observations, edges, manifest, 1025), INVALID_ARGUMENT, "threads=1025")
    require_failure(
        foundry.run(observations, edges, manifest, 0, output_capacity=0),
        OUTPUT_TOO_SMALL,
        "capacity precedence",
    )
    require_failure(
        foundry.run(observations, edges, manifest, 32, corrupt_first_observation=True),
        INVALID_ARGUMENT,
        "malformed observation",
    )
    permuted = foundry.run(
        observations,
        edges,
        manifest,
        32,
        reverse_candidates=True,
    )
    expected = array_bytes(
        (PartialEdge * len(edges))(*(native_edge(edge) for edge in edges))
    )
    if permuted["status"] != OK or permuted["output"] != expected:
        raise RuntimeError("valid candidate-array permutation changed output")

    result = {
        "schema": "resonith-r208-cuda-structural-gate-1",
        "status": "PASS",
        "corpus_sha256": inventory["sha256"],
        "cpu_cases_twice": 288,
        "nonzero_cuda_cases": 252,
        "zero_invalid_argument_cases": 36,
        "cuda_thread_values": list(THREADS),
        "aggregate_groups": aggregate_hashes,
        "boundary_pair_count": len(boundary_hashes),
        "boundary_hash_sha256": sha256_bytes(
            json.dumps(boundary_hashes, sort_keys=True).encode()
        ),
        "cpu_union_sha256": cpu_digest.hexdigest(),
        "negative_profiles": [
            "zero-candidate",
            "threads-0",
            "threads-1025",
            "output-capacity-precedence",
            "malformed-observation",
            "valid-candidate-array-permutation",
        ],
        "status_reachability": {
            "OK": "direct",
            "INVALID_ARGUMENT": "direct",
            "OUTPUT_TOO_SMALL": "direct",
            "BACKEND_UNAVAILABLE": "environment-dependent",
            "COMPILATION_FAILED": "fault-injection-only",
            "DEVICE_FAILED": "fault-injection-only",
            "RANGE_OVERFLOW": "safely-unreachable in this structural gate",
        },
        "elapsed_seconds": time.perf_counter() - started,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
