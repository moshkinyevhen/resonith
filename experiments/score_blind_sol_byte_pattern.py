"""Score the blind Codex Sol Ultra proposer with the R-152 CUDA authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))
sys.path.insert(0, str(ROOT))

from experiments.gemini_byte_pattern_gate import (  # noqa: E402
    _native_results,
    _real_blocks,
    _score_case,
    _synthetic_blocks,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case_map(proposal: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = {}
    for item in proposal.get("cases", []):
        if not isinstance(item, Mapping):
            continue
        case_id = item.get("case_id")
        candidates = item.get("candidates")
        if isinstance(case_id, str) and isinstance(candidates, list):
            cases[case_id] = [
                dict(candidate)
                for candidate in candidates
                if isinstance(candidate, Mapping)
            ]
    return cases


def _provider_neutral(report: dict[str, Any]) -> dict[str, Any]:
    return {
        (
            key.replace("gemini_", "sol_ultra_")
            if key.startswith("gemini_")
            else key
        ): value
        for key, value in report.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--blind-input", type=Path, required=True)
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
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "experiments"
            / "results"
            / "sol_ultra_byte_pattern_r154_2026-07-27.json"
        ),
    )
    args = parser.parse_args()

    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    proposed = _case_map(proposal)
    blocks_by_case = {
        "synthetic-known-laws": (_synthetic_blocks(), 0.0),
        "ebu-speech-bytes": (
            _real_blocks(args.speech, 61440, 12, 64),
            0.05,
        ),
    }
    if set(proposed) - set(blocks_by_case):
        raise ValueError("blind proposal contains an unknown case")

    foundry = GainPhaseCudaFoundry(
        args.foundry_library,
        args.nvrtc_directory,
    )
    reports = []
    for case_id, (blocks, threshold) in blocks_by_case.items():
        native, native_seconds = _native_results(
            foundry,
            np.asarray(blocks, dtype=np.int16),
            threshold,
        )
        report = _provider_neutral(
            _score_case(
                case_id,
                blocks,
                threshold,
                native,
                proposed.get(case_id, []),
            )
        )
        report["native_foundry_seconds"] = native_seconds
        reports.append(report)

    output = {
        "schema": "resonith-r154-sol-ultra-byte-pattern-gate-1",
        "status": (
            "measured blind Codex proposer evidence; "
            "not a Responses API or codec claim"
        ),
        "model": "gpt-5.6-sol",
        "reasoning_effort": "ultra",
        "execution_surface": "isolated Codex sub-agent",
        "provider_input": "hexadecimal PCM16LE text; no audio MIME",
        "blind_input_sha256": _sha256(args.blind_input),
        "proposal_sha256": _sha256(args.proposal),
        "cases": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
