"""R-104 bounded voiced long-term prediction research oracle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib

import numpy as np

from .lapped_oracle import (
    LappedAnalysis,
    analyze_lapped_source,
    decode_lapped_stream,
    encode_lapped_analysis,
)


MAGIC = b"VPR1"
VERSION = 1
HEADER = struct.Struct("<4sBIIIII")
PARAMETER = struct.Struct("<HB")
CHECKSUM = struct.Struct("<I")
GAIN_SHIFT = 7
MAX_GAIN_Q = 115
MIN_CORRELATION = 0.58
MAX_SAMPLE_COUNT = (1 << 31) - 1


@dataclass(frozen=True)
class PitchParameter:
    """One bounded causal lag/gain law for a fixed sample interval."""

    lag: int
    gain_q: int


@dataclass(frozen=True)
class VoicedPredictiveAnalysis:
    """Immutable predictor parameters and transform-ready Innovation."""

    sample_rate: int
    source: np.ndarray
    block_size: int
    parameters: tuple[PitchParameter, ...]
    innovation: np.ndarray
    lapped_analysis: LappedAnalysis


@dataclass(frozen=True)
class VoicedPredictiveResult:
    """Complete research stream, decoded PCM, and exact byte evidence."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _round_shift(value: int, shift: int) -> int:
    magnitude = (abs(value) + (1 << (shift - 1))) >> shift
    return -magnitude if value < 0 else magnitude


def _parameter_bounds(sample_rate: int) -> tuple[int, int]:
    if not 8000 <= sample_rate <= 192000:
        raise ValueError("voiced predictor sample rate exceeds the bound")
    minimum_lag = max(1, (sample_rate + 399) // 400)
    maximum_lag = min(65535, sample_rate // 60)
    return minimum_lag, maximum_lag


def _fit_parameter(
    source: np.ndarray,
    start: int,
    stop: int,
    minimum_lag: int,
    maximum_lag: int,
) -> PitchParameter:
    if start < maximum_lag or stop <= start:
        return PitchParameter(0, 0)
    current = source[start:stop].astype(np.float64)
    current_energy = float(current @ current)
    if current_energy < 64.0 * 64.0 * current.size:
        return PitchParameter(0, 0)

    best_lag = 0
    best_correlation = -1.0
    best_dot = 0.0
    best_past_energy = 0.0
    for lag in range(minimum_lag, maximum_lag + 1):
        past = source[start - lag : stop - lag].astype(np.float64)
        past_energy = float(past @ past)
        if past_energy <= 0.0:
            continue
        dot = float(current @ past)
        correlation = dot / np.sqrt(current_energy * past_energy)
        if correlation > best_correlation:
            best_lag = lag
            best_correlation = correlation
            best_dot = dot
            best_past_energy = past_energy
    if best_correlation < MIN_CORRELATION or best_dot <= 0.0:
        return PitchParameter(0, 0)
    gain = min(MAX_GAIN_Q / float(1 << GAIN_SHIFT), best_dot / best_past_energy)
    gain_q = int(np.rint(gain * (1 << GAIN_SHIFT)))
    if not 1 <= gain_q <= MAX_GAIN_Q:
        return PitchParameter(0, 0)
    return PitchParameter(best_lag, gain_q)


def _prediction_innovation(
    source: np.ndarray,
    block_size: int,
    parameters: tuple[PitchParameter, ...],
) -> tuple[np.ndarray, tuple[PitchParameter, ...]]:
    innovation = source.astype(np.int64, copy=True)
    accepted_parameters = list(parameters)
    for block_index, parameter in enumerate(parameters):
        if parameter.gain_q == 0:
            continue
        start = block_index * block_size
        stop = min(source.size, start + block_size)
        for index in range(start, stop):
            if index < parameter.lag:
                continue
            predicted = _round_shift(
                parameter.gain_q * int(source[index - parameter.lag]),
                GAIN_SHIFT,
            )
            innovation[index] = int(source[index]) - predicted
        if (
            innovation[start:stop].size
            and int(np.max(np.abs(innovation[start:stop]))) > 32767
        ):
            innovation[start:stop] = source[start:stop]
            accepted_parameters[block_index] = PitchParameter(0, 0)
    return (
        np.clip(innovation, -32768, 32767).astype(np.int16),
        tuple(accepted_parameters),
    )


def analyze_voiced_predictive_source(
    samples: np.ndarray,
    sample_rate: int,
    *,
    block_size: int = 512,
) -> VoicedPredictiveAnalysis:
    """Fit bounded pitch laws and analyze their Innovation once for RDO."""

    source_view = np.asarray(samples)
    if source_view.dtype != np.int16 or source_view.ndim != 1:
        raise TypeError("voiced predictor input must be mono int16 PCM")
    if not 128 <= block_size <= 8192:
        raise ValueError("voiced predictor block size exceeds the bound")
    if source_view.size > MAX_SAMPLE_COUNT:
        raise ValueError("voiced predictor sample count exceeds the bound")
    minimum_lag, maximum_lag = _parameter_bounds(sample_rate)
    source = np.array(source_view, dtype=np.int16, copy=True)
    proposed_parameters = tuple(
        _fit_parameter(
            source,
            start,
            min(source.size, start + block_size),
            minimum_lag,
            maximum_lag,
        )
        for start in range(0, source.size, block_size)
    )
    innovation, parameters = _prediction_innovation(
        source,
        block_size,
        proposed_parameters,
    )
    lapped_analysis = analyze_lapped_source(
        innovation.reshape(-1, 1),
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    source.flags.writeable = False
    innovation.flags.writeable = False
    return VoicedPredictiveAnalysis(
        sample_rate,
        source,
        block_size,
        parameters,
        innovation,
        lapped_analysis,
    )


def _pack(
    analysis: VoicedPredictiveAnalysis,
    residual_payload: bytes,
) -> bytes:
    parameters = b"".join(
        PARAMETER.pack(parameter.lag, parameter.gain_q)
        for parameter in analysis.parameters
    )
    body = (
        HEADER.pack(
            MAGIC,
            VERSION,
            analysis.sample_rate,
            analysis.block_size,
            int(analysis.source.size),
            len(analysis.parameters),
            len(residual_payload),
        )
        + parameters
        + residual_payload
    )
    return body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF)


def _parse(
    payload: bytes,
) -> tuple[int, int, int, tuple[PitchParameter, ...], bytes]:
    if len(payload) < HEADER.size + CHECKSUM.size:
        raise ValueError("truncated voiced predictor stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack(
        payload[-CHECKSUM.size:]
    )[0]:
        raise ValueError("voiced predictor checksum mismatch")
    (
        magic,
        version,
        sample_rate,
        block_size,
        sample_count,
        block_count,
        residual_bytes,
    ) = HEADER.unpack_from(body)
    if magic != MAGIC or version != VERSION:
        raise ValueError("unsupported voiced predictor stream")
    minimum_lag, maximum_lag = _parameter_bounds(sample_rate)
    if (
        not 128 <= block_size <= 8192
        or sample_count > MAX_SAMPLE_COUNT
        or block_count
            != (sample_count + block_size - 1) // block_size
    ):
        raise ValueError("voiced predictor header exceeds the bound")
    parameter_bytes = block_count * PARAMETER.size
    expected_bytes = HEADER.size + parameter_bytes + residual_bytes
    if expected_bytes != len(body):
        raise ValueError("voiced predictor stream length mismatch")
    parameters = []
    cursor = HEADER.size
    for _ in range(block_count):
        lag, gain_q = PARAMETER.unpack_from(body, cursor)
        cursor += PARAMETER.size
        if gain_q == 0:
            if lag != 0:
                raise ValueError("zero-gain voiced predictor has a lag")
        elif (
            not minimum_lag <= lag <= maximum_lag
            or gain_q > MAX_GAIN_Q
        ):
            raise ValueError("voiced predictor parameter exceeds the bound")
        parameters.append(PitchParameter(lag, gain_q))
    return (
        sample_rate,
        block_size,
        sample_count,
        tuple(parameters),
        body[cursor:],
    )


def _synthesize(
    residual: np.ndarray,
    block_size: int,
    parameters: tuple[PitchParameter, ...],
) -> np.ndarray:
    output = residual.astype(np.int64, copy=True)
    for block_index, parameter in enumerate(parameters):
        if parameter.gain_q == 0:
            continue
        start = block_index * block_size
        stop = min(output.size, start + block_size)
        for index in range(start, stop):
            if index < parameter.lag:
                continue
            prediction = _round_shift(
                parameter.gain_q * int(output[index - parameter.lag]),
                GAIN_SHIFT,
            )
            output[index] = np.clip(
                int(residual[index]) + prediction,
                -32768,
                32767,
            )
    return output.astype(np.int16)


def decode_voiced_predictive_stream(payload: bytes) -> tuple[int, np.ndarray]:
    """Independently parse and reconstruct one prospective VPR1 stream."""

    sample_rate, block_size, sample_count, parameters, residual_payload = (
        _parse(payload)
    )
    residual = decode_lapped_stream(residual_payload)
    if (
        residual.sample_rate != sample_rate
        or residual.samples.shape != (sample_count, 1)
    ):
        raise ValueError("voiced predictor residual configuration mismatch")
    reconstruction = _synthesize(
        residual.samples[:, 0],
        block_size,
        parameters,
    )
    reconstruction.flags.writeable = False
    return sample_rate, reconstruction


def encode_voiced_predictive_analysis(
    analysis: VoicedPredictiveAnalysis,
    *,
    coefficients_per_frame: int,
) -> VoicedPredictiveResult:
    """Encode one complete candidate and verify independent reconstruction."""

    residual = encode_lapped_analysis(
        analysis.lapped_analysis,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    payload = _pack(analysis, residual.payload)
    sample_rate, reconstruction = decode_voiced_predictive_stream(payload)
    if sample_rate != analysis.sample_rate:
        raise RuntimeError("voiced predictor decoder sample rate differs")
    voiced_blocks = sum(
        parameter.gain_q != 0 for parameter in analysis.parameters
    )
    report = {
        "status": "R-104 research oracle; no Main syntax assigned",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "residual_stream_bytes": len(residual.payload),
        "parameter_envelope_bytes": len(payload) - len(residual.payload),
        "block_size": analysis.block_size,
        "block_count": len(analysis.parameters),
        "voiced_block_count": voiced_blocks,
        "voiced_block_fraction": (
            voiced_blocks / max(1, len(analysis.parameters))
        ),
        "coefficients_per_frame": coefficients_per_frame,
        "decoder_change": True,
        "bitstream_status": "prospective research VPR1",
    }
    return VoicedPredictiveResult(payload, reconstruction, report)
