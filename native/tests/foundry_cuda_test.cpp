#include "resonith/foundry_cuda.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <vector>

namespace {

bool same(
    const resonith_foundry_gain_phase_result& left,
    const resonith_foundry_gain_phase_result& right
) noexcept {
    return left.basis_index == right.basis_index
        && left.target_index == right.target_index
        && left.source_offset == right.source_offset
        && left.gain_q15 == right.gain_q15
        && left.end_gain_q15 == right.end_gain_q15
        && left.transform_flags == right.transform_flags
        && left.squared_error == right.squared_error
        && left.target_energy == right.target_energy;
}

bool same(
    const resonith_foundry_warp_result& left,
    const resonith_foundry_warp_result& right
) noexcept {
    return left.basis_index == right.basis_index
        && left.target_index == right.target_index
        && left.source_position_q16 == right.source_position_q16
        && left.source_step_q16 == right.source_step_q16
        && left.end_source_step_q16 == right.end_source_step_q16
        && left.gain_q15 == right.gain_q15
        && left.end_gain_q15 == right.end_gain_q15
        && left.transform_flags == right.transform_flags
        && left.squared_error == right.squared_error
        && left.target_energy == right.target_energy;
}

void fail(const char* message) {
    std::fprintf(stderr, "foundry_cuda_test: %s\n", message);
    std::exit(1);
}

std::int16_t scale_q15(std::int16_t sample, std::int32_t gain) {
    const std::int64_t product =
        static_cast<std::int64_t>(sample) * gain;
    const std::int64_t rounded = product >= 0
        ? (product + 16384) / 32768
        : -((-product + 16384) / 32768);
    return static_cast<std::int16_t>(rounded);
}

std::int32_t interpolate_q15(
    std::int32_t start,
    std::int32_t end,
    std::uint32_t sample,
    std::uint32_t count
) {
    const std::int64_t numerator =
        static_cast<std::int64_t>(end - start) * sample;
    const std::int64_t denominator = count - 1U;
    const std::int64_t offset = numerator >= 0
        ? (numerator + denominator / 2) / denominator
        : -((-numerator + denominator / 2) / denominator);
    return static_cast<std::int32_t>(start + offset);
}

std::int64_t divide_away(
    std::int64_t numerator,
    std::int64_t denominator
) {
    return numerator >= 0
        ? (numerator + denominator / 2) / denominator
        : -((-numerator + denominator / 2) / denominator);
}

std::int64_t test_warp_position(
    std::int32_t start_position,
    std::int32_t start_step,
    std::int32_t end_step,
    std::uint32_t sample,
    std::uint32_t count
) {
    std::int64_t position =
        static_cast<std::int64_t>(start_position)
        + static_cast<std::int64_t>(start_step) * sample;
    if (sample < 2U) {
        return position;
    }
    return position + divide_away(
        static_cast<std::int64_t>(end_step - start_step)
            * sample * (sample - 1U),
        2LL * static_cast<std::int64_t>(count - 2U)
    );
}

std::int16_t test_warp_value(
    const std::int16_t* basis,
    std::uint32_t count,
    std::int64_t position_q16
) {
    const std::int64_t period = static_cast<std::int64_t>(count) * 65536LL;
    std::int64_t wrapped = position_q16 % period;
    if (wrapped < 0) {
        wrapped += period;
    }
    const std::uint32_t left =
        static_cast<std::uint32_t>(wrapped / 65536LL);
    const std::uint32_t fraction =
        static_cast<std::uint32_t>(wrapped % 65536LL);
    const std::uint32_t right = (left + 1U) % count;
    return static_cast<std::int16_t>(divide_away(
        static_cast<std::int64_t>(basis[left]) * (65536U - fraction)
            + static_cast<std::int64_t>(basis[right]) * fraction,
        65536LL
    ));
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(
            stderr,
            "usage: resonith_foundry_cuda_test <nvrtc-bin-directory>\n"
        );
        return 2;
    }

    /*
     * R-156 hashes every origin, including a motif that straddles a notional
     * 16-sample implementation tile at origin 13.
     */
    std::array<std::int16_t, 48> gridless{};
    for (std::size_t index = 0U; index < gridless.size(); ++index) {
        gridless[index] = static_cast<std::int16_t>(
            (index * 1237U + 97U) % 30001U
        );
    }
    constexpr std::size_t motif_origin = 13U;
    constexpr std::size_t repeated_origin = 29U;
    constexpr std::uint32_t motif_samples = 8U;
    std::copy_n(
        gridless.begin() + motif_origin,
        motif_samples,
        gridless.begin() + repeated_origin
    );
    std::array<std::uint64_t, 41> rolling{};
    if (
        resonith_foundry_rolling_hash_cpu(
            gridless.data(),
            gridless.size(),
            motif_samples,
            rolling.data(),
            rolling.size()
        ) != RESONITH_FOUNDRY_OK
        || rolling[motif_origin] != rolling[repeated_origin]
    ) {
        fail("gridless rolling hash missed a cross-tile motif");
    }
    std::array<std::uint32_t, 41> anchors{};
    std::size_t anchor_count = 0U;
    if (
        resonith_foundry_winnow_cpu(
            rolling.data(),
            rolling.size(),
            5U,
            anchors.data(),
            anchors.size(),
            &anchor_count
        ) != RESONITH_FOUNDRY_OK
        || anchor_count == 0U
        || !std::is_sorted(
            anchors.begin(),
            anchors.begin() + static_cast<std::ptrdiff_t>(anchor_count)
        )
    ) {
        fail("gridless content-defined anchors are not canonical");
    }

    constexpr std::uint32_t block_count = 5U;
    constexpr std::uint32_t block_samples = 32U;
    std::array<std::int16_t, block_count * block_samples> blocks{};
    for (
        std::uint32_t sample = 0U;
        sample < block_samples;
        ++sample
    ) {
        const std::int32_t value =
            static_cast<std::int32_t>((sample * 7919U) % 24001U) - 12000;
        blocks[sample] = static_cast<std::int16_t>(value);
    }
    constexpr std::uint32_t known_offset = 7U;
    constexpr std::int32_t known_gain = -16384;
    constexpr std::uint32_t linear_offset = 11U;
    constexpr std::int32_t linear_start_gain = 28672;
    constexpr std::int32_t linear_end_gain = 8192;
    constexpr std::uint32_t reverse_offset = 19U;
    for (
        std::uint32_t sample = 0U;
        sample < block_samples;
        ++sample
    ) {
        blocks[block_samples + sample] = scale_q15(
            blocks[(sample + known_offset) % block_samples],
            known_gain
        );
        blocks[2U * block_samples + sample] = scale_q15(
            blocks[(sample + linear_offset) % block_samples],
            interpolate_q15(
                linear_start_gain,
                linear_end_gain,
                sample,
                block_samples
            )
        );
        blocks[3U * block_samples + sample] = blocks[
            (
                reverse_offset + block_samples
                - sample % block_samples
            ) % block_samples
        ];
        blocks[4U * block_samples + sample] =
            static_cast<std::int16_t>(300 - sample * 11U);
    }

    std::uint64_t candidate_count = 0U;
    if (
        resonith_foundry_gain_phase_candidate_count(
            block_count,
            block_samples,
            &candidate_count
        ) != RESONITH_FOUNDRY_OK
        || candidate_count
            != static_cast<std::uint64_t>(
                block_count * (block_count - 1U) * block_samples
                * 2U
            )
    ) {
        fail("candidate cardinality is incomplete");
    }

    /*
     * Deliberately use uneven tiles: R-149 requires tiling to preserve the
     * exact candidate set and result order.
     */
    constexpr std::uint64_t tile_size = 73U;
    std::vector<resonith_foundry_gain_phase_result> cpu(candidate_count);
    std::vector<resonith_foundry_gain_phase_result> gpu(candidate_count);
    resonith_foundry_cuda_evidence last_evidence{};
    for (
        std::uint64_t first = 0U;
        first < candidate_count;
        first += tile_size
    ) {
        const std::uint64_t count = std::min(
            tile_size,
            candidate_count - first
        );
        const resonith_foundry_gain_phase_range range{
            block_count,
            block_samples,
            first,
            count,
        };
        if (
            resonith_foundry_gain_phase_cpu(
                blocks.data(),
                blocks.size(),
                &range,
                cpu.data() + first,
                static_cast<std::size_t>(count)
            ) != RESONITH_FOUNDRY_OK
        ) {
            fail("CPU reference failed");
        }
        std::array<char, 4096> error{};
        const resonith_foundry_status status =
            resonith_foundry_gain_phase_cuda(
                blocks.data(),
                blocks.size(),
                &range,
                gpu.data() + first,
                static_cast<std::size_t>(count),
                argv[1],
                &last_evidence,
                error.data(),
                error.size()
            );
        if (status != RESONITH_FOUNDRY_OK) {
            std::fprintf(
                stderr,
                "CUDA status %s: %s\n",
                resonith_foundry_status_string(status),
                error.data()
            );
            return 1;
        }
    }

    for (
        std::uint64_t index = 0U;
        index < candidate_count;
        ++index
    ) {
        if (!same(cpu[index], gpu[index])) {
            std::fprintf(
                stderr,
                "CPU/GPU mismatch at candidate %llu\n",
                static_cast<unsigned long long>(index)
            );
            return 1;
        }
    }

    const auto known = std::find_if(
        gpu.begin(),
        gpu.end(),
        [](const resonith_foundry_gain_phase_result& item) {
            return item.basis_index == 0U
                && item.target_index == 1U
                && item.source_offset == known_offset
                && item.gain_q15 == known_gain
                && item.squared_error == 0U;
        }
    );
    if (known == gpu.end()) {
        const auto nearest = std::min_element(
            gpu.begin(),
            gpu.end(),
            [](const auto& left, const auto& right) {
                const bool left_pair =
                    left.basis_index == 0U && left.target_index == 1U;
                const bool right_pair =
                    right.basis_index == 0U && right.target_index == 1U;
                if (left_pair != right_pair) {
                    return left_pair;
                }
                return left.squared_error < right.squared_error;
            }
        );
        std::fprintf(
            stderr,
            "nearest known transform: offset=%u gain=%d sse=%llu\n",
            nearest->source_offset,
            nearest->gain_q15,
            static_cast<unsigned long long>(nearest->squared_error)
        );
        fail("complete search missed the known transform");
    }
    const auto linear = std::find_if(
        gpu.begin(),
        gpu.end(),
        [](const resonith_foundry_gain_phase_result& item) {
            return item.basis_index == 0U
                && item.target_index == 2U
                && item.source_offset == linear_offset
                && item.gain_q15 == linear_start_gain
                && item.end_gain_q15 == linear_end_gain
                && (
                    item.transform_flags
                    & RESONITH_FOUNDRY_TRANSFORM_LINEAR_GAIN
                ) != 0U
                && item.squared_error == 0U;
        }
    );
    if (linear == gpu.end()) {
        fail("complete search missed the known linear state law");
    }
    const auto reverse = std::find_if(
        gpu.begin(),
        gpu.end(),
        [](const resonith_foundry_gain_phase_result& item) {
            return item.basis_index == 0U
                && item.target_index == 3U
                && item.source_offset == reverse_offset
                && item.gain_q15 == 32767
                && (
                    item.transform_flags
                    & RESONITH_FOUNDRY_TRANSFORM_REVERSE
                ) != 0U
                && item.squared_error == 0U;
        }
    );
    if (reverse == gpu.end()) {
        fail("complete search missed the known reverse law");
    }

    /*
     * R-157 evaluates the complete fractional phase x start/end step lattice
     * in large GPU batches. The known target combines sub-sample phase,
     * bounded pitch/time drift, and signed gain, and must be recalled exactly.
     */
    constexpr std::uint32_t warp_block_count = 3U;
    constexpr std::uint32_t warp_block_samples = 16U;
    constexpr std::uint32_t warp_phase_subsamples = 4U;
    constexpr std::uint32_t warp_step_radius = 1U;
    constexpr std::uint32_t warp_step_increment = 512U;
    constexpr std::uint32_t warp_end_step_radius = 1U;
    constexpr std::int32_t warp_position = 3 * 65536 + 16384;
    constexpr std::int32_t warp_start_step = 65536 + 512;
    constexpr std::int32_t warp_end_step = warp_start_step + 512;
    constexpr std::int32_t warp_gain = -16384;
    std::array<
        std::int16_t,
        warp_block_count * warp_block_samples
    > warp_blocks{};
    for (
        std::uint32_t sample = 0U;
        sample < warp_block_samples;
        ++sample
    ) {
        warp_blocks[sample] = static_cast<std::int16_t>(
            static_cast<std::int32_t>((sample * 5279U + 101U) % 22001U)
                - 11000
        );
    }
    for (
        std::uint32_t sample = 0U;
        sample < warp_block_samples;
        ++sample
    ) {
        const std::int16_t aligned = test_warp_value(
            warp_blocks.data(),
            warp_block_samples,
            test_warp_position(
                warp_position,
                warp_start_step,
                warp_end_step,
                sample,
                warp_block_samples
            )
        );
        warp_blocks[warp_block_samples + sample] =
            scale_q15(aligned, warp_gain);
        warp_blocks[2U * warp_block_samples + sample] =
            static_cast<std::int16_t>(sample * 97 - 700);
    }
    resonith_foundry_warp_range warp_range{
        warp_block_count,
        warp_block_samples,
        warp_phase_subsamples,
        warp_step_radius,
        warp_step_increment,
        warp_end_step_radius,
        0U,
        1U,
    };
    std::uint64_t warp_candidate_count = 0U;
    if (
        resonith_foundry_warp_candidate_count(
            &warp_range,
            &warp_candidate_count
        ) != RESONITH_FOUNDRY_OK
        || warp_candidate_count != 6912U
    ) {
        fail("R-157 warp candidate cardinality is incomplete");
    }
    std::vector<resonith_foundry_warp_result> warp_cpu(
        warp_candidate_count
    );
    std::vector<resonith_foundry_warp_result> warp_gpu(
        warp_candidate_count
    );
    constexpr std::uint64_t warp_tile_size = 4099U;
    for (
        std::uint64_t first = 0U;
        first < warp_candidate_count;
        first += warp_tile_size
    ) {
        const std::uint64_t count = std::min(
            warp_tile_size,
            warp_candidate_count - first
        );
        warp_range.first_candidate = first;
        warp_range.candidate_count = count;
        if (
            resonith_foundry_warp_cpu(
                warp_blocks.data(),
                warp_blocks.size(),
                &warp_range,
                warp_cpu.data() + first,
                static_cast<std::size_t>(count)
            ) != RESONITH_FOUNDRY_OK
        ) {
            fail("R-157 CPU warp reference failed");
        }
        std::array<char, 16384> warp_error{};
        const resonith_foundry_status warp_status =
            resonith_foundry_warp_cuda(
                warp_blocks.data(),
                warp_blocks.size(),
                &warp_range,
                warp_gpu.data() + first,
                static_cast<std::size_t>(count),
                argv[1],
                &last_evidence,
                warp_error.data(),
                warp_error.size()
            );
        if (warp_status != RESONITH_FOUNDRY_OK) {
            std::fprintf(
                stderr,
                "R-157 CUDA status %s: %s\n",
                resonith_foundry_status_string(warp_status),
                warp_error.data()
            );
            return 1;
        }
    }
    for (
        std::uint64_t index = 0U;
        index < warp_candidate_count;
        ++index
    ) {
        if (!same(warp_cpu[index], warp_gpu[index])) {
            std::fprintf(
                stderr,
                "R-157 CPU/GPU mismatch at candidate %llu\n",
                static_cast<unsigned long long>(index)
            );
            return 1;
        }
    }
    const auto known_warp = std::find_if(
        warp_gpu.begin(),
        warp_gpu.end(),
        [](const resonith_foundry_warp_result& item) {
            return item.basis_index == 0U
                && item.target_index == 1U
                && item.source_position_q16 == warp_position
                && item.source_step_q16 == warp_start_step
                && item.end_source_step_q16 == warp_end_step
                && std::abs(item.gain_q15 - warp_gain) <= 8
                && (
                    item.transform_flags
                    & RESONITH_FOUNDRY_WARP_LINEAR_STEP
                ) != 0U
                && item.squared_error == 0U;
        }
    );
    if (known_warp == warp_gpu.end()) {
        const auto nearest_warp = std::min_element(
            warp_gpu.begin(),
            warp_gpu.end(),
            [](const auto& left, const auto& right) {
                const bool left_pair =
                    left.basis_index == 0U && left.target_index == 1U;
                const bool right_pair =
                    right.basis_index == 0U && right.target_index == 1U;
                if (left_pair != right_pair) {
                    return left_pair;
                }
                return left.squared_error < right.squared_error;
            }
        );
        std::fprintf(
            stderr,
            "nearest warp: position=%d step=%d end_step=%d "
            "gain=%d end_gain=%d flags=%u sse=%llu\n",
            nearest_warp->source_position_q16,
            nearest_warp->source_step_q16,
            nearest_warp->end_source_step_q16,
            nearest_warp->gain_q15,
            nearest_warp->end_gain_q15,
            nearest_warp->transform_flags,
            static_cast<unsigned long long>(nearest_warp->squared_error)
        );
        fail("R-157 complete warp search missed the known exact law");
    }

    const resonith_partial_resolution partial_resolution{
        sizeof(resonith_partial_resolution),
        RESONITH_PARTIAL_GRAPH_ABI_VERSION,
        7U,
        1024U,
        128U,
        {0U, 0U, 0U},
    };
    resonith_partial_graph_manifest partial_manifest{};
    partial_manifest.struct_size = sizeof(partial_manifest);
    partial_manifest.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
    partial_manifest.sample_rate = 8000U;
    partial_manifest.resolution_count = 1U;
    partial_manifest.gap_count = 2U;
    partial_manifest.neighbors_per_gap = 2U;
    partial_manifest.cycle_offset_count = 3U;
    partial_manifest.minimum_track_observations = 3U;
    partial_manifest.maximum_frequency_jump_hz_q20 = 80LL << 20U;
    partial_manifest.maximum_frequency_slope_hz_per_sample_q20 = 1LL << 16U;
    partial_manifest.continuation_base_bits_q8 = 12 * 256;
    partial_manifest.continuation_reward_q8 = 12 * 256;
    partial_manifest.score_saturation = (1LL << 31U) - 1LL;
    partial_manifest.maximum_edge_records = 1024U;
    partial_manifest.maximum_path_hypotheses = 128U;
    partial_manifest.exact_set_candidate_limit = 20U;
    partial_manifest.gaps[0] = 1U;
    partial_manifest.gaps[1] = 2U;
    partial_manifest.cycle_offsets[0] = -1;
    partial_manifest.cycle_offsets[1] = 0;
    partial_manifest.cycle_offsets[2] = 1;
    const std::uint32_t partial_step_440 = static_cast<std::uint32_t>(
        (440ULL << 32U) / partial_manifest.sample_rate
    );
    const std::uint32_t partial_step_442 = static_cast<std::uint32_t>(
        (442ULL << 32U) / partial_manifest.sample_rate
    );
    auto partial_observation = [](
        std::uint64_t id,
        std::uint32_t frame,
        std::int64_t frequency,
        std::uint32_t phase,
        std::uint32_t step,
        std::uint32_t amplitude,
        std::uint32_t ownership
    ) {
        resonith_partial_observation value{};
        value.struct_size = sizeof(value);
        value.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
        value.observation_id = id;
        value.center_sample = static_cast<std::uint64_t>(frame) * 128U;
        value.frequency_hz_q20 = frequency;
        value.frequency_uncertainty_hz_q20 = 1U << 20U;
        value.phase_turn_u32 = phase;
        value.phase_step_u32 = step;
        value.normalized_amplitude_q16 = amplitude;
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
    };
    std::array<resonith_partial_observation, 5> partial_observations{
        partial_observation(
            10U, 0U, 440LL << 20U, 0x10000000U,
            partial_step_440, 12000U << 16U, 0U
        ),
        partial_observation(
            11U, 1U, 441LL << 20U, 0x1ccccccdU,
            partial_step_440, 11800U << 16U, 1U
        ),
        partial_observation(
            12U, 1U, 900LL << 20U, 0x20000000U,
            0x1ccccccdU, 4000U << 16U, 2U
        ),
        partial_observation(
            13U, 2U, 442LL << 20U, 0x2999999aU,
            partial_step_442, 11600U << 16U, 3U
        ),
        partial_observation(
            14U, 2U, 1500LL << 20U, 0x30000000U,
            0x4ccccccdU, 2000U << 16U, 4U
        ),
    };
    std::size_t partial_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &partial_resolution,
            1U,
            partial_observations.data(),
            partial_observations.size(),
            &partial_manifest,
            nullptr,
            0U,
            &partial_count
        ) != RESONITH_STATUS_OK
        || partial_count != 9U
    ) {
        fail("R-190 CPU edge preflight failed");
    }
    std::vector<resonith_partial_edge> partial_cpu(partial_count);
    if (
        resonith_partial_graph_edges_cpu(
            &partial_resolution,
            1U,
            partial_observations.data(),
            partial_observations.size(),
            &partial_manifest,
            partial_cpu.data(),
            partial_cpu.size(),
            &partial_count
        ) != RESONITH_STATUS_OK
    ) {
        fail("R-190 CPU edge scoring failed");
    }
    for (
        const std::uint32_t threads
        : std::array<std::uint32_t, 6>{1U, 31U, 32U, 255U, 256U, 1024U}
    ) {
        std::vector<resonith_partial_edge> partial_gpu(partial_count);
        std::array<char, 16384> partial_error{};
        const resonith_foundry_status partial_status =
            resonith_foundry_partial_edge_cuda(
                partial_observations.data(),
                partial_observations.size(),
                partial_cpu.data(),
                partial_cpu.size(),
                &partial_manifest,
                partial_gpu.data(),
                partial_gpu.size(),
                threads,
                argv[1],
                &last_evidence,
                partial_error.data(),
                partial_error.size()
            );
        if (partial_status != RESONITH_FOUNDRY_OK) {
            std::fprintf(
                stderr,
                "R-190 CUDA status %s: %s\n",
                resonith_foundry_status_string(partial_status),
                partial_error.data()
            );
            return 1;
        }
        if (
            std::memcmp(
                partial_cpu.data(),
                partial_gpu.data(),
                partial_count * sizeof(resonith_partial_edge)
            ) != 0
        ) {
            fail("R-190 CPU/CUDA edge records are not bit-exact");
        }
    }
    std::vector<resonith_partial_observation> randomized_observations;
    randomized_observations.reserve(32U * partial_observations.size());
    std::uint64_t random_state = 0x5191d00d4a4655ULL;
    auto next_random = [&random_state]() {
        random_state = random_state * 6364136223846793005ULL
            + 1442695040888963407ULL;
        return random_state;
    };
    for (std::uint32_t test_case = 0U; test_case < 32U; ++test_case) {
        const std::int64_t base_frequency = static_cast<std::int64_t>(
            200U + next_random() % 1800U
        );
        for (
            std::size_t index = 0U;
            index < partial_observations.size();
            ++index
        ) {
            resonith_partial_observation value = partial_observations[index];
            value.observation_id =
                static_cast<std::uint64_t>(test_case) * 100U + index;
            value.detector_id = static_cast<std::int32_t>(test_case);
            value.frequency_hz_q20 = (
                index == 2U || index == 4U
                    ? base_frequency
                        + 240
                        + static_cast<std::int64_t>(next_random() % 600U)
                    : base_frequency + static_cast<std::int64_t>(index)
            ) << 20U;
            value.phase_turn_u32 =
                static_cast<std::uint32_t>(next_random());
            value.phase_step_u32 =
                static_cast<std::uint32_t>(next_random());
            value.normalized_amplitude_q16 = static_cast<std::uint32_t>(
                1000U + next_random() % 50000U
            ) << 16U;
            value.ownership_component =
                test_case * 16U + static_cast<std::uint32_t>(index);
            randomized_observations.push_back(value);
        }
    }
    resonith_partial_graph_manifest randomized_manifest = partial_manifest;
    randomized_manifest.maximum_edge_records = 32768U;
    std::size_t randomized_edge_count = 0U;
    if (
        resonith_partial_graph_edges_cpu(
            &partial_resolution,
            1U,
            randomized_observations.data(),
            randomized_observations.size(),
            &randomized_manifest,
            nullptr,
            0U,
            &randomized_edge_count
        ) != RESONITH_STATUS_OK
        || randomized_edge_count == 0U
    ) {
        fail("randomized R-190 CPU edge preflight failed");
    }
    std::vector<resonith_partial_edge> randomized_cpu(
        randomized_edge_count
    );
    if (
        resonith_partial_graph_edges_cpu(
            &partial_resolution,
            1U,
            randomized_observations.data(),
            randomized_observations.size(),
            &randomized_manifest,
            randomized_cpu.data(),
            randomized_cpu.size(),
            &randomized_edge_count
        ) != RESONITH_STATUS_OK
    ) {
        fail("randomized R-190 CPU edge fill failed");
    }
    std::vector<resonith_partial_edge> randomized_gpu(
        randomized_edge_count
    );
    std::array<char, 16384> randomized_error{};
    const resonith_foundry_status randomized_status =
        resonith_foundry_partial_edge_cuda(
            randomized_observations.data(),
            randomized_observations.size(),
            randomized_cpu.data(),
            randomized_cpu.size(),
            &randomized_manifest,
            randomized_gpu.data(),
            randomized_gpu.size(),
            127U,
            argv[1],
            &last_evidence,
            randomized_error.data(),
            randomized_error.size()
        );
    if (
        randomized_status != RESONITH_FOUNDRY_OK
        || std::memcmp(
            randomized_cpu.data(),
            randomized_gpu.data(),
            randomized_edge_count * sizeof(resonith_partial_edge)
        ) != 0
    ) {
        std::fprintf(
            stderr,
            "randomized R-190 CPU/CUDA parity failed (%s): %s\n",
            resonith_foundry_status_string(randomized_status),
            randomized_error.data()
        );
        return 1;
    }
    std::printf(
        "{\n"
        "  \"schema\": \"resonith-r157-cuda-parity-1\",\n"
        "  \"backend\": \"CUDA NVRTC C++23\",\n"
        "  \"device\": \"%s\",\n"
        "  \"compute_capability\": \"%u.%u\",\n"
        "  \"nvrtc\": \"%u.%u\",\n"
        "  \"candidate_count\": %llu,\n"
        "  \"tile_size\": %llu,\n"
        "  \"warp_candidate_count\": %llu,\n"
        "  \"warp_tile_size\": %llu,\n"
        "  \"partial_edge_count\": %zu,\n"
        "  \"partial_tile_sizes\": [1,31,32,255,256,1024],\n"
        "  \"randomized_partial_cases\": 32,\n"
        "  \"randomized_partial_edge_count\": %zu,\n"
        "  \"cpu_gpu_exact\": true,\n"
        "  \"known_transform_recall\": true,\n"
        "  \"known_warp_recall\": true\n"
        "}\n",
        last_evidence.device_name,
        last_evidence.compute_major,
        last_evidence.compute_minor,
        last_evidence.nvrtc_major,
        last_evidence.nvrtc_minor,
        static_cast<unsigned long long>(candidate_count),
        static_cast<unsigned long long>(tile_size),
        static_cast<unsigned long long>(warp_candidate_count),
        static_cast<unsigned long long>(warp_tile_size),
        partial_count,
        randomized_edge_count
    );
    return 0;
}
