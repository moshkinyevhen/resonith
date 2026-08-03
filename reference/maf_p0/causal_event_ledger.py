"""R-175 exact causal-event ledger with one timeline per anonymous lane."""

from __future__ import annotations

from dataclasses import dataclass
import zlib

from .causal_law_grammar import (
    CausalLawGrammarLanguage,
    decode_causal_law_tokens,
    encode_causal_law_tokens,
)
from .causal_sequence_atlas import CausalEvent


WRAPPER_MAGIC = b"CEZ1"
ROW_MAGIC = b"CER1"
COLUMN_MAGIC = b"CEC1"

_COLUMN_NAMES = (
    "time",
    "basis",
    "pitch",
    "phase",
    "gain",
    "envelope",
    "resonator",
    "route",
)


@dataclass(frozen=True)
class CausalEventLedgerCandidate:
    """Exact RDO choice between complete rows and shared-time columns."""

    selected_kind: str
    packed_stream: bytes
    row_stream_bytes: int
    column_stream_bytes: int
    decoded_events: tuple[CausalEvent, ...]
    report: dict


def _varuint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned varint cannot encode a negative value")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _varsint(value: int) -> bytes:
    zigzag = (value << 1) if value >= 0 else ((-value << 1) - 1)
    return _varuint(zigzag)


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.cursor = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.cursor + count > len(self.payload):
            raise ValueError("truncated causal-event ledger")
        result = self.payload[self.cursor : self.cursor + count]
        self.cursor += count
        return result

    def varuint(self) -> int:
        value = 0
        shift = 0
        while shift <= 63:
            byte = self.take(1)[0]
            value |= (byte & 0x7F) << shift
            if byte < 0x80:
                return value
            shift += 7
        raise ValueError("causal-event ledger varint exceeds 64 bits")

    def varsint(self) -> int:
        value = self.varuint()
        return -(value // 2) - 1 if value & 1 else value // 2


def _wrap(body: bytes) -> bytes:
    checksum = (zlib.crc32(body) & 0xFFFF_FFFF).to_bytes(4, "little")
    return WRAPPER_MAGIC + zlib.compress(body, level=9) + checksum


def _unwrap(payload: bytes) -> bytes:
    if len(payload) < 9 or payload[:4] != WRAPPER_MAGIC:
        raise ValueError("bad causal-event ledger magic")
    try:
        body = zlib.decompress(payload[4:-4])
    except zlib.error as error:
        raise ValueError("invalid causal-event compressed body") from error
    checksum = int.from_bytes(payload[-4:], "little")
    if zlib.crc32(body) & 0xFFFF_FFFF != checksum:
        raise ValueError("causal-event ledger checksum mismatch")
    return body


def _validate_events(
    events: tuple[CausalEvent, ...],
    *,
    maximum_events: int,
) -> None:
    if len(events) > maximum_events:
        raise ValueError("causal-event count exceeds bound")
    if any(
        event.time < 0
        or (index and event.time <= events[index - 1].time)
        for index, event in enumerate(events)
    ):
        raise ValueError("causal events must have strictly increasing time")


def _pack_rows(events: tuple[CausalEvent, ...]) -> bytes:
    body = bytearray(ROW_MAGIC)
    body.extend(_varuint(len(events)))
    previous_time = 0
    for event in events:
        body.extend(_varuint(event.time - previous_time))
        previous_time = event.time
        for value in (
            event.basis_state,
            event.pitch_q,
            event.phase_q,
            event.gain_q,
            event.envelope_q,
            event.resonator_q,
        ):
            body.extend(_varsint(value))
        body.extend(_varuint(len(event.route_q)))
        for value in event.route_q:
            body.extend(_varsint(value))
    return _wrap(bytes(body))


def _columns(
    events: tuple[CausalEvent, ...],
) -> dict[str, tuple[tuple[int, ...], ...]]:
    if not events:
        return {"time": ()}
    time_values = [events[0].time]
    time_values.extend(
        current.time - previous.time
        for previous, current in zip(events, events[1:])
    )
    result = {
        "time": tuple((value,) for value in time_values),
        "basis": tuple((event.basis_state,) for event in events),
        "pitch": tuple((event.pitch_q,) for event in events),
        "phase": tuple((event.phase_q,) for event in events),
        "gain": tuple((event.gain_q,) for event in events),
        "envelope": tuple((event.envelope_q,) for event in events),
        "resonator": tuple((event.resonator_q,) for event in events),
        "route": tuple(event.route_q for event in events),
    }
    return {
        name: values
        for name, values in result.items()
        if name == "time"
        or any(any(value != 0 for value in token) for token in values)
    }


def _pack_columns(
    events: tuple[CausalEvent, ...],
    *,
    grammar_language: CausalLawGrammarLanguage,
) -> tuple[bytes, dict]:
    body = bytearray(COLUMN_MAGIC)
    body.extend(_varuint(len(events)))
    columns = _columns(events)
    body.extend(_varuint(len(columns)))
    column_reports = {}
    for name in _COLUMN_NAMES:
        values = columns.get(name)
        if values is None:
            continue
        candidate = encode_causal_law_tokens(
            values,
            language=grammar_language,
        )
        body.extend(_varuint(_COLUMN_NAMES.index(name)))
        body.extend(_varuint(len(candidate.packed_stream)))
        body.extend(candidate.packed_stream)
        column_reports[name] = candidate.report
    return _wrap(bytes(body)), column_reports


def encode_causal_event_ledger(
    events: tuple[CausalEvent, ...],
    *,
    grammar_language: CausalLawGrammarLanguage = (
        CausalLawGrammarLanguage()
    ),
) -> CausalEventLedgerCandidate:
    """Price complete rows against one shared timeline and factorized columns."""

    _validate_events(events, maximum_events=grammar_language.maximum_tokens)
    row_stream = _pack_rows(events)
    column_stream, column_reports = _pack_columns(
        events,
        grammar_language=grammar_language,
    )
    selected_kind, packed_stream = min(
        (
            ("row", row_stream),
            ("column", column_stream),
        ),
        key=lambda item: (len(item[1]), item[0]),
    )
    decoded = decode_causal_event_ledger(
        packed_stream,
        grammar_language=grammar_language,
    )
    if decoded != events:
        raise RuntimeError("causal-event ledger encoder round-trip failed")
    return CausalEventLedgerCandidate(
        selected_kind=selected_kind,
        packed_stream=packed_stream,
        row_stream_bytes=len(row_stream),
        column_stream_bytes=len(column_stream),
        decoded_events=decoded,
        report={
            "schema": "resonith-r175-causal-event-ledger-1",
            "status": "exact event-ledger RDO; audio integration pending",
            "semantic_source_classes": False,
            "event_count": len(events),
            "one_timeline_per_lane": True,
            "omitted_zero_default_columns": sorted(
                set(_COLUMN_NAMES) - set(_columns(events))
            ),
            "row_bytes": len(row_stream),
            "column_bytes": len(column_stream),
            "selected_kind": selected_kind,
            "selected_bytes": len(packed_stream),
            "column_reports": column_reports,
            "exact_event_round_trip": True,
        },
    )


def decode_causal_event_ledger(
    payload: bytes,
    *,
    grammar_language: CausalLawGrammarLanguage = (
        CausalLawGrammarLanguage()
    ),
) -> tuple[CausalEvent, ...]:
    """Decode and bound one anonymous causal-lane event ledger."""

    reader = _Reader(_unwrap(payload))
    magic = reader.take(4)
    event_count = reader.varuint()
    if event_count > grammar_language.maximum_tokens:
        raise ValueError("causal-event count exceeds decoder bound")
    if magic == ROW_MAGIC:
        events = []
        time = 0
        for _index in range(event_count):
            time += reader.varuint()
            values = [reader.varsint() for _ in range(6)]
            route_width = reader.varuint()
            if route_width > grammar_language.maximum_token_width:
                raise ValueError("causal-event route width exceeds bound")
            route = tuple(reader.varsint() for _ in range(route_width))
            events.append(CausalEvent(time, *values, route))
    elif magic == COLUMN_MAGIC:
        column_count = reader.varuint()
        if column_count > len(_COLUMN_NAMES):
            raise ValueError("causal-event column count exceeds bound")
        columns = {}
        for _index in range(column_count):
            column_id = reader.varuint()
            if column_id >= len(_COLUMN_NAMES):
                raise ValueError("unknown causal-event column")
            name = _COLUMN_NAMES[column_id]
            if name in columns:
                raise ValueError("duplicate causal-event column")
            child = reader.take(reader.varuint())
            values = decode_causal_law_tokens(
                child,
                language=grammar_language,
            )
            if len(values) != event_count:
                raise ValueError("causal-event column length mismatch")
            columns[name] = values
        if "time" not in columns:
            raise ValueError("causal-event timeline is missing")
        scalar_names = (
            "basis",
            "pitch",
            "phase",
            "gain",
            "envelope",
            "resonator",
        )
        scalar_values = {
            name: (
                columns[name]
                if name in columns
                else ((0,),) * event_count
            )
            for name in scalar_names
        }
        route_values = columns.get("route", ((),) * event_count)
        events = []
        time = 0
        for index in range(event_count):
            time_value = columns["time"][index]
            if len(time_value) != 1 or time_value[0] < 0:
                raise ValueError("invalid causal-event time column")
            time += time_value[0]
            scalars = []
            for name in scalar_names:
                token = scalar_values[name][index]
                if len(token) != 1:
                    raise ValueError("causal-event scalar column is not scalar")
                scalars.append(token[0])
            events.append(
                CausalEvent(
                    time,
                    *scalars,
                    tuple(route_values[index]),
                )
            )
    else:
        raise ValueError("unknown causal-event ledger magic")
    if reader.cursor != len(reader.payload):
        raise ValueError("trailing causal-event ledger bytes")
    result = tuple(events)
    _validate_events(
        result,
        maximum_events=grammar_language.maximum_tokens,
    )
    return result

