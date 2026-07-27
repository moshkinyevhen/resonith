"""R-108 PVE2: compact PVQ basis plus sparse transform TruthInnovation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .codec import _quality_report
from .lapped_oracle import LappedAnalysis, _band_edges, _synthesize
from .pvq_envelope_oracle import (
    PvqEnvelopeDecodeResult,
    _source_coefficient_row,
    decode_pvq_envelope_stream,
    encode_pvq_envelope_analysis,
)
from .rsc1 import SECTION_CRITICAL, RSC1Section, pack_rsc1, parse_rsc1
from .sparse_entropy import decode_sparse_lapped, encode_sparse_lapped
from .stream_sections import unpack_conf


MAGIC = b"PTI1"
VERSION = 1
HEADER = struct.Struct("<4sBBHI")
MAX_PAYLOAD_BYTES = 512 << 20


@dataclass(frozen=True)
class PvqTruthDecodeResult:
    """Independently decoded PVE2 PCM and bounded stream parameters."""

    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    frame_count: int
    maximum_pulses_per_frame: int
    corrections_per_frame: int


@dataclass(frozen=True)
class PvqTruthEncodeResult:
    """Complete PVE2 stream, actual decode, and exact byte evidence."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _round_shift_signed(value: int, shift: int) -> int:
    """Round one signed integer symmetrically away from a half tie."""

    if shift == 0:
        return value
    magnitude = abs(value)
    rounded = (magnitude + (1 << (shift - 1))) >> shift
    return -rounded if value < 0 else rounded


def _correction_fields(
    analysis: LappedAnalysis,
    base: PvqEnvelopeDecodeResult,
    corrections_per_frame: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Select and quantize measured source-minus-PVQ transform error."""

    if not 1 <= corrections_per_frame <= analysis.half_window:
        raise ValueError("PVE2 correction count exceeds the transform window")
    edges = _band_edges(analysis.half_window, analysis.band_count)
    channels = analysis.samples.shape[1]
    scales = np.zeros(
        (channels, analysis.frame_count, analysis.band_count),
        dtype=np.uint8,
    )
    positions = np.empty(
        (channels, analysis.frame_count, corrections_per_frame),
        dtype=np.uint16,
    )
    values = np.empty(
        (channels, analysis.frame_count, corrections_per_frame),
        dtype=np.int8,
    )
    for channel in range(channels):
        for frame in range(analysis.frame_count):
            target = _source_coefficient_row(
                analysis,
                channel,
                frame,
                edges,
            )
            residual = target - base.coefficient_grid[channel, frame]
            if corrections_per_frame == analysis.half_window:
                selected = np.arange(analysis.half_window, dtype=np.int64)
            else:
                selected = np.argpartition(
                    np.abs(residual),
                    -corrections_per_frame,
                )[-corrections_per_frame:]
                selected.sort()
            positions[channel, frame] = selected.astype(np.uint16)

            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                local_mask = (selected >= start) & (selected < end)
                if not np.any(local_mask):
                    continue
                local_positions = selected[local_mask]
                local_residual = residual[local_positions]
                maximum = int(np.max(np.abs(local_residual)))
                shift = max(0, maximum.bit_length() - 7)
                while shift < 31 and any(
                    abs(_round_shift_signed(int(item), shift)) > 127
                    for item in local_residual
                ):
                    shift += 1
                if shift > 31:
                    raise ValueError("PVE2 correction scale exceeds the profile")
                scales[channel, frame, band] = shift
                quantized = [
                    _round_shift_signed(int(item), shift)
                    for item in local_residual
                ]
                if any(item < -128 or item > 127 for item in quantized):
                    raise RuntimeError("PVE2 correction quantizer overflow")
                frame_indices = np.flatnonzero(local_mask)
                values[channel, frame, frame_indices] = np.asarray(
                    quantized,
                    dtype=np.int8,
                )
    return scales, positions, values


def _materialize_corrections(
    scales: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    half_window: int,
    edges: tuple[int, ...],
) -> np.ndarray:
    """Expand bounded sparse TruthInnovation to full integer coefficients."""

    channels, frame_count, _ = scales.shape
    output = np.zeros((channels, frame_count, half_window), dtype=np.int64)
    for channel in range(channels):
        for frame in range(frame_count):
            frame_positions = positions[channel, frame]
            frame_values = values[channel, frame]
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                mask = (frame_positions >= start) & (frame_positions < end)
                output[channel, frame, frame_positions[mask]] = (
                    frame_values[mask].astype(np.int64)
                    << int(scales[channel, frame, band])
                )
    return output


def encode_pvq_truth_analysis(
    analysis: LappedAnalysis,
    *,
    maximum_pulses_per_frame: int,
    corrections_per_frame: int,
    minimum_active_power_ratio_q20: int = 10,
) -> PvqTruthEncodeResult:
    """Serialize and independently decode one complete prospective PVE2."""

    if not isinstance(analysis, LappedAnalysis) or not analysis.fixed_transform:
        raise TypeError("PVE2 requires one fixed-integer LappedAnalysis")
    base = encode_pvq_envelope_analysis(
        analysis,
        maximum_pulses_per_frame=maximum_pulses_per_frame,
        minimum_active_power_ratio_q20=minimum_active_power_ratio_q20,
    )
    base_decoded = decode_pvq_envelope_stream(base.payload)
    scales, positions, values = _correction_fields(
        analysis,
        base_decoded,
        corrections_per_frame,
    )
    sparse_payload = encode_sparse_lapped(
        scales,
        positions,
        values,
        half_window=analysis.half_window,
    )
    truth_body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            corrections_per_frame,
            len(sparse_payload),
        )
        + sparse_payload
    )
    base_info = parse_rsc1(base.payload)
    base_sections = {
        bytes(section.type_code): section for section in base_info.sections
    }
    payload = pack_rsc1(
        [
            RSC1Section("CONF", base_sections[b"CONF"].payload),
            RSC1Section("PVE1", base_sections[b"PVE1"].payload),
            RSC1Section("PTI1", truth_body),
        ],
        profile=0,
        level=6,
        timebase_hz=analysis.sample_rate,
    )
    decoded = decode_pvq_truth_stream(payload)
    quality = _quality_report(
        analysis.samples.reshape(-1),
        decoded.samples.reshape(-1),
    )
    report = {
        **quality,
        "status": (
            "R-108 prospective integer PVQ plus sparse TruthInnovation; "
            "non-normative"
        ),
        "format_profile": "prospective-PVE2-RSC1-level-6",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": analysis.sample_rate,
        "frame_count": int(analysis.samples.shape[0]),
        "channel_count": int(analysis.samples.shape[1]),
        "transform_frame_count": analysis.frame_count,
        "half_window": analysis.half_window,
        "band_count": analysis.band_count,
        "maximum_pulses_per_frame": maximum_pulses_per_frame,
        "minimum_active_power_ratio_q20": minimum_active_power_ratio_q20,
        "corrections_per_frame": corrections_per_frame,
        "base_section_bytes": len(base_sections[b"PVE1"].payload),
        "truth_section_bytes": len(truth_body),
        "sparse_truth_bytes": len(sparse_payload),
        "analysis_backend": analysis.analysis_backend,
        "reconstruction_backend": (
            "independent Python integer PVE2 decoder"
        ),
    }
    return PvqTruthEncodeResult(payload, decoded.samples, report)


def decode_pvq_truth_stream(payload: bytes) -> PvqTruthDecodeResult:
    """Validate, bound, and decode one prospective PVE2 stream."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 6):
        raise ValueError("unsupported PVE2 research profile")
    sections: dict[bytes, object] = {}
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code in (b"CONF", b"PVE1", b"PTI1"):
            if type_code in sections:
                raise ValueError("duplicate PVE2 section")
            sections[type_code] = section
        elif section.flags & SECTION_CRITICAL:
            raise ValueError("unknown critical PVE2 section")
    if set(sections) != {b"CONF", b"PVE1", b"PTI1"}:
        raise ValueError("incomplete PVE2 section set")
    if any(
        section.instance_id != 0 or section.start_tick != 0
        for section in sections.values()
    ):
        raise ValueError("non-canonical PVE2 section scope")
    config = unpack_conf(sections[b"CONF"].payload)
    base_payload = pack_rsc1(
        [
            RSC1Section("CONF", sections[b"CONF"].payload),
            RSC1Section("PVE1", sections[b"PVE1"].payload),
        ],
        profile=0,
        level=5,
        timebase_hz=info.timebase_hz,
    )
    base = decode_pvq_envelope_stream(base_payload)
    body = sections[b"PTI1"].payload
    if len(body) < HEADER.size or len(body) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid PVE2 TruthInnovation section size")
    magic, version, flags, corrections_per_frame, sparse_bytes = (
        HEADER.unpack_from(body)
    )
    if magic != MAGIC or version != VERSION or flags != 0:
        raise ValueError("unsupported PVE2 TruthInnovation stream")
    sparse_payload = body[HEADER.size:]
    if sparse_bytes != len(sparse_payload):
        raise ValueError("PVE2 TruthInnovation length mismatch")
    fields = decode_sparse_lapped(
        sparse_payload,
        half_window=base.half_window,
        expected_channels=config.output_channels,
        expected_frames=base.frame_count,
        expected_bands=base.band_count,
    )
    if fields.positions.shape[2] != corrections_per_frame:
        raise ValueError("PVE2 correction count mismatch")
    edges = _band_edges(base.half_window, base.band_count)
    correction_grid = _materialize_corrections(
        fields.scales,
        fields.positions,
        fields.values,
        half_window=base.half_window,
        edges=edges,
    )
    coefficient_grid = base.coefficient_grid + correction_grid
    zero_scales = np.zeros_like(base.scale_grid)
    reconstruction = _synthesize(
        coefficient_grid,
        zero_scales,
        sample_count=config.sample_count,
        half_window=base.half_window,
        edges=edges,
        fixed_transform=True,
    )
    return PvqTruthDecodeResult(
        info.timebase_hz,
        reconstruction,
        base.half_window,
        base.band_count,
        base.frame_count,
        base.maximum_pulses_per_frame,
        corrections_per_frame,
    )
