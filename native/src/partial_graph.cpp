#include "resonith/partial_graph.h"

#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <limits>
#include <map>
#include <memory_resource>
#include <new>
#include <set>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr std::uint32_t ratio_fraction_bits = 16U;
constexpr std::uint32_t score_fraction_bits = 8U;
constexpr std::uint64_t ratio_integer_cap = 65535U;

template <typename Value>
bool reserved_zero(const Value& value) noexcept {
    for (const std::uint32_t item : value.reserved) {
        if (item != 0U) {
            return false;
        }
    }
    return true;
}

std::int64_t saturating_add(
    std::int64_t left,
    std::int64_t right,
    std::int64_t limit
) noexcept {
    if (right > 0 && left > limit - right) {
        return limit;
    }
    if (right < 0 && left < -limit - right) {
        return -limit;
    }
    return std::clamp(left + right, -limit, limit);
}

std::uint64_t unsigned_abs(std::int64_t value) noexcept {
    if (value >= 0) {
        return static_cast<std::uint64_t>(value);
    }
    return static_cast<std::uint64_t>(-(value + 1)) + 1U;
}

std::uint64_t fractional_divide_q16(
    std::uint64_t remainder,
    std::uint64_t denominator
) noexcept {
    std::uint64_t fraction = 0U;
    for (std::uint32_t bit = 0U; bit < ratio_fraction_bits; ++bit) {
        fraction <<= 1U;
        if (remainder >= denominator - remainder) {
            remainder -= denominator - remainder;
            fraction |= 1U;
        } else {
            remainder *= 2U;
        }
    }
    return fraction;
}

std::uint64_t ratio_q16(
    std::uint64_t numerator,
    std::uint64_t denominator
) noexcept {
    if (denominator == 0U) {
        return (ratio_integer_cap << ratio_fraction_bits)
            | ((1U << ratio_fraction_bits) - 1U);
    }
    const std::uint64_t integer = numerator / denominator;
    if (integer >= ratio_integer_cap) {
        return (ratio_integer_cap << ratio_fraction_bits)
            | ((1U << ratio_fraction_bits) - 1U);
    }
    const std::uint64_t remainder = numerator % denominator;
    return (integer << ratio_fraction_bits)
        | fractional_divide_q16(remainder, denominator);
}

std::int32_t log2_one_plus_ratio_q8(
    std::uint64_t numerator,
    std::uint64_t denominator
) noexcept {
    const std::uint64_t value_q16 =
        (1U << ratio_fraction_bits) + ratio_q16(numerator, denominator);
    const std::uint32_t most_significant =
        static_cast<std::uint32_t>(std::bit_width(value_q16)) - 1U;
    const std::int32_t integer_part =
        static_cast<std::int32_t>(most_significant)
        - static_cast<std::int32_t>(ratio_fraction_bits);
    std::uint64_t normalized_q31 = most_significant <= 31U
        ? value_q16 << (31U - most_significant)
        : value_q16 >> (most_significant - 31U);
    std::uint32_t fractional = 0U;
    for (std::uint32_t bit = 0U; bit < score_fraction_bits; ++bit) {
        const std::uint64_t product =
            normalized_q31 * normalized_q31;
        std::uint64_t squared_q31 = product >> 31U;
        fractional <<= 1U;
        if (squared_q31 >= (1ULL << 32U)) {
            squared_q31 >>= 1U;
            fractional |= 1U;
        }
        normalized_q31 = squared_q31;
    }
    return integer_part * static_cast<std::int32_t>(
        1U << score_fraction_bits
    ) + static_cast<std::int32_t>(fractional);
}

std::int32_t signed_log_amplitude_ratio_q8(
    std::uint32_t target,
    std::uint32_t source
) noexcept {
    if (target == source) {
        return 0;
    }
    if (source == 0U) {
        return target == 0U
            ? 0
            : std::numeric_limits<std::int32_t>::max() / 4;
    }
    if (target == 0U) {
        return std::numeric_limits<std::int32_t>::min() / 4;
    }
    if (target > source) {
        return log2_one_plus_ratio_q8(
            static_cast<std::uint64_t>(target - source),
            source
        );
    }
    return -log2_one_plus_ratio_q8(
        static_cast<std::uint64_t>(source - target),
        target
    );
}

std::uint32_t phase_advance_u32(
    std::uint32_t source_step,
    std::uint32_t target_step,
    std::uint64_t center_delta
) noexcept {
    const std::uint64_t step_sum =
        static_cast<std::uint64_t>(source_step) + target_step;
    const std::uint64_t half_sum = step_sum >> 1U;
    const std::uint32_t product = static_cast<std::uint32_t>(
        static_cast<std::uint64_t>(
            static_cast<std::uint32_t>(half_sum)
        ) * static_cast<std::uint32_t>(center_delta)
    );
    if ((step_sum & 1U) == 0U) {
        return product;
    }
    const std::uint32_t rounded_half_delta =
        static_cast<std::uint32_t>(
            (center_delta >> 1U) + (center_delta & 1U)
        );
    return product + rounded_half_delta;
}

std::uint32_t phase_error_u31(
    const resonith_partial_observation& source,
    const resonith_partial_observation& target
) noexcept {
    const std::uint64_t delta = target.center_sample - source.center_sample;
    const std::uint32_t expected = source.phase_turn_u32
        + phase_advance_u32(
            source.phase_step_u32,
            target.phase_step_u32,
            delta
        );
    const std::int32_t wrapped = static_cast<std::int32_t>(
        target.phase_turn_u32 - expected
    );
    if (wrapped == std::numeric_limits<std::int32_t>::min()) {
        return 1U << 31U;
    }
    return static_cast<std::uint32_t>(
        wrapped < 0 ? -wrapped : wrapped
    );
}

struct resolution_record {
    std::uint32_t fft_samples;
    std::uint32_t hop_samples;
};

struct ranked_target {
    std::size_t observation_index;
    std::int32_t normalized_distance_q8;
    std::int32_t neighbor_priority_q8;
    std::uint64_t observation_id;
};

class managed_profile_bound final : public std::bad_alloc {};
class environmental_out_of_memory final : public std::bad_alloc {};

class counting_memory_resource final : public std::pmr::memory_resource {
public:
    explicit counting_memory_resource(
        std::uint64_t limit,
        std::pmr::memory_resource* upstream =
            std::pmr::new_delete_resource()
    ) noexcept
        : limit_(limit), upstream_(upstream) {}

    [[nodiscard]] std::uint64_t peak_bytes() const noexcept {
        return peak_;
    }

private:
    void* do_allocate(std::size_t bytes, std::size_t alignment) override {
        if (
            bytes > limit_
            || live_ > limit_ - static_cast<std::uint64_t>(bytes)
        ) {
            throw managed_profile_bound{};
        }
        void* result = nullptr;
        try {
            result = upstream_->allocate(bytes, alignment);
        } catch (const std::bad_alloc&) {
            throw environmental_out_of_memory{};
        }
        live_ += bytes;
        peak_ = std::max(peak_, live_);
        return result;
    }

    void do_deallocate(
        void* pointer,
        std::size_t bytes,
        std::size_t alignment
    ) override {
        upstream_->deallocate(pointer, bytes, alignment);
        live_ -= bytes;
    }

    bool do_is_equal(
        const std::pmr::memory_resource& other
    ) const noexcept override {
        return this == &other;
    }

    std::uint64_t limit_;
    std::pmr::memory_resource* upstream_;
    std::uint64_t live_ = 0U;
    std::uint64_t peak_ = 0U;
};

constexpr std::uint64_t maximum_edge_api_managed_bytes = 16ULL << 30U;

bool checked_add_scaled(
    std::uint64_t* total,
    std::uint64_t count,
    std::uint64_t bytes_per_item
) noexcept {
    if (
        bytes_per_item != 0U
        && count > (
            std::numeric_limits<std::uint64_t>::max() - *total
        ) / bytes_per_item
    ) {
        return false;
    }
    *total += count * bytes_per_item;
    return *total <= maximum_edge_api_managed_bytes;
}

bool edge_api_managed_limit(
    std::size_t resolution_count,
    std::size_t observation_count,
    std::uint64_t maximum_edge_records,
    std::uint64_t* limit
) noexcept {
    std::uint64_t total = 64U << 10U;
    if (
        !checked_add_scaled(&total, resolution_count, 512U)
        || !checked_add_scaled(&total, observation_count, 1024U)
        || !checked_add_scaled(
            &total,
            maximum_edge_records,
            sizeof(resonith_partial_edge)
        )
    ) {
        return false;
    }
    *limit = total;
    return true;
}

template <typename ResolutionTable>
bool valid_manifest(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_graph_manifest& manifest,
    ResolutionTable* table
) {
    if (
        manifest.struct_size != sizeof(manifest)
        || manifest.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
        || manifest.sample_rate == 0U
        || manifest.sample_rate > 384000U
        || manifest.resolution_count != resolution_count
        || resolution_count == 0U
        || resolution_count > RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS
        || manifest.gap_count == 0U
        || manifest.gap_count > RESONITH_PARTIAL_GRAPH_MAX_GAPS
        || manifest.neighbors_per_gap == 0U
        || manifest.neighbors_per_gap > 16U
        || manifest.cycle_offset_count == 0U
        || manifest.cycle_offset_count
            > RESONITH_PARTIAL_GRAPH_MAX_CYCLE_OFFSETS
        || manifest.minimum_track_observations < 2U
        || manifest.maximum_frequency_jump_hz_q20 < 0
        || manifest.maximum_frequency_slope_hz_per_sample_q20 < 0
        || manifest.score_saturation < 1024
        || manifest.maximum_edge_records == 0U
        || manifest.maximum_path_hypotheses == 0U
        || manifest.exact_set_candidate_limit == 0U
        || !reserved_zero(manifest)
    ) {
        return false;
    }
    for (std::uint32_t index = 0U; index < manifest.gap_count; ++index) {
        if (
            manifest.gaps[index] == 0U
            || (
                index != 0U
                && manifest.gaps[index] <= manifest.gaps[index - 1U]
            )
        ) {
            return false;
        }
    }
    bool zero_cycle = false;
    for (
        std::uint32_t index = 0U;
        index < manifest.cycle_offset_count;
        ++index
    ) {
        zero_cycle = zero_cycle || manifest.cycle_offsets[index] == 0;
        if (
            index != 0U
            && manifest.cycle_offsets[index]
                <= manifest.cycle_offsets[index - 1U]
        ) {
            return false;
        }
    }
    if (!zero_cycle) {
        return false;
    }
    for (std::size_t index = 0U; index < resolution_count; ++index) {
        const resonith_partial_resolution& item = resolutions[index];
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || item.fft_samples < 128U
            || (item.fft_samples & (item.fft_samples - 1U)) != 0U
            || item.hop_samples == 0U
            || item.hop_samples > item.fft_samples / 2U
            || !reserved_zero(item)
            || table->contains(item.resolution_id)
        ) {
            return false;
        }
        table->emplace(
            item.resolution_id,
            resolution_record{item.fft_samples, item.hop_samples}
        );
    }
    return true;
}

template <typename ResolutionTable, typename IdVector>
bool valid_observations(
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    std::uint32_t sample_rate,
    const ResolutionTable& resolutions,
    IdVector* ids
) {
    ids->reserve(observation_count);
    const std::int64_t nyquist_q20 =
        static_cast<std::int64_t>(sample_rate / 2U) << 20U;
    for (std::size_t index = 0U; index < observation_count; ++index) {
        const resonith_partial_observation& item = observations[index];
        const auto resolution = resolutions.find(item.resolution_id);
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || item.frequency_hz_q20 < 0
            || item.frequency_hz_q20 > nyquist_q20
            || item.phase_uncertainty_u31 > (1U << 31U)
            || resolution == resolutions.end()
            || item.center_sample
                != static_cast<std::uint64_t>(item.frame_index)
                    * resolution->second.hop_samples
            || !reserved_zero(item)
        ) {
            return false;
        }
        ids->push_back(item.observation_id);
    }
    std::sort(ids->begin(), ids->end());
    return std::adjacent_find(ids->begin(), ids->end()) == ids->end();
}

std::int64_t maximum_frequency_distance(
    const resonith_partial_graph_manifest& manifest,
    std::uint64_t center_delta
) noexcept {
    const std::uint64_t slope =
        static_cast<std::uint64_t>(
            manifest.maximum_frequency_slope_hz_per_sample_q20
        );
    const std::uint64_t limit =
        static_cast<std::uint64_t>(
            std::numeric_limits<std::int64_t>::max()
        );
    const std::uint64_t product = (
        center_delta != 0U && slope > limit / center_delta
    )
        ? limit
        : slope * center_delta;
    const std::uint64_t jump = static_cast<std::uint64_t>(
        manifest.maximum_frequency_jump_hz_q20
    );
    return static_cast<std::int64_t>(
        product > limit - jump ? limit : product + jump
    );
}

resonith_partial_edge score_edge(
    std::uint64_t candidate_id,
    const resonith_partial_observation& source,
    const resonith_partial_observation& target,
    std::uint32_t gap,
    std::int32_t cycle_offset,
    const resonith_partial_graph_manifest& manifest
) noexcept {
    const std::int64_t frequency_delta =
        target.frequency_hz_q20 - source.frequency_hz_q20;
    const std::uint64_t frequency_uncertainty =
        source.frequency_uncertainty_hz_q20
        > std::numeric_limits<std::uint64_t>::max()
            - target.frequency_uncertainty_hz_q20
        ? std::numeric_limits<std::uint64_t>::max()
        : source.frequency_uncertainty_hz_q20
            + target.frequency_uncertainty_hz_q20;
    const std::int32_t frequency_cost = log2_one_plus_ratio_q8(
        unsigned_abs(frequency_delta),
        std::max<std::uint64_t>(1U, frequency_uncertainty)
    );
    const std::int32_t amplitude_log = signed_log_amplitude_ratio_q8(
        target.normalized_amplitude_q16,
        source.normalized_amplitude_q16
    );
    const std::uint64_t scaled_amplitude = unsigned_abs(amplitude_log) * 8U;
    const std::int32_t amplitude_cost = log2_one_plus_ratio_q8(
        scaled_amplitude,
        1U << score_fraction_bits
    );
    const bool phase_usable = (
        source.flags & RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
    ) != 0U && (
        target.flags & RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
    ) != 0U;
    const std::uint32_t phase_error = phase_usable
        ? phase_error_u31(source, target)
        : 0U;
    const std::uint64_t phase_uncertainty =
        static_cast<std::uint64_t>(source.phase_uncertainty_u31)
        + target.phase_uncertainty_u31;
    const std::int32_t phase_cost = phase_usable
        ? log2_one_plus_ratio_q8(
            phase_error,
            std::max<std::uint64_t>(1U, phase_uncertainty)
        )
        : 0;
    const std::int32_t gap_cost = log2_one_plus_ratio_q8(gap, 1U);
    const std::int32_t cycle_cost = log2_one_plus_ratio_q8(
        unsigned_abs(cycle_offset),
        1U
    );
    std::int64_t continuity = 0;
    for (const std::int32_t item : {
        frequency_cost,
        amplitude_cost,
        phase_cost,
        gap_cost,
        cycle_cost,
    }) {
        continuity = saturating_add(
            continuity,
            item,
            manifest.score_saturation
        );
    }
    const std::int64_t program = saturating_add(
        manifest.continuation_base_bits_q8,
        continuity,
        manifest.score_saturation
    );
    return resonith_partial_edge{
        sizeof(resonith_partial_edge),
        RESONITH_PARTIAL_GRAPH_ABI_VERSION,
        candidate_id,
        source.observation_id,
        target.observation_id,
        target.center_sample - source.center_sample,
        frequency_delta,
        gap,
        cycle_offset,
        phase_error,
        static_cast<std::int32_t>(std::clamp<std::int64_t>(
            continuity,
            std::numeric_limits<std::int32_t>::min(),
            std::numeric_limits<std::int32_t>::max()
        )),
        static_cast<std::int32_t>(std::clamp<std::int64_t>(
            program,
            std::numeric_limits<std::int32_t>::min(),
            std::numeric_limits<std::int32_t>::max()
        )),
        phase_usable ? 1U : 0U,
        {0U, 0U},
    };
}

template <typename Sink, typename ResolutionTable, typename WorkCharge>
resonith_status enumerate_edges_stream(
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_graph_manifest& manifest,
    const ResolutionTable& resolutions,
    std::pmr::memory_resource* memory,
    Sink&& sink,
    WorkCharge&& charge_work,
    std::size_t* edge_count
) {
    charge_work(observation_count);
    std::pmr::vector<std::size_t> canonical_observation_order(
        observation_count,
        memory
    );
    for (std::size_t index = 0U; index < observation_count; ++index) {
        canonical_observation_order[index] = index;
    }
    std::sort(
        canonical_observation_order.begin(),
        canonical_observation_order.end(),
        [observations, &charge_work](
            std::size_t left_index,
            std::size_t right_index
        ) {
            charge_work(1U);
            const resonith_partial_observation& left = observations[left_index];
            const resonith_partial_observation& right = observations[right_index];
            return std::tie(
                left.center_sample,
                left.resolution_id,
                left.detector_id,
                left.frequency_hz_q20,
                left.observation_id
            ) < std::tie(
                right.center_sample,
                right.resolution_id,
                right.detector_id,
                right.frequency_hz_q20,
                right.observation_id
            );
        }
    );

    std::uint64_t candidate_id = 0U;
    for (const std::size_t source_index : canonical_observation_order) {
        charge_work(1U);
        const resonith_partial_observation& source = observations[source_index];
        if (
            source.flags
            & RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE
        ) {
            const resolution_record resolution =
                resolutions.at(source.resolution_id);
            for (
                std::uint32_t gap_index = 0U;
                gap_index < manifest.gap_count;
                ++gap_index
            ) {
                charge_work(1U);
                const std::uint32_t gap = manifest.gaps[gap_index];
                const std::uint64_t delta =
                    static_cast<std::uint64_t>(gap)
                    * resolution.hop_samples;
                if (
                    source.center_sample
                    > std::numeric_limits<std::uint64_t>::max() - delta
                ) {
                    continue;
                }
                const std::uint64_t target_center =
                    source.center_sample + delta;
                const std::int64_t maximum_distance =
                    maximum_frequency_distance(manifest, delta);
                std::pmr::vector<ranked_target> targets(memory);
                for (const std::size_t target_index : canonical_observation_order) {
                    charge_work(1U);
                    const resonith_partial_observation& target =
                        observations[target_index];
                    if (
                        target.resolution_id != source.resolution_id
                        || target.detector_id != source.detector_id
                        || target.center_sample != target_center
                        || (
                            target.flags
                            & RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE
                        ) == 0U
                    ) {
                        continue;
                    }
                    const std::int64_t frequency_delta =
                        target.frequency_hz_q20 - source.frequency_hz_q20;
                    if (
                        unsigned_abs(frequency_delta)
                        > static_cast<std::uint64_t>(maximum_distance)
                    ) {
                        continue;
                    }
                    const std::uint64_t uncertainty =
                        source.frequency_uncertainty_hz_q20
                        > std::numeric_limits<std::uint64_t>::max()
                            - target.frequency_uncertainty_hz_q20
                        ? std::numeric_limits<std::uint64_t>::max()
                        : source.frequency_uncertainty_hz_q20
                            + target.frequency_uncertainty_hz_q20;
                    targets.push_back(ranked_target{
                        target_index,
                        log2_one_plus_ratio_q8(
                            unsigned_abs(frequency_delta),
                            std::max<std::uint64_t>(1U, uncertainty)
                        ),
                        target.neighbor_priority_q8,
                        target.observation_id,
                    });
                }
                std::sort(
                    targets.begin(),
                    targets.end(),
                    [&charge_work](
                        const ranked_target& left,
                        const ranked_target& right
                    ) {
                        charge_work(1U);
                        if (
                            left.normalized_distance_q8
                            != right.normalized_distance_q8
                        ) {
                            return left.normalized_distance_q8
                                < right.normalized_distance_q8;
                        }
                        if (
                            left.neighbor_priority_q8
                            != right.neighbor_priority_q8
                        ) {
                            return left.neighbor_priority_q8
                                > right.neighbor_priority_q8;
                        }
                        return left.observation_id < right.observation_id;
                    }
                );
                if (targets.size() > manifest.neighbors_per_gap) {
                    targets.resize(manifest.neighbors_per_gap);
                }
                for (const ranked_target& ranked : targets) {
                    const resonith_partial_observation& target =
                        observations[ranked.observation_index];
                    for (
                        std::uint32_t cycle_index = 0U;
                        cycle_index < manifest.cycle_offset_count;
                        ++cycle_index
                    ) {
                        charge_work(1U);
                        if (
                            candidate_id >= manifest.maximum_edge_records
                            || candidate_id
                                == std::numeric_limits<std::uint64_t>::max()
                        ) {
                            return RESONITH_STATUS_PROFILE_BOUND;
                        }
                        const resonith_partial_edge edge = score_edge(
                            candidate_id,
                            source,
                            target,
                            gap,
                            manifest.cycle_offsets[cycle_index],
                            manifest
                        );
                        const resonith_status status = sink(edge);
                        if (status != RESONITH_STATUS_OK) {
                            return status;
                        }
                        ++candidate_id;
                    }
                }
            }
        }
    }
    if (
        candidate_id
        > static_cast<std::uint64_t>(
            std::numeric_limits<std::size_t>::max()
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    *edge_count = static_cast<std::size_t>(candidate_id);
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_partial_graph_edges_cpu(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_graph_manifest* manifest,
    resonith_partial_edge* output,
    std::size_t output_capacity,
    std::size_t* output_count
) {
    if (
        resolutions == nullptr
        || observations == nullptr
        || manifest == nullptr
        || output_count == nullptr
        || (output == nullptr && output_capacity != 0U)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *output_count = 0U;
    std::uint64_t managed_limit = 0U;
    if (
        manifest->struct_size != sizeof(*manifest)
        || manifest->abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        !edge_api_managed_limit(
            resolution_count,
            observation_count,
            manifest->maximum_edge_records,
            &managed_limit
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    try {
        counting_memory_resource managed_memory(managed_limit);
        std::pmr::map<std::uint32_t, resolution_record> resolution_table(
            &managed_memory
        );
        std::pmr::vector<std::uint64_t> observation_ids(&managed_memory);
        if (
            !valid_manifest(
                resolutions,
                resolution_count,
                *manifest,
                &resolution_table
            )
            || !valid_observations(
                observations,
                observation_count,
                manifest->sample_rate,
                resolution_table,
                &observation_ids
            )
        ) {
            return RESONITH_STATUS_INVALID_ARGUMENT;
        }

        const auto no_work_limit = [](std::uint64_t) {};
        std::size_t required = 0U;
        const resonith_status count_status = enumerate_edges_stream(
            observations,
            observation_count,
            *manifest,
            resolution_table,
            &managed_memory,
            [](const resonith_partial_edge&) {
                return RESONITH_STATUS_OK;
            },
            no_work_limit,
            &required
        );
        if (count_status != RESONITH_STATUS_OK) {
            return count_status;
        }
        *output_count = required;
        if (output == nullptr) {
            return RESONITH_STATUS_OK;
        }
        if (output_capacity < required) {
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }

        std::pmr::vector<resonith_partial_edge> staged(&managed_memory);
        staged.reserve(required);
        std::size_t verified_count = 0U;
        const resonith_status fill_status = enumerate_edges_stream(
            observations,
            observation_count,
            *manifest,
            resolution_table,
            &managed_memory,
            [&staged](const resonith_partial_edge& edge) {
                staged.push_back(edge);
                return RESONITH_STATUS_OK;
            },
            no_work_limit,
            &verified_count
        );
        if (
            fill_status != RESONITH_STATUS_OK
            || verified_count != required
            || staged.size() != required
        ) {
            return fill_status == RESONITH_STATUS_OK
                ? RESONITH_STATUS_INVALID_ARGUMENT
                : fill_status;
        }
        std::copy(staged.begin(), staged.end(), output);
        return RESONITH_STATUS_OK;
    } catch (const managed_profile_bound&) {
        return RESONITH_STATUS_PROFILE_BOUND;
    } catch (const environmental_out_of_memory&) {
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (const std::bad_alloc&) {
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (...) {
        return RESONITH_STATUS_MALFORMED;
    }
}

namespace {

constexpr std::uint64_t birth_edge_id =
    std::numeric_limits<std::uint64_t>::max();
constexpr std::uint32_t edge_phase_usable = 1U;

struct path_state {
    std::vector<std::uint64_t> observation_ids;
    std::vector<std::uint64_t> incoming_edge_ids;
    std::vector<std::int32_t> second_order_costs;
    std::int64_t continuity_cost = 0;
    std::int64_t potential = 0;
    std::int64_t uncertainty_penalty = 0;
    std::int64_t provisional_program_cost = 0;
    std::uint64_t phase_error_sum = 0U;
    std::uint32_t phase_error_count = 0U;
};

using path_key = std::pair<
    std::vector<std::uint64_t>,
    std::vector<std::uint64_t>
>;

struct path_output {
    explicit path_output(
        std::pmr::memory_resource* memory = std::pmr::new_delete_resource()
    )
        : paths(memory), entries(memory) {}

    std::pmr::vector<resonith_partial_path> paths;
    std::pmr::vector<resonith_partial_path_entry> entries;
};

std::int64_t saturating_add_path(
    std::int64_t left,
    std::int64_t right,
    std::int64_t limit,
    std::uint64_t* saturation_count
) noexcept {
    if (right > 0 && left > limit - right) {
        ++*saturation_count;
        return limit;
    }
    if (right < 0 && left < -limit - right) {
        ++*saturation_count;
        return -limit;
    }
    return std::clamp(left + right, -limit, limit);
}

struct unsigned_division {
    std::uint64_t quotient;
    std::uint64_t remainder;
    bool saturated;
};

/*
 * Computes floor(a*b/d) plus remainder without a 128-bit product. Splitting
 * `a` into quotient/remainder leaves one bit-serial modular product whose
 * quotient is bounded by `b`.
 */
unsigned_division multiply_divide_floor(
    std::uint64_t a,
    std::uint64_t b,
    std::uint64_t denominator,
    std::uint64_t limit
) noexcept {
    const std::uint64_t base_quotient = a / denominator;
    const std::uint64_t base_remainder = a % denominator;
    if (
        base_quotient != 0U
        && b > limit / base_quotient
    ) {
        return unsigned_division{limit, 0U, true};
    }
    std::uint64_t quotient = base_quotient * b;
    std::uint64_t fractional_quotient = 0U;
    std::uint64_t remainder = 0U;
    for (std::uint32_t bit = 64U; bit-- > 0U;) {
        std::uint32_t increment = 0U;
        if (remainder >= denominator - remainder) {
            remainder -= denominator - remainder;
            ++increment;
        } else {
            remainder *= 2U;
        }
        if (((b >> bit) & 1U) != 0U) {
            if (remainder >= denominator - base_remainder) {
                remainder -= denominator - base_remainder;
                ++increment;
            } else {
                remainder += base_remainder;
            }
        }
        if (
            fractional_quotient
            > (std::numeric_limits<std::uint64_t>::max() - increment) / 2U
        ) {
            return unsigned_division{limit, 0U, true};
        }
        fractional_quotient =
            fractional_quotient * 2U + increment;
    }
    if (fractional_quotient > limit - quotient) {
        return unsigned_division{limit, 0U, true};
    }
    quotient += fractional_quotient;
    return unsigned_division{quotient, remainder, false};
}

std::pair<std::int64_t, bool> scale_nearest_even(
    std::int64_t value,
    std::uint64_t numerator,
    std::uint64_t denominator,
    std::int64_t saturation
) noexcept {
    if (denominator == 0U) {
        return {value < 0 ? -saturation : saturation, true};
    }
    unsigned_division result = multiply_divide_floor(
        unsigned_abs(value),
        numerator,
        denominator,
        static_cast<std::uint64_t>(saturation)
    );
    if (!result.saturated) {
        const std::uint64_t complement = denominator - result.remainder;
        const bool round_up = result.remainder > complement
            || (
                result.remainder == complement
                && (result.quotient & 1U) != 0U
            );
        if (round_up) {
            if (
                result.quotient
                == static_cast<std::uint64_t>(saturation)
            ) {
                result.saturated = true;
            } else {
                ++result.quotient;
            }
        }
    }
    const std::int64_t magnitude = static_cast<std::int64_t>(
        std::min(
            result.quotient,
            static_cast<std::uint64_t>(saturation)
        )
    );
    return {value < 0 ? -magnitude : magnitude, result.saturated};
}

std::pair<std::uint64_t, bool> scale_ceil_unsigned(
    std::uint64_t value,
    std::uint64_t numerator,
    std::uint64_t denominator
) noexcept {
    if (denominator == 0U) {
        return {std::numeric_limits<std::uint64_t>::max(), true};
    }
    unsigned_division result = multiply_divide_floor(
        value,
        numerator,
        denominator,
        std::numeric_limits<std::uint64_t>::max()
    );
    if (!result.saturated && result.remainder != 0U) {
        if (result.quotient == std::numeric_limits<std::uint64_t>::max()) {
            result.saturated = true;
        } else {
            ++result.quotient;
        }
    }
    return {result.quotient, result.saturated};
}

std::uint64_t signed_distance(
    std::int64_t left,
    std::int64_t right
) noexcept {
    if ((left < 0) == (right < 0)) {
        return unsigned_abs(left >= right ? left - right : right - left);
    }
    const std::uint64_t first = unsigned_abs(left);
    const std::uint64_t second = unsigned_abs(right);
    return first > std::numeric_limits<std::uint64_t>::max() - second
        ? std::numeric_limits<std::uint64_t>::max()
        : first + second;
}

std::pair<std::int32_t, bool> second_order_cost(
    const resonith_partial_observation& previous,
    const resonith_partial_observation& current,
    const resonith_partial_observation& target,
    const resonith_partial_path_manifest& manifest
) noexcept {
    const std::uint64_t dt01 =
        current.center_sample - previous.center_sample;
    const std::uint64_t dt12 =
        target.center_sample - current.center_sample;
    const auto predicted_frequency = scale_nearest_even(
        current.frequency_hz_q20 - previous.frequency_hz_q20,
        dt12,
        dt01,
        manifest.score_saturation
    );
    const std::int64_t actual_frequency =
        target.frequency_hz_q20 - current.frequency_hz_q20;
    const std::uint64_t frequency_residual = signed_distance(
        actual_frequency,
        predicted_frequency.first
    );
    const std::uint64_t pair_uncertainty = (
        previous.frequency_uncertainty_hz_q20
        > std::numeric_limits<std::uint64_t>::max()
            - current.frequency_uncertainty_hz_q20
    )
        ? std::numeric_limits<std::uint64_t>::max()
        : previous.frequency_uncertainty_hz_q20
            + current.frequency_uncertainty_hz_q20;
    const auto scaled_pair_uncertainty = scale_ceil_unsigned(
        pair_uncertainty,
        dt12,
        dt01
    );
    std::uint64_t frequency_sigma =
        target.frequency_uncertainty_hz_q20;
    for (const std::uint64_t item : {
        current.frequency_uncertainty_hz_q20,
        scaled_pair_uncertainty.first,
    }) {
        frequency_sigma = frequency_sigma
            > std::numeric_limits<std::uint64_t>::max() - item
            ? std::numeric_limits<std::uint64_t>::max()
            : frequency_sigma + item;
    }
    frequency_sigma = std::max(
        frequency_sigma,
        manifest.frequency_sigma_floor_hz_q20
    );
    const std::int32_t frequency_cost = log2_one_plus_ratio_q8(
        frequency_residual,
        frequency_sigma
    );

    const std::uint32_t amplitude_floor = manifest.amplitude_floor_q16;
    const std::uint32_t previous_amplitude = std::max(
        amplitude_floor,
        previous.normalized_amplitude_q16
    );
    const std::uint32_t current_amplitude = std::max(
        amplitude_floor,
        current.normalized_amplitude_q16
    );
    const std::uint32_t target_amplitude = std::max(
        amplitude_floor,
        target.normalized_amplitude_q16
    );
    const std::int32_t first_log_delta = signed_log_amplitude_ratio_q8(
        current_amplitude,
        previous_amplitude
    );
    const std::int32_t actual_log_delta = signed_log_amplitude_ratio_q8(
        target_amplitude,
        current_amplitude
    );
    const auto predicted_log = scale_nearest_even(
        first_log_delta,
        dt12,
        dt01,
        manifest.score_saturation
    );
    const std::uint64_t amplitude_residual = signed_distance(
        actual_log_delta,
        predicted_log.first
    );
    const std::uint64_t weight = manifest.amplitude_residual_weight_q8;
    const std::uint64_t weighted = (
        weight != 0U
        && amplitude_residual
            > std::numeric_limits<std::uint64_t>::max() / weight
    )
        ? std::numeric_limits<std::uint64_t>::max()
        : amplitude_residual * weight;
    const std::int32_t amplitude_cost = log2_one_plus_ratio_q8(
        weighted,
        1U << 16U
    );
    const std::int64_t total =
        static_cast<std::int64_t>(frequency_cost) + amplitude_cost;
    const bool total_saturated = total > manifest.score_saturation;
    return {
        static_cast<std::int32_t>(std::min<std::int64_t>(
            total,
            std::min<std::int64_t>(
                manifest.score_saturation,
                std::numeric_limits<std::int32_t>::max()
            )
        )),
        predicted_frequency.second
            || predicted_log.second
            || scaled_pair_uncertainty.second
            || total_saturated,
    };
}

std::int64_t state_continuity_score(
    const path_state& state,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest
) noexcept {
    const std::uint64_t continuation_count =
        state.observation_ids.size() - 1U;
    std::int64_t reward = path_manifest.score_saturation;
    if (
        graph_manifest.continuation_reward_q8 >= 0
        && continuation_count
            <= static_cast<std::uint64_t>(path_manifest.score_saturation)
                / static_cast<std::uint64_t>(
                    graph_manifest.continuation_reward_q8
                )
    ) {
        reward = static_cast<std::int64_t>(continuation_count)
            * graph_manifest.continuation_reward_q8;
    }
    return saturating_add(
        reward,
        -state.continuity_cost,
        path_manifest.score_saturation
    );
}

std::int64_t state_value_score(
    const path_state& state,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest
) noexcept {
    std::int64_t result = saturating_add(
        state.potential,
        -state.uncertainty_penalty,
        path_manifest.score_saturation
    );
    const std::int64_t continuity = state_continuity_score(
        state,
        graph_manifest,
        path_manifest
    );
    const std::int64_t half_continuity =
        continuity / 2
        - (
            continuity < 0 && continuity % 2 != 0
                ? 1
                : 0
        );
    return saturating_add(
        result,
        half_continuity,
        path_manifest.score_saturation
    );
}

path_key state_identity(const path_state& state) {
    return {state.observation_ids, state.incoming_edge_ids};
}

std::vector<path_state> retain_state_union(
    std::vector<path_state> candidates,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest
) {
    std::map<path_key, path_state> unique;
    for (path_state& candidate : candidates) {
        unique[state_identity(candidate)] = std::move(candidate);
    }
    std::vector<path_state> value_ranked;
    value_ranked.reserve(unique.size());
    for (const auto& [key, state] : unique) {
        static_cast<void>(key);
        value_ranked.push_back(state);
    }
    std::vector<path_state> continuity_ranked = value_ranked;
    std::sort(
        value_ranked.begin(),
        value_ranked.end(),
        [&](const path_state& left, const path_state& right) {
            const std::int64_t left_score = state_value_score(
                left,
                graph_manifest,
                path_manifest
            );
            const std::int64_t right_score = state_value_score(
                right,
                graph_manifest,
                path_manifest
            );
            if (left_score != right_score) {
                return left_score > right_score;
            }
            if (left.observation_ids.size() != right.observation_ids.size()) {
                return left.observation_ids.size()
                    > right.observation_ids.size();
            }
            return state_identity(left) < state_identity(right);
        }
    );
    std::sort(
        continuity_ranked.begin(),
        continuity_ranked.end(),
        [&](const path_state& left, const path_state& right) {
            const std::int64_t left_score = state_continuity_score(
                left,
                graph_manifest,
                path_manifest
            );
            const std::int64_t right_score = state_continuity_score(
                right,
                graph_manifest,
                path_manifest
            );
            if (left_score != right_score) {
                return left_score > right_score;
            }
            if (left.observation_ids.size() != right.observation_ids.size()) {
                return left.observation_ids.size()
                    > right.observation_ids.size();
            }
            return state_identity(left) < state_identity(right);
        }
    );
    std::map<path_key, path_state> retained;
    const std::size_t value_count = std::min<std::size_t>(
        value_ranked.size(),
        path_manifest.k_value_per_state
    );
    for (std::size_t index = 0U; index < value_count; ++index) {
        retained[state_identity(value_ranked[index])] = value_ranked[index];
    }
    const std::size_t continuity_count = std::min<std::size_t>(
        continuity_ranked.size(),
        path_manifest.k_continuity_per_state
    );
    for (std::size_t index = 0U; index < continuity_count; ++index) {
        retained[state_identity(continuity_ranked[index])] =
            continuity_ranked[index];
    }
    std::vector<path_state> result;
    result.reserve(retained.size());
    for (auto& [key, state] : retained) {
        static_cast<void>(key);
        result.push_back(std::move(state));
    }
    std::sort(
        result.begin(),
        result.end(),
        [&](const path_state& left, const path_state& right) {
            const std::int64_t left_score = state_value_score(
                left,
                graph_manifest,
                path_manifest
            );
            const std::int64_t right_score = state_value_score(
                right,
                graph_manifest,
                path_manifest
            );
            return left_score != right_score
                ? left_score > right_score
                : state_identity(left) < state_identity(right);
        }
    );
    return result;
}

bool valid_path_manifest(
    const resonith_partial_path_manifest& manifest,
    const resonith_partial_graph_manifest& graph_manifest
) noexcept {
    if (
        manifest.struct_size != sizeof(manifest)
        || manifest.abi_version != RESONITH_PARTIAL_PATH_ABI_VERSION
        || manifest.second_order_law_version != 2U
        || manifest.protected_band_count == 0U
        || manifest.protected_band_count
            > RESONITH_PARTIAL_PATH_MAX_PROTECTED_BANDS
        || manifest.k_value_per_state == 0U
        || manifest.k_value_per_state > 64U
        || manifest.k_continuity_per_state == 0U
        || manifest.k_continuity_per_state > 64U
        || manifest.top_k_value == 0U
        || manifest.top_k_continuity == 0U
        || manifest.top_k_protected == 0U
        || manifest.protected_paths_per_band == 0U
        || manifest.minimum_path_observations < 2U
        || manifest.minimum_path_observations
            > manifest.maximum_path_observations
        || manifest.exact_set_candidate_limit == 0U
        || manifest.exact_set_candidate_limit > 24U
        || manifest.amplitude_floor_q16 == 0U
        || manifest.amplitude_residual_weight_q8 == 0U
        || manifest.reserved_alignment != 0U
        || manifest.frequency_sigma_floor_hz_q20 == 0U
        || manifest.score_saturation < 1024
        || manifest.maximum_path_records == 0U
        || manifest.maximum_total_entries == 0U
        || manifest.maximum_frontier_states == 0U
        || manifest.maximum_work_units == 0U
        || manifest.maximum_state_records == 0U
        || manifest.maximum_state_records
            >= static_cast<std::uint64_t>(
                std::numeric_limits<std::uint32_t>::max()
            )
        || manifest.maximum_managed_bytes == 0U
        || manifest.maximum_path_records
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::size_t>::max()
            )
        || manifest.maximum_total_entries
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::size_t>::max()
            )
        || !reserved_zero(manifest)
    ) {
        return false;
    }
    const std::uint64_t family_reservation =
        static_cast<std::uint64_t>(manifest.top_k_value)
        + manifest.top_k_continuity
        + manifest.top_k_protected;
    if (
        manifest.maximum_path_records < family_reservation
        || manifest.top_k_value > manifest.maximum_path_records
        || manifest.top_k_continuity > manifest.maximum_path_records
        || manifest.top_k_protected > manifest.maximum_path_records
        || (
            manifest.protected_paths_per_band != 0U
            && manifest.protected_band_count
                > std::numeric_limits<std::uint64_t>::max()
                    / manifest.protected_paths_per_band
        )
    ) {
        return false;
    }
    const std::int64_t nyquist_q20 =
        static_cast<std::int64_t>(graph_manifest.sample_rate / 2U) << 20U;
    for (
        std::uint32_t index = 0U;
        index + 1U < manifest.protected_band_count;
        ++index
    ) {
        const std::int64_t upper =
            manifest.protected_band_upper_hz_q20[index];
        if (
            upper <= 0
            || upper >= nyquist_q20
            || (
                index != 0U
                && upper
                    <= manifest.protected_band_upper_hz_q20[index - 1U]
            )
        ) {
            return false;
        }
    }
    for (
        std::uint32_t index =
            manifest.protected_band_count - 1U;
        index + 1U < RESONITH_PARTIAL_PATH_MAX_PROTECTED_BANDS;
        ++index
    ) {
        if (manifest.protected_band_upper_hz_q20[index] != 0) {
            return false;
        }
    }
    return true;
}

template <typename WorkCharge>
bool valid_path_inputs(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_edge* edges,
    std::size_t edge_count,
    const resonith_partial_graph_manifest& graph_manifest,
    std::pmr::memory_resource* memory,
    WorkCharge&& charge_work
) {
    std::pmr::unordered_map<std::uint32_t, resolution_record> resolution_table(
        memory
    );
    std::pmr::vector<std::uint64_t> validated_observation_ids(memory);
    if (
        !valid_manifest(
            resolutions,
            resolution_count,
            graph_manifest,
            &resolution_table
        )
        || !valid_observations(
            observations,
            observation_count,
            graph_manifest.sample_rate,
            resolution_table,
            &validated_observation_ids
        )
    ) {
        return false;
    }
    std::pmr::set<std::uint64_t> observation_ids(memory);
    const std::int64_t nyquist_q20 =
        static_cast<std::int64_t>(graph_manifest.sample_rate / 2U) << 20U;
    for (std::size_t index = 0U; index < observation_count; ++index) {
        const resonith_partial_observation& item = observations[index];
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || item.frequency_hz_q20 < 0
            || item.frequency_hz_q20 > nyquist_q20
            || !reserved_zero(item)
            || !observation_ids.insert(item.observation_id).second
        ) {
            return false;
        }
    }
    for (std::size_t index = 0U; index < edge_count; ++index) {
        const resonith_partial_edge& edge = edges[index];
        if (
            edge.struct_size != sizeof(edge)
            || edge.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || !reserved_zero(edge)
            || !observation_ids.contains(edge.source_observation_id)
            || !observation_ids.contains(edge.target_observation_id)
            || edge.center_delta_samples == 0U
            || (edge.flags & ~edge_phase_usable) != 0U
            || edge.candidate_id != index
        ) {
            return false;
        }
    }
    std::size_t compared = 0U;
    std::size_t required = 0U;
    const resonith_status status = enumerate_edges_stream(
        observations,
        observation_count,
        graph_manifest,
        resolution_table,
        memory,
        [&](const resonith_partial_edge& expected) {
            charge_work(1U);
            if (
                compared >= edge_count
                || std::memcmp(
                    &edges[compared],
                    &expected,
                    sizeof(resonith_partial_edge)
                ) != 0
            ) {
                return RESONITH_STATUS_INVALID_ARGUMENT;
            }
            ++compared;
            return RESONITH_STATUS_OK;
        },
        std::forward<WorkCharge>(charge_work),
        &required
    );
    return status == RESONITH_STATUS_OK
        && required == edge_count
        && compared == edge_count;
}

std::array<std::uint64_t, 4> fingerprint_begin() noexcept {
    return {
        0xcbf29ce484222325ULL,
        0x84222325cbf29ce4ULL,
        0x9e3779b185ebca87ULL,
        0xd6e8feb86659fd93ULL,
    };
}

void fingerprint_bytes(
    std::array<std::uint64_t, 4>* state,
    const void* data,
    std::size_t size
) noexcept {
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    constexpr std::array<std::uint64_t, 4> primes = {
        0x100000001b3ULL,
        0x100000001c9ULL,
        0x100000001e7ULL,
        0x10000000233ULL,
    };
    for (std::size_t byte = 0U; byte < size; ++byte) {
        for (std::size_t lane = 0U; lane < state->size(); ++lane) {
            (*state)[lane] ^= static_cast<std::uint64_t>(
                bytes[byte] + static_cast<std::uint8_t>(lane * 53U)
            );
            (*state)[lane] *= primes[lane];
        }
    }
}

std::array<std::uint64_t, 4> input_fingerprint(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_edge* edges,
    std::size_t edge_count,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest,
    std::pmr::memory_resource* memory
) {
    std::pmr::vector<resonith_partial_resolution> canonical_resolutions(
        resolutions,
        resolutions + resolution_count,
        memory
    );
    std::sort(
        canonical_resolutions.begin(),
        canonical_resolutions.end(),
        [](const auto& left, const auto& right) {
            return left.resolution_id < right.resolution_id;
        }
    );
    std::pmr::vector<resonith_partial_observation> canonical_observations(
        observations,
        observations + observation_count,
        memory
    );
    std::sort(
        canonical_observations.begin(),
        canonical_observations.end(),
        [](const auto& left, const auto& right) {
            return std::tie(
                left.center_sample,
                left.resolution_id,
                left.detector_id,
                left.frequency_hz_q20,
                left.observation_id
            ) < std::tie(
                right.center_sample,
                right.resolution_id,
                right.detector_id,
                right.frequency_hz_q20,
                right.observation_id
            );
        }
    );
    resonith_partial_path_manifest canonical_manifest = path_manifest;
    std::fill(
        std::begin(canonical_manifest.expected_input_fingerprint),
        std::end(canonical_manifest.expected_input_fingerprint),
        0U
    );
    auto state = fingerprint_begin();
    constexpr std::uint64_t canonical_order_contract = 0x5250313931563201ULL;
    const std::array<std::uint64_t, 4> counts_and_order = {
        resolution_count,
        observation_count,
        edge_count,
        canonical_order_contract,
    };
    fingerprint_bytes(
        &state,
        counts_and_order.data(),
        counts_and_order.size() * sizeof(std::uint64_t)
    );
    fingerprint_bytes(
        &state,
        &graph_manifest,
        sizeof(graph_manifest)
    );
    fingerprint_bytes(
        &state,
        &canonical_manifest,
        sizeof(canonical_manifest)
    );
    if (!canonical_resolutions.empty()) {
        fingerprint_bytes(
            &state,
            canonical_resolutions.data(),
            canonical_resolutions.size()
                * sizeof(resonith_partial_resolution)
        );
    }
    if (!canonical_observations.empty()) {
        fingerprint_bytes(
            &state,
            canonical_observations.data(),
            canonical_observations.size()
                * sizeof(resonith_partial_observation)
        );
    }
    if (edge_count != 0U) {
        fingerprint_bytes(
            &state,
            edges,
            edge_count * sizeof(resonith_partial_edge)
        );
    }
    return state;
}

std::uint32_t frequency_band(
    const path_state& state,
    const std::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    >& observations,
    const resonith_partial_path_manifest& manifest
) {
    std::vector<std::int64_t> frequencies;
    frequencies.reserve(state.observation_ids.size());
    for (const std::uint64_t identifier : state.observation_ids) {
        frequencies.push_back(observations.at(identifier)->frequency_hz_q20);
    }
    std::sort(frequencies.begin(), frequencies.end());
    const std::int64_t median =
        frequencies[(frequencies.size() - 1U) / 2U];
    std::uint32_t band = 0U;
    while (
        band + 1U < manifest.protected_band_count
        && median >= manifest.protected_band_upper_hz_q20[band]
    ) {
        ++band;
    }
    return band;
}

bool path_conflict(
    const path_state& first,
    const path_state& second,
    const std::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    >& observations
) {
    std::set<std::uint32_t> components;
    for (const std::uint64_t identifier : first.observation_ids) {
        components.insert(observations.at(identifier)->ownership_component);
    }
    for (const std::uint64_t identifier : second.observation_ids) {
        if (
            components.contains(
                observations.at(identifier)->ownership_component
            )
        ) {
            return true;
        }
    }
    return false;
}

bool add_work(
    std::uint64_t amount,
    const resonith_partial_path_manifest& manifest,
    resonith_partial_path_report* report
) noexcept {
    if (
        amount > manifest.maximum_work_units
        || report->work_units > manifest.maximum_work_units - amount
    ) {
        report->termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        return false;
    }
    report->work_units += amount;
    return true;
}

[[maybe_unused]] resonith_status compute_paths(
    const resonith_partial_observation* observation_data,
    std::size_t observation_count,
    const resonith_partial_edge* edge_data,
    std::size_t edge_count,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest,
    resonith_partial_path_report* report,
    path_output* output
) {
    std::vector<const resonith_partial_observation*> ordered_observations;
    ordered_observations.reserve(observation_count);
    std::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    > observations;
    for (std::size_t index = 0U; index < observation_count; ++index) {
        ordered_observations.push_back(&observation_data[index]);
        observations.emplace(
            observation_data[index].observation_id,
            &observation_data[index]
        );
    }
    std::sort(
        ordered_observations.begin(),
        ordered_observations.end(),
        [](const auto* left, const auto* right) {
            return std::tie(
                left->center_sample,
                left->resolution_id,
                left->detector_id,
                left->frequency_hz_q20,
                left->observation_id
            ) < std::tie(
                right->center_sample,
                right->resolution_id,
                right->detector_id,
                right->frequency_hz_q20,
                right->observation_id
            );
        }
    );
    std::vector<const resonith_partial_edge*> ordered_edges;
    ordered_edges.reserve(edge_count);
    std::map<std::uint64_t, std::vector<const resonith_partial_edge*>> incoming;
    for (std::size_t index = 0U; index < edge_count; ++index) {
        ordered_edges.push_back(&edge_data[index]);
    }
    std::sort(
        ordered_edges.begin(),
        ordered_edges.end(),
        [](const auto* left, const auto* right) {
            return left->candidate_id < right->candidate_id;
        }
    );
    for (const auto* edge : ordered_edges) {
        incoming[edge->target_observation_id].push_back(edge);
    }

    std::map<
        std::pair<std::uint64_t, std::uint64_t>,
        std::vector<path_state>
    > states;
    for (const auto* target : ordered_observations) {
        std::map<
            std::pair<std::uint64_t, std::uint64_t>,
            std::vector<path_state>
        > pending;
        const auto incoming_rows = incoming.find(target->observation_id);
        if (incoming_rows == incoming.end()) {
            continue;
        }
        for (const auto* edge : incoming_rows->second) {
            const auto* source = observations.at(edge->source_observation_id);
            std::vector<path_state> candidates;
            path_state birth;
            birth.observation_ids = {
                source->observation_id,
                target->observation_id,
            };
            birth.incoming_edge_ids = {birth_edge_id, edge->candidate_id};
            birth.second_order_costs = {0, 0};
            birth.continuity_cost = edge->continuity_cost_q8;
            birth.potential = saturating_add_path(
                source->potential_node_value_q8,
                target->potential_node_value_q8,
                path_manifest.score_saturation,
                &report->score_saturation_count
            );
            birth.uncertainty_penalty = saturating_add_path(
                source->uncertainty_leakage_penalty_q8,
                target->uncertainty_leakage_penalty_q8,
                path_manifest.score_saturation,
                &report->score_saturation_count
            );
            birth.provisional_program_cost = saturating_add_path(
                path_manifest.birth_cost_bits_q8,
                edge->provisional_program_cost_q8,
                path_manifest.score_saturation,
                &report->score_saturation_count
            );
            if ((edge->flags & edge_phase_usable) != 0U) {
                birth.phase_error_sum = edge->phase_error_u31;
                birth.phase_error_count = 1U;
            }
            candidates.push_back(std::move(birth));

            for (const auto& [state_key, prior_states] : states) {
                if (state_key.second != source->observation_id) {
                    continue;
                }
                const auto* previous = observations.at(state_key.first);
                for (const path_state& prior : prior_states) {
                    if (
                        prior.observation_ids.size()
                        >= path_manifest.maximum_path_observations
                    ) {
                        continue;
                    }
                    const auto second_order = second_order_cost(
                        *previous,
                        *source,
                        *target,
                        path_manifest
                    );
                    if (second_order.second) {
                        ++report->score_saturation_count;
                    }
                    path_state extended = prior;
                    extended.observation_ids.push_back(target->observation_id);
                    extended.incoming_edge_ids.push_back(edge->candidate_id);
                    extended.second_order_costs.push_back(second_order.first);
                    extended.continuity_cost = saturating_add_path(
                        saturating_add_path(
                            prior.continuity_cost,
                            edge->continuity_cost_q8,
                            path_manifest.score_saturation,
                            &report->score_saturation_count
                        ),
                        second_order.first,
                        path_manifest.score_saturation,
                        &report->score_saturation_count
                    );
                    extended.potential = saturating_add_path(
                        prior.potential,
                        target->potential_node_value_q8,
                        path_manifest.score_saturation,
                        &report->score_saturation_count
                    );
                    extended.uncertainty_penalty = saturating_add_path(
                        prior.uncertainty_penalty,
                        target->uncertainty_leakage_penalty_q8,
                        path_manifest.score_saturation,
                        &report->score_saturation_count
                    );
                    extended.provisional_program_cost = saturating_add_path(
                        prior.provisional_program_cost,
                        edge->provisional_program_cost_q8,
                        path_manifest.score_saturation,
                        &report->score_saturation_count
                    );
                    if ((edge->flags & edge_phase_usable) != 0U) {
                        extended.phase_error_sum =
                            prior.phase_error_sum
                            > std::numeric_limits<std::uint64_t>::max()
                                - edge->phase_error_u31
                                ? std::numeric_limits<std::uint64_t>::max()
                                : prior.phase_error_sum
                                    + edge->phase_error_u31;
                        ++extended.phase_error_count;
                    }
                    candidates.push_back(std::move(extended));
                }
            }
            report->raw_state_count += candidates.size();
            if (!add_work(candidates.size(), path_manifest, report)) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            auto& destination = pending[{
                source->observation_id,
                target->observation_id,
            }];
            destination.insert(
                destination.end(),
                std::make_move_iterator(candidates.begin()),
                std::make_move_iterator(candidates.end())
            );
        }
        for (auto& [key, candidates] : pending) {
            states[key] = retain_state_union(
                std::move(candidates),
                graph_manifest,
                path_manifest
            );
        }
        std::uint64_t frontier_size = 0U;
        for (const auto& [key, rows] : states) {
            static_cast<void>(key);
            frontier_size += rows.size();
        }
        report->frontier_peak = std::max(
            report->frontier_peak,
            frontier_size
        );
        if (frontier_size > path_manifest.maximum_frontier_states) {
            report->termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            report->flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }

    std::map<path_key, path_state> raw_paths;
    for (const auto& [key, rows] : states) {
        static_cast<void>(key);
        for (const path_state& state : rows) {
            if (
                state.observation_ids.size()
                >= path_manifest.minimum_path_observations
            ) {
                raw_paths[state_identity(state)] = state;
            }
        }
    }
    std::vector<path_state> value_ranked;
    value_ranked.reserve(raw_paths.size());
    for (const auto& [key, state] : raw_paths) {
        static_cast<void>(key);
        value_ranked.push_back(state);
    }
    std::vector<path_state> continuity_ranked = value_ranked;
    std::sort(
        value_ranked.begin(),
        value_ranked.end(),
        [&](const path_state& left, const path_state& right) {
            const auto left_score = state_value_score(
                left,
                graph_manifest,
                path_manifest
            );
            const auto right_score = state_value_score(
                right,
                graph_manifest,
                path_manifest
            );
            return left_score != right_score
                ? left_score > right_score
                : state_identity(left) < state_identity(right);
        }
    );
    std::sort(
        continuity_ranked.begin(),
        continuity_ranked.end(),
        [&](const path_state& left, const path_state& right) {
            const auto left_score = state_continuity_score(
                left,
                graph_manifest,
                path_manifest
            );
            const auto right_score = state_continuity_score(
                right,
                graph_manifest,
                path_manifest
            );
            return left_score != right_score
                ? left_score > right_score
                : state_identity(left) < state_identity(right);
        }
    );

    std::map<path_key, std::uint32_t> families;
    std::map<path_key, std::uint32_t> value_ranks;
    std::map<path_key, std::uint32_t> continuity_ranks;
    std::map<path_key, std::uint32_t> protected_ranks;
    const std::size_t value_count = std::min<std::size_t>(
        value_ranked.size(),
        path_manifest.top_k_value
    );
    for (std::size_t index = 0U; index < value_count; ++index) {
        const path_key key = state_identity(value_ranked[index]);
        families[key] |= RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL;
        value_ranks[key] = static_cast<std::uint32_t>(index);
    }
    const std::size_t continuity_count = std::min<std::size_t>(
        continuity_ranked.size(),
        path_manifest.top_k_continuity
    );
    for (std::size_t index = 0U; index < continuity_count; ++index) {
        const path_key key = state_identity(continuity_ranked[index]);
        families[key] |= RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY;
        continuity_ranks[key] = static_cast<std::uint32_t>(index);
    }

    std::map<std::uint32_t, std::vector<path_state>> protected_by_band;
    for (const auto& [key, state] : raw_paths) {
        static_cast<void>(key);
        const bool protected_path = std::any_of(
            state.observation_ids.begin(),
            state.observation_ids.end(),
            [&](std::uint64_t identifier) {
                return (
                    observations.at(identifier)->flags
                    & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
                ) != 0U;
            }
        );
        if (protected_path) {
            protected_by_band[frequency_band(
                state,
                observations,
                path_manifest
            )].push_back(state);
        }
    }
    auto protected_count = [&](const path_state& state) {
        return std::count_if(
            state.observation_ids.begin(),
            state.observation_ids.end(),
            [&](std::uint64_t identifier) {
                return (
                    observations.at(identifier)->flags
                    & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
                ) != 0U;
            }
        );
    };
    auto protected_score = [&](const path_state& state) {
        std::int64_t score = 0;
        for (const std::uint64_t identifier : state.observation_ids) {
            const auto* observation = observations.at(identifier);
            if (
                (
                    observation->flags
                    & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
                ) != 0U
                && observation->protected_rank_q8 > 0
            ) {
                score = saturating_add(
                    score,
                    observation->protected_rank_q8,
                    path_manifest.score_saturation
                );
            }
        }
        return score;
    };
    using protected_row = std::pair<std::uint32_t, path_state>;
    std::vector<protected_row> protected_candidates;
    for (auto& [band, rows] : protected_by_band) {
        std::sort(
            rows.begin(),
            rows.end(),
            [&](const path_state& left, const path_state& right) {
                const auto left_count = protected_count(left);
                const auto right_count = protected_count(right);
                if (left_count != right_count) {
                    return left_count > right_count;
                }
                const auto left_score = protected_score(left);
                const auto right_score = protected_score(right);
                if (left_score != right_score) {
                    return left_score > right_score;
                }
                const auto left_continuity = state_continuity_score(
                    left,
                    graph_manifest,
                    path_manifest
                );
                const auto right_continuity = state_continuity_score(
                    right,
                    graph_manifest,
                    path_manifest
                );
                return left_continuity != right_continuity
                    ? left_continuity > right_continuity
                    : state_identity(left) < state_identity(right);
            }
        );
        const std::size_t count = std::min<std::size_t>(
            rows.size(),
            path_manifest.protected_paths_per_band
        );
        for (std::size_t index = 0U; index < count; ++index) {
            protected_candidates.emplace_back(band, rows[index]);
        }
    }
    std::sort(
        protected_candidates.begin(),
        protected_candidates.end(),
        [&](const protected_row& left, const protected_row& right) {
            const auto left_count = protected_count(left.second);
            const auto right_count = protected_count(right.second);
            if (left_count != right_count) {
                return left_count > right_count;
            }
            const auto left_score = protected_score(left.second);
            const auto right_score = protected_score(right.second);
            if (left_score != right_score) {
                return left_score > right_score;
            }
            const auto left_continuity = state_continuity_score(
                left.second,
                graph_manifest,
                path_manifest
            );
            const auto right_continuity = state_continuity_score(
                right.second,
                graph_manifest,
                path_manifest
            );
            if (left_continuity != right_continuity) {
                return left_continuity > right_continuity;
            }
            if (left.first != right.first) {
                return left.first < right.first;
            }
            return state_identity(left.second) < state_identity(right.second);
        }
    );
    const std::size_t protected_total = std::min<std::size_t>(
        protected_candidates.size(),
        path_manifest.top_k_protected
    );
    for (std::size_t index = 0U; index < protected_total; ++index) {
        const path_key key = state_identity(protected_candidates[index].second);
        families[key] |= RESONITH_PARTIAL_PATH_FAMILY_PROTECTED_WEAK;
        protected_ranks[key] = static_cast<std::uint32_t>(index);
    }

    std::vector<path_state> union_paths;
    union_paths.reserve(families.size());
    for (const auto& [key, family] : families) {
        static_cast<void>(family);
        union_paths.push_back(raw_paths.at(key));
    }
    std::sort(
        union_paths.begin(),
        union_paths.end(),
        [&](const path_state& left, const path_state& right) {
            const auto left_value = state_value_score(
                left,
                graph_manifest,
                path_manifest
            );
            const auto right_value = state_value_score(
                right,
                graph_manifest,
                path_manifest
            );
            if (left_value != right_value) {
                return left_value > right_value;
            }
            const auto left_continuity = state_continuity_score(
                left,
                graph_manifest,
                path_manifest
            );
            const auto right_continuity = state_continuity_score(
                right,
                graph_manifest,
                path_manifest
            );
            return left_continuity != right_continuity
                ? left_continuity > right_continuity
                : state_identity(left) < state_identity(right);
        }
    );
    if (union_paths.size() > path_manifest.maximum_path_records) {
        report->termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::vector<std::uint32_t> internal_conflicts(union_paths.size(), 0U);
    std::vector<std::uint32_t> bands(union_paths.size(), 0U);
    std::map<path_key, std::uint64_t> path_ids;
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        const path_state& state = union_paths[index];
        std::set<std::uint32_t> components;
        for (const std::uint64_t identifier : state.observation_ids) {
            components.insert(observations.at(identifier)->ownership_component);
        }
        internal_conflicts[index] = static_cast<std::uint32_t>(
            state.observation_ids.size() - components.size()
        );
        report->internal_conflict_count += internal_conflicts[index];
        bands[index] = frequency_band(state, observations, path_manifest);
        path_ids[state_identity(state)] = index;
    }

    std::vector<std::size_t> selection_candidates;
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        const std::int64_t selection_score = std::max<std::int64_t>({
            0,
            state_value_score(
                union_paths[index],
                graph_manifest,
                path_manifest
            ),
            state_continuity_score(
                union_paths[index],
                graph_manifest,
                path_manifest
            ),
        });
        if (internal_conflicts[index] == 0U && selection_score > 0) {
            selection_candidates.push_back(index);
        }
    }
    report->selected_candidate_count = selection_candidates.size();
    std::set<std::pair<std::size_t, std::size_t>> conflict_pairs;
    for (
        std::size_t left = 0U;
        left < selection_candidates.size();
        ++left
    ) {
        for (
            std::size_t right = left + 1U;
            right < selection_candidates.size();
            ++right
        ) {
            if (path_conflict(
                union_paths[selection_candidates[left]],
                union_paths[selection_candidates[right]],
                observations
            )) {
                conflict_pairs.emplace(left, right);
            }
        }
    }
    report->cross_path_conflict_count = conflict_pairs.size();
    if (!add_work(conflict_pairs.size(), path_manifest, report)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::set<std::uint64_t> selected_ids;
    if (
        selection_candidates.size()
        <= path_manifest.exact_set_candidate_limit
    ) {
        report->solver = RESONITH_PARTIAL_PATH_SOLVER_EXACT_SMALL;
        const std::uint64_t mask_count =
            1ULL << selection_candidates.size();
        std::int64_t best_score = 0;
        std::vector<std::uint64_t> best_ids;
        for (std::uint64_t mask = 0U; mask < mask_count; ++mask) {
            if (!add_work(1U, path_manifest, report)) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            bool valid = true;
            for (const auto& [left, right] : conflict_pairs) {
                if (
                    (mask & (1ULL << left)) != 0U
                    && (mask & (1ULL << right)) != 0U
                ) {
                    valid = false;
                    break;
                }
            }
            if (!valid) {
                continue;
            }
            std::int64_t score = 0;
            std::vector<std::uint64_t> identifiers;
            for (
                std::size_t candidate = 0U;
                candidate < selection_candidates.size();
                ++candidate
            ) {
                if ((mask & (1ULL << candidate)) == 0U) {
                    continue;
                }
                const std::size_t path_index =
                    selection_candidates[candidate];
                score = saturating_add(
                    score,
                    std::max<std::int64_t>({
                        0,
                        state_value_score(
                            union_paths[path_index],
                            graph_manifest,
                            path_manifest
                        ),
                        state_continuity_score(
                            union_paths[path_index],
                            graph_manifest,
                            path_manifest
                        ),
                    }),
                    path_manifest.score_saturation
                );
                identifiers.push_back(path_index);
            }
            if (
                score > best_score
                || (score == best_score && identifiers < best_ids)
            ) {
                best_score = score;
                best_ids = std::move(identifiers);
            }
        }
        selected_ids.insert(best_ids.begin(), best_ids.end());
    } else {
        report->solver = RESONITH_PARTIAL_PATH_SOLVER_BOUNDED_GREEDY;
        std::sort(
            selection_candidates.begin(),
            selection_candidates.end(),
            [&](std::size_t left, std::size_t right) {
                const auto left_score = std::max<std::int64_t>({
                    0,
                    state_value_score(
                        union_paths[left],
                        graph_manifest,
                        path_manifest
                    ),
                    state_continuity_score(
                        union_paths[left],
                        graph_manifest,
                        path_manifest
                    ),
                });
                const auto right_score = std::max<std::int64_t>({
                    0,
                    state_value_score(
                        union_paths[right],
                        graph_manifest,
                        path_manifest
                    ),
                    state_continuity_score(
                        union_paths[right],
                        graph_manifest,
                        path_manifest
                    ),
                });
                return left_score != right_score
                    ? left_score > right_score
                    : state_identity(union_paths[left])
                        < state_identity(union_paths[right]);
            }
        );
        std::vector<std::size_t> selected;
        for (const std::size_t candidate : selection_candidates) {
            const bool conflict = std::any_of(
                selected.begin(),
                selected.end(),
                [&](std::size_t incumbent) {
                    return path_conflict(
                        union_paths[candidate],
                        union_paths[incumbent],
                        observations
                    );
                }
            );
            if (!conflict) {
                selected.push_back(candidate);
                selected_ids.insert(candidate);
            }
        }
    }
    report->selected_path_count = selected_ids.size();

    std::uint64_t entry_offset = 0U;
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        const path_state& state = union_paths[index];
        if (
            state.observation_ids.size()
            > path_manifest.maximum_total_entries - entry_offset
        ) {
            report->termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            report->flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        const path_key key = state_identity(state);
        std::uint32_t flags = 0U;
        if (selected_ids.contains(index)) {
            flags |= RESONITH_PARTIAL_PATH_SELECTED;
        }
        if (internal_conflicts[index] != 0U) {
            flags |= RESONITH_PARTIAL_PATH_INTERNAL_OWNERSHIP_CONFLICT;
        }
        if (state.phase_error_count != 0U) {
            flags |= RESONITH_PARTIAL_PATH_PHASE_EVIDENCE;
        }
        const std::int64_t continuity = state_continuity_score(
            state,
            graph_manifest,
            path_manifest
        );
        const std::int64_t value = state_value_score(
            state,
            graph_manifest,
            path_manifest
        );
        const std::int64_t selection = std::max<std::int64_t>({
            0,
            continuity,
            value,
        });
        output->paths.push_back(resonith_partial_path{
            sizeof(resonith_partial_path),
            RESONITH_PARTIAL_PATH_ABI_VERSION,
            index,
            entry_offset,
            static_cast<std::uint32_t>(state.observation_ids.size()),
            families.at(key),
            state.observation_ids.back(),
            continuity,
            state.potential,
            state.uncertainty_penalty,
            saturating_add_path(
                state.provisional_program_cost,
                path_manifest.death_cost_bits_q8,
                path_manifest.score_saturation,
                &report->score_saturation_count
            ),
            selection,
            state.phase_error_sum,
            state.phase_error_count,
            internal_conflicts[index],
            bands[index],
            value_ranks.contains(key)
                ? value_ranks.at(key)
                : RESONITH_PARTIAL_PATH_RANK_ABSENT,
            continuity_ranks.contains(key)
                ? continuity_ranks.at(key)
                : RESONITH_PARTIAL_PATH_RANK_ABSENT,
            protected_ranks.contains(key)
                ? protected_ranks.at(key)
                : RESONITH_PARTIAL_PATH_RANK_ABSENT,
            flags,
            {0U, 0U, 0U, 0U, 0U},
        });
        for (
            std::size_t entry = 0U;
            entry < state.observation_ids.size();
            ++entry
        ) {
            output->entries.push_back(resonith_partial_path_entry{
                sizeof(resonith_partial_path_entry),
                RESONITH_PARTIAL_PATH_ABI_VERSION,
                state.observation_ids[entry],
                state.incoming_edge_ids[entry],
                observations.at(
                    state.observation_ids[entry]
                )->ownership_component,
                state.second_order_costs[entry],
                0U,
                {0U, 0U, 0U},
            });
        }
        entry_offset += state.observation_ids.size();
    }
    report->required_path_count = output->paths.size();
    report->required_entry_count = output->entries.size();
    report->peak_live_managed_bytes =
        output->paths.size() * sizeof(resonith_partial_path)
        + output->entries.size() * sizeof(resonith_partial_path_entry);
    if (
        report->peak_live_managed_bytes
        > path_manifest.maximum_managed_bytes
    ) {
        report->termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    for (const resonith_partial_path& path : output->paths) {
        report->value_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL
        ) != 0U;
        report->continuity_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY
        ) != 0U;
        report->protected_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_PROTECTED_WEAK
        ) != 0U;
    }
    return RESONITH_STATUS_OK;
}

using bounded_state_index = std::uint32_t;
constexpr bounded_state_index bounded_state_sentinel =
    std::numeric_limits<bounded_state_index>::max();

/*
 * One arena node stores only the newest observation and a checked parent
 * index. Paths therefore grow in O(1) managed bytes per hypothesis instead of
 * copying every historical observation at every extension.
 */
struct bounded_state_node {
    bounded_state_index parent = bounded_state_sentinel;
    bounded_state_index next_free = bounded_state_sentinel;
    std::uint64_t first_observation_id = 0U;
    std::uint64_t previous_observation_id = 0U;
    std::uint64_t current_observation_id = 0U;
    std::uint64_t incoming_edge_id = birth_edge_id;
    std::uint32_t length = 0U;
    std::uint32_t reference_count = 0U;
    std::int32_t second_order_cost = 0;
    std::int64_t continuity_cost = 0;
    std::int64_t potential = 0;
    std::int64_t uncertainty_penalty = 0;
    std::int64_t provisional_program_cost = 0;
    std::uint64_t phase_error_sum = 0U;
    std::uint32_t phase_error_count = 0U;
    std::uint32_t protected_observation_count = 0U;
    std::int64_t protected_rank_sum = 0;
    bool occupied = false;
};

class bounded_state_arena {
public:
    bounded_state_arena(
        std::pmr::memory_resource* memory,
        std::uint64_t maximum_records,
        resonith_partial_path_report* report
    )
        : nodes_(memory),
          maximum_records_(maximum_records),
          report_(report) {}

    bounded_state_arena(const bounded_state_arena&) = delete;
    bounded_state_arena& operator=(const bounded_state_arena&) = delete;

    [[nodiscard]] bounded_state_index create(
        const bounded_state_node& value
    ) {
        if (
            live_count_ >= maximum_records_
            || live_count_
                >= static_cast<std::uint64_t>(bounded_state_sentinel)
        ) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        bounded_state_index index = bounded_state_sentinel;
        if (free_head_ != bounded_state_sentinel) {
            index = free_head_;
            free_head_ = nodes_[index].next_free;
            nodes_[index] = value;
        } else {
            if (
                nodes_.size()
                >= static_cast<std::size_t>(bounded_state_sentinel)
            ) {
                ++report_->bound_rejected_count;
                throw managed_profile_bound{};
            }
            nodes_.push_back(value);
            index = static_cast<bounded_state_index>(nodes_.size() - 1U);
        }
        bounded_state_node& node = nodes_[index];
        node.reference_count = 1U;
        node.occupied = true;
        node.next_free = bounded_state_sentinel;
        if (node.parent != bounded_state_sentinel) {
            add_reference(node.parent);
        }
        ++live_count_;
        report_->state_arena_peak = std::max(
            report_->state_arena_peak,
            live_count_
        );
        return index;
    }

    void add_reference(bounded_state_index index) {
        bounded_state_node& node = checked(index);
        if (node.reference_count == std::numeric_limits<std::uint32_t>::max()) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        ++node.reference_count;
    }

    void release(bounded_state_index index) noexcept {
        while (index != bounded_state_sentinel) {
            bounded_state_node& node = nodes_[index];
            if (!node.occupied || node.reference_count == 0U) {
                std::terminate();
            }
            --node.reference_count;
            if (node.reference_count != 0U) {
                return;
            }
            const bounded_state_index parent = node.parent;
            node = bounded_state_node{};
            node.next_free = free_head_;
            free_head_ = index;
            --live_count_;
            index = parent;
        }
    }

    [[nodiscard]] const bounded_state_node& at(
        bounded_state_index index
    ) const {
        if (
            index == bounded_state_sentinel
            || index >= nodes_.size()
            || !nodes_[index].occupied
        ) {
            throw std::logic_error("invalid bounded state index");
        }
        return nodes_[index];
    }

private:
    [[nodiscard]] bounded_state_node& checked(bounded_state_index index) {
        if (
            index == bounded_state_sentinel
            || index >= nodes_.size()
            || !nodes_[index].occupied
        ) {
            throw std::logic_error("invalid bounded state index");
        }
        return nodes_[index];
    }

    std::pmr::vector<bounded_state_node> nodes_;
    std::uint64_t maximum_records_;
    resonith_partial_path_report* report_;
    bounded_state_index free_head_ = bounded_state_sentinel;
    std::uint64_t live_count_ = 0U;
};

class bounded_node_reference {
public:
    bounded_node_reference() noexcept = default;

    static bounded_node_reference adopt(
        bounded_state_arena* arena,
        bounded_state_index index
    ) noexcept {
        return bounded_node_reference(arena, index);
    }

    static bounded_node_reference retain(
        bounded_state_arena* arena,
        bounded_state_index index
    ) {
        arena->add_reference(index);
        return bounded_node_reference(arena, index);
    }

    bounded_node_reference(const bounded_node_reference&) = delete;
    bounded_node_reference& operator=(const bounded_node_reference&) = delete;

    bounded_node_reference(bounded_node_reference&& other) noexcept
        : arena_(std::exchange(other.arena_, nullptr)),
          index_(std::exchange(other.index_, bounded_state_sentinel)) {}

    bounded_node_reference& operator=(
        bounded_node_reference&& other
    ) noexcept {
        if (this != &other) {
            reset();
            arena_ = std::exchange(other.arena_, nullptr);
            index_ = std::exchange(other.index_, bounded_state_sentinel);
        }
        return *this;
    }

    ~bounded_node_reference() {
        reset();
    }

    [[nodiscard]] bounded_state_index get() const noexcept {
        return index_;
    }

    void reset() noexcept {
        if (arena_ != nullptr) {
            arena_->release(index_);
            arena_ = nullptr;
            index_ = bounded_state_sentinel;
        }
    }

private:
    bounded_node_reference(
        bounded_state_arena* arena,
        bounded_state_index index
    ) noexcept
        : arena_(arena), index_(index) {}

    bounded_state_arena* arena_ = nullptr;
    bounded_state_index index_ = bounded_state_sentinel;
};

class bounded_work_meter {
public:
    bounded_work_meter(
        const resonith_partial_path_manifest& manifest,
        resonith_partial_path_report* report
    ) noexcept
        : manifest_(manifest), report_(report) {}

    void charge(std::uint64_t amount) {
        if (!add_work(amount, manifest_, report_)) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
    }

    void charge_product(std::uint64_t left, std::uint64_t right) {
        if (
            left != 0U
            && right > std::numeric_limits<std::uint64_t>::max() / left
        ) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        charge(left * right);
    }

private:
    const resonith_partial_path_manifest& manifest_;
    resonith_partial_path_report* report_;
};

struct bounded_identity {
    explicit bounded_identity(std::pmr::memory_resource* memory)
        : observations(memory), incoming_edges(memory) {}

    bounded_identity(
        const bounded_identity& other,
        std::pmr::memory_resource* memory
    )
        : observations(
              other.observations.begin(),
              other.observations.end(),
              memory
          ),
          incoming_edges(
              other.incoming_edges.begin(),
              other.incoming_edges.end(),
              memory
          ) {}

    bounded_identity(bounded_identity&&) noexcept = default;
    bounded_identity& operator=(bounded_identity&&) noexcept = default;
    bounded_identity(const bounded_identity&) = delete;
    bounded_identity& operator=(const bounded_identity&) = delete;

    std::pmr::vector<std::uint64_t> observations;
    std::pmr::vector<std::uint64_t> incoming_edges;
};

bounded_identity materialize_identity(
    const bounded_state_arena& arena,
    bounded_state_index index,
    std::pmr::memory_resource* memory,
    bounded_work_meter* work
) {
    const bounded_state_node& leaf = arena.at(index);
    work->charge_product(leaf.length, 2U);
    bounded_identity result(memory);
    result.observations.resize(leaf.length);
    result.incoming_edges.resize(leaf.length);
    bounded_state_index cursor = index;
    std::size_t position = leaf.length;
    while (cursor != bounded_state_sentinel) {
        const bounded_state_node& node = arena.at(cursor);
        if (position < 2U) {
            throw std::logic_error("invalid bounded parent chain");
        }
        --position;
        result.observations[position] = node.current_observation_id;
        result.incoming_edges[position] = node.incoming_edge_id;
        if (node.parent == bounded_state_sentinel) {
            --position;
            result.observations[position] = node.previous_observation_id;
            result.incoming_edges[position] = birth_edge_id;
        }
        cursor = node.parent;
    }
    if (position != 0U) {
        throw std::logic_error("bounded parent chain length mismatch");
    }
    return result;
}

int compare_identity(
    const bounded_identity& left,
    const bounded_identity& right,
    bounded_work_meter* work
) {
    work->charge(
        static_cast<std::uint64_t>(left.observations.size())
        + right.observations.size()
        + left.incoming_edges.size()
        + right.incoming_edges.size()
    );
    if (left.observations < right.observations) {
        return -1;
    }
    if (right.observations < left.observations) {
        return 1;
    }
    if (left.incoming_edges < right.incoming_edges) {
        return -1;
    }
    if (right.incoming_edges < left.incoming_edges) {
        return 1;
    }
    return 0;
}

std::int64_t bounded_continuity_score(
    const bounded_state_node& state,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest
) noexcept {
    const std::uint64_t continuation_count = state.length - 1U;
    std::int64_t reward = path_manifest.score_saturation;
    if (
        graph_manifest.continuation_reward_q8 >= 0
        && (
            graph_manifest.continuation_reward_q8 == 0
            || continuation_count
                <= static_cast<std::uint64_t>(
                    path_manifest.score_saturation
                ) / static_cast<std::uint64_t>(
                    graph_manifest.continuation_reward_q8
                )
        )
    ) {
        reward = static_cast<std::int64_t>(continuation_count)
            * graph_manifest.continuation_reward_q8;
    }
    return saturating_add(
        reward,
        -state.continuity_cost,
        path_manifest.score_saturation
    );
}

std::int64_t bounded_value_score(
    const bounded_state_node& state,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest
) noexcept {
    const std::int64_t base = saturating_add(
        state.potential,
        -state.uncertainty_penalty,
        path_manifest.score_saturation
    );
    const std::int64_t continuity = bounded_continuity_score(
        state,
        graph_manifest,
        path_manifest
    );
    const std::int64_t half_continuity =
        continuity / 2
        - (continuity < 0 && continuity % 2 != 0 ? 1 : 0);
    return saturating_add(
        base,
        half_continuity,
        path_manifest.score_saturation
    );
}

struct bounded_candidate {
    bounded_candidate(
        bounded_node_reference node_value,
        bounded_identity identity_value,
        std::int64_t value,
        std::int64_t continuity,
        std::uint32_t length_value
    )
        : node(std::move(node_value)),
          identity(std::move(identity_value)),
          value_score(value),
          continuity_score(continuity),
          length(length_value) {}

    bounded_candidate(bounded_candidate&&) noexcept = default;
    bounded_candidate& operator=(bounded_candidate&&) noexcept = default;
    bounded_candidate(const bounded_candidate&) = delete;
    bounded_candidate& operator=(const bounded_candidate&) = delete;

    bounded_node_reference node;
    bounded_identity identity;
    std::int64_t value_score;
    std::int64_t continuity_score;
    std::uint32_t length;
    bool duplicate = false;
    bool retained = false;
};

bool candidate_better_value(
    const bounded_candidate& left,
    const bounded_candidate& right,
    bounded_work_meter* work
) {
    work->charge(1U);
    if (left.value_score != right.value_score) {
        return left.value_score > right.value_score;
    }
    if (left.length != right.length) {
        return left.length > right.length;
    }
    return compare_identity(left.identity, right.identity, work) < 0;
}

bool candidate_better_continuity(
    const bounded_candidate& left,
    const bounded_candidate& right,
    bounded_work_meter* work
) {
    work->charge(1U);
    if (left.continuity_score != right.continuity_score) {
        return left.continuity_score > right.continuity_score;
    }
    if (left.length != right.length) {
        return left.length > right.length;
    }
    return compare_identity(left.identity, right.identity, work) < 0;
}

std::pmr::vector<bounded_node_reference> retain_bounded_state_union(
    std::pmr::vector<bounded_node_reference> candidates,
    bounded_state_arena* arena,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest,
    std::pmr::memory_resource* memory,
    bounded_work_meter* work,
    resonith_partial_path_report* report
) {
    std::pmr::vector<bounded_candidate> materialized(memory);
    materialized.reserve(candidates.size());
    for (bounded_node_reference& node : candidates) {
        const bounded_state_index index = node.get();
        const bounded_state_node& state = arena->at(index);
        materialized.emplace_back(
            std::move(node),
            materialize_identity(*arena, index, memory, work),
            bounded_value_score(state, graph_manifest, path_manifest),
            bounded_continuity_score(state, graph_manifest, path_manifest),
            state.length
        );
    }

    /*
     * Duplicate detection is deliberately quadratic and fully metered. State
     * K is at most 64 per objective, while exact sequence equality prevents a
     * diagnostic hash collision from becoming semantic authority.
     */
    for (std::size_t left = 0U; left < materialized.size(); ++left) {
        if (materialized[left].duplicate) {
            continue;
        }
        for (
            std::size_t right = left + 1U;
            right < materialized.size();
            ++right
        ) {
            if (
                !materialized[right].duplicate
                && compare_identity(
                    materialized[left].identity,
                    materialized[right].identity,
                    work
                ) == 0
            ) {
                materialized[right].duplicate = true;
                ++report->duplicate_state_count;
            }
        }
    }

    auto select_family = [&](std::uint32_t limit, bool value_family) {
        for (std::uint32_t rank = 0U; rank < limit; ++rank) {
            std::size_t best = materialized.size();
            for (
                std::size_t index = 0U;
                index < materialized.size();
                ++index
            ) {
                if (materialized[index].duplicate) {
                    continue;
                }
                if (best == materialized.size()) {
                    best = index;
                    continue;
                }
                const bool better = value_family
                    ? candidate_better_value(
                          materialized[index],
                          materialized[best],
                          work
                      )
                    : candidate_better_continuity(
                          materialized[index],
                          materialized[best],
                          work
                      );
                if (better) {
                    best = index;
                }
            }
            if (best == materialized.size()) {
                break;
            }
            materialized[best].retained = true;
            materialized[best].duplicate = true;
        }
        for (bounded_candidate& item : materialized) {
            if (item.retained) {
                item.duplicate = false;
            }
        }
    };
    select_family(path_manifest.k_value_per_state, true);
    select_family(path_manifest.k_continuity_per_state, false);

    std::pmr::vector<bounded_node_reference> result(memory);
    for (bounded_candidate& item : materialized) {
        if (item.retained) {
            result.push_back(std::move(item.node));
        } else if (!item.duplicate) {
            ++report->state_k_discarded_count;
        }
    }
    if (report->state_k_discarded_count != 0U) {
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_PRUNED;
    }
    report->terminal_retained_state_count += result.size();

    /*
     * Canonical terminal order is value score, then full identity. It affects
     * neither search membership nor output rank, but freezes extension order.
     */
    for (std::size_t index = 1U; index < result.size(); ++index) {
        bounded_node_reference moving = std::move(result[index]);
        const bounded_state_node& moving_state = arena->at(moving.get());
        bounded_identity moving_identity = materialize_identity(
            *arena,
            moving.get(),
            memory,
            work
        );
        std::size_t position = index;
        while (position != 0U) {
            work->charge(1U);
            const bounded_state_node& previous_state = arena->at(
                result[position - 1U].get()
            );
            const std::int64_t moving_score = bounded_value_score(
                moving_state,
                graph_manifest,
                path_manifest
            );
            const std::int64_t previous_score = bounded_value_score(
                previous_state,
                graph_manifest,
                path_manifest
            );
            bounded_identity previous_identity = materialize_identity(
                *arena,
                result[position - 1U].get(),
                memory,
                work
            );
            if (
                moving_score < previous_score
                || (
                    moving_score == previous_score
                    && compare_identity(
                        moving_identity,
                        previous_identity,
                        work
                    ) >= 0
                )
            ) {
                break;
            }
            result[position] = std::move(result[position - 1U]);
            --position;
        }
        result[position] = std::move(moving);
    }
    return result;
}

struct bounded_family_entry {
    bounded_family_entry(
        bounded_node_reference node_value,
        bounded_identity identity_value,
        std::int64_t value,
        std::int64_t continuity,
        std::uint32_t length_value,
        std::uint32_t protected_count_value,
        std::int64_t protected_score_value,
        std::uint32_t band_value
    )
        : node(std::move(node_value)),
          identity(std::move(identity_value)),
          value_score(value),
          continuity_score(continuity),
          length(length_value),
          protected_count(protected_count_value),
          protected_score(protected_score_value),
          band(band_value) {}

    bounded_family_entry(bounded_family_entry&&) noexcept = default;
    bounded_family_entry& operator=(bounded_family_entry&&) noexcept = default;
    bounded_family_entry(const bounded_family_entry&) = delete;
    bounded_family_entry& operator=(const bounded_family_entry&) = delete;

    bounded_node_reference node;
    bounded_identity identity;
    std::int64_t value_score;
    std::int64_t continuity_score;
    std::uint32_t length;
    std::uint32_t protected_count;
    std::int64_t protected_score;
    std::uint32_t band;
};

enum class bounded_family_kind {
    value,
    continuity,
    protected_band,
    protected_global,
};

bool family_better(
    const bounded_family_entry& left,
    const bounded_family_entry& right,
    bounded_family_kind kind,
    bounded_work_meter* work
) {
    work->charge(1U);
    if (
        kind == bounded_family_kind::value
        && left.value_score != right.value_score
    ) {
        return left.value_score > right.value_score;
    }
    if (
        kind == bounded_family_kind::continuity
        && left.continuity_score != right.continuity_score
    ) {
        return left.continuity_score > right.continuity_score;
    }
    if (
        (
            kind == bounded_family_kind::protected_band
            || kind == bounded_family_kind::protected_global
        )
    ) {
        if (left.protected_count != right.protected_count) {
            return left.protected_count > right.protected_count;
        }
        if (left.protected_score != right.protected_score) {
            return left.protected_score > right.protected_score;
        }
        if (left.continuity_score != right.continuity_score) {
            return left.continuity_score > right.continuity_score;
        }
        if (
            kind == bounded_family_kind::protected_global
            && left.band != right.band
        ) {
            return left.band < right.band;
        }
    }
    return compare_identity(left.identity, right.identity, work) < 0;
}

void insert_family_reservoir(
    std::pmr::vector<bounded_family_entry>* reservoir,
    bounded_family_entry candidate,
    std::size_t limit,
    bounded_family_kind kind,
    bounded_work_meter* work,
    std::uint64_t* discarded,
    resonith_partial_path_report* report
) {
    std::size_t position = 0U;
    while (
        position < reservoir->size()
        && !family_better(candidate, (*reservoir)[position], kind, work)
    ) {
        ++position;
    }
    if (position >= limit) {
        ++*discarded;
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_PRUNED;
        return;
    }
    work->charge(reservoir->size() - position);
    reservoir->insert(
        reservoir->begin() + static_cast<std::ptrdiff_t>(position),
        std::move(candidate)
    );
    if (reservoir->size() > limit) {
        reservoir->pop_back();
        ++*discarded;
        report->flags |= RESONITH_PARTIAL_PATH_REPORT_PRUNED;
    }
}

std::uint32_t bounded_frequency_band(
    const bounded_identity& identity,
    const std::pmr::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    >& observations,
    const resonith_partial_path_manifest& manifest,
    std::pmr::memory_resource* memory,
    bounded_work_meter* work
) {
    work->charge_product(identity.observations.size(), identity.observations.size());
    std::pmr::vector<std::int64_t> frequencies(memory);
    frequencies.reserve(identity.observations.size());
    for (const std::uint64_t identifier : identity.observations) {
        frequencies.push_back(observations.at(identifier)->frequency_hz_q20);
    }
    std::sort(frequencies.begin(), frequencies.end());
    const std::int64_t median =
        frequencies[(frequencies.size() - 1U) / 2U];
    std::uint32_t band = 0U;
    while (
        band + 1U < manifest.protected_band_count
        && median >= manifest.protected_band_upper_hz_q20[band]
    ) {
        ++band;
    }
    return band;
}

struct bounded_output_candidate {
    bounded_output_candidate(
        bounded_state_index node_value,
        bounded_identity identity_value,
        std::pmr::memory_resource* memory
    )
        : node(node_value),
          identity(std::move(identity_value)),
          ownership_components(memory) {}

    bounded_output_candidate(bounded_output_candidate&&) noexcept = default;
    bounded_output_candidate& operator=(
        bounded_output_candidate&&
    ) noexcept = default;
    bounded_output_candidate(const bounded_output_candidate&) = delete;
    bounded_output_candidate& operator=(const bounded_output_candidate&) =
        delete;

    bounded_state_index node;
    bounded_identity identity;
    std::pmr::vector<std::uint32_t> ownership_components;
    std::uint32_t family_flags = 0U;
    std::uint32_t value_rank = RESONITH_PARTIAL_PATH_RANK_ABSENT;
    std::uint32_t continuity_rank = RESONITH_PARTIAL_PATH_RANK_ABSENT;
    std::uint32_t protected_rank = RESONITH_PARTIAL_PATH_RANK_ABSENT;
    std::uint32_t internal_conflicts = 0U;
    std::uint32_t band = 0U;
    std::int64_t value_score = 0;
    std::int64_t continuity_score = 0;
    std::int64_t selection_score = 0;
};

struct wide_positive_score {
    std::uint64_t high = 0U;
    std::uint64_t low = 0U;
};

wide_positive_score add_wide_score(
    wide_positive_score value,
    std::uint64_t increment
) {
    const std::uint64_t previous = value.low;
    value.low += increment;
    if (value.low < previous) {
        if (value.high == std::numeric_limits<std::uint64_t>::max()) {
            throw managed_profile_bound{};
        }
        ++value.high;
    }
    return value;
}

int compare_wide_score(
    const wide_positive_score& left,
    const wide_positive_score& right
) noexcept {
    if (left.high != right.high) {
        return left.high < right.high ? -1 : 1;
    }
    if (left.low != right.low) {
        return left.low < right.low ? -1 : 1;
    }
    return 0;
}

bool output_identity_set_less(
    const std::pmr::vector<std::size_t>& left,
    const std::pmr::vector<std::size_t>& right,
    const std::pmr::vector<bounded_output_candidate>& candidates,
    bounded_work_meter* work
) {
    const std::size_t common = std::min(left.size(), right.size());
    for (std::size_t index = 0U; index < common; ++index) {
        const int comparison = compare_identity(
            candidates[left[index]].identity,
            candidates[right[index]].identity,
            work
        );
        if (comparison != 0) {
            return comparison < 0;
        }
    }
    return left.size() < right.size();
}

void canonical_insert_identity_index(
    std::pmr::vector<std::size_t>* values,
    std::size_t candidate,
    const std::pmr::vector<bounded_output_candidate>& candidates,
    bounded_work_meter* work
) {
    std::size_t position = values->size();
    values->push_back(candidate);
    while (
        position != 0U
        && compare_identity(
            candidates[candidate].identity,
            candidates[(*values)[position - 1U]].identity,
            work
        ) < 0
    ) {
        (*values)[position] = (*values)[position - 1U];
        --position;
    }
    (*values)[position] = candidate;
}

resonith_status compute_paths_bounded(
    const resonith_partial_observation* observation_data,
    std::size_t observation_count,
    const resonith_partial_edge* edge_data,
    std::size_t edge_count,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest& path_manifest,
    resonith_partial_path_report* report,
    path_output* output,
    std::pmr::memory_resource* memory
) {
    bounded_work_meter work(path_manifest, report);
    bounded_state_arena arena(
        memory,
        path_manifest.maximum_state_records,
        report
    );
    using observation_table = std::pmr::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    >;
    observation_table observations(memory);
    observations.reserve(observation_count);
    std::pmr::vector<const resonith_partial_observation*> ordered_observations(
        memory
    );
    ordered_observations.reserve(observation_count);
    for (std::size_t index = 0U; index < observation_count; ++index) {
        observations.emplace(
            observation_data[index].observation_id,
            &observation_data[index]
        );
        ordered_observations.push_back(&observation_data[index]);
    }
    work.charge_product(observation_count, observation_count);
    std::sort(
        ordered_observations.begin(),
        ordered_observations.end(),
        [](const auto* left, const auto* right) {
            return std::tie(
                left->center_sample,
                left->resolution_id,
                left->detector_id,
                left->frequency_hz_q20,
                left->observation_id
            ) < std::tie(
                right->center_sample,
                right->resolution_id,
                right->detector_id,
                right->frequency_hz_q20,
                right->observation_id
            );
        }
    );

    using edge_rows = std::pmr::vector<const resonith_partial_edge*>;
    std::pmr::map<std::uint64_t, edge_rows> incoming(memory);
    std::pmr::unordered_map<std::uint64_t, std::uint64_t> outgoing_remaining(
        memory
    );
    outgoing_remaining.reserve(observation_count);
    for (std::size_t index = 0U; index < edge_count; ++index) {
        const resonith_partial_edge* edge = &edge_data[index];
        auto [incoming_row, inserted] = incoming.try_emplace(
            edge->target_observation_id
        );
        static_cast<void>(inserted);
        incoming_row->second.push_back(edge);
        ++outgoing_remaining[edge->source_observation_id];
    }

    using terminal_key = std::pair<std::uint64_t, std::uint64_t>;
    using state_rows = std::pmr::vector<bounded_node_reference>;
    std::pmr::map<terminal_key, state_rows> states(memory);
    std::pmr::unordered_map<std::uint64_t, std::pmr::vector<terminal_key>>
        terminal_keys_by_current(memory);
    terminal_keys_by_current.reserve(observation_count);
    std::uint64_t frontier_size = 0U;

    std::pmr::vector<bounded_family_entry> value_reservoir(memory);
    std::pmr::vector<bounded_family_entry> continuity_reservoir(memory);
    std::pmr::map<std::uint32_t, std::pmr::vector<bounded_family_entry>>
        protected_by_band(memory);

    auto add_rank = [&](std::int64_t left, std::int32_t right) {
        return right > 0
            ? saturating_add_path(
                  left,
                  right,
                  path_manifest.score_saturation,
                  &report->score_saturation_count
              )
            : left;
    };

    auto create_birth = [&](
        const resonith_partial_observation& source,
        const resonith_partial_observation& target,
        const resonith_partial_edge& edge
    ) {
        work.charge(1U);
        if (report->raw_state_count == std::numeric_limits<std::uint64_t>::max()) {
            ++report->bound_rejected_count;
            throw managed_profile_bound{};
        }
        ++report->raw_state_count;
        bounded_state_node node;
        node.first_observation_id = source.observation_id;
        node.previous_observation_id = source.observation_id;
        node.current_observation_id = target.observation_id;
        node.incoming_edge_id = edge.candidate_id;
        node.length = 2U;
        node.continuity_cost = edge.continuity_cost_q8;
        node.potential = saturating_add_path(
            source.potential_node_value_q8,
            target.potential_node_value_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.uncertainty_penalty = saturating_add_path(
            source.uncertainty_leakage_penalty_q8,
            target.uncertainty_leakage_penalty_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.provisional_program_cost = saturating_add_path(
            path_manifest.birth_cost_bits_q8,
            edge.provisional_program_cost_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        if ((edge.flags & edge_phase_usable) != 0U) {
            node.phase_error_sum = edge.phase_error_u31;
            node.phase_error_count = 1U;
        }
        node.protected_observation_count =
            (
                source.flags
                & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
            ) != 0U
            ? 1U
            : 0U;
        node.protected_observation_count +=
            (
                target.flags
                & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
            ) != 0U
            ? 1U
            : 0U;
        node.protected_rank_sum = add_rank(
            0,
            (
                source.flags
                & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
            ) != 0U
                ? source.protected_rank_q8
                : 0
        );
        node.protected_rank_sum = add_rank(
            node.protected_rank_sum,
            (
                target.flags
                & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
            ) != 0U
                ? target.protected_rank_q8
                : 0
        );
        return bounded_node_reference::adopt(
            &arena,
            arena.create(node)
        );
    };

    auto create_extension = [&](
        bounded_state_index prior_index,
        const resonith_partial_observation& previous,
        const resonith_partial_observation& source,
        const resonith_partial_observation& target,
        const resonith_partial_edge& edge
    ) {
        work.charge(1U);
        if (report->raw_state_count == std::numeric_limits<std::uint64_t>::max()) {
            ++report->bound_rejected_count;
            throw managed_profile_bound{};
        }
        ++report->raw_state_count;
        const bounded_state_node& prior = arena.at(prior_index);
        const auto second_order = second_order_cost(
            previous,
            source,
            target,
            path_manifest
        );
        if (second_order.second) {
            ++report->score_saturation_count;
        }
        bounded_state_node node;
        node.parent = prior_index;
        node.first_observation_id = prior.first_observation_id;
        node.previous_observation_id = source.observation_id;
        node.current_observation_id = target.observation_id;
        node.incoming_edge_id = edge.candidate_id;
        node.length = prior.length + 1U;
        node.second_order_cost = second_order.first;
        node.continuity_cost = saturating_add_path(
            saturating_add_path(
                prior.continuity_cost,
                edge.continuity_cost_q8,
                path_manifest.score_saturation,
                &report->score_saturation_count
            ),
            second_order.first,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.potential = saturating_add_path(
            prior.potential,
            target.potential_node_value_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.uncertainty_penalty = saturating_add_path(
            prior.uncertainty_penalty,
            target.uncertainty_leakage_penalty_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.provisional_program_cost = saturating_add_path(
            prior.provisional_program_cost,
            edge.provisional_program_cost_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        node.phase_error_sum = prior.phase_error_sum;
        node.phase_error_count = prior.phase_error_count;
        if ((edge.flags & edge_phase_usable) != 0U) {
            if (
                node.phase_error_sum
                > std::numeric_limits<std::uint64_t>::max()
                    - edge.phase_error_u31
            ) {
                node.phase_error_sum =
                    std::numeric_limits<std::uint64_t>::max();
                ++report->score_saturation_count;
            } else {
                node.phase_error_sum += edge.phase_error_u31;
            }
            if (
                node.phase_error_count
                == std::numeric_limits<std::uint32_t>::max()
            ) {
                ++report->bound_rejected_count;
                throw managed_profile_bound{};
            }
            ++node.phase_error_count;
        }
        node.protected_observation_count =
            prior.protected_observation_count;
        node.protected_rank_sum = prior.protected_rank_sum;
        if (
            (
                target.flags
                & RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK
            ) != 0U
        ) {
            if (
                node.protected_observation_count
                == std::numeric_limits<std::uint32_t>::max()
            ) {
                ++report->bound_rejected_count;
                throw managed_profile_bound{};
            }
            ++node.protected_observation_count;
            node.protected_rank_sum = add_rank(
                node.protected_rank_sum,
                target.protected_rank_q8
            );
        }
        return bounded_node_reference::adopt(
            &arena,
            arena.create(node)
        );
    };

    auto present_families = [&](bounded_state_index index) {
        const bounded_state_node& node = arena.at(index);
        if (node.length < path_manifest.minimum_path_observations) {
            return;
        }
        bounded_identity identity = materialize_identity(
            arena,
            index,
            memory,
            &work
        );
        const std::int64_t value = bounded_value_score(
            node,
            graph_manifest,
            path_manifest
        );
        const std::int64_t continuity = bounded_continuity_score(
            node,
            graph_manifest,
            path_manifest
        );

        ++report->value_family_presented_count;
        insert_family_reservoir(
            &value_reservoir,
            bounded_family_entry(
                bounded_node_reference::retain(&arena, index),
                bounded_identity(identity, memory),
                value,
                continuity,
                node.length,
                node.protected_observation_count,
                node.protected_rank_sum,
                0U
            ),
            path_manifest.top_k_value,
            bounded_family_kind::value,
            &work,
            &report->value_family_discarded_count,
            report
        );

        ++report->continuity_family_presented_count;
        insert_family_reservoir(
            &continuity_reservoir,
            bounded_family_entry(
                bounded_node_reference::retain(&arena, index),
                bounded_identity(identity, memory),
                value,
                continuity,
                node.length,
                node.protected_observation_count,
                node.protected_rank_sum,
                0U
            ),
            path_manifest.top_k_continuity,
            bounded_family_kind::continuity,
            &work,
            &report->continuity_family_discarded_count,
            report
        );

        if (node.protected_observation_count != 0U) {
            const std::uint32_t band = bounded_frequency_band(
                identity,
                observations,
                path_manifest,
                memory,
                &work
            );
            ++report->protected_family_presented_count;
            auto [band_row, inserted] = protected_by_band.try_emplace(
                band
            );
            static_cast<void>(inserted);
            insert_family_reservoir(
                &band_row->second,
                bounded_family_entry(
                    bounded_node_reference::retain(&arena, index),
                    std::move(identity),
                    value,
                    continuity,
                    node.length,
                    node.protected_observation_count,
                    node.protected_rank_sum,
                    band
                ),
                path_manifest.protected_paths_per_band,
                bounded_family_kind::protected_band,
                &work,
                &report->protected_family_discarded_count,
                report
            );
        }
    };

    for (const resonith_partial_observation* target : ordered_observations) {
        const auto incoming_row = incoming.find(target->observation_id);
        if (incoming_row == incoming.end()) {
            continue;
        }
        std::pmr::map<terminal_key, state_rows> pending(memory);
        for (const resonith_partial_edge* edge : incoming_row->second) {
            const resonith_partial_observation* source = observations.at(
                edge->source_observation_id
            );
            const terminal_key destination_key{
                source->observation_id,
                target->observation_id,
            };
            auto [destination, inserted] = pending.try_emplace(
                destination_key
            );
            static_cast<void>(inserted);
            destination->second.push_back(
                create_birth(*source, *target, *edge)
            );

            const auto terminal_rows = terminal_keys_by_current.find(
                source->observation_id
            );
            if (terminal_rows != terminal_keys_by_current.end()) {
                work.charge(terminal_rows->second.size());
                for (const terminal_key& prior_key : terminal_rows->second) {
                    const state_rows& prior_states = states.at(prior_key);
                    work.charge(prior_states.size());
                    const resonith_partial_observation* previous =
                        observations.at(prior_key.first);
                    for (const bounded_node_reference& prior : prior_states) {
                        if (
                            arena.at(prior.get()).length
                            >= path_manifest.maximum_path_observations
                        ) {
                            continue;
                        }
                        destination->second.push_back(create_extension(
                            prior.get(),
                            *previous,
                            *source,
                            *target,
                            *edge
                        ));
                    }
                }
            }

            auto remaining = outgoing_remaining.find(source->observation_id);
            if (
                remaining == outgoing_remaining.end()
                || remaining->second == 0U
            ) {
                throw std::logic_error("outgoing edge accounting mismatch");
            }
            --remaining->second;
            if (remaining->second == 0U) {
                const auto stale = terminal_keys_by_current.find(
                    source->observation_id
                );
                if (stale != terminal_keys_by_current.end()) {
                    work.charge(stale->second.size());
                    for (const terminal_key& key : stale->second) {
                        const auto row = states.find(key);
                        if (row != states.end()) {
                            frontier_size -= row->second.size();
                            states.erase(row);
                        }
                    }
                    terminal_keys_by_current.erase(stale);
                }
            }
        }

        for (auto& [key, candidates] : pending) {
            state_rows retained = retain_bounded_state_union(
                std::move(candidates),
                &arena,
                graph_manifest,
                path_manifest,
                memory,
                &work,
                report
            );
            for (const bounded_node_reference& item : retained) {
                present_families(item.get());
            }
            const auto target_outgoing = outgoing_remaining.find(key.second);
            if (
                target_outgoing == outgoing_remaining.end()
                || target_outgoing->second == 0U
            ) {
                continue;
            }
            frontier_size += retained.size();
            auto [row, inserted] = states.try_emplace(key);
            if (!inserted) {
                throw std::logic_error("duplicate terminal bucket");
            }
            row->second = std::move(retained);
            auto [index_row, index_inserted] =
                terminal_keys_by_current.try_emplace(key.second);
            static_cast<void>(index_inserted);
            index_row->second.push_back(key);
        }
        report->frontier_peak = std::max(
            report->frontier_peak,
            frontier_size
        );
        if (frontier_size > path_manifest.maximum_frontier_states) {
            ++report->bound_rejected_count;
            throw managed_profile_bound{};
        }
    }

    /*
     * Family reservoirs now own every possible output. Releasing terminal
     * buckets proves that non-output history is reclaimable before selection.
     */
    states.clear();
    terminal_keys_by_current.clear();
    frontier_size = 0U;
    static_cast<void>(frontier_size);

    std::pmr::vector<bounded_family_entry> protected_reservoir(memory);
    for (auto& [band, rows] : protected_by_band) {
        static_cast<void>(band);
        while (!rows.empty()) {
            bounded_family_entry candidate = std::move(rows.back());
            rows.pop_back();
            insert_family_reservoir(
                &protected_reservoir,
                std::move(candidate),
                path_manifest.top_k_protected,
                bounded_family_kind::protected_global,
                &work,
                &report->protected_family_discarded_count,
                report
            );
        }
    }
    protected_by_band.clear();

    std::pmr::vector<bounded_output_candidate> union_paths(memory);
    union_paths.reserve(
        value_reservoir.size()
        + continuity_reservoir.size()
        + protected_reservoir.size()
    );
    auto merge_family = [&](
        const std::pmr::vector<bounded_family_entry>& family,
        std::uint32_t flag
    ) {
        for (std::size_t rank = 0U; rank < family.size(); ++rank) {
            const bounded_family_entry& source = family[rank];
            std::size_t found = union_paths.size();
            for (std::size_t index = 0U; index < union_paths.size(); ++index) {
                if (
                    compare_identity(
                        union_paths[index].identity,
                        source.identity,
                        &work
                    ) == 0
                ) {
                    found = index;
                    break;
                }
            }
            if (found == union_paths.size()) {
                union_paths.emplace_back(
                    source.node.get(),
                    bounded_identity(source.identity, memory),
                    memory
                );
                found = union_paths.size() - 1U;
            } else {
                ++report->output_deduplicated_count;
            }
            bounded_output_candidate& destination = union_paths[found];
            destination.family_flags |= flag;
            if (flag == RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL) {
                destination.value_rank = static_cast<std::uint32_t>(rank);
            } else if (flag == RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY) {
                destination.continuity_rank =
                    static_cast<std::uint32_t>(rank);
            } else {
                destination.protected_rank =
                    static_cast<std::uint32_t>(rank);
            }
        }
    };
    merge_family(
        value_reservoir,
        RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL
    );
    merge_family(
        continuity_reservoir,
        RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY
    );
    merge_family(
        protected_reservoir,
        RESONITH_PARTIAL_PATH_FAMILY_PROTECTED_WEAK
    );
    if (union_paths.size() > path_manifest.maximum_path_records) {
        ++report->bound_rejected_count;
        throw managed_profile_bound{};
    }

    for (bounded_output_candidate& candidate : union_paths) {
        const bounded_state_node& node = arena.at(candidate.node);
        candidate.value_score = bounded_value_score(
            node,
            graph_manifest,
            path_manifest
        );
        candidate.continuity_score = bounded_continuity_score(
            node,
            graph_manifest,
            path_manifest
        );
        candidate.selection_score = std::max<std::int64_t>({
            0,
            candidate.value_score,
            candidate.continuity_score,
        });
    }
    for (std::size_t index = 1U; index < union_paths.size(); ++index) {
        bounded_output_candidate moving = std::move(union_paths[index]);
        std::size_t position = index;
        while (position != 0U) {
            work.charge(1U);
            const bounded_output_candidate& previous =
                union_paths[position - 1U];
            bool better = moving.value_score > previous.value_score;
            if (moving.value_score == previous.value_score) {
                better = moving.continuity_score > previous.continuity_score;
                if (moving.continuity_score == previous.continuity_score) {
                    better = compare_identity(
                        moving.identity,
                        previous.identity,
                        &work
                    ) < 0;
                }
            }
            if (!better) {
                break;
            }
            union_paths[position] = std::move(union_paths[position - 1U]);
            --position;
        }
        union_paths[position] = std::move(moving);
    }

    for (bounded_output_candidate& candidate : union_paths) {
        work.charge_product(
            candidate.identity.observations.size(),
            candidate.identity.observations.size()
        );
        candidate.ownership_components.reserve(
            candidate.identity.observations.size()
        );
        for (const std::uint64_t identifier : candidate.identity.observations) {
            candidate.ownership_components.push_back(
                observations.at(identifier)->ownership_component
            );
        }
        std::sort(
            candidate.ownership_components.begin(),
            candidate.ownership_components.end()
        );
        const auto unique_end = std::unique(
            candidate.ownership_components.begin(),
            candidate.ownership_components.end()
        );
        candidate.internal_conflicts = static_cast<std::uint32_t>(
            candidate.ownership_components.end() - unique_end
        );
        candidate.ownership_components.erase(
            unique_end,
            candidate.ownership_components.end()
        );
        report->internal_conflict_count += candidate.internal_conflicts;
        candidate.band = bounded_frequency_band(
            candidate.identity,
            observations,
            path_manifest,
            memory,
            &work
        );
    }

    std::pmr::vector<std::size_t> selection_candidates(memory);
    work.charge(union_paths.size());
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        if (
            union_paths[index].internal_conflicts == 0U
            && union_paths[index].selection_score > 0
        ) {
            selection_candidates.push_back(index);
        }
    }
    report->selected_candidate_count = selection_candidates.size();
    const std::uint64_t candidate_count = selection_candidates.size();
    const std::uint64_t pair_left = candidate_count > 1U
        ? (
            candidate_count % 2U == 0U
                ? candidate_count / 2U
                : candidate_count
        )
        : 0U;
    const std::uint64_t pair_right = candidate_count > 1U
        ? (
            candidate_count % 2U == 0U
                ? candidate_count - 1U
                : (candidate_count - 1U) / 2U
        )
        : 0U;
    if (
        pair_left != 0U
        && pair_right
            > std::numeric_limits<std::uint64_t>::max() / pair_left
    ) {
        ++report->bound_rejected_count;
        throw managed_profile_bound{};
    }
    const std::uint64_t pair_count = pair_left * pair_right;
    work.charge(pair_count);
    if (
        selection_candidates.size() != 0U
        && selection_candidates.size()
            > std::numeric_limits<std::size_t>::max()
                / selection_candidates.size()
    ) {
        ++report->bound_rejected_count;
        throw managed_profile_bound{};
    }
    std::pmr::vector<std::uint8_t> conflicts(
        selection_candidates.size() * selection_candidates.size(),
        0U,
        memory
    );
    for (std::size_t left = 0U; left < selection_candidates.size(); ++left) {
        for (
            std::size_t right = left + 1U;
            right < selection_candidates.size();
            ++right
        ) {
            const auto& first =
                union_paths[selection_candidates[left]].ownership_components;
            const auto& second =
                union_paths[selection_candidates[right]].ownership_components;
            work.charge(first.size() + second.size());
            std::size_t first_index = 0U;
            std::size_t second_index = 0U;
            bool conflict = false;
            while (
                first_index < first.size()
                && second_index < second.size()
            ) {
                if (first[first_index] == second[second_index]) {
                    conflict = true;
                    break;
                }
                if (first[first_index] < second[second_index]) {
                    ++first_index;
                } else {
                    ++second_index;
                }
            }
            if (conflict) {
                conflicts[
                    left * selection_candidates.size() + right
                ] = 1U;
                conflicts[
                    right * selection_candidates.size() + left
                ] = 1U;
                ++report->cross_path_conflict_count;
            }
        }
    }

    std::pmr::vector<std::uint8_t> selected(union_paths.size(), 0U, memory);
    if (
        selection_candidates.size()
        <= path_manifest.exact_set_candidate_limit
    ) {
        report->solver = RESONITH_PARTIAL_PATH_SOLVER_EXACT_SMALL;
        const std::uint64_t mask_count =
            1ULL << selection_candidates.size();
        wide_positive_score best_score{};
        bool best_initialized = false;
        std::pmr::vector<std::size_t> best(memory);
        std::pmr::vector<std::size_t> current(memory);
        best.reserve(selection_candidates.size());
        current.reserve(selection_candidates.size());
        for (std::uint64_t mask = 0U; mask < mask_count; ++mask) {
            work.charge(1U);
            current.clear();
            wide_positive_score score{};
            bool valid = true;
            for (
                std::size_t candidate = 0U;
                candidate < selection_candidates.size();
                ++candidate
            ) {
                work.charge(1U);
                if ((mask & (1ULL << candidate)) == 0U) {
                    continue;
                }
                for (const std::size_t incumbent : current) {
                    work.charge(1U);
                    work.charge(selection_candidates.size());
                    const auto incumbent_position = static_cast<std::size_t>(
                        std::find(
                            selection_candidates.begin(),
                            selection_candidates.end(),
                            incumbent
                        ) - selection_candidates.begin()
                    );
                    if (
                        conflicts[
                            candidate * selection_candidates.size()
                            + incumbent_position
                        ] != 0U
                    ) {
                        valid = false;
                        break;
                    }
                }
                if (!valid) {
                    break;
                }
                const std::size_t output_index =
                    selection_candidates[candidate];
                score = add_wide_score(
                    score,
                    static_cast<std::uint64_t>(
                        union_paths[output_index].selection_score
                    )
                );
                canonical_insert_identity_index(
                    &current,
                    output_index,
                    union_paths,
                    &work
                );
            }
            if (!valid) {
                continue;
            }
            const int score_comparison = compare_wide_score(score, best_score);
            if (
                !best_initialized
                || score_comparison > 0
                || (
                    score_comparison == 0
                    && output_identity_set_less(
                        current,
                        best,
                        union_paths,
                        &work
                    )
                )
            ) {
                best_initialized = true;
                best_score = score;
                best.assign(current.begin(), current.end());
            }
        }
        for (const std::size_t index : best) {
            selected[index] = 1U;
        }
    } else {
        report->solver = RESONITH_PARTIAL_PATH_SOLVER_BOUNDED_GREEDY;
        std::pmr::vector<std::size_t> order(memory);
        for (const std::size_t index : selection_candidates) {
            std::size_t position = order.size();
            order.push_back(index);
            while (position != 0U) {
                const std::size_t previous = order[position - 1U];
                bool better =
                    union_paths[index].selection_score
                    > union_paths[previous].selection_score;
                if (
                    union_paths[index].selection_score
                    == union_paths[previous].selection_score
                ) {
                    better = compare_identity(
                        union_paths[index].identity,
                        union_paths[previous].identity,
                        &work
                    ) < 0;
                }
                if (!better) {
                    break;
                }
                order[position] = previous;
                --position;
            }
            order[position] = index;
        }
        std::pmr::vector<std::size_t> accepted(memory);
        for (const std::size_t candidate : order) {
            bool conflict = false;
            work.charge(selection_candidates.size());
            const auto candidate_position = static_cast<std::size_t>(
                std::find(
                    selection_candidates.begin(),
                    selection_candidates.end(),
                    candidate
                ) - selection_candidates.begin()
            );
            for (const std::size_t incumbent : accepted) {
                work.charge(1U);
                work.charge(selection_candidates.size());
                const auto incumbent_position = static_cast<std::size_t>(
                    std::find(
                        selection_candidates.begin(),
                        selection_candidates.end(),
                        incumbent
                    ) - selection_candidates.begin()
                );
                if (
                    conflicts[
                        candidate_position * selection_candidates.size()
                        + incumbent_position
                    ] != 0U
                ) {
                    conflict = true;
                    break;
                }
            }
            if (!conflict) {
                accepted.push_back(candidate);
                selected[candidate] = 1U;
            }
        }
    }
    work.charge(selected.size());
    report->selected_path_count = static_cast<std::uint64_t>(
        std::count(
            selected.begin(),
            selected.end(),
            static_cast<std::uint8_t>(1U)
        )
    );

    std::uint64_t entry_offset = 0U;
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        bounded_output_candidate& candidate = union_paths[index];
        const bounded_state_node& node = arena.at(candidate.node);
        if (
            candidate.identity.observations.size()
            > path_manifest.maximum_total_entries - entry_offset
        ) {
            ++report->bound_rejected_count;
            throw managed_profile_bound{};
        }
        work.charge(candidate.identity.observations.size());
        std::pmr::vector<std::int32_t> second_order(
            candidate.identity.observations.size(),
            0,
            memory
        );
        bounded_state_index cursor = candidate.node;
        std::size_t position = second_order.size();
        while (cursor != bounded_state_sentinel) {
            const bounded_state_node& state = arena.at(cursor);
            --position;
            second_order[position] = state.second_order_cost;
            if (state.parent == bounded_state_sentinel) {
                --position;
                second_order[position] = 0;
            }
            cursor = state.parent;
        }
        if (position != 0U) {
            throw std::logic_error("output backpointer length mismatch");
        }
        std::uint32_t flags = 0U;
        if (selected[index] != 0U) {
            flags |= RESONITH_PARTIAL_PATH_SELECTED;
        }
        if (candidate.internal_conflicts != 0U) {
            flags |= RESONITH_PARTIAL_PATH_INTERNAL_OWNERSHIP_CONFLICT;
        }
        if (node.phase_error_count != 0U) {
            flags |= RESONITH_PARTIAL_PATH_PHASE_EVIDENCE;
        }
        const std::int64_t packed_program_cost = saturating_add_path(
            node.provisional_program_cost,
            path_manifest.death_cost_bits_q8,
            path_manifest.score_saturation,
            &report->score_saturation_count
        );
        output->paths.push_back(resonith_partial_path{
            sizeof(resonith_partial_path),
            RESONITH_PARTIAL_PATH_ABI_VERSION,
            index,
            entry_offset,
            static_cast<std::uint32_t>(
                candidate.identity.observations.size()
            ),
            candidate.family_flags,
            candidate.identity.observations.back(),
            candidate.continuity_score,
            node.potential,
            node.uncertainty_penalty,
            packed_program_cost,
            candidate.selection_score,
            node.phase_error_sum,
            node.phase_error_count,
            candidate.internal_conflicts,
            candidate.band,
            candidate.value_rank,
            candidate.continuity_rank,
            candidate.protected_rank,
            flags,
            {0U, 0U, 0U, 0U, 0U},
        });
        for (
            std::size_t entry = 0U;
            entry < candidate.identity.observations.size();
            ++entry
        ) {
            const std::uint64_t observation_id =
                candidate.identity.observations[entry];
            output->entries.push_back(resonith_partial_path_entry{
                sizeof(resonith_partial_path_entry),
                RESONITH_PARTIAL_PATH_ABI_VERSION,
                observation_id,
                candidate.identity.incoming_edges[entry],
                observations.at(observation_id)->ownership_component,
                second_order[entry],
                0U,
                {0U, 0U, 0U},
            });
        }
        entry_offset += candidate.identity.observations.size();
    }

    report->required_path_count = output->paths.size();
    report->required_entry_count = output->entries.size();
    work.charge(output->paths.size());
    for (const resonith_partial_path& path : output->paths) {
        report->value_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_LOCAL_POTENTIAL
        ) != 0U;
        report->continuity_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_CONTINUITY
        ) != 0U;
        report->protected_family_count += (
            path.family_flags
            & RESONITH_PARTIAL_PATH_FAMILY_PROTECTED_WEAK
        ) != 0U;
    }
    return RESONITH_STATUS_OK;
}

}  // namespace

namespace resonith::internal {

bool partial_graph_environmental_oom_probe() noexcept {
    class failing_resource final : public std::pmr::memory_resource {
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
    } failing;

    try {
        counting_memory_resource counted(1024U, &failing);
        std::pmr::vector<std::uint8_t> values(&counted);
        values.reserve(1U);
    } catch (const environmental_out_of_memory&) {
        return true;
    } catch (...) {
        return false;
    }
    return false;
}

}  // namespace resonith::internal

extern "C" resonith_status resonith_partial_graph_paths_cpu_v2(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_edge* edges,
    std::size_t edge_count,
    const resonith_partial_graph_manifest* graph_manifest,
    const resonith_partial_path_manifest* path_manifest,
    resonith_partial_path* paths,
    std::size_t path_capacity,
    resonith_partial_path_entry* entries,
    std::size_t entry_capacity,
    resonith_partial_path_report* report
) {
    if (
        resolutions == nullptr
        || observations == nullptr
        || edges == nullptr
        || graph_manifest == nullptr
        || path_manifest == nullptr
        || report == nullptr
        || graph_manifest->struct_size != sizeof(*graph_manifest)
        || graph_manifest->abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
        || path_manifest->struct_size != sizeof(*path_manifest)
        || path_manifest->abi_version != RESONITH_PARTIAL_PATH_ABI_VERSION
        || report->struct_size != sizeof(*report)
        || report->abi_version != RESONITH_PARTIAL_PATH_ABI_VERSION
        || !reserved_zero(*report)
        || (
            (paths == nullptr || entries == nullptr)
            && (
                paths != nullptr
                || entries != nullptr
                || path_capacity != 0U
                || entry_capacity != 0U
            )
        )
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    resonith_partial_path_report local_report{};
    local_report.struct_size = sizeof(local_report);
    local_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (!valid_path_manifest(*path_manifest, *graph_manifest)) {
        *report = local_report;
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    counting_memory_resource managed_memory(
        path_manifest->maximum_managed_bytes
    );
    struct peak_report_guard {
        counting_memory_resource* memory;
        resonith_partial_path_report* local;
        resonith_partial_path_report* destination;

        ~peak_report_guard() {
            local->peak_live_managed_bytes = memory->peak_bytes();
            destination->peak_live_managed_bytes = memory->peak_bytes();
        }
    } peak_guard{&managed_memory, &local_report, report};
    try {
    bounded_work_meter preflight_work(*path_manifest, &local_report);
    preflight_work.charge_product(resolution_count, resolution_count);
    preflight_work.charge_product(observation_count, observation_count);
    preflight_work.charge_product(observation_count, observation_count);
    preflight_work.charge(edge_count);
    if (
        !valid_path_inputs(
            resolutions,
            resolution_count,
            observations,
            observation_count,
            edges,
            edge_count,
            *graph_manifest,
            &managed_memory,
            [&preflight_work](std::uint64_t amount) {
                preflight_work.charge(amount);
            }
        )
    ) {
        *report = local_report;
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    const auto fingerprint = input_fingerprint(
        resolutions,
        resolution_count,
        observations,
        observation_count,
        edges,
        edge_count,
        *graph_manifest,
        *path_manifest,
        &managed_memory
    );
    std::copy(
        fingerprint.begin(),
        fingerprint.end(),
        local_report.input_fingerprint
    );
    const bool fill = paths != nullptr;
    const bool expected_present = std::any_of(
        std::begin(path_manifest->expected_input_fingerprint),
        std::end(path_manifest->expected_input_fingerprint),
        [](std::uint64_t item) { return item != 0U; }
    );
    if (
        expected_present
        && !std::equal(
            fingerprint.begin(),
            fingerprint.end(),
            path_manifest->expected_input_fingerprint
        )
    ) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT;
        *report = local_report;
        return RESONITH_STATUS_HASH_MISMATCH;
    }
    if (fill && !expected_present) {
        *report = local_report;
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    path_output output(&managed_memory);
    const resonith_status status = compute_paths_bounded(
        observations,
        observation_count,
        edges,
        edge_count,
        *graph_manifest,
        *path_manifest,
        &local_report,
        &output,
        &managed_memory
    );
    if (status != RESONITH_STATUS_OK) {
        *report = local_report;
        return status;
    }
    auto output_hash = fingerprint_begin();
    if (!output.paths.empty()) {
        fingerprint_bytes(
            &output_hash,
            output.paths.data(),
            output.paths.size() * sizeof(resonith_partial_path)
        );
    }
    if (!output.entries.empty()) {
        fingerprint_bytes(
            &output_hash,
            output.entries.data(),
            output.entries.size() * sizeof(resonith_partial_path_entry)
        );
    }
    std::copy(
        output_hash.begin(),
        output_hash.end(),
        local_report.output_fingerprint
    );
    if (!fill) {
        *report = local_report;
        return RESONITH_STATUS_OK;
    }
    if (
        path_capacity < output.paths.size()
        || entry_capacity < output.entries.size()
    ) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_OUTPUT_TOO_SMALL;
        *report = local_report;
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    std::copy(output.paths.begin(), output.paths.end(), paths);
    std::copy(output.entries.begin(), output.entries.end(), entries);
    local_report.written_path_count = output.paths.size();
    local_report.written_entry_count = output.entries.size();
    *report = local_report;
    return RESONITH_STATUS_OK;
    } catch (const managed_profile_bound&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        ++local_report.bound_rejected_count;
        *report = local_report;
        return RESONITH_STATUS_PROFILE_BOUND;
    } catch (const environmental_out_of_memory&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM;
        *report = local_report;
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (const std::bad_alloc&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM;
        *report = local_report;
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (...) {
        *report = local_report;
        return RESONITH_STATUS_MALFORMED;
    }
}
