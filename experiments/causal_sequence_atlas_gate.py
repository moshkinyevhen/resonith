#!/usr/bin/env python3
"""Run the R-167/R-171 causal-lane sequence atlas long-first diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from reference.maf_p0.causal_sequence_atlas import (
    CausalAtlasLanguage,
    build_causal_sequence_atlas,
    causal_events_from_partial_bases,
)
from reference.maf_p0.coherent_partial_bundle import (
    CoherentPartialLanguage,
    infer_causal_lane_field,
)
from reference.maf_p0.wav_io import read_pcm16_channels


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
DEFAULT_OUTPUT = (
    ROOT / "experiments/results/causal_sequence_atlas_r171_2026-07-27.json"
)


def _pcm_hash(values: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(values, dtype="<i2").tobytes()
    ).hexdigest()


def _analyze(path: Path, maximum_seconds: float) -> dict:
    sample_rate, samples = read_pcm16_channels(path)
    frame_count = min(
        samples.shape[0],
        int(round(maximum_seconds * sample_rate)),
    )
    source = samples[:frame_count].copy()
    partial_language = CoherentPartialLanguage(
        fft_samples=1024,
        hop_samples=256,
        minimum_fundamental_hz=50.0,
        maximum_fundamental_hz=1800.0,
        maximum_partials=24,
        harmonic_bin_radius=1,
        minimum_harmonic_fraction=0.22,
        transient_flux_quantile=0.94,
        inharmonic_peak_quantile=0.88,
    )
    lane_started = time.perf_counter()
    field = infer_causal_lane_field(
        source,
        sample_rate=sample_rate,
        language=partial_language,
    )
    lane_seconds = time.perf_counter() - lane_started

    events = causal_events_from_partial_bases(
        field.bases,
        hop_samples=partial_language.hop_samples,
        phase_modulus=256,
        pitch_step_cents=5.0,
        gain_step_db=0.25,
        envelope_bins=256,
    )
    atlas_started = time.perf_counter()
    atlas = build_causal_sequence_atlas(
        events,
        language=CausalAtlasLanguage(
            minimum_sequence_events=3,
            minimum_occurrences=2,
            phase_modulus=256,
            maximum_reported_occurrence_positions=128,
        ),
    )
    atlas_seconds = time.perf_counter() - atlas_started
    candidates_by_mode = {}
    for candidate in atlas.candidates:
        item = candidates_by_mode.setdefault(
            candidate.mode,
            {
                "candidate_class_count": 0,
                "maximum_event_count": 0,
                "maximum_occurrence_count": 0,
                "covered_candidate_length_count": 0,
            },
        )
        item["candidate_class_count"] += 1
        item["maximum_event_count"] = max(
            item["maximum_event_count"],
            candidate.maximum_event_count,
        )
        item["maximum_occurrence_count"] = max(
            item["maximum_occurrence_count"],
            candidate.occurrence_count,
        )
        item["covered_candidate_length_count"] += (
            candidate.maximum_event_count
            - candidate.minimum_event_count
            + 1
        )
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / Fast analytic sequence diagnostic / "
            "not complete-stream compression"
        ),
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_sha256": _pcm_hash(source),
        "reconstruction_sha256": _pcm_hash(field.reconstruction),
        "exact_reconstruction": bool(
            np.array_equal(field.reconstruction, source.astype(np.int64))
        ),
        "partial_language": {
            "fft_samples": partial_language.fft_samples,
            "hop_samples": partial_language.hop_samples,
            "minimum_fundamental_hz": (
                partial_language.minimum_fundamental_hz
            ),
            "maximum_fundamental_hz": (
                partial_language.maximum_fundamental_hz
            ),
            "maximum_partials": partial_language.maximum_partials,
        },
        "causal_quantization": {
            "pitch_step_cents": 5.0,
            "phase_bins": 256,
            "gain_step_db": 0.25,
            "envelope_bins": 256,
            "role": (
                "exact finite proposer alphabet; original parameters and "
                "audio remain decoder-verified by bounded laws plus Truth"
            ),
        },
        "causal_event_count": len(events),
        "candidate_classes_by_mode": candidates_by_mode,
        "lane_report": field.report,
        "atlas_report": atlas.report,
        "lane_wall_seconds": lane_seconds,
        "atlas_wall_seconds": atlas_seconds,
        "total_wall_seconds": lane_seconds + atlas_seconds,
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    payload = {
        "schema": "resonith-r171-causal-sequence-atlas-gate-1",
        "status": "running-long",
        "test_order": ["long", "freeze-long", "short"],
        "claim_boundary": (
            "sequence-discovery diagnostic; no bitrate or Opus claim"
        ),
        "long_results": [],
        "short_results": [],
    }
    _write(payload, arguments.output)

    long_path = arguments.long_input.resolve()
    print(f"R-171 long-first: {long_path.name}", flush=True)
    long_result = _analyze(long_path, arguments.long_seconds)
    payload["long_results"].append(long_result)
    payload["long_frontier_frozen"] = True
    payload["status"] = "long-frozen-short-running"
    _write(payload, arguments.output)
    print(
        "  long frozen "
        f"events={long_result['causal_event_count']} "
        f"classes={long_result['atlas_report']['candidate_class_count']} "
        f"wall={long_result['total_wall_seconds']:.3f}s",
        flush=True,
    )

    for path in arguments.short_inputs:
        short_path = path.resolve()
        print(f"R-171 short-second: {short_path.name}", flush=True)
        result = _analyze(short_path, arguments.short_seconds)
        payload["short_results"].append(result)
        _write(payload, arguments.output)
        print(
            "  short "
            f"events={result['causal_event_count']} "
            f"classes={result['atlas_report']['candidate_class_count']} "
            f"wall={result['total_wall_seconds']:.3f}s",
            flush=True,
        )
    payload["status"] = "complete-fast-diagnostic"
    _write(payload, arguments.output)
    print(f"Wrote {arguments.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
