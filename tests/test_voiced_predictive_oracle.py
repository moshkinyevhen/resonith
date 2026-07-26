from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.voiced_predictive_oracle import (  # noqa: E402
    analyze_voiced_predictive_source,
    decode_voiced_predictive_stream,
    encode_voiced_predictive_analysis,
)


class VoicedPredictiveOracleTests(unittest.TestCase):
    @staticmethod
    def _voiced(sample_count: int = 8192) -> np.ndarray:
        period = 80
        phase = np.arange(period, dtype=np.float64)
        cycle = np.rint(
            11000.0 * np.sin(2.0 * np.pi * phase / period)
            + 2400.0 * np.sin(4.0 * np.pi * phase / period + 0.3)
        ).astype(np.int16)
        return np.resize(cycle, sample_count).astype(np.int16)

    def test_complete_stream_uses_independent_bounded_decode(self) -> None:
        source = self._voiced()
        analysis = analyze_voiced_predictive_source(
            source,
            16000,
            block_size=512,
        )
        encoded = encode_voiced_predictive_analysis(
            analysis,
            coefficients_per_frame=48,
        )
        sample_rate, decoded = decode_voiced_predictive_stream(encoded.payload)

        self.assertEqual(sample_rate, 16000)
        np.testing.assert_array_equal(decoded, encoded.reconstruction)
        self.assertGreater(encoded.report["voiced_block_count"], 0)
        self.assertGreater(encoded.report["parameter_envelope_bytes"], 0)
        self.assertEqual(decoded.shape, source.shape)

    def test_stream_corruption_and_configuration_are_rejected(self) -> None:
        source = self._voiced(2048)
        analysis = analyze_voiced_predictive_source(source, 16000)
        encoded = encode_voiced_predictive_analysis(
            analysis,
            coefficients_per_frame=32,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_voiced_predictive_stream(bytes(corrupted))
        with self.assertRaisesRegex(TypeError, "mono int16"):
            analyze_voiced_predictive_source(
                source.reshape(-1, 1),
                16000,
            )
        with self.assertRaisesRegex(ValueError, "block size"):
            analyze_voiced_predictive_source(
                source,
                16000,
                block_size=64,
            )


if __name__ == "__main__":
    unittest.main()
