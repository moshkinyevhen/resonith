#include "resonith/stream.h"

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

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
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
    return 0;
}
