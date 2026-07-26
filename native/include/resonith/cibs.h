#ifndef RESONITH_CIBS_H
#define RESONITH_CIBS_H

#include <stddef.h>
#include <stdint.h>

#include "resonith/status.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * One periodic channel-local refinement kernel. Coefficients are row-major
 * [basis_channels][kernel_width] and remain owned by the model registry.
 */
typedef struct resonith_cibs_refinement_stage {
    const int8_t* kernels;
    uint8_t kernel_width;
    uint8_t shift;
    uint16_t reserved;
} resonith_cibs_refinement_stage;

/*
 * Immutable registered CIBS synthesis model.
 *
 * Projection is row-major [channels * coarse_length][latent_elements].
 * Bias contains one int32 value per projection row. Model memory must remain
 * alive and immutable during inspection and materialization.
 */
typedef struct resonith_cibs_model {
    const uint8_t* model_id;
    size_t model_id_bytes;
    const int8_t* projection;
    const int32_t* projection_bias;
    const resonith_cibs_refinement_stage* refinement_stages;
    uint32_t basis_channels;
    uint32_t coarse_length;
    uint32_t latent_elements;
    uint8_t projection_shift;
    uint8_t refinement_stage_count;
    uint16_t reserved;
} resonith_cibs_model;

/*
 * Optional bounded low-rank projection delta.
 *
 * U is row-major [coarse_elements][rank]; V is row-major
 * [rank][latent_elements]. Both arrays are caller-owned immutable int8 data.
 */
typedef struct resonith_cibs_adapter {
    const int8_t* u;
    const int8_t* v;
    uint8_t rank;
    uint8_t inner_shift;
    uint8_t output_shift;
    uint8_t reserved;
} resonith_cibs_adapter;

typedef struct resonith_cibs_info {
    uint32_t basis_channels;
    uint32_t output_length;
    uint32_t output_elements;
    uint32_t scratch_elements;
} resonith_cibs_info;

/*
 * Validates model/adapter shapes and reports exact output and int64 scratch
 * bounds. The model descriptor is registry state, not untrusted bitstream
 * memory. No synthesis occurs.
 */
RESONITH_API resonith_status resonith_cibs_inspect_model(
    const resonith_cibs_model* model,
    const resonith_cibs_adapter* adapter,
    resonith_cibs_info* info
);

/*
 * Materializes a Basis using the CIBS-0 integer rules from Resonith-0.
 *
 * `correction` is optional int32 objective correction in channel-major output
 * order. `expected_sha256` may be NULL for analysis, but normative Basis
 * commit supplies 32 bytes. Output is not modified unless all validation and
 * the optional hash comparison succeed. `actual_sha256` and `integer_macs`
 * may be NULL. Output and scratch must not overlap.
 */
RESONITH_API resonith_status resonith_cibs_materialize(
    const resonith_cibs_model* model,
    const int8_t* latent,
    size_t latent_count,
    const resonith_cibs_adapter* adapter,
    const int32_t* correction,
    size_t correction_count,
    const uint8_t* expected_sha256,
    uint8_t* actual_sha256,
    int16_t* output,
    size_t output_capacity,
    int64_t* scratch,
    size_t scratch_count,
    uint64_t* integer_macs
);

#ifdef __cplusplus
}
#endif

#endif
