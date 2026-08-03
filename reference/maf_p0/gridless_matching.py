"""R-156 arbitrary-interval transformed and partial-band candidate discovery."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .foundry_cuda import GainPhaseCudaFoundry
from .gridless_pattern_field import (
    GridlessLocation,
    GridlessPatternField,
    discover_gridless_pattern_field,
)
from .partial_spectrum_orbit import (
    reversible_multiband_analysis,
    reversible_multiband_synthesis,
)
from .warp_dictionary import WarpFit, _fingerprint, _fit_warp


@dataclass(frozen=True)
class GridlessWarpProposal:
    """One objective transformed relation between arbitrary intervals."""

    basis: GridlessLocation
    target: GridlessLocation
    fit: WarpFit


@dataclass(frozen=True)
class GridlessWarpField:
    """One multiscale, phase-aware, cross-channel proposal set."""

    proposals: tuple[GridlessWarpProposal, ...]
    report: dict


@dataclass(frozen=True)
class GridlessBandOriginField:
    """One perfect-reconstruction band with gridless candidate origins."""

    band_index: int
    coefficient_count: int
    channel_count: int
    field: GridlessPatternField


@dataclass(frozen=True)
class GridlessPartialSpectrumField:
    """Independent gridless fields over a reversible multiband analysis."""

    levels: int
    padded_frames: int
    bands: tuple[GridlessBandOriginField, ...]
    report: dict


def discover_gridless_warp_proposals(
    samples: np.ndarray,
    field: GridlessPatternField,
    *,
    maximum_normalized_error: float = 2.0e-2,
    maximum_proposals: int = 65536,
    regular_stride: int = 1,
) -> GridlessWarpField:
    """Fit R-155 laws at content and declared overlapping regular origins."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.shape != (field.frames, field.channels)
        or regular_stride <= 0
    ):
        raise TypeError("R-156 warp field differs from its PCM source")
    proposals: list[GridlessWarpProposal] = []
    evaluated_pairs = 0
    buckets_by_scale: dict[
        int,
        dict[bytes, list[GridlessLocation]],
    ] = {}
    for origin_set in field.origin_sets:
        origins = set(origin_set.content_defined_origins)
        origins.update(
            origin_set.regular_first + index * origin_set.regular_hop
            for index in range(
                0,
                origin_set.regular_count,
                regular_stride,
            )
        )
        buckets = buckets_by_scale.setdefault(
            origin_set.sample_count,
            {},
        )
        for start in sorted(origins):
            location = GridlessLocation(
                origin_set.channel,
                start,
                origin_set.sample_count,
            )
            segment = source[
                start : start + origin_set.sample_count,
                origin_set.channel,
            ]
            if int(np.max(np.abs(segment))) < 32:
                continue
            buckets.setdefault(_fingerprint(segment), []).append(location)

    for sample_count in sorted(buckets_by_scale):
        for bucket in buckets_by_scale[sample_count].values():
            if len(bucket) < 2:
                continue
            basis_location = bucket[0]
            basis = source[
                basis_location.start : basis_location.start + sample_count,
                basis_location.channel,
            ]
            for target_location in bucket[1:]:
                if len(proposals) >= maximum_proposals:
                    break
                fit = _fit_warp(
                    basis,
                    source[
                        target_location.start
                            : target_location.start + sample_count,
                        target_location.channel,
                    ],
                )
                evaluated_pairs += 1
                if fit.normalized_error <= maximum_normalized_error:
                    proposals.append(
                        GridlessWarpProposal(
                            basis_location,
                            target_location,
                            fit,
                        )
                    )
            if len(proposals) >= maximum_proposals:
                break
        if len(proposals) >= maximum_proposals:
            break
    return GridlessWarpField(
        tuple(proposals),
        {
            "schema": "resonith-r156-gridless-warp-field-1",
            "status": "objective proposals; global RDO pending",
            "evaluated_pair_count": evaluated_pairs,
            "accepted_proposal_count": len(proposals),
            "scale_count": len(buckets_by_scale),
            "cross_channel_proposal_count": sum(
                item.basis.channel != item.target.channel
                for item in proposals
            ),
            "fractional_phase_proposal_count": sum(
                item.fit.source_position_q16 % (1 << 16) != 0
                for item in proposals
            ),
            "pitch_time_proposal_count": sum(
                abs(item.fit.source_step_q16) != (1 << 16)
                or item.fit.end_source_step_q16 is not None
                for item in proposals
            ),
            "reverse_proposal_count": sum(
                item.fit.source_step_q16 < 0 for item in proposals
            ),
        },
    )


def _fold_band_to_pcm16(values: np.ndarray) -> np.ndarray:
    """Fold int64 coefficients to a collision-safe anchor-proposal lane."""

    source = np.asarray(values, dtype=np.int64)
    folded = source ^ np.right_shift(source, 16) ^ np.right_shift(source, 32)
    return np.asarray(folded & 0xFFFF, dtype=np.uint16).view(np.int16)


def discover_gridless_partial_spectrum(
    samples: np.ndarray,
    *,
    foundry: GainPhaseCudaFoundry,
    levels: int = 3,
    scales: tuple[int, ...] = (16, 32, 64, 128),
) -> GridlessPartialSpectrumField:
    """Build independent gridless origin fields on exact lifting bands."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-156 partial spectrum requires PCM16 channels")
    channel_bands = [
        reversible_multiband_analysis(source[:, channel], levels)
        for channel in range(source.shape[1])
    ]
    padded_frames = channel_bands[0][1]
    bands_per_channel = [item[0] for item in channel_bands]
    fields = []
    for band_index in range(levels + 1):
        matrix = np.column_stack(
            tuple(
                _fold_band_to_pcm16(bands_per_channel[channel][band_index])
                for channel in range(source.shape[1])
            )
        )
        valid_scales = tuple(
            value for value in scales if value <= matrix.shape[0]
        )
        if not valid_scales:
            continue
        raw_field = discover_gridless_pattern_field(
            np.ascontiguousarray(matrix, dtype=np.int16),
            foundry=foundry,
            scales=valid_scales,
        )
        field_report = dict(raw_field.report)
        field_report.update({
            "status": "folded anchor proposals; equality untrusted",
            "exact_group_count": 0,
            "exact_instance_count": 0,
        })
        field = GridlessPatternField(
            raw_field.frames,
            raw_field.channels,
            raw_field.scales,
            raw_field.origin_sets,
            (),
            field_report,
        )
        fields.append(
            GridlessBandOriginField(
                band_index,
                matrix.shape[0],
                matrix.shape[1],
                field,
            )
        )

    # The analysis remains exact; folded lanes only propose anchors.
    for channel in range(source.shape[1]):
        restored = reversible_multiband_synthesis(
            bands_per_channel[channel],
            source.shape[0],
        )
        if not np.array_equal(restored, source[:, channel]):
            raise RuntimeError("R-156 partial-spectrum lifting is not exact")
    return GridlessPartialSpectrumField(
        levels,
        padded_frames,
        tuple(fields),
        {
            "schema": "resonith-r156-gridless-partial-spectrum-1",
            "status": "perfect-reconstruction origin fields; RDO pending",
            "levels": levels,
            "band_count": len(fields),
            "channel_count": source.shape[1],
            "rolling_origin_count": sum(
                item.field.report["rolling_origin_count"] for item in fields
            ),
            "content_defined_origin_count": sum(
                item.field.report["content_defined_origin_count"]
                for item in fields
            ),
            "perfect_reconstruction": True,
            "folded_lane_is_proposer_only": True,
        },
    )
