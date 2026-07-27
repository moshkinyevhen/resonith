"""R-142 exact/gain immutable-Basis research oracle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .foundry_cuda import GainPhaseCudaFoundry
from .lpc_oracle import (
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
)
from .maf_typed import (
    MafBasis,
    MafBasisInstance,
    MafMix,
    pack_maf_typed,
)
from .native_core import NativeMain0Decoder


@dataclass(frozen=True)
class MotifOrbitCandidate:
    """One lossless complete-byte result for the R-142 representation."""

    maf_payload: bytes
    truth_payload: bytes
    reconstruction: np.ndarray
    report: dict

    @property
    def representation_bytes(self) -> int:
        """Return every candidate byte beyond a common outer container."""

        return len(self.maf_payload) + len(self.truth_payload)


def _canonical_fingerprint(block: np.ndarray) -> bytes:
    """Return a gain, polarity, and circular-phase-invariant proposal key."""

    source = np.asarray(block, dtype=np.int64)
    spectrum = np.abs(np.fft.rfft(source.astype(np.float64)))
    peak = max(1.0, float(np.max(spectrum)))
    boundaries = np.linspace(0, spectrum.size, 17, dtype=np.int64)
    shape = np.empty(16, dtype=np.float64)
    for index in range(16):
        start = int(boundaries[index])
        end = max(start + 1, int(boundaries[index + 1]))
        shape[index] = float(np.mean(spectrum[start:end])) / peak
    quantized = np.clip(np.rint(shape * 8.0), 0, 8).astype(np.uint8)
    return hashlib.blake2s(quantized.tobytes(), digest_size=8).digest()


def _fit_gain_q15(
    basis: np.ndarray,
    target: np.ndarray,
) -> tuple[int, float]:
    """Fit the normative signed Q1.15 gain and return normalized error."""

    left = np.asarray(basis, dtype=np.int64)
    right = np.asarray(target, dtype=np.int64)
    denominator = int(np.dot(left, left))
    if denominator == 0:
        return 0, 1.0
    numerator = int(np.dot(left, right))
    gain = int(np.rint(numerator * 32768.0 / denominator))
    gain = min(32768, max(-32768, gain))
    product = left * gain
    predicted = np.where(
        product >= 0,
        (product + 16384) // 32768,
        -((-product + 16384) // 32768),
    )
    error = right - predicted
    target_energy = max(1, int(np.dot(right, right)))
    normalized_error = float(np.dot(error, error)) / target_energy
    return gain, normalized_error


def _fit_gain_shift_q15(
    basis: np.ndarray,
    target: np.ndarray,
) -> tuple[int, int, float]:
    """Fit circular phase/alignment, polarity, and normative Q1.15 gain."""

    left = np.asarray(basis, dtype=np.int64)
    right = np.asarray(target, dtype=np.int64)
    if left.size != right.size or left.size == 0:
        raise ValueError("R-146 alignment requires equal non-empty vectors")
    correlation = np.fft.ifft(
        np.conj(np.fft.fft(left.astype(np.float64)))
        * np.fft.fft(right.astype(np.float64))
    ).real
    circular_lag = int(np.argmax(np.abs(correlation)))
    source_offset = (-circular_lag) % left.size
    aligned = np.roll(left, circular_lag)
    gain, normalized_error = _fit_gain_q15(aligned, right)
    return gain, source_offset, normalized_error


def _interpolated_gains_q15(
    start: int,
    end: int,
    count: int,
) -> np.ndarray:
    if count <= 0:
        raise ValueError("R-147 gain law requires a positive count")
    if count == 1:
        return np.asarray((start,), dtype=np.int64)
    positions = np.arange(count, dtype=np.int64)
    numerator = (int(end) - int(start)) * positions
    denominator = count - 1
    magnitude = np.abs(numerator)
    quotient = magnitude // denominator
    quotient += (2 * (magnitude % denominator) >= denominator)
    signed = np.where(numerator < 0, -quotient, quotient)
    gains = int(start) + signed
    gains[-1] = int(end)
    return gains


def _render_gain_shift_envelope(
    basis: np.ndarray,
    source_offset: int,
    start_gain_q15: int,
    end_gain_q15: int | None,
) -> np.ndarray:
    source = np.asarray(basis, dtype=np.int64)
    aligned = np.concatenate(
        (source[source_offset:], source[:source_offset])
    )
    gains = (
        np.full(source.size, start_gain_q15, dtype=np.int64)
        if end_gain_q15 is None
        else _interpolated_gains_q15(
            start_gain_q15,
            end_gain_q15,
            source.size,
        )
    )
    product = aligned * gains
    return np.where(
        product >= 0,
        (product + 16384) // 32768,
        -((-product + 16384) // 32768),
    )


def _fit_gain_envelope_shift_q15(
    basis: np.ndarray,
    target: np.ndarray,
) -> tuple[int, int | None, int, float]:
    """Fit top circular phases, polarity, and constant/linear gain laws."""

    left = np.asarray(basis, dtype=np.int64)
    right = np.asarray(target, dtype=np.int64)
    correlation = np.fft.ifft(
        np.conj(np.fft.fft(left.astype(np.float64)))
        * np.fft.fft(right.astype(np.float64))
    ).real
    candidate_count = min(4, left.size)
    lags = np.argpartition(
        np.abs(correlation),
        -candidate_count,
    )[-candidate_count:]
    target_energy = max(1, int(np.dot(right, right)))
    candidates: list[tuple[float, bool, int, int, int | None]] = []
    for lag_value in sorted(int(value) for value in lags):
        source_offset = (-lag_value) % left.size
        aligned = np.roll(left, lag_value)
        gain, constant_error = _fit_gain_q15(aligned, right)
        candidates.append(
            (constant_error, False, source_offset, gain, None)
        )

        position = np.linspace(0.0, 1.0, left.size)
        first = aligned.astype(np.float64) * (1.0 - position)
        second = aligned.astype(np.float64) * position
        target_scaled = right.astype(np.float64) * 32768.0
        aa = float(np.dot(first, first))
        ab = float(np.dot(first, second))
        bb = float(np.dot(second, second))
        ay = float(np.dot(first, target_scaled))
        by = float(np.dot(second, target_scaled))
        determinant = aa * bb - ab * ab
        if determinant <= max(1.0, aa * bb) * 1.0e-12:
            continue
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
        rendered = _render_gain_shift_envelope(
            left,
            source_offset,
            start_gain,
            end_gain,
        )
        error = right - rendered
        linear_error = float(np.dot(error, error)) / target_energy
        if linear_error < constant_error * 0.98:
            candidates.append(
                (
                    linear_error,
                    True,
                    source_offset,
                    start_gain,
                    end_gain,
                )
            )
    error, _, source_offset, gain, end_gain = min(candidates)
    return gain, end_gain, source_offset, error


def _discover_groups(
    source: np.ndarray,
    block_samples: int,
    *,
    maximum_bases: int,
    maximum_instances: int,
    maximum_normalized_error: float,
) -> tuple[list[np.ndarray], list[MafBasisInstance], dict]:
    """Find fixed-lattice gain-equivalent groups before complete-byte RDO."""

    complete_blocks = source.size // block_samples
    buckets: dict[bytes, list[int]] = {}
    for block_index in range(complete_blocks):
        start = block_index * block_samples
        block = source[start : start + block_samples]
        if int(np.max(np.abs(block))) < 32:
            continue
        buckets.setdefault(_canonical_fingerprint(block), []).append(start)

    proposals: list[
        tuple[int, np.ndarray, list[tuple[int, int, int, float]]]
    ] = []
    rejected_matches = 0
    for starts in buckets.values():
        remaining = list(starts)
        while len(remaining) >= 2:
            basis = source[
                remaining[0] : remaining[0] + block_samples
            ].copy()
            matches: list[tuple[int, int, int, float]] = []
            unmatched: list[int] = []
            for start in remaining:
                target = source[start : start + block_samples]
                gain, source_offset, normalized_error = (
                    _fit_gain_shift_q15(basis, target)
                )
                if normalized_error <= maximum_normalized_error:
                    matches.append(
                        (start, gain, source_offset, normalized_error)
                    )
                else:
                    unmatched.append(start)
                    rejected_matches += 1
            if len(matches) >= 2:
                raw_coverage_bytes = len(matches) * block_samples * 2
                syntax_bytes = 16 + block_samples * 2 + len(matches) * 32
                estimated_saving = raw_coverage_bytes - syntax_bytes
                if estimated_saving > 0:
                    proposals.append((estimated_saving, basis, matches))
                remaining = unmatched
            else:
                remaining = remaining[1:]

    proposals.sort(key=lambda item: item[0], reverse=True)
    bases: list[np.ndarray] = []
    instances: list[MafBasisInstance] = []
    occupied = np.zeros(complete_blocks, dtype=np.bool_)
    normalized_errors: list[float] = []
    for _, basis, matches in proposals:
        retained = []
        for start, gain, source_offset, normalized_error in matches:
            block_index = start // block_samples
            if not occupied[block_index]:
                retained.append(
                    (start, gain, source_offset, normalized_error)
                )
        if len(retained) < 2:
            continue
        if len(bases) >= maximum_bases:
            break
        remaining = maximum_instances - len(instances)
        if remaining < 2:
            break
        retained = retained[:remaining]
        if len(retained) < 2:
            continue
        basis_id = len(bases)
        bases.append(basis)
        for start, gain, source_offset, normalized_error in retained:
            occupied[start // block_samples] = True
            normalized_errors.append(normalized_error)
            instances.append(
                MafBasisInstance(
                    emitter_id=0,
                    basis_id=basis_id,
                    start=start,
                    gain_q15=gain,
                    source_offset=source_offset,
                    sample_count=block_samples,
                    circular=True,
                )
            )

    return bases, instances, {
        "complete_blocks": complete_blocks,
        "proposal_bucket_count": sum(
            int(len(starts) >= 2) for starts in buckets.values()
        ),
        "rejected_match_count": rejected_matches,
        "covered_blocks": int(np.count_nonzero(occupied)),
        "covered_samples": int(np.count_nonzero(occupied) * block_samples),
        "mean_normalized_fit_error": (
            float(np.mean(normalized_errors)) if normalized_errors else None
        ),
        "maximum_normalized_fit_error": (
            float(np.max(normalized_errors)) if normalized_errors else None
        ),
    }


def _discover_complete_cuda(
    source_matrix: np.ndarray,
    block_samples: int,
    *,
    foundry: GainPhaseCudaFoundry,
    maximum_bases: int,
    maximum_instances: int,
    maximum_normalized_error: float,
    tile_candidates: int,
) -> tuple[list[np.ndarray], list[MafBasisInstance], dict]:
    """Run the complete R-149 pair x phase x gain/envelope lattice on CUDA."""

    frames, channels = source_matrix.shape
    complete_blocks = frames // block_samples
    locations: list[tuple[int, int]] = []
    blocks = []
    for channel in range(channels):
        for block_index in range(complete_blocks):
            start = block_index * block_samples
            locations.append((channel, start))
            blocks.append(
                source_matrix[
                    start : start + block_samples,
                    channel,
                ]
            )
    if len(blocks) < 2:
        return [], [], {
            "search_mode": "foundry",
            "complete_hypothesis_language": True,
            "candidate_count": 0,
            "fit_eligible_pair_count": 0,
            "covered_blocks": 0,
            "covered_samples": 0,
        }
    block_matrix = np.ascontiguousarray(np.stack(blocks), dtype=np.int16)
    transform_lattice = block_samples * 2
    pair_aligned_tile = max(
        transform_lattice,
        (tile_candidates // transform_lattice) * transform_lattice,
    )
    matches_by_basis: list[
        list[tuple[int, int, int, int | None, int, bool, float]]
    ] = [[] for _ in locations]
    executed_candidates = 0
    tile_count = 0
    last_evidence = None
    for results, evidence in foundry.evaluate_tiles(
        block_matrix,
        tile_candidates=pair_aligned_tile,
    ):
        if results.size % transform_lattice != 0:
            raise RuntimeError("R-149 CUDA tile split a phase lattice")
        rows = results.reshape((-1, transform_lattice))
        choices = np.argmin(rows["squared_error"], axis=1)
        best = rows[np.arange(rows.shape[0]), choices]
        target_energy = np.maximum(best["target_energy"], 1)
        normalized = (
            best["squared_error"].astype(np.float64)
            / target_energy.astype(np.float64)
        )
        accepted = np.flatnonzero(
            normalized <= maximum_normalized_error
        )
        for row_index in accepted:
            record = best[int(row_index)]
            basis_index = int(record["basis_index"])
            target_index = int(record["target_index"])
            channel, start = locations[target_index]
            linear = (
                int(record["transform_flags"])
                & 1
            ) != 0
            reverse = (
                int(record["transform_flags"])
                & 2
            ) != 0
            matches_by_basis[basis_index].append(
                (
                    channel,
                    start,
                    int(record["gain_q15"]),
                    (
                        int(record["end_gain_q15"])
                        if linear
                        else None
                    ),
                    int(record["source_offset"]),
                    reverse,
                    float(normalized[int(row_index)]),
                )
            )
        executed_candidates += int(results.size)
        tile_count += 1
        last_evidence = evidence

    proposals: list[
        tuple[
            int,
            int,
            list[tuple[int, int, int, int | None, int, bool, float]],
        ]
    ] = []
    for basis_index, related in enumerate(matches_by_basis):
        channel, start = locations[basis_index]
        matches = [
            (channel, start, 32768, None, 0, False, 0.0),
            *related,
        ]
        if len(matches) < 2:
            continue
        estimated = (
            (len(matches) - 1) * block_samples * 2
            - len(matches) * 32
            - 16
        )
        if estimated > 0:
            proposals.append((estimated, basis_index, matches))
    proposals.sort(key=lambda item: (-item[0], item[1]))

    occupied = np.zeros((channels, complete_blocks), dtype=np.bool_)
    selected_bases: list[np.ndarray] = []
    instances: list[MafBasisInstance] = []
    normalized_errors: list[float] = []
    covered_by_channel = np.zeros(channels, dtype=np.int64)
    linear_instances = 0
    for _, source_index, matches in proposals:
        available = [
            item
            for item in matches
            if not occupied[item[0], item[1] // block_samples]
        ]
        if len(available) < 2:
            continue
        if len(selected_bases) >= maximum_bases:
            break
        capacity = maximum_instances - len(instances)
        if capacity < 2:
            break
        available = available[:capacity]
        if len(available) < 2:
            continue
        basis_id = len(selected_bases)
        selected_bases.append(
            block_matrix[source_index].astype(np.int64)
        )
        for (
            channel,
            start,
            gain,
            end_gain,
            source_offset,
            reverse,
            normalized_error,
        ) in available:
            occupied[channel, start // block_samples] = True
            normalized_errors.append(normalized_error)
            covered_by_channel[channel] += block_samples
            linear_instances += int(end_gain is not None)
            instances.append(
                MafBasisInstance(
                    emitter_id=channel,
                    basis_id=basis_id,
                    start=start,
                    gain_q15=gain,
                    source_offset=source_offset,
                    sample_count=block_samples,
                    circular=True,
                    end_gain_q15=end_gain,
                    reverse=reverse,
                )
            )

    return selected_bases, instances, {
        "search_mode": "foundry",
        "complete_hypothesis_language": True,
        "hypothesis_language": (
            "all fixed-lattice blocks x ordered unequal pairs x all "
            "circular phases x forward/reverse direction x signed "
            "constant/linear Q1.15 gain laws"
        ),
        "block_count": len(locations),
        "candidate_count": foundry.candidate_count(
            len(locations),
            block_samples,
        ),
        "executed_candidate_count": executed_candidates,
        "tile_count": tile_count,
        "fit_eligible_pair_count": sum(
            len(items) for items in matches_by_basis
        ),
        "proposal_count": len(proposals),
        "covered_blocks": int(np.count_nonzero(occupied)),
        "covered_samples": int(
            np.count_nonzero(occupied) * block_samples
        ),
        "covered_samples_by_channel": [
            int(value) for value in covered_by_channel
        ],
        "linear_gain_instance_count": linear_instances,
        "mean_normalized_fit_error": (
            float(np.mean(normalized_errors)) if normalized_errors else None
        ),
        "maximum_normalized_fit_error": (
            float(np.max(normalized_errors)) if normalized_errors else None
        ),
        "gpu": (
            {
                "device": last_evidence.device_name,
                "compute_capability": last_evidence.compute_capability,
                "nvrtc": last_evidence.nvrtc,
                "device_memory_bytes": last_evidence.device_memory_bytes,
                "tile_output_bytes": last_evidence.output_bytes,
            }
            if last_evidence is not None
            else None
        ),
    }


def encode_gain_orbit_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder: NativeMain0Decoder,
    block_samples: int,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
    maximum_bases: int = 256,
    maximum_instances: int = 4096,
    maximum_normalized_error: float = 5.0e-2,
    search_mode: str = "fast",
    foundry: GainPhaseCudaFoundry | None = None,
    foundry_tile_candidates: int = 1 << 20,
) -> MotifOrbitCandidate:
    """Encode one mono PCM16 signal as Basis instances plus exact Truth."""

    source_matrix = np.asarray(samples)
    if (
        source_matrix.ndim != 2
        or source_matrix.shape[1] != 1
        or source_matrix.dtype != np.int16
    ):
        raise TypeError("R-142 oracle currently requires mono PCM16")
    if not 64 <= block_samples <= 16384:
        raise ValueError("R-142 block size exceeds the first Basis profile")
    if not truth_block_sizes:
        raise ValueError("R-142 requires one or more Truth block sizes")
    source = source_matrix[:, 0].astype(np.int64)
    if search_mode == "foundry":
        if foundry is None:
            raise ValueError("Foundry mode requires the native CUDA backend")
        bases, instances, discovery = _discover_complete_cuda(
            source_matrix,
            block_samples,
            foundry=foundry,
            maximum_bases=maximum_bases,
            maximum_instances=maximum_instances,
            maximum_normalized_error=maximum_normalized_error,
            tile_candidates=foundry_tile_candidates,
        )
    elif search_mode == "fast":
        bases, instances, discovery = _discover_groups(
            source,
            block_samples,
            maximum_bases=maximum_bases,
            maximum_instances=maximum_instances,
            maximum_normalized_error=maximum_normalized_error,
        )
        discovery["search_mode"] = "fast"
        discovery["complete_hypothesis_language"] = False
    else:
        raise ValueError("search_mode must be 'foundry' or 'fast'")
    maf_payload = pack_maf_typed(
        sample_rate=sample_rate,
        total_frames=source.size,
        render_quantum=min(4096, source.size),
        output_channels=1,
        emitter_count=1,
        mixes=(MafMix(0, source.size, ((32767,),)),),
        bases=tuple(
            MafBasis(tuple(int(value) for value in basis))
            for basis in bases
        ),
        basis_instances=tuple(instances),
        declared_operations_per_frame=64,
    )
    prediction = native_decoder.decode_maf_typed(
        maf_payload,
        callback_frames=min(997, source.size),
    ).samples[:, 0].astype(np.int64)
    residual = source - prediction

    truth_candidates = [
        encode_lpc_liftpack_oracle(
            residual,
            block_size=int(truth_block_size),
        )
        for truth_block_size in truth_block_sizes
    ]
    truth_payload, truth_report = min(
        truth_candidates,
        key=lambda item: (len(item[0]), item[1]["block_size"]),
    )
    restored = (
        prediction
        + decode_lpc_liftpack_oracle(
            truth_payload,
            expected_count=source.size,
        )
    )
    if not np.array_equal(restored, source):
        raise RuntimeError("R-142 exact Truth composition failed")

    return MotifOrbitCandidate(
        maf_payload=maf_payload,
        truth_payload=truth_payload,
        reconstruction=restored.astype(np.int16)[:, None],
        report={
            "schema": "resonith-r142-gain-orbit-candidate-1",
            "status": "lossless research candidate; not a codec claim",
            "sample_rate": int(sample_rate),
            "frames": int(source.size),
            "block_samples": int(block_samples),
            "basis_count": len(bases),
            "instance_count": len(instances),
            "maf_bytes": len(maf_payload),
            "truth_bytes": len(truth_payload),
            "representation_bytes": len(maf_payload) + len(truth_payload),
            "truth": truth_report,
            "discovery": discovery,
        },
    )


def encode_optimized_independent_truth(
    samples: np.ndarray,
    *,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
) -> tuple[bytes, dict]:
    """Return the smallest admitted exact RSL2 stream for one mono signal."""

    source = np.asarray(samples)
    if (
        source.ndim != 2
        or source.shape[1] != 1
        or source.dtype != np.int16
    ):
        raise TypeError("R-142 Truth oracle currently requires mono PCM16")
    candidates = [
        encode_lpc_liftpack_oracle(
            source[:, 0],
            block_size=int(block_size),
        )
        for block_size in truth_block_sizes
    ]
    payload, report = min(
        candidates,
        key=lambda item: (len(item[0]), item[1]["block_size"]),
    )
    if not np.array_equal(
        decode_lpc_liftpack_oracle(
            payload,
            expected_count=source.shape[0],
        ),
        source[:, 0],
    ):
        raise RuntimeError("R-142 independent Truth round trip failed")
    return payload, report


def encode_multichannel_gain_orbit_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder: NativeMain0Decoder,
    block_samples: int,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
    maximum_normalized_error: float = 5.0e-2,
    maximum_bases: int = 256,
    maximum_instances: int = 4096,
    search_mode: str = "fast",
    foundry: GainPhaseCudaFoundry | None = None,
    foundry_tile_candidates: int = 1 << 20,
) -> MotifOrbitCandidate:
    """Search one shared phase/envelope Basis dictionary across all channels."""

    source_matrix = np.asarray(samples)
    if (
        source_matrix.ndim != 2
        or source_matrix.dtype != np.int16
        or not 1 <= source_matrix.shape[1] <= 8
    ):
        raise TypeError("R-147 oracle requires interleaved PCM16 channels")
    if not 64 <= block_samples <= 16384:
        raise ValueError("R-147 block size exceeds the first Basis profile")
    frames, channels = source_matrix.shape
    complete_blocks = frames // block_samples
    source64 = source_matrix.astype(np.int64)
    discovery: dict
    if search_mode == "foundry":
        if foundry is None:
            raise ValueError("Foundry mode requires the native CUDA backend")
        bases, instances, discovery = _discover_complete_cuda(
            source_matrix,
            block_samples,
            foundry=foundry,
            maximum_bases=maximum_bases,
            maximum_instances=maximum_instances,
            maximum_normalized_error=maximum_normalized_error,
            tile_candidates=foundry_tile_candidates,
        )
        covered_by_channel = np.asarray(
            discovery["covered_samples_by_channel"],
            dtype=np.int64,
        )
        linear_instances = int(
            discovery["linear_gain_instance_count"]
        )
    elif search_mode != "fast":
        raise ValueError("search_mode must be 'foundry' or 'fast'")

    if search_mode == "fast":
        discovery = {
            "search_mode": "fast",
            "complete_hypothesis_language": False,
        }
        buckets: dict[bytes, list[tuple[int, int]]] = {}
        for channel in range(channels):
            for block_index in range(complete_blocks):
                start = block_index * block_samples
                block = source64[start : start + block_samples, channel]
                if int(np.max(np.abs(block))) < 32:
                    continue
                buckets.setdefault(
                    _canonical_fingerprint(block),
                    [],
                ).append((channel, start))

        proposals: list[
            tuple[
                int,
                np.ndarray,
                list[tuple[int, int, int, int | None, int, float]],
            ]
        ] = []
        for locations in buckets.values():
            remaining = list(locations)
            while len(remaining) >= 2:
                seed_channel, seed_start = remaining[0]
                basis = source64[
                    seed_start : seed_start + block_samples,
                    seed_channel,
                ].copy()
                matches = []
                unmatched = []
                for channel, start in remaining:
                    gain, end_gain, source_offset, error = (
                        _fit_gain_envelope_shift_q15(
                            basis,
                            source64[
                                start : start + block_samples,
                                channel,
                            ],
                        )
                    )
                    if error <= maximum_normalized_error:
                        matches.append(
                            (
                                channel,
                                start,
                                gain,
                                end_gain,
                                source_offset,
                                error,
                            )
                        )
                    else:
                        unmatched.append((channel, start))
                if len(matches) >= 2:
                    estimated = (
                        (len(matches) - 1) * block_samples * 2
                        - len(matches) * 32
                        - 16
                    )
                    if estimated > 0:
                        proposals.append((estimated, basis, matches))
                    remaining = unmatched
                else:
                    remaining = remaining[1:]
        proposals.sort(key=lambda item: item[0], reverse=True)

        occupied = np.zeros((channels, complete_blocks), dtype=np.bool_)
        bases = []
        instances = []
        covered_by_channel = np.zeros(channels, dtype=np.int64)
        linear_instances = 0
        for _, basis, matches in proposals:
            available = [
                item
                for item in matches
                if not occupied[item[0], item[1] // block_samples]
            ]
            if len(available) < 2 or len(bases) >= maximum_bases:
                continue
            available = available[
                : maximum_instances - len(instances)
            ]
            if len(available) < 2:
                break
            basis_id = len(bases)
            bases.append(basis)
            for (
                channel,
                start,
                gain,
                end_gain,
                source_offset,
                _,
            ) in available:
                occupied[channel, start // block_samples] = True
                covered_by_channel[channel] += block_samples
                linear_instances += int(end_gain is not None)
                instances.append(
                    MafBasisInstance(
                        emitter_id=channel,
                        basis_id=basis_id,
                        start=start,
                        gain_q15=gain,
                        source_offset=source_offset,
                        sample_count=block_samples,
                        circular=True,
                        end_gain_q15=end_gain,
                    )
                )
            if len(instances) >= maximum_instances:
                break
        discovery.update(
            {
                "proposal_bucket_count": sum(
                    int(len(items) >= 2) for items in buckets.values()
                ),
                "proposal_count": len(proposals),
            }
        )

    matrix = tuple(
        tuple(
            32767 if output == emitter else 0
            for emitter in range(channels)
        )
        for output in range(channels)
    )
    maf_payload = pack_maf_typed(
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
        basis_instances=tuple(instances),
        declared_operations_per_frame=256,
    )
    prediction = native_decoder.decode_maf_typed(
        maf_payload,
        callback_frames=min(997, frames),
    ).samples.astype(np.int64)
    residual = source64 - prediction

    truth_parts = []
    truth_reports = []
    restored_channels = []
    for channel in range(channels):
        candidates = [
            encode_lpc_liftpack_oracle(
                residual[:, channel],
                block_size=int(block_size),
            )
            for block_size in truth_block_sizes
        ]
        payload, report = min(
            candidates,
            key=lambda item: (len(item[0]), item[1]["block_size"]),
        )
        truth_parts.append(struct.pack("<I", len(payload)) + payload)
        truth_reports.append(report)
        restored_channels.append(
            prediction[:, channel]
            + decode_lpc_liftpack_oracle(
                payload,
                expected_count=frames,
            )
        )
    reconstruction = np.column_stack(restored_channels)
    if not np.array_equal(reconstruction, source64):
        raise RuntimeError("R-147 exact multichannel Truth composition failed")
    truth_payload = b"".join(truth_parts)
    return MotifOrbitCandidate(
        maf_payload=maf_payload,
        truth_payload=truth_payload,
        reconstruction=reconstruction.astype(np.int16),
        report={
            "schema": "resonith-r147-cross-channel-orbit-candidate-1",
            "status": "lossless research candidate; not a codec claim",
            "sample_rate": int(sample_rate),
            "frames": int(frames),
            "channels": int(channels),
            "block_samples": int(block_samples),
            "basis_count": len(bases),
            "instance_count": len(instances),
            "linear_gain_instance_count": linear_instances,
            "covered_samples_by_channel": [
                int(value) for value in covered_by_channel
            ],
            "maf_bytes": len(maf_payload),
            "truth_bytes": len(truth_payload),
            "representation_bytes": len(maf_payload) + len(truth_payload),
            "truth": truth_reports,
            "discovery": discovery,
        },
    )
