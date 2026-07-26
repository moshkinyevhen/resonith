"""Typed Main-0 configuration and periodic-Atom section payloads."""

from __future__ import annotations

from dataclasses import dataclass
import struct

import numpy as np

from .composition import GainEventLaw, MAX_INNOVATION_STEP
from .periodic import PhaseTrajectory


CONFIG = struct.Struct("<IIHHI")
BCIB_HEADER = struct.Struct("<BBHHHII32s")
ATOM_HEADER = struct.Struct("<IIIIII")
PHASE_KNOT = struct.Struct("<II")
GAIN_EVENT = struct.Struct("<Ii")
MAX_CHANNELS = 8
MAX_ATOM_RECORDS = 1_000_000
MAX_CIBS_LATENT_ELEMENTS = 128
MAX_BASIS_ELEMENTS = 16_384


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
class CachedCIBSBasis:
    """One latent-only BCIB schema-1 immutable Basis declaration."""

    model_id: str
    latent: np.ndarray
    channels: int
    samples_per_channel: int
    expected_sha256: bytes

    def __post_init__(self) -> None:
        model_id_bytes = self.model_id.encode("utf-8")
        if not 1 <= len(model_id_bytes) <= 255:
            raise ValueError("BCIB model ID must occupy 1 through 255 bytes")
        latent = np.asarray(self.latent)
        if latent.dtype != np.int8 or latent.ndim != 1:
            raise TypeError("BCIB latent must be one int8 vector")
        if not 1 <= latent.size <= MAX_CIBS_LATENT_ELEMENTS:
            raise ValueError("BCIB latent exceeds the Main-0 bound")
        if (
            not 1 <= self.channels <= MAX_CHANNELS
            or self.samples_per_channel < 2
            or self.samples_per_channel > 2048
            or self.channels * self.samples_per_channel > MAX_BASIS_ELEMENTS
        ):
            raise ValueError("BCIB Basis shape exceeds the Main-0 bound")
        if not isinstance(self.expected_sha256, bytes):
            raise TypeError("BCIB expected hash must be raw bytes")
        if len(self.expected_sha256) != 32:
            raise ValueError("BCIB expected hash must contain 32 bytes")
        latent = latent.copy()
        latent.flags.writeable = False
        object.__setattr__(self, "latent", latent)


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


def pack_bcib(basis: CachedCIBSBasis) -> bytes:
    """Serialize one latent-only cached CIBS Basis."""

    model_id = basis.model_id.encode("utf-8")
    return (
        BCIB_HEADER.pack(
            len(model_id),
            0,
            int(basis.latent.size),
            basis.channels,
            0,
            basis.samples_per_channel,
            0,
            basis.expected_sha256,
        )
        + model_id
        + basis.latent.tobytes()
    )


def unpack_bcib(payload: bytes) -> CachedCIBSBasis:
    """Validate BCIB schema 1 without resolving the external model registry."""

    if len(payload) < BCIB_HEADER.size:
        raise ValueError("truncated BCIB schema-1 header")
    (
        model_id_bytes,
        flags,
        latent_elements,
        channels,
        reserved,
        samples_per_channel,
        reserved2,
        expected_sha256,
    ) = BCIB_HEADER.unpack_from(payload)
    if flags != 0:
        raise ValueError("unsupported BCIB feature")
    if reserved != 0 or reserved2 != 0:
        raise ValueError("non-zero BCIB reserved field")
    expected_size = BCIB_HEADER.size + model_id_bytes + latent_elements
    if len(payload) != expected_size:
        raise ValueError("BCIB schema-1 payload size mismatch")
    model_start = BCIB_HEADER.size
    try:
        model_id = payload[
            model_start:model_start + model_id_bytes
        ].decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("BCIB model ID is not canonical UTF-8") from error
    latent = np.frombuffer(
        payload,
        dtype=np.int8,
        count=latent_elements,
        offset=model_start + model_id_bytes,
    ).copy()
    return CachedCIBSBasis(
        model_id=model_id,
        latent=latent,
        channels=channels,
        samples_per_channel=samples_per_channel,
        expected_sha256=expected_sha256,
    )


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
