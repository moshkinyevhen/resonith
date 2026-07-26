#include "resonith/seek.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::array<std::uint8_t, 139> kSource = {
    0x52, 0x53, 0x4c, 0x31, 0x01, 0x10, 0x00, 0x40, 0x00, 0x00, 0x00, 0x04,
    0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x02, 0xe0, 0x00, 0x00, 0x00,
    0xec, 0xf3, 0xfd, 0xf3, 0xef, 0xff, 0xfc, 0xdf, 0xff, 0xcf, 0xff, 0xef,
    0xff, 0x3f, 0xff, 0xff, 0xfd, 0xff, 0x3f, 0xff, 0xff, 0xef, 0xff, 0xff,
    0xcf, 0xff, 0xff, 0xdf, 0x10, 0x00, 0x01, 0x01, 0x08, 0x80, 0x00, 0x00,
    0x00, 0xc8, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e,
    0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x10, 0x00, 0x02, 0x00, 0x01, 0x9b, 0x00,
    0x00, 0x00, 0xff, 0xff, 0xff, 0x7f, 0x63, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x99, 0x99, 0x99, 0x99, 0x99, 0x99, 0x99, 0x01, 0x10, 0x00,
    0x03, 0x01, 0x0a, 0xa0, 0x00, 0x00, 0x00, 0x48, 0xd1, 0xa0, 0x81, 0x06,
    0x84, 0xbd, 0x31, 0xe6, 0x1b, 0xc2, 0x08, 0x53, 0xb2, 0x30, 0xc2, 0x08,
    0x23, 0x4c, 0xc9, 0x3a, 0x63, 0xd9, 0x65,
};

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    std::size_t canonical_size = 0U;
    if (
        resonith_seek_index_required_size(
            kSource.data(),
            kSource.size(),
            &canonical_size
        ) != RESONITH_STATUS_OK
    ) {
        __builtin_trap();
    }
    std::vector<std::uint8_t> canonical(canonical_size);
    std::size_t written = 0U;
    if (
        resonith_seek_index_build(
            kSource.data(),
            kSource.size(),
            canonical.data(),
            canonical.size(),
            &written
        ) != RESONITH_STATUS_OK
        || written != canonical.size()
    ) {
        __builtin_trap();
    }

    const std::uint8_t* candidate = canonical.data();
    std::size_t candidate_size = canonical.size();
    if (size != 0U && (data[0] & 1U) != 0U) {
        candidate = data + 1U;
        candidate_size = size - 1U;
    } else if (size > 1U) {
        const std::size_t mutation_bytes = std::min(
            size - 1U,
            canonical.size()
        );
        for (std::size_t index = 0U; index < mutation_bytes; ++index) {
            canonical[index] ^= data[index + 1U];
        }
    }

    resonith_seek_index_view view{};
    if (
        resonith_seek_index_open(
            candidate,
            candidate_size,
            kSource.data(),
            kSource.size(),
            &view
        ) != RESONITH_STATUS_OK
    ) {
        return 0;
    }
    if (view.block_count == 0U) {
        return 0;
    }

    const std::uint32_t selected = size == 0U
        ? 0U
        : static_cast<std::uint32_t>(data[size - 1U]) % view.block_count;
    std::vector<std::int64_t> indexed_output(view.block_size);
    std::vector<std::int64_t> direct_output(view.block_size);
    resonith_liftpack_info info{};
    if (
        resonith_liftpack_inspect(
            kSource.data(),
            kSource.size(),
            &info
        ) != RESONITH_STATUS_OK
    ) {
        __builtin_trap();
    }
    std::vector<std::int64_t> scratch(
        resonith_liftpack_required_scratch(&info)
    );
    std::uint32_t indexed_offset = 0U;
    std::size_t indexed_samples = 0U;
    std::uint32_t direct_offset = 0U;
    std::size_t direct_samples = 0U;
    if (
        resonith_seek_index_decode_block(
            &view,
            selected,
            indexed_output.data(),
            indexed_output.size(),
            scratch.data(),
            scratch.size(),
            &indexed_offset,
            &indexed_samples
        ) != RESONITH_STATUS_OK
        || resonith_liftpack_decode_block(
            kSource.data(),
            kSource.size(),
            selected,
            direct_output.data(),
            direct_output.size(),
            scratch.data(),
            scratch.size(),
            &direct_offset,
            &direct_samples
        ) != RESONITH_STATUS_OK
        || indexed_offset != direct_offset
        || indexed_samples != direct_samples
        || !std::equal(
            indexed_output.begin(),
            indexed_output.begin()
                + static_cast<std::ptrdiff_t>(indexed_samples),
            direct_output.begin()
        )
    ) {
        __builtin_trap();
    }
    return 0;
}
