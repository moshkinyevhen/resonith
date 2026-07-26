from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.composition import GainEventLaw  # noqa: E402
from maf_p0.main0 import (  # noqa: E402
    Main0State,
    decode_main0_raw_stream,
    encode_main0_periodic_rdo,
    encode_main0_state_rdo,
    pack_main0_cibs_stream,
    pack_main0_lpc_residual_stream,
    pack_main0_state_stream,
)
from maf_p0.model import encode_basis_latent, train_linear_cibs  # noqa: E402
from maf_p0.native_core import (  # noqa: E402
    NativeCoreError,
    NativeMain0Decoder,
)
from maf_p0.multichannel import (  # noqa: E402
    decode_main0_independent_stream,
    encode_main0_independent_rdo,
)
from maf_p0.periodic import constant_phase_trajectory  # noqa: E402


class NativeBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        library = os.environ.get("RESONITH_NATIVE_CORE")
        if not library:
            raise unittest.SkipTest(
                "set RESONITH_NATIVE_CORE to the shared Golden Core"
            )
        cls.library = library
        cls.decoder = NativeMain0Decoder(library)

        sample_count = 8192
        position = np.arange(sample_count, dtype=np.float64)
        phase = 2.0 * np.pi * position / 240.0
        envelope = 0.58 + 0.27 * np.sin(
            2.0 * np.pi * position / sample_count
        )
        signal = envelope * (
            22_000.0 * np.sin(phase)
            + 5_000.0 * np.sin(2.0 * phase + 0.17)
        )
        cls.samples = np.clip(
            np.rint(signal),
            -32768,
            32767,
        ).astype(np.int16)

    def test_native_decoder_is_the_rdo_acceptance_gate(self) -> None:
        encoded = encode_main0_periodic_rdo(
            self.samples,
            48_000,
            native_decoder=self.decoder,
            basis_length=128,
            gain_block_sizes=(512, 1024),
            innovation_step=1,
            residual_block_size=256,
            phase_knot_interval=4096,
        )
        self.assertEqual(encoded.report["native_decoder_gate"], "verified")
        self.assertEqual(encoded.report["candidate_count"], 10)
        native = self.decoder.decode(encoded.payload)
        np.testing.assert_array_equal(native.samples, encoded.reconstructed)
        np.testing.assert_array_equal(native.samples, self.samples)

    def test_native_status_and_host_memory_ceiling_are_enforced(self) -> None:
        encoded = encode_main0_periodic_rdo(
            self.samples,
            48_000,
            native_decoder=self.decoder,
            basis_length=128,
            gain_block_sizes=(1024,),
            innovation_step=1,
            residual_block_size=256,
        )
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 1
        with self.assertRaises(NativeCoreError):
            self.decoder.decode(bytes(corrupted))

        constrained = NativeMain0Decoder(
            self.library,
            max_workspace_bytes=1,
        )
        with self.assertRaises(MemoryError):
            constrained.inspect(encoded.payload)

    def test_zero_atom_truth_stream_has_zero_model_workspace(self) -> None:
        innovation = np.asarray(
            [-20_000, -10_923, -1, 0, 1, 10_922, 20_000],
            dtype=np.int32,
        )
        stream = pack_main0_lpc_residual_stream(
            sample_rate=48_000,
            innovation_q=innovation,
            innovation_step=3,
            residual_block_size=16,
            lpc_orders=(4,),
        )
        reference = decode_main0_raw_stream(stream)
        native = self.decoder.decode(stream)
        self.assertEqual(native.requirements.atom_count, 0)
        self.assertEqual(native.requirements.basis_count, 0)
        self.assertEqual(native.requirements.basis_elements, 0)
        self.assertEqual(native.requirements.phase_knot_count, 0)
        self.assertEqual(native.requirements.gain_event_count, 0)
        self.assertEqual(native.requirements.render_elements, 0)
        np.testing.assert_array_equal(native.samples, reference.samples)
        streamed = self.decoder.decode_streaming(stream)
        np.testing.assert_array_equal(streamed.samples, native.samples)
        self.assertEqual(streamed.sample_rate, native.sample_rate)
        self.assertEqual(streamed.requirements, native.requirements)

    def test_state_partition_and_basis_reuse_match_reference(self) -> None:
        basis = np.rint(
            20_000.0
            * np.sin(2.0 * np.pi * np.arange(64, dtype=np.float64) / 64.0)
        ).astype(np.int16)
        durations = (4000, 4192)
        states = tuple(
            Main0State(
                basis.copy(),
                constant_phase_trajectory(
                    duration,
                    0x0200_0000 + index * 0x0010_0000,
                    phase_origin_q32=index * 0x1111_0000,
                ),
                GainEventLaw(
                    np.asarray([0, duration // 2], dtype=np.uint32),
                    np.asarray([32768, 24576 + index * 4096], dtype=np.int32),
                    duration,
                ),
            )
            for index, duration in enumerate(durations)
        )
        stream = pack_main0_state_stream(
            sample_rate=48_000,
            states=states,
            innovation_q=np.zeros(sum(durations), dtype=np.int16),
            innovation_step=1,
            residual_block_size=256,
        )
        reference = decode_main0_raw_stream(stream)
        native = self.decoder.decode(stream)
        self.assertEqual(native.requirements.atom_count, 2)
        self.assertEqual(native.requirements.basis_count, 1)
        self.assertEqual(native.requirements.render_elements, max(durations))
        np.testing.assert_array_equal(native.samples, reference.samples)
        streamed = self.decoder.decode_streaming(stream)
        np.testing.assert_array_equal(streamed.samples, native.samples)

    def test_registry_backed_bcib_whole_and_callback_decode(self) -> None:
        basis = np.rint(
            20_000.0
            * np.sin(2.0 * np.pi * np.arange(64, dtype=np.float64) / 64.0)
        ).astype(np.int16)
        training = np.stack(
            (basis, np.roll(basis, 1), np.roll(basis, 2), -basis)
        ).astype(np.int16)[:, np.newaxis, :]
        model = train_linear_cibs(
            training,
            latent_elements=3,
            model_id="CIBS0-NATIVE-MAIN0-TEST",
        )
        latent = encode_basis_latent(basis.reshape(1, -1), model)
        duration = 4096
        trajectory = constant_phase_trajectory(duration, 0x0200_0000)
        gain = GainEventLaw(
            np.asarray([0, 2048], dtype=np.uint32),
            np.asarray([32768, 24576], dtype=np.int32),
            duration,
        )
        stream = pack_main0_cibs_stream(
            sample_rate=48_000,
            model=model,
            latent=latent,
            trajectory=trajectory,
            gain_law=gain,
            innovation_q=np.zeros(duration, dtype=np.int16),
            innovation_step=1,
            residual_block_size=16,
        )
        with self.assertRaises(NativeCoreError):
            self.decoder.decode(stream)
        reference = decode_main0_raw_stream(
            stream,
            cibs_models=(model,),
        )
        native = self.decoder.decode(stream, cibs_models=(model,))
        self.assertEqual(native.requirements.atom_count, 1)
        self.assertEqual(native.requirements.basis_count, 1)
        self.assertGreaterEqual(
            native.requirements.liftpack_scratch_elements,
            model.output_elements * 2,
        )
        np.testing.assert_array_equal(native.samples, reference.samples)
        streamed = self.decoder.decode_streaming(
            stream,
            cibs_models=(model,),
        )
        np.testing.assert_array_equal(streamed.samples, native.samples)

    def test_complete_byte_state_rdo_keeps_one_state_fallback(self) -> None:
        encoded = encode_main0_state_rdo(
            self.samples,
            48_000,
            native_decoder=self.decoder,
            basis_length=128,
            gain_block_sizes=(4096,),
            innovation_step=64,
            residual_block_size=(256, 512),
            fixed_state_durations_seconds=(0.08,),
            adaptive_change_penalties=(),
        )
        self.assertEqual(encoded.report["native_decoder_gate"], "verified")
        self.assertEqual(encoded.report["candidate_count"], 12)
        self.assertGreater(encoded.report["one_state_bytes"], 0)
        self.assertIn(
            encoded.report["residual_block_size"],
            {256, 512},
        )
        native = self.decoder.decode(encoded.payload)
        np.testing.assert_array_equal(native.samples, encoded.reconstructed)

    def test_independent_stereo_whole_and_callback_decode(self) -> None:
        right = np.roll(self.samples, 37)
        stereo = np.stack((self.samples, right), axis=1)
        encoded = encode_main0_independent_rdo(
            stereo,
            48_000,
            innovation_step=1,
            residual_block_sizes=(256, 512),
        )
        reference = decode_main0_independent_stream(encoded.payload)
        native = self.decoder.decode_multichannel(encoded.payload)
        streamed = self.decoder.decode_multichannel_streaming(encoded.payload)

        self.assertEqual(native.requirements.output_channels, 2)
        self.assertEqual(
            native.requirements.output_block_elements,
            native.requirements.block_size * 2,
        )
        np.testing.assert_array_equal(native.samples, reference.samples)
        np.testing.assert_array_equal(streamed.samples, native.samples)


if __name__ == "__main__":
    unittest.main()
