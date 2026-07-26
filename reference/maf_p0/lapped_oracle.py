"""R-057 lapped band-adaptive Innovation research codec."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import struct
import zlib

import numpy as np

from .codec import _quality_report
from .fixed_lapped import (
    analyze_fixed_lapped,
    fixed_lapped_tables,
    round_shift_signed,
    synthesize_fixed_lapped_frame,
    synthesis_output_shift,
)
from .rsc1 import SECTION_CRITICAL, RSC1Section, pack_rsc1, parse_rsc1
from .sparse_entropy import (
    decode_sparse_lapped,
    decode_variable_sparse_lapped,
    encode_sparse_lapped,
    encode_variable_sparse_lapped,
)
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAGIC = b"LPI1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIIHHII")
MAX_CHANNELS = 8
MAX_HALF_WINDOW = 1024
MAX_BANDS = 64
MAX_RAW_BYTES = 512 << 20
ENTROPY_ZLIB = 0
ENTROPY_BOUNDED_SPARSE = 1
FLAG_ENTROPY_MASK = 0x01
FLAG_FIXED_TRANSFORM = 0x02
FLAG_VARIABLE_DENSITY = 0x04


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
    selected_scales: np.ndarray
    selected_coefficients: np.ndarray


@dataclass(frozen=True)
class LappedAnalysis:
    """Reusable transform analysis for exact-byte density/RDO searches."""

    sample_rate: int
    samples: np.ndarray
    half_window: int
    band_count: int
    frame_count: int
    fixed_transform: bool
    fixed_table_sha256: str | None
    analysis_backend: str
    scales: np.ndarray
    quantized_grid: np.ndarray
    score_grid: np.ndarray


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
    denominator = band_count * band_count
    raw = []
    for index in range(band_count + 1):
        quotient, remainder = divmod(
            index * index * half_window,
            denominator,
        )
        if (
            2 * remainder > denominator
            or (2 * remainder == denominator and quotient & 1)
        ):
            quotient += 1
        raw.append(quotient)
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
    fixed_transform: bool,
) -> np.ndarray:
    """Synthesize frame-major PCM through overlap-add and final rounding."""

    channels, frame_count, coefficient_count = coefficient_grid.shape
    if coefficient_count != half_window:
        raise ValueError("lapped coefficient grid shape mismatch")
    if fixed_transform:
        padded_integer = np.zeros(
            (sample_count + 2 * half_window, channels),
            dtype=np.int64,
        )
        for channel in range(channels):
            for frame in range(frame_count):
                coefficients = np.empty(half_window, dtype=np.int64)
                for band, (start, end) in enumerate(
                    zip(edges[:-1], edges[1:], strict=True)
                ):
                    coefficients[start:end] = (
                        coefficient_grid[channel, frame, start:end].astype(
                            np.int64
                        )
                        * (1 << int(scale_grid[channel, frame, band]))
                    )
                start = frame * half_window
                padded_integer[
                    start : start + 2 * half_window,
                    channel,
                ] += synthesize_fixed_lapped_frame(
                    coefficients,
                    half_window,
                )
        rounded = round_shift_signed(
            padded_integer[half_window : half_window + sample_count],
            synthesis_output_shift(half_window),
        )
        reconstruction = np.clip(
            rounded,
            -32768,
            32767,
        ).astype(np.int16)
    else:
        window, matrix = _mdct_tables(half_window)
        padded_float = np.zeros(
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
                padded_float[
                    start : start + 2 * half_window,
                    channel,
                ] += inverse_scale * (coefficients @ matrix) * window
        reconstruction = np.clip(
            np.rint(padded_float[half_window : half_window + sample_count]),
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
    if flags & ~(
        FLAG_ENTROPY_MASK
        | FLAG_FIXED_TRANSFORM
        | FLAG_VARIABLE_DENSITY
    ):
        raise ValueError("unsupported lapped entropy backend")
    entropy_backend = flags & FLAG_ENTROPY_MASK
    fixed_transform = bool(flags & FLAG_FIXED_TRANSFORM)
    variable_density = bool(flags & FLAG_VARIABLE_DENSITY)
    if not 1 <= channels <= MAX_CHANNELS:
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
    ):
        raise ValueError("lapped research cross-section mismatch")
    if entropy_backend == ENTROPY_ZLIB:
        if variable_density:
            raise ValueError("zlib comparator does not carry variable density")
        if raw_bytes != expected_raw:
            raise ValueError("lapped zlib grid length mismatch")
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
    else:
        sparse_payload = body[HEADER.size:]
        if raw_bytes != len(sparse_payload):
            raise ValueError("lapped sparse payload length mismatch")
        coefficient_grid = np.zeros(
            (channels, frame_count, half_window),
            dtype=np.int8,
        )
        if variable_density:
            sparse_variable = decode_variable_sparse_lapped(
                sparse_payload,
                half_window=half_window,
                expected_channels=channels,
                expected_frames=frame_count,
                expected_bands=band_count,
            )
            scale_grid = sparse_variable.scales
            cursor = 0
            for channel in range(channels):
                for frame in range(frame_count):
                    count = int(sparse_variable.counts[channel, frame])
                    end = cursor + count
                    coefficient_grid[
                        channel,
                        frame,
                        sparse_variable.positions[cursor:end],
                    ] = sparse_variable.values[cursor:end]
                    cursor = end
            if cursor != sparse_variable.positions.size:
                raise ValueError("variable sparse coefficient coverage mismatch")
        else:
            sparse = decode_sparse_lapped(
                sparse_payload,
                half_window=half_window,
                expected_channels=channels,
                expected_frames=frame_count,
                expected_bands=band_count,
            )
            scale_grid = sparse.scales
            channel_index = np.arange(channels)[:, None, None]
            frame_index = np.arange(frame_count)[None, :, None]
            coefficient_grid[
                channel_index,
                frame_index,
                sparse.positions,
            ] = sparse.values
    reconstruction = _synthesize(
        coefficient_grid,
        scale_grid,
        sample_count=sample_count,
        half_window=half_window,
        edges=edges,
        fixed_transform=fixed_transform,
    )
    return LappedDecodeResult(
        sample_rate,
        reconstruction,
        half_window,
        band_count,
        frame_count,
    )


def analyze_lapped_source(
    samples: np.ndarray,
    sample_rate: int,
    *,
    half_window: int = 512,
    band_count: int = 24,
    transform_backend: str = "fixed",
    native_analyzer=None,
) -> LappedAnalysis:
    """Transform and quantize source PCM once for many exact-byte trials."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
        or not 1 <= source_view.shape[1] <= MAX_CHANNELS
    ):
        raise TypeError("lapped input must be frame-major 1-8 channel PCM16")
    if sample_rate <= 0:
        raise ValueError("lapped sample rate must be positive")
    source = np.array(source_view, dtype=np.int16, copy=True)
    edges = _band_edges(half_window, band_count)
    if transform_backend == "float":
        window, matrix = _mdct_tables(half_window)
        table_sha256 = None
        fixed_transform = False
    elif transform_backend == "fixed":
        _window, _matrix, table_sha256 = fixed_lapped_tables(half_window)
        fixed_transform = True
    else:
        raise ValueError("unknown lapped transform backend")
    frame_count = source.shape[0] // half_window + 1
    if native_analyzer is not None:
        if not fixed_transform:
            raise ValueError("native analysis requires the fixed transform")
        native = native_analyzer.analyze_lapped(
            source,
            half_window=half_window,
            band_count=band_count,
        )
        if native.transform_frame_count != frame_count:
            raise RuntimeError("native lapped analysis frame count differs")
        scales = np.array(native.scales, dtype=np.uint8, copy=True)
        quantized_grid = np.array(
            native.quantized_grid,
            dtype=np.int16,
            copy=True,
        )
        score_grid = np.array(native.score_grid, dtype=np.float64, copy=True)
        analysis_backend = "native C99 fixed Q15/Q14"
    else:
        padded = np.pad(
            source.astype(np.float64),
            ((half_window, half_window), (0, 0)),
        )
        scales = np.empty(
            (source.shape[1], frame_count, band_count),
            dtype=np.uint8,
        )
        quantized_grid = np.empty(
            (source.shape[1], frame_count, half_window),
            dtype=np.int16,
        )
        score_grid = np.empty(
            (source.shape[1], frame_count, half_window),
            dtype=np.float64,
        )
        for channel in range(source.shape[1]):
            for frame in range(frame_count):
                start = frame * half_window
                if fixed_transform:
                    spectrum = analyze_fixed_lapped(
                        padded[
                            start : start + 2 * half_window,
                            channel,
                        ].astype(np.int64),
                        half_window,
                    )
                else:
                    spectrum = (
                        padded[start : start + 2 * half_window, channel]
                        * window
                    ) @ matrix.T
                quantized = np.empty(half_window, dtype=np.int64)
                for band, (band_start, band_end) in enumerate(
                    zip(edges[:-1], edges[1:], strict=True)
                ):
                    maximum = max(
                        1,
                        int(np.max(np.abs(spectrum[band_start:band_end]))),
                    )
                    minimum_step = max(1, (maximum + 126) // 127)
                    exponent = min(31, (minimum_step - 1).bit_length())
                    scales[channel, frame, band] = exponent
                    if fixed_transform:
                        quantized[band_start:band_end] = round_shift_signed(
                            spectrum[band_start:band_end],
                            exponent,
                        ) if exponent else spectrum[band_start:band_end]
                    else:
                        quantized[band_start:band_end] = np.rint(
                            spectrum[band_start:band_end]
                            / float(1 << exponent)
                        ).astype(np.int64)
                quantized_grid[channel, frame] = np.clip(
                    quantized,
                    -127,
                    127,
                ).astype(np.int16)
                score_grid[channel, frame] = np.square(
                    spectrum.astype(np.float64)
                )
        analysis_backend = (
            "python fixed Q15/Q14"
            if fixed_transform
            else "python float64"
        )
    source.flags.writeable = False
    scales.flags.writeable = False
    quantized_grid.flags.writeable = False
    score_grid.flags.writeable = False
    return LappedAnalysis(
        sample_rate=sample_rate,
        samples=source,
        half_window=half_window,
        band_count=band_count,
        frame_count=frame_count,
        fixed_transform=fixed_transform,
        fixed_table_sha256=table_sha256,
        analysis_backend=analysis_backend,
        scales=scales,
        quantized_grid=quantized_grid,
        score_grid=score_grid,
    )


def encode_lapped_analysis(
    analysis: LappedAnalysis,
    *,
    coefficients_per_frame: int,
    entropy_backend: str = "bounded",
    density_backend: str = "fixed",
    native_decoder=None,
) -> LappedEncodeResult:
    """Select, pack, and verify one stream from reusable source analysis."""

    if not isinstance(analysis, LappedAnalysis):
        raise TypeError("lapped encoder requires LappedAnalysis")
    source = analysis.samples
    sample_rate = analysis.sample_rate
    half_window = analysis.half_window
    band_count = analysis.band_count
    frame_count = analysis.frame_count
    fixed_transform = analysis.fixed_transform
    table_sha256 = analysis.fixed_table_sha256
    scales = analysis.scales
    quantized_grid = analysis.quantized_grid
    score_grid = analysis.score_grid
    if not 1 <= coefficients_per_frame <= half_window:
        raise ValueError("lapped coefficient budget exceeds the window")
    coefficients = np.zeros(
        (source.shape[1], frame_count, half_window),
        dtype=np.int8,
    )

    selected_positions = None
    selected_values_grid = None
    variable_counts = None
    variable_positions = None
    variable_values = None
    if density_backend == "fixed":
        selected_positions = np.empty(
            (source.shape[1], frame_count, coefficients_per_frame),
            dtype=np.uint16,
        )
        selected_values_grid = np.empty(
            (source.shape[1], frame_count, coefficients_per_frame),
            dtype=np.int8,
        )
        for channel in range(source.shape[1]):
            for frame in range(frame_count):
                selected = np.sort(
                    np.argpartition(
                        score_grid[channel, frame],
                        -coefficients_per_frame,
                    )[-coefficients_per_frame:]
                )
                selected_values = quantized_grid[
                    channel,
                    frame,
                    selected,
                ].astype(np.int8)
                coefficients[channel, frame, selected] = selected_values
                selected_positions[channel, frame] = selected
                selected_values_grid[channel, frame] = selected_values
        selected_count_min = coefficients_per_frame
        selected_count_max = coefficients_per_frame
    elif density_backend == "adaptive":
        if entropy_backend != "bounded":
            raise ValueError("adaptive density requires bounded sparse entropy")
        total_budget = (
            coefficients_per_frame
            * source.shape[1]
            * frame_count
        )
        flat_quantized = quantized_grid.reshape(-1)
        valid_indices = np.flatnonzero(flat_quantized)
        selected_total = min(total_budget, int(valid_indices.size))
        if selected_total == valid_indices.size:
            selected_global = valid_indices
        else:
            valid_scores = score_grid.reshape(-1)[valid_indices]
            selected_global = valid_indices[
                np.argpartition(valid_scores, -selected_total)[
                    -selected_total:
                ]
            ]
        selected_mask = np.zeros(flat_quantized.size, dtype=np.bool_)
        selected_mask[selected_global] = True
        selected_mask = selected_mask.reshape(quantized_grid.shape)
        variable_counts = np.empty(
            (source.shape[1], frame_count),
            dtype=np.uint16,
        )
        position_parts = []
        value_parts = []
        for channel in range(source.shape[1]):
            for frame in range(frame_count):
                positions = np.flatnonzero(
                    selected_mask[channel, frame]
                ).astype(np.uint16)
                values = quantized_grid[
                    channel,
                    frame,
                    positions,
                ].astype(np.int8)
                variable_counts[channel, frame] = positions.size
                coefficients[channel, frame, positions] = values
                position_parts.append(positions)
                value_parts.append(values)
        variable_positions = np.concatenate(position_parts)
        variable_values = np.concatenate(value_parts)
        selected_count_min = int(np.min(variable_counts))
        selected_count_max = int(np.max(variable_counts))
    else:
        raise ValueError("unknown lapped density backend")
    nonzero_count = int(np.count_nonzero(coefficients))

    raw = bytearray()
    for channel in range(source.shape[1]):
        for frame in range(frame_count):
            raw += scales[channel, frame].tobytes()
            raw += coefficients[channel, frame].tobytes()
    if entropy_backend == "zlib":
        entropy_id = ENTROPY_ZLIB
        entropy_payload = zlib.compress(bytes(raw), level=9)
        entropy_name = "zlib level 9; non-normative comparator"
    elif entropy_backend == "bounded":
        entropy_id = ENTROPY_BOUNDED_SPARSE
        if density_backend == "adaptive":
            entropy_payload = encode_variable_sparse_lapped(
                scales,
                variable_counts,
                variable_positions,
                variable_values,
                half_window=half_window,
            )
            entropy_name = (
                "bounded variable-density sparse Rice/packed research syntax"
            )
        else:
            entropy_payload = encode_sparse_lapped(
                scales,
                selected_positions,
                selected_values_grid,
                half_window=half_window,
            )
            entropy_name = "bounded sparse Rice/packed research syntax"
    else:
        raise ValueError("unknown lapped entropy backend")
    inner = (
        HEADER.pack(
            MAGIC,
            VERSION,
            entropy_id
            | (FLAG_FIXED_TRANSFORM if fixed_transform else 0)
            | (
                FLAG_VARIABLE_DENSITY
                if density_backend == "adaptive"
                else 0
            ),
            source.shape[1],
            sample_rate,
            source.shape[0],
            half_window,
            band_count,
            frame_count,
            len(raw) if entropy_id == ENTROPY_ZLIB else len(entropy_payload),
        )
        + entropy_payload
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
    if native_decoder is None:
        reconstruction = decode_lapped_stream(payload).samples
        reconstruction_backend = "python fixed reference"
    else:
        native = native_decoder.decode_lapped(payload)
        if (
            native.sample_rate != sample_rate
            or native.samples.shape != source.shape
        ):
            raise RuntimeError("native lapped reconstruction shape differs")
        reconstruction = native.samples
        reconstruction_backend = "native C99 Golden Core"
    report = {
        "status": "research lapped Innovation; syntax is non-normative",
        "format_profile": "prospective-LPF1-RSC1-level-5",
        "entropy_backend": entropy_name,
        "transform_backend": (
            "fixed Q15 window/Q14 cosine" if fixed_transform else "float64"
        ),
        "fixed_table_sha256": table_sha256,
        "analysis_backend": analysis.analysis_backend,
        "reconstruction_backend": reconstruction_backend,
        "density_backend": density_backend,
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
        "selected_count_min": selected_count_min,
        "selected_count_max": selected_count_max,
        "nonzero_coefficients": nonzero_count,
        "raw_grid_bytes": len(raw),
        "compressed_grid_bytes": len(entropy_payload),
        **_quality_report(
            source.reshape(-1),
            reconstruction.reshape(-1),
        ),
    }
    coefficients.flags.writeable = False
    return LappedEncodeResult(
        payload,
        reconstruction,
        report,
        scales,
        coefficients,
    )


def pack_lapped_selected_grid(
    scales: np.ndarray,
    coefficients: np.ndarray,
    *,
    sample_rate: int,
    sample_count: int,
    half_window: int,
    fixed_transform: bool = True,
) -> bytes:
    """Pack an already selected grid as one adaptive-density LPF1 child."""

    if sample_rate <= 0:
        raise ValueError("selected lapped sample rate must be positive")
    entropy_payload = pack_lapped_selected_payload(
        scales,
        coefficients,
        sample_count=sample_count,
        half_window=half_window,
    )
    scale_grid = np.asarray(scales)
    channels, frame_count, band_count = scale_grid.shape
    inner = (
        HEADER.pack(
            MAGIC,
            VERSION,
            ENTROPY_BOUNDED_SPARSE
            | FLAG_VARIABLE_DENSITY
            | (FLAG_FIXED_TRANSFORM if fixed_transform else 0),
            channels,
            sample_rate,
            sample_count,
            half_window,
            band_count,
            frame_count,
            len(entropy_payload),
        )
        + entropy_payload
    )
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, 1, channels)),
            ),
            RSC1Section("LPF1", inner),
        ],
        profile=0,
        level=5,
        timebase_hz=sample_rate,
    )


def pack_lapped_selected_payload(
    scales: np.ndarray,
    coefficients: np.ndarray,
    *,
    sample_count: int,
    half_window: int,
) -> bytes:
    """Pack only bounded LSE2 fields under stream-level lapped parameters."""

    scale_grid = np.asarray(scales)
    coefficient_grid = np.asarray(coefficients)
    if (
        scale_grid.dtype != np.uint8
        or scale_grid.ndim != 3
        or coefficient_grid.dtype != np.int8
        or coefficient_grid.ndim != 3
        or scale_grid.shape[:2] != coefficient_grid.shape[:2]
        or coefficient_grid.shape[2] != half_window
        or sample_count <= 0
    ):
        raise TypeError("invalid selected lapped grid")
    channels, frame_count, band_count = scale_grid.shape
    _band_edges(half_window, band_count)
    if (
        not 1 <= channels <= MAX_CHANNELS
        or frame_count != sample_count // half_window + 1
        or np.any(scale_grid > 31)
    ):
        raise ValueError("selected lapped grid exceeds the profile")

    counts = np.count_nonzero(coefficient_grid, axis=2).astype(np.uint16)
    position_parts = []
    value_parts = []
    for channel in range(channels):
        for frame in range(frame_count):
            positions = np.flatnonzero(
                coefficient_grid[channel, frame]
            ).astype(np.uint16)
            position_parts.append(positions)
            value_parts.append(
                coefficient_grid[channel, frame, positions].astype(np.int8)
            )
    positions = np.concatenate(position_parts)
    values = np.concatenate(value_parts)
    entropy_payload = encode_variable_sparse_lapped(
        scale_grid,
        counts,
        positions,
        values,
        half_window=half_window,
    )
    return entropy_payload


def synthesize_lapped_selected_grid(
    scales: np.ndarray,
    coefficients: np.ndarray,
    *,
    sample_count: int,
    half_window: int,
    fixed_transform: bool = True,
) -> np.ndarray:
    """Render one validated selected grid through the canonical lapped kernel."""

    scale_grid = np.asarray(scales)
    coefficient_grid = np.asarray(coefficients)
    if (
        scale_grid.dtype != np.uint8
        or scale_grid.ndim != 3
        or coefficient_grid.dtype != np.int8
        or coefficient_grid.ndim != 3
        or scale_grid.shape[:2] != coefficient_grid.shape[:2]
        or coefficient_grid.shape[2] != half_window
        or sample_count <= 0
        or scale_grid.shape[1] != sample_count // half_window + 1
        or np.any(scale_grid > 31)
    ):
        raise TypeError("invalid selected lapped synthesis grid")
    edges = _band_edges(half_window, scale_grid.shape[2])
    output = _synthesize(
        coefficient_grid,
        scale_grid,
        sample_count=sample_count,
        half_window=half_window,
        edges=edges,
        fixed_transform=fixed_transform,
    )
    output.flags.writeable = False
    return output


def encode_lapped_stream(
    samples: np.ndarray,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    half_window: int = 512,
    band_count: int = 24,
    entropy_backend: str = "bounded",
    transform_backend: str = "fixed",
    density_backend: str = "fixed",
    native_analyzer=None,
    native_decoder=None,
) -> LappedEncodeResult:
    """Analyze source PCM, then encode one exact-byte lapped candidate."""

    analysis = analyze_lapped_source(
        samples,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend=transform_backend,
        native_analyzer=native_analyzer,
    )
    return encode_lapped_analysis(
        analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend=entropy_backend,
        density_backend=density_backend,
        native_decoder=native_decoder,
    )
