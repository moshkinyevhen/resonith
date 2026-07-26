from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.fixed_lapped import (  # noqa: E402
    analyze_fixed_lapped,
    fixed_lapped_tables,
    round_shift_signed,
    synthesize_fixed_lapped_frame,
    synthesis_output_shift,
)


class FixedLappedTests(unittest.TestCase):
    def test_tables_and_transform_are_deterministic(self) -> None:
        window, cosine, identity = fixed_lapped_tables(64)
        repeated_window, repeated_cosine, repeated_identity = (
            fixed_lapped_tables(64)
        )
        np.testing.assert_array_equal(window, repeated_window)
        np.testing.assert_array_equal(cosine, repeated_cosine)
        self.assertEqual(identity, repeated_identity)
        self.assertEqual(len(identity), 64)

        block = np.arange(-64, 64, dtype=np.int16)
        coefficients = analyze_fixed_lapped(block, 64)
        synthesis = synthesize_fixed_lapped_frame(coefficients, 64)
        self.assertEqual(coefficients.shape, (64,))
        self.assertEqual(synthesis.shape, (128,))
        self.assertEqual(synthesis_output_shift(64), 34)

    def test_signed_rounding_is_symmetric(self) -> None:
        values = np.asarray([-7, -6, -5, 5, 6, 7], dtype=np.int64)
        rounded = round_shift_signed(values, 2)
        np.testing.assert_array_equal(
            rounded,
            np.asarray([-2, -2, -1, 1, 2, 2], dtype=np.int64),
        )

    def test_lapped_backend_round_trip_is_independently_fixed(self) -> None:
        from maf_p0.lapped_oracle import (
            decode_lapped_stream,
            encode_lapped_stream,
        )

        frame = np.arange(4096, dtype=np.float64)
        source = np.stack(
            (
                np.rint(12000 * np.sin(2 * np.pi * frame / 97)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 151)),
            ),
            axis=1,
        ).astype(np.int16)
        encoded = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=48,
            half_window=256,
            band_count=16,
            entropy_backend="bounded",
            transform_backend="fixed",
        )
        decoded = decode_lapped_stream(encoded.payload)

        np.testing.assert_array_equal(decoded.samples, encoded.reconstruction)
        self.assertIn("fixed Q15", encoded.report["transform_backend"])
        self.assertEqual(len(encoded.report["fixed_table_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
