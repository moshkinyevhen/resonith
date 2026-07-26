"""R-042 full-byte oracle for bounded integer LPC residual blocks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .codec import _quality_report, _quantize_signed
from .main0 import pack_main0_residual_stream
from .residual import (
    ENTROPY_PACKED,
    ENTROPY_RICE,
    MAX_ABSOLUTE_COEFFICIENT,
    MAX_ABSOLUTE_INPUT,
    TRANSFORM_HAAR,
    TRANSFORM_NAMES,
    _choose_entropy,
    _decode_entropy,
    _encode_entropy,
    _forward_transform,
    _inverse_transform,
    _next_power_of_two,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf


MAGIC = b"RSL2"
VERSION = 1
TRANSFORM_LPC = 4
LPC_PRECISION = 12
MAX_LPC_ORDER = 16
MAX_COEFFICIENT_SUM_Q = 8 << LPC_PRECISION
STREAM_HEADER = struct.Struct("<4sBHII")
BLOCK_HEADER = struct.Struct("<HBBBI")
LPC_HEADER = struct.Struct("<BB")
CHECKSUM = struct.Struct("<I")


@dataclass(frozen=True)
class LPCOracleResult:
    """Best complete prospective RSC1 stream and exact decoder evidence."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


@dataclass(frozen=True)
class LPCBlockInfo:
    """Canonical byte/sample interval for one independently seeded block."""

    block_index: int
    byte_offset: int
    byte_size: int
    sample_offset: int
    sample_count: int
    transform: int
    entropy: int
    lpc_order: int
    bit_count: int


@dataclass(frozen=True)
class _LPCBlockView:
    info: LPCBlockInfo
    parameter: int
    coefficient_count: int
    coefficients_q: np.ndarray | None
    entropy_payload: bytes


@dataclass(frozen=True)
class _LPCStreamView:
    block_size: int
    sample_count: int
    blocks: tuple[_LPCBlockView, ...]


def _round_shift(value: int, precision: int) -> int:
    magnitude = (abs(value) + (1 << (precision - 1))) >> precision
    return -magnitude if value < 0 else magnitude


def _fit_lpc_coefficients(
    block: np.ndarray,
    order: int,
) -> np.ndarray | None:
    if block.size <= order or not 1 <= order <= MAX_LPC_ORDER:
        return None
    signal = block.astype(np.float64)
    signal -= signal.mean()
    autocorrelation = np.asarray(
        [
            float(signal[lag:] @ signal[: signal.size - lag])
            for lag in range(order + 1)
        ],
        dtype=np.float64,
    )
    if autocorrelation[0] < 1.0:
        return None
    matrix = np.empty((order, order), dtype=np.float64)
    for row in range(order):
        for column in range(order):
            matrix[row, column] = autocorrelation[abs(row - column)]
    regularization = max(1e-6, autocorrelation[0] * 1e-9)
    matrix.flat[:: order + 1] += regularization
    try:
        coefficients = np.linalg.solve(matrix, autocorrelation[1:])
    except np.linalg.LinAlgError:
        return None
    quantized = np.clip(
        np.rint(coefficients * (1 << LPC_PRECISION)),
        -32768,
        32767,
    ).astype(np.int16)
    if int(np.sum(np.abs(quantized.astype(np.int64)))) > MAX_COEFFICIENT_SUM_Q:
        return None
    return quantized


def _forward_lpc(block: np.ndarray, coefficients_q: np.ndarray) -> np.ndarray:
    order = int(coefficients_q.size)
    source = block.astype(np.int64, copy=False)
    output = source.copy()
    coefficients = coefficients_q.astype(np.int64)
    windows = np.lib.stride_tricks.sliding_window_view(source, order)[:-1]
    accumulators = windows[:, ::-1] @ coefficients
    magnitudes = (
        np.abs(accumulators) + (1 << (LPC_PRECISION - 1))
    ) >> LPC_PRECISION
    predictions = np.where(accumulators < 0, -magnitudes, magnitudes)
    output[order:] = source[order:] - predictions
    if output.size and int(np.max(np.abs(output))) > MAX_ABSOLUTE_COEFFICIENT:
        raise ValueError("LPC coefficient exceeds the residual bound")
    return output


def _candidate_record(
    coefficients: np.ndarray,
    *,
    transform: int,
    transform_name: str,
    order: int,
    coefficients_q: np.ndarray | None,
) -> tuple[int, int, str, int, np.ndarray, np.ndarray | None, dict]:
    entropy, parameter, bit_count = _choose_entropy(coefficients)
    metadata_bytes = LPC_HEADER.size + 2 * order if coefficients_q is not None else 0
    encoded_bytes = BLOCK_HEADER.size + metadata_bytes + (bit_count + 7) // 8
    report = {
        "transform": transform_name,
        "order": order,
        "entropy": "rice" if entropy == ENTROPY_RICE else "packed",
    }
    return (
        encoded_bytes,
        bit_count,
        transform_name,
        order,
        coefficients,
        coefficients_q,
        {
            **report,
            "transform_id": transform,
            "entropy_id": entropy,
            "entropy_parameter": parameter,
        },
    )


def _measure_block(
    block: np.ndarray,
    lpc_orders: tuple[int, ...],
) -> tuple[int, dict]:
    candidate = _select_block_candidate(block, lpc_orders)
    return candidate[0], {
        key: candidate[6][key]
        for key in ("transform", "order", "entropy")
    }


def _select_block_candidate(
    block: np.ndarray,
    lpc_orders: tuple[int, ...],
) -> tuple[int, int, str, int, np.ndarray, np.ndarray | None, dict]:
    candidates = [
        _candidate_record(
            _forward_transform(block, transform),
            transform=transform,
            transform_name=transform_name,
            order=0,
            coefficients_q=None,
        )
        for transform, transform_name in TRANSFORM_NAMES.items()
    ]
    for order in lpc_orders:
        coefficients_q = _fit_lpc_coefficients(block, order)
        if coefficients_q is None:
            continue
        candidates.append(
            _candidate_record(
                _forward_lpc(block, coefficients_q),
                transform=TRANSFORM_LPC,
                transform_name="lpc",
                order=order,
                coefficients_q=coefficients_q,
            )
        )
    return min(
        candidates,
        key=lambda item: (item[0], item[1], item[2], item[3]),
    )


def _inverse_lpc(
    residual: np.ndarray,
    coefficients_q: np.ndarray,
) -> np.ndarray:
    order = int(coefficients_q.size)
    output = residual.astype(np.int64, copy=True)
    coefficients = coefficients_q.astype(np.int64)
    for index in range(order, output.size):
        past = output[index - order : index][::-1]
        prediction = _round_shift(
            int(coefficients @ past),
            LPC_PRECISION,
        )
        value = int(residual[index]) + prediction
        if not -MAX_ABSOLUTE_INPUT <= value <= MAX_ABSOLUTE_INPUT:
            raise ValueError("LPC inverse exceeds the sample bound")
        output[index] = value
    if output.size and int(np.max(np.abs(output))) > MAX_ABSOLUTE_INPUT:
        raise ValueError("LPC seed exceeds the sample bound")
    return output


def _encode_block(
    block: np.ndarray,
    lpc_orders: tuple[int, ...],
) -> tuple[bytes, dict]:
    (
        measured_bytes,
        measured_bits,
        _,
        order,
        coefficients,
        coefficients_q,
        details,
    ) = _select_block_candidate(block, lpc_orders)
    entropy, parameter, payload, bit_count = _encode_entropy(coefficients)
    if (
        entropy != details["entropy_id"]
        or parameter != details["entropy_parameter"]
        or bit_count != measured_bits
    ):
        raise RuntimeError("LPC block measurement and serialization disagree")
    metadata = (
        LPC_HEADER.pack(order, LPC_PRECISION)
        + coefficients_q.astype("<i2", copy=False).tobytes()
        if coefficients_q is not None
        else b""
    )
    encoded = (
        BLOCK_HEADER.pack(
            int(block.size),
            details["transform_id"],
            entropy,
            parameter,
            bit_count,
        )
        + metadata
        + payload
    )
    if len(encoded) != measured_bytes:
        raise RuntimeError("LPC block byte measurement is not exact")
    return encoded, {
        key: details[key] for key in ("transform", "order", "entropy")
    }


def encode_lpc_liftpack_oracle(
    values: np.ndarray,
    *,
    block_size: int,
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> tuple[bytes, dict]:
    """Encode an exact prospective RSL2 payload with per-block RDO."""

    source = np.asarray(values)
    if source.ndim != 1 or not np.issubdtype(source.dtype, np.signedinteger):
        raise TypeError("RSL2 input must be a signed integer vector")
    if not 16 <= block_size <= 32768:
        raise ValueError("RSL2 block size exceeds the bound")
    source64 = source.astype(np.int64)
    if source64.size and int(np.max(np.abs(source64))) > MAX_ABSOLUTE_INPUT:
        raise ValueError("RSL2 input exceeds the sample bound")
    orders = tuple(sorted(set(int(order) for order in lpc_orders)))
    if not orders or orders[0] < 1 or orders[-1] > MAX_LPC_ORDER:
        raise ValueError("RSL2 LPC order exceeds the bound")

    blocks: list[bytes] = []
    transform_counts = {
        **{name: 0 for name in TRANSFORM_NAMES.values()},
        "lpc": 0,
    }
    lpc_order_counts = {str(order): 0 for order in orders}
    for start in range(0, source64.size, block_size):
        encoded, block_report = _encode_block(
            source64[start : start + block_size],
            orders,
        )
        blocks.append(encoded)
        transform_counts[block_report["transform"]] += 1
        if block_report["transform"] == "lpc":
            lpc_order_counts[str(block_report["order"])] += 1

    body = (
        STREAM_HEADER.pack(
            MAGIC,
            VERSION,
            block_size,
            int(source64.size),
            len(blocks),
        )
        + b"".join(blocks)
    )
    payload = body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)
    return payload, {
        "stream_bytes": len(payload),
        "block_size": block_size,
        "block_count": len(blocks),
        "transform_counts": transform_counts,
        "lpc_order_counts": lpc_order_counts,
    }


def _parse_lpc_liftpack(payload: bytes) -> _LPCStreamView:
    """Validate one RSL2 envelope and index every block without decoding."""

    if len(payload) < STREAM_HEADER.size + CHECKSUM.size:
        raise ValueError("truncated RSL2 stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("RSL2 checksum mismatch")
    magic, version, block_size, sample_count, block_count = (
        STREAM_HEADER.unpack_from(body)
    )
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported RSL2 stream")
    if (
        not 16 <= block_size <= 32768
        or sample_count > (1 << 31) - 1
    ):
        raise ValueError("RSL2 stream exceeds the profile bound")
    expected_blocks = (
        (sample_count + block_size - 1) // block_size
        if sample_count
        else 0
    )
    if block_count != expected_blocks:
        raise ValueError("non-canonical RSL2 block count")
    cursor = STREAM_HEADER.size
    sample_offset = 0
    blocks: list[_LPCBlockView] = []
    for block_index in range(block_count):
        block_start = cursor
        if cursor + BLOCK_HEADER.size > len(body):
            raise ValueError("truncated RSL2 block header")
        length, transform, entropy, parameter, bit_count = (
            BLOCK_HEADER.unpack_from(body, cursor)
        )
        cursor += BLOCK_HEADER.size
        expected_length = min(block_size, sample_count - sample_offset)
        if length != expected_length:
            raise ValueError("non-canonical RSL2 block length")

        coefficients_q = None
        coefficient_count = length
        if transform == TRANSFORM_LPC:
            if cursor + LPC_HEADER.size > len(body):
                raise ValueError("truncated RSL2 LPC header")
            order, precision = LPC_HEADER.unpack_from(body, cursor)
            cursor += LPC_HEADER.size
            if not 1 <= order <= MAX_LPC_ORDER or precision != LPC_PRECISION:
                raise ValueError("RSL2 LPC parameter exceeds the bound")
            coefficient_bytes = 2 * order
            end = cursor + coefficient_bytes
            if end > len(body):
                raise ValueError("truncated RSL2 LPC coefficients")
            coefficients_q = np.frombuffer(
                body[cursor:end],
                dtype="<i2",
            ).copy()
            coefficients_q.flags.writeable = False
            if (
                int(np.sum(np.abs(coefficients_q.astype(np.int64))))
                > MAX_COEFFICIENT_SUM_Q
            ):
                raise ValueError("RSL2 coefficient sum exceeds the bound")
            cursor = end
        elif transform == TRANSFORM_HAAR:
            coefficient_count = _next_power_of_two(length)
        elif transform not in TRANSFORM_NAMES:
            raise ValueError("unknown RSL2 transform")

        if bit_count > coefficient_count * 96:
            raise ValueError("RSL2 entropy payload exceeds the block bound")
        payload_bytes = (bit_count + 7) // 8
        end = cursor + payload_bytes
        if end > len(body):
            raise ValueError("truncated RSL2 entropy payload")
        blocks.append(
            _LPCBlockView(
                info=LPCBlockInfo(
                    block_index=block_index,
                    byte_offset=block_start,
                    byte_size=end - block_start,
                    sample_offset=sample_offset,
                    sample_count=length,
                    transform=transform,
                    entropy=entropy,
                    lpc_order=(
                        0
                        if coefficients_q is None
                        else int(coefficients_q.size)
                    ),
                    bit_count=bit_count,
                ),
                parameter=parameter,
                coefficient_count=coefficient_count,
                coefficients_q=coefficients_q,
                entropy_payload=body[cursor:end],
            )
        )
        sample_offset += length
        cursor = end
    if sample_offset != sample_count or cursor != len(body):
        raise ValueError("trailing or incomplete RSL2 data")
    return _LPCStreamView(
        block_size=block_size,
        sample_count=sample_count,
        blocks=tuple(blocks),
    )


def _decode_lpc_block(block: _LPCBlockView) -> np.ndarray:
    coefficients = _decode_entropy(
        block.entropy_payload,
        block.info.bit_count,
        block.coefficient_count,
        block.info.entropy,
        block.parameter,
    )
    restored = (
        _inverse_lpc(coefficients, block.coefficients_q)
        if block.coefficients_q is not None
        else _inverse_transform(
            coefficients,
            block.info.transform,
            block.info.sample_count,
        )
    )
    return restored[: block.info.sample_count]


def index_lpc_liftpack_blocks(payload: bytes) -> tuple[LPCBlockInfo, ...]:
    """Return immutable canonical RSL2 block intervals after full validation."""

    return tuple(block.info for block in _parse_lpc_liftpack(payload).blocks)


def decode_lpc_liftpack_block(
    payload: bytes,
    block_index: int,
) -> tuple[LPCBlockInfo, np.ndarray]:
    """Independently reconstruct one block without decoding earlier samples."""

    stream = _parse_lpc_liftpack(payload)
    if not 0 <= block_index < len(stream.blocks):
        raise IndexError("RSL2 block index is out of range")
    block = stream.blocks[block_index]
    output = _decode_lpc_block(block)
    output.flags.writeable = False
    return block.info, output


def decode_lpc_liftpack_oracle(
    payload: bytes,
    *,
    expected_count: int | None = None,
) -> np.ndarray:
    """Independently parse and exactly invert one prospective RSL2 payload."""

    stream = _parse_lpc_liftpack(payload)
    if expected_count is not None and stream.sample_count != expected_count:
        raise ValueError("RSL2 sample count mismatch")
    output = np.empty(stream.sample_count, dtype=np.int64)
    for block in stream.blocks:
        start = block.info.sample_offset
        end = start + block.info.sample_count
        output[start:end] = _decode_lpc_block(block)
    return output


def run_lpc_liftpack_oracle(
    samples: np.ndarray,
    sample_rate: int,
    *,
    innovation_step: int = 64,
    block_sizes: tuple[int, ...] = (1024, 2048, 4096, 8192, 16384, 32768),
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> LPCOracleResult:
    """Compare complete RSL2 envelopes with block-RDO Main-0 RSL1."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("LPC oracle input must be mono int16 PCM")
    if source.size < 64 or sample_rate <= 0:
        raise ValueError("invalid LPC oracle input")
    blocks = tuple(sorted(set(int(value) for value in block_sizes)))
    if not blocks:
        raise ValueError("block_sizes must not be empty")

    innovation_q = _quantize_signed(
        source.astype(np.int64),
        innovation_step,
    )
    current_candidates = [
        pack_main0_residual_stream(
            sample_rate=sample_rate,
            innovation_q=innovation_q,
            innovation_step=innovation_step,
            residual_block_size=block_size,
        )
        for block_size in blocks
    ]
    current_anchor = min(current_candidates, key=len)

    candidates: list[tuple[bytes, np.ndarray, dict]] = []
    for block_size in blocks:
        residual_payload, residual_report = encode_lpc_liftpack_oracle(
            innovation_q,
            block_size=block_size,
            lpc_orders=lpc_orders,
        )
        restored_q = decode_lpc_liftpack_oracle(
            residual_payload,
            expected_count=int(source.size),
        )
        if not np.array_equal(restored_q, innovation_q.astype(np.int64)):
            raise RuntimeError("RSL2 oracle failed exact Innovation round-trip")
        payload = pack_rsc1(
            [
                RSC1Section(
                    "CONF",
                    pack_conf(
                        StreamConfig(
                            int(source.size),
                            innovation_step,
                            1,
                        )
                    ),
                ),
                RSC1Section("RSL2", residual_payload),
            ],
            profile=0,
            level=3,
            timebase_hz=sample_rate,
        )
        reconstruction = np.clip(
            restored_q * innovation_step,
            -32768,
            32767,
        ).astype(np.int16)
        parsed = parse_rsc1(payload)
        section_bytes = {
            bytes(section.type_code).decode("ascii"): len(section.payload)
            for section in parsed.sections
        }
        section_bytes["ENVELOPE"] = len(payload) - sum(section_bytes.values())
        report = {
            **residual_report,
            "block_size": block_size,
            "residual_stream_bytes": residual_report["stream_bytes"],
            "stream_bytes": len(payload),
            "stream_sha256": hashlib.sha256(payload).hexdigest(),
            "section_bytes": section_bytes,
            **_quality_report(source, reconstruction),
        }
        reconstruction.flags.writeable = False
        candidates.append((payload, reconstruction, report))

    selected_payload, selected_reconstruction, selected_report = min(
        candidates,
        key=lambda item: (item[2]["stream_bytes"], item[2]["block_size"]),
    )
    report = {
        **selected_report,
        "status": "research oracle; not a decodable Main-0 profile",
        "format_profile": "prospective-LPC-RSC1-level-3",
        "rdo_objective": (
            "minimum complete prospective stream bytes at one Innovation step"
        ),
        "current_rsl1_anchor_bytes": len(current_anchor),
        "selected_reduction_vs_rsl1": (
            1.0 - len(selected_payload) / len(current_anchor)
        ),
        "candidate_count": len(candidates),
        "candidates": [candidate[2] for candidate in candidates],
    }
    return LPCOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
