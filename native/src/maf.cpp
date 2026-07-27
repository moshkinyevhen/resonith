#include "resonith/maf.h"

#include "resonith/trajectory.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace {

constexpr std::int32_t kMaximumReflectionQ15 = 29491;
constexpr std::int32_t kMaximumGainQ15 = 4 * 32768;
constexpr std::int64_t kMaximumLpcQ15 = 1LL << 22;

bool checked_multiply(
    std::uint64_t left,
    std::uint64_t right,
    std::uint64_t& result
) noexcept {
    if (
        left != 0U
        && right > std::numeric_limits<std::uint64_t>::max() / left
    ) {
        return false;
    }
    result = left * right;
    return true;
}

bool valid_gain(std::int32_t gain_q15) noexcept {
    return gain_q15 >= -kMaximumGainQ15
        && gain_q15 <= kMaximumGainQ15;
}

std::int64_t round_shift_q15(std::int64_t value) noexcept {
    const bool negative = value < 0;
    const std::uint64_t magnitude = negative
        ? static_cast<std::uint64_t>(-(value + 1)) + 1U
        : static_cast<std::uint64_t>(value);
    const std::uint64_t rounded = (magnitude + 16384U) >> 15U;
    return negative
        ? -static_cast<std::int64_t>(rounded)
        : static_cast<std::int64_t>(rounded);
}

std::int16_t saturate_int16(std::int64_t value) noexcept {
    return static_cast<std::int16_t>(
        std::clamp<std::int64_t>(value, -32768, 32767)
    );
}

resonith_status preflight_budget(
    resonith_maf_operation_budget* budget,
    std::uint64_t required
) noexcept {
    if (budget == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (budget->remaining < required) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    return RESONITH_STATUS_OK;
}

void commit_budget(
    resonith_maf_operation_budget& budget,
    std::uint64_t used
) noexcept {
    budget.remaining -= used;
}

std::uint64_t splitmix64(std::uint64_t value) noexcept {
    value += 0x9e3779b97f4a7c15ULL;
    value = (value ^ (value >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    value = (value ^ (value >> 27U)) * 0x94d049bb133111ebULL;
    return value ^ (value >> 31U);
}

std::int16_t scale_q15(
    std::int16_t sample,
    std::int32_t gain_q15
) noexcept {
    return saturate_int16(
        round_shift_q15(
            static_cast<std::int64_t>(sample) * gain_q15
        )
    );
}

}  // namespace

extern "C" resonith_status resonith_maf_main_limits(
    resonith_maf_limits* limits
) {
    if (limits == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *limits = {
        384000U,
        RESONITH_MAF_MAIN_MAX_RENDER_FRAMES,
        RESONITH_MAF_MAIN_MAX_EMITTERS,
        RESONITH_MAF_MAIN_MAX_BASES,
        1U << 20U,
        1U << 16U,
        1U << 16U,
        RESONITH_MAF_MAIN_MAX_FILTERS,
        RESONITH_MAF_MAIN_MAX_STOCHASTIC_FIELDS,
        RESONITH_MAF_MAIN_MAX_TRANSIENTS,
        RESONITH_MAF_MAIN_MAX_CHANNELS,
        RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
        RESONITH_MAF_MAIN_MAX_PVQ_DIMENSION,
        RESONITH_MAF_MAIN_MAX_PVQ_PULSES,
        64ULL << 20U,
        32ULL << 20U,
        1ULL << 20U,
    };
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_resources_validate(
    const resonith_maf_limits* limits,
    const resonith_maf_resource_declaration* declaration,
    resonith_maf_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (limits == nullptr || declaration == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        declaration->sample_rate < 8000U
        || declaration->sample_rate > limits->maximum_sample_rate
        || declaration->render_frames == 0U
        || declaration->render_frames > limits->maximum_render_frames
        || declaration->output_channels == 0U
        || declaration->output_channels > limits->maximum_output_channels
        || declaration->emitter_count > limits->maximum_emitters
        || declaration->basis_count > limits->maximum_bases
        || declaration->basis_elements > limits->maximum_basis_elements
        || declaration->phase_knot_count > limits->maximum_phase_knots
        || declaration->gain_event_count > limits->maximum_gain_events
        || declaration->filter_count > limits->maximum_filters
        || declaration->maximum_filter_order
            > limits->maximum_filter_order
        || declaration->stochastic_field_count
            > limits->maximum_stochastic_fields
        || declaration->transient_count > limits->maximum_transients
        || declaration->maximum_pvq_dimension
            > limits->maximum_pvq_dimension
        || declaration->maximum_pvq_pulses
            > limits->maximum_pvq_pulses
        || declaration->persistent_bytes > limits->maximum_persistent_bytes
        || declaration->scratch_bytes > limits->maximum_scratch_bytes
        || declaration->operations_per_frame
            > limits->maximum_operations_per_frame
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        (declaration->basis_count == 0U)
            != (declaration->basis_elements == 0U)
        || (declaration->filter_count == 0U)
            != (declaration->maximum_filter_order == 0U)
        || declaration->maximum_pvq_pulses
            > declaration->maximum_pvq_dimension
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::uint64_t output_elements = 0U;
    std::uint64_t output_bytes = 0U;
    std::uint64_t operations_per_block = 0U;
    if (
        !checked_multiply(
            declaration->render_frames,
            declaration->output_channels,
            output_elements
        )
        || !checked_multiply(output_elements, 2U, output_bytes)
        || !checked_multiply(
            declaration->render_frames,
            declaration->operations_per_frame,
            operations_per_block
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    requirements->output_elements = output_elements;
    requirements->output_bytes = output_bytes;
    requirements->persistent_bytes = declaration->persistent_bytes;
    requirements->scratch_bytes = declaration->scratch_bytes;
    requirements->operations_per_block = operations_per_block;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_periodic_render(
    const std::int16_t* basis,
    std::size_t basis_count,
    const resonith_prepared_phase_trajectory* trajectory,
    std::uint32_t output_start,
    std::size_t output_count,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    std::uint64_t operations = 0U;
    if (!checked_multiply(output_count, 8U, operations)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    resonith_status status = preflight_budget(budget, operations);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_periodic_render(
        basis,
        basis_count,
        trajectory,
        output_start,
        output_count,
        output,
        output_capacity
    );
    if (status == RESONITH_STATUS_OK) {
        commit_budget(*budget, operations);
    }
    return status;
}

extern "C" resonith_status resonith_maf_compose_truth(
    const std::int16_t* unity_prediction,
    const std::int64_t* innovation_q,
    std::uint32_t innovation_step,
    const resonith_prepared_gain_law* gain_law,
    std::uint32_t output_start,
    std::size_t output_count,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    std::uint64_t operations = 0U;
    if (!checked_multiply(output_count, 8U, operations)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    resonith_status status = preflight_budget(budget, operations);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_compose_truth(
        unity_prediction,
        innovation_q,
        innovation_step,
        gain_law,
        output_start,
        output_count,
        output,
        output_capacity
    );
    if (status == RESONITH_STATUS_OK) {
        commit_budget(*budget, operations);
    }
    return status;
}

extern "C" resonith_status resonith_maf_noise_render(
    std::uint64_t stream_seed,
    std::uint32_t field_id,
    std::uint16_t channel_id,
    std::uint32_t absolute_start,
    std::int32_t gain_q15,
    std::size_t output_count,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        output_capacity < output_count
        || field_id >= RESONITH_MAF_MAIN_MAX_STOCHASTIC_FIELDS
        || channel_id >= RESONITH_MAF_MAIN_MAX_CHANNELS
        || !valid_gain(gain_q15)
        || output_count > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
        || output_count
            > std::numeric_limits<std::uint32_t>::max() - absolute_start
    ) {
        return output_capacity < output_count
            ? RESONITH_STATUS_OUTPUT_TOO_SMALL
            : RESONITH_STATUS_PROFILE_BOUND;
    }
    std::uint64_t operations = 0U;
    if (!checked_multiply(output_count, 12U, operations)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const resonith_status budget_status = preflight_budget(
        budget,
        operations
    );
    if (budget_status != RESONITH_STATUS_OK) {
        return budget_status;
    }

    const std::uint64_t identity = stream_seed
        ^ (static_cast<std::uint64_t>(field_id) << 32U)
        ^ (static_cast<std::uint64_t>(channel_id) << 56U);
    for (std::size_t index = 0U; index < output_count; ++index) {
        const std::uint64_t absolute =
            static_cast<std::uint64_t>(absolute_start) + index;
        const std::uint64_t random = splitmix64(
            identity ^ (absolute * 0xd1342543de82ef95ULL)
        );
        const std::uint16_t bits = static_cast<std::uint16_t>(random >> 48U);
        const std::int32_t signed_sample =
            static_cast<std::int32_t>(bits) - 32768;
        output[index] = scale_q15(
            static_cast<std::int16_t>(signed_sample),
            gain_q15
        );
    }
    commit_budget(*budget, operations);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_filter_prepare(
    const std::int16_t* reflection_q15,
    std::uint16_t order,
    std::int32_t* coefficients_q15,
    std::size_t coefficient_capacity,
    resonith_maf_filter* prepared
) {
    if (prepared == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *prepared = {};
    if (
        reflection_q15 == nullptr
        || coefficients_q15 == nullptr
        || order == 0U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        order > RESONITH_MAF_MAIN_MAX_FILTER_ORDER
        || coefficient_capacity < order
    ) {
        return coefficient_capacity < order
            ? RESONITH_STATUS_OUTPUT_TOO_SMALL
            : RESONITH_STATUS_PROFILE_BOUND;
    }

    std::array<std::int64_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> current{};
    std::array<std::int64_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> next{};
    for (std::uint16_t stage = 0U; stage < order; ++stage) {
        const std::int32_t reflection = reflection_q15[stage];
        if (
            reflection < -kMaximumReflectionQ15
            || reflection > kMaximumReflectionQ15
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        next.fill(0);
        for (std::uint16_t index = 0U; index < stage; ++index) {
            const std::uint16_t reverse = static_cast<std::uint16_t>(
                stage - 1U - index
            );
            next[index] = current[index] + round_shift_q15(
                static_cast<std::int64_t>(reflection) * current[reverse]
            );
            if (
                next[index] < -kMaximumLpcQ15
                || next[index] > kMaximumLpcQ15
            ) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
        }
        next[stage] = reflection;
        current = next;
    }
    for (std::uint16_t index = 0U; index < order; ++index) {
        coefficients_q15[index] =
            static_cast<std::int32_t>(current[index]);
    }
    prepared->coefficients_q15 = coefficients_q15;
    prepared->order = order;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_filter_render(
    const resonith_maf_filter* filter,
    const std::int16_t* excitation,
    std::size_t sample_count,
    std::int16_t* history,
    std::size_t history_capacity,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (
        filter == nullptr
        || filter->coefficients_q15 == nullptr
        || excitation == nullptr
        || history == nullptr
        || output == nullptr
        || filter->order == 0U
        || filter->reserved != 0U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        filter->order > RESONITH_MAF_MAIN_MAX_FILTER_ORDER
        || history_capacity < filter->order
        || output_capacity < sample_count
        || sample_count > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
    ) {
        if (history_capacity < filter->order) {
            return RESONITH_STATUS_SCRATCH_TOO_SMALL;
        }
        if (output_capacity < sample_count) {
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    for (std::uint16_t index = 0U; index < filter->order; ++index) {
        const std::int32_t coefficient = filter->coefficients_q15[index];
        if (
            coefficient < -kMaximumLpcQ15
            || coefficient > kMaximumLpcQ15
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    const std::uint64_t operations_per_sample =
        2U * filter->order + 4U;
    std::uint64_t operations = 0U;
    if (!checked_multiply(
            sample_count,
            operations_per_sample,
            operations
        )) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const resonith_status budget_status = preflight_budget(
        budget,
        operations
    );
    if (budget_status != RESONITH_STATUS_OK) {
        return budget_status;
    }

    for (std::size_t sample = 0U; sample < sample_count; ++sample) {
        std::int64_t accumulator = 0;
        for (std::uint16_t index = 0U; index < filter->order; ++index) {
            accumulator += static_cast<std::int64_t>(
                filter->coefficients_q15[index]
            ) * history[index];
        }
        const std::int16_t value = saturate_int16(
            static_cast<std::int64_t>(excitation[sample])
                - round_shift_q15(accumulator)
        );
        for (
            std::uint16_t index = filter->order - 1U;
            index > 0U;
            --index
        ) {
            history[index] = history[index - 1U];
        }
        history[0] = value;
        output[sample] = value;
    }
    commit_budget(*budget, operations);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_innovation_add(
    const std::int16_t* prediction,
    const std::int64_t* innovation_q,
    std::uint32_t innovation_step,
    std::size_t sample_count,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (
        prediction == nullptr
        || innovation_q == nullptr
        || output == nullptr
        || innovation_step == 0U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (
        sample_count > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
        || innovation_step > 65535U
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::uint64_t operations = 0U;
    if (!checked_multiply(sample_count, 4U, operations)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const resonith_status budget_status = preflight_budget(
        budget,
        operations
    );
    if (budget_status != RESONITH_STATUS_OK) {
        return budget_status;
    }

    const std::int64_t step = innovation_step;
    for (std::size_t index = 0U; index < sample_count; ++index) {
        const std::int64_t positive_limit =
            (32767 - prediction[index]) / step;
        const std::int64_t negative_limit =
            (-32768 - prediction[index]) / step;
        if (innovation_q[index] > positive_limit) {
            output[index] = 32767;
        } else if (innovation_q[index] < negative_limit) {
            output[index] = -32768;
        } else {
            output[index] = static_cast<std::int16_t>(
                prediction[index] + innovation_q[index] * step
            );
        }
    }
    commit_budget(*budget, operations);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_transients_add(
    const std::int16_t* base,
    std::uint32_t absolute_start,
    std::size_t sample_count,
    const resonith_maf_transient* transients,
    std::size_t transient_count,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (
        base == nullptr
        || output == nullptr
        || (transient_count != 0U && transients == nullptr)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (
        sample_count > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
        || transient_count > RESONITH_MAF_MAIN_MAX_TRANSIENTS
        || sample_count
            > std::numeric_limits<std::uint32_t>::max() - absolute_start
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    const std::uint64_t render_stop =
        static_cast<std::uint64_t>(absolute_start) + sample_count;
    std::uint64_t overlap_samples = 0U;
    for (std::size_t index = 0U; index < transient_count; ++index) {
        const resonith_maf_transient& transient = transients[index];
        if (
            transient.samples == nullptr
            || transient.sample_count == 0U
            || transient.sample_count
                > RESONITH_MAF_MAIN_MAX_TRANSIENT_SAMPLES
            || transient.reserved != 0U
            || !valid_gain(transient.gain_q15)
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        const std::uint64_t transient_stop =
            static_cast<std::uint64_t>(transient.onset)
            + transient.sample_count;
        const std::uint64_t overlap_start = std::max<std::uint64_t>(
            absolute_start,
            transient.onset
        );
        const std::uint64_t overlap_stop = std::min(
            render_stop,
            transient_stop
        );
        if (overlap_stop > overlap_start) {
            overlap_samples += overlap_stop - overlap_start;
        }
    }
    std::uint64_t transient_operations = 0U;
    if (
        !checked_multiply(overlap_samples, 5U, transient_operations)
        || transient_operations
            > std::numeric_limits<std::uint64_t>::max() - sample_count
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint64_t operations =
        transient_operations + sample_count;
    const resonith_status budget_status = preflight_budget(
        budget,
        operations
    );
    if (budget_status != RESONITH_STATUS_OK) {
        return budget_status;
    }

    std::copy(base, base + sample_count, output);
    for (std::size_t index = 0U; index < transient_count; ++index) {
        const resonith_maf_transient& transient = transients[index];
        const std::uint64_t transient_stop =
            static_cast<std::uint64_t>(transient.onset)
            + transient.sample_count;
        const std::uint64_t overlap_start = std::max<std::uint64_t>(
            absolute_start,
            transient.onset
        );
        const std::uint64_t overlap_stop = std::min(
            render_stop,
            transient_stop
        );
        for (
            std::uint64_t absolute = overlap_start;
            absolute < overlap_stop;
            ++absolute
        ) {
            const std::size_t output_index = static_cast<std::size_t>(
                absolute - absolute_start
            );
            const std::size_t transient_index = static_cast<std::size_t>(
                absolute - transient.onset
            );
            output[output_index] = saturate_int16(
                static_cast<std::int64_t>(output[output_index])
                + scale_q15(
                    transient.samples[transient_index],
                    transient.gain_q15
                )
            );
        }
    }
    commit_budget(*budget, operations);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_mix_q15(
    const std::int16_t* planar_sources,
    std::uint16_t source_count,
    std::size_t frame_count,
    const std::int16_t* matrix_q15,
    std::uint16_t output_channels,
    std::int16_t* interleaved_output,
    std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (
        planar_sources == nullptr
        || matrix_q15 == nullptr
        || interleaved_output == nullptr
        || source_count == 0U
        || output_channels == 0U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    std::uint64_t output_elements = 0U;
    if (
        source_count > RESONITH_MAF_MAIN_MAX_EMITTERS
        || output_channels > RESONITH_MAF_MAIN_MAX_CHANNELS
        || frame_count > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
        || !checked_multiply(frame_count, output_channels, output_elements)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (output_capacity < output_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    const std::uint64_t operations_per_output =
        2U * source_count + 2U;
    std::uint64_t operations = 0U;
    if (!checked_multiply(
            output_elements,
            operations_per_output,
            operations
        )) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const resonith_status budget_status = preflight_budget(
        budget,
        operations
    );
    if (budget_status != RESONITH_STATUS_OK) {
        return budget_status;
    }

    for (std::size_t frame = 0U; frame < frame_count; ++frame) {
        for (
            std::uint16_t channel = 0U;
            channel < output_channels;
            ++channel
        ) {
            std::int64_t accumulator = 0;
            for (
                std::uint16_t source = 0U;
                source < source_count;
                ++source
            ) {
                accumulator += static_cast<std::int64_t>(
                    matrix_q15[
                        static_cast<std::size_t>(channel) * source_count
                            + source
                    ]
                ) * planar_sources[
                    static_cast<std::size_t>(source) * frame_count + frame
                ];
            }
            interleaved_output[
                frame * output_channels + channel
            ] = saturate_int16(round_shift_q15(accumulator));
        }
    }
    commit_budget(*budget, operations);
    return RESONITH_STATUS_OK;
}
