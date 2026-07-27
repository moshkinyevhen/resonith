"""Compare GPT-5.6 Sol max/pro with Gemini and exact native Foundry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping
import urllib.error
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT))

from experiments.gemini_byte_pattern_gate import (  # noqa: E402
    _build_byte_pattern_prompt,
    _hex_blocks,
    _native_results,
    _real_blocks,
    _response_schema,
    _score_case,
    _synthetic_blocks,
)
from experiments.gemini_semantic_arbiter_gate import (  # noqa: E402
    _read_windows_credential,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402


OPENAI_API_ROOT = "https://api.openai.com"
DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_CREDENTIAL_TARGET = "Resonith/Provider/OpenAI/ApiKey"


def _openai_request(
    api_key: str,
    model: str,
    cases: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], float, int]:
    prompt = _build_byte_pattern_prompt(cases)
    request_body = json.dumps(
        {
            "model": model,
            "input": json.dumps(prompt, separators=(",", ":")),
            "reasoning": {
                "effort": "max",
                "mode": "pro",
            },
            "text": {
                "verbosity": "low",
                "format": {
                    "type": "json_schema",
                    "name": "resonith_byte_pattern_candidates",
                    "strict": True,
                    "schema": _response_schema(),
                },
            },
            "max_output_tokens": 16384,
            "store": False,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    started = time.perf_counter()
    request = urllib.request.Request(
        f"{OPENAI_API_ROOT}/v1/responses",
        data=request_body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response_stream:
            body = response_stream.read()
    except urllib.error.HTTPError as error:
        status = "unknown"
        message = "provider rejected the request"
        try:
            payload = json.loads(error.read(1 << 16))
            provider_error = payload.get("error", {})
            if isinstance(provider_error, Mapping):
                status = str(provider_error.get("code", status))
                message = " ".join(
                    str(provider_error.get("message", message)).split()
                )[:800]
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        raise RuntimeError(
            f"OpenAI byte-pattern analysis failed with HTTP "
            f"{error.code} ({status}): {message}"
        ) from None
    elapsed = time.perf_counter() - started
    response = json.loads(body)
    text_parts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, Mapping) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, Mapping)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                text_parts.append(content["text"])
    if len(text_parts) != 1:
        raise RuntimeError("OpenAI returned ambiguous byte-pattern output")
    usage = response.get("usage", {})
    if not isinstance(usage, Mapping):
        usage = {}
    return json.loads(text_parts[0]), dict(usage), elapsed, len(request_body)


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
            / "openai_byte_pattern_r153_2026-07-27.json"
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

    proposal, usage, provider_seconds, request_bytes = _openai_request(
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
        "schema": "resonith-r153-openai-byte-pattern-gate-1",
        "status": "measured proposer evidence; not a codec claim",
        "model": args.model,
        "reasoning_effort": "max",
        "reasoning_mode": "pro",
        "provider_input": "hexadecimal PCM16LE text; no audio MIME",
        "request_bytes": request_bytes,
        "usage": usage,
        "provider_seconds": provider_seconds,
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
