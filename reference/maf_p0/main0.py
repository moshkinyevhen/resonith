"""Executable mono Main-0 RSC1 stream packer and reference decoder."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .basis_section import pack_braw, unpack_braw
from .composition import GainEventLaw, compose_truth
from .periodic import PhaseTrajectory, render_basis_trajectory
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


REQUIRED_TYPES = frozenset({b"ATOM", b"BRAW", b"CONF", b"RSL1"})


@dataclass(frozen=True)
class Main0DecodeResult:
    """Verified mono PCM and its RSC1 sample timebase."""

    samples: np.ndarray
    sample_rate: int


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

    basis_vector = np.asarray(basis)
    innovation = np.asarray(innovation_q)
    if basis_vector.dtype != np.int16 or basis_vector.ndim != 1:
        raise TypeError("Main-0 periodic Basis must be a mono int16 vector")
    if (
        innovation.ndim != 1
        or not np.issubdtype(innovation.dtype, np.signedinteger)
    ):
        raise TypeError("Main-0 Innovation must be a signed integer vector")
    config = StreamConfig(
        sample_count=trajectory.sample_count,
        innovation_step=innovation_step,
        output_channels=1,
    )
    if gain_law.sample_count != config.sample_count:
        raise ValueError("Main-0 gain lifetime differs from the stream")
    if innovation.size != config.sample_count:
        raise ValueError("Main-0 Innovation length differs from the stream")
    atom = PeriodicAtom(0, trajectory, gain_law)
    sections = [
        RSC1Section("ATOM", pack_periodic_atom(atom)),
        RSC1Section("BRAW", pack_braw(basis_vector.reshape(1, -1))),
        RSC1Section("CONF", pack_conf(config)),
        RSC1Section(
            "RSL1",
            encode_liftpack(
                innovation,
                block_size=residual_block_size,
            ).payload,
        ),
    ]
    return pack_rsc1(sections, profile=0, level=0, timebase_hz=sample_rate)


def decode_main0_raw_stream(payload: bytes) -> Main0DecodeResult:
    """Verify and decode the first executable mono Main-0 RSC1 subset."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 0):
        raise ValueError("unsupported Resonith profile or level")

    required: dict[bytes, RSC1Section] = {}
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code not in REQUIRED_TYPES:
            if section.flags & SECTION_CRITICAL:
                raise ValueError("unknown critical Main-0 section")
            continue
        if section.instance_id != 0:
            raise ValueError("unsupported Main-0 section instance")
        if section.schema_version != 1:
            raise ValueError("unsupported Main-0 section schema")
        if section.start_tick != 0:
            raise ValueError("the executable Main-0 subset starts at tick zero")
        required[type_code] = section
    if required.keys() != REQUIRED_TYPES:
        missing = sorted(REQUIRED_TYPES - required.keys())
        raise ValueError(f"missing required Main-0 section: {missing!r}")

    config = unpack_conf(required[b"CONF"].payload)
    if config.output_channels != 1:
        raise ValueError("the executable Main-0 subset is mono")
    basis = unpack_braw(required[b"BRAW"].payload)
    if basis.shape[0] != 1:
        raise ValueError("periodic Main-0 BRAW must contain one channel")
    atom = unpack_periodic_atom(required[b"ATOM"].payload)
    if atom.basis_instance_id != required[b"BRAW"].instance_id:
        raise ValueError("ATOM references an unavailable Basis instance")
    if atom.trajectory.sample_count != config.sample_count:
        raise ValueError("ATOM lifetime differs from CONF")
    innovation = decode_liftpack(
        required[b"RSL1"].payload,
        expected_count=config.sample_count,
    ).astype(np.int64, copy=False)
    unity = render_basis_trajectory(basis[0], atom.trajectory)
    output = compose_truth(
        unity,
        atom.gain_law,
        innovation_q=innovation,
        innovation_step=config.innovation_step,
    )
    output.flags.writeable = False
    return Main0DecodeResult(output, info.timebase_hz)
