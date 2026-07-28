"""R-163/R-165 per-duration Pareto selector for LSPF candidates.

The selector never averages across duration classes. It requires the retained
incumbent and independent fallback to be present in every candidate set, and
keeps a one-axis generation open until its bounded refinement is completed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LspfDurationCandidate:
    """One decoder-measured candidate after objective quality evaluation."""

    candidate_id: str
    complete_bytes: int
    quality_eligible: bool
    quality_utility: float
    bounded_decoder: bool

    def __post_init__(self) -> None:
        if not self.candidate_id or self.complete_bytes < 0:
            raise ValueError("invalid duration RDO candidate")


@dataclass(frozen=True)
class LspfDurationSelection:
    """Auditable winner for one input and one duration bucket."""

    duration_class: str
    incumbent_candidate_id: str
    fallback_candidate_id: str
    selected_candidate_id: str
    candidates: tuple[LspfDurationCandidate, ...]
    report: dict


def select_lspf_duration_candidate(
    *,
    duration_class: str,
    candidates: tuple[LspfDurationCandidate, ...],
    incumbent_candidate_id: str,
    fallback_candidate_id: str,
    matched_byte_tolerance: int = 0,
    minimum_quality_delta: float = 0.0,
    dual_axis_refinement_completed: bool = False,
) -> LspfDurationSelection:
    """Select eligible complete bytes while retaining required baselines."""

    if duration_class not in {"short", "medium", "long"}:
        raise ValueError("unknown duration class")
    if matched_byte_tolerance < 0 or minimum_quality_delta < 0.0:
        raise ValueError("invalid duration comparison tolerance")
    identifiers = [candidate.candidate_id for candidate in candidates]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate duration candidate identifier")
    if incumbent_candidate_id not in identifiers:
        raise ValueError("duration incumbent is missing")
    if fallback_candidate_id not in identifiers:
        raise ValueError("independent fallback is missing")

    eligible = tuple(
        candidate
        for candidate in candidates
        if candidate.quality_eligible and candidate.bounded_decoder
    )
    if not eligible:
        raise ValueError("no quality-eligible bounded duration candidate")
    incumbent = next(
        candidate
        for candidate in candidates
        if candidate.candidate_id == incumbent_candidate_id
    )
    winner = min(
        eligible,
        key=lambda candidate: (
            candidate.complete_bytes,
            -candidate.quality_utility,
            candidate.candidate_id,
        ),
    )
    rejected = {
        candidate.candidate_id: (
            "quality-floor"
            if not candidate.quality_eligible
            else "decoder-bound"
            if not candidate.bounded_decoder
            else "complete-bytes-or-equal-byte-quality"
        )
        for candidate in candidates
        if candidate.candidate_id != winner.candidate_id
    }
    axis_results = {}
    successful_ids = []
    refinement_required_ids = []
    for candidate in candidates:
        quality_improved = (
            candidate.quality_utility
            > incumbent.quality_utility + minimum_quality_delta
        )
        rate_success = (
            candidate.candidate_id != incumbent_candidate_id
            and candidate.quality_eligible
            and candidate.bounded_decoder
            and candidate.complete_bytes < incumbent.complete_bytes
        )
        matched_bytes = (
            abs(candidate.complete_bytes - incumbent.complete_bytes)
            <= matched_byte_tolerance
        )
        quality_success = (
            candidate.candidate_id != incumbent_candidate_id
            and candidate.quality_eligible
            and candidate.bounded_decoder
            and matched_bytes
            and quality_improved
        )
        dual_axis_success = rate_success and quality_improved
        successful = rate_success or quality_success
        refinement_required = successful and not dual_axis_success
        if successful:
            successful_ids.append(candidate.candidate_id)
        if refinement_required:
            refinement_required_ids.append(candidate.candidate_id)
        axis_results[candidate.candidate_id] = {
            "rate_success": rate_success,
            "quality_success": quality_success,
            "quality_improved": quality_improved,
            "matched_bytes": matched_bytes,
            "dual_axis_success": dual_axis_success,
            "successful_pareto_candidate": successful,
            "dual_axis_refinement_required": refinement_required,
        }

    retained_pareto_ids = []
    for candidate in eligible:
        dominated = any(
            other.candidate_id != candidate.candidate_id
            and other.complete_bytes <= candidate.complete_bytes
            and other.quality_utility >= candidate.quality_utility
            and (
                other.complete_bytes < candidate.complete_bytes
                or other.quality_utility > candidate.quality_utility
            )
            for other in eligible
        )
        if not dominated:
            retained_pareto_ids.append(candidate.candidate_id)
    fixation_allowed = (
        not refinement_required_ids or dual_axis_refinement_completed
    )
    return LspfDurationSelection(
        duration_class=duration_class,
        incumbent_candidate_id=incumbent_candidate_id,
        fallback_candidate_id=fallback_candidate_id,
        selected_candidate_id=winner.candidate_id,
        candidates=candidates,
        report={
            "schema": "resonith-r165-duration-pareto-selection-1",
            "duration_class": duration_class,
            "incumbent_candidate_id": incumbent_candidate_id,
            "fallback_candidate_id": fallback_candidate_id,
            "selected_candidate_id": winner.candidate_id,
            "selection_order": (
                "quality eligibility, bounded decoder, complete bytes, "
                "equal-byte quality utility, stable candidate id"
            ),
            "cross_duration_averaging": False,
            "matched_byte_tolerance": matched_byte_tolerance,
            "minimum_quality_delta": minimum_quality_delta,
            "successful_candidate_ids": successful_ids,
            "retained_pareto_candidate_ids": retained_pareto_ids,
            "dual_axis_refinement_required_candidate_ids": (
                refinement_required_ids
            ),
            "dual_axis_refinement_completed": (
                dual_axis_refinement_completed
            ),
            "generation_fixation_allowed": fixation_allowed,
            "axis_results": axis_results,
            "candidates": [asdict(candidate) for candidate in candidates],
            "rejected": rejected,
        },
    )
