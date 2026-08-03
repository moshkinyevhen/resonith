"""Freeze exact internal S11 identities around the R-218 mechanical refactor.

This evidence tool observes the existing public research encoder without
changing its candidate language or selection.  It is intentionally separate
from the product path and records hashes rather than serializing large private
objects to disk.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import fields, is_dataclass
import hashlib
import json
from pathlib import Path
import struct
import time
from typing import Any

import numpy as np

from experiments.r215_s11_focused_gate import (
    _process_peak_working_set_bytes,
    _signals,
)
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.partial_graph_fixed import NativePartialGraph
from reference.maf_p0 import persistent_partial_field as persistent
from reference.maf_p0.wav_io import read_pcm16_channels


SCHEMA = "resonith-r218-s11-internal-identity-2"


def _write_size(hasher: Any, value: int) -> None:
    if value < 0:
        raise ValueError("canonical size cannot be negative")
    hasher.update(struct.pack(">Q", value))


def _write_blob(hasher: Any, tag: bytes, payload: bytes) -> None:
    hasher.update(tag)
    _write_size(hasher, len(payload))
    hasher.update(payload)


def _canonical_update(hasher: Any, value: Any) -> None:
    """Hash values with type, order, shape, and exact floating-point bits."""

    if value is None:
        hasher.update(b"N")
        return
    if isinstance(value, bool):
        hasher.update(b"B1" if value else b"B0")
        return
    if isinstance(value, int):
        sign = b"-" if value < 0 else b"+"
        magnitude = abs(value)
        encoded = magnitude.to_bytes(max(1, (magnitude.bit_length() + 7) // 8), "big")
        _write_blob(hasher, b"I" + sign, encoded)
        return
    if isinstance(value, float):
        hasher.update(b"F" + struct.pack(">d", value))
        return
    if isinstance(value, complex):
        hasher.update(b"C" + struct.pack(">dd", value.real, value.imag))
        return
    if isinstance(value, str):
        _write_blob(hasher, b"S", value.encode("utf-8"))
        return
    if isinstance(value, (bytes, bytearray, memoryview)):
        _write_blob(hasher, b"Y", bytes(value))
        return
    if isinstance(value, Path):
        _write_blob(hasher, b"P", str(value).encode("utf-8"))
        return
    if isinstance(value, np.generic):
        _write_blob(hasher, b"G", value.dtype.str.encode("ascii"))
        _write_blob(hasher, b"g", value.tobytes())
        return
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            raise TypeError("object arrays are not canonical evidence")
        hasher.update(b"A")
        _write_blob(hasher, b"d", value.dtype.str.encode("ascii"))
        _canonical_update(hasher, tuple(int(dimension) for dimension in value.shape))
        _write_blob(hasher, b"a", value.tobytes(order="C"))
        return
    if isinstance(value, ctypes.Array):
        hasher.update(b"R")
        _write_blob(
            hasher,
            b"t",
            f"{type(value).__module__}.{type(value).__qualname__}".encode("utf-8"),
        )
        _write_size(hasher, len(value))
        for item in value:
            _canonical_update(hasher, item)
        return
    if isinstance(value, ctypes.Structure):
        hasher.update(b"U")
        _write_blob(
            hasher,
            b"t",
            f"{type(value).__module__}.{type(value).__qualname__}".encode("utf-8"),
        )
        _write_size(hasher, len(value._fields_))
        for name, *_field_type in value._fields_:
            _write_blob(hasher, b"n", name.encode("utf-8"))
            _canonical_update(hasher, getattr(value, name))
        return
    if is_dataclass(value) and not isinstance(value, type):
        hasher.update(b"D")
        _write_blob(
            hasher,
            b"t",
            f"{type(value).__module__}.{type(value).__qualname__}".encode("utf-8"),
        )
        dataclass_fields = fields(value)
        _write_size(hasher, len(dataclass_fields))
        for field in dataclass_fields:
            _write_blob(hasher, b"n", field.name.encode("utf-8"))
            _canonical_update(hasher, getattr(value, field.name))
        return
    if isinstance(value, dict):
        hasher.update(b"M")
        _write_size(hasher, len(value))
        for key, item in value.items():
            _canonical_update(hasher, key)
            _canonical_update(hasher, item)
        return
    if isinstance(value, tuple):
        hasher.update(b"T")
        _write_size(hasher, len(value))
        for item in value:
            _canonical_update(hasher, item)
        return
    if isinstance(value, list):
        hasher.update(b"L")
        _write_size(hasher, len(value))
        for item in value:
            _canonical_update(hasher, item)
        return
    if isinstance(value, (set, frozenset)):
        encoded_items = []
        for item in value:
            item_hasher = hashlib.sha256()
            _canonical_update(item_hasher, item)
            encoded_items.append(item_hasher.digest())
        hasher.update(b"E")
        _write_size(hasher, len(encoded_items))
        for encoded in sorted(encoded_items):
            _write_blob(hasher, b"e", encoded)
        return
    if isinstance(value, ctypes._SimpleCData):
        hasher.update(b"Q")
        _write_blob(
            hasher,
            b"t",
            f"{type(value).__module__}.{type(value).__qualname__}".encode("utf-8"),
        )
        _canonical_update(hasher, value.value)
        return
    raise TypeError(f"unsupported canonical evidence type: {type(value)!r}")


def canonical_sha256(value: Any) -> str:
    hasher = hashlib.sha256()
    _canonical_update(hasher, value)
    return hasher.hexdigest()


class _Capture:
    def __init__(self) -> None:
        self.values: dict[str, list[Any]] = {
            "observation_sets": [],
            "fixed_graph_inputs": [],
            "edge_results": [],
            "path_results": [],
            "lowered_lanes": [],
            "evaluated_subsets": [],
        }

    def append(self, name: str, value: Any) -> None:
        self.values[name].append(value)

    def fingerprints(self) -> dict[str, dict[str, Any]]:
        result = {}
        for name, values in self.values.items():
            result[name] = {
                "call_count": len(values),
                "sha256": canonical_sha256(values),
                "per_call_sha256": [canonical_sha256(value) for value in values],
            }
        return result


class _CapturingGraph:
    def __init__(self, inner: NativePartialGraph, capture: _Capture) -> None:
        self._inner = inner
        self._capture = capture

    def edges(self, *arguments: Any, **keywords: Any) -> Any:
        result = self._inner.edges(*arguments, **keywords)
        self._capture.append("edge_results", result)
        return result

    def paths(self, *arguments: Any, **keywords: Any) -> Any:
        result = self._inner.paths(*arguments, **keywords)
        self._capture.append("path_results", result)
        return result


def _stable_candidate(candidate: Any) -> dict[str, Any]:
    report = dict(candidate.report)
    report.pop("elapsed_seconds", None)
    return {
        "selected_payload": candidate.selected_payload,
        "selected_reconstruction": candidate.selected_reconstruction,
        "selected_kind": candidate.selected_kind,
        "baseline_payload": candidate.baseline_payload,
        "baseline_reconstruction": candidate.baseline_reconstruction,
        "lanes": candidate.lanes,
        "report": report,
    }


def _encode_with_capture(
    samples: np.ndarray,
    sample_rate: int,
    *,
    native_core: Path,
    coefficients_per_frame: int,
    half_window: int,
    band_count: int,
) -> tuple[Any, _Capture, float]:
    capture = _Capture()
    decoder = NativeMain0Decoder(str(native_core))
    graph = _CapturingGraph(NativePartialGraph(str(native_core)), capture)
    original_observe = persistent.observe_complex_partials
    original_fixed = persistent._fixed_graph_inputs
    original_lower = persistent._lower_lane
    original_evaluate = persistent._evaluate_subset

    def observed(*arguments: Any, **keywords: Any) -> Any:
        result = original_observe(*arguments, **keywords)
        capture.append("observation_sets", result)
        return result

    def fixed(*arguments: Any, **keywords: Any) -> Any:
        result = original_fixed(*arguments, **keywords)
        capture.append("fixed_graph_inputs", result)
        return result

    def lowered(*arguments: Any, **keywords: Any) -> Any:
        result = original_lower(*arguments, **keywords)
        capture.append("lowered_lanes", result)
        return result

    def evaluated(*arguments: Any, **keywords: Any) -> Any:
        result = original_evaluate(*arguments, **keywords)
        capture.append("evaluated_subsets", result)
        return result

    persistent.observe_complex_partials = observed
    persistent._fixed_graph_inputs = fixed
    persistent._lower_lane = lowered
    persistent._evaluate_subset = evaluated
    started = time.perf_counter()
    try:
        candidate = persistent.encode_persistent_partial_truth_candidate(
            samples,
            sample_rate,
            native_graph=graph,
            native_decoder=decoder,
            coefficients_per_frame=coefficients_per_frame,
            half_window=half_window,
            band_count=band_count,
        )
    finally:
        persistent.observe_complex_partials = original_observe
        persistent._fixed_graph_inputs = original_fixed
        persistent._lower_lane = original_lower
        persistent._evaluate_subset = original_evaluate
    return candidate, capture, time.perf_counter() - started


def _load_input(arguments: argparse.Namespace) -> tuple[int, np.ndarray, str]:
    if arguments.focused_name is not None:
        samples = _signals()[arguments.focused_name]
        return 8000, samples, f"focused:{arguments.focused_name}"
    sample_rate, samples = read_pcm16_channels(arguments.source_wav)
    if arguments.prefix_frames is not None:
        samples = samples[: arguments.prefix_frames].copy()
    return sample_rate, samples, str(arguments.source_wav.resolve())


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--focused-name", choices=tuple(_signals()))
    source.add_argument("--source-wav", type=Path)
    parser.add_argument("--prefix-frames", type=int)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--native-core", type=Path, required=True)
    parser.add_argument("--coefficients-per-frame", type=int, required=True)
    parser.add_argument("--half-window", type=int, required=True)
    parser.add_argument("--band-count", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.prefix_frames is not None and arguments.prefix_frames <= 0:
        raise ValueError("prefix frames must be positive")
    if arguments.focused_name is not None and arguments.prefix_frames is not None:
        raise ValueError("focused fixtures cannot be truncated")

    sample_rate, samples, source_name = _load_input(arguments)
    if not np.any(samples):
        raise ValueError("identity input must be acoustically active")
    candidate, capture, encode_seconds = _encode_with_capture(
        samples,
        sample_rate,
        native_core=arguments.native_core.resolve(),
        coefficients_per_frame=arguments.coefficients_per_frame,
        half_window=arguments.half_window,
        band_count=arguments.band_count,
    )
    stable_candidate = _stable_candidate(candidate)
    fingerprints = capture.fingerprints()
    fingerprints["rdo_ledger"] = {
        "call_count": 1,
        "sha256": canonical_sha256(stable_candidate),
        "per_call_sha256": [canonical_sha256(stable_candidate)],
    }
    combined = canonical_sha256(fingerprints)
    pcm = np.ascontiguousarray(samples, dtype="<i2")
    peak_working_set_bytes = _process_peak_working_set_bytes()
    result = {
        "schema": SCHEMA,
        "case_id": arguments.case_id,
        "source": source_name,
        "sample_rate": sample_rate,
        "frames": int(samples.shape[0]),
        "channels": int(samples.shape[1]),
        "source_pcm16le_sha256": hashlib.sha256(pcm.tobytes()).hexdigest(),
        "source_rms": float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))),
        "coefficients_per_frame": arguments.coefficients_per_frame,
        "half_window": arguments.half_window,
        "band_count": arguments.band_count,
        "native_core_sha256": hashlib.sha256(
            arguments.native_core.read_bytes()
        ).hexdigest(),
        "analyzer_sha256": hashlib.sha256(
            Path(persistent.__file__).with_name(
                "complex_partial_analyzer.py"
            ).read_bytes()
        ).hexdigest(),
        "predictor_sha256": hashlib.sha256(Path(persistent.__file__).read_bytes()).hexdigest(),
        "encode_seconds": encode_seconds,
        "diagnostic_process_peak_working_set_bytes": peak_working_set_bytes,
        "resource_measurement_authority": "external-parent-receipt-required",
        "selected_kind": candidate.selected_kind,
        "selected_bytes": len(candidate.selected_payload),
        "selected_payload_sha256": hashlib.sha256(candidate.selected_payload).hexdigest(),
        "selected_pcm16le_sha256": hashlib.sha256(
            np.asarray(candidate.selected_reconstruction, dtype="<i2").tobytes()
        ).hexdigest(),
        "fingerprints": fingerprints,
        "combined_internal_sha256": combined,
        "retained_evidence_bytes": 0,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    while True:
        encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        if result["retained_evidence_bytes"] == len(encoded):
            break
        result["retained_evidence_bytes"] = len(encoded)
    arguments.output.write_bytes(encoded)
    print(json.dumps({
        "status": "PASS",
        "case_id": arguments.case_id,
        "encode_seconds": encode_seconds,
        "combined_internal_sha256": combined,
        "output": str(arguments.output.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
