"""Run the R-051 held-out cached-Basis simultaneous-source gate."""

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

from maf_p0.additive_oracle import _period_candidates  # noqa: E402
from maf_p0.cached_additive_oracle import (  # noqa: E402
    pack_registry_model,
    run_cached_additive_oracle,
)
from maf_p0.model import save_analysis_model, train_linear_cibs  # noqa: E402
from maf_p0.periodic import analyze_periodic_basis  # noqa: E402
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


def _collect_held_out_training_bases(
    manifest: dict,
    cache: Path,
    *,
    basis_length: int,
    window_seconds: float,
    maximum_windows_per_source: int,
    periods_per_window: int,
) -> tuple[np.ndarray, list[dict]]:
    """Extract Basis examples only after each declared evaluation crop."""

    bases: list[np.ndarray] = []
    intervals: list[dict] = []
    for record in manifest["sources"]:
        source_path = fetch_source(record, cache)
        sample_rate, full_samples, _conversion = read_pcm_as_mono16(
            source_path
        )
        crop_end_seconds = (
            float(record["start_seconds"])
            + float(record["duration_seconds"])
        )
        training_start = min(
            full_samples.size,
            int(round(crop_end_seconds * sample_rate)),
        )
        window = max(
            basis_length * 4,
            int(round(window_seconds * sample_rate)),
        )
        available = full_samples.size - training_start
        if available < window:
            intervals.append(
                {
                    "id": record["id"],
                    "sample_rate": sample_rate,
                    "start_sample": training_start,
                    "end_sample": int(full_samples.size),
                    "window_count": 0,
                    "basis_count": 0,
                }
            )
            continue
        offsets = np.linspace(
            training_start,
            full_samples.size - window,
            num=min(
                maximum_windows_per_source,
                1 + available // window,
            ),
            dtype=np.int64,
        )
        source_basis_start = len(bases)
        for offset in offsets:
            segment = full_samples[int(offset):int(offset) + window]
            periods = _period_candidates(
                segment,
                sample_rate,
                maximum_candidates=max(4, periods_per_window * 2),
            )
            for period in periods[:periods_per_window]:
                try:
                    analysis = analyze_periodic_basis(
                        segment,
                        sample_rate,
                        basis_length=basis_length,
                        period_samples=period,
                    )
                except ValueError:
                    continue
                bases.append(analysis.basis.reshape(1, -1))
        intervals.append(
            {
                "id": record["id"],
                "sample_rate": sample_rate,
                "start_sample": training_start,
                "end_sample": int(full_samples.size),
                "window_count": int(offsets.size),
                "basis_count": len(bases) - source_basis_start,
            }
        )
    if len(bases) < 2:
        raise RuntimeError("held-out intervals produced too few CIBS examples")
    return np.stack(bases).astype(np.int16), intervals


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
    parser.add_argument("--basis-length", type=int, default=256)
    parser.add_argument("--latent-elements", type=int, default=16)
    parser.add_argument("--maximum-atoms", type=int, default=4)
    parser.add_argument("--analysis-period-candidates", type=int, default=16)
    parser.add_argument("--period-rdo-shortlist", type=int, default=8)
    parser.add_argument("--training-window-seconds", type=float, default=0.25)
    parser.add_argument("--training-windows-per-source", type=int, default=32)
    parser.add_argument("--training-periods-per-window", type=int, default=2)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "cached_cibs_additive",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    training_bases, training_intervals = _collect_held_out_training_bases(
        manifest,
        args.cache,
        basis_length=args.basis_length,
        window_seconds=args.training_window_seconds,
        maximum_windows_per_source=args.training_windows_per_source,
        periods_per_window=args.training_periods_per_window,
    )
    model = train_linear_cibs(
        training_bases,
        latent_elements=args.latent_elements,
        model_id="CIBS0-HELDOUT-MUSIC-R051",
    )
    model_path = args.output_directory / "development_model.npz"
    save_analysis_model(model_path, model)
    registry_bytes = pack_registry_model(model)
    registry_path = args.output_directory / "development_model.crm1"
    registry_path.write_bytes(registry_bytes)

    clip_reports = {}
    winning_clips = 0
    reductions: list[float] = []
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_pcm_as_mono16(source_path)
        samples = crop_source(full_samples, sample_rate, record)
        sample_limit = int(round(args.maximum_seconds * sample_rate))
        samples = samples[:sample_limit].copy()

        started = time.perf_counter()
        result = run_cached_additive_oracle(
            samples,
            sample_rate,
            model,
            gain_block_size=4096,
            innovation_step=64,
            residual_block_sizes=(4096, 16384, 32768),
            maximum_atoms=args.maximum_atoms,
            analysis_period_candidates=args.analysis_period_candidates,
            period_rdo_shortlist=args.period_rdo_shortlist,
        )
        encode_seconds = time.perf_counter() - started
        reduction = float(result.report["selected_reduction_vs_zero_atom"])
        won = result.report["atom_count"] > 0 and reduction >= 0.03
        winning_clips += int(won)
        reductions.append(reduction)

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
            "three_percent_cached_atom_win": won,
            "result": result.report,
        }

    mean_reduction = float(np.mean(reductions))
    gate_passed = winning_clips >= 2 and mean_reduction >= 0.05
    report = {
        "status": (
            "compression gate passed; simultaneous mixing may be promoted"
            if gate_passed
            else "compression gate failed; simultaneous mixing remains deferred"
        ),
        "research_only": True,
        "gate_rule": (
            "cached Atoms save at least 3% on two clips and 5% arithmetic mean "
            "against complete zero-Atom RSL2"
        ),
        "gate_passed": gate_passed,
        "winning_clips": winning_clips,
        "clip_count": len(clip_reports),
        "arithmetic_mean_reduction": mean_reduction,
        "maximum_seconds_per_clip": args.maximum_seconds,
        "maximum_atoms": args.maximum_atoms,
        "analysis_period_candidates": args.analysis_period_candidates,
        "period_rdo_shortlist": args.period_rdo_shortlist,
        "model": {
            "id": model.model_id,
            "basis_length": model.output_length,
            "latent_elements": model.latent_elements,
            "training_example_count": int(training_bases.shape[0]),
            "training_pcm_intervals": training_intervals,
            "registry_bytes": len(registry_bytes),
            "registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
            "npz_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        },
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
