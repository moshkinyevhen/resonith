#include "resonith/liftpack.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::uint32_t kFuzzMaximumSamples = 1U << 16U;
constexpr std::uint32_t kFuzzMaximumBlocks = 1U << 12U;

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_liftpack_info info{};
    if (
        resonith_liftpack_inspect(data, size, &info)
        != RESONITH_STATUS_OK
    ) {
        return 0;
    }
    if (
        info.sample_count > kFuzzMaximumSamples
        || info.block_count > kFuzzMaximumBlocks
    ) {
        return 0;
    }

    std::vector<resonith_liftpack_block_info> index(info.block_count);
    std::size_t indexed_blocks = 0;
    const resonith_status index_status = resonith_liftpack_index_blocks(
        data,
        size,
        index.data(),
        index.size(),
        &indexed_blocks
    );
    if (index_status != RESONITH_STATUS_OK) {
        return 0;
    }

    const std::size_t scratch_count = resonith_liftpack_required_scratch(
        &info
    );
    std::vector<std::int64_t> output(info.sample_count);
    std::vector<std::int64_t> scratch(scratch_count);
    std::size_t samples_written = 0;
    const resonith_status decode_status = resonith_liftpack_decode(
        data,
        size,
        output.data(),
        output.size(),
        scratch.data(),
        scratch.size(),
        &samples_written
    );
    if (
        decode_status == RESONITH_STATUS_OK
        && (
            samples_written != info.sample_count
            || indexed_blocks != info.block_count
        )
    ) {
        __builtin_trap();
    }
    if (decode_status == RESONITH_STATUS_OK && info.block_count != 0U) {
        const std::uint32_t block_id = info.block_count - 1U;
        std::vector<std::int64_t> block_output(info.block_size);
        std::uint32_t sample_offset = 0U;
        std::size_t block_samples = 0U;
        const resonith_status block_status = resonith_liftpack_decode_block(
            data,
            size,
            block_id,
            block_output.data(),
            block_output.size(),
            scratch.data(),
            scratch.size(),
            &sample_offset,
            &block_samples
        );
        if (
            block_status != RESONITH_STATUS_OK
            || sample_offset != index[block_id].sample_offset
            || block_samples != index[block_id].sample_count
        ) {
            __builtin_trap();
        }
        for (std::size_t index_in_block = 0; index_in_block < block_samples;
             ++index_in_block) {
            if (
                block_output[index_in_block]
                != output[sample_offset + index_in_block]
            ) {
                __builtin_trap();
            }
        }
    }
    return 0;
}
