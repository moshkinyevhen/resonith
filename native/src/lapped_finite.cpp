#include "resonith/lapped_finite.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kHeaderBytes = 43U;
constexpr std::size_t kCompactHeaderBytes = 28U;
constexpr std::size_t kRiceValueCompactHeaderBytes = 30U;
constexpr std::uint8_t kVersion = 1U;
constexpr std::uint8_t kEntropyRice = 0U;
constexpr std::uint8_t kEntropyPacked = 1U;
constexpr std::uint8_t kMaximumRiceParameter = 20U;
constexpr std::uint32_t kRiceEscapeQuotient = 31U;
constexpr std::uint16_t kMaximumChannels = 8U;
constexpr std::uint16_t kMaximumBands = 64U;
constexpr std::uint16_t kMaximumHalfWindow = 1024U;
constexpr std::uint32_t kMaximumSymbols = 64U << 20U;
constexpr std::size_t kMaximumPayloadBytes = 512U << 20U;
constexpr std::uint64_t kTop = (1ULL << 32U) - 1U;
constexpr std::uint64_t kHalf = 1ULL << 31U;
constexpr std::uint64_t kQuarter = 1ULL << 30U;
constexpr std::uint64_t kThreeQuarters = 3ULL << 30U;
constexpr std::uint32_t kModelLimit = 1U << 14U;

class bit_reader {
public:
    bit_reader(
        const std::uint8_t* data,
        std::size_t data_size,
        std::uint32_t bit_count
    ) noexcept
        : data_(data),
          data_size_(data_size),
          bit_count_(bit_count) {}

    bool valid_padding() const noexcept {
        if (
            data_ == nullptr
            || bit_count_ > data_size_ * 8U
            || data_size_ != (static_cast<std::size_t>(bit_count_) + 7U) / 8U
        ) {
            return false;
        }
        if (bit_count_ % 8U == 0U || data_size_ == 0U) {
            return true;
        }
        const std::uint8_t mask = static_cast<std::uint8_t>(
            (1U << (bit_count_ % 8U)) - 1U
        );
        return (data_[data_size_ - 1U] & static_cast<std::uint8_t>(~mask)) == 0U;
    }

    bool read_bit(std::uint32_t* value) noexcept {
        if (value == nullptr || position_ >= bit_count_) {
            return false;
        }
        *value = (
            data_[position_ / 8U] >> (position_ % 8U)
        ) & 1U;
        ++position_;
        return true;
    }

    bool read_bit_or_zero(std::uint32_t* value) noexcept {
        if (value == nullptr) {
            return false;
        }
        if (position_ == bit_count_) {
            *value = 0U;
            return true;
        }
        return read_bit(value);
    }

    bool read_bits(std::uint32_t count, std::uint64_t* value) noexcept {
        if (
            value == nullptr
            || count > 64U
            || position_ > bit_count_
            || count > bit_count_ - position_
        ) {
            return false;
        }
        std::uint64_t output = 0U;
        for (std::uint32_t offset = 0U; offset < count; ++offset) {
            std::uint32_t bit = 0U;
            if (!read_bit(&bit)) {
                return false;
            }
            output |= static_cast<std::uint64_t>(bit) << offset;
        }
        *value = output;
        return true;
    }

    std::uint32_t position() const noexcept {
        return position_;
    }

private:
    const std::uint8_t* data_;
    std::size_t data_size_;
    std::uint32_t bit_count_;
    std::uint32_t position_ = 0U;
};

class bit_writer {
public:
    bit_writer(std::uint8_t* output, std::size_t capacity) noexcept
        : output_(output), capacity_(capacity) {}

    bool write_bit(std::uint32_t value) noexcept {
        if (value > 1U || output_ == nullptr) {
            return false;
        }
        if (used_ == 0U) {
            if (size_ >= capacity_) {
                return false;
            }
            output_[size_] = 0U;
        }
        output_[size_] |= static_cast<std::uint8_t>(value << used_);
        ++used_;
        ++bit_count_;
        if (used_ == 8U) {
            used_ = 0U;
            ++size_;
        }
        return true;
    }

    bool emit_with_pending(
        std::uint32_t value,
        std::uint32_t pending
    ) noexcept {
        if (!write_bit(value)) {
            return false;
        }
        for (std::uint32_t index = 0U; index < pending; ++index) {
            if (!write_bit(1U - value)) {
                return false;
            }
        }
        return true;
    }

    bool write_bits(std::uint64_t value, std::uint32_t count) noexcept {
        if (count > 64U) {
            return false;
        }
        for (std::uint32_t offset = 0U; offset < count; ++offset) {
            if (
                !write_bit(
                    static_cast<std::uint32_t>((value >> offset) & 1U)
                )
            ) {
                return false;
            }
        }
        return true;
    }

    std::size_t size() const noexcept {
        return size_ + (used_ == 0U ? 0U : 1U);
    }

    std::uint32_t bit_count() const noexcept {
        return bit_count_;
    }

private:
    std::uint8_t* output_;
    std::size_t capacity_;
    std::size_t size_ = 0U;
    std::uint32_t bit_count_ = 0U;
    std::uint8_t used_ = 0U;
};

struct adaptive_model {
    std::array<std::uint16_t, 512U> counts{};
    std::uint16_t alphabet_size = 0U;
    std::uint32_t total = 0U;

    bool reset(std::uint16_t alphabet) noexcept {
        if (alphabet < 2U || alphabet > counts.size()) {
            return false;
        }
        alphabet_size = alphabet;
        total = alphabet;
        for (std::uint16_t index = 0U; index < alphabet; ++index) {
            counts[index] = 1U;
        }
        return true;
    }

    bool resolve(
        std::uint32_t scaled,
        std::uint16_t* symbol,
        std::uint32_t* cumulative_low,
        std::uint32_t* cumulative_high
    ) const noexcept {
        if (
            symbol == nullptr
            || cumulative_low == nullptr
            || cumulative_high == nullptr
            || scaled >= total
        ) {
            return false;
        }
        std::uint32_t cumulative = 0U;
        for (
            std::uint16_t candidate = 0U;
            candidate < alphabet_size;
            ++candidate
        ) {
            const std::uint32_t following = cumulative + counts[candidate];
            if (scaled < following) {
                *symbol = candidate;
                *cumulative_low = cumulative;
                *cumulative_high = following;
                return true;
            }
            cumulative = following;
        }
        return false;
    }

    bool interval(
        std::uint16_t symbol,
        std::uint32_t* cumulative_low,
        std::uint32_t* cumulative_high
    ) const noexcept {
        if (
            symbol >= alphabet_size
            || cumulative_low == nullptr
            || cumulative_high == nullptr
        ) {
            return false;
        }
        std::uint32_t cumulative = 0U;
        for (std::uint16_t index = 0U; index < symbol; ++index) {
            cumulative += counts[index];
        }
        *cumulative_low = cumulative;
        *cumulative_high = cumulative + counts[symbol];
        return true;
    }

    void update(std::uint16_t symbol) noexcept {
        ++counts[symbol];
        ++total;
        if (total < kModelLimit) {
            return;
        }
        total = 0U;
        for (std::uint16_t index = 0U; index < alphabet_size; ++index) {
            counts[index] = static_cast<std::uint16_t>(
                (static_cast<std::uint32_t>(counts[index]) + 1U) / 2U
            );
            if (counts[index] == 0U) {
                counts[index] = 1U;
            }
            total += counts[index];
        }
    }
};

resonith_status encode_adaptive(
    const std::uint16_t* symbols,
    std::size_t symbol_count,
    std::uint16_t alphabet_size,
    std::uint8_t* output,
    std::size_t output_capacity,
    std::size_t* output_size,
    std::uint32_t* bit_count
) noexcept {
    if (
        output_size == nullptr
        || bit_count == nullptr
        || alphabet_size < 2U
        || alphabet_size > 512U
        || symbol_count > kMaximumSymbols
        || (symbol_count != 0U && (symbols == nullptr || output == nullptr))
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *output_size = 0U;
    *bit_count = 0U;
    if (symbol_count == 0U) {
        return RESONITH_STATUS_OK;
    }

    adaptive_model model{};
    if (!model.reset(alphabet_size)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    bit_writer writer(output, output_capacity);
    std::uint64_t low = 0U;
    std::uint64_t high = kTop;
    std::uint32_t pending = 0U;
    for (std::size_t index = 0U; index < symbol_count; ++index) {
        const std::uint16_t symbol = symbols[index];
        std::uint32_t cumulative_low = 0U;
        std::uint32_t cumulative_high = 0U;
        if (
            !model.interval(
                symbol,
                &cumulative_low,
                &cumulative_high
            )
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        const std::uint64_t width = high - low + 1U;
        high = low + width * cumulative_high / model.total - 1U;
        low = low + width * cumulative_low / model.total;
        while (true) {
            if (high < kHalf) {
                if (!writer.emit_with_pending(0U, pending)) {
                    return RESONITH_STATUS_OUTPUT_TOO_SMALL;
                }
                pending = 0U;
            } else if (low >= kHalf) {
                if (!writer.emit_with_pending(1U, pending)) {
                    return RESONITH_STATUS_OUTPUT_TOO_SMALL;
                }
                pending = 0U;
                low -= kHalf;
                high -= kHalf;
            } else if (low >= kQuarter && high < kThreeQuarters) {
                ++pending;
                low -= kQuarter;
                high -= kQuarter;
            } else {
                break;
            }
            low = (low << 1U) & kTop;
            high = ((high << 1U) | 1U) & kTop;
        }
        model.update(symbol);
    }
    ++pending;
    if (
        !writer.emit_with_pending(
            low < kQuarter ? 0U : 1U,
            pending
        )
    ) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    *output_size = writer.size();
    *bit_count = writer.bit_count();
    return RESONITH_STATUS_OK;
}

std::uint64_t zigzag_encode(std::int16_t value) noexcept {
    const std::int64_t wide = value;
    return wide >= 0
        ? static_cast<std::uint64_t>(wide) * 2U
        : static_cast<std::uint64_t>(-wide * 2 - 1);
}

std::uint8_t bit_width(std::uint64_t value) noexcept {
    std::uint8_t width = 1U;
    while (value > 1U) {
        value >>= 1U;
        ++width;
    }
    return width;
}

std::uint64_t bounded_rice_cost(
    const std::int16_t* values,
    std::size_t value_count,
    std::uint8_t parameter
) noexcept {
    std::uint64_t total = 0U;
    for (std::size_t index = 0U; index < value_count; ++index) {
        const std::uint64_t value = zigzag_encode(values[index]);
        const std::uint64_t quotient = value >> parameter;
        total += quotient < kRiceEscapeQuotient
            ? quotient + 1U + parameter
            : kRiceEscapeQuotient + 1U + 64U;
    }
    return total;
}

resonith_status encode_int16_entropy(
    const std::int16_t* values,
    std::size_t value_count,
    std::uint8_t* entropy_mode,
    std::uint8_t* entropy_parameter,
    std::uint8_t* output,
    std::size_t output_capacity,
    std::size_t* output_size,
    std::uint32_t* bit_count
) noexcept {
    if (
        entropy_mode == nullptr
        || entropy_parameter == nullptr
        || output_size == nullptr
        || bit_count == nullptr
        || value_count > kMaximumSymbols
        || (value_count != 0U && (values == nullptr || output == nullptr))
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *entropy_mode = kEntropyRice;
    *entropy_parameter = 0U;
    *output_size = 0U;
    *bit_count = 0U;
    if (value_count == 0U) {
        return RESONITH_STATUS_OK;
    }

    std::uint64_t maximum = 0U;
    for (std::size_t index = 0U; index < value_count; ++index) {
        maximum = std::max(maximum, zigzag_encode(values[index]));
    }
    const std::uint8_t packed_width = bit_width(maximum);
    const std::uint64_t packed_bits =
        static_cast<std::uint64_t>(value_count) * packed_width;

    std::uint8_t rice_parameter = 0U;
    std::uint64_t rice_bits = bounded_rice_cost(values, value_count, 0U);
    for (
        std::uint8_t candidate = 1U;
        candidate <= kMaximumRiceParameter;
        ++candidate
    ) {
        const std::uint64_t candidate_bits = bounded_rice_cost(
            values,
            value_count,
            candidate
        );
        if (candidate_bits < rice_bits) {
            rice_bits = candidate_bits;
            rice_parameter = candidate;
        }
    }

    const bool use_rice = rice_bits <= packed_bits;
    const std::uint64_t selected_bits = use_rice ? rice_bits : packed_bits;
    if (selected_bits > std::numeric_limits<std::uint32_t>::max()) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    *entropy_mode = use_rice ? kEntropyRice : kEntropyPacked;
    *entropy_parameter = use_rice ? rice_parameter : packed_width;

    bit_writer writer(output, output_capacity);
    for (std::size_t index = 0U; index < value_count; ++index) {
        const std::uint64_t value = zigzag_encode(values[index]);
        if (!use_rice) {
            if (!writer.write_bits(value, packed_width)) {
                return RESONITH_STATUS_OUTPUT_TOO_SMALL;
            }
            continue;
        }
        const std::uint64_t quotient = value >> rice_parameter;
        const std::uint64_t prefix = std::min<std::uint64_t>(
            quotient,
            kRiceEscapeQuotient
        );
        for (std::uint64_t unary = 0U; unary < prefix; ++unary) {
            if (!writer.write_bit(1U)) {
                return RESONITH_STATUS_OUTPUT_TOO_SMALL;
            }
        }
        if (!writer.write_bit(0U)) {
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }
        if (quotient < kRiceEscapeQuotient) {
            const std::uint64_t mask = rice_parameter == 0U
                ? 0U
                : (1ULL << rice_parameter) - 1U;
            if (!writer.write_bits(value & mask, rice_parameter)) {
                return RESONITH_STATUS_OUTPUT_TOO_SMALL;
            }
        } else if (!writer.write_bits(value, 64U)) {
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }
    }
    if (writer.bit_count() != selected_bits) {
        return RESONITH_STATUS_MALFORMED;
    }
    *output_size = writer.size();
    *bit_count = writer.bit_count();
    return RESONITH_STATUS_OK;
}

struct arithmetic_decoder {
    bit_reader* reader = nullptr;
    adaptive_model model{};
    std::uint64_t low = 0U;
    std::uint64_t high = kTop;
    std::uint64_t code = 0U;

    bool initialize(
        bit_reader* source,
        std::uint16_t alphabet_size
    ) noexcept {
        if (
            source == nullptr
            || !source->valid_padding()
            || !model.reset(alphabet_size)
        ) {
            return false;
        }
        reader = source;
        for (std::uint32_t index = 0U; index < 32U; ++index) {
            std::uint32_t bit = 0U;
            if (!reader->read_bit_or_zero(&bit)) {
                return false;
            }
            code = ((code << 1U) | bit) & kTop;
        }
        return true;
    }

    bool decode(std::uint16_t* output) noexcept {
        if (output == nullptr || reader == nullptr) {
            return false;
        }
        const std::uint64_t width = high - low + 1U;
        const std::uint64_t numerator =
            (code - low + 1U) * model.total - 1U;
        const std::uint32_t scaled = static_cast<std::uint32_t>(
            numerator / width
        );
        std::uint16_t symbol = 0U;
        std::uint32_t cumulative_low = 0U;
        std::uint32_t cumulative_high = 0U;
        if (
            !model.resolve(
                scaled,
                &symbol,
                &cumulative_low,
                &cumulative_high
            )
        ) {
            return false;
        }
        high = low + width * cumulative_high / model.total - 1U;
        low = low + width * cumulative_low / model.total;
        while (true) {
            if (high < kHalf) {
                // The interval is already in the lower half.
            } else if (low >= kHalf) {
                low -= kHalf;
                high -= kHalf;
                code -= kHalf;
            } else if (low >= kQuarter && high < kThreeQuarters) {
                low -= kQuarter;
                high -= kQuarter;
                code -= kQuarter;
            } else {
                break;
            }
            std::uint32_t bit = 0U;
            if (!reader->read_bit_or_zero(&bit)) {
                return false;
            }
            low = (low << 1U) & kTop;
            high = ((high << 1U) | 1U) & kTop;
            code = ((code << 1U) | bit) & kTop;
        }
        model.update(symbol);
        *output = symbol;
        return true;
    }
};

struct parsed_finite {
    std::uint8_t count_entropy = 0U;
    std::uint8_t count_parameter = 0U;
    std::uint8_t value_entropy = 0U;
    std::uint8_t value_parameter = 0U;
    bool bounded_values = false;
    std::uint16_t gap_threshold = 0U;
    std::uint32_t frame_count = 0U;
    std::uint16_t channels = 0U;
    std::uint16_t band_count = 0U;
    std::uint32_t coefficient_count = 0U;
    std::uint32_t scale_bits = 0U;
    std::uint32_t count_bits = 0U;
    std::uint32_t gap_bits = 0U;
    std::uint32_t raw_gap_bits = 0U;
    std::uint32_t value_bits = 0U;
    const std::uint8_t* scale_payload = nullptr;
    const std::uint8_t* count_payload = nullptr;
    const std::uint8_t* gap_payload = nullptr;
    const std::uint8_t* raw_gap_payload = nullptr;
    const std::uint8_t* value_payload = nullptr;
};

std::uint16_t read_u16(const std::uint8_t* data) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data[0U])
        | (static_cast<std::uint16_t>(data[1U]) << 8U)
    );
}

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(
        static_cast<std::uint32_t>(data[0U])
        | (static_cast<std::uint32_t>(data[1U]) << 8U)
        | (static_cast<std::uint32_t>(data[2U]) << 16U)
        | (static_cast<std::uint32_t>(data[3U]) << 24U)
    );
}

bool checked_product(
    std::size_t left,
    std::size_t right,
    std::size_t* output
) noexcept {
    if (
        output == nullptr
        || (
            right != 0U
            && left > std::numeric_limits<std::size_t>::max() / right
        )
    ) {
        return false;
    }
    *output = left * right;
    return true;
}

std::size_t bit_bytes(std::uint32_t bits) noexcept {
    return (static_cast<std::size_t>(bits) + 7U) / 8U;
}

bool valid_entropy(std::uint8_t mode, std::uint8_t parameter) noexcept {
    return (
        mode == kEntropyRice && parameter <= kMaximumRiceParameter
    ) || (
        mode == kEntropyPacked && parameter >= 1U && parameter <= 64U
    );
}

std::uint32_t position_width(std::uint16_t half_window) noexcept {
    std::uint32_t width = 0U;
    std::uint32_t maximum =
        static_cast<std::uint32_t>(half_window) - 1U;
    while (maximum != 0U) {
        ++width;
        maximum >>= 1U;
    }
    return width == 0U ? 1U : width;
}

resonith_status parse_finite(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint16_t half_window,
    parsed_finite* parsed,
    resonith_lapped_finite_requirements* requirements
) noexcept {
    if (
        data == nullptr
        || parsed == nullptr
        || requirements == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (data_size < kHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (data_size > kMaximumPayloadBytes) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (std::memcmp(data, "LAF1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4U] != kVersion) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    parsed->count_entropy = data[6U];
    parsed->count_parameter = data[7U];
    parsed->gap_threshold = read_u16(data + 9U);
    parsed->frame_count = read_u32(data + 11U);
    parsed->channels = read_u16(data + 15U);
    parsed->band_count = read_u16(data + 17U);
    parsed->coefficient_count = read_u32(data + 19U);
    parsed->scale_bits = read_u32(data + 23U);
    parsed->count_bits = read_u32(data + 27U);
    parsed->gap_bits = read_u32(data + 31U);
    parsed->raw_gap_bits = read_u32(data + 35U);
    parsed->value_bits = read_u32(data + 39U);
    if (
        data[5U] != 0U
        || data[8U] != 0U
        || !valid_entropy(
            parsed->count_entropy,
            parsed->count_parameter
        )
        || half_window < 2U
        || half_window > kMaximumHalfWindow
        || parsed->channels == 0U
        || parsed->channels > kMaximumChannels
        || parsed->band_count == 0U
        || parsed->band_count > kMaximumBands
        || parsed->frame_count == 0U
        || parsed->gap_threshold == 0U
        || parsed->gap_threshold > half_window
        || parsed->coefficient_count > kMaximumSymbols
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t maximum_coefficients = 0U;
    if (
        !checked_product(
            parsed->channels,
            parsed->frame_count,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            parsed->band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            half_window,
            &maximum_coefficients
        )
        || scale_elements > kMaximumSymbols
        || parsed->coefficient_count > maximum_coefficients
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::size_t scale_bytes = bit_bytes(parsed->scale_bits);
    const std::size_t count_bytes = bit_bytes(parsed->count_bits);
    const std::size_t gap_bytes = bit_bytes(parsed->gap_bits);
    const std::size_t raw_gap_bytes = bit_bytes(parsed->raw_gap_bits);
    const std::size_t value_bytes = bit_bytes(parsed->value_bits);
    std::size_t consumed = kHeaderBytes;
    for (
        const std::size_t field_bytes :
        {scale_bytes, count_bytes, gap_bytes, raw_gap_bytes, value_bytes}
    ) {
        if (field_bytes > data_size - consumed) {
            return RESONITH_STATUS_TRUNCATED;
        }
        consumed += field_bytes;
    }
    if (consumed != data_size) {
        return RESONITH_STATUS_MALFORMED;
    }
    parsed->scale_payload = data + kHeaderBytes;
    parsed->count_payload = parsed->scale_payload + scale_bytes;
    parsed->gap_payload = parsed->count_payload + count_bytes;
    parsed->raw_gap_payload = parsed->gap_payload + gap_bytes;
    parsed->value_payload = parsed->raw_gap_payload + raw_gap_bytes;
    requirements->transform_frame_count = parsed->frame_count;
    requirements->channels = parsed->channels;
    requirements->band_count = parsed->band_count;
    requirements->half_window = half_window;
    requirements->gap_threshold = parsed->gap_threshold;
    requirements->scale_elements = scale_elements;
    requirements->count_elements = channel_frames;
    requirements->position_elements = parsed->coefficient_count;
    requirements->coefficient_elements = parsed->coefficient_count;
    return RESONITH_STATUS_OK;
}

resonith_status parse_compact_finite(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_lapped_requirements& shape,
    parsed_finite* parsed,
    resonith_lapped_finite_requirements* requirements
) noexcept {
    if (
        data == nullptr
        || parsed == nullptr
        || requirements == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (data_size < kCompactHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (data_size > kMaximumPayloadBytes) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    parsed->count_entropy = data[0U];
    parsed->count_parameter = data[1U];
    parsed->gap_threshold = read_u16(data + 2U);
    parsed->frame_count = shape.transform_frame_count;
    parsed->channels = shape.output_channels;
    parsed->band_count = shape.band_count;
    parsed->coefficient_count = read_u32(data + 4U);
    parsed->scale_bits = read_u32(data + 8U);
    parsed->count_bits = read_u32(data + 12U);
    parsed->gap_bits = read_u32(data + 16U);
    parsed->raw_gap_bits = read_u32(data + 20U);
    parsed->value_bits = read_u32(data + 24U);
    if (
        !valid_entropy(
            parsed->count_entropy,
            parsed->count_parameter
        )
        || shape.transform_frame_count == 0U
        || shape.output_channels == 0U
        || shape.output_channels > kMaximumChannels
        || shape.band_count == 0U
        || shape.band_count > kMaximumBands
        || shape.half_window < 2U
        || shape.half_window > kMaximumHalfWindow
        || parsed->gap_threshold == 0U
        || parsed->gap_threshold > shape.half_window
        || parsed->coefficient_count > kMaximumSymbols
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t maximum_coefficients = 0U;
    if (
        !checked_product(
            shape.output_channels,
            shape.transform_frame_count,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            shape.band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            shape.half_window,
            &maximum_coefficients
        )
        || scale_elements > kMaximumSymbols
        || parsed->coefficient_count > maximum_coefficients
        || shape.scale_elements != scale_elements
        || shape.count_elements != channel_frames
        || shape.position_elements != parsed->coefficient_count
        || shape.coefficient_elements != parsed->coefficient_count
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    const std::size_t scale_bytes = bit_bytes(parsed->scale_bits);
    const std::size_t count_bytes = bit_bytes(parsed->count_bits);
    const std::size_t gap_bytes = bit_bytes(parsed->gap_bits);
    const std::size_t raw_gap_bytes = bit_bytes(parsed->raw_gap_bits);
    const std::size_t value_bytes = bit_bytes(parsed->value_bits);
    std::size_t consumed = kCompactHeaderBytes;
    for (
        const std::size_t field_bytes :
        {scale_bytes, count_bytes, gap_bytes, raw_gap_bytes, value_bytes}
    ) {
        if (field_bytes > data_size - consumed) {
            return RESONITH_STATUS_TRUNCATED;
        }
        consumed += field_bytes;
    }
    if (consumed != data_size) {
        return RESONITH_STATUS_MALFORMED;
    }

    parsed->scale_payload = data + kCompactHeaderBytes;
    parsed->count_payload = parsed->scale_payload + scale_bytes;
    parsed->gap_payload = parsed->count_payload + count_bytes;
    parsed->raw_gap_payload = parsed->gap_payload + gap_bytes;
    parsed->value_payload = parsed->raw_gap_payload + raw_gap_bytes;
    requirements->transform_frame_count = shape.transform_frame_count;
    requirements->channels = shape.output_channels;
    requirements->band_count = shape.band_count;
    requirements->half_window = shape.half_window;
    requirements->gap_threshold = parsed->gap_threshold;
    requirements->scale_elements = scale_elements;
    requirements->count_elements = channel_frames;
    requirements->position_elements = parsed->coefficient_count;
    requirements->coefficient_elements = parsed->coefficient_count;
    return RESONITH_STATUS_OK;
}

resonith_status parse_compact_rice_value(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_lapped_requirements& shape,
    parsed_finite* parsed,
    resonith_lapped_finite_requirements* requirements
) noexcept {
    if (
        data == nullptr
        || parsed == nullptr
        || requirements == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (data_size < kRiceValueCompactHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (data_size > kMaximumPayloadBytes) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    parsed->count_entropy = data[0U];
    parsed->count_parameter = data[1U];
    parsed->value_entropy = data[2U];
    parsed->value_parameter = data[3U];
    parsed->bounded_values = true;
    parsed->gap_threshold = read_u16(data + 4U);
    parsed->frame_count = shape.transform_frame_count;
    parsed->channels = shape.output_channels;
    parsed->band_count = shape.band_count;
    parsed->coefficient_count = read_u32(data + 6U);
    parsed->scale_bits = read_u32(data + 10U);
    parsed->count_bits = read_u32(data + 14U);
    parsed->gap_bits = read_u32(data + 18U);
    parsed->raw_gap_bits = read_u32(data + 22U);
    parsed->value_bits = read_u32(data + 26U);
    if (
        !valid_entropy(
            parsed->count_entropy,
            parsed->count_parameter
        )
        || !valid_entropy(
            parsed->value_entropy,
            parsed->value_parameter
        )
        || shape.transform_frame_count == 0U
        || shape.output_channels == 0U
        || shape.output_channels > kMaximumChannels
        || shape.band_count == 0U
        || shape.band_count > kMaximumBands
        || shape.half_window < 2U
        || shape.half_window > kMaximumHalfWindow
        || parsed->gap_threshold == 0U
        || parsed->gap_threshold > shape.half_window
        || parsed->coefficient_count > kMaximumSymbols
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t maximum_coefficients = 0U;
    if (
        !checked_product(
            shape.output_channels,
            shape.transform_frame_count,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            shape.band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            shape.half_window,
            &maximum_coefficients
        )
        || scale_elements > kMaximumSymbols
        || parsed->coefficient_count > maximum_coefficients
        || shape.scale_elements != scale_elements
        || shape.count_elements != channel_frames
        || shape.position_elements != parsed->coefficient_count
        || shape.coefficient_elements != parsed->coefficient_count
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        parsed->value_entropy == kEntropyPacked
        && (
            static_cast<std::uint64_t>(parsed->coefficient_count)
                * parsed->value_parameter
            != parsed->value_bits
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::size_t scale_bytes = bit_bytes(parsed->scale_bits);
    const std::size_t count_bytes = bit_bytes(parsed->count_bits);
    const std::size_t gap_bytes = bit_bytes(parsed->gap_bits);
    const std::size_t raw_gap_bytes = bit_bytes(parsed->raw_gap_bits);
    const std::size_t value_bytes = bit_bytes(parsed->value_bits);
    std::size_t consumed = kRiceValueCompactHeaderBytes;
    for (
        const std::size_t field_bytes :
        {scale_bytes, count_bytes, gap_bytes, raw_gap_bytes, value_bytes}
    ) {
        if (field_bytes > data_size - consumed) {
            return RESONITH_STATUS_TRUNCATED;
        }
        consumed += field_bytes;
    }
    if (consumed != data_size) {
        return RESONITH_STATUS_MALFORMED;
    }

    parsed->scale_payload = data + kRiceValueCompactHeaderBytes;
    parsed->count_payload = parsed->scale_payload + scale_bytes;
    parsed->gap_payload = parsed->count_payload + count_bytes;
    parsed->raw_gap_payload = parsed->gap_payload + gap_bytes;
    parsed->value_payload = parsed->raw_gap_payload + raw_gap_bytes;
    requirements->transform_frame_count = shape.transform_frame_count;
    requirements->channels = shape.output_channels;
    requirements->band_count = shape.band_count;
    requirements->half_window = shape.half_window;
    requirements->gap_threshold = parsed->gap_threshold;
    requirements->scale_elements = scale_elements;
    requirements->count_elements = channel_frames;
    requirements->position_elements = parsed->coefficient_count;
    requirements->coefficient_elements = parsed->coefficient_count;
    return RESONITH_STATUS_OK;
}

bool decode_unsigned(
    bit_reader* reader,
    std::uint8_t entropy,
    std::uint8_t parameter,
    std::uint64_t* value
) noexcept {
    if (reader == nullptr || value == nullptr) {
        return false;
    }
    if (entropy == kEntropyPacked) {
        return reader->read_bits(parameter, value);
    }
    std::uint32_t quotient = 0U;
    while (true) {
        std::uint32_t bit = 0U;
        if (!reader->read_bit(&bit)) {
            return false;
        }
        if (bit == 0U) {
            break;
        }
        ++quotient;
        if (quotient > kRiceEscapeQuotient) {
            return false;
        }
    }
    if (quotient == kRiceEscapeQuotient) {
        return reader->read_bits(64U, value);
    }
    std::uint64_t remainder = 0U;
    if (!reader->read_bits(parameter, &remainder)) {
        return false;
    }
    *value = (
        static_cast<std::uint64_t>(quotient) << parameter
    ) | remainder;
    return true;
}

bool zigzag_decode(std::uint64_t value, std::int64_t* output) noexcept {
    if (output == nullptr) {
        return false;
    }
    const std::uint64_t magnitude = value >> 1U;
    if (
        magnitude
        > static_cast<std::uint64_t>(
            std::numeric_limits<std::int64_t>::max()
        )
    ) {
        return false;
    }
    *output = (value & 1U) == 0U
        ? static_cast<std::int64_t>(magnitude)
        : -static_cast<std::int64_t>(magnitude) - 1;
    return true;
}

bool valid_workspace(
    const resonith_lapped_finite_requirements& requirements,
    const resonith_lapped_workspace& workspace
) noexcept {
    return (
        workspace.scales != nullptr
        && workspace.scale_capacity >= requirements.scale_elements
        && workspace.counts != nullptr
        && workspace.count_capacity >= requirements.count_elements
        && workspace.positions != nullptr
        && workspace.position_capacity >= requirements.position_elements
        && workspace.coefficients != nullptr
        && workspace.coefficient_capacity
            >= requirements.coefficient_elements
    );
}

resonith_status decode_finite(
    const parsed_finite& parsed,
    const resonith_lapped_finite_requirements& requirements,
    const resonith_lapped_workspace& workspace
) noexcept {
    bit_reader scale_reader(
        parsed.scale_payload,
        bit_bytes(parsed.scale_bits),
        parsed.scale_bits
    );
    arithmetic_decoder scale_decoder{};
    if (
        parsed.scale_bits == 0U
        || !scale_decoder.initialize(&scale_reader, 63U)
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    for (
        std::size_t index = 0U;
        index < requirements.scale_elements;
        ++index
    ) {
        std::uint16_t symbol = 0U;
        if (!scale_decoder.decode(&symbol)) {
            return RESONITH_STATUS_TRUNCATED;
        }
        const std::int64_t delta =
            static_cast<std::int64_t>(symbol) - 31;
        const std::size_t within_channel =
            index % (
                static_cast<std::size_t>(parsed.frame_count)
                * parsed.band_count
            );
        const std::size_t frame = within_channel / parsed.band_count;
        const std::int64_t predictor = frame == 0U
            ? 0
            : workspace.scales[index - parsed.band_count];
        const std::int64_t scale = predictor + delta;
        if (scale < 0 || scale > 31) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        workspace.scales[index] = static_cast<std::uint8_t>(scale);
    }

    bit_reader count_reader(
        parsed.count_payload,
        bit_bytes(parsed.count_bits),
        parsed.count_bits
    );
    if (!count_reader.valid_padding()) {
        return RESONITH_STATUS_MALFORMED;
    }
    std::size_t coefficient_total = 0U;
    for (
        std::size_t index = 0U;
        index < requirements.count_elements;
        ++index
    ) {
        std::uint64_t unsigned_value = 0U;
        std::int64_t delta = 0;
        if (
            !decode_unsigned(
                &count_reader,
                parsed.count_entropy,
                parsed.count_parameter,
                &unsigned_value
            )
            || !zigzag_decode(unsigned_value, &delta)
        ) {
            return RESONITH_STATUS_TRUNCATED;
        }
        const std::size_t frame = index % parsed.frame_count;
        const std::int64_t predictor = frame == 0U
            ? 0
            : workspace.counts[index - 1U];
        const std::int64_t count = predictor + delta;
        if (count < 0 || count > requirements.half_window) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        workspace.counts[index] = static_cast<std::uint16_t>(count);
        if (
            static_cast<std::size_t>(count)
            > requirements.position_elements - coefficient_total
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        coefficient_total += static_cast<std::size_t>(count);
    }
    if (
        count_reader.position() != parsed.count_bits
        || coefficient_total != requirements.position_elements
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::uint16_t gap_alphabet = parsed.gap_threshold
        < requirements.half_window
        ? static_cast<std::uint16_t>(parsed.gap_threshold + 1U)
        : requirements.half_window;
    bit_reader gap_reader(
        parsed.gap_payload,
        bit_bytes(parsed.gap_bits),
        parsed.gap_bits
    );
    arithmetic_decoder gap_decoder{};
    if (
        requirements.position_elements != 0U
        && (
            parsed.gap_bits == 0U
            || !gap_decoder.initialize(&gap_reader, gap_alphabet)
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    bit_reader raw_gap_reader(
        parsed.raw_gap_payload,
        bit_bytes(parsed.raw_gap_bits),
        parsed.raw_gap_bits
    );
    if (!raw_gap_reader.valid_padding()) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t raw_width = position_width(
        requirements.half_window
    );
    std::size_t position_cursor = 0U;
    for (
        std::size_t frame = 0U;
        frame < requirements.count_elements;
        ++frame
    ) {
        std::uint64_t previous = 0U;
        for (
            std::size_t within_frame = 0U;
            within_frame < workspace.counts[frame];
            ++within_frame
        ) {
            std::uint16_t category = 0U;
            if (!gap_decoder.decode(&category)) {
                return RESONITH_STATUS_TRUNCATED;
            }
            std::uint64_t gap = category;
            if (
                parsed.gap_threshold < requirements.half_window
                && category == parsed.gap_threshold
            ) {
                if (!raw_gap_reader.read_bits(raw_width, &gap)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
                if (
                    gap < parsed.gap_threshold
                    || gap >= requirements.half_window
                ) {
                    return RESONITH_STATUS_PROFILE_BOUND;
                }
            }
            const std::uint64_t position = within_frame == 0U
                ? gap
                : previous + 1U + gap;
            if (
                position >= requirements.half_window
                || position_cursor >= requirements.position_elements
            ) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            workspace.positions[position_cursor] =
                static_cast<std::uint16_t>(position);
            previous = position;
            ++position_cursor;
        }
    }
    if (
        position_cursor != requirements.position_elements
        || raw_gap_reader.position() != parsed.raw_gap_bits
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    bit_reader value_reader(
        parsed.value_payload,
        bit_bytes(parsed.value_bits),
        parsed.value_bits
    );
    if (parsed.bounded_values) {
        if (!value_reader.valid_padding()) {
            return RESONITH_STATUS_MALFORMED;
        }
        for (
            std::size_t index = 0U;
            index < requirements.coefficient_elements;
            ++index
        ) {
            std::uint64_t unsigned_value = 0U;
            std::int64_t value = 0;
            if (
                !decode_unsigned(
                    &value_reader,
                    parsed.value_entropy,
                    parsed.value_parameter,
                    &unsigned_value
                )
                || !zigzag_decode(unsigned_value, &value)
            ) {
                return RESONITH_STATUS_TRUNCATED;
            }
            if (value < -128 || value > 127 || value == 0) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            workspace.coefficients[index] =
                static_cast<std::int8_t>(value);
        }
        return value_reader.position() == parsed.value_bits
            ? RESONITH_STATUS_OK
            : RESONITH_STATUS_MALFORMED;
    }

    arithmetic_decoder value_decoder{};
    if (
        requirements.coefficient_elements != 0U
        && (
            parsed.value_bits == 0U
            || !value_decoder.initialize(&value_reader, 256U)
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    for (
        std::size_t index = 0U;
        index < requirements.coefficient_elements;
        ++index
    ) {
        std::uint16_t symbol = 0U;
        if (!value_decoder.decode(&symbol)) {
            return RESONITH_STATUS_TRUNCATED;
        }
        const std::int16_t value =
            static_cast<std::int16_t>(symbol) - 128;
        if (value == 0) {
            return RESONITH_STATUS_MALFORMED;
        }
        workspace.coefficients[index] = static_cast<std::int8_t>(value);
    }
    return RESONITH_STATUS_OK;
}

}  // namespace

namespace resonith::internal {

resonith_status lapped_finite_compact_fields_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_lapped_requirements& shape,
    const resonith_lapped_workspace& workspace,
    resonith_lapped_requirements* requirements
) noexcept {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    parsed_finite parsed{};
    resonith_lapped_finite_requirements finite_requirements{};
    const resonith_status status = parse_compact_finite(
        data,
        data_size,
        shape,
        &parsed,
        &finite_requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (!valid_workspace(finite_requirements, workspace)) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    const resonith_status decode_status = decode_finite(
        parsed,
        finite_requirements,
        workspace
    );
    if (decode_status == RESONITH_STATUS_OK) {
        *requirements = shape;
    }
    return decode_status;
}

resonith_status lapped_rice_value_compact_fields_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_lapped_requirements& shape,
    const resonith_lapped_workspace& workspace,
    resonith_lapped_requirements* requirements
) noexcept {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    parsed_finite parsed{};
    resonith_lapped_finite_requirements finite_requirements{};
    const resonith_status status = parse_compact_rice_value(
        data,
        data_size,
        shape,
        &parsed,
        &finite_requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (!valid_workspace(finite_requirements, workspace)) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    const resonith_status decode_status = decode_finite(
        parsed,
        finite_requirements,
        workspace
    );
    if (decode_status == RESONITH_STATUS_OK) {
        *requirements = shape;
    }
    return decode_status;
}

}  // namespace resonith::internal

extern "C" resonith_status resonith_lapped_finite_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint16_t half_window,
    resonith_lapped_finite_requirements* requirements
) {
    if (data == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    parsed_finite parsed{};
    return parse_finite(
        data,
        data_size,
        half_window,
        &parsed,
        requirements
    );
}

extern "C" resonith_status resonith_lapped_finite_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint16_t half_window,
    const resonith_lapped_workspace* workspace
) {
    if (data == nullptr || workspace == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    parsed_finite parsed{};
    resonith_lapped_finite_requirements requirements{};
    const resonith_status status = parse_finite(
        data,
        data_size,
        half_window,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (!valid_workspace(requirements, *workspace)) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    return decode_finite(parsed, requirements, *workspace);
}

extern "C" resonith_status resonith_lapped_adaptive_encode(
    const std::uint16_t* symbols,
    std::size_t symbol_count,
    std::uint16_t alphabet_size,
    std::uint8_t* output,
    std::size_t output_capacity,
    std::size_t* output_size,
    std::uint32_t* bit_count
) {
    return encode_adaptive(
        symbols,
        symbol_count,
        alphabet_size,
        output,
        output_capacity,
        output_size,
        bit_count
    );
}

extern "C" resonith_status resonith_lapped_int16_entropy_encode(
    const std::int16_t* values,
    std::size_t value_count,
    std::uint8_t* entropy_mode,
    std::uint8_t* entropy_parameter,
    std::uint8_t* output,
    std::size_t output_capacity,
    std::size_t* output_size,
    std::uint32_t* bit_count
) {
    return encode_int16_entropy(
        values,
        value_count,
        entropy_mode,
        entropy_parameter,
        output,
        output_capacity,
        output_size,
        bit_count
    );
}
