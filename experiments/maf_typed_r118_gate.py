"""Run typed MAF plus Truth against the complete R-118 evidence union."""

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

from active_band_selection_gate import _diagnostics  # noqa: E402
from bounded_value_entropy_gate import (  # noqa: E402
    _metric_delta,
    _parse_sources,
    _prepared_sources,
)
from maf_typed_truth_fast_gate import _quality_guard  # noqa: E402
from maf_p0.maf_typed_candidate import (  # noqa: E402
    encode_maf_typed_truth_candidate,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _selected_path(root: Path, clip_id: str, field: str) -> Path:
    normalized = field.replace("\\", "/")
    for candidate in (
        root / normalized,
        root / clip_id / Path(normalized).name,
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing selected artifact: {field}")


def _load_references(
    report_paths: list[Path],
    directories: list[Path],
) -> dict[str, tuple[dict, Path]]:
    if len(report_paths) != len(directories):
        raise ValueError("reference report and directory counts must match")
    references: dict[str, tuple[dict, Path]] = {}
    for report_path, directory in zip(report_paths, directories, strict=True):
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for clip_id, evidence in report["clips"].items():
            if clip_id in references:
                raise ValueError(f"duplicate reference clip: {clip_id}")
            references[clip_id] = (evidence, directory)
    return references


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-report", type=Path, action="append", required=True)
    parser.add_argument(
        "--reference-directory",
        type=Path,
        action="append",
        required=True,
    )
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path)
    parser.add_argument("--prepared-directory", type=Path)
    parser.add_argument("--source", action="append")
    parser.add_argument("--clip-id", action="append")
    parser.add_argument("--segment-milliseconds", type=float, default=240.0)
    parser.add_argument("--filter-order", type=int, default=10)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    references = _load_references(
        args.reference_report,
        args.reference_directory,
    )
    sources = _parse_sources(args.source)
    categories: dict[str, list[str]] = {}
    if args.prepared_manifest is not None:
        if args.prepared_directory is None:
            raise ValueError("--prepared-directory is required with its manifest")
        prepared_sources, prepared_categories = _prepared_sources(
            args.prepared_manifest,
            args.prepared_directory,
        )
        sources.update(prepared_sources)
        categories.update(prepared_categories)
    selected_ids = args.clip_id or list(sources)
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("duplicate clip identifier")
    if any(clip_id not in sources for clip_id in selected_ids):
        raise ValueError("one or more clips have no source")
    if any(clip_id not in references for clip_id in selected_ids):
        raise ValueError("one or more clips have no preceding reference")

    native_core = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    gate_started = time.perf_counter()
    clips: dict[str, dict] = {}
    for clip_id in selected_ids:
        item_started = time.perf_counter()
        source_path = sources[clip_id]
        reference, reference_directory = references[clip_id]
        sample_rate, samples = read_pcm16_channels(source_path)
        clip_categories = categories.get(
            clip_id,
            ["speech"] if clip_id == "speech" else ["music"],
        )
        mode = "speech" if "speech" in clip_categories else "music"
        budget = int(
            reference["candidate"]["stream_report"]["coefficients_per_frame"]
        )

        baseline_path = _selected_path(
            reference_directory,
            clip_id,
            reference["selected"]["stream_file"],
        )
        baseline_payload = baseline_path.read_bytes()
        baseline_decoded = native_core.decode_lapped_compact_packets(
            baseline_payload
        ).samples
        if baseline_decoded.shape != samples.shape:
            raise ValueError(f"baseline shape mismatch: {clip_id}")

        candidate = encode_maf_typed_truth_candidate(
            samples,
            sample_rate,
            native_decoder=native_core,
            coefficients_per_frame=budget,
            segment_milliseconds=args.segment_milliseconds,
            filter_order=args.filter_order,
            half_window=512,
            band_count=24,
        )
        candidate_metrics = _diagnostics(
            samples,
            candidate.reconstruction,
            sample_rate,
            mode,
        )
        baseline_metrics = _diagnostics(
            samples,
            baseline_decoded,
            sample_rate,
            mode,
        )
        guard = _quality_guard(candidate_metrics, baseline_metrics)
        byte_non_regression = len(candidate.payload) <= len(baseline_payload)
        eligible = bool(byte_non_regression and guard["passed"])
        selected_payload = candidate.payload if eligible else baseline_payload
        selected_reconstruction = (
            candidate.reconstruction if eligible else baseline_decoded
        )

        clip_directory = args.output_directory / clip_id
        clip_directory.mkdir(parents=True, exist_ok=True)
        candidate_path = clip_directory / "candidate.resonith"
        candidate_wav = clip_directory / "candidate-decoded.wav"
        selected_path = clip_directory / "selected.resonith"
        selected_wav = clip_directory / "selected-decoded.wav"
        candidate_path.write_bytes(candidate.payload)
        selected_path.write_bytes(selected_payload)
        write_pcm16_channels(
            candidate_wav,
            sample_rate,
            candidate.reconstruction,
        )
        write_pcm16_channels(
            selected_wav,
            sample_rate,
            selected_reconstruction,
        )
        clips[clip_id] = {
            "categories": clip_categories,
            "source": {
                "file": source_path.name,
                "bytes": source_path.stat().st_size,
                "sha256": _sha256_file(source_path),
                "sample_rate": sample_rate,
                "frames": int(samples.shape[0]),
                "channels": int(samples.shape[1]),
            },
            "preceding": {
                "backend": reference["selected"]["backend"],
                "bytes": len(baseline_payload),
                "sha256": _sha256_bytes(baseline_payload),
                "metrics": baseline_metrics,
            },
            "candidate": {
                "bytes": len(candidate.payload),
                "sha256": _sha256_bytes(candidate.payload),
                "stream_file": str(
                    candidate_path.relative_to(args.output_directory)
                ),
                "decoded_file": str(
                    candidate_wav.relative_to(args.output_directory)
                ),
                "decoded_sha256": _sha256_file(candidate_wav),
                "metrics": candidate_metrics,
                "deltas_vs_preceding": _metric_delta(
                    candidate_metrics,
                    baseline_metrics,
                ),
                "byte_non_regression": byte_non_regression,
                "quality_guard": guard,
                "eligible": eligible,
                "encoder_report": candidate.report,
            },
            "selected": {
                "backend": (
                    "R-131 typed MAF plus Truth"
                    if eligible
                    else "exact preceding Resonith fallback"
                ),
                "bytes": len(selected_payload),
                "sha256": _sha256_bytes(selected_payload),
                "stream_file": str(
                    selected_path.relative_to(args.output_directory)
                ),
                "decoded_file": str(
                    selected_wav.relative_to(args.output_directory)
                ),
                "decoded_sha256": _sha256_file(selected_wav),
            },
            "wall_seconds": time.perf_counter() - item_started,
        }
        delta = clips[clip_id]["candidate"]["deltas_vs_preceding"]
        print(
            f"{clip_id}: {len(candidate.payload)} / "
            f"{len(baseline_payload)} B, "
            f"SNR {delta['snr_db']:+.6f} dB, "
            f"log-mel {delta['log_mel_rmse']:+.6f}, "
            f"{'selected' if eligible else 'fallback'}",
            flush=True,
        )

    selected_count = sum(
        int(record["candidate"]["eligible"]) for record in clips.values()
    )
    report = {
        "schema": "resonith-maf-typed-r118-gate-1",
        "decision": "R-131/R-135",
        "status": (
            "complete R-118 architecture gate; Opus and listening pending"
        ),
        "source_revision": args.source_revision,
        "configuration": {
            "segment_milliseconds": args.segment_milliseconds,
            "filter_order": args.filter_order,
            "half_window": 512,
            "band_count": 24,
        },
        "evaluated_clip_count": len(clips),
        "selected_clip_count": selected_count,
        "fallback_clip_count": len(clips) - selected_count,
        "total_wall_seconds": time.perf_counter() - gate_started,
        "native_core": {
            "path": args.native_core.name,
            "sha256": _sha256_file(args.native_core),
        },
        "clips": clips,
    }
    report_path = args.output_directory / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
