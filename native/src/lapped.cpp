#include "resonith/lapped.h"

#include "resonith/container.h"
#include "resonith/stream.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::uint16_t kSchemaVersion = 1U;
constexpr std::size_t kLappedHeaderBytes = 28U;
constexpr std::size_t kSparseHeaderBytes = 34U;
constexpr std::size_t kVariableSparseHeaderBytes = 42U;
constexpr std::uint8_t kLappedVersion = 1U;
constexpr std::uint8_t kSparseVersion = 1U;
constexpr std::uint8_t kFixedLappedFlags = 3U;
constexpr std::uint8_t kVariableLappedFlags = 7U;
constexpr std::uint8_t kEntropyRice = 0U;
constexpr std::uint8_t kEntropyPacked = 1U;
constexpr std::uint8_t kMaximumRiceParameter = 20U;
constexpr std::uint32_t kRiceEscapeQuotient = 31U;
constexpr std::uint16_t kMaximumChannels = 8U;
constexpr std::uint16_t kMaximumBands = 64U;
constexpr std::uint16_t kMaximumHalfWindow = 1024U;
constexpr std::uint32_t kMaximumSymbols = 64U << 20U;
constexpr std::size_t kMaximumPayloadBytes = 512U << 20U;
constexpr std::int64_t kCosineMagnitudeQ14 = 1LL << 14U;
constexpr std::int64_t kWindowMagnitudeQ15 = 1LL << 15U;
constexpr std::uint32_t kRomHalfWindow = 1024U;
constexpr std::uint32_t kRomCycle = 8U * kRomHalfWindow;

#include "lapped_rom.inc"

struct parsed_lapped {
    resonith_container_view container{};
    resonith_container_section config{};
    resonith_container_section lapped{};
    resonith_stream_config stream_config{};
    const std::uint8_t* sparse = nullptr;
    std::size_t sparse_size = 0U;
    std::uint32_t sample_rate = 0U;
    std::uint32_t sample_count = 0U;
    std::uint32_t transform_frames = 0U;
    std::uint16_t channels = 0U;
    std::uint16_t half_window = 0U;
    std::uint16_t band_count = 0U;
    std::uint16_t coefficients_per_frame = 0U;
    bool variable_density = false;
    std::uint8_t scale_entropy = 0U;
    std::uint8_t scale_parameter = 0U;
    std::uint8_t count_entropy = 0U;
    std::uint8_t count_parameter = 0U;
    std::uint8_t position_parameter = 0U;
    std::uint8_t value_entropy = 0U;
    std::uint8_t value_parameter = 0U;
    std::uint32_t scale_bits = 0U;
    std::uint32_t count_bits = 0U;
    std::uint32_t position_bits = 0U;
    std::uint32_t value_bits = 0U;
    const std::uint8_t* scale_payload = nullptr;
    const std::uint8_t* count_payload = nullptr;
    const std::uint8_t* position_payload = nullptr;
    const std::uint8_t* value_payload = nullptr;
};

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

bool type_is(
    const std::uint8_t actual[4],
    const char (&expected)[5]
) noexcept {
    return std::memcmp(actual, expected, 4U) == 0;
}

bool is_power_of_two(std::uint16_t value) noexcept {
    return value != 0U && (value & static_cast<std::uint16_t>(value - 1U)) == 0U;
}

std::uint32_t log2_power_of_two(std::uint16_t value) noexcept {
    std::uint32_t result = 0U;
    while (value > 1U) {
        value = static_cast<std::uint16_t>(value >> 1U);
        ++result;
    }
    return result;
}

bool checked_product(
    std::size_t left,
    std::size_t right,
    std::size_t* output
) noexcept {
    if (
        output == nullptr
        || (right != 0U && left > std::numeric_limits<std::size_t>::max() / right)
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

resonith_status parse_sparse_fields(
    parsed_lapped* parsed,
    resonith_lapped_requirements* requirements
) noexcept {
    if (parsed == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    const std::size_t sparse_header_bytes = parsed->variable_density
        ? kVariableSparseHeaderBytes
        : kSparseHeaderBytes;
    if (
        parsed->sparse == nullptr
        || parsed->sparse_size < sparse_header_bytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }

    const std::uint8_t* sparse = parsed->sparse;
    const char* expected_sparse_magic = parsed->variable_density
        ? "LSE2"
        : "LSE1";
    if (std::memcmp(sparse, expected_sparse_magic, 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (sparse[4] != kSparseVersion) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    parsed->scale_entropy = sparse[6U];
    parsed->scale_parameter = sparse[7U];
    std::uint32_t declared_sparse_elements = 0U;
    if (parsed->variable_density) {
        parsed->count_entropy = sparse[8U];
        parsed->count_parameter = sparse[9U];
        parsed->position_parameter = sparse[10U];
        parsed->value_entropy = sparse[11U];
        parsed->value_parameter = sparse[12U];
        declared_sparse_elements = read_u32(sparse + 22U);
        parsed->scale_bits = read_u32(sparse + 26U);
        parsed->count_bits = read_u32(sparse + 30U);
        parsed->position_bits = read_u32(sparse + 34U);
        parsed->value_bits = read_u32(sparse + 38U);
        if (
            sparse[5U] != 0U
            || sparse[13U] != 0U
            || read_u32(sparse + 14U) != parsed->transform_frames
            || read_u16(sparse + 18U) != parsed->channels
            || read_u16(sparse + 20U) != parsed->band_count
            || !valid_entropy(
                parsed->count_entropy,
                parsed->count_parameter
            )
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
    } else {
        parsed->position_parameter = sparse[8U];
        parsed->value_entropy = sparse[9U];
        parsed->value_parameter = sparse[10U];
        parsed->coefficients_per_frame = read_u16(sparse + 20U);
        parsed->scale_bits = read_u32(sparse + 22U);
        parsed->position_bits = read_u32(sparse + 26U);
        parsed->value_bits = read_u32(sparse + 30U);
        if (
            sparse[5U] != 0U
            || sparse[11U] != 0U
            || read_u32(sparse + 12U) != parsed->transform_frames
            || read_u16(sparse + 16U) != parsed->channels
            || read_u16(sparse + 18U) != parsed->band_count
            || parsed->coefficients_per_frame == 0U
            || parsed->coefficients_per_frame > parsed->half_window
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
    }
    if (
        !valid_entropy(parsed->scale_entropy, parsed->scale_parameter)
        || !valid_entropy(parsed->value_entropy, parsed->value_parameter)
        || parsed->position_parameter
            > static_cast<std::uint8_t>(
                log2_power_of_two(parsed->half_window)
            )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::size_t scale_bytes = bit_bytes(parsed->scale_bits);
    const std::size_t count_bytes = bit_bytes(parsed->count_bits);
    const std::size_t position_bytes = bit_bytes(parsed->position_bits);
    const std::size_t value_bytes = bit_bytes(parsed->value_bits);
    if (
        scale_bytes > parsed->sparse_size - sparse_header_bytes
        || count_bytes
            > parsed->sparse_size - sparse_header_bytes - scale_bytes
        || position_bytes
            > parsed->sparse_size
                - sparse_header_bytes
                - scale_bytes
                - count_bytes
        || value_bytes
            != parsed->sparse_size
                - sparse_header_bytes
                - scale_bytes
                - count_bytes
                - position_bytes
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    parsed->scale_payload = sparse + sparse_header_bytes;
    parsed->count_payload = parsed->scale_payload + scale_bytes;
    parsed->position_payload = parsed->count_payload + count_bytes;
    parsed->value_payload = parsed->position_payload + position_bytes;

    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t sparse_elements = 0U;
    std::size_t output_elements = 0U;
    if (
        !checked_product(
            parsed->channels,
            parsed->transform_frames,
            &channel_frames
        )
        || !checked_product(
            channel_frames,
            parsed->band_count,
            &scale_elements
        )
        || !checked_product(
            parsed->sample_count,
            parsed->channels,
            &output_elements
        )
        || scale_elements > kMaximumSymbols
        || parsed->sample_count
            > std::numeric_limits<std::size_t>::max()
                - 2U * parsed->half_window
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (parsed->variable_density) {
        sparse_elements = declared_sparse_elements;
        std::size_t maximum_sparse_elements = 0U;
        if (
            !checked_product(
                channel_frames,
                parsed->half_window,
                &maximum_sparse_elements
            )
            || sparse_elements > maximum_sparse_elements
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
    } else if (
        !checked_product(
            channel_frames,
            parsed->coefficients_per_frame,
            &sparse_elements
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (sparse_elements > kMaximumSymbols) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    requirements->sample_rate = parsed->sample_rate;
    requirements->frame_count = parsed->sample_count;
    requirements->transform_frame_count = parsed->transform_frames;
    requirements->half_window = parsed->half_window;
    requirements->band_count = parsed->band_count;
    requirements->coefficients_per_frame =
        parsed->coefficients_per_frame;
    requirements->output_channels = parsed->channels;
    requirements->scale_elements = scale_elements;
    requirements->count_elements = parsed->variable_density
        ? channel_frames
        : 0U;
    requirements->position_elements = sparse_elements;
    requirements->coefficient_elements = sparse_elements;
    requirements->overlap_elements =
        static_cast<std::size_t>(parsed->sample_count)
        + 2U * parsed->half_window;
    requirements->output_elements = output_elements;
    return RESONITH_STATUS_OK;
}

resonith_status parse_lapped(
    const std::uint8_t* data,
    std::size_t data_size,
    parsed_lapped* parsed,
    resonith_lapped_requirements* requirements
) noexcept {
    if (parsed == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *parsed = {};
    *requirements = {};
    resonith_status status = resonith_container_open(
        data,
        data_size,
        &parsed->container
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        parsed->container.profile != 0U
        || parsed->container.level != 5U
    ) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    bool found_config = false;
    bool found_lapped = false;
    for (
        std::uint32_t index = 0U;
        index < parsed->container.section_count;
        ++index
    ) {
        resonith_container_section section{};
        status = resonith_container_get_section(
            &parsed->container,
            index,
            &section
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        const bool is_config = type_is(section.type, "CONF");
        const bool is_lapped = type_is(section.type, "LPF1");
        if (!is_config && !is_lapped) {
            if (
                (section.flags & RESONITH_RSC1_SECTION_CRITICAL) != 0U
            ) {
                return RESONITH_STATUS_UNSUPPORTED_FEATURE;
            }
            continue;
        }
        if (
            section.schema_version != kSchemaVersion
            || (section.flags & RESONITH_RSC1_SECTION_CRITICAL) == 0U
            || section.instance_id != 0U
            || section.start_tick != 0U
        ) {
            return section.schema_version != kSchemaVersion
                ? RESONITH_STATUS_UNSUPPORTED_FEATURE
                : RESONITH_STATUS_MALFORMED;
        }
        status = resonith_container_verify_section(&section);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (is_config) {
            if (found_config) {
                return RESONITH_STATUS_MALFORMED;
            }
            parsed->config = section;
            found_config = true;
        } else {
            if (found_lapped) {
                return RESONITH_STATUS_MALFORMED;
            }
            parsed->lapped = section;
            found_lapped = true;
        }
    }
    if (!found_config || !found_lapped) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    status = resonith_stream_config_parse(
        parsed->config.payload,
        parsed->config.payload_size,
        &parsed->stream_config
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        parsed->stream_config.innovation_step != 1U
        || parsed->lapped.payload_size < kLappedHeaderBytes
    ) {
        return parsed->lapped.payload_size < kLappedHeaderBytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }

    const std::uint8_t* lapped = parsed->lapped.payload;
    if (std::memcmp(lapped, "LPI1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (lapped[4] != kLappedVersion) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (
        lapped[5] != kFixedLappedFlags
        && lapped[5] != kVariableLappedFlags
    ) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    parsed->variable_density = lapped[5] == kVariableLappedFlags;
    parsed->channels = read_u16(lapped + 6U);
    parsed->sample_rate = read_u32(lapped + 8U);
    parsed->sample_count = read_u32(lapped + 12U);
    parsed->half_window = read_u16(lapped + 16U);
    parsed->band_count = read_u16(lapped + 18U);
    parsed->transform_frames = read_u32(lapped + 20U);
    const std::uint32_t sparse_bytes = read_u32(lapped + 24U);
    if (
        parsed->channels == 0U
        || parsed->channels > kMaximumChannels
        || parsed->half_window < 32U
        || parsed->half_window > kMaximumHalfWindow
        || !is_power_of_two(parsed->half_window)
        || kRomHalfWindow % parsed->half_window != 0U
        || parsed->band_count == 0U
        || parsed->band_count > kMaximumBands
        || parsed->sample_rate != parsed->container.timebase_hz
        || parsed->sample_count != parsed->stream_config.sample_count
        || parsed->channels != parsed->stream_config.output_channels
        || parsed->transform_frames
            != parsed->sample_count / parsed->half_window + 1U
        || sparse_bytes > kMaximumPayloadBytes
        || sparse_bytes != parsed->lapped.payload_size - kLappedHeaderBytes
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    parsed->sparse = lapped + kLappedHeaderBytes;
    parsed->sparse_size = sparse_bytes;
    return parse_sparse_fields(parsed, requirements);
}

resonith_status parse_selected_lapped(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint32_t sample_rate,
    std::uint32_t sample_count,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    parsed_lapped* parsed,
    resonith_lapped_requirements* requirements
) noexcept {
    if (
        data == nullptr
        || parsed == nullptr
        || requirements == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *parsed = {};
    *requirements = {};
    if (
        data_size < kVariableSparseHeaderBytes
        || data_size > kMaximumPayloadBytes
    ) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (
        sample_rate == 0U
        || sample_count == 0U
        || channels == 0U
        || channels > kMaximumChannels
        || half_window < 32U
        || half_window > kMaximumHalfWindow
        || !is_power_of_two(half_window)
        || kRomHalfWindow % half_window != 0U
        || band_count == 0U
        || band_count > kMaximumBands
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    parsed->sparse = data;
    parsed->sparse_size = data_size;
    parsed->sample_rate = sample_rate;
    parsed->sample_count = sample_count;
    parsed->transform_frames = sample_count / half_window + 1U;
    parsed->channels = channels;
    parsed->half_window = half_window;
    parsed->band_count = band_count;
    parsed->variable_density = true;
    return parse_sparse_fields(parsed, requirements);
}

bool decode_unsigned(
    bit_reader* reader,
    std::uint8_t mode,
    std::uint8_t parameter,
    std::uint64_t* output
) noexcept {
    if (reader == nullptr || output == nullptr) {
        return false;
    }
    if (mode == kEntropyPacked) {
        return reader->read_bits(parameter, output);
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
        return reader->read_bits(64U, output);
    }
    std::uint64_t remainder = 0U;
    if (!reader->read_bits(parameter, &remainder)) {
        return false;
    }
    *output = (static_cast<std::uint64_t>(quotient) << parameter) | remainder;
    return true;
}

bool zigzag_decode(std::uint64_t value, std::int64_t* output) noexcept {
    if (output == nullptr) {
        return false;
    }
    if ((value & 1U) == 0U) {
        const std::uint64_t magnitude = value >> 1U;
        if (
            magnitude
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::int64_t>::max()
            )
        ) {
            return false;
        }
        *output = static_cast<std::int64_t>(magnitude);
    } else {
        const std::uint64_t magnitude = value >> 1U;
        if (
            magnitude
            > static_cast<std::uint64_t>(
                std::numeric_limits<std::int64_t>::max()
            )
        ) {
            return false;
        }
        *output = -static_cast<std::int64_t>(magnitude) - 1;
    }
    return true;
}

resonith_status decode_fields(
    const parsed_lapped& parsed,
    const resonith_lapped_requirements& requirements,
    const resonith_lapped_workspace& workspace
) noexcept {
    bit_reader scale_reader(
        parsed.scale_payload,
        bit_bytes(parsed.scale_bits),
        parsed.scale_bits
    );
    if (!scale_reader.valid_padding()) {
        return RESONITH_STATUS_MALFORMED;
    }
    for (
        std::size_t index = 0U;
        index < requirements.scale_elements;
        ++index
    ) {
        std::uint64_t unsigned_value = 0U;
        std::int64_t delta = 0;
        if (
            !decode_unsigned(
                &scale_reader,
                parsed.scale_entropy,
                parsed.scale_parameter,
                &unsigned_value
            )
            || !zigzag_decode(unsigned_value, &delta)
        ) {
            return RESONITH_STATUS_TRUNCATED;
        }
        const std::size_t within_channel =
            index % (
                static_cast<std::size_t>(parsed.transform_frames)
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
    if (scale_reader.position() != parsed.scale_bits) {
        return RESONITH_STATUS_MALFORMED;
    }

    if (parsed.variable_density) {
        bit_reader count_reader(
            parsed.count_payload,
            bit_bytes(parsed.count_bits),
            parsed.count_bits
        );
        if (!count_reader.valid_padding()) {
            return RESONITH_STATUS_MALFORMED;
        }
        std::size_t total_coefficients = 0U;
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
            const std::size_t frame =
                index % parsed.transform_frames;
            const std::int64_t predictor = frame == 0U
                ? 0
                : workspace.counts[index - 1U];
            const std::int64_t count = predictor + delta;
            if (count < 0 || count > parsed.half_window) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            workspace.counts[index] = static_cast<std::uint16_t>(count);
            if (
                static_cast<std::size_t>(count)
                > requirements.position_elements - total_coefficients
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            total_coefficients += static_cast<std::size_t>(count);
        }
        if (
            count_reader.position() != parsed.count_bits
            || total_coefficients != requirements.position_elements
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
    }

    const std::uint32_t position_width = static_cast<std::uint32_t>(
        log2_power_of_two(parsed.half_window)
    );
    bit_reader position_reader(
        parsed.position_payload,
        bit_bytes(parsed.position_bits),
        parsed.position_bits
    );
    if (!position_reader.valid_padding()) {
        return RESONITH_STATUS_MALFORMED;
    }
    std::size_t position_cursor = 0U;
    const std::size_t channel_frames =
        static_cast<std::size_t>(parsed.channels) * parsed.transform_frames;
    for (std::size_t frame = 0U; frame < channel_frames; ++frame) {
        const std::size_t frame_coefficients = parsed.variable_density
            ? workspace.counts[frame]
            : parsed.coefficients_per_frame;
        std::uint64_t previous = 0U;
        for (
            std::size_t within_frame = 0U;
            within_frame < frame_coefficients;
            ++within_frame
        ) {
            std::uint32_t quotient = 0U;
            while (true) {
                std::uint32_t bit = 0U;
                if (!position_reader.read_bit(&bit)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
                if (bit == 0U) {
                    break;
                }
                ++quotient;
                if (quotient > kRiceEscapeQuotient) {
                    return RESONITH_STATUS_MALFORMED;
                }
            }
            std::uint64_t gap = 0U;
            if (quotient == kRiceEscapeQuotient) {
                if (!position_reader.read_bits(position_width, &gap)) {
                    return RESONITH_STATUS_TRUNCATED;
                }
            } else {
                std::uint64_t remainder = 0U;
                if (
                    !position_reader.read_bits(
                        parsed.position_parameter,
                        &remainder
                    )
                ) {
                    return RESONITH_STATUS_TRUNCATED;
                }
                gap = (
                    static_cast<std::uint64_t>(quotient)
                    << parsed.position_parameter
                ) | remainder;
            }
            const std::uint64_t position = within_frame == 0U
                ? gap
                : previous + 1U + gap;
            if (
                position >= parsed.half_window
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
    if (position_cursor != requirements.position_elements) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (position_reader.position() != parsed.position_bits) {
        return RESONITH_STATUS_MALFORMED;
    }

    bit_reader value_reader(
        parsed.value_payload,
        bit_bytes(parsed.value_bits),
        parsed.value_bits
    );
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
        if (value < -128 || value > 127) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        workspace.coefficients[index] = static_cast<std::int8_t>(value);
    }
    return value_reader.position() == parsed.value_bits
        ? RESONITH_STATUS_OK
        : RESONITH_STATUS_MALFORMED;
}

bool build_band_edges(
    std::uint16_t half_window,
    std::uint16_t band_count,
    std::array<std::uint16_t, kMaximumBands + 1U>* edges
) noexcept {
    if (edges == nullptr) {
        return false;
    }
    const std::uint64_t denominator =
        static_cast<std::uint64_t>(band_count) * band_count;
    (*edges)[0] = 0U;
    for (std::uint16_t index = 1U; index < band_count; ++index) {
        const std::uint64_t numerator =
            static_cast<std::uint64_t>(index)
            * index
            * half_window;
        std::uint64_t quotient = numerator / denominator;
        const std::uint64_t remainder = numerator % denominator;
        if (
            2U * remainder > denominator
            || (
                2U * remainder == denominator
                && (quotient & 1U) != 0U
            )
        ) {
            ++quotient;
        }
        if (
            quotient <= (*edges)[index - 1U]
            || quotient >= half_window
        ) {
            return false;
        }
        (*edges)[index] = static_cast<std::uint16_t>(quotient);
    }
    (*edges)[band_count] = half_window;
    return true;
}

std::int32_t quarter_lookup(
    const std::array<std::int32_t, 2049>& table,
    std::int64_t raw_index
) noexcept {
    std::int64_t index = raw_index % kRomCycle;
    if (index < 0) {
        index += kRomCycle;
    }
    if (index <= 2LL * kRomHalfWindow) {
        return table[static_cast<std::size_t>(index)];
    }
    if (index <= 4LL * kRomHalfWindow) {
        return -table[
            static_cast<std::size_t>(4LL * kRomHalfWindow - index)
        ];
    }
    if (index <= 6LL * kRomHalfWindow) {
        return -table[
            static_cast<std::size_t>(index - 4LL * kRomHalfWindow)
        ];
    }
    return table[
        static_cast<std::size_t>(8LL * kRomHalfWindow - index)
    ];
}

std::int64_t round_shift_signed(
    std::int64_t value,
    std::uint32_t shift
) noexcept {
    const std::int64_t rounding = 1LL << (shift - 1U);
    return value >= 0
        ? (value + rounding) >> shift
        : -(((-value) + rounding) >> shift);
}

resonith_status validate_synthesis_bounds(
    const parsed_lapped& parsed,
    const resonith_lapped_workspace& workspace
) noexcept {
    const std::uint64_t maximum_sum = static_cast<std::uint64_t>(
        std::numeric_limits<std::int64_t>::max()
        / (kCosineMagnitudeQ14 * kWindowMagnitudeQ15 * 2)
    );
    const std::size_t frame_count = parsed.transform_frames;
    std::array<std::uint16_t, kMaximumBands + 1U> edges{};
    if (!build_band_edges(
            parsed.half_window,
            parsed.band_count,
            &edges
        )) {
        return RESONITH_STATUS_MALFORMED;
    }
    std::size_t sparse_cursor = 0U;
    for (std::uint16_t channel = 0U; channel < parsed.channels; ++channel) {
        for (std::uint32_t frame = 0U; frame < frame_count; ++frame) {
            const std::size_t count_index =
                static_cast<std::size_t>(channel) * frame_count + frame;
            const std::size_t coefficient_count = parsed.variable_density
                ? workspace.counts[count_index]
                : parsed.coefficients_per_frame;
            const std::size_t sparse_base = parsed.variable_density
                ? sparse_cursor
                : count_index * coefficient_count;
            const std::size_t scale_base = (
                static_cast<std::size_t>(channel) * frame_count + frame
            ) * parsed.band_count;
            std::uint64_t coefficient_sum = 0U;
            std::uint16_t band = 0U;
            for (
                std::size_t index = 0U;
                index < coefficient_count;
                ++index
            ) {
                const std::uint16_t position =
                    workspace.positions[sparse_base + index];
                while (
                    band + 1U < parsed.band_count
                    && position >= edges[band + 1U]
                ) {
                    ++band;
                }
                const std::int64_t signed_value =
                    workspace.coefficients[sparse_base + index];
                const std::uint64_t magnitude = static_cast<std::uint64_t>(
                    signed_value < 0 ? -signed_value : signed_value
                ) << workspace.scales[scale_base + band];
                if (magnitude > maximum_sum - coefficient_sum) {
                    return RESONITH_STATUS_PROFILE_BOUND;
                }
                coefficient_sum += magnitude;
            }
            if (parsed.variable_density) {
                sparse_cursor += coefficient_count;
            }
        }
    }
    return RESONITH_STATUS_OK;
}

void render_channel(
    const parsed_lapped& parsed,
    const resonith_lapped_workspace& workspace,
    std::uint16_t channel,
    std::int16_t* output
) noexcept {
    std::fill(
        workspace.overlap_q29,
        workspace.overlap_q29
            + static_cast<std::ptrdiff_t>(
                parsed.sample_count + 2U * parsed.half_window
            ),
        0
    );
    std::array<std::uint16_t, kMaximumBands + 1U> edges{};
    static_cast<void>(
        build_band_edges(parsed.half_window, parsed.band_count, &edges)
    );
    const std::uint32_t rom_stride =
        kRomHalfWindow / parsed.half_window;
    const std::size_t transform_frames = parsed.transform_frames;
    std::size_t sparse_cursor = 0U;
    if (parsed.variable_density) {
        const std::size_t preceding_frames =
            static_cast<std::size_t>(channel) * transform_frames;
        for (std::size_t index = 0U; index < preceding_frames; ++index) {
            sparse_cursor += workspace.counts[index];
        }
    }
    for (std::uint32_t frame = 0U; frame < transform_frames; ++frame) {
        const std::size_t count_index =
            static_cast<std::size_t>(channel) * transform_frames + frame;
        const std::size_t coefficient_count = parsed.variable_density
            ? workspace.counts[count_index]
            : parsed.coefficients_per_frame;
        const std::size_t sparse_base = parsed.variable_density
            ? sparse_cursor
            : count_index * coefficient_count;
        const std::size_t scale_base = (
            static_cast<std::size_t>(channel) * transform_frames + frame
        ) * parsed.band_count;
        std::array<std::int64_t, kMaximumHalfWindow> values{};
        std::uint16_t band = 0U;
        for (
            std::size_t index = 0U;
            index < coefficient_count;
            ++index
        ) {
            const std::uint16_t position =
                workspace.positions[sparse_base + index];
            while (
                band + 1U < parsed.band_count
                && position >= edges[band + 1U]
            ) {
                ++band;
            }
            values[index] = (
                static_cast<std::int64_t>(
                    workspace.coefficients[sparse_base + index]
                )
                * (1LL << workspace.scales[scale_base + band])
            );
        }
        for (
            std::uint32_t sample = 0U;
            sample < 2U * parsed.half_window;
            ++sample
        ) {
            std::int64_t time_q14 = 0;
            for (
                std::size_t index = 0U;
                index < coefficient_count;
                ++index
            ) {
                const std::uint32_t position =
                    workspace.positions[sparse_base + index];
                const std::int64_t phase = static_cast<std::int64_t>(
                    (2U * position + 1U)
                    * (2U * sample + 1U + parsed.half_window)
                    * rom_stride
                );
                time_q14 += values[index]
                    * quarter_lookup(kCosineQuarterQ14, phase);
            }
            const std::int64_t window_phase =
                (
                    2LL * parsed.half_window
                    - (2LL * sample + 1LL)
                )
                * rom_stride;
            const std::int64_t weighted_q29 = time_q14
                * quarter_lookup(kCosineQuarterQ15, window_phase);
            workspace.overlap_q29[
                static_cast<std::size_t>(frame) * parsed.half_window + sample
            ] += weighted_q29;
        }
        if (parsed.variable_density) {
            sparse_cursor += coefficient_count;
        }
    }

    const std::uint32_t normalization_shift = static_cast<std::uint32_t>(
        28U + log2_power_of_two(parsed.half_window)
    );
    for (std::uint32_t frame = 0U; frame < parsed.sample_count; ++frame) {
        const std::int64_t rounded = round_shift_signed(
            workspace.overlap_q29[
                static_cast<std::size_t>(parsed.half_window) + frame
            ],
            normalization_shift
        );
        const std::int64_t clipped = std::clamp<std::int64_t>(
            rounded,
            -32768,
            32767
        );
        output[
            static_cast<std::size_t>(frame) * parsed.channels + channel
        ] = static_cast<std::int16_t>(clipped);
    }
}

resonith_status decode_parsed_lapped(
    const parsed_lapped& parsed,
    const resonith_lapped_requirements& requirements,
    const resonith_lapped_workspace& workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* frames_written
) noexcept {
    if (output_capacity < requirements.output_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (
        workspace.scales == nullptr
        || workspace.positions == nullptr
        || workspace.coefficients == nullptr
        || workspace.overlap_q29 == nullptr
        || workspace.scale_capacity < requirements.scale_elements
        || (
            requirements.count_elements != 0U
            && (
                workspace.counts == nullptr
                || workspace.count_capacity < requirements.count_elements
            )
        )
        || workspace.position_capacity < requirements.position_elements
        || workspace.coefficient_capacity
            < requirements.coefficient_elements
        || workspace.overlap_capacity < requirements.overlap_elements
    ) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    resonith_status status = decode_fields(
        parsed,
        requirements,
        workspace
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = validate_synthesis_bounds(parsed, workspace);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    for (
        std::uint16_t channel = 0U;
        channel < parsed.channels;
        ++channel
    ) {
        render_channel(parsed, workspace, channel, output);
    }
    *frames_written = parsed.sample_count;
    return RESONITH_STATUS_OK;
}

}  // namespace

extern "C" resonith_status resonith_lapped_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_lapped_requirements* requirements
) {
    if (data == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    parsed_lapped parsed{};
    return parse_lapped(data, data_size, &parsed, requirements);
}

extern "C" resonith_status resonith_lapped_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_lapped_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* frames_written
) {
    if (
        data == nullptr
        || workspace == nullptr
        || output == nullptr
        || frames_written == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_written = 0U;
    parsed_lapped parsed{};
    resonith_lapped_requirements requirements{};
    resonith_status status = parse_lapped(
        data,
        data_size,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    return decode_parsed_lapped(
        parsed,
        requirements,
        *workspace,
        output,
        output_capacity,
        frames_written
    );
}

extern "C" resonith_status resonith_lapped_selected_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint32_t sample_rate,
    std::uint32_t sample_count,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    resonith_lapped_requirements* requirements
) {
    if (data == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    parsed_lapped parsed{};
    return parse_selected_lapped(
        data,
        data_size,
        sample_rate,
        sample_count,
        channels,
        half_window,
        band_count,
        &parsed,
        requirements
    );
}

extern "C" resonith_status resonith_lapped_selected_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint32_t sample_rate,
    std::uint32_t sample_count,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    const resonith_lapped_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* frames_written
) {
    if (
        data == nullptr
        || workspace == nullptr
        || output == nullptr
        || frames_written == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_written = 0U;
    parsed_lapped parsed{};
    resonith_lapped_requirements requirements{};
    resonith_status status = parse_selected_lapped(
        data,
        data_size,
        sample_rate,
        sample_count,
        channels,
        half_window,
        band_count,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    return decode_parsed_lapped(
        parsed,
        requirements,
        *workspace,
        output,
        output_capacity,
        frames_written
    );
}

extern "C" resonith_status resonith_lapped_analyze_requirements(
    std::uint32_t sample_frame_count,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    resonith_lapped_analysis_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    if (
        sample_frame_count == 0U
        || channels == 0U
        || channels > kMaximumChannels
        || half_window < 32U
        || half_window > kMaximumHalfWindow
        || (half_window & (half_window - 1U)) != 0U
        || band_count == 0U
        || band_count > kMaximumBands
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::array<std::uint16_t, kMaximumBands + 1U> edges{};
    if (!build_band_edges(half_window, band_count, &edges)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint32_t transform_frames =
        sample_frame_count / half_window + 1U;
    std::size_t channel_frames = 0U;
    std::size_t scale_elements = 0U;
    std::size_t coefficient_elements = 0U;
    if (
        !checked_product(channels, transform_frames, &channel_frames)
        || !checked_product(
            channel_frames,
            band_count,
            &scale_elements
        )
        || !checked_product(
            channel_frames,
            half_window,
            &coefficient_elements
        )
        || scale_elements > kMaximumSymbols
        || coefficient_elements > kMaximumSymbols
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    requirements->transform_frame_count = transform_frames;
    requirements->scale_elements = scale_elements;
    requirements->coefficient_elements = coefficient_elements;
    requirements->score_elements = coefficient_elements;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_lapped_analyze_pcm16(
    const std::int16_t* interleaved_input,
    std::size_t input_elements,
    std::uint32_t sample_frame_count,
    std::uint16_t channels,
    std::uint16_t half_window,
    std::uint16_t band_count,
    std::uint8_t* scales,
    std::size_t scale_capacity,
    std::int16_t* quantized_coefficients,
    std::size_t coefficient_capacity,
    std::uint64_t* squared_scores,
    std::size_t score_capacity
) {
    if (
        interleaved_input == nullptr
        || scales == nullptr
        || quantized_coefficients == nullptr
        || squared_scores == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    resonith_lapped_analysis_requirements requirements{};
    resonith_status status = resonith_lapped_analyze_requirements(
        sample_frame_count,
        channels,
        half_window,
        band_count,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    std::size_t required_input = 0U;
    if (
        !checked_product(sample_frame_count, channels, &required_input)
        || input_elements < required_input
        || scale_capacity < requirements.scale_elements
        || coefficient_capacity < requirements.coefficient_elements
        || score_capacity < requirements.score_elements
    ) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    std::array<std::uint16_t, kMaximumBands + 1U> edges{};
    if (!build_band_edges(half_window, band_count, &edges)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint32_t rom_stride = kRomHalfWindow / half_window;
    std::array<std::int64_t, kMaximumHalfWindow> spectrum{};
    std::array<std::int64_t, 2U * kMaximumHalfWindow> windowed_q15{};
    for (std::uint16_t channel = 0U; channel < channels; ++channel) {
        for (
            std::uint32_t frame = 0U;
            frame < requirements.transform_frame_count;
            ++frame
        ) {
            for (
                std::uint32_t sample = 0U;
                sample < 2U * half_window;
                ++sample
            ) {
                const std::int64_t source_frame =
                    static_cast<std::int64_t>(frame) * half_window
                    + sample
                    - half_window;
                std::int64_t input = 0;
                if (
                    source_frame >= 0
                    && source_frame < sample_frame_count
                ) {
                    input = interleaved_input[
                        static_cast<std::size_t>(source_frame) * channels
                        + channel
                    ];
                }
                const std::int64_t window_phase =
                    (
                        2LL * half_window
                        - (2LL * sample + 1LL)
                    )
                    * rom_stride;
                windowed_q15[sample] = input
                    * quarter_lookup(kCosineQuarterQ15, window_phase);
            }
            for (
                std::uint16_t coefficient = 0U;
                coefficient < half_window;
                ++coefficient
            ) {
                std::int64_t accumulator_q29 = 0;
                for (
                    std::uint32_t sample = 0U;
                    sample < 2U * half_window;
                    ++sample
                ) {
                    const std::int64_t cosine_phase =
                        static_cast<std::int64_t>(
                            (2U * coefficient + 1U)
                            * (2U * sample + 1U + half_window)
                            * rom_stride
                        );
                    accumulator_q29 += windowed_q15[sample]
                        * quarter_lookup(
                            kCosineQuarterQ14,
                            cosine_phase
                        );
                }
                spectrum[coefficient] = round_shift_signed(
                    accumulator_q29,
                    29U
                );
            }
            const std::size_t frame_index =
                static_cast<std::size_t>(channel)
                    * requirements.transform_frame_count
                + frame;
            for (std::uint16_t band = 0U; band < band_count; ++band) {
                std::uint64_t maximum = 1U;
                for (
                    std::uint16_t coefficient = edges[band];
                    coefficient < edges[band + 1U];
                    ++coefficient
                ) {
                    const std::int64_t value = spectrum[coefficient];
                    const std::uint64_t magnitude =
                        static_cast<std::uint64_t>(
                            value < 0 ? -value : value
                        );
                    maximum = std::max(maximum, magnitude);
                }
                const std::uint64_t minimum_step =
                    std::max<std::uint64_t>(1U, (maximum + 126U) / 127U);
                std::uint8_t exponent = 0U;
                std::uint64_t power = 1U;
                while (power < minimum_step && exponent < 31U) {
                    power <<= 1U;
                    ++exponent;
                }
                scales[frame_index * band_count + band] = exponent;
                for (
                    std::uint16_t coefficient = edges[band];
                    coefficient < edges[band + 1U];
                    ++coefficient
                ) {
                    const std::int64_t value = spectrum[coefficient];
                    const std::int64_t quantized = exponent == 0U
                        ? value
                        : round_shift_signed(value, exponent);
                    const std::size_t output_index =
                        frame_index * half_window + coefficient;
                    quantized_coefficients[output_index] =
                        static_cast<std::int16_t>(
                            std::clamp<std::int64_t>(
                                quantized,
                                -127,
                                127
                            )
                        );
                    const std::uint64_t magnitude =
                        static_cast<std::uint64_t>(
                            value < 0 ? -value : value
                        );
                    squared_scores[output_index] = magnitude * magnitude;
                }
            }
        }
    }
    return RESONITH_STATUS_OK;
}
