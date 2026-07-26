#include "resonith/lapped_compact.h"

#include "integrity.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kHeaderBytes = 28U;
constexpr std::size_t kDigestBytes = 32U;
constexpr std::size_t kCompactDescriptorBytes = 27U;
constexpr std::size_t kRecordCrcBytes = 4U;
constexpr std::size_t kMaximumStreamBytes = 512U << 20U;
constexpr std::uint32_t kMaximumPacketCount = 1U << 20U;
constexpr std::uint32_t kMaximumSymbols = 64U << 20U;
constexpr std::uint8_t kEntropyRice = 0U;
constexpr std::uint8_t kEntropyPacked = 1U;
constexpr std::uint8_t kMaximumRiceParameter = 20U;

struct compact_record_view {
    const std::uint8_t* data = nullptr;
    std::size_t size = 0U;
    std::size_t next_offset = 0U;
    std::uint32_t logical_count = 0U;
    resonith_lapped_requirements requirements{};
};

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

bool checked_product(
    std::size_t left,
    std::size_t right,
    std::size_t* output
) noexcept {
    if (
        output == nullptr
        || (
            left != 0U
            && right > std::numeric_limits<std::size_t>::max() / left
        )
    ) {
        return false;
    }
    *output = left * right;
    return true;
}

bool checked_add(
    std::size_t left,
    std::size_t right,
    std::size_t* output
) noexcept {
    if (
        output == nullptr
        || right > std::numeric_limits<std::size_t>::max() - left
    ) {
        return false;
    }
    *output = left + right;
    return true;
}

std::size_t bit_bytes(std::uint32_t bits) noexcept {
    return (static_cast<std::size_t>(bits) + 7U) / 8U;
}

std::uint32_t log2_power_of_two(std::uint16_t value) noexcept {
    std::uint32_t result = 0U;
    while (value > 1U) {
        value = static_cast<std::uint16_t>(value >> 1U);
        ++result;
    }
    return result;
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

bool valid_entropy(std::uint8_t mode, std::uint8_t parameter) noexcept {
    return (
        mode == kEntropyRice && parameter <= kMaximumRiceParameter
    ) || (
        mode == kEntropyPacked && parameter >= 1U && parameter <= 64U
    );
}

bool valid_padding(
    const std::uint8_t* payload,
    std::size_t bytes,
    std::uint32_t bits
) noexcept {
    if (payload == nullptr || bytes != bit_bytes(bits)) {
        return false;
    }
    if (bytes == 0U || bits % 8U == 0U) {
        return true;
    }
    const std::uint8_t used_mask = static_cast<std::uint8_t>(
        (1U << (bits % 8U)) - 1U
    );
    return (
        payload[bytes - 1U] & static_cast<std::uint8_t>(~used_mask)
    ) == 0U;
}

bool packed_size_matches(
    std::uint8_t mode,
    std::uint8_t parameter,
    std::size_t symbols,
    std::uint32_t bits
) noexcept {
    if (mode != kEntropyPacked) {
        return true;
    }
    std::size_t expected = 0U;
    return checked_product(symbols, parameter, &expected)
        && expected <= std::numeric_limits<std::uint32_t>::max()
        && bits == expected;
}

void maximize(
    resonith_lapped_requirements* maximum,
    const resonith_lapped_requirements& current
) noexcept {
    maximum->sample_rate = current.sample_rate;
    maximum->half_window = current.half_window;
    maximum->band_count = current.band_count;
    maximum->output_channels = current.output_channels;
    maximum->frame_count = std::max(
        maximum->frame_count,
        current.frame_count
    );
    maximum->transform_frame_count = std::max(
        maximum->transform_frame_count,
        current.transform_frame_count
    );
    maximum->scale_elements = std::max(
        maximum->scale_elements,
        current.scale_elements
    );
    maximum->count_elements = std::max(
        maximum->count_elements,
        current.count_elements
    );
    maximum->position_elements = std::max(
        maximum->position_elements,
        current.position_elements
    );
    maximum->coefficient_elements = std::max(
        maximum->coefficient_elements,
        current.coefficient_elements
    );
    maximum->overlap_elements = std::max(
        maximum->overlap_elements,
        current.overlap_elements
    );
    maximum->output_elements = std::max(
        maximum->output_elements,
        current.output_elements
    );
}

resonith_status parse_record(
    const resonith_lapped_compact_session& session,
    std::size_t offset,
    std::uint32_t packet_index,
    compact_record_view* view
) noexcept {
    if (view == nullptr || packet_index >= session.packet_count) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (
        offset > session.data_size
        || session.data_size - offset
            < kCompactDescriptorBytes + kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }

    const std::uint64_t logical_start_64 =
        static_cast<std::uint64_t>(packet_index) * session.packet_frames;
    if (logical_start_64 >= session.frame_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t logical_start =
        static_cast<std::uint32_t>(logical_start_64);
    const std::uint32_t logical_count = std::min(
        session.packet_frames,
        session.frame_count - logical_start
    );
    const bool final_packet = packet_index + 1U == session.packet_count;
    const std::uint32_t transform_frames =
        logical_count / session.half_window + (final_packet ? 1U : 0U);
    if (transform_frames == 0U) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::uint8_t* record = session.data + offset;
    const std::uint8_t scale_entropy = record[0U];
    const std::uint8_t scale_parameter = record[1U];
    const std::uint8_t count_entropy = record[2U];
    const std::uint8_t count_parameter = record[3U];
    const std::uint8_t position_parameter = record[4U];
    const std::uint8_t value_entropy = record[5U];
    const std::uint8_t value_parameter = record[6U];
    const std::uint32_t coefficient_count = read_u32(record + 7U);
    const std::array<std::uint32_t, 4U> bit_counts = {
        read_u32(record + 11U),
        read_u32(record + 15U),
        read_u32(record + 19U),
        read_u32(record + 23U),
    };
    if (
        !valid_entropy(scale_entropy, scale_parameter)
        || !valid_entropy(count_entropy, count_parameter)
        || !valid_entropy(value_entropy, value_parameter)
        || position_parameter > log2_power_of_two(session.half_window)
        || coefficient_count > kMaximumSymbols
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t maximum_coefficients = 0U;
    std::size_t output_elements = 0U;
    std::size_t overlap_elements = 0U;
    if (
        !checked_product(
            session.output_channels,
            transform_frames,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            session.band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            session.half_window,
            &maximum_coefficients
        )
        || !checked_product(
            logical_count,
            session.output_channels,
            &output_elements
        )
        || !checked_add(
            logical_count,
            2U * session.half_window,
            &overlap_elements
        )
        || channel_frames > kMaximumSymbols
        || scale_elements > kMaximumSymbols
        || coefficient_count > maximum_coefficients
        || !packed_size_matches(
            scale_entropy,
            scale_parameter,
            scale_elements,
            bit_counts[0U]
        )
        || !packed_size_matches(
            count_entropy,
            count_parameter,
            channel_frames,
            bit_counts[1U]
        )
        || !packed_size_matches(
            value_entropy,
            value_parameter,
            coefficient_count,
            bit_counts[3U]
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::array<std::size_t, 4U> field_bytes{};
    std::size_t record_size = kCompactDescriptorBytes;
    for (std::size_t field = 0U; field < field_bytes.size(); ++field) {
        field_bytes[field] = bit_bytes(bit_counts[field]);
        if (!checked_add(record_size, field_bytes[field], &record_size)) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    if (
        record_size > kMaximumStreamBytes
        || record_size > session.data_size - offset
        || session.data_size - offset - record_size < kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (
        resonith::internal::crc32(record, record_size)
        != read_u32(record + record_size)
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }

    const std::uint8_t* field = record + kCompactDescriptorBytes;
    for (std::size_t index = 0U; index < field_bytes.size(); ++index) {
        if (!valid_padding(field, field_bytes[index], bit_counts[index])) {
            return RESONITH_STATUS_MALFORMED;
        }
        field += field_bytes[index];
    }

    view->data = record;
    view->size = record_size;
    view->next_offset = offset + record_size + kRecordCrcBytes;
    view->logical_count = logical_count;
    view->requirements.sample_rate = session.sample_rate;
    view->requirements.frame_count = logical_count;
    view->requirements.transform_frame_count = transform_frames;
    view->requirements.half_window = session.half_window;
    view->requirements.band_count = session.band_count;
    view->requirements.output_channels = session.output_channels;
    view->requirements.scale_elements = scale_elements;
    view->requirements.count_elements = channel_frames;
    view->requirements.position_elements = coefficient_count;
    view->requirements.coefficient_elements = coefficient_count;
    view->requirements.overlap_elements = overlap_elements;
    view->requirements.output_elements = output_elements;
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_lapped_compact_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_lapped_compact_session* session,
    resonith_lapped_compact_requirements* requirements
) {
    if (data == nullptr || session == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *session = {};
    *requirements = {};
    if (
        data_size < kHeaderBytes + kDigestBytes
            + kCompactDescriptorBytes + kRecordCrcBytes
        || data_size > kMaximumStreamBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (std::memcmp(data, "LPS4", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4U] != 1U) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (data[5U] != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (!digest_matches(data, kHeaderBytes, data + kHeaderBytes)) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }

    resonith_lapped_compact_session parsed = {
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

    resonith_lapped_requirements maximum_current{};
    resonith_lapped_requirements maximum_lookahead{};
    std::size_t maximum_output = 0U;
    std::size_t offset = parsed.next_offset;
    for (
        std::uint32_t packet = 0U;
        packet < parsed.packet_count;
        ++packet
    ) {
        compact_record_view view{};
        const resonith_status status = parse_record(
            parsed,
            offset,
            packet,
            &view
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        maximize(&maximum_current, view.requirements);
        if (packet != 0U) {
            maximize(&maximum_lookahead, view.requirements);
        }
        maximum_output = std::max(
            maximum_output,
            view.requirements.output_elements
        );
        offset = view.next_offset;
    }
    if (offset != data_size) {
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
    requirements->maximum_current = maximum_current;
    requirements->maximum_lookahead = maximum_lookahead;
    requirements->maximum_logical_output_elements = maximum_output;
    return RESONITH_STATUS_OK;
}
