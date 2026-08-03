"""R-186 audited complex-partial observation and resolvability oracle.

This module is encoder-side evidence only. It does not synthesize audio,
select a codec program, or claim authoritative phase trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np
from scipy import signal


@dataclass(frozen=True)
class PartialResolution:
    """One explicitly bounded centered-window analysis hypothesis."""

    fft_samples: int
    hop_samples: int

    def __post_init__(self) -> None:
        if (
            self.fft_samples < 128
            or self.fft_samples & (self.fft_samples - 1)
            or not 1 <= self.hop_samples <= self.fft_samples // 2
        ):
            raise ValueError("invalid complex-partial resolution")


@dataclass(frozen=True)
class ComplexPartialAnalyzerManifest:
    """Finite R-186 observation union and resource ceiling."""

    resolutions: tuple[PartialResolution, ...] = (
        PartialResolution(512, 128),
        PartialResolution(2048, 512),
        PartialResolution(8192, 2048),
    )
    logarithmic_band_count: int = 24
    observations_per_band: int = 2
    observations_per_detector_frame: int = 48
    minimum_snr_db: float = 3.0
    phase_snr_db: float = 6.0
    rayleigh_separation_bins: float = 1.5
    maximum_observations: int = 3_500_000
    maximum_host_bytes: int = 16 * 1024**3
    phase_estimators: tuple[str, ...] = ("direct-dtft",)

    def __post_init__(self) -> None:
        if (
            not self.resolutions
            or len(set(self.resolutions)) != len(self.resolutions)
            or not 4 <= self.logarithmic_band_count <= 128
            or not 1 <= self.observations_per_band <= 8
            or not 1 <= self.observations_per_detector_frame <= 256
            or not -20.0 <= self.minimum_snr_db <= 80.0
            or not self.minimum_snr_db <= self.phase_snr_db <= 100.0
            or not 0.5 <= self.rayleigh_separation_bins <= 4.0
            or not 1 <= self.maximum_observations <= 20_000_000
            or not 1 << 20 <= self.maximum_host_bytes <= 1 << 45
            or self.phase_estimators != ("direct-dtft",)
        ):
            raise ValueError("invalid R-186 analyzer manifest")


@dataclass(frozen=True)
class AnalyticPartial:
    """Known synthetic line used only by the resolvability oracle."""

    frequency_hz: float
    amplitude: float
    phase_radians: float = 0.0


@dataclass(frozen=True)
class ComplexPartialObservation:
    """One phase-evidence observation with uncertainty and provenance."""

    observation_id: int
    resolution_id: int
    fft_samples: int
    hop_samples: int
    detector_channel: int
    frame_index: int
    center_sample: int
    frequency_hz: float
    resolution_hz: float
    aggregate_amplitude: float
    aggregate_phase: float
    normalized_detector_amplitude: float
    amplitude_lower_confidence: float
    local_noise_floor: float
    peak_prominence_db: float
    channel_amplitudes: tuple[float, ...]
    channel_phases: tuple[float, ...]
    snr_db: float
    snr_known: bool
    frequency_uncertainty_hz: float
    phase_uncertainty_radians: float
    amplitude_uncertainty: float
    phase_usable: bool
    locally_resolvable: bool
    ambiguity_group: tuple[int, int, int, int]
    provenance: tuple[int, int, int, int]
    conflict_group: int = -1


@dataclass(frozen=True)
class ComplexPartialObservationSet:
    """Finite multiresolution/per-channel proposal union."""

    observations: tuple[ComplexPartialObservation, ...]
    report: dict


def analytic_resolvability_mask(
    partials: tuple[AnalyticPartial, ...],
    *,
    sample_rate: int,
    fft_samples: int,
    rayleigh_separation_bins: float = 1.5,
) -> tuple[bool, ...]:
    """Mark only lines distinguishable under the declared Rayleigh gate."""

    if sample_rate <= 0 or fft_samples < 2:
        raise ValueError("invalid analytic resolvability request")
    separation_hz = rayleigh_separation_bins * sample_rate / fft_samples
    mask = []
    for index, partial in enumerate(partials):
        nearest = min(
            (
                abs(partial.frequency_hz - other.frequency_hz)
                for other_index, other in enumerate(partials)
                if other_index != index
            ),
            default=math.inf,
        )
        mask.append(
            partial.amplitude > 0.0
            and 0.0 < partial.frequency_hz < sample_rate / 2.0
            and nearest >= separation_hz
        )
    return tuple(mask)


def _centered_frame(
    samples: np.ndarray,
    center_sample: int,
    fft_samples: int,
) -> np.ndarray:
    start = center_sample - fft_samples // 2
    source_start = max(0, start)
    source_end = min(samples.shape[0], start + fft_samples)
    frame = np.zeros(
        (fft_samples, samples.shape[1]),
        dtype=np.float64,
    )
    if source_end > source_start:
        target_start = source_start - start
        frame[
            target_start : target_start + source_end - source_start
        ] = samples[source_start:source_end]
    return frame


def _sub_bin_peak(magnitude: np.ndarray, peak: int) -> float:
    if peak <= 0 or peak >= magnitude.size - 1:
        return float(peak)
    left = math.log(max(float(magnitude[peak - 1]), 1.0e-30))
    center = math.log(max(float(magnitude[peak]), 1.0e-30))
    right = math.log(max(float(magnitude[peak + 1]), 1.0e-30))
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


def _direct_dtft(
    weighted_frame: np.ndarray,
    relative_sample: np.ndarray,
    frequency_hz: float,
    sample_rate: int,
    normalization: float,
) -> np.ndarray:
    """Evaluate phase at the fitted frequency and centered time origin."""

    kernel = np.exp(
        -2j
        * np.pi
        * frequency_hz
        * relative_sample
        / sample_rate
    )
    return (
        np.sum(weighted_frame * kernel[:, None], axis=0)
        / normalization
    )


def _band_edges(
    sample_rate: int,
    fft_samples: int,
    band_count: int,
) -> tuple[tuple[int, int], ...]:
    maximum_bin = fft_samples // 2
    minimum_hz = max(20.0, sample_rate / fft_samples)
    edges_hz = np.geomspace(
        minimum_hz,
        sample_rate / 2.0,
        band_count + 1,
    )
    bins = np.clip(
        np.rint(edges_hz * fft_samples / sample_rate).astype(np.int64),
        1,
        maximum_bin,
    )
    bins[0] = 1
    # Nyquist is excluded from the positive-frequency partial detector. The
    # final value is therefore an exclusive boundary.
    bins[-1] = maximum_bin
    boundaries = tuple(sorted(set(int(value) for value in bins)))
    return tuple(
        (begin, end)
        for begin, end in zip(boundaries, boundaries[1:])
        if begin < end
    )


def _candidate_peaks(
    magnitude: np.ndarray,
    bands: tuple[tuple[int, int], ...],
    manifest: ComplexPartialAnalyzerManifest,
) -> tuple[tuple[tuple[int, float, float, bool], ...], dict]:
    # A peak is a property of the detector spectrum, not of an allocation
    # band. Detect it once so a monotonic band edge can never become a second
    # sinusoidal observation. SciPy deterministically returns the lower middle
    # sample for an even plateau.
    canonical_peaks, _properties = signal.find_peaks(
        magnitude,
        plateau_size=(1, None),
    )
    canonical_peaks = canonical_peaks[
        (canonical_peaks > 0)
        & (canonical_peaks < magnitude.size - 1)
    ]
    if not canonical_peaks.size:
        return (), {
            "candidate_pool_count": 0,
            "retained_candidate_ids": [],
            "discarded_candidate_ids": [],
            "resource_pruned": False,
        }
    prominences = signal.peak_prominences(
        magnitude,
        canonical_peaks,
    )[0]
    prominence_by_peak = {
        int(peak): float(prominence)
        for peak, prominence in zip(canonical_peaks, prominences)
    }

    # The Hann main lobe spans approximately four FFT bins null-to-null.
    # Noise annotation therefore uses bins outside a +/-2-bin guard around
    # every canonical maximum. An empty annulus means unknown confidence, not
    # rejection.
    guarded = np.zeros(magnitude.size, dtype=bool)
    for peak in canonical_peaks:
        guarded[
            max(1, int(peak) - 2) : min(
                magnitude.size - 1,
                int(peak) + 3,
            )
        ] = True

    rows = []
    for band_id, (begin, end) in enumerate(bands):
        eligible = tuple(
            int(peak)
            for peak in canonical_peaks
            if begin <= int(peak) < end
            )
        for peak in eligible:
            annulus_begin = max(1, peak - 12)
            annulus_end = min(magnitude.size - 1, peak + 13)
            clean_bins = np.flatnonzero(
                ~guarded[annulus_begin:annulus_end]
            ) + annulus_begin
            clean_values = magnitude[clean_bins]
            clean_values = clean_values[clean_values > 1.0e-15]
            noise_known = clean_values.size >= 4
            noise_floor = (
                float(np.quantile(clean_values, 0.75))
                if noise_known
                else float(magnitude[peak])
            )
            prominence = prominence_by_peak[peak]
            lower_confidence_proxy = max(
                0.0,
                float(magnitude[peak]) - 2.0 * noise_floor,
            )
            relative_prominence = (
                prominence / max(float(magnitude[peak]), 1.0e-15)
            )
            rows.append(
                (
                    len(rows),
                    peak,
                    noise_floor,
                    prominence,
                    band_id,
                    noise_known,
                    lower_confidence_proxy,
                    relative_prominence,
                )
            )

    by_band: dict[int, list[tuple]] = {}
    for row in rows:
        by_band.setdefault(row[4], []).append(row)
    first_slots = []
    later_slots = []
    for band_id in sorted(by_band):
        candidates = by_band[band_id]
        salience = sorted(
            candidates,
            key=lambda row: (
                -row[6],
                -row[3],
                -float(magnitude[row[1]]),
                row[1],
                row[0],
            ),
        )
        protected = sorted(
            candidates,
            key=lambda row: (
                -row[7],
                -row[3],
                -row[6],
                row[1],
                row[0],
            ),
        )
        band_selected = [protected[0]]
        if (
            manifest.observations_per_band >= 2
            and salience[0][0] != protected[0][0]
        ):
            band_selected.append(salience[0])
        for row in salience:
            if len(band_selected) >= manifest.observations_per_band:
                break
            if all(row[0] != selected[0] for selected in band_selected):
                band_selected.append(row)
        first_slots.append(band_selected[0])
        later_slots.extend(band_selected[1:])

    first_slots.sort(
        key=lambda row: (
            -row[7],
            -row[3],
            row[4],
            row[1],
            row[0],
        )
    )
    later_slots.sort(
        key=lambda row: (
            -row[6],
            -row[3],
            row[4],
            row[1],
            row[0],
        )
    )
    selected = (
        first_slots + later_slots
    )[: manifest.observations_per_detector_frame]
    selected_ids = {row[0] for row in selected}
    discarded_ids = [
        row[0] for row in rows if row[0] not in selected_ids
    ]
    selected.sort(key=lambda row: (row[1], row[0]))
    return (
        tuple(
            (row[1], row[2], row[3], row[5])
            for row in selected
        ),
        {
            "candidate_pool_count": len(rows),
            "retained_candidate_ids": [
                row[0] for row in selected
            ],
            "discarded_candidate_ids": discarded_ids,
            "resource_pruned": bool(discarded_ids),
        },
    )


def _assign_conflict_groups(
    observations: list[ComplexPartialObservation],
    minimum_hop: int,
) -> list[ComplexPartialObservation]:
    """Attach non-destructive duplicate ownership relations."""

    parent = list(range(len(observations)))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first: int, second: int) -> None:
        left = find(first)
        right = find(second)
        if left != right:
            parent[max(left, right)] = min(left, right)

    ordered = sorted(
        range(len(observations)),
        key=lambda index: (
            observations[index].center_sample,
            observations[index].frequency_hz,
            observations[index].observation_id,
        ),
    )
    for position, first_index in enumerate(ordered):
        first = observations[first_index]
        # Walk the same ordered suffix by index.  Materializing the suffix here
        # copied O(n^2) references even though the time-window break examines
        # only nearby observations; indexing preserves comparison/union order.
        for second_position in range(position + 1, len(ordered)):
            second_index = ordered[second_position]
            second = observations[second_index]
            if second.center_sample - first.center_sample > minimum_hop // 2:
                break
            if (
                first.provenance[:3] == second.provenance[:3]
                or abs(first.center_sample - second.center_sample)
                > minimum_hop // 2
            ):
                continue
            frequency_gate = max(
                sample_resolution_hz(first),
                sample_resolution_hz(second),
                3.0
                * (
                    first.frequency_uncertainty_hz
                    + second.frequency_uncertainty_hz
                ),
            )
            if abs(first.frequency_hz - second.frequency_hz) <= frequency_gate:
                union(first_index, second_index)
    roots = sorted({find(index) for index in range(len(observations))})
    group_ids = {root: group for group, root in enumerate(roots)}
    return [
        replace(
            observation,
            conflict_group=group_ids[find(index)],
        )
        for index, observation in enumerate(observations)
    ]


def sample_resolution_hz(observation: ComplexPartialObservation) -> float:
    """Return the observation's Rayleigh-bin width."""

    return observation.resolution_hz


def observe_complex_partials(
    samples: np.ndarray,
    sample_rate: int,
    *,
    manifest: ComplexPartialAnalyzerManifest = (
        ComplexPartialAnalyzerManifest()
    ),
) -> ComplexPartialObservationSet:
    """Build the finite R-186 multiresolution observation union.

    The caller owns a stable PCM16 snapshot and must not mutate it concurrently
    during analysis; deterministic encoding never defined concurrent mutation.
    """

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("complex-partial analyzer requires frame-major PCM16")
    estimated_frames = sum(
        math.ceil(source.shape[0] / resolution.hop_samples) + 1
        for resolution in manifest.resolutions
    )
    estimated_observations = (
        estimated_frames
        * (source.shape[1] + 1)
        * manifest.observations_per_detector_frame
    )
    if estimated_observations > manifest.maximum_observations:
        raise ValueError("R-186 observation manifest exceeds its hard bound")

    # PCM16 values are exactly representable in float64.  Convert the stable
    # source once instead of allocating the same full array for every frame.
    source_float64 = source.astype(np.float64)
    observations: list[ComplexPartialObservation] = []
    allocation_reports = []
    for resolution_id, resolution in enumerate(manifest.resolutions):
        window = signal.windows.hann(
            resolution.fft_samples,
            sym=False,
        )
        relative_sample = (
            np.arange(resolution.fft_samples, dtype=np.float64)
            - resolution.fft_samples // 2
        )
        normalization = max(float(np.sum(window)), 1.0e-30)
        bands = _band_edges(
            sample_rate,
            resolution.fft_samples,
            manifest.logarithmic_band_count,
        )
        frame_count = (
            math.ceil(source.shape[0] / resolution.hop_samples) + 1
        )
        for frame_index in range(frame_count):
            center_sample = frame_index * resolution.hop_samples
            frame = _centered_frame(
                source_float64,
                center_sample,
                resolution.fft_samples,
            )
            # Reuse the exact left operand that the incumbent expressions
            # independently formed for the FFT and every direct DTFT.  The
            # exponential and axis-0 reduction order remain unchanged.
            weighted_frame = frame * window[:, None]
            spectrum = np.fft.rfft(
                weighted_frame,
                axis=0,
            ) / normalization
            channel_magnitude = 2.0 * np.abs(spectrum).T
            detector_magnitudes = (
                np.sqrt(np.sum(channel_magnitude**2, axis=0)),
                *tuple(channel_magnitude[channel] for channel in range(
                    source.shape[1]
                )),
            )
            for detector_index, detector_magnitude in enumerate(
                detector_magnitudes
            ):
                detector_channel = detector_index - 1
                candidates, allocation_report = _candidate_peaks(
                    detector_magnitude,
                    bands,
                    manifest,
                )
                allocation_reports.append({
                    "resolution_id": resolution_id,
                    "detector_channel": detector_channel,
                    "frame_index": frame_index,
                    **allocation_report,
                })
                fitted_candidates = tuple(
                    (
                        peak,
                        noise_floor,
                        prominence,
                        noise_known,
                        _sub_bin_peak(detector_magnitude, peak),
                    )
                    for peak, noise_floor, prominence, noise_known in candidates
                )
                ordered_candidate_ids = sorted(
                    range(len(fitted_candidates)),
                    key=lambda candidate_id: (
                        fitted_candidates[candidate_id][4],
                        fitted_candidates[candidate_id][0],
                    ),
                )
                local_ambiguity_groups = {}
                ambiguity_group_id = -1
                previous_sub_bin = None
                for candidate_id in ordered_candidate_ids:
                    sub_bin = fitted_candidates[candidate_id][4]
                    if (
                        previous_sub_bin is None
                        or sub_bin - previous_sub_bin
                        >= manifest.rayleigh_separation_bins
                    ):
                        ambiguity_group_id += 1
                    local_ambiguity_groups[candidate_id] = (
                        ambiguity_group_id
                    )
                    previous_sub_bin = sub_bin
                ambiguity_group_sizes = {
                    group_id: sum(
                        value == group_id
                        for value in local_ambiguity_groups.values()
                    )
                    for group_id in set(local_ambiguity_groups.values())
                }
                for local_candidate_id, (
                    peak,
                    noise_floor,
                    prominence,
                    noise_known,
                    sub_bin,
                ) in enumerate(fitted_candidates):
                    frequency_hz = (
                        sub_bin * sample_rate / resolution.fft_samples
                    )
                    values = _direct_dtft(
                        weighted_frame,
                        relative_sample,
                        frequency_hz,
                        sample_rate,
                        normalization,
                    )
                    amplitudes = 2.0 * np.abs(values)
                    aggregate_amplitude = float(np.linalg.norm(amplitudes))
                    reference_channel = int(np.argmax(amplitudes))
                    detector_amplitude = (
                        aggregate_amplitude
                        if detector_channel < 0
                        else float(amplitudes[detector_channel])
                    )
                    snr_db = 20.0 * math.log10(
                        max(detector_amplitude, 1.0e-15)
                        / max(noise_floor, 1.0e-15)
                    )
                    power_snr = max(10.0 ** (snr_db / 10.0), 1.0e-12)
                    bin_width = sample_rate / resolution.fft_samples
                    frequency_uncertainty = min(
                        bin_width,
                        max(
                            bin_width / 8.0,
                            bin_width / (2.0 * math.sqrt(power_snr)),
                        ),
                    )
                    phase_uncertainty = min(
                        math.pi,
                        max(
                            0.005,
                            1.0 / math.sqrt(2.0 * power_snr),
                        ),
                    )
                    amplitude_uncertainty = (
                        detector_amplitude
                        / math.sqrt(2.0 * power_snr)
                    )
                    detector_channel_count = (
                        source.shape[1] if detector_channel < 0 else 1
                    )
                    normalized_detector_amplitude = (
                        detector_amplitude
                        / math.sqrt(detector_channel_count)
                    )
                    normalized_amplitude_uncertainty = (
                        amplitude_uncertainty
                        / math.sqrt(detector_channel_count)
                    )
                    amplitude_lower_confidence = max(
                        0.0,
                        normalized_detector_amplitude
                        - 2.0 * normalized_amplitude_uncertainty,
                    )
                    peak_prominence_db = 20.0 * math.log10(
                        1.0
                        + max(prominence, 0.0)
                        / max(noise_floor, 1.0e-15)
                    )
                    observations.append(
                        ComplexPartialObservation(
                            observation_id=len(observations),
                            resolution_id=resolution_id,
                            fft_samples=resolution.fft_samples,
                            hop_samples=resolution.hop_samples,
                            detector_channel=detector_channel,
                            frame_index=frame_index,
                            center_sample=center_sample,
                            frequency_hz=frequency_hz,
                            resolution_hz=bin_width,
                            aggregate_amplitude=aggregate_amplitude,
                            aggregate_phase=float(np.angle(
                                values[reference_channel]
                            )),
                            normalized_detector_amplitude=(
                                normalized_detector_amplitude
                            ),
                            amplitude_lower_confidence=(
                                amplitude_lower_confidence
                            ),
                            local_noise_floor=(
                                noise_floor
                                / math.sqrt(detector_channel_count)
                            ),
                            peak_prominence_db=peak_prominence_db,
                            channel_amplitudes=tuple(
                                float(value) for value in amplitudes
                            ),
                            channel_phases=tuple(
                                float(np.angle(value)) for value in values
                            ),
                            snr_db=snr_db,
                            snr_known=noise_known,
                            frequency_uncertainty_hz=frequency_uncertainty,
                            phase_uncertainty_radians=phase_uncertainty,
                            amplitude_uncertainty=amplitude_uncertainty,
                            phase_usable=(
                                noise_known
                                and snr_db >= manifest.phase_snr_db
                            ),
                            locally_resolvable=(
                                ambiguity_group_sizes[
                                    local_ambiguity_groups[
                                        local_candidate_id
                                    ]
                                ]
                                == 1
                            ),
                            ambiguity_group=(
                                resolution_id,
                                detector_channel,
                                frame_index,
                                local_ambiguity_groups[
                                    local_candidate_id
                                ],
                            ),
                            provenance=(
                                resolution_id,
                                detector_channel,
                                frame_index,
                                local_candidate_id,
                            ),
                        )
                    )
    observations = _assign_conflict_groups(
        observations,
        min(item.hop_samples for item in manifest.resolutions),
    )
    estimated_bytes = len(observations) * 256
    if estimated_bytes > manifest.maximum_host_bytes:
        raise ValueError("R-186 observation set exceeds host-memory bound")
    return ComplexPartialObservationSet(
        observations=tuple(observations),
        report={
            "schema": "resonith-r186-complex-partial-observations-1",
            "status": "analyzer evidence only; predictor and syntax blocked",
            "phase_evidence_only": True,
            "phase_authoritative": False,
            "fundamental_required": False,
            "phase_estimator_hypotheses": list(
                manifest.phase_estimators
            ),
            "window": "periodic Hann",
            "phase_time_origin": "center_sample",
            "amplitude_normalization": (
                "direct DTFT divided by window coherent gain; "
                "aggregate detector divided by sqrt(channel count)"
            ),
            "peak_detection": (
                "global plateau-aware local maxima before half-open "
                "log-band allocation; DC/Nyquist excluded"
            ),
            "resolution_manifest": [
                {
                    "fft_samples": item.fft_samples,
                    "hop_samples": item.hop_samples,
                }
                for item in manifest.resolutions
            ],
            "detector_hypotheses": source.shape[1] + 1,
            "observation_count": len(observations),
            "phase_usable_count": sum(
                observation.phase_usable for observation in observations
            ),
            "conflict_group_count": len({
                observation.conflict_group for observation in observations
            }),
            "estimated_host_bytes": estimated_bytes,
            "candidate_allocation_reports": allocation_reports,
            "candidate_pool_count": sum(
                row["candidate_pool_count"]
                for row in allocation_reports
            ),
            "candidate_discarded_count": sum(
                len(row["discarded_candidate_ids"])
                for row in allocation_reports
            ),
            "resource_pruned": any(
                row["resource_pruned"] for row in allocation_reports
            ),
            "semantic_source_classes": False,
        },
    )
