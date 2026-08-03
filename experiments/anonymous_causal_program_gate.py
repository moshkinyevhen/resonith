"""Run the R-179 long-first anonymous causal program fast evidence gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from reference.maf_p0.anonymous_causal_program import (
    AnonymousCausalProgramLanguage,
    compile_anonymous_causal_program,
)
from reference.maf_p0.coherent_partial_bundle import CoherentPartialLanguage
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.wav_io import (
    read_pcm16_channels,
    write_pcm16_channels,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "experiments" / "results" / (
    "anonymous_causal_program_r179_2026-07-28.json"
)
ARTIFACTS = ROOT / "experiments" / "artifacts" / "r179-causal-program"
NATIVE = ROOT / "build" / "cpp23-clang22-ninja" / (
    "libresonith_core_shared.dll"
)


def _language() -> AnonymousCausalProgramLanguage:
    return AnonymousCausalProgramLanguage(
        partial_language=CoherentPartialLanguage(
            fft_samples=1024,
            hop_samples=256,
            minimum_fundamental_hz=50.0,
            maximum_fundamental_hz=1800.0,
            maximum_partials=24,
            minimum_harmonic_fraction=0.18,
            maximum_basis_clusters=16,
            minimum_cluster_observations=8,
        ),
        maximum_trajectory_observations=256,
        minimum_hold_frames=3,
        phase_candidates=16,
        maximum_normalized_error=0.65,
        dictionary_block_samples=512,
        dictionary_maximum_bases=32,
        dictionary_maximum_instances=1024,
        stochastic_segment_milliseconds=240.0,
        maximum_exact_columns=8,
        residual_budget_divisors=(1, 2),
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _save(report: dict) -> None:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    temporary = RESULT.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(RESULT)


def _run_one(
    identifier: str,
    path: Path,
    *,
    seconds: float | None,
    decoder: NativeMain0Decoder,
) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    if seconds is not None:
        samples = samples[: round(sample_rate * seconds)]
    started = time.perf_counter()
    candidate = compile_anonymous_causal_program(
        samples,
        sample_rate,
        native_decoder=decoder,
        coefficients_per_frame=64,
        half_window=512,
        band_count=24,
        language=_language(),
    )
    wall = time.perf_counter() - started
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    encoded = ARTIFACTS / f"{identifier}-selected.resonith"
    decoded = ARTIFACTS / f"{identifier}-selected-decoded.wav"
    encoded.write_bytes(candidate.selected_payload)
    write_pcm16_channels(
        decoded,
        sample_rate,
        candidate.selected_reconstruction,
    )
    return {
        "id": identifier,
        "path": str(path),
        "duration_seconds": samples.shape[0] / sample_rate,
        "sample_rate": sample_rate,
        "frames": int(samples.shape[0]),
        "channels": int(samples.shape[1]),
        "source_sha256": _sha256(samples.astype("<i2").tobytes()),
        "selected_encoded_path": str(encoded),
        "selected_encoded_sha256": _sha256(candidate.selected_payload),
        "selected_decoded_path": str(decoded),
        "selected_decoded_sha256": _sha256(
            candidate.selected_reconstruction.astype("<i2").tobytes()
        ),
        "wall_seconds": wall,
        "report": candidate.report,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--long-only",
        action="store_true",
        help="stop after freezing the first 120-second Mozart frontier",
    )
    parser.add_argument(
        "--mozart",
        type=Path,
        required=True,
        help="path to the public full-length Mozart WAV reference",
    )
    args = parser.parse_args()
    decoder = NativeMain0Decoder(NATIVE)
    report = {
        "schema": "resonith-r179-anonymous-causal-program-gate-1",
        "status": "running-long",
        "claim_boundary": (
            "real PCM complete-program fast gate; not R-118 or Opus evidence"
        ),
        "test_order": ["long", "freeze-long", "short"],
        "long_frontier_frozen": False,
        "long_results": [],
        "short_results": [],
    }
    _save(report)
    report["long_results"].append(
        _run_one(
            "mozart-120s",
            args.mozart,
            seconds=120.0,
            decoder=decoder,
        )
    )
    report["long_frontier_frozen"] = True
    report["status"] = "long-complete"
    _save(report)
    if args.long_only:
        return
    report["status"] = "running-short"
    _save(report)
    for identifier, path in (
        (
            "ebu-female-speech-en",
            ROOT / "artifacts" / "corpus" / "prepared-r111"
            / "ebu-female-speech-en.wav",
        ),
        (
            "ebu-dense-orchestra",
            ROOT / "artifacts" / "corpus" / "prepared-r111"
            / "ebu-dense-orchestra.wav",
        ),
        (
            "ebu-pink-noise",
            ROOT / "artifacts" / "corpus" / "prepared-r111"
            / "ebu-pink-noise.wav",
        ),
    ):
        report["short_results"].append(
            _run_one(
                identifier,
                path,
                seconds=12.0,
                decoder=decoder,
            )
        )
        _save(report)
    report["status"] = "complete-fast-diagnostic"
    _save(report)


if __name__ == "__main__":
    main()
