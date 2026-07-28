#!/usr/bin/env python3
"""Run the R-176 CBF1 plus final Truth long-first fast diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from reference.maf_p0.causal_basis_truth_candidate import (
    encode_causal_basis_truth_candidate,
)
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.wav_io import (
    read_pcm16_channels,
    write_pcm16_channels,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LONG = (
    Path("G:/Orkela/comparison/public-benchmark-2026-07-26")
    / "mozart-original.wav"
)
DEFAULT_SHORT = (
    ROOT / "artifacts/corpus/prepared-r111/ebu-female-speech-en.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-dense-orchestra.wav",
    ROOT / "artifacts/corpus/prepared-r111/ebu-pink-noise.wav",
)
DEFAULT_NATIVE = (
    ROOT / "build/cpp23-clang22-ninja/libresonith_core_shared.dll"
)
DEFAULT_OUTPUT = (
    ROOT / "experiments/results/causal_basis_truth_r176_2026-07-27.json"
)
DEFAULT_ARTIFACTS = ROOT / "experiments/artifacts/r176-cbf-truth"


def _pcm_hash(values: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(values, dtype="<i2").tobytes()
    ).hexdigest()


def _analyze(
    path: Path,
    maximum_seconds: float,
    *,
    native_decoder: NativeMain0Decoder,
    artifacts: Path,
) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_count = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_count].copy()
    started = time.perf_counter()
    candidate = encode_causal_basis_truth_candidate(
        source,
        sample_rate,
        native_decoder=native_decoder,
        coefficients_per_frame=64,
        half_window=512,
        band_count=24,
        block_samples=1024,
        maximum_normalized_error=8.0e-2,
    )
    wall_seconds = time.perf_counter() - started
    artifacts.mkdir(parents=True, exist_ok=True)
    encoded_path = artifacts / f"{path.stem}-selected.resonith"
    decoded_path = artifacts / f"{path.stem}-selected-decoded.wav"
    encoded_path.write_bytes(candidate.selected_payload)
    write_pcm16_channels(
        decoded_path,
        sample_rate,
        candidate.selected_reconstruction,
    )
    source_hash = _pcm_hash(source)
    decoded_hash = _pcm_hash(candidate.selected_reconstruction)
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / Complete CBF1+Truth fast diagnostic / "
            "not R-118 or Opus comparison"
        ),
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_sha256": source_hash,
        "selected_decode_sha256": decoded_hash,
        "selected_is_pcm_exact": source_hash == decoded_hash,
        "selected_encoded_path": str(encoded_path),
        "selected_decoded_path": str(decoded_path),
        "selected_encoded_sha256": hashlib.sha256(
            candidate.selected_payload
        ).hexdigest(),
        "wall_seconds": wall_seconds,
        "report": candidate.report,
    }


def _write(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--long-input", type=Path, default=DEFAULT_LONG)
    parser.add_argument(
        "--short-inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_SHORT),
    )
    parser.add_argument("--long-seconds", type=float, default=120.0)
    parser.add_argument("--short-seconds", type=float, default=12.0)
    parser.add_argument("--native-core", type=Path, default=DEFAULT_NATIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    arguments = parser.parse_args()
    decoder = NativeMain0Decoder(arguments.native_core.resolve())
    payload = {
        "schema": "resonith-r176-causal-basis-truth-gate-1",
        "status": "running-long",
        "test_order": ["long", "freeze-long", "short"],
        "claim_boundary": (
            "complete CBF1 plus final Truth fast diagnostic; full R-118 and "
            "maximum-effort Opus pending"
        ),
        "long_results": [],
        "short_results": [],
    }
    _write(payload, arguments.output)

    long_path = arguments.long_input.resolve()
    print(f"R-176 long-first: {long_path.name}", flush=True)
    long_result = _analyze(
        long_path,
        arguments.long_seconds,
        native_decoder=decoder,
        artifacts=arguments.artifacts,
    )
    payload["long_results"].append(long_result)
    payload["long_frontier_frozen"] = True
    payload["status"] = "long-frozen-short-running"
    _write(payload, arguments.output)
    print(
        "  long frozen "
        f"selected={long_result['report']['selected_kind']} "
        f"bytes={long_result['report']['selected_bytes']} "
        f"wall={long_result['wall_seconds']:.3f}s",
        flush=True,
    )

    for path in arguments.short_inputs:
        short_path = path.resolve()
        print(f"R-176 short-second: {short_path.name}", flush=True)
        result = _analyze(
            short_path,
            arguments.short_seconds,
            native_decoder=decoder,
            artifacts=arguments.artifacts,
        )
        payload["short_results"].append(result)
        _write(payload, arguments.output)
        print(
            "  short "
            f"selected={result['report']['selected_kind']} "
            f"bytes={result['report']['selected_bytes']} "
            f"wall={result['wall_seconds']:.3f}s",
            flush=True,
        )
    payload["status"] = "complete-fast-diagnostic"
    _write(payload, arguments.output)
    print(f"Wrote {arguments.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
