#include "resonith/stream.h"

#include "resonith/basis.h"
#include "resonith/composition.h"
#include "resonith/container.h"
#include "resonith/liftpack.h"
#include "resonith/maf.h"
#include "resonith/trajectory.h"

#include <algorithm>
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
    resonith_container_section config{};
    resonith_container_section innovation{};
    resonith_stream_config stream_config{};
    resonith_liftpack_info innovation_info{};
};

constexpr std::uint8_t kAtomType[4] = {'A', 'T', 'O', 'M'};
constexpr std::uint8_t kRawBasisType[4] = {'B', 'R', 'A', 'W'};
constexpr std::uint8_t kCibsBasisType[4] = {'B', 'C', 'I', 'B'};

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

bool type_is(
    const std::uint8_t actual[4],
    const char (&expected)[5]
) noexcept {
    return std::memcmp(actual, expected, 4U) == 0;
}

bool known_type(const std::uint8_t type[4]) noexcept {
    return type_is(type, "ATOM")
        || type_is(type, "BCIB")
        || type_is(type, "BRAW")
        || type_is(type, "CONF")
        || type_is(type, "RSL1")
        || type_is(type, "RSL2");
}

resonith_status find_basis_section(
    const resonith_container_view& view,
    std::uint32_t basis_id,
    resonith_container_section& section,
    bool& is_cibs
) noexcept {
    resonith_container_section raw{};
    resonith_container_section cibs{};
    const resonith_status raw_status = resonith_container_find_section(
        &view,
        kRawBasisType,
        basis_id,
        &raw
    );
    const resonith_status cibs_status = resonith_container_find_section(
        &view,
        kCibsBasisType,
        basis_id,
        &cibs
    );
    if (
        raw_status != RESONITH_STATUS_OK
        && raw_status != RESONITH_STATUS_NOT_FOUND
    ) {
        return raw_status;
    }
    if (
        cibs_status != RESONITH_STATUS_OK
        && cibs_status != RESONITH_STATUS_NOT_FOUND
    ) {
        return cibs_status;
    }
    const bool has_raw = raw_status == RESONITH_STATUS_OK;
    const bool has_cibs = cibs_status == RESONITH_STATUS_OK;
    if (has_raw == has_cibs) {
        return RESONITH_STATUS_MALFORMED;
    }
    section = has_cibs ? cibs : raw;
    is_cibs = has_cibs;
    return RESONITH_STATUS_OK;
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
    const resonith_cibs_registry* registry,
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

    bool found_config = false;
    bool found_innovation = false;
    std::uint32_t atom_count = 0U;
    std::uint32_t basis_count = 0U;

    /*
     * Integrity precedes typed interpretation. This first pass verifies each
     * known payload exactly once and freezes the canonical instance registry.
     */
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
            section.schema_version != kSchemaVersion
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
            if (section.instance_id != atom_count) {
                return RESONITH_STATUS_MALFORMED;
            }
            ++atom_count;
        } else if (
            type_is(section.type, "BRAW")
            || type_is(section.type, "BCIB")
        ) {
            ++basis_count;
        } else if (type_is(section.type, "CONF")) {
            if (
                found_config
                || section.instance_id != 0U
                || section.start_tick != 0U
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            parsed->config = section;
            found_config = true;
        } else {
            if (
                found_innovation
                || section.instance_id != 0U
                || section.start_tick != 0U
            ) {
                return RESONITH_STATUS_MALFORMED;
            }
            parsed->innovation = section;
            found_innovation = true;
        }
    }
    if (!found_config || !found_innovation) {
        return RESONITH_STATUS_NOT_FOUND;
    }
    if ((atom_count == 0U) != (basis_count == 0U)) {
        return RESONITH_STATUS_MALFORMED;
    }

    status = resonith_stream_config_parse(
        parsed->config.payload,
        parsed->config.payload_size,
        &parsed->stream_config
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
    if (parsed->stream_config.output_channels != 1U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (
        parsed->innovation_info.sample_count
            != parsed->stream_config.sample_count
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    std::uint32_t maximum_basis_elements = 0U;
    std::size_t maximum_cibs_scratch = 0U;
    for (std::uint32_t basis_id = 0U; basis_id < basis_count; ++basis_id) {
        resonith_container_section basis{};
        bool is_cibs = false;
        status = find_basis_section(
            parsed->view,
            basis_id,
            basis,
            is_cibs
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        std::uint32_t basis_elements = 0U;
        std::uint32_t basis_length = 0U;
        std::uint16_t basis_channels = 0U;
        if (is_cibs) {
            if (registry == nullptr) {
                return RESONITH_STATUS_UNSUPPORTED_FEATURE;
            }
            resonith_cibs_basis_info basis_info{};
            status = resonith_cibs_basis_inspect(
                basis.payload,
                basis.payload_size,
                registry,
                &basis_info
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            basis_elements = basis_info.output_elements;
            basis_length = basis_info.output_length;
            basis_channels = basis_info.channels;
            maximum_cibs_scratch = std::max<std::size_t>(
                maximum_cibs_scratch,
                basis_info.scratch_elements
            );
        } else {
            resonith_raw_basis_info basis_info{};
            status = resonith_raw_basis_inspect(
                basis.payload,
                basis.payload_size,
                &basis_info
            );
            if (status != RESONITH_STATUS_OK) {
                return status;
            }
            basis_elements = basis_info.total_elements;
            basis_length = basis_info.samples_per_channel;
            basis_channels = basis_info.channels;
        }
        if (
            basis_channels != 1U
            || basis_length < 2U
            || basis.start_tick >= parsed->stream_config.sample_count
        ) {
            return basis_channels != 1U
                ? RESONITH_STATUS_UNSUPPORTED_FEATURE
                : RESONITH_STATUS_MALFORMED;
        }
        if (basis_elements > maximum_basis_elements) {
            maximum_basis_elements = basis_elements;
        }
    }

    std::uint64_t cursor = 0U;
    std::uint32_t maximum_phase_knots = 0U;
    std::uint32_t maximum_gain_events = 0U;
    std::uint32_t maximum_atom_samples = 0U;
    for (std::uint32_t atom_id = 0U; atom_id < atom_count; ++atom_id) {
        resonith_container_section atom{};
        status = resonith_container_find_section(
            &parsed->view,
            kAtomType,
            atom_id,
            &atom
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (atom.start_tick != cursor) {
            return RESONITH_STATUS_MALFORMED;
        }
        resonith_periodic_atom_info atom_info{};
        status = resonith_periodic_atom_inspect(
            atom.payload,
            atom.payload_size,
            &atom_info
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (atom_info.basis_instance_id >= basis_count) {
            return RESONITH_STATUS_NOT_FOUND;
        }
        resonith_container_section basis{};
        bool is_cibs = false;
        status = find_basis_section(
            parsed->view,
            atom_info.basis_instance_id,
            basis,
            is_cibs
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (basis.start_tick > atom.start_tick) {
            return RESONITH_STATUS_MALFORMED;
        }
        cursor += atom_info.duration_samples;
        if (cursor > parsed->stream_config.sample_count) {
            return RESONITH_STATUS_MALFORMED;
        }
        if (atom_info.phase_knot_count > maximum_phase_knots) {
            maximum_phase_knots = atom_info.phase_knot_count;
        }
        if (atom_info.gain_event_count > maximum_gain_events) {
            maximum_gain_events = atom_info.gain_event_count;
        }
        if (atom_info.duration_samples > maximum_atom_samples) {
            maximum_atom_samples = atom_info.duration_samples;
        }
    }
    if (
        atom_count != 0U
        && cursor != parsed->stream_config.sample_count
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    requirements->timebase_hz = parsed->view.timebase_hz;
    requirements->sample_count = parsed->stream_config.sample_count;
    requirements->basis_elements = maximum_basis_elements;
    requirements->phase_knot_count = maximum_phase_knots;
    requirements->gain_event_count = maximum_gain_events;
    requirements->atom_count = atom_count;
    requirements->basis_count = basis_count;
    requirements->render_elements = maximum_atom_samples;
    requirements->liftpack_scratch_elements = std::max<std::size_t>(
        resonith_liftpack_required_scratch(&parsed->innovation_info),
        maximum_cibs_scratch
    );
    requirements->output_channels =
        parsed->stream_config.output_channels;
    requirements->reserved = 0U;
    return RESONITH_STATUS_OK;
}

bool workspace_present(
    const resonith_main0_workspace& workspace,
    const resonith_main0_requirements& requirements
) noexcept {
    return (
            requirements.basis_elements == 0U
            || workspace.basis != nullptr
        )
        && (
            requirements.phase_knot_count == 0U
            || (
                workspace.phase_positions != nullptr
                && workspace.phase_increments_q32 != nullptr
                && workspace.phase_origins_q32 != nullptr
            )
        )
        && (
            requirements.gain_event_count == 0U
            || (
                workspace.gain_positions != nullptr
                && workspace.gains_q15 != nullptr
            )
        )
        && (
            requirements.render_elements == 0U
            || workspace.unity_prediction != nullptr
        )
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
        && workspace.unity_capacity >= requirements.render_elements
        && workspace.innovation_capacity >= requirements.sample_count
        && workspace.liftpack_scratch_capacity
            >= requirements.liftpack_scratch_elements;
}

struct player_atom_state {
    resonith_periodic_atom_info atom{};
    resonith_prepared_phase_trajectory phase{};
    resonith_prepared_gain_law gain{};
    std::uint32_t start_sample = 0U;
    std::uint32_t end_sample = 0U;
    std::size_t basis_elements = 0U;
};

resonith_status load_basis(
    const main0_sections& parsed,
    const resonith_cibs_registry* registry,
    std::uint32_t basis_id,
    resonith_main0_workspace& workspace,
    std::size_t& elements_written
) {
    elements_written = 0U;
    resonith_container_section basis_section{};
    bool is_cibs = false;
    resonith_status status = find_basis_section(
        parsed.view,
        basis_id,
        basis_section,
        is_cibs
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (!is_cibs) {
        return resonith_raw_basis_decode(
            basis_section.payload,
            basis_section.payload_size,
            workspace.basis,
            workspace.basis_capacity,
            &elements_written
        );
    }
    if (registry == nullptr) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    return resonith_cibs_basis_materialize(
        basis_section.payload,
        basis_section.payload_size,
        registry,
        workspace.basis,
        workspace.basis_capacity,
        workspace.liftpack_scratch,
        workspace.liftpack_scratch_capacity,
        nullptr,
        nullptr,
        &elements_written
    );
}

resonith_status preflight_cibs_bases(
    const main0_sections& parsed,
    const resonith_cibs_registry* registry,
    std::uint32_t basis_count,
    resonith_main0_workspace& workspace,
    std::uint32_t& cached_basis_id,
    std::size_t& cached_basis_elements
) {
    cached_basis_id = 0xffff'ffffU;
    cached_basis_elements = 0U;
    for (std::uint32_t basis_id = 0U; basis_id < basis_count; ++basis_id) {
        resonith_container_section basis_section{};
        bool is_cibs = false;
        resonith_status status = find_basis_section(
            parsed.view,
            basis_id,
            basis_section,
            is_cibs
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (!is_cibs) {
            continue;
        }
        status = load_basis(
            parsed,
            registry,
            basis_id,
            workspace,
            cached_basis_elements
        );
        if (
            status != RESONITH_STATUS_OK
            || cached_basis_elements < 2U
        ) {
            return status == RESONITH_STATUS_OK
                ? RESONITH_STATUS_MALFORMED
                : status;
        }
        cached_basis_id = basis_id;
    }
    return RESONITH_STATUS_OK;
}

resonith_status prepare_player_atom(
    const main0_sections& parsed,
    const resonith_cibs_registry* registry,
    std::uint32_t atom_id,
    resonith_main0_workspace& workspace,
    std::uint32_t& cached_basis_id,
    std::size_t& cached_basis_elements,
    player_atom_state& state
) {
    resonith_container_section atom_section{};
    resonith_status status = resonith_container_find_section(
        &parsed.view,
        kAtomType,
        atom_id,
        &atom_section
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    resonith_periodic_atom_info atom{};
    status = resonith_periodic_atom_decode(
        atom_section.payload,
        atom_section.payload_size,
        workspace.phase_positions,
        workspace.phase_increments_q32,
        workspace.phase_capacity,
        workspace.gain_positions,
        workspace.gains_q15,
        workspace.gain_capacity,
        &atom
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    if (cached_basis_id != atom.basis_instance_id) {
        std::size_t basis_written = 0U;
        status = load_basis(
            parsed,
            registry,
            atom.basis_instance_id,
            workspace,
            basis_written
        );
        if (status != RESONITH_STATUS_OK || basis_written < 2U) {
            return status == RESONITH_STATUS_OK
                ? RESONITH_STATUS_MALFORMED
                : status;
        }
        cached_basis_id = atom.basis_instance_id;
        cached_basis_elements = basis_written;
    }

    const resonith_phase_trajectory phase_source = {
        workspace.phase_positions,
        workspace.phase_increments_q32,
        atom.phase_knot_count,
        atom.phase_origin_q32,
    };
    resonith_prepared_phase_trajectory phase{};
    status = resonith_phase_prepare(
        &phase_source,
        workspace.phase_origins_q32,
        workspace.phase_capacity,
        &phase
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    const resonith_gain_event_law gain_source = {
        workspace.gain_positions,
        workspace.gains_q15,
        atom.gain_event_count,
        atom.duration_samples,
    };
    resonith_prepared_gain_law gain{};
    status = resonith_gain_prepare(&gain_source, &gain);
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (atom_section.start_tick > kMaximumSampleCount) {
        return RESONITH_STATUS_MALFORMED;
    }
    const std::uint32_t start =
        static_cast<std::uint32_t>(atom_section.start_tick);
    state.atom = atom;
    state.phase = phase;
    state.gain = gain;
    state.start_sample = start;
    state.end_sample = start + atom.duration_samples;
    state.basis_elements = cached_basis_elements;
    return RESONITH_STATUS_OK;
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
    return resonith_main0_inspect_with_registry(
        data,
        data_size,
        nullptr,
        requirements
    );
}

extern "C" resonith_status resonith_main0_inspect_with_registry(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
    resonith_main0_requirements* requirements
) {
    if (requirements == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    main0_sections parsed{};
    return parse_main0(
        data,
        data_size,
        registry,
        &parsed,
        requirements
    );
}

extern "C" resonith_status resonith_main0_decode(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_main0_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    std::size_t* samples_written
) {
    return resonith_main0_decode_with_registry(
        data,
        data_size,
        nullptr,
        workspace,
        output,
        output_capacity,
        samples_written
    );
}

extern "C" resonith_status resonith_main0_decode_with_registry(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
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
        registry,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (output_capacity < requirements.sample_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (!workspace_present(*workspace, requirements)) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (!workspace_large_enough(*workspace, requirements)) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    std::uint32_t cached_basis_id = 0xffff'ffffU;
    std::size_t cached_basis_elements = 0U;
    status = preflight_cibs_bases(
        parsed,
        registry,
        requirements.basis_count,
        *workspace,
        cached_basis_id,
        cached_basis_elements
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

    if (requirements.atom_count == 0U) {
        for (
            std::uint32_t sample = 0U;
            sample < requirements.sample_count;
            ++sample
        ) {
            output[sample] = scale_innovation(
                workspace->innovation_q[sample],
                parsed.stream_config.innovation_step
            );
        }
        *samples_written = requirements.sample_count;
        return RESONITH_STATUS_OK;
    }

    std::uint32_t output_cursor = 0U;
    for (
        std::uint32_t atom_id = 0U;
        atom_id < requirements.atom_count;
        ++atom_id
    ) {
        resonith_container_section atom_section{};
        status = resonith_container_find_section(
            &parsed.view,
            kAtomType,
            atom_id,
            &atom_section
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        resonith_periodic_atom_info atom{};
        status = resonith_periodic_atom_decode(
            atom_section.payload,
            atom_section.payload_size,
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

        if (cached_basis_id != atom.basis_instance_id) {
            status = load_basis(
                parsed,
                registry,
                atom.basis_instance_id,
                *workspace,
                cached_basis_elements
            );
            if (
                status != RESONITH_STATUS_OK
                || cached_basis_elements < 2U
            ) {
                return status == RESONITH_STATUS_OK
                    ? RESONITH_STATUS_MALFORMED
                    : status;
            }
            cached_basis_id = atom.basis_instance_id;
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
        resonith_maf_operation_budget budget = {
            static_cast<std::uint64_t>(atom.duration_samples) * 16U,
        };
        status = resonith_maf_periodic_render(
            workspace->basis,
            cached_basis_elements,
            &phase,
            0U,
            atom.duration_samples,
            workspace->unity_prediction,
            workspace->unity_capacity,
            &budget
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
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
        status = resonith_maf_compose_truth(
            workspace->unity_prediction,
            workspace->innovation_q + output_cursor,
            parsed.stream_config.innovation_step,
            &gain,
            0U,
            atom.duration_samples,
            output + output_cursor,
            output_capacity - output_cursor,
            &budget
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        output_cursor += atom.duration_samples;
    }
    if (output_cursor != requirements.sample_count) {
        return RESONITH_STATUS_MALFORMED;
    }
    *samples_written = requirements.sample_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_main0_player_open(
    const std::uint8_t* data,
    std::size_t data_size,
    resonith_main0_player_view* view
) {
    return resonith_main0_player_open_with_registry(
        data,
        data_size,
        nullptr,
        view
    );
}

extern "C" resonith_status resonith_main0_player_open_with_registry(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
    resonith_main0_player_view* view
) {
    if (view == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *view = {};
    main0_sections parsed{};
    resonith_main0_requirements requirements{};
    const resonith_status status = parse_main0(
        data,
        data_size,
        registry,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    view->innovation_data = parsed.innovation.payload;
    view->innovation_size = parsed.innovation.payload_size;
    view->timebase_hz = requirements.timebase_hz;
    view->sample_count = requirements.sample_count;
    view->innovation_step = parsed.stream_config.innovation_step;
    view->block_size = parsed.innovation_info.block_size;
    view->block_count = parsed.innovation_info.block_count;
    view->atom_count = requirements.atom_count;
    view->liftpack_scratch_elements =
        requirements.liftpack_scratch_elements;
    view->output_channels = requirements.output_channels;
    view->reserved = 0U;
    view->stream_data = data;
    view->stream_size = data_size;
    view->basis_elements = requirements.basis_elements;
    view->phase_knot_count = requirements.phase_knot_count;
    view->gain_event_count = requirements.gain_event_count;
    view->basis_count = requirements.basis_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_main0_player_decode_block(
    const resonith_main0_player_view* view,
    std::uint32_t block_index,
    std::int64_t* innovation_q,
    std::size_t innovation_capacity,
    std::int64_t* liftpack_scratch,
    std::size_t liftpack_scratch_capacity,
    std::int16_t* output,
    std::size_t output_capacity,
    std::uint32_t* sample_offset,
    std::size_t* samples_written
) {
    if (sample_offset == nullptr || samples_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *sample_offset = 0U;
    *samples_written = 0U;
    if (
        view == nullptr
        || innovation_q == nullptr
        || liftpack_scratch == nullptr
        || output == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        view->innovation_data == nullptr
        || view->innovation_size == 0U
        || view->innovation_step == 0U
        || view->innovation_step > kMaximumInnovationStep
        || view->output_channels != 1U
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (view->atom_count != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    std::uint32_t decoded_offset = 0U;
    std::size_t decoded_count = 0U;
    const resonith_status status = resonith_liftpack_decode_block(
        view->innovation_data,
        view->innovation_size,
        block_index,
        innovation_q,
        innovation_capacity,
        liftpack_scratch,
        liftpack_scratch_capacity,
        &decoded_offset,
        &decoded_count
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (output_capacity < decoded_count) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    for (std::size_t sample = 0U; sample < decoded_count; ++sample) {
        output[sample] = scale_innovation(
            innovation_q[sample],
            view->innovation_step
        );
    }
    *sample_offset = decoded_offset;
    *samples_written = decoded_count;
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_main0_player_stream(
    const resonith_main0_player_view* view,
    std::int64_t* innovation_q,
    std::size_t innovation_capacity,
    std::int64_t* liftpack_scratch,
    std::size_t liftpack_scratch_capacity,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_pcm16_callback callback,
    void* user,
    std::size_t* samples_emitted
) {
    if (samples_emitted == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *samples_emitted = 0U;
    if (
        view == nullptr
        || innovation_q == nullptr
        || liftpack_scratch == nullptr
        || output == nullptr
        || callback == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        view->innovation_data == nullptr
        || view->innovation_size == 0U
        || view->innovation_step == 0U
        || view->innovation_step > kMaximumInnovationStep
        || view->output_channels != 1U
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (view->atom_count != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }

    resonith_liftpack_cursor cursor{};
    resonith_status status = resonith_liftpack_cursor_open(
        view->innovation_data,
        view->innovation_size,
        &cursor
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        cursor.info.sample_count != view->sample_count
        || cursor.info.block_count != view->block_count
        || cursor.info.block_size != view->block_size
        || resonith_liftpack_required_scratch(&cursor.info)
            != view->liftpack_scratch_elements
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    while (cursor.next_block < cursor.info.block_count) {
        std::uint32_t block_offset = 0U;
        std::size_t block_samples = 0U;
        status = resonith_liftpack_cursor_decode_next(
            &cursor,
            innovation_q,
            innovation_capacity,
            liftpack_scratch,
            liftpack_scratch_capacity,
            &block_offset,
            &block_samples
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        if (output_capacity < block_samples) {
            return RESONITH_STATUS_OUTPUT_TOO_SMALL;
        }
        for (std::size_t sample = 0U; sample < block_samples; ++sample) {
            output[sample] = scale_innovation(
                innovation_q[sample],
                view->innovation_step
            );
        }
        status = callback(user, block_offset, output, block_samples);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        *samples_emitted += block_samples;
    }
    return *samples_emitted == view->sample_count
        ? RESONITH_STATUS_OK
        : RESONITH_STATUS_MALFORMED;
}

extern "C" resonith_status resonith_main0_player_stream_complete(
    const resonith_main0_player_view* view,
    resonith_main0_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_pcm16_callback callback,
    void* user,
    std::size_t* samples_emitted
) {
    return resonith_main0_player_stream_complete_with_registry(
        view,
        nullptr,
        workspace,
        output,
        output_capacity,
        callback,
        user,
        samples_emitted
    );
}

extern "C" resonith_status resonith_main0_player_stream_complete_with_registry(
    const resonith_main0_player_view* view,
    const resonith_cibs_registry* registry,
    resonith_main0_workspace* workspace,
    std::int16_t* output,
    std::size_t output_capacity,
    resonith_pcm16_callback callback,
    void* user,
    std::size_t* samples_emitted
) {
    if (samples_emitted == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *samples_emitted = 0U;
    if (
        view == nullptr
        || workspace == nullptr
        || output == nullptr
        || callback == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        view->stream_data == nullptr
        || view->stream_size == 0U
        || workspace->innovation_q == nullptr
        || workspace->liftpack_scratch == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    main0_sections parsed{};
    resonith_main0_requirements requirements{};
    resonith_status status = parse_main0(
        view->stream_data,
        view->stream_size,
        registry,
        &parsed,
        &requirements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }
    if (
        parsed.innovation.payload != view->innovation_data
        || parsed.innovation.payload_size != view->innovation_size
        || requirements.sample_count != view->sample_count
        || requirements.atom_count != view->atom_count
        || requirements.basis_count != view->basis_count
        || requirements.basis_elements != view->basis_elements
        || requirements.phase_knot_count != view->phase_knot_count
        || requirements.gain_event_count != view->gain_event_count
        || parsed.innovation_info.block_size != view->block_size
        || parsed.innovation_info.block_count != view->block_count
        || requirements.liftpack_scratch_elements
            != view->liftpack_scratch_elements
        || requirements.timebase_hz != view->timebase_hz
        || requirements.output_channels != view->output_channels
        || parsed.stream_config.innovation_step != view->innovation_step
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    const std::size_t stream_render_elements = std::min<std::size_t>(
        view->block_size,
        requirements.render_elements
    );
    if (
        (
            requirements.basis_elements != 0U
            && workspace->basis == nullptr
        )
        || (
            requirements.phase_knot_count != 0U
            && (
                workspace->phase_positions == nullptr
                || workspace->phase_increments_q32 == nullptr
                || workspace->phase_origins_q32 == nullptr
            )
        )
        || (
            requirements.gain_event_count != 0U
            && (
                workspace->gain_positions == nullptr
                || workspace->gains_q15 == nullptr
            )
        )
        || (
            stream_render_elements != 0U
            && workspace->unity_prediction == nullptr
        )
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        workspace->basis_capacity < requirements.basis_elements
        || workspace->phase_capacity < requirements.phase_knot_count
        || workspace->gain_capacity < requirements.gain_event_count
        || workspace->unity_capacity < stream_render_elements
        || workspace->innovation_capacity < view->block_size
        || workspace->liftpack_scratch_capacity
            < requirements.liftpack_scratch_elements
        || output_capacity < view->block_size
    ) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }

    std::uint32_t cached_basis_id = 0xffff'ffffU;
    std::size_t cached_basis_elements = 0U;
    status = preflight_cibs_bases(
        parsed,
        registry,
        requirements.basis_count,
        *workspace,
        cached_basis_id,
        cached_basis_elements
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    resonith_liftpack_cursor cursor{};
    status = resonith_liftpack_cursor_open(
        view->innovation_data,
        view->innovation_size,
        &cursor
    );
    if (status != RESONITH_STATUS_OK) {
        return status;
    }

    std::uint32_t next_atom_id = 0U;
    player_atom_state state{};
    bool state_ready = false;
    while (cursor.next_block < cursor.info.block_count) {
        std::uint32_t block_offset = 0U;
        std::size_t block_samples = 0U;
        status = resonith_liftpack_cursor_decode_next(
            &cursor,
            workspace->innovation_q,
            workspace->innovation_capacity,
            workspace->liftpack_scratch,
            workspace->liftpack_scratch_capacity,
            &block_offset,
            &block_samples
        );
        if (status != RESONITH_STATUS_OK) {
            return status;
        }

        if (requirements.atom_count == 0U) {
            for (std::size_t sample = 0U; sample < block_samples; ++sample) {
                output[sample] = scale_innovation(
                    workspace->innovation_q[sample],
                    parsed.stream_config.innovation_step
                );
            }
        } else {
            std::size_t block_cursor = 0U;
            while (block_cursor < block_samples) {
                const std::uint32_t absolute_sample = block_offset
                    + static_cast<std::uint32_t>(block_cursor);
                while (
                    !state_ready
                    || absolute_sample >= state.end_sample
                ) {
                    if (next_atom_id >= requirements.atom_count) {
                        return RESONITH_STATUS_MALFORMED;
                    }
                    status = prepare_player_atom(
                        parsed,
                        registry,
                        next_atom_id,
                        *workspace,
                        cached_basis_id,
                        cached_basis_elements,
                        state
                    );
                    if (status != RESONITH_STATUS_OK) {
                        return status;
                    }
                    ++next_atom_id;
                    state_ready = true;
                }
                if (absolute_sample < state.start_sample) {
                    return RESONITH_STATUS_MALFORMED;
                }
                const std::uint32_t local_sample =
                    absolute_sample - state.start_sample;
                const std::size_t segment_samples = std::min<std::size_t>(
                    block_samples - block_cursor,
                    state.end_sample - absolute_sample
                );
                resonith_maf_operation_budget budget = {
                    static_cast<std::uint64_t>(segment_samples) * 16U,
                };
                status = resonith_maf_periodic_render(
                    workspace->basis,
                    state.basis_elements,
                    &state.phase,
                    local_sample,
                    segment_samples,
                    workspace->unity_prediction,
                    workspace->unity_capacity,
                    &budget
                );
                if (status != RESONITH_STATUS_OK) {
                    return status;
                }
                status = resonith_maf_compose_truth(
                    workspace->unity_prediction,
                    workspace->innovation_q + block_cursor,
                    parsed.stream_config.innovation_step,
                    &state.gain,
                    local_sample,
                    segment_samples,
                    output + block_cursor,
                    output_capacity - block_cursor,
                    &budget
                );
                if (status != RESONITH_STATUS_OK) {
                    return status;
                }
                block_cursor += segment_samples;
            }
        }

        status = callback(user, block_offset, output, block_samples);
        if (status != RESONITH_STATUS_OK) {
            return status;
        }
        *samples_emitted += block_samples;
    }
    if (
        *samples_emitted != view->sample_count
        || (
            requirements.atom_count != 0U
            && (
                !state_ready
                || state.end_sample != view->sample_count
                || next_atom_id != requirements.atom_count
            )
        )
    ) {
        return RESONITH_STATUS_MALFORMED;
    }
    return RESONITH_STATUS_OK;
}
