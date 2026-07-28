#include <array>
#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
);

int main() {
    constexpr std::array<std::array<std::uint8_t, 96>, 8> cases = {{
        {},
        {1U, 0U, 0U, 0U, 0U, 0U, 0U, 0U},
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
    return 0;
}
