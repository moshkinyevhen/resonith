"""R-131 decoder-in-loop MFT1 predictor plus lapped Truth experiment."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from .lapped_oracle import (
    LappedEncodeResult,
    analyze_lapped_source,
    encode_lapped_analysis,
    encode_lapped_stream,
)
from .maf_source_filter_oracle import _fit_reflection_law
from .maf_typed import (
    IMPULSE_EXCITATION,
    PERIODIC_BASIS_EXCITATION,
    STOCHASTIC_EXCITATION,
    MafBasis,
    MafFilter,
    MafMix,
    MafSourceFilter,
    MafStochastic,
    pack_maf_typed,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAX_SOURCE_LIFETIMES = 4096
UNIFORM_NOISE_RMS = 18918.0
NO_MODEL = 0


@dataclass(frozen=True)
class MafTypedPrediction:
    """One native-decoded MFT1 predictor and exact encoder ledger."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


@dataclass(frozen=True)
class MafTypedTruthCandidate:
    """One complete MFT1 plus nested lapped Truth candidate."""

    payload: bytes
    reconstruction: np.ndarray
    predictor: MafTypedPrediction
    residual: LappedEncodeResult
    baseline: LappedEncodeResult
    selected_payload: bytes
    selected_reconstruction: np.ndarray
    selected_kind: str
    report: dict


def _estimate_period(
    segment: np.ndarray,
    sample_rate: int,
) -> tuple[float, float]:
    """Estimate the shortest strong periodic recurrence, not its long multiple."""

    source = segment.astype(np.float64)
    source -= float(np.mean(source))
    energy = float(source @ source)
    if source.size < 64 or energy <= source.size * 64.0 * 64.0:
        return sample_rate / 100.0, 0.0
    # MFT1 periodic Basis also represents musical partials and test tones well
    # above the vocal-pitch range. Restricting this search to 500 Hz made a
    # 1 kHz tone select an exact ten-cycle recurrence and then fit the wrong
    # sinusoid. The exact RDO fallback protects quality, but it also hides the
    # very persistence gain this experiment is intended to measure.
    minimum_lag = max(2, math.ceil(sample_rate / 5000.0))
    maximum_lag = min(source.size - 2, sample_rate // 30)
    if maximum_lag < minimum_lag:
        return sample_rate / 100.0, 0.0
    fft_size = 1 << (2 * source.size - 1).bit_length()
    spectrum = np.fft.rfft(source, fft_size)
    correlation = np.fft.irfft(
        spectrum * np.conjugate(spectrum),
        fft_size,
    )[: source.size]
    square = source * source
    prefix = np.concatenate(([0.0], np.cumsum(square)))
    lags = np.arange(minimum_lag, maximum_lag + 1, dtype=np.int64)
    current_energy = prefix[source.size - lags]
    past_energy = prefix[source.size] - prefix[lags]
    denominator = np.sqrt(
        np.maximum(current_energy * past_energy, 1.0)
    )
    normalized = correlation[lags] / denominator
    maximum = float(np.max(normalized))
    local_peaks = np.flatnonzero(
        (normalized[1:-1] >= normalized[:-2])
        & (normalized[1:-1] >= normalized[2:])
    ) + 1
    strong_floor = max(0.70, maximum * 0.90)
    strong_peaks = local_peaks[normalized[local_peaks] >= strong_floor]
    if strong_peaks.size:
        # A waveform paid once should use its fundamental recurrence whenever
        # it is nearly as predictive as a later integer-multiple recurrence.
        best_index = int(strong_peaks[0])
    else:
        best_index = int(np.argmax(normalized))
    lag = float(lags[best_index])
    score = float(normalized[best_index])
    if 0 < best_index < normalized.size - 1:
        left = float(normalized[best_index - 1])
        center = score
        right = float(normalized[best_index + 1])
        curvature = left - 2.0 * center + right
        if curvature < -1.0e-9:
            lag += max(-0.5, min(0.5, 0.5 * (left - right) / curvature))
    return lag, score


def _optimal_gain(
    source: np.ndarray,
    prediction: np.ndarray,
    initial_gain: int,
) -> int:
    target = source.astype(np.float64)
    rendered = prediction.astype(np.float64)
    energy = float(rendered @ rendered)
    if energy <= 1.0:
        return 0
    multiplier = float(target @ rendered) / energy
    return max(-32768, min(32768, int(round(initial_gain * multiplier))))


def _fit_sinusoid(
    segment: np.ndarray,
    period: float,
) -> tuple[int, int]:
    if segment.size == 0 or period <= 0.0:
        return 0, 0
    phase = 2.0 * np.pi * np.arange(segment.size, dtype=np.float64) / period
    source = segment.astype(np.float64)
    sine = float(source @ np.sin(phase))
    cosine = float(source @ np.cos(phase))
    amplitude = 2.0 * math.hypot(sine, cosine) / segment.size
    origin = math.atan2(cosine, sine) / (2.0 * np.pi)
    return (
        max(0, min(32768, int(round(amplitude)))),
        int(round(origin * (1 << 32))) & 0xFFFF_FFFF,
    )


def _identity_mix(channels: int, frames: int) -> MafMix:
    return MafMix(
        0,
        frames,
        tuple(
            tuple(32767 if output == emitter else 0 for emitter in range(channels))
            for output in range(channels)
        ),
    )


def _pack_variant(
    *,
    samples: np.ndarray,
    sample_rate: int,
    render_quantum: int,
    segment_frames: int,
    filters: tuple[MafFilter, ...],
    stochastic: tuple[MafStochastic, ...],
    modes: tuple[int, ...],
    gains: tuple[int, ...],
    periods: tuple[float, ...],
    phase_origins: tuple[int, ...],
    bases: tuple[MafBasis, ...],
) -> bytes:
    frames, channels = samples.shape
    records: list[MafSourceFilter] = []
    state = 0
    for channel in range(channels):
        for start in range(0, frames, segment_frames):
            end = min(frames, start + segment_frames)
            mode = modes[state]
            period = max(1.0, periods[state])
            if mode != NO_MODEL:
                periodic = mode == PERIODIC_BASIS_EXCITATION
                records.append(
                    MafSourceFilter(
                        channel,
                        0xFFFF if periodic else channel,
                        mode,
                        (
                            None
                            if mode == IMPULSE_EXCITATION
                            else (0 if periodic else channel)
                        ),
                        start,
                        end,
                        gains[state],
                        phase_origins[state] if periodic else 0,
                        (
                            max(
                                1,
                                min(
                                    0xFFFF_FFFF,
                                    int(round((1 << 32) / period)),
                                ),
                            )
                            if mode in {
                                IMPULSE_EXCITATION,
                                PERIODIC_BASIS_EXCITATION,
                            }
                            else 0
                        ),
                    )
                )
            state += 1
    filter_order = len(filters[0].reflection_q15) if filters else 0
    maximum_source_operations = channels * (12 + 2 * filter_order + 4)
    mix_operations = channels * (2 * channels + 2)
    return pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=frames,
        render_quantum=render_quantum,
        output_channels=channels,
        emitter_count=channels,
        filters=filters,
        stochastic=stochastic,
        sources=tuple(records),
        transients=(),
        mixes=(_identity_mix(channels, frames),),
        bases=bases,
        declared_operations_per_frame=(
            maximum_source_operations + mix_operations
        ),
    )


def _selected_grid(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    coefficients_per_frame: int,
    half_window: int,
    band_count: int,
) -> np.ndarray:
    analysis = native_decoder.analyze_lapped(
        samples,
        half_window=half_window,
        band_count=band_count,
    )
    from .lapped_oracle import LappedAnalysis

    wrapped = LappedAnalysis(
        sample_rate=sample_rate,
        samples=np.array(samples, copy=True),
        half_window=half_window,
        band_count=band_count,
        frame_count=analysis.transform_frame_count,
        fixed_transform=True,
        fixed_table_sha256=None,
        analysis_backend="native C++23 R-131 rate router",
        scales=analysis.scales,
        quantized_grid=analysis.quantized_grid,
        score_grid=analysis.score_grid,
    )
    selected = encode_lapped_analysis(
        wrapped,
        coefficients_per_frame=coefficients_per_frame,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
        emit_stream=False,
    )
    return selected.selected_coefficients


def _coefficient_proxy(
    grid: np.ndarray,
    *,
    channel: int,
    start: int,
    end: int,
    half_window: int,
) -> float:
    first = max(0, start // half_window)
    last = min(
        grid.shape[1],
        (end + half_window - 1) // half_window + 1,
    )
    values = np.abs(
        grid[channel, first:last].astype(np.float64)
    )
    return float(np.sum(np.log2(2.0 + values)))


def fit_maf_typed_prediction(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    segment_milliseconds: float = 120.0,
    filter_order: int = 10,
    render_quantum: int = 1024,
    rate_coefficients_per_frame: int = 64,
    rate_half_window: int = 512,
    rate_band_count: int = 24,
    allowed_modes: tuple[int, ...] | None = None,
) -> MafTypedPrediction:
    """Fit impulse/stochastic lifetimes and judge them in the native decoder."""

    source_view = np.asarray(samples)
    if (
        source_view.dtype != np.int16
        or source_view.ndim != 2
        or source_view.shape[0] == 0
        or not 1 <= source_view.shape[1] <= 8
    ):
        raise TypeError("typed MAF fitting requires frame-major PCM16")
    if not 1 <= filter_order <= 16:
        raise ValueError("typed MAF filter order exceeds Main")
    supported_modes = {
        IMPULSE_EXCITATION,
        STOCHASTIC_EXCITATION,
        PERIODIC_BASIS_EXCITATION,
    }
    enabled_modes = (
        supported_modes
        if allowed_modes is None
        else set(allowed_modes)
    )
    if not enabled_modes <= supported_modes:
        raise ValueError("typed MAF mode mask contains an unknown family")
    source = np.ascontiguousarray(source_view)
    frames, channels = source.shape
    minimum_segment = math.ceil(frames * channels / MAX_SOURCE_LIFETIMES)
    requested_segment = max(64, round(sample_rate * segment_milliseconds / 1000.0))
    segment_frames = max(minimum_segment, requested_segment)

    filters = tuple(
        MafFilter(
            tuple(
                int(value) << 8
                for value in _fit_reflection_law(
                    source[:, channel],
                    filter_order,
                ).reflection_q7
            )
        )
        for channel in range(channels)
    )
    fields = tuple(
        MafStochastic(None, 0, frames, 32768)
        for _ in range(channels)
    )

    periods: list[float] = []
    phase_origins: list[int] = []
    impulse_gains: list[int] = []
    noise_gains: list[int] = []
    periodic_gains: list[int] = []
    periodicities: list[float] = []
    for channel in range(channels):
        for start in range(0, frames, segment_frames):
            end = min(frames, start + segment_frames)
            segment = source[start:end, channel]
            period, periodicity = _estimate_period(segment, sample_rate)
            rms = float(
                np.sqrt(np.mean(np.square(segment.astype(np.float64))))
            )
            periods.append(period)
            periodicities.append(periodicity)
            periodic_gain, phase_origin = _fit_sinusoid(segment, period)
            periodic_gains.append(periodic_gain)
            phase_origins.append(phase_origin)
            impulse_gains.append(
                min(32767, max(0, int(round(rms * math.sqrt(period)))))
            )
            noise_gains.append(
                min(32768, max(0, int(round(rms * 32768.0 / UNIFORM_NOISE_RMS))))
            )

    impulse_modes = (IMPULSE_EXCITATION,) * len(periods)
    noise_modes = (STOCHASTIC_EXCITATION,) * len(periods)
    periodic_modes = (PERIODIC_BASIS_EXCITATION,) * len(periods)
    sine_basis = MafBasis(
        tuple(
            int(round(32767.0 * math.sin(2.0 * math.pi * index / 256.0)))
            for index in range(256)
        )
    )
    impulse_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=filters,
        stochastic=fields,
        modes=impulse_modes,
        gains=tuple(impulse_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(),
    )
    noise_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=filters,
        stochastic=fields,
        modes=noise_modes,
        gains=tuple(noise_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(),
    )
    periodic_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=(),
        stochastic=(),
        modes=periodic_modes,
        gains=tuple(periodic_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(sine_basis,),
    )
    impulse_pcm = native_decoder.decode_maf_typed(impulse_payload).samples
    noise_pcm = native_decoder.decode_maf_typed(noise_payload).samples
    periodic_pcm = native_decoder.decode_maf_typed(periodic_payload).samples

    impulse_scaled_gains: list[int] = []
    noise_scaled_gains: list[int] = []
    periodic_scaled_gains: list[int] = []
    state = 0
    for channel in range(channels):
        for start in range(0, frames, segment_frames):
            end = min(frames, start + segment_frames)
            target = source[start:end, channel]
            impulse = impulse_pcm[start:end, channel]
            noise = noise_pcm[start:end, channel]
            periodic = periodic_pcm[start:end, channel]
            impulse_gain = _optimal_gain(
                target,
                impulse,
                impulse_gains[state],
            )
            noise_gain = _optimal_gain(
                target,
                noise,
                noise_gains[state],
            )
            impulse_scaled_gains.append(impulse_gain)
            noise_scaled_gains.append(noise_gain)
            periodic_scaled_gains.append(
                _optimal_gain(
                    target,
                    periodic,
                    periodic_gains[state],
                )
            )
            state += 1

    impulse_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=filters,
        stochastic=fields,
        modes=impulse_modes,
        gains=tuple(impulse_scaled_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(),
    )
    noise_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=filters,
        stochastic=fields,
        modes=noise_modes,
        gains=tuple(noise_scaled_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(),
    )
    periodic_payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=(),
        stochastic=(),
        modes=periodic_modes,
        gains=tuple(periodic_scaled_gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(sine_basis,),
    )
    impulse_pcm = native_decoder.decode_maf_typed(impulse_payload).samples
    noise_pcm = native_decoder.decode_maf_typed(noise_payload).samples
    periodic_pcm = native_decoder.decode_maf_typed(periodic_payload).samples
    source_grid = _selected_grid(
        source,
        sample_rate,
        native_decoder=native_decoder,
        coefficients_per_frame=rate_coefficients_per_frame,
        half_window=rate_half_window,
        band_count=rate_band_count,
    )
    impulse_residual = np.clip(
        source.astype(np.int32) - impulse_pcm.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    noise_residual = np.clip(
        source.astype(np.int32) - noise_pcm.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    periodic_residual = np.clip(
        source.astype(np.int32) - periodic_pcm.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    impulse_grid = _selected_grid(
        impulse_residual,
        sample_rate,
        native_decoder=native_decoder,
        coefficients_per_frame=rate_coefficients_per_frame,
        half_window=rate_half_window,
        band_count=rate_band_count,
    )
    noise_grid = _selected_grid(
        noise_residual,
        sample_rate,
        native_decoder=native_decoder,
        coefficients_per_frame=rate_coefficients_per_frame,
        half_window=rate_half_window,
        band_count=rate_band_count,
    )
    periodic_grid = _selected_grid(
        periodic_residual,
        sample_rate,
        native_decoder=native_decoder,
        coefficients_per_frame=rate_coefficients_per_frame,
        half_window=rate_half_window,
        band_count=rate_band_count,
    )

    modes: list[int] = []
    gains: list[int] = []
    state = 0
    impulse_selected = 0
    stochastic_selected = 0
    periodic_selected = 0
    no_model_selected = 0
    record_penalty_bits = 40.0 * 8.0
    for channel in range(channels):
        for start in range(0, frames, segment_frames):
            end = min(frames, start + segment_frames)
            costs = [
                (
                    _coefficient_proxy(
                        source_grid,
                        channel=channel,
                        start=start,
                        end=end,
                        half_window=rate_half_window,
                    ),
                    NO_MODEL,
                    0,
                ),
            ]
            if IMPULSE_EXCITATION in enabled_modes:
                costs.append((
                    _coefficient_proxy(
                        impulse_grid,
                        channel=channel,
                        start=start,
                        end=end,
                        half_window=rate_half_window,
                    ) + record_penalty_bits,
                    IMPULSE_EXCITATION,
                    impulse_scaled_gains[state],
                ))
            if STOCHASTIC_EXCITATION in enabled_modes:
                costs.append((
                    _coefficient_proxy(
                        noise_grid,
                        channel=channel,
                        start=start,
                        end=end,
                        half_window=rate_half_window,
                    ) + record_penalty_bits,
                    STOCHASTIC_EXCITATION,
                    noise_scaled_gains[state],
                ))
            if PERIODIC_BASIS_EXCITATION in enabled_modes:
                costs.append((
                    _coefficient_proxy(
                        periodic_grid,
                        channel=channel,
                        start=start,
                        end=end,
                        half_window=rate_half_window,
                    ) + record_penalty_bits,
                    PERIODIC_BASIS_EXCITATION,
                    periodic_scaled_gains[state],
                ))
            _, mode, gain = min(costs, key=lambda item: (item[0], item[1]))
            modes.append(mode)
            gains.append(gain)
            if mode == IMPULSE_EXCITATION:
                impulse_selected += 1
            elif mode == STOCHASTIC_EXCITATION:
                stochastic_selected += 1
            elif mode == PERIODIC_BASIS_EXCITATION:
                periodic_selected += 1
            else:
                no_model_selected += 1
            state += 1

    source_filter_active = any(
        mode in {IMPULSE_EXCITATION, STOCHASTIC_EXCITATION}
        for mode in modes
    )
    periodic_active = any(
        mode == PERIODIC_BASIS_EXCITATION for mode in modes
    )
    payload = _pack_variant(
        samples=source,
        sample_rate=sample_rate,
        render_quantum=render_quantum,
        segment_frames=segment_frames,
        filters=filters if source_filter_active else (),
        stochastic=fields if source_filter_active else (),
        modes=tuple(modes),
        gains=tuple(gains),
        periods=tuple(periods),
        phase_origins=tuple(phase_origins),
        bases=(sine_basis,) if periodic_active else (),
    )
    native = native_decoder.decode_maf_typed(payload)
    prediction = native.samples
    residual = source.astype(np.int32) - prediction.astype(np.int32)
    report = {
        "status": "R-131 exact native MFT1 predictor; no rate claim",
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "frames": frames,
        "channels": channels,
        "sample_rate": sample_rate,
        "segment_frames": segment_frames,
        "segment_milliseconds": 1000.0 * segment_frames / sample_rate,
        "source_lifetime_count": (
            impulse_selected + stochastic_selected + periodic_selected
        ),
        "router_segment_count": len(modes),
        "filter_count": len(filters) if source_filter_active else 0,
        "stochastic_field_count": len(fields) if source_filter_active else 0,
        "basis_count": 1 if periodic_active else 0,
        "allowed_modes": sorted(enabled_modes),
        "impulse_lifetime_count": impulse_selected,
        "stochastic_lifetime_count": stochastic_selected,
        "periodic_basis_lifetime_count": periodic_selected,
        "no_model_lifetime_count": no_model_selected,
        "median_periodicity": float(np.median(periodicities)),
        "residual_rms": float(np.sqrt(np.mean(np.square(residual)))),
        "residual_clip_count": int(np.count_nonzero(
            (residual < -32768) | (residual > 32767)
        )),
        "workspace_bytes": native.workspace_bytes,
    }
    prediction.flags.writeable = False
    return MafTypedPrediction(payload, prediction, report)


def encode_maf_typed_truth_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    coefficients_per_frame: int,
    segment_milliseconds: float = 120.0,
    filter_order: int = 10,
    half_window: int = 512,
    band_count: int = 24,
    residual_budget_override: int | None = None,
    allowed_modes: tuple[int, ...] | None = None,
    residual_selection_backend: str = "energy",
    residual_frame_whitening: float = 0.0,
    residual_band_whitening: float = 0.0,
) -> MafTypedTruthCandidate:
    """Encode complete MFT1+Truth and preserve the direct lapped fallback."""

    source = np.ascontiguousarray(samples, dtype=np.int16)
    prediction = fit_maf_typed_prediction(
        source,
        sample_rate,
        native_decoder=native_decoder,
        segment_milliseconds=segment_milliseconds,
        filter_order=filter_order,
        rate_coefficients_per_frame=coefficients_per_frame,
        rate_half_window=half_window,
        rate_band_count=band_count,
        allowed_modes=allowed_modes,
    )
    difference = (
        source.astype(np.int32) - prediction.reconstruction.astype(np.int32)
    )
    clipped_residual = np.clip(difference, -32768, 32767).astype(np.int16)
    baseline = encode_lapped_stream(
        source,
        sample_rate,
        coefficients_per_frame=coefficients_per_frame,
        half_window=half_window,
        band_count=band_count,
        entropy_backend="bounded",
        transform_backend="fixed",
        density_backend="adaptive",
        native_analyzer=native_decoder,
        native_decoder=native_decoder,
    )
    baseline_error = (
        source.astype(np.int64) - baseline.reconstruction.astype(np.int64)
    )
    baseline_sse = int(np.sum(baseline_error * baseline_error))
    residual_analysis = analyze_lapped_source(
        clipped_residual,
        sample_rate,
        half_window=half_window,
        band_count=band_count,
        transform_backend="fixed",
        native_analyzer=native_decoder,
    )
    budget_candidates = sorted(
        {
            1,
            2,
            4,
            8,
            12,
            16,
            24,
            32,
            48,
            64,
            coefficients_per_frame,
        }
    )
    budget_candidates = [
        budget
        for budget in budget_candidates
        if budget <= coefficients_per_frame
    ]
    if residual_budget_override is not None:
        if not 1 <= residual_budget_override <= coefficients_per_frame:
            raise ValueError("residual budget override exceeds the candidate")
        budget_candidates = [residual_budget_override]
    candidate_options = []
    for residual_budget in budget_candidates:
        current_residual = encode_lapped_analysis(
            residual_analysis,
            coefficients_per_frame=residual_budget,
            entropy_backend="bounded",
            density_backend="adaptive",
            selection_backend=residual_selection_backend,
            frame_whitening=residual_frame_whitening,
            band_whitening=residual_band_whitening,
            native_decoder=native_decoder,
        )
        current_reconstruction = np.clip(
            prediction.reconstruction.astype(np.int32)
            + current_residual.reconstruction.astype(np.int32),
            -32768,
            32767,
        ).astype(np.int16)
        payload = pack_rsc1(
            (
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
                RSC1Section("MFT1", prediction.payload),
                RSC1Section("MRI1", current_residual.payload),
            ),
            profile=0,
            level=6,
            timebase_hz=sample_rate,
        )
        error = (
            source.astype(np.int64)
            - current_reconstruction.astype(np.int64)
        )
        candidate_options.append(
            (
                int(np.sum(error * error)),
                len(payload),
                residual_budget,
                payload,
                current_reconstruction,
                current_residual,
            )
        )
    quality_options = [
        option for option in candidate_options if option[0] <= baseline_sse
    ]
    chosen = min(
        quality_options or candidate_options,
        key=lambda option: (
            option[1] if quality_options else option[0],
            option[0],
            option[2],
        ),
    )
    (
        candidate_sse,
        _,
        selected_residual_budget,
        payload,
        reconstructed,
        residual,
    ) = chosen
    decoded_rate, decoded = decode_maf_typed_truth_candidate(
        payload,
        native_decoder=native_decoder,
    )
    if decoded_rate != sample_rate or not np.array_equal(decoded, reconstructed):
        raise RuntimeError("R-131 encoder and independent decode disagree")

    # This early gate admits only a strict byte win with no larger waveform
    # squared error. Higher-level perceptual RDO is added by the R-118 driver.
    admitted = len(payload) < len(baseline.payload) and candidate_sse <= baseline_sse
    selected_payload = payload if admitted else baseline.payload
    selected_reconstruction = reconstructed if admitted else baseline.reconstruction
    selected_kind = "mft1-truth" if admitted else "truth-fallback"
    report = {
        "status": "R-131 complete-byte fast candidate; R-118 pending",
        "candidate_bytes": len(payload),
        "baseline_bytes": len(baseline.payload),
        "byte_delta": len(payload) - len(baseline.payload),
        "candidate_sse": candidate_sse,
        "baseline_sse": baseline_sse,
        "selected_kind": selected_kind,
        "predictor": prediction.report,
        "residual_stream_bytes": len(residual.payload),
        "selected_residual_coefficients_per_frame": selected_residual_budget,
        "residual_selection_backend": residual_selection_backend,
        "residual_frame_whitening": residual_frame_whitening,
        "residual_band_whitening": residual_band_whitening,
        "tested_residual_coefficients_per_frame": budget_candidates,
        "residual_clip_count": int(np.count_nonzero(
            (difference < -32768) | (difference > 32767)
        )),
    }
    reconstructed.flags.writeable = False
    selected_reconstruction.flags.writeable = False
    return MafTypedTruthCandidate(
        payload,
        reconstructed,
        prediction,
        residual,
        baseline,
        selected_payload,
        selected_reconstruction,
        selected_kind,
        report,
    )


def decode_maf_typed_truth_candidate(
    payload: bytes,
    *,
    native_decoder,
) -> tuple[int, np.ndarray]:
    """Independently decode the exact R-131 research section envelope."""

    info = parse_rsc1(payload)
    if info.profile != 0 or info.level != 6:
        raise ValueError("unsupported typed MAF Truth profile")
    sections = {bytes(section.type_code): section.payload for section in info.sections}
    if set(sections) != {b"CONF", b"MFT1", b"MRI1"}:
        raise ValueError("non-canonical typed MAF Truth sections")
    config = unpack_conf(sections[b"CONF"])
    prediction = native_decoder.decode_maf_typed(sections[b"MFT1"])
    residual = native_decoder.decode_lapped(sections[b"MRI1"])
    if (
        prediction.sample_rate != info.timebase_hz
        or residual.sample_rate != info.timebase_hz
        or prediction.samples.shape != residual.samples.shape
        or prediction.samples.shape
            != (config.sample_count, config.output_channels)
    ):
        raise ValueError("typed MAF Truth section layout mismatch")
    output = np.clip(
        prediction.samples.astype(np.int32)
        + residual.samples.astype(np.int32),
        -32768,
        32767,
    ).astype(np.int16)
    output.flags.writeable = False
    return info.timebase_hz, output
