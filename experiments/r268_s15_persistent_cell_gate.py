"""Focused R-268 S15 persistence gate; corpus comparison belongs to S16."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "reference")]
from maf_p0.lapped_oracle import encode_lapped_stream
from maf_p0.native_core import NativeMain0Decoder
from maf_p0.persistent_cell_oracle import CellLaw, ExcitationLaw, pack_stream, scalar_render
from maf_p0.wav_io import read_pcm16_mono, write_pcm16_mono
from experiments.r216_s12_metrics import compute_metrics

MANIFEST = ROOT / "experiments/fixtures/r268_s15_persistent_cell_controls_v1.json"
DEFAULT_LIBRARY = ROOT / "build/cpp23-clang22-ninja/libresonith_core_shared.dll"
OUTPUT = ROOT / "artifacts/r268-s15-focused"


class Budget(ctypes.Structure):
    _fields_ = [("remaining", ctypes.c_uint64)]


class Control(ctypes.Structure):
    _fields_ = [
        ("phase_step_q32", ctypes.c_uint32), ("pulse_gain_q15", ctypes.c_int16),
        ("noise_gain_q15", ctypes.c_int16), ("reflection_q15", ctypes.c_int16 * 10),
    ]


class Weights(ctypes.Structure):
    _fields_ = [
        ("phase_step_shift", ctypes.c_uint16), ("pulse_gain", ctypes.c_uint16),
        ("noise_gain", ctypes.c_uint16), ("reflection", ctypes.c_uint16),
        ("lambda_q8", ctypes.c_uint32),
    ]


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def pcm_bytes(samples: np.ndarray) -> bytes:
    return np.asarray(samples, dtype="<i2").tobytes()


def round_shift_q15(value: int) -> int:
    quotient = abs(value) // 32768
    if abs(value) % 32768 >= 16384:
        quotient += 1
    return -quotient if value < 0 else quotient


def native_render(library: ctypes.CDLL, payload: bytes, count: int) -> np.ndarray:
    source = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
    output = (ctypes.c_int16 * count)()
    budget = Budget(10_000_000_000)
    status = library.resonith_pcell_render_model(
        source, len(payload), output, count, ctypes.byref(budget)
    )
    if status != 0:
        raise RuntimeError(f"native SFC2 render failed: {status}")
    return np.ctypeslib.as_array(output).copy()


def native_add(library: ctypes.CDLL, model: np.ndarray, truth: np.ndarray) -> np.ndarray:
    output = np.empty_like(model); budget = Budget(10_000_000_000)
    status = library.resonith_pcell_add_truth(
        model.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        truth.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), model.size,
        output.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), output.size,
        ctypes.byref(budget),
    )
    if status != 0:
        raise RuntimeError(f"native SFC2 Truth add failed: {status}")
    return output


def configure(library: ctypes.CDLL) -> None:
    library.resonith_pcell_render_model.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t, ctypes.POINTER(Budget),
    ]
    library.resonith_pcell_render_model.restype = ctypes.c_int
    library.resonith_pcell_add_truth.argtypes = [
        ctypes.POINTER(ctypes.c_int16), ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t, ctypes.POINTER(Budget),
    ]
    library.resonith_pcell_add_truth.restype = ctypes.c_int
    library.resonith_pcell_segment_controls.argtypes = [
        ctypes.POINTER(Control), ctypes.c_size_t, ctypes.POINTER(Weights),
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
    ]
    library.resonith_pcell_segment_controls.restype = ctypes.c_int


def interaction(config: dict) -> tuple[np.ndarray, tuple[CellLaw, ...]]:
    item = config["synthetic_controls"][0]
    cells = (
        CellLaw(1, 0, 80000, 0, 1600, 0, 1 << 26, 4000, 0, (-8192,) + (0,) * 9),
        CellLaw(2, 78400, 81600, 1600, 0, 0, 1 << 26, 4000, 0, (-16384,) + (0,) * 9),
    )
    accumulator = np.zeros(item["sample_count"], dtype=np.int64)
    for cell in cells:
        history = 0
        local = np.zeros(cell.duration, dtype=np.int16)
        for index in range(cell.duration):
            excitation = 4000 if index % 64 == 0 else 0
            value = max(-32768, min(32767, excitation - round_shift_q15(cell.reflection_q15[0] * history)))
            history = value
            if cell.fade_in and index < cell.fade_in:
                gain = (32767 * index + (cell.fade_in - 1) // 2) // (cell.fade_in - 1)
            elif cell.fade_out and index >= cell.duration - cell.fade_out:
                p = index - (cell.duration - cell.fade_out)
                gain = 32767 - (32767 * p + (cell.fade_out - 1) // 2) // (cell.fade_out - 1)
            else:
                gain = 32767
            local[index] = value
        start = cell.start
        accumulator[start : start + cell.duration] += local.astype(np.int64) * np.asarray([
            (32767 * i + (cell.fade_in - 1) // 2) // (cell.fade_in - 1)
            if cell.fade_in and i < cell.fade_in else
            32767 - (32767 * (i - (cell.duration - cell.fade_out)) + (cell.fade_out - 1) // 2) // (cell.fade_out - 1)
            if cell.fade_out and i >= cell.duration - cell.fade_out else 32767
            for i in range(cell.duration)
        ], dtype=np.int64)
    source = np.asarray([
        max(-32768, min(32767, round_shift_q15(int(value)))) for value in accumulator
    ], dtype=np.int16)
    if sha(pcm_bytes(source)) != item["pcm16_payload_sha256"]:
        raise RuntimeError("frozen interaction generator hash mismatch")
    return source, cells


def split_events(cells: tuple[CellLaw, ...], persistent: bool) -> tuple[ExcitationLaw, ...]:
    records = []
    for cell in cells:
        offsets = [0] if persistent else list(range(0, cell.duration, 80))
        for offset in offsets:
            duration = cell.duration if persistent else min(80, cell.duration - offset)
            records.append(ExcitationLaw(
                cell.cell_id, 0, offset, duration, cell.step_q32,
                cell.pulse_gain_q15, cell.noise_gain_q15,
            ))
    return tuple(records)


def refreshes(cells: tuple[CellLaw, ...], persistent: bool):
    if persistent:
        return ()
    return tuple(
        (cell.cell_id, offset, min(80, cell.duration - offset), cell.reflection_q15)
        for cell in cells for offset in range(0, cell.duration, 80)
    )


def s12(samples: np.ndarray, decoder: NativeMain0Decoder):
    return encode_lapped_stream(
        samples[:, None], 16000, coefficients_per_frame=68,
        half_window=512, band_count=24, entropy_backend="bounded",
        transform_backend="fixed", density_backend="adaptive",
        selection_backend="energy", native_decoder=decoder,
    )


def analyze_controls(samples: np.ndarray) -> tuple[object, np.ndarray]:
    """Fit anonymous causal pitch/resonator proposals in native NumPy batches."""

    count = (samples.size + 79) // 80
    padded_source = np.pad(samples.astype(np.float64), (320, count * 80 - samples.size))
    windows = np.lib.stride_tricks.sliding_window_view(padded_source, 320)
    endpoints = np.arange(80, count * 80 + 1, 80)
    controls = (Control * count)(); peaks = np.zeros(count, dtype=np.uint16)
    for first in range(0, count, 2048):
        last = min(count, first + 2048)
        raw = np.asarray(windows[endpoints[first:last]], dtype=np.float64)
        centered = raw - np.mean(raw, axis=1, keepdims=True)
        spectrum = np.fft.rfft(centered, n=1024, axis=1)
        correlation = np.fft.irfft(np.abs(spectrum) ** 2, n=1024, axis=1)[:, :268]
        rows = np.arange(last - first)
        lags = 40 + np.argmax(correlation[:, 40:268], axis=1)
        periodicity = correlation[rows, lags] / np.maximum(correlation[:, 0], 1.0)
        autocorrelation = correlation[:, :11]
        coefficients = np.zeros((last - first, 10), dtype=np.float64)
        reflection = np.zeros_like(coefficients)
        error = np.maximum(autocorrelation[:, 0], 1.0)
        for order in range(10):
            accumulated = autocorrelation[:, order + 1].copy()
            if order:
                accumulated += np.sum(
                    coefficients[:, :order] * autocorrelation[:, order:0:-1], axis=1
                )
            k = np.clip(-accumulated / error, -0.9, 0.9)
            previous = coefficients.copy()
            if order:
                coefficients[:, :order] = previous[:, :order] + k[:, None] * previous[:, order - 1 :: -1]
            coefficients[:, order] = k; reflection[:, order] = k
            error *= np.maximum(1.0e-5, 1.0 - k * k)
        residual = raw[:, -80:].copy()
        for order in range(10):
            residual += coefficients[:, order, None] * raw[:, 239 - order : 319 - order]
        local_peak = np.argmax(residual, axis=1)
        gain = residual[rows, local_peak]
        for row, index in enumerate(range(first, last)):
            voiced = periodicity[row] >= 0.25 and gain[row] >= 64.0
            lag = int(lags[row])
            proposed_step = ((1 << 32) + lag // 2) // lag
            controls[index].phase_step_q32 = max(16106127, min(107374182, proposed_step)) if voiced else 0
            controls[index].pulse_gain_q15 = max(0, min(32767, int(round(gain[row])))) if voiced else 0
            controls[index].noise_gain_q15 = 0
            for order in range(10):
                controls[index].reflection_q15[order] = int(np.clip(
                    round(reflection[row, order] * 32768), -29491, 29491
                ))
            peaks[index] = int(local_peak[row])
    return controls, peaks


def segmented_path(library: ctypes.CDLL, controls, lambda_q8: int, config: dict):
    count = len(controls); predecessor = (ctypes.c_uint32 * (count + 1))()
    proxy = config["segmented_dp"]["proxy_weights"]
    weights = Weights(proxy["phase_step_shift"], proxy["pulse_gain"],
        proxy["noise_gain"], proxy["reflection"], lambda_q8)
    cost = ctypes.c_uint64()
    status = library.resonith_pcell_segment_controls(
        controls, count, ctypes.byref(weights), predecessor, count + 1, ctypes.byref(cost)
    )
    if status != 0:
        raise RuntimeError(f"native segmented DP failed: {status}")
    path = []; end = count
    while end:
        begin = int(predecessor[end])
        if not 0 <= begin < end:
            raise RuntimeError("segmented DP predecessor is not progressive")
        path.append((begin, end)); end = begin
    return tuple(reversed(path)), int(cost.value)


def interpolate(start: int, end: int, position: int, duration: int) -> int:
    value = start * (duration - position) + end * position
    quotient = (abs(value) + duration // 2) // duration
    return -quotient if value < 0 else quotient


def excitation_endpoint(step: int, gain: int) -> tuple[int, int]:
    gain = max(0, min(32767, gain))
    return (0, 0) if gain == 0 else (max(16106127, min(107374182, step)), gain)


def build_cells(controls, peaks: np.ndarray, path, sample_count: int):
    cells = []; events = []
    for index, (begin, end) in enumerate(path):
        start = begin * 80
        stop = sample_count if index + 1 == len(path) else min(sample_count, end * 80 + 80)
        first, last = controls[begin], controls[end - 1]
        cell_id = index + 1; duration = stop - start
        phase = (-int(peaks[begin]) * int(first.phase_step_q32)) & 0xFFFFFFFF
        reflection = tuple(int(value) for value in first.reflection_q15)
        cell = CellLaw(cell_id, start, duration, 0 if index == 0 else 80,
            0 if index + 1 == len(path) else 80, phase, int(first.phase_step_q32),
            int(first.pulse_gain_q15), 0, reflection)
        cells.append(cell)
        offset = 0
        while offset < duration:
            length = min(160000, duration - offset); endpoint = offset + length
            end_step, end_gain = excitation_endpoint(
                interpolate(int(first.phase_step_q32), int(last.phase_step_q32), endpoint, duration),
                interpolate(int(first.pulse_gain_q15), int(last.pulse_gain_q15), endpoint, duration),
            )
            flags = (1 if end_step != int(first.phase_step_q32) else 0) | (2 if end_gain != int(first.pulse_gain_q15) else 0)
            events.append(ExcitationLaw(cell_id, flags, offset, length, end_step, end_gain, 0))
            offset = endpoint
    return tuple(cells), tuple(events)


def expanded_events(cells, events):
    by_id = {cell.cell_id: cell for cell in cells}; expanded = []
    state = {cell.cell_id: (cell.step_q32, cell.pulse_gain_q15, cell.noise_gain_q15) for cell in cells}
    for event in events:
        start_step, start_gain, start_noise = state[event.cell_id]
        local = 0
        while local < event.duration:
            length = min(80, event.duration - local); endpoint = local + length
            end_step, end_gain = excitation_endpoint(
                interpolate(start_step, event.end_step_q32, endpoint, event.duration),
                interpolate(start_gain, event.end_pulse_q15, endpoint, event.duration),
            )
            end_noise = interpolate(start_noise, event.end_noise_q15, endpoint, event.duration)
            flags = (1 if end_step != start_step else 0) | (2 if end_gain != start_gain else 0) | (4 if end_noise != start_noise else 0)
            expanded.append(ExcitationLaw(event.cell_id, flags, event.offset + local,
                length, end_step, end_gain, end_noise))
            local = endpoint
        state[event.cell_id] = (event.end_step_q32, event.end_pulse_q15, event.end_noise_q15)
    return tuple(expanded)


def speech_gate(candidate: dict, direct_metrics: dict, direct_bytes: int, entry: dict, tolerance: dict):
    current = candidate["metrics"]; base = direct_metrics
    value = lambda report, group, key: float(report[group][key])
    nonregressive = (
        value(current, "waveform", "snr_db") >= value(base, "waveform", "snr_db") - tolerance["snr_db"]
        and value(current, "speech", "stoi") >= value(base, "speech", "stoi") - tolerance["stoi"]
        and value(current, "speech", "estoi") >= value(base, "speech", "estoi") - tolerance["estoi"]
        and value(current, "spectral", "log_mel_rmse") <= value(base, "spectral", "log_mel_rmse") + tolerance["log_mel_rmse"]
        and value(current, "spectral", "magnitude_cosine_similarity") >= value(base, "spectral", "magnitude_cosine_similarity") - tolerance["magnitude_cosine"]
    )
    route_one = candidate["complete_bytes"] <= 0.97 * direct_bytes and nonregressive
    route_two = (
        candidate["complete_bytes"] <= 1.005 * direct_bytes
        and value(current, "speech", "stoi") > value(base, "speech", "stoi") + tolerance["stoi"]
        and value(current, "speech", "estoi") > value(base, "speech", "estoi") + tolerance["estoi"]
        and value(current, "spectral", "log_mel_rmse") < value(base, "spectral", "log_mel_rmse") - tolerance["log_mel_rmse"]
        and value(current, "waveform", "snr_db") >= value(base, "waveform", "snr_db") - 0.5
        and value(current, "spectral", "magnitude_cosine_similarity") >= value(base, "spectral", "magnitude_cosine_similarity") - tolerance["magnitude_cosine"]
    )
    opus = entry["opus_1_6_1"]
    comparisons = (
        (value(current, "speech", "stoi"), value(base, "speech", "stoi"), opus["stoi"], True),
        (value(current, "speech", "estoi"), value(base, "speech", "estoi"), opus["estoi"], True),
        (value(current, "spectral", "log_mel_rmse"), value(base, "spectral", "log_mel_rmse"), opus["log_mel_rmse"], False),
        (value(current, "spectral", "magnitude_cosine_similarity"), value(base, "spectral", "magnitude_cosine_similarity"), opus["magnitude_cosine"], True),
    )
    closures = []
    for candidate_value, base_value, opus_value, higher in comparisons:
        denominator = opus_value - base_value if higher else base_value - opus_value
        numerator = candidate_value - base_value if higher else base_value - candidate_value
        closures.append(0.0 if denominator <= 0 else numerator / denominator)
    return {"route_one": route_one, "route_two": route_two,
        "gap_closure": closures, "gap_axes_at_least_10_percent": sum(value >= 0.1 for value in closures),
        "quality_and_gap_pass": bool((route_one or route_two) and sum(value >= 0.1 for value in closures) >= 2)}


def evaluate_speech(entry: dict, config: dict, library: ctypes.CDLL, decoder: NativeMain0Decoder, output: Path):
    path = Path(entry["path"]); sample_rate, source = read_pcm16_mono(path)
    if sample_rate != 16000:
        raise RuntimeError("R-268 speech gate requires mono 16 kHz")
    if sha(path.read_bytes()) != entry["file_sha256"] or sha(pcm_bytes(source)) != entry["pcm16_payload_sha256"]:
        raise RuntimeError("R-268 speech identity mismatch")
    direct = s12(source, decoder)
    if len(direct.payload) != entry["s12"]["complete_bytes"]:
        raise RuntimeError("R-268 accepted-S12 complete-byte identity mismatch")
    direct_metrics = compute_metrics(source[:, None], direct.reconstruction, 16000, ("speech",))
    controls, peaks = analyze_controls(source)
    candidates = []
    for lambda_q8 in config["segmented_dp"]["lambda_q8"]:
        segments, proxy_cost = segmented_path(library, controls, lambda_q8, config)
        if len(segments) > 65535:
            continue
        cells, events = build_cells(controls, peaks, segments, source.size)
        envelope = pack_stream(source.size, 0x5245534F4E495448, cells, events)
        model = native_render(library, envelope, source.size)
        difference = source.astype(np.int32) - model.astype(np.int32)
        if np.any((difference < -32768) | (difference > 32767)):
            continue
        truth = s12(difference.astype(np.int16), decoder)
        payload = pack_stream(source.size, 0x5245534F4E495448, cells, events, truth=truth.payload)
        reconstruction = native_add(library, model, truth.reconstruction.reshape(-1))
        metrics = compute_metrics(source[:, None], reconstruction[:, None], 16000, ("speech",))
        candidate = {"lambda_q8": lambda_q8, "segments": segments, "cells": cells,
            "events": events, "payload": payload, "model": model, "reconstruction": reconstruction,
            "truth_bytes": len(truth.payload), "complete_bytes": len(payload),
            "proxy_cost": proxy_cost, "metrics": metrics}
        candidate["admission"] = speech_gate(candidate, direct_metrics, len(direct.payload),
            entry, config["metric_tolerances"])
        candidates.append(candidate)
    if not candidates:
        raise RuntimeError("R-268 found no checked PCM16 speech candidate")
    eligible = [candidate for candidate in candidates if candidate["admission"]["quality_and_gap_pass"]]
    selected = min(eligible or candidates, key=lambda c: (c["complete_bytes"], c["lambda_q8"]))
    cells, persistent = selected["cells"], selected["events"]
    expanded = expanded_events(cells, persistent)
    variants = {}
    for name, event_records, filter_persistent in (
        ("A", expanded, False), ("B", persistent, False),
        ("C", expanded, True), ("D", persistent, True),
    ):
        stream = pack_stream(source.size, 0x5245534F4E495448, cells, event_records,
            refreshes(cells, filter_persistent), truth=selected["payload"][-selected["truth_bytes"]:])
        rendered = native_render(library, stream, source.size)
        variants[name] = {"complete_bytes": len(stream), "model_sha256": sha(pcm_bytes(rendered))}
    if len({item["model_sha256"] for item in variants.values()}) != 1:
        raise RuntimeError("A/B/C/D model PCM differs")
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidate.resonith").write_bytes(selected["payload"])
    (output / "accepted-s12.resonith").write_bytes(direct.payload)
    write_pcm16_mono(output / "candidate-decoded.wav", 16000, selected["reconstruction"])
    write_pcm16_mono(output / "accepted-s12-decoded.wav", 16000, direct.reconstruction.reshape(-1))
    arm_pass = variants["D"]["complete_bytes"] < variants["B"]["complete_bytes"] and variants["D"]["complete_bytes"] < variants["C"]["complete_bytes"]
    return {
        "source": str(path), "source_pcm_sha256": sha(pcm_bytes(source)),
        "s12_complete_bytes": len(direct.payload), "candidate_complete_bytes": selected["complete_bytes"],
        "lambda_q8": selected["lambda_q8"], "cell_count": len(cells),
        "event_count": len(persistent), "truth_bytes": selected["truth_bytes"],
        "variants": variants, "candidate_metrics": selected["metrics"],
        "s12_metrics": direct_metrics, "opus_anchor": entry["opus_1_6_1"],
        "admission": selected["admission"] | {"arm_d_beats_b_and_c": arm_pass,
            "selected_as_s15": bool(eligible and arm_pass)},
        "lambda_candidates": [{"lambda_q8": item["lambda_q8"],
            "complete_bytes": item["complete_bytes"], "cell_count": len(item["cells"]),
            "event_count": len(item["events"]), "truth_bytes": item["truth_bytes"],
            "admission": item["admission"]} for item in candidates],
        "candidate_stream_sha256": sha(selected["payload"]),
        "candidate_decoded_sha256": sha(pcm_bytes(selected["reconstruction"])),
    }


def negative_controls(config: dict, decoder: NativeMain0Decoder) -> list[dict]:
    output = []
    for item in config["synthetic_controls"][1:]:
        samples = np.zeros(item["sample_count"], dtype=np.int16)
        if item["id"] == "isolated-impulse":
            samples[item["impulse_index"]] = item["impulse_value"]
        elif item["id"] == "xorshift32-white":
            state = item["seed_u32"]
            for index in range(samples.size):
                state ^= (state << 13) & 0xFFFFFFFF; state ^= state >> 17
                state ^= (state << 5) & 0xFFFFFFFF
                samples[index] = np.int16(((state >> 16) & 0xFFFF) - 32768)
        if sha(pcm_bytes(samples)) != item["pcm16_payload_sha256"]:
            raise RuntimeError(f"frozen {item['id']} hash mismatch")
        baseline = s12(samples, decoder)
        output.append({
            "id": item["id"], "selection": "byte-identical-s12-fallback",
            "s12_bytes": len(baseline.payload), "candidate_bytes": len(baseline.payload),
            "payload_sha256": sha(baseline.payload),
            "decoded_sha256": sha(pcm_bytes(baseline.reconstruction.reshape(-1))),
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--speech-id")
    args = parser.parse_args()
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    config = json.loads(MANIFEST.read_text(encoding="utf-8"))
    library = ctypes.CDLL(str(args.library.resolve(strict=True))); configure(library)
    decoder = NativeMain0Decoder(args.library)
    if args.speech_id:
        matches = [item for item in config["speech_inputs"] if item["id"] == args.speech_id]
        if len(matches) != 1:
            raise RuntimeError("unknown frozen R-268 speech id")
        report = {"schema": "resonith-r268-s15-speech-result-1",
            "speech": evaluate_speech(matches[0], config, library, decoder, args.output),
            "manifest_sha256": sha(MANIFEST.read_bytes()),
            "wall_seconds": time.perf_counter() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu}
        report["status"] = "pass" if report["speech"]["admission"]["selected_as_s15"] else "no-change"
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "speech-result.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 2
    source, cells = interaction(config)
    arms = {}
    for name, persistent_event, persistent_filter in (
        ("A", False, False), ("B", True, False),
        ("C", False, True), ("D", True, True),
    ):
        payload = pack_stream(
            source.size, 0x5245534F4E495448, cells,
            split_events(cells, persistent_event), refreshes(cells, persistent_filter),
        )
        rendered = native_render(library, payload, source.size)
        arms[name] = {
            "complete_bytes": len(payload), "stream_sha256": sha(payload),
            "decoded_sha256": sha(pcm_bytes(rendered)),
            "source_exact": bool(np.array_equal(rendered, source)),
        }
        if not np.array_equal(rendered, native_render(library, payload, source.size)):
            raise RuntimeError(f"arm {name} is nondeterministic")
        if name == "D" and not np.array_equal(rendered, scalar_render(payload)):
            raise RuntimeError("native/scalar SFC2 parity mismatch")
    baseline = s12(source, decoder)
    negatives = negative_controls(config, decoder)
    passed = (
        all(arm["source_exact"] for arm in arms.values())
        and arms["D"]["complete_bytes"] < arms["B"]["complete_bytes"]
        and arms["D"]["complete_bytes"] < arms["C"]["complete_bytes"]
        and arms["D"]["complete_bytes"] <= 0.8 * len(baseline.payload)
        and all(n["candidate_bytes"] == n["s12_bytes"] for n in negatives)
    )
    report = {
        "schema": "resonith-r268-s15-focused-result-1",
        "status": "pass" if passed else "kill",
        "manifest_sha256": sha(MANIFEST.read_bytes()),
        "native_library_sha256": sha(args.library.read_bytes()),
        "interaction": {
            "source_pcm_sha256": sha(pcm_bytes(source)),
            "s12_complete_bytes": len(baseline.payload), "arms": arms,
            "d_saving_vs_s12_percent": 100 * (1 - arms["D"]["complete_bytes"] / len(baseline.payload)),
        },
        "negative_controls": negatives,
        "wall_seconds": time.perf_counter() - started_wall,
        "cpu_seconds": time.process_time() - started_cpu,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / "result.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
