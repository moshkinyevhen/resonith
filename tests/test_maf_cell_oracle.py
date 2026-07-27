from __future__ import annotations

import unittest

import numpy as np

from maf_p0.lapped_oracle import analyze_lapped_source
from maf_p0.maf_cell_oracle import (
    CellMode,
    decode_maf_cell_stream,
    encode_maf_cell_analysis,
)


class MafCellOracleTests(unittest.TestCase):
    @staticmethod
    def _analysis(*, stereo: bool = False):
        sample_rate = 16000
        time = np.arange(4096, dtype=np.float64)
        mono = (
            9000.0 * np.sin(2.0 * np.pi * 173.0 * time / sample_rate)
            + 2400.0 * np.sin(2.0 * np.pi * 346.0 * time / sample_rate)
        )
        mono[2048] += 14000.0
        first = np.clip(np.rint(mono), -32768, 32767).astype(np.int16)
        if stereo:
            second = np.clip(
                np.rint(0.75 * mono),
                -32768,
                32767,
            ).astype(np.int16)
            source = np.column_stack((first, second))
        else:
            source = first[:, None]
        return analyze_lapped_source(
            source,
            sample_rate,
            half_window=64,
            band_count=8,
        )

    def test_event_stream_is_deterministic_and_independently_decodable(
        self,
    ) -> None:
        analysis = self._analysis()
        first = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=8192,
        )
        second = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=8192,
        )
        decoded = decode_maf_cell_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        np.testing.assert_array_equal(first.reconstruction, decoded.samples)
        self.assertEqual(decoded.samples.shape, analysis.samples.shape)
        self.assertGreater(first.report["basis_count"], 0)
        self.assertGreater(first.report["hold_cells"], 0)
        self.assertGreater(first.report["changed_cells"], 0)
        self.assertEqual(
            sum(first.report["mode_counts"].values()),
            first.report["changed_cells"],
        )

    def test_joint_channel_mode_is_available_to_the_rdo(self) -> None:
        analysis = self._analysis(stereo=True)
        encoded = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=1024,
        )
        decoded = decode_maf_cell_stream(encoded.payload)

        np.testing.assert_array_equal(encoded.reconstruction, decoded.samples)
        self.assertGreater(
            encoded.report["mode_counts"][CellMode.CHANNEL_SET.name],
            0,
        )

    def test_learned_dictionary_is_paid_once_and_referenced(self) -> None:
        analysis = self._analysis()
        encoded = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=8192,
            basis_search_limit=4,
            dictionary_bases_per_band=2,
            dictionary_pulses_per_basis=12,
        )
        decoded = decode_maf_cell_stream(encoded.payload)

        np.testing.assert_array_equal(encoded.reconstruction, decoded.samples)
        self.assertGreater(encoded.report["dictionary_basis_count"], 0)
        self.assertGreater(encoded.report["dictionary_section_bytes"], 0)
        self.assertGreater(
            encoded.report["mode_counts"][CellMode.BASIS_REF.name]
            + encoded.report["mode_counts"][CellMode.BASIS_UPDATE.name],
            0,
        )

    def test_truncation_corruption_and_bounds_are_rejected(self) -> None:
        analysis = self._analysis()
        encoded = encode_maf_cell_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            rate_lambda_q20=512,
        )
        with self.assertRaises(ValueError):
            decode_maf_cell_stream(encoded.payload[:-1])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 0x40
        with self.assertRaises(ValueError):
            decode_maf_cell_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            encode_maf_cell_analysis(
                analysis,
                maximum_pulses_per_frame=0,
                rate_lambda_q20=512,
            )
        with self.assertRaises(ValueError):
            encode_maf_cell_analysis(
                analysis,
                maximum_pulses_per_frame=12,
                rate_lambda_q20=-1,
            )


if __name__ == "__main__":
    unittest.main()
