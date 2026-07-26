from __future__ import annotations

from pathlib import Path
import hashlib
import sys
import unittest

import numpy as np


REFERENCE_ROOT = Path(__file__).resolve().parents[1] / "reference"
sys.path.insert(0, str(REFERENCE_ROOT))

from maf_p0.residual import decode_liftpack, encode_liftpack  # noqa: E402


class LiftPackTests(unittest.TestCase):
    def test_structured_and_hostile_blocks_round_trip_exactly(self) -> None:
        rng = np.random.default_rng(0x5245534F)
        signals = [
            np.zeros(4097, dtype=np.int32),
            np.arange(-2048, 2049, dtype=np.int32),
            np.square(np.arange(-64, 65, dtype=np.int32)),
            rng.integers(-65535, 65536, size=5003, dtype=np.int32),
        ]
        for source in signals:
            with self.subTest(sample_count=source.size):
                packet = encode_liftpack(source, block_size=256)
                restored = decode_liftpack(
                    packet.payload,
                    expected_count=source.size,
                )
                np.testing.assert_array_equal(restored, source)
                self.assertEqual(
                    sum(packet.report["transform_counts"].values()),
                    packet.report["block_count"],
                )

    def test_encoder_uses_actual_transform_and_entropy_cost(self) -> None:
        ramp = np.arange(8192, dtype=np.int32)
        packet = encode_liftpack(ramp, block_size=1024)
        predictive_blocks = (
            packet.report["transform_counts"]["delta1"]
            + packet.report["transform_counts"]["delta2"]
        )
        self.assertGreater(predictive_blocks, 0)
        self.assertGreater(packet.report["entropy_counts"]["rice"], 0)
        self.assertLess(len(packet.payload), ramp.nbytes // 20)

    def test_checksum_truncation_and_expected_count_are_enforced(self) -> None:
        source = np.arange(2048, dtype=np.int32)
        packet = encode_liftpack(source)

        corrupted = bytearray(packet.payload)
        corrupted[len(corrupted) // 2] ^= 0x20
        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_liftpack(bytes(corrupted))
        with self.assertRaises(ValueError):
            decode_liftpack(packet.payload[:-1])
        with self.assertRaisesRegex(ValueError, "sample count mismatch"):
            decode_liftpack(packet.payload, expected_count=source.size + 1)

    def test_input_and_profile_bounds_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            encode_liftpack(np.zeros(32, dtype=np.float64))
        with self.assertRaises(ValueError):
            encode_liftpack(np.zeros(32, dtype=np.int16), block_size=8)
        with self.assertRaises(ValueError):
            encode_liftpack(
                np.asarray([1 << 31], dtype=np.int64),
            )
        with self.assertRaises(ValueError):
            encode_liftpack(
                np.asarray([np.iinfo(np.int64).min], dtype=np.int64),
            )

    def test_canonical_stream_has_a_frozen_conformance_hash(self) -> None:
        source = np.concatenate(
            (
                np.zeros(64, dtype=np.int32),
                np.arange(-32, 32, dtype=np.int32),
                np.tile(
                    np.asarray([32767, -32768], dtype=np.int32),
                    32,
                ),
            )
        )
        packet = encode_liftpack(source, block_size=64)
        self.assertEqual(
            hashlib.sha256(packet.payload).hexdigest(),
            "6d58812162388dfe58c2b602372bf144d36af00f7a19cb39250e0d920609fee6",
        )


if __name__ == "__main__":
    unittest.main()
