"""Fail-closed external resource evidence for the final R-218 C checkpoint."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import wave


REPOSITORY = Path(__file__).resolve().parents[1]
SCHEMA = "resonith-r218-s11-resource-receipt-1"
GIB = 1024**3
RSS_LIMIT = 8 * GIB
DISK_LIMIT = 2 * GIB
TIME_LIMIT_SECONDS = 600.0
POLL_SECONDS = 0.010
MAX_SAMPLE_GAP_SECONDS = 0.025
OUTPUT_LIMIT_BYTES = 1024 * 1024

PYTHON = REPOSITORY / "artifacts/tools/python-3.14.6-amd64/python.exe"
HELPER = REPOSITORY / "experiments/r218_s11_internal_identity.py"
ANALYZER = REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py"
PREDICTOR = REPOSITORY / "reference/maf_p0/persistent_partial_field.py"
CORE = REPOSITORY / "build/cpp23-clang22-ninja/libresonith_core_shared.dll"
ISOLATED_BOOTSTRAP = (
    "import runpy,sys;"
    f"sys.path[:0]=[{str(REPOSITORY)!r},{str(REPOSITORY / 'reference')!r}];"
    "sys.argv=['experiments.r218_s11_internal_identity',*sys.argv[1:]];"
    "runpy.run_module('experiments.r218_s11_internal_identity',run_name='__main__')"
)

STATIC_AUTHORITIES = {
    "python_executable": "03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38",
    "identity_helper": "f8d5a18a725f5331ebd752a0a8a1031c2aecb270afcb5d2889e36cf592c7270d",
    "analyzer": "c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c",
    "predictor": "583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec",
    "native_core": "f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed",
}

ITEMS = {
    "ebu-claves": {
        "source": REPOSITORY / "artifacts/corpus/prepared-r111/ebu-claves.wav",
        "source_file_sha256": "9069b02a7bf39a67c36f634aef759d79ad63241b8b709d08b12f8a6a043959df",
        "source_pcm16le_sha256": "1a8b6faffd774da205898a453deb3fa9d8e42c4da5e20d05aaac2a05e26cd65b",
        "combined_internal_sha256": "79c11ca6b160d80330c30944e82d59207b8b7e4157d5984d3b7826f019a34a2b",
        "selected_payload_sha256": "9156b28ec67b25c6fc222a52d74431e9cf656f67b7bc01409e94ff4e601927dd",
        "selected_pcm16le_sha256": "32a3e399fd6b747aa14f372f1d1447b93290e133cce99e888fba17eb2f6fb96e",
    },
    "ebu-cymbal": {
        "source": REPOSITORY / "artifacts/corpus/prepared-r111/ebu-cymbal.wav",
        "source_file_sha256": "4e5fed73eea73f72b9b227591a9a586dbd664d762497aa6a9457920571447b42",
        "source_pcm16le_sha256": "a9513b354efa40700c811f9fae8122f4a1a16196d849f684281263b2bdffd8cd",
        "combined_internal_sha256": "30c5bb7d38c254a3ae9159c9377a0e6f132aaf5d4c7ea33ccaba5a6a6d29c34c",
        "selected_payload_sha256": "1f149b8ca110f17782b673a9cb7c84903b37b094ccd8301e88ef41bc4265fe5b",
        "selected_pcm16le_sha256": "782f7cedf6fa10bd4fa5600c605c086e2edca18fd7528706e6d036cb239ae9cb",
    },
}


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


class _BoundedPipe:
    def __init__(self, pipe, limit: int) -> None:
        self._pipe = pipe
        self._limit = limit
        self.buffer = bytearray()
        self.total_bytes = 0
        self.overflow = False
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._drain, daemon=True)

    def _drain(self) -> None:
        try:
            while True:
                chunk = self._pipe.read(65536)
                if not chunk:
                    return
                self.total_bytes += len(chunk)
                remaining = self._limit - len(self.buffer)
                if remaining > 0:
                    self.buffer.extend(chunk[:remaining])
                if self.total_bytes > self._limit:
                    self.overflow = True
        except BaseException as error:  # pragma: no cover - fail-closed path
            self.error = error

    def start(self) -> None:
        self.thread.start()

    def finish(self) -> None:
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise RuntimeError("bounded pipe reader did not terminate")
        if self.error is not None:
            raise RuntimeError("bounded pipe reader failed") from self.error


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _pcm_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
            raise RuntimeError("resource-gate source must be uncompressed PCM16")
        while True:
            block = source.readframes(65536)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


def _identity_snapshot(item: dict[str, object]) -> dict[str, str]:
    paths = {
        "python_executable": PYTHON,
        "resource_gate": Path(__file__).resolve(),
        "identity_helper": HELPER,
        "analyzer": ANALYZER,
        "predictor": PREDICTOR,
        "native_core": CORE,
        "source_file": Path(item["source"]),
    }
    snapshot = {name: _sha256(path) for name, path in paths.items()}
    snapshot["source_pcm16le"] = _pcm_sha256(Path(item["source"]))
    return snapshot


def _validate_static_authorities(
    snapshot: dict[str, str], item: dict[str, object], audited_gate_sha256: str
) -> None:
    expected = {
        **STATIC_AUTHORITIES,
        "resource_gate": audited_gate_sha256,
        "source_file": str(item["source_file_sha256"]),
        "source_pcm16le": str(item["source_pcm16le_sha256"]),
    }
    for name, digest in expected.items():
        if snapshot.get(name) != digest:
            raise RuntimeError(f"R-218 authority mismatch: {name}")


def _scan_staging(root: Path) -> int:
    resolved_root = root.resolve(strict=True)
    if resolved_root != root:
        raise RuntimeError("staging root changed identity")
    total = 0
    for path in (root, *root.rglob("*")):
        resolved = path.resolve(strict=True)
        if resolved != path or (resolved != root and root not in resolved.parents):
            raise RuntimeError("staging path escaped containment")
        status = path.lstat()
        if getattr(status, "st_file_attributes", 0) & 0x400:
            raise RuntimeError("reparse point in staging tree")
        if path.is_file():
            total += status.st_size
    return total


def _fresh_staging(path: Path) -> Path:
    if os.name != "nt":
        raise RuntimeError("R-218 resource gate currently requires Windows")
    path = path.resolve(strict=False)
    if path.drive.upper() != "G:":
        raise RuntimeError("R-218 resource evidence must remain on G:")
    if path.exists():
        raise RuntimeError("resource staging root must be fresh")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()
    if _scan_staging(path) != 0:
        raise RuntimeError("resource staging root must be empty")
    return path


def _windows_api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
    ]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
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
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return kernel, psapi


def _raise_last(message: str) -> None:
    error = ctypes.get_last_error()
    raise OSError(error, f"{message}: Windows error {error}")


def _close_handle(kernel, handle: int, label: str) -> None:
    if handle and not kernel.CloseHandle(handle):
        _raise_last(f"CloseHandle failed for {label}")


def _create_job(kernel) -> int:
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        _raise_last("CreateJobObjectW failed")
    limits = _JobExtendedLimit()
    limits.BasicLimitInformation.LimitFlags = 0x00000008 | 0x00002000
    limits.BasicLimitInformation.ActiveProcessLimit = 1
    if not kernel.SetInformationJobObject(
        job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
    ):
        original_error = ctypes.get_last_error()
        _close_handle(kernel, job, "unconfigured job")
        raise OSError(
            original_error,
            f"SetInformationJobObject failed: Windows error {original_error}",
        )
    return int(job)


def _resume_suspended_process(kernel, process_id: int) -> None:
    snapshot = kernel.CreateToolhelp32Snapshot(0x00000004, 0)
    if int(snapshot) == ctypes.c_void_p(-1).value:
        _raise_last("CreateToolhelp32Snapshot failed")
    resumed = 0
    try:
        entry = _ThreadEntry32(dwSize=ctypes.sizeof(_ThreadEntry32))
        ctypes.set_last_error(0)
        more = kernel.Thread32First(snapshot, ctypes.byref(entry))
        if not more:
            _raise_last("Thread32First failed")
        while more:
            if entry.th32OwnerProcessID == process_id:
                thread = kernel.OpenThread(0x0002, False, entry.th32ThreadID)
                if not thread:
                    _raise_last("OpenThread failed")
                try:
                    prior = kernel.ResumeThread(thread)
                    if prior == 0xFFFFFFFF or prior == 0:
                        _raise_last("ResumeThread did not resume suspended child")
                    resumed += 1
                finally:
                    _close_handle(kernel, thread, "suspended child thread")
            ctypes.set_last_error(0)
            more = kernel.Thread32Next(snapshot, ctypes.byref(entry))
        if ctypes.get_last_error() not in (0, 18):
            _raise_last("Thread32Next failed")
    finally:
        _close_handle(kernel, snapshot, "thread snapshot")
    if resumed != 1:
        raise RuntimeError(f"expected one suspended child thread, found {resumed}")


def _peak_working_set(psapi, process_handle: int) -> int:
    counters = _ProcessMemoryCounters(cb=ctypes.sizeof(_ProcessMemoryCounters))
    if not psapi.GetProcessMemoryInfo(
        process_handle, ctypes.byref(counters), counters.cb
    ):
        _raise_last("GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def _job_peak_memory(kernel, job: int) -> int:
    limits = _JobExtendedLimit()
    returned = wintypes.DWORD()
    if not kernel.QueryInformationJobObject(
        job, 9, ctypes.byref(limits), ctypes.sizeof(limits), ctypes.byref(returned)
    ):
        _raise_last("QueryInformationJobObject failed")
    return int(limits.PeakJobMemoryUsed)


def run_monitored(command: list[str], staging: Path) -> dict[str, object]:
    """Run one suspended, single-process child and return measured resources."""
    kernel, psapi = _windows_api()
    job = _create_job(kernel)
    process: subprocess.Popen | None = None
    stdout_reader = stderr_reader = None
    assigned_to_job = False
    started = time.perf_counter()
    disk_high_water = _scan_staging(staging)
    try:
        process = subprocess.Popen(
            command,
            cwd=REPOSITORY,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            creationflags=0x00000004,
        )
        process_handle = int(process._handle)  # Retained by Popen through postflight.
        if not kernel.AssignProcessToJobObject(job, process_handle):
            _raise_last("AssignProcessToJobObject failed")
        assigned_to_job = True
        stdout_reader = _BoundedPipe(process.stdout, OUTPUT_LIMIT_BYTES)
        stderr_reader = _BoundedPipe(process.stderr, OUTPUT_LIMIT_BYTES)
        stdout_reader.start()
        stderr_reader.start()
        _resume_suspended_process(kernel, process.pid)

        peak_working_set = 0
        peak_job_memory = 0
        next_sample = time.perf_counter()
        last_sample_started: float | None = None
        maximum_sample_gap = 0.0
        sample_count = 0
        while True:
            sample_started = time.perf_counter()
            if last_sample_started is not None:
                gap = sample_started - last_sample_started
                maximum_sample_gap = max(maximum_sample_gap, gap)
                if gap > MAX_SAMPLE_GAP_SECONDS:
                    raise TimeoutError(
                        "R-218 resource sample gap exceeded 25 milliseconds"
                    )
            last_sample_started = sample_started
            sample_count += 1
            peak_working_set = max(
                peak_working_set, _peak_working_set(psapi, process_handle)
            )
            peak_job_memory = max(peak_job_memory, _job_peak_memory(kernel, job))
            disk_high_water = max(disk_high_water, _scan_staging(staging))
            if peak_working_set > RSS_LIMIT:
                raise MemoryError("R-218 child peak working set exceeded 8 GiB")
            if disk_high_water > DISK_LIMIT:
                raise OSError("R-218 staging high-water exceeded 2 GiB")
            if time.perf_counter() - started > TIME_LIMIT_SECONDS:
                raise TimeoutError("R-218 final-C child exceeded 600 seconds")
            if process.poll() is not None:
                break
            next_sample += POLL_SECONDS
            time.sleep(max(0.0, next_sample - time.perf_counter()))

        peak_working_set = max(
            peak_working_set, _peak_working_set(psapi, process_handle)
        )
        peak_job_memory = max(peak_job_memory, _job_peak_memory(kernel, job))
        disk_high_water = max(disk_high_water, _scan_staging(staging))
        stdout_reader.finish()
        stderr_reader.finish()
        if stdout_reader.overflow or stderr_reader.overflow:
            raise RuntimeError("R-218 child output exceeded bounded capture")
        if process.returncode != 0:
            stdout_sha = hashlib.sha256(stdout_reader.buffer).hexdigest()
            stderr_sha = hashlib.sha256(stderr_reader.buffer).hexdigest()
            stdout_excerpt = bytes(stdout_reader.buffer[:4096]).decode(
                "utf-8", errors="replace"
            )
            stderr_excerpt = bytes(stderr_reader.buffer[:4096]).decode(
                "utf-8", errors="replace"
            )
            raise RuntimeError(
                f"R-218 child failed with exit {process.returncode}; "
                f"stdout_sha256={stdout_sha}; stderr_sha256={stderr_sha}; "
                f"stdout_excerpt={stdout_excerpt!r}; "
                f"stderr_excerpt={stderr_excerpt!r}"
            )
        return {
            "wall_seconds": time.perf_counter() - started,
            "process_peak_working_set_bytes": peak_working_set,
            "job_peak_memory_bytes": peak_job_memory,
            "sample_count": sample_count,
            "maximum_sample_gap_seconds": maximum_sample_gap,
            "maximum_sample_gap_limit_seconds": MAX_SAMPLE_GAP_SECONDS,
            "staging_disk_high_water_before_parent_receipt_bytes": disk_high_water,
            "stdout_total_bytes": stdout_reader.total_bytes,
            "stdout_sha256": hashlib.sha256(stdout_reader.buffer).hexdigest(),
            "stdout_utf8": stdout_reader.buffer.decode("utf-8", errors="replace"),
            "stderr_total_bytes": stderr_reader.total_bytes,
            "stderr_sha256": hashlib.sha256(stderr_reader.buffer).hexdigest(),
            "stderr_utf8": stderr_reader.buffer.decode("utf-8", errors="replace"),
            "exit_code": process.returncode,
        }
    finally:
        cleanup_errors: list[BaseException] = []
        if process is not None and process.poll() is None:
            if assigned_to_job:
                if not kernel.TerminateJobObject(job, 1):
                    error = ctypes.get_last_error()
                    cleanup_errors.append(OSError(
                        error,
                        f"TerminateJobObject failed: Windows error {error}",
                    ))
            if not assigned_to_job or cleanup_errors:
                try:
                    process.kill()
                except BaseException as error:  # pragma: no cover - hostile API
                    cleanup_errors.append(error)
            try:
                process.wait(timeout=30)
            except BaseException as error:  # pragma: no cover - hostile API
                cleanup_errors.append(error)
                try:
                    process.kill()
                    process.wait(timeout=30)
                except BaseException as fallback_error:
                    cleanup_errors.append(fallback_error)
        if process is not None and process.poll() is None:
            cleanup_errors.append(RuntimeError("R-218 child survived cleanup"))
        if stdout_reader is not None and stdout_reader.thread.is_alive():
            try:
                stdout_reader.finish()
            except BaseException as error:
                cleanup_errors.append(error)
        if stderr_reader is not None and stderr_reader.thread.is_alive():
            try:
                stderr_reader.finish()
            except BaseException as error:
                cleanup_errors.append(error)
        if process is not None:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except BaseException as error:
                        cleanup_errors.append(error)
        if job:
            try:
                _close_handle(kernel, job, "R-218 job")
            except BaseException as error:
                cleanup_errors.append(error)
        if cleanup_errors:
            raise RuntimeError("R-218 resource monitor cleanup failed") from cleanup_errors[0]


def _helper_command(arguments: list[str]) -> list[str]:
    return [str(PYTHON), "-I", "-c", ISOLATED_BOOTSTRAP, *arguments]


def _child_command(item_id: str, item: dict[str, object], output: Path) -> list[str]:
    return _helper_command([
        "--source-wav", str(item["source"]),
        "--case-id", f"{item_id}-full-resource-gate",
        "--native-core", str(CORE),
        "--coefficients-per-frame", "71",
        "--half-window", "512",
        "--band-count", "24",
        "--output", str(output),
    ])


def _verify_child_result(result: dict[str, object], item: dict[str, object]) -> None:
    if result.get("schema") != "resonith-r218-s11-internal-identity-2":
        raise RuntimeError("unexpected R-218 child schema")
    expected = {
        "source_pcm16le_sha256": item["source_pcm16le_sha256"],
        "combined_internal_sha256": item["combined_internal_sha256"],
        "selected_payload_sha256": item["selected_payload_sha256"],
        "selected_pcm16le_sha256": item["selected_pcm16le_sha256"],
    }
    for name, value in expected.items():
        if result.get(name) != value:
            raise RuntimeError(f"final-C child authority mismatch: {name}")
    if result.get("resource_measurement_authority") != "external-parent-receipt-required":
        raise RuntimeError("child did not disclaim self-reported resource authority")


def _write_fixed_point_receipt(path: Path, receipt: dict[str, object]) -> bytes:
    receipt["parent_receipt_bytes"] = 0
    receipt["staging_bytes_postflight"] = 0
    while True:
        encoded = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
        child_bytes = _scan_staging(path.parent)
        final_total = child_bytes + len(encoded)
        high_water = max(
            int(receipt["resources"]["staging_disk_high_water_before_parent_receipt_bytes"]),
            final_total,
        )
        changed = (
            receipt["parent_receipt_bytes"] != len(encoded)
            or receipt["staging_bytes_postflight"] != final_total
            or receipt.get("staging_disk_high_water_bytes") != high_water
        )
        receipt["parent_receipt_bytes"] = len(encoded)
        receipt["staging_bytes_postflight"] = final_total
        receipt["staging_disk_high_water_bytes"] = high_water
        if high_water > DISK_LIMIT:
            raise OSError("R-218 receipt-inclusive staging exceeded 2 GiB")
        if not changed:
            break
    path.write_bytes(encoded)
    if _scan_staging(path.parent) != receipt["staging_bytes_postflight"]:
        raise RuntimeError("parent receipt fixed-point accounting mismatch")
    return encoded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", choices=tuple(ITEMS), required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--audited-gate-sha256", required=True)
    arguments = parser.parse_args()

    item = ITEMS[arguments.item]
    staging = _fresh_staging(arguments.staging_root)
    child_output = staging / "final-c-child.json"
    preflight = _identity_snapshot(item)
    _validate_static_authorities(
        preflight, item, arguments.audited_gate_sha256
    )
    command = _child_command(arguments.item, item, child_output)
    resources = run_monitored(command, staging)
    if not child_output.is_file():
        raise RuntimeError("final-C child output missing")
    child_result = json.loads(child_output.read_text(encoding="utf-8"))
    _verify_child_result(child_result, item)
    postflight = _identity_snapshot(item)
    _validate_static_authorities(
        postflight, item, arguments.audited_gate_sha256
    )
    if postflight != preflight:
        raise RuntimeError("R-218 authority changed between preflight and postflight")

    receipt = {
        "schema": SCHEMA,
        "status": "PASS",
        "item_id": arguments.item,
        "argv": command,
        "controller_argv": [str(Path(sys.executable).resolve()), *sys.argv],
        "audited_resource_gate_sha256": arguments.audited_gate_sha256,
        "shell": False,
        "poll_interval_seconds": POLL_SECONDS,
        "maximum_sample_gap_seconds": MAX_SAMPLE_GAP_SECONDS,
        "rss_limit_bytes": RSS_LIMIT,
        "disk_limit_bytes": DISK_LIMIT,
        "time_limit_seconds": TIME_LIMIT_SECONDS,
        "staging_bytes_prelaunch": 0,
        "identities_prelaunch": preflight,
        "identities_postflight": postflight,
        "resources": resources,
        "child_output_sha256": _sha256(child_output),
        "child_result": child_result,
    }
    receipt_path = staging / "parent-resource-receipt.json"
    encoded = _write_fixed_point_receipt(receipt_path, receipt)
    print(json.dumps({
        "status": "PASS",
        "item_id": arguments.item,
        "receipt": str(receipt_path),
        "receipt_bytes": len(encoded),
        "receipt_sha256": hashlib.sha256(encoded).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
