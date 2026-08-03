"""Run the bounded R-156/R-157 structural gate across the R-118 union."""

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
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from bounded_value_entropy_gate import (  # noqa: E402
    _parse_sources,
    _prepared_sources,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402
from maf_p0.gridless_pattern_field import (  # noqa: E402
    GridlessOriginSet,
    GridlessPatternField,
)
from maf_p0.gridless_truth_rdo import (  # noqa: E402
    encode_gridless_truth_candidate,
    search_gridless_warp_field,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _active_window(samples: np.ndarray, frame_count: int) -> tuple[int, np.ndarray]:
    """Select the highest-energy complete non-overlapping diagnostic window."""

    frames = samples.shape[0]
    if frames <= frame_count:
        return 0, samples
    best_start = 0
    best_energy = -1
    for start in range(0, frames - frame_count + 1, frame_count):
        values = samples[start : start + frame_count].astype(np.int64)
        energy = int(np.sum(values * values))
        if energy > best_energy:
            best_start = start
            best_energy = energy
    return best_start, samples[best_start : best_start + frame_count]


def _even_subset(values: set[int], maximum_count: int) -> tuple[int, ...]:
    ordered = tuple(sorted(values))
    if len(ordered) <= maximum_count:
        return ordered
    indices = np.rint(
        np.linspace(0, len(ordered) - 1, maximum_count)
    ).astype(np.int64)
    return tuple(ordered[int(index)] for index in np.unique(indices))


def _diagnostic_field(
    samples: np.ndarray,
    *,
    foundry: GainPhaseCudaFoundry,
    sample_counts: tuple[int, ...],
    maximum_locations: int,
) -> GridlessPatternField:
    """Declare a reproducible Fast subset; Foundry claims apply only inside it."""

    frames, channels = samples.shape
    base_sample_count = min(sample_counts)
    origin_sets = []
    locations_by_scale: dict[int, int] = {}
    for sample_count in sample_counts:
        scale_locations = max(
            2 * channels,
            int(round(
                maximum_locations
                * (base_sample_count / sample_count) ** 0.5
            )),
        )
        per_channel = max(2, scale_locations // channels)
        for channel in range(channels):
            hashes = foundry.rolling_hashes(
                samples[:, channel],
                window_samples=sample_count,
            )
            anchors = foundry.content_defined_anchors(
                hashes,
                selection_window=max(1, sample_count // 2),
            )
            union = {int(value) for value in anchors}
            union.update(range(0, frames - sample_count + 1, sample_count))
            selected = _even_subset(union, per_channel)
            origin_sets.append(
                GridlessOriginSet(
                    channel,
                    sample_count,
                    int(hashes.size),
                    0,
                    sample_count,
                    0,
                    selected,
                )
            )
            locations_by_scale[sample_count] = (
                locations_by_scale.get(sample_count, 0) + len(selected)
            )
    return GridlessPatternField(
        frames,
        channels,
        sample_counts,
        tuple(origin_sets),
        (),
        {
            "schema": "resonith-r157-r118-fast-origin-manifest-1",
            "status": "Fast diagnostic subset; no whole-file Foundry claim",
            "frames": frames,
            "channels": channels,
            "sample_counts": list(sample_counts),
            "maximum_locations": maximum_locations,
            "locations_by_scale": locations_by_scale,
            "declared_locations": sum(
                len(item.content_defined_origins) for item in origin_sets
            ),
            "gridless_meaning": True,
            "tiled_execution": True,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--source", action="append")
    parser.add_argument("--foundry-library", type=Path, required=True)
    parser.add_argument("--nvrtc-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--analysis-frames", type=int, default=4096)
    parser.add_argument("--sample-count", type=int, action="append")
    parser.add_argument("--maximum-locations", type=int, default=16)
    parser.add_argument("--phase-subsamples", type=int, default=4)
    parser.add_argument("--step-radius", type=int, default=1)
    parser.add_argument("--step-increment-q16", type=int, default=512)
    parser.add_argument("--end-step-radius", type=int, default=1)
    parser.add_argument("--maximum-normalized-error", type=float, default=0.02)
    args = parser.parse_args()

    sources, categories = _prepared_sources(
        args.prepared_manifest,
        args.prepared_directory,
    )
    sources.update(_parse_sources(args.source))
    categories.update({
        "speech": ["speech", "mono"],
        "emotional-piano": ["music", "piano", "stereo"],
        "mozart-full": ["music", "classical", "orchestral", "stereo"],
    })
    expected = {
        "speech",
        "emotional-piano",
        "mozart-full",
        *(
            item["id"]
            for item in json.loads(
                args.prepared_manifest.read_text(encoding="utf-8")
            )["clips"]
        ),
    }
    if set(sources) != expected:
        missing = sorted(expected - set(sources))
        extra = sorted(set(sources) - expected)
        raise ValueError(f"R-118 source mismatch; missing={missing}, extra={extra}")
    sample_counts = tuple(sorted(set(args.sample_count or (64,))))
    if (
        not sample_counts
        or any(
            value < 3 or value > args.analysis_frames
            for value in sample_counts
        )
        or args.maximum_locations < 2
    ):
        raise ValueError("invalid R-157 diagnostic bounds")

    foundry = GainPhaseCudaFoundry(
        args.foundry_library,
        args.nvrtc_directory,
    )
    native = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    clips: dict[str, dict] = {}
    for clip_id in sorted(sources):
        clip_started = time.perf_counter()
        sample_rate, complete = read_pcm16_channels(sources[clip_id])
        window_start, samples = _active_window(
            complete,
            args.analysis_frames,
        )
        field = _diagnostic_field(
            samples,
            foundry=foundry,
            sample_counts=sample_counts,
            maximum_locations=args.maximum_locations,
        )
        search = search_gridless_warp_field(
            samples,
            field=field,
            foundry=foundry,
            phase_subsamples=args.phase_subsamples,
            step_radius=args.step_radius,
            step_increment_q16=args.step_increment_q16,
            end_step_radius=args.end_step_radius,
            maximum_normalized_error=args.maximum_normalized_error,
        )
        candidate = encode_gridless_truth_candidate(
            samples,
            sample_rate,
            search=search,
            native_decoder=native,
            truth_block_sizes=(256, 1024, 4096),
        )
        if not np.array_equal(candidate.reconstruction, samples):
            raise RuntimeError(f"R-157 Truth mismatch: {clip_id}")
        clip_directory = args.output_directory / clip_id
        clip_directory.mkdir(parents=True, exist_ok=True)
        write_pcm16_channels(
            clip_directory / "analysis-original.wav",
            sample_rate,
            samples,
        )
        write_pcm16_channels(
            clip_directory / "selected-exact.wav",
            sample_rate,
            candidate.reconstruction,
        )
        if candidate.maf_payload:
            (clip_directory / "selected.mft1").write_bytes(
                candidate.maf_payload
            )
        (clip_directory / "selected.truth").write_bytes(
            candidate.truth_payload
        )
        complete_bytes = (
            len(candidate.maf_payload) + len(candidate.truth_payload)
        )
        independent = candidate.report["independent_truth_bytes"]
        clips[clip_id] = {
            "categories": categories[clip_id],
            "source_file": sources[clip_id].name,
            "source_frames": int(complete.shape[0]),
            "channels": int(complete.shape[1]),
            "sample_rate": sample_rate,
            "analysis_start": window_start,
            "analysis_frames": int(samples.shape[0]),
            "origin_manifest": field.report,
            "search": search.report,
            "candidate": candidate.report,
            "complete_bytes": complete_bytes,
            "independent_truth_bytes": independent,
            "byte_delta": complete_bytes - independent,
            "saving_percent": (
                100.0 * (independent - complete_bytes) / independent
                if independent
                else 0.0
            ),
            "selected_exact_sha256": _sha256(
                np.ascontiguousarray(
                    candidate.reconstruction,
                    dtype="<i2",
                ).tobytes()
            ),
            "wall_seconds": time.perf_counter() - clip_started,
        }
        print(
            f"{clip_id}: {search.report['candidate_count']:,} candidates, "
            f"{len(search.matches):,} eligible, "
            f"{candidate.selected_kind}, "
            f"{complete_bytes}/{independent} B",
            flush=True,
        )

    selected = sum(
        item["candidate"]["selected_kind"] == "gridless-warp-truth"
        for item in clips.values()
    )
    report = {
        "schema": "resonith-r157-r118-fast-structural-gate-1",
        "status": (
            "complete 19-item Fast structural diagnostic; "
            "whole-file quality/Opus gate pending"
        ),
        "configuration": {
            "analysis_frames": args.analysis_frames,
            "sample_counts": list(sample_counts),
            "maximum_locations": args.maximum_locations,
            "phase_subsamples": args.phase_subsamples,
            "step_radius": args.step_radius,
            "step_increment_q16": args.step_increment_q16,
            "end_step_radius": args.end_step_radius,
            "maximum_normalized_error": args.maximum_normalized_error,
        },
        "clip_count": len(clips),
        "structured_selection_count": selected,
        "fallback_count": len(clips) - selected,
        "total_candidates": sum(
            item["search"]["candidate_count"] for item in clips.values()
        ),
        "total_executed_candidates": sum(
            item["search"]["executed_candidate_count"]
            for item in clips.values()
        ),
        "total_wall_seconds": time.perf_counter() - started,
        "clips": clips,
    }
    (args.output_directory / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({
        key: report[key]
        for key in (
            "status",
            "clip_count",
            "structured_selection_count",
            "fallback_count",
            "total_candidates",
            "total_executed_candidates",
            "total_wall_seconds",
        )
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
