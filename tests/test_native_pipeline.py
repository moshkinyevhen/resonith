from __future__ import annotations

from pathlib import Path
import hashlib
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.main0 import decode_main0_raw_stream  # noqa: E402


class NativePipelineTests(unittest.TestCase):
    def test_complete_native_vector_matches_python(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "pipeline_test.cpp"
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
                int(token.rstrip("U"), 0)
                for token in re.findall(
                    r"(?<![A-Za-z0-9_])(-?0x[0-9a-fA-F]+U?|-?\d+U?)",
                    match.group(1),
                )
            ]

        stream = bytes(array("kMain0Stream"))
        decoded = decode_main0_raw_stream(stream)
        self.assertEqual(decoded.sample_rate, 48_000)
        self.assertEqual(
            hashlib.sha256(stream).hexdigest(),
            "32e4e7d0f8b5ff7c2d7c33ed51579c24731d57ee9c681cbc480eee23e0e3aa74",
        )
        np.testing.assert_array_equal(
            decoded.samples,
            np.asarray(array("kExpectedPcm"), dtype=np.int16),
        )


if __name__ == "__main__":
    unittest.main()
