"""Run the R-113 LPS6 gate against complete-byte-bounded LPS5 evidence."""

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
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
)
from maf_p0.lapped_oracle import analyze_lapped_source  # noqa: E402
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


def _parse_sources(items: list[str] | None) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for item in items or []:
        clip_id, separator, raw_path = item.partition("=")
        if not separator or not clip_id or not raw_path:
            raise ValueError("--source must use clip-id=path")
        sources[clip_id] = Path(raw_path)
    return sources


def _prepared_sources(
    manifest_path: Path,
    directory: Path,
) -> tuple[dict[str, Path], dict[str, list[str]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "resonith-prepared-extended-audio-corpus-1":
        raise ValueError("unsupported prepared R-111 manifest")
    sources: dict[str, Path] = {}
    categories: dict[str, list[str]] = {}
    for item in manifest["clips"]:
        path = directory / item["output_file"]
        if _sha256_file(path) != item["output_sha256"]:
            raise ValueError(f"prepared source hash mismatch: {item['id']}")
        sources[item["id"]] = path
        categories[item["id"]] = list(item["categories"])
    return sources, categories


def _quality_non_regression(
    candidate: dict,
    baseline: dict,
    *,
    speech: bool,
) -> bool:
    epsilon = 1.0e-12
    passed = (
        candidate["waveform"]["snr_db"]
        >= baseline["waveform"]["snr_db"] - epsilon
        and candidate["spectral"]["log_mel_rmse"]
        <= baseline["spectral"]["log_mel_rmse"] + epsilon
    )
    if speech:
        passed = (
            passed
            and candidate["speech"]["stoi"]
            >= baseline["speech"]["stoi"] - epsilon
            and candidate["speech"]["estoi"]
            >= baseline["speech"]["estoi"] - epsilon
        )
    return bool(passed)


def _metric_delta(candidate: dict, baseline: dict) -> dict:
    delta = {
        "snr_db": (
            candidate["waveform"]["snr_db"]
            - baseline["waveform"]["snr_db"]
        ),
        "log_mel_rmse": (
            candidate["spectral"]["log_mel_rmse"]
            - baseline["spectral"]["log_mel_rmse"]
        ),
    }
    if "speech" in candidate and "speech" in baseline:
        delta["stoi"] = (
            candidate["speech"]["stoi"] - baseline["speech"]["stoi"]
        )
        delta["estoi"] = (
            candidate["speech"]["estoi"] - baseline["speech"]["estoi"]
        )
    return delta


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
    args = parser.parse_args()

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
    if not sources:
        raise ValueError("at least one explicit or prepared source is required")

    selected_ids = args.clip_id or list(sources)
    if any(item not in sources for item in selected_ids):
        raise ValueError("one or more requested clip IDs have no source")
    if any(item not in reference["clips"] for item in selected_ids):
        raise ValueError("one or more requested clip IDs have no LPS5 evidence")

    native_core = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    clips: dict[str, dict] = {}
    gate_started = time.perf_counter()
    for clip_id in selected_ids:
        evidence = reference["clips"][clip_id]
        gain_evidence = evidence["gain_shape"]
        source_path = sources[clip_id]
        sample_rate, samples = read_pcm16_channels(source_path)
        clip_categories = categories.get(
            clip_id,
            ["speech"] if clip_id == "speech" else ["music"],
        )
        speech = "speech" in clip_categories or clip_id == "speech"
        mode = "speech" if speech else "music"
        base_budget = int(gain_evidence["coefficients_per_frame"])
        packet_frames = max(
            512,
            round(sample_rate * 0.256 / 512) * 512,
        )

        reference_path = (
            args.reference_directory / clip_id / "gain-shape.resonith"
        )
        reference_payload = reference_path.read_bytes()
        reference_decoded = native_core.decode_lapped_compact_packets(
            reference_payload
        ).samples
        if reference_decoded.shape != samples.shape:
            raise ValueError(f"LPS5 shape mismatch: {clip_id}")

        clip_directory = args.output_directory / clip_id
        clip_directory.mkdir(parents=True, exist_ok=True)
        analysis_started = time.perf_counter()
        shared_analysis = analyze_lapped_source(
            samples,
            sample_rate,
            half_window=512,
            band_count=24,
            transform_backend="fixed",
            native_analyzer=native_core,
        )
        analysis_wall_seconds = time.perf_counter() - analysis_started
        candidates: list[dict] = []
        encoded_by_budget = {}
        for budget in (base_budget, base_budget + 1):
            started = time.perf_counter()
            encoded = encode_lapped_finite_packet_stream(
                samples,
                sample_rate,
                coefficients_per_frame=budget,
                packet_frames=packet_frames,
                half_window=512,
                band_count=24,
                selection_backend="gain-shape",
                value_entropy_backend="bounded",
                native_core=native_core,
                precomputed_analysis=shared_analysis,
            )
            wall_seconds = time.perf_counter() - started
            stream_name = f"lps6-b{budget}.resonith"
            (clip_directory / stream_name).write_bytes(encoded.payload)
            candidate = {
                "budget": budget,
                "bytes": len(encoded.payload),
                "sha256": _sha256_bytes(encoded.payload),
                "encode_wall_seconds": wall_seconds,
                "audio_seconds_per_wall_second": (
                    samples.shape[0] / sample_rate / wall_seconds
                ),
                "eligible_under_lps5_complete_bytes": (
                    len(encoded.payload) <= len(reference_payload)
                ),
                "stream_file": stream_name,
                "stream_report": encoded.report,
            }
            candidates.append(candidate)
            encoded_by_budget[budget] = encoded

        eligible = [
            item
            for item in candidates
            if item["eligible_under_lps5_complete_bytes"]
        ]
        selected_candidate = (
            max(eligible, key=lambda item: (item["budget"], -item["bytes"]))
            if eligible
            else None
        )
        if selected_candidate is None:
            selected_backend = "LPS5 fallback"
            selected_budget = base_budget
            selected_payload = reference_payload
            selected_reconstruction = reference_decoded
        else:
            selected_backend = "LPS6 bounded values"
            selected_budget = int(selected_candidate["budget"])
            selected = encoded_by_budget[selected_budget]
            selected_payload = selected.payload
            selected_reconstruction = selected.reconstruction

        selected_metrics = _diagnostics(
            samples,
            selected_reconstruction,
            sample_rate,
            mode,
        )
        baseline_metrics = gain_evidence["metrics"]
        if not _quality_non_regression(
            selected_metrics,
            baseline_metrics,
            speech=speech,
        ):
            base_candidate = next(
                (
                    item
                    for item in candidates
                    if (
                        item["budget"] == base_budget
                        and item["eligible_under_lps5_complete_bytes"]
                    )
                ),
                None,
            )
            if base_candidate is None:
                selected_backend = "LPS5 fallback"
                selected_budget = base_budget
                selected_payload = reference_payload
                selected_reconstruction = reference_decoded
            else:
                selected_backend = "LPS6 bounded values"
                selected_budget = base_budget
                selected = encoded_by_budget[base_budget]
                selected_payload = selected.payload
                selected_reconstruction = selected.reconstruction
            selected_metrics = _diagnostics(
                samples,
                selected_reconstruction,
                sample_rate,
                mode,
            )

        exact_base_pcm = np.array_equal(
            encoded_by_budget[base_budget].reconstruction,
            reference_decoded,
        )
        selected_stream = clip_directory / "selected.resonith"
        selected_wav = clip_directory / "selected-decoded.wav"
        selected_stream.write_bytes(selected_payload)
        write_pcm16_channels(
            selected_wav,
            sample_rate,
            selected_reconstruction,
        )
        opus_metrics = evidence.get("opus", {}).get("metrics")
        clips[clip_id] = {
            "categories": clip_categories,
            "source": {
                "file": source_path.name,
                "sha256": _sha256_file(source_path),
                "sample_rate": sample_rate,
                "frames": int(samples.shape[0]),
                "channels": int(samples.shape[1]),
            },
            "lps5_baseline": {
                "budget": base_budget,
                "bytes": len(reference_payload),
                "sha256": _sha256_bytes(reference_payload),
                "metrics": baseline_metrics,
            },
            "shared_analysis_wall_seconds": analysis_wall_seconds,
            "lps6_candidates": candidates,
            "base_budget_pcm_identical_to_lps5": exact_base_pcm,
            "selected": {
                "backend": selected_backend,
                "budget": selected_budget,
                "bytes": len(selected_payload),
                "sha256": _sha256_bytes(selected_payload),
                "stream_file": str(
                    selected_stream.relative_to(args.output_directory)
                ),
                "decoded_file": str(
                    selected_wav.relative_to(args.output_directory)
                ),
                "decoded_sha256": _sha256_file(selected_wav),
                "metrics": selected_metrics,
                "complete_byte_non_regression": (
                    len(selected_payload) <= len(reference_payload)
                ),
                "quality_non_regression": _quality_non_regression(
                    selected_metrics,
                    baseline_metrics,
                    speech=speech,
                ),
            },
            "deltas_vs_lps5": {
                "bytes": len(selected_payload) - len(reference_payload),
                **_metric_delta(selected_metrics, baseline_metrics),
            },
            "deltas_vs_opus": (
                None
                if opus_metrics is None
                else {
                    "bytes": (
                        len(selected_payload)
                        - int(evidence["opus"]["bytes"])
                    ),
                    **_metric_delta(selected_metrics, opus_metrics),
                }
            ),
        }
        print(
            f"{clip_id}: selected {selected_backend} b{selected_budget}, "
            f"{len(selected_payload)} / {len(reference_payload)} B, "
            f"SNR delta {clips[clip_id]['deltas_vs_lps5']['snr_db']:.4f} dB",
            flush=True,
        )

    passed = all(
        item["base_budget_pcm_identical_to_lps5"]
        and item["selected"]["complete_byte_non_regression"]
        and item["selected"]["quality_non_regression"]
        for item in clips.values()
    )
    report = {
        "schema": "resonith-bounded-value-entropy-gate-1",
        "decision": "R-113",
        "status": (
            "passed selected-corpus non-regression gate"
            if passed
            else "failed selected-corpus non-regression gate"
        ),
        "all_passed": passed,
        "selected_clip_ids": selected_ids,
        "reference_report_sha256": _sha256_file(args.reference_report),
        "native_core": {
            "file": args.native_core.name,
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
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
