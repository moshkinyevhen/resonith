#ifndef RESONITH_LIFTPACK_H
#define RESONITH_LIFTPACK_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) && defined(RESONITH_SHARED)
#if defined(RESONITH_BUILDING_LIBRARY)
#define RESONITH_API __declspec(dllexport)
#else
#define RESONITH_API __declspec(dllimport)
#endif
#elif defined(__GNUC__) && defined(RESONITH_SHARED)
#define RESONITH_API __attribute__((visibility("default")))
#else
#define RESONITH_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef enum resonith_status {
    RESONITH_STATUS_OK = 0,
    RESONITH_STATUS_INVALID_ARGUMENT = 1,
    RESONITH_STATUS_TRUNCATED = 2,
    RESONITH_STATUS_BAD_MAGIC = 3,
    RESONITH_STATUS_UNSUPPORTED_VERSION = 4,
    RESONITH_STATUS_CHECKSUM_MISMATCH = 5,
    RESONITH_STATUS_PROFILE_BOUND = 6,
    RESONITH_STATUS_MALFORMED = 7,
    RESONITH_STATUS_OUTPUT_TOO_SMALL = 8,
    RESONITH_STATUS_SCRATCH_TOO_SMALL = 9
} resonith_status;

typedef struct resonith_liftpack_info {
    uint32_t sample_count;
    uint32_t block_count;
    uint16_t block_size;
    uint16_t reserved;
} resonith_liftpack_info;

/*
 * Validates the LiftPack-1 stream envelope and CRC before exposing sizes.
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

RESONITH_API const char* resonith_status_string(resonith_status status);

#ifdef __cplusplus
}
#endif

#endif
