"""Independent builder/parser for the prospective R-130 MFT1 stream."""

from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib

import numpy as np


MAGIC = b"MFT1"
VERSION = 1
HEADER_BYTES = 64
RECORD_HEADER = struct.Struct("<BBHI")
NO_EMITTER = 0xFFFF
NO_REFERENCE = 0xFFFF
FILTER = 1
STOCHASTIC = 2
SOURCE_FILTER = 3
TRANSIENT = 4
MIX = 5
BASIS = 6
BASIS_INSTANCE = 7
BASIS_WARP_INSTANCE = 8
IMPULSE_EXCITATION = 1
STOCHASTIC_EXCITATION = 2
PERIODIC_BASIS_EXCITATION = 3
MAX_FILTER_ORDER = 16
MAX_CHANNELS = 8
MAX_EMITTERS = 64
MAX_RENDER_QUANTUM = 4096
MAX_TRANSIENT_SAMPLES = 512
MAX_WARP_INSTANCE_SAMPLES = 65535
WARP_ONE_Q16 = 1 << 16
MAX_WARP_STEP_Q16 = 8 * WARP_ONE_Q16


@dataclass(frozen=True)
class MafFilter:
    """One immutable stable reflection-coefficient filter."""

    reflection_q15: tuple[int, ...]


@dataclass(frozen=True)
class MafBasis:
    """One immutable periodic PCM16 waveform."""

    samples: tuple[int, ...]


@dataclass(frozen=True)
class MafBasisInstance:
    """One finite placement of an immutable Basis subrange."""

    emitter_id: int
    basis_id: int
    start: int
    gain_q15: int
    source_offset: int
    sample_count: int
    circular: bool = False
    end_gain_q15: int | None = None
    reverse: bool = False


@dataclass(frozen=True)
class MafBasisWarpInstance:
    """One bounded fractional phase/pitch/time placement of a Basis."""

    emitter_id: int
    basis_id: int
    start: int
    sample_count: int
    source_position_q16: int
    source_step_q16: int
    gain_q15: int
    circular: bool = False
    end_source_step_q16: int | None = None
    end_gain_q15: int | None = None


@dataclass(frozen=True)
class MafStochastic:
    """One counter-addressed field lifetime."""

    emitter_id: int | None
    start: int
    end: int
    gain_q15: int


@dataclass(frozen=True)
class MafSourceFilter:
    """One causal source-filter lifetime with exactly one excitation family."""

    emitter_id: int
    filter_id: int
    excitation: int
    reference_id: int | None
    start: int
    end: int
    gain_q15: int
    phase_origin_q32: int = 0
    phase_increment_q32: int = 0


@dataclass(frozen=True)
class MafTransient:
    """One finite onset-addressed immutable PCM16 shape."""

    emitter_id: int
    onset: int
    gain_q15: int
    samples: tuple[int, ...]


@dataclass(frozen=True)
class MafMix:
    """One output-major Q1.15 matrix lifetime."""

    start: int
    end: int
    matrix_q15: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class MafTypedInfo:
    """Validated independent view of one MFT1 stream."""

    sample_rate: int
    total_frames: int
    render_quantum: int
    output_channels: int
    emitter_count: int
    stream_seed: int
    declared_operations_per_frame: int
    filters: tuple[MafFilter, ...]
    stochastic: tuple[MafStochastic, ...]
    sources: tuple[MafSourceFilter, ...]
    transients: tuple[MafTransient, ...]
    mixes: tuple[MafMix, ...]
    bases: tuple[MafBasis, ...]
    basis_instances: tuple[MafBasisInstance, ...]
    basis_warp_instances: tuple[MafBasisWarpInstance, ...]


def _validated_gain(value: int) -> int:
    gain = int(value)
    if not -32768 <= gain <= 32768:
        raise ValueError("MFT1 gain exceeds schema-1 bounds")
    return gain


def _divide_round_away(numerator: int, denominator: int) -> int:
    """Match C++ signed division followed by half-away-from-zero rounding."""

    magnitude, remainder = divmod(abs(int(numerator)), int(denominator))
    if 2 * remainder >= denominator:
        magnitude += 1
    return -magnitude if numerator < 0 else magnitude


def _warp_source_position_q16(
    start_position_q16: int,
    start_step_q16: int,
    end_step_q16: int,
    linear_step: bool,
    output_index: int,
    output_count: int,
) -> int:
    position = int(start_position_q16) + int(start_step_q16) * output_index
    if not linear_step or output_index < 2:
        return position
    numerator = (
        (int(end_step_q16) - int(start_step_q16))
        * output_index
        * (output_index - 1)
    )
    denominator = 2 * (output_count - 2)
    return position + _divide_round_away(numerator, denominator)


def _record(record_type: int, body: bytes) -> bytes:
    return RECORD_HEADER.pack(record_type, 1, 0, len(body)) + body


def _filter_body(identifier: int, item: MafFilter) -> bytes:
    reflection = tuple(int(value) for value in item.reflection_q15)
    if (
        not 1 <= len(reflection) <= MAX_FILTER_ORDER
        or any(not -29491 <= value <= 29491 for value in reflection)
    ):
        raise ValueError("MFT1 reflection filter exceeds stability bounds")
    return (
        struct.pack("<HHI", identifier, len(reflection), 0)
        + struct.pack(f"<{len(reflection)}h", *reflection)
    )


def _stochastic_body(identifier: int, item: MafStochastic) -> bytes:
    emitter = NO_EMITTER if item.emitter_id is None else int(item.emitter_id)
    return struct.pack(
        "<HHIIiI",
        identifier,
        emitter,
        int(item.start),
        int(item.end),
        _validated_gain(item.gain_q15),
        0,
    )


def _source_body(identifier: int, item: MafSourceFilter) -> bytes:
    reference = (
        NO_REFERENCE if item.reference_id is None else int(item.reference_id)
    )
    return struct.pack(
        "<HHHBBHHIIiII",
        identifier,
        int(item.emitter_id),
        int(item.filter_id),
        int(item.excitation),
        0,
        reference,
        0,
        int(item.start),
        int(item.end),
        _validated_gain(item.gain_q15),
        int(item.phase_origin_q32),
        int(item.phase_increment_q32),
    )


def _transient_body(identifier: int, item: MafTransient) -> bytes:
    samples = tuple(int(value) for value in item.samples)
    if (
        not 1 <= len(samples) <= MAX_TRANSIENT_SAMPLES
        or any(not -32768 <= value <= 32767 for value in samples)
    ):
        raise ValueError("MFT1 transient exceeds schema-1 bounds")
    return (
        struct.pack(
            "<HHIHHi",
            identifier,
            int(item.emitter_id),
            int(item.onset),
            len(samples),
            0,
            _validated_gain(item.gain_q15),
        )
        + struct.pack(f"<{len(samples)}h", *samples)
    )


def _mix_body(
    identifier: int,
    item: MafMix,
    *,
    output_channels: int,
    emitter_count: int,
) -> bytes:
    matrix = np.asarray(item.matrix_q15)
    if (
        matrix.shape != (output_channels, emitter_count)
        or not np.issubdtype(matrix.dtype, np.integer)
        or np.any(matrix < -32768)
        or np.any(matrix > 32767)
    ):
        raise ValueError("MFT1 mix matrix differs from the stream layout")
    values = np.ascontiguousarray(matrix, dtype="<i2").reshape(-1)
    emitters = tuple(range(emitter_count))
    return (
        struct.pack(
            "<HHIIHH",
            identifier,
            emitter_count,
            int(item.start),
            int(item.end),
            output_channels,
            0,
        )
        + struct.pack(f"<{emitter_count}H", *emitters)
        + values.tobytes()
    )


def _basis_body(identifier: int, item: MafBasis) -> bytes:
    samples = tuple(int(value) for value in item.samples)
    if (
        not 2 <= len(samples) <= 8 * 2048
        or any(not -32768 <= value <= 32767 for value in samples)
    ):
        raise ValueError("MFT1 periodic Basis exceeds Main")
    return (
        struct.pack("<HHI", identifier, len(samples), 0)
        + struct.pack(f"<{len(samples)}h", *samples)
    )


def _basis_instance_body(
    identifier: int,
    item: MafBasisInstance,
) -> bytes:
    if (
        not 0 <= int(item.source_offset) <= 0xFFFF
        or not 1 <= int(item.sample_count) <= 0xFFFF
    ):
        raise ValueError("MFT1 Basis Instance crop exceeds schema-1 bounds")
    flags = int(bool(item.circular))
    if item.reverse:
        flags |= 4
    end_gain = 0
    if item.end_gain_q15 is not None:
        flags |= 2
        end_gain = _validated_gain(item.end_gain_q15)
        if int(item.sample_count) < 2:
            raise ValueError("MFT1 linear gain requires two samples")
    return struct.pack(
        "<HHHHIiHHI",
        identifier,
        int(item.emitter_id),
        int(item.basis_id),
        flags,
        int(item.start),
        _validated_gain(item.gain_q15),
        int(item.source_offset),
        int(item.sample_count),
        end_gain & 0xFFFF_FFFF,
    )


def _basis_warp_instance_body(
    identifier: int,
    item: MafBasisWarpInstance,
) -> bytes:
    sample_count = int(item.sample_count)
    if not 1 <= sample_count <= MAX_WARP_INSTANCE_SAMPLES:
        raise ValueError("MFT1 Basis Warp lifetime exceeds schema-1 bounds")
    flags = int(bool(item.circular))
    end_gain = 0
    if item.end_gain_q15 is not None:
        if sample_count < 2:
            raise ValueError("MFT1 linear gain requires two samples")
        flags |= 2
        end_gain = _validated_gain(item.end_gain_q15)
    end_step = 0
    if item.end_source_step_q16 is not None:
        if sample_count < 3:
            raise ValueError("MFT1 linear step requires three samples")
        flags |= 4
        end_step = int(item.end_source_step_q16)
    return struct.pack(
        "<HHHHIIiiiii",
        identifier,
        int(item.emitter_id),
        int(item.basis_id),
        flags,
        int(item.start),
        sample_count,
        int(item.source_position_q16),
        int(item.source_step_q16),
        end_step,
        _validated_gain(item.gain_q15),
        end_gain,
    )


def pack_maf_typed(
    *,
    sample_rate: int,
    total_frames: int,
    render_quantum: int,
    output_channels: int,
    emitter_count: int,
    filters: tuple[MafFilter, ...] = (),
    stochastic: tuple[MafStochastic, ...] = (),
    sources: tuple[MafSourceFilter, ...] = (),
    transients: tuple[MafTransient, ...] = (),
    mixes: tuple[MafMix, ...],
    bases: tuple[MafBasis, ...] = (),
    basis_instances: tuple[MafBasisInstance, ...] = (),
    basis_warp_instances: tuple[MafBasisWarpInstance, ...] = (),
    stream_seed: int = 0x5245_534F_4E49_5448,
    declared_operations_per_frame: int = 1 << 20,
) -> bytes:
    """Pack one canonical prospective MFT1 stream for native verification."""

    if (
        not 8000 <= sample_rate <= 384000
        or not 1 <= total_frames <= 0xFFFF_FFFF
        or not 1 <= render_quantum <= MAX_RENDER_QUANTUM
        or not 1 <= output_channels <= MAX_CHANNELS
        or not 1 <= emitter_count <= MAX_EMITTERS
        or not 1 <= declared_operations_per_frame <= 1 << 20
    ):
        raise ValueError("MFT1 configuration exceeds the Main profile")
    if len(filters) > 64 or len(stochastic) > 64:
        raise ValueError("MFT1 immutable resource count exceeds Main")
    if len(sources) > 4096 or len(transients) > 4096:
        raise ValueError("MFT1 lifetime/event count exceeds Main")
    if not 1 <= len(mixes) <= 4096:
        raise ValueError("MFT1 requires one or more mix lifetimes")
    if len(bases) > 256:
        raise ValueError("MFT1 Basis count exceeds Main")
    if len(basis_instances) + len(basis_warp_instances) > 4096:
        raise ValueError("MFT1 Basis Instance count exceeds Main")
    for instance in basis_instances:
        basis_length = len(bases[int(instance.basis_id)].samples) if (
            0 <= int(instance.basis_id) < len(bases)
        ) else 0
        crop_is_valid = (
            (
                0 <= int(instance.source_offset) < basis_length
                and int(instance.sample_count) <= basis_length
            )
            if instance.circular
            else (
                0 <= int(instance.source_offset) < basis_length
                and int(instance.sample_count)
                <= int(instance.source_offset) + 1
            )
            if instance.reverse
            else (
                0 <= int(instance.source_offset) <= basis_length
                and int(instance.sample_count)
                <= basis_length - int(instance.source_offset)
            )
        )
        if (
            not 0 <= int(instance.emitter_id) < emitter_count
            or not 0 <= int(instance.basis_id) < len(bases)
            or not 0 <= int(instance.start) < total_frames
            or int(instance.sample_count) > total_frames - int(instance.start)
            or not crop_is_valid
        ):
            raise ValueError("MFT1 Basis Instance exceeds its resolved bounds")
    for instance in basis_warp_instances:
        basis_length = len(bases[int(instance.basis_id)].samples) if (
            0 <= int(instance.basis_id) < len(bases)
        ) else 0
        sample_count = int(instance.sample_count)
        start_step = int(instance.source_step_q16)
        linear_step = instance.end_source_step_q16 is not None
        end_step = (
            int(instance.end_source_step_q16)
            if linear_step
            else start_step
        )
        final_position = _warp_source_position_q16(
            int(instance.source_position_q16),
            start_step,
            end_step,
            linear_step,
            max(0, sample_count - 1),
            sample_count,
        )
        minimum_position = min(
            int(instance.source_position_q16),
            final_position,
        )
        maximum_position = max(
            int(instance.source_position_q16),
            final_position,
        )
        same_direction = (
            start_step >= 0 and end_step >= 0
        ) or (
            start_step <= 0 and end_step <= 0
        )
        positions_are_valid = instance.circular or (
            minimum_position >= 0
            and maximum_position <= (basis_length - 1) * WARP_ONE_Q16
        )
        if (
            not 0 <= int(instance.emitter_id) < emitter_count
            or not 0 <= int(instance.basis_id) < len(bases)
            or not 0 <= int(instance.start) < total_frames
            or not 1 <= sample_count <= MAX_WARP_INSTANCE_SAMPLES
            or sample_count > total_frames - int(instance.start)
            or not -MAX_WARP_STEP_Q16 <= start_step <= MAX_WARP_STEP_Q16
            or not -MAX_WARP_STEP_Q16 <= end_step <= MAX_WARP_STEP_Q16
            or not same_direction
            or (linear_step and sample_count < 3)
            or (
                instance.end_gain_q15 is not None
                and sample_count < 2
            )
            or not positions_are_valid
        ):
            raise ValueError(
                "MFT1 Basis Warp Instance exceeds its resolved bounds"
            )

    records: list[bytes] = []
    records.extend(
        _record(FILTER, _filter_body(index, item))
        for index, item in enumerate(filters)
    )
    records.extend(
        _record(STOCHASTIC, _stochastic_body(index, item))
        for index, item in enumerate(stochastic)
    )
    records.extend(
        _record(SOURCE_FILTER, _source_body(index, item))
        for index, item in enumerate(sources)
    )
    records.extend(
        _record(TRANSIENT, _transient_body(index, item))
        for index, item in enumerate(transients)
    )
    records.extend(
        _record(
            MIX,
            _mix_body(
                index,
                item,
                output_channels=output_channels,
                emitter_count=emitter_count,
            ),
        )
        for index, item in enumerate(mixes)
    )
    records.extend(
        _record(BASIS, _basis_body(index, item))
        for index, item in enumerate(bases)
    )
    records.extend(
        _record(
            BASIS_INSTANCE,
            _basis_instance_body(index, item),
        )
        for index, item in enumerate(basis_instances)
    )
    records.extend(
        _record(
            BASIS_WARP_INSTANCE,
            _basis_warp_instance_body(index, item),
        )
        for index, item in enumerate(basis_warp_instances)
    )
    body = b"".join(records)
    coefficient_elements = len(filters) * MAX_FILTER_ORDER
    history_elements = emitter_count * MAX_FILTER_ORDER
    planar_elements = emitter_count * render_quantum
    mix_elements = output_channels * emitter_count
    basis_elements = sum(len(item.samples) for item in bases)
    persistent_bytes = (
        4 * coefficient_elements
        + 2 * history_elements
        + 2 * basis_elements
    )
    scratch_bytes = 2 * (
        planar_elements + 2 * render_quantum + mix_elements
    )

    header = bytearray(HEADER_BYTES)
    struct.pack_into("<4sBBH", header, 0, MAGIC, VERSION, 0, HEADER_BYTES)
    struct.pack_into(
        "<IIIHHHHHHHH",
        header,
        8,
        sample_rate,
        total_frames,
        render_quantum,
        output_channels,
        emitter_count,
        len(filters),
        len(stochastic),
        len(sources),
        len(transients),
        len(mixes),
        len(records),
    )
    struct.pack_into("<Q", header, 36, stream_seed)
    struct.pack_into(
        "<IIIII",
        header,
        44,
        declared_operations_per_frame,
        len(body),
        persistent_bytes,
        scratch_bytes,
        0,
    )
    stream = bytes(header) + body
    return stream + struct.pack("<I", zlib.crc32(stream) & 0xFFFF_FFFF)


def parse_maf_typed(payload: bytes) -> MafTypedInfo:
    """Independently validate and reconstruct one canonical MFT1 record view."""

    if len(payload) < HEADER_BYTES + 4:
        raise ValueError("truncated MFT1 stream")
    magic, version, flags, header_bytes = struct.unpack_from(
        "<4sBBH",
        payload,
    )
    if magic != MAGIC:
        raise ValueError("not an MFT1 stream")
    if version != VERSION:
        raise ValueError("unsupported MFT1 version")
    if flags != 0 or header_bytes != HEADER_BYTES:
        raise ValueError("non-canonical MFT1 header")
    (
        sample_rate,
        total_frames,
        render_quantum,
        output_channels,
        emitter_count,
        filter_count,
        stochastic_count,
        source_count,
        transient_count,
        mix_count,
        record_count,
    ) = struct.unpack_from("<IIIHHHHHHHH", payload, 8)
    stream_seed = struct.unpack_from("<Q", payload, 36)[0]
    (
        operations,
        body_bytes,
        persistent_bytes,
        scratch_bytes,
        reserved,
    ) = struct.unpack_from("<IIIII", payload, 44)
    if reserved != 0 or len(payload) != HEADER_BYTES + body_bytes + 4:
        raise ValueError("non-canonical MFT1 size")
    if zlib.crc32(payload[:-4]) & 0xFFFF_FFFF != struct.unpack_from(
        "<I",
        payload,
        len(payload) - 4,
    )[0]:
        raise ValueError("MFT1 checksum mismatch")
    fixed_records = (
        filter_count
        + stochastic_count
        + source_count
        + transient_count
        + mix_count
    )
    if record_count < fixed_records:
        raise ValueError("MFT1 record count mismatch")
    expected_persistent_without_basis = 4 * filter_count * MAX_FILTER_ORDER
    expected_persistent_without_basis += 2 * emitter_count * MAX_FILTER_ORDER
    expected_scratch = 2 * (
        emitter_count * render_quantum
        + 2 * render_quantum
        + output_channels * emitter_count
    )
    if scratch_bytes != expected_scratch:
        raise ValueError("MFT1 memory declaration mismatch")

    filters: list[MafFilter] = []
    fields: list[MafStochastic] = []
    sources: list[MafSourceFilter] = []
    transients: list[MafTransient] = []
    mixes: list[MafMix] = []
    bases: list[MafBasis] = []
    basis_instances: list[MafBasisInstance] = []
    basis_warp_instances: list[MafBasisWarpInstance] = []
    expected_ids = [0] * 9
    previous_type = 0
    cursor = HEADER_BYTES
    body_end = cursor + body_bytes
    while cursor < body_end:
        if body_end - cursor < RECORD_HEADER.size:
            raise ValueError("truncated MFT1 record")
        record_type, record_version, record_flags, size = (
            RECORD_HEADER.unpack_from(payload, cursor)
        )
        cursor += RECORD_HEADER.size
        if (
            record_version != 1
            or record_flags != 0
            or record_type < FILTER
            or record_type > BASIS_WARP_INSTANCE
            or record_type < previous_type
            or size > body_end - cursor
        ):
            raise ValueError("non-canonical MFT1 record")
        body = payload[cursor : cursor + size]
        cursor += size
        previous_type = record_type
        if len(body) < 2:
            raise ValueError("truncated MFT1 record identifier")
        identifier = struct.unpack_from("<H", body)[0]
        if identifier != expected_ids[record_type]:
            raise ValueError("non-canonical MFT1 identifier")
        expected_ids[record_type] += 1

        if record_type == FILTER:
            _, order, zero = struct.unpack_from("<HHI", body)
            if zero != 0 or len(body) != 8 + 2 * order:
                raise ValueError("invalid MFT1 filter")
            filters.append(
                MafFilter(struct.unpack_from(f"<{order}h", body, 8))
            )
        elif record_type == STOCHASTIC:
            _, emitter, start, end, gain, zero = struct.unpack(
                "<HHIIiI",
                body,
            )
            if zero != 0:
                raise ValueError("invalid MFT1 stochastic field")
            fields.append(
                MafStochastic(
                    None if emitter == NO_EMITTER else emitter,
                    start,
                    end,
                    gain,
                )
            )
        elif record_type == SOURCE_FILTER:
            (
                _,
                emitter,
                filter_id,
                excitation,
                source_flags,
                reference,
                zero,
                start,
                end,
                gain,
                origin,
                increment,
            ) = struct.unpack("<HHHBBHHIIiII", body)
            if source_flags != 0 or zero != 0:
                raise ValueError("invalid MFT1 source-filter flags")
            sources.append(
                MafSourceFilter(
                    emitter,
                    filter_id,
                    excitation,
                    None if reference == NO_REFERENCE else reference,
                    start,
                    end,
                    gain,
                    origin,
                    increment,
                )
            )
        elif record_type == TRANSIENT:
            _, emitter, onset, count, zero, gain = struct.unpack_from(
                "<HHIHHi",
                body,
            )
            if zero != 0 or len(body) != 16 + 2 * count:
                raise ValueError("invalid MFT1 transient")
            transients.append(
                MafTransient(
                    emitter,
                    onset,
                    gain,
                    struct.unpack_from(f"<{count}h", body, 16),
                )
            )
        elif record_type == MIX:
            (
                _,
                source_total,
                start,
                end,
                channels,
                zero,
            ) = struct.unpack_from("<HHIIHH", body)
            matrix_offset = 16 + 2 * source_total
            matrix_count = channels * source_total
            if (
                zero != 0
                or len(body) != matrix_offset + 2 * matrix_count
                or struct.unpack_from(
                    f"<{source_total}H",
                    body,
                    16,
                ) != tuple(range(source_total))
            ):
                raise ValueError("invalid MFT1 mix")
            flat = struct.unpack_from(
                f"<{matrix_count}h",
                body,
                matrix_offset,
            )
            matrix = tuple(
                tuple(flat[channel * source_total : (channel + 1) * source_total])
                for channel in range(channels)
            )
            mixes.append(MafMix(start, end, matrix))
        elif record_type == BASIS:
            _, count, zero = struct.unpack_from("<HHI", body)
            if (
                zero != 0
                or not 2 <= count <= 8 * 2048
                or len(body) != 8 + 2 * count
            ):
                raise ValueError("invalid MFT1 periodic Basis")
            bases.append(
                MafBasis(struct.unpack_from(f"<{count}h", body, 8))
            )
        elif record_type == BASIS_INSTANCE:
            if len(body) != 24:
                raise ValueError("invalid MFT1 Basis Instance size")
            (
                _,
                emitter,
                basis_id,
                instance_flags,
                start,
                gain,
                source_offset,
                sample_count,
                end_gain_bits,
            ) = struct.unpack("<HHHHIiHHI", body)
            if instance_flags & ~7:
                raise ValueError("invalid MFT1 Basis Instance flags")
            end_gain = struct.unpack("<i", struct.pack("<I", end_gain_bits))[0]
            linear_gain = bool(instance_flags & 2)
            if (
                (not linear_gain and end_gain != 0)
                or (linear_gain and sample_count < 2)
            ):
                raise ValueError("invalid MFT1 Basis Instance gain law")
            basis_instances.append(
                MafBasisInstance(
                    emitter,
                    basis_id,
                    start,
                    gain,
                    source_offset,
                    sample_count,
                    bool(instance_flags & 1),
                    end_gain if linear_gain else None,
                    bool(instance_flags & 4),
                )
            )
        else:
            if len(body) != 36:
                raise ValueError("invalid MFT1 Basis Warp Instance size")
            (
                _,
                emitter,
                basis_id,
                instance_flags,
                start,
                sample_count,
                source_position_q16,
                start_step_q16,
                end_step_q16,
                start_gain,
                end_gain,
            ) = struct.unpack("<HHHHIIiiiii", body)
            if instance_flags & ~7:
                raise ValueError("invalid MFT1 Basis Warp Instance flags")
            linear_gain = bool(instance_flags & 2)
            linear_step = bool(instance_flags & 4)
            if (
                (not linear_gain and end_gain != 0)
                or (linear_gain and sample_count < 2)
                or (not linear_step and end_step_q16 != 0)
                or (linear_step and sample_count < 3)
            ):
                raise ValueError("invalid MFT1 Basis Warp law")
            basis_warp_instances.append(
                MafBasisWarpInstance(
                    emitter,
                    basis_id,
                    start,
                    sample_count,
                    source_position_q16,
                    start_step_q16,
                    start_gain,
                    bool(instance_flags & 1),
                    end_step_q16 if linear_step else None,
                    end_gain if linear_gain else None,
                )
            )
    if cursor != body_end:
        raise ValueError("trailing MFT1 record bytes")
    if record_count != (
        fixed_records
        + len(bases)
        + len(basis_instances)
        + len(basis_warp_instances)
    ):
        raise ValueError("MFT1 record count mismatch")
    if (
        len(bases) > 256
        or len(basis_instances) + len(basis_warp_instances) > 4096
    ):
        raise ValueError("MFT1 immutable resource count exceeds Main")
    for instance in basis_instances:
        basis_length = len(bases[instance.basis_id].samples) if (
            0 <= instance.basis_id < len(bases)
        ) else 0
        crop_is_valid = (
            (
                instance.source_offset < basis_length
                and instance.sample_count <= basis_length
            )
            if instance.circular
            else (
                instance.source_offset < basis_length
                and instance.sample_count <= instance.source_offset + 1
            )
            if instance.reverse
            else (
                instance.source_offset <= basis_length
                and instance.sample_count
                <= basis_length - instance.source_offset
            )
        )
        if (
            not -32768 <= instance.gain_q15 <= 32768
            or (
                instance.end_gain_q15 is not None
                and not -32768 <= instance.end_gain_q15 <= 32768
            )
            or not 0 <= instance.emitter_id < emitter_count
            or not 0 <= instance.basis_id < len(bases)
            or not 0 <= instance.start < total_frames
            or instance.sample_count <= 0
            or instance.sample_count > total_frames - instance.start
            or not crop_is_valid
        ):
            raise ValueError("MFT1 Basis Instance exceeds its resolved bounds")
    for instance in basis_warp_instances:
        basis_length = len(bases[instance.basis_id].samples) if (
            0 <= instance.basis_id < len(bases)
        ) else 0
        start_step = int(instance.source_step_q16)
        linear_step = instance.end_source_step_q16 is not None
        end_step = (
            int(instance.end_source_step_q16)
            if linear_step
            else start_step
        )
        final_position = _warp_source_position_q16(
            instance.source_position_q16,
            start_step,
            end_step,
            linear_step,
            max(0, instance.sample_count - 1),
            instance.sample_count,
        )
        same_direction = (
            start_step >= 0 and end_step >= 0
        ) or (
            start_step <= 0 and end_step <= 0
        )
        if (
            not -32768 <= instance.gain_q15 <= 32768
            or (
                instance.end_gain_q15 is not None
                and not -32768 <= instance.end_gain_q15 <= 32768
            )
            or not 0 <= instance.emitter_id < emitter_count
            or not 0 <= instance.basis_id < len(bases)
            or not 0 <= instance.start < total_frames
            or not 1 <= instance.sample_count <= MAX_WARP_INSTANCE_SAMPLES
            or instance.sample_count > total_frames - instance.start
            or not -MAX_WARP_STEP_Q16 <= start_step <= MAX_WARP_STEP_Q16
            or not -MAX_WARP_STEP_Q16 <= end_step <= MAX_WARP_STEP_Q16
            or not same_direction
            or (
                not instance.circular
                and (
                    min(instance.source_position_q16, final_position) < 0
                    or max(instance.source_position_q16, final_position)
                    > (basis_length - 1) * WARP_ONE_Q16
                )
            )
        ):
            raise ValueError(
                "MFT1 Basis Warp Instance exceeds its resolved bounds"
            )
    if persistent_bytes != expected_persistent_without_basis + 2 * sum(
        len(item.samples) for item in bases
    ):
        raise ValueError("MFT1 memory declaration mismatch")
    return MafTypedInfo(
        sample_rate,
        total_frames,
        render_quantum,
        output_channels,
        emitter_count,
        stream_seed,
        operations,
        tuple(filters),
        tuple(fields),
        tuple(sources),
        tuple(transients),
        tuple(mixes),
        tuple(bases),
        tuple(basis_instances),
        tuple(basis_warp_instances),
    )
