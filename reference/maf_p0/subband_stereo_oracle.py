"""R-047 oracle for two-band reversible spatial lifting."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .codec import _quality_report, _quantize_signed
from .lpc_oracle import decode_lpc_liftpack_oracle
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stereo_oracle import (
    ID_MODES,
    MODE_IDS,
    _best_component,
    _forward_channels,
    _inverse_channels,
    decode_stereo_oracle,
    run_stereo_lifting_oracle,
)
from .stream_sections import StreamConfig, pack_conf, unpack_conf


SUBBAND_MAGIC = b"SBM0"
SUBBAND_VERSION = 1
SUBBAND_HEADER = struct.Struct("<4sBBBB")


@dataclass(frozen=True)
class SubbandStereoOracleResult:
    """Selected R-045 fallback or exact two-band stereo candidate."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _forward_temporal_haar(channels: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    source = channels.astype(np.int64, copy=False)
    padding = source.shape[0] & 1
    if padding:
        source = np.vstack((source, np.zeros((1, 2), dtype=np.int64)))
    even = source[0::2]
    odd = source[1::2]
    high = odd - even
    low = even + np.floor_divide(high, 2)
    return low, high, padding


def _inverse_temporal_haar(
    low: np.ndarray,
    high: np.ndarray,
    padding: int,
) -> np.ndarray:
    if low.shape != high.shape or low.ndim != 2 or low.shape[1] != 2:
        raise ValueError("two-band stereo coefficient shapes differ")
    even = low - np.floor_divide(high, 2)
    odd = high + even
    output = np.empty((2 * low.shape[0], 2), dtype=np.int64)
    output[0::2] = even
    output[1::2] = odd
    return output[:-1] if padding else output


def _pack_subband_stream(
    *,
    sample_rate: int,
    sample_count: int,
    innovation_step: int,
    low_mode: str,
    high_mode: str,
    padding: int,
    components: tuple[bytes, bytes],
) -> bytes:
    header = SUBBAND_HEADER.pack(
        SUBBAND_MAGIC,
        SUBBAND_VERSION,
        MODE_IDS[low_mode],
        MODE_IDS[high_mode],
        padding,
    )
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, innovation_step, 2)),
            ),
            RSC1Section("RSL2", components[0], instance_id=0),
            RSC1Section("RSL2", components[1], instance_id=1),
            RSC1Section("SBMX", header),
        ],
        profile=0,
        level=3,
        timebase_hz=sample_rate,
    )


def decode_subband_stereo_oracle(payload: bytes) -> tuple[int, np.ndarray]:
    """Decode a two-band research stream or its exact R-045 fallback."""

    info = parse_rsc1(payload)
    type_codes = {bytes(section.type_code) for section in info.sections}
    if b"SBMX" not in type_codes:
        return decode_stereo_oracle(payload)
    sections = {
        (bytes(section.type_code), section.instance_id): section
        for section in info.sections
    }
    expected = {
        (b"CONF", 0),
        (b"RSL2", 0),
        (b"RSL2", 1),
        (b"SBMX", 0),
    }
    if set(sections) != expected:
        raise ValueError("subband stereo stream has non-canonical sections")
    config = unpack_conf(sections[(b"CONF", 0)].payload)
    if config.output_channels != 2:
        raise ValueError("subband stereo stream must have two channels")
    header = sections[(b"SBMX", 0)].payload
    if len(header) != SUBBAND_HEADER.size:
        raise ValueError("invalid subband stereo header")
    magic, version, low_mode_id, high_mode_id, padding = (
        SUBBAND_HEADER.unpack(header)
    )
    if (
        magic != SUBBAND_MAGIC
        or version != SUBBAND_VERSION
        or low_mode_id not in ID_MODES
        or high_mode_id not in ID_MODES
        or padding not in {0, 1}
        or padding != config.sample_count % 2
    ):
        raise ValueError("unsupported subband stereo mode")
    padded_count = config.sample_count + padding
    first = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 0)].payload,
        expected_count=padded_count,
    )
    second = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 1)].payload,
        expected_count=padded_count,
    )
    band_length = padded_count // 2
    low = _inverse_channels(
        first[:band_length],
        second[:band_length],
        ID_MODES[low_mode_id],
    )
    high = _inverse_channels(
        first[band_length:],
        second[band_length:],
        ID_MODES[high_mode_id],
    )
    return info.timebase_hz, _inverse_temporal_haar(low, high, padding)


def run_subband_stereo_oracle(
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
) -> SubbandStereoOracleResult:
    """Compete all sixteen two-band channel maps by complete bytes."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 2 or source.shape[1] != 2:
        raise TypeError("subband stereo input must be frame-major stereo int16")
    if source.shape[0] < 64 or sample_rate <= 0:
        raise ValueError("invalid subband stereo input")
    blocks = tuple(sorted(set(int(value) for value in block_sizes)))
    if not blocks:
        raise ValueError("subband stereo block_sizes must not be empty")
    quantized = np.column_stack(
        (
            _quantize_signed(source[:, 0].astype(np.int64), innovation_step),
            _quantize_signed(source[:, 1].astype(np.int64), innovation_step),
        )
    )
    low, high, padding = _forward_temporal_haar(quantized)
    fallback = run_stereo_lifting_oracle(
        source,
        sample_rate,
        innovation_step=innovation_step,
        block_sizes=blocks,
        lpc_orders=lpc_orders,
    )

    candidates: list[tuple[bytes, np.ndarray, dict]] = []
    for low_mode in MODE_IDS:
        low_first, low_second = _forward_channels(low, low_mode)
        for high_mode in MODE_IDS:
            high_first, high_second = _forward_channels(high, high_mode)
            first = np.concatenate((low_first, high_first))
            second = np.concatenate((low_second, high_second))
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
            payload = _pack_subband_stream(
                sample_rate=sample_rate,
                sample_count=int(source.shape[0]),
                innovation_step=innovation_step,
                low_mode=low_mode,
                high_mode=high_mode,
                padding=padding,
                components=(first_payload, second_payload),
            )
            decoded_rate, restored_q = decode_subband_stereo_oracle(payload)
            if (
                decoded_rate != sample_rate
                or not np.array_equal(restored_q, quantized.astype(np.int64))
            ):
                raise RuntimeError("two-band stereo candidate is not exact")
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
                        "low_mode": low_mode,
                        "high_mode": high_mode,
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
                        **_quality_report(source, reconstruction),
                    },
                )
            )

    best_subband = min(
        candidates,
        key=lambda item: (
            len(item[0]),
            MODE_IDS[item[2]["low_mode"]],
            MODE_IDS[item[2]["high_mode"]],
        ),
    )
    subband_won = len(best_subband[0]) < len(fallback.selected_payload)
    if subband_won:
        selected_payload, selected_reconstruction, selected_report = best_subband
    else:
        selected_payload = fallback.selected_payload
        selected_reconstruction = fallback.selected_reconstruction
        selected_report = {
            "mode": f"r045_{fallback.report['mode']}",
            "stream_bytes": len(fallback.selected_payload),
            "stream_sha256": hashlib.sha256(
                fallback.selected_payload
            ).hexdigest(),
            **_quality_report(source, fallback.selected_reconstruction),
        }
    report = {
        **selected_report,
        "status": "research oracle; no normative subband stereo syntax",
        "format_profile": "prospective-two-band-stereo-RSC1-level-3",
        "rdo_objective": "minimum complete bytes at one channel-local Truth step",
        "r045_anchor_bytes": len(fallback.selected_payload),
        "r045_anchor_mode": fallback.report["mode"],
        "best_subband_bytes": len(best_subband[0]),
        "subband_won": subband_won,
        "selected_reduction_vs_r045": (
            1.0 - len(best_subband[0]) / len(fallback.selected_payload)
        ),
        "candidate_count": 1 + len(candidates),
        "subband_candidates": [candidate[2] for candidate in candidates],
    }
    return SubbandStereoOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
