"""Atomically capture bounded R-246 Phase-A evidence; this changes no codec code."""
from __future__ import annotations
import argparse, cProfile, hashlib, importlib, io, json, math, os
from pathlib import Path
import platform, pstats, secrets, shutil, statistics, subprocess, sys, time, traceback
from types import SimpleNamespace
PROCESS_CPU_START = time.process_time()
sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = PROJECT_ROOT / "artifacts"
RESULT_ROOT = PROJECT_ROOT / "experiments/results"
FINAL_OUTPUT = ARTIFACT_ROOT / "r246-s15-short-baseline-prechange"
STAGING_OUTPUT = ARTIFACT_ROOT / "r246-s15-short-baseline-prechange.staging"
FAILURE_OUTPUT = ARTIFACT_ROOT / "r246-s15-short-baseline-prechange-failure.json"
FUTURE_SUMMARY = RESULT_ROOT / "r246_s15_short_baseline_prechange.json"
AUTHORITY_PATH = PROJECT_ROOT / "experiments/fixtures/r246_s15_phase_a_authority.json"
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
ALLOWED_DIRS = {".", "profile", "provenance", "timing"}
ALLOWED_FILES = set("""profile-request.consumed profile-request.json profile.stderr.log profile.stdout.log
profile/cumulative.txt profile/report.json profile/rescored-decoded.pcm16le profile/rescored-encoder-report.json
profile/rescored.prof profile/rescored.resonith profile/self.txt provenance/authority.json provenance/preclearance-audit.md
provenance/preflight.md provenance/remediation.md provenance/runner.py receipt.json timing-request.consumed timing-request.json
timing.stderr.log timing.stdout.log timing/golden-vectors.json timing/legacy-decoded.pcm16le timing/legacy-report.json
timing/legacy.resonith timing/report.json timing/rescored-decoded.pcm16le timing/rescored-report.json timing/rescored.resonith""".split())
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
    if path.exists() and exclusive: raise FileExistsError(f"refusing to replace {path}")
    if temporary.exists(): raise FileExistsError(f"temporary path exists: {temporary}")
    payload = _canonical_bytes(value)
    try:
        with temporary.open("xb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        if exclusive and path.exists(): raise FileExistsError(f"refusing to replace {path}")
        temporary.replace(path)
    finally:
        if temporary.exists(): temporary.unlink()
def _is_reparse(path: Path) -> bool:
    if not path.exists(): return False
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & 0x400)
def _exact_parent(path: Path, parent: Path) -> None:
    if path.resolve(strict=False).parent != parent.resolve(strict=True): raise RuntimeError(f"path escapes exact parent: {path}")
    if _is_reparse(parent) or _is_reparse(path): raise RuntimeError(f"reparse point is forbidden: {path}")
def _safe_remove_staging() -> str | None:
    try:
        _exact_parent(STAGING_OUTPUT, ARTIFACT_ROOT)
        if STAGING_OUTPUT.exists():
            if STAGING_OUTPUT.name != "r246-s15-short-baseline-prechange.staging": raise RuntimeError("unexpected staging name")
            shutil.rmtree(STAGING_OUTPUT)
        return None
    except BaseException as error:
        return f"{type(error).__name__}: {error}"
def _read_authority(path: Path, expected_sha256: str, *, check_git: bool) -> dict:
    resolved = path.resolve(strict=True)
    if resolved != AUTHORITY_PATH.resolve(strict=True): raise RuntimeError("R-246 authority path mismatch")
    raw = resolved.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256.lower(): raise RuntimeError("R-243 authority SHA-256 mismatch")
    authority = json.loads(raw)
    if authority.get("schema") != "resonith-r246-s15-phase-a-authority-1": raise RuntimeError("R-246 authority schema mismatch")
    if set(authority) != {"budgets", "environment", "files", "git_commit", "output_paths", "python", "runner", "runtime", "schema", "scope", "source"}: raise RuntimeError("R-246 authority top-level schema mismatch")
    if authority["environment"] != ENVIRONMENT or set(authority["python"]) != {"path", "sha256", "version"} or set(authority["runtime"]) != {"numpy", "windows_build"}: raise RuntimeError("R-246 authority runtime contract mismatch")
    if set(authority["files"]) != {"audit", "base_authority", "configuration", "implementation_audit", "native_core", "numpy_binary", "oracle", "preflight", "r232_runner", "r243_closure", "r243_preflight", "remediation", "runner", "source", "test_module"}: raise RuntimeError("R-246 authority file-set mismatch")
    if authority["budgets"] != {"controller_wall_seconds": 510.0, "log_bytes_each": LOG_LIMIT, "profile_cpu_seconds": PROFILE_CPU_LIMIT, "profile_wall_seconds": PROFILE_WALL_LIMIT, "retained_bytes": RETAINED_LIMIT, "timing_cpu_seconds": WORKER_CPU_LIMIT, "timing_wall_seconds": TIMING_WALL_LIMIT, "worker_peak_memory_bytes": MEMORY_LIMIT}: raise RuntimeError("R-246 authority budget mismatch")
    if authority["output_paths"] != {"failure": FAILURE_OUTPUT.as_posix(), "future_summary": FUTURE_SUMMARY.as_posix(), "staging": STAGING_OUTPUT.as_posix(), "success": FINAL_OUTPUT.as_posix()}: raise RuntimeError("R-246 authority output-path mismatch")
    if authority["source"] != {"channels": 1, "sample_count": 93680, "sample_rate": 16000} or authority["scope"] != "one immutable short pre-change timing/profile/golden transaction only": raise RuntimeError("R-246 authority scope/source mismatch")
    if set(authority["runner"]) != {"bytes", "lines", "maximum_bytes", "maximum_lines"} or authority["runner"]["maximum_bytes"] != 65536 or authority["runner"]["maximum_lines"] != 640: raise RuntimeError("R-246 authority runner contract mismatch")
    if Path(sys.executable).resolve(strict=True) != Path(authority["python"]["path"]).resolve(strict=True): raise RuntimeError("R-243 Python executable path mismatch")
    if platform.python_version() != authority["python"]["version"]: raise RuntimeError("R-243 Python version mismatch")
    if _sha256(Path(sys.executable).resolve(strict=True)) != authority["python"]["sha256"]: raise RuntimeError("R-243 Python executable hash mismatch")
    if platform.version() != authority["runtime"]["windows_build"]: raise RuntimeError("R-243 Windows build mismatch")
    for name, expected in authority["environment"].items():
        if os.environ.get(name) != expected or ENVIRONMENT.get(name) != expected: raise RuntimeError(f"R-243 environment mismatch: {name}")
    if not sys.dont_write_bytecode or sys.flags.optimize != 0 or os.name != "nt": raise RuntimeError("R-243 interpreter mode mismatch")
    for name, record in authority["files"].items():
        candidate = Path(record["path"])
        candidate = (candidate if candidate.is_absolute() else PROJECT_ROOT / candidate).resolve(strict=True)
        if _is_reparse(candidate) or _sha256(candidate) != record["sha256"]: raise RuntimeError(f"R-243 authority file drift: {name}")
    runner = Path(__file__).resolve(strict=True)
    authorized_runner = (PROJECT_ROOT / authority["files"]["runner"]["path"]).resolve(strict=True)
    if runner != authorized_runner: raise RuntimeError("R-246 executing runner path mismatch")
    if runner.stat().st_size != authority["runner"]["bytes"]: raise RuntimeError("R-243 runner byte count mismatch")
    if len(runner.read_text(encoding="utf-8").splitlines()) != authority["runner"]["lines"]: raise RuntimeError("R-243 runner line count mismatch")
    if runner.stat().st_size > 65536 or authority["runner"]["lines"] > 640: raise RuntimeError("R-246 runner exceeds its audited source bound")
    if check_git:
        observed = subprocess.run(["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        if observed != authority["git_commit"]: raise RuntimeError("R-243 Git commit drift")
    return authority
def _load_codec(authority: dict):
    sys.path[:0] = [str(PROJECT_ROOT), str(PROJECT_ROOT / "reference"), str(PROJECT_ROOT / "experiments")]
    gate = importlib.import_module("r232_s15_source_filter_gate")
    base = authority["files"]["base_authority"]
    base_authority, files = gate._validate_authority((PROJECT_ROOT / base["path"]).resolve(strict=True), base["sha256"])
    widened = dict(base_authority); widened["local_modules"] = dict(base_authority["local_modules"])
    widened["local_modules"][Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix()] = _sha256(Path(__file__))
    gate._load_runtime(widened)
    oracle = importlib.import_module("maf_p0.maf_source_filter_oracle")
    if gate.np.__version__ != authority["runtime"]["numpy"]: raise RuntimeError("R-243 NumPy version mismatch")
    return gate, oracle, files
def _normalize(value):
    if isinstance(value, dict): return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [_normalize(item) for item in value]
    if hasattr(value, "item"): return value.item()
    return value
def _counter_map(value) -> dict:
    counters = {}
    def visit(item, path=""):
        if isinstance(item, dict):
            for key, child in item.items():
                here = f"{path}.{key}" if path else str(key)
                if type(child) in {int, float} and ("candidate" in key or "subframe" in key): counters[here] = child
                visit(child, here)
        elif isinstance(item, list):
            for index, child in enumerate(item): visit(child, f"{path}[{index}]")
    visit(value); return counters
def _identity(encoded, gate, source, sample_rate: int) -> tuple[dict, object]:
    decoded_rate, decoded = gate.decode_maf_source_filter_stream(encoded.payload)
    if decoded_rate != sample_rate or not gate.np.array_equal(decoded, encoded.reconstruction): raise RuntimeError("R-243 independent decode mismatch")
    report = _normalize(encoded.report)
    report_bytes = _canonical_bytes(report)
    pcm = decoded.astype("<i2", copy=False).tobytes()
    counters = _counter_map(report)
    error = source.astype(gate.np.int64) - decoded.astype(gate.np.int64)
    record = {
        "bytes": len(encoded.payload),
        "candidate_subframe_counters": counters,
        "decoded_pcm_bytes": len(pcm),
        "decoded_pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "report_bytes": len(report_bytes),
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
                output, clipping = oracle._synthesize_short_filter_candidate(analysis, raw, committed, start, stop)
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
    if len(cases) != 128 or observed_ids != expected_ids or len(set(observed_ids)) != 128: raise RuntimeError("R-243 golden cardinality/order mismatch")
    if len(maximum) != 16 or any(len(case["touched_lpc_q14"]) != 9 for case in maximum): raise RuntimeError("R-243 golden nine-law witness mismatch")
    if any(
        case["source_dtype"] != "int16"
        or case["committed_output_dtype"] != "int64"
        or case["raw_excitation_dtype"] != "int64"
        for case in cases
    ):
        raise RuntimeError("R-243 golden dtype mismatch")
    destination.write_bytes(_canonical_bytes(payload))
    if json.loads(destination.read_text(encoding="utf-8")) != payload: raise RuntimeError("R-243 golden readback mismatch")
    return {"case_count": len(cases), "sha256": _sha256(destination)}
def _timing_worker(authority_path: Path, authority_sha: str, output: Path) -> None:
    authority = _read_authority(authority_path, authority_sha, check_git=False)
    gate, oracle, files = _load_codec(authority)
    output.mkdir()
    source_path = Path(authority["files"]["source"]["path"])
    sample_rate, channels = gate.read_pcm16_channels(source_path)
    if sample_rate != 16000 or channels.shape != (93680, 1): raise RuntimeError("R-243 source metadata mismatch")
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
        if any(record != frozen[0] for record in frozen[1:]): raise RuntimeError(f"R-243 nondeterministic {label} identity")
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
    if source_after != authority["files"]["source"]["sha256"]: raise RuntimeError("R-243 source drifted during timing worker")
    report = {
        "analysis": analysis_record,
        "golden": golden,
        "identities": {label: records[0] for label, records in identities.items()},
        "medians": medians,
        "pair_order": [list(pair) for pair in PAIR_ORDER],
        "schema": "resonith-r246-s15-timing-worker-1",
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
    (output / "rescored-decoded.pcm16le").write_bytes(retained[1])
    (output / "rescored-encoder-report.json").write_bytes(retained[2])
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
    if set(selected) != {"_lpc_q14", "encode_maf_source_filter_analysis"}: raise RuntimeError("R-243 required profile functions missing")
    ratio = selected["_lpc_q14"]["cumulative_seconds"] / selected["encode_maf_source_filter_analysis"]["cumulative_seconds"]
    _read_authority(authority_path, authority_sha, check_git=False)
    source_after = _sha256(source_path)
    if source_after != authority["files"]["source"]["sha256"]: raise RuntimeError("R-243 source drifted during profile worker")
    _atomic_json(output / "report.json", {
        "cumulative_sha256": _sha256(output / "cumulative.txt"), "identity": identity, "lpc_to_encode_cumulative_ratio": ratio, "profile_functions": selected,
        "profile_sha256": _sha256(profile_path), "schema": "resonith-r246-s15-profile-worker-1",
        "self_sha256": _sha256(output / "self.txt"),
        "source_sha256_after": source_after,
        "worker_process_cpu_seconds_proxy": time.process_time() - PROCESS_CPU_START})
def _manifest(root: Path) -> list[dict]:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != "receipt.json"):
        records.append({"bytes": path.stat().st_size, "path": path.relative_to(root).as_posix(),
                        "sha256": _sha256(path)})
    return records
def _full_base(gate, authority: dict) -> None:
    base = authority["files"]["base_authority"]
    gate._validate_authority((PROJECT_ROOT / base["path"]).resolve(strict=True), base["sha256"])
def _validate_tree(root: Path, *, receipt: bool) -> None:
    top = list(root.iterdir())
    if any(_is_reparse(path) for path in top): raise RuntimeError("R-246 retained reparse entry")
    directories = {"."} | {path.name for path in top if path.is_dir()}; files = {path.name for path in top if path.is_file()}
    for directory in (path for path in top if path.is_dir()):
        children = list(directory.iterdir())
        if any(_is_reparse(path) or path.is_dir() for path in children): raise RuntimeError("R-246 retained nested/reparse entry")
        files.update(f"{directory.name}/{path.name}" for path in children if path.is_file())
    expected = ALLOWED_FILES if receipt else ALLOWED_FILES - {"receipt.json"}
    if directories != ALLOWED_DIRS or files != expected: raise RuntimeError("R-246 retained path allowlist mismatch")
    lexical = Path(os.path.abspath(root)); cursor = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        cursor /= part
        if _is_reparse(cursor): raise RuntimeError(f"R-246 retained reparse component: {cursor}")
    if any(not any(path.iterdir()) for path in top if path.is_dir()): raise RuntimeError("R-246 empty retained directory")
def _valid_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
def _validate_identity(root: Path, label: str, identity: dict, report_name: str | None = None) -> None:
    stream, pcm = root / f"{label}.resonith", root / f"{label}-decoded.pcm16le"
    report = root / (report_name or f"{label}-report.json")
    if set(identity) != {"bytes", "candidate_subframe_counters", "decoded_pcm_bytes", "decoded_pcm_sha256", "report_bytes", "report_sha256", "stream_sha256", "waveform_sse"}: raise RuntimeError("R-246 retained identity schema mismatch")
    if not all(type(identity[key]) is int and identity[key] >= 0 for key in ("bytes", "decoded_pcm_bytes", "report_bytes", "waveform_sse")) or not all(_valid_sha(identity[key]) for key in ("decoded_pcm_sha256", "report_sha256", "stream_sha256")): raise RuntimeError("R-246 retained identity type mismatch")
    counters = identity["candidate_subframe_counters"]
    expected = {"maf_cell.subframe_count", "maf_cell.subframe_size"} | ({"maf_cell.decoder_domain_candidate_evaluations", "maf_cell.decoder_domain_rejected_candidate_evaluations"} if label == "rescored" else set())
    if not isinstance(counters, dict) or set(counters) != expected or any(type(value) is not int or value < 0 for value in counters.values()) or counters != _counter_map(_read_canonical(report)): raise RuntimeError("R-246 retained counter schema mismatch")
    if stream.stat().st_size != identity["bytes"] or _sha256(stream) != identity["stream_sha256"]: raise RuntimeError("R-246 retained stream identity mismatch")
    if pcm.stat().st_size != identity["decoded_pcm_bytes"] or report.stat().st_size != identity["report_bytes"]: raise RuntimeError("R-246 retained PCM/report size mismatch")
    if _sha256(pcm) != identity["decoded_pcm_sha256"] or _sha256(report) != identity["report_sha256"]: raise RuntimeError("R-246 retained PCM/report identity mismatch")
def _validate_provenance(authority_path: Path, authority_sha: str, authority: dict) -> None:
    records = {"authority.json": authority_sha, "preflight.md": authority["files"]["preflight"]["sha256"],
               "preclearance-audit.md": authority["files"]["audit"]["sha256"], "remediation.md": authority["files"]["remediation"]["sha256"],
               "runner.py": authority["files"]["runner"]["sha256"]}
    for name, expected in records.items():
        if _sha256(STAGING_OUTPUT / "provenance" / name) != expected: raise RuntimeError(f"R-246 frozen provenance mismatch: {name}")
def _read_canonical(path: Path):
    raw = path.read_bytes(); value = json.loads(raw)
    if raw != _canonical_bytes(value): raise RuntimeError(f"R-246 noncanonical JSON: {path.name}")
    return value
def _nonnegative(value) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and value >= 0
def _validate_requests(records: dict) -> None:
    if set(records) != {"timing", "profile"}: raise RuntimeError("R-246 request record set mismatch")
    for mode, record in records.items():
        raw = (STAGING_OUTPUT / f"{mode}-request.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"] or raw != _canonical_bytes(record["payload"]): raise RuntimeError("R-246 request identity mismatch")
        if (STAGING_OUTPUT / f"{mode}-request.consumed").read_bytes() != (record["sha256"] + "\n").encode("ascii"): raise RuntimeError("R-246 consumed marker mismatch")
def _validate_evidence(authority: dict):
    timing = _read_canonical(STAGING_OUTPUT / "timing/report.json"); profile = _read_canonical(STAGING_OUTPUT / "profile/report.json")
    timing_keys = {"analysis", "golden", "identities", "medians", "pair_order", "schema", "source_sha256_after", "trials", "worker_process_cpu_seconds_proxy"}
    profile_keys = {"cumulative_sha256", "identity", "lpc_to_encode_cumulative_ratio", "profile_functions", "profile_sha256", "schema", "self_sha256", "source_sha256_after", "worker_process_cpu_seconds_proxy"}
    if set(timing) != timing_keys or set(profile) != profile_keys or timing["schema"] != "resonith-r246-s15-timing-worker-1" or profile["schema"] != "resonith-r246-s15-profile-worker-1": raise RuntimeError("R-246 worker report schema mismatch")
    if timing["source_sha256_after"] != authority["files"]["source"]["sha256"] or profile["source_sha256_after"] != timing["source_sha256_after"]: raise RuntimeError("R-246 worker source mismatch")
    if set(timing["analysis"]) != {"cpu_seconds", "wall_seconds"} or not all(_nonnegative(value) for value in timing["analysis"].values()): raise RuntimeError("R-246 analysis timing mismatch")
    expected_trials = [(index, label) for index, pair in enumerate(PAIR_ORDER) for label in pair]
    if timing["pair_order"] != [list(pair) for pair in PAIR_ORDER] or len(timing["trials"]) != len(expected_trials): raise RuntimeError("R-246 trial order mismatch")
    for trial, (pair_index, label) in zip(timing["trials"], expected_trials, strict=True):
        if set(trial) != {"arm", "pair_index", "cpu_seconds", "wall_seconds"} or trial["arm"] != label or trial["pair_index"] != pair_index or not _nonnegative(trial["cpu_seconds"]) or not _nonnegative(trial["wall_seconds"]): raise RuntimeError("R-246 malformed timing trial")
    recomputed = {label: {kind: statistics.median(trial[kind] for trial in timing["trials"] if trial["arm"] == label) for kind in ("cpu_seconds", "wall_seconds")} for label in ("legacy", "rescored")}
    if timing["medians"] != recomputed or set(timing["identities"]) != {"legacy", "rescored"}: raise RuntimeError("R-246 timing aggregate mismatch")
    functions = profile["profile_functions"]
    if set(functions) != {"_lpc_q14", "encode_maf_source_filter_analysis"}: raise RuntimeError("R-246 profile function set mismatch")
    for record in functions.values():
        if set(record) != {"cumulative_seconds", "filename", "line", "primitive_calls", "self_seconds", "total_calls"} or not all(_nonnegative(record[key]) for key in ("cumulative_seconds", "self_seconds")) or not all(type(record[key]) is int and record[key] >= 0 for key in ("line", "primitive_calls", "total_calls")) or not isinstance(record["filename"], str): raise RuntimeError("R-246 malformed profile function")
    denominator = functions["encode_maf_source_filter_analysis"]["cumulative_seconds"]
    if denominator <= 0 or not _nonnegative(profile["lpc_to_encode_cumulative_ratio"]) or profile["lpc_to_encode_cumulative_ratio"] != functions["_lpc_q14"]["cumulative_seconds"] / denominator: raise RuntimeError("R-246 profile ratio mismatch")
    if not _nonnegative(timing["worker_process_cpu_seconds_proxy"]) or timing["worker_process_cpu_seconds_proxy"] > WORKER_CPU_LIMIT or not _nonnegative(profile["worker_process_cpu_seconds_proxy"]) or profile["worker_process_cpu_seconds_proxy"] > PROFILE_CPU_LIMIT: raise RuntimeError("R-246 worker CPU report mismatch")
    if _sha256(STAGING_OUTPUT / "profile/rescored.prof") != profile["profile_sha256"] or _sha256(STAGING_OUTPUT / "profile/cumulative.txt") != profile["cumulative_sha256"] or _sha256(STAGING_OUTPUT / "profile/self.txt") != profile["self_sha256"]: raise RuntimeError("R-246 retained profile identity mismatch")
    if profile["identity"] != timing["identities"]["rescored"]: raise RuntimeError("R-246 timing/profile identity mismatch")
    _validate_identity(STAGING_OUTPUT / "timing", "legacy", timing["identities"]["legacy"]); _validate_identity(STAGING_OUTPUT / "timing", "rescored", timing["identities"]["rescored"]); _validate_identity(STAGING_OUTPUT / "profile", "rescored", profile["identity"], "rescored-encoder-report.json")
    if set(timing["golden"]) != {"case_count", "sha256"} or timing["golden"]["case_count"] != 128: raise RuntimeError("R-246 golden declaration mismatch")
    _validate_golden(STAGING_OUTPUT / "timing/golden-vectors.json", timing["golden"]["sha256"])
    predicates = {"lpc_calls_at_least_100000": profile["profile_functions"]["_lpc_q14"]["total_calls"] >= 100000, "lpc_cumulative_ratio_at_least_half": profile["lpc_to_encode_cumulative_ratio"] >= 0.5, "rescored_cpu_greater_than_legacy": timing["medians"]["rescored"]["cpu_seconds"] > timing["medians"]["legacy"]["cpu_seconds"]}; return timing, profile, predicates
def _validate_golden(path: Path, expected_sha256: str) -> None:
    if _sha256(path) != expected_sha256: raise RuntimeError("R-243 golden hash mismatch")
    raw = path.read_bytes(); payload = json.loads(raw)
    cases = payload.get("cases", [])
    expected_ids = [f"i{i}-l{law}-p{pattern}" for i in range(8) for law in range(4) for pattern in range(4)]
    maximum = [case for case in cases if case.get("subframe_index") == 57]
    if set(payload) != {"case_count", "cases", "schema"} or payload.get("schema") != "resonith-r243-golden-1" or payload.get("case_count") != 128: raise RuntimeError("R-243 golden schema/count mismatch")
    if len(cases) != 128 or [case.get("id") for case in cases] != expected_ids: raise RuntimeError("R-243 golden identity/order mismatch")
    base_keys = {"block_size", "candidate_output", "clipping_count", "committed_output_dtype", "desired_excitation", "id", "law_family", "pattern", "raw_excitation_dtype", "source_dtype", "source_size", "start", "stop", "touched_lpc_q14"}
    for case, (interval_index, law_index, pattern_index) in zip(cases, ((i, law, pattern) for i in range(8) for law in range(4) for pattern in range(4)), strict=True):
        source_size, block_size, start, stop = INTERVALS[interval_index]; special = (source_size, block_size, start, stop) == (40000, 65, 29184, 29696)
        if set(case) != base_keys | ({"subframe_index", "subframe_size"} if special else set()) or (case["source_size"], case["block_size"], case["start"], case["stop"], case["pattern"], case["law_family"]) != (source_size, block_size, start, stop, PATTERNS[pattern_index], list(LAW_FAMILIES[law_index])): raise RuntimeError("R-246 golden matrix metadata mismatch")
        expected_blocks = list(range(start // block_size, min((source_size + block_size - 1) // block_size - 1, (stop - 1) // block_size) + 1)); touched = case["touched_lpc_q14"]
        if len(case["candidate_output"]) != stop - start or len(case["desired_excitation"]) != stop - start or not all(type(value) is int for value in case["candidate_output"] + case["desired_excitation"]): raise RuntimeError("R-246 golden vector shape mismatch")
        if type(case["clipping_count"]) is not int or case["clipping_count"] < 0 or [item.get("absolute_block") for item in touched] != expected_blocks or any(set(item) != {"absolute_block", "lpc_q14"} or len(item["lpc_q14"]) != len(LAW_FAMILIES[law_index]) or not all(type(value) is int for value in item["lpc_q14"]) for item in touched): raise RuntimeError("R-246 golden law witness mismatch")
        if special and (case["subframe_index"], case["subframe_size"]) != (57, 512): raise RuntimeError("R-246 golden subframe metadata mismatch")
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
    if raw != _canonical_bytes(payload): raise RuntimeError("R-243 golden serialization is not canonical")
def _worker_request(path: Path, expected_sha256: str) -> dict:
    _exact_parent(STAGING_OUTPUT, ARTIFACT_ROOT)
    if not STAGING_OUTPUT.is_dir() or _is_reparse(STAGING_OUTPUT): raise RuntimeError("R-243 worker staging ownership invalid")
    _exact_parent(path, STAGING_OUTPUT)
    resolved = path.resolve(strict=True); raw = resolved.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256.lower(): raise RuntimeError("R-243 worker request hash mismatch")
    request = json.loads(raw)
    if raw != _canonical_bytes(request): raise RuntimeError("R-246 worker request is not canonical")
    mode = request.get("mode")
    if request.get("schema") != "resonith-r246-worker-request-1" or mode not in {"timing", "profile"}: raise RuntimeError("R-243 worker request schema/mode mismatch")
    if path.resolve() != (STAGING_OUTPUT / f"{mode}-request.json").resolve(): raise RuntimeError("R-243 worker request path mismatch")
    if request.get("parent_pid") != os.getppid() or len(request.get("nonce", "")) != 64: raise RuntimeError("R-243 worker parent/nonce mismatch")
    output = Path(request["output"]).resolve(strict=False)
    if output != (STAGING_OUTPUT / mode).resolve(strict=False) or output.exists(): raise RuntimeError("R-243 worker output path mismatch")
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
def _copy_provenance(authority_path: Path, authority_sha: str, authority: dict) -> None:
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
    _validate_provenance(authority_path, authority_sha, authority)
def _deadline(started: float) -> None:
    if time.perf_counter() - started > CONTROLLER_WALL_LIMIT: raise TimeoutError("R-246 controller wall limit exceeded")
def _controller(authority_path: Path, authority_sha: str, output: Path) -> None:
    started = time.perf_counter()
    authority = _read_authority(authority_path, authority_sha, check_git=True)
    if output.resolve(strict=False) != FINAL_OUTPUT.resolve(strict=False): raise RuntimeError("R-243 output differs from the authorized exact path")
    for path, parent in ((FINAL_OUTPUT, ARTIFACT_ROOT), (STAGING_OUTPUT, ARTIFACT_ROOT),
                         (FAILURE_OUTPUT, ARTIFACT_ROOT), (FUTURE_SUMMARY, RESULT_ROOT)):
        _exact_parent(path, parent)
        if path.exists(): raise FileExistsError(f"R-243 pre-launch target exists: {path}")
    unexpected = list(ARTIFACT_ROOT.glob("r246-s15-short-baseline-prechange.staging-*"))
    if unexpected: raise FileExistsError("R-243 unexpected staging sibling exists")
    source_hash = authority["files"]["source"]["sha256"]
    state = {"completed_modes": [], "phase": "owned", "resources": {}, "last_validated": {"authority_sha256": authority_sha.lower(), "git_commit": authority["git_commit"], "source_sha256": source_hash, "stage": "owned"}}
    STAGING_OUTPUT.mkdir()
    try:
        _copy_provenance(authority_path, authority_sha, authority)
        gate = importlib.import_module("r232_s15_source_filter_gate")
        _full_base(gate, authority); _validate_provenance(authority_path, authority_sha, authority)
        commands = []; requests = {}
        for mode, wall_limit, cpu_limit in (
            ("timing", TIMING_WALL_LIMIT, WORKER_CPU_LIMIT),
            ("profile", PROFILE_WALL_LIMIT, PROFILE_CPU_LIMIT),
        ):
            _deadline(started)
            state["phase"] = f"{mode}-worker"
            request_path = STAGING_OUTPUT / f"{mode}-request.json"
            request = {"authority_sha256": authority_sha.lower(), "mode": mode, "nonce": secrets.token_hex(32),
                       "output": str((STAGING_OUTPUT / mode).resolve(strict=False)), "parent_pid": os.getpid(),
                       "schema": "resonith-r246-worker-request-1"}
            _atomic_json(request_path, request)
            request_sha = _sha256(request_path)
            requests[mode] = {"payload": request, "sha256": request_sha}
            command = [sys.executable, str(Path(__file__).resolve()),
                       "--worker-request", str(request_path), "--worker-request-sha256", request_sha,
                       "--authority", str(authority_path.resolve()), "--authority-sha256", authority_sha]
            commands.append(command)
            original_create_job = _install_hard_cpu_job(gate, cpu_limit)
            effective_wall = min(wall_limit, CONTROLLER_WALL_LIMIT - (time.perf_counter() - started))
            if effective_wall <= 0: _deadline(started)
            try:
                state["resources"][mode] = gate._run_monitored(
                    command, STAGING_OUTPUT, STAGING_OUTPUT / mode,
                    context={"hard_cpu_limit_seconds": cpu_limit, "mode": mode},
                    memory_limit=MEMORY_LIMIT, wall_limit=effective_wall,
                    retained_limit=RETAINED_LIMIT, output_limit=LOG_LIMIT,
                )
            finally:
                gate._create_job = original_create_job
            _deadline(started)
            raw_request = request_path.read_bytes()
            if hashlib.sha256(raw_request).hexdigest() != request_sha or raw_request != _canonical_bytes(request) or request_path.with_suffix(".consumed").read_bytes() != (request_sha + "\n").encode("ascii"): raise RuntimeError("R-246 request/marker drift")
            report = _read_canonical(STAGING_OUTPUT / mode / "report.json")
            expected_schema = f"resonith-r246-s15-{mode}-worker-1"
            if report.get("schema") != expected_schema: raise RuntimeError(f"R-243 {mode} worker schema mismatch")
            if report.get("source_sha256_after") != authority["files"]["source"]["sha256"]: raise RuntimeError(f"R-243 {mode} source identity mismatch")
            cpu_proxy = report["worker_process_cpu_seconds_proxy"]
            if cpu_proxy > cpu_limit: raise RuntimeError(f"R-243 {mode} CPU proxy exceeded hard limit")
            state["resources"][mode]["process_cpu_proxy_seconds"] = cpu_proxy
            _read_authority(authority_path, authority_sha, check_git=True); _full_base(gate, authority)
            source_hash = _sha256(Path(authority["files"]["source"]["path"]))
            if source_hash != authority["files"]["source"]["sha256"]: raise RuntimeError(f"R-243 source drift after {mode}")
            state["last_validated"] = {"authority_sha256": authority_sha.lower(), "git_commit": authority["git_commit"], "source_sha256": source_hash, "stage": mode}
            state["completed_modes"].append(mode)
        timing, profile, predicates = _validate_evidence(authority)
        state["observed"] = {"lpc_cumulative_ratio": profile["lpc_to_encode_cumulative_ratio"], "lpc_total_calls": profile["profile_functions"]["_lpc_q14"]["total_calls"], "medians": timing["medians"], "predicates": predicates}
        if not all(predicates.values()): raise RuntimeError(f"R-243 Phase-A consistency predicate failed: {predicates}")
        state["phase"] = "precommit"
        _deadline(started); _read_authority(authority_path, authority_sha, check_git=True); _full_base(gate, authority); _validate_provenance(authority_path, authority_sha, authority); _validate_requests(requests); _validate_tree(STAGING_OUTPUT, receipt=False)
        source_hash = _sha256(Path(authority["files"]["source"]["path"]))
        if source_hash != authority["files"]["source"]["sha256"]: raise RuntimeError("R-243 source drift before publication")
        state["last_validated"] = {"authority_sha256": authority_sha.lower(), "git_commit": authority["git_commit"], "source_sha256": source_hash, "stage": "precommit"}
        receipt = {
            "authority_sha256": authority_sha, "commands": commands, "controller_command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
            "controller_wall_seconds_before_receipt": time.perf_counter() - started,
            "environment": ENVIRONMENT, "git_commit": authority["git_commit"], "identities": authority["files"],
            "predicates": predicates, "python": authority["python"], "requests": requests, "resources": state["resources"],
            "retained_files": _manifest(STAGING_OUTPUT), "runtime": authority["runtime"],
            "schema": "resonith-r246-s15-phase-a-receipt-1", "status": "PASS"}
        _atomic_json(STAGING_OUTPUT / "receipt.json", receipt)
        _validate_tree(STAGING_OUTPUT, receipt=True)
        receipt_raw = (STAGING_OUTPUT / "receipt.json").read_bytes(); retained_receipt = json.loads(receipt_raw)
        if receipt_raw != _canonical_bytes(receipt) or retained_receipt != receipt: raise RuntimeError("R-246 retained receipt mismatch")
        if retained_receipt.get("retained_files") != _manifest(STAGING_OUTPUT): raise RuntimeError("R-246 post-receipt manifest mismatch")
        _, _, post_predicates = _validate_evidence(authority)
        if post_predicates != predicates: raise RuntimeError("R-246 post-receipt predicate drift")
        _validate_provenance(authority_path, authority_sha, authority); _validate_requests(requests)
        total = sum(path.stat().st_size for path in STAGING_OUTPUT.rglob("*") if path.is_file())
        if total > RETAINED_LIMIT: raise OSError("R-243 retained output exceeds 32 MiB")
        _read_authority(authority_path, authority_sha, check_git=True); _full_base(gate, authority)
        if _sha256(Path(authority["files"]["source"]["path"])) != source_hash: raise RuntimeError("R-243 source changed at final publication boundary")
        _deadline(started)
        if FINAL_OUTPUT.exists(): raise FileExistsError("R-246 final target appeared before publication")
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
        "error": f"{type(error).__name__}: {error}"[:4096], "monitored_failure_evidence": monitored,
        "phase_state": state, "schema": "resonith-r246-s15-phase-a-failure-1",
        "staging_cleanup_error": cleanup_error[:4096] if cleanup_error else None, "status": "FAIL", "traceback": traceback.format_exc()[-16384:]}
    if len(_canonical_bytes(payload)) > LOG_LIMIT:
        payload = {"authority_sha256": authority_sha.lower(), "controller_wall_seconds": time.perf_counter() - started, "error": payload["error"][:1024], "monitored_failure_evidence": monitored, "phase_state": {key: state.get(key) for key in ("completed_modes", "last_validated", "observed", "phase_at_failure", "resources")}, "schema": payload["schema"], "staging_cleanup_error": payload["staging_cleanup_error"], "status": "FAIL", "traceback": "failure receipt compacted"}
    if len(_canonical_bytes(payload)) > LOG_LIMIT: raise RuntimeError("R-246 internal failure receipt bound violated")
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
        if arguments.output is not None or not arguments.worker_request_sha256: raise RuntimeError("R-243 controller/worker roles are exclusive")
        request = _worker_request(arguments.worker_request, arguments.worker_request_sha256)
        if request["authority_sha256"] != arguments.authority_sha256.lower(): raise RuntimeError("R-243 request authority mismatch")
        worker_output = Path(request["output"])
        if request["mode"] == "timing":
            _timing_worker(arguments.authority, arguments.authority_sha256, worker_output)
        else:
            _profile_worker(arguments.authority, arguments.authority_sha256, worker_output)
        return
    if arguments.output is None or arguments.worker_request_sha256: raise RuntimeError("R-243 controller requires exact --output")
    expected = ["--authority", str(AUTHORITY_PATH), "--authority-sha256", arguments.authority_sha256, "--output", str(FINAL_OUTPUT)]
    if arguments.authority_sha256 != arguments.authority_sha256.lower() or sys.argv[1:] != expected: raise RuntimeError("R-246 controller invocation mismatch")
    _controller(arguments.authority, arguments.authority_sha256, arguments.output)
if __name__ == "__main__":
    main()
