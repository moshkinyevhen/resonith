#!/usr/bin/env python3
"""Run the R-174 exact causal-law grammar long-first byte diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from reference.maf_p0.causal_law_grammar import (
    CausalLawGrammarLanguage,
    encode_causal_law_tokens,
)
from reference.maf_p0.causal_sequence_atlas import (
    canonicalize_causal_events,
    causal_events_from_lane_observations,
    factorized_causal_event_laws,
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
    ROOT / "experiments/results/causal_law_grammar_r174_2026-07-27.json"
)


def _pcm_hash(values: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(values, dtype="<i2").tobytes()
    ).hexdigest()


def _analyze(
    path: Path,
    maximum_seconds: float,
    grammar_language: CausalLawGrammarLanguage,
) -> dict:
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
    lane_events = causal_events_from_lane_observations(
        field.lane_observations,
        hop_samples=partial_language.hop_samples,
        phase_modulus=256,
        pitch_step_cents=5.0,
        gain_step_db=0.25,
        envelope_bins=256,
        resonator_step_cents=25.0,
        route_gain_step_db=0.25,
    )
    law_events = factorized_causal_event_laws(lane_events)

    grammar_started = time.perf_counter()
    law_results = {}
    for law_name, events in law_events.items():
        streams = canonicalize_causal_events(events, phase_modulus=256)
        stream = next(
            (
                item
                for item in streams
                if item.mode == "constant-offset/first-difference"
            ),
            None,
        )
        tokens = stream.tokens if stream is not None else ()
        candidate = encode_causal_law_tokens(
            tokens,
            language=grammar_language,
        )
        law_results[law_name] = {
            **candidate.report,
            "event_origin_offset": (
                stream.event_origin_offset if stream is not None else 0
            ),
            "decoded_token_sha256": hashlib.sha256(
                repr(candidate.decoded_tokens).encode("utf-8")
            ).hexdigest(),
        }
    grammar_seconds = time.perf_counter() - grammar_started
    raw_bytes = sum(item["raw_bytes"] for item in law_results.values())
    selected_bytes = sum(
        item["selected_bytes"] for item in law_results.values()
    )
    source_hash = _pcm_hash(source)
    reconstruction_hash = _pcm_hash(field.reconstruction)
    return {
        "id": path.stem,
        "path": str(path),
        "status": (
            "Real PCM / Exact factorized token-ledger byte diagnostic / "
            "not complete-stream compression"
        ),
        "sample_rate": sample_rate,
        "channels": int(source.shape[1]),
        "frames": int(source.shape[0]),
        "duration_seconds": source.shape[0] / sample_rate,
        "source_sha256": source_hash,
        "reconstruction_sha256": reconstruction_hash,
        "exact_audio_reconstruction": source_hash == reconstruction_hash,
        "law_count": len(law_results),
        "raw_token_ledger_bytes": raw_bytes,
        "selected_token_ledger_bytes": selected_bytes,
        "token_ledger_delta_bytes": selected_bytes - raw_bytes,
        "token_ledger_delta_fraction": (
            selected_bytes / raw_bytes - 1.0 if raw_bytes else 0.0
        ),
        "law_results": law_results,
        "lane_wall_seconds": lane_seconds,
        "grammar_wall_seconds": grammar_seconds,
        "total_wall_seconds": lane_seconds + grammar_seconds,
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
    parser.add_argument("--maximum-rules", type=int, default=32)
    parser.add_argument("--candidate-pairs", type=int, default=8)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    grammar_language = CausalLawGrammarLanguage(
        minimum_pair_occurrences=3,
        maximum_rules=arguments.maximum_rules,
        maximum_candidate_pairs_per_round=arguments.candidate_pairs,
    )
    payload = {
        "schema": "resonith-r174-causal-law-grammar-gate-1",
        "status": "running-long",
        "test_order": ["long", "freeze-long", "short"],
        "claim_boundary": (
            "factorized canonical token-ledger bytes only; no Resonith or "
            "Opus compression claim"
        ),
        "grammar_language": {
            "minimum_pair_occurrences": (
                grammar_language.minimum_pair_occurrences
            ),
            "maximum_rules": grammar_language.maximum_rules,
            "maximum_candidate_pairs_per_round": (
                grammar_language.maximum_candidate_pairs_per_round
            ),
        },
        "long_results": [],
        "short_results": [],
    }
    _write(payload, arguments.output)

    long_path = arguments.long_input.resolve()
    print(f"R-174 long-first: {long_path.name}", flush=True)
    long_result = _analyze(
        long_path,
        arguments.long_seconds,
        grammar_language,
    )
    payload["long_results"].append(long_result)
    payload["long_frontier_frozen"] = True
    payload["status"] = "long-frozen-short-running"
    _write(payload, arguments.output)
    print(
        "  long frozen "
        f"raw={long_result['raw_token_ledger_bytes']} "
        f"selected={long_result['selected_token_ledger_bytes']} "
        f"delta={long_result['token_ledger_delta_fraction']:+.6%} "
        f"wall={long_result['total_wall_seconds']:.3f}s",
        flush=True,
    )

    for path in arguments.short_inputs:
        short_path = path.resolve()
        print(f"R-174 short-second: {short_path.name}", flush=True)
        result = _analyze(
            short_path,
            arguments.short_seconds,
            grammar_language,
        )
        payload["short_results"].append(result)
        _write(payload, arguments.output)
        print(
            "  short "
            f"raw={result['raw_token_ledger_bytes']} "
            f"selected={result['selected_token_ledger_bytes']} "
            f"delta={result['token_ledger_delta_fraction']:+.6%} "
            f"wall={result['total_wall_seconds']:.3f}s",
            flush=True,
        )
    payload["status"] = "complete-fast-diagnostic"
    _write(payload, arguments.output)
    print(f"Wrote {arguments.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
