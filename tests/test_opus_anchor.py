from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.opus_anchor import (  # noqa: E402
    resolve_opus_tools,
    run_opus_anchor,
    run_opus_multichannel_anchor,
)


class OpusAnchorTests(unittest.TestCase):
    def test_invalid_configuration_is_rejected_before_execution(self) -> None:
        samples = np.zeros(4800, dtype=np.int16)
        with self.assertRaises(ValueError):
            run_opus_anchor(samples, 48000, bitrate_kbps=1.0)
        with self.assertRaises(ValueError):
            run_opus_anchor(samples, 48000, bitrate_kbps=64.0, mode="invalid")

    @unittest.skipUnless(
        os.environ.get("RESONITH_OPUS_TOOLS"),
        "set RESONITH_OPUS_TOOLS for the external integration test",
    )
    def test_real_opus_round_trip_and_provenance(self) -> None:
        sample_rate = 48000
        time = np.arange(9600, dtype=np.float64) / sample_rate
        samples = np.rint(
            12000.0 * np.sin(2.0 * np.pi * 440.0 * time)
        ).astype(np.int16)
        tools = resolve_opus_tools()
        result = run_opus_anchor(
            samples,
            sample_rate,
            bitrate_kbps=64.0,
            tools=tools,
        )
        repeated = run_opus_anchor(
            samples,
            sample_rate,
            bitrate_kbps=64.0,
            tools=tools,
        )
        self.assertEqual(result.reconstructed.shape, samples.shape)
        self.assertGreater(len(result.payload), 0)
        self.assertIn("libopus", result.report["encoder_version"])
        self.assertEqual(len(result.report["encoder_sha256"]), 64)
        self.assertEqual(len(result.report["stream_sha256"]), 64)
        self.assertEqual(
            result.report["stream_sha256"],
            repeated.report["stream_sha256"],
        )
        np.testing.assert_array_equal(
            result.reconstructed,
            repeated.reconstructed,
        )
        self.assertGreater(result.report["snr_db"], 20.0)

    @unittest.skipUnless(
        os.environ.get("RESONITH_OPUS_TOOLS"),
        "set RESONITH_OPUS_TOOLS for the external integration test",
    )
    def test_real_stereo_anchor_and_shape(self) -> None:
        frame = np.arange(4800, dtype=np.float64)
        samples = np.stack(
            (
                np.rint(12000 * np.sin(2 * np.pi * frame / 109)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 163)),
            ),
            axis=1,
        ).astype(np.int16)
        result = run_opus_multichannel_anchor(
            samples,
            48000,
            bitrate_kbps=96.0,
        )

        self.assertEqual(result.reconstructed.shape, samples.shape)
        self.assertEqual(result.report["channel_count"], 2)
        self.assertEqual(result.report["frame_count"], samples.shape[0])
        self.assertGreater(result.report["stream_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
