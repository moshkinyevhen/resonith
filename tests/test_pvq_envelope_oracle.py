from __future__ import annotations

import unittest

import numpy as np

from maf_p0.lapped_oracle import analyze_lapped_source
from maf_p0.pvq_envelope_oracle import (
    _pvq_codebook_size,
    _rank_pvq,
    _unrank_pvq,
    decode_pvq_envelope_stream,
    encode_pvq_envelope_analysis,
)


class PvqEnvelopeOracleTests(unittest.TestCase):
    def test_enumerative_pvq_rank_is_bijective(self) -> None:
        for dimension in range(1, 6):
            for pulses in range(5):
                size = _pvq_codebook_size(dimension, pulses)
                vectors = set()
                for rank in range(size):
                    vector = _unrank_pvq(dimension, pulses, rank)
                    reranked, actual_pulses = _rank_pvq(vector)
                    self.assertEqual(reranked, rank)
                    self.assertEqual(actual_pulses, pulses)
                    vectors.add(tuple(int(value) for value in vector))
                self.assertEqual(len(vectors), size)

    def test_complete_stream_round_trips_independent_decode(self) -> None:
        sample_rate = 16000
        frame = np.arange(4096, dtype=np.float64)
        signal = (
            9000.0 * np.sin(2.0 * np.pi * 173.0 * frame / sample_rate)
            + 3500.0 * np.sin(2.0 * np.pi * 421.0 * frame / sample_rate)
        )
        signal[::257] += 12000.0
        samples = np.clip(np.rint(signal), -32768, 32767).astype(np.int16)
        source = samples[:, None]
        analysis = analyze_lapped_source(
            source,
            sample_rate,
            half_window=64,
            band_count=8,
        )
        first = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=14,
        )
        second = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=14,
        )
        decoded = decode_pvq_envelope_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        np.testing.assert_array_equal(first.reconstruction, decoded.samples)
        self.assertEqual(decoded.samples.shape, source.shape)
        self.assertEqual(decoded.sample_rate, sample_rate)
        self.assertEqual(decoded.maximum_pulses_per_frame, 14)
        self.assertEqual(
            first.report["logical_bits"],
            first.report["count_bits"]
            + first.report["gain_bits"]
            + first.report["shape_bits"],
        )

    def test_corruption_and_bounds_are_rejected(self) -> None:
        samples = np.arange(1024, dtype=np.int16)[:, None]
        analysis = analyze_lapped_source(
            samples,
            16000,
            half_window=64,
            band_count=8,
        )
        encoded = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=8,
        )
        with self.assertRaises(ValueError):
            decode_pvq_envelope_stream(encoded.payload[:-1])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 0x80
        with self.assertRaises(ValueError):
            decode_pvq_envelope_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            encode_pvq_envelope_analysis(
                analysis,
                maximum_pulses_per_frame=0,
            )

    def test_persistent_coarse_gain_is_explicit_and_deterministic(self) -> None:
        sample_rate = 16000
        frame = np.arange(8192, dtype=np.float64)
        envelope = np.where((frame // 512) % 3 == 1, 0.0, 1.0)
        signal = envelope * (
            10000.0 * np.sin(2.0 * np.pi * 211.0 * frame / sample_rate)
        )
        source = np.rint(signal).astype(np.int16)[:, None]
        analysis = analyze_lapped_source(
            source,
            sample_rate,
            half_window=64,
            band_count=8,
        )
        legacy = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=12,
        )
        explicit_legacy = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            gain_fraction_bits=8,
            persistent_gain_memory=False,
        )
        compact = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            gain_fraction_bits=4,
            persistent_gain_memory=True,
        )
        repeated = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            gain_fraction_bits=4,
            persistent_gain_memory=True,
        )
        decoded = decode_pvq_envelope_stream(compact.payload)

        self.assertEqual(legacy.payload, explicit_legacy.payload)
        self.assertEqual(compact.payload, repeated.payload)
        self.assertEqual(compact.report["stream_version"], 2)
        self.assertEqual(compact.report["gain_fraction_bits"], 4)
        self.assertTrue(compact.report["persistent_gain_memory"])
        np.testing.assert_array_equal(compact.reconstruction, decoded.samples)
        self.assertLess(
            compact.report["gain_bits"],
            legacy.report["gain_bits"],
        )
        with self.assertRaises(ValueError):
            encode_pvq_envelope_analysis(
                analysis,
                maximum_pulses_per_frame=12,
                gain_fraction_bits=9,
            )


if __name__ == "__main__":
    unittest.main()
