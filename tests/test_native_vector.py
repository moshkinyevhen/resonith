from __future__ import annotations

from pathlib import Path
import hashlib
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = REPOSITORY_ROOT / "reference"
sys.path.insert(0, str(REFERENCE_ROOT))

from maf_p0.residual import decode_liftpack, encode_liftpack  # noqa: E402
from maf_p0.rsc1 import RSC1Section, pack_rsc1, parse_rsc1  # noqa: E402


class NativeConformanceVectorTests(unittest.TestCase):
    @staticmethod
    def _embedded_array(cpp_source: str, name: str) -> bytes:
        initializer = re.search(
            rf"{name}\s*=\s*\{{(.*?)\}};",
            cpp_source,
            re.DOTALL,
        )
        if initializer is None:
            raise AssertionError(f"missing C++ byte array {name}")
        return bytes(
            int(value, 16)
            for value in re.findall(
                r"0x([0-9a-fA-F]{2})",
                initializer.group(1),
            )
        )

    def test_cpp_vector_matches_the_python_golden_encoder(self) -> None:
        source = np.concatenate(
            (
                np.zeros(64, dtype=np.int32),
                np.arange(-32, 32, dtype=np.int32),
                np.tile(
                    np.asarray([32767, -32768], dtype=np.int32),
                    32,
                ),
            )
        )
        canonical = encode_liftpack(source, block_size=64).payload

        cpp_source = (
            REPOSITORY_ROOT / "native" / "tests" / "liftpack_test.cpp"
        ).read_text(encoding="utf-8")
        embedded = self._embedded_array(cpp_source, "kConformanceStream")

        self.assertEqual(embedded, canonical)
        self.assertEqual(
            hashlib.sha256(embedded).hexdigest(),
            "6d58812162388dfe58c2b602372bf144d36af00f7a19cb39250e0d920609fee6",
        )

    def test_cpp_all_modes_vector_is_valid_in_the_python_decoder(self) -> None:
        cpp_source = (
            REPOSITORY_ROOT / "native" / "tests" / "liftpack_test.cpp"
        ).read_text(encoding="utf-8")
        embedded = self._embedded_array(cpp_source, "kAllModesStream")
        self.assertEqual(
            hashlib.sha256(embedded).hexdigest(),
            "78098148fcd6bfd2e11e0276a7b93d9936a334f80e4a4b60f578d11bcd83182e",
        )

        index = np.arange(16, dtype=np.int64)
        expected = np.concatenate(
            (
                np.where(index % 2 == 0, 1, -1) * (index * 3 + 1),
                100 + index * 7,
                index * index - 50,
                (index % 5) * 100 - index * 3,
            )
        )
        np.testing.assert_array_equal(decode_liftpack(embedded), expected)

    def test_cpp_rsc1_prefix_matches_the_python_container(self) -> None:
        cpp_source = (
            REPOSITORY_ROOT / "native" / "tests" / "liftpack_test.cpp"
        ).read_text(encoding="utf-8")
        residual = self._embedded_array(cpp_source, "kConformanceStream")
        prefix = self._embedded_array(cpp_source, "kContainerPrefix")
        embedded = prefix + residual
        canonical = pack_rsc1(
            [RSC1Section("RSL1", residual)],
            timebase_hz=48_000,
        )
        self.assertEqual(embedded, canonical)
        self.assertEqual(
            hashlib.sha256(embedded).hexdigest(),
            "d8fc786a31c43e30b6d0d612ac22730aaded9847bdc739e74119bc3ce9247c1d",
        )
        parsed = parse_rsc1(embedded)
        self.assertEqual(parsed.sections[0].payload, residual)


if __name__ == "__main__":
    unittest.main()
