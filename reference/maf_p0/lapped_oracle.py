"""R-057 lapped band-adaptive Innovation research codec."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import struct
import zlib

import numpy as np

from .codec import _quality_report
from .rsc1 import SECTION_CRITICAL, RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAGIC = b"LPI1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIIHHII")
MAX_CHANNELS = 8
MAX_HALF_WINDOW = 1024
MAX_BANDS = 64
MAX_RAW_BYTES = 512 << 20


@dataclass(frozen=True)
class LappedDecodeResult:
    """Independent research decode and declared transform parameters."""

    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    frame_count: int


@dataclass(frozen=True)
class LappedEncodeResult:
    """Complete research stream, reconstruction, and exact byte evidence."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


@lru_cache(maxsize=8)
def _mdct_tables(half_window: int) -> tuple[np.ndarray, np.ndarray]:
    """Build immutable perfect-reconstruction sine-window MDCT tables."""

    if (
        half_window < 32
        or half_window > MAX_HALF_WINDOW
        or half_window & (half_window - 1)
    ):
        raise ValueError("lapped half-window must be a power of two, 32-1024")
    sample = np.arange(2 * half_window, dtype=np.float64)
    coefficient = np.arange(half_window, dtype=np.float64)
    window = np.sin(
        np.pi / (2.0 * half_window) * (sample + 0.5)
    )
    matrix = np.cos(
        np.pi
        / half_window
        * np.outer(
            coefficient + 0.5,
            sample + 0.5 + half_window / 2.0,
        )
    )
    window.flags.writeable = False
    matrix.flags.writeable = False
    return window, matrix


@lru_cache(maxsize=32)
def _band_edges(half_window: int, band_count: int) -> tuple[int, ...]:
    """Create deterministic low-frequency-dense coefficient partitions."""

    if not 1 <= band_count <= min(MAX_BANDS, half_window):
        raise ValueError("lapped band count exceeds the profile bound")
    raw = np.rint(
        np.linspace(0.0, np.sqrt(half_window), band_count + 1) ** 2
    ).astype(np.int64)
    raw[0] = 0
    raw[-1] = half_window
    edges = [0]
    for value in raw[1:-1]:
        candidate = int(value)
        if candidate > edges[-1] and candidate < half_window:
            edges.append(candidate)
    edges.append(half_window)
    if len(edges) - 1 != band_count:
        raise ValueError("lapped band count is too dense for the window")
    return tuple(edges)


def _decompress_exact(compressed: bytes, expected_bytes: int) -> bytes:
    """Bound decompression before accepting any research coefficient grid."""

    if not 0 <= expected_bytes <= MAX_RAW_BYTES:
        raise ValueError("lapped coefficient grid exceeds the byte bound")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, expected_bytes + 1)
    if len(raw) != expected_bytes or decoder.unconsumed_tail:
        raise ValueError("lapped coefficient grid length mismatch")
    if decoder.unused_data or not decoder.eof:
        raise ValueError("non-canonical lapped deflate stream")
    if decoder.flush():
        raise ValueError("trailing lapped deflate output")
    return raw


def _synthesize(
    coefficient_grid: np.ndarray,
    scale_grid: np.ndarray,
    *,
    sample_count: int,
    half_window: int,
    edges: tuple[int, ...],
) -> np.ndarray:
    """Synthesize frame-major PCM through overlap-add and final rounding."""

    channels, frame_count, coefficient_count = coefficient_grid.shape
    if coefficient_count != half_window:
        raise ValueError("lapped coefficient grid shape mismatch")
    window, matrix = _mdct_tables(half_window)
    padded = np.zeros(
        (sample_count + 2 * half_window, channels),
        dtype=np.float64,
    )
    inverse_scale = 2.0 / half_window
    for channel in range(channels):
        for frame in range(frame_count):
            coefficients = np.empty(half_window, dtype=np.float64)
            for band, (start, end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                coefficients[start:end] = (
                    coefficient_grid[channel, frame, start:end].astype(
                        np.float64
                    )
                    * float(1 << int(scale_grid[channel, frame, band]))
                )
            start = frame * half_window
            padded[start : start + 2 * half_window, channel] += (
                inverse_scale * (coefficients @ matrix) * window
            )
    reconstruction = np.clip(
        np.rint(padded[half_window : half_window + sample_count]),
        -32768,
        32767,
    ).astype(np.int16)
    reconstruction.flags.writeable = False
    return reconstruction


def decode_lapped_stream(payload: bytes) -> LappedDecodeResult:
    """Independently validate and decode one prospective LPF1 RSC1 stream."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 5):
        raise ValueError("unsupported lapped research profile")
    config_sections = []
    lapped_sections = []
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code == b"CONF":
            config_sections.append(section)
        elif type_code == b"LPF1":
            lapped_sections.append(section)
        elif section.flags & SECTION_CRITICAL:
            raise ValueError("unknown critical lapped research section")
    if (
        len(config_sections) != 1
        or len(lapped_sections) != 1
        or config_sections[0].instance_id != 0
        or lapped_sections[0].instance_id != 0
        or config_sections[0].start_tick != 0
        or lapped_sections[0].start_tick != 0
    ):
        raise ValueError("non-canonical lapped research sections")
    config = unpack_conf(config_sections[0].payload)
    body = lapped_sections[0].payload
    if len(body) < HEADER.size:
        raise ValueError("truncated lapped research header")
    (
        magic,
        version,
        flags,
        channels,
        sample_rate,
        sample_count,
        half_window,
        declared_band_count,
        frame_count,
        raw_bytes,
    ) = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported lapped research stream")
    if flags != 0 or not 1 <= channels <= MAX_CHANNELS:
        raise ValueError("lapped research header exceeds the profile")
    edges = _band_edges(half_window, declared_band_count)
    band_count = len(edges) - 1
    expected_frames = sample_count // half_window + 1
    expected_raw = (
        channels
        * frame_count
        * (band_count + half_window)
    )
    if (
        sample_rate != info.timebase_hz
        or sample_count != config.sample_count
        or channels != config.output_channels
        or config.innovation_step != 1
        or frame_count != expected_frames
        or raw_bytes != expected_raw
    ):
        raise ValueError("lapped research cross-section mismatch")
    raw = _decompress_exact(body[HEADER.size:], raw_bytes)
    frame_bytes = band_count + half_window
    scale_grid = np.empty(
        (channels, frame_count, band_count),
        dtype=np.uint8,
    )
    coefficient_grid = np.empty(
        (channels, frame_count, half_window),
        dtype=np.int8,
    )
    cursor = 0
    for channel in range(channels):
        for frame in range(frame_count):
            scales_end = cursor + band_count
            frame_end = cursor + frame_bytes
            scale_grid[channel, frame] = np.frombuffer(
                raw[cursor:scales_end],
                dtype=np.uint8,
            )
            coefficient_grid[channel, frame] = np.frombuffer(
                raw[scales_end:frame_end],
                dtype=np.int8,
            )
            cursor = frame_end
    if cursor != len(raw) or np.any(scale_grid > 31):
        raise ValueError("invalid lapped scale grid")
    reconstruction = _synthesize(
        coefficient_grid,
        scale_grid,
        sample_count=sample_count,
        half_window=half_window,
        edges=edges,
    )
    return LappedDecodeResult(
        sample_rate,
        reconstruction,
        half_window,
        band_count,
        frame_count,
    )


def encode_lapped_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    half_window: int = 512,
    band_count: int = 24,
) -> LappedEncodeResult:
    """Encode top-energy band-scaled MDCT coefficients with exact bytes."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= MAX_CHANNELS
    ):
        raise TypeError("lapped input must be frame-major 1-8 channel PCM16")
    if sample_rate <= 0:
        raise ValueError("lapped sample rate must be positive")
    if not 1 <= coefficients_per_frame <= half_window:
        raise ValueError("lapped coefficient budget exceeds the window")
    edges = _band_edges(half_window, band_count)
    window, matrix = _mdct_tables(half_window)
    frame_count = source.shape[0] // half_window + 1
    padded = np.pad(
        source.astype(np.float64),
        ((half_window, half_window), (0, 0)),
    )
    scales = np.empty(
        (source.shape[1], frame_count, band_count),
        dtype=np.uint8,
    )
    coefficients = np.zeros(
        (source.shape[1], frame_count, half_window),
        dtype=np.int8,
    )
    nonzero_count = 0
    for channel in range(source.shape[1]):
        for frame in range(frame_count):
            start = frame * half_window
            spectrum = (
                padded[start : start + 2 * half_window, channel]
                * window
            ) @ matrix.T
            quantized = np.empty(half_window, dtype=np.int64)
            for band, (band_start, band_end) in enumerate(
                zip(edges[:-1], edges[1:], strict=True)
            ):
                maximum = max(
                    1.0,
                    float(np.max(np.abs(spectrum[band_start:band_end]))),
                )
                step = max(1.0, maximum / 127.0)
                exponent = min(
                    31,
                    max(0, int(np.ceil(np.log2(step)))),
                )
                scales[channel, frame, band] = exponent
                quantized[band_start:band_end] = np.rint(
                    spectrum[band_start:band_end] / float(1 << exponent)
                ).astype(np.int64)
            selected = np.argpartition(
                np.abs(spectrum),
                -coefficients_per_frame,
            )[-coefficients_per_frame:]
            selected_values = np.clip(
                quantized[selected],
                -127,
                127,
            ).astype(np.int8)
            coefficients[channel, frame, selected] = selected_values
            nonzero_count += int(np.count_nonzero(selected_values))

    raw = bytearray()
    for channel in range(source.shape[1]):
        for frame in range(frame_count):
            raw += scales[channel, frame].tobytes()
            raw += coefficients[channel, frame].tobytes()
    compressed = zlib.compress(bytes(raw), level=9)
    inner = (
        HEADER.pack(
            MAGIC,
            VERSION,
            0,
            source.shape[1],
            sample_rate,
            source.shape[0],
            half_window,
            band_count,
            frame_count,
            len(raw),
        )
        + compressed
    )
    payload = pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(
                    StreamConfig(
                        source.shape[0],
                        1,
                        source.shape[1],
                    )
                ),
            ),
            RSC1Section("LPF1", inner),
        ],
        profile=0,
        level=5,
        timebase_hz=sample_rate,
    )
    decoded = decode_lapped_stream(payload)
    report = {
        "status": "research lapped Innovation; syntax is non-normative",
        "format_profile": "prospective-LPF1-RSC1-level-5",
        "entropy_proxy": "zlib level 9; must be replaced before promotion",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_rate": sample_rate,
        "frame_count": int(source.shape[0]),
        "channel_count": int(source.shape[1]),
        "half_window": half_window,
        "overlap_percent": 50,
        "transform_frame_count": frame_count,
        "band_count": band_count,
        "coefficients_per_frame": coefficients_per_frame,
        "nonzero_coefficients": nonzero_count,
        "raw_grid_bytes": len(raw),
        "compressed_grid_bytes": len(compressed),
        **_quality_report(
            source.reshape(-1),
            decoded.samples.reshape(-1),
        ),
    }
    return LappedEncodeResult(payload, decoded.samples, report)
