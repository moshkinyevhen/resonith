"""R-156 gridless multiscale origin and exact-pattern discovery."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np

from .foundry_cuda import GainPhaseCudaFoundry
from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    pack_maf_typed,
)


@dataclass(frozen=True, order=True)
class GridlessLocation:
    """One arbitrary source interval independent of implementation tiles."""

    channel: int
    start: int
    sample_count: int


@dataclass(frozen=True)
class GridlessExactGroup:
    """One sample-verified exact Basis group."""

    digest: str
    locations: tuple[GridlessLocation, ...]


@dataclass(frozen=True)
class GridlessOriginSet:
    """Finite origin declaration for one channel and duration."""

    channel: int
    sample_count: int
    rolling_origin_count: int
    regular_first: int
    regular_hop: int
    regular_count: int
    content_defined_origins: tuple[int, ...]


@dataclass(frozen=True)
class GridlessPatternField:
    """Published R-156 candidate-origin union and exact groups."""

    frames: int
    channels: int
    scales: tuple[int, ...]
    origin_sets: tuple[GridlessOriginSet, ...]
    exact_groups: tuple[GridlessExactGroup, ...]
    report: dict


@dataclass(frozen=True)
class GridlessExactPrediction:
    """One emitted arbitrary-interval exact dictionary predictor."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _regular_count(frames: int, sample_count: int, hop: int) -> int:
    if frames < sample_count:
        return 0
    return (frames - sample_count) // hop + 1


def _verified_exact_groups(
    source: np.ndarray,
    hashes_by_channel: tuple[np.ndarray, ...],
    sample_count: int,
    *,
    maximum_groups: int,
    maximum_instances: int,
) -> list[GridlessExactGroup]:
    """Group equal hashes, then require byte equality before admission."""

    hash_locations: dict[int, list[tuple[int, int]]] = {}
    combined = np.concatenate(hashes_by_channel)
    values, counts = np.unique(combined, return_counts=True)
    repeated = values[counts >= 2]
    if repeated.size == 0:
        return []
    for channel, hashes in enumerate(hashes_by_channel):
        for start in np.flatnonzero(
            np.isin(hashes, repeated)
        ):
            hash_locations.setdefault(
                int(hashes[int(start)]),
                [],
            ).append((channel, int(start)))

    groups: list[GridlessExactGroup] = []
    retained_instances = 0
    for hash_value in sorted(hash_locations):
        locations = hash_locations[hash_value]
        if len(locations) < 2:
            continue
        verified: dict[bytes, list[GridlessLocation]] = {}
        for channel, start in locations:
            segment = np.ascontiguousarray(
                source[start : start + sample_count, channel],
                dtype="<i2",
            )
            if not np.any(segment):
                # Silence is represented by the absence of an active emitter.
                continue
            verified.setdefault(segment.tobytes(), []).append(
                GridlessLocation(channel, start, sample_count)
            )
        for payload, exact_locations in verified.items():
            if len(exact_locations) < 2:
                continue
            capacity = maximum_instances - retained_instances
            if capacity < 2 or len(groups) >= maximum_groups:
                return groups
            exact_locations = exact_locations[:capacity]
            retained_instances += len(exact_locations)
            groups.append(
                GridlessExactGroup(
                    hashlib.sha256(payload).hexdigest(),
                    tuple(sorted(exact_locations)),
                )
            )
    return groups


def discover_gridless_pattern_field(
    samples: np.ndarray,
    *,
    foundry: GainPhaseCudaFoundry,
    scales: tuple[int, ...] = (128, 256, 512, 1024, 2048, 4096),
    regular_hop_divisor: int = 8,
    anchor_window_divisor: int = 2,
    maximum_exact_groups: int = 4096,
    maximum_exact_instances: int = 65536,
) -> GridlessPatternField:
    """Declare rolling, content-defined, and overlapping origins at all scales."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-156 discovery requires frame-major PCM16")
    if (
        not scales
        or tuple(sorted(set(scales))) != scales
        or any(not 16 <= value <= 16384 for value in scales)
        or regular_hop_divisor <= 0
        or anchor_window_divisor <= 0
    ):
        raise ValueError("R-156 finite scale declaration is not canonical")

    frames, channels = source.shape
    origin_sets: list[GridlessOriginSet] = []
    exact_groups: list[GridlessExactGroup] = []
    rolling_origins = 0
    regular_origins = 0
    anchor_origins = 0
    for sample_count in scales:
        if sample_count > frames:
            continue
        hashes_by_channel = []
        for channel in range(channels):
            hashes = foundry.rolling_hashes(
                source[:, channel],
                window_samples=sample_count,
            )
            hashes_by_channel.append(hashes)
            selection_window = max(
                1,
                sample_count // anchor_window_divisor,
            )
            anchors = foundry.content_defined_anchors(
                hashes,
                selection_window=selection_window,
            )
            hop = max(1, sample_count // regular_hop_divisor)
            regular_count = _regular_count(frames, sample_count, hop)
            origin_sets.append(
                GridlessOriginSet(
                    channel,
                    sample_count,
                    int(hashes.size),
                    0,
                    hop,
                    regular_count,
                    tuple(int(value) for value in anchors),
                )
            )
            rolling_origins += int(hashes.size)
            regular_origins += regular_count
            anchor_origins += int(anchors.size)
        capacity_groups = maximum_exact_groups - len(exact_groups)
        capacity_instances = maximum_exact_instances - sum(
            len(group.locations) for group in exact_groups
        )
        if capacity_groups >= 1 and capacity_instances >= 2:
            exact_groups.extend(
                _verified_exact_groups(
                    source,
                    tuple(hashes_by_channel),
                    sample_count,
                    maximum_groups=capacity_groups,
                    maximum_instances=capacity_instances,
                )
            )

    return GridlessPatternField(
        frames,
        channels,
        scales,
        tuple(origin_sets),
        tuple(exact_groups),
        {
            "schema": "resonith-r156-gridless-pattern-field-1",
            "status": "candidate-origin manifest; global RDO pending",
            "frames": int(frames),
            "channels": int(channels),
            "scales": list(scales),
            "rolling_origin_count": rolling_origins,
            "overlapping_regular_origin_count": regular_origins,
            "content_defined_origin_count": anchor_origins,
            "exact_group_count": len(exact_groups),
            "exact_instance_count": sum(
                len(group.locations) for group in exact_groups
            ),
            "regular_hop_divisor": regular_hop_divisor,
            "anchor_window_divisor": anchor_window_divisor,
            "gridless_meaning": True,
            "tiled_execution": True,
        },
    )


def encode_gridless_exact_prediction(
    samples: np.ndarray,
    sample_rate: int,
    field: GridlessPatternField,
    *,
    native_decoder,
    maximum_bases: int = 256,
    maximum_instances: int = 4096,
) -> GridlessExactPrediction:
    """Emit profitable exact groups as arbitrary-start type-8 Basis events."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape != (field.frames, field.channels)
    ):
        raise TypeError("R-156 field differs from its PCM source")
    proposals = []
    for group in field.exact_groups:
        sample_count = group.locations[0].sample_count
        estimated_saving = (
            (len(group.locations) - 1) * sample_count * 2
            - len(group.locations) * 44
            - 16
        )
        if estimated_saving > 0:
            proposals.append((estimated_saving, group))
    proposals.sort(
        key=lambda item: (
            -item[0],
            item[1].locations[0].sample_count,
            item[1].digest,
        )
    )

    occupied = np.zeros(
        (field.channels, field.frames),
        dtype=np.bool_,
    )
    bases: list[MafBasis] = []
    instances: list[MafBasisWarpInstance] = []
    selected_groups = 0
    covered_samples = 0
    for _, group in proposals:
        available = [
            location
            for location in group.locations
            if not np.any(
                occupied[
                    location.channel,
                    location.start : location.start + location.sample_count,
                ]
            )
        ]
        if len(available) < 2 or len(bases) >= maximum_bases:
            continue
        capacity = maximum_instances - len(instances)
        if capacity < 2:
            break
        available = available[:capacity]
        if len(available) < 2:
            break
        canonical = available[0]
        basis_id = len(bases)
        bases.append(
            MafBasis(tuple(
                int(value)
                for value in source[
                    canonical.start : canonical.start
                        + canonical.sample_count,
                    canonical.channel,
                ]
            ))
        )
        for location in available:
            occupied[
                location.channel,
                location.start : location.start + location.sample_count,
            ] = True
            covered_samples += location.sample_count
            instances.append(
                MafBasisWarpInstance(
                    emitter_id=location.channel,
                    basis_id=basis_id,
                    start=location.start,
                    sample_count=location.sample_count,
                    source_position_q16=0,
                    source_step_q16=WARP_ONE_Q16,
                    gain_q15=32768,
                    circular=False,
                )
            )
        selected_groups += 1

    matrix = tuple(
        tuple(
            32767 if output == emitter else 0
            for emitter in range(field.channels)
        )
        for output in range(field.channels)
    )
    payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=field.frames,
        render_quantum=min(4096, field.frames),
        output_channels=field.channels,
        emitter_count=field.channels,
        mixes=(MafMix(0, field.frames, matrix),),
        bases=tuple(bases),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=256,
    )
    reconstruction = native_decoder.decode_maf_typed(
        payload,
        callback_frames=min(997, field.frames),
    ).samples
    for instance in instances:
        start = instance.start
        end = start + instance.sample_count
        if not np.array_equal(
            reconstruction[start:end, instance.emitter_id],
            source[start:end, instance.emitter_id],
        ):
            raise RuntimeError("R-156 native exact placement changed PCM")
    reconstruction.flags.writeable = False
    return GridlessExactPrediction(
        payload,
        reconstruction,
        {
            "schema": "resonith-r156-gridless-exact-prediction-1",
            "status": "native exact predictor; Truth/global RDO pending",
            "basis_count": len(bases),
            "instance_count": len(instances),
            "selected_group_count": selected_groups,
            "covered_samples": covered_samples,
            "predictor_bytes": len(payload),
            "arbitrary_interval_type": "BASIS_WARP_INSTANCE",
        },
    )
