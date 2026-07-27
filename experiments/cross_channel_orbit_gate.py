"""Measure R-146/R-147 shared phase/envelope Basis reuse across channels."""

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
    _render_gain_shift_envelope,
    encode_multichannel_gain_orbit_candidate,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry  # noqa: E402
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.rsc1 import RSC1Section, pack_rsc1  # noqa: E402
from maf_p0.stereo_oracle import run_stereo_lifting_oracle  # noqa: E402
from maf_p0.stream_sections import StreamConfig, pack_conf  # noqa: E402
from maf_p0.wav_io import read_pcm16_channels  # noqa: E402


DEFAULT_CLIPS = (
    "ebu-violin",
    "ebu-claves",
    "ebu-cymbal",
    "ebu-grand-piano",
    "ebu-dense-orchestra",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _synthetic_stereo() -> tuple[int, np.ndarray]:
    sample_rate = 48000
    length = 256
    position = np.arange(length, dtype=np.float64)
    basis = np.rint(
        9000.0 * np.sin(2.0 * np.pi * 5.0 * position / length)
        + 2500.0 * np.sin(2.0 * np.pi * 19.0 * position / length)
    ).astype(np.int64)
    left_blocks = []
    right_blocks = []
    for block_index in range(128):
        left_blocks.append(
            _render_gain_shift_envelope(
                basis,
                (3 * block_index) % length,
                32768 - 256 * (block_index % 8),
                None,
            )
        )
        right_blocks.append(
            _render_gain_shift_envelope(
                basis,
                (5 * block_index + 17) % length,
                28672,
                12288,
            )
        )
    return sample_rate, np.column_stack(
        (
            np.concatenate(left_blocks),
            np.concatenate(right_blocks),
        )
    ).astype(np.int16)


def _pack_candidate(
    candidate,
    sample_rate: int,
    frames: int,
    channels: int,
) -> bytes:
    return pack_rsc1(
        [
            RSC1Section(
                "CONF",
                pack_conf(StreamConfig(frames, 1, channels)),
            ),
            RSC1Section("MFT1", candidate.maf_payload),
            RSC1Section("T147", candidate.truth_payload),
        ],
        profile=0,
        level=3,
        timebase_hz=sample_rate,
    )


def _evaluate(
    clip_id: str,
    source_path: Path | None,
    sample_rate: int,
    samples: np.ndarray,
    *,
    decoder: NativeMain0Decoder,
    block_samples: tuple[int, ...],
    truth_block_sizes: tuple[int, ...],
    maximum_bases: int,
    search_mode: str,
    foundry: GainPhaseCudaFoundry | None,
) -> dict:
    if samples.shape[1] != 2:
        raise ValueError("R-147 evidence requires native stereo PCM")
    started = time.perf_counter()
    baseline = run_stereo_lifting_oracle(
        samples,
        sample_rate,
        innovation_step=1,
        block_sizes=truth_block_sizes,
    )
    candidates = []
    for length in block_samples:
        candidate = encode_multichannel_gain_orbit_candidate(
            samples,
            sample_rate,
            native_decoder=decoder,
            block_samples=length,
            truth_block_sizes=truth_block_sizes,
            maximum_bases=maximum_bases,
            search_mode=search_mode,
            foundry=foundry,
        )
        wrapped = _pack_candidate(
            candidate,
            sample_rate,
            samples.shape[0],
            samples.shape[1],
        )
        record = dict(candidate.report)
        record["complete_rsc1_bytes"] = len(wrapped)
        record["ratio_vs_stereo_truth"] = (
            len(wrapped) / len(baseline.selected_payload)
        )
        candidates.append(record)
    best = min(
        candidates,
        key=lambda item: (
            item["complete_rsc1_bytes"],
            item["block_samples"],
        ),
    )
    selected_orbit = best["complete_rsc1_bytes"] < len(
        baseline.selected_payload
    )
    source_record = {
        "kind": (
            "generated channel-transfer signal"
            if source_path is None
            else "pinned native stereo PCM"
        ),
        "sample_rate": sample_rate,
        "frames": int(samples.shape[0]),
        "channels": 2,
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
        "source": source_record,
        "stereo_truth": {
            "bytes": len(baseline.selected_payload),
            "report": baseline.report,
        },
        "best_shared_orbit": best,
        "selected": {
            "kind": (
                "shared-cross-channel-orbit"
                if selected_orbit
                else "stereo-truth-fallback"
            ),
            "bytes": (
                best["complete_rsc1_bytes"]
                if selected_orbit
                else len(baseline.selected_payload)
            ),
            "saving_percent": (
                100.0
                * (
                    len(baseline.selected_payload)
                    - best["complete_rsc1_bytes"]
                )
                / len(baseline.selected_payload)
                if selected_orbit
                else 0.0
            ),
        },
        "candidates": candidates,
        "wall_seconds": time.perf_counter() - started,
    }
    print(
        f"{clip_id}: shared orbit {best['complete_rsc1_bytes']:,} B / "
        f"stereo Truth {len(baseline.selected_payload):,} B; "
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
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--maximum-bases", type=int, default=64)
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
    lengths = tuple(args.block_samples or (128, 256, 512))
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

    sample_rate, synthetic = _synthetic_stereo()
    results = {
        "synthetic-channel-transfer": _evaluate(
            "synthetic-channel-transfer",
            None,
            sample_rate,
            synthetic,
            decoder=decoder,
            block_samples=(256,),
            truth_block_sizes=truth_sizes,
            maximum_bases=args.maximum_bases,
            search_mode=args.search_mode,
            foundry=foundry,
        )
    }
    for clip_id in (() if args.synthetic_only else selected_ids):
        if clip_id not in manifest_clips:
            raise ValueError(f"missing prepared clip: {clip_id}")
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
            maximum_bases=args.maximum_bases,
            search_mode=args.search_mode,
            foundry=foundry,
        )

    report = {
        "schema": "resonith-r147-cross-channel-orbit-gate-1",
        "decision": "R-146/R-147",
        "status": (
            "lossless architecture diagnostic; not R-118 or an Opus claim"
        ),
        "source_revision": args.source_revision,
        "configuration": {
            "block_samples": lengths,
            "truth_block_sizes": truth_sizes,
            "semantic_labels_used_for_matching": False,
            "phase_invariant_proposal": True,
            "complex_correlation_alignment": True,
            "constant_or_linear_gain_rdo": True,
            "maximum_bases": args.maximum_bases,
            "search_mode": args.search_mode,
        },
        "total_wall_seconds": time.perf_counter() - gate_started,
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
