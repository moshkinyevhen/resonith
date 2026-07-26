from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.variable_block_oracle import (  # noqa: E402
    decode_variable_liftpack_oracle,
    encode_variable_liftpack_oracle,
    run_variable_block_oracle,
)


class VariableBlockOracleTests(unittest.TestCase):
    def test_variable_partition_is_exact_and_uses_multiple_lengths(self) -> None:
        first = np.rint(
            4000 * np.sin(2 * np.pi * np.arange(4096) / 71)
        ).astype(np.int16)
        second = np.rint(
            12000 * np.sin(2 * np.pi * np.arange(2048) / 19)
        ).astype(np.int16)
        source = np.concatenate((first, second, first[:1024]))
        packet, report = encode_variable_liftpack_oracle(
            source,
            boundary_quantum=1024,
            maximum_block_size=4096,
            lpc_orders=(4, 8),
        )

        restored = decode_variable_liftpack_oracle(
            packet,
            expected_count=source.size,
        )

        np.testing.assert_array_equal(restored, source.astype(np.int64))
        self.assertGreaterEqual(report["block_count"], 2)
        self.assertEqual(
            sum(report["block_length_counts"].values()),
            report["block_count"],
        )

    def test_complete_oracle_preserves_fixed_fallback(self) -> None:
        source = np.zeros(8192, dtype=np.int16)
        result = run_variable_block_oracle(
            source,
            48000,
            fixed_block_sizes=(1024, 4096),
            boundary_quanta=(1024,),
            lpc_orders=(4,),
        )

        np.testing.assert_array_equal(result.selected_reconstruction, source)
        self.assertLessEqual(
            result.report["stream_bytes"],
            result.report["best_variable_bytes"],
        )

    def test_checksum_and_lifetime_bounds_are_rejected(self) -> None:
        source = np.arange(64, dtype=np.int16)
        packet, _ = encode_variable_liftpack_oracle(
            source,
            boundary_quantum=32,
            maximum_block_size=64,
            lpc_orders=(4,),
        )
        damaged = bytearray(packet)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_variable_liftpack_oracle(bytes(damaged))

        with self.assertRaisesRegex(ValueError, "shorter"):
            encode_variable_liftpack_oracle(
                np.zeros(15, dtype=np.int16),
                boundary_quantum=16,
            )


if __name__ == "__main__":
    unittest.main()
