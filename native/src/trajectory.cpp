#include "resonith/trajectory.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace {

constexpr std::uint32_t kMaximumKnotSpan = 32768;
constexpr std::uint32_t kMaximumKnots = 1'000'000;
constexpr std::uint32_t kMaximumSampleCount = 0x7fff'ffffU;
constexpr std::size_t kMaximumBasisSamples = 8U * 2048U;

std::int64_t round_divide_ties_away(
    std::int64_t numerator,
    std::int64_t denominator
) noexcept {
    const bool negative = numerator < 0;
    const std::uint64_t magnitude = negative
        ? static_cast<std::uint64_t>(-(numerator + 1)) + 1U
        : static_cast<std::uint64_t>(numerator);
    const std::uint64_t rounded = (
        magnitude + static_cast<std::uint64_t>(denominator / 2)
    ) / static_cast<std::uint64_t>(denominator);
    return negative
        ? -static_cast<std::int64_t>(rounded)
        : static_cast<std::int64_t>(rounded);
}

std::int64_t floor_divide_65536(std::int64_t value) noexcept {
    constexpr std::int64_t kDivisor = 65536;
    if (value >= 0) {
        return value / kDivisor;
    }
    return -((-value + kDivisor - 1) / kDivisor);
}

std::int16_t saturate_int16(std::int64_t value) noexcept {
    return static_cast<std::int16_t>(
        std::clamp<std::int64_t>(value, -32768, 32767)
    );
}

std::int64_t phase_advance(
    std::uint32_t length,
    std::uint32_t start_increment,
    std::uint32_t end_increment
) noexcept {
    const std::int64_t delta = static_cast<std::int64_t>(end_increment)
        - start_increment;
    const std::int64_t curve = delta
        * length
        * (static_cast<std::int64_t>(length) - 1);
    return static_cast<std::int64_t>(length) * start_increment
        + round_divide_ties_away(
            curve,
            2 * static_cast<std::int64_t>(length)
        );
}

bool valid_prepared(
    const resonith_prepared_phase_trajectory* trajectory
) noexcept {
    return trajectory != nullptr
        && trajectory->positions != nullptr
        && trajectory->increments_q32 != nullptr
        && trajectory->knot_origins_q32 != nullptr
        && trajectory->knot_count >= 2U
        && trajectory->knot_count <= kMaximumKnots
        && trajectory->sample_count != 0U
        && trajectory->sample_count <= kMaximumSampleCount;
}

std::uint32_t interval_for(
    const resonith_prepared_phase_trajectory& trajectory,
    std::uint32_t position
) noexcept {
    std::uint32_t lower = 0U;
    std::uint32_t upper = trajectory.knot_count - 1U;
    while (lower + 1U < upper) {
        const std::uint32_t middle = lower + (upper - lower) / 2U;
        if (trajectory.positions[middle] <= position) {
            lower = middle;
        } else {
            upper = middle;
        }
    }
    return lower;
}

std::uint32_t phase_at(
    const resonith_prepared_phase_trajectory& trajectory,
    std::uint32_t interval,
    std::uint32_t absolute_position
) noexcept {
    const std::uint32_t interval_start = trajectory.positions[interval];
    const std::uint32_t interval_end = trajectory.positions[interval + 1U];
    const std::uint32_t local = absolute_position - interval_start;
    const std::uint32_t length = interval_end - interval_start;
    const std::uint32_t increment = trajectory.increments_q32[interval];
    const std::int64_t delta = static_cast<std::int64_t>(
        trajectory.increments_q32[interval + 1U]
    ) - increment;
    const std::int64_t curve_numerator = delta
        * local
        * (static_cast<std::int64_t>(local) - 1);
    const std::int64_t phase =
        trajectory.knot_origins_q32[interval]
        + static_cast<std::int64_t>(local) * increment
        + round_divide_ties_away(
            curve_numerator,
            2 * static_cast<std::int64_t>(length)
        );
    return static_cast<std::uint32_t>(phase);
}

resonith_status validate_slice(
    const resonith_prepared_phase_trajectory* trajectory,
    std::uint32_t output_start,
    std::size_t output_count,
    std::size_t output_capacity
) noexcept {
    if (!valid_prepared(trajectory)) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        output_start > trajectory->sample_count
        || output_count
            > static_cast<std::size_t>(
                trajectory->sample_count - output_start
            )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (output_capacity < output_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_phase_prepare(
    const resonith_phase_trajectory* trajectory,
    std::uint32_t* knot_origins_q32,
    std::size_t origin_capacity,
    resonith_prepared_phase_trajectory* prepared
) {
    if (
        trajectory == nullptr
        || prepared == nullptr
        || trajectory->positions == nullptr
        || trajectory->increments_q32 == nullptr
        || knot_origins_q32 == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *prepared = {};
    if (
        trajectory->knot_count < 2U
        || trajectory->knot_count > kMaximumKnots
        || origin_capacity < trajectory->knot_count
    ) {
        return origin_capacity < trajectory->knot_count
            ? RESONITH_STATUS_OUTPUT_TOO_SMALL
            : RESONITH_STATUS_PROFILE_BOUND;
    }
    if (trajectory->positions[0] != 0U) {
        return RESONITH_STATUS_MALFORMED;
    }
    for (
        std::uint32_t index = 0;
        index + 1U < trajectory->knot_count;
        ++index
    ) {
        const std::uint32_t start = trajectory->positions[index];
        const std::uint32_t end = trajectory->positions[index + 1U];
        if (end <= start || end - start > kMaximumKnotSpan) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    const std::uint32_t sample_count =
        trajectory->positions[trajectory->knot_count - 1U];
    if (sample_count == 0U || sample_count > kMaximumSampleCount) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    knot_origins_q32[0] = trajectory->phase_origin_q32;
    for (
        std::uint32_t index = 0;
        index + 1U < trajectory->knot_count;
        ++index
    ) {
        const std::uint32_t length =
            trajectory->positions[index + 1U]
            - trajectory->positions[index];
        const std::int64_t next =
            knot_origins_q32[index]
            + phase_advance(
                length,
                trajectory->increments_q32[index],
                trajectory->increments_q32[index + 1U]
            );
        knot_origins_q32[index + 1U] = static_cast<std::uint32_t>(next);
    }

    prepared->positions = trajectory->positions;
    prepared->increments_q32 = trajectory->increments_q32;
    prepared->knot_origins_q32 = knot_origins_q32;
    prepared->knot_count = trajectory->knot_count;
    prepared->sample_count = sample_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_phase_render(
    const resonith_prepared_phase_trajectory* trajectory,
    std::uint32_t output_start,
    std::size_t output_count,
    std::uint32_t* output,
    std::size_t output_capacity
) {
    const resonith_status slice_status = validate_slice(
        trajectory,
        output_start,
        output_count,
        output_capacity
    );
    if (slice_status != RESONITH_STATUS_OK) {
        return slice_status;
    }
    if (output_count == 0U) {
        return RESONITH_STATUS_OK;
    }
    if (output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    std::uint32_t interval = interval_for(*trajectory, output_start);
    for (std::size_t index = 0; index < output_count; ++index) {
        const std::uint32_t absolute =
            output_start + static_cast<std::uint32_t>(index);
        while (
            absolute >= trajectory->positions[interval + 1U]
            && interval + 2U < trajectory->knot_count
        ) {
            ++interval;
        }
        output[index] = phase_at(*trajectory, interval, absolute);
    }
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_periodic_render(
    const std::int16_t* basis,
    std::size_t basis_count,
    const resonith_prepared_phase_trajectory* trajectory,
    std::uint32_t output_start,
    std::size_t output_count,
    std::int16_t* output,
    std::size_t output_capacity
) {
    const resonith_status slice_status = validate_slice(
        trajectory,
        output_start,
        output_count,
        output_capacity
    );
    if (slice_status != RESONITH_STATUS_OK) {
        return slice_status;
    }
    if (
        basis == nullptr
        || basis_count < 2U
        || basis_count > kMaximumBasisSamples
        || (output_count != 0U && output == nullptr)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_count == 0U) {
        return RESONITH_STATUS_OK;
    }

    std::uint32_t interval = interval_for(*trajectory, output_start);
    for (std::size_t index = 0; index < output_count; ++index) {
        const std::uint32_t absolute =
            output_start + static_cast<std::uint32_t>(index);
        while (
            absolute >= trajectory->positions[interval + 1U]
            && interval + 2U < trajectory->knot_count
        ) {
            ++interval;
        }
        const std::uint64_t position =
            static_cast<std::uint64_t>(
                phase_at(*trajectory, interval, absolute)
            ) * basis_count;
        const std::size_t left_index =
            static_cast<std::size_t>(position >> 32U);
        const std::size_t right_index =
            left_index + 1U == basis_count ? 0U : left_index + 1U;
        const std::int64_t fraction =
            static_cast<std::int64_t>((position >> 16U) & 0xffffU);
        const std::int64_t weighted =
            static_cast<std::int64_t>(basis[left_index])
                * (65536 - fraction)
            + static_cast<std::int64_t>(basis[right_index]) * fraction
            + 32768;
        output[index] = saturate_int16(floor_divide_65536(weighted));
    }
    return RESONITH_STATUS_OK;
}
