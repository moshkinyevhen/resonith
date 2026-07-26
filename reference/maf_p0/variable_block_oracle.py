"""R-044 exact-byte oracle for variable LiftPack-2 block lifetimes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .codec import _quality_report, _quantize_signed
from .lpc_oracle import (
    BLOCK_HEADER,
    CHECKSUM,
    LPC_HEADER,
    LPC_PRECISION,
    MAX_COEFFICIENT_SUM_Q,
    MAX_LPC_ORDER,
    STREAM_HEADER,
    TRANSFORM_LPC,
    TRANSFORM_NAMES,
    VERSION,
    _encode_block,
    _inverse_lpc,
    _measure_block,
    encode_lpc_liftpack_oracle,
)
from .residual import (
    MAX_ABSOLUTE_INPUT,
    TRANSFORM_HAAR,
    _decode_entropy,
    _inverse_transform,
    _next_power_of_two,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf


MAGIC = b"RSLV"
MINIMUM_BLOCK_SAMPLES = 16
MAXIMUM_BLOCK_SAMPLES = 32768


@dataclass(frozen=True)
class VariableBlockOracleResult:
    """Smallest fixed or variable complete stream and its gate evidence."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _candidate_boundaries(sample_count: int, quantum: int) -> tuple[int, ...]:
    if quantum < MINIMUM_BLOCK_SAMPLES:
        raise ValueError("variable-block quantum is below the profile bound")
    boundaries = [0]
    position = quantum
    while position < sample_count:
        if sample_count - position >= MINIMUM_BLOCK_SAMPLES:
            boundaries.append(position)
        position += quantum
    boundaries.append(sample_count)
    return tuple(boundaries)


def encode_variable_liftpack_oracle(
    values: np.ndarray,
    *,
    boundary_quantum: int = 1024,
    maximum_block_size: int = MAXIMUM_BLOCK_SAMPLES,
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> tuple[bytes, dict]:
    """Find an exact minimum-byte partition over a bounded boundary lattice."""

    source = np.asarray(values)
    if source.ndim != 1 or not np.issubdtype(source.dtype, np.signedinteger):
        raise TypeError("RSLV input must be a signed integer vector")
    source64 = source.astype(np.int64)
    if source64.size < MINIMUM_BLOCK_SAMPLES:
        raise ValueError("RSLV input is shorter than one bounded block")
    if (
        maximum_block_size < boundary_quantum
        or maximum_block_size > MAXIMUM_BLOCK_SAMPLES
    ):
        raise ValueError("RSLV maximum block size exceeds the profile bound")
    if int(np.max(np.abs(source64))) > MAX_ABSOLUTE_INPUT:
        raise ValueError("RSLV input exceeds the sample bound")
    orders = tuple(sorted(set(int(order) for order in lpc_orders)))
    if not orders or orders[0] < 1 or orders[-1] > MAX_LPC_ORDER:
        raise ValueError("RSLV LPC order exceeds the bound")

    boundaries = _candidate_boundaries(int(source64.size), boundary_quantum)
    costs = [1 << 62] * len(boundaries)
    block_counts = [1 << 30] * len(boundaries)
    previous = [-1] * len(boundaries)
    measured_edges: dict[tuple[int, int], tuple[int, dict]] = {}
    costs[0] = 0
    block_counts[0] = 0

    # Every edge cost is the exact serialized block byte count. The dynamic
    # program therefore creates no boundary that fails to repay its header.
    for end_index in range(1, len(boundaries)):
        end = boundaries[end_index]
        for start_index in range(end_index - 1, -1, -1):
            start = boundaries[start_index]
            length = end - start
            if length > maximum_block_size:
                break
            if length < MINIMUM_BLOCK_SAMPLES or previous[start_index] < 0 and start:
                continue
            encoded_bytes, block_report = _measure_block(
                source64[start:end],
                orders,
            )
            measured_edges[(start_index, end_index)] = (
                encoded_bytes,
                block_report,
            )
            candidate_key = (
                costs[start_index] + encoded_bytes,
                block_counts[start_index] + 1,
                -length,
                start,
            )
            current_key = (
                costs[end_index],
                block_counts[end_index],
                0,
                boundaries[previous[end_index]]
                if previous[end_index] >= 0
                else int(source64.size),
            )
            if candidate_key < current_key:
                costs[end_index] = candidate_key[0]
                block_counts[end_index] = candidate_key[1]
                previous[end_index] = start_index
    if previous[-1] < 0:
        raise ValueError("RSLV boundary lattice cannot cover the input")

    edge_path: list[tuple[int, int]] = []
    cursor = len(boundaries) - 1
    while cursor:
        parent = previous[cursor]
        if parent < 0:
            raise RuntimeError("RSLV dynamic-program backpointer is invalid")
        edge_path.append((parent, cursor))
        cursor = parent
    edge_path.reverse()

    blocks: list[bytes] = []
    lengths: list[int] = []
    transform_counts = {
        **{name: 0 for name in TRANSFORM_NAMES.values()},
        "lpc": 0,
    }
    lpc_order_counts = {str(order): 0 for order in orders}
    for start_index, end_index in edge_path:
        encoded, block_report = _encode_block(
            source64[boundaries[start_index] : boundaries[end_index]],
            orders,
        )
        blocks.append(encoded)
        lengths.append(boundaries[end_index] - boundaries[start_index])
        transform_counts[block_report["transform"]] += 1
        if block_report["transform"] == "lpc":
            lpc_order_counts[str(block_report["order"])] += 1

    body = (
        STREAM_HEADER.pack(
            MAGIC,
            VERSION,
            max(lengths),
            int(source64.size),
            len(blocks),
        )
        + b"".join(blocks)
    )
    payload = body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)
    length_counts = {
        str(length): lengths.count(length)
        for length in sorted(set(lengths))
    }
    return payload, {
        "stream_bytes": len(payload),
        "boundary_quantum": boundary_quantum,
        "maximum_block_size": max(lengths),
        "block_count": len(blocks),
        "block_length_counts": length_counts,
        "boundary_samples": [
            boundaries[end_index]
            for _, end_index in edge_path[:-1]
        ],
        "transform_counts": transform_counts,
        "lpc_order_counts": lpc_order_counts,
        "evaluated_edge_count": len(measured_edges),
    }


def decode_variable_liftpack_oracle(
    payload: bytes,
    *,
    expected_count: int | None = None,
) -> np.ndarray:
    """Independently validate and invert one research-only RSLV payload."""

    if len(payload) < STREAM_HEADER.size + CHECKSUM.size:
        raise ValueError("truncated RSLV stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("RSLV checksum mismatch")
    magic, version, maximum_block_size, sample_count, block_count = (
        STREAM_HEADER.unpack_from(body)
    )
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported RSLV stream")
    if (
        not MINIMUM_BLOCK_SAMPLES
        <= maximum_block_size
        <= MAXIMUM_BLOCK_SAMPLES
        or sample_count > (1 << 31) - 1
        or block_count == 0
        or block_count > (sample_count + MINIMUM_BLOCK_SAMPLES - 1)
        // MINIMUM_BLOCK_SAMPLES
    ):
        raise ValueError("RSLV stream exceeds the research bound")
    if expected_count is not None and sample_count != expected_count:
        raise ValueError("RSLV sample count mismatch")

    output = np.empty(sample_count, dtype=np.int64)
    cursor = STREAM_HEADER.size
    output_cursor = 0
    for _ in range(block_count):
        if cursor + BLOCK_HEADER.size > len(body):
            raise ValueError("truncated RSLV block header")
        length, transform, entropy, parameter, bit_count = (
            BLOCK_HEADER.unpack_from(body, cursor)
        )
        cursor += BLOCK_HEADER.size
        if (
            length < MINIMUM_BLOCK_SAMPLES
            or length > maximum_block_size
            or length > sample_count - output_cursor
        ):
            raise ValueError("RSLV block length exceeds the declared lifetime")

        coefficients_q = None
        coefficient_count = length
        if transform == TRANSFORM_LPC:
            if cursor + LPC_HEADER.size > len(body):
                raise ValueError("truncated RSLV LPC header")
            order, precision = LPC_HEADER.unpack_from(body, cursor)
            cursor += LPC_HEADER.size
            if (
                not 1 <= order <= MAX_LPC_ORDER
                or order >= length
                or precision != LPC_PRECISION
            ):
                raise ValueError("RSLV LPC parameter exceeds the bound")
            coefficient_bytes = 2 * order
            end = cursor + coefficient_bytes
            if end > len(body):
                raise ValueError("truncated RSLV LPC coefficients")
            coefficients_q = np.frombuffer(
                body[cursor:end],
                dtype="<i2",
            ).copy()
            if (
                int(np.sum(np.abs(coefficients_q.astype(np.int64))))
                > MAX_COEFFICIENT_SUM_Q
            ):
                raise ValueError("RSLV coefficient sum exceeds the bound")
            cursor = end
        elif transform == TRANSFORM_HAAR:
            coefficient_count = _next_power_of_two(length)
        elif transform not in TRANSFORM_NAMES:
            raise ValueError("unknown RSLV transform")

        if bit_count > coefficient_count * 96:
            raise ValueError("RSLV entropy payload exceeds the block bound")
        payload_bytes = (bit_count + 7) // 8
        end = cursor + payload_bytes
        if end > len(body):
            raise ValueError("truncated RSLV entropy payload")
        coefficients = _decode_entropy(
            body[cursor:end],
            bit_count,
            coefficient_count,
            entropy,
            parameter,
        )
        restored = (
            _inverse_lpc(coefficients, coefficients_q)
            if coefficients_q is not None
            else _inverse_transform(coefficients, transform, length)
        )
        output[output_cursor : output_cursor + length] = restored[:length]
        output_cursor += length
        cursor = end
    if output_cursor != sample_count or cursor != len(body):
        raise ValueError("trailing or incomplete RSLV data")
    return output


def _pack_complete_stream(
    residual_type: str,
    residual_payload: bytes,
    *,
    sample_rate: int,
    sample_count: int,
    innovation_step: int,
) -> bytes:
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, innovation_step, 1)),
            ),
            RSC1Section(residual_type, residual_payload),
        ],
        profile=0,
        level=3,
        timebase_hz=sample_rate,
    )


def run_variable_block_oracle(
    samples: np.ndarray,
    sample_rate: int,
    *,
    innovation_step: int = 64,
    fixed_block_sizes: tuple[int, ...] = (
        1024,
        2048,
        4096,
        8192,
        16384,
        32768,
    ),
    boundary_quanta: tuple[int, ...] = (1024,),
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> VariableBlockOracleResult:
    """Compare complete variable-lifetime streams with every fixed RSL2 anchor."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("variable-block oracle input must be mono int16 PCM")
    if source.size < MINIMUM_BLOCK_SAMPLES or sample_rate <= 0:
        raise ValueError("invalid variable-block oracle input")
    innovation_q = _quantize_signed(source.astype(np.int64), innovation_step)

    fixed_candidates: list[tuple[bytes, dict]] = []
    for block_size in sorted(set(int(value) for value in fixed_block_sizes)):
        residual, residual_report = encode_lpc_liftpack_oracle(
            innovation_q,
            block_size=block_size,
            lpc_orders=lpc_orders,
        )
        complete = _pack_complete_stream(
            "RSL2",
            residual,
            sample_rate=sample_rate,
            sample_count=int(source.size),
            innovation_step=innovation_step,
        )
        fixed_candidates.append(
            (
                complete,
                {
                    **residual_report,
                    "mode": "fixed",
                    "stream_bytes": len(complete),
                    "residual_stream_bytes": len(residual),
                },
            )
        )
    fixed_payload, fixed_report = min(
        fixed_candidates,
        key=lambda item: (len(item[0]), item[1]["block_size"]),
    )

    variable_candidates: list[tuple[bytes, np.ndarray, dict]] = []
    for quantum in sorted(set(int(value) for value in boundary_quanta)):
        residual, residual_report = encode_variable_liftpack_oracle(
            innovation_q,
            boundary_quantum=quantum,
            lpc_orders=lpc_orders,
        )
        restored_q = decode_variable_liftpack_oracle(
            residual,
            expected_count=int(source.size),
        )
        if not np.array_equal(restored_q, innovation_q.astype(np.int64)):
            raise RuntimeError("RSLV failed exact Innovation round-trip")
        complete = _pack_complete_stream(
            "RSLV",
            residual,
            sample_rate=sample_rate,
            sample_count=int(source.size),
            innovation_step=innovation_step,
        )
        reconstruction = np.clip(
            restored_q * innovation_step,
            -32768,
            32767,
        ).astype(np.int16)
        parsed = parse_rsc1(complete)
        section_bytes = {
            bytes(section.type_code).decode("ascii"): len(section.payload)
            for section in parsed.sections
        }
        section_bytes["ENVELOPE"] = len(complete) - sum(section_bytes.values())
        report = {
            **residual_report,
            "mode": "variable",
            "stream_bytes": len(complete),
            "residual_stream_bytes": len(residual),
            "stream_sha256": hashlib.sha256(complete).hexdigest(),
            "section_bytes": section_bytes,
            **_quality_report(source, reconstruction),
        }
        reconstruction.flags.writeable = False
        variable_candidates.append((complete, reconstruction, report))
    variable_payload, variable_reconstruction, variable_report = min(
        variable_candidates,
        key=lambda item: (
            len(item[0]),
            item[2]["boundary_quantum"],
        ),
    )

    variable_won = len(variable_payload) < len(fixed_payload)
    selected_payload = variable_payload if variable_won else fixed_payload
    selected_reconstruction = (
        variable_reconstruction
        if variable_won
        else np.clip(
            innovation_q.astype(np.int64) * innovation_step,
            -32768,
            32767,
        ).astype(np.int16)
    )
    selected_reconstruction.flags.writeable = False
    selected_report = variable_report if variable_won else fixed_report
    report = {
        **selected_report,
        "status": "research oracle; no normative variable-block syntax",
        "format_profile": "prospective-variable-RSC1-level-3",
        "rdo_objective": "minimum complete bytes at one Innovation step",
        "fixed_anchor_bytes": len(fixed_payload),
        "fixed_anchor_block_size": fixed_report["block_size"],
        "best_variable_bytes": len(variable_payload),
        "variable_won": variable_won,
        "variable_reduction_vs_fixed": (
            1.0 - len(variable_payload) / len(fixed_payload)
        ),
        "candidate_count": len(fixed_candidates) + len(variable_candidates),
        "variable_candidates": [
            candidate[2] for candidate in variable_candidates
        ],
    }
    return VariableBlockOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
