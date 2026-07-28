from __future__ import annotations

import math

import numpy as np

from reference.maf_p0.complex_partial_analyzer import (
    AnalyticPartial,
    ComplexPartialAnalyzerManifest,
    PartialResolution,
    analytic_resolvability_mask,
    observe_complex_partials,
)


def _phase_error(first: float, second: float) -> float:
    return abs((first - second + math.pi) % (2.0 * math.pi) - math.pi)


def _single_resolution(
    fft_samples: int = 1024,
    hop_samples: int = 128,
) -> ComplexPartialAnalyzerManifest:
    return ComplexPartialAnalyzerManifest(
        resolutions=(PartialResolution(fft_samples, hop_samples),),
        logarithmic_band_count=24,
        observations_per_band=2,
        observations_per_detector_frame=48,
        maximum_observations=200_000,
    )


def test_resolvability_oracle_separates_possible_from_impossible() -> None:
    resolvable = analytic_resolvability_mask(
        (
            AnalyticPartial(400.0, 1.0),
            AnalyticPartial(430.0, 1.0),
        ),
        sample_rate=8000,
        fft_samples=1024,
    )
    unresolved = analytic_resolvability_mask(
        (
            AnalyticPartial(400.0, 1.0),
            AnalyticPartial(405.0, 1.0),
        ),
        sample_rate=8000,
        fft_samples=1024,
    )

    assert resolvable == (True, True)
    assert unresolved == (False, False)


def test_direct_dtft_uses_fitted_sub_bin_and_centered_phase() -> None:
    sample_rate = 8000
    sample_count = sample_rate // 2
    frequency_hz = 440.3
    initial_phase = 0.73
    index = np.arange(sample_count, dtype=np.float64)
    source = 12000.0 * np.cos(
        2.0 * np.pi * frequency_hz * index / sample_rate
        + initial_phase
    )
    samples = np.rint(source).astype(np.int16)[:, None]

    result = observe_complex_partials(
        samples,
        sample_rate,
        manifest=_single_resolution(),
    )
    center = sample_count // 2
    candidate = min(
        (
            observation
            for observation in result.observations
            if observation.detector_channel == -1
            and abs(observation.center_sample - center) <= 64
        ),
        key=lambda observation: abs(
            observation.frequency_hz - frequency_hz
        ),
    )
    expected_phase = (
        initial_phase
        + 2.0
        * np.pi
        * frequency_hz
        * candidate.center_sample
        / sample_rate
    )

    assert abs(candidate.frequency_hz - frequency_hz) < 0.5
    assert _phase_error(candidate.aggregate_phase, expected_phase) < 0.08
    assert (
        abs(candidate.frequency_hz - frequency_hz)
        <= candidate.frequency_uncertainty_hz
    )
    assert (
        _phase_error(candidate.aggregate_phase, expected_phase)
        <= candidate.phase_uncertainty_radians
    )
    assert candidate.phase_usable
    assert result.report["phase_evidence_only"]
    assert result.report["phase_authoritative"] is False


def test_per_band_union_retains_weak_tone_below_strong_tone() -> None:
    sample_rate = 8000
    sample_count = sample_rate // 2
    index = np.arange(sample_count, dtype=np.float64)
    source = (
        12000.0 * np.cos(2.0 * np.pi * 440.0 * index / sample_rate)
        + 50.0 * np.cos(
            2.0 * np.pi * 2000.0 * index / sample_rate + 0.2
        )
    )
    samples = np.rint(source).astype(np.int16)[:, None]

    result = observe_complex_partials(
        samples,
        sample_rate,
        manifest=_single_resolution(),
    )
    middle = [
        observation
        for observation in result.observations
        if observation.detector_channel == -1
        and sample_count // 3
        <= observation.center_sample
        <= 2 * sample_count // 3
    ]
    weak_hits = [
        observation
        for observation in middle
        if abs(observation.frequency_hz - 2000.0) < 5.0
    ]

    assert len(weak_hits) >= 6


def test_opposite_polarity_channels_do_not_cancel_observation_phase() -> None:
    sample_rate = 8000
    sample_count = sample_rate // 4
    index = np.arange(sample_count, dtype=np.float64)
    tone = 9000.0 * np.cos(
        2.0 * np.pi * 700.25 * index / sample_rate + 0.4
    )
    samples = np.stack(
        (
            np.rint(tone).astype(np.int16),
            np.rint(-tone).astype(np.int16),
        ),
        axis=1,
    )

    result = observe_complex_partials(
        samples,
        sample_rate,
        manifest=_single_resolution(512, 64),
    )
    candidate = min(
        (
            observation
            for observation in result.observations
            if observation.detector_channel == -1
            and observation.center_sample >= 512
        ),
        key=lambda observation: abs(observation.frequency_hz - 700.25),
    )
    channel_phase_difference = _phase_error(
        candidate.channel_phases[0],
        candidate.channel_phases[1],
    )

    assert candidate.aggregate_amplitude > 1000.0
    assert abs(channel_phase_difference - math.pi) < 0.08
    assert result.report["conflict_group_count"] < len(result.observations)


def test_white_noise_observation_count_respects_finite_manifest() -> None:
    generator = np.random.default_rng(184)
    sample_rate = 8000
    samples = generator.integers(
        -12000,
        12001,
        size=(sample_rate // 8, 1),
        dtype=np.int16,
    )
    manifest = _single_resolution(512, 128)

    result = observe_complex_partials(
        samples,
        sample_rate,
        manifest=manifest,
    )
    frame_count = math.ceil(samples.shape[0] / 128) + 1
    hard_bound = (
        frame_count
        * 2
        * manifest.observations_per_detector_frame
    )

    assert len(result.observations) <= hard_bound
    assert result.report["semantic_source_classes"] is False
    assert result.report["candidate_pool_count"] >= len(result.observations)
    assert "candidate_allocation_reports" in result.report
    assert all(
        len(row["retained_candidate_ids"])
        <= manifest.observations_per_detector_frame
        for row in result.report["candidate_allocation_reports"]
    )


def test_canonical_peak_pool_removes_band_boundary_duplicates() -> None:
    sample_rate = 8000
    sample_count = sample_rate
    index = np.arange(sample_count, dtype=np.float64)
    time = index / sample_rate
    slope_hz_per_second = 800.0
    source = (
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
                1100.0 * time
                - 0.5 * slope_hz_per_second * time**2
            )
            - 0.4
        )
    )
    samples = np.rint(source).astype(np.int16)[:, None]

    result = observe_complex_partials(
        samples,
        sample_rate,
        manifest=_single_resolution(256, 32),
    )
    frame = [
        observation
        for observation in result.observations
        if observation.detector_channel == -1
        and observation.frame_index == 50
    ]
    near_460 = [
        observation
        for observation in frame
        if abs(observation.frequency_hz - 460.0) < 5.0
    ]
    near_940 = [
        observation
        for observation in frame
        if abs(observation.frequency_hz - 940.0) < 5.0
    ]

    assert len(near_460) == 1
    assert len(near_940) == 1
    assert near_460[0].locally_resolvable
    assert near_940[0].locally_resolvable
    assert not any(
        5.0 <= abs(observation.frequency_hz - 460.0) < 20.0
        or 5.0 <= abs(observation.frequency_hz - 940.0) < 20.0
        for observation in frame
    )
