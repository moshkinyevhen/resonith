"""Validate untrusted semantic proposals before they can seed Foundry search.

This module deliberately contains no provider SDK and no network code.  It is
the deterministic boundary between an optional cloud analyst and the local
codec laboratory: provider JSON is accepted only after exact shape, enum,
finite-number, time-range, count, and overlap checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np


SCHEMA_VERSION = "resonith-semantic-proposal-1"
MAX_SOURCES = 12
MAX_REGIONS = 32
MAX_EVENTS = 64
MAX_SPECIALIST_TASKS = 8
MAX_OVERLAP_DEPTH = 8
MAX_BOUNDARY_ANCHORS = 4
MAX_EXACT_BOUNDARY_CANDIDATES = 256

PRIMARY_CLASSES = frozenset(
    {
        "speech",
        "music",
        "noise",
        "mixed",
        "synthetic",
        "tonal",
        "percussion",
        "unknown",
    }
)
SOURCE_CLASSES = frozenset(
    {
        "speech",
        "singing",
        "tonal_instrument",
        "percussion",
        "noise",
        "ambience",
        "effects",
        "mixed",
        "unknown",
    }
)
BASIS_FAMILIES = frozenset(
    {
        "coherent",
        "source_filter",
        "stochastic",
        "transient",
        "resonant",
        "mix",
        "truth",
    }
)
REASON_CODES = frozenset(
    {
        "stable_pitch",
        "formant",
        "noise_texture",
        "attack",
        "decay",
        "repetition",
        "polyphony",
        "unpredictable",
    }
)
ACOUSTIC_STYLES = frozenset(
    {
        "steady_tonal",
        "voiced",
        "unvoiced",
        "attack",
        "decay",
        "stationary_noise",
        "rhythmic",
        "polyphonic",
        "dense_mix",
        "ambience",
        "transition",
        "unknown",
    }
)
EVENT_TYPES = frozenset(
    {
        "source_start",
        "source_stop",
        "section_change",
        "pitch_regime_change",
        "timbre_change",
        "energy_change",
        "rhythm_change",
        "transient",
        "spatial_change",
        "speech_state_change",
        "uncertain_change",
    }
)
SPECIALIST_PROVIDERS = frozenset({"elevenlabs", "azure", "none"})
SPECIALIST_TASKS = frozenset(
    {
        "speech_timing",
        "diarization",
        "voice_isolation",
        "domain_speech",
        "none",
    }
)


class ProposalValidationError(ValueError):
    """Raised when an untrusted provider response violates the local contract."""


@dataclass(frozen=True)
class LocalEvidence:
    """Coarse local evidence used only to audit semantic search proposals."""

    duration_seconds: float
    frame_times: np.ndarray
    energy_change_times: np.ndarray
    onset_times: np.ndarray
    periodic_times: np.ndarray
    stochastic_times: np.ndarray


def _require_exact_keys(
    value: Mapping[str, Any],
    required: frozenset[str],
    *,
    context: str,
) -> None:
    keys = frozenset(value)
    if keys != required:
        missing = sorted(required - keys)
        extra = sorted(keys - required)
        raise ProposalValidationError(
            f"{context} keys mismatch; missing={missing}, extra={extra}"
        )


def _finite_number(value: Any, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProposalValidationError(f"{context} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ProposalValidationError(f"{context} must be finite")
    return result


def _bounded_confidence(value: Any, *, context: str) -> float:
    confidence = _finite_number(value, context=context)
    if not 0.0 <= confidence <= 1.0:
        raise ProposalValidationError(f"{context} must be in [0, 1]")
    return confidence


def _bounded_interval(
    start_value: Any,
    end_value: Any,
    *,
    duration_seconds: float,
    context: str,
) -> tuple[float, float]:
    start = _finite_number(start_value, context=f"{context}.start_seconds")
    end = _finite_number(end_value, context=f"{context}.end_seconds")
    epsilon = max(0.050, duration_seconds * 0.001)
    if start < -epsilon or end > duration_seconds + epsilon or end <= start:
        raise ProposalValidationError(f"{context} interval is outside the clip")
    return max(0.0, start), min(duration_seconds, end)


def _enum(value: Any, allowed: frozenset[str], *, context: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ProposalValidationError(f"{context} has an unsupported value")
    return value


def _check_overlap_depth(
    intervals: Sequence[tuple[float, float]],
    *,
    context: str,
) -> None:
    events: list[tuple[float, int]] = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    # End events sort before start events at the same timestamp.
    events.sort(key=lambda event: (event[0], event[1]))
    depth = 0
    for _, delta in events:
        depth += delta
        if depth > MAX_OVERLAP_DEPTH:
            raise ProposalValidationError(f"{context} overlap limit exceeded")


def validate_semantic_proposals(
    payload: Any,
    expected_clips: Mapping[str, float],
) -> dict[str, Any]:
    """Return a canonical copy of one strictly validated provider response."""

    if not isinstance(payload, Mapping):
        raise ProposalValidationError("response must be an object")
    _require_exact_keys(
        payload,
        frozenset({"schema_version", "clips"}),
        context="response",
    )
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ProposalValidationError("unsupported semantic proposal schema")
    clips = payload["clips"]
    if not isinstance(clips, list) or len(clips) != len(expected_clips):
        raise ProposalValidationError("response must contain every requested clip")

    canonical_clips: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    clip_keys = frozenset(
        {
            "clip_id",
            "duration_seconds",
            "primary_class",
            "sources",
            "regions",
            "events",
            "specialist_tasks",
        }
    )
    for clip_index, clip in enumerate(clips):
        context = f"clips[{clip_index}]"
        if not isinstance(clip, Mapping):
            raise ProposalValidationError(f"{context} must be an object")
        _require_exact_keys(clip, clip_keys, context=context)
        clip_id = clip["clip_id"]
        if not isinstance(clip_id, str) or clip_id not in expected_clips:
            raise ProposalValidationError(f"{context}.clip_id is unknown")
        if clip_id in seen_ids:
            raise ProposalValidationError(f"{context}.clip_id is duplicated")
        seen_ids.add(clip_id)
        expected_duration = float(expected_clips[clip_id])
        reported_duration = _finite_number(
            clip["duration_seconds"],
            context=f"{context}.duration_seconds",
        )
        if abs(reported_duration - expected_duration) > max(
            0.100,
            expected_duration * 0.002,
        ):
            raise ProposalValidationError(f"{context} duration mismatch")

        sources = clip["sources"]
        regions = clip["regions"]
        events = clip["events"]
        tasks = clip["specialist_tasks"]
        if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
            raise ProposalValidationError(f"{context}.sources exceeds its bound")
        if not isinstance(regions, list) or not 1 <= len(regions) <= MAX_REGIONS:
            raise ProposalValidationError(f"{context}.regions exceeds its bound")
        if not isinstance(events, list) or len(events) > MAX_EVENTS:
            raise ProposalValidationError(f"{context}.events exceeds its bound")
        if not isinstance(tasks, list) or len(tasks) > MAX_SPECIALIST_TASKS:
            raise ProposalValidationError(
                f"{context}.specialist_tasks exceeds its bound"
            )

        canonical_sources: list[dict[str, Any]] = []
        source_ids: set[str] = set()
        source_intervals: list[tuple[float, float]] = []
        source_keys = frozenset(
            {
                "source_id",
                "source_class",
                "start_seconds",
                "end_seconds",
                "confidence",
            }
        )
        for source_index, source in enumerate(sources):
            source_context = f"{context}.sources[{source_index}]"
            if not isinstance(source, Mapping):
                raise ProposalValidationError(f"{source_context} must be an object")
            _require_exact_keys(source, source_keys, context=source_context)
            source_id = source["source_id"]
            if (
                not isinstance(source_id, str)
                or not 1 <= len(source_id) <= 48
                or source_id in source_ids
            ):
                raise ProposalValidationError(f"{source_context}.source_id invalid")
            source_ids.add(source_id)
            interval = _bounded_interval(
                source["start_seconds"],
                source["end_seconds"],
                duration_seconds=expected_duration,
                context=source_context,
            )
            source_intervals.append(interval)
            canonical_sources.append(
                {
                    "source_id": source_id,
                    "source_class": _enum(
                        source["source_class"],
                        SOURCE_CLASSES,
                        context=f"{source_context}.source_class",
                    ),
                    "start_seconds": interval[0],
                    "end_seconds": interval[1],
                    "confidence": _bounded_confidence(
                        source["confidence"],
                        context=f"{source_context}.confidence",
                    ),
                }
            )
        _check_overlap_depth(source_intervals, context=f"{context}.sources")

        canonical_regions: list[dict[str, Any]] = []
        region_intervals: list[tuple[float, float]] = []
        region_keys = frozenset(
            {
                "start_seconds",
                "end_seconds",
                "primary_basis",
                "confidence",
                "lifetime_seconds",
                "reason_code",
                "acoustic_style",
            }
        )
        for region_index, region in enumerate(regions):
            region_context = f"{context}.regions[{region_index}]"
            if not isinstance(region, Mapping):
                raise ProposalValidationError(f"{region_context} must be an object")
            _require_exact_keys(region, region_keys, context=region_context)
            interval = _bounded_interval(
                region["start_seconds"],
                region["end_seconds"],
                duration_seconds=expected_duration,
                context=region_context,
            )
            lifetime = _finite_number(
                region["lifetime_seconds"],
                context=f"{region_context}.lifetime_seconds",
            )
            interval_duration = interval[1] - interval[0]
            if not 0.0 < lifetime <= interval_duration + 0.100:
                raise ProposalValidationError(
                    f"{region_context}.lifetime_seconds invalid"
                )
            region_intervals.append(interval)
            canonical_regions.append(
                {
                    "start_seconds": interval[0],
                    "end_seconds": interval[1],
                    "primary_basis": _enum(
                        region["primary_basis"],
                        BASIS_FAMILIES,
                        context=f"{region_context}.primary_basis",
                    ),
                    "confidence": _bounded_confidence(
                        region["confidence"],
                        context=f"{region_context}.confidence",
                    ),
                    "lifetime_seconds": lifetime,
                    "reason_code": _enum(
                        region["reason_code"],
                        REASON_CODES,
                        context=f"{region_context}.reason_code",
                    ),
                    "acoustic_style": _enum(
                        region["acoustic_style"],
                        ACOUSTIC_STYLES,
                        context=f"{region_context}.acoustic_style",
                    ),
                }
            )
        _check_overlap_depth(region_intervals, context=f"{context}.regions")

        canonical_events: list[dict[str, Any]] = []
        event_keys = frozenset(
            {
                "time_seconds",
                "event_type",
                "source_id",
                "acoustic_style",
                "primary_basis",
                "change_strength",
                "confidence",
            }
        )
        for event_index, event in enumerate(events):
            event_context = f"{context}.events[{event_index}]"
            if not isinstance(event, Mapping):
                raise ProposalValidationError(f"{event_context} must be an object")
            _require_exact_keys(event, event_keys, context=event_context)
            event_time = _finite_number(
                event["time_seconds"],
                context=f"{event_context}.time_seconds",
            )
            epsilon = max(0.050, expected_duration * 0.001)
            if not -epsilon <= event_time <= expected_duration + epsilon:
                raise ProposalValidationError(
                    f"{event_context}.time_seconds is outside the clip"
                )
            source_id = event["source_id"]
            if not isinstance(source_id, str) or len(source_id) > 48:
                raise ProposalValidationError(f"{event_context}.source_id invalid")
            if source_id and source_id not in source_ids:
                raise ProposalValidationError(
                    f"{event_context}.source_id is not declared"
                )
            canonical_events.append(
                {
                    "time_seconds": min(
                        expected_duration,
                        max(0.0, event_time),
                    ),
                    "event_type": _enum(
                        event["event_type"],
                        EVENT_TYPES,
                        context=f"{event_context}.event_type",
                    ),
                    "source_id": source_id,
                    "acoustic_style": _enum(
                        event["acoustic_style"],
                        ACOUSTIC_STYLES,
                        context=f"{event_context}.acoustic_style",
                    ),
                    "primary_basis": _enum(
                        event["primary_basis"],
                        BASIS_FAMILIES,
                        context=f"{event_context}.primary_basis",
                    ),
                    "change_strength": _bounded_confidence(
                        event["change_strength"],
                        context=f"{event_context}.change_strength",
                    ),
                    "confidence": _bounded_confidence(
                        event["confidence"],
                        context=f"{event_context}.confidence",
                    ),
                }
            )
        canonical_events.sort(
            key=lambda event: (
                event["time_seconds"],
                event["source_id"],
                event["event_type"],
            )
        )

        primary_class = _enum(
            clip["primary_class"],
            PRIMARY_CLASSES,
            context=f"{context}.primary_class",
        )
        changing_classes = {
            "speech",
            "music",
            "mixed",
            "synthetic",
            "percussion",
        }
        if (
            expected_duration > 5.0
            and primary_class in changing_classes
            and not canonical_events
        ):
            raise ProposalValidationError(
                f"{context} changing long-form clip has no events"
            )

        canonical_tasks: list[dict[str, Any]] = []
        task_keys = frozenset(
            {
                "provider",
                "task",
                "start_seconds",
                "end_seconds",
                "confidence",
            }
        )
        for task_index, task in enumerate(tasks):
            task_context = f"{context}.specialist_tasks[{task_index}]"
            if not isinstance(task, Mapping):
                raise ProposalValidationError(f"{task_context} must be an object")
            _require_exact_keys(task, task_keys, context=task_context)
            interval = _bounded_interval(
                task["start_seconds"],
                task["end_seconds"],
                duration_seconds=expected_duration,
                context=task_context,
            )
            provider = _enum(
                task["provider"],
                SPECIALIST_PROVIDERS,
                context=f"{task_context}.provider",
            )
            task_name = _enum(
                task["task"],
                SPECIALIST_TASKS,
                context=f"{task_context}.task",
            )
            if (provider == "none") != (task_name == "none"):
                raise ProposalValidationError(
                    f"{task_context} none provider/task must match"
                )
            if provider == "none":
                continue
            canonical_tasks.append(
                {
                    "provider": provider,
                    "task": task_name,
                    "start_seconds": interval[0],
                    "end_seconds": interval[1],
                    "confidence": _bounded_confidence(
                        task["confidence"],
                        context=f"{task_context}.confidence",
                    ),
                }
            )

        canonical_clips.append(
            {
                "clip_id": clip_id,
                "duration_seconds": expected_duration,
                "primary_class": primary_class,
                "sources": canonical_sources,
                "regions": canonical_regions,
                "events": canonical_events,
                "specialist_tasks": canonical_tasks,
            }
        )

    if seen_ids != set(expected_clips):
        raise ProposalValidationError("response omitted a requested clip")
    canonical_clips.sort(key=lambda clip: clip["clip_id"])
    return {"schema_version": SCHEMA_VERSION, "clips": canonical_clips}


def analyze_proxy_evidence(
    samples: np.ndarray,
    sample_rate: int,
) -> LocalEvidence:
    """Extract bounded low-resolution evidence from a mono 16-bit proxy."""

    source = np.asarray(samples, dtype=np.float64).reshape(-1)
    if source.size < 64 or not 8000 <= sample_rate <= 48000:
        raise ValueError("invalid semantic proxy")
    source /= 32768.0
    frame_size = max(256, round(sample_rate * 0.064))
    hop = max(128, frame_size // 2)
    frame_count = 1 + max(0, (source.size - frame_size) // hop)
    if frame_count == 0:
        raise ValueError("semantic proxy is too short")

    window = np.hanning(frame_size)
    energy = np.empty(frame_count, dtype=np.float64)
    centroid = np.empty(frame_count, dtype=np.float64)
    flatness = np.empty(frame_count, dtype=np.float64)
    periodicity = np.empty(frame_count, dtype=np.float64)
    frequencies = np.fft.rfftfreq(frame_size, 1.0 / sample_rate)
    minimum_lag = max(1, sample_rate // 800)
    maximum_lag = min(frame_size // 2, sample_rate // 60)

    for frame_index in range(frame_count):
        start = frame_index * hop
        frame = source[start : start + frame_size] * window
        energy[frame_index] = np.sqrt(np.mean(frame * frame) + 1.0e-12)
        magnitude = np.abs(np.fft.rfft(frame)) + 1.0e-12
        magnitude_sum = float(np.sum(magnitude))
        centroid[frame_index] = float(
            np.sum(magnitude * frequencies) / magnitude_sum
        )
        flatness[frame_index] = float(
            np.exp(np.mean(np.log(magnitude))) / np.mean(magnitude)
        )
        # Wiener–Khinchin avoids an O(N²) lag scan on long corpus gates.
        autocorrelation = np.fft.irfft(
            np.abs(np.fft.rfft(frame, n=frame_size * 2)) ** 2,
            n=frame_size * 2,
        )[:frame_size]
        denominator = float(autocorrelation[0]) + 1.0e-12
        periodicity[frame_index] = (
            float(np.max(autocorrelation[minimum_lag:maximum_lag])) / denominator
            if maximum_lag > minimum_lag
            else 0.0
        )

    times = (np.arange(frame_count, dtype=np.float64) * hop + frame_size / 2) / (
        sample_rate
    )
    log_energy = 20.0 * np.log10(energy + 1.0e-12)
    energy_delta = np.abs(np.diff(log_energy, prepend=log_energy[0]))
    centroid_delta = np.abs(np.diff(centroid, prepend=centroid[0]))
    onset_score = energy_delta + centroid_delta / 1000.0
    return LocalEvidence(
        duration_seconds=source.size / sample_rate,
        frame_times=times,
        energy_change_times=times[energy_delta >= np.percentile(energy_delta, 85.0)],
        onset_times=times[onset_score >= np.percentile(onset_score, 90.0)],
        periodic_times=times[periodicity >= 0.45],
        stochastic_times=times[flatness >= 0.32],
    )


def audit_proposals(
    proposal: Mapping[str, Any],
    evidence: Mapping[str, LocalEvidence],
) -> dict[str, Any]:
    """Score proposal families against independent local feature evidence."""

    clips: list[dict[str, Any]] = []
    total_supported = 0
    total_weak = 0
    total_contradicted = 0
    total_boundaries = 0
    nontrivial_clips = 0
    total_events = 0
    for clip in proposal["clips"]:
        clip_id = clip["clip_id"]
        local = evidence[clip_id]
        family_counts: dict[str, dict[str, int]] = {}
        if len(clip["regions"]) > 1:
            nontrivial_clips += 1
            total_boundaries += len(clip["regions"]) - 1
        total_events += len(clip["events"])
        for region in clip["regions"]:
            family = region["primary_basis"]
            start = float(region["start_seconds"])
            end = float(region["end_seconds"])
            duration = end - start
            frame_mask = (local.frame_times >= start) & (local.frame_times < end)
            frame_count = int(np.count_nonzero(frame_mask))
            if family in {"coherent", "source_filter", "resonant"}:
                matching = local.periodic_times
                required_fraction = 0.25 if family == "source_filter" else 0.35
            elif family == "stochastic":
                matching = local.stochastic_times
                required_fraction = 0.35
            elif family == "transient":
                matching = local.onset_times
                required_fraction = 0.0
            else:
                matching = np.empty(0, dtype=np.float64)
                required_fraction = 0.0
            matching_count = int(
                np.count_nonzero((matching >= start) & (matching < end))
            )
            evidence_fraction = matching_count / max(1, frame_count)
            if family in {"mix", "truth"}:
                # These are safe fallbacks, not evidence of a cheaper basis.
                status = "weak"
            elif family == "transient":
                if duration <= 1.0 and matching_count > 0:
                    status = "supported"
                elif duration <= 2.0 and matching_count > 0:
                    status = "weak"
                else:
                    status = "contradicted"
            elif matching_count == 0:
                status = "contradicted"
            elif evidence_fraction >= required_fraction:
                status = "supported"
            elif evidence_fraction >= required_fraction * 0.5:
                status = "weak"
            else:
                status = "contradicted"
            counts = family_counts.setdefault(
                family,
                {"supported": 0, "weak": 0, "contradicted": 0},
            )
            counts[status] += 1
            if status == "supported":
                total_supported += 1
            elif status == "weak":
                total_weak += 1
            else:
                total_contradicted += 1
        clips.append(
            {
                "clip_id": clip_id,
                "primary_class": clip["primary_class"],
                "source_count": len(clip["sources"]),
                "region_count": len(clip["regions"]),
                "event_count": len(clip["events"]),
                "specialist_task_count": len(clip["specialist_tasks"]),
                "family_evidence": family_counts,
                "event_types": sorted(
                    {event["event_type"] for event in clip["events"]}
                ),
                "acoustic_styles": sorted(
                    {
                        region["acoustic_style"]
                        for region in clip["regions"]
                    }
                ),
            }
        )
    return {
        "clips": clips,
        "totals": {
            "supported": total_supported,
            "weak": total_weak,
            "contradicted": total_contradicted,
            "proposed_boundaries": total_boundaries,
            "proposed_events": total_events,
            "nontrivial_clip_count": nontrivial_clips,
        },
    }


def _rank_separated_anchors(
    samples: np.ndarray,
    scores: np.ndarray,
    *,
    maximum_count: int,
    minimum_separation: int,
) -> list[int]:
    """Return deterministic high-score anchors without one peak monopolizing K."""

    order = np.lexsort((samples, -scores))
    selected: list[int] = []
    for index in order:
        candidate = int(samples[int(index)])
        if all(
            abs(candidate - previous) >= minimum_separation
            for previous in selected
        ):
            selected.append(candidate)
            if len(selected) == maximum_count:
                break
    return selected


def _fine_change_anchors(
    source: np.ndarray,
    sample_rate: int,
    event_type: str,
    coarse_sample: int,
) -> list[int]:
    """Locate several sub-millisecond change anchors on original mono PCM."""

    half_window = max(32, round(sample_rate * 0.006))
    radius = max(half_window * 2, round(sample_rate * 0.020))
    hop = max(1, round(sample_rate * 0.00025))
    first = max(half_window, coarse_sample - radius)
    last = min(source.size - half_window - 1, coarse_sample + radius)
    if last < first:
        return [min(max(coarse_sample, 0), source.size - 1)]

    anchors = np.arange(first, last + 1, hop, dtype=np.int64)
    window = np.hanning(half_window)
    scores = np.empty(anchors.size, dtype=np.float64)
    for index, anchor in enumerate(anchors):
        position = int(anchor)
        left = source[position - half_window : position] * window
        right = source[position : position + half_window] * window
        left_rms = math.sqrt(float(left @ left) / half_window + 1.0e-12)
        right_rms = math.sqrt(float(right @ right) / half_window + 1.0e-12)
        energy_delta = 20.0 * math.log10(
            (right_rms + 1.0e-12) / (left_rms + 1.0e-12)
        )
        left_spectrum = np.abs(np.fft.rfft(left)) + 1.0e-12
        right_spectrum = np.abs(np.fft.rfft(right)) + 1.0e-12
        left_spectrum /= float(np.sum(left_spectrum))
        right_spectrum /= float(np.sum(right_spectrum))
        spectral_change = 0.5 * float(
            np.sum(np.abs(right_spectrum - left_spectrum))
        )
        if event_type == "source_start":
            scores[index] = max(energy_delta, 0.0) + 8.0 * spectral_change
        elif event_type == "source_stop":
            scores[index] = max(-energy_delta, 0.0) + 8.0 * spectral_change
        elif event_type == "transient":
            scores[index] = abs(energy_delta) + 10.0 * spectral_change
        elif event_type in {
            "pitch_regime_change",
            "timbre_change",
            "speech_state_change",
        }:
            scores[index] = 12.0 * spectral_change + 0.10 * abs(energy_delta)
        else:
            scores[index] = 8.0 * spectral_change + 0.25 * abs(energy_delta)

    selected = _rank_separated_anchors(
        anchors,
        scores,
        maximum_count=MAX_BOUNDARY_ANCHORS,
        minimum_separation=max(1, round(sample_rate * 0.001)),
    )
    if event_type in {"source_start", "source_stop", "transient"}:
        edge_radius = max(2, round(sample_rate * 0.010))
        edge_start = max(0, selected[0] - edge_radius)
        edge_end = min(source.size, selected[0] + edge_radius + 1)
        absolute = np.abs(source[edge_start:edge_end])
        if absolute.size > 1:
            derivative = np.diff(absolute)
            if event_type == "source_start":
                edge_offset = int(np.argmax(derivative))
            elif event_type == "source_stop":
                edge_offset = int(np.argmin(derivative))
            else:
                edge_offset = int(np.argmax(np.abs(derivative)))
            exact_edge = edge_start + edge_offset + 1
            selected = [exact_edge] + [
                anchor for anchor in selected if anchor != exact_edge
            ]
    return selected[:MAX_BOUNDARY_ANCHORS]


def _expand_exact_candidates(
    anchors: Sequence[int],
    *,
    provider_sample: int,
    sample_count: int,
    sample_rate: int,
) -> list[int]:
    """Expand fine anchors into a bounded, exact source-sample RDO lattice."""

    radius = max(2, round(sample_rate * 0.0005))
    ordered: list[int] = []
    seen: set[int] = set()
    for anchor in [*anchors, provider_sample]:
        clamped = min(max(int(anchor), 0), sample_count - 1)
        for delta in range(radius + 1):
            offsets = (0,) if delta == 0 else (-delta, delta)
            for offset in offsets:
                candidate = clamped + offset
                if 0 <= candidate < sample_count and candidate not in seen:
                    seen.add(candidate)
                    ordered.append(candidate)
                    if len(ordered) == MAX_EXACT_BOUNDARY_CANDIDATES:
                        return ordered
    return ordered


def align_event_boundaries(
    samples: np.ndarray,
    sample_rate: int,
    events: Sequence[Mapping[str, Any]],
    *,
    search_radius_seconds: float = 0.250,
    hop_seconds: float = 0.001,
) -> dict[str, Any]:
    """Snap coarse provider events to deterministic local PCM change evidence.

    The provider timestamp is only the center of a bounded search window.
    Twenty-millisecond analysis frames advance by one millisecond. Each coarse
    peak is then rescored with opposing six-millisecond PCM windows at a
    quarter-millisecond hop and expanded into exact source-sample candidates.
    Exact encoder RDO may test these samples or reject the event entirely.
    """

    source = np.asarray(samples, dtype=np.float64)
    if source.ndim == 2:
        source = np.mean(source, axis=1)
    source = source.reshape(-1)
    if (
        source.size < 64
        or not 8000 <= sample_rate <= 192000
        or not 0.050 <= search_radius_seconds <= 1.0
        or not 0.00025 <= hop_seconds <= 0.010
    ):
        raise ValueError("invalid local event-alignment input")
    source /= 32768.0
    analysis_size = max(64, round(sample_rate * 0.020))
    hop_size = max(1, round(sample_rate * hop_seconds))
    radius_samples = max(analysis_size, round(sample_rate * search_radius_seconds))
    window = np.hanning(analysis_size)

    aligned_events: list[dict[str, Any]] = []
    supported_count = 0
    shifts: list[float] = []
    for event in events:
        provider_time = float(event["time_seconds"])
        event_type = str(event["event_type"])
        center = int(round(provider_time * sample_rate))
        fine_anchors = [min(max(center, 0), source.size - 1)]
        search_start = max(0, center - radius_samples - analysis_size)
        search_end = min(source.size, center + radius_samples + analysis_size)
        excerpt = source[search_start:search_end]
        if event_type == "source_start" and center <= hop_size * 2:
            aligned_sample = 0
            fine_anchors = [aligned_sample]
            support = 1.0
        elif (
            event_type == "source_stop"
            and source.size - center <= hop_size * 2
        ):
            aligned_sample = source.size - 1
            fine_anchors = [aligned_sample]
            support = 1.0
        elif excerpt.size < analysis_size * 2:
            aligned_sample = min(max(center, 0), source.size - 1)
            fine_anchors = [aligned_sample]
            support = 0.0
        else:
            starts = np.arange(
                0,
                excerpt.size - analysis_size + 1,
                hop_size,
                dtype=np.int64,
            )
            energy = np.empty(starts.size, dtype=np.float64)
            centroid = np.empty(starts.size, dtype=np.float64)
            flux = np.zeros(starts.size, dtype=np.float64)
            previous_normalized: np.ndarray | None = None
            frequencies = np.fft.rfftfreq(analysis_size, 1.0 / sample_rate)
            for frame_index, start in enumerate(starts):
                frame = excerpt[start : start + analysis_size] * window
                energy[frame_index] = np.sqrt(np.mean(frame * frame) + 1.0e-12)
                magnitude = np.abs(np.fft.rfft(frame)) + 1.0e-12
                magnitude_sum = float(np.sum(magnitude))
                normalized = magnitude / magnitude_sum
                centroid[frame_index] = float(
                    np.sum(normalized * frequencies)
                )
                if previous_normalized is not None:
                    flux[frame_index] = float(
                        np.sum(np.maximum(normalized - previous_normalized, 0.0))
                    )
                previous_normalized = normalized
            log_energy = 20.0 * np.log10(energy + 1.0e-12)
            energy_delta = np.diff(log_energy, prepend=log_energy[0])
            centroid_delta = np.abs(
                np.diff(centroid, prepend=centroid[0])
            ) / max(1000.0, sample_rate / 8.0)
            if event_type in {"source_start", "transient"}:
                score = np.maximum(energy_delta, 0.0) + 12.0 * flux
            elif event_type == "source_stop":
                score = np.maximum(-energy_delta, 0.0) + 8.0 * flux
            elif event_type in {
                "pitch_regime_change",
                "timbre_change",
                "speech_state_change",
            }:
                score = 5.0 * flux + centroid_delta + 0.15 * np.abs(energy_delta)
            else:
                score = 8.0 * flux + centroid_delta + 0.30 * np.abs(energy_delta)
            frame_centers = search_start + starts + analysis_size // 2
            allowed = np.abs(frame_centers - center) <= radius_samples
            allowed_indices = np.flatnonzero(allowed)
            if allowed_indices.size == 0:
                aligned_sample = min(max(center, 0), source.size - 1)
                fine_anchors = [aligned_sample]
                support = 0.0
            else:
                local_scores = score[allowed_indices]
                best_local = int(np.argmax(local_scores))
                best_index = int(allowed_indices[best_local])
                aligned_sample = int(frame_centers[best_index])
                rank = float(
                    np.count_nonzero(local_scores <= local_scores[best_local])
                ) / local_scores.size
                median = float(np.median(local_scores))
                deviation = float(np.median(np.abs(local_scores - median))) + 1.0e-9
                prominence = max(
                    0.0,
                    (float(local_scores[best_local]) - median) / deviation,
                )
                support = min(1.0, 0.5 * rank + 0.1 * prominence)
                fine_anchors = _fine_change_anchors(
                    source,
                    sample_rate,
                    event_type,
                    aligned_sample,
                )
                aligned_sample = fine_anchors[0]
        exact_candidates = _expand_exact_candidates(
            fine_anchors,
            provider_sample=center,
            sample_count=source.size,
            sample_rate=sample_rate,
        )
        aligned_time = aligned_sample / sample_rate
        shift_ms = (aligned_time - provider_time) * 1000.0
        supported = support >= 0.70
        if supported:
            supported_count += 1
        shifts.append(abs(shift_ms))
        aligned_events.append(
            {
                "provider_time_seconds": provider_time,
                "aligned_sample": aligned_sample,
                "aligned_time_seconds": aligned_time,
                "candidate_samples": exact_candidates,
                "candidate_times_seconds": [
                    sample / sample_rate for sample in exact_candidates
                ],
                "candidate_count": len(exact_candidates),
                "no_boundary_candidate": True,
                "shift_ms": shift_ms,
                "support": support,
                "supported": supported,
                "event_type": event["event_type"],
                "source_id": event["source_id"],
                "primary_basis": event["primary_basis"],
            }
        )
    return {
        "events": aligned_events,
        "summary": {
            "event_count": len(aligned_events),
            "supported_count": supported_count,
            "unsupported_count": len(aligned_events) - supported_count,
            "median_absolute_shift_ms": (
                float(np.median(shifts)) if shifts else 0.0
            ),
            "maximum_absolute_shift_ms": max(shifts, default=0.0),
            "analysis_hop_ms": hop_size * 1000.0 / sample_rate,
            "fine_analysis_hop_ms": (
                max(1, round(sample_rate * 0.00025)) * 1000.0 / sample_rate
            ),
            "exact_candidate_resolution_samples": 1,
            "maximum_candidates_per_event": MAX_EXACT_BOUNDARY_CANDIDATES,
            "search_radius_ms": search_radius_seconds * 1000.0,
        },
    }
