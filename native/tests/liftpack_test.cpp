#include "resonith/container.h"
#include "resonith/liftpack.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::uint8_t, 203> kConformanceStream = {
    0x52, 0x53, 0x4c, 0x31, 0x01, 0x40, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x03,
    0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x02, 0x00,
    0x00, 0xa1, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x7f, 0x3f, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x40, 0x00, 0x00, 0x01, 0x10, 0x00, 0x04, 0x00, 0x00, 0xfe,
    0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0x25, 0x28, 0x68, 0x53,
};

/*
 * Encoder-forced coverage vector: four 16-sample blocks exercise IDENTITY,
 * DELTA1, DELTA2, and HAAR with both Rice and packed entropy paths.
 */
constexpr std::array<std::uint8_t, 139> kAllModesStream = {
    0x52, 0x53, 0x4c, 0x31, 0x01, 0x10, 0x00, 0x40, 0x00, 0x00, 0x00, 0x04,
    0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x02, 0xe0, 0x00, 0x00, 0x00,
    0xec, 0xf3, 0xfd, 0xf3, 0xef, 0xff, 0xfc, 0xdf, 0xff, 0xcf, 0xff, 0xef,
    0xff, 0x3f, 0xff, 0xff, 0xfd, 0xff, 0x3f, 0xff, 0xff, 0xef, 0xff, 0xff,
    0xcf, 0xff, 0xff, 0xdf, 0x10, 0x00, 0x01, 0x01, 0x08, 0x80, 0x00, 0x00,
    0x00, 0xc8, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x0e,
    0x0e, 0x0e, 0x0e, 0x0e, 0x0e, 0x10, 0x00, 0x02, 0x00, 0x01, 0x9b, 0x00,
    0x00, 0x00, 0xff, 0xff, 0xff, 0x7f, 0x63, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x99, 0x99, 0x99, 0x99, 0x99, 0x99, 0x99, 0x01, 0x10, 0x00,
    0x03, 0x01, 0x0a, 0xa0, 0x00, 0x00, 0x00, 0x48, 0xd1, 0xa0, 0x81, 0x06,
    0x84, 0xbd, 0x31, 0xe6, 0x1b, 0xc2, 0x08, 0x53, 0xb2, 0x30, 0xc2, 0x08,
    0x23, 0x4c, 0xc9, 0x3a, 0x63, 0xd9, 0x65,
};

/*
 * Canonical RSC1 header and directory for kConformanceStream. Keeping the
 * payload in one array avoids duplicating the LiftPack bytes in the test.
 */
constexpr std::array<std::uint8_t, 112> kContainerPrefix = {
    0x52, 0x53, 0x43, 0x31, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0xbb, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x00,
    0x50, 0x00, 0x00, 0x00, 0x66, 0x9f, 0x6b, 0xc4, 0x52, 0x53, 0x4c, 0x31,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x70, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xcb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xcb, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x1c, 0xdf, 0x44, 0x21, 0x6d, 0x58, 0x81, 0x21,
    0x62, 0x38, 0x8d, 0xfe, 0x58, 0xc2, 0xb6, 0x02, 0x37, 0x2b, 0xf1, 0x44,
    0xd3, 0x6a, 0xf0, 0x0f, 0x7a, 0x19, 0xcb, 0x39, 0x25, 0x0e, 0x0d, 0x92,
    0x06, 0x09, 0xfe, 0xe6,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    std::array<std::uint8_t, 315> container_stream{};
    std::copy(
        kContainerPrefix.begin(),
        kContainerPrefix.end(),
        container_stream.begin()
    );
    std::copy(
        kConformanceStream.begin(),
        kConformanceStream.end(),
        container_stream.begin()
            + static_cast<std::ptrdiff_t>(kContainerPrefix.size())
    );

    resonith_container_view container{};
    if (!expect(
            resonith_container_open(
                container_stream.data(),
                container_stream.size(),
                &container
            ) == RESONITH_STATUS_OK
                && container.section_count == 1U
                && container.timebase_hz == 48'000U,
            "RSC1 container inspection"
        )) {
        return 1;
    }
    constexpr std::array<std::uint8_t, 4> kResidualType = {
        'R',
        'S',
        'L',
        '1',
    };
    resonith_container_section residual_section{};
    if (!expect(
            resonith_container_find_section(
                &container,
                kResidualType.data(),
                0U,
                &residual_section
            ) == RESONITH_STATUS_OK
                && residual_section.payload_size == kConformanceStream.size(),
            "RSC1 residual lookup"
        )) {
        return 1;
    }
    if (!expect(
            resonith_container_verify_section(&residual_section)
                == RESONITH_STATUS_OK,
            "RSC1 residual integrity"
        )) {
        return 1;
    }
    resonith_container_section missing_section{};
    if (!expect(
            resonith_container_get_section(
                &container,
                1U,
                &missing_section
            ) == RESONITH_STATUS_NOT_FOUND,
            "RSC1 section bound"
        )) {
        return 1;
    }

    resonith_liftpack_info info{};
    if (!expect(
            resonith_liftpack_inspect(
                residual_section.payload,
                residual_section.payload_size,
                &info
            ) == RESONITH_STATUS_OK,
            "conformance stream inspection"
        )) {
        return 1;
    }
    if (!expect(
            info.sample_count == 192
                && info.block_count == 3
                && info.block_size == 64,
            "conformance stream metadata"
        )) {
        return 1;
    }

    std::array<std::int64_t, 192> output{};
    std::array<std::int64_t, 128> scratch{};
    std::size_t written = 0;
    if (!expect(
            resonith_liftpack_decode(
                residual_section.payload,
                residual_section.payload_size,
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size(),
                &written
            ) == RESONITH_STATUS_OK,
            "conformance stream decode"
        )) {
        return 1;
    }
    if (!expect(written == output.size(), "decoded sample count")) {
        return 1;
    }
    for (std::size_t index = 0; index < 64; ++index) {
        if (!expect(output[index] == 0, "zero block output")) {
            return 1;
        }
        if (!expect(
                output[64 + index] == static_cast<std::int64_t>(index) - 32,
                "ramp block output"
            )) {
            return 1;
        }
        const std::int64_t expected = index % 2 == 0 ? 32767 : -32768;
        if (!expect(output[128 + index] == expected, "packed block output")) {
            return 1;
        }
    }

    std::array<std::int64_t, 64> all_modes_output{};
    written = 0;
    if (!expect(
            resonith_liftpack_decode(
                kAllModesStream.data(),
                kAllModesStream.size(),
                all_modes_output.data(),
                all_modes_output.size(),
                scratch.data(),
                scratch.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == all_modes_output.size(),
            "all transform and entropy modes decode"
        )) {
        return 1;
    }
    for (std::int64_t index = 0; index < 16; ++index) {
        const std::int64_t identity = (index % 2 == 0 ? 1 : -1)
            * (index * 3 + 1);
        if (!expect(
                all_modes_output[static_cast<std::size_t>(index)] == identity,
                "identity mode output"
            )) {
            return 1;
        }
        if (!expect(
                all_modes_output[16U + static_cast<std::size_t>(index)]
                    == 100 + index * 7,
                "delta1 mode output"
            )) {
            return 1;
        }
        if (!expect(
                all_modes_output[32U + static_cast<std::size_t>(index)]
                    == index * index - 50,
                "delta2 mode output"
            )) {
            return 1;
        }
        if (!expect(
                all_modes_output[48U + static_cast<std::size_t>(index)]
                    == (index % 5) * 100 - index * 3,
                "Haar mode output"
            )) {
            return 1;
        }
    }

    auto damaged_directory = container_stream;
    damaged_directory[40] ^= 0x01U;
    if (!expect(
            resonith_container_open(
                damaged_directory.data(),
                damaged_directory.size(),
                &container
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "RSC1 directory checksum rejection"
        )) {
        return 1;
    }
    auto damaged_payload = container_stream;
    damaged_payload.back() ^= 0x01U;
    if (!expect(
            resonith_container_open(
                damaged_payload.data(),
                damaged_payload.size(),
                &container
            ) == RESONITH_STATUS_OK
                && resonith_container_find_section(
                    &container,
                    kResidualType.data(),
                    0U,
                    &residual_section
                ) == RESONITH_STATUS_OK
                && resonith_container_verify_section(&residual_section)
                    == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "RSC1 payload checksum rejection"
        )) {
        return 1;
    }

    auto corrupted = kConformanceStream;
    corrupted[80] ^= 0x01;
    if (!expect(
            resonith_liftpack_inspect(
                corrupted.data(),
                corrupted.size(),
                &info
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "checksum rejection"
        )) {
        return 1;
    }
    if (!expect(
            resonith_liftpack_inspect(
                kConformanceStream.data(),
                12,
                &info
            ) == RESONITH_STATUS_TRUNCATED,
            "truncation rejection"
        )) {
        return 1;
    }
    written = 99;
    if (!expect(
            resonith_liftpack_decode(
                kConformanceStream.data(),
                kConformanceStream.size(),
                output.data(),
                output.size() - 1,
                scratch.data(),
                scratch.size(),
                &written
            ) == RESONITH_STATUS_OUTPUT_TOO_SMALL
                && written == 0,
            "output bound rejection"
        )) {
        return 1;
    }
    if (!expect(
            resonith_liftpack_decode(
                kConformanceStream.data(),
                kConformanceStream.size(),
                output.data(),
                output.size(),
                scratch.data(),
                scratch.size() - 1,
                &written
            ) == RESONITH_STATUS_SCRATCH_TOO_SMALL,
            "scratch bound rejection"
        )) {
        return 1;
    }
    return 0;
}
