"""R-155 semantic-free fractional Basis dictionary research encoder."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    pack_maf_typed,
)


@dataclass(frozen=True)
class WarpFit:
    """One deterministic orbit member selected by the encoder."""

    source_position_q16: int
    source_step_q16: int
    end_source_step_q16: int | None
    gain_q15: int
    end_gain_q15: int | None
    normalized_error: float


@dataclass(frozen=True)
class WarpDictionaryPrediction:
    """One native-decoded MFT1 predictor and its discovery evidence."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _round_divide_away(values: np.ndarray, denominator: int) -> np.ndarray:
    """Round signed integer numerators to nearest with ties away from zero."""

    values64 = np.asarray(values, dtype=np.int64)
    magnitude = np.abs(values64)
    quotient = magnitude // denominator
    quotient += 2 * (magnitude % denominator) >= denominator
    return np.where(values64 < 0, -quotient, quotient)


def _source_positions_q16(
    count: int,
    start_position_q16: int,
    start_step_q16: int,
    end_step_q16: int | None,
) -> np.ndarray:
    """Mirror the normative closed R-155 coordinate trajectory."""

    index = np.arange(count, dtype=np.int64)
    positions = int(start_position_q16) + int(start_step_q16) * index
    if end_step_q16 is None:
        return positions
    if count < 3:
        raise ValueError("linear warp step requires at least three samples")
    numerator = (
        (int(end_step_q16) - int(start_step_q16))
        * index
        * np.maximum(index - 1, 0)
    )
    positions += _round_divide_away(numerator, 2 * (count - 2))
    return positions


def _render_basis(
    basis: np.ndarray,
    count: int,
    start_position_q16: int,
    start_step_q16: int,
    end_step_q16: int | None,
) -> np.ndarray:
    """Render one circular two-tap R-155 Basis trajectory exactly."""

    source = np.asarray(basis, dtype=np.int64)
    period_q16 = source.size * WARP_ONE_Q16
    positions = np.mod(
        _source_positions_q16(
            count,
            start_position_q16,
            start_step_q16,
            end_step_q16,
        ),
        period_q16,
    )
    whole = positions // WARP_ONE_Q16
    fraction = positions % WARP_ONE_Q16
    left = source[whole]
    right = source[(whole + 1) % source.size]
    numerator = left * (WARP_ONE_Q16 - fraction) + right * fraction
    return _round_divide_away(numerator, WARP_ONE_Q16)


def _apply_gain(
    waveform: np.ndarray,
    start_gain_q15: int,
    end_gain_q15: int | None,
) -> np.ndarray:
    count = waveform.size
    if end_gain_q15 is None:
        gains = np.full(count, start_gain_q15, dtype=np.int64)
    else:
        position = np.arange(count, dtype=np.int64)
        gains = int(start_gain_q15) + _round_divide_away(
            (int(end_gain_q15) - int(start_gain_q15)) * position,
            count - 1,
        )
        gains[-1] = int(end_gain_q15)
    return _round_divide_away(
        np.asarray(waveform, dtype=np.int64) * gains,
        32768,
    )


def _fit_gain_law(
    waveform: np.ndarray,
    target: np.ndarray,
) -> tuple[int, int | None, float]:
    """Fit constant and linear Q1.15 laws, then score exact integer renders."""

    basis = np.asarray(waveform, dtype=np.int64)
    desired = np.asarray(target, dtype=np.int64)
    target_energy = max(1, int(desired @ desired))
    denominator = int(basis @ basis)
    if denominator == 0:
        return 0, None, 1.0
    constant = int(np.rint(int(basis @ desired) * 32768.0 / denominator))
    constant = int(np.clip(constant, -32768, 32768))
    constant_render = _apply_gain(basis, constant, None)
    constant_error = desired - constant_render
    best = (
        constant,
        None,
        float(constant_error @ constant_error) / target_energy,
    )

    position = np.linspace(0.0, 1.0, basis.size)
    first = basis.astype(np.float64) * (1.0 - position)
    second = basis.astype(np.float64) * position
    desired_scaled = desired.astype(np.float64) * 32768.0
    aa = float(first @ first)
    ab = float(first @ second)
    bb = float(second @ second)
    ay = float(first @ desired_scaled)
    by = float(second @ desired_scaled)
    determinant = aa * bb - ab * ab
    if determinant > max(1.0, aa * bb) * 1.0e-12:
        start_gain = int(np.clip(
            np.rint((ay * bb - by * ab) / determinant),
            -32768,
            32768,
        ))
        end_gain = int(np.clip(
            np.rint((by * aa - ay * ab) / determinant),
            -32768,
            32768,
        ))
        linear_render = _apply_gain(basis, start_gain, end_gain)
        linear_error = desired - linear_render
        normalized = float(linear_error @ linear_error) / target_energy
        if normalized < best[2]:
            best = start_gain, end_gain, normalized
    return best


def _fit_warp(
    basis: np.ndarray,
    target: np.ndarray,
) -> WarpFit:
    """Search fractional phase, direction, and bounded pitch/time laws."""

    source = np.asarray(basis, dtype=np.int64)
    desired = np.asarray(target, dtype=np.int64)
    target_spectrum = np.fft.fft(desired.astype(np.float64))
    step_offsets = (-1024, -512, 0, 512, 1024)
    candidates: list[WarpFit] = []
    constant_seeds: list[WarpFit] = []
    for direction in (1, -1):
        base_step = direction * WARP_ONE_Q16
        unaligned = _render_basis(
            source,
            source.size,
            0,
            base_step,
            None,
        )
        correlation = np.fft.ifft(
            np.conj(np.fft.fft(unaligned.astype(np.float64)))
            * target_spectrum
        ).real
        lag = int(np.argmax(np.abs(correlation)))
        for fraction in (
            0,
            WARP_ONE_Q16 // 4,
            WARP_ONE_Q16 // 2,
            3 * WARP_ONE_Q16 // 4,
        ):
            for step_offset in step_offsets:
                step = direction * (WARP_ONE_Q16 + step_offset)
                source_position = (
                    fraction - lag * step
                ) % (source.size * WARP_ONE_Q16)
                rendered = _render_basis(
                    source,
                    source.size,
                    source_position,
                    step,
                    None,
                )
                gain, end_gain, error = _fit_gain_law(rendered, desired)
                constant_seeds.append(
                    WarpFit(
                        source_position,
                        step,
                        None,
                        gain,
                        end_gain,
                        error,
                    )
                )

    constant_seeds.sort(
        key=lambda item: (
            item.normalized_error,
            abs(item.source_step_q16) != WARP_ONE_Q16,
            item.source_position_q16,
        )
    )
    candidates.extend(constant_seeds)
    for seed in constant_seeds[:4]:
        direction = 1 if seed.source_step_q16 >= 0 else -1
        for drift in (-512, 512):
            end_step = seed.source_step_q16 + direction * drift
            if seed.source_step_q16 * end_step < 0:
                continue
            rendered = _render_basis(
                source,
                source.size,
                seed.source_position_q16,
                seed.source_step_q16,
                end_step,
            )
            gain, end_gain, error = _fit_gain_law(rendered, desired)
            candidates.append(
                WarpFit(
                    seed.source_position_q16,
                    seed.source_step_q16,
                    end_step,
                    gain,
                    end_gain,
                    error,
                )
            )
    return min(
        candidates,
        key=lambda item: (
            item.normalized_error,
            item.end_source_step_q16 is not None,
            item.end_gain_q15 is not None,
            abs(abs(item.source_step_q16) - WARP_ONE_Q16),
        ),
    )


def _fingerprint(block: np.ndarray) -> bytes:
    """Return a polarity/phase/gain-invariant spectral proposal key."""

    spectrum = np.abs(np.fft.rfft(
        np.asarray(block, dtype=np.float64),
    ))
    boundaries = np.unique(np.rint(np.geomspace(
        1,
        spectrum.size,
        17,
    )).astype(np.int64))
    if boundaries.size < 17:
        boundaries = np.linspace(1, spectrum.size, 17, dtype=np.int64)
    band_rms = np.empty(16, dtype=np.float64)
    for index in range(16):
        start = max(0, int(boundaries[index]) - 1)
        end = max(start + 1, int(boundaries[index + 1]))
        values = spectrum[start:end]
        band_rms[index] = math.sqrt(float(np.mean(values * values)))
    peak = max(1.0, float(np.max(band_rms)))
    relative_db = 20.0 * np.log10(np.maximum(band_rms / peak, 1.0e-9))
    quantized = np.clip(
        np.rint((relative_db + 72.0) / 6.0),
        0,
        12,
    ).astype(np.uint8)
    return hashlib.blake2s(quantized.tobytes(), digest_size=8).digest()


def fit_warp_dictionary_prediction(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    block_samples: int = 4096,
    maximum_bases: int = 64,
    maximum_instances: int = 4096,
    maximum_normalized_error: float = 2.0e-2,
    seeds_per_bucket: int = 2,
) -> WarpDictionaryPrediction:
    """Fit one shared semantic-free warp dictionary across every channel."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-155 fitting requires frame-major PCM16")
    if not 64 <= block_samples <= 16384:
        raise ValueError("R-155 block size exceeds the first Basis profile")
    frames, channels = source.shape
    complete_blocks = frames // block_samples
    locations: list[tuple[int, int]] = []
    buckets: dict[bytes, list[int]] = {}
    for channel in range(channels):
        for block_index in range(complete_blocks):
            start = block_index * block_samples
            block = source[start : start + block_samples, channel]
            if int(np.max(np.abs(block))) < 32:
                continue
            location = len(locations)
            locations.append((channel, start))
            buckets.setdefault(_fingerprint(block), []).append(location)

    proposals: list[tuple[int, int, list[tuple[int, WarpFit]]]] = []
    evaluated_pairs = 0
    for bucket in buckets.values():
        if len(bucket) < 2:
            continue
        remaining = list(bucket)
        for _ in range(min(seeds_per_bucket, len(bucket) - 1)):
            seed_index = remaining[0]
            seed_channel, seed_start = locations[seed_index]
            basis = source[
                seed_start : seed_start + block_samples,
                seed_channel,
            ]
            matches = [
                (
                    seed_index,
                    WarpFit(0, WARP_ONE_Q16, None, 32768, None, 0.0),
                )
            ]
            unmatched = []
            for target_index in remaining[1:]:
                target_channel, target_start = locations[target_index]
                fit = _fit_warp(
                    basis,
                    source[
                        target_start : target_start + block_samples,
                        target_channel,
                    ],
                )
                evaluated_pairs += 1
                if fit.normalized_error <= maximum_normalized_error:
                    matches.append((target_index, fit))
                else:
                    unmatched.append(target_index)
            if len(matches) >= 2:
                estimated = (
                    (len(matches) - 1) * block_samples * 2
                    - len(matches) * 44
                    - 16
                )
                if estimated > 0:
                    proposals.append((estimated, seed_index, matches))
            remaining = unmatched
            if len(remaining) < 2:
                break

    proposals.sort(key=lambda item: (-item[0], item[1]))
    occupied = np.zeros((channels, complete_blocks), dtype=np.bool_)
    bases: list[np.ndarray] = []
    instances: list[MafBasisWarpInstance] = []
    errors: list[float] = []
    linear_steps = 0
    linear_gains = 0
    reverse_steps = 0
    for _, seed_index, matches in proposals:
        available = [
            (target_index, fit)
            for target_index, fit in matches
            if not occupied[
                locations[target_index][0],
                locations[target_index][1] // block_samples,
            ]
        ]
        if len(available) < 2:
            continue
        if len(bases) >= maximum_bases:
            break
        capacity = maximum_instances - len(instances)
        if capacity < 2:
            break
        available = available[:capacity]
        basis_id = len(bases)
        seed_channel, seed_start = locations[seed_index]
        bases.append(
            source[
                seed_start : seed_start + block_samples,
                seed_channel,
            ].astype(np.int64)
        )
        for target_index, fit in available:
            channel, start = locations[target_index]
            occupied[channel, start // block_samples] = True
            errors.append(fit.normalized_error)
            linear_steps += int(fit.end_source_step_q16 is not None)
            linear_gains += int(fit.end_gain_q15 is not None)
            reverse_steps += int(fit.source_step_q16 < 0)
            instances.append(
                MafBasisWarpInstance(
                    emitter_id=channel,
                    basis_id=basis_id,
                    start=start,
                    sample_count=block_samples,
                    source_position_q16=fit.source_position_q16,
                    source_step_q16=fit.source_step_q16,
                    gain_q15=fit.gain_q15,
                    circular=True,
                    end_source_step_q16=fit.end_source_step_q16,
                    end_gain_q15=fit.end_gain_q15,
                )
            )

    matrix = tuple(
        tuple(
            32767 if output == emitter else 0
            for emitter in range(channels)
        )
        for output in range(channels)
    )
    payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=frames,
        render_quantum=min(4096, frames),
        output_channels=channels,
        emitter_count=channels,
        mixes=(MafMix(0, frames, matrix),),
        bases=tuple(
            MafBasis(tuple(int(value) for value in basis))
            for basis in bases
        ),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=256,
    )
    native = native_decoder.decode_maf_typed(
        payload,
        callback_frames=min(997, frames),
    )
    reconstruction = native.samples
    residual = source.astype(np.int64) - reconstruction.astype(np.int64)
    reconstruction.flags.writeable = False
    return WarpDictionaryPrediction(
        payload,
        reconstruction,
        {
            "schema": "resonith-r155-warp-dictionary-prediction-1",
            "status": "native-decoded predictor; Truth admission pending",
            "sample_rate": int(sample_rate),
            "frames": int(frames),
            "channels": int(channels),
            "block_samples": int(block_samples),
            "basis_count": len(bases),
            "instance_count": len(instances),
            "linear_step_instance_count": linear_steps,
            "linear_gain_instance_count": linear_gains,
            "reverse_instance_count": reverse_steps,
            "covered_blocks": int(np.count_nonzero(occupied)),
            "covered_samples": int(
                np.count_nonzero(occupied) * block_samples
            ),
            "spectral_bucket_count": len(buckets),
            "evaluated_pair_count": evaluated_pairs,
            "mean_normalized_fit_error": (
                float(np.mean(errors)) if errors else None
            ),
            "maximum_normalized_fit_error": (
                float(np.max(errors)) if errors else None
            ),
            "predictor_bytes": len(payload),
            "predictor_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_rms": float(
                math.sqrt(np.mean(residual.astype(np.float64) ** 2))
            ),
            "residual_clip_count": int(np.count_nonzero(
                (residual < -32768) | (residual > 32767)
            )),
            "workspace_bytes": native.workspace_bytes,
        },
    )
