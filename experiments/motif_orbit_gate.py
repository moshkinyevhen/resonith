"""Measure R-142 immutable gain-orbit reuse against exact independent Truth."""

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

from maf_p0.motif_orbit import (  # noqa: E402
    encode_gain_orbit_candidate,
    encode_optimized_independent_truth,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import read_pcm16_channels  # noqa: E402


DEFAULT_CLIPS = (
    "ebu-sustained-sine",
    "ebu-electronic-tune",
    "ebu-female-speech-en",
    "ebu-claves",
    "ebu-pink-noise",
    "ebu-dense-orchestra",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _mono_analysis_view(samples: np.ndarray) -> np.ndarray:
    if samples.shape[1] == 1:
        return samples
    mixed = np.rint(
        np.mean(samples.astype(np.int64), axis=1, dtype=np.float64)
    )
    return np.clip(mixed, -32768, 32767).astype(np.int16)[:, None]


def _synthetic_source() -> tuple[int, np.ndarray]:
    sample_rate = 48000
    length = 512
    position = np.arange(length, dtype=np.float64)
    basis = np.rint(
        10000.0 * np.sin(2.0 * np.pi * 7.0 * position / length)
        + 3500.0 * np.sin(2.0 * np.pi * 23.0 * position / length)
    ).astype(np.int64)
    gains = (32768, 28672, 24576, -32768, 20480, 16384) * 64
    generator = np.random.default_rng(0x5231_3432)
    blocks = []
    for gain in gains:
        product = basis * gain
        scaled = np.where(
            product >= 0,
            (product + 16384) // 32768,
            -((-product + 16384) // 32768),
        )
        innovation = generator.integers(-2, 3, length, dtype=np.int64)
        blocks.append(np.clip(scaled + innovation, -32768, 32767))
    return sample_rate, np.concatenate(blocks).astype(np.int16)[:, None]


def _evaluate(
    clip_id: str,
    source_path: Path | None,
    sample_rate: int,
    samples: np.ndarray,
    *,
    decoder: NativeMain0Decoder,
    block_samples: tuple[int, ...],
    truth_block_sizes: tuple[int, ...],
    search_mode: str,
    foundry: GainPhaseCudaFoundry | None,
) -> dict:
    started = time.perf_counter()
    analysis_samples = _mono_analysis_view(samples)
    baseline_payload, baseline_report = encode_optimized_independent_truth(
        analysis_samples,
        truth_block_sizes=truth_block_sizes,
    )
    winning_truth_block = int(baseline_report["block_size"])
    candidates = []
    for length in block_samples:
        candidate = encode_gain_orbit_candidate(
            analysis_samples,
            sample_rate,
            native_decoder=decoder,
            block_samples=length,
            truth_block_sizes=(winning_truth_block,),
            search_mode=search_mode,
            foundry=foundry,
        )
        candidate_report = dict(candidate.report)
        candidate_report["byte_delta_vs_independent_truth"] = (
            candidate.representation_bytes - len(baseline_payload)
        )
        candidate_report["ratio_vs_independent_truth"] = (
            candidate.representation_bytes / len(baseline_payload)
        )
        candidates.append(candidate_report)

    best = min(
        candidates,
        key=lambda item: (
            item["representation_bytes"],
            item["block_samples"],
        ),
    )
    selected_orbit = best["representation_bytes"] < len(baseline_payload)
    source_record = {
        "kind": "generated transformed-loop"
        if source_path is None
        else "pinned PCM analysis view",
        "sample_rate": sample_rate,
        "frames": int(samples.shape[0]),
        "source_channels": int(samples.shape[1]),
        "analysis_channels": 1,
    }
    if source_path is not None:
        source_record.update(
            {
                "file": source_path.name,
                "file_bytes": source_path.stat().st_size,
                "sha256": _sha256(source_path),
            }
        )
    result = {
        "clip_id": clip_id,
        "source": source_record,
        "independent_truth": {
            "bytes": len(baseline_payload),
            "report": baseline_report,
        },
        "best_forced_orbit": best,
        "selected": {
            "kind": "gain-orbit-plus-truth"
            if selected_orbit
            else "independent-truth-fallback",
            "bytes": (
                best["representation_bytes"]
                if selected_orbit
                else len(baseline_payload)
            ),
            "saving_percent": (
                100.0
                * (len(baseline_payload) - best["representation_bytes"])
                / len(baseline_payload)
                if selected_orbit
                else 0.0
            ),
        },
        "candidates": candidates,
        "wall_seconds": time.perf_counter() - started,
    }
    print(
        f"{clip_id}: orbit {best['representation_bytes']:,} B / "
        f"Truth {len(baseline_payload):,} B; "
        f"{result['selected']['kind']}",
        flush=True,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clip-id", action="append")
    parser.add_argument(
        "--block-samples",
        type=int,
        action="append",
        default=[],
    )
    parser.add_argument(
        "--truth-block-size",
        type=int,
        action="append",
        default=[],
    )
    parser.add_argument("--source-revision", required=True)
    parser.add_argument(
        "--search-mode",
        choices=("foundry", "fast"),
        default="foundry",
    )
    parser.add_argument("--foundry-cuda", type=Path)
    parser.add_argument("--nvrtc-directory", type=Path)
    args = parser.parse_args()

    manifest = json.loads(
        args.prepared_manifest.read_text(encoding="utf-8")
    )
    manifest_clips = {item["id"]: item for item in manifest["clips"]}
    selected_ids = tuple(args.clip_id or DEFAULT_CLIPS)
    if any(clip_id not in manifest_clips for clip_id in selected_ids):
        raise ValueError("one or more requested R-142 clips are unavailable")
    lengths = tuple(
        args.block_samples or (64, 128, 256, 512, 1024, 2048)
    )
    truth_sizes = tuple(args.truth_block_size or (1024, 4096, 16384))
    decoder = NativeMain0Decoder(args.native_core)
    foundry = None
    if args.search_mode == "foundry":
        if args.foundry_cuda is None or args.nvrtc_directory is None:
            parser.error(
                "Foundry mode requires --foundry-cuda and "
                "--nvrtc-directory"
            )
        foundry = GainPhaseCudaFoundry(
            args.foundry_cuda,
            args.nvrtc_directory,
        )
    gate_started = time.perf_counter()

    sample_rate, synthetic = _synthetic_source()
    results = {
        "synthetic-transformed-loop": _evaluate(
            "synthetic-transformed-loop",
            None,
            sample_rate,
            synthetic,
            decoder=decoder,
            block_samples=(512,),
            truth_block_sizes=truth_sizes,
            search_mode=args.search_mode,
            foundry=foundry,
        )
    }
    for clip_id in selected_ids:
        source_path = (
            args.prepared_directory / manifest_clips[clip_id]["output_file"]
        )
        sample_rate, samples = read_pcm16_channels(source_path)
        results[clip_id] = _evaluate(
            clip_id,
            source_path,
            sample_rate,
            samples,
            decoder=decoder,
            block_samples=lengths,
            truth_block_sizes=truth_sizes,
            search_mode=args.search_mode,
            foundry=foundry,
        )

    selected_count = sum(
        int(item["selected"]["kind"] == "gain-orbit-plus-truth")
        for item in results.values()
    )
    report = {
        "schema": "resonith-r142-motif-orbit-gate-1",
        "decision": "R-142",
        "status": (
            "lossless architecture diagnostic; not R-118 or an Opus claim"
        ),
        "source_revision": args.source_revision,
        "configuration": {
            "block_samples": lengths,
            "truth_block_sizes": truth_sizes,
            "search_mode": args.search_mode,
            "maximum_normalized_fit_error": 5.0e-2,
            "mono_analysis_view": True,
            "common_outer_container_bytes_excluded": True,
        },
        "selected_count": selected_count,
        "fallback_count": len(results) - selected_count,
        "total_wall_seconds": time.perf_counter() - gate_started,
        "native_core": {
            "file": args.native_core.name,
            "sha256": _sha256(args.native_core),
        },
        "clips": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
