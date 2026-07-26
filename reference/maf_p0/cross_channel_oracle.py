"""R-046 oracle for one-MAC reversible cross-channel prediction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .codec import _quality_report, _quantize_signed
from .lpc_oracle import decode_lpc_liftpack_oracle
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stereo_oracle import (
    _best_component,
    decode_stereo_oracle,
    run_stereo_lifting_oracle,
)
from .stream_sections import StreamConfig, pack_conf, unpack_conf


CROSS_MAGIC = b"XCH0"
CROSS_VERSION = 1
CROSS_HEADER = struct.Struct("<4sBBhhH")
GAIN_PRECISION = 12
MAXIMUM_DELAY = 32


@dataclass(frozen=True)
class CrossChannelOracleResult:
    """Selected R-045 fallback or exact cross-channel candidate."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _round_q12(values: np.ndarray) -> np.ndarray:
    magnitudes = (np.abs(values) + (1 << (GAIN_PRECISION - 1))) >> GAIN_PRECISION
    return np.where(values < 0, -magnitudes, magnitudes).astype(np.int64)


def _overlap_slices(
    sample_count: int,
    delay: int,
) -> tuple[slice, slice]:
    if delay >= 0:
        return slice(delay, sample_count), slice(0, sample_count - delay)
    lookahead = -delay
    return slice(0, sample_count - lookahead), slice(lookahead, sample_count)


def _predict_reference(
    reference: np.ndarray,
    coefficient_q12: int,
    delay: int,
) -> np.ndarray:
    output = np.zeros(reference.size, dtype=np.int64)
    target_slice, reference_slice = _overlap_slices(reference.size, delay)
    accumulator = (
        reference[reference_slice].astype(np.int64, copy=False)
        * int(coefficient_q12)
    )
    output[target_slice] = _round_q12(accumulator)
    return output


def _fit_gain_delay(
    reference: np.ndarray,
    target: np.ndarray,
    delay: int,
) -> tuple[int, np.ndarray, int]:
    target_slice, reference_slice = _overlap_slices(reference.size, delay)
    reference_overlap = reference[reference_slice].astype(
        np.int64,
        copy=False,
    )
    target_overlap = target[target_slice].astype(np.int64, copy=False)
    energy = int(reference_overlap @ reference_overlap)
    if energy == 0:
        coefficient = 0
    else:
        coefficient = int(
            np.clip(
                np.rint(
                    float(target_overlap @ reference_overlap)
                    * (1 << GAIN_PRECISION)
                    / energy
                ),
                -32768,
                32767,
            )
        )
    residual = target.astype(np.int64) - _predict_reference(
        reference,
        coefficient,
        delay,
    )
    residual_energy = int(residual @ residual)
    return coefficient, residual, residual_energy


def _pack_cross_stream(
    *,
    sample_rate: int,
    sample_count: int,
    innovation_step: int,
    direction: int,
    delay: int,
    coefficient_q12: int,
    components: tuple[bytes, bytes],
) -> bytes:
    header = CROSS_HEADER.pack(
        CROSS_MAGIC,
        CROSS_VERSION,
        direction,
        delay,
        coefficient_q12,
        0,
    )
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, innovation_step, 2)),
            ),
            RSC1Section("RSL2", components[0], instance_id=0),
            RSC1Section("RSL2", components[1], instance_id=1),
            RSC1Section("XCHN", header),
        ],
        profile=0,
        level=3,
        timebase_hz=sample_rate,
    )


def decode_cross_channel_oracle(payload: bytes) -> tuple[int, np.ndarray]:
    """Decode a cross-channel research stream or its exact R-045 fallback."""

    info = parse_rsc1(payload)
    type_codes = {bytes(section.type_code) for section in info.sections}
    if b"XCHN" not in type_codes:
        return decode_stereo_oracle(payload)
    sections = {
        (bytes(section.type_code), section.instance_id): section
        for section in info.sections
    }
    expected = {
        (b"CONF", 0),
        (b"RSL2", 0),
        (b"RSL2", 1),
        (b"XCHN", 0),
    }
    if set(sections) != expected:
        raise ValueError("cross-channel stream has non-canonical sections")
    config = unpack_conf(sections[(b"CONF", 0)].payload)
    if config.output_channels != 2:
        raise ValueError("cross-channel stream must have two channels")
    header = sections[(b"XCHN", 0)].payload
    if len(header) != CROSS_HEADER.size:
        raise ValueError("invalid cross-channel header")
    magic, version, direction, delay, coefficient, reserved = (
        CROSS_HEADER.unpack(header)
    )
    if (
        magic != CROSS_MAGIC
        or version != CROSS_VERSION
        or direction not in {0, 1}
        or abs(delay) > MAXIMUM_DELAY
        or reserved != 0
    ):
        raise ValueError("unsupported cross-channel predictor")
    reference = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 0)].payload,
        expected_count=config.sample_count,
    )
    residual = decode_lpc_liftpack_oracle(
        sections[(b"RSL2", 1)].payload,
        expected_count=config.sample_count,
    )
    target = residual + _predict_reference(reference, coefficient, delay)
    output = (
        np.column_stack((reference, target))
        if direction == 0
        else np.column_stack((target, reference))
    )
    return info.timebase_hz, output.astype(np.int64, copy=False)


def run_cross_channel_oracle(
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
    delays: tuple[int, ...] = tuple(range(-32, 33)),
    shortlist_per_direction: int = 4,
) -> CrossChannelOracleResult:
    """Shortlist by residual energy, then select only by complete bytes."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 2 or source.shape[1] != 2:
        raise TypeError("cross-channel input must be frame-major stereo int16")
    if source.shape[0] < 64 or sample_rate <= 0:
        raise ValueError("invalid cross-channel input")
    if shortlist_per_direction < 1 or shortlist_per_direction > 16:
        raise ValueError("cross-channel shortlist exceeds the research bound")
    delay_candidates = tuple(sorted(set(int(value) for value in delays)))
    if (
        not delay_candidates
        or delay_candidates[0] < -MAXIMUM_DELAY
        or delay_candidates[-1] > MAXIMUM_DELAY
    ):
        raise ValueError("cross-channel delay exceeds the research bound")

    fallback = run_stereo_lifting_oracle(
        source,
        sample_rate,
        innovation_step=innovation_step,
        block_sizes=block_sizes,
        lpc_orders=lpc_orders,
    )
    quantized = np.column_stack(
        (
            _quantize_signed(source[:, 0].astype(np.int64), innovation_step),
            _quantize_signed(source[:, 1].astype(np.int64), innovation_step),
        )
    )
    blocks = tuple(sorted(set(int(value) for value in block_sizes)))
    cross_candidates: list[tuple[bytes, np.ndarray, dict]] = []
    for direction in (0, 1):
        reference = quantized[:, direction].astype(np.int64, copy=False)
        target = quantized[:, 1 - direction].astype(np.int64, copy=False)
        reference_payload, reference_report = _best_component(
            reference,
            blocks,
            lpc_orders,
        )
        proposals = []
        for delay in delay_candidates:
            coefficient, residual, residual_energy = _fit_gain_delay(
                reference,
                target,
                delay,
            )
            proposals.append(
                (
                    residual_energy,
                    abs(delay),
                    delay,
                    coefficient,
                    residual,
                )
            )
        shortlisted = sorted(
            proposals,
            key=lambda item: item[:4],
        )[:shortlist_per_direction]
        for residual_energy, _, delay, coefficient, residual in shortlisted:
            residual_payload, residual_report = _best_component(
                residual,
                blocks,
                lpc_orders,
            )
            payload = _pack_cross_stream(
                sample_rate=sample_rate,
                sample_count=int(source.shape[0]),
                innovation_step=innovation_step,
                direction=direction,
                delay=delay,
                coefficient_q12=coefficient,
                components=(reference_payload, residual_payload),
            )
            decoded_rate, restored_q = decode_cross_channel_oracle(payload)
            if (
                decoded_rate != sample_rate
                or not np.array_equal(restored_q, quantized.astype(np.int64))
            ):
                raise RuntimeError("cross-channel candidate is not exact")
            reconstruction = np.clip(
                restored_q * innovation_step,
                -32768,
                32767,
            ).astype(np.int16)
            reconstruction.flags.writeable = False
            cross_candidates.append(
                (
                    payload,
                    reconstruction,
                    {
                        "mode": (
                            "left_reference"
                            if direction == 0
                            else "right_reference"
                        ),
                        "delay": delay,
                        "coefficient_q12": coefficient,
                        "residual_energy": residual_energy,
                        "stream_bytes": len(payload),
                        "stream_sha256": hashlib.sha256(payload).hexdigest(),
                        "component_bytes": [
                            len(reference_payload),
                            len(residual_payload),
                        ],
                        "component_block_sizes": [
                            reference_report["block_size"],
                            residual_report["block_size"],
                        ],
                        **_quality_report(source, reconstruction),
                    },
                )
            )

    best_cross = min(
        cross_candidates,
        key=lambda item: (
            len(item[0]),
            item[2]["mode"],
            abs(item[2]["delay"]),
            item[2]["delay"],
        ),
    )
    cross_won = len(best_cross[0]) < len(fallback.selected_payload)
    if cross_won:
        selected_payload, selected_reconstruction, selected_report = best_cross
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
        "status": "research oracle; no normative cross-channel syntax",
        "format_profile": "prospective-cross-channel-RSC1-level-3",
        "rdo_objective": "minimum complete bytes at one channel-local Truth step",
        "r045_anchor_bytes": len(fallback.selected_payload),
        "r045_anchor_mode": fallback.report["mode"],
        "best_cross_bytes": len(best_cross[0]),
        "cross_won": cross_won,
        "selected_reduction_vs_r045": (
            1.0 - len(best_cross[0]) / len(fallback.selected_payload)
        ),
        "candidate_count": 1 + len(cross_candidates),
        "cross_candidates": [candidate[2] for candidate in cross_candidates],
    }
    return CrossChannelOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
