#include "resonith/foundry_cuda.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace {

constexpr std::uint64_t q15_scale = 32768U;
constexpr std::int64_t gain_neighbour_radius = 8;
constexpr std::uint64_t direction_count = 2U;
constexpr std::uint64_t rolling_hash_base = 0x9E3779B185EBCA87ULL;

struct partial_edge_cuda_input {
    std::uint64_t candidate_id;
    std::uint64_t source_observation_id;
    std::uint64_t target_observation_id;
    std::uint64_t center_delta_samples;
    std::int64_t source_frequency_hz_q20;
    std::int64_t target_frequency_hz_q20;
    std::uint64_t source_frequency_uncertainty_hz_q20;
    std::uint64_t target_frequency_uncertainty_hz_q20;
    std::uint32_t source_phase_turn_u32;
    std::uint32_t target_phase_turn_u32;
    std::uint32_t source_phase_step_u32;
    std::uint32_t target_phase_step_u32;
    std::uint32_t source_amplitude_q16;
    std::uint32_t target_amplitude_q16;
    std::uint32_t source_phase_uncertainty_u31;
    std::uint32_t target_phase_uncertainty_u31;
    std::uint32_t gap_hops;
    std::int32_t cycle_offset;
    std::uint32_t phase_usable;
    std::uint32_t reserved;
};

struct partial_edge_cuda_score {
    std::uint64_t candidate_id;
    std::uint32_t phase_error_u31;
    std::int32_t continuity_cost_q8;
    std::int32_t provisional_program_cost_q8;
    std::uint32_t flags;
};

static_assert(sizeof(partial_edge_cuda_input) == 112U);
static_assert(sizeof(partial_edge_cuda_score) == 24U);

bool multiply_fits(
    std::uint64_t left,
    std::uint64_t right,
    std::uint64_t* product
) noexcept {
    if (
        right != 0U
        && left > std::numeric_limits<std::uint64_t>::max() / right
    ) {
        return false;
    }
    *product = left * right;
    return true;
}

resonith_foundry_status validate_range(
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range& range,
    std::size_t output_capacity,
    std::uint64_t* total_candidates
) noexcept {
    if (range.block_count < 2U || range.block_samples == 0U) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t required_elements = 0U;
    if (
        !multiply_fits(
            range.block_count,
            range.block_samples,
            &required_elements
        )
        || required_elements != block_element_count
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t pair_count = 0U;
    if (
        !multiply_fits(
            range.block_count,
            range.block_count - 1U,
            &pair_count
        )
        || !multiply_fits(pair_count, range.block_samples, total_candidates)
        || !multiply_fits(
            *total_candidates,
            direction_count,
            total_candidates
        )
    ) {
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    if (
        range.first_candidate > *total_candidates
        || range.candidate_count == 0U
        || range.candidate_count
            > *total_candidates - range.first_candidate
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    if (range.candidate_count > output_capacity) {
        return RESONITH_FOUNDRY_OUTPUT_TOO_SMALL;
    }
    return RESONITH_FOUNDRY_OK;
}

std::int64_t round_divide_away(
    std::int64_t numerator,
    std::int64_t denominator
) noexcept {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

std::int64_t round_q15(std::int64_t product) noexcept {
    return round_divide_away(product, static_cast<std::int64_t>(q15_scale));
}

std::int64_t interpolated_gain(
    std::int64_t start,
    std::int64_t end,
    std::uint64_t sample,
    std::uint64_t count
) noexcept {
    if (count <= 1U) {
        return start;
    }
    return start + round_divide_away(
        (end - start) * static_cast<std::int64_t>(sample),
        static_cast<std::int64_t>(count - 1U)
    );
}

resonith_foundry_gain_phase_result evaluate_candidate(
    const std::int16_t* blocks,
    const resonith_foundry_gain_phase_range& range,
    std::uint64_t candidate_id
) noexcept {
    const bool reverse = candidate_id % direction_count != 0U;
    const std::uint64_t direction_id = candidate_id / direction_count;
    const std::uint64_t offset =
        direction_id % range.block_samples;
    const std::uint64_t pair_id =
        direction_id / range.block_samples;
    const std::uint64_t basis_index =
        pair_id / (range.block_count - 1U);
    const std::uint64_t target_slot =
        pair_id % (range.block_count - 1U);
    const std::uint64_t target_index =
        target_slot >= basis_index ? target_slot + 1U : target_slot;
    const std::int16_t* const basis =
        blocks + basis_index * range.block_samples;
    const std::int16_t* const target =
        blocks + target_index * range.block_samples;

    std::int64_t basis_energy = 0;
    std::int64_t target_energy = 0;
    std::int64_t correlation = 0;
    for (
        std::uint64_t sample = 0U;
        sample < range.block_samples;
        ++sample
    ) {
        const std::uint64_t source_index = reverse
            ? (
                offset + range.block_samples
                - sample % range.block_samples
            ) % range.block_samples
            : (sample + offset) % range.block_samples;
        const std::int64_t left = basis[source_index];
        const std::int64_t right = target[sample];
        basis_energy += left * left;
        target_energy += right * right;
        correlation += left * right;
    }

    std::int64_t fitted_gain = 0;
    if (basis_energy != 0) {
        fitted_gain = round_divide_away(
            correlation * static_cast<std::int64_t>(q15_scale),
            basis_energy
        );
        fitted_gain = std::clamp<std::int64_t>(
            fitted_gain,
            -static_cast<std::int64_t>(q15_scale),
            static_cast<std::int64_t>(q15_scale)
        );
    }

    std::int64_t gain = fitted_gain;
    std::int64_t end_gain = 0;
    std::uint32_t transform_flags = reverse
        ? static_cast<std::uint32_t>(RESONITH_FOUNDRY_TRANSFORM_REVERSE)
        : 0U;
    std::uint64_t squared_error = std::numeric_limits<std::uint64_t>::max();
    const std::int64_t first_gain = std::max<std::int64_t>(
        -static_cast<std::int64_t>(q15_scale),
        fitted_gain - gain_neighbour_radius
    );
    const std::int64_t final_gain = std::min<std::int64_t>(
        static_cast<std::int64_t>(q15_scale),
        fitted_gain + gain_neighbour_radius
    );
    for (
        std::int64_t candidate_gain = first_gain;
        candidate_gain <= final_gain;
        ++candidate_gain
    ) {
        std::uint64_t candidate_error = 0U;
        for (
            std::uint64_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const std::uint64_t source_index = reverse
                ? (
                    offset + range.block_samples
                    - sample % range.block_samples
                ) % range.block_samples
                : (sample + offset) % range.block_samples;
            const std::int64_t predicted = round_q15(
                static_cast<std::int64_t>(basis[source_index])
                    * candidate_gain
            );
            const std::int64_t difference =
                static_cast<std::int64_t>(target[sample]) - predicted;
            candidate_error += static_cast<std::uint64_t>(
                difference * difference
            );
        }
        if (
            candidate_error < squared_error
            || (
                candidate_error == squared_error
                && (
                    std::abs(candidate_gain) < std::abs(gain)
                    || (
                        std::abs(candidate_gain) == std::abs(gain)
                        && candidate_gain < gain
                    )
                )
            )
        ) {
            gain = candidate_gain;
            end_gain = 0;
            transform_flags = reverse
                ? static_cast<std::uint32_t>(
                      RESONITH_FOUNDRY_TRANSFORM_REVERSE
                  )
                : 0U;
            squared_error = candidate_error;
        }
    }

    if (range.block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator =
            static_cast<double>(range.block_samples - 1U);
        for (
            std::uint64_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const double position =
                static_cast<double>(sample) / denominator;
            const std::uint64_t source_index = reverse
                ? (
                    offset + range.block_samples
                    - sample % range.block_samples
                ) % range.block_samples
                : (sample + offset) % range.block_samples;
            const double aligned =
                static_cast<double>(basis[source_index]);
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double scaled_target =
                static_cast<double>(target[sample])
                * static_cast<double>(q15_scale);
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * scaled_target;
            by += second * scaled_target;
        }
        const double determinant = aa * bb - ab * ab;
        if (determinant > std::max(1.0, aa * bb) * 1.0e-12) {
            const auto fitted_start = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (ay * bb - by * ab) / determinant
                    + ((ay * bb - by * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -static_cast<std::int64_t>(q15_scale),
                static_cast<std::int64_t>(q15_scale)
            );
            const auto fitted_end = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (by * aa - ay * ab) / determinant
                    + ((by * aa - ay * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -static_cast<std::int64_t>(q15_scale),
                static_cast<std::int64_t>(q15_scale)
            );
            const std::int64_t first_start = std::max<std::int64_t>(
                -static_cast<std::int64_t>(q15_scale),
                fitted_start - gain_neighbour_radius
            );
            const std::int64_t final_start = std::min<std::int64_t>(
                static_cast<std::int64_t>(q15_scale),
                fitted_start + gain_neighbour_radius
            );
            const std::int64_t first_end = std::max<std::int64_t>(
                -static_cast<std::int64_t>(q15_scale),
                fitted_end - gain_neighbour_radius
            );
            const std::int64_t final_end = std::min<std::int64_t>(
                static_cast<std::int64_t>(q15_scale),
                fitted_end + gain_neighbour_radius
            );
            for (
                std::int64_t candidate_start = first_start;
                candidate_start <= final_start;
                ++candidate_start
            ) {
                for (
                    std::int64_t candidate_end = first_end;
                    candidate_end <= final_end;
                    ++candidate_end
                ) {
                    std::uint64_t candidate_error = 0U;
                    for (
                        std::uint64_t sample = 0U;
                        sample < range.block_samples;
                        ++sample
                    ) {
                        const std::int64_t current_gain =
                            interpolated_gain(
                                candidate_start,
                                candidate_end,
                                sample,
                                range.block_samples
                            );
                        const std::uint64_t source_index = reverse
                            ? (
                                offset + range.block_samples
                                - sample % range.block_samples
                            ) % range.block_samples
                            : (sample + offset) % range.block_samples;
                        const std::int64_t predicted = round_q15(
                            static_cast<std::int64_t>(
                                basis[source_index]
                            ) * current_gain
                        );
                        const std::int64_t difference =
                            static_cast<std::int64_t>(target[sample])
                            - predicted;
                        candidate_error += static_cast<std::uint64_t>(
                            difference * difference
                        );
                    }
                    if (candidate_error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        transform_flags =
                            RESONITH_FOUNDRY_TRANSFORM_LINEAR_GAIN
                            | (
                                reverse
                                    ? static_cast<std::uint32_t>(
                                          RESONITH_FOUNDRY_TRANSFORM_REVERSE
                                      )
                                    : 0U
                            );
                        squared_error = candidate_error;
                    }
                }
            }
        }
    }
    return {
        static_cast<std::uint32_t>(basis_index),
        static_cast<std::uint32_t>(target_index),
        static_cast<std::uint32_t>(offset),
        static_cast<std::int32_t>(gain),
        static_cast<std::int32_t>(end_gain),
        transform_flags,
        squared_error,
        static_cast<std::uint64_t>(target_energy),
    };
}

bool warp_candidate_count(
    const resonith_foundry_warp_range& range,
    std::uint64_t* candidate_count
) noexcept {
    if (
        range.block_count < 2U
        || range.block_samples < 3U
        || range.block_samples > 32767U
        || range.phase_subsamples == 0U
        || 65536U % range.phase_subsamples != 0U
        || range.step_increment_q16 == 0U
    ) {
        return false;
    }
    const std::uint64_t minimum_step_delta =
        static_cast<std::uint64_t>(range.step_radius)
        * range.step_increment_q16;
    const std::uint64_t maximum_step_delta =
        static_cast<std::uint64_t>(
            range.step_radius + range.end_step_radius
        ) * range.step_increment_q16;
    if (
        minimum_step_delta >= 65536U
        || 65536U + maximum_step_delta > 8U * 65536U
    ) {
        return false;
    }
    std::uint64_t count = 0U;
    if (
        !multiply_fits(range.block_count, range.block_count - 1U, &count)
        || !multiply_fits(count, range.block_samples, &count)
        || !multiply_fits(count, range.phase_subsamples, &count)
        || !multiply_fits(count, direction_count, &count)
        || !multiply_fits(count, 2U * range.step_radius + 1U, &count)
        || !multiply_fits(
            count,
            2U * range.end_step_radius + 1U,
            &count
        )
    ) {
        return false;
    }
    *candidate_count = count;
    return true;
}

resonith_foundry_status validate_warp_range(
    std::size_t block_element_count,
    const resonith_foundry_warp_range& range,
    std::size_t output_capacity,
    std::uint64_t* total_candidates
) noexcept {
    std::uint64_t required_elements = 0U;
    if (
        !warp_candidate_count(range, total_candidates)
        || !multiply_fits(
            range.block_count,
            range.block_samples,
            &required_elements
        )
        || required_elements != block_element_count
        || range.first_candidate > *total_candidates
        || range.candidate_count == 0U
        || range.candidate_count
            > *total_candidates - range.first_candidate
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    return range.candidate_count <= output_capacity
        ? RESONITH_FOUNDRY_OK
        : RESONITH_FOUNDRY_OUTPUT_TOO_SMALL;
}

std::int64_t warp_position_q16(
    std::int32_t start_position,
    std::int32_t start_step,
    std::int32_t end_step,
    bool linear_step,
    std::uint32_t sample,
    std::uint32_t count
) noexcept {
    std::int64_t position =
        static_cast<std::int64_t>(start_position)
        + static_cast<std::int64_t>(start_step) * sample;
    if (!linear_step || sample < 2U) {
        return position;
    }
    return position + round_divide_away(
        static_cast<std::int64_t>(end_step - start_step)
            * sample * (sample - 1U),
        2LL * static_cast<std::int64_t>(count - 2U)
    );
}

std::int64_t warp_basis_value(
    const std::int16_t* basis,
    std::uint32_t basis_samples,
    std::int64_t position_q16
) noexcept {
    const std::int64_t period =
        static_cast<std::int64_t>(basis_samples) * 65536LL;
    std::int64_t wrapped = position_q16 % period;
    if (wrapped < 0) {
        wrapped += period;
    }
    const std::uint32_t left =
        static_cast<std::uint32_t>(wrapped / 65536LL);
    const std::uint32_t fraction =
        static_cast<std::uint32_t>(wrapped % 65536LL);
    if (fraction == 0U) {
        return basis[left];
    }
    const std::uint32_t right = (left + 1U) % basis_samples;
    return round_divide_away(
        static_cast<std::int64_t>(basis[left]) * (65536U - fraction)
            + static_cast<std::int64_t>(basis[right]) * fraction,
        65536LL
    );
}

resonith_foundry_warp_result evaluate_warp_candidate(
    const std::int16_t* blocks,
    const resonith_foundry_warp_range& range,
    std::uint64_t candidate_id
) noexcept {
    const std::uint64_t end_choice_count =
        2U * range.end_step_radius + 1U;
    const std::uint64_t end_choice =
        candidate_id % end_choice_count;
    candidate_id /= end_choice_count;
    const std::uint64_t step_choice_count =
        2U * range.step_radius + 1U;
    const std::uint64_t step_choice =
        candidate_id % step_choice_count;
    candidate_id /= step_choice_count;
    const bool reverse = candidate_id % direction_count != 0U;
    candidate_id /= direction_count;
    const std::uint64_t phase_count =
        static_cast<std::uint64_t>(range.block_samples)
        * range.phase_subsamples;
    const std::uint64_t phase_choice = candidate_id % phase_count;
    const std::uint64_t pair_id = candidate_id / phase_count;
    const std::uint64_t basis_index =
        pair_id / (range.block_count - 1U);
    const std::uint64_t target_slot =
        pair_id % (range.block_count - 1U);
    const std::uint64_t target_index =
        target_slot >= basis_index ? target_slot + 1U : target_slot;
    const std::int32_t direction = reverse ? -1 : 1;
    const std::int32_t source_position = static_cast<std::int32_t>(
        phase_choice * 65536U / range.phase_subsamples
    );
    const std::int32_t start_magnitude = static_cast<std::int32_t>(
        65536LL
        + (
            static_cast<std::int64_t>(step_choice)
            - range.step_radius
        ) * range.step_increment_q16
    );
    const std::int32_t end_delta = static_cast<std::int32_t>(
        (
            static_cast<std::int64_t>(end_choice)
            - range.end_step_radius
        ) * range.step_increment_q16
    );
    const bool linear_step = end_delta != 0;
    const std::int32_t start_step = direction * start_magnitude;
    const std::int32_t end_step = linear_step
        ? direction * (start_magnitude + end_delta)
        : 0;
    const auto* basis =
        blocks + basis_index * range.block_samples;
    const auto* target =
        blocks + target_index * range.block_samples;

    std::int64_t basis_energy = 0;
    std::int64_t target_energy = 0;
    std::int64_t correlation = 0;
    for (std::uint32_t sample = 0U; sample < range.block_samples; ++sample) {
        const std::int64_t aligned = warp_basis_value(
            basis,
            range.block_samples,
            warp_position_q16(
                source_position,
                start_step,
                linear_step ? end_step : start_step,
                linear_step,
                sample,
                range.block_samples
            )
        );
        const std::int64_t desired = target[sample];
        basis_energy += aligned * aligned;
        target_energy += desired * desired;
        correlation += aligned * desired;
    }
    std::int64_t fitted_gain = basis_energy == 0
        ? 0
        : round_divide_away(correlation * 32768LL, basis_energy);
    fitted_gain = std::clamp<std::int64_t>(fitted_gain, -32768, 32768);
    std::int64_t gain = fitted_gain;
    std::int64_t end_gain = 0;
    std::uint32_t flags = linear_step
        ? RESONITH_FOUNDRY_WARP_LINEAR_STEP
        : 0U;
    std::uint64_t squared_error = std::numeric_limits<std::uint64_t>::max();
    for (
        std::int64_t candidate_gain =
            std::max<std::int64_t>(-32768, fitted_gain - 2);
        candidate_gain <= std::min<std::int64_t>(32768, fitted_gain + 2);
        ++candidate_gain
    ) {
        std::uint64_t error = 0U;
        for (
            std::uint32_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const std::int64_t aligned = warp_basis_value(
                basis,
                range.block_samples,
                warp_position_q16(
                    source_position,
                    start_step,
                    linear_step ? end_step : start_step,
                    linear_step,
                    sample,
                    range.block_samples
                )
            );
            const std::int64_t predicted = round_q15(
                aligned * candidate_gain
            );
            const std::int64_t difference =
                static_cast<std::int64_t>(target[sample]) - predicted;
            error += static_cast<std::uint64_t>(difference * difference);
        }
        if (error < squared_error) {
            gain = candidate_gain;
            end_gain = 0;
            flags = linear_step
                ? RESONITH_FOUNDRY_WARP_LINEAR_STEP
                : 0U;
            squared_error = error;
        }
    }

    if (range.block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator =
            static_cast<double>(range.block_samples - 1U);
        for (
            std::uint32_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const double position = static_cast<double>(sample) / denominator;
            const double aligned = static_cast<double>(warp_basis_value(
                basis,
                range.block_samples,
                warp_position_q16(
                    source_position,
                    start_step,
                    linear_step ? end_step : start_step,
                    linear_step,
                    sample,
                    range.block_samples
                )
            ));
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double desired =
                static_cast<double>(target[sample]) * 32768.0;
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * desired;
            by += second * desired;
        }
        const double determinant = aa * bb - ab * ab;
        if (determinant > std::max(1.0, aa * bb) * 1.0e-12) {
            const std::int64_t fitted_start = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (ay * bb - by * ab) / determinant
                    + ((ay * bb - by * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -32768,
                32768
            );
            const std::int64_t fitted_end = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (by * aa - ay * ab) / determinant
                    + ((by * aa - ay * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -32768,
                32768
            );
            for (
                std::int64_t candidate_start =
                    std::max<std::int64_t>(-32768, fitted_start - 1);
                candidate_start
                    <= std::min<std::int64_t>(32768, fitted_start + 1);
                ++candidate_start
            ) {
                for (
                    std::int64_t candidate_end =
                        std::max<std::int64_t>(-32768, fitted_end - 1);
                    candidate_end
                        <= std::min<std::int64_t>(32768, fitted_end + 1);
                    ++candidate_end
                ) {
                    std::uint64_t error = 0U;
                    for (
                        std::uint32_t sample = 0U;
                        sample < range.block_samples;
                        ++sample
                    ) {
                        const std::int64_t aligned = warp_basis_value(
                            basis,
                            range.block_samples,
                            warp_position_q16(
                                source_position,
                                start_step,
                                linear_step ? end_step : start_step,
                                linear_step,
                                sample,
                                range.block_samples
                            )
                        );
                        const std::int64_t current_gain = interpolated_gain(
                            candidate_start,
                            candidate_end,
                            sample,
                            range.block_samples
                        );
                        const std::int64_t predicted =
                            round_q15(aligned * current_gain);
                        const std::int64_t difference =
                            static_cast<std::int64_t>(target[sample])
                            - predicted;
                        error += static_cast<std::uint64_t>(
                            difference * difference
                        );
                    }
                    if (error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        flags = RESONITH_FOUNDRY_WARP_LINEAR_GAIN
                            | (
                                linear_step
                                    ? RESONITH_FOUNDRY_WARP_LINEAR_STEP
                                    : 0U
                            );
                        squared_error = error;
                    }
                }
            }
        }
    }
    return {
        static_cast<std::uint32_t>(basis_index),
        static_cast<std::uint32_t>(target_index),
        source_position,
        start_step,
        end_step,
        static_cast<std::int32_t>(gain),
        static_cast<std::int32_t>(end_gain),
        flags,
        squared_error,
        static_cast<std::uint64_t>(target_energy),
    };
}

void copy_error(
    const std::string& message,
    char* error,
    std::size_t error_capacity
) noexcept {
    if (error == nullptr || error_capacity == 0U) {
        return;
    }
    const std::size_t count = std::min(
        message.size(),
        error_capacity - 1U
    );
    std::memcpy(error, message.data(), count);
    error[count] = '\0';
}

#if defined(_WIN32)

using nvrtc_program = void*;
using nvrtc_result = int;
using cuda_result = int;
using cuda_device = int;
using cuda_context = void*;
using cuda_module = void*;
using cuda_function = void*;
using cuda_stream = void*;
using cuda_device_ptr = std::uint64_t;

constexpr nvrtc_result nvrtc_success = 0;
constexpr cuda_result cuda_success = 0;

struct nvrtc_api {
    HMODULE library = nullptr;
    HMODULE builtins = nullptr;
    nvrtc_result (*version)(int*, int*) = nullptr;
    nvrtc_result (*create_program)(
        nvrtc_program*,
        const char*,
        const char*,
        int,
        const char* const*,
        const char* const*
    ) = nullptr;
    nvrtc_result (*compile_program)(
        nvrtc_program,
        int,
        const char* const*
    ) = nullptr;
    nvrtc_result (*log_size)(nvrtc_program, std::size_t*) = nullptr;
    nvrtc_result (*get_log)(nvrtc_program, char*) = nullptr;
    nvrtc_result (*cubin_size)(nvrtc_program, std::size_t*) = nullptr;
    nvrtc_result (*get_cubin)(nvrtc_program, char*) = nullptr;
    nvrtc_result (*destroy_program)(nvrtc_program*) = nullptr;

    ~nvrtc_api() {
        if (library != nullptr) {
            FreeLibrary(library);
        }
        if (builtins != nullptr) {
            FreeLibrary(builtins);
        }
    }
};

struct cuda_api {
    HMODULE library = nullptr;
    cuda_result (__stdcall *init)(unsigned int) = nullptr;
    cuda_result (__stdcall *device_get)(cuda_device*, int) = nullptr;
    cuda_result (__stdcall *device_name)(char*, int, cuda_device) = nullptr;
    cuda_result (__stdcall *device_compute_capability)(
        int*,
        int*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *device_total_memory)(
        std::size_t*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *primary_context_retain)(
        cuda_context*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *primary_context_release)(cuda_device) = nullptr;
    cuda_result (__stdcall *context_set_current)(cuda_context) = nullptr;
    cuda_result (__stdcall *memory_allocate)(
        cuda_device_ptr*,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *memory_free)(cuda_device_ptr) = nullptr;
    cuda_result (__stdcall *copy_host_to_device)(
        cuda_device_ptr,
        const void*,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *copy_device_to_host)(
        void*,
        cuda_device_ptr,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *module_load_data)(
        cuda_module*,
        const void*
    ) = nullptr;
    cuda_result (__stdcall *module_get_function)(
        cuda_function*,
        cuda_module,
        const char*
    ) = nullptr;
    cuda_result (__stdcall *launch_kernel)(
        cuda_function,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        cuda_stream,
        void**,
        void**
    ) = nullptr;
    cuda_result (__stdcall *context_synchronize)() = nullptr;
    cuda_result (__stdcall *module_unload)(cuda_module) = nullptr;

    ~cuda_api() {
        if (library != nullptr) {
            FreeLibrary(library);
        }
    }
};

template <typename function_type>
bool load_symbol(
    HMODULE library,
    const char* name,
    function_type* function
) noexcept {
    const FARPROC address = GetProcAddress(library, name);
    if (address == nullptr) {
        *function = nullptr;
        return false;
    }
    static_assert(sizeof(address) == sizeof(*function));
    std::memcpy(function, &address, sizeof(address));
    return true;
}

std::wstring widen_ascii(const std::string& text) {
    return std::wstring(text.begin(), text.end());
}

std::wstring library_path(
    const char* directory,
    const wchar_t* library_name
) {
    if (directory == nullptr || directory[0] == '\0') {
        return library_name;
    }
    std::wstring result = widen_ascii(directory);
    if (!result.empty() && result.back() != L'\\' && result.back() != L'/') {
        result.push_back(L'\\');
    }
    result.append(library_name);
    return result;
}

bool load_nvrtc(
    const char* directory,
    nvrtc_api* api,
    std::string* error
) {
    std::vector<wchar_t> previous_directory;
    if (directory != nullptr && directory[0] != '\0') {
        const DWORD previous_length = GetDllDirectoryW(0U, nullptr);
        previous_directory.resize(
            std::max<DWORD>(1U, previous_length + 1U),
            L'\0'
        );
        if (previous_length != 0U) {
            GetDllDirectoryW(
                static_cast<DWORD>(previous_directory.size()),
                previous_directory.data()
            );
        }
        const std::wstring wide_directory = widen_ascii(directory);
        SetDllDirectoryW(wide_directory.c_str());
    }
    api->builtins = LoadLibraryW(
        library_path(
            directory,
            L"nvrtc-builtins64_133.dll"
        ).c_str()
    );
    api->library = LoadLibraryW(
        library_path(directory, L"nvrtc64_130_0.dll").c_str()
    );
    if (directory != nullptr && directory[0] != '\0') {
        SetDllDirectoryW(
            previous_directory.empty() || previous_directory[0] == L'\0'
                ? nullptr
                : previous_directory.data()
        );
    }
    if (api->library == nullptr || api->builtins == nullptr) {
        *error = "cannot load NVIDIA NVRTC 13 and its builtins";
        return false;
    }
    const bool complete =
        load_symbol(api->library, "nvrtcVersion", &api->version)
        && load_symbol(
            api->library,
            "nvrtcCreateProgram",
            &api->create_program
        )
        && load_symbol(
            api->library,
            "nvrtcCompileProgram",
            &api->compile_program
        )
        && load_symbol(
            api->library,
            "nvrtcGetProgramLogSize",
            &api->log_size
        )
        && load_symbol(
            api->library,
            "nvrtcGetProgramLog",
            &api->get_log
        )
        && load_symbol(
            api->library,
            "nvrtcGetCUBINSize",
            &api->cubin_size
        )
        && load_symbol(api->library, "nvrtcGetCUBIN", &api->get_cubin)
        && load_symbol(
            api->library,
            "nvrtcDestroyProgram",
            &api->destroy_program
        );
    if (!complete) {
        *error = "NVRTC library is missing a required symbol";
    }
    return complete;
}

bool load_cuda(cuda_api* api, std::string* error) {
    api->library = LoadLibraryW(L"nvcuda.dll");
    if (api->library == nullptr) {
        *error = "cannot load the NVIDIA CUDA driver";
        return false;
    }
    const bool complete =
        load_symbol(api->library, "cuInit", &api->init)
        && load_symbol(api->library, "cuDeviceGet", &api->device_get)
        && load_symbol(
            api->library,
            "cuDeviceGetName",
            &api->device_name
        )
        && load_symbol(
            api->library,
            "cuDeviceComputeCapability",
            &api->device_compute_capability
        )
        && load_symbol(
            api->library,
            "cuDeviceTotalMem_v2",
            &api->device_total_memory
        )
        && load_symbol(
            api->library,
            "cuDevicePrimaryCtxRetain",
            &api->primary_context_retain
        )
        && load_symbol(
            api->library,
            "cuDevicePrimaryCtxRelease_v2",
            &api->primary_context_release
        )
        && load_symbol(
            api->library,
            "cuCtxSetCurrent",
            &api->context_set_current
        )
        && load_symbol(
            api->library,
            "cuMemAlloc_v2",
            &api->memory_allocate
        )
        && load_symbol(
            api->library,
            "cuMemFree_v2",
            &api->memory_free
        )
        && load_symbol(
            api->library,
            "cuMemcpyHtoD_v2",
            &api->copy_host_to_device
        )
        && load_symbol(
            api->library,
            "cuMemcpyDtoH_v2",
            &api->copy_device_to_host
        )
        && load_symbol(
            api->library,
            "cuModuleLoadData",
            &api->module_load_data
        )
        && load_symbol(
            api->library,
            "cuModuleGetFunction",
            &api->module_get_function
        )
        && load_symbol(
            api->library,
            "cuLaunchKernel",
            &api->launch_kernel
        )
        && load_symbol(
            api->library,
            "cuCtxSynchronize",
            &api->context_synchronize
        )
        && load_symbol(
            api->library,
            "cuModuleUnload",
            &api->module_unload
        );
    if (!complete) {
        *error = "CUDA driver is missing a required symbol";
    }
    return complete;
}

constexpr char gain_phase_kernel[] = R"cuda(
struct Result {
    unsigned int basis_index;
    unsigned int target_index;
    unsigned int source_offset;
    int gain_q15;
    int end_gain_q15;
    unsigned int transform_flags;
    unsigned long long squared_error;
    unsigned long long target_energy;
};

__device__ long long round_divide_away(
    long long numerator,
    long long denominator
) {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

__device__ long long interpolated_gain(
    long long start,
    long long end,
    unsigned int sample,
    unsigned int count
) {
    if (count <= 1U) {
        return start;
    }
    return start + round_divide_away(
        (end - start) * (long long)sample,
        (long long)(count - 1U)
    );
}

extern "C" __global__ void exhaustive_gain_phase(
    const short* blocks,
    unsigned int block_count,
    unsigned int block_samples,
    unsigned long long first_candidate,
    unsigned long long candidate_count,
    Result* output
) {
    const unsigned long long local =
        (unsigned long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (local >= candidate_count) {
        return;
    }
    const unsigned long long candidate = first_candidate + local;
    const bool reverse = candidate % 2ULL != 0ULL;
    const unsigned long long direction = candidate / 2ULL;
    const unsigned long long offset = direction % block_samples;
    const unsigned long long pair = direction / block_samples;
    const unsigned long long basis_index = pair / (block_count - 1U);
    const unsigned long long target_slot = pair % (block_count - 1U);
    const unsigned long long target_index =
        target_slot >= basis_index ? target_slot + 1U : target_slot;
    const short* basis = blocks + basis_index * block_samples;
    const short* target = blocks + target_index * block_samples;

    long long basis_energy = 0;
    long long target_energy = 0;
    long long correlation = 0;
    for (unsigned int sample = 0; sample < block_samples; ++sample) {
        const unsigned long long source_index = reverse
            ? (
                offset + block_samples
                - sample % block_samples
            ) % block_samples
            : (sample + offset) % block_samples;
        const long long left = basis[source_index];
        const long long right = target[sample];
        basis_energy += left * left;
        target_energy += right * right;
        correlation += left * right;
    }

    long long fitted_gain = 0;
    if (basis_energy != 0) {
        fitted_gain = round_divide_away(
            correlation * 32768LL,
            basis_energy
        );
        fitted_gain = fitted_gain < -32768LL ? -32768LL : fitted_gain;
        fitted_gain = fitted_gain > 32768LL ? 32768LL : fitted_gain;
    }

    long long gain = fitted_gain;
    long long end_gain = 0;
    unsigned int transform_flags = reverse ? 2U : 0U;
    unsigned long long squared_error = ~0ULL;
    long long first_gain = fitted_gain - 8LL;
    long long final_gain = fitted_gain + 8LL;
    first_gain = first_gain < -32768LL ? -32768LL : first_gain;
    final_gain = final_gain > 32768LL ? 32768LL : final_gain;
    for (
        long long candidate_gain = first_gain;
        candidate_gain <= final_gain;
        ++candidate_gain
    ) {
        unsigned long long candidate_error = 0;
        for (unsigned int sample = 0; sample < block_samples; ++sample) {
            const unsigned long long source_index = reverse
                ? (
                    offset + block_samples
                    - sample % block_samples
                ) % block_samples
                : (sample + offset) % block_samples;
            const long long product =
                (long long)basis[source_index] * candidate_gain;
            const long long predicted =
                round_divide_away(product, 32768LL);
            const long long difference =
                (long long)target[sample] - predicted;
            candidate_error +=
                (unsigned long long)(difference * difference);
        }
        const long long candidate_abs =
            candidate_gain < 0 ? -candidate_gain : candidate_gain;
        const long long best_abs = gain < 0 ? -gain : gain;
        if (
            candidate_error < squared_error
            || (
                candidate_error == squared_error
                && (
                    candidate_abs < best_abs
                    || (
                        candidate_abs == best_abs
                        && candidate_gain < gain
                    )
                )
            )
        ) {
            gain = candidate_gain;
            end_gain = 0;
            transform_flags = reverse ? 2U : 0U;
            squared_error = candidate_error;
        }
    }

    if (block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator = (double)(block_samples - 1U);
        for (unsigned int sample = 0; sample < block_samples; ++sample) {
            const double position = (double)sample / denominator;
            const unsigned long long source_index = reverse
                ? (
                    offset + block_samples
                    - sample % block_samples
                ) % block_samples
                : (sample + offset) % block_samples;
            const double aligned = (double)basis[source_index];
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double scaled_target = (double)target[sample] * 32768.0;
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * scaled_target;
            by += second * scaled_target;
        }
        const double determinant = aa * bb - ab * ab;
        const double determinant_floor =
            (aa * bb > 1.0 ? aa * bb : 1.0) * 1.0e-12;
        if (determinant > determinant_floor) {
            const double raw_start = (ay * bb - by * ab) / determinant;
            const double raw_end = (by * aa - ay * ab) / determinant;
            long long fitted_start = (long long)(
                raw_start + (raw_start >= 0.0 ? 0.5 : -0.5)
            );
            long long fitted_end = (long long)(
                raw_end + (raw_end >= 0.0 ? 0.5 : -0.5)
            );
            fitted_start =
                fitted_start < -32768LL ? -32768LL : fitted_start;
            fitted_start =
                fitted_start > 32768LL ? 32768LL : fitted_start;
            fitted_end = fitted_end < -32768LL ? -32768LL : fitted_end;
            fitted_end = fitted_end > 32768LL ? 32768LL : fitted_end;
            long long first_start = fitted_start - 8LL;
            long long final_start = fitted_start + 8LL;
            long long first_end = fitted_end - 8LL;
            long long final_end = fitted_end + 8LL;
            first_start = first_start < -32768LL ? -32768LL : first_start;
            final_start = final_start > 32768LL ? 32768LL : final_start;
            first_end = first_end < -32768LL ? -32768LL : first_end;
            final_end = final_end > 32768LL ? 32768LL : final_end;
            for (
                long long candidate_start = first_start;
                candidate_start <= final_start;
                ++candidate_start
            ) {
                for (
                    long long candidate_end = first_end;
                    candidate_end <= final_end;
                    ++candidate_end
                ) {
                    unsigned long long candidate_error = 0;
                    for (
                        unsigned int sample = 0;
                        sample < block_samples;
                        ++sample
                    ) {
                        const long long current_gain = interpolated_gain(
                            candidate_start,
                            candidate_end,
                            sample,
                            block_samples
                        );
                        const unsigned long long source_index = reverse
                            ? (
                                offset + block_samples
                                - sample % block_samples
                            ) % block_samples
                            : (sample + offset) % block_samples;
                        const long long product =
                            (long long)basis[source_index] * current_gain;
                        const long long predicted =
                            round_divide_away(product, 32768LL);
                        const long long difference =
                            (long long)target[sample] - predicted;
                        candidate_error +=
                            (unsigned long long)(difference * difference);
                    }
                    if (candidate_error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        transform_flags = 1U | (reverse ? 2U : 0U);
                        squared_error = candidate_error;
                    }
                }
            }
        }
    }
    output[local] = {
        (unsigned int)basis_index,
        (unsigned int)target_index,
        (unsigned int)offset,
        (int)gain,
        (int)end_gain,
        transform_flags,
        squared_error,
        (unsigned long long)target_energy
    };
}
)cuda";

constexpr char partial_edge_kernel[] = R"cuda(
struct PartialInput {
    unsigned long long candidate_id;
    unsigned long long source_observation_id;
    unsigned long long target_observation_id;
    unsigned long long center_delta_samples;
    long long source_frequency_hz_q20;
    long long target_frequency_hz_q20;
    unsigned long long source_frequency_uncertainty_hz_q20;
    unsigned long long target_frequency_uncertainty_hz_q20;
    unsigned int source_phase_turn_u32;
    unsigned int target_phase_turn_u32;
    unsigned int source_phase_step_u32;
    unsigned int target_phase_step_u32;
    unsigned int source_amplitude_q16;
    unsigned int target_amplitude_q16;
    unsigned int source_phase_uncertainty_u31;
    unsigned int target_phase_uncertainty_u31;
    unsigned int gap_hops;
    int cycle_offset;
    unsigned int phase_usable;
    unsigned int reserved;
};

struct PartialScore {
    unsigned long long candidate_id;
    unsigned int phase_error_u31;
    int continuity_cost_q8;
    int provisional_program_cost_q8;
    unsigned int flags;
};

__device__ unsigned long long partial_abs(long long value) {
    return value >= 0
        ? (unsigned long long)value
        : (unsigned long long)(-(value + 1LL)) + 1ULL;
}

__device__ unsigned long long partial_fraction_q16(
    unsigned long long remainder,
    unsigned long long denominator
) {
    unsigned long long fraction = 0ULL;
    for (unsigned int bit = 0U; bit < 16U; ++bit) {
        fraction <<= 1U;
        if (remainder >= denominator - remainder) {
            remainder -= denominator - remainder;
            fraction |= 1ULL;
        } else {
            remainder *= 2ULL;
        }
    }
    return fraction;
}

__device__ unsigned long long partial_ratio_q16(
    unsigned long long numerator,
    unsigned long long denominator
) {
    if (denominator == 0ULL) {
        return (65535ULL << 16U) | 65535ULL;
    }
    const unsigned long long integer = numerator / denominator;
    if (integer >= 65535ULL) {
        return (65535ULL << 16U) | 65535ULL;
    }
    return (integer << 16U)
        | partial_fraction_q16(numerator % denominator, denominator);
}

__device__ unsigned int partial_bit_width(
    unsigned long long value
) {
    unsigned int width = 0U;
    while (value != 0ULL) {
        ++width;
        value >>= 1U;
    }
    return width;
}

__device__ int partial_log2_one_plus_ratio_q8(
    unsigned long long numerator,
    unsigned long long denominator
) {
    const unsigned long long value_q16 =
        (1ULL << 16U) + partial_ratio_q16(numerator, denominator);
    const unsigned int most_significant =
        partial_bit_width(value_q16) - 1U;
    const int integer_part = (int)most_significant - 16;
    unsigned long long normalized_q31 = most_significant <= 31U
        ? value_q16 << (31U - most_significant)
        : value_q16 >> (most_significant - 31U);
    unsigned int fractional = 0U;
    for (unsigned int bit = 0U; bit < 8U; ++bit) {
        const unsigned long long product =
            normalized_q31 * normalized_q31;
        unsigned long long squared_q31 = product >> 31U;
        fractional <<= 1U;
        if (squared_q31 >= (1ULL << 32U)) {
            squared_q31 >>= 1U;
            fractional |= 1U;
        }
        normalized_q31 = squared_q31;
    }
    return integer_part * 256 + (int)fractional;
}

__device__ int partial_signed_log_amplitude_q8(
    unsigned int target,
    unsigned int source
) {
    if (target == source) {
        return 0;
    }
    if (source == 0U) {
        return target == 0U ? 0 : 0x1fffffff;
    }
    if (target == 0U) {
        return (int)0xe0000000U;
    }
    if (target > source) {
        return partial_log2_one_plus_ratio_q8(
            (unsigned long long)(target - source),
            source
        );
    }
    return -partial_log2_one_plus_ratio_q8(
        (unsigned long long)(source - target),
        target
    );
}

__device__ unsigned int partial_phase_advance(
    unsigned int source_step,
    unsigned int target_step,
    unsigned long long delta
) {
    const unsigned long long step_sum =
        (unsigned long long)source_step + target_step;
    const unsigned long long half_sum = step_sum >> 1U;
    unsigned int product = (unsigned int)(
        (unsigned long long)(unsigned int)half_sum
        * (unsigned int)delta
    );
    if ((step_sum & 1ULL) != 0ULL) {
        product += (unsigned int)((delta >> 1U) + (delta & 1ULL));
    }
    return product;
}

__device__ unsigned int partial_phase_error(
    const PartialInput& input
) {
    const unsigned int predicted =
        input.source_phase_turn_u32
        + partial_phase_advance(
            input.source_phase_step_u32,
            input.target_phase_step_u32,
            input.center_delta_samples
        );
    const unsigned int difference =
        input.target_phase_turn_u32 - predicted;
    if (difference == 0x80000000U) {
        return 0x80000000U;
    }
    return (difference & 0x80000000U) != 0U
        ? 0U - difference
        : difference;
}

__device__ long long partial_saturating_add(
    long long left,
    long long right,
    long long limit
) {
    if (right > 0LL && left > limit - right) {
        return limit;
    }
    if (right < 0LL && left < -limit - right) {
        return -limit;
    }
    const long long total = left + right;
    return total < -limit ? -limit : (total > limit ? limit : total);
}

extern "C" __global__ void score_partial_edges(
    const PartialInput* input,
    unsigned long long candidate_count,
    int continuation_base_bits_q8,
    long long score_saturation,
    PartialScore* output
) {
    const unsigned long long index =
        (unsigned long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (index >= candidate_count) {
        return;
    }
    const PartialInput candidate = input[index];
    const long long frequency_delta =
        candidate.target_frequency_hz_q20
        - candidate.source_frequency_hz_q20;
    const unsigned long long uncertainty =
        candidate.source_frequency_uncertainty_hz_q20
        > 0xffffffffffffffffULL
            - candidate.target_frequency_uncertainty_hz_q20
            ? 0xffffffffffffffffULL
            : candidate.source_frequency_uncertainty_hz_q20
                + candidate.target_frequency_uncertainty_hz_q20;
    const int frequency_cost = partial_log2_one_plus_ratio_q8(
        partial_abs(frequency_delta),
        uncertainty == 0ULL ? 1ULL : uncertainty
    );
    const int amplitude_log = partial_signed_log_amplitude_q8(
        candidate.target_amplitude_q16,
        candidate.source_amplitude_q16
    );
    const unsigned long long amplitude_magnitude =
        amplitude_log >= 0
            ? (unsigned long long)amplitude_log
            : (unsigned long long)(-(amplitude_log + 1)) + 1ULL;
    const int amplitude_cost = partial_log2_one_plus_ratio_q8(
        amplitude_magnitude * 8ULL,
        256ULL
    );
    const unsigned int phase_error = candidate.phase_usable != 0U
        ? partial_phase_error(candidate)
        : 0U;
    const unsigned long long phase_uncertainty =
        (unsigned long long)candidate.source_phase_uncertainty_u31
        + candidate.target_phase_uncertainty_u31;
    const int phase_cost = candidate.phase_usable != 0U
        ? partial_log2_one_plus_ratio_q8(
            phase_error,
            phase_uncertainty == 0ULL ? 1ULL : phase_uncertainty
        )
        : 0;
    const int gap_cost = partial_log2_one_plus_ratio_q8(
        candidate.gap_hops,
        1ULL
    );
    const unsigned long long cycle_magnitude = candidate.cycle_offset >= 0
        ? (unsigned long long)candidate.cycle_offset
        : (unsigned long long)(-(candidate.cycle_offset + 1)) + 1ULL;
    const int cycle_cost = partial_log2_one_plus_ratio_q8(
        cycle_magnitude,
        1ULL
    );
    long long continuity = 0LL;
    continuity = partial_saturating_add(
        continuity,
        frequency_cost,
        score_saturation
    );
    continuity = partial_saturating_add(
        continuity,
        amplitude_cost,
        score_saturation
    );
    continuity = partial_saturating_add(
        continuity,
        phase_cost,
        score_saturation
    );
    continuity = partial_saturating_add(
        continuity,
        gap_cost,
        score_saturation
    );
    continuity = partial_saturating_add(
        continuity,
        cycle_cost,
        score_saturation
    );
    const long long program = partial_saturating_add(
        continuation_base_bits_q8,
        continuity,
        score_saturation
    );
    output[index] = PartialScore{
        candidate.candidate_id,
        phase_error,
        continuity < -2147483648LL
            ? (int)0x80000000U
            : (continuity > 2147483647LL ? 2147483647 : (int)continuity),
        program < -2147483648LL
            ? (int)0x80000000U
            : (program > 2147483647LL ? 2147483647 : (int)program),
        candidate.phase_usable != 0U ? 1U : 0U
    };
}
)cuda";

constexpr char warp_kernel[] = R"cuda(
struct WarpResult {
    unsigned int basis_index;
    unsigned int target_index;
    int source_position_q16;
    int source_step_q16;
    int end_source_step_q16;
    int gain_q15;
    int end_gain_q15;
    unsigned int transform_flags;
    unsigned long long squared_error;
    unsigned long long target_energy;
};

__device__ long long warp_round_divide_away(
    long long numerator,
    long long denominator
) {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

__device__ long long warp_interpolated_gain(
    long long start,
    long long end,
    unsigned int sample,
    unsigned int count
) {
    if (count <= 1U) {
        return start;
    }
    return start + warp_round_divide_away(
        (end - start) * (long long)sample,
        (long long)(count - 1U)
    );
}

__device__ long long warp_position(
    int start_position,
    int start_step,
    int end_step,
    bool linear_step,
    unsigned int sample,
    unsigned int count
) {
    long long position =
        (long long)start_position + (long long)start_step * sample;
    if (!linear_step || sample < 2U) {
        return position;
    }
    return position + warp_round_divide_away(
        (long long)(end_step - start_step) * sample * (sample - 1U),
        2LL * (long long)(count - 2U)
    );
}

__device__ long long warp_basis_value(
    const short* basis,
    unsigned int basis_samples,
    long long position_q16
) {
    const long long period = (long long)basis_samples * 65536LL;
    long long wrapped = position_q16 % period;
    if (wrapped < 0) {
        wrapped += period;
    }
    const unsigned int left = (unsigned int)(wrapped / 65536LL);
    const unsigned int fraction = (unsigned int)(wrapped % 65536LL);
    if (fraction == 0U) {
        return basis[left];
    }
    const unsigned int right = (left + 1U) % basis_samples;
    return warp_round_divide_away(
        (long long)basis[left] * (65536U - fraction)
            + (long long)basis[right] * fraction,
        65536LL
    );
}

extern "C" __global__ void exhaustive_warp(
    const short* blocks,
    unsigned int block_count,
    unsigned int block_samples,
    unsigned int phase_subsamples,
    unsigned int step_radius,
    unsigned int step_increment_q16,
    unsigned int end_step_radius,
    unsigned long long first_candidate,
    unsigned long long candidate_count,
    WarpResult* output
) {
    const unsigned long long local =
        (unsigned long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (local >= candidate_count) {
        return;
    }
    unsigned long long candidate = first_candidate + local;
    const unsigned long long end_choice_count =
        2ULL * end_step_radius + 1ULL;
    const unsigned long long end_choice =
        candidate % end_choice_count;
    candidate /= end_choice_count;
    const unsigned long long step_choice_count =
        2ULL * step_radius + 1ULL;
    const unsigned long long step_choice =
        candidate % step_choice_count;
    candidate /= step_choice_count;
    const bool reverse = candidate % 2ULL != 0ULL;
    candidate /= 2ULL;
    const unsigned long long phase_count =
        (unsigned long long)block_samples * phase_subsamples;
    const unsigned long long phase_choice = candidate % phase_count;
    const unsigned long long pair = candidate / phase_count;
    const unsigned long long basis_index = pair / (block_count - 1U);
    const unsigned long long target_slot = pair % (block_count - 1U);
    const unsigned long long target_index =
        target_slot >= basis_index ? target_slot + 1ULL : target_slot;
    const int direction = reverse ? -1 : 1;
    const int source_position = (int)(
        phase_choice * 65536ULL / phase_subsamples
    );
    const int start_magnitude = (int)(
        65536LL
        + (
            (long long)step_choice - (long long)step_radius
        ) * step_increment_q16
    );
    const int end_delta = (int)(
        (
            (long long)end_choice - (long long)end_step_radius
        ) * step_increment_q16
    );
    const bool linear_step = end_delta != 0;
    const int start_step = direction * start_magnitude;
    const int end_step = linear_step
        ? direction * (start_magnitude + end_delta)
        : 0;
    const short* basis = blocks + basis_index * block_samples;
    const short* target = blocks + target_index * block_samples;

    long long basis_energy = 0;
    long long target_energy = 0;
    long long correlation = 0;
    for (unsigned int sample = 0U; sample < block_samples; ++sample) {
        const long long aligned = warp_basis_value(
            basis,
            block_samples,
            warp_position(
                source_position,
                start_step,
                linear_step ? end_step : start_step,
                linear_step,
                sample,
                block_samples
            )
        );
        const long long desired = target[sample];
        basis_energy += aligned * aligned;
        target_energy += desired * desired;
        correlation += aligned * desired;
    }
    long long fitted_gain = basis_energy == 0
        ? 0
        : warp_round_divide_away(correlation * 32768LL, basis_energy);
    fitted_gain = fitted_gain < -32768LL ? -32768LL : fitted_gain;
    fitted_gain = fitted_gain > 32768LL ? 32768LL : fitted_gain;
    long long gain = fitted_gain;
    long long end_gain = 0;
    unsigned int flags = linear_step ? 2U : 0U;
    unsigned long long squared_error = ~0ULL;
    long long first_gain = fitted_gain - 2LL;
    long long final_gain = fitted_gain + 2LL;
    first_gain = first_gain < -32768LL ? -32768LL : first_gain;
    final_gain = final_gain > 32768LL ? 32768LL : final_gain;
    for (
        long long candidate_gain = first_gain;
        candidate_gain <= final_gain;
        ++candidate_gain
    ) {
        unsigned long long error = 0U;
        for (unsigned int sample = 0U; sample < block_samples; ++sample) {
            const long long aligned = warp_basis_value(
                basis,
                block_samples,
                warp_position(
                    source_position,
                    start_step,
                    linear_step ? end_step : start_step,
                    linear_step,
                    sample,
                    block_samples
                )
            );
            const long long predicted = warp_round_divide_away(
                aligned * candidate_gain,
                32768LL
            );
            const long long difference =
                (long long)target[sample] - predicted;
            error += (unsigned long long)(difference * difference);
        }
        if (error < squared_error) {
            gain = candidate_gain;
            end_gain = 0;
            flags = linear_step ? 2U : 0U;
            squared_error = error;
        }
    }

    if (block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator = (double)(block_samples - 1U);
        for (unsigned int sample = 0U; sample < block_samples; ++sample) {
            const double position = (double)sample / denominator;
            const double aligned = (double)warp_basis_value(
                basis,
                block_samples,
                warp_position(
                    source_position,
                    start_step,
                    linear_step ? end_step : start_step,
                    linear_step,
                    sample,
                    block_samples
                )
            );
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double desired = (double)target[sample] * 32768.0;
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * desired;
            by += second * desired;
        }
        const double determinant = aa * bb - ab * ab;
        const double determinant_floor =
            (aa * bb) > 1.0 ? (aa * bb) * 1.0e-12 : 1.0e-12;
        if (determinant > determinant_floor) {
            const double start_value =
                (ay * bb - by * ab) / determinant;
            const double end_value =
                (by * aa - ay * ab) / determinant;
            long long fitted_start = (long long)(
                start_value + (start_value >= 0.0 ? 0.5 : -0.5)
            );
            long long fitted_end = (long long)(
                end_value + (end_value >= 0.0 ? 0.5 : -0.5)
            );
            fitted_start =
                fitted_start < -32768LL ? -32768LL : fitted_start;
            fitted_start =
                fitted_start > 32768LL ? 32768LL : fitted_start;
            fitted_end = fitted_end < -32768LL ? -32768LL : fitted_end;
            fitted_end = fitted_end > 32768LL ? 32768LL : fitted_end;
            long long first_start = fitted_start - 1LL;
            long long final_start = fitted_start + 1LL;
            long long first_end = fitted_end - 1LL;
            long long final_end = fitted_end + 1LL;
            first_start = first_start < -32768LL ? -32768LL : first_start;
            final_start = final_start > 32768LL ? 32768LL : final_start;
            first_end = first_end < -32768LL ? -32768LL : first_end;
            final_end = final_end > 32768LL ? 32768LL : final_end;
            for (
                long long candidate_start = first_start;
                candidate_start <= final_start;
                ++candidate_start
            ) {
                for (
                    long long candidate_end = first_end;
                    candidate_end <= final_end;
                    ++candidate_end
                ) {
                    unsigned long long error = 0U;
                    for (
                        unsigned int sample = 0U;
                        sample < block_samples;
                        ++sample
                    ) {
                        const long long aligned = warp_basis_value(
                            basis,
                            block_samples,
                            warp_position(
                                source_position,
                                start_step,
                                linear_step ? end_step : start_step,
                                linear_step,
                                sample,
                                block_samples
                            )
                        );
                        const long long current_gain =
                            warp_interpolated_gain(
                                candidate_start,
                                candidate_end,
                                sample,
                                block_samples
                            );
                        const long long predicted =
                            warp_round_divide_away(
                                aligned * current_gain,
                                32768LL
                            );
                        const long long difference =
                            (long long)target[sample] - predicted;
                        error += (unsigned long long)(
                            difference * difference
                        );
                    }
                    if (error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        flags = 1U | (linear_step ? 2U : 0U);
                        squared_error = error;
                    }
                }
            }
        }
    }
    output[local] = WarpResult{
        (unsigned int)basis_index,
        (unsigned int)target_index,
        source_position,
        start_step,
        end_step,
        (int)gain,
        (int)end_gain,
        flags,
        squared_error,
        (unsigned long long)target_energy
    };
}
)cuda";

struct cuda_resources {
    cuda_api* api = nullptr;
    cuda_device device = 0;
    bool retained = false;
    cuda_module module = nullptr;
    cuda_device_ptr input = 0U;
    cuda_device_ptr output = 0U;

    ~cuda_resources() {
        if (api == nullptr) {
            return;
        }
        if (output != 0U) {
            api->memory_free(output);
        }
        if (input != 0U) {
            api->memory_free(input);
        }
        if (module != nullptr) {
            api->module_unload(module);
        }
        if (retained) {
            api->primary_context_release(device);
        }
    }
};

resonith_foundry_status compile_kernel(
    nvrtc_api& api,
    int compute_major,
    int compute_minor,
    const char* source,
    const char* source_name,
    std::vector<char>* image,
    std::string* error
) {
    static std::mutex cache_mutex;
    static std::unordered_map<std::string, std::vector<char>> image_cache;
    const std::string cache_key =
        std::string(source_name)
        + "@sm_"
        + std::to_string(compute_major)
        + std::to_string(compute_minor);
    const std::lock_guard<std::mutex> cache_lock(cache_mutex);
    const auto cached = image_cache.find(cache_key);
    if (cached != image_cache.end()) {
        *image = cached->second;
        return RESONITH_FOUNDRY_OK;
    }
    nvrtc_program program = nullptr;
    nvrtc_result status = api.create_program(
        &program,
        source,
        source_name,
        0,
        nullptr,
        nullptr
    );
    if (status != nvrtc_success) {
        *error = "NVRTC could not create the Foundry program";
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    const std::string architecture =
        "--gpu-architecture=sm_"
        + std::to_string(compute_major)
        + std::to_string(compute_minor);
    const std::array<const char*, 3> options{
        "--std=c++23",
        architecture.c_str(),
        "--fmad=false",
    };
    status = api.compile_program(
        program,
        static_cast<int>(options.size()),
        options.data()
    );
    std::size_t log_size = 0U;
    api.log_size(program, &log_size);
    std::vector<char> log(std::max<std::size_t>(1U, log_size), '\0');
    if (log_size != 0U) {
        api.get_log(program, log.data());
    }
    if (status != nvrtc_success) {
        *error = "NVRTC compilation failed: ";
        error->append(log.data());
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    std::size_t image_size = 0U;
    if (
        api.cubin_size(program, &image_size) != nvrtc_success
        || image_size == 0U
    ) {
        *error = "NVRTC produced no device binary";
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    image->resize(image_size);
    if (api.get_cubin(program, image->data()) != nvrtc_success) {
        *error = "NVRTC could not return the device binary";
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    api.destroy_program(&program);
    image_cache.emplace(cache_key, *image);
    return RESONITH_FOUNDRY_OK;
}

#endif

}  // namespace

extern "C" resonith_foundry_status resonith_foundry_rolling_hash_cpu(
    const std::int16_t* samples,
    std::size_t sample_count,
    std::uint32_t window_samples,
    std::uint64_t* output_hashes,
    std::size_t output_capacity
) {
    if (
        samples == nullptr
        || output_hashes == nullptr
        || window_samples == 0U
        || static_cast<std::size_t>(window_samples) > sample_count
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    const std::size_t hash_count =
        sample_count - static_cast<std::size_t>(window_samples) + 1U;
    if (output_capacity < hash_count) {
        return RESONITH_FOUNDRY_OUTPUT_TOO_SMALL;
    }

    /*
     * Unsigned overflow is the modulus 2^64. Every origin has a hash, so a
     * pattern can cross any later CUDA/entropy/render tile boundary.
     */
    std::uint64_t outgoing_power = 1U;
    for (std::uint32_t index = 1U; index < window_samples; ++index) {
        outgoing_power *= rolling_hash_base;
    }
    const auto symbol = [](std::int16_t sample) noexcept {
        return static_cast<std::uint64_t>(
            static_cast<std::uint16_t>(sample) ^ std::uint16_t{0x8000U}
        ) + 1U;
    };
    std::uint64_t hash = 0U;
    for (std::uint32_t index = 0U; index < window_samples; ++index) {
        hash = hash * rolling_hash_base + symbol(samples[index]);
    }
    output_hashes[0] = hash;
    for (std::size_t origin = 1U; origin < hash_count; ++origin) {
        hash -= symbol(samples[origin - 1U]) * outgoing_power;
        hash = hash * rolling_hash_base
            + symbol(
                samples[
                    origin + static_cast<std::size_t>(window_samples) - 1U
                ]
            );
        output_hashes[origin] = hash;
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_winnow_cpu(
    const std::uint64_t* hashes,
    std::size_t hash_count,
    std::uint32_t selection_window,
    std::uint32_t* output_origins,
    std::size_t output_capacity,
    std::size_t* output_count
) {
    if (
        hashes == nullptr
        || output_origins == nullptr
        || output_count == nullptr
        || selection_window == 0U
        || static_cast<std::size_t>(selection_window) > hash_count
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }

    /*
     * A monotonic deque selects the newest minimum on ties. This canonical
     * rule is O(N), deterministic, and independent of host/GPU tile splits.
     */
    std::vector<std::uint32_t> queue(hash_count);
    std::size_t head = 0U;
    std::size_t tail = 0U;
    std::size_t emitted = 0U;
    std::uint32_t previous = std::numeric_limits<std::uint32_t>::max();
    for (std::size_t index = 0U; index < hash_count; ++index) {
        while (
            head < tail
            && static_cast<std::size_t>(queue[head])
                    + selection_window
                <= index
        ) {
            ++head;
        }
        while (
            head < tail
            && hashes[queue[tail - 1U]] >= hashes[index]
        ) {
            --tail;
        }
        queue[tail++] = static_cast<std::uint32_t>(index);
        if (index + 1U < selection_window) {
            continue;
        }
        const std::uint32_t current = queue[head];
        if (current == previous) {
            continue;
        }
        if (emitted < output_capacity) {
            output_origins[emitted] = current;
        }
        ++emitted;
        previous = current;
    }
    *output_count = emitted;
    return emitted <= output_capacity
        ? RESONITH_FOUNDRY_OK
        : RESONITH_FOUNDRY_OUTPUT_TOO_SMALL;
}

extern "C" resonith_foundry_status
resonith_foundry_gain_phase_candidate_count(
    std::uint32_t block_count,
    std::uint32_t block_samples,
    std::uint64_t* candidate_count
) {
    if (
        candidate_count == nullptr
        || block_count < 2U
        || block_samples == 0U
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t pair_count = 0U;
    if (
        !multiply_fits(block_count, block_count - 1U, &pair_count)
        || !multiply_fits(pair_count, block_samples, candidate_count)
        || !multiply_fits(
            *candidate_count,
            direction_count,
            candidate_count
        )
    ) {
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_warp_candidate_count(
    const resonith_foundry_warp_range* range,
    std::uint64_t* candidate_count
) {
    if (
        range == nullptr
        || candidate_count == nullptr
        || !warp_candidate_count(*range, candidate_count)
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_warp_cpu(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_warp_range* range,
    resonith_foundry_warp_result* output,
    std::size_t output_capacity
) {
    if (blocks == nullptr || range == nullptr || output == nullptr) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status status = validate_warp_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (status != RESONITH_FOUNDRY_OK) {
        return status;
    }
    for (
        std::uint64_t local = 0U;
        local < range->candidate_count;
        ++local
    ) {
        output[local] = evaluate_warp_candidate(
            blocks,
            *range,
            range->first_candidate + local
        );
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_gain_phase_cpu(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    std::size_t output_capacity
) {
    if (blocks == nullptr || range == nullptr || output == nullptr) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status status = validate_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (status != RESONITH_FOUNDRY_OK) {
        return status;
    }
    for (
        std::uint64_t local = 0U;
        local < range->candidate_count;
        ++local
    ) {
        output[local] = evaluate_candidate(
            blocks,
            *range,
            range->first_candidate + local
        );
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_gain_phase_cuda(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    std::size_t output_capacity,
    const char* nvrtc_library_directory,
    resonith_foundry_cuda_evidence* evidence,
    char* error,
    std::size_t error_capacity
) {
    if (error != nullptr && error_capacity != 0U) {
        error[0] = '\0';
    }
    if (
        blocks == nullptr
        || range == nullptr
        || output == nullptr
        || evidence == nullptr
    ) {
        copy_error("invalid Foundry argument", error, error_capacity);
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status range_status = validate_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (range_status != RESONITH_FOUNDRY_OK) {
        copy_error("invalid Foundry candidate range", error, error_capacity);
        return range_status;
    }
    std::memset(evidence, 0, sizeof(*evidence));
#if !defined(_WIN32)
    (void)nvrtc_library_directory;
    copy_error(
        "this build has no CUDA dynamic-loader implementation",
        error,
        error_capacity
    );
    return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
#else
    nvrtc_api nvrtc{};
    cuda_api cuda{};
    std::string detail;
    if (!load_nvrtc(nvrtc_library_directory, &nvrtc, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    if (!load_cuda(&cuda, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    int compiler_major = 0;
    int compiler_minor = 0;
    if (
        nvrtc.version(&compiler_major, &compiler_minor) != nvrtc_success
        || cuda.init(0U) != cuda_success
    ) {
        copy_error("cannot initialize NVRTC/CUDA", error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    cuda_resources resources{};
    resources.api = &cuda;
    int compute_major = 0;
    int compute_minor = 0;
    if (
        cuda.device_get(&resources.device, 0) != cuda_success
        || cuda.device_compute_capability(
            &compute_major,
            &compute_minor,
            resources.device
        ) != cuda_success
    ) {
        copy_error("cannot query CUDA device 0", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    evidence->nvrtc_major = static_cast<std::uint32_t>(compiler_major);
    evidence->nvrtc_minor = static_cast<std::uint32_t>(compiler_minor);
    evidence->compute_major = static_cast<std::uint32_t>(compute_major);
    evidence->compute_minor = static_cast<std::uint32_t>(compute_minor);
    std::size_t device_memory = 0U;
    cuda.device_total_memory(&device_memory, resources.device);
    evidence->device_memory_bytes = device_memory;
    cuda.device_name(
        evidence->device_name,
        static_cast<int>(sizeof(evidence->device_name)),
        resources.device
    );
    evidence->device_name[sizeof(evidence->device_name) - 1U] = '\0';
    evidence->first_candidate = range->first_candidate;
    evidence->candidate_count = range->candidate_count;
    evidence->input_bytes =
        block_element_count * sizeof(std::int16_t);
    evidence->output_bytes =
        range->candidate_count
        * sizeof(resonith_foundry_gain_phase_result);

    std::vector<char> device_image;
    const resonith_foundry_status compile_status = compile_kernel(
        nvrtc,
        compute_major,
        compute_minor,
        gain_phase_kernel,
        "resonith_foundry_gain_phase.cu",
        &device_image,
        &detail
    );
    if (compile_status != RESONITH_FOUNDRY_OK) {
        copy_error(detail, error, error_capacity);
        return compile_status;
    }
    cuda_context context = nullptr;
    if (
        cuda.primary_context_retain(&context, resources.device)
        != cuda_success
    ) {
        copy_error("cannot retain the CUDA primary context", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    resources.retained = true;
    if (cuda.context_set_current(context) != cuda_success) {
        copy_error("cannot activate the CUDA primary context", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    cuda_function function = nullptr;
    if (
        cuda.module_load_data(
            &resources.module,
            device_image.data()
        ) != cuda_success
        || cuda.module_get_function(
            &function,
            resources.module,
            "exhaustive_gain_phase"
        ) != cuda_success
    ) {
        copy_error("cannot load the Foundry CUDA kernel", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    const std::size_t input_bytes =
        block_element_count * sizeof(std::int16_t);
    const std::size_t output_bytes =
        static_cast<std::size_t>(range->candidate_count)
        * sizeof(resonith_foundry_gain_phase_result);
    if (
        cuda.memory_allocate(&resources.input, input_bytes) != cuda_success
        || cuda.memory_allocate(&resources.output, output_bytes)
            != cuda_success
        || cuda.copy_host_to_device(
            resources.input,
            blocks,
            input_bytes
        ) != cuda_success
    ) {
        copy_error("cannot allocate/copy Foundry CUDA buffers", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }

    const unsigned int threads = 128U;
    const std::uint64_t grid64 =
        (range->candidate_count + threads - 1U) / threads;
    if (grid64 > std::numeric_limits<unsigned int>::max()) {
        copy_error("CUDA tile exceeds the one-dimensional grid", error, error_capacity);
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    std::uint32_t block_count = range->block_count;
    std::uint32_t block_samples = range->block_samples;
    std::uint64_t first_candidate = range->first_candidate;
    std::uint64_t candidate_count = range->candidate_count;
    void* arguments[] = {
        &resources.input,
        &block_count,
        &block_samples,
        &first_candidate,
        &candidate_count,
        &resources.output,
    };
    if (
        cuda.launch_kernel(
            function,
            static_cast<unsigned int>(grid64),
            1U,
            1U,
            threads,
            1U,
            1U,
            0U,
            nullptr,
            arguments,
            nullptr
        ) != cuda_success
        || cuda.context_synchronize() != cuda_success
        || cuda.copy_device_to_host(
            output,
            resources.output,
            output_bytes
        ) != cuda_success
    ) {
        copy_error("Foundry CUDA kernel execution failed", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    return RESONITH_FOUNDRY_OK;
#endif
}

extern "C" resonith_foundry_status resonith_foundry_warp_cuda(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_warp_range* range,
    resonith_foundry_warp_result* output,
    std::size_t output_capacity,
    const char* nvrtc_library_directory,
    resonith_foundry_cuda_evidence* evidence,
    char* error,
    std::size_t error_capacity
) {
    if (error != nullptr && error_capacity != 0U) {
        error[0] = '\0';
    }
    if (
        blocks == nullptr
        || range == nullptr
        || output == nullptr
        || evidence == nullptr
    ) {
        copy_error("invalid warp Foundry argument", error, error_capacity);
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status range_status = validate_warp_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (range_status != RESONITH_FOUNDRY_OK) {
        copy_error(
            "invalid warp Foundry candidate range",
            error,
            error_capacity
        );
        return range_status;
    }
    std::memset(evidence, 0, sizeof(*evidence));
#if !defined(_WIN32)
    (void)nvrtc_library_directory;
    copy_error(
        "this build has no CUDA dynamic-loader implementation",
        error,
        error_capacity
    );
    return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
#else
    nvrtc_api nvrtc{};
    cuda_api cuda{};
    std::string detail;
    if (!load_nvrtc(nvrtc_library_directory, &nvrtc, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    if (!load_cuda(&cuda, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    int compiler_major = 0;
    int compiler_minor = 0;
    if (
        nvrtc.version(&compiler_major, &compiler_minor) != nvrtc_success
        || cuda.init(0U) != cuda_success
    ) {
        copy_error("cannot initialize NVRTC/CUDA", error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    cuda_resources resources{};
    resources.api = &cuda;
    int compute_major = 0;
    int compute_minor = 0;
    if (
        cuda.device_get(&resources.device, 0) != cuda_success
        || cuda.device_compute_capability(
            &compute_major,
            &compute_minor,
            resources.device
        ) != cuda_success
    ) {
        copy_error("cannot query CUDA device 0", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    evidence->nvrtc_major = static_cast<std::uint32_t>(compiler_major);
    evidence->nvrtc_minor = static_cast<std::uint32_t>(compiler_minor);
    evidence->compute_major = static_cast<std::uint32_t>(compute_major);
    evidence->compute_minor = static_cast<std::uint32_t>(compute_minor);
    std::size_t device_memory = 0U;
    cuda.device_total_memory(&device_memory, resources.device);
    evidence->device_memory_bytes = device_memory;
    cuda.device_name(
        evidence->device_name,
        static_cast<int>(sizeof(evidence->device_name)),
        resources.device
    );
    evidence->device_name[sizeof(evidence->device_name) - 1U] = '\0';
    evidence->first_candidate = range->first_candidate;
    evidence->candidate_count = range->candidate_count;
    evidence->input_bytes =
        block_element_count * sizeof(std::int16_t);
    evidence->output_bytes =
        range->candidate_count * sizeof(resonith_foundry_warp_result);

    std::vector<char> device_image;
    const resonith_foundry_status compile_status = compile_kernel(
        nvrtc,
        compute_major,
        compute_minor,
        warp_kernel,
        "resonith_foundry_warp.cu",
        &device_image,
        &detail
    );
    if (compile_status != RESONITH_FOUNDRY_OK) {
        copy_error(detail, error, error_capacity);
        return compile_status;
    }
    cuda_context context = nullptr;
    if (
        cuda.primary_context_retain(&context, resources.device)
        != cuda_success
    ) {
        copy_error(
            "cannot retain the CUDA primary context",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    resources.retained = true;
    if (cuda.context_set_current(context) != cuda_success) {
        copy_error(
            "cannot activate the CUDA primary context",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    cuda_function function = nullptr;
    if (
        cuda.module_load_data(&resources.module, device_image.data())
            != cuda_success
        || cuda.module_get_function(
            &function,
            resources.module,
            "exhaustive_warp"
        ) != cuda_success
    ) {
        copy_error(
            "cannot load the warp Foundry CUDA kernel",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    const std::size_t input_bytes =
        block_element_count * sizeof(std::int16_t);
    const std::size_t output_bytes =
        static_cast<std::size_t>(range->candidate_count)
        * sizeof(resonith_foundry_warp_result);
    if (
        cuda.memory_allocate(&resources.input, input_bytes) != cuda_success
        || cuda.memory_allocate(&resources.output, output_bytes)
            != cuda_success
        || cuda.copy_host_to_device(
            resources.input,
            blocks,
            input_bytes
        ) != cuda_success
    ) {
        copy_error(
            "cannot allocate/copy warp Foundry CUDA buffers",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }

    const unsigned int threads = 128U;
    const std::uint64_t grid64 =
        (range->candidate_count + threads - 1U) / threads;
    if (grid64 > std::numeric_limits<unsigned int>::max()) {
        copy_error(
            "warp CUDA tile exceeds the one-dimensional grid",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    std::uint32_t block_count = range->block_count;
    std::uint32_t block_samples = range->block_samples;
    std::uint32_t phase_subsamples = range->phase_subsamples;
    std::uint32_t step_radius = range->step_radius;
    std::uint32_t step_increment_q16 = range->step_increment_q16;
    std::uint32_t end_step_radius = range->end_step_radius;
    std::uint64_t first_candidate = range->first_candidate;
    std::uint64_t candidate_count = range->candidate_count;
    void* arguments[] = {
        &resources.input,
        &block_count,
        &block_samples,
        &phase_subsamples,
        &step_radius,
        &step_increment_q16,
        &end_step_radius,
        &first_candidate,
        &candidate_count,
        &resources.output,
    };
    if (
        cuda.launch_kernel(
            function,
            static_cast<unsigned int>(grid64),
            1U,
            1U,
            threads,
            1U,
            1U,
            0U,
            nullptr,
            arguments,
            nullptr
        ) != cuda_success
        || cuda.context_synchronize() != cuda_success
        || cuda.copy_device_to_host(
            output,
            resources.output,
            output_bytes
        ) != cuda_success
    ) {
        copy_error(
            "warp Foundry CUDA kernel execution failed",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    return RESONITH_FOUNDRY_OK;
#endif
}

extern "C" resonith_foundry_status resonith_foundry_partial_edge_cuda(
    const resonith_partial_observation* observations,
    std::size_t observation_count,
    const resonith_partial_edge* candidates,
    std::size_t candidate_count,
    const resonith_partial_graph_manifest* manifest,
    resonith_partial_edge* output,
    std::size_t output_capacity,
    std::uint32_t threads_per_block,
    const char* nvrtc_library_directory,
    resonith_foundry_cuda_evidence* evidence,
    char* error,
    std::size_t error_capacity
) {
    if (error != nullptr && error_capacity != 0U) {
        error[0] = '\0';
    }
    if (
        observations == nullptr
        || candidates == nullptr
        || manifest == nullptr
        || output == nullptr
        || evidence == nullptr
        || observation_count == 0U
        || candidate_count == 0U
        || output_capacity < candidate_count
        || threads_per_block == 0U
        || threads_per_block > 1024U
        || manifest->struct_size != sizeof(*manifest)
        || manifest->abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
        || manifest->score_saturation < 1024
    ) {
        copy_error(
            "invalid R-190 partial-edge CUDA argument",
            error,
            error_capacity
        );
        return output_capacity < candidate_count
            ? RESONITH_FOUNDRY_OUTPUT_TOO_SMALL
            : RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    const std::uint64_t candidate_count_u64 =
        static_cast<std::uint64_t>(candidate_count);
    std::uint64_t declared_input_bytes = 0U;
    std::uint64_t declared_output_bytes = 0U;
    if (
        !multiply_fits(
            candidate_count_u64,
            sizeof(partial_edge_cuda_input),
            &declared_input_bytes
        )
        || !multiply_fits(
            candidate_count_u64,
            sizeof(partial_edge_cuda_score),
            &declared_output_bytes
        )
        || declared_input_bytes
            > std::numeric_limits<std::uint64_t>::max()
                - declared_output_bytes
        || declared_input_bytes
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::size_t>::max()
            )
        || declared_output_bytes
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::size_t>::max()
            )
    ) {
        copy_error(
            "R-190 partial-edge byte count overflows",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    std::unordered_map<
        std::uint64_t,
        const resonith_partial_observation*
    > by_id;
    for (std::size_t index = 0U; index < observation_count; ++index) {
        const resonith_partial_observation& item = observations[index];
        bool reserved_is_zero = true;
        for (const std::uint32_t value : item.reserved) {
            reserved_is_zero = reserved_is_zero && value == 0U;
        }
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || !reserved_is_zero
            || by_id.contains(item.observation_id)
        ) {
            copy_error(
                "invalid R-190 partial observation",
                error,
                error_capacity
            );
            return RESONITH_FOUNDRY_INVALID_ARGUMENT;
        }
        by_id.emplace(item.observation_id, &item);
    }
    std::vector<const resonith_partial_edge*> ordered_candidates;
    ordered_candidates.reserve(candidate_count);
    for (std::size_t index = 0U; index < candidate_count; ++index) {
        const resonith_partial_edge& item = candidates[index];
        bool reserved_is_zero = true;
        for (const std::uint32_t value : item.reserved) {
            reserved_is_zero = reserved_is_zero && value == 0U;
        }
        if (
            item.struct_size != sizeof(item)
            || item.abi_version != RESONITH_PARTIAL_GRAPH_ABI_VERSION
            || !reserved_is_zero
            || !by_id.contains(item.source_observation_id)
            || !by_id.contains(item.target_observation_id)
        ) {
            copy_error(
                "invalid R-190 partial edge candidate",
                error,
                error_capacity
            );
            return RESONITH_FOUNDRY_INVALID_ARGUMENT;
        }
        ordered_candidates.push_back(&item);
    }
    std::sort(
        ordered_candidates.begin(),
        ordered_candidates.end(),
        [](const auto* left, const auto* right) {
            return left->candidate_id < right->candidate_id;
        }
    );
    std::vector<partial_edge_cuda_input> input;
    input.reserve(candidate_count);
    for (std::size_t index = 0U; index < candidate_count; ++index) {
        const resonith_partial_edge& edge = *ordered_candidates[index];
        if (edge.candidate_id != index) {
            copy_error(
                "partial edge IDs are not canonical",
                error,
                error_capacity
            );
            return RESONITH_FOUNDRY_INVALID_ARGUMENT;
        }
        const auto& source = *by_id.at(edge.source_observation_id);
        const auto& target = *by_id.at(edge.target_observation_id);
        if (
            target.center_sample <= source.center_sample
            || target.center_sample - source.center_sample
                != edge.center_delta_samples
            || target.frequency_hz_q20 - source.frequency_hz_q20
                != edge.frequency_delta_hz_q20
        ) {
            copy_error(
                "partial edge descriptor disagrees with observations",
                error,
                error_capacity
            );
            return RESONITH_FOUNDRY_INVALID_ARGUMENT;
        }
        input.push_back(partial_edge_cuda_input{
            edge.candidate_id,
            edge.source_observation_id,
            edge.target_observation_id,
            edge.center_delta_samples,
            source.frequency_hz_q20,
            target.frequency_hz_q20,
            source.frequency_uncertainty_hz_q20,
            target.frequency_uncertainty_hz_q20,
            source.phase_turn_u32,
            target.phase_turn_u32,
            source.phase_step_u32,
            target.phase_step_u32,
            source.normalized_amplitude_q16,
            target.normalized_amplitude_q16,
            source.phase_uncertainty_u31,
            target.phase_uncertainty_u31,
            edge.gap_hops,
            edge.cycle_offset,
            (
                (
                    source.flags
                    & RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
                ) != 0U
                && (
                    target.flags
                    & RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE
                ) != 0U
            ) ? 1U : 0U,
            0U,
        });
    }
    std::memset(evidence, 0, sizeof(*evidence));
#if !defined(_WIN32)
    (void)nvrtc_library_directory;
    copy_error(
        "this build has no CUDA dynamic-loader implementation",
        error,
        error_capacity
    );
    return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
#else
    nvrtc_api nvrtc{};
    cuda_api cuda{};
    std::string detail;
    if (!load_nvrtc(nvrtc_library_directory, &nvrtc, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    if (!load_cuda(&cuda, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    int compiler_major = 0;
    int compiler_minor = 0;
    if (
        nvrtc.version(&compiler_major, &compiler_minor) != nvrtc_success
        || cuda.init(0U) != cuda_success
    ) {
        copy_error("cannot initialize NVRTC/CUDA", error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    cuda_resources resources{};
    resources.api = &cuda;
    int compute_major = 0;
    int compute_minor = 0;
    if (
        cuda.device_get(&resources.device, 0) != cuda_success
        || cuda.device_compute_capability(
            &compute_major,
            &compute_minor,
            resources.device
        ) != cuda_success
    ) {
        copy_error("cannot query CUDA device 0", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    evidence->nvrtc_major = static_cast<std::uint32_t>(compiler_major);
    evidence->nvrtc_minor = static_cast<std::uint32_t>(compiler_minor);
    evidence->compute_major = static_cast<std::uint32_t>(compute_major);
    evidence->compute_minor = static_cast<std::uint32_t>(compute_minor);
    std::size_t device_memory = 0U;
    cuda.device_total_memory(&device_memory, resources.device);
    evidence->device_memory_bytes = device_memory;
    cuda.device_name(
        evidence->device_name,
        static_cast<int>(sizeof(evidence->device_name)),
        resources.device
    );
    evidence->device_name[sizeof(evidence->device_name) - 1U] = '\0';
    evidence->candidate_count = candidate_count;
    evidence->input_bytes = declared_input_bytes;
    evidence->output_bytes = declared_output_bytes;
    constexpr std::uint64_t vram_limit = 7ULL << 30U;
    const std::uint64_t total_device_bytes =
        evidence->input_bytes + evidence->output_bytes;
    if (
        total_device_bytes > vram_limit
        || total_device_bytes > evidence->device_memory_bytes
    ) {
        copy_error(
            "R-190 partial edge tile exceeds the declared VRAM bound",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }

    std::vector<char> device_image;
    const resonith_foundry_status compile_status = compile_kernel(
        nvrtc,
        compute_major,
        compute_minor,
        partial_edge_kernel,
        "resonith_foundry_partial_edge.cu",
        &device_image,
        &detail
    );
    if (compile_status != RESONITH_FOUNDRY_OK) {
        copy_error(detail, error, error_capacity);
        return compile_status;
    }
    cuda_context context = nullptr;
    if (
        cuda.primary_context_retain(&context, resources.device)
        != cuda_success
    ) {
        copy_error(
            "cannot retain the CUDA primary context",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    resources.retained = true;
    if (cuda.context_set_current(context) != cuda_success) {
        copy_error(
            "cannot activate the CUDA primary context",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    cuda_function function = nullptr;
    if (
        cuda.module_load_data(
            &resources.module,
            device_image.data()
        ) != cuda_success
        || cuda.module_get_function(
            &function,
            resources.module,
            "score_partial_edges"
        ) != cuda_success
    ) {
        copy_error(
            "cannot load the partial-edge CUDA kernel",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    const std::size_t input_bytes =
        static_cast<std::size_t>(declared_input_bytes);
    const std::size_t score_bytes =
        static_cast<std::size_t>(declared_output_bytes);
    if (
        cuda.memory_allocate(&resources.input, input_bytes) != cuda_success
        || cuda.memory_allocate(&resources.output, score_bytes)
            != cuda_success
        || cuda.copy_host_to_device(
            resources.input,
            input.data(),
            input_bytes
        ) != cuda_success
    ) {
        copy_error(
            "cannot allocate/copy partial-edge CUDA buffers",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    const std::uint64_t grid64 =
        (candidate_count + threads_per_block - 1U) / threads_per_block;
    if (grid64 > std::numeric_limits<unsigned int>::max()) {
        copy_error(
            "partial-edge CUDA tile exceeds the one-dimensional grid",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    std::uint64_t count_argument = candidate_count;
    std::int32_t base_bits = manifest->continuation_base_bits_q8;
    std::int64_t score_saturation = manifest->score_saturation;
    void* arguments[] = {
        &resources.input,
        &count_argument,
        &base_bits,
        &score_saturation,
        &resources.output,
    };
    std::vector<partial_edge_cuda_score> scores(candidate_count);
    if (
        cuda.launch_kernel(
            function,
            static_cast<unsigned int>(grid64),
            1U,
            1U,
            threads_per_block,
            1U,
            1U,
            0U,
            nullptr,
            arguments,
            nullptr
        ) != cuda_success
        || cuda.context_synchronize() != cuda_success
        || cuda.copy_device_to_host(
            scores.data(),
            resources.output,
            score_bytes
        ) != cuda_success
    ) {
        copy_error(
            "partial-edge CUDA kernel execution failed",
            error,
            error_capacity
        );
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    std::vector<resonith_partial_edge> staged(candidate_count);
    for (std::size_t index = 0U; index < candidate_count; ++index) {
        if (scores[index].candidate_id != index) {
            copy_error(
                "partial-edge CUDA output order changed",
                error,
                error_capacity
            );
            return RESONITH_FOUNDRY_DEVICE_FAILED;
        }
        staged[index] = *ordered_candidates[index];
        staged[index].phase_error_u31 = scores[index].phase_error_u31;
        staged[index].continuity_cost_q8 =
            scores[index].continuity_cost_q8;
        staged[index].provisional_program_cost_q8 =
            scores[index].provisional_program_cost_q8;
        staged[index].flags = scores[index].flags;
    }
    std::copy(staged.begin(), staged.end(), output);
    return RESONITH_FOUNDRY_OK;
#endif
}

extern "C" const char* resonith_foundry_status_string(
    resonith_foundry_status status
) {
    switch (status) {
        case RESONITH_FOUNDRY_OK:
            return "ok";
        case RESONITH_FOUNDRY_INVALID_ARGUMENT:
            return "invalid argument";
        case RESONITH_FOUNDRY_OUTPUT_TOO_SMALL:
            return "output too small";
        case RESONITH_FOUNDRY_BACKEND_UNAVAILABLE:
            return "backend unavailable";
        case RESONITH_FOUNDRY_COMPILATION_FAILED:
            return "compilation failed";
        case RESONITH_FOUNDRY_DEVICE_FAILED:
            return "device failed";
        case RESONITH_FOUNDRY_RANGE_OVERFLOW:
            return "range overflow";
    }
    return "unknown";
}
