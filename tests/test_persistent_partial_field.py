from __future__ import annotations

import math
import os
from types import SimpleNamespace

import numpy as np
import pytest

from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.partial_graph_fixed import NativePartialGraph
from reference.maf_p0.persistent_partial_field import (
    _boundary_valid_support,
    encode_persistent_partial_truth_candidate,
)


def test_boundary_valid_support_never_bridges_an_invalid_observation() -> None:
    rows = tuple(
        SimpleNamespace(center_sample=center, fft_samples=fft)
        for center, fft in (
            (256, 512),
            (512, 512),
            (800, 2048),
            (1024, 512),
            (1536, 512),
        )
    )
    retained, identifiers, discarded = _boundary_valid_support(
        rows, (10, 11, 12, 13, 14), 2000
    )

    assert tuple(row.center_sample for row in retained) == (1024, 1536)
    assert identifiers == (13, 14)
    assert discarded == 3


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_analyzer_recovered_lane_has_deterministic_continuous_phase_fit() -> None:
    sample_rate = 8000
    sample_count = 3968
    index = np.arange(sample_count, dtype=np.float64)
    source = np.rint(
        8000.0 * np.cos(2.0 * math.pi * 440.3 * index / sample_rate)
    ).astype(np.int16)[:, None]
    core = os.environ["RESONITH_NATIVE_CORE"]

    def encode():
        return encode_persistent_partial_truth_candidate(
            source,
            sample_rate,
            native_graph=NativePartialGraph(core),
            native_decoder=NativeMain0Decoder(core),
            coefficients_per_frame=128,
            half_window=128,
            band_count=8,
        )

    first = encode()
    second = encode()
    assert first.selected_payload == second.selected_payload
    assert np.array_equal(first.selected_reconstruction, second.selected_reconstruction)
    assert first.report["lane_proposals"] == second.report["lane_proposals"]
    lane = first.report["lane_proposals"][0]
    assert lane["span_fit_kinds"] == ["decoder-coordinate-phase-fit"]
    assert len(lane["knot_native_observation_ids"]) == 2
    assert lane["placement_count_before_tail_fusion"] == 2
    assert lane["placement_count"] == 1
    assert lane["tail_fused"] is True
    assert lane["tail_boundary_phase_identity"] is True
    assert lane["maximum_phase_error_radians"] < 0.001
    assert all(
        row["predictor_transport_pcm_identity"]
        and row["complete_decode_identity"]
        and row["s11_record_language_only"]
        for row in first.report["evaluated_subsets"]
    )


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_native_profile_bound_is_an_explicit_truth_fallback() -> None:
    class ProfileBoundGraph:
        def edges(self, *_arguments, **_keywords):
            raise RuntimeError("native edge preflight failed: 6")

    sample_rate = 8000
    index = np.arange(2048, dtype=np.float64)
    source = np.rint(
        6000.0 * np.cos(2.0 * math.pi * 440.3 * index / sample_rate)
    ).astype(np.int16)[:, None]
    core = os.environ["RESONITH_NATIVE_CORE"]
    candidate = encode_persistent_partial_truth_candidate(
        source,
        sample_rate,
        native_graph=ProfileBoundGraph(),
        native_decoder=NativeMain0Decoder(core),
        coefficients_per_frame=64,
        half_window=128,
        band_count=8,
    )

    assert candidate.selected_kind == "truth-fallback"
    assert candidate.selected_payload == candidate.baseline_payload
    assert candidate.report["graph"]["status"].startswith("native profile bound")
