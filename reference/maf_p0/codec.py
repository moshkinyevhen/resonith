"""End-to-end MAF-P0 periodic + CIBS + objective residual codec."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from cibs0 import CIBS0Model, materialize_basis

from .container import pack_container, unpack_container
from .model import encode_basis_latent
from .periodic import (
    analyze_periodic_basis,
    apply_block_gains,
    fit_block_gains,
    render_unity_basis,
)


@dataclass(frozen=True)
class EncodeResult:
    payload: bytes
    reconstructed: np.ndarray
    report: dict


@dataclass(frozen=True)
class DecodeResult:
    sample_rate: int
    samples: np.ndarray
    report: dict


def _quantize_signed(value: np.ndarray, step: int) -> np.ndarray:
    if step < 1:
        raise ValueError("quantization step must be positive")
    signed = value.astype(np.int64)
    magnitude = np.abs(signed)
    quantized = (magnitude + step // 2) // step
    quantized = np.where(signed < 0, -quantized, quantized)
    return np.clip(
        quantized, np.iinfo(np.int32).min, np.iinfo(np.int32).max
    ).astype(np.int32)


def _dequantize_signed(value: np.ndarray, step: int) -> np.ndarray:
    return value.astype(np.int64) * int(step)


def _compact_signed(value: np.ndarray) -> np.ndarray:
    minimum = int(np.min(value)) if value.size else 0
    maximum = int(np.max(value)) if value.size else 0
    if np.iinfo(np.int16).min <= minimum and maximum <= np.iinfo(np.int16).max:
        return value.astype(np.int16)
    return value.astype(np.int32)


def _quality_report(source: np.ndarray, reconstructed: np.ndarray) -> dict:
    error = source.astype(np.float64) - reconstructed.astype(np.float64)
    signal_energy = float(np.sum(source.astype(np.float64) ** 2))
    error_energy = float(np.sum(error**2))
    if error_energy == 0.0:
        snr_db = math.inf
    elif signal_energy == 0.0:
        snr_db = -math.inf
    else:
        snr_db = 10.0 * math.log10(signal_energy / error_energy)
    return {
        "snr_db": snr_db,
        "max_abs_error": int(np.max(np.abs(error))) if error.size else 0,
        "exact": bool(np.array_equal(source, reconstructed)),
    }


def encode_samples(
    samples: np.ndarray,
    sample_rate: int,
    *,
    basis_mode: str = "raw",
    cibs_model: CIBS0Model | None = None,
    basis_length: int = 256,
    gain_block_size: int = 1024,
    basis_correction_step: int = 1,
    residual_step: int = 1,
    period_samples: int | None = None,
) -> EncodeResult:
    """Encode one mono PCM16 signal into the P0 research bitstream."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if samples.size == 0:
        raise ValueError("empty input")
    if basis_mode not in {"raw", "cibs"}:
        raise ValueError("basis_mode must be raw or cibs")

    analysis = analyze_periodic_basis(
        samples,
        sample_rate,
        basis_length=basis_length,
        period_samples=period_samples,
    )
    target_basis = analysis.basis.reshape(1, -1)
    arrays: dict[str, np.ndarray] = {}
    metadata: dict = {
        "sample_rate": int(sample_rate),
        "sample_count": int(samples.size),
        "basis_mode": basis_mode,
        "basis_channels": 1,
        "basis_length": int(basis_length),
        "period_samples": int(analysis.period_samples),
        "phase_increment_q32": int(analysis.phase_increment_q32),
        "phase_origin_q32": 0,
        "gain_block_size": int(gain_block_size),
        "gain_shift": 15,
        "basis_correction_step": int(basis_correction_step),
        "residual_step": int(residual_step),
    }

    cibs_macs = 0
    if basis_mode == "raw":
        materialized_basis = target_basis.copy()
        arrays["BASI"] = materialized_basis.astype(np.int16)
        metadata["model_id"] = None
    else:
        if cibs_model is None:
            raise ValueError("CIBS mode requires a model")
        if cibs_model.basis_channels != 1:
            raise ValueError("MAF-P0 requires one-channel CIBS Basis")
        if cibs_model.output_length != basis_length:
            raise ValueError("CIBS model Basis length mismatch")
        latent = encode_basis_latent(target_basis, cibs_model)
        synthesized = materialize_basis(latent, cibs_model)
        difference = (
            target_basis.astype(np.int64)
            - synthesized.samples.astype(np.int64)
        )
        correction_q = _quantize_signed(difference, basis_correction_step)
        corrected = synthesized.samples.astype(np.int64) + _dequantize_signed(
            correction_q, basis_correction_step
        )
        materialized_basis = np.clip(
            corrected, -32768, 32767
        ).astype(np.int16)
        verified = materialize_basis(
            latent,
            cibs_model,
            correction=_dequantize_signed(
                correction_q, basis_correction_step
            ).astype(np.int32),
        )
        arrays["LATE"] = latent
        arrays["BCOR"] = _compact_signed(correction_q)
        metadata["model_id"] = cibs_model.model_id
        metadata["basis_sha256"] = verified.sha256
        cibs_macs = synthesized.integer_macs

    unity = render_unity_basis(
        materialized_basis.reshape(-1),
        samples.size,
        analysis.phase_increment_q32,
    )
    gains = fit_block_gains(samples, unity, gain_block_size)
    prediction = apply_block_gains(unity, gains, gain_block_size)
    residual = samples.astype(np.int64) - prediction.astype(np.int64)
    residual_q = _quantize_signed(residual, residual_step)

    reconstructed64 = (
        prediction.astype(np.int64)
        + _dequantize_signed(residual_q, residual_step)
    )
    reconstructed = np.clip(
        reconstructed64, -32768, 32767
    ).astype(np.int16)
    arrays["GAIN"] = gains
    arrays["RESI"] = _compact_signed(residual_q)

    metadata["pcm_sha256"] = hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()
    payload = pack_container(metadata, arrays)
    packed_metadata, _ = unpack_container(payload)
    quality = _quality_report(samples, reconstructed)
    report = {
        **quality,
        "stream_bytes": len(payload),
        "pcm_bytes": int(samples.nbytes),
        "ratio_vs_pcm": len(payload) / samples.nbytes,
        "saving_vs_pcm": 1.0 - len(payload) / samples.nbytes,
        "period_samples": analysis.period_samples,
        "basis_mode": basis_mode,
        "cibs_integer_macs": cibs_macs,
        "section_raw_bytes": {
            name: int(array.nbytes) for name, array in arrays.items()
        },
        "section_compressed_bytes": {
            str(section["name"]): int(section["compressed_bytes"])
            for section in packed_metadata["sections"]
        },
        "container_overhead_bytes": len(payload)
        - sum(
            int(section["compressed_bytes"])
            for section in packed_metadata["sections"]
        ),
    }
    return EncodeResult(payload, reconstructed, report)


def decode_bytes(
    payload: bytes,
    *,
    cibs_model: CIBS0Model | None = None,
) -> DecodeResult:
    metadata, arrays = unpack_container(payload)
    sample_rate = int(metadata["sample_rate"])
    sample_count = int(metadata["sample_count"])
    basis_mode = str(metadata["basis_mode"])

    if basis_mode == "raw":
        basis = arrays["BASI"]
    elif basis_mode == "cibs":
        if cibs_model is None:
            raise ValueError("CIBS stream requires a model")
        if cibs_model.model_id != metadata["model_id"]:
            raise ValueError("CIBS model ID mismatch")
        correction_q = arrays["BCOR"]
        correction = _dequantize_signed(
            correction_q, int(metadata["basis_correction_step"])
        ).astype(np.int32)
        materialized = materialize_basis(
            arrays["LATE"],
            cibs_model,
            correction=correction,
            expected_sha256=str(metadata["basis_sha256"]),
        )
        basis = materialized.samples
    else:
        raise ValueError("unknown Basis mode")

    unity = render_unity_basis(
        basis.reshape(-1),
        sample_count,
        int(metadata["phase_increment_q32"]),
        phase_origin_q32=int(metadata["phase_origin_q32"]),
    )
    prediction = apply_block_gains(
        unity,
        arrays["GAIN"],
        int(metadata["gain_block_size"]),
    )
    residual = _dequantize_signed(
        arrays["RESI"], int(metadata["residual_step"])
    )
    output = np.clip(
        prediction.astype(np.int64) + residual,
        -32768,
        32767,
    ).astype(np.int16)
    report = {
        "stream_bytes": len(payload),
        "sample_count": sample_count,
        "basis_mode": basis_mode,
        "pcm_sha256": hashlib.sha256(
            output.astype("<i2", copy=False).tobytes()
        ).hexdigest(),
        "matches_source_hash": hashlib.sha256(
            output.astype("<i2", copy=False).tobytes()
        ).hexdigest()
        == metadata["pcm_sha256"],
    }
    return DecodeResult(sample_rate, output, report)
