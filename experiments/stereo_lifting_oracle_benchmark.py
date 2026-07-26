"""Run the R-045 reversible stereo-lifting oracle on licensed music."""

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

from maf_p0.stereo_oracle import run_stereo_lifting_oracle  # noqa: E402
from maf_p0.wav_io import write_pcm16_channels  # noqa: E402
from real_music_benchmark import (  # noqa: E402
    fetch_source,
    read_pcm_as_channels16,
)


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()


def _crop_channels(
    samples: np.ndarray,
    sample_rate: int,
    record: dict,
    maximum_seconds: float,
) -> np.ndarray:
    start = int(round(float(record["start_seconds"]) * sample_rate))
    count = min(
        int(round(float(record["duration_seconds"]) * sample_rate)),
        int(round(maximum_seconds * sample_rate)),
    )
    end = min(samples.shape[0], start + count)
    if start < 0 or end <= start:
        raise ValueError(f"invalid stereo corpus crop: {record['id']}")
    return samples[start:end].copy()


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
        default=PROJECT_ROOT / "artifacts" / "stereo_lifting_oracle",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    clip_reports = {}
    winning_clips = 0
    reductions: list[float] = []
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_pcm_as_channels16(
            source_path
        )
        if full_samples.shape[1] != 2:
            raise ValueError(
                f"R-045 corpus source is not stereo: {record['id']}"
            )
        samples = _crop_channels(
            full_samples,
            sample_rate,
            record,
            args.maximum_seconds,
        )

        started = time.perf_counter()
        result = run_stereo_lifting_oracle(samples, sample_rate)
        encode_seconds = time.perf_counter() - started
        reduction = float(
            result.report["selected_reduction_vs_independent"]
        )
        won = reduction > 0.0
        winning_clips += int(won)
        reductions.append(reduction)

        clip_directory = args.output_directory / record["id"]
        clip_directory.mkdir(parents=True, exist_ok=True)
        (clip_directory / "selected.research-rsc1").write_bytes(
            result.selected_payload
        )
        write_pcm16_channels(
            clip_directory / "selected.wav",
            sample_rate,
            result.selected_reconstruction,
        )
        clip_reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "sample_count": int(samples.shape[0]),
            "duration_seconds": samples.shape[0] / sample_rate,
            "stereo_pcm_sha256": _pcm_sha256(samples),
            "encode_wall_seconds": encode_seconds,
            "decorrelation_won": won,
            "result": result.report,
        }

    mean_reduction = float(np.mean(reductions)) if reductions else 0.0
    gate_passed = winning_clips >= 2 and mean_reduction >= 0.12
    report = {
        "status": (
            "compression gate passed; reversible stereo lift may be promoted"
            if gate_passed
            else "compression gate failed; stereo lifting remains deferred"
        ),
        "research_only": True,
        "gate_rule": (
            "stereo lifting must save at least 10% on two clips and 12% "
            "on the arithmetic mean"
        ),
        "gate_passed": gate_passed,
        "winning_clips": winning_clips,
        "mean_reduction_vs_independent": mean_reduction,
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
