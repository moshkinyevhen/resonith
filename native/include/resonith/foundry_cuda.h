#ifndef RESONITH_FOUNDRY_CUDA_H
#define RESONITH_FOUNDRY_CUDA_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) && defined(RESONITH_FOUNDRY_SHARED)
#if defined(RESONITH_BUILDING_FOUNDRY)
#define RESONITH_FOUNDRY_API __declspec(dllexport)
#else
#define RESONITH_FOUNDRY_API __declspec(dllimport)
#endif
#elif defined(__GNUC__) && defined(RESONITH_FOUNDRY_SHARED)
#define RESONITH_FOUNDRY_API __attribute__((visibility("default")))
#else
#define RESONITH_FOUNDRY_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*
 * R-149 Foundry status is separate from the decoder ABI: a missing accelerator
 * cannot make a Resonith stream undecodable.
 */
typedef enum resonith_foundry_status {
    RESONITH_FOUNDRY_OK = 0,
    RESONITH_FOUNDRY_INVALID_ARGUMENT = 1,
    RESONITH_FOUNDRY_OUTPUT_TOO_SMALL = 2,
    RESONITH_FOUNDRY_BACKEND_UNAVAILABLE = 3,
    RESONITH_FOUNDRY_COMPILATION_FAILED = 4,
    RESONITH_FOUNDRY_DEVICE_FAILED = 5,
    RESONITH_FOUNDRY_RANGE_OVERFLOW = 6
} resonith_foundry_status;

/*
 * One exact fixed-point result for an ordered Basis/target pair and one
 * circular source offset. The record is deliberately free of floating point.
 */
typedef struct resonith_foundry_gain_phase_result {
    uint32_t basis_index;
    uint32_t target_index;
    uint32_t source_offset;
    int32_t gain_q15;
    int32_t end_gain_q15;
    uint32_t transform_flags;
    uint64_t squared_error;
    uint64_t target_energy;
} resonith_foundry_gain_phase_result;

enum {
    RESONITH_FOUNDRY_TRANSFORM_LINEAR_GAIN = 1U,
    RESONITH_FOUNDRY_TRANSFORM_REVERSE = 2U
};

/*
 * A range is one deterministic tile of the complete declared lattice.
 * Candidate IDs enumerate every ordered unequal block pair, then every
 * circular source offset, then forward/reverse direction in ascending order.
 */
typedef struct resonith_foundry_gain_phase_range {
    uint32_t block_count;
    uint32_t block_samples;
    uint64_t first_candidate;
    uint64_t candidate_count;
} resonith_foundry_gain_phase_range;

typedef struct resonith_foundry_cuda_evidence {
    uint32_t nvrtc_major;
    uint32_t nvrtc_minor;
    uint32_t compute_major;
    uint32_t compute_minor;
    uint64_t device_memory_bytes;
    uint64_t input_bytes;
    uint64_t output_bytes;
    uint64_t first_candidate;
    uint64_t candidate_count;
    char device_name[128];
} resonith_foundry_cuda_evidence;

/*
 * Returns the complete number of discrete gain/phase candidates.
 * See Resonith decision R-149.
 */
RESONITH_FOUNDRY_API resonith_foundry_status
resonith_foundry_gain_phase_candidate_count(
    uint32_t block_count,
    uint32_t block_samples,
    uint64_t* candidate_count
);

/*
 * Portable exact reference for one tile. `blocks` is block-major PCM16.
 */
RESONITH_FOUNDRY_API resonith_foundry_status
resonith_foundry_gain_phase_cpu(
    const int16_t* blocks,
    size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    size_t output_capacity
);

/*
 * CUDA-C++23/NVRTC implementation of the identical tile.
 *
 * `nvrtc_library_directory` contains nvrtc64_130_0.dll and its builtins DLL.
 * Passing NULL requests the normal operating-system library search path.
 * Diagnostic text is always NUL-terminated when `error_capacity` is nonzero.
 */
RESONITH_FOUNDRY_API resonith_foundry_status
resonith_foundry_gain_phase_cuda(
    const int16_t* blocks,
    size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    size_t output_capacity,
    const char* nvrtc_library_directory,
    resonith_foundry_cuda_evidence* evidence,
    char* error,
    size_t error_capacity
);

RESONITH_FOUNDRY_API const char* resonith_foundry_status_string(
    resonith_foundry_status status
);

#ifdef __cplusplus
}
#endif

#endif
