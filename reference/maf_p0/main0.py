"""Executable mono Main-0 RSC1 stream packer and reference decoder."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import TYPE_CHECKING, Sequence

import numpy as np

from .basis_section import pack_braw, unpack_braw
from .codec import _quality_report, _quantize_signed
from .composition import GainEventLaw, compose_truth
from .periodic import (
    PhaseTrajectory,
    analyze_periodic_basis,
    constant_phase_trajectory,
    estimate_phase_trajectory,
    fit_block_gains,
    render_basis_trajectory,
)
from .residual import decode_liftpack, encode_liftpack
from .rsc1 import RSC1Section, SECTION_CRITICAL, pack_rsc1, parse_rsc1
from .stream_sections import (
    PeriodicAtom,
    StreamConfig,
    pack_conf,
    pack_periodic_atom,
    unpack_conf,
    unpack_periodic_atom,
)

if TYPE_CHECKING:
    from .native_core import NativeMain0Decoder


REQUIRED_TYPES = frozenset({b"ATOM", b"BRAW", b"CONF", b"RSL1"})


@dataclass(frozen=True)
class Main0DecodeResult:
    """Verified mono PCM and its RSC1 sample timebase."""

    samples: np.ndarray
    sample_rate: int


@dataclass(frozen=True)
class Main0EncodeResult:
    """One native-decoder-verified typed stream and its RDO evidence."""

    payload: bytes
    reconstructed: np.ndarray
    report: dict


@dataclass(frozen=True)
class Main0State:
    """One state-local periodic Atom and its immutable raw Basis."""

    basis: np.ndarray
    trajectory: PhaseTrajectory
    gain_law: GainEventLaw


def pack_main0_raw_stream(
    *,
    sample_rate: int,
    basis: np.ndarray,
    trajectory: PhaseTrajectory,
    gain_law: GainEventLaw,
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int = 1024,
) -> bytes:
    """Pack the first executable Main-0 subset using one raw periodic Basis."""

    return pack_main0_state_stream(
        sample_rate=sample_rate,
        states=(Main0State(basis, trajectory, gain_law),),
        innovation_q=innovation_q,
        innovation_step=innovation_step,
        residual_block_size=residual_block_size,
    )


def pack_main0_state_stream(
    *,
    sample_rate: int,
    states: Sequence[Main0State],
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int = 1024,
) -> bytes:
    """Pack a canonical state partition with content-deduplicated raw Bases."""

    if not states:
        raise ValueError("Main-0 requires at least one state")
    innovation = np.asarray(innovation_q)
    if (
        innovation.ndim != 1
        or not np.issubdtype(innovation.dtype, np.signedinteger)
    ):
        raise TypeError("Main-0 Innovation must be a signed integer vector")
    sample_count = sum(state.trajectory.sample_count for state in states)
    config = StreamConfig(
        sample_count=sample_count,
        innovation_step=innovation_step,
        output_channels=1,
    )
    if innovation.size != config.sample_count:
        raise ValueError("Main-0 Innovation length differs from the stream")
    sections = [
        RSC1Section("CONF", pack_conf(config)),
        RSC1Section(
            "RSL1",
            encode_liftpack(
                innovation,
                block_size=residual_block_size,
            ).payload,
        ),
    ]
    basis_ids: dict[bytes, int] = {}
    basis_payloads: list[bytes] = []
    basis_births: list[int] = []
    cursor = 0
    for atom_id, state in enumerate(states):
        basis_vector = np.asarray(state.basis)
        if basis_vector.dtype != np.int16 or basis_vector.ndim != 1:
            raise TypeError("Main-0 periodic Basis must be a mono int16 vector")
        if state.gain_law.sample_count != state.trajectory.sample_count:
            raise ValueError("Main-0 state gain and phase lifetimes differ")
        basis_payload = pack_braw(basis_vector.reshape(1, -1))
        basis_id = basis_ids.get(basis_payload)
        if basis_id is None:
            basis_id = len(basis_payloads)
            basis_ids[basis_payload] = basis_id
            basis_payloads.append(basis_payload)
            basis_births.append(cursor)
        atom = PeriodicAtom(
            basis_id,
            state.trajectory,
            state.gain_law,
        )
        sections.append(
            RSC1Section(
                "ATOM",
                pack_periodic_atom(atom),
                instance_id=atom_id,
                start_tick=cursor,
            )
        )
        cursor += state.trajectory.sample_count
    sections.extend(
        RSC1Section(
            "BRAW",
            payload,
            instance_id=basis_id,
            start_tick=basis_births[basis_id],
        )
        for basis_id, payload in enumerate(basis_payloads)
    )
    return pack_rsc1(sections, profile=0, level=0, timebase_hz=sample_rate)


def decode_main0_raw_stream(payload: bytes) -> Main0DecodeResult:
    """Verify and decode the first executable mono Main-0 RSC1 subset."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 0):
        raise ValueError("unsupported Resonith profile or level")

    required: dict[bytes, list[RSC1Section]] = {
        type_code: [] for type_code in REQUIRED_TYPES
    }
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code not in REQUIRED_TYPES:
            if section.flags & SECTION_CRITICAL:
                raise ValueError("unknown critical Main-0 section")
            continue
        if section.schema_version != 1:
            raise ValueError("unsupported Main-0 section schema")
        required[type_code].append(section)
    missing = sorted(
        type_code
        for type_code, sections in required.items()
        if not sections
    )
    if missing:
        raise ValueError(f"missing required Main-0 section: {missing!r}")

    if (
        len(required[b"CONF"]) != 1
        or required[b"CONF"][0].instance_id != 0
        or required[b"CONF"][0].start_tick != 0
        or len(required[b"RSL1"]) != 1
        or required[b"RSL1"][0].instance_id != 0
        or required[b"RSL1"][0].start_tick != 0
    ):
        raise ValueError("non-canonical singleton Main-0 section")
    for type_code in (b"ATOM", b"BRAW"):
        if [
            section.instance_id for section in required[type_code]
        ] != list(range(len(required[type_code]))):
            raise ValueError("non-canonical Main-0 section instances")

    config = unpack_conf(required[b"CONF"][0].payload)
    if config.output_channels != 1:
        raise ValueError("the executable Main-0 subset is mono")
    bases: list[np.ndarray] = []
    for section in required[b"BRAW"]:
        basis = unpack_braw(section.payload)
        if basis.shape[0] != 1 or basis.shape[1] < 2:
            raise ValueError("periodic Main-0 BRAW must contain one Basis")
        bases.append(basis[0])
    innovation = decode_liftpack(
        required[b"RSL1"][0].payload,
        expected_count=config.sample_count,
    ).astype(np.int64, copy=False)
    output = np.empty(config.sample_count, dtype=np.int16)
    cursor = 0
    for section in required[b"ATOM"]:
        if section.start_tick != cursor:
            raise ValueError("Main-0 Atom states must exactly partition time")
        atom = unpack_periodic_atom(section.payload)
        if atom.basis_instance_id >= len(bases):
            raise ValueError("ATOM references an unavailable Basis instance")
        basis_section = required[b"BRAW"][atom.basis_instance_id]
        if basis_section.start_tick > cursor:
            raise ValueError("ATOM predates its referenced Basis")
        end = cursor + atom.trajectory.sample_count
        if end > config.sample_count:
            raise ValueError("ATOM lifetime exceeds CONF")
        unity = render_basis_trajectory(
            bases[atom.basis_instance_id],
            atom.trajectory,
        )
        output[cursor:end] = compose_truth(
            unity,
            atom.gain_law,
            innovation_q=innovation[cursor:end],
            innovation_step=config.innovation_step,
        )
        cursor = end
    if cursor != config.sample_count:
        raise ValueError("Main-0 Atom states do not cover CONF")
    output.flags.writeable = False
    return Main0DecodeResult(output, info.timebase_hz)


def _sparse_block_gain_law(
    gains_q15: np.ndarray,
    *,
    block_size: int,
    sample_count: int,
) -> GainEventLaw:
    positions = np.arange(0, sample_count, block_size, dtype=np.uint32)
    if positions.size != gains_q15.size:
        raise ValueError("gain candidate does not cover the stream")
    keep = np.ones(gains_q15.size, dtype=np.bool_)
    keep[1:] = gains_q15[1:] != gains_q15[:-1]
    return GainEventLaw(
        positions[keep],
        gains_q15[keep],
        sample_count,
    )


def encode_main0_periodic_rdo(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_decoder: "NativeMain0Decoder",
    basis_length: int = 256,
    gain_block_sizes: Sequence[int] = (512, 1024, 2048, 4096),
    innovation_step: int = 1,
    residual_block_size: int = 1024,
    phase_knot_interval: int = 4096,
) -> Main0EncodeResult:
    """RDO periodic candidates only after exact native decoder acceptance."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 1:
        raise TypeError("Main-0 RDO input must be mono int16 PCM")
    if source.size < 64:
        raise ValueError("Main-0 RDO requires at least 64 input samples")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if native_decoder is None:
        raise ValueError("Main-0 RDO requires an explicit native decoder")
    blocks = sorted({int(value) for value in gain_block_sizes})
    if not blocks or blocks[0] <= 0:
        raise ValueError("gain_block_sizes must contain positive values")

    analysis = analyze_periodic_basis(
        source,
        sample_rate,
        basis_length=basis_length,
    )
    phase_candidates: list[tuple[str, PhaseTrajectory]] = [
        (
            "constant",
            constant_phase_trajectory(
                int(source.size),
                analysis.phase_increment_q32,
            ),
        )
    ]
    try:
        estimated = estimate_phase_trajectory(
            source,
            sample_rate,
            knot_interval=phase_knot_interval,
        )
        if not (
            np.array_equal(
                estimated.positions,
                phase_candidates[0][1].positions,
            )
            and np.array_equal(
                estimated.increments_q32,
                phase_candidates[0][1].increments_q32,
            )
        ):
            phase_candidates.append(("continuous", estimated))
    except ValueError:
        pass

    candidates: list[tuple[str, bytes, np.ndarray, dict]] = []
    for phase_name, trajectory in phase_candidates:
        unity = render_basis_trajectory(analysis.basis, trajectory)
        for block_size in blocks:
            block_gains = fit_block_gains(source, unity, block_size)
            gain_law = _sparse_block_gain_law(
                block_gains,
                block_size=block_size,
                sample_count=int(source.size),
            )
            prediction = compose_truth(unity, gain_law)
            innovation_q = _quantize_signed(
                source.astype(np.int64) - prediction.astype(np.int64),
                innovation_step,
            )
            payload = pack_main0_raw_stream(
                sample_rate=sample_rate,
                basis=analysis.basis,
                trajectory=trajectory,
                gain_law=gain_law,
                innovation_q=innovation_q,
                innovation_step=innovation_step,
                residual_block_size=residual_block_size,
            )

            reference = decode_main0_raw_stream(payload)
            native = native_decoder.decode(payload)
            if (
                native.sample_rate != reference.sample_rate
                or not np.array_equal(native.samples, reference.samples)
            ):
                raise RuntimeError(
                    "native decoder disagrees with the Main-0 reference"
                )
            name = f"{phase_name}-gain-{block_size}"
            quality = _quality_report(source, reference.samples)
            candidate_report = {
                "name": name,
                "stream_bytes": len(payload),
                "phase_knots": int(trajectory.positions.size),
                "gain_events": int(gain_law.positions.size),
                **quality,
            }
            candidates.append(
                (name, payload, reference.samples, candidate_report)
            )

    selected_name, payload, reconstructed, selected_report = min(
        candidates,
        key=lambda item: (len(item[1]), item[0]),
    )
    reconstructed.flags.writeable = False
    report = {
        **selected_report,
        "format_profile": "Main-0-periodic-RSC1",
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "pcm_bytes": int(source.nbytes),
        "ratio_vs_pcm": len(payload) / source.nbytes,
        "native_decoder_gate": "verified",
        "rdo_objective": (
            "minimum complete typed stream bytes at one Innovation step"
        ),
        "selected_candidate": selected_name,
        "candidate_count": len(candidates),
        "candidates": [item[3] for item in candidates],
    }
    return Main0EncodeResult(payload, reconstructed, report)
