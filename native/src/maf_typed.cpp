#include "resonith/maf_typed.h"

#include "integrity.h"
#include "resonith/maf.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::size_t kHeaderBytes = RESONITH_MAF_TYPED_HEADER_BYTES;
constexpr std::size_t kRecordHeaderBytes =
    RESONITH_MAF_TYPED_RECORD_HEADER_BYTES;
constexpr std::uint16_t kNoEmitter = 0xffffU;
constexpr std::uint16_t kNoReference = 0xffffU;

struct Header {
    std::uint32_t sample_rate;
    std::uint32_t total_frames;
    std::uint32_t render_quantum;
    std::uint64_t stream_seed;
    std::uint32_t declared_operations_per_frame;
    std::uint32_t payload_bytes;
    std::uint32_t persistent_bytes;
    std::uint32_t scratch_bytes;
    std::uint16_t output_channels;
    std::uint16_t emitter_count;
    std::uint16_t filter_count;
    std::uint16_t stochastic_count;
    std::uint16_t source_count;
    std::uint16_t transient_count;
    std::uint16_t mix_count;
    std::uint16_t basis_count;
    std::uint16_t basis_instance_count;
    std::uint16_t record_count;
};

struct Record {
    std::uint8_t type;
    const std::uint8_t* payload;
    std::uint32_t payload_size;
};

std::uint16_t read_u16(const std::uint8_t* data) noexcept {
    return static_cast<std::uint16_t>(
        data[0] | (static_cast<std::uint16_t>(data[1]) << 8U)
    );
}

std::int16_t read_i16(const std::uint8_t* data) noexcept {
    return static_cast<std::int16_t>(read_u16(data));
}

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(data[0])
        | (static_cast<std::uint32_t>(data[1]) << 8U)
        | (static_cast<std::uint32_t>(data[2]) << 16U)
        | (static_cast<std::uint32_t>(data[3]) << 24U);
}

std::int32_t read_i32(const std::uint8_t* data) noexcept {
    return static_cast<std::int32_t>(read_u32(data));
}

std::uint64_t read_u64(const std::uint8_t* data) noexcept {
    return read_u32(data)
        | (static_cast<std::uint64_t>(read_u32(data + 4U)) << 32U);
}

bool checked_add(
    std::uint64_t left,
    std::uint64_t right,
    std::uint64_t& result
) noexcept {
    if (right > std::numeric_limits<std::uint64_t>::max() - left) {
        return false;
    }
    result = left + right;
    return true;
}

bool checked_multiply(
    std::uint64_t left,
    std::uint64_t right,
    std::uint64_t& result
) noexcept {
    if (
        left != 0U
        && right > std::numeric_limits<std::uint64_t>::max() / left
    ) {
        return false;
    }
    result = left * right;
    return true;
}

resonith_status parse_header(
    const std::uint8_t* data,
    std::size_t data_size,
    Header& header
) noexcept {
    if (data == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (data_size < kHeaderBytes + 4U) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (std::memcmp(data, "MFT1", 4U) != 0) {
        return RESONITH_STATUS_BAD_MAGIC;
    }
    if (data[4] != 1U) {
        return RESONITH_STATUS_UNSUPPORTED_VERSION;
    }
    if (
        data[5] != 0U
        || read_u16(data + 6U) != kHeaderBytes
        || read_u32(data + 60U) != 0U
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    header.sample_rate = read_u32(data + 8U);
    header.total_frames = read_u32(data + 12U);
    header.render_quantum = read_u32(data + 16U);
    header.output_channels = read_u16(data + 20U);
    header.emitter_count = read_u16(data + 22U);
    header.filter_count = read_u16(data + 24U);
    header.stochastic_count = read_u16(data + 26U);
    header.source_count = read_u16(data + 28U);
    header.transient_count = read_u16(data + 30U);
    header.mix_count = read_u16(data + 32U);
    header.record_count = read_u16(data + 34U);
    header.stream_seed = read_u64(data + 36U);
    header.declared_operations_per_frame = read_u32(data + 44U);
    header.payload_bytes = read_u32(data + 48U);
    header.persistent_bytes = read_u32(data + 52U);
    header.scratch_bytes = read_u32(data + 56U);

    const std::uint64_t expected_size =
        kHeaderBytes + static_cast<std::uint64_t>(header.payload_bytes) + 4U;
    if (expected_size > data_size) {
        return RESONITH_STATUS_TRUNCATED;
    }
    if (expected_size != data_size) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t expected_crc = read_u32(
        data + kHeaderBytes + header.payload_bytes
    );
    if (
        resonith::internal::crc32(
            data,
            kHeaderBytes + header.payload_bytes
        ) != expected_crc
    ) {
        return RESONITH_STATUS_CHECKSUM_MISMATCH;
    }
    return RESONITH_STATUS_OK;
}

resonith_status next_record(
    const Header& header,
    const std::uint8_t* data,
    std::size_t& cursor,
    Record& record
) noexcept {
    const std::size_t payload_end = kHeaderBytes + header.payload_bytes;
    if (cursor > payload_end || payload_end - cursor < kRecordHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    const std::uint8_t* prefix = data + cursor;
    if (
        prefix[1] != 1U
        || read_u16(prefix + 2U) != 0U
    ) {
        return prefix[1] != 1U
            ? RESONITH_STATUS_UNSUPPORTED_VERSION
            : RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t payload_size = read_u32(prefix + 4U);
    cursor += kRecordHeaderBytes;
    if (payload_size > payload_end - cursor) {
        return RESONITH_STATUS_TRUNCATED;
    }
    record.type = prefix[0];
    record.payload = data + cursor;
    record.payload_size = payload_size;
    cursor += payload_size;
    return RESONITH_STATUS_OK;
}

bool valid_lifetime(
    std::uint32_t start,
    std::uint32_t end,
    std::uint32_t total_frames
) noexcept {
    return start < end && end <= total_frames;
}

std::int32_t combine_gain_q15(
    std::int32_t left,
    std::int32_t right
) noexcept {
    constexpr std::int64_t kDenominator = 1LL << 15U;
    constexpr std::int64_t kHalf = kDenominator / 2;
    const std::int64_t product =
        static_cast<std::int64_t>(left) * right;
    std::int64_t quotient = product / kDenominator;
    const std::int64_t remainder = product % kDenominator;
    if (remainder >= kHalf) {
        ++quotient;
    } else if (remainder <= -kHalf) {
        --quotient;
    }
    return static_cast<std::int32_t>(
        std::clamp<std::int64_t>(quotient, -32768, 32768)
    );
}

std::int32_t interpolate_gain_q15(
    std::int32_t start,
    std::int32_t end,
    std::uint32_t position,
    std::uint32_t count
) noexcept {
    if (count <= 1U || position == 0U) {
        return start;
    }
    if (position + 1U == count) {
        return end;
    }
    const std::int64_t denominator = count - 1U;
    const std::int64_t numerator =
        static_cast<std::int64_t>(end - start) * position;
    std::int64_t quotient = numerator / denominator;
    const std::int64_t remainder = numerator % denominator;
    const std::int64_t remainder_magnitude =
        remainder < 0 ? -remainder : remainder;
    if (2 * remainder_magnitude >= denominator) {
        quotient += numerator < 0 ? -1 : 1;
    }
    return static_cast<std::int32_t>(start + quotient);
}

resonith_status find_record(
    const Header& header,
    const std::uint8_t* data,
    std::uint8_t type,
    std::uint16_t id,
    Record& found
) noexcept {
    std::size_t cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        const resonith_status status = next_record(
            header,
            data,
            cursor,
            record
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (
            record.type == type
            && record.payload_size >= 2U
            && read_u16(record.payload) == id
        ) {
            found = record;
            return RESONITH_STATUS_OK;
        }
    }
    return RESONITH_STATUS_NOT_FOUND;
}

resonith_status find_basis(
    const Header& header,
    const std::uint8_t* data,
    std::uint16_t id,
    std::uint32_t& element_offset,
    Record& found
) noexcept {
    element_offset = 0U;
    std::size_t cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        const resonith_status status = next_record(
            header,
            data,
            cursor,
            record
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (record.type != RESONITH_MAF_TYPED_BASIS) {
            continue;
        }
        if (read_u16(record.payload) == id) {
            found = record;
            return RESONITH_STATUS_OK;
        }
        const std::uint32_t count = read_u16(record.payload + 2U);
        if (count > std::numeric_limits<std::uint32_t>::max() - element_offset) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        element_offset += count;
    }
    return RESONITH_STATUS_NOT_FOUND;
}

resonith_status calculate_requirements(
    Header& header,
    const std::uint8_t* data,
    resonith_maf_typed_requirements& requirements
) noexcept {
    resonith_maf_limits limits{};
    const resonith_status limit_status = resonith_maf_main_limits(&limits);
    if (limit_status != RESONITH_STATUS_OK) {
        return limit_status;
    }
    if (
        header.sample_rate < 8000U
        || header.sample_rate > limits.maximum_sample_rate
        || header.total_frames == 0U
        || header.render_quantum == 0U
        || header.render_quantum > RESONITH_MAF_MAIN_MAX_RENDER_FRAMES
        || header.output_channels == 0U
        || header.output_channels > RESONITH_MAF_MAIN_MAX_CHANNELS
        || header.emitter_count == 0U
        || header.emitter_count > RESONITH_MAF_MAIN_MAX_EMITTERS
        || header.filter_count > RESONITH_MAF_MAIN_MAX_FILTERS
        || header.stochastic_count
            > RESONITH_MAF_MAIN_MAX_STOCHASTIC_FIELDS
        || header.source_count > RESONITH_MAF_TYPED_MAX_SOURCE_LIFETIMES
        || header.transient_count > RESONITH_MAF_MAIN_MAX_TRANSIENTS
        || header.mix_count == 0U
        || header.mix_count > RESONITH_MAF_TYPED_MAX_SOURCE_LIFETIMES
        || header.declared_operations_per_frame == 0U
        || header.declared_operations_per_frame
            > limits.maximum_operations_per_frame
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint32_t fixed_records =
        static_cast<std::uint32_t>(header.filter_count)
        + header.stochastic_count
        + header.source_count
        + header.transient_count
        + header.mix_count;
    if (header.record_count < fixed_records) {
        return RESONITH_STATUS_MALFORMED;
    }
    header.basis_count = 0U;
    header.basis_instance_count = 0U;

    std::uint64_t coefficient_elements = 0U;
    std::uint64_t history_elements = 0U;
    std::uint64_t planar_elements = 0U;
    std::uint64_t working_elements = 0U;
    std::uint64_t mix_elements = 0U;
    std::uint64_t basis_elements = 0U;
    if (
        !checked_multiply(
            header.filter_count,
            RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            coefficient_elements
        )
        || !checked_multiply(
            header.emitter_count,
            RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            history_elements
        )
        || !checked_multiply(
            header.emitter_count,
            header.render_quantum,
            planar_elements
        )
        || !checked_multiply(2U, header.render_quantum, working_elements)
        || !checked_multiply(
            header.output_channels,
            header.emitter_count,
            mix_elements
        )
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::size_t record_cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        const resonith_status status = next_record(
            header,
            data,
            record_cursor,
            record
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (record.type == RESONITH_MAF_TYPED_BASIS) {
            if (record.payload_size < 4U) {
                return RESONITH_STATUS_TRUNCATED;
            }
            if (
                !checked_add(
                    basis_elements,
                    read_u16(record.payload + 2U),
                    basis_elements
                )
                || basis_elements > limits.maximum_basis_elements
            ) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            ++header.basis_count;
        } else if (record.type == RESONITH_MAF_TYPED_BASIS_INSTANCE) {
            ++header.basis_instance_count;
        }
    }
    if (
        header.basis_count > RESONITH_MAF_MAIN_MAX_BASES
        || header.basis_instance_count
            > RESONITH_MAF_TYPED_MAX_BASIS_INSTANCES
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        fixed_records + header.basis_count + header.basis_instance_count
        != header.record_count
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint64_t persistent_bytes =
        coefficient_elements * sizeof(std::int32_t)
        + (history_elements + basis_elements) * sizeof(std::int16_t);
    const std::uint64_t scratch_bytes =
        (planar_elements + working_elements + mix_elements)
        * sizeof(std::int16_t);
    if (
        persistent_bytes != header.persistent_bytes
        || scratch_bytes != header.scratch_bytes
        || persistent_bytes > limits.maximum_persistent_bytes
        || scratch_bytes > limits.maximum_scratch_bytes
        || coefficient_elements > std::numeric_limits<std::uint32_t>::max()
        || history_elements > std::numeric_limits<std::uint32_t>::max()
        || planar_elements > std::numeric_limits<std::uint32_t>::max()
        || working_elements > std::numeric_limits<std::uint32_t>::max()
        || mix_elements > std::numeric_limits<std::uint32_t>::max()
        || basis_elements > std::numeric_limits<std::uint32_t>::max()
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    requirements = {
        header.sample_rate,
        header.total_frames,
        header.render_quantum,
        static_cast<std::uint32_t>(coefficient_elements),
        static_cast<std::uint32_t>(history_elements),
        static_cast<std::uint32_t>(planar_elements),
        static_cast<std::uint32_t>(working_elements),
        static_cast<std::uint32_t>(mix_elements),
        static_cast<std::uint32_t>(basis_elements),
        header.declared_operations_per_frame,
        header.output_channels,
        header.emitter_count,
        header.filter_count,
        header.stochastic_count,
        header.source_count,
        header.transient_count,
        header.mix_count,
        header.basis_count,
        header.basis_instance_count,
    };
    return RESONITH_STATUS_OK;
}

resonith_status validate_records(
    const Header& header,
    const std::uint8_t* data
) noexcept {
    std::array<bool, RESONITH_MAF_MAIN_MAX_EMITTERS> stochastic_emitter{};
    std::array<std::uint32_t, RESONITH_MAF_MAIN_MAX_EMITTERS> last_source_end{};
    std::array<std::int16_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> reflection{};
    std::array<std::int32_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> coefficients{};
    std::uint8_t previous_type = 0U;
    std::uint16_t expected_id[8] = {};
    std::uint32_t mix_cursor = 0U;
    std::uint16_t previous_source_emitter = 0U;
    bool have_source = false;
    std::size_t cursor = kHeaderBytes;

    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        resonith_status status = next_record(header, data, cursor, record);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (
            record.type < RESONITH_MAF_TYPED_FILTER
            || record.type > RESONITH_MAF_TYPED_BASIS_INSTANCE
            || record.type < previous_type
            || record.payload_size < 2U
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        previous_type = record.type;
        const std::uint16_t record_id = read_u16(record.payload);
        if (record_id != expected_id[record.type]++) {
            return RESONITH_STATUS_MALFORMED;
        }

        if (record.type == RESONITH_MAF_TYPED_FILTER) {
            if (record.payload_size < 8U) {
                return RESONITH_STATUS_TRUNCATED;
            }
            const std::uint16_t order = read_u16(record.payload + 2U);
            if (
                order == 0U
                || order > RESONITH_MAF_MAIN_MAX_FILTER_ORDER
                || read_u32(record.payload + 4U) != 0U
                || record.payload_size != 8U + 2U * order
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            for (std::uint16_t item = 0U; item < order; ++item) {
                reflection[item] = read_i16(
                    record.payload + 8U + 2U * item
                );
            }
            resonith_maf_filter prepared{};
            status = resonith_maf_filter_prepare(
                reflection.data(),
                order,
                coefficients.data(),
                coefficients.size(),
                &prepared
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
        } else if (record.type == RESONITH_MAF_TYPED_STOCHASTIC) {
            if (record.payload_size != 20U) {
                return RESONITH_STATUS_MALFORMED;
            }
            const std::uint16_t emitter = read_u16(record.payload + 2U);
            const std::uint32_t start = read_u32(record.payload + 4U);
            const std::uint32_t end = read_u32(record.payload + 8U);
            const std::int32_t gain = read_i32(record.payload + 12U);
            if (
                !valid_lifetime(start, end, header.total_frames)
                || gain < -32768
                || gain > 32768
                || read_u32(record.payload + 16U) != 0U
                || (
                    emitter != kNoEmitter
                    && (
                        emitter >= header.emitter_count
                        || stochastic_emitter[emitter]
                    )
                )
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            if (emitter != kNoEmitter) {
                stochastic_emitter[emitter] = true;
            }
        } else if (record.type == RESONITH_MAF_TYPED_SOURCE_FILTER) {
            if (record.payload_size != 32U) {
                return RESONITH_STATUS_MALFORMED;
            }
            const std::uint16_t emitter = read_u16(record.payload + 2U);
            const std::uint16_t filter = read_u16(record.payload + 4U);
            const std::uint8_t excitation = record.payload[6U];
            const std::uint16_t reference = read_u16(record.payload + 8U);
            const std::uint32_t start = read_u32(record.payload + 12U);
            const std::uint32_t end = read_u32(record.payload + 16U);
            const std::int32_t gain = read_i32(record.payload + 20U);
            const std::uint32_t phase_increment =
                read_u32(record.payload + 28U);
            if (
                emitter >= header.emitter_count
                || stochastic_emitter[emitter]
                || record.payload[7U] != 0U
                || read_u16(record.payload + 10U) != 0U
                || !valid_lifetime(start, end, header.total_frames)
                || gain < -32768
                || gain > 32768
                || (
                    excitation != RESONITH_MAF_TYPED_EXCITATION_IMPULSE
                    && excitation
                        != RESONITH_MAF_TYPED_EXCITATION_STOCHASTIC
                    && excitation
                        != RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS
                )
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            if (
                excitation != RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS
                && filter >= header.filter_count
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            if (
                have_source
                && (
                    emitter < previous_source_emitter
                    || (
                        emitter == previous_source_emitter
                        && start < last_source_end[emitter]
                    )
                )
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            if (
                excitation == RESONITH_MAF_TYPED_EXCITATION_IMPULSE
                && (reference != kNoReference || phase_increment == 0U)
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            if (
                excitation == RESONITH_MAF_TYPED_EXCITATION_STOCHASTIC
            ) {
                Record field{};
                status = find_record(
                    header,
                    data,
                    RESONITH_MAF_TYPED_STOCHASTIC,
                    reference,
                    field
                );
                if (
                    status != RESONITH_STATUS_OK
                    || read_u16(field.payload + 2U) != kNoEmitter
                    || read_u32(field.payload + 4U) > start
                    || read_u32(field.payload + 8U) < end
                    || phase_increment != 0U
                ) {
                    return RESONITH_STATUS_MALFORMED;
                }
            }
            if (
                excitation == RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS
            ) {
                Record basis{};
                status = find_record(
                    header,
                    data,
                    RESONITH_MAF_TYPED_BASIS,
                    reference,
                    basis
                );
                if (
                    filter != kNoReference
                    || status != RESONITH_STATUS_OK
                    || phase_increment == 0U
                ) {
                    return RESONITH_STATUS_MALFORMED;
                }
            }
            last_source_end[emitter] = end;
            previous_source_emitter = emitter;
            have_source = true;
        } else if (record.type == RESONITH_MAF_TYPED_TRANSIENT) {
            if (record.payload_size < 16U) {
                return RESONITH_STATUS_TRUNCATED;
            }
            const std::uint16_t emitter = read_u16(record.payload + 2U);
            const std::uint32_t onset = read_u32(record.payload + 4U);
            const std::uint16_t sample_count =
                read_u16(record.payload + 8U);
            const std::int32_t gain = read_i32(record.payload + 12U);
            if (
                emitter >= header.emitter_count
                || sample_count == 0U
                || sample_count > RESONITH_MAF_MAIN_MAX_TRANSIENT_SAMPLES
                || read_u16(record.payload + 10U) != 0U
                || gain < -32768
                || gain > 32768
                || onset > header.total_frames
                || sample_count > header.total_frames - onset
                || record.payload_size != 16U + 2U * sample_count
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
        } else if (record.type == RESONITH_MAF_TYPED_MIX) {
            if (record.payload_size < 16U) {
                return RESONITH_STATUS_TRUNCATED;
            }
            const std::uint16_t source_count =
                read_u16(record.payload + 2U);
            const std::uint32_t start = read_u32(record.payload + 4U);
            const std::uint32_t end = read_u32(record.payload + 8U);
            const std::uint16_t channels =
                read_u16(record.payload + 12U);
            std::uint64_t matrix_elements = 0U;
            if (
                source_count != header.emitter_count
                || channels != header.output_channels
                || read_u16(record.payload + 14U) != 0U
                || start != mix_cursor
                || !valid_lifetime(start, end, header.total_frames)
                || !checked_multiply(
                    source_count,
                    channels,
                    matrix_elements
                )
                || record.payload_size
                    != 16U + 2U * source_count + 2U * matrix_elements
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            std::array<bool, RESONITH_MAF_MAIN_MAX_EMITTERS> seen{};
            for (std::uint16_t item = 0U; item < source_count; ++item) {
                const std::uint16_t emitter = read_u16(
                    record.payload + 16U + 2U * item
                );
                if (
                    emitter != item
                    || emitter >= header.emitter_count
                    || seen[emitter]
                ) {
                    return RESONITH_STATUS_MALFORMED;
                }
                seen[emitter] = true;
            }
            mix_cursor = end;
        } else if (record.type == RESONITH_MAF_TYPED_BASIS) {
            if (record.payload_size < 8U) {
                return RESONITH_STATUS_TRUNCATED;
            }
            const std::uint16_t sample_count =
                read_u16(record.payload + 2U);
            if (
                sample_count < 2U
                || sample_count > 8U * 2048U
                || read_u32(record.payload + 4U) != 0U
                || record.payload_size != 8U + 2U * sample_count
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
        } else {
            if (record.payload_size != 24U) {
                return RESONITH_STATUS_MALFORMED;
            }
            const std::uint16_t emitter = read_u16(record.payload + 2U);
            const std::uint16_t basis_id = read_u16(record.payload + 4U);
            const std::uint16_t flags = read_u16(record.payload + 6U);
            const std::uint32_t start = read_u32(record.payload + 8U);
            const std::int32_t gain = read_i32(record.payload + 12U);
            const std::uint16_t source_offset =
                read_u16(record.payload + 16U);
            const std::uint16_t sample_count =
                read_u16(record.payload + 18U);
            const std::int32_t end_gain =
                read_i32(record.payload + 20U);
            Record basis{};
            status = find_record(
                header,
                data,
                RESONITH_MAF_TYPED_BASIS,
                basis_id,
                basis
            );
            const std::uint16_t basis_samples =
                status == RESONITH_STATUS_OK
                    ? read_u16(basis.payload + 2U)
                    : 0U;
            const bool circular =
                (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_CIRCULAR) != 0U;
            const bool linear_gain =
                (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_LINEAR_GAIN) != 0U;
            const bool reverse =
                (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_REVERSE) != 0U;
            const bool crop_is_valid = circular
                ? (
                    source_offset < basis_samples
                    && sample_count <= basis_samples
                )
                : reverse
                    ? (
                        source_offset < basis_samples
                        && sample_count
                            <= static_cast<std::uint32_t>(source_offset) + 1U
                    )
                    : (
                        source_offset <= basis_samples
                        && sample_count <= basis_samples - source_offset
                    );
            if (
                emitter >= header.emitter_count
                || (flags & ~std::uint16_t{7U}) != 0U
                || gain < -32768
                || gain > 32768
                || end_gain < -32768
                || end_gain > 32768
                || (!linear_gain && end_gain != 0)
                || (linear_gain && sample_count < 2U)
                || sample_count == 0U
                || start > header.total_frames
                || sample_count > header.total_frames - start
                || !crop_is_valid
                || status != RESONITH_STATUS_OK
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
        }
    }
    if (
        cursor != kHeaderBytes + header.payload_bytes
        || expected_id[RESONITH_MAF_TYPED_FILTER] != header.filter_count
        || expected_id[RESONITH_MAF_TYPED_STOCHASTIC]
            != header.stochastic_count
        || expected_id[RESONITH_MAF_TYPED_SOURCE_FILTER]
            != header.source_count
        || expected_id[RESONITH_MAF_TYPED_TRANSIENT]
            != header.transient_count
        || expected_id[RESONITH_MAF_TYPED_MIX] != header.mix_count
        || expected_id[RESONITH_MAF_TYPED_BASIS] != header.basis_count
        || expected_id[RESONITH_MAF_TYPED_BASIS_INSTANCE]
            != header.basis_instance_count
        || mix_cursor != header.total_frames
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    return RESONITH_STATUS_OK;
}

resonith_status parse_and_validate(
    const std::uint8_t* data,
    std::size_t data_size,
    Header& header,
    resonith_maf_typed_requirements& requirements
) noexcept {
    resonith_status status = parse_header(data, data_size, header);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = calculate_requirements(header, data, requirements);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    return validate_records(header, data);
}

bool overlaps(
    std::uint32_t left_start,
    std::uint32_t left_end,
    std::uint32_t right_start,
    std::uint32_t right_end
) noexcept {
    return left_start < right_end && right_start < left_end;
}

std::uint32_t next_boundary(
    const Header& header,
    const std::uint8_t* data,
    std::uint32_t cursor,
    std::uint32_t proposed_end
) noexcept {
    std::uint32_t result = proposed_end;
    std::size_t record_cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        if (
            next_record(header, data, record_cursor, record)
            != RESONITH_STATUS_OK
        ) {
            return cursor;
        }
        std::uint32_t start = proposed_end;
        std::uint32_t end = proposed_end;
        if (record.type == RESONITH_MAF_TYPED_STOCHASTIC) {
            start = read_u32(record.payload + 4U);
            end = read_u32(record.payload + 8U);
        } else if (record.type == RESONITH_MAF_TYPED_SOURCE_FILTER) {
            start = read_u32(record.payload + 12U);
            end = read_u32(record.payload + 16U);
        } else if (record.type == RESONITH_MAF_TYPED_TRANSIENT) {
            start = read_u32(record.payload + 4U);
            end = start + read_u16(record.payload + 8U);
        } else if (record.type == RESONITH_MAF_TYPED_MIX) {
            start = read_u32(record.payload + 4U);
            end = read_u32(record.payload + 8U);
        } else if (record.type == RESONITH_MAF_TYPED_BASIS_INSTANCE) {
            start = read_u32(record.payload + 8U);
            end = start + read_u16(record.payload + 18U);
        }
        if (start > cursor && start < result) {
            result = start;
        }
        if (end > cursor && end < result) {
            result = end;
        }
    }
    return result;
}

std::uint64_t slice_operations(
    const Header& header,
    const std::uint8_t* data,
    std::uint32_t start,
    std::uint32_t frames
) noexcept {
    const std::uint32_t end = start + frames;
    std::uint64_t operations = 0U;
    std::size_t cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        if (next_record(header, data, cursor, record) != RESONITH_STATUS_OK) {
            return std::numeric_limits<std::uint64_t>::max();
        }
        std::uint64_t addition = 0U;
        if (record.type == RESONITH_MAF_TYPED_STOCHASTIC) {
            const std::uint16_t emitter = read_u16(record.payload + 2U);
            if (
                emitter != kNoEmitter
                && overlaps(
                    start,
                    end,
                    read_u32(record.payload + 4U),
                    read_u32(record.payload + 8U)
                )
            ) {
                addition = 12U * frames;
            }
        } else if (record.type == RESONITH_MAF_TYPED_SOURCE_FILTER) {
            const std::uint32_t lifetime_start =
                read_u32(record.payload + 12U);
            const std::uint32_t lifetime_end =
                read_u32(record.payload + 16U);
            if (overlaps(start, end, lifetime_start, lifetime_end)) {
                if (
                    record.payload[6U]
                    == RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS
                ) {
                    addition = 16U * frames;
                    if (!checked_add(operations, addition, operations)) {
                        return std::numeric_limits<std::uint64_t>::max();
                    }
                    continue;
                }
                Record filter{};
                if (
                    find_record(
                        header,
                        data,
                        RESONITH_MAF_TYPED_FILTER,
                        read_u16(record.payload + 4U),
                        filter
                    ) != RESONITH_STATUS_OK
                ) {
                    return std::numeric_limits<std::uint64_t>::max();
                }
                const std::uint16_t order = read_u16(filter.payload + 2U);
                const std::uint64_t excitation_operations =
                    record.payload[6U]
                            == RESONITH_MAF_TYPED_EXCITATION_STOCHASTIC
                        ? 12U
                        : 4U;
                addition = frames
                    * (excitation_operations + 2U * order + 4U);
            }
        } else if (record.type == RESONITH_MAF_TYPED_TRANSIENT) {
            const std::uint32_t onset = read_u32(record.payload + 4U);
            const std::uint32_t stop =
                onset + read_u16(record.payload + 8U);
            const std::uint32_t overlap_start = std::max(start, onset);
            const std::uint32_t overlap_end = std::min(end, stop);
            if (overlap_end > overlap_start) {
                addition = frames + 5U * (overlap_end - overlap_start);
            }
        } else if (record.type == RESONITH_MAF_TYPED_MIX) {
            if (
                overlaps(
                    start,
                    end,
                    read_u32(record.payload + 4U),
                    read_u32(record.payload + 8U)
                )
            ) {
                const std::uint16_t sources =
                    read_u16(record.payload + 2U);
                addition = static_cast<std::uint64_t>(frames)
                    * header.output_channels
                    * (2U * sources + 2U);
            }
        } else if (record.type == RESONITH_MAF_TYPED_BASIS_INSTANCE) {
            const std::uint32_t onset = read_u32(record.payload + 8U);
            const std::uint32_t stop =
                onset + read_u16(record.payload + 18U);
            const std::uint32_t overlap_start = std::max(start, onset);
            const std::uint32_t overlap_end = std::min(end, stop);
            if (overlap_end > overlap_start) {
                const std::uint64_t per_sample =
                    (read_u16(record.payload + 6U)
                        & RESONITH_MAF_TYPED_BASIS_INSTANCE_LINEAR_GAIN)
                    != 0U
                        ? 9U
                        : 5U;
                addition = frames
                    + per_sample * (overlap_end - overlap_start);
            }
        }
        if (!checked_add(operations, addition, operations)) {
            return std::numeric_limits<std::uint64_t>::max();
        }
    }
    return operations;
}

void impulse_render(
    std::uint32_t lifetime_start,
    std::uint32_t absolute_start,
    std::uint32_t phase_origin,
    std::uint32_t phase_increment,
    std::int32_t gain_q15,
    std::uint32_t frames,
    std::int16_t* output
) noexcept {
    for (std::uint32_t index = 0U; index < frames; ++index) {
        const std::uint32_t local =
            absolute_start + index - lifetime_start;
        const std::uint32_t phase =
            phase_origin + local * phase_increment;
        const std::uint32_t next = phase + phase_increment;
        const bool pulse = local == 0U || next < phase;
        output[index] = pulse
            ? static_cast<std::int16_t>(
                std::clamp<std::int32_t>(gain_q15, -32768, 32767)
            )
            : 0;
    }
}

resonith_status render_slice(
    resonith_maf_typed_session& session,
    const Header& header,
    std::uint32_t start,
    std::uint32_t frames,
    std::int16_t* output
) noexcept {
    const std::uint32_t end = start + frames;
    const std::uint64_t operations = slice_operations(
        header,
        session.stream_data,
        start,
        frames
    );
    std::uint64_t declared_operations = 0U;
    if (
        operations == std::numeric_limits<std::uint64_t>::max()
        || !checked_multiply(
            header.declared_operations_per_frame,
            frames,
            declared_operations
        )
        || operations > declared_operations
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    resonith_maf_operation_budget budget{operations};
    std::fill(
        session.workspace.planar_sources,
        session.workspace.planar_sources
            + static_cast<std::size_t>(header.emitter_count) * frames,
        std::int16_t{0}
    );

    // Long-lived standalone stochastic emitters.
    std::size_t cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        (void)next_record(header, session.stream_data, cursor, record);
        if (record.type != RESONITH_MAF_TYPED_STOCHASTIC) {
            continue;
        }
        const std::uint16_t emitter = read_u16(record.payload + 2U);
        if (
            emitter == kNoEmitter
            || !overlaps(
                start,
                end,
                read_u32(record.payload + 4U),
                read_u32(record.payload + 8U)
            )
        ) {
            continue;
        }
        const resonith_status status = resonith_maf_noise_render(
            header.stream_seed,
            read_u16(record.payload),
            0U,
            start,
            read_i32(record.payload + 12U),
            frames,
            session.workspace.planar_sources
                + static_cast<std::size_t>(emitter) * frames,
            frames,
            &budget
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    // Exactly one excitation family feeds each active causal source filter.
    cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record source{};
        (void)next_record(header, session.stream_data, cursor, source);
        if (source.type != RESONITH_MAF_TYPED_SOURCE_FILTER) {
            continue;
        }
        const std::uint32_t lifetime_start =
            read_u32(source.payload + 12U);
        const std::uint32_t lifetime_end =
            read_u32(source.payload + 16U);
        if (!overlaps(start, end, lifetime_start, lifetime_end)) {
            continue;
        }
        const std::uint16_t emitter = read_u16(source.payload + 2U);
        const std::uint16_t filter_id = read_u16(source.payload + 4U);
        const std::uint8_t excitation_type = source.payload[6U];
        if (
            excitation_type
            == RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS
        ) {
            Record basis_record{};
            std::uint32_t basis_offset = 0U;
            resonith_status status = find_basis(
                header,
                session.stream_data,
                read_u16(source.payload + 8U),
                basis_offset,
                basis_record
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            const std::uint16_t basis_count =
                read_u16(basis_record.payload + 2U);
            const std::uint32_t local_start = start - lifetime_start;
            const std::uint32_t phase_increment =
                read_u32(source.payload + 28U);
            const std::array<std::uint32_t, 2> positions = {
                0U,
                frames,
            };
            const std::array<std::uint32_t, 2> increments = {
                phase_increment,
                phase_increment,
            };
            std::array<std::uint32_t, 2> origins{};
            const resonith_phase_trajectory phase_source = {
                positions.data(),
                increments.data(),
                2U,
                read_u32(source.payload + 24U)
                    + local_start * phase_increment,
            };
            resonith_prepared_phase_trajectory phase{};
            status = resonith_phase_prepare(
                &phase_source,
                origins.data(),
                origins.size(),
                &phase
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            status = resonith_maf_periodic_render(
                session.workspace.bases + basis_offset,
                basis_count,
                &phase,
                0U,
                frames,
                session.workspace.excitation,
                session.workspace.excitation_capacity,
                &budget
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            const std::array<std::uint32_t, 1> gain_positions = {0U};
            const std::array<std::int32_t, 1> gains = {
                read_i32(source.payload + 20U),
            };
            const resonith_gain_event_law gain_source = {
                gain_positions.data(),
                gains.data(),
                1U,
                frames,
            };
            resonith_prepared_gain_law gain{};
            status = resonith_gain_prepare(&gain_source, &gain);
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            status = resonith_maf_compose_truth(
                session.workspace.excitation,
                nullptr,
                1U,
                &gain,
                0U,
                frames,
                session.workspace.filtered,
                session.workspace.filtered_capacity,
                &budget
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            std::copy(
                session.workspace.filtered,
                session.workspace.filtered + frames,
                session.workspace.planar_sources
                    + static_cast<std::size_t>(emitter) * frames
            );
            continue;
        }
        if (start == lifetime_start) {
            std::fill(
                session.workspace.filter_histories
                    + static_cast<std::size_t>(emitter)
                        * RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
                session.workspace.filter_histories
                    + static_cast<std::size_t>(emitter + 1U)
                        * RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
                std::int16_t{0}
            );
        }
        Record filter_record{};
        (void)find_record(
            header,
            session.stream_data,
            RESONITH_MAF_TYPED_FILTER,
            filter_id,
            filter_record
        );
        const std::uint16_t filter_order =
            read_u16(filter_record.payload + 2U);
        const resonith_maf_filter filter = {
            session.workspace.filter_coefficients_q15
                + static_cast<std::size_t>(filter_id)
                    * RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            filter_order,
            0U,
        };
        resonith_status status = RESONITH_STATUS_OK;
        if (
            excitation_type == RESONITH_MAF_TYPED_EXCITATION_IMPULSE
        ) {
            impulse_render(
                lifetime_start,
                start,
                read_u32(source.payload + 24U),
                read_u32(source.payload + 28U),
                read_i32(source.payload + 20U),
                frames,
                session.workspace.excitation
            );
            const std::uint64_t impulse_operations = 4U * frames;
            if (budget.remaining < impulse_operations) {
                return RESONITH_STATUS_PROFILE_BOUND;
            }
            budget.remaining -= impulse_operations;
        } else {
            Record field{};
            (void)find_record(
                header,
                session.stream_data,
                RESONITH_MAF_TYPED_STOCHASTIC,
                read_u16(source.payload + 8U),
                field
            );
            status = resonith_maf_noise_render(
                header.stream_seed,
                read_u16(field.payload),
                0U,
                start,
                combine_gain_q15(
                    read_i32(field.payload + 12U),
                    read_i32(source.payload + 20U)
                ),
                frames,
                session.workspace.excitation,
                session.workspace.excitation_capacity,
                &budget
            );
        }
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        status = resonith_maf_filter_render(
            &filter,
            session.workspace.excitation,
            frames,
            session.workspace.filter_histories
                + static_cast<std::size_t>(emitter)
                    * RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            session.workspace.filtered,
            session.workspace.filtered_capacity,
            &budget
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        std::copy(
            session.workspace.filtered,
            session.workspace.filtered + frames,
            session.workspace.planar_sources
                + static_cast<std::size_t>(emitter) * frames
        );
    }

    // Finite onset events reuse the same emitter plane without changing its
    // long-lived source state.
    std::array<std::int16_t, RESONITH_MAF_MAIN_MAX_TRANSIENT_SAMPLES>
        transient_samples{};
    cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        (void)next_record(header, session.stream_data, cursor, record);
        if (record.type != RESONITH_MAF_TYPED_TRANSIENT) {
            continue;
        }
        const std::uint32_t onset = read_u32(record.payload + 4U);
        const std::uint16_t sample_count =
            read_u16(record.payload + 8U);
        if (!overlaps(start, end, onset, onset + sample_count)) {
            continue;
        }
        const std::uint16_t emitter = read_u16(record.payload + 2U);
        for (std::uint16_t sample = 0U; sample < sample_count; ++sample) {
            transient_samples[sample] = read_i16(
                record.payload + 16U + 2U * sample
            );
        }
        const resonith_maf_transient transient = {
            transient_samples.data(),
            onset,
            sample_count,
            0U,
            read_i32(record.payload + 12U),
        };
        std::copy(
            session.workspace.planar_sources
                + static_cast<std::size_t>(emitter) * frames,
            session.workspace.planar_sources
                + static_cast<std::size_t>(emitter + 1U) * frames,
            session.workspace.filtered
        );
        const resonith_status status = resonith_maf_transients_add(
            session.workspace.filtered,
            start,
            frames,
            &transient,
            1U,
            session.workspace.planar_sources
                + static_cast<std::size_t>(emitter) * frames,
            frames,
            &budget
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    /*
     * Immutable one-shot Basis instances are the exact R-139 dictionary
     * subset. They add objective PCM from caller-owned Basis memory; content
     * search, hashing, and semantic labels never enter the decoder.
     */
    cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        (void)next_record(header, session.stream_data, cursor, record);
        if (record.type != RESONITH_MAF_TYPED_BASIS_INSTANCE) {
            continue;
        }
        const std::uint32_t onset = read_u32(record.payload + 8U);
        const std::uint16_t sample_count =
            read_u16(record.payload + 18U);
        if (!overlaps(start, end, onset, onset + sample_count)) {
            continue;
        }
        Record basis_record{};
        std::uint32_t basis_offset = 0U;
        const resonith_status find_status = find_basis(
            header,
            session.stream_data,
            read_u16(record.payload + 4U),
            basis_offset,
            basis_record
        );
        if (find_status != RESONITH_STATUS_OK) {
            return find_status;
        }
        const std::uint32_t overlap_start = std::max(start, onset);
        const std::uint32_t overlap_end =
            std::min(end, onset + sample_count);
        const std::uint64_t required_operations =
            frames
            + (
                (read_u16(record.payload + 6U)
                    & RESONITH_MAF_TYPED_BASIS_INSTANCE_LINEAR_GAIN)
                != 0U
                    ? 9U
                    : 5U
            ) * (overlap_end - overlap_start);
        if (budget.remaining < required_operations) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        budget.remaining -= required_operations;
        const std::uint16_t emitter = read_u16(record.payload + 2U);
        const std::uint16_t source_offset =
            read_u16(record.payload + 16U);
        const std::uint16_t flags = read_u16(record.payload + 6U);
        const std::int32_t start_gain = read_i32(record.payload + 12U);
        const std::int32_t end_gain = read_i32(record.payload + 20U);
        const bool circular =
            (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_CIRCULAR) != 0U;
        const bool linear_gain =
            (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_LINEAR_GAIN) != 0U;
        const bool reverse =
            (flags & RESONITH_MAF_TYPED_BASIS_INSTANCE_REVERSE) != 0U;
        const std::uint16_t basis_samples =
            read_u16(basis_record.payload + 2U);
        std::int16_t* emitter_plane =
            session.workspace.planar_sources
            + static_cast<std::size_t>(emitter) * frames;
        for (
            std::uint32_t position = overlap_start;
            position < overlap_end;
            ++position
        ) {
            const std::uint32_t local_instance = position - onset;
            const std::uint32_t local_slice = position - start;
            const std::uint32_t source_index = reverse
                ? circular
                    ? (
                        static_cast<std::uint32_t>(source_offset)
                        + basis_samples
                        - local_instance % basis_samples
                    ) % basis_samples
                    : source_offset - local_instance
                : circular
                    ? (
                        static_cast<std::uint32_t>(source_offset)
                            + local_instance
                    ) % basis_samples
                    : source_offset + local_instance;
            const std::int32_t gain = linear_gain
                ? interpolate_gain_q15(
                    start_gain,
                    end_gain,
                    local_instance,
                    sample_count
                )
                : start_gain;
            const std::int32_t scaled = combine_gain_q15(
                session.workspace.bases[
                    basis_offset + source_index
                ],
                gain
            );
            emitter_plane[local_slice] = static_cast<std::int16_t>(
                std::clamp<std::int32_t>(
                    static_cast<std::int32_t>(emitter_plane[local_slice])
                        + scaled,
                    -32768,
                    32767
                )
            );
        }
    }

    // The active matrix is a lifetime record, not a repeated frame header.
    cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        (void)next_record(header, session.stream_data, cursor, record);
        if (
            record.type != RESONITH_MAF_TYPED_MIX
            || !overlaps(
                start,
                end,
                read_u32(record.payload + 4U),
                read_u32(record.payload + 8U)
            )
        ) {
            continue;
        }
        const std::uint16_t source_count = read_u16(record.payload + 2U);
        const std::uint8_t* emitter_ids = record.payload + 16U;
        const std::uint8_t* matrix =
            emitter_ids + 2U * source_count;
        for (std::uint16_t channel = 0U; channel < header.output_channels;
             ++channel) {
            for (std::uint16_t source = 0U; source < source_count; ++source) {
                session.workspace.mix_matrix_q15[
                    static_cast<std::size_t>(channel) * source_count + source
                ] = read_i16(
                    matrix
                        + 2U * (
                            static_cast<std::size_t>(channel) * source_count
                            + source
                        )
                );
            }
        }
        return resonith_maf_mix_q15(
            session.workspace.planar_sources,
            source_count,
            frames,
            session.workspace.mix_matrix_q15,
            header.output_channels,
            output,
            static_cast<std::size_t>(frames) * header.output_channels,
            &budget
        );
    }
    return RESONITH_STATUS_MALFORMED;
}

}  // namespace

extern "C" resonith_status resonith_maf_typed_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_maf_typed_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *requirements = {};
    Header header{};
    return parse_and_validate(data, data_size, header, *requirements);
}

extern "C" resonith_status resonith_maf_typed_open(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_maf_typed_workspace* workspace,
    resonith_maf_typed_session* session
) {
    if (workspace == nullptr || session == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *session = {};
    Header header{};
    resonith_maf_typed_requirements requirements{};
    resonith_status status = parse_and_validate(
        data,
        data_size,
        header,
        requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        workspace->filter_coefficients_q15 == nullptr
        || workspace->bases == nullptr
        || workspace->filter_histories == nullptr
        || workspace->planar_sources == nullptr
        || workspace->excitation == nullptr
        || workspace->filtered == nullptr
        || workspace->mix_matrix_q15 == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        workspace->filter_coefficient_capacity
            < requirements.filter_coefficient_elements
        || workspace->basis_capacity < requirements.basis_elements
        || workspace->filter_history_capacity
            < requirements.filter_history_elements
        || workspace->planar_capacity < requirements.planar_elements
        || workspace->excitation_capacity < requirements.render_quantum
        || workspace->filtered_capacity < requirements.render_quantum
        || workspace->mix_matrix_capacity
            < requirements.mix_matrix_elements
    ) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    std::array<std::int16_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> reflection{};
    std::size_t basis_offset = 0U;
    std::size_t cursor = kHeaderBytes;
    for (std::uint16_t index = 0U; index < header.record_count; ++index) {
        Record record{};
        (void)next_record(header, data, cursor, record);
        if (record.type != RESONITH_MAF_TYPED_FILTER) {
            if (record.type == RESONITH_MAF_TYPED_BASIS) {
                const std::uint16_t sample_count =
                    read_u16(record.payload + 2U);
                for (std::uint16_t sample = 0U; sample < sample_count;
                     ++sample) {
                    workspace->bases[basis_offset + sample] = read_i16(
                        record.payload + 8U + 2U * sample
                    );
                }
                basis_offset += sample_count;
            }
            continue;
        }
        const std::uint16_t filter_id = read_u16(record.payload);
        const std::uint16_t order = read_u16(record.payload + 2U);
        for (std::uint16_t item = 0U; item < order; ++item) {
            reflection[item] = read_i16(record.payload + 8U + 2U * item);
        }
        resonith_maf_filter prepared{};
        status = resonith_maf_filter_prepare(
            reflection.data(),
            order,
            workspace->filter_coefficients_q15
                + static_cast<std::size_t>(filter_id)
                    * RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            RESONITH_MAF_MAIN_MAX_FILTER_ORDER,
            &prepared
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }
    std::fill(
        workspace->filter_histories,
        workspace->filter_histories + requirements.filter_history_elements,
        std::int16_t{0}
    );
    session->stream_data = data;
    session->stream_size = data_size;
    session->stream_seed = header.stream_seed;
    session->cursor = 0U;
    session->requirements = requirements;
    session->workspace = *workspace;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_maf_typed_render(
    resonith_maf_typed_session* session,
    std::uint32_t requested_frames,
    std::int16_t* interleaved_output,
    std::size_t output_capacity,
    std::uint32_t* frames_written
) {
    if (session == nullptr || frames_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_written = 0U;
    if (
        session->stream_data == nullptr
        || requested_frames > session->requirements.render_quantum
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (session->cursor >= session->requirements.total_frames) {
        return RESONITH_STATUS_OK;
    }
    if (requested_frames == 0U || interleaved_output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    const std::uint32_t frames = std::min(
        requested_frames,
        session->requirements.total_frames - session->cursor
    );
    const std::size_t required_output =
        static_cast<std::size_t>(frames)
        * session->requirements.output_channels;
    if (output_capacity < required_output) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    Header header{};
    const resonith_status header_status = parse_header(
        session->stream_data,
        session->stream_size,
        header
    );
    if (header_status != RESONITH_STATUS_OK) {
        return header_status;
    }

    /*
     * Preflight every internal lifetime slice before the first history or PCM
     * write. This keeps one public render call transactional even when it
     * crosses several source, transient, or mix boundaries.
     */
    std::uint32_t preflighted = 0U;
    while (preflighted < frames) {
        const std::uint32_t slice_start = session->cursor + preflighted;
        const std::uint32_t slice_end = next_boundary(
            header,
            session->stream_data,
            slice_start,
            session->cursor + frames
        );
        if (slice_end <= slice_start) {
            return RESONITH_STATUS_MALFORMED;
        }
        const std::uint32_t slice_frames = slice_end - slice_start;
        const std::uint64_t operations = slice_operations(
            header,
            session->stream_data,
            slice_start,
            slice_frames
        );
        std::uint64_t declared_operations = 0U;
        if (
            operations == std::numeric_limits<std::uint64_t>::max()
            || !checked_multiply(
                header.declared_operations_per_frame,
                slice_frames,
                declared_operations
            )
            || operations > declared_operations
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        preflighted += slice_frames;
    }

    std::uint32_t rendered = 0U;
    while (rendered < frames) {
        const std::uint32_t slice_start = session->cursor + rendered;
        const std::uint32_t proposed_end = session->cursor + frames;
        const std::uint32_t slice_end = next_boundary(
            header,
            session->stream_data,
            slice_start,
            proposed_end
        );
        if (slice_end <= slice_start) {
            return RESONITH_STATUS_MALFORMED;
        }
        const std::uint32_t slice_frames = slice_end - slice_start;
        const resonith_status status = render_slice(
            *session,
            header,
            slice_start,
            slice_frames,
            interleaved_output
                + static_cast<std::size_t>(rendered)
                    * header.output_channels
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        rendered += slice_frames;
    }
    session->cursor += frames;
    *frames_written = frames;
    return RESONITH_STATUS_OK;
}
