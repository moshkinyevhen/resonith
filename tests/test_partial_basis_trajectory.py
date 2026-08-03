from __future__ import annotations

import os

import numpy as np
import pytest

from reference.maf_p0.coherent_partial_bundle import CoherentPartialLanguage
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.partial_basis_trajectory import (
    fit_partial_basis_trajectory_prediction,
)


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_anonymous_partial_bases_compile_to_native_trajectories() -> None:
    decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])
    sample_rate = 8000
    frame = np.arange(sample_rate * 2, dtype=np.float64)
    phase = 2.0 * np.pi * 180.0 * frame / sample_rate
    first = (
        9000.0 * np.sin(phase)
        + 3500.0 * np.sin(2.0 * phase + 0.2)
        + 1200.0 * np.sin(3.0 * phase - 0.4)
    )
    second = (
        6500.0 * np.sin(phase)
        + 1500.0 * np.sin(2.0 * phase - 0.7)
        + 4200.0 * np.sin(4.0 * phase + 0.3)
    )
    source = np.where(frame < sample_rate, first, second)
    source = np.clip(np.rint(source), -32768, 32767).astype(np.int16)[:, None]

    result = fit_partial_basis_trajectory_prediction(
        source,
        sample_rate,
        native_decoder=decoder,
        language=CoherentPartialLanguage(
            fft_samples=512,
            hop_samples=64,
            minimum_fundamental_hz=60.0,
            maximum_fundamental_hz=1000.0,
            maximum_partials=12,
            minimum_harmonic_fraction=0.15,
            maximum_basis_clusters=4,
            minimum_cluster_observations=8,
        ),
        maximum_trajectory_observations=24,
        minimum_hold_frames=3,
        phase_candidates=8,
        maximum_normalized_error=1.0,
    )

    assert result.report["semantic_source_classes"] is False
    assert result.report["analytic_basis_count"] >= 1
    assert result.report["transmitted_basis_count"] >= 1
    assert result.report["selected_instance_count"] >= 1
    assert result.reconstruction.shape == source.shape
    assert np.any(result.reconstruction)

