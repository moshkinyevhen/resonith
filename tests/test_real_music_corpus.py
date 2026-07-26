from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import wave

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from real_music_benchmark import (  # noqa: E402
    read_pcm_as_channels16,
    read_pcm_as_mono16,
)


def pack_pcm24(values: np.ndarray) -> bytes:
    unsigned = np.where(values < 0, values + (1 << 24), values).astype(np.uint32)
    packed = np.empty((values.size, 3), dtype=np.uint8)
    packed[:, 0] = unsigned & 0xFF
    packed[:, 1] = (unsigned >> 8) & 0xFF
    packed[:, 2] = (unsigned >> 16) & 0xFF
    return packed.tobytes()


class RealMusicCorpusTests(unittest.TestCase):
    def test_manifest_pins_source_license_and_hash(self) -> None:
        manifest = json.loads(
            (
                PROJECT_ROOT / "experiments" / "real_music_corpus.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], "resonith-real-music-corpus-1")
        self.assertGreaterEqual(len(manifest["sources"]), 3)
        for source in manifest["sources"]:
            self.assertEqual(len(source["sha256"]), 64)
            self.assertTrue(source["source_page"].startswith("https://"))
            self.assertTrue(source["download_url"].startswith("https://"))
            self.assertTrue(source["license"])

    def test_pcm16_stereo_downmix_is_deterministic(self) -> None:
        frames = np.asarray(
            [
                [1000, -1000],
                [32767, 32767],
                [-32768, -32768],
            ],
            dtype="<i2",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stereo16.wav"
            with wave.open(str(path), "wb") as destination:
                destination.setnchannels(2)
                destination.setsampwidth(2)
                destination.setframerate(48000)
                destination.writeframes(frames.tobytes())
            rate, mono, report = read_pcm_as_mono16(path)
        self.assertEqual(rate, 48000)
        self.assertEqual(report["source_sample_width_bits"], 16)
        np.testing.assert_array_equal(
            mono,
            np.asarray([0, 32767, -32768], dtype=np.int16),
        )

    def test_pcm24_downconversion_rounds_symmetrically(self) -> None:
        frames = np.asarray(
            [
                [256, 256],
                [-256, -256],
                [128, 128],
                [-128, -128],
            ],
            dtype=np.int32,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stereo24.wav"
            with wave.open(str(path), "wb") as destination:
                destination.setnchannels(2)
                destination.setsampwidth(3)
                destination.setframerate(44100)
                destination.writeframes(pack_pcm24(frames.reshape(-1)))
            _, mono, report = read_pcm_as_mono16(path)
        self.assertEqual(report["source_sample_width_bits"], 24)
        np.testing.assert_array_equal(
            mono,
            np.asarray([1, -1, 1, -1], dtype=np.int16),
        )

    def test_pcm_channels_preserve_stereo_without_downmix(self) -> None:
        frames = np.asarray(
            [[1000, -1000], [32767, -32768]],
            dtype="<i2",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "channels16.wav"
            with wave.open(str(path), "wb") as destination:
                destination.setnchannels(2)
                destination.setsampwidth(2)
                destination.setframerate(48000)
                destination.writeframes(frames.tobytes())
            rate, channels, report = read_pcm_as_channels16(path)
        self.assertEqual(rate, 48000)
        self.assertEqual(report["source_channels"], 2)
        np.testing.assert_array_equal(channels, frames)


if __name__ == "__main__":
    unittest.main()
