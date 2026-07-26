#ifndef RESONITH_INTERNAL_LAPPED_H
#define RESONITH_INTERNAL_LAPPED_H

#include "resonith/lapped.h"
#include "resonith/status.h"

#include <cstddef>
#include <cstdint>

namespace resonith::internal {

/*
 * Decodes one CRC-excluded LPS4 compact entropy record into caller-owned
 * fields. The inherited shape was authenticated by the sequence envelope.
 */
resonith_status lapped_compact_fields_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint32_t sample_rate,
    std::uint32_t sample_count,
    std::uint32_t transform_frames,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    const resonith_lapped_workspace& workspace,
    resonith_lapped_requirements* requirements
) noexcept;

/*
 * Renders current single-owner transform fields plus, when non-null, the first
 * transform frame from the next record. Validation completes before PCM write.
 */
resonith_status lapped_render_chained(
    const resonith_lapped_requirements& current_requirements,
    const resonith_lapped_workspace& current_workspace,
    const resonith_lapped_requirements* lookahead_requirements,
    const resonith_lapped_workspace* lookahead_workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* frames_written
) noexcept;

}  // namespace resonith::internal

#endif
