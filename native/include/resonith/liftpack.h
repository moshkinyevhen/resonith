#ifndef RESONITH_LIFTPACK_H
#define RESONITH_LIFTPACK_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct resonith_liftpack_info {
    uint32_t sample_count;
    uint32_t block_count;
    uint16_t block_size;
    uint16_t reserved;
} resonith_liftpack_info;

/*
 * Validates the LiftPack-1 stream envelope and CRC before exposing sizes.
 * No allocation, logging, I/O, or global mutable state occurs.
 */
RESONITH_API resonith_status resonith_liftpack_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_liftpack_info* info
);

/*
 * Returns the int64 element count needed by resonith_liftpack_decode().
 * The scratch region is caller-owned so decode remains allocation-free.
 */
RESONITH_API size_t resonith_liftpack_required_scratch(
    const resonith_liftpack_info* info
);

/*
 * Decodes quantized objective residuals into caller-owned int64 storage.
 * Scratch and output must not overlap. On failure, samples_written is zero.
 */
RESONITH_API resonith_status resonith_liftpack_decode(
    const uint8_t* data,
    size_t data_size,
    int64_t* output,
    size_t output_capacity,
    int64_t* scratch,
    size_t scratch_count,
    size_t* samples_written
);

#ifdef __cplusplus
}
#endif

#endif
