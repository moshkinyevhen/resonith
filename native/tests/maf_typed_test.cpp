#include "resonith/maf_typed.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace {

void append_u16(std::vector<std::uint8_t>& bytes, std::uint16_t value) {
    bytes.push_back(static_cast<std::uint8_t>(value));
    bytes.push_back(static_cast<std::uint8_t>(value >> 8U));
}

void append_i16(std::vector<std::uint8_t>& bytes, std::int16_t value) {
    append_u16(bytes, static_cast<std::uint16_t>(value));
}

void append_u32(std::vector<std::uint8_t>& bytes, std::uint32_t value) {
    for (unsigned shift = 0U; shift < 32U; shift += 8U) {
        bytes.push_back(static_cast<std::uint8_t>(value >> shift));
    }
}

void append_i32(std::vector<std::uint8_t>& bytes, std::int32_t value) {
    append_u32(bytes, static_cast<std::uint32_t>(value));
}

void write_u16(
    std::vector<std::uint8_t>& bytes,
    std::size_t offset,
    std::uint16_t value
) {
    bytes[offset] = static_cast<std::uint8_t>(value);
    bytes[offset + 1U] = static_cast<std::uint8_t>(value >> 8U);
}

void write_u32(
    std::vector<std::uint8_t>& bytes,
    std::size_t offset,
    std::uint32_t value
) {
    for (unsigned shift = 0U; shift < 32U; shift += 8U) {
        bytes[offset + shift / 8U] =
            static_cast<std::uint8_t>(value >> shift);
    }
}

void write_u64(
    std::vector<std::uint8_t>& bytes,
    std::size_t offset,
    std::uint64_t value
) {
    write_u32(bytes, offset, static_cast<std::uint32_t>(value));
    write_u32(
        bytes,
        offset + 4U,
        static_cast<std::uint32_t>(value >> 32U)
    );
}

std::uint32_t crc32(
    const std::uint8_t* data,
    std::size_t size
) noexcept {
    std::uint32_t crc = 0xffff'ffffU;
    for (std::size_t index = 0U; index < size; ++index) {
        crc ^= data[index];
        for (unsigned bit = 0U; bit < 8U; ++bit) {
            const std::uint32_t mask = 0U - (crc & 1U);
            crc = (crc >> 1U) ^ (0xedb8'8320U & mask);
        }
    }
    return ~crc;
}

void append_record(
    std::vector<std::uint8_t>& payload,
    std::uint8_t type,
    const std::vector<std::uint8_t>& record
) {
    payload.push_back(type);
    payload.push_back(1U);
    append_u16(payload, 0U);
    append_u32(payload, static_cast<std::uint32_t>(record.size()));
    payload.insert(payload.end(), record.begin(), record.end());
}

std::vector<std::uint8_t> build_stream() {
    std::vector<std::uint8_t> payload;

    std::vector<std::uint8_t> filter;
    append_u16(filter, 0U);
    append_u16(filter, 2U);
    append_u32(filter, 0U);
    append_i16(filter, 4096);
    append_i16(filter, -2048);
    append_record(payload, RESONITH_MAF_TYPED_FILTER, filter);

    std::vector<std::uint8_t> direct_noise;
    append_u16(direct_noise, 0U);
    append_u16(direct_noise, 1U);
    append_u32(direct_noise, 0U);
    append_u32(direct_noise, 32U);
    append_i32(direct_noise, 6000);
    append_u32(direct_noise, 0U);
    append_record(
        payload,
        RESONITH_MAF_TYPED_STOCHASTIC,
        direct_noise
    );

    std::vector<std::uint8_t> excitation_noise;
    append_u16(excitation_noise, 1U);
    append_u16(excitation_noise, 0xffffU);
    append_u32(excitation_noise, 16U);
    append_u32(excitation_noise, 32U);
    append_i32(excitation_noise, 9000);
    append_u32(excitation_noise, 0U);
    append_record(
        payload,
        RESONITH_MAF_TYPED_STOCHASTIC,
        excitation_noise
    );

    std::vector<std::uint8_t> impulse_source;
    append_u16(impulse_source, 0U);
    append_u16(impulse_source, 0U);
    append_u16(impulse_source, 0U);
    impulse_source.push_back(RESONITH_MAF_TYPED_EXCITATION_IMPULSE);
    impulse_source.push_back(0U);
    append_u16(impulse_source, 0xffffU);
    append_u16(impulse_source, 0U);
    append_u32(impulse_source, 0U);
    append_u32(impulse_source, 16U);
    append_i32(impulse_source, 18000);
    append_u32(impulse_source, 0U);
    append_u32(impulse_source, 0x4000'0000U);
    append_record(
        payload,
        RESONITH_MAF_TYPED_SOURCE_FILTER,
        impulse_source
    );

    std::vector<std::uint8_t> noise_source;
    append_u16(noise_source, 1U);
    append_u16(noise_source, 0U);
    append_u16(noise_source, 0U);
    noise_source.push_back(RESONITH_MAF_TYPED_EXCITATION_STOCHASTIC);
    noise_source.push_back(0U);
    append_u16(noise_source, 1U);
    append_u16(noise_source, 0U);
    append_u32(noise_source, 16U);
    append_u32(noise_source, 32U);
    append_i32(noise_source, 16384);
    append_u32(noise_source, 0U);
    append_u32(noise_source, 0U);
    append_record(
        payload,
        RESONITH_MAF_TYPED_SOURCE_FILTER,
        noise_source
    );

    std::vector<std::uint8_t> transient;
    append_u16(transient, 0U);
    append_u16(transient, 0U);
    append_u32(transient, 8U);
    append_u16(transient, 4U);
    append_u16(transient, 0U);
    append_i32(transient, 32768);
    append_i16(transient, 1000);
    append_i16(transient, 2000);
    append_i16(transient, -1000);
    append_i16(transient, -500);
    append_record(payload, RESONITH_MAF_TYPED_TRANSIENT, transient);

    std::vector<std::uint8_t> mix;
    append_u16(mix, 0U);
    append_u16(mix, 2U);
    append_u32(mix, 0U);
    append_u32(mix, 32U);
    append_u16(mix, 2U);
    append_u16(mix, 0U);
    append_u16(mix, 0U);
    append_u16(mix, 1U);
    append_i16(mix, 32767);
    append_i16(mix, 0);
    append_i16(mix, 0);
    append_i16(mix, 32767);
    append_record(payload, RESONITH_MAF_TYPED_MIX, mix);

    std::vector<std::uint8_t> stream(
        RESONITH_MAF_TYPED_HEADER_BYTES,
        0U
    );
    std::memcpy(stream.data(), "MFT1", 4U);
    stream[4] = 1U;
    write_u16(stream, 6U, RESONITH_MAF_TYPED_HEADER_BYTES);
    write_u32(stream, 8U, 48000U);
    write_u32(stream, 12U, 32U);
    write_u32(stream, 16U, 16U);
    write_u16(stream, 20U, 2U);
    write_u16(stream, 22U, 2U);
    write_u16(stream, 24U, 1U);
    write_u16(stream, 26U, 2U);
    write_u16(stream, 28U, 2U);
    write_u16(stream, 30U, 1U);
    write_u16(stream, 32U, 1U);
    write_u16(stream, 34U, 7U);
    write_u64(stream, 36U, 0x5245'534f'4e49'5448ULL);
    write_u32(stream, 44U, 256U);
    write_u32(stream, 48U, static_cast<std::uint32_t>(payload.size()));
    write_u32(stream, 52U, 128U);
    write_u32(stream, 56U, 136U);
    stream.insert(stream.end(), payload.begin(), payload.end());
    append_u32(stream, crc32(stream.data(), stream.size()));
    return stream;
}

std::vector<std::uint8_t> build_basis_instance_stream() {
    std::vector<std::uint8_t> payload;

    std::vector<std::uint8_t> mix;
    append_u16(mix, 0U);
    append_u16(mix, 1U);
    append_u32(mix, 0U);
    append_u32(mix, 20U);
    append_u16(mix, 1U);
    append_u16(mix, 0U);
    append_u16(mix, 0U);
    append_i16(mix, 32767);
    append_record(payload, RESONITH_MAF_TYPED_MIX, mix);

    std::vector<std::uint8_t> basis;
    append_u16(basis, 0U);
    append_u16(basis, 4U);
    append_u32(basis, 0U);
    append_i16(basis, 1000);
    append_i16(basis, -2000);
    append_i16(basis, 3000);
    append_i16(basis, -4000);
    append_record(payload, RESONITH_MAF_TYPED_BASIS, basis);

    for (std::uint16_t id = 0U; id < 3U; ++id) {
        std::vector<std::uint8_t> instance;
        append_u16(instance, id);
        append_u16(instance, 0U);
        append_u16(instance, 0U);
        append_u16(
            instance,
            id == 0U
                ? 0U
                : (
                    RESONITH_MAF_TYPED_BASIS_INSTANCE_CIRCULAR
                    | (
                        id == 2U
                            ? static_cast<std::uint16_t>(
                                  RESONITH_MAF_TYPED_BASIS_INSTANCE_LINEAR_GAIN
                              )
                            : 0U
                    )
                )
        );
        append_u32(instance, id == 0U ? 0U : (id == 1U ? 8U : 14U));
        append_i32(instance, id == 1U ? -32768 : 32768);
        append_u16(instance, id == 0U ? 0U : (id == 1U ? 1U : 2U));
        append_u16(instance, 4U);
        append_i32(instance, 0);
        append_record(
            payload,
            RESONITH_MAF_TYPED_BASIS_INSTANCE,
            instance
        );
    }

    std::vector<std::uint8_t> stream(
        RESONITH_MAF_TYPED_HEADER_BYTES,
        0U
    );
    std::memcpy(stream.data(), "MFT1", 4U);
    stream[4] = 1U;
    write_u16(stream, 6U, RESONITH_MAF_TYPED_HEADER_BYTES);
    write_u32(stream, 8U, 48000U);
    write_u32(stream, 12U, 20U);
    write_u32(stream, 16U, 8U);
    write_u16(stream, 20U, 1U);
    write_u16(stream, 22U, 1U);
    write_u16(stream, 32U, 1U);
    write_u16(stream, 34U, 5U);
    write_u64(stream, 36U, 0x5245'534f'4e49'5448ULL);
    write_u32(stream, 44U, 128U);
    write_u32(stream, 48U, static_cast<std::uint32_t>(payload.size()));
    write_u32(stream, 52U, 40U);
    write_u32(stream, 56U, 50U);
    stream.insert(stream.end(), payload.begin(), payload.end());
    append_u32(stream, crc32(stream.data(), stream.size()));
    return stream;
}

std::vector<std::uint8_t> build_reverse_basis_instance_stream() {
    std::vector<std::uint8_t> payload;

    std::vector<std::uint8_t> mix;
    append_u16(mix, 0U);
    append_u16(mix, 1U);
    append_u32(mix, 0U);
    append_u32(mix, 8U);
    append_u16(mix, 1U);
    append_u16(mix, 0U);
    append_u16(mix, 0U);
    append_i16(mix, 32767);
    append_record(payload, RESONITH_MAF_TYPED_MIX, mix);

    std::vector<std::uint8_t> basis;
    append_u16(basis, 0U);
    append_u16(basis, 4U);
    append_u32(basis, 0U);
    constexpr std::array<std::int16_t, 4> basis_values{
        100,
        -200,
        300,
        -400,
    };
    for (const std::int16_t value : basis_values) {
        append_i16(basis, value);
    }
    append_record(payload, RESONITH_MAF_TYPED_BASIS, basis);

    for (std::uint16_t id = 0U; id < 2U; ++id) {
        std::vector<std::uint8_t> instance;
        append_u16(instance, id);
        append_u16(instance, 0U);
        append_u16(instance, 0U);
        append_u16(
            instance,
            RESONITH_MAF_TYPED_BASIS_INSTANCE_REVERSE
                | (
                    id == 1U
                        ? static_cast<std::uint16_t>(
                              RESONITH_MAF_TYPED_BASIS_INSTANCE_CIRCULAR
                          )
                        : 0U
                )
        );
        append_u32(instance, id == 0U ? 0U : 4U);
        append_i32(instance, 32768);
        append_u16(instance, id == 0U ? 3U : 1U);
        append_u16(instance, 4U);
        append_i32(instance, 0);
        append_record(
            payload,
            RESONITH_MAF_TYPED_BASIS_INSTANCE,
            instance
        );
    }

    std::vector<std::uint8_t> stream(
        RESONITH_MAF_TYPED_HEADER_BYTES,
        0U
    );
    std::memcpy(stream.data(), "MFT1", 4U);
    stream[4] = 1U;
    write_u16(stream, 6U, RESONITH_MAF_TYPED_HEADER_BYTES);
    write_u32(stream, 8U, 48000U);
    write_u32(stream, 12U, 8U);
    write_u32(stream, 16U, 8U);
    write_u16(stream, 20U, 1U);
    write_u16(stream, 22U, 1U);
    write_u16(stream, 32U, 1U);
    write_u16(stream, 34U, 4U);
    write_u64(stream, 36U, 0x5245'534f'4e49'5448ULL);
    write_u32(stream, 44U, 128U);
    write_u32(stream, 48U, static_cast<std::uint32_t>(payload.size()));
    write_u32(stream, 52U, 40U);
    write_u32(stream, 56U, 50U);
    stream.insert(stream.end(), payload.begin(), payload.end());
    append_u32(stream, crc32(stream.data(), stream.size()));
    return stream;
}

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

struct Memory {
    std::array<std::int32_t, 16> coefficients{};
    std::array<std::int16_t, 4> bases{};
    std::array<std::int16_t, 32> histories{};
    std::array<std::int16_t, 32> planar{};
    std::array<std::int16_t, 16> excitation{};
    std::array<std::int16_t, 16> filtered{};
    std::array<std::int16_t, 4> matrix{};

    resonith_maf_typed_workspace view() {
        return {
            coefficients.data(),
            coefficients.size(),
            bases.data(),
            0U,
            histories.data(),
            histories.size(),
            planar.data(),
            planar.size(),
            excitation.data(),
            excitation.size(),
            filtered.data(),
            filtered.size(),
            matrix.data(),
            matrix.size(),
        };
    }
};

bool render_partition(
    const std::vector<std::uint8_t>& stream,
    const std::vector<std::uint32_t>& partitions,
    std::array<std::int16_t, 64>& output
) {
    Memory memory{};
    const resonith_maf_typed_workspace workspace = memory.view();
    resonith_maf_typed_session session{};
    if (
        resonith_maf_typed_open(
            stream.data(),
            stream.size(),
            &workspace,
            &session
        ) != RESONITH_STATUS_OK
    ) {
        return false;
    }
    std::uint32_t cursor = 0U;
    for (const std::uint32_t requested : partitions) {
        std::uint32_t written = 0U;
        if (
            resonith_maf_typed_render(
                &session,
                requested,
                output.data() + 2U * cursor,
                output.size() - 2U * cursor,
                &written
            ) != RESONITH_STATUS_OK
            || written != requested
        ) {
            return false;
        }
        cursor += written;
    }
    std::uint32_t written = 99U;
    return cursor == 32U
        && resonith_maf_typed_render(
            &session,
            1U,
            output.data(),
            output.size(),
            &written
        ) == RESONITH_STATUS_OK
        && written == 0U;
}

bool test_inspect_and_partition_invariance() {
    const std::vector<std::uint8_t> stream = build_stream();
    resonith_maf_typed_requirements requirements{};
    if (!expect(
            resonith_maf_typed_inspect(
                stream.data(),
                stream.size(),
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.total_frames == 32U
                && requirements.output_channels == 2U
                && requirements.filter_coefficient_elements == 16U
                && requirements.planar_elements == 32U
                && requirements.working_elements == 32U,
            "MFT1 exact inspection"
        )) {
        return false;
    }
    std::array<std::int16_t, 64> regular{};
    std::array<std::int16_t, 64> irregular{};
    if (
        !render_partition(stream, {16U, 16U}, regular)
        || !render_partition(stream, {7U, 5U, 4U, 9U, 7U}, irregular)
    ) {
        return expect(false, "MFT1 sequential render");
    }
    return expect(
        regular == irregular
            && std::any_of(
                regular.begin(),
                regular.end(),
                [](std::int16_t value) { return value != 0; }
            ),
        "MFT1 callback partition invariance"
    );
}

bool test_hostile_streams() {
    const std::vector<std::uint8_t> stream = build_stream();
    resonith_maf_typed_requirements requirements{};
    if (!expect(
            resonith_maf_typed_inspect(
                stream.data(),
                stream.size() - 1U,
                &requirements
            ) == RESONITH_STATUS_TRUNCATED,
            "MFT1 truncation rejection"
        )) {
        return false;
    }
    std::vector<std::uint8_t> corrupt = stream;
    corrupt[80U] ^= 0x80U;
    if (!expect(
            resonith_maf_typed_inspect(
                corrupt.data(),
                corrupt.size(),
                &requirements
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "MFT1 checksum rejection"
        )) {
        return false;
    }

    std::vector<std::uint8_t> underdeclared = stream;
    write_u32(underdeclared, 44U, 1U);
    write_u32(
        underdeclared,
        underdeclared.size() - 4U,
        crc32(underdeclared.data(), underdeclared.size() - 4U)
    );
    Memory memory{};
    const resonith_maf_typed_workspace workspace = memory.view();
    resonith_maf_typed_session session{};
    std::array<std::int16_t, 32> untouched{};
    untouched.fill(1234);
    std::uint32_t written = 77U;
    if (!expect(
            resonith_maf_typed_open(
                underdeclared.data(),
                underdeclared.size(),
                &workspace,
                &session
            ) == RESONITH_STATUS_OK
                && resonith_maf_typed_render(
                    &session,
                    16U,
                    untouched.data(),
                    untouched.size(),
                    &written
                ) == RESONITH_STATUS_PROFILE_BOUND
                && session.cursor == 0U
                && written == 0U
                && std::all_of(
                    untouched.begin(),
                    untouched.end(),
                    [](std::int16_t value) { return value == 1234; }
                ),
            "MFT1 operation preflight is transactional"
        )) {
        return false;
    }

    // The second source body begins at byte 188 in this canonical vector.
    std::vector<std::uint8_t> overlap = stream;
    write_u32(overlap, 188U + 12U, 15U);
    write_u32(
        overlap,
        overlap.size() - 4U,
        crc32(overlap.data(), overlap.size() - 4U)
    );
    return expect(
        resonith_maf_typed_inspect(
            overlap.data(),
            overlap.size(),
            &requirements
        ) == RESONITH_STATUS_MALFORMED,
        "MFT1 overlapping source-lifetime rejection"
    );
}

bool test_basis_instance_partition_invariance() {
    const std::vector<std::uint8_t> stream = build_basis_instance_stream();
    resonith_maf_typed_requirements requirements{};
    const resonith_status inspection_status = resonith_maf_typed_inspect(
        stream.data(),
        stream.size(),
        &requirements
    );
    if (inspection_status != RESONITH_STATUS_OK) {
        std::fprintf(
            stderr,
            "MFT1 Basis Instance inspection status: %d\n",
            static_cast<int>(inspection_status)
        );
    }
    if (!expect(
            inspection_status == RESONITH_STATUS_OK
                && requirements.basis_count == 1U
                && requirements.basis_instance_count == 3U
                && requirements.basis_elements == 4U,
            "MFT1 Basis Instance inspection"
        )) {
        return false;
    }

    Memory regular_memory{};
    Memory irregular_memory{};
    resonith_maf_typed_workspace regular_workspace = regular_memory.view();
    resonith_maf_typed_workspace irregular_workspace =
        irregular_memory.view();
    regular_workspace.basis_capacity = regular_memory.bases.size();
    irregular_workspace.basis_capacity = irregular_memory.bases.size();
    resonith_maf_typed_session regular_session{};
    resonith_maf_typed_session irregular_session{};
    if (
        resonith_maf_typed_open(
            stream.data(),
            stream.size(),
            &regular_workspace,
            &regular_session
        ) != RESONITH_STATUS_OK
        || resonith_maf_typed_open(
            stream.data(),
            stream.size(),
            &irregular_workspace,
            &irregular_session
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "MFT1 Basis Instance open");
    }

    std::array<std::int16_t, 20> regular{};
    std::array<std::int16_t, 20> irregular{};
    std::uint32_t regular_cursor = 0U;
    for (const std::uint32_t request : {8U, 8U, 4U}) {
        std::uint32_t written = 0U;
        const resonith_status status = resonith_maf_typed_render(
            &regular_session,
            request,
            regular.data() + regular_cursor,
            regular.size() - regular_cursor,
            &written
        );
        if (status != RESONITH_STATUS_OK) {
            std::fprintf(
                stderr,
                "MFT1 Basis Instance render status: %d at %u\n",
                static_cast<int>(status),
                regular_cursor
            );
            return expect(false, "MFT1 Basis Instance regular render");
        }
        regular_cursor += written;
    }
    std::uint32_t irregular_cursor = 0U;
    for (const std::uint32_t request : {3U, 5U, 2U, 7U, 3U}) {
        std::uint32_t written = 0U;
        if (
            resonith_maf_typed_render(
                &irregular_session,
                request,
                irregular.data() + irregular_cursor,
                irregular.size() - irregular_cursor,
                &written
            ) != RESONITH_STATUS_OK
        ) {
            return expect(false, "MFT1 Basis Instance irregular render");
        }
        irregular_cursor += written;
    }
    if (!expect(
        regular_cursor == 20U
            && irregular_cursor == 20U
            && regular == irregular
            && regular[0] == 1000
            && regular[1] == -2000
            && regular[2] == 3000
            && regular[3] == -4000
            && std::all_of(
                regular.begin() + 4,
                regular.begin() + 8,
                [](std::int16_t value) { return value == 0; }
            )
            && regular[8] == 2000
            && regular[9] == -3000
            && regular[10] == 4000
            && regular[11] == -1000
            && std::all_of(
                regular.begin() + 12,
                regular.begin() + 14,
                [](std::int16_t value) { return value == 0; }
            )
            && regular[14] == 3000
            && regular[17] == 0
            && regular[18] == 0
            && regular[19] == 0,
        "MFT1 phase, counterphase, envelope, and callback invariance"
    )) {
        return false;
    }

    std::vector<std::uint8_t> invalid_reference = stream;
    write_u16(invalid_reference, 128U, 1U);
    write_u32(
        invalid_reference,
        invalid_reference.size() - 4U,
        crc32(
            invalid_reference.data(),
            invalid_reference.size() - 4U
        )
    );
    resonith_maf_typed_requirements invalid_requirements{};
    if (!expect(
        resonith_maf_typed_inspect(
            invalid_reference.data(),
            invalid_reference.size(),
            &invalid_requirements
        ) == RESONITH_STATUS_MALFORMED,
        "MFT1 unresolved Basis Instance rejection"
    )) {
        return false;
    }

    std::vector<std::uint8_t> invalid_flags = stream;
    write_u16(invalid_flags, 130U, 4U);
    write_u32(
        invalid_flags,
        invalid_flags.size() - 4U,
        crc32(invalid_flags.data(), invalid_flags.size() - 4U)
    );
    return expect(
        resonith_maf_typed_inspect(
            invalid_flags.data(),
            invalid_flags.size(),
            &invalid_requirements
        ) == RESONITH_STATUS_MALFORMED,
        "MFT1 unknown Basis Instance flag rejection"
    );
}

bool test_reverse_basis_instances() {
    const std::vector<std::uint8_t> stream =
        build_reverse_basis_instance_stream();
    resonith_maf_typed_requirements requirements{};
    if (!expect(
            resonith_maf_typed_inspect(
                stream.data(),
                stream.size(),
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.basis_count == 1U
                && requirements.basis_instance_count == 2U,
            "MFT1 reverse Basis Instance inspection"
        )) {
        return false;
    }

    Memory memory{};
    resonith_maf_typed_workspace workspace = memory.view();
    workspace.basis_capacity = memory.bases.size();
    resonith_maf_typed_session session{};
    if (
        resonith_maf_typed_open(
            stream.data(),
            stream.size(),
            &workspace,
            &session
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "MFT1 reverse Basis Instance open");
    }
    std::array<std::int16_t, 8> output{};
    std::uint32_t cursor = 0U;
    for (const std::uint32_t request : {3U, 2U, 3U}) {
        std::uint32_t written = 0U;
        if (
            resonith_maf_typed_render(
                &session,
                request,
                output.data() + cursor,
                output.size() - cursor,
                &written
            ) != RESONITH_STATUS_OK
            || written != request
        ) {
            return expect(false, "MFT1 reverse Basis Instance render");
        }
        cursor += written;
    }
    const std::array<std::int16_t, 8> expected{
        -400,
        300,
        -200,
        100,
        -200,
        100,
        -400,
        300,
    };
    return expect(
        cursor == output.size() && output == expected,
        "MFT1 reverse/circular composition and callback invariance"
    );
}

}  // namespace

int main() {
    return test_inspect_and_partition_invariance()
            && test_basis_instance_partition_invariance()
            && test_reverse_basis_instances()
            && test_hostile_streams()
        ? 0
        : 1;
}
