"""R-177 anonymous coherent-partial Basis and long trajectory compiler."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np

from .coherent_partial_bundle import (
    CausalLaneField,
    CoherentPartialBasis,
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
from .warp_dictionary import (
    _apply_gain,
    _fit_gain_law,
    _render_basis,
    _source_positions_q16,
)


@dataclass(frozen=True)
class PartialBasisTrajectoryPrediction:
    """Native-decoded anonymous partial-Basis trajectory predictor."""

    payload: bytes
    reconstruction: np.ndarray
    causal_field: CausalLaneField
    report: dict


def _basis_waveform(
    basis: CoherentPartialBasis,
    *,
    sample_count: int,
) -> np.ndarray:
    position = (
        2.0 * np.pi * np.arange(sample_count, dtype=np.float64)
        / sample_count
    )
    waveform = np.zeros(sample_count, dtype=np.float64)
    for partial_index, (amplitude, phase) in enumerate(
        zip(
            basis.amplitude_ratios,
            basis.relative_phases,
            strict=True,
        ),
        start=1,
    ):
        if amplitude <= 1.0e-9:
            continue
        waveform += float(amplitude) * np.cos(
            partial_index * position + float(phase)
        )
    peak = max(float(np.max(np.abs(waveform))), 1.0e-12)
    return np.clip(
        np.rint(waveform * (32767.0 / peak)),
        -32768,
        32767,
    ).astype(np.int64)


def _observed_basis_waveform(
    lane_target: np.ndarray,
    *,
    sample_rate: int,
    emitter_id: int,
    basis: CoherentPartialBasis,
    hop_samples: int,
    minimum_samples: int,
) -> np.ndarray:
    """Cache one real unnamed acoustic cycle instead of a semantic template."""

    representative = max(
        basis.observations,
        key=lambda item: (
            item.harmonic_fraction,
            item.gain,
            -item.frame_index,
        ),
    )
    period = max(
        2,
        int(round(sample_rate / representative.fundamental_hz)),
    )
    cycles = max(1, min(4, math.ceil(minimum_samples / period)))
    sample_count = min(8 * 2048, period * cycles)
    center = representative.frame_index * hop_samples
    start = center - sample_count // 2
    indices = np.clip(
        np.arange(start, start + sample_count, dtype=np.int64),
        0,
        lane_target.shape[0] - 1,
    )
    waveform = lane_target[indices, emitter_id].astype(np.float64)
    waveform -= float(np.mean(waveform))
    peak = float(np.max(np.abs(waveform)))
    if peak < 1.0:
        return _basis_waveform(basis, sample_count=max(32, sample_count))
    return np.clip(
        np.rint(waveform * (32767.0 / peak)),
        -32768,
        32767,
    ).astype(np.int64)


def _labelled_observations(
    bases: tuple[CoherentPartialBasis, ...],
) -> list[tuple[PartialBundleObservation, int]]:
    labelled = [
        (observation, basis_id)
        for basis_id, basis in enumerate(bases)
        for observation in basis.observations
    ]
    labelled.sort(key=lambda item: item[0].frame_index)
    return labelled


def _trajectory_runs(
    labelled: list[tuple[PartialBundleObservation, int]],
    *,
    maximum_observations: int,
    minimum_hold_frames: int,
) -> list[tuple[int, tuple[PartialBundleObservation, ...]]]:
    if not labelled:
        return []
    raw_runs = []
    start = 0
    for index in range(1, len(labelled) + 1):
        boundary = index == len(labelled)
        if not boundary:
            previous, previous_basis = labelled[index - 1]
            current, current_basis = labelled[index]
            boundary = (
                current.frame_index != previous.frame_index + 1
                or current_basis != previous_basis
            )
        if boundary:
            raw_runs.append(labelled[start:index])
            start = index

    # Short state flicker is encoder uncertainty, not a physical source event.
    # Merge it into an adjacent anonymous state before creating trajectories.
    merged = []
    for run in raw_runs:
        if (
            merged
            and len(run) < minimum_hold_frames
            and run[0][0].frame_index
            == merged[-1][-1][0].frame_index + 1
        ):
            previous_basis = merged[-1][0][1]
            merged[-1].extend(
                (observation, previous_basis)
                for observation, _basis_id in run
            )
        else:
            merged.append(list(run))

    trajectories = []
    for run in merged:
        basis_counts = {}
        for _observation, basis_id in run:
            basis_counts[basis_id] = basis_counts.get(basis_id, 0) + 1
        basis_id = min(
            basis_counts,
            key=lambda item: (-basis_counts[item], item),
        )
        observations = [item[0] for item in run]
        for begin in range(0, len(observations), maximum_observations):
            chunk = tuple(
                observations[begin : begin + maximum_observations]
            )
            trajectories.append((basis_id, chunk))
    return trajectories


def _fit_piecewise_instances(
    source: np.ndarray,
    *,
    sample_rate: int,
    basis: np.ndarray,
    basis_id: int,
    emitter_id: int,
    observations: tuple[PartialBundleObservation, ...],
    hop_samples: int,
    phase_candidates: int,
    taper_boundaries: bool,
    boundary_taper_samples: int,
    track_observation_phase: bool,
) -> tuple[tuple[MafBasisWarpInstance, ...], float] | None:
    """Fit one continuous phase state with observation-rate numeric laws."""

    start = observations[0].frame_index * hop_samples
    end = min(
        source.shape[0],
        (observations[-1].frame_index + 1) * hop_samples,
    )
    sample_count = end - start
    if sample_count < 64 or sample_count > 65535:
        return None

    steps = tuple(
        int(round(
            basis.size
            * observation.fundamental_hz
            * WARP_ONE_Q16
            / sample_rate
        ))
        for observation in observations
    )
    if any(
        not -8 * WARP_ONE_Q16 <= step <= 8 * WARP_ONE_Q16
        for step in steps
    ):
        return None

    first_count = min(hop_samples, sample_count)
    first_end_step = steps[1] if len(steps) > 1 else steps[0]
    base_position = int(round(
        (
            observations[0].phase_anchor / (2.0 * math.pi)
            % 1.0
        )
        * basis.size
        * WARP_ONE_Q16
    ))
    first_target = source[
        start : start + first_count,
        emitter_id,
    ].astype(np.int64)
    best_probe = None
    for phase_index in range(phase_candidates):
        source_position = (
            base_position
            + phase_index
            * basis.size
            * WARP_ONE_Q16
            // phase_candidates
        ) % (basis.size * WARP_ONE_Q16)
        probe = _render_basis(
            basis,
            first_count,
            source_position,
            steps[0],
            first_end_step if first_count >= 3 else None,
        )
        denominator = max(1, int(probe @ probe))
        correlation = abs(int(probe @ first_target))
        key = (-correlation * correlation / denominator, phase_index)
        if best_probe is None or key < best_probe[0]:
            best_probe = key, source_position
    assert best_probe is not None
    source_position = best_probe[1]

    segment_rows = []
    cursor = start
    for observation_index, observation in enumerate(observations):
        next_cursor = min(
            end,
            (
                observations[observation_index + 1].frame_index * hop_samples
                if observation_index + 1 < len(observations)
                else (observation.frame_index + 1) * hop_samples
            ),
        )
        count = next_cursor - cursor
        if count < 2:
            continue
        start_step = steps[observation_index]
        end_step = (
            steps[observation_index + 1]
            if observation_index + 1 < len(observations)
            else start_step
        )
        target = source[cursor:next_cursor, emitter_id]
        if track_observation_phase and observation_index:
            phase_base = int(round(
                (
                    observation.phase_anchor / (2.0 * math.pi)
                    % 1.0
                )
                * basis.size
                * WARP_ONE_Q16
            ))
            candidates = {int(source_position)}
            candidates.update(
                (
                    phase_base
                    + phase_index
                    * basis.size
                    * WARP_ONE_Q16
                    // phase_candidates
                ) % (basis.size * WARP_ONE_Q16)
                for phase_index in range(phase_candidates)
            )
            best_position = None
            for candidate_position in sorted(candidates):
                candidate_waveform = _render_basis(
                    basis,
                    count,
                    candidate_position,
                    start_step,
                    end_step if count >= 3 else None,
                )
                gain, end_gain, error = _fit_gain_law(
                    candidate_waveform,
                    target,
                )
                key = (
                    error,
                    candidate_position != source_position,
                    candidate_position,
                )
                if best_position is None or key < best_position[0]:
                    best_position = (
                        key,
                        candidate_position,
                        candidate_waveform,
                        gain,
                        end_gain,
                    )
            assert best_position is not None
            (
                _key,
                source_position,
                waveform,
                gain,
                end_gain,
            ) = best_position
        else:
            waveform = _render_basis(
                basis,
                count,
                source_position,
                start_step,
                end_step if count >= 3 else None,
            )
            gain, end_gain, _error = _fit_gain_law(waveform, target)
        if end_gain is None:
            end_gain = gain
        positions = _source_positions_q16(
            count,
            source_position,
            start_step,
            end_step if count >= 3 else None,
        )
        segment_rows.append(
            (
                cursor,
                count,
                source_position,
                start_step,
                end_step,
                waveform,
                gain,
                end_gain,
            )
        )
        source_position = int(positions[-1] + end_step)
        cursor = next_cursor

    if not segment_rows:
        return None

    # Average independently fitted gains at shared boundaries. This keeps the
    # rendered cause continuous without inventing a semantic state change.
    boundary_gains = [segment_rows[0][6]]
    for previous, current in zip(
        segment_rows[:-1],
        segment_rows[1:],
        strict=True,
    ):
        boundary_gains.append(
            int(round((previous[7] + current[6]) / 2.0))
        )
    boundary_gains.append(segment_rows[-1][7])
    if taper_boundaries:
        boundary_gains[0] = 0
        boundary_gains[-1] = 0

    instances = []
    rendered_parts = []
    for segment_index, row in enumerate(segment_rows):
        (
            cursor,
            count,
            position,
            start_step,
            end_step,
            waveform,
            _gain,
            _end_gain,
        ) = row
        start_gain = boundary_gains[segment_index]
        end_gain = boundary_gains[segment_index + 1]
        rendered_parts.append(_apply_gain(waveform, start_gain, end_gain))
        instances.append(
            MafBasisWarpInstance(
                emitter_id=emitter_id,
                basis_id=basis_id,
                start=cursor,
                sample_count=count,
                source_position_q16=position,
                source_step_q16=start_step,
                gain_q15=start_gain,
                circular=True,
                end_source_step_q16=(
                    end_step if end_step != start_step else None
                ),
                end_gain_q15=(
                    end_gain if end_gain != start_gain else None
                ),
            )
        )

    rendered = np.concatenate(rendered_parts)
    target = source[start : start + rendered.size, emitter_id].astype(np.int64)
    error = target - rendered
    target_energy = max(1, int(target @ target))
    normalized_error = float(error @ error) / target_energy
    return tuple(instances), normalized_error


def _fit_instance(
    source: np.ndarray,
    *,
    sample_rate: int,
    basis: np.ndarray,
    basis_id: int,
    emitter_id: int,
    observations: tuple[PartialBundleObservation, ...],
    hop_samples: int,
    phase_candidates: int,
    taper_boundaries: bool,
    boundary_taper_samples: int,
    piecewise_laws: bool,
    track_observation_phase: bool,
) -> tuple[tuple[MafBasisWarpInstance, ...], float] | None:
    if piecewise_laws:
        return _fit_piecewise_instances(
            source,
            sample_rate=sample_rate,
            basis=basis,
            basis_id=basis_id,
            emitter_id=emitter_id,
            observations=observations,
            hop_samples=hop_samples,
            phase_candidates=phase_candidates,
            taper_boundaries=taper_boundaries,
            boundary_taper_samples=boundary_taper_samples,
            track_observation_phase=track_observation_phase,
        )

    start = observations[0].frame_index * hop_samples
    end = min(
        source.shape[0],
        (observations[-1].frame_index + 1) * hop_samples,
    )
    sample_count = end - start
    if sample_count < 64 or sample_count > 65535:
        return None
    start_step = int(round(
        basis.size
        * observations[0].fundamental_hz
        * WARP_ONE_Q16
        / sample_rate
    ))
    end_step = int(round(
        basis.size
        * observations[-1].fundamental_hz
        * WARP_ONE_Q16
        / sample_rate
    ))
    if (
        not -8 * WARP_ONE_Q16 <= start_step <= 8 * WARP_ONE_Q16
        or not -8 * WARP_ONE_Q16 <= end_step <= 8 * WARP_ONE_Q16
    ):
        return None
    base_position = int(round(
        (
            observations[0].phase_anchor / (2.0 * math.pi)
            % 1.0
        )
        * basis.size
        * WARP_ONE_Q16
    ))
    probe_count = min(sample_count, 1024)
    target_probe = source[
        start : start + probe_count,
        emitter_id,
    ].astype(np.int64)
    best_probe = None
    for phase_index in range(phase_candidates):
        source_position = (
            base_position
            + phase_index
            * basis.size
            * WARP_ONE_Q16
            // phase_candidates
        ) % (basis.size * WARP_ONE_Q16)
        probe = _render_basis(
            basis,
            probe_count,
            source_position,
            start_step,
            (
                end_step
                if probe_count == sample_count and sample_count >= 3
                else None
            ),
        )
        denominator = max(1, int(probe @ probe))
        correlation = abs(int(probe @ target_probe))
        key = (-correlation * correlation / denominator, phase_index)
        if best_probe is None or key < best_probe[0]:
            best_probe = (key, source_position)
    assert best_probe is not None
    source_position = best_probe[1]
    waveform = _render_basis(
        basis,
        sample_count,
        source_position,
        start_step,
        end_step if sample_count >= 3 else None,
    )
    target = source[start:end, emitter_id]
    if taper_boundaries and sample_count >= 128:
        edge = min(boundary_taper_samples, sample_count // 4)
        middle_count = sample_count - 2 * edge
        if edge < 1 or middle_count < 2:
            return None
        positions = _source_positions_q16(
            sample_count,
            source_position,
            start_step,
            end_step,
        )
        gain, end_gain, _untapered_error = _fit_gain_law(waveform, target)
        if end_gain is None:
            end_gain = gain

        def interpolate(value0: int, value1: int, position: int) -> int:
            return int(round(
                value0
                + (value1 - value0) * position / (sample_count - 1)
            ))

        boundaries = (0, edge, sample_count - edge, sample_count)
        boundary_gains = (
            0,
            interpolate(gain, end_gain, edge),
            interpolate(gain, end_gain, sample_count - edge),
            0,
        )
        instances = []
        rendered_parts = []
        for part_index in range(3):
            part_start = boundaries[part_index]
            part_end = boundaries[part_index + 1]
            part_count = part_end - part_start
            part_start_step = interpolate(
                start_step,
                end_step,
                part_start,
            )
            part_end_step = interpolate(
                start_step,
                end_step,
                min(sample_count - 1, part_end),
            )
            part_position = int(positions[part_start])
            part_waveform = _render_basis(
                basis,
                part_count,
                part_position,
                part_start_step,
                part_end_step if part_count >= 3 else None,
            )
            part_start_gain = boundary_gains[part_index]
            part_end_gain = boundary_gains[part_index + 1]
            rendered_parts.append(
                _apply_gain(
                    part_waveform,
                    part_start_gain,
                    part_end_gain,
                )
            )
            instances.append(
                MafBasisWarpInstance(
                    emitter_id=emitter_id,
                    basis_id=basis_id,
                    start=start + part_start,
                    sample_count=part_count,
                    source_position_q16=part_position,
                    source_step_q16=part_start_step,
                    gain_q15=part_start_gain,
                    circular=True,
                    end_source_step_q16=(
                        part_end_step
                        if part_end_step != part_start_step
                        else None
                    ),
                    end_gain_q15=(
                        part_end_gain
                        if part_end_gain != part_start_gain
                        else None
                    ),
                )
            )
        rendered = np.concatenate(rendered_parts)
        error = target.astype(np.int64) - rendered
        target_energy = max(
            1,
            int(target.astype(np.int64) @ target.astype(np.int64)),
        )
        normalized_error = float(error @ error) / target_energy
        return tuple(instances), normalized_error
    gain, end_gain, normalized_error = _fit_gain_law(waveform, target)
    return (
        (
            MafBasisWarpInstance(
                emitter_id=emitter_id,
                basis_id=basis_id,
                start=start,
                sample_count=sample_count,
                source_position_q16=source_position,
                source_step_q16=start_step,
                gain_q15=gain,
                circular=True,
                end_source_step_q16=(
                    end_step if end_step != start_step else None
                ),
                end_gain_q15=end_gain,
            ),
        ),
        normalized_error,
    )


def fit_partial_basis_trajectory_prediction(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder,
    language: CoherentPartialLanguage = CoherentPartialLanguage(),
    basis_samples: int = 64,
    maximum_trajectory_observations: int = 32,
    minimum_hold_frames: int = 4,
    phase_candidates: int = 16,
    taper_boundaries: bool = True,
    boundary_taper_samples: int = 32,
    piecewise_laws: bool = True,
    track_observation_phase: bool = False,
    basis_waveform_mode: str = "observed",
    maximum_instances: int = 4096,
    maximum_normalized_error: float = 0.65,
) -> PartialBasisTrajectoryPrediction:
    """Compile clustered complex partial states into bounded warp lifetimes."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("partial-Basis trajectories require frame-major PCM16")
    if (
        not 32 <= basis_samples <= 1024
        or basis_samples & (basis_samples - 1)
        or not 2 <= maximum_trajectory_observations <= 256
        or not 1 <= minimum_hold_frames <= 64
        or not 4 <= phase_candidates <= 256
        or not 1 <= boundary_taper_samples <= 1024
        or not 1 <= maximum_instances <= 4096
        or not 0.0 < maximum_normalized_error <= 4.0
        or basis_waveform_mode not in {"observed", "analytic"}
    ):
        raise ValueError("invalid partial-Basis trajectory language")
    causal_field = infer_causal_lane_field(
        source,
        sample_rate=sample_rate,
        language=language,
    )
    basis_arrays = tuple(
        (
            _observed_basis_waveform(
                causal_field.coherent_harmonic,
                sample_rate=sample_rate,
                emitter_id=emitter_id,
                basis=basis,
                hop_samples=language.hop_samples,
                minimum_samples=basis_samples,
            )
            if basis_waveform_mode == "observed"
            else _basis_waveform(
                basis,
                sample_count=max(32, basis_samples),
            )
        )
        for basis in causal_field.bases
        for emitter_id in range(source.shape[1])
    )
    basis_id_by_state_channel = {
        (basis_id, emitter_id): (
            basis_id * source.shape[1] + emitter_id
        )
        for basis_id in range(len(causal_field.bases))
        for emitter_id in range(source.shape[1])
    }
    trajectories = _trajectory_runs(
        _labelled_observations(causal_field.bases),
        maximum_observations=maximum_trajectory_observations,
        minimum_hold_frames=minimum_hold_frames,
    )
    candidates = []
    evaluated = 0
    for basis_id, observations in trajectories:
        for emitter_id in range(source.shape[1]):
            observed_basis_id = basis_id_by_state_channel[
                (basis_id, emitter_id)
            ]
            fitted = _fit_instance(
                causal_field.coherent_harmonic,
                sample_rate=sample_rate,
                basis=basis_arrays[observed_basis_id],
                basis_id=observed_basis_id,
                emitter_id=emitter_id,
                observations=observations,
                hop_samples=language.hop_samples,
                phase_candidates=phase_candidates,
                taper_boundaries=taper_boundaries,
                boundary_taper_samples=boundary_taper_samples,
                piecewise_laws=piecewise_laws,
                track_observation_phase=track_observation_phase,
            )
            evaluated += 1
            if fitted is None:
                continue
            fitted_instances, error = fitted
            if error <= maximum_normalized_error:
                covered = sum(
                    instance.sample_count for instance in fitted_instances
                )
                score = covered * (1.0 - error)
                candidates.append((score, fitted_instances, error))
    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1][0].start,
            item[1][0].emitter_id,
        )
    )
    selected = []
    instance_count = 0
    for item in candidates:
        if instance_count + len(item[1]) > maximum_instances:
            continue
        selected.append(item)
        instance_count += len(item[1])
    selected.sort(
        key=lambda item: (item[1][0].start, item[1][0].emitter_id)
    )
    used_basis_ids = sorted(
        {
            instance.basis_id
            for item in selected
            for instance in item[1]
        }
    )
    remap = {
        old_id: new_id for new_id, old_id in enumerate(used_basis_ids)
    }
    instances = tuple(
        MafBasisWarpInstance(
            emitter_id=instance.emitter_id,
            basis_id=remap[instance.basis_id],
            start=instance.start,
            sample_count=instance.sample_count,
            source_position_q16=instance.source_position_q16,
            source_step_q16=instance.source_step_q16,
            gain_q15=instance.gain_q15,
            circular=instance.circular,
            end_source_step_q16=instance.end_source_step_q16,
            end_gain_q15=instance.end_gain_q15,
        )
        for _score, item, _error in selected
        for instance in item
    )
    bases = tuple(
        MafBasis(tuple(int(value) for value in basis_arrays[old_id]))
        for old_id in used_basis_ids
    )
    channels = source.shape[1]
    matrix = tuple(
        tuple(
            32767 if output == emitter else 0
            for emitter in range(channels)
        )
        for output in range(channels)
    )
    payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=source.shape[0],
        render_quantum=min(4096, source.shape[0]),
        output_channels=channels,
        emitter_count=channels,
        mixes=(MafMix(0, source.shape[0], matrix),),
        bases=bases,
        basis_warp_instances=instances,
        declared_operations_per_frame=256,
    )
    native = native_decoder.decode_maf_typed(payload)
    reconstruction = native.samples
    residual = source.astype(np.int64) - reconstruction.astype(np.int64)
    reconstruction.flags.writeable = False
    covered = sum(item.sample_count for item in instances)
    return PartialBasisTrajectoryPrediction(
        payload=payload,
        reconstruction=reconstruction,
        causal_field=causal_field,
        report={
            "schema": "resonith-r177-partial-basis-trajectory-1",
            "status": "native-decoded predictor; complete Truth RDO pending",
            "semantic_source_classes": False,
            "phase_tracking": (
                "observation-locked"
                if track_observation_phase
                else "continuous-integrated"
            ),
            "basis_waveform_mode": basis_waveform_mode,
            "analytic_basis_count": len(causal_field.bases),
            "transmitted_basis_count": len(bases),
            "trajectory_run_count": len(trajectories),
            "evaluated_instance_count": evaluated,
            "selected_instance_count": len(instances),
            "covered_emitter_samples": covered,
            "covered_sample_fraction": (
                covered / source.size if source.size else 0.0
            ),
            "mean_normalized_fit_error": (
                float(np.mean([item[2] for item in selected]))
                if selected
                else None
            ),
            "predictor_bytes": len(payload),
            "predictor_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_rms": float(np.sqrt(
                np.mean(residual.astype(np.float64) ** 2)
            )),
            "residual_clip_count": int(np.count_nonzero(
                (residual < -32768) | (residual > 32767)
            )),
            "workspace_bytes": native.workspace_bytes,
        },
    )
