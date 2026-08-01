/*
 * Test-only reachability witness for the retired exact-path implementation.
 *
 * R-203 inventories every stable_merge_sort_v1 instantiation even when the
 * enclosing function is no longer exported. Including the implementation in
 * this isolated executable keeps production objects unchanged while proving
 * that the legacy invocation remains syntactically and dynamically viable.
 * The empty input is intentional: the witness reaches the invocation without
 * treating its no-op accounting callback as production Class-B evidence.
 */
#include "../src/partial_graph.cpp"

#include <cstdio>

int main() {
    const resonith_partial_graph_manifest graph_manifest{};
    resonith_partial_path_manifest path_manifest{};
    path_manifest.maximum_work_units = 16U;
    path_manifest.maximum_managed_bytes = 1U;
    resonith_partial_path_report report{};
    path_output output(std::pmr::get_default_resource());

    const resonith_status status = compute_paths(
        nullptr,
        0U,
        nullptr,
        0U,
        graph_manifest,
        path_manifest,
        &report,
        &output
    );
    if (
        status != RESONITH_STATUS_OK
        || !output.paths.empty()
        || !output.entries.empty()
    ) {
        std::fprintf(
            stderr,
            "legacy helper witness failed: status=%u paths=%zu entries=%zu\n",
            static_cast<unsigned>(status),
            output.paths.size(),
            output.entries.size()
        );
        return 1;
    }
    return 0;
}
