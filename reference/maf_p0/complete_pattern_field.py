"""R-151 finite-complete multiscale pattern-search control plane.

Heavy pair/phase/envelope evaluation remains in the native C++23/CUDA
Foundry. This module declares the finite language, constructs every requested
time/channel cell from original PCM, and retains every quality-eligible result
for the global selector. It deliberately contains no semantic audio labels.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Iterable, Iterator

import numpy as np

from .foundry_cuda import GainPhaseCudaFoundry
from .hierarchical_grammar import (
    GrammarSelection,
    GrammarSpan,
    select_minimum_description,
)
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
class PatternScale:
    """One independently searched duration and complete origin lattice."""

    samples: int
    origin_step: int = 1

    def __post_init__(self) -> None:
        if not 2 <= self.samples <= 16384:
            raise ValueError("pattern duration exceeds the R-151 research bound")
        if self.origin_step <= 0:
            raise ValueError("pattern origin step must be positive")


@dataclass(frozen=True)
class PatternLanguage:
    """Published finite subset of the R-151 hypothesis language."""

    scales: tuple[PatternScale, ...]
    maximum_normalized_error: float
    include_constant_gain: bool = True
    include_linear_gain: bool = True
    include_circular_phase: bool = True

    def __post_init__(self) -> None:
        if not self.scales:
            raise ValueError("complete pattern language requires a scale")
        if len({item.samples for item in self.scales}) != len(self.scales):
            raise ValueError("pattern durations must be unique")
        if not 0.0 <= self.maximum_normalized_error <= 1.0:
            raise ValueError("normalized error must be in [0, 1]")
        if not (
            self.include_constant_gain
            and self.include_linear_gain
            and self.include_circular_phase
        ):
            raise ValueError(
                "the current native R-151 kernel evaluates all schema-1 laws"
            )


@dataclass(frozen=True)
class PatternLocation:
    """Absolute location of one original-PCM analysis cell."""

    channel: int
    start: int


@dataclass(frozen=True)
class PatternMatch:
    """One exact fixed-point Basis-orbit result retained after quality gating."""

    scale_samples: int
    basis: PatternLocation
    target: PatternLocation
    source_offset: int
    gain_q15: int
    end_gain_q15: int | None
    squared_error: int
    target_energy: int
    reverse: bool = False

    @property
    def normalized_error(self) -> float:
        return self.squared_error / max(1, self.target_energy)


@dataclass(frozen=True)
class ScaleEvidence:
    """Cardinality and execution evidence for one independently searched scale."""

    samples: int
    origin_step: int
    block_count: int
    candidate_count: int
    executed_candidate_count: int
    eligible_match_count: int
    cuda_device: str
    cuda_compute_capability: str
    nvrtc_version: str


@dataclass(frozen=True)
class CompletePatternResult:
    """All quality-eligible results and proof of complete lattice execution."""

    language: PatternLanguage
    matches: tuple[PatternMatch, ...]
    scales: tuple[ScaleEvidence, ...]

    @property
    def candidate_count(self) -> int:
        return sum(item.candidate_count for item in self.scales)

    @property
    def executed_candidate_count(self) -> int:
        return sum(item.executed_candidate_count for item in self.scales)


@dataclass(frozen=True)
class PatternRdoCandidate:
    """One emitted-span cost offered to the exact bounded global chart."""

    match: PatternMatch
    basis_id: str
    activation_bytes: int
    placement_and_correction_bytes: int


@dataclass(frozen=True)
class PatternRdoResult:
    """Exact bounded dictionary-activation and non-overlap selection."""

    selection: GrammarSelection
    candidate_count: int
    safely_rejected_basis_count: int


@dataclass(frozen=True)
class PatternFieldCandidate:
    """One emitted lossless MFT1 plus Truth candidate or exact fallback."""

    selected_kind: str
    maf_payload: bytes
    truth_payload: bytes
    reconstruction: np.ndarray
    report: dict


def _scale_blocks(
    samples: np.ndarray,
    scale: PatternScale,
) -> tuple[np.ndarray, tuple[PatternLocation, ...]]:
    frames, channels = samples.shape
    locations = tuple(
        PatternLocation(channel, start)
        for channel in range(channels)
        for start in range(
            0,
            frames - scale.samples + 1,
            scale.origin_step,
        )
    )
    if len(locations) < 2:
        return (
            np.empty((0, scale.samples), dtype=np.int16),
            locations,
        )
    blocks = np.empty(
        (len(locations), scale.samples),
        dtype=np.int16,
    )
    for index, location in enumerate(locations):
        blocks[index] = samples[
            location.start : location.start + scale.samples,
            location.channel,
        ]
    return blocks, locations


def _eligible_rows(
    rows: np.ndarray,
    maximum_normalized_error: float,
) -> Iterator[np.void]:
    energy = rows["target_energy"]
    error = rows["squared_error"]
    eligible = error.astype(np.float64) <= (
        np.maximum(energy, 1).astype(np.float64)
        * maximum_normalized_error
    )
    yield from rows[eligible]


def search_complete_pattern_field(
    samples: np.ndarray,
    *,
    language: PatternLanguage,
    foundry: GainPhaseCudaFoundry,
    tile_candidates: int = 1 << 20,
) -> CompletePatternResult:
    """Evaluate every candidate in the declared multiscale/channel language."""

    source = np.asarray(samples)
    if (
        source.ndim != 2
        or source.dtype != np.int16
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-151 search requires interleaved PCM16 channels")
    if tile_candidates <= 0:
        raise ValueError("tile_candidates must be positive")

    matches: list[PatternMatch] = []
    evidence: list[ScaleEvidence] = []
    for scale in language.scales:
        blocks, locations = _scale_blocks(source, scale)
        if blocks.shape[0] < 2:
            evidence.append(
                ScaleEvidence(
                    samples=scale.samples,
                    origin_step=scale.origin_step,
                    block_count=int(blocks.shape[0]),
                    candidate_count=0,
                    executed_candidate_count=0,
                    eligible_match_count=0,
                    cuda_device="not-run",
                    cuda_compute_capability="not-run",
                    nvrtc_version="not-run",
                )
            )
            continue
        candidate_count = foundry.candidate_count(
            int(blocks.shape[0]),
            scale.samples,
        )
        executed = 0
        eligible_count = 0
        last_device = ""
        last_compute = ""
        last_nvrtc = ""
        for rows, tile_evidence in foundry.evaluate_tiles(
            blocks,
            tile_candidates=tile_candidates,
        ):
            executed += int(rows.size)
            last_device = tile_evidence.device_name
            last_compute = tile_evidence.compute_capability
            last_nvrtc = tile_evidence.nvrtc
            for row in _eligible_rows(
                rows,
                language.maximum_normalized_error,
            ):
                flags = int(row["transform_flags"])
                matches.append(
                    PatternMatch(
                        scale_samples=scale.samples,
                        basis=locations[int(row["basis_index"])],
                        target=locations[int(row["target_index"])],
                        source_offset=int(row["source_offset"]),
                        gain_q15=int(row["gain_q15"]),
                        end_gain_q15=(
                            int(row["end_gain_q15"])
                            if flags & 1
                            else None
                        ),
                        squared_error=int(row["squared_error"]),
                        target_energy=int(row["target_energy"]),
                        reverse=bool(flags & 2),
                    )
                )
                eligible_count += 1
        if executed != candidate_count:
            raise RuntimeError("R-151 CUDA search omitted declared candidates")
        evidence.append(
            ScaleEvidence(
                samples=scale.samples,
                origin_step=scale.origin_step,
                block_count=int(blocks.shape[0]),
                candidate_count=candidate_count,
                executed_candidate_count=executed,
                eligible_match_count=eligible_count,
                cuda_device=last_device,
                cuda_compute_capability=last_compute,
                nvrtc_version=last_nvrtc,
            )
        )
    return CompletePatternResult(
        language=language,
        matches=tuple(matches),
        scales=tuple(evidence),
    )


def assert_cpu_gpu_parity(
    samples: np.ndarray,
    *,
    language: PatternLanguage,
    foundry: GainPhaseCudaFoundry,
    tile_candidates: int = 1 << 16,
) -> int:
    """Require byte-identical CPU/GPU result records at every declared scale."""

    source = np.asarray(samples)
    if source.ndim != 2 or source.dtype != np.int16:
        raise TypeError("R-151 parity requires interleaved PCM16 channels")
    compared = 0
    for scale in language.scales:
        blocks, _ = _scale_blocks(source, scale)
        if blocks.shape[0] < 2:
            continue
        cpu = foundry.evaluate_cpu_tiles(
            blocks,
            tile_candidates=tile_candidates,
        )
        gpu = (
            rows
            for rows, _ in foundry.evaluate_tiles(
                blocks,
                tile_candidates=tile_candidates,
            )
        )
        for cpu_rows, gpu_rows in zip(cpu, gpu, strict=True):
            if not np.array_equal(cpu_rows, gpu_rows):
                raise RuntimeError("R-151 CPU/GPU fixed-point parity failed")
            compared += int(cpu_rows.size)
    return compared


def select_complete_pattern_cover(
    frame_count: int,
    channel_count: int,
    truth_bytes_by_sample: Iterable[int],
    candidates: Iterable[PatternRdoCandidate],
    *,
    maximum_basis_families: int = 20,
) -> PatternRdoResult:
    """Select a globally non-overlapping multichannel cover with Basis costs.

    Channels are concatenated only for chart indexing. Basis identifiers remain
    global, so one immutable dictionary activation can serve every channel.
    """

    if frame_count < 0 or channel_count <= 0:
        raise ValueError("invalid R-151 output dimensions")
    truth = tuple(int(value) for value in truth_bytes_by_sample)
    if len(truth) != frame_count * channel_count:
        raise ValueError("Truth prices must cover every channel/sample")
    materialized = tuple(candidates)
    activation: dict[str, int] = {}
    spans: list[GrammarSpan] = []
    for index, item in enumerate(materialized):
        match = item.match
        if not (
            0 <= match.target.channel < channel_count
            and 0 <= match.target.start
            and match.target.start + match.scale_samples <= frame_count
        ):
            raise ValueError("pattern placement exceeds the output")
        previous = activation.setdefault(
            item.basis_id,
            int(item.activation_bytes),
        )
        if previous != int(item.activation_bytes):
            raise ValueError("one Basis has inconsistent activation cost")
        start = (
            match.target.channel * frame_count
            + match.target.start
        )
        spans.append(
            GrammarSpan(
                start=start,
                end=start + match.scale_samples,
                payload_bytes=int(item.placement_and_correction_bytes),
                label=f"pattern-{index}",
                basis_id=item.basis_id,
            )
        )

    # A Basis whose maximum independent gross saving cannot pay activation is
    # mathematically dominated. Removing it preserves the exact optimum.
    spans_by_basis: dict[str, list[GrammarSpan]] = {}
    for span in spans:
        assert span.basis_id is not None
        spans_by_basis.setdefault(span.basis_id, []).append(span)
    rejected: set[str] = set()
    for basis_id, basis_spans in spans_by_basis.items():
        gross_upper_bound = 0
        for span in basis_spans:
            truth_cost = sum(truth[span.start : span.end])
            gross_upper_bound += max(0, truth_cost - span.payload_bytes)
        if gross_upper_bound <= activation[basis_id]:
            rejected.add(basis_id)
    admitted_spans = tuple(
        span for span in spans if span.basis_id not in rejected
    )
    admitted_activation = {
        basis_id: cost
        for basis_id, cost in activation.items()
        if basis_id not in rejected
    }
    selection = select_minimum_description(
        frame_count * channel_count,
        truth,
        admitted_spans,
        admitted_activation,
        maximum_basis_families=maximum_basis_families,
    )
    return PatternRdoResult(
        selection=selection,
        candidate_count=len(materialized),
        safely_rejected_basis_count=len(rejected),
    )


def _round_divide_away(numerator: int, denominator: int) -> int:
    if numerator >= 0:
        return (numerator + denominator // 2) // denominator
    return -((-numerator + denominator // 2) // denominator)


def _render_match(
    basis: np.ndarray,
    match: PatternMatch,
) -> np.ndarray:
    """Render the exact schema-1 transform before output-matrix scaling."""

    length = match.scale_samples
    output = np.empty(length, dtype=np.int64)
    for sample in range(length):
        source_index = (
            (
                match.source_offset + length - sample % length
            ) % length
            if match.reverse
            else (match.source_offset + sample) % length
        )
        gain = match.gain_q15
        if match.end_gain_q15 is not None and length > 1:
            gain += _round_divide_away(
                (match.end_gain_q15 - match.gain_q15) * sample,
                length - 1,
            )
        output[sample] = _round_divide_away(
            int(basis[source_index]) * gain,
            32768,
        )
    return output


def _optimized_truth(
    values: np.ndarray,
    block_sizes: tuple[int, ...],
) -> tuple[bytes, dict]:
    candidates = [
        encode_lpc_liftpack_oracle(
            np.asarray(values, dtype=np.int64),
            block_size=int(block_size),
        )
        for block_size in block_sizes
    ]
    return min(
        candidates,
        key=lambda item: (len(item[0]), int(item[1]["block_size"])),
    )


def encode_complete_pattern_field_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    search: CompletePatternResult,
    native_decoder: NativeMain0Decoder,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
    maximum_basis_families: int = 20,
) -> PatternFieldCandidate:
    """Run exact bounded global selection, emit MFT1, and verify Truth.

    The chart uses independently decodable local correction payloads as an
    additive lower-level price. Admission is decided again from the actual
    complete MFT1 and whole-channel Truth payloads, so a proxy win can never
    make the final lossless stream larger than the independent fallback.
    """

    source = np.asarray(samples)
    if (
        source.ndim != 2
        or source.dtype != np.int16
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("R-151 candidate requires interleaved PCM16 channels")
    if sample_rate <= 0 or not truth_block_sizes:
        raise ValueError("invalid R-151 sample rate or Truth lattice")
    frames, channels = source.shape
    source64 = source.astype(np.int64)

    basis_values: dict[str, np.ndarray] = {}
    rdo_candidates: list[PatternRdoCandidate] = []
    candidate_identity: set[tuple[str, int, int]] = set()
    best_matches: dict[
        tuple[str, int, int, int],
        PatternMatch,
    ] = {}
    for match in search.matches:
        basis = source64[
            match.basis.start : match.basis.start + match.scale_samples,
            match.basis.channel,
        ]
        basis_bytes = np.asarray(basis, dtype="<i2").tobytes()
        basis_id = (
            f"basis-{match.scale_samples}-"
            + hashlib.blake2s(basis_bytes, digest_size=12).hexdigest()
        )
        basis_values.setdefault(basis_id, basis.copy())
        key = (
            basis_id,
            match.target.channel,
            match.target.start,
            match.scale_samples,
        )
        previous = best_matches.get(key)
        rank = (
            match.squared_error,
            int(match.reverse),
            match.source_offset,
            abs(match.gain_q15),
            match.gain_q15,
            match.end_gain_q15 or 0,
        )
        if previous is None:
            best_matches[key] = match
        else:
            previous_rank = (
                previous.squared_error,
                int(previous.reverse),
                previous.source_offset,
                abs(previous.gain_q15),
                previous.gain_q15,
                previous.end_gain_q15 or 0,
            )
            if rank < previous_rank:
                best_matches[key] = match

        identity_key = (
            basis_id,
            match.basis.channel,
            match.basis.start,
        )
        if identity_key not in candidate_identity:
            candidate_identity.add(identity_key)
            identity = PatternMatch(
                scale_samples=match.scale_samples,
                basis=match.basis,
                target=match.basis,
                source_offset=0,
                gain_q15=32768,
                end_gain_q15=None,
                squared_error=0,
                target_energy=int(np.dot(basis, basis)),
            )
            rdo_candidates.append(
                PatternRdoCandidate(
                    identity,
                    basis_id,
                    16 + 2 * match.scale_samples,
                    32,
                )
            )

    for key, match in sorted(
        best_matches.items(),
        key=lambda item: (
            item[0],
            item[1].target.channel,
            item[1].target.start,
        ),
    ):
        basis_id = key[0]
        basis = basis_values[basis_id]
        target = source64[
            match.target.start : match.target.start + match.scale_samples,
            match.target.channel,
        ]
        residual = target - _render_match(basis, match)
        if np.any(residual):
            correction, _ = _optimized_truth(
                residual,
                truth_block_sizes,
            )
            correction_bytes = len(correction)
        else:
            correction_bytes = 0
        rdo_candidates.append(
            PatternRdoCandidate(
                match,
                basis_id,
                16 + 2 * match.scale_samples,
                32 + correction_bytes,
            )
        )

    truth_price = (2,) * (frames * channels)
    rdo = select_complete_pattern_cover(
        frames,
        channels,
        truth_price,
        rdo_candidates,
        maximum_basis_families=maximum_basis_families,
    )
    selected_indices = tuple(
        int(span.label.removeprefix("pattern-"))
        for span in rdo.selection.selected_spans
    )
    selected_candidates = tuple(rdo_candidates[index] for index in selected_indices)
    selected_basis_ids = tuple(
        sorted({item.basis_id for item in selected_candidates})
    )
    basis_indices = {
        basis_id: index
        for index, basis_id in enumerate(selected_basis_ids)
    }
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
            MafBasis(tuple(int(value) for value in basis_values[basis_id]))
            for basis_id in selected_basis_ids
        ),
        basis_instances=tuple(
            MafBasisInstance(
                emitter_id=item.match.target.channel,
                basis_id=basis_indices[item.basis_id],
                start=item.match.target.start,
                gain_q15=item.match.gain_q15,
                source_offset=item.match.source_offset,
                sample_count=item.match.scale_samples,
                circular=True,
                end_gain_q15=item.match.end_gain_q15,
                reverse=item.match.reverse,
            )
            for item in selected_candidates
        ),
        declared_operations_per_frame=512,
    )
    prediction = native_decoder.decode_maf_typed(
        maf_payload,
        callback_frames=min(997, frames),
    ).samples.astype(np.int64)
    residual = source64 - prediction

    truth_parts: list[bytes] = []
    restored_channels: list[np.ndarray] = []
    truth_reports: list[dict] = []
    independent_parts: list[bytes] = []
    independent_reports: list[dict] = []
    for channel in range(channels):
        truth, truth_report = _optimized_truth(
            residual[:, channel],
            truth_block_sizes,
        )
        independent, independent_report = _optimized_truth(
            source64[:, channel],
            truth_block_sizes,
        )
        truth_parts.append(struct.pack("<I", len(truth)) + truth)
        independent_parts.append(struct.pack("<I", len(independent)) + independent)
        truth_reports.append(truth_report)
        independent_reports.append(independent_report)
        restored_channels.append(
            prediction[:, channel]
            + decode_lpc_liftpack_oracle(
                truth,
                expected_count=frames,
            )
        )
    reconstruction = np.column_stack(restored_channels)
    if not np.array_equal(reconstruction, source64):
        raise RuntimeError("R-151 complete-pattern Truth verification failed")

    truth_payload = b"".join(truth_parts)
    independent_payload = b"".join(independent_parts)
    structured_bytes = len(maf_payload) + len(truth_payload)
    independent_bytes = len(independent_payload)
    if structured_bytes < independent_bytes:
        selected_kind = "complete-pattern-field"
        output_maf = maf_payload
        output_truth = truth_payload
        output_reconstruction = reconstruction.astype(np.int16)
    else:
        selected_kind = "independent-truth-fallback"
        output_maf = b""
        output_truth = independent_payload
        output_reconstruction = source.copy()
    return PatternFieldCandidate(
        selected_kind=selected_kind,
        maf_payload=output_maf,
        truth_payload=output_truth,
        reconstruction=output_reconstruction,
        report={
            "schema": "resonith-r151-complete-pattern-candidate-1",
            "status": "lossless research candidate; not a codec claim",
            "sample_rate": int(sample_rate),
            "frames": int(frames),
            "channels": int(channels),
            "searched_candidates": search.candidate_count,
            "eligible_matches": len(search.matches),
            "rdo_candidate_count": len(rdo_candidates),
            "chart_states": rdo.selection.state_count,
            "chart_proxy_bytes": rdo.selection.complete_bytes,
            "safely_rejected_basis_count": rdo.safely_rejected_basis_count,
            "selected_basis_count": len(selected_basis_ids),
            "selected_instance_count": len(selected_candidates),
            "maf_bytes": len(maf_payload),
            "structured_truth_bytes": len(truth_payload),
            "structured_complete_bytes": structured_bytes,
            "independent_truth_bytes": independent_bytes,
            "selected_kind": selected_kind,
            "truth": truth_reports,
            "independent_truth": independent_reports,
        },
    )
