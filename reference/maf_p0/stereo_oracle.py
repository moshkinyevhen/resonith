"""R-045 complete-byte oracle for reversible stereo lifting."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .codec import _quality_report, _quantize_signed
from .lpc_oracle import (
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf


CHANNEL_MAGIC = b"CHM0"
CHANNEL_VERSION = 1
CHANNEL_HEADER = struct.Struct("<4sBBH")
MODE_IDS = {
    "independent": 0,
    "mid_side": 1,
    "left_side": 2,
    "right_side": 3,
}
ID_MODES = {value: key for key, value in MODE_IDS.items()}


@dataclass(frozen=True)
class StereoOracleResult:
    """Selected prospective stereo stream and exact channel reconstruction."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _forward_channels(
    channels: np.ndarray,
    mode: str,
) -> tuple[np.ndarray, np.ndarray]:
    left = channels[:, 0].astype(np.int64, copy=False)
    right = channels[:, 1].astype(np.int64, copy=False)
    if mode == "independent":
        return left.copy(), right.copy()
    if mode == "mid_side":
        side = right - left
        mid = left + np.floor_divide(side, 2)
        return mid, side
    if mode == "left_side":
        return left.copy(), right - left
    if mode == "right_side":
        return right.copy(), left - right
    raise ValueError("unknown stereo lifting mode")


def _inverse_channels(
    first: np.ndarray,
    second: np.ndarray,
    mode: str,
) -> np.ndarray:
    if mode == "independent":
        left, right = first, second
    elif mode == "mid_side":
        left = first - np.floor_divide(second, 2)
        right = second + left
    elif mode == "left_side":
        left = first
        right = first + second
    elif mode == "right_side":
        right = first
        left = first + second
    else:
        raise ValueError("unknown stereo lifting mode")
    return np.column_stack((left, right)).astype(np.int64, copy=False)


def _best_component(
    values: np.ndarray,
    block_sizes: tuple[int, ...],
    lpc_orders: tuple[int, ...],
) -> tuple[bytes, dict]:
    candidates = []
    for block_size in block_sizes:
        payload, report = encode_lpc_liftpack_oracle(
            values,
            block_size=block_size,
            lpc_orders=lpc_orders,
        )
        candidates.append((payload, report))
    return min(
        candidates,
        key=lambda item: (len(item[0]), item[1]["block_size"]),
    )


def _pack_channel_header(mode: str) -> bytes:
    return CHANNEL_HEADER.pack(
        CHANNEL_MAGIC,
        CHANNEL_VERSION,
        MODE_IDS[mode],
        0,
    )


def _pack_stereo_stream(
    *,
    sample_rate: int,
    sample_count: int,
    innovation_step: int,
    mode: str,
    components: tuple[bytes, bytes],
) -> bytes:
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, innovation_step, 2)),
            ),
            RSC1Section("CHMX", _pack_channel_header(mode)),
            RSC1Section("RSL2", components[0], instance_id=0),
            RSC1Section("RSL2", components[1], instance_id=1),
        ],
        profile=0,
        level=3,
        timebase_hz=sample_rate,
    )


def decode_stereo_oracle(payload: bytes) -> tuple[int, np.ndarray]:
    """Independently parse and invert one prospective two-channel stream."""

    info = parse_rsc1(payload)
    sections: dict[tuple[bytes, int], RSC1Section] = {
        (bytes(section.type_code), section.instance_id): section
        for section in info.sections
    }
    expected = {
        (b"CHMX", 0),
        (b"CONF", 0),
        (b"RSL2", 0),
        (b"RSL2", 1),
    }
    if set(sections) != expected:
        raise ValueError("prospective stereo stream has non-canonical sections")
    config = unpack_conf(sections[(b"CONF", 0)].payload)
    if config.output_channels != 2:
        raise ValueError("prospective stereo stream must have two channels")
    channel_payload = sections[(b"CHMX", 0)].payload
    if len(channel_payload) != CHANNEL_HEADER.size:
        raise ValueError("invalid prospective stereo channel header")
    magic, version, mode_id, reserved = CHANNEL_HEADER.unpack(channel_payload)
    if (
        magic != CHANNEL_MAGIC
        or version != CHANNEL_VERSION
        or mode_id not in ID_MODES
        or reserved != 0
    ):
        raise ValueError("unsupported prospective stereo channel mode")
    first = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 0)].payload,
        expected_count=config.sample_count,
    )
    second = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 1)].payload,
        expected_count=config.sample_count,
    )
    return info.timebase_hz, _inverse_channels(
        first,
        second,
        ID_MODES[mode_id],
    )


def run_stereo_lifting_oracle(
    samples: np.ndarray,
    sample_rate: int,
    *,
    innovation_step: int = 64,
    block_sizes: tuple[int, ...] = (
        1024,
        2048,
        4096,
        8192,
        16384,
        32768,
    ),
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> StereoOracleResult:
    """Compete four reversible channel maps by complete prospective bytes."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 2 or source.shape[1] != 2:
        raise TypeError("stereo oracle input must be frame-major stereo int16")
    if source.shape[0] < 64 or sample_rate <= 0:
        raise ValueError("invalid stereo oracle input")
    blocks = tuple(sorted(set(int(value) for value in block_sizes)))
    if not blocks:
        raise ValueError("stereo oracle block_sizes must not be empty")
    quantized = np.column_stack(
        (
            _quantize_signed(source[:, 0].astype(np.int64), innovation_step),
            _quantize_signed(source[:, 1].astype(np.int64), innovation_step),
        )
    )

    candidates: list[tuple[bytes, np.ndarray, dict]] = []
    for mode in MODE_IDS:
        first, second = _forward_channels(quantized, mode)
        first_payload, first_report = _best_component(
            first,
            blocks,
            lpc_orders,
        )
        second_payload, second_report = _best_component(
            second,
            blocks,
            lpc_orders,
        )
        payload = _pack_stereo_stream(
            sample_rate=sample_rate,
            sample_count=int(source.shape[0]),
            innovation_step=innovation_step,
            mode=mode,
            components=(first_payload, second_payload),
        )
        decoded_rate, restored_q = decode_stereo_oracle(payload)
        if (
            decoded_rate != sample_rate
            or not np.array_equal(restored_q, quantized.astype(np.int64))
        ):
            raise RuntimeError("prospective stereo lifting is not exact")
        reconstruction = np.clip(
            restored_q * innovation_step,
            -32768,
            32767,
        ).astype(np.int16)
        reconstruction.flags.writeable = False
        candidates.append(
            (
                payload,
                reconstruction,
                {
                    "mode": mode,
                    "stream_bytes": len(payload),
                    "stream_sha256": hashlib.sha256(payload).hexdigest(),
                    "component_bytes": [
                        len(first_payload),
                        len(second_payload),
                    ],
                    "component_block_sizes": [
                        first_report["block_size"],
                        second_report["block_size"],
                    ],
                    "component_transform_counts": [
                        first_report["transform_counts"],
                        second_report["transform_counts"],
                    ],
                    **_quality_report(source, reconstruction),
                },
            )
        )

    independent = next(
        item for item in candidates if item[2]["mode"] == "independent"
    )
    selected_payload, selected_reconstruction, selected_report = min(
        candidates,
        key=lambda item: (len(item[0]), MODE_IDS[item[2]["mode"]]),
    )
    report = {
        **selected_report,
        "status": "research oracle; no normative stereo syntax",
        "format_profile": "prospective-stereo-RSC1-level-3",
        "rdo_objective": "minimum complete bytes at one channel-local Truth step",
        "independent_anchor_bytes": len(independent[0]),
        "selected_reduction_vs_independent": (
            1.0 - len(selected_payload) / len(independent[0])
        ),
        "candidate_count": len(candidates),
        "candidates": [candidate[2] for candidate in candidates],
    }
    return StereoOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
