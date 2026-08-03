#include "resonith/persistent_cell.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <vector>

namespace {

bool expect(bool condition, const char* message) {
    if (!condition) std::fprintf(stderr, "FAIL: %s\n", message);
    return condition;
}

void put16(std::vector<std::uint8_t>& bytes, std::size_t at, std::uint16_t value) {
    bytes[at] = static_cast<std::uint8_t>(value);
    bytes[at + 1U] = static_cast<std::uint8_t>(value >> 8U);
}

void put32(std::vector<std::uint8_t>& bytes, std::size_t at, std::uint32_t value) {
    for (std::size_t i = 0U; i < 4U; ++i)
        bytes[at + i] = static_cast<std::uint8_t>(value >> (8U * i));
}

void put64(std::vector<std::uint8_t>& bytes, std::size_t at, std::uint64_t value) {
    for (std::size_t i = 0U; i < 8U; ++i)
        bytes[at + i] = static_cast<std::uint8_t>(value >> (8U * i));
}

void cell(
    std::vector<std::uint8_t>& bytes,
    std::size_t at,
    std::uint16_t id,
    std::uint32_t start,
    std::uint32_t duration,
    std::uint16_t fade_in,
    std::uint16_t fade_out,
    std::int16_t reflection
) {
    put16(bytes, at, id); put32(bytes, at + 4U, start);
    put32(bytes, at + 8U, duration); put16(bytes, at + 12U, fade_in);
    put16(bytes, at + 14U, fade_out); put32(bytes, at + 20U, 1U << 26U);
    put16(bytes, at + 24U, 4000U);
    put16(bytes, at + 28U, static_cast<std::uint16_t>(reflection));
}

void event(
    std::vector<std::uint8_t>& bytes,
    std::size_t at,
    std::uint16_t id,
    std::uint32_t duration
) {
    put16(bytes, at, id); put32(bytes, at + 8U, duration);
    put32(bytes, at + 12U, 1U << 26U); put16(bytes, at + 16U, 4000U);
}

std::vector<std::uint8_t> stream() {
    constexpr std::uint32_t samples = 512U, cells = 2U, events = 2U;
    std::vector<std::uint8_t> bytes(
        RESONITH_PCELL_HEADER_BYTES + cells * RESONITH_PCELL_CELL_BYTES
            + events * RESONITH_PCELL_EVENT_BYTES);
    bytes[0] = 'S'; bytes[1] = 'F'; bytes[2] = 'C'; bytes[3] = '2';
    bytes[4] = 2U; put32(bytes, 8U, RESONITH_PCELL_SAMPLE_RATE);
    put32(bytes, 12U, samples); put64(bytes, 16U, 0x5245534f4e495448ULL);
    put32(bytes, 24U, cells); put32(bytes, 28U, events);
    put32(bytes, 40U, RESONITH_PCELL_HEADER_BYTES);
    cell(bytes, 48U, 1U, 0U, 320U, 0U, 80U, -8192);
    cell(bytes, 96U, 2U, 240U, 272U, 80U, 0U, -16384);
    event(bytes, 144U, 1U, 320U); event(bytes, 168U, 2U, 272U);
    return bytes;
}

bool test_inspect_and_render() {
    const auto bytes = stream(); resonith_pcell_inspection inspection{};
    if (!expect(resonith_pcell_inspect(bytes.data(), bytes.size(), &inspection)
            == RESONITH_STATUS_OK && inspection.sample_count == 512U
            && inspection.cell_count == 2U && inspection.truth_offset == bytes.size(),
            "inspect canonical stream")) return false;
    std::array<std::int16_t, 512> first{}, second{};
    resonith_maf_operation_budget a{1000000000ULL}, b{1000000000ULL};
    if (!expect(resonith_pcell_render_model(bytes.data(), bytes.size(), first.data(),
            first.size(), &a) == RESONITH_STATUS_OK
        && resonith_pcell_render_model(bytes.data(), bytes.size(), second.data(),
            second.size(), &b) == RESONITH_STATUS_OK
        && first == second && first[0] >= 3998 && first[0] <= 4001
        && std::any_of(first.begin(), first.end(), [](auto value) { return value != 0; }),
        "deterministic nonzero render")) return false;
    std::array<std::int16_t, 512> truth{}, combined{}; truth.fill(1);
    resonith_maf_operation_budget c{10000000ULL};
    return expect(resonith_pcell_add_truth(first.data(), truth.data(), first.size(),
        combined.data(), combined.size(), &c) == RESONITH_STATUS_OK
        && combined[100] == std::min<std::int32_t>(32767, first[100] + 1),
        "native additive Truth");
}

bool test_malformed_crossfade() {
    auto bytes = stream(); put16(bytes, 96U + 12U, 81U);
    resonith_pcell_inspection inspection{};
    return expect(resonith_pcell_inspect(bytes.data(), bytes.size(), &inspection)
        == RESONITH_STATUS_MALFORMED, "reject mismatched paired fade");
}

bool test_segmented_dp() {
    std::array<resonith_pcell_control, 8> controls{};
    for (auto& control : controls) {
        control.phase_step_q32 = 1U << 26U;
        control.pulse_gain_q15 = 4000;
        control.reflection_q15[0] = -8192;
    }
    resonith_pcell_dp_weights weights{12U, 4U, 4U, 1U, 256U};
    std::array<std::uint32_t, 9> predecessor{}; std::uint64_t cost = 0U;
    return expect(resonith_pcell_segment_controls(controls.data(), controls.size(),
        &weights, predecessor.data(), predecessor.size(), &cost) == RESONITH_STATUS_OK
        && predecessor[8] == 0U && cost == 72U, "bounded DP prefers one law");
}

} // namespace

int main() {
    return test_inspect_and_render() && test_malformed_crossfade()
        && test_segmented_dp() ? 0 : 1;
}
