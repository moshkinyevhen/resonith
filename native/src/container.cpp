#include "resonith/container.h"

#include "integrity.h"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kHeaderBytes = 32;
constexpr std::size_t kDirectoryRecordBytes = 80;
constexpr std::uint8_t kVersionMajor = 1;
constexpr std::uint8_t kVersionMinor = 0;
constexpr std::uint32_t kMaximumSections = 4096;
constexpr std::uint64_t kMaximumSectionBytes = 512ULL << 20U;
constexpr std::uint64_t kMaximumTotalBytes = 1ULL << 30U;
constexpr std::uint32_t kMaximumTimebaseHz = 1'000'000'000U;
constexpr std::uint16_t kKnownSectionFlags =
    RESONITH_RSC1_SECTION_CRITICAL;

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

std::uint64_t read_u64(const std::uint8_t* data) noexcept {
    std::uint64_t output = 0;
    for (unsigned index = 0; index < 8U; ++index) {
        output |= static_cast<std::uint64_t>(data[index]) << (index * 8U);
    }
    return output;
}

bool valid_type(const std::uint8_t* type) noexcept {
    for (std::size_t index = 0; index < 4U; ++index) {
        const bool uppercase = type[index] >= static_cast<std::uint8_t>('A')
            && type[index] <= static_cast<std::uint8_t>('Z');
        const bool digit = type[index] >= static_cast<std::uint8_t>('0')
            && type[index] <= static_cast<std::uint8_t>('9');
        if (!uppercase && !digit) {
            return false;
        }
    }
    return true;
}

int compare_key(
    const std::uint8_t* left_type,
    std::uint32_t left_id,
    const std::uint8_t* right_type,
    std::uint32_t right_id
) noexcept {
    const int type_order = std::memcmp(left_type, right_type, 4U);
    if (type_order != 0) {
        return type_order;
    }
    if (left_id < right_id) {
        return -1;
    }
    if (left_id > right_id) {
        return 1;
    }
    return 0;
}

const std::uint8_t* record_at(
    const resonith_container_view* view,
    std::uint32_t index
) noexcept {
    return view->data
        + kHeaderBytes
        + static_cast<std::size_t>(index) * kDirectoryRecordBytes;
}

void decode_section(
    const resonith_container_view* view,
    const std::uint8_t* record,
    resonith_container_section* section
) noexcept {
    const std::uint64_t payload_offset = read_u64(record + 20U);
    section->payload = view->data + static_cast<std::size_t>(payload_offset);
    section->payload_size = static_cast<std::size_t>(read_u64(record + 28U));
    section->start_tick = read_u64(record + 12U);
    section->instance_id = read_u32(record + 8U);
    section->expected_crc32 = read_u32(record + 44U);
    section->schema_version = read_u16(record + 4U);
    section->flags = read_u16(record + 6U);
    std::memcpy(section->type, record, 4U);
    std::memcpy(section->expected_sha256, record + 48U, 32U);
}

}  // namespace

extern "C" resonith_status resonith_container_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_container_view* view
) {
    if (data == nullptr || view == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (data_size < kHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (std::memcmp(data, "RSC1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4] != kVersionMajor || data[5] != kVersionMinor) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (read_u32(data + 8U) != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    const std::uint32_t timebase_hz = read_u32(data + 12U);
    const std::uint32_t section_count = read_u32(data + 16U);
    const std::uint32_t record_bytes = read_u32(data + 20U);
    const std::uint32_t directory_bytes = read_u32(data + 24U);
    if (timebase_hz == 0U || timebase_hz > kMaximumTimebaseHz) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (section_count > kMaximumSections) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (record_bytes != kDirectoryRecordBytes) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    const std::size_t expected_directory_bytes =
        static_cast<std::size_t>(section_count) * kDirectoryRecordBytes;
    if (directory_bytes != expected_directory_bytes) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        expected_directory_bytes > data_size - kHeaderBytes
        || resonith::internal::crc32(
            data + kHeaderBytes,
            expected_directory_bytes
        ) != read_u32(data + 28U)
    ) {
        return expected_directory_bytes > data_size - kHeaderBytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_CHECKSUM_MISMATCH;
    }

    std::uint64_t payload_cursor =
        kHeaderBytes + expected_directory_bytes;
    std::uint64_t total_raw_bytes = 0;
    const std::uint8_t* previous_record = nullptr;
    for (std::uint32_t index = 0; index < section_count; ++index) {
        const std::uint8_t* record = data
            + kHeaderBytes
            + static_cast<std::size_t>(index) * kDirectoryRecordBytes;
        const std::uint16_t schema_version = read_u16(record + 4U);
        const std::uint16_t flags = read_u16(record + 6U);
        const std::uint64_t offset = read_u64(record + 20U);
        const std::uint64_t stored_bytes = read_u64(record + 28U);
        const std::uint64_t raw_bytes = read_u64(record + 36U);
        if (!valid_type(record) || schema_version == 0U) {
            return RESONITH_STATUS_MALFORMED;
        }
        if ((flags & ~kKnownSectionFlags) != 0U) {
            return RESONITH_STATUS_UNSUPPORTED_FEATURE;
        }
        if (
            previous_record != nullptr
            && compare_key(
                previous_record,
                read_u32(previous_record + 8U),
                record,
                read_u32(record + 8U)
            ) >= 0
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        if (stored_bytes != raw_bytes) {
            return RESONITH_STATUS_UNSUPPORTED_FEATURE;
        }
        if (raw_bytes > kMaximumSectionBytes) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        if (offset != payload_cursor) {
            return RESONITH_STATUS_MALFORMED;
        }
        if (
            total_raw_bytes > kMaximumTotalBytes - raw_bytes
            || stored_bytes > std::numeric_limits<std::size_t>::max()
            || payload_cursor > std::numeric_limits<std::size_t>::max()
            || stored_bytes > data_size
            || payload_cursor > data_size - stored_bytes
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        total_raw_bytes += raw_bytes;
        payload_cursor += stored_bytes;
        previous_record = record;
    }
    if (payload_cursor != data_size) {
        return payload_cursor > data_size
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }

    view->data = data;
    view->data_size = data_size;
    view->timebase_hz = timebase_hz;
    view->section_count = section_count;
    view->version_major = data[4];
    view->version_minor = data[5];
    view->profile = data[6];
    view->level = data[7];
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_container_get_section(
    const resonith_container_view* view,
    std::uint32_t index,
    resonith_container_section* section
) {
    if (
        view == nullptr
        || section == nullptr
        || view->data == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *section = {};
    if (index >= view->section_count) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    decode_section(view, record_at(view, index), section);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_container_find_section(
    const resonith_container_view* view,
    const std::uint8_t type[4],
    std::uint32_t instance_id,
    resonith_container_section* section
) {
    if (
        view == nullptr
        || type == nullptr
        || section == nullptr
        || view->data == nullptr
        || !valid_type(type)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *section = {};
    for (std::uint32_t index = 0; index < view->section_count; ++index) {
        const std::uint8_t* record = record_at(view, index);
        const int order = compare_key(
            record,
            read_u32(record + 8U),
            type,
            instance_id
        );
        if (order == 0) {
            decode_section(view, record, section);
            return RESONITH_STATUS_OK;
        }
        if (order > 0) {
            break;
        }
    }
    return RESONITH_STATUS_NOT_FOUND;
}

extern "C" resonith_status resonith_container_verify_section(
    const resonith_container_section* section
) {
    if (
        section == nullptr
        || (section->payload_size != 0U && section->payload == nullptr)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        resonith::internal::crc32(
            section->payload,
            section->payload_size
        ) != section->expected_crc32
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }
    std::uint8_t digest[32]{};
    resonith::internal::sha256(
        section->payload,
        section->payload_size,
        digest
    );
    if (std::memcmp(digest, section->expected_sha256, 32U) != 0) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }
    return RESONITH_STATUS_OK;
}
