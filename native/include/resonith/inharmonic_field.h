#ifndef RESONITH_INHARMONIC_FIELD_H
#define RESONITH_INHARMONIC_FIELD_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/maf.h"
#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    RESONITH_IMF_HEADER_BYTES = 96,
    RESONITH_IMF_BASIS_BYTES = 16,
    RESONITH_IMF_MODE_BYTES = 16,
    RESONITH_IMF_INSTANCE_BYTES = 32,
    RESONITH_IMF_KNOT_BYTES = 16,
    RESONITH_IMU_HEADER_BYTES = 64,
    RESONITH_IMU_RECORD_BYTES = 32,
    RESONITH_IMU_KNOT_BYTES = 16,
    RESONITH_IMF_MAX_BASES = 8,
    RESONITH_IMF_MAX_INSTANCES = 16,
    RESONITH_IMF_MAX_MODES = 64,
    RESONITH_IMF_MAX_KNOTS = 2048,
    RESONITH_IMF_MAX_KNOTS_PER_INSTANCE = 256,
    RESONITH_IMU_MAX_RECORDS = 256,
    RESONITH_IMU_MAX_KNOTS = 32768
};

typedef struct resonith_inharmonic_inspection {
    uint32_t sample_rate;
    uint32_t sample_count;
    uint32_t basis_count;
    uint32_t mode_count;
    uint32_t instance_count;
    uint32_t knot_count;
    uint32_t truth_bytes;
    uint64_t truth_offset;
    uint64_t complete_bytes;
    uint64_t mode_samples;
} resonith_inharmonic_inspection;

RESONITH_API resonith_status resonith_imf_inspect(
    const uint8_t* data, size_t size,
    resonith_inharmonic_inspection* inspection
);

RESONITH_API resonith_status resonith_imu_inspect(
    const uint8_t* data, size_t size,
    resonith_inharmonic_inspection* inspection
);

/* Transactional model render: output and budget change only after dry-run.
   The writable output and budget ranges must not overlap the pack or Basis. */
RESONITH_API resonith_status resonith_imf_render_model(
    const uint8_t* data, size_t size, const int16_t* periodic_basis,
    size_t periodic_basis_count, int16_t* output, size_t output_capacity,
    resonith_maf_operation_budget* budget
);

RESONITH_API resonith_status resonith_imu_render_model(
    const uint8_t* data, size_t size, const int16_t* periodic_basis,
    size_t periodic_basis_count, int16_t* output, size_t output_capacity,
    resonith_maf_operation_budget* budget
);

/* Encoder-only exact search for the V5 monotone Q31 decay law. */
RESONITH_API resonith_status resonith_imf_fit_decay(
    uint16_t relative_gain_q15, const uint32_t* knot_offsets,
    const uint32_t* target_ratios_q31, size_t knot_count,
    uint32_t* decay_q31, uint64_t* work_units
);

#ifdef __cplusplus
}
#endif

#endif
