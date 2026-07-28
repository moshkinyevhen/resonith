"""R-176 compressed Causal Basis Field transport for bounded MFT1 warp DSP."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

from .causal_event_ledger import (
    decode_causal_event_ledger,
    encode_causal_event_ledger,
)
from .causal_law_grammar import CausalLawGrammarLanguage
from .causal_sequence_atlas import CausalEvent
from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    pack_maf_typed,
    parse_maf_typed,
)


WRAPPER_MAGIC = b"CBZ1"
BODY_MAGIC = b"CBF1"
VERSION = 2
LEGACY_VERSION = 1


@dataclass(frozen=True)
class CausalBasisFieldInfo:
    """Validated immutable Basis dictionary and anonymous emitter ledgers."""

    sample_rate: int
    total_frames: int
    render_quantum: int
    output_channels: int
    emitter_count: int
    declared_operations_per_frame: int
    bases: tuple[MafBasis, ...]
    mix: MafMix
    emitter_events: tuple[tuple[CausalEvent, ...], ...]
    mft1_payload: bytes


@dataclass(frozen=True)
class CausalBasisFieldCandidate:
    """Complete-byte choice between raw MFT1 and compressed CBF1 transport."""

    selected_kind: str
    selected_payload: bytes
    cbf_payload: bytes
    mft1_payload: bytes
    info: CausalBasisFieldInfo
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


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.cursor = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.cursor + count > len(self.payload):
            raise ValueError("truncated Causal Basis Field")
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
        raise ValueError("CBF1 varint exceeds 64 bits")


def _wrap(body: bytes) -> bytes:
    checksum = (zlib.crc32(body) & 0xFFFF_FFFF).to_bytes(4, "little")
    return WRAPPER_MAGIC + zlib.compress(body, level=9) + checksum


def _unwrap(payload: bytes) -> bytes:
    if len(payload) < 9 or payload[:4] != WRAPPER_MAGIC:
        raise ValueError("bad Causal Basis Field magic")
    try:
        body = zlib.decompress(payload[4:-4])
    except zlib.error as error:
        raise ValueError("invalid Causal Basis Field body") from error
    checksum = int.from_bytes(payload[-4:], "little")
    if zlib.crc32(body) & 0xFFFF_FFFF != checksum:
        raise ValueError("Causal Basis Field checksum mismatch")
    return body


def _identity_mix(channels: int, frames: int) -> MafMix:
    return MafMix(
        0,
        frames,
        tuple(
            tuple(
                32767 if output == emitter else 0
                for emitter in range(channels)
            )
            for output in range(channels)
        ),
    )


def _validate_source_mft1(payload: bytes):
    info = parse_maf_typed(payload)
    static_mix = (
        info.mixes[0]
        if (
            len(info.mixes) == 1
            and info.mixes[0].start == 0
            and info.mixes[0].end == info.total_frames
        )
        else None
    )
    if (
        not 1 <= info.emitter_count <= 64
        or info.filters
        or info.stochastic
        or info.sources
        or info.transients
        or info.basis_instances
        or static_mix is None
    ):
        raise ValueError("CBF1 accepts the bounded Basis-warp MFT1 subset only")
    return info


def _event_from_instance(
    instance: MafBasisWarpInstance,
) -> CausalEvent:
    flags = int(instance.circular)
    if instance.end_source_step_q16 is not None:
        flags |= 2
    if instance.end_gain_q15 is not None:
        flags |= 4
    return CausalEvent(
        time=int(instance.start),
        basis_state=int(instance.basis_id),
        pitch_q=int(instance.source_step_q16),
        phase_q=int(instance.source_position_q16),
        gain_q=int(instance.gain_q15),
        envelope_q=(
            int(instance.end_gain_q15)
            if instance.end_gain_q15 is not None
            else int(instance.gain_q15)
        ),
        resonator_q=(
            int(instance.end_source_step_q16)
            if instance.end_source_step_q16 is not None
            else int(instance.source_step_q16)
        ),
        route_q=(int(instance.sample_count), flags),
    )


def _instance_from_event(
    emitter_id: int,
    event: CausalEvent,
) -> MafBasisWarpInstance:
    if len(event.route_q) != 2:
        raise ValueError("CBF1 warp event route must contain lifetime and flags")
    sample_count, flags = event.route_q
    if flags & ~7:
        raise ValueError("CBF1 warp flags exceed the declared subset")
    return MafBasisWarpInstance(
        emitter_id=emitter_id,
        basis_id=event.basis_state,
        start=event.time,
        sample_count=sample_count,
        source_position_q16=event.phase_q,
        source_step_q16=event.pitch_q,
        gain_q15=event.gain_q,
        circular=bool(flags & 1),
        end_source_step_q16=(
            event.resonator_q if flags & 2 else None
        ),
        end_gain_q15=event.envelope_q if flags & 4 else None,
    )


def encode_causal_basis_field_from_mft1(
    mft1_payload: bytes,
    *,
    grammar_language: CausalLawGrammarLanguage = (
        CausalLawGrammarLanguage()
    ),
) -> CausalBasisFieldCandidate:
    """Compress one verified Basis-warp MFT1 program into CBF1 ledgers."""

    source = _validate_source_mft1(mft1_payload)
    grouped = [[] for _ in range(source.emitter_count)]
    for instance in source.basis_warp_instances:
        grouped[instance.emitter_id].append(_event_from_instance(instance))
    emitter_events = []
    ledgers = []
    ledger_reports = []
    for rows in grouped:
        rows.sort()
        events = tuple(rows)
        if any(
            index and event.time <= events[index - 1].time
            for index, event in enumerate(events)
        ):
            raise ValueError("CBF1 requires one ordered event per emitter time")
        candidate = encode_causal_event_ledger(
            events,
            grammar_language=grammar_language,
        )
        emitter_events.append(events)
        ledgers.append(candidate.packed_stream)
        ledger_reports.append(candidate.report)

    body = bytearray(BODY_MAGIC)
    body.extend(_varuint(VERSION))
    for value in (
        source.sample_rate,
        source.total_frames,
        source.render_quantum,
        source.output_channels,
        source.emitter_count,
        len(source.bases),
    ):
        body.extend(_varuint(value))
    body.extend(_varuint(source.declared_operations_per_frame))
    for row in source.mixes[0].matrix_q15:
        body.extend(struct.pack(f"<{len(row)}h", *row))
    for basis in source.bases:
        body.extend(_varuint(len(basis.samples)))
        body.extend(struct.pack(f"<{len(basis.samples)}h", *basis.samples))
    body.extend(_varuint(len(ledgers)))
    for emitter_id, ledger in enumerate(ledgers):
        body.extend(_varuint(emitter_id))
        body.extend(_varuint(len(ledger)))
        body.extend(ledger)
    cbf_payload = _wrap(bytes(body))
    decoded = parse_causal_basis_field(
        cbf_payload,
        grammar_language=grammar_language,
    )
    if (
        decoded.emitter_events != tuple(emitter_events)
        or decoded.mix != source.mixes[0]
    ):
        raise RuntimeError("CBF1 event round-trip failed")
    selected_kind, selected_payload = min(
        (("cbf1", cbf_payload), ("mft1", mft1_payload)),
        key=lambda item: (len(item[1]), item[0]),
    )
    return CausalBasisFieldCandidate(
        selected_kind=selected_kind,
        selected_payload=selected_payload,
        cbf_payload=cbf_payload,
        mft1_payload=mft1_payload,
        info=decoded,
        report={
            "schema": "resonith-r176-causal-basis-field-1",
            "status": "bounded MFT1 translation transport; final Truth pending",
            "semantic_source_classes": False,
            "basis_count": len(source.bases),
            "warp_instance_count": len(source.basis_warp_instances),
            "emitter_count": source.emitter_count,
            "mft1_bytes": len(mft1_payload),
            "cbf1_bytes": len(cbf_payload),
            "selected_kind": selected_kind,
            "selected_bytes": len(selected_payload),
            "cbf1_sha256": hashlib.sha256(cbf_payload).hexdigest(),
            "ledger_reports": ledger_reports,
            "exact_event_round_trip": True,
        },
    )


def parse_causal_basis_field(
    payload: bytes,
    *,
    grammar_language: CausalLawGrammarLanguage = (
        CausalLawGrammarLanguage()
    ),
) -> CausalBasisFieldInfo:
    """Validate CBF1 and reconstruct its equivalent bounded MFT1 program."""

    reader = _Reader(_unwrap(payload))
    if reader.take(4) != BODY_MAGIC:
        raise ValueError("unsupported Causal Basis Field version")
    version = reader.varuint()
    if version not in {LEGACY_VERSION, VERSION}:
        raise ValueError("unsupported Causal Basis Field version")
    sample_rate = reader.varuint()
    total_frames = reader.varuint()
    render_quantum = reader.varuint()
    output_channels = reader.varuint()
    emitter_count = reader.varuint()
    basis_count = reader.varuint()
    if (
        not 8000 <= sample_rate <= 384000
        or not 1 <= total_frames <= 0xFFFF_FFFF
        or not 1 <= render_quantum <= 4096
        or not 1 <= output_channels <= 8
        or not 1 <= emitter_count <= 64
        or basis_count > 256
    ):
        raise ValueError("CBF1 header exceeds bounded MFT1 subset")
    if version == LEGACY_VERSION:
        if emitter_count != output_channels:
            raise ValueError("legacy CBF1 requires an identity mix")
        mix = _identity_mix(output_channels, total_frames)
        declared_operations_per_frame = 256
    else:
        declared_operations_per_frame = reader.varuint()
        if not 1 <= declared_operations_per_frame <= 0xFFFF_FFFF:
            raise ValueError("CBF1 operation declaration exceeds bounds")
        matrix = tuple(
            tuple(
                struct.unpack("<h", reader.take(2))[0]
                for _emitter in range(emitter_count)
            )
            for _output in range(output_channels)
        )
        mix = MafMix(0, total_frames, matrix)
    bases = []
    for _index in range(basis_count):
        sample_count = reader.varuint()
        if not 2 <= sample_count <= 8 * 2048:
            raise ValueError("CBF1 Basis length exceeds bound")
        values = struct.unpack(
            f"<{sample_count}h",
            reader.take(sample_count * 2),
        )
        bases.append(MafBasis(tuple(values)))

    ledger_count = reader.varuint()
    if ledger_count != emitter_count:
        raise ValueError("CBF1 requires one ledger per emitter")
    emitter_events: list[tuple[CausalEvent, ...] | None] = [
        None
    ] * emitter_count
    instances = []
    for _index in range(ledger_count):
        emitter_id = reader.varuint()
        if emitter_id >= emitter_count or emitter_events[emitter_id] is not None:
            raise ValueError("CBF1 emitter ledger is invalid or duplicated")
        ledger = reader.take(reader.varuint())
        events = decode_causal_event_ledger(
            ledger,
            grammar_language=grammar_language,
        )
        emitter_events[emitter_id] = events
        instances.extend(
            _instance_from_event(emitter_id, event)
            for event in events
        )
    if reader.cursor != len(reader.payload):
        raise ValueError("trailing Causal Basis Field bytes")
    resolved_events = tuple(
        events if events is not None else ()
        for events in emitter_events
    )
    mft1_payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=total_frames,
        render_quantum=render_quantum,
        output_channels=output_channels,
        emitter_count=emitter_count,
        mixes=(mix,),
        bases=tuple(bases),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=declared_operations_per_frame,
    )
    return CausalBasisFieldInfo(
        sample_rate=sample_rate,
        total_frames=total_frames,
        render_quantum=render_quantum,
        output_channels=output_channels,
        emitter_count=emitter_count,
        declared_operations_per_frame=declared_operations_per_frame,
        bases=tuple(bases),
        mix=mix,
        emitter_events=resolved_events,
        mft1_payload=mft1_payload,
    )
