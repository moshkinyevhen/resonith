#include "resonith/partial_graph.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory_resource>
#include <new>
#include <vector>

namespace resonith::internal {
bool partial_graph_environmental_oom_probe() noexcept;
bool partial_graph_memory_provenance_probe() noexcept;
bool partial_graph_generation_arena_probe() noexcept;
bool partial_graph_work_ledger_probe() noexcept;
void partial_graph_set_test_upstream_resource(
    std::pmr::memory_resource* resource
) noexcept;
}

namespace {

class fail_allocation_resource final : public std::pmr::memory_resource {
private:
    void* do_allocate(std::size_t, std::size_t) override {
        throw std::bad_alloc{};
    }

    void do_deallocate(void*, std::size_t, std::size_t) override {}

    bool do_is_equal(
        const std::pmr::memory_resource& other
    ) const noexcept override {
        return this == &other;
    }
};

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
    if (!resonith::internal::partial_graph_memory_provenance_probe()) {
        fail("host memory provenance counters or rollback are unsound");
    }
    if (!resonith::internal::partial_graph_generation_arena_probe()) {
        fail("generation-safe arena accepted a stale reused handle");
    }
    if (!resonith::internal::partial_graph_work_ledger_probe()) {
        fail("typed work ledger violated an event-prefix boundary");
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
    const std::size_t count_canary =
        std::numeric_limits<std::size_t>::max() - 17U;
    rejected_edge_count = count_canary;
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
        || rejected_edge_count != count_canary
        || std::memcmp(
            edge_canary.data(),
            edge_canary_before.data(),
            edge_canary.size() * sizeof(resonith_partial_edge)
        ) != 0
    ) {
        fail("R-190 managed-byte overflow was not rejected transactionally");
    }
    std::size_t overlap_count = count_canary;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &manifest,
            reinterpret_cast<resonith_partial_edge*>(observations.data()),
            1U,
            &overlap_count
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || overlap_count != count_canary
    ) {
        fail("R-190 overlapping input/output ranges were not rejected");
    }
    resonith_partial_graph_manifest empty_manifest = manifest;
    std::size_t empty_count = 99U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            nullptr,
            0U,
            &empty_manifest,
            nullptr,
            0U,
            &empty_count
        ) != RESONITH_STATUS_OK
        || empty_count != 0U
    ) {
        fail("R-190 empty bounded snapshot preflight failed");
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

    resonith_partial_path_report retired_v2_report{};
    retired_v2_report.struct_size = sizeof(retired_v2_report);
    retired_v2_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    const resonith_partial_path_report retired_v2_before =
        retired_v2_report;
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
            &retired_v2_report
        ) != RESONITH_STATUS_UNSUPPORTED_VERSION
        || std::memcmp(
            &retired_v2_report,
            &retired_v2_before,
            sizeof(retired_v2_report)
        ) != 0
    ) {
        fail("retired R-191 v2 ABI was not a no-write safe stub");
    }

    resonith_partial_path_manifest_v3 path_manifest_v3{};
    std::memcpy(&path_manifest_v3, &path_manifest, 144U);
    path_manifest_v3.struct_size = sizeof(path_manifest_v3);
    path_manifest_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    path_manifest_v3.work_ledger_version =
        RESONITH_PARTIAL_PATH_WORK_LEDGER_VERSION;
    path_manifest_v3.maximum_device_bytes =
        RESONITH_PARTIAL_MAX_DEVICE_BYTES;
    std::copy(
        std::begin(path_manifest.protected_band_upper_hz_q20),
        std::end(path_manifest.protected_band_upper_hz_q20),
        path_manifest_v3.protected_band_upper_hz_q20
    );
    resonith_partial_path_report_v3 report_v3{};
    report_v3.struct_size = sizeof(report_v3);
    report_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &report_v3
        ) != RESONITH_STATUS_OK
        || report_v3.required_path_count != 8U
        || report_v3.required_entry_count != 24U
        || report_v3.work_event_counts[18] != 33U
        || report_v3.work_event_counts[19] != 1U
        || report_v3.reserved_host_bytes == 0U
        || report_v3.reserved_host_bytes
            < report_v3.committed_host_bytes
        || report_v3.committed_host_bytes
            < report_v3.peak_live_host_bytes
        || report_v3.peak_live_host_bytes
            > path_manifest_v3.maximum_managed_bytes
        || report_v3.reserved_device_bytes != 0U
        || report_v3.committed_device_bytes != 0U
        || report_v3.peak_live_device_bytes != 0U
        || report_v3.work_event_counts[
            RESONITH_PARTIAL_WORK_CUDA_ITEM
        ] != 0U
    ) {
        fail("R-197 v3 transactional preflight failed");
    }
    fail_allocation_resource failed_upstream;
    resonith::internal::partial_graph_set_test_upstream_resource(
        &failed_upstream
    );
    resonith_partial_path_report_v3 oom_v3{};
    oom_v3.struct_size = sizeof(oom_v3);
    oom_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const resonith_status oom_status = resonith_partial_graph_paths_cpu_v3(
        &resolution,
        1U,
        observations.data(),
        observations.size(),
        first.data(),
        first.size(),
        &manifest,
        &path_manifest_v3,
        nullptr,
        0U,
        nullptr,
        0U,
        &oom_v3
    );
    resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
    if (
        oom_status != RESONITH_STATUS_OUT_OF_MEMORY
        || oom_v3.termination
            != RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM
        || oom_v3.reserved_host_bytes == 0U
        || oom_v3.committed_host_bytes != 0U
        || oom_v3.peak_live_host_bytes != 0U
        || oom_v3.reserved_device_bytes != 0U
        || oom_v3.committed_device_bytes != 0U
        || oom_v3.peak_live_device_bytes != 0U
    ) {
        std::fprintf(
            stderr,
            "R-201 OOM status=%u termination=%u host=%llu/%llu/%llu "
            "device=%llu/%llu/%llu\n",
            static_cast<unsigned>(oom_status),
            static_cast<unsigned>(oom_v3.termination),
            static_cast<unsigned long long>(oom_v3.reserved_host_bytes),
            static_cast<unsigned long long>(oom_v3.committed_host_bytes),
            static_cast<unsigned long long>(oom_v3.peak_live_host_bytes),
            static_cast<unsigned long long>(oom_v3.reserved_device_bytes),
            static_cast<unsigned long long>(oom_v3.committed_device_bytes),
            static_cast<unsigned long long>(oom_v3.peak_live_device_bytes)
        );
        fail("R-201 environmental OOM provenance report is not exact");
    }

    resonith_partial_path_report_v3 invalid_header_v3{};
    invalid_header_v3.struct_size = 0U;
    invalid_header_v3.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto invalid_header_before = invalid_header_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &invalid_header_v3
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || std::memcmp(
            &invalid_header_v3,
            &invalid_header_before,
            sizeof(invalid_header_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 1 modified an invalid report");
    }

    resonith_partial_path_report_v3 overflow_v3{};
    overflow_v3.struct_size = sizeof(overflow_v3);
    overflow_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto overflow_before = overflow_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            std::numeric_limits<std::size_t>::max(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &overflow_v3
        ) != RESONITH_STATUS_PROFILE_BOUND
        || std::memcmp(
            &overflow_v3,
            &overflow_before,
            sizeof(overflow_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 2 did not preserve the report");
    }

    auto overlap_manifest_v3 = path_manifest_v3;
    const auto overlap_manifest_before = overlap_manifest_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &overlap_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            reinterpret_cast<resonith_partial_path_report_v3*>(
                &overlap_manifest_v3
            )
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || std::memcmp(
            &overlap_manifest_v3,
            &overlap_manifest_before,
            sizeof(overlap_manifest_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 3 did not reject overlap transactionally");
    }

    auto reserved_manifest_v3 = path_manifest_v3;
    reserved_manifest_v3.reserved[0] = 1U;
    resonith_partial_path_report_v3 reserved_v3{};
    reserved_v3.struct_size = sizeof(reserved_v3);
    reserved_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto reserved_before = reserved_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &reserved_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &reserved_v3
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || std::memcmp(
            &reserved_v3,
            &reserved_before,
            sizeof(reserved_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 4 modified the report");
    }

    auto hard_manifest_v3 = path_manifest_v3;
    hard_manifest_v3.maximum_path_records =
        RESONITH_PARTIAL_PATH_MAX_RECORDS + 1ULL;
    resonith_partial_path_report_v3 hard_v3{};
    hard_v3.struct_size = sizeof(hard_v3);
    hard_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto hard_before = hard_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &hard_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &hard_v3
        ) != RESONITH_STATUS_PROFILE_BOUND
        || std::memcmp(&hard_v3, &hard_before, sizeof(hard_v3)) != 0
    ) {
        fail("R-197 precedence row 5 modified the report");
    }

    resonith_partial_path_report_v3 invalid_overflow_v3{};
    invalid_overflow_v3.struct_size = 0U;
    invalid_overflow_v3.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto invalid_overflow_before = invalid_overflow_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            std::numeric_limits<std::size_t>::max(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &invalid_overflow_v3
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || std::memcmp(
            &invalid_overflow_v3,
            &invalid_overflow_before,
            sizeof(invalid_overflow_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 1 did not beat row 2");
    }

    auto reserved_hard_manifest_v3 = hard_manifest_v3;
    reserved_hard_manifest_v3.reserved[0] = 1U;
    resonith_partial_path_report_v3 reserved_hard_v3{};
    reserved_hard_v3.struct_size = sizeof(reserved_hard_v3);
    reserved_hard_v3.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto reserved_hard_before = reserved_hard_v3;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &reserved_hard_manifest_v3,
            nullptr,
            0U,
            nullptr,
            0U,
            &reserved_hard_v3
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || std::memcmp(
            &reserved_hard_v3,
            &reserved_hard_before,
            sizeof(reserved_hard_v3)
        ) != 0
    ) {
        fail("R-197 precedence row 4 did not beat row 5");
    }

    std::vector<resonith_partial_path_v3> paths_v3(
        report_v3.required_path_count
    );
    std::vector<resonith_partial_path_entry_v3> entries_v3(
        report_v3.required_entry_count
    );
    const std::uint64_t canary = 0x5a5aa5a55a5aa5a5ULL;
    paths_v3[0].path_id = canary;
    entries_v3[0].incoming_edge_candidate_id = canary;
    resonith_partial_path_report_v3 no_fingerprint_v3{};
    no_fingerprint_v3.struct_size = sizeof(no_fingerprint_v3);
    no_fingerprint_v3.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            paths_v3.data(),
            1U,
            entries_v3.data(),
            entries_v3.size(),
            &no_fingerprint_v3
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || paths_v3[0].path_id != canary
        || entries_v3[0].incoming_edge_candidate_id != canary
        || no_fingerprint_v3.work_event_counts[
               RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE
           ] != 0U
        || std::any_of(
               std::begin(no_fingerprint_v3.input_fingerprint),
               std::end(no_fingerprint_v3.input_fingerprint),
               [](std::uint64_t item) { return item != 0U; }
           )
    ) {
        fail(
            "R-199 missing identity did not precede fingerprint transactionally"
        );
    }
    std::copy(
        std::begin(report_v3.input_fingerprint),
        std::end(report_v3.input_fingerprint),
        path_manifest_v3.expected_input_fingerprint
    );
    report_v3 = {};
    report_v3.struct_size = sizeof(report_v3);
    report_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            paths_v3.data(),
            paths_v3.size(),
            entries_v3.data(),
            entries_v3.size(),
            &report_v3
        ) != RESONITH_STATUS_OK
        || report_v3.written_path_count != 8U
        || report_v3.written_entry_count != 24U
        || report_v3.reserved_host_bytes
            < report_v3.committed_host_bytes
        || report_v3.committed_host_bytes
            < report_v3.peak_live_host_bytes
        || report_v3.reserved_device_bytes != 0U
        || report_v3.committed_device_bytes != 0U
        || report_v3.peak_live_device_bytes != 0U
        || report_v3.work_event_counts[
            RESONITH_PARTIAL_WORK_CUDA_ITEM
        ] != 0U
        || paths_v3[0].abi_version
            != RESONITH_PARTIAL_PATH_V3_ABI_VERSION
        || entries_v3[0].abi_version
            != RESONITH_PARTIAL_PATH_V3_ABI_VERSION
    ) {
        fail("R-197 v3 transactional fill failed");
    }
    const auto paths_v3_before = paths_v3;
    const auto entries_v3_before = entries_v3;
    resonith_partial_path_report_v3 small_v3{};
    small_v3.struct_size = sizeof(small_v3);
    small_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            paths_v3.data(),
            1U,
            entries_v3.data(),
            entries_v3.size(),
            &small_v3
        ) != RESONITH_STATUS_OUTPUT_TOO_SMALL
        || std::memcmp(
            paths_v3.data(),
            paths_v3_before.data(),
            paths_v3.size() * sizeof(resonith_partial_path_v3)
        ) != 0
        || std::memcmp(
            entries_v3.data(),
            entries_v3_before.data(),
            entries_v3.size() * sizeof(resonith_partial_path_entry_v3)
        ) != 0
    ) {
        fail("R-197 v3 capacity failure published partial payload");
    }

    auto changed_observations = observations;
    ++changed_observations[0].potential_node_value_q8;
    resonith_partial_path_report_v3 changed_input_v3{};
    changed_input_v3.struct_size = sizeof(changed_input_v3);
    changed_input_v3.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            changed_observations.data(),
            changed_observations.size(),
            first.data(),
            first.size(),
            &manifest,
            &path_manifest_v3,
            paths_v3.data(),
            1U,
            entries_v3.data(),
            entries_v3.size(),
            &changed_input_v3
        ) != RESONITH_STATUS_HASH_MISMATCH
        || changed_input_v3.termination
            != RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT
        || changed_input_v3.work_event_counts[
               RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE
           ] == 0U
        || std::equal(
               std::begin(changed_input_v3.input_fingerprint),
               std::end(changed_input_v3.input_fingerprint),
               std::begin(path_manifest_v3.expected_input_fingerprint)
           )
        || std::memcmp(
            paths_v3.data(),
            paths_v3_before.data(),
            paths_v3.size() * sizeof(resonith_partial_path_v3)
        ) != 0
        || std::memcmp(
            entries_v3.data(),
            entries_v3_before.data(),
            entries_v3.size() * sizeof(resonith_partial_path_entry_v3)
        ) != 0
    ) {
        fail(
            "R-199 stale identity lacked the actual canonical fingerprint"
        );
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
        "\"reserved_host_bytes\":%llu,"
        "\"committed_host_bytes\":%llu,"
        "\"peak_live_host_bytes\":%llu,"
        "\"device_bytes\":0,"
        "\"deterministic\":true,"
        "\"predictor_integrated\":false}\n",
        first_count,
        static_cast<unsigned long long>(report_v3.written_path_count),
        static_cast<unsigned long long>(report_v3.reserved_host_bytes),
        static_cast<unsigned long long>(report_v3.committed_host_bytes),
        static_cast<unsigned long long>(report_v3.peak_live_host_bytes)
    );
    return 0;
}
