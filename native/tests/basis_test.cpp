#include "resonith/basis.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::int16_t, 16> kExpectedBasis = {
    -30000, -20000, -10000, 0, 10000, 20000, 30000, 20000,
    10000, 0, -10000, -20000, -30000, -15000, 0, 15000,
};
constexpr std::array<std::uint8_t, 40> kBrawPayload = {
    0x01, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00,
    0xd0, 0x8a, 0xe0, 0xb1, 0xf0, 0xd8, 0x00, 0x00,
    0x10, 0x27, 0x20, 0x4e, 0x30, 0x75, 0x20, 0x4e,
    0x10, 0x27, 0x00, 0x00, 0xf0, 0xd8, 0xe0, 0xb1,
    0xd0, 0x8a, 0x68, 0xc5, 0x00, 0x00, 0x98, 0x3a,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    resonith_raw_basis_info info{};
    if (!expect(
            resonith_raw_basis_inspect(
                kBrawPayload.data(),
                kBrawPayload.size(),
                &info
            ) == RESONITH_STATUS_OK
                && info.channels == 1U
                && info.samples_per_channel == 16U
                && info.total_elements == 16U,
            "BRAW inspection"
        )) {
        return 1;
    }

    std::array<std::int16_t, 16> output{};
    std::size_t written = 0U;
    if (!expect(
            resonith_raw_basis_decode(
                kBrawPayload.data(),
                kBrawPayload.size(),
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == output.size()
                && output == kExpectedBasis,
            "BRAW decoding"
        )) {
        return 1;
    }
    if (!expect(
            resonith_raw_basis_inspect(
                kBrawPayload.data(),
                kBrawPayload.size() - 1U,
                &info
            ) == RESONITH_STATUS_TRUNCATED,
            "BRAW truncation rejection"
        )) {
        return 1;
    }
    auto unsupported = kBrawPayload;
    unsupported[2] = 1U;
    if (!expect(
            resonith_raw_basis_inspect(
                unsupported.data(),
                unsupported.size(),
                &info
            ) == RESONITH_STATUS_UNSUPPORTED_FEATURE,
            "BRAW feature rejection"
        )) {
        return 1;
    }
    written = 99U;
    if (!expect(
            resonith_raw_basis_decode(
                kBrawPayload.data(),
                kBrawPayload.size(),
                output.data(),
                output.size() - 1U,
                &written
            ) == RESONITH_STATUS_OUTPUT_TOO_SMALL
                && written == 0U,
            "BRAW output bound"
        )) {
        return 1;
    }
    return 0;
}
