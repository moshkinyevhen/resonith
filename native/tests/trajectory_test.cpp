#include "resonith/trajectory.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::int16_t, 16> kBasis = {
    -30000, -20000, -10000, 0, 10000, 20000, 30000, 20000,
    10000, 0, -10000, -20000, -30000, -15000, 0, 15000,
};
constexpr std::array<std::uint32_t, 4> kPositions = {
    0U,
    5U,
    17U,
    40U,
};
constexpr std::array<std::uint32_t, 4> kIncrements = {
    0x08000000U,
    0x10000000U,
    0x06000000U,
    0x18000000U,
};
constexpr std::array<std::uint32_t, 4> kOrigins = {
    0x12345678U,
    0x4a345678U,
    0xd3345678U,
    0x23345678U,
};
constexpr std::array<std::uint32_t, 40> kExpectedPhases = {
    0x12345678U, 0x1a345678U, 0x23cdf012U, 0x2f012345U, 0x3bcdf012U,
    0x4a345678U, 0x5a345678U, 0x695f0123U, 0x77b45678U, 0x85345678U,
    0x91df0123U, 0x9db45678U, 0xa8b45678U, 0xb2df0123U, 0xbc345678U,
    0xc4b45678U, 0xcc5f0123U, 0xd3345678U, 0xd9345678U, 0xdffcaf83U,
    0xe78d6199U, 0xefe66cbbU, 0xf907d0e7U, 0x02f18e1fU, 0x0da3a462U,
    0x191e13b0U, 0x2560dc09U, 0x326bfd6dU, 0x403f77dcU, 0x4edb4b57U,
    0x5e3f77dcU, 0x6e6bfd6dU, 0x7f60dc09U, 0x911e13b0U, 0xa3a3a462U,
    0xb6f18e1fU, 0xcb07d0e7U, 0xdfe66cbbU, 0xf58d6199U, 0x0bfcaf83U,
};
constexpr std::array<std::int16_t, 40> kExpectedOutput = {
    -18622, -13622, -7622, -622, 7378, 16378, 26378, 24143, 15185, 6747,
    -1169, -8565, -15440, -21794, -27628, -25590, -18402, -11996, -6371,
    -12, 7080, 14906, -10398, -28160, -21476, -14302, -6639, 1514, 10155,
    19285, 28905, 20986, 10389, -698, -12274, -24340, -19659, -94, -616,
    -22508,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    const resonith_phase_trajectory source = {
        kPositions.data(),
        kIncrements.data(),
        static_cast<std::uint32_t>(kPositions.size()),
        0x12345678U,
    };
    std::array<std::uint32_t, 4> origins{};
    resonith_prepared_phase_trajectory trajectory{};
    if (!expect(
            resonith_phase_prepare(
                &source,
                origins.data(),
                origins.size(),
                &trajectory
            ) == RESONITH_STATUS_OK
                && origins == kOrigins
                && trajectory.sample_count == 40U,
            "phase trajectory preparation"
        )) {
        return 1;
    }

    std::array<std::uint32_t, 40> phases{};
    if (!expect(
            resonith_phase_render(
                &trajectory,
                0U,
                phases.size(),
                phases.data(),
                phases.size()
            ) == RESONITH_STATUS_OK
                && phases == kExpectedPhases,
            "absolute phase rendering"
        )) {
        return 1;
    }
    std::array<std::int16_t, 40> output{};
    if (!expect(
            resonith_periodic_render(
                kBasis.data(),
                kBasis.size(),
                &trajectory,
                0U,
                output.size(),
                output.data(),
                output.size()
            ) == RESONITH_STATUS_OK
                && output == kExpectedOutput,
            "periodic Basis rendering"
        )) {
        return 1;
    }

    // Discontinuous callback sizes must concatenate to the same absolute law.
    std::array<std::int16_t, 40> sliced{};
    constexpr std::array<std::uint32_t, 7> kCuts = {
        0U, 1U, 5U, 13U, 17U, 31U, 40U,
    };
    for (std::size_t index = 0; index + 1U < kCuts.size(); ++index) {
        const std::uint32_t start = kCuts[index];
        const std::size_t count = kCuts[index + 1U] - start;
        if (!expect(
                resonith_periodic_render(
                    kBasis.data(),
                    kBasis.size(),
                    &trajectory,
                    start,
                    count,
                    sliced.data() + start,
                    sliced.size() - start
                ) == RESONITH_STATUS_OK,
                "sliced periodic rendering"
            )) {
            return 1;
        }
    }
    if (!expect(sliced == output, "callback partition independence")) {
        return 1;
    }

    auto invalid_positions = kPositions;
    invalid_positions[1] = 32769U;
    const resonith_phase_trajectory invalid = {
        invalid_positions.data(),
        kIncrements.data(),
        static_cast<std::uint32_t>(invalid_positions.size()),
        0U,
    };
    if (!expect(
            resonith_phase_prepare(
                &invalid,
                origins.data(),
                origins.size(),
                &trajectory
            ) == RESONITH_STATUS_PROFILE_BOUND,
            "phase span rejection"
        )) {
        return 1;
    }
    return 0;
}
