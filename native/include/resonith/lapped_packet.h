#ifndef RESONITH_LAPPED_PACKET_H
#define RESONITH_LAPPED_PACKET_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/lapped.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct resonith_lapped_packet_requirements {
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t packet_frames;
    uint32_t packet_count;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t output_channels;
    uint16_t reserved;
    resonith_lapped_requirements maximum_child;
    size_t maximum_child_output_elements;
    size_t maximum_logical_output_elements;
} resonith_lapped_packet_requirements;

typedef struct resonith_lapped_packet_session {
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
} resonith_lapped_packet_session;

/*
 * Authenticates the header and every packet, validates every LPF1 child, and
 * reports maximum caller-owned storage. No PCM is written.
 */
RESONITH_API resonith_status resonith_lapped_packet_open(
    const uint8_t* data,
    size_t data_size,
    resonith_lapped_packet_session* session,
    resonith_lapped_packet_requirements* requirements
);

/*
 * Transactionally decodes one child. `child_output` holds the child including
 * context; `logical_output` receives only the central committed interval.
 */
RESONITH_API resonith_status resonith_lapped_packet_decode_next(
    resonith_lapped_packet_session* session,
    const resonith_lapped_workspace* workspace,
    int16_t* child_output,
    size_t child_output_capacity,
    int16_t* logical_output,
    size_t logical_output_capacity,
    uint32_t* logical_start,
    size_t* frames_written
);

#ifdef __cplusplus
}
#endif

#endif
