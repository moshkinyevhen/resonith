"""Measure R-145 semantic-free partial-spectrum reuse with exact correction."""

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
    encode_optimized_independent_truth,
)
from maf_p0.partial_spectrum_orbit import (  # noqa: E402
    encode_partial_spectrum_orbit,
    reversible_multiband_synthesis,
)
from maf_p0.wav_io import read_pcm16_channels  # noqa: E402


DEFAULT_CLIPS = (
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


def _synthetic_partial_band_source() -> tuple[int, np.ndarray]:
    sample_rate = 48000
    levels = 3
    frame_count = 131072
    generator = np.random.default_rng(0x5231_3435)
    low = generator.integers(-400, 401, frame_count // 8, dtype=np.int64)
    detail3 = generator.integers(-80, 81, frame_count // 8, dtype=np.int64)
    detail2 = generator.integers(-80, 81, frame_count // 4, dtype=np.int64)
    phase = np.arange(64, dtype=np.float64)
    basis = np.rint(
        1800.0 * np.sin(2.0 * np.pi * 7.0 * phase / 64.0)
    ).astype(np.int64)
    gains = (32768, 24576, -32768, 16384) * (
        (frame_count // 2) // (4 * basis.size)
    )
    detail1 = np.concatenate(
        [
            np.where(
                np.roll(basis, (7 * block_index) % basis.size) * gain >= 0,
                (
                    np.roll(basis, (7 * block_index) % basis.size) * gain
                    + 16384
                )
                // 32768,
                -(
                    (
                        -np.roll(basis, (7 * block_index) % basis.size) * gain
                        + 16384
                    )
                    // 32768
                ),
            )
            for block_index, gain in enumerate(gains)
        ]
    )
    source = reversible_multiband_synthesis(
        (low, detail3, detail2, detail1),
        frame_count,
    )
    return sample_rate, source.astype(np.int16)[:, None]


def _evaluate(
    clip_id: str,
    source_path: Path | None,
    sample_rate: int,
    samples: np.ndarray,
    *,
    levels: tuple[int, ...],
    block_samples: tuple[int, ...],
    truth_block_sizes: tuple[int, ...],
) -> dict:
    started = time.perf_counter()
    source = _mono_analysis_view(samples)
    independent, independent_report = encode_optimized_independent_truth(
        source,
        truth_block_sizes=truth_block_sizes,
    )
    winning_truth_block = int(independent_report["block_size"])
    candidates = []
    payloads: dict[tuple[int, int], bytes] = {}
    for level_count in levels:
        for length in block_samples:
            candidate = encode_partial_spectrum_orbit(
                source,
                levels=level_count,
                block_samples=length,
                truth_block_sizes=(winning_truth_block,),
            )
            record = dict(candidate.report)
            record["ratio_dictionary_vs_independent_truth"] = (
                len(candidate.dictionary_payload) / len(independent)
            )
            record["ratio_multiband_truth_vs_independent_truth"] = (
                len(candidate.multiband_truth_payload) / len(independent)
            )
            candidates.append(record)
            payloads[(level_count, length)] = candidate.dictionary_payload

    best_dictionary = min(
        candidates,
        key=lambda item: (
            item["dictionary_bytes"],
            item["levels"],
            item["block_samples"],
        ),
    )
    best_multiband_truth = min(
        candidates,
        key=lambda item: (
            item["multiband_truth_bytes"],
            item["levels"],
            item["block_samples"],
        ),
    )
    alternatives = (
        ("independent-truth", len(independent)),
        (
            "partial-spectrum-dictionary",
            best_dictionary["dictionary_bytes"],
        ),
        ("multiband-truth", best_multiband_truth["multiband_truth_bytes"]),
    )
    selected_kind, selected_bytes = min(
        alternatives,
        key=lambda item: (item[1], item[0]),
    )
    source_record = {
        "kind": (
            "generated partial-band mixture"
            if source_path is None
            else "pinned PCM mono analysis view"
        ),
        "sample_rate": sample_rate,
        "frames": int(samples.shape[0]),
        "source_channels": int(samples.shape[1]),
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
        "independent_truth": {
            "bytes": len(independent),
            "report": independent_report,
        },
        "best_dictionary": best_dictionary,
        "best_multiband_truth": best_multiband_truth,
        "selected": {
            "kind": selected_kind,
            "bytes": selected_bytes,
            "saving_percent_vs_independent_truth": max(
                0.0,
                100.0 * (len(independent) - selected_bytes) / len(independent),
            ),
        },
        "candidates": candidates,
        "wall_seconds": time.perf_counter() - started,
    }
    print(
        f"{clip_id}: dictionary {best_dictionary['dictionary_bytes']:,} B, "
        f"multiband Truth {best_multiband_truth['multiband_truth_bytes']:,} B, "
        f"independent Truth {len(independent):,} B; {selected_kind}",
        flush=True,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clip-id", action="append")
    parser.add_argument("--levels", type=int, action="append", default=[])
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
    args = parser.parse_args()

    manifest = json.loads(
        args.prepared_manifest.read_text(encoding="utf-8")
    )
    manifest_clips = {item["id"]: item for item in manifest["clips"]}
    selected_ids = tuple(args.clip_id or DEFAULT_CLIPS)
    if any(clip_id not in manifest_clips for clip_id in selected_ids):
        raise ValueError("one or more requested R-145 clips are unavailable")
    levels = tuple(args.levels or (2, 3, 4))
    lengths = tuple(args.block_samples or (64, 128, 256))
    truth_sizes = tuple(args.truth_block_size or (1024, 4096, 16384))
    gate_started = time.perf_counter()

    sample_rate, synthetic = _synthetic_partial_band_source()
    results = {
        "synthetic-partial-band-mixture": _evaluate(
            "synthetic-partial-band-mixture",
            None,
            sample_rate,
            synthetic,
            levels=(3,),
            block_samples=(64,),
            truth_block_sizes=truth_sizes,
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
            levels=levels,
            block_samples=lengths,
            truth_block_sizes=truth_sizes,
        )

    report = {
        "schema": "resonith-r145-partial-spectrum-orbit-gate-1",
        "decision": "R-145",
        "status": (
            "lossless architecture diagnostic; not R-118 or an Opus claim"
        ),
        "source_revision": args.source_revision,
        "configuration": {
            "levels": levels,
            "block_samples": lengths,
            "truth_block_sizes": truth_sizes,
            "maximum_normalized_fit_error": 5.0e-2,
            "semantic_labels_used_for_matching": False,
            "mono_analysis_view": True,
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
