"""A/B-test Gemini 3.6 Flash against the exact R-149 byte-pattern search.

Gemini receives hexadecimal PCM16LE blocks as text, never audio input. Native
Foundry remains the authority and verifies every returned relationship and
fixed-point parameter before metrics are computed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
from typing import Any, Mapping
import urllib.request
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT))

from experiments.gemini_semantic_arbiter_gate import (  # noqa: E402
    API_ROOT,
    DEFAULT_CREDENTIAL_TARGET,
    DEFAULT_MODEL,
    _read_windows_credential,
    _request,
    _sanitize_usage,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402


def _read_pcm16_mono(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2:
            raise ValueError("byte-pattern gate requires PCM16 WAV")
        channels = source.getnchannels()
        sample_rate = source.getframerate()
        frames = source.getnframes()
        payload = source.readframes(frames)
    matrix = np.frombuffer(payload, dtype="<i2").reshape(-1, channels)
    if channels == 1:
        mono = matrix[:, 0]
    else:
        mono = np.rint(matrix.astype(np.float64).mean(axis=1)).astype(np.int16)
    return sample_rate, np.ascontiguousarray(mono)


def _synthetic_blocks() -> np.ndarray:
    base = np.asarray(
        (1200, -3000, 4400, -2100, 700, 5100, -6200, 3300) * 2,
        dtype=np.int16,
    )
    phase = np.roll(base, -5)
    counter = np.negative(base, dtype=np.int16)
    half = np.rint(base.astype(np.float64) * 0.5).astype(np.int16)
    envelope = np.rint(
        base.astype(np.float64)
        * np.linspace(0.25, 0.9, base.size)
    ).astype(np.int16)
    unrelated = np.asarray(
        (
            19,
            -701,
            88,
            3001,
            -17,
            940,
            -4011,
            73,
            1900,
            42,
            -90,
            712,
            100,
            -200,
            300,
            -400,
        ),
        dtype=np.int16,
    )
    return np.vstack((base, phase, counter, half, envelope, unrelated))


def _real_blocks(path: Path, start: int, count: int, length: int) -> np.ndarray:
    _, mono = _read_pcm16_mono(path)
    end = start + count * length
    if start < 0 or end > mono.size:
        raise ValueError("real byte-pattern window exceeds the source")
    return mono[start:end].reshape(count, length).copy()


def _hex_blocks(blocks: np.ndarray) -> list[dict[str, Any]]:
    return [
        {
            "block_index": index,
            "pcm16le_hex": np.asarray(block, dtype="<i2").tobytes().hex(),
        }
        for index, block in enumerate(blocks)
    ]


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "case_id": {"type": "string"},
                        "candidates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "basis_index": {
                                        "type": "integer",
                                        "minimum": 0,
                                    },
                                    "target_index": {
                                        "type": "integer",
                                        "minimum": 0,
                                    },
                                    "source_offset": {
                                        "type": "integer",
                                        "minimum": 0,
                                    },
                                    "gain_q15": {
                                        "type": "integer",
                                        "minimum": -32768,
                                        "maximum": 32768,
                                    },
                                    "end_gain_q15": {
                                        "type": "integer",
                                        "minimum": -32768,
                                        "maximum": 32768,
                                    },
                                    "linear_gain": {"type": "boolean"},
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                },
                                "required": [
                                    "basis_index",
                                    "target_index",
                                    "source_offset",
                                    "gain_q15",
                                    "end_gain_q15",
                                    "linear_gain",
                                    "confidence",
                                ],
                            },
                        },
                    },
                    "required": ["case_id", "candidates"],
                },
            }
        },
        "required": ["cases"],
    }


def _gemini_request(
    api_key: str,
    model: str,
    cases: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, int], float, int]:
    prompt = _build_byte_pattern_prompt(cases)
    request_body = json.dumps(
        {
            "model": model,
            "input": [
                {
                    "type": "text",
                    "text": json.dumps(prompt, separators=(",", ":")),
                }
            ],
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": _response_schema(),
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    started = time.perf_counter()
    body, _ = _request(
        urllib.request.Request(
            f"{API_ROOT}/v1beta/interactions",
            data=request_body,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        ),
        operation="Gemini byte-pattern analysis",
    )
    elapsed = time.perf_counter() - started
    response = json.loads(body)
    text_parts: list[str] = []
    for output in response.get("outputs", []):
        if (
            isinstance(output, Mapping)
            and output.get("type") == "text"
            and isinstance(output.get("text"), str)
        ):
            text_parts.append(output["text"])
    for step in response.get("steps", []):
        if not isinstance(step, Mapping):
            continue
        for part in step.get("content", []):
            if (
                isinstance(part, Mapping)
                and part.get("type") == "text"
                and isinstance(part.get("text"), str)
            ):
                text_parts.append(part["text"])
    if len(text_parts) != 1:
        raise RuntimeError("Gemini returned ambiguous byte-pattern output")
    return (
        json.loads(text_parts[0]),
        _sanitize_usage(response.get("usage")),
        elapsed,
        len(request_body),
    )


def _build_byte_pattern_prompt(
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the provider-neutral R-152/R-153 comparison prompt."""

    return {
        "task": (
            "Find reusable mathematical relationships in byte sequences. "
            "Inputs are PCM16 little-endian hexadecimal bytes presented only "
            "as numbered blocks; do not interpret them as sound or use "
            "semantic audio knowledge. For every ordered unequal block pair, "
            "test every circular source offset. Fit signed Q1.15 constant gain "
            "and a Q1.15 gain linearly interpolated between the first and last "
            "sample. Q1.15 synthesis rounds halves away from zero. Return every "
            "relationship whose squared error / max(target energy,1) is at or "
            "below the case threshold. Never invent indices. For constant gain "
            "set end_gain_q15=0 and linear_gain=false. Prefer completeness over "
            "explanation and emit JSON only."
        ),
        "cases": cases,
    }


def _native_results(
    foundry: GainPhaseCudaFoundry,
    blocks: np.ndarray,
    threshold: float,
) -> tuple[np.ndarray, float]:
    """Return the exact forward transform language declared in the prompt.

    The production Foundry may grow additional transform flags. R-152/R-154
    remain frozen to circular offset plus constant/linear gain, so later
    reverse candidates must not silently change the comparison authority.
    """

    started = time.perf_counter()
    rows = np.concatenate(
        [
            tile
            for tile, _ in foundry.evaluate_tiles(
                blocks,
                tile_candidates=1 << 16,
            )
        ]
    )
    elapsed = time.perf_counter() - started
    rows = _prompt_language_rows(rows)
    eligible = rows[
        rows["squared_error"].astype(np.float64)
        <= np.maximum(rows["target_energy"], 1).astype(np.float64) * threshold
    ]
    return eligible, elapsed


def _prompt_language_rows(rows: np.ndarray) -> np.ndarray:
    """Freeze R-152/R-154 to the transforms named in their blind prompt."""

    return rows[(rows["transform_flags"] & 2) == 0]


def _score_case(
    case_id: str,
    blocks: np.ndarray,
    threshold: float,
    native_rows: np.ndarray,
    proposed: list[dict[str, Any]],
) -> dict[str, Any]:
    native_by_relation = {
        (
            int(row["basis_index"]),
            int(row["target_index"]),
            int(row["source_offset"]),
        ): row
        for row in native_rows
    }
    best_error_by_target: dict[int, int] = {}
    for row in native_rows:
        target = int(row["target_index"])
        error = int(row["squared_error"])
        best_error_by_target[target] = min(
            error,
            best_error_by_target.get(target, error),
        )

    valid = 0
    eligible_relations: set[tuple[int, int, int]] = set()
    exact_parameters = 0
    best_targets: set[int] = set()
    for item in proposed:
        basis = int(item["basis_index"])
        target = int(item["target_index"])
        offset = int(item["source_offset"])
        if (
            basis == target
            or not 0 <= basis < blocks.shape[0]
            or not 0 <= target < blocks.shape[0]
            or not 0 <= offset < blocks.shape[1]
        ):
            continue
        valid += 1
        relation = (basis, target, offset)
        native = native_by_relation.get(relation)
        if native is None:
            continue
        eligible_relations.add(relation)
        native_linear = bool(int(native["transform_flags"]) & 1)
        if (
            int(item["gain_q15"]) == int(native["gain_q15"])
            and bool(item["linear_gain"]) == native_linear
            and int(item["end_gain_q15"])
            == (
                int(native["end_gain_q15"])
                if native_linear
                else 0
            )
        ):
            exact_parameters += 1
        if int(native["squared_error"]) == best_error_by_target[target]:
            best_targets.add(target)

    native_relations = set(native_by_relation)
    targets_with_native = set(best_error_by_target)
    return {
        "case_id": case_id,
        "block_count": int(blocks.shape[0]),
        "block_samples": int(blocks.shape[1]),
        "input_sha256": hashlib.sha256(
            np.asarray(blocks, dtype="<i2").tobytes()
        ).hexdigest(),
        "maximum_normalized_error": threshold,
        "native_eligible_candidate_count": len(native_relations),
        "native_target_count": len(targets_with_native),
        "gemini_proposal_count": len(proposed),
        "gemini_valid_index_count": valid,
        "gemini_eligible_relation_count": len(eligible_relations),
        "gemini_exact_parameter_count": exact_parameters,
        "eligible_relation_precision": (
            len(eligible_relations) / valid if valid else 0.0
        ),
        "eligible_relation_recall": (
            len(eligible_relations) / len(native_relations)
            if native_relations
            else 1.0
        ),
        "best_target_recall": (
            len(best_targets) / len(targets_with_native)
            if targets_with_native
            else 1.0
        ),
        "exact_parameter_rate_on_eligible": (
            exact_parameters / len(eligible_relations)
            if eligible_relations
            else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundry-library", type=Path, required=True)
    parser.add_argument("--nvrtc-directory", type=Path, required=True)
    parser.add_argument(
        "--speech",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "corpus"
            / "prepared-r111"
            / "ebu-female-speech-en.wav"
        ),
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--credential-target",
        default=DEFAULT_CREDENTIAL_TARGET,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "experiments"
            / "results"
            / "gemini_byte_pattern_r152_2026-07-27.json"
        ),
    )
    args = parser.parse_args()

    blocks_by_case = {
        "synthetic-known-laws": (_synthetic_blocks(), 0.0),
        "ebu-speech-bytes": (
            _real_blocks(args.speech, 61440, 12, 64),
            0.05,
        ),
    }
    foundry = GainPhaseCudaFoundry(
        args.foundry_library,
        args.nvrtc_directory,
    )
    native: dict[str, np.ndarray] = {}
    native_seconds: dict[str, float] = {}
    request_cases = []
    for case_id, (blocks, threshold) in blocks_by_case.items():
        native[case_id], native_seconds[case_id] = _native_results(
            foundry,
            blocks,
            threshold,
        )
        request_cases.append(
            {
                "case_id": case_id,
                "format": "PCM16LE_HEX",
                "block_samples": int(blocks.shape[1]),
                "maximum_normalized_error": threshold,
                "blocks": _hex_blocks(blocks),
            }
        )

    proposal, usage, gemini_seconds, request_bytes = _gemini_request(
        _read_windows_credential(args.credential_target),
        args.model,
        request_cases,
    )
    proposed_cases = {
        str(item["case_id"]): list(item["candidates"])
        for item in proposal.get("cases", [])
        if isinstance(item, Mapping)
        and isinstance(item.get("candidates"), list)
    }
    case_reports = []
    for case_id, (blocks, threshold) in blocks_by_case.items():
        report = _score_case(
            case_id,
            blocks,
            threshold,
            native[case_id],
            proposed_cases.get(case_id, []),
        )
        report["native_foundry_seconds"] = native_seconds[case_id]
        case_reports.append(report)
    output = {
        "schema": "resonith-r152-gemini-byte-pattern-gate-1",
        "status": "measured proposer evidence; not a codec claim",
        "model": args.model,
        "provider_input": "hexadecimal PCM16LE text; no audio MIME",
        "request_bytes": request_bytes,
        "usage": usage,
        "gemini_seconds": gemini_seconds,
        "cases": case_reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
