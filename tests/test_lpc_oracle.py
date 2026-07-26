from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lpc_oracle import (  # noqa: E402
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
    run_lpc_liftpack_oracle,
)
from maf_p0.rsc1 import parse_rsc1  # noqa: E402


class LPCOracleTests(unittest.TestCase):
    def test_multitone_truth_round_trips_and_selects_lpc(self) -> None:
        sample_rate = 48_000
        count = 16_384
        position = np.arange(count, dtype=np.float64)
        source = np.rint(
            12_000.0 * np.sin(2.0 * np.pi * 440.0 * position / sample_rate)
            + 6_000.0
            * np.sin(2.0 * np.pi * 733.0 * position / sample_rate + 0.3)
        ).astype(np.int16)

        packet, report = encode_lpc_liftpack_oracle(
            source,
            block_size=4096,
            lpc_orders=(4, 8),
        )
        restored = decode_lpc_liftpack_oracle(
            packet,
            expected_count=count,
        )
        np.testing.assert_array_equal(restored, source.astype(np.int64))
        self.assertGreater(report["transform_counts"]["lpc"], 0)

        result = run_lpc_liftpack_oracle(
            source,
            sample_rate,
            innovation_step=64,
            block_sizes=(2048, 4096),
            lpc_orders=(4, 8),
        )
        self.assertGreater(result.report["selected_reduction_vs_rsl1"], 0.0)
        self.assertLessEqual(result.report["max_abs_error"], 32)
        parsed = parse_rsc1(result.selected_payload)
        self.assertEqual((parsed.profile, parsed.level), (0, 3))
        self.assertEqual(
            [bytes(section.type_code) for section in parsed.sections],
            [b"CONF", b"RSL2"],
        )

    def test_corruption_and_bounds_are_rejected(self) -> None:
        source = np.arange(64, dtype=np.int16)
        packet, _ = encode_lpc_liftpack_oracle(
            source,
            block_size=16,
            lpc_orders=(4,),
        )
        corrupted = bytearray(packet)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_lpc_liftpack_oracle(bytes(corrupted))
        with self.assertRaises(ValueError):
            encode_lpc_liftpack_oracle(
                source,
                block_size=15,
                lpc_orders=(4,),
            )


if __name__ == "__main__":
    unittest.main()
