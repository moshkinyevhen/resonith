from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.transient import (  # noqa: E402
    TransientEvent,
    decode_transient_events,
    detect_transients,
    encode_transient_events,
    haar_lift_forward,
    haar_lift_inverse,
)


class TransientTests(unittest.TestCase):
    def test_integer_haar_round_trip_is_exact(self) -> None:
        generator = np.random.default_rng(20260726)
        for length in (1, 2, 16, 256, 1024):
            source = generator.integers(
                -32768,
                32768,
                size=length,
                dtype=np.int16,
            )
            coefficients = haar_lift_forward(source)
            restored = haar_lift_inverse(coefficients)
            np.testing.assert_array_equal(restored, source.astype(np.int64))

    def test_detector_finds_isolated_attack(self) -> None:
        samples = np.zeros(4096, dtype=np.int16)
        samples[2000:2004] = np.array([28000, -24000, 12000, 0], dtype=np.int16)
        events = detect_transients(samples, window_size=256, pre_roll=32)
        self.assertEqual(len(events), 1)
        self.assertLessEqual(events[0].start, 2000)
        self.assertGreater(events[0].end, 2000)

    def test_transient_transport_is_local_and_lossless(self) -> None:
        samples = np.zeros(2048, dtype=np.int16)
        samples[700:708] = np.array(
            [3000, 15000, 28000, -18000, -9000, 4000, 1000, 0],
            dtype=np.int16,
        )
        event = TransientEvent(672, 256)
        packet = encode_transient_events(samples, [event], quantization_step=1)
        prediction, coverage = decode_transient_events(packet, samples.size)
        np.testing.assert_array_equal(
            prediction[event.start : event.end],
            samples[event.start : event.end],
        )
        self.assertFalse(np.any(prediction[: event.start]))
        self.assertFalse(np.any(prediction[event.end :]))
        self.assertFalse(np.any(coverage[: event.start]))
        self.assertFalse(np.any(coverage[event.end :]))

    def test_overlap_and_trailing_coefficients_are_rejected(self) -> None:
        samples = np.zeros(1024, dtype=np.int16)
        with self.assertRaises(ValueError):
            encode_transient_events(
                samples,
                [TransientEvent(100, 200), TransientEvent(250, 200)],
            )


if __name__ == "__main__":
    unittest.main()
