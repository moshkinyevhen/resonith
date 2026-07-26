"""Encoder-side full-byte oracle for simultaneous periodic Atoms.

This module deliberately does not extend the Main-0 decoder. It measures a
prospective overlapping-Atom envelope so decoder syntax is added only after a
complete-byte compression win. See decision R-038.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np

from .basis_section import pack_braw
from .codec import _quality_report, _quantize_signed
from .composition import compose_truth
from .main0 import Main0State, _sparse_block_gain_law
from .periodic import (
    analyze_periodic_basis,
    constant_phase_trajectory,
    fit_block_gains,
    render_basis_trajectory,
)
from .residual import decode_liftpack, encode_liftpack
from .rsc1 import RSC1Section, pack_rsc1, parse_rsc1
from .stream_sections import (
    PeriodicAtom,
    StreamConfig,
    pack_conf,
    pack_periodic_atom,
)


@dataclass(frozen=True)
class AdditiveOracleResult:
    """Full prospective streams and measurements for one matching-pursuit run."""

    selected_payload: bytes
    selected_reconstruction: np.ndarray
    report: dict


def _period_candidates(
    samples: np.ndarray,
    sample_rate: int,
    *,
    maximum_candidates: int,
    minimum_frequency: float = 50.0,
    maximum_frequency: float = 2000.0,
) -> tuple[int, ...]:
    """Return deterministic autocorrelation and subharmonic hypotheses."""

    count = min(samples.size, 32768)
    signal = samples[:count].astype(np.float64)
    signal -= signal.mean()
    if float(np.max(np.abs(signal))) < 1.0:
        return (2,)
    signal *= np.hanning(count)
    minimum_lag = max(2, int(sample_rate / maximum_frequency))
    maximum_lag = min(count // 2, int(sample_rate / minimum_frequency))
    if minimum_lag >= maximum_lag:
        return (minimum_lag,)

    fft_size = 1 << ((2 * count - 1).bit_length())
    spectrum = np.fft.rfft(signal, fft_size)
    correlation = np.fft.irfft(
        spectrum * np.conj(spectrum),
        fft_size,
    )[:count]
    energy = np.cumsum(signal * signal)
    lags = np.arange(minimum_lag, maximum_lag + 1)
    left_energy = energy[count - lags - 1]
    right_energy = energy[-1] - np.concatenate(
        ([0.0], energy[lags[:-1] - 1])
    )
    score = correlation[lags] / np.sqrt(
        np.maximum(left_energy * right_energy, 1.0)
    )

    local_peak = np.ones(score.size, dtype=np.bool_)
    if score.size > 2:
        local_peak[1:-1] = (
            (score[1:-1] >= score[:-2])
            & (score[1:-1] >= score[2:])
        )
    peak_indices = np.flatnonzero(local_peak)
    ranked = peak_indices[
        np.argsort(-score[peak_indices], kind="stable")
    ][:maximum_candidates]

    # Autocorrelation often prefers an integer multiple of the fundamental.
    # A bounded divisor expansion exposes that ambiguity to complete-byte RDO.
    expanded: list[int] = []
    for index in ranked:
        lag = int(lags[index])
        expanded.append(lag)
        for divisor in range(2, 9):
            reduced = int(round(lag / divisor))
            expanded.extend((reduced - 1, reduced, reduced + 1))
    return tuple(
        dict.fromkeys(
            lag
            for lag in expanded
            if minimum_lag <= lag <= maximum_lag
        )
    )


def _fit_periodic_atom(
    objective_residual: np.ndarray,
    sample_rate: int,
    *,
    period_samples: int,
    basis_length: int,
    gain_block_size: int,
) -> tuple[Main0State, np.ndarray]:
    """Fit one immutable Basis and sparse gain law at a proposed period."""

    analysis = analyze_periodic_basis(
        objective_residual,
        sample_rate,
        basis_length=basis_length,
        period_samples=period_samples,
    )
    trajectory = constant_phase_trajectory(
        int(objective_residual.size),
        analysis.phase_increment_q32,
    )
    unity = render_basis_trajectory(analysis.basis, trajectory)
    block_gains = fit_block_gains(
        objective_residual,
        unity,
        gain_block_size,
    )
    gain_law = _sparse_block_gain_law(
        block_gains,
        block_size=gain_block_size,
        sample_count=int(objective_residual.size),
    )
    state = Main0State(analysis.basis, trajectory, gain_law)
    return state, compose_truth(unity, gain_law)


def _pack_prospective_additive_stream(
    *,
    sample_rate: int,
    atoms: tuple[Main0State, ...],
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int,
) -> tuple[bytes, dict[str, int]]:
    """Pack overlapping Atoms without declaring their syntax normative."""

    if not atoms:
        raise ValueError("the additive envelope requires at least one Atom")
    sample_count = atoms[0].trajectory.sample_count
    if any(
        atom.trajectory.sample_count != sample_count
        or atom.gain_law.sample_count != sample_count
        for atom in atoms
    ):
        raise ValueError("additive Atoms must share one full-stream lifetime")
    innovation = np.asarray(innovation_q)
    if innovation.dtype != np.int32 or innovation.shape != (sample_count,):
        raise TypeError("additive Innovation must be one int32 stream")

    residual_packet = encode_liftpack(
        innovation,
        block_size=residual_block_size,
    )
    # The oracle verifies entropy round-trip even though no overlap decoder
    # exists. This isolates any byte gain from an invalid residual envelope.
    restored_innovation = decode_liftpack(
        residual_packet.payload,
        expected_count=sample_count,
    )
    if not np.array_equal(restored_innovation, innovation.astype(np.int64)):
        raise RuntimeError("prospective additive Innovation did not round-trip")

    sections = [
        RSC1Section(
            "CONF",
            pack_conf(StreamConfig(sample_count, innovation_step, 1)),
        ),
        RSC1Section("RSL1", residual_packet.payload),
    ]
    basis_ids: dict[bytes, int] = {}
    basis_payloads: list[bytes] = []
    for atom_id, state in enumerate(atoms):
        basis_payload = pack_braw(state.basis.reshape(1, -1))
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
                        state.trajectory,
                        state.gain_law,
                    )
                ),
                instance_id=atom_id,
                start_tick=0,
            )
        )
    sections.extend(
        RSC1Section(
            "BRAW",
            payload,
            instance_id=basis_id,
            start_tick=0,
        )
        for basis_id, payload in enumerate(basis_payloads)
    )

    # Level 1 is reserved here only as an unmistakable research marker. The
    # current native and Python Main-0 decoders intentionally reject it.
    payload = pack_rsc1(
        sections,
        profile=0,
        level=1,
        timebase_hz=sample_rate,
    )
    parsed = parse_rsc1(payload)
    section_bytes: dict[str, int] = {}
    for section in parsed.sections:
        name = bytes(section.type_code).decode("ascii")
        section_bytes[name] = section_bytes.get(name, 0) + len(section.payload)
    section_bytes["ENVELOPE"] = len(payload) - sum(section_bytes.values())
    return payload, section_bytes


def run_additive_atom_oracle(
    samples: np.ndarray,
    sample_rate: int,
    *,
    basis_length: int = 256,
    gain_block_size: int = 4096,
    innovation_step: int = 64,
    residual_block_size: int = 1024,
    maximum_atoms: int = 4,
    analysis_period_candidates: int = 16,
    period_rdo_shortlist: int = 8,
) -> AdditiveOracleResult:
    """Measure one through ``maximum_atoms`` simultaneous periodic causes.

    Each matching-pursuit step analyzes the objective residual left by the
    preceding Atoms. Candidate ranking uses complete prospective RSC1 bytes at
    one fixed Innovation step; waveform quality is reported, never optimized
    independently.
    """

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("additive oracle input must be mono int16 PCM")
    if source.size < 64 or sample_rate <= 0:
        raise ValueError("invalid additive oracle input")
    if not 8 <= basis_length <= 2048:
        raise ValueError("basis length exceeds the BRAW profile bound")
    if gain_block_size <= 0 or residual_block_size <= 0:
        raise ValueError("block sizes must be positive")
    if not 1 <= innovation_step <= (1 << 20):
        raise ValueError("Innovation step exceeds the profile bound")
    if not 1 <= maximum_atoms <= 16:
        raise ValueError("maximum_atoms must be between one and sixteen")
    if analysis_period_candidates <= 0 or period_rdo_shortlist <= 0:
        raise ValueError("period candidate bounds must be positive")

    source64 = source.astype(np.int64)
    prediction_sum = np.zeros(source.size, dtype=np.int64)
    atoms: list[Main0State] = []
    candidates: list[tuple[bytes, np.ndarray, dict]] = []

    for atom_index in range(maximum_atoms):
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
        fitted: list[tuple[int, int, Main0State, np.ndarray]] = []
        for period_samples in periods:
            try:
                state, atom_prediction = _fit_periodic_atom(
                    objective_residual,
                    sample_rate,
                    period_samples=period_samples,
                    basis_length=basis_length,
                    gain_block_size=gain_block_size,
                )
            except ValueError:
                continue
            remaining = (
                source64
                - prediction_sum
                - atom_prediction.astype(np.int64)
            )
            residual_energy = int(remaining @ remaining)
            fitted.append(
                (
                    residual_energy,
                    period_samples,
                    state,
                    atom_prediction,
                )
            )

        if not fitted:
            zero_basis = np.zeros(basis_length, dtype=np.int16)
            zero_trajectory = constant_phase_trajectory(
                int(source.size),
                1,
            )
            zero_unity = render_basis_trajectory(
                zero_basis,
                zero_trajectory,
            )
            zero_gains = fit_block_gains(
                objective_residual,
                zero_unity,
                gain_block_size,
            )
            zero_gain_law = _sparse_block_gain_law(
                zero_gains,
                block_size=gain_block_size,
                sample_count=int(source.size),
            )
            fitted.append(
                (
                    int((source64 - prediction_sum) @ (
                        source64 - prediction_sum
                    )),
                    0,
                    Main0State(
                        zero_basis,
                        zero_trajectory,
                        zero_gain_law,
                    ),
                    np.zeros(source.size, dtype=np.int16),
                )
            )

        # Residual energy is only a cheap encoder-side preselection. Every
        # surviving proposal is still ranked by a fully packed RSC1 envelope.
        shortlist = sorted(
            fitted,
            key=lambda item: (item[0], item[1]),
        )[:period_rdo_shortlist]
        step_candidates: list[
            tuple[bytes, np.ndarray, dict, Main0State, np.ndarray]
        ] = []
        for (
            residual_energy,
            period_samples,
            state,
            atom_prediction,
        ) in shortlist:
            proposed_sum = (
                prediction_sum + atom_prediction.astype(np.int64)
            )
            innovation_q = _quantize_signed(
                source64 - proposed_sum,
                innovation_step,
            )
            payload, section_bytes = _pack_prospective_additive_stream(
                sample_rate=sample_rate,
                atoms=tuple((*atoms, state)),
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
            candidate_report = {
                "atom_count": atom_index + 1,
                "basis_count": sum(
                    bytes(section.type_code) == b"BRAW"
                    for section in parse_rsc1(payload).sections
                ),
                "stream_bytes": len(payload),
                "stream_sha256": hashlib.sha256(payload).hexdigest(),
                "added_atom_period_samples": period_samples,
                "added_atom_gain_events": int(
                    state.gain_law.positions.size
                ),
                "analysis_residual_energy": residual_energy,
                "period_shortlist_size": len(shortlist),
                "section_bytes": section_bytes,
                **_quality_report(source, reconstruction),
            }
            step_candidates.append(
                (
                    payload,
                    reconstruction,
                    candidate_report,
                    state,
                    atom_prediction,
                )
            )

        (
            payload,
            reconstruction,
            candidate_report,
            selected_state,
            selected_prediction,
        ) = min(
            step_candidates,
            key=lambda item: (
                item[2]["stream_bytes"],
                item[2]["added_atom_period_samples"],
            ),
        )
        atoms.append(selected_state)
        prediction_sum += selected_prediction.astype(np.int64)
        reconstruction.flags.writeable = False
        candidates.append((payload, reconstruction, candidate_report))

    selected_payload, selected_reconstruction, selected_report = min(
        candidates,
        key=lambda item: (
            item[2]["stream_bytes"],
            item[2]["atom_count"],
        ),
    )
    one_atom_bytes = candidates[0][2]["stream_bytes"]
    report = {
        **selected_report,
        "status": "research oracle; not a decodable Main-0 profile",
        "format_profile": "prospective-additive-RSC1-level-1",
        "rdo_objective": (
            "minimum complete prospective stream bytes at one Innovation step"
        ),
        "one_atom_bytes": one_atom_bytes,
        "selected_reduction_vs_one_atom": (
            1.0 - selected_report["stream_bytes"] / one_atom_bytes
        ),
        "candidate_count": len(candidates),
        "candidates": [candidate[2] for candidate in candidates],
    }
    return AdditiveOracleResult(
        selected_payload,
        selected_reconstruction,
        report,
    )
