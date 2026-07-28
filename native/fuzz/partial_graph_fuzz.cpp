#include "resonith/partial_graph.h"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>

namespace {

std::uint32_t read_u32(
    const std::uint8_t* data,
    std::size_t size,
    std::size_t offset
) noexcept {
    std::uint32_t value = 0U;
    for (std::size_t index = 0U; index < 4U; ++index) {
        if (offset + index < size) {
            value |= static_cast<std::uint32_t>(data[offset + index])
                << static_cast<std::uint32_t>(index * 8U);
        }
    }
    return value;
}

void require(bool condition) {
    if (!condition) {
        std::abort();
    }
}

template <typename Value>
bool byte_equal(
    const std::vector<Value>& left,
    const std::vector<Value>& right
) {
    return left.size() == right.size()
        && std::memcmp(
            left.data(),
            right.data(),
            left.size() * sizeof(Value)
        ) == 0;
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    if (data == nullptr || size == 0U) {
        return 0;
    }
    const std::size_t observation_count = 2U + data[0] % 9U;
    const resonith_partial_resolution resolution{
        sizeof(resonith_partial_resolution),
        RESONITH_PARTIAL_GRAPH_ABI_VERSION,
        1U,
        512U,
        64U,
        {0U, 0U, 0U},
    };
    resonith_partial_graph_manifest graph{};
    graph.struct_size = sizeof(graph);
    graph.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
    graph.sample_rate = 16000U;
    graph.resolution_count = 1U;
    graph.gap_count = 2U;
    graph.neighbors_per_gap = 3U;
    graph.cycle_offset_count = 3U;
    graph.minimum_track_observations = 2U;
    graph.maximum_frequency_jump_hz_q20 = 8000LL << 20U;
    graph.maximum_frequency_slope_hz_per_sample_q20 = 1LL << 20U;
    graph.continuation_base_bits_q8 = 12 * 256;
    graph.continuation_reward_q8 = 12 * 256;
    graph.score_saturation = (1LL << 31U) - 1LL;
    graph.maximum_edge_records = 4096U;
    graph.maximum_path_hypotheses = 64U;
    graph.exact_set_candidate_limit = 16U;
    graph.gaps[0] = 1U;
    graph.gaps[1] = 2U;
    graph.cycle_offsets[0] = -1;
    graph.cycle_offsets[1] = 0;
    graph.cycle_offsets[2] = 1;

    std::vector<resonith_partial_observation> observations(
        observation_count
    );
    for (std::size_t index = 0U; index < observation_count; ++index) {
        resonith_partial_observation& item = observations[index];
        const std::uint32_t random = read_u32(
            data,
            size,
            1U + index * 4U
        );
        item.struct_size = sizeof(item);
        item.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
        item.observation_id = index + 1U;
        item.frame_index = static_cast<std::uint32_t>(index);
        item.center_sample = index * 64U;
        item.frequency_hz_q20 =
            static_cast<std::int64_t>(20U + random % 7980U) << 20U;
        item.frequency_uncertainty_hz_q20 =
            1U + ((random >> 4U) & 0xffffU);
        item.phase_turn_u32 = random * 2654435761U;
        item.phase_step_u32 = random ^ 0x9e3779b9U;
        item.normalized_amplitude_q16 =
            1U + (random & 0x7fffffffU);
        item.amplitude_uncertainty_q16 = (random >> 8U) | 1U;
        item.phase_uncertainty_u31 = random & 0x7fffffffU;
        item.resolution_id = 1U;
        item.detector_id = 0;
        item.band_id = random % 8U;
        item.ownership_component = static_cast<std::uint32_t>(index);
        item.ambiguity_component = RESONITH_PARTIAL_AMBIGUITY_NONE;
        item.flags = RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE
            | (
                (random & 1U) != 0U
                    ? static_cast<std::uint32_t>(
                        RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
                    )
                    : 0U
            )
            | (
                (random & 2U) != 0U
                    ? static_cast<std::uint32_t>(
                        RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
                    )
                    : 0U
            );
        item.protected_rank_q8 = static_cast<std::int32_t>(random);
        item.neighbor_priority_q8 = static_cast<std::int32_t>(
            random ^ 0x80000000U
        );
        item.potential_node_value_q8 = static_cast<std::int32_t>(
            random >> 1U
        );
        item.uncertainty_leakage_penalty_q8 =
            static_cast<std::int32_t>(random >> 3U);
    }

    std::size_t edge_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            nullptr,
            0U,
            &edge_count
        ) != RESONITH_STATUS_OK
        || edge_count == 0U
    ) {
        return 0;
    }
    if (size > 3U && (data[3] & 1U) != 0U && edge_count != 0U) {
        std::vector<resonith_partial_edge> transactional(edge_count + 2U);
        std::memset(
            transactional.data(),
            0xa5,
            transactional.size() * sizeof(resonith_partial_edge)
        );
        const auto before = transactional;
        std::size_t too_small_count = 0U;
        const resonith_status too_small_status =
            resonith_partial_graph_edges_cpu(
                &resolution,
                1U,
                observations.data(),
                observations.size(),
                &graph,
                transactional.data() + 1U,
                edge_count - 1U,
                &too_small_count
            );
        require(too_small_status == RESONITH_STATUS_OUTPUT_TOO_SMALL);
        require(too_small_count == edge_count);
        require(byte_equal(transactional, before));
    }
    std::vector<resonith_partial_edge> edges(edge_count);
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            edges.data(),
            edges.size(),
            &edge_count
        ) != RESONITH_STATUS_OK
    ) {
        return 0;
    }

    if (size > 2U && (data[1] & 0x80U) != 0U) {
        resonith_partial_edge& edge = edges[data[2] % edges.size()];
        const std::uint32_t mutation = data[1] % 15U;
        switch (mutation) {
        case 0U: edge.candidate_id ^= 1U; break;
        case 1U: edge.source_observation_id ^= 1U; break;
        case 2U: edge.target_observation_id ^= 1U; break;
        case 3U: edge.center_delta_samples ^= 1U; break;
        case 4U: edge.frequency_delta_hz_q20 ^= 1; break;
        case 5U: edge.gap_hops ^= 1U; break;
        case 6U: edge.cycle_offset ^= 1; break;
        case 7U: edge.phase_error_u31 ^= 1U; break;
        case 8U: edge.continuity_cost_q8 ^= 1; break;
        case 9U: edge.provisional_program_cost_q8 ^= 1; break;
        case 10U: edge.flags ^= 1U; break;
        case 11U: edge.struct_size ^= 1U; break;
        case 12U: edge.abi_version ^= 1U; break;
        case 13U: edge.reserved[0] ^= 1U; break;
        default: edge.reserved[1] ^= 1U; break;
        }
    }

    resonith_partial_path_manifest path{};
    path.struct_size = sizeof(path);
    path.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    path.second_order_law_version = 2U;
    path.protected_band_count = 1U;
    path.k_value_per_state = 2U;
    path.k_continuity_per_state = 2U;
    path.top_k_value = 4U;
    path.top_k_continuity = 4U;
    path.top_k_protected = 4U;
    path.protected_paths_per_band = 4U;
    path.minimum_path_observations = 2U;
    path.maximum_path_observations = 12U;
    path.exact_set_candidate_limit = 12U;
    path.amplitude_floor_q16 = 1U;
    path.amplitude_residual_weight_q8 = 256U;
    path.frequency_sigma_floor_hz_q20 = 1U;
    path.birth_cost_bits_q8 = 16 * 256;
    path.death_cost_bits_q8 = 8 * 256;
    path.score_saturation = (1LL << 31U) - 1LL;
    path.maximum_path_records = 12U;
    path.maximum_total_entries = 144U;
    path.maximum_frontier_states = 1024U;
    path.maximum_state_records = 4096U;
    path.maximum_work_units = 2'000'000U;
    path.maximum_managed_bytes = 4U << 20U;
    if (size > 5U && (data[3] & 0x40U) != 0U) {
        switch (data[4] % 8U) {
        case 0U: path.maximum_path_records = 1U; break;
        case 1U: path.maximum_total_entries = 1U; break;
        case 2U: path.maximum_frontier_states = 1U; break;
        case 3U: path.maximum_state_records = 1U; break;
        case 4U: path.maximum_work_units = 1U; break;
        case 5U: path.maximum_managed_bytes = 1U; break;
        case 6U: path.exact_set_candidate_limit = 1U; break;
        default: path.score_saturation = 1024; break;
        }
    }

    resonith_partial_path_report preflight{};
    preflight.struct_size = sizeof(preflight);
    preflight.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    const resonith_status preflight_status =
        resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            edges.data(),
            edges.size(),
            &graph,
            &path,
            nullptr,
            0U,
            nullptr,
            0U,
            &preflight
        );
    if (preflight_status != RESONITH_STATUS_OK) {
        std::vector<resonith_partial_path> rejected_paths(4U);
        std::vector<resonith_partial_path_entry> rejected_entries(8U);
        std::memset(
            rejected_paths.data(),
            0xa5,
            rejected_paths.size() * sizeof(resonith_partial_path)
        );
        std::memset(
            rejected_entries.data(),
            0x5a,
            rejected_entries.size() * sizeof(resonith_partial_path_entry)
        );
        const auto rejected_paths_before = rejected_paths;
        const auto rejected_entries_before = rejected_entries;
        resonith_partial_path_report rejected_report{};
        rejected_report.struct_size = sizeof(rejected_report);
        rejected_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
        static_cast<void>(resonith_partial_graph_paths_cpu_v2(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            edges.data(),
            edges.size(),
            &graph,
            &path,
            rejected_paths.data(),
            rejected_paths.size(),
            rejected_entries.data(),
            rejected_entries.size(),
            &rejected_report
        ));
        require(byte_equal(rejected_paths, rejected_paths_before));
        require(byte_equal(rejected_entries, rejected_entries_before));
        return 0;
    }
    std::memcpy(
        path.expected_input_fingerprint,
        preflight.input_fingerprint,
        sizeof(path.expected_input_fingerprint)
    );
    std::vector<resonith_partial_path> output_paths(
        preflight.required_path_count + 2U
    );
    std::vector<resonith_partial_path_entry> output_entries(
        preflight.required_entry_count + 2U
    );
    std::memset(
        output_paths.data(),
        0xa5,
        output_paths.size() * sizeof(resonith_partial_path)
    );
    std::memset(
        output_entries.data(),
        0x5a,
        output_entries.size() * sizeof(resonith_partial_path_entry)
    );
    const auto paths_before = output_paths;
    const auto entries_before = output_entries;

    std::size_t path_capacity = preflight.required_path_count;
    std::size_t entry_capacity = preflight.required_entry_count;
    if (size > 6U) {
        switch (data[5] % 7U) {
        case 0U:
            path.expected_input_fingerprint[0] ^= 1U;
            break;
        case 1U:
            observations[0].phase_turn_u32 ^= 1U;
            break;
        case 2U:
            if (path_capacity != 0U) {
                --path_capacity;
            }
            break;
        case 3U:
            if (entry_capacity != 0U) {
                --entry_capacity;
            }
            break;
        case 4U:
            path.maximum_work_units = 1U;
            break;
        case 5U:
            path.maximum_managed_bytes = 1U;
            break;
        default:
            break;
        }
    }
    resonith_partial_path_report fill{};
    fill.struct_size = sizeof(fill);
    fill.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    const resonith_status fill_status = resonith_partial_graph_paths_cpu_v2(
        &resolution,
        1U,
        observations.data(),
        observations.size(),
        edges.data(),
        edges.size(),
        &graph,
        &path,
        output_paths.data() + 1U,
        path_capacity,
        output_entries.data() + 1U,
        entry_capacity,
        &fill
    );
    require(std::memcmp(
        output_paths.data(),
        paths_before.data(),
        sizeof(resonith_partial_path)
    ) == 0);
    require(std::memcmp(
        output_paths.data() + output_paths.size() - 1U,
        paths_before.data() + paths_before.size() - 1U,
        sizeof(resonith_partial_path)
    ) == 0);
    require(std::memcmp(
        output_entries.data(),
        entries_before.data(),
        sizeof(resonith_partial_path_entry)
    ) == 0);
    require(std::memcmp(
        output_entries.data() + output_entries.size() - 1U,
        entries_before.data() + entries_before.size() - 1U,
        sizeof(resonith_partial_path_entry)
    ) == 0);
    if (fill_status == RESONITH_STATUS_OK) {
        require(fill.written_path_count == preflight.required_path_count);
        require(fill.written_entry_count == preflight.required_entry_count);
    } else {
        require(byte_equal(output_paths, paths_before));
        require(byte_equal(output_entries, entries_before));
    }
    return 0;
}
