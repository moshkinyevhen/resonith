#include "resonith/liftpack.h"

#include <stddef.h>

int main(void) {
    resonith_liftpack_info info = {0U, 0U, 0U, 0U};
    const resonith_status status = resonith_liftpack_inspect(
        NULL,
        0U,
        &info
    );
    if (status != RESONITH_STATUS_INVALID_ARGUMENT) {
        return 1;
    }
    return resonith_status_string(status) == NULL ? 1 : 0;
}
