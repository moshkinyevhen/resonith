from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.lapped_oracle import (  # noqa: E402
    decode_lapped_stream,
    encode_lapped_stream,
)


class LappedOracleTests(unittest.TestCase):
    @staticmethod
    def _stereo(frame_count: int = 4096) -> np.ndarray:
        frame = np.arange(frame_count, dtype=np.float64)
        return np.stack(
            (
                np.rint(
                    13000 * np.sin(2 * np.pi * frame / 109)
                    + 5000 * np.sin(2 * np.pi * frame / 47)
                ),
                np.rint(
                    9000 * np.sin(2 * np.pi * frame / 157 + 0.4)
                ),
            ),
            axis=1,
        ).astype(np.int16)

    def test_independent_decode_is_deterministic(self) -> None:
        source = self._stereo()
        encoded = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=48,
            half_window=256,
            band_count=16,
        )
        decoded = decode_lapped_stream(encoded.payload)
        repeated = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=48,
            half_window=256,
            band_count=16,
        )

        np.testing.assert_array_equal(
            decoded.samples,
            encoded.reconstruction,
        )
        self.assertEqual(encoded.payload, repeated.payload)
        self.assertEqual(decoded.samples.shape, source.shape)
        self.assertEqual(decoded.sample_rate, 48000)
        self.assertGreater(encoded.report["snr_db"], 10.0)
        self.assertIn("bounded sparse", encoded.report["entropy_backend"])

    def test_zlib_comparator_reconstructs_identically(self) -> None:
        source = self._stereo(2048)
        bounded = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=32,
            half_window=256,
            band_count=16,
            entropy_backend="bounded",
        )
        zlib_comparator = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=32,
            half_window=256,
            band_count=16,
            entropy_backend="zlib",
        )

        np.testing.assert_array_equal(
            bounded.reconstruction,
            zlib_comparator.reconstruction,
        )
        self.assertNotEqual(bounded.payload, zlib_comparator.payload)

    def test_adaptive_density_uses_one_average_budget(self) -> None:
        source = self._stereo(4096)
        encoded = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=32,
            half_window=256,
            band_count=16,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="adaptive",
        )
        decoded = decode_lapped_stream(encoded.payload)

        np.testing.assert_array_equal(
            decoded.samples,
            encoded.reconstruction,
        )
        self.assertEqual(encoded.report["density_backend"], "adaptive")
        self.assertLess(
            encoded.report["selected_count_min"],
            encoded.report["selected_count_max"],
        )

    def test_more_coefficients_improve_the_sanity_metric(self) -> None:
        source = self._stereo(2048)
        sparse = encode_lapped_stream(
            source,
            44100,
            coefficients_per_frame=8,
            half_window=128,
            band_count=12,
        )
        dense = encode_lapped_stream(
            source,
            44100,
            coefficients_per_frame=48,
            half_window=128,
            band_count=12,
        )

        self.assertGreater(
            dense.report["snr_db"],
            sparse.report["snr_db"],
        )
        self.assertGreater(
            dense.report["stream_bytes"],
            sparse.report["stream_bytes"],
        )

    def test_corruption_and_bounds_are_rejected(self) -> None:
        source = self._stereo(1024)
        encoded = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=16,
            half_window=128,
            band_count=12,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(ValueError):
            decode_lapped_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            encode_lapped_stream(
                source,
                48000,
                coefficients_per_frame=129,
                half_window=128,
                band_count=12,
            )


if __name__ == "__main__":
    unittest.main()
