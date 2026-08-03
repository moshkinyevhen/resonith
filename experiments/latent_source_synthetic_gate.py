#!/usr/bin/env python3
"""Reproduce the constructive R-159/R-160 changing-overlap gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from reference.maf_p0.latent_source_field import (
    LatentSourceLanguage,
    infer_latent_source_pattern_field,
)
from reference.maf_p0.sparse_motif_grammar import (
    SparseMotifLanguage,
    SparsePathLanguage,
    pack_latent_field_event_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/results/latent_source_pattern_field_r160_synthetic_2026-07-27.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    rng = np.random.default_rng(160)
    index = np.arange(128)
    basis = np.rint(
        7000.0 * np.sin(
            2.0 * np.pi * (0.021 * index + 0.000037 * index**2)
        )
        + 2200.0 * np.sin(2.0 * np.pi * 0.113 * index)
    ).astype(np.int16)
    samples = rng.integers(-19, 20, size=(1760, 1), dtype=np.int16)
    starts = tuple(16 + 168 * occurrence for occurrence in range(10))
    gains_q15 = (
        19000,
        23000,
        27000,
        31000,
        35000,
        39000,
        43000,
        37000,
        29000,
        25000,
    )
    for occurrence, (start, gain_q15) in enumerate(zip(starts, gains_q15)):
        product = basis.astype(np.int64) * gain_q15
        rendered = np.where(
            product >= 0,
            (product + 16384) // 32768,
            -((-product + 16384) // 32768),
        ).astype(np.int16)
        samples[start : start + basis.size, 0] = np.clip(
            samples[start : start + basis.size, 0].astype(np.int32)
                + rendered,
            -32768,
            32767,
        ).astype(np.int16)
        contaminated = (
            np.arange(occurrence * 11, occurrence * 11 + 11) % basis.size
        )
        samples[start + contaminated, 0] = np.clip(
            samples[start + contaminated, 0].astype(np.int32)
                + rng.integers(-140, 141, size=contaminated.size),
            -32768,
            32767,
        ).astype(np.int16)

    result = infer_latent_source_pattern_field(
        samples,
        language=LatentSourceLanguage(
            scales=(128,),
            origin_hop=4,
            minimum_occurrences=6,
            maximum_components=2,
            maximum_cluster_members=12,
            maximum_lag=3,
            minimum_spectral_similarity=0.92,
            maximum_normalized_correction=0.08,
        ),
    )
    ledger = pack_latent_field_event_ledger(
        result,
        pair_language=SparseMotifLanguage(minimum_occurrences=3),
        path_language=SparsePathLanguage(
            minimum_occurrences=3,
            minimum_steps=3,
            maximum_steps=4,
        ),
    )
    short_rng = np.random.default_rng(159)
    short_basis = np.rint(
        9000.0 * np.sin(
            2.0 * np.pi * (
                0.031 * np.arange(64)
                + 0.00031 * np.arange(64) ** 2
            )
        )
    ).astype(np.int16)
    short_samples = short_rng.integers(
        -23,
        24,
        size=(640, 1),
        dtype=np.int16,
    )
    for occurrence, start in enumerate((17, 109, 203, 301, 397, 509)):
        short_samples[start : start + short_basis.size, 0] = np.clip(
            short_samples[
                start : start + short_basis.size,
                0,
            ].astype(np.int32) + short_basis,
            -32768,
            32767,
        ).astype(np.int16)
        contaminated = (
            np.arange(occurrence * 9, occurrence * 9 + 13)
            % short_basis.size
        )
        short_samples[start + contaminated, 0] = np.clip(
            short_samples[start + contaminated, 0].astype(np.int32)
                + short_rng.integers(
                    -1700,
                    1701,
                    size=contaminated.size,
                ),
            -32768,
            32767,
        ).astype(np.int16)
    short_result = infer_latent_source_pattern_field(
        short_samples,
        language=LatentSourceLanguage(
            scales=(64,),
            origin_hop=1,
            minimum_occurrences=4,
            maximum_components=2,
            maximum_cluster_members=32,
            maximum_lag=4,
            minimum_spectral_similarity=0.96,
            maximum_normalized_correction=0.20,
        ),
    )
    direct_bytes = result.report["direct_proxy_bytes"]
    structured_bytes = result.report["structured_proxy_bytes"]
    payload = {
        "schema": "resonith-r160-changing-overlap-synthetic-1",
        "status": "Synthetic / exact structural proxy / not full codec",
        "no_direct_exact_mixed_group": (
            result.report["direct_exact_group_count"] == 0
        ),
        "component_count": result.report["latent_component_count"],
        "occurrence_count": result.report["latent_occurrence_count"],
        "direct_proxy_bytes": direct_bytes,
        "structured_proxy_bytes": structured_bytes,
        "saving_bytes": direct_bytes - structured_bytes,
        "saving_percent": (
            100.0 * (direct_bytes - structured_bytes) / direct_bytes
        ),
        "short_candidate": {
            "best_candidate_byte_delta": short_result.report[
                "best_candidate_byte_delta"
            ],
            "selected_component_count": short_result.report[
                "latent_component_count"
            ],
            "exact_reconstruction": short_result.report[
                "exact_integer_reconstruction"
            ],
        },
        "event_ledger": ledger.report,
        "oracle": result.report,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
