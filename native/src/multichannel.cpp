#include "resonith/multichannel.h"

#include "resonith/container.h"
#include "resonith/liftpack.h"
#include "resonith/stream.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::uint16_t kSchemaVersion = 1U;

struct multichannel_sections {
    resonith_container_view container{};
    resonith_container_section config{};
    resonith_container_section residuals[RESONITH_MAIN0_MAX_CHANNELS]{};
    resonith_liftpack_info residual_info[RESONITH_MAIN0_MAX_CHANNELS]{};
    resonith_stream_config stream_config{};
};

bool type_is(
    const std::uint8_t actual[4],
    const char (&expected)[5]
) noexcept {
    return std::memcmp(actual, expected, 4U) == 0;
}

std::int16_t scale_innovation(
    std::int64_t value,
    std::uint32_t step
) noexcept {
    const auto positive_limit =
        static_cast<std::int64_t>(32767) / step;
    const auto negative_limit =
        static_cast<std::int64_t>(-32768) / step;
    if (value > positive_limit) {
        return 32767;
    }
    if (value < negative_limit) {
        return -32768;
    }
    return static_cast<std::int16_t>(
        value * static_cast<std::int64_t>(step)
    );
}

resonith_status parse_multichannel(
    const std::uint8_t* data,
    std::size_t data_size,
    multichannel_sections* parsed,
    resonith_multichannel_requirements* requirements
) noexcept {
    if (parsed == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *parsed = {};
    *requirements = {};

    resonith_status status = resonith_container_open(
        data,
        data_size,
        &parsed->container
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        parsed->container.profile != 0U
        || parsed->container.level != 0U
    ) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    bool found_config = false;
    bool found_residual[RESONITH_MAIN0_MAX_CHANNELS]{};
    std::uint32_t residual_count = 0U;
    for (
        std::uint32_t index = 0U;
        index < parsed->container.section_count;
        ++index
    ) {
        resonith_container_section section{};
        status = resonith_container_get_section(
            &parsed->container,
            index,
            &section
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        const bool is_config = type_is(section.type, "CONF");
        const bool is_residual = type_is(section.type, "RSL2");
        if (!is_config && !is_residual) {
            if (
                (section.flags & RESONITH_RSC1_SECTION_CRITICAL) != 0U
            ) {
                return RESONITH_STATUS_UNSUPPORTED_FEATURE;
            }
            continue;
        }
        if (
            section.schema_version != kSchemaVersion
            || (section.flags & RESONITH_RSC1_SECTION_CRITICAL) == 0U
        ) {
            return section.schema_version != kSchemaVersion
                ? RESONITH_STATUS_UNSUPPORTED_FEATURE
                : RESONITH_STATUS_MALFORMED;
        }
        status = resonith_container_verify_section(&section);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }

        if (is_config) {
            if (
                found_config
                || section.instance_id != 0U
                || section.start_tick != 0U
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            parsed->config = section;
            found_config = true;
            continue;
        }
        if (
            section.instance_id >= RESONITH_MAIN0_MAX_CHANNELS
            || found_residual[section.instance_id]
            || section.start_tick != 0U
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        parsed->residuals[section.instance_id] = section;
        found_residual[section.instance_id] = true;
        ++residual_count;
    }
    if (!found_config || residual_count == 0U) {
        return RESONITH_STATUS_NOT_FOUND;
    }

    status = resonith_stream_config_parse(
        parsed->config.payload,
        parsed->config.payload_size,
        &parsed->stream_config
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    const std::uint16_t channels =
        parsed->stream_config.output_channels;
    if (
        channels == 0U
        || channels > RESONITH_MAIN0_MAX_CHANNELS
        || residual_count != channels
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::size_t maximum_scratch = 0U;
    std::uint16_t common_block_size = 0U;
    std::uint32_t common_block_count = 0U;
    for (std::uint16_t channel = 0U; channel < channels; ++channel) {
        if (!found_residual[channel]) {
            return RESONITH_STATUS_MALFORMED;
        }
        status = resonith_liftpack_inspect(
            parsed->residuals[channel].payload,
            parsed->residuals[channel].payload_size,
            &parsed->residual_info[channel]
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        const resonith_liftpack_info& info =
            parsed->residual_info[channel];
        if (info.sample_count != parsed->stream_config.sample_count) {
            return RESONITH_STATUS_MALFORMED;
        }
        if (channel == 0U) {
            common_block_size = info.block_size;
            common_block_count = info.block_count;
        } else if (
            info.block_size != common_block_size
            || info.block_count != common_block_count
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        maximum_scratch = std::max(
            maximum_scratch,
            resonith_liftpack_required_scratch(&info)
        );
    }

    const std::size_t frame_count =
        parsed->stream_config.sample_count;
    const std::size_t channel_count = channels;
    if (
        frame_count
            > std::numeric_limits<std::size_t>::max() / channel_count
        || static_cast<std::size_t>(common_block_size)
            > std::numeric_limits<std::size_t>::max() / channel_count
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    requirements->timebase_hz = parsed->container.timebase_hz;
    requirements->frame_count = parsed->stream_config.sample_count;
    requirements->block_count = common_block_count;
    requirements->block_size = common_block_size;
    requirements->output_channels = channels;
    requirements->innovation_elements = frame_count;
    requirements->liftpack_scratch_elements = maximum_scratch;
    requirements->output_elements = frame_count * channel_count;
    requirements->output_block_elements =
        static_cast<std::size_t>(common_block_size) * channel_count;
    return RESONITH_STATUS_OK;
}

bool view_matches(
    const resonith_multichannel_player_view& view,
    const multichannel_sections& parsed,
    const resonith_multichannel_requirements& requirements
) noexcept {
    if (
        view.stream_data == nullptr
        || view.stream_size == 0U
        || view.timebase_hz != requirements.timebase_hz
        || view.frame_count != requirements.frame_count
        || view.block_count != requirements.block_count
        || view.block_size != requirements.block_size
        || view.output_channels != requirements.output_channels
        || view.innovation_step
            != parsed.stream_config.innovation_step
        || view.liftpack_scratch_elements
            != requirements.liftpack_scratch_elements
    ) {
        return false;
    }
    for (
        std::uint16_t channel = 0U;
        channel < requirements.output_channels;
        ++channel
    ) {
        if (
            view.innovation_data[channel]
                != parsed.residuals[channel].payload
            || view.innovation_size[channel]
                != parsed.residuals[channel].payload_size
        ) {
            return false;
        }
    }
    return true;
}

}  // namespace

extern "C" resonith_status resonith_multichannel_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_multichannel_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    multichannel_sections parsed{};
    return parse_multichannel(data, data_size, &parsed, requirements);
}

extern "C" resonith_status resonith_multichannel_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::int64_t* innovation_q,
    std::size_t innovation_capacity,
    std::int64_t* liftpack_scratch,
    std::size_t liftpack_scratch_capacity,
    std::int16_t* interleaved_output,
    std::size_t output_capacity,
    std::size_t* frames_written
) {
    if (frames_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_written = 0U;
    if (
        innovation_q == nullptr
        || liftpack_scratch == nullptr
        || interleaved_output == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    multichannel_sections parsed{};
    resonith_multichannel_requirements requirements{};
    resonith_status status = parse_multichannel(
        data,
        data_size,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (innovation_capacity < requirements.innovation_elements) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    if (
        liftpack_scratch_capacity
            < requirements.liftpack_scratch_elements
    ) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    if (output_capacity < requirements.output_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    /*
     * Preflight all entropy paths before the first PCM write. This second pass
     * is intentional: it preserves atomic whole-decode output while retaining
     * one channel-sized workspace.
     */
    for (
        std::uint16_t channel = 0U;
        channel < requirements.output_channels;
        ++channel
    ) {
        std::size_t decoded = 0U;
        status = resonith_liftpack_decode(
            parsed.residuals[channel].payload,
            parsed.residuals[channel].payload_size,
            innovation_q,
            innovation_capacity,
            liftpack_scratch,
            liftpack_scratch_capacity,
            &decoded
        );
        if (
            status != RESONITH_STATUS_OK
            || decoded != requirements.frame_count
        ) {
            return status == RESONITH_STATUS_OK
                ? RESONITH_STATUS_MALFORMED
                : status;
        }
    }

    for (
        std::uint16_t channel = 0U;
        channel < requirements.output_channels;
        ++channel
    ) {
        std::size_t decoded = 0U;
        status = resonith_liftpack_decode(
            parsed.residuals[channel].payload,
            parsed.residuals[channel].payload_size,
            innovation_q,
            innovation_capacity,
            liftpack_scratch,
            liftpack_scratch_capacity,
            &decoded
        );
        if (
            status != RESONITH_STATUS_OK
            || decoded != requirements.frame_count
        ) {
            return status == RESONITH_STATUS_OK
                ? RESONITH_STATUS_MALFORMED
                : status;
        }
        for (
            std::size_t frame = 0U;
            frame < requirements.frame_count;
            ++frame
        ) {
            const std::size_t output_index =
                frame * requirements.output_channels + channel;
            interleaved_output[output_index] = scale_innovation(
                innovation_q[frame],
                parsed.stream_config.innovation_step
            );
        }
    }
    *frames_written = requirements.frame_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_multichannel_player_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_multichannel_player_view* view
) {
    if (view == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    multichannel_sections parsed{};
    resonith_multichannel_requirements requirements{};
    const resonith_status status = parse_multichannel(
        data,
        data_size,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    for (
        std::uint16_t channel = 0U;
        channel < requirements.output_channels;
        ++channel
    ) {
        view->innovation_data[channel] =
            parsed.residuals[channel].payload;
        view->innovation_size[channel] =
            parsed.residuals[channel].payload_size;
    }
    view->stream_data = data;
    view->stream_size = data_size;
    view->timebase_hz = requirements.timebase_hz;
    view->frame_count = requirements.frame_count;
    view->block_count = requirements.block_count;
    view->block_size = requirements.block_size;
    view->output_channels = requirements.output_channels;
    view->innovation_step = parsed.stream_config.innovation_step;
    view->liftpack_scratch_elements =
        requirements.liftpack_scratch_elements;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_multichannel_player_stream(
    const resonith_multichannel_player_view* view,
    std::int64_t* innovation_q,
    std::size_t innovation_capacity,
    std::int64_t* liftpack_scratch,
    std::size_t liftpack_scratch_capacity,
    std::int16_t* interleaved_output,
    std::size_t output_capacity,
    resonith_pcm16_interleaved_callback callback,
    void* user,
    std::size_t* frames_emitted
) {
    if (frames_emitted == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *frames_emitted = 0U;
    if (
        view == nullptr
        || innovation_q == nullptr
        || liftpack_scratch == nullptr
        || interleaved_output == nullptr
        || callback == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    multichannel_sections parsed{};
    resonith_multichannel_requirements requirements{};
    resonith_status status = parse_multichannel(
        view->stream_data,
        view->stream_size,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (!view_matches(*view, parsed, requirements)) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        innovation_capacity < requirements.block_size
        || liftpack_scratch_capacity
            < requirements.liftpack_scratch_elements
    ) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    if (output_capacity < requirements.output_block_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    resonith_liftpack_cursor
        cursors[RESONITH_MAIN0_MAX_CHANNELS]{};
    for (
        std::uint16_t channel = 0U;
        channel < requirements.output_channels;
        ++channel
    ) {
        status = resonith_liftpack_cursor_open(
            parsed.residuals[channel].payload,
            parsed.residuals[channel].payload_size,
            &cursors[channel]
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
    }

    for (
        std::uint32_t block = 0U;
        block < requirements.block_count;
        ++block
    ) {
        std::uint32_t common_offset = 0U;
        std::size_t common_frames = 0U;
        for (
            std::uint16_t channel = 0U;
            channel < requirements.output_channels;
            ++channel
        ) {
            std::uint32_t frame_offset = 0U;
            std::size_t block_frames = 0U;
            status = resonith_liftpack_cursor_decode_next(
                &cursors[channel],
                innovation_q,
                innovation_capacity,
                liftpack_scratch,
                liftpack_scratch_capacity,
                &frame_offset,
                &block_frames
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            if (channel == 0U) {
                common_offset = frame_offset;
                common_frames = block_frames;
            } else if (
                frame_offset != common_offset
                || block_frames != common_frames
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            for (std::size_t frame = 0U; frame < block_frames; ++frame) {
                const std::size_t output_index =
                    frame * requirements.output_channels + channel;
                interleaved_output[output_index] = scale_innovation(
                    innovation_q[frame],
                    parsed.stream_config.innovation_step
                );
            }
        }
        status = callback(
            user,
            common_offset,
            interleaved_output,
            common_frames,
            requirements.output_channels
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        *frames_emitted += common_frames;
    }
    return *frames_emitted == requirements.frame_count
        ? RESONITH_STATUS_OK
        : RESONITH_STATUS_MALFORMED;
}
