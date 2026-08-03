from __future__ import annotations

from reference.maf_p0.lspf_analysis_policy import (
    LspfPolicyRequest,
    choose_lspf_analysis_plan,
)


def _request(duration_seconds: int) -> LspfPolicyRequest:
    sample_rate = 48000
    return LspfPolicyRequest(
        duration_frames=duration_seconds * sample_rate,
        sample_rate=sample_rate,
        channels=2,
        latency_target_ms=500,
        encoder_time_budget_x=30.0,
        encoder_memory_bytes=16 << 30,
        gpu_memory_bytes=8 << 30,
        lossless=True,
    )


def test_short_and_long_plans_share_decoder_but_expand_search_deterministically() -> None:
    short = choose_lspf_analysis_plan(_request(8))
    long = choose_lspf_analysis_plan(_request(180))

    assert short.duration_class == "short"
    assert long.duration_class == "long"
    assert short.syntax_family == long.syntax_family == "Resonith/MAF"
    assert short.decoder_profile == long.decoder_profile
    assert short.exact_truth_fallback and long.exact_truth_fallback
    assert short.quality_floors_required and long.quality_floors_required
    assert short.duration_pareto_preservation
    assert long.duration_pareto_preservation
    assert short.incumbent_candidate_required
    assert long.incumbent_candidate_required
    assert max(long.scales_samples) > max(short.scales_samples)
    assert max(long.convolution_depths) >= max(short.convolution_depths)
    assert long.maximum_dictionary_lifetime_frames > (
        short.maximum_dictionary_lifetime_frames
    )
    assert long.to_manifest()["duration_class"] == "long"
