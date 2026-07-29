#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

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

std::uint64_t next_random(std::uint64_t* state) noexcept {
    *state ^= *state << 13U;
    *state ^= *state >> 7U;
    *state ^= *state << 17U;
    return *state;
}

int main(int argument_count, char** arguments) {
    std::uint64_t stress_count = 0U;
    if (argument_count == 2) {
        char* end = nullptr;
        const unsigned long long parsed = std::strtoull(
            arguments[1],
            &end,
            10
        );
        if (
            end == arguments[1]
            || *end != '\0'
            || parsed > 1'000'000ULL
        ) {
            return 2;
        }
        stress_count = static_cast<std::uint64_t>(parsed);
    } else if (argument_count != 1) {
        return 2;
    }
    constexpr std::array<std::array<std::uint8_t, 96>, 10> cases = {{
        {},
        {1U, 0U, 0U, 0U, 0U, 0U, 0U, 0U},
        {0x7eU, 0x15U, 0x00U, 0x2bU, 0x2bU, 0x21U, 0x00U, 0x0aU},
        {0x7eU, 0x00U, 0x00U, 0x2bU, 0x2bU, 0x01U, 0x00U, 0x0aU},
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
    std::uint64_t random_state = 0x7265736f6e697468ULL;
    for (
        std::uint64_t iteration = 0U;
        iteration < stress_count;
        ++iteration
    ) {
        std::array<std::uint8_t, 96> input{};
        const std::size_t size = 1U + static_cast<std::size_t>(
            next_random(&random_state) % input.size()
        );
        for (std::size_t index = 0U; index < size; ++index) {
            input[index] = static_cast<std::uint8_t>(
                next_random(&random_state)
            );
        }
        if (LLVMFuzzerTestOneInput(input.data(), size) != 0) {
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
        "\"v2_mutation_fuzz\":false,\"stress_inputs\":%llu,"
        "\"device_bytes\":0}\n",
        reachability,
        static_cast<unsigned long long>(stress_count)
    );
    return 0;
}
