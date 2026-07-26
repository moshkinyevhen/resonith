#ifndef RESONITH_INTERNAL_INTEGRITY_H
#define RESONITH_INTERNAL_INTEGRITY_H

#include <array>
#include <cstddef>
#include <cstdint>

namespace resonith::internal {

std::uint32_t crc32(const std::uint8_t* data, std::size_t size) noexcept;

struct Sha256Context {
    std::array<std::uint32_t, 8> state{};
    std::array<std::uint8_t, 64> buffer{};
    std::uint64_t total_bytes = 0;
    std::size_t buffered_bytes = 0;
};

void sha256_init(Sha256Context& context) noexcept;

void sha256_update(
    Sha256Context& context,
    const std::uint8_t* data,
    std::size_t size
) noexcept;

void sha256_final(
    Sha256Context& context,
    std::uint8_t output[32]
) noexcept;

void sha256(
    const std::uint8_t* data,
    std::size_t size,
    std::uint8_t output[32]
) noexcept;

}  // namespace resonith::internal

#endif
