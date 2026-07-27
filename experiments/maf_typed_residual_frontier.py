"""Search the R-136 quality-constrained Truth frontier without new syntax."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from active_band_selection_gate import _diagnostics  # noqa: E402
from maf_typed_truth_fast_gate import _quality_guard  # noqa: E402
from maf_p0.maf_typed_candidate import (  # noqa: E402
    encode_maf_typed_truth_candidate,
)
from maf_p0.native_core import NativeMain0Decoder  # noqa: E402
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--preceding-stream", type=Path, required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--maximum-budget", type=int, required=True)
    parser.add_argument("--budget", type=int, action="append", required=True)
    parser.add_argument("--segment-milliseconds", type=float, default=240.0)
    parser.add_argument("--filter-order", type=int, default=10)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    budgets = sorted(set(args.budget))
    if any(not 1 <= budget <= args.maximum_budget for budget in budgets):
        raise ValueError("frontier budget exceeds its bound")
    sample_rate, samples = read_pcm16_channels(args.source)
    decoder = NativeMain0Decoder(args.native_core)
    preceding_payload = args.preceding_stream.read_bytes()
    preceding_decoded = decoder.decode_lapped_compact_packets(
        preceding_payload
    ).samples
    if preceding_decoded.shape != samples.shape:
        raise ValueError("preceding stream shape mismatch")
    preceding_metrics = _diagnostics(
        samples,
        preceding_decoded,
        sample_rate,
        "music",
    )

    args.output_directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    points: list[dict] = []
    for budget in budgets:
        point_started = time.perf_counter()
        candidate = encode_maf_typed_truth_candidate(
            samples,
            sample_rate,
            native_decoder=decoder,
            coefficients_per_frame=args.maximum_budget,
            segment_milliseconds=args.segment_milliseconds,
            filter_order=args.filter_order,
            half_window=512,
            band_count=24,
            residual_budget_override=budget,
        )
        metrics = _diagnostics(
            samples,
            candidate.reconstruction,
            sample_rate,
            "music",
        )
        guard = _quality_guard(metrics, preceding_metrics)
        stream_path = args.output_directory / f"candidate-b{budget}.resonith"
        decoded_path = args.output_directory / f"candidate-b{budget}-decoded.wav"
        stream_path.write_bytes(candidate.payload)
        write_pcm16_channels(
            decoded_path,
            sample_rate,
            candidate.reconstruction,
        )
        eligible = bool(
            len(candidate.payload) <= len(preceding_payload)
            and guard["passed"]
        )
        points.append(
            {
                "residual_budget": budget,
                "bytes": len(candidate.payload),
                "sha256": _sha256_file(stream_path),
                "stream_file": stream_path.name,
                "decoded_file": decoded_path.name,
                "decoded_sha256": _sha256_file(decoded_path),
                "metrics": metrics,
                "quality_guard": guard,
                "byte_non_regression": (
                    len(candidate.payload) <= len(preceding_payload)
                ),
                "eligible": eligible,
                "predictor": candidate.report["predictor"],
                "wall_seconds": time.perf_counter() - point_started,
            }
        )
        print(
            f"budget {budget}: {len(candidate.payload)} bytes, "
            f"log-mel {metrics['spectral']['log_mel_rmse']:.6f}, "
            f"{'eligible' if eligible else 'rejected'}",
            flush=True,
        )

    eligible_points = [point for point in points if point["eligible"]]
    selected = min(
        eligible_points,
        key=lambda point: (point["bytes"], point["residual_budget"]),
        default=None,
    )
    selected_stream = args.output_directory / "selected.resonith"
    selected_wav = args.output_directory / "selected-decoded.wav"
    if selected is None:
        shutil.copyfile(args.preceding_stream, selected_stream)
        write_pcm16_channels(
            selected_wav,
            sample_rate,
            preceding_decoded,
        )
        selected_record = {
            "backend": "exact preceding Resonith fallback",
            "bytes": len(preceding_payload),
            "sha256": _sha256_file(selected_stream),
        }
    else:
        shutil.copyfile(
            args.output_directory / selected["stream_file"],
            selected_stream,
        )
        shutil.copyfile(
            args.output_directory / selected["decoded_file"],
            selected_wav,
        )
        selected_record = {
            "backend": "R-136 typed MAF quality frontier",
            "residual_budget": selected["residual_budget"],
            "bytes": selected["bytes"],
            "sha256": _sha256_file(selected_stream),
        }
    selected_record["decoded_file"] = selected_wav.name
    selected_record["decoded_sha256"] = _sha256_file(selected_wav)

    report = {
        "schema": "resonith-maf-typed-residual-frontier-1",
        "decision": "R-136",
        "status": (
            "one quality-constrained MAF point admitted"
            if selected is not None
            else "no MAF point admitted; exact preceding fallback retained"
        ),
        "source_revision": args.source_revision,
        "source": {
            "file": args.source.name,
            "bytes": args.source.stat().st_size,
            "sha256": _sha256_file(args.source),
            "sample_rate": sample_rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
        },
        "preceding": {
            "file": args.preceding_stream.name,
            "bytes": len(preceding_payload),
            "sha256": _sha256_file(args.preceding_stream),
            "metrics": preceding_metrics,
        },
        "configuration": {
            "maximum_budget": args.maximum_budget,
            "budgets": budgets,
            "segment_milliseconds": args.segment_milliseconds,
            "filter_order": args.filter_order,
            "half_window": 512,
            "band_count": 24,
        },
        "points": points,
        "selected": selected_record,
        "total_wall_seconds": time.perf_counter() - started,
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
