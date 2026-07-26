#include "resonith/seek.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

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

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    std::size_t required = 0U;
    if (!expect(
            resonith_seek_index_required_size(
                kSource.data(),
                kSource.size(),
                &required
            ) == RESONITH_STATUS_OK
                && required == 228U,
            "RSI1 exact required size"
        )) {
        return 1;
    }

    std::array<std::uint8_t, 228> sidecar{};
    std::size_t written = 0U;
    if (!expect(
            resonith_seek_index_build(
                kSource.data(),
                kSource.size(),
                sidecar.data(),
                sidecar.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == sidecar.size(),
            "build canonical RSI1 sidecar"
        )) {
        return 1;
    }

    resonith_seek_index_view view{};
    if (!expect(
            resonith_seek_index_open(
                sidecar.data(),
                sidecar.size(),
                kSource.data(),
                kSource.size(),
                &view
            ) == RESONITH_STATUS_OK
                && view.sample_count == 64U
                && view.block_count == 4U
                && view.block_size == 16U,
            "verify source-bound RSI1 sidecar"
        )) {
        return 1;
    }

    resonith_liftpack_block_info entry{};
    if (!expect(
            resonith_seek_index_get_block(&view, 2U, &entry)
                == RESONITH_STATUS_OK
                && entry.sample_offset == 32U
                && entry.sample_count == 16U
                && entry.transform == 2U,
            "constant-time RSI1 entry lookup"
        )) {
        return 1;
    }

    std::array<std::int64_t, 16> output{};
    std::array<std::int64_t, 32> scratch{};
    std::uint32_t sample_offset = 99U;
    std::size_t samples_written = 99U;
    if (!expect(
            resonith_seek_index_decode_block(
                &view,
                2U,
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &sample_offset,
                &samples_written
            ) == RESONITH_STATUS_OK
                && sample_offset == 32U
                && samples_written == output.size(),
            "decode one verified indexed block"
        )) {
        return 1;
    }
    for (std::int64_t index = 0; index < 16; ++index) {
        if (!expect(
                output[static_cast<std::size_t>(index)]
                    == index * index - 50,
                "indexed block exact PCM"
            )) {
            return 1;
        }
    }

    auto damaged = sidecar;
    damaged[80] ^= 1U;
    view.sample_count = 99U;
    if (!expect(
            resonith_seek_index_open(
                damaged.data(),
                damaged.size(),
                kSource.data(),
                kSource.size(),
                &view
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH
                && view.sample_count == 0U
                && view.index_data == nullptr,
            "damaged sidecar is rejected atomically"
        )) {
        return 1;
    }
    return 0;
}
