"""Validate and descriptively summarize manifest-bound blind listening results."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any


RESULT_SCHEMA = "resonith-blind-listening-result-1"
MANIFEST_SCHEMA = "resonith-blind-listening-2"
KEY_SCHEMA = "resonith-blind-listening-key-1"
PLAYBACK_SETUPS = {"headphones", "speakers", "other"}
ARTIFACT_TAGS = {"pre-echo", "timbre", "noise", "spatial", "other"}


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    payload = path.read_bytes()
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value, payload


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _trial_maps(
    manifest: dict[str, Any],
) -> tuple[list[str], dict[str, list[str]], float]:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("unsupported listening manifest schema")
    trials = manifest.get("trials")
    if not isinstance(trials, list) or not trials:
        raise ValueError("manifest must contain trials")
    clip_ids: list[str] = []
    labels_by_clip: dict[str, list[str]] = {}
    for trial in trials:
        if not isinstance(trial, dict):
            raise ValueError("manifest trial must be an object")
        clip_id = trial.get("clip_id")
        candidates = trial.get("candidates")
        reference = trial.get("reference")
        if (
            not isinstance(clip_id, str)
            or clip_id in labels_by_clip
            or not isinstance(candidates, list)
            or not isinstance(reference, dict)
            or not isinstance(reference.get("path"), str)
        ):
            raise ValueError("malformed or duplicate manifest trial")
        labels = [candidate.get("label") for candidate in candidates]
        if (
            not labels
            or any(not isinstance(label, str) for label in labels)
            or len(set(labels)) != len(labels)
        ):
            raise ValueError("manifest candidate labels must be unique strings")
        clip_ids.append(clip_id)
        labels_by_clip[clip_id] = labels
    minimum = manifest.get("protocol", {}).get(
        "minimum_audition_seconds",
        0.5,
    )
    if not _is_number(minimum) or float(minimum) < 0:
        raise ValueError("invalid minimum audition time")
    return clip_ids, labels_by_clip, float(minimum)


def validate_result(
    result: dict[str, Any],
    manifest: dict[str, Any],
    manifest_sha256: str,
) -> None:
    """Reject incomplete, unbound, or structurally ambiguous result data."""

    clip_ids, labels_by_clip, minimum_audition = _trial_maps(manifest)
    if result.get("schema") != RESULT_SCHEMA:
        raise ValueError("unsupported listening result schema")
    if result.get("manifest_sha256") != manifest_sha256:
        raise ValueError("result is bound to a different manifest")
    listener_id = result.get("listener_id")
    if (
        not isinstance(listener_id, str)
        or not listener_id.strip()
        or len(listener_id) > 64
    ):
        raise ValueError("listener ID must contain 1 through 64 characters")
    if result.get("playback_setup") not in PLAYBACK_SETUPS:
        raise ValueError("unsupported playback setup")
    trials = result.get("trials")
    if not isinstance(trials, list) or len(trials) != len(clip_ids):
        raise ValueError("result must contain every manifest trial exactly once")
    result_clips = [trial.get("clip_id") for trial in trials]
    if result_clips != clip_ids:
        raise ValueError("result trial order or identity does not match manifest")

    for trial in trials:
        clip_id = trial["clip_id"]
        labels = labels_by_clip[clip_id]
        expected = set(labels)
        scores = trial.get("scores")
        auditions = trial.get("audition_seconds")
        artifacts = trial.get("artifacts")
        notes = trial.get("notes")
        if not all(
            isinstance(value, dict)
            for value in (scores, auditions, artifacts, notes)
        ):
            raise ValueError(f"{clip_id}: result maps are missing")
        if set(scores) != expected:
            raise ValueError(f"{clip_id}: every candidate needs one score")
        for label, score in scores.items():
            if not _is_number(score) or not 0 <= float(score) <= 100:
                raise ValueError(f"{clip_id}/{label}: score is outside 0..100")
        if set(auditions) != expected | {"reference"}:
            raise ValueError(f"{clip_id}: audition labels do not match manifest")
        for label, seconds in auditions.items():
            if (
                not _is_number(seconds)
                or float(seconds) < minimum_audition
            ):
                raise ValueError(
                    f"{clip_id}/{label}: insufficient audition time"
                )
        switch_count = trial.get("switch_count")
        if (
            not isinstance(switch_count, int)
            or isinstance(switch_count, bool)
            or switch_count < 0
        ):
            raise ValueError(f"{clip_id}: invalid switch count")
        if set(artifacts) != expected or set(notes) != expected:
            raise ValueError(f"{clip_id}: annotation labels do not match")
        for label in labels:
            tags = artifacts[label]
            note = notes[label]
            if (
                not isinstance(tags, list)
                or len(tags) != len(set(tags))
                or any(tag not in ARTIFACT_TAGS for tag in tags)
                or not isinstance(note, str)
                or len(note) > 500
            ):
                raise ValueError(f"{clip_id}/{label}: invalid annotations")


def _validated_key(
    answer_key: dict[str, Any],
    clip_ids: list[str],
    labels_by_clip: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    if answer_key.get("schema") != KEY_SCHEMA:
        raise ValueError("unsupported answer-key schema")
    key_trials = answer_key.get("trials")
    if not isinstance(key_trials, list):
        raise ValueError("answer key must contain trials")
    by_clip: dict[str, dict[str, Any]] = {}
    for trial in key_trials:
        if not isinstance(trial, dict):
            raise ValueError("answer-key trial must be an object")
        clip_id = trial.get("clip_id")
        answers = trial.get("answers")
        reference_identity = trial.get("reference_identity")
        if (
            clip_id not in labels_by_clip
            or clip_id in by_clip
            or not isinstance(answers, dict)
            or list(answers) != labels_by_clip[clip_id]
            or any(not isinstance(value, str) for value in answers.values())
            or not isinstance(reference_identity, str)
        ):
            raise ValueError("answer key does not match manifest labels")
        by_clip[clip_id] = trial
    if list(by_clip) != clip_ids:
        raise ValueError("answer-key trial order does not match manifest")
    return by_clip


def summarize_results(
    results: list[dict[str, Any]],
    manifest: dict[str, Any],
    manifest_sha256: str,
    answer_key: dict[str, Any],
) -> dict[str, Any]:
    """Unblind valid sessions and emit descriptive, non-inferential evidence."""

    if not results:
        raise ValueError("at least one result is required")
    clip_ids, labels_by_clip, _minimum = _trial_maps(manifest)
    key_by_clip = _validated_key(answer_key, clip_ids, labels_by_clip)
    listener_ids: set[str] = set()
    scores: dict[str, list[float]] = defaultdict(list)
    artifacts: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    hidden_reference_scores: list[float] = []
    observations = 0
    for result in results:
        validate_result(result, manifest, manifest_sha256)
        listener_id = result["listener_id"].strip()
        if listener_id in listener_ids:
            raise ValueError(f"duplicate listener ID: {listener_id}")
        listener_ids.add(listener_id)
        for trial in result["trials"]:
            clip_id = trial["clip_id"]
            key_trial = key_by_clip[clip_id]
            for label, score in trial["scores"].items():
                identity = key_trial["answers"][label]
                numeric_score = float(score)
                scores[identity].append(numeric_score)
                observations += 1
                if identity == key_trial["reference_identity"]:
                    hidden_reference_scores.append(numeric_score)
                for tag in trial["artifacts"][label]:
                    artifacts[identity][tag] += 1

    conditions = {}
    for identity in sorted(scores):
        values = scores[identity]
        conditions[identity] = {
            "observations": len(values),
            "mean_score": statistics.fmean(values),
            "median_score": statistics.median(values),
            "minimum_score": min(values),
            "maximum_score": max(values),
            "sample_standard_deviation": (
                statistics.stdev(values) if len(values) >= 2 else None
            ),
            "artifact_counts": dict(sorted(artifacts[identity].items())),
        }
    return {
        "schema": "resonith-blind-listening-summary-1",
        "manifest_sha256": manifest_sha256,
        "listener_count": len(listener_ids),
        "clip_count": len(clip_ids),
        "score_observations": observations,
        "conditions": conditions,
        "hidden_reference_screening": {
            "observations": len(hidden_reference_scores),
            "mean_score": statistics.fmean(hidden_reference_scores),
            "scores_below_90": sum(
                score < 90 for score in hidden_reference_scores
            ),
            "automatic_listener_exclusion": False,
        },
        "interpretation": (
            "Descriptive only. Do not claim matched MUSHRA significance "
            "without a preregistered panel, anchors, and statistical analysis."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest, manifest_payload = _read_json(args.manifest)
    answer_key, _key_payload = _read_json(args.answer_key)
    result_values = [_read_json(path)[0] for path in args.results]
    summary = summarize_results(
        result_values,
        manifest,
        _sha256(manifest_payload),
        answer_key,
    )
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
