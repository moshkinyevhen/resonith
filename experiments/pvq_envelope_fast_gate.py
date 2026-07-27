"""Run the R-108 PVE1 fast frontier against R-107 and Opus decodes."""

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
    "ebu-electronic-tune",
    "ebu-female-speech-en",
    "ebu-male-speech-en",
    "ebu-claves",
    "ebu-side-drum",
    "ebu-grand-piano",
    "ebu-dense-orchestra",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _load_decode(path: Path, sample_rate: int, shape: tuple[int, int]):
    decoded_rate, decoded = read_pcm16_channels(path)
    if decoded_rate != sample_rate or decoded.shape != shape:
        raise ValueError(f"decoded configuration differs: {path}")
    return decoded


def _case(
    *,
    clip_id: str,
    mode: str,
    source_path: Path,
    baseline_stream_path: Path,
    baseline_decoded_path: Path,
    opus_stream_path: Path,
    opus_decoded_path: Path,
) -> dict:
    return {
        "id": clip_id,
        "mode": mode,
        "source_path": source_path,
        "baseline_stream_path": baseline_stream_path,
        "baseline_decoded_path": baseline_decoded_path,
        "opus_stream_path": opus_stream_path,
        "opus_decoded_path": opus_decoded_path,
    }


def _evaluate_case(
    record: dict,
    *,
    budgets: tuple[int, ...],
    active_power_ratio_q20: int,
    native_core: NativeMain0Decoder,
    output_directory: Path,
) -> dict:
    sample_rate, samples = read_pcm16_channels(record["source_path"])
    baseline_decoded = _load_decode(
        record["baseline_decoded_path"],
        sample_rate,
        samples.shape,
    )
    opus_decoded = _load_decode(
        record["opus_decoded_path"],
        sample_rate,
        samples.shape,
    )
    baseline_bytes = record["baseline_stream_path"].stat().st_size

    analysis_started = time.perf_counter()
    analysis = analyze_lapped_source(
        samples,
        sample_rate,
        half_window=512,
        band_count=24,
        native_analyzer=native_core,
    )
    analysis_seconds = time.perf_counter() - analysis_started
    candidates = []
    for budget in budgets:
        started = time.perf_counter()
        encoded = encode_pvq_envelope_analysis(
            analysis,
            maximum_pulses_per_frame=budget,
            minimum_active_power_ratio_q20=active_power_ratio_q20,
        )
        candidates.append(
            {
                "budget": budget,
                "result": encoded,
                "encode_wall_seconds": time.perf_counter() - started,
            }
        )
    selected = min(
        candidates,
        key=lambda candidate: (
            abs(len(candidate["result"].payload) - baseline_bytes),
            len(candidate["result"].payload),
        ),
    )
    baseline_metrics = _diagnostics(
        samples,
        baseline_decoded,
        sample_rate,
        record["mode"],
    )
    opus_metrics = _diagnostics(
        samples,
        opus_decoded,
        sample_rate,
        record["mode"],
    )
    selected_metrics = _diagnostics(
        samples,
        selected["result"].reconstruction,
        sample_rate,
        record["mode"],
    )

    clip_directory = output_directory / record["id"]
    clip_directory.mkdir(parents=True, exist_ok=True)
    stream_path = clip_directory / "pvq-envelope.resonith"
    decoded_path = clip_directory / "pvq-envelope-decoded.wav"
    stream_path.write_bytes(selected["result"].payload)
    write_pcm16_channels(
        decoded_path,
        sample_rate,
        selected["result"].reconstruction,
    )

    selected_bytes = len(selected["result"].payload)
    snr_delta = (
        selected_metrics["waveform"]["snr_db"]
        - baseline_metrics["waveform"]["snr_db"]
    )
    log_mel_ratio = (
        selected_metrics["spectral"]["log_mel_rmse"]
        / max(baseline_metrics["spectral"]["log_mel_rmse"], 1e-12)
    )
    hard_gate = bool(
        selected_bytes <= baseline_bytes
        and snr_delta >= 0.0
        and log_mel_ratio < 1.0
    )
    if record["mode"] == "speech":
        hard_gate = bool(
            hard_gate
            and selected_metrics["speech"]["stoi"]
                > baseline_metrics["speech"]["stoi"]
            and selected_metrics["speech"]["estoi"]
                > baseline_metrics["speech"]["estoi"]
        )
    return {
        "source": {
            "path": record["source_path"].name,
            "sha256": _sha256_file(record["source_path"]),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "baseline": {
            "bytes": baseline_bytes,
            "stream_sha256": _sha256_file(record["baseline_stream_path"]),
            "decoded_sha256": _sha256_file(record["baseline_decoded_path"]),
            "metrics": baseline_metrics,
        },
        "opus": {
            "bytes": record["opus_stream_path"].stat().st_size,
            "stream_sha256": _sha256_file(record["opus_stream_path"]),
            "decoded_sha256": _sha256_file(record["opus_decoded_path"]),
            "metrics": opus_metrics,
        },
        "selected": {
            "budget": selected["budget"],
            "bytes": selected_bytes,
            "stream_sha256": _sha256_file(stream_path),
            "decoded_sha256": _sha256_file(decoded_path),
            "analysis_wall_seconds": analysis_seconds,
            "encode_wall_seconds": selected["encode_wall_seconds"],
            "snr_delta_db_vs_r107": snr_delta,
            "log_mel_ratio_vs_r107": log_mel_ratio,
            "metrics": selected_metrics,
            **selected["result"].report,
        },
        "frontier": [
            {
                "budget": candidate["budget"],
                "bytes": len(candidate["result"].payload),
                "encode_wall_seconds": candidate["encode_wall_seconds"],
                "logical_bits": candidate["result"].report["logical_bits"],
                "count_bits": candidate["result"].report["count_bits"],
                "gain_bits": candidate["result"].report["gain_bits"],
                "shape_bits": candidate["result"].report["shape_bits"],
                "snr_db": candidate["result"].report["snr_db"],
            }
            for candidate in candidates
        ],
        "hard_gate_passed": hard_gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech-source", type=Path, required=True)
    parser.add_argument("--speech-r107", type=Path, required=True)
    parser.add_argument("--speech-r107-decoded", type=Path, required=True)
    parser.add_argument("--speech-opus", type=Path, required=True)
    parser.add_argument("--speech-opus-decoded", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--r111-r107-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=(32, 48, 64, 96, 128, 160, 192, 224),
    )
    parser.add_argument(
        "--r111-id",
        action="append",
        choices=DEFAULT_R111_IDS,
    )
    parser.add_argument(
        "--active-power-ratio-q20",
        type=int,
        default=10,
    )
    args = parser.parse_args()
    budgets = tuple(sorted(set(args.budgets)))
    if not budgets or budgets[0] <= 0:
        raise ValueError("PVE1 budgets must be positive")

    prepared = json.loads(args.prepared_manifest.read_text(encoding="utf-8"))
    prepared_by_id = {record["id"]: record for record in prepared["clips"]}
    selected_ids = tuple(args.r111_id or DEFAULT_R111_IDS)
    cases = [
        _case(
            clip_id="libri-speech",
            mode="speech",
            source_path=args.speech_source,
            baseline_stream_path=args.speech_r107,
            baseline_decoded_path=args.speech_r107_decoded,
            opus_stream_path=args.speech_opus,
            opus_decoded_path=args.speech_opus_decoded,
        )
    ]
    for clip_id in selected_ids:
        record = prepared_by_id[clip_id]
        root = args.r111_r107_directory / clip_id
        cases.append(
            _case(
                clip_id=clip_id,
                mode=(
                    "speech"
                    if "speech" in record["categories"]
                    else "music"
                ),
                source_path=args.prepared_directory / record["output_file"],
                baseline_stream_path=root / "gain-shape.resonith",
                baseline_decoded_path=root / "gain-shape-decoded.wav",
                opus_stream_path=root / "opus.opus",
                opus_decoded_path=root / "opus-decoded.wav",
            )
        )

    native_core = NativeMain0Decoder(args.native_core)
    args.output_directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    clips = {}
    for record in cases:
        clips[record["id"]] = _evaluate_case(
            record,
            budgets=budgets,
            active_power_ratio_q20=args.active_power_ratio_q20,
            native_core=native_core,
            output_directory=args.output_directory,
        )
        result = clips[record["id"]]
        print(
            f"{record['id']}: PVE1 {result['selected']['bytes']} B / "
            f"R-107 {result['baseline']['bytes']} B, "
            f"SNR delta {result['selected']['snr_delta_db_vs_r107']:.3f} dB, "
            f"log-mel ratio {result['selected']['log_mel_ratio_vs_r107']:.3f}",
            flush=True,
        )
    report = {
        "schema": "resonith-pvq-envelope-fast-gate-1",
        "decision": "R-108",
        "status": (
            "all selected fast gates passed"
            if all(record["hard_gate_passed"] for record in clips.values())
            else "one or more fast gates failed; PVE1 remains an oracle"
        ),
        "all_fast_gates_passed": all(
            record["hard_gate_passed"] for record in clips.values()
        ),
        "budgets": list(budgets),
        "active_power_ratio_q20": args.active_power_ratio_q20,
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
