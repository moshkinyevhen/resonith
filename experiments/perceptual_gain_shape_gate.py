"""Run the R-107 complete-transport gain-shape evidence gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from active_band_selection_gate import (  # noqa: E402
    _diagnostics,
    _opus_diagnostics,
)
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _load_matching_decode(
    path: Path,
    sample_rate: int,
    shape: tuple[int, int],
):
    decoded_rate, decoded = read_pcm16_channels(path)
    if decoded_rate != sample_rate or decoded.shape != shape:
        raise ValueError("existing decoder output configuration differs")
    return decoded


def _encode_candidate(
    samples,
    sample_rate: int,
    *,
    coefficients_per_frame: int,
    half_window: int,
    band_count: int,
    frame_whitening: float,
    band_whitening: float,
    native_core: NativeMain0Decoder,
):
    packet_frames = max(
        half_window,
        round(sample_rate * 0.256 / half_window) * half_window,
    )
    return encode_lapped_finite_packet_stream(
        samples,
        sample_rate,
        coefficients_per_frame=coefficients_per_frame,
        packet_frames=packet_frames,
        half_window=half_window,
        band_count=band_count,
        selection_backend="gain-shape",
        frame_whitening=frame_whitening,
        band_whitening=band_whitening,
        native_core=native_core,
    )


def _evaluate_clip(
    *,
    clip_id: str,
    mode: str,
    source_path: Path,
    baseline_path: Path,
    baseline_decoded_path: Path,
    opus_path: Path,
    opus_decoded_path: Path,
    opus_decoder_version: str,
    output_directory: Path,
    candidate_budget: int,
    candidate_half_window: int,
    candidate_band_count: int,
    candidate_frame_whitening: float = 0.0,
    candidate_band_whitening: float = 0.0,
    include_short_frontier: bool = False,
    native_core: NativeMain0Decoder,
) -> dict:
    sample_rate, samples = read_pcm16_channels(source_path)
    baseline_decoded = _load_matching_decode(
        baseline_decoded_path,
        sample_rate,
        samples.shape,
    )
    started = time.perf_counter()
    candidate = _encode_candidate(
        samples,
        sample_rate,
        coefficients_per_frame=candidate_budget,
        half_window=candidate_half_window,
        band_count=candidate_band_count,
        frame_whitening=candidate_frame_whitening,
        band_whitening=candidate_band_whitening,
        native_core=native_core,
    )
    candidate_seconds = time.perf_counter() - started
    baseline_metrics = _diagnostics(
        samples,
        baseline_decoded,
        sample_rate,
        mode,
    )
    candidate_metrics = _diagnostics(
        samples,
        candidate.reconstruction,
        sample_rate,
        mode,
    )
    opus_metrics = _opus_diagnostics(
        source_path,
        opus_decoded_path,
        mode,
    )

    clip_directory = output_directory / clip_id
    clip_directory.mkdir(parents=True, exist_ok=True)
    candidate_path = clip_directory / "gain-shape.resonith"
    candidate_decoded_path = clip_directory / "gain-shape-decoded.wav"
    candidate_path.write_bytes(candidate.payload)
    write_pcm16_channels(
        candidate_decoded_path,
        sample_rate,
        candidate.reconstruction,
    )

    snr_delta = (
        candidate_metrics["waveform"]["snr_db"]
        - baseline_metrics["waveform"]["snr_db"]
    )
    log_mel_ratio = (
        candidate_metrics["spectral"]["log_mel_rmse"]
        / baseline_metrics["spectral"]["log_mel_rmse"]
    )
    rate_delta_vs_opus = len(candidate.payload) / opus_path.stat().st_size - 1.0
    if mode == "speech":
        admission_passed = bool(
            len(candidate.payload) <= opus_path.stat().st_size
            and snr_delta >= -0.5
            and log_mel_ratio < 1.0
            and candidate_metrics["speech"]["stoi"]
                > baseline_metrics["speech"]["stoi"]
            and candidate_metrics["speech"]["estoi"]
                > baseline_metrics["speech"]["estoi"]
        )
        breakthrough_passed = bool(
            len(candidate.payload) <= opus_path.stat().st_size
            and candidate_metrics["speech"]["stoi"]
                > opus_metrics["speech"]["stoi"]
            and candidate_metrics["speech"]["estoi"]
                > opus_metrics["speech"]["estoi"]
        )
    else:
        admission_passed = bool(
            abs(rate_delta_vs_opus) <= 0.005
            and snr_delta >= -0.5
            and log_mel_ratio <= 1.03
        )
        breakthrough_passed = False

    record = {
        "source": {
            "path": source_path.name,
            "bytes": source_path.stat().st_size,
            "sha256": _sha256_file(source_path),
            "sample_rate": sample_rate,
            "channels": int(samples.shape[1]),
            "frames": int(samples.shape[0]),
        },
        "baseline": {
            "path": baseline_path.name,
            "bytes": baseline_path.stat().st_size,
            "sha256": _sha256_file(baseline_path),
            "decoded_path": baseline_decoded_path.name,
            "decoded_sha256": _sha256_file(baseline_decoded_path),
            "metrics": baseline_metrics,
        },
        "gain_shape": {
            "path": candidate_path.name,
            "bytes": len(candidate.payload),
            "sha256": _sha256_file(candidate_path),
            "decoded_path": candidate_decoded_path.name,
            "decoded_sha256": _sha256_file(candidate_decoded_path),
            "encode_wall_seconds": candidate_seconds,
            "snr_delta_db": snr_delta,
            "log_mel_ratio": log_mel_ratio,
            "rate_delta_vs_opus": rate_delta_vs_opus,
            "metrics": candidate_metrics,
            **candidate.report,
        },
        "opus": {
            "path": opus_path.name,
            "bytes": opus_path.stat().st_size,
            "sha256": _sha256_file(opus_path),
            "decoded_path": opus_decoded_path.name,
            "decoded_sha256": _sha256_file(opus_decoded_path),
            "decoder_version": opus_decoder_version,
            "metrics": opus_metrics,
        },
        "admission_gate_passed": admission_passed,
        "breakthrough_target_passed": breakthrough_passed,
    }

    if include_short_frontier:
        frontier_started = time.perf_counter()
        frontier = _encode_candidate(
            samples,
            sample_rate,
            coefficients_per_frame=30,
            half_window=256,
            band_count=12,
            frame_whitening=0.1,
            band_whitening=0.5,
            native_core=native_core,
        )
        frontier_seconds = time.perf_counter() - frontier_started
        frontier_metrics = _diagnostics(
            samples,
            frontier.reconstruction,
            sample_rate,
            mode,
        )
        frontier_path = clip_directory / "short-lattice-frontier.resonith"
        frontier_decoded_path = (
            clip_directory / "short-lattice-frontier-decoded.wav"
        )
        frontier_path.write_bytes(frontier.payload)
        write_pcm16_channels(
            frontier_decoded_path,
            sample_rate,
            frontier.reconstruction,
        )
        record["short_lattice_frontier"] = {
            "path": frontier_path.name,
            "bytes": len(frontier.payload),
            "sha256": _sha256_file(frontier_path),
            "decoded_sha256": _sha256_file(frontier_decoded_path),
            "encode_wall_seconds": frontier_seconds,
            "metrics": frontier_metrics,
            **frontier.report,
        }
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech-source", type=Path, required=True)
    parser.add_argument("--speech-baseline", type=Path, required=True)
    parser.add_argument("--speech-baseline-decoded", type=Path, required=True)
    parser.add_argument("--speech-opus", type=Path, required=True)
    parser.add_argument("--speech-opus-decoded", type=Path, required=True)
    parser.add_argument("--speech-opus-decoder-version", required=True)
    parser.add_argument("--piano-source", type=Path, required=True)
    parser.add_argument("--piano-baseline", type=Path, required=True)
    parser.add_argument("--piano-baseline-decoded", type=Path, required=True)
    parser.add_argument("--piano-opus", type=Path, required=True)
    parser.add_argument("--piano-opus-decoded", type=Path, required=True)
    parser.add_argument("--piano-opus-decoder-version", required=True)
    parser.add_argument("--mozart-source", type=Path, required=True)
    parser.add_argument("--mozart-baseline", type=Path, required=True)
    parser.add_argument("--mozart-baseline-decoded", type=Path, required=True)
    parser.add_argument("--mozart-opus", type=Path, required=True)
    parser.add_argument("--mozart-opus-decoded", type=Path, required=True)
    parser.add_argument("--mozart-opus-decoder-version", required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    native_core = NativeMain0Decoder(args.native_core)

    clips = {
        "speech": _evaluate_clip(
            clip_id="speech",
            mode="speech",
            source_path=args.speech_source,
            baseline_path=args.speech_baseline,
            baseline_decoded_path=args.speech_baseline_decoded,
            opus_path=args.speech_opus,
            opus_decoded_path=args.speech_opus_decoded,
            opus_decoder_version=args.speech_opus_decoder_version,
            output_directory=args.output_directory,
            candidate_budget=67,
            candidate_half_window=512,
            candidate_band_count=24,
            include_short_frontier=True,
            native_core=native_core,
        ),
        "emotional-piano": _evaluate_clip(
            clip_id="emotional-piano",
            mode="music",
            source_path=args.piano_source,
            baseline_path=args.piano_baseline,
            baseline_decoded_path=args.piano_baseline_decoded,
            opus_path=args.piano_opus,
            opus_decoded_path=args.piano_opus_decoded,
            opus_decoder_version=args.piano_opus_decoder_version,
            output_directory=args.output_directory,
            candidate_budget=71,
            candidate_half_window=512,
            candidate_band_count=24,
            native_core=native_core,
        ),
        "mozart-full": _evaluate_clip(
            clip_id="mozart-full",
            mode="music",
            source_path=args.mozart_source,
            baseline_path=args.mozart_baseline,
            baseline_decoded_path=args.mozart_baseline_decoded,
            opus_path=args.mozart_opus,
            opus_decoded_path=args.mozart_opus_decoded,
            opus_decoder_version=args.mozart_opus_decoder_version,
            output_directory=args.output_directory,
            candidate_budget=72,
            candidate_half_window=512,
            candidate_band_count=24,
            native_core=native_core,
        ),
    }
    report = {
        "schema": "resonith-perceptual-gain-shape-gate-1",
        "decision": "R-107",
        "status": (
            "cross-content admission gate passed; breakthrough target failed"
            if all(
                clip["admission_gate_passed"]
                for clip in clips.values()
            )
            and not clips["speech"]["breakthrough_target_passed"]
            else "cross-content admission gate failed"
        ),
        "cross_content_admission_passed": all(
            clip["admission_gate_passed"] for clip in clips.values()
        ),
        "speech_breakthrough_target_passed": clips["speech"][
            "breakthrough_target_passed"
        ],
        "decoder_change": False,
        "bitstream_change": False,
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
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
