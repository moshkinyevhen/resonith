from __future__ import annotations

import os

import numpy as np
import pytest

from reference.maf_p0.causal_basis_field import (
    encode_causal_basis_field_from_mft1,
    parse_causal_basis_field,
)
from reference.maf_p0.causal_law_grammar import CausalLawGrammarLanguage
from reference.maf_p0.maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    pack_maf_typed,
)
from reference.maf_p0.native_core import NativeMain0Decoder


def _mft1_vector() -> bytes:
    basis = MafBasis(
        tuple(
            int(round(
                16000.0 * np.sin(2.0 * np.pi * index / 64.0)
            ))
            for index in range(64)
        )
    )
    instances = []
    for emitter in range(2):
        for occurrence in range(96):
            instances.append(
                MafBasisWarpInstance(
                    emitter_id=emitter,
                    basis_id=0,
                    start=occurrence * 64,
                    sample_count=64,
                    source_position_q16=(occurrence % 8) * 8192,
                    source_step_q16=65536 + (occurrence % 3) * 128,
                    gain_q15=12000 + emitter * 3000,
                    circular=True,
                    end_source_step_q16=(
                        65536 + (occurrence % 3) * 128 + 64
                    ),
                    end_gain_q15=12500 + emitter * 3000,
                )
            )
    return pack_maf_typed(
        sample_rate=48000,
        total_frames=96 * 64,
        render_quantum=256,
        output_channels=2,
        emitter_count=2,
        mixes=(
            MafMix(
                0,
                96 * 64,
                (
                    (32767, 0),
                    (0, 32767),
                ),
            ),
        ),
        bases=(basis,),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=256,
    )


def test_cbf1_compresses_repeated_warp_records_and_round_trips() -> None:
    source = _mft1_vector()
    result = encode_causal_basis_field_from_mft1(
        source,
        grammar_language=CausalLawGrammarLanguage(
            maximum_rules=32,
            maximum_candidate_pairs_per_round=8,
        ),
    )

    assert result.selected_kind == "cbf1"
    assert len(result.cbf_payload) < len(source)
    assert result.report["semantic_source_classes"] is False
    assert result.report["warp_instance_count"] == 192
    parsed = parse_causal_basis_field(result.cbf_payload)
    assert sum(len(events) for events in parsed.emitter_events) == 192
    assert parsed.bases == result.info.bases


def test_cbf1_checksum_corruption_is_rejected() -> None:
    result = encode_causal_basis_field_from_mft1(_mft1_vector())
    damaged = bytearray(result.cbf_payload)
    damaged[-1] ^= 0x20

    with pytest.raises(ValueError):
        parse_causal_basis_field(bytes(damaged))


@pytest.mark.skipif(
    not os.environ.get("RESONITH_NATIVE_CORE"),
    reason="set RESONITH_NATIVE_CORE to the shared Golden Core",
)
def test_cbf1_translation_is_native_sample_identical() -> None:
    decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])
    source = _mft1_vector()
    result = encode_causal_basis_field_from_mft1(source)

    direct = decoder.decode_maf_typed(source).samples
    translated = decoder.decode_maf_typed(
        result.info.mft1_payload
    ).samples

    np.testing.assert_array_equal(translated, direct)

