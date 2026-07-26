"""Run the R-103 encoder-only active-band coefficient selection gate."""

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

from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
)
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)
from objective_audio_metrics import (  # noqa: E402
    _align,
    _global_metrics,
    _load,
    _spectral_metrics,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized(samples: np.ndarray) -> np.ndarray:
    return samples.astype(np.float32) / 32768.0


def _diagnostics(
    reference: np.ndarray,
    degraded: np.ndarray,
    sample_rate: int,
    mode: str,
) -> dict:
    reference_float = _normalized(reference)
    degraded_float = _normalized(degraded)
    report = {
        "waveform": _global_metrics(
            reference_float,
            degraded_float,
            sample_rate,
        ),
        "spectral": _spectral_metrics(
            reference_float,
            degraded_float,
            sample_rate,
            mode,
        ),
    }
    if mode == "speech":
        from pystoi import stoi

        reference_mono = np.mean(reference_float, axis=1)
        degraded_mono = np.mean(degraded_float, axis=1)
        report["speech"] = {
            "stoi": float(
                stoi(
                    reference_mono,
                    degraded_mono,
                    sample_rate,
                    extended=False,
                )
            ),
            "estoi": float(
                stoi(
                    reference_mono,
                    degraded_mono,
                    sample_rate,
                    extended=True,
                )
            ),
        }
    return report


def _opus_diagnostics(
    source: Path,
    decoded: Path,
    mode: str,
) -> dict:
    reference, reference_rate = _load(source)
    degraded, degraded_rate = _load(decoded)
    if reference_rate != degraded_rate:
        raise ValueError("Opus comparison sample rates differ")
    reference, degraded, lag = _align(
        reference,
        degraded,
        reference_rate,
    )
    report = {
        "alignment_lag_samples": lag,
        "waveform": _global_metrics(reference, degraded, reference_rate),
        "spectral": _spectral_metrics(
            reference,
            degraded,
            reference_rate,
            mode,
        ),
    }
    if mode == "speech":
        from pystoi import stoi

        reference_mono = np.mean(reference, axis=1)
        degraded_mono = np.mean(degraded, axis=1)
        report["speech"] = {
            "stoi": float(
                stoi(
                    reference_mono,
                    degraded_mono,
                    reference_rate,
                    extended=False,
                )
            ),
            "estoi": float(
                stoi(
                    reference_mono,
                    degraded_mono,
                    reference_rate,
                    extended=True,
                )
            ),
        }
    return report


def _encode_clip(
    *,
    clip_id: str,
    source_path: Path,
    opus_path: Path,
    opus_decoded_path: Path,
    opus_decoder_version: str,
    mode: str,
    baseline_budget: int,
    output_directory: Path,
) -> dict:
    sample_rate, samples = read_pcm16_channels(source_path)
    started = time.perf_counter()
    analysis = analyze_lapped_source(
        samples,
        sample_rate,
        half_window=512,
        band_count=24,
        transform_backend="fixed",
    )
    analysis_seconds = time.perf_counter() - started
    baseline = encode_lapped_analysis(
        analysis,
        coefficients_per_frame=baseline_budget,
        entropy_backend="bounded",
        density_backend="adaptive",
        selection_backend="energy",
    )
    candidates = []
    for budget in range(
        max(1, baseline_budget - 8),
        min(512, baseline_budget + 8) + 1,
    ):
        encoded = encode_lapped_analysis(
            analysis,
            coefficients_per_frame=budget,
            entropy_backend="bounded",
            density_backend="adaptive",
            selection_backend="active-band",
        )
        candidates.append(encoded)
    selected = min(
        candidates,
        key=lambda result: (
            abs(len(result.payload) - len(baseline.payload)),
            len(result.payload) > len(baseline.payload),
            result.report["coefficients_per_frame"],
        ),
    )
    encode_seconds = time.perf_counter() - started

    clip_directory = output_directory / clip_id
    clip_directory.mkdir(parents=True, exist_ok=True)
    (clip_directory / "energy.lpf1").write_bytes(baseline.payload)
    (clip_directory / "active-band.lpf1").write_bytes(selected.payload)
    write_pcm16_channels(
        clip_directory / "energy-decoded.wav",
        sample_rate,
        baseline.reconstruction,
    )
    write_pcm16_channels(
        clip_directory / "active-band-decoded.wav",
        sample_rate,
        selected.reconstruction,
    )

    baseline_metrics = _diagnostics(
        samples,
        baseline.reconstruction,
        sample_rate,
        mode,
    )
    candidate_metrics = _diagnostics(
        samples,
        selected.reconstruction,
        sample_rate,
        mode,
    )
    opus_metrics = _opus_diagnostics(
        source_path,
        opus_decoded_path,
        mode,
    )
    byte_delta_fraction = (
        len(selected.payload) / len(baseline.payload) - 1.0
    )
    snr_delta = (
        candidate_metrics["waveform"]["snr_db"]
        - baseline_metrics["waveform"]["snr_db"]
    )
    if mode == "speech":
        gate_passed = bool(
            abs(byte_delta_fraction) <= 0.005
            and snr_delta >= -0.5
            and candidate_metrics["speech"]["stoi"]
                > baseline_metrics["speech"]["stoi"]
            and candidate_metrics["speech"]["estoi"]
                > baseline_metrics["speech"]["estoi"]
        )
    else:
        candidate_log_mel = candidate_metrics["spectral"]["log_mel_rmse"]
        baseline_log_mel = baseline_metrics["spectral"]["log_mel_rmse"]
        gate_passed = bool(
            abs(byte_delta_fraction) <= 0.005
            and snr_delta >= -0.5
            and candidate_log_mel <= baseline_log_mel * 1.03
        )

    return {
        "source": {
            "path": source_path.name,
            "bytes": source_path.stat().st_size,
            "sha256": _sha256(source_path.read_bytes()),
            "sample_rate": sample_rate,
            "channels": int(samples.shape[1]),
            "frames": int(samples.shape[0]),
        },
        "analysis_wall_seconds": analysis_seconds,
        "complete_experiment_wall_seconds": encode_seconds,
        "energy": {
            "coefficients_per_frame": baseline_budget,
            "bytes": len(baseline.payload),
            "sha256": _sha256(baseline.payload),
            "metrics": baseline_metrics,
        },
        "active_band": {
            "coefficients_per_frame": selected.report[
                "coefficients_per_frame"
            ],
            "bytes": len(selected.payload),
            "sha256": _sha256(selected.payload),
            "byte_delta_fraction": byte_delta_fraction,
            "snr_delta_db": snr_delta,
            "metrics": candidate_metrics,
        },
        "opus": {
            "bytes": opus_path.stat().st_size,
            "sha256": _sha256(opus_path.read_bytes()),
            "decoded_sha256": _sha256(opus_decoded_path.read_bytes()),
            "decoder_version": opus_decoder_version,
            "metrics": opus_metrics,
        },
        "fast_gate_passed": gate_passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech-source", type=Path, required=True)
    parser.add_argument("--speech-opus", type=Path, required=True)
    parser.add_argument("--speech-opus-decoded", type=Path, required=True)
    parser.add_argument("--speech-opus-decoder-version", required=True)
    parser.add_argument("--piano-source", type=Path, required=True)
    parser.add_argument("--piano-opus", type=Path, required=True)
    parser.add_argument("--piano-opus-decoded", type=Path, required=True)
    parser.add_argument("--piano-opus-decoder-version", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    clips = {
        "speech": _encode_clip(
            clip_id="speech",
            source_path=args.speech_source,
            opus_path=args.speech_opus,
            opus_decoded_path=args.speech_opus_decoded,
            opus_decoder_version=args.speech_opus_decoder_version,
            mode="speech",
            baseline_budget=64,
            output_directory=args.output_directory,
        ),
        "emotional-piano": _encode_clip(
            clip_id="emotional-piano",
            source_path=args.piano_source,
            opus_path=args.piano_opus,
            opus_decoded_path=args.piano_opus_decoded,
            opus_decoder_version=args.piano_opus_decoder_version,
            mode="music",
            baseline_budget=68,
            output_directory=args.output_directory,
        ),
    }
    report = {
        "schema": "resonith-active-band-selection-gate-1",
        "decision": "R-103",
        "status": (
            "fast gate passed; run complete Mozart promotion gate"
            if all(clip["fast_gate_passed"] for clip in clips.values())
            else "fast gate failed; do not run complete Mozart"
        ),
        "fast_gate_passed": all(
            clip["fast_gate_passed"] for clip in clips.values()
        ),
        "decoder_change": False,
        "bitstream_change": False,
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
