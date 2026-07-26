#include "resonith/stream.h"

#include "resonith/basis.h"
#include "resonith/composition.h"
#include "resonith/container.h"
#include "resonith/liftpack.h"
#include "resonith/trajectory.h"

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

constexpr std::size_t kConfigBytes = 16U;
constexpr std::size_t kAtomHeaderBytes = 24U;
constexpr std::size_t kAtomRecordBytes = 8U;
constexpr std::uint32_t kMaximumRecords = 1'000'000U;
constexpr std::uint32_t kMaximumSampleCount = 0x7fff'ffffU;
constexpr std::uint32_t kMaximumInnovationStep = 1U << 20U;
constexpr std::uint16_t kMaximumChannels = 8U;
constexpr std::uint32_t kMaximumKnotSpan = 32768U;
constexpr std::int32_t kMinimumGain = -131072;
constexpr std::int32_t kMaximumGain = 131071;
constexpr std::uint16_t kSchemaVersion = 1U;

struct main0_sections {
    resonith_container_view view{};
    resonith_container_section atom{};
    resonith_container_section basis{};
    resonith_container_section config{};
    resonith_container_section innovation{};
    resonith_stream_config stream_config{};
    resonith_periodic_atom_info atom_info{};
    resonith_raw_basis_info basis_info{};
    resonith_liftpack_info innovation_info{};
};

std::uint16_t read_u16(const std::uint8_t* data) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data[0])
        | (static_cast<std::uint16_t>(data[1]) << 8U)
    );
}

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(data[0])
        | (static_cast<std::uint32_t>(data[1]) << 8U)
        | (static_cast<std::uint32_t>(data[2]) << 16U)
        | (static_cast<std::uint32_t>(data[3]) << 24U);
}

std::int32_t read_i32(const std::uint8_t* data) noexcept {
    const std::uint32_t raw = read_u32(data);
    if (raw <= 0x7fff'ffffU) {
        return static_cast<std::int32_t>(raw);
    }
    return -1 - static_cast<std::int32_t>(~raw);
}

bool type_is(
    const std::uint8_t actual[4],
    const char (&expected)[5]
) noexcept {
    return std::memcmp(actual, expected, 4U) == 0;
}

bool known_type(const std::uint8_t type[4]) noexcept {
    return type_is(type, "ATOM")
        || type_is(type, "BRAW")
        || type_is(type, "CONF")
        || type_is(type, "RSL1");
}

resonith_status validate_atom_records(
    const std::uint8_t* data,
    const resonith_periodic_atom_info& info
) noexcept {
    const std::uint8_t* phase = data + kAtomHeaderBytes;
    std::uint32_t previous = 0U;
    for (std::uint32_t index = 0; index < info.phase_knot_count; ++index) {
        const std::size_t offset =
            static_cast<std::size_t>(index) * kAtomRecordBytes;
        const std::uint32_t position = read_u32(phase + offset);
        if (
            (index == 0U && position != 0U)
            || (index != 0U
                && (position <= previous
                    || position - previous > kMaximumKnotSpan))
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        previous = position;
    }
    if (previous != info.duration_samples) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::uint8_t* gains = phase
        + static_cast<std::size_t>(info.phase_knot_count)
            * kAtomRecordBytes;
    previous = 0U;
    for (std::uint32_t index = 0; index < info.gain_event_count; ++index) {
        const std::size_t offset =
            static_cast<std::size_t>(index) * kAtomRecordBytes;
        const std::uint32_t position = read_u32(gains + offset);
        const std::int32_t gain = read_i32(gains + offset + 4U);
        if (
            (index == 0U && position != 0U)
            || (index != 0U && position <= previous)
            || position >= info.duration_samples
            || gain < kMinimumGain
            || gain > kMaximumGain
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        previous = position;
    }
    return RESONITH_STATUS_OK;
}

resonith_status parse_main0(
    const std::uint8_t* data,
    std::size_t data_size,
    main0_sections* parsed,
    resonith_main0_requirements* requirements
) {
    if (parsed == nullptr || requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *parsed = {};
    *requirements = {};
    resonith_status status = resonith_container_open(
        data,
        data_size,
        &parsed->view
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (parsed->view.profile != 0U || parsed->view.level != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    bool found_atom = false;
    bool found_basis = false;
    bool found_config = false;
    bool found_innovation = false;
    for (
        std::uint32_t index = 0;
        index < parsed->view.section_count;
        ++index
    ) {
        resonith_container_section section{};
        status = resonith_container_get_section(
            &parsed->view,
            index,
            &section
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (!known_type(section.type)) {
            if (
                (section.flags & RESONITH_RSC1_SECTION_CRITICAL) != 0U
            ) {
                return RESONITH_STATUS_UNSUPPORTED_FEATURE;
            }
            continue;
        }
        if (
            section.instance_id != 0U
            || section.schema_version != kSchemaVersion
            || section.start_tick != 0U
        ) {
            return RESONITH_STATUS_UNSUPPORTED_FEATURE;
        }
        if (
            (section.flags & RESONITH_RSC1_SECTION_CRITICAL) == 0U
        ) {
            return RESONITH_STATUS_MALFORMED;
        }
        status = resonith_container_verify_section(&section);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }

        if (type_is(section.type, "ATOM")) {
            parsed->atom = section;
            found_atom = true;
        } else if (type_is(section.type, "BRAW")) {
            parsed->basis = section;
            found_basis = true;
        } else if (type_is(section.type, "CONF")) {
            parsed->config = section;
            found_config = true;
        } else {
            parsed->innovation = section;
            found_innovation = true;
        }
    }
    if (
        !found_atom
        || !found_basis
        || !found_config
        || !found_innovation
    ) {
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
    status = resonith_periodic_atom_inspect(
        parsed->atom.payload,
        parsed->atom.payload_size,
        &parsed->atom_info
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_raw_basis_inspect(
        parsed->basis.payload,
        parsed->basis.payload_size,
        &parsed->basis_info
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_liftpack_inspect(
        parsed->innovation.payload,
        parsed->innovation.payload_size,
        &parsed->innovation_info
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        parsed->stream_config.output_channels != 1U
        || parsed->basis_info.channels != 1U
    ) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (
        parsed->basis_info.samples_per_channel < 2U
        || parsed->atom_info.basis_instance_id
            != parsed->basis.instance_id
        || parsed->atom_info.duration_samples
            != parsed->stream_config.sample_count
        || parsed->innovation_info.sample_count
            != parsed->stream_config.sample_count
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    requirements->timebase_hz = parsed->view.timebase_hz;
    requirements->sample_count = parsed->stream_config.sample_count;
    requirements->basis_elements = parsed->basis_info.total_elements;
    requirements->phase_knot_count = parsed->atom_info.phase_knot_count;
    requirements->gain_event_count = parsed->atom_info.gain_event_count;
    requirements->liftpack_scratch_elements =
        resonith_liftpack_required_scratch(&parsed->innovation_info);
    requirements->output_channels =
        parsed->stream_config.output_channels;
    requirements->reserved = 0U;
    return RESONITH_STATUS_OK;
}

bool workspace_present(
    const resonith_main0_workspace& workspace
) noexcept {
    return workspace.basis != nullptr
        && workspace.phase_positions != nullptr
        && workspace.phase_increments_q32 != nullptr
        && workspace.phase_origins_q32 != nullptr
        && workspace.gain_positions != nullptr
        && workspace.gains_q15 != nullptr
        && workspace.unity_prediction != nullptr
        && workspace.innovation_q != nullptr
        && workspace.liftpack_scratch != nullptr;
}

bool workspace_large_enough(
    const resonith_main0_workspace& workspace,
    const resonith_main0_requirements& requirements
) noexcept {
    return workspace.basis_capacity >= requirements.basis_elements
        && workspace.phase_capacity >= requirements.phase_knot_count
        && workspace.gain_capacity >= requirements.gain_event_count
        && workspace.unity_capacity >= requirements.sample_count
        && workspace.innovation_capacity >= requirements.sample_count
        && workspace.liftpack_scratch_capacity
            >= requirements.liftpack_scratch_elements;
}

}  // namespace

extern "C" resonith_status resonith_stream_config_parse(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_stream_config* config
) {
    if (data == nullptr || config == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *config = {};
    if (data_size != kConfigBytes) {
        return data_size < kConfigBytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t sample_count = read_u32(data);
    const std::uint32_t innovation_step = read_u32(data + 4U);
    const std::uint16_t output_channels = read_u16(data + 8U);
    const std::uint16_t flags = read_u16(data + 10U);
    const std::uint32_t reserved = read_u32(data + 12U);
    if (flags != 0U || reserved != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (
        sample_count == 0U
        || sample_count > kMaximumSampleCount
        || innovation_step == 0U
        || innovation_step > kMaximumInnovationStep
        || output_channels == 0U
        || output_channels > kMaximumChannels
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    config->sample_count = sample_count;
    config->innovation_step = innovation_step;
    config->output_channels = output_channels;
    config->reserved = 0U;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_periodic_atom_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_periodic_atom_info* info
) {
    if (data == nullptr || info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *info = {};
    if (data_size < kAtomHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }
    resonith_periodic_atom_info candidate{};
    candidate.basis_instance_id = read_u32(data);
    candidate.duration_samples = read_u32(data + 4U);
    candidate.phase_origin_q32 = read_u32(data + 8U);
    candidate.phase_knot_count = read_u32(data + 12U);
    candidate.gain_event_count = read_u32(data + 16U);
    const std::uint32_t flags = read_u32(data + 20U);
    if (flags != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (
        candidate.duration_samples == 0U
        || candidate.duration_samples > kMaximumSampleCount
        || candidate.phase_knot_count < 2U
        || candidate.phase_knot_count > kMaximumRecords
        || candidate.gain_event_count == 0U
        || candidate.gain_event_count > kMaximumRecords
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::size_t record_count =
        static_cast<std::size_t>(candidate.phase_knot_count)
        + candidate.gain_event_count;
    const std::size_t expected_bytes =
        kAtomHeaderBytes + record_count * kAtomRecordBytes;
    if (data_size != expected_bytes) {
        return data_size < expected_bytes
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    const resonith_status validation =
        validate_atom_records(data, candidate);
    if (validation != RESONITH_STATUS_OK) {
        return validation;
    }
    *info = candidate;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_periodic_atom_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    std::uint32_t* phase_positions,
    std::uint32_t* phase_increments_q32,
    std::size_t phase_capacity,
    std::uint32_t* gain_positions,
    std::int32_t* gains_q15,
    std::size_t gain_capacity,
    resonith_periodic_atom_info* info
) {
    if (info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    resonith_periodic_atom_info candidate{};
    const resonith_status status = resonith_periodic_atom_inspect(
        data,
        data_size,
        &candidate
    );
    if (status != RESONITH_STATUS_OK) {
        *info = {};
        return status;
    }
    if (
        phase_positions == nullptr
        || phase_increments_q32 == nullptr
        || gain_positions == nullptr
        || gains_q15 == nullptr
    ) {
        *info = {};
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        phase_capacity < candidate.phase_knot_count
        || gain_capacity < candidate.gain_event_count
    ) {
        *info = {};
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }

    const std::uint8_t* phase = data + kAtomHeaderBytes;
    for (
        std::uint32_t index = 0;
        index < candidate.phase_knot_count;
        ++index
    ) {
        const std::size_t offset =
            static_cast<std::size_t>(index) * kAtomRecordBytes;
        phase_positions[index] = read_u32(phase + offset);
        phase_increments_q32[index] = read_u32(phase + offset + 4U);
    }
    const std::uint8_t* gains = phase
        + static_cast<std::size_t>(candidate.phase_knot_count)
            * kAtomRecordBytes;
    for (
        std::uint32_t index = 0;
        index < candidate.gain_event_count;
        ++index
    ) {
        const std::size_t offset =
            static_cast<std::size_t>(index) * kAtomRecordBytes;
        gain_positions[index] = read_u32(gains + offset);
        gains_q15[index] = read_i32(gains + offset + 4U);
    }
    *info = candidate;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_main0_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_main0_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    main0_sections parsed{};
    return parse_main0(data, data_size, &parsed, requirements);
}

extern "C" resonith_status resonith_main0_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_main0_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* samples_written
) {
    if (samples_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *samples_written = 0U;
    if (workspace == nullptr || output == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    main0_sections parsed{};
    resonith_main0_requirements requirements{};
    resonith_status status = parse_main0(
        data,
        data_size,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (output_capacity < requirements.sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (!workspace_present(*workspace)) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!workspace_large_enough(*workspace, requirements)) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    std::size_t basis_written = 0U;
    status = resonith_raw_basis_decode(
        parsed.basis.payload,
        parsed.basis.payload_size,
        workspace->basis,
        workspace->basis_capacity,
        &basis_written
    );
    if (
        status != RESONITH_STATUS_OK
        || basis_written != requirements.basis_elements
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }
    resonith_periodic_atom_info atom{};
    status = resonith_periodic_atom_decode(
        parsed.atom.payload,
        parsed.atom.payload_size,
        workspace->phase_positions,
        workspace->phase_increments_q32,
        workspace->phase_capacity,
        workspace->gain_positions,
        workspace->gains_q15,
        workspace->gain_capacity,
        &atom
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    const resonith_phase_trajectory phase_source = {
        workspace->phase_positions,
        workspace->phase_increments_q32,
        atom.phase_knot_count,
        atom.phase_origin_q32,
    };
    resonith_prepared_phase_trajectory phase{};
    status = resonith_phase_prepare(
        &phase_source,
        workspace->phase_origins_q32,
        workspace->phase_capacity,
        &phase
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_periodic_render(
        workspace->basis,
        basis_written,
        &phase,
        0U,
        requirements.sample_count,
        workspace->unity_prediction,
        workspace->unity_capacity
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    std::size_t innovation_written = 0U;
    status = resonith_liftpack_decode(
        parsed.innovation.payload,
        parsed.innovation.payload_size,
        workspace->innovation_q,
        workspace->innovation_capacity,
        workspace->liftpack_scratch,
        workspace->liftpack_scratch_capacity,
        &innovation_written
    );
    if (
        status != RESONITH_STATUS_OK
        || innovation_written != requirements.sample_count
    ) {
        return status == RESONITH_STATUS_OK
            ? RESONITH_STATUS_MALFORMED
            : status;
    }

    const resonith_gain_event_law gain_source = {
        workspace->gain_positions,
        workspace->gains_q15,
        atom.gain_event_count,
        atom.duration_samples,
    };
    resonith_prepared_gain_law gain{};
    status = resonith_gain_prepare(&gain_source, &gain);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    status = resonith_compose_truth(
        workspace->unity_prediction,
        workspace->innovation_q,
        parsed.stream_config.innovation_step,
        &gain,
        0U,
        requirements.sample_count,
        output,
        output_capacity
    );
    if (status == RESONITH_STATUS_OK) {
        *samples_written = requirements.sample_count;
    }
    return status;
}
