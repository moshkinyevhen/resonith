from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.cli import (  # noqa: E402
    _decode_lapped,
    _encode_lapped,
    _encode_resonith,
)
from maf_p0.lapped_streaming import decode_lapped_packet_stream  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


class LappedCliTests(unittest.TestCase):
    def test_adaptive_stereo_encode_and_decode_workflow(self) -> None:
        frame = np.arange(4096, dtype=np.float64)
        source = np.stack(
            (
                np.rint(12000 * np.sin(2 * np.pi * frame / 109)),
                np.rint(9000 * np.sin(2 * np.pi * frame / 157 + 0.4)),
            ),
            axis=1,
        ).astype(np.int16)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source_path = directory / "source.wav"
            stream_path = directory / "audio.rsc"
            decoded_path = directory / "decoded.wav"
            write_pcm16_channels(source_path, 48000, source)
            encode_output = io.StringIO()
            with redirect_stdout(encode_output):
                _encode_lapped(
                    argparse.Namespace(
                        input=source_path,
                        output=stream_path,
                        average_coefficients=32,
                        half_window=256,
                        bands=16,
                        density="adaptive",
                        packet_frames=1024,
                        native_core=None,
                    )
                )
            reference = decode_lapped_packet_stream(stream_path.read_bytes())
            with redirect_stdout(io.StringIO()):
                _decode_lapped(
                    argparse.Namespace(
                        input=stream_path,
                        output=decoded_path,
                    )
                )
            sample_rate, decoded = read_pcm16_channels(decoded_path)
            report = json.loads(encode_output.getvalue())

        self.assertEqual(sample_rate, 48000)
        self.assertEqual(report["density_backend"], "adaptive")
        self.assertEqual(report["packet_count"], 4)
        self.assertGreater(report["stream_bytes"], 0)
        np.testing.assert_array_equal(decoded, reference.samples)

    def test_canonical_resonith_encode_uses_lps5_and_auto_packet_size(
        self,
    ) -> None:
        frame = np.arange(8192, dtype=np.float64)
        source = np.rint(
            11000 * np.sin(2 * np.pi * frame / 83)
        ).astype(np.int16).reshape(-1, 1)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source_path = directory / "speech.wav"
            stream_path = directory / "speech.resonith"
            write_pcm16_channels(source_path, 16000, source)
            encoded_output = io.StringIO()
            with redirect_stdout(encoded_output):
                _encode_resonith(
                    argparse.Namespace(
                        input=source_path,
                        output=stream_path,
                        average_coefficients=24,
                        half_window=512,
                        bands=24,
                        packet_frames=0,
                        native_core=None,
                    )
                )
            report = json.loads(encoded_output.getvalue())
            payload = stream_path.read_bytes()
            decoded = decode_lapped_packet_stream(payload)
            decoded_path = directory / "decoded.wav"
            with redirect_stdout(io.StringIO()):
                _decode_lapped(
                    argparse.Namespace(
                        input=stream_path,
                        output=decoded_path,
                    )
                )
            decoded_rate, decoded_from_cli = read_pcm16_channels(decoded_path)

        self.assertEqual(report["format_profile"], "prospective-LPS5")
        self.assertEqual(report["packet_frames"], 4096)
        self.assertTrue(payload.startswith(b"LPS5"))
        self.assertEqual(decoded.sample_rate, 16000)
        self.assertEqual(decoded.samples.shape, source.shape)
        self.assertEqual(decoded_rate, 16000)
        np.testing.assert_array_equal(decoded_from_cli, decoded.samples)


if __name__ == "__main__":
    unittest.main()
