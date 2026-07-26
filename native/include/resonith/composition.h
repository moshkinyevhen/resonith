#ifndef RESONITH_COMPOSITION_H
#define RESONITH_COMPOSITION_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Sparse absolute step law for signed Q17.15 Atom gain.
 *
 * Positions begin at zero and are strictly increasing. Each gain remains
 * active through the sample immediately before the next event.
 */
typedef struct resonith_gain_event_law {
    const uint32_t* positions;
    const int32_t* gains_q15;
    uint32_t event_count;
    uint32_t sample_count;
} resonith_gain_event_law;

typedef struct resonith_prepared_gain_law {
    const uint32_t* positions;
    const int32_t* gains_q15;
    uint32_t event_count;
    uint32_t sample_count;
} resonith_prepared_gain_law;

/* Validates a complete immutable gain law without allocation. */
RESONITH_API resonith_status resonith_gain_prepare(
    const resonith_gain_event_law* source,
    resonith_prepared_gain_law* prepared
);

/*
 * Applies the absolute gain law and optional quantized Truth Innovation.
 *
 * `unity_prediction` and `innovation_q` address only the requested slice;
 * `output_start` locates it in the gain law. Innovation is zero when its
 * pointer is NULL and otherwise is multiplied by `innovation_step`.
 */
RESONITH_API resonith_status resonith_compose_truth(
    const int16_t* unity_prediction,
    const int64_t* innovation_q,
    uint32_t innovation_step,
    const resonith_prepared_gain_law* gain_law,
    uint32_t output_start,
    size_t output_count,
    int16_t* output,
    size_t output_capacity
);

#ifdef __cplusplus
}
#endif

#endif
