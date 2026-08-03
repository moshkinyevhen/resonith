"""R-159 objective latent-source pattern tomography.

This encoder-side oracle infers recurring additive layers from differently
overlapped observations. It never assigns semantic source names and never
changes Truth: the returned prediction plus correction equals the input in
integer arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import zlib

import numpy as np


@dataclass(frozen=True)
class LatentSourceLanguage:
    """Finite R-159 oracle language published with each evidence run."""

    scales: tuple[int, ...]
    origin_hop: int = 1
    minimum_occurrences: int = 3
    maximum_components: int = 8
    maximum_cluster_members: int = 96
    maximum_lag: int = 8
    minimum_spectral_similarity: float = 0.90
    maximum_normalized_correction: float = 0.55
    consensus_iterations: int = 3
    similarity_batch_rows: int = 512

    def __post_init__(self) -> None:
        if (
            not self.scales
            or tuple(sorted(set(self.scales))) != self.scales
            or any(not 16 <= scale <= 16384 for scale in self.scales)
        ):
            raise ValueError("R-159 scales must be unique canonical durations")
        if self.origin_hop <= 0:
            raise ValueError("R-159 origin hop must be positive")
        if not 2 <= self.minimum_occurrences <= self.maximum_cluster_members:
            raise ValueError("R-159 occurrence bounds are inconsistent")
        if not 1 <= self.maximum_components <= 64:
            raise ValueError("R-159 component bound is outside the oracle profile")
        if not 0 <= self.maximum_lag <= 256:
            raise ValueError("R-159 lag exceeds the oracle profile")
        if not 0.0 <= self.minimum_spectral_similarity <= 1.0:
            raise ValueError("R-159 similarity must be in [0, 1]")
        if not 0.0 <= self.maximum_normalized_correction <= 1.0:
            raise ValueError("R-159 correction threshold must be in [0, 1]")
        if not 1 <= self.consensus_iterations <= 16:
            raise ValueError("R-159 consensus iteration bound is invalid")
        if not 16 <= self.similarity_batch_rows <= 16384:
            raise ValueError("R-159 similarity batch bound is invalid")


@dataclass(frozen=True, order=True)
class LatentOccurrence:
    """One objective placement of an inferred mono Basis."""

    channel: int
    start: int
    sample_count: int
    alignment_lag: int
    gain_q15: int
    squared_correction: int
    target_energy: int


@dataclass(frozen=True)
class LatentComponent:
    """One unnamed recurring component and its verified observations."""

    component_id: int
    basis: np.ndarray
    occurrences: tuple[LatentOccurrence, ...]
    event_map: bytes
    direct_truth_bytes: int
    structured_proxy_bytes: int


@dataclass(frozen=True)
class LatentSourceField:
    """Exact additive layer proposal plus objective correction."""

    components: tuple[LatentComponent, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    report: dict


def _round_q15(values: np.ndarray, gain_q15: int) -> np.ndarray:
    product = values.astype(np.int64) * gain_q15
    rounded = np.where(
        product >= 0,
        (product + 16384) // 32768,
        -((-product + 16384) // 32768),
    )
    return np.clip(rounded, -32768, 32767).astype(np.int16)


def _spectral_signatures(blocks: np.ndarray) -> np.ndarray:
    """Return phase-invariant proposals; time-domain fitting verifies phase."""

    length = blocks.shape[1]
    window = np.sqrt(np.hanning(length) + 1.0e-12)
    spectrum = np.fft.rfft(blocks.astype(np.float64) * window, axis=1)
    magnitude = np.log1p(np.abs(spectrum))
    # Autocorrelation retains periodic/phase structure while allowing an
    # unknown absolute onset to be fitted by the bounded alignment law.
    autocorrelation = np.fft.irfft(
        spectrum * np.conj(spectrum),
        n=length,
        axis=1,
    )[:, : min(32, length)]
    autocorrelation /= np.maximum(
        np.abs(autocorrelation[:, :1]),
        1.0,
    )
    signature = np.concatenate((magnitude, autocorrelation), axis=1)
    signature -= np.mean(signature, axis=1, keepdims=True)
    norm = np.linalg.norm(signature, axis=1, keepdims=True)
    return signature / np.maximum(norm, 1.0e-12)


def _connected_clusters(
    signatures: np.ndarray,
    threshold: float,
    minimum_members: int,
    batch_rows: int,
) -> list[np.ndarray]:
    """Return coherent neighborhoods without single-linkage chain collapse.

    Sliding origins produce a continuum of adjacent windows. Connected
    components incorrectly merge that continuum through transitive edges even
    when its endpoints describe unrelated sounds. Each proposal is therefore
    a direct neighborhood around one medoid candidate; later exact fitting and
    byte RDO remain the judges.
    """

    candidates: list[tuple[float, tuple[int, ...]]] = []
    for batch_start in range(0, signatures.shape[0], batch_rows):
        batch_end = min(batch_start + batch_rows, signatures.shape[0])
        similarity = signatures[batch_start:batch_end] @ signatures.T
        for local_center in range(batch_end - batch_start):
            members = np.flatnonzero(similarity[local_center] >= threshold)
            if members.size < minimum_members:
                continue
            # For unit signatures, mean pairwise cosine is the squared norm of
            # their sum divided by M^2. This is exactly the former submatrix
            # mean without materializing an M x M temporary.
            vector_sum = np.sum(signatures[members], axis=0)
            coherence = float(
                (vector_sum @ vector_sum) / (members.size * members.size)
            )
            candidates.append(
                (
                    coherence,
                    tuple(int(index) for index in members),
                )
            )

    accepted: list[np.ndarray] = []
    accepted_sets: list[set[int]] = []
    for _coherence, members in sorted(
        candidates,
        key=lambda item: (-len(item[1]), -item[0], item[1]),
    ):
        member_set = set(members)
        if any(
            len(member_set & previous)
                >= min(len(member_set), len(previous)) * 3 // 4
            for previous in accepted_sets
        ):
            continue
        accepted.append(np.asarray(members, dtype=np.int64))
        accepted_sets.append(member_set)
    return accepted


def _fit_basis(
    basis: np.ndarray,
    target: np.ndarray,
    maximum_lag: int,
) -> tuple[int, int, np.ndarray, int]:
    target64 = target.astype(np.int64)
    best: tuple[int, int, np.ndarray, int] | None = None
    for lag in range(-maximum_lag, maximum_lag + 1):
        aligned = _zero_fill_shift(basis, lag)
        aligned64 = aligned.astype(np.int64)
        denominator = int(aligned64 @ aligned64)
        if denominator == 0:
            continue
        numerator = int(target64 @ aligned64)
        gain_q15 = int(np.rint(numerator * 32768.0 / denominator))
        gain_q15 = int(np.clip(gain_q15, -4 * 32768, 4 * 32768))
        rendered = _round_q15(aligned, gain_q15)
        delta = target64 - rendered.astype(np.int64)
        squared_error = int(delta @ delta)
        candidate = (squared_error, lag, rendered, gain_q15)
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        return (0, 0, np.zeros_like(target), int(target64 @ target64))
    squared_error, lag, rendered, gain_q15 = best
    return (lag, gain_q15, rendered, squared_error)


def _zero_fill_shift(values: np.ndarray, lag: int) -> np.ndarray:
    """Translate a finite Basis without circularly wrapping its boundaries."""

    shifted = np.zeros_like(values)
    if lag == 0:
        shifted[...] = values
    elif 0 < lag < len(values):
        shifted[lag:] = values[:-lag]
    elif -len(values) < lag < 0:
        shifted[:lag] = values[-lag:]
    return shifted


def _robust_consensus(
    initial: np.ndarray,
    members: np.ndarray,
    language: LatentSourceLanguage,
) -> np.ndarray:
    basis = initial.copy()
    for _ in range(language.consensus_iterations):
        normalized: list[np.ndarray] = []
        for target in members:
            lag, gain_q15, _, _ = _fit_basis(
                basis,
                target,
                language.maximum_lag,
            )
            if abs(gain_q15) < 2048:
                continue
            aligned = _zero_fill_shift(target, -lag).astype(np.float64)
            normalized.append(aligned * 32768.0 / gain_q15)
        if len(normalized) < language.minimum_occurrences:
            break
        basis = np.clip(
            np.rint(np.median(np.stack(normalized), axis=0)),
            -32768,
            32767,
        ).astype(np.int16)
    return basis


def _non_overlapping(
    occurrences: list[LatentOccurrence],
) -> list[LatentOccurrence]:
    selected: list[LatentOccurrence] = []
    end_by_channel: dict[int, int] = {}
    for occurrence in sorted(
        occurrences,
        key=lambda item: (
            item.channel,
            item.start,
            item.squared_correction,
        ),
    ):
        if occurrence.start < end_by_channel.get(occurrence.channel, 0):
            continue
        selected.append(occurrence)
        end_by_channel[occurrence.channel] = (
            occurrence.start + occurrence.sample_count
        )
    return selected


def _compressed_pcm_bytes(samples: np.ndarray) -> int:
    payload = np.ascontiguousarray(samples, dtype="<i2").tobytes()
    return len(zlib.compress(payload, level=9))


def _unsigned_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned event-map value cannot be negative")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _signed_varint(value: int) -> bytes:
    zigzag = (value << 1) if value >= 0 else ((-value << 1) - 1)
    return _unsigned_varint(zigzag)


def _encode_occurrence_map(
    occurrences: list[LatentOccurrence],
) -> bytes:
    """Serialize one sparse lifetime map with gap and transform deltas."""

    output = bytearray()
    ordered = sorted(occurrences, key=lambda item: (item.channel, item.start))
    output.extend(_unsigned_varint(len(ordered)))
    previous_channel = 0
    end_by_channel: dict[int, int] = {}
    gain_by_channel: dict[int, int] = {}
    for occurrence in ordered:
        output.extend(
            _signed_varint(occurrence.channel - previous_channel)
        )
        previous_channel = occurrence.channel
        previous_end = end_by_channel.get(occurrence.channel, 0)
        output.extend(_unsigned_varint(occurrence.start - previous_end))
        previous_gain = gain_by_channel.get(occurrence.channel, 0)
        output.extend(
            _signed_varint(occurrence.gain_q15 - previous_gain)
        )
        output.extend(_signed_varint(occurrence.alignment_lag))
        end_by_channel[occurrence.channel] = (
            occurrence.start + occurrence.sample_count
        )
        gain_by_channel[occurrence.channel] = occurrence.gain_q15
    return bytes(output)


def _diverse_seed_indices(
    member_indices: np.ndarray,
    blocks: np.ndarray,
    locations: list[tuple[int, int]],
    scale: int,
    limit: int,
) -> list[int]:
    """Choose energetic hypotheses without spending all seeds on one onset."""

    energy = np.sum(
        blocks[member_indices].astype(np.int64) ** 2,
        axis=1,
    )
    ranked = sorted(
        range(member_indices.size),
        key=lambda local: (
            -int(energy[local]),
            locations[int(member_indices[local])],
        ),
    )
    selected: list[int] = []
    exclusion = max(1, scale // 2)
    for local in ranked:
        index = int(member_indices[local])
        channel, start = locations[index]
        if any(
            channel == locations[previous][0]
            and abs(start - locations[previous][1]) < exclusion
            for previous in selected
        ):
            continue
        selected.append(index)
        if len(selected) >= limit:
            break
    return selected


def infer_latent_source_pattern_field(
    samples: np.ndarray,
    *,
    language: LatentSourceLanguage,
) -> LatentSourceField:
    """Infer unnamed recurring layers and preserve exact integer Truth."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-159 inference requires frame-major PCM16")

    residual = source.astype(np.int64)
    prediction = np.zeros_like(residual)
    components: list[LatentComponent] = []
    direct_exact_groups = 0
    evaluated_cells = 0
    evaluated_pairs = 0
    fitted_candidate_count = 0
    best_candidate_byte_delta: int | None = None

    for scale in language.scales:
        if len(components) >= language.maximum_components or scale > source.shape[0]:
            break
        locations = [
            (channel, start)
            for channel in range(source.shape[1])
            for start in range(
                0,
                source.shape[0] - scale + 1,
                language.origin_hop,
            )
        ]
        if len(locations) < language.minimum_occurrences:
            continue
        blocks = np.stack(
            [
                np.clip(
                    residual[start : start + scale, channel],
                    -32768,
                    32767,
                ).astype(np.int16)
                for channel, start in locations
            ]
        )
        evaluated_cells += len(locations)
        evaluated_pairs += len(locations) * (len(locations) - 1) // 2

        payload_counts: dict[bytes, int] = {}
        for block in blocks:
            key = np.ascontiguousarray(block, dtype="<i2").tobytes()
            payload_counts[key] = payload_counts.get(key, 0) + 1
        direct_exact_groups += sum(
            1 for count in payload_counts.values() if count >= 2
        )

        signatures = _spectral_signatures(blocks)
        clusters = _connected_clusters(
            signatures,
            language.minimum_spectral_similarity,
            language.minimum_occurrences,
            language.similarity_batch_rows,
        )
        cluster_order = sorted(
            clusters,
            key=lambda members: (-members.size, int(members[0])),
        )
        for member_indices in cluster_order:
            if len(components) >= language.maximum_components:
                break
            best_candidate: tuple[
                int,
                int,
                np.ndarray,
                list[LatentOccurrence],
                dict[tuple[int, int], np.ndarray],
                bytes,
            ] | None = None
            seeds = _diverse_seed_indices(
                member_indices,
                blocks,
                locations,
                scale,
                min(24, language.maximum_cluster_members),
            )
            for seed_index in seeds:
                preliminary: list[LatentOccurrence] = []
                for member_index in member_indices:
                    channel, start = locations[int(member_index)]
                    target = blocks[int(member_index)]
                    lag, gain_q15, _rendered, squared_error = _fit_basis(
                        blocks[seed_index],
                        target,
                        language.maximum_lag,
                    )
                    target64 = target.astype(np.int64)
                    energy = int(target64 @ target64)
                    if (
                        squared_error
                        <= max(1, energy)
                            * language.maximum_normalized_correction
                    ):
                        preliminary.append(
                            LatentOccurrence(
                                channel,
                                start,
                                scale,
                                lag,
                                gain_q15,
                                squared_error,
                                energy,
                            )
                        )
                preliminary = _non_overlapping(preliminary)
                if len(preliminary) < language.minimum_occurrences:
                    continue
                consensus_indices = [
                    locations.index((item.channel, item.start))
                    for item in preliminary[
                        : language.maximum_cluster_members
                    ]
                ]
                basis = _robust_consensus(
                    blocks[seed_index],
                    blocks[consensus_indices],
                    language,
                )
                if not np.any(basis):
                    continue

                occurrence_candidates: list[LatentOccurrence] = []
                rendered_by_location: dict[tuple[int, int], np.ndarray] = {}
                for member_index in member_indices:
                    channel, start = locations[int(member_index)]
                    target = blocks[int(member_index)]
                    lag, gain_q15, rendered, squared_error = _fit_basis(
                        basis,
                        target,
                        language.maximum_lag,
                    )
                    target64 = target.astype(np.int64)
                    energy = int(target64 @ target64)
                    if (
                        squared_error
                        > max(1, energy)
                            * language.maximum_normalized_correction
                    ):
                        continue
                    occurrence_candidates.append(
                        LatentOccurrence(
                            channel,
                            start,
                            scale,
                            lag,
                            gain_q15,
                            squared_error,
                            energy,
                        )
                    )
                    rendered_by_location[(channel, start)] = rendered

                admitted = _non_overlapping(occurrence_candidates)
                if len(admitted) < language.minimum_occurrences:
                    continue
                admitted_keys = {
                    (item.channel, item.start) for item in admitted
                }
                direct_segments = [
                    blocks[locations.index(key)]
                    for key in sorted(admitted_keys)
                ]
                correction_segments = [
                    np.clip(
                        blocks[locations.index(key)].astype(np.int64)
                            - rendered_by_location[key].astype(np.int64),
                        -32768,
                        32767,
                    ).astype(np.int16)
                    for key in sorted(admitted_keys)
                ]
                direct_bytes = _compressed_pcm_bytes(
                    np.concatenate(direct_segments)
                )
                event_map = _encode_occurrence_map(admitted)
                structured_bytes = (
                    _compressed_pcm_bytes(basis)
                    + len(event_map)
                    + _compressed_pcm_bytes(
                        np.concatenate(correction_segments)
                    )
                )
                candidate = (
                    structured_bytes - direct_bytes,
                    direct_bytes,
                    basis,
                    admitted,
                    rendered_by_location,
                    event_map,
                )
                fitted_candidate_count += 1
                if (
                    best_candidate_byte_delta is None
                    or candidate[0] < best_candidate_byte_delta
                ):
                    best_candidate_byte_delta = candidate[0]
                if (
                    best_candidate is None
                    or candidate[0] < best_candidate[0]
                ):
                    best_candidate = candidate

            if best_candidate is None or best_candidate[0] >= 0:
                continue
            (
                byte_delta,
                direct_bytes,
                basis,
                admitted,
                rendered_by_location,
                event_map,
            ) = best_candidate
            structured_bytes = direct_bytes + byte_delta
            for occurrence in admitted:
                key = (occurrence.channel, occurrence.start)
                rendered = rendered_by_location[key].astype(np.int64)
                span = slice(
                    occurrence.start,
                    occurrence.start + occurrence.sample_count,
                )
                prediction[span, occurrence.channel] += rendered
                residual[span, occurrence.channel] -= rendered
            immutable_basis = basis.copy()
            immutable_basis.flags.writeable = False
            components.append(
                LatentComponent(
                    len(components),
                    immutable_basis,
                    tuple(admitted),
                    event_map,
                    direct_bytes,
                    structured_bytes,
                )
            )

    reconstruction = prediction + residual
    if not np.array_equal(reconstruction, source.astype(np.int64)):
        raise RuntimeError("R-159 additive Truth identity failed")
    prediction.flags.writeable = False
    residual.flags.writeable = False
    reconstruction.flags.writeable = False
    source_hash = hashlib.sha256(
        np.ascontiguousarray(source, dtype="<i2").tobytes()
    ).hexdigest()
    reconstruction_hash = hashlib.sha256(
        np.ascontiguousarray(
            reconstruction.astype(np.int16),
            dtype="<i2",
        ).tobytes()
    ).hexdigest()
    return LatentSourceField(
        tuple(components),
        prediction,
        residual,
        reconstruction,
        {
            "schema": "resonith-r159-latent-source-field-1",
            "status": "encoder-side oracle; complete-byte native RDO pending",
            "frames": int(source.shape[0]),
            "channels": int(source.shape[1]),
            "scales": list(language.scales),
            "origin_hop": language.origin_hop,
            "similarity_batch_rows": language.similarity_batch_rows,
            "evaluated_cell_count": evaluated_cells,
            "evaluated_pair_count": evaluated_pairs,
            "fitted_candidate_count": fitted_candidate_count,
            "best_candidate_byte_delta": best_candidate_byte_delta,
            "direct_exact_group_count": direct_exact_groups,
            "latent_component_count": len(components),
            "latent_occurrence_count": sum(
                len(component.occurrences) for component in components
            ),
            "event_map_bytes": sum(
                len(component.event_map) for component in components
            ),
            "direct_proxy_bytes": sum(
                component.direct_truth_bytes for component in components
            ),
            "structured_proxy_bytes": sum(
                component.structured_proxy_bytes for component in components
            ),
            "source_sha256": source_hash,
            "reconstruction_sha256": reconstruction_hash,
            "exact_integer_reconstruction": source_hash == reconstruction_hash,
            "semantic_labels": False,
            "bounded_non_circular_sample_alignment_verified": True,
            "fractional_phase_alignment_verified": False,
            "cross_channel_union": True,
        },
    )
