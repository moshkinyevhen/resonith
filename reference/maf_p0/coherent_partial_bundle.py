"""R-167/R-169 analytic coherent-partial and causal-lane proposer.

This encoder-only model separates coherent harmonic, deterministic inharmonic,
transient, and stochastic coefficient lanes while preserving complex mixture
phase and cross-channel relationships. The masks are proposal evidence; only a
future bounded decoder law plus complete RDO may enter the bitstream.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class CoherentPartialLanguage:
    """Finite analytic proposer settings declared by an evidence run."""

    fft_samples: int = 2048
    hop_samples: int = 256
    minimum_fundamental_hz: float = 50.0
    maximum_fundamental_hz: float = 2000.0
    maximum_partials: int = 24
    harmonic_bin_radius: int = 1
    minimum_harmonic_fraction: float = 0.28
    transient_flux_quantile: float = 0.94
    inharmonic_peak_quantile: float = 0.88
    maximum_basis_clusters: int = 8
    minimum_cluster_observations: int = 32
    maximum_simultaneous_bundles: int = 1

    def __post_init__(self) -> None:
        if (
            self.fft_samples < 128
            or self.fft_samples & (self.fft_samples - 1)
            or not 1 <= self.hop_samples <= self.fft_samples // 2
            or not 10.0 <= self.minimum_fundamental_hz
            < self.maximum_fundamental_hz
            or not 1 <= self.maximum_partials <= 128
            or not 0 <= self.harmonic_bin_radius <= 4
            or not 0.0 <= self.minimum_harmonic_fraction <= 1.0
            or not 0.5 <= self.transient_flux_quantile < 1.0
            or not 0.5 <= self.inharmonic_peak_quantile < 1.0
            or not 1 <= self.maximum_basis_clusters <= 64
            or not 2 <= self.minimum_cluster_observations <= 65535
            or not 1 <= self.maximum_simultaneous_bundles <= 16
        ):
            raise ValueError("invalid coherent-partial proposer language")


@dataclass(frozen=True)
class PartialBundleObservation:
    """One phase-aware occurrence of an unnamed coherent spectral bundle."""

    frame_index: int
    fundamental_hz: float
    gain: float
    phase_anchor: float
    harmonic_fraction: float
    amplitude_ratios: tuple[float, ...] = ()
    relative_phases: tuple[float, ...] = ()
    frequency_offsets_hz: tuple[float, ...] = ()
    channel_partial_phases: tuple[tuple[float, ...], ...] = ()


@dataclass(frozen=True)
class CoherentPartialBasis:
    """Track-local normalized complex partial template."""

    amplitude_ratios: np.ndarray
    relative_phases: np.ndarray
    observations: tuple[PartialBundleObservation, ...]


@dataclass(frozen=True)
class CausalLaneObservation:
    """One anonymous, phase-aware state observation from one causal lane."""

    frame_index: int
    lane: str
    gain: float
    spectral_centroid_hz: float
    spectral_spread_hz: float
    spectral_flatness: float
    phase_anchor: float
    route_gain_db: tuple[float, ...]
    route_phase: tuple[float, ...]


@dataclass(frozen=True)
class CausalLaneField:
    """Four analytic proposal lanes plus one authoritative final Truth."""

    bases: tuple[CoherentPartialBasis, ...]
    lane_observations: dict[str, tuple[CausalLaneObservation, ...]]
    coherent_harmonic: np.ndarray
    deterministic_inharmonic: np.ndarray
    sparse_transient: np.ndarray
    stochastic: np.ndarray
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    report: dict


def _observe_causal_lanes(
    spectrum_field: np.ndarray,
    lane_masks: tuple[np.ndarray, ...],
    *,
    sample_rate: int,
    language: CoherentPartialLanguage,
) -> dict[str, tuple[CausalLaneObservation, ...]]:
    """Describe each owned lane without requiring semantic source labels."""

    lane_names = (
        "coherent_harmonic",
        "deterministic_inharmonic",
        "sparse_transient",
        "stochastic",
    )
    frequency_hz = np.fft.rfftfreq(
        language.fft_samples,
        d=1.0 / sample_rate,
    )
    observations: dict[str, tuple[CausalLaneObservation, ...]] = {}
    for lane_name, mask in zip(lane_names, lane_masks, strict=True):
        lane_rows: list[CausalLaneObservation] = []
        for frame_index in range(mask.shape[1]):
            selected = mask[:, frame_index]
            if not np.any(selected):
                continue
            frame = spectrum_field[:, selected, frame_index]
            energy_by_channel = np.sum(np.abs(frame) ** 2, axis=1)
            total_energy = float(np.sum(energy_by_channel))
            if total_energy <= 1.0e-18:
                continue
            reference_channel = int(np.argmax(energy_by_channel))
            reference_energy = max(
                float(energy_by_channel[reference_channel]),
                1.0e-18,
            )
            frequency_energy = np.sum(np.abs(frame) ** 2, axis=0)
            selected_frequency = frequency_hz[selected]
            centroid = float(
                np.sum(selected_frequency * frequency_energy)
                / np.sum(frequency_energy)
            )
            spread = float(np.sqrt(
                np.sum(
                    (selected_frequency - centroid) ** 2
                    * frequency_energy
                )
                / np.sum(frequency_energy)
            ))
            positive_magnitude = np.sqrt(
                np.maximum(frequency_energy, 1.0e-30)
            )
            flatness = float(
                np.exp(np.mean(np.log(positive_magnitude)))
                / max(float(np.mean(positive_magnitude)), 1.0e-15)
            )
            reference = frame[reference_channel]
            if lane_name == "stochastic":
                # A stochastic law owns distribution and routing; its random
                # realization phase is intentionally not made predictive.
                phase_anchor = 0.0
            else:
                phase_anchor = float(np.angle(
                    np.sum(
                        reference
                        * np.maximum(np.abs(reference), 1.0e-15)
                    )
                ))
            route_gain_db = []
            route_phase = []
            for channel in range(spectrum_field.shape[0]):
                channel_energy = max(
                    float(energy_by_channel[channel]),
                    1.0e-18,
                )
                route_gain_db.append(
                    10.0 * np.log10(channel_energy / reference_energy)
                )
                cross_power = np.sum(
                    frame[channel] * np.conj(reference)
                )
                route_phase.append(float(np.angle(cross_power)))
            lane_rows.append(
                CausalLaneObservation(
                    frame_index=frame_index,
                    lane=lane_name,
                    gain=float(np.sqrt(total_energy)),
                    spectral_centroid_hz=centroid,
                    spectral_spread_hz=spread,
                    spectral_flatness=flatness,
                    phase_anchor=phase_anchor,
                    route_gain_db=tuple(route_gain_db),
                    route_phase=tuple(route_phase),
                )
            )
        observations[lane_name] = tuple(lane_rows)
    return observations


def _cluster_partial_bases(
    observations: list[PartialBundleObservation],
    ratio_rows: list[np.ndarray],
    phase_rows: list[np.ndarray],
    *,
    language: CoherentPartialLanguage,
) -> tuple[CoherentPartialBasis, ...]:
    """Build deterministic anonymous timbre states without semantic labels."""

    if not observations:
        return ()
    amplitudes = np.stack(ratio_rows)
    phases = np.stack(phase_rows)
    scaled_amplitudes = np.log1p(np.maximum(amplitudes, 0.0) * 16.0)
    scaled_amplitudes /= np.maximum(
        np.linalg.norm(scaled_amplitudes, axis=1, keepdims=True),
        1.0e-12,
    )
    phase_weight = np.minimum(amplitudes, 1.0)
    features = np.concatenate(
        (
            scaled_amplitudes,
            np.cos(phases) * phase_weight,
            np.sin(phases) * phase_weight,
        ),
        axis=1,
    )
    requested_clusters = min(
        language.maximum_basis_clusters,
        max(
            1,
            len(observations) // language.minimum_cluster_observations,
        ),
    )
    median = np.median(features, axis=0)
    first = int(np.argmin(np.sum((features - median) ** 2, axis=1)))
    center_indices = [first]
    minimum_distance = np.sum(
        (features - features[first]) ** 2,
        axis=1,
    )
    while len(center_indices) < requested_clusters:
        candidate = int(np.argmax(minimum_distance))
        if float(minimum_distance[candidate]) <= 1.0e-12:
            break
        center_indices.append(candidate)
        minimum_distance = np.minimum(
            minimum_distance,
            np.sum(
                (features - features[candidate]) ** 2,
                axis=1,
            ),
        )
    centers = features[center_indices].copy()
    assignments = np.zeros(len(observations), dtype=np.int64)
    for _iteration in range(12):
        distances = np.sum(
            (
                features[:, None, :]
                - centers[None, :, :]
            )
            ** 2,
            axis=2,
        )
        updated = np.argmin(distances, axis=1)
        if np.array_equal(updated, assignments) and _iteration:
            break
        assignments = updated
        next_centers = []
        active_labels = []
        for label in range(centers.shape[0]):
            members = features[assignments == label]
            if members.size:
                next_centers.append(np.mean(members, axis=0))
                active_labels.append(label)
        if len(next_centers) != centers.shape[0]:
            remap = {
                old_label: new_label
                for new_label, old_label in enumerate(active_labels)
            }
            assignments = np.array(
                [remap[int(label)] for label in assignments],
                dtype=np.int64,
            )
        centers = np.stack(next_centers)

    counts = np.bincount(assignments, minlength=centers.shape[0])
    retained = np.flatnonzero(
        counts >= language.minimum_cluster_observations
    )
    if retained.size == 0:
        retained = np.array([int(np.argmax(counts))], dtype=np.int64)
    if retained.size != centers.shape[0]:
        retained_centers = centers[retained]
        distances = np.sum(
            (
                features[:, None, :]
                - retained_centers[None, :, :]
            )
            ** 2,
            axis=2,
        )
        assignments = np.argmin(distances, axis=1)

    cluster_rows = []
    for label in range(int(np.max(assignments)) + 1):
        member_indices = np.flatnonzero(assignments == label)
        if member_indices.size == 0:
            continue
        cluster_amplitudes = amplitudes[member_indices]
        cluster_phases = phases[member_indices]
        amplitude_ratios = np.median(cluster_amplitudes, axis=0)
        phase_weights = np.maximum(cluster_amplitudes, 1.0e-9)
        relative_phases = np.angle(
            np.sum(
                phase_weights * np.exp(1j * cluster_phases),
                axis=0,
            )
        )
        amplitude_ratios.flags.writeable = False
        relative_phases.flags.writeable = False
        cluster_observations = tuple(
            observations[int(index)] for index in member_indices
        )
        cluster_rows.append(
            (
                cluster_observations[0].frame_index,
                CoherentPartialBasis(
                    amplitude_ratios=amplitude_ratios,
                    relative_phases=relative_phases,
                    observations=cluster_observations,
                ),
            )
        )
    cluster_rows.sort(key=lambda item: item[0])
    return tuple(item[1] for item in cluster_rows)


def _fundamental_candidate(
    magnitude: np.ndarray,
    *,
    sample_rate: int,
    language: CoherentPartialLanguage,
) -> tuple[int, float]:
    minimum_bin = max(
        1,
        int(np.ceil(
            language.minimum_fundamental_hz
            * language.fft_samples
            / sample_rate
        )),
    )
    maximum_bin = min(
        magnitude.size - 1,
        int(np.floor(
            language.maximum_fundamental_hz
            * language.fft_samples
            / sample_rate
        )),
    )
    total_energy = float(np.sum(magnitude**2))
    if maximum_bin < minimum_bin or total_energy <= 1.0e-18:
        return 0, 0.0
    best_bin = 0
    best_score = -1.0
    best_fraction = 0.0
    for fundamental_bin in range(minimum_bin, maximum_bin + 1):
        partial_bins = np.arange(
            fundamental_bin,
            min(
                magnitude.size,
                fundamental_bin * (language.maximum_partials + 1),
            ),
            fundamental_bin,
            dtype=np.int64,
        )
        if partial_bins.size < 2:
            continue
        partial_energy = float(np.sum(magnitude[partial_bins] ** 2))
        fraction = partial_energy / total_energy
        # Reward multiple supported partials without allowing a high-frequency
        # single peak to masquerade as a fundamental.
        supported = int(
            np.count_nonzero(
                magnitude[partial_bins]
                >= max(float(np.max(magnitude)) * 0.02, 1.0e-12)
            )
        )
        score = fraction * np.log2(1.0 + supported)
        if score > best_score:
            best_score = score
            best_bin = fundamental_bin
            best_fraction = fraction
    return best_bin, best_fraction


def _fundamental_candidates(
    magnitude: np.ndarray,
    *,
    sample_rate: int,
    language: CoherentPartialLanguage,
) -> tuple[tuple[int, float], ...]:
    """Extract several disjoint unnamed harmonic bundles from one mixture."""

    residual = np.array(magnitude, dtype=np.float64, copy=True)
    candidates = []
    for _bundle in range(language.maximum_simultaneous_bundles):
        fundamental_bin, harmonic_fraction = _fundamental_candidate(
            residual,
            sample_rate=sample_rate,
            language=language,
        )
        if (
            fundamental_bin <= 0
            or harmonic_fraction < language.minimum_harmonic_fraction
        ):
            break
        candidates.append((fundamental_bin, harmonic_fraction))
        partial_bins = np.arange(
            fundamental_bin,
            min(
                residual.size,
                fundamental_bin * (language.maximum_partials + 1),
            ),
            fundamental_bin,
            dtype=np.int64,
        )
        for partial_bin in partial_bins:
            begin = max(
                0,
                partial_bin - language.harmonic_bin_radius,
            )
            end = min(
                residual.size,
                partial_bin + language.harmonic_bin_radius + 1,
            )
            residual[begin:end] = 0.0
    return tuple(candidates)


def _render_masked_lane(
    spectrum_field: np.ndarray,
    mask: np.ndarray,
    *,
    sample_rate: int,
    frame_count: int,
    language: CoherentPartialLanguage,
) -> np.ndarray:
    overlap = language.fft_samples - language.hop_samples
    rendered = np.empty(
        (frame_count, spectrum_field.shape[0]),
        dtype=np.int64,
    )
    for channel in range(spectrum_field.shape[0]):
        _times, lane = signal.istft(
            spectrum_field[channel] * mask,
            fs=sample_rate,
            window="hann",
            nperseg=language.fft_samples,
            noverlap=overlap,
            input_onesided=True,
            boundary=True,
        )
        lane = lane[:frame_count]
        if lane.size < frame_count:
            lane = np.pad(lane, (0, frame_count - lane.size))
        rendered[:, channel] = np.rint(lane).astype(np.int64)
    return rendered


def infer_causal_lane_field(
    samples: np.ndarray,
    *,
    sample_rate: int,
    language: CoherentPartialLanguage,
) -> CausalLaneField:
    """Infer analytic spectral lanes and preserve exact integer reconstruction."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("causal lanes require frame-major PCM16")
    overlap = language.fft_samples - language.hop_samples
    spectra = []
    for channel in range(source.shape[1]):
        _frequencies, _times, spectrum = signal.stft(
            source[:, channel].astype(np.float64),
            fs=sample_rate,
            window="hann",
            nperseg=language.fft_samples,
            noverlap=overlap,
            boundary="zeros",
            padded=True,
        )
        spectra.append(spectrum)
    spectrum_field = np.stack(spectra, axis=0)
    magnitude = np.sqrt(
        np.sum(np.abs(spectrum_field) ** 2, axis=0)
    )
    normalized = magnitude / np.maximum(
        np.linalg.norm(magnitude, axis=0, keepdims=True),
        1.0e-12,
    )
    flux = np.zeros(magnitude.shape[1], dtype=np.float64)
    if magnitude.shape[1] > 1:
        delta = np.maximum(normalized[:, 1:] - normalized[:, :-1], 0.0)
        flux[1:] = np.linalg.norm(delta, axis=0)
    transient_threshold = float(
        np.quantile(flux, language.transient_flux_quantile)
    )
    transient_frames = flux > max(transient_threshold, 1.0e-9)

    harmonic_mask = np.zeros(magnitude.shape, dtype=bool)
    inharmonic_mask = np.zeros(magnitude.shape, dtype=bool)
    observations: list[PartialBundleObservation] = []
    ratio_rows: list[np.ndarray] = []
    phase_rows: list[np.ndarray] = []
    for frame_index in range(magnitude.shape[1]):
        if transient_frames[frame_index]:
            continue
        frame_magnitude = magnitude[:, frame_index]
        fundamental_candidates = _fundamental_candidates(
            frame_magnitude,
            sample_rate=sample_rate,
            language=language,
        )
        for fundamental_bin, harmonic_fraction in fundamental_candidates:
            partial_bins = np.arange(
                fundamental_bin,
                min(
                    frame_magnitude.size,
                    fundamental_bin * (language.maximum_partials + 1),
                ),
                fundamental_bin,
                dtype=np.int64,
            )
            for partial_bin in partial_bins:
                begin = max(0, partial_bin - language.harmonic_bin_radius)
                end = min(
                    harmonic_mask.shape[0],
                    partial_bin + language.harmonic_bin_radius + 1,
                )
                harmonic_mask[begin:end, frame_index] = True
            partial_energy_by_channel = np.sum(
                np.abs(
                    spectrum_field[
                        :,
                        partial_bins,
                        frame_index,
                    ]
                )
                ** 2,
                axis=1,
            )
            reference_channel = int(np.argmax(partial_energy_by_channel))
            reference_spectrum = spectrum_field[
                reference_channel,
                :,
                frame_index,
            ]
            fundamental = reference_spectrum[fundamental_bin]
            fundamental_offset = 0.0
            if 0 < fundamental_bin < frame_magnitude.size - 1:
                left = np.log(max(frame_magnitude[fundamental_bin - 1], 1e-15))
                center = np.log(max(frame_magnitude[fundamental_bin], 1e-15))
                right = np.log(max(frame_magnitude[fundamental_bin + 1], 1e-15))
                curvature = left - 2.0 * center + right
                if curvature < -1.0e-12:
                    fundamental_offset = float(np.clip(
                        0.5 * (left - right) / curvature,
                        -0.5,
                        0.5,
                    ))
            fundamental_hz = (
                (fundamental_bin + fundamental_offset)
                * sample_rate
                / language.fft_samples
            )
            gain = max(float(np.abs(fundamental)), 1.0e-12)
            amplitudes = np.zeros(
                language.maximum_partials,
                dtype=np.float64,
            )
            phases = np.zeros_like(amplitudes)
            frequency_offsets = np.zeros_like(amplitudes)
            channel_partial_phases = np.zeros(
                (source.shape[1], language.maximum_partials),
                dtype=np.float64,
            )
            fundamental_phase = float(np.angle(fundamental))
            for partial_index, expected_bin in enumerate(partial_bins):
                begin = max(
                    1,
                    expected_bin - language.harmonic_bin_radius,
                )
                end = min(
                    frame_magnitude.size - 1,
                    expected_bin + language.harmonic_bin_radius + 1,
                )
                local = frame_magnitude[begin:end]
                partial_bin = (
                    begin + int(np.argmax(local))
                    if local.size
                    else expected_bin
                )
                partial_offset = 0.0
                if 0 < partial_bin < frame_magnitude.size - 1:
                    left = np.log(max(frame_magnitude[partial_bin - 1], 1e-15))
                    center = np.log(max(frame_magnitude[partial_bin], 1e-15))
                    right = np.log(max(frame_magnitude[partial_bin + 1], 1e-15))
                    curvature = left - 2.0 * center + right
                    if curvature < -1.0e-12:
                        partial_offset = float(np.clip(
                            0.5 * (left - right) / curvature,
                            -0.5,
                            0.5,
                        ))
                value = reference_spectrum[partial_bin]
                amplitudes[partial_index] = float(np.abs(value)) / gain
                partial_hz = (
                    (partial_bin + partial_offset)
                    * sample_rate
                    / language.fft_samples
                )
                frequency_offsets[partial_index] = (
                    partial_hz - (partial_index + 1) * fundamental_hz
                )
                phases[partial_index] = float(
                    np.angle(
                        np.exp(
                            1j
                            * (
                                np.angle(value)
                                - (partial_index + 1) * fundamental_phase
                            )
                        )
                    )
                )
                channel_partial_phases[:, partial_index] = np.angle(
                    spectrum_field[
                        :,
                        partial_bin,
                        frame_index,
                    ]
                )
            ratio_rows.append(amplitudes)
            phase_rows.append(phases)
            observations.append(
                PartialBundleObservation(
                    frame_index=frame_index,
                    fundamental_hz=fundamental_hz,
                    gain=gain,
                    phase_anchor=fundamental_phase,
                    harmonic_fraction=harmonic_fraction,
                    amplitude_ratios=tuple(float(value) for value in amplitudes),
                    relative_phases=tuple(float(value) for value in phases),
                    frequency_offsets_hz=tuple(
                        float(value) for value in frequency_offsets
                    ),
                    channel_partial_phases=tuple(
                        tuple(float(value) for value in row)
                        for row in channel_partial_phases
                    ),
                )
            )

        candidate = frame_magnitude.copy()
        candidate[harmonic_mask[:, frame_index]] = 0.0
        local_peak = signal.find_peaks(candidate)[0]
        nonzero = candidate[candidate > 0.0]
        if local_peak.size and nonzero.size:
            peak_threshold = float(
                np.quantile(nonzero, language.inharmonic_peak_quantile)
            )
            selected_peaks = local_peak[
                candidate[local_peak] >= peak_threshold
            ]
            inharmonic_mask[selected_peaks, frame_index] = True

    transient_mask = np.broadcast_to(
        transient_frames[None, :],
        magnitude.shape,
    ).copy()
    harmonic_mask &= ~transient_mask
    inharmonic_mask &= ~(transient_mask | harmonic_mask)
    stochastic_mask = ~(
        transient_mask | harmonic_mask | inharmonic_mask
    )
    ownership_count = (
        harmonic_mask.astype(np.uint8)
        + inharmonic_mask.astype(np.uint8)
        + transient_mask.astype(np.uint8)
        + stochastic_mask.astype(np.uint8)
    )
    if not np.all(ownership_count == 1):
        raise RuntimeError("causal spectral lanes violate single ownership")

    lane_masks = (
        harmonic_mask,
        inharmonic_mask,
        transient_mask,
        stochastic_mask,
    )
    lane_observations = _observe_causal_lanes(
        spectrum_field,
        lane_masks,
        sample_rate=sample_rate,
        language=language,
    )
    lanes = tuple(
        _render_masked_lane(
            spectrum_field,
            mask,
            sample_rate=sample_rate,
            frame_count=source.shape[0],
            language=language,
        )
        for mask in lane_masks
    )
    prediction = sum(
        lanes,
        start=np.zeros(source.shape, dtype=np.int64),
    )
    source64 = source.astype(np.int64)
    truth = source64 - prediction
    reconstruction = prediction + truth
    source_hash = hashlib.sha256(
        np.ascontiguousarray(source, dtype="<i2").tobytes()
    ).hexdigest()
    reconstruction_hash = hashlib.sha256(
        np.ascontiguousarray(reconstruction, dtype="<i2").tobytes()
    ).hexdigest()
    if source_hash != reconstruction_hash:
        raise RuntimeError("causal lane final-Truth identity failed")

    bases = _cluster_partial_bases(
        observations,
        ratio_rows,
        phase_rows,
        language=language,
    )
    source_energy = float(np.sum(source64.astype(np.float64) ** 2))
    lane_names = (
        "coherent_harmonic",
        "deterministic_inharmonic",
        "sparse_transient",
        "stochastic",
    )
    lane_energy = {
        name: (
            float(np.sum(lane.astype(np.float64) ** 2)) / source_energy
            if source_energy
            else 0.0
        )
        for name, lane in zip(lane_names, lanes, strict=True)
    }
    return CausalLaneField(
        bases=bases,
        lane_observations=lane_observations,
        coherent_harmonic=lanes[0],
        deterministic_inharmonic=lanes[1],
        sparse_transient=lanes[2],
        stochastic=lanes[3],
        prediction=prediction,
        truth_correction=truth,
        reconstruction=reconstruction,
        report={
            "schema": "resonith-r169-causal-lane-field-1",
            "status": (
                "encoder-side analytic proposer; normative PartialBasis "
                "transport and complete RDO pending"
            ),
            "semantic_labels": False,
            "complex_mixture_phase_preserved": True,
            "shared_cross_channel_ownership_masks": True,
            "single_primary_lane_ownership": True,
            "one_final_mixture_truth": True,
            "exact_integer_reconstruction": True,
            "partial_basis_count": len(bases),
            "partial_observation_count": len(observations),
            "partial_basis_observation_count": [
                len(basis.observations) for basis in bases
            ],
            "lane_observation_count": {
                name: len(lane_observations[name])
                for name in lane_names
            },
            "transient_frame_count": int(np.count_nonzero(transient_frames)),
            "coefficient_ownership_fraction": {
                name: float(np.mean(mask))
                for name, mask in zip(lane_names, lane_masks, strict=True)
            },
            "lane_energy_fraction": lane_energy,
            "source_sha256": source_hash,
            "reconstruction_sha256": reconstruction_hash,
        },
    )
