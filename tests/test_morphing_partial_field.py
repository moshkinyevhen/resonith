from __future__ import annotations

import os

import numpy as np
import pytest

from reference.maf_p0.causal_basis_field import (
    encode_causal_basis_field_from_mft1,
    parse_causal_basis_field,
)
from reference.maf_p0.coherent_partial_bundle import CoherentPartialLanguage
from reference.maf_p0.morphing_partial_field import (
    fit_morphing_partial_prediction,
)
from reference.maf_p0.native_core import NativeMain0Decoder


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_morphing_partial_field_tracks_vector_shape_and_compacts() -> None:
    decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])
    sample_rate = 8000
    index = np.arange(sample_rate * 2, dtype=np.float64)
    fundamental = 170.0 + 35.0 * index / index.size
    phase = 2.0 * np.pi * np.cumsum(fundamental) / sample_rate
    source = (
        9000.0 * np.sin(phase)
        + 3500.0 * np.sin(2.0 * phase + 0.2)
        + 1800.0 * np.sin(3.03 * phase - 0.4)
    )
    samples = np.clip(
        np.rint(source),
        -32768,
        32767,
    ).astype(np.int16)[:, None]

    result = fit_morphing_partial_prediction(
        samples,
        sample_rate,
        native_decoder=decoder,
        partial_language=CoherentPartialLanguage(
            fft_samples=512,
            hop_samples=64,
            minimum_fundamental_hz=50.0,
            maximum_fundamental_hz=1000.0,
            maximum_partials=12,
            minimum_harmonic_fraction=0.12,
            maximum_basis_clusters=4,
            minimum_cluster_observations=4,
        ),
    )
    compact = encode_causal_basis_field_from_mft1(result.payload)
    parsed = parse_causal_basis_field(compact.cbf_payload)
    decoded = decoder.decode_maf_typed(parsed.mft1_payload).samples

    assert result.report["semantic_source_classes"] is False
    assert result.report["partial_instance_count"] > 100
    assert result.report["mean_event_normalized_error"] < 0.05
    assert len(compact.cbf_payload) < len(result.payload)
    assert parsed.emitter_count > parsed.output_channels
    np.testing.assert_array_equal(decoded, result.reconstruction)
