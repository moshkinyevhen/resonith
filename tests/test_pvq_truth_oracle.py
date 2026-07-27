from __future__ import annotations

import unittest

import numpy as np

from maf_p0.lapped_oracle import analyze_lapped_source
from maf_p0.pvq_truth_oracle import (
    decode_pvq_truth_stream,
    encode_pvq_truth_analysis,
)


class PvqTruthOracleTests(unittest.TestCase):
    def _analysis(self):
        sample_rate = 16000
        frame = np.arange(4096, dtype=np.float64)
        signal = (
            9000.0 * np.sin(2.0 * np.pi * 173.0 * frame / sample_rate)
            + 3500.0 * np.sin(2.0 * np.pi * 421.0 * frame / sample_rate)
        )
        signal[::257] += 12000.0
        source = np.clip(
            np.rint(signal),
            -32768,
            32767,
        ).astype(np.int16)[:, None]
        return source, analyze_lapped_source(
            source,
            sample_rate,
            half_window=64,
            band_count=8,
        )

    def test_complete_stream_is_deterministic_and_independently_decoded(
        self,
    ) -> None:
        source, analysis = self._analysis()
        first = encode_pvq_truth_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            corrections_per_frame=16,
        )
        second = encode_pvq_truth_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            corrections_per_frame=16,
        )
        decoded = decode_pvq_truth_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        np.testing.assert_array_equal(first.reconstruction, decoded.samples)
        self.assertEqual(decoded.samples.shape, source.shape)
        self.assertEqual(decoded.corrections_per_frame, 16)
        self.assertLess(
            first.report["max_abs_error"],
            32768,
        )

    def test_more_truth_coefficients_do_not_reduce_snr(self) -> None:
        _, analysis = self._analysis()
        sparse = encode_pvq_truth_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            corrections_per_frame=8,
        )
        dense = encode_pvq_truth_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            corrections_per_frame=32,
        )
        self.assertGreaterEqual(
            dense.report["snr_db"],
            sparse.report["snr_db"],
        )

    def test_corruption_and_bounds_are_rejected(self) -> None:
        _, analysis = self._analysis()
        encoded = encode_pvq_truth_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            corrections_per_frame=16,
        )
        with self.assertRaises(ValueError):
            decode_pvq_truth_stream(encoded.payload[:-1])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 0x40
        with self.assertRaises(ValueError):
            decode_pvq_truth_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            encode_pvq_truth_analysis(
                analysis,
                maximum_pulses_per_frame=12,
                corrections_per_frame=0,
            )


if __name__ == "__main__":
    unittest.main()
