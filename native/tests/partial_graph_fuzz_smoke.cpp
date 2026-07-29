#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
);
extern "C" void
resonith_partial_graph_fuzz_reset_reachability() noexcept;
extern "C" std::size_t
resonith_partial_graph_fuzz_reachability_count() noexcept;
extern "C" std::uint64_t resonith_partial_graph_fuzz_reachability(
    std::size_t index
) noexcept;

int main() {
    constexpr std::array<std::array<std::uint8_t, 96>, 9> cases = {{
        {},
        {1U, 0U, 0U, 0U, 0U, 0U, 0U, 0U},
        {0x7eU, 0x15U, 0x00U, 0x2bU, 0x2bU, 0x21U, 0x00U, 0x0aU},
        {8U, 1U, 3U, 0xffU, 0U, 0x80U, 0x7fU, 0x55U},
        {8U, 2U, 4U, 1U, 2U, 3U, 4U, 5U},
        {8U, 3U, 5U, 0xffU, 0xffU, 0xffU, 0xffU, 0xffU},
        {8U, 4U, 6U, 0x55U, 0xaaU, 0x55U, 0xaaU, 0x55U},
        {8U, 13U, 7U, 0U, 1U, 0U, 1U, 0U},
        {8U, 14U, 8U, 0x80U, 0U, 0x80U, 0U, 0x80U},
    }};
    for (const auto& input : cases) {
        if (LLVMFuzzerTestOneInput(input.data(), input.size()) != 0) {
            return 1;
        }
    }
    for (std::uint8_t mutation = 0U; mutation < 15U; ++mutation) {
        std::array<std::uint8_t, 96> input{};
        input[0] = 8U;
        input[1] = static_cast<std::uint8_t>(
            0x80U + ((mutation + 7U) % 15U)
        );
        input[2] = mutation;
        if (LLVMFuzzerTestOneInput(input.data(), input.size()) != 0) {
            return 1;
        }
    }
    for (std::uint8_t bound = 0U; bound < 8U; ++bound) {
        std::array<std::uint8_t, 96> input{};
        input[0] = 8U;
        input[3] = 0x41U;
        input[4] = bound;
        input[5] = static_cast<std::uint8_t>(bound % 7U);
        if (LLVMFuzzerTestOneInput(input.data(), input.size()) != 0) {
            return 1;
        }
    }
    resonith_partial_graph_fuzz_reset_reachability();
    for (std::uint32_t repetition = 0U; repetition < 100U; ++repetition) {
        std::array<std::uint8_t, 96> baseline{};
        baseline[0] = 8U;
        baseline[5] = 6U;
        if (
            LLVMFuzzerTestOneInput(baseline.data(), baseline.size()) != 0
        ) {
            return 1;
        }
        for (std::uint8_t mutation = 0U; mutation < 15U; ++mutation) {
            std::array<std::uint8_t, 96> input{};
            input[0] = 8U;
            input[1] = static_cast<std::uint8_t>(
                0x80U + ((mutation + 7U) % 15U)
            );
            input[2] = mutation;
            if (LLVMFuzzerTestOneInput(input.data(), input.size()) != 0) {
                return 1;
            }
        }
        for (std::uint8_t mutation = 0U; mutation < 8U; ++mutation) {
            std::array<std::uint8_t, 96> input{};
            input[0] = 8U;
            input[5] = mutation;
            if (LLVMFuzzerTestOneInput(input.data(), input.size()) != 0) {
                return 1;
            }
        }
    }
    const std::size_t reachability =
        resonith_partial_graph_fuzz_reachability_count();
    if (reachability != 11U) {
        return 1;
    }
    for (std::size_t index = 0U; index < reachability; ++index) {
        if (resonith_partial_graph_fuzz_reachability(index) < 100U) {
            return 1;
        }
    }
    std::printf(
        "{\"schema\":\"resonith-r202-v3-reachability-1\","
        "\"branches\":%zu,\"minimum_hits\":100,"
        "\"v2_mutation_fuzz\":false,\"device_bytes\":0}\n",
        reachability
    );
    return 0;
}
