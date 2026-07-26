#include "resonith/lapped_compact.h"

#include <cstddef>
#include <cstdint>

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
    return 0;
}
