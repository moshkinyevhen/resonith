"""Prepare hashed real-music LPS4 inputs for physical-device measurements."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    decode_lapped_packet_stream,
    encode_lapped_compact_packet_stream,
)
from packet_loss_benchmark import (  # noqa: E402
    pcm_sha256,
    read_bounded_pcm16,
)
from real_music_benchmark import fetch_source  # noqa: E402


RATE_MATCHED_AVERAGE_BUDGETS = {
    "corelli-sonata-realization": 54,
    "emotional-piano-cc0": 68,
    "patro-de-bateria": 44,
}


def sha256(payload: bytes) -> str:
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
    parser.add_argument("--packet-seconds", type=float, default=0.04)
    parser.add_argument("--half-window", type=int, default=512)
    parser.add_argument("--band-count", type=int, default=24)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "lapped_device_streams",
    )
    args = parser.parse_args()
    if (
        args.maximum_seconds <= 0.0
        or args.packet_seconds <= 0.0
        or args.half_window <= 0
        or args.band_count <= 0
    ):
        raise ValueError("invalid device-stream configuration")

    source_manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    streams = {}
    for record in source_manifest["sources"]:
        source_path = fetch_source(record, args.cache)
        sample_rate, full_samples, conversion = read_bounded_pcm16(source_path)
        start = int(round(float(record["start_seconds"]) * sample_rate))
        frame_count = min(
            int(round(float(record["duration_seconds"]) * sample_rate)),
            int(round(args.maximum_seconds * sample_rate)),
        )
        samples = full_samples[start : start + frame_count].copy()
        packet_frames = max(
            args.half_window,
            int(args.packet_seconds * sample_rate)
            // args.half_window
            * args.half_window,
        )
        budget = RATE_MATCHED_AVERAGE_BUDGETS[record["id"]]
        encoded = encode_lapped_compact_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=budget,
            packet_frames=packet_frames,
            half_window=args.half_window,
            band_count=args.band_count,
        )
        decoded = decode_lapped_packet_stream(encoded.payload)
        path = args.output_directory / f"{record['id']}.lps"
        path.write_bytes(encoded.payload)
        streams[record["id"]] = {
            "path": path.name,
            "stream_sha256": sha256(encoded.payload),
            "stream_bytes": len(encoded.payload),
            "source_pcm16_sha256": pcm_sha256(samples),
            "decoded_pcm16_sha256": pcm_sha256(decoded.samples),
            "sample_rate": sample_rate,
            "frame_count": int(samples.shape[0]),
            "channel_count": int(samples.shape[1]),
            "average_coefficients": budget,
            "half_window": args.half_window,
            "band_count": args.band_count,
            "packet_frames": decoded.packet_frames,
            "packet_count": decoded.packet_count,
            "conversion": conversion,
            "provenance": record,
        }

    report = {
        "schema": "resonith-lapped-device-stream-set-1",
        "codec": "LPS4 fixed-integer bounded adaptive-density",
        "maximum_seconds": args.maximum_seconds,
        "packet_seconds_request": args.packet_seconds,
        "streams": streams,
    }
    (args.output_directory / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
