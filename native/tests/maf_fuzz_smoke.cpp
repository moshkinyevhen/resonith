#include <array>
#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
);

namespace {

std::uint64_t next_random(std::uint64_t& state) noexcept {
    state ^= state << 13U;
    state ^= state >> 7U;
    state ^= state << 17U;
    return state;
}

}  // namespace

int main() {
    constexpr std::size_t kMaximumInput = 1024U;
    constexpr std::size_t kIterations = 20000U;
    std::array<std::uint8_t, kMaximumInput> input{};
    std::uint64_t state = 0x5245534f4e495448ULL;

    // Exercise reproducible edge corpora before pseudo-random mutations.
    (void)LLVMFuzzerTestOneInput(input.data(), input.size());
    input.fill(0xffU);
    (void)LLVMFuzzerTestOneInput(input.data(), input.size());
    for (std::size_t index = 0U; index < input.size(); ++index) {
        input[index] = static_cast<std::uint8_t>(index);
    }
    (void)LLVMFuzzerTestOneInput(input.data(), input.size());

    for (std::size_t iteration = 0U; iteration < kIterations; ++iteration) {
        const std::size_t size = 1U + static_cast<std::size_t>(
            next_random(state) % kMaximumInput
        );
        for (std::size_t index = 0U; index < size; ++index) {
            input[index] = static_cast<std::uint8_t>(next_random(state));
        }
        (void)LLVMFuzzerTestOneInput(input.data(), size);
    }
    return 0;
}
