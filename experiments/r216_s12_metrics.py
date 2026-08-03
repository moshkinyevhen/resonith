"""Zero-lag full-reference metrics for the audited R-216 S12 gate."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy import signal

from experiments.objective_audio_metrics import _spectral_metrics
from reference.maf_p0.perceptual_metrics import transient_pre_echo_error_db


EPSILON = 1.0e-12


def _note(notes: dict[str, str], path: str, reason: str) -> None:
    notes[path] = reason


def _waveform_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    notes: dict[str, str],
) -> dict[str, float | None]:
    reference64 = reference.astype(np.float64, copy=False)
    degraded64 = degraded.astype(np.float64, copy=False)
    error = reference64 - degraded64
    reference_energy = float(np.sum(reference64 * reference64))
    error_energy = float(np.sum(error * error))
    silent = reference_energy <= EPSILON
    if silent:
        snr = None
        si_sdr = None
        _note(notes, "waveform.snr_db", "silent-reference")
        _note(notes, "waveform.si_sdr_db", "silent-reference")
    else:
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
    if count == 0:
        segmental = None
        _note(notes, "waveform.segmental_snr_db", "insufficient-length")
    else:
        reference_frames = reference64[: count * frame].reshape(
            count, frame, reference.shape[1]
        )
        error_frames = error[: count * frame].reshape(
            count, frame, reference.shape[1]
        )
        reference_frame_energy = np.mean(
            reference_frames * reference_frames, axis=(1, 2)
        )
        error_frame_energy = np.mean(error_frames * error_frames, axis=(1, 2))
        active = reference_frame_energy > 10.0 ** (-50.0 / 10.0)
        if not np.any(active):
            segmental = None
            _note(notes, "waveform.segmental_snr_db", "no-active-frame")
        else:
            values = 10.0 * np.log10(
                (reference_frame_energy[active] + EPSILON)
                / (error_frame_energy[active] + EPSILON)
            )
            segmental = float(np.mean(np.clip(values, -10.0, 35.0)))
    return {
        "snr_db": snr,
        "si_sdr_db": si_sdr,
        "segmental_snr_db": segmental,
        "maximum_absolute_error": float(np.max(np.abs(error))),
        "rms_error": float(np.sqrt(np.mean(error * error))),
    }


def _phase_pair(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
) -> dict[str, float | int | None]:
    window_size = 2048 if sample_rate >= 32000 else 512
    if len(reference) < window_size:
        return {"mae_radians": None, "rmse_radians": None,
                "circular_coherence": None, "reliable_bin_count": 0}
    hop = window_size // 4
    window = signal.windows.hann(window_size, sym=False)
    weight_sum = absolute_sum = square_sum = cosine_sum = 0.0
    reliable_count = 0
    chunk_frames = sample_rate * 10
    for start in range(0, len(reference), chunk_frames):
        stop = min(len(reference), start + chunk_frames)
        if stop - start < window_size:
            continue
        _, _, ref_stft = signal.stft(
            reference[start:stop], fs=sample_rate, window=window,
            nperseg=window_size, noverlap=window_size-hop,
            nfft=window_size, boundary=None, padded=False,
        )
        _, _, deg_stft = signal.stft(
            degraded[start:stop], fs=sample_rate, window=window,
            nperseg=window_size, noverlap=window_size-hop,
            nfft=window_size, boundary=None, padded=False,
        )
        magnitude = np.abs(ref_stft)
        threshold = np.maximum(np.max(magnitude, axis=0, keepdims=True)*1.0e-3,
                               1.0e-9)
        reliable = magnitude >= threshold
        if not np.any(reliable):
            continue
        delta = np.angle(deg_stft) - np.angle(ref_stft)
        wrapped = np.arctan2(np.sin(delta), np.cos(delta))
        weights = np.square(magnitude[reliable])
        values = wrapped[reliable]
        weight_sum += float(np.sum(weights))
        absolute_sum += float(np.sum(weights * np.abs(values)))
        square_sum += float(np.sum(weights * np.square(values)))
        cosine_sum += float(np.sum(weights * np.cos(values)))
        reliable_count += int(np.count_nonzero(reliable))
    if reliable_count == 0 or weight_sum <= 0.0:
        return {"mae_radians": None, "rmse_radians": None,
                "circular_coherence": None, "reliable_bin_count": 0}
    return {
        "mae_radians": absolute_sum / weight_sum,
        "rmse_radians": math.sqrt(square_sum / weight_sum),
        "circular_coherence": cosine_sum / weight_sum,
        "reliable_bin_count": reliable_count,
    }


def _interchannel_phase_error(
    reference_left: np.ndarray,
    reference_right: np.ndarray,
    degraded_left: np.ndarray,
    degraded_right: np.ndarray,
    sample_rate: int,
) -> dict[str, float | int | None]:
    """Compare source and degraded L/R phase differences on identical bins."""

    window_size = 2048 if sample_rate >= 32000 else 512
    if len(reference_left) < window_size:
        return {"mae_radians": None, "rmse_radians": None,
                "circular_coherence": None, "reliable_bin_count": 0}
    hop = window_size // 4
    window = signal.windows.hann(window_size, sym=False)
    weight_sum = absolute_sum = square_sum = cosine_sum = 0.0
    reliable_count = 0
    chunk_frames = sample_rate * 10
    for start in range(0, len(reference_left), chunk_frames):
        stop = min(len(reference_left), start + chunk_frames)
        if stop - start < window_size:
            continue
        spectra = []
        for samples in (
            reference_left, reference_right, degraded_left, degraded_right
        ):
            _, _, stft = signal.stft(
                samples[start:stop], fs=sample_rate, window=window,
                nperseg=window_size, noverlap=window_size-hop,
                nfft=window_size, boundary=None, padded=False,
            )
            spectra.append(stft)
        ref_l, ref_r, deg_l, deg_r = spectra
        ref_magnitude = np.minimum(np.abs(ref_l), np.abs(ref_r))
        threshold = np.maximum(
            np.max(ref_magnitude, axis=0, keepdims=True) * 1.0e-3,
            1.0e-9,
        )
        reliable = ref_magnitude >= threshold
        if not np.any(reliable):
            continue
        reference_delta = np.angle(ref_r) - np.angle(ref_l)
        degraded_delta = np.angle(deg_r) - np.angle(deg_l)
        error = degraded_delta - reference_delta
        wrapped = np.arctan2(np.sin(error), np.cos(error))
        weights = np.square(ref_magnitude[reliable])
        values = wrapped[reliable]
        weight_sum += float(np.sum(weights))
        absolute_sum += float(np.sum(weights * np.abs(values)))
        square_sum += float(np.sum(weights * np.square(values)))
        cosine_sum += float(np.sum(weights * np.cos(values)))
        reliable_count += int(np.count_nonzero(reliable))
    if reliable_count == 0 or weight_sum <= 0.0:
        return {"mae_radians": None, "rmse_radians": None,
                "circular_coherence": None, "reliable_bin_count": 0}
    return {
        "mae_radians": absolute_sum / weight_sum,
        "rmse_radians": math.sqrt(square_sum / weight_sum),
        "circular_coherence": cosine_sum / weight_sum,
        "reliable_bin_count": reliable_count,
    }


def _phase_channel_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    notes: dict[str, str],
) -> dict[str, object]:
    normalized_reference = reference.astype(np.float64) / 32768.0
    normalized_degraded = degraded.astype(np.float64) / 32768.0
    channels = []
    for channel in range(reference.shape[1]):
        phase = _phase_pair(
            normalized_reference[:, channel],
            normalized_degraded[:, channel], sample_rate,
        )
        if phase["reliable_bin_count"] == 0:
            _note(notes, f"phase.channels.{channel}", "no-reliable-bin")
        ref = normalized_reference[:, channel]
        err = ref - normalized_degraded[:, channel]
        energy = float(np.sum(ref * ref))
        if energy <= EPSILON:
            channel_snr = None
            _note(notes, f"channels.{channel}.snr_db", "silent-reference")
        else:
            channel_snr = 10.0 * math.log10(
                (energy + EPSILON) / (float(np.sum(err * err)) + EPSILON)
            )
        channels.append({"snr_db": channel_snr, "phase": phase})

    stereo = None
    if reference.shape[1] == 2:
        ref_l, ref_r = normalized_reference.T
        deg_l, deg_r = normalized_degraded.T
        ref_var = float(np.var(ref_l) * np.var(ref_r))
        deg_var = float(np.var(deg_l) * np.var(deg_r))
        if ref_var <= EPSILON:
            correlation_error = None
            _note(notes, "stereo.correlation_error", "zero-channel-variance")
        else:
            ref_corr = float(np.corrcoef(ref_l, ref_r)[0, 1])
            if deg_var <= EPSILON:
                deg_corr = 0.0
                _note(notes, "stereo.degraded_correlation",
                      "zero-variance-penalized-as-zero-correlation")
            else:
                deg_corr = float(np.corrcoef(deg_l, deg_r)[0, 1])
            correlation_error = abs(ref_corr - deg_corr)
        ref_mid, ref_side = (ref_l + ref_r) / 2.0, (ref_l - ref_r) / 2.0
        deg_mid, deg_side = (deg_l + deg_r) / 2.0, (deg_l - deg_r) / 2.0
        ref_ratio = 10.0 * math.log10(
            (float(np.sum(ref_side * ref_side)) + EPSILON)
            / (float(np.sum(ref_mid * ref_mid)) + EPSILON)
        )
        deg_ratio = 10.0 * math.log10(
            (float(np.sum(deg_side * deg_side)) + EPSILON)
            / (float(np.sum(deg_mid * deg_mid)) + EPSILON)
        )
        interchannel_phase = _interchannel_phase_error(
            ref_l, ref_r, deg_l, deg_r, sample_rate
        )
        if interchannel_phase["reliable_bin_count"] == 0:
            _note(notes, "stereo.interchannel_phase_rmse_error",
                  "no-reliable-bin")
        stereo = {
            "correlation_error": correlation_error,
            "reference_mid_side_ratio_db": ref_ratio,
            "degraded_mid_side_ratio_db": deg_ratio,
            "mid_side_ratio_error_db": abs(ref_ratio - deg_ratio),
            "interchannel_phase_error": interchannel_phase,
        }
    return {"channels": channels, "stereo": stereo}


def _speech_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    notes: dict[str, str],
) -> dict[str, float | None]:
    mono_reference = np.mean(reference.astype(np.float64) / 32768.0, axis=1)
    mono_degraded = np.mean(degraded.astype(np.float64) / 32768.0, axis=1)
    if float(np.sum(mono_reference * mono_reference)) <= EPSILON:
        _note(notes, "speech.stoi", "silent-reference")
        _note(notes, "speech.estoi", "silent-reference")
        return {"stoi": None, "estoi": None}
    try:
        from pystoi import stoi
        return {
            "stoi": float(stoi(mono_reference, mono_degraded,
                               sample_rate, extended=False)),
            "estoi": float(stoi(mono_reference, mono_degraded,
                                sample_rate, extended=True)),
        }
    except (ValueError, RuntimeError) as error:
        reason = f"pystoi-rejected:{type(error).__name__}"
        _note(notes, "speech.stoi", reason)
        _note(notes, "speech.estoi", reason)
        return {"stoi": None, "estoi": None}


def _reject_nonfinite(value: object, path: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite metric at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_nonfinite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_nonfinite(item, f"{path}.{index}")


def compute_metrics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    categories: Iterable[str],
) -> dict[str, object]:
    """Compute the frozen zero-lag S12 metric vector."""

    if (reference.dtype != np.int16 or degraded.dtype != np.int16
            or reference.ndim != 2 or reference.shape != degraded.shape
            or reference.shape[0] == 0 or sample_rate <= 0):
        raise TypeError("S12 metrics require equal non-empty frame-major PCM16")
    notes: dict[str, str] = {}
    mode = "speech" if "speech" in set(categories) else "music"
    waveform = _waveform_metrics(reference, degraded, sample_rate, notes)
    spectral = _spectral_metrics(reference, degraded, sample_rate, mode)
    if not np.any(reference):
        spectral["log_spectral_distance_db"] = None
        spectral["magnitude_cosine_similarity"] = None
        _note(notes, "spectral.log_spectral_distance_db", "silent-reference")
        _note(notes, "spectral.magnitude_cosine_similarity", "silent-reference")
    transient = transient_pre_echo_error_db(reference, degraded, sample_rate)
    if transient["onset_count"] == 0:
        _note(notes, "transient", "no-transient-onset")
    report: dict[str, object] = {
        "schema": "resonith-r216-zero-lag-metrics-1",
        "sample_rate": sample_rate,
        "channels": reference.shape[1],
        "frames": reference.shape[0],
        "alignment_lag_samples": 0,
        "waveform": waveform,
        "spectral": spectral,
        "transient": transient,
        "phase_channel": _phase_channel_metrics(
            reference, degraded, sample_rate, notes
        ),
        "notes": notes,
    }
    if mode == "speech":
        report["speech"] = _speech_metrics(
            reference, degraded, sample_rate, notes
        )
    _reject_nonfinite(report)
    return report


def _walk_numeric(value: object, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from _walk_numeric(item, path)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield prefix, float(value)


def quality_axes(report: dict[str, object]) -> dict[str, tuple[str, float]]:
    """Return comparable quality axes as path -> (min|max, value)."""

    directions = {
        "waveform.snr_db": "max", "waveform.si_sdr_db": "max",
        "waveform.segmental_snr_db": "max",
        "waveform.maximum_absolute_error": "min", "waveform.rms_error": "min",
        "spectral.log_spectral_distance_db": "min",
        "spectral.magnitude_cosine_similarity": "max",
        "spectral.log_mel_rmse": "min", "transient.mean_pre_echo_error_db": "min",
        "transient.worst_pre_echo_error_db": "min", "speech.stoi": "max",
        "speech.estoi": "max",
    }
    axes: dict[str, tuple[str, float]] = {}
    for path, value in _walk_numeric(report):
        direction = directions.get(path)
        if direction is None and path.startswith("spectral.multiresolution_stft."):
            direction = "min"
        elif direction is None and path.endswith(".snr_db"):
            direction = "max"
        elif direction is None and path.endswith((
            ".mae_radians", ".rmse_radians", ".correlation_error",
            ".mid_side_ratio_error_db",
        )):
            direction = "min"
        if direction is not None:
            axes[path] = (direction, value)
    return axes


def dominates(left: dict[str, object], right: dict[str, object]) -> bool:
    left_axes, right_axes = quality_axes(left), quality_axes(right)
    if set(left_axes) != set(right_axes):
        raise ValueError("quality applicability differs between compared points")
    strict = False
    for name in sorted(left_axes):
        direction, left_value = left_axes[name]
        right_direction, right_value = right_axes[name]
        if direction != right_direction:
            raise ValueError("quality direction mismatch")
        if direction == "max":
            if left_value < right_value:
                return False
            strict |= left_value > right_value
        else:
            if left_value > right_value:
                return False
            strict |= left_value < right_value
    return strict
