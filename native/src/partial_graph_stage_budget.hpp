#pragma once

#include "resonith/partial_graph.h"

#include <cstdint>
#include <limits>

namespace resonith::internal {

struct partial_graph_stage_budget final {
    std::uint64_t bytes;
    bool overflow;
    bool over_limit;
};

/*
 * Computes the complete legacy-plus-v3 publication staging budget without
 * wrapping. This is an internal arithmetic boundary; allocation and
 * publication remain owned by resonith_partial_graph_paths_cpu_v3().
 */
[[nodiscard]] constexpr partial_graph_stage_budget
checked_partial_graph_stage_budget(
    std::uint64_t path_count,
    std::uint64_t entry_count,
    std::uint64_t maximum_managed_bytes
) noexcept {
    constexpr std::uint64_t path_bytes =
        sizeof(resonith_partial_path) + sizeof(resonith_partial_path_v3);
    constexpr std::uint64_t entry_bytes =
        sizeof(resonith_partial_path_entry)
        + sizeof(resonith_partial_path_entry_v3);
    constexpr std::uint64_t maximum =
        std::numeric_limits<std::uint64_t>::max();

    std::uint64_t bytes = 0U;
    const auto add_component = [&bytes](
        std::uint64_t count,
        std::uint64_t unit_bytes
    ) constexpr noexcept {
        if (count > maximum / unit_bytes) {
            return false;
        }
        const std::uint64_t component = count * unit_bytes;
        if (component > maximum - bytes) {
            return false;
        }
        bytes += component;
        return true;
    };

    if (
        !add_component(path_count, path_bytes)
        || !add_component(entry_count, entry_bytes)
    ) {
        return {0U, true, false};
    }
    return {bytes, false, bytes > maximum_managed_bytes};
}

} // namespace resonith::internal
