#include "resonith/lapped_packet.h"

#include "integrity.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kHeaderBytes = 28U;
constexpr std::size_t kPacketHeaderBytes = 12U;
constexpr std::size_t kDigestBytes = 32U;
constexpr std::size_t kMaximumStreamBytes = 512U << 20U;
constexpr std::uint32_t kMaximumPacketCount = 1U << 20U;

std::uint16_t read_u16(const std::uint8_t* data) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data[0])
        | (static_cast<std::uint16_t>(data[1]) << 8U)
    );
}

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(data[0])
        | (static_cast<std::uint32_t>(data[1]) << 8U)
        | (static_cast<std::uint32_t>(data[2]) << 16U)
        | (static_cast<std::uint32_t>(data[3]) << 24U);
}

bool digest_matches(
    const std::uint8_t* data,
    std::size_t size,
    const std::uint8_t* expected
) noexcept {
    std::array<std::uint8_t, kDigestBytes> actual{};
    resonith::internal::sha256(data, size, actual.data());
    std::uint8_t difference = 0U;
    for (std::size_t index = 0U; index < actual.size(); ++index) {
        difference |= static_cast<std::uint8_t>(
            actual[index] ^ expected[index]
        );
    }
    return difference == 0U;
}

bool checked_product(
    std::size_t left,
    std::size_t right,
    std::size_t* output
) noexcept {
    if (
        output == nullptr
        || (left != 0U
            && right > std::numeric_limits<std::size_t>::max() / left)
    ) {
        return false;
    }
    *output = left * right;
    return true;
}

resonith_status validate_child(
    const std::uint8_t* child,
    std::size_t child_size,
    std::uint32_t logical_count,
    const resonith_lapped_packet_session& session,
    resonith_lapped_requirements* child_requirements
) noexcept {
    resonith_status status = resonith_lapped_inspect(
        child,
        child_size,
        child_requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        logical_count
            > std::numeric_limits<std::uint32_t>::max()
                - 2U * session.half_window
        || child_requirements->sample_rate != session.sample_rate
        || child_requirements->frame_count
            != logical_count + 2U * session.half_window
        || child_requirements->half_window != session.half_window
        || child_requirements->band_count != session.band_count
        || child_requirements->output_channels != session.output_channels
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    return RESONITH_STATUS_OK;
}

resonith_status parse_packet(
    const resonith_lapped_packet_session& session,
    std::size_t offset,
    std::uint32_t expected_start,
    std::uint32_t* logical_count,
    const std::uint8_t** child,
    std::size_t* child_size,
    std::size_t* next_offset
) noexcept {
    if (
        logical_count == nullptr
        || child == nullptr
        || child_size == nullptr
        || next_offset == nullptr
        || offset > session.data_size
        || session.data_size - offset < kPacketHeaderBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::uint8_t* packet = session.data + offset;
    const std::uint32_t logical_start = read_u32(packet);
    const std::uint32_t count = read_u32(packet + 4U);
    const std::uint32_t bytes = read_u32(packet + 8U);
    const std::size_t remaining =
        session.data_size - offset - kPacketHeaderBytes;
    if (
        logical_start != expected_start
        || count == 0U
        || count > session.packet_frames
        || expected_start > session.frame_count
        || count > session.frame_count - expected_start
        || bytes == 0U
        || static_cast<std::size_t>(bytes) > remaining
        || remaining - bytes < kDigestBytes
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::size_t authenticated_bytes =
        kPacketHeaderBytes + static_cast<std::size_t>(bytes);
    const std::uint8_t* digest = packet + authenticated_bytes;
    if (!digest_matches(packet, authenticated_bytes, digest)) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }
    *logical_count = count;
    *child = packet + kPacketHeaderBytes;
    *child_size = bytes;
    *next_offset = offset + authenticated_bytes + kDigestBytes;
    return RESONITH_STATUS_OK;
}

void maximize_child(
    resonith_lapped_requirements* maximum,
    const resonith_lapped_requirements& child
) noexcept {
    maximum->transform_frame_count = std::max(
        maximum->transform_frame_count,
        child.transform_frame_count
    );
    maximum->frame_count = std::max(
        maximum->frame_count,
        child.frame_count
    );
    maximum->scale_elements = std::max(
        maximum->scale_elements,
        child.scale_elements
    );
    maximum->count_elements = std::max(
        maximum->count_elements,
        child.count_elements
    );
    maximum->position_elements = std::max(
        maximum->position_elements,
        child.position_elements
    );
    maximum->coefficient_elements = std::max(
        maximum->coefficient_elements,
        child.coefficient_elements
    );
    maximum->overlap_elements = std::max(
        maximum->overlap_elements,
        child.overlap_elements
    );
    maximum->output_elements = std::max(
        maximum->output_elements,
        child.output_elements
    );
}

}  // namespace

extern "C" resonith_status resonith_lapped_packet_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_lapped_packet_session* session,
    resonith_lapped_packet_requirements* requirements
) {
    if (data == nullptr || session == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *session = {};
    *requirements = {};
    if (
        data_size < kHeaderBytes + kDigestBytes
        || data_size > kMaximumStreamBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (std::memcmp(data, "LPS1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4] != 1U) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (data[5] != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (!digest_matches(data, kHeaderBytes, data + kHeaderBytes)) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }
    resonith_lapped_packet_session parsed = {
        data,
        data_size,
        kHeaderBytes + kDigestBytes,
        0U,
        0U,
        read_u32(data + 8U),
        read_u32(data + 12U),
        read_u32(data + 20U),
        read_u32(data + 24U),
        read_u16(data + 16U),
        read_u16(data + 18U),
        read_u16(data + 6U),
        0U,
    };
    if (
        parsed.sample_rate == 0U
        || parsed.frame_count == 0U
        || parsed.output_channels == 0U
        || parsed.output_channels > 8U
        || parsed.half_window < 32U
        || parsed.half_window > 1024U
        || (parsed.half_window & (parsed.half_window - 1U)) != 0U
        || parsed.band_count == 0U
        || parsed.band_count > 64U
        || parsed.packet_frames < parsed.half_window
        || parsed.packet_frames % parsed.half_window != 0U
        || parsed.packet_count == 0U
        || parsed.packet_count > kMaximumPacketCount
        || parsed.packet_count
            != parsed.frame_count / parsed.packet_frames
                + (parsed.frame_count % parsed.packet_frames != 0U ? 1U : 0U)
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    resonith_lapped_requirements maximum_child{};
    maximum_child.sample_rate = parsed.sample_rate;
    maximum_child.half_window = parsed.half_window;
    maximum_child.band_count = parsed.band_count;
    maximum_child.output_channels = parsed.output_channels;
    std::size_t offset = parsed.next_offset;
    std::uint32_t expected_start = 0U;
    std::size_t maximum_logical_output = 0U;
    for (
        std::uint32_t packet_index = 0U;
        packet_index < parsed.packet_count;
        ++packet_index
    ) {
        std::uint32_t logical_count = 0U;
        const std::uint8_t* child = nullptr;
        std::size_t child_size = 0U;
        std::size_t next_offset = 0U;
        resonith_status status = parse_packet(
            parsed,
            offset,
            expected_start,
            &logical_count,
            &child,
            &child_size,
            &next_offset
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        resonith_lapped_requirements child_requirements{};
        status = validate_child(
            child,
            child_size,
            logical_count,
            parsed,
            &child_requirements
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        maximize_child(&maximum_child, child_requirements);
        std::size_t logical_elements = 0U;
        if (
            !checked_product(
                logical_count,
                parsed.output_channels,
                &logical_elements
            )
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        maximum_logical_output = std::max(
            maximum_logical_output,
            logical_elements
        );
        expected_start += logical_count;
        offset = next_offset;
    }
    if (offset != data_size || expected_start != parsed.frame_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    *session = parsed;
    requirements->sample_rate = parsed.sample_rate;
    requirements->frame_count = parsed.frame_count;
    requirements->packet_frames = parsed.packet_frames;
    requirements->packet_count = parsed.packet_count;
    requirements->half_window = parsed.half_window;
    requirements->band_count = parsed.band_count;
    requirements->output_channels = parsed.output_channels;
    requirements->maximum_child = maximum_child;
    requirements->maximum_child_output_elements =
        maximum_child.output_elements;
    requirements->maximum_logical_output_elements =
        maximum_logical_output;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_lapped_packet_decode_next(
    resonith_lapped_packet_session* session,
    const resonith_lapped_workspace* workspace,
    std::int16_t* child_output,
    std::size_t child_output_capacity,
    std::int16_t* logical_output,
    std::size_t logical_output_capacity,
    std::uint32_t* logical_start,
    std::size_t* frames_written
) {
    if (
        session == nullptr
        || workspace == nullptr
        || child_output == nullptr
        || logical_output == nullptr
        || logical_start == nullptr
        || frames_written == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *logical_start = 0U;
    *frames_written = 0U;
    if (session->next_packet >= session->packet_count) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    std::uint32_t logical_count = 0U;
    const std::uint8_t* child = nullptr;
    std::size_t child_size = 0U;
    std::size_t next_offset = 0U;
    resonith_status status = parse_packet(
        *session,
        session->next_offset,
        session->next_frame,
        &logical_count,
        &child,
        &child_size,
        &next_offset
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    resonith_lapped_requirements child_requirements{};
    status = validate_child(
        child,
        child_size,
        logical_count,
        *session,
        &child_requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    std::size_t logical_elements = 0U;
    if (
        !checked_product(
            logical_count,
            session->output_channels,
            &logical_elements
        )
        || child_output_capacity < child_requirements.output_elements
        || logical_output_capacity < logical_elements
    ) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    std::size_t child_frames = 0U;
    status = resonith_lapped_decode(
        child,
        child_size,
        workspace,
        child_output,
        child_output_capacity,
        &child_frames
    );
    if (
        status != RESONITH_STATUS_OK
        || child_frames != child_requirements.frame_count
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }
    const std::size_t trim_elements =
        static_cast<std::size_t>(session->half_window)
        * session->output_channels;
    std::copy_n(
        child_output + static_cast<std::ptrdiff_t>(trim_elements),
        logical_elements,
        logical_output
    );
    *logical_start = session->next_frame;
    *frames_written = logical_count;
    session->next_offset = next_offset;
    ++session->next_packet;
    session->next_frame += logical_count;
    return RESONITH_STATUS_OK;
}
