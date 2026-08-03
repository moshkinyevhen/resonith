from __future__ import annotations

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


def _path_frequencies(tracking, path) -> tuple[np.ndarray, np.ndarray]:
    by_id = {
        observation.observation_id: observation
        for observation in tracking.observations
    }
    times = np.asarray([
        by_id[observation_id].center_sample
        for observation_id in path.observation_ids
    ])
    frequencies = np.asarray([
        by_id[observation_id].frequency_hz
        for observation_id in path.observation_ids
    ])
    return times, frequencies


def test_clean_sub_bin_tone_keeps_frequency_and_phase_continuity() -> None:
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
    for path in tracking.paths:
        _times, frequencies = _path_frequencies(tracking, path)
        candidates.append((
            float(np.median(np.abs(frequencies - frequency_hz))),
            path,
        ))
    frequency_error, best = min(candidates, key=lambda row: row[0])

    assert frequency_error < 0.5
    assert len(best.observation_ids) >= 24
    assert best.mean_phase_error_radians is not None
    assert best.mean_phase_error_radians < 0.03
    assert tracking.report["actual_byte_rdo"] is False
    assert tracking.report["node_value_unit"].startswith("dimensionless")
    assert tracking.report["program_cost_unit"].startswith("provisional")


def test_crossing_chirps_both_survive_top_k_without_sidelobe_displacement() -> None:
    sample_rate = 8000
    duration_seconds = 0.5
    sample_count = int(sample_rate * duration_seconds)
    index = np.arange(sample_count, dtype=np.float64)
    time = index / sample_rate
    slope_hz_per_second = 800.0
    first_frequency = 300.0 + slope_hz_per_second * time
    second_frequency = 700.0 - slope_hz_per_second * time
    samples = np.rint(
        7000.0
        * np.cos(
            2.0
            * np.pi
            * (
                300.0 * time
                + 0.5 * slope_hz_per_second * time**2
            )
            + 0.2
        )
        + 6500.0
        * np.cos(
            2.0
            * np.pi
            * (
                700.0 * time
                - 0.5 * slope_hz_per_second * time**2
            )
            - 0.4
        )
    ).astype(np.int16)[:, None]

    tracking = track_complex_partials(
        _observations(
            samples,
            sample_rate,
            256,
            32,
            observations_per_band=1,
            observations_per_frame=24,
        ),
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
    first_errors = []
    second_errors = []
    for path in tracking.paths:
        sample_times, frequencies = _path_frequencies(tracking, path)
        seconds = sample_times / sample_rate
        first_truth = 300.0 + slope_hz_per_second * seconds
        second_truth = 700.0 - slope_hz_per_second * seconds
        first_errors.append((
            float(np.median(np.abs(frequencies - first_truth))),
            len(frequencies),
        ))
        second_errors.append((
            float(np.median(np.abs(frequencies - second_truth))),
            len(frequencies),
        ))

    best_first = min(first_errors, key=lambda row: row[0])
    best_second = min(second_errors, key=lambda row: row[0])
    assert best_first[0] < 1.0 and best_first[1] >= 24
    assert best_second[0] < 1.0 and best_second[1] >= 8


def test_minus_47_db_line_survives_protected_path_family() -> None:
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
    for path in tracking.paths:
        if "protected-weak-line" not in path.families:
            continue
        _times, frequencies = _path_frequencies(tracking, path)
        protected.append((
            float(np.median(np.abs(frequencies - 2000.0))),
            len(frequencies),
        ))

    best = min(protected, key=lambda row: row[0])
    assert best[0] < 1.0
    assert best[1] >= 24


def test_small_path_union_uses_exact_disjoint_set_oracle() -> None:
    sample_rate = 8000
    sample_count = 1024
    index = np.arange(sample_count, dtype=np.float64)
    samples = np.rint(
        9000.0 * np.cos(2.0 * np.pi * 600.0 * index / sample_rate)
    ).astype(np.int16)[:, None]

    tracking = track_complex_partials(
        _observations(
            samples,
            sample_rate,
            256,
            64,
            observations_per_band=1,
            observations_per_frame=12,
        ),
        sample_rate,
        manifest=ComplexPartialTrackerManifest(
            minimum_track_observations=4,
            k_best_per_state_per_family=2,
            top_k_per_family=4,
            maximum_path_hypotheses=12,
            exact_set_candidate_limit=20,
        ),
    )

    assert len(tracking.paths) <= 12
    assert tracking.selected_set.solver == "exact-small-disjoint-heuristic"
