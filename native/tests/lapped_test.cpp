#include "resonith/lapped.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>

namespace {

#include "lapped_vector.inc"

bool expect(bool condition, const char* message) {
    if (!condition) {
        std::fprintf(stderr, "FAIL: %s\n", message);
    }
    return condition;
}

}  // namespace

int main() {
    resonith_lapped_analysis_requirements analysis_requirements{};
    if (!expect(
            resonith_lapped_analyze_requirements(
                96U,
                2U,
                32U,
                4U,
                &analysis_requirements
            ) == RESONITH_STATUS_OK
                && analysis_requirements.transform_frame_count == 4U
                && analysis_requirements.scale_elements
                    == kExpectedLappedScales.size()
                && analysis_requirements.coefficient_elements
                    == kExpectedLappedQuantized.size()
                && analysis_requirements.score_elements
                    == kExpectedLappedScores.size(),
            "fixed LPF1 analysis requirements"
        )) {
        return 1;
    }
    std::array<std::uint8_t, kExpectedLappedScales.size()>
        analyzed_scales{};
    std::array<std::int16_t, kExpectedLappedQuantized.size()>
        analyzed_quantized{};
    std::array<std::uint64_t, kExpectedLappedScores.size()>
        analyzed_scores{};
    if (!expect(
            resonith_lapped_analyze_pcm16(
                kLappedSourcePcm.data(),
                kLappedSourcePcm.size(),
                96U,
                2U,
                32U,
                4U,
                analyzed_scales.data(),
                analyzed_scales.size(),
                analyzed_quantized.data(),
                analyzed_quantized.size(),
                analyzed_scores.data(),
                analyzed_scores.size()
            ) == RESONITH_STATUS_OK
                && analyzed_scales == kExpectedLappedScales
                && analyzed_quantized == kExpectedLappedQuantized
                && analyzed_scores == kExpectedLappedScores,
            "Python and native fixed LPF1 analysis parity"
        )) {
        return 1;
    }

    resonith_lapped_requirements requirements{};
    if (!expect(
            resonith_lapped_inspect(
                kLappedStream.data(),
                kLappedStream.size(),
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.sample_rate == 48000U
                && requirements.frame_count == 96U
                && requirements.transform_frame_count == 4U
                && requirements.half_window == 32U
                && requirements.band_count == 4U
                && requirements.coefficients_per_frame == 8U
                && requirements.output_channels == 2U
                && requirements.scale_elements == 32U
                && requirements.count_elements == 0U
                && requirements.position_elements == 64U
                && requirements.coefficient_elements == 64U
                && requirements.overlap_elements == 160U
                && requirements.output_elements == 192U,
            "fixed bounded LPF1 inspect"
        )) {
        return 1;
    }

    std::array<std::uint8_t, 32> scales{};
    std::array<std::uint16_t, 8> counts{};
    std::array<std::uint16_t, 64> positions{};
    std::array<std::int8_t, 64> coefficients{};
    std::array<std::int64_t, 160> overlap{};
    resonith_lapped_workspace workspace = {
        scales.data(),
        scales.size(),
        counts.data(),
        0U,
        positions.data(),
        positions.size(),
        coefficients.data(),
        coefficients.size(),
        overlap.data(),
        overlap.size(),
    };
    std::array<std::int16_t, 192> output{};
    std::size_t written = 0U;
    if (!expect(
            resonith_lapped_decode(
                kLappedStream.data(),
                kLappedStream.size(),
                &workspace,
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == 96U
                && output == kExpectedLappedPcm,
            "Python and native fixed LPF1 PCM parity"
        )) {
        return 1;
    }

    if (!expect(
            resonith_lapped_inspect(
                kAdaptiveLappedStream.data(),
                kAdaptiveLappedStream.size(),
                &requirements
            ) == RESONITH_STATUS_OK
                && requirements.coefficients_per_frame == 0U
                && requirements.count_elements == counts.size()
                && requirements.position_elements == positions.size(),
            "variable-density LPF1 inspect"
        )) {
        return 1;
    }
    workspace.count_capacity = counts.size();
    if (!expect(
            resonith_lapped_decode(
                kAdaptiveLappedStream.data(),
                kAdaptiveLappedStream.size(),
                &workspace,
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_OK
                && written == 96U
                && output == kExpectedAdaptiveLappedPcm,
            "Python and native variable-density PCM parity"
        )) {
        return 1;
    }

    auto corrupted = kLappedStream;
    corrupted.back() ^= 1U;
    if (!expect(
            resonith_lapped_inspect(
                corrupted.data(),
                corrupted.size(),
                &requirements
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "LPF1 section integrity"
        )) {
        return 1;
    }

    output.fill(1234);
    workspace.count_capacity = 0U;
    written = 9U;
    if (!expect(
            resonith_lapped_decode(
                kAdaptiveLappedStream.data(),
                kAdaptiveLappedStream.size(),
                &workspace,
                output.data(),
                output.size(),
                &written
            ) == RESONITH_STATUS_SCRATCH_TOO_SMALL
                && written == 0U
                && std::all_of(
                    output.begin(),
                    output.end(),
                    [](std::int16_t value) { return value == 1234; }
                ),
            "LPF1 workspace rejection is output-atomic"
        )) {
        return 1;
    }
    return 0;
}
