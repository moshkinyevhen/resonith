from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.cross_channel_oracle import (  # noqa: E402
    decode_cross_channel_oracle,
    run_cross_channel_oracle,
)


class CrossChannelOracleTests(unittest.TestCase):
    def test_delayed_scaled_channel_selects_one_mac_predictor(self) -> None:
        rng = np.random.default_rng(46)
        reference = rng.integers(-12000, 12001, size=4096, dtype=np.int16)
        target = np.zeros_like(reference)
        target[5:] = np.rint(
            reference[:-5].astype(np.float64) * 0.75
        ).astype(np.int16)
        source = np.column_stack((reference, target))

        result = run_cross_channel_oracle(
            source,
            48000,
            innovation_step=1,
            block_sizes=(1024, 4096),
            lpc_orders=(4,),
            delays=tuple(range(-8, 9)),
            shortlist_per_direction=2,
        )
        sample_rate, restored = decode_cross_channel_oracle(
            result.selected_payload
        )

        self.assertEqual(sample_rate, 48000)
        np.testing.assert_array_equal(restored, source.astype(np.int64))
        self.assertTrue(result.report["cross_won"])
        self.assertEqual(result.report["mode"], "left_reference")
        self.assertEqual(result.report["delay"], 5)

    def test_uncorrelated_channels_retain_r045_fallback(self) -> None:
        rng = np.random.default_rng(460)
        source = rng.integers(
            -2000,
            2001,
            size=(2048, 2),
            dtype=np.int16,
        )
        result = run_cross_channel_oracle(
            source,
            44100,
            block_sizes=(1024, 2048),
            lpc_orders=(4,),
            delays=(-1, 0, 1),
            shortlist_per_direction=1,
        )

        self.assertLessEqual(
            result.report["stream_bytes"],
            result.report["best_cross_bytes"],
        )
        self.assertEqual(result.report["candidate_count"], 3)


if __name__ == "__main__":
    unittest.main()
