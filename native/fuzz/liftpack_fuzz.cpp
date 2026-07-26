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
    return 0;
}
