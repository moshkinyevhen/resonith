"""Run the R-038 simultaneous-Atom oracle on pinned licensed music."""

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
    parser.add_argument("--maximum-atoms", type=int, default=4)
    parser.add_argument("--analysis-period-candidates", type=int, default=16)
    parser.add_argument("--period-rdo-shortlist", type=int, default=8)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "additive_atom_oracle",
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
        sample_limit = int(round(args.maximum_seconds * sample_rate))
        samples = samples[:sample_limit].copy()

        started = time.perf_counter()
        result = run_additive_atom_oracle(
            samples,
            sample_rate,
            basis_length=256,
            gain_block_size=4096,
            innovation_step=64,
            residual_block_size=1024,
            maximum_atoms=args.maximum_atoms,
            analysis_period_candidates=args.analysis_period_candidates,
            period_rdo_shortlist=args.period_rdo_shortlist,
        )
        encode_seconds = time.perf_counter() - started
        selected_atoms = int(result.report["atom_count"])
        won = (
            selected_atoms > 1
            and result.report["stream_bytes"] < result.report["one_atom_bytes"]
        )
        winning_clips += int(won)

        clip_directory = args.output_directory / record["id"]
        clip_directory.mkdir(parents=True, exist_ok=True)
        (clip_directory / "selected.research-rsc1").write_bytes(
            result.selected_payload
        )
        write_pcm16_mono(
            clip_directory / "selected.wav",
            sample_rate,
            result.selected_reconstruction,
        )
        candidates = []
        for candidate in result.report["candidates"]:
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
            "additional_atom_won": won,
            "result": {
                **result.report,
                "candidates": candidates,
            },
        }

    gate_passed = winning_clips >= 2
    report = {
        "status": (
            "compression gate passed; normative overlap may be considered"
            if gate_passed
            else "compression gate failed; normative overlap remains deferred"
        ),
        "research_only": True,
        "gate_rule": (
            "an additional Atom must reduce complete bytes on at least "
            "two declared clips"
        ),
        "gate_passed": gate_passed,
        "winning_clips": winning_clips,
        "clip_count": len(clip_reports),
        "maximum_seconds_per_clip": args.maximum_seconds,
        "maximum_atoms": args.maximum_atoms,
        "analysis_period_candidates": args.analysis_period_candidates,
        "period_rdo_shortlist": args.period_rdo_shortlist,
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
