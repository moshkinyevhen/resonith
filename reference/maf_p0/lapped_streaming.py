"""Independent-context LPF1 packet sequence for bounded streaming research."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .codec import _quality_report
from .lapped_oracle import (
    MAX_BANDS,
    MAX_CHANNELS,
    MAX_HALF_WINDOW,
    decode_lapped_stream,
    encode_lapped_stream,
)


MAGIC = b"LPS1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIIHHII")
PACKET_HEADER = struct.Struct("<III")
DIGEST_BYTES = 32
MAX_STREAM_BYTES = 512 << 20
MAX_PACKET_COUNT = 1 << 20


@dataclass(frozen=True)
class LappedPacketDecodeResult:
    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    packet_frames: int
    packet_count: int


@dataclass(frozen=True)
class LappedPacketEncodeResult:
    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _validate_header(
    channels: int,
    sample_rate: int,
    total_frames: int,
    half_window: int,
    band_count: int,
    packet_frames: int,
    packet_count: int,
) -> None:
    if (
        not 1 <= channels <= MAX_CHANNELS
        or sample_rate <= 0
        or total_frames <= 0
        or half_window < 32
        or half_window > MAX_HALF_WINDOW
        or half_window & (half_window - 1)
        or not 1 <= band_count <= min(MAX_BANDS, half_window)
        or packet_frames < half_window
        or packet_frames % half_window
        or not 1 <= packet_count <= MAX_PACKET_COUNT
    ):
        raise ValueError("LPS1 header exceeds the research profile")
    expected_packets = (total_frames + packet_frames - 1) // packet_frames
    if packet_count != expected_packets:
        raise ValueError("LPS1 packet count is non-canonical")


def decode_lapped_packet_stream(
    payload: bytes,
    *,
    native_decoder=None,
) -> LappedPacketDecodeResult:
    """Decode independently verifiable context packets to contiguous PCM."""

    if (
        not isinstance(payload, bytes)
        or len(payload) < HEADER.size + DIGEST_BYTES
        or len(payload) > MAX_STREAM_BYTES
    ):
        raise ValueError("invalid LPS1 payload")
    header_bytes = payload[:HEADER.size]
    if (
        hashlib.sha256(header_bytes).digest()
        != payload[HEADER.size : HEADER.size + DIGEST_BYTES]
    ):
        raise ValueError("LPS1 header integrity mismatch")
    (
        magic,
        version,
        flags,
        channels,
        sample_rate,
        total_frames,
        half_window,
        band_count,
        packet_frames,
        packet_count,
    ) = HEADER.unpack(header_bytes)
    if magic != MAGIC or version != VERSION or flags != 0:
        raise ValueError("unsupported LPS1 envelope")
    _validate_header(
        channels,
        sample_rate,
        total_frames,
        half_window,
        band_count,
        packet_frames,
        packet_count,
    )
    output = np.empty((total_frames, channels), dtype=np.int16)
    cursor = HEADER.size + DIGEST_BYTES
    expected_start = 0
    for packet_index in range(packet_count):
        if cursor + PACKET_HEADER.size > len(payload):
            raise ValueError("truncated LPS1 packet header")
        packet_start = cursor
        logical_start, logical_count, packet_bytes = PACKET_HEADER.unpack_from(
            payload,
            cursor,
        )
        cursor += PACKET_HEADER.size
        if (
            logical_start != expected_start
            or logical_count == 0
            or logical_count > packet_frames
            or logical_start + logical_count > total_frames
            or packet_bytes == 0
            or packet_bytes + DIGEST_BYTES > len(payload) - cursor
        ):
            raise ValueError("invalid LPS1 packet index")
        child_payload = payload[cursor : cursor + packet_bytes]
        cursor += packet_bytes
        packet_digest = payload[cursor : cursor + DIGEST_BYTES]
        if (
            hashlib.sha256(payload[packet_start:cursor]).digest()
            != packet_digest
        ):
            raise ValueError("LPS1 packet integrity mismatch")
        cursor += DIGEST_BYTES
        if native_decoder is None:
            child = decode_lapped_stream(child_payload)
            child_samples = child.samples
            child_sample_rate = child.sample_rate
            child_half_window = child.half_window
            child_band_count = child.band_count
        else:
            native = native_decoder.decode_lapped(child_payload)
            child_samples = native.samples
            child_sample_rate = native.sample_rate
            child_half_window = native.requirements.half_window
            child_band_count = native.requirements.band_count
        if (
            child_sample_rate != sample_rate
            or child_half_window != half_window
            or child_band_count != band_count
            or child_samples.shape != (
                logical_count + 2 * half_window,
                channels,
            )
        ):
            raise ValueError("LPS1 child stream differs from its envelope")
        output[logical_start : logical_start + logical_count] = child_samples[
            half_window : half_window + logical_count
        ]
        expected_start += logical_count
    if cursor != len(payload) or expected_start != total_frames:
        raise ValueError("trailing or incomplete LPS1 packet sequence")
    output.flags.writeable = False
    return LappedPacketDecodeResult(
        sample_rate,
        output,
        half_window,
        band_count,
        packet_frames,
        packet_count,
    )


def encode_lapped_packet_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    packet_frames: int,
    half_window: int = 512,
    band_count: int = 24,
    density_backend: str = "adaptive",
    native_core=None,
) -> LappedPacketEncodeResult:
    """Encode bounded independent packets with one-window source context."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
    ):
        raise TypeError("LPS1 input must be frame-major PCM16")
    source = np.array(source_view, dtype=np.int16, copy=True)
    if packet_frames <= 0:
        raise ValueError("LPS1 packet size must be positive")
    packet_count = (
        source.shape[0] + packet_frames - 1
    ) // packet_frames
    _validate_header(
        source.shape[1],
        sample_rate,
        source.shape[0],
        half_window,
        band_count,
        packet_frames,
        packet_count,
    )
    header = HEADER.pack(
        MAGIC,
        VERSION,
        0,
        source.shape[1],
        sample_rate,
        source.shape[0],
        half_window,
        band_count,
        packet_frames,
        packet_count,
    )
    body = bytearray(header + hashlib.sha256(header).digest())
    child_bytes = []
    context_frames = 0
    for logical_start in range(0, source.shape[0], packet_frames):
        logical_count = min(
            packet_frames,
            source.shape[0] - logical_start,
        )
        contextual = np.zeros(
            (logical_count + 2 * half_window, source.shape[1]),
            dtype=np.int16,
        )
        source_start = max(0, logical_start - half_window)
        source_end = min(
            source.shape[0],
            logical_start + logical_count + half_window,
        )
        destination_start = (
            source_start - logical_start + half_window
        )
        contextual[
            destination_start : destination_start + source_end - source_start
        ] = source[source_start:source_end]
        child = encode_lapped_stream(
            contextual,
            sample_rate,
            coefficients_per_frame=coefficients_per_frame,
            half_window=half_window,
            band_count=band_count,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend=density_backend,
            native_analyzer=native_core,
            native_decoder=native_core,
        )
        packet_header = PACKET_HEADER.pack(
            logical_start,
            logical_count,
            len(child.payload),
        )
        body += packet_header
        body += child.payload
        body += hashlib.sha256(packet_header + child.payload).digest()
        child_bytes.append(len(child.payload))
        context_frames += contextual.shape[0] - logical_count
    payload = bytes(body)
    decoded = decode_lapped_packet_stream(
        payload,
        native_decoder=native_core,
    )
    report = {
        "status": "independent-context LPF1 packet research stream",
        "format_profile": "prospective-LPS1",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": sample_rate,
        "frame_count": int(source.shape[0]),
        "channel_count": int(source.shape[1]),
        "half_window": half_window,
        "band_count": band_count,
        "coefficients_per_frame": coefficients_per_frame,
        "density_backend": density_backend,
        "packet_frames": packet_frames,
        "packet_count": packet_count,
        "packet_payload_bytes": child_bytes,
        "context_frames_transmitted": context_frames,
        "maximum_child_pcm_frames": min(
            packet_frames,
            source.shape[0],
        )
        + 2 * half_window,
        **_quality_report(
            source.reshape(-1),
            decoded.samples.reshape(-1),
        ),
    }
    return LappedPacketEncodeResult(
        payload,
        decoded.samples,
        report,
    )
