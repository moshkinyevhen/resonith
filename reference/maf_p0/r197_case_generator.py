"""Frozen R-197 case generation independent of the native implementation.

This module deliberately imports only the Python arbitrary-precision oracle.
It never loads the Resonith shared library and therefore can be used as an
independent input and expected-semantic authority.
"""

from __future__ import annotations

import ctypes
import hashlib
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .partial_graph_fixed import (
    PATH_V3_ABI_VERSION,
    PartialGraphManifest,
    PartialObservation,
    PartialPathManifestV3,
    PartialResolution,
    build_paths_fixed,
    enumerate_edges_fixed,
    make_manifest,
    make_observation,
    make_path_manifest,
    make_resolution,
    upgrade_path_manifest_v3,
)


GENERATOR_ID = "R197-SPLITMIX64-1"
SCHEMA = "resonith-r197-exact-small-jsonl-1"
MASK64 = (1 << 64) - 1
FROZEN_CONTRACT_SHA256 = (
    "10e24fa8721dfe69c2e1be82f9ffcc83e5dc7b32da0a038d29ec46b943d761bc"
)
EXACT_SAMPLE_RATE = 48_000
EXACT_RESOLUTION = (128, 64)

FREQUENCY_HZ = (0, 110, 220, 440, 1_000, 12_000, 24_000)
FREQUENCY_UNCERTAINTY_Q20 = (0, 1 << 20, 1 << 19, 4 << 20)
PHASE_TURN = (0, 0x40000000, 0x80000000, 0xC0000000)
PHASE_STEP = (0, 0x10000000, 0x20000000, 0xFFFFFFFF)
NORMALIZED_AMPLITUDE_Q16 = (1, 32768, 65536, 0xFFFFFFFF)
AMPLITUDE_UNCERTAINTY_Q16 = (0, 1, 32768)
PHASE_UNCERTAINTY_U31 = (0, 1, 0x40000000, 0x80000000)
DETECTOR_ID = (-1, 0, 1)
BAND_ID = (0, 1, 127)
OWNERSHIP_COMPONENT = (0, 1, 2)
AMBIGUITY_COMPONENT = (0, 1, 0xFFFFFFFF)
FLAGS = (2, 3, 6, 7)
SIGNED_Q8 = (-256, 0, 256)

MANIFEST_FAMILIES = (
    ((1,), 1, (0,), 0, 0),
    ((1, 2), 2, (-1, 0, 1), 1 << 20, 0),
    ((1, 3), 16, (0,), 0, 1 << 20),
    ((1, 2, 4, 8), 4, (-1, 0, 1), 440 << 20, 1 << 20),
)

FINGERPRINT_INITIAL = (
    0xCBF29CE484222325,
    0x84222325CBF29CE4,
    0x9E3779B185EBCA87,
    0xD6E8FEB86659FD93,
)
FINGERPRINT_PRIMES = (
    0x100000001B3,
    0x100000001C9,
    0x100000001E7,
    0x10000000233,
)
INPUT_FINGERPRINT_DOMAIN = b"RPGF\x01\x00\x00\x00"
OUTPUT_FINGERPRINT_DOMAIN = b"RPOF\x01\x00\x00\x00"


@dataclass
class SplitMix64:
    """Normative unsigned SplitMix64 state machine from the frozen contract."""

    state: int

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK64
        value = self.state
        value = (
            (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9
        ) & MASK64
        value = (
            (value ^ (value >> 27)) * 0x94D049BB133111EB
        ) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def choose(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("SplitMix64 bound must be positive")
        return self.next() % bound


def fisher_yates(
    values: Sequence[int],
    generator: SplitMix64,
) -> tuple[int, ...]:
    """Return one frozen Fisher-Yates permutation with exactly n-1 draws."""

    result = list(values)
    for index in range(len(result) - 1, 0, -1):
        other = generator.choose(index + 1)
        result[index], result[other] = result[other], result[index]
    return tuple(result)


def exact_permutations(
    observation_count: int,
    template_family: int,
    manifest_index: int,
) -> tuple[tuple[int, ...], ...]:
    """Return the complete or frozen 64-permutation exact-small campaign."""

    if observation_count < 0 or observation_count > 7:
        raise ValueError("exact-small observation count must be in [0, 7]")
    if not 0 <= template_family < 8:
        raise ValueError("template family must be in [0, 7]")
    if not 0 <= manifest_index < len(MANIFEST_FAMILIES):
        raise ValueError("manifest index must be in [0, 3]")

    identity = tuple(range(observation_count))
    if observation_count <= 5:
        return tuple(itertools.permutations(identity))

    generator = SplitMix64(
        0x6A09E667F3BCC909
        ^ observation_count
        ^ (template_family << 8)
        ^ (manifest_index << 16)
    )
    distinct: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    while len(distinct) < 64:
        permutation = fisher_yates(identity, generator)
        if permutation not in seen:
            seen.add(permutation)
            distinct.append(permutation)
    return tuple(distinct)


def _select(row: Sequence[int], index: int, family: int) -> int:
    return row[(index + family) % len(row)]


def make_exact_observations(
    observation_count: int,
    template_family: int,
) -> tuple[PartialObservation, ...]:
    """Construct one exact-small observation template in canonical ID order."""

    observations: list[PartialObservation] = []
    for index in range(observation_count):
        observation = make_observation(
            observation_id=index,
            frame_index=index,
            resolution_id=0,
            hop_samples=EXACT_RESOLUTION[1],
            frequency_hz_q20=(
                _select(FREQUENCY_HZ, index, template_family) << 20
            ),
            phase_turn_u32=_select(
                PHASE_TURN,
                index,
                template_family,
            ),
            phase_step_u32=_select(
                PHASE_STEP,
                index,
                template_family,
            ),
            normalized_amplitude_q16=_select(
                NORMALIZED_AMPLITUDE_Q16,
                index,
                template_family,
            ),
            ownership_component=_select(
                OWNERSHIP_COMPONENT,
                index,
                template_family,
            ),
            detector_id=_select(DETECTOR_ID, index, template_family),
            frequency_uncertainty_hz_q20=_select(
                FREQUENCY_UNCERTAINTY_Q20,
                index,
                template_family,
            ),
            phase_uncertainty_u31=_select(
                PHASE_UNCERTAINTY_U31,
                index,
                template_family,
            ),
            flags=_select(FLAGS, index, template_family),
            neighbor_priority_q8=_select(
                SIGNED_Q8,
                index,
                template_family,
            ),
            potential_node_value_q8=_select(
                SIGNED_Q8,
                index,
                template_family,
            ),
            uncertainty_leakage_penalty_q8=_select(
                SIGNED_Q8,
                index,
                template_family,
            ),
        )
        observation.amplitude_uncertainty_q16 = _select(
            AMPLITUDE_UNCERTAINTY_Q16,
            index,
            template_family,
        )
        observation.band_id = _select(BAND_ID, index, template_family)
        observation.ambiguity_component = _select(
            AMBIGUITY_COMPONENT,
            index,
            template_family,
        )
        observation.protected_rank_q8 = _select(
            SIGNED_Q8,
            index,
            template_family,
        )
        observations.append(observation)
    return tuple(observations)


def make_exact_manifests(
    observation_count: int,
    manifest_index: int,
) -> tuple[PartialGraphManifest, PartialPathManifestV3]:
    """Construct the frozen policy values without consulting native code."""

    gaps, neighbours, cycles, jump_q20, slope_q20 = MANIFEST_FAMILIES[
        manifest_index
    ]
    graph = make_manifest(
        sample_rate=EXACT_SAMPLE_RATE,
        resolution_count=1,
        gaps=gaps,
        neighbors_per_gap=neighbours,
        cycle_offsets=cycles,
        maximum_frequency_jump_hz_q20=jump_q20,
        maximum_frequency_slope_hz_per_sample_q20=slope_q20,
        maximum_edge_records=4_194_304,
    )
    graph.minimum_track_observations = 2
    graph.continuation_base_bits_q8 = 256
    graph.continuation_reward_q8 = 256
    graph.score_saturation = (1 << 62) - 1
    graph.maximum_path_hypotheses = 1024
    graph.exact_set_candidate_limit = 20

    legacy_path = make_path_manifest(
        protected_band_upper_hz_q20=(),
        minimum_path_observations=2,
        maximum_path_observations=max(2, observation_count),
        k_value_per_state=8,
        k_continuity_per_state=8,
        top_k_value=128,
        top_k_continuity=128,
        top_k_protected=128,
        protected_paths_per_band=2,
        exact_set_candidate_limit=20,
        maximum_path_records=65_536,
        maximum_total_entries=4_194_304,
        maximum_frontier_states=1_048_576,
        maximum_state_records=4_194_304,
        maximum_work_units=(1 << 48) - 1,
        maximum_managed_bytes=8 << 30,
    )
    return graph, upgrade_path_manifest_v3(
        legacy_path,
        maximum_device_bytes=0,
    )


def _ctypes_value(value: object) -> object:
    if isinstance(value, ctypes.Array):
        return [_ctypes_value(item) for item in value]
    if isinstance(value, ctypes.Structure):
        return {
            name: _ctypes_value(getattr(value, name))
            for name, *_ in value._fields_
        }
    return value


@dataclass
class FingerprintV1:
    """Independent four-lane field serializer and hash accumulator."""

    lanes: list[int]
    byte_count: int = 0

    @classmethod
    def begin(cls) -> "FingerprintV1":
        return cls(list(FINGERPRINT_INITIAL))

    def raw(self, data: bytes) -> None:
        for byte in data:
            for lane, prime in enumerate(FINGERPRINT_PRIMES):
                mixed = byte + 53 * lane
                self.lanes[lane] = (
                    (self.lanes[lane] ^ (mixed & 0xFF)) * prime
                ) & MASK64
            self.byte_count += 1

    def integer(self, value: int, width: int, signed: bool = False) -> None:
        self.raw(int(value).to_bytes(width, "little", signed=signed))

    def result(self) -> tuple[int, int, int, int]:
        return tuple(self.lanes)  # type: ignore[return-value]


def _is_signed_scalar(field_type: type[ctypes._SimpleCData]) -> bool:
    return field_type(-1).value == -1


def _fingerprint_ctypes_value(
    fingerprint: FingerprintV1,
    value: object,
    field_type: object,
    *,
    zero: bool = False,
) -> None:
    if isinstance(field_type, type) and issubclass(field_type, ctypes.Array):
        element_type = field_type._type_
        for index in range(field_type._length_):
            element = 0 if zero else value[index]
            _fingerprint_ctypes_value(
                fingerprint,
                element,
                element_type,
                zero=zero,
            )
        return
    width = ctypes.sizeof(field_type)
    integer = 0 if zero else int(value)
    fingerprint.integer(
        integer,
        width,
        signed=_is_signed_scalar(field_type),
    )


def _fingerprint_ctypes_struct(
    fingerprint: FingerprintV1,
    value: ctypes.Structure,
    *,
    zero_fields: frozenset[str] = frozenset(),
) -> None:
    for name, field_type, *_ in value._fields_:
        _fingerprint_ctypes_value(
            fingerprint,
            getattr(value, name),
            field_type,
            zero=name in zero_fields,
        )


def input_fingerprint_v1(
    resolutions: Sequence[PartialResolution],
    observations: Sequence[PartialObservation],
    edges: Sequence[object],
    graph_manifest: PartialGraphManifest,
    path_manifest: PartialPathManifestV3,
) -> tuple[tuple[int, int, int, int], int]:
    """Compute the frozen input identity without C object-byte hashing."""

    canonical_resolutions = sorted(
        resolutions,
        key=lambda item: item.resolution_id,
    )
    canonical_observations = sorted(
        observations,
        key=lambda item: (
            item.center_sample,
            item.resolution_id,
            item.detector_id,
            item.frequency_hz_q20,
            item.observation_id,
        ),
    )
    canonical_edges = sorted(edges, key=lambda item: item.candidate_id)

    fingerprint = FingerprintV1.begin()
    fingerprint.raw(INPUT_FINGERPRINT_DOMAIN)
    fingerprint.integer(path_manifest.work_ledger_version, 4)
    fingerprint.integer(len(canonical_resolutions), 8)
    fingerprint.integer(len(canonical_observations), 8)
    fingerprint.integer(len(canonical_edges), 8)
    _fingerprint_ctypes_struct(fingerprint, graph_manifest)
    _fingerprint_ctypes_struct(
        fingerprint,
        path_manifest,
        zero_fields=frozenset({"expected_input_fingerprint"}),
    )
    for resolution in canonical_resolutions:
        _fingerprint_ctypes_struct(fingerprint, resolution)
    for observation in canonical_observations:
        _fingerprint_ctypes_struct(fingerprint, observation)
    for edge in canonical_edges:
        fingerprint.integer(80, 4)
        fingerprint.integer(1, 4)
        fingerprint.integer(edge.candidate_id, 8)
        fingerprint.integer(edge.source_observation_id, 8)
        fingerprint.integer(edge.target_observation_id, 8)
        fingerprint.integer(edge.center_delta_samples, 8)
        fingerprint.integer(edge.frequency_delta_hz_q20, 8, signed=True)
        fingerprint.integer(edge.gap_hops, 4)
        fingerprint.integer(edge.cycle_offset, 4, signed=True)
        fingerprint.integer(edge.phase_error_u31, 4)
        fingerprint.integer(edge.continuity_cost_q8, 4, signed=True)
        fingerprint.integer(
            edge.provisional_program_cost_q8,
            4,
            signed=True,
        )
        fingerprint.integer(edge.flags, 4)
        fingerprint.integer(0, 4)
        fingerprint.integer(0, 4)
    return fingerprint.result(), fingerprint.byte_count


def output_fingerprint_v1(
    result: object,
) -> tuple[tuple[int, int, int, int], int]:
    """Serialize oracle paths and entries as packed ABI-v3 logical fields."""

    fingerprint = FingerprintV1.begin()
    fingerprint.raw(OUTPUT_FINGERPRINT_DOMAIN)
    entry_count = sum(len(path.entries) for path in result.paths)
    fingerprint.integer(len(result.paths), 8)
    fingerprint.integer(entry_count, 8)

    entry_offset = 0
    for path in result.paths:
        fingerprint.integer(136, 4)
        fingerprint.integer(PATH_V3_ABI_VERSION, 4)
        fingerprint.integer(path.path_id, 8)
        fingerprint.integer(entry_offset, 8)
        fingerprint.integer(len(path.entries), 4)
        fingerprint.integer(path.family_flags, 4)
        fingerprint.integer(path.terminal_observation_id, 8)
        fingerprint.integer(path.continuity_score_q8, 8, signed=True)
        fingerprint.integer(path.potential_node_value_q8, 8, signed=True)
        fingerprint.integer(
            path.uncertainty_leakage_penalty_q8,
            8,
            signed=True,
        )
        fingerprint.integer(
            path.provisional_program_cost_q8,
            8,
            signed=True,
        )
        fingerprint.integer(path.selection_score_q8, 8, signed=True)
        fingerprint.integer(path.phase_error_sum_u64, 8)
        fingerprint.integer(path.phase_error_count, 4)
        fingerprint.integer(path.ownership_conflict_count, 4)
        fingerprint.integer(path.protected_band_id, 4)
        fingerprint.integer(path.value_rank, 4)
        fingerprint.integer(path.continuity_rank, 4)
        fingerprint.integer(path.protected_rank, 4)
        fingerprint.integer(path.flags, 4)
        for _ in range(5):
            fingerprint.integer(0, 4)
        entry_offset += len(path.entries)

    for path in result.paths:
        for entry in path.entries:
            fingerprint.integer(48, 4)
            fingerprint.integer(PATH_V3_ABI_VERSION, 4)
            fingerprint.integer(entry.observation_id, 8)
            fingerprint.integer(entry.incoming_edge_candidate_id, 8)
            fingerprint.integer(entry.ownership_component, 4)
            fingerprint.integer(
                entry.second_order_cost_q8,
                4,
                signed=True,
            )
            fingerprint.integer(entry.flags, 4)
            for _ in range(3):
                fingerprint.integer(0, 4)
    return fingerprint.result(), fingerprint.byte_count


def _path_semantics(
    result: object,
    input_fingerprint: tuple[int, int, int, int],
    input_fingerprint_bytes: int,
) -> dict[str, object]:
    output_fingerprint, output_fingerprint_bytes = output_fingerprint_v1(
        result
    )
    return {
        "paths": [asdict(path) for path in result.paths],
        "selected_path_ids": list(result.selected_path_ids),
        "algorithm_report": result.report,
        "input_fingerprint": list(input_fingerprint),
        "output_fingerprint": list(output_fingerprint),
        "preflight_fingerprint_event_count": (
            input_fingerprint_bytes + output_fingerprint_bytes
        ),
        "fill_fingerprint_event_count": (
            input_fingerprint_bytes + 3 * output_fingerprint_bytes
        ),
    }


def exact_small_cases() -> Iterator[dict[str, object]]:
    """Yield all 9,024 valid exact-small presentation cases."""

    resolution = make_resolution(0, *EXACT_RESOLUTION)
    case_index = 0
    for observation_count in range(8):
        for template_family in range(8):
            canonical_observations = make_exact_observations(
                observation_count,
                template_family,
            )
            for manifest_index in range(len(MANIFEST_FAMILIES)):
                graph_manifest, path_manifest = make_exact_manifests(
                    observation_count,
                    manifest_index,
                )
                edges = enumerate_edges_fixed(
                    (resolution,),
                    canonical_observations,
                    graph_manifest,
                )
                oracle = build_paths_fixed(
                    canonical_observations,
                    edges,
                    graph_manifest,
                    path_manifest,
                )
                input_fingerprint, input_fingerprint_bytes = (
                    input_fingerprint_v1(
                        (resolution,),
                        canonical_observations,
                        edges,
                        graph_manifest,
                        path_manifest,
                    )
                )
                for permutation in exact_permutations(
                    observation_count,
                    template_family,
                    manifest_index,
                ):
                    presented = tuple(
                        canonical_observations[index]
                        for index in permutation
                    )
                    yield {
                        "schema": SCHEMA,
                        "generator_id": GENERATOR_ID,
                        "contract_sha256": FROZEN_CONTRACT_SHA256,
                        "campaign": "exact-small-valid",
                        "case_index": case_index,
                        "observation_count": observation_count,
                        "template_family": template_family,
                        "manifest_index": manifest_index,
                        "observation_permutation": list(permutation),
                        "expected_first_status": "OK",
                        "resolutions": [_ctypes_value(resolution)],
                        "observations": [
                            _ctypes_value(item) for item in presented
                        ],
                        "canonical_edges": [
                            asdict(item) for item in edges
                        ],
                        "graph_manifest": _ctypes_value(graph_manifest),
                        "path_manifest": _ctypes_value(path_manifest),
                        "expected": _path_semantics(
                            oracle,
                            input_fingerprint,
                            input_fingerprint_bytes,
                        ),
                    }
                    case_index += 1


def canonical_json_bytes(value: object) -> bytes:
    """Encode one evidence record with one cross-platform JSON law."""

    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def emit_jsonl(
    destination: Path,
    cases: Iterable[dict[str, object]],
) -> dict[str, object]:
    """Atomically emit a deterministic JSONL corpus and its inventory."""

    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    digest = hashlib.sha256()
    byte_count = 0
    case_count = 0
    with temporary.open("wb") as stream:
        for case in cases:
            line = canonical_json_bytes(case) + b"\n"
            stream.write(line)
            digest.update(line)
            byte_count += len(line)
            case_count += 1
        stream.flush()
    temporary.replace(destination)
    return {
        "schema": "resonith-r197-jsonl-inventory-1",
        "generator_id": GENERATOR_ID,
        "path": destination.as_posix(),
        "case_count": case_count,
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
    }


def verify_contract(path: Path) -> str:
    """Fail closed when the frozen written contract was edited."""

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != FROZEN_CONTRACT_SHA256:
        raise RuntimeError(
            "R-197 case contract hash mismatch: "
            f"expected {FROZEN_CONTRACT_SHA256}, got {digest}"
        )
    return digest
