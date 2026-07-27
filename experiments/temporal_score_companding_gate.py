"""Measure R-117 temporal score companding with exact stream fallback."""

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
    _quality_non_regression,
)
from maf_p0.lapped_oracle import analyze_lapped_source  # noqa: E402
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
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
    """Resolve a report-relative selected artifact without trusting filenames."""

    normalized = field.replace("\\", "/")
    candidate = root / normalized
    if candidate.is_file():
        return candidate
    candidate = root / clip_id / Path(normalized).name
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"missing selected artifact: {field}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--reference-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path)
    parser.add_argument("--prepared-directory", type=Path)
    parser.add_argument("--source", action="append")
    parser.add_argument("--clip-id", action="append")
    parser.add_argument("--frame-whitening", type=float, default=0.02)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    if not 0.0 <= args.frame_whitening <= 1.0:
        raise ValueError("--frame-whitening must be in [0, 1]")
    reference = json.loads(
        args.reference_report.read_text(encoding="utf-8")
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
    if not selected_ids:
        raise ValueError("at least one clip is required")
    if any(clip_id not in sources for clip_id in selected_ids):
        raise ValueError("one or more clips have no source")
    if any(clip_id not in reference["clips"] for clip_id in selected_ids):
        raise ValueError("one or more clips have no R-113 evidence")

    native_core = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    clips: dict[str, dict] = {}
    gate_started = time.perf_counter()

    for clip_id in selected_ids:
        evidence = reference["clips"][clip_id]
        selected_evidence = evidence["selected"]
        source_path = sources[clip_id]
        sample_rate, samples = read_pcm16_channels(source_path)
        clip_categories = categories.get(
            clip_id,
            ["speech"] if clip_id == "speech" else ["music"],
        )
        speech = "speech" in clip_categories or clip_id == "speech"
        mode = "speech" if speech else "music"
        budget = int(selected_evidence["budget"])
        packet_frames = max(
            512,
            round(sample_rate * 0.256 / 512) * 512,
        )

        baseline_stream_path = _selected_path(
            args.reference_directory,
            clip_id,
            selected_evidence["stream_file"],
        )
        baseline_payload = baseline_stream_path.read_bytes()
        baseline_decoded = native_core.decode_lapped_compact_packets(
            baseline_payload
        ).samples
        if baseline_decoded.shape != samples.shape:
            raise ValueError(f"baseline shape mismatch: {clip_id}")
        baseline_metrics = _diagnostics(
            samples,
            baseline_decoded,
            sample_rate,
            mode,
        )

        analysis_started = time.perf_counter()
        analysis = analyze_lapped_source(
            samples,
            sample_rate,
            half_window=512,
            band_count=24,
            transform_backend="fixed",
            native_analyzer=native_core,
        )
        analysis_seconds = time.perf_counter() - analysis_started
        encode_started = time.perf_counter()
        candidate = encode_lapped_finite_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=512,
            band_count=24,
            selection_backend="gain-shape",
            frame_whitening=args.frame_whitening,
            band_whitening=0.0,
            value_entropy_backend="bounded",
            native_core=native_core,
            precomputed_analysis=analysis,
        )
        encode_seconds = time.perf_counter() - encode_started
        candidate_metrics = _diagnostics(
            samples,
            candidate.reconstruction,
            sample_rate,
            mode,
        )
        candidate_eligible = bool(
            len(candidate.payload) <= len(baseline_payload)
            and _quality_non_regression(
                candidate_metrics,
                baseline_metrics,
                speech=speech,
            )
            and not np.array_equal(candidate.reconstruction, baseline_decoded)
        )

        clip_directory = args.output_directory / clip_id
        clip_directory.mkdir(parents=True, exist_ok=True)
        candidate_path = clip_directory / "candidate.resonith"
        candidate_wav = clip_directory / "candidate-decoded.wav"
        candidate_path.write_bytes(candidate.payload)
        write_pcm16_channels(
            candidate_wav,
            sample_rate,
            candidate.reconstruction,
        )
        if candidate_eligible:
            selected_backend = "R-117 temporal score companding"
            selected_payload = candidate.payload
            selected_reconstruction = candidate.reconstruction
            selected_metrics = candidate_metrics
        else:
            selected_backend = "R-113 exact fallback"
            selected_payload = baseline_payload
            selected_reconstruction = baseline_decoded
            selected_metrics = baseline_metrics
        selected_path = clip_directory / "selected.resonith"
        selected_wav = clip_directory / "selected-decoded.wav"
        selected_path.write_bytes(selected_payload)
        write_pcm16_channels(
            selected_wav,
            sample_rate,
            selected_reconstruction,
        )

        clips[clip_id] = {
            "categories": clip_categories,
            "source": {
                "file": source_path.name,
                "sha256": _sha256_file(source_path),
                "sample_rate": sample_rate,
                "frames": int(samples.shape[0]),
                "channels": int(samples.shape[1]),
            },
            "baseline": {
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
                "deltas_vs_baseline": _metric_delta(
                    candidate_metrics,
                    baseline_metrics,
                ),
                "complete_byte_non_regression": (
                    len(candidate.payload) <= len(baseline_payload)
                ),
                "quality_non_regression": _quality_non_regression(
                    candidate_metrics,
                    baseline_metrics,
                    speech=speech,
                ),
                "eligible": candidate_eligible,
                "analysis_wall_seconds": analysis_seconds,
                "encode_wall_seconds": encode_seconds,
                "stream_report": candidate.report,
            },
            "selected": {
                "backend": selected_backend,
                "bytes": len(selected_payload),
                "sha256": _sha256_bytes(selected_payload),
                "stream_file": str(
                    selected_path.relative_to(args.output_directory)
                ),
                "decoded_file": str(
                    selected_wav.relative_to(args.output_directory)
                ),
                "decoded_sha256": _sha256_file(selected_wav),
                "metrics": selected_metrics,
            },
        }
        delta = clips[clip_id]["candidate"]["deltas_vs_baseline"]
        print(
            f"{clip_id}: {len(candidate.payload)} / "
            f"{len(baseline_payload)} B, "
            f"SNR {delta['snr_db']:+.6f} dB, "
            f"log-mel {delta['log_mel_rmse']:+.6f}, "
            f"{'selected' if candidate_eligible else 'fallback'}",
            flush=True,
        )

    selected_count = sum(
        item["candidate"]["eligible"] for item in clips.values()
    )
    report = {
        "schema": "resonith-temporal-score-companding-gate-1",
        "decision": "R-117",
        "status": (
            "one or more clips selected the candidate"
            if selected_count
            else "all clips retained the exact R-113 fallback"
        ),
        "frame_whitening": args.frame_whitening,
        "band_whitening": 0.0,
        "source_revision": args.source_revision,
        "selected_clip_count": selected_count,
        "evaluated_clip_count": len(clips),
        "native_core": {
            "path": args.native_core.name,
            "sha256": _sha256_file(args.native_core),
        },
        "total_wall_seconds": time.perf_counter() - gate_started,
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
