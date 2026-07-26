#include "resonith/stream.h"
#include "resonith/multichannel.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

constexpr std::uint32_t kFuzzMaximumSamples = 1U << 16U;
constexpr std::uint32_t kFuzzMaximumRecords = 1U << 10U;
constexpr std::size_t kFuzzMaximumWorkspaceElements = 1U << 18U;

bool requirements_are_bounded(
    const resonith_main0_requirements& requirements
) noexcept {
    return requirements.sample_count <= kFuzzMaximumSamples
        && requirements.atom_count <= kFuzzMaximumRecords
        && requirements.basis_count <= kFuzzMaximumRecords
        && requirements.basis_elements <= kFuzzMaximumWorkspaceElements
        && requirements.phase_knot_count <= kFuzzMaximumWorkspaceElements
        && requirements.gain_event_count <= kFuzzMaximumWorkspaceElements
        && requirements.render_elements <= kFuzzMaximumWorkspaceElements
        && requirements.liftpack_scratch_elements
            <= kFuzzMaximumWorkspaceElements;
}

template <typename T>
T* optional_data(std::vector<T>& values) noexcept {
    return values.empty() ? nullptr : values.data();
}

struct CallbackOracle {
    const std::vector<std::int16_t>* expected;
    std::size_t cursor;
};

struct InterleavedCallbackOracle {
    const std::vector<std::int16_t>* expected;
    std::size_t frame_cursor;
    std::uint16_t channels;
};

resonith_status compare_callback(
    void* user,
    std::uint32_t sample_offset,
    const std::int16_t* samples,
    std::size_t sample_count
) {
    auto* oracle = static_cast<CallbackOracle*>(user);
    if (
        oracle == nullptr
        || oracle->expected == nullptr
        || samples == nullptr
        || sample_offset != oracle->cursor
        || oracle->cursor > oracle->expected->size()
        || sample_count > oracle->expected->size() - oracle->cursor
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    for (std::size_t index = 0U; index < sample_count; ++index) {
        if (samples[index] != (*oracle->expected)[oracle->cursor + index]) {
            return RESONITH_STATUS_MALFORMED;
        }
    }
    oracle->cursor += sample_count;
    return RESONITH_STATUS_OK;
}

resonith_status compare_interleaved_callback(
    void* user,
    std::uint32_t frame_offset,
    const std::int16_t* samples,
    std::size_t frame_count,
    std::uint16_t channels
) {
    auto* oracle = static_cast<InterleavedCallbackOracle*>(user);
    if (
        oracle == nullptr
        || oracle->expected == nullptr
        || samples == nullptr
        || channels != oracle->channels
        || frame_offset != oracle->frame_cursor
        || oracle->frame_cursor > oracle->expected->size() / channels
        || frame_count
            > (oracle->expected->size() / channels) - oracle->frame_cursor
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::size_t sample_offset = oracle->frame_cursor * channels;
    const std::size_t sample_count = frame_count * channels;
    for (std::size_t index = 0U; index < sample_count; ++index) {
        if (samples[index] != (*oracle->expected)[sample_offset + index]) {
            return RESONITH_STATUS_MALFORMED;
        }
    }
    oracle->frame_cursor += frame_count;
    return RESONITH_STATUS_OK;
}

void fuzz_multichannel(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_multichannel_requirements requirements{};
    if (
        resonith_multichannel_inspect(data, size, &requirements)
            != RESONITH_STATUS_OK
        || requirements.frame_count > kFuzzMaximumSamples
        || requirements.innovation_elements > kFuzzMaximumWorkspaceElements
        || requirements.liftpack_scratch_elements
            > kFuzzMaximumWorkspaceElements
        || requirements.output_elements > kFuzzMaximumWorkspaceElements
        || requirements.output_block_elements > kFuzzMaximumWorkspaceElements
    ) {
        return;
    }

    std::vector<std::int64_t> innovation(
        requirements.innovation_elements
    );
    std::vector<std::int64_t> scratch(
        requirements.liftpack_scratch_elements
    );
    std::vector<std::int16_t> output(requirements.output_elements);
    std::size_t frames_written = 0U;
    const resonith_status decode_status = resonith_multichannel_decode(
        data,
        size,
        optional_data(innovation),
        innovation.size(),
        optional_data(scratch),
        scratch.size(),
        optional_data(output),
        output.size(),
        &frames_written
    );
    if (decode_status != RESONITH_STATUS_OK) {
        return;
    }
    if (frames_written != requirements.frame_count) {
        __builtin_trap();
    }

    resonith_multichannel_player_view player{};
    if (
        resonith_multichannel_player_open(data, size, &player)
            != RESONITH_STATUS_OK
        || player.frame_count != requirements.frame_count
        || player.output_channels != requirements.output_channels
    ) {
        __builtin_trap();
    }
    std::vector<std::int64_t> block_innovation(
        requirements.block_size
    );
    std::vector<std::int16_t> block_output(
        requirements.output_block_elements
    );
    InterleavedCallbackOracle oracle = {
        &output,
        0U,
        requirements.output_channels,
    };
    std::size_t frames_emitted = 0U;
    if (
        resonith_multichannel_player_stream(
            &player,
            optional_data(block_innovation),
            block_innovation.size(),
            optional_data(scratch),
            scratch.size(),
            optional_data(block_output),
            block_output.size(),
            compare_interleaved_callback,
            &oracle,
            &frames_emitted
        ) != RESONITH_STATUS_OK
        || frames_emitted != requirements.frame_count
        || oracle.frame_cursor != requirements.frame_count
    ) {
        __builtin_trap();
    }
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    fuzz_multichannel(data, size);

    resonith_main0_requirements requirements{};
    if (
        resonith_main0_inspect(data, size, &requirements)
            != RESONITH_STATUS_OK
        || !requirements_are_bounded(requirements)
    ) {
        return 0;
    }

    std::vector<std::int16_t> basis(requirements.basis_elements);
    std::vector<std::uint32_t> phase_positions(
        requirements.phase_knot_count
    );
    std::vector<std::uint32_t> phase_increments(
        requirements.phase_knot_count
    );
    std::vector<std::uint32_t> phase_origins(
        requirements.phase_knot_count
    );
    std::vector<std::uint32_t> gain_positions(
        requirements.gain_event_count
    );
    std::vector<std::int32_t> gains(requirements.gain_event_count);
    std::vector<std::int16_t> prediction(requirements.render_elements);
    std::vector<std::int64_t> innovation(requirements.sample_count);
    std::vector<std::int64_t> scratch(
        requirements.liftpack_scratch_elements
    );
    std::vector<std::int16_t> output(requirements.sample_count);
    resonith_main0_workspace workspace = {
        optional_data(basis),
        basis.size(),
        optional_data(phase_positions),
        optional_data(phase_increments),
        optional_data(phase_origins),
        phase_positions.size(),
        optional_data(gain_positions),
        optional_data(gains),
        gain_positions.size(),
        optional_data(prediction),
        prediction.size(),
        optional_data(innovation),
        innovation.size(),
        optional_data(scratch),
        scratch.size(),
    };
    std::size_t samples_written = 0U;
    const resonith_status decode_status = resonith_main0_decode(
        data,
        size,
        &workspace,
        optional_data(output),
        output.size(),
        &samples_written
    );
    if (
        decode_status == RESONITH_STATUS_OK
        && samples_written != requirements.sample_count
    ) {
        __builtin_trap();
    }

    resonith_main0_player_view player{};
    const resonith_status player_status = resonith_main0_player_open(
        data,
        size,
        &player
    );
    if (
        player_status != RESONITH_STATUS_OK
        || player.sample_count != requirements.sample_count
        || player.atom_count != requirements.atom_count
    ) {
        __builtin_trap();
    }
    if (
        decode_status == RESONITH_STATUS_OK
        && player.atom_count == 0U
        && player.block_count != 0U
    ) {
        std::vector<std::int64_t> block_innovation(player.block_size);
        std::vector<std::int16_t> block_output(player.block_size);
        std::uint32_t sample_offset = 0U;
        std::size_t block_samples = 0U;
        const std::uint32_t block_index = player.block_count - 1U;
        const resonith_status block_status =
            resonith_main0_player_decode_block(
                &player,
                block_index,
                block_innovation.data(),
                block_innovation.size(),
                scratch.data(),
                scratch.size(),
                block_output.data(),
                block_output.size(),
                &sample_offset,
                &block_samples
            );
        if (
            block_status != RESONITH_STATUS_OK
            || sample_offset + block_samples != requirements.sample_count
        ) {
            __builtin_trap();
        }
        for (std::size_t index = 0U; index < block_samples; ++index) {
            if (block_output[index] != output[sample_offset + index]) {
                __builtin_trap();
            }
        }
        CallbackOracle oracle = {&output, 0U};
        std::size_t samples_emitted = 0U;
        if (
            resonith_main0_player_stream(
                &player,
                block_innovation.data(),
                block_innovation.size(),
                scratch.data(),
                scratch.size(),
                block_output.data(),
                block_output.size(),
                compare_callback,
                &oracle,
                &samples_emitted
            ) != RESONITH_STATUS_OK
            || samples_emitted != output.size()
            || oracle.cursor != output.size()
        ) {
            __builtin_trap();
        }
    }
    if (
        decode_status == RESONITH_STATUS_OK
        && player.block_count != 0U
    ) {
        std::vector<std::int16_t> block_output(player.block_size);
        CallbackOracle oracle = {&output, 0U};
        std::size_t samples_emitted = 0U;
        if (
            resonith_main0_player_stream_complete(
                &player,
                &workspace,
                block_output.data(),
                block_output.size(),
                compare_callback,
                &oracle,
                &samples_emitted
            ) != RESONITH_STATUS_OK
            || samples_emitted != output.size()
            || oracle.cursor != output.size()
        ) {
            __builtin_trap();
        }
    }
    return 0;
}
