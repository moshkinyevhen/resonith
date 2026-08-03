from __future__ import annotations

import numpy as np

from reference.maf_p0.coherent_partial_bundle import (
    CoherentPartialLanguage,
    infer_causal_lane_field,
)


def _harmonic_mixture(sample_rate: int, seconds: float) -> np.ndarray:
    frame = np.arange(int(round(sample_rate * seconds)))
    phase = 2.0 * np.pi * 220.0 * frame / sample_rate
    harmonic = (
        9000.0 * np.sin(phase)
        + 4200.0 * np.sin(2.0 * phase + 0.2)
        + 2400.0 * np.sin(3.0 * phase - 0.4)
        + 1300.0 * np.sin(5.0 * phase + 0.7)
    )
    noise = np.random.default_rng(169).normal(0.0, 180.0, frame.size)
    harmonic[frame.size // 2] += 12000.0
    left = np.clip(np.rint(harmonic + noise), -32768, 32767)
    right = np.clip(np.rint(-0.75 * harmonic + noise), -32768, 32767)
    return np.stack((left, right), axis=1).astype(np.int16)


def test_causal_lanes_separate_bundle_and_preserve_exact_truth() -> None:
    samples = _harmonic_mixture(8000, 2.0)
    result = infer_causal_lane_field(
        samples,
        sample_rate=8000,
        language=CoherentPartialLanguage(
            fft_samples=512,
            hop_samples=64,
            minimum_fundamental_hz=80.0,
            maximum_fundamental_hz=800.0,
            maximum_partials=12,
            minimum_harmonic_fraction=0.20,
        ),
    )

    assert result.report["single_primary_lane_ownership"]
    assert result.report["one_final_mixture_truth"]
    assert result.report["exact_integer_reconstruction"]
    assert result.report["partial_basis_count"] >= 1
    assert result.report["partial_observation_count"] > 0
    assert (
        result.report["lane_observation_count"]["coherent_harmonic"]
        > 0
    )
    assert result.lane_observations["stochastic"]
    assert np.any(result.coherent_harmonic)
    assert np.any(result.stochastic)
    np.testing.assert_array_equal(
        result.reconstruction,
        samples.astype(np.int64),
    )


def test_shared_lane_mask_preserves_counterphase_channel_route() -> None:
    samples = _harmonic_mixture(8000, 1.0)
    result = infer_causal_lane_field(
        samples,
        sample_rate=8000,
        language=CoherentPartialLanguage(
            fft_samples=512,
            hop_samples=64,
            minimum_fundamental_hz=80.0,
            maximum_fundamental_hz=800.0,
            maximum_partials=12,
            minimum_harmonic_fraction=0.20,
        ),
    )

    correlation = float(
        np.dot(
            result.coherent_harmonic[:, 0].astype(np.float64),
            result.coherent_harmonic[:, 1].astype(np.float64),
        )
    )
    assert correlation < 0.0
