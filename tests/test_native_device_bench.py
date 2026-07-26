from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_compact_packet_stream,
)


class NativeDeviceBenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        executable = os.environ.get("RESONITH_NATIVE_DEVICE_BENCH")
        if not executable:
            raise unittest.SkipTest(
                "set RESONITH_NATIVE_DEVICE_BENCH to the native executable"
            )
        cls.executable = executable

    def test_repeated_compact_decode_is_exact_and_machine_readable(self) -> None:
        frame = np.arange(4096, dtype=np.float64)
        samples = np.stack(
            (
                np.rint(12000.0 * np.sin(2.0 * np.pi * frame / 71.0)),
                np.rint(9000.0 * np.sin(2.0 * np.pi * frame / 113.0)),
            ),
            axis=1,
        ).astype(np.int16)
        encoded = encode_lapped_compact_packet_stream(
            samples,
            48000,
            coefficients_per_frame=32,
            packet_frames=1536,
            half_window=512,
            band_count=24,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.lps"
            path.write_bytes(encoded.payload)
            completed = subprocess.run(
                [self.executable, str(path), "2", "1"],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)
            self.assertEqual(
                report["schema"],
                "resonith-lapped-device-bench-1",
            )
            self.assertEqual(report["frame_count"], samples.shape[0])
            self.assertEqual(report["channel_count"], samples.shape[1])
            self.assertEqual(report["iterations"], 2)
            self.assertEqual(
                report["callback_observations"],
                2 * report["packet_count"],
            )
            self.assertTrue(report["all_passes_exact"])
            self.assertEqual(len(report["pcm_fnv1a64"]), 16)
            self.assertGreater(report["decode_realtime_speed"], 0.0)
            self.assertGreater(report["caller_workspace_bytes"], 0)

            corrupted = bytearray(encoded.payload)
            corrupted[-1] ^= 1
            path.write_bytes(corrupted)
            rejected = subprocess.run(
                [self.executable, str(path), "1", "1"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, "")
            self.assertIn("preflight failed", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
