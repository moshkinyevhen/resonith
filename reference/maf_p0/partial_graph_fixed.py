"""Independent Python oracle for the fixed-point R-190 native edge graph."""

from __future__ import annotations

import ctypes
import hashlib
from dataclasses import dataclass
from pathlib import Path


ABI_VERSION = 1
MAX_GAPS = 8
MAX_CYCLE_OFFSETS = 9
PHASE_USABLE = 1
LOCALLY_RESOLVABLE = 2
PROTECTED_WEAK = 4
AMBIGUITY_NONE = 0xFFFFFFFF
_U32_MASK = 0xFFFFFFFF
_I32_MAX = (1 << 31) - 1
_I32_MIN = -(1 << 31)
_U64_MAX = (1 << 64) - 1


class PartialResolution(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("resolution_id", ctypes.c_uint32),
        ("fft_samples", ctypes.c_uint32),
        ("hop_samples", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 3),
    ]


class PartialGraphManifest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("sample_rate", ctypes.c_uint32),
        ("resolution_count", ctypes.c_uint32),
        ("gap_count", ctypes.c_uint32),
        ("neighbors_per_gap", ctypes.c_uint32),
        ("cycle_offset_count", ctypes.c_uint32),
        ("minimum_track_observations", ctypes.c_uint32),
        ("maximum_frequency_jump_hz_q20", ctypes.c_int64),
        ("maximum_frequency_slope_hz_per_sample_q20", ctypes.c_int64),
        ("continuation_base_bits_q8", ctypes.c_int32),
        ("continuation_reward_q8", ctypes.c_int32),
        ("score_saturation", ctypes.c_int64),
        ("maximum_edge_records", ctypes.c_uint64),
        ("maximum_path_hypotheses", ctypes.c_uint32),
        ("exact_set_candidate_limit", ctypes.c_uint32),
        ("gaps", ctypes.c_uint32 * MAX_GAPS),
        ("cycle_offsets", ctypes.c_int32 * MAX_CYCLE_OFFSETS),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class PartialObservation(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("observation_id", ctypes.c_uint64),
        ("center_sample", ctypes.c_uint64),
        ("frequency_hz_q20", ctypes.c_int64),
        ("frequency_uncertainty_hz_q20", ctypes.c_uint64),
        ("phase_turn_u32", ctypes.c_uint32),
        ("phase_step_u32", ctypes.c_uint32),
        ("normalized_amplitude_q16", ctypes.c_uint32),
        ("amplitude_uncertainty_q16", ctypes.c_uint32),
        ("phase_uncertainty_u31", ctypes.c_uint32),
        ("frame_index", ctypes.c_uint32),
        ("resolution_id", ctypes.c_uint32),
        ("detector_id", ctypes.c_int32),
        ("band_id", ctypes.c_uint32),
        ("ownership_component", ctypes.c_uint32),
        ("ambiguity_component", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("protected_rank_q8", ctypes.c_int32),
        ("neighbor_priority_q8", ctypes.c_int32),
        ("potential_node_value_q8", ctypes.c_int32),
        ("uncertainty_leakage_penalty_q8", ctypes.c_int32),
        ("reserved", ctypes.c_uint32 * 6),
    ]


class PartialEdge(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("candidate_id", ctypes.c_uint64),
        ("source_observation_id", ctypes.c_uint64),
        ("target_observation_id", ctypes.c_uint64),
        ("center_delta_samples", ctypes.c_uint64),
        ("frequency_delta_hz_q20", ctypes.c_int64),
        ("gap_hops", ctypes.c_uint32),
        ("cycle_offset", ctypes.c_int32),
        ("phase_error_u31", ctypes.c_uint32),
        ("continuity_cost_q8", ctypes.c_int32),
        ("provisional_program_cost_q8", ctypes.c_int32),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 2),
    ]


PATH_ABI_VERSION = 2
PATH_V3_ABI_VERSION = 3
PATH_WORK_LEDGER_VERSION = 1
PATH_V3_WORK_EVENT_COUNT = 22
PATH_WORK_EVENT_NAMES = (
    "VALIDATE_RECORD",
    "SNAPSHOT_BYTE",
    "RADIX_BUCKET",
    "RADIX_CLASSIFY",
    "RADIX_SCATTER",
    "MERGE_COMPARE",
    "MERGE_MOVE",
    "GRAPH_SOURCE",
    "GRAPH_GAP",
    "GRAPH_TARGET",
    "GRAPH_CYCLE",
    "EDGE_FIELD",
    "LOOKUP",
    "STATE",
    "REFERENCE",
    "SELECT",
    "RECONSTRUCT",
    "MEMORY_PAGE",
    "STAGE_RECORD",
    "COMMIT_RECORD",
    "FINGERPRINT_BYTE",
    "CUDA_ITEM",
)
MAX_PROTECTED_BANDS = 128
PATH_FAMILY_LOCAL_POTENTIAL = 1
PATH_FAMILY_CONTINUITY = 2
PATH_FAMILY_PROTECTED_WEAK = 4
PATH_FLAG_SELECTED = 1
PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT = 2
PATH_FLAG_PHASE_EVIDENCE = 4
PATH_ENTRY_BIRTH_EDGE = _U64_MAX
PATH_RANK_ABSENT = _U32_MASK


class PartialPathManifest(ctypes.Structure):
    """Packed R-191 frontier policy; never serialized into Resonith."""

    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("second_order_law_version", ctypes.c_uint32),
        ("protected_band_count", ctypes.c_uint32),
        ("k_value_per_state", ctypes.c_uint32),
        ("k_continuity_per_state", ctypes.c_uint32),
        ("top_k_value", ctypes.c_uint32),
        ("top_k_continuity", ctypes.c_uint32),
        ("top_k_protected", ctypes.c_uint32),
        ("protected_paths_per_band", ctypes.c_uint32),
        ("minimum_path_observations", ctypes.c_uint32),
        ("maximum_path_observations", ctypes.c_uint32),
        ("exact_set_candidate_limit", ctypes.c_uint32),
        ("amplitude_floor_q16", ctypes.c_uint32),
        ("amplitude_residual_weight_q8", ctypes.c_uint32),
        ("reserved_alignment", ctypes.c_uint32),
        ("frequency_sigma_floor_hz_q20", ctypes.c_uint64),
        ("birth_cost_bits_q8", ctypes.c_int64),
        ("death_cost_bits_q8", ctypes.c_int64),
        ("score_saturation", ctypes.c_int64),
        ("maximum_path_records", ctypes.c_uint64),
        ("maximum_total_entries", ctypes.c_uint64),
        ("maximum_frontier_states", ctypes.c_uint64),
        ("maximum_state_records", ctypes.c_uint64),
        ("maximum_work_units", ctypes.c_uint64),
        ("maximum_managed_bytes", ctypes.c_uint64),
        ("expected_input_fingerprint", ctypes.c_uint64 * 4),
        (
            "protected_band_upper_hz_q20",
            ctypes.c_int64 * (MAX_PROTECTED_BANDS - 1),
        ),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class PartialPath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("path_id", ctypes.c_uint64),
        ("entry_offset", ctypes.c_uint64),
        ("entry_count", ctypes.c_uint32),
        ("family_flags", ctypes.c_uint32),
        ("terminal_observation_id", ctypes.c_uint64),
        ("continuity_score_q8", ctypes.c_int64),
        ("potential_node_value_q8", ctypes.c_int64),
        ("uncertainty_leakage_penalty_q8", ctypes.c_int64),
        ("provisional_program_cost_q8", ctypes.c_int64),
        ("selection_score_q8", ctypes.c_int64),
        ("phase_error_sum_u64", ctypes.c_uint64),
        ("phase_error_count", ctypes.c_uint32),
        ("ownership_conflict_count", ctypes.c_uint32),
        ("protected_band_id", ctypes.c_uint32),
        ("value_rank", ctypes.c_uint32),
        ("continuity_rank", ctypes.c_uint32),
        ("protected_rank", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 5),
    ]


class PartialPathEntry(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("observation_id", ctypes.c_uint64),
        ("incoming_edge_candidate_id", ctypes.c_uint64),
        ("ownership_component", ctypes.c_uint32),
        ("second_order_cost_q8", ctypes.c_int32),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 3),
    ]


class PartialPathReport(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("termination", ctypes.c_uint32),
        ("solver", ctypes.c_uint32),
        ("required_path_count", ctypes.c_uint64),
        ("required_entry_count", ctypes.c_uint64),
        ("written_path_count", ctypes.c_uint64),
        ("written_entry_count", ctypes.c_uint64),
        ("raw_state_count", ctypes.c_uint64),
        ("frontier_peak", ctypes.c_uint64),
        ("work_units", ctypes.c_uint64),
        ("peak_live_managed_bytes", ctypes.c_uint64),
        ("selected_candidate_count", ctypes.c_uint64),
        ("selected_path_count", ctypes.c_uint64),
        ("internal_conflict_count", ctypes.c_uint64),
        ("cross_path_conflict_count", ctypes.c_uint64),
        ("score_saturation_count", ctypes.c_uint64),
        ("value_family_count", ctypes.c_uint64),
        ("continuity_family_count", ctypes.c_uint64),
        ("protected_family_count", ctypes.c_uint64),
        ("duplicate_state_count", ctypes.c_uint64),
        ("terminal_retained_state_count", ctypes.c_uint64),
        ("state_k_discarded_count", ctypes.c_uint64),
        ("state_arena_peak", ctypes.c_uint64),
        ("value_family_presented_count", ctypes.c_uint64),
        ("continuity_family_presented_count", ctypes.c_uint64),
        ("protected_family_presented_count", ctypes.c_uint64),
        ("value_family_discarded_count", ctypes.c_uint64),
        ("continuity_family_discarded_count", ctypes.c_uint64),
        ("protected_family_discarded_count", ctypes.c_uint64),
        ("output_deduplicated_count", ctypes.c_uint64),
        ("bound_rejected_count", ctypes.c_uint64),
        ("input_fingerprint", ctypes.c_uint64 * 4),
        ("output_fingerprint", ctypes.c_uint64 * 4),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 7),
    ]


class PartialPathManifestV3(ctypes.Structure):
    """Packed transactional R-197 path policy; never serialized."""

    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("second_order_law_version", ctypes.c_uint32),
        ("protected_band_count", ctypes.c_uint32),
        ("k_value_per_state", ctypes.c_uint32),
        ("k_continuity_per_state", ctypes.c_uint32),
        ("top_k_value", ctypes.c_uint32),
        ("top_k_continuity", ctypes.c_uint32),
        ("top_k_protected", ctypes.c_uint32),
        ("protected_paths_per_band", ctypes.c_uint32),
        ("minimum_path_observations", ctypes.c_uint32),
        ("maximum_path_observations", ctypes.c_uint32),
        ("exact_set_candidate_limit", ctypes.c_uint32),
        ("amplitude_floor_q16", ctypes.c_uint32),
        ("amplitude_residual_weight_q8", ctypes.c_uint32),
        ("work_ledger_version", ctypes.c_uint32),
        ("frequency_sigma_floor_hz_q20", ctypes.c_uint64),
        ("birth_cost_bits_q8", ctypes.c_int64),
        ("death_cost_bits_q8", ctypes.c_int64),
        ("score_saturation", ctypes.c_int64),
        ("maximum_path_records", ctypes.c_uint64),
        ("maximum_total_entries", ctypes.c_uint64),
        ("maximum_frontier_states", ctypes.c_uint64),
        ("maximum_state_records", ctypes.c_uint64),
        ("maximum_work_units", ctypes.c_uint64),
        ("maximum_managed_bytes", ctypes.c_uint64),
        ("maximum_device_bytes", ctypes.c_uint64),
        ("expected_input_fingerprint", ctypes.c_uint64 * 4),
        (
            "protected_band_upper_hz_q20",
            ctypes.c_int64 * (MAX_PROTECTED_BANDS - 1),
        ),
        ("reserved", ctypes.c_uint32 * 8),
    ]


class PartialPathV3(ctypes.Structure):
    _pack_ = 1
    _fields_ = PartialPath._fields_


class PartialPathEntryV3(ctypes.Structure):
    _pack_ = 1
    _fields_ = PartialPathEntry._fields_


class PartialPathReportV3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("abi_version", ctypes.c_uint32),
        ("termination", ctypes.c_uint32),
        ("solver", ctypes.c_uint32),
        ("required_path_count", ctypes.c_uint64),
        ("required_entry_count", ctypes.c_uint64),
        ("written_path_count", ctypes.c_uint64),
        ("written_entry_count", ctypes.c_uint64),
        ("raw_state_count", ctypes.c_uint64),
        ("frontier_peak", ctypes.c_uint64),
        ("work_units", ctypes.c_uint64),
        ("peak_live_managed_bytes", ctypes.c_uint64),
        ("selected_candidate_count", ctypes.c_uint64),
        ("selected_path_count", ctypes.c_uint64),
        ("internal_conflict_count", ctypes.c_uint64),
        ("cross_path_conflict_count", ctypes.c_uint64),
        ("score_saturation_count", ctypes.c_uint64),
        ("value_family_count", ctypes.c_uint64),
        ("continuity_family_count", ctypes.c_uint64),
        ("protected_family_count", ctypes.c_uint64),
        ("duplicate_state_count", ctypes.c_uint64),
        ("terminal_retained_state_count", ctypes.c_uint64),
        ("state_k_discarded_count", ctypes.c_uint64),
        ("state_arena_peak", ctypes.c_uint64),
        ("value_family_presented_count", ctypes.c_uint64),
        ("continuity_family_presented_count", ctypes.c_uint64),
        ("protected_family_presented_count", ctypes.c_uint64),
        ("value_family_discarded_count", ctypes.c_uint64),
        ("continuity_family_discarded_count", ctypes.c_uint64),
        ("protected_family_discarded_count", ctypes.c_uint64),
        ("output_deduplicated_count", ctypes.c_uint64),
        ("bound_rejected_count", ctypes.c_uint64),
        ("input_fingerprint", ctypes.c_uint64 * 4),
        ("output_fingerprint", ctypes.c_uint64 * 4),
        ("work_event_counts", ctypes.c_uint64 * PATH_V3_WORK_EVENT_COUNT),
        ("reserved_host_bytes", ctypes.c_uint64),
        ("committed_host_bytes", ctypes.c_uint64),
        ("peak_live_host_bytes", ctypes.c_uint64),
        ("reserved_device_bytes", ctypes.c_uint64),
        ("committed_device_bytes", ctypes.c_uint64),
        ("peak_live_device_bytes", ctypes.c_uint64),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 7),
    ]


@dataclass(frozen=True)
class EdgeRecord:
    candidate_id: int
    source_observation_id: int
    target_observation_id: int
    center_delta_samples: int
    frequency_delta_hz_q20: int
    gap_hops: int
    cycle_offset: int
    phase_error_u31: int
    continuity_cost_q8: int
    provisional_program_cost_q8: int
    flags: int


@dataclass(frozen=True)
class PathEntryRecord:
    observation_id: int
    incoming_edge_candidate_id: int
    ownership_component: int
    second_order_cost_q8: int
    flags: int = 0


@dataclass(frozen=True)
class PathRecord:
    path_id: int
    entries: tuple[PathEntryRecord, ...]
    family_flags: int
    terminal_observation_id: int
    continuity_score_q8: int
    potential_node_value_q8: int
    uncertainty_leakage_penalty_q8: int
    provisional_program_cost_q8: int
    selection_score_q8: int
    phase_error_sum_u64: int
    phase_error_count: int
    ownership_conflict_count: int
    protected_band_id: int
    value_rank: int
    continuity_rank: int
    protected_rank: int
    flags: int


@dataclass(frozen=True)
class PathOracleResult:
    paths: tuple[PathRecord, ...]
    selected_path_ids: tuple[int, ...]
    report: dict


@dataclass(frozen=True)
class _PathState:
    observation_ids: tuple[int, ...]
    incoming_edge_ids: tuple[int, ...]
    second_order_costs_q8: tuple[int, ...]
    continuity_cost_q8: int
    potential_node_value_q8: int
    uncertainty_leakage_penalty_q8: int
    provisional_program_cost_q8: int
    phase_error_sum_u64: int
    phase_error_count: int


def make_resolution(
    resolution_id: int,
    fft_samples: int,
    hop_samples: int,
) -> PartialResolution:
    value = PartialResolution()
    value.struct_size = ctypes.sizeof(value)
    value.abi_version = ABI_VERSION
    value.resolution_id = resolution_id
    value.fft_samples = fft_samples
    value.hop_samples = hop_samples
    return value


def make_manifest(
    *,
    sample_rate: int,
    resolution_count: int,
    gaps: tuple[int, ...] = (1, 2, 4, 8),
    neighbors_per_gap: int = 4,
    cycle_offsets: tuple[int, ...] = (-2, -1, 0, 1, 2),
    maximum_frequency_jump_hz_q20: int = 80 << 20,
    maximum_frequency_slope_hz_per_sample_q20: int = 1 << 16,
    maximum_edge_records: int = 1_000_000,
) -> PartialGraphManifest:
    value = PartialGraphManifest()
    value.struct_size = ctypes.sizeof(value)
    value.abi_version = ABI_VERSION
    value.sample_rate = sample_rate
    value.resolution_count = resolution_count
    value.gap_count = len(gaps)
    value.neighbors_per_gap = neighbors_per_gap
    value.cycle_offset_count = len(cycle_offsets)
    value.minimum_track_observations = 4
    value.maximum_frequency_jump_hz_q20 = (
        maximum_frequency_jump_hz_q20
    )
    value.maximum_frequency_slope_hz_per_sample_q20 = (
        maximum_frequency_slope_hz_per_sample_q20
    )
    value.continuation_base_bits_q8 = 12 << 8
    value.continuation_reward_q8 = 12 << 8
    value.score_saturation = (1 << 31) - 1
    value.maximum_edge_records = maximum_edge_records
    value.maximum_path_hypotheses = 65536
    value.exact_set_candidate_limit = 20
    for index, gap in enumerate(gaps):
        value.gaps[index] = gap
    for index, offset in enumerate(cycle_offsets):
        value.cycle_offsets[index] = offset
    return value


def make_observation(
    *,
    observation_id: int,
    frame_index: int,
    resolution_id: int,
    hop_samples: int,
    frequency_hz_q20: int,
    phase_turn_u32: int,
    phase_step_u32: int,
    normalized_amplitude_q16: int,
    ownership_component: int,
    detector_id: int = -1,
    frequency_uncertainty_hz_q20: int = 1 << 20,
    phase_uncertainty_u31: int = 1 << 20,
    flags: int = PHASE_USABLE | LOCALLY_RESOLVABLE,
    neighbor_priority_q8: int = 512,
    potential_node_value_q8: int = 1024,
    uncertainty_leakage_penalty_q8: int = 64,
) -> PartialObservation:
    value = PartialObservation()
    value.struct_size = ctypes.sizeof(value)
    value.abi_version = ABI_VERSION
    value.observation_id = observation_id
    value.center_sample = frame_index * hop_samples
    value.frequency_hz_q20 = frequency_hz_q20
    value.frequency_uncertainty_hz_q20 = (
        frequency_uncertainty_hz_q20
    )
    value.phase_turn_u32 = phase_turn_u32 & _U32_MASK
    value.phase_step_u32 = phase_step_u32 & _U32_MASK
    value.normalized_amplitude_q16 = normalized_amplitude_q16
    value.amplitude_uncertainty_q16 = 1 << 12
    value.phase_uncertainty_u31 = phase_uncertainty_u31
    value.frame_index = frame_index
    value.resolution_id = resolution_id
    value.detector_id = detector_id
    value.band_id = 3
    value.ownership_component = ownership_component
    value.ambiguity_component = AMBIGUITY_NONE
    value.flags = flags
    value.protected_rank_q8 = 256
    value.neighbor_priority_q8 = neighbor_priority_q8
    value.potential_node_value_q8 = potential_node_value_q8
    value.uncertainty_leakage_penalty_q8 = (
        uncertainty_leakage_penalty_q8
    )
    return value


def _ratio_q16(numerator: int, denominator: int) -> int:
    if denominator == 0:
        return (65535 << 16) | 0xFFFF
    integer, remainder = divmod(numerator, denominator)
    if integer >= 65535:
        return (65535 << 16) | 0xFFFF
    fraction = 0
    for _bit in range(16):
        fraction <<= 1
        if remainder >= denominator - remainder:
            remainder -= denominator - remainder
            fraction |= 1
        else:
            remainder *= 2
    return (integer << 16) | fraction


def log2_one_plus_ratio_q8(numerator: int, denominator: int) -> int:
    """Return the exact integer law frozen by R-190."""

    value_q16 = (1 << 16) + _ratio_q16(numerator, denominator)
    most_significant = value_q16.bit_length() - 1
    integer_part = most_significant - 16
    if most_significant <= 31:
        normalized_q31 = value_q16 << (31 - most_significant)
    else:
        normalized_q31 = value_q16 >> (most_significant - 31)
    fractional = 0
    for _bit in range(8):
        squared_q31 = (normalized_q31 * normalized_q31) >> 31
        fractional <<= 1
        if squared_q31 >= 1 << 32:
            squared_q31 >>= 1
            fractional |= 1
        normalized_q31 = squared_q31
    return integer_part * 256 + fractional


def _signed_log_amplitude_ratio_q8(target: int, source: int) -> int:
    if target == source:
        return 0
    if source == 0:
        return 0 if target == 0 else _I32_MAX // 4
    if target == 0:
        return _I32_MIN // 4
    if target > source:
        return log2_one_plus_ratio_q8(target - source, source)
    return -log2_one_plus_ratio_q8(source - target, target)


def _phase_advance_u32(
    source_step: int,
    target_step: int,
    center_delta: int,
) -> int:
    step_sum = source_step + target_step
    product = (
        (step_sum >> 1) & _U32_MASK
    ) * (center_delta & _U32_MASK)
    result = product & _U32_MASK
    if step_sum & 1:
        result = (
            result + ((center_delta >> 1) + (center_delta & 1))
        ) & _U32_MASK
    return result


def _phase_error_u31(
    source: PartialObservation,
    target: PartialObservation,
) -> int:
    center_delta = target.center_sample - source.center_sample
    expected = (
        source.phase_turn_u32
        + _phase_advance_u32(
            source.phase_step_u32,
            target.phase_step_u32,
            center_delta,
        )
    ) & _U32_MASK
    raw = (target.phase_turn_u32 - expected) & _U32_MASK
    wrapped = raw if raw < 1 << 31 else raw - (1 << 32)
    return abs(wrapped)


def _saturating_add(left: int, right: int, limit: int) -> int:
    return max(-limit, min(limit, left + right))


def _score_edge(
    candidate_id: int,
    source: PartialObservation,
    target: PartialObservation,
    gap: int,
    cycle_offset: int,
    manifest: PartialGraphManifest,
) -> EdgeRecord:
    frequency_delta = (
        target.frequency_hz_q20 - source.frequency_hz_q20
    )
    uncertainty = min(
        _U64_MAX,
        source.frequency_uncertainty_hz_q20
        + target.frequency_uncertainty_hz_q20,
    )
    frequency_cost = log2_one_plus_ratio_q8(
        abs(frequency_delta),
        max(1, uncertainty),
    )
    amplitude_log = _signed_log_amplitude_ratio_q8(
        target.normalized_amplitude_q16,
        source.normalized_amplitude_q16,
    )
    amplitude_cost = log2_one_plus_ratio_q8(
        abs(amplitude_log) * 8,
        256,
    )
    phase_usable = (
        source.flags & PHASE_USABLE
        and target.flags & PHASE_USABLE
    )
    phase_error = (
        _phase_error_u31(source, target) if phase_usable else 0
    )
    phase_uncertainty = (
        source.phase_uncertainty_u31
        + target.phase_uncertainty_u31
    )
    phase_cost = (
        log2_one_plus_ratio_q8(
            phase_error,
            max(1, phase_uncertainty),
        )
        if phase_usable
        else 0
    )
    components = (
        frequency_cost,
        amplitude_cost,
        phase_cost,
        log2_one_plus_ratio_q8(gap, 1),
        log2_one_plus_ratio_q8(abs(cycle_offset), 1),
    )
    continuity = 0
    for component in components:
        continuity = _saturating_add(
            continuity,
            component,
            manifest.score_saturation,
        )
    program = _saturating_add(
        manifest.continuation_base_bits_q8,
        continuity,
        manifest.score_saturation,
    )
    return EdgeRecord(
        candidate_id=candidate_id,
        source_observation_id=source.observation_id,
        target_observation_id=target.observation_id,
        center_delta_samples=(
            target.center_sample - source.center_sample
        ),
        frequency_delta_hz_q20=frequency_delta,
        gap_hops=gap,
        cycle_offset=cycle_offset,
        phase_error_u31=phase_error,
        continuity_cost_q8=max(_I32_MIN, min(_I32_MAX, continuity)),
        provisional_program_cost_q8=max(
            _I32_MIN,
            min(_I32_MAX, program),
        ),
        flags=1 if phase_usable else 0,
    )


def enumerate_edges_fixed(
    resolutions: tuple[PartialResolution, ...],
    observations: tuple[PartialObservation, ...],
    manifest: PartialGraphManifest,
) -> tuple[EdgeRecord, ...]:
    resolution_table = {
        item.resolution_id: item for item in resolutions
    }
    edges = []
    candidate_id = 0
    canonical_observations = tuple(sorted(
        observations,
        key=lambda item: (
            item.center_sample,
            item.resolution_id,
            item.detector_id,
            item.frequency_hz_q20,
            item.observation_id,
        ),
    ))
    for source in canonical_observations:
        if not source.flags & LOCALLY_RESOLVABLE:
            continue
        resolution = resolution_table[source.resolution_id]
        for gap_index in range(manifest.gap_count):
            gap = manifest.gaps[gap_index]
            center_delta = gap * resolution.hop_samples
            target_center = source.center_sample + center_delta
            slope = manifest.maximum_frequency_slope_hz_per_sample_q20
            maximum_distance = min(
                (1 << 63) - 1,
                manifest.maximum_frequency_jump_hz_q20
                + slope * center_delta,
            )
            targets = []
            for target in canonical_observations:
                if (
                    target.resolution_id != source.resolution_id
                    or target.detector_id != source.detector_id
                    or target.center_sample != target_center
                    or not target.flags & LOCALLY_RESOLVABLE
                ):
                    continue
                frequency_delta = (
                    target.frequency_hz_q20
                    - source.frequency_hz_q20
                )
                if abs(frequency_delta) > maximum_distance:
                    continue
                uncertainty = min(
                    _U64_MAX,
                    source.frequency_uncertainty_hz_q20
                    + target.frequency_uncertainty_hz_q20,
                )
                targets.append((
                    log2_one_plus_ratio_q8(
                        abs(frequency_delta),
                        max(1, uncertainty),
                    ),
                    -target.neighbor_priority_q8,
                    target.observation_id,
                    target,
                ))
            targets.sort(key=lambda row: row[:3])
            for _distance, _priority, _identifier, target in targets[
                : manifest.neighbors_per_gap
            ]:
                for cycle_index in range(manifest.cycle_offset_count):
                    if candidate_id >= manifest.maximum_edge_records:
                        raise OverflowError("R-190 edge bound reached")
                    edges.append(_score_edge(
                        candidate_id,
                        source,
                        target,
                        gap,
                        manifest.cycle_offsets[cycle_index],
                        manifest,
                    ))
                    candidate_id += 1
    return tuple(edges)


def make_path_manifest(
    *,
    protected_band_upper_hz_q20: tuple[int, ...],
    minimum_path_observations: int = 3,
    maximum_path_observations: int = 4096,
    k_value_per_state: int = 8,
    k_continuity_per_state: int = 8,
    top_k_value: int = 128,
    top_k_continuity: int = 128,
    top_k_protected: int = 128,
    protected_paths_per_band: int = 2,
    exact_set_candidate_limit: int = 20,
    maximum_path_records: int = 1024,
    maximum_total_entries: int = 1_000_000,
    maximum_frontier_states: int = 250_000,
    maximum_state_records: int = 1_000_000,
    maximum_work_units: int = 10_000_000,
    maximum_managed_bytes: int = 2 << 30,
) -> PartialPathManifest:
    if (
        len(protected_band_upper_hz_q20) >= MAX_PROTECTED_BANDS
        or tuple(sorted(set(protected_band_upper_hz_q20)))
        != protected_band_upper_hz_q20
    ):
        raise ValueError("invalid protected frequency bands")
    value = PartialPathManifest()
    value.struct_size = ctypes.sizeof(value)
    value.abi_version = PATH_ABI_VERSION
    value.second_order_law_version = 2
    value.protected_band_count = (
        len(protected_band_upper_hz_q20) + 1
    )
    value.k_value_per_state = k_value_per_state
    value.k_continuity_per_state = k_continuity_per_state
    value.top_k_value = top_k_value
    value.top_k_continuity = top_k_continuity
    value.top_k_protected = top_k_protected
    value.protected_paths_per_band = protected_paths_per_band
    value.minimum_path_observations = minimum_path_observations
    value.maximum_path_observations = maximum_path_observations
    value.exact_set_candidate_limit = exact_set_candidate_limit
    value.amplitude_floor_q16 = 1
    value.amplitude_residual_weight_q8 = 4 << 8
    value.frequency_sigma_floor_hz_q20 = 1 << 19
    value.birth_cost_bits_q8 = 48 << 8
    value.death_cost_bits_q8 = 8 << 8
    value.score_saturation = (1 << 62) - 1
    value.maximum_path_records = maximum_path_records
    value.maximum_total_entries = maximum_total_entries
    value.maximum_frontier_states = maximum_frontier_states
    value.maximum_state_records = maximum_state_records
    value.maximum_work_units = maximum_work_units
    value.maximum_managed_bytes = maximum_managed_bytes
    for index, upper in enumerate(protected_band_upper_hz_q20):
        value.protected_band_upper_hz_q20[index] = upper
    return value


def upgrade_path_manifest_v3(
    source: PartialPathManifest,
    *,
    maximum_device_bytes: int = 0,
) -> PartialPathManifestV3:
    """Promote an R-191 policy to the transactional R-197 ABI."""

    value = PartialPathManifestV3()
    value.struct_size = ctypes.sizeof(value)
    value.abi_version = PATH_V3_ABI_VERSION
    value.second_order_law_version = source.second_order_law_version
    value.protected_band_count = source.protected_band_count
    value.k_value_per_state = source.k_value_per_state
    value.k_continuity_per_state = source.k_continuity_per_state
    value.top_k_value = source.top_k_value
    value.top_k_continuity = source.top_k_continuity
    value.top_k_protected = source.top_k_protected
    value.protected_paths_per_band = source.protected_paths_per_band
    value.minimum_path_observations = source.minimum_path_observations
    value.maximum_path_observations = source.maximum_path_observations
    value.exact_set_candidate_limit = source.exact_set_candidate_limit
    value.amplitude_floor_q16 = source.amplitude_floor_q16
    value.amplitude_residual_weight_q8 = source.amplitude_residual_weight_q8
    value.work_ledger_version = PATH_WORK_LEDGER_VERSION
    value.frequency_sigma_floor_hz_q20 = (
        source.frequency_sigma_floor_hz_q20
    )
    value.birth_cost_bits_q8 = source.birth_cost_bits_q8
    value.death_cost_bits_q8 = source.death_cost_bits_q8
    value.score_saturation = source.score_saturation
    value.maximum_path_records = source.maximum_path_records
    value.maximum_total_entries = source.maximum_total_entries
    value.maximum_frontier_states = source.maximum_frontier_states
    value.maximum_state_records = source.maximum_state_records
    value.maximum_work_units = source.maximum_work_units
    value.maximum_managed_bytes = source.maximum_managed_bytes
    value.maximum_device_bytes = maximum_device_bytes
    for index in range(4):
        value.expected_input_fingerprint[index] = (
            source.expected_input_fingerprint[index]
        )
    for index in range(MAX_PROTECTED_BANDS - 1):
        value.protected_band_upper_hz_q20[index] = (
            source.protected_band_upper_hz_q20[index]
        )
    return value


def _scale_nearest_even(
    value: int,
    numerator: int,
    denominator: int,
    saturation: int,
) -> tuple[int, bool]:
    """Return R-191 signed ratio scaling and whether it saturated."""

    if denominator <= 0 or numerator < 0 or saturation <= 0:
        raise ValueError("invalid R-191 scale")
    magnitude = abs(value)
    quotient, remainder = divmod(magnitude * numerator, denominator)
    complement = denominator - remainder
    if remainder > complement or (
        remainder == complement and quotient & 1
    ):
        quotient += 1
    saturated = quotient > saturation
    quotient = min(quotient, saturation)
    return (-quotient if value < 0 else quotient), saturated


def _second_order_cost_q8(
    previous: PartialObservation,
    current: PartialObservation,
    target: PartialObservation,
    manifest: PartialPathManifest,
) -> tuple[int, bool]:
    dt01 = current.center_sample - previous.center_sample
    dt12 = target.center_sample - current.center_sample
    if dt01 <= 0 or dt12 <= 0:
        return manifest.score_saturation, True

    predicted_frequency_delta, frequency_saturated = (
        _scale_nearest_even(
            current.frequency_hz_q20 - previous.frequency_hz_q20,
            dt12,
            dt01,
            manifest.score_saturation,
        )
    )
    actual_frequency_delta = (
        target.frequency_hz_q20 - current.frequency_hz_q20
    )
    frequency_residual = abs(
        actual_frequency_delta - predicted_frequency_delta
    )
    pair_uncertainty = min(
        _U64_MAX,
        previous.frequency_uncertainty_hz_q20
        + current.frequency_uncertainty_hz_q20,
    )
    scaled_pair_uncertainty = min(
        _U64_MAX,
        (
            pair_uncertainty * dt12
            + dt01
            - 1
        )
        // dt01,
    )
    frequency_sigma = max(
        manifest.frequency_sigma_floor_hz_q20,
        min(
            _U64_MAX,
            target.frequency_uncertainty_hz_q20
            + current.frequency_uncertainty_hz_q20
            + scaled_pair_uncertainty,
        ),
    )
    frequency_cost = log2_one_plus_ratio_q8(
        frequency_residual,
        frequency_sigma,
    )

    amplitude_floor = manifest.amplitude_floor_q16
    previous_amplitude = max(
        amplitude_floor,
        previous.normalized_amplitude_q16,
    )
    current_amplitude = max(
        amplitude_floor,
        current.normalized_amplitude_q16,
    )
    target_amplitude = max(
        amplitude_floor,
        target.normalized_amplitude_q16,
    )
    first_log_delta = _signed_log_amplitude_ratio_q8(
        current_amplitude,
        previous_amplitude,
    )
    actual_log_delta = _signed_log_amplitude_ratio_q8(
        target_amplitude,
        current_amplitude,
    )
    predicted_log_delta, amplitude_saturated = _scale_nearest_even(
        first_log_delta,
        dt12,
        dt01,
        manifest.score_saturation,
    )
    amplitude_residual = abs(
        actual_log_delta - predicted_log_delta
    )
    weighted_amplitude = min(
        _U64_MAX,
        amplitude_residual
        * manifest.amplitude_residual_weight_q8,
    )
    amplitude_cost = log2_one_plus_ratio_q8(
        weighted_amplitude,
        1 << 16,
    )
    total = frequency_cost + amplitude_cost
    total_saturated = total > manifest.score_saturation
    return (
        min(total, manifest.score_saturation),
        frequency_saturated or amplitude_saturated or total_saturated,
    )


def _path_saturating_sum(
    left: int,
    right: int,
    manifest: PartialPathManifest,
    saturation_counter: list[int],
) -> int:
    total = left + right
    if total > manifest.score_saturation:
        saturation_counter[0] += 1
        return manifest.score_saturation
    if total < -manifest.score_saturation:
        saturation_counter[0] += 1
        return -manifest.score_saturation
    return total


def _state_continuity_score_q8(
    state: _PathState,
    graph_manifest: PartialGraphManifest,
    path_manifest: PartialPathManifest,
    saturation_counter: list[int],
) -> int:
    reward = (
        graph_manifest.continuation_reward_q8
        * (len(state.observation_ids) - 1)
    )
    del saturation_counter
    return max(
        -path_manifest.score_saturation,
        min(
            path_manifest.score_saturation,
            reward - state.continuity_cost_q8,
        ),
    )


def _state_value_score_q8(
    state: _PathState,
    graph_manifest: PartialGraphManifest,
    path_manifest: PartialPathManifest,
    saturation_counter: list[int],
) -> int:
    del saturation_counter
    continuity = _state_continuity_score_q8(
        state,
        graph_manifest,
        path_manifest,
        [],
    )
    return max(
        -path_manifest.score_saturation,
        min(
            path_manifest.score_saturation,
            state.potential_node_value_q8
            - state.uncertainty_leakage_penalty_q8
            + half_score_floor(continuity),
        ),
    )


def half_score_floor(value: int) -> int:
    """Divide a signed score by two with the normative floor tie rule."""

    return value // 2


def _state_identity(
    state: _PathState,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return state.observation_ids, state.incoming_edge_ids


def _retain_path_state_union(
    states: list[_PathState],
    graph_manifest: PartialGraphManifest,
    path_manifest: PartialPathManifest,
    saturation_counter: list[int],
) -> list[_PathState]:
    unique = {_state_identity(state): state for state in states}
    value_ranked = sorted(
        unique.values(),
        key=lambda state: (
            -_state_value_score_q8(
                state,
                graph_manifest,
                path_manifest,
                saturation_counter,
            ),
            -len(state.observation_ids),
            _state_identity(state),
        ),
    )
    continuity_ranked = sorted(
        unique.values(),
        key=lambda state: (
            -_state_continuity_score_q8(
                state,
                graph_manifest,
                path_manifest,
                saturation_counter,
            ),
            -len(state.observation_ids),
            _state_identity(state),
        ),
    )
    retained = {
        _state_identity(state): state
        for state in value_ranked[: path_manifest.k_value_per_state]
    }
    for state in continuity_ranked[
        : path_manifest.k_continuity_per_state
    ]:
        retained[_state_identity(state)] = state
    return sorted(
        retained.values(),
        key=lambda state: (
            -_state_value_score_q8(
                state,
                graph_manifest,
                path_manifest,
                saturation_counter,
            ),
            _state_identity(state),
        ),
    )


def _lower_median_frequency_band(
    observation_ids: tuple[int, ...],
    by_id: dict[int, PartialObservation],
    manifest: PartialPathManifest,
) -> int:
    frequencies = sorted(
        by_id[observation_id].frequency_hz_q20
        for observation_id in observation_ids
    )
    median = frequencies[(len(frequencies) - 1) // 2]
    band = 0
    while (
        band + 1 < manifest.protected_band_count
        and median
        >= manifest.protected_band_upper_hz_q20[band]
    ):
        band += 1
    return band


def _paths_conflict(
    first: _PathState,
    second: _PathState,
    by_id: dict[int, PartialObservation],
) -> bool:
    first_components = {
        by_id[item].ownership_component
        for item in first.observation_ids
    }
    return any(
        by_id[item].ownership_component in first_components
        for item in second.observation_ids
    )


def build_paths_fixed(
    observations: tuple[PartialObservation, ...],
    edges: tuple[EdgeRecord, ...],
    graph_manifest: PartialGraphManifest,
    path_manifest: PartialPathManifest,
) -> PathOracleResult:
    """Build the R-191 analyzer path union without predictor/byte claims."""

    by_id = {
        observation.observation_id: observation
        for observation in observations
    }
    if len(by_id) != len(observations):
        raise ValueError("duplicate observation ID")
    edge_by_id = {edge.candidate_id: edge for edge in edges}
    if len(edge_by_id) != len(edges):
        raise ValueError("duplicate edge candidate ID")
    if (
        path_manifest.second_order_law_version != 2
        or path_manifest.amplitude_floor_q16 == 0
        or path_manifest.frequency_sigma_floor_hz_q20 == 0
        or path_manifest.minimum_path_observations < 2
        or path_manifest.minimum_path_observations
        > path_manifest.maximum_path_observations
        or path_manifest.maximum_path_records
        < (
            path_manifest.top_k_value
            + path_manifest.top_k_continuity
            + path_manifest.top_k_protected
        )
    ):
        raise ValueError("invalid R-191 path manifest")

    canonical_edges = tuple(sorted(edges, key=lambda edge: edge.candidate_id))
    incoming: dict[int, list[EdgeRecord]] = {}
    for edge in canonical_edges:
        if (
            edge.source_observation_id not in by_id
            or edge.target_observation_id not in by_id
            or by_id[edge.target_observation_id].center_sample
            <= by_id[edge.source_observation_id].center_sample
        ):
            raise ValueError("invalid edge topology")
        incoming.setdefault(edge.target_observation_id, []).append(edge)

    saturation_count = [0]
    work_units = 0
    raw_state_count = 0
    frontier_peak = 0
    states: dict[tuple[int, int], list[_PathState]] = {}
    ordered_targets = sorted(
        observations,
        key=lambda item: (
            item.center_sample,
            item.resolution_id,
            item.detector_id,
            item.frequency_hz_q20,
            item.observation_id,
        ),
    )
    for target in ordered_targets:
        pending: dict[tuple[int, int], list[_PathState]] = {}
        for edge in incoming.get(target.observation_id, ()):
            source_id = edge.source_observation_id
            source = by_id[source_id]
            candidates = [
                _PathState(
                    observation_ids=(source_id, target.observation_id),
                    incoming_edge_ids=(
                        PATH_ENTRY_BIRTH_EDGE,
                        edge.candidate_id,
                    ),
                    second_order_costs_q8=(0, 0),
                    continuity_cost_q8=edge.continuity_cost_q8,
                    potential_node_value_q8=_path_saturating_sum(
                        source.potential_node_value_q8,
                        target.potential_node_value_q8,
                        path_manifest,
                        saturation_count,
                    ),
                    uncertainty_leakage_penalty_q8=(
                        _path_saturating_sum(
                            source.uncertainty_leakage_penalty_q8,
                            target.uncertainty_leakage_penalty_q8,
                            path_manifest,
                            saturation_count,
                        )
                    ),
                    provisional_program_cost_q8=_path_saturating_sum(
                        path_manifest.birth_cost_bits_q8,
                        edge.provisional_program_cost_q8,
                        path_manifest,
                        saturation_count,
                    ),
                    phase_error_sum_u64=(
                        edge.phase_error_u31 if edge.flags & 1 else 0
                    ),
                    phase_error_count=1 if edge.flags & 1 else 0,
                )
            ]
            for (previous_id, current_id), prior_states in tuple(
                states.items()
            ):
                if current_id != source_id:
                    continue
                for prior in prior_states:
                    if (
                        len(prior.observation_ids)
                        >= path_manifest.maximum_path_observations
                    ):
                        continue
                    second_order, saturated = _second_order_cost_q8(
                        by_id[previous_id],
                        source,
                        target,
                        path_manifest,
                    )
                    if saturated:
                        saturation_count[0] += 1
                    candidates.append(_PathState(
                        observation_ids=(
                            *prior.observation_ids,
                            target.observation_id,
                        ),
                        incoming_edge_ids=(
                            *prior.incoming_edge_ids,
                            edge.candidate_id,
                        ),
                        second_order_costs_q8=(
                            *prior.second_order_costs_q8,
                            second_order,
                        ),
                        continuity_cost_q8=_path_saturating_sum(
                            _path_saturating_sum(
                                prior.continuity_cost_q8,
                                edge.continuity_cost_q8,
                                path_manifest,
                                saturation_count,
                            ),
                            second_order,
                            path_manifest,
                            saturation_count,
                        ),
                        potential_node_value_q8=_path_saturating_sum(
                            prior.potential_node_value_q8,
                            target.potential_node_value_q8,
                            path_manifest,
                            saturation_count,
                        ),
                        uncertainty_leakage_penalty_q8=(
                            _path_saturating_sum(
                                prior.uncertainty_leakage_penalty_q8,
                                target.uncertainty_leakage_penalty_q8,
                                path_manifest,
                                saturation_count,
                            )
                        ),
                        provisional_program_cost_q8=(
                            _path_saturating_sum(
                                prior.provisional_program_cost_q8,
                                edge.provisional_program_cost_q8,
                                path_manifest,
                                saturation_count,
                            )
                        ),
                        phase_error_sum_u64=min(
                            _U64_MAX,
                            prior.phase_error_sum_u64
                            + (
                                edge.phase_error_u31
                                if edge.flags & 1
                                else 0
                            ),
                        ),
                        phase_error_count=(
                            prior.phase_error_count
                            + (1 if edge.flags & 1 else 0)
                        ),
                    ))
            work_units += len(candidates)
            raw_state_count += len(candidates)
            if work_units > path_manifest.maximum_work_units:
                raise OverflowError("R-191 work-unit bound reached")
            pending.setdefault(
                (source_id, target.observation_id),
                [],
            ).extend(candidates)
        for state_key, candidates in pending.items():
            states[state_key] = _retain_path_state_union(
                candidates,
                graph_manifest,
                path_manifest,
                saturation_count,
            )
        frontier_size = sum(len(rows) for rows in states.values())
        frontier_peak = max(frontier_peak, frontier_size)
        if frontier_size > path_manifest.maximum_frontier_states:
            raise OverflowError("R-191 frontier-state bound reached")

    raw_paths = {}
    for rows in states.values():
        for state in rows:
            if (
                len(state.observation_ids)
                >= path_manifest.minimum_path_observations
            ):
                raw_paths[_state_identity(state)] = state

    def continuity_score(state: _PathState) -> int:
        return _state_continuity_score_q8(
            state,
            graph_manifest,
            path_manifest,
            saturation_count,
        )

    def value_score(state: _PathState) -> int:
        return _state_value_score_q8(
            state,
            graph_manifest,
            path_manifest,
            saturation_count,
        )

    value_ranked = sorted(
        raw_paths.values(),
        key=lambda state: (
            -value_score(state),
            _state_identity(state),
        ),
    )
    continuity_ranked = sorted(
        raw_paths.values(),
        key=lambda state: (
            -continuity_score(state),
            _state_identity(state),
        ),
    )
    family_members: dict[
        tuple[tuple[int, ...], tuple[int, ...]],
        int,
    ] = {}
    value_ranks = {}
    continuity_ranks = {}
    protected_ranks = {}
    for rank, state in enumerate(
        value_ranked[: path_manifest.top_k_value]
    ):
        identity = _state_identity(state)
        family_members[identity] = (
            family_members.get(identity, 0)
            | PATH_FAMILY_LOCAL_POTENTIAL
        )
        value_ranks[identity] = rank
    for rank, state in enumerate(
        continuity_ranked[: path_manifest.top_k_continuity]
    ):
        identity = _state_identity(state)
        family_members[identity] = (
            family_members.get(identity, 0)
            | PATH_FAMILY_CONTINUITY
        )
        continuity_ranks[identity] = rank

    protected_by_band: dict[int, list[_PathState]] = {}
    for state in raw_paths.values():
        if not any(
            by_id[item].flags & PROTECTED_WEAK
            for item in state.observation_ids
        ):
            continue
        band = _lower_median_frequency_band(
            state.observation_ids,
            by_id,
            path_manifest,
        )
        protected_by_band.setdefault(band, []).append(state)

    protected_candidates = []
    for band, rows in protected_by_band.items():
        rows.sort(key=lambda state: (
            -sum(
                1
                for item in state.observation_ids
                if by_id[item].flags & PROTECTED_WEAK
            ),
            -sum(
                max(0, by_id[item].protected_rank_q8)
                for item in state.observation_ids
                if by_id[item].flags & PROTECTED_WEAK
            ),
            -continuity_score(state),
            _state_identity(state),
        ))
        protected_candidates.extend(
            (band, state)
            for state in rows[: path_manifest.protected_paths_per_band]
        )
    protected_candidates.sort(key=lambda row: (
        -sum(
            1
            for item in row[1].observation_ids
            if by_id[item].flags & PROTECTED_WEAK
        ),
        -sum(
            max(0, by_id[item].protected_rank_q8)
            for item in row[1].observation_ids
            if by_id[item].flags & PROTECTED_WEAK
        ),
        -continuity_score(row[1]),
        row[0],
        _state_identity(row[1]),
    ))
    for rank, (_band, state) in enumerate(
        protected_candidates[: path_manifest.top_k_protected]
    ):
        identity = _state_identity(state)
        family_members[identity] = (
            family_members.get(identity, 0)
            | PATH_FAMILY_PROTECTED_WEAK
        )
        protected_ranks[identity] = rank

    union = [raw_paths[identity] for identity in family_members]
    union.sort(key=lambda state: (
        -value_score(state),
        -continuity_score(state),
        _state_identity(state),
    ))
    if len(union) > path_manifest.maximum_path_records:
        raise OverflowError("R-191 path-record bound reached")

    internal_conflicts = {}
    bands = {}
    for state in union:
        components = [
            by_id[item].ownership_component
            for item in state.observation_ids
        ]
        internal_conflicts[_state_identity(state)] = (
            len(components) - len(set(components))
        )
        bands[_state_identity(state)] = _lower_median_frequency_band(
            state.observation_ids,
            by_id,
            path_manifest,
        )

    path_ids = {
        _state_identity(state): index
        for index, state in enumerate(union)
    }
    selection_candidates = [
        state
        for state in union
        if internal_conflicts[_state_identity(state)] == 0
        and max(0, value_score(state), continuity_score(state)) > 0
    ]
    cross_conflict_count = 0
    conflict_pairs = set()
    for left_index, left in enumerate(selection_candidates):
        for right_index in range(left_index + 1, len(selection_candidates)):
            right = selection_candidates[right_index]
            if _paths_conflict(left, right, by_id):
                conflict_pairs.add((left_index, right_index))
                cross_conflict_count += 1
    work_units += len(conflict_pairs)
    if work_units > path_manifest.maximum_work_units:
        raise OverflowError("R-191 work-unit bound reached")

    if (
        len(selection_candidates)
        <= path_manifest.exact_set_candidate_limit
    ):
        best_score = 0
        best_ids: tuple[int, ...] = ()
        for mask in range(1 << len(selection_candidates)):
            work_units += 1
            if work_units > path_manifest.maximum_work_units:
                raise OverflowError("R-191 work-unit bound reached")
            chosen = tuple(
                index
                for index in range(len(selection_candidates))
                if mask & (1 << index)
            )
            if any(
                left in chosen and right in chosen
                for left, right in conflict_pairs
            ):
                continue
            ids = tuple(sorted(
                path_ids[_state_identity(selection_candidates[index])]
                for index in chosen
            ))
            score = sum(
                max(
                    0,
                    value_score(selection_candidates[index]),
                    continuity_score(selection_candidates[index]),
                )
                for index in chosen
            )
            if score > best_score or (
                score == best_score and ids < best_ids
            ):
                best_score = score
                best_ids = ids
        selected_ids = best_ids
        solver = "exact-small-disjoint-heuristic"
    else:
        selected_states = []
        for state in sorted(
            selection_candidates,
            key=lambda item: (
                -max(0, value_score(item), continuity_score(item)),
                _state_identity(item),
            ),
        ):
            if any(
                _paths_conflict(state, incumbent, by_id)
                for incumbent in selected_states
            ):
                continue
            selected_states.append(state)
        selected_ids = tuple(sorted(
            path_ids[_state_identity(state)]
            for state in selected_states
        ))
        solver = "deterministic-bounded-disjoint-heuristic"

    records = []
    total_entries = 0
    for path_id, state in enumerate(union):
        identity = _state_identity(state)
        entries = tuple(
            PathEntryRecord(
                observation_id=observation_id,
                incoming_edge_candidate_id=state.incoming_edge_ids[index],
                ownership_component=(
                    by_id[observation_id].ownership_component
                ),
                second_order_cost_q8=(
                    state.second_order_costs_q8[index]
                ),
            )
            for index, observation_id in enumerate(state.observation_ids)
        )
        total_entries += len(entries)
        flags = 0
        if path_id in selected_ids:
            flags |= PATH_FLAG_SELECTED
        if internal_conflicts[identity]:
            flags |= PATH_FLAG_INTERNAL_OWNERSHIP_CONFLICT
        if state.phase_error_count:
            flags |= PATH_FLAG_PHASE_EVIDENCE
        score = max(0, value_score(state), continuity_score(state))
        records.append(PathRecord(
            path_id=path_id,
            entries=entries,
            family_flags=family_members[identity],
            terminal_observation_id=state.observation_ids[-1],
            continuity_score_q8=continuity_score(state),
            potential_node_value_q8=state.potential_node_value_q8,
            uncertainty_leakage_penalty_q8=(
                state.uncertainty_leakage_penalty_q8
            ),
            provisional_program_cost_q8=_path_saturating_sum(
                state.provisional_program_cost_q8,
                path_manifest.death_cost_bits_q8,
                path_manifest,
                saturation_count,
            ),
            selection_score_q8=score,
            phase_error_sum_u64=state.phase_error_sum_u64,
            phase_error_count=state.phase_error_count,
            ownership_conflict_count=internal_conflicts[identity],
            protected_band_id=bands[identity],
            value_rank=value_ranks.get(identity, PATH_RANK_ABSENT),
            continuity_rank=continuity_ranks.get(
                identity,
                PATH_RANK_ABSENT,
            ),
            protected_rank=protected_ranks.get(
                identity,
                PATH_RANK_ABSENT,
            ),
            flags=flags,
        ))
    if total_entries > path_manifest.maximum_total_entries:
        raise OverflowError("R-191 path-entry bound reached")
    managed_bytes = (
        len(records) * ctypes.sizeof(PartialPath)
        + total_entries * ctypes.sizeof(PartialPathEntry)
    )
    if managed_bytes > path_manifest.maximum_managed_bytes:
        raise OverflowError("R-191 host-byte bound reached")

    return PathOracleResult(
        paths=tuple(records),
        selected_path_ids=selected_ids,
        report={
            "schema": "resonith-r191-fixed-path-oracle-1",
            "status": "analyzer paths only; no predictor or byte claim",
            "raw_state_count": raw_state_count,
            "frontier_peak": frontier_peak,
            "work_units": work_units,
            "peak_live_managed_bytes": managed_bytes,
            "path_count": len(records),
            "entry_count": total_entries,
            "selected_candidate_count": len(selection_candidates),
            "selected_path_count": len(selected_ids),
            "internal_conflict_count": sum(internal_conflicts.values()),
            "cross_path_conflict_count": cross_conflict_count,
            "score_saturation_count": saturation_count[0],
            "value_family_count": sum(
                bool(record.family_flags & PATH_FAMILY_LOCAL_POTENTIAL)
                for record in records
            ),
            "continuity_family_count": sum(
                bool(record.family_flags & PATH_FAMILY_CONTINUITY)
                for record in records
            ),
            "protected_family_count": sum(
                bool(record.family_flags & PATH_FAMILY_PROTECTED_WEAK)
                for record in records
            ),
            "solver": solver,
            "predictor_integrated": False,
            "actual_byte_rdo": False,
        },
    )


class NativePartialGraph:
    """Thin bridge to the C++23 CPU oracle; no Python product dependency."""

    def __init__(self, library_path: str | Path):
        self._library = ctypes.CDLL(str(Path(library_path)))
        self._last_path_evidence: dict[str, object] | None = None
        self._function = self._library.resonith_partial_graph_edges_cpu
        self._function.argtypes = [
            ctypes.POINTER(PartialResolution),
            ctypes.c_size_t,
            ctypes.POINTER(PartialObservation),
            ctypes.c_size_t,
            ctypes.POINTER(PartialGraphManifest),
            ctypes.POINTER(PartialEdge),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._function.restype = ctypes.c_int
        self._path_function_v3 = (
            self._library.resonith_partial_graph_paths_cpu_v3
        )
        self._path_function_v3.argtypes = [
            ctypes.POINTER(PartialResolution),
            ctypes.c_size_t,
            ctypes.POINTER(PartialObservation),
            ctypes.c_size_t,
            ctypes.POINTER(PartialEdge),
            ctypes.c_size_t,
            ctypes.POINTER(PartialGraphManifest),
            ctypes.POINTER(PartialPathManifestV3),
            ctypes.POINTER(PartialPathV3),
            ctypes.c_size_t,
            ctypes.POINTER(PartialPathEntryV3),
            ctypes.c_size_t,
            ctypes.POINTER(PartialPathReportV3),
        ]
        self._path_function_v3.restype = ctypes.c_int

    @property
    def last_path_evidence(self) -> dict[str, object]:
        """Return complete logical fields from the latest successful call."""

        if self._last_path_evidence is None:
            raise RuntimeError("no native path evidence is available")
        return self._last_path_evidence

    def edges(
        self,
        resolutions: tuple[PartialResolution, ...],
        observations: tuple[PartialObservation, ...],
        manifest: PartialGraphManifest,
    ) -> tuple[EdgeRecord, ...]:
        resolution_array = (PartialResolution * len(resolutions))(
            *resolutions
        )
        observation_array = (PartialObservation * len(observations))(
            *observations
        )
        required = ctypes.c_size_t()
        status = self._function(
            resolution_array,
            len(resolutions),
            observation_array,
            len(observations),
            ctypes.byref(manifest),
            None,
            0,
            ctypes.byref(required),
        )
        if status != 0:
            raise RuntimeError(f"native edge preflight failed: {status}")
        output = (PartialEdge * required.value)()
        status = self._function(
            resolution_array,
            len(resolutions),
            observation_array,
            len(observations),
            ctypes.byref(manifest),
            output,
            required.value,
            ctypes.byref(required),
        )
        if status != 0:
            raise RuntimeError(f"native edge scoring failed: {status}")
        return tuple(
            EdgeRecord(
                candidate_id=item.candidate_id,
                source_observation_id=item.source_observation_id,
                target_observation_id=item.target_observation_id,
                center_delta_samples=item.center_delta_samples,
                frequency_delta_hz_q20=item.frequency_delta_hz_q20,
                gap_hops=item.gap_hops,
                cycle_offset=item.cycle_offset,
                phase_error_u31=item.phase_error_u31,
                continuity_cost_q8=item.continuity_cost_q8,
                provisional_program_cost_q8=(
                    item.provisional_program_cost_q8
                ),
                flags=item.flags,
            )
            for item in output
        )

    def paths(
        self,
        resolutions: tuple[PartialResolution, ...],
        observations: tuple[PartialObservation, ...],
        edges: tuple[EdgeRecord, ...],
        graph_manifest: PartialGraphManifest,
        path_manifest: PartialPathManifest,
    ) -> PathOracleResult:
        resolution_array = (PartialResolution * len(resolutions))(
            *resolutions
        )
        observation_array = (PartialObservation * len(observations))(
            *observations
        )
        native_edges = []
        for edge in edges:
            value = PartialEdge()
            value.struct_size = ctypes.sizeof(value)
            value.abi_version = ABI_VERSION
            value.candidate_id = edge.candidate_id
            value.source_observation_id = edge.source_observation_id
            value.target_observation_id = edge.target_observation_id
            value.center_delta_samples = edge.center_delta_samples
            value.frequency_delta_hz_q20 = edge.frequency_delta_hz_q20
            value.gap_hops = edge.gap_hops
            value.cycle_offset = edge.cycle_offset
            value.phase_error_u31 = edge.phase_error_u31
            value.continuity_cost_q8 = edge.continuity_cost_q8
            value.provisional_program_cost_q8 = (
                edge.provisional_program_cost_q8
            )
            value.flags = edge.flags
            native_edges.append(value)
        edge_array = (PartialEdge * len(native_edges))(*native_edges)

        preflight_manifest = upgrade_path_manifest_v3(path_manifest)
        preflight_report = PartialPathReportV3()
        preflight_report.struct_size = ctypes.sizeof(preflight_report)
        preflight_report.abi_version = PATH_V3_ABI_VERSION
        status = self._path_function_v3(
            resolution_array,
            len(resolutions),
            observation_array,
            len(observations),
            edge_array,
            len(native_edges),
            ctypes.byref(graph_manifest),
            ctypes.byref(preflight_manifest),
            None,
            0,
            None,
            0,
            ctypes.byref(preflight_report),
        )
        if status != 0:
            raise RuntimeError(f"native path preflight failed: {status}")

        fill_manifest = PartialPathManifestV3.from_buffer_copy(
            bytes(preflight_manifest)
        )
        for index in range(4):
            fill_manifest.expected_input_fingerprint[index] = (
                preflight_report.input_fingerprint[index]
            )
        path_array = (
            PartialPathV3 * preflight_report.required_path_count
        )()
        entry_array = (
            PartialPathEntryV3 * preflight_report.required_entry_count
        )()
        fill_report = PartialPathReportV3()
        fill_report.struct_size = ctypes.sizeof(fill_report)
        fill_report.abi_version = PATH_V3_ABI_VERSION
        status = self._path_function_v3(
            resolution_array,
            len(resolutions),
            observation_array,
            len(observations),
            edge_array,
            len(native_edges),
            ctypes.byref(graph_manifest),
            ctypes.byref(fill_manifest),
            path_array,
            len(path_array),
            entry_array,
            len(entry_array),
            ctypes.byref(fill_report),
        )
        if status != 0:
            raise RuntimeError(f"native path fill failed: {status}")
        if (
            tuple(preflight_report.input_fingerprint)
            != tuple(fill_report.input_fingerprint)
            or preflight_report.required_path_count
            != fill_report.required_path_count
            or preflight_report.required_entry_count
            != fill_report.required_entry_count
            or fill_report.required_path_count
            != fill_report.written_path_count
            or fill_report.required_entry_count
            != fill_report.written_entry_count
            or sum(preflight_report.work_event_counts)
            != preflight_report.work_units
            or sum(fill_report.work_event_counts)
            != fill_report.work_units
            or preflight_report.reserved_device_bytes
            or preflight_report.committed_device_bytes
            or preflight_report.peak_live_device_bytes
            or fill_report.reserved_device_bytes
            or fill_report.committed_device_bytes
            or fill_report.peak_live_device_bytes
        ):
            raise RuntimeError(
                "native path preflight/fill typed evidence mismatch"
            )
        if (
            tuple(preflight_report.output_fingerprint)
            != tuple(fill_report.output_fingerprint)
        ):
            raise RuntimeError(
                "native path preflight/fill output fingerprint mismatch"
            )

        def logical_fields(value: object) -> object:
            if isinstance(value, ctypes.Array):
                return [logical_fields(item) for item in value]
            if isinstance(value, ctypes.Structure):
                return {
                    name: logical_fields(getattr(value, name))
                    for name, *_ in value._fields_
                }
            return value

        path_bytes = bytes(path_array)
        entry_bytes = bytes(entry_array)
        case_payload = b"".join(
            (
                bytes(preflight_manifest),
                bytes(fill_manifest),
                path_bytes,
                entry_bytes,
                bytes(preflight_report),
                bytes(fill_report),
            )
        )
        self._last_path_evidence = {
            "preflight_manifest": logical_fields(preflight_manifest),
            "fill_manifest": logical_fields(fill_manifest),
            "preflight_report": logical_fields(preflight_report),
            "fill_report": logical_fields(fill_report),
            "paths": logical_fields(path_array),
            "entries": logical_fields(entry_array),
            "path_payload_sha256": hashlib.sha256(path_bytes).hexdigest(),
            "entry_payload_sha256": hashlib.sha256(entry_bytes).hexdigest(),
            "case_payload_sha256": hashlib.sha256(
                case_payload
            ).hexdigest(),
            "path_payload_bytes": len(path_bytes),
            "entry_payload_bytes": len(entry_bytes),
        }

        records = []
        selected = []
        for item in path_array:
            entries = tuple(
                PathEntryRecord(
                    observation_id=entry.observation_id,
                    incoming_edge_candidate_id=(
                        entry.incoming_edge_candidate_id
                    ),
                    ownership_component=entry.ownership_component,
                    second_order_cost_q8=entry.second_order_cost_q8,
                    flags=entry.flags,
                )
                for entry in entry_array[
                    item.entry_offset
                    : item.entry_offset + item.entry_count
                ]
            )
            records.append(PathRecord(
                path_id=item.path_id,
                entries=entries,
                family_flags=item.family_flags,
                terminal_observation_id=item.terminal_observation_id,
                continuity_score_q8=item.continuity_score_q8,
                potential_node_value_q8=item.potential_node_value_q8,
                uncertainty_leakage_penalty_q8=(
                    item.uncertainty_leakage_penalty_q8
                ),
                provisional_program_cost_q8=(
                    item.provisional_program_cost_q8
                ),
                selection_score_q8=item.selection_score_q8,
                phase_error_sum_u64=item.phase_error_sum_u64,
                phase_error_count=item.phase_error_count,
                ownership_conflict_count=item.ownership_conflict_count,
                protected_band_id=item.protected_band_id,
                value_rank=item.value_rank,
                continuity_rank=item.continuity_rank,
                protected_rank=item.protected_rank,
                flags=item.flags,
            ))
            if item.flags & PATH_FLAG_SELECTED:
                selected.append(item.path_id)
        solver = (
            "exact-small-disjoint-heuristic"
            if fill_report.solver == 0
            else "deterministic-bounded-disjoint-heuristic"
        )
        return PathOracleResult(
            paths=tuple(records),
            selected_path_ids=tuple(selected),
            report={
                "schema": "resonith-r197-native-path-v3-1",
                "raw_state_count": fill_report.raw_state_count,
                "frontier_peak": fill_report.frontier_peak,
                "work_units": fill_report.work_units,
                "peak_live_managed_bytes": fill_report.peak_live_host_bytes,
                "legacy_peak_live_managed_bytes": (
                    fill_report.peak_live_managed_bytes
                ),
                "path_count": fill_report.written_path_count,
                "entry_count": fill_report.written_entry_count,
                "selected_candidate_count": (
                    fill_report.selected_candidate_count
                ),
                "selected_path_count": fill_report.selected_path_count,
                "internal_conflict_count": (
                    fill_report.internal_conflict_count
                ),
                "cross_path_conflict_count": (
                    fill_report.cross_path_conflict_count
                ),
                "score_saturation_count": (
                    fill_report.score_saturation_count
                ),
                "value_family_count": fill_report.value_family_count,
                "continuity_family_count": (
                    fill_report.continuity_family_count
                ),
                "protected_family_count": (
                    fill_report.protected_family_count
                ),
                "duplicate_state_count": (
                    fill_report.duplicate_state_count
                ),
                "terminal_retained_state_count": (
                    fill_report.terminal_retained_state_count
                ),
                "state_k_discarded_count": (
                    fill_report.state_k_discarded_count
                ),
                "state_arena_peak": fill_report.state_arena_peak,
                "value_family_presented_count": (
                    fill_report.value_family_presented_count
                ),
                "continuity_family_presented_count": (
                    fill_report.continuity_family_presented_count
                ),
                "protected_family_presented_count": (
                    fill_report.protected_family_presented_count
                ),
                "value_family_discarded_count": (
                    fill_report.value_family_discarded_count
                ),
                "continuity_family_discarded_count": (
                    fill_report.continuity_family_discarded_count
                ),
                "protected_family_discarded_count": (
                    fill_report.protected_family_discarded_count
                ),
                "output_deduplicated_count": (
                    fill_report.output_deduplicated_count
                ),
                "bound_rejected_count": fill_report.bound_rejected_count,
                "work_event_counts": tuple(fill_report.work_event_counts),
                "reserved_host_bytes": fill_report.reserved_host_bytes,
                "committed_host_bytes": fill_report.committed_host_bytes,
                "peak_live_host_bytes": fill_report.peak_live_host_bytes,
                "reserved_device_bytes": fill_report.reserved_device_bytes,
                "committed_device_bytes": fill_report.committed_device_bytes,
                "peak_live_device_bytes": fill_report.peak_live_device_bytes,
                "input_fingerprint": tuple(
                    fill_report.input_fingerprint
                ),
                "output_fingerprint": tuple(
                    fill_report.output_fingerprint
                ),
                "flags": fill_report.flags,
                "solver": solver,
                "predictor_integrated": False,
                "actual_byte_rdo": False,
            },
        )
