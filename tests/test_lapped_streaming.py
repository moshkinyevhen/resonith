from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.lapped_streaming import (  # noqa: E402
    decode_lapped_chained_packet_view,
    decode_lapped_packet_stream,
    decode_lapped_packet_view,
    encode_lapped_packet_stream,
    encode_lapped_chained_packet_stream,
    encode_lapped_compact_packet_stream,
    encode_lapped_transform_packet_stream,
    index_lapped_packet_stream,
)
from maf_p0.packet_loss import simulate_lapped_packet_loss  # noqa: E402


class LappedStreamingTests(unittest.TestCase):
    @staticmethod
    def _stereo(frame_count: int = 4096) -> np.ndarray:
        frame = np.arange(frame_count, dtype=np.float64)
        return np.stack(
            (
                np.rint(14000 * np.sin(2 * np.pi * frame / 97)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 151 + 0.2)),
            ),
            axis=1,
        ).astype(np.int16)

    def test_fixed_density_packets_match_monolithic_interior(self) -> None:
        source = self._stereo()
        packeted = encode_lapped_packet_stream(
            source,
            48000,
            coefficients_per_frame=32,
            packet_frames=1024,
            half_window=128,
            band_count=12,
            density_backend="fixed",
        )
        monolithic = encode_lapped_stream(
            source,
            48000,
            coefficients_per_frame=32,
            half_window=128,
            band_count=12,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="fixed",
        )

        np.testing.assert_array_equal(
            packeted.reconstruction,
            monolithic.reconstruction,
        )
        self.assertEqual(packeted.report["packet_count"], 4)

    def test_adaptive_packets_round_trip_and_detect_corruption(self) -> None:
        source = self._stereo(3072)
        encoded = encode_lapped_packet_stream(
            source,
            44100,
            coefficients_per_frame=24,
            packet_frames=1024,
            half_window=128,
            band_count=12,
            density_backend="adaptive",
        )
        decoded = decode_lapped_packet_stream(encoded.payload)

        np.testing.assert_array_equal(
            decoded.samples,
            encoded.reconstruction,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(ValueError):
            decode_lapped_packet_stream(bytes(corrupted))

    def test_packet_alignment_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            encode_lapped_packet_stream(
                self._stereo(1024),
                48000,
                coefficients_per_frame=16,
                packet_frames=1000,
                half_window=128,
                band_count=12,
            )

    def test_packet_loss_is_exactly_contained(self) -> None:
        source = self._stereo(4096)
        encoded = encode_lapped_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
            density_backend="adaptive",
        )
        info = index_lapped_packet_stream(encoded.payload)
        third = decode_lapped_packet_view(info, info.packets[2])
        simulation = simulate_lapped_packet_loss(
            encoded.payload,
            lost_packets=(1,),
        )

        np.testing.assert_array_equal(
            third,
            simulation.truth[2048:3072],
        )
        np.testing.assert_array_equal(
            simulation.reconstruction[:1024],
            simulation.truth[:1024],
        )
        np.testing.assert_array_equal(
            simulation.reconstruction[2048:],
            simulation.truth[2048:],
        )
        self.assertTrue(simulation.report["exact_outside_loss"])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(ValueError):
            decode_lapped_packet_stream(bytes(corrupted))
        self.assertTrue(
            simulation.report["all_recoverable_next_packets_exact"]
        )
        self.assertFalse(
            simulation.report["truth_reference_uses_concealment"]
        )

    def test_transform_packets_equal_one_global_selected_field(self) -> None:
        source = self._stereo(4096)
        encoded = encode_lapped_transform_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
        )
        info = index_lapped_packet_stream(encoded.payload)
        simulation = simulate_lapped_packet_loss(
            encoded.payload,
            lost_packets=(1,),
        )

        self.assertTrue(info.transform_boundary)
        self.assertEqual(len(info.packets), 4)
        self.assertTrue(
            encoded.report["exact_monolithic_reconstruction"]
        )
        np.testing.assert_array_equal(
            decode_lapped_packet_view(info, info.packets[2]),
            encoded.reconstruction[2048:3072],
        )
        np.testing.assert_array_equal(
            simulation.reconstruction[2048:],
            simulation.truth[2048:],
        )
        self.assertTrue(simulation.report["exact_outside_loss"])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(ValueError):
            decode_lapped_packet_stream(bytes(corrupted))

    def test_chained_packets_own_each_transform_frame_once(self) -> None:
        source = self._stereo(4096)
        independent = encode_lapped_transform_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
        )
        chained = encode_lapped_chained_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
        )
        info = index_lapped_packet_stream(chained.payload)

        self.assertTrue(info.chained_boundary)
        self.assertFalse(info.transform_boundary)
        self.assertEqual(
            chained.report["duplicated_boundary_transform_frames"],
            0,
        )
        self.assertLess(len(chained.payload), len(independent.payload))
        np.testing.assert_array_equal(
            chained.reconstruction,
            independent.reconstruction,
        )
        np.testing.assert_array_equal(
            decode_lapped_chained_packet_view(info, 2),
            chained.reconstruction[2048:3072],
        )
        with self.assertRaises(ValueError):
            decode_lapped_packet_view(info, info.packets[0])

    def test_compact_packets_remove_repeated_transport_metadata(self) -> None:
        source = self._stereo(4096)
        chained = encode_lapped_chained_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
        )
        compact = encode_lapped_compact_packet_stream(
            source,
            48000,
            coefficients_per_frame=28,
            packet_frames=1024,
            half_window=128,
            band_count=12,
        )
        info = index_lapped_packet_stream(compact.payload)

        self.assertTrue(info.chained_boundary)
        self.assertTrue(info.compact_transport)
        self.assertLess(len(compact.payload), len(chained.payload))
        np.testing.assert_array_equal(
            compact.reconstruction,
            chained.reconstruction,
        )
        corrupted = bytearray(compact.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(ValueError):
            decode_lapped_packet_stream(bytes(corrupted))


if __name__ == "__main__":
    unittest.main()
