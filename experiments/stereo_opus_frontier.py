"""Build the R-056 stereo Resonith/Opus frontier and blind trials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.multichannel import encode_main0_independent_rdo  # noqa: E402
from maf_p0.opus_anchor import (  # noqa: E402
    resolve_opus_tools,
    run_opus_multichannel_anchor,
)
from maf_p0.wav_io import write_pcm16_channels  # noqa: E402
from listening_set import create_blinded_listening_set  # noqa: E402
from packet_loss_benchmark import (  # noqa: E402
    pcm_sha256,
    read_bounded_pcm16,
)
from real_music_benchmark import fetch_source  # noqa: E402


def _point(report: dict, *, control_name: str, control_value: int) -> dict:
    return {
        control_name: control_value,
        "stream_bytes": report["stream_bytes"],
        "effective_bitrate_kbps": report["effective_bitrate_kbps"],
        "snr_db_diagnostic": report["snr_db"],
        "max_abs_error": report["max_abs_error"],
        "stream_sha256": report["stream_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "real_music_corpus.json",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "real_music_source",
    )
    parser.add_argument("--maximum-seconds", type=float, default=1.0)
    parser.add_argument(
        "--resonith-q-steps",
        type=int,
        nargs="+",
        default=(32, 64, 128, 256, 512, 1024),
    )
    parser.add_argument(
        "--opus-bitrates",
        type=int,
        nargs="+",
        default=(48, 64, 96, 128, 192),
    )
    parser.add_argument("--residual-block-size", type=int, default=4096)
    parser.add_argument("--listening-opus-bitrate", type=int, default=96)
    parser.add_argument("--opus-tools", type=Path)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "stereo_opus_frontier",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    tools = resolve_opus_tools(args.opus_tools)

    clips: dict[str, dict] = {}
    listening_inputs: dict[str, dict[str, Path]] = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + frame_count].copy()
        duration_seconds = samples.shape[0] / sample_rate
        clip_directory = args.output_directory / "decoded" / record["id"]
        clip_directory.mkdir(parents=True, exist_ok=True)
        source_wav = clip_directory / "source.wav"
        write_pcm16_channels(source_wav, sample_rate, samples)

        resonith_results = []
        for step in sorted(set(args.resonith_q_steps)):
            started = time.perf_counter()
            encoded = encode_main0_independent_rdo(
                samples,
                sample_rate,
                innovation_step=step,
                residual_block_sizes=(args.residual_block_size,),
            )
            report = {
                **encoded.report,
                "effective_bitrate_kbps": (
                    8.0 * len(encoded.payload) / duration_seconds / 1000.0
                ),
                "encode_wall_seconds": time.perf_counter() - started,
            }
            resonith_results.append((step, encoded, report))

        opus_results = []
        for bitrate in sorted(set(args.opus_bitrates)):
            started = time.perf_counter()
            encoded = run_opus_multichannel_anchor(
                samples,
                sample_rate,
                bitrate_kbps=bitrate,
                tools=tools,
            )
            report = {
                **encoded.report,
                "encode_decode_wall_seconds": (
                    time.perf_counter() - started
                ),
            }
            opus_results.append((bitrate, encoded, report))

        requested_opus = min(
            opus_results,
            key=lambda item: (
                abs(item[0] - args.listening_opus_bitrate),
                item[0],
            ),
        )
        nearest_resonith = min(
            resonith_results,
            key=lambda item: (
                abs(
                    item[2]["stream_bytes"]
                    - requested_opus[2]["stream_bytes"]
                ),
                item[2]["stream_bytes"],
            ),
        )
        resonith_stream = clip_directory / "resonith-rate-matched.rsc"
        resonith_wav = clip_directory / "resonith-rate-matched.wav"
        opus_stream = clip_directory / "opus-anchor.opus"
        opus_wav = clip_directory / "opus-anchor.wav"
        resonith_stream.write_bytes(nearest_resonith[1].payload)
        write_pcm16_channels(
            resonith_wav,
            sample_rate,
            nearest_resonith[1].reconstruction,
        )
        opus_stream.write_bytes(requested_opus[1].payload)
        write_pcm16_channels(
            opus_wav,
            sample_rate,
            requested_opus[1].reconstructed,
        )
        listening_inputs[record["id"]] = {
            "source": source_wav,
            (
                "resonith-q"
                f"{nearest_resonith[0]}-"
                f"{nearest_resonith[2]['stream_bytes']}B"
            ): resonith_wav,
            (
                "opus-"
                f"{requested_opus[0]}k-"
                f"{requested_opus[2]['stream_bytes']}B"
            ): opus_wav,
        }

        clips[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "pcm16_sha256": pcm_sha256(samples),
            "resonith_frontier": [
                _point(
                    report,
                    control_name="innovation_step",
                    control_value=step,
                )
                | {"encode_wall_seconds": report["encode_wall_seconds"]}
                for step, _encoded, report in resonith_results
            ],
            "opus_frontier": [
                _point(
                    report,
                    control_name="requested_bitrate_kbps",
                    control_value=bitrate,
                )
                | {
                    "encode_decode_wall_seconds": (
                        report["encode_decode_wall_seconds"]
                    )
                }
                for bitrate, _encoded, report in opus_results
            ],
            "blind_rate_pair": {
                "resonith_innovation_step": nearest_resonith[0],
                "resonith_stream_bytes": nearest_resonith[2]["stream_bytes"],
                "opus_requested_bitrate_kbps": requested_opus[0],
                "opus_stream_bytes": requested_opus[2]["stream_bytes"],
                "byte_difference": (
                    nearest_resonith[2]["stream_bytes"]
                    - requested_opus[2]["stream_bytes"]
                ),
                "conclusion": "pending blinded listening scores",
            },
        }

    listening_directory = args.output_directory / "listening"
    manifest_out, _answer_key = create_blinded_listening_set(
        listening_inputs,
        listening_directory,
        seed="resonith-r056-stereo-opus-2026-07-26",
    )
    report = {
        "status": "diagnostic frontier complete; listening conclusions pending",
        "research_only": True,
        "waveform_metrics_are_not_perceptual_equivalence": True,
        "maximum_seconds_per_clip": args.maximum_seconds,
        "residual_block_size": args.residual_block_size,
        "resonith_q_steps": sorted(set(args.resonith_q_steps)),
        "opus_bitrates": sorted(set(args.opus_bitrates)),
        "opus_tools": {
            "encoder_version": tools.encoder_version,
            "decoder_version": tools.decoder_version,
            "encoder_sha256": tools.encoder_sha256,
            "decoder_sha256": tools.decoder_sha256,
        },
        "listening_manifest_schema": manifest_out["schema"],
        "clips": clips,
    }
    (args.output_directory / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
