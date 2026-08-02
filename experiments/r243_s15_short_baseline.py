"""Atomically capture bounded R-243 Phase-A evidence; this changes no codec code."""
from __future__ import annotations
import argparse
import cProfile
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import platform
import pstats
import secrets
import shutil
import statistics
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace
PROCESS_CPU_START = time.process_time()
sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "artifacts"
RESULT_ROOT = PROJECT_ROOT / "experiments/results"
FINAL_OUTPUT = ARTIFACT_ROOT / "r243-s15-short-baseline-prechange"
STAGING_OUTPUT = ARTIFACT_ROOT / "r243-s15-short-baseline-prechange.staging"
FAILURE_OUTPUT = ARTIFACT_ROOT / "r243-s15-short-baseline-prechange-failure.json"
FUTURE_SUMMARY = RESULT_ROOT / "r243_s15_short_baseline_prechange.json"
ENVIRONMENT = {name: "1" for name in (
    "PYTHONDONTWRITEBYTECODE", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
ENVIRONMENT["PYTHONHASHSEED"] = "0"
PAIR_ORDER = (("legacy", "rescored"), ("rescored", "legacy"), ("legacy", "rescored"))
INTERVALS = (
    (2048, 64, 192, 193), (2048, 64, 193, 209), (2048, 64, 255, 319), (2048, 64, 256, 320),
    (2048, 64, 511, 1022), (40000, 65, 29184, 29696), (300, 64, 287, 300), (32768, 8192, 16383, 16895),
)
LAW_FAMILIES = ((-115,), (0,), (115,),
                (-115, 103, -91, 79, -67, 55, -43, 31, -19, 7, 11, -23, 35, -47, 59, -71))
PATTERNS = ("zero", "alternating", "lcg", "clipping")
TIMING_WALL_LIMIT, PROFILE_WALL_LIMIT = 300.0, 180.0
WORKER_CPU_LIMIT, PROFILE_CPU_LIMIT = 300.0, 180.0
CONTROLLER_WALL_LIMIT = 510.0
MEMORY_LIMIT, RETAINED_LIMIT, LOG_LIMIT = 512 << 20, 32 << 20, 1 << 20
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()
def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
def _atomic_json(path: Path, value: object, *, exclusive: bool = True) -> None:
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if path.exists() and exclusive:
        raise FileExistsError(f"refusing to replace {path}")
    if temporary.exists():
        raise FileExistsError(f"temporary path exists: {temporary}")
    payload = _canonical_bytes(value)
    try:
        with temporary.open("xb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        if exclusive and path.exists():
            raise FileExistsError(f"refusing to replace {path}")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
def _is_reparse(path: Path) -> bool:
    if not path.exists():
        return False
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & 0x400)
def _exact_parent(path: Path, parent: Path) -> None:
    if path.resolve(strict=False).parent != parent.resolve(strict=True):
        raise RuntimeError(f"path escapes exact parent: {path}")
    if _is_reparse(parent) or _is_reparse(path):
        raise RuntimeError(f"reparse point is forbidden: {path}")
def _safe_remove_staging() -> str | None:
    try:
        _exact_parent(STAGING_OUTPUT, ARTIFACT_ROOT)
        if STAGING_OUTPUT.exists():
            if STAGING_OUTPUT.name != "r243-s15-short-baseline-prechange.staging":
                raise RuntimeError("unexpected staging name")
            shutil.rmtree(STAGING_OUTPUT)
        return None
    except BaseException as error:
        return f"{type(error).__name__}: {error}"
def _read_authority(path: Path, expected_sha256: str, *, check_git: bool) -> dict:
    resolved = path.resolve(strict=True)
    if _sha256(resolved) != expected_sha256.lower():
        raise RuntimeError("R-243 authority SHA-256 mismatch")
    authority = json.loads(resolved.read_text(encoding="utf-8"))
    if authority.get("schema") != "resonith-r243-s15-phase-a-authority-1":
        raise RuntimeError("R-243 authority schema mismatch")
    if Path(sys.executable).resolve(strict=True) != Path(authority["python"]["path"]).resolve(strict=True):
        raise RuntimeError("R-243 Python executable path mismatch")
    if platform.python_version() != authority["python"]["version"]:
        raise RuntimeError("R-243 Python version mismatch")
    if _sha256(Path(sys.executable).resolve(strict=True)) != authority["python"]["sha256"]:
        raise RuntimeError("R-243 Python executable hash mismatch")
    if platform.version() != authority["runtime"]["windows_build"]:
        raise RuntimeError("R-243 Windows build mismatch")
    for name, expected in authority["environment"].items():
        if os.environ.get(name) != expected or ENVIRONMENT.get(name) != expected:
            raise RuntimeError(f"R-243 environment mismatch: {name}")
    if not sys.dont_write_bytecode or sys.flags.optimize != 0 or os.name != "nt":
        raise RuntimeError("R-243 interpreter mode mismatch")
    for name, record in authority["files"].items():
        candidate = Path(record["path"])
        candidate = candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
        candidate = candidate.resolve(strict=True)
        if _is_reparse(candidate) or _sha256(candidate) != record["sha256"]:
            raise RuntimeError(f"R-243 authority file drift: {name}")
    runner = Path(__file__).resolve(strict=True)
    if runner.stat().st_size != authority["runner"]["bytes"]:
        raise RuntimeError("R-243 runner byte count mismatch")
    if len(runner.read_text(encoding="utf-8").splitlines()) != authority["runner"]["lines"]:
        raise RuntimeError("R-243 runner line count mismatch")
    if runner.stat().st_size > 65536 or authority["runner"]["lines"] > 600:
        raise RuntimeError("R-243 runner exceeds its audited source bound")
    if check_git:
        observed = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if observed != authority["git_commit"]:
            raise RuntimeError("R-243 Git commit drift")
    return authority
def _load_codec(authority: dict):
    sys.path[:0] = [str(PROJECT_ROOT), str(PROJECT_ROOT / "reference"), str(PROJECT_ROOT / "experiments")]
    gate = importlib.import_module("r232_s15_source_filter_gate")
    base = authority["files"]["base_authority"]
    base_authority, files = gate._validate_authority(
        (PROJECT_ROOT / base["path"]).resolve(strict=True), base["sha256"]
    )
    widened = dict(base_authority)
    widened["local_modules"] = dict(base_authority["local_modules"])
    widened["local_modules"][Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix()] = _sha256(Path(__file__))
    gate._load_runtime(widened)
    oracle = importlib.import_module("maf_p0.maf_source_filter_oracle")
    if gate.np.__version__ != authority["runtime"]["numpy"]:
        raise RuntimeError("R-243 NumPy version mismatch")
    return gate, oracle, files
def _normalize(value):
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value
def _identity(encoded, gate, source, sample_rate: int) -> tuple[dict, object]:
    decoded_rate, decoded = gate.decode_maf_source_filter_stream(encoded.payload)
    if decoded_rate != sample_rate or not gate.np.array_equal(decoded, encoded.reconstruction):
        raise RuntimeError("R-243 independent decode mismatch")
    report = _normalize(encoded.report)
    report_bytes = _canonical_bytes(report)
    pcm = decoded.astype("<i2", copy=False).tobytes()
    counters = {}
    def visit(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                here = f"{path}.{key}" if path else str(key)
                if isinstance(child, (int, float)) and ("candidate" in key or "subframe" in key):
                    counters[here] = child
                visit(child, here)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
    visit(report)
    error = source.astype(gate.np.int64) - decoded.astype(gate.np.int64)
    record = {
        "bytes": len(encoded.payload),
        "candidate_subframe_counters": counters,
        "decoded_pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "stream_sha256": hashlib.sha256(encoded.payload).hexdigest(),
        "waveform_sse": int(error @ error),
    }
    return record, (encoded.payload, pcm, report_bytes)
def _timed_encode(gate, analysis, configuration, rescoring: bool):
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    encoded = gate._encode_arm(analysis, configuration, rescoring)
    wall_ns = time.perf_counter_ns() - wall_start
    cpu_ns = time.process_time_ns() - cpu_start
    return encoded, {"cpu_seconds": cpu_ns / 1e9, "wall_seconds": wall_ns / 1e9}
def _lcg(np, count: int):
    state = 0x00524243
    values = np.empty(count, dtype=np.int16)
    for index in range(count):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        values[index] = ((state >> 16) & 0xFFFF) - 32768
    return values
def _pattern(np, name: str, count: int, start: int, stop: int):
    alternate = np.where(np.arange(count) % 2 == 0, -32768, 32767).astype(np.int16)
    if name == "zero":
        source = np.zeros(count, dtype=np.int16)
        committed = np.zeros(count, dtype=np.int64)
        raw = np.zeros(stop - start, dtype=np.int64)
    elif name == "alternating":
        source = alternate
        committed = alternate.astype(np.int64)
        raw = alternate[start:stop].astype(np.int64)
    elif name == "lcg":
        source = _lcg(np, count)
        committed = source.astype(np.int64)
        raw = source[start:stop].astype(np.int64)
    else:
        source = alternate
        committed = alternate.astype(np.int64)
        raw = np.full(stop - start, 32767, dtype=np.int64)
    return source, committed, raw
def _golden_vectors(gate, oracle, destination: Path) -> dict:
    cases = []
    for interval_index, (source_size, block_size, start, stop) in enumerate(INTERVALS):
        law_count = (source_size + block_size - 1) // block_size
        for law_index, base in enumerate(LAW_FAMILIES):
            laws = []
            for block in range(law_count):
                first = -115 + ((base[0] + 115 + 17 * block) % 231)
                laws.append(oracle.FilterLaw((first, *base[1:])))
            for pattern_index, pattern in enumerate(PATTERNS):
                source, committed, raw = _pattern(gate.np, pattern, source_size, start, stop)
                analysis = SimpleNamespace(source=source, block_size=block_size, filter_laws=tuple(laws))
                desired = oracle._desired_short_excitation_target(analysis, start, stop)
                output, clipping = oracle._synthesize_short_filter_candidate(
                    analysis, raw, committed, start, stop
                )
                first_block = start // block_size
                last_block = min(law_count - 1, (stop - 1) // block_size)
                touched = [
                    {"absolute_block": block, "lpc_q14": list(oracle._lpc_q14(laws[block]))}
                    for block in range(first_block, last_block + 1)
                ]
                case = {
                    "block_size": block_size,
                    "candidate_output": [int(value) for value in output],
                    "clipping_count": int(clipping),
                    "committed_output_dtype": str(committed.dtype),
                    "desired_excitation": [int(value) for value in desired],
                    "id": f"i{interval_index}-l{law_index}-p{pattern_index}",
                    "law_family": list(base),
                    "pattern": pattern,
                    "raw_excitation_dtype": str(raw.dtype),
                    "source_dtype": str(source.dtype),
                    "source_size": source_size,
                    "start": start,
                    "stop": stop,
                    "touched_lpc_q14": touched,
                }
                if (source_size, block_size, start, stop) == (40000, 65, 29184, 29696):
                    case.update({"subframe_index": 57, "subframe_size": 512})
                cases.append(case)
    payload = {"case_count": len(cases), "cases": cases, "schema": "resonith-r243-golden-1"}
    expected_ids = [f"i{i}-l{law}-p{pattern}" for i in range(8) for law in range(4) for pattern in range(4)]
    observed_ids = [case["id"] for case in cases]
    maximum = [case for case in cases if case.get("subframe_index") == 57]
    if len(cases) != 128 or observed_ids != expected_ids or len(set(observed_ids)) != 128:
        raise RuntimeError("R-243 golden cardinality/order mismatch")
    if len(maximum) != 16 or any(len(case["touched_lpc_q14"]) != 9 for case in maximum):
        raise RuntimeError("R-243 golden nine-law witness mismatch")
    if any(
        case["source_dtype"] != "int16"
        or case["committed_output_dtype"] != "int64"
        or case["raw_excitation_dtype"] != "int64"
        for case in cases
    ):
        raise RuntimeError("R-243 golden dtype mismatch")
    destination.write_bytes(_canonical_bytes(payload))
    if json.loads(destination.read_text(encoding="utf-8")) != payload:
        raise RuntimeError("R-243 golden readback mismatch")
    return {"case_count": len(cases), "sha256": _sha256(destination)}
def _timing_worker(authority_path: Path, authority_sha: str, output: Path) -> None:
    authority = _read_authority(authority_path, authority_sha, check_git=False)
    gate, oracle, files = _load_codec(authority)
    output.mkdir()
    source_path = Path(authority["files"]["source"]["path"])
    sample_rate, channels = gate.read_pcm16_channels(source_path)
    if sample_rate != 16000 or channels.shape != (93680, 1):
        raise RuntimeError("R-243 source metadata mismatch")
    source = channels[:, 0]
    configuration = json.loads(files["configuration"].read_text(encoding="utf-8"))
    analysis_cpu = time.process_time_ns()
    analysis_wall = time.perf_counter_ns()
    analysis = gate._analyze(source, sample_rate, configuration, files["native_core"])
    analysis_record = {
        "cpu_seconds": (time.process_time_ns() - analysis_cpu) / 1e9,
        "wall_seconds": (time.perf_counter_ns() - analysis_wall) / 1e9,
    }
    identities = {"legacy": [], "rescored": []}
    final_outputs = {}
    for label, rescoring in (("legacy", False), ("rescored", True)):
        encoded = gate._encode_arm(analysis, configuration, rescoring)
        identity, retained = _identity(encoded, gate, source, sample_rate)
        identities[label].append(identity)
        final_outputs[label] = retained
    trials = []
    for pair_index, pair in enumerate(PAIR_ORDER):
        for label in pair:
            encoded, elapsed = _timed_encode(gate, analysis, configuration, label == "rescored")
            identity, retained = _identity(encoded, gate, source, sample_rate)
            identities[label].append(identity)
            final_outputs[label] = retained
            trials.append({"arm": label, "pair_index": pair_index, **elapsed})
    for label, records in identities.items():
        frozen = [{key: value for key, value in record.items()} for record in records]
        if any(record != frozen[0] for record in frozen[1:]):
            raise RuntimeError(f"R-243 nondeterministic {label} identity")
        payload, pcm, report = final_outputs[label]
        (output / f"{label}.resonith").write_bytes(payload)
        (output / f"{label}-decoded.pcm16le").write_bytes(pcm)
        (output / f"{label}-report.json").write_bytes(report)
    medians = {}
    for label in ("legacy", "rescored"):
        selected = [trial for trial in trials if trial["arm"] == label]
        medians[label] = {
            "cpu_seconds": statistics.median(item["cpu_seconds"] for item in selected),
            "wall_seconds": statistics.median(item["wall_seconds"] for item in selected),
        }
    golden = _golden_vectors(gate, oracle, output / "golden-vectors.json")
    _read_authority(authority_path, authority_sha, check_git=False)
    source_after = _sha256(source_path)
    if source_after != authority["files"]["source"]["sha256"]:
        raise RuntimeError("R-243 source drifted during timing worker")
    report = {
        "analysis": analysis_record,
        "golden": golden,
        "identities": {label: records[0] for label, records in identities.items()},
        "medians": medians,
        "pair_order": [list(pair) for pair in PAIR_ORDER],
        "schema": "resonith-r243-s15-timing-worker-1",
        "source_sha256_after": source_after,
        "trials": trials,
        "worker_process_cpu_seconds_proxy": time.process_time() - PROCESS_CPU_START,
    }
    _atomic_json(output / "report.json", report)
def _profile_worker(authority_path: Path, authority_sha: str, output: Path) -> None:
    authority = _read_authority(authority_path, authority_sha, check_git=False)
    gate, _, files = _load_codec(authority)
    output.mkdir()
    source_path = Path(authority["files"]["source"]["path"])
    sample_rate, channels = gate.read_pcm16_channels(source_path)
    configuration = json.loads(files["configuration"].read_text(encoding="utf-8"))
    analysis = gate._analyze(channels[:, 0], sample_rate, configuration, files["native_core"])
    profile_path = output / "rescored.prof"
    profiler = cProfile.Profile()
    profiler.enable()
    encoded = gate._encode_arm(analysis, configuration, True)
    profiler.disable()
    profiler.dump_stats(profile_path)
    identity, retained = _identity(encoded, gate, channels[:, 0], sample_rate)
    (output / "rescored.resonith").write_bytes(retained[0])
    stats = pstats.Stats(profiler)
    for name, sort_key in (("cumulative.txt", "cumulative"), ("self.txt", "tottime")):
        stream = io.StringIO()
        pstats.Stats(profile_path, stream=stream).strip_dirs().sort_stats(sort_key).print_stats()
        (output / name).write_text(stream.getvalue(), encoding="utf-8", newline="\n")
    selected = {}
    for key, value in stats.stats.items():
        filename, line, function = key
        if function in {"_lpc_q14", "encode_maf_source_filter_analysis"}:
            primitive, total, self_time, cumulative, _ = value
            selected[function] = {"cumulative_seconds": cumulative, "filename": filename, "line": line,
                                  "primitive_calls": primitive, "self_seconds": self_time, "total_calls": total}
    if set(selected) != {"_lpc_q14", "encode_maf_source_filter_analysis"}:
        raise RuntimeError("R-243 required profile functions missing")
    ratio = selected["_lpc_q14"]["cumulative_seconds"] / selected["encode_maf_source_filter_analysis"]["cumulative_seconds"]
    _read_authority(authority_path, authority_sha, check_git=False)
    source_after = _sha256(source_path)
    if source_after != authority["files"]["source"]["sha256"]:
        raise RuntimeError("R-243 source drifted during profile worker")
    _atomic_json(output / "report.json", {
        "identity": identity, "lpc_to_encode_cumulative_ratio": ratio, "profile_functions": selected,
        "profile_sha256": _sha256(profile_path), "schema": "resonith-r243-s15-profile-worker-1",
        "source_sha256_after": source_after,
        "worker_process_cpu_seconds_proxy": time.process_time() - PROCESS_CPU_START})
def _manifest(root: Path) -> list[dict]:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "receipt.json"):
        records.append({"bytes": path.stat().st_size, "path": path.relative_to(root).as_posix(),
                        "sha256": _sha256(path)})
    return records
def _validate_golden(path: Path, expected_sha256: str) -> None:
    if _sha256(path) != expected_sha256:
        raise RuntimeError("R-243 golden hash mismatch")
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    cases = payload.get("cases", [])
    expected_ids = [f"i{i}-l{law}-p{pattern}" for i in range(8) for law in range(4) for pattern in range(4)]
    maximum = [case for case in cases if case.get("subframe_index") == 57]
    if payload.get("schema") != "resonith-r243-golden-1" or payload.get("case_count") != 128:
        raise RuntimeError("R-243 golden schema/count mismatch")
    if len(cases) != 128 or [case.get("id") for case in cases] != expected_ids:
        raise RuntimeError("R-243 golden identity/order mismatch")
    if len(maximum) != 16 or any(
        case.get("subframe_size") != 512 or len(case.get("touched_lpc_q14", [])) != 9
        for case in maximum
    ):
        raise RuntimeError("R-243 golden maximum witness mismatch")
    if any(
        (case.get("source_dtype"), case.get("committed_output_dtype"), case.get("raw_excitation_dtype"))
        != ("int16", "int64", "int64")
        for case in cases
    ):
        raise RuntimeError("R-243 golden dtype readback mismatch")
    if raw != _canonical_bytes(payload):
        raise RuntimeError("R-243 golden serialization is not canonical")
def _worker_request(path: Path, expected_sha256: str) -> dict:
    _exact_parent(STAGING_OUTPUT, ARTIFACT_ROOT)
    if not STAGING_OUTPUT.is_dir() or _is_reparse(STAGING_OUTPUT):
        raise RuntimeError("R-243 worker staging ownership invalid")
    _exact_parent(path, STAGING_OUTPUT)
    if _sha256(path.resolve(strict=True)) != expected_sha256.lower():
        raise RuntimeError("R-243 worker request hash mismatch")
    request = json.loads(path.read_text(encoding="utf-8"))
    mode = request.get("mode")
    if request.get("schema") != "resonith-r243-worker-request-1" or mode not in {"timing", "profile"}:
        raise RuntimeError("R-243 worker request schema/mode mismatch")
    if path.resolve() != (STAGING_OUTPUT / f"{mode}-request.json").resolve():
        raise RuntimeError("R-243 worker request path mismatch")
    if request.get("parent_pid") != os.getppid() or len(request.get("nonce", "")) != 64:
        raise RuntimeError("R-243 worker parent/nonce mismatch")
    output = Path(request["output"]).resolve(strict=False)
    if output != (STAGING_OUTPUT / mode).resolve(strict=False) or output.exists():
        raise RuntimeError("R-243 worker output path mismatch")
    consumed = path.with_suffix(".consumed")
    with consumed.open("xb") as destination:
        destination.write(expected_sha256.lower().encode("ascii") + b"\n")
        destination.flush()
        os.fsync(destination.fileno())
    return request
def _install_hard_cpu_job(gate, cpu_limit: float):
    original = gate._create_job
    def create_job(kernel, memory_limit=MEMORY_LIMIT):
        job = kernel.CreateJobObjectW(None, None)
        if not job:
            gate._raise_last("CreateJobObjectW failed")
        limits = gate._JobExtendedLimit()
        limits.BasicLimitInformation.PerProcessUserTimeLimit = int(cpu_limit * 10_000_000)
        limits.BasicLimitInformation.LimitFlags = 0x2 | 0x8 | 0x100 | 0x200 | 0x2000
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        limits.ProcessMemoryLimit = memory_limit
        limits.JobMemoryLimit = memory_limit
        if not kernel.SetInformationJobObject(job, 9, gate.ctypes.byref(limits), gate.ctypes.sizeof(limits)):
            kernel.CloseHandle(job)
            gate._raise_last("SetInformationJobObject failed")
        return int(job)
    gate._create_job = create_job
    return original
def _copy_provenance(authority_path: Path, authority: dict) -> None:
    destination = STAGING_OUTPUT / "provenance"
    destination.mkdir()
    records = {
        "authority.json": authority_path.resolve(strict=True),
        "preflight.md": (PROJECT_ROOT / authority["files"]["preflight"]["path"]).resolve(strict=True),
        "preclearance-audit.md": (PROJECT_ROOT / authority["files"]["audit"]["path"]).resolve(strict=True), "remediation.md": (PROJECT_ROOT / authority["files"]["remediation"]["path"]).resolve(strict=True),
        "runner.py": Path(__file__).resolve(strict=True),
    }
    for name, source in records.items():
        shutil.copyfile(source, destination / name)
        if _sha256(destination / name) != _sha256(source):
            raise RuntimeError(f"R-243 provenance copy mismatch: {name}")
def _controller(authority_path: Path, authority_sha: str, output: Path) -> None:
    started = time.perf_counter()
    authority = _read_authority(authority_path, authority_sha, check_git=True)
    if output.resolve(strict=False) != FINAL_OUTPUT.resolve(strict=False):
        raise RuntimeError("R-243 output differs from the authorized exact path")
    for path, parent in ((FINAL_OUTPUT, ARTIFACT_ROOT), (STAGING_OUTPUT, ARTIFACT_ROOT),
                         (FAILURE_OUTPUT, ARTIFACT_ROOT), (FUTURE_SUMMARY, RESULT_ROOT)):
        _exact_parent(path, parent)
        if path.exists():
            raise FileExistsError(f"R-243 pre-launch target exists: {path}")
    unexpected = list(ARTIFACT_ROOT.glob("r243-s15-short-baseline-prechange.staging-*"))
    if unexpected:
        raise FileExistsError("R-243 unexpected staging sibling exists")
    STAGING_OUTPUT.mkdir()
    state = {"completed_modes": [], "phase": "owned", "resources": {}}
    try:
        _copy_provenance(authority_path, authority)
        gate = importlib.import_module("r232_s15_source_filter_gate")
        commands = []
        for mode, wall_limit, cpu_limit in (
            ("timing", TIMING_WALL_LIMIT, WORKER_CPU_LIMIT),
            ("profile", PROFILE_WALL_LIMIT, PROFILE_CPU_LIMIT),
        ):
            state["phase"] = f"{mode}-worker"
            request_path = STAGING_OUTPUT / f"{mode}-request.json"
            request = {"authority_sha256": authority_sha.lower(), "mode": mode, "nonce": secrets.token_hex(32),
                       "output": str((STAGING_OUTPUT / mode).resolve(strict=False)), "parent_pid": os.getpid(),
                       "schema": "resonith-r243-worker-request-1"}
            _atomic_json(request_path, request)
            request_sha = _sha256(request_path)
            command = [sys.executable, str(Path(__file__).resolve()),
                       "--worker-request", str(request_path), "--worker-request-sha256", request_sha,
                       "--authority", str(authority_path.resolve()), "--authority-sha256", authority_sha]
            commands.append(command)
            original_create_job = _install_hard_cpu_job(gate, cpu_limit)
            try:
                state["resources"][mode] = gate._run_monitored(
                    command, STAGING_OUTPUT, STAGING_OUTPUT / mode,
                    context={"hard_cpu_limit_seconds": cpu_limit, "mode": mode},
                    memory_limit=MEMORY_LIMIT, wall_limit=wall_limit,
                    retained_limit=RETAINED_LIMIT, output_limit=LOG_LIMIT,
                )
            finally:
                gate._create_job = original_create_job
            report = json.loads((STAGING_OUTPUT / mode / "report.json").read_text(encoding="utf-8"))
            expected_schema = f"resonith-r243-s15-{mode}-worker-1"
            if report.get("schema") != expected_schema:
                raise RuntimeError(f"R-243 {mode} worker schema mismatch")
            if report.get("source_sha256_after") != authority["files"]["source"]["sha256"]:
                raise RuntimeError(f"R-243 {mode} source identity mismatch")
            cpu_proxy = report["worker_process_cpu_seconds_proxy"]
            if cpu_proxy > cpu_limit:
                raise RuntimeError(f"R-243 {mode} CPU proxy exceeded hard limit")
            state["resources"][mode]["process_cpu_proxy_seconds"] = cpu_proxy
            _read_authority(authority_path, authority_sha, check_git=True)
            if _sha256(Path(authority["files"]["source"]["path"])) != authority["files"]["source"]["sha256"]:
                raise RuntimeError(f"R-243 source drift after {mode}")
            state["last_validated"] = {"authority_sha256": authority_sha.lower(), "source_sha256": authority["files"]["source"]["sha256"], "stage": mode}
            state["completed_modes"].append(mode)
        timing = json.loads((STAGING_OUTPUT / "timing/report.json").read_text(encoding="utf-8"))
        profile = json.loads((STAGING_OUTPUT / "profile/report.json").read_text(encoding="utf-8"))
        if profile["identity"] != timing["identities"]["rescored"]:
            raise RuntimeError("R-243 timing/profile rescored identity mismatch")
        _validate_golden(STAGING_OUTPUT / "timing/golden-vectors.json", timing["golden"]["sha256"])
        predicates = {
            "lpc_calls_at_least_100000": profile["profile_functions"]["_lpc_q14"]["total_calls"] >= 100000,
            "lpc_cumulative_ratio_at_least_half": profile["lpc_to_encode_cumulative_ratio"] >= 0.5,
            "rescored_cpu_greater_than_legacy": timing["medians"]["rescored"]["cpu_seconds"] > timing["medians"]["legacy"]["cpu_seconds"],
        }
        if not all(predicates.values()):
            raise RuntimeError(f"R-243 Phase-A consistency predicate failed: {predicates}")
        state["phase"] = "precommit"
        _read_authority(authority_path, authority_sha, check_git=True)
        source_hash = _sha256(Path(authority["files"]["source"]["path"]))
        if source_hash != authority["files"]["source"]["sha256"]:
            raise RuntimeError("R-243 source drift before publication")
        state["last_validated"] = {"authority_sha256": authority_sha.lower(), "source_sha256": source_hash, "stage": "precommit"}
        receipt = {
            "authority_sha256": authority_sha, "commands": commands,
            "controller_wall_seconds_before_receipt": time.perf_counter() - started,
            "environment": ENVIRONMENT, "git_commit": authority["git_commit"], "identities": authority["files"],
            "predicates": predicates, "python": authority["python"], "resources": state["resources"],
            "retained_files": _manifest(STAGING_OUTPUT), "runtime": authority["runtime"],
            "schema": "resonith-r243-s15-phase-a-receipt-1", "status": "PASS"}
        _atomic_json(STAGING_OUTPUT / "receipt.json", receipt)
        total = sum(path.stat().st_size for path in STAGING_OUTPUT.rglob("*") if path.is_file())
        if total > RETAINED_LIMIT:
            raise OSError("R-243 retained output exceeds 32 MiB")
        _read_authority(authority_path, authority_sha, check_git=True)
        if _sha256(Path(authority["files"]["source"]["path"])) != source_hash:
            raise RuntimeError("R-243 source changed at final publication boundary")
        if time.perf_counter() - started > CONTROLLER_WALL_LIMIT:
            raise TimeoutError("R-243 controller wall limit exceeded at precommit")
        STAGING_OUTPUT.replace(FINAL_OUTPUT)
    except BaseException as error:
        state["phase_at_failure"] = state["phase"]
        _failure(error, authority_sha, started, state)
        raise
def _failure(error: BaseException, authority_sha: str, started: float, state: dict) -> None:
    monitored = getattr(error, "evidence", None)
    cleanup_error = _safe_remove_staging()
    payload = {
        "authority_sha256": authority_sha.lower(), "controller_wall_seconds": time.perf_counter() - started,
        "error": f"{type(error).__name__}: {error}", "monitored_failure_evidence": monitored,
        "phase_state": state, "schema": "resonith-r243-s15-phase-a-failure-1",
        "staging_cleanup_error": cleanup_error, "status": "FAIL", "traceback": traceback.format_exc()[-16384:]}
    if len(_canonical_bytes(payload)) > LOG_LIMIT:
        payload["traceback"] = "failure receipt truncated"
    _atomic_json(FAILURE_OUTPUT, payload)
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--authority-sha256", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-request", type=Path)
    parser.add_argument("--worker-request-sha256")
    arguments = parser.parse_args()
    if arguments.worker_request:
        if arguments.output is not None or not arguments.worker_request_sha256:
            raise RuntimeError("R-243 controller/worker roles are exclusive")
        request = _worker_request(arguments.worker_request, arguments.worker_request_sha256)
        if request["authority_sha256"] != arguments.authority_sha256.lower():
            raise RuntimeError("R-243 request authority mismatch")
        worker_output = Path(request["output"])
        if request["mode"] == "timing":
            _timing_worker(arguments.authority, arguments.authority_sha256, worker_output)
        else:
            _profile_worker(arguments.authority, arguments.authority_sha256, worker_output)
        return
    if arguments.output is None or arguments.worker_request_sha256:
        raise RuntimeError("R-243 controller requires exact --output")
    _controller(arguments.authority, arguments.authority_sha256, arguments.output)
if __name__ == "__main__":
    main()
