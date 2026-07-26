#include "resonith/liftpack.h"

#include "integrity.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kStreamHeaderBytes = 15;
constexpr std::size_t kBlockHeaderBytes = 9;
constexpr std::size_t kChecksumBytes = 4;
constexpr std::uint8_t kVersion = 1;
constexpr std::uint16_t kMinimumBlockSize = 16;
constexpr std::uint16_t kMaximumBlockSize = 32768;
constexpr std::uint32_t kMaximumSampleCount = 0x7fff'ffffU;
constexpr std::uint8_t kMaximumRiceParameter = 20;
constexpr std::uint32_t kMaximumBitsPerCoefficient = 96;
constexpr std::int64_t kMaximumInputMagnitude = 0x7fff'ffffLL;
constexpr std::int64_t kMaximumCoefficientMagnitude = (1LL << 34) - 1;

constexpr std::uint8_t kTransformIdentity = 0;
constexpr std::uint8_t kTransformDelta1 = 1;
constexpr std::uint8_t kTransformDelta2 = 2;
constexpr std::uint8_t kTransformHaar = 3;
constexpr std::uint8_t kTransformLpc = 4;
constexpr std::uint8_t kEntropyRice = 0;
constexpr std::uint8_t kEntropyPacked = 1;
constexpr std::uint8_t kLpcPrecision = 12;
constexpr std::uint8_t kMaximumLpcOrder = 16;
constexpr std::int64_t kMaximumLpcCoefficientSum = 8LL << kLpcPrecision;

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

std::int16_t read_i16(const std::uint8_t* data) noexcept {
    const std::uint16_t raw = read_u16(data);
    const std::int32_t value = raw <= 0x7fffU
        ? static_cast<std::int32_t>(raw)
        : static_cast<std::int32_t>(raw) - 0x1'0000;
    return static_cast<std::int16_t>(value);
}

std::size_t next_power_of_two(std::size_t value) noexcept {
    std::size_t output = 1;
    while (output < value) {
        output <<= 1U;
    }
    return output;
}

std::int64_t floor_divide_two(std::int64_t value) noexcept {
    if (value >= 0) {
        return value / 2;
    }
    return -(((-value) + 1) / 2);
}

bool in_input_range(std::int64_t value) noexcept {
    return value >= -kMaximumInputMagnitude
        && value <= kMaximumInputMagnitude;
}

std::int64_t round_lpc_q12(std::int64_t value) noexcept {
    constexpr std::int64_t half = 1LL << (kLpcPrecision - 1U);
    if (value >= 0) {
        return (value + half) >> kLpcPrecision;
    }
    return -(((-value) + half) >> kLpcPrecision);
}

class BitReader {
public:
    BitReader(
        const std::uint8_t* payload,
        std::size_t payload_bytes,
        std::uint32_t bit_count
    ) noexcept
        : payload_(payload),
          payload_bytes_(payload_bytes),
          bit_count_(bit_count) {}

    bool padding_is_zero() const noexcept {
        if (bit_count_ == 0 || bit_count_ % 8U == 0U) {
            return true;
        }
        const std::uint8_t valid_bits = static_cast<std::uint8_t>(
            bit_count_ % 8U
        );
        const std::uint8_t valid_mask = static_cast<std::uint8_t>(
            (1U << valid_bits) - 1U
        );
        return (payload_[payload_bytes_ - 1] & ~valid_mask) == 0;
    }

    bool read_bit(std::uint8_t& output) noexcept {
        if (position_ >= bit_count_) {
            return false;
        }
        output = static_cast<std::uint8_t>(
            (payload_[position_ / 8U] >> (position_ % 8U)) & 1U
        );
        ++position_;
        return true;
    }

    bool read_bits(unsigned count, std::uint64_t& output) noexcept {
        if (count > 64U || position_ + count > bit_count_) {
            return false;
        }
        output = 0;
        for (unsigned offset = 0; offset < count; ++offset) {
            std::uint8_t bit = 0;
            if (!read_bit(bit)) {
                return false;
            }
            output |= static_cast<std::uint64_t>(bit) << offset;
        }
        return true;
    }

    std::uint32_t position() const noexcept {
        return position_;
    }

private:
    const std::uint8_t* payload_;
    std::size_t payload_bytes_;
    std::uint32_t bit_count_;
    std::uint32_t position_ = 0;
};

resonith_status decode_zigzag(
    std::uint64_t encoded,
    std::int64_t& output
) noexcept {
    const std::uint64_t magnitude = (encoded >> 1U) + (encoded & 1U);
    if (magnitude > static_cast<std::uint64_t>(kMaximumCoefficientMagnitude)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    output = (encoded & 1U) == 0U
        ? static_cast<std::int64_t>(magnitude)
        : -static_cast<std::int64_t>(magnitude);
    return RESONITH_STATUS_OK;
}

resonith_status decode_entropy(
    BitReader& reader,
    std::uint8_t entropy,
    std::uint8_t parameter,
    std::size_t coefficient_count,
    std::int64_t* coefficients
) noexcept {
    for (std::size_t index = 0; index < coefficient_count; ++index) {
        std::uint64_t encoded = 0;
        if (entropy == kEntropyRice) {
            if (parameter > kMaximumRiceParameter) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            std::uint32_t quotient = 0;
            while (true) {
                std::uint8_t bit = 0;
                if (!reader.read_bit(bit)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
                if (bit == 0) {
                    break;
                }
                ++quotient;
                if (quotient > 31U) {
                    return RESONITH_STATUS_PROFILE_BOUND;
                }
            }
            if (quotient == 31U) {
                if (!reader.read_bits(64, encoded)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
            } else {
                std::uint64_t remainder = 0;
                if (!reader.read_bits(parameter, remainder)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
                encoded = (
                    static_cast<std::uint64_t>(quotient) << parameter
                ) | remainder;
            }
        } else if (entropy == kEntropyPacked) {
            if (parameter == 0U || parameter > 64U) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            if (!reader.read_bits(parameter, encoded)) {
                return RESONITH_STATUS_TRUNCATED;
            }
        } else {
            return RESONITH_STATUS_MALFORMED;
        }
        const resonith_status status = decode_zigzag(
            encoded,
            coefficients[index]
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }
    return RESONITH_STATUS_OK;
}

resonith_status inverse_transform(
    std::uint8_t transform,
    std::int64_t* coefficients,
    std::size_t coefficient_count,
    std::size_t sample_count,
    std::int64_t* temporary,
    std::int64_t* output
) noexcept {
    if (transform == kTransformIdentity) {
        std::copy_n(coefficients, sample_count, output);
    } else if (transform == kTransformDelta1) {
        std::int64_t accumulator = 0;
        for (std::size_t index = 0; index < sample_count; ++index) {
            accumulator += coefficients[index];
            if (!in_input_range(accumulator)) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            output[index] = accumulator;
        }
    } else if (transform == kTransformDelta2) {
        if (sample_count > 0) {
            output[0] = coefficients[0];
        }
        if (sample_count > 1) {
            output[1] = coefficients[1] + output[0];
        }
        if (
            (sample_count > 0 && !in_input_range(output[0]))
            || (sample_count > 1 && !in_input_range(output[1]))
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        for (std::size_t index = 2; index < sample_count; ++index) {
            const std::int64_t value = coefficients[index]
                + 2 * output[index - 1]
                - output[index - 2];
            if (!in_input_range(value)) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            output[index] = value;
        }
    } else if (transform == kTransformHaar) {
        std::size_t active = 1;
        while (active < coefficient_count) {
            for (std::size_t index = 0; index < active; ++index) {
                const std::int64_t low = coefficients[index];
                const std::int64_t difference = coefficients[active + index];
                const std::int64_t even = low - floor_divide_two(difference);
                temporary[2 * index] = even;
                temporary[2 * index + 1] = difference + even;
            }
            std::copy_n(temporary, 2 * active, coefficients);
            active *= 2;
        }
        std::copy_n(coefficients, sample_count, output);
    } else {
        return RESONITH_STATUS_MALFORMED;
    }
    for (std::size_t index = 0; index < sample_count; ++index) {
        if (!in_input_range(output[index])) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    }
    return RESONITH_STATUS_OK;
}

resonith_status inverse_lpc(
    const std::int64_t* residual,
    std::size_t sample_count,
    const std::array<std::int16_t, kMaximumLpcOrder>& coefficients,
    std::uint8_t order,
    std::int64_t* output
) noexcept {
    for (std::size_t index = 0; index < sample_count; ++index) {
        std::int64_t value = residual[index];
        if (index >= order) {
            std::int64_t accumulator = 0;
            for (std::uint8_t tap = 0; tap < order; ++tap) {
                accumulator += static_cast<std::int64_t>(coefficients[tap])
                    * output[index - static_cast<std::size_t>(tap) - 1U];
            }
            value += round_lpc_q12(accumulator);
        }
        if (!in_input_range(value)) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        output[index] = value;
    }
    return RESONITH_STATUS_OK;
}

struct ParsedBlock {
    std::size_t byte_offset = 0;
    std::size_t byte_size = 0;
    std::size_t payload_offset = 0;
    std::size_t payload_bytes = 0;
    std::size_t coefficient_count = 0;
    std::uint16_t sample_count = 0;
    std::uint8_t transform = 0;
    std::uint8_t entropy = 0;
    std::uint8_t entropy_parameter = 0;
    std::uint8_t lpc_order = 0;
    std::uint32_t bit_count = 0;
    std::array<std::int16_t, kMaximumLpcOrder> lpc_coefficients{};
};

resonith_status parse_block(
    const std::uint8_t* data,
    std::size_t body_size,
    bool lpc_stream,
    std::size_t expected_length,
    std::size_t& cursor,
    ParsedBlock& block
) noexcept {
    block = ParsedBlock{};
    block.byte_offset = cursor;
    if (cursor > body_size || body_size - cursor < kBlockHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    block.sample_count = read_u16(data + cursor);
    block.transform = data[cursor + 2U];
    block.entropy = data[cursor + 3U];
    block.entropy_parameter = data[cursor + 4U];
    block.bit_count = read_u32(data + cursor + 5U);
    cursor += kBlockHeaderBytes;
    if (block.sample_count != expected_length) {
        return RESONITH_STATUS_MALFORMED;
    }

    block.coefficient_count = block.sample_count;
    if (block.transform == kTransformLpc) {
        if (!lpc_stream || cursor > body_size || body_size - cursor < 2U) {
            return lpc_stream
                ? RESONITH_STATUS_TRUNCATED
                : RESONITH_STATUS_UNSUPPORTED_FEATURE;
        }
        block.lpc_order = data[cursor];
        const std::uint8_t precision = data[cursor + 1U];
        cursor += 2U;
        if (
            block.lpc_order == 0U
            || block.lpc_order > kMaximumLpcOrder
            || block.lpc_order >= block.sample_count
            || precision != kLpcPrecision
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        const std::size_t coefficient_bytes =
            2U * static_cast<std::size_t>(block.lpc_order);
        if (cursor > body_size || coefficient_bytes > body_size - cursor) {
            return RESONITH_STATUS_TRUNCATED;
        }
        std::int64_t coefficient_sum = 0;
        for (std::uint8_t tap = 0U; tap < block.lpc_order; ++tap) {
            const std::int16_t coefficient = read_i16(
                data + cursor + 2U * static_cast<std::size_t>(tap)
            );
            block.lpc_coefficients[tap] = coefficient;
            coefficient_sum += coefficient >= 0
                ? coefficient
                : -static_cast<std::int64_t>(coefficient);
        }
        if (coefficient_sum > kMaximumLpcCoefficientSum) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        cursor += coefficient_bytes;
    } else if (block.transform == kTransformHaar) {
        block.coefficient_count = next_power_of_two(block.sample_count);
    } else if (
        block.transform != kTransformIdentity
        && block.transform != kTransformDelta1
        && block.transform != kTransformDelta2
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        (block.entropy == kEntropyRice
            && block.entropy_parameter > kMaximumRiceParameter)
        || (block.entropy == kEntropyPacked
            && (
                block.entropy_parameter == 0U
                || block.entropy_parameter > 64U
            ))
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        block.entropy != kEntropyRice
        && block.entropy != kEntropyPacked
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        block.bit_count
        > block.coefficient_count * static_cast<std::size_t>(
            kMaximumBitsPerCoefficient
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    block.payload_bytes = (
        static_cast<std::size_t>(block.bit_count) + 7U
    ) / 8U;
    if (cursor > body_size || block.payload_bytes > body_size - cursor) {
        return RESONITH_STATUS_TRUNCATED;
    }
    block.payload_offset = cursor;
    BitReader reader(
        data + block.payload_offset,
        block.payload_bytes,
        block.bit_count
    );
    if (!reader.padding_is_zero()) {
        return RESONITH_STATUS_MALFORMED;
    }
    cursor += block.payload_bytes;
    block.byte_size = cursor - block.byte_offset;
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_liftpack_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_liftpack_info* info
) {
    if (data == nullptr || info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (data_size < kStreamHeaderBytes + kChecksumBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (
        std::memcmp(data, "RSL1", 4) != 0
        && std::memcmp(data, "RSL2", 4) != 0
    ) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4] != kVersion) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    const std::uint16_t block_size = read_u16(data + 5);
    const std::uint32_t sample_count = read_u32(data + 7);
    const std::uint32_t block_count = read_u32(data + 11);
    if (
        block_size < kMinimumBlockSize
        || block_size > kMaximumBlockSize
        || sample_count > kMaximumSampleCount
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint32_t canonical_blocks = sample_count == 0U
        ? 0U
        : (sample_count + block_size - 1U) / block_size;
    if (block_count != canonical_blocks) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::size_t body_size = data_size - kChecksumBytes;
    if (
        resonith::internal::crc32(data, body_size)
        != read_u32(data + body_size)
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }
    info->sample_count = sample_count;
    info->block_count = block_count;
    info->block_size = block_size;
    info->reserved = 0;
    return RESONITH_STATUS_OK;
}

extern "C" std::size_t resonith_liftpack_required_scratch(
    const resonith_liftpack_info* info
) {
    if (
        info == nullptr
        || info->block_size < kMinimumBlockSize
        || info->block_size > kMaximumBlockSize
    ) {
        return 0;
    }
    return 2U * next_power_of_two(info->block_size);
}

extern "C" resonith_status resonith_liftpack_index_blocks(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_liftpack_block_info* entries,
    std::size_t entry_capacity,
    std::size_t* entries_written
) {
    if (entries_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *entries_written = 0;
    resonith_liftpack_info info{};
    const resonith_status inspect_status = resonith_liftpack_inspect(
        data,
        data_size,
        &info
    );
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    if (
        (info.block_count != 0U && entries == nullptr)
        || entry_capacity < info.block_count
    ) {
        return entries == nullptr && info.block_count != 0U
            ? RESONITH_STATUS_INVALID_ARGUMENT
            : RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    const std::size_t body_size = data_size - kChecksumBytes;
    const bool lpc_stream = std::memcmp(data, "RSL2", 4) == 0;
    std::size_t cursor = kStreamHeaderBytes;
    std::size_t sample_offset = 0;
    for (std::uint32_t index = 0; index < info.block_count; ++index) {
        const std::size_t expected_length = std::min<std::size_t>(
            info.block_size,
            info.sample_count - sample_offset
        );
        ParsedBlock block{};
        const resonith_status status = parse_block(
            data,
            body_size,
            lpc_stream,
            expected_length,
            cursor,
            block
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        entries[index] = resonith_liftpack_block_info{
            static_cast<std::uint64_t>(block.byte_offset),
            static_cast<std::uint64_t>(block.byte_size),
            static_cast<std::uint32_t>(sample_offset),
            block.bit_count,
            block.sample_count,
            block.transform,
            block.entropy,
            block.entropy_parameter,
            block.lpc_order,
            0U,
        };
        sample_offset += block.sample_count;
    }
    if (sample_offset != info.sample_count || cursor != body_size) {
        return RESONITH_STATUS_MALFORMED;
    }
    *entries_written = info.block_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_liftpack_decode_block(
    const std::uint8_t* data,
    std::size_t data_size,
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
    resonith_liftpack_info info{};
    const resonith_status inspect_status = resonith_liftpack_inspect(
        data,
        data_size,
        &info
    );
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    if (block_index >= info.block_count) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    if (output == nullptr || scratch == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    const std::size_t required_scratch = resonith_liftpack_required_scratch(
        &info
    );
    if (scratch_count < required_scratch) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    const std::size_t body_size = data_size - kChecksumBytes;
    const bool lpc_stream = std::memcmp(data, "RSL2", 4) == 0;
    std::size_t cursor = kStreamHeaderBytes;
    std::size_t current_sample_offset = 0U;
    std::size_t target_sample_offset = 0U;
    ParsedBlock target{};
    for (std::uint32_t index = 0; index < info.block_count; ++index) {
        const std::size_t expected_length = std::min<std::size_t>(
            info.block_size,
            info.sample_count - current_sample_offset
        );
        ParsedBlock parsed{};
        const resonith_status status = parse_block(
            data,
            body_size,
            lpc_stream,
            expected_length,
            cursor,
            parsed
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (index == block_index) {
            target = parsed;
            target_sample_offset = current_sample_offset;
        }
        current_sample_offset += parsed.sample_count;
    }
    if (current_sample_offset != info.sample_count || cursor != body_size) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (output_capacity < target.sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    BitReader reader(
        data + target.payload_offset,
        target.payload_bytes,
        target.bit_count
    );
    resonith_status status = decode_entropy(
        reader,
        target.entropy,
        target.entropy_parameter,
        target.coefficient_count,
        scratch
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (reader.position() != target.bit_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    status = target.transform == kTransformLpc
        ? inverse_lpc(
            scratch,
            target.sample_count,
            target.lpc_coefficients,
            target.lpc_order,
            output
        )
        : inverse_transform(
            target.transform,
            scratch,
            target.coefficient_count,
            target.sample_count,
            scratch + target.coefficient_count,
            output
        );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    *sample_offset = static_cast<std::uint32_t>(target_sample_offset);
    *samples_written = target.sample_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_liftpack_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::int64_t* output,
    std::size_t output_capacity,
    std::int64_t* scratch,
    std::size_t scratch_count,
    std::size_t* samples_written
) {
    if (samples_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *samples_written = 0;
    resonith_liftpack_info info{};
    const resonith_status inspect_status = resonith_liftpack_inspect(
        data,
        data_size,
        &info
    );
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    if (
        (info.sample_count != 0U && output == nullptr)
        || scratch == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < info.sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    const std::size_t required_scratch = resonith_liftpack_required_scratch(
        &info
    );
    if (scratch_count < required_scratch) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    const std::size_t body_size = data_size - kChecksumBytes;
    const bool lpc_stream = std::memcmp(data, "RSL2", 4) == 0;
    std::size_t cursor = kStreamHeaderBytes;
    std::size_t output_offset = 0;
    for (std::uint32_t block = 0; block < info.block_count; ++block) {
        const std::size_t expected_length = std::min<std::size_t>(
            info.block_size,
            info.sample_count - output_offset
        );
        ParsedBlock parsed{};
        resonith_status status = parse_block(
            data,
            body_size,
            lpc_stream,
            expected_length,
            cursor,
            parsed
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }

        BitReader reader(
            data + parsed.payload_offset,
            parsed.payload_bytes,
            parsed.bit_count
        );
        status = decode_entropy(
            reader,
            parsed.entropy,
            parsed.entropy_parameter,
            parsed.coefficient_count,
            scratch
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (reader.position() != parsed.bit_count) {
            return RESONITH_STATUS_MALFORMED;
        }
        status = parsed.transform == kTransformLpc
            ? inverse_lpc(
                scratch,
                parsed.sample_count,
                parsed.lpc_coefficients,
                parsed.lpc_order,
                output + output_offset
            )
            : inverse_transform(
                parsed.transform,
                scratch,
                parsed.coefficient_count,
                parsed.sample_count,
                scratch + parsed.coefficient_count,
                output + output_offset
            );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        output_offset += parsed.sample_count;
    }
    if (output_offset != info.sample_count || cursor != body_size) {
        return RESONITH_STATUS_MALFORMED;
    }
    *samples_written = output_offset;
    return RESONITH_STATUS_OK;
}
