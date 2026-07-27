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
MAX_SPECIALIST_TASKS = 8
MAX_OVERLAP_DEPTH = 8

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
        tasks = clip["specialist_tasks"]
        if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
            raise ProposalValidationError(f"{context}.sources exceeds its bound")
        if not isinstance(regions, list) or not 1 <= len(regions) <= MAX_REGIONS:
            raise ProposalValidationError(f"{context}.regions exceeds its bound")
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
                }
            )
        _check_overlap_depth(region_intervals, context=f"{context}.regions")

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
                "primary_class": _enum(
                    clip["primary_class"],
                    PRIMARY_CLASSES,
                    context=f"{context}.primary_class",
                ),
                "sources": canonical_sources,
                "regions": canonical_regions,
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
    for clip in proposal["clips"]:
        clip_id = clip["clip_id"]
        local = evidence[clip_id]
        family_counts: dict[str, dict[str, int]] = {}
        for region in clip["regions"]:
            family = region["primary_basis"]
            midpoint = 0.5 * (
                float(region["start_seconds"]) + float(region["end_seconds"])
            )
            radius = max(0.150, 0.5 * float(region["lifetime_seconds"]))
            if family in {"coherent", "source_filter", "resonant"}:
                matching = local.periodic_times
            elif family == "stochastic":
                matching = local.stochastic_times
            elif family == "transient":
                matching = local.onset_times
            else:
                matching = local.energy_change_times
            if matching.size == 0:
                status = "contradicted"
            else:
                distance = float(np.min(np.abs(matching - midpoint)))
                if distance <= radius:
                    status = "supported"
                elif distance <= radius * 2.0:
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
                "specialist_task_count": len(clip["specialist_tasks"]),
                "family_evidence": family_counts,
            }
        )
    return {
        "clips": clips,
        "totals": {
            "supported": total_supported,
            "weak": total_weak,
            "contradicted": total_contradicted,
        },
    }
