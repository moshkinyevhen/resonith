from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from listening_set import create_blinded_listening_set  # noqa: E402


class ListeningSetTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_identity_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / "sources"
            sources.mkdir()
            candidates = {}
            for name, payload in {
                "reference": b"RIFF-reference",
                "resonith": b"RIFF-resonith",
                "opus": b"RIFF-opus",
            }.items():
                path = sources / f"{name}.wav"
                path.write_bytes(payload)
                candidates[name] = path

            output = root / "blind"
            manifest, key = create_blinded_listening_set(
                {"clip-one": candidates},
                output,
                seed="fixed-test-seed",
            )
            self.assertNotIn(
                "resonith",
                json.dumps(manifest["trials"]),
            )
            self.assertIn("resonith", json.dumps(key))
            first_manifest = (output / "manifest.json").read_bytes()
            first_key = (output / "answer-key.json").read_bytes()

            second = root / "blind-again"
            create_blinded_listening_set(
                {"clip-one": candidates},
                second,
                seed="fixed-test-seed",
            )
            self.assertEqual(
                first_manifest,
                (second / "manifest.json").read_bytes(),
            )
            self.assertEqual(
                first_key,
                (second / "answer-key.json").read_bytes(),
            )

    def test_unsafe_clip_ids_and_missing_candidates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "candidate.wav"
            path.write_bytes(b"wave")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                create_blinded_listening_set(
                    {"../escape": {"a": path, "b": path}},
                    root / "out",
                    seed="seed",
                )
            with self.assertRaisesRegex(ValueError, "missing"):
                create_blinded_listening_set(
                    {
                        "safe": {
                            "a": path,
                            "b": root / "missing.wav",
                        }
                    },
                    root / "out2",
                    seed="seed",
                )


if __name__ == "__main__":
    unittest.main()
