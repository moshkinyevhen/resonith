#include "resonith/basis.h"
#include "resonith/cibs.h"
#include "resonith/composition.h"
#include "resonith/container.h"
#include "resonith/liftpack.h"
#include "resonith/multichannel.h"
#include "resonith/seek.h"
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
    resonith_liftpack_cursor cursor = {0};
    resonith_cibs_info cibs_info = {0U, 0U, 0U, 0U};
    resonith_cibs_registry cibs_registry = {NULL, 0U};
    resonith_cibs_basis_info cibs_basis_info = {
        NULL,
        NULL,
        NULL,
        0U,
        0U,
        0U,
        0U,
        0U
    };
    resonith_raw_basis_info basis_info = {0U, 0U, 0U, 0U};
    resonith_prepared_phase_trajectory trajectory = {
        NULL,
        NULL,
        NULL,
        0U,
        0U
    };
    resonith_prepared_gain_law gain_law = {NULL, NULL, 0U, 0U};
    resonith_main0_requirements requirements = {0};
    resonith_main0_player_view player = {0};
    resonith_multichannel_requirements multichannel_requirements = {0};
    resonith_multichannel_player_view multichannel_player = {0};
    resonith_multichannel_session multichannel_session = {0};
    resonith_seek_index_view seek_view = {
        NULL,
        0U,
        NULL,
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
        resonith_cibs_basis_inspect(
            NULL,
            0U,
            &cibs_registry,
            &cibs_basis_info
        ) != RESONITH_STATUS_INVALID_ARGUMENT
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
    if (
        resonith_multichannel_inspect(
            NULL,
            0U,
            &multichannel_requirements
        ) != RESONITH_STATUS_INVALID_ARGUMENT
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
    uint32_t block_sample_offset = 99U;
    size_t block_samples_written = 99U;
    if (
        resonith_liftpack_decode_block(
            NULL,
            0U,
            0U,
            NULL,
            0U,
            NULL,
            0U,
            &block_sample_offset,
            &block_samples_written
        ) != RESONITH_STATUS_INVALID_ARGUMENT
        || block_sample_offset != 0U
        || block_samples_written != 0U
    ) {
        return 1;
    }
    if (
        resonith_liftpack_cursor_open(NULL, 0U, &cursor)
            != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_liftpack_cursor_decode_next(
            &cursor,
            NULL,
            0U,
            NULL,
            0U,
            &block_sample_offset,
            &block_samples_written
        ) != RESONITH_STATUS_MALFORMED
    ) {
        return 1;
    }
    if (
        resonith_seek_index_open(
            NULL,
            0U,
            NULL,
            0U,
            &seek_view
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_main0_player_open(NULL, 0U, &player)
            != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_multichannel_player_open(
            NULL,
            0U,
            &multichannel_player
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_multichannel_session_open(
            NULL,
            &multichannel_session
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_main0_player_decode_block(
            &player,
            0U,
            NULL,
            0U,
            NULL,
            0U,
            NULL,
            0U,
            &block_sample_offset,
            &block_samples_written
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_main0_player_stream(
            &player,
            NULL,
            0U,
            NULL,
            0U,
            NULL,
            0U,
            NULL,
            NULL,
            &block_samples_written
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    if (
        resonith_main0_player_stream_complete(
            &player,
            NULL,
            NULL,
            0U,
            NULL,
            NULL,
            &block_samples_written
        ) != RESONITH_STATUS_INVALID_ARGUMENT
    ) {
        return 1;
    }
    return resonith_status_string(status) == NULL ? 1 : 0;
}
