"""Typed Main-0 configuration and periodic-Atom section payloads."""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np

from .composition import GainEventLaw, MAX_INNOVATION_STEP
from .periodic import PhaseTrajectory


CONFIG = struct.Struct("<IIHHI")
ATOM_HEADER = struct.Struct("<IIIIII")
PHASE_KNOT = struct.Struct("<II")
GAIN_EVENT = struct.Struct("<Ii")
MAX_CHANNELS = 8
MAX_ATOM_RECORDS = 1_000_000


@dataclass(frozen=True)
class StreamConfig:
    """Fixed stream-wide limits needed before decoder workspace allocation."""

    sample_count: int
    innovation_step: int
    output_channels: int = 1

    def __post_init__(self) -> None:
        if not 1 <= self.sample_count <= 0x7FFF_FFFF:
            raise ValueError("CONF sample count exceeds the Main-0 bound")
        if not 1 <= self.innovation_step <= MAX_INNOVATION_STEP:
            raise ValueError("CONF Innovation step exceeds the Main-0 bound")
        if not 1 <= self.output_channels <= MAX_CHANNELS:
            raise ValueError("CONF output channel count exceeds the Main-0 bound")


@dataclass(frozen=True)
class PeriodicAtom:
    """One immutable-Basis periodic Atom with absolute control laws."""

    basis_instance_id: int
    trajectory: PhaseTrajectory
    gain_law: GainEventLaw

    def __post_init__(self) -> None:
        if not 0 <= self.basis_instance_id <= 0xFFFF_FFFF:
            raise ValueError("ATOM Basis instance ID exceeds uint32")
        if self.trajectory.sample_count != self.gain_law.sample_count:
            raise ValueError("ATOM phase and gain lifetimes differ")
        if self.trajectory.positions.size > MAX_ATOM_RECORDS:
            raise ValueError("ATOM phase-knot count exceeds the Main-0 bound")
        if self.gain_law.positions.size > MAX_ATOM_RECORDS:
            raise ValueError("ATOM gain-event count exceeds the Main-0 bound")


def pack_conf(config: StreamConfig) -> bytes:
    """Serialize canonical fixed-size `CONF` schema 1."""

    return CONFIG.pack(
        config.sample_count,
        config.innovation_step,
        config.output_channels,
        0,
        0,
    )


def unpack_conf(payload: bytes) -> StreamConfig:
    if len(payload) != CONFIG.size:
        raise ValueError("CONF schema 1 must contain exactly 16 bytes")
    sample_count, innovation_step, output_channels, flags, reserved = (
        CONFIG.unpack(payload)
    )
    if flags != 0 or reserved != 0:
        raise ValueError("unsupported CONF feature")
    return StreamConfig(sample_count, innovation_step, output_channels)


def pack_periodic_atom(atom: PeriodicAtom) -> bytes:
    """Serialize canonical `ATOM` schema 1 in timeline order."""

    trajectory = atom.trajectory
    gain_law = atom.gain_law
    output = bytearray(
        ATOM_HEADER.pack(
            atom.basis_instance_id,
            trajectory.sample_count,
            int(trajectory.phase_origin_q32),
            int(trajectory.positions.size),
            int(gain_law.positions.size),
            0,
        )
    )
    for position, increment in zip(
        trajectory.positions,
        trajectory.increments_q32,
        strict=True,
    ):
        output += PHASE_KNOT.pack(int(position), int(increment))
    for position, gain in zip(
        gain_law.positions,
        gain_law.gains_q15,
        strict=True,
    ):
        output += GAIN_EVENT.pack(int(position), int(gain))
    return bytes(output)


def unpack_periodic_atom(payload: bytes) -> PeriodicAtom:
    if len(payload) < ATOM_HEADER.size:
        raise ValueError("truncated ATOM schema-1 header")
    (
        basis_instance_id,
        duration_samples,
        phase_origin_q32,
        knot_count,
        gain_event_count,
        flags,
    ) = ATOM_HEADER.unpack_from(payload)
    if flags != 0:
        raise ValueError("unsupported ATOM feature")
    if not 2 <= knot_count <= MAX_ATOM_RECORDS:
        raise ValueError("ATOM phase-knot count exceeds the Main-0 bound")
    if not 1 <= gain_event_count <= MAX_ATOM_RECORDS:
        raise ValueError("ATOM gain-event count exceeds the Main-0 bound")
    expected_size = (
        ATOM_HEADER.size
        + knot_count * PHASE_KNOT.size
        + gain_event_count * GAIN_EVENT.size
    )
    if len(payload) != expected_size:
        raise ValueError("ATOM schema-1 payload size mismatch")

    phase_offset = ATOM_HEADER.size
    phase_records = [
        PHASE_KNOT.unpack_from(payload, phase_offset + index * PHASE_KNOT.size)
        for index in range(knot_count)
    ]
    gain_offset = phase_offset + knot_count * PHASE_KNOT.size
    gain_records = [
        GAIN_EVENT.unpack_from(payload, gain_offset + index * GAIN_EVENT.size)
        for index in range(gain_event_count)
    ]
    trajectory = PhaseTrajectory(
        np.asarray([record[0] for record in phase_records], dtype=np.int64),
        np.asarray([record[1] for record in phase_records], dtype=np.uint32),
        phase_origin_q32,
    )
    if trajectory.sample_count != duration_samples:
        raise ValueError("ATOM duration differs from its phase endpoint")
    gain_law = GainEventLaw(
        np.asarray([record[0] for record in gain_records], dtype=np.uint32),
        np.asarray([record[1] for record in gain_records], dtype=np.int32),
        duration_samples,
    )
    return PeriodicAtom(basis_instance_id, trajectory, gain_law)
