"""Compute reproducible full-reference codec diagnostics on decoded PCM."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import signal
import soundfile as sf


EPSILON = 1.0e-12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> tuple[np.ndarray, int]:
    samples, sample_rate = sf.read(
        path,
        dtype="float32",
        always_2d=True,
    )
    if not np.all(np.isfinite(samples)):
        raise ValueError(f"non-finite PCM in {path}")
    return samples, sample_rate


def _select_alignment_slice(reference: np.ndarray, sample_rate: int) -> slice:
    mono = np.mean(reference, axis=1, dtype=np.float64)
    block = sample_rate
    block_count = len(mono) // block
    if block_count == 0:
        return slice(0, len(mono))
    energies = np.asarray(
        [
            np.mean(
                np.square(
                    mono[index * block : (index + 1) * block],
                    dtype=np.float64,
                )
            )
            for index in range(block_count)
        ]
    )
    center = int(np.argmax(energies)) * block + block // 2
    radius = min(4 * sample_rate, len(mono) // 2)
    return slice(max(0, center - radius), min(len(mono), center + radius))


def _align(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    selection = _select_alignment_slice(reference, sample_rate)
    reference_probe = np.mean(reference[selection], axis=1, dtype=np.float64)
    degraded_probe = np.mean(
        degraded[
            selection.start : min(selection.stop, len(degraded))
        ],
        axis=1,
        dtype=np.float64,
    )
    probe_count = min(len(reference_probe), len(degraded_probe))
    reference_probe = reference_probe[:probe_count]
    degraded_probe = degraded_probe[:probe_count]
    maximum_lag = min(round(0.2 * sample_rate), probe_count - 1)
    correlation = signal.correlate(
        degraded_probe,
        reference_probe,
        mode="full",
        method="fft",
    )
    lags = signal.correlation_lags(
        len(degraded_probe),
        len(reference_probe),
        mode="full",
    )
    permitted = np.abs(lags) <= maximum_lag
    lag = int(lags[permitted][np.argmax(correlation[permitted])])
    if lag > 0:
        degraded = degraded[lag:]
    elif lag < 0:
        reference = reference[-lag:]
    common = min(len(reference), len(degraded))
    return reference[:common], degraded[:common], lag


def _global_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
) -> dict[str, float]:
    reference64 = reference.astype(np.float64, copy=False)
    degraded64 = degraded.astype(np.float64, copy=False)
    error = reference64 - degraded64
    reference_energy = float(np.sum(reference64 * reference64))
    error_energy = float(np.sum(error * error))
    snr = 10.0 * math.log10(
        (reference_energy + EPSILON) / (error_energy + EPSILON)
    )
    scale = float(np.sum(reference64 * degraded64)) / (
        reference_energy + EPSILON
    )
    target = scale * reference64
    distortion = degraded64 - target
    si_sdr = 10.0 * math.log10(
        (float(np.sum(target * target)) + EPSILON)
        / (float(np.sum(distortion * distortion)) + EPSILON)
    )

    frame = max(1, round(sample_rate * 0.020))
    count = len(reference) // frame
    reference_frames = reference64[: count * frame].reshape(
        count,
        frame,
        reference.shape[1],
    )
    error_frames = error[: count * frame].reshape(
        count,
        frame,
        reference.shape[1],
    )
    frame_reference_energy = np.mean(
        reference_frames * reference_frames,
        axis=(1, 2),
    )
    frame_error_energy = np.mean(
        error_frames * error_frames,
        axis=(1, 2),
    )
    active = frame_reference_energy > 10.0 ** (-50.0 / 10.0)
    segmental = 10.0 * np.log10(
        (frame_reference_energy[active] + EPSILON)
        / (frame_error_energy[active] + EPSILON)
    )
    segmental = np.clip(segmental, -10.0, 35.0)
    return {
        "snr_db": snr,
        "si_sdr_db": si_sdr,
        "segmental_snr_db": float(np.mean(segmental)),
        "maximum_absolute_error": float(np.max(np.abs(error))),
        "rms_error": float(np.sqrt(np.mean(error * error))),
    }


def _mel_filter_bank(
    sample_rate: int,
    fft_size: int,
    band_count: int,
) -> np.ndarray:
    maximum_hz = sample_rate / 2.0

    def hz_to_mel(value: np.ndarray | float) -> np.ndarray:
        return 2595.0 * np.log10(1.0 + np.asarray(value) / 700.0)

    def mel_to_hz(value: np.ndarray) -> np.ndarray:
        return 700.0 * (10.0 ** (value / 2595.0) - 1.0)

    mel_points = np.linspace(
        hz_to_mel(0.0),
        hz_to_mel(maximum_hz),
        band_count + 2,
    )
    bins = np.floor(
        (fft_size + 1) * mel_to_hz(mel_points) / sample_rate
    ).astype(int)
    bins = np.clip(bins, 0, fft_size // 2)
    filters = np.zeros((band_count, fft_size // 2 + 1), dtype=np.float64)
    for band in range(band_count):
        left, center, right = bins[band : band + 3]
        if center > left:
            filters[band, left:center] = (
                np.arange(left, center) - left
            ) / (center - left)
        if right > center:
            filters[band, center:right] = (
                right - np.arange(center, right)
            ) / (right - center)
    return filters


def _spectral_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    mode: str,
) -> dict[str, object]:
    mono_reference = np.mean(reference, axis=1, dtype=np.float64)
    mono_degraded = np.mean(degraded, axis=1, dtype=np.float64)
    fft_sizes = (256, 512, 1024) if mode == "speech" else (512, 2048, 8192)
    primary_fft = 512 if mode == "speech" else 2048
    mel_bands = 40 if mode == "speech" else 64
    chunk_frames = sample_rate * 10
    spectral_accumulators = {
        size: {
            "error_square": 0.0,
            "reference_square": 0.0,
            "log_absolute": 0.0,
            "elements": 0,
        }
        for size in fft_sizes
    }
    lsd_square = 0.0
    lsd_frames = 0
    cosine_sum = 0.0
    mel_square = 0.0
    mel_elements = 0
    mel_filters = _mel_filter_bank(sample_rate, primary_fft, mel_bands)

    for start in range(0, len(mono_reference), chunk_frames):
        stop = min(len(mono_reference), start + chunk_frames)
        if stop - start < max(fft_sizes):
            continue
        reference_chunk = mono_reference[start:stop]
        degraded_chunk = mono_degraded[start:stop]
        for fft_size in fft_sizes:
            hop = fft_size // 4
            _, _, reference_stft = signal.stft(
                reference_chunk,
                fs=sample_rate,
                window="hann",
                nperseg=fft_size,
                noverlap=fft_size - hop,
                nfft=fft_size,
                boundary=None,
                padded=False,
            )
            _, _, degraded_stft = signal.stft(
                degraded_chunk,
                fs=sample_rate,
                window="hann",
                nperseg=fft_size,
                noverlap=fft_size - hop,
                nfft=fft_size,
                boundary=None,
                padded=False,
            )
            reference_magnitude = np.abs(reference_stft)
            degraded_magnitude = np.abs(degraded_stft)
            accumulator = spectral_accumulators[fft_size]
            accumulator["error_square"] += float(
                np.sum(
                    np.square(
                        reference_magnitude - degraded_magnitude
                    )
                )
            )
            accumulator["reference_square"] += float(
                np.sum(np.square(reference_magnitude))
            )
            accumulator["log_absolute"] += float(
                np.sum(
                    np.abs(
                        np.log(reference_magnitude + 1.0e-7)
                        - np.log(degraded_magnitude + 1.0e-7)
                    )
                )
            )
            accumulator["elements"] += reference_magnitude.size

            if fft_size != primary_fft:
                continue
            reference_db = 20.0 * np.log10(reference_magnitude + 1.0e-7)
            degraded_db = 20.0 * np.log10(degraded_magnitude + 1.0e-7)
            active = (
                np.mean(np.square(reference_magnitude), axis=0)
                > 10.0 ** (-70.0 / 10.0)
            )
            if np.any(active):
                difference = reference_db[:, active] - degraded_db[:, active]
                lsd_square += float(np.sum(np.mean(difference * difference, axis=0)))
                lsd_frames += int(np.count_nonzero(active))
                dot = np.sum(
                    reference_magnitude[:, active]
                    * degraded_magnitude[:, active],
                    axis=0,
                )
                norm = np.linalg.norm(
                    reference_magnitude[:, active],
                    axis=0,
                ) * np.linalg.norm(
                    degraded_magnitude[:, active],
                    axis=0,
                )
                cosine_sum += float(np.sum(dot / (norm + EPSILON)))
            reference_mel = mel_filters @ np.square(reference_magnitude)
            degraded_mel = mel_filters @ np.square(degraded_magnitude)
            mel_difference = (
                np.log(reference_mel + 1.0e-10)
                - np.log(degraded_mel + 1.0e-10)
            )
            mel_square += float(np.sum(mel_difference * mel_difference))
            mel_elements += mel_difference.size

    multiresolution = {}
    for fft_size, accumulator in spectral_accumulators.items():
        multiresolution[str(fft_size)] = {
            "spectral_convergence": math.sqrt(
                accumulator["error_square"]
                / (accumulator["reference_square"] + EPSILON)
            ),
            "log_magnitude_mae": (
                accumulator["log_absolute"]
                / max(1, accumulator["elements"])
            ),
        }
    return {
        "log_spectral_distance_db": math.sqrt(
            lsd_square / max(1, lsd_frames)
        ),
        "magnitude_cosine_similarity": cosine_sum / max(1, lsd_frames),
        "log_mel_rmse": math.sqrt(mel_square / max(1, mel_elements)),
        "multiresolution_stft": multiresolution,
    }


def _harmonic_peak_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
) -> dict[str, float | int]:
    mono_reference = np.mean(reference, axis=1, dtype=np.float64)
    mono_degraded = np.mean(degraded, axis=1, dtype=np.float64)
    fft_size = 4096 if sample_rate >= 32000 else 2048
    hop = max(1, round(sample_rate * 0.100))
    window = np.hanning(fft_size)
    maximum_bin = min(
        fft_size // 2,
        math.floor(8000.0 * fft_size / sample_rate),
    )
    minimum_bin = max(1, math.ceil(50.0 * fft_size / sample_rate))
    frequency_errors: list[float] = []
    amplitude_errors: list[float] = []
    examined_frames = 0
    candidate_peaks = 0
    preserved_peaks = 0
    for start in range(0, len(mono_reference) - fft_size + 1, hop):
        reference_magnitude = np.abs(
            np.fft.rfft(mono_reference[start : start + fft_size] * window)
        )
        degraded_magnitude = np.abs(
            np.fft.rfft(mono_degraded[start : start + fft_size] * window)
        )
        region = reference_magnitude[minimum_bin : maximum_bin + 1]
        if np.max(region) < 1.0e-5:
            continue
        peaks, _ = signal.find_peaks(region)
        if len(peaks) == 0:
            continue
        peaks = peaks + minimum_bin
        threshold = np.max(region) * 10.0 ** (-40.0 / 20.0)
        peaks = peaks[reference_magnitude[peaks] >= threshold]
        if len(peaks) == 0:
            continue
        strongest = peaks[
            np.argsort(reference_magnitude[peaks])[-8:]
        ]
        examined_frames += 1
        for reference_bin in strongest:
            candidate_peaks += 1
            left = max(minimum_bin, reference_bin - 3)
            right = min(maximum_bin, reference_bin + 3)
            degraded_bin = left + int(
                np.argmax(degraded_magnitude[left : right + 1])
            )
            ratio = (
                degraded_magnitude[degraded_bin] + EPSILON
            ) / (reference_magnitude[reference_bin] + EPSILON)
            amplitude_errors.append(
                min(80.0, abs(20.0 * math.log10(ratio)))
            )
            if ratio >= 10.0 ** (-40.0 / 20.0):
                preserved_peaks += 1
                frequency_errors.append(
                    abs(1200.0 * math.log2(degraded_bin / reference_bin))
                )
    frequency = np.asarray(frequency_errors or [math.nan])
    amplitude = np.asarray(amplitude_errors or [math.nan])
    return {
        "examined_frames": examined_frames,
        "candidate_peaks": candidate_peaks,
        "preserved_peaks": preserved_peaks,
        "peak_preservation_fraction": (
            preserved_peaks / candidate_peaks if candidate_peaks else math.nan
        ),
        "median_frequency_error_cents": float(
            np.median(frequency)
        ),
        "p95_frequency_error_cents": float(
            np.percentile(frequency, 95)
        ),
        "median_amplitude_error_db": float(
            np.median(amplitude)
        ),
        "p95_amplitude_error_db": float(
            np.percentile(amplitude, 95)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("degraded", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("music", "speech"), required=True)
    args = parser.parse_args()

    reference, reference_rate = _load(args.reference)
    degraded, degraded_rate = _load(args.degraded)
    if reference_rate != degraded_rate:
        raise ValueError("reference and degraded sample rates differ")
    if reference.shape[1] != degraded.shape[1]:
        raise ValueError("reference and degraded channel counts differ")
    reference, degraded, lag = _align(
        reference,
        degraded,
        reference_rate,
    )
    report: dict[str, object] = {
        "schema": "resonith-objective-audio-diagnostics-1",
        "mode": args.mode,
        "reference": {
            "path": args.reference.name,
            "bytes": args.reference.stat().st_size,
            "sha256": _sha256(args.reference),
        },
        "degraded": {
            "path": args.degraded.name,
            "bytes": args.degraded.stat().st_size,
            "sha256": _sha256(args.degraded),
        },
        "sample_rate": reference_rate,
        "channels": reference.shape[1],
        "compared_frames": len(reference),
        "alignment_lag_samples": lag,
        "alignment_lag_milliseconds": 1000.0 * lag / reference_rate,
        "waveform": _global_metrics(reference, degraded, reference_rate),
        "spectral": _spectral_metrics(
            reference,
            degraded,
            reference_rate,
            args.mode,
        ),
        "harmonic_peaks": _harmonic_peak_metrics(
            reference,
            degraded,
            reference_rate,
        ),
        "interpretation": (
            "Diagnostics are deterministic full-reference measurements, "
            "not a substitute for controlled blinded listening."
        ),
    }
    if args.mode == "speech":
        from pystoi import stoi

        report["speech"] = {
            "stoi": float(
                stoi(
                    np.mean(reference, axis=1),
                    np.mean(degraded, axis=1),
                    reference_rate,
                    extended=False,
                )
            ),
            "estoi": float(
                stoi(
                    np.mean(reference, axis=1),
                    np.mean(degraded, axis=1),
                    reference_rate,
                    extended=True,
                )
            ),
        }
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
