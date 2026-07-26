"""Compare all-long and all-short lapped windows before mixed syntax."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.opus_anchor import (  # noqa: E402
    resolve_opus_tools,
    run_opus_multichannel_anchor,
)
from maf_p0.perceptual_metrics import (  # noqa: E402
    multiresolution_spectral_error_db,
    transient_pre_echo_error_db,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402


LONG_BUDGETS = {
    "corelli-sonata-realization": (59, 60, 61, 62),
    "emotional-piano-cc0": (64, 65, 66, 67),
    "patro-de-bateria": (45, 46, 47, 48),
}


def _frontier(
    samples,
    sample_rate: int,
    budgets: tuple[int, ...],
    *,
    half_window: int,
    band_count: int,
) -> list:
    return [
        encode_lapped_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            half_window=half_window,
            band_count=band_count,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend="adaptive",
        )
        for budget in budgets
    ]


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
        "--short-budgets",
        type=int,
        nargs="+",
        default=(10, 12, 14, 16, 18, 20),
    )
    parser.add_argument("--opus-bitrate", type=int, default=96)
    parser.add_argument("--opus-tools", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "artifacts"
            / "window_transient_gate"
            / "report.json"
        ),
    )
    args = parser.parse_args()
    tools = resolve_opus_tools(args.opus_tools)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    clips = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + frame_count].copy()
        opus = run_opus_multichannel_anchor(
            samples,
            sample_rate,
            bitrate_kbps=args.opus_bitrate,
            tools=tools,
        )
        long_frontier = _frontier(
            samples,
            sample_rate,
            LONG_BUDGETS[record["id"]],
            half_window=512,
            band_count=24,
        )
        short_frontier = _frontier(
            samples,
            sample_rate,
            tuple(sorted(set(args.short_budgets))),
            half_window=128,
            band_count=12,
        )
        select = lambda frontier: min(  # noqa: E731
            frontier,
            key=lambda item: (
                abs(item.report["stream_bytes"] - opus.report["stream_bytes"]),
                item.report["stream_bytes"],
            ),
        )
        selected_long = select(long_frontier)
        selected_short = select(short_frontier)

        def describe(result) -> dict:
            return {
                "average_coefficients": result.report[
                    "coefficients_per_frame"
                ],
                "stream_bytes": result.report["stream_bytes"],
                "snr_db_diagnostic": result.report["snr_db"],
                "spectral": multiresolution_spectral_error_db(
                    samples,
                    result.reconstruction,
                ),
                "transient": transient_pre_echo_error_db(
                    samples,
                    result.reconstruction,
                    sample_rate,
                ),
            }

        clips[record["id"]] = {
            "provenance": record,
            "conversion": conversion,
            "opus": {
                "stream_bytes": opus.report["stream_bytes"],
                "snr_db_diagnostic": opus.report["snr_db"],
                "spectral": multiresolution_spectral_error_db(
                    samples,
                    opus.reconstructed,
                ),
                "transient": transient_pre_echo_error_db(
                    samples,
                    opus.reconstructed,
                    sample_rate,
                ),
            },
            "long": describe(selected_long),
            "short": describe(selected_short),
        }
    report = {
        "status": "all-short transient oracle complete; listening pending",
        "research_only": True,
        "metric_warning": (
            "spectral and pre-echo metrics are diagnostics, not perceptual "
            "equivalence"
        ),
        "clips": clips,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
