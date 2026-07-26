"""Independent-context LPF1 packet sequence for bounded streaming research."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .codec import _quality_report
from .lapped_oracle import (
    MAX_BANDS,
    MAX_CHANNELS,
    MAX_HALF_WINDOW,
    analyze_lapped_source,
    decode_lapped_stream,
    encode_lapped_analysis,
    encode_lapped_stream,
    pack_lapped_selected_payload,
    synthesize_lapped_selected_grid,
)
from .sparse_entropy import (
    compact_variable_sparse_lapped,
    compact_variable_sparse_lapped_size,
    decode_variable_sparse_lapped,
    expand_compact_variable_sparse_lapped,
)


MAGIC = b"LPS1"
TRANSFORM_MAGIC = b"LPS2"
CHAINED_MAGIC = b"LPS3"
COMPACT_MAGIC = b"LPS4"
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


@dataclass(frozen=True)
class LappedPacketView:
    """One authenticated independently decodable logical interval."""

    packet_index: int
    logical_start: int
    logical_count: int
    child_payload: bytes


@dataclass(frozen=True)
class LappedPacketStreamInfo:
    """Authenticated LPS1 envelope and packet index."""

    channels: int
    sample_rate: int
    total_frames: int
    half_window: int
    band_count: int
    packet_frames: int
    transform_boundary: bool
    chained_boundary: bool
    compact_transport: bool
    packets: tuple[LappedPacketView, ...]


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

    info = index_lapped_packet_stream(payload)
    output = np.empty((info.total_frames, info.channels), dtype=np.int16)
    for packet in info.packets:
        block = (
            decode_lapped_chained_packet_view(info, packet.packet_index)
            if info.chained_boundary
            else decode_lapped_packet_view(
                info,
                packet,
                native_decoder=native_decoder,
            )
        )
        output[
            packet.logical_start : packet.logical_start + packet.logical_count
        ] = block
    output.flags.writeable = False
    return LappedPacketDecodeResult(
        info.sample_rate,
        output,
        info.half_window,
        info.band_count,
        info.packet_frames,
        len(info.packets),
    )


def index_lapped_packet_stream(payload: bytes) -> LappedPacketStreamInfo:
    """Authenticate an LPS1 envelope and expose immutable packet records."""

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
    if (
        magic not in (
            MAGIC,
            TRANSFORM_MAGIC,
            CHAINED_MAGIC,
            COMPACT_MAGIC,
        )
        or version != VERSION
        or flags != 0
    ):
        raise ValueError("unsupported lapped packet envelope")
    _validate_header(
        channels,
        sample_rate,
        total_frames,
        half_window,
        band_count,
        packet_frames,
        packet_count,
    )
    cursor = HEADER.size + DIGEST_BYTES
    expected_start = 0
    packets: list[LappedPacketView] = []
    if magic == COMPACT_MAGIC:
        for packet_index in range(packet_count):
            logical_start = packet_index * packet_frames
            logical_count = min(
                packet_frames,
                total_frames - logical_start,
            )
            record_size = compact_variable_sparse_lapped_size(
                payload[cursor:]
            )
            record_end = cursor + record_size
            if len(payload) - record_end < 4:
                raise ValueError("truncated LPS4 packet CRC")
            record = payload[cursor:record_end]
            declared_crc = struct.unpack_from("<I", payload, record_end)[0]
            if zlib.crc32(record) & 0xFFFF_FFFF != declared_crc:
                raise ValueError("LPS4 packet CRC mismatch")
            final_packet = packet_index + 1 == packet_count
            owned_frames = (
                logical_count // half_window
                + (1 if final_packet else 0)
            )
            child_payload = expand_compact_variable_sparse_lapped(
                record,
                frame_count=owned_frames,
                channels=channels,
                band_count=band_count,
            )
            packets.append(
                LappedPacketView(
                    packet_index,
                    logical_start,
                    logical_count,
                    child_payload,
                )
            )
            expected_start += logical_count
            cursor = record_end + 4
    else:
        for packet_index in range(packet_count):
            if cursor + PACKET_HEADER.size > len(payload):
                raise ValueError("truncated lapped packet header")
            packet_start = cursor
            (
                logical_start,
                logical_count,
                packet_bytes,
            ) = PACKET_HEADER.unpack_from(payload, cursor)
            cursor += PACKET_HEADER.size
            if (
                logical_start != expected_start
                or logical_count == 0
                or logical_count > packet_frames
                or logical_start + logical_count > total_frames
                or packet_bytes == 0
                or packet_bytes + DIGEST_BYTES > len(payload) - cursor
            ):
                raise ValueError("invalid lapped packet index")
            child_payload = payload[cursor : cursor + packet_bytes]
            cursor += packet_bytes
            packet_digest = payload[cursor : cursor + DIGEST_BYTES]
            if (
                hashlib.sha256(payload[packet_start:cursor]).digest()
                != packet_digest
            ):
                raise ValueError("lapped packet integrity mismatch")
            cursor += DIGEST_BYTES
            packets.append(
                LappedPacketView(
                    packet_index,
                    logical_start,
                    logical_count,
                    child_payload,
                )
            )
            expected_start += logical_count
    if cursor != len(payload) or expected_start != total_frames:
        raise ValueError("trailing or incomplete LPS1 packet sequence")
    return LappedPacketStreamInfo(
        channels,
        sample_rate,
        total_frames,
        half_window,
        band_count,
        packet_frames,
        magic == TRANSFORM_MAGIC,
        magic in (CHAINED_MAGIC, COMPACT_MAGIC),
        magic == COMPACT_MAGIC,
        tuple(packets),
    )


def decode_lapped_packet_view(
    info: LappedPacketStreamInfo,
    packet: LappedPacketView,
    *,
    native_decoder=None,
) -> np.ndarray:
    """Decode one authenticated packet without using adjacent packet state."""

    if not isinstance(info, LappedPacketStreamInfo):
        raise TypeError("lapped packet stream info has an invalid type")
    if (
        not isinstance(packet, LappedPacketView)
        or packet.packet_index < 0
        or packet.packet_index >= len(info.packets)
        or info.packets[packet.packet_index] != packet
    ):
        raise ValueError("lapped packet view is not part of this envelope")
    if info.chained_boundary:
        raise ValueError("LPS3 decode requires the following boundary packet")
    if info.transform_boundary:
        frame_count = packet.logical_count // info.half_window + 1
        scales, coefficient_grid = _decode_selected_packet_fields(
            info,
            packet,
            frame_count,
        )
        return synthesize_lapped_selected_grid(
            scales,
            coefficient_grid,
            sample_count=packet.logical_count,
            half_window=info.half_window,
            fixed_transform=True,
        )

    if native_decoder is None:
        child = decode_lapped_stream(packet.child_payload)
        child_samples = child.samples
        child_sample_rate = child.sample_rate
        child_half_window = child.half_window
        child_band_count = child.band_count
    else:
        native = native_decoder.decode_lapped(packet.child_payload)
        child_samples = native.samples
        child_sample_rate = native.sample_rate
        child_half_window = native.requirements.half_window
        child_band_count = native.requirements.band_count
    expected_child_frames = packet.logical_count + 2 * info.half_window
    if (
        child_sample_rate != info.sample_rate
        or child_half_window != info.half_window
        or child_band_count != info.band_count
        or child_samples.shape != (expected_child_frames, info.channels)
    ):
        raise ValueError("LPS1 child stream differs from its envelope")
    logical = child_samples[
        info.half_window : info.half_window + packet.logical_count
    ]
    logical.flags.writeable = False
    return logical


def _decode_selected_packet_fields(
    info: LappedPacketStreamInfo,
    packet: LappedPacketView,
    expected_frames: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Decode one direct LSE2 packet into bounded selected fields."""

    fields = decode_variable_sparse_lapped(
        packet.child_payload,
        half_window=info.half_window,
        expected_channels=info.channels,
        expected_frames=expected_frames,
        expected_bands=info.band_count,
    )
    coefficient_grid = np.zeros(
        (info.channels, expected_frames, info.half_window),
        dtype=np.int8,
    )
    cursor = 0
    for channel in range(info.channels):
        for frame in range(expected_frames):
            count = int(fields.counts[channel, frame])
            end = cursor + count
            coefficient_grid[
                channel,
                frame,
                fields.positions[cursor:end],
            ] = fields.values[cursor:end]
            cursor = end
    if cursor != fields.positions.size:
        raise ValueError("lapped packet coefficient coverage mismatch")
    return fields.scales, coefficient_grid


def decode_lapped_chained_packet_view(
    info: LappedPacketStreamInfo,
    packet_index: int,
) -> np.ndarray:
    """Decode one LPS3 interval with one following boundary-frame lookahead."""

    if not info.chained_boundary:
        raise ValueError("packet sequence is not LPS3")
    if not 0 <= packet_index < len(info.packets):
        raise ValueError("LPS3 packet index exceeds the sequence")
    packet = info.packets[packet_index]
    final_packet = packet_index + 1 == len(info.packets)
    owned_frames = (
        packet.logical_count // info.half_window
        + (1 if final_packet else 0)
    )
    scales, coefficients = _decode_selected_packet_fields(
        info,
        packet,
        owned_frames,
    )
    if not final_packet:
        next_scales, next_coefficients = _decode_selected_packet_fields(
            info,
            info.packets[packet_index + 1],
            (
                info.packets[packet_index + 1].logical_count
                // info.half_window
                + (
                    1
                    if packet_index + 2 == len(info.packets)
                    else 0
                )
            ),
        )
        scales = np.concatenate((scales, next_scales[:, :1]), axis=1)
        coefficients = np.concatenate(
            (coefficients, next_coefficients[:, :1]),
            axis=1,
        )
    return synthesize_lapped_selected_grid(
        scales,
        coefficients,
        sample_count=packet.logical_count,
        half_window=info.half_window,
        fixed_transform=True,
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


def encode_lapped_transform_packet_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    packet_frames: int,
    half_window: int = 512,
    band_count: int = 24,
    native_core=None,
) -> LappedPacketEncodeResult:
    """Packetize one globally selected grid with one shared boundary frame."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
    ):
        raise TypeError("LPS2 input must be frame-major PCM16")
    source = np.array(source_view, dtype=np.int16, copy=True)
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
    analysis = analyze_lapped_source(
        source,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_core,
    )
    monolithic = encode_lapped_analysis(
        analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        native_decoder=native_core,
    )
    header = HEADER.pack(
        TRANSFORM_MAGIC,
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
    for logical_start in range(0, source.shape[0], packet_frames):
        logical_count = min(
            packet_frames,
            source.shape[0] - logical_start,
        )
        first_transform = logical_start // half_window
        child_transform_count = logical_count // half_window + 1
        transform_end = first_transform + child_transform_count
        child_payload = pack_lapped_selected_payload(
            monolithic.selected_scales[
                :, first_transform:transform_end
            ],
            monolithic.selected_coefficients[
                :, first_transform:transform_end
            ],
            half_window=half_window,
        )
        packet_header = PACKET_HEADER.pack(
            logical_start,
            logical_count,
            len(child_payload),
        )
        body += packet_header
        body += child_payload
        body += hashlib.sha256(packet_header + child_payload).digest()
        child_bytes.append(len(child_payload))

    payload = bytes(body)
    decoded = decode_lapped_packet_stream(
        payload,
        native_decoder=native_core,
    )
    if not np.array_equal(decoded.samples, monolithic.reconstruction):
        raise RuntimeError("LPS2 packet reconstruction differs from LPF1")
    report = {
        "status": "transform-boundary LPF1 packet research stream",
        "format_profile": "prospective-LPS2",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": sample_rate,
        "frame_count": int(source.shape[0]),
        "channel_count": int(source.shape[1]),
        "half_window": half_window,
        "band_count": band_count,
        "coefficients_per_frame": coefficients_per_frame,
        "density_backend": "adaptive-global",
        "packet_frames": packet_frames,
        "packet_count": packet_count,
        "packet_payload_bytes": child_bytes,
        "duplicated_boundary_transform_frames": max(0, packet_count - 1),
        "monolithic_stream_bytes": len(monolithic.payload),
        "packet_byte_overhead_fraction": (
            len(payload) / len(monolithic.payload) - 1.0
        ),
        "exact_monolithic_reconstruction": True,
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


def encode_lapped_chained_packet_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    packet_frames: int,
    half_window: int = 512,
    band_count: int = 24,
    native_core=None,
) -> LappedPacketEncodeResult:
    """Assign every selected transform frame to exactly one LPS3 packet."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
    ):
        raise TypeError("LPS3 input must be frame-major PCM16")
    source = np.array(source_view, dtype=np.int16, copy=True)
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
    analysis = analyze_lapped_source(
        source,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_core,
    )
    monolithic = encode_lapped_analysis(
        analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        native_decoder=native_core,
    )
    header = HEADER.pack(
        CHAINED_MAGIC,
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
    logical_starts = list(range(0, source.shape[0], packet_frames))
    for packet_index, logical_start in enumerate(logical_starts):
        logical_count = min(
            packet_frames,
            source.shape[0] - logical_start,
        )
        final_packet = packet_index + 1 == packet_count
        first_transform = logical_start // half_window
        owned_frames = (
            logical_count // half_window
            + (1 if final_packet else 0)
        )
        transform_end = first_transform + owned_frames
        child_payload = pack_lapped_selected_payload(
            monolithic.selected_scales[
                :, first_transform:transform_end
            ],
            monolithic.selected_coefficients[
                :, first_transform:transform_end
            ],
            half_window=half_window,
        )
        packet_header = PACKET_HEADER.pack(
            logical_start,
            logical_count,
            len(child_payload),
        )
        body += packet_header
        body += child_payload
        body += hashlib.sha256(packet_header + child_payload).digest()
        child_bytes.append(len(child_payload))

    payload = bytes(body)
    decoded = decode_lapped_packet_stream(payload)
    if not np.array_equal(decoded.samples, monolithic.reconstruction):
        raise RuntimeError("LPS3 packet reconstruction differs from LPF1")
    report = {
        "status": "single-owner transform packet research stream",
        "format_profile": "prospective-LPS3",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": sample_rate,
        "frame_count": int(source.shape[0]),
        "channel_count": int(source.shape[1]),
        "half_window": half_window,
        "band_count": band_count,
        "coefficients_per_frame": coefficients_per_frame,
        "density_backend": "adaptive-global",
        "packet_frames": packet_frames,
        "packet_count": packet_count,
        "packet_payload_bytes": child_bytes,
        "duplicated_boundary_transform_frames": 0,
        "lookahead_frames": half_window,
        "maximum_loss_extension_frames": half_window,
        "monolithic_stream_bytes": len(monolithic.payload),
        "packet_byte_overhead_fraction": (
            len(payload) / len(monolithic.payload) - 1.0
        ),
        "exact_monolithic_reconstruction": True,
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


def encode_lapped_compact_packet_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    packet_frames: int,
    half_window: int = 512,
    band_count: int = 24,
    native_core=None,
) -> LappedPacketEncodeResult:
    """Pack single-owner fields without repeated shape or SHA metadata."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
    ):
        raise TypeError("LPS4 input must be frame-major PCM16")
    source = np.array(source_view, dtype=np.int16, copy=True)
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
    analysis = analyze_lapped_source(
        source,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_core,
    )
    monolithic = encode_lapped_analysis(
        analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        native_decoder=native_core,
    )
    header = HEADER.pack(
        COMPACT_MAGIC,
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
    record_bytes = []
    logical_starts = list(range(0, source.shape[0], packet_frames))
    for packet_index, logical_start in enumerate(logical_starts):
        logical_count = min(
            packet_frames,
            source.shape[0] - logical_start,
        )
        final_packet = packet_index + 1 == packet_count
        first_transform = logical_start // half_window
        owned_frames = (
            logical_count // half_window
            + (1 if final_packet else 0)
        )
        transform_end = first_transform + owned_frames
        full_lse2 = pack_lapped_selected_payload(
            monolithic.selected_scales[
                :, first_transform:transform_end
            ],
            monolithic.selected_coefficients[
                :, first_transform:transform_end
            ],
            half_window=half_window,
        )
        record = compact_variable_sparse_lapped(full_lse2)
        body += record
        body += struct.pack("<I", zlib.crc32(record) & 0xFFFF_FFFF)
        record_bytes.append(len(record) + 4)

    payload = bytes(body)
    decoded = decode_lapped_packet_stream(payload)
    if not np.array_equal(decoded.samples, monolithic.reconstruction):
        raise RuntimeError("LPS4 packet reconstruction differs from LPF1")
    report = {
        "status": "compact transport-framed transform packet research stream",
        "format_profile": "prospective-LPS4",
        "integrity": (
            "SHA-256 sequence header plus CRC-32 packet records; "
            "cryptographic packet authentication is a transport requirement"
        ),
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": sample_rate,
        "frame_count": int(source.shape[0]),
        "channel_count": int(source.shape[1]),
        "half_window": half_window,
        "band_count": band_count,
        "coefficients_per_frame": coefficients_per_frame,
        "density_backend": "adaptive-global",
        "packet_frames": packet_frames,
        "packet_count": packet_count,
        "packet_record_bytes": record_bytes,
        "duplicated_boundary_transform_frames": 0,
        "lookahead_frames": half_window,
        "maximum_loss_extension_frames": half_window,
        "monolithic_stream_bytes": len(monolithic.payload),
        "packet_byte_overhead_fraction": (
            len(payload) / len(monolithic.payload) - 1.0
        ),
        "exact_monolithic_reconstruction": True,
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
