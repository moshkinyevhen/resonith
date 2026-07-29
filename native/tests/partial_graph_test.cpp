#include "resonith/partial_graph.h"
#include "partial_graph_stage_budget.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory_resource>
#include <new>
#include <vector>

namespace resonith::internal {
bool partial_graph_environmental_oom_probe() noexcept;
bool partial_graph_memory_provenance_probe() noexcept;
bool partial_graph_generation_arena_probe() noexcept;
bool partial_graph_work_ledger_probe() noexcept;
void partial_graph_set_test_upstream_resource(
    std::pmr::memory_resource *resource) noexcept;
} // namespace resonith::internal

namespace {

class fail_allocation_resource final : public std::pmr::memory_resource {
private:
  void *do_allocate(std::size_t, std::size_t) override {
    throw std::bad_alloc{};
  }

  void do_deallocate(void *, std::size_t, std::size_t) override {}

  bool
  do_is_equal(const std::pmr::memory_resource &other) const noexcept override {
    return this == &other;
  }
};

class throw_non_allocation_resource final : public std::pmr::memory_resource {
private:
  void *do_allocate(std::size_t, std::size_t) override { throw 7; }

  void do_deallocate(void *, std::size_t, std::size_t) override {}

  bool
  do_is_equal(const std::pmr::memory_resource &other) const noexcept override {
    return this == &other;
  }
};

void fail(const char *message) {
  std::fprintf(stderr, "partial_graph_test: %s\n", message);
  std::exit(1);
}

resonith_partial_observation
observation(std::uint64_t id, std::uint32_t frame, std::int64_t frequency_q20,
            std::uint32_t phase, std::uint32_t step,
            std::uint32_t amplitude_q16, std::uint32_t ownership) {
  resonith_partial_observation value{};
  value.struct_size = sizeof(value);
  value.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
  value.observation_id = id;
  value.center_sample = static_cast<std::uint64_t>(frame) * 128U;
  value.frequency_hz_q20 = frequency_q20;
  value.frequency_uncertainty_hz_q20 = 1U << 20U;
  value.phase_turn_u32 = phase;
  value.phase_step_u32 = step;
  value.normalized_amplitude_q16 = amplitude_q16;
  value.amplitude_uncertainty_q16 = 1U << 12U;
  value.phase_uncertainty_u31 = 1U << 20U;
  value.frame_index = frame;
  value.resolution_id = 7U;
  value.detector_id = -1;
  value.band_id = 3U;
  value.ownership_component = ownership;
  value.ambiguity_component = RESONITH_PARTIAL_AMBIGUITY_NONE;
  value.flags = RESONITH_PARTIAL_OBSERVATION_PHASE_USABLE |
                RESONITH_PARTIAL_OBSERVATION_LOCALLY_RESOLVABLE;
  value.protected_rank_q8 = 256;
  value.neighbor_priority_q8 = 512;
  value.potential_node_value_q8 = 1024;
  value.uncertainty_leakage_penalty_q8 = 64;
  return value;
}

} // namespace

int main() {
  if (!resonith::internal::partial_graph_environmental_oom_probe()) {
    fail("environmental allocation failure was not distinguished");
  }
  if (!resonith::internal::partial_graph_memory_provenance_probe()) {
    fail("host memory provenance counters or rollback are unsound");
  }
  if (!resonith::internal::partial_graph_generation_arena_probe()) {
    fail("generation-safe arena accepted a stale reused handle");
  }
  if (!resonith::internal::partial_graph_work_ledger_probe()) {
    fail("typed work ledger violated an event-prefix boundary");
  }
  const resonith_partial_resolution resolution{
      sizeof(resonith_partial_resolution),
      RESONITH_PARTIAL_GRAPH_ABI_VERSION,
      7U,
      1024U,
      128U,
      {0U, 0U, 0U},
  };
  resonith_partial_graph_manifest manifest{};
  manifest.struct_size = sizeof(manifest);
  manifest.abi_version = RESONITH_PARTIAL_GRAPH_ABI_VERSION;
  manifest.sample_rate = 8000U;
  manifest.resolution_count = 1U;
  manifest.gap_count = 2U;
  manifest.neighbors_per_gap = 2U;
  manifest.cycle_offset_count = 3U;
  manifest.minimum_track_observations = 4U;
  manifest.maximum_frequency_jump_hz_q20 = 80LL << 20U;
  manifest.maximum_frequency_slope_hz_per_sample_q20 = 1LL << 16U;
  manifest.continuation_base_bits_q8 = 12 * 256;
  manifest.continuation_reward_q8 = 12 * 256;
  manifest.score_saturation = (1LL << 31U) - 1LL;
  manifest.maximum_edge_records = 1024U;
  manifest.maximum_path_hypotheses = 128U;
  manifest.exact_set_candidate_limit = 20U;
  manifest.gaps[0] = 1U;
  manifest.gaps[1] = 2U;
  manifest.cycle_offsets[0] = -1;
  manifest.cycle_offsets[1] = 0;
  manifest.cycle_offsets[2] = 1;

  const std::uint32_t step_440 =
      static_cast<std::uint32_t>((440ULL << 32U) / manifest.sample_rate);
  const std::uint32_t step_442 =
      static_cast<std::uint32_t>((442ULL << 32U) / manifest.sample_rate);
  std::array<resonith_partial_observation, 5> observations{
      observation(10U, 0U, 440LL << 20U, 0x10000000U, step_440, 12000U << 16U,
                  0U),
      observation(11U, 1U, 441LL << 20U, 0x1ccccccdU, step_440, 11800U << 16U,
                  1U),
      observation(12U, 1U, 900LL << 20U, 0x20000000U, 0x1ccccccdU, 4000U << 16U,
                  2U),
      observation(13U, 2U, 442LL << 20U, 0x2999999aU, step_442, 11600U << 16U,
                  3U),
      observation(14U, 2U, 1500LL << 20U, 0x30000000U, 0x4ccccccdU,
                  2000U << 16U, 4U),
  };

  std::size_t required = 0U;
  if (resonith_partial_graph_edges_cpu(&resolution, 1U, observations.data(),
                                       observations.size(), &manifest, nullptr,
                                       0U, &required) != RESONITH_STATUS_OK ||
      required != 9U) {
    fail("unexpected canonical edge cardinality");
  }
  std::vector<resonith_partial_edge> edge_canary(required);
  std::memset(edge_canary.data(), 0xa5,
              edge_canary.size() * sizeof(resonith_partial_edge));
  const auto edge_canary_before = edge_canary;
  std::size_t rejected_edge_count = 0U;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &manifest,
          edge_canary.data(), required - 1U,
          &rejected_edge_count) != RESONITH_STATUS_OUTPUT_TOO_SMALL ||
      rejected_edge_count != required ||
      std::memcmp(edge_canary.data(), edge_canary_before.data(),
                  edge_canary.size() * sizeof(resonith_partial_edge)) != 0) {
    fail("R-190 capacity failure partially wrote semantic output");
  }
  resonith_partial_graph_manifest oversized_manifest = manifest;
  oversized_manifest.maximum_edge_records =
      std::numeric_limits<std::uint64_t>::max();
  const std::size_t count_canary =
      std::numeric_limits<std::size_t>::max() - 17U;
  rejected_edge_count = count_canary;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(),
          &oversized_manifest, edge_canary.data(), edge_canary.size(),
          &rejected_edge_count) != RESONITH_STATUS_PROFILE_BOUND ||
      rejected_edge_count != count_canary ||
      std::memcmp(edge_canary.data(), edge_canary_before.data(),
                  edge_canary.size() * sizeof(resonith_partial_edge)) != 0) {
    fail("R-190 managed-byte overflow was not rejected transactionally");
  }
  std::size_t overlap_count = count_canary;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &manifest,
          reinterpret_cast<resonith_partial_edge *>(observations.data()), 1U,
          &overlap_count) != RESONITH_STATUS_INVALID_ARGUMENT ||
      overlap_count != count_canary) {
    fail("R-190 overlapping input/output ranges were not rejected");
  }
  resonith_partial_graph_manifest empty_manifest = manifest;
  std::size_t empty_count = 99U;
  if (resonith_partial_graph_edges_cpu(&resolution, 1U, nullptr, 0U,
                                       &empty_manifest, nullptr, 0U,
                                       &empty_count) != RESONITH_STATUS_OK ||
      empty_count != 0U) {
    fail("R-190 empty bounded snapshot preflight failed");
  }
  std::vector<resonith_partial_edge> first(required);
  std::vector<resonith_partial_edge> second(required);
  std::size_t first_count = 0U;
  std::size_t second_count = 0U;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &manifest,
          first.data(), first.size(), &first_count) != RESONITH_STATUS_OK ||
      resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &manifest,
          second.data(), second.size(), &second_count) != RESONITH_STATUS_OK ||
      first_count != required || second_count != required) {
    fail("native edge scoring failed");
  }
  for (std::size_t index = 0U; index < required; ++index) {
    const resonith_partial_edge &left = first[index];
    const resonith_partial_edge &right = second[index];
    if (left.candidate_id != index || left.candidate_id != right.candidate_id ||
        left.source_observation_id != right.source_observation_id ||
        left.target_observation_id != right.target_observation_id ||
        left.continuity_cost_q8 != right.continuity_cost_q8 ||
        left.provisional_program_cost_q8 != right.provisional_program_cost_q8 ||
        left.phase_error_u31 != right.phase_error_u31) {
      fail("candidate order or score is not deterministic");
    }
  }
  if (first[0].source_observation_id != 10U ||
      first[0].target_observation_id != 11U || first[0].cycle_offset != -1 ||
      first[1].cycle_offset != 0 || first[2].cycle_offset != 1) {
    fail("candidate ID formula changed");
  }

  for (resonith_partial_observation &item : observations) {
    if (item.observation_id == 10U || item.observation_id == 11U ||
        item.observation_id == 13U) {
      item.flags |= RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK;
    }
  }
  resonith_partial_path_manifest path_manifest{};
  path_manifest.struct_size = sizeof(path_manifest);
  path_manifest.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
  path_manifest.second_order_law_version = 2U;
  path_manifest.protected_band_count = 4U;
  path_manifest.k_value_per_state = 8U;
  path_manifest.k_continuity_per_state = 8U;
  path_manifest.top_k_value = 8U;
  path_manifest.top_k_continuity = 8U;
  path_manifest.top_k_protected = 8U;
  path_manifest.protected_paths_per_band = 2U;
  path_manifest.minimum_path_observations = 3U;
  path_manifest.maximum_path_observations = 4096U;
  path_manifest.exact_set_candidate_limit = 20U;
  path_manifest.amplitude_floor_q16 = 1U;
  path_manifest.amplitude_residual_weight_q8 = 4U << 8U;
  path_manifest.frequency_sigma_floor_hz_q20 = 1U << 19U;
  path_manifest.birth_cost_bits_q8 = 48LL << 8U;
  path_manifest.death_cost_bits_q8 = 8LL << 8U;
  path_manifest.score_saturation = (1LL << 62U) - 1LL;
  path_manifest.maximum_path_records = 24U;
  path_manifest.maximum_total_entries = 1'000'000U;
  path_manifest.maximum_frontier_states = 250'000U;
  path_manifest.maximum_state_records = 1'000'000U;
  path_manifest.maximum_work_units = 10'000'000U;
  path_manifest.maximum_managed_bytes = 2ULL << 30U;
  path_manifest.protected_band_upper_hz_q20[0] = 500LL << 20U;
  path_manifest.protected_band_upper_hz_q20[1] = 1000LL << 20U;
  path_manifest.protected_band_upper_hz_q20[2] = 2000LL << 20U;

  resonith_partial_path_report retired_v2_report{};
  retired_v2_report.struct_size = sizeof(retired_v2_report);
  retired_v2_report.abi_version = RESONITH_PARTIAL_PATH_ABI_VERSION;
  const resonith_partial_path_report retired_v2_before = retired_v2_report;
  if (resonith_partial_graph_paths_cpu_v2(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest, nullptr, 0U,
          nullptr, 0U,
          &retired_v2_report) != RESONITH_STATUS_UNSUPPORTED_VERSION ||
      std::memcmp(&retired_v2_report, &retired_v2_before,
                  sizeof(retired_v2_report)) != 0) {
    fail("retired R-191 v2 ABI was not a no-write safe stub");
  }

  resonith_partial_path_manifest_v3 path_manifest_v3{};
  std::memcpy(&path_manifest_v3, &path_manifest, 144U);
  path_manifest_v3.struct_size = sizeof(path_manifest_v3);
  path_manifest_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  path_manifest_v3.work_ledger_version =
      RESONITH_PARTIAL_PATH_WORK_LEDGER_VERSION;
  path_manifest_v3.maximum_device_bytes = RESONITH_PARTIAL_MAX_DEVICE_BYTES;
  std::copy(std::begin(path_manifest.protected_band_upper_hz_q20),
            std::end(path_manifest.protected_band_upper_hz_q20),
            path_manifest_v3.protected_band_upper_hz_q20);
  resonith_partial_path_report_v3 report_v3{};
  report_v3.struct_size = sizeof(report_v3);
  report_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest_v3, nullptr, 0U,
          nullptr, 0U, &report_v3) != RESONITH_STATUS_OK ||
      report_v3.required_path_count != 8U ||
      report_v3.required_entry_count != 24U ||
      report_v3.work_event_counts[18] != 33U ||
      report_v3.work_event_counts[19] != 1U ||
      report_v3.reserved_host_bytes == 0U ||
      report_v3.reserved_host_bytes < report_v3.committed_host_bytes ||
      report_v3.committed_host_bytes < report_v3.peak_live_host_bytes ||
      report_v3.peak_live_host_bytes > path_manifest_v3.maximum_managed_bytes ||
      report_v3.reserved_device_bytes != 0U ||
      report_v3.committed_device_bytes != 0U ||
      report_v3.peak_live_device_bytes != 0U ||
      report_v3.work_event_counts[RESONITH_PARTIAL_WORK_CUDA_ITEM] != 0U) {
    fail("R-197 v3 transactional preflight failed");
  }
  fail_allocation_resource failed_upstream;
  resonith::internal::partial_graph_set_test_upstream_resource(
      &failed_upstream);
  resonith_partial_path_report_v3 oom_v3{};
  oom_v3.struct_size = sizeof(oom_v3);
  oom_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const resonith_status oom_status = resonith_partial_graph_paths_cpu_v3(
      &resolution, 1U, observations.data(), observations.size(), first.data(),
      first.size(), &manifest, &path_manifest_v3, nullptr, 0U, nullptr, 0U,
      &oom_v3);
  resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
  if (oom_status != RESONITH_STATUS_OUT_OF_MEMORY ||
      oom_v3.termination !=
          RESONITH_PARTIAL_PATH_TERMINATION_ENVIRONMENTAL_OOM ||
      oom_v3.reserved_host_bytes == 0U || oom_v3.committed_host_bytes != 0U ||
      oom_v3.peak_live_host_bytes != 0U || oom_v3.reserved_device_bytes != 0U ||
      oom_v3.committed_device_bytes != 0U ||
      oom_v3.peak_live_device_bytes != 0U) {
    std::fprintf(
        stderr,
        "R-201 OOM status=%u termination=%u host=%llu/%llu/%llu "
        "device=%llu/%llu/%llu\n",
        static_cast<unsigned>(oom_status),
        static_cast<unsigned>(oom_v3.termination),
        static_cast<unsigned long long>(oom_v3.reserved_host_bytes),
        static_cast<unsigned long long>(oom_v3.committed_host_bytes),
        static_cast<unsigned long long>(oom_v3.peak_live_host_bytes),
        static_cast<unsigned long long>(oom_v3.reserved_device_bytes),
        static_cast<unsigned long long>(oom_v3.committed_device_bytes),
        static_cast<unsigned long long>(oom_v3.peak_live_device_bytes));
    fail("R-201 environmental OOM provenance report is not exact");
  }

  resonith_partial_path_report_v3 invalid_header_v3{};
  invalid_header_v3.struct_size = 0U;
  invalid_header_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto invalid_header_before = invalid_header_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest_v3, nullptr, 0U,
          nullptr, 0U,
          &invalid_header_v3) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(&invalid_header_v3, &invalid_header_before,
                  sizeof(invalid_header_v3)) != 0) {
    fail("R-197 precedence row 1 modified an invalid report");
  }

  resonith_partial_path_report_v3 overflow_v3{};
  overflow_v3.struct_size = sizeof(overflow_v3);
  overflow_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto overflow_before = overflow_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(),
          std::numeric_limits<std::size_t>::max(), first.data(), first.size(),
          &manifest, &path_manifest_v3, nullptr, 0U, nullptr, 0U,
          &overflow_v3) != RESONITH_STATUS_PROFILE_BOUND ||
      std::memcmp(&overflow_v3, &overflow_before, sizeof(overflow_v3)) != 0) {
    fail("R-197 precedence row 2 did not preserve the report");
  }

  auto overlap_manifest_v3 = path_manifest_v3;
  const auto overlap_manifest_before = overlap_manifest_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &overlap_manifest_v3, nullptr,
          0U, nullptr, 0U,
          reinterpret_cast<resonith_partial_path_report_v3 *>(
              &overlap_manifest_v3)) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(&overlap_manifest_v3, &overlap_manifest_before,
                  sizeof(overlap_manifest_v3)) != 0) {
    fail("R-197 precedence row 3 did not reject overlap transactionally");
  }

  auto reserved_manifest_v3 = path_manifest_v3;
  reserved_manifest_v3.reserved[0] = 1U;
  resonith_partial_path_report_v3 reserved_v3{};
  reserved_v3.struct_size = sizeof(reserved_v3);
  reserved_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto reserved_before = reserved_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &reserved_manifest_v3, nullptr,
          0U, nullptr, 0U, &reserved_v3) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(&reserved_v3, &reserved_before, sizeof(reserved_v3)) != 0) {
    fail("R-197 precedence row 4 modified the report");
  }

  auto hard_manifest_v3 = path_manifest_v3;
  hard_manifest_v3.maximum_path_records =
      RESONITH_PARTIAL_PATH_MAX_RECORDS + 1ULL;
  resonith_partial_path_report_v3 hard_v3{};
  hard_v3.struct_size = sizeof(hard_v3);
  hard_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto hard_before = hard_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &hard_manifest_v3, nullptr, 0U,
          nullptr, 0U, &hard_v3) != RESONITH_STATUS_PROFILE_BOUND ||
      std::memcmp(&hard_v3, &hard_before, sizeof(hard_v3)) != 0) {
    fail("R-197 precedence row 5 modified the report");
  }

  resonith_partial_path_report_v3 invalid_overflow_v3{};
  invalid_overflow_v3.struct_size = 0U;
  invalid_overflow_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto invalid_overflow_before = invalid_overflow_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(),
          std::numeric_limits<std::size_t>::max(), first.data(), first.size(),
          &manifest, &path_manifest_v3, nullptr, 0U, nullptr, 0U,
          &invalid_overflow_v3) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(&invalid_overflow_v3, &invalid_overflow_before,
                  sizeof(invalid_overflow_v3)) != 0) {
    fail("R-197 precedence row 1 did not beat row 2");
  }

  auto reserved_hard_manifest_v3 = hard_manifest_v3;
  reserved_hard_manifest_v3.reserved[0] = 1U;
  resonith_partial_path_report_v3 reserved_hard_v3{};
  reserved_hard_v3.struct_size = sizeof(reserved_hard_v3);
  reserved_hard_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const auto reserved_hard_before = reserved_hard_v3;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &reserved_hard_manifest_v3,
          nullptr, 0U, nullptr, 0U,
          &reserved_hard_v3) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(&reserved_hard_v3, &reserved_hard_before,
                  sizeof(reserved_hard_v3)) != 0) {
    fail("R-197 precedence row 4 did not beat row 5");
  }

  std::vector<resonith_partial_path_v3> paths_v3(report_v3.required_path_count);
  std::vector<resonith_partial_path_entry_v3> entries_v3(
      report_v3.required_entry_count);
  const std::uint64_t canary = 0x5a5aa5a55a5aa5a5ULL;
  paths_v3[0].path_id = canary;
  entries_v3[0].incoming_edge_candidate_id = canary;
  resonith_partial_path_report_v3 no_fingerprint_v3{};
  no_fingerprint_v3.struct_size = sizeof(no_fingerprint_v3);
  no_fingerprint_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest_v3,
          paths_v3.data(), 1U, entries_v3.data(), entries_v3.size(),
          &no_fingerprint_v3) != RESONITH_STATUS_INVALID_ARGUMENT ||
      paths_v3[0].path_id != canary ||
      entries_v3[0].incoming_edge_candidate_id != canary ||
      no_fingerprint_v3
              .work_event_counts[RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE] !=
          0U ||
      std::any_of(std::begin(no_fingerprint_v3.input_fingerprint),
                  std::end(no_fingerprint_v3.input_fingerprint),
                  [](std::uint64_t item) { return item != 0U; })) {
    fail("R-199 missing identity did not precede fingerprint transactionally");
  }
  std::copy(std::begin(report_v3.input_fingerprint),
            std::end(report_v3.input_fingerprint),
            path_manifest_v3.expected_input_fingerprint);
  report_v3 = {};
  report_v3.struct_size = sizeof(report_v3);
  report_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest_v3,
          paths_v3.data(), paths_v3.size(), entries_v3.data(),
          entries_v3.size(), &report_v3) != RESONITH_STATUS_OK ||
      report_v3.written_path_count != 8U ||
      report_v3.written_entry_count != 24U ||
      report_v3.reserved_host_bytes < report_v3.committed_host_bytes ||
      report_v3.committed_host_bytes < report_v3.peak_live_host_bytes ||
      report_v3.reserved_device_bytes != 0U ||
      report_v3.committed_device_bytes != 0U ||
      report_v3.peak_live_device_bytes != 0U ||
      report_v3.work_event_counts[RESONITH_PARTIAL_WORK_CUDA_ITEM] != 0U ||
      paths_v3[0].abi_version != RESONITH_PARTIAL_PATH_V3_ABI_VERSION ||
      entries_v3[0].abi_version != RESONITH_PARTIAL_PATH_V3_ABI_VERSION) {
    fail("R-197 v3 transactional fill failed");
  }
  const auto paths_v3_before = paths_v3;
  const auto entries_v3_before = entries_v3;
  resonith_partial_path_report_v3 small_v3{};
  small_v3.struct_size = sizeof(small_v3);
  small_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest, &path_manifest_v3,
          paths_v3.data(), 1U, entries_v3.data(), entries_v3.size(),
          &small_v3) != RESONITH_STATUS_OUTPUT_TOO_SMALL ||
      std::memcmp(paths_v3.data(), paths_v3_before.data(),
                  paths_v3.size() * sizeof(resonith_partial_path_v3)) != 0 ||
      std::memcmp(entries_v3.data(), entries_v3_before.data(),
                  entries_v3.size() * sizeof(resonith_partial_path_entry_v3)) !=
          0) {
    fail("R-197 v3 capacity failure published partial payload");
  }

  auto changed_observations = observations;
  ++changed_observations[0].potential_node_value_q8;
  resonith_partial_path_report_v3 changed_input_v3{};
  changed_input_v3.struct_size = sizeof(changed_input_v3);
  changed_input_v3.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, changed_observations.data(),
          changed_observations.size(), first.data(), first.size(), &manifest,
          &path_manifest_v3, paths_v3.data(), 1U, entries_v3.data(),
          entries_v3.size(),
          &changed_input_v3) != RESONITH_STATUS_HASH_MISMATCH ||
      changed_input_v3.termination !=
          RESONITH_PARTIAL_PATH_TERMINATION_STALE_INPUT ||
      changed_input_v3
              .work_event_counts[RESONITH_PARTIAL_WORK_FINGERPRINT_BYTE] ==
          0U ||
      std::equal(std::begin(changed_input_v3.input_fingerprint),
                 std::end(changed_input_v3.input_fingerprint),
                 std::begin(path_manifest_v3.expected_input_fingerprint)) ||
      std::memcmp(paths_v3.data(), paths_v3_before.data(),
                  paths_v3.size() * sizeof(resonith_partial_path_v3)) != 0 ||
      std::memcmp(entries_v3.data(), entries_v3_before.data(),
                  entries_v3.size() * sizeof(resonith_partial_path_entry_v3)) !=
          0) {
    fail("R-199 stale identity lacked the actual canonical fingerprint");
  }

  resonith_partial_graph_manifest invalid = manifest;
  invalid.sample_rate = 384001U;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &invalid,
          nullptr, 0U, &required) != RESONITH_STATUS_INVALID_ARGUMENT) {
    fail("invalid maximum sample rate was accepted");
  }
  invalid = manifest;
  invalid.maximum_edge_records = 2U;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &invalid,
          nullptr, 0U, &required) != RESONITH_STATUS_PROFILE_BOUND) {
    fail("edge-cardinality bound did not stop enumeration");
  }

  /*
   * R-202 exact ABI decision matrix. Each row flips one public condition
   * while the canonical fixture remains unchanged. This is deliberately
   * separate from randomized fuzzing: every short-circuit leaf has a named,
   * deterministic witness that survives corpus minimization.
   */
  enum class r190_topology_case {
    null_resolutions,
    zero_resolution_count,
    null_observations_with_count,
    null_manifest,
    null_output_count,
    null_output_with_capacity,
  };
  constexpr std::array r190_topology_cases{
      r190_topology_case::null_resolutions,
      r190_topology_case::zero_resolution_count,
      r190_topology_case::null_observations_with_count,
      r190_topology_case::null_manifest,
      r190_topology_case::null_output_count,
      r190_topology_case::null_output_with_capacity,
  };
  for (const r190_topology_case row : r190_topology_cases) {
    const resonith_partial_resolution *row_resolutions = &resolution;
    std::size_t row_resolution_count = 1U;
    const resonith_partial_observation *row_observations = observations.data();
    std::size_t row_observation_count = observations.size();
    const resonith_partial_graph_manifest *row_manifest = &manifest;
    resonith_partial_edge *row_output = nullptr;
    std::size_t row_output_capacity = 0U;
    std::size_t row_count = 0x55aaU;
    std::size_t *row_count_pointer = &row_count;
    switch (row) {
    case r190_topology_case::null_resolutions:
      row_resolutions = nullptr;
      break;
    case r190_topology_case::zero_resolution_count:
      row_resolution_count = 0U;
      break;
    case r190_topology_case::null_observations_with_count:
      row_observations = nullptr;
      row_observation_count = 1U;
      break;
    case r190_topology_case::null_manifest:
      row_manifest = nullptr;
      break;
    case r190_topology_case::null_output_count:
      row_count_pointer = nullptr;
      break;
    case r190_topology_case::null_output_with_capacity:
      row_output_capacity = 1U;
      break;
    }
    if (resonith_partial_graph_edges_cpu(
            row_resolutions, row_resolution_count, row_observations,
            row_observation_count, row_manifest, row_output,
            row_output_capacity,
            row_count_pointer) != RESONITH_STATUS_INVALID_ARGUMENT ||
        (row_count_pointer != nullptr &&
         row_count != static_cast<std::size_t>(0x55aaU))) {
      fail("R-202 R-190 pointer-topology matrix failed");
    }
  }

  alignas(std::size_t) std::array<std::byte, sizeof(std::size_t) + 1U>
      misaligned_count_bytes{};
  std::size_t matrix_count = 0x55aaU;
  if (resonith_partial_graph_edges_cpu(
          &resolution, 1U, observations.data(), observations.size(), &manifest,
          nullptr, 0U,
          reinterpret_cast<std::size_t *>(misaligned_count_bytes.data() +
                                          1U)) !=
      RESONITH_STATUS_INVALID_ARGUMENT) {
    fail("R-202 R-190 invalid byte range was not rejected");
  }
  if constexpr (sizeof(std::uintptr_t) >= sizeof(std::uint64_t)) {
    constexpr std::uintptr_t high_aligned_address =
        std::numeric_limits<std::uintptr_t>::max() &
        ~static_cast<std::uintptr_t>(alignof(resonith_partial_observation) -
                                     1U);
    matrix_count = 0x55aaU;
    if (resonith_partial_graph_edges_cpu(
            &resolution, 1U,
            reinterpret_cast<const resonith_partial_observation *>(
                high_aligned_address),
            1U, &manifest, nullptr, 0U,
            &matrix_count) != RESONITH_STATUS_PROFILE_BOUND ||
        matrix_count != static_cast<std::size_t>(0x55aaU)) {
      fail("R-202 R-190 overflowing byte range was not rejected");
    }

    constexpr std::uintptr_t synthetic_resolution_address =
        UINT64_C(0x0000100000000000);
    constexpr std::uintptr_t synthetic_observation_address =
        UINT64_C(0x0000200000000000);
    constexpr std::uintptr_t synthetic_output_address =
        UINT64_C(0x0000300000000000);
    struct r190_cap_case {
      std::size_t resolution_count;
      std::size_t observation_count;
      std::size_t output_capacity;
    };
    constexpr std::array r190_cap_cases{
        r190_cap_case{
            RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS + 1U,
            0U,
            0U,
        },
        r190_cap_case{
            1U,
            RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS + 1U,
            0U,
        },
        r190_cap_case{
            1U,
            0U,
            RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS + 1U,
        },
    };
    for (const r190_cap_case &row : r190_cap_cases) {
      matrix_count = 0x55aaU;
      const bool oversized_resolution = row.resolution_count != 1U;
      const bool oversized_observation = row.observation_count != 0U;
      const bool oversized_output = row.output_capacity != 0U;
      if (resonith_partial_graph_edges_cpu(
              oversized_resolution
                  ? reinterpret_cast<const resonith_partial_resolution *>(
                        synthetic_resolution_address)
                  : &resolution,
              row.resolution_count,
              oversized_observation
                  ? reinterpret_cast<const resonith_partial_observation *>(
                        synthetic_observation_address)
                  : nullptr,
              row.observation_count, &manifest,
              oversized_output ? reinterpret_cast<resonith_partial_edge *>(
                                     synthetic_output_address)
                               : nullptr,
              row.output_capacity,
              &matrix_count) != RESONITH_STATUS_PROFILE_BOUND ||
          matrix_count != static_cast<std::size_t>(0x55aaU)) {
        fail("R-202 R-190 hard-cap matrix failed");
      }
    }
  }

  for (const bool damage_size : {true, false}) {
    resonith_partial_graph_manifest bad_header = manifest;
    if (damage_size) {
      --bad_header.struct_size;
    } else {
      ++bad_header.abi_version;
    }
    matrix_count = 0x55aaU;
    if (resonith_partial_graph_edges_cpu(&resolution, 1U, observations.data(),
                                         observations.size(), &bad_header,
                                         nullptr, 0U, &matrix_count) !=
            RESONITH_STATUS_INVALID_ARGUMENT ||
        matrix_count != static_cast<std::size_t>(0x55aaU)) {
      fail("R-202 R-190 manifest-header matrix failed");
    }
  }

  enum class v3_topology_case {
    null_resolutions,
    zero_resolution_count,
    null_observations_with_count,
    null_observations_without_count,
    null_edges_with_count,
    null_edges_without_count,
    null_graph_manifest,
    null_path_manifest,
    null_report,
    path_without_entries,
    entries_without_path,
    null_payload_with_path_capacity,
    null_payload_with_entry_capacity,
  };
  constexpr std::array v3_topology_cases{
      v3_topology_case::null_resolutions,
      v3_topology_case::zero_resolution_count,
      v3_topology_case::null_observations_with_count,
      v3_topology_case::null_observations_without_count,
      v3_topology_case::null_edges_with_count,
      v3_topology_case::null_edges_without_count,
      v3_topology_case::null_graph_manifest,
      v3_topology_case::null_path_manifest,
      v3_topology_case::null_report,
      v3_topology_case::path_without_entries,
      v3_topology_case::entries_without_path,
      v3_topology_case::null_payload_with_path_capacity,
      v3_topology_case::null_payload_with_entry_capacity,
  };
  for (const v3_topology_case row : v3_topology_cases) {
    const resonith_partial_resolution *row_resolutions = &resolution;
    std::size_t row_resolution_count = 1U;
    const resonith_partial_observation *row_observations = observations.data();
    std::size_t row_observation_count = observations.size();
    const resonith_partial_edge *row_edges = first.data();
    std::size_t row_edge_count = first.size();
    const resonith_partial_graph_manifest *row_graph = &manifest;
    const resonith_partial_path_manifest_v3 *row_path_manifest =
        &path_manifest_v3;
    resonith_partial_path_v3 *row_paths = nullptr;
    std::size_t row_path_capacity = 0U;
    resonith_partial_path_entry_v3 *row_entries = nullptr;
    std::size_t row_entry_capacity = 0U;
    resonith_partial_path_report_v3 row_report{};
    row_report.struct_size = sizeof(row_report);
    row_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto row_report_before = row_report;
    resonith_partial_path_report_v3 *row_report_pointer = &row_report;
    switch (row) {
    case v3_topology_case::null_resolutions:
      row_resolutions = nullptr;
      break;
    case v3_topology_case::zero_resolution_count:
      row_resolution_count = 0U;
      break;
    case v3_topology_case::null_observations_with_count:
      row_observations = nullptr;
      row_observation_count = 1U;
      break;
    case v3_topology_case::null_observations_without_count:
      row_observations = nullptr;
      row_observation_count = 0U;
      break;
    case v3_topology_case::null_edges_with_count:
      row_edges = nullptr;
      row_edge_count = 1U;
      break;
    case v3_topology_case::null_edges_without_count:
      row_edges = nullptr;
      row_edge_count = 0U;
      break;
    case v3_topology_case::null_graph_manifest:
      row_graph = nullptr;
      break;
    case v3_topology_case::null_path_manifest:
      row_path_manifest = nullptr;
      break;
    case v3_topology_case::null_report:
      row_report_pointer = nullptr;
      break;
    case v3_topology_case::path_without_entries:
      row_paths = paths_v3.data();
      break;
    case v3_topology_case::entries_without_path:
      row_entries = entries_v3.data();
      break;
    case v3_topology_case::null_payload_with_path_capacity:
      row_path_capacity = 1U;
      break;
    case v3_topology_case::null_payload_with_entry_capacity:
      row_entry_capacity = 1U;
      break;
    }
    const bool reaches_late_validation =
        row == v3_topology_case::null_observations_without_count ||
        row == v3_topology_case::null_edges_without_count;
    if (resonith_partial_graph_paths_cpu_v3(
            row_resolutions, row_resolution_count, row_observations,
            row_observation_count, row_edges, row_edge_count, row_graph,
            row_path_manifest, row_paths, row_path_capacity, row_entries,
            row_entry_capacity,
            row_report_pointer) != RESONITH_STATUS_INVALID_ARGUMENT ||
        (!reaches_late_validation && row_report_pointer != nullptr &&
         std::memcmp(&row_report, &row_report_before, sizeof(row_report)) !=
             0)) {
      fail("R-202 v3 pointer-topology matrix failed");
    }
  }

  resonith_partial_path_report_v3 matrix_report{};
  matrix_report.struct_size = sizeof(matrix_report);
  matrix_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;

  /*
   * The report starts eight bytes into the path-manifest object. Both ABI
   * headers are independently valid, so rejection must come from the range
   * overlap itself rather than from the earlier header-precedence checks.
   */
  alignas(std::max_align_t)
      std::array<std::byte, sizeof(resonith_partial_path_manifest_v3) + 8U>
          overlap_storage{};
  std::memcpy(
      overlap_storage.data(),
      &path_manifest_v3,
      sizeof(path_manifest_v3));
  resonith_partial_path_report_v3 overlap_report_header{};
  overlap_report_header.struct_size = sizeof(overlap_report_header);
  overlap_report_header.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  std::memcpy(
      overlap_storage.data() + 8U,
      &overlap_report_header,
      sizeof(overlap_report_header));
  const auto overlap_storage_before = overlap_storage;
  if (resonith_partial_graph_paths_cpu_v3(
          &resolution, 1U, observations.data(), observations.size(),
          first.data(), first.size(), &manifest,
          reinterpret_cast<const resonith_partial_path_manifest_v3 *>(
              overlap_storage.data()),
          nullptr, 0U, nullptr, 0U,
          reinterpret_cast<resonith_partial_path_report_v3 *>(
              overlap_storage.data() + 8U)) != RESONITH_STATUS_INVALID_ARGUMENT ||
      std::memcmp(
          overlap_storage.data(),
          overlap_storage_before.data(),
          overlap_storage.size()) != 0) {
    fail("R-202 v3 overlapping valid ABI objects were not rejected");
  }

  /*
   * Header, semantic, and reserved-field validation use one-field mutations
   * so precedence and no-publication behavior remain auditable.
   */
  enum class v3_manifest_mutation {
    graph_size,
    graph_version,
    path_size,
    path_version,
    report_size,
    report_version,
    second_order_law,
    work_ledger,
    graph_reserved,
    path_reserved,
    report_reserved,
  };
  constexpr std::array v3_manifest_mutations{
      v3_manifest_mutation::graph_size,
      v3_manifest_mutation::graph_version,
      v3_manifest_mutation::path_size,
      v3_manifest_mutation::path_version,
      v3_manifest_mutation::report_size,
      v3_manifest_mutation::report_version,
      v3_manifest_mutation::second_order_law,
      v3_manifest_mutation::work_ledger,
      v3_manifest_mutation::graph_reserved,
      v3_manifest_mutation::path_reserved,
      v3_manifest_mutation::report_reserved,
  };
  for (const v3_manifest_mutation row : v3_manifest_mutations) {
    resonith_partial_graph_manifest row_graph = manifest;
    resonith_partial_path_manifest_v3 row_path = path_manifest_v3;
    resonith_partial_path_report_v3 row_report{};
    row_report.struct_size = sizeof(row_report);
    row_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    switch (row) {
    case v3_manifest_mutation::graph_size:
      --row_graph.struct_size;
      break;
    case v3_manifest_mutation::graph_version:
      ++row_graph.abi_version;
      break;
    case v3_manifest_mutation::path_size:
      --row_path.struct_size;
      break;
    case v3_manifest_mutation::path_version:
      ++row_path.abi_version;
      break;
    case v3_manifest_mutation::report_size:
      --row_report.struct_size;
      break;
    case v3_manifest_mutation::report_version:
      ++row_report.abi_version;
      break;
    case v3_manifest_mutation::second_order_law:
      ++row_path.second_order_law_version;
      break;
    case v3_manifest_mutation::work_ledger:
      ++row_path.work_ledger_version;
      break;
    case v3_manifest_mutation::graph_reserved:
      row_graph.reserved[0] = 1U;
      break;
    case v3_manifest_mutation::path_reserved:
      row_path.reserved[0] = 1U;
      break;
    case v3_manifest_mutation::report_reserved:
      row_report.reserved[0] = 1U;
      break;
    }
    const auto row_report_before = row_report;
    if (resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &row_graph, &row_path, nullptr, 0U,
            nullptr, 0U, &row_report) != RESONITH_STATUS_INVALID_ARGUMENT ||
        std::memcmp(&row_report, &row_report_before, sizeof(row_report)) != 0) {
      fail("R-202 v3 manifest/semantic matrix failed");
    }
  }

  enum class v3_cap_case {
    graph_edge_records,
    maximum_path_observations,
    maximum_path_records,
    maximum_total_entries,
    maximum_frontier_states,
    maximum_state_records,
    exact_set_candidates,
    work_too_small,
    work_too_large,
    managed_bytes,
    device_bytes,
  };
  constexpr std::array v3_cap_cases{
      v3_cap_case::graph_edge_records,
      v3_cap_case::maximum_path_observations,
      v3_cap_case::maximum_path_records,
      v3_cap_case::maximum_total_entries,
      v3_cap_case::maximum_frontier_states,
      v3_cap_case::maximum_state_records,
      v3_cap_case::exact_set_candidates,
      v3_cap_case::work_too_small,
      v3_cap_case::work_too_large,
      v3_cap_case::managed_bytes,
      v3_cap_case::device_bytes,
  };
  for (const v3_cap_case row : v3_cap_cases) {
    resonith_partial_graph_manifest row_graph = manifest;
    resonith_partial_path_manifest_v3 row_path = path_manifest_v3;
    switch (row) {
    case v3_cap_case::graph_edge_records:
      row_graph.maximum_edge_records =
          RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS + 1ULL;
      break;
    case v3_cap_case::maximum_path_observations:
      row_path.maximum_path_observations =
          RESONITH_PARTIAL_PATH_MAX_OBSERVATIONS + 1U;
      break;
    case v3_cap_case::maximum_path_records:
      row_path.maximum_path_records = RESONITH_PARTIAL_PATH_MAX_RECORDS + 1ULL;
      break;
    case v3_cap_case::maximum_total_entries:
      row_path.maximum_total_entries = RESONITH_PARTIAL_PATH_MAX_ENTRIES + 1ULL;
      break;
    case v3_cap_case::maximum_frontier_states:
      row_path.maximum_frontier_states =
          RESONITH_PARTIAL_PATH_MAX_FRONTIER_STATES + 1ULL;
      break;
    case v3_cap_case::maximum_state_records:
      row_path.maximum_state_records =
          RESONITH_PARTIAL_PATH_MAX_STATE_RECORDS + 1ULL;
      break;
    case v3_cap_case::exact_set_candidates:
      row_path.exact_set_candidate_limit =
          RESONITH_PARTIAL_PATH_MAX_EXACT_SET_CANDIDATES + 1U;
      break;
    case v3_cap_case::work_too_small:
      row_path.maximum_work_units = 1U;
      break;
    case v3_cap_case::work_too_large:
      row_path.maximum_work_units = RESONITH_PARTIAL_MAX_WORK_EVENTS + 1U;
      break;
    case v3_cap_case::managed_bytes:
      row_path.maximum_managed_bytes = RESONITH_PARTIAL_MAX_HOST_BYTES + 1U;
      break;
    case v3_cap_case::device_bytes:
      row_path.maximum_device_bytes = RESONITH_PARTIAL_MAX_DEVICE_BYTES + 1U;
      break;
    }
    resonith_partial_path_report_v3 row_report{};
    row_report.struct_size = sizeof(row_report);
    row_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const auto row_report_before = row_report;
    if (resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &row_graph, &row_path, nullptr, 0U,
            nullptr, 0U, &row_report) != RESONITH_STATUS_PROFILE_BOUND ||
        std::memcmp(&row_report, &row_report_before, sizeof(row_report)) != 0) {
      fail("R-202 v3 hard-cap manifest matrix failed");
    }
  }

  if constexpr (sizeof(std::uintptr_t) >= sizeof(std::uint64_t)) {
    constexpr std::uintptr_t synthetic_v3_resolution_address =
        UINT64_C(0x0000110000000000);
    constexpr std::uintptr_t synthetic_v3_observation_address =
        UINT64_C(0x0000220000000000);
    constexpr std::uintptr_t synthetic_v3_edge_address =
        UINT64_C(0x0000330000000000);
    constexpr std::uintptr_t synthetic_v3_path_address =
        UINT64_C(0x0000440000000000);
    constexpr std::uintptr_t synthetic_v3_entry_address =
        UINT64_C(0x0000550000000000);
    enum class v3_count_cap_case {
      resolution_count,
      observation_count,
      edge_count,
      path_capacity,
      entry_capacity,
    };
    constexpr std::array v3_count_cap_cases{
        v3_count_cap_case::resolution_count,
        v3_count_cap_case::observation_count,
        v3_count_cap_case::edge_count,
        v3_count_cap_case::path_capacity,
        v3_count_cap_case::entry_capacity,
    };
    for (const v3_count_cap_case row : v3_count_cap_cases) {
      const bool cap_resolutions =
          row == v3_count_cap_case::resolution_count;
      const bool cap_observations =
          row == v3_count_cap_case::observation_count;
      const bool cap_edges = row == v3_count_cap_case::edge_count;
      const bool cap_paths = row == v3_count_cap_case::path_capacity;
      const bool cap_entries = row == v3_count_cap_case::entry_capacity;
      resonith_partial_path_report_v3 row_report{};
      row_report.struct_size = sizeof(row_report);
      row_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
      const auto row_report_before = row_report;
      if (resonith_partial_graph_paths_cpu_v3(
              cap_resolutions
                  ? reinterpret_cast<const resonith_partial_resolution *>(
                        synthetic_v3_resolution_address)
                  : &resolution,
              cap_resolutions ? RESONITH_PARTIAL_GRAPH_MAX_RESOLUTIONS + 1U
                              : 1U,
              cap_observations
                  ? reinterpret_cast<const resonith_partial_observation *>(
                        synthetic_v3_observation_address)
                  : observations.data(),
              cap_observations ? RESONITH_PARTIAL_GRAPH_MAX_OBSERVATIONS + 1U
                               : observations.size(),
              cap_edges ? reinterpret_cast<const resonith_partial_edge *>(
                              synthetic_v3_edge_address)
                        : first.data(),
              cap_edges ? RESONITH_PARTIAL_GRAPH_MAX_EDGE_RECORDS + 1U
                        : first.size(),
              &manifest, &path_manifest_v3,
              cap_paths || cap_entries
                  ? reinterpret_cast<resonith_partial_path_v3 *>(
                        synthetic_v3_path_address)
                  : nullptr,
              cap_paths ? RESONITH_PARTIAL_PATH_MAX_RECORDS + 1U : 0U,
              cap_paths || cap_entries
                  ? reinterpret_cast<resonith_partial_path_entry_v3 *>(
                        synthetic_v3_entry_address)
                  : nullptr,
              cap_entries ? RESONITH_PARTIAL_PATH_MAX_ENTRIES + 1U : 0U,
              &row_report) != RESONITH_STATUS_PROFILE_BOUND ||
          std::memcmp(&row_report, &row_report_before, sizeof(row_report)) !=
              0) {
        fail("R-202 v3 counted hard-cap matrix failed");
      }
    }

    constexpr std::uintptr_t high_graph_address =
        std::numeric_limits<std::uintptr_t>::max() &
        ~static_cast<std::uintptr_t>(alignof(resonith_partial_graph_manifest) -
                                     1U);
    constexpr std::uintptr_t high_path_address =
        std::numeric_limits<std::uintptr_t>::max() &
        ~static_cast<std::uintptr_t>(
            alignof(resonith_partial_path_manifest_v3) - 1U);
    constexpr std::uintptr_t high_report_address =
        std::numeric_limits<std::uintptr_t>::max() &
        ~static_cast<std::uintptr_t>(alignof(resonith_partial_path_report_v3) -
                                     1U);
    if (resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(),
            reinterpret_cast<const resonith_partial_graph_manifest *>(
                high_graph_address),
            &path_manifest_v3, nullptr, 0U, nullptr, 0U,
            &matrix_report) != RESONITH_STATUS_PROFILE_BOUND ||
        resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &manifest,
            reinterpret_cast<const resonith_partial_path_manifest_v3 *>(
                high_path_address),
            nullptr, 0U, nullptr, 0U,
            &matrix_report) != RESONITH_STATUS_PROFILE_BOUND ||
        resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &manifest, &path_manifest_v3, nullptr,
            0U, nullptr, 0U,
            reinterpret_cast<resonith_partial_path_report_v3 *>(
                high_report_address)) != RESONITH_STATUS_PROFILE_BOUND) {
      fail("R-202 v3 fixed-object overflow matrix failed");
    }

    constexpr std::uintptr_t high_observation_address =
        std::numeric_limits<std::uintptr_t>::max() &
        ~static_cast<std::uintptr_t>(alignof(resonith_partial_observation) -
                                     1U);
    matrix_report = {};
    matrix_report.struct_size = sizeof(matrix_report);
    matrix_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    if (resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U,
            reinterpret_cast<const resonith_partial_observation *>(
                high_observation_address),
            1U, first.data(), first.size(), &manifest, &path_manifest_v3,
            nullptr, 0U, nullptr, 0U,
            &matrix_report) != RESONITH_STATUS_PROFILE_BOUND) {
      fail("R-202 v3 counted-input overflow was not rejected");
    }
  }

  /*
   * A non-allocation exception from the injected test upstream must never
   * escape the C ABI or publish caller payload. It is intentionally distinct
   * from the environmental bad_alloc path covered above.
   */
  throw_non_allocation_resource unexpected_upstream;
  resonith::internal::partial_graph_set_test_upstream_resource(
      &unexpected_upstream);
  matrix_count = 0x55aaU;
  const resonith_status unexpected_r190 = resonith_partial_graph_edges_cpu(
      &resolution, 1U, observations.data(), observations.size(), &manifest,
      nullptr, 0U, &matrix_count);
  matrix_report = {};
  matrix_report.struct_size = sizeof(matrix_report);
  matrix_report.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
  const resonith_status unexpected_v3 = resonith_partial_graph_paths_cpu_v3(
      &resolution, 1U, observations.data(), observations.size(), first.data(),
      first.size(), &manifest, &path_manifest_v3, nullptr, 0U, nullptr, 0U,
      &matrix_report);
  resonith::internal::partial_graph_set_test_upstream_resource(nullptr);
  if (unexpected_r190 != RESONITH_STATUS_MALFORMED ||
      matrix_count != static_cast<std::size_t>(0x55aaU) ||
      unexpected_v3 != RESONITH_STATUS_MALFORMED ||
      matrix_report.termination !=
          RESONITH_PARTIAL_PATH_TERMINATION_INTERNAL_MALFORMED) {
    fail("R-202 unexpected-exception C ABI barrier failed");
  }

  /*
   * The public wrapper's over-limit outcome is allocation-invariant
   * unreachable after successful preflight. Exercise the shared checked
   * arithmetic directly without manufacturing wrapper reachability.
   */
  constexpr std::uint64_t stage_path_bytes =
      sizeof(resonith_partial_path) + sizeof(resonith_partial_path_v3);
  constexpr std::uint64_t stage_entry_bytes =
      sizeof(resonith_partial_path_entry) +
      sizeof(resonith_partial_path_entry_v3);
  constexpr std::uint64_t exact_stage_bytes =
      3U * stage_path_bytes + 1542U * stage_entry_bytes;
  constexpr auto exact_stage =
      resonith::internal::checked_partial_graph_stage_budget(
          3U, 1542U, exact_stage_bytes);
  constexpr auto over_limit_stage =
      resonith::internal::checked_partial_graph_stage_budget(
          3U, 1542U, exact_stage_bytes - 1U);
  constexpr auto path_overflow_stage =
      resonith::internal::checked_partial_graph_stage_budget(
          std::numeric_limits<std::uint64_t>::max() / stage_path_bytes + 1U,
          0U, std::numeric_limits<std::uint64_t>::max());
  constexpr auto entry_overflow_stage =
      resonith::internal::checked_partial_graph_stage_budget(
          0U,
          std::numeric_limits<std::uint64_t>::max() / stage_entry_bytes + 1U,
          std::numeric_limits<std::uint64_t>::max());
  constexpr auto additive_overflow_stage =
      resonith::internal::checked_partial_graph_stage_budget(
          std::numeric_limits<std::uint64_t>::max() / stage_path_bytes,
          std::numeric_limits<std::uint64_t>::max() / stage_entry_bytes,
          std::numeric_limits<std::uint64_t>::max());
  static_assert(!exact_stage.overflow && !exact_stage.over_limit);
  static_assert(exact_stage.bytes == exact_stage_bytes);
  static_assert(!over_limit_stage.overflow && over_limit_stage.over_limit);
  static_assert(path_overflow_stage.overflow);
  static_assert(entry_overflow_stage.overflow);
  static_assert(additive_overflow_stage.overflow);
  if (exact_stage.bytes != exact_stage_bytes ||
      exact_stage.overflow || exact_stage.over_limit ||
      over_limit_stage.overflow || !over_limit_stage.over_limit ||
      !path_overflow_stage.overflow || !entry_overflow_stage.overflow ||
      !additive_overflow_stage.overflow) {
    fail("R-202 checked stage-budget boundary failed");
  }

  /*
   * Integer work-budget sweep: preflight discovers identity at every viable
   * budget, then fill reuses that exact identity. This reaches every
   * resource-ledger prefix without test-only failpoint hooks in production.
   */
  const std::uint64_t canonical_fill_work = report_v3.work_units;
  bool saw_budgeted_preflight = false;
  bool saw_budgeted_fill_rejection = false;
  bool saw_budgeted_fill_success = false;
  for (std::uint64_t work_limit = 2U; work_limit <= canonical_fill_work;
       ++work_limit) {
    resonith_partial_path_manifest_v3 budget_path = path_manifest_v3;
    budget_path.maximum_work_units = work_limit;
    std::fill(std::begin(budget_path.expected_input_fingerprint),
              std::end(budget_path.expected_input_fingerprint), 0U);
    resonith_partial_path_report_v3 budget_preflight{};
    budget_preflight.struct_size = sizeof(budget_preflight);
    budget_preflight.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const resonith_status budget_preflight_status =
        resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &manifest, &budget_path, nullptr, 0U,
            nullptr, 0U, &budget_preflight);
    if (budget_preflight_status != RESONITH_STATUS_OK) {
      if (budget_preflight_status != RESONITH_STATUS_PROFILE_BOUND) {
        fail("R-202 work sweep produced unexpected preflight status");
      }
      continue;
    }
    saw_budgeted_preflight = true;
    std::copy(std::begin(budget_preflight.input_fingerprint),
              std::end(budget_preflight.input_fingerprint),
              budget_path.expected_input_fingerprint);
    auto budget_paths = paths_v3_before;
    auto budget_entries = entries_v3_before;
    resonith_partial_path_report_v3 budget_fill{};
    budget_fill.struct_size = sizeof(budget_fill);
    budget_fill.abi_version = RESONITH_PARTIAL_PATH_V3_ABI_VERSION;
    const resonith_status budget_fill_status =
        resonith_partial_graph_paths_cpu_v3(
            &resolution, 1U, observations.data(), observations.size(),
            first.data(), first.size(), &manifest, &budget_path,
            budget_paths.data(), budget_paths.size(), budget_entries.data(),
            budget_entries.size(), &budget_fill);
    if (budget_fill_status == RESONITH_STATUS_OK) {
      saw_budgeted_fill_success = true;
    } else if (budget_fill_status == RESONITH_STATUS_PROFILE_BOUND) {
      saw_budgeted_fill_rejection = true;
      if (std::memcmp(budget_paths.data(), paths_v3_before.data(),
                      budget_paths.size() * sizeof(budget_paths[0])) != 0 ||
          std::memcmp(budget_entries.data(), entries_v3_before.data(),
                      budget_entries.size() * sizeof(budget_entries[0])) != 0) {
        fail("R-202 work-budget rejection published payload");
      }
    } else {
      fail("R-202 work sweep produced unexpected fill status");
    }
  }
  if (canonical_fill_work < 2U || !saw_budgeted_preflight ||
      !saw_budgeted_fill_rejection || !saw_budgeted_fill_success) {
    fail("R-202 work-budget sweep missed a required phase");
  }

  std::printf("{\"schema\":\"resonith-r190-native-edge-cpu-1\","
              "\"edge_count\":%zu,\"path_count\":%llu,"
              "\"reserved_host_bytes\":%llu,"
              "\"committed_host_bytes\":%llu,"
              "\"peak_live_host_bytes\":%llu,"
              "\"device_bytes\":0,\"work_sweep_max\":%llu,"
              "\"stage_budget_helper\":true,"
              "\"deterministic\":true,"
              "\"predictor_integrated\":false}\n",
              first_count,
              static_cast<unsigned long long>(report_v3.written_path_count),
              static_cast<unsigned long long>(report_v3.reserved_host_bytes),
              static_cast<unsigned long long>(report_v3.committed_host_bytes),
              static_cast<unsigned long long>(report_v3.peak_live_host_bytes),
              static_cast<unsigned long long>(canonical_fill_work));
  return 0;
}
