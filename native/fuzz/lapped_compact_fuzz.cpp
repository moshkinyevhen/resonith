#include "resonith/lapped_compact.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::size_t kMaximumElements = 1U << 20U;
constexpr std::uint32_t kMaximumPackets = 64U;
constexpr std::size_t kSequenceHeaderBytes = 60U;
constexpr std::size_t kCompactDescriptorBytes = 27U;
constexpr std::size_t kRecordCrcBytes = 4U;

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(data[0])
        | (static_cast<std::uint32_t>(data[1]) << 8U)
        | (static_cast<std::uint32_t>(data[2]) << 16U)
        | (static_cast<std::uint32_t>(data[3]) << 24U);
}

std::size_t compact_record_size(const std::uint8_t* data) noexcept {
    std::size_t size = kCompactDescriptorBytes + kRecordCrcBytes;
    for (std::size_t field = 0U; field < 4U; ++field) {
        size += (
            static_cast<std::size_t>(read_u32(data + 11U + 4U * field))
            + 7U
        ) / 8U;
    }
    return size;
}

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
    std::vector<std::int16_t> stateless_output(output.size());

    resonith_lapped_compact_sequence sequence{};
    if (
        resonith_lapped_compact_sequence_open(
            data,
            kSequenceHeaderBytes,
            &sequence
        ) != RESONITH_STATUS_OK
    ) {
        __builtin_trap();
    }
    resonith_lapped_compact_requirements header_requirements{};
    const resonith_status header_requirement_status =
        resonith_lapped_compact_sequence_requirements(
            &sequence,
            &header_requirements
        );
    if (
        header_requirement_status == RESONITH_STATUS_OK
        && (
            header_requirements.maximum_current.scale_elements
                < requirements.maximum_current.scale_elements
            || header_requirements.maximum_current.count_elements
                < requirements.maximum_current.count_elements
            || header_requirements.maximum_current.position_elements
                < requirements.maximum_current.position_elements
            || header_requirements.maximum_current.coefficient_elements
                < requirements.maximum_current.coefficient_elements
            || header_requirements.maximum_current.overlap_elements
                < requirements.maximum_current.overlap_elements
            || header_requirements.maximum_lookahead.scale_elements
                < requirements.maximum_lookahead.scale_elements
            || header_requirements.maximum_lookahead.count_elements
                < requirements.maximum_lookahead.count_elements
            || header_requirements.maximum_lookahead.position_elements
                < requirements.maximum_lookahead.position_elements
            || header_requirements.maximum_lookahead.coefficient_elements
                < requirements.maximum_lookahead.coefficient_elements
            || header_requirements.maximum_logical_output_elements
                < requirements.maximum_logical_output_elements
        )
    ) {
        __builtin_trap();
    }
    std::vector<std::size_t> record_offsets;
    std::vector<std::size_t> record_sizes;
    record_offsets.reserve(requirements.packet_count);
    record_sizes.reserve(requirements.packet_count);
    std::size_t record_offset = kSequenceHeaderBytes;
    for (
        std::uint32_t packet = 0U;
        packet < requirements.packet_count;
        ++packet
    ) {
        if (
            record_offset > size
            || size - record_offset
                < kCompactDescriptorBytes + kRecordCrcBytes
        ) {
            __builtin_trap();
        }
        const std::size_t record_size =
            compact_record_size(data + record_offset);
        if (record_size > size - record_offset) {
            __builtin_trap();
        }
        record_offsets.push_back(record_offset);
        record_sizes.push_back(record_size);
        record_offset += record_size;
    }
    if (record_offset != size) {
        __builtin_trap();
    }

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
        std::uint32_t stateless_start = 1U;
        std::size_t stateless_frames = 1U;
        const bool final_packet =
            packet + 1U == requirements.packet_count;
        if (
            resonith_lapped_compact_decode_record_pair(
                &sequence,
                packet,
                data + record_offsets[packet],
                record_sizes[packet],
                final_packet ? nullptr : data + record_offsets[packet + 1U],
                final_packet ? 0U : record_sizes[packet + 1U],
                &current_workspace,
                final_packet ? nullptr : &lookahead_workspace,
                stateless_output.data(),
                stateless_output.size(),
                &stateless_start,
                &stateless_frames
            ) != RESONITH_STATUS_OK
            || stateless_start != logical_start
            || stateless_frames != frames_written
            || !std::equal(
                output.begin(),
                output.begin()
                    + static_cast<std::ptrdiff_t>(
                        frames_written * sequence.output_channels
                    ),
                stateless_output.begin()
            )
        ) {
            __builtin_trap();
        }
        if (!final_packet) {
            std::uint32_t prefix_start = 1U;
            std::size_t prefix_frames = 1U;
            if (
                resonith_lapped_compact_decode_record_prefix(
                    &sequence,
                    packet,
                    data + record_offsets[packet],
                    record_sizes[packet],
                    &current_workspace,
                    stateless_output.data(),
                    stateless_output.size(),
                    &prefix_start,
                    &prefix_frames
                ) != RESONITH_STATUS_OK
                || prefix_start != logical_start
                || prefix_frames + sequence.half_window != frames_written
                || !std::equal(
                    output.begin(),
                    output.begin()
                        + static_cast<std::ptrdiff_t>(
                            prefix_frames * sequence.output_channels
                        ),
                    stateless_output.begin()
                )
            ) {
                __builtin_trap();
            }
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
