#include "resonith/lapped_compact.h"
#include "resonith/status.h"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct field_storage {
    std::vector<std::uint8_t> scales;
    std::vector<std::uint16_t> counts;
    std::vector<std::uint16_t> positions;
    std::vector<std::int8_t> coefficients;
    std::vector<std::int64_t> overlap;

    explicit field_storage(
        const resonith_lapped_requirements& requirements,
        bool include_overlap
    )
        : scales(std::max<std::size_t>(1U, requirements.scale_elements)),
          counts(std::max<std::size_t>(1U, requirements.count_elements)),
          positions(
              std::max<std::size_t>(1U, requirements.position_elements)
          ),
          coefficients(
              std::max<std::size_t>(1U, requirements.coefficient_elements)
          ),
          overlap(
              include_overlap
                  ? std::max<std::size_t>(
                        1U,
                        requirements.overlap_elements
                    )
                  : 0U
          ) {}

    resonith_lapped_workspace view(
        const resonith_lapped_requirements& requirements
    ) noexcept {
        return {
            scales.data(),
            requirements.scale_elements,
            counts.data(),
            requirements.count_elements,
            positions.data(),
            requirements.position_elements,
            coefficients.data(),
            requirements.coefficient_elements,
            overlap.empty() ? nullptr : overlap.data(),
            overlap.empty() ? 0U : requirements.overlap_elements,
        };
    }
};

void write_u16(std::ostream& output, std::uint16_t value) {
    const char bytes[2] = {
        static_cast<char>(value & 0xffU),
        static_cast<char>((value >> 8U) & 0xffU),
    };
    output.write(bytes, 2);
}

void write_u32(std::ostream& output, std::uint32_t value) {
    const char bytes[4] = {
        static_cast<char>(value & 0xffU),
        static_cast<char>((value >> 8U) & 0xffU),
        static_cast<char>((value >> 16U) & 0xffU),
        static_cast<char>((value >> 24U) & 0xffU),
    };
    output.write(bytes, 4);
}

void write_wave_header(
    std::ostream& output,
    std::uint32_t sample_rate,
    std::uint16_t channels,
    std::uint32_t data_bytes
) {
    output.write("RIFF", 4);
    write_u32(output, 36U + data_bytes);
    output.write("WAVEfmt ", 8);
    write_u32(output, 16U);
    write_u16(output, 1U);
    write_u16(output, channels);
    write_u32(output, sample_rate);
    write_u32(
        output,
        sample_rate * static_cast<std::uint32_t>(channels) * 2U
    );
    write_u16(output, static_cast<std::uint16_t>(channels * 2U));
    write_u16(output, 16U);
    output.write("data", 4);
    write_u32(output, data_bytes);
}

std::vector<std::uint8_t> read_file(const std::string& path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) {
        throw std::runtime_error("cannot open input");
    }
    const std::streampos end_position = input.tellg();
    if (
        end_position == std::streampos(-1)
        || end_position == std::streampos(0)
    ) {
        throw std::runtime_error("input is empty");
    }
    const std::streamoff end = end_position - std::streampos(0);
    if (end <= 0) {
        throw std::runtime_error("invalid input size");
    }
    const auto unsigned_size = static_cast<std::uintmax_t>(end);
    if (
        unsigned_size > std::numeric_limits<std::size_t>::max()
        || unsigned_size > (512U << 20U)
    ) {
        throw std::runtime_error("input exceeds the decoder ceiling");
    }
    const auto size = static_cast<std::size_t>(unsigned_size);
    std::vector<std::uint8_t> bytes(size);
    input.seekg(0, std::ios::beg);
    input.read(
        reinterpret_cast<char*>(bytes.data()),
        static_cast<std::streamsize>(size)
    );
    if (!input) {
        throw std::runtime_error("cannot read complete input");
    }
    return bytes;
}

void write_pcm16(
    std::ostream& output,
    const std::int16_t* samples,
    std::size_t element_count,
    std::vector<char>* staging
) {
    if (
        element_count
            > std::numeric_limits<std::size_t>::max() / 2U
    ) {
        throw std::runtime_error("PCM block size overflow");
    }
    staging->resize(element_count * 2U);
    for (std::size_t index = 0U; index < element_count; ++index) {
        const auto value = static_cast<std::uint16_t>(samples[index]);
        (*staging)[2U * index] =
            static_cast<char>(value & 0xffU);
        (*staging)[2U * index + 1U] =
            static_cast<char>(value >> 8U);
    }
    output.write(
        staging->data(),
        static_cast<std::streamsize>(staging->size())
    );
    if (!output) {
        throw std::runtime_error("cannot write decoded PCM");
    }
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 3) {
            std::cerr
                << "usage: resonith_decode <input.resonith> <output.wav>\n";
            return 2;
        }
        const std::vector<std::uint8_t> input = read_file(argv[1]);
        resonith_lapped_compact_session session{};
        resonith_lapped_compact_requirements requirements{};
        const resonith_status open_status = resonith_lapped_compact_open(
            input.data(),
            input.size(),
            &session,
            &requirements
        );
        if (open_status != RESONITH_STATUS_OK) {
            throw std::runtime_error(
                std::string("preflight failed: ")
                + resonith_status_string(open_status)
            );
        }
        const std::uint64_t data_bytes_64 =
            static_cast<std::uint64_t>(session.frame_count)
            * session.output_channels
            * 2U;
        if (
            data_bytes_64
            > std::numeric_limits<std::uint32_t>::max() - 36U
        ) {
            throw std::runtime_error(
                "decoded PCM exceeds the portable RIFF/WAVE limit"
            );
        }

        field_storage current(requirements.maximum_current, true);
        field_storage lookahead(requirements.maximum_lookahead, false);
        resonith_lapped_workspace current_workspace =
            current.view(requirements.maximum_current);
        resonith_lapped_workspace lookahead_workspace =
            lookahead.view(requirements.maximum_lookahead);
        std::vector<std::int16_t> pcm(
            std::max<std::size_t>(
                1U,
                requirements.maximum_logical_output_elements
            )
        );
        std::vector<char> pcm_bytes;
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        if (!output) {
            throw std::runtime_error("cannot create output");
        }
        write_wave_header(
            output,
            session.sample_rate,
            session.output_channels,
            static_cast<std::uint32_t>(data_bytes_64)
        );

        std::uint32_t expected_start = 0U;
        while (session.next_packet < session.packet_count) {
            const bool final_packet =
                session.next_packet + 1U == session.packet_count;
            std::uint32_t logical_start = 0U;
            std::size_t frames_written = 0U;
            const resonith_status status =
                resonith_lapped_compact_decode_next(
                    &session,
                    &current_workspace,
                    final_packet ? nullptr : &lookahead_workspace,
                    pcm.data(),
                    pcm.size(),
                    &logical_start,
                    &frames_written
                );
            if (
                status != RESONITH_STATUS_OK
                || logical_start != expected_start
            ) {
                throw std::runtime_error(
                    std::string("decode failed: ")
                    + resonith_status_string(status)
                );
            }
            write_pcm16(
                output,
                pcm.data(),
                frames_written * session.output_channels,
                &pcm_bytes
            );
            expected_start += static_cast<std::uint32_t>(frames_written);
        }
        if (expected_start != session.frame_count) {
            throw std::runtime_error("decoder returned partial PCM");
        }
        output.close();
        if (!output) {
            throw std::runtime_error("cannot finalize output");
        }
        std::cout
            << "{\"sample_rate\":" << session.sample_rate
            << ",\"channels\":" << session.output_channels
            << ",\"frames\":" << session.frame_count
            << ",\"wav_bytes\":" << (44U + data_bytes_64)
            << "}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "resonith_decode: " << error.what() << '\n';
        return 1;
    }
}
