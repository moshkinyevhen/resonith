from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.container import (  # noqa: E402
    MAGIC,
    MAX_HEADER_BYTES,
    VERSION,
    pack_container,
    unpack_container,
)


def rewrite_directory(payload: bytes, sections: list[dict], bodies: bytes) -> bytes:
    prefix_size = len(MAGIC) + struct.calcsize("<BI")
    _, header_length = struct.unpack_from("<BI", payload, len(MAGIC))
    header = json.loads(
        payload[prefix_size : prefix_size + header_length].decode("utf-8")
    )
    header["sections"] = sections
    encoded = json.dumps(
        header,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return MAGIC + struct.pack("<BI", VERSION, len(encoded)) + encoded + bodies


class ContainerTests(unittest.TestCase):
    def test_integer_sections_round_trip(self) -> None:
        arrays = {
            "I16": np.arange(128, dtype=np.int16),
            "U32": np.arange(16, dtype=np.uint32),
            "BOOL": np.array([True, False, True], dtype=np.bool_),
        }
        metadata, restored = unpack_container(pack_container({"kind": "test"}, arrays))
        self.assertEqual(metadata["kind"], "test")
        for name, expected in arrays.items():
            np.testing.assert_array_equal(restored[name], expected)

    def test_preencoded_section_is_stored_without_second_compression(self) -> None:
        encoded = np.arange(257, dtype=np.uint8)
        payload = pack_container(
            {"profile": "test"},
            {"RSL1": encoded},
            stored_sections={"RSL1"},
        )
        metadata, arrays = unpack_container(payload)
        section = metadata["sections"][0]
        self.assertEqual(section["compression"], "stored")
        self.assertEqual(section["compressed_bytes"], encoded.nbytes)
        np.testing.assert_array_equal(arrays["RSL1"], encoded)

    def test_float_and_expansion_mismatch_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dtype"):
            pack_container({}, {"FLOAT": np.zeros(8, dtype=np.float32)})

        payload = pack_container({}, {"DATA": np.zeros(4096, dtype=np.int16)})
        prefix_size = len(MAGIC) + struct.calcsize("<BI")
        _, header_length = struct.unpack_from("<BI", payload, len(MAGIC))
        header = json.loads(
            payload[prefix_size : prefix_size + header_length].decode("utf-8")
        )
        section = dict(header["sections"][0])
        section["raw_bytes"] = 1
        body = payload[prefix_size + header_length :]
        damaged = rewrite_directory(payload, [section], body)
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            unpack_container(damaged)

    def test_duplicate_sections_and_oversized_header_are_rejected(self) -> None:
        payload = pack_container({}, {"DATA": np.arange(16, dtype=np.int16)})
        prefix_size = len(MAGIC) + struct.calcsize("<BI")
        _, header_length = struct.unpack_from("<BI", payload, len(MAGIC))
        header = json.loads(
            payload[prefix_size : prefix_size + header_length].decode("utf-8")
        )
        body = payload[prefix_size + header_length :]
        duplicate = rewrite_directory(
            payload,
            [header["sections"][0], header["sections"][0]],
            body + body,
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            unpack_container(duplicate)

        oversized = MAGIC + struct.pack("<BI", VERSION, MAX_HEADER_BYTES + 1)
        with self.assertRaisesRegex(ValueError, "header exceeds"):
            unpack_container(oversized)


if __name__ == "__main__":
    unittest.main()
