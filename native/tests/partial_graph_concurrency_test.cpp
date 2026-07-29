#include "resonith/partial_graph.h"

#include <array>
#include <atomic>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <thread>

namespace {

constexpr std::size_t worker_count = 8U;
constexpr std::uint64_t default_sequence_count = 1000U;
constexpr std::uint64_t maximum_sequence_count = 1'000'000U;

resonith_partial_observation make_observation(
    std::uint64_t id,
    std::uint32_t frame,
    std::int64_t frequency_q20,
    std::uint32_t phase,
    std::uint32_t step,
    std::uint32_t amplitude_q16,
    std::uint32_t ownership
) noexcept {
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

std::uint64_t hash_bytes(
    std::uint64_t hash,
    const void* pointer,
    std::size_t size
) noexcept {
    constexpr std::uint64_t prime = 1099511628211ULL;
    const auto* bytes = static_cast<const std::uint8_t*>(pointer);
    for (std::size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= prime;
    }
    return hash;
}

bool run_sequence(std::uint64_t* output_hash) noexcept {
    const resonith_partial_resolution resolution{
        sizeof(resonith_partial_resolution),
        RESONITH_PARTIAL_GRAPH_ABI_VERSION,
        7U,
        1024U,
        128U,
        {0U, 0U, 0U},
    };
    resonith_partial_graph_manifest graph{};
    graph.struct_size = sizeof(graph);
    graph.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
    graph.sample_rate = 8000U;
    graph.resolution_count = 1U;
    graph.gap_count = 2U;
    graph.neighbors_per_gap = 2U;
    graph.cycle_offset_count = 3U;
    graph.minimum_track_observations = 4U;
    graph.maximum_frequency_jump_hz_q20 = 80LL << 20U;
    graph.maximum_frequency_slope_hz_per_sample_q20 = 1LL << 16U;
    graph.continuation_base_bits_q8 = 12 * 256;
    graph.continuation_reward_q8 = 12 * 256;
    graph.score_saturation = (1LL << 31U) - 1LL;
    graph.maximum_edge_records = 1024U;
    graph.maximum_path_hypotheses = 128U;
    graph.exact_set_candidate_limit = 20U;
    graph.gaps[0] = 1U;
    graph.gaps[1] = 2U;
    graph.cycle_offsets[0] = -1;
    graph.cycle_offsets[1] = 0;
    graph.cycle_offsets[2] = 1;

    const std::uint32_t step_440 = static_cast<std::uint32_t>(
        (440ULL << 32U) / graph.sample_rate
    );
    const std::uint32_t step_442 = static_cast<std::uint32_t>(
        (442ULL << 32U) / graph.sample_rate
    );
    std::array<resonith_partial_observation, 5U> observations{
        make_observation(
            10U, 0U, 440LL << 20U, 0x10000000U, step_440,
            12000U << 16U, 0U
        ),
        make_observation(
            11U, 1U, 441LL << 20U, 0x1ccccccdU, step_440,
            11800U << 16U, 1U
        ),
        make_observation(
            12U, 1U, 900LL << 20U, 0x20000000U, 0x1ccccccdU,
            4000U << 16U, 2U
        ),
        make_observation(
            13U, 2U, 442LL << 20U, 0x2999999aU, step_442,
            11600U << 16U, 3U
        ),
        make_observation(
            14U, 2U, 1500LL << 20U, 0x30000000U, 0x4ccccccdU,
            2000U << 16U, 4U
        ),
    };
    for (resonith_partial_observation& item : observations) {
        if (
            item.observation_id == 10U
            || item.observation_id == 11U
            || item.observation_id == 13U
        ) {
            item.flags |= RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK;
        }
    }

    std::size_t required_edges = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            nullptr,
            0U,
            &required_edges
        ) != RESONITH_STATUS_OK
        || required_edges != 9U
    ) {
        return false;
    }
    std::array<resonith_partial_edge, 16U> edges{};
    std::size_t written_edges = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            edges.data(),
            edges.size(),
            &written_edges
        ) != RESONITH_STATUS_OK
        || written_edges != required_edges
    ) {
        return false;
    }

    resonith_partial_path_manifest_v3 path{};
    path.struct_size = sizeof(path);
    path.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    path.second_order_law_version = 2U;
    path.protected_band_count = 4U;
    path.k_value_per_state = 8U;
    path.k_continuity_per_state = 8U;
    path.top_k_value = 8U;
    path.top_k_continuity = 8U;
    path.top_k_protected = 8U;
    path.protected_paths_per_band = 2U;
    path.minimum_path_observations = 3U;
    path.maximum_path_observations = 4096U;
    path.exact_set_candidate_limit = 20U;
    path.amplitude_floor_q16 = 1U;
    path.amplitude_residual_weight_q8 = 4U << 8U;
    path.work_ledger_version = RESONITH_PARTIAL_PATH_WORK_LEDGER_VERSION;
    path.frequency_sigma_floor_hz_q20 = 1U << 19U;
    path.birth_cost_bits_q8 = 48LL << 8U;
    path.death_cost_bits_q8 = 8LL << 8U;
    path.score_saturation = (1LL << 62U) - 1LL;
    path.maximum_path_records = 24U;
    path.maximum_total_entries = 1'000'000U;
    path.maximum_frontier_states = 250'000U;
    path.maximum_state_records = 1'000'000U;
    path.maximum_work_units = 10'000'000U;
    path.maximum_managed_bytes = 2ULL << 30U;
    path.maximum_device_bytes = RESONITH_PARTIAL_MAX_DEVICE_BYTES;
    path.protected_band_upper_hz_q20[0] = 500LL << 20U;
    path.protected_band_upper_hz_q20[1] = 1000LL << 20U;
    path.protected_band_upper_hz_q20[2] = 2000LL << 20U;

    resonith_partial_path_report_v3 preflight{};
    preflight.struct_size = sizeof(preflight);
    preflight.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            edges.data(),
            written_edges,
            &graph,
            &path,
            nullptr,
            0U,
            nullptr,
            0U,
            &preflight
        ) != RESONITH_STATUS_OK
        || preflight.required_path_count != 8U
        || preflight.required_entry_count != 24U
    ) {
        return false;
    }
    std::memcpy(
        path.expected_input_fingerprint,
        preflight.input_fingerprint,
        sizeof(path.expected_input_fingerprint)
    );
    std::array<resonith_partial_path_v3, 24U> paths{};
    std::array<resonith_partial_path_entry_v3, 64U> entries{};
    resonith_partial_path_report_v3 fill{};
    fill.struct_size = sizeof(fill);
    fill.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            edges.data(),
            written_edges,
            &graph,
            &path,
            paths.data(),
            paths.size(),
            entries.data(),
            entries.size(),
            &fill
        ) != RESONITH_STATUS_OK
        || fill.written_path_count != preflight.required_path_count
        || fill.written_entry_count != preflight.required_entry_count
        || fill.reserved_device_bytes != 0U
        || fill.committed_device_bytes != 0U
        || fill.peak_live_device_bytes != 0U
        || fill.work_event_counts[RESONITH_PARTIAL_WORK_CUDA_ITEM] != 0U
    ) {
        return false;
    }

    std::uint64_t hash = 1469598103934665603ULL;
    hash = hash_bytes(
        hash,
        edges.data(),
        written_edges * sizeof(resonith_partial_edge)
    );
    hash = hash_bytes(
        hash,
        paths.data(),
        fill.written_path_count * sizeof(resonith_partial_path_v3)
    );
    hash = hash_bytes(
        hash,
        entries.data(),
        fill.written_entry_count * sizeof(resonith_partial_path_entry_v3)
    );
    hash = hash_bytes(hash, &fill, sizeof(fill));
    *output_hash = hash;
    return true;
}

bool parse_sequence_count(
    int argument_count,
    char** arguments,
    std::uint64_t* output
) noexcept {
    if (argument_count == 1) {
        *output = default_sequence_count;
        return true;
    }
    if (argument_count != 2 || arguments[1] == nullptr) {
        return false;
    }
    errno = 0;
    char* end = nullptr;
    const unsigned long long parsed = std::strtoull(
        arguments[1],
        &end,
        10
    );
    if (
        errno != 0
        || end == arguments[1]
        || *end != '\0'
        || parsed == 0ULL
        || parsed > maximum_sequence_count
    ) {
        return false;
    }
    *output = static_cast<std::uint64_t>(parsed);
    return true;
}

struct worker_result {
    std::uint64_t hash = 0U;
    std::uint64_t sequences = 0U;
};

}  // namespace

int main(int argument_count, char** arguments) {
    std::uint64_t sequence_count = 0U;
    if (!parse_sequence_count(argument_count, arguments, &sequence_count)) {
        std::fprintf(
            stderr,
            "usage: resonith_partial_graph_concurrency_test "
            "[1..1000000 sequences]\n"
        );
        return 2;
    }

    std::uint64_t reference_hash = 0U;
    if (!run_sequence(&reference_hash)) {
        std::fprintf(
            stderr,
            "partial_graph_concurrency_test: serial reference failed\n"
        );
        return 1;
    }

    std::atomic<std::size_t> ready{0U};
    std::atomic<bool> begin{false};
    std::atomic<bool> failed{false};
    std::array<worker_result, worker_count> results{};
    std::array<std::thread, worker_count> workers{};
    for (std::size_t worker = 0U; worker < worker_count; ++worker) {
        workers[worker] = std::thread([&, worker]() {
            ready.fetch_add(1U, std::memory_order_release);
            while (!begin.load(std::memory_order_acquire)) {
                std::this_thread::yield();
            }
            const std::uint64_t first = static_cast<std::uint64_t>(worker);
            const std::uint64_t stride =
                static_cast<std::uint64_t>(worker_count);
            for (
                std::uint64_t sequence = first;
                sequence < sequence_count;
                sequence += stride
            ) {
                std::uint64_t hash = 0U;
                if (!run_sequence(&hash) || hash != reference_hash) {
                    failed.store(true, std::memory_order_release);
                    return;
                }
                results[worker].hash ^= hash;
                ++results[worker].sequences;
            }
        });
    }
    while (ready.load(std::memory_order_acquire) != worker_count) {
        std::this_thread::yield();
    }
    begin.store(true, std::memory_order_release);
    for (std::thread& worker : workers) {
        worker.join();
    }
    if (failed.load(std::memory_order_acquire)) {
        std::fprintf(
            stderr,
            "partial_graph_concurrency_test: concurrent sequence failed\n"
        );
        return 1;
    }

    std::uint64_t completed = 0U;
    std::uint64_t aggregate_hash = 0U;
    for (const worker_result& result : results) {
        completed += result.sequences;
        aggregate_hash ^= result.hash;
    }
    if (completed != sequence_count) {
        std::fprintf(
            stderr,
            "partial_graph_concurrency_test: sequence count mismatch\n"
        );
        return 1;
    }
    std::printf(
        "{\"schema\":\"resonith-r202-concurrency-1\","
        "\"threads\":%zu,\"sequences\":%llu,"
        "\"reference_hash\":\"%016llx\","
        "\"aggregate_hash\":\"%016llx\","
        "\"device_bytes\":0}\n",
        worker_count,
        static_cast<unsigned long long>(completed),
        static_cast<unsigned long long>(reference_hash),
        static_cast<unsigned long long>(aggregate_hash)
    );
    return 0;
}
