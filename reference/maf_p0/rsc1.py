"""Compact deterministic RSC1 section container reference."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib


MAGIC = b"RSC1"
VERSION_MAJOR = 1
VERSION_MINOR = 0
HEADER = struct.Struct("<4sBBBBIIIIII")
DIRECTORY_RECORD = struct.Struct("<4sHHIQQQQI32s")
MAX_SECTIONS = 4096
MAX_SECTION_BYTES = 512 << 20
MAX_TOTAL_BYTES = 1 << 30
MAX_TIMEBASE_HZ = 1_000_000_000
SECTION_CRITICAL = 1
KNOWN_SECTION_FLAGS = SECTION_CRITICAL


def _validated_type(type_code: bytes | str) -> bytes:
    encoded = (
        type_code.encode("ascii")
        if isinstance(type_code, str)
        else bytes(type_code)
    )
    if (
        len(encoded) != 4
        or any(
            not (ord("A") <= value <= ord("Z") or ord("0") <= value <= ord("9"))
            for value in encoded
        )
    ):
        raise ValueError("RSC1 type must be four uppercase ASCII letters/digits")
    return encoded


@dataclass(frozen=True)
class RSC1Section:
    """One typed immutable RSC1 payload and its timeline scope."""

    type_code: bytes | str
    payload: bytes
    instance_id: int = 0
    schema_version: int = 1
    flags: int = SECTION_CRITICAL
    start_tick: int = 0

    def validated(self) -> "RSC1Section":
        type_code = _validated_type(self.type_code)
        payload = bytes(self.payload)
        if not 0 <= self.instance_id <= 0xFFFF_FFFF:
            raise ValueError("RSC1 instance ID exceeds uint32")
        if not 1 <= self.schema_version <= 0xFFFF:
            raise ValueError("RSC1 schema version exceeds uint16")
        if self.flags & ~KNOWN_SECTION_FLAGS:
            raise ValueError("RSC1 section uses an unsupported flag")
        if not 0 <= self.start_tick <= 0xFFFF_FFFF_FFFF_FFFF:
            raise ValueError("RSC1 start tick exceeds uint64")
        if len(payload) > MAX_SECTION_BYTES:
            raise ValueError("RSC1 section exceeds the byte bound")
        return RSC1Section(
            type_code=type_code,
            payload=payload,
            instance_id=self.instance_id,
            schema_version=self.schema_version,
            flags=self.flags,
            start_tick=self.start_tick,
        )


@dataclass(frozen=True)
class RSC1Info:
    """Validated stream metadata returned by the reference parser."""

    profile: int
    level: int
    timebase_hz: int
    sections: tuple[RSC1Section, ...]


def pack_rsc1(
    sections: list[RSC1Section] | tuple[RSC1Section, ...],
    *,
    profile: int = 0,
    level: int = 0,
    timebase_hz: int = 48_000,
) -> bytes:
    """Build one canonical stored-section RSC1 stream."""

    if not 0 <= profile <= 0xFF or not 0 <= level <= 0xFF:
        raise ValueError("RSC1 profile and level must fit uint8")
    if not 1 <= timebase_hz <= MAX_TIMEBASE_HZ:
        raise ValueError("RSC1 timebase exceeds the profile bound")
    if len(sections) > MAX_SECTIONS:
        raise ValueError("too many RSC1 sections")

    validated = sorted(
        (section.validated() for section in sections),
        key=lambda item: (bytes(item.type_code), item.instance_id),
    )
    keys = [
        (bytes(section.type_code), section.instance_id)
        for section in validated
    ]
    if any(left == right for left, right in zip(keys, keys[1:])):
        raise ValueError("duplicate RSC1 section key")

    directory_bytes = len(validated) * DIRECTORY_RECORD.size
    payload_offset = HEADER.size + directory_bytes
    total_bytes = 0
    directory = bytearray()
    payloads: list[bytes] = []
    for section in validated:
        payload = bytes(section.payload)
        total_bytes += len(payload)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("RSC1 stream exceeds the total byte bound")
        directory += DIRECTORY_RECORD.pack(
            bytes(section.type_code),
            section.schema_version,
            section.flags,
            section.instance_id,
            section.start_tick,
            payload_offset,
            len(payload),
            len(payload),
            zlib.crc32(payload) & 0xFFFF_FFFF,
            hashlib.sha256(payload).digest(),
        )
        payload_offset += len(payload)
        payloads.append(payload)

    header = HEADER.pack(
        MAGIC,
        VERSION_MAJOR,
        VERSION_MINOR,
        profile,
        level,
        0,
        timebase_hz,
        len(validated),
        DIRECTORY_RECORD.size,
        len(directory),
        zlib.crc32(directory) & 0xFFFF_FFFF,
    )
    return header + bytes(directory) + b"".join(payloads)


def parse_rsc1(payload: bytes) -> RSC1Info:
    """Validate all structure and section hashes in one bounded pass."""

    if len(payload) < HEADER.size:
        raise ValueError("truncated RSC1 header")
    (
        magic,
        version_major,
        version_minor,
        profile,
        level,
        flags,
        timebase_hz,
        section_count,
        record_bytes,
        directory_bytes,
        expected_directory_crc,
    ) = HEADER.unpack_from(payload)
    if magic != MAGIC:
        raise ValueError("not an RSC1 stream")
    if (version_major, version_minor) != (VERSION_MAJOR, VERSION_MINOR):
        raise ValueError("unsupported RSC1 version")
    if flags != 0:
        raise ValueError("unsupported RSC1 feature")
    if not 1 <= timebase_hz <= MAX_TIMEBASE_HZ:
        raise ValueError("RSC1 timebase exceeds the profile bound")
    if section_count > MAX_SECTIONS:
        raise ValueError("too many RSC1 sections")
    if record_bytes != DIRECTORY_RECORD.size:
        raise ValueError("unsupported RSC1 directory record")
    if directory_bytes != section_count * DIRECTORY_RECORD.size:
        raise ValueError("non-canonical RSC1 directory size")

    directory_end = HEADER.size + directory_bytes
    if directory_end > len(payload):
        raise ValueError("truncated RSC1 directory")
    directory = payload[HEADER.size:directory_end]
    if zlib.crc32(directory) & 0xFFFF_FFFF != expected_directory_crc:
        raise ValueError("RSC1 directory checksum mismatch")

    cursor = directory_end
    total_bytes = 0
    previous_key: tuple[bytes, int] | None = None
    sections: list[RSC1Section] = []
    for index in range(section_count):
        record = DIRECTORY_RECORD.unpack_from(
            directory,
            index * DIRECTORY_RECORD.size,
        )
        (
            type_code,
            schema_version,
            section_flags,
            instance_id,
            start_tick,
            offset,
            stored_bytes,
            raw_bytes,
            expected_crc,
            expected_sha,
        ) = record
        _validated_type(type_code)
        if schema_version == 0:
            raise ValueError("invalid RSC1 section schema")
        if section_flags & ~KNOWN_SECTION_FLAGS:
            raise ValueError("unsupported RSC1 section flag")
        key = (type_code, instance_id)
        if previous_key is not None and key <= previous_key:
            raise ValueError("non-canonical or duplicate RSC1 section key")
        if stored_bytes != raw_bytes:
            raise ValueError("unsupported RSC1 section encoding")
        if raw_bytes > MAX_SECTION_BYTES:
            raise ValueError("RSC1 section exceeds the byte bound")
        if offset != cursor:
            raise ValueError("non-canonical RSC1 section offset")
        total_bytes += raw_bytes
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("RSC1 stream exceeds the total byte bound")
        end = cursor + stored_bytes
        if end > len(payload):
            raise ValueError("truncated RSC1 section")
        body = payload[cursor:end]
        if zlib.crc32(body) & 0xFFFF_FFFF != expected_crc:
            raise ValueError("RSC1 section checksum mismatch")
        if hashlib.sha256(body).digest() != expected_sha:
            raise ValueError("RSC1 section hash mismatch")
        sections.append(
            RSC1Section(
                type_code=type_code,
                payload=body,
                instance_id=instance_id,
                schema_version=schema_version,
                flags=section_flags,
                start_tick=start_tick,
            )
        )
        cursor = end
        previous_key = key

    if cursor != len(payload):
        raise ValueError("trailing bytes in RSC1 stream")
    return RSC1Info(
        profile=profile,
        level=level,
        timebase_hz=timebase_hz,
        sections=tuple(sections),
    )
