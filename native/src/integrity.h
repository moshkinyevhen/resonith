#ifndef RESONITH_INTERNAL_INTEGRITY_H
#define RESONITH_INTERNAL_INTEGRITY_H

#include <cstddef>
#include <cstdint>

namespace resonith::internal {

std::uint32_t crc32(const std::uint8_t* data, std::size_t size) noexcept;

void sha256(
    const std::uint8_t* data,
    std::size_t size,
    std::uint8_t output[32]
) noexcept;

}  // namespace resonith::internal

#endif
