#include "resonith/seek.h"

#include "integrity.h"

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

constexpr std::size_t kHeaderBytes = 64U;
constexpr std::size_t kEntryBytes = 32U;
constexpr std::size_t kTrailerBytes = 36U;
constexpr std::uint8_t kVersion = 1U;
constexpr std::uint32_t kMaximumEntries = 1'000'000U;

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
    std::uint64_t value = 0U;
    for (unsigned shift = 0U; shift < 64U; shift += 8U) {
        value |= static_cast<std::uint64_t>(data[shift / 8U]) << shift;
    }
    return value;
}

void write_u16(std::uint8_t* data, std::uint16_t value) noexcept {
    data[0] = static_cast<std::uint8_t>(value);
    data[1] = static_cast<std::uint8_t>(value >> 8U);
}

void write_u32(std::uint8_t* data, std::uint32_t value) noexcept {
    for (unsigned shift = 0U; shift < 32U; shift += 8U) {
        data[shift / 8U] = static_cast<std::uint8_t>(value >> shift);
    }
}

void write_u64(std::uint8_t* data, std::uint64_t value) noexcept {
    for (unsigned shift = 0U; shift < 64U; shift += 8U) {
        data[shift / 8U] = static_cast<std::uint8_t>(value >> shift);
    }
}

std::size_t required_size(std::uint32_t block_count) noexcept {
    return kHeaderBytes
        + static_cast<std::size_t>(block_count) * kEntryBytes
        + kTrailerBytes;
}

void write_entry(
    std::uint8_t* data,
    const resonith_liftpack_block_info& entry
) noexcept {
    write_u64(data, entry.byte_offset);
    write_u64(data + 8U, entry.byte_size);
    write_u32(data + 16U, entry.sample_offset);
    write_u32(data + 20U, entry.bit_count);
    write_u16(data + 24U, entry.sample_count);
    data[26] = entry.transform;
    data[27] = entry.entropy;
    data[28] = entry.entropy_parameter;
    data[29] = entry.lpc_order;
    write_u16(data + 30U, 0U);
}

resonith_status read_entry(
    const std::uint8_t* data,
    resonith_liftpack_block_info& entry
) noexcept {
    if (read_u16(data + 30U) != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    entry = resonith_liftpack_block_info{
        read_u64(data),
        read_u64(data + 8U),
        read_u32(data + 16U),
        read_u32(data + 20U),
        read_u16(data + 24U),
        data[26],
        data[27],
        data[28],
        data[29],
        0U,
    };
    return RESONITH_STATUS_OK;
}

bool entries_equal(
    const resonith_liftpack_block_info& left,
    const resonith_liftpack_block_info& right
) noexcept {
    return left.byte_offset == right.byte_offset
        && left.byte_size == right.byte_size
        && left.sample_offset == right.sample_offset
        && left.bit_count == right.bit_count
        && left.sample_count == right.sample_count
        && left.transform == right.transform
        && left.entropy == right.entropy
        && left.entropy_parameter == right.entropy_parameter
        && left.lpc_order == right.lpc_order;
}

}  // namespace

extern "C" resonith_status resonith_seek_index_required_size(
    const std::uint8_t* source,
    std::size_t source_size,
    std::size_t* index_size
) {
    if (index_size == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *index_size = 0U;
    resonith_liftpack_info info{};
    const resonith_status status = resonith_liftpack_inspect(
        source,
        source_size,
        &info
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (info.block_count > kMaximumEntries) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    *index_size = required_size(info.block_count);
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_seek_index_build(
    const std::uint8_t* source,
    std::size_t source_size,
    std::uint8_t* output,
    std::size_t output_capacity,
    std::size_t* bytes_written
) {
    if (bytes_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *bytes_written = 0U;
    std::size_t index_size = 0U;
    resonith_status status = resonith_seek_index_required_size(
        source,
        source_size,
        &index_size
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < index_size) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    resonith_liftpack_cursor cursor{};
    status = resonith_liftpack_cursor_open(source, source_size, &cursor);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    std::memset(output, 0, index_size);
    std::memcpy(output, "RSI1", 4U);
    output[4] = kVersion;
    write_u16(output + 6U, static_cast<std::uint16_t>(kHeaderBytes));
    write_u16(output + 8U, static_cast<std::uint16_t>(kEntryBytes));
    write_u32(output + 12U, cursor.info.block_count);
    write_u16(output + 16U, cursor.info.block_size);
    write_u32(output + 20U, cursor.info.sample_count);
    write_u64(output + 24U, static_cast<std::uint64_t>(source_size));
    resonith::internal::sha256(source, source_size, output + 32U);

    for (
        std::uint32_t block = 0U;
        block < cursor.info.block_count;
        ++block
    ) {
        resonith_liftpack_block_info entry{};
        status = resonith_liftpack_cursor_index_next(&cursor, &entry);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        write_entry(
            output + kHeaderBytes
                + static_cast<std::size_t>(block) * kEntryBytes,
            entry
        );
    }
    const std::size_t protected_bytes = index_size - kTrailerBytes;
    write_u32(
        output + protected_bytes,
        resonith::internal::crc32(output, protected_bytes)
    );
    resonith::internal::sha256(
        output,
        protected_bytes,
        output + protected_bytes + 4U
    );
    *bytes_written = index_size;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_seek_index_open(
    const std::uint8_t* index_data,
    std::size_t index_size,
    const std::uint8_t* source,
    std::size_t source_size,
    resonith_seek_index_view* view
) {
    if (view == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    if (index_data == nullptr || source == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (index_size < kHeaderBytes + kTrailerBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (std::memcmp(index_data, "RSI1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (index_data[4] != kVersion) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (
        index_data[5] != 0U
        || read_u16(index_data + 6U) != kHeaderBytes
        || read_u16(index_data + 8U) != kEntryBytes
        || read_u16(index_data + 10U) != 0U
        || read_u16(index_data + 18U) != 0U
    ) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    const std::uint32_t block_count = read_u32(index_data + 12U);
    if (block_count > kMaximumEntries) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::size_t expected_size = required_size(block_count);
    if (index_size != expected_size) {
        return index_size < expected_size
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    const std::size_t protected_bytes = index_size - kTrailerBytes;
    if (
        resonith::internal::crc32(index_data, protected_bytes)
        != read_u32(index_data + protected_bytes)
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }
    std::uint8_t index_hash[32]{};
    resonith::internal::sha256(index_data, protected_bytes, index_hash);
    if (
        std::memcmp(index_hash, index_data + protected_bytes + 4U, 32U)
        != 0
    ) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }

    resonith_liftpack_cursor cursor{};
    resonith_status status = resonith_liftpack_cursor_open(
        source,
        source_size,
        &cursor
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        read_u16(index_data + 16U) != cursor.info.block_size
        || read_u32(index_data + 20U) != cursor.info.sample_count
        || read_u64(index_data + 24U) != source_size
        || block_count != cursor.info.block_count
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    std::uint8_t source_hash[32]{};
    resonith::internal::sha256(source, source_size, source_hash);
    if (std::memcmp(source_hash, index_data + 32U, 32U) != 0) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }

    for (std::uint32_t block = 0U; block < block_count; ++block) {
        resonith_liftpack_block_info stored{};
        status = read_entry(
            index_data + kHeaderBytes
                + static_cast<std::size_t>(block) * kEntryBytes,
            stored
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        resonith_liftpack_block_info actual{};
        status = resonith_liftpack_cursor_index_next(&cursor, &actual);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (!entries_equal(stored, actual)) {
            return RESONITH_STATUS_MALFORMED;
        }
    }

    view->index_data = index_data;
    view->index_size = index_size;
    view->source_data = source;
    view->source_size = source_size;
    view->sample_count = cursor.info.sample_count;
    view->block_count = cursor.info.block_count;
    view->block_size = cursor.info.block_size;
    view->reserved = 0U;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_seek_index_get_block(
    const resonith_seek_index_view* view,
    std::uint32_t block_index,
    resonith_liftpack_block_info* entry
) {
    if (entry == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *entry = {};
    if (
        view == nullptr
        || view->index_data == nullptr
        || view->source_data == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (block_index >= view->block_count) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    if (view->index_size != required_size(view->block_count)) {
        return RESONITH_STATUS_MALFORMED;
    }
    return read_entry(
        view->index_data + kHeaderBytes
            + static_cast<std::size_t>(block_index) * kEntryBytes,
        *entry
    );
}

extern "C" resonith_status resonith_seek_index_decode_block(
    const resonith_seek_index_view* view,
    std::uint32_t block_index,
    std::int64_t* output,
    std::size_t output_capacity,
    std::int64_t* scratch,
    std::size_t scratch_count,
    std::uint32_t* sample_offset,
    std::size_t* samples_written
) {
    if (sample_offset == nullptr || samples_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *sample_offset = 0U;
    *samples_written = 0U;
    resonith_liftpack_block_info entry{};
    resonith_status status = resonith_seek_index_get_block(
        view,
        block_index,
        &entry
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (output == nullptr || scratch == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    resonith_liftpack_cursor cursor{};
    cursor.data = view->source_data;
    cursor.data_size = view->source_size;
    cursor.byte_offset = static_cast<std::size_t>(entry.byte_offset);
    cursor.sample_offset = entry.sample_offset;
    cursor.next_block = block_index;
    cursor.info = resonith_liftpack_info{
        view->sample_count,
        view->block_count,
        view->block_size,
        0U,
    };
    cursor.lpc_stream =
        std::memcmp(view->source_data, "RSL2", 4U) == 0 ? 1U : 0U;
    status = resonith_liftpack_cursor_decode_next(
        &cursor,
        output,
        output_capacity,
        scratch,
        scratch_count,
        sample_offset,
        samples_written
    );
    if (
        status == RESONITH_STATUS_OK
        && (
            *sample_offset != entry.sample_offset
            || *samples_written != entry.sample_count
        )
    ) {
        *sample_offset = 0U;
        *samples_written = 0U;
        return RESONITH_STATUS_MALFORMED;
    }
    return status;
}
