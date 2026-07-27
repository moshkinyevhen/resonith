"""Exact semantic-free partial-spectrum dictionary tests."""

from __future__ import annotations

import unittest

import numpy as np

from maf_p0.partial_spectrum_orbit import (
    decode_partial_spectrum_orbit,
    encode_partial_spectrum_orbit,
    reversible_multiband_analysis,
    reversible_multiband_synthesis,
)


class PartialSpectrumOrbitTests(unittest.TestCase):
    def test_reversible_multiband_round_trip(self) -> None:
        generator = np.random.default_rng(145)
        source = generator.integers(
            -32768,
            32768,
            4099,
            dtype=np.int16,
        )
        bands, _ = reversible_multiband_analysis(source, 4)
        restored = reversible_multiband_synthesis(bands, source.size)
        np.testing.assert_array_equal(restored, source)

    def test_repeated_partial_band_beats_multiband_truth(self) -> None:
        levels = 3
        frame_count = 32768
        generator = np.random.default_rng(0x5231_3435)
        low = generator.integers(-400, 401, frame_count // 8, dtype=np.int64)
        detail3 = generator.integers(
            -80,
            81,
            frame_count // 8,
            dtype=np.int64,
        )
        detail2 = generator.integers(
            -80,
            81,
            frame_count // 4,
            dtype=np.int64,
        )
        phase = np.arange(64, dtype=np.float64)
        basis = np.rint(
            1800.0 * np.sin(2.0 * np.pi * 7.0 * phase / 64.0)
        ).astype(np.int64)
        gains = (32768, 24576, -32768, 16384) * 64
        detail1_blocks = []
        for block_index, gain in enumerate(gains):
            shifted = np.roll(basis, (7 * block_index) % basis.size)
            product = shifted * gain
            detail1_blocks.append(
                np.where(
                    product >= 0,
                    (product + 16384) // 32768,
                    -((-product + 16384) // 32768),
                )
            )
        detail1 = np.concatenate(detail1_blocks)
        source = reversible_multiband_synthesis(
            (low, detail3, detail2, detail1),
            frame_count,
        )
        self.assertLessEqual(int(np.max(np.abs(source))), 32767)
        pcm = source.astype(np.int16)[:, None]
        candidate = encode_partial_spectrum_orbit(
            pcm,
            levels=levels,
            block_samples=64,
            truth_block_sizes=(1024,),
            maximum_normalized_error=1.0e-6,
        )
        self.assertEqual(
            candidate.report["selected"],
            "partial-spectrum-dictionary",
        )
        self.assertLess(
            candidate.report["dictionary_bytes"],
            candidate.report["multiband_truth_bytes"],
        )
        np.testing.assert_array_equal(
            decode_partial_spectrum_orbit(candidate.payload),
            source,
        )

    def test_checksum_failure_is_rejected(self) -> None:
        source = np.zeros((1024, 1), dtype=np.int16)
        candidate = encode_partial_spectrum_orbit(
            source,
            levels=2,
            block_samples=64,
            truth_block_sizes=(1024,),
        )
        damaged = bytearray(candidate.payload)
        damaged[-5] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_partial_spectrum_orbit(bytes(damaged))


if __name__ == "__main__":
    unittest.main()
