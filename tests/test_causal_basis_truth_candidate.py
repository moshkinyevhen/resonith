from __future__ import annotations

import os

import numpy as np
import pytest

from reference.maf_p0.causal_basis_truth_candidate import (
    decode_causal_basis_truth_candidate,
    encode_causal_basis_truth_candidate,
)
from reference.maf_p0.native_core import NativeMain0Decoder


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_causal_basis_truth_runs_native_decoder_and_keeps_fallback() -> None:
    decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])
    frame = np.arange(1024, dtype=np.float64)
    basis = np.rint(
        9000.0 * np.sin(2.0 * np.pi * 13.0 * frame / 1024.0)
        + 3000.0 * np.sin(2.0 * np.pi * 29.0 * frame / 1024.0)
    ).astype(np.int16)
    source = np.tile(basis, 16)[:, None]

    result = encode_causal_basis_truth_candidate(
        source,
        48000,
        native_decoder=decoder,
        coefficients_per_frame=12,
        half_window=128,
        band_count=12,
        block_samples=1024,
        maximum_normalized_error=1.0e-6,
    )

    assert result.report["semantic_source_classes"] is False
    assert result.report["independent_decode"]
    assert result.predictor.report["instance_count"] >= 2
    rate, decoded = decode_causal_basis_truth_candidate(
        result.cbf_payload,
        native_decoder=decoder,
    )
    assert rate == 48000
    np.testing.assert_array_equal(decoded, result.reconstruction)
    assert result.selected_kind in {
        "cbf1-truth",
        "mft1-truth",
        "truth-fallback",
    }
    assert len(result.selected_payload) <= len(result.baseline.payload)

