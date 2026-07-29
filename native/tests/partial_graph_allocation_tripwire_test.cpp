#include "resonith/partial_graph.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory_resource>
#include <new>

#if defined(_WIN32)
#include <malloc.h>
#endif

namespace {

thread_local bool upstream_permitted = false;
bool tripwire_armed = false;
std::uint64_t forbidden_allocations = 0U;
std::uint64_t permitted_allocations = 0U;

void* allocate_unaligned(std::size_t size) {
    if (tripwire_armed) {
        if (!upstream_permitted) {
            ++forbidden_allocations;
            throw std::bad_alloc{};
        }
        ++permitted_allocations;
    }
    if (void* pointer = std::malloc(size == 0U ? 1U : size)) {
        return pointer;
    }
    throw std::bad_alloc{};
}

void* allocate_aligned(std::size_t size, std::size_t alignment) {
    if (tripwire_armed) {
        if (!upstream_permitted) {
            ++forbidden_allocations;
            throw std::bad_alloc{};
        }
        ++permitted_allocations;
    }
#if defined(_WIN32)
    if (void* pointer = _aligned_malloc(size == 0U ? 1U : size, alignment)) {
        return pointer;
    }
#else
    void* pointer = nullptr;
    if (
        posix_memalign(
            &pointer,
            alignment,
            size == 0U ? alignment : size
        ) == 0
    ) {
        return pointer;
    }
#endif
    throw std::bad_alloc{};
}

void release_aligned(void* pointer) noexcept {
#if defined(_WIN32)
    _aligned_free(pointer);
#else
    std::free(pointer);
#endif
}

void set_upstream_permit(bool permitted) noexcept {
    upstream_permitted = permitted;
}

class tripwire_upstream_resource final : public std::pmr::memory_resource {
private:
    void* do_allocate(std::size_t bytes, std::size_t alignment) override {
        if (alignment <= alignof(std::max_align_t)) {
            return ::operator new(bytes);
        }
        return ::operator new(bytes, std::align_val_t{alignment});
    }

    void do_deallocate(
        void* pointer,
        std::size_t,
        std::size_t alignment
    ) override {
        if (alignment <= alignof(std::max_align_t)) {
            ::operator delete(pointer);
            return;
        }
        ::operator delete(pointer, std::align_val_t{alignment});
    }

    bool do_is_equal(
        const std::pmr::memory_resource& other
    ) const noexcept override {
        return this == &other;
    }
};

[[noreturn]] void fail(const char* message) {
    tripwire_armed = false;
    std::fprintf(stderr, "partial_graph_allocation_tripwire_test: %s\n", message);
    std::exit(1);
}

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

}  // namespace

void* operator new(std::size_t size) {
    return allocate_unaligned(size);
}

void* operator new[](std::size_t size) {
    return allocate_unaligned(size);
}

void* operator new(std::size_t size, const std::nothrow_t&) noexcept {
    try {
        return allocate_unaligned(size);
    } catch (...) {
        return nullptr;
    }
}

void* operator new[](std::size_t size, const std::nothrow_t&) noexcept {
    try {
        return allocate_unaligned(size);
    } catch (...) {
        return nullptr;
    }
}

void* operator new(std::size_t size, std::align_val_t alignment) {
    return allocate_aligned(size, static_cast<std::size_t>(alignment));
}

void* operator new[](
    std::size_t size,
    std::align_val_t alignment
) {
    return allocate_aligned(size, static_cast<std::size_t>(alignment));
}

void* operator new(
    std::size_t size,
    std::align_val_t alignment,
    const std::nothrow_t&
) noexcept {
    try {
        return allocate_aligned(size, static_cast<std::size_t>(alignment));
    } catch (...) {
        return nullptr;
    }
}

void* operator new[](
    std::size_t size,
    std::align_val_t alignment,
    const std::nothrow_t&
) noexcept {
    try {
        return allocate_aligned(size, static_cast<std::size_t>(alignment));
    } catch (...) {
        return nullptr;
    }
}

void operator delete(void* pointer) noexcept {
    std::free(pointer);
}

void operator delete[](void* pointer) noexcept {
    std::free(pointer);
}

void operator delete(void* pointer, std::size_t) noexcept {
    std::free(pointer);
}

void operator delete[](void* pointer, std::size_t) noexcept {
    std::free(pointer);
}

void operator delete(void* pointer, const std::nothrow_t&) noexcept {
    std::free(pointer);
}

void operator delete[](void* pointer, const std::nothrow_t&) noexcept {
    std::free(pointer);
}

void operator delete(void* pointer, std::align_val_t) noexcept {
    release_aligned(pointer);
}

void operator delete[](void* pointer, std::align_val_t) noexcept {
    release_aligned(pointer);
}

void operator delete(
    void* pointer,
    std::size_t,
    std::align_val_t
) noexcept {
    release_aligned(pointer);
}

void operator delete[](
    void* pointer,
    std::size_t,
    std::align_val_t
) noexcept {
    release_aligned(pointer);
}

void operator delete(
    void* pointer,
    std::align_val_t,
    const std::nothrow_t&
) noexcept {
    release_aligned(pointer);
}

void operator delete[](
    void* pointer,
    std::align_val_t,
    const std::nothrow_t&
) noexcept {
    release_aligned(pointer);
}

namespace resonith::internal {
void partial_graph_set_test_allocation_permit_callback(
    void (*callback)(bool) noexcept
) noexcept;
void partial_graph_set_test_upstream_resource(
    std::pmr::memory_resource* resource
) noexcept;
}

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

    std::array<resonith_partial_edge, 16U> edges{};
    std::array<resonith_partial_path_v3, 24U> paths{};
    std::array<resonith_partial_path_entry_v3, 64U> entries{};

    resonith::internal::partial_graph_set_test_allocation_permit_callback(
        &set_upstream_permit
    );
    tripwire_upstream_resource tripwire_upstream;
    resonith::internal::partial_graph_set_test_upstream_resource(
        &tripwire_upstream
    );
    tripwire_armed = true;
    for (std::uint32_t pass = 0U; pass < 2U; ++pass) {
        const std::uint64_t before_r190_preflight = permitted_allocations;
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
            || permitted_allocations <= before_r190_preflight
        ) {
            fail("R-190 preflight failed under armed tripwire");
        }
        const std::uint64_t before_r190_fill = permitted_allocations;
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
            || permitted_allocations <= before_r190_fill
        ) {
            fail("R-190 fill failed under armed tripwire");
        }

        const std::uint64_t before_r191_preflight = permitted_allocations;
        std::memset(
            path.expected_input_fingerprint,
            0,
            sizeof(path.expected_input_fingerprint)
        );
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
            || preflight.reserved_host_bytes
                < preflight.committed_host_bytes
            || preflight.committed_host_bytes
                < preflight.peak_live_host_bytes
            || preflight.reserved_device_bytes != 0U
            || preflight.committed_device_bytes != 0U
            || preflight.peak_live_device_bytes != 0U
            || permitted_allocations <= before_r191_preflight
        ) {
            fail("R-191 preflight failed under armed tripwire");
        }
        std::memcpy(
            path.expected_input_fingerprint,
            preflight.input_fingerprint,
            sizeof(path.expected_input_fingerprint)
        );
        resonith_partial_path_report_v3 fill{};
        fill.struct_size = sizeof(fill);
        fill.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        const std::uint64_t before_r191_fill = permitted_allocations;
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
            || fill.written_path_count != 8U
            || fill.written_entry_count != 24U
            || fill.reserved_device_bytes != 0U
            || fill.committed_device_bytes != 0U
            || fill.peak_live_device_bytes != 0U
            || permitted_allocations <= before_r191_fill
        ) {
            fail("R-191 fill failed under armed tripwire");
        }
    }
    tripwire_armed = false;
    resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
    resonith::internal::partial_graph_set_test_allocation_permit_callback(
        nullptr
    );
    if (
        forbidden_allocations != 0U
        || permitted_allocations == 0U
        || upstream_permitted
    ) {
        fail("project-controlled allocation escaped the counted resource");
    }
    std::printf(
        "{\"schema\":\"resonith-r201-allocation-tripwire-1\","
        "\"r190_passes\":2,\"r191_passes\":2,"
        "\"permitted_allocations\":%llu,"
        "\"forbidden_allocations\":0,\"device_bytes\":0}\n",
        static_cast<unsigned long long>(permitted_allocations)
    );
    return 0;
}
