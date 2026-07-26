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

typedef struct resonith_liftpack_block_info {
    uint64_t byte_offset;
    uint64_t byte_size;
    uint32_t sample_offset;
    uint32_t bit_count;
    uint16_t sample_count;
    uint8_t transform;
    uint8_t entropy;
    uint8_t entropy_parameter;
    uint8_t lpc_order;
    uint16_t reserved;
} resonith_liftpack_block_info;

/*
 * Mutable caller-owned cursor for one forward LiftPack pass.
 *
 * The cursor borrows immutable encoded bytes. A failed decode does not advance
 * it, allowing the application to decide whether to retry, conceal, or stop.
 */
typedef struct resonith_liftpack_cursor {
    const uint8_t* data;
    size_t data_size;
    size_t byte_offset;
    uint32_t sample_offset;
    uint32_t next_block;
    resonith_liftpack_info info;
    uint8_t lpc_stream;
    uint8_t reserved[7];
} resonith_liftpack_cursor;

/*
 * Validates a LiftPack-1 or LiftPack-2 stream envelope and CRC before sizes.
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
 * Validates every block envelope and writes its byte/sample index.
 * Entry capacity must cover the block_count returned by inspect().
 * See Resonith-0 Section 6.6 and decision R-048.
 */
RESONITH_API resonith_status resonith_liftpack_index_blocks(
    const uint8_t* data,
    size_t data_size,
    resonith_liftpack_block_info* entries,
    size_t entry_capacity,
    size_t* entries_written
);

/*
 * Verifies the stream envelope and initializes a single-pass block cursor.
 * On failure, `cursor` is zeroed.
 */
RESONITH_API resonith_status resonith_liftpack_cursor_open(
    const uint8_t* data,
    size_t data_size,
    resonith_liftpack_cursor* cursor
);

/*
 * Parses and indexes exactly the next block without reconstructing samples.
 * The cursor advances only after the complete block envelope is canonical.
 */
RESONITH_API resonith_status resonith_liftpack_cursor_index_next(
    resonith_liftpack_cursor* cursor,
    resonith_liftpack_block_info* entry
);

/*
 * Parses and decodes exactly the next block in linear time.
 * Returns NOT_FOUND after the canonical final block.
 */
RESONITH_API resonith_status resonith_liftpack_cursor_decode_next(
    resonith_liftpack_cursor* cursor,
    int64_t* output,
    size_t output_capacity,
    int64_t* scratch,
    size_t scratch_count,
    uint32_t* sample_offset,
    size_t* samples_written
);

/*
 * Validates the complete stream envelope and all block envelopes, then
 * decodes one independently seeded block. On failure, both outputs are zero.
 */
RESONITH_API resonith_status resonith_liftpack_decode_block(
    const uint8_t* data,
    size_t data_size,
    uint32_t block_index,
    int64_t* output,
    size_t output_capacity,
    int64_t* scratch,
    size_t scratch_count,
    uint32_t* sample_offset,
    size_t* samples_written
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
