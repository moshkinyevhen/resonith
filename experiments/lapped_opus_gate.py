"""Run the R-057 lapped Innovation nearest-byte Opus sanity gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
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
        "--coefficient-budgets",
        type=int,
        nargs="+",
        default=(16, 24, 32, 48, 64, 96),
    )
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--entropy-backend",
        choices=("bounded", "zlib"),
        default="bounded",
    )
    parser.add_argument(
        "--transform-backend",
        choices=("fixed", "float"),
        default="fixed",
    )
    parser.add_argument("--opus-bitrate", type=int, default=96)
    parser.add_argument("--opus-tools", type=Path)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "lapped_opus_gate",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    tools = resolve_opus_tools(args.opus_tools)

    clip_reports: dict[str, dict] = {}
    listening_inputs: dict[str, dict[str, Path]] = {}
    snr_deltas: list[float] = []
    winning_clips = 0
    table_hashes: set[str] = set()
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

        opus_started = time.perf_counter()
        opus = run_opus_multichannel_anchor(
            samples,
            sample_rate,
            bitrate_kbps=args.opus_bitrate,
            tools=tools,
        )
        opus_seconds = time.perf_counter() - opus_started
        candidates = []
        for budget in sorted(set(args.coefficient_budgets)):
            started = time.perf_counter()
            encoded = encode_lapped_stream(
                samples,
                sample_rate,
                coefficients_per_frame=budget,
                half_window=args.half_window,
                band_count=args.band_count,
                entropy_backend=args.entropy_backend,
                transform_backend=args.transform_backend,
            )
            candidates.append(
                (
                    budget,
                    encoded,
                    time.perf_counter() - started,
                )
            )
            table_hash = encoded.report["fixed_table_sha256"]
            if table_hash is not None:
                table_hashes.add(table_hash)
        selected = min(
            candidates,
            key=lambda item: (
                abs(
                    item[1].report["stream_bytes"]
                    - opus.report["stream_bytes"]
                ),
                item[1].report["stream_bytes"],
            ),
        )
        byte_ratio = (
            selected[1].report["stream_bytes"]
            / opus.report["stream_bytes"]
        )
        snr_delta = (
            selected[1].report["snr_db"] - opus.report["snr_db"]
        )
        sane_rate_match = 0.90 <= byte_ratio <= 1.10
        objective_win = sane_rate_match and snr_delta >= 0.0
        winning_clips += int(objective_win)
        snr_deltas.append(snr_delta)

        lapped_path = clip_directory / "lapped-rate-matched.wav"
        opus_path = clip_directory / "opus-anchor.wav"
        write_pcm16_channels(
            lapped_path,
            sample_rate,
            selected[1].reconstruction,
        )
        write_pcm16_channels(
            opus_path,
            sample_rate,
            opus.reconstructed,
        )
        (clip_directory / "lapped-rate-matched.rsc").write_bytes(
            selected[1].payload
        )
        (clip_directory / "opus-anchor.opus").write_bytes(opus.payload)
        listening_inputs[record["id"]] = {
            "source": source_wav,
            (
                f"lapped-k{selected[0]}-"
                f"{selected[1].report['stream_bytes']}B"
            ): lapped_path,
            (
                f"opus-{args.opus_bitrate}k-"
                f"{opus.report['stream_bytes']}B"
            ): opus_path,
        }
        clip_reports[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "pcm16_sha256": pcm_sha256(samples),
            "selected_budget": selected[0],
            "selected_stream_bytes": selected[1].report["stream_bytes"],
            "selected_effective_bitrate_kbps": (
                8.0
                * selected[1].report["stream_bytes"]
                / duration_seconds
                / 1000.0
            ),
            "selected_snr_db_diagnostic": selected[1].report["snr_db"],
            "selected_max_abs_error": (
                selected[1].report["max_abs_error"]
            ),
            "selected_encode_wall_seconds": selected[2],
            "opus_stream_bytes": opus.report["stream_bytes"],
            "opus_effective_bitrate_kbps": (
                opus.report["effective_bitrate_kbps"]
            ),
            "opus_snr_db_diagnostic": opus.report["snr_db"],
            "opus_max_abs_error": opus.report["max_abs_error"],
            "opus_encode_decode_wall_seconds": opus_seconds,
            "byte_ratio_vs_opus": byte_ratio,
            "snr_delta_db_diagnostic": snr_delta,
            "objective_sanity_win": objective_win,
            "frontier": [
                {
                    "coefficients_per_frame": budget,
                    "stream_bytes": result.report["stream_bytes"],
                    "effective_bitrate_kbps": (
                        8.0
                        * result.report["stream_bytes"]
                        / duration_seconds
                        / 1000.0
                    ),
                    "snr_db_diagnostic": result.report["snr_db"],
                    "max_abs_error": result.report["max_abs_error"],
                    "compressed_grid_bytes": (
                        result.report["compressed_grid_bytes"]
                    ),
                    "entropy_backend": result.report["entropy_backend"],
                    "transform_backend": result.report["transform_backend"],
                    "fixed_table_sha256": (
                        result.report["fixed_table_sha256"]
                    ),
                    "encode_wall_seconds": wall_seconds,
                }
                for budget, result, wall_seconds in candidates
            ],
        }

    mean_snr_delta = sum(snr_deltas) / len(snr_deltas)
    sanity_gate_passed = winning_clips >= 2 and mean_snr_delta >= 0.0
    promotion_blockers = [
        "blinded listening scores",
        "native independent decoder parity",
        "native resource and timing gates",
    ]
    if args.entropy_backend != "bounded":
        promotion_blockers.insert(1, "bounded context entropy replacing zlib")
    if args.transform_backend != "fixed":
        promotion_blockers.insert(1, "fixed-integer transform parity")
    listening_directory = args.output_directory / "listening"
    listening_manifest, _answer_key = create_blinded_listening_set(
        listening_inputs,
        listening_directory,
        seed="resonith-r057-lapped-opus-2026-07-26",
    )
    report = {
        "status": (
            "objective sanity gate passed; native/listening gates remain"
            if sanity_gate_passed
            else "objective sanity gate failed; lapped design remains research"
        ),
        "research_only": True,
        "entropy_backend": args.entropy_backend,
        "transform_backend": args.transform_backend,
        "fixed_table_sha256": (
            next(iter(table_hashes)) if len(table_hashes) == 1 else None
        ),
        "promotion_blockers": promotion_blockers,
        "gate_rule": (
            "nearest-byte point within 10% of Opus, non-negative waveform "
            "SNR delta on at least two clips, and non-negative mean delta"
        ),
        "sanity_gate_passed": sanity_gate_passed,
        "winning_clips": winning_clips,
        "mean_snr_delta_db_diagnostic": mean_snr_delta,
        "maximum_seconds_per_clip": args.maximum_seconds,
        "half_window": args.half_window,
        "band_count": args.band_count,
        "coefficient_budgets": sorted(set(args.coefficient_budgets)),
        "opus_requested_bitrate_kbps": args.opus_bitrate,
        "opus_tools": {
            "encoder_version": tools.encoder_version,
            "decoder_version": tools.decoder_version,
            "encoder_sha256": tools.encoder_sha256,
            "decoder_sha256": tools.decoder_sha256,
        },
        "listening_manifest_schema": listening_manifest["schema"],
        "clips": clip_reports,
    }
    (args.output_directory / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
