"""Run the R-107 gain-shape gate across the prepared R-111 corpus."""

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
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.opus_anchor import (  # noqa: E402
    OpusAnchorResult,
    OpusTools,
    resolve_opus_tools,
    run_opus_multichannel_anchor,
)
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


def _encode(
    samples,
    sample_rate: int,
    *,
    budget: int,
    selection_backend: str,
    native_core: NativeMain0Decoder,
):
    half_window = 512
    packet_frames = max(
        half_window,
        round(sample_rate * 0.256 / half_window) * half_window,
    )
    return encode_lapped_finite_packet_stream(
        samples,
        sample_rate,
        coefficients_per_frame=budget,
        packet_frames=packet_frames,
        half_window=half_window,
        band_count=24,
        selection_backend=selection_backend,
        native_core=native_core,
    )


def _matched_opus(
    samples,
    sample_rate: int,
    *,
    target_bytes: int,
    application: str,
    tools: OpusTools,
) -> OpusAnchorResult:
    """Find the nearest complete Ogg size with a bounded bitrate search."""

    channels = int(samples.shape[1])
    low = 6.0
    high = 256.0 * channels
    tried: dict[float, OpusAnchorResult] = {}

    def evaluate(bitrate: float) -> OpusAnchorResult:
        key = round(bitrate, 4)
        if key not in tried:
            tried[key] = run_opus_multichannel_anchor(
                samples,
                sample_rate,
                bitrate_kbps=key,
                mode="vbr",
                application=application,
                frame_size_ms=20.0,
                tools=tools,
            )
        return tried[key]

    # VBR size is not perfectly monotonic. Binary search locates the region,
    # then a small local lattice selects by actual complete Ogg bytes.
    for _ in range(12):
        middle = (low + high) * 0.5
        result = evaluate(middle)
        if len(result.payload) < target_bytes:
            low = middle
        else:
            high = middle
    center = (low + high) * 0.5
    span = max(0.5, (high - low) * 4.0)
    for index in range(-8, 9):
        bitrate = min(
            256.0 * channels,
            max(6.0, center + span * index / 8.0),
        )
        evaluate(bitrate)
    return min(
        tried.values(),
        key=lambda result: (
            abs(len(result.payload) - target_bytes),
            len(result.payload),
        ),
    )


def _write_codec_artifacts(
    directory: Path,
    *,
    name: str,
    payload: bytes,
    reconstructed,
    sample_rate: int,
    extension: str,
) -> dict:
    stream_path = directory / f"{name}.{extension}"
    decoded_path = directory / f"{name}-decoded.wav"
    stream_path.write_bytes(payload)
    write_pcm16_channels(decoded_path, sample_rate, reconstructed)
    return {
        "stream_file": stream_path.name,
        "stream_file_sha256": _sha256_file(stream_path),
        "decoded_file": decoded_path.name,
        "decoded_sha256": _sha256_file(decoded_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--opus-tools", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--clip-id", action="append")
    args = parser.parse_args()

    manifest = json.loads(args.prepared_manifest.read_text(encoding="utf-8"))
    if manifest.get("schema") != "resonith-prepared-extended-audio-corpus-1":
        raise ValueError("unsupported prepared R-111 manifest")
    native_core = NativeMain0Decoder(args.native_core)
    opus_tools = resolve_opus_tools(args.opus_tools)
    args.output_directory.mkdir(parents=True, exist_ok=True)

    records = manifest["clips"]
    if args.clip_id:
        selected_ids = set(args.clip_id)
        records = [
            record for record in records if record["id"] in selected_ids
        ]
        if {record["id"] for record in records} != selected_ids:
            raise ValueError("one or more --clip-id values are unknown")

    clips: dict[str, dict] = {}
    total_started = time.perf_counter()
    for record in records:
        source_path = args.prepared_directory / record["output_file"]
        if _sha256_file(source_path) != record["output_sha256"]:
            raise ValueError(f"prepared source hash mismatch: {record['id']}")
        sample_rate, samples = read_pcm16_channels(source_path)
        categories = set(record["categories"])
        speech = "speech" in categories
        budget = 67 if samples.shape[1] == 1 else 71
        mode = "speech" if speech else "music"
        application = "speech" if speech else "music"

        clip_started = time.perf_counter()
        energy_started = time.perf_counter()
        energy = _encode(
            samples,
            sample_rate,
            budget=budget,
            selection_backend="energy",
            native_core=native_core,
        )
        energy_seconds = time.perf_counter() - energy_started
        gain_started = time.perf_counter()
        gain_shape = _encode(
            samples,
            sample_rate,
            budget=budget,
            selection_backend="gain-shape",
            native_core=native_core,
        )
        gain_seconds = time.perf_counter() - gain_started
        opus_started = time.perf_counter()
        opus = _matched_opus(
            samples,
            sample_rate,
            target_bytes=len(gain_shape.payload),
            application=application,
            tools=opus_tools,
        )
        opus_seconds = time.perf_counter() - opus_started

        energy_metrics = _diagnostics(
            samples,
            energy.reconstruction,
            sample_rate,
            mode,
        )
        gain_metrics = _diagnostics(
            samples,
            gain_shape.reconstruction,
            sample_rate,
            mode,
        )
        opus_metrics = _diagnostics(
            samples,
            opus.reconstructed,
            sample_rate,
            mode,
        )
        directory = args.output_directory / record["id"]
        directory.mkdir(parents=True, exist_ok=True)
        source_copy = directory / "source.wav"
        write_pcm16_channels(source_copy, sample_rate, samples)
        energy_files = _write_codec_artifacts(
            directory,
            name="energy",
            payload=energy.payload,
            reconstructed=energy.reconstruction,
            sample_rate=sample_rate,
            extension="resonith",
        )
        gain_files = _write_codec_artifacts(
            directory,
            name="gain-shape",
            payload=gain_shape.payload,
            reconstructed=gain_shape.reconstruction,
            sample_rate=sample_rate,
            extension="resonith",
        )
        opus_files = _write_codec_artifacts(
            directory,
            name="opus",
            payload=opus.payload,
            reconstructed=opus.reconstructed,
            sample_rate=sample_rate,
            extension="opus",
        )

        rate_delta = len(gain_shape.payload) / len(opus.payload) - 1.0
        clips[record["id"]] = {
            "categories": record["categories"],
            "source": {
                "file": source_copy.name,
                "sha256": _sha256_file(source_copy),
                "sample_rate": sample_rate,
                "frames": int(samples.shape[0]),
                "channels": int(samples.shape[1]),
            },
            "configuration": {
                "coefficients_per_frame": budget,
                "half_window": 512,
                "band_count": 24,
            },
            "energy": {
                "bytes": len(energy.payload),
                "encode_wall_seconds": energy_seconds,
                "metrics": energy_metrics,
                **energy_files,
                **energy.report,
            },
            "gain_shape": {
                "bytes": len(gain_shape.payload),
                "encode_wall_seconds": gain_seconds,
                "rate_delta_vs_opus": rate_delta,
                "metrics": gain_metrics,
                **gain_files,
                **gain_shape.report,
            },
            "opus": {
                "bytes": len(opus.payload),
                "encode_search_wall_seconds": opus_seconds,
                "metrics": opus_metrics,
                **opus_files,
                **opus.report,
            },
            "deltas": {
                "gain_shape_bytes_vs_energy": (
                    len(gain_shape.payload) - len(energy.payload)
                ),
                "gain_shape_snr_db_vs_energy": (
                    gain_metrics["waveform"]["snr_db"]
                    - energy_metrics["waveform"]["snr_db"]
                ),
                "gain_shape_log_mel_ratio_vs_energy": (
                    gain_metrics["spectral"]["log_mel_rmse"]
                    / max(
                        energy_metrics["spectral"]["log_mel_rmse"],
                        1e-12,
                    )
                ),
                "gain_shape_snr_db_vs_opus": (
                    gain_metrics["waveform"]["snr_db"]
                    - opus_metrics["waveform"]["snr_db"]
                ),
                "gain_shape_log_mel_ratio_vs_opus": (
                    gain_metrics["spectral"]["log_mel_rmse"]
                    / max(
                        opus_metrics["spectral"]["log_mel_rmse"],
                        1e-12,
                    )
                ),
            },
            "clip_wall_seconds": time.perf_counter() - clip_started,
        }
        print(
            f"{record['id']}: Resonith {len(gain_shape.payload)} B, "
            f"Opus {len(opus.payload)} B, "
            f"SNR delta {clips[record['id']]['deltas']['gain_shape_snr_db_vs_opus']:.3f} dB, "
            f"log-mel ratio {clips[record['id']]['deltas']['gain_shape_log_mel_ratio_vs_opus']:.3f}",
            flush=True,
        )

    report = {
        "schema": "resonith-r111-heterogeneous-gain-shape-gate-1",
        "decision": "R-107/R-111",
        "status": "measured heterogeneous diagnostic; no universal win claimed",
        "selected_clip_ids": [record["id"] for record in records],
        "prepared_manifest_sha256": _sha256_file(args.prepared_manifest),
        "native_core": {
            "file": args.native_core.name,
            "sha256": _sha256_file(args.native_core),
        },
        "opus_tools": {
            "encoder_version": opus_tools.encoder_version,
            "decoder_version": opus_tools.decoder_version,
            "encoder_sha256": opus_tools.encoder_sha256,
            "decoder_sha256": opus_tools.decoder_sha256,
        },
        "total_wall_seconds": time.perf_counter() - total_started,
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
