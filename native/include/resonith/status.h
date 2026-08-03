#ifndef RESONITH_STATUS_H
#define RESONITH_STATUS_H

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
    RESONITH_STATUS_SCRATCH_TOO_SMALL = 9,
    RESONITH_STATUS_HASH_MISMATCH = 10,
    RESONITH_STATUS_NOT_FOUND = 11,
    RESONITH_STATUS_UNSUPPORTED_FEATURE = 12,
    RESONITH_STATUS_OUT_OF_MEMORY = 13
} resonith_status;

/* Returns a static English description and never returns NULL. */
RESONITH_API const char* resonith_status_string(resonith_status status);

#ifdef __cplusplus
}
#endif

#endif
