"""Measure byte-identical R-107 native packing throughput."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_finite_packet_stream,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
from maf_p0.wav_io import read_pcm16_channels  # noqa: E402


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--reference-stream", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--baseline-seconds", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sample_rate, samples = read_pcm16_channels(args.source)
    reference_payload = args.reference_stream.read_bytes()
    native_core = NativeMain0Decoder(args.native_core)
    packet_frames = max(
        512,
        round(sample_rate * 0.256 / 512) * 512,
    )
    started = time.perf_counter()
    result = encode_lapped_finite_packet_stream(
        samples,
        sample_rate,
        coefficients_per_frame=args.budget,
        packet_frames=packet_frames,
        half_window=512,
        band_count=24,
        selection_backend="gain-shape",
        native_core=native_core,
    )
    wall_seconds = time.perf_counter() - started
    duration_seconds = samples.shape[0] / sample_rate
    byte_identical = result.payload == reference_payload
    report = {
        "schema": "resonith-native-packing-benchmark-1",
        "decision": "R-112",
        "source": {
            "file": args.source.name,
            "sha256": _sha256_file(args.source),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
            "duration_seconds": duration_seconds,
        },
        "reference_stream": {
            "file": args.reference_stream.name,
            "bytes": len(reference_payload),
            "sha256": _sha256(reference_payload),
            "published_encode_wall_seconds": args.baseline_seconds,
        },
        "optimized": {
            "bytes": len(result.payload),
            "sha256": _sha256(result.payload),
            "encode_wall_seconds": wall_seconds,
            "audio_seconds_per_wall_second": duration_seconds / wall_seconds,
            "speedup_vs_published": args.baseline_seconds / wall_seconds,
            "byte_identical": byte_identical,
            "monolithic_conformance_checked_in_hot_path": result.report[
                "monolithic_conformance_checked"
            ],
        },
        "native_core": {
            "file": args.native_core.name,
            "sha256": _sha256_file(args.native_core),
        },
        "host": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "status": (
            "passed: optimized stream is byte-identical"
            if byte_identical
            else "failed: optimized stream differs"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not byte_identical:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
