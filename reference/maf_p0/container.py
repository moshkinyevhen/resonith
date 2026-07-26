"""Small self-describing experimental MAF-P0 container."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib

import numpy as np


MAGIC = b"MAF0"
VERSION = 1


def pack_container(metadata: dict, arrays: dict[str, np.ndarray]) -> bytes:
    section_metadata: list[dict] = []
    compressed_sections: list[bytes] = []

    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        raw = array.tobytes(order="C")
        compressed = zlib.compress(raw, level=9)
        section_metadata.append(
            {
                "name": name,
                "dtype": array.dtype.str,
                "shape": list(array.shape),
                "raw_bytes": len(raw),
                "compressed_bytes": len(compressed),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        compressed_sections.append(compressed)

    header = dict(metadata)
    header["sections"] = section_metadata
    header_bytes = json.dumps(
        header, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    prefix = MAGIC + struct.pack("<BI", VERSION, len(header_bytes))
    return prefix + header_bytes + b"".join(compressed_sections)


def unpack_container(payload: bytes) -> tuple[dict, dict[str, np.ndarray]]:
    minimum = len(MAGIC) + struct.calcsize("<BI")
    if len(payload) < minimum or payload[:4] != MAGIC:
        raise ValueError("not a MAF-P0 stream")
    version, header_length = struct.unpack_from("<BI", payload, 4)
    if version != VERSION:
        raise ValueError(f"unsupported MAF-P0 version {version}")
    header_start = minimum
    header_end = header_start + header_length
    if header_end > len(payload):
        raise ValueError("truncated MAF-P0 header")
    metadata = json.loads(payload[header_start:header_end].decode("utf-8"))

    cursor = header_end
    arrays: dict[str, np.ndarray] = {}
    for section in metadata.get("sections", []):
        compressed_bytes = int(section["compressed_bytes"])
        end = cursor + compressed_bytes
        if end > len(payload):
            raise ValueError("truncated MAF-P0 section")
        try:
            raw = zlib.decompress(payload[cursor:end])
        except zlib.error as error:
            raise ValueError("invalid compressed MAF-P0 section") from error
        cursor = end
        if len(raw) != int(section["raw_bytes"]):
            raise ValueError("section size mismatch")
        if hashlib.sha256(raw).hexdigest() != section["sha256"]:
            raise ValueError("section hash mismatch")
        dtype = np.dtype(section["dtype"])
        shape = tuple(int(value) for value in section["shape"])
        array = np.frombuffer(raw, dtype=dtype)
        expected = int(np.prod(shape, dtype=np.int64))
        if array.size != expected:
            raise ValueError("section element count mismatch")
        arrays[str(section["name"])] = array.reshape(shape).copy()

    if cursor != len(payload):
        raise ValueError("trailing bytes in MAF-P0 stream")
    return metadata, arrays
