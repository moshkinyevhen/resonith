"""R-156/R-157 gridless warp search with exact Truth and global byte RDO."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np

from .complete_pattern_field import (
    PatternLocation,
    PatternMatch,
    PatternRdoCandidate,
    _optimized_truth,
    select_complete_pattern_cover,
)
from .foundry_cuda import GainPhaseCudaFoundry
from .gridless_pattern_field import GridlessPatternField
from .lpc_oracle import decode_lpc_liftpack_oracle
from .maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    pack_maf_typed,
)
from .warp_dictionary import WarpFit, _apply_gain, _render_basis


@dataclass(frozen=True)
class GridlessWarpMatch:
    """One exact R-157 result between arbitrary absolute intervals."""

    sample_count: int
    basis: PatternLocation
    target: PatternLocation
    fit: WarpFit
    squared_error: int
    target_energy: int

    @property
    def normalized_error(self) -> float:
        return self.squared_error / max(1, self.target_energy)


@dataclass(frozen=True)
class GridlessWarpSearch:
    """Complete execution evidence for the declared R-156 origin union."""

    matches: tuple[GridlessWarpMatch, ...]
    report: dict


@dataclass(frozen=True)
class GridlessTruthCandidate:
    """One lossless structured candidate or independent Truth fallback."""

    selected_kind: str
    maf_payload: bytes
    truth_payload: bytes
    reconstruction: np.ndarray
    report: dict


def _declared_locations(
    field: GridlessPatternField,
    sample_count: int,
) -> tuple[PatternLocation, ...]:
    """Materialize the exact content-anchor plus overlap-origin union."""

    locations: set[tuple[int, int]] = set()
    for origin_set in field.origin_sets:
        if origin_set.sample_count != sample_count:
            continue
        locations.update(
            (origin_set.channel, int(start))
            for start in origin_set.content_defined_origins
        )
        locations.update(
            (
                origin_set.channel,
                origin_set.regular_first
                    + index * origin_set.regular_hop,
            )
            for index in range(origin_set.regular_count)
        )
    return tuple(
        PatternLocation(channel, start)
        for channel, start in sorted(locations)
        if start + sample_count <= field.frames
    )


def search_gridless_warp_field(
    samples: np.ndarray,
    *,
    field: GridlessPatternField,
    foundry: GainPhaseCudaFoundry,
    phase_subsamples: int = 4,
    step_radius: int = 2,
    step_increment_q16: int = 512,
    end_step_radius: int = 1,
    maximum_normalized_error: float = 2.0e-2,
    tile_candidates: int = 1 << 20,
) -> GridlessWarpSearch:
    """Evaluate every R-157 law over every declared R-156 interval pair."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.shape != (field.frames, field.channels)
    ):
        raise TypeError("gridless warp field differs from its PCM source")
    if not 0.0 <= maximum_normalized_error <= 1.0:
        raise ValueError("normalized-error threshold must be in [0, 1]")
    matches: list[GridlessWarpMatch] = []
    scale_reports: list[dict] = []
    executed_total = 0
    declared_total = 0
    for sample_count in field.scales:
        locations = _declared_locations(field, sample_count)
        if len(locations) < 2:
            scale_reports.append({
                "sample_count": sample_count,
                "location_count": len(locations),
                "candidate_count": 0,
                "executed_candidate_count": 0,
                "eligible_match_count": 0,
            })
            continue
        blocks = np.stack(
            tuple(
                source[
                    location.start : location.start + sample_count,
                    location.channel,
                ]
                for location in locations
            )
        )
        declared = foundry.warp_candidate_count(
            len(locations),
            sample_count,
            phase_subsamples=phase_subsamples,
            step_radius=step_radius,
            step_increment_q16=step_increment_q16,
            end_step_radius=end_step_radius,
        )
        declared_total += declared
        executed = 0
        eligible = 0
        device = ""
        compute = ""
        nvrtc = ""
        for rows, evidence in foundry.evaluate_warp_tiles(
            blocks,
            phase_subsamples=phase_subsamples,
            step_radius=step_radius,
            step_increment_q16=step_increment_q16,
            end_step_radius=end_step_radius,
            tile_candidates=tile_candidates,
        ):
            executed += int(rows.size)
            device = evidence.device_name
            compute = evidence.compute_capability
            nvrtc = evidence.nvrtc
            threshold = (
                np.maximum(rows["target_energy"], 1).astype(np.float64)
                * maximum_normalized_error
            )
            for row in rows[
                rows["squared_error"].astype(np.float64) <= threshold
            ]:
                flags = int(row["transform_flags"])
                matches.append(
                    GridlessWarpMatch(
                        sample_count,
                        locations[int(row["basis_index"])],
                        locations[int(row["target_index"])],
                        WarpFit(
                            int(row["source_position_q16"]),
                            int(row["source_step_q16"]),
                            (
                                int(row["end_source_step_q16"])
                                if flags & 2
                                else None
                            ),
                            int(row["gain_q15"]),
                            (
                                int(row["end_gain_q15"])
                                if flags & 1
                                else None
                            ),
                            int(row["squared_error"])
                                / max(1, int(row["target_energy"])),
                        ),
                        int(row["squared_error"]),
                        int(row["target_energy"]),
                    )
                )
                eligible += 1
        if executed != declared:
            raise RuntimeError("R-157 CUDA omitted declared warp candidates")
        executed_total += executed
        scale_reports.append({
            "sample_count": sample_count,
            "location_count": len(locations),
            "candidate_count": declared,
            "executed_candidate_count": executed,
            "eligible_match_count": eligible,
            "cuda_device": device,
            "compute_capability": compute,
            "nvrtc": nvrtc,
        })
    return GridlessWarpSearch(
        tuple(matches),
        {
            "schema": "resonith-r157-gridless-warp-search-1",
            "status": "complete declared finite lattice; RDO not implied",
            "candidate_count": declared_total,
            "executed_candidate_count": executed_total,
            "eligible_match_count": len(matches),
            "phase_subsamples": phase_subsamples,
            "step_radius": step_radius,
            "step_increment_q16": step_increment_q16,
            "end_step_radius": end_step_radius,
            "maximum_normalized_error": maximum_normalized_error,
            "scales": scale_reports,
        },
    )


def _render_gridless_match(
    basis: np.ndarray,
    match: GridlessWarpMatch,
) -> np.ndarray:
    rendered = _render_basis(
        basis,
        match.sample_count,
        match.fit.source_position_q16,
        match.fit.source_step_q16,
        match.fit.end_source_step_q16,
    )
    return _apply_gain(
        rendered,
        match.fit.gain_q15,
        match.fit.end_gain_q15,
    )


def _pattern_proxy(match: GridlessWarpMatch) -> PatternMatch:
    """Adapt an R-157 span to the already-proved R-150 chart interface."""

    return PatternMatch(
        scale_samples=match.sample_count,
        basis=match.basis,
        target=match.target,
        source_offset=0,
        gain_q15=match.fit.gain_q15,
        end_gain_q15=match.fit.end_gain_q15,
        squared_error=match.squared_error,
        target_energy=match.target_energy,
    )


def encode_gridless_truth_candidate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    search: GridlessWarpSearch,
    native_decoder,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
    maximum_basis_families: int = 20,
) -> GridlessTruthCandidate:
    """Select Basis+warp+exact correction globally and verify PCM identity."""

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or not 1 <= source.shape[1] <= 8
        or sample_rate <= 0
    ):
        raise TypeError("gridless Truth RDO requires interleaved PCM16")
    frames, channels = source.shape
    source64 = source.astype(np.int64)
    basis_values: dict[str, np.ndarray] = {}
    best: dict[tuple[str, int, int, int], GridlessWarpMatch] = {}
    for match in search.matches:
        basis = source64[
            match.basis.start : match.basis.start + match.sample_count,
            match.basis.channel,
        ]
        basis_id = (
            f"warp-{match.sample_count}-"
            + hashlib.blake2s(
                np.asarray(basis, dtype="<i2").tobytes(),
                digest_size=12,
            ).hexdigest()
        )
        basis_values.setdefault(basis_id, basis.copy())
        key = (
            basis_id,
            match.target.channel,
            match.target.start,
            match.sample_count,
        )
        previous = best.get(key)
        rank = (
            match.squared_error,
            match.fit.end_source_step_q16 is not None,
            match.fit.end_gain_q15 is not None,
            abs(abs(match.fit.source_step_q16) - 65536),
            match.fit.source_position_q16,
        )
        if previous is None:
            best[key] = match
        else:
            previous_rank = (
                previous.squared_error,
                previous.fit.end_source_step_q16 is not None,
                previous.fit.end_gain_q15 is not None,
                abs(abs(previous.fit.source_step_q16) - 65536),
                previous.fit.source_position_q16,
            )
            if rank < previous_rank:
                best[key] = match

    rdo_candidates: list[PatternRdoCandidate] = []
    warp_candidates: list[tuple[str, GridlessWarpMatch]] = []
    identity_seen: set[tuple[str, int, int]] = set()
    for key, match in sorted(best.items()):
        basis_id = key[0]
        identity_key = (
            basis_id,
            match.basis.channel,
            match.basis.start,
        )
        if identity_key not in identity_seen:
            identity_seen.add(identity_key)
            identity_match = GridlessWarpMatch(
                match.sample_count,
                match.basis,
                match.basis,
                WarpFit(0, 65536, None, 32768, None, 0.0),
                0,
                int(np.dot(
                    basis_values[basis_id],
                    basis_values[basis_id],
                )),
            )
            warp_candidates.append((basis_id, identity_match))
            rdo_candidates.append(
                PatternRdoCandidate(
                    _pattern_proxy(identity_match),
                    basis_id,
                    16 + 2 * match.sample_count,
                    48,
                )
            )
        target = source64[
            match.target.start : match.target.start + match.sample_count,
            match.target.channel,
        ]
        correction_values = (
            target - _render_gridless_match(basis_values[basis_id], match)
        )
        correction_bytes = 0
        if np.any(correction_values):
            correction, _ = _optimized_truth(
                correction_values,
                truth_block_sizes,
            )
            correction_bytes = len(correction)
        warp_candidates.append((basis_id, match))
        rdo_candidates.append(
            PatternRdoCandidate(
                _pattern_proxy(match),
                basis_id,
                16 + 2 * match.sample_count,
                48 + correction_bytes,
            )
        )

    rdo = select_complete_pattern_cover(
        frames,
        channels,
        (2,) * (frames * channels),
        rdo_candidates,
        maximum_basis_families=maximum_basis_families,
    )
    selected_indices = tuple(
        int(span.label.removeprefix("pattern-"))
        for span in rdo.selection.selected_spans
    )
    selected = tuple(warp_candidates[index] for index in selected_indices)
    basis_ids = tuple(sorted({basis_id for basis_id, _ in selected}))
    basis_index = {
        basis_id: index for index, basis_id in enumerate(basis_ids)
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
            for basis_id in basis_ids
        ),
        basis_warp_instances=tuple(
            MafBasisWarpInstance(
                emitter_id=match.target.channel,
                basis_id=basis_index[basis_id],
                start=match.target.start,
                sample_count=match.sample_count,
                source_position_q16=match.fit.source_position_q16,
                source_step_q16=match.fit.source_step_q16,
                gain_q15=match.fit.gain_q15,
                circular=True,
                end_source_step_q16=match.fit.end_source_step_q16,
                end_gain_q15=match.fit.end_gain_q15,
            )
            for basis_id, match in selected
        ),
        declared_operations_per_frame=512,
    )
    prediction = native_decoder.decode_maf_typed(
        maf_payload,
        callback_frames=min(997, frames),
    ).samples.astype(np.int64)
    residual = source64 - prediction
    truth_parts: list[bytes] = []
    independent_parts: list[bytes] = []
    restored_channels = []
    for channel in range(channels):
        truth, _ = _optimized_truth(
            residual[:, channel],
            truth_block_sizes,
        )
        independent, _ = _optimized_truth(
            source64[:, channel],
            truth_block_sizes,
        )
        truth_parts.append(struct.pack("<I", len(truth)) + truth)
        independent_parts.append(
            struct.pack("<I", len(independent)) + independent
        )
        restored_channels.append(
            prediction[:, channel]
            + decode_lpc_liftpack_oracle(
                truth,
                expected_count=frames,
            )
        )
    reconstruction = np.column_stack(restored_channels)
    if not np.array_equal(reconstruction, source64):
        raise RuntimeError("R-157 exact Truth correction changed PCM")
    truth_payload = b"".join(truth_parts)
    independent_payload = b"".join(independent_parts)
    structured_bytes = len(maf_payload) + len(truth_payload)
    independent_bytes = len(independent_payload)
    if structured_bytes < independent_bytes:
        selected_kind = "gridless-warp-truth"
        output_maf = maf_payload
        output_truth = truth_payload
        output_reconstruction = reconstruction.astype(np.int16)
    else:
        selected_kind = "independent-truth-fallback"
        output_maf = b""
        output_truth = independent_payload
        output_reconstruction = source.copy()
    output_reconstruction.flags.writeable = False
    return GridlessTruthCandidate(
        selected_kind,
        output_maf,
        output_truth,
        output_reconstruction,
        {
            "schema": "resonith-r157-gridless-truth-rdo-1",
            "status": "lossless complete-byte gate; not a lossy codec claim",
            "searched_candidates": search.report["candidate_count"],
            "eligible_matches": len(search.matches),
            "rdo_candidate_count": len(rdo_candidates),
            "chart_states": rdo.selection.state_count,
            "selected_basis_count": len(basis_ids),
            "selected_instance_count": len(selected),
            "maf_bytes": len(maf_payload),
            "structured_truth_bytes": len(truth_payload),
            "structured_complete_bytes": structured_bytes,
            "independent_truth_bytes": independent_bytes,
            "selected_kind": selected_kind,
            "exact_pcm": True,
        },
    )
