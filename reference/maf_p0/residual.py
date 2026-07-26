"""Bounded reversible lifting and entropy transport for objective Innovation."""

from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib

import numpy as np

from .transient import haar_lift_forward, haar_lift_inverse


MAGIC = b"RSL1"
VERSION = 1
DEFAULT_BLOCK_SIZE = 1024
MAX_BLOCK_SIZE = 32768
MAX_SAMPLE_COUNT = (1 << 31) - 1
MAX_ABSOLUTE_INPUT = (1 << 31) - 1
MAX_ABSOLUTE_COEFFICIENT = (1 << 34) - 1
MAX_RICE_PARAMETER = 20
RICE_ESCAPE_QUOTIENT = 31
MAX_BITS_PER_COEFFICIENT = RICE_ESCAPE_QUOTIENT + 1 + 64

TRANSFORM_IDENTITY = 0
TRANSFORM_DELTA1 = 1
TRANSFORM_DELTA2 = 2
TRANSFORM_HAAR = 3
TRANSFORM_NAMES = {
    TRANSFORM_IDENTITY: "identity",
    TRANSFORM_DELTA1: "delta1",
    TRANSFORM_DELTA2: "delta2",
    TRANSFORM_HAAR: "haar",
}

ENTROPY_RICE = 0
ENTROPY_PACKED = 1

_STREAM_HEADER = struct.Struct("<4sBHII")
_BLOCK_HEADER = struct.Struct("<HBBBI")
_CHECKSUM = struct.Struct("<I")


@dataclass(frozen=True)
class ResidualPacket:
    """Canonical LiftPack-1 bytes plus encoder-only RDO diagnostics."""

    payload: bytes
    report: dict


class _BitWriter:
    """Little-endian bit accumulator with a canonical zero-padded final byte."""

    def __init__(self) -> None:
        self._bytes = bytearray()
        self._current = 0
        self._used = 0
        self.bit_count = 0

    def write_bit(self, value: int) -> None:
        if value not in {0, 1}:
            raise ValueError("bit value must be zero or one")
        self._current |= value << self._used
        self._used += 1
        self.bit_count += 1
        if self._used == 8:
            self._bytes.append(self._current)
            self._current = 0
            self._used = 0

    def write_bits(self, value: int, count: int) -> None:
        if count < 0 or value < 0 or value >= (1 << count):
            raise ValueError("bit field is outside its declared width")
        for offset in range(count):
            self.write_bit((value >> offset) & 1)

    def finish(self) -> bytes:
        if self._used:
            self._bytes.append(self._current)
        return bytes(self._bytes)


class _BitReader:
    """Bounded counterpart of :class:`_BitWriter`."""

    def __init__(self, payload: bytes, bit_count: int) -> None:
        if bit_count < 0 or bit_count > len(payload) * 8:
            raise ValueError("invalid entropy payload bit count")
        if bit_count % 8 and payload:
            valid_mask = (1 << (bit_count % 8)) - 1
            if payload[-1] & ~valid_mask:
                raise ValueError("non-zero entropy padding bits")
        self._payload = payload
        self.bit_count = bit_count
        self.position = 0

    def read_bit(self) -> int:
        if self.position >= self.bit_count:
            raise ValueError("truncated entropy payload")
        value = (self._payload[self.position // 8] >> (self.position % 8)) & 1
        self.position += 1
        return value

    def read_bits(self, count: int) -> int:
        if count < 0 or self.position + count > self.bit_count:
            raise ValueError("truncated entropy bit field")
        value = 0
        for offset in range(count):
            value |= self.read_bit() << offset
        return value


def _zigzag_encode(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def _zigzag_decode(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value // 2) - 1


def _next_power_of_two(value: int) -> int:
    return 1 << (value - 1).bit_length()


def _validate_input(values: np.ndarray, block_size: int) -> np.ndarray:
    source = np.asarray(values)
    if source.ndim != 1 or not np.issubdtype(source.dtype, np.signedinteger):
        raise TypeError("residual input must be a one-dimensional signed integer array")
    if source.size > MAX_SAMPLE_COUNT:
        raise ValueError("residual sample count exceeds the LiftPack-1 bound")
    if block_size < 16 or block_size > MAX_BLOCK_SIZE:
        raise ValueError("residual block size is outside the LiftPack-1 bound")
    source64 = source.astype(np.int64, copy=True)
    if source64.size:
        minimum = int(np.min(source64))
        maximum = int(np.max(source64))
        if minimum < -MAX_ABSOLUTE_INPUT or maximum > MAX_ABSOLUTE_INPUT:
            raise ValueError("residual sample magnitude exceeds the LiftPack-1 bound")
    return source64


def _forward_transform(values: np.ndarray, mode: int) -> np.ndarray:
    if mode == TRANSFORM_IDENTITY:
        output = values.copy()
    elif mode == TRANSFORM_DELTA1:
        output = values.copy()
        output[1:] = values[1:] - values[:-1]
    elif mode == TRANSFORM_DELTA2:
        output = values.copy()
        if values.size > 1:
            output[1] = values[1] - values[0]
            output[2:] = values[2:] - 2 * values[1:-1] + values[:-2]
    elif mode == TRANSFORM_HAAR:
        padded = np.zeros(_next_power_of_two(values.size), dtype=np.int64)
        padded[: values.size] = values
        output = haar_lift_forward(padded)
    else:
        raise ValueError("unknown LiftPack-1 transform")
    if output.size and int(np.max(np.abs(output))) > MAX_ABSOLUTE_COEFFICIENT:
        raise ValueError("lifting coefficient exceeds the LiftPack-1 bound")
    return output


def _inverse_transform(coefficients: np.ndarray, mode: int, length: int) -> np.ndarray:
    if mode == TRANSFORM_IDENTITY:
        output = coefficients.copy()
    elif mode == TRANSFORM_DELTA1:
        if coefficients.size != length:
            raise ValueError("delta1 coefficient count mismatch")
        output = np.empty(length, dtype=np.int64)
        accumulator = 0
        for index, value in enumerate(coefficients):
            accumulator += int(value)
            if abs(accumulator) > MAX_ABSOLUTE_INPUT:
                raise ValueError("delta1 inverse exceeds the sample bound")
            output[index] = accumulator
    elif mode == TRANSFORM_DELTA2:
        if coefficients.size != length:
            raise ValueError("delta2 coefficient count mismatch")
        output = np.empty(length, dtype=np.int64)
        if length:
            output[0] = coefficients[0]
        if length > 1:
            output[1] = int(coefficients[1]) + int(output[0])
        for index in range(2, length):
            value = (
                int(coefficients[index])
                + 2 * int(output[index - 1])
                - int(output[index - 2])
            )
            if abs(value) > MAX_ABSOLUTE_INPUT:
                raise ValueError("delta2 inverse exceeds the sample bound")
            output[index] = value
    elif mode == TRANSFORM_HAAR:
        expected = _next_power_of_two(length)
        if coefficients.size != expected:
            raise ValueError("Haar coefficient count mismatch")
        output = haar_lift_inverse(coefficients)[:length]
    else:
        raise ValueError("unknown LiftPack-1 transform")
    if output.size and int(np.max(np.abs(output))) > MAX_ABSOLUTE_INPUT:
        raise ValueError("inverse lifting output exceeds the sample bound")
    return output


def _rice_bit_count(unsigned: np.ndarray, parameter: int) -> int:
    quotient = np.right_shift(unsigned, np.uint64(parameter))
    costs = np.where(
        quotient < RICE_ESCAPE_QUOTIENT,
        quotient + np.uint64(1 + parameter),
        np.uint64(RICE_ESCAPE_QUOTIENT + 1 + 64),
    )
    return int(np.sum(costs, dtype=np.uint64))


def _encode_rice(unsigned: np.ndarray, parameter: int) -> tuple[bytes, int]:
    writer = _BitWriter()
    for item in unsigned:
        value = int(item)
        quotient = value >> parameter
        if quotient < RICE_ESCAPE_QUOTIENT:
            for _ in range(quotient):
                writer.write_bit(1)
            writer.write_bit(0)
            writer.write_bits(value & ((1 << parameter) - 1), parameter)
        else:
            for _ in range(RICE_ESCAPE_QUOTIENT):
                writer.write_bit(1)
            writer.write_bit(0)
            writer.write_bits(value, 64)
    return writer.finish(), writer.bit_count


def _decode_rice(reader: _BitReader, count: int, parameter: int) -> np.ndarray:
    output = np.empty(count, dtype=np.int64)
    for index in range(count):
        quotient = 0
        while reader.read_bit():
            quotient += 1
            if quotient > RICE_ESCAPE_QUOTIENT:
                raise ValueError("Rice unary prefix exceeds the LiftPack-1 bound")
        if quotient == RICE_ESCAPE_QUOTIENT:
            unsigned = reader.read_bits(64)
        else:
            remainder = reader.read_bits(parameter)
            unsigned = (quotient << parameter) | remainder
        value = _zigzag_decode(unsigned)
        if abs(value) > MAX_ABSOLUTE_COEFFICIENT:
            raise ValueError("decoded coefficient exceeds the LiftPack-1 bound")
        output[index] = value
    return output


def _choose_entropy(values: np.ndarray) -> tuple[int, int, int]:
    """Return the exact winning entropy mode without materializing its bits."""

    unsigned = np.where(
        values >= 0,
        values * 2,
        -values * 2 - 1,
    ).astype(np.uint64)
    maximum = int(np.max(unsigned)) if unsigned.size else 0
    packed_width = max(1, maximum.bit_length())
    packed_bits = packed_width * unsigned.size

    best_parameter = min(
        range(MAX_RICE_PARAMETER + 1),
        key=lambda parameter: (_rice_bit_count(unsigned, parameter), parameter),
    )
    rice_bits = _rice_bit_count(unsigned, best_parameter)
    if rice_bits <= packed_bits:
        return ENTROPY_RICE, best_parameter, rice_bits
    return ENTROPY_PACKED, packed_width, int(packed_bits)


def _encode_entropy(values: np.ndarray) -> tuple[int, int, bytes, int]:
    mode, parameter, expected_bit_count = _choose_entropy(values)
    unsigned = np.where(
        values >= 0,
        values * 2,
        -values * 2 - 1,
    ).astype(np.uint64)
    if mode == ENTROPY_RICE:
        payload, bit_count = _encode_rice(unsigned, parameter)
        if bit_count != expected_bit_count:
            raise RuntimeError("Rice measurement and serialization disagree")
        return mode, parameter, payload, bit_count
    writer = _BitWriter()
    for item in unsigned:
        writer.write_bits(int(item), parameter)
    if writer.bit_count != expected_bit_count:
        raise RuntimeError("packed measurement and serialization disagree")
    return mode, parameter, writer.finish(), writer.bit_count


def _decode_entropy(
    payload: bytes,
    bit_count: int,
    count: int,
    mode: int,
    parameter: int,
) -> np.ndarray:
    reader = _BitReader(payload, bit_count)
    if mode == ENTROPY_RICE:
        if not 0 <= parameter <= MAX_RICE_PARAMETER:
            raise ValueError("Rice parameter exceeds the LiftPack-1 bound")
        output = _decode_rice(reader, count, parameter)
    elif mode == ENTROPY_PACKED:
        if not 1 <= parameter <= 64:
            raise ValueError("packed coefficient width is invalid")
        output = np.asarray(
            [
                _zigzag_decode(reader.read_bits(parameter))
                for _ in range(count)
            ],
            dtype=np.int64,
        )
        if output.size and int(np.max(np.abs(output))) > MAX_ABSOLUTE_COEFFICIENT:
            raise ValueError("decoded coefficient exceeds the LiftPack-1 bound")
    else:
        raise ValueError("unknown LiftPack-1 entropy mode")
    if reader.position != bit_count:
        raise ValueError("trailing bits in LiftPack-1 block")
    return output


def encode_liftpack(
    values: np.ndarray,
    *,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> ResidualPacket:
    """Encode signed residual samples with exact per-block transform RDO."""

    source = _validate_input(values, block_size)
    blocks: list[bytes] = []
    transform_counts = {name: 0 for name in TRANSFORM_NAMES.values()}
    entropy_counts = {"rice": 0, "packed": 0}
    entropy_bits = 0

    for start in range(0, source.size, block_size):
        block = source[start : start + block_size]
        candidates: list[tuple[int, int, int, bytes, int, int]] = []
        for transform in TRANSFORM_NAMES:
            coefficients = _forward_transform(block, transform)
            entropy_mode, parameter, payload, bit_count = _encode_entropy(coefficients)
            candidates.append(
                (
                    len(payload),
                    bit_count,
                    transform,
                    payload,
                    entropy_mode,
                    parameter,
                )
            )
        _, bit_count, transform, payload, entropy_mode, parameter = min(candidates)
        blocks.append(
            _BLOCK_HEADER.pack(
                int(block.size),
                transform,
                entropy_mode,
                parameter,
                bit_count,
            )
            + payload
        )
        transform_counts[TRANSFORM_NAMES[transform]] += 1
        entropy_counts["rice" if entropy_mode == ENTROPY_RICE else "packed"] += 1
        entropy_bits += bit_count

    body = (
        _STREAM_HEADER.pack(
            MAGIC,
            VERSION,
            block_size,
            int(source.size),
            len(blocks),
        )
        + b"".join(blocks)
    )
    payload = body + _CHECKSUM.pack(zlib.crc32(body))
    return ResidualPacket(
        payload,
        {
            "codec": "LiftPack-1",
            "sample_count": int(source.size),
            "block_size": int(block_size),
            "block_count": len(blocks),
            "stream_bytes": len(payload),
            "entropy_bits": entropy_bits,
            "transform_counts": transform_counts,
            "entropy_counts": entropy_counts,
        },
    )


def decode_liftpack(
    payload: bytes,
    *,
    expected_count: int | None = None,
) -> np.ndarray:
    """Decode LiftPack-1 after validating all bounds and the stream checksum."""

    minimum = _STREAM_HEADER.size + _CHECKSUM.size
    if len(payload) < minimum:
        raise ValueError("truncated LiftPack-1 stream")
    body = payload[:-_CHECKSUM.size]
    expected_crc = _CHECKSUM.unpack(payload[-_CHECKSUM.size :])[0]
    if zlib.crc32(body) != expected_crc:
        raise ValueError("LiftPack-1 checksum mismatch")

    magic, version, block_size, sample_count, block_count = _STREAM_HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported LiftPack-1 stream")
    if not 16 <= block_size <= MAX_BLOCK_SIZE:
        raise ValueError("LiftPack-1 block size is outside the profile bound")
    if sample_count > MAX_SAMPLE_COUNT:
        raise ValueError("LiftPack-1 sample count exceeds the profile bound")
    canonical_block_count = (
        (sample_count + block_size - 1) // block_size
        if sample_count
        else 0
    )
    if block_count != canonical_block_count:
        raise ValueError("non-canonical LiftPack-1 block count")
    if expected_count is not None and sample_count != expected_count:
        raise ValueError("LiftPack-1 sample count mismatch")

    output = np.empty(sample_count, dtype=np.int64)
    cursor = _STREAM_HEADER.size
    output_offset = 0
    for block_index in range(block_count):
        if cursor + _BLOCK_HEADER.size > len(body):
            raise ValueError("truncated LiftPack-1 block header")
        length, transform, entropy_mode, parameter, bit_count = (
            _BLOCK_HEADER.unpack_from(body, cursor)
        )
        cursor += _BLOCK_HEADER.size
        expected_length = min(block_size, sample_count - output_offset)
        if length != expected_length:
            raise ValueError("non-canonical LiftPack-1 block length")
        coefficient_count = (
            _next_power_of_two(length)
            if transform == TRANSFORM_HAAR
            else length
        )
        if bit_count > coefficient_count * MAX_BITS_PER_COEFFICIENT:
            raise ValueError("LiftPack-1 entropy payload exceeds the block bound")
        payload_bytes = (bit_count + 7) // 8
        end = cursor + payload_bytes
        if end > len(body):
            raise ValueError("truncated LiftPack-1 entropy payload")
        coefficients = _decode_entropy(
            body[cursor:end],
            bit_count,
            coefficient_count,
            entropy_mode,
            parameter,
        )
        restored = _inverse_transform(coefficients, transform, length)
        output[output_offset : output_offset + length] = restored
        output_offset += length
        cursor = end
    if output_offset != sample_count or cursor != len(body):
        raise ValueError("trailing or incomplete LiftPack-1 data")
    return output
