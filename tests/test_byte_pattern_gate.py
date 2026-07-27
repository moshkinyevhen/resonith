"""Regression tests for the frozen R-152/R-154 provider comparison."""

from __future__ import annotations

import unittest

import numpy as np

from experiments.gemini_byte_pattern_gate import _prompt_language_rows
from maf_p0.foundry_cuda import RESULT_DTYPE


class BytePatternGateTests(unittest.TestCase):
    def test_later_reverse_law_cannot_change_the_frozen_prompt_authority(
        self,
    ) -> None:
        rows = np.zeros(3, dtype=RESULT_DTYPE)
        rows["transform_flags"] = (0, 1, 2)
        filtered = _prompt_language_rows(rows)
        self.assertEqual(filtered.size, 2)
        np.testing.assert_array_equal(
            filtered["transform_flags"],
            np.asarray((0, 1), dtype=np.uint32),
        )


if __name__ == "__main__":
    unittest.main()
