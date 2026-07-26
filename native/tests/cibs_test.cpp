#include "resonith/cibs.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::int8_t, 128> kProjection = {
    -10, 7, -7, 10, -4, 13, -1, -15, 2, -12, 5, -9, 8, -6, 11, -3,
    14, 0, -14, 3, -11, 6, -8, 9, -5, 12, -2, 15, 1, -13, 4, -10,
    7, -7, 10, -4, 13, -1, -15, 2, -12, 5, -9, 8, -6, 11, -3, 14,
    0, -14, 3, -11, 6, -8, 9, -5, 12, -2, 15, 1, -13, 4, -10, 7,
    -7, 10, -4, 13, -1, -15, 2, -12, 5, -9, 8, -6, 11, -3, 14, 0,
    -14, 3, -11, 6, -8, 9, -5, 12, -2, 15, 1, -13, 4, -10, 7, -7,
    10, -4, 13, -1, -15, 2, -12, 5, -9, 8, -6, 11, -3, 14, 0, -14,
    3, -11, 6, -8, 9, -5, 12, -2, 15, 1, -13, 4, -10, 7, -7, 10,
};
constexpr std::array<std::int32_t, 16> kProjectionBias = {
    -37, -8, 21, -47, -18, 11, 40, -28,
    1, 30, -38, -9, 20, -48, -19, 10,
};
constexpr std::array<std::int8_t, 10> kKernelZero = {
    1, 2, 10, 2, 1,
    1, 3, 8, 3, 1,
};
constexpr std::array<std::int8_t, 6> kKernelOne = {
    1, 6, 1,
    1, 6, 1,
};
constexpr std::array<std::int8_t, 8> kLatent = {
    12, -7, 3, 19, -22, 6, 1, -4,
};
constexpr std::array<std::int8_t, 32> kAdapterU = {
    -3, -2, -1, 0, 1, 2, 3, -3,
    -2, -1, 0, 1, 2, 3, -3, -2,
    -1, 0, 1, 2, 3, -3, -2, -1,
    0, 1, 2, 3, -3, -2, -1, 0,
};
constexpr std::array<std::int8_t, 16> kAdapterV = {
    1, -1, 2, 0, 1, -2, 1, 0,
    0, 1, -1, 2, -2, 1, 0, 1,
};
constexpr std::array<std::uint8_t, 32> kPlainDigest = {
    0x2c, 0x90, 0x1e, 0x3a, 0x32, 0xe0, 0x42, 0xa9,
    0x60, 0xd0, 0x6d, 0x71, 0xdc, 0x59, 0x61, 0x17,
    0x1d, 0x7b, 0x63, 0x04, 0xc5, 0xe9, 0x84, 0xf8,
    0x92, 0x90, 0x4b, 0x34, 0xef, 0x80, 0x78, 0x2f,
};
constexpr std::array<std::uint8_t, 32> kAdapterDigest = {
    0xea, 0x7d, 0x2f, 0xaa, 0xcc, 0x01, 0x17, 0x77,
    0xe2, 0xa8, 0xf3, 0x1c, 0xc3, 0x37, 0x40, 0x33,
    0x81, 0xac, 0xc1, 0xe5, 0xcf, 0x4f, 0x5b, 0xf6,
    0x06, 0x4a, 0xd6, 0x16, 0x6e, 0xa6, 0x9a, 0xa1,
};
constexpr std::array<std::uint8_t, 32> kCorrectionDigest = {
    0xbf, 0x52, 0x45, 0x37, 0x19, 0xbd, 0x7b, 0x60,
    0xb9, 0x96, 0xfc, 0xd2, 0xa9, 0x22, 0x08, 0x6c,
    0x57, 0x96, 0x79, 0x9a, 0xda, 0x90, 0xb6, 0xb8,
    0x49, 0x4b, 0x16, 0xb9, 0x27, 0xd4, 0x37, 0x7d,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    constexpr char kModelId[] = "CIBS0-DEMO-NOT-NORMATIVE";
    const std::array<resonith_cibs_refinement_stage, 2> stages = {{
        {kKernelZero.data(), 5U, 4U, 0U},
        {kKernelOne.data(), 3U, 3U, 0U},
    }};
    const resonith_cibs_model model = {
        reinterpret_cast<const std::uint8_t*>(kModelId),
        sizeof(kModelId) - 1U,
        kProjection.data(),
        kProjectionBias.data(),
        stages.data(),
        2U,
        8U,
        8U,
        3U,
        2U,
        0U,
    };

    resonith_cibs_info info{};
    if (!expect(
            resonith_cibs_inspect_model(&model, nullptr, &info)
                == RESONITH_STATUS_OK
                && info.basis_channels == 2U
                && info.output_length == 32U
                && info.output_elements == 64U
                && info.scratch_elements == 128U,
            "CIBS model inspection"
        )) {
        return 1;
    }

    std::array<std::int16_t, 64> output{};
    std::array<std::int64_t, 130> scratch{};
    std::array<std::uint8_t, 32> digest{};
    std::uint64_t macs = 0U;
    if (!expect(
            resonith_cibs_materialize(
                &model,
                kLatent.data(),
                kLatent.size(),
                nullptr,
                nullptr,
                0U,
                kPlainDigest.data(),
                digest.data(),
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &macs
            ) == RESONITH_STATUS_OK
                && digest == kPlainDigest
                && macs == 480U
                && output.front() == 31
                && output.back() == 37,
            "plain CIBS materialization"
        )) {
        return 1;
    }

    // Hash failure must leave the caller's committed Basis untouched.
    output.fill(-1234);
    std::array<std::uint8_t, 32> wrong_digest{};
    if (!expect(
            resonith_cibs_materialize(
                &model,
                kLatent.data(),
                kLatent.size(),
                nullptr,
                nullptr,
                0U,
                wrong_digest.data(),
                digest.data(),
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &macs
            ) == RESONITH_STATUS_HASH_MISMATCH
                && std::all_of(
                    output.begin(),
                    output.end(),
                    [](std::int16_t value) { return value == -1234; }
                ),
            "CIBS atomic hash guard"
        )) {
        return 1;
    }

    const resonith_cibs_adapter adapter = {
        kAdapterU.data(),
        kAdapterV.data(),
        2U,
        1U,
        1U,
        0U,
    };
    if (!expect(
            resonith_cibs_inspect_model(&model, &adapter, &info)
                == RESONITH_STATUS_OK
                && info.scratch_elements == 130U,
            "CIBS adapter inspection"
        )) {
        return 1;
    }
    if (!expect(
            resonith_cibs_materialize(
                &model,
                kLatent.data(),
                kLatent.size(),
                &adapter,
                nullptr,
                0U,
                kAdapterDigest.data(),
                digest.data(),
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &macs
            ) == RESONITH_STATUS_OK
                && digest == kAdapterDigest
                && macs == 528U,
            "adapted CIBS materialization"
        )) {
        return 1;
    }

    std::array<std::int32_t, 64> correction{};
    correction.fill(100'000);
    if (!expect(
            resonith_cibs_materialize(
                &model,
                kLatent.data(),
                kLatent.size(),
                nullptr,
                correction.data(),
                correction.size(),
                kCorrectionDigest.data(),
                digest.data(),
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &macs
            ) == RESONITH_STATUS_OK
                && digest == kCorrectionDigest
                && std::all_of(
                    output.begin(),
                    output.end(),
                    [](std::int16_t value) { return value == 32767; }
                ),
            "CIBS objective correction saturation"
        )) {
        return 1;
    }
    return 0;
}
