from __future__ import annotations

import unittest

import numpy as np

from maf_p0.maf_source_filter_oracle import (
    analyze_maf_source_filter_source,
    decode_maf_source_filter_stream,
    encode_maf_source_filter_analysis,
)


class MafSourceFilterOracleTests(unittest.TestCase):
    @staticmethod
    def _source() -> tuple[int, np.ndarray]:
        sample_rate = 16000
        time = np.arange(2048, dtype=np.float64)
        pitch = 125.0 + 8.0 * time / time.size
        phase = np.cumsum(2.0 * np.pi * pitch / sample_rate)
        excitation = (
            7500.0 * np.sin(phase)
            + 2600.0 * np.sin(2.0 * phase)
            + 900.0 * np.sin(3.0 * phase)
        )
        source = np.clip(
            np.rint(excitation),
            -32768,
            32767,
        ).astype(np.int16)
        return sample_rate, source

    def test_persistent_laws_preserve_exact_analysis_identity(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            parameter_lambda=4.0,
            half_window=64,
            band_count=8,
        )

        self.assertEqual(analysis.source.shape, analysis.innovation.shape)
        self.assertEqual(len(analysis.pitch_laws), 8)
        self.assertEqual(len(analysis.filter_laws), 8)
        self.assertGreater(
            analysis.parameter_report["pitch_hold_count"]
            + analysis.parameter_report["filter_hold_count"],
            0,
        )

    def test_complete_source_filter_stream_round_trips(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            parameter_lambda=4.0,
            half_window=64,
            band_count=8,
        )
        first = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        second = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        decoded_rate, decoded = decode_maf_source_filter_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(first.reconstruction, decoded)
        self.assertGreater(first.report["parameter_event_count"], 0)
        self.assertGreater(first.report["maf_cell"]["basis_count"], 0)

    def test_adaptive_excitation_stream_round_trips(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=6,
            parameter_lambda=0.0,
            half_window=64,
            band_count=8,
        )
        encoded = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            excitation_backend="epvq",
            excitation_subframe_size=64,
            excitation_pulses=4,
        )
        decoded_rate, decoded = decode_maf_source_filter_stream(
            encoded.payload
        )

        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(encoded.reconstruction, decoded)
        self.assertEqual(encoded.report["excitation_backend"], "epvq")
        self.assertGreater(
            encoded.report["maf_cell"]["pitch_update_count"],
            0,
        )

    def test_corruption_and_invalid_parameters_are_rejected(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            half_window=64,
            band_count=8,
        )
        encoded = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        with self.assertRaises(ValueError):
            decode_maf_source_filter_stream(encoded.payload[:-1])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 0x20
        with self.assertRaises(ValueError):
            decode_maf_source_filter_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            analyze_maf_source_filter_source(
                source,
                sample_rate,
                filter_order=17,
            )


if __name__ == "__main__":
    unittest.main()
