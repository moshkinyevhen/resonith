#include "resonith/persistent_cell.h"

#include "resonith/composition.h"
#include "resonith/trajectory.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

namespace {

constexpr std::array<std::uint32_t, 12> kDurations = {
    1U, 2U, 4U, 8U, 16U, 32U, 64U, 128U, 256U, 512U, 1000U, 2000U,
};
constexpr std::int32_t kMaximumReflectionQ15 = 29491;
constexpr std::uint32_t kMinimumStepQ32 = 16106127U;
constexpr std::uint32_t kMaximumStepQ32 = 107374182U;
constexpr std::uint64_t kCellSeedMultiplier = 0x9e3779b97f4a7c15ULL;
constexpr std::size_t kChunk = RESONITH_MAF_MAIN_MAX_RENDER_FRAMES;
constexpr std::uint32_t kMaximumPhaseSpan = RESONITH_PCELL_CONTROL_SAMPLES;
constexpr std::size_t kMaximumPhaseKnots = RESONITH_PCELL_MAX_EVENT_CONTROLS + 1U;

std::uint16_t u16(const std::uint8_t* p) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(p[0])
            | (static_cast<std::uint16_t>(p[1]) << 8U)
    );
}

std::int16_t i16(const std::uint8_t* p) noexcept {
    return static_cast<std::int16_t>(u16(p));
}

std::uint32_t u32(const std::uint8_t* p) noexcept {
    return static_cast<std::uint32_t>(p[0])
        | (static_cast<std::uint32_t>(p[1]) << 8U)
        | (static_cast<std::uint32_t>(p[2]) << 16U)
        | (static_cast<std::uint32_t>(p[3]) << 24U);
}

std::uint64_t u64(const std::uint8_t* p) noexcept {
    return static_cast<std::uint64_t>(u32(p))
        | (static_cast<std::uint64_t>(u32(p + 4U)) << 32U);
}

bool add64(std::uint64_t a, std::uint64_t b, std::uint64_t& out) noexcept {
    if (b > std::numeric_limits<std::uint64_t>::max() - a) {
        return false;
    }
    out = a + b;
    return true;
}

bool mul64(std::uint64_t a, std::uint64_t b, std::uint64_t& out) noexcept {
    if (a != 0U && b > std::numeric_limits<std::uint64_t>::max() / a) {
        return false;
    }
    out = a * b;
    return true;
}

struct Header {
    std::uint32_t sample_count{};
    std::uint64_t seed{};
    std::uint32_t cells{};
    std::uint32_t events{};
    std::uint32_t refreshes{};
    std::uint32_t truth_bytes{};
    std::uint64_t cell_offset{RESONITH_PCELL_HEADER_BYTES};
    std::uint64_t event_offset{};
    std::uint64_t refresh_offset{};
    std::uint64_t truth_offset{};
};

struct Cell {
    std::uint16_t id{};
    std::uint32_t start{};
    std::uint32_t duration{};
    std::uint16_t fade_in{};
    std::uint16_t fade_out{};
    std::uint32_t phase{};
    std::uint32_t step{};
    std::int16_t pulse_gain{};
    std::int16_t noise_gain{};
    std::array<std::int16_t, RESONITH_PCELL_FILTER_ORDER> reflection{};

    std::uint32_t end() const noexcept { return start + duration; }
};

struct Event {
    std::uint16_t id{};
    std::uint16_t flags{};
    std::uint32_t offset{};
    std::uint32_t duration{};
    std::uint32_t end_step{};
    std::int16_t end_pulse{};
    std::int16_t end_noise{};
};

bool valid_gains(std::int16_t pulse, std::int16_t noise) noexcept {
    return pulse >= 0 && noise >= 0
        && static_cast<std::int32_t>(pulse) + noise <= 32767;
}

bool valid_step(std::uint32_t step, std::int16_t pulse) noexcept {
    return (pulse == 0 && step == 0U)
        || (step >= kMinimumStepQ32 && step <= kMaximumStepQ32);
}

Cell cell_at(const std::uint8_t* data, const Header& h, std::uint32_t index) {
    const std::uint8_t* p = data + h.cell_offset
        + static_cast<std::uint64_t>(index) * RESONITH_PCELL_CELL_BYTES;
    Cell cell{};
    cell.id = u16(p);
    cell.start = u32(p + 4U);
    cell.duration = u32(p + 8U);
    cell.fade_in = u16(p + 12U);
    cell.fade_out = u16(p + 14U);
    cell.phase = u32(p + 16U);
    cell.step = u32(p + 20U);
    cell.pulse_gain = i16(p + 24U);
    cell.noise_gain = i16(p + 26U);
    for (std::size_t i = 0U; i < cell.reflection.size(); ++i) {
        cell.reflection[i] = i16(p + 28U + 2U * i);
    }
    return cell;
}

Event event_at(const std::uint8_t* data, const Header& h, std::uint32_t index) {
    const std::uint8_t* p = data + h.event_offset
        + static_cast<std::uint64_t>(index) * RESONITH_PCELL_EVENT_BYTES;
    return {u16(p), u16(p + 2U), u32(p + 4U), u32(p + 8U),
            u32(p + 12U), i16(p + 16U), i16(p + 18U)};
}

const Cell find_cell(
    const std::uint8_t* data,
    const Header& h,
    std::uint16_t id,
    bool& found
) {
    std::uint32_t lo = 0U, hi = h.cells;
    while (lo < hi) {
        const std::uint32_t mid = lo + (hi - lo) / 2U;
        const Cell cell = cell_at(data, h, mid);
        if (cell.id < id) lo = mid + 1U;
        else hi = mid;
    }
    found = lo < h.cells && cell_at(data, h, lo).id == id;
    return found ? cell_at(data, h, lo) : Cell{};
}

resonith_status parse_header(
    const std::uint8_t* data,
    std::size_t size,
    Header& h
) noexcept {
    if (data == nullptr) return RESONITH_STATUS_INVALID_ARGUMENT;
    if (size < RESONITH_PCELL_HEADER_BYTES) return RESONITH_STATUS_TRUNCATED;
    if (data[0] != 'S' || data[1] != 'F' || data[2] != 'C' || data[3] != '2')
        return RESONITH_STATUS_BAD_MAGIC;
    if (data[4] != 2U || data[5] != 0U) return RESONITH_STATUS_UNSUPPORTED_VERSION;
    if (u16(data + 6U) != 0U || u32(data + 8U) != RESONITH_PCELL_SAMPLE_RATE
        || u32(data + 40U) != RESONITH_PCELL_HEADER_BYTES
        || u32(data + 44U) != 0U) return RESONITH_STATUS_MALFORMED;
    h.sample_count = u32(data + 12U); h.seed = u64(data + 16U);
    h.cells = u32(data + 24U); h.events = u32(data + 28U);
    h.refreshes = u32(data + 32U); h.truth_bytes = u32(data + 36U);
    if (h.sample_count == 0U || h.sample_count > RESONITH_PCELL_MAX_SAMPLES
        || h.cells == 0U || h.cells > RESONITH_PCELL_MAX_CELLS) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::uint64_t n = (h.sample_count + 79U) / 80U;
    if (h.events > 2U * (n + 1U) || h.refreshes > 2U * (n + 1U))
        return RESONITH_STATUS_PROFILE_BOUND;
    std::uint64_t bytes = 0U;
    if (!mul64(h.cells, RESONITH_PCELL_CELL_BYTES, bytes)
        || !add64(h.cell_offset, bytes, h.event_offset)
        || !mul64(h.events, RESONITH_PCELL_EVENT_BYTES, bytes)
        || !add64(h.event_offset, bytes, h.refresh_offset)
        || !mul64(h.refreshes, RESONITH_PCELL_REFRESH_BYTES, bytes)
        || !add64(h.refresh_offset, bytes, h.truth_offset)
        || !add64(h.truth_offset, h.truth_bytes, bytes)) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (bytes != size) return bytes > size ? RESONITH_STATUS_TRUNCATED : RESONITH_STATUS_MALFORMED;
    if (bytes > RESONITH_PCELL_MAX_STREAM_BYTES) return RESONITH_STATUS_PROFILE_BOUND;
    return RESONITH_STATUS_OK;
}

resonith_status validate_cells(const std::uint8_t* data, const Header& h) {
    std::uint64_t coverage = 0U;
    Cell previous{};
    Cell before_previous{};
    for (std::uint32_t index = 0U; index < h.cells; ++index) {
        const Cell cell = cell_at(data, h, index);
        const std::uint8_t* raw = data + h.cell_offset
            + static_cast<std::uint64_t>(index) * RESONITH_PCELL_CELL_BYTES;
        if (u16(raw + 2U) != 0U || cell.duration == 0U
            || cell.start > h.sample_count || cell.duration > h.sample_count - cell.start
            || !valid_gains(cell.pulse_gain, cell.noise_gain)
            || !valid_step(cell.step, cell.pulse_gain)) return RESONITH_STATUS_MALFORMED;
        for (const std::int16_t k : cell.reflection)
            if (k < -kMaximumReflectionQ15 || k > kMaximumReflectionQ15)
                return RESONITH_STATUS_PROFILE_BOUND;
        coverage += (cell.duration + 79U) / 80U;
        if (index == 0U) {
            if (cell.start != 0U || cell.fade_in != 0U) return RESONITH_STATUS_MALFORMED;
        } else {
            if (cell.id <= previous.id || cell.start < previous.start
                || cell.start >= previous.end()) return RESONITH_STATUS_MALFORMED;
            const std::uint32_t overlap = previous.end() - cell.start;
            if (overlap < 80U || overlap > 1600U || previous.fade_out != overlap
                || cell.fade_in != overlap) return RESONITH_STATUS_MALFORMED;
            if (index > 1U && cell.start < before_previous.end())
                return RESONITH_STATUS_PROFILE_BOUND;
        }
        before_previous = previous; previous = cell;
    }
    if (previous.end() != h.sample_count || previous.fade_out != 0U
        || coverage > 2ULL * (((h.sample_count + 79U) / 80U) + 1U))
        return RESONITH_STATUS_MALFORMED;
    return RESONITH_STATUS_OK;
}

struct Coverage { std::uint16_t id{}; std::uint32_t end{}; bool used{}; };

Coverage* coverage_slot(std::array<Coverage, 2>& slots, std::uint16_t id) {
    for (auto& slot : slots) if (slot.used && slot.id == id) return &slot;
    for (auto& slot : slots) if (!slot.used) { slot = {id, 0U, true}; return &slot; }
    return nullptr;
}

resonith_status validate_events(const std::uint8_t* data, const Header& h) {
    std::array<Coverage, 2> slots{};
    std::uint32_t completed = 0U, last_absolute = 0U;
    std::uint16_t last_id = 0U; std::uint32_t last_offset = 0U;
    bool first = true;
    for (std::uint32_t index = 0U; index < h.events; ++index) {
        const Event event = event_at(data, h, index);
        const std::uint8_t* raw = data + h.event_offset
            + static_cast<std::uint64_t>(index) * RESONITH_PCELL_EVENT_BYTES;
        bool found = false; const Cell cell = find_cell(data, h, event.id, found);
        if (!found || (event.flags & ~7U) != 0U || u32(raw + 20U) != 0U
            || event.duration == 0U || event.duration > 160000U
            || event.offset > cell.duration || event.duration > cell.duration - event.offset
            || !valid_gains(event.end_pulse, event.end_noise)
            || !valid_step(event.end_step, event.end_pulse)) return RESONITH_STATUS_MALFORMED;
        const std::uint32_t absolute = cell.start + event.offset;
        if (!first && (absolute < last_absolute
            || (absolute == last_absolute && (event.id < last_id
                || (event.id == last_id && event.offset <= last_offset)))))
            return RESONITH_STATUS_MALFORMED;
        first = false; last_absolute = absolute; last_id = event.id; last_offset = event.offset;
        Coverage* slot = coverage_slot(slots, event.id);
        if (slot == nullptr || slot->end != event.offset) return RESONITH_STATUS_MALFORMED;
        slot->end += event.duration;
        if (slot->end == cell.duration) { slot->used = false; ++completed; }
    }
    return completed == h.cells ? RESONITH_STATUS_OK : RESONITH_STATUS_MALFORMED;
}

resonith_status validate_refreshes(const std::uint8_t* data, const Header& h) {
    if (h.refreshes == 0U) return RESONITH_STATUS_OK;
    std::array<Coverage, 2> slots{}; std::uint32_t completed = 0U;
    std::uint32_t last_absolute = 0U; std::uint16_t last_id = 0U;
    std::uint32_t last_offset = 0U; bool first = true;
    for (std::uint32_t index = 0U; index < h.refreshes; ++index) {
        const std::uint8_t* p = data + h.refresh_offset
            + static_cast<std::uint64_t>(index) * RESONITH_PCELL_REFRESH_BYTES;
        const std::uint16_t id = u16(p); const std::uint32_t offset = u32(p + 4U);
        const std::uint32_t duration = u32(p + 8U);
        bool found = false; const Cell cell = find_cell(data, h, id, found);
        if (!found || u16(p + 2U) != 0U || duration == 0U || offset > cell.duration
            || duration > cell.duration - offset) return RESONITH_STATUS_MALFORMED;
        for (std::size_t k = 0U; k < cell.reflection.size(); ++k)
            if (i16(p + 12U + 2U * k) != cell.reflection[k]) return RESONITH_STATUS_MALFORMED;
        const std::uint32_t absolute = cell.start + offset;
        if (!first && (absolute < last_absolute || (absolute == last_absolute
            && (id < last_id || (id == last_id && offset <= last_offset)))))
            return RESONITH_STATUS_MALFORMED;
        first = false; last_absolute = absolute; last_id = id; last_offset = offset;
        Coverage* slot = coverage_slot(slots, id);
        if (slot == nullptr || slot->end != offset) return RESONITH_STATUS_MALFORMED;
        slot->end += duration;
        if (slot->end == cell.duration) { slot->used = false; ++completed; }
    }
    return completed == h.cells ? RESONITH_STATUS_OK : RESONITH_STATUS_MALFORMED;
}

std::int32_t interpolate(std::int32_t a, std::int32_t b, std::uint32_t p, std::uint32_t d) {
    if (d == 0U) return b;
    const std::int64_t numerator = static_cast<std::int64_t>(a) * (d - p)
        + static_cast<std::int64_t>(b) * p;
    const std::int64_t magnitude = numerator < 0 ? -numerator : numerator;
    const std::int64_t rounded = (magnitude + d / 2U) / d;
    return static_cast<std::int32_t>(numerator < 0 ? -rounded : rounded);
}

std::int32_t fade_weight(const Cell& cell, std::uint32_t absolute) {
    if (cell.fade_in != 0U && absolute < cell.start + cell.fade_in) {
        const std::uint32_t p = absolute - cell.start, d = cell.fade_in;
        return static_cast<std::int32_t>((32767ULL * p + (d - 1U) / 2U) / (d - 1U));
    }
    if (cell.fade_out != 0U && absolute >= cell.end() - cell.fade_out) {
        const std::uint32_t p = absolute - (cell.end() - cell.fade_out), d = cell.fade_out;
        const std::int32_t incoming = static_cast<std::int32_t>(
            (32767ULL * p + (d - 1U) / 2U) / (d - 1U));
        return 32767 - incoming;
    }
    return 32767;
}

struct Active {
    Cell cell{}; Event event{}; bool used{}; bool has_event{};
    std::uint32_t event_absolute{}; std::uint32_t event_phase{};
    std::uint32_t start_step{}; std::int16_t start_pulse{}, start_noise{};
    std::array<std::int32_t, RESONITH_PCELL_FILTER_ORDER> coefficients{};
    std::array<std::int16_t, RESONITH_PCELL_FILTER_ORDER> history{};
    resonith_maf_filter filter{};
};

Active* active_by_id(std::array<Active, 2>& active, std::uint16_t id) {
    for (auto& state : active) if (state.used && state.cell.id == id) return &state;
    return nullptr;
}

resonith_status prepare_event_phase(
    std::uint32_t start_step,
    std::int16_t start_pulse,
    const Event& event,
    std::uint32_t origin,
    std::array<std::uint32_t, kMaximumPhaseKnots>& positions,
    std::array<std::uint32_t, kMaximumPhaseKnots>& increments,
    std::array<std::uint32_t, kMaximumPhaseKnots>& origins,
    resonith_prepared_phase_trajectory& prepared
) {
    std::uint32_t position = 0U; std::uint32_t count = 0U;
    while (true) {
        if (count >= positions.size()) return RESONITH_STATUS_PROFILE_BOUND;
        positions[count] = position;
        std::uint32_t step = (event.flags & 1U) != 0U
            ? static_cast<std::uint32_t>(interpolate(
                static_cast<std::int32_t>(start_step),
                static_cast<std::int32_t>(event.end_step), position, event.duration))
            : start_step;
        const std::int32_t pulse = (event.flags & 2U) != 0U
            ? interpolate(start_pulse, event.end_pulse, position, event.duration)
            : start_pulse;
        if (pulse == 0) step = 0U;
        else step = std::clamp(step, kMinimumStepQ32, kMaximumStepQ32);
        increments[count] = step;
        ++count;
        if (position == event.duration) break;
        position = std::min(event.duration, position + kMaximumPhaseSpan);
    }
    const resonith_phase_trajectory source = {
        positions.data(), increments.data(), count, origin};
    return resonith_phase_prepare(&source, origins.data(), origins.size(), &prepared);
}

resonith_status render_active(
    Active& state, std::uint64_t seed, std::uint32_t absolute,
    std::size_t count, std::int16_t* output, resonith_maf_operation_budget* budget
) {
    if (!state.has_event) return RESONITH_STATUS_MALFORMED;
    const std::uint32_t local = absolute - state.event_absolute;
    const std::uint32_t duration = state.event.duration;
    std::array<std::uint32_t, kMaximumPhaseKnots> phase_positions{}, increments{}, origins{};
    resonith_prepared_phase_trajectory phase{};
    resonith_status status = prepare_event_phase(state.start_step, state.start_pulse, state.event,
        state.event_phase, phase_positions, increments, origins, phase);
    if (status != RESONITH_STATUS_OK) return status;

    std::array<std::int16_t, 64> basis{}; basis[0] = 32767;
    std::array<std::int16_t, kChunk> pulse{}, noise{}, scaled_pulse{}, scaled_noise{};
    std::array<std::int16_t, kChunk * 2U> planar{};
    std::array<std::uint32_t, RESONITH_PCELL_MAX_EVENT_CONTROLS> positions{};
    std::array<std::int32_t, RESONITH_PCELL_MAX_EVENT_CONTROLS> pulse_gains{}, noise_gains{};
    std::uint32_t gain_count = 0U;
    for (std::uint32_t p = 0U; p < duration; p += RESONITH_PCELL_CONTROL_SAMPLES) {
        positions[gain_count] = p;
        const bool lp = (state.event.flags & 2U) != 0U;
        const bool ln = (state.event.flags & 4U) != 0U;
        pulse_gains[gain_count] = lp ? interpolate(state.start_pulse, state.event.end_pulse, p, duration) : state.start_pulse;
        noise_gains[gain_count] = ln ? interpolate(state.start_noise, state.event.end_noise, p, duration) : state.start_noise;
        ++gain_count;
    }
    const resonith_gain_event_law pulse_law = {positions.data(), pulse_gains.data(), gain_count, duration};
    const resonith_gain_event_law noise_law = {positions.data(), noise_gains.data(), gain_count, duration};
    resonith_prepared_gain_law prepared_pulse{}, prepared_noise{};
    if ((status = resonith_gain_prepare(&pulse_law, &prepared_pulse)) != RESONITH_STATUS_OK
        || (status = resonith_gain_prepare(&noise_law, &prepared_noise)) != RESONITH_STATUS_OK) return status;
    if ((status = resonith_maf_periodic_render(basis.data(), basis.size(), &phase, local,
            count, pulse.data(), pulse.size(), budget)) != RESONITH_STATUS_OK
        || (status = resonith_maf_compose_truth(pulse.data(), nullptr, 1U, &prepared_pulse,
            local, count, scaled_pulse.data(), scaled_pulse.size(), budget)) != RESONITH_STATUS_OK
        || (status = resonith_maf_noise_render(seed ^ (state.cell.id * kCellSeedMultiplier),
            0U, 0U, absolute, 32767, count, noise.data(), noise.size(), budget)) != RESONITH_STATUS_OK
        || (status = resonith_maf_compose_truth(noise.data(), nullptr, 1U, &prepared_noise,
            local, count, scaled_noise.data(), scaled_noise.size(), budget)) != RESONITH_STATUS_OK) return status;
    std::copy_n(scaled_pulse.data(), count, planar.data());
    std::copy_n(scaled_noise.data(), count, planar.data() + count);
    const std::array<std::int16_t, 2> unity = {32767, 32767};
    std::array<std::int16_t, kChunk> excitation{}, filtered{};
    if ((status = resonith_maf_mix_q15(planar.data(), 2U, count, unity.data(), 1U,
            excitation.data(), excitation.size(), budget)) != RESONITH_STATUS_OK
        || (status = resonith_maf_filter_render(&state.filter, excitation.data(), count,
            state.history.data(), state.history.size(), filtered.data(), filtered.size(), budget)) != RESONITH_STATUS_OK) return status;

    std::copy_n(filtered.data(), count, output);
    return RESONITH_STATUS_OK;
}

std::uint64_t square(std::int64_t value) {
    const std::uint64_t magnitude = static_cast<std::uint64_t>(value < 0 ? -value : value);
    if (magnitude != 0U && magnitude > std::numeric_limits<std::uint64_t>::max() / magnitude)
        return std::numeric_limits<std::uint64_t>::max();
    return magnitude * magnitude;
}

void add_weighted(
    std::uint64_t value,
    std::uint64_t weight,
    std::uint64_t& accumulator
) {
    if (value != 0U && weight > std::numeric_limits<std::uint64_t>::max() / value) {
        accumulator = std::numeric_limits<std::uint64_t>::max();
        return;
    }
    const std::uint64_t product = value * weight;
    if (product > std::numeric_limits<std::uint64_t>::max() - accumulator)
        accumulator = std::numeric_limits<std::uint64_t>::max();
    else accumulator += product;
}

} // namespace

extern "C" resonith_status resonith_pcell_inspect(
    const std::uint8_t* data, std::size_t size, resonith_pcell_inspection* inspection
) {
    if (inspection == nullptr) return RESONITH_STATUS_INVALID_ARGUMENT;
    *inspection = {};
    Header h{}; resonith_status status = parse_header(data, size, h);
    if (status != RESONITH_STATUS_OK) return status;
    if ((status = validate_cells(data, h)) != RESONITH_STATUS_OK
        || (status = validate_events(data, h)) != RESONITH_STATUS_OK
        || (status = validate_refreshes(data, h)) != RESONITH_STATUS_OK) return status;
    *inspection = {RESONITH_PCELL_SAMPLE_RATE, h.sample_count, h.seed, h.cells,
        h.events, h.refreshes, h.truth_bytes, h.truth_offset, size};
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_pcell_render_model(
    const std::uint8_t* data, std::size_t size, std::int16_t* output,
    std::size_t output_capacity, resonith_maf_operation_budget* budget
) {
    if (output == nullptr || budget == nullptr) return RESONITH_STATUS_INVALID_ARGUMENT;
    resonith_pcell_inspection inspection{};
    resonith_status status = resonith_pcell_inspect(data, size, &inspection);
    if (status != RESONITH_STATUS_OK) return status;
    if (output_capacity < inspection.sample_count) return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    Header h{}; if ((status = parse_header(data, size, h)) != RESONITH_STATUS_OK) return status;
    std::fill_n(output, h.sample_count, std::int16_t{0});
    std::array<Active, 2> active{}; std::uint32_t next_cell = 0U, next_event = 0U;
    std::uint32_t position = 0U;
    std::array<std::int16_t, kChunk * 2U> rendered{};
    while (position < h.sample_count) {
        while (next_cell < h.cells && cell_at(data, h, next_cell).start == position) {
            Active* slot = nullptr;
            for (auto& candidate : active) if (!candidate.used) { slot = &candidate; break; }
            if (slot == nullptr) return RESONITH_STATUS_PROFILE_BOUND;
            *slot = {}; slot->cell = cell_at(data, h, next_cell++); slot->used = true;
            slot->start_step = slot->cell.step; slot->start_pulse = slot->cell.pulse_gain;
            slot->start_noise = slot->cell.noise_gain; slot->event_phase = slot->cell.phase;
            status = resonith_maf_filter_prepare(slot->cell.reflection.data(),
                RESONITH_PCELL_FILTER_ORDER, slot->coefficients.data(),
                slot->coefficients.size(), &slot->filter);
            if (status != RESONITH_STATUS_OK) return status;
        }
        while (next_event < h.events) {
            const Event event = event_at(data, h, next_event);
            bool found = false; const Cell cell = find_cell(data, h, event.id, found);
            if (!found || cell.start + event.offset != position) break;
            Active* state = active_by_id(active, event.id);
            if (state == nullptr) return RESONITH_STATUS_MALFORMED;
            if (state->has_event) {
                state->start_step = state->event.end_step;
                state->start_pulse = state->event.end_pulse;
                state->start_noise = state->event.end_noise;
            }
            state->event = event; state->event_absolute = position; state->has_event = true;
            ++next_event;
        }
        std::uint32_t boundary = std::min<std::uint32_t>(h.sample_count, position + kChunk);
        if (next_cell < h.cells) boundary = std::min(boundary, cell_at(data, h, next_cell).start);
        for (const auto& state : active) if (state.used) {
            boundary = std::min(boundary, state.cell.end());
            if (state.has_event) boundary = std::min(boundary, state.event_absolute + state.event.duration);
            if ((state.cell.fade_in != 0U && position < state.cell.start + state.cell.fade_in)
                || (state.cell.fade_out != 0U
                    && position >= state.cell.end() - state.cell.fade_out)) {
                boundary = std::min(boundary, position + 1U);
            }
        }
        if (boundary <= position) return RESONITH_STATUS_MALFORMED;
        const std::size_t count = boundary - position;
        std::uint16_t source_count = 0U;
        for (auto& state : active) if (state.used) {
            status = render_active(state, h.seed, position, count,
                rendered.data() + source_count * count, budget);
            if (status != RESONITH_STATUS_OK) return status;
            ++source_count;
        }
        std::array<std::int16_t, 2> weights{}; std::uint16_t weight_index = 0U;
        for (const auto& state : active) if (state.used)
            weights[weight_index++] = static_cast<std::int16_t>(fade_weight(state.cell, position));
        if ((status = resonith_maf_mix_q15(rendered.data(), source_count, count,
                weights.data(), 1U, output + position, output_capacity - position,
                budget)) != RESONITH_STATUS_OK) return status;
        position = boundary;
        for (auto& state : active) if (state.used) {
            if (state.has_event && position == state.event_absolute + state.event.duration) {
                std::array<std::uint32_t, kMaximumPhaseKnots> positions{}, increments{}, origins{};
                resonith_prepared_phase_trajectory prepared{};
                if ((status = prepare_event_phase(state.start_step, state.start_pulse, state.event,
                        state.event_phase, positions, increments, origins, prepared))
                    != RESONITH_STATUS_OK) return status;
                state.event_phase = origins[prepared.knot_count - 1U];
                state.start_step = state.event.end_step;
                state.start_pulse = state.event.end_pulse;
                state.start_noise = state.event.end_noise;
                state.has_event = false;
            }
            if (position == state.cell.end()) state = {};
        }
    }
    return next_cell == h.cells && next_event == h.events ? RESONITH_STATUS_OK : RESONITH_STATUS_MALFORMED;
}

extern "C" resonith_status resonith_pcell_add_truth(
    const std::int16_t* model, const std::int16_t* decoded_truth,
    std::size_t sample_count, std::int16_t* output, std::size_t output_capacity,
    resonith_maf_operation_budget* budget
) {
    if (model == nullptr || decoded_truth == nullptr || output == nullptr || budget == nullptr)
        return RESONITH_STATUS_INVALID_ARGUMENT;
    if (output_capacity < sample_count) return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    std::array<std::int64_t, kChunk> widened{};
    for (std::size_t offset = 0U; offset < sample_count; offset += kChunk) {
        const std::size_t count = std::min(kChunk, sample_count - offset);
        for (std::size_t i = 0U; i < count; ++i) widened[i] = decoded_truth[offset + i];
        const resonith_status status = resonith_maf_innovation_add(model + offset,
            widened.data(), 1U, count, output + offset, output_capacity - offset, budget);
        if (status != RESONITH_STATUS_OK) return status;
    }
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_pcell_segment_controls(
    const resonith_pcell_control* controls, std::size_t control_count,
    const resonith_pcell_dp_weights* weights, std::uint32_t* predecessor,
    std::size_t predecessor_capacity, std::uint64_t* total_cost
) {
    if (controls == nullptr || weights == nullptr || predecessor == nullptr || total_cost == nullptr)
        return RESONITH_STATUS_INVALID_ARGUMENT;
    if (control_count == 0U || control_count > 120000U
        || predecessor_capacity < control_count + 1U
        || weights->phase_step_shift > 31U) return RESONITH_STATUS_PROFILE_BOUND;
    for (std::size_t index = 0U; index < control_count; ++index) {
        if (!valid_gains(controls[index].pulse_gain_q15, controls[index].noise_gain_q15)
            || !valid_step(controls[index].phase_step_q32, controls[index].pulse_gain_q15))
            return RESONITH_STATUS_PROFILE_BOUND;
        for (const std::int16_t reflection : controls[index].reflection_q15)
            if (reflection < -kMaximumReflectionQ15 || reflection > kMaximumReflectionQ15)
                return RESONITH_STATUS_PROFILE_BOUND;
    }
    std::vector<std::uint64_t> cost(control_count + 1U, std::numeric_limits<std::uint64_t>::max());
    cost[0] = 0U; predecessor[0] = 0U;
    for (std::size_t end = 1U; end <= control_count; ++end) {
        for (const std::uint32_t duration : kDurations) {
            if (duration > end) continue;
            const std::size_t begin = end - duration;
            const auto& first = controls[begin]; const auto& last = controls[end - 1U];
            std::uint64_t error = 0U;
            for (std::uint32_t p = 0U; p < duration; ++p) {
                const auto& value = controls[begin + p];
                const std::int64_t phase = static_cast<std::int64_t>(value.phase_step_q32 >> weights->phase_step_shift)
                    - interpolate(static_cast<std::int32_t>(first.phase_step_q32 >> weights->phase_step_shift),
                        static_cast<std::int32_t>(last.phase_step_q32 >> weights->phase_step_shift), p, duration - 1U);
                const std::int64_t pulse = value.pulse_gain_q15
                    - interpolate(first.pulse_gain_q15, last.pulse_gain_q15, p, duration - 1U);
                const std::int64_t noise = value.noise_gain_q15
                    - interpolate(first.noise_gain_q15, last.noise_gain_q15, p, duration - 1U);
                std::uint64_t increment = square(phase);
                add_weighted(square(pulse), weights->pulse_gain, increment);
                add_weighted(square(noise), weights->noise_gain, increment);
                for (std::size_t k = 0U; k < RESONITH_PCELL_FILTER_ORDER; ++k)
                    add_weighted(square(static_cast<std::int64_t>(
                        value.reflection_q15[k]) - first.reflection_q15[k]),
                        weights->reflection, increment);
                if (increment > std::numeric_limits<std::uint64_t>::max() - error) { error = std::numeric_limits<std::uint64_t>::max(); break; }
                error += increment;
            }
            const std::uint64_t weighted = weights->lambda_q8 == 0U ? 0U
                : (error > std::numeric_limits<std::uint64_t>::max() / weights->lambda_q8
                    ? std::numeric_limits<std::uint64_t>::max()
                    : (error * weights->lambda_q8) / 256U);
            const std::uint64_t event_bytes = RESONITH_PCELL_EVENT_BYTES + RESONITH_PCELL_CELL_BYTES;
            if (cost[begin] == std::numeric_limits<std::uint64_t>::max()
                || weighted > std::numeric_limits<std::uint64_t>::max() - event_bytes - cost[begin]) continue;
            const std::uint64_t candidate = cost[begin] + event_bytes + weighted;
            if (candidate < cost[end] || (candidate == cost[end] && begin < predecessor[end])) {
                cost[end] = candidate; predecessor[end] = static_cast<std::uint32_t>(begin);
            }
        }
        if (cost[end] == std::numeric_limits<std::uint64_t>::max()) return RESONITH_STATUS_PROFILE_BOUND;
    }
    *total_cost = cost[control_count];
    return RESONITH_STATUS_OK;
}
