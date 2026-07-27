#include "resonith/lapped_compact.h"

#include "integrity.h"
#include "lapped_internal.h"

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
constexpr std::size_t kFiniteCompactDescriptorBytes = 28U;
constexpr std::size_t kRiceValueCompactDescriptorBytes = 30U;
constexpr std::size_t kRecordCrcBytes = 4U;
constexpr std::size_t kMaximumStreamBytes = 512U << 20U;
constexpr std::uint32_t kMaximumPacketCount = 1U << 20U;
constexpr std::uint32_t kMaximumSymbols = 64U << 20U;
constexpr std::uint8_t kEntropyRice = 0U;
constexpr std::uint8_t kEntropyPacked = 1U;
constexpr std::uint8_t kMaximumRiceParameter = 20U;
constexpr std::uint16_t kTransportLps4 = 0U;
constexpr std::uint16_t kTransportLps5 = 1U;
constexpr std::uint16_t kTransportLps6 = 2U;

struct compact_record_view {
    const std::uint8_t* data = nullptr;
    std::size_t size = 0U;
    std::size_t framed_size = 0U;
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

bool valid_sequence_shape(
    const resonith_lapped_compact_sequence& sequence
) noexcept {
    return sequence.reserved <= kTransportLps6
        && sequence.sample_rate != 0U
        && sequence.frame_count != 0U
        && sequence.output_channels != 0U
        && sequence.output_channels <= 8U
        && sequence.half_window >= 32U
        && sequence.half_window <= 1024U
        && (sequence.half_window & (sequence.half_window - 1U)) == 0U
        && sequence.band_count != 0U
        && sequence.band_count <= 64U
        && sequence.packet_frames >= sequence.half_window
        && sequence.packet_frames % sequence.half_window == 0U
        && sequence.packet_count != 0U
        && sequence.packet_count <= kMaximumPacketCount
        && sequence.packet_count
            == sequence.frame_count / sequence.packet_frames
                + (
                    sequence.frame_count % sequence.packet_frames != 0U
                        ? 1U
                        : 0U
                );
}

resonith_status parse_sequence_header(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_lapped_compact_sequence* sequence
) noexcept {
    if (data == nullptr || sequence == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *sequence = {};
    if (data_size < kHeaderBytes + kDigestBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const bool is_lps4 = std::memcmp(data, "LPS4", 4U) == 0;
    const bool is_lps5 = std::memcmp(data, "LPS5", 4U) == 0;
    const bool is_lps6 = std::memcmp(data, "LPS6", 4U) == 0;
    if (!is_lps4 && !is_lps5 && !is_lps6) {
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

    resonith_lapped_compact_sequence parsed = {
        read_u32(data + 8U),
        read_u32(data + 12U),
        read_u32(data + 20U),
        read_u32(data + 24U),
        read_u16(data + 16U),
        read_u16(data + 18U),
        read_u16(data + 6U),
        is_lps6
            ? kTransportLps6
            : (is_lps5 ? kTransportLps5 : kTransportLps4),
    };
    if (!valid_sequence_shape(parsed)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    *sequence = parsed;
    return RESONITH_STATUS_OK;
}

resonith_lapped_compact_sequence sequence_from_session(
    const resonith_lapped_compact_session& session
) noexcept {
    return {
        session.sample_rate,
        session.frame_count,
        session.packet_frames,
        session.packet_count,
        session.half_window,
        session.band_count,
        session.output_channels,
        session.reserved,
    };
}

resonith_status sequence_record_requirements(
    const resonith_lapped_compact_sequence& sequence,
    std::uint32_t packet_index,
    resonith_lapped_requirements* requirements
) noexcept {
    if (
        requirements == nullptr
        || packet_index >= sequence.packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    const std::uint64_t logical_start_64 =
        static_cast<std::uint64_t>(packet_index) * sequence.packet_frames;
    if (logical_start_64 >= sequence.frame_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t logical_start =
        static_cast<std::uint32_t>(logical_start_64);
    const std::uint32_t logical_count = std::min(
        sequence.packet_frames,
        sequence.frame_count - logical_start
    );
    const bool final_packet = packet_index + 1U == sequence.packet_count;
    const std::uint32_t transform_frames =
        logical_count / sequence.half_window + (final_packet ? 1U : 0U);
    if (transform_frames == 0U) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t coefficient_elements = 0U;
    std::size_t output_elements = 0U;
    std::size_t overlap_elements = 0U;
    if (
        !checked_product(
            sequence.output_channels,
            transform_frames,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            sequence.band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            sequence.half_window,
            &coefficient_elements
        )
        || !checked_product(
            logical_count,
            sequence.output_channels,
            &output_elements
        )
        || !checked_add(
            logical_count,
            2U * sequence.half_window,
            &overlap_elements
        )
        || channel_frames > kMaximumSymbols
        || scale_elements > kMaximumSymbols
        || coefficient_elements > kMaximumSymbols
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    requirements->sample_rate = sequence.sample_rate;
    requirements->frame_count = logical_count;
    requirements->transform_frame_count = transform_frames;
    requirements->half_window = sequence.half_window;
    requirements->band_count = sequence.band_count;
    requirements->output_channels = sequence.output_channels;
    requirements->scale_elements = scale_elements;
    requirements->count_elements = channel_frames;
    requirements->position_elements = coefficient_elements;
    requirements->coefficient_elements = coefficient_elements;
    requirements->overlap_elements = overlap_elements;
    requirements->output_elements = output_elements;
    return RESONITH_STATUS_OK;
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

resonith_status parse_lps4_record_bytes(
    const resonith_lapped_compact_sequence& sequence,
    const std::uint8_t* record,
    std::size_t available,
    std::uint32_t packet_index,
    bool exact_framing,
    compact_record_view* view
) noexcept {
    if (
        record == nullptr
        || view == nullptr
        || packet_index >= sequence.packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (
        available < kCompactDescriptorBytes + kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }

    const std::uint64_t logical_start_64 =
        static_cast<std::uint64_t>(packet_index) * sequence.packet_frames;
    if (logical_start_64 >= sequence.frame_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t logical_start =
        static_cast<std::uint32_t>(logical_start_64);
    const std::uint32_t logical_count = std::min(
        sequence.packet_frames,
        sequence.frame_count - logical_start
    );
    const bool final_packet = packet_index + 1U == sequence.packet_count;
    const std::uint32_t transform_frames =
        logical_count / sequence.half_window + (final_packet ? 1U : 0U);
    if (transform_frames == 0U) {
        return RESONITH_STATUS_MALFORMED;
    }

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
        || position_parameter > log2_power_of_two(sequence.half_window)
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
            sequence.output_channels,
            transform_frames,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            sequence.band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            sequence.half_window,
            &maximum_coefficients
        )
        || !checked_product(
            logical_count,
            sequence.output_channels,
            &output_elements
        )
        || !checked_add(
            logical_count,
            2U * sequence.half_window,
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
        || record_size > available
        || available - record_size < kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::size_t framed_size = record_size + kRecordCrcBytes;
    if (exact_framing && framed_size != available) {
        return RESONITH_STATUS_MALFORMED;
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
    view->framed_size = framed_size;
    view->logical_count = logical_count;
    view->requirements.sample_rate = sequence.sample_rate;
    view->requirements.frame_count = logical_count;
    view->requirements.transform_frame_count = transform_frames;
    view->requirements.half_window = sequence.half_window;
    view->requirements.band_count = sequence.band_count;
    view->requirements.output_channels = sequence.output_channels;
    view->requirements.scale_elements = scale_elements;
    view->requirements.count_elements = channel_frames;
    view->requirements.position_elements = coefficient_count;
    view->requirements.coefficient_elements = coefficient_count;
    view->requirements.overlap_elements = overlap_elements;
    view->requirements.output_elements = output_elements;
    return RESONITH_STATUS_OK;
}

resonith_status parse_lps5_record_bytes(
    const resonith_lapped_compact_sequence& sequence,
    const std::uint8_t* record,
    std::size_t available,
    std::uint32_t packet_index,
    bool exact_framing,
    compact_record_view* view
) noexcept {
    if (
        record == nullptr
        || view == nullptr
        || packet_index >= sequence.packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (available < kFiniteCompactDescriptorBytes + kRecordCrcBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }

    resonith_lapped_requirements shape{};
    const resonith_status shape_status = sequence_record_requirements(
        sequence,
        packet_index,
        &shape
    );
    if (shape_status != RESONITH_STATUS_OK) {
        return shape_status;
    }

    const std::uint8_t count_entropy = record[0U];
    const std::uint8_t count_parameter = record[1U];
    const std::uint16_t gap_threshold = read_u16(record + 2U);
    const std::uint32_t coefficient_count = read_u32(record + 4U);
    const std::array<std::uint32_t, 5U> bit_counts = {
        read_u32(record + 8U),
        read_u32(record + 12U),
        read_u32(record + 16U),
        read_u32(record + 20U),
        read_u32(record + 24U),
    };
    if (
        !valid_entropy(count_entropy, count_parameter)
        || gap_threshold == 0U
        || gap_threshold > sequence.half_window
        || coefficient_count > shape.position_elements
        || bit_counts[0U] == 0U
        || (
            coefficient_count == 0U
            && (bit_counts[2U] != 0U || bit_counts[4U] != 0U)
        )
        || (
            coefficient_count != 0U
            && (bit_counts[2U] == 0U || bit_counts[4U] == 0U)
        )
        || !packed_size_matches(
            count_entropy,
            count_parameter,
            shape.count_elements,
            bit_counts[1U]
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::array<std::size_t, 5U> field_bytes{};
    std::size_t record_size = kFiniteCompactDescriptorBytes;
    for (std::size_t field = 0U; field < field_bytes.size(); ++field) {
        field_bytes[field] = bit_bytes(bit_counts[field]);
        if (!checked_add(record_size, field_bytes[field], &record_size)) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    if (
        record_size > kMaximumStreamBytes
        || record_size > available
        || available - record_size < kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::size_t framed_size = record_size + kRecordCrcBytes;
    if (exact_framing && framed_size != available) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        resonith::internal::crc32(record, record_size)
        != read_u32(record + record_size)
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }

    const std::uint8_t* field = record + kFiniteCompactDescriptorBytes;
    for (std::size_t index = 0U; index < field_bytes.size(); ++index) {
        if (!valid_padding(field, field_bytes[index], bit_counts[index])) {
            return RESONITH_STATUS_MALFORMED;
        }
        field += field_bytes[index];
    }

    view->data = record;
    view->size = record_size;
    view->framed_size = framed_size;
    view->logical_count = shape.frame_count;
    view->requirements = shape;
    view->requirements.position_elements = coefficient_count;
    view->requirements.coefficient_elements = coefficient_count;
    return RESONITH_STATUS_OK;
}

resonith_status parse_lps6_record_bytes(
    const resonith_lapped_compact_sequence& sequence,
    const std::uint8_t* record,
    std::size_t available,
    std::uint32_t packet_index,
    bool exact_framing,
    compact_record_view* view
) noexcept {
    if (
        record == nullptr
        || view == nullptr
        || packet_index >= sequence.packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (available < kRiceValueCompactDescriptorBytes + kRecordCrcBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }

    resonith_lapped_requirements shape{};
    const resonith_status shape_status = sequence_record_requirements(
        sequence,
        packet_index,
        &shape
    );
    if (shape_status != RESONITH_STATUS_OK) {
        return shape_status;
    }

    const std::uint8_t count_entropy = record[0U];
    const std::uint8_t count_parameter = record[1U];
    const std::uint8_t value_entropy = record[2U];
    const std::uint8_t value_parameter = record[3U];
    const std::uint16_t gap_threshold = read_u16(record + 4U);
    const std::uint32_t coefficient_count = read_u32(record + 6U);
    const std::array<std::uint32_t, 5U> bit_counts = {
        read_u32(record + 10U),
        read_u32(record + 14U),
        read_u32(record + 18U),
        read_u32(record + 22U),
        read_u32(record + 26U),
    };
    if (
        !valid_entropy(count_entropy, count_parameter)
        || !valid_entropy(value_entropy, value_parameter)
        || gap_threshold == 0U
        || gap_threshold > sequence.half_window
        || coefficient_count > shape.position_elements
        || bit_counts[0U] == 0U
        || (
            coefficient_count == 0U
            && (bit_counts[2U] != 0U || bit_counts[4U] != 0U)
        )
        || (
            coefficient_count != 0U
            && (bit_counts[2U] == 0U || bit_counts[4U] == 0U)
        )
        || !packed_size_matches(
            count_entropy,
            count_parameter,
            shape.count_elements,
            bit_counts[1U]
        )
        || !packed_size_matches(
            value_entropy,
            value_parameter,
            coefficient_count,
            bit_counts[4U]
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::array<std::size_t, 5U> field_bytes{};
    std::size_t record_size = kRiceValueCompactDescriptorBytes;
    for (std::size_t field = 0U; field < field_bytes.size(); ++field) {
        field_bytes[field] = bit_bytes(bit_counts[field]);
        if (!checked_add(record_size, field_bytes[field], &record_size)) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    if (
        record_size > kMaximumStreamBytes
        || record_size > available
        || available - record_size < kRecordCrcBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::size_t framed_size = record_size + kRecordCrcBytes;
    if (exact_framing && framed_size != available) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        resonith::internal::crc32(record, record_size)
        != read_u32(record + record_size)
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }

    const std::uint8_t* field = record + kRiceValueCompactDescriptorBytes;
    for (std::size_t index = 0U; index < field_bytes.size(); ++index) {
        if (!valid_padding(field, field_bytes[index], bit_counts[index])) {
            return RESONITH_STATUS_MALFORMED;
        }
        field += field_bytes[index];
    }

    view->data = record;
    view->size = record_size;
    view->framed_size = framed_size;
    view->logical_count = shape.frame_count;
    view->requirements = shape;
    view->requirements.position_elements = coefficient_count;
    view->requirements.coefficient_elements = coefficient_count;
    return RESONITH_STATUS_OK;
}

resonith_status parse_record_bytes(
    const resonith_lapped_compact_sequence& sequence,
    const std::uint8_t* record,
    std::size_t available,
    std::uint32_t packet_index,
    bool exact_framing,
    compact_record_view* view
) noexcept {
    if (sequence.reserved == kTransportLps5) {
        return parse_lps5_record_bytes(
            sequence,
            record,
            available,
            packet_index,
            exact_framing,
            view
        );
    }
    if (sequence.reserved == kTransportLps6) {
        return parse_lps6_record_bytes(
            sequence,
            record,
            available,
            packet_index,
            exact_framing,
            view
        );
    }
    return parse_lps4_record_bytes(
        sequence,
        record,
        available,
        packet_index,
        exact_framing,
        view
    );
}

resonith_status parse_record(
    const resonith_lapped_compact_session& session,
    std::size_t offset,
    std::uint32_t packet_index,
    compact_record_view* view
) noexcept {
    if (view == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (offset > session.data_size) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const resonith_status status = parse_record_bytes(
        sequence_from_session(session),
        session.data + offset,
        session.data_size - offset,
        packet_index,
        false,
        view
    );
    if (status == RESONITH_STATUS_OK) {
        view->next_offset = offset + view->framed_size;
    }
    return status;
}

resonith_status decode_record_fields(
    const resonith_lapped_compact_sequence& sequence,
    const compact_record_view& view,
    const resonith_lapped_workspace& workspace,
    resonith_lapped_requirements* requirements
) noexcept {
    if (sequence.reserved == kTransportLps5) {
        return resonith::internal::lapped_finite_compact_fields_decode(
            view.data,
            view.size,
            view.requirements,
            workspace,
            requirements
        );
    }
    if (sequence.reserved == kTransportLps6) {
        return resonith::internal::lapped_rice_value_compact_fields_decode(
            view.data,
            view.size,
            view.requirements,
            workspace,
            requirements
        );
    }
    return resonith::internal::lapped_compact_fields_decode(
        view.data,
        view.size,
        sequence.sample_rate,
        view.logical_count,
        view.requirements.transform_frame_count,
        sequence.output_channels,
        sequence.half_window,
        sequence.band_count,
        workspace,
        requirements
    );
}

resonith_status decode_record_views(
    const resonith_lapped_compact_sequence& sequence,
    std::uint32_t packet_index,
    const compact_record_view& current,
    const compact_record_view* lookahead,
    const resonith_lapped_workspace& current_workspace,
    const resonith_lapped_workspace* lookahead_workspace,
    std::int16_t* logical_output,
    std::size_t logical_output_capacity,
    std::size_t* frames_written
) noexcept {
    if (
        logical_output == nullptr
        || frames_written == nullptr
        || packet_index >= sequence.packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_written = 0U;
    if (logical_output_capacity < current.requirements.output_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    const bool final_packet = packet_index + 1U == sequence.packet_count;
    if (
        (final_packet && (lookahead != nullptr || lookahead_workspace != nullptr))
        || (
            !final_packet
            && (lookahead == nullptr || lookahead_workspace == nullptr)
        )
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    resonith_lapped_requirements decoded_current{};
    resonith_status status = decode_record_fields(
        sequence,
        current,
        current_workspace,
        &decoded_current
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    resonith_lapped_requirements decoded_lookahead{};
    if (!final_packet) {
        status = decode_record_fields(
            sequence,
            *lookahead,
            *lookahead_workspace,
            &decoded_lookahead
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    std::size_t rendered_frames = 0U;
    status = resonith::internal::lapped_render_chained(
        decoded_current,
        current_workspace,
        final_packet ? nullptr : &decoded_lookahead,
        final_packet ? nullptr : lookahead_workspace,
        logical_output,
        logical_output_capacity,
        &rendered_frames
    );
    if (
        status != RESONITH_STATUS_OK
        || rendered_frames != current.logical_count
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }
    *frames_written = rendered_frames;
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_lapped_compact_sequence_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_lapped_compact_sequence* sequence
) {
    if (data == nullptr || sequence == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (data_size != kHeaderBytes + kDigestBytes) {
        *sequence = {};
        return data_size < kHeaderBytes + kDigestBytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    return parse_sequence_header(data, data_size, sequence);
}

extern "C" resonith_status resonith_lapped_compact_sequence_requirements(
    const resonith_lapped_compact_sequence* sequence,
    resonith_lapped_compact_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (sequence == nullptr || !valid_sequence_shape(*sequence)) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    resonith_lapped_requirements maximum_current{};
    resonith_lapped_requirements maximum_lookahead{};
    resonith_lapped_requirements shape{};
    resonith_status status = sequence_record_requirements(
        *sequence,
        0U,
        &shape
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    maximize(&maximum_current, shape);

    const std::uint32_t final_index = sequence->packet_count - 1U;
    if (final_index != 0U) {
        status = sequence_record_requirements(
            *sequence,
            final_index,
            &shape
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        maximize(&maximum_current, shape);
        maximize(&maximum_lookahead, shape);
    }
    if (sequence->packet_count > 2U) {
        status = sequence_record_requirements(
            *sequence,
            1U,
            &shape
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        maximize(&maximum_lookahead, shape);
    }

    requirements->sample_rate = sequence->sample_rate;
    requirements->frame_count = sequence->frame_count;
    requirements->packet_frames = sequence->packet_frames;
    requirements->packet_count = sequence->packet_count;
    requirements->half_window = sequence->half_window;
    requirements->band_count = sequence->band_count;
    requirements->output_channels = sequence->output_channels;
    requirements->maximum_current = maximum_current;
    requirements->maximum_lookahead = maximum_lookahead;
    requirements->maximum_logical_output_elements =
        maximum_current.output_elements;
    return RESONITH_STATUS_OK;
}

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
    resonith_lapped_compact_sequence sequence{};
    const resonith_status header_status = parse_sequence_header(
        data,
        data_size,
        &sequence
    );
    if (header_status != RESONITH_STATUS_OK) {
        return header_status;
    }
    resonith_lapped_compact_session parsed = {
        data,
        data_size,
        kHeaderBytes + kDigestBytes,
        0U,
        0U,
        sequence.sample_rate,
        sequence.frame_count,
        sequence.packet_frames,
        sequence.packet_count,
        sequence.half_window,
        sequence.band_count,
        sequence.output_channels,
        sequence.reserved,
    };

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

extern "C" resonith_status resonith_lapped_compact_decode_next(
    resonith_lapped_compact_session* session,
    const resonith_lapped_workspace* current_workspace,
    const resonith_lapped_workspace* lookahead_workspace,
    std::int16_t* logical_output,
    std::size_t logical_output_capacity,
    std::uint32_t* logical_start,
    std::size_t* frames_written
) {
    if (
        session == nullptr
        || current_workspace == nullptr
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

    compact_record_view current{};
    resonith_status status = parse_record(
        *session,
        session->next_offset,
        session->next_packet,
        &current
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    const bool final_packet =
        session->next_packet + 1U == session->packet_count;
    compact_record_view lookahead{};
    if (!final_packet) {
        if (lookahead_workspace == nullptr) {
            return RESONITH_STATUS_INVALID_ARGUMENT;
        }
        status = parse_record(
            *session,
            current.next_offset,
            session->next_packet + 1U,
            &lookahead
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    std::size_t rendered_frames = 0U;
    status = decode_record_views(
        sequence_from_session(*session),
        session->next_packet,
        current,
        final_packet ? nullptr : &lookahead,
        *current_workspace,
        final_packet ? nullptr : lookahead_workspace,
        logical_output,
        logical_output_capacity,
        &rendered_frames
    );
    if (
        status != RESONITH_STATUS_OK
        || rendered_frames != current.logical_count
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }

    *logical_start = session->next_frame;
    *frames_written = rendered_frames;
    session->next_offset = current.next_offset;
    ++session->next_packet;
    session->next_frame += current.logical_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_lapped_compact_decode_record_pair(
    const resonith_lapped_compact_sequence* sequence,
    std::uint32_t packet_index,
    const std::uint8_t* current_record,
    std::size_t current_record_size,
    const std::uint8_t* lookahead_record,
    std::size_t lookahead_record_size,
    const resonith_lapped_workspace* current_workspace,
    const resonith_lapped_workspace* lookahead_workspace,
    std::int16_t* logical_output,
    std::size_t logical_output_capacity,
    std::uint32_t* logical_start,
    std::size_t* frames_written
) {
    if (
        logical_start == nullptr
        || frames_written == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *logical_start = 0U;
    *frames_written = 0U;
    if (
        sequence == nullptr
        || current_record == nullptr
        || current_workspace == nullptr
        || logical_output == nullptr
        || !valid_sequence_shape(*sequence)
        || packet_index >= sequence->packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    const bool final_packet = packet_index + 1U == sequence->packet_count;
    if (
        (
            final_packet
            && (
                lookahead_record != nullptr
                || lookahead_record_size != 0U
                || lookahead_workspace != nullptr
            )
        )
        || (
            !final_packet
            && (
                lookahead_record == nullptr
                || lookahead_record_size == 0U
                || lookahead_workspace == nullptr
            )
        )
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    compact_record_view current{};
    resonith_status status = parse_record_bytes(
        *sequence,
        current_record,
        current_record_size,
        packet_index,
        true,
        &current
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    compact_record_view lookahead{};
    if (!final_packet) {
        status = parse_record_bytes(
            *sequence,
            lookahead_record,
            lookahead_record_size,
            packet_index + 1U,
            true,
            &lookahead
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    std::size_t rendered_frames = 0U;
    status = decode_record_views(
        *sequence,
        packet_index,
        current,
        final_packet ? nullptr : &lookahead,
        *current_workspace,
        final_packet ? nullptr : lookahead_workspace,
        logical_output,
        logical_output_capacity,
        &rendered_frames
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    *logical_start = packet_index * sequence->packet_frames;
    *frames_written = rendered_frames;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_lapped_compact_decode_record_prefix(
    const resonith_lapped_compact_sequence* sequence,
    std::uint32_t packet_index,
    const std::uint8_t* current_record,
    std::size_t current_record_size,
    const resonith_lapped_workspace* current_workspace,
    std::int16_t* logical_output,
    std::size_t logical_output_capacity,
    std::uint32_t* logical_start,
    std::size_t* frames_written
) {
    if (logical_start == nullptr || frames_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *logical_start = 0U;
    *frames_written = 0U;
    if (
        sequence == nullptr
        || current_record == nullptr
        || current_workspace == nullptr
        || logical_output == nullptr
        || !valid_sequence_shape(*sequence)
        || packet_index >= sequence->packet_count
        || packet_index + 1U == sequence->packet_count
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    compact_record_view current{};
    resonith_status status = parse_record_bytes(
        *sequence,
        current_record,
        current_record_size,
        packet_index,
        true,
        &current
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    resonith_lapped_requirements decoded_current{};
    status = decode_record_fields(
        *sequence,
        current,
        *current_workspace,
        &decoded_current
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    std::size_t rendered_frames = 0U;
    status = resonith::internal::lapped_render_prefix(
        decoded_current,
        *current_workspace,
        logical_output,
        logical_output_capacity,
        &rendered_frames
    );
    if (
        status != RESONITH_STATUS_OK
        || rendered_frames + sequence->half_window != current.logical_count
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }
    *logical_start = packet_index * sequence->packet_frames;
    *frames_written = rendered_frames;
    return RESONITH_STATUS_OK;
}
