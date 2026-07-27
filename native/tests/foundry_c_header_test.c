#include "resonith/foundry_cuda.h"

#include <stddef.h>
#include <stdint.h>

int main(void) {
    uint64_t candidate_count = 0U;
    resonith_foundry_gain_phase_range range = {2U, 16U, 0U, 16U};
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
        || resonith_foundry_gain_phase_candidate_count(
            2U,
            16U,
            &candidate_count
        ) != RESONITH_FOUNDRY_OK
        || candidate_count != 64U
    );
}
