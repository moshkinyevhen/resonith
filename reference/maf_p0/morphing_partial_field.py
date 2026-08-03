"""R-180 anonymous morphing complex-partial field compiler."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from .coherent_partial_bundle import (
    CausalLaneField,
    CoherentPartialLanguage,
    PartialBundleObservation,
    infer_causal_lane_field,
)
from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    pack_maf_typed,
)
from .warp_dictionary import _apply_gain, _render_basis


@dataclass(frozen=True)
class MorphingPartialLanguage:
    """Finite vector-state law for one unnamed point-cause proposal."""

    maximum_partials: int = 12
    minimum_relative_amplitude: float = 0.015
    maximum_event_normalized_error: float = 0.95
    maximum_instances: int = 65536
    maximum_point_causes: int = 8
    phase_locked: bool = True

    def __post_init__(self) -> None:
        if (
            not 1 <= self.maximum_partials <= 32
            or not 0.0 <= self.minimum_relative_amplitude <= 1.0
            or not 0.0 < self.maximum_event_normalized_error <= 4.0
            or not 1 <= self.maximum_instances <= 262144
            or not 1 <= self.maximum_point_causes <= 32
        ):
            raise ValueError("invalid morphing partial language")


@dataclass(frozen=True)
class MorphingPartialPrediction:
    """Native-decoded vector partial-frequency/shape trajectory predictor."""

    payload: bytes
    reconstruction: np.ndarray
    causal_field: CausalLaneField
    report: dict


@dataclass(frozen=True)
class _PartialEvent:
    channel: int
    emitter_id: int
    start: int
    sample_count: int
    partial_index: int
    source_position_q16: int
    start_step_q16: int
    end_step_q16: int
    gain_q15: int
    local_saving: float


def _selected_tracks(
    causal_field: CausalLaneField,
    maximum_point_causes: int,
) -> tuple[tuple[PartialBundleObservation, ...], ...]:
    rows = []
    for basis_index, basis in enumerate(causal_field.bases):
        observations = tuple(sorted(
            basis.observations,
            key=lambda item: item.frame_index,
        ))
        if not observations:
            continue
        energy = sum(
            observation.gain**2 * observation.harmonic_fraction
            for observation in observations
        )
        rows.append(
            (
                -energy,
                observations[0].frame_index,
                basis_index,
                observations,
            )
        )
    rows.sort()
    return tuple(
        row[3] for row in rows[:maximum_point_causes]
    )


def _cosine_basis(sample_count: int = 16) -> np.ndarray:
    return np.rint(
        32767.0
        * np.cos(
            2.0 * np.pi * np.arange(sample_count, dtype=np.float64)
            / sample_count
        )
    ).astype(np.int64)


def _partial_frequency(
    observation: PartialBundleObservation,
    partial_index: int,
) -> float:
    offset = (
        observation.frequency_offsets_hz[partial_index]
        if partial_index < len(observation.frequency_offsets_hz)
        else 0.0
    )
    return max(
        0.0,
        (partial_index + 1) * observation.fundamental_hz + offset,
    )


def _partial_phase(
    observation: PartialBundleObservation,
    partial_index: int,
    channel: int,
) -> float:
    if (
        channel < len(observation.channel_partial_phases)
        and partial_index
        < len(observation.channel_partial_phases[channel])
    ):
        return observation.channel_partial_phases[channel][partial_index]
    relative = (
        observation.relative_phases[partial_index]
        if partial_index < len(observation.relative_phases)
        else 0.0
    )
    return (
        (partial_index + 1) * observation.phase_anchor + relative
    )


def _partial_amplitude(
    observation: PartialBundleObservation,
    partial_index: int,
) -> float:
    if partial_index >= len(observation.amplitude_ratios):
        return 0.0
    return max(0.0, observation.amplitude_ratios[partial_index])


def fit_morphing_partial_prediction(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    partial_language: CoherentPartialLanguage = CoherentPartialLanguage(),
    language: MorphingPartialLanguage = MorphingPartialLanguage(),
) -> MorphingPartialPrediction:
    """Fit independent partial frequency, phase, and shape laws per event."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("morphing partial field requires frame-major PCM16")
    causal_field = infer_causal_lane_field(
        source,
        sample_rate=sample_rate,
        language=partial_language,
    )
    tracks = _selected_tracks(
        causal_field,
        language.maximum_point_causes,
    )
    basis = _cosine_basis()
    track_count = max(1, len(tracks))
    partials_per_track = min(
        language.maximum_partials,
        64 // (source.shape[1] * track_count),
    )
    if partials_per_track < 1:
        raise ValueError("morphing partial emitter layout exceeds MFT1 bounds")
    observations_by_frame: dict[
        int,
        list[
            tuple[
                int,
                PartialBundleObservation,
                PartialBundleObservation,
            ]
        ],
    ] = {}
    for track_id, track in enumerate(tracks):
        for observation_index, observation in enumerate(track):
            next_observation = (
                track[observation_index + 1]
                if (
                    observation_index + 1 < len(track)
                    and track[observation_index + 1].frame_index
                    == observation.frame_index + 1
                )
                else observation
            )
            observations_by_frame.setdefault(
                observation.frame_index,
                [],
            ).append((track_id, observation, next_observation))
    proposed_events: list[_PartialEvent] = []
    event_errors = []
    modeled_events = 0
    for frame_index in sorted(observations_by_frame):
        frame_observations = observations_by_frame[frame_index]
        start = frame_index * partial_language.hop_samples
        end = min(
            source.shape[0],
            start + partial_language.hop_samples,
        )
        count = end - start
        if count < 3:
            continue
        for channel in range(source.shape[1]):
            waveforms = []
            parameters = []
            for (
                track_id,
                observation,
                next_observation,
            ) in frame_observations:
                ranked = sorted(
                    range(
                        min(
                            partials_per_track,
                            len(observation.amplitude_ratios),
                        )
                    ),
                    key=lambda partial: (
                        -_partial_amplitude(observation, partial),
                        partial,
                    ),
                )
                for partial_index in ranked:
                    if (
                        _partial_amplitude(observation, partial_index)
                        < language.minimum_relative_amplitude
                        or _partial_frequency(observation, partial_index)
                        >= sample_rate / 2.0
                    ):
                        continue
                    start_frequency = _partial_frequency(
                        observation,
                        partial_index,
                    )
                    end_frequency = _partial_frequency(
                        next_observation,
                        partial_index,
                    )
                    start_step = int(round(
                        basis.size
                        * start_frequency
                        * WARP_ONE_Q16
                        / sample_rate
                    ))
                    end_step = int(round(
                        basis.size
                        * end_frequency
                        * WARP_ONE_Q16
                        / sample_rate
                    ))
                    if (
                        not 0 <= start_step <= 8 * WARP_ONE_Q16
                        or not 0 <= end_step <= 8 * WARP_ONE_Q16
                    ):
                        continue
                    phase = _partial_phase(
                        observation,
                        partial_index,
                        channel,
                    )
                    source_position = int(round(
                        (phase / (2.0 * math.pi) % 1.0)
                        * basis.size
                        * WARP_ONE_Q16
                    ))
                    waveform = _render_basis(
                        basis,
                        count,
                        source_position,
                        start_step,
                        end_step if count >= 3 else None,
                    )
                    waveforms.append(waveform.astype(np.float64))
                    parameters.append(
                        (
                            track_id,
                            partial_index,
                            source_position,
                            start_step,
                            end_step,
                        )
                    )
            if not waveforms:
                continue
            design = np.stack(waveforms, axis=1)
            target = causal_field.coherent_harmonic[
                start:end,
                channel,
            ].astype(np.float64)
            gains, _residuals, _rank, _singular = np.linalg.lstsq(
                design,
                target,
                rcond=1.0e-6,
            )
            gains_q15 = np.clip(
                np.rint(gains * 32768.0),
                -32768,
                32768,
            ).astype(np.int64)
            rendered = np.zeros(count, dtype=np.int64)
            active = []
            for waveform, parameters_row, gain_q15 in zip(
                waveforms,
                parameters,
                gains_q15,
                strict=True,
            ):
                if abs(int(gain_q15)) < 2:
                    continue
                integer_waveform = np.rint(waveform).astype(np.int64)
                rendered += _apply_gain(
                    integer_waveform,
                    int(gain_q15),
                    None,
                )
                active.append((parameters_row, int(gain_q15)))
            if not active:
                continue
            target64 = np.rint(target).astype(np.int64)
            zero_error = int(target64 @ target64)
            error = target64 - rendered
            modeled_error = int(error @ error)
            normalized = modeled_error / max(1, zero_error)
            if (
                modeled_error >= zero_error
                or normalized > language.maximum_event_normalized_error
            ):
                continue
            saving = float(zero_error - modeled_error) / len(active)
            for (
                track_id,
                partial_index,
                source_position,
                start_step,
                end_step,
            ), gain_q15 in active:
                proposed_events.append(
                    _PartialEvent(
                        channel=channel,
                        emitter_id=(
                            channel
                            * track_count
                            * partials_per_track
                            + track_id * partials_per_track
                            + partial_index
                        ),
                        start=start,
                        sample_count=count,
                        partial_index=partial_index,
                        source_position_q16=source_position,
                        start_step_q16=start_step,
                        end_step_q16=end_step,
                        gain_q15=gain_q15,
                        local_saving=saving,
                    )
                )
            event_errors.append(normalized)
            modeled_events += 1

    proposed_events.sort(
        key=lambda item: (
            -item.local_saving,
            item.start,
            item.channel,
            item.partial_index,
        )
    )
    retained = proposed_events[: language.maximum_instances]
    retained.sort(
        key=lambda item: (
            item.start,
            item.channel,
            item.partial_index,
        )
    )
    instances = tuple(
        MafBasisWarpInstance(
            emitter_id=event.emitter_id,
            basis_id=0,
            start=event.start,
            sample_count=event.sample_count,
            source_position_q16=event.source_position_q16,
            source_step_q16=event.start_step_q16,
            gain_q15=event.gain_q15,
            circular=True,
            end_source_step_q16=(
                event.end_step_q16
                if event.end_step_q16 != event.start_step_q16
                else None
            ),
        )
        for event in retained
    )
    channels = source.shape[1]
    emitter_count = channels * track_count * partials_per_track
    emitters_per_channel = track_count * partials_per_track
    matrix = tuple(
        tuple(
            (
                32767
                if emitter // emitters_per_channel == output
                else 0
            )
            for emitter in range(emitter_count)
        )
        for output in range(channels)
    )
    payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=source.shape[0],
        render_quantum=min(4096, source.shape[0]),
        output_channels=channels,
        emitter_count=emitter_count,
        mixes=(MafMix(0, source.shape[0], matrix),),
        bases=(MafBasis(tuple(int(value) for value in basis)),),
        basis_warp_instances=instances,
        declared_operations_per_frame=max(
            256,
            32 * partials_per_track * track_count * channels,
        ),
    )
    native = native_decoder.decode_maf_typed(payload)
    reconstruction = native.samples
    residual = source.astype(np.int64) - reconstruction.astype(np.int64)
    reconstruction.flags.writeable = False
    return MorphingPartialPrediction(
        payload=payload,
        reconstruction=reconstruction,
        causal_field=causal_field,
        report={
            "schema": "resonith-r180-morphing-partial-field-1",
            "status": "native-decoded vector-state predictor; R-179 RDO pending",
            "semantic_source_classes": False,
            "point_cause_state": (
                "per-partial frequency, detuning, phase, amplitude, and shape"
            ),
            "observation_count": sum(len(track) for track in tracks),
            "point_cause_track_count": len(tracks),
            "modeled_event_count": modeled_events,
            "partial_instance_count": len(instances),
            "maximum_partials": language.maximum_partials,
            "active_partials_per_track": partials_per_track,
            "mean_event_normalized_error": (
                float(np.mean(event_errors)) if event_errors else None
            ),
            "predictor_bytes": len(payload),
            "predictor_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_rms": float(np.sqrt(
                np.mean(residual.astype(np.float64) ** 2)
            )),
            "workspace_bytes": native.workspace_bytes,
        },
    )
