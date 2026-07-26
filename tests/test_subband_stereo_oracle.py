from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.subband_stereo_oracle import (  # noqa: E402
    _inverse_temporal_haar,
    decode_subband_stereo_oracle,
    run_subband_stereo_oracle,
)


class SubbandStereoOracleTests(unittest.TestCase):
    def test_band_local_correlation_can_select_different_modes(self) -> None:
        rng = np.random.default_rng(47)
        low_left = rng.integers(-2000, 2001, size=2048, dtype=np.int16)
        low = np.column_stack((low_left, low_left)).astype(np.int64)
        high = rng.integers(
            -500,
            501,
            size=(2048, 2),
            dtype=np.int16,
        ).astype(np.int64)
        source = _inverse_temporal_haar(low, high, 0).astype(np.int16)

        result = run_subband_stereo_oracle(
            source,
            48000,
            innovation_step=1,
            block_sizes=(1024, 4096),
            lpc_orders=(4,),
        )
        sample_rate, restored = decode_subband_stereo_oracle(
            result.selected_payload
        )

        self.assertEqual(sample_rate, 48000)
        np.testing.assert_array_equal(restored, source.astype(np.int64))
        self.assertTrue(result.report["subband_won"])
        self.assertNotEqual(result.report["low_mode"], "independent")

    def test_complete_fallback_is_never_larger(self) -> None:
        rng = np.random.default_rng(470)
        source = rng.integers(
            -2000,
            2001,
            size=(2048, 2),
            dtype=np.int16,
        )
        result = run_subband_stereo_oracle(
            source,
            44100,
            block_sizes=(1024, 2048),
            lpc_orders=(4,),
        )

        self.assertLessEqual(
            result.report["stream_bytes"],
            result.report["best_subband_bytes"],
        )
        self.assertEqual(result.report["candidate_count"], 17)


if __name__ == "__main__":
    unittest.main()
