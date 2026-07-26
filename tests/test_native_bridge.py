from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.main0 import encode_main0_periodic_rdo  # noqa: E402
from maf_p0.native_core import (  # noqa: E402
    NativeCoreError,
    NativeMain0Decoder,
)


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
        self.assertEqual(encoded.report["candidate_count"], 4)
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


if __name__ == "__main__":
    unittest.main()
