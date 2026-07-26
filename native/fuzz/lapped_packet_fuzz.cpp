#include "resonith/lapped_packet.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::size_t kMaximumElements = 1U << 20U;
constexpr std::uint32_t kMaximumPackets = 64U;

bool bounded(
    const resonith_lapped_packet_requirements& requirements
) noexcept {
    const resonith_lapped_requirements& child = requirements.maximum_child;
    return requirements.packet_count <= kMaximumPackets
        && child.scale_elements <= kMaximumElements
        && child.count_elements <= kMaximumElements
        && child.position_elements <= kMaximumElements
        && child.coefficient_elements <= kMaximumElements
        && child.overlap_elements <= kMaximumElements
        && requirements.maximum_child_output_elements <= kMaximumElements
        && requirements.maximum_logical_output_elements <= kMaximumElements;
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_lapped_packet_session session{};
    resonith_lapped_packet_requirements requirements{};
    if (
        resonith_lapped_packet_open(
            data,
            size,
            &session,
            &requirements
        ) != RESONITH_STATUS_OK
        || !bounded(requirements)
    ) {
        return 0;
    }
    const resonith_lapped_requirements& child = requirements.maximum_child;
    std::vector<std::uint8_t> scales(
        std::max<std::size_t>(1U, child.scale_elements)
    );
    std::vector<std::uint16_t> counts(
        std::max<std::size_t>(1U, child.count_elements)
    );
    std::vector<std::uint16_t> positions(
        std::max<std::size_t>(1U, child.position_elements)
    );
    std::vector<std::int8_t> coefficients(
        std::max<std::size_t>(1U, child.coefficient_elements)
    );
    std::vector<std::int64_t> overlap(
        std::max<std::size_t>(1U, child.overlap_elements)
    );
    std::vector<std::int16_t> child_output(
        requirements.maximum_child_output_elements
    );
    std::vector<std::int16_t> logical_output(
        requirements.maximum_logical_output_elements
    );
    resonith_lapped_workspace workspace = {
        scales.data(),
        child.scale_elements,
        counts.data(),
        child.count_elements,
        positions.data(),
        child.position_elements,
        coefficients.data(),
        child.coefficient_elements,
        overlap.data(),
        child.overlap_elements,
    };
    std::uint32_t expected_start = 0U;
    for (
        std::uint32_t packet = 0U;
        packet < requirements.packet_count;
        ++packet
    ) {
        std::uint32_t logical_start = 1U;
        std::size_t frames_written = 1U;
        if (
            resonith_lapped_packet_decode_next(
                &session,
                &workspace,
                child_output.data(),
                child_output.size(),
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &frames_written
            ) != RESONITH_STATUS_OK
            || logical_start != expected_start
            || frames_written == 0U
        ) {
            __builtin_trap();
        }
        expected_start += static_cast<std::uint32_t>(frames_written);
    }
    if (
        expected_start != requirements.frame_count
        || session.next_frame != requirements.frame_count
    ) {
        __builtin_trap();
    }
    return 0;
}
