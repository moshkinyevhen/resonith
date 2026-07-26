#include "resonith/lapped.h"

#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace {

constexpr std::size_t kMaximumWorkspaceElements = 1U << 20U;
constexpr std::size_t kMaximumSynthesisMacs = 1U << 18U;

bool bounded(const resonith_lapped_requirements& requirements) noexcept {
    if (
        requirements.scale_elements > kMaximumWorkspaceElements
        || requirements.count_elements > kMaximumWorkspaceElements
        || requirements.position_elements > kMaximumWorkspaceElements
        || requirements.coefficient_elements > kMaximumWorkspaceElements
        || requirements.overlap_elements > kMaximumWorkspaceElements
        || requirements.output_elements > kMaximumWorkspaceElements
    ) {
        return false;
    }
    if (
        requirements.position_elements
        > std::numeric_limits<std::size_t>::max()
            / (2U * requirements.half_window)
    ) {
        return false;
    }
    return (
        requirements.position_elements
        * 2U
        * requirements.half_window
        <= kMaximumSynthesisMacs
    );
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_lapped_requirements requirements{};
    if (
        resonith_lapped_inspect(data, size, &requirements)
        != RESONITH_STATUS_OK
        || !bounded(requirements)
    ) {
        return 0;
    }

    std::vector<std::uint8_t> scales(requirements.scale_elements);
    std::vector<std::uint16_t> counts(requirements.count_elements);
    std::vector<std::uint16_t> positions(requirements.position_elements);
    std::vector<std::int8_t> coefficients(
        requirements.coefficient_elements
    );
    std::vector<std::int64_t> overlap(requirements.overlap_elements);
    std::vector<std::int16_t> output(
        requirements.output_elements,
        static_cast<std::int16_t>(0x4A4A)
    );
    resonith_lapped_workspace workspace = {
        scales.data(),
        scales.size(),
        counts.data(),
        counts.size(),
        positions.data(),
        positions.size(),
        coefficients.data(),
        coefficients.size(),
        overlap.data(),
        overlap.size(),
    };
    std::size_t frames_written = 1U;
    const resonith_status status = resonith_lapped_decode(
        data,
        size,
        &workspace,
        output.data(),
        output.size(),
        &frames_written
    );
    if (
        (status == RESONITH_STATUS_OK
            && frames_written != requirements.frame_count)
        || (status != RESONITH_STATUS_OK && frames_written != 0U)
    ) {
        __builtin_trap();
    }
    return 0;
}
