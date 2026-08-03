"""Reproduce the quarantined R-187 complex-partial analyzer gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from reference.maf_p0.complex_partial_analyzer import (
    ComplexPartialAnalyzerManifest,
    PartialResolution,
    observe_complex_partials,
)
from reference.maf_p0.complex_partial_tracker import (
    ComplexPartialTrackerManifest,
    track_complex_partials,
)


def _observations(
    samples: np.ndarray,
    sample_rate: int,
    fft_samples: int,
    hop_samples: int,
    *,
    observations_per_band: int = 2,
    observations_per_frame: int = 48,
):
    return observe_complex_partials(
        samples,
        sample_rate,
        manifest=ComplexPartialAnalyzerManifest(
            resolutions=(
                PartialResolution(fft_samples, hop_samples),
            ),
            observations_per_band=observations_per_band,
            observations_per_detector_frame=observations_per_frame,
            maximum_observations=1_000_000,
        ),
    )


def _path_frequency_rows(tracking):
    by_id = {
        observation.observation_id: observation
        for observation in tracking.observations
    }
    for path in tracking.paths:
        yield path, np.asarray([
            by_id[observation_id].center_sample
            for observation_id in path.observation_ids
        ]), np.asarray([
            by_id[observation_id].frequency_hz
            for observation_id in path.observation_ids
        ])


def _clean_tone() -> dict:
    sample_rate = 8000
    sample_count = sample_rate // 2
    frequency_hz = 440.3
    index = np.arange(sample_count, dtype=np.float64)
    samples = np.rint(
        12000.0
        * np.cos(
            2.0 * np.pi * frequency_hz * index / sample_rate + 0.73
        )
    ).astype(np.int16)[:, None]
    tracking = track_complex_partials(
        _observations(samples, sample_rate, 1024, 128),
        sample_rate,
        manifest=ComplexPartialTrackerManifest(
            minimum_track_observations=5,
            maximum_frequency_jump_hz=40.0,
            maximum_frequency_slope_hz_per_second=500.0,
            top_k_per_family=128,
        ),
    )
    candidates = []
    for path, _times, frequencies in _path_frequency_rows(tracking):
        candidates.append((
            float(np.median(np.abs(frequencies - frequency_hz))),
            path,
        ))
    frequency_error_hz, path = min(candidates, key=lambda row: row[0])
    return {
        "frequency_error_hz": frequency_error_hz,
        "observation_count": len(path.observation_ids),
        "mean_phase_error_radians": path.mean_phase_error_radians,
    }


def _crossing_chirps() -> dict:
    sample_rate = 8000
    duration_seconds = 0.5
    sample_count = int(sample_rate * duration_seconds)
    index = np.arange(sample_count, dtype=np.float64)
    seconds = index / sample_rate
    slope_hz_per_second = 800.0
    samples = np.rint(
        7000.0
        * np.cos(
            2.0
            * np.pi
            * (
                300.0 * seconds
                + 0.5 * slope_hz_per_second * seconds**2
            )
            + 0.2
        )
        + 6500.0
        * np.cos(
            2.0
            * np.pi
            * (
                700.0 * seconds
                - 0.5 * slope_hz_per_second * seconds**2
            )
            - 0.4
        )
    ).astype(np.int16)[:, None]
    observations = _observations(
        samples,
        sample_rate,
        256,
        32,
        observations_per_band=1,
        observations_per_frame=24,
    )
    tracking = track_complex_partials(
        observations,
        sample_rate,
        manifest=ComplexPartialTrackerManifest(
            neighbors_per_gap=3,
            k_best_per_state_per_family=4,
            minimum_track_observations=8,
            maximum_frequency_jump_hz=60.0,
            maximum_frequency_slope_hz_per_second=2000.0,
            top_k_per_family=64,
        ),
    )
    first_rows = []
    second_rows = []
    for path, sample_times, frequencies in _path_frequency_rows(tracking):
        path_seconds = sample_times / sample_rate
        first_truth = 300.0 + slope_hz_per_second * path_seconds
        second_truth = 700.0 - slope_hz_per_second * path_seconds
        first_rows.append((
            float(np.median(np.abs(frequencies - first_truth))),
            len(frequencies),
        ))
        second_rows.append((
            float(np.median(np.abs(frequencies - second_truth))),
            len(frequencies),
        ))
    first = min(first_rows, key=lambda row: row[0])
    second = min(second_rows, key=lambda row: row[0])
    frame_50 = [
        observation
        for observation in observations.observations
        if observation.detector_channel == -1
        and observation.frame_index == 50
    ]
    return {
        "first_median_frequency_error_hz": first[0],
        "first_observation_count": first[1],
        "second_median_frequency_error_hz": second[0],
        "second_observation_count": second[1],
        "frame_50_frequencies_hz": [
            observation.frequency_hz for observation in frame_50
        ],
        "tracking_report": tracking.report,
    }


def _weak_line() -> dict:
    sample_rate = 8000
    sample_count = sample_rate // 2
    index = np.arange(sample_count, dtype=np.float64)
    samples = np.rint(
        12000.0 * np.cos(2.0 * np.pi * 440.0 * index / sample_rate)
        + 50.0
        * np.cos(
            2.0 * np.pi * 2000.0 * index / sample_rate + 0.2
        )
    ).astype(np.int16)[:, None]
    tracking = track_complex_partials(
        _observations(samples, sample_rate, 1024, 128),
        sample_rate,
        manifest=ComplexPartialTrackerManifest(
            minimum_track_observations=5,
            maximum_frequency_jump_hz=40.0,
            maximum_frequency_slope_hz_per_second=500.0,
            top_k_per_family=256,
        ),
    )
    protected = []
    for path, _times, frequencies in _path_frequency_rows(tracking):
        if "protected-weak-line" not in path.families:
            continue
        protected.append((
            float(np.median(np.abs(frequencies - 2000.0))),
            len(frequencies),
        ))
    best = min(protected, key=lambda row: row[0])
    return {
        "relative_level_db": 20.0 * np.log10(50.0 / 12000.0),
        "median_frequency_error_hz": best[0],
        "observation_count": best[1],
        "protected_family_survived": True,
    }


def _white_noise() -> dict:
    generator = np.random.default_rng(187)
    sample_rate = 8000
    samples = generator.integers(
        -12000,
        12001,
        size=(sample_rate // 8, 1),
        dtype=np.int16,
    )
    result = _observations(samples, sample_rate, 512, 128)
    return {
        "observation_count": len(result.observations),
        "candidate_pool_count": result.report["candidate_pool_count"],
        "candidate_discarded_count": (
            result.report["candidate_discarded_count"]
        ),
        "resource_pruned": result.report["resource_pruned"],
        "per_frame_bound_respected": all(
            len(row["retained_candidate_ids"]) <= 48
            for row in result.report["candidate_allocation_reports"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "experiments/results/"
            "complex_partial_r187_2026-07-28.json"
        ),
    )
    arguments = parser.parse_args()
    started = time.perf_counter()
    report = {
        "schema": "resonith-r187-synthetic-gate-1",
        "status": (
            "analyzer evidence only; no predictor, bitstream, or "
            "compression claim"
        ),
        "clean_tone": _clean_tone(),
        "crossing_chirps": _crossing_chirps(),
        "weak_line": _weak_line(),
        "white_noise": _white_noise(),
    }
    report["wall_seconds"] = time.perf_counter() - started
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
