#include "resonith/lapped_compact.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::size_t kMaximumElements = 1U << 20U;
constexpr std::uint32_t kMaximumPackets = 64U;

bool bounded(
    const resonith_lapped_compact_requirements& requirements
) noexcept {
    const resonith_lapped_requirements& current =
        requirements.maximum_current;
    const resonith_lapped_requirements& lookahead =
        requirements.maximum_lookahead;
    return requirements.packet_count <= kMaximumPackets
        && current.scale_elements <= kMaximumElements
        && current.count_elements <= kMaximumElements
        && current.position_elements <= kMaximumElements
        && current.coefficient_elements <= kMaximumElements
        && current.overlap_elements <= kMaximumElements
        && lookahead.scale_elements <= kMaximumElements
        && lookahead.count_elements <= kMaximumElements
        && lookahead.position_elements <= kMaximumElements
        && lookahead.coefficient_elements <= kMaximumElements
        && requirements.maximum_logical_output_elements <= kMaximumElements;
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_lapped_compact_session session{};
    resonith_lapped_compact_requirements requirements{};
    if (
        resonith_lapped_compact_open(
            data,
            size,
            &session,
            &requirements
        ) != RESONITH_STATUS_OK
        || !bounded(requirements)
    ) {
        return 0;
    }
    if (
        session.data != data
        || session.data_size != size
        || session.next_packet != 0U
        || session.next_frame != 0U
        || session.frame_count != requirements.frame_count
        || session.packet_count != requirements.packet_count
    ) {
        __builtin_trap();
    }

    const resonith_lapped_requirements& current =
        requirements.maximum_current;
    const resonith_lapped_requirements& lookahead =
        requirements.maximum_lookahead;
    std::vector<std::uint8_t> current_scales(
        std::max<std::size_t>(1U, current.scale_elements)
    );
    std::vector<std::uint16_t> current_counts(
        std::max<std::size_t>(1U, current.count_elements)
    );
    std::vector<std::uint16_t> current_positions(
        std::max<std::size_t>(1U, current.position_elements)
    );
    std::vector<std::int8_t> current_coefficients(
        std::max<std::size_t>(1U, current.coefficient_elements)
    );
    std::vector<std::int64_t> current_overlap(
        std::max<std::size_t>(1U, current.overlap_elements)
    );
    resonith_lapped_workspace current_workspace = {
        current_scales.data(),
        current.scale_elements,
        current_counts.data(),
        current.count_elements,
        current_positions.data(),
        current.position_elements,
        current_coefficients.data(),
        current.coefficient_elements,
        current_overlap.data(),
        current.overlap_elements,
    };

    std::vector<std::uint8_t> lookahead_scales(
        std::max<std::size_t>(1U, lookahead.scale_elements)
    );
    std::vector<std::uint16_t> lookahead_counts(
        std::max<std::size_t>(1U, lookahead.count_elements)
    );
    std::vector<std::uint16_t> lookahead_positions(
        std::max<std::size_t>(1U, lookahead.position_elements)
    );
    std::vector<std::int8_t> lookahead_coefficients(
        std::max<std::size_t>(1U, lookahead.coefficient_elements)
    );
    resonith_lapped_workspace lookahead_workspace = {
        lookahead_scales.data(),
        lookahead.scale_elements,
        lookahead_counts.data(),
        lookahead.count_elements,
        lookahead_positions.data(),
        lookahead.position_elements,
        lookahead_coefficients.data(),
        lookahead.coefficient_elements,
        nullptr,
        0U,
    };
    std::vector<std::int16_t> output(
        requirements.maximum_logical_output_elements
    );

    std::uint32_t expected_start = 0U;
    for (
        std::uint32_t packet = 0U;
        packet < requirements.packet_count;
        ++packet
    ) {
        std::uint32_t logical_start = 1U;
        std::size_t frames_written = 1U;
        if (
            resonith_lapped_compact_decode_next(
                &session,
                &current_workspace,
                &lookahead_workspace,
                output.data(),
                output.size(),
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
