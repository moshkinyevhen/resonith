from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.basis_section import pack_braw, unpack_braw  # noqa: E402


class RawBasisSectionTests(unittest.TestCase):
    def test_round_trip_is_exact_and_channel_major(self) -> None:
        basis = np.arange(-24, 24, dtype=np.int16).reshape(3, 16)
        restored = unpack_braw(pack_braw(basis))
        np.testing.assert_array_equal(restored, basis)

    def test_invalid_dtype_shape_and_truncation_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            pack_braw(np.zeros(16, dtype=np.int16))
        with self.assertRaises(TypeError):
            pack_braw(np.zeros((1, 16), dtype=np.float32))
        payload = pack_braw(np.zeros((1, 16), dtype=np.int16))
        with self.assertRaisesRegex(ValueError, "size"):
            unpack_braw(payload[:-1])

    def test_native_payload_matches_python(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "basis_test.cpp"
        ).read_text(encoding="utf-8")

        def array(name: str) -> list[int]:
            match = re.search(
                rf"{name}\s*=\s*\{{(.*?)\}};",
                source,
                re.DOTALL,
            )
            if match is None:
                raise AssertionError(f"missing native array {name}")
            return [
                int(token, 0)
                for token in re.findall(
                    r"(?<![A-Za-z0-9_])(-?0x[0-9a-fA-F]+|-?\d+)",
                    match.group(1),
                )
            ]

        expected = np.asarray(array("kExpectedBasis"), dtype=np.int16).reshape(
            1,
            -1,
        )
        native_payload = bytes(array("kBrawPayload"))
        self.assertEqual(native_payload, pack_braw(expected))
        np.testing.assert_array_equal(unpack_braw(native_payload), expected)

    def test_feature_flags_are_rejected(self) -> None:
        payload = bytearray(pack_braw(np.zeros((1, 2), dtype=np.int16)))
        payload[2] = 1
        with self.assertRaisesRegex(ValueError, "feature"):
            unpack_braw(bytes(payload))


if __name__ == "__main__":
    unittest.main()
