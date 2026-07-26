from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.stereo_oracle import (  # noqa: E402
    decode_stereo_oracle,
    run_stereo_lifting_oracle,
)


class StereoOracleTests(unittest.TestCase):
    def test_correlated_stereo_selects_reversible_decorrelation(self) -> None:
        index = np.arange(4096)
        left = np.rint(12000 * np.sin(2 * np.pi * index / 71)).astype(np.int16)
        right = np.clip(
            left.astype(np.int64)
            + np.rint(300 * np.sin(2 * np.pi * index / 19)).astype(np.int64),
            -32768,
            32767,
        ).astype(np.int16)
        source = np.column_stack((left, right))

        result = run_stereo_lifting_oracle(
            source,
            48000,
            innovation_step=1,
            block_sizes=(1024, 4096),
            lpc_orders=(4, 8),
        )
        sample_rate, restored = decode_stereo_oracle(result.selected_payload)

        self.assertEqual(sample_rate, 48000)
        np.testing.assert_array_equal(restored, source.astype(np.int64))
        self.assertNotEqual(result.report["mode"], "independent")
        self.assertGreater(
            result.report["selected_reduction_vs_independent"],
            0.0,
        )

    def test_uncorrelated_input_retains_complete_fallback(self) -> None:
        rng = np.random.default_rng(45)
        source = rng.integers(
            -2000,
            2001,
            size=(2048, 2),
            dtype=np.int16,
        )
        result = run_stereo_lifting_oracle(
            source,
            44100,
            block_sizes=(1024, 2048),
            lpc_orders=(4,),
        )

        self.assertLessEqual(
            result.report["stream_bytes"],
            result.report["independent_anchor_bytes"],
        )
        self.assertEqual(result.report["candidate_count"], 4)


if __name__ == "__main__":
    unittest.main()
