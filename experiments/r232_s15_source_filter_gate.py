"""Execute the sealed R-232 S15 source-filter evidence gate.

The public role is a fail-closed controller. Every evidence input executes in
one suspended Windows child assigned to a bounded Job Object. The private
worker role accepts only a hash-bound request and publishes one input
transactionally. Real-audio admission remains disabled until its actual-
decoder comparison authority receives a separate audit.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import ast
import ctypes
from ctypes import wintypes
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = PROJECT_ROOT / "reference"
EXPERIMENT_ROOT = PROJECT_ROOT / "experiments"

np = None
analyze_maf_source_filter_source = None
decode_maf_source_filter_stream = None
encode_maf_source_filter_analysis = None
NativeMain0Decoder = None
read_pcm16_channels = None
write_pcm16_channels = None
compute_metrics = None
quality_axes = None

LOCAL_IMPORT_ROOTS = (
    "reference/maf_p0/maf_source_filter_oracle.py",
    "reference/maf_p0/native_core.py",
    "reference/maf_p0/wav_io.py",
    "experiments/r216_s12_metrics.py",
)


CONFIG_PATH = PROJECT_ROOT / "experiments/fixtures/r232_s15_frozen_configuration.json"
CONTROL_ORDER = (
    "stable-ar-periodic",
    "white-noise",
    "impulse",
    "two-component",
)
SYNTHETIC_SECONDS = 120
SAMPLE_RATE = 16000
WORKER_MEMORY_LIMIT = 3 << 30
WORKER_WALL_LIMIT = 900.0
RETAINED_LIMIT = 8 << 30
OUTPUT_CAPTURE_LIMIT = 8 << 20
POLL_SECONDS = 0.05


class _JobBasicLimit(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JobExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobBasicLimit),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _JobBasicAccounting(ctypes.Structure): _fields_ = [(name,ctype) for name,ctype in (("TotalUserTime",ctypes.c_longlong),("TotalKernelTime",ctypes.c_longlong),("ThisPeriodTotalUserTime",ctypes.c_longlong),("ThisPeriodTotalKernelTime",ctypes.c_longlong),("TotalPageFaultCount",wintypes.DWORD),("TotalProcesses",wintypes.DWORD),("ActiveProcesses",wintypes.DWORD),("TotalTerminatedProcesses",wintypes.DWORD))]
class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class _ThreadEntry32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()
def _directory_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            continue
    return total


def _atomic_write_json(path: Path, value: object, deadline: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"R-232 temporary receipt exists: {temporary}")
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as destination:
            destination.write(payload)
            destination.flush(); os.fsync(destination.fileno())
            if deadline is not None and time.perf_counter() > deadline: raise TimeoutError("R-263 receipt flush deadline exceeded")
        temporary.replace(path); deadline is None or time.perf_counter() <= deadline or (path.unlink(),(_ for _ in ()).throw(TimeoutError("R-263 receipt publication deadline exceeded")))
    finally:
        if temporary.exists():
            temporary.unlink()


def _safe_remove_staging(path: Path, expected_parent: Path) -> None:
    resolved = path.resolve(strict=False)
    parent = expected_parent.resolve(strict=True)
    if resolved.parent != parent or ".staging-" not in resolved.name:
        raise RuntimeError("R-232 refused unsafe staging cleanup")
    if resolved.exists():
        shutil.rmtree(resolved)


def _retained_files(root: Path) -> list[dict[str, object]]:
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        records.append(
            {
                "bytes": path.stat().st_size,
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
            }
        )
    return records


def _read_bound_json(path: Path, expected_sha256: str, label: str) -> dict:
    payload = path.resolve(strict=True).read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256.lower():
        raise RuntimeError(f"R-232 {label} SHA-256 mismatch")
    return json.loads(payload.decode("utf-8"))


def _tree_sha256(root: Path) -> str:
    """Hash stable relative names and every file byte in one runtime tree."""

    resolved = root.resolve(strict=True)
    digest = hashlib.sha256()
    for path in sorted(item for item in resolved.rglob("*") if item.is_file()):
        relative = path.relative_to(resolved)
        name = relative.as_posix().encode("utf-8")
        digest.update(len(name).to_bytes(4, "little"))
        digest.update(name)
        digest.update(path.stat().st_size.to_bytes(8, "little"))
        with path.open("rb") as source:
            while chunk := source.read(1 << 20):
                digest.update(chunk)
    return digest.hexdigest()
def _filtered_tree_sha256(root: Path) -> str:
    if root.is_symlink() or getattr((state := root.lstat()), "st_file_attributes", 0) & 0x400: raise RuntimeError("R-257 runtime tree root is a reparse entry")
    resolved = root.resolve(strict=True); digest = hashlib.sha256(b"resonith-r257-filtered-tree-1\0"); files: list[tuple[bytes,int,Path]] = []; stack = [(resolved,())]
    while stack:
        parent, parts = stack.pop()
        for entry in os.scandir(parent):
            relative, state = (*parts,entry.name), entry.stat(follow_symlinks=False)
            if entry.is_symlink() or getattr(state,"st_file_attributes",0) & 0x400: raise RuntimeError("R-257 runtime tree contains a reparse entry")
            if entry.is_dir(follow_symlinks=False): (entry.name != "__pycache__" and stack.append((Path(entry.path),relative))); continue
            if not entry.is_file(follow_symlinks=False): raise RuntimeError("R-257 runtime tree contains a non-regular entry")
            if Path(entry.name).suffix.lower() in {".pyc", ".pyo"}: raise RuntimeError("R-257 sourceless runtime bytecode is forbidden")
            files.append(("/".join(relative).encode(),state.st_size,Path(entry.path)))
    for name, size, path in sorted(files):
        digest.update(b"F"+len(name).to_bytes(4,"little")+name+size.to_bytes(8,"little")+bytes.fromhex(_sha256(path)))
    return digest.hexdigest()


def _module_index() -> tuple[dict[str, Path], dict[Path, str]]:
    index: dict[str, Path] = {}
    canonical: dict[Path, str] = {}

    def add(name: str, path: Path) -> None:
        if name:
            index[name] = path

    for path in sorted(REFERENCE_ROOT.rglob("*.py")):
        relative = path.relative_to(REFERENCE_ROOT).with_suffix("")
        parts = list(relative.parts)
        if parts[-1] == "__init__":
            parts.pop()
        primary = ".".join(parts)
        resolved = path.resolve(strict=True)
        canonical[resolved] = primary
        add(primary, resolved)
        add("reference." + primary, resolved)
    for path in sorted(EXPERIMENT_ROOT.glob("*.py")):
        primary = "experiments." + path.stem
        resolved = path.resolve(strict=True)
        canonical[resolved] = primary
        add(primary, resolved)
        add(path.stem, resolved)
    return index, canonical


def _discover_local_import_closure() -> dict[str, Path]:
    """Return the complete statically declared local import closure."""

    index, canonical = _module_index()
    pending = [
        (PROJECT_ROOT / relative).resolve(strict=True)
        for relative in LOCAL_IMPORT_ROOTS
    ]
    closure = {Path(__file__).resolve(strict=True)}
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        closure.add(path)
        module_name = canonical.get(path)
        if module_name is None:
            raise RuntimeError(f"R-232 local module is not indexed: {path}")
        package = (
            module_name
            if path.name == "__init__.py"
            else module_name.rpartition(".")[0]
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        dependencies: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                dependencies.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    target = "." * node.level + (node.module or "")
                    base = importlib.util.resolve_name(target, package)
                else:
                    base = node.module or ""
                dependencies.add(base)
                dependencies.update(
                    f"{base}.{alias.name}" if base else alias.name
                    for alias in node.names
                )
        for dependency in dependencies:
            candidate = index.get(dependency)
            if candidate is not None and candidate not in closure:
                pending.append(candidate)
        top_package = module_name.split(".", 1)[0]
        package_init = index.get(top_package)
        if package_init is not None and package_init not in closure:
            pending.append(package_init)
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): path
        for path in sorted(closure)
    }


def _discover_local_bytecode_closure(
    local_modules: dict[str, Path],
) -> dict[str, Path]:
    """Enumerate every existing cache CPython could select for local source."""

    bytecode = set()
    for source in local_modules.values():
        for legacy in (source.with_suffix(".pyc"), source.with_suffix(".pyo")):
            if legacy.exists():
                bytecode.add(legacy.resolve(strict=True))
        cache = source.parent / "__pycache__"
        if cache.exists():
            for pattern in (source.stem + ".*.pyc", source.stem + ".*.pyo"):
                bytecode.update(
                    item.resolve(strict=True) for item in cache.glob(pattern)
                )
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): path
        for path in sorted(bytecode)
    }


def _resolve_authorized_file(record: dict[str, str], base: Path) -> Path:
    raw_path = Path(record["path"])
    path = raw_path if raw_path.is_absolute() else base / raw_path
    resolved = path.resolve(strict=True)
    if _sha256(resolved) != record["sha256"].lower():
        raise RuntimeError(f"R-232 authority file drift: {record['path']}")
    return resolved


def _validate_authority(path: Path, expected_sha256: str) -> tuple[dict, dict[str, Path]]:
    authority = _read_bound_json(
        path,
        expected_sha256,
        "implementation authority",
    )
    schema = authority.get("schema")
    if schema not in {"resonith-r232-s15-implementation-authority-2","resonith-r257-source-execution-authority-1"}: raise RuntimeError("R-232 implementation authority schema mismatch")
    source_authority = schema == "resonith-r257-source-execution-authority-1"
    required_files = {"bootstrap","configuration","gate","golden","native_core","r253_preflight","r257_preflight","r260_probe","r260_probe_runner","r260_probe_summary","r260_remediation","r262_remediation","r263_remediation","test_module"} if source_authority else {"configuration","native_core","preflight","test_module"}
    if set(authority.get("files",{})) != required_files: raise RuntimeError("R-232 implementation authority file set mismatch")
    files = {
        name: _resolve_authorized_file(record, PROJECT_ROOT)
        for name, record in authority["files"].items()
    }
    if files["configuration"] != CONFIG_PATH.resolve(strict=True):
        raise RuntimeError("R-232 authority does not bind the frozen configuration")
    discovered = _discover_local_import_closure()
    declared = authority.get("local_modules", {})
    if set(declared) != set(discovered):
        raise RuntimeError("R-232 local import closure differs from authority")
    for relative, module_path in discovered.items():
        if _sha256(module_path) != declared[relative].lower():
            raise RuntimeError(f"R-232 local module drift: {relative}")
    if source_authority:
        if "local_bytecode" in authority: raise RuntimeError("R-257 source authority contains bytecode")
        local_imports = authority.get("local_imports", {})
        if not isinstance(local_imports,dict): raise RuntimeError("R-257 local import map is invalid")
        import_paths = []
        for name, record in local_imports.items():
            if not name or not isinstance(record,dict): raise RuntimeError("R-257 local import record is invalid")
            resolved = _resolve_authorized_file(record,PROJECT_ROOT); import_paths.append(resolved.relative_to(PROJECT_ROOT).as_posix())
            if record.get("package") is not (resolved.name == "__init__.py"): raise RuntimeError(f"R-257 local package identity drift: {name}")
        expected_paths = set(discovered) | {files["test_module"].relative_to(PROJECT_ROOT).as_posix()}
        if len(import_paths) != len(set(import_paths)) or set(import_paths) != expected_paths:
            raise RuntimeError("R-257 local import map does not close source paths")
        source_execution = authority.get("source_execution", {})
        expected_loaders = [[suffix,loader.__module__,loader.__qualname__] for loader,suffixes in ((importlib.machinery.ExtensionFileLoader,importlib.machinery.EXTENSION_SUFFIXES),(importlib.machinery.SourceFileLoader,importlib.machinery.SOURCE_SUFFIXES),(importlib.machinery.SourcelessFileLoader,importlib.machinery.BYTECODE_SUFFIXES)) for suffix in suffixes]
        required_imports = {"controller":["r232_s15_source_filter_gate"],"focused":["maf_p0.maf_source_filter_oracle","r232_s15_source_filter_gate","test_maf_source_filter_oracle"]}
        if source_execution.get("digest") != "resonith-r257-filtered-tree-1" or source_execution.get("file_finder_loaders") != expected_loaders or source_execution.get("python_flags") != {"stage0":["-I","-S","-B"],"stage1":["-S","-P","-B"]} or source_execution.get("required_local_imports") != required_imports or not isinstance(source_execution.get("r263_launcher_source"),str) or hashlib.sha256(source_execution.get("r263_launcher_source","").encode()).hexdigest() != source_execution.get("r263_launcher_sha256") or Path(authority.get("prefix_root","")).resolve(strict=True) != (PROJECT_ROOT/"artifacts").resolve(strict=True): raise RuntimeError("R-257 source-execution policy drift")
        if Path(source_execution.get("python_executable_path", "")).resolve(strict=True) != Path(sys.executable).resolve(strict=True) or _sha256(Path(sys.executable)) != authority["runtime_files"]["python.exe"]: raise RuntimeError("R-263 Python executable identity drift")
    else:
        discovered_bytecode = _discover_local_bytecode_closure(discovered); declared_bytecode = authority.get("local_bytecode",{})
        if set(declared_bytecode) != set(discovered_bytecode): raise RuntimeError("R-232 local executable bytecode closure differs")
        for relative, bytecode_path in discovered_bytecode.items():
            if _sha256(bytecode_path) != declared_bytecode[relative].lower(): raise RuntimeError(f"R-232 local bytecode drift: {relative}")

    runtime_root = Path(sys.executable).resolve(strict=True).parent
    required_runtime_files = {
        "python.exe",
        "python3.dll",
        "python314.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
    }
    runtime_files = authority.get("runtime_files", {})
    if set(runtime_files) != required_runtime_files:
        raise RuntimeError("R-232 Python runtime file set mismatch")
    for name, expected in runtime_files.items():
        runtime_file = (runtime_root / name).resolve(strict=True)
        if _sha256(runtime_file) != expected.lower():
            raise RuntimeError(f"R-232 Python runtime drift: {name}")
    runtime_trees = authority.get("runtime_trees", {})
    if set(runtime_trees) != {"DLLs", "Lib"}:
        raise RuntimeError("R-232 Python runtime tree set mismatch")
    tree_hash = _filtered_tree_sha256 if source_authority else _tree_sha256
    for name, expected in runtime_trees.items():
        if tree_hash(runtime_root / name) != expected.lower():
            raise RuntimeError(f"R-232 Python runtime tree drift: {name}")

    metadata = importlib.import_module("importlib.metadata"); source_versions = {distribution.metadata["Name"].lower():distribution.version for distribution in metadata.distributions(path=[authority["site_packages"]])} if source_authority else None
    expected_runtime = {
        "external_packages": {
            name: source_versions[name] if source_authority else metadata.version(name)
            for name in ("numpy", "scipy", "soundfile", "pystoi", "cffi")
        },
        "python": platform.python_version(),
        "windows_build": platform.version(),
    }
    if authority.get("runtime") != expected_runtime:
        raise RuntimeError("R-232 runtime identity mismatch")
    required_environment = {
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
    for name, expected in required_environment.items():
        if os.environ.get(name) != expected:
            raise RuntimeError(f"R-232 requires {name}={expected}")
    if not sys.dont_write_bytecode: raise RuntimeError("R-232 requires disabled bytecode writes")
    if source_authority:
        prefix = Path(os.environ.get("PYTHONPYCACHEPREFIX", "")).resolve(strict=True)
        if sys.pycache_prefix is None or prefix != Path(sys.pycache_prefix).resolve(strict=True): raise RuntimeError("R-257 source-execution prefix mismatch")
        if any(prefix.iterdir()): raise RuntimeError("R-257 source-execution prefix is not empty")
        expected_site = (runtime_root / "Lib" / "site-packages").resolve(strict=True)
        if Path(authority.get("site_packages", "")).resolve(strict=True) != expected_site: raise RuntimeError("R-257 site-packages authority mismatch")
    elif sys.pycache_prefix is not None: raise RuntimeError("R-232 requires default-location bytecode reads")
    if sys.flags.optimize != 0: raise RuntimeError("R-232 requires Python optimization level zero")
    if os.name != "nt": raise RuntimeError("R-232 frozen execution is Windows-only")
    return authority, files


def _load_runtime(authority: dict) -> None:
    """Import third-party and project code only after authority validation."""

    global np
    global analyze_maf_source_filter_source
    global decode_maf_source_filter_stream
    global encode_maf_source_filter_analysis
    global NativeMain0Decoder
    global read_pcm16_channels
    global write_pcm16_channels
    global compute_metrics
    global quality_axes
    if np is not None:
        return
    np = importlib.import_module("numpy")
    oracle = importlib.import_module("maf_p0.maf_source_filter_oracle")
    native = importlib.import_module("maf_p0.native_core")
    wav = importlib.import_module("maf_p0.wav_io")
    metrics = importlib.import_module("r216_s12_metrics")
    analyze_maf_source_filter_source = oracle.analyze_maf_source_filter_source
    decode_maf_source_filter_stream = oracle.decode_maf_source_filter_stream
    encode_maf_source_filter_analysis = oracle.encode_maf_source_filter_analysis
    NativeMain0Decoder = native.NativeMain0Decoder
    read_pcm16_channels = wav.read_pcm16_channels
    write_pcm16_channels = wav.write_pcm16_channels
    compute_metrics = metrics.compute_metrics
    quality_axes = metrics.quality_axes
    authorized = set(authority["local_modules"])
    loaded = set()
    runtime_root = Path(sys.executable).resolve(strict=True).parent
    for module in tuple(sys.modules.values()):
        raw_path = getattr(module, "__file__", None)
        if raw_path is None:
            continue
        try:
            resolved = Path(raw_path).resolve(strict=True)
            if resolved == runtime_root or runtime_root in resolved.parents:
                continue
            relative = resolved.relative_to(PROJECT_ROOT).as_posix()
        except (OSError, ValueError):
            continue
        if resolved.suffix == ".py":
            loaded.add(relative)
    unauthorized = loaded - authorized
    if unauthorized:
        raise RuntimeError(
            "R-232 imported unauthorized local modules: "
            + ", ".join(sorted(unauthorized))
        )


def _synthetic(control: str) -> np.ndarray:
    count = SYNTHETIC_SECONDS * SAMPLE_RATE
    index = np.arange(count, dtype=np.float64)
    if control == "stable-ar-periodic":
        excitation = np.zeros(count, dtype=np.float64)
        excitation[::128] = 9000.0
        output = np.zeros(count, dtype=np.float64)
        for sample in range(count):
            previous = output[sample - 1] if sample else 0.0
            second = output[sample - 2] if sample > 1 else 0.0
            output[sample] = excitation[sample] + 1.72 * previous - 0.78 * second
        output *= 12000.0 / max(1.0, float(np.max(np.abs(output))))
    elif control == "white-noise":
        output = np.random.Generator(np.random.PCG64(0x5232)).normal(
            0.0, 5000.0, count
        )
    elif control == "impulse":
        output = np.zeros(count, dtype=np.float64)
        output[::SAMPLE_RATE] = 24000.0
    elif control == "two-component":
        phase_a = 2.0 * math.pi * (127.0 * index / SAMPLE_RATE)
        phase_b = 2.0 * math.pi * (
            311.0 * index / SAMPLE_RATE + 0.12 * np.sin(index / 19000.0)
        )
        output = 7800.0 * np.sin(phase_a) + 5200.0 * np.sin(phase_b)
    else:
        raise ValueError("unknown R-232 synthetic control")
    return np.clip(np.rint(output), -32768, 32767).astype(np.int16)


def _encode_arm(analysis, configuration: dict, rescoring: bool):
    encoder = configuration["encoder"]
    return encode_maf_source_filter_analysis(
        analysis,
        maximum_pulses_per_frame=encoder["maximum_pulses_per_frame"],
        rate_lambda_q20=encoder["rate_lambda_q20"],
        stream_seed=encoder["stream_seed"],
        basis_search_limit=encoder["basis_search_limit"],
        dictionary_bases_per_band=encoder["dictionary_bases_per_band"],
        dictionary_pulses_per_basis=encoder["dictionary_pulses_per_basis"],
        synthesis_aware_rdo=encoder["synthesis_aware_rdo"],
        pvq_guard_q12=encoder["pvq_guard_q12"],
        excitation_backend=encoder["excitation_backend"],
        excitation_subframe_size=encoder["excitation_subframe_size"],
        excitation_pulses=encoder["excitation_pulses"],
        excitation_quality_guard_q12=encoder["excitation_quality_guard_q12"],
        adaptive_quality_guard_q12=encoder["adaptive_quality_guard_q12"],
        excitation_basis_count=encoder["excitation_basis_count"],
        excitation_basis_pulses=encoder["excitation_basis_pulses"],
        excitation_basis_iterations=encoder["excitation_basis_iterations"],
        excitation_basis_search_limit=encoder["excitation_basis_search_limit"],
        excitation_basis_correction_pulses=(
            encoder["excitation_basis_correction_pulses"]
        ),
        decoder_domain_rescoring=rescoring,
    )


def _analyze(source: np.ndarray, sample_rate: int, configuration: dict, native_core: Path):
    analysis = configuration["analysis"]
    return analyze_maf_source_filter_source(
        source,
        sample_rate,
        block_size=analysis["block_size"],
        filter_order=analysis["filter_order"],
        parameter_lambda=analysis["parameter_lambda"],
        filter_basis_count=analysis["filter_basis_count"],
        filter_basis_iterations=analysis["filter_basis_iterations"],
        half_window=analysis["half_window"],
        band_count=analysis["band_count"],
        native_analyzer=NativeMain0Decoder(native_core),
    )


def _arm_record(label: str, encoded, source: np.ndarray, sample_rate: int, staging: Path):
    stream_path = staging / f"{label}.resonith"
    decoded_path = staging / f"{label}-decoded.wav"
    stream_path.write_bytes(encoded.payload)
    decoded_rate, decoded = decode_maf_source_filter_stream(encoded.payload)
    if decoded_rate != sample_rate or not np.array_equal(decoded, encoded.reconstruction):
        raise RuntimeError(f"R-232 {label} independent decode mismatch")
    write_pcm16_channels(decoded_path, sample_rate, decoded[:, None])
    error = source.astype(np.int64) - decoded.astype(np.int64)
    return {
        "bytes": len(encoded.payload),
        "decoded_wav_sha256": _sha256(decoded_path),
        "encoder_report": encoded.report,
        "metrics": compute_metrics(source[:, None], decoded[:, None], sample_rate, ("synthetic",)),
        "residual_energy_sse_proxy": int(error @ error),
        "stream_sha256": _sha256(stream_path),
    }


def _trace_alignment(legacy_report: dict, rescored_report: dict) -> dict[str, object]:
    legacy_cell = legacy_report["maf_cell"]
    rescored_cell = rescored_report["maf_cell"]
    legacy_winners = legacy_cell["selected_candidate_signatures"]
    rescored_winners = rescored_cell["selected_candidate_signatures"]
    legacy_choices = legacy_cell["candidate_choice_digests"]
    rescored_choices = rescored_cell["candidate_choice_digests"]
    if not (
        len(legacy_winners)
        == len(rescored_winners)
        == len(legacy_choices)
        == len(rescored_choices)
    ):
        raise RuntimeError("R-232 trace length mismatch")
    first_divergence = next(
        (index for index, pair in enumerate(zip(legacy_winners, rescored_winners)) if pair[0] != pair[1]),
        None,
    )
    required_count = len(legacy_choices) if first_divergence is None else first_divergence + 1
    prefix_equal = legacy_choices[:required_count] == rescored_choices[:required_count]
    if not prefix_equal:
        raise RuntimeError("R-232 candidate list diverged before its first winner divergence")
    return {
        "first_divergent_winner_subframe": first_divergence,
        "prefix_candidate_trace_identity": prefix_equal,
        "verified_choice_count": required_count,
    }


def _synthetic_admission(control: str, legacy: dict, rescored: dict) -> dict[str, object]:
    left = quality_axes(rescored["metrics"])
    right = quality_axes(legacy["metrics"])
    if set(left) != set(right):
        raise RuntimeError("R-232 synthetic metric applicability differs")
    regressions = []
    for name in sorted(left):
        direction, candidate = left[name]
        reference_direction, baseline = right[name]
        if direction != reference_direction:
            raise RuntimeError("R-232 synthetic metric direction differs")
        tolerance = 1.0e-12 * max(1.0, abs(baseline))
        regressed = (
            candidate + tolerance < baseline
            if direction == "max"
            else candidate > baseline + tolerance
        )
        if regressed:
            regressions.append(
                {"axis": name, "baseline": baseline, "candidate": candidate}
            )
    no_larger = rescored["bytes"] <= legacy["bytes"]
    decision_changes = rescored["encoder_report"]["maf_cell"][
        "decoder_domain_decision_changes"
    ]
    positive_witness = control != "stable-ar-periodic" or decision_changes > 0
    return {
        "bytes_no_larger": no_larger,
        "decision_changes": decision_changes,
        "metric_regressions": regressions,
        "passed": no_larger and not regressions and positive_witness,
        "positive_witness": positive_witness,
    }


def _run_legacy_identity(request: dict, authority: dict, files: dict[str, Path], staging: Path) -> dict:
    source_path = Path(request["source_path"]).resolve(strict=True)
    expected_source = request["source_sha256"].lower()
    if _sha256(source_path) != expected_source:
        raise RuntimeError("R-232 legacy identity source drift")
    if expected_source != authority["legacy_identity"]["source_sha256"]:
        raise RuntimeError("R-232 legacy identity source is unauthorized")
    sample_rate, channels = read_pcm16_channels(source_path)
    if channels.shape[1] != 1:
        raise RuntimeError("R-232 legacy identity source must be mono")
    configuration = json.loads(files["configuration"].read_text(encoding="utf-8"))
    analysis = _analyze(channels[:, 0], sample_rate, configuration, files["native_core"])
    encoded = _encode_arm(analysis, configuration, False)
    stream_path = staging / "legacy.resonith"
    decoded_path = staging / "legacy-decoded.wav"
    stream_path.write_bytes(encoded.payload)
    decoded_rate, decoded = decode_maf_source_filter_stream(encoded.payload)
    if decoded_rate != sample_rate or not np.array_equal(decoded, encoded.reconstruction):
        raise RuntimeError("R-232 legacy identity decoder mismatch")
    write_pcm16_channels(decoded_path, sample_rate, decoded[:, None])
    expected = authority["legacy_identity"]
    observed = {
        "decoded_wav_sha256": _sha256(decoded_path),
        "stream_bytes": stream_path.stat().st_size,
        "stream_sha256": _sha256(stream_path),
    }
    passed = all(observed[name] == expected[name] for name in observed)
    if not passed:
        raise RuntimeError("R-232 legacy R-120 identity changed")
    return {"expected": expected, "observed": observed, "passed": True}


def _run_control(request: dict, files: dict[str, Path], staging: Path) -> dict:
    control = request["control"]
    if control not in CONTROL_ORDER:
        raise RuntimeError("R-232 unauthorized control")
    source = _synthetic(control)
    source_path = staging / "source.wav"
    write_pcm16_channels(source_path, SAMPLE_RATE, source[:, None])
    configuration = json.loads(files["configuration"].read_text(encoding="utf-8"))
    analysis_started = time.perf_counter()
    analysis = _analyze(source, SAMPLE_RATE, configuration, files["native_core"])
    analysis_wall = time.perf_counter() - analysis_started
    arms = {}
    for label, rescoring in (("legacy", False), ("rescored", True)):
        started = time.perf_counter()
        encoded = _encode_arm(analysis, configuration, rescoring)
        arms[label] = _arm_record(label, encoded, source, SAMPLE_RATE, staging)
        arms[label]["encode_decode_metric_wall_seconds"] = time.perf_counter() - started
    trace = _trace_alignment(
        arms["legacy"]["encoder_report"],
        arms["rescored"]["encoder_report"],
    )
    admission = _synthetic_admission(control, arms["legacy"], arms["rescored"])
    if not admission["passed"]:
        raise RuntimeError(f"R-232 synthetic control rejected: {control}")
    return {
        "admission": admission,
        "analysis_wall_seconds": analysis_wall,
        "arms": arms,
        "source_sha256": _sha256(source_path),
        "trace": trace,
    }


def _worker(request_path: Path, expected_request_sha256: str, authority_path: Path, expected_authority_sha256: str) -> None:
    request = _read_bound_json(
        request_path,
        expected_request_sha256,
        "worker request",
    )
    if request.get("schema") != "resonith-r232-s15-worker-request-1":
        raise RuntimeError("R-232 worker request schema mismatch")
    authority, files = _validate_authority(authority_path, expected_authority_sha256)
    _load_runtime(authority)
    output = Path(request["output_directory"]).resolve(strict=False)
    parent = output.parent.resolve(strict=True)
    if output.exists():
        raise FileExistsError("R-232 worker output already exists")
    staging = output.with_name(output.name + f".staging-{os.getpid()}")
    if staging.exists():
        raise FileExistsError("R-232 worker staging already exists")
    staging.mkdir()
    source_identity = request.get("source_sha256")
    code_before = {
        "authority_sha256": expected_authority_sha256.lower(),
        "local_closure_sha256": hashlib.sha256(
            json.dumps(
                authority["local_modules"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        **{name: _sha256(path) for name, path in files.items()},
    }
    started = time.perf_counter()
    cpu_started = time.process_time()
    try:
        if request["kind"] == "legacy-identity":
            result = _run_legacy_identity(request, authority, files, staging)
        elif request["kind"] == "synthetic-control":
            result = _run_control(request, files, staging)
        else:
            raise RuntimeError("R-232 worker kind is unauthorized")
        _validate_authority(authority_path, expected_authority_sha256)
        if source_identity is not None and request["kind"] == "legacy-identity":
            if _sha256(Path(request["source_path"])) != source_identity:
                raise RuntimeError("R-232 source changed during work")
        report = {
            "cpu_seconds": time.process_time() - cpu_started,
            "identities": code_before,
            "kind": request["kind"],
            "result": result,
            "schema": "resonith-r232-s15-worker-report-1",
            "status": "PASS",
            "wall_seconds": time.perf_counter() - started,
        }
        _atomic_write_json(staging / "report.json", report)
        retained = _retained_files(staging)
        _atomic_write_json(
            staging / "receipt.json",
            {
                "retained_files": retained,
                "schema": "resonith-r232-s15-worker-receipt-1",
                "status": "PASS",
            },
        )
        staging.replace(output)
    except BaseException:
        _safe_remove_staging(staging, parent)
        raise


def _windows_api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryInformationJobObject.restype = wintypes.BOOL
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry32)]
    kernel.Thread32First.restype = wintypes.BOOL
    kernel.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry32)]
    kernel.Thread32Next.restype = wintypes.BOOL
    kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenThread.restype = wintypes.HANDLE
    kernel.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel.ResumeThread.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]; kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]; kernel.WaitForSingleObject.restype = wintypes.DWORD
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return kernel, psapi


def _raise_last(message: str) -> None:
    error = ctypes.get_last_error()
    raise OSError(error, f"{message}: Windows error {error}")


def _create_job(kernel, memory_limit: int = WORKER_MEMORY_LIMIT, *, active_process_limit: int = 1, job_memory_limit: int | None = None, call_results: list | None = None) -> int:
    job = kernel.CreateJobObjectW(None, None); call_results is not None and call_results.append({"call":"CreateJobObjectW","ok":bool(job)})
    if not job:
        _raise_last("CreateJobObjectW failed")
    limits = _JobExtendedLimit()
    limits.BasicLimitInformation.LimitFlags = 0x8 | 0x100 | 0x200 | 0x2000
    limits.BasicLimitInformation.ActiveProcessLimit = active_process_limit
    limits.ProcessMemoryLimit = memory_limit
    limits.JobMemoryLimit = memory_limit if job_memory_limit is None else job_memory_limit
    configured = bool(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits))); call_results is not None and call_results.append({"call":"SetInformationJobObject","ok":configured})
    if not configured: last_error = ctypes.get_last_error(); closed = bool(kernel.CloseHandle(job)); call_results is not None and call_results.append({"call":"CloseHandleAfterSetFailure","ok":closed}); raise OSError(last_error,f"SetInformationJobObject failed: Windows error {last_error}")
    return int(job)


def _resume_suspended_process(kernel, process_id: int) -> None:
    snapshot = kernel.CreateToolhelp32Snapshot(0x4, 0)
    if int(snapshot) == ctypes.c_void_p(-1).value:
        _raise_last("CreateToolhelp32Snapshot failed")
    resumed = 0
    try:
        entry = _ThreadEntry32(dwSize=ctypes.sizeof(_ThreadEntry32))
        more = kernel.Thread32First(snapshot, ctypes.byref(entry))
        if not more:
            _raise_last("Thread32First failed")
        while more:
            if entry.th32OwnerProcessID == process_id:
                thread = kernel.OpenThread(0x2, False, entry.th32ThreadID)
                if not thread:
                    _raise_last("OpenThread failed")
                try:
                    if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                        _raise_last("ResumeThread failed")
                    resumed += 1
                finally:
                    kernel.CloseHandle(thread)
            more = kernel.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    if resumed != 1:
        raise RuntimeError(f"R-232 expected one suspended worker thread, found {resumed}")


def _process_peak_working_set(psapi, handle: int) -> int:
    counters = _ProcessMemoryCounters(cb=ctypes.sizeof(_ProcessMemoryCounters))
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        _raise_last("GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def _job_peak_memory(kernel, job: int) -> int:
    limits = _JobExtendedLimit()
    returned = wintypes.DWORD()
    if not kernel.QueryInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits), ctypes.byref(returned)):
        _raise_last("QueryInformationJobObject failed")
    return int(limits.PeakJobMemoryUsed)
def _job_snapshot(kernel, job: int, label: str, started: float) -> dict[str, object]:
    """Return the authoritative live PID set and lifetime accounting."""; accounting, returned = _JobBasicAccounting(), wintypes.DWORD()
    if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), ctypes.byref(returned)): _raise_last("QueryInformationJobObject accounting failed")
    capacity = max(1, int(accounting.ActiveProcesses))
    while True:
        size = 8 + capacity * ctypes.sizeof(ctypes.c_size_t); storage = ctypes.create_string_buffer(size); ok = kernel.QueryInformationJobObject(job, 3, storage, size, ctypes.byref(returned)); assigned, listed = int.from_bytes(storage.raw[:4], "little"), int.from_bytes(storage.raw[4:8], "little")
        if ok and assigned <= capacity and listed == assigned:
            pids = list((ctypes.c_size_t * listed).from_buffer(storage, 8)); break
        if not ok and ctypes.get_last_error() != 234:
            _raise_last("QueryInformationJobObject process list failed")
        capacity = max(capacity * 2, assigned, listed, 1)
    return {"active_processes":int(accounting.ActiveProcesses),"elapsed_seconds":time.perf_counter()-started,"label":label,"pids":pids,"total_processes":int(accounting.TotalProcesses),"total_terminated_processes":int(accounting.TotalTerminatedProcesses)}
class _MonitoredFailure(RuntimeError):
    """One child failure carrying terminal resource evidence."""

    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence
def _r263_require(ok: object, message: str) -> None: ok or (_ for _ in ()).throw(RuntimeError(message))
def _logged_windows_call(log: list, name: str, function, arguments: tuple): result = function(*arguments); error = ctypes.get_last_error(); numeric = 0 if result is None else int(result); ok = numeric != ctypes.c_void_p(-1).value if name == "CreateToolhelp32Snapshot" else numeric != 0xFFFFFFFF if name == "ResumeThread" else bool(result) or name == "Thread32Next" and error == 18 or name == "QueryInformationJobObject" and error == 234; log.append({"call":name,"information_class":int(arguments[1]) if name == "QueryInformationJobObject" else None,"last_error":error,"ok":ok,"result":numeric}); ok or (_ for _ in ()).throw(ctypes.WinError(error)); return result
def _r263_attempt(function):
    try: return function(),None
    except BaseException as caught: return None,caught
class _WindowsCalls:
    def __init__(self, target, log: list) -> None: self.target,self.log = target,log
    def __getattr__(self, name: str): function = getattr(self.target,name); return lambda *arguments:_logged_windows_call(self.log,name,function,arguments)
def _consume_r263_progress(path: Path, offset: int, tail: bytes, records: list[dict[str, object]], started: float) -> tuple[int, bytes]:
    if not path.exists(): return offset, tail
    with path.open("rb") as source:
        source.seek(offset); incoming = source.read()
    offset += len(incoming); chunks = (tail + incoming).split(b"\n"); tail = chunks.pop()
    for line in chunks:
        _r263_require(line.startswith(b"R263_PROGRESS="),"R-263 outer progress stream contained ordinary bytes"); record = json.loads(line.removeprefix(b"R263_PROGRESS=")); _r263_require(record.get("schema") == "resonith-r263-progress-relay-1" and record.get("relay_sequence") == len(records)+1,"R-263 outer progress sequence drift"); inner = record.get("record",{}); _r263_require(inner.get("schema") == "resonith-r263-progress-1" and inner.get("producer") in {"stage0","stage1"} and (inner.get("producer") == "stage1" or inner.get("sequence") == record["relay_sequence"]),"R-263 outer progress schema/sequence drift")
        record["observed_seconds"] = time.perf_counter() - started; records.append(record)
    return offset, tail
def _validate_r263_progress(records: list[dict[str, object]]) -> None:
    phases = [record["record"]["phase"] for record in records]; required = ["stage0_preflight","stage1_full_closure","tests_start","tests_end","stage1_endpoint","stage0_endpoint"]; positions = [phases.index(phase) for phase in required]; _r263_require(set(phases) <= {*required,"isolated_start","isolated_end"} and all(phases.count(phase) == 1 for phase in required) and positions == sorted(positions) and next(record["record"].get("completed") for record in records if record["record"]["phase"] == "tests_end") == 26,"R-263 progress coverage/order drift"); events = [(record["record"].get("phase"),record["record"].get("label")) for record in records]; isolated = [event for event in events if event[0].startswith("isolated_")]; labels = {label for phase,label in isolated if phase == "isolated_start"}; _r263_require(labels == {"post-exit-drift","sentinel-invalidate","source-drift"} and len(isolated) == 6 and {label for _phase,label in isolated} == labels and all(isolated.count((phase,label)) == 1 and positions[2] < events.index(("isolated_start",label)) < events.index(("isolated_end",label)) < positions[3] for label in labels for phase in ("isolated_start","isolated_end")),"R-263 isolated progress coverage/order drift")
    deadlines = {"tests_start":24.0,"tests_end":62.0,"stage0_endpoint":68.0}; _r263_require(not any(next(record["observed_seconds"] for record in records if record["record"]["phase"] == phase) > deadline for phase,deadline in deadlines.items()),"R-263 progress phase exceeded its absolute ceiling")
def _r263_receipts(path: Path, context: dict[str, object]) -> dict[str, object]:
    lines = path.read_bytes().splitlines(); stage1 = [json.loads(line.removeprefix(b"R257_RECEIPT=")) for line in lines if line.startswith(b"R257_RECEIPT=")]; stage0 = [json.loads(line.removeprefix(b"R257_STAGE0_RECEIPT=")) for line in lines if line.startswith(b"R257_STAGE0_RECEIPT=")]; _r263_require(len(lines) == len(stage1) + len(stage0) == 2 and len(stage1) == len(stage0) == 1 and lines[0].startswith(b"R257_RECEIPT=") and lines[1].startswith(b"R257_STAGE0_RECEIPT="),"R-263 final receipt cardinality/order drift"); one, zero = stage1[0],stage0[0]; expected0 = str(Path(context["stage0_prefix"]).resolve(strict=False)); expected1 = str(Path(expected0).with_name(Path(expected0).name.removesuffix("-s0") + "-s1")); _r263_require(one.get("schema") == "resonith-r263-stage1-receipt-1" and zero.get("schema") == "resonith-r263-stage0-receipt-1" and one.get("status") == zero.get("status") == "PASS" and one.get("authority_sha256") == context["authority_sha256"] and zero.get("authority_sha256") == context["authority_sha256"] and one.get("role") == zero.get("role") == "focused" and zero.get("child_exit_code") == 0 and one.get("prefix") == zero.get("stage1") and zero.get("stage0",{}).get("path") == expected0 and zero.get("stage1",{}).get("path") == expected1 and isinstance(zero.get("default_cache_sha256"),str) and len(zero["default_cache_sha256"]) == 64 and bool(zero.get("startup_cache_paths")),"R-263 final receipt identity drift"); return {"entry_counts":{"imports":len(one.get("imports",[])),"loaded":len(one.get("loaded",[])),"namespace_baseline":len(one.get("namespace_baseline",[]))},"stage0_prefix":zero["stage0"],"stage0_receipt_sha256":hashlib.sha256(json.dumps(zero,sort_keys=True,separators=(",", ":")).encode()).hexdigest(),"stage1_prefix":one["prefix"],"stage1_receipt_sha256":hashlib.sha256(json.dumps(one,sort_keys=True,separators=(",", ":")).encode()).hexdigest()}
def _run_r263_monitored(command: list[str], suite_staging: Path, log_stem: Path, context: dict[str, object], environment: dict[str, str], receipt_path: Path) -> dict[str, object]:
    kernel, _psapi = _windows_api(); job = None; stdout_path, stderr_path = log_stem.with_suffix(".stdout.log"), log_stem.with_suffix(".stderr.log"); stdout_path.parent.mkdir(parents=True, exist_ok=True)
    process = None; assigned = closed = termination_attempted = termination_succeeded = False; error = None; calls, observations, progress = [], [], []; observed_kernel = _WindowsCalls(kernel,calls); offset, tail = 0, b""; started = time.perf_counter(); peak_job_memory = 0; retained_high_water = _directory_bytes(suite_staging)
    try:
        job = _create_job(kernel,512 << 20,active_process_limit=8,job_memory_limit=2 << 30,call_results=calls)
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            try:
                process = subprocess.Popen(command, cwd=PROJECT_ROOT, env=environment, stdout=stdout, stderr=stderr, shell=False, creationflags=0x4)
                assigned_result = bool(kernel.AssignProcessToJobObject(job,int(process._handle))); calls.append({"call":"AssignProcessToJobObject","ok":assigned_result}); _r263_require(assigned_result,ctypes.WinError(ctypes.get_last_error()))
                assigned = True; observations.append(_job_snapshot(observed_kernel, job, "assigned-before-resume", started)); _resume_suspended_process(observed_kernel, process.pid)
                while process.poll() is None:
                    before = len(progress); offset, tail = _consume_r263_progress(stderr_path, offset, tail, progress, started)
                    observations.extend(_job_snapshot(observed_kernel,job,f"progress-{index}",started) for index in range(before+1,len(progress)+1))
                    elapsed = time.perf_counter() - started; phases = {record["record"]["phase"] for record in progress}
                    if elapsed >= 24.0 and "tests_start" not in phases or elapsed >= 62.0 and "tests_end" not in phases or elapsed >= 68.0: raise TimeoutError("R-263 absolute phase/work deadline exceeded")
                    peak_job_memory = max(peak_job_memory,_job_peak_memory(observed_kernel,job)); retained_high_water = max(retained_high_water,_directory_bytes(suite_staging)); _r263_require(peak_job_memory <= 2 << 30 and retained_high_water <= 64 << 20 and stdout_path.stat().st_size <= 4 << 20 and stderr_path.stat().st_size <= 4 << 20,RuntimeError("R-263 resource ceiling exceeded"))
                    ceiling = 24.0 if "tests_start" not in phases else 62.0 if "tests_end" not in phases else 68.0; wait_result = int(kernel.WaitForSingleObject(int(process._handle),max(0,min(50,int((ceiling-(time.perf_counter()-started))*1000))))); calls.append({"call":"WaitForSingleObjectWork","ok":wait_result in {0,258},"result":wait_result}); _r263_require(wait_result in {0,258},RuntimeError("R-263 work wait failed"))
            except BaseException as caught: error = caught
            if process is not None and process.poll() is None:
                observations.append(_job_snapshot(observed_kernel, job, "before-termination", started))
                if assigned:
                    termination_attempted = True; terminated_result, caught = _r263_attempt(lambda:bool(kernel.TerminateJobObject(job,124))); termination_succeeded = caught is None and terminated_result is True; calls.append({"call":"TerminateJobObject","error":None if caught is None else type(caught).__name__,"ok":termination_succeeded}); error = error or caught or (None if termination_succeeded else ctypes.WinError(ctypes.get_last_error()))
                else: raise RuntimeError("R-263 suspended process was not assigned before containment")
            while assigned and time.perf_counter() - started < 73.0:
                snapshot = _job_snapshot(observed_kernel,job,"containment",started); observations.append(snapshot); peak_job_memory = max(peak_job_memory,_job_peak_memory(observed_kernel,job)); retained_high_water = max(retained_high_water,_directory_bytes(suite_staging))
                if not snapshot["pids"] and snapshot["active_processes"] == 0: break
                time.sleep(min(POLL_SECONDS,max(0.0,73.0-(time.perf_counter()-started))))
            before = len(progress); offset, tail = _consume_r263_progress(stderr_path, offset, tail, progress, started); observations.extend(_job_snapshot(observed_kernel,job,f"progress-{index}",started) for index in range(before+1,len(progress)+1))
        zero = bool(observations) and not observations[-1]["pids"] and observations[-1]["active_processes"] == 0
        final_pids = [] if zero or not observations else list(observations[-1]["pids"])
        opened = [(pid,int(kernel.OpenProcess(0x00100000,False,pid))) for pid in final_pids]; calls.extend({"call":"OpenProcess","ok":bool(handle),"pid":pid} for pid,handle in opened); wait_handles = [handle for _pid,handle in opened if handle]; error = error or (RuntimeError("R-263 survivor wait-handle open failed") if len(wait_handles) != len(opened) else None)
        if time.perf_counter() - started > 73.5: error = error or TimeoutError("R-263 Job close deadline exceeded")
        close_result = bool(kernel.CloseHandle(job)); calls.append({"call":"CloseHandleJob","ok":close_result}); error = error or (None if close_result else ctypes.WinError(ctypes.get_last_error())); error = error or (TimeoutError("R-263 Job close deadline exceeded") if time.perf_counter()-started > 73.5 else None)
        closed = True
        for handle in wait_handles:
            remaining = max(0, int((74.5 - (time.perf_counter() - started)) * 1000))
            wait_result = int(kernel.WaitForSingleObject(handle,remaining)); calls.append({"call":"WaitForSingleObject","ok":wait_result in {0,0x80},"result":wait_result}); error = error or (None if wait_result in {0,0x80} else TimeoutError("R-263 survivor wait exceeded"))
            handle_close = bool(kernel.CloseHandle(handle)); calls.append({"call":"CloseHandleProcess","ok":handle_close}); error = error or (None if handle_close else ctypes.WinError(ctypes.get_last_error())); error = error or (TimeoutError("R-263 survivor wait exceeded") if time.perf_counter()-started > 74.5 else None)
        if tail: error = error or RuntimeError("R-263 truncated outer progress record")
        if error is None: _validate_r263_progress(progress)
        if process is not None: process.poll()
        if process is None or process.returncode != 0: error = error or RuntimeError(f"R-263 Stage-0 tree exited {None if process is None else process.returncode}")
        if not zero or observations[-1]["total_processes"] != 34: error = error or RuntimeError("R-263 zero-survivor or exact process-ledger proof failed")
        receipts = _r263_receipts(stdout_path,context) if error is None else None
    except BaseException as caught: error = error or caught
    finally:
        if job is not None and not closed:
            if assigned and not termination_attempted:
                termination_attempted = True; terminated_result, caught = _r263_attempt(lambda:bool(kernel.TerminateJobObject(job,124))); termination_succeeded = caught is None and terminated_result is True; calls.append({"call":"TerminateJobObject","error":None if caught is None else type(caught).__name__,"ok":termination_succeeded}); error = error or caught or (None if termination_succeeded else ctypes.WinError(ctypes.get_last_error()))
            elif process is not None and process.poll() is None and not termination_attempted: termination_attempted = True; _result, caught = _r263_attempt(process.kill); termination_succeeded = caught is None; calls.append({"call":"Popen.kill","error":None if caught is None else type(caught).__name__,"ok":termination_succeeded}); error = error or caught; wait_result, caught = _r263_attempt(lambda:int(kernel.WaitForSingleObject(int(process._handle),max(0,int((74.5-(time.perf_counter()-started))*1000))))); wait_ok = caught is None and wait_result in {0,0x80}; calls.append({"call":"WaitForSingleObjectUnassigned","error":None if caught is None else type(caught).__name__,"ok":wait_ok,"result":wait_result}); error = error or caught or (None if wait_ok else TimeoutError("R-263 unassigned process wait exceeded"))
            close_result = bool(kernel.CloseHandle(job)); calls.append({"call":"CloseHandleJob","ok":close_result}); error = error or (None if close_result else ctypes.WinError(ctypes.get_last_error())); closed = True
    elapsed = time.perf_counter() - started; retained_high_water = max(retained_high_water,_directory_bytes(suite_staging)); stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0; stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0; error = error or (RuntimeError("R-263 final resource ceiling exceeded") if retained_high_water > 64 << 20 or stdout_bytes > 4 << 20 or stderr_bytes > 4 << 20 else None); error = error or (TimeoutError("R-263 receipt publication safety margin exceeded") if elapsed > 74.5 else None)
    evidence = {**context,"active_process_limit":8,"assignment_before_resume":assigned,"command":command,"creation_flags":4,"error":None if error is None else f"{type(error).__name__}: {error}","exit_code":None if process is None else process.returncode,"expected_total_processes":34,"final_receipts":receipts if "receipts" in locals() else None,"job_limit_flags":0x2308,"job_memory_limit_bytes":2 << 30,"job_observations":observations,"job_peak_memory_bytes":peak_job_memory,"kill_on_close":True,"process_memory_limit_bytes":512 << 20,"progress":progress,"retained_high_water_bytes":retained_high_water,"schema":"resonith-r263-stage-minus-one-receipt-1","status":"PASS" if error is None else "FAIL","stderr_bytes":stderr_bytes,"stderr_sha256":_sha256(stderr_path) if stderr_path.exists() else None,"stdout_bytes":stdout_bytes,"stdout_sha256":_sha256(stdout_path) if stdout_path.exists() else None,"terminate_calls":int(termination_attempted),"termination_succeeded":termination_succeeded,"wall_seconds":elapsed,"windows_calls":calls}
    _atomic_write_json(receipt_path,evidence,deadline=started+75.0)
    if error is not None: raise _MonitoredFailure(str(error), evidence) from error
    return evidence
def _run_monitored(
    command: list[str],
    suite_staging: Path,
    log_stem: Path,
    *,
    context: dict[str, object] | None = None,
    environment: dict[str, str] | None = None,
    memory_limit: int = WORKER_MEMORY_LIMIT,
    wall_limit: float = WORKER_WALL_LIMIT,
    retained_limit: int = RETAINED_LIMIT,
    output_limit: int = OUTPUT_CAPTURE_LIMIT,
    active_process_limit: int = 1,
    job_memory_limit: int | None = None,
    r263_receipt: Path | None = None,
) -> dict[str, object]:
    if r263_receipt is not None:
        return _run_r263_monitored(command, suite_staging, log_stem, context or {}, environment or os.environ.copy(), r263_receipt)
    kernel, psapi = _windows_api()
    job = _create_job(kernel, memory_limit, active_process_limit=active_process_limit, job_memory_limit=job_memory_limit)
    process = None
    assigned = False
    caught: BaseException | None = None
    started = time.perf_counter()
    peak_working_set = 0
    peak_job_memory = 0
    disk_high_water = _directory_bytes(suite_staging)
    stdout_path = log_stem.with_suffix(".stdout.log")
    stderr_path = log_stem.with_suffix(".stderr.log")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=PROJECT_ROOT,
                    env=environment if environment is not None else os.environ.copy(),
                    stdout=stdout,
                    stderr=stderr,
                    shell=False,
                    creationflags=0x4,
                )
                process_handle = int(process._handle)
                if not kernel.AssignProcessToJobObject(job, process_handle):
                    _raise_last("AssignProcessToJobObject failed")
                assigned = True
                _resume_suspended_process(kernel, process.pid)
                while process.poll() is None:
                    peak_working_set = max(
                        peak_working_set,
                        _process_peak_working_set(psapi, process_handle),
                    )
                    peak_job_memory = max(
                        peak_job_memory,
                        _job_peak_memory(kernel, job),
                    )
                    disk_high_water = max(
                        disk_high_water,
                        _directory_bytes(suite_staging),
                    )
                    if peak_working_set > memory_limit or peak_job_memory > (memory_limit if job_memory_limit is None else job_memory_limit):
                        raise MemoryError("R-232 worker exceeded its hard memory ceiling")
                    if disk_high_water > retained_limit:
                        raise OSError("R-232 retained/working evidence exceeded its ceiling")
                    if stdout_path.stat().st_size > output_limit or stderr_path.stat().st_size > output_limit:
                        raise OSError("R-232 worker log exceeded its bounded capture")
                    if time.perf_counter() - started > wall_limit:
                        raise TimeoutError("R-232 worker exceeded its wall ceiling")
                    time.sleep(POLL_SECONDS)
            except BaseException as error:
                caught = error
            finally:
                if process is not None and process.poll() is None:
                    if assigned:
                        if not kernel.TerminateJobObject(job, 1):
                            caught = caught or OSError(
                                ctypes.get_last_error(),
                                "R-232 TerminateJobObject failed",
                            )
                    else:
                        process.kill()
                    try:
                        process.wait(timeout=30)
                    except BaseException as error:
                        caught = caught or error
                        process.kill()
                        process.wait(timeout=30)

        wall_seconds = time.perf_counter() - started
        if process is not None:
            process_handle = int(process._handle)
            peak_working_set = max(
                peak_working_set,
                _process_peak_working_set(psapi, process_handle),
            )
            peak_job_memory = max(
                peak_job_memory,
                _job_peak_memory(kernel, job),
            )
        disk_high_water = max(disk_high_water, _directory_bytes(suite_staging))
        stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
        stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
        r257_receipt = r257_receipt_error = None; expected_prefix = (context or {}).get("prefix_receipt")
        if expected_prefix is not None and stdout_path.exists():
            try:
                signed_prefix = {key: value for key, value in expected_prefix.items() if key != "sha256"}
                if expected_prefix.get("child_command") != command or expected_prefix.get("sha256") != hashlib.sha256(json.dumps(signed_prefix, sort_keys=True, separators=(",", ":")).encode()).hexdigest(): raise RuntimeError("R-257 worker launch receipt was not authenticated")
                receipt_lines = [line.removeprefix(b"R257_RECEIPT=") for line in stdout_path.read_bytes().splitlines() if line.startswith(b"R257_RECEIPT=")]
                if len(receipt_lines) != 1: raise RuntimeError("R-257 worker emitted other than one receipt")
                r257_receipt = json.loads(receipt_lines[0]); expected_identity = {key:expected_prefix[key] for key in ("file_id","final_path","path","volume")}
                if r257_receipt.get("prefix") != expected_identity or r257_receipt.get("authority_sha256") != expected_prefix["authority_sha256"] or r257_receipt.get("role") != "controller": raise RuntimeError("R-257 worker receipt identity mismatch")
            except BaseException as error: r257_receipt_error = f"{type(error).__name__}: {error}"
        evidence = {
            **(context or {}),
            "exit_code": process.returncode if process is not None else None,
            "job_peak_memory_bytes": peak_job_memory,
            "memory_limit_bytes": memory_limit,
            "process_peak_working_set_bytes": peak_working_set,
            "retained_limit_bytes": retained_limit,
            "r257_receipt": r257_receipt,
            "staging_disk_high_water_bytes": disk_high_water,
            "stderr_bytes": stderr_bytes,
            "stderr_excerpt": (
                stderr_path.read_bytes()[-4096:].decode("utf-8", errors="replace")
                if stderr_path.exists()
                else ""
            ),
            "stderr_sha256": _sha256(stderr_path) if stderr_path.exists() else None,
            "stdout_bytes": stdout_bytes,
            "stdout_excerpt": (
                stdout_path.read_bytes()[-4096:].decode("utf-8", errors="replace")
                if stdout_path.exists()
                else ""
            ),
            "stdout_sha256": _sha256(stdout_path) if stdout_path.exists() else None,
            "wall_limit_seconds": wall_limit,
            "wall_seconds": wall_seconds,
        }
        post_exit_error = None
        if peak_working_set > memory_limit or peak_job_memory > (memory_limit if job_memory_limit is None else job_memory_limit):
            post_exit_error = "R-232 worker exceeded its hard memory ceiling"
        elif disk_high_water > retained_limit:
            post_exit_error = "R-232 retained/working evidence exceeded its ceiling"
        elif stdout_bytes > output_limit or stderr_bytes > output_limit:
            post_exit_error = "R-232 worker log exceeded its bounded capture"
        elif wall_seconds > wall_limit:
            post_exit_error = "R-232 worker exceeded its wall ceiling"
        elif process is None or process.returncode != 0:
            post_exit_error = f"R-232 worker exited {evidence['exit_code']}"
        elif r257_receipt_error is not None:
            post_exit_error = r257_receipt_error
        if caught is not None or post_exit_error is not None:
            message = (
                f"{type(caught).__name__}: {caught}"
                if caught is not None
                else str(post_exit_error)
            )
            raise _MonitoredFailure(message, evidence) from caught
        return evidence
    finally:
        if process is not None and process.poll() is None:
            if assigned:
                kernel.TerminateJobObject(job, 1)
            else:
                process.kill()
            process.wait(timeout=30)
        kernel.CloseHandle(job)


def _execute_suite_transaction(
    output: Path,
    authority_sha256: str,
    tasks: list[dict[str, object]],
    execute_task,
) -> None:
    output = output.resolve(strict=False)
    parent = output.parent.resolve(strict=True)
    failure = output.with_name(output.name + "-failure.json")
    if output.exists() or failure.exists():
        raise FileExistsError("R-232 terminal output/failure already exists")
    orphans = sorted(parent.glob(output.name + ".staging-*"))
    if orphans:
        raise FileExistsError("R-232 orphan suite staging blocks execution")
    staging = output.with_name(output.name + f".staging-{os.getpid()}")
    staging_created = False
    runs = []
    current_task = None
    try:
        staging.mkdir()
        staging_created = True
        (staging / "runs").mkdir()
        (staging / "requests").mkdir()
        (staging / "logs").mkdir()
        for index, task in enumerate(tasks):
            current_task = task
            run = execute_task(staging, index, task)
            runs.append(run)
            _atomic_write_json(
                staging / "run-index.json",
                {
                    "completed": runs,
                    "next_index": index + 1,
                    "schema": "resonith-r232-s15-run-index-1",
                    "status": (
                        "RUNNING" if index + 1 < len(tasks) else "COMPLETE"
                    ),
                },
            )
        if _directory_bytes(staging) > RETAINED_LIMIT:
            raise OSError("R-232 retained suite exceeded 8 GiB")
        _atomic_write_json(
            staging / "receipt.json",
            {
                "authority_sha256": authority_sha256.lower(),
                "retained_files": _retained_files(staging),
                "runs": runs,
                "schema": "resonith-r232-s15-control-suite-receipt-1",
                "status": "PASS",
            },
        )
        staging.replace(output)
    except BaseException as error:
        run_index = staging / "run-index.json"
        record = {
            "authority_sha256": authority_sha256.lower(),
            "completed_runs": runs,
            "error": f"{type(error).__name__}: {error}",
            "failing_task": current_task,
            "resource_evidence": getattr(error, "evidence", None),
            "run_index_sha256": _sha256(run_index) if run_index.exists() else None,
            "runner_sha256": _sha256(Path(__file__).resolve(strict=True)),
            "schema": "resonith-r232-s15-control-suite-failure-2",
            "status": "FAIL",
        }
        publication_error = None
        try:
            _atomic_write_json(failure, record)
        except BaseException as receipt_error:
            publication_error = receipt_error
        finally:
            if staging_created:
                _safe_remove_staging(staging, parent)
        if publication_error is not None:
            raise publication_error from error
        raise


def _validate_completed_worker(
    run_output: Path,
    resources: dict[str, object],
    authority_path: Path,
    expected_authority_sha256: str,
    *,
    kind: str,
    name: str,
    request_sha256: str,
) -> dict[str, object]:
    """Revalidate parent authority and one published worker transaction."""

    try:
        # The parent must distrust both its own pre-launch view and the child's
        # self-check after the bounded process exits.
        _validate_authority(authority_path, expected_authority_sha256)
        receipt_path = run_output / "receipt.json"
        receipt_sha256 = _sha256(receipt_path)
        receipt = _read_bound_json(
            receipt_path,
            receipt_sha256,
            "worker receipt",
        )
        if (
            receipt.get("schema") != "resonith-r232-s15-worker-receipt-1"
            or receipt.get("status") != "PASS"
        ):
            raise RuntimeError("R-232 worker receipt is not a schema-bound PASS")
        declared = receipt.get("retained_files")
        if not isinstance(declared, list):
            raise RuntimeError("R-232 worker retained-file manifest is invalid")
        actual = [
            record
            for record in _retained_files(run_output)
            if record["path"] != "receipt.json"
        ]
        if declared != actual:
            raise RuntimeError("R-232 worker retained-file manifest drift")
        report_path = run_output / "report.json"
        report_sha256 = _sha256(report_path)
        report = _read_bound_json(report_path, report_sha256, "worker report")
        if (
            report.get("schema") != "resonith-r232-s15-worker-report-1"
            or report.get("status") != "PASS"
            or report.get("kind") != kind
        ):
            raise RuntimeError("R-232 worker report identity mismatch")
        return {
            "kind": kind,
            "name": name,
            "report_sha256": report_sha256,
            "request_sha256": request_sha256,
            "resources": resources,
            "worker_receipt_sha256": receipt_sha256,
        }
    except BaseException as error:
        raise _MonitoredFailure(
            f"R-232 post-worker validation failed: {type(error).__name__}: {error}",
            {
                **resources,
                "post_worker_validation_error": (
                    f"{type(error).__name__}: {error}"
                ),
            },
        ) from error


def _claim_prefix_receipt(receipt: dict[str, object], used: set[tuple[str, object]]) -> None:
    claims = (("path", receipt["path"]), ("identity", (receipt["volume"], receipt["file_id"])), ("sha256", receipt["sha256"]))
    if any(claim in used for claim in claims): raise RuntimeError("R-257 worker prefix receipt was reused")
    used.update(claims)
def _controller(arguments) -> None:
    authority_path = arguments.authority.resolve(strict=True); authority, _files = _validate_authority(authority_path,arguments.expected_authority_sha256); legacy_source = arguments.legacy_identity_source.resolve(strict=True); legacy_source_sha256 = _sha256(legacy_source)
    if legacy_source_sha256 != authority["legacy_identity"]["source_sha256"]: raise RuntimeError("R-232 legacy identity source mismatch")
    tasks = [{"control":None,"kind":"legacy-identity","name":"legacy-identity"}]+[{"control":control,"kind":"synthetic-control","name":control} for control in CONTROL_ORDER]
    used_prefix_receipts: set[tuple[str, object]] = set()
    if authority["schema"] == "resonith-r257-source-execution-authority-1":
        controller_claim = {"file_id": int(os.environ["RESONITH_R257_PREFIX_FILE_ID"]), "final_path": os.environ["RESONITH_R257_PREFIX_FINAL_PATH"], "path": str(Path(sys.pycache_prefix).resolve()), "role": "controller", "volume": int(os.environ["RESONITH_R257_PREFIX_VOLUME"])}
        controller_claim["sha256"] = hashlib.sha256(json.dumps(controller_claim, sort_keys=True, separators=(",", ":")).encode()).hexdigest(); _claim_prefix_receipt(controller_claim, used_prefix_receipts)

    def execute(staging: Path, index: int, task: dict[str, object]) -> dict:
        name, kind, control = str(task["name"]),str(task["kind"]),task["control"]; run_output = staging/"runs"/f"{index:02d}-{name}"
        request = {
            "control": control,
            "kind": kind,
            "output_directory": str(run_output),
            "schema": "resonith-r232-s15-worker-request-1",
            "source_path": str(legacy_source) if kind == "legacy-identity" else None,
            "source_sha256": legacy_source_sha256 if kind == "legacy-identity" else None,
        }
        request_path = staging/"requests"/f"{index:02d}-{name}.json"; _atomic_write_json(request_path,request); request_sha256 = _sha256(request_path); run_index = staging/"run-index.json"; worker_arguments = ["--worker-request",str(request_path),"--expected-worker-request-sha256",request_sha256,"--authority",str(authority_path),"--expected-authority-sha256",arguments.expected_authority_sha256]; worker_prefix = worker_handle = worker_identity = environment = None
        if authority["schema"] == "resonith-r257-source-execution-authority-1":
            bootstrap = sys.modules.get("__main__"); prepare, finish = getattr(bootstrap,"worker_child",None),getattr(bootstrap,"finish_child",None)
            if not callable(prepare) or not callable(finish): raise RuntimeError("R-257 worker bootstrap helpers are unavailable")
            worker_prefix, state = prepare(authority_path,arguments.expected_authority_sha256,worker_arguments)
            command, environment, worker_handle, worker_identity = state
            prefix_receipt = {"authority_sha256":arguments.expected_authority_sha256.lower(),"child_command":command,"file_id":worker_identity[1],"final_path":worker_identity[2],"path":str(worker_prefix),"volume":worker_identity[0]}; prefix_receipt["sha256"] = hashlib.sha256(json.dumps(prefix_receipt,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
            _claim_prefix_receipt(prefix_receipt, used_prefix_receipts)
        else: command = [sys.executable,str(Path(__file__).resolve(strict=True)),*worker_arguments]; prefix_receipt = None
        try:
            context = {"authority_sha256":arguments.expected_authority_sha256.lower(),"prefix_receipt":prefix_receipt,"request_sha256":request_sha256,"run_index_sha256":_sha256(run_index) if run_index.exists() else None,"runner_sha256":_sha256(Path(__file__).resolve(strict=True)),"task_name":name}
            resources = _run_monitored(command,staging,staging/"logs"/f"{index:02d}-{name}",context=context,environment=environment)
        finally:
            if worker_prefix is not None:
                finish(worker_prefix, worker_handle, worker_identity)
        return _validate_completed_worker(run_output,resources,authority_path,arguments.expected_authority_sha256,kind=kind,name=name,request_sha256=request_sha256)
    _execute_suite_transaction(arguments.output_directory,arguments.expected_authority_sha256,tasks,execute)
def _r263_focused_admission(arguments) -> None:
    authority_path = arguments.authority.resolve(strict=True); authority, files = _validate_authority(authority_path,arguments.expected_authority_sha256); source = authority["source_execution"]["r263_launcher_source"]; original = list(sys.orig_argv)
    _r263_require("-c" in original and original[original.index("-c")+1] == source and hashlib.sha256(source.encode()).hexdigest() == authority["source_execution"]["r263_launcher_sha256"],"R-263 inline launcher identity drift")
    prefix, receipt = arguments.stage0_prefix.resolve(strict=False), arguments.stage_minus_one_receipt.resolve(strict=False)
    artifact_root = (PROJECT_ROOT/"artifacts").resolve(strict=True); _r263_require(not prefix.exists() and prefix.parent.resolve(strict=True) == artifact_root and not receipt.exists() and receipt.parent.parent.resolve(strict=True) == artifact_root and receipt.parent.is_dir() and not receipt.parent.is_symlink() and not getattr(receipt.parent.lstat(),"st_file_attributes",0) & 0x400 and not any(receipt.parent.iterdir()),"R-263 admission paths are not fresh, empty, or contained")
    command = [sys.executable, "-I", "-S", "-B", "-X", f"pycache_prefix={prefix}", str(files["bootstrap"]), "--stage0-prefix", str(prefix), "--authority", str(authority_path), "--expected-authority-sha256", arguments.expected_authority_sha256, "--role", "focused", "--target"]
    environment = {key:value for key,value in os.environ.items() if not key.upper().startswith("PYTHON") and key != "RESONITH_R257_STAGE1"}
    environment.update({"LLVM_PROFILE_FILE":str(receipt.parent/"r263-%p.profraw"), "MKL_NUM_THREADS":"1", "NUMEXPR_NUM_THREADS":"1", "OMP_NUM_THREADS":"1", "OPENBLAS_NUM_THREADS":"1", "PYTHONDONTWRITEBYTECODE":"1", "PYTHONHASHSEED":"0", "PYTHONPYCACHEPREFIX":str(prefix), "RESONITH_R263_PROGRESS":"1", "RESONITH_R263_RUN_ROOT":str(receipt.parent), "TEMP":str(receipt.parent), "TMP":str(receipt.parent), "TMPDIR":str(receipt.parent)})
    context = {"authority_path":str(authority_path), "authority_sha256":arguments.expected_authority_sha256.lower(), "bootstrap_sha256":authority["files"]["bootstrap"]["sha256"], "gate_sha256":authority["files"]["gate"]["sha256"], "launcher_sha256":authority["source_execution"]["r263_launcher_sha256"], "outer_command":original, "python_executable":str(Path(sys.executable).resolve(strict=True)), "r263_remediation_sha256":authority["files"]["r263_remediation"]["sha256"], "stage0_prefix":str(prefix)}
    _run_monitored(command, receipt.parent, receipt.with_suffix(""), context=context, environment=environment, r263_receipt=receipt)
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-suite", action="store_true")
    parser.add_argument("--r263-focused-admission", action="store_true")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--legacy-identity-source", type=Path)
    parser.add_argument("--stage0-prefix", type=Path)
    parser.add_argument("--stage-minus-one-receipt", type=Path)
    parser.add_argument("--worker-request", type=Path)
    parser.add_argument("--expected-worker-request-sha256")
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--expected-authority-sha256", required=True)
    arguments = parser.parse_args()
    if arguments.r263_focused_admission:
        if arguments.control_suite or arguments.worker_request is not None or arguments.output_directory is not None or arguments.legacy_identity_source is not None or arguments.expected_worker_request_sha256 is not None or arguments.stage0_prefix is None or arguments.stage_minus_one_receipt is None or any(sys.argv.count(name) != 1 for name in ("--r263-focused-admission","--stage0-prefix","--stage-minus-one-receipt")):
            raise ValueError("R-263 admission role is incomplete or mixed")
        _r263_focused_admission(arguments)
        return
    if arguments.worker_request is not None:
        if arguments.control_suite or arguments.output_directory is not None:
            raise ValueError("R-232 worker/controller roles are exclusive")
        if arguments.expected_worker_request_sha256 is None:
            raise ValueError("R-232 worker requires its request SHA-256")
        _worker(
            arguments.worker_request,
            arguments.expected_worker_request_sha256,
            arguments.authority,
            arguments.expected_authority_sha256,
        )
        return
    if not arguments.control_suite:
        raise ValueError("R-232 real-audio mode remains audit-blocked")
    if arguments.output_directory is None or arguments.legacy_identity_source is None:
        raise ValueError("R-232 control suite requires output and legacy source")
    _controller(arguments)


if __name__ == "__main__":
    main()
