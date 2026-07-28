from __future__ import annotations

import pytest

from reference.maf_p0.lspf_duration_rdo import (
    LspfDurationCandidate,
    select_lspf_duration_candidate,
)


def _candidate(
    candidate_id: str,
    complete_bytes: int,
    *,
    quality: float = 1.0,
    eligible: bool = True,
) -> LspfDurationCandidate:
    return LspfDurationCandidate(
        candidate_id=candidate_id,
        complete_bytes=complete_bytes,
        quality_eligible=eligible,
        quality_utility=quality,
        bounded_decoder=True,
    )


def test_long_winner_is_retained_while_short_specialization_competes() -> None:
    long = select_lspf_duration_candidate(
        duration_class="long",
        candidates=(
            _candidate("truth", 1000),
            _candidate("long-incumbent", 700),
            _candidate("short-specialist", 920),
        ),
        incumbent_candidate_id="long-incumbent",
        fallback_candidate_id="truth",
    )
    short = select_lspf_duration_candidate(
        duration_class="short",
        candidates=(
            _candidate("truth", 100),
            _candidate("long-incumbent", 108),
            _candidate("short-specialist", 82),
        ),
        incumbent_candidate_id="long-incumbent",
        fallback_candidate_id="truth",
    )

    assert long.selected_candidate_id == "long-incumbent"
    assert short.selected_candidate_id == "short-specialist"
    assert long.report["cross_duration_averaging"] is False


def test_ineligible_challenger_cannot_replace_incumbent() -> None:
    selection = select_lspf_duration_candidate(
        duration_class="long",
        candidates=(
            _candidate("truth", 1000),
            _candidate("incumbent", 800),
            _candidate("smaller-but-bad", 600, eligible=False),
        ),
        incumbent_candidate_id="incumbent",
        fallback_candidate_id="truth",
    )

    assert selection.selected_candidate_id == "incumbent"
    assert selection.report["rejected"]["smaller-but-bad"] == "quality-floor"


def test_one_axis_win_requires_refinement_before_generation_freeze() -> None:
    open_selection = select_lspf_duration_candidate(
        duration_class="long",
        candidates=(
            _candidate("truth", 1200, quality=0.9),
            _candidate("incumbent", 1000, quality=1.0),
            _candidate("quality-point", 1008, quality=1.2),
        ),
        incumbent_candidate_id="incumbent",
        fallback_candidate_id="truth",
        matched_byte_tolerance=10,
        minimum_quality_delta=0.05,
    )
    closed_selection = select_lspf_duration_candidate(
        duration_class="long",
        candidates=open_selection.candidates,
        incumbent_candidate_id="incumbent",
        fallback_candidate_id="truth",
        matched_byte_tolerance=10,
        minimum_quality_delta=0.05,
        dual_axis_refinement_completed=True,
    )

    quality_axes = open_selection.report["axis_results"]["quality-point"]
    assert quality_axes["quality_success"]
    assert quality_axes["dual_axis_refinement_required"]
    assert not open_selection.report["generation_fixation_allowed"]
    assert closed_selection.report["generation_fixation_allowed"]


def test_missing_incumbent_is_rejected() -> None:
    with pytest.raises(ValueError, match="incumbent"):
        select_lspf_duration_candidate(
            duration_class="short",
            candidates=(_candidate("truth", 100),),
            incumbent_candidate_id="missing",
            fallback_candidate_id="truth",
        )
