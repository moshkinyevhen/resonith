#ifndef RESONITH_MULTICHANNEL_H
#define RESONITH_MULTICHANNEL_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/liftpack.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_MAIN0_MAX_CHANNELS = 8
};

/*
 * Exact caller-owned memory and aligned partition requirements for the
 * independent-channel Main-0 subset. Counts are elements or PCM frames, never
 * bytes. See Resonith-0 Section 4.1.6 and decision R-052.
 */
typedef struct resonith_multichannel_requirements {
    uint32_t timebase_hz;
    uint32_t frame_count;
    uint32_t block_count;
    uint16_t block_size;
    uint16_t output_channels;
    size_t innovation_elements;
    size_t liftpack_scratch_elements;
    size_t output_elements;
    size_t output_block_elements;
} resonith_multichannel_requirements;

/*
 * Immutable allocation-free view for aligned interleaved playback.
 *
 * The caller owns `stream_data` and must keep it immutable and alive.
 * Per-channel arrays are valid only up to `output_channels`.
 */
typedef struct resonith_multichannel_player_view {
    const uint8_t* innovation_data[RESONITH_MAIN0_MAX_CHANNELS];
    size_t innovation_size[RESONITH_MAIN0_MAX_CHANNELS];
    const uint8_t* stream_data;
    size_t stream_size;
    uint32_t timebase_hz;
    uint32_t frame_count;
    uint32_t block_count;
    uint16_t block_size;
    uint16_t output_channels;
    uint32_t innovation_step;
    size_t liftpack_scratch_elements;
} resonith_multichannel_player_view;

/*
 * Mutable caller-owned pull state. It borrows immutable residual bytes through
 * its cursors and is neither thread-safe nor shared between playback heads.
 */
typedef struct resonith_multichannel_session {
    resonith_liftpack_cursor cursors[RESONITH_MAIN0_MAX_CHANNELS];
    uint32_t frame_count;
    uint32_t block_count;
    uint32_t next_block;
    uint32_t next_frame;
    uint32_t innovation_step;
    uint32_t state_tag;
    uint16_t block_size;
    uint16_t output_channels;
    size_t liftpack_scratch_elements;
} resonith_multichannel_session;

/*
 * Receives one aligned block of canonical interleaved PCM16 frames.
 * Returning a non-OK status stops delivery before the frame counter advances.
 */
typedef resonith_status (*resonith_pcm16_interleaved_callback)(
    void* user,
    uint32_t frame_offset,
    const int16_t* interleaved_samples,
    size_t frame_count,
    uint16_t channels
);

/*
 * Verifies one CONF plus one consecutive RSL2 instance per channel and reports
 * exact bounded workspace. No output pointer is retained.
 */
RESONITH_API resonith_status resonith_multichannel_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_multichannel_requirements* requirements
);

/*
 * Decodes independent channel residuals to canonical interleaved PCM16.
 *
 * `innovation_q` and `liftpack_scratch` are reused channel-by-channel, so
 * their capacities do not scale with channel count. The function preflights
 * every channel decode before writing PCM. `frames_written` is zero on failure.
 */
RESONITH_API resonith_status resonith_multichannel_decode(
    const uint8_t* data,
    size_t data_size,
    int64_t* innovation_q,
    size_t innovation_capacity,
    int64_t* liftpack_scratch,
    size_t liftpack_scratch_capacity,
    int16_t* interleaved_output,
    size_t output_capacity,
    size_t* frames_written
);

/* Opens an immutable, aligned independent-channel player view. */
RESONITH_API resonith_status resonith_multichannel_player_open(
    const uint8_t* data,
    size_t data_size,
    resonith_multichannel_player_view* view
);

/*
 * Initializes one transactional forward playback head from a verified view.
 * On failure, `session` is zeroed.
 */
RESONITH_API resonith_status resonith_multichannel_session_open(
    const resonith_multichannel_player_view* view,
    resonith_multichannel_session* session
);

/*
 * Pulls exactly one aligned interleaved block.
 *
 * Cursor advances are committed only when all channels succeed. On failure or
 * end-of-stream, both output counters are zero. NOT_FOUND denotes canonical
 * end-of-stream and is not a malformed-stream condition.
 */
RESONITH_API resonith_status resonith_multichannel_session_decode_next(
    resonith_multichannel_session* session,
    int64_t* innovation_q,
    size_t innovation_capacity,
    int64_t* liftpack_scratch,
    size_t liftpack_scratch_capacity,
    int16_t* interleaved_output,
    size_t output_capacity,
    uint32_t* frame_offset,
    size_t* frames_written
);

/*
 * Streams aligned RSL2 blocks to an interleaved callback.
 *
 * Work memory is one channel block, one maximum LiftPack scratch region, and
 * one interleaved output block. No allocation, logging, or global mutation
 * occurs in the block loop.
 */
RESONITH_API resonith_status resonith_multichannel_player_stream(
    const resonith_multichannel_player_view* view,
    int64_t* innovation_q,
    size_t innovation_capacity,
    int64_t* liftpack_scratch,
    size_t liftpack_scratch_capacity,
    int16_t* interleaved_output,
    size_t output_capacity,
    resonith_pcm16_interleaved_callback callback,
    void* user,
    size_t* frames_emitted
);

#ifdef __cplusplus
}
#endif

#endif
