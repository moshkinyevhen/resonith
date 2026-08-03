"""R-166 maximum-effort official Opus frontier search."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from .opus_anchor import (
    OpusAnchorResult,
    OpusTools,
    run_opus_multichannel_anchor,
)


@dataclass(frozen=True, order=True)
class OpusEffortConfig:
    """One lawful offline opusenc control combination."""

    mode: str
    application: str
    frame_size_ms: float
    phase_inversion: bool


@dataclass(frozen=True)
class OpusEffortPoint:
    """One actual official encode/decode result and its declared utility."""

    config: OpusEffortConfig
    requested_bitrate_kbps: float
    quality_eligible: bool
    quality_utility: float
    quality_details: dict
    result: OpusAnchorResult


@dataclass(frozen=True)
class OpusMaxEffortFrontier:
    """Selected Opus anchor plus all searched control points."""

    selected: OpusEffortPoint
    points: tuple[OpusEffortPoint, ...]
    report: dict


QualityEvaluator = Callable[[OpusAnchorResult], tuple[bool, float, dict]]
AnchorRunner = Callable[..., OpusAnchorResult]


def opus_max_effort_configurations(
    channel_count: int,
) -> tuple[OpusEffortConfig, ...]:
    """Enumerate the applicable official opusenc offline control lattice."""

    if not 1 <= channel_count <= 8:
        raise ValueError("unsupported Opus channel count")
    phase_modes = (True, False) if channel_count >= 2 else (True,)
    return tuple(
        OpusEffortConfig(mode, application, frame_size, phase_inversion)
        for mode in ("vbr", "cvbr", "hard-cbr")
        for application in ("auto", "music", "speech")
        for frame_size in (2.5, 5.0, 10.0, 20.0, 40.0, 60.0)
        for phase_inversion in phase_modes
    )


def _default_quality(
    result: OpusAnchorResult,
) -> tuple[bool, float, dict]:
    return True, float(result.report["snr_db"]), {
        "utility_name": "snr_db_diagnostic",
        "snr_db": float(result.report["snr_db"]),
    }


def run_opus_max_effort_frontier(
    samples: np.ndarray,
    sample_rate: int,
    *,
    target_complete_bytes: int,
    tools: OpusTools,
    matched_byte_tolerance: int | None = None,
    refinement_rounds: int = 3,
    configurations: tuple[OpusEffortConfig, ...] | None = None,
    quality_evaluator: QualityEvaluator | None = None,
    anchor_runner: AnchorRunner = run_opus_multichannel_anchor,
) -> OpusMaxEffortFrontier:
    """Search every declared control and size-match it by actual Ogg bytes."""

    if (
        samples.dtype != np.int16
        or samples.ndim != 2
        or samples.shape[0] == 0
        or not 1 <= samples.shape[1] <= 8
        or sample_rate <= 0
        or target_complete_bytes <= 0
        or not 1 <= refinement_rounds <= 12
    ):
        raise ValueError("invalid maximum-effort Opus frontier request")
    duration_seconds = samples.shape[0] / sample_rate
    tolerance = (
        max(64, target_complete_bytes // 1000)
        if matched_byte_tolerance is None
        else matched_byte_tolerance
    )
    if tolerance < 0:
        raise ValueError("matched-byte tolerance must be non-negative")
    evaluator = quality_evaluator or _default_quality
    configs = configurations or opus_max_effort_configurations(
        samples.shape[1]
    )
    if not configs:
        raise ValueError("maximum-effort Opus lattice is empty")

    minimum_bitrate = 6.0
    maximum_bitrate = 256.0 * samples.shape[1]
    initial_bitrate = float(
        np.clip(
            target_complete_bytes * 8.0 / duration_seconds / 1000.0,
            minimum_bitrate,
            maximum_bitrate,
        )
    )
    points: list[OpusEffortPoint] = []
    selected_by_config: list[OpusEffortPoint] = []
    for config in configs:
        tried: dict[float, OpusEffortPoint] = {}
        bitrate = initial_bitrate
        for _ in range(refinement_rounds + 1):
            key = round(bitrate, 5)
            if key not in tried:
                result = anchor_runner(
                    samples,
                    sample_rate,
                    bitrate_kbps=key,
                    mode=config.mode,
                    application=config.application,
                    frame_size_ms=config.frame_size_ms,
                    phase_inversion=config.phase_inversion,
                    maximum_container_delay_ms=1000,
                    expected_loss_percent=0,
                    tools=tools,
                )
                eligible, utility, details = evaluator(result)
                tried[key] = OpusEffortPoint(
                    config=config,
                    requested_bitrate_kbps=key,
                    quality_eligible=bool(eligible),
                    quality_utility=float(utility),
                    quality_details=details,
                    result=result,
                )
            actual_bytes = len(tried[key].result.payload)
            if actual_bytes <= 0:
                raise RuntimeError("official Opus encoder produced no bytes")
            bitrate = float(
                np.clip(
                    bitrate * target_complete_bytes / actual_bytes,
                    minimum_bitrate,
                    maximum_bitrate,
                )
            )
        config_points = tuple(tried.values())
        points.extend(config_points)
        selected_by_config.append(
            min(
                config_points,
                key=lambda point: (
                    abs(len(point.result.payload) - target_complete_bytes),
                    len(point.result.payload),
                    -point.quality_utility,
                ),
            )
        )

    matched = tuple(
        point
        for point in selected_by_config
        if point.quality_eligible
        and abs(len(point.result.payload) - target_complete_bytes) <= tolerance
    )
    if not matched:
        matched = tuple(
            point
            for point in selected_by_config
            if point.quality_eligible
            and len(point.result.payload) <= target_complete_bytes + tolerance
        )
    if not matched:
        raise RuntimeError("no quality-eligible size-matched Opus point")
    selected = max(
        matched,
        key=lambda point: (
            point.quality_utility,
            -abs(len(point.result.payload) - target_complete_bytes),
            -len(point.result.payload),
            point.config,
        ),
    )
    return OpusMaxEffortFrontier(
        selected=selected,
        points=tuple(points),
        report={
            "schema": "resonith-r166-opus-max-effort-frontier-1",
            "status": "official libopus maximum-effort decoded frontier",
            "target_complete_bytes": target_complete_bytes,
            "matched_byte_tolerance": tolerance,
            "complexity": 10,
            "expected_loss_percent": 0,
            "maximum_container_delay_ms": 1000,
            "configuration_count": len(configs),
            "actual_encode_decode_count": len(points),
            "selected": {
                "config": asdict(selected.config),
                "requested_bitrate_kbps": (
                    selected.requested_bitrate_kbps
                ),
                "stream_bytes": len(selected.result.payload),
                "quality_eligible": selected.quality_eligible,
                "quality_utility": selected.quality_utility,
                "quality_details": selected.quality_details,
                "codec_report": selected.result.report,
            },
            "candidates": [
                {
                    "config": asdict(point.config),
                    "requested_bitrate_kbps": point.requested_bitrate_kbps,
                    "stream_bytes": len(point.result.payload),
                    "quality_eligible": point.quality_eligible,
                    "quality_utility": point.quality_utility,
                    "quality_details": point.quality_details,
                    "codec_report": point.result.report,
                }
                for point in points
            ],
        },
    )
