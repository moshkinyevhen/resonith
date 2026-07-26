from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REFERENCE_ROOT = Path(__file__).resolve().parents[1] / "reference"
sys.path.insert(0, str(REFERENCE_ROOT))

from maf_p0.segmentation import segment_acoustic_states  # noqa: E402


def sine(sample_count: int, period: float, amplitude: float) -> np.ndarray:
    position = np.arange(sample_count, dtype=np.float64)
    return np.rint(
        amplitude * np.sin(2.0 * np.pi * position / period)
    ).astype(np.int16)


class AcousticSegmentationTests(unittest.TestCase):
    def test_known_timbre_change_is_found_deterministically(self) -> None:
        first = sine(24576, 240.0, 9000.0)
        second = sine(24576, 73.0, 15000.0)
        source = np.concatenate((first, second))

        first_result = segment_acoustic_states(
            source,
            hop_samples=512,
            minimum_segment_samples=4096,
            maximum_segment_samples=32768,
            change_penalty=30.0,
        )
        second_result = segment_acoustic_states(
            source,
            hop_samples=512,
            minimum_segment_samples=4096,
            maximum_segment_samples=32768,
            change_penalty=30.0,
        )
        self.assertEqual(first_result.intervals, second_result.intervals)
        boundaries = [start for start, _ in first_result.intervals[1:]]
        self.assertTrue(
            any(abs(boundary - first.size) <= 1024 for boundary in boundaries),
            boundaries,
        )

    def test_partition_is_complete_and_profile_bounded(self) -> None:
        rng = np.random.default_rng(0x53544154)
        source = rng.integers(
            -10000,
            10001,
            size=65536,
            dtype=np.int16,
        )
        result = segment_acoustic_states(
            source,
            hop_samples=512,
            minimum_segment_samples=4096,
            maximum_segment_samples=16384,
            change_penalty=80.0,
        )
        self.assertEqual(result.intervals[0][0], 0)
        self.assertEqual(result.intervals[-1][1], source.size)
        for left, right in zip(
            result.intervals[:-1],
            result.intervals[1:],
            strict=True,
        ):
            self.assertEqual(left[1], right[0])
        self.assertTrue(
            all(end - start <= 16384 for start, end in result.intervals)
        )

    def test_invalid_analysis_bounds_are_rejected(self) -> None:
        source = np.zeros(8192, dtype=np.int16)
        with self.assertRaises(ValueError):
            segment_acoustic_states(source, hop_samples=128)
        with self.assertRaises(ValueError):
            segment_acoustic_states(
                source,
                minimum_segment_samples=1024,
                maximum_segment_samples=512,
            )


if __name__ == "__main__":
    unittest.main()
