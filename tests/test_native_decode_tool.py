from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
)
from maf_p0.wav_io import read_pcm16_channels  # noqa: E402


class NativeDecodeToolTests(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("RESONITH_NATIVE_DECODE"),
        "native decoder executable is not configured",
    )
    def test_lps5_to_wave_matches_python_reconstruction(self) -> None:
        frame = np.arange(8192, dtype=np.float64)
        source = np.stack(
            (
                np.rint(12000 * np.sin(2 * np.pi * frame / 109)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 157 + 0.4)),
            ),
            axis=1,
        ).astype(np.int16)
        encoded = encode_lapped_finite_packet_stream(
            source,
            48000,
            coefficients_per_frame=32,
            packet_frames=2048,
            half_window=256,
            band_count=16,
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            stream_path = directory / "test.resonith"
            wave_path = directory / "decoded.wav"
            stream_path.write_bytes(encoded.payload)
            completed = subprocess.run(
                [
                    os.environ["RESONITH_NATIVE_DECODE"],
                    str(stream_path),
                    str(wave_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            sample_rate, decoded = read_pcm16_channels(wave_path)

        self.assertIn('"frames":8192', completed.stdout)
        self.assertEqual(sample_rate, 48000)
        np.testing.assert_array_equal(decoded, encoded.reconstruction)


if __name__ == "__main__":
    unittest.main()
