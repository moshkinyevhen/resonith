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
    MafBasisInstance,
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
from maf_p0.motif_orbit import _fit_gain_shift_q15
from maf_p0.native_core import NativeMain0Decoder
from maf_p0.motif_orbit import (
    _render_gain_shift_envelope,
    encode_gain_orbit_candidate,
    encode_multichannel_gain_orbit_candidate,
    encode_optimized_independent_truth,
)


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
        self.assertEqual(len(info.basis_instances), 0)

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

    def test_basis_instance_reference_is_checked_before_packing(self) -> None:
        with self.assertRaisesRegex(ValueError, "resolved bounds"):
            pack_maf_typed(
                sample_rate=48000,
                total_frames=16,
                render_quantum=8,
                output_channels=1,
                emitter_count=1,
                mixes=(MafMix(0, 16, ((32767,),)),),
                bases=(MafBasis((1, 2, 3, 4)),),
                basis_instances=(
                    MafBasisInstance(0, 1, 0, 32768, 0, 4),
                ),
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

    def test_basis_instance_reuses_one_immutable_waveform(self) -> None:
        basis = (1000, -2000, 3000, -4000)
        payload = pack_maf_typed(
            sample_rate=48000,
            total_frames=20,
            render_quantum=8,
            output_channels=1,
            emitter_count=1,
            mixes=(MafMix(0, 20, ((32767,),)),),
            bases=(MafBasis(basis),),
            basis_instances=(
                MafBasisInstance(0, 0, 0, 32768, 0, len(basis)),
                MafBasisInstance(0, 0, 8, 32768, 0, len(basis)),
            ),
            declared_operations_per_frame=32,
        )
        info = parse_maf_typed(payload)
        self.assertEqual(info.bases[0].samples, basis)
        self.assertEqual(len(info.basis_instances), 2)
        regular = self.decoder.decode_maf_typed(payload, callback_frames=8)
        irregular = self.decoder.decode_maf_typed(payload, callback_frames=3)
        np.testing.assert_array_equal(regular.samples, irregular.samples)
        np.testing.assert_array_equal(
            regular.samples[0:4, 0],
            regular.samples[8:12, 0],
        )
        self.assertTrue(np.all(regular.samples[4:8, 0] == 0))
        self.assertTrue(np.all(regular.samples[12:, 0] == 0))

    def test_basis_instance_phase_counterphase_and_envelope(self) -> None:
        basis = (1000, -2000, 3000, -4000)
        payload = pack_maf_typed(
            sample_rate=48000,
            total_frames=16,
            render_quantum=8,
            output_channels=1,
            emitter_count=1,
            mixes=(MafMix(0, 16, ((32767,),)),),
            bases=(MafBasis(basis),),
            basis_instances=(
                MafBasisInstance(
                    0,
                    0,
                    0,
                    -32768,
                    1,
                    4,
                    circular=True,
                ),
                MafBasisInstance(
                    0,
                    0,
                    8,
                    32768,
                    2,
                    4,
                    circular=True,
                    end_gain_q15=0,
                ),
            ),
            declared_operations_per_frame=64,
        )
        info = parse_maf_typed(payload)
        self.assertTrue(info.basis_instances[0].circular)
        self.assertEqual(info.basis_instances[1].end_gain_q15, 0)
        decoded = self.decoder.decode_maf_typed(payload, callback_frames=3)
        np.testing.assert_array_equal(
            decoded.samples[0:4, 0],
            np.asarray((2000, -3000, 4000, -1000), dtype=np.int16),
        )
        self.assertEqual(int(decoded.samples[8, 0]), 3000)
        self.assertEqual(int(decoded.samples[11, 0]), 0)

    def test_basis_instance_reverse_and_circular_reverse(self) -> None:
        basis = (100, -200, 300, -400)
        payload = pack_maf_typed(
            sample_rate=48000,
            total_frames=8,
            render_quantum=4,
            output_channels=1,
            emitter_count=1,
            mixes=(MafMix(0, 8, ((32767,),)),),
            bases=(MafBasis(basis),),
            basis_instances=(
                MafBasisInstance(
                    0,
                    0,
                    0,
                    32768,
                    3,
                    4,
                    reverse=True,
                ),
                MafBasisInstance(
                    0,
                    0,
                    4,
                    32768,
                    1,
                    4,
                    circular=True,
                    reverse=True,
                ),
            ),
            declared_operations_per_frame=64,
        )
        info = parse_maf_typed(payload)
        self.assertTrue(all(item.reverse for item in info.basis_instances))
        regular = self.decoder.decode_maf_typed(payload, callback_frames=4)
        irregular = self.decoder.decode_maf_typed(payload, callback_frames=3)
        np.testing.assert_array_equal(regular.samples, irregular.samples)
        np.testing.assert_array_equal(
            regular.samples[:, 0],
            np.asarray(
                (-400, 300, -200, 100, -200, 100, -400, 300),
                dtype=np.int16,
            ),
        )

    def test_phase_search_finds_shift_and_counterphase(self) -> None:
        basis = np.asarray((100, 200, -300, 500, -700, 1100), dtype=np.int64)
        target = -np.roll(basis, 2)
        gain, source_offset, error = _fit_gain_shift_q15(basis, target)
        self.assertEqual(gain, -32768)
        self.assertEqual(source_offset, basis.size - 2)
        self.assertEqual(error, 0.0)

    def test_one_basis_routes_to_two_channels_with_transfer_laws(self) -> None:
        basis = (1000, -2000, 3000, -4000)
        payload = pack_maf_typed(
            sample_rate=48000,
            total_frames=16,
            render_quantum=8,
            output_channels=2,
            emitter_count=2,
            mixes=(
                MafMix(
                    0,
                    16,
                    (
                        (32767, 0),
                        (0, 32767),
                    ),
                ),
            ),
            bases=(MafBasis(basis),),
            basis_instances=(
                MafBasisInstance(0, 0, 0, 32768, 0, 4),
                MafBasisInstance(
                    1,
                    0,
                    2,
                    16384,
                    1,
                    4,
                    circular=True,
                    end_gain_q15=0,
                ),
            ),
            declared_operations_per_frame=128,
        )
        regular = self.decoder.decode_maf_typed(payload, callback_frames=8)
        irregular = self.decoder.decode_maf_typed(payload, callback_frames=3)
        np.testing.assert_array_equal(regular.samples, irregular.samples)
        np.testing.assert_array_equal(
            regular.samples[0:4, 0],
            np.asarray(basis, dtype=np.int16),
        )
        self.assertEqual(int(regular.samples[2, 1]), -1000)
        self.assertEqual(int(regular.samples[5, 1]), 0)
        self.assertTrue(np.all(regular.samples[6:, 1] == 0))

    def test_cross_channel_phase_and_decay_dictionary_reduces_bytes(self) -> None:
        length = 256
        position = np.arange(length, dtype=np.float64)
        basis = np.rint(
            9000.0 * np.sin(2.0 * np.pi * 5.0 * position / length)
            + 2500.0 * np.sin(2.0 * np.pi * 19.0 * position / length)
        ).astype(np.int64)
        left_blocks = []
        right_blocks = []
        for block_index in range(32):
            left_blocks.append(
                _render_gain_shift_envelope(
                    basis,
                    (3 * block_index) % length,
                    32768 - 256 * (block_index % 8),
                    None,
                )
            )
            right_blocks.append(
                _render_gain_shift_envelope(
                    basis,
                    (5 * block_index + 17) % length,
                    28672,
                    16384,
                )
            )
        source = np.column_stack(
            (
                np.concatenate(left_blocks),
                np.concatenate(right_blocks),
            )
        ).astype(np.int16)
        baseline_bytes = 0
        for channel in range(2):
            payload, _ = encode_optimized_independent_truth(
                source[:, channel : channel + 1],
                truth_block_sizes=(1024,),
            )
            baseline_bytes += 4 + len(payload)
        candidate = encode_multichannel_gain_orbit_candidate(
            source,
            48000,
            native_decoder=self.decoder,
            block_samples=length,
            truth_block_sizes=(1024,),
            maximum_normalized_error=1.0e-6,
        )
        np.testing.assert_array_equal(candidate.reconstruction, source)
        self.assertEqual(candidate.report["basis_count"], 1)
        self.assertGreater(
            candidate.report["linear_gain_instance_count"],
            0,
        )
        self.assertTrue(
            all(
                value > 0
                for value in candidate.report["covered_samples_by_channel"]
            )
        )
        self.assertLess(candidate.representation_bytes, baseline_bytes)

    def test_gain_orbit_reduces_exact_transformed_loop_bytes(self) -> None:
        length = 256
        phase = np.arange(length, dtype=np.float64)
        basis = np.rint(
            9000.0 * np.sin(2.0 * np.pi * 5.0 * phase / length)
            + 3000.0 * np.sin(2.0 * np.pi * 17.0 * phase / length)
        ).astype(np.int64)
        gains = (32768, 24576, -32768, 16384) * 16
        blocks = []
        for gain in gains:
            product = basis * gain
            scaled = np.where(
                product >= 0,
                (product + 16384) // 32768,
                -((-product + 16384) // 32768),
            )
            blocks.append(scaled.astype(np.int16))
        source = np.concatenate(blocks)[:, None]
        baseline, _ = encode_optimized_independent_truth(
            source,
            truth_block_sizes=(1024,),
        )
        candidate = encode_gain_orbit_candidate(
            source,
            48000,
            native_decoder=self.decoder,
            block_samples=length,
            truth_block_sizes=(1024,),
            maximum_normalized_error=1.0e-6,
        )
        np.testing.assert_array_equal(candidate.reconstruction, source)
        self.assertEqual(candidate.report["basis_count"], 1)
        self.assertEqual(candidate.report["instance_count"], len(gains))
        self.assertLess(candidate.representation_bytes, len(baseline))


if __name__ == "__main__":
    unittest.main()
