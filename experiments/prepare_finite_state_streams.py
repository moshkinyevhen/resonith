"""Prepare reproducible R-095 LAF1 inputs for native device timing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from finite_state_oracle_benchmark import _flatten_selected  # noqa: E402
from maf_p0.finite_state_oracle import encode_finite_state_lapped  # noqa: E402
from maf_p0.lapped_oracle import (  # noqa: E402
    analyze_lapped_source,
    encode_lapped_analysis,
)
from packet_loss_benchmark import read_bounded_pcm16  # noqa: E402
from real_music_benchmark import fetch_source  # noqa: E402
from temporal_support_oracle_benchmark import R084_BUDGETS  # noqa: E402


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
    parser.add_argument("--maximum-seconds", type=float, default=3.0)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "finite_state_streams",
    )
    args = parser.parse_args()
    if args.maximum_seconds <= 0.0:
        raise ValueError("--maximum-seconds must be positive")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)

    streams: dict[str, dict] = {}
    for record in manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        crop_start = int(round(float(record["start_seconds"]) * sample_rate))
        sample_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[crop_start : crop_start + sample_count].copy()
        analysis = analyze_lapped_source(
            samples,
            sample_rate,
            half_window=512,
            band_count=24,
            transform_backend="fixed",
        )
        selected = encode_lapped_analysis(
            analysis,
            coefficients_per_frame=R084_BUDGETS[record["id"]],
            entropy_backend="bounded",
            density_backend="adaptive",
        )
        counts, positions, values = _flatten_selected(
            selected.selected_coefficients
        )
        payload = encode_finite_state_lapped(
            selected.selected_scales,
            counts,
            positions,
            values,
            half_window=512,
        )
        filename = f"{record['id']}.laf"
        (args.output_directory / filename).write_bytes(payload)
        streams[record["id"]] = {
            "filename": filename,
            "sha256": _sha256(payload),
            "bytes": len(payload),
            "sample_rate": sample_rate,
            "sample_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "transform_frame_count": analysis.frame_count,
            "half_window": 512,
            "band_count": 24,
            "r084_coefficients_per_frame": R084_BUDGETS[record["id"]],
            "conversion": conversion,
        }
    output_manifest = {
        "schema": "resonith-laf1-device-inputs-1",
        "research_only": True,
        "maximum_seconds_per_clip": args.maximum_seconds,
        "streams": streams,
    }
    (args.output_directory / "manifest.json").write_text(
        json.dumps(output_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(output_manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
