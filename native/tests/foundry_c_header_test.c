#include "resonith/foundry_cuda.h"

#include <stddef.h>
#include <stdint.h>

int main(void) {
    uint64_t candidate_count = 0U;
    int16_t samples[4] = {1, 2, 1, 2};
    uint64_t hashes[3] = {0U, 0U, 0U};
    uint32_t anchors[3] = {0U, 0U, 0U};
    size_t anchor_count = 0U;
    resonith_foundry_gain_phase_range range = {2U, 16U, 0U, 16U};
    resonith_foundry_warp_range warp_range = {
        2U,
        16U,
        4U,
        1U,
        512U,
        1U,
        0U,
        1U,
    };
    resonith_foundry_warp_result warp_result = {
        0U,
        1U,
        0,
        65536,
        0,
        32768,
        0,
        0U,
        0U,
        0U,
    };
    resonith_foundry_gain_phase_result result = {
        0U,
        1U,
        0U,
        32768,
        0,
        0U,
        0U,
        0U,
    };
    return (
        range.candidate_count != 16U
        || result.target_index != 1U
        || warp_result.source_step_q16 != 65536
        || resonith_foundry_warp_candidate_count(
            &warp_range,
            &candidate_count
        ) != RESONITH_FOUNDRY_OK
        || candidate_count != 2304U
        || resonith_foundry_gain_phase_candidate_count(
            2U,
            16U,
            &candidate_count
        ) != RESONITH_FOUNDRY_OK
        || candidate_count != 64U
        || resonith_foundry_rolling_hash_cpu(
            samples,
            4U,
            2U,
            hashes,
            3U
        ) != RESONITH_FOUNDRY_OK
        || hashes[0] != hashes[2]
        || resonith_foundry_winnow_cpu(
            hashes,
            3U,
            2U,
            anchors,
            3U,
            &anchor_count
        ) != RESONITH_FOUNDRY_OK
        || anchor_count == 0U
    );
}
