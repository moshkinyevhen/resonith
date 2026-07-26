"""Deterministic opaque WAV sets for informal blind codec listening."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil


CLIP_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


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
) -> tuple[dict, dict]:
    """Copy candidate WAVs under opaque labels and write a separate key."""

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

        ordered_names = sorted(
            candidates,
            key=lambda name: hashlib.sha256(
                f"{seed}\0{clip_id}\0{name}".encode("utf-8")
            ).digest(),
        )
        trial_directory = output_directory / clip_id
        trial_directory.mkdir(parents=True, exist_ok=True)
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
        trials.append({"clip_id": clip_id, "candidates": opaque})
        answer_trials.append({"clip_id": clip_id, "answers": answers})

    manifest = {
        "schema": "resonith-blind-listening-1",
        "instructions": (
            "Use identical playback gain. Score timbre, attacks, spatial "
            "stability, noise, and preference before opening the answer key."
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
    return manifest, answer_key
