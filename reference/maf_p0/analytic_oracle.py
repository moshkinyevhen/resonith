"""Full-byte R-039 oracle for a batched analytic oscillator bank."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct

import numpy as np

from .codec import _quality_report, _quantize_signed
from .composition import GainEventLaw, compose_truth
from .main0 import _sparse_block_gain_law
from .periodic import (
    PHASE_SCALE,
    PhaseTrajectory,
    constant_phase_trajectory,
    fit_block_gains,
    render_basis_trajectory,
)
from .residual import decode_liftpack, encode_liftpack
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import StreamConfig, pack_conf


SINE_ROM_LENGTH = 1024
SINE_ROM_SHA256 = (
    "c0074ac685d02073a0c5bd8072657e3e2d4e3bd991288dd52ac6e02de941e729"
)
HARMONIC_BANK_HEADER = struct.Struct("<HHII")
HARMONIC_ATOM = struct.Struct("<III")
GAIN_EVENT = struct.Struct("<Ii")


def _make_sine_rom() -> np.ndarray:
    """Materialize and verify the research ROM used by integer rendering."""

    positions = np.arange(SINE_ROM_LENGTH, dtype=np.float64)
    table = np.rint(
        32767.0 * np.sin(2.0 * np.pi * positions / SINE_ROM_LENGTH)
    ).astype(np.int16)
    digest = hashlib.sha256(
        table.astype("<i2", copy=False).tobytes()
    ).hexdigest()
    if digest != SINE_ROM_SHA256:
        raise RuntimeError("analytic oscillator ROM differs from R-039")
    table.flags.writeable = False
    return table


SINE_ROM = _make_sine_rom()


@dataclass(frozen=True)
class AnalyticAtom:
    """One full-lifetime oscillator with absolute phase and sparse gain."""

    trajectory: PhaseTrajectory
    gain_law: GainEventLaw

    def __post_init__(self) -> None:
        if self.trajectory.sample_count != self.gain_law.sample_count:
            raise ValueError("analytic phase and gain lifetimes differ")
        increments = self.trajectory.increments_q32
        if np.any(increments != increments[0]):
            raise ValueError("R-039 accepts only constant-frequency Atoms")


@dataclass(frozen=True)
class AnalyticOracleResult:
    """Prospective stream selected by complete-byte analytic RDO."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _spectral_increments(
    samples: np.ndarray,
    sample_rate: int,
    *,
    maximum_candidates: int,
    minimum_frequency: float,
    maximum_frequency: float,
) -> tuple[int, ...]:
    """Propose Q32 increments from deterministic local spectral peaks."""

    count = min(samples.size, 32768)
    signal = samples[:count].astype(np.float64)
    signal -= signal.mean()
    if float(np.max(np.abs(signal))) < 1.0:
        return (1,)
    signal *= np.hanning(count)
    spectrum = np.fft.rfft(signal)
    magnitude = np.abs(spectrum)
    minimum_bin = max(1, int(math.ceil(minimum_frequency * count / sample_rate)))
    maximum_bin = min(
        magnitude.size - 2,
        int(math.floor(maximum_frequency * count / sample_rate)),
    )
    if minimum_bin > maximum_bin:
        raise ValueError("invalid analytic frequency range")

    region = magnitude[minimum_bin : maximum_bin + 1]
    local = np.ones(region.size, dtype=np.bool_)
    if region.size > 2:
        local[1:-1] = (
            (region[1:-1] >= region[:-2])
            & (region[1:-1] >= region[2:])
        )
    local_indices = np.flatnonzero(local)
    ranked = local_indices[
        np.argsort(-region[local_indices], kind="stable")
    ][:maximum_candidates]

    increments: list[int] = []
    for local_index in ranked:
        index = minimum_bin + int(local_index)
        left = float(magnitude[index - 1])
        center = float(magnitude[index])
        right = float(magnitude[index + 1])
        denominator = left - 2.0 * center + right
        offset = (
            0.5 * (left - right) / denominator
            if denominator != 0.0
            else 0.0
        )
        offset = float(np.clip(offset, -0.5, 0.5))
        increment = int(round(PHASE_SCALE * (index + offset) / count))
        increments.append(max(1, min(0xFFFF_FFFF, increment)))
    return tuple(dict.fromkeys(increments)) or (1,)


def _fit_analytic_atom(
    objective_residual: np.ndarray,
    phase_increment_q32: int,
    *,
    gain_block_size: int,
) -> tuple[AnalyticAtom, np.ndarray]:
    """Estimate global phase, then fit sparse integer amplitude events."""

    sample_count = int(objective_residual.size)
    zero_phase = constant_phase_trajectory(
        sample_count,
        phase_increment_q32,
    )
    quarter_phase = constant_phase_trajectory(
        sample_count,
        phase_increment_q32,
        phase_origin_q32=PHASE_SCALE // 4,
    )
    sine = render_basis_trajectory(SINE_ROM, zero_phase).astype(np.float64)
    cosine = render_basis_trajectory(SINE_ROM, quarter_phase).astype(np.float64)
    target = objective_residual.astype(np.float64)
    sine_denominator = float(sine @ sine)
    cosine_denominator = float(cosine @ cosine)
    sine_weight = float(target @ sine) / max(sine_denominator, 1.0)
    cosine_weight = float(target @ cosine) / max(cosine_denominator, 1.0)
    phase = math.atan2(cosine_weight, sine_weight)
    phase_origin_q32 = int(
        round(PHASE_SCALE * phase / (2.0 * math.pi))
    ) & 0xFFFF_FFFF

    trajectory = constant_phase_trajectory(
        sample_count,
        phase_increment_q32,
        phase_origin_q32=phase_origin_q32,
    )
    unity = render_basis_trajectory(SINE_ROM, trajectory)
    gains = fit_block_gains(
        objective_residual,
        unity,
        gain_block_size,
    )
    gain_law = _sparse_block_gain_law(
        gains,
        block_size=gain_block_size,
        sample_count=sample_count,
    )
    atom = AnalyticAtom(trajectory, gain_law)
    return atom, compose_truth(unity, gain_law)


def _pack_harmonic_bank(atoms: tuple[AnalyticAtom, ...]) -> bytes:
    sample_count = atoms[0].trajectory.sample_count if atoms else 0
    output = bytearray(
        HARMONIC_BANK_HEADER.pack(1, 0, len(atoms), sample_count)
    )
    for atom in atoms:
        output += HARMONIC_ATOM.pack(
            int(atom.trajectory.increments_q32[0]),
            int(atom.trajectory.phase_origin_q32),
            int(atom.gain_law.positions.size),
        )
        for position, gain in zip(
            atom.gain_law.positions,
            atom.gain_law.gains_q15,
            strict=True,
        ):
            output += GAIN_EVENT.pack(int(position), int(gain))
    return bytes(output)


def _pack_prospective_analytic_stream(
    *,
    sample_rate: int,
    sample_count: int,
    atoms: tuple[AnalyticAtom, ...],
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int,
) -> tuple[bytes, dict[str, int]]:
    """Pack one research-only level-2 envelope with a batched Atom bank."""

    if any(atom.trajectory.sample_count != sample_count for atom in atoms):
        raise ValueError("analytic Atom lifetime differs from the stream")
    residual = encode_liftpack(
        innovation_q,
        block_size=residual_block_size,
    )
    restored = decode_liftpack(
        residual.payload,
        expected_count=sample_count,
    )
    if not np.array_equal(restored, innovation_q.astype(np.int64)):
        raise RuntimeError("analytic Innovation did not round-trip")
    payload = pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(sample_count, innovation_step, 1)),
            ),
            RSC1Section("HBNK", _pack_harmonic_bank(atoms)),
            RSC1Section("RSL1", residual.payload),
        ],
        profile=0,
        level=2,
        timebase_hz=sample_rate,
    )
    parsed = parse_rsc1(payload)
    section_bytes = {
        bytes(section.type_code).decode("ascii"): len(section.payload)
        for section in parsed.sections
    }
    section_bytes["ENVELOPE"] = len(payload) - sum(section_bytes.values())
    return payload, section_bytes


def run_analytic_oscillator_oracle(
    samples: np.ndarray,
    sample_rate: int,
    *,
    gain_block_size: int = 4096,
    innovation_step: int = 64,
    residual_block_size: int = 1024,
    maximum_atoms: int = 8,
    spectral_candidates: int = 24,
    rdo_shortlist: int = 8,
    minimum_frequency: float = 50.0,
    maximum_frequency: float = 8000.0,
) -> AnalyticOracleResult:
    """RDO zero or more batched oscillators against one final Innovation."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("analytic oracle input must be mono int16 PCM")
    if source.size < 64 or sample_rate <= 0:
        raise ValueError("invalid analytic oracle input")
    if gain_block_size <= 0 or residual_block_size <= 0:
        raise ValueError("block sizes must be positive")
    if not 1 <= innovation_step <= (1 << 20):
        raise ValueError("Innovation step exceeds the profile bound")
    if not 0 <= maximum_atoms <= 64:
        raise ValueError("maximum_atoms must be between zero and sixty-four")
    if spectral_candidates <= 0 or rdo_shortlist <= 0:
        raise ValueError("candidate bounds must be positive")

    source64 = source.astype(np.int64)
    prediction_sum = np.zeros(source.size, dtype=np.int64)
    atoms: list[AnalyticAtom] = []
    candidates: list[
        tuple[bytes, np.ndarray, dict]
    ] = []

    zero_innovation = _quantize_signed(source64, innovation_step)
    zero_payload, zero_sections = _pack_prospective_analytic_stream(
        sample_rate=sample_rate,
        sample_count=int(source.size),
        atoms=(),
        innovation_q=zero_innovation,
        innovation_step=innovation_step,
        residual_block_size=residual_block_size,
    )
    zero_reconstruction = np.clip(
        zero_innovation.astype(np.int64) * innovation_step,
        -32768,
        32767,
    ).astype(np.int16)
    zero_report = {
        "atom_count": 0,
        "stream_bytes": len(zero_payload),
        "stream_sha256": hashlib.sha256(zero_payload).hexdigest(),
        "section_bytes": zero_sections,
        **_quality_report(source, zero_reconstruction),
    }
    zero_reconstruction.flags.writeable = False
    candidates.append((zero_payload, zero_reconstruction, zero_report))

    for atom_index in range(maximum_atoms):
        objective_residual = np.clip(
            source64 - prediction_sum,
            -32768,
            32767,
        ).astype(np.int16)
        increments = _spectral_increments(
            objective_residual,
            sample_rate,
            maximum_candidates=spectral_candidates,
            minimum_frequency=minimum_frequency,
            maximum_frequency=maximum_frequency,
        )
        fitted: list[tuple[int, int, AnalyticAtom, np.ndarray]] = []
        for increment in increments:
            atom, atom_prediction = _fit_analytic_atom(
                objective_residual,
                increment,
                gain_block_size=gain_block_size,
            )
            remaining = (
                source64
                - prediction_sum
                - atom_prediction.astype(np.int64)
            )
            fitted.append(
                (
                    int(remaining @ remaining),
                    increment,
                    atom,
                    atom_prediction,
                )
            )
        shortlist = sorted(
            fitted,
            key=lambda item: (item[0], item[1]),
        )[:rdo_shortlist]

        step: list[
            tuple[bytes, np.ndarray, dict, AnalyticAtom, np.ndarray]
        ] = []
        for residual_energy, increment, atom, atom_prediction in shortlist:
            proposed_sum = (
                prediction_sum + atom_prediction.astype(np.int64)
            )
            innovation_q = _quantize_signed(
                source64 - proposed_sum,
                innovation_step,
            )
            payload, section_bytes = _pack_prospective_analytic_stream(
                sample_rate=sample_rate,
                sample_count=int(source.size),
                atoms=tuple((*atoms, atom)),
                innovation_q=innovation_q,
                innovation_step=innovation_step,
                residual_block_size=residual_block_size,
            )
            reconstruction = np.clip(
                proposed_sum
                + innovation_q.astype(np.int64) * innovation_step,
                -32768,
                32767,
            ).astype(np.int16)
            report = {
                "atom_count": atom_index + 1,
                "stream_bytes": len(payload),
                "stream_sha256": hashlib.sha256(payload).hexdigest(),
                "added_increment_q32": increment,
                "added_frequency_hz": (
                    increment * sample_rate / PHASE_SCALE
                ),
                "added_gain_events": int(atom.gain_law.positions.size),
                "analysis_residual_energy": residual_energy,
                "section_bytes": section_bytes,
                **_quality_report(source, reconstruction),
            }
            step.append((payload, reconstruction, report, atom, atom_prediction))
        (
            payload,
            reconstruction,
            report,
            selected_atom,
            selected_prediction,
        ) = min(
            step,
            key=lambda item: (
                item[2]["stream_bytes"],
                item[2]["added_increment_q32"],
            ),
        )
        atoms.append(selected_atom)
        prediction_sum += selected_prediction.astype(np.int64)
        reconstruction.flags.writeable = False
        candidates.append((payload, reconstruction, report))

    selected_payload, selected_reconstruction, selected_report = min(
        candidates,
        key=lambda item: (
            item[2]["stream_bytes"],
            item[2]["atom_count"],
        ),
    )
    report = {
        **selected_report,
        "status": "research oracle; not a decodable Main-0 profile",
        "format_profile": "prospective-analytic-RSC1-level-2",
        "sine_rom_sha256": SINE_ROM_SHA256,
        "rdo_objective": (
            "minimum complete prospective stream bytes at one Innovation step"
        ),
        "zero_atom_bytes": len(zero_payload),
        "selected_reduction_vs_zero_atom": (
            1.0 - selected_report["stream_bytes"] / len(zero_payload)
        ),
        "candidate_count": len(candidates),
        "candidates": [candidate[2] for candidate in candidates],
    }
    return AnalyticOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
