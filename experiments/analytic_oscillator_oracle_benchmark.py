"""Run the R-039 batched analytic oscillator oracle on licensed music."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.additive_oracle import run_additive_atom_oracle  # noqa: E402
from maf_p0.analytic_oracle import (  # noqa: E402
    run_analytic_oscillator_oracle,
)
from maf_p0.wav_io import write_pcm16_mono  # noqa: E402
from real_music_benchmark import (  # noqa: E402
    crop_source,
    fetch_source,
    read_pcm_as_mono16,
)


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "real_music_corpus.json",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "real_music_source",
    )
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument("--maximum-atoms", type=int, default=8)
    parser.add_argument("--spectral-candidates", type=int, default=24)
    parser.add_argument("--rdo-shortlist", type=int, default=8)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "analytic_oscillator_oracle",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    clip_reports = {}
    winning_clips = 0
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_pcm_as_mono16(source_path)
        samples = crop_source(full_samples, sample_rate, record)
        samples = samples[
            : int(round(args.maximum_seconds * sample_rate))
        ].copy()

        started = time.perf_counter()
        raw_anchor = run_additive_atom_oracle(
            samples,
            sample_rate,
            maximum_atoms=1,
        )
        analytic = run_analytic_oscillator_oracle(
            samples,
            sample_rate,
            maximum_atoms=args.maximum_atoms,
            spectral_candidates=args.spectral_candidates,
            rdo_shortlist=args.rdo_shortlist,
        )
        encode_seconds = time.perf_counter() - started
        selected_atoms = int(analytic.report["atom_count"])
        won = (
            selected_atoms > 0
            and analytic.report["stream_bytes"]
            < analytic.report["zero_atom_bytes"]
            and analytic.report["stream_bytes"]
            < raw_anchor.report["stream_bytes"]
        )
        winning_clips += int(won)

        clip_directory = args.output_directory / record["id"]
        clip_directory.mkdir(parents=True, exist_ok=True)
        (clip_directory / "selected.research-rsc1").write_bytes(
            analytic.selected_payload
        )
        write_pcm16_mono(
            clip_directory / "selected.wav",
            sample_rate,
            analytic.selected_reconstruction,
        )
        candidates = []
        for candidate in analytic.report["candidates"]:
            candidates.append(
                {
                    **candidate,
                    "effective_bitrate_kbps": (
                        8.0
                        * candidate["stream_bytes"]
                        * sample_rate
                        / samples.size
                        / 1000.0
                    ),
                }
            )
        clip_reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.size),
            "duration_seconds": samples.size / sample_rate,
            "mono_pcm_sha256": _pcm_sha256(samples),
            "encode_wall_seconds": encode_seconds,
            "analytic_bank_won": won,
            "raw_basis_anchor_bytes": raw_anchor.report["stream_bytes"],
            "result": {
                **analytic.report,
                "candidates": candidates,
            },
        }

    gate_passed = winning_clips >= 2
    report = {
        "status": (
            "compression gate passed; analytic bank syntax may be considered"
            if gate_passed
            else "compression gate failed; analytic bank syntax remains deferred"
        ),
        "research_only": True,
        "gate_rule": (
            "a nonempty analytic bank must beat both its zero-Atom envelope "
            "and the best one-Atom raw-Basis envelope on at least two clips"
        ),
        "gate_passed": gate_passed,
        "winning_clips": winning_clips,
        "clip_count": len(clip_reports),
        "maximum_seconds_per_clip": args.maximum_seconds,
        "maximum_atoms": args.maximum_atoms,
        "spectral_candidates": args.spectral_candidates,
        "rdo_shortlist": args.rdo_shortlist,
        "clips": clip_reports,
    }
    report_path = args.output_directory / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
