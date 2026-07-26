from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.temporal_support_oracle import (  # noqa: E402
    decode_temporal_support_lapped,
    encode_temporal_support_lapped,
)


class TemporalSupportOracleTests(unittest.TestCase):
    @staticmethod
    def _fields() -> tuple[np.ndarray, np.ndarray]:
        scales = np.asarray(
            [
                [[1, 2, 3], [1, 3, 3], [0, 3, 4]],
                [[2, 2, 4], [2, 2, 4], [2, 3, 4]],
            ],
            dtype=np.uint8,
        )
        coefficients = np.zeros((2, 3, 64), dtype=np.int8)
        coefficients[0, 0, [1, 7, 50]] = [4, -7, 2]
        coefficients[0, 1, [1, 8, 50]] = [3, -6, 1]
        coefficients[0, 2, [8, 50, 63]] = [-5, 2, 7]
        coefficients[1, 0, [2, 9]] = [-4, 7]
        coefficients[1, 1, [2, 9]] = [-3, 6]
        coefficients[1, 2, [2, 10, 60]] = [-2, 5, -1]
        return scales, coefficients

    def test_round_trip_is_exact_deterministic_and_reset(self) -> None:
        scales, coefficients = self._fields()
        payload = encode_temporal_support_lapped(
            scales,
            coefficients,
            half_window=64,
        )
        repeated = encode_temporal_support_lapped(
            scales,
            coefficients,
            half_window=64,
        )
        decoded = decode_temporal_support_lapped(
            payload,
            half_window=64,
            expected_channels=2,
            expected_frames=3,
            expected_bands=3,
        )

        self.assertEqual(payload, repeated)
        np.testing.assert_array_equal(decoded.scales, scales)
        np.testing.assert_array_equal(decoded.coefficients, coefficients)

    def test_header_corruption_truncation_and_trailing_bytes_are_rejected(
        self,
    ) -> None:
        scales, coefficients = self._fields()
        payload = encode_temporal_support_lapped(
            scales,
            coefficients,
            half_window=64,
        )
        corrupted = bytearray(payload)
        corrupted[0] ^= 1
        for candidate in (bytes(corrupted), payload[:-1], payload + b"\0"):
            with self.assertRaises(ValueError):
                decode_temporal_support_lapped(
                    candidate,
                    half_window=64,
                    expected_channels=2,
                    expected_frames=3,
                    expected_bands=3,
                )

    def test_shape_type_and_profile_bounds_are_enforced(self) -> None:
        scales, coefficients = self._fields()
        with self.assertRaises(TypeError):
            encode_temporal_support_lapped(
                scales.astype(np.int16),
                coefficients,
                half_window=64,
            )
        with self.assertRaises(ValueError):
            encode_temporal_support_lapped(
                np.full_like(scales, 32),
                coefficients,
                half_window=64,
            )
        payload = encode_temporal_support_lapped(
            scales,
            coefficients,
            half_window=64,
        )
        with self.assertRaises(ValueError):
            decode_temporal_support_lapped(
                payload,
                half_window=64,
                expected_channels=1,
                expected_frames=3,
                expected_bands=3,
            )


if __name__ == "__main__":
    unittest.main()
