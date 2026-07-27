#ifndef RESONITH_MAF_H
#define RESONITH_MAF_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/composition.h"
#include "resonith/status.h"
#include "resonith/trajectory.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_MAF_MAIN_MAX_CHANNELS = 8,
    RESONITH_MAF_MAIN_MAX_EMITTERS = 64,
    RESONITH_MAF_MAIN_MAX_BASES = 256,
    RESONITH_MAF_MAIN_MAX_FILTERS = 64,
    RESONITH_MAF_MAIN_MAX_FILTER_ORDER = 16,
    RESONITH_MAF_MAIN_MAX_STOCHASTIC_FIELDS = 64,
    RESONITH_MAF_MAIN_MAX_TRANSIENTS = 4096,
    RESONITH_MAF_MAIN_MAX_TRANSIENT_SAMPLES = 512,
    RESONITH_MAF_MAIN_MAX_PVQ_DIMENSION = 2048,
    RESONITH_MAF_MAIN_MAX_PVQ_PULSES = 256,
    RESONITH_MAF_MAIN_MAX_RENDER_FRAMES = 4096
};

/*
 * Hard profile limits installed with the decoder, never supplied by a track.
 * Byte and operation limits use 64-bit values to keep validation overflow-free.
 */
typedef struct resonith_maf_limits {
    uint32_t maximum_sample_rate;
    uint32_t maximum_render_frames;
    uint32_t maximum_emitters;
    uint32_t maximum_bases;
    uint32_t maximum_basis_elements;
    uint32_t maximum_phase_knots;
    uint32_t maximum_gain_events;
    uint32_t maximum_filters;
    uint32_t maximum_stochastic_fields;
    uint32_t maximum_transients;
    uint16_t maximum_output_channels;
    uint16_t maximum_filter_order;
    uint16_t maximum_pvq_dimension;
    uint16_t maximum_pvq_pulses;
    uint64_t maximum_persistent_bytes;
    uint64_t maximum_scratch_bytes;
    uint64_t maximum_operations_per_frame;
} resonith_maf_limits;

/* Complete resource declaration extracted from one validated stream. */
typedef struct resonith_maf_resource_declaration {
    uint32_t sample_rate;
    uint32_t render_frames;
    uint32_t emitter_count;
    uint32_t basis_count;
    uint32_t basis_elements;
    uint32_t phase_knot_count;
    uint32_t gain_event_count;
    uint32_t filter_count;
    uint32_t stochastic_field_count;
    uint32_t transient_count;
    uint16_t output_channels;
    uint16_t maximum_filter_order;
    uint16_t maximum_pvq_dimension;
    uint16_t maximum_pvq_pulses;
    uint64_t persistent_bytes;
    uint64_t scratch_bytes;
    uint64_t operations_per_frame;
} resonith_maf_resource_declaration;

typedef struct resonith_maf_requirements {
    uint64_t output_elements;
    uint64_t output_bytes;
    uint64_t persistent_bytes;
    uint64_t scratch_bytes;
    uint64_t operations_per_block;
} resonith_maf_requirements;

/* Monotonically decreasing render budget owned by one playback transaction. */
typedef struct resonith_maf_operation_budget {
    uint64_t remaining;
} resonith_maf_operation_budget;

/*
 * Prepared stable all-pole source/resonator filter.
 *
 * Coefficients are caller-owned Q17.15 LPC values produced by
 * resonith_maf_filter_prepare. History stores newest decoded PCM first and is
 * mutable playback-head state.
 */
typedef struct resonith_maf_filter {
    const int32_t* coefficients_q15;
    uint16_t order;
    uint16_t reserved;
} resonith_maf_filter;

/* Resolved bounded transient; sample storage remains caller-owned immutable. */
typedef struct resonith_maf_transient {
    const int16_t* samples;
    uint32_t onset;
    uint16_t sample_count;
    uint16_t reserved;
    int32_t gain_q15;
} resonith_maf_transient;

/* Returns the normative Main-0 limits implemented by this Core. */
RESONITH_API resonith_status resonith_maf_main_limits(
    resonith_maf_limits* limits
);

/* Validates all stream-declared resources without allocation or PCM writes. */
RESONITH_API resonith_status resonith_maf_resources_validate(
    const resonith_maf_limits* limits,
    const resonith_maf_resource_declaration* declaration,
    resonith_maf_requirements* requirements
);

/*
 * Wraps canonical periodic Basis rendering with an exact operation preflight.
 * Output is unchanged when the budget is insufficient.
 */
RESONITH_API resonith_status resonith_maf_periodic_render(
    const int16_t* basis,
    size_t basis_count,
    const resonith_prepared_phase_trajectory* trajectory,
    uint32_t output_start,
    size_t output_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Applies a gain law and optional quantized Truth Innovation through the
 * bounded MAF transaction. Output is unchanged when preflight fails.
 */
RESONITH_API resonith_status resonith_maf_compose_truth(
    const int16_t* unity_prediction,
    const int64_t* innovation_q,
    uint32_t innovation_step,
    const resonith_prepared_gain_law* gain_law,
    uint32_t output_start,
    size_t output_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Renders counter-addressed Q15 noise. Output depends only on the declared
 * seed, IDs, gain, and absolute sample index, never callback partitioning.
 */
RESONITH_API resonith_status resonith_maf_noise_render(
    uint64_t stream_seed,
    uint32_t field_id,
    uint16_t channel_id,
    uint32_t absolute_start,
    int32_t gain_q15,
    size_t output_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Converts bounded Q15 reflection coefficients to stable Q17.15 LPC state.
 * Preparation belongs outside the audio callback.
 */
RESONITH_API resonith_status resonith_maf_filter_prepare(
    const int16_t* reflection_q15,
    uint16_t order,
    int32_t* coefficients_q15,
    size_t coefficient_capacity,
    resonith_maf_filter* prepared
);

/*
 * Applies one prepared causal synthesis filter. History is committed only
 * after argument and operation-budget preflight succeeds.
 */
RESONITH_API resonith_status resonith_maf_filter_render(
    const resonith_maf_filter* filter,
    const int16_t* excitation,
    size_t sample_count,
    int16_t* history,
    size_t history_capacity,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/* Adds quantized deterministic Innovation with saturating PCM16 commit. */
RESONITH_API resonith_status resonith_maf_innovation_add(
    const int16_t* prediction,
    const int64_t* innovation_q,
    uint32_t innovation_step,
    size_t sample_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Adds every transient overlapping one absolute render slice. All events are
 * validated before the first output write.
 */
RESONITH_API resonith_status resonith_maf_transients_add(
    const int16_t* base,
    uint32_t absolute_start,
    size_t sample_count,
    const resonith_maf_transient* transients,
    size_t transient_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Mixes source-major planar PCM through an output-major signed Q1.15 matrix
 * into interleaved PCM16. The complete block is budgeted before output commit.
 */
RESONITH_API resonith_status resonith_maf_mix_q15(
    const int16_t* planar_sources,
    uint16_t source_count,
    size_t frame_count,
    const int16_t* matrix_q15,
    uint16_t output_channels,
    int16_t* interleaved_output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

#ifdef __cplusplus
}
#endif

#endif
