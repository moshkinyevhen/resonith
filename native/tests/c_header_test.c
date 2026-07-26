#include "resonith/basis.h"
#include "resonith/cibs.h"
#include "resonith/composition.h"
#include "resonith/container.h"
#include "resonith/liftpack.h"
#include "resonith/stream.h"
#include "resonith/trajectory.h"

#include <stddef.h>

int main(void) {
    resonith_container_view view = {
        NULL,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U
    };
    resonith_liftpack_info info = {0U, 0U, 0U, 0U};
    resonith_liftpack_block_info block_info = {
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U
    };
    resonith_cibs_info cibs_info = {0U, 0U, 0U, 0U};
    resonith_raw_basis_info basis_info = {0U, 0U, 0U, 0U};
    resonith_prepared_phase_trajectory trajectory = {
        NULL,
        NULL,
        NULL,
        0U,
        0U
    };
    resonith_prepared_gain_law gain_law = {NULL, NULL, 0U, 0U};
    resonith_main0_requirements requirements = {
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U,
        0U
    };
    if (
        resonith_cibs_inspect_model(NULL, NULL, &cibs_info)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_raw_basis_inspect(NULL, 0U, &basis_info)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_gain_prepare(NULL, &gain_law)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_phase_prepare(NULL, NULL, 0U, &trajectory)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_container_open(NULL, 0U, &view)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_main0_inspect(NULL, 0U, &requirements)
        != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    const resonith_status status = resonith_liftpack_inspect(
        NULL,
        0U,
        &info
    );
    if (status != RESONITH_STATUS_INVALID_ARGUMENT) {
        return 1;
    }
    size_t indexed_blocks = 99U;
    if (
        resonith_liftpack_index_blocks(
            NULL,
            0U,
            &block_info,
            1U,
            &indexed_blocks
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || indexed_blocks != 0U
    ) {
        return 1;
    }
    return resonith_status_string(status) == NULL ? 1 : 0;
}
