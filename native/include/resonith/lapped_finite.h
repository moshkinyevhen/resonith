#ifndef RESONITH_LAPPED_FINITE_H
#define RESONITH_LAPPED_FINITE_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/lapped.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Allocation contract for the LAF1 research entropy candidate.
 *
 * The shape is carried by LAF1 while `half_window` is inherited from the
 * authenticated transform envelope. The decoder owns no heap or mutable
 * global state.
 */
typedef struct resonith_lapped_finite_requirements {
    uint32_t transform_frame_count;
    uint16_t channels;
    uint16_t band_count;
    uint16_t half_window;
    uint16_t gap_threshold;
    size_t scale_elements;
    size_t count_elements;
    size_t position_elements;
    size_t coefficient_elements;
} resonith_lapped_finite_requirements;

/*
 * Validates exact LAF1 framing and bounded allocation arithmetic without
 * decoding symbols or writing caller memory.
 */
RESONITH_API resonith_status resonith_lapped_finite_inspect(
    const uint8_t* data,
    size_t data_size,
    uint16_t half_window,
    resonith_lapped_finite_requirements* requirements
);

/*
 * Decodes LAF1 into the ordinary sparse lapped workspace. Only scales, counts,
 * positions, and coefficients are used; overlap storage is not required.
 */
RESONITH_API resonith_status resonith_lapped_finite_decode(
    const uint8_t* data,
    size_t data_size,
    uint16_t half_window,
    const resonith_lapped_workspace* workspace
);

/*
 * Encodes one bounded unsigned-symbol field with the exact LAF1 adaptive
 * arithmetic model. The caller supplies output storage; no heap or global
 * mutable state is used. `output_size` and `bit_count` are always set on
 * success and report the canonical zero-padded field length.
 */
RESONITH_API resonith_status resonith_lapped_adaptive_encode(
    const uint16_t* symbols,
    size_t symbol_count,
    uint16_t alphabet_size,
    uint8_t* output,
    size_t output_capacity,
    size_t* output_size,
    uint32_t* bit_count
);

#ifdef __cplusplus
}
#endif

#endif
