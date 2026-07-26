#include "resonith/stream.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

constexpr std::array<std::uint8_t, 263> kZeroAtomStream = {
    0x52, 0x53, 0x43, 0x31, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x80, 0xbb, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x00,
    0xa0, 0x00, 0x00, 0x00, 0x0e, 0x39, 0x28, 0xac, 0x43, 0x4f, 0x4e, 0x46,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x46, 0xe2, 0xb0, 0x40, 0x24, 0xac, 0xc5, 0x04,
    0x94, 0x0b, 0x62, 0xff, 0x18, 0x10, 0xdf, 0xb0, 0x51, 0x76, 0x48, 0x53,
    0x1f, 0x53, 0x04, 0xf1, 0xec, 0x94, 0x3d, 0x4e, 0x28, 0x39, 0xfa, 0x91,
    0x87, 0xb8, 0x0b, 0x6b, 0x52, 0x53, 0x4c, 0x32, 0x01, 0x00, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xd0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x37, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x37, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x1c, 0xdf, 0x44, 0x21, 0x44, 0x19, 0xcc, 0xd5, 0xa6, 0xe7, 0x51, 0xff,
    0xa3, 0x25, 0xc4, 0x31, 0xc8, 0xa3, 0x51, 0xe8, 0x6e, 0x0c, 0xa2, 0x67,
    0x34, 0xf7, 0x15, 0xf4, 0x58, 0xa9, 0x65, 0xda, 0x98, 0x05, 0xa6, 0x7b,
    0x20, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x52, 0x53, 0x4c, 0x32, 0x01, 0x10, 0x00, 0x20,
    0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x10, 0x00, 0x02, 0x00, 0x00,
    0x12, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x10, 0x00, 0x01, 0x00, 0x05,
    0x75, 0x00, 0x00, 0x00, 0x3f, 0x64, 0x9a, 0xa6, 0x69, 0x9a, 0xe6, 0xbf,
    0x11, 0x0a, 0x85, 0x42, 0xa1, 0x50, 0x08, 0x90, 0x8c, 0x8a, 0x46,
};

constexpr std::array<std::int16_t, 16> kSecondBlockPcm = {
    300, 270, 240, 210, 180, 150, 120, 90,
    -300, -240, -180, -120, -60, 0, 60, 120,
};

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

struct CallbackState {
    std::array<std::int16_t, 32> samples{};
    std::size_t cursor = 0U;
    std::uint32_t calls = 0U;
};

resonith_status collect_pcm(
    void* user,
    std::uint32_t sample_offset,
    const std::int16_t* samples,
    std::size_t sample_count
) {
    auto* state = static_cast<CallbackState*>(user);
    if (
        state == nullptr
        || samples == nullptr
        || sample_offset != state->cursor
        || state->cursor > state->samples.size()
        || sample_count > state->samples.size() - state->cursor
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    std::copy(
        samples,
        samples + sample_count,
        state->samples.begin() + static_cast<std::ptrdiff_t>(state->cursor)
    );
    state->cursor += sample_count;
    ++state->calls;
    return RESONITH_STATUS_OK;
}

}  // namespace

int main() {
    resonith_main0_player_view player{};
    if (!expect(
            resonith_main0_player_open(
                kZeroAtomStream.data(),
                kZeroAtomStream.size(),
                &player
            ) == RESONITH_STATUS_OK
                && player.timebase_hz == 48000U
                && player.sample_count == 32U
                && player.innovation_step == 3U
                && player.block_size == 16U
                && player.block_count == 2U
                && player.atom_count == 0U
                && player.output_channels == 1U,
            "open zero-Atom block player"
        )) {
        return 1;
    }

    std::array<std::int64_t, 16> innovation{};
    std::array<std::int64_t, 32> scratch{};
    std::array<std::int16_t, 16> output{};
    std::uint32_t sample_offset = 99U;
    std::size_t samples_written = 99U;
    if (!expect(
            resonith_main0_player_decode_block(
                &player,
                1U,
                innovation.data(),
                innovation.size(),
                scratch.data(),
                scratch.size(),
                output.data(),
                output.size(),
                &sample_offset,
                &samples_written
            ) == RESONITH_STATUS_OK
                && sample_offset == 16U
                && samples_written == output.size()
                && output == kSecondBlockPcm,
            "seek and decode exact second block"
        )) {
        return 1;
    }

    CallbackState callback_state{};
    std::size_t samples_emitted = 99U;
    if (!expect(
            resonith_main0_player_stream(
                &player,
                innovation.data(),
                innovation.size(),
                scratch.data(),
                scratch.size(),
                output.data(),
                output.size(),
                collect_pcm,
                &callback_state,
                &samples_emitted
            ) == RESONITH_STATUS_OK
                && samples_emitted == callback_state.samples.size()
                && callback_state.cursor == callback_state.samples.size()
                && callback_state.calls == 2U
                && std::equal(
                    callback_state.samples.begin() + 16,
                    callback_state.samples.end(),
                    kSecondBlockPcm.begin()
                ),
            "linear callback player emits exact blocks"
        )) {
        return 1;
    }

    output.fill(1234);
    sample_offset = 99U;
    samples_written = 99U;
    if (!expect(
            resonith_main0_player_decode_block(
                &player,
                2U,
                innovation.data(),
                innovation.size(),
                scratch.data(),
                scratch.size(),
                output.data(),
                output.size(),
                &sample_offset,
                &samples_written
            ) == RESONITH_STATUS_NOT_FOUND
                && sample_offset == 0U
                && samples_written == 0U
                && std::all_of(
                    output.begin(),
                    output.end(),
                    [](std::int16_t value) { return value == 1234; }
                ),
            "failed seek leaves PCM untouched"
        )) {
        return 1;
    }

    auto damaged = kZeroAtomStream;
    damaged.back() ^= 1U;
    player.sample_count = 99U;
    if (!expect(
            resonith_main0_player_open(
                damaged.data(),
                damaged.size(),
                &player
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH
                && player.sample_count == 0U
                && player.innovation_data == nullptr,
            "failed player open zeroes view"
        )) {
        return 1;
    }
    return 0;
}
