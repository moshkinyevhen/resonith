#ifndef RESONITH_CONTAINER_H
#define RESONITH_CONTAINER_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_RSC1_SECTION_CRITICAL = 1U
};

/*
 * Immutable view initialized by resonith_container_open().
 *
 * The caller owns the backing bytes and must keep them immutable and alive
 * while the view or any derived section is used. The view contains no
 * allocation and may be read concurrently by any number of threads.
 */
typedef struct resonith_container_view {
    const uint8_t* data;
    size_t data_size;
    uint32_t timebase_hz;
    uint32_t section_count;
    uint8_t version_major;
    uint8_t version_minor;
    uint8_t profile;
    uint8_t level;
} resonith_container_view;

/*
 * Zero-copy view of one structurally validated RSC1 directory record.
 *
 * Content integrity is not implied until resonith_container_verify_section()
 * succeeds. `type` is a four-byte code and is not NUL-terminated.
 */
typedef struct resonith_container_section {
    const uint8_t* payload;
    size_t payload_size;
    uint64_t start_tick;
    uint32_t instance_id;
    uint32_t expected_crc32;
    uint16_t schema_version;
    uint16_t flags;
    uint8_t type[4];
    uint8_t expected_sha256[32];
} resonith_container_section;

/*
 * Validates the fixed RSC1 header, sorted directory, canonical offsets,
 * resource bounds, and directory CRC in one allocation-free linear pass.
 */
RESONITH_API resonith_status resonith_container_open(
    const uint8_t* data,
    size_t data_size,
    resonith_container_view* view
);

/*
 * Returns a zero-copy section by canonical directory index.
 * `view` must be an unmodified result of resonith_container_open().
 */
RESONITH_API resonith_status resonith_container_get_section(
    const resonith_container_view* view,
    uint32_t index,
    resonith_container_section* section
);

/*
 * Finds the exact four-byte type and instance ID in the sorted directory.
 * Returns RESONITH_STATUS_NOT_FOUND when the key is absent.
 */
RESONITH_API resonith_status resonith_container_find_section(
    const resonith_container_view* view,
    const uint8_t type[4],
    uint32_t instance_id,
    resonith_container_section* section
);

/*
 * Recomputes both CRC-32 and SHA-256 over the stored section payload.
 * The function owns no state and is safe outside the real-time sample loop.
 */
RESONITH_API resonith_status resonith_container_verify_section(
    const resonith_container_section* section
);

#ifdef __cplusplus
}
#endif

#endif
