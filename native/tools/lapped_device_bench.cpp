#include "resonith/lapped_compact.h"
#include "resonith/status.h"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using clock_type = std::chrono::steady_clock;

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

    std::size_t bytes() const noexcept {
        return scales.size() * sizeof(scales[0])
            + counts.size() * sizeof(counts[0])
            + positions.size() * sizeof(positions[0])
            + coefficients.size() * sizeof(coefficients[0])
            + overlap.size() * sizeof(overlap[0]);
    }
};

struct pass_result {
    std::uint64_t pcm_hash = 0U;
    std::uint32_t frames = 0U;
    std::uint64_t deadline_misses = 0U;
};

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
        || unsigned_size
            > static_cast<std::uintmax_t>(
                std::numeric_limits<std::streamsize>::max()
            )
    ) {
        throw std::runtime_error("input is too large");
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

std::uint32_t parse_count(const char* text, const char* name) {
    try {
        const unsigned long value = std::stoul(text);
        if (
            value == 0UL
            || value > std::numeric_limits<std::uint32_t>::max()
        ) {
            throw std::runtime_error("out of range");
        }
        return static_cast<std::uint32_t>(value);
    } catch (const std::exception&) {
        throw std::runtime_error(std::string("invalid ") + name);
    }
}

double percentile(
    const std::vector<double>& sorted,
    double probability
) {
    if (sorted.empty()) {
        return 0.0;
    }
    const double position = probability
        * static_cast<double>(sorted.size() - 1U);
    const auto lower = static_cast<std::size_t>(position);
    const auto upper = std::min(lower + 1U, sorted.size() - 1U);
    const double fraction = position - static_cast<double>(lower);
    return sorted[lower] * (1.0 - fraction) + sorted[upper] * fraction;
}

void hash_pcm(
    const std::int16_t* samples,
    std::size_t count,
    std::uint64_t* hash
) noexcept {
    for (std::size_t index = 0U; index < count; ++index) {
        const auto value = static_cast<std::uint16_t>(samples[index]);
        *hash ^= static_cast<std::uint8_t>(value & 0xffU);
        *hash *= 1099511628211ULL;
        *hash ^= static_cast<std::uint8_t>(value >> 8U);
        *hash *= 1099511628211ULL;
    }
}

pass_result decode_pass(
    const resonith_lapped_compact_session& pristine,
    resonith_lapped_workspace* current_workspace,
    resonith_lapped_workspace* lookahead_workspace,
    std::vector<std::int16_t>* output,
    std::vector<double>* measured_seconds
) {
    resonith_lapped_compact_session session = pristine;
    pass_result result{1469598103934665603ULL, 0U, 0U};
    while (session.next_packet < session.packet_count) {
        const auto started = clock_type::now();
        std::uint32_t logical_start = 0U;
        std::size_t frames_written = 0U;
        const bool final_packet =
            session.next_packet + 1U == session.packet_count;
        const resonith_status status = resonith_lapped_compact_decode_next(
            &session,
            current_workspace,
            final_packet ? nullptr : lookahead_workspace,
            output->data(),
            output->size(),
            &logical_start,
            &frames_written
        );
        const auto finished = clock_type::now();
        if (status != RESONITH_STATUS_OK || logical_start != result.frames) {
            throw std::runtime_error(
                std::string("decode failed: ") + resonith_status_string(status)
            );
        }
        const double seconds =
            std::chrono::duration<double>(finished - started).count();
        if (measured_seconds != nullptr) {
            measured_seconds->push_back(seconds);
            const double deadline = static_cast<double>(frames_written)
                / static_cast<double>(session.sample_rate);
            result.deadline_misses += seconds > deadline ? 1U : 0U;
        }
        hash_pcm(
            output->data(),
            frames_written * session.output_channels,
            &result.pcm_hash
        );
        result.frames += static_cast<std::uint32_t>(frames_written);
    }
    if (result.frames != pristine.frame_count) {
        throw std::runtime_error("decoded frame count mismatch");
    }
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2 || argc > 4) {
            std::cerr
                << "usage: resonith_lapped_device_bench "
                << "<input.lps> [iterations] [warmups]\n";
            return 2;
        }
        const std::uint32_t iterations =
            argc >= 3 ? parse_count(argv[2], "iterations") : 20U;
        const std::uint32_t warmups =
            argc >= 4 ? parse_count(argv[3], "warmups") : 3U;
        const std::vector<std::uint8_t> input = read_file(argv[1]);

        resonith_lapped_compact_session pristine{};
        resonith_lapped_compact_requirements requirements{};
        const resonith_status open_status = resonith_lapped_compact_open(
            input.data(),
            input.size(),
            &pristine,
            &requirements
        );
        if (open_status != RESONITH_STATUS_OK) {
            throw std::runtime_error(
                std::string("preflight failed: ")
                + resonith_status_string(open_status)
            );
        }

        field_storage current(
            requirements.maximum_current,
            true
        );
        field_storage lookahead(
            requirements.maximum_lookahead,
            false
        );
        resonith_lapped_workspace current_workspace =
            current.view(requirements.maximum_current);
        resonith_lapped_workspace lookahead_workspace =
            lookahead.view(requirements.maximum_lookahead);
        std::vector<std::int16_t> output(
            std::max<std::size_t>(
                1U,
                requirements.maximum_logical_output_elements
            )
        );

        std::uint64_t expected_hash = 0U;
        for (std::uint32_t pass = 0U; pass < warmups; ++pass) {
            const pass_result result = decode_pass(
                pristine,
                &current_workspace,
                &lookahead_workspace,
                &output,
                nullptr
            );
            if (pass == 0U) {
                expected_hash = result.pcm_hash;
            } else if (result.pcm_hash != expected_hash) {
                throw std::runtime_error("warmup PCM hash mismatch");
            }
        }

        std::vector<double> callback_seconds;
        callback_seconds.reserve(
            static_cast<std::size_t>(iterations)
            * requirements.packet_count
        );
        std::uint64_t deadline_misses = 0U;
        for (std::uint32_t pass = 0U; pass < iterations; ++pass) {
            const pass_result result = decode_pass(
                pristine,
                &current_workspace,
                &lookahead_workspace,
                &output,
                &callback_seconds
            );
            if (expected_hash == 0U) {
                expected_hash = result.pcm_hash;
            }
            if (result.pcm_hash != expected_hash) {
                throw std::runtime_error("measured PCM hash mismatch");
            }
            deadline_misses += result.deadline_misses;
        }

        const double total_decode_seconds = std::accumulate(
            callback_seconds.begin(),
            callback_seconds.end(),
            0.0
        );
        std::sort(callback_seconds.begin(), callback_seconds.end());
        const double audio_seconds =
            static_cast<double>(requirements.frame_count)
            / static_cast<double>(requirements.sample_rate);
        const std::size_t workspace_bytes =
            current.bytes() + lookahead.bytes()
            + output.size() * sizeof(output[0]);

        std::cout << std::fixed << std::setprecision(9)
                  << "{\n"
                  << "  \"schema\": \"resonith-lapped-device-bench-1\",\n"
                  << "  \"sample_rate\": " << requirements.sample_rate
                  << ",\n"
                  << "  \"frame_count\": " << requirements.frame_count
                  << ",\n"
                  << "  \"channel_count\": "
                  << requirements.output_channels << ",\n"
                  << "  \"packet_frames\": " << requirements.packet_frames
                  << ",\n"
                  << "  \"packet_count\": " << requirements.packet_count
                  << ",\n"
                  << "  \"iterations\": " << iterations << ",\n"
                  << "  \"warmups\": " << warmups << ",\n"
                  << "  \"callback_observations\": "
                  << callback_seconds.size() << ",\n"
                  << "  \"callback_seconds_min\": "
                  << callback_seconds.front() << ",\n"
                  << "  \"callback_seconds_median\": "
                  << percentile(callback_seconds, 0.5) << ",\n"
                  << "  \"callback_seconds_p95\": "
                  << percentile(callback_seconds, 0.95) << ",\n"
                  << "  \"callback_seconds_p99\": "
                  << percentile(callback_seconds, 0.99) << ",\n"
                  << "  \"callback_seconds_max\": "
                  << callback_seconds.back() << ",\n"
                  << "  \"deadline_misses\": " << deadline_misses << ",\n"
                  << "  \"decode_realtime_speed\": "
                  << (
                         audio_seconds * static_cast<double>(iterations)
                         / total_decode_seconds
                     )
                  << ",\n"
                  << "  \"caller_workspace_bytes\": " << workspace_bytes
                  << ",\n"
                  << "  \"stream_bytes\": " << input.size() << ",\n"
                  << "  \"pcm_fnv1a64\": \""
                  << std::hex << std::setw(16) << std::setfill('0')
                  << expected_hash << std::dec << "\",\n"
                  << "  \"all_passes_exact\": true\n"
                  << "}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "resonith_lapped_device_bench: "
                  << error.what() << '\n';
        return 1;
    }
}
