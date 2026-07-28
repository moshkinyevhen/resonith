#include "resonith/partial_graph.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <vector>

namespace resonith::internal {
bool partial_graph_environmental_oom_probe() noexcept;
}

namespace {

void fail(const char* message) {
    std::fprintf(stderr, "partial_graph_test: %s\n", message);
    std::exit(1);
}

resonith_partial_observation observation(
    std::uint64_t id,
    std::uint32_t frame,
    std::int64_t frequency_q20,
    std::uint32_t phase,
    std::uint32_t step,
    std::uint32_t amplitude_q16,
    std::uint32_t ownership
) {
    resonith_partial_observation value{};
    value.struct_size = sizeof(value);
    value.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
    value.observation_id = id;
    value.center_sample = static_cast<std::uint64_t>(frame) * 128U;
    value.frequency_hz_q20 = frequency_q20;
    value.frequency_uncertainty_hz_q20 = 1U << 20U;
    value.phase_turn_u32 = phase;
    value.phase_step_u32 = step;
    value.normalized_amplitude_q16 = amplitude_q16;
    value.amplitude_uncertainty_q16 = 1U << 12U;
    value.phase_uncertainty_u31 = 1U << 20U;
    value.frame_index = frame;
    value.resolution_id = 7U;
    value.detector_id = -1;
    value.band_id = 3U;
    value.ownership_component = ownership;
    value.ambiguity_component = RESONITH_PARTIAL_AMBIGUITY_NONE;
    value.flags = RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
        | RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE;
    value.protected_rank_q8 = 256;
    value.neighbor_priority_q8 = 512;
    value.potential_node_value_q8 = 1024;
    value.uncertainty_leakage_penalty_q8 = 64;
    return value;
}

}  // namespace

int main() {
    if (!resonith::internal::partial_graph_environmental_oom_probe()) {
        fail("environmental allocation failure was not distinguished");
    }
    const resonith_partial_resolution resolution{
        sizeof(resonith_partial_resolution),
        RESONITH_PARTIAL_GRAPH_ABI_VERSION,
        7U,
        1024U,
        128U,
        {0U, 0U, 0U},
    };
    resonith_partial_graph_manifest manifest{};
    manifest.struct_size = sizeof(manifest);
    manifest.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
    manifest.sample_rate = 8000U;
    manifest.resolution_count = 1U;
    manifest.gap_count = 2U;
    manifest.neighbors_per_gap = 2U;
    manifest.cycle_offset_count = 3U;
    manifest.minimum_track_observations = 4U;
    manifest.maximum_frequency_jump_hz_q20 = 80LL << 20U;
    manifest.maximum_frequency_slope_hz_per_sample_q20 = 1LL << 16U;
    manifest.continuation_base_bits_q8 = 12 * 256;
    manifest.continuation_reward_q8 = 12 * 256;
    manifest.score_saturation = (1LL << 31U) - 1LL;
    manifest.maximum_edge_records = 1024U;
    manifest.maximum_path_hypotheses = 128U;
    manifest.exact_set_candidate_limit = 20U;
    manifest.gaps[0] = 1U;
    manifest.gaps[1] = 2U;
    manifest.cycle_offsets[0] = -1;
    manifest.cycle_offsets[1] = 0;
    manifest.cycle_offsets[2] = 1;

    const std::uint32_t step_440 = static_cast<std::uint32_t>(
        (440ULL << 32U) / manifest.sample_rate
    );
    const std::uint32_t step_442 = static_cast<std::uint32_t>(
        (442ULL << 32U) / manifest.sample_rate
    );
    std::array<resonith_partial_observation, 5> observations{
        observation(
            10U,
            0U,
            440LL << 20U,
            0x10000000U,
            step_440,
            12000U << 16U,
            0U
        ),
        observation(
            11U,
            1U,
            441LL << 20U,
            0x1ccccccdU,
            step_440,
            11800U << 16U,
            1U
        ),
        observation(
            12U,
            1U,
            900LL << 20U,
            0x20000000U,
            0x1ccccccdU,
            4000U << 16U,
            2U
        ),
        observation(
            13U,
            2U,
            442LL << 20U,
            0x2999999aU,
            step_442,
            11600U << 16U,
            3U
        ),
        observation(
            14U,
            2U,
            1500LL << 20U,
            0x30000000U,
            0x4ccccccdU,
            2000U << 16U,
            4U
        ),
    };

    std::size_t required = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &manifest,
            nullptr,
            0U,
            &required
        ) != RESONITH_STATUS_OK
        || required != 9U
    ) {
        fail("unexpected canonical edge cardinality");
    }
    std::vector<resonith_partial_edge> edge_canary(required);
    std::memset(
        edge_canary.data(),
        0xa5,
        edge_canary.size() * sizeof(resonith_partial_edge)
    );
    const auto edge_canary_before = edge_canary;
    std::size_t rejected_edge_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &manifest,
            edge_canary.data(),
            required - 1U,
            &rejected_edge_count
        ) != RESONITH_STATUS_OUTPUT_TOO_SMALL
        || rejected_edge_count != required
        || std::memcmp(
            edge_canary.data(),
            edge_canary_before.data(),
            edge_canary.size() * sizeof(resonith_partial_edge)
        ) != 0
    ) {
        fail("R-190 capacity failure partially wrote semantic output");
    }
    resonith_partial_graph_manifest oversized_manifest = manifest;
    oversized_manifest.maximum_edge_records =
        std::numeric_limits<std::uint64_t>::max();
    rejected_edge_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &oversized_manifest,
            edge_canary.data(),
            edge_canary.size(),
            &rejected_edge_count
        ) != RESONITH_STATUS_PROFILE_BOUND
        || std::memcmp(
            edge_canary.data(),
            edge_canary_before.data(),
            edge_canary.size() * sizeof(resonith_partial_edge)
        ) != 0
    ) {
        fail("R-190 managed-byte overflow was not rejected transactionally");
    }
    std::vector<resonith_partial_edge> first(required);
    std::vector<resonith_partial_edge> second(required);
    std::size_t first_count = 0U;
    std::size_t second_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &manifest,
            first.data(),
            first.size(),
            &first_count
        ) != RESONITH_STATUS_OK
        || resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &manifest,
            second.data(),
            second.size(),
            &second_count
        ) != RESONITH_STATUS_OK
        || first_count != required
        || second_count != required
    ) {
        fail("native edge scoring failed");
    }
    for (std::size_t index = 0U; index < required; ++index) {
        const resonith_partial_edge& left = first[index];
        const resonith_partial_edge& right = second[index];
        if (
            left.candidate_id != index
            || left.candidate_id != right.candidate_id
            || left.source_observation_id != right.source_observation_id
            || left.target_observation_id != right.target_observation_id
            || left.continuity_cost_q8 != right.continuity_cost_q8
            || left.provisional_program_cost_q8
                != right.provisional_program_cost_q8
            || left.phase_error_u31 != right.phase_error_u31
        ) {
            fail("candidate order or score is not deterministic");
        }
    }
    if (
        first[0].source_observation_id != 10U
        || first[0].target_observation_id != 11U
        || first[0].cycle_offset != -1
        || first[1].cycle_offset != 0
        || first[2].cycle_offset != 1
    ) {
        fail("candidate ID formula changed");
    }

    for (resonith_partial_observation& item : observations) {
        if (
            item.observation_id == 10U
            || item.observation_id == 11U
            || item.observation_id == 13U
        ) {
            item.flags |= RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK;
        }
    }
    resonith_partial_path_manifest path_manifest{};
    path_manifest.struct_size = sizeof(path_manifest);
    path_manifest.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    path_manifest.second_order_law_version = 2U;
    path_manifest.protected_band_count = 4U;
    path_manifest.k_value_per_state = 8U;
    path_manifest.k_continuity_per_state = 8U;
    path_manifest.top_k_value = 8U;
    path_manifest.top_k_continuity = 8U;
    path_manifest.top_k_protected = 8U;
    path_manifest.protected_paths_per_band = 2U;
    path_manifest.minimum_path_observations = 3U;
    path_manifest.maximum_path_observations = 4096U;
    path_manifest.exact_set_candidate_limit = 20U;
    path_manifest.amplitude_floor_q16 = 1U;
    path_manifest.amplitude_residual_weight_q8 = 4U << 8U;
    path_manifest.frequency_sigma_floor_hz_q20 = 1U << 19U;
    path_manifest.birth_cost_bits_q8 = 48LL << 8U;
    path_manifest.death_cost_bits_q8 = 8LL << 8U;
    path_manifest.score_saturation = (1LL << 62U) - 1LL;
    path_manifest.maximum_path_records = 24U;
    path_manifest.maximum_total_entries = 1'000'000U;
    path_manifest.maximum_frontier_states = 250'000U;
    path_manifest.maximum_state_records = 1'000'000U;
    path_manifest.maximum_work_units = 10'000'000U;
    path_manifest.maximum_managed_bytes = 2ULL << 30U;
    path_manifest.protected_band_upper_hz_q20[0] = 500LL << 20U;
    path_manifest.protected_band_upper_hz_q20[1] = 1000LL << 20U;
    path_manifest.protected_band_upper_hz_q20[2] = 2000LL << 20U;

    resonith_partial_path_report path_report{};
    path_report.struct_size = sizeof(path_report);
    path_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest,
            nullptr,
            0U,
            nullptr,
            0U,
            &path_report
        ) != RESONITH_STATUS_OK
        || path_report.required_path_count != 8U
        || path_report.required_entry_count != 24U
        || path_report.protected_family_count != 2U
    ) {
        fail("R-191 path preflight failed");
    }
    std::copy(
        std::begin(path_report.input_fingerprint),
        std::end(path_report.input_fingerprint),
        path_manifest.expected_input_fingerprint
    );
    std::vector<resonith_partial_path> paths(
        path_report.required_path_count
    );
    std::vector<resonith_partial_path_entry> entries(
        path_report.required_entry_count
    );
    path_report = {};
    path_report.struct_size = sizeof(path_report);
    path_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest,
            paths.data(),
            paths.size(),
            entries.data(),
            entries.size(),
            &path_report
        ) != RESONITH_STATUS_OK
        || path_report.written_path_count != 8U
        || path_report.written_entry_count != 24U
        || path_report.selected_path_count != 1U
        || (paths[0].flags & RESONITH_PARTIAL_PATH_SELECTED) == 0U
        || paths[0].family_flags != 7U
        || entries[0].incoming_edge_candidate_id != UINT64_MAX
    ) {
        fail("R-191 path fill failed");
    }

    resonith_partial_path_manifest stale_manifest = path_manifest;
    stale_manifest.expected_input_fingerprint[0] ^= 1U;
    resonith_partial_path_report stale_report{};
    stale_report.struct_size = sizeof(stale_report);
    stale_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &stale_manifest,
            paths.data(),
            paths.size(),
            entries.data(),
            entries.size(),
            &stale_report
        ) != RESONITH_STATUS_HASH_MISMATCH
        || stale_report.termination
            != RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT
    ) {
        fail("stale R-191 preflight was accepted");
    }

    const std::uint64_t canary = 0x5a5aa5a55a5aa5a5ULL;
    paths[0].path_id = canary;
    entries[0].incoming_edge_candidate_id = canary;
    resonith_partial_path_report small_report{};
    small_report.struct_size = sizeof(small_report);
    small_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest,
            paths.data(),
            1U,
            entries.data(),
            entries.size(),
            &small_report
        ) != RESONITH_STATUS_OUTPUT_TOO_SMALL
        || paths[0].path_id != canary
        || entries[0].incoming_edge_candidate_id != canary
    ) {
        fail("capacity failure partially wrote semantic output");
    }

    resonith_partial_path_manifest no_fingerprint = path_manifest;
    std::fill(
        std::begin(no_fingerprint.expected_input_fingerprint),
        std::end(no_fingerprint.expected_input_fingerprint),
        0U
    );
    resonith_partial_path_report no_fingerprint_report{};
    no_fingerprint_report.struct_size = sizeof(no_fingerprint_report);
    no_fingerprint_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &no_fingerprint,
            paths.data(),
            paths.size(),
            entries.data(),
            entries.size(),
            &no_fingerprint_report
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || paths[0].path_id != canary
        || entries[0].incoming_edge_candidate_id != canary
    ) {
        fail("fill without preflight fingerprint wrote semantic output");
    }

    auto changed_observations = observations;
    ++changed_observations[0].potential_node_value_q8;
    resonith_partial_path_report changed_input_report{};
    changed_input_report.struct_size = sizeof(changed_input_report);
    changed_input_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            changed_observations.data(),
            changed_observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest,
            paths.data(),
            paths.size(),
            entries.data(),
            entries.size(),
            &changed_input_report
        ) != RESONITH_STATUS_HASH_MISMATCH
        || changed_input_report.termination
            != RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT
        || paths[0].path_id != canary
        || entries[0].incoming_edge_candidate_id != canary
    ) {
        fail("changed input after preflight was not rejected transactionally");
    }

    resonith_partial_graph_manifest invalid = manifest;
    invalid.sample_rate = 384001U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &invalid,
            nullptr,
            0U,
            &required
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        fail("invalid maximum sample rate was accepted");
    }
    invalid = manifest;
    invalid.maximum_edge_records = 2U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &invalid,
            nullptr,
            0U,
            &required
        ) != RESONITH_STATUS_PROFILE_BOUND
    ) {
        fail("edge-cardinality bound did not stop enumeration");
    }

    std::printf(
        "{\"schema\":\"resonith-r190-native-edge-cpu-1\","
        "\"edge_count\":%zu,\"path_count\":%llu,"
        "\"deterministic\":true,"
        "\"predictor_integrated\":false}\n",
        first_count,
        static_cast<unsigned long long>(path_report.written_path_count)
    );
    return 0;
}
