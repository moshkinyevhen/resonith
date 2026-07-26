"""Encoder-only acoustic-state change-point segmentation for MAF-P1."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


MAX_FEATURE_FRAMES = 1_000_000
DEFAULT_HOP_SAMPLES = 1024
DEFAULT_MINIMUM_SEGMENT_SAMPLES = 4096
DEFAULT_MAXIMUM_SEGMENT_SAMPLES = 96000
DEFAULT_CHANGE_PENALTY = 200.0
SPECTRAL_BANDS = 12


@dataclass(frozen=True)
class SegmentationResult:
    """Half-open sample intervals and bounded encoder diagnostics."""

    intervals: tuple[tuple[int, int], ...]
    report: dict


def _feature_matrix(samples: np.ndarray, hop_samples: int) -> np.ndarray:
    """Extract compact timbre/energy features; no value enters the bitstream."""

    frame_count = math.ceil(samples.size / hop_samples)
    if frame_count > MAX_FEATURE_FRAMES:
        raise ValueError("acoustic feature frame count exceeds the P1 bound")
    frame_size = 2 * hop_samples
    window = np.hanning(frame_size)
    spectrum_bins = frame_size // 2 + 1

    # Log-spaced bands preserve broad timbre changes without building a large
    # normative model. The entire analysis remains encoder-side floating point.
    edges = np.unique(
        np.rint(
            np.geomspace(1, spectrum_bins, SPECTRAL_BANDS + 1)
        ).astype(np.int64)
    )
    if edges[-1] != spectrum_bins:
        edges = np.append(edges, spectrum_bins)
    band_count = edges.size - 1
    features = np.empty((frame_count, 4 + band_count), dtype=np.float64)

    source = samples.astype(np.float64) / 32768.0
    for frame_index in range(frame_count):
        center = frame_index * hop_samples
        start = center - hop_samples // 2
        frame = np.zeros(frame_size, dtype=np.float64)
        source_start = max(0, start)
        source_end = min(samples.size, start + frame_size)
        destination_start = source_start - start
        frame[
            destination_start : destination_start + source_end - source_start
        ] = source[source_start:source_end]

        power = np.abs(np.fft.rfft(frame * window)) ** 2
        total_power = float(np.sum(power)) + 1e-18
        frequencies = np.arange(power.size, dtype=np.float64)
        log_energy = math.log(float(np.mean(frame * frame)) + 1e-12)
        zero_crossing = float(np.mean(np.signbit(frame[1:]) != np.signbit(frame[:-1])))
        centroid = float(np.dot(power, frequencies) / total_power) / max(
            power.size - 1,
            1,
        )
        flatness = math.exp(float(np.mean(np.log(power + 1e-18)))) / (
            float(np.mean(power)) + 1e-18
        )
        features[frame_index, :4] = (
            log_energy,
            zero_crossing,
            centroid,
            flatness,
        )
        for band_index, (left, right) in enumerate(
            zip(edges[:-1], edges[1:], strict=True)
        ):
            features[frame_index, 4 + band_index] = math.log(
                float(np.sum(power[left:right])) + 1e-12
            )
    return features


def _robust_normalize(features: np.ndarray) -> np.ndarray:
    median = np.median(features, axis=0)
    deviation = np.median(np.abs(features - median), axis=0)
    scale = np.maximum(1.4826 * deviation, 1e-3)
    return np.clip((features - median) / scale, -8.0, 8.0)


def _segment_cost(
    prefix: np.ndarray,
    prefix_square: np.ndarray,
    start: int,
    end: int,
) -> float:
    count = end - start
    total = prefix[end] - prefix[start]
    square = prefix_square[end] - prefix_square[start]
    variance_sum = square - total * total / count
    return max(0.0, float(np.sum(variance_sum)))


def segment_acoustic_states(
    samples: np.ndarray,
    *,
    hop_samples: int = DEFAULT_HOP_SAMPLES,
    minimum_segment_samples: int = DEFAULT_MINIMUM_SEGMENT_SAMPLES,
    maximum_segment_samples: int = DEFAULT_MAXIMUM_SEGMENT_SAMPLES,
    change_penalty: float = DEFAULT_CHANGE_PENALTY,
) -> SegmentationResult:
    """Find a deterministic bounded partition by dynamic-programming RDO proxy."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if samples.size == 0:
        raise ValueError("cannot segment an empty signal")
    if not 256 <= hop_samples <= 4096:
        raise ValueError("segmentation hop is outside the P1 bound")
    if minimum_segment_samples < 2 * hop_samples:
        raise ValueError("minimum acoustic-state lifetime is too short")
    if maximum_segment_samples < minimum_segment_samples:
        raise ValueError("maximum acoustic-state lifetime is below the minimum")
    if not math.isfinite(change_penalty) or change_penalty < 0.0:
        raise ValueError("change penalty must be finite and non-negative")

    features = _robust_normalize(_feature_matrix(samples, hop_samples))
    frame_count = features.shape[0]
    minimum_frames = max(1, math.ceil(minimum_segment_samples / hop_samples))
    maximum_frames = max(
        minimum_frames,
        maximum_segment_samples // hop_samples,
    )
    if frame_count <= minimum_frames:
        intervals = ((0, int(samples.size)),)
        return SegmentationResult(
            intervals,
            {
                "mode": "adaptive",
                "feature_frames": frame_count,
                "hop_samples": hop_samples,
                "state_count": 1,
                "boundary_samples": [],
                "objective": 0.0,
            },
        )

    prefix = np.vstack(
        (
            np.zeros((1, features.shape[1]), dtype=np.float64),
            np.cumsum(features, axis=0),
        )
    )
    prefix_square = np.vstack(
        (
            np.zeros((1, features.shape[1]), dtype=np.float64),
            np.cumsum(features * features, axis=0),
        )
    )
    novelty = np.zeros(frame_count + 1, dtype=np.float64)
    novelty[1:frame_count] = np.linalg.norm(
        features[1:] - features[:-1],
        axis=1,
    )

    # A new state pays a fixed description cost. Strong measured novelty can
    # recover only a bounded fraction, preventing one noisy frame from forcing
    # an arbitrarily dense partition.
    costs = np.full(frame_count + 1, np.inf, dtype=np.float64)
    previous = np.full(frame_count + 1, -1, dtype=np.int64)
    costs[0] = -change_penalty
    for end in range(1, frame_count + 1):
        first = max(0, end - maximum_frames)
        last = end - minimum_frames
        if last < first:
            continue
        for start in range(first, last + 1):
            if not np.isfinite(costs[start]):
                continue
            novelty_credit = (
                min(change_penalty * 0.5, float(novelty[start]))
                if start
                else 0.0
            )
            candidate = (
                costs[start]
                + _segment_cost(prefix, prefix_square, start, end)
                + change_penalty
                - novelty_credit
            )
            if candidate < costs[end]:
                costs[end] = candidate
                previous[end] = start
    if previous[frame_count] < 0:
        raise ValueError("segmentation constraints cannot cover the signal")

    boundaries = [frame_count]
    cursor = frame_count
    while cursor:
        cursor = int(previous[cursor])
        if cursor < 0:
            raise ValueError("invalid segmentation backpointer")
        boundaries.append(cursor)
    boundaries.reverse()

    intervals_list: list[tuple[int, int]] = []
    for start_frame, end_frame in zip(boundaries[:-1], boundaries[1:], strict=True):
        start = start_frame * hop_samples
        end = min(int(samples.size), end_frame * hop_samples)
        intervals_list.append((start, end))
    if intervals_list[-1][1] != samples.size:
        raise ValueError("adaptive segmentation did not cover the final sample")
    boundary_samples = [start for start, _ in intervals_list[1:]]
    return SegmentationResult(
        tuple(intervals_list),
        {
            "mode": "adaptive",
            "feature_frames": frame_count,
            "feature_dimensions": int(features.shape[1]),
            "hop_samples": hop_samples,
            "minimum_segment_samples": minimum_segment_samples,
            "maximum_segment_samples": maximum_segment_samples,
            "change_penalty": float(change_penalty),
            "state_count": len(intervals_list),
            "boundary_samples": boundary_samples,
            "boundary_novelty": [
                float(novelty[sample // hop_samples])
                for sample in boundary_samples
            ],
            "objective": float(costs[frame_count]),
        },
    )
