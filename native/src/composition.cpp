#include "resonith/composition.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace {

constexpr std::uint32_t kMaximumEvents = 1'000'000;
constexpr std::uint32_t kMaximumSampleCount = 0x7fff'ffffU;
constexpr std::int32_t kMinimumGain = -131072;
constexpr std::int32_t kMaximumGain = 131071;
constexpr std::uint32_t kMaximumInnovationStep = 1U << 20U;

std::int64_t floor_divide_32768(std::int64_t value) noexcept {
    constexpr std::int64_t kDivisor = 32768;
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

std::uint32_t event_for(
    const resonith_prepared_gain_law& law,
    std::uint32_t position
) noexcept {
    std::uint32_t lower = 0U;
    std::uint32_t upper = law.event_count;
    while (lower + 1U < upper) {
        const std::uint32_t middle = lower + (upper - lower) / 2U;
        if (law.positions[middle] <= position) {
            lower = middle;
        } else {
            upper = middle;
        }
    }
    return lower;
}

}  // namespace

extern "C" resonith_status resonith_gain_prepare(
    const resonith_gain_event_law* source,
    resonith_prepared_gain_law* prepared
) {
    if (
        source == nullptr
        || prepared == nullptr
        || source->positions == nullptr
        || source->gains_q15 == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *prepared = {};
    if (
        source->event_count == 0U
        || source->event_count > kMaximumEvents
        || source->sample_count == 0U
        || source->sample_count > kMaximumSampleCount
        || source->positions[0] != 0U
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::uint32_t previous = 0U;
    for (std::uint32_t index = 0; index < source->event_count; ++index) {
        const std::uint32_t position = source->positions[index];
        const std::int32_t gain = source->gains_q15[index];
        if (
            (index != 0U && position <= previous)
            || position >= source->sample_count
            || gain < kMinimumGain
            || gain > kMaximumGain
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        previous = position;
    }
    prepared->positions = source->positions;
    prepared->gains_q15 = source->gains_q15;
    prepared->event_count = source->event_count;
    prepared->sample_count = source->sample_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_compose_truth(
    const std::int16_t* unity_prediction,
    const std::int64_t* innovation_q,
    std::uint32_t innovation_step,
    const resonith_prepared_gain_law* gain_law,
    std::uint32_t output_start,
    std::size_t output_count,
    std::int16_t* output,
    std::size_t output_capacity
) {
    if (
        gain_law == nullptr
        || gain_law->positions == nullptr
        || gain_law->gains_q15 == nullptr
        || gain_law->event_count == 0U
        || gain_law->event_count > kMaximumEvents
        || gain_law->sample_count == 0U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        output_start > gain_law->sample_count
        || output_count
            > static_cast<std::size_t>(
                gain_law->sample_count - output_start
            )
        || (innovation_q != nullptr
            && (innovation_step == 0U
                || innovation_step > kMaximumInnovationStep))
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (output_capacity < output_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (
        output_count != 0U
        && (unity_prediction == nullptr || output == nullptr)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_count == 0U) {
        return RESONITH_STATUS_OK;
    }

    std::uint32_t event = event_for(*gain_law, output_start);
    for (std::size_t index = 0; index < output_count; ++index) {
        const std::uint32_t absolute =
            output_start + static_cast<std::uint32_t>(index);
        while (
            event + 1U < gain_law->event_count
            && absolute >= gain_law->positions[event + 1U]
        ) {
            ++event;
        }
        const std::int64_t scaled = floor_divide_32768(
            static_cast<std::int64_t>(unity_prediction[index])
                * gain_law->gains_q15[event]
            + 16384
        );
        const std::int64_t innovation = innovation_q == nullptr
            ? 0
            : innovation_q[index] * innovation_step;
        output[index] = saturate_int16(scaled + innovation);
    }
    return RESONITH_STATUS_OK;
}
