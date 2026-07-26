#include "resonith/basis.h"

#include <cstddef>
#include <cstdint>

namespace {

constexpr std::size_t kHeaderBytes = 8;
constexpr std::uint16_t kMaximumChannels = 8;
constexpr std::uint32_t kMaximumElements = 8U * 2048U;

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

}  // namespace

extern "C" resonith_status resonith_raw_basis_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_raw_basis_info* info
) {
    if (data == nullptr || info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *info = {};
    if (data_size < kHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::uint16_t channels = read_u16(data);
    const std::uint16_t flags = read_u16(data + 2U);
    const std::uint32_t samples_per_channel = read_u32(data + 4U);
    const std::uint64_t elements =
        static_cast<std::uint64_t>(channels) * samples_per_channel;
    if (
        channels == 0U
        || channels > kMaximumChannels
        || samples_per_channel == 0U
        || elements > kMaximumElements
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (flags != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    const std::size_t expected_bytes =
        kHeaderBytes + static_cast<std::size_t>(elements) * 2U;
    if (data_size != expected_bytes) {
        return data_size < expected_bytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    info->samples_per_channel = samples_per_channel;
    info->total_elements = static_cast<std::uint32_t>(elements);
    info->channels = channels;
    info->reserved = 0U;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_raw_basis_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* elements_written
) {
    if (elements_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *elements_written = 0U;
    resonith_raw_basis_info info{};
    const resonith_status inspect_status = resonith_raw_basis_inspect(
        data,
        data_size,
        &info
    );
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    if (output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < info.total_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    const std::uint8_t* samples = data + kHeaderBytes;
    for (std::uint32_t index = 0; index < info.total_elements; ++index) {
        output[index] = static_cast<std::int16_t>(
            read_u16(samples + static_cast<std::size_t>(index) * 2U)
        );
    }
    *elements_written = info.total_elements;
    return RESONITH_STATUS_OK;
}
