from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from listening_results import summarize_results, validate_result  # noqa: E402
from listening_set import create_blinded_listening_set  # noqa: E402


class ListeningResultTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
    ) -> tuple[dict, str, dict, dict]:
        source = root / "source.wav"
        resonith = root / "resonith.wav"
        opus = root / "opus.wav"
        source.write_bytes(b"RIFF-source")
        resonith.write_bytes(b"RIFF-resonith")
        opus.write_bytes(b"RIFF-opus")
        output = root / "listening"
        manifest, answer_key = create_blinded_listening_set(
            {
                "clip-one": {
                    "source": source,
                    "resonith": resonith,
                    "opus": opus,
                }
            },
            output,
            seed="result-test",
        )
        manifest_payload = (output / "manifest.json").read_bytes()
        manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
        labels = [
            candidate["label"]
            for candidate in manifest["trials"][0]["candidates"]
        ]
        result = {
            "schema": "resonith-blind-listening-result-1",
            "manifest_sha256": manifest_sha256,
            "listener_id": "listener-01",
            "playback_setup": "headphones",
            "session_started_utc": "2026-07-26T18:00:00.000Z",
            "session_completed_utc": "2026-07-26T18:05:00.000Z",
            "trials": [
                {
                    "clip_id": "clip-one",
                    "scores": {
                        label: 80 + index
                        for index, label in enumerate(labels)
                    },
                    "audition_seconds": {
                        "reference": 2.0,
                        **{label: 1.0 for label in labels},
                    },
                    "switch_count": 4,
                    "artifacts": {label: [] for label in labels},
                    "notes": {label: "" for label in labels},
                }
            ],
        }
        return manifest, manifest_sha256, answer_key, result

    def test_valid_result_unblinds_to_descriptive_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._fixture(Path(directory))
            manifest, digest, key, result = fixture
            validate_result(result, manifest, digest)
            summary = summarize_results(
                [result],
                manifest,
                digest,
                key,
            )
            self.assertEqual(summary["listener_count"], 1)
            self.assertEqual(summary["score_observations"], 3)
            self.assertEqual(
                set(summary["conditions"]),
                {"source", "resonith", "opus"},
            )
            self.assertEqual(
                summary["hidden_reference_screening"]["observations"],
                1,
            )
            self.assertFalse(
                summary["hidden_reference_screening"][
                    "automatic_listener_exclusion"
                ]
            )

    def test_manifest_mismatch_and_incomplete_scores_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest, digest, _key, result = self._fixture(Path(directory))
            wrong_manifest = copy.deepcopy(result)
            wrong_manifest["manifest_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "different manifest"):
                validate_result(wrong_manifest, manifest, digest)

            incomplete = copy.deepcopy(result)
            first_label = next(iter(incomplete["trials"][0]["scores"]))
            del incomplete["trials"][0]["scores"][first_label]
            with self.assertRaisesRegex(ValueError, "one score"):
                validate_result(incomplete, manifest, digest)

    def test_score_audition_and_duplicate_listener_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest, digest, key, result = self._fixture(Path(directory))
            invalid_score = copy.deepcopy(result)
            label = next(iter(invalid_score["trials"][0]["scores"]))
            invalid_score["trials"][0]["scores"][label] = 101
            with self.assertRaisesRegex(ValueError, "outside"):
                validate_result(invalid_score, manifest, digest)

            short_audition = copy.deepcopy(result)
            short_audition["trials"][0]["audition_seconds"][label] = 0.1
            with self.assertRaisesRegex(ValueError, "insufficient"):
                validate_result(short_audition, manifest, digest)

            with self.assertRaisesRegex(ValueError, "duplicate listener"):
                summarize_results(
                    [result, json.loads(json.dumps(result))],
                    manifest,
                    digest,
                    key,
                )


if __name__ == "__main__":
    unittest.main()
