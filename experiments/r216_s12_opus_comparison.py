"""Restartable, streaming R-216 S12 Resonith-versus-Opus comparison."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import ctypes
import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import time
import uuid

import numpy as np

from experiments.r216_s12_metrics import compute_metrics, dominates, quality_axes
from reference.maf_p0.causal_basis_truth_candidate import decode_causal_basis_truth_candidate
from reference.maf_p0.complex_partial_analyzer import ComplexPartialAnalyzerManifest
from reference.maf_p0.lapped_oracle import encode_lapped_stream
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.partial_graph_fixed import NativePartialGraph
from reference.maf_p0.persistent_partial_field import (
    PersistentPartialLanguage, encode_persistent_partial_truth_candidate)
from reference.maf_p0.wav_io import read_pcm16_channels, write_pcm16_channels


REPOSITORY = Path(__file__).resolve().parents[1]; MANIFEST_SHA256 = "551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0"
MANIFEST_SCHEMA = "resonith-r216-s12-opus-only-manifest-2"; RECEIPT_SCHEMA = "resonith-r216-s12-item-receipt-1"; RUN_SCHEMA = "resonith-r216-s12-run-index-1"; RUNNER_SCHEMA = "resonith-r216-s12-opus-only-runner-1"
EXPECTED_SOURCE_REVISION = "7e2726789ca980177a32e6b36cfcd9f1d90b5463"; EXPECTED_PREDICTOR_SHA256 = "583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec"; EXPECTED_WRAPPER_SHA256 = "32c514e5c9cf4f1beffba61c62d262489f35e2fb0c2e74c3cfdae2a132694045"
EXPECTED_CORE_SHA256 = "f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed"; EXPECTED_OPUSENC_SHA256 = "0b8d4e8db7697bd8981e9246de1bd8a1df05c2bbb98bba2b2090d7bb585e70f9"
EXPECTED_OPUSDEC_SHA256 = "ea1a553102020f58f0af86eb1cf2377a055ccbc93a2130fa62f77c96f522c8e3"; EXPECTED_OBJECTIVE_SHA256 = "284e27fca406775e90f0c0db075808b5203c9075600ccebf090e0065cb1c9bc5"
EXPECTED_PERCEPTUAL_SHA256 = "4c02f3a7d2b04f26a0c51646c567daaeae391f1b1d23ba19974cf5780663c425"; EXPECTED_PREFLIGHT_SHA256 = "5e87d450ca17699884eb4a66bbc95ff7a8b59c16c8efed754d614f6f24679201"; EXPECTED_HELPER_SHA256 = "ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3"; EXPECTED_TESTS_SHA256 = "a466820c8a1f47e9ee9c30213e727023e2f4e174e4b18d0a63e37fe2e2a7ecc6"
MAXIMUM_OBSERVATIONS = 3_500_000; GIB = 1024**3
MODE_CODE = {"vbr": 0, "cvbr": 1, "hard-cbr": 2}; APPLICATION_CODE = {"auto": 0, "music": 1, "speech": 2}


@dataclass(frozen=True, order=True)
class OpusConfig:
    mode: str; application: str
    frame_us: int; phase_inversion: bool
    bandwidth_request: int = 0; bandwidth_value: int = -1000; force_channels: int = -1000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(samples, dtype="<i2").tobytes()
    ).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ) + "\n").encode("utf-8")


def write_fsynced(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(path)
    with path.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())


def write_json_fsynced(path: Path, value: object) -> None:
    write_fsynced(path, _json_bytes(value))


def append_jsonl_fsynced(path: Path, value: object) -> None:
    payload = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("ab") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())


def replace_json_fsynced(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    write_json_fsynced(temporary, value)
    os.replace(temporary, path)


def write_wav_fsynced(path: Path, rate: int, samples: np.ndarray) -> None:
    if path.exists():
        raise FileExistsError(path)
    write_pcm16_channels(path, rate, samples)
    with path.open("r+b") as source:
        os.fsync(source.fileno())


def _round_ratio_even(numerator: int, denominator: int) -> int:
    if numerator < 0 or denominator <= 0:
        raise ValueError("round-half-even accepts a nonnegative ratio")
    quotient, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    if twice > denominator or (twice == denominator and quotient & 1):
        quotient += 1
    return quotient


def initial_q5(target_bytes: int, rate: int, frames: int, channels: int) -> int:
    value = _round_ratio_even(
        target_bytes * 8 * 100_000 * rate, frames * 1000
    )
    return min(256 * channels * 100_000, max(6 * 100_000, value))


def feedback_q5(previous: int, target_bytes: int, actual_bytes: int,
                channels: int) -> int:
    value = _round_ratio_even(previous * target_bytes, actual_bytes)
    return min(256 * channels * 100_000, max(6 * 100_000, value))


def serial_for_point(manifest_digest: bytes, item_id: str,
                     config: OpusConfig, q5: int) -> int:
    item = item_id.encode("utf-8")
    if len(item) > 65535:
        raise ValueError("item ID is too long")
    domain = bytearray(b"resonith-r216-opus-serial-v1\0")
    domain.extend(manifest_digest)
    domain.extend(struct.pack("<H", len(item)))
    domain.extend(item)
    domain.extend(struct.pack(
        "<BBIBiiiQ", MODE_CODE[config.mode],
        APPLICATION_CODE[config.application], config.frame_us,
        int(config.phase_inversion), config.bandwidth_request,
        config.bandwidth_value, config.force_channels, q5,
    ))
    serial = int.from_bytes(hashlib.sha256(domain).digest()[:4], "little")
    return serial or 1


def normalized_ogg_sha256(path: Path) -> tuple[str, int]:
    payload = path.read_bytes()
    digest, cursor, pages = hashlib.sha256(), 0, 0
    while cursor < len(payload):
        if cursor + 27 > len(payload) or payload[cursor:cursor+4] != b"OggS":
            raise RuntimeError("invalid Ogg page")
        segments = payload[cursor + 26]
        header_end = cursor + 27 + segments
        if header_end > len(payload):
            raise RuntimeError("truncated Ogg segment table")
        page_end = header_end + sum(payload[cursor+27:header_end])
        if page_end > len(payload):
            raise RuntimeError("truncated Ogg body")
        page = bytearray(payload[cursor:page_end])
        page[14:18] = b"\0" * 4
        page[22:26] = b"\0" * 4
        digest.update(page)
        cursor, pages = page_end, pages + 1
    return digest.hexdigest(), pages


def base_configurations(channels: int) -> tuple[OpusConfig, ...]:
    phase_modes = (True, False) if channels == 2 else (True,)
    return tuple(
        OpusConfig(mode, application, int(frame * 1000), phase)
        for mode in ("vbr", "cvbr", "hard-cbr")
        for application in ("auto", "music", "speech")
        for frame in (2.5, 5, 10, 20, 40, 60)
        for phase in phase_modes
    )


def ctl_configurations(seed: OpusConfig, channels: int) -> tuple[OpusConfig, ...]:
    configs = []
    forces = (-1000, 1) if channels == 2 else (-1000,)
    for request in (4004, 4008):
        for value in range(1101, 1106):
            for force in forces:
                configs.append(replace(
                    seed, bandwidth_request=request,
                    bandwidth_value=value, force_channels=force,
                ))
    if channels == 2:
        configs.append(replace(seed, force_channels=1))
    return tuple(configs)


def analyzer_bound(frames: int, channels: int,
                   manifest: ComplexPartialAnalyzerManifest | None = None) -> int:
    manifest = manifest or ComplexPartialAnalyzerManifest()
    detector_frames = sum(
        (frames + resolution.hop_samples - 1) // resolution.hop_samples + 1
        for resolution in manifest.resolutions
    )
    return (detector_frames * (channels + 1)
            * manifest.observations_per_detector_frame)


def _child_resources(process: subprocess.Popen) -> tuple[int, float]:
    if os.name != "nt":
        return 0, 0.0
    query = 0x0400 | 0x0010
    handle = ctypes.windll.kernel32.OpenProcess(query, False, process.pid)
    if not handle:
        return 0, 0.0
    try:
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = Counters(cb=ctypes.sizeof(Counters))
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        creation, exit_time, kernel, user = (ctypes.c_uint64() for _ in range(4))
        times_ok = ctypes.windll.kernel32.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exit_time),
            ctypes.byref(kernel), ctypes.byref(user),
        )
        peak = int(counters.PeakWorkingSetSize) if ok else 0
        cpu = (kernel.value + user.value) / 10_000_000 if times_ok else 0.0
        return peak, cpu
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _tree_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _terminate_tree(process: subprocess.Popen) -> tuple[str, str]:
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if result.returncode: raise RuntimeError("Windows process-tree termination failed")
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    return process.communicate(timeout=30)


def run_bounded(command: list[str], timeout: float, rss_limit: int,
                cwd: Path, disk_root: Path | None = None,
                disk_limit: int | None = None) -> dict[str, object]:
    started = time.perf_counter()
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=os.name != "nt",
    )
    peak = cpu = 0.0
    while process.poll() is None:
        child_peak, child_cpu = _child_resources(process)
        peak, cpu = max(peak, child_peak), max(cpu, child_cpu)
        if peak > rss_limit:
            _terminate_tree(process)
            raise MemoryError(f"child RSS exceeded {rss_limit}")
        if disk_root is not None and disk_limit is not None and _tree_bytes(disk_root) > disk_limit:
            _terminate_tree(process)
            raise OSError(f"staging exceeded {disk_limit} bytes")
        if time.perf_counter() - started > timeout:
            _terminate_tree(process)
            raise TimeoutError(f"child exceeded {timeout} seconds")
        time.sleep(0.025)
    stdout, stderr = process.communicate()
    child_peak, child_cpu = _child_resources(process)
    peak, cpu = max(peak, child_peak), max(cpu, child_cpu)
    if process.returncode:
        detail = (stderr or stdout).strip()
        raise RuntimeError(f"subprocess failed ({process.returncode}): {detail}")
    return {
        "wall_seconds": time.perf_counter() - started,
        "cpu_seconds": cpu,
        "peak_rss_bytes": int(peak),
    }


def _opus_command(opusenc: Path, source: Path, output: Path,
                  config: OpusConfig, q5: int, serial: int) -> list[str]:
    command = [
        str(opusenc), "--quiet", "--bitrate",
        f"{q5 // 100_000}.{q5 % 100_000:05d}",
        {"vbr": "--vbr", "cvbr": "--cvbr", "hard-cbr": "--hard-cbr"}[
            config.mode
        ], "--framesize", f"{config.frame_us / 1000:g}", "--comp", "10",
        "--expect-loss", "0", "--max-delay", "1000",
        "--discard-comments", "--discard-pictures", "--padding", "0",
        "--serial", str(serial),
    ]
    if config.application != "auto":
        command.append(f"--{config.application}")
    if not config.phase_inversion:
        command.append("--no-phase-inv")
    if config.bandwidth_request:
        command.extend(("--set-ctl-int",
                        f"{config.bandwidth_request}={config.bandwidth_value}"))
    if config.force_channels != -1000:
        command.extend(("--set-ctl-int", f"4022={config.force_channels}"))
    command.extend((str(source), str(output)))
    return command


def _encode_point(opusenc: Path, source: Path, output: Path,
                  manifest_digest: bytes, item_id: str, config: OpusConfig,
                  q5: int, timeout: float) -> dict[str, object]:
    serial = serial_for_point(manifest_digest, item_id, config, q5)
    command = _opus_command(opusenc, source, output, config, q5, serial)
    resources = run_bounded(command, timeout, 12 * GIB, REPOSITORY)
    normalized_hash, pages = normalized_ogg_sha256(output)
    record = {
        "config": asdict(config), "q5": q5, "serial": serial,
        "argv": command[1:-2] + ["<source>", "<output>"],
        "bytes": output.stat().st_size,
        "raw_sha256": sha256_file(output),
        "normalized_sha256": normalized_hash, "ogg_pages": pages,
        "encode_resources": resources,
    }
    return record


def _feedback_search(opusenc: Path, source: Path, temporary: Path,
                     manifest_digest: bytes, item_id: str, config: OpusConfig,
                     target: int, rate: int, frames: int, channels: int,
                     timeout: float, deadline: float,
                     ledger: Path) -> list[dict[str, object]]:
    q5 = initial_q5(target, rate, frames, channels)
    records = []
    for attempt in range(4):
        output = temporary / f"feedback-{uuid.uuid4().hex}.opus"
        remaining = min(timeout, deadline - time.perf_counter())
        if remaining <= 0:
            raise TimeoutError("Opus item wall ceiling exceeded")
        record = _encode_point(
            opusenc, source, output, manifest_digest, item_id, config, q5,
            remaining,
        )
        record["attempt"] = attempt
        append_jsonl_fsynced(ledger, {"record_kind": "feedback", **record})
        output.unlink()
        records.append(record)
        q5 = feedback_q5(q5, target, int(record["bytes"]), channels)
    return records


def _decode_strict_point(point: dict[str, object], opusenc: Path,
                         opusdec: Path, source: Path, temporary: Path,
                         manifest_digest: bytes, item_id: str, rate: int,
                         expected_shape: tuple[int, int], categories: list[str],
                         timeout: float, deadline: float,
                         ledger: Path) -> tuple[dict[str, object], Path]:
    config = OpusConfig(**point["config"])
    q5 = int(point["q5"])
    encoded = temporary / f"strict-{uuid.uuid4().hex}.opus"
    serial = serial_for_point(manifest_digest, item_id, config, q5)
    remaining = min(timeout, deadline - time.perf_counter())
    if remaining <= 0:
        raise TimeoutError("Opus item wall ceiling exceeded")
    encode_resources = run_bounded(
        _opus_command(opusenc, source, encoded, config, q5, serial),
        remaining, 12 * GIB, REPOSITORY,
    )
    if sha256_file(encoded) != point["raw_sha256"]:
        raise RuntimeError("Opus retained-byte determinism failure")
    decoded = temporary / f"decoded-{uuid.uuid4().hex}.wav"
    remaining = min(timeout, deadline - time.perf_counter())
    if remaining <= 0:
        raise TimeoutError("Opus item wall ceiling exceeded")
    decode_resources = run_bounded(
        [str(opusdec), "--quiet", "--rate", str(rate),
         str(encoded), str(decoded)], remaining, 12 * GIB, REPOSITORY,
    )
    decoded_rate, samples = read_pcm16_channels(decoded)
    source_rate, reference = read_pcm16_channels(source)
    if decoded_rate != rate or source_rate != rate or samples.shape != expected_shape:
        raise RuntimeError("Opus decoder PCM shape/rate mismatch")
    metrics = compute_metrics(reference, samples, rate, categories)
    record = dict(point)
    record.update({
        "metrics": metrics, "decode_resources": decode_resources,
        "repeat_encode_resources": encode_resources,
        "decoded_pcm16le_sha256": pcm_sha256(samples),
    })
    append_jsonl_fsynced(ledger, {"record_kind": "strict-measurement", **record})
    decoded.unlink()
    del samples, reference
    return record, encoded


def _nested(report: dict[str, object], path: str) -> float | None:
    value: object = report
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return float(value) if isinstance(value, (int, float)) else None


def _phase_rmse(report: dict[str, object]) -> float | None:
    channels = report["phase_channel"]["channels"]
    values = [row["phase"]["rmse_radians"] for row in channels
              if row["phase"]["rmse_radians"] is not None]
    return max(map(float, values)) if values else None


def _axis(record: dict[str, object], axis: str) -> float | None:
    report = record["metrics"]
    if axis == "phase_rmse":
        return _phase_rmse(report)
    paths = {
        "snr": "waveform.snr_db", "si_sdr": "waveform.si_sdr_db",
        "segmental": "waveform.segmental_snr_db",
        "cosine": "spectral.magnitude_cosine_similarity",
        "rms": "waveform.rms_error",
        "maximum": "waveform.maximum_absolute_error",
        "log_mel": "spectral.log_mel_rmse",
        "lsd": "spectral.log_spectral_distance_db",
        "transient": "transient.worst_pre_echo_error_db",
        "correlation": "phase_channel.stereo.correlation_error",
        "mid_side": "phase_channel.stereo.mid_side_ratio_error_db",
        "stoi": "speech.stoi", "estoi": "speech.estoi",
    }
    return _nested(report, paths[axis])


def _best_axis(points: list[dict[str, object]], axis: str,
               direction: str) -> dict[str, object] | None:
    available = [point for point in points if _axis(point, axis) is not None]
    if not available:
        return None
    sign = -1.0 if direction == "max" else 1.0
    return min(available, key=lambda point: (
        sign * float(_axis(point, axis)), abs(int(point["byte_delta"])),
        tuple(asdict(OpusConfig(**point["config"])).values()), int(point["q5"]),
    ))


def choose_seeds(points: list[dict[str, object]]) -> tuple[OpusConfig, ...]:
    ordered_axes = (
        ("snr", "max"), ("si_sdr", "max"), ("segmental", "max"),
        ("cosine", "max"), ("rms", "min"), ("maximum", "min"),
        ("log_mel", "min"), ("lsd", "min"), ("phase_rmse", "min"),
        ("transient", "min"), ("correlation", "min"),
        ("mid_side", "min"), ("stoi", "max"), ("estoi", "max"),
    )
    chosen = []
    for axis, direction in ordered_axes:
        point = _best_axis(points, axis, direction)
        if point is not None:
            chosen.append(OpusConfig(**point["config"]))
    if points:
        chosen.append(OpusConfig(**choose_listening_point(points)["config"]))
    return tuple(dict.fromkeys(chosen))[:15]


def choose_listening_point(points: list[dict[str, object]]) -> dict[str, object]:
    if not points:
        raise ValueError("no Opus points for listening selection")
    speech = any(_axis(point, "estoi") is not None for point in points)
    def missing(value: float | None, high: bool) -> float:
        if value is None:
            return math.inf
        return -value if high else value
    def key(point: dict[str, object]):
        if speech:
            quality = (
                missing(_axis(point, "estoi"), True),
                missing(_axis(point, "stoi"), True),
                missing(_axis(point, "log_mel"), False),
                missing(_axis(point, "si_sdr"), True),
            )
        else:
            quality = (
                missing(_axis(point, "log_mel"), False),
                missing(_axis(point, "si_sdr"), True),
                missing(_axis(point, "phase_rmse"), False),
                missing(_axis(point, "transient"), False),
            )
        return quality + (
            abs(int(point["byte_delta"])),
            tuple(asdict(OpusConfig(**point["config"])).values()), int(point["q5"]),
        )
    return min(points, key=key)


def pareto_points(points: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        point for index, point in enumerate(points)
        if not any(
            other_index != index
            and dominates(other["metrics"], point["metrics"])
            for other_index, other in enumerate(points)
        )
    ]


def _run_opus_frontier(source: Path, source_samples: np.ndarray, rate: int,
                       categories: list[str], target: int, item_id: str,
                       manifest_digest: bytes, opusenc: Path, opusdec: Path,
                       temporary: Path, retained: Path,
                       staging_ceiling: int, item_deadline: float) -> dict[str, object]:
    channels, frames = source_samples.shape[1], source_samples.shape[0]
    tolerance = max(64, target // 1000)
    timeout = max(120.0, 2.0 * frames / rate + 30.0)
    all_attempts, strict = [], []
    ledger = retained / "point-ledger.jsonl"

    def stage(configs: tuple[OpusConfig, ...], label: str) -> None:
        for config_index, config in enumerate(configs):
            if time.perf_counter() > item_deadline:
                raise TimeoutError("Opus item wall ceiling exceeded")
            attempts = _feedback_search(
                opusenc, source, temporary, manifest_digest, item_id, config,
                target, rate, frames, channels, timeout,
                item_deadline, ledger,
            )
            for point in attempts:
                point["stage"] = label
                point["configuration_index"] = config_index
                point["byte_delta"] = int(point["bytes"]) - target
                all_attempts.append(point)
                if abs(int(point["byte_delta"])) <= tolerance:
                    measured, ogg = _decode_strict_point(
                        point, opusenc, opusdec, source, temporary,
                        manifest_digest, item_id, rate, source_samples.shape,
                        categories, timeout,
                        item_deadline, ledger,
                    )
                    measured["temporary_ogg"] = str(ogg)
                    strict.append(measured)

    stage(base_configurations(channels), "base")
    base_strict = list(strict)
    seeds = choose_seeds(base_strict)
    ctl = tuple(dict.fromkeys(
        config for seed in seeds for config in ctl_configurations(seed, channels)
    ))
    stage(ctl, "stable-public-ctl")
    pareto = pareto_points(strict)
    existing_bytes = sum(
        path.stat().st_size
        for path in retained.parent.parent.rglob("*") if path.is_file()
    )
    bounded_wav_allowance = 44 + frames * channels * 2
    if (existing_bytes + sum(int(point["bytes"]) for point in pareto)
            + bounded_wav_allowance > staging_ceiling):
        raise RuntimeError("Pareto materialization would exceed staging ceiling")
    pareto_ids = {id(point) for point in pareto}
    for index, point in enumerate(strict):
        source_ogg = Path(point.pop("temporary_ogg"))
        if id(point) in pareto_ids:
            name = f"pareto-{index:04d}.opus"
            destination = retained / name
            with source_ogg.open("r+b") as payload:
                os.fsync(payload.fileno())
            os.replace(source_ogg, destination)
            point["retained_ogg"] = name
        else:
            source_ogg.unlink()
    listening = None
    if pareto:
        listening = choose_listening_point(pareto)
        decoded_path = retained / "opus-listening.wav"
        remaining = min(timeout, item_deadline - time.perf_counter())
        if remaining <= 0: raise TimeoutError("Opus item wall ceiling exceeded")
        run_bounded(
            [str(opusdec), "--quiet", "--rate", str(rate),
             str(retained / listening["retained_ogg"]), str(decoded_path)],
            remaining, 12 * GIB, REPOSITORY,
        )
        with decoded_path.open("r+b") as wav:
            os.fsync(wav.fileno())
    return {
        "target_complete_bytes": target, "strict_tolerance_bytes": tolerance,
        "base_configuration_count": len(base_configurations(channels)),
        "seed_configurations": [asdict(seed) for seed in seeds],
        "ctl_configuration_count": len(ctl),
        "all_attempts": all_attempts,
        "strict_point_count": len(strict),
        "strict_points": strict,
        "pareto_point_count": len(pareto),
        "pareto_points": pareto,
        "listening_point_raw_sha256": (
            listening["raw_sha256"] if listening else None
        ),
    }


def _encode_s11(samples: np.ndarray, rate: int, budget: int,
                item: dict[str, object], core: Path) -> tuple[bytes, np.ndarray, dict]:
    decoder = NativeMain0Decoder(core)
    count = analyzer_bound(samples.shape[0], samples.shape[1])
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    if count > MAXIMUM_OBSERVATIONS:
        result = encode_lapped_stream(
            samples, rate, coefficients_per_frame=budget,
            half_window=int(item["challenger"]["half_window"]),
            band_count=int(item["challenger"]["band_count"]),
            entropy_backend="bounded", transform_backend="fixed",
            density_backend="adaptive", native_analyzer=decoder,
            native_decoder=decoder,
        )
        payload, reconstruction, kind = (
            result.payload, result.reconstruction, "truth-fallback"
        )
        analyzer_invoked = False
    else:
        graph = NativePartialGraph(core)
        candidate = encode_persistent_partial_truth_candidate(
            samples, rate, native_graph=graph, native_decoder=decoder,
            coefficients_per_frame=budget,
            half_window=int(item["challenger"]["half_window"]),
            band_count=int(item["challenger"]["band_count"]),
            language=PersistentPartialLanguage(),
        )
        payload, reconstruction, kind = (
            candidate.selected_payload, candidate.selected_reconstruction,
            candidate.selected_kind,
        )
        analyzer_invoked = True
    if kind == "truth-fallback":
        decoded = decoder.decode_lapped(payload)
        decoded_rate, decoded_samples = decoded.sample_rate, decoded.samples
    else:
        decoded_rate, decoded_samples = decode_causal_basis_truth_candidate(
            payload, native_decoder=decoder
        )
    if decoded_rate != rate or decoded_samples.shape != samples.shape:
        raise RuntimeError("S11 actual decoder shape/rate mismatch")
    if not np.array_equal(decoded_samples, reconstruction):
        raise RuntimeError("S11 encoder reconstruction differs from byte decode")
    report = {
        "coefficient_budget": budget, "selected_kind": kind,
        "complete_bytes": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "decoded_pcm16le_sha256": pcm_sha256(decoded_samples),
        "analyzer_bound": count, "analyzer_invoked": analyzer_invoked,
        "analyzer_maximum_observations": MAXIMUM_OBSERVATIONS,
        "wall_seconds": time.perf_counter() - started_wall,
        "cpu_seconds": time.process_time() - started_cpu,
    }
    return payload, decoded_samples, report


def _retained_manifest(staging: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(item for item in staging.rglob("*") if item.is_file()):
        if path.name in {"receipt.json", "work-request.json"}:
            continue
        rows.append({
            "path": path.relative_to(staging).as_posix(),
            "bytes": path.stat().st_size, "sha256": sha256_file(path),
        })
    return rows


def _run_s11_request(request_path: Path) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    source = Path(request["source_path"])
    rate, samples = read_pcm16_channels(source)
    payload, decoded, report = _encode_s11(
        samples, rate, int(request["budget"]), request["item"],
        Path(request["native_core"]),
    )
    output = Path(request["output"])
    write_fsynced(output / "challenger.resonith", payload)
    write_wav_fsynced(output / "challenger-decoded.wav", rate, decoded)
    write_json_fsynced(output / "s11-report.json", report)
    return 0


def _run_worker(request_path: Path) -> int:
    worker_wall_started, worker_cpu_started = time.perf_counter(), time.process_time()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    staging = request_path.parent
    item = request["item"]
    source = Path(request["source_path"])
    rate, samples = read_pcm16_channels(source)
    if (rate != item["source"]["sample_rate"]
            or list(samples.shape) != [item["source"]["frame_count"],
                                       item["source"]["channel_count"]]
            or pcm_sha256(samples) != item["source"]["pcm16_payload_sha256"]):
        raise RuntimeError("worker source identity mismatch")
    categories = list(item["categories"])
    core = Path(request["native_core"])
    opusenc, opusdec = Path(request["opusenc"]), Path(request["opusdec"])
    manifest_digest = bytes.fromhex(request["manifest_sha256"])
    temporary = staging / "temporary"
    temporary.mkdir()
    staging_ceiling = 8 * GIB if item["id"] == "mozart-full" else 2 * GIB
    opus_wall_limit = max(1800.0, 60.0 * samples.shape[0] / rate)
    opus_wall_used = 0.0
    budgets, candidates = [int(item["challenger"]["coefficients_per_frame"])], []
    for budget_index, budget in enumerate(budgets):
        budget_root = staging / f"budget-{budget}"
        budget_root.mkdir()
        stream = budget_root / "challenger.resonith"
        wav = budget_root / "challenger-decoded.wav"
        s11_request = temporary / f"s11-{budget}.json"
        write_json_fsynced(s11_request, {
            "source_path": str(source), "budget": budget, "item": item,
            "native_core": str(core), "output": str(budget_root),
        })
        s11_resources = run_bounded(
            [sys.executable, str(Path(__file__).resolve()),
             "--s11-request", str(s11_request)],
            max(900.0, 30.0 * samples.shape[0] / rate), 12 * GIB, REPOSITORY,
            staging, staging_ceiling,
        )
        payload = stream.read_bytes()
        decoded_rate, decoded = read_pcm16_channels(wav)
        if decoded_rate != rate or decoded.shape != samples.shape:
            raise RuntimeError("bounded S11 child output mismatch")
        s11 = json.loads((budget_root / "s11-report.json").read_text(encoding="utf-8"))
        (budget_root / "s11-report.json").unlink()
        s11_request.unlink()
        s11["process_resources"] = s11_resources
        s11["metrics"] = compute_metrics(samples, decoded, rate, categories)
        opus_root = budget_root / "opus"
        opus_root.mkdir()
        opus_started = time.perf_counter()
        opus = _run_opus_frontier(
            source, samples, rate, categories, len(payload), item["id"],
            manifest_digest, opusenc, opusdec, temporary, opus_root,
            staging_ceiling,
            time.perf_counter() + max(0.0, opus_wall_limit - opus_wall_used),
        )
        opus_wall_used += time.perf_counter() - opus_started
        if opus_wall_used > opus_wall_limit:
            raise TimeoutError("Opus item wall ceiling exceeded")
        strict = opus["strict_points"]
        non_dominated = bool(strict) and not any(
            dominates(point["metrics"], s11["metrics"]) for point in strict
        )
        candidates.append({
            "s11": s11, "opus": opus,
            "opus_matched": bool(strict),
            "s11_non_dominated": non_dominated if strict else None,
        })
        if budget_index == 0 and non_dominated:
            lower = max(1, budget - 8)
            if lower != budget:
                budgets.append(lower)
    shutil.rmtree(temporary)
    receipt = {
        "schema": RECEIPT_SCHEMA, "status": "PASS",
        "run_identity": request["run_identity"], "item_id": item["id"],
        "order": item["order"], "source_logical_path": item["source"]["path"],
        "source_file_sha256": sha256_file(source),
        "source_pcm16_payload_sha256": pcm_sha256(samples),
        "sample_rate": rate, "frames": samples.shape[0],
        "channels": samples.shape[1], "categories": categories,
        "candidates": candidates, "retained_files": _retained_manifest(staging),
        "worker_self_timing": {
            "wall_seconds": time.perf_counter() - worker_wall_started,
            "cpu_seconds": time.process_time() - worker_cpu_started,
        },
        "directory_fsync": "not available portably on Windows",
    }
    write_json_fsynced(staging / "receipt.json", receipt)
    return 0


def _resolve_source(item: dict[str, object], roots: dict[str, Path]) -> Path:
    logical = Path(item["source"]["path"])
    if not logical.parts or logical.parts[0] not in roots:
        raise ValueError("unmapped logical source root")
    return roots[logical.parts[0]].joinpath(*logical.parts[1:]).resolve()


def load_and_validate_manifest(path: Path, roots: dict[str, Path]) -> tuple[dict, dict[str, Path]]:
    if sha256_file(path) != MANIFEST_SHA256:
        raise RuntimeError("registered manifest hash mismatch")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    items = manifest.get("items", [])
    if (manifest.get("schema") != MANIFEST_SCHEMA
            or manifest.get("item_count") != 19 or len(items) != 19
            or [row.get("order") for row in items] != list(range(1, 20))
            or len({row.get("id") for row in items}) != 19
            or items[0].get("id") != "mozart-full"):
        raise RuntimeError("registered manifest structure/order mismatch")
    paths = {}
    for item in items:
        source = _resolve_source(item, roots)
        if not source.is_file() or sha256_file(source) != item["source"]["file_sha256"]:
            raise RuntimeError(f"source file identity mismatch: {item['id']}")
        rate, samples = read_pcm16_channels(source)
        if (rate != item["source"]["sample_rate"]
                or samples.shape != (item["source"]["frame_count"],
                                     item["source"]["channel_count"])
                or pcm_sha256(samples) != item["source"]["pcm16_payload_sha256"]):
            raise RuntimeError(f"source PCM identity mismatch: {item['id']}")
        paths[item["id"]] = source
    return manifest, paths


def _identity_files(arguments) -> dict[str, Path]:
    return {
        "predictor": REPOSITORY / "reference/maf_p0/persistent_partial_field.py",
        "python_wrapper": REPOSITORY / "reference/maf_p0/native_core.py",
        "native_core": arguments.native_core,
        "opusenc": arguments.opusenc, "opusdec": arguments.opusdec,
        "objective_metrics": REPOSITORY / "experiments/objective_audio_metrics.py",
        "perceptual_metrics": REPOSITORY / "reference/maf_p0/perceptual_metrics.py",
        "runner": Path(__file__).resolve(),
        "metric_helper": REPOSITORY / "experiments/r216_s12_metrics.py",
        "focused_tests": REPOSITORY / "tests/test_opus_max_effort.py",
        "preflight": REPOSITORY / "docs/reviews/R216_S12_REGISTERED_COMPARISON_PREFLIGHT_2026-08-02.md",
        "r117_complete_report": arguments.r117_complete_report,
        "r117_r111_report": arguments.r117_r111_report,
        "prepared_manifest": arguments.prepared_root / "prepared-manifest.json",
        "real_music_corpus": REPOSITORY / "experiments/real_music_corpus.json",
    }


def _validate_identities(arguments, files: dict[str, Path]) -> dict[str, str]:
    expected = {
        "predictor": EXPECTED_PREDICTOR_SHA256,
        "python_wrapper": EXPECTED_WRAPPER_SHA256,
        "native_core": EXPECTED_CORE_SHA256,
        "opusenc": EXPECTED_OPUSENC_SHA256, "opusdec": EXPECTED_OPUSDEC_SHA256,
        "objective_metrics": EXPECTED_OBJECTIVE_SHA256,
        "perceptual_metrics": EXPECTED_PERCEPTUAL_SHA256,
        "runner": arguments.audited_runner_sha256,
        "metric_helper": EXPECTED_HELPER_SHA256,
        "focused_tests": EXPECTED_TESTS_SHA256,
        "preflight": EXPECTED_PREFLIGHT_SHA256,
        "r117_complete_report": "cc906ac76c0bbd8acb3d4303818071c608e187eb0d152e075dd0986acfd98665",
        "r117_r111_report": "51709d0e18184f9d86b9397e8e282e1315ca6aa50304c3d86dffa719ca492fe8",
        "prepared_manifest": "2af905648ec33b092d172fb8868abcdb4f09db91615a9e675cacd4ddc54930f3",
        "real_music_corpus": "6eb7e6e6e330cf7d3890688ab5d67a0180c8be0403589e44dfe221b118f1ab9b",
    }
    hashes = {name: sha256_file(path.resolve()) for name, path in files.items()}
    for name, digest in expected.items():
        if hashes.get(name) != digest:
            raise RuntimeError(f"frozen identity mismatch: {name}")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if revision != EXPECTED_SOURCE_REVISION:
        raise RuntimeError("frozen source revision mismatch")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--",
         "reference/maf_p0", "experiments/objective_audio_metrics.py"],
        cwd=REPOSITORY, capture_output=True, text=True,
    )
    if dirty.returncode != 0 or dirty.stdout:
        raise RuntimeError("dirty imported tracked implementation")
    help_text = subprocess.run(
        [str(arguments.opusenc), "--help"], check=True,
        capture_output=True, text=True, timeout=15,
    ).stdout
    for option in ("--serial", "--set-ctl-int", "--no-phase-inv",
                   "--discard-pictures", "--padding"):
        if option not in help_text:
            raise RuntimeError(f"opusenc lacks frozen option {option}")
    encoder_process = subprocess.run(
        [str(arguments.opusenc), "--version"], check=True,
        capture_output=True, text=True, timeout=15,
    )
    decoder_process = subprocess.run(
        [str(arguments.opusdec), "--version"], check=True,
        capture_output=True, text=True, timeout=15,
    )
    encoder_version = encoder_process.stdout + encoder_process.stderr
    decoder_version = decoder_process.stdout + decoder_process.stderr
    if "opus-tools 0.2" not in encoder_version or "libopus 1.6.1" not in encoder_version:
        raise RuntimeError("unexpected opusenc version")
    if "opus-tools 0.2" not in decoder_version or "libopus 1.6.1" not in decoder_version:
        raise RuntimeError("unexpected opusdec version")
    versions = {
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": metadata.version("scipy"),
        "pystoi": metadata.version("pystoi"),
    }
    if versions != {
        "python": "3.14.6", "numpy": "2.5.1",
        "scipy": "1.18.0", "pystoi": "0.4.1",
    }:
        raise RuntimeError(f"frozen dependency version mismatch: {versions}")
    return hashes


def _verify_receipt(final: Path, run_identity: str, item: dict) -> dict:
    receipt_path = final / "receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("final item has no receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("schema") != RECEIPT_SCHEMA
            or receipt.get("status") != "PASS"
            or receipt.get("run_identity") != run_identity
            or receipt.get("item_id") != item["id"]):
        raise RuntimeError("stale or corrupt final receipt")
    retained_rows = receipt.get("retained_files", [])
    retained_names = {row["path"] for row in retained_rows}
    actual_names = {
        path.relative_to(final).as_posix()
        for path in final.rglob("*")
        if path.is_file() and path.name not in {"receipt.json", "work-request.json"}
    }
    if retained_names != actual_names:
        raise RuntimeError("retained evidence file set drift")
    for row in retained_rows:
        path = final / row["path"]
        if (not path.is_file() or path.stat().st_size != row["bytes"]
                or sha256_file(path) != row["sha256"]):
            raise RuntimeError("retained evidence drift")
    return receipt


def _aggregate(root: Path, manifest: dict, run_identity: str,
               run_material: dict[str, object]) -> None:
    receipts = [
        _verify_receipt(root / item["id"], run_identity, item)
        for item in manifest["items"]
    ]
    rows = []
    for receipt in receipts:
        primary = receipt["candidates"][0]
        rows.append({
            "id": receipt["item_id"],
            "resonith_bytes": primary["s11"]["complete_bytes"],
            "resonith_kind": primary["s11"]["selected_kind"],
            "opus_strict_points": primary["opus"]["strict_point_count"],
            "opus_pareto_points": primary["opus"]["pareto_point_count"],
            "resonith_non_dominated": primary["s11_non_dominated"],
            "refinement_count": len(receipt["candidates"]) - 1,
        })
    report = {
        "schema": "resonith-r216-s12-aggregate-1", "status": "PASS",
        "scope": "R-215 S11 versus official maximum-effort Opus only",
        "run_identity": run_identity, "run_material": run_material,
        "item_count": len(rows), "rows": rows,
    }
    replace_json_fsynced(root / "aggregate.json", report)
    lines = [
        "# R-216 S12 Resonith versus maximum-effort Opus", "",
        f"Run identity: `{run_identity}`", "",
        "This report compares R-215 S11 only with official Opus 1.6.1. It does not compare a preceding Resonith generation.", "",
        "| Item | Resonith bytes | Path | Strict Opus | Opus Pareto | Resonith non-dominated |", "|---|---:|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['resonith_bytes']} | {row['resonith_kind']} | "
            f"{row['opus_strict_points']} | {row['opus_pareto_points']} | "
            f"{row['resonith_non_dominated']} |"
        )
    lines.extend(("", "All numbers come from actual complete streams and decoded PCM. Objective metrics do not replace blinded listening.", ""))
    temporary = root / f".report.{uuid.uuid4().hex}.tmp"
    write_fsynced(temporary, "\n".join(lines).encode("utf-8"))
    os.replace(temporary, root / "REPORT.md")


def _run_controller(arguments) -> int:
    if shutil.disk_usage("G:\\").free < 10 * GIB:
        raise RuntimeError("S12 requires at least 10 GiB free on G:")
    roots = {
        "orkela-public-benchmark": arguments.public_benchmark_root,
        "orkela-emotional-piano-8s": arguments.emotional_piano_root,
        "prepared-r111": arguments.prepared_root,
    }
    manifest, source_paths = load_and_validate_manifest(arguments.manifest, roots)
    files = _identity_files(arguments)
    identities = _validate_identities(arguments, files)
    run_material = {
        "schema": RUNNER_SCHEMA, "manifest_sha256": MANIFEST_SHA256,
        "identities": identities, "python": sys.version,
        "numpy": np.__version__, "platform": platform.platform(),
        "configuration": "frozen R-216 S12 preflight V4",
        "execution_devices": {
            "s11": "CPU Python analysis plus native CPU Golden Core",
            "opus": "official CPU opusenc and opusdec",
            "gpu_used": False,
        },
    }
    run_identity = hashlib.sha256(_json_bytes(run_material)).hexdigest()
    root = arguments.output.resolve()
    if os.name == "nt" and root.drive.upper() != "G:":
        raise RuntimeError("S12 output must be on the audited G: volume")
    root_existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    for staging in root.glob(".*.staging.*"):
        quarantine = root / f"quarantine-{staging.name[1:]}-{uuid.uuid4().hex}"
        os.replace(staging, quarantine)
        raise RuntimeError(f"leftover staging quarantined: {quarantine.name}")
    index_path = root / "run-index.json"
    if root_existed and not index_path.exists() and any(root.iterdir()):
        raise RuntimeError("nonempty output root has no S12 run index")
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if index.get("schema") != RUN_SCHEMA or index.get("run_identity") != run_identity:
            raise RuntimeError("output root belongs to a different run")
    else:
        index = {"schema": RUN_SCHEMA, "run_identity": run_identity,
                 "completed_item_ids": [], "worker_resources": {},
                 "run_started_unix": time.time()}
        replace_json_fsynced(index_path, index)
    if not isinstance(index.get("run_started_unix"), (int, float)):
        raise RuntimeError("run index lacks cumulative wall origin")
    for item in manifest["items"]:
        remaining_run_wall = 12 * 3600.0 - (time.time() - index["run_started_unix"])
        if remaining_run_wall <= 0:
            raise TimeoutError("complete S12 wall ceiling exceeded")
        if _tree_bytes(root) > 12 * GIB:
            raise RuntimeError("retained S12 root ceiling exceeded")
        final = root / item["id"]
        if final.exists():
            recovered = _verify_receipt(final, run_identity, item)
            if item["id"] not in index["completed_item_ids"]:
                index["completed_item_ids"].append(item["id"])
                index.setdefault("worker_resources", {})[item["id"]] = {
                    **recovered["worker_resources"],
                    "index_recovery": "verified-final-after-rename",
                }
                replace_json_fsynced(index_path, index)
            continue
        if item["id"] in index["completed_item_ids"]:
            raise RuntimeError("run index references a missing item")
        staging = root / f".{item['id']}.staging.{uuid.uuid4().hex}"
        staging.mkdir()
        request = {
            "schema": "resonith-r216-s12-work-request-1",
            "run_identity": run_identity, "manifest_sha256": MANIFEST_SHA256,
            "item": item, "source_path": str(source_paths[item["id"]]),
            "native_core": str(arguments.native_core.resolve()),
            "opusenc": str(arguments.opusenc.resolve()),
            "opusdec": str(arguments.opusdec.resolve()),
        }
        request_path = staging / "work-request.json"
        write_json_fsynced(request_path, request)
        duration = float(item["source"]["duration_seconds"])
        ceiling = 8 * GIB if item["id"] == "mozart-full" else 2 * GIB
        retained_before = _tree_bytes(root) - _tree_bytes(staging)
        ceiling = min(ceiling, 12 * GIB - retained_before)
        if ceiling <= 0:
            raise RuntimeError("retained S12 root ceiling exhausted")
        command = [sys.executable, str(Path(__file__).resolve()),
                   "--worker-request", str(request_path)]
        worker_resources = run_bounded(
            command, min(remaining_run_wall, max(3600.0, 180.0 * duration)),
            12 * GIB, REPOSITORY, staging, ceiling,
        )
        receipt_path = staging / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["worker_resources"] = worker_resources
        replace_json_fsynced(receipt_path, receipt)
        if os.environ.get("RESONITH_R216_INJECT_BEFORE_RENAME") == item["id"]:
            raise RuntimeError("injected pre-rename failure")
        _verify_receipt(staging, run_identity, item)
        retained = _tree_bytes(staging)
        if retained > ceiling:
            raise RuntimeError("item staging ceiling exceeded")
        request_path.unlink()
        os.replace(staging, final)
        index["completed_item_ids"].append(item["id"])
        index.setdefault("worker_resources", {})[item["id"]] = worker_resources
        replace_json_fsynced(index_path, index)
    _aggregate(root, manifest, run_identity, run_material)
    if sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) > 12 * GIB:
        raise RuntimeError("retained S12 root ceiling exceeded")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-request", type=Path)
    parser.add_argument("--s11-request", type=Path)
    parser.add_argument("--manifest", type=Path,
                        default=REPOSITORY / "experiments/fixtures/r216_s12_registered_manifest.json")
    parser.add_argument("--public-benchmark-root", type=Path)
    parser.add_argument("--emotional-piano-root", type=Path)
    parser.add_argument("--prepared-root", type=Path)
    parser.add_argument("--r117-complete-report", type=Path)
    parser.add_argument("--r117-r111-report", type=Path)
    parser.add_argument("--native-core", type=Path)
    parser.add_argument("--opusenc", type=Path)
    parser.add_argument("--opusdec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audited-runner-sha256")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.s11_request is not None:
        return _run_s11_request(arguments.s11_request.resolve())
    if arguments.worker_request is not None:
        return _run_worker(arguments.worker_request.resolve())
    required = (
        "public_benchmark_root", "emotional_piano_root", "prepared_root",
        "r117_complete_report", "r117_r111_report", "native_core",
        "opusenc", "opusdec", "output",
        "audited_runner_sha256",
    )
    missing = [name for name in required if getattr(arguments, name) is None]
    if missing:
        raise ValueError(f"missing controller arguments: {', '.join(missing)}")
    return _run_controller(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
