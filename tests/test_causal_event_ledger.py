from __future__ import annotations

import pytest

from reference.maf_p0.causal_event_ledger import (
    decode_causal_event_ledger,
    encode_causal_event_ledger,
)
from reference.maf_p0.causal_law_grammar import CausalLawGrammarLanguage
from reference.maf_p0.causal_sequence_atlas import CausalEvent


def _structured_events(count: int) -> tuple[CausalEvent, ...]:
    events = []
    time = 0
    for index in range(count):
        time += 7 if index % 17 else 12
        pitch, phase, gain, envelope, resonator = (
            ((index // divisor) * multiplier) % 10007 - 5000
            for divisor, multiplier in (
                (7, 1009),
                (11, 917),
                (15, 811),
                (19, 613),
                (23, 419),
            )
        )
        events.append(
            CausalEvent(
                time,
                0,
                pitch,
                phase,
                gain,
                envelope,
                resonator,
                (),
            )
        )
    return tuple(events)


def test_shared_timeline_column_ledger_round_trips_and_can_win() -> None:
    events = _structured_events(2000)
    result = encode_causal_event_ledger(
        events,
        grammar_language=CausalLawGrammarLanguage(
            maximum_rules=32,
            maximum_candidate_pairs_per_round=8,
        ),
    )

    assert result.selected_kind == "column"
    assert result.column_stream_bytes < result.row_stream_bytes
    assert result.report["one_timeline_per_lane"]
    assert "route" in result.report["omitted_zero_default_columns"]
    assert result.decoded_events == events
    assert decode_causal_event_ledger(result.packed_stream) == events


def test_row_fallback_remains_available_for_irregular_events() -> None:
    events = tuple(
        CausalEvent(
            index * index + index + 1,
            index % 7,
            index * 1009,
            index * 917,
            -(index * 811),
            index * 613,
            index * 419,
            (index * 307, -(index * 211)),
        )
        for index in range(1, 300)
    )
    result = encode_causal_event_ledger(events)

    assert result.selected_kind in {"row", "column"}
    assert result.decoded_events == events
    assert len(result.packed_stream) <= result.row_stream_bytes


def test_corrupt_event_ledger_is_rejected() -> None:
    result = encode_causal_event_ledger(_structured_events(32))
    damaged = bytearray(result.packed_stream)
    damaged[-2] ^= 0x40

    with pytest.raises(ValueError):
        decode_causal_event_ledger(bytes(damaged))
