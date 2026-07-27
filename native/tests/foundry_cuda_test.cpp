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

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(
            stderr,
            "usage: resonith_foundry_cuda_test <nvrtc-bin-directory>\n"
        );
        return 2;
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
    std::printf(
        "{\n"
        "  \"schema\": \"resonith-r149-cuda-parity-1\",\n"
        "  \"backend\": \"CUDA NVRTC C++23\",\n"
        "  \"device\": \"%s\",\n"
        "  \"compute_capability\": \"%u.%u\",\n"
        "  \"nvrtc\": \"%u.%u\",\n"
        "  \"candidate_count\": %llu,\n"
        "  \"tile_size\": %llu,\n"
        "  \"cpu_gpu_exact\": true,\n"
        "  \"known_transform_recall\": true\n"
        "}\n",
        last_evidence.device_name,
        last_evidence.compute_major,
        last_evidence.compute_minor,
        last_evidence.nvrtc_major,
        last_evidence.nvrtc_minor,
        static_cast<unsigned long long>(candidate_count),
        static_cast<unsigned long long>(tile_size)
    );
    return 0;
}
