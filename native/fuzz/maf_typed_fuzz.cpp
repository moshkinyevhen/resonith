#include "resonith/maf_typed.h"

#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(
    const std::uint8_t* data,
    std::size_t size
) {
    resonith_maf_typed_requirements requirements{};
    (void)resonith_maf_typed_inspect(data, size, &requirements);
    return 0;
}
