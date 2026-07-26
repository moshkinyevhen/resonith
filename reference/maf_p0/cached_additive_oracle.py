"""Held-out complete-byte oracle for cached simultaneous periodic causes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Sequence

import numpy as np

from cibs0 import CIBS0Model, materialize_basis

from .additive_oracle import _period_candidates
from .codec import _quality_report, _quantize_signed
from .composition import GainEventLaw
from .lpc_oracle import (
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
)
from .main0 import _sparse_block_gain_law
from .model import encode_basis_latent
from .periodic import (
    PhaseTrajectory,
    analyze_periodic_basis,
    constant_phase_trajectory,
    fit_block_gains,
    render_basis_trajectory,
)
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import (
    CachedCIBSBasis,
    PeriodicAtom,
    StreamConfig,
    pack_bcib,
    pack_conf,
    pack_periodic_atom,
)


REGISTRY_HEADER = struct.Struct("<4sBBBBIHH")
REGISTRY_STAGE = struct.Struct("<BBH")


@dataclass(frozen=True)
class CachedPeriodicAtom:
    """One prospective Atom backed by a frozen CIBS registry model."""

    latent: np.ndarray
    expected_sha256: bytes
    basis: np.ndarray
    trajectory: PhaseTrajectory
    gain_law: GainEventLaw


@dataclass(frozen=True)
class CachedAdditiveOracleResult:
    """Selected prospective stream and complete gate evidence."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def pack_registry_model(model: CIBS0Model) -> bytes:
    """Serialize deterministic development-ROM bytes for cost accounting."""

    model.validate()
    model_id = model.model_id.encode("utf-8")
    output = bytearray(
        REGISTRY_HEADER.pack(
            b"CRM1",
            len(model_id),
            model.basis_channels,
            len(model.refinement_kernels),
            model.projection_shift,
            model.coarse_length,
            model.latent_elements,
            0,
        )
    )
    output += model_id
    output += model.projection.astype(np.int8, copy=False).tobytes(order="C")
    output += model.projection_bias.astype("<i4", copy=False).tobytes(order="C")
    for kernel, shift in zip(
        model.refinement_kernels,
        model.refinement_shifts,
        strict=True,
    ):
        output += REGISTRY_STAGE.pack(kernel.shape[1], shift, 0)
        output += kernel.astype(np.int8, copy=False).tobytes(order="C")
    return bytes(output)


def _wide_scaled_prediction(
    unity_prediction: np.ndarray,
    gain_law: GainEventLaw,
) -> np.ndarray:
    """Apply the normative Q15 gain law without an intermediate PCM clip."""

    unity = np.asarray(unity_prediction)
    if unity.dtype != np.int16 or unity.ndim != 1:
        raise TypeError("cached Atom unity prediction must be mono int16")
    if unity.size != gain_law.sample_count:
        raise ValueError("cached Atom gain law differs from its trajectory")
    positions = np.arange(unity.size, dtype=np.uint32)
    event_indices = np.searchsorted(
        gain_law.positions,
        positions,
        side="right",
    ) - 1
    gains = gain_law.gains_q15[event_indices].astype(np.int64)
    return np.floor_divide(
        unity.astype(np.int64) * gains + 16384,
        32768,
    )


def _fit_cached_atom(
    objective_residual: np.ndarray,
    sample_rate: int,
    model: CIBS0Model,
    *,
    period_samples: int,
    gain_block_size: int,
) -> tuple[CachedPeriodicAtom, np.ndarray]:
    """Fit, project, decode, and refit one periodic cause."""

    analysis = analyze_periodic_basis(
        objective_residual,
        sample_rate,
        basis_length=model.output_length,
        period_samples=period_samples,
    )
    latent = encode_basis_latent(
        analysis.basis.reshape(1, -1),
        model,
    )
    materialized = materialize_basis(latent, model)
    basis = materialized.samples[0]
    trajectory = constant_phase_trajectory(
        int(objective_residual.size),
        analysis.phase_increment_q32,
    )
    unity = render_basis_trajectory(basis, trajectory)
    gains = fit_block_gains(
        objective_residual,
        unity,
        gain_block_size,
    )
    gain_law = _sparse_block_gain_law(
        gains,
        block_size=gain_block_size,
        sample_count=int(objective_residual.size),
    )
    prediction = _wide_scaled_prediction(unity, gain_law)
    atom = CachedPeriodicAtom(
        latent=latent,
        expected_sha256=bytes.fromhex(materialized.sha256),
        basis=basis,
        trajectory=trajectory,
        gain_law=gain_law,
    )
    return atom, prediction


def _pack_candidate(
    *,
    sample_rate: int,
    model: CIBS0Model,
    atoms: Sequence[CachedPeriodicAtom],
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int,
    lpc_orders: tuple[int, ...],
) -> tuple[bytes, dict[str, int]]:
    """Pack a complete research-level envelope and verify exact residual."""

    innovation = np.asarray(innovation_q)
    if innovation.ndim != 1 or not np.issubdtype(
        innovation.dtype,
        np.signedinteger,
    ):
        raise TypeError("cached additive Innovation must be signed")
    residual, _ = encode_lpc_liftpack_oracle(
        innovation,
        block_size=residual_block_size,
        lpc_orders=lpc_orders,
    )
    restored = decode_lpc_liftpack_oracle(
        residual,
        expected_count=int(innovation.size),
    )
    if not np.array_equal(restored, innovation.astype(np.int64)):
        raise RuntimeError("cached additive RSL2 did not round-trip")

    sections = [
        RSC1Section(
            "CONF",
            pack_conf(
                StreamConfig(
                    int(innovation.size),
                    innovation_step,
                    1,
                )
            ),
        ),
        RSC1Section("RSL2", residual),
    ]
    basis_ids: dict[bytes, int] = {}
    basis_payloads: list[bytes] = []
    for atom_id, atom in enumerate(atoms):
        declaration = CachedCIBSBasis(
            model_id=model.model_id,
            latent=atom.latent,
            channels=1,
            samples_per_channel=model.output_length,
            expected_sha256=atom.expected_sha256,
        )
        basis_payload = pack_bcib(declaration)
        basis_id = basis_ids.get(basis_payload)
        if basis_id is None:
            basis_id = len(basis_payloads)
            basis_ids[basis_payload] = basis_id
            basis_payloads.append(basis_payload)
        sections.append(
            RSC1Section(
                "ATOM",
                pack_periodic_atom(
                    PeriodicAtom(
                        basis_id,
                        atom.trajectory,
                        atom.gain_law,
                    )
                ),
                instance_id=atom_id,
                start_tick=0,
            )
        )
    sections.extend(
        RSC1Section(
            "BCIB",
            payload,
            instance_id=basis_id,
            start_tick=0,
        )
        for basis_id, payload in enumerate(basis_payloads)
    )
    payload = pack_rsc1(
        sections,
        profile=0,
        level=1,
        timebase_hz=sample_rate,
    )
    section_bytes: dict[str, int] = {}
    for section in parse_rsc1(payload).sections:
        name = bytes(section.type_code).decode("ascii")
        section_bytes[name] = section_bytes.get(name, 0) + len(section.payload)
    section_bytes["ENVELOPE"] = len(payload) - sum(section_bytes.values())
    return payload, section_bytes


def run_cached_additive_oracle(
    samples: np.ndarray,
    sample_rate: int,
    model: CIBS0Model,
    *,
    gain_block_size: int = 4096,
    innovation_step: int = 64,
    residual_block_sizes: Sequence[int] = (4096, 16384, 32768),
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
    maximum_atoms: int = 4,
    analysis_period_candidates: int = 16,
    period_rdo_shortlist: int = 8,
) -> CachedAdditiveOracleResult:
    """Compete zero through four cached causes by complete prospective bytes."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("cached additive input must be mono int16 PCM")
    if source.size < 64 or sample_rate <= 0:
        raise ValueError("invalid cached additive input")
    model.validate()
    if model.basis_channels != 1 or not 8 <= model.output_length <= 2048:
        raise ValueError("cached additive model must synthesize one mono Basis")
    if gain_block_size <= 0:
        raise ValueError("gain block size must be positive")
    blocks = tuple(sorted({int(value) for value in residual_block_sizes}))
    if not blocks or blocks[0] < 16 or blocks[-1] > 32768:
        raise ValueError("RSL2 block candidate exceeds Main-0 bounds")
    if not 1 <= innovation_step <= (1 << 20):
        raise ValueError("Innovation step exceeds Main-0 bounds")
    if not 1 <= maximum_atoms <= 16:
        raise ValueError("maximum Atoms must be between one and sixteen")

    registry_bytes = pack_registry_model(model)
    source64 = source.astype(np.int64)
    prediction_sum = np.zeros(source.size, dtype=np.int64)
    atoms: list[CachedPeriodicAtom] = []
    candidates: list[tuple[bytes, np.ndarray, dict]] = []

    def evaluate(
        proposed_atoms: Sequence[CachedPeriodicAtom],
        proposed_prediction: np.ndarray,
        *,
        added_period: int | None,
        residual_energy: int,
        shortlist_size: int,
    ) -> tuple[bytes, np.ndarray, dict]:
        innovation_q = _quantize_signed(
            source64 - proposed_prediction,
            innovation_step,
        )
        packed: list[tuple[bytes, dict[str, int], int]] = []
        for block_size in blocks:
            payload, section_bytes = _pack_candidate(
                sample_rate=sample_rate,
                model=model,
                atoms=proposed_atoms,
                innovation_q=innovation_q,
                innovation_step=innovation_step,
                residual_block_size=block_size,
                lpc_orders=lpc_orders,
            )
            packed.append((payload, section_bytes, block_size))
        payload, section_bytes, block_size = min(
            packed,
            key=lambda item: (len(item[0]), item[2]),
        )
        reconstruction = np.clip(
            proposed_prediction
            + innovation_q.astype(np.int64) * innovation_step,
            -32768,
            32767,
        ).astype(np.int16)
        reconstruction.flags.writeable = False
        basis_count = sum(
            bytes(section.type_code) == b"BCIB"
            for section in parse_rsc1(payload).sections
        )
        report = {
            "atom_count": len(proposed_atoms),
            "basis_count": basis_count,
            "stream_bytes": len(payload),
            "stream_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_block_size": block_size,
            "added_atom_period_samples": added_period,
            "analysis_residual_energy": residual_energy,
            "period_shortlist_size": shortlist_size,
            "section_bytes": section_bytes,
            **_quality_report(source, reconstruction),
        }
        return payload, reconstruction, report

    zero = evaluate(
        (),
        prediction_sum,
        added_period=None,
        residual_energy=int(source64 @ source64),
        shortlist_size=0,
    )
    candidates.append(zero)

    for _atom_index in range(maximum_atoms):
        objective_residual = np.clip(
            source64 - prediction_sum,
            -32768,
            32767,
        ).astype(np.int16)
        periods = _period_candidates(
            objective_residual,
            sample_rate,
            maximum_candidates=analysis_period_candidates,
        )
        fitted: list[
            tuple[int, int, CachedPeriodicAtom, np.ndarray]
        ] = []
        for period_samples in periods:
            try:
                atom, atom_prediction = _fit_cached_atom(
                    objective_residual,
                    sample_rate,
                    model,
                    period_samples=period_samples,
                    gain_block_size=gain_block_size,
                )
            except (TypeError, ValueError, np.linalg.LinAlgError):
                continue
            remaining = (
                source64
                - prediction_sum
                - atom_prediction
            )
            fitted.append(
                (
                    int(remaining @ remaining),
                    period_samples,
                    atom,
                    atom_prediction,
                )
            )
        if not fitted:
            break
        shortlist = sorted(
            fitted,
            key=lambda item: (item[0], item[1]),
        )[:period_rdo_shortlist]
        step_candidates: list[
            tuple[bytes, np.ndarray, dict, CachedPeriodicAtom, np.ndarray]
        ] = []
        for residual_energy, period, atom, atom_prediction in shortlist:
            proposed_prediction = prediction_sum + atom_prediction
            payload, reconstruction, report = evaluate(
                (*atoms, atom),
                proposed_prediction,
                added_period=period,
                residual_energy=residual_energy,
                shortlist_size=len(shortlist),
            )
            step_candidates.append(
                (
                    payload,
                    reconstruction,
                    report,
                    atom,
                    atom_prediction,
                )
            )
        selected = min(
            step_candidates,
            key=lambda item: (
                item[2]["stream_bytes"],
                item[2]["added_atom_period_samples"],
            ),
        )
        atoms.append(selected[3])
        prediction_sum += selected[4]
        candidates.append(selected[:3])

    selected_payload, selected_reconstruction, selected_report = min(
        candidates,
        key=lambda item: (
            item[2]["stream_bytes"],
            item[2]["atom_count"],
        ),
    )
    zero_bytes = candidates[0][2]["stream_bytes"]
    amortized = {
        str(stream_count): selected_report["stream_bytes"]
        + (len(registry_bytes) + stream_count - 1) // stream_count
        for stream_count in (1, 10, 100, 1000)
    }
    report = {
        **selected_report,
        "status": "research oracle; overlap remains non-normative",
        "format_profile": "prospective-cached-additive-RSC1-level-1",
        "rdo_objective": (
            "minimum complete stream bytes against zero-Atom RSL2"
        ),
        "zero_atom_bytes": zero_bytes,
        "selected_reduction_vs_zero_atom": (
            1.0 - selected_report["stream_bytes"] / zero_bytes
        ),
        "candidate_count": len(candidates),
        "candidates": [candidate[2] for candidate in candidates],
        "registry_model_bytes": len(registry_bytes),
        "registry_model_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "selected_plus_amortized_registry_bytes": amortized,
    }
    return CachedAdditiveOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
