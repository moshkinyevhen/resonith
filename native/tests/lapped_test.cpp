#include "resonith/lapped.h"
#include "resonith/lapped_compact.h"
#include "resonith/lapped_packet.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <vector>

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

    resonith_lapped_packet_session packet_session{};
    resonith_lapped_packet_requirements packet_requirements{};
    if (!expect(
            resonith_lapped_packet_open(
                kLappedPacketStream.data(),
                kLappedPacketStream.size(),
                &packet_session,
                &packet_requirements
            ) == RESONITH_STATUS_OK
                && packet_requirements.frame_count == 96U
                && packet_requirements.packet_frames == 64U
                && packet_requirements.packet_count == 2U
                && packet_requirements.maximum_child.scale_elements == 40U
                && packet_requirements.maximum_child.position_elements == 80U
                && packet_requirements.maximum_child_output_elements == 256U
                && packet_requirements.maximum_logical_output_elements == 128U,
            "LPS1 preflight and maximum workspace"
        )) {
        return 1;
    }
    std::array<std::uint8_t, 40> packet_scales{};
    std::array<std::uint16_t, 8> packet_counts{};
    std::array<std::uint16_t, 80> packet_positions{};
    std::array<std::int8_t, 80> packet_coefficients{};
    std::array<std::int64_t, 192> packet_overlap{};
    resonith_lapped_workspace packet_workspace = {
        packet_scales.data(),
        packet_scales.size(),
        packet_counts.data(),
        0U,
        packet_positions.data(),
        packet_positions.size(),
        packet_coefficients.data(),
        packet_coefficients.size(),
        packet_overlap.data(),
        packet_overlap.size(),
    };
    std::array<std::int16_t, 256> child_output{};
    std::array<std::int16_t, 128> logical_output{};
    std::array<std::int16_t, 192> packet_pcm{};
    for (std::uint32_t packet = 0U; packet < 2U; ++packet) {
        std::uint32_t logical_start = 99U;
        std::size_t logical_frames = 99U;
        if (!expect(
                resonith_lapped_packet_decode_next(
                    &packet_session,
                    &packet_workspace,
                    child_output.data(),
                    child_output.size(),
                    logical_output.data(),
                    logical_output.size(),
                    &logical_start,
                    &logical_frames
                ) == RESONITH_STATUS_OK
                    && logical_start == (packet == 0U ? 0U : 64U)
                    && logical_frames == (packet == 0U ? 64U : 32U),
                "LPS1 transactional packet decode"
            )) {
            return 1;
        }
        std::copy_n(
            logical_output.begin(),
            logical_frames * 2U,
            packet_pcm.begin()
                + static_cast<std::ptrdiff_t>(logical_start * 2U)
        );
    }
    if (!expect(
            packet_pcm == kExpectedLappedPcm,
            "LPS1 fixed-density output equals monolithic LPF1"
        )) {
        return 1;
    }
    std::uint32_t logical_start = 99U;
    std::size_t logical_frames = 99U;
    if (!expect(
            resonith_lapped_packet_decode_next(
                &packet_session,
                &packet_workspace,
                child_output.data(),
                child_output.size(),
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_NOT_FOUND
                && logical_start == 0U
                && logical_frames == 0U,
            "LPS1 canonical end of stream"
        )) {
        return 1;
    }

    packet_session = {};
    packet_requirements = {};
    if (!expect(
            resonith_lapped_packet_open(
                kLappedTransformPacketStream.data(),
                kLappedTransformPacketStream.size(),
                &packet_session,
                &packet_requirements
            ) == RESONITH_STATUS_OK
                && packet_session.packet_mode == 2U
                && packet_requirements.frame_count == 96U
                && packet_requirements.packet_count == 2U
                && packet_requirements.maximum_child.count_elements <= 8U
                && packet_requirements.maximum_child.position_elements <= 80U
                && packet_requirements.maximum_child_output_elements <= 128U,
            "LPS2 direct LSE2 preflight"
        )) {
        return 1;
    }
    packet_workspace.count_capacity = packet_counts.size();
    packet_pcm.fill(0);
    for (std::uint32_t packet = 0U; packet < 2U; ++packet) {
        logical_start = 99U;
        logical_frames = 99U;
        if (!expect(
                resonith_lapped_packet_decode_next(
                    &packet_session,
                    &packet_workspace,
                    child_output.data(),
                    child_output.size(),
                    logical_output.data(),
                    logical_output.size(),
                    &logical_start,
                    &logical_frames
                ) == RESONITH_STATUS_OK
                    && logical_start == (packet == 0U ? 0U : 64U)
                    && logical_frames == (packet == 0U ? 64U : 32U),
                "LPS2 transactional direct-field decode"
            )) {
            return 1;
        }
        std::copy_n(
            logical_output.begin(),
            logical_frames * 2U,
            packet_pcm.begin()
                + static_cast<std::ptrdiff_t>(logical_start * 2U)
        );
    }
    if (!expect(
            packet_pcm == kExpectedAdaptiveLappedPcm,
            "LPS2 output equals monolithic adaptive LPF1"
        )) {
        return 1;
    }

    resonith_lapped_compact_session compact_session{};
    resonith_lapped_compact_requirements compact_requirements{};
    if (!expect(
            resonith_lapped_compact_open(
                kLappedCompactPacketStream.data(),
                kLappedCompactPacketStream.size(),
                &compact_session,
                &compact_requirements
            ) == RESONITH_STATUS_OK
                && compact_requirements.frame_count == 96U
                && compact_requirements.packet_frames == 64U
                && compact_requirements.packet_count == 2U
                && compact_requirements.maximum_current
                    .transform_frame_count == 2U
                && compact_requirements.maximum_current.scale_elements == 16U
                && compact_requirements.maximum_current.count_elements == 4U
                && compact_requirements.maximum_current.position_elements
                    == 39U
                && compact_requirements.maximum_lookahead
                    .transform_frame_count == 2U
                && compact_requirements.maximum_logical_output_elements
                    == 128U,
            "LPS4 bounded compact preflight"
        )) {
        return 1;
    }
    auto compact_corrupted = kLappedCompactPacketStream;
    compact_corrupted[compact_corrupted.size() - 5U] ^= 1U;
    if (!expect(
            resonith_lapped_compact_open(
                compact_corrupted.data(),
                compact_corrupted.size(),
                &compact_session,
                &compact_requirements
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH,
            "LPS4 CRC corruption rejection"
        )) {
        return 1;
    }
    std::array<std::uint8_t, 16> compact_lookahead_scales{};
    std::array<std::uint16_t, 4> compact_lookahead_counts{};
    std::array<std::uint16_t, 39> compact_lookahead_positions{};
    std::array<std::int8_t, 39> compact_lookahead_coefficients{};
    resonith_lapped_workspace compact_lookahead_workspace = {
        compact_lookahead_scales.data(),
        compact_lookahead_scales.size(),
        compact_lookahead_counts.data(),
        compact_lookahead_counts.size(),
        compact_lookahead_positions.data(),
        compact_lookahead_positions.size(),
        compact_lookahead_coefficients.data(),
        compact_lookahead_coefficients.size(),
        nullptr,
        0U,
    };

    compact_corrupted[compact_corrupted.size() - 5U] ^= 1U;
    if (!expect(
            resonith_lapped_compact_open(
                compact_corrupted.data(),
                compact_corrupted.size(),
                &compact_session,
                &compact_requirements
            ) == RESONITH_STATUS_OK,
            "LPS4 transactional fixture preflight"
        )) {
        return 1;
    }
    compact_corrupted[compact_corrupted.size() - 5U] ^= 1U;
    logical_output.fill(1234);
    logical_start = 99U;
    logical_frames = 99U;
    if (!expect(
            resonith_lapped_compact_decode_next(
                &compact_session,
                &packet_workspace,
                &compact_lookahead_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH
                && compact_session.next_packet == 0U
                && compact_session.next_frame == 0U
                && logical_start == 0U
                && logical_frames == 0U
                && std::all_of(
                    logical_output.begin(),
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 failed lookahead pull is transactional"
        )) {
        return 1;
    }
    compact_corrupted[compact_corrupted.size() - 5U] ^= 1U;

    if (!expect(
            resonith_lapped_compact_open(
                kLappedCompactPacketStream.data(),
                kLappedCompactPacketStream.size(),
                &compact_session,
                &compact_requirements
            ) == RESONITH_STATUS_OK,
            "LPS4 pull-session preflight"
        )) {
        return 1;
    }
    packet_pcm.fill(0);
    for (std::uint32_t packet = 0U; packet < 2U; ++packet) {
        logical_start = 99U;
        logical_frames = 99U;
        if (!expect(
                resonith_lapped_compact_decode_next(
                    &compact_session,
                    &packet_workspace,
                    &compact_lookahead_workspace,
                    logical_output.data(),
                    logical_output.size(),
                    &logical_start,
                    &logical_frames
                ) == RESONITH_STATUS_OK
                    && logical_start == (packet == 0U ? 0U : 64U)
                    && logical_frames == (packet == 0U ? 64U : 32U),
                "LPS4 two-workspace transactional pull"
            )) {
            return 1;
        }
        std::copy_n(
            logical_output.begin(),
            logical_frames * 2U,
            packet_pcm.begin()
                + static_cast<std::ptrdiff_t>(logical_start * 2U)
        );
    }
    if (!expect(
            packet_pcm == kExpectedAdaptiveLappedPcm,
            "LPS4 output equals monolithic adaptive LPF1"
        )) {
        return 1;
    }

    constexpr std::size_t compact_header_size = 60U;
    const std::size_t compact_first_size = kLappedCompactRecordSizes[0U];
    const std::size_t compact_second_offset =
        compact_header_size + compact_first_size;
    const std::size_t compact_second_size = kLappedCompactRecordSizes[1U];
    resonith_lapped_compact_sequence compact_sequence{};
    if (!expect(
            resonith_lapped_compact_sequence_open(
                kLappedCompactPacketStream.data(),
                compact_header_size,
                &compact_sequence
            ) == RESONITH_STATUS_OK
                && compact_sequence.sample_rate == 48000U
                && compact_sequence.frame_count == 96U
                && compact_sequence.packet_frames == 64U
                && compact_sequence.packet_count == 2U,
            "LPS4 authenticated sequence context"
        )) {
        return 1;
    }
    resonith_lapped_compact_requirements header_requirements{};
    if (!expect(
            resonith_lapped_compact_sequence_requirements(
                &compact_sequence,
                &header_requirements
            ) == RESONITH_STATUS_OK
                && header_requirements.maximum_current.scale_elements
                    >= compact_requirements.maximum_current.scale_elements
                && header_requirements.maximum_current.count_elements
                    >= compact_requirements.maximum_current.count_elements
                && header_requirements.maximum_current.position_elements
                    >= compact_requirements.maximum_current.position_elements
                && header_requirements.maximum_current.coefficient_elements
                    >= compact_requirements.maximum_current
                        .coefficient_elements
                && header_requirements.maximum_current.overlap_elements
                    >= compact_requirements.maximum_current.overlap_elements
                && header_requirements.maximum_lookahead.position_elements
                    >= compact_requirements.maximum_lookahead.position_elements
                && header_requirements.maximum_logical_output_elements
                    >= compact_requirements.maximum_logical_output_elements,
            "LPS4 header-only requirements cover exact preflight"
        )) {
        return 1;
    }
    const auto& header_current = header_requirements.maximum_current;
    const auto& header_lookahead = header_requirements.maximum_lookahead;
    std::vector<std::uint8_t> header_current_scales(
        header_current.scale_elements
    );
    std::vector<std::uint16_t> header_current_counts(
        header_current.count_elements
    );
    std::vector<std::uint16_t> header_current_positions(
        header_current.position_elements
    );
    std::vector<std::int8_t> header_current_coefficients(
        header_current.coefficient_elements
    );
    std::vector<std::int64_t> header_current_overlap(
        header_current.overlap_elements
    );
    resonith_lapped_workspace header_current_workspace = {
        header_current_scales.data(),
        header_current_scales.size(),
        header_current_counts.data(),
        header_current_counts.size(),
        header_current_positions.data(),
        header_current_positions.size(),
        header_current_coefficients.data(),
        header_current_coefficients.size(),
        header_current_overlap.data(),
        header_current_overlap.size(),
    };
    std::vector<std::uint8_t> header_lookahead_scales(
        header_lookahead.scale_elements
    );
    std::vector<std::uint16_t> header_lookahead_counts(
        header_lookahead.count_elements
    );
    std::vector<std::uint16_t> header_lookahead_positions(
        header_lookahead.position_elements
    );
    std::vector<std::int8_t> header_lookahead_coefficients(
        header_lookahead.coefficient_elements
    );
    resonith_lapped_workspace header_lookahead_workspace = {
        header_lookahead_scales.data(),
        header_lookahead_scales.size(),
        header_lookahead_counts.data(),
        header_lookahead_counts.size(),
        header_lookahead_positions.data(),
        header_lookahead_positions.size(),
        header_lookahead_coefficients.data(),
        header_lookahead_coefficients.size(),
        nullptr,
        0U,
    };

    logical_output.fill(1234);
    logical_start = 99U;
    logical_frames = 99U;
    if (!expect(
            resonith_lapped_compact_decode_record_pair(
                &compact_sequence,
                0U,
                kLappedCompactPacketStream.data() + compact_header_size,
                compact_first_size,
                nullptr,
                0U,
                &packet_workspace,
                nullptr,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_INVALID_ARGUMENT
                && logical_start == 0U
                && logical_frames == 0U
                && std::all_of(
                    logical_output.begin(),
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 stateless pull requires immediate lookahead"
        )) {
        return 1;
    }

    auto compact_transport_corrupted = kLappedCompactPacketStream;
    compact_transport_corrupted[
        compact_transport_corrupted.size() - 1U
    ] ^= 1U;
    logical_output.fill(1234);
    if (!expect(
            resonith_lapped_compact_decode_record_pair(
                &compact_sequence,
                0U,
                compact_transport_corrupted.data() + compact_header_size,
                compact_first_size,
                compact_transport_corrupted.data() + compact_second_offset,
                compact_second_size,
                &header_current_workspace,
                &header_lookahead_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH
                && logical_start == 0U
                && logical_frames == 0U
                && std::all_of(
                    logical_output.begin(),
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 corrupt stateless lookahead writes no PCM"
        )) {
        return 1;
    }

    std::array<std::int16_t, 192> compact_stateless_pcm{};
    if (!expect(
            resonith_lapped_compact_decode_record_pair(
                &compact_sequence,
                0U,
                kLappedCompactPacketStream.data() + compact_header_size,
                compact_first_size,
                kLappedCompactPacketStream.data() + compact_second_offset,
                compact_second_size,
                &header_current_workspace,
                &header_lookahead_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_OK
                && logical_start == 0U
                && logical_frames == 64U,
            "LPS4 stateless first record pair"
        )) {
        return 1;
    }
    std::copy_n(
        logical_output.begin(),
        logical_frames * 2U,
        compact_stateless_pcm.begin()
    );

    logical_output.fill(1234);
    logical_start = 99U;
    logical_frames = 99U;
    if (!expect(
            resonith_lapped_compact_decode_record_prefix(
                &compact_sequence,
                0U,
                kLappedCompactPacketStream.data() + compact_header_size,
                compact_first_size,
                &header_current_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_OK
                && logical_start == 0U
                && logical_frames == 32U
                && std::equal(
                    logical_output.begin(),
                    logical_output.begin() + 64,
                    kExpectedAdaptiveLappedPcm.begin()
                )
                && std::all_of(
                    logical_output.begin() + 64,
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 prefix salvage is exact and writes no unresolved suffix"
        )) {
        return 1;
    }

    auto compact_current_corrupted = kLappedCompactPacketStream;
    compact_current_corrupted[
        compact_header_size + compact_first_size - 1U
    ] ^= 1U;
    logical_output.fill(1234);
    if (!expect(
            resonith_lapped_compact_decode_record_prefix(
                &compact_sequence,
                0U,
                compact_current_corrupted.data() + compact_header_size,
                compact_first_size,
                &header_current_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_CHECKSUM_MISMATCH
                && logical_start == 0U
                && logical_frames == 0U
                && std::all_of(
                    logical_output.begin(),
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 corrupt prefix record writes no PCM"
        )) {
        return 1;
    }
    if (!expect(
            resonith_lapped_compact_decode_record_prefix(
                &compact_sequence,
                0U,
                kLappedCompactPacketStream.data() + compact_header_size,
                compact_first_size,
                &header_current_workspace,
                logical_output.data(),
                63U,
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_OUTPUT_TOO_SMALL
                && logical_start == 0U
                && logical_frames == 0U,
            "LPS4 prefix rejects undersized output"
        )) {
        return 1;
    }
    if (!expect(
            resonith_lapped_compact_decode_record_prefix(
                &compact_sequence,
                1U,
                kLappedCompactPacketStream.data() + compact_second_offset,
                compact_second_size,
                &header_current_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_INVALID_ARGUMENT
                && logical_start == 0U
                && logical_frames == 0U,
            "LPS4 final record forbids prefix salvage"
        )) {
        return 1;
    }

    logical_output.fill(1234);
    if (!expect(
            resonith_lapped_compact_decode_record_pair(
                &compact_sequence,
                0U,
                kLappedCompactPacketStream.data() + compact_header_size,
                compact_first_size + 1U,
                kLappedCompactPacketStream.data() + compact_second_offset,
                compact_second_size,
                &header_current_workspace,
                &compact_lookahead_workspace,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_MALFORMED
                && logical_start == 0U
                && logical_frames == 0U
                && std::all_of(
                    logical_output.begin(),
                    logical_output.end(),
                    [](std::int16_t sample) { return sample == 1234; }
                ),
            "LPS4 stateless record rejects trailing bytes"
        )) {
        return 1;
    }

    if (!expect(
            resonith_lapped_compact_decode_record_pair(
                &compact_sequence,
                1U,
                kLappedCompactPacketStream.data() + compact_second_offset,
                compact_second_size,
                nullptr,
                0U,
                &header_current_workspace,
                nullptr,
                logical_output.data(),
                logical_output.size(),
                &logical_start,
                &logical_frames
            ) == RESONITH_STATUS_OK
                && logical_start == 64U
                && logical_frames == 32U,
            "LPS4 later stateless record survives earlier loss"
        )) {
        return 1;
    }
    std::copy_n(
        logical_output.begin(),
        logical_frames * 2U,
        compact_stateless_pcm.begin()
            + static_cast<std::ptrdiff_t>(logical_start * 2U)
    );
    if (!expect(
            compact_stateless_pcm == kExpectedAdaptiveLappedPcm,
            "LPS4 stateless output equals sequential and monolithic PCM"
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
