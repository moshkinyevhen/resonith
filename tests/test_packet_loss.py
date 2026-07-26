from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.lpc_oracle import (  # noqa: E402
    decode_lpc_liftpack_block,
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
    index_lpc_liftpack_blocks,
)
from maf_p0.multichannel import encode_main0_independent_rdo  # noqa: E402
from maf_p0.packet_loss import simulate_aligned_packet_loss  # noqa: E402


class PacketLossTests(unittest.TestCase):
    @staticmethod
    def _stereo(frame_count: int = 2048) -> np.ndarray:
        frame = np.arange(frame_count, dtype=np.float64)
        return np.stack(
            (
                np.rint(14000 * np.sin(2 * np.pi * frame / 97)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 151 + 0.2)),
            ),
            axis=1,
        ).astype(np.int16)

    def test_single_block_decode_matches_full_rsl2(self) -> None:
        source = self._stereo()[:, 0]
        payload, _ = encode_lpc_liftpack_oracle(
            source,
            block_size=256,
        )
        full = decode_lpc_liftpack_oracle(payload)
        index = index_lpc_liftpack_blocks(payload)
        for block in (0, 3, len(index) - 1):
            info, decoded = decode_lpc_liftpack_block(payload, block)
            start = info.sample_offset
            end = start + info.sample_count
            np.testing.assert_array_equal(decoded, full[start:end])

    def test_loss_is_exactly_bounded_to_declared_blocks(self) -> None:
        source = self._stereo()
        encoded = encode_main0_independent_rdo(
            source,
            48000,
            innovation_step=1,
            residual_block_sizes=(256,),
        )
        result = simulate_aligned_packet_loss(
            encoded.payload,
            lost_blocks=(2, 3),
        )

        np.testing.assert_array_equal(
            result.reconstruction[:512],
            result.truth[:512],
        )
        self.assertFalse(
            np.array_equal(
                result.reconstruction[512:1024],
                result.truth[512:1024],
            )
        )
        np.testing.assert_array_equal(
            result.reconstruction[1024:],
            result.truth[1024:],
        )
        self.assertTrue(result.report["exact_outside_loss"])
        self.assertTrue(
            result.report["all_recoverable_next_blocks_exact"]
        )
        self.assertEqual(result.report["affected_frames"], 512)
        self.assertGreater(result.report["lost_payload_bytes"], 0)

    def test_first_and_invalid_loss_indices(self) -> None:
        encoded = encode_main0_independent_rdo(
            self._stereo(1024),
            48000,
            innovation_step=32,
            residual_block_sizes=(256,),
        )
        first = simulate_aligned_packet_loss(
            encoded.payload,
            lost_blocks=(0,),
        )
        self.assertTrue(np.all(first.reconstruction[:256] == 0))
        self.assertTrue(first.report["exact_outside_loss"])

        with self.assertRaisesRegex(ValueError, "exceeds"):
            simulate_aligned_packet_loss(
                encoded.payload,
                lost_blocks=(99,),
            )


if __name__ == "__main__":
    unittest.main()
