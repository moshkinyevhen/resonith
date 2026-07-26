from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.sparse_entropy import (  # noqa: E402
    decode_sparse_lapped,
    decode_variable_sparse_lapped,
    encode_sparse_lapped,
    encode_variable_sparse_lapped,
)


class SparseEntropyTests(unittest.TestCase):
    @staticmethod
    def _fields() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        scales = np.asarray(
            [
                [[1, 3, 4], [1, 4, 4]],
                [[2, 2, 5], [2, 3, 4]],
            ],
            dtype=np.uint8,
        )
        positions = np.asarray(
            [
                [[0, 7, 63], [1, 8, 62]],
                [[2, 9, 61], [3, 10, 60]],
            ],
            dtype=np.uint16,
        )
        values = np.asarray(
            [
                [[4, -7, 2], [3, -6, 1]],
                [[-4, 7, -2], [-3, 6, -1]],
            ],
            dtype=np.int8,
        )
        return scales, positions, values

    def test_round_trip_is_exact_and_deterministic(self) -> None:
        scales, positions, values = self._fields()
        payload = encode_sparse_lapped(
            scales,
            positions,
            values,
            half_window=64,
        )
        repeated = encode_sparse_lapped(
            scales,
            positions,
            values,
            half_window=64,
        )
        decoded = decode_sparse_lapped(
            payload,
            half_window=64,
            expected_channels=2,
            expected_frames=2,
            expected_bands=3,
        )

        self.assertEqual(payload, repeated)
        np.testing.assert_array_equal(decoded.scales, scales)
        np.testing.assert_array_equal(decoded.positions, positions)
        np.testing.assert_array_equal(decoded.values, values)

    def test_shape_corruption_and_order_are_rejected(self) -> None:
        scales, positions, values = self._fields()
        invalid_positions = positions.copy()
        invalid_positions[0, 0, 1] = invalid_positions[0, 0, 0]
        with self.assertRaises(ValueError):
            encode_sparse_lapped(
                scales,
                invalid_positions,
                values,
                half_window=64,
            )
        payload = encode_sparse_lapped(
            scales,
            positions,
            values,
            half_window=64,
        )
        with self.assertRaises(ValueError):
            decode_sparse_lapped(
                payload,
                half_window=64,
                expected_channels=1,
                expected_frames=2,
                expected_bands=3,
            )
        corrupted = bytearray(payload)
        corrupted[0] ^= 1
        with self.assertRaises(ValueError):
            decode_sparse_lapped(
                bytes(corrupted),
                half_window=64,
                expected_channels=2,
                expected_frames=2,
                expected_bands=3,
            )

    def test_variable_density_round_trip_including_empty_frame(self) -> None:
        scales, _positions, _values = self._fields()
        counts = np.asarray([[2, 0], [1, 3]], dtype=np.uint16)
        positions = np.asarray([0, 7, 2, 3, 10, 60], dtype=np.uint16)
        values = np.asarray([4, -7, -4, -3, 6, -1], dtype=np.int8)
        payload = encode_variable_sparse_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        decoded = decode_variable_sparse_lapped(
            payload,
            half_window=64,
            expected_channels=2,
            expected_frames=2,
            expected_bands=3,
        )

        np.testing.assert_array_equal(decoded.scales, scales)
        np.testing.assert_array_equal(decoded.counts, counts)
        np.testing.assert_array_equal(decoded.positions, positions)
        np.testing.assert_array_equal(decoded.values, values)


if __name__ == "__main__":
    unittest.main()
