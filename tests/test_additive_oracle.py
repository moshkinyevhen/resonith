from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.additive_oracle import run_additive_atom_oracle  # noqa: E402
from maf_p0.rsc1 import parse_rsc1  # noqa: E402


class AdditiveOracleTests(unittest.TestCase):
    def test_two_period_mixture_is_deterministic_and_fully_costed(self) -> None:
        sample_count = 12_000
        positions = np.arange(sample_count, dtype=np.float64)
        mixture = (
            11_000.0 * np.sin(2.0 * np.pi * positions / 97.0)
            + 7_000.0 * np.sin(2.0 * np.pi * positions / 211.0 + 0.4)
        )
        source = np.clip(np.rint(mixture), -32768, 32767).astype(np.int16)

        first = run_additive_atom_oracle(
            source,
            48_000,
            gain_block_size=4096,
            innovation_step=64,
            maximum_atoms=3,
            analysis_period_candidates=8,
            period_rdo_shortlist=4,
        )
        second = run_additive_atom_oracle(
            source,
            48_000,
            gain_block_size=4096,
            innovation_step=64,
            maximum_atoms=3,
            analysis_period_candidates=8,
            period_rdo_shortlist=4,
        )

        self.assertEqual(first.selected_payload, second.selected_payload)
        np.testing.assert_array_equal(
            first.selected_reconstruction,
            second.selected_reconstruction,
        )
        self.assertEqual(first.report["candidate_count"], 3)
        self.assertEqual(first.report["atom_count"], 2)
        self.assertGreater(first.report["selected_reduction_vs_one_atom"], 0.0)
        self.assertLessEqual(first.report["max_abs_error"], 32)
        parsed = parse_rsc1(first.selected_payload)
        self.assertEqual((parsed.profile, parsed.level), (0, 1))
        self.assertEqual(
            first.report["atom_count"],
            sum(
                bytes(section.type_code) == b"ATOM"
                for section in parsed.sections
            ),
        )
        for candidate in first.report["candidates"]:
            self.assertEqual(
                candidate["stream_bytes"],
                sum(candidate["section_bytes"].values()),
            )
            self.assertEqual(
                candidate["section_bytes"]["ENVELOPE"]
                + candidate["section_bytes"]["ATOM"]
                + candidate["section_bytes"]["BRAW"]
                + candidate["section_bytes"]["CONF"]
                + candidate["section_bytes"]["RSL1"],
                candidate["stream_bytes"],
            )

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            run_additive_atom_oracle(
                np.zeros((2, 64), dtype=np.int16),
                48_000,
            )
        with self.assertRaises(ValueError):
            run_additive_atom_oracle(
                np.zeros(64, dtype=np.int16),
                0,
            )


if __name__ == "__main__":
    unittest.main()
