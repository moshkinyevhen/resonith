from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.listening_anchor import lowpass_anchor  # noqa: E402


class ListeningAnchorTests(unittest.TestCase):
    def test_lowpass_anchor_is_deterministic_and_attenuates_high_band(self) -> None:
        sample_rate = 48000
        frame = np.arange(sample_rate, dtype=np.float64)
        source = np.rint(
            8000.0 * np.sin(2.0 * np.pi * 1000.0 * frame / sample_rate)
            + 8000.0 * np.sin(2.0 * np.pi * 10000.0 * frame / sample_rate)
        ).astype(np.int16)
        first = lowpass_anchor(source, sample_rate)
        second = lowpass_anchor(source, sample_rate)
        np.testing.assert_array_equal(first, second)
        spectrum = np.abs(np.fft.rfft(first.astype(np.float64)))
        frequencies = np.fft.rfftfreq(first.size, 1.0 / sample_rate)
        low = spectrum[np.argmin(np.abs(frequencies - 1000.0))]
        high = spectrum[np.argmin(np.abs(frequencies - 10000.0))]
        self.assertGreater(low, 100.0 * high)

    def test_invalid_anchor_shapes_and_cutoffs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lowpass_anchor(np.zeros((2, 2, 2), dtype=np.int16), 48000)
        with self.assertRaises(ValueError):
            lowpass_anchor(np.zeros(16, dtype=np.float32), 48000)
        with self.assertRaises(ValueError):
            lowpass_anchor(
                np.zeros(16, dtype=np.int16),
                48000,
                cutoff_hz=24000.0,
            )


if __name__ == "__main__":
    unittest.main()
