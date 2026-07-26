#include "integrity.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace resonith::internal {
namespace {

constexpr std::array<std::uint32_t, 64> kRoundConstants = {
    0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
    0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
    0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
    0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
    0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
    0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
    0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
    0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
    0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
    0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
    0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
    0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
    0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
    0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
    0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
    0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
};

constexpr std::uint32_t rotate_right(
    std::uint32_t value,
    unsigned count
) noexcept {
    return (value >> count) | (value << (32U - count));
}

std::uint32_t read_be32(const std::uint8_t* data) noexcept {
    return (static_cast<std::uint32_t>(data[0]) << 24U)
        | (static_cast<std::uint32_t>(data[1]) << 16U)
        | (static_cast<std::uint32_t>(data[2]) << 8U)
        | static_cast<std::uint32_t>(data[3]);
}

void write_be32(std::uint8_t* data, std::uint32_t value) noexcept {
    data[0] = static_cast<std::uint8_t>(value >> 24U);
    data[1] = static_cast<std::uint8_t>(value >> 16U);
    data[2] = static_cast<std::uint8_t>(value >> 8U);
    data[3] = static_cast<std::uint8_t>(value);
}

void compress_block(
    const std::uint8_t* block,
    std::array<std::uint32_t, 8>& state
) noexcept {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16; ++index) {
        words[index] = read_be32(block + index * 4U);
    }
    for (std::size_t index = 16; index < words.size(); ++index) {
        const std::uint32_t before_two = words[index - 2U];
        const std::uint32_t before_fifteen = words[index - 15U];
        const std::uint32_t sigma_one = rotate_right(before_two, 17U)
            ^ rotate_right(before_two, 19U)
            ^ (before_two >> 10U);
        const std::uint32_t sigma_zero = rotate_right(before_fifteen, 7U)
            ^ rotate_right(before_fifteen, 18U)
            ^ (before_fifteen >> 3U);
        words[index] = words[index - 16U]
            + sigma_zero
            + words[index - 7U]
            + sigma_one;
    }

    std::uint32_t a = state[0];
    std::uint32_t b = state[1];
    std::uint32_t c = state[2];
    std::uint32_t d = state[3];
    std::uint32_t e = state[4];
    std::uint32_t f = state[5];
    std::uint32_t g = state[6];
    std::uint32_t h = state[7];

    for (std::size_t round = 0; round < words.size(); ++round) {
        const std::uint32_t sum_one = rotate_right(e, 6U)
            ^ rotate_right(e, 11U)
            ^ rotate_right(e, 25U);
        const std::uint32_t choose = (e & f) ^ (~e & g);
        const std::uint32_t temporary_one = h
            + sum_one
            + choose
            + kRoundConstants[round]
            + words[round];
        const std::uint32_t sum_zero = rotate_right(a, 2U)
            ^ rotate_right(a, 13U)
            ^ rotate_right(a, 22U);
        const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const std::uint32_t temporary_two = sum_zero + majority;

        h = g;
        g = f;
        f = e;
        e = d + temporary_one;
        d = c;
        c = b;
        b = a;
        a = temporary_one + temporary_two;
    }

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
    state[5] += f;
    state[6] += g;
    state[7] += h;
}

}  // namespace

std::uint32_t crc32(const std::uint8_t* data, std::size_t size) noexcept {
    std::uint32_t crc = 0xffff'ffffU;
    for (std::size_t index = 0; index < size; ++index) {
        crc ^= data[index];
        for (unsigned bit = 0; bit < 8; ++bit) {
            const std::uint32_t mask = 0U - (crc & 1U);
            crc = (crc >> 1U) ^ (0xedb8'8320U & mask);
        }
    }
    return ~crc;
}

void sha256_init(Sha256Context& context) noexcept {
    context.state = {
        0x6a09e667U,
        0xbb67ae85U,
        0x3c6ef372U,
        0xa54ff53aU,
        0x510e527fU,
        0x9b05688cU,
        0x1f83d9abU,
        0x5be0cd19U,
    };
    context.buffer.fill(0U);
    context.total_bytes = 0U;
    context.buffered_bytes = 0U;
}

void sha256_update(
    Sha256Context& context,
    const std::uint8_t* data,
    std::size_t size
) noexcept {
    context.total_bytes += static_cast<std::uint64_t>(size);
    std::size_t cursor = 0U;

    if (context.buffered_bytes != 0U) {
        const std::size_t needed = 64U - context.buffered_bytes;
        const std::size_t copied = std::min(needed, size);
        if (copied != 0U) {
            std::memcpy(
                context.buffer.data() + context.buffered_bytes,
                data,
                copied
            );
        }
        context.buffered_bytes += copied;
        cursor += copied;
        if (context.buffered_bytes == 64U) {
            compress_block(context.buffer.data(), context.state);
            context.buffered_bytes = 0U;
        }
    }

    while (size - cursor >= 64U) {
        compress_block(data + cursor, context.state);
        cursor += 64U;
    }

    const std::size_t remainder = size - cursor;
    if (remainder != 0U) {
        std::memcpy(context.buffer.data(), data + cursor, remainder);
        context.buffered_bytes = remainder;
    }
}

void sha256_final(
    Sha256Context& context,
    std::uint8_t output[32]
) noexcept {
    const std::uint64_t bit_length = context.total_bytes * 8U;
    context.buffer[context.buffered_bytes] = 0x80U;
    ++context.buffered_bytes;
    if (context.buffered_bytes > 56U) {
        std::fill(
            context.buffer.begin()
                + static_cast<std::ptrdiff_t>(context.buffered_bytes),
            context.buffer.end(),
            std::uint8_t{0}
        );
        compress_block(context.buffer.data(), context.state);
        context.buffered_bytes = 0U;
    }
    std::fill(
        context.buffer.begin()
            + static_cast<std::ptrdiff_t>(context.buffered_bytes),
        context.buffer.begin() + 56,
        std::uint8_t{0}
    );
    for (unsigned index = 0; index < 8U; ++index) {
        context.buffer[63U - index] = static_cast<std::uint8_t>(
            bit_length >> (index * 8U)
        );
    }
    compress_block(context.buffer.data(), context.state);

    for (std::size_t index = 0; index < context.state.size(); ++index) {
        write_be32(output + index * 4U, context.state[index]);
    }
}

void sha256(
    const std::uint8_t* data,
    std::size_t size,
    std::uint8_t output[32]
) noexcept {
    Sha256Context context{};
    sha256_init(context);
    sha256_update(context, data, size);
    sha256_final(context, output);
}

}  // namespace resonith::internal
