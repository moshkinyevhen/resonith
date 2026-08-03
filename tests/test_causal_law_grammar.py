from __future__ import annotations

import pytest

from reference.maf_p0.causal_law_grammar import (
    CausalLawGrammarLanguage,
    decode_causal_law_tokens,
    encode_causal_law_tokens,
)


def test_hierarchical_grammar_reduces_repeated_causal_ledger() -> None:
    motif = (
        (7, 12, -3, 1),
        (11, -4, 9, 2),
        (5, 8, 2, -7),
        (13, 3, -6, 4),
        (17, -9, 5, 8),
        (19, 1, 7, -2),
    )
    tokens = motif * 500

    result = encode_causal_law_tokens(
        tokens,
        language=CausalLawGrammarLanguage(
            minimum_pair_occurrences=3,
            maximum_rules=64,
            maximum_candidate_pairs_per_round=16,
        ),
    )

    assert result.selected_kind == "grammar"
    assert result.rules
    assert len(result.packed_stream) < result.raw_stream_bytes
    assert result.decoded_tokens == tokens
    assert decode_causal_law_tokens(result.packed_stream) == tokens


def test_unstructured_tokens_round_trip_with_safe_fallback() -> None:
    tokens = tuple(
        (index, index * 1009 + 17, -(index * index + 3))
        for index in range(300)
    )

    result = encode_causal_law_tokens(tokens)

    assert result.selected_kind in {"raw", "dictionary", "grammar"}
    assert result.decoded_tokens == tokens
    assert len(result.packed_stream) <= result.raw_stream_bytes


def test_corruption_is_rejected() -> None:
    result = encode_causal_law_tokens(((1, 2), (1, 2), (1, 2)))
    damaged = bytearray(result.packed_stream)
    damaged[-1] ^= 0x80

    with pytest.raises(ValueError):
        decode_causal_law_tokens(bytes(damaged))


def test_decoder_rejects_expansion_beyond_declared_bound() -> None:
    tokens = ((1,), (2,), (1,), (2,)) * 32
    result = encode_causal_law_tokens(tokens)

    with pytest.raises(ValueError):
        decode_causal_law_tokens(
            result.packed_stream,
            language=CausalLawGrammarLanguage(maximum_tokens=16),
        )

