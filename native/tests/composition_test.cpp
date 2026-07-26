#include "resonith/composition.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::int16_t, 20> kUnity = {
    -32768, -30000, -20000, -10000, 0, 10000, 20000, 30000, 32767, -12345,
    12345, -22222, 22222, -1, 1, 15000, -15000, 25000, -25000, 7777,
};
constexpr std::array<std::uint32_t, 4> kGainPositions = {
    0U, 3U, 10U, 15U,
};
constexpr std::array<std::int32_t, 4> kGainsQ15 = {
    32768, 16384, -32768, 65536,
};
constexpr std::array<std::int64_t, 20> kInnovation = {
    -10, -9, -8, -7, -6, -5, -4, -3, -2, -1,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
};
constexpr std::array<std::int16_t, 20> kExpected = {
    -32768, -30027, -20024, -5021, -18, 4985, 9988, 14991, 16378, -6175,
    -12345, 22225, -22216, 10, 11, 30015, -29982, 32767, -32768, 15581,
};
constexpr std::array<std::int16_t, 20> kExpectedGainOnly = {
    -32768, -30000, -20000, -5000, 0, 5000, 10000, 15000, 16384, -6172,
    -12345, 22222, -22222, 1, -1, 30000, -30000, 32767, -32768, 15554,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    const resonith_gain_event_law source = {
        kGainPositions.data(),
        kGainsQ15.data(),
        static_cast<std::uint32_t>(kGainPositions.size()),
        static_cast<std::uint32_t>(kUnity.size()),
    };
    resonith_prepared_gain_law law{};
    if (!expect(
            resonith_gain_prepare(&source, &law) == RESONITH_STATUS_OK,
            "gain law preparation"
        )) {
        return 1;
    }

    std::array<std::int16_t, 20> output{};
    if (!expect(
            resonith_compose_truth(
                kUnity.data(),
                kInnovation.data(),
                3U,
                &law,
                0U,
                output.size(),
                output.data(),
                output.size()
            ) == RESONITH_STATUS_OK
                && output == kExpected,
            "gain and Truth composition"
        )) {
        return 1;
    }
    if (!expect(
            resonith_compose_truth(
                kUnity.data(),
                nullptr,
                0U,
                &law,
                0U,
                output.size(),
                output.data(),
                output.size()
            ) == RESONITH_STATUS_OK
                && output == kExpectedGainOnly,
            "gain-only composition"
        )) {
        return 1;
    }

    output.fill(0);
    constexpr std::array<std::uint32_t, 6> kCuts = {
        0U, 2U, 7U, 10U, 16U, 20U,
    };
    for (std::size_t index = 0; index + 1U < kCuts.size(); ++index) {
        const std::uint32_t start = kCuts[index];
        const std::size_t count = kCuts[index + 1U] - start;
        if (!expect(
                resonith_compose_truth(
                    kUnity.data() + start,
                    kInnovation.data() + start,
                    3U,
                    &law,
                    start,
                    count,
                    output.data() + start,
                    output.size() - start
                ) == RESONITH_STATUS_OK,
                "sliced Truth composition"
            )) {
            return 1;
        }
    }
    if (!expect(output == kExpected, "composition partition independence")) {
        return 1;
    }

    auto invalid_gains = kGainsQ15;
    invalid_gains[0] = 131072;
    const resonith_gain_event_law invalid = {
        kGainPositions.data(),
        invalid_gains.data(),
        static_cast<std::uint32_t>(kGainPositions.size()),
        static_cast<std::uint32_t>(kUnity.size()),
    };
    if (!expect(
            resonith_gain_prepare(&invalid, &law)
                == RESONITH_STATUS_PROFILE_BOUND,
            "gain bound rejection"
        )) {
        return 1;
    }
    return 0;
}
