#include "resonith/maf.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

bool test_resources() {
    resonith_maf_limits limits{};
    if (!expect(
            resonith_maf_main_limits(&limits) == RESONITH_STATUS_OK
                && limits.maximum_output_channels == 8U
                && limits.maximum_filter_order == 16U,
            "Main MAF limits"
        )) {
        return false;
    }
    const resonith_maf_resource_declaration declaration = {
        48000U,
        256U,
        4U,
        2U,
        512U,
        12U,
        8U,
        1U,
        1U,
        2U,
        2U,
        10U,
        64U,
        12U,
        4096U,
        8192U,
        2000U,
    };
    resonith_maf_requirements requirements{};
    if (!expect(
            resonith_maf_resources_validate(
                &limits,
                &declaration,
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.output_elements == 512U
                && requirements.output_bytes == 1024U
                && requirements.operations_per_block == 512000U,
            "resource preflight"
        )) {
        return false;
    }
    resonith_maf_resource_declaration malformed = declaration;
    malformed.basis_elements = 0U;
    return expect(
        resonith_maf_resources_validate(
            &limits,
            &malformed,
            &requirements
        ) == RESONITH_STATUS_MALFORMED
            && requirements.output_elements == 0U,
        "inconsistent Basis declaration"
    );
}

bool test_noise_partition_and_budget() {
    std::array<std::int16_t, 32> whole{};
    std::array<std::int16_t, 32> partitioned{};
    resonith_maf_operation_budget whole_budget{10000U};
    resonith_maf_operation_budget first_budget{10000U};
    resonith_maf_operation_budget second_budget{10000U};
    if (
        resonith_maf_noise_render(
            0x5245534f4e495448ULL,
            7U,
            1U,
            1000U,
            24576,
            whole.size(),
            whole.data(),
            whole.size(),
            &whole_budget
        ) != RESONITH_STATUS_OK
        || resonith_maf_noise_render(
            0x5245534f4e495448ULL,
            7U,
            1U,
            1000U,
            24576,
            13U,
            partitioned.data(),
            partitioned.size(),
            &first_budget
        ) != RESONITH_STATUS_OK
        || resonith_maf_noise_render(
            0x5245534f4e495448ULL,
            7U,
            1U,
            1013U,
            24576,
            19U,
            partitioned.data() + 13U,
            partitioned.size() - 13U,
            &second_budget
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "counter noise render");
    }
    if (!expect(whole == partitioned, "counter noise callback invariance")) {
        return false;
    }

    std::array<std::int16_t, 4> untouched = {11, 22, 33, 44};
    resonith_maf_operation_budget insufficient{47U};
    return expect(
        resonith_maf_noise_render(
            1U,
            0U,
            0U,
            0U,
            32768,
            untouched.size(),
            untouched.data(),
            untouched.size(),
            &insufficient
        ) == RESONITH_STATUS_PROFILE_BOUND
            && untouched == std::array<std::int16_t, 4>{11, 22, 33, 44}
            && insufficient.remaining == 47U,
        "noise budget failure is transactional"
    );
}

bool test_periodic_and_filter_partition() {
    const std::array<std::int16_t, 4> basis = {
        0,
        20000,
        0,
        -20000,
    };
    const std::array<std::uint32_t, 2> positions = {0U, 8U};
    const std::array<std::uint32_t, 2> increments = {
        0x20000000U,
        0x20000000U,
    };
    std::array<std::uint32_t, 2> origins{};
    const resonith_phase_trajectory source = {
        positions.data(),
        increments.data(),
        2U,
        0U,
    };
    resonith_prepared_phase_trajectory trajectory{};
    if (
        resonith_phase_prepare(
            &source,
            origins.data(),
            origins.size(),
            &trajectory
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "phase preparation");
    }
    std::array<std::int16_t, 8> periodic{};
    resonith_maf_operation_budget periodic_budget{64U};
    if (!expect(
            resonith_maf_periodic_render(
                basis.data(),
                basis.size(),
                &trajectory,
                0U,
                periodic.size(),
                periodic.data(),
                periodic.size(),
                &periodic_budget
            ) == RESONITH_STATUS_OK
                && periodic_budget.remaining == 0U
                && std::any_of(
                    periodic.begin(),
                    periodic.end(),
                    [](std::int16_t value) { return value != 0; }
                ),
            "bounded periodic render"
        )) {
        return false;
    }

    const std::array<std::uint32_t, 1> gain_positions = {0U};
    const std::array<std::int32_t, 1> gains_q15 = {32768};
    const resonith_gain_event_law gain_source = {
        gain_positions.data(),
        gains_q15.data(),
        1U,
        static_cast<std::uint32_t>(periodic.size()),
    };
    resonith_prepared_gain_law gain{};
    if (
        resonith_gain_prepare(&gain_source, &gain)
        != RESONITH_STATUS_OK
    ) {
        return expect(false, "gain preparation");
    }
    std::array<std::int16_t, 8> composed{};
    resonith_maf_operation_budget compose_budget{64U};
    if (!expect(
            resonith_maf_compose_truth(
                periodic.data(),
                nullptr,
                1U,
                &gain,
                0U,
                periodic.size(),
                composed.data(),
                composed.size(),
                &compose_budget
            ) == RESONITH_STATUS_OK
                && composed == periodic
                && compose_budget.remaining == 0U,
            "bounded Truth composition"
        )) {
        return false;
    }

    const std::array<std::int16_t, 3> reflection = {
        8192,
        -4096,
        2048,
    };
    std::array<std::int32_t, 3> coefficients{};
    resonith_maf_filter filter{};
    if (
        resonith_maf_filter_prepare(
            reflection.data(),
            static_cast<std::uint16_t>(reflection.size()),
            coefficients.data(),
            coefficients.size(),
            &filter
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "stable filter preparation");
    }
    const std::array<std::int16_t, 12> excitation = {
        12000, 0, 0, 0, 0, 0, -4000, 0, 0, 0, 0, 0,
    };
    std::array<std::int16_t, 12> whole{};
    std::array<std::int16_t, 12> partitioned{};
    std::array<std::int16_t, 3> whole_history{};
    std::array<std::int16_t, 3> split_history{};
    resonith_maf_operation_budget whole_budget{1000U};
    resonith_maf_operation_budget split_budget{1000U};
    if (
        resonith_maf_filter_render(
            &filter,
            excitation.data(),
            excitation.size(),
            whole_history.data(),
            whole_history.size(),
            whole.data(),
            whole.size(),
            &whole_budget
        ) != RESONITH_STATUS_OK
        || resonith_maf_filter_render(
            &filter,
            excitation.data(),
            5U,
            split_history.data(),
            split_history.size(),
            partitioned.data(),
            partitioned.size(),
            &split_budget
        ) != RESONITH_STATUS_OK
        || resonith_maf_filter_render(
            &filter,
            excitation.data() + 5U,
            excitation.size() - 5U,
            split_history.data(),
            split_history.size(),
            partitioned.data() + 5U,
            partitioned.size() - 5U,
            &split_budget
        ) != RESONITH_STATUS_OK
    ) {
        return expect(false, "source filter render");
    }
    return expect(
        whole == partitioned && whole_history == split_history,
        "source filter callback invariance"
    );
}

bool test_innovation_transient_and_mix() {
    const std::array<std::int16_t, 4> prediction = {
        100,
        -100,
        32000,
        -32000,
    };
    const std::array<std::int64_t, 4> innovation = {
        3,
        -3,
        1000000000000LL,
        -1000000000000LL,
    };
    std::array<std::int16_t, 4> composed{};
    resonith_maf_operation_budget innovation_budget{16U};
    if (!expect(
            resonith_maf_innovation_add(
                prediction.data(),
                innovation.data(),
                10U,
                prediction.size(),
                composed.data(),
                composed.size(),
                &innovation_budget
            ) == RESONITH_STATUS_OK
                && composed
                    == std::array<std::int16_t, 4>{
                        130,
                        -130,
                        32767,
                        -32768,
                    },
            "bounded Innovation add"
        )) {
        return false;
    }

    const std::array<std::int16_t, 4> transient_shape = {
        1000,
        2000,
        -1000,
        -500,
    };
    const resonith_maf_transient transient = {
        transient_shape.data(),
        3U,
        static_cast<std::uint16_t>(transient_shape.size()),
        0U,
        32768,
    };
    const std::array<std::int16_t, 8> base{};
    std::array<std::int16_t, 8> transient_output{};
    resonith_maf_operation_budget transient_budget{100U};
    const resonith_status transient_status = resonith_maf_transients_add(
        base.data(),
        0U,
        base.size(),
        &transient,
        1U,
        transient_output.data(),
        transient_output.size(),
        &transient_budget
    );
    const bool transient_ok =
        transient_status == RESONITH_STATUS_OK
        && transient_output[3] == 1000
        && transient_output[4] == 2000
        && transient_output[5] == -1000
        && transient_output[6] == -500;
    if (!transient_ok) {
        std::fprintf(
            stderr,
            "FAIL: bounded transient injection status=%d budget=%llu pcm="
            "%d,%d,%d,%d,%d,%d,%d,%d\n",
            static_cast<int>(transient_status),
            static_cast<unsigned long long>(transient_budget.remaining),
            static_cast<int>(transient_output[0]),
            static_cast<int>(transient_output[1]),
            static_cast<int>(transient_output[2]),
            static_cast<int>(transient_output[3]),
            static_cast<int>(transient_output[4]),
            static_cast<int>(transient_output[5]),
            static_cast<int>(transient_output[6]),
            static_cast<int>(transient_output[7])
        );
        return false;
    }

    const std::array<std::int16_t, 6> planar = {
        1000, 2000, 3000,
        -1000, -2000, -3000,
    };
    const std::array<std::int16_t, 4> matrix = {
        32767, 0,
        16384, 16384,
    };
    std::array<std::int16_t, 6> interleaved{};
    resonith_maf_operation_budget mix_budget{100U};
    return expect(
        resonith_maf_mix_q15(
            planar.data(),
            2U,
            3U,
            matrix.data(),
            2U,
            interleaved.data(),
            interleaved.size(),
            &mix_budget
        ) == RESONITH_STATUS_OK
            && interleaved
                == std::array<std::int16_t, 6>{
                    1000, 0,
                    2000, 0,
                    3000, 0,
                },
        "bounded channel matrix"
    );
}

}  // namespace

int main() {
    return test_resources()
            && test_noise_partition_and_budget()
            && test_periodic_and_filter_partition()
            && test_innovation_transient_and_mix()
        ? 0
        : 1;
}
