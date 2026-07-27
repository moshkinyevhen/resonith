#include "resonith/maf.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

std::uint16_t read_u16(
    const std::uint8_t* data,
    std::size_t size,
    std::size_t offset
) noexcept {
    if (offset + 2U > size) {
        return 0U;
    }
    return static_cast<std::uint16_t>(
        data[offset]
        | (static_cast<std::uint16_t>(data[offset + 1U]) << 8U)
    );
}

std::uint32_t read_u32(
    const std::uint8_t* data,
    std::size_t size,
    std::size_t offset
) noexcept {
    if (offset + 4U > size) {
        return 0U;
    }
    return static_cast<std::uint32_t>(data[offset])
        | (static_cast<std::uint32_t>(data[offset + 1U]) << 8U)
        | (static_cast<std::uint32_t>(data[offset + 2U]) << 16U)
        | (static_cast<std::uint32_t>(data[offset + 3U]) << 24U);
}

std::uint64_t read_u64(
    const std::uint8_t* data,
    std::size_t size,
    std::size_t offset
) noexcept {
    return read_u32(data, size, offset)
        | (static_cast<std::uint64_t>(
            read_u32(data, size, offset + 4U)
        ) << 32U);
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    if (data == nullptr || size == 0U) {
        return 0;
    }

    resonith_maf_limits limits{};
    (void)resonith_maf_main_limits(&limits);
    resonith_maf_resource_declaration declaration = {
        read_u32(data, size, 0U),
        read_u32(data, size, 4U),
        read_u32(data, size, 8U),
        read_u32(data, size, 12U),
        read_u32(data, size, 16U),
        read_u32(data, size, 20U),
        read_u32(data, size, 24U),
        read_u32(data, size, 28U),
        read_u32(data, size, 32U),
        read_u32(data, size, 36U),
        read_u16(data, size, 40U),
        read_u16(data, size, 42U),
        read_u16(data, size, 44U),
        read_u16(data, size, 46U),
        read_u64(data, size, 48U),
        read_u64(data, size, 56U),
        read_u64(data, size, 64U),
    };
    resonith_maf_requirements requirements{};
    (void)resonith_maf_resources_validate(
        &limits,
        &declaration,
        &requirements
    );

    constexpr std::size_t kMaximumSamples = 64U;
    const std::size_t sample_count = size % (kMaximumSamples + 1U);
    std::array<std::int16_t, kMaximumSamples> excitation{};
    std::array<std::int16_t, kMaximumSamples> output{};
    std::array<std::int64_t, kMaximumSamples> innovation{};
    for (std::size_t index = 0U; index < sample_count; ++index) {
        excitation[index] = static_cast<std::int16_t>(
            read_u16(data, size, index)
        );
        innovation[index] = static_cast<std::int8_t>(
            data[index % size]
        );
    }

    resonith_maf_operation_budget budget{
        read_u64(data, size, 3U),
    };
    (void)resonith_maf_noise_render(
        read_u64(data, size, 11U),
        read_u32(data, size, 19U),
        read_u16(data, size, 23U),
        read_u32(data, size, 25U),
        static_cast<std::int32_t>(read_u32(data, size, 29U)),
        sample_count,
        output.data(),
        output.size(),
        &budget
    );

    const std::uint16_t filter_order = static_cast<std::uint16_t>(
        1U + data[0] % RESONITH_MAF_MAIN_MAX_FILTER_ORDER
    );
    std::array<std::int16_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> reflection{};
    std::array<std::int32_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> coefficients{};
    std::array<std::int16_t, RESONITH_MAF_MAIN_MAX_FILTER_ORDER> history{};
    for (std::uint16_t index = 0U; index < filter_order; ++index) {
        reflection[index] = static_cast<std::int16_t>(
            read_u16(data, size, index * 2U)
        );
    }
    resonith_maf_filter filter{};
    if (
        resonith_maf_filter_prepare(
            reflection.data(),
            filter_order,
            coefficients.data(),
            coefficients.size(),
            &filter
        ) == RESONITH_STATUS_OK
    ) {
        budget.remaining = read_u64(data, size, 37U);
        (void)resonith_maf_filter_render(
            &filter,
            excitation.data(),
            sample_count,
            history.data(),
            history.size(),
            output.data(),
            output.size(),
            &budget
        );
    }

    budget.remaining = read_u64(data, size, 45U);
    (void)resonith_maf_innovation_add(
        excitation.data(),
        innovation.data(),
        read_u32(data, size, 53U),
        sample_count,
        output.data(),
        output.size(),
        &budget
    );

    const resonith_maf_transient transient = {
        excitation.data(),
        read_u32(data, size, 57U),
        static_cast<std::uint16_t>(sample_count),
        read_u16(data, size, 61U),
        static_cast<std::int32_t>(read_u32(data, size, 63U)),
    };
    budget.remaining = read_u64(data, size, 67U);
    (void)resonith_maf_transients_add(
        excitation.data(),
        read_u32(data, size, 71U),
        sample_count,
        &transient,
        1U,
        output.data(),
        output.size(),
        &budget
    );
    return 0;
}
