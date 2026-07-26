from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.cli import _decode_main0, _encode_main0  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


class MultichannelCliTests(unittest.TestCase):
    @staticmethod
    def _stereo() -> np.ndarray:
        frames = np.arange(2048, dtype=np.int64)
        left = np.rint(
            12_000.0 * np.sin(2.0 * np.pi * frames / 127.0)
        ).astype(np.int16)
        right = np.rint(
            9_000.0 * np.sin(2.0 * np.pi * frames / 173.0)
        ).astype(np.int16)
        return np.stack((left, right), axis=1)

    def test_pcm16_stereo_cli_round_trip(self) -> None:
        source = self._stereo()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source_path = directory / "source.wav"
            stream_path = directory / "audio.rsc"
            decoded_path = directory / "decoded.wav"
            write_pcm16_channels(source_path, 48000, source)

            with redirect_stdout(io.StringIO()):
                _encode_main0(
                    argparse.Namespace(
                        input=source_path,
                        output=stream_path,
                        innovation_step=1,
                        residual_blocks=(256, 512),
                    )
                )
                _decode_main0(
                    argparse.Namespace(
                        input=stream_path,
                        output=decoded_path,
                        model=None,
                    )
                )
            sample_rate, decoded = read_pcm16_channels(decoded_path)

        self.assertEqual(sample_rate, 48000)
        np.testing.assert_array_equal(decoded, source)

    def test_reader_rejects_more_than_eight_channels(self) -> None:
        source = np.zeros((32, 9), dtype=np.int16)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.wav"
            with self.assertRaisesRegex(TypeError, "1-8 channels"):
                write_pcm16_channels(path, 48000, source)


if __name__ == "__main__":
    unittest.main()
