"""R-105 nonrecursive fixed-ROM harmonic excitation Basis oracle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .analytic_oracle import SINE_ROM
from .lapped_oracle import (
    LappedAnalysis,
    analyze_lapped_source,
    decode_lapped_stream,
    encode_lapped_analysis,
)
from .periodic import PHASE_SCALE


MAGIC = b"HBR1"
VERSION = 1
HEADER = struct.Struct("<4sBIHIBI")
ACTIVE_BLOCK = struct.Struct("<HH")
CHECKSUM = struct.Struct("<I")
MAX_HARMONICS = 8
MAX_BLOCK_COUNT = 65535
MIN_HARMONIC_COEFFICIENT = -2048
MAX_HARMONIC_COEFFICIENT = 2047
MAX_SAMPLE_COUNT = (1 << 31) - 1
MIN_CORRELATION = 0.55
ROM_INDEX_SHIFT = 22
ROM_QUARTER = len(SINE_ROM) // 4


@dataclass(frozen=True)
class HarmonicBlock:
    """One absolute local phase law and bounded sine/cosine amplitudes."""

    increment_q32: int
    coefficients: np.ndarray


@dataclass(frozen=True)
class HarmonicBasisAnalysis:
    """Immutable harmonic model and lapped analysis of its Innovation."""

    sample_rate: int
    source: np.ndarray
    block_size: int
    harmonic_count: int
    blocks: tuple[HarmonicBlock, ...]
    innovation: np.ndarray
    lapped_analysis: LappedAnalysis


@dataclass(frozen=True)
class HarmonicBasisResult:
    """Complete prospective stream and independently decoded PCM."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _round_shift(value: int, shift: int) -> int:
    magnitude = (abs(value) + (1 << (shift - 1))) >> shift
    return -magnitude if value < 0 else magnitude


def _render_block(
    sample_count: int,
    increment_q32: int,
    coefficients: np.ndarray,
) -> np.ndarray:
    if increment_q32 == 0:
        return np.zeros(sample_count, dtype=np.int16)
    harmonic_count = coefficients.shape[0]
    output = np.empty(sample_count, dtype=np.int16)
    for sample in range(sample_count):
        accumulator = 0
        for harmonic in range(1, harmonic_count + 1):
            phase = (
                sample * harmonic * increment_q32
            ) & 0xFFFF_FFFF
            index = phase >> ROM_INDEX_SHIFT
            sine = int(SINE_ROM[index])
            cosine = int(
                SINE_ROM[(index + ROM_QUARTER) % len(SINE_ROM)]
            )
            accumulator += (
                int(coefficients[harmonic - 1, 0]) * sine
                + int(coefficients[harmonic - 1, 1]) * cosine
            )
        output[sample] = np.clip(
            _round_shift(accumulator, 15),
            -32768,
            32767,
        )
    return output


def _pitch_increment(
    samples: np.ndarray,
    sample_rate: int,
) -> int:
    minimum_lag = max(1, (sample_rate + 399) // 400)
    maximum_lag = min(samples.size // 2, sample_rate // 60)
    if maximum_lag < minimum_lag:
        return 0
    centered = samples.astype(np.float64)
    centered -= np.mean(centered)
    total_energy = float(centered @ centered)
    if total_energy < 64.0 * 64.0 * samples.size:
        return 0
    best_lag = 0
    best_correlation = -1.0
    for lag in range(minimum_lag, maximum_lag + 1):
        left = centered[lag:]
        right = centered[:-lag]
        denominator = np.sqrt(float(left @ left) * float(right @ right))
        if denominator <= 0.0:
            continue
        correlation = float(left @ right) / denominator
        if correlation > best_correlation:
            best_lag = lag
            best_correlation = correlation
    if best_correlation < MIN_CORRELATION:
        return 0
    return max(
        1,
        min(0xFFFF_FFFF, int(round(PHASE_SCALE / best_lag))),
    )


def _fit_block(
    samples: np.ndarray,
    sample_rate: int,
    harmonic_count: int,
) -> tuple[HarmonicBlock, np.ndarray]:
    increment_q32 = _pitch_increment(samples, sample_rate)
    if increment_q32 == 0:
        coefficients = np.zeros((harmonic_count, 2), dtype=np.int16)
        coefficients.flags.writeable = False
        return HarmonicBlock(0, coefficients), samples.copy()

    design = np.empty((samples.size, 2 * harmonic_count), dtype=np.float64)
    for harmonic in range(1, harmonic_count + 1):
        for sample in range(samples.size):
            phase = (
                sample * harmonic * increment_q32
            ) & 0xFFFF_FFFF
            index = phase >> ROM_INDEX_SHIFT
            design[sample, 2 * (harmonic - 1)] = (
                int(SINE_ROM[index]) / 32768.0
            )
            design[sample, 2 * (harmonic - 1) + 1] = (
                int(SINE_ROM[(index + ROM_QUARTER) % len(SINE_ROM)])
                / 32768.0
            )
    fitted, _residuals, _rank, _singular = np.linalg.lstsq(
        design,
        samples.astype(np.float64),
        rcond=None,
    )
    coefficients = np.clip(
        np.rint(fitted),
        MIN_HARMONIC_COEFFICIENT,
        MAX_HARMONIC_COEFFICIENT,
    ).astype(np.int16).reshape(harmonic_count, 2)
    prediction = _render_block(
        samples.size,
        increment_q32,
        coefficients,
    )
    innovation = samples.astype(np.int64) - prediction.astype(np.int64)
    if innovation.size and int(np.max(np.abs(innovation))) > 32767:
        coefficients = np.zeros((harmonic_count, 2), dtype=np.int16)
        coefficients.flags.writeable = False
        return HarmonicBlock(0, coefficients), samples.copy()
    coefficients.flags.writeable = False
    return (
        HarmonicBlock(increment_q32, coefficients),
        innovation.astype(np.int16),
    )


def analyze_harmonic_basis_source(
    samples: np.ndarray,
    sample_rate: int,
    *,
    block_size: int,
    harmonic_count: int,
) -> HarmonicBasisAnalysis:
    """Fit nonrecursive harmonic blocks and analyze exact Innovation."""

    source_view = np.asarray(samples)
    if source_view.dtype != np.int16 or source_view.ndim != 1:
        raise TypeError("harmonic Basis input must be mono int16 PCM")
    if not 512 <= block_size <= 8192:
        raise ValueError("harmonic Basis block size exceeds the bound")
    if not 1 <= harmonic_count <= MAX_HARMONICS:
        raise ValueError("harmonic Basis count exceeds the bound")
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("harmonic Basis sample rate exceeds the bound")
    if source_view.size > MAX_SAMPLE_COUNT:
        raise ValueError("harmonic Basis sample count exceeds the bound")
    source = np.array(source_view, dtype=np.int16, copy=True)
    innovation = np.empty_like(source)
    blocks = []
    for start in range(0, source.size, block_size):
        stop = min(source.size, start + block_size)
        block, block_innovation = _fit_block(
            source[start:stop],
            sample_rate,
            harmonic_count,
        )
        blocks.append(block)
        innovation[start:stop] = block_innovation
    lapped_analysis = analyze_lapped_source(
        innovation.reshape(-1, 1),
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    source.flags.writeable = False
    innovation.flags.writeable = False
    return HarmonicBasisAnalysis(
        sample_rate,
        source,
        block_size,
        harmonic_count,
        tuple(blocks),
        innovation,
        lapped_analysis,
    )


def _pack_coefficient_pairs(coefficients: np.ndarray) -> bytes:
    output = bytearray()
    for sine, cosine in coefficients:
        sine_bits = int(sine) & 0x0FFF
        cosine_bits = int(cosine) & 0x0FFF
        packed = sine_bits | (cosine_bits << 12)
        output += packed.to_bytes(3, "little")
    return bytes(output)


def _unpack_coefficient_pairs(
    payload: bytes,
    harmonic_count: int,
) -> np.ndarray:
    if len(payload) != 3 * harmonic_count:
        raise ValueError("harmonic coefficient payload length mismatch")
    coefficients = np.empty((harmonic_count, 2), dtype=np.int16)
    for harmonic in range(harmonic_count):
        packed = int.from_bytes(
            payload[3 * harmonic : 3 * harmonic + 3],
            "little",
        )
        sine = packed & 0x0FFF
        cosine = (packed >> 12) & 0x0FFF
        coefficients[harmonic, 0] = sine - 4096 if sine & 0x0800 else sine
        coefficients[harmonic, 1] = (
            cosine - 4096 if cosine & 0x0800 else cosine
        )
    coefficients.flags.writeable = False
    return coefficients


def _pack(
    analysis: HarmonicBasisAnalysis,
    residual_payload: bytes,
) -> bytes:
    parameter_bytes = bytearray()
    for block_index, block in enumerate(analysis.blocks):
        if block.increment_q32 == 0:
            continue
        lag = int(round(PHASE_SCALE / block.increment_q32))
        parameter_bytes += ACTIVE_BLOCK.pack(block_index, lag)
        parameter_bytes += _pack_coefficient_pairs(block.coefficients)
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            analysis.sample_rate,
            analysis.block_size,
            int(analysis.source.size),
            analysis.harmonic_count,
            len(residual_payload),
        )
        + parameter_bytes
        + residual_payload
    )
    return body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)


def _parse(
    payload: bytes,
) -> tuple[
    int,
    int,
    int,
    int,
    tuple[HarmonicBlock, ...],
    bytes,
]:
    if len(payload) < HEADER.size + CHECKSUM.size:
        raise ValueError("truncated harmonic Basis stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("harmonic Basis checksum mismatch")
    (
        magic,
        version,
        sample_rate,
        block_size,
        sample_count,
        harmonic_count,
        residual_bytes,
    ) = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported harmonic Basis stream")
    if (
        not 8000 <= sample_rate <= 192000
        or not 512 <= block_size <= 8192
        or sample_count > MAX_SAMPLE_COUNT
        or not 1 <= harmonic_count <= MAX_HARMONICS
    ):
        raise ValueError("harmonic Basis header exceeds the bound")
    block_count = (sample_count + block_size - 1) // block_size
    if block_count > MAX_BLOCK_COUNT or residual_bytes > len(body):
        raise ValueError("harmonic Basis block count exceeds the bound")
    residual_start = len(body) - residual_bytes
    if residual_start < HEADER.size:
        raise ValueError("harmonic Basis stream length mismatch")
    zero_coefficients = np.zeros(
        (harmonic_count, 2),
        dtype=np.int16,
    )
    zero_coefficients.flags.writeable = False
    blocks = [
        HarmonicBlock(0, zero_coefficients)
        for _ in range(block_count)
    ]
    cursor = HEADER.size
    previous_index = -1
    coefficient_bytes = 3 * harmonic_count
    entry_bytes = ACTIVE_BLOCK.size + coefficient_bytes
    while cursor < residual_start:
        if cursor + entry_bytes > residual_start:
            raise ValueError("truncated active harmonic block")
        block_index, lag = ACTIVE_BLOCK.unpack_from(body, cursor)
        cursor += ACTIVE_BLOCK.size
        if (
            block_index <= previous_index
            or block_index >= block_count
            or not 1 <= lag <= 65535
        ):
            raise ValueError("non-canonical active harmonic block")
        coefficients = _unpack_coefficient_pairs(
            body[cursor : cursor + coefficient_bytes],
            harmonic_count,
        )
        cursor += coefficient_bytes
        increment_q32 = max(
            1,
            min(0xFFFF_FFFF, int(round(PHASE_SCALE / lag))),
        )
        blocks[block_index] = HarmonicBlock(
            increment_q32,
            coefficients,
        )
        previous_index = block_index
    if cursor != residual_start:
        raise ValueError("harmonic Basis parameter length mismatch")
    return (
        sample_rate,
        block_size,
        sample_count,
        harmonic_count,
        tuple(blocks),
        body[residual_start:],
    )


def _synthesize(
    residual: np.ndarray,
    block_size: int,
    blocks: tuple[HarmonicBlock, ...],
) -> np.ndarray:
    output = residual.astype(np.int64, copy=True)
    for block_index, block in enumerate(blocks):
        start = block_index * block_size
        stop = min(output.size, start + block_size)
        prediction = _render_block(
            stop - start,
            block.increment_q32,
            block.coefficients,
        )
        output[start:stop] = np.clip(
            output[start:stop] + prediction.astype(np.int64),
            -32768,
            32767,
        )
    return output.astype(np.int16)


def decode_harmonic_basis_stream(payload: bytes) -> tuple[int, np.ndarray]:
    """Independently parse and reconstruct one prospective HBR1 stream."""

    (
        sample_rate,
        block_size,
        sample_count,
        _harmonic_count,
        blocks,
        residual_payload,
    ) = _parse(payload)
    residual = decode_lapped_stream(residual_payload)
    if (
        residual.sample_rate != sample_rate
        or residual.samples.shape != (sample_count, 1)
    ):
        raise ValueError("harmonic Basis residual configuration mismatch")
    reconstruction = _synthesize(
        residual.samples[:, 0],
        block_size,
        blocks,
    )
    reconstruction.flags.writeable = False
    return sample_rate, reconstruction


def encode_harmonic_basis_analysis(
    analysis: HarmonicBasisAnalysis,
    *,
    coefficients_per_frame: int,
) -> HarmonicBasisResult:
    """Encode, parse, and synthesize one complete HBR1 candidate."""

    residual = encode_lapped_analysis(
        analysis.lapped_analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    payload = _pack(analysis, residual.payload)
    sample_rate, reconstruction = decode_harmonic_basis_stream(payload)
    if sample_rate != analysis.sample_rate:
        raise RuntimeError("harmonic Basis decoder sample rate differs")
    active_blocks = sum(block.increment_q32 != 0 for block in analysis.blocks)
    report = {
        "status": "R-105 research oracle; no Main syntax assigned",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "residual_stream_bytes": len(residual.payload),
        "basis_envelope_bytes": len(payload) - len(residual.payload),
        "block_size": analysis.block_size,
        "block_count": len(analysis.blocks),
        "harmonic_count": analysis.harmonic_count,
        "active_block_count": active_blocks,
        "active_block_fraction": active_blocks / max(1, len(analysis.blocks)),
        "coefficients_per_frame": coefficients_per_frame,
        "decoder_change": True,
        "bitstream_status": "prospective research HBR1",
    }
    return HarmonicBasisResult(payload, reconstruction, report)
