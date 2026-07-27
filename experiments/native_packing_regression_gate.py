"""Re-encode the R-111 corpus and require exact R-107 stream identity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--prepared-directory", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--reference-directory", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prepared = json.loads(args.prepared_manifest.read_text(encoding="utf-8"))
    prepared_by_id = {
        item["id"]: item for item in prepared["clips"]
    }
    reference = json.loads(args.reference_report.read_text(encoding="utf-8"))
    native_core = NativeMain0Decoder(args.native_core)
    clips = {}
    gate_started = time.perf_counter()
    for clip_id, evidence in reference["clips"].items():
        item = prepared_by_id[clip_id]
        source_path = args.prepared_directory / item["output_file"]
        reference_path = (
            args.reference_directory
            / clip_id
            / "gain-shape.resonith"
        )
        sample_rate, samples = read_pcm16_channels(source_path)
        packet_frames = max(
            512,
            round(sample_rate * 0.256 / 512) * 512,
        )
        started = time.perf_counter()
        encoded = encode_lapped_finite_packet_stream(
            samples,
            sample_rate,
            coefficients_per_frame=int(
                evidence["gain_shape"]["coefficients_per_frame"]
            ),
            packet_frames=packet_frames,
            half_window=512,
            band_count=24,
            selection_backend="gain-shape",
            native_core=native_core,
        )
        wall_seconds = time.perf_counter() - started
        reference_payload = reference_path.read_bytes()
        identical = encoded.payload == reference_payload
        clips[clip_id] = {
            "budget": int(
                evidence["gain_shape"]["coefficients_per_frame"]
            ),
            "duration_seconds": samples.shape[0] / sample_rate,
            "optimized_encode_wall_seconds": wall_seconds,
            "audio_seconds_per_wall_second": (
                samples.shape[0] / sample_rate / wall_seconds
            ),
            "bytes": len(encoded.payload),
            "sha256": _sha256(encoded.payload),
            "reference_bytes": len(reference_payload),
            "reference_sha256": _sha256(reference_payload),
            "byte_identical": identical,
        }
        print(
            f"{clip_id}: {wall_seconds:.3f}s, "
            f"{len(encoded.payload)} bytes, identical={identical}",
            flush=True,
        )
    all_passed = all(item["byte_identical"] for item in clips.values())
    report = {
        "schema": "resonith-native-packing-regression-gate-1",
        "decision": "R-112",
        "clip_count": len(clips),
        "all_byte_identical": all_passed,
        "total_wall_seconds": time.perf_counter() - gate_started,
        "native_core": {
            "file": args.native_core.name,
            "sha256": _sha256(args.native_core.read_bytes()),
        },
        "clips": clips,
        "status": (
            "passed: every R-111 stream is byte-identical"
            if all_passed
            else "failed: one or more streams differ"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
