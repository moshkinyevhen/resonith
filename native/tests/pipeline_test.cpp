#include "resonith/basis.h"
#include "resonith/composition.h"
#include "resonith/liftpack.h"
#include "resonith/trajectory.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::uint8_t, 40> kBrawPayload = {
    0x01, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00,
    0xd0, 0x8a, 0xe0, 0xb1, 0xf0, 0xd8, 0x00, 0x00,
    0x10, 0x27, 0x20, 0x4e, 0x30, 0x75, 0x20, 0x4e,
    0x10, 0x27, 0x00, 0x00, 0xf0, 0xd8, 0xe0, 0xb1,
    0xd0, 0x8a, 0x68, 0xc5, 0x00, 0x00, 0x98, 0x3a,
};
constexpr std::array<std::uint8_t, 61> kInnovationPayload = {
    0x52, 0x53, 0x4c, 0x31, 0x01, 0x10, 0x00, 0x28, 0x00, 0x00, 0x00, 0x03,
    0x00, 0x00, 0x00, 0x10, 0x00, 0x02, 0x00, 0x01, 0x34, 0x00, 0x00, 0x00,
    0xff, 0xff, 0x37, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x02, 0x00, 0x00,
    0x19, 0x00, 0x00, 0x00, 0x7f, 0x03, 0x00, 0x00, 0x08, 0x00, 0x02, 0x00,
    0x01, 0x1d, 0x00, 0x00, 0x00, 0xff, 0x4f, 0x00, 0x00, 0x4e, 0x0b, 0x65,
    0xa5,
};
constexpr std::array<std::uint32_t, 4> kPhasePositions = {
    0U, 5U, 17U, 40U,
};
constexpr std::array<std::uint32_t, 4> kPhaseIncrements = {
    0x08000000U, 0x10000000U, 0x06000000U, 0x18000000U,
};
constexpr std::array<std::uint32_t, 4> kGainPositions = {
    0U, 7U, 23U, 35U,
};
constexpr std::array<std::int32_t, 4> kGainsQ15 = {
    32768, 24576, -16384, 49152,
};
constexpr std::array<std::int16_t, 40> kExpectedPcm = {
    -18682, -13679, -7676, -673, 7330, 16333, 26336, 18068, 11353, 5027,
    -907, -6451, -11604, -16366, -20739, -19207, -13813, -9006, -4784, -12,
    5310, 11183, -7792, 14089, 10750, 7166, 3338, -736, -5053, -9615,
    -14422, -10460, -5158, 388, 6179, -32768, -29440, -90, -870, -32768,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    std::array<std::int16_t, 16> basis{};
    std::size_t basis_elements = 0U;
    if (!expect(
            resonith_raw_basis_decode(
                kBrawPayload.data(),
                kBrawPayload.size(),
                basis.data(),
                basis.size(),
                &basis_elements
            ) == RESONITH_STATUS_OK
                && basis_elements == basis.size(),
            "pipeline Basis decode"
        )) {
        return 1;
    }

    const resonith_phase_trajectory phase_source = {
        kPhasePositions.data(),
        kPhaseIncrements.data(),
        static_cast<std::uint32_t>(kPhasePositions.size()),
        0x12345678U,
    };
    std::array<std::uint32_t, 4> origins{};
    resonith_prepared_phase_trajectory phase{};
    if (!expect(
            resonith_phase_prepare(
                &phase_source,
                origins.data(),
                origins.size(),
                &phase
            ) == RESONITH_STATUS_OK,
            "pipeline phase prepare"
        )) {
        return 1;
    }
    std::array<std::int16_t, 40> unity{};
    if (!expect(
            resonith_periodic_render(
                basis.data(),
                basis.size(),
                &phase,
                0U,
                unity.size(),
                unity.data(),
                unity.size()
            ) == RESONITH_STATUS_OK,
            "pipeline periodic render"
        )) {
        return 1;
    }

    resonith_liftpack_info innovation_info{};
    if (!expect(
            resonith_liftpack_inspect(
                kInnovationPayload.data(),
                kInnovationPayload.size(),
                &innovation_info
            ) == RESONITH_STATUS_OK
                && innovation_info.sample_count == unity.size(),
            "pipeline Innovation inspect"
        )) {
        return 1;
    }
    std::array<std::int64_t, 40> innovation{};
    std::array<std::int64_t, 32> liftpack_scratch{};
    std::size_t innovation_count = 0U;
    if (!expect(
            resonith_liftpack_decode(
                kInnovationPayload.data(),
                kInnovationPayload.size(),
                innovation.data(),
                innovation.size(),
                liftpack_scratch.data(),
                liftpack_scratch.size(),
                &innovation_count
            ) == RESONITH_STATUS_OK
                && innovation_count == innovation.size(),
            "pipeline Innovation decode"
        )) {
        return 1;
    }

    const resonith_gain_event_law gain_source = {
        kGainPositions.data(),
        kGainsQ15.data(),
        static_cast<std::uint32_t>(kGainPositions.size()),
        static_cast<std::uint32_t>(unity.size()),
    };
    resonith_prepared_gain_law gain{};
    if (!expect(
            resonith_gain_prepare(&gain_source, &gain) == RESONITH_STATUS_OK,
            "pipeline gain prepare"
        )) {
        return 1;
    }
    std::array<std::int16_t, 40> output{};
    if (!expect(
            resonith_compose_truth(
                unity.data(),
                innovation.data(),
                3U,
                &gain,
                0U,
                output.size(),
                output.data(),
                output.size()
            ) == RESONITH_STATUS_OK
                && output == kExpectedPcm,
            "complete causal pipeline"
        )) {
        return 1;
    }
    return 0;
}
