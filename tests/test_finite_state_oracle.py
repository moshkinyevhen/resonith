from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.finite_state_oracle import (  # noqa: E402
    _decode_adaptive,
    _encode_adaptive,
    compact_finite_state_lapped,
    compact_finite_state_lapped_size,
    compact_rice_value_lapped,
    compact_rice_value_lapped_size,
    decode_finite_state_lapped,
    decode_rice_value_lapped,
    encode_finite_state_lapped,
    encode_rice_value_lapped,
    expand_compact_finite_state_lapped,
    expand_compact_rice_value_lapped,
)


class FiniteStateOracleTests(unittest.TestCase):
    def test_adaptive_integer_coder_round_trips_and_is_deterministic(self) -> None:
        symbols = np.asarray(
            [0, 1, 0, 2, 31, 0, 1, 31] * 3000,
            dtype=np.int64,
        )
        payload, bit_count = _encode_adaptive(symbols, 32)
        repeated, repeated_bits = _encode_adaptive(symbols, 32)
        decoded = _decode_adaptive(payload, bit_count, symbols.size, 32)

        self.assertEqual((payload, bit_count), (repeated, repeated_bits))
        np.testing.assert_array_equal(decoded, symbols)

    @staticmethod
    def _fields() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        scales = np.asarray(
            [
                [[1, 2, 3], [1, 3, 3], [0, 3, 4]],
                [[2, 2, 4], [2, 2, 4], [2, 3, 4]],
            ],
            dtype=np.uint8,
        )
        counts = np.asarray([[3, 3, 3], [2, 2, 3]], dtype=np.uint16)
        positions = np.asarray(
            [
                1, 7, 50,
                1, 8, 50,
                8, 50, 63,
                2, 9,
                2, 9,
                2, 10, 60,
            ],
            dtype=np.uint16,
        )
        values = np.asarray(
            [
                4, -7, 2,
                3, -6, 1,
                -5, 2, 7,
                -4, 7,
                -3, 6,
                -2, 5, -1,
            ],
            dtype=np.int8,
        )
        return scales, counts, positions, values

    def test_sparse_fields_round_trip_with_exact_framing(self) -> None:
        scales, counts, positions, values = self._fields()
        payload = encode_finite_state_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        repeated = encode_finite_state_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        decoded = decode_finite_state_lapped(
            payload,
            half_window=64,
            expected_channels=2,
            expected_frames=3,
            expected_bands=3,
        )

        self.assertEqual(payload, repeated)
        np.testing.assert_array_equal(decoded.scales, scales)
        np.testing.assert_array_equal(decoded.counts, counts)
        np.testing.assert_array_equal(decoded.positions, positions)
        np.testing.assert_array_equal(decoded.values, values)

    def test_compact_transport_restores_exact_laf1(self) -> None:
        scales, counts, positions, values = self._fields()
        payload = encode_finite_state_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        compact = compact_finite_state_lapped(payload)
        restored = expand_compact_finite_state_lapped(
            compact,
            frame_count=3,
            channels=2,
            band_count=3,
        )

        self.assertEqual(restored, payload)
        self.assertEqual(compact_finite_state_lapped_size(compact), len(compact))
        with self.assertRaises(ValueError):
            compact_finite_state_lapped_size(compact[:-1])
        with self.assertRaises(ValueError):
            expand_compact_finite_state_lapped(
                compact + b"\0",
                frame_count=3,
                channels=2,
                band_count=3,
            )

    def test_rice_value_fields_and_compact_transport_round_trip(self) -> None:
        scales, counts, positions, values = self._fields()
        payload = encode_rice_value_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        compact = compact_rice_value_lapped(payload)
        restored = expand_compact_rice_value_lapped(
            compact,
            frame_count=3,
            channels=2,
            band_count=3,
        )
        decoded = decode_rice_value_lapped(
            restored,
            half_window=64,
            expected_channels=2,
            expected_frames=3,
            expected_bands=3,
        )

        self.assertEqual(restored, payload)
        self.assertEqual(compact_rice_value_lapped_size(compact), len(compact))
        np.testing.assert_array_equal(decoded.scales, scales)
        np.testing.assert_array_equal(decoded.counts, counts)
        np.testing.assert_array_equal(decoded.positions, positions)
        np.testing.assert_array_equal(decoded.values, values)
        with self.assertRaises(ValueError):
            compact_rice_value_lapped_size(compact[:-1])
        corrupted = bytearray(payload)
        corrupted[0] ^= 1
        for candidate in (bytes(corrupted), payload[:-1], payload + b"\0"):
            with self.assertRaises(ValueError):
                decode_rice_value_lapped(
                    candidate,
                    half_window=64,
                    expected_channels=2,
                    expected_frames=3,
                    expected_bands=3,
                )

    def test_corrupt_header_truncation_and_trailing_bytes_are_rejected(
        self,
    ) -> None:
        scales, counts, positions, values = self._fields()
        payload = encode_finite_state_lapped(
            scales,
            counts,
            positions,
            values,
            half_window=64,
        )
        corrupted = bytearray(payload)
        corrupted[0] ^= 1
        for candidate in (bytes(corrupted), payload[:-1], payload + b"\0"):
            with self.assertRaises(ValueError):
                decode_finite_state_lapped(
                    candidate,
                    half_window=64,
                    expected_channels=2,
                    expected_frames=3,
                    expected_bands=3,
                )

    def test_input_types_order_and_shape_are_bounded(self) -> None:
        scales, counts, positions, values = self._fields()
        with self.assertRaises(TypeError):
            encode_finite_state_lapped(
                scales.astype(np.int16),
                counts,
                positions,
                values,
                half_window=64,
            )
        invalid_positions = positions.copy()
        invalid_positions[1] = invalid_positions[0]
        with self.assertRaises(ValueError):
            encode_finite_state_lapped(
                scales,
                counts,
                invalid_positions,
                values,
                half_window=64,
            )


if __name__ == "__main__":
    unittest.main()
