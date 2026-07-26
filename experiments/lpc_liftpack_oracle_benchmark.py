"""Run the R-042 bounded integer LPC oracle on pinned licensed music."""

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

from maf_p0.lpc_oracle import run_lpc_liftpack_oracle  # noqa: E402
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
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "lpc_liftpack_oracle",
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
        result = run_lpc_liftpack_oracle(samples, sample_rate)
        encode_seconds = time.perf_counter() - started
        won = result.report["selected_reduction_vs_rsl1"] > 0.0
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
        clip_reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.size),
            "duration_seconds": samples.size / sample_rate,
            "mono_pcm_sha256": _pcm_sha256(samples),
            "encode_wall_seconds": encode_seconds,
            "lpc_won": won,
            "result": result.report,
        }

    gate_passed = winning_clips >= 2
    report = {
        "status": (
            "compression gate passed; native LPC syntax may be considered"
            if gate_passed
            else "compression gate failed; native LPC syntax remains deferred"
        ),
        "research_only": True,
        "gate_rule": (
            "bounded LPC must reduce complete bytes beyond block-size-RDO "
            "RSL1 on at least two declared clips"
        ),
        "gate_passed": gate_passed,
        "winning_clips": winning_clips,
        "clip_count": len(clip_reports),
        "maximum_seconds_per_clip": args.maximum_seconds,
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
