#ifndef RESONITH_STREAM_H
#define RESONITH_STREAM_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct resonith_stream_config {
    uint32_t sample_count;
    uint32_t innovation_step;
    uint16_t output_channels;
    uint16_t reserved;
} resonith_stream_config;

typedef struct resonith_periodic_atom_info {
    uint32_t basis_instance_id;
    uint32_t duration_samples;
    uint32_t phase_origin_q32;
    uint32_t phase_knot_count;
    uint32_t gain_event_count;
} resonith_periodic_atom_info;

/*
 * Exact caller-owned memory needed by the executable mono Main-0 subset.
 * Counts are elements, never bytes. The RSC1 timebase is the PCM sample rate.
 */
typedef struct resonith_main0_requirements {
    uint32_t timebase_hz;
    uint32_t sample_count;
    uint32_t basis_elements;
    uint32_t phase_knot_count;
    uint32_t gain_event_count;
    size_t liftpack_scratch_elements;
    uint16_t output_channels;
    uint16_t reserved;
} resonith_main0_requirements;

/*
 * Mutable decoder memory supplied by the application.
 *
 * Every region must be disjoint and remain valid for the complete call.
 * Decode performs no allocation and leaves final PCM untouched until all
 * required RSC1 sections have passed integrity and cross-section checks.
 */
typedef struct resonith_main0_workspace {
    int16_t* basis;
    size_t basis_capacity;
    uint32_t* phase_positions;
    uint32_t* phase_increments_q32;
    uint32_t* phase_origins_q32;
    size_t phase_capacity;
    uint32_t* gain_positions;
    int32_t* gains_q15;
    size_t gain_capacity;
    int16_t* unity_prediction;
    size_t unity_capacity;
    int64_t* innovation_q;
    size_t innovation_capacity;
    int64_t* liftpack_scratch;
    size_t liftpack_scratch_capacity;
} resonith_main0_workspace;

/* Parses the fixed 16-byte CONF schema-1 payload. */
RESONITH_API resonith_status resonith_stream_config_parse(
    const uint8_t* data,
    size_t data_size,
    resonith_stream_config* config
);

/* Validates ATOM schema 1 and reports exact phase/gain array sizes. */
RESONITH_API resonith_status resonith_periodic_atom_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_periodic_atom_info* info
);

/*
 * Decodes one already validated ATOM schema-1 payload to host-endian arrays.
 * All five output arrays are caller-owned; no input/output region may overlap.
 */
RESONITH_API resonith_status resonith_periodic_atom_decode(
    const uint8_t* data,
    size_t data_size,
    uint32_t* phase_positions,
    uint32_t* phase_increments_q32,
    size_t phase_capacity,
    uint32_t* gain_positions,
    int32_t* gains_q15,
    size_t gain_capacity,
    resonith_periodic_atom_info* info
);

/*
 * Opens and verifies a complete RSC1 stream, rejects unknown critical state,
 * and computes exact allocation-free decoder requirements.
 */
RESONITH_API resonith_status resonith_main0_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_main0_requirements* requirements
);

/*
 * Executes RSC1 -> Basis/Atom/Innovation -> exact mono int16 PCM.
 * See Resonith-0 sections 4.1.1, 5.1, and 5.5.
 */
RESONITH_API resonith_status resonith_main0_decode(
    const uint8_t* data,
    size_t data_size,
    resonith_main0_workspace* workspace,
    int16_t* output,
    size_t output_capacity,
    size_t* samples_written
);

#ifdef __cplusplus
}
#endif

#endif
