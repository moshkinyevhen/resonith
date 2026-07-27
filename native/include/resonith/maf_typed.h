#ifndef RESONITH_MAF_TYPED_H
#define RESONITH_MAF_TYPED_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_MAF_TYPED_HEADER_BYTES = 64,
    RESONITH_MAF_TYPED_RECORD_HEADER_BYTES = 8,
    RESONITH_MAF_TYPED_MAX_SOURCE_LIFETIMES = 4096
};

typedef enum resonith_maf_typed_record_type {
    RESONITH_MAF_TYPED_FILTER = 1,
    RESONITH_MAF_TYPED_STOCHASTIC = 2,
    RESONITH_MAF_TYPED_SOURCE_FILTER = 3,
    RESONITH_MAF_TYPED_TRANSIENT = 4,
    RESONITH_MAF_TYPED_MIX = 5,
    RESONITH_MAF_TYPED_BASIS = 6
} resonith_maf_typed_record_type;

typedef enum resonith_maf_typed_excitation {
    RESONITH_MAF_TYPED_EXCITATION_IMPULSE = 1,
    RESONITH_MAF_TYPED_EXCITATION_STOCHASTIC = 2,
    RESONITH_MAF_TYPED_EXCITATION_PERIODIC_BASIS = 3
} resonith_maf_typed_excitation;

/*
 * Exact caller-owned memory for one validated prospective MFT1 stream.
 *
 * Counts are elements. No allocation is performed by inspect, open, or render.
 * See Resonith-0 section 14.5 and decision R-130.
 */
typedef struct resonith_maf_typed_requirements {
    uint32_t sample_rate;
    uint32_t total_frames;
    uint32_t render_quantum;
    uint32_t filter_coefficient_elements;
    uint32_t filter_history_elements;
    uint32_t planar_elements;
    uint32_t working_elements;
    uint32_t mix_matrix_elements;
    uint32_t basis_elements;
    uint32_t declared_operations_per_frame;
    uint16_t output_channels;
    uint16_t emitter_count;
    uint16_t filter_count;
    uint16_t stochastic_count;
    uint16_t source_filter_count;
    uint16_t transient_count;
    uint16_t mix_count;
    uint16_t basis_count;
} resonith_maf_typed_requirements;

/*
 * Mutable playback memory. Every region is disjoint and remains alive until
 * the session is closed. The callback performs no allocation, I/O, or locks.
 */
typedef struct resonith_maf_typed_workspace {
    int32_t* filter_coefficients_q15;
    size_t filter_coefficient_capacity;
    int16_t* bases;
    size_t basis_capacity;
    int16_t* filter_histories;
    size_t filter_history_capacity;
    int16_t* planar_sources;
    size_t planar_capacity;
    int16_t* excitation;
    size_t excitation_capacity;
    int16_t* filtered;
    size_t filtered_capacity;
    int16_t* mix_matrix_q15;
    size_t mix_matrix_capacity;
} resonith_maf_typed_workspace;

/*
 * Prepared sequential decoder view. Fields are public for C ABI stability but
 * applications SHALL treat them as opaque and mutate only through this API.
 */
typedef struct resonith_maf_typed_session {
    const uint8_t* stream_data;
    size_t stream_size;
    uint64_t stream_seed;
    uint32_t cursor;
    resonith_maf_typed_requirements requirements;
    resonith_maf_typed_workspace workspace;
} resonith_maf_typed_session;

/*
 * Verifies MFT1 integrity, canonical records, references, lifetimes, stable
 * filters, declared memory, and operation limits without retaining pointers.
 */
RESONITH_API resonith_status resonith_maf_typed_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_maf_typed_requirements* requirements
);

/*
 * Revalidates the stream, prepares stable filters into caller-owned memory,
 * clears lifetime histories, and opens an allocation-free sequential session.
 */
RESONITH_API resonith_status resonith_maf_typed_open(
    const uint8_t* data,
    size_t data_size,
    const resonith_maf_typed_workspace* workspace,
    resonith_maf_typed_session* session
);

/*
 * Renders at most one declared quantum into interleaved PCM16. The decoder
 * internally splits at exact lifetime boundaries; output is invariant under
 * caller partitioning. End of stream is reported as OK with zero frames.
 */
RESONITH_API resonith_status resonith_maf_typed_render(
    resonith_maf_typed_session* session,
    uint32_t requested_frames,
    int16_t* interleaved_output,
    size_t output_capacity,
    uint32_t* frames_written
);

#ifdef __cplusplus
}
#endif

#endif
