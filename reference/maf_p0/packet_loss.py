"""Block-local packet-loss containment experiments for Main-0."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .codec import _quality_report
from .lpc_oracle import (
    LPCBlockInfo,
    decode_lpc_liftpack_block,
    index_lpc_liftpack_blocks,
)
from .multichannel import decode_main0_independent_stream
from .rsc1 import parse_rsc1
from .stream_sections import unpack_conf


@dataclass(frozen=True)
class PacketLossSimulationResult:
    """Concealed PCM, undamaged Truth, and containment evidence."""

    reconstruction: np.ndarray
    truth: np.ndarray
    report: dict


def _loss_runs(losses: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Return inclusive consecutive block-index intervals."""

    if not losses:
        return ()
    runs: list[tuple[int, int]] = []
    start = losses[0]
    previous = start
    for block in losses[1:]:
        if block != previous + 1:
            runs.append((start, previous))
            start = block
        previous = block
    runs.append((start, previous))
    return tuple(runs)


def _fade_last_frame(previous: np.ndarray, frame_count: int) -> np.ndarray:
    """Conceal one interval with signed integer decay toward exact zero."""

    if frame_count <= 0:
        raise ValueError("concealment frame count must be positive")
    source = np.asarray(previous)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("concealment state must be one PCM16 frame")
    factors = np.arange(frame_count - 1, -1, -1, dtype=np.int64)
    magnitudes = (
        np.abs(source.astype(np.int64))[np.newaxis, :]
        * factors[:, np.newaxis]
    ) // frame_count
    concealed = np.where(
        source[np.newaxis, :] < 0,
        -magnitudes,
        magnitudes,
    ).astype(np.int16)
    return concealed


def simulate_aligned_packet_loss(
    payload: bytes,
    *,
    lost_blocks: tuple[int, ...] | list[int],
) -> PacketLossSimulationResult:
    """Lose aligned channel blocks and prove exact recovery afterward."""

    truth_result = decode_main0_independent_stream(payload)
    info = parse_rsc1(payload)
    config_sections = [
        section
        for section in info.sections
        if bytes(section.type_code) == b"CONF"
    ]
    residual_sections = [
        section
        for section in info.sections
        if bytes(section.type_code) == b"RSL2"
    ]
    if len(config_sections) != 1:
        raise ValueError("packet-loss simulation requires one CONF")
    config = unpack_conf(config_sections[0].payload)
    if len(residual_sections) != config.output_channels:
        raise ValueError("packet-loss simulation requires every channel")

    channel_indexes = tuple(
        index_lpc_liftpack_blocks(section.payload)
        for section in residual_sections
    )
    block_count = len(channel_indexes[0])
    if any(len(index) != block_count for index in channel_indexes):
        raise ValueError("packet-loss channel block counts differ")
    for block in range(block_count):
        anchor = channel_indexes[0][block]
        if any(
            (
                index[block].sample_offset,
                index[block].sample_count,
            )
            != (anchor.sample_offset, anchor.sample_count)
            for index in channel_indexes[1:]
        ):
            raise ValueError("packet-loss channel block intervals differ")

    losses = tuple(sorted({int(value) for value in lost_blocks}))
    if any(block < 0 or block >= block_count for block in losses):
        raise ValueError("lost block index exceeds the stream")
    lost_set = frozenset(losses)
    output = np.empty_like(truth_result.samples)
    affected = np.zeros(config.sample_count, dtype=bool)
    lost_payload_bytes = 0
    recovery_checks: list[dict] = []

    for block in range(block_count):
        anchor = channel_indexes[0][block]
        start = anchor.sample_offset
        end = start + anchor.sample_count
        if block in lost_set:
            previous = (
                output[start - 1]
                if start > 0
                else np.zeros(config.output_channels, dtype=np.int16)
            )
            output[start:end] = _fade_last_frame(
                previous,
                anchor.sample_count,
            )
            affected[start:end] = True
            lost_payload_bytes += sum(
                channel_indexes[channel][block].byte_size
                for channel in range(config.output_channels)
            )
            continue

        decoded_channels: list[np.ndarray] = []
        for channel, section in enumerate(residual_sections):
            block_info, innovation = decode_lpc_liftpack_block(
                section.payload,
                block,
            )
            expected = channel_indexes[channel][block]
            if block_info != expected:
                raise RuntimeError("RSL2 block decode index drift")
            decoded_channels.append(innovation)
        innovation_matrix = np.stack(decoded_channels, axis=1)
        output[start:end] = np.clip(
            innovation_matrix * np.int64(config.innovation_step),
            -32768,
            32767,
        ).astype(np.int16)

    runs = _loss_runs(losses)
    for first, last in runs:
        next_block = last + 1
        if next_block >= block_count:
            recovery_checks.append(
                {
                    "lost_block_start": first,
                    "lost_block_end": last,
                    "next_block": None,
                    "next_block_exact": None,
                }
            )
            continue
        next_info: LPCBlockInfo = channel_indexes[0][next_block]
        start = next_info.sample_offset
        end = start + next_info.sample_count
        recovery_checks.append(
            {
                "lost_block_start": first,
                "lost_block_end": last,
                "next_block": next_block,
                "next_block_exact": bool(
                    np.array_equal(
                        output[start:end],
                        truth_result.samples[start:end],
                    )
                ),
            }
        )

    exact_outside_loss = bool(
        np.array_equal(
            output[~affected],
            truth_result.samples[~affected],
        )
    )
    output.flags.writeable = False
    report = {
        "status": "research packet-loss containment simulation",
        "concealment": "integer fade from last available frame to zero",
        "block_count": block_count,
        "lost_blocks": list(losses),
        "loss_runs": [list(run) for run in runs],
        "lost_block_fraction": len(losses) / block_count,
        "affected_frames": int(np.count_nonzero(affected)),
        "lost_payload_bytes": lost_payload_bytes,
        "exact_outside_loss": exact_outside_loss,
        "all_recoverable_next_blocks_exact": all(
            item["next_block_exact"] is not False
            for item in recovery_checks
        ),
        "recovery_checks": recovery_checks,
        **_quality_report(
            truth_result.samples.reshape(-1),
            output.reshape(-1),
        ),
    }
    return PacketLossSimulationResult(
        reconstruction=output,
        truth=truth_result.samples,
        report=report,
    )
