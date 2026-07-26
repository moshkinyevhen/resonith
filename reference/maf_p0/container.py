"""Small self-describing experimental MAF-P0 container."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib

import numpy as np


MAGIC = b"MAF0"
VERSION = 1
MAX_HEADER_BYTES = 4 << 20
MAX_SECTIONS = 4096
MAX_SECTION_RAW_BYTES = 512 << 20
MAX_TOTAL_RAW_BYTES = 1 << 30
MAX_ARRAY_DIMENSIONS = 8
MAX_ARRAY_ELEMENTS = (1 << 31) - 1


def _validate_section_name(name: str) -> None:
    if not name or len(name) > 32 or not name.isascii():
        raise ValueError("section name must be 1-32 ASCII characters")


def _validated_dtype(text: str) -> np.dtype:
    dtype = np.dtype(text)
    if dtype.hasobject or dtype.kind not in {"b", "i", "u"} or dtype.itemsize > 8:
        raise ValueError("unsupported MAF-P0 section dtype")
    return dtype


def _validated_shape(shape_value: object) -> tuple[int, ...]:
    if not isinstance(shape_value, list) or len(shape_value) > MAX_ARRAY_DIMENSIONS:
        raise ValueError("invalid MAF-P0 section rank")
    if any(type(value) is not int for value in shape_value):
        raise ValueError("MAF-P0 section dimensions must be integers")
    shape = tuple(shape_value)
    if any(value < 0 for value in shape):
        raise ValueError("negative MAF-P0 section dimension")
    elements = 1
    for value in shape:
        elements *= value
        if elements > MAX_ARRAY_ELEMENTS:
            raise ValueError("MAF-P0 section element count exceeds the bound")
    return shape


def pack_container(metadata: dict, arrays: dict[str, np.ndarray]) -> bytes:
    if len(arrays) > MAX_SECTIONS:
        raise ValueError("too many MAF-P0 sections")
    section_metadata: list[dict] = []
    compressed_sections: list[bytes] = []
    total_raw_bytes = 0

    for name in sorted(arrays):
        _validate_section_name(name)
        array = np.ascontiguousarray(arrays[name])
        _validated_dtype(array.dtype.str)
        _validated_shape(list(array.shape))
        raw = array.tobytes(order="C")
        if len(raw) > MAX_SECTION_RAW_BYTES:
            raise ValueError("MAF-P0 section exceeds the raw-byte bound")
        total_raw_bytes += len(raw)
        if total_raw_bytes > MAX_TOTAL_RAW_BYTES:
            raise ValueError("MAF-P0 stream exceeds the total raw-byte bound")
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
    if len(header_bytes) > MAX_HEADER_BYTES:
        raise ValueError("MAF-P0 header exceeds the bound")
    prefix = MAGIC + struct.pack("<BI", VERSION, len(header_bytes))
    return prefix + header_bytes + b"".join(compressed_sections)


def unpack_container(payload: bytes) -> tuple[dict, dict[str, np.ndarray]]:
    minimum = len(MAGIC) + struct.calcsize("<BI")
    if len(payload) < minimum or payload[:4] != MAGIC:
        raise ValueError("not a MAF-P0 stream")
    version, header_length = struct.unpack_from("<BI", payload, 4)
    if version != VERSION:
        raise ValueError(f"unsupported MAF-P0 version {version}")
    if header_length > MAX_HEADER_BYTES:
        raise ValueError("MAF-P0 header exceeds the bound")
    header_start = minimum
    header_end = header_start + header_length
    if header_end > len(payload):
        raise ValueError("truncated MAF-P0 header")
    metadata = json.loads(payload[header_start:header_end].decode("utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("MAF-P0 header must be an object")
    sections = metadata.get("sections", [])
    if not isinstance(sections, list) or len(sections) > MAX_SECTIONS:
        raise ValueError("invalid MAF-P0 section directory")

    cursor = header_end
    arrays: dict[str, np.ndarray] = {}
    total_raw_bytes = 0
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("invalid MAF-P0 section record")
        name = str(section["name"])
        _validate_section_name(name)
        if name in arrays:
            raise ValueError("duplicate MAF-P0 section name")
        if type(section["compressed_bytes"]) is not int or type(section["raw_bytes"]) is not int:
            raise ValueError("MAF-P0 section sizes must be integers")
        compressed_bytes = section["compressed_bytes"]
        raw_bytes = section["raw_bytes"]
        if compressed_bytes < 0 or raw_bytes < 0:
            raise ValueError("negative MAF-P0 section size")
        if raw_bytes > MAX_SECTION_RAW_BYTES:
            raise ValueError("MAF-P0 section exceeds the raw-byte bound")
        total_raw_bytes += raw_bytes
        if total_raw_bytes > MAX_TOTAL_RAW_BYTES:
            raise ValueError("MAF-P0 stream exceeds the total raw-byte bound")
        end = cursor + compressed_bytes
        if end > len(payload):
            raise ValueError("truncated MAF-P0 section")
        try:
            decompressor = zlib.decompressobj()
            raw = decompressor.decompress(
                payload[cursor:end],
                raw_bytes + 1,
            )
        except zlib.error as error:
            raise ValueError("invalid compressed MAF-P0 section") from error
        cursor = end
        if (
            len(raw) != raw_bytes
            or not decompressor.eof
            or decompressor.unconsumed_tail
            or decompressor.unused_data
        ):
            raise ValueError("section size mismatch")
        if hashlib.sha256(raw).hexdigest() != section["sha256"]:
            raise ValueError("section hash mismatch")
        dtype = _validated_dtype(str(section["dtype"]))
        shape = _validated_shape(section["shape"])
        array = np.frombuffer(raw, dtype=dtype)
        expected = math.prod(shape)
        if array.size != expected:
            raise ValueError("section element count mismatch")
        arrays[name] = array.reshape(shape).copy()

    if cursor != len(payload):
        raise ValueError("trailing bytes in MAF-P0 stream")
    return metadata, arrays
