#ifndef RESONITH_PERSISTENT_CELL_H
#define RESONITH_PERSISTENT_CELL_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/maf.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_PCELL_SAMPLE_RATE = 16000,
    RESONITH_PCELL_CONTROL_SAMPLES = 80,
    RESONITH_PCELL_MAX_SAMPLES = 9600000,
    RESONITH_PCELL_MAX_CELLS = 65535,
    RESONITH_PCELL_MAX_ACTIVE = 2,
    RESONITH_PCELL_FILTER_ORDER = 10,
    RESONITH_PCELL_HEADER_BYTES = 48,
    RESONITH_PCELL_CELL_BYTES = 48,
    RESONITH_PCELL_EVENT_BYTES = 24,
    RESONITH_PCELL_REFRESH_BYTES = 32,
    RESONITH_PCELL_MAX_STREAM_BYTES = 268435456,
    RESONITH_PCELL_MAX_EVENT_CONTROLS = 2000
};

typedef struct resonith_pcell_inspection {
    uint32_t sample_rate;
    uint32_t sample_count;
    uint64_t stream_seed;
    uint32_t cell_count;
    uint32_t excitation_event_count;
    uint32_t refresh_count;
    uint32_t truth_bytes;
    uint64_t truth_offset;
    uint64_t complete_bytes;
} resonith_pcell_inspection;

typedef struct resonith_pcell_control {
    uint32_t phase_step_q32;
    int16_t pulse_gain_q15;
    int16_t noise_gain_q15;
    int16_t reflection_q15[RESONITH_PCELL_FILTER_ORDER];
} resonith_pcell_control;

typedef struct resonith_pcell_dp_weights {
    uint16_t phase_step_shift;
    uint16_t pulse_gain;
    uint16_t noise_gain;
    uint16_t reflection;
    uint32_t lambda_q8;
} resonith_pcell_dp_weights;

/* Validates the complete fixed-record SFC2 envelope without allocating. */
RESONITH_API resonith_status resonith_pcell_inspect(
    const uint8_t* data,
    size_t size,
    resonith_pcell_inspection* inspection
);

/* Renders only the deterministic Cell model through frozen MAF primitives. */
RESONITH_API resonith_status resonith_pcell_render_model(
    const uint8_t* data,
    size_t size,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/* Adds an independently decoded signed-PCM16 S12 Truth signal. */
RESONITH_API resonith_status resonith_pcell_add_truth(
    const int16_t* model,
    const int16_t* decoded_truth,
    size_t sample_count,
    int16_t* output,
    size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/*
 * Runs the frozen twelve-predecessor bounded segmentation recurrence.
 * `predecessor[j]` receives the preceding control index for endpoint j;
 * predecessor[0] is zero. Caller owns all memory.
 */
RESONITH_API resonith_status resonith_pcell_segment_controls(
    const resonith_pcell_control* controls,
    size_t control_count,
    const resonith_pcell_dp_weights* weights,
    uint32_t* predecessor,
    size_t predecessor_capacity,
    uint64_t* total_cost
);

#ifdef __cplusplus
}
#endif

#endif
