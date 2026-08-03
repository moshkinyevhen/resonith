#ifndef RESONITH_PARTIAL_GRAPH_H
#define RESONITH_PARTIAL_GRAPH_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_PARTIAL_GRAPH_ABI_VERSION = 1U,
    RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS = 8U,
    RESONITH_PARTIAL_GRAPH_MAX_GAPS = 8U,
    RESONITH_PARTIAL_GRAPH_MAX_CYCLE_OFFSETS = 9U,
    RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE = 1U,
    RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE = 2U,
    RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK = 4U,
    RESONITH_PARTIAL_PATH_ABI_VERSION = 2U,
    RESONITH_PARTIAL_PATH_V3_ABI_VERSION = 3U,
    RESONITH_PARTIAL_PATH_WORK_LEDGER_VERSION = 1U,
    RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT = 22U,
    RESONITH_PARTIAL_PATH_MAX_PROTECTED_BANDS = 128U,
    RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL = 1U,
    RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY = 2U,
    RESONITH_PARTIAL_PATH_FAMILY_PROTECTED_WEAK = 4U,
    RESONITH_PARTIAL_PATH_SELECTED = 1U,
    RESONITH_PARTIAL_PATH_INTERNAL_OWNERSHIP_CONFLICT = 2U,
    RESONITH_PARTIAL_PATH_PHASE_EVIDENCE = 4U,
    RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT = 1U,
    RESONITH_PARTIAL_PATH_REPORT_PRUNED = 2U,
    RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS = 1048576U,
    RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS = 4194304U,
    RESONITH_PARTIAL_PATH_MAX_OBSERVATIONS = 1048576U,
    RESONITH_PARTIAL_PATH_MAX_RECORDS = 65536U,
    RESONITH_PARTIAL_PATH_MAX_ENTRIES = 4194304U,
    RESONITH_PARTIAL_PATH_MAX_FRONTIER_STATES = 1048576U,
    RESONITH_PARTIAL_PATH_MAX_STATE_RECORDS = 4194304U,
    RESONITH_PARTIAL_PATH_MAX_EXACT_SET_CANDIDATES = 24U,
    RESONITH_PARTIAL_CUDA_MAX_BLOCKS = 65535U,
    RESONITH_PARTIAL_CUDA_MAX_THREADS = 1024U
};

#define RESONITH_PARTIAL_MAX_WORK_EVENTS UINT64_C(281474976710655)
#define RESONITH_PARTIAL_MAX_HOST_BYTES UINT64_C(8589934592)
#define RESONITH_PARTIAL_MAX_DEVICE_BYTES UINT64_C(4294967296)

#define RESONITH_PARTIAL_AMBIGUITY_NONE UINT32_MAX
#define RESONITH_PARTIAL_PATH_RANK_ABSENT UINT32_MAX

typedef enum resonith_partial_path_termination {
    RESONITH_PARTIAL_PATH_TERMINATION_COMPLETE = 0,
    RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND = 1,
    RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT = 2,
    RESONITH_PARTIAL_PATH_TERMINATION_OUTPUT_TOO_SMALL = 3,
    RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM = 4,
    RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED = 5
} resonith_partial_path_termination;

typedef enum resonith_partial_path_solver {
    RESONITH_PARTIAL_PATH_SOLVER_EXACT_SMALL = 0,
    RESONITH_PARTIAL_PATH_SOLVER_BOUNDED_GREEDY = 1
} resonith_partial_path_solver;

typedef enum resonith_partial_path_work_event {
    RESONITH_PARTIAL_WORK_VALIDATE_RECORD = 0,
    RESONITH_PARTIAL_WORK_SNAPSHOT_BYTE = 1,
    RESONITH_PARTIAL_WORK_RADIX_BUCKET = 2,
    RESONITH_PARTIAL_WORK_RADIX_CLASSIFY = 3,
    RESONITH_PARTIAL_WORK_RADIX_SCATTER = 4,
    RESONITH_PARTIAL_WORK_MERGE_COMPARE = 5,
    RESONITH_PARTIAL_WORK_MERGE_MOVE = 6,
    RESONITH_PARTIAL_WORK_GRAPH_SOURCE = 7,
    RESONITH_PARTIAL_WORK_GRAPH_GAP = 8,
    RESONITH_PARTIAL_WORK_GRAPH_TARGET = 9,
    RESONITH_PARTIAL_WORK_GRAPH_CYCLE = 10,
    RESONITH_PARTIAL_WORK_EDGE_FIELD = 11,
    RESONITH_PARTIAL_WORK_LOOKUP = 12,
    RESONITH_PARTIAL_WORK_STATE = 13,
    RESONITH_PARTIAL_WORK_REFERENCE = 14,
    RESONITH_PARTIAL_WORK_SELECT = 15,
    RESONITH_PARTIAL_WORK_RECONSTRUCT = 16,
    RESONITH_PARTIAL_WORK_MEMORY_PAGE = 17,
    RESONITH_PARTIAL_WORK_STAGE_RECORD = 18,
    RESONITH_PARTIAL_WORK_COMMIT_RECORD = 19,
    RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE = 20,
    RESONITH_PARTIAL_WORK_CUDA_ITEM = 21
} resonith_partial_path_work_event;

/*
 * R-190 records are a versioned in-memory C ABI, not serialized Resonith
 * syntax. Packing plus reserved-zero fields makes hashes and cross-toolchain
 * fixtures independent of implicit padding.
 */
#pragma pack(push, 1)

typedef struct resonith_partial_resolution {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t resolution_id;
    uint32_t fft_samples;
    uint32_t hop_samples;
    uint32_t reserved[3];
} resonith_partial_resolution;

typedef struct resonith_partial_graph_manifest {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t sample_rate;
    uint32_t resolution_count;
    uint32_t gap_count;
    uint32_t neighbors_per_gap;
    uint32_t cycle_offset_count;
    uint32_t minimum_track_observations;
    int64_t maximum_frequency_jump_hz_q20;
    int64_t maximum_frequency_slope_hz_per_sample_q20;
    int32_t continuation_base_bits_q8;
    int32_t continuation_reward_q8;
    int64_t score_saturation;
    uint64_t maximum_edge_records;
    uint32_t maximum_path_hypotheses;
    uint32_t exact_set_candidate_limit;
    uint32_t gaps[RESONITH_PARTIAL_GRAPH_MAX_GAPS];
    int32_t cycle_offsets[RESONITH_PARTIAL_GRAPH_MAX_CYCLE_OFFSETS];
    uint32_t reserved[8];
} resonith_partial_graph_manifest;

typedef struct resonith_partial_observation {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t observation_id;
    uint64_t center_sample;
    int64_t frequency_hz_q20;
    uint64_t frequency_uncertainty_hz_q20;
    uint32_t phase_turn_u32;
    uint32_t phase_step_u32;
    uint32_t normalized_amplitude_q16;
    uint32_t amplitude_uncertainty_q16;
    uint32_t phase_uncertainty_u31;
    uint32_t frame_index;
    uint32_t resolution_id;
    int32_t detector_id;
    uint32_t band_id;
    uint32_t ownership_component;
    uint32_t ambiguity_component;
    uint32_t flags;
    int32_t protected_rank_q8;
    int32_t neighbor_priority_q8;
    int32_t potential_node_value_q8;
    int32_t uncertainty_leakage_penalty_q8;
    uint32_t reserved[6];
} resonith_partial_observation;

typedef struct resonith_partial_edge {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t candidate_id;
    uint64_t source_observation_id;
    uint64_t target_observation_id;
    uint64_t center_delta_samples;
    int64_t frequency_delta_hz_q20;
    uint32_t gap_hops;
    int32_t cycle_offset;
    uint32_t phase_error_u31;
    int32_t continuity_cost_q8;
    int32_t provisional_program_cost_q8;
    uint32_t flags;
    uint32_t reserved[2];
} resonith_partial_edge;

typedef struct resonith_partial_path_manifest {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t second_order_law_version;
    uint32_t protected_band_count;
    uint32_t k_value_per_state;
    uint32_t k_continuity_per_state;
    uint32_t top_k_value;
    uint32_t top_k_continuity;
    uint32_t top_k_protected;
    uint32_t protected_paths_per_band;
    uint32_t minimum_path_observations;
    uint32_t maximum_path_observations;
    uint32_t exact_set_candidate_limit;
    uint32_t amplitude_floor_q16;
    uint32_t amplitude_residual_weight_q8;
    uint32_t reserved_alignment;
    uint64_t frequency_sigma_floor_hz_q20;
    int64_t birth_cost_bits_q8;
    int64_t death_cost_bits_q8;
    int64_t score_saturation;
    uint64_t maximum_path_records;
    uint64_t maximum_total_entries;
    uint64_t maximum_frontier_states;
    uint64_t maximum_state_records;
    uint64_t maximum_work_units;
    uint64_t maximum_managed_bytes;
    uint64_t expected_input_fingerprint[4];
    int64_t protected_band_upper_hz_q20[
        RESONITH_PARTIAL_PATH_MAX_PROTECTED_BANDS - 1U
    ];
    uint32_t reserved[8];
} resonith_partial_path_manifest;

typedef struct resonith_partial_path {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t path_id;
    uint64_t entry_offset;
    uint32_t entry_count;
    uint32_t family_flags;
    uint64_t terminal_observation_id;
    int64_t continuity_score_q8;
    int64_t potential_node_value_q8;
    int64_t uncertainty_leakage_penalty_q8;
    int64_t provisional_program_cost_q8;
    int64_t selection_score_q8;
    uint64_t phase_error_sum_u64;
    uint32_t phase_error_count;
    uint32_t ownership_conflict_count;
    uint32_t protected_band_id;
    uint32_t value_rank;
    uint32_t continuity_rank;
    uint32_t protected_rank;
    uint32_t flags;
    uint32_t reserved[5];
} resonith_partial_path;

typedef struct resonith_partial_path_entry {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t observation_id;
    uint64_t incoming_edge_candidate_id;
    uint32_t ownership_component;
    int32_t second_order_cost_q8;
    uint32_t flags;
    uint32_t reserved[3];
} resonith_partial_path_entry;

typedef struct resonith_partial_path_report {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t termination;
    uint32_t solver;
    uint64_t required_path_count;
    uint64_t required_entry_count;
    uint64_t written_path_count;
    uint64_t written_entry_count;
    uint64_t raw_state_count;
    uint64_t frontier_peak;
    uint64_t work_units;
    uint64_t peak_live_managed_bytes;
    uint64_t selected_candidate_count;
    uint64_t selected_path_count;
    uint64_t internal_conflict_count;
    uint64_t cross_path_conflict_count;
    uint64_t score_saturation_count;
    uint64_t value_family_count;
    uint64_t continuity_family_count;
    uint64_t protected_family_count;
    uint64_t duplicate_state_count;
    uint64_t terminal_retained_state_count;
    uint64_t state_k_discarded_count;
    uint64_t state_arena_peak;
    uint64_t value_family_presented_count;
    uint64_t continuity_family_presented_count;
    uint64_t protected_family_presented_count;
    uint64_t value_family_discarded_count;
    uint64_t continuity_family_discarded_count;
    uint64_t protected_family_discarded_count;
    uint64_t output_deduplicated_count;
    uint64_t bound_rejected_count;
    uint64_t input_fingerprint[4];
    uint64_t output_fingerprint[4];
    uint32_t flags;
    uint32_t reserved[7];
} resonith_partial_path_report;

/*
 * R-197 path ABI v3 is the transactional, resource-accounted successor to
 * the quarantined v2 analyzer ABI. These are in-memory analysis records, not
 * serialized Resonith bitstream syntax.
 */
typedef struct resonith_partial_path_manifest_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t second_order_law_version;
    uint32_t protected_band_count;
    uint32_t k_value_per_state;
    uint32_t k_continuity_per_state;
    uint32_t top_k_value;
    uint32_t top_k_continuity;
    uint32_t top_k_protected;
    uint32_t protected_paths_per_band;
    uint32_t minimum_path_observations;
    uint32_t maximum_path_observations;
    uint32_t exact_set_candidate_limit;
    uint32_t amplitude_floor_q16;
    uint32_t amplitude_residual_weight_q8;
    uint32_t work_ledger_version;
    uint64_t frequency_sigma_floor_hz_q20;
    int64_t birth_cost_bits_q8;
    int64_t death_cost_bits_q8;
    int64_t score_saturation;
    uint64_t maximum_path_records;
    uint64_t maximum_total_entries;
    uint64_t maximum_frontier_states;
    uint64_t maximum_state_records;
    uint64_t maximum_work_units;
    uint64_t maximum_managed_bytes;
    uint64_t maximum_device_bytes;
    uint64_t expected_input_fingerprint[4];
    int64_t protected_band_upper_hz_q20[
        RESONITH_PARTIAL_PATH_MAX_PROTECTED_BANDS - 1U
    ];
    uint32_t reserved[8];
} resonith_partial_path_manifest_v3;

typedef struct resonith_partial_path_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t path_id;
    uint64_t entry_offset;
    uint32_t entry_count;
    uint32_t family_flags;
    uint64_t terminal_observation_id;
    int64_t continuity_score_q8;
    int64_t potential_node_value_q8;
    int64_t uncertainty_leakage_penalty_q8;
    int64_t provisional_program_cost_q8;
    int64_t selection_score_q8;
    uint64_t phase_error_sum_u64;
    uint32_t phase_error_count;
    uint32_t ownership_conflict_count;
    uint32_t protected_band_id;
    uint32_t value_rank;
    uint32_t continuity_rank;
    uint32_t protected_rank;
    uint32_t flags;
    uint32_t reserved[5];
} resonith_partial_path_v3;

typedef struct resonith_partial_path_entry_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t observation_id;
    uint64_t incoming_edge_candidate_id;
    uint32_t ownership_component;
    int32_t second_order_cost_q8;
    uint32_t flags;
    uint32_t reserved[3];
} resonith_partial_path_entry_v3;

typedef struct resonith_partial_path_report_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t termination;
    uint32_t solver;
    uint64_t required_path_count;
    uint64_t required_entry_count;
    uint64_t written_path_count;
    uint64_t written_entry_count;
    uint64_t raw_state_count;
    uint64_t frontier_peak;
    uint64_t work_units;
    uint64_t peak_live_managed_bytes;
    uint64_t selected_candidate_count;
    uint64_t selected_path_count;
    uint64_t internal_conflict_count;
    uint64_t cross_path_conflict_count;
    uint64_t score_saturation_count;
    uint64_t value_family_count;
    uint64_t continuity_family_count;
    uint64_t protected_family_count;
    uint64_t duplicate_state_count;
    uint64_t terminal_retained_state_count;
    uint64_t state_k_discarded_count;
    uint64_t state_arena_peak;
    uint64_t value_family_presented_count;
    uint64_t continuity_family_presented_count;
    uint64_t protected_family_presented_count;
    uint64_t value_family_discarded_count;
    uint64_t continuity_family_discarded_count;
    uint64_t protected_family_discarded_count;
    uint64_t output_deduplicated_count;
    uint64_t bound_rejected_count;
    uint64_t input_fingerprint[4];
    uint64_t output_fingerprint[4];
    uint64_t work_event_counts[RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT];
    /*
     * Per-call high-water provenance. Reserved counts profile-admitted
     * outstanding bytes before the upstream outcome; committed counts bytes
     * backed by successful upstream allocations; peak-live counts bytes made
     * available to the analyzer. Therefore reserved >= committed >=
     * peak-live. The CPU implementation reports all device fields as zero.
     */
    uint64_t reserved_host_bytes;
    uint64_t committed_host_bytes;
    uint64_t peak_live_host_bytes;
    uint64_t reserved_device_bytes;
    uint64_t committed_device_bytes;
    uint64_t peak_live_device_bytes;
    uint32_t flags;
    uint32_t reserved[7];
} resonith_partial_path_report_v3;

#pragma pack(pop)

/*
 * A negative-bound typedef is intentionally used instead of C11
 * _Static_assert. It keeps every public offset guard active in C89/C11,
 * MSVC C, C++23, and embedded toolchains that do not define
 * __STDC_VERSION__ consistently.
 */
#define RESONITH_PARTIAL_OFFSET_ASSERT(type, field, expected)              \
    typedef char resonith_offset_guard_##type##_##field[                   \
        offsetof(type, field) == (expected) ? 1 : -1                       \
    ]

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, second_order_law_version, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, protected_band_count, 12U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, k_value_per_state, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, k_continuity_per_state, 20U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, top_k_value, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, top_k_continuity, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, top_k_protected, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, protected_paths_per_band, 36U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, minimum_path_observations, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_path_observations, 44U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, exact_set_candidate_limit, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, amplitude_floor_q16, 52U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, amplitude_residual_weight_q8, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, reserved_alignment, 60U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, frequency_sigma_floor_hz_q20, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, birth_cost_bits_q8, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, death_cost_bits_q8, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, score_saturation, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_path_records, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_total_entries, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_frontier_states, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_state_records, 120U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_work_units, 128U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, maximum_managed_bytes, 136U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, expected_input_fingerprint, 144U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, protected_band_upper_hz_q20, 176U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest, reserved, 1192U);

RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, path_id, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, entry_offset, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, entry_count, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, family_flags, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, terminal_observation_id, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, continuity_score_q8, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, potential_node_value_q8, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, uncertainty_leakage_penalty_q8, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, provisional_program_cost_q8, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, selection_score_q8, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, phase_error_sum_u64, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, phase_error_count, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, ownership_conflict_count, 92U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, protected_band_id, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, value_rank, 100U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, continuity_rank, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path, protected_rank, 108U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, flags, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(resonith_partial_path, reserved, 116U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, observation_id, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, incoming_edge_candidate_id, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, ownership_component, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, second_order_cost_q8, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, flags, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry, reserved, 36U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, termination, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, solver, 12U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, required_path_count, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, required_entry_count, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, written_path_count, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, written_entry_count, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, raw_state_count, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, frontier_peak, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, work_units, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, peak_live_managed_bytes, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, selected_candidate_count, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, selected_path_count, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, internal_conflict_count, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, cross_path_conflict_count, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, score_saturation_count, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, value_family_count, 120U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, continuity_family_count, 128U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, protected_family_count, 136U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, duplicate_state_count, 144U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, terminal_retained_state_count, 152U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, state_k_discarded_count, 160U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, state_arena_peak, 168U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, value_family_presented_count, 176U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, continuity_family_presented_count, 184U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, protected_family_presented_count, 192U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, value_family_discarded_count, 200U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, continuity_family_discarded_count, 208U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, protected_family_discarded_count, 216U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, output_deduplicated_count, 224U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, bound_rejected_count, 232U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, input_fingerprint, 240U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, output_fingerprint, 272U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, flags, 304U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report, reserved, 308U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, second_order_law_version, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, protected_band_count, 12U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, k_value_per_state, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, k_continuity_per_state, 20U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, top_k_value, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, top_k_continuity, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, top_k_protected, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, protected_paths_per_band, 36U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, minimum_path_observations, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_path_observations, 44U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, exact_set_candidate_limit, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, amplitude_floor_q16, 52U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, amplitude_residual_weight_q8, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, work_ledger_version, 60U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, frequency_sigma_floor_hz_q20, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, birth_cost_bits_q8, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, death_cost_bits_q8, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, score_saturation, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_path_records, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_total_entries, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_frontier_states, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_state_records, 120U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_work_units, 128U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_managed_bytes, 136U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, maximum_device_bytes, 144U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, expected_input_fingerprint, 152U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, protected_band_upper_hz_q20, 184U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_manifest_v3, reserved, 1200U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, path_id, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, entry_offset, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, entry_count, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, family_flags, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, terminal_observation_id, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, continuity_score_q8, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, potential_node_value_q8, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, uncertainty_leakage_penalty_q8, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, provisional_program_cost_q8, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, selection_score_q8, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, phase_error_sum_u64, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, phase_error_count, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, ownership_conflict_count, 92U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, protected_band_id, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, value_rank, 100U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, continuity_rank, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, protected_rank, 108U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, flags, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_v3, reserved, 116U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, observation_id, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, incoming_edge_candidate_id, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, ownership_component, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, second_order_cost_q8, 28U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, flags, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_entry_v3, reserved, 36U);

RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, struct_size, 0U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, abi_version, 4U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, termination, 8U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, solver, 12U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, required_path_count, 16U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, required_entry_count, 24U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, written_path_count, 32U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, written_entry_count, 40U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, raw_state_count, 48U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, frontier_peak, 56U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, work_units, 64U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, peak_live_managed_bytes, 72U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, selected_candidate_count, 80U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, selected_path_count, 88U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, internal_conflict_count, 96U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, cross_path_conflict_count, 104U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, score_saturation_count, 112U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, value_family_count, 120U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, continuity_family_count, 128U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, protected_family_count, 136U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, duplicate_state_count, 144U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, terminal_retained_state_count, 152U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, state_k_discarded_count, 160U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, state_arena_peak, 168U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, value_family_presented_count, 176U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3,
    continuity_family_presented_count,
    184U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, protected_family_presented_count, 192U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, value_family_discarded_count, 200U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3,
    continuity_family_discarded_count,
    208U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, protected_family_discarded_count, 216U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, output_deduplicated_count, 224U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, bound_rejected_count, 232U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, input_fingerprint, 240U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, output_fingerprint, 272U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, work_event_counts, 304U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, reserved_host_bytes, 480U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, committed_host_bytes, 488U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, peak_live_host_bytes, 496U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, reserved_device_bytes, 504U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, committed_device_bytes, 512U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, peak_live_device_bytes, 520U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, flags, 528U);
RESONITH_PARTIAL_OFFSET_ASSERT(
    resonith_partial_path_report_v3, reserved, 532U);

#undef RESONITH_PARTIAL_OFFSET_ASSERT

/*
 * Enumerates and scores the complete declared first-order edge/cycle union.
 * Passing `output == NULL` with zero capacity performs preflight and returns
 * the required record count. Output order is canonical candidate-ID order.
 */
RESONITH_API resonith_status resonith_partial_graph_edges_cpu(
    const resonith_partial_resolution* resolutions,
    size_t resolution_count,
    const resonith_partial_observation* observations,
    size_t observation_count,
    const resonith_partial_graph_manifest* manifest,
    resonith_partial_edge* output,
    size_t output_capacity,
    size_t* output_count
);

/*
 * Retained R-191 v2 migration symbol. It always returns
 * RESONITH_STATUS_UNSUPPORTED_VERSION and never reads or writes caller
 * payload/report storage. Use resonith_partial_graph_paths_cpu_v3().
 */
RESONITH_API resonith_status resonith_partial_graph_paths_cpu_v2(
    const resonith_partial_resolution* resolutions,
    size_t resolution_count,
    const resonith_partial_observation* observations,
    size_t observation_count,
    const resonith_partial_edge* edges,
    size_t edge_count,
    const resonith_partial_graph_manifest* graph_manifest,
    const resonith_partial_path_manifest* path_manifest,
    resonith_partial_path* paths,
    size_t path_capacity,
    resonith_partial_path_entry* entries,
    size_t entry_capacity,
    resonith_partial_path_report* report
);

/*
 * Builds the transactional R-197 v3 path union. No path or entry byte is
 * published until complete validation, bounded staging, and commit reservation
 * succeed. Preflight passes null path/entry pointers and zero capacities.
 */
RESONITH_API resonith_status resonith_partial_graph_paths_cpu_v3(
    const resonith_partial_resolution* resolutions,
    size_t resolution_count,
    const resonith_partial_observation* observations,
    size_t observation_count,
    const resonith_partial_edge* edges,
    size_t edge_count,
    const resonith_partial_graph_manifest* graph_manifest,
    const resonith_partial_path_manifest_v3* path_manifest,
    resonith_partial_path_v3* paths,
    size_t path_capacity,
    resonith_partial_path_entry_v3* entries,
    size_t entry_capacity,
    resonith_partial_path_report_v3* report
);

#ifdef __cplusplus
}

static_assert(sizeof(resonith_partial_resolution) == 32U);
static_assert(sizeof(resonith_partial_graph_manifest) == 180U);
static_assert(sizeof(resonith_partial_observation) == 128U);
static_assert(sizeof(resonith_partial_edge) == 80U);
static_assert(sizeof(resonith_partial_path_manifest) == 1224U);
static_assert(sizeof(resonith_partial_path) == 136U);
static_assert(sizeof(resonith_partial_path_entry) == 48U);
static_assert(sizeof(resonith_partial_path_report) == 336U);
static_assert(sizeof(resonith_partial_path_manifest_v3) == 1232U);
static_assert(sizeof(resonith_partial_path_v3) == 136U);
static_assert(sizeof(resonith_partial_path_entry_v3) == 48U);
static_assert(sizeof(resonith_partial_path_report_v3) == 560U);
#endif

#endif
