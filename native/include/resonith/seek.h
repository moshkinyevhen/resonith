#ifndef RESONITH_SEEK_H
#define RESONITH_SEEK_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/liftpack.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Verified immutable view of one RSI1 sidecar and its exact LiftPack source.
 *
 * Both backing byte arrays remain caller-owned and must stay immutable and
 * alive. The sidecar is optional metadata and never changes decoded Truth.
 */
typedef struct resonith_seek_index_view {
    const uint8_t* index_data;
    size_t index_size;
    const uint8_t* source_data;
    size_t source_size;
    uint32_t sample_count;
    uint32_t block_count;
    uint16_t block_size;
    uint16_t reserved;
} resonith_seek_index_view;

/* Reports the exact RSI1 byte count for a valid bounded LiftPack source. */
RESONITH_API resonith_status resonith_seek_index_required_size(
    const uint8_t* source,
    size_t source_size,
    size_t* index_size
);

/*
 * Builds a canonical source-bound RSI1 sidecar into caller-owned bytes.
 * Source and output regions must not overlap.
 */
RESONITH_API resonith_status resonith_seek_index_build(
    const uint8_t* source,
    size_t source_size,
    uint8_t* output,
    size_t output_capacity,
    size_t* bytes_written
);

/*
 * Verifies both identities and every serialized entry against the source.
 * On failure, `view` is zeroed.
 */
RESONITH_API resonith_status resonith_seek_index_open(
    const uint8_t* index_data,
    size_t index_size,
    const uint8_t* source,
    size_t source_size,
    resonith_seek_index_view* view
);

/* Returns one fixed-size entry after a successful open. */
RESONITH_API resonith_status resonith_seek_index_get_block(
    const resonith_seek_index_view* view,
    uint32_t block_index,
    resonith_liftpack_block_info* entry
);

/*
 * Decodes one verified independently seeded block in time proportional to the
 * selected block, without scanning earlier envelopes.
 */
RESONITH_API resonith_status resonith_seek_index_decode_block(
    const resonith_seek_index_view* view,
    uint32_t block_index,
    int64_t* output,
    size_t output_capacity,
    int64_t* scratch,
    size_t scratch_count,
    uint32_t* sample_offset,
    size_t* samples_written
);

#ifdef __cplusplus
}
#endif

#endif
