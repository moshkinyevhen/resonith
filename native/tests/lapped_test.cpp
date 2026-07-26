#include "resonith/lapped.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

#include "lapped_vector.inc"

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    resonith_lapped_requirements requirements{};
    if (!expect(
            resonith_lapped_inspect(
                kLappedStream.data(),
                kLappedStream.size(),
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.sample_rate == 48000U
                && requirements.frame_count == 96U
                && requirements.transform_frame_count == 4U
                && requirements.half_window == 32U
                && requirements.band_count == 4U
                && requirements.coefficients_per_frame == 8U
                && requirements.output_channels == 2U
                && requirements.scale_elements == 32U
                && requirements.position_elements == 64U
                && requirements.coefficient_elements == 64U
                && requirements.overlap_elements == 160U
                && requirements.output_elements == 192U,
            "fixed bounded LPF1 inspect"
        )) {
        return 1;
    }

    std::array<std::uint8_t, 32> scales{};
    std::array<std::uint16_t, 64> positions{};
    std::array<std::int8_t, 64> coefficients{};
    std::array<std::int64_t, 160> overlap{};
    resonith_lapped_workspace workspace = {
        scales.data(),
        scales.size(),
        positions.data(),
        positions.size(),
        coefficients.data(),
        coefficients.size(),
        overlap.data(),
        overlap.size(),
    };
    std::array<std::int16_t, 192> output{};
    std::size_t written = 0U;
    if (!expect(
            resonith_lapped_decode(
                kLappedStream.data(),
                kLappedStream.size(),
                &workspace,
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == 96U
                && output == kExpectedLappedPcm,
            "Python and native fixed LPF1 PCM parity"
        )) {
        return 1;
    }

    auto corrupted = kLappedStream;
    corrupted.back() ^= 1U;
    if (!expect(
            resonith_lapped_inspect(
                corrupted.data(),
                corrupted.size(),
                &requirements
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "LPF1 section integrity"
        )) {
        return 1;
    }

    output.fill(1234);
    workspace.position_capacity = positions.size() - 1U;
    written = 9U;
    if (!expect(
            resonith_lapped_decode(
                kLappedStream.data(),
                kLappedStream.size(),
                &workspace,
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_SCRATCH_TOO_SMALL
                && written == 0U
                && std::all_of(
                    output.begin(),
                    output.end(),
                    [](std::int16_t value) { return value == 1234; }
                ),
            "LPF1 workspace rejection is output-atomic"
        )) {
        return 1;
    }
    return 0;
}
