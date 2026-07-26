#include "resonith/lapped_finite.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::size_t kMaximumWorkspaceElements = 1U << 20U;

bool bounded(
    const resonith_lapped_finite_requirements& requirements
) noexcept {
    return (
        requirements.scale_elements <= kMaximumWorkspaceElements
        && requirements.count_elements <= kMaximumWorkspaceElements
        && requirements.position_elements <= kMaximumWorkspaceElements
        && requirements.coefficient_elements <= kMaximumWorkspaceElements
    );
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    constexpr std::array<std::uint16_t, 6U> kHalfWindows = {
        32U, 64U, 128U, 256U, 512U, 1024U
    };
    for (const std::uint16_t half_window : kHalfWindows) {
        resonith_lapped_finite_requirements requirements{};
        if (
            resonith_lapped_finite_inspect(
                data,
                size,
                half_window,
                &requirements
            ) != RESONITH_STATUS_OK
            || !bounded(requirements)
        ) {
            continue;
        }
        std::vector<std::uint8_t> scales(requirements.scale_elements);
        std::vector<std::uint16_t> counts(requirements.count_elements);
        std::vector<std::uint16_t> positions(requirements.position_elements);
        std::vector<std::int8_t> coefficients(
            requirements.coefficient_elements
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
            nullptr,
            0U,
        };
        (void)resonith_lapped_finite_decode(
            data,
            size,
            half_window,
            &workspace
        );
    }
    return 0;
}
