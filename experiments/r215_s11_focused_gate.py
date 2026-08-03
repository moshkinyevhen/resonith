"""Run the minimal executable R-215 S11 claim ledger.

This is a focused implementation gate, not the R-198 music comparison.  S12
owns the complete registered long-first corpus and maximum-effort Opus anchor.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import wave

import numpy as np

from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.partial_graph_fixed import NativePartialGraph
from reference.maf_p0.persistent_partial_field import (
    encode_persistent_partial_truth_candidate,
)


SAMPLE_RATE = 8000
REPOSITORY = Path(__file__).resolve().parents[1]


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(samples, dtype="<i2").tobytes()).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_wav(path: Path, samples: np.ndarray) -> None:
    source = np.ascontiguousarray(samples, dtype="<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(source.shape[1])
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(source.tobytes())


def _process_peak_working_set_bytes() -> int:
    """Read process peak memory without instrumenting encoder allocations."""

    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_uint32),
                ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        get_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype = ctypes.c_void_p
        get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ProcessMemoryCounters),
            ctypes.c_uint32,
        )
        get_memory.restype = ctypes.c_int
        process = get_process()
        if not get_memory(
            process, ctypes.byref(counters), counters.cb
        ):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _signals() -> dict[str, np.ndarray]:
    stable_count = 3968
    stable_time = np.arange(stable_count, dtype=np.float64) / SAMPLE_RATE
    stable = np.rint(
        8000.0 * np.cos(2.0 * np.pi * 440.3 * stable_time)
    ).astype(np.int16)[:, None]

    count = SAMPLE_RATE
    index = np.arange(count, dtype=np.float64)
    seconds = index / SAMPLE_RATE
    edge = np.maximum(
        0.0,
        np.minimum(1.0, np.minimum(index / 256.0, (count - 1 - index) / 256.0)),
    )
    upward_phase = 2.0 * np.pi * (320.0 * seconds + 220.0 * seconds**2)
    downward_phase = 2.0 * np.pi * (760.0 * seconds - 220.0 * seconds**2)
    crossing = np.rint(
        edge
        * (
            3800.0 * np.cos(upward_phase)
            + 3600.0 * np.cos(downward_phase + 0.7)
        )
    ).astype(np.int16)[:, None]

    first = np.zeros(count)
    second = np.zeros(count)
    first[512:6500] = 1.0
    second[2800:7600] = 1.0
    birth_death = np.rint(
        5000.0 * first * np.cos(2.0 * np.pi * 440.3 * seconds + 0.2)
        + 4200.0 * second * np.cos(2.0 * np.pi * 659.7 * seconds + 0.8)
    ).astype(np.int16)[:, None]

    gap = np.zeros(count)
    gap[512:3000] = 1.0
    gap[4800:7600] = 1.0
    reappearance = np.rint(
        7000.0 * gap * np.cos(2.0 * np.pi * 440.3 * seconds + 0.4)
    ).astype(np.int16)[:, None]

    generator = np.random.default_rng(0x215)
    noise = np.rint(generator.normal(0.0, 2500.0, count)).clip(
        -32768, 32767
    ).astype(np.int16)[:, None]
    transient = np.zeros((count, 1), dtype=np.int16)
    transient[[511, 2048, 4097, 7000], 0] = [24000, -28000, 20000, -16000]

    mono = np.rint(
        6000.0 * np.cos(2.0 * np.pi * 523.7 * seconds + 0.35)
    ).astype(np.int16)
    delayed = np.zeros_like(mono)
    delayed[7:] = -mono[:-7]
    stereo = np.column_stack((mono, delayed))
    return {
        "stable-tone": stable,
        "crossing": crossing,
        "birth-death": birth_death,
        "gap-reappearance": reappearance,
        "noise": noise,
        "transient": transient,
        "delayed-antiphase-stereo": stereo,
    }


def _metric_identity(report: dict) -> str:
    stable = dict(report)
    stable.pop("elapsed_seconds", None)
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _encode_case(
    name: str,
    samples: np.ndarray,
    core_path: str,
    output: Path,
) -> tuple[dict, object]:
    decoder = NativeMain0Decoder(core_path)
    graph = NativePartialGraph(core_path)
    started = time.perf_counter()
    candidate = encode_persistent_partial_truth_candidate(
        samples,
        SAMPLE_RATE,
        native_graph=graph,
        native_decoder=decoder,
        coefficients_per_frame=128,
        half_window=128,
        band_count=8,
    )
    wall_seconds = time.perf_counter() - started
    peak_bytes = _process_peak_working_set_bytes()
    evaluated = candidate.report["evaluated_subsets"]
    pareto = [
        row
        for row in evaluated
        if row["sse"] <= candidate.report["truth_fallback_sse"]
        and (
            row["complete_bytes"] < len(candidate.baseline_payload)
            or row["sse"] < candidate.report["truth_fallback_sse"]
        )
    ]
    best = min(
        evaluated,
        key=lambda row: (row["complete_bytes"], row["sse"], row["lane_keys"]),
        default=None,
    )
    retained_keys = {
        tuple(key) for key in candidate.report["retained_lane_keys"]
    }
    active_lane_evidence = [
        lane
        for lane in candidate.report["lane_proposals"]
        if (lane["path_id"], lane["channel"]) in retained_keys
    ]
    active_lane_evidence_sha256 = hashlib.sha256(
        json.dumps(
            active_lane_evidence, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    predictor_transport_identity = all(
        row["predictor_transport_pcm_identity"] for row in evaluated
    )
    complete_decode_identity = all(
        row["complete_decode_identity"] for row in evaluated
    )
    s11_record_language_only = all(
        row["s11_record_language_only"] for row in evaluated
    )
    encoded_path = output / f"{name}.resonith"
    source_path = output / f"{name}-source.wav"
    decoded_path = output / f"{name}-selected-decoded.wav"
    encoded_path.write_bytes(candidate.selected_payload)
    _write_wav(source_path, samples)
    _write_wav(decoded_path, candidate.selected_reconstruction)
    return ({
        "source_frames": int(samples.shape[0]),
        "channels": int(samples.shape[1]),
        "source_pcm16le_sha256": _pcm_sha256(samples),
        "baseline_bytes": len(candidate.baseline_payload),
        "baseline_sse": candidate.report["truth_fallback_sse"],
        "selected_kind": candidate.selected_kind,
        "selected_bytes": len(candidate.selected_payload),
        "selected_sha256": hashlib.sha256(candidate.selected_payload).hexdigest(),
        "selected_pcm16le_sha256": _pcm_sha256(candidate.selected_reconstruction),
        "lane_proposals": candidate.report["lane_proposals"],
        "retained_lane_keys": candidate.report["retained_lane_keys"],
        "active_lane_evidence": active_lane_evidence,
        "active_lane_evidence_sha256": active_lane_evidence_sha256,
        "predictor_transport_pcm_identity": predictor_transport_identity,
        "complete_decode_identity": complete_decode_identity,
        "s11_record_language_only": s11_record_language_only,
        "evaluated_subset_count": len(evaluated),
        "best_evaluated": best,
        "pareto_count": len(pareto),
        "wall_seconds": wall_seconds,
        "process_peak_working_set_bytes": peak_bytes,
        "report_metric_identity": _metric_identity(candidate.report),
        "artifacts": {
            "encoded": str(encoded_path),
            "source_wav": str(source_path),
            "selected_decoded_wav": str(decoded_path),
        },
    }, candidate)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-core", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-receipt", type=Path, required=True)
    parser.add_argument("--prior-receipt-sha256", required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)
    prior_receipt_sha256 = _file_sha256(arguments.prior_receipt)
    if prior_receipt_sha256 != arguments.prior_receipt_sha256.lower():
        raise ValueError("prior focused receipt identity mismatch")
    prior_report = json.loads(arguments.prior_receipt.read_text(encoding="utf-8"))

    results = {}
    for name, samples in _signals().items():
        results[name], _candidate = _encode_case(
            name, samples, arguments.native_core, arguments.output
        )
    repeated, _repeated_candidate = _encode_case(
        "delayed-antiphase-stereo-repeat",
        _signals()["delayed-antiphase-stereo"],
        arguments.native_core,
        arguments.output,
    )
    stable = results["stable-tone"]
    active = results["delayed-antiphase-stereo"]
    repeated_identity = (
        active["selected_kind"] != "truth-fallback"
        and active["selected_sha256"] == repeated["selected_sha256"]
        and active["selected_pcm16le_sha256"]
        == repeated["selected_pcm16le_sha256"]
        and active["active_lane_evidence_sha256"]
        == repeated["active_lane_evidence_sha256"]
        and active["report_metric_identity"] == repeated["report_metric_identity"]
    )
    structure_passes = sum(
        results[name]["pareto_count"] > 0
        for name in ("crossing", "birth-death", "gap-reappearance")
    )
    stable_lanes = stable["lane_proposals"]
    stable_fit = bool(stable_lanes) and any(
        "decoder-coordinate-phase-fit" in lane["span_fit_kinds"]
        and len(lane["knot_native_observation_ids"]) == 2
        for lane in stable_lanes
    )
    explicit_fallbacks = all(
        results[name]["selected_kind"] == "truth-fallback"
        for name in ("noise", "transient")
    )
    cbf1_mft1_identity = all(
        result["predictor_transport_pcm_identity"] for result in results.values()
    ) and repeated["predictor_transport_pcm_identity"]
    complete_decode_identity = all(
        result["complete_decode_identity"] for result in results.values()
    ) and repeated["complete_decode_identity"]
    s11_record_language_only = all(
        result["s11_record_language_only"] for result in results.values()
    ) and repeated["s11_record_language_only"]
    phase_anchor_or_reset_records = 0 if s11_record_language_only else None
    executed_subset_count = sum(
        result["evaluated_subset_count"] for result in results.values()
    ) + repeated["evaluated_subset_count"]
    tail_fusion_comparison = {}
    prior_input_identity = True
    for name in ("stable-tone", "delayed-antiphase-stereo"):
        before = prior_report["results"][name]
        after = results[name]
        prior_input_identity = prior_input_identity and (
            before["source_pcm16le_sha256"] == after["source_pcm16le_sha256"]
            and before["baseline_bytes"] == after["baseline_bytes"]
            and before["baseline_sse"] == after["baseline_sse"]
        )
        tail_fusion_comparison[name] = {
            "input_and_direct_truth_identity": (
                before["source_pcm16le_sha256"] == after["source_pcm16le_sha256"]
                and before["baseline_bytes"] == after["baseline_bytes"]
                and before["baseline_sse"] == after["baseline_sse"]
            ),
            "before": {
                "placement_counts": [
                    lane["placement_count"] for lane in before["lane_proposals"]
                ],
                "predictor_bytes": before["best_evaluated"]["predictor_bytes"],
                "truth_bytes": before["best_evaluated"]["residual_bytes"],
                "complete_bytes": before["best_evaluated"]["complete_bytes"],
                "sse": before["best_evaluated"]["sse"],
            },
            "after": {
                "placement_counts": [
                    lane["placement_count"] for lane in after["lane_proposals"]
                ],
                "placement_counts_before_tail_fusion": [
                    lane["placement_count_before_tail_fusion"]
                    for lane in after["lane_proposals"]
                ],
                "tail_boundary_phase_identity": [
                    lane["tail_boundary_phase_identity"]
                    for lane in after["lane_proposals"]
                ],
                "predictor_bytes": after["best_evaluated"]["predictor_bytes"],
                "truth_bytes": after["best_evaluated"]["residual_bytes"],
                "complete_bytes": after["best_evaluated"]["complete_bytes"],
                "sse": after["best_evaluated"]["sse"],
            },
        }
    passed = (
        stable_fit
        and structure_passes >= 2
        and explicit_fallbacks
        and repeated_identity
        and cbf1_mft1_identity
        and complete_decode_identity
        and phase_anchor_or_reset_records == 0
        and executed_subset_count > 0
        and prior_input_identity
    )
    script_path = Path(__file__).resolve()
    predictor_path = REPOSITORY / "reference" / "maf_p0" / "persistent_partial_field.py"
    test_path = REPOSITORY / "tests" / "test_persistent_partial_field.py"
    report = {
        "schema": "resonith-r215-s11-focused-gate-2",
        "status": "PASS" if passed else "FAIL",
        "scope": "focused S11 implementation gate; not R-198 or Opus evidence",
        "sample_rate": SAMPLE_RATE,
        "native_core": str(Path(arguments.native_core).resolve()),
        "native_core_sha256": hashlib.sha256(
            Path(arguments.native_core).read_bytes()
        ).hexdigest(),
        "exact_command": [
            str(Path(sys.executable).resolve()),
            str(script_path),
            "--native-core",
            str(Path(arguments.native_core).resolve()),
            "--output",
            str(arguments.output.resolve()),
            "--prior-receipt",
            str(arguments.prior_receipt.resolve()),
            "--prior-receipt-sha256",
            arguments.prior_receipt_sha256.lower(),
        ],
        "working_directory": str(Path.cwd().resolve()),
        "replay_environment": {
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        },
        "generator_sha256": _file_sha256(script_path),
        "predictor_sha256": _file_sha256(predictor_path),
        "focused_test_sha256": _file_sha256(test_path),
        "results": results,
        "model_active_repeat": repeated,
        "tail_fusion_comparison": {
            "prior_receipt": str(arguments.prior_receipt.resolve()),
            "prior_receipt_sha256": prior_receipt_sha256,
            "cases": tail_fusion_comparison,
        },
        "gates": {
            "stable_decoder_coordinate_fit": stable_fit,
            "structure_pareto_passes": structure_passes,
            "structure_required": 2,
            "noise_transient_explicit_fallback": explicit_fallbacks,
            "model_active_bytes_pcm_lane_and_metric_identity": repeated_identity,
            "cbf1_mft1_identity": cbf1_mft1_identity,
            "complete_decode_identity": complete_decode_identity,
            "s11_record_language_only": s11_record_language_only,
            "phase_anchor_or_reset_records": phase_anchor_or_reset_records,
            "executed_subset_count": executed_subset_count,
            "prior_input_and_direct_truth_identity": prior_input_identity,
        },
    }
    receipt = arguments.output / "r215_s11_focused_gate.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": str(receipt)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
