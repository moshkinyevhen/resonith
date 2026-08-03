from __future__ import annotations

import os

import numpy as np
import pytest

from reference.maf_p0.anonymous_causal_program import (
    AnonymousCausalProgramLanguage,
    compile_anonymous_causal_program,
    decode_anonymous_causal_program,
)
from reference.maf_p0.coherent_partial_bundle import CoherentPartialLanguage
from reference.maf_p0.native_core import NativeMain0Decoder


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_anonymous_program_exact_subset_keeps_one_final_truth() -> None:
    decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])
    sample_rate = 8000
    frame = np.arange(sample_rate, dtype=np.float64)
    source = (
        7000.0 * np.sin(2.0 * np.pi * 180.0 * frame / sample_rate)
        + 2600.0 * np.sin(
            2.0 * np.pi * 360.0 * frame / sample_rate + 0.25
        )
    )
    samples = np.clip(
        np.rint(source),
        -32768,
        32767,
    ).astype(np.int16)[:, None]
    language = AnonymousCausalProgramLanguage(
        partial_language=CoherentPartialLanguage(
            fft_samples=512,
            hop_samples=64,
            minimum_fundamental_hz=50.0,
            maximum_fundamental_hz=1000.0,
            maximum_partials=12,
            minimum_harmonic_fraction=0.15,
            maximum_basis_clusters=4,
            minimum_cluster_observations=4,
        ),
        maximum_trajectory_observations=256,
        minimum_hold_frames=2,
        phase_candidates=8,
        maximum_normalized_error=1.0,
        enabled_families=("coherent",),
    )

    result = compile_anonymous_causal_program(
        samples,
        sample_rate,
        native_decoder=decoder,
        coefficients_per_frame=24,
        half_window=128,
        band_count=12,
        language=language,
    )

    assert result.report["semantic_source_classes"] is False
    assert result.report["one_final_mixture_truth"]
    assert result.report["tested_subset_count"] <= 5
    assert "coherent-morphing-partials" in result.report["column_families"]
    assert result.selected_kind in {
        "anonymous-causal-program",
        "truth-fallback",
    }
    assert len(result.selected_payload) <= len(result.baseline.payload)
    if result.payload:
        rate, decoded = decode_anonymous_causal_program(
            result.payload,
            native_decoder=decoder,
        )
        assert rate == sample_rate
        np.testing.assert_array_equal(decoded, result.reconstruction)
