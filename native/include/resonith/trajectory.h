#ifndef RESONITH_TRAJECTORY_H
#define RESONITH_TRAJECTORY_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Absolute piecewise-linear Q32 phase law.
 *
 * Positions begin at zero, end at the Atom sample count, and are strictly
 * increasing. Increments contain unsigned Q0.32 cycles/sample at each knot.
 * All arrays are caller-owned immutable memory.
 */
typedef struct resonith_phase_trajectory {
    const uint32_t* positions;
    const uint32_t* increments_q32;
    uint32_t knot_count;
    uint32_t phase_origin_q32;
} resonith_phase_trajectory;

/*
 * Validated trajectory plus caller-owned phase at every knot. The source
 * arrays and origin array must remain immutable and alive during rendering.
 */
typedef struct resonith_prepared_phase_trajectory {
    const uint32_t* positions;
    const uint32_t* increments_q32;
    const uint32_t* knot_origins_q32;
    uint32_t knot_count;
    uint32_t sample_count;
} resonith_prepared_phase_trajectory;

/*
 * Validates the complete law and materializes one Q32 phase origin per knot.
 * Preparation is allocation-free and belongs outside the audio callback.
 */
RESONITH_API resonith_status resonith_phase_prepare(
    const resonith_phase_trajectory* trajectory,
    uint32_t* knot_origins_q32,
    size_t origin_capacity,
    resonith_prepared_phase_trajectory* prepared
);

/*
 * Evaluates exact absolute Q32 phases for an arbitrary half-open slice.
 * Output is independent of earlier calls and callback partitioning.
 */
RESONITH_API resonith_status resonith_phase_render(
    const resonith_prepared_phase_trajectory* trajectory,
    uint32_t output_start,
    size_t output_count,
    uint32_t* output,
    size_t output_capacity
);

/*
 * Renders one immutable mono int16 Basis with canonical Q16 interpolation.
 * The Basis contains one full periodic cycle in sample order.
 */
RESONITH_API resonith_status resonith_periodic_render(
    const int16_t* basis,
    size_t basis_count,
    const resonith_prepared_phase_trajectory* trajectory,
    uint32_t output_start,
    size_t output_count,
    int16_t* output,
    size_t output_capacity
);

#ifdef __cplusplus
}
#endif

#endif
