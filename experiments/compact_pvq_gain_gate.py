"""Run the R-119 compact PVQ gain fast gate on five acoustic classes."""

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

from active_band_selection_gate import _diagnostics  # noqa: E402
from maf_p0.lapped_oracle import analyze_lapped_source  # noqa: E402
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.pvq_envelope_oracle import (  # noqa: E402
    encode_pvq_envelope_analysis,
)
from maf_p0.wav_io import (  # noqa: E402
    read_pcm16_channels,
    write_pcm16_channels,
)


DEFAULT_R111_IDS = (
    "ebu-sustained-sine",
    "ebu-pink-noise",
    "ebu-side-drum",
    "ebu-grand-piano",
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _stream_summary(encoded) -> dict:
    report = encoded.report
    return {
        "bytes": len(encoded.payload),
        "sha256": _sha256_bytes(encoded.payload),
        "snr_db": report["snr_db"],
        "logical_bits": report["logical_bits"],
        "count_bits": report["count_bits"],
        "gain_bits": report["gain_bits"],
        "shape_bits": report["shape_bits"],
        "maximum_pulses_per_frame": report["maximum_pulses_per_frame"],
        "gain_fraction_bits": report["gain_fraction_bits"],
        "persistent_gain_memory": report["persistent_gain_memory"],
        "stream_version": report["stream_version"],
    }


def _evaluate(
    clip_id: str,
    source_path: Path,
    *,
    mode: str,
    baseline_budget: int,
    reinvestment_budgets: tuple[int, ...],
    native_core: NativeMain0Decoder,
    output_directory: Path,
) -> dict:
    sample_rate, samples = read_pcm16_channels(source_path)
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
    legacy = encode_pvq_envelope_analysis(
        analysis,
        maximum_pulses_per_frame=baseline_budget,
    )
    legacy_seconds = time.perf_counter() - encode_started
    precision_variants = []
    encoded_by_budget = {}
    for fraction_bits in (3, 4, 5):
        for persistent in (False, True):
            started = time.perf_counter()
            encoded = encode_pvq_envelope_analysis(
                analysis,
                maximum_pulses_per_frame=baseline_budget,
                gain_fraction_bits=fraction_bits,
                persistent_gain_memory=persistent,
            )
            precision_variants.append(
                {
                    **_stream_summary(encoded),
                    "encode_wall_seconds": time.perf_counter() - started,
                }
            )
    for budget in reinvestment_budgets:
        started = time.perf_counter()
        encoded = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=budget,
            gain_fraction_bits=4,
            persistent_gain_memory=False,
        )
        encoded_by_budget[budget] = encoded
        precision_variants.append(
            {
                **_stream_summary(encoded),
                "encode_wall_seconds": time.perf_counter() - started,
                "reinvestment_candidate": True,
            }
        )

    eligible = [
        encoded
        for encoded in encoded_by_budget.values()
        if len(encoded.payload) <= len(legacy.payload)
    ]
    if not eligible:
        raise RuntimeError(f"no R-119 reinvestment candidate fits {clip_id}")
    selected = max(
        eligible,
        key=lambda encoded: (
            encoded.report["maximum_pulses_per_frame"],
            -len(encoded.payload),
        ),
    )
    legacy_metrics = _diagnostics(
        samples,
        legacy.reconstruction,
        sample_rate,
        mode,
    )
    selected_metrics = _diagnostics(
        samples,
        selected.reconstruction,
        sample_rate,
        mode,
    )

    clip_directory = output_directory / clip_id
    clip_directory.mkdir(parents=True, exist_ok=True)
    legacy_path = clip_directory / "legacy-pve1.resonith"
    selected_path = clip_directory / "selected-compact-gain.resonith"
    selected_wav = clip_directory / "selected-compact-gain-decoded.wav"
    legacy_path.write_bytes(legacy.payload)
    selected_path.write_bytes(selected.payload)
    write_pcm16_channels(
        selected_wav,
        sample_rate,
        selected.reconstruction,
    )

    snr_delta = (
        selected_metrics["waveform"]["snr_db"]
        - legacy_metrics["waveform"]["snr_db"]
    )
    log_mel_delta = (
        selected_metrics["spectral"]["log_mel_rmse"]
        - legacy_metrics["spectral"]["log_mel_rmse"]
    )
    hard_gate = bool(
        len(selected.payload) <= len(legacy.payload)
        and snr_delta > 0.0
        and log_mel_delta < 0.0
    )
    speech_delta = None
    if mode == "speech":
        speech_delta = {
            "stoi": (
                selected_metrics["speech"]["stoi"]
                - legacy_metrics["speech"]["stoi"]
            ),
            "estoi": (
                selected_metrics["speech"]["estoi"]
                - legacy_metrics["speech"]["estoi"]
            ),
        }
        hard_gate = bool(
            hard_gate
            and speech_delta["stoi"] > 0.0
            and speech_delta["estoi"] > 0.0
        )

    return {
        "source": {
            "file": source_path.name,
            "sha256": _sha256_file(source_path),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "analysis_wall_seconds": analysis_seconds,
        "legacy": {
            **_stream_summary(legacy),
            "encode_wall_seconds": legacy_seconds,
            "stream_file": str(
                legacy_path.relative_to(output_directory)
            ),
            "metrics": legacy_metrics,
        },
        "selected": {
            **_stream_summary(selected),
            "stream_file": str(
                selected_path.relative_to(output_directory)
            ),
            "decoded_file": str(
                selected_wav.relative_to(output_directory)
            ),
            "decoded_sha256": _sha256_file(selected_wav),
            "metrics": selected_metrics,
        },
        "deltas_vs_legacy": {
            "bytes": len(selected.payload) - len(legacy.payload),
            "snr_db": snr_delta,
            "log_mel_rmse": log_mel_delta,
            "speech": speech_delta,
        },
        "precision_and_reinvestment_frontier": precision_variants,
        "hard_gate_passed": hard_gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech-source", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--baseline-budget", type=int, default=96)
    parser.add_argument(
        "--reinvestment-budgets",
        type=int,
        nargs="+",
        default=(96, 128, 144, 160, 176, 192, 224),
    )
    parser.add_argument(
        "--r111-id",
        action="append",
        choices=DEFAULT_R111_IDS,
    )
    args = parser.parse_args()

    budgets = tuple(sorted(set(args.reinvestment_budgets)))
    if (
        args.baseline_budget <= 0
        or not budgets
        or budgets[0] <= 0
        or budgets[-1] > 512
    ):
        raise ValueError("invalid R-119 pulse budget")
    prepared = json.loads(
        args.prepared_manifest.read_text(encoding="utf-8")
    )
    prepared_by_id = {
        record["id"]: record for record in prepared["clips"]
    }
    selected_ids = tuple(args.r111_id or DEFAULT_R111_IDS)
    native_core = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)

    cases = [
        ("libri-speech", args.speech_source, "speech"),
        *[
            (
                clip_id,
                args.prepared_directory
                / prepared_by_id[clip_id]["output_file"],
                "music",
            )
            for clip_id in selected_ids
        ],
    ]
    started = time.perf_counter()
    clips = {}
    for clip_id, source_path, mode in cases:
        clips[clip_id] = _evaluate(
            clip_id,
            source_path,
            mode=mode,
            baseline_budget=args.baseline_budget,
            reinvestment_budgets=budgets,
            native_core=native_core,
            output_directory=args.output_directory,
        )
        result = clips[clip_id]
        print(
            f"{clip_id}: {result['selected']['bytes']} / "
            f"{result['legacy']['bytes']} B, "
            f"pulses {result['selected']['maximum_pulses_per_frame']}, "
            f"SNR {result['deltas_vs_legacy']['snr_db']:+.3f} dB, "
            f"log-mel {result['deltas_vs_legacy']['log_mel_rmse']:+.3f}, "
            f"{'pass' if result['hard_gate_passed'] else 'fail'}",
            flush=True,
        )

    report = {
        "schema": "resonith-compact-pvq-gain-gate-1",
        "decision": "R-119",
        "status": (
            "all five fast gates passed"
            if all(item["hard_gate_passed"] for item in clips.values())
            else "one or more fast gates failed"
        ),
        "all_fast_gates_passed": all(
            item["hard_gate_passed"] for item in clips.values()
        ),
        "source_revision": args.source_revision,
        "baseline_budget": args.baseline_budget,
        "reinvestment_budgets": list(budgets),
        "native_core": {
            "path": args.native_core.name,
            "sha256": _sha256_file(args.native_core),
        },
        "total_wall_seconds": time.perf_counter() - started,
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
