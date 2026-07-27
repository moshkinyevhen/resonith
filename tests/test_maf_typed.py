"""Python-pack/native-decode parity for prospective MFT1 lifetimes."""

from __future__ import annotations

import os
import unittest

import numpy as np

from maf_p0.maf_typed import (
    IMPULSE_EXCITATION,
    PERIODIC_BASIS_EXCITATION,
    STOCHASTIC_EXCITATION,
    MafBasis,
    MafFilter,
    MafMix,
    MafSourceFilter,
    MafStochastic,
    MafTransient,
    pack_maf_typed,
    parse_maf_typed,
)
from maf_p0.maf_typed_candidate import (
    _estimate_period,
    decode_maf_typed_truth_candidate,
    encode_maf_typed_truth_candidate,
    fit_maf_typed_prediction,
)
from maf_p0.native_core import NativeMain0Decoder


def _vector() -> bytes:
    return pack_maf_typed(
        sample_rate=48000,
        total_frames=32,
        render_quantum=16,
        output_channels=2,
        emitter_count=2,
        filters=(MafFilter((4096, -2048)),),
        stochastic=(
            MafStochastic(1, 0, 32, 6000),
            MafStochastic(None, 16, 32, 9000),
        ),
        sources=(
            MafSourceFilter(
                0,
                0,
                IMPULSE_EXCITATION,
                None,
                0,
                16,
                18000,
                0,
                0x4000_0000,
            ),
            MafSourceFilter(
                0,
                0,
                STOCHASTIC_EXCITATION,
                1,
                16,
                32,
                16384,
            ),
        ),
        transients=(MafTransient(0, 8, 32768, (1000, 2000, -1000, -500)),),
        mixes=(
            MafMix(
                0,
                32,
                (
                    (32767, 0),
                    (0, 32767),
                ),
            ),
        ),
        declared_operations_per_frame=256,
    )


class MafTypedReferenceTests(unittest.TestCase):
    def test_pack_parse_round_trip(self) -> None:
        payload = _vector()
        info = parse_maf_typed(payload)
        self.assertEqual(info.total_frames, 32)
        self.assertEqual(info.output_channels, 2)
        self.assertEqual(len(info.filters), 1)
        self.assertEqual(len(info.stochastic), 2)
        self.assertEqual(len(info.sources), 2)
        self.assertEqual(len(info.transients), 1)
        self.assertEqual(len(info.mixes), 1)
        self.assertEqual(len(info.bases), 0)

    def test_checksum_mutation_is_rejected(self) -> None:
        payload = bytearray(_vector())
        payload[80] ^= 0x80
        with self.assertRaisesRegex(ValueError, "checksum"):
            parse_maf_typed(bytes(payload))

    def test_period_estimator_prefers_fundamental_over_exact_multiple(self) -> None:
        sample_rate = 44100
        frame = np.arange(sample_rate // 4, dtype=np.float64)
        source = np.rint(
            np.sin(2.0 * np.pi * 1000.0 * frame / sample_rate) * 12000.0
        ).astype(np.int16)
        period, score = _estimate_period(source, sample_rate)
        self.assertLess(abs(period - 44.1), 0.25)
        self.assertGreater(score, 0.99)

    def test_unknown_representation_mask_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown family"):
            fit_maf_typed_prediction(
                np.zeros((128, 1), dtype=np.int16),
                16000,
                native_decoder=None,
                allowed_modes=(99,),
            )


@unittest.skipUnless(
    os.environ.get("RESONITH_NATIVE_CORE"),
    "set RESONITH_NATIVE_CORE to the shared Golden Core",
)
class MafTypedNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.decoder = NativeMain0Decoder(os.environ["RESONITH_NATIVE_CORE"])

    def test_python_pack_native_partition_parity(self) -> None:
        payload = _vector()
        quantum = self.decoder.decode_maf_typed(
            payload,
            callback_frames=16,
        )
        irregular = self.decoder.decode_maf_typed(
            payload,
            callback_frames=7,
        )
        np.testing.assert_array_equal(quantum.samples, irregular.samples)
        self.assertTrue(np.any(quantum.samples))
        self.assertEqual(quantum.sample_rate, 48000)
        self.assertEqual(quantum.samples.shape, (32, 2))

    def test_complete_predictor_truth_candidate(self) -> None:
        sample_rate = 16000
        frame = np.arange(4096, dtype=np.float64)
        source = np.rint(
            12000.0 * np.sin(2.0 * np.pi * 200.0 * frame / sample_rate)
        ).astype(np.int16)[:, None]
        prediction = fit_maf_typed_prediction(
            source,
            sample_rate,
            native_decoder=self.decoder,
            segment_milliseconds=128.0,
            filter_order=6,
            render_quantum=256,
        )
        self.assertEqual(prediction.reconstruction.shape, source.shape)
        candidate = encode_maf_typed_truth_candidate(
            source,
            sample_rate,
            native_decoder=self.decoder,
            coefficients_per_frame=24,
            segment_milliseconds=128.0,
            filter_order=6,
            half_window=64,
            band_count=8,
            residual_budget_override=7,
        )
        decoded_rate, decoded = decode_maf_typed_truth_candidate(
            candidate.payload,
            native_decoder=self.decoder,
        )
        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(decoded, candidate.reconstruction)
        self.assertIn(
            candidate.selected_kind,
            {"mft1-truth", "truth-fallback"},
        )
        self.assertEqual(
            candidate.report["selected_residual_coefficients_per_frame"],
            7,
        )

    def test_periodic_basis_is_absolute_and_partition_invariant(self) -> None:
        payload = pack_maf_typed(
            sample_rate=48000,
            total_frames=32,
            render_quantum=16,
            output_channels=1,
            emitter_count=1,
            sources=(
                MafSourceFilter(
                    0,
                    0xFFFF,
                    PERIODIC_BASIS_EXCITATION,
                    0,
                    0,
                    32,
                    32768,
                    0,
                    0x4000_0000,
                ),
            ),
            mixes=(MafMix(0, 32, ((32767,),)),),
            bases=(MafBasis((0, 32767, 0, -32768)),),
            declared_operations_per_frame=32,
        )
        regular = self.decoder.decode_maf_typed(payload, callback_frames=16)
        irregular = self.decoder.decode_maf_typed(payload, callback_frames=7)
        np.testing.assert_array_equal(regular.samples, irregular.samples)
        self.assertGreater(np.max(np.abs(regular.samples)), 32000)


if __name__ == "__main__":
    unittest.main()
