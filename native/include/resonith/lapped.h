#ifndef RESONITH_LAPPED_H
#define RESONITH_LAPPED_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Allocation contract for the prospective fixed/bounded LPF1 research path.
 *
 * Counts describe caller-owned arrays. The decoder owns no heap, global
 * mutable state, locks, callbacks, or floating-point state.
 */
typedef struct resonith_lapped_requirements {
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t transform_frame_count;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t coefficients_per_frame;
    uint16_t output_channels;
    size_t scale_elements;
    size_t count_elements;
    size_t position_elements;
    size_t coefficient_elements;
    size_t overlap_elements;
    size_t output_elements;
} resonith_lapped_requirements;

typedef struct resonith_lapped_workspace {
    uint8_t* scales;
    size_t scale_capacity;
    uint16_t* counts;
    size_t count_capacity;
    uint16_t* positions;
    size_t position_capacity;
    int8_t* coefficients;
    size_t coefficient_capacity;
    int64_t* overlap_q29;
    size_t overlap_capacity;
} resonith_lapped_workspace;

typedef struct resonith_lapped_analysis_requirements {
    uint32_t transform_frame_count;
    size_t scale_elements;
    size_t coefficient_elements;
    size_t score_elements;
} resonith_lapped_analysis_requirements;

/*
 * Bounded sequential renderer for one authenticated LPF1 stream.
 *
 * Entropy fields are decoded and validated once by
 * resonith_lapped_pull_open(). The session then renders only the requested
 * PCM interval, so a long recording does not require a frame-sized PCM or
 * overlap buffer before playback can begin.
 */
typedef struct resonith_lapped_pull_requirements {
    resonith_lapped_requirements field;
    uint32_t render_quantum;
    size_t maximum_output_elements;
} resonith_lapped_pull_requirements;

typedef struct resonith_lapped_pull_session {
    uint32_t sample_rate;
    uint32_t frame_count;
    uint32_t transform_frame_count;
    uint32_t next_frame;
    uint32_t render_quantum;
    uint16_t half_window;
    uint16_t band_count;
    uint16_t coefficients_per_frame;
    uint16_t output_channels;
    uint8_t variable_density;
    uint8_t reserved[3];
} resonith_lapped_pull_session;

/*
 * Computes allocation sizes for the fixed Q15/Q14 forward transform.
 * `sample_frame_count` is the number of interleaved PCM frames, not elements.
 */
RESONITH_API resonith_status resonith_lapped_analyze_requirements(
    uint32_t sample_frame_count,
    uint16_t channels,
    uint16_t half_window,
    uint16_t band_count,
    resonith_lapped_analysis_requirements* requirements
);

/*
 * Produces channel-major transform frames. Scales are [channel, frame, band];
 * quantized coefficients and squared objective scores are
 * [channel, frame, coefficient]. The function allocates no memory.
 */
RESONITH_API resonith_status resonith_lapped_analyze_pcm16(
    const int16_t* interleaved_input,
    size_t input_elements,
    uint32_t sample_frame_count,
    uint16_t channels,
    uint16_t half_window,
    uint16_t band_count,
    uint8_t* scales,
    size_t scale_capacity,
    int16_t* quantized_coefficients,
    size_t coefficient_capacity,
    uint64_t* squared_scores,
    size_t score_capacity
);

/*
 * Validates RSC1, CONF, LPF1, bounded shape arithmetic, section integrity, and
 * entropy envelope lengths without allocating or exposing PCM.
 */
RESONITH_API resonith_status resonith_lapped_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_lapped_requirements* requirements
);

/*
 * Decodes the fixed-integer, bounded-sparse LPF1 subset to interleaved PCM16.
 *
 * Every entropy field is decoded and validated before the first output write.
 * `frames_written` is zero on failure and equals frame_count on success.
 */
RESONITH_API resonith_status resonith_lapped_decode(
    const uint8_t* data,
    size_t data_size,
    const resonith_lapped_workspace* workspace,
    int16_t* output,
    size_t output_capacity,
    size_t* frames_written
);

/*
 * Reports bounded field and output storage for sequential LPF1 rendering.
 * Unlike resonith_lapped_inspect(), `field.overlap_elements` is bounded by
 * render_quantum rather than the complete recording duration.
 */
RESONITH_API resonith_status resonith_lapped_pull_inspect(
    const uint8_t* data,
    size_t data_size,
    resonith_lapped_pull_requirements* requirements
);

/*
 * Authenticates the complete stream and decodes its entropy fields into
 * caller-owned memory. No PCM synthesis is performed during open.
 */
RESONITH_API resonith_status resonith_lapped_pull_open(
    const uint8_t* data,
    size_t data_size,
    const resonith_lapped_workspace* workspace,
    resonith_lapped_pull_session* session,
    resonith_lapped_pull_requirements* requirements
);

/*
 * Renders the next sequential interval. `requested_frames` must be non-zero
 * and no larger than render_quantum. End of stream is reported by
 * frames_written == 0.
 */
RESONITH_API resonith_status resonith_lapped_pull_decode_next(
    resonith_lapped_pull_session* session,
    const resonith_lapped_workspace* workspace,
    uint32_t requested_frames,
    int16_t* output,
    size_t output_capacity,
    uint32_t* logical_start,
    size_t* frames_written
);

/*
 * Validates or decodes one direct adaptive-density LSE2 field under parameters
 * inherited from an authenticated packet envelope. The arithmetic and
 * workspace are identical to the complete LPF1 path.
 */
RESONITH_API resonith_status resonith_lapped_selected_inspect(
    const uint8_t* data,
    size_t data_size,
    uint32_t sample_rate,
    uint32_t sample_count,
    uint16_t channels,
    uint16_t half_window,
    uint16_t band_count,
    resonith_lapped_requirements* requirements
);

RESONITH_API resonith_status resonith_lapped_selected_decode(
    const uint8_t* data,
    size_t data_size,
    uint32_t sample_rate,
    uint32_t sample_count,
    uint16_t channels,
    uint16_t half_window,
    uint16_t band_count,
    const resonith_lapped_workspace* workspace,
    int16_t* output,
    size_t output_capacity,
    size_t* frames_written
);

#ifdef __cplusplus
}
#endif

#endif
