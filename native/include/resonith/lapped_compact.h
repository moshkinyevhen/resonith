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

/*
 * Authenticated sequence context for independently transported LPS4 records.
 *
 * The fixed 60-byte sequence header is immutable for the lifetime of this
 * context. A transport authenticates it once, then binds every record to the
 * same context and its explicit packet index.
 */
typedef struct resonith_lapped_compact_sequence {
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t packet_frames;
    uint32_t packet_count;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t output_channels;
    uint16_t reserved;
} resonith_lapped_compact_sequence;

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
 * Validates exactly one 60-byte LPS4 sequence header and its SHA-256.
 *
 * This parser does not inspect packet records and performs no allocation.
 * SHA-256 and per-record CRC-32 detect corruption; neither authenticates an
 * untrusted transport.
 */
RESONITH_API resonith_status resonith_lapped_compact_sequence_open(
    const uint8_t* data,
    size_t data_size,
    resonith_lapped_compact_sequence* sequence
);

/*
 * Derives a conservative receiver memory ceiling from sequence context alone.
 *
 * Unlike complete-stream preflight, this operation needs no packet record and
 * therefore supports allocation before independently transported data arrives.
 */
RESONITH_API resonith_status resonith_lapped_compact_sequence_requirements(
    const resonith_lapped_compact_sequence* sequence,
    resonith_lapped_compact_requirements* requirements
);

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

/*
 * Transactionally decodes one logical LPS4 interval.
 *
 * Non-final pulls require `lookahead_workspace`; the final pull permits NULL.
 * Entropy fields and synthesis bounds are validated before any PCM write, and
 * the session advances only after the complete interval succeeds.
 */
RESONITH_API resonith_status resonith_lapped_compact_decode_next(
    resonith_lapped_compact_session* session,
    const resonith_lapped_workspace* current_workspace,
    const resonith_lapped_workspace* lookahead_workspace,
    int16_t* logical_output,
    size_t logical_output_capacity,
    uint32_t* logical_start,
    size_t* frames_written
);

/*
 * Transactionally decodes one independently framed LPS4 record.
 *
 * `packet_index` supplies the record's position in `sequence`. Every byte of
 * each supplied record must belong to that record. A non-final record requires
 * its immediate successor as lookahead; a final record forbids lookahead.
 *
 * The transport MUST authenticate the sequence context, packet index, and
 * record bytes, and MUST enforce replay policy before calling this function.
 * Record CRC-32 is only an accidental-corruption check.
 */
RESONITH_API resonith_status resonith_lapped_compact_decode_record_pair(
    const resonith_lapped_compact_sequence* sequence,
    uint32_t packet_index,
    const uint8_t* current_record,
    size_t current_record_size,
    const uint8_t* lookahead_record,
    size_t lookahead_record_size,
    const resonith_lapped_workspace* current_workspace,
    const resonith_lapped_workspace* lookahead_workspace,
    int16_t* logical_output,
    size_t logical_output_capacity,
    uint32_t* logical_start,
    size_t* frames_written
);

#ifdef __cplusplus
}
#endif

#endif
