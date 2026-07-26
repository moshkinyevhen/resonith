from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.harmonic_basis_oracle import (  # noqa: E402
    analyze_harmonic_basis_source,
    decode_harmonic_basis_stream,
    encode_harmonic_basis_analysis,
)


class HarmonicBasisOracleTests(unittest.TestCase):
    @staticmethod
    def _voiced(sample_count: int = 8192) -> np.ndarray:
        sample = np.arange(sample_count, dtype=np.float64)
        return np.rint(
            11000.0 * np.sin(2.0 * np.pi * sample / 80.0)
            + 2500.0 * np.sin(4.0 * np.pi * sample / 80.0 + 0.2)
        ).astype(np.int16)

    def test_nonrecursive_basis_round_trips_through_independent_decode(
        self,
    ) -> None:
        source = self._voiced()
        analysis = analyze_harmonic_basis_source(
            source,
            16000,
            block_size=1024,
            harmonic_count=4,
        )
        encoded = encode_harmonic_basis_analysis(
            analysis,
            coefficients_per_frame=40,
        )
        sample_rate, decoded = decode_harmonic_basis_stream(encoded.payload)

        self.assertEqual(sample_rate, 16000)
        np.testing.assert_array_equal(decoded, encoded.reconstruction)
        self.assertGreater(encoded.report["active_block_count"], 0)
        self.assertEqual(encoded.report["harmonic_count"], 4)
        self.assertGreater(encoded.report["basis_envelope_bytes"], 0)

    def test_corruption_and_profile_bounds_are_rejected(self) -> None:
        source = self._voiced(2048)
        analysis = analyze_harmonic_basis_source(
            source,
            16000,
            block_size=1024,
            harmonic_count=2,
        )
        encoded = encode_harmonic_basis_analysis(
            analysis,
            coefficients_per_frame=32,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_harmonic_basis_stream(bytes(corrupted))
        with self.assertRaisesRegex(TypeError, "mono int16"):
            analyze_harmonic_basis_source(
                source.reshape(-1, 1),
                16000,
                block_size=1024,
                harmonic_count=2,
            )
        with self.assertRaisesRegex(ValueError, "count"):
            analyze_harmonic_basis_source(
                source,
                16000,
                block_size=1024,
                harmonic_count=9,
            )


if __name__ == "__main__":
    unittest.main()
