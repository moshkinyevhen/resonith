#include "resonith/lapped_finite.h"
#include "resonith/status.h"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using clock_type = std::chrono::steady_clock;

std::vector<std::uint8_t> read_file(const std::string& path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) {
        throw std::runtime_error("cannot open input");
    }
    const std::streampos end_position = input.tellg();
    if (end_position <= std::streampos(0)) {
        throw std::runtime_error("input is empty");
    }
    const std::streamoff end = end_position - std::streampos(0);
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
    const double position = probability
        * static_cast<double>(sorted.size() - 1U);
    const auto lower = static_cast<std::size_t>(position);
    const auto upper = std::min(lower + 1U, sorted.size() - 1U);
    const double fraction = position - static_cast<double>(lower);
    return sorted[lower] * (1.0 - fraction) + sorted[upper] * fraction;
}

template <typename T>
void hash_values(
    const std::vector<T>& values,
    std::size_t count,
    std::uint64_t* hash
) noexcept {
    const auto* bytes = reinterpret_cast<const std::uint8_t*>(values.data());
    const std::size_t byte_count = count * sizeof(T);
    for (std::size_t index = 0U; index < byte_count; ++index) {
        *hash ^= bytes[index];
        *hash *= 1099511628211ULL;
    }
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 4 || argc > 6) {
            std::cerr
                << "usage: resonith_lapped_finite_bench "
                << "<input.laf> <half-window> <sample-rate> "
                << "[iterations] [warmups]\n";
            return 2;
        }
        const auto half_window = static_cast<std::uint16_t>(
            parse_count(argv[2], "half-window")
        );
        const std::uint32_t sample_rate = parse_count(argv[3], "sample-rate");
        const std::uint32_t iterations =
            argc >= 5 ? parse_count(argv[4], "iterations") : 100U;
        const std::uint32_t warmups =
            argc >= 6 ? parse_count(argv[5], "warmups") : 10U;
        const std::vector<std::uint8_t> input = read_file(argv[1]);

        resonith_lapped_finite_requirements requirements{};
        const resonith_status inspect_status = resonith_lapped_finite_inspect(
            input.data(),
            input.size(),
            half_window,
            &requirements
        );
        if (inspect_status != RESONITH_STATUS_OK) {
            throw std::runtime_error(
                std::string("preflight failed: ")
                + resonith_status_string(inspect_status)
            );
        }
        std::vector<std::uint8_t> scales(requirements.scale_elements);
        std::vector<std::uint16_t> counts(requirements.count_elements);
        std::vector<std::uint16_t> positions(requirements.position_elements);
        std::vector<std::int8_t> values(requirements.coefficient_elements);
        resonith_lapped_workspace workspace = {
            scales.data(),
            scales.size(),
            counts.data(),
            counts.size(),
            positions.data(),
            positions.size(),
            values.data(),
            values.size(),
            nullptr,
            0U,
        };

        std::uint64_t expected_hash = 0U;
        std::vector<double> seconds;
        seconds.reserve(iterations);
        for (
            std::uint32_t pass = 0U;
            pass < warmups + iterations;
            ++pass
        ) {
            const auto started = clock_type::now();
            const resonith_status status = resonith_lapped_finite_decode(
                input.data(),
                input.size(),
                half_window,
                &workspace
            );
            const auto finished = clock_type::now();
            if (status != RESONITH_STATUS_OK) {
                throw std::runtime_error(
                    std::string("decode failed: ")
                    + resonith_status_string(status)
                );
            }
            std::uint64_t hash = 1469598103934665603ULL;
            hash_values(
                scales,
                requirements.scale_elements,
                &hash
            );
            hash_values(
                counts,
                requirements.count_elements,
                &hash
            );
            hash_values(
                positions,
                requirements.position_elements,
                &hash
            );
            hash_values(
                values,
                requirements.coefficient_elements,
                &hash
            );
            if (pass == 0U) {
                expected_hash = hash;
            } else if (hash != expected_hash) {
                throw std::runtime_error("decoded field hash mismatch");
            }
            if (pass >= warmups) {
                seconds.push_back(
                    std::chrono::duration<double>(finished - started).count()
                );
            }
        }
        std::sort(seconds.begin(), seconds.end());
        const double duration_seconds =
            static_cast<double>(
                requirements.transform_frame_count - 1U
            ) * static_cast<double>(half_window) / sample_rate;
        const double median = percentile(seconds, 0.50);
        const std::size_t workspace_bytes =
            requirements.scale_elements
            + 2U * requirements.count_elements
            + 2U * requirements.position_elements
            + requirements.coefficient_elements;

        std::cout
            << std::setprecision(12)
            << "{\n"
            << "  \"adaptive_stream_bytes\": " << input.size() << ",\n"
            << "  \"coefficient_elements\": "
            << requirements.coefficient_elements << ",\n"
            << "  \"duration_seconds\": " << duration_seconds << ",\n"
            << "  \"field_hash_fnv1a64\": \""
            << std::hex << expected_hash << std::dec << "\",\n"
            << "  \"gap_threshold\": " << requirements.gap_threshold << ",\n"
            << "  \"iterations\": " << iterations << ",\n"
            << "  \"maximum_ms\": " << seconds.back() * 1000.0 << ",\n"
            << "  \"median_ms\": " << median * 1000.0 << ",\n"
            << "  \"minimum_ms\": " << seconds.front() * 1000.0 << ",\n"
            << "  \"p95_ms\": " << percentile(seconds, 0.95) * 1000.0
            << ",\n"
            << "  \"p99_ms\": " << percentile(seconds, 0.99) * 1000.0
            << ",\n"
            << "  \"realtime_speed_median\": "
            << duration_seconds / median << ",\n"
            << "  \"transform_frame_count\": "
            << requirements.transform_frame_count << ",\n"
            << "  \"workspace_bytes\": " << workspace_bytes << "\n"
            << "}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
