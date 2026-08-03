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

namespace resonith::internal {
void partial_graph_set_test_upstream_resource(
    std::pmr::memory_resource* resource
) noexcept;
}

namespace {

[[noreturn]] void fail(const char* message) {
    resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
    std::fprintf(stderr, "partial_graph_allocation_ordinal_test: %s\n", message);
    std::exit(1);
}

struct allocation_record {
    std::uint64_t bytes;
    std::uint64_t alignment;
};

class ordinal_resource final : public std::pmr::memory_resource {
public:
    void reset(std::uint64_t fail_ordinal = 0U) noexcept {
        fail_ordinal_ = fail_ordinal;
        ordinal_ = 0U;
        current_bytes_ = 0U;
        live_allocations_ = 0U;
        peak_reserved_ = 0U;
        peak_committed_ = 0U;
        record_count_ = 0U;
        internal_failure_ = false;
    }

    [[nodiscard]] std::uint64_t allocation_count() const noexcept {
        return ordinal_;
    }

    [[nodiscard]] std::uint64_t peak_reserved() const noexcept {
        return peak_reserved_;
    }

    [[nodiscard]] std::uint64_t peak_committed() const noexcept {
        return peak_committed_;
    }

    [[nodiscard]] bool healthy() const noexcept {
        return !internal_failure_
            && current_bytes_ == 0U
            && live_allocations_ == 0U;
    }

    [[nodiscard]] std::uint64_t trace_hash() const noexcept {
        std::uint64_t hash = 1469598103934665603ULL;
        const auto mix = [&hash](std::uint64_t value) {
            for (std::uint32_t index = 0U; index < 8U; ++index) {
                hash ^= (value >> (index * 8U)) & 0xffU;
                hash *= 1099511628211ULL;
            }
        };
        mix(record_count_);
        for (std::size_t index = 0U; index < record_count_; ++index) {
            mix(records_[index].bytes);
            mix(records_[index].alignment);
        }
        return hash;
    }

private:
    void* do_allocate(std::size_t bytes, std::size_t alignment) override {
        if (record_count_ >= records_.size()) {
            internal_failure_ = true;
            throw std::bad_alloc{};
        }
        records_[record_count_++] = {
            static_cast<std::uint64_t>(bytes),
            static_cast<std::uint64_t>(alignment),
        };
        ++ordinal_;
        const std::uint64_t requested = static_cast<std::uint64_t>(bytes);
        if (
            requested > std::numeric_limits<std::uint64_t>::max()
                - current_bytes_
        ) {
            internal_failure_ = true;
            throw std::bad_alloc{};
        }
        peak_reserved_ = std::max(
            peak_reserved_,
            current_bytes_ + requested
        );
        if (fail_ordinal_ != 0U && ordinal_ == fail_ordinal_) {
            throw std::bad_alloc{};
        }
        void* pointer = upstream_->allocate(bytes, alignment);
        current_bytes_ += requested;
        ++live_allocations_;
        peak_committed_ = std::max(peak_committed_, current_bytes_);
        return pointer;
    }

    void do_deallocate(
        void* pointer,
        std::size_t bytes,
        std::size_t alignment
    ) override {
        const auto released = static_cast<std::uint64_t>(bytes);
        if (released > current_bytes_ || live_allocations_ == 0U) {
            internal_failure_ = true;
        } else {
            current_bytes_ -= released;
            --live_allocations_;
        }
        upstream_->deallocate(pointer, bytes, alignment);
    }

    bool do_is_equal(
        const std::pmr::memory_resource& other
    ) const noexcept override {
        return this == &other;
    }

    std::pmr::memory_resource* upstream_ =
        std::pmr::new_delete_resource();
    std::array<allocation_record, 4096U> records_{};
    std::uint64_t fail_ordinal_ = 0U;
    std::uint64_t ordinal_ = 0U;
    std::uint64_t current_bytes_ = 0U;
    std::uint64_t live_allocations_ = 0U;
    std::uint64_t peak_reserved_ = 0U;
    std::uint64_t peak_committed_ = 0U;
    std::size_t record_count_ = 0U;
    bool internal_failure_ = false;
};

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

bool exact_report_memory(
    const resonith_partial_path_report_v3& report,
    const ordinal_resource& resource
) noexcept {
    std::uint64_t work_sum = 0U;
    for (const std::uint64_t count : report.work_event_counts) {
        if (count > std::numeric_limits<std::uint64_t>::max() - work_sum) {
            return false;
        }
        work_sum += count;
    }
    return report.reserved_host_bytes == resource.peak_reserved()
        && report.committed_host_bytes == resource.peak_committed()
        && report.peak_live_host_bytes == resource.peak_committed()
        && report.reserved_device_bytes == 0U
        && report.committed_device_bytes == 0U
        && report.peak_live_device_bytes == 0U
        && report.work_event_counts[RESONITH_PARTIAL_WORK_CUDA_ITEM] == 0U
        && report.work_units == work_sum;
}

}  // namespace

int main() {
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
            10U,
            0U,
            440LL << 20U,
            0x10000000U,
            step_440,
            12000U << 16U,
            0U
        ),
        make_observation(
            11U,
            1U,
            441LL << 20U,
            0x1ccccccdU,
            step_440,
            11800U << 16U,
            1U
        ),
        make_observation(
            12U,
            1U,
            900LL << 20U,
            0x20000000U,
            0x1ccccccdU,
            4000U << 16U,
            2U
        ),
        make_observation(
            13U,
            2U,
            442LL << 20U,
            0x2999999aU,
            step_442,
            11600U << 16U,
            3U
        ),
        make_observation(
            14U,
            2U,
            1500LL << 20U,
            0x30000000U,
            0x4ccccccdU,
            2000U << 16U,
            4U
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

    std::array<resonith_partial_edge, 16U> canonical_edges{};
    std::size_t canonical_edge_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            canonical_edges.data(),
            canonical_edges.size(),
            &canonical_edge_count
        ) != RESONITH_STATUS_OK
        || canonical_edge_count != 9U
    ) {
        fail("canonical R-190 fixture failed");
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

    resonith_partial_path_report_v3 canonical_preflight{};
    canonical_preflight.struct_size = sizeof(canonical_preflight);
    canonical_preflight.abi_version =
        RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (
        resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            canonical_edges.data(),
            canonical_edge_count,
            &graph,
            &path,
            nullptr,
            0U,
            nullptr,
            0U,
            &canonical_preflight
        ) != RESONITH_STATUS_OK
        || canonical_preflight.required_path_count != 8U
        || canonical_preflight.required_entry_count != 24U
    ) {
        fail("canonical R-191 preflight failed");
    }

    ordinal_resource resource;
    const auto run_r190_preflight = [&](std::uint64_t fail_ordinal) {
        resource.reset(fail_ordinal);
        resonith::internal::partial_graph_set_test_upstream_resource(&resource);
        std::size_t count = std::numeric_limits<std::size_t>::max() - 7U;
        const resonith_status status = resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            nullptr,
            0U,
            &count
        );
        resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
        if (!resource.healthy()) {
            fail("R-190 preflight leaked an upstream allocation");
        }
        if (
            fail_ordinal == 0U
                ? status != RESONITH_STATUS_OK || count != 9U
                : status != RESONITH_STATUS_OUT_OF_MEMORY
                    || count != std::numeric_limits<std::size_t>::max() - 7U
        ) {
            fail("R-190 preflight ordinal status/publication mismatch");
        }
        return resource.allocation_count();
    };

    resource.reset();
    const std::uint64_t r190_preflight_allocations =
        run_r190_preflight(0U);
    const std::uint64_t r190_preflight_hash = resource.trace_hash();
    if (
        r190_preflight_allocations == 0U
        || run_r190_preflight(0U) != r190_preflight_allocations
        || resource.trace_hash() != r190_preflight_hash
    ) {
        fail("R-190 preflight allocation trace is nondeterministic");
    }
    for (
        std::uint64_t ordinal = 1U;
        ordinal <= r190_preflight_allocations;
        ++ordinal
    ) {
        const std::uint64_t first_count = run_r190_preflight(ordinal);
        const std::uint64_t first_hash = resource.trace_hash();
        if (
            run_r190_preflight(ordinal) != first_count
            || resource.trace_hash() != first_hash
        ) {
            fail("R-190 preflight failed-ordinal trace changed");
        }
        static_cast<void>(run_r190_preflight(0U));
    }

    const auto run_r190_fill = [&](std::uint64_t fail_ordinal) {
        resource.reset(fail_ordinal);
        std::array<resonith_partial_edge, 16U> output{};
        std::memset(output.data(), 0xa5, sizeof(output));
        const auto before = output;
        std::size_t count = std::numeric_limits<std::size_t>::max() - 9U;
        resonith::internal::partial_graph_set_test_upstream_resource(&resource);
        const resonith_status status = resonith_partial_graph_edges_cpu(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            &graph,
            output.data(),
            output.size(),
            &count
        );
        resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
        if (!resource.healthy()) {
            fail("R-190 fill leaked an upstream allocation");
        }
        if (fail_ordinal == 0U) {
            if (status != RESONITH_STATUS_OK || count != 9U) {
                fail("R-190 fill baseline failed");
            }
        } else if (
            status != RESONITH_STATUS_OUT_OF_MEMORY
            || count != std::numeric_limits<std::size_t>::max() - 9U
            || std::memcmp(output.data(), before.data(), sizeof(output)) != 0
        ) {
            fail("R-190 fill ordinal transaction mismatch");
        }
        return resource.allocation_count();
    };

    const std::uint64_t r190_fill_allocations = run_r190_fill(0U);
    const std::uint64_t r190_fill_hash = resource.trace_hash();
    if (
        r190_fill_allocations == 0U
        || run_r190_fill(0U) != r190_fill_allocations
        || resource.trace_hash() != r190_fill_hash
    ) {
        fail("R-190 fill allocation trace is nondeterministic");
    }
    for (
        std::uint64_t ordinal = 1U;
        ordinal <= r190_fill_allocations;
        ++ordinal
    ) {
        const std::uint64_t first_count = run_r190_fill(ordinal);
        const std::uint64_t first_hash = resource.trace_hash();
        if (
            run_r190_fill(ordinal) != first_count
            || resource.trace_hash() != first_hash
        ) {
            fail("R-190 fill failed-ordinal trace changed");
        }
        static_cast<void>(run_r190_fill(0U));
    }

    const auto run_v3_preflight = [&](std::uint64_t fail_ordinal) {
        resource.reset(fail_ordinal);
        resonith_partial_path_report_v3 report{};
        report.struct_size = sizeof(report);
        report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        resonith::internal::partial_graph_set_test_upstream_resource(&resource);
        const resonith_status status = resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            canonical_edges.data(),
            canonical_edge_count,
            &graph,
            &path,
            nullptr,
            0U,
            nullptr,
            0U,
            &report
        );
        resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
        if (!resource.healthy() || !exact_report_memory(report, resource)) {
            fail("R-191 preflight memory provenance mismatch");
        }
        if (
            fail_ordinal == 0U
                ? status != RESONITH_STATUS_OK
                : status != RESONITH_STATUS_OUT_OF_MEMORY
                    || report.termination
                        != RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM
                    || report.written_path_count != 0U
                    || report.written_entry_count != 0U
        ) {
            fail("R-191 preflight ordinal status/publication mismatch");
        }
        return resource.allocation_count();
    };

    const std::uint64_t v3_preflight_allocations = run_v3_preflight(0U);
    const std::uint64_t v3_preflight_hash = resource.trace_hash();
    if (
        v3_preflight_allocations == 0U
        || run_v3_preflight(0U) != v3_preflight_allocations
        || resource.trace_hash() != v3_preflight_hash
    ) {
        fail("R-191 preflight allocation trace is nondeterministic");
    }
    for (
        std::uint64_t ordinal = 1U;
        ordinal <= v3_preflight_allocations;
        ++ordinal
    ) {
        const std::uint64_t first_count = run_v3_preflight(ordinal);
        const std::uint64_t first_hash = resource.trace_hash();
        if (
            run_v3_preflight(ordinal) != first_count
            || resource.trace_hash() != first_hash
        ) {
            fail("R-191 preflight failed-ordinal trace changed");
        }
        static_cast<void>(run_v3_preflight(0U));
    }

    std::copy(
        std::begin(canonical_preflight.input_fingerprint),
        std::end(canonical_preflight.input_fingerprint),
        path.expected_input_fingerprint
    );
    const auto run_v3_fill = [&](std::uint64_t fail_ordinal) {
        resource.reset(fail_ordinal);
        std::array<resonith_partial_path_v3, 24U> output_paths{};
        std::array<resonith_partial_path_entry_v3, 64U> output_entries{};
        std::memset(output_paths.data(), 0xa5, sizeof(output_paths));
        std::memset(output_entries.data(), 0x5a, sizeof(output_entries));
        const auto paths_before = output_paths;
        const auto entries_before = output_entries;
        resonith_partial_path_report_v3 report{};
        report.struct_size = sizeof(report);
        report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        resonith::internal::partial_graph_set_test_upstream_resource(&resource);
        const resonith_status status = resonith_partial_graph_paths_cpu_v3(
            &resolution,
            1U,
            observations.data(),
            observations.size(),
            canonical_edges.data(),
            canonical_edge_count,
            &graph,
            &path,
            output_paths.data(),
            output_paths.size(),
            output_entries.data(),
            output_entries.size(),
            &report
        );
        resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
        if (!resource.healthy() || !exact_report_memory(report, resource)) {
            fail("R-191 fill memory provenance mismatch");
        }
        if (fail_ordinal == 0U) {
            if (
                status != RESONITH_STATUS_OK
                || report.written_path_count != 8U
                || report.written_entry_count != 24U
            ) {
                fail("R-191 fill baseline failed");
            }
        } else if (
            status != RESONITH_STATUS_OUT_OF_MEMORY
            || report.termination
                != RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM
            || report.written_path_count != 0U
            || report.written_entry_count != 0U
            || std::memcmp(
                output_paths.data(),
                paths_before.data(),
                sizeof(output_paths)
            ) != 0
            || std::memcmp(
                output_entries.data(),
                entries_before.data(),
                sizeof(output_entries)
            ) != 0
        ) {
            fail("R-191 fill ordinal transaction mismatch");
        }
        return resource.allocation_count();
    };

    const std::uint64_t v3_fill_allocations = run_v3_fill(0U);
    const std::uint64_t v3_fill_hash = resource.trace_hash();
    if (
        v3_fill_allocations == 0U
        || run_v3_fill(0U) != v3_fill_allocations
        || resource.trace_hash() != v3_fill_hash
    ) {
        fail("R-191 fill allocation trace is nondeterministic");
    }
    for (
        std::uint64_t ordinal = 1U;
        ordinal <= v3_fill_allocations;
        ++ordinal
    ) {
        const std::uint64_t first_count = run_v3_fill(ordinal);
        const std::uint64_t first_hash = resource.trace_hash();
        if (
            run_v3_fill(ordinal) != first_count
            || resource.trace_hash() != first_hash
        ) {
            fail("R-191 fill failed-ordinal trace changed");
        }
        static_cast<void>(run_v3_fill(0U));
    }

    const std::uint64_t combined_hash =
        r190_preflight_hash
        ^ (r190_fill_hash << 1U)
        ^ (v3_preflight_hash << 2U)
        ^ (v3_fill_hash << 3U);
    std::printf(
        "{\"schema\":\"resonith-r202-allocation-ordinal-1\","
        "\"r190_preflight\":%llu,\"r190_fill\":%llu,"
        "\"v3_preflight\":%llu,\"v3_fill\":%llu,"
        "\"campaign_calls\":%llu,\"trace_hash\":\"%016llx\","
        "\"terminal_live_allocations\":0,\"device_bytes\":0}\n",
        static_cast<unsigned long long>(r190_preflight_allocations),
        static_cast<unsigned long long>(r190_fill_allocations),
        static_cast<unsigned long long>(v3_preflight_allocations),
        static_cast<unsigned long long>(v3_fill_allocations),
        static_cast<unsigned long long>(
            8U
            + 3U * (
                r190_preflight_allocations
                + r190_fill_allocations
                + v3_preflight_allocations
                + v3_fill_allocations
            )
        ),
        static_cast<unsigned long long>(combined_hash)
    );
    return 0;
}
