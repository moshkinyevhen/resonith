"""R-224 isolated execution of the pre-S11 direct-Truth producer.

This evidence controller does not alter the codec.  It materializes commit
``ca87dec`` into a fresh tree, runs its real direct-Truth encoder once per
registered R-221 input, decodes the bytes with the frozen native Core, and
requires byte-for-byte and PCM-for-PCM identity with the retained S11 fallback.

The authority and stopping contract is frozen in
``docs/reviews/R224_S13_PHASE_ECONOMY_ORACLE_PREFLIGHT_2026-08-02.md``.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import time
import uuid
import wave
import zipfile


REPOSITORY = Path(__file__).resolve().parents[1]
PYTHON = REPOSITORY / "artifacts/tools/python-3.14.6-amd64/python.exe"
GIT = REPOSITORY / "artifacts/tools/mingit-2.55.0.3-64-bit/cmd/git.exe"
MANIFEST = REPOSITORY / "experiments/fixtures/r216_s12_registered_manifest.json"
R221_ROOT = REPOSITORY / "artifacts/r221-s12-bounded-rate-direct"
NATIVE_CORE = REPOSITORY / "build/cpp23-clang22-ninja/libresonith_core_shared.dll"
PREFLIGHT = REPOSITORY / "docs/reviews/R224_S13_PHASE_ECONOMY_ORACLE_PREFLIGHT_2026-08-02.md"

SCHEMA = "resonith-r224-s13-predecessor-comparison-1"
WORK_SCHEMA = "resonith-r224-s13-predecessor-work-1"
RECEIPT_SCHEMA = "resonith-r224-s13-predecessor-item-receipt-1"
HISTORICAL_REF = "ca87dec"
EXPECTED_HISTORICAL_COMMIT = "ca87decf7d4b255bae11ce980e6f4be6fe3065f0"
EXPECTED_HISTORICAL_TREE = "ca6b528b9024109c118aec537ce4488ceb5cd2eb"
EXPECTED_MANIFEST_SHA256 = "551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0"
EXPECTED_R221_INDEX_SHA256 = "ed1d8e5505ccf0fe0af4b59725e1f5e1c30fefc67218aff9b3608b9046140ecd"
EXPECTED_R221_AGGREGATE_SHA256 = "f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf"
EXPECTED_R221_RUN_IDENTITY = "470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c"
EXPECTED_NATIVE_CORE_SHA256 = "f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed"
EXPECTED_PREFLIGHT_SHA256 = "a92b3ad2f04719c59cb1364294db1e4dc8d05a0872d1d590c85ef7920e1ca134"
EXPECTED_ITEM_COUNT = 19
GIB = 1024**3
MIB = 1024**2

FROZEN_CONFIG = {
    "entropy_backend": "bounded",
    "transform_backend": "fixed",
    "density_backend": "adaptive",
    "selection_backend": "energy",
    "frame_whitening": 0.0,
    "band_whitening": 0.0,
}

UNCHANGED_PROJECT_FILES = (
    "reference/maf_p0/lapped_oracle.py",
    "reference/maf_p0/native_core.py",
    "reference/maf_p0/wav_io.py",
    "native/src/lapped.cpp",
    "native/include/resonith/lapped.h",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ) + "\n").encode("utf-8")


def write_atomic(path: Path, payload: bytes) -> None:
    """Publish one complete file without adopting a partial prior result."""

    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: object) -> None:
    write_atomic(path, json_bytes(value))


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_digest(value: object) -> str:
    return sha256_bytes(json_bytes(value))


def validate_execution_argv(
    actual: object, actual_digest: object, request: dict[str, object]
) -> None:
    expected = request.get("execution_argv")
    expected_digest = request.get("execution_argv_sha256")
    if (not isinstance(expected, list) or not expected
            or not all(isinstance(value, str) for value in expected)
            or expected_digest != canonical_digest(expected)
            or actual != expected or actual_digest != expected_digest
            or canonical_digest(actual) != actual_digest):
        raise RuntimeError("execution argv authority drift")


def validate_aggregate_argv_rows(
    rows: list[dict[str, object]], requests: dict[str, dict[str, object]]
) -> None:
    if {str(row.get("item_id")) for row in rows} != set(requests):
        raise RuntimeError("aggregate argv membership drift")
    for row in rows:
        request = requests[str(row["item_id"])]
        validate_execution_argv(
            row.get("execution_argv"), row.get("execution_argv_sha256"), request
        )


def _is_reparse(path: Path) -> bool:
    info = path.lstat()
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def require_reparse_free(path: Path, *, hardlink_check: bool = True) -> None:
    """Walk a checked lexical tree without following a reparse entry."""

    root = lexical_absolute(path)
    root_info = root.lstat()
    if bool(getattr(root_info, "st_file_attributes", 0) & 0x400):
        raise RuntimeError(f"reparse point rejected: {root}")
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                target = Path(entry.path)
                info = entry.stat(follow_symlinks=False)
                if bool(getattr(info, "st_file_attributes", 0) & 0x400):
                    raise RuntimeError(f"reparse point rejected: {target}")
                if entry.is_dir(follow_symlinks=False):
                    stack.append(target)
                elif entry.is_file(follow_symlinks=False):
                    if hardlink_check and target.lstat().st_nlink != 1:
                        raise RuntimeError(f"hard link rejected: {target}")
                else:
                    raise RuntimeError(f"non-regular filesystem object rejected: {target}")


def lexical_absolute(path: Path) -> Path:
    """Make a local drive path absolute without resolving a link or junction."""

    raw = os.fspath(path)
    raw_parts = Path(raw).parts
    if any(part in {".", ".."} for part in raw_parts):
        raise ValueError(f"relative path component rejected: {path}")
    if raw.startswith(("\\\\", "\\\\?\\", "\\\\.\\")):
        raise ValueError(f"UNC or device path rejected: {path}")
    absolute = path if path.is_absolute() else path.absolute()
    if (not absolute.is_absolute() or len(absolute.drive) != 2
            or absolute.drive[1] != ":" or absolute.root not in {"\\", "/"}):
        raise ValueError(f"unsupported output path grammar: {path}")
    return absolute


def require_ancestry_reparse_free(path: Path) -> None:
    """Check only the existing path ancestry, never an unrelated sibling tree."""

    lexical = lexical_absolute(path)
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current = current / part
        if os.path.lexists(current) and _is_reparse(current):
            raise RuntimeError(f"reparse point rejected in ancestry: {current}")


def safe_archive_member(name: str) -> PurePosixPath:
    """Return one normalized archive name or reject traversal/ADS aliases."""

    if not name or "\\" in name or "\x00" in name or ":" in name:
        raise ValueError(f"unsafe archive member: {name!r}")
    raw_parts = name.split("/")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError(f"unsafe archive member: {name!r}")
    return path


def extract_git_archive(archive: Path, destination: Path) -> list[dict[str, object]]:
    """Extract a Git ZIP with explicit type, alias, and containment checks."""

    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=False)
    require_reparse_free(destination)
    seen: set[str] = set()
    inventory: list[dict[str, object]] = []
    with zipfile.ZipFile(archive, "r") as source:
        for member in source.infolist():
            logical = safe_archive_member(member.filename.rstrip("/"))
            alias = logical.as_posix().casefold()
            if alias in seen:
                raise ValueError(f"duplicate archive alias: {logical}")
            seen.add(alias)
            mode = member.external_attr >> 16
            kind = stat.S_IFMT(mode)
            is_directory = member.is_dir()
            if kind not in ({stat.S_IFDIR, 0} if is_directory else {stat.S_IFREG, 0}):
                raise ValueError(f"non-regular archive member: {logical}")
            target = destination.joinpath(*logical.parts)
            resolved_parent = target.parent.resolve()
            if destination.resolve() not in (resolved_parent, *resolved_parent.parents):
                raise ValueError(f"archive containment failure: {logical}")
            if is_directory:
                target.mkdir(parents=True, exist_ok=False)
                digest = None
                size = 0
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                payload = source.read(member)
                if len(payload) != member.file_size:
                    raise RuntimeError(f"archive member truncated: {logical}")
                with target.open("xb") as output:
                    output.write(payload)
                digest = sha256_bytes(payload)
                size = len(payload)
            inventory.append({
                "path": logical.as_posix(),
                "kind": "directory" if is_directory else "file",
                "mode": mode,
                "bytes": size,
                "crc32": member.CRC,
                "sha256": digest,
            })
    require_reparse_free(destination)
    return inventory


def tree_inventory(root: Path) -> tuple[list[dict[str, object]], str]:
    require_reparse_free(root)
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            rows.append({"path": relative, "kind": "directory"})
        elif path.is_file():
            rows.append({
                "path": relative,
                "kind": "file",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
        else:
            raise RuntimeError(f"non-regular extracted object: {path}")
    return rows, canonical_digest(rows)


def run_checked(command: list[str], *, cwd: Path, environment: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True, text=True,
        check=False, timeout=120,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"command failed ({result.returncode}): {detail}")
    return result.stdout.strip()


def _duplicate_process_handle(process: subprocess.Popen[str]) -> int:
    if os.name != "nt":
        raise RuntimeError("R-224 resource authority is implemented for Windows only")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.DuplicateHandle.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong, ctypes.c_bool,
        ctypes.c_ulong,
    ]
    kernel32.DuplicateHandle.restype = ctypes.c_bool
    kernel32.GetProcessId.argtypes = [ctypes.c_void_p]
    kernel32.GetProcessId.restype = ctypes.c_ulong
    current = kernel32.GetCurrentProcess()
    duplicate = ctypes.c_void_p()
    if not kernel32.DuplicateHandle(
        current, ctypes.c_void_p(int(process._handle)), current,
        ctypes.byref(duplicate), 0, False, 0x00000002,
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    handle = int(duplicate.value)
    if kernel32.GetProcessId(ctypes.c_void_p(handle)) != process.pid:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        raise RuntimeError("duplicated child process handle identity mismatch")
    return handle


class _ProcessCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _sample_process_handle(handle: int) -> tuple[int, float]:
    counters = _ProcessCounters()
    counters.cb = ctypes.sizeof(counters)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(_ProcessCounters), ctypes.c_ulong,
    ]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_bool
    kernel32.GetProcessTimes.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    kernel32.GetProcessTimes.restype = ctypes.c_bool
    if not psapi.GetProcessMemoryInfo(
        ctypes.c_void_p(handle), ctypes.byref(counters), counters.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    creation, exit_time, kernel, user = (ctypes.c_uint64() for _ in range(4))
    if not kernel32.GetProcessTimes(
        ctypes.c_void_p(handle), ctypes.byref(creation), ctypes.byref(exit_time),
        ctypes.byref(kernel), ctypes.byref(user),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return (
        int(counters.PeakWorkingSetSize),
        (kernel.value + user.value) / 10_000_000,
    )


def _final_process_sample(handle: int) -> tuple[int, float]:
    return _sample_process_handle(handle)


def _close_process_handle(handle: int) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_bool
    if not kernel32.CloseHandle(ctypes.c_void_p(handle)):
        raise ctypes.WinError(ctypes.get_last_error())


def _terminate_with_final_sample(
    process: subprocess.Popen[str], handle: int, interim_peak: int,
    interim_cpu: float,
) -> tuple[int, float]:
    """Terminate a failed child but still bind its lifetime resource peak."""

    _terminate_tree(process)
    final_peak, final_cpu = _final_process_sample(handle)
    if final_peak < interim_peak or final_cpu < interim_cpu:
        raise RuntimeError("post-exit lifetime resource counters regressed")
    return final_peak, final_cpu


def _terminate_tree(process: subprocess.Popen[str]) -> tuple[str, str]:
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
        )
        if result.returncode and process.poll() is None:
            raise RuntimeError("Windows process-tree termination failed")
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    return process.communicate(timeout=30)


def tree_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def run_bounded(
    command: list[str], *, timeout: float, rss_limit: int, cwd: Path,
    environment: dict[str, str], disk_root: Path, disk_limit: int,
) -> dict[str, object]:
    """Run one worker once; fail closed on time, memory, or storage breach."""

    started = time.perf_counter()
    process = subprocess.Popen(
        command, cwd=cwd, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, start_new_session=os.name != "nt",
    )
    try:
        lifetime_handle = _duplicate_process_handle(process)
    except Exception:
        if process.poll() is None:
            _terminate_tree(process)
        raise
    peak = 0
    cpu = 0.0
    sample_count = 0
    disk_high = tree_bytes(disk_root)
    try:
        while process.poll() is None:
            try:
                child_peak, child_cpu = _sample_process_handle(lifetime_handle)
            except Exception:
                _terminate_with_final_sample(process, lifetime_handle, peak, cpu)
                raise
            peak, cpu = max(peak, child_peak), max(cpu, child_cpu)
            sample_count += 1
            disk_high = max(disk_high, tree_bytes(disk_root))
            if peak > rss_limit:
                _terminate_with_final_sample(process, lifetime_handle, peak, cpu)
                raise MemoryError(f"child RSS exceeded {rss_limit}")
            if disk_high > disk_limit:
                _terminate_with_final_sample(process, lifetime_handle, peak, cpu)
                raise OSError(f"staging exceeded {disk_limit} bytes")
            if time.perf_counter() - started > timeout:
                _terminate_with_final_sample(process, lifetime_handle, peak, cpu)
                raise TimeoutError(f"child exceeded {timeout} seconds")
            time.sleep(0.05)
        stdout, stderr = process.communicate()
        final_peak, final_cpu = _final_process_sample(lifetime_handle)
        if final_peak < peak or final_cpu < cpu:
            raise RuntimeError("post-exit lifetime resource counters regressed")
        peak, cpu = final_peak, final_cpu
        if peak > rss_limit:
            raise MemoryError(f"child final lifetime RSS exceeded {rss_limit}")
        disk_high = max(disk_high, tree_bytes(disk_root))
        if process.returncode:
            detail = (stderr or stdout).strip()
            raise RuntimeError(f"subprocess failed ({process.returncode}): {detail}")
        return {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": cpu,
            "peak_rss_bytes": peak,
            "interim_resource_sample_count": sample_count,
            "final_resource_sample_count": 1,
            "final_post_exit_sample": True,
            "process_scope": "exact-duplicated-popen-handle",
            "disk_high_water_bytes": disk_high,
            "launched_argv": list(command),
            "launched_argv_sha256": canonical_digest(list(command)),
            "stdout": stdout.strip(),
        }
    finally:
        _close_process_handle(lifetime_handle)


def read_pcm16(path: Path) -> tuple[int, int, int, bytes]:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        rate = source.getframerate()
        frames = source.getnframes()
        compression = source.getcomptype()
        payload = source.readframes(frames)
    if not 1 <= channels <= 8 or width != 2 or compression != "NONE":
        raise ValueError(f"non-canonical PCM16 WAV: {path}")
    if len(payload) != frames * channels * 2:
        raise ValueError(f"truncated PCM16 WAV: {path}")
    return rate, frames, channels, payload


def validate_config(value: dict[str, object]) -> None:
    if value != FROZEN_CONFIG:
        raise ValueError("frozen direct-Truth configuration drift")


def require_bytes_equal(old: bytes, current: bytes, label: str) -> None:
    if old != current:
        raise RuntimeError(f"{label} mismatch")


def validate_module_origins(
    origins: dict[str, str], extracted_root: Path
) -> None:
    allowed = extracted_root.resolve()
    required_prefixes = ("reference.maf_p0", "maf_p0", "cibs0")
    for name, origin in origins.items():
        if not name.startswith(required_prefixes):
            continue
        resolved = Path(origin).resolve()
        if allowed not in (resolved, *resolved.parents):
            raise RuntimeError(f"historical module escaped archive: {name} -> {origin}")


def module_inventory() -> dict[str, dict[str, object]]:
    """Categorize every loaded module and bind historical source-file hashes."""

    inventory: dict[str, dict[str, object]] = {}
    historical_prefixes = ("reference.maf_p0", "maf_p0", "cibs0")
    for name, module in sorted(sys.modules.items()):
        specification = getattr(module, "__spec__", None)
        spec_origin = getattr(specification, "origin", None)
        file_origin = getattr(module, "__file__", None)
        if file_origin is not None:
            resolved = Path(file_origin).resolve()
            if not resolved.is_file():
                raise RuntimeError(f"loaded module origin is not a file: {name}")
            entry: dict[str, object] = {
                "kind": "file",
                "origin": str(resolved),
            }
            if name.startswith(historical_prefixes):
                entry["sha256"] = sha256_file(resolved)
        elif spec_origin in {"built-in", "frozen"}:
            entry = {"kind": str(spec_origin), "origin": str(spec_origin)}
        elif spec_origin is None:
            entry = {"kind": "originless", "origin": None}
        else:
            entry = {"kind": "logical", "origin": str(spec_origin)}
        inventory[name] = entry
    return inventory


def validate_historical_module_inventory(
    inventory: dict[str, dict[str, object]], extracted_root: Path
) -> None:
    allowed = extracted_root.resolve()
    historical_prefixes = ("reference.maf_p0", "maf_p0", "cibs0")
    for name, entry in inventory.items():
        if not name.startswith(historical_prefixes):
            continue
        if entry.get("kind") != "file" or not entry.get("origin"):
            raise RuntimeError(f"historical module has no file origin: {name}")
        resolved = Path(str(entry["origin"])).resolve()
        if allowed not in (resolved, *resolved.parents):
            raise RuntimeError(f"historical module escaped archive: {name} -> {resolved}")
        if entry.get("sha256") != sha256_file(resolved):
            raise RuntimeError(f"historical module hash drift: {name}")


def _manifest_and_r221() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if sha256_file(MANIFEST) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("registered manifest drift")
    index_path = R221_ROOT / "run-index.json"
    aggregate_path = R221_ROOT / "aggregate.json"
    if sha256_file(index_path) != EXPECTED_R221_INDEX_SHA256:
        raise RuntimeError("R-221 index drift")
    if sha256_file(aggregate_path) != EXPECTED_R221_AGGREGATE_SHA256:
        raise RuntimeError("R-221 aggregate drift")
    manifest, index, aggregate = (
        load_json(MANIFEST), load_json(index_path), load_json(aggregate_path)
    )
    items = manifest.get("items")
    if not isinstance(items, list) or len(items) != EXPECTED_ITEM_COUNT:
        raise RuntimeError("registered manifest cardinality drift")
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)) or ids != index.get("completed_item_ids"):
        raise RuntimeError("registered order or uniqueness drift")
    if aggregate.get("item_count") != EXPECTED_ITEM_COUNT:
        raise RuntimeError("R-221 aggregate cardinality drift")
    if aggregate.get("status") != "PASS" or aggregate.get("receipt_sha256") != index.get(
        "receipt_sha256"
    ):
        raise RuntimeError("R-221 aggregate receipt authority drift")
    if [row["id"] for row in aggregate.get("rows", [])] != ids:
        raise RuntimeError("R-221 aggregate membership drift")
    if index.get("run_identity") != EXPECTED_R221_RUN_IDENTITY:
        raise RuntimeError("R-221 run identity drift")
    directories = {path.name for path in R221_ROOT.iterdir() if path.is_dir()}
    if directories != set(ids):
        raise RuntimeError("R-221 unexpected, missing, or quarantined item directory")
    return manifest, index, aggregate


def validate_current_item(
    item: dict[str, object], index: dict[str, object]
) -> dict[str, object]:
    item_id = str(item["id"])
    directory = R221_ROOT / item_id
    receipt_path = directory / "receipt.json"
    request_path = directory / "work-request.json"
    if sha256_file(receipt_path) != index["receipt_sha256"][item_id]:
        raise RuntimeError(f"R-221 receipt drift: {item_id}")
    if sha256_file(request_path) != index["work_request_sha256"][item_id]:
        raise RuntimeError(f"R-221 request drift: {item_id}")
    receipt, request = load_json(receipt_path), load_json(request_path)
    source = item["source"]
    if (receipt.get("status") != "PASS" or receipt.get("item_id") != item_id
            or receipt.get("order") != item["order"]):
        raise RuntimeError(f"R-221 receipt status drift: {item_id}")
    if (request.get("schema") != "resonith-r221-s12-bounded-rate-work-request-1"
            or request.get("run_identity") != EXPECTED_R221_RUN_IDENTITY
            or request.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256):
        raise RuntimeError(f"R-221 work-request authority drift: {item_id}")
    if receipt.get("resonith", {}).get("selected_kind") != "truth-fallback":
        raise RuntimeError(f"R-221 item is not direct Truth: {item_id}")
    if request.get("item") != item:
        raise RuntimeError(f"R-221 manifest item drift: {item_id}")
    source_path = Path(str(request["source_path"])).resolve()
    if sha256_file(source_path) != source["file_sha256"]:
        raise RuntimeError(f"source file drift: {item_id}")
    rate, frames, channels, source_pcm = read_pcm16(source_path)
    expected_tuple = (
        int(source["sample_rate"]), int(source["frame_count"]),
        int(source["channel_count"]), str(source["pcm16_payload_sha256"]),
    )
    if (rate, frames, channels, sha256_bytes(source_pcm)) != expected_tuple:
        raise RuntimeError(f"source PCM tuple drift: {item_id}")
    stream = directory / "resonith/challenger.resonith"
    decoded_wav = directory / "resonith/challenger-decoded.wav"
    stream_hash = sha256_file(stream)
    resonith = receipt["resonith"]
    if (stream_hash != resonith["payload_sha256"]
            or stream.stat().st_size != resonith["complete_bytes"]):
        raise RuntimeError(f"R-221 stream drift: {item_id}")
    decoded_rate, decoded_frames, decoded_channels, decoded_pcm = read_pcm16(decoded_wav)
    if (decoded_rate, decoded_frames, decoded_channels) != (rate, frames, channels):
        raise RuntimeError(f"R-221 decoded shape drift: {item_id}")
    if sha256_bytes(decoded_pcm) != resonith["decoded_pcm16le_sha256"]:
        raise RuntimeError(f"R-221 decoded PCM drift: {item_id}")
    retained = {entry["path"]: entry for entry in receipt["retained_files"]}
    for relative, actual in (
        ("resonith/challenger.resonith", stream),
        ("resonith/challenger-decoded.wav", decoded_wav),
    ):
        entry = retained.get(relative)
        if (entry is None or entry["sha256"] != sha256_file(actual)
                or entry["bytes"] != actual.stat().st_size):
            raise RuntimeError(f"R-221 retained-file drift: {item_id}/{relative}")
    return {
        "item_id": item_id,
        "source_path": str(source_path),
        "source_file_sha256": source["file_sha256"],
        "source_pcm16le_sha256": source["pcm16_payload_sha256"],
        "sample_rate": rate,
        "frames": frames,
        "channels": channels,
        "current_stream_path": str(stream.resolve()),
        "current_stream_sha256": stream_hash,
        "current_stream_bytes": stream.stat().st_size,
        "current_decoded_wav_path": str(decoded_wav.resolve()),
        "current_decoded_wav_sha256": sha256_file(decoded_wav),
        "current_decoded_pcm16le_sha256": sha256_bytes(decoded_pcm),
        "receipt_path": str(receipt_path.resolve()),
        "receipt_sha256": sha256_file(receipt_path),
        "work_request_path": str(request_path.resolve()),
        "work_request_sha256": sha256_file(request_path),
        "coefficients_per_frame": int(item["challenger"]["coefficients_per_frame"]),
        "half_window": int(item["challenger"]["half_window"]),
        "band_count": int(item["challenger"]["band_count"]),
        "duration_seconds": float(source["duration_seconds"]),
    }


def _validate_receipt_common(
    receipt: dict[str, object], request: dict[str, object], expected_status: str
) -> tuple[dict[str, object], dict[str, object]]:
    material = dict(receipt)
    claimed_material = material.pop("receipt_material_sha256", None)
    if claimed_material != canonical_digest(material):
        raise RuntimeError("worker receipt material hash mismatch")
    if (receipt.get("schema") != RECEIPT_SCHEMA
            or receipt.get("status") != expected_status
            or receipt.get("proof_kind") != "actual-ca87dec-counterfactual-execution"
            or receipt.get("item_id") != request["item_id"]):
        raise RuntimeError("worker receipt identity mismatch")
    historical = receipt.get("historical", {})
    current = receipt.get("current", {})
    source = receipt.get("source", {})
    references = receipt.get("references", {})
    runtime = receipt.get("runtime", {})
    if (current.get("payload_sha256") != request["current_stream_sha256"]
            or current.get("payload_bytes") != request["current_stream_bytes"]
            or current.get("decoded_pcm16le_sha256")
            != request["current_decoded_pcm16le_sha256"]):
        raise RuntimeError("worker receipt current comparator binding mismatch")
    expected_tuple = request["source_tuple"]
    if [source.get("sample_rate"), source.get("frames"), source.get("channels"),
        source.get("pcm16le_sha256")] != expected_tuple:
        raise RuntimeError("worker receipt source tuple mismatch")
    if (source.get("file_sha256") != request["source_file_sha256"]
            or source.get("dtype") != "int16"
            or source.get("byte_order") != "little-endian"):
        raise RuntimeError("worker receipt source identity mismatch")
    if receipt.get("configuration") != FROZEN_CONFIG:
        raise RuntimeError("worker receipt configuration mismatch")
    expected_references = {
        "current_stream_path": request["current_stream_path"],
        "current_stream_sha256": request["current_stream_sha256"],
        "current_decoded_wav_path": request["current_decoded_wav_path"],
        "current_decoded_wav_sha256": request["current_decoded_wav_sha256"],
        "r221_receipt_path": request["r221_receipt_path"],
        "r221_receipt_sha256": request["r221_receipt_sha256"],
        "r221_work_request_path": request["r221_work_request_path"],
        "r221_work_request_sha256": request["r221_work_request_sha256"],
    }
    if references != expected_references:
        raise RuntimeError("worker receipt reference mismatch")
    if (runtime.get("loaded_native_core") != str(NATIVE_CORE.resolve())
            or runtime.get("loaded_native_core_sha256") != EXPECTED_NATIVE_CORE_SHA256
            or runtime.get("isolated") != 1
            or runtime.get("no_user_site") != 1
            or runtime.get("safe_path") is not True
            or runtime.get("environment")
            != normalized_environment(request["environment"])):
        raise RuntimeError("worker receipt runtime authority mismatch")
    validate_execution_argv(
        runtime.get("execution_argv"), runtime.get("execution_argv_sha256"), request
    )
    return historical, current


def validate_worker_receipt(
    receipt: dict[str, object], request: dict[str, object]
) -> None:
    """Validate every decision-bearing passing child field before aggregate use."""

    historical, current = _validate_receipt_common(receipt, request, "PASS")
    if receipt.get("payload_identity") is not True:
        raise RuntimeError("worker receipt payload identity is not true")
    if receipt.get("decoded_pcm_identity") is not True:
        raise RuntimeError("worker receipt PCM identity is not true")
    if receipt.get("mismatch_artifacts") != []:
        raise RuntimeError("passing receipt unexpectedly retains mismatch artifacts")
    if (historical.get("payload_sha256") != current.get("payload_sha256")
            or historical.get("payload_bytes") != current.get("payload_bytes")
            or historical.get("decoded_pcm16le_sha256")
            != current.get("decoded_pcm16le_sha256")):
        raise RuntimeError("passing receipt historical/current identity mismatch")


def validate_mismatch_receipt(
    receipt: dict[str, object], request: dict[str, object], item_root: Path
) -> None:
    """Validate the real worker's terminal mismatch evidence package."""

    historical, current = _validate_receipt_common(receipt, request, "MISMATCH")
    payload_equal = (
        historical.get("payload_sha256") == current.get("payload_sha256")
        and historical.get("payload_bytes") == current.get("payload_bytes")
    )
    pcm_equal = (
        historical.get("decoded_pcm16le_sha256")
        == current.get("decoded_pcm16le_sha256")
        and historical.get("sample_rate") == current.get("sample_rate")
        and historical.get("frames") == current.get("frames")
        and historical.get("channels") == current.get("channels")
    )
    if (receipt.get("payload_identity") is not payload_equal
            or receipt.get("decoded_pcm_identity") is not pcm_equal
            or payload_equal and pcm_equal):
        raise RuntimeError("mismatch receipt identity flags are inconsistent")
    artifacts = receipt.get("mismatch_artifacts")
    if not isinstance(artifacts, list) or [row.get("path") for row in artifacts] != [
        "historical.resonith", "historical-decoded.wav"
    ]:
        raise RuntimeError("mismatch receipt artifact set is incomplete")
    for row in artifacts:
        path = item_root / str(row["path"])
        if (not path.is_file() or path.stat().st_size != row.get("bytes")
                or sha256_file(path) != row.get("sha256")):
            raise RuntimeError("mismatch artifact identity drift")
    if list(item_root.glob(".*.tmp")):
        raise RuntimeError("mismatch evidence left an atomic temporary file")
    require_reparse_free(item_root)


def remaining_deadline(deadline: float, per_item: float) -> float:
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise TimeoutError("R-224 aggregate 30-minute deadline exceeded")
    return min(per_item, remaining)


def require_storage_budget(current: int, pending: int, limit: int) -> None:
    if current + pending >= limit:
        raise RuntimeError("successful R-224 retained-storage budget exceeded")


def authority_snapshot(runner: Path) -> dict[str, object]:
    return {
        "manifest_sha256": sha256_file(MANIFEST),
        "r221_index_sha256": sha256_file(R221_ROOT / "run-index.json"),
        "r221_aggregate_sha256": sha256_file(R221_ROOT / "aggregate.json"),
        "preflight_sha256": sha256_file(PREFLIGHT),
        "native_core_sha256": sha256_file(NATIVE_CORE),
        "python_sha256": sha256_file(PYTHON),
        "git_sha256": sha256_file(GIT),
        "runner_sha256": sha256_file(runner),
        "unchanged_project_files": {
            relative: sha256_file(REPOSITORY / relative)
            for relative in UNCHANGED_PROJECT_FILES
        },
    }


def require_frozen_authorities(snapshot: dict[str, object]) -> None:
    expected = {
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "r221_index_sha256": EXPECTED_R221_INDEX_SHA256,
        "r221_aggregate_sha256": EXPECTED_R221_AGGREGATE_SHA256,
        "preflight_sha256": EXPECTED_PREFLIGHT_SHA256,
        "native_core_sha256": EXPECTED_NATIVE_CORE_SHA256,
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            raise RuntimeError(f"frozen authority drift: {key}")


def isolated_environment() -> dict[str, str]:
    allowed: dict[str, str] = {}
    for name in ("SystemRoot", "WINDIR", "ComSpec", "TEMP", "TMP"):
        if name in os.environ:
            allowed[name] = os.environ[name]
    allowed.update({
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    })
    return allowed


def normalized_environment(value: dict[str, str]) -> dict[str, str]:
    """Canonicalize Windows' case-insensitive environment-key spelling."""

    return {name.upper(): entry for name, entry in value.items()}


def _loaded_library_path(handle: int) -> Path:
    if os.name != "nt":
        return NATIVE_CORE.resolve()
    buffer = ctypes.create_unicode_buffer(32768)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleFileNameW.argtypes = [
        ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong,
    ]
    kernel32.GetModuleFileNameW.restype = ctypes.c_ulong
    size = kernel32.GetModuleFileNameW(
        ctypes.c_void_p(handle), buffer, len(buffer)
    )
    if not size:
        raise ctypes.WinError()
    return Path(buffer.value).resolve()


def pcm16_wav_bytes(rate: int, samples) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(int(samples.shape[1]))
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.astype("<i2", copy=False).tobytes())
    return buffer.getvalue()


def retain_mismatch_artifacts(
    item_root: Path, payload: bytes, rate: int, samples
) -> list[dict[str, object]]:
    """Retain both historical artifacts atomically after either mismatch."""

    stream = item_root / "historical.resonith"
    wav = item_root / "historical-decoded.wav"
    write_atomic(stream, payload)
    write_atomic(wav, pcm16_wav_bytes(rate, samples))
    return [
        {"path": stream.name, "bytes": stream.stat().st_size, "sha256": sha256_file(stream)},
        {"path": wav.name, "bytes": wav.stat().st_size, "sha256": sha256_file(wav)},
    ]


def worker(request_path: Path) -> int:
    """Execute one historical producer in an isolated Python process."""

    request = load_json(request_path)
    if request.get("schema") != WORK_SCHEMA:
        raise RuntimeError("worker schema mismatch")
    actual_argv = list(sys.orig_argv)
    validate_execution_argv(actual_argv, canonical_digest(actual_argv), request)
    if normalized_environment(dict(os.environ)) != normalized_environment(
        request["environment"]
    ):
        raise RuntimeError("worker environment allowlist drift")
    extracted_root = Path(str(request["extracted_root"])).resolve()
    repository = Path(str(request["repository"])).resolve()
    python_home = Path(sys.prefix).resolve()
    base_paths = []
    for entry in sys.path:
        if not entry:
            continue
        resolved = Path(entry).resolve()
        if python_home not in (resolved, *resolved.parents):
            raise RuntimeError(f"isolated interpreter path escaped pinned runtime: {resolved}")
        base_paths.append(str(resolved))
    sys.path[:] = [str(extracted_root), str(extracted_root / "reference"), *base_paths]

    import numpy as np
    from reference.maf_p0.lapped_oracle import encode_lapped_stream
    from reference.maf_p0.native_core import NativeMain0Decoder
    from reference.maf_p0.wav_io import read_pcm16_channels

    modules_before = module_inventory()
    validate_historical_module_inventory(modules_before, extracted_root)
    source = Path(str(request["source_path"])).resolve()
    if sha256_file(source) != request["source_file_sha256"]:
        raise RuntimeError("worker source file drift")
    rate, samples = read_pcm16_channels(source)
    source_pcm_hash = sha256_bytes(np.ascontiguousarray(samples, dtype="<i2").tobytes())
    actual_tuple = [rate, int(samples.shape[0]), int(samples.shape[1]), source_pcm_hash]
    if actual_tuple != request["source_tuple"]:
        raise RuntimeError("worker source PCM tuple drift")
    validate_config(request["configuration"])

    core = Path(str(request["native_core"])).resolve()
    if sha256_file(core) != EXPECTED_NATIVE_CORE_SHA256:
        raise RuntimeError("worker native Core drift")
    decoder = NativeMain0Decoder(core)
    loaded_core = _loaded_library_path(decoder._library._handle)
    if loaded_core != core or sha256_file(loaded_core) != EXPECTED_NATIVE_CORE_SHA256:
        raise RuntimeError("resolved native Core identity drift")

    started_wall, started_cpu = time.perf_counter(), time.process_time()
    result = encode_lapped_stream(
        samples,
        rate,
        coefficients_per_frame=int(request["coefficients_per_frame"]),
        half_window=int(request["half_window"]),
        band_count=int(request["band_count"]),
        entropy_backend="bounded",
        transform_backend="fixed",
        density_backend="adaptive",
        selection_backend="energy",
        frame_whitening=0.0,
        band_whitening=0.0,
        native_analyzer=decoder,
        native_decoder=decoder,
    )
    decoded = decoder.decode_lapped(result.payload)
    if decoded.sample_rate != rate or decoded.samples.shape != samples.shape:
        raise RuntimeError("historical decoder shape/rate mismatch")
    if not np.array_equal(decoded.samples, result.reconstruction):
        raise RuntimeError("historical encoder reconstruction differs from decode")

    current_stream_path = Path(str(request["current_stream_path"]))
    if (sha256_file(current_stream_path) != request["current_stream_sha256"]
            or current_stream_path.stat().st_size != request["current_stream_bytes"]):
        raise RuntimeError("worker current stream authority drift")
    current_wav_path = Path(str(request["current_decoded_wav_path"]))
    if sha256_file(current_wav_path) != request["current_decoded_wav_sha256"]:
        raise RuntimeError("worker current decoded-WAV authority drift")
    r221_receipt_path = Path(str(request["r221_receipt_path"]))
    if sha256_file(r221_receipt_path) != request["r221_receipt_sha256"]:
        raise RuntimeError("worker R-221 receipt authority drift")
    r221_work_request_path = Path(str(request["r221_work_request_path"]))
    if sha256_file(r221_work_request_path) != request["r221_work_request_sha256"]:
        raise RuntimeError("worker R-221 work-request authority drift")
    current_stream = current_stream_path.read_bytes()
    current_rate, current_samples = read_pcm16_channels(
        current_wav_path
    )
    current_pcm_hash = sha256_bytes(
        np.ascontiguousarray(current_samples, dtype="<i2").tobytes()
    )
    if current_pcm_hash != request["current_decoded_pcm16le_sha256"]:
        raise RuntimeError("worker current decoded-PCM authority drift")
    if (sha256_file(source) != request["source_file_sha256"]
            or sha256_file(current_stream_path) != request["current_stream_sha256"]
            or current_stream_path.stat().st_size != request["current_stream_bytes"]
            or sha256_file(current_wav_path) != request["current_decoded_wav_sha256"]
            or sha256_file(r221_receipt_path) != request["r221_receipt_sha256"]
            or sha256_file(r221_work_request_path) != request["r221_work_request_sha256"]):
        raise RuntimeError("worker authority changed during comparison")
    payload_equal = result.payload == current_stream
    pcm_equal = (
        current_rate == rate
        and current_samples.shape == decoded.samples.shape
        and np.array_equal(current_samples, decoded.samples)
    )
    item_root = request_path.parent
    mismatch_artifacts = []
    if not payload_equal or not pcm_equal:
        mismatch_artifacts = retain_mismatch_artifacts(
            item_root, result.payload, rate, decoded.samples
        )

    modules_after = module_inventory()
    validate_historical_module_inventory(modules_after, extracted_root)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "PASS" if payload_equal and pcm_equal else "MISMATCH",
        "proof_kind": "actual-ca87dec-counterfactual-execution",
        "item_id": request["item_id"],
        "historical_commit": request["historical_commit"],
        "historical_tree": request["historical_tree"],
        "source": {
            "path": str(source),
            "file_sha256": sha256_file(source),
            "pcm16le_sha256": source_pcm_hash,
            "sample_rate": rate,
            "frames": int(samples.shape[0]),
            "channels": int(samples.shape[1]),
            "shape": [int(samples.shape[0]), int(samples.shape[1])],
            "dtype": "int16",
            "byte_order": "little-endian",
        },
        "configuration": request["configuration"],
        "historical": {
            "payload_bytes": len(result.payload),
            "payload_sha256": sha256_bytes(result.payload),
            "decoded_pcm16le_sha256": sha256_bytes(
                np.ascontiguousarray(decoded.samples, dtype="<i2").tobytes()
            ),
            "sample_rate": decoded.sample_rate,
            "frames": int(decoded.samples.shape[0]),
            "channels": int(decoded.samples.shape[1]),
        },
        "current": {
            "payload_bytes": len(current_stream),
            "payload_sha256": sha256_bytes(current_stream),
            "decoded_pcm16le_sha256": sha256_bytes(
                np.ascontiguousarray(current_samples, dtype="<i2").tobytes()
            ),
            "sample_rate": current_rate,
            "frames": int(current_samples.shape[0]),
            "channels": int(current_samples.shape[1]),
        },
        "payload_identity": payload_equal,
        "decoded_pcm_identity": pcm_equal,
        "runtime": {
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "python_architecture": platform.architecture()[0],
            "isolated": sys.flags.isolated,
            "no_user_site": sys.flags.no_user_site,
            "safe_path": sys.flags.safe_path,
            "sys_path": list(sys.path),
            "cwd": str(Path.cwd().resolve()),
            "environment": normalized_environment(dict(os.environ)),
            "execution_argv": actual_argv,
            "execution_argv_sha256": canonical_digest(actual_argv),
            "numpy_version": np.__version__,
            "numpy_origin": str(Path(np.__file__).resolve()),
            "module_inventory_before": modules_before,
            "module_inventory_after": modules_after,
            "requested_native_core": str(core),
            "loaded_native_core": str(loaded_core),
            "loaded_native_core_sha256": sha256_file(loaded_core),
            "max_workspace_bytes": int(decoder._max_workspace_bytes),
            "self_wall_seconds": time.perf_counter() - started_wall,
            "self_cpu_seconds": time.process_time() - started_cpu,
        },
        "references": {
            "current_stream_path": request["current_stream_path"],
            "current_stream_sha256": request["current_stream_sha256"],
            "current_decoded_wav_path": request["current_decoded_wav_path"],
            "current_decoded_wav_sha256": request["current_decoded_wav_sha256"],
            "r221_receipt_path": request["r221_receipt_path"],
            "r221_receipt_sha256": request["r221_receipt_sha256"],
            "r221_work_request_path": request["r221_work_request_path"],
            "r221_work_request_sha256": request["r221_work_request_sha256"],
        },
        "mismatch_artifacts": mismatch_artifacts,
    }
    receipt["receipt_material_sha256"] = canonical_digest(receipt)
    write_json_atomic(item_root / "receipt.json", receipt)
    if not payload_equal:
        require_reparse_free(item_root)
        raise RuntimeError("historical payload differs from R-221 fallback")
    if not pcm_equal:
        require_reparse_free(item_root)
        raise RuntimeError("historical decoded PCM differs from R-221 fallback")
    print(json.dumps({"item_id": request["item_id"], "status": "PASS"}))
    return 0


def controller(output_root: Path) -> int:
    """Create and execute one non-resumable nineteen-item evidence package."""

    output_root = lexical_absolute(output_root)
    controller_started = time.perf_counter()
    aggregate_deadline = controller_started + 30.0 * 60.0
    runner = Path(__file__).resolve()
    if output_root.exists():
        raise FileExistsError(output_root)
    if output_root.parent.exists():
        require_ancestry_reparse_free(output_root.parent)
    output_root.mkdir(parents=False)
    require_ancestry_reparse_free(output_root)
    require_reparse_free(output_root)

    initial_authorities = authority_snapshot(runner)
    require_frozen_authorities(initial_authorities)
    manifest, index, aggregate = _manifest_and_r221()
    del aggregate
    if sha256_file(NATIVE_CORE) != EXPECTED_NATIVE_CORE_SHA256:
        raise RuntimeError("native Core drift")

    commit = run_checked(
        [str(GIT), "-C", str(REPOSITORY), "rev-parse", f"{HISTORICAL_REF}^{{commit}}"],
        cwd=REPOSITORY,
    )
    tree = run_checked(
        [str(GIT), "-C", str(REPOSITORY), "rev-parse", f"{HISTORICAL_REF}^{{tree}}"],
        cwd=REPOSITORY,
    )
    if commit != EXPECTED_HISTORICAL_COMMIT or tree != EXPECTED_HISTORICAL_TREE:
        raise RuntimeError("historical Git authority drift")
    archive = output_root / "ca87dec.zip"
    run_checked(
        [str(GIT), "-C", str(REPOSITORY), "archive", "--format=zip",
         f"--output={archive}", commit],
        cwd=REPOSITORY,
    )
    archive_hash = sha256_file(archive)
    extracted = output_root / "ca87dec-tree"
    archive_inventory = extract_git_archive(archive, extracted)
    extracted_inventory, extracted_digest = tree_inventory(extracted)

    historical_project_hashes = {
        relative: sha256_file(extracted / relative)
        for relative in UNCHANGED_PROJECT_FILES
    }
    if historical_project_hashes != initial_authorities["unchanged_project_files"]:
        raise RuntimeError("historical/current lapped producer or ABI drift")

    environment = isolated_environment()
    rows: list[dict[str, object]] = []
    bindings: dict[str, dict[str, object]] = {}
    execution_requests: dict[str, dict[str, object]] = {}
    for item in manifest["items"]:
        binding = validate_current_item(item, index)
        bindings[str(item["id"])] = binding
        before_inventory, before_digest = tree_inventory(extracted)
        if before_digest != extracted_digest or before_inventory != extracted_inventory:
            raise RuntimeError("extracted historical tree drift before child")
        item_root = output_root / f"{int(item['order']):02d}-{item['id']}"
        item_root.mkdir()
        config = dict(FROZEN_CONFIG)
        validate_config(config)
        request = {
            "schema": WORK_SCHEMA,
            "item_id": binding["item_id"],
            "repository": str(REPOSITORY.resolve()),
            "extracted_root": str(extracted.resolve()),
            "historical_commit": commit,
            "historical_tree": tree,
            "native_core": str(NATIVE_CORE.resolve()),
            "source_path": binding["source_path"],
            "source_file_sha256": binding["source_file_sha256"],
            "source_tuple": [
                binding["sample_rate"], binding["frames"], binding["channels"],
                binding["source_pcm16le_sha256"],
            ],
            "coefficients_per_frame": binding["coefficients_per_frame"],
            "half_window": binding["half_window"],
            "band_count": binding["band_count"],
            "configuration": config,
            "current_stream_path": binding["current_stream_path"],
            "current_stream_sha256": binding["current_stream_sha256"],
            "current_stream_bytes": binding["current_stream_bytes"],
            "current_decoded_wav_path": binding["current_decoded_wav_path"],
            "current_decoded_wav_sha256": binding["current_decoded_wav_sha256"],
            "current_decoded_pcm16le_sha256": binding["current_decoded_pcm16le_sha256"],
            "r221_receipt_path": binding["receipt_path"],
            "r221_receipt_sha256": binding["receipt_sha256"],
            "r221_work_request_path": binding["work_request_path"],
            "r221_work_request_sha256": binding["work_request_sha256"],
            "environment": environment,
        }
        request_path = item_root / "work-request.json"
        command = [
            str(PYTHON), "-I", "-B", "-X", "utf8", str(runner),
            "--worker", str(request_path),
        ]
        request["execution_argv"] = command
        request["execution_argv_sha256"] = canonical_digest(command)
        execution_requests[str(item["id"])] = request
        write_json_atomic(request_path, request)
        request_hash_before = sha256_file(request_path)
        per_item_timeout = min(
            900.0, max(300.0, 3.0 * float(binding["duration_seconds"]))
        )
        timeout = remaining_deadline(aggregate_deadline, per_item_timeout)
        resources = run_bounded(
            command, timeout=timeout, rss_limit=4 * GIB, cwd=extracted,
            environment=environment, disk_root=output_root, disk_limit=4 * GIB,
        )
        receipt_path = item_root / "receipt.json"
        receipt = load_json(receipt_path)
        if sha256_file(request_path) != request_hash_before:
            raise RuntimeError(f"worker request drift: {item['id']}")
        validate_execution_argv(
            resources.get("launched_argv"),
            resources.get("launched_argv_sha256"), request,
        )
        validate_worker_receipt(receipt, request)
        if (item_root / "historical.resonith").exists() or (
            item_root / "historical-decoded.wav"
        ).exists():
            raise RuntimeError(f"passing item retained mismatch artifacts: {item['id']}")
        after_inventory, after_digest = tree_inventory(extracted)
        if after_digest != before_digest or after_inventory != before_inventory:
            raise RuntimeError("extracted historical tree drift after child")
        rows.append({
            "order": item["order"],
            "item_id": item["id"],
            "status": receipt["status"],
            "proof_kind": receipt["proof_kind"],
            "payload_identity": receipt["payload_identity"],
            "decoded_pcm_identity": receipt["decoded_pcm_identity"],
            "historical_payload_sha256": receipt["historical"]["payload_sha256"],
            "current_payload_sha256": receipt["current"]["payload_sha256"],
            "complete_bytes": receipt["current"]["payload_bytes"],
            "historical_pcm16le_sha256": receipt["historical"]["decoded_pcm16le_sha256"],
            "current_pcm16le_sha256": receipt["current"]["decoded_pcm16le_sha256"],
            "receipt_path": str(receipt_path.relative_to(output_root).as_posix()),
            "receipt_sha256": sha256_file(receipt_path),
            "request_sha256": request_hash_before,
            "execution_argv": request["execution_argv"],
            "execution_argv_sha256": request["execution_argv_sha256"],
            "historical_tree_sha256_before": before_digest,
            "historical_tree_sha256_after": after_digest,
            "process_resources": resources,
        })
        print(f"[{len(rows):02d}/{EXPECTED_ITEM_COUNT}] {item['id']}: PASS", flush=True)

    final_authorities = authority_snapshot(runner)
    require_frozen_authorities(final_authorities)
    validate_aggregate_argv_rows(rows, execution_requests)
    for item in manifest["items"]:
        item_id = str(item["id"])
        if validate_current_item(item, index) != bindings[item_id]:
            raise RuntimeError(f"final R-221 item authority drift: {item_id}")
        row = next(entry for entry in rows if entry["item_id"] == item_id)
        item_root = output_root / f"{int(item['order']):02d}-{item_id}"
        if (sha256_file(item_root / "work-request.json") != row["request_sha256"]
                or sha256_file(item_root / "receipt.json") != row["receipt_sha256"]):
            raise RuntimeError(f"final R-224 item authority drift: {item_id}")
    final_inventory, final_extracted_digest = tree_inventory(extracted)
    if final_authorities != initial_authorities:
        raise RuntimeError("frozen authority drift during complete run")
    if final_inventory != extracted_inventory or final_extracted_digest != extracted_digest:
        raise RuntimeError("historical archive tree drift during complete run")
    if len(rows) != EXPECTED_ITEM_COUNT or any(
        not row["payload_identity"] or not row["decoded_pcm_identity"] for row in rows
    ):
        raise RuntimeError("nineteen-item aggregate identity failed")
    retained_bytes = tree_bytes(output_root)

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "proof_kind": "actual-ca87dec-counterfactual-execution",
        "scope": "preceding Resonith comparison only; Opus not rerun; no S13 syntax",
        "historical_commit": commit,
        "historical_tree": tree,
        "archive": {
            "path": archive.name,
            "bytes": archive.stat().st_size,
            "sha256": archive_hash,
            "member_count": len(archive_inventory),
            "members": archive_inventory,
            "extracted_inventory": extracted_inventory,
            "extracted_inventory_sha256": extracted_digest,
        },
        "runtime_authority": {
            "python_path": str(PYTHON.resolve()),
            "python_version": run_checked([str(PYTHON), "-I", "-c", "import sys; print(sys.version)"], cwd=REPOSITORY),
            "python_executable_sha256": sha256_file(PYTHON),
            "git_path": str(GIT.resolve()),
            "git_version": run_checked([str(GIT), "--version"], cwd=REPOSITORY),
            "git_executable_sha256": sha256_file(GIT),
            "environment": environment,
        },
        "authorities_before": initial_authorities,
        "authorities_after": final_authorities,
        "historical_project_hashes": historical_project_hashes,
        "registered_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "r221_run_identity": EXPECTED_R221_RUN_IDENTITY,
        "item_count": len(rows),
        "skipped_count": 0,
        "duplicate_count": 0,
        "quarantined_count": 0,
        "payload_identity_count": sum(bool(row["payload_identity"]) for row in rows),
        "decoded_pcm_identity_count": sum(bool(row["decoded_pcm_identity"]) for row in rows),
        "rows": rows,
        "retained_bytes_before_aggregate": retained_bytes,
        "controller_wall_seconds_before_aggregate": time.perf_counter() - controller_started,
    }
    result["aggregate_material_sha256"] = canonical_digest(result)
    aggregate_path = output_root / "aggregate.json"
    aggregate_payload = json_bytes(result)
    require_storage_budget(retained_bytes, len(aggregate_payload), 256 * MIB)
    if time.perf_counter() > aggregate_deadline:
        raise TimeoutError("R-224 aggregate 30-minute deadline exceeded")
    write_atomic(aggregate_path, aggregate_payload)
    require_reparse_free(output_root)
    final_retained_bytes = tree_bytes(output_root)
    if final_retained_bytes >= 256 * MIB:
        raise RuntimeError("successful R-224 final retained-storage budget exceeded")
    if time.perf_counter() > aggregate_deadline:
        raise TimeoutError("R-224 aggregate 30-minute deadline exceeded")
    print(json.dumps({
        "status": "PASS",
        "items": len(rows),
        "aggregate": str(aggregate_path),
        "aggregate_file_sha256": sha256_file(aggregate_path),
        "aggregate_material_sha256": result["aggregate_material_sha256"],
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=REPOSITORY / "artifacts/r224-s13-predecessor-comparison",
    )
    arguments = parser.parse_args(argv)
    if arguments.worker is not None:
        return worker(arguments.worker.resolve())
    return controller(lexical_absolute(arguments.output))


if __name__ == "__main__":
    raise SystemExit(main())
