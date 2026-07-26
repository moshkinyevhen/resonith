from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.lpc_oracle import encode_lpc_liftpack_oracle  # noqa: E402
from maf_p0.multichannel import (
    decode_main0_independent_stream,
    encode_main0_independent_rdo,
    pack_main0_independent_stream,
)  # noqa: E402
from maf_p0.rsc1 import (  # noqa: E402
    RSC1Section,
    pack_rsc1,
    parse_rsc1,
)
from maf_p0.stream_sections import (  # noqa: E402
    StreamConfig,
    pack_conf,
)


class IndependentChannelTests(unittest.TestCase):
    @staticmethod
    def _stereo(frames: int = 1536) -> np.ndarray:
        positions = np.arange(frames, dtype=np.int64)
        left = (
            9000 * np.sin(positions * 2.0 * np.pi / 97.0)
        ).round().astype(np.int16)
        right = (
            7000 * np.sin(positions * 2.0 * np.pi / 131.0)
            + ((positions % 113) == 0) * 4000
        ).round().astype(np.int16)
        return np.stack((left, right), axis=1)

    def test_lossless_rdo_round_trip(self) -> None:
        source = self._stereo()
        encoded = encode_main0_independent_rdo(
            source,
            48000,
            innovation_step=1,
            residual_block_sizes=(256, 512),
        )
        decoded = decode_main0_independent_stream(encoded.payload)

        self.assertTrue(np.array_equal(decoded.samples, source))
        self.assertEqual(decoded.sample_rate, 48000)
        self.assertEqual(encoded.report["channel_count"], 2)
        self.assertEqual(encoded.report["frame_count"], source.shape[0])
        self.assertEqual(encoded.report["max_abs_error"], 0)
        self.assertIn(encoded.report["residual_block_size"], (256, 512))

    def test_lossy_stream_matches_quantized_reconstruction(self) -> None:
        source = self._stereo(1024)
        encoded = encode_main0_independent_rdo(
            source,
            44100,
            innovation_step=32,
            residual_block_sizes=(256,),
        )
        decoded = decode_main0_independent_stream(encoded.payload)

        self.assertTrue(
            np.array_equal(decoded.samples, encoded.reconstruction)
        )
        self.assertLessEqual(
            int(np.max(np.abs(
                source.astype(np.int32)
                - decoded.samples.astype(np.int32)
            ))),
            16,
        )

    def test_rejects_mismatched_channel_partition(self) -> None:
        source = self._stereo(1024).astype(np.int64)
        left, _ = encode_lpc_liftpack_oracle(
            source[:, 0],
            block_size=256,
        )
        right, _ = encode_lpc_liftpack_oracle(
            source[:, 1],
            block_size=512,
        )
        payload = pack_rsc1(
            [
                RSC1Section(
                    "CONF",
                    pack_conf(StreamConfig(1024, 1, 2)),
                ),
                RSC1Section("RSL2", left, instance_id=0),
                RSC1Section("RSL2", right, instance_id=1),
            ],
            profile=0,
            level=0,
            timebase_hz=48000,
        )

        with self.assertRaisesRegex(ValueError, "partitions differ"):
            decode_main0_independent_stream(payload)

    def test_rejects_missing_channel_instance(self) -> None:
        source = self._stereo(128).astype(np.int64)
        payload = pack_main0_independent_stream(
            sample_rate=48000,
            innovation_q=source,
            innovation_step=1,
            residual_block_size=128,
        )
        info = parse_rsc1(payload)
        damaged = pack_rsc1(
            [
                section
                for section in info.sections
                if not (
                    bytes(section.type_code) == b"RSL2"
                    and section.instance_id == 1
                )
            ],
            profile=info.profile,
            level=info.level,
            timebase_hz=info.timebase_hz,
        )

        with self.assertRaisesRegex(ValueError, "RSL2 instances"):
            decode_main0_independent_stream(damaged)


if __name__ == "__main__":
    unittest.main()
