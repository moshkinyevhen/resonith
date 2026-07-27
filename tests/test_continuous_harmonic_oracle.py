from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.continuous_harmonic_oracle import (  # noqa: E402
    analyze_continuous_harmonic_field,
    analyze_continuous_harmonic_source,
    decode_continuous_harmonic_field,
    decode_continuous_harmonic_stream,
    encode_continuous_harmonic_field_analysis,
    encode_continuous_harmonic_analysis,
)


class ContinuousHarmonicOracleTests(unittest.TestCase):
    @staticmethod
    def _voiced(sample_count: int = 12288) -> np.ndarray:
        sample = np.arange(sample_count, dtype=np.float64)
        phase = 2.0 * np.pi * (
            sample / 83.0 + 0.5 * sample * sample / (sample_count * 900.0)
        )
        envelope = 0.75 + 0.2 * sample / sample_count
        return np.rint(
            envelope
            * (
                10500.0 * np.sin(phase + 0.3)
                + 2300.0 * np.sin(2.0 * phase - 0.2)
            )
        ).astype(np.int16)

    def test_continuous_trajectory_round_trips_independent_decode(
        self,
    ) -> None:
        source = self._voiced()
        analysis = analyze_continuous_harmonic_source(
            source,
            16000,
            state_size=4096,
            harmonic_count=2,
        )
        encoded = encode_continuous_harmonic_analysis(
            analysis,
            coefficients_per_frame=40,
        )
        sample_rate, decoded = decode_continuous_harmonic_stream(
            encoded.payload
        )

        self.assertEqual(sample_rate, 16000)
        np.testing.assert_array_equal(decoded, encoded.reconstruction)
        self.assertGreater(encoded.report["active_state_count"], 0)
        self.assertGreater(encoded.report["run_count"], 0)
        self.assertEqual(encoded.report["harmonic_count"], 2)
        self.assertGreater(encoded.report["basis_envelope_bytes"], 0)

    def test_stereo_field_preserves_joint_residual_and_decode(self) -> None:
        left = self._voiced(8192)
        right = np.roll(left, 17)
        source = np.column_stack((left, right)).astype(np.int16)
        analysis = analyze_continuous_harmonic_field(
            source,
            16000,
            state_size=2048,
            harmonic_count=1,
        )
        encoded = encode_continuous_harmonic_field_analysis(
            analysis,
            coefficients_per_frame=36,
        )
        sample_rate, decoded = decode_continuous_harmonic_field(
            encoded.payload
        )

        self.assertEqual(sample_rate, 16000)
        np.testing.assert_array_equal(decoded, encoded.reconstruction)
        self.assertEqual(encoded.report["channel_count"], 2)
        self.assertGreater(encoded.report["active_state_count"], 0)

    def test_corruption_and_profile_bounds_are_rejected(self) -> None:
        source = self._voiced(4096)
        analysis = analyze_continuous_harmonic_source(
            source,
            16000,
            state_size=2048,
            harmonic_count=2,
        )
        encoded = encode_continuous_harmonic_analysis(
            analysis,
            coefficients_per_frame=32,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_continuous_harmonic_stream(bytes(corrupted))
        with self.assertRaisesRegex(TypeError, "mono int16"):
            analyze_continuous_harmonic_source(
                source.reshape(-1, 1),
                16000,
                state_size=2048,
                harmonic_count=2,
            )
        with self.assertRaisesRegex(ValueError, "count"):
            analyze_continuous_harmonic_source(
                source,
                16000,
                state_size=2048,
                harmonic_count=9,
            )
        with self.assertRaisesRegex(TypeError, "1-8 channel"):
            analyze_continuous_harmonic_field(
                source,
                16000,
                state_size=2048,
                harmonic_count=1,
            )


if __name__ == "__main__":
    unittest.main()
