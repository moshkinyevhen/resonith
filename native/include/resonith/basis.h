#ifndef RESONITH_BASIS_H
#define RESONITH_BASIS_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct resonith_raw_basis_info {
    uint32_t samples_per_channel;
    uint32_t total_elements;
    uint16_t channels;
    uint16_t reserved;
} resonith_raw_basis_info;

/*
 * Validates one BRAW schema-1 payload: u16 channels, zero u16 flags,
 * u32 samples/channel, then channel-major little-endian int16 samples.
 */
RESONITH_API resonith_status resonith_raw_basis_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_raw_basis_info* info
);

/* Decodes a validated BRAW payload to caller-owned host-endian int16 memory. */
RESONITH_API resonith_status resonith_raw_basis_decode(
    const uint8_t* data,
    size_t data_size,
    int16_t* output,
    size_t output_capacity,
    size_t* elements_written
);

#ifdef __cplusplus
}
#endif

#endif
