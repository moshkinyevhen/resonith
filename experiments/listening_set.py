"""Deterministic opaque WAV sets for informal blind codec listening."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil


CLIP_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LISTENING_APP = Path(__file__).with_name("listening_app")
REFERENCE_ALIASES = ("source", "reference", "hidden-reference")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def create_blinded_listening_set(
    inputs: dict[str, dict[str, Path]],
    output_directory: Path,
    *,
    seed: str,
    reference_candidate: str | None = None,
) -> tuple[dict, dict]:
    """Create a synchronized offline blind set and separate answer key."""

    if not seed:
        raise ValueError("listening-set seed must not be empty")
    output_directory.mkdir(parents=True, exist_ok=True)
    trials = []
    answer_trials = []
    for clip_id, candidates in sorted(inputs.items()):
        if CLIP_ID.fullmatch(clip_id) is None:
            raise ValueError("clip ID is unsafe for a listening-set path")
        if not 2 <= len(candidates) <= 26:
            raise ValueError("a listening trial requires 2 through 26 candidates")
        for name, path in candidates.items():
            if not name or not path.is_file():
                raise ValueError("listening candidate is missing")
        selected_reference = reference_candidate
        if selected_reference is None:
            matches = [
                name for name in REFERENCE_ALIASES if name in candidates
            ]
            if len(matches) != 1:
                raise ValueError(
                    "exactly one source/reference candidate is required"
                )
            selected_reference = matches[0]
        if selected_reference not in candidates:
            raise ValueError("reference candidate is missing")

        ordered_names = sorted(
            candidates,
            key=lambda name: hashlib.sha256(
                f"{seed}\0{clip_id}\0{name}".encode("utf-8")
            ).digest(),
        )
        trial_directory = output_directory / clip_id
        trial_directory.mkdir(parents=True, exist_ok=True)
        reference_path = trial_directory / "reference.wav"
        shutil.copyfile(candidates[selected_reference], reference_path)
        opaque = []
        answers = {}
        for index, name in enumerate(ordered_names):
            label = chr(ord("A") + index)
            destination = trial_directory / f"{label}.wav"
            shutil.copyfile(candidates[name], destination)
            opaque.append(
                {
                    "label": label,
                    "path": f"{clip_id}/{label}.wav",
                    "sha256": _sha256(destination),
                }
            )
            answers[label] = name
        trials.append(
            {
                "clip_id": clip_id,
                "reference": {
                    "path": f"{clip_id}/reference.wav",
                    "sha256": _sha256(reference_path),
                },
                "candidates": opaque,
            }
        )
        answer_trials.append(
            {
                "clip_id": clip_id,
                "reference_identity": selected_reference,
                "answers": answers,
            }
        )

    manifest = {
        "schema": "resonith-blind-listening-2",
        "protocol": {
            "score_minimum": 0,
            "score_maximum": 100,
            "minimum_audition_seconds": 0.5,
            "switching": "shared-clock-continuous-position",
            "formal_mushra_claim": False,
        },
        "instructions": (
            "Use identical playback gain. Audition the named reference and "
            "every opaque condition on the shared clock. Score overall "
            "quality, timbre, attacks, spatial stability, and noise before "
            "opening the separate answer key."
        ),
        "trials": trials,
    }
    answer_key = {
        "schema": "resonith-blind-listening-key-1",
        "seed": seed,
        "trials": answer_trials,
    }
    (output_directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_directory / "answer-key.json").write_text(
        json.dumps(answer_key, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for asset in ("index.html", "style.css", "app.js"):
        shutil.copyfile(LISTENING_APP / asset, output_directory / asset)
    (output_directory / "RUN_LISTENING.md").write_text(
        "# Run the Resonith blind listening set\n\n"
        "Do not open `answer-key.json` until every listener has exported a "
        "result.\n\n"
        "From this directory, start a local static server:\n\n"
        "```sh\n"
        "python -m http.server 8765\n"
        "```\n\n"
        "Then open `http://127.0.0.1:8765/` in a modern browser. The app has "
        "no network service, analytics, or upload path. Each listener exports "
        "one manifest-bound JSON result locally.\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest, answer_key
