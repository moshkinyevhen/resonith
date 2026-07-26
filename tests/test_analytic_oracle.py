from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.analytic_oracle import (  # noqa: E402
    SINE_ROM_SHA256,
    run_analytic_oscillator_oracle,
)
from maf_p0.rsc1 import parse_rsc1  # noqa: E402


class AnalyticOracleTests(unittest.TestCase):
    def test_two_tones_select_a_batched_integer_oscillator_bank(self) -> None:
        sample_rate = 48_000
        sample_count = 12_000
        position = np.arange(sample_count, dtype=np.float64)
        source = np.rint(
            11_000.0 * np.sin(2.0 * np.pi * 440.0 * position / sample_rate)
            + 7_000.0
            * np.sin(
                2.0 * np.pi * 733.0 * position / sample_rate + 0.4
            )
        ).astype(np.int16)

        result = run_analytic_oscillator_oracle(
            source,
            sample_rate,
            maximum_atoms=3,
            spectral_candidates=8,
            rdo_shortlist=4,
        )

        self.assertGreaterEqual(result.report["atom_count"], 1)
        self.assertLess(
            result.report["stream_bytes"],
            result.report["zero_atom_bytes"],
        )
        self.assertLessEqual(result.report["max_abs_error"], 32)
        self.assertEqual(result.report["sine_rom_sha256"], SINE_ROM_SHA256)
        parsed = parse_rsc1(result.selected_payload)
        self.assertEqual((parsed.profile, parsed.level), (0, 2))
        self.assertEqual(
            [bytes(section.type_code) for section in parsed.sections],
            [b"CONF", b"HBNK", b"RSL1"],
        )
        for candidate in result.report["candidates"]:
            self.assertEqual(
                candidate["stream_bytes"],
                sum(candidate["section_bytes"].values()),
            )

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            run_analytic_oscillator_oracle(
                np.zeros((2, 64), dtype=np.int16),
                48_000,
            )
        with self.assertRaises(ValueError):
            run_analytic_oscillator_oracle(
                np.zeros(64, dtype=np.int16),
                48_000,
                maximum_atoms=65,
            )


if __name__ == "__main__":
    unittest.main()
