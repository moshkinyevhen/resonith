"""Rejected pre-audit R-184 scratch retained only for counterexample review.

The public entry points deliberately fail. R-186 through R-189 replaced this
draft with audited observation and path-proposal modules; predictor use remains
blocked until native parity and a second R-185 review.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np
from scipy import optimize, signal, sparse

from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    pack_maf_typed,
)


@dataclass(frozen=True)
class ComplexPartialFlowLanguage:
    """Finite phase-aware observation and continuation graph."""

    fft_samples: int = 1024
    hop_samples: int = 128
    minimum_peak_fraction: float = 0.012
    maximum_peaks_per_frame: int = 48
    maximum_gap_frames: int = 3
    maximum_frequency_jump_hz: float = 55.0
    maximum_relative_frequency_jump: float = 0.035
    minimum_edge_benefit: float = 0.25
    minimum_track_observations: int = 4
    maximum_exact_edges: int = 5000
    maximum_rendered_tracks: int = 24

    def __post_init__(self) -> None:
        if (
            self.fft_samples < 128
            or self.fft_samples & (self.fft_samples - 1)
            or not 1 <= self.hop_samples <= self.fft_samples // 2
            or not 0.0 < self.minimum_peak_fraction < 1.0
            or not 1 <= self.maximum_peaks_per_frame <= 512
            or not 1 <= self.maximum_gap_frames <= 16
            or not 0.0 < self.maximum_frequency_jump_hz <= 4000.0
            or not 0.0 < self.maximum_relative_frequency_jump <= 1.0
            or not 0.0 <= self.minimum_edge_benefit <= 64.0
            or not 2 <= self.minimum_track_observations <= 65535
            or not 1 <= self.maximum_exact_edges <= 1_000_000
            or not 1 <= self.maximum_rendered_tracks <= 64
        ):
            raise ValueError("invalid complex partial flow language")


@dataclass(frozen=True)
class ComplexPartialObservation:
    """One anonymous sub-bin complex spectral observation."""

    index: int
    frame_index: int
    time_sample: int
    frequency_hz: float
    amplitude: float
    phase: float
    channel_amplitudes: tuple[float, ...]
    channel_phases: tuple[float, ...]


@dataclass(frozen=True)
class ComplexPartialTrack:
    """One globally linked partial path through the complete input."""

    track_id: int
    observations: tuple[ComplexPartialObservation, ...]
    edge_benefit: float
    phase_error_radians_rms: float


@dataclass(frozen=True)
class ComplexPartialFlow:
    """Finite whole-track observation graph and selected independent paths."""

    observations: tuple[ComplexPartialObservation, ...]
    tracks: tuple[ComplexPartialTrack, ...]
    report: dict


@dataclass(frozen=True)
class ComplexPartialFlowPrediction:
    """Native-decoded independent partial trajectories before cause grouping."""

    payload: bytes
    reconstruction: np.ndarray
    flow: ComplexPartialFlow
    report: dict


@dataclass(frozen=True)
class _ContinuationEdge:
    source: int
    target: int
    benefit: float
    phase_error: float


def _wrap_phase(value: float) -> float:
    return float((value + math.pi) % (2.0 * math.pi) - math.pi)


def _sub_bin_peak(magnitude: np.ndarray, peak: int) -> float:
    if peak <= 0 or peak >= magnitude.size - 1:
        return float(peak)
    left = math.log(max(float(magnitude[peak - 1]), 1.0e-20))
    center = math.log(max(float(magnitude[peak]), 1.0e-20))
    right = math.log(max(float(magnitude[peak + 1]), 1.0e-20))
    curvature = left - 2.0 * center + right
    if curvature >= -1.0e-12:
        return float(peak)
    return float(
        peak
        + np.clip(
            0.5 * (left - right) / curvature,
            -0.5,
            0.5,
        )
    )


def _observe_complex_partials(
    samples: np.ndarray,
    sample_rate: int,
    language: ComplexPartialFlowLanguage,
) -> tuple[ComplexPartialObservation, ...]:
    spectra = []
    overlap = language.fft_samples - language.hop_samples
    for channel in range(samples.shape[1]):
        _frequency, _time, spectrum = signal.stft(
            samples[:, channel].astype(np.float64),
            fs=sample_rate,
            window="hann",
            nperseg=language.fft_samples,
            noverlap=overlap,
            boundary="zeros",
            padded=True,
        )
        spectra.append(spectrum)
    field = np.stack(spectra, axis=0)
    aggregate = np.sqrt(np.sum(np.abs(field) ** 2, axis=0))
    observations = []
    for frame_index in range(aggregate.shape[1]):
        magnitude = aggregate[:, frame_index]
        maximum = float(np.max(magnitude))
        if maximum <= 1.0e-12:
            continue
        peaks, _properties = signal.find_peaks(
            magnitude,
            height=maximum * language.minimum_peak_fraction,
        )
        if peaks.size > language.maximum_peaks_per_frame:
            order = np.argsort(
                magnitude[peaks],
                kind="stable",
            )[-language.maximum_peaks_per_frame :]
            peaks = peaks[order]
        for peak in sorted(int(value) for value in peaks):
            sub_bin = _sub_bin_peak(magnitude, peak)
            frequency_hz = sub_bin * sample_rate / language.fft_samples
            if frequency_hz <= 0.0 or frequency_hz >= sample_rate / 2.0:
                continue
            channel_values = field[:, peak, frame_index]
            channel_amplitudes = tuple(
                float(abs(value)) for value in channel_values
            )
            reference_channel = int(np.argmax(channel_amplitudes))
            observations.append(
                ComplexPartialObservation(
                    index=len(observations),
                    frame_index=frame_index,
                    time_sample=frame_index * language.hop_samples,
                    frequency_hz=frequency_hz,
                    amplitude=float(magnitude[peak]),
                    phase=float(np.angle(channel_values[reference_channel])),
                    channel_amplitudes=channel_amplitudes,
                    channel_phases=tuple(
                        float(np.angle(value)) for value in channel_values
                    ),
                )
            )
    return tuple(observations)


def _edge_between(
    source: ComplexPartialObservation,
    target: ComplexPartialObservation,
    *,
    sample_rate: int,
    language: ComplexPartialFlowLanguage,
) -> _ContinuationEdge | None:
    gap = target.frame_index - source.frame_index
    if not 1 <= gap <= language.maximum_gap_frames:
        return None
    maximum_jump = gap * max(
        language.maximum_frequency_jump_hz,
        language.maximum_relative_frequency_jump
        * max(source.frequency_hz, target.frequency_hz),
    )
    frequency_error = abs(target.frequency_hz - source.frequency_hz)
    if frequency_error > maximum_jump:
        return None
    duration = (
        target.time_sample - source.time_sample
    ) / sample_rate
    phase_errors = []
    phase_weights = []
    for source_amplitude, source_phase, target_amplitude, target_phase in zip(
        source.channel_amplitudes,
        source.channel_phases,
        target.channel_amplitudes,
        target.channel_phases,
        strict=True,
    ):
        weight = math.sqrt(max(source_amplitude * target_amplitude, 0.0))
        if weight <= 1.0e-15:
            continue
        predicted = (
            source_phase
            + 2.0
            * math.pi
            * 0.5
            * (source.frequency_hz + target.frequency_hz)
            * duration
        )
        phase_errors.append(abs(_wrap_phase(target_phase - predicted)))
        phase_weights.append(weight)
    phase_error = (
        float(np.average(phase_errors, weights=phase_weights))
        if phase_errors
        else math.pi
    )
    amplitude_error = abs(
        math.log(
            max(target.amplitude, 1.0e-15)
            / max(source.amplitude, 1.0e-15)
        )
    )
    route_error = 0.0
    if len(source.channel_amplitudes) > 1:
        source_total = max(sum(source.channel_amplitudes), 1.0e-15)
        target_total = max(sum(target.channel_amplitudes), 1.0e-15)
        route_error = float(np.mean([
            abs(
                math.log(max(target_value / target_total, 1.0e-15))
                - math.log(max(source_value / source_total, 1.0e-15))
            )
            for source_value, target_value in zip(
                source.channel_amplitudes,
                target.channel_amplitudes,
                strict=True,
            )
        ]))
    benefit = (
        9.0
        - 4.5 * frequency_error / max(maximum_jump, 1.0e-12)
        - 2.5 * phase_error / math.pi
        - 0.8 * min(amplitude_error, 6.0)
        - 0.7 * min(route_error, 6.0)
        - 1.2 * (gap - 1)
    )
    if benefit < language.minimum_edge_benefit:
        return None
    return _ContinuationEdge(
        source=source.index,
        target=target.index,
        benefit=benefit,
        phase_error=phase_error,
    )


def _continuation_edges(
    observations: tuple[ComplexPartialObservation, ...],
    *,
    sample_rate: int,
    language: ComplexPartialFlowLanguage,
) -> tuple[_ContinuationEdge, ...]:
    by_frame: dict[int, list[ComplexPartialObservation]] = {}
    for observation in observations:
        by_frame.setdefault(observation.frame_index, []).append(observation)
    edges = []
    for source in observations:
        for gap in range(1, language.maximum_gap_frames + 1):
            for target in by_frame.get(source.frame_index + gap, ()):
                edge = _edge_between(
                    source,
                    target,
                    sample_rate=sample_rate,
                    language=language,
                )
                if edge is not None:
                    edges.append(edge)
    edges.sort(key=lambda item: (item.source, item.target))
    return tuple(edges)


def _select_edges_exact(
    observation_count: int,
    edges: tuple[_ContinuationEdge, ...],
) -> tuple[_ContinuationEdge, ...]:
    row_indices = []
    column_indices = []
    values = []
    for edge_index, edge in enumerate(edges):
        row_indices.extend((edge.source, observation_count + edge.target))
        column_indices.extend((edge_index, edge_index))
        values.extend((1.0, 1.0))
    constraints = sparse.coo_matrix(
        (values, (row_indices, column_indices)),
        shape=(2 * observation_count, len(edges)),
    ).tocsr()
    result = optimize.milp(
        c=-np.array([edge.benefit for edge in edges], dtype=np.float64),
        integrality=np.ones(len(edges), dtype=np.uint8),
        bounds=optimize.Bounds(0.0, 1.0),
        constraints=optimize.LinearConstraint(
            constraints,
            0.0,
            1.0,
        ),
        options={"presolve": True},
    )
    if not result.success or result.x is None:
        raise RuntimeError("exact complex-partial flow solver failed")
    return tuple(
        edge
        for edge, selected in zip(edges, result.x, strict=True)
        if selected >= 0.5
    )


def _select_edges_bounded(
    edges: tuple[_ContinuationEdge, ...],
) -> tuple[_ContinuationEdge, ...]:
    """Deterministic sparse matching fallback for large proposal graphs."""

    incoming = set()
    outgoing = set()
    selected = []
    for edge in sorted(
        edges,
        key=lambda item: (
            -item.benefit,
            item.phase_error,
            item.source,
            item.target,
        ),
    ):
        if edge.source in outgoing or edge.target in incoming:
            continue
        outgoing.add(edge.source)
        incoming.add(edge.target)
        selected.append(edge)
    selected.sort(key=lambda item: (item.source, item.target))
    return tuple(selected)


def _tracks_from_edges(
    observations: tuple[ComplexPartialObservation, ...],
    selected_edges: tuple[_ContinuationEdge, ...],
    minimum_observations: int,
) -> tuple[ComplexPartialTrack, ...]:
    successor = {edge.source: edge for edge in selected_edges}
    predecessor = {edge.target: edge for edge in selected_edges}
    starts = sorted(
        source
        for source in successor
        if source not in predecessor
    )
    tracks = []
    for start in starts:
        indices = [start]
        benefits = []
        phase_errors = []
        cursor = start
        while cursor in successor:
            edge = successor[cursor]
            benefits.append(edge.benefit)
            phase_errors.append(edge.phase_error)
            cursor = edge.target
            indices.append(cursor)
        if len(indices) < minimum_observations:
            continue
        tracks.append(
            ComplexPartialTrack(
                track_id=len(tracks),
                observations=tuple(observations[index] for index in indices),
                edge_benefit=float(sum(benefits)),
                phase_error_radians_rms=float(
                    math.sqrt(np.mean(np.square(phase_errors)))
                ),
            )
        )
    tracks.sort(
        key=lambda track: (
            track.observations[0].time_sample,
            track.observations[0].frequency_hz,
            -len(track.observations),
        )
    )
    return tuple(
        ComplexPartialTrack(
            track_id=index,
            observations=track.observations,
            edge_benefit=track.edge_benefit,
            phase_error_radians_rms=track.phase_error_radians_rms,
        )
        for index, track in enumerate(tracks)
    )


def infer_complex_partial_flow(
    samples: np.ndarray,
    sample_rate: int,
    *,
    language: ComplexPartialFlowLanguage = ComplexPartialFlowLanguage(),
) -> ComplexPartialFlow:
    """Reject use of the pre-audit flow draft."""

    raise RuntimeError(
        "R-184 scratch is quarantined; use complex_partial_analyzer and "
        "complex_partial_tracker for non-predictive evidence"
    )
    # The rejected implementation below remains for audit archaeology.
    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("complex partial flow requires frame-major PCM16")
    observations = _observe_complex_partials(source, sample_rate, language)
    edges = _continuation_edges(
        observations,
        sample_rate=sample_rate,
        language=language,
    )
    if not edges:
        selected_edges = ()
        solver = "empty"
    elif len(edges) <= language.maximum_exact_edges:
        selected_edges = _select_edges_exact(len(observations), edges)
        solver = "exact-binary-flow"
    else:
        selected_edges = _select_edges_bounded(edges)
        solver = "deterministic-bounded-matching"
    tracks = _tracks_from_edges(
        observations,
        selected_edges,
        language.minimum_track_observations,
    )
    tracked_observations = sum(len(track.observations) for track in tracks)
    return ComplexPartialFlow(
        observations=observations,
        tracks=tracks,
        report={
            "schema": "resonith-r184-global-complex-partial-flow-1",
            "status": "encoder proposer; actual complete-program RDO pending",
            "semantic_source_classes": False,
            "fundamental_required": False,
            "phase_authoritative": True,
            "observation_count": len(observations),
            "continuation_edge_count": len(edges),
            "selected_edge_count": len(selected_edges),
            "track_count": len(tracks),
            "tracked_observation_count": tracked_observations,
            "tracked_observation_fraction": (
                tracked_observations / len(observations)
                if observations
                else 0.0
            ),
            "solver": solver,
            "mean_track_phase_error_radians": (
                float(np.mean([
                    track.phase_error_radians_rms for track in tracks
                ]))
                if tracks
                else None
            ),
        },
    )


def _cosine_basis(sample_count: int = 256) -> np.ndarray:
    return np.rint(
        32767.0
        * np.cos(
            2.0 * np.pi * np.arange(sample_count, dtype=np.float64)
            / sample_count
        )
    ).astype(np.int64)


def fit_complex_partial_flow_prediction(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    language: ComplexPartialFlowLanguage = ComplexPartialFlowLanguage(),
) -> ComplexPartialFlowPrediction:
    """Reject predictor compilation from the pre-audit flow draft."""

    raise RuntimeError(
        "complex-partial prediction is blocked pending native parity and "
        "a second R-185 audit"
    )
    # The rejected implementation below remains for audit archaeology.
    source = np.ascontiguousarray(samples, dtype=np.int16)
    flow = infer_complex_partial_flow(
        source,
        sample_rate,
        language=language,
    )
    maximum_tracks = min(
        language.maximum_rendered_tracks,
        64 // source.shape[1],
    )
    ranked = sorted(
        flow.tracks,
        key=lambda track: (
            -sum(
                observation.amplitude**2
                for observation in track.observations
            ),
            track.track_id,
        ),
    )[:maximum_tracks]
    ranked.sort(key=lambda track: track.track_id)
    basis = _cosine_basis()
    track_count = max(1, len(ranked))
    instances = []
    for rendered_track_id, track in enumerate(ranked):
        for observation_index, observation in enumerate(track.observations):
            next_observation = (
                track.observations[observation_index + 1]
                if observation_index + 1 < len(track.observations)
                else observation
            )
            gap_frames = max(
                1,
                next_observation.frame_index - observation.frame_index,
            )
            sample_count = min(
                source.shape[0] - observation.time_sample,
                gap_frames * language.hop_samples,
            )
            if sample_count < 3:
                continue
            start_step = int(round(
                basis.size
                * observation.frequency_hz
                * WARP_ONE_Q16
                / sample_rate
            ))
            end_step = int(round(
                basis.size
                * next_observation.frequency_hz
                * WARP_ONE_Q16
                / sample_rate
            ))
            for channel in range(source.shape[1]):
                gain = int(np.clip(
                    round(2.0 * observation.channel_amplitudes[channel]),
                    -32768,
                    32767,
                ))
                end_gain = int(np.clip(
                    round(2.0 * next_observation.channel_amplitudes[channel]),
                    -32768,
                    32767,
                ))
                if max(abs(gain), abs(end_gain)) < 2:
                    continue
                phase = observation.channel_phases[channel]
                source_position = int(round(
                    (phase / (2.0 * math.pi) % 1.0)
                    * basis.size
                    * WARP_ONE_Q16
                ))
                instances.append(
                    MafBasisWarpInstance(
                        emitter_id=channel * track_count + rendered_track_id,
                        basis_id=0,
                        start=observation.time_sample,
                        sample_count=sample_count,
                        source_position_q16=source_position,
                        source_step_q16=start_step,
                        gain_q15=gain,
                        circular=True,
                        end_source_step_q16=(
                            end_step if end_step != start_step else None
                        ),
                        end_gain_q15=(
                            end_gain if end_gain != gain else None
                        ),
                    )
                )
    emitter_count = source.shape[1] * track_count
    matrix = tuple(
        tuple(
            32767 if emitter // track_count == output else 0
            for emitter in range(emitter_count)
        )
        for output in range(source.shape[1])
    )
    payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=source.shape[0],
        render_quantum=min(4096, source.shape[0]),
        output_channels=source.shape[1],
        emitter_count=emitter_count,
        mixes=(MafMix(0, source.shape[0], matrix),),
        bases=(MafBasis(tuple(int(value) for value in basis)),),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=max(
            256,
            emitter_count * 32,
        ),
    )
    reconstruction = native_decoder.decode_maf_typed(payload).samples
    difference = source.astype(np.int64) - reconstruction.astype(np.int64)
    reconstruction.flags.writeable = False
    return ComplexPartialFlowPrediction(
        payload=payload,
        reconstruction=reconstruction,
        flow=flow,
        report={
            **flow.report,
            "schema": "resonith-r184-complex-partial-flow-prediction-1",
            "status": "native-decoded independent paths; R-182 RDO pending",
            "rendered_track_count": len(ranked),
            "warp_instance_count": len(instances),
            "predictor_bytes": len(payload),
            "predictor_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_rms": float(np.sqrt(np.mean(
                difference.astype(np.float64) ** 2
            ))),
            "workspace_bytes": native_decoder.decode_maf_typed(
                payload
            ).workspace_bytes,
        },
    )
