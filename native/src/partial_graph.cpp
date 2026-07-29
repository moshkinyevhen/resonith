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
#include <optional>
#include <set>
#include <stdexcept>
#include <tuple>
#include <type_traits>
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
class memory_provenance_failure final : public std::exception {};

using allocation_permit_callback = void (*)(bool) noexcept;

thread_local allocation_permit_callback test_allocation_permit_callback =
    nullptr;
thread_local std::pmr::memory_resource* test_upstream_resource = nullptr;

std::pmr::memory_resource* selected_upstream_resource() noexcept {
    return test_upstream_resource != nullptr
        ? test_upstream_resource
        : std::pmr::new_delete_resource();
}

class checked_upstream_scope {
public:
    checked_upstream_scope() noexcept {
        if (test_allocation_permit_callback != nullptr) {
            test_allocation_permit_callback(true);
        }
    }

    checked_upstream_scope(const checked_upstream_scope&) = delete;
    checked_upstream_scope& operator=(const checked_upstream_scope&) = delete;

    ~checked_upstream_scope() {
        if (test_allocation_permit_callback != nullptr) {
            test_allocation_permit_callback(false);
        }
    }
};

enum class range_status {
    ok,
    invalid,
    overflow,
};

struct byte_range {
    std::uintptr_t begin = 0U;
    std::uintptr_t end = 0U;

    [[nodiscard]] bool empty() const noexcept {
        return begin == end;
    }
};

range_status checked_byte_range(
    const void* pointer,
    std::size_t count,
    std::size_t item_size,
    std::size_t alignment,
    bool require_pointer,
    byte_range* result
) noexcept {
    if (
        result == nullptr
        || item_size == 0U
        || alignment == 0U
        || (pointer == nullptr && (require_pointer || count != 0U))
    ) {
        return range_status::invalid;
    }
    if (pointer == nullptr) {
        *result = {};
        return range_status::ok;
    }
    const std::uintptr_t begin = reinterpret_cast<std::uintptr_t>(pointer);
    if (begin % alignment != 0U) {
        return range_status::invalid;
    }
    if (
        count > (
            std::numeric_limits<std::uintptr_t>::max() - begin
        ) / item_size
    ) {
        return range_status::overflow;
    }
    *result = byte_range{begin, begin + count * item_size};
    return range_status::ok;
}

bool ranges_overlap(const byte_range& left, const byte_range& right) noexcept {
    return !left.empty()
        && !right.empty()
        && left.begin < right.end
        && right.begin < left.end;
}

template <std::size_t Count>
bool pairwise_disjoint(const std::array<byte_range, Count>& ranges) noexcept {
    for (std::size_t left = 0U; left < Count; ++left) {
        for (std::size_t right = left + 1U; right < Count; ++right) {
            if (ranges_overlap(ranges[left], ranges[right])) {
                return false;
            }
        }
    }
    return true;
}

class counting_memory_resource final : public std::pmr::memory_resource {
public:
    using page_prepare_callback = void (*)(void*, std::uint64_t);
    using page_transition_callback =
        bool (*)(void*, std::uint64_t) noexcept;

    explicit counting_memory_resource(
        std::uint64_t limit,
        std::pmr::memory_resource* upstream = nullptr,
        void* page_context = nullptr,
        page_prepare_callback prepare_pages = nullptr,
        page_transition_callback commit_pages = nullptr,
        page_transition_callback cancel_pages = nullptr,
        page_transition_callback release_pages = nullptr
    ) noexcept
        : limit_(limit),
          upstream_(
              upstream != nullptr ? upstream : selected_upstream_resource()
          ),
          page_context_(page_context),
          prepare_pages_(prepare_pages),
          commit_pages_(commit_pages),
          cancel_pages_(cancel_pages),
          release_pages_(release_pages) {}

    [[nodiscard]] std::uint64_t reserved_bytes() const noexcept {
        return peak_reserved_;
    }

    [[nodiscard]] std::uint64_t committed_bytes() const noexcept {
        return peak_committed_;
    }

    [[nodiscard]] std::uint64_t peak_bytes() const noexcept {
        return peak_live_;
    }

    [[nodiscard]] std::uint64_t current_reserved_bytes() const noexcept {
        return reserved_;
    }

    [[nodiscard]] std::uint64_t current_committed_bytes() const noexcept {
        return committed_;
    }

    [[nodiscard]] std::uint64_t current_live_bytes() const noexcept {
        return live_;
    }

    [[nodiscard]] bool healthy() const noexcept {
        return healthy_
            && reserved_ == committed_
            && committed_ == live_;
    }

private:
    void* do_allocate(std::size_t bytes, std::size_t alignment) override {
        const auto requested = static_cast<std::uint64_t>(bytes);
        if (
            requested > limit_
            || live_ > limit_ - requested
        ) {
            throw managed_profile_bound{};
        }
        const std::uint64_t candidate = live_ + requested;
        reserved_ = candidate;
        peak_reserved_ = std::max(peak_reserved_, reserved_);
        const std::uint64_t pages =
            requested / 4096U + (requested % 4096U != 0U ? 1U : 0U);
        if (prepare_pages_ != nullptr) {
            try {
                prepare_pages_(page_context_, pages);
            } catch (...) {
                reserved_ = committed_;
                throw;
            }
        }
        void* result = nullptr;
        try {
            checked_upstream_scope permit;
            result = upstream_->allocate(bytes, alignment);
        } catch (const std::bad_alloc&) {
            const bool cancelled = cancel_pages_ == nullptr
                || cancel_pages_(page_context_, pages);
            reserved_ = committed_;
            if (!cancelled) {
                healthy_ = false;
                throw memory_provenance_failure{};
            }
            throw environmental_out_of_memory{};
        } catch (...) {
            const bool cancelled = cancel_pages_ == nullptr
                || cancel_pages_(page_context_, pages);
            reserved_ = committed_;
            if (!cancelled) {
                healthy_ = false;
            }
            throw memory_provenance_failure{};
        }
        const bool committed = commit_pages_ == nullptr
            || commit_pages_(page_context_, pages);
        if (!committed) {
            healthy_ = false;
            {
                checked_upstream_scope permit;
                upstream_->deallocate(result, bytes, alignment);
            }
            if (
                cancel_pages_ != nullptr
                && !cancel_pages_(page_context_, pages)
            ) {
                healthy_ = false;
            }
            reserved_ = committed_;
            throw memory_provenance_failure{};
        }
        committed_ = candidate;
        peak_committed_ = std::max(peak_committed_, committed_);
        live_ = candidate;
        peak_live_ = std::max(peak_live_, live_);
        return result;
    }

    void do_deallocate(
        void* pointer,
        std::size_t bytes,
        std::size_t alignment
    ) override {
        const std::uint64_t pages =
            static_cast<std::uint64_t>(bytes) / 4096U
            + (
                static_cast<std::uint64_t>(bytes) % 4096U != 0U
                    ? 1U
                    : 0U
            );
        const auto released = static_cast<std::uint64_t>(bytes);
        const bool valid_counts = released <= reserved_
            && released <= committed_
            && released <= live_;
        if (!valid_counts) {
            healthy_ = false;
        }
        if (
            release_pages_ != nullptr
            && !release_pages_(page_context_, pages)
        ) {
            healthy_ = false;
        }
        {
            checked_upstream_scope permit;
            upstream_->deallocate(pointer, bytes, alignment);
        }
        if (valid_counts) {
            reserved_ -= released;
            committed_ -= released;
            live_ -= released;
        }
    }

    bool do_is_equal(
        const std::pmr::memory_resource& other
    ) const noexcept override {
        return this == &other;
    }

    std::uint64_t limit_;
    std::pmr::memory_resource* upstream_;
    void* page_context_;
    page_prepare_callback prepare_pages_;
    page_transition_callback commit_pages_;
    page_transition_callback cancel_pages_;
    page_transition_callback release_pages_;
    std::uint64_t reserved_ = 0U;
    std::uint64_t committed_ = 0U;
    std::uint64_t live_ = 0U;
    std::uint64_t peak_reserved_ = 0U;
    std::uint64_t peak_committed_ = 0U;
    std::uint64_t peak_live_ = 0U;
    bool healthy_ = true;
};

constexpr std::uint64_t maximum_edge_api_managed_bytes =
    RESONITH_PARTIAL_MAX_HOST_BYTES;

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

template <typename Vector, typename Less, typename WorkCharge>
void stable_merge_sort_v1(
    Vector* values,
    Less&& less,
    WorkCharge&& charge_work
) {
    if (values->size() < 2U) {
        return;
    }
    Vector scratch(values->get_allocator());
    scratch.reserve(values->size());
    const std::size_t count = values->size();
    bool source_is_canonical = true;
    std::size_t width = 1U;
    while (width < count) {
        Vector& source = source_is_canonical ? *values : scratch;
        Vector& destination = source_is_canonical ? scratch : *values;
        destination.clear();
        for (std::size_t base = 0U; base < count;) {
            const std::size_t middle = std::min(
                count,
                base + width
            );
            const std::size_t end = std::min(
                count,
                middle + width
            );
            std::size_t left = base;
            std::size_t right = middle;
            while (left < middle || right < end) {
                bool take_right = false;
                if (left < middle && right < end) {
                    charge_work(RESONITH_PARTIAL_WORK_MERGE_COMPARE, 1U);
                    take_right = less(source[right], source[left]);
                } else {
                    take_right = left == middle;
                }
                charge_work(RESONITH_PARTIAL_WORK_MERGE_MOVE, 1U);
                if (take_right) {
                    destination.push_back(std::move(source[right]));
                    ++right;
                } else {
                    destination.push_back(std::move(source[left]));
                    ++left;
                }
            }
            base = end;
        }
        source_is_canonical = !source_is_canonical;
        if (width > count / 2U) {
            width = count;
        } else {
            width *= 2U;
        }
    }
    if (!source_is_canonical) {
        values->clear();
        values->reserve(count);
        for (auto& value : scratch) {
            charge_work(RESONITH_PARTIAL_WORK_MERGE_MOVE, 1U);
            values->push_back(std::move(value));
        }
    }
}

class deterministic_resolution_table {
public:
    struct record {
        std::uint32_t first;
        resolution_record second;
    };

    template <typename WorkCharge>
    deterministic_resolution_table(
        std::pmr::memory_resource* memory,
        WorkCharge* charge_work
    )
        : values_(memory),
          context_(charge_work),
          sink_(&emit_adapter<WorkCharge>) {}

    bool contains(std::uint32_t key) const {
        return find(key) != nullptr;
    }

    void emplace(std::uint32_t key, resolution_record value) {
        const auto [position, found] = locate(key);
        if (found) {
            throw std::logic_error("duplicate resolution key");
        }
        values_.insert(
            values_.begin() + static_cast<std::ptrdiff_t>(position),
            record{key, value}
        );
    }

    const record* find(std::uint32_t key) const {
        const auto [position, found] = locate(key);
        return found ? &values_[position] : nullptr;
    }

    resolution_record at(std::uint32_t key) const {
        const record* item = find(key);
        if (item == nullptr) {
            throw std::logic_error("missing resolution key");
        }
        return item->second;
    }

private:
    template <typename WorkCharge>
    static void emit_adapter(
        const void* context,
        resonith_partial_path_work_event event,
        std::uint64_t amount
    ) {
        (*static_cast<const WorkCharge*>(context))(event, amount);
    }

    std::pair<std::size_t, bool> locate(std::uint32_t key) const {
        std::size_t first = 0U;
        std::size_t last = values_.size();
        while (first < last) {
            const std::size_t middle = first + (last - first) / 2U;
            sink_(context_, RESONITH_PARTIAL_WORK_LOOKUP, 1U);
            const std::uint32_t value = values_[middle].first;
            if (value == key) {
                return {middle, true};
            }
            if (value < key) {
                first = middle + 1U;
            } else {
                last = middle;
            }
        }
        return {first, false};
    }

    std::pmr::vector<record> values_;
    const void* context_;
    void (*sink_)(
        const void*,
        resonith_partial_path_work_event,
        std::uint64_t
    );
};

template <typename ResolutionTable, typename WorkCharge>
bool valid_manifest(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_graph_manifest& manifest,
    ResolutionTable* table,
    WorkCharge&& charge_work
) {
    charge_work(RESONITH_PARTIAL_WORK_VALIDATE_RECORD, 1U);
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
        charge_work(RESONITH_PARTIAL_WORK_VALIDATE_RECORD, 1U);
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

template <typename ResolutionTable, typename IdVector, typename WorkCharge>
bool valid_observations(
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    std::uint32_t sample_rate,
    const ResolutionTable& resolutions,
    IdVector* ids,
    WorkCharge&& charge_work
) {
    ids->reserve(observation_count);
    const std::int64_t nyquist_q20 =
        static_cast<std::int64_t>(sample_rate / 2U) << 20U;
    for (std::size_t index = 0U; index < observation_count; ++index) {
        charge_work(RESONITH_PARTIAL_WORK_VALIDATE_RECORD, 1U);
        const resonith_partial_observation& item = observations[index];
        const auto* resolution = resolutions.find(item.resolution_id);
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || item.frequency_hz_q20 < 0
            || item.frequency_hz_q20 > nyquist_q20
            || item.phase_uncertainty_u31 > (1U << 31U)
            || resolution == nullptr
            || item.center_sample
                != static_cast<std::uint64_t>(item.frame_index)
                    * resolution->second.hop_samples
            || !reserved_zero(item)
        ) {
            return false;
        }
        ids->push_back(item.observation_id);
    }
    stable_merge_sort_v1(
        ids,
        [](std::uint64_t left, std::uint64_t right) {
            return left < right;
        },
        charge_work
    );
    for (std::size_t index = 1U; index < ids->size(); ++index) {
        charge_work(RESONITH_PARTIAL_WORK_LOOKUP, 1U);
        if ((*ids)[index - 1U] == (*ids)[index]) {
            return false;
        }
    }
    return true;
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
    std::pmr::vector<std::size_t> canonical_observation_order(
        observation_count,
        memory
    );
    for (std::size_t index = 0U; index < observation_count; ++index) {
        canonical_observation_order[index] = index;
    }
    stable_merge_sort_v1(
        &canonical_observation_order,
        [observations](
            std::size_t left_index,
            std::size_t right_index
        ) {
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
        },
        charge_work
    );

    std::uint64_t candidate_id = 0U;
    for (const std::size_t source_index : canonical_observation_order) {
        charge_work(RESONITH_PARTIAL_WORK_GRAPH_SOURCE, 1U);
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
                charge_work(RESONITH_PARTIAL_WORK_GRAPH_GAP, 1U);
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
                    charge_work(RESONITH_PARTIAL_WORK_GRAPH_TARGET, 1U);
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
                stable_merge_sort_v1(
                    &targets,
                    [](
                        const ranked_target& left,
                        const ranked_target& right
                    ) {
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
                    },
                    charge_work
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
                        charge_work(RESONITH_PARTIAL_WORK_GRAPH_CYCLE, 1U);
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
    /*
     * R-197 phase 1: validate pointer topology and freeze caller input before
     * any semantic work. The edge payload and output_count are published only
     * after complete canonical enumeration succeeds.
     */
    if (
        resolutions == nullptr
        || resolution_count == 0U
        || (observations == nullptr && observation_count != 0U)
        || manifest == nullptr
        || output_count == nullptr
        || (output == nullptr && output_capacity != 0U)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    byte_range resolution_range{};
    byte_range observation_range{};
    byte_range manifest_range{};
    byte_range output_range{};
    byte_range count_range{};
    const std::array<range_status, 5U> range_results = {
        checked_byte_range(
            resolutions,
            resolution_count,
            sizeof(*resolutions),
            alignof(resonith_partial_resolution),
            true,
            &resolution_range
        ),
        checked_byte_range(
            observations,
            observation_count,
            sizeof(*observations),
            alignof(resonith_partial_observation),
            false,
            &observation_range
        ),
        checked_byte_range(
            manifest,
            1U,
            sizeof(*manifest),
            alignof(resonith_partial_graph_manifest),
            true,
            &manifest_range
        ),
        checked_byte_range(
            output,
            output_capacity,
            sizeof(*output),
            alignof(resonith_partial_edge),
            output != nullptr,
            &output_range
        ),
        checked_byte_range(
            output_count,
            1U,
            sizeof(*output_count),
            alignof(std::size_t),
            true,
            &count_range
        ),
    };
    if (std::find(range_results.begin(), range_results.end(), range_status::invalid)
        != range_results.end()) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (std::find(range_results.begin(), range_results.end(), range_status::overflow)
        != range_results.end()) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (!pairwise_disjoint(std::array{
            resolution_range,
            observation_range,
            manifest_range,
            output_range,
            count_range,
        })) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    resonith_partial_graph_manifest manifest_snapshot{};
    std::memcpy(&manifest_snapshot, manifest, sizeof(manifest_snapshot));
    if (
        resolution_count > RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS
        || observation_count > RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS
        || output_capacity > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
        || manifest_snapshot.maximum_edge_records
            > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::uint64_t managed_limit = 0U;
    if (
        manifest_snapshot.struct_size != sizeof(manifest_snapshot)
        || manifest_snapshot.abi_version
            != RESONITH_PARTIAL_GRAPH_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        !edge_api_managed_limit(
            resolution_count,
            observation_count,
            manifest_snapshot.maximum_edge_records,
            &managed_limit
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    try {
        counting_memory_resource managed_memory(managed_limit);
        std::pmr::vector<resonith_partial_resolution> resolution_snapshot(
            &managed_memory
        );
        resolution_snapshot.assign(
            resolutions,
            resolutions + resolution_count
        );
        std::pmr::vector<resonith_partial_observation> observation_snapshot(
            &managed_memory
        );
        if (observation_count != 0U) {
            observation_snapshot.assign(
                observations,
                observations + observation_count
            );
        }
        const auto no_work_limit = [](
            resonith_partial_path_work_event,
            std::uint64_t
        ) {};
        deterministic_resolution_table resolution_table(
            &managed_memory,
            &no_work_limit
        );
        std::pmr::vector<std::uint64_t> observation_ids(&managed_memory);
        if (
            !valid_manifest(
                resolution_snapshot.data(),
                resolution_snapshot.size(),
                manifest_snapshot,
                &resolution_table,
                no_work_limit
            )
            || !valid_observations(
                observation_snapshot.data(),
                observation_snapshot.size(),
                manifest_snapshot.sample_rate,
                resolution_table,
                &observation_ids,
                no_work_limit
            )
        ) {
            return RESONITH_STATUS_INVALID_ARGUMENT;
        }

        std::size_t required = 0U;
        const resonith_status count_status = enumerate_edges_stream(
            observation_snapshot.data(),
            observation_snapshot.size(),
            manifest_snapshot,
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
        if (output == nullptr) {
            *output_count = required;
            return RESONITH_STATUS_OK;
        }
        if (output_capacity < required) {
            *output_count = required;
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }

        std::pmr::vector<resonith_partial_edge> staged(&managed_memory);
        staged.reserve(required);
        std::size_t verified_count = 0U;
        const resonith_status fill_status = enumerate_edges_stream(
            observation_snapshot.data(),
            observation_snapshot.size(),
            manifest_snapshot,
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
        *output_count = required;
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
    explicit path_output(std::pmr::memory_resource* memory)
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
    deterministic_resolution_table resolution_table(
        memory,
        &charge_work
    );
    std::pmr::vector<std::uint64_t> validated_observation_ids(memory);
    if (
        !valid_manifest(
            resolutions,
            resolution_count,
            graph_manifest,
            &resolution_table,
            charge_work
        )
        || !valid_observations(
            observations,
            observation_count,
            graph_manifest.sample_rate,
            resolution_table,
            &validated_observation_ids,
            charge_work
        )
    ) {
        return false;
    }
    const auto contains_observation = [&](std::uint64_t identifier) {
        std::size_t first = 0U;
        std::size_t last = validated_observation_ids.size();
        while (first < last) {
            const std::size_t middle = first + (last - first) / 2U;
            charge_work(RESONITH_PARTIAL_WORK_LOOKUP, 1U);
            const std::uint64_t value = validated_observation_ids[middle];
            if (value == identifier) {
                return true;
            }
            if (value < identifier) {
                first = middle + 1U;
            } else {
                last = middle;
            }
        }
        return false;
    };
    for (std::size_t index = 0U; index < edge_count; ++index) {
        charge_work(RESONITH_PARTIAL_WORK_VALIDATE_RECORD, 1U);
        const resonith_partial_edge& edge = edges[index];
        if (
            edge.struct_size != sizeof(edge)
            || edge.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || !reserved_zero(edge)
            || !contains_observation(edge.source_observation_id)
            || !contains_observation(edge.target_observation_id)
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
            if (compared >= edge_count) {
                return RESONITH_STATUS_INVALID_ARGUMENT;
            }
            const resonith_partial_edge& actual = edges[compared];
            bool equal = true;
            const auto compare_field = [&](auto left, auto right) {
                if (equal) {
                    charge_work(RESONITH_PARTIAL_WORK_EDGE_FIELD, 1U);
                    equal = left == right;
                }
            };
            compare_field(actual.struct_size, expected.struct_size);
            compare_field(actual.abi_version, expected.abi_version);
            compare_field(actual.candidate_id, expected.candidate_id);
            compare_field(
                actual.source_observation_id,
                expected.source_observation_id
            );
            compare_field(
                actual.target_observation_id,
                expected.target_observation_id
            );
            compare_field(
                actual.center_delta_samples,
                expected.center_delta_samples
            );
            compare_field(
                actual.frequency_delta_hz_q20,
                expected.frequency_delta_hz_q20
            );
            compare_field(actual.gap_hops, expected.gap_hops);
            compare_field(actual.cycle_offset, expected.cycle_offset);
            compare_field(actual.phase_error_u31, expected.phase_error_u31);
            compare_field(
                actual.continuity_cost_q8,
                expected.continuity_cost_q8
            );
            compare_field(
                actual.provisional_program_cost_q8,
                expected.provisional_program_cost_q8
            );
            compare_field(actual.flags, expected.flags);
            compare_field(actual.reserved[0], expected.reserved[0]);
            compare_field(actual.reserved[1], expected.reserved[1]);
            if (!equal) {
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

struct work_ledger_v1 {
    std::uint64_t maximum{};
    std::uint64_t total{};
    std::uint64_t reserved{};
    std::array<
        std::uint64_t,
        RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT
    > counts{};
    std::array<
        std::uint64_t,
        RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT
    > reserved_counts{};

    bool emit(
        resonith_partial_path_work_event event,
        std::uint64_t amount = 1U
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= counts.size()
            || amount != 1U
            || amount > maximum
            || reserved > maximum - amount
            || total > maximum - amount - reserved
            || counts[index] > std::numeric_limits<std::uint64_t>::max() - amount
        ) {
            return false;
        }
        counts[index] += amount;
        total += amount;
        return true;
    }

    bool reserve(
        resonith_partial_path_work_event event,
        std::uint64_t amount
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= reserved_counts.size()
            || amount > maximum
            || total > maximum - amount
            || reserved > maximum - amount - total
            || reserved_counts[index]
                > std::numeric_limits<std::uint64_t>::max() - amount
        ) {
            return false;
        }
        reserved += amount;
        reserved_counts[index] += amount;
        return true;
    }

    bool cancel_reserved(
        resonith_partial_path_work_event event,
        std::uint64_t amount
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= reserved_counts.size()
            || amount > reserved
            || amount > reserved_counts[index]
        ) {
            return false;
        }
        reserved -= amount;
        reserved_counts[index] -= amount;
        return true;
    }

    bool emit_reserved(
        resonith_partial_path_work_event event,
        std::uint64_t amount = 1U
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= counts.size()
            || amount > reserved
            || amount > reserved_counts[index]
            || counts[index] > std::numeric_limits<std::uint64_t>::max() - amount
        ) {
            return false;
        }
        reserved -= amount;
        reserved_counts[index] -= amount;
        counts[index] += amount;
        total += amount;
        return true;
    }
};

bool fingerprint_raw_v1(
    std::array<std::uint64_t, 4>* state,
    const std::uint8_t* bytes,
    std::size_t size,
    work_ledger_v1* ledger
) noexcept {
    constexpr std::array<std::uint64_t, 4> primes = {
        0x100000001b3ULL,
        0x100000001c9ULL,
        0x100000001e7ULL,
        0x10000000233ULL,
    };
    for (std::size_t byte = 0U; byte < size; ++byte) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE)) {
            return false;
        }
        for (std::size_t lane = 0U; lane < state->size(); ++lane) {
            (*state)[lane] ^= static_cast<std::uint64_t>(
                bytes[byte] + static_cast<std::uint8_t>(lane * 53U)
            );
            (*state)[lane] *= primes[lane];
        }
    }
    return true;
}

template <typename Integer>
bool fingerprint_integer_v1(
    std::array<std::uint64_t, 4>* state,
    Integer value,
    work_ledger_v1* ledger
) noexcept {
    static_assert(std::is_integral_v<Integer>);
    using unsigned_type = std::make_unsigned_t<Integer>;
    unsigned_type bits = static_cast<unsigned_type>(value);
    std::array<std::uint8_t, sizeof(Integer)> bytes{};
    for (std::size_t index = 0U; index < bytes.size(); ++index) {
        bytes[index] = static_cast<std::uint8_t>(bits & 0xffU);
        bits >>= 8U;
    }
    return fingerprint_raw_v1(state, bytes.data(), bytes.size(), ledger);
}

template <typename Value>
bool fingerprint_array_v1(
    std::array<std::uint64_t, 4>* state,
    const Value* values,
    std::size_t count,
    work_ledger_v1* ledger
) noexcept {
    for (std::size_t index = 0U; index < count; ++index) {
        if (!fingerprint_integer_v1(state, values[index], ledger)) {
            return false;
        }
    }
    return true;
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_graph_manifest& value,
    work_ledger_v1* ledger
) noexcept {
    bool ok = true;
    const auto put = [&](auto item) {
        if (ok) {
            ok = fingerprint_integer_v1(state, item, ledger);
        }
    };
    put(value.struct_size);
    put(value.abi_version);
    put(value.sample_rate);
    put(value.resolution_count);
    put(value.gap_count);
    put(value.neighbors_per_gap);
    put(value.cycle_offset_count);
    put(value.minimum_track_observations);
    put(value.maximum_frequency_jump_hz_q20);
    put(value.maximum_frequency_slope_hz_per_sample_q20);
    put(value.continuation_base_bits_q8);
    put(value.continuation_reward_q8);
    put(value.score_saturation);
    put(value.maximum_edge_records);
    put(value.maximum_path_hypotheses);
    put(value.exact_set_candidate_limit);
    ok = ok && fingerprint_array_v1(
        state,
        value.gaps,
        RESONITH_PARTIAL_GRAPH_MAX_GAPS,
        ledger
    );
    ok = ok && fingerprint_array_v1(
        state,
        value.cycle_offsets,
        RESONITH_PARTIAL_GRAPH_MAX_CYCLE_OFFSETS,
        ledger
    );
    return ok && fingerprint_array_v1(
        state,
        value.reserved,
        std::size(value.reserved),
        ledger
    );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_path_manifest_v3& value,
    work_ledger_v1* ledger
) noexcept {
    bool ok = true;
    const auto put = [&](auto item) {
        if (ok) {
            ok = fingerprint_integer_v1(state, item, ledger);
        }
    };
    put(value.struct_size);
    put(value.abi_version);
    put(value.second_order_law_version);
    put(value.protected_band_count);
    put(value.k_value_per_state);
    put(value.k_continuity_per_state);
    put(value.top_k_value);
    put(value.top_k_continuity);
    put(value.top_k_protected);
    put(value.protected_paths_per_band);
    put(value.minimum_path_observations);
    put(value.maximum_path_observations);
    put(value.exact_set_candidate_limit);
    put(value.amplitude_floor_q16);
    put(value.amplitude_residual_weight_q8);
    put(value.work_ledger_version);
    put(value.frequency_sigma_floor_hz_q20);
    put(value.birth_cost_bits_q8);
    put(value.death_cost_bits_q8);
    put(value.score_saturation);
    put(value.maximum_path_records);
    put(value.maximum_total_entries);
    put(value.maximum_frontier_states);
    put(value.maximum_state_records);
    put(value.maximum_work_units);
    put(value.maximum_managed_bytes);
    put(value.maximum_device_bytes);
    for (std::size_t index = 0U; index < 4U; ++index) {
        put(std::uint64_t{0});
    }
    ok = ok && fingerprint_array_v1(
        state,
        value.protected_band_upper_hz_q20,
        std::size(value.protected_band_upper_hz_q20),
        ledger
    );
    return ok && fingerprint_array_v1(
        state,
        value.reserved,
        std::size(value.reserved),
        ledger
    );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_resolution& value,
    work_ledger_v1* ledger
) noexcept {
    return fingerprint_integer_v1(state, value.struct_size, ledger)
        && fingerprint_integer_v1(state, value.abi_version, ledger)
        && fingerprint_integer_v1(state, value.resolution_id, ledger)
        && fingerprint_integer_v1(state, value.fft_samples, ledger)
        && fingerprint_integer_v1(state, value.hop_samples, ledger)
        && fingerprint_array_v1(
            state,
            value.reserved,
            std::size(value.reserved),
            ledger
        );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_observation& value,
    work_ledger_v1* ledger
) noexcept {
    bool ok = true;
    const auto put = [&](auto item) {
        if (ok) {
            ok = fingerprint_integer_v1(state, item, ledger);
        }
    };
    put(value.struct_size);
    put(value.abi_version);
    put(value.observation_id);
    put(value.center_sample);
    put(value.frequency_hz_q20);
    put(value.frequency_uncertainty_hz_q20);
    put(value.phase_turn_u32);
    put(value.phase_step_u32);
    put(value.normalized_amplitude_q16);
    put(value.amplitude_uncertainty_q16);
    put(value.phase_uncertainty_u31);
    put(value.frame_index);
    put(value.resolution_id);
    put(value.detector_id);
    put(value.band_id);
    put(value.ownership_component);
    put(value.ambiguity_component);
    put(value.flags);
    put(value.protected_rank_q8);
    put(value.neighbor_priority_q8);
    put(value.potential_node_value_q8);
    put(value.uncertainty_leakage_penalty_q8);
    return ok && fingerprint_array_v1(
        state,
        value.reserved,
        std::size(value.reserved),
        ledger
    );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_edge& value,
    work_ledger_v1* ledger
) noexcept {
    return fingerprint_integer_v1(state, value.struct_size, ledger)
        && fingerprint_integer_v1(state, value.abi_version, ledger)
        && fingerprint_integer_v1(state, value.candidate_id, ledger)
        && fingerprint_integer_v1(
            state,
            value.source_observation_id,
            ledger
        )
        && fingerprint_integer_v1(
            state,
            value.target_observation_id,
            ledger
        )
        && fingerprint_integer_v1(state, value.center_delta_samples, ledger)
        && fingerprint_integer_v1(state, value.frequency_delta_hz_q20, ledger)
        && fingerprint_integer_v1(state, value.gap_hops, ledger)
        && fingerprint_integer_v1(state, value.cycle_offset, ledger)
        && fingerprint_integer_v1(state, value.phase_error_u31, ledger)
        && fingerprint_integer_v1(state, value.continuity_cost_q8, ledger)
        && fingerprint_integer_v1(
            state,
            value.provisional_program_cost_q8,
            ledger
        )
        && fingerprint_integer_v1(state, value.flags, ledger)
        && fingerprint_array_v1(
            state,
            value.reserved,
            std::size(value.reserved),
            ledger
        );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_path_v3& value,
    work_ledger_v1* ledger
) noexcept {
    bool ok = true;
    const auto put = [&](auto item) {
        if (ok) {
            ok = fingerprint_integer_v1(state, item, ledger);
        }
    };
    put(value.struct_size);
    put(value.abi_version);
    put(value.path_id);
    put(value.entry_offset);
    put(value.entry_count);
    put(value.family_flags);
    put(value.terminal_observation_id);
    put(value.continuity_score_q8);
    put(value.potential_node_value_q8);
    put(value.uncertainty_leakage_penalty_q8);
    put(value.provisional_program_cost_q8);
    put(value.selection_score_q8);
    put(value.phase_error_sum_u64);
    put(value.phase_error_count);
    put(value.ownership_conflict_count);
    put(value.protected_band_id);
    put(value.value_rank);
    put(value.continuity_rank);
    put(value.protected_rank);
    put(value.flags);
    return ok && fingerprint_array_v1(
        state,
        value.reserved,
        std::size(value.reserved),
        ledger
    );
}

bool fingerprint_fields_v1(
    std::array<std::uint64_t, 4>* state,
    const resonith_partial_path_entry_v3& value,
    work_ledger_v1* ledger
) noexcept {
    return fingerprint_integer_v1(state, value.struct_size, ledger)
        && fingerprint_integer_v1(state, value.abi_version, ledger)
        && fingerprint_integer_v1(state, value.observation_id, ledger)
        && fingerprint_integer_v1(
            state,
            value.incoming_edge_candidate_id,
            ledger
        )
        && fingerprint_integer_v1(state, value.ownership_component, ledger)
        && fingerprint_integer_v1(state, value.second_order_cost_q8, ledger)
        && fingerprint_integer_v1(state, value.flags, ledger)
        && fingerprint_array_v1(
            state,
            value.reserved,
            std::size(value.reserved),
            ledger
        );
}

template <typename Vector, typename ByteKey>
bool stable_radix_pass_v1(
    Vector* values,
    Vector* scratch,
    ByteKey byte_key,
    work_ledger_v1* ledger
) {
    std::array<std::size_t, 256> counts{};
    for (std::size_t bucket = 0U; bucket < counts.size(); ++bucket) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_RADIX_BUCKET)) {
            return false;
        }
        counts[bucket] = 0U;
    }
    for (const auto& value : *values) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_RADIX_CLASSIFY)) {
            return false;
        }
        ++counts[byte_key(value)];
    }
    std::array<std::size_t, 256> offsets{};
    std::size_t prefix = 0U;
    for (std::size_t bucket = 0U; bucket < counts.size(); ++bucket) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_RADIX_BUCKET)) {
            return false;
        }
        offsets[bucket] = prefix;
        prefix += counts[bucket];
    }
    scratch->resize(values->size());
    for (const auto& value : *values) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_RADIX_SCATTER)) {
            return false;
        }
        const std::uint8_t bucket = byte_key(value);
        (*scratch)[offsets[bucket]++] = value;
    }
    values->swap(*scratch);
    return true;
}

template <typename Vector>
bool canonicalize_resolutions_v1(
    Vector* values,
    work_ledger_v1* ledger
) {
    Vector scratch(values->size(), values->get_allocator());
    for (std::uint32_t byte = 0U; byte < 4U; ++byte) {
        if (
            !stable_radix_pass_v1(
                values,
                &scratch,
                [byte](const resonith_partial_resolution& value) {
                    return static_cast<std::uint8_t>(
                        (value.resolution_id >> (byte * 8U)) & 0xffU
                    );
                },
                ledger
            )
        ) {
            return false;
        }
    }
    return true;
}

std::uint8_t observation_radix_byte_v1(
    const resonith_partial_observation& value,
    std::uint32_t pass
) noexcept {
    if (pass < 8U) {
        return static_cast<std::uint8_t>(
            (value.observation_id >> (pass * 8U)) & 0xffU
        );
    }
    if (pass < 16U) {
        const std::uint32_t byte = pass - 8U;
        const std::uint64_t bits =
            static_cast<std::uint64_t>(value.frequency_hz_q20);
        std::uint8_t result = static_cast<std::uint8_t>(
            (bits >> (byte * 8U)) & 0xffU
        );
        if (byte == 7U) {
            result ^= 0x80U;
        }
        return result;
    }
    if (pass < 20U) {
        const std::uint32_t byte = pass - 16U;
        const std::uint32_t bits =
            static_cast<std::uint32_t>(value.detector_id);
        std::uint8_t result = static_cast<std::uint8_t>(
            (bits >> (byte * 8U)) & 0xffU
        );
        if (byte == 3U) {
            result ^= 0x80U;
        }
        return result;
    }
    if (pass < 24U) {
        const std::uint32_t byte = pass - 20U;
        return static_cast<std::uint8_t>(
            (value.resolution_id >> (byte * 8U)) & 0xffU
        );
    }
    const std::uint32_t byte = pass - 24U;
    return static_cast<std::uint8_t>(
        (value.center_sample >> (byte * 8U)) & 0xffU
    );
}

template <typename Vector>
bool canonicalize_observations_v1(
    Vector* values,
    work_ledger_v1* ledger
) {
    Vector scratch(values->size(), values->get_allocator());
    for (std::uint32_t pass = 0U; pass < 32U; ++pass) {
        if (
            !stable_radix_pass_v1(
                values,
                &scratch,
                [pass](const resonith_partial_observation& value) {
                    return observation_radix_byte_v1(value, pass);
                },
                ledger
            )
        ) {
            return false;
        }
    }
    return true;
}

template <typename Record>
bool snapshot_object_v1(
    Record* destination,
    const Record* source,
    work_ledger_v1* ledger
) {
    auto* output = reinterpret_cast<std::uint8_t*>(destination);
    const auto* input = reinterpret_cast<const std::uint8_t*>(source);
    for (std::size_t byte = 0U; byte < sizeof(Record); ++byte) {
        if (!ledger->emit(RESONITH_PARTIAL_WORK_SNAPSHOT_BYTE)) {
            return false;
        }
        output[byte] = input[byte];
    }
    return true;
}

template <typename Record>
bool snapshot_records_v1(
    std::pmr::vector<Record>* destination,
    const Record* source,
    std::size_t count,
    work_ledger_v1* ledger
) {
    destination->reserve(count);
    for (std::size_t record = 0U; record < count; ++record) {
        destination->emplace_back();
        if (
            !snapshot_object_v1(
                &destination->back(),
                &source[record],
                ledger
            )
        ) {
            return false;
        }
    }
    return true;
}

bool snapshot_canonical_inputs_v3(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    work_ledger_v1* ledger,
    std::pmr::vector<resonith_partial_resolution>* canonical_resolutions,
    std::pmr::vector<resonith_partial_observation>* canonical_observations
) {
    return snapshot_records_v1(
               canonical_resolutions,
               resolutions,
               resolution_count,
               ledger
           )
        && snapshot_records_v1(
               canonical_observations,
               observations,
               observation_count,
               ledger
           )
        && canonicalize_resolutions_v1(canonical_resolutions, ledger)
        && canonicalize_observations_v1(canonical_observations, ledger);
}

bool input_fingerprint_v3(
    const std::pmr::vector<resonith_partial_resolution>& canonical_resolutions,
    const std::pmr::vector<resonith_partial_observation>& canonical_observations,
    const resonith_partial_edge* edges,
    std::size_t edge_count,
    const resonith_partial_graph_manifest& graph_manifest,
    const resonith_partial_path_manifest_v3& path_manifest,
    work_ledger_v1* ledger,
    std::pmr::memory_resource* memory,
    std::array<std::uint64_t, 4>* result
) {
    std::pmr::vector<resonith_partial_edge> canonical_edges(memory);
    if (
        !snapshot_records_v1(
            &canonical_edges,
            edges,
            edge_count,
            ledger
        )
    ) {
        return false;
    }
    const auto charge_merge = [ledger](
        resonith_partial_path_work_event event,
        std::uint64_t amount
    ) {
        if (!ledger->emit(event, amount)) {
            throw managed_profile_bound{};
        }
    };
    stable_merge_sort_v1(
        &canonical_edges,
        [](const resonith_partial_edge& left,
           const resonith_partial_edge& right) {
            return left.candidate_id < right.candidate_id;
        },
        charge_merge
    );

    auto state = fingerprint_begin();
    constexpr std::array<std::uint8_t, 8> domain = {
        0x52U, 0x50U, 0x47U, 0x46U, 0x01U, 0x00U, 0x00U, 0x00U,
    };
    bool ok = fingerprint_raw_v1(
        &state,
        domain.data(),
        domain.size(),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        path_manifest.work_ledger_version,
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(canonical_resolutions.size()),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(canonical_observations.size()),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(edge_count),
        ledger
    );
    ok = ok && fingerprint_fields_v1(&state, graph_manifest, ledger);
    ok = ok && fingerprint_fields_v1(&state, path_manifest, ledger);
    for (const auto& item : canonical_resolutions) {
        ok = ok && fingerprint_fields_v1(&state, item, ledger);
    }
    for (const auto& item : canonical_observations) {
        ok = ok && fingerprint_fields_v1(&state, item, ledger);
    }
    for (const auto& item : canonical_edges) {
        ok = ok && fingerprint_fields_v1(&state, item, ledger);
    }
    if (ok) {
        *result = state;
    }
    return ok;
}

template <typename PathVector, typename EntryVector>
bool output_fingerprint_v3(
    const PathVector& paths,
    const EntryVector& entries,
    work_ledger_v1* ledger,
    std::array<std::uint64_t, 4>* result
) noexcept {
    auto state = fingerprint_begin();
    constexpr std::array<std::uint8_t, 8> domain = {
        0x52U, 0x50U, 0x4fU, 0x46U, 0x01U, 0x00U, 0x00U, 0x00U,
    };
    bool ok = fingerprint_raw_v1(
        &state,
        domain.data(),
        domain.size(),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(paths.size()),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(entries.size()),
        ledger
    );
    for (const auto& path : paths) {
        ok = ok && fingerprint_fields_v1(&state, path, ledger);
    }
    for (const auto& entry : entries) {
        ok = ok && fingerprint_fields_v1(&state, entry, ledger);
    }
    if (ok) {
        *result = state;
    }
    return ok;
}

template <typename PathVector, typename EntryVector>
bool output_fingerprint_legacy_as_v3(
    const PathVector& paths,
    const EntryVector& entries,
    work_ledger_v1* ledger,
    std::array<std::uint64_t, 4>* result
) noexcept {
    auto state = fingerprint_begin();
    constexpr std::array<std::uint8_t, 8> domain = {
        0x52U, 0x50U, 0x4fU, 0x46U, 0x01U, 0x00U, 0x00U, 0x00U,
    };
    bool ok = fingerprint_raw_v1(
        &state,
        domain.data(),
        domain.size(),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(paths.size()),
        ledger
    );
    ok = ok && fingerprint_integer_v1(
        &state,
        static_cast<std::uint64_t>(entries.size()),
        ledger
    );
    for (const resonith_partial_path& legacy : paths) {
        resonith_partial_path_v3 converted{};
        static_assert(sizeof(converted) == sizeof(legacy));
        std::memcpy(&converted, &legacy, sizeof(converted));
        converted.struct_size = sizeof(converted);
        converted.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        ok = ok && fingerprint_fields_v1(&state, converted, ledger);
    }
    for (const resonith_partial_path_entry& legacy : entries) {
        resonith_partial_path_entry_v3 converted{};
        static_assert(sizeof(converted) == sizeof(legacy));
        std::memcpy(&converted, &legacy, sizeof(converted));
        converted.struct_size = sizeof(converted);
        converted.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        ok = ok && fingerprint_fields_v1(&state, converted, ledger);
    }
    if (ok) {
        *result = state;
    }
    return ok;
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
    stable_merge_sort_v1(
        &ordered_observations,
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
        },
        [](
            resonith_partial_path_work_event,
            std::uint64_t
        ) {}
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

class bounded_work_meter {
public:
    bounded_work_meter(
        const resonith_partial_path_manifest& manifest,
        resonith_partial_path_report* report,
        work_ledger_v1* ledger = nullptr
    ) noexcept
        : maximum_work_units_(manifest.maximum_work_units),
          report_(report),
          ledger_(ledger) {}

    void charge(
        std::uint64_t amount,
        resonith_partial_path_work_event event
    ) {
        if (amount != 1U) {
            throw std::logic_error("work events must be emitted one by one");
        }
        if (
            amount > maximum_work_units_
            || report_->work_units > maximum_work_units_ - amount
        ) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        report_->work_units += amount;
        if (ledger_ != nullptr && !ledger_->emit(event, amount)) {
            report_->work_units -= amount;
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
    }

    void reserve(
        std::uint64_t amount,
        resonith_partial_path_work_event event
    ) {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= reserved_counts_.size()
            || amount > maximum_work_units_
            || report_->work_units
                > maximum_work_units_ - amount
            || reserved_
                > maximum_work_units_
                    - amount
                    - report_->work_units
            || reserved_counts_[index]
                > std::numeric_limits<std::uint64_t>::max() - amount
            || ledger_ == nullptr
            || !ledger_->reserve(event, amount)
        ) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        reserved_ += amount;
        reserved_counts_[index] += amount;
    }

    [[nodiscard]] bool cancel_reserved(
        std::uint64_t amount,
        resonith_partial_path_work_event event
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= reserved_counts_.size()
            || amount > maximum_work_units_
            || amount > reserved_
            || amount > reserved_counts_[index]
            || ledger_ == nullptr
            || !ledger_->cancel_reserved(event, amount)
        ) {
            internal_failure_ = true;
            return false;
        }
        reserved_ -= amount;
        reserved_counts_[index] -= amount;
        return true;
    }

    [[nodiscard]] bool charge_reserved(
        std::uint64_t amount,
        resonith_partial_path_work_event event
    ) noexcept {
        const auto index = static_cast<std::size_t>(event);
        if (
            index >= reserved_counts_.size()
            || amount > reserved_
            || amount > reserved_counts_[index]
            || report_->work_units
                > maximum_work_units_ - amount
            || ledger_ == nullptr
            || !ledger_->emit_reserved(event, amount)
        ) {
            internal_failure_ = true;
            return false;
        }
        report_->work_units += amount;
        reserved_ -= amount;
        reserved_counts_[index] -= amount;
        return true;
    }

    [[nodiscard]] bool healthy() const noexcept {
        return !internal_failure_;
    }

private:
    std::uint64_t maximum_work_units_;
    resonith_partial_path_report* report_;
    work_ledger_v1* ledger_;
    std::uint64_t reserved_ = 0U;
    std::array<
        std::uint64_t,
        RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT
    > reserved_counts_{};
    bool internal_failure_ = false;
};

using bounded_state_index = std::uint32_t;
constexpr bounded_state_index bounded_state_free_sentinel =
    std::numeric_limits<bounded_state_index>::max();

struct bounded_state_handle {
    bounded_state_index index = bounded_state_free_sentinel;
    std::uint32_t generation = 0U;

    friend bool operator==(
        const bounded_state_handle&,
        const bounded_state_handle&
    ) = default;
};

constexpr bounded_state_handle bounded_state_sentinel{};

class bounded_node_reference;
struct bounded_state_arena_probe_access;

/*
 * One arena node stores only the newest observation and a checked parent
 * generation-tagged handle. Paths therefore grow in O(1) managed bytes per
 * hypothesis instead of copying every historical observation at every
 * extension. A recycled slot never validates a handle from its prior life.
 */
struct bounded_state_node {
    bounded_state_handle parent = bounded_state_sentinel;
    bounded_state_index next_free = bounded_state_free_sentinel;
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
    std::uint32_t generation = 0U;
    bool occupied = false;
};

class bounded_state_arena {
public:
    bounded_state_arena(
        std::pmr::memory_resource* memory,
        std::uint64_t maximum_records,
        resonith_partial_path_report* report,
        bounded_work_meter* work
    )
        : nodes_(memory),
          maximum_records_(maximum_records),
          report_(report),
          work_(work) {}

    bounded_state_arena(const bounded_state_arena&) = delete;
    bounded_state_arena& operator=(const bounded_state_arena&) = delete;

    [[nodiscard]] bounded_node_reference create_owned(
        const bounded_state_node& value
    );

    [[nodiscard]] bounded_node_reference retain_owned(
        bounded_state_handle handle
    );

    [[nodiscard]] const bounded_state_node& at(
        bounded_state_handle handle
    ) const {
        work_->charge(1U, RESONITH_PARTIAL_WORK_REFERENCE);
        return checked(handle);
    }

    [[nodiscard]] bool healthy() const noexcept {
        return !internal_failure_;
    }

    [[nodiscard]] bool empty() const noexcept {
        return live_count_ == 0U
            && outstanding_reference_reservations_ == 0U;
    }

private:
    friend class bounded_node_reference;
    friend struct bounded_state_arena_probe_access;

    [[nodiscard]] bounded_state_handle create_handle(
        const bounded_state_node& value
    ) {
        if (
            value.parent == bounded_state_sentinel
            && value.length != 2U
        ) {
            throw std::logic_error("bounded root rank mismatch");
        }
        if (
            live_count_ >= maximum_records_
            || live_count_
                >= static_cast<std::uint64_t>(bounded_state_free_sentinel)
        ) {
            ++report_->bound_rejected_count;
            throw managed_profile_bound{};
        }
        bounded_state_index index = bounded_state_free_sentinel;
        const bool reuse = free_head_ != bounded_state_free_sentinel;
        if (reuse) {
            index = free_head_;
        } else {
            if (
                nodes_.size()
                >= static_cast<std::size_t>(bounded_state_free_sentinel)
            ) {
                ++report_->bound_rejected_count;
                throw managed_profile_bound{};
            }
            nodes_.push_back(bounded_state_node{});
            index = static_cast<bounded_state_index>(nodes_.size() - 1U);
        }
        const std::uint32_t previous_generation = nodes_[index].generation;
        if (previous_generation == std::numeric_limits<std::uint32_t>::max()) {
            if (!reuse) {
                nodes_.pop_back();
            }
            throw std::logic_error("bounded state generation exhausted");
        }
        const std::uint32_t generation = previous_generation + 1U;
        bool owner_release_reserved = false;
        bool parent_acquired = false;
        try {
            work_->charge(1U, RESONITH_PARTIAL_WORK_REFERENCE);
            if (
                outstanding_reference_reservations_
                == std::numeric_limits<std::uint64_t>::max()
            ) {
                throw std::logic_error(
                    "bounded reference reservation exhausted"
                );
            }
            work_->reserve(1U, RESONITH_PARTIAL_WORK_REFERENCE);
            ++outstanding_reference_reservations_;
            owner_release_reserved = true;
            if (value.parent != bounded_state_sentinel) {
                add_child_reference(value.parent, value);
                parent_acquired = true;
            }
        } catch (...) {
            if (parent_acquired) {
                if (!release(value.parent)) {
                    internal_failure_ = true;
                }
            }
            if (owner_release_reserved) {
                if (
                    work_->cancel_reserved(
                        1U,
                        RESONITH_PARTIAL_WORK_REFERENCE
                    )
                ) {
                    --outstanding_reference_reservations_;
                } else {
                    internal_failure_ = true;
                }
            }
            if (!reuse) {
                nodes_.pop_back();
            }
            throw;
        }
        bounded_state_node node = value;
        node.reference_count = 1U;
        node.generation = generation;
        node.occupied = true;
        node.next_free = bounded_state_free_sentinel;
        if (reuse) {
            free_head_ = nodes_[index].next_free;
        }
        nodes_[index] = node;
        ++live_count_;
        report_->state_arena_peak = std::max(
            report_->state_arena_peak,
            live_count_
        );
        return bounded_state_handle{index, generation};
    }

    void add_reference(bounded_state_handle handle) {
        work_->charge(1U, RESONITH_PARTIAL_WORK_REFERENCE);
        bounded_state_node& node = checked(handle);
        if (node.reference_count == std::numeric_limits<std::uint32_t>::max()) {
            throw std::logic_error("bounded state reference count exhausted");
        }
        if (
            outstanding_reference_reservations_
            == std::numeric_limits<std::uint64_t>::max()
        ) {
            throw std::logic_error("bounded reference reservation exhausted");
        }
        work_->reserve(1U, RESONITH_PARTIAL_WORK_REFERENCE);
        ++outstanding_reference_reservations_;
        ++node.reference_count;
    }

    void add_child_reference(
        bounded_state_handle handle,
        const bounded_state_node& child
    ) {
        work_->charge(1U, RESONITH_PARTIAL_WORK_REFERENCE);
        bounded_state_node& parent = checked(handle);
        if (
            parent.length == std::numeric_limits<std::uint32_t>::max()
            || child.length != parent.length + 1U
            || child.first_observation_id != parent.first_observation_id
            || child.previous_observation_id
                != parent.current_observation_id
        ) {
            throw std::logic_error("bounded parent rank or linkage mismatch");
        }
        if (parent.reference_count == std::numeric_limits<std::uint32_t>::max()) {
            throw std::logic_error("bounded state reference count exhausted");
        }
        if (
            outstanding_reference_reservations_
            == std::numeric_limits<std::uint64_t>::max()
        ) {
            throw std::logic_error("bounded reference reservation exhausted");
        }
        work_->reserve(1U, RESONITH_PARTIAL_WORK_REFERENCE);
        ++outstanding_reference_reservations_;
        ++parent.reference_count;
    }

    [[nodiscard]] bool release(bounded_state_handle handle) noexcept {
        while (handle != bounded_state_sentinel) {
            if (
                outstanding_reference_reservations_ == 0U
                || !work_->charge_reserved(
                    1U,
                    RESONITH_PARTIAL_WORK_REFERENCE
                )
                || handle.index >= nodes_.size()
            ) {
                internal_failure_ = true;
                return false;
            }
            --outstanding_reference_reservations_;
            bounded_state_node& node = nodes_[handle.index];
            if (
                !node.occupied
                || node.generation != handle.generation
                || node.reference_count == 0U
            ) {
                internal_failure_ = true;
                return false;
            }
            --node.reference_count;
            if (node.reference_count != 0U) {
                return true;
            }
            const bounded_state_handle parent = node.parent;
            const std::uint32_t generation = node.generation;
            node = bounded_state_node{};
            node.generation = generation;
            node.next_free = free_head_;
            free_head_ = handle.index;
            --live_count_;
            handle = parent;
        }
        return true;
    }
    [[nodiscard]] bounded_state_node& checked(bounded_state_handle handle) {
        if (
            handle == bounded_state_sentinel
            || handle.index >= nodes_.size()
            || !nodes_[handle.index].occupied
            || nodes_[handle.index].generation != handle.generation
        ) {
            throw std::logic_error("stale bounded state handle");
        }
        return nodes_[handle.index];
    }

    [[nodiscard]] const bounded_state_node& checked(
        bounded_state_handle handle
    ) const {
        if (
            handle == bounded_state_sentinel
            || handle.index >= nodes_.size()
            || !nodes_[handle.index].occupied
            || nodes_[handle.index].generation != handle.generation
        ) {
            throw std::logic_error("stale bounded state handle");
        }
        return nodes_[handle.index];
    }

    std::pmr::vector<bounded_state_node> nodes_;
    std::uint64_t maximum_records_;
    resonith_partial_path_report* report_;
    bounded_work_meter* work_;
    bounded_state_index free_head_ = bounded_state_free_sentinel;
    std::uint64_t live_count_ = 0U;
    std::uint64_t outstanding_reference_reservations_ = 0U;
    bool internal_failure_ = false;
};

class bounded_node_reference {
public:
    bounded_node_reference() noexcept = default;

    bounded_node_reference(const bounded_node_reference&) = delete;
    bounded_node_reference& operator=(const bounded_node_reference&) = delete;

    bounded_node_reference(bounded_node_reference&& other) noexcept
        : arena_(std::exchange(other.arena_, nullptr)),
          handle_(std::exchange(other.handle_, bounded_state_sentinel)) {}

    bounded_node_reference& operator=(
        bounded_node_reference&& other
    ) noexcept {
        if (this != &other) {
            reset();
            arena_ = std::exchange(other.arena_, nullptr);
            handle_ = std::exchange(other.handle_, bounded_state_sentinel);
        }
        return *this;
    }

    ~bounded_node_reference() {
        reset();
    }

    [[nodiscard]] bounded_state_handle get() const noexcept {
        return handle_;
    }

    void reset() noexcept {
        if (arena_ != nullptr) {
            static_cast<void>(arena_->release(handle_));
            arena_ = nullptr;
            handle_ = bounded_state_sentinel;
        }
    }

private:
    friend class bounded_state_arena;

    bounded_node_reference(
        bounded_state_arena* arena,
        bounded_state_handle handle
    ) noexcept
        : arena_(arena), handle_(handle) {}

    bounded_state_arena* arena_ = nullptr;
    bounded_state_handle handle_ = bounded_state_sentinel;
};

bounded_node_reference bounded_state_arena::create_owned(
    const bounded_state_node& value
) {
    return bounded_node_reference(this, create_handle(value));
}

bounded_node_reference bounded_state_arena::retain_owned(
    bounded_state_handle handle
) {
    add_reference(handle);
    return bounded_node_reference(this, handle);
}

struct bounded_state_arena_probe_access {
    static bool release(
        bounded_state_arena* arena,
        bounded_state_handle handle
    ) noexcept {
        return arena->release(handle);
    }

    static std::uint32_t reference_count(
        const bounded_state_arena& arena,
        bounded_state_handle handle
    ) {
        return arena.checked(handle).reference_count;
    }

    static bool set_reference_count(
        bounded_state_arena* arena,
        bounded_state_handle handle,
        std::uint32_t value
    ) {
        bounded_state_node& node = arena->checked(handle);
        node.reference_count = value;
        return true;
    }

    static bool set_free_generation(
        bounded_state_arena* arena,
        bounded_state_index index,
        std::uint32_t generation
    ) noexcept {
        if (
            index >= arena->nodes_.size()
            || arena->nodes_[index].occupied
        ) {
            return false;
        }
        arena->nodes_[index].generation = generation;
        return true;
    }

    static bounded_state_index free_head(
        const bounded_state_arena& arena
    ) noexcept {
        return arena.free_head_;
    }

    static std::uint64_t outstanding_references(
        const bounded_state_arena& arena
    ) noexcept {
        return arena.outstanding_reference_reservations_;
    }

    static bool audit(const bounded_state_arena& arena) noexcept {
        std::uint64_t occupied_count = 0U;
        std::uint64_t reference_sum = 0U;
        for (const bounded_state_node& node : arena.nodes_) {
            if (node.occupied) {
                if (
                    node.generation == 0U
                    || node.reference_count == 0U
                    || node.next_free != bounded_state_free_sentinel
                    || reference_sum
                        > std::numeric_limits<std::uint64_t>::max()
                            - node.reference_count
                ) {
                    return false;
                }
                ++occupied_count;
                reference_sum += node.reference_count;
                if (node.parent == bounded_state_sentinel) {
                    if (node.length != 2U) {
                        return false;
                    }
                } else {
                    if (
                        node.parent.index >= arena.nodes_.size()
                        || !arena.nodes_[node.parent.index].occupied
                        || arena.nodes_[node.parent.index].generation
                            != node.parent.generation
                    ) {
                        return false;
                    }
                    const bounded_state_node& parent =
                        arena.nodes_[node.parent.index];
                    if (
                        parent.length
                            == std::numeric_limits<std::uint32_t>::max()
                        || node.length != parent.length + 1U
                        || node.first_observation_id
                            != parent.first_observation_id
                        || node.previous_observation_id
                            != parent.current_observation_id
                    ) {
                        return false;
                    }
                }
            } else if (node.reference_count != 0U) {
                return false;
            }
        }
        if (
            occupied_count != arena.live_count_
            || reference_sum
                != arena.outstanding_reference_reservations_
        ) {
            return false;
        }

        std::uint64_t free_count = 0U;
        bounded_state_index cursor = arena.free_head_;
        while (cursor != bounded_state_free_sentinel) {
            if (
                cursor >= arena.nodes_.size()
                || arena.nodes_[cursor].occupied
                || free_count >= arena.nodes_.size()
            ) {
                return false;
            }
            ++free_count;
            cursor = arena.nodes_[cursor].next_free;
        }
        return free_count
            == static_cast<std::uint64_t>(arena.nodes_.size())
                - arena.live_count_;
    }
};

void account_host_page_prepare(void* context, std::uint64_t pages) {
    auto* work = static_cast<bounded_work_meter*>(context);
    if (
        pages
        > std::numeric_limits<std::uint64_t>::max() / 2U
    ) {
        throw managed_profile_bound{};
    }
    const std::uint64_t cleanup_events = pages * 2U;
    work->reserve(cleanup_events, RESONITH_PARTIAL_WORK_MEMORY_PAGE);
    try {
        for (std::uint64_t page = 0U; page < pages; ++page) {
            work->charge(1U, RESONITH_PARTIAL_WORK_MEMORY_PAGE);
        }
    } catch (...) {
        if (!work->cancel_reserved(
                cleanup_events,
                RESONITH_PARTIAL_WORK_MEMORY_PAGE
            )) {
            throw memory_provenance_failure{};
        }
        throw;
    }
}

bool account_host_page_commit(
    void* context,
    std::uint64_t pages
) noexcept {
    auto* work = static_cast<bounded_work_meter*>(context);
    return work->charge_reserved(
        pages,
        RESONITH_PARTIAL_WORK_MEMORY_PAGE
    );
}

bool account_host_page_cancel(
    void* context,
    std::uint64_t pages
) noexcept {
    auto* work = static_cast<bounded_work_meter*>(context);
    const bool charged = work->charge_reserved(
        pages,
        RESONITH_PARTIAL_WORK_MEMORY_PAGE
    );
    const std::uint64_t cancellation =
        charged || pages > std::numeric_limits<std::uint64_t>::max() / 2U
            ? pages
            : pages * 2U;
    const bool cancelled = work->cancel_reserved(
        cancellation,
        RESONITH_PARTIAL_WORK_MEMORY_PAGE
    );
    return charged && cancelled;
}

bool account_host_page_release(
    void* context,
    std::uint64_t pages
) noexcept {
    auto* work = static_cast<bounded_work_meter*>(context);
    return work->charge_reserved(
        pages,
        RESONITH_PARTIAL_WORK_MEMORY_PAGE
    );
}

template <typename Key, typename Value, typename Less = std::less<Key>>
class deterministic_flat_map {
public:
    struct record {
        record(const Key& key, std::pmr::memory_resource* memory)
            : first(key), second(make_value(memory)) {}

        Key first;
        Value second;

    private:
        static Value make_value(std::pmr::memory_resource* memory) {
            if constexpr (
                std::is_constructible_v<Value, std::pmr::memory_resource*>
            ) {
                return Value(memory);
            } else {
                static_cast<void>(memory);
                return Value{};
            }
        }
    };

    explicit deterministic_flat_map(std::pmr::memory_resource* memory)
        : values_(memory), memory_(memory) {}

    std::pair<record*, bool> try_emplace(
        const Key& key,
        bounded_work_meter* work
    ) {
        const auto [position, found] = locate(key, work);
        if (found) {
            return {&values_[position], false};
        }
        auto inserted = values_.emplace(
            values_.begin() + static_cast<std::ptrdiff_t>(position),
            key,
            memory_
        );
        return {&*inserted, true};
    }

    record* find(const Key& key, bounded_work_meter* work) {
        const auto [position, found] = locate(key, work);
        return found ? &values_[position] : nullptr;
    }

    const record* find(const Key& key, bounded_work_meter* work) const {
        const auto [position, found] = locate(key, work);
        return found ? &values_[position] : nullptr;
    }

    record& at(const Key& key, bounded_work_meter* work) {
        record* item = find(key, work);
        if (item == nullptr) {
            throw std::logic_error("missing deterministic table key");
        }
        return *item;
    }

    const record& at(const Key& key, bounded_work_meter* work) const {
        const record* item = find(key, work);
        if (item == nullptr) {
            throw std::logic_error("missing deterministic table key");
        }
        return *item;
    }

    void erase(record* item) {
        const auto position = static_cast<std::size_t>(item - values_.data());
        values_.erase(
            values_.begin() + static_cast<std::ptrdiff_t>(position)
        );
    }

    void clear() noexcept {
        values_.clear();
    }

    auto begin() noexcept {
        return values_.begin();
    }

    auto end() noexcept {
        return values_.end();
    }

    auto begin() const noexcept {
        return values_.begin();
    }

    auto end() const noexcept {
        return values_.end();
    }

private:
    std::pair<std::size_t, bool> locate(
        const Key& key,
        bounded_work_meter* work
    ) const {
        std::size_t first = 0U;
        std::size_t last = values_.size();
        while (first < last) {
            const std::size_t middle = first + (last - first) / 2U;
            work->charge(1U, RESONITH_PARTIAL_WORK_LOOKUP);
            if (less_(values_[middle].first, key)) {
                first = middle + 1U;
            } else {
                last = middle;
            }
        }
        if (first == values_.size()) {
            return {first, false};
        }
        work->charge(1U, RESONITH_PARTIAL_WORK_LOOKUP);
        const bool equal = !less_(key, values_[first].first)
            && !less_(values_[first].first, key);
        return {first, equal};
    }

    std::pmr::vector<record> values_;
    std::pmr::memory_resource* memory_;
    Less less_{};
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
    bounded_state_handle handle,
    std::pmr::memory_resource* memory,
    bounded_work_meter* work
) {
    const bounded_state_node& leaf = arena.at(handle);
    bounded_identity result(memory);
    result.observations.resize(leaf.length);
    result.incoming_edges.resize(leaf.length);
    bounded_state_handle cursor = handle;
    std::size_t position = leaf.length;
    while (cursor != bounded_state_sentinel) {
        work->charge(1U, RESONITH_PARTIAL_WORK_RECONSTRUCT);
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
    work->charge(1U, RESONITH_PARTIAL_WORK_STATE);
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
    work->charge(1U, RESONITH_PARTIAL_WORK_SELECT);
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
    work->charge(1U, RESONITH_PARTIAL_WORK_SELECT);
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
        const bounded_state_handle handle = node.get();
        const bounded_state_node& state = arena->at(handle);
        materialized.emplace_back(
            std::move(node),
            materialize_identity(*arena, handle, memory, work),
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
    stable_merge_sort_v1(
        &result,
        [&](const bounded_node_reference& left, const bounded_node_reference& right) {
            const bounded_state_node& left_state = arena->at(left.get());
            const bounded_state_node& right_state = arena->at(right.get());
            const std::int64_t left_score = bounded_value_score(
                left_state,
                graph_manifest,
                path_manifest
            );
            const std::int64_t right_score = bounded_value_score(
                right_state,
                graph_manifest,
                path_manifest
            );
            if (left_score != right_score) {
                return left_score > right_score;
            }
            bounded_identity left_identity = materialize_identity(
                *arena,
                left.get(),
                memory,
                work
            );
            bounded_identity right_identity = materialize_identity(
                *arena,
                right.get(),
                memory,
                work
            );
            if (left_identity.observations != right_identity.observations) {
                return left_identity.observations < right_identity.observations;
            }
            return left_identity.incoming_edges < right_identity.incoming_edges;
        },
        [work](resonith_partial_path_work_event event, std::uint64_t amount) {
            work->charge(amount, event);
        }
    );
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
    work->charge(1U, RESONITH_PARTIAL_WORK_SELECT);
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

template <typename ObservationTable>
std::uint32_t bounded_frequency_band(
    const bounded_identity& identity,
    const ObservationTable& observations,
    const resonith_partial_path_manifest& manifest,
    std::pmr::memory_resource* memory,
    bounded_work_meter* work
) {
    std::pmr::vector<std::int64_t> frequencies(memory);
    frequencies.reserve(identity.observations.size());
    for (const std::uint64_t identifier : identity.observations) {
        frequencies.push_back(
            observations.at(identifier, work).second->frequency_hz_q20
        );
    }
    stable_merge_sort_v1(
        &frequencies,
        [](std::int64_t left, std::int64_t right) {
            return left < right;
        },
        [work](resonith_partial_path_work_event event, std::uint64_t amount) {
            work->charge(amount, event);
        }
    );
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
        bounded_state_handle node_value,
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

    bounded_state_handle node;
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
    std::pmr::memory_resource* memory,
    work_ledger_v1* ledger
) {
    bounded_work_meter work(path_manifest, report, ledger);
    bounded_state_arena arena(
        memory,
        path_manifest.maximum_state_records,
        report,
        &work
    );
    using observation_table = deterministic_flat_map<
        std::uint64_t,
        const resonith_partial_observation*
    >;
    observation_table observations(memory);
    std::pmr::vector<const resonith_partial_observation*> ordered_observations(
        memory
    );
    ordered_observations.reserve(observation_count);
    for (std::size_t index = 0U; index < observation_count; ++index) {
        auto [row, inserted] = observations.try_emplace(
            observation_data[index].observation_id,
            &work
        );
        if (!inserted) {
            throw std::logic_error("duplicate observation index");
        }
        row->second = &observation_data[index];
        ordered_observations.push_back(&observation_data[index]);
    }
    stable_merge_sort_v1(
        &ordered_observations,
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
        },
        [&work](
            resonith_partial_path_work_event event,
            std::uint64_t amount
        ) {
            work.charge(amount, event);
        }
    );

    using edge_rows = std::pmr::vector<const resonith_partial_edge*>;
    deterministic_flat_map<std::uint64_t, edge_rows> incoming(memory);
    deterministic_flat_map<std::uint64_t, std::uint64_t> outgoing_remaining(
        memory
    );
    for (std::size_t index = 0U; index < edge_count; ++index) {
        const resonith_partial_edge* edge = &edge_data[index];
        auto [incoming_row, inserted] = incoming.try_emplace(
            edge->target_observation_id,
            &work
        );
        static_cast<void>(inserted);
        incoming_row->second.push_back(edge);
        auto [remaining, remaining_inserted] =
            outgoing_remaining.try_emplace(
                edge->source_observation_id,
                &work
            );
        static_cast<void>(remaining_inserted);
        ++remaining->second;
    }

    using terminal_key = std::pair<std::uint64_t, std::uint64_t>;
    using state_rows = std::pmr::vector<bounded_node_reference>;
    deterministic_flat_map<terminal_key, state_rows> states(memory);
    deterministic_flat_map<std::uint64_t, std::pmr::vector<terminal_key>>
        terminal_keys_by_current(memory);
    std::uint64_t frontier_size = 0U;

    std::pmr::vector<bounded_family_entry> value_reservoir(memory);
    std::pmr::vector<bounded_family_entry> continuity_reservoir(memory);
    deterministic_flat_map<
        std::uint32_t,
        std::pmr::vector<bounded_family_entry>
    > protected_by_band(memory);

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
        work.charge(1U, RESONITH_PARTIAL_WORK_STATE);
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
        return arena.create_owned(node);
    };

    auto create_extension = [&](
        bounded_state_handle prior_handle,
        const resonith_partial_observation& previous,
        const resonith_partial_observation& source,
        const resonith_partial_observation& target,
        const resonith_partial_edge& edge
    ) {
        work.charge(1U, RESONITH_PARTIAL_WORK_STATE);
        if (report->raw_state_count == std::numeric_limits<std::uint64_t>::max()) {
            ++report->bound_rejected_count;
            throw managed_profile_bound{};
        }
        ++report->raw_state_count;
        const bounded_state_node& prior = arena.at(prior_handle);
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
        node.parent = prior_handle;
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
        return arena.create_owned(node);
    };

    auto present_families = [&](bounded_state_handle handle) {
        const bounded_state_node& node = arena.at(handle);
        if (node.length < path_manifest.minimum_path_observations) {
            return;
        }
        bounded_identity identity = materialize_identity(
            arena,
            handle,
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
                arena.retain_owned(handle),
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
                arena.retain_owned(handle),
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
                band,
                &work
            );
            static_cast<void>(inserted);
            insert_family_reservoir(
                &band_row->second,
                bounded_family_entry(
                    arena.retain_owned(handle),
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
        const auto incoming_row = incoming.find(
            target->observation_id,
            &work
        );
        if (incoming_row == nullptr) {
            continue;
        }
        deterministic_flat_map<terminal_key, state_rows> pending(memory);
        for (const resonith_partial_edge* edge : incoming_row->second) {
            const resonith_partial_observation* source =
                observations.at(edge->source_observation_id, &work).second;
            const terminal_key destination_key{
                source->observation_id,
                target->observation_id,
            };
            auto [destination, inserted] = pending.try_emplace(
                destination_key,
                &work
            );
            static_cast<void>(inserted);
            destination->second.push_back(
                create_birth(*source, *target, *edge)
            );

            const auto terminal_rows = terminal_keys_by_current.find(
                source->observation_id,
                &work
            );
            if (terminal_rows != nullptr) {
                for (const terminal_key& prior_key : terminal_rows->second) {
                    const state_rows& prior_states =
                        states.at(prior_key, &work).second;
                    const resonith_partial_observation* previous =
                        observations.at(prior_key.first, &work).second;
                    for (const bounded_node_reference& prior : prior_states) {
                        work.charge(1U, RESONITH_PARTIAL_WORK_STATE);
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

            auto remaining = outgoing_remaining.find(
                source->observation_id,
                &work
            );
            if (
                remaining == nullptr
                || remaining->second == 0U
            ) {
                throw std::logic_error("outgoing edge accounting mismatch");
            }
            --remaining->second;
            if (remaining->second == 0U) {
                const auto stale = terminal_keys_by_current.find(
                    source->observation_id,
                    &work
                );
                if (stale != nullptr) {
                    for (const terminal_key& key : stale->second) {
                        const auto row = states.find(key, &work);
                        if (row != nullptr) {
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
            const auto target_outgoing = outgoing_remaining.find(
                key.second,
                &work
            );
            if (
                target_outgoing == nullptr
                || target_outgoing->second == 0U
            ) {
                continue;
            }
            frontier_size += retained.size();
            auto [row, inserted] = states.try_emplace(key, &work);
            if (!inserted) {
                throw std::logic_error("duplicate terminal bucket");
            }
            row->second = std::move(retained);
            auto [index_row, index_inserted] =
                terminal_keys_by_current.try_emplace(key.second, &work);
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
    stable_merge_sort_v1(
        &union_paths,
        [](const bounded_output_candidate& left,
           const bounded_output_candidate& right) {
            if (left.value_score != right.value_score) {
                return left.value_score > right.value_score;
            }
            if (left.continuity_score != right.continuity_score) {
                return left.continuity_score > right.continuity_score;
            }
            if (left.identity.observations != right.identity.observations) {
                return left.identity.observations
                    < right.identity.observations;
            }
            return left.identity.incoming_edges < right.identity.incoming_edges;
        },
        [&work](
            resonith_partial_path_work_event event,
            std::uint64_t amount
        ) {
            work.charge(amount, event);
        }
    );

    for (bounded_output_candidate& candidate : union_paths) {
        candidate.ownership_components.reserve(
            candidate.identity.observations.size()
        );
        for (const std::uint64_t identifier : candidate.identity.observations) {
            work.charge(1U, RESONITH_PARTIAL_WORK_LOOKUP);
            candidate.ownership_components.push_back(
                observations.at(identifier, &work).second->ownership_component
            );
        }
        stable_merge_sort_v1(
            &candidate.ownership_components,
            [](std::uint32_t left, std::uint32_t right) {
                return left < right;
            },
            [&work](
                resonith_partial_path_work_event event,
                std::uint64_t amount
            ) {
                work.charge(amount, event);
            }
        );
        std::size_t unique_count = 0U;
        for (
            std::size_t read = 0U;
            read < candidate.ownership_components.size();
            ++read
        ) {
            bool duplicate = false;
            if (unique_count != 0U) {
                work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
                duplicate =
                    candidate.ownership_components[unique_count - 1U]
                    == candidate.ownership_components[read];
            }
            if (!duplicate) {
                candidate.ownership_components[unique_count] =
                    candidate.ownership_components[read];
                ++unique_count;
            }
        }
        candidate.internal_conflicts = static_cast<std::uint32_t>(
            candidate.ownership_components.size() - unique_count
        );
        candidate.ownership_components.resize(unique_count);
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
    for (std::size_t index = 0U; index < union_paths.size(); ++index) {
        work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
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
    static_cast<void>(pair_count);
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
            std::size_t first_index = 0U;
            std::size_t second_index = 0U;
            bool conflict = false;
            while (
                first_index < first.size()
                && second_index < second.size()
            ) {
                work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
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
    const auto selection_position = [&](std::size_t value) {
        for (
            std::size_t index = 0U;
            index < selection_candidates.size();
            ++index
        ) {
            work.charge(1U, RESONITH_PARTIAL_WORK_LOOKUP);
            if (selection_candidates[index] == value) {
                return index;
            }
        }
        throw std::logic_error("missing selection candidate");
    };
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
            work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
            current.clear();
            wide_positive_score score{};
            bool valid = true;
            for (
                std::size_t candidate = 0U;
                candidate < selection_candidates.size();
                ++candidate
            ) {
                work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
                if ((mask & (1ULL << candidate)) == 0U) {
                    continue;
                }
                for (const std::size_t incumbent : current) {
                    work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
                    const std::size_t incumbent_position =
                        selection_position(incumbent);
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
            const std::size_t candidate_position =
                selection_position(candidate);
            for (const std::size_t incumbent : accepted) {
                work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
                const std::size_t incumbent_position =
                    selection_position(incumbent);
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
    report->selected_path_count = 0U;
    for (const std::uint8_t value : selected) {
        work.charge(1U, RESONITH_PARTIAL_WORK_SELECT);
        report->selected_path_count += value == 1U ? 1U : 0U;
    }

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
        std::pmr::vector<std::int32_t> second_order(
            candidate.identity.observations.size(),
            0,
            memory
        );
        bounded_state_handle cursor = candidate.node;
        std::size_t position = second_order.size();
        while (cursor != bounded_state_sentinel) {
            work.charge(1U, RESONITH_PARTIAL_WORK_RECONSTRUCT);
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
        work.charge(1U, RESONITH_PARTIAL_WORK_STAGE_RECORD);
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
            work.charge(1U, RESONITH_PARTIAL_WORK_STAGE_RECORD);
            output->entries.push_back(resonith_partial_path_entry{
                sizeof(resonith_partial_path_entry),
                RESONITH_PARTIAL_PATH_ABI_VERSION,
                observation_id,
                candidate.identity.incoming_edges[entry],
                observations.at(observation_id, &work)
                    .second->ownership_component,
                second_order[entry],
                0U,
                {0U, 0U, 0U},
            });
        }
        entry_offset += candidate.identity.observations.size();
    }

    report->required_path_count = output->paths.size();
    report->required_entry_count = output->entries.size();
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
    union_paths.clear();
    value_reservoir.clear();
    continuity_reservoir.clear();
    protected_reservoir.clear();
    if (!arena.empty() || !arena.healthy() || !work.healthy()) {
        throw std::logic_error("bounded reference ledger invariant failed");
    }
    return RESONITH_STATUS_OK;
}

}  // namespace

namespace resonith::internal {

void partial_graph_set_test_allocation_permit_callback(
    void (*callback)(bool) noexcept
) noexcept {
    test_allocation_permit_callback = callback;
}

void partial_graph_set_test_upstream_resource(
    std::pmr::memory_resource* resource
) noexcept {
    test_upstream_resource = resource;
}

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

bool partial_graph_memory_provenance_probe() noexcept {
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
        counting_memory_resource counted(1024U);
        {
            std::pmr::vector<std::uint8_t> values(&counted);
            values.reserve(128U);
            if (
                counted.reserved_bytes() != 128U
                || counted.committed_bytes() != 128U
                || counted.peak_bytes() != 128U
                || counted.current_reserved_bytes() != 128U
                || counted.current_committed_bytes() != 128U
                || counted.current_live_bytes() != 128U
                || !counted.healthy()
            ) {
                return false;
            }
        }
        if (
            counted.current_reserved_bytes() != 0U
            || counted.current_committed_bytes() != 0U
            || counted.current_live_bytes() != 0U
            || !counted.healthy()
        ) {
            return false;
        }

        counting_memory_resource bounded(127U);
        bool profile_rejected = false;
        try {
            static_cast<void>(bounded.allocate(128U));
        } catch (const managed_profile_bound&) {
            profile_rejected = true;
        }
        if (
            !profile_rejected
            || bounded.reserved_bytes() != 0U
            || bounded.committed_bytes() != 0U
            || bounded.peak_bytes() != 0U
            || !bounded.healthy()
        ) {
            return false;
        }

        counting_memory_resource environmental(1024U, &failing);
        bool oom_rejected = false;
        try {
            static_cast<void>(environmental.allocate(128U));
        } catch (const environmental_out_of_memory&) {
            oom_rejected = true;
        }
        if (
            !oom_rejected
            || environmental.reserved_bytes() != 128U
            || environmental.committed_bytes() != 0U
            || environmental.peak_bytes() != 0U
            || environmental.current_reserved_bytes() != 0U
            || environmental.current_committed_bytes() != 0U
            || environmental.current_live_bytes() != 0U
            || !environmental.healthy()
        ) {
            return false;
        }

        struct callback_trace {
            std::uint64_t prepared = 0U;
            std::uint64_t committed = 0U;
            std::uint64_t cancelled = 0U;
            std::uint64_t released = 0U;
        } trace;
        const auto prepare = [](void* context, std::uint64_t pages) {
            static_cast<callback_trace*>(context)->prepared += pages;
        };
        const auto commit = [](void* context, std::uint64_t pages) noexcept {
            static_cast<callback_trace*>(context)->committed += pages;
            return true;
        };
        const auto cancel = [](void* context, std::uint64_t pages) noexcept {
            static_cast<callback_trace*>(context)->cancelled += pages;
            return true;
        };
        const auto release = [](void* context, std::uint64_t pages) noexcept {
            static_cast<callback_trace*>(context)->released += pages;
            return true;
        };
        counting_memory_resource traced(
            8192U,
            nullptr,
            &trace,
            prepare,
            commit,
            cancel,
            release
        );
        void* pointer = traced.allocate(5000U);
        traced.deallocate(pointer, 5000U);
        if (
            trace.prepared != 2U
            || trace.committed != 2U
            || trace.cancelled != 0U
            || trace.released != 2U
            || traced.reserved_bytes() != 5000U
            || traced.committed_bytes() != 5000U
            || traced.peak_bytes() != 5000U
            || traced.current_reserved_bytes() != 0U
            || traced.current_committed_bytes() != 0U
            || traced.current_live_bytes() != 0U
            || !traced.healthy()
        ) {
            return false;
        }

        const auto reject_commit = [](
            void*,
            std::uint64_t
        ) noexcept {
            return false;
        };
        counting_memory_resource broken(
            1024U,
            nullptr,
            nullptr,
            nullptr,
            reject_commit
        );
        bool provenance_rejected = false;
        try {
            static_cast<void>(broken.allocate(64U));
        } catch (const memory_provenance_failure&) {
            provenance_rejected = true;
        }
        if (
            !provenance_rejected
            || broken.reserved_bytes() != 64U
            || broken.committed_bytes() != 0U
            || broken.peak_bytes() != 0U
            || broken.current_reserved_bytes() != 0U
            || broken.current_committed_bytes() != 0U
            || broken.current_live_bytes() != 0U
            || broken.healthy()
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }
    return true;
}

bool partial_graph_generation_arena_probe() noexcept {
    struct fixture {
        static resonith_partial_path_manifest make_manifest(
            std::uint64_t work_limit,
            std::uint64_t state_limit
        ) noexcept {
            resonith_partial_path_manifest value{};
            value.maximum_work_units = work_limit;
            value.maximum_state_records = state_limit;
            return value;
        }

        resonith_partial_path_manifest manifest{};
        resonith_partial_path_report report{};
        work_ledger_v1 ledger;
        bounded_work_meter work;
        std::array<std::byte, 65536U> storage{};
        std::pmr::monotonic_buffer_resource memory;
        bounded_state_arena arena;

        fixture(std::uint64_t work_limit, std::uint64_t state_limit)
            : manifest(make_manifest(work_limit, state_limit)),
              ledger{.maximum = work_limit},
              work(manifest, &report, &ledger),
              memory(
                  storage.data(),
                  storage.size(),
                  std::pmr::null_memory_resource()
              ),
              arena(&memory, state_limit, &report, &work) {}
    };
    const auto root_node = [](
        std::uint64_t first,
        std::uint64_t current
    ) {
        bounded_state_node value{};
        value.first_observation_id = first;
        value.previous_observation_id = first;
        value.current_observation_id = current;
        value.length = 2U;
        return value;
    };
    const auto child_node = [](
        bounded_state_handle parent,
        std::uint64_t first,
        std::uint64_t previous,
        std::uint64_t current,
        std::uint32_t length
    ) {
        bounded_state_node value{};
        value.parent = parent;
        value.first_observation_id = first;
        value.previous_observation_id = previous;
        value.current_observation_id = current;
        value.length = length;
        return value;
    };

    try {
        fixture value(8192U, 16U);
        auto first_owner = value.arena.create_owned(root_node(10U, 11U));
        const bounded_state_handle first = first_owner.get();
        auto second_owner = value.arena.create_owned(root_node(20U, 21U));
        auto retained = value.arena.retain_owned(first);
        auto child_owner = value.arena.create_owned(
            child_node(first, 10U, 11U, 12U, 3U)
        );
        const bounded_state_handle child = child_owner.get();
        first_owner.reset();
        auto third_owner = value.arena.create_owned(root_node(30U, 31U));
        if (third_owner.get().index == first.index) {
            return false;
        }
        retained.reset();
        auto fourth_owner = value.arena.create_owned(root_node(40U, 41U));
        if (fourth_owner.get().index == first.index) {
            return false;
        }
        child_owner.reset();
        if (
            bounded_state_arena_probe_access::free_head(value.arena)
            != first.index
        ) {
            return false;
        }
        auto reused_parent = value.arena.create_owned(root_node(50U, 51U));
        auto reused_child_slot =
            value.arena.create_owned(root_node(60U, 61U));
        if (
            reused_parent.get().index != first.index
            || reused_parent.get().generation == first.generation
            || reused_child_slot.get().index != child.index
            || reused_child_slot.get().generation == child.generation
        ) {
            return false;
        }
        bool stale_rejected = false;
        try {
            static_cast<void>(value.arena.at(first));
        } catch (const std::logic_error&) {
            stale_rejected = true;
        }
        auto moved_owner = std::move(reused_parent);
        if (
            reused_parent.get() != bounded_state_sentinel
            || moved_owner.get().index != first.index
        ) {
            return false;
        }
        second_owner.reset();
        third_owner.reset();
        fourth_owner.reset();
        moved_owner.reset();
        reused_child_slot.reset();
        if (
            !stale_rejected
            || !value.arena.empty()
            || !value.arena.healthy()
            || !value.work.healthy()
            || value.ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    try {
        fixture value(4096U, 4U);
        auto parent = value.arena.create_owned(root_node(100U, 101U));
        const auto before_references =
            bounded_state_arena_probe_access::reference_count(
                value.arena,
                parent.get()
            );
        const auto before_reserved =
            bounded_state_arena_probe_access::outstanding_references(
                value.arena
            );
        bool rank_rejected = false;
        try {
            static_cast<void>(value.arena.create_owned(
                child_node(parent.get(), 100U, 101U, 102U, 2U)
            ));
        } catch (const std::logic_error&) {
            rank_rejected = true;
        }
        bool root_rejected = false;
        try {
            bounded_state_node invalid_root = root_node(200U, 201U);
            invalid_root.length = 1U;
            static_cast<void>(value.arena.create_owned(invalid_root));
        } catch (const std::logic_error&) {
            root_rejected = true;
        }
        if (
            !rank_rejected
            || !root_rejected
            || bounded_state_arena_probe_access::reference_count(
                   value.arena,
                   parent.get()
               ) != before_references
            || bounded_state_arena_probe_access::outstanding_references(
                   value.arena
               ) != before_reserved
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
        parent.reset();
        if (
            !value.arena.empty()
            || value.ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    try {
        fixture owner_reserve_failure(1U, 2U);
        bool rejected = false;
        try {
            static_cast<void>(
                owner_reserve_failure.arena.create_owned(root_node(1U, 2U))
            );
        } catch (const managed_profile_bound&) {
            rejected = true;
        }
        if (
            !rejected
            || !owner_reserve_failure.arena.empty()
            || owner_reserve_failure.ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(
                owner_reserve_failure.arena
            )
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    for (const std::uint64_t work_limit : {4U, 5U}) {
        try {
            fixture parent_failure(work_limit, 4U);
            auto parent =
                parent_failure.arena.create_owned(root_node(10U, 11U));
            bool rejected = false;
            try {
                static_cast<void>(parent_failure.arena.create_owned(
                    child_node(parent.get(), 10U, 11U, 12U, 3U)
                ));
            } catch (const managed_profile_bound&) {
                rejected = true;
            }
            if (
                !rejected
                || bounded_state_arena_probe_access::reference_count(
                       parent_failure.arena,
                       parent.get()
                   ) != 1U
                || bounded_state_arena_probe_access::outstanding_references(
                       parent_failure.arena
                   ) != 1U
                || !bounded_state_arena_probe_access::audit(
                    parent_failure.arena
                )
            ) {
                return false;
            }
            parent.reset();
            if (
                !parent_failure.arena.empty()
                || parent_failure.ledger.reserved != 0U
            ) {
                return false;
            }
        } catch (...) {
            return false;
        }
    }

    try {
        resonith_partial_path_manifest manifest{};
        manifest.maximum_work_units = 64U;
        resonith_partial_path_report report{};
        work_ledger_v1 ledger{.maximum = manifest.maximum_work_units};
        bounded_work_meter work(manifest, &report, &ledger);
        bounded_state_arena arena(
            std::pmr::null_memory_resource(),
            2U,
            &report,
            &work
        );
        bool allocation_rejected = false;
        try {
            static_cast<void>(arena.create_owned(root_node(1U, 2U)));
        } catch (const std::bad_alloc&) {
            allocation_rejected = true;
        }
        if (
            !allocation_rejected
            || !arena.empty()
            || ledger.total != 0U
            || ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    try {
        fixture value(4096U, 4U);
        auto owner = value.arena.create_owned(root_node(1U, 2U));
        const bounded_state_handle handle = owner.get();
        static_cast<void>(
            bounded_state_arena_probe_access::set_reference_count(
                &value.arena,
                handle,
                std::numeric_limits<std::uint32_t>::max()
            )
        );
        bool overflow_rejected = false;
        try {
            static_cast<void>(value.arena.retain_owned(handle));
        } catch (const std::logic_error&) {
            overflow_rejected = true;
        }
        static_cast<void>(
            bounded_state_arena_probe_access::set_reference_count(
                &value.arena,
                handle,
                1U
            )
        );
        owner.reset();
        if (
            !overflow_rejected
            || !value.arena.empty()
            || value.ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    try {
        fixture value(4096U, 2U);
        auto owner = value.arena.create_owned(root_node(1U, 2U));
        const bounded_state_handle stale = owner.get();
        owner.reset();
        if (
            !bounded_state_arena_probe_access::set_free_generation(
                &value.arena,
                stale.index,
                std::numeric_limits<std::uint32_t>::max()
            )
        ) {
            return false;
        }
        bool generation_rejected = false;
        try {
            static_cast<void>(
                value.arena.create_owned(root_node(3U, 4U))
            );
        } catch (const std::logic_error&) {
            generation_rejected = true;
        }
        if (
            !generation_rejected
            || bounded_state_arena_probe_access::free_head(value.arena)
                != stale.index
            || !bounded_state_arena_probe_access::set_free_generation(
                &value.arena,
                stale.index,
                41U
            )
        ) {
            return false;
        }
        auto recovered = value.arena.create_owned(root_node(5U, 6U));
        if (recovered.get().generation != 42U) {
            return false;
        }
        recovered.reset();
        if (
            !value.arena.empty()
            || value.ledger.reserved != 0U
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }

    try {
        fixture value(256U, 2U);
        auto owner = value.arena.create_owned(root_node(1U, 2U));
        const bounded_state_handle stale = owner.get();
        owner.reset();
        if (
            bounded_state_arena_probe_access::release(
                &value.arena,
                stale
            )
            || value.arena.healthy()
            || !bounded_state_arena_probe_access::audit(value.arena)
        ) {
            return false;
        }
    } catch (...) {
        return false;
    }
    return true;
}

bool partial_graph_work_ledger_probe() noexcept {
    constexpr std::size_t event_count =
        RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT;
    for (std::size_t prefix = 0U; prefix < event_count; ++prefix) {
        work_ledger_v1 ledger{
            .maximum = static_cast<std::uint64_t>(prefix),
        };
        for (std::size_t index = 0U; index < prefix; ++index) {
            if (
                !ledger.emit(
                    static_cast<resonith_partial_path_work_event>(index)
                )
            ) {
                return false;
            }
        }
        if (
            ledger.emit(
                static_cast<resonith_partial_path_work_event>(prefix)
            )
            || ledger.total != prefix
        ) {
            return false;
        }
    }
    for (std::size_t index = 0U; index < event_count; ++index) {
        const auto event =
            static_cast<resonith_partial_path_work_event>(index);
        const auto other = static_cast<resonith_partial_path_work_event>(
            (index + 1U) % event_count
        );
        work_ledger_v1 ledger{.maximum = 1U};
        if (
            !ledger.reserve(event, 1U)
            || ledger.emit_reserved(other, 1U)
            || ledger.reserved != 1U
            || ledger.reserved_counts[index] != 1U
            || !ledger.emit_reserved(event, 1U)
            || ledger.total != 1U
            || ledger.reserved != 0U
            || ledger.counts[index] != 1U
            || ledger.reserved_counts[index] != 0U
        ) {
            return false;
        }
    }
    {
        work_ledger_v1 one_slot{.maximum = 1U};
        if (
            !one_slot.reserve(RESONITH_PARTIAL_WORK_STAGE_RECORD, 1U)
            || one_slot.reserve(RESONITH_PARTIAL_WORK_COMMIT_RECORD, 1U)
            || !one_slot.cancel_reserved(
                RESONITH_PARTIAL_WORK_STAGE_RECORD,
                1U
            )
            || one_slot.total != 0U
            || one_slot.reserved != 0U
        ) {
            return false;
        }
    }
    {
        work_ledger_v1 pair{.maximum = 2U};
        if (
            !pair.reserve(RESONITH_PARTIAL_WORK_STAGE_RECORD, 1U)
            || !pair.reserve(RESONITH_PARTIAL_WORK_COMMIT_RECORD, 1U)
            || !pair.emit_reserved(RESONITH_PARTIAL_WORK_STAGE_RECORD, 1U)
            || !pair.emit_reserved(RESONITH_PARTIAL_WORK_COMMIT_RECORD, 1U)
            || pair.total != 2U
            || pair.reserved != 0U
            || pair.counts[RESONITH_PARTIAL_WORK_STAGE_RECORD] != 1U
            || pair.counts[RESONITH_PARTIAL_WORK_COMMIT_RECORD] != 1U
        ) {
            return false;
        }
    }
    return true;
}

}  // namespace resonith::internal

static resonith_status resonith_partial_graph_paths_cpu_v2_internal(
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
    resonith_partial_path_report* report,
    work_ledger_v1* ledger,
    const std::array<std::uint64_t, 4>& input_identity,
    bool validation_only,
    counting_memory_resource* shared_memory
) {
    if (
        resolutions == nullptr
        || resolution_count == 0U
        || (observations == nullptr && observation_count != 0U)
        || (edges == nullptr && edge_count != 0U)
        || graph_manifest == nullptr
        || path_manifest == nullptr
        || report == nullptr
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

    byte_range resolution_range{};
    byte_range observation_range{};
    byte_range edge_range{};
    byte_range graph_manifest_range{};
    byte_range path_manifest_range{};
    byte_range path_range{};
    byte_range entry_range{};
    byte_range report_range{};
    const std::array<range_status, 8U> range_results = {
        checked_byte_range(
            resolutions,
            resolution_count,
            sizeof(*resolutions),
            alignof(resonith_partial_resolution),
            true,
            &resolution_range
        ),
        checked_byte_range(
            observations,
            observation_count,
            sizeof(*observations),
            alignof(resonith_partial_observation),
            false,
            &observation_range
        ),
        checked_byte_range(
            edges,
            edge_count,
            sizeof(*edges),
            alignof(resonith_partial_edge),
            false,
            &edge_range
        ),
        checked_byte_range(
            graph_manifest,
            1U,
            sizeof(*graph_manifest),
            alignof(resonith_partial_graph_manifest),
            true,
            &graph_manifest_range
        ),
        checked_byte_range(
            path_manifest,
            1U,
            sizeof(*path_manifest),
            alignof(resonith_partial_path_manifest),
            true,
            &path_manifest_range
        ),
        checked_byte_range(
            paths,
            path_capacity,
            sizeof(*paths),
            alignof(resonith_partial_path),
            paths != nullptr,
            &path_range
        ),
        checked_byte_range(
            entries,
            entry_capacity,
            sizeof(*entries),
            alignof(resonith_partial_path_entry),
            entries != nullptr,
            &entry_range
        ),
        checked_byte_range(
            report,
            1U,
            sizeof(*report),
            alignof(resonith_partial_path_report),
            true,
            &report_range
        ),
    };
    if (std::find(range_results.begin(), range_results.end(), range_status::invalid)
        != range_results.end()) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (std::find(range_results.begin(), range_results.end(), range_status::overflow)
        != range_results.end()) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (!pairwise_disjoint(std::array{
            resolution_range,
            observation_range,
            edge_range,
            graph_manifest_range,
            path_manifest_range,
            path_range,
            entry_range,
            report_range,
        })) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    resonith_partial_graph_manifest graph_manifest_snapshot{};
    resonith_partial_path_manifest path_manifest_snapshot{};
    resonith_partial_path_report report_header{};
    if (
        ledger == nullptr
        || !snapshot_object_v1(
            &graph_manifest_snapshot,
            graph_manifest,
            ledger
        )
        || !snapshot_object_v1(
            &path_manifest_snapshot,
            path_manifest,
            ledger
        )
        || !snapshot_object_v1(&report_header, report, ledger)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        !ledger->emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        graph_manifest_snapshot.struct_size != sizeof(graph_manifest_snapshot)
        || graph_manifest_snapshot.abi_version
            != RESONITH_PARTIAL_GRAPH_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!ledger->emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        path_manifest_snapshot.struct_size != sizeof(path_manifest_snapshot)
        || path_manifest_snapshot.abi_version
            != RESONITH_PARTIAL_PATH_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!ledger->emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        report_header.struct_size != sizeof(report_header)
        || report_header.abi_version != RESONITH_PARTIAL_PATH_ABI_VERSION
        || !reserved_zero(report_header)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        resolution_count > RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS
        || observation_count > RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS
        || edge_count > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
        || path_capacity > RESONITH_PARTIAL_PATH_MAX_RECORDS
        || entry_capacity > RESONITH_PARTIAL_PATH_MAX_ENTRIES
        || graph_manifest_snapshot.maximum_edge_records
            > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
        || path_manifest_snapshot.maximum_path_observations
            > RESONITH_PARTIAL_PATH_MAX_OBSERVATIONS
        || path_manifest_snapshot.maximum_path_records
            > RESONITH_PARTIAL_PATH_MAX_RECORDS
        || path_manifest_snapshot.maximum_total_entries
            > RESONITH_PARTIAL_PATH_MAX_ENTRIES
        || path_manifest_snapshot.maximum_frontier_states
            > RESONITH_PARTIAL_PATH_MAX_FRONTIER_STATES
        || path_manifest_snapshot.maximum_state_records
            > RESONITH_PARTIAL_PATH_MAX_STATE_RECORDS
        || path_manifest_snapshot.exact_set_candidate_limit
            > RESONITH_PARTIAL_PATH_MAX_EXACT_SET_CANDIDATES
        || path_manifest_snapshot.maximum_work_units
            > RESONITH_PARTIAL_MAX_WORK_EVENTS
        || path_manifest_snapshot.maximum_managed_bytes
            > RESONITH_PARTIAL_MAX_HOST_BYTES
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    resonith_partial_path_report local_report{};
    local_report.struct_size = sizeof(local_report);
    local_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    if (!valid_path_manifest(path_manifest_snapshot, graph_manifest_snapshot)) {
        *report = local_report;
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    bounded_work_meter preflight_work(
        path_manifest_snapshot,
        &local_report,
        ledger
    );
    std::optional<counting_memory_resource> owned_memory;
    if (shared_memory == nullptr) {
        owned_memory.emplace(
            path_manifest_snapshot.maximum_managed_bytes,
            selected_upstream_resource(),
            &preflight_work,
            &account_host_page_prepare,
            &account_host_page_commit,
            &account_host_page_cancel,
            &account_host_page_release
        );
        shared_memory = &*owned_memory;
    }
    struct peak_report_guard {
        counting_memory_resource* memory;
        resonith_partial_path_report* local;
        resonith_partial_path_report* destination;

        ~peak_report_guard() {
            local->peak_live_managed_bytes = memory->peak_bytes();
            destination->peak_live_managed_bytes = memory->peak_bytes();
        }
    } peak_guard{shared_memory, &local_report, report};
    try {
    std::pmr::vector<resonith_partial_resolution> resolution_snapshot(
        shared_memory
    );
    std::pmr::vector<resonith_partial_observation> observation_snapshot(
        shared_memory
    );
    std::pmr::vector<resonith_partial_edge> edge_snapshot(shared_memory);
    if (
        !snapshot_records_v1(
            &resolution_snapshot,
            resolutions,
            resolution_count,
            ledger
        )
        || !snapshot_records_v1(
            &observation_snapshot,
            observations,
            observation_count,
            ledger
        )
        || !snapshot_records_v1(
            &edge_snapshot,
            edges,
            edge_count,
            ledger
        )
    ) {
        throw managed_profile_bound{};
    }

    if (
        !valid_path_inputs(
            resolution_snapshot.data(),
            resolution_snapshot.size(),
            observation_snapshot.data(),
            observation_snapshot.size(),
            edge_snapshot.data(),
            edge_snapshot.size(),
            graph_manifest_snapshot,
            shared_memory,
            [&preflight_work](
                resonith_partial_path_work_event event,
                std::uint64_t amount
            ) {
                preflight_work.charge(amount, event);
            }
        )
    ) {
        *report = local_report;
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    const auto fingerprint = input_identity;
    std::copy(
        fingerprint.begin(),
        fingerprint.end(),
        local_report.input_fingerprint
    );
    if (validation_only) {
        *report = local_report;
        return RESONITH_STATUS_OK;
    }
    const bool fill = paths != nullptr;
    const bool expected_present = std::any_of(
        std::begin(path_manifest_snapshot.expected_input_fingerprint),
        std::end(path_manifest_snapshot.expected_input_fingerprint),
        [](std::uint64_t item) { return item != 0U; }
    );
    if (
        expected_present
        && !std::equal(
            fingerprint.begin(),
            fingerprint.end(),
            path_manifest_snapshot.expected_input_fingerprint
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

    path_output output(shared_memory);
    const resonith_status status = compute_paths_bounded(
        observation_snapshot.data(),
        observation_snapshot.size(),
        edge_snapshot.data(),
        edge_snapshot.size(),
        graph_manifest_snapshot,
        path_manifest_snapshot,
        &local_report,
        &output,
        shared_memory,
        ledger
    );
    if (status != RESONITH_STATUS_OK) {
        *report = local_report;
        return status;
    }
    std::array<std::uint64_t, 4> output_hash{};
    if (
        !output_fingerprint_legacy_as_v3(
            output.paths,
            output.entries,
            ledger,
            &output_hash
        )
    ) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        *report = local_report;
        return RESONITH_STATUS_PROFILE_BOUND;
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
    for (std::size_t index = 0U; index < output.paths.size(); ++index) {
        preflight_work.charge(1U, RESONITH_PARTIAL_WORK_STAGE_RECORD);
        paths[index] = output.paths[index];
    }
    for (std::size_t index = 0U; index < output.entries.size(); ++index) {
        preflight_work.charge(1U, RESONITH_PARTIAL_WORK_STAGE_RECORD);
        entries[index] = output.entries[index];
    }
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

extern "C" resonith_status resonith_partial_graph_paths_cpu_v2(
    const resonith_partial_resolution*,
    std::size_t,
    const resonith_partial_observation*,
    std::size_t,
    const resonith_partial_edge*,
    std::size_t,
    const resonith_partial_graph_manifest*,
    const resonith_partial_path_manifest*,
    resonith_partial_path*,
    std::size_t,
    resonith_partial_path_entry*,
    std::size_t,
    resonith_partial_path_report*
) {
    return RESONITH_STATUS_UNSUPPORTED_VERSION;
}

extern "C" resonith_status resonith_partial_graph_paths_cpu_v3(
    const resonith_partial_resolution* resolutions,
    std::size_t resolution_count,
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_edge* edges,
    std::size_t edge_count,
    const resonith_partial_graph_manifest* graph_manifest,
    const resonith_partial_path_manifest_v3* path_manifest,
    resonith_partial_path_v3* paths,
    std::size_t path_capacity,
    resonith_partial_path_entry_v3* entries,
    std::size_t entry_capacity,
    resonith_partial_path_report_v3* report
) {
    const bool fill = paths != nullptr;
    if (
        resolutions == nullptr
        || resolution_count == 0U
        || (observations == nullptr && observation_count != 0U)
        || (edges == nullptr && edge_count != 0U)
        || graph_manifest == nullptr
        || path_manifest == nullptr
        || report == nullptr
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

    byte_range resolution_range{};
    byte_range observation_range{};
    byte_range edge_range{};
    byte_range graph_manifest_range{};
    byte_range path_manifest_range{};
    byte_range path_range{};
    byte_range entry_range{};
    byte_range report_range{};
    const std::array<range_status, 8U> range_results = {
        checked_byte_range(
            resolutions,
            resolution_count,
            sizeof(*resolutions),
            alignof(resonith_partial_resolution),
            true,
            &resolution_range
        ),
        checked_byte_range(
            observations,
            observation_count,
            sizeof(*observations),
            alignof(resonith_partial_observation),
            false,
            &observation_range
        ),
        checked_byte_range(
            edges,
            edge_count,
            sizeof(*edges),
            alignof(resonith_partial_edge),
            false,
            &edge_range
        ),
        checked_byte_range(
            graph_manifest,
            1U,
            sizeof(*graph_manifest),
            alignof(resonith_partial_graph_manifest),
            true,
            &graph_manifest_range
        ),
        checked_byte_range(
            path_manifest,
            1U,
            sizeof(*path_manifest),
            alignof(resonith_partial_path_manifest_v3),
            true,
            &path_manifest_range
        ),
        checked_byte_range(
            paths,
            path_capacity,
            sizeof(*paths),
            alignof(resonith_partial_path_v3),
            fill,
            &path_range
        ),
        checked_byte_range(
            entries,
            entry_capacity,
            sizeof(*entries),
            alignof(resonith_partial_path_entry_v3),
            fill,
            &entry_range
        ),
        checked_byte_range(
            report,
            1U,
            sizeof(*report),
            alignof(resonith_partial_path_report_v3),
            true,
            &report_range
        ),
    };
    if (std::find(range_results.begin(), range_results.end(), range_status::invalid)
        != range_results.end()) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        range_results[3U] == range_status::overflow
        || range_results[4U] == range_status::overflow
        || range_results[7U] == range_status::overflow
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    work_ledger_v1 ledger{
        .maximum = RESONITH_PARTIAL_MAX_WORK_EVENTS,
    };
    resonith_partial_graph_manifest graph_snapshot{};
    resonith_partial_path_manifest_v3 manifest_snapshot{};
    resonith_partial_path_report_v3 report_header{};
    if (
        !snapshot_object_v1(&graph_snapshot, graph_manifest, &ledger)
        || !snapshot_object_v1(&manifest_snapshot, path_manifest, &ledger)
        || !snapshot_object_v1(&report_header, report, &ledger)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (!ledger.emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        graph_snapshot.struct_size != sizeof(graph_snapshot)
        || graph_snapshot.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!ledger.emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        manifest_snapshot.struct_size != sizeof(manifest_snapshot)
        || manifest_snapshot.abi_version
            != RESONITH_PARTIAL_PATH_V3_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!ledger.emit(RESONITH_PARTIAL_WORK_VALIDATE_RECORD)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        report_header.struct_size != sizeof(report_header)
        || report_header.abi_version != RESONITH_PARTIAL_PATH_V3_ABI_VERSION
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (std::find(range_results.begin(), range_results.end(), range_status::overflow)
        != range_results.end()) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (!pairwise_disjoint(std::array{
            resolution_range,
            observation_range,
            edge_range,
            graph_manifest_range,
            path_manifest_range,
            path_range,
            entry_range,
            report_range,
        })) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        manifest_snapshot.second_order_law_version != 2U
        || manifest_snapshot.work_ledger_version
            != RESONITH_PARTIAL_PATH_WORK_LEDGER_VERSION
        || !reserved_zero(graph_snapshot)
        || !reserved_zero(manifest_snapshot)
        || !reserved_zero(report_header)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        resolution_count > RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS
        || observation_count > RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS
        || edge_count > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
        || path_capacity > RESONITH_PARTIAL_PATH_MAX_RECORDS
        || entry_capacity > RESONITH_PARTIAL_PATH_MAX_ENTRIES
        || graph_snapshot.maximum_edge_records
            > RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS
        || manifest_snapshot.maximum_path_observations
            > RESONITH_PARTIAL_PATH_MAX_OBSERVATIONS
        || manifest_snapshot.maximum_path_records
            > RESONITH_PARTIAL_PATH_MAX_RECORDS
        || manifest_snapshot.maximum_total_entries
            > RESONITH_PARTIAL_PATH_MAX_ENTRIES
        || manifest_snapshot.maximum_frontier_states
            > RESONITH_PARTIAL_PATH_MAX_FRONTIER_STATES
        || manifest_snapshot.maximum_state_records
            > RESONITH_PARTIAL_PATH_MAX_STATE_RECORDS
        || manifest_snapshot.exact_set_candidate_limit
            > RESONITH_PARTIAL_PATH_MAX_EXACT_SET_CANDIDATES
        || manifest_snapshot.maximum_work_units < 2U
        || manifest_snapshot.maximum_work_units
            > RESONITH_PARTIAL_MAX_WORK_EVENTS
        || manifest_snapshot.maximum_managed_bytes
            > RESONITH_PARTIAL_MAX_HOST_BYTES
        || manifest_snapshot.maximum_device_bytes
            > RESONITH_PARTIAL_MAX_DEVICE_BYTES
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    ledger.maximum = manifest_snapshot.maximum_work_units;
    if (
        ledger.total > ledger.maximum
        || ledger.reserved > ledger.maximum - ledger.total
        || !ledger.reserve(RESONITH_PARTIAL_WORK_STAGE_RECORD, 1U)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (!ledger.reserve(RESONITH_PARTIAL_WORK_COMMIT_RECORD, 1U)) {
        static_cast<void>(ledger.cancel_reserved(
            RESONITH_PARTIAL_WORK_STAGE_RECORD,
            1U
        ));
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        !ledger.emit_reserved(RESONITH_PARTIAL_WORK_STAGE_RECORD, 1U)
    ) {
        static_cast<void>(ledger.cancel_reserved(
            RESONITH_PARTIAL_WORK_COMMIT_RECORD,
            1U
        ));
        return RESONITH_STATUS_MALFORMED;
    }

    resonith_partial_path_report_v3 local_report{};
    local_report.struct_size = sizeof(local_report);
    local_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    counting_memory_resource* active_memory = nullptr;
    const auto sync_ledger = [&]() noexcept {
        local_report.work_units = ledger.total + ledger.reserved;
        for (std::size_t index = 0U; index < ledger.counts.size(); ++index) {
            local_report.work_event_counts[index] =
                ledger.counts[index] + ledger.reserved_counts[index];
        }
    };
    sync_ledger();

    const auto publish_report = [&]() noexcept {
        if (
            !ledger.emit_reserved(
                RESONITH_PARTIAL_WORK_COMMIT_RECORD,
                1U
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
        }
        sync_ledger();
        if (active_memory != nullptr) {
            local_report.reserved_host_bytes =
                active_memory->reserved_bytes();
            local_report.committed_host_bytes =
                active_memory->committed_bytes();
            local_report.peak_live_host_bytes = active_memory->peak_bytes();
            if (!active_memory->healthy()) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
            }
        }
        local_report.written_path_count = 0U;
        local_report.written_entry_count = 0U;
        *report = local_report;
    };
    const auto import_legacy_report = [&](
        const resonith_partial_path_report& legacy
    ) noexcept {
        const auto event_counts = ledger.counts;
        const auto wrapper_work = ledger.total;
        std::memcpy(&local_report, &legacy, 304U);
        local_report.struct_size = sizeof(local_report);
        local_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
        ledger.counts = event_counts;
        ledger.total = wrapper_work;
        local_report.work_units = wrapper_work;
        std::copy(
            event_counts.begin(),
            event_counts.end(),
            local_report.work_event_counts
        );
        local_report.peak_live_host_bytes = legacy.peak_live_managed_bytes;
        local_report.flags = legacy.flags;
    };

    resonith_partial_path_manifest legacy_manifest{};
    std::memcpy(&legacy_manifest, &manifest_snapshot, 144U);
    legacy_manifest.struct_size = sizeof(legacy_manifest);
    legacy_manifest.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    legacy_manifest.reserved_alignment = 0U;
    legacy_manifest.maximum_work_units =
        manifest_snapshot.maximum_work_units
        - ledger.total
        - ledger.reserved;
    std::fill(
        std::begin(legacy_manifest.expected_input_fingerprint),
        std::end(legacy_manifest.expected_input_fingerprint),
        0U
    );
    std::copy(
        std::begin(manifest_snapshot.protected_band_upper_hz_q20),
        std::end(manifest_snapshot.protected_band_upper_hz_q20),
        legacy_manifest.protected_band_upper_hz_q20
    );
    resonith_partial_path_report shared_memory_report{};
    shared_memory_report.struct_size = sizeof(shared_memory_report);
    shared_memory_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
    bounded_work_meter shared_memory_work(
        legacy_manifest,
        &shared_memory_report,
        &ledger
    );
    counting_memory_resource shared_memory(
        manifest_snapshot.maximum_managed_bytes,
        selected_upstream_resource(),
        &shared_memory_work,
        &account_host_page_prepare,
        &account_host_page_commit,
        &account_host_page_cancel,
        &account_host_page_release
    );
    active_memory = &shared_memory;

    try {
        std::array<std::uint64_t, 4> v3_input_fingerprint{};
        std::pmr::vector<resonith_partial_resolution> canonical_resolutions(
            &shared_memory
        );
        std::pmr::vector<resonith_partial_observation> canonical_observations(
            &shared_memory
        );
        if (
            !snapshot_canonical_inputs_v3(
                resolutions,
                resolution_count,
                observations,
                observation_count,
                &ledger,
                &canonical_resolutions,
                &canonical_observations
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        legacy_manifest.maximum_work_units =
            manifest_snapshot.maximum_work_units
            - ledger.total
            - ledger.reserved;
        resonith_partial_path_report validation_report{};
        validation_report.struct_size = sizeof(validation_report);
        validation_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
        resonith_status status = resonith_partial_graph_paths_cpu_v2_internal(
            canonical_resolutions.data(),
            canonical_resolutions.size(),
            canonical_observations.data(),
            canonical_observations.size(),
            edges,
            edge_count,
            &graph_snapshot,
            &legacy_manifest,
            nullptr,
            0U,
            nullptr,
            0U,
            &validation_report,
            &ledger,
            v3_input_fingerprint,
            true,
            &shared_memory
        );
        if (status != RESONITH_STATUS_OK) {
            import_legacy_report(validation_report);
            publish_report();
            return status;
        }
        if (fill) {
            const bool expected_present = std::any_of(
                std::begin(manifest_snapshot.expected_input_fingerprint),
                std::end(manifest_snapshot.expected_input_fingerprint),
                [](std::uint64_t item) { return item != 0U; }
            );
            if (!expected_present) {
                publish_report();
                return RESONITH_STATUS_INVALID_ARGUMENT;
            }
        }
        if (
            !input_fingerprint_v3(
                canonical_resolutions,
                canonical_observations,
                edges,
                edge_count,
                graph_snapshot,
                manifest_snapshot,
                &ledger,
                &shared_memory,
                &v3_input_fingerprint
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        std::copy(
            v3_input_fingerprint.begin(),
            v3_input_fingerprint.end(),
            local_report.input_fingerprint
        );
        if (fill) {
            if (
                !std::equal(
                    v3_input_fingerprint.begin(),
                    v3_input_fingerprint.end(),
                    manifest_snapshot.expected_input_fingerprint
                )
            ) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT;
                publish_report();
                return RESONITH_STATUS_HASH_MISMATCH;
            }
        }
        legacy_manifest.maximum_work_units =
            manifest_snapshot.maximum_work_units
            - ledger.total
            - ledger.reserved;
        resonith_partial_path_report legacy_report{};
        legacy_report.struct_size = sizeof(legacy_report);
        legacy_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
        status = resonith_partial_graph_paths_cpu_v2_internal(
            canonical_resolutions.data(),
            canonical_resolutions.size(),
            canonical_observations.data(),
            canonical_observations.size(),
            edges,
            edge_count,
            &graph_snapshot,
            &legacy_manifest,
            nullptr,
            0U,
            nullptr,
            0U,
            &legacy_report,
            &ledger,
            v3_input_fingerprint,
            false,
            &shared_memory
        );
        import_legacy_report(legacy_report);
        std::copy(
            v3_input_fingerprint.begin(),
            v3_input_fingerprint.end(),
            local_report.input_fingerprint
        );
        if (status != RESONITH_STATUS_OK) {
            publish_report();
            return status;
        }
        if (!fill) {
            publish_report();
            return RESONITH_STATUS_OK;
        }
        std::copy(
            std::begin(legacy_report.input_fingerprint),
            std::end(legacy_report.input_fingerprint),
            legacy_manifest.expected_input_fingerprint
        );
        if (
            path_capacity < legacy_report.required_path_count
            || entry_capacity < legacy_report.required_entry_count
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_OUTPUT_TOO_SMALL;
            publish_report();
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }

        std::uint64_t stage_bytes =
            legacy_report.required_path_count
            * (
                sizeof(resonith_partial_path)
                + sizeof(resonith_partial_path_v3)
            );
        if (
            legacy_report.required_entry_count
            > (
                std::numeric_limits<std::uint64_t>::max() - stage_bytes
            ) / (
                sizeof(resonith_partial_path_entry)
                + sizeof(resonith_partial_path_entry_v3)
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        stage_bytes += legacy_report.required_entry_count
            * (
                sizeof(resonith_partial_path_entry)
                + sizeof(resonith_partial_path_entry_v3)
            );
        if (stage_bytes > manifest_snapshot.maximum_managed_bytes) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        std::pmr::vector<resonith_partial_path> staged_paths(&shared_memory);
        std::pmr::vector<resonith_partial_path_entry> staged_entries(
            &shared_memory
        );
        staged_paths.resize(legacy_report.required_path_count);
        staged_entries.resize(legacy_report.required_entry_count);
        legacy_report = {};
        legacy_report.struct_size = sizeof(legacy_report);
        legacy_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
        status = resonith_partial_graph_paths_cpu_v2_internal(
            canonical_resolutions.data(),
            canonical_resolutions.size(),
            canonical_observations.data(),
            canonical_observations.size(),
            edges,
            edge_count,
            &graph_snapshot,
            &legacy_manifest,
            staged_paths.data(),
            staged_paths.size(),
            staged_entries.data(),
            staged_entries.size(),
            &legacy_report,
            &ledger,
            v3_input_fingerprint,
            false,
            &shared_memory
        );
        import_legacy_report(legacy_report);
        std::copy(
            v3_input_fingerprint.begin(),
            v3_input_fingerprint.end(),
            local_report.input_fingerprint
        );
        local_report.reserved_host_bytes = shared_memory.reserved_bytes();
        local_report.committed_host_bytes = shared_memory.committed_bytes();
        local_report.peak_live_host_bytes = shared_memory.peak_bytes();
        if (
            local_report.peak_live_host_bytes
            > manifest_snapshot.maximum_managed_bytes
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        if (status != RESONITH_STATUS_OK) {
            publish_report();
            return status;
        }

        std::pmr::vector<resonith_partial_path_v3> staged_paths_v3(
            &shared_memory
        );
        staged_paths_v3.reserve(staged_paths.size());
        for (const resonith_partial_path& legacy : staged_paths) {
            if (!ledger.emit(RESONITH_PARTIAL_WORK_STAGE_RECORD)) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
                local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
                publish_report();
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            resonith_partial_path_v3 converted{};
            std::memcpy(&converted, &legacy, sizeof(converted));
            converted.struct_size = sizeof(converted);
            converted.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
            staged_paths_v3.push_back(converted);
        }
        std::pmr::vector<resonith_partial_path_entry_v3> staged_entries_v3(
            &shared_memory
        );
        staged_entries_v3.reserve(staged_entries.size());
        for (const resonith_partial_path_entry& legacy : staged_entries) {
            if (!ledger.emit(RESONITH_PARTIAL_WORK_STAGE_RECORD)) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
                local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
                publish_report();
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            resonith_partial_path_entry_v3 converted{};
            std::memcpy(&converted, &legacy, sizeof(converted));
            converted.struct_size = sizeof(converted);
            converted.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
            staged_entries_v3.push_back(converted);
        }

        std::array<std::uint64_t, 4> output_hash{};
        if (
            !output_fingerprint_v3(
                staged_paths_v3,
                staged_entries_v3,
                &ledger,
                &output_hash
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        std::copy(
            output_hash.begin(),
            output_hash.end(),
            local_report.output_fingerprint
        );

        const std::uint64_t payload_commit_count =
            static_cast<std::uint64_t>(staged_paths_v3.size())
            + static_cast<std::uint64_t>(staged_entries_v3.size());
        if (
            !ledger.reserve(
                RESONITH_PARTIAL_WORK_COMMIT_RECORD,
                payload_commit_count
            )
        ) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
            local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
            publish_report();
            return RESONITH_STATUS_PROFILE_BOUND;
        }

        for (std::size_t index = 0U; index < staged_paths_v3.size(); ++index) {
            if (
                !ledger.emit_reserved(
                    RESONITH_PARTIAL_WORK_COMMIT_RECORD,
                    1U
                )
            ) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
                publish_report();
                return RESONITH_STATUS_MALFORMED;
            }
            paths[index] = staged_paths_v3[index];
        }
        for (std::size_t index = 0U; index < staged_entries_v3.size(); ++index) {
            if (
                !ledger.emit_reserved(
                    RESONITH_PARTIAL_WORK_COMMIT_RECORD,
                    1U
                )
            ) {
                local_report.termination =
                    RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
                publish_report();
                return RESONITH_STATUS_MALFORMED;
            }
            entries[index] = staged_entries_v3[index];
        }
        if (!shared_memory.healthy() || !shared_memory_work.healthy()) {
            local_report.termination =
                RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
            publish_report();
            return RESONITH_STATUS_MALFORMED;
        }
        local_report.reserved_host_bytes = shared_memory.reserved_bytes();
        local_report.committed_host_bytes = shared_memory.committed_bytes();
        local_report.peak_live_host_bytes = shared_memory.peak_bytes();
        local_report.written_path_count = staged_paths_v3.size();
        local_report.written_entry_count = staged_entries_v3.size();
        if (
            !ledger.emit_reserved(
                RESONITH_PARTIAL_WORK_COMMIT_RECORD,
                1U
            )
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        sync_ledger();
        *report = local_report;
        return RESONITH_STATUS_OK;
    } catch (const managed_profile_bound&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_PROFILE_BOUND;
        local_report.flags |= RESONITH_PARTIAL_PATH_REPORT_BOUND_HIT;
        publish_report();
        return RESONITH_STATUS_PROFILE_BOUND;
    } catch (const environmental_out_of_memory&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM;
        publish_report();
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (const std::bad_alloc&) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM;
        publish_report();
        return RESONITH_STATUS_OUT_OF_MEMORY;
    } catch (...) {
        local_report.termination =
            RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED;
        publish_report();
        return RESONITH_STATUS_MALFORMED;
    }
}
