#ifndef RESONITH_LAPPED_COMPACT_H
#define RESONITH_LAPPED_COMPACT_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/lapped.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Allocation contract for prospective LPS4, Resonith-0 section 4.1.10.
 *
 * A pull decoder owns one field workspace for the current record and one for
 * the following boundary record. The Core never allocates either workspace.
 */
typedef struct resonith_lapped_compact_requirements {
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t packet_frames;
    uint32_t packet_count;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t output_channels;
    uint16_t reserved;
    resonith_lapped_requirements maximum_current;
    resonith_lapped_requirements maximum_lookahead;
    size_t maximum_logical_output_elements;
} resonith_lapped_compact_requirements;

typedef struct resonith_lapped_compact_session {
    const uint8_t* data;
    size_t data_size;
    size_t next_offset;
    uint32_t next_packet;
    uint32_t next_frame;
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t packet_frames;
    uint32_t packet_count;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t output_channels;
    uint16_t reserved;
} resonith_lapped_compact_session;

/*
 * Fully preflights an LPS4 sequence without writing PCM or allocating memory.
 *
 * The operation verifies the sequence SHA-256, every derived record length and
 * CRC-32, canonical bit padding, inherited shape, and bounded resource
 * arithmetic. CRC-32 is not transport authentication.
 */
RESONITH_API resonith_status resonith_lapped_compact_open(
    const uint8_t* data,
    size_t data_size,
    resonith_lapped_compact_session* session,
    resonith_lapped_compact_requirements* requirements
);

#ifdef __cplusplus
}
#endif

#endif
