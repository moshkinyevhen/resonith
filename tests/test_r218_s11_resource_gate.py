from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path

import pytest

from experiments import r218_s11_resource_gate as gate


@pytest.mark.skipif(gate.os.name != "nt", reason="Windows Job Object gate")
def test_job_gate_runs_one_child_and_captures_bounded_output(tmp_path: Path) -> None:
    result = gate.run_monitored(
        [str(gate.PYTHON), "-c", "print('job-smoke')"], tmp_path
    )
    assert result["exit_code"] == 0
    assert result["stdout_utf8"] == "job-smoke\r\n"
    assert result["stderr_total_bytes"] == 0
    assert 0 < result["process_peak_working_set_bytes"] < gate.RSS_LIMIT
    assert result["staging_disk_high_water_before_parent_receipt_bytes"] == 0


@pytest.mark.skipif(gate.os.name != "nt", reason="Windows Job Object gate")
def test_identity_helper_isolated_launch_needs_no_pythonpath(tmp_path: Path) -> None:
    result = gate.run_monitored(gate._helper_command(["--help"]), tmp_path)
    assert result["exit_code"] == 0
    assert "--source-wav" in result["stdout_utf8"]
    command = gate._child_command(
        "ebu-claves", gate.ITEMS["ebu-claves"], tmp_path / "child.json"
    )
    assert command[:4] == [str(gate.PYTHON), "-I", "-c", gate.ISOLATED_BOOTSTRAP]


@pytest.mark.skipif(gate.os.name != "nt", reason="Windows Job Object gate")
def test_job_gate_denies_descendant_process(tmp_path: Path) -> None:
    child = (
        "import subprocess,sys; "
        "\ntry: subprocess.run([sys.executable,'-c','print(1)'],check=True)"
        "\nexcept OSError: print('DESCENDANT_DENIED')"
        "\nelse: raise SystemExit(91)"
    )
    result = gate.run_monitored([str(gate.PYTHON), "-c", child], tmp_path)
    assert result["exit_code"] == 0
    assert result["stdout_utf8"] == "DESCENDANT_DENIED\r\n"


@pytest.mark.skipif(gate.os.name != "nt", reason="Windows Job Object gate")
def test_job_gate_fails_closed_on_output_overflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate, "OUTPUT_LIMIT_BYTES", 16)
    with pytest.raises(RuntimeError, match="bounded capture"):
        gate.run_monitored(
            [str(gate.PYTHON), "-c", "print('x' * 1024)"], tmp_path
        )


def test_frozen_source_authorities_match_real_pcm() -> None:
    for item in gate.ITEMS.values():
        snapshot = gate._identity_snapshot(item)
        gate._validate_static_authorities(
            snapshot, item, gate._sha256(Path(gate.__file__))
        )


def test_wrong_external_parent_hash_fails_closed() -> None:
    item = gate.ITEMS["ebu-claves"]
    snapshot = gate._identity_snapshot(item)
    with pytest.raises(RuntimeError, match="resource_gate"):
        gate._validate_static_authorities(snapshot, item, "0" * 64)


def test_parent_receipt_has_exact_fixed_point_accounting(tmp_path: Path) -> None:
    (tmp_path / "final-c-child.json").write_text("{}\n", encoding="utf-8")
    receipt = {
        "schema": gate.SCHEMA,
        "resources": {
            "staging_disk_high_water_before_parent_receipt_bytes": 3,
        },
    }
    encoded = gate._write_fixed_point_receipt(
        tmp_path / "parent-resource-receipt.json", receipt
    )
    parsed = json.loads(encoded)
    assert parsed["parent_receipt_bytes"] == len(encoded)
    assert parsed["staging_bytes_postflight"] == gate._scan_staging(tmp_path)
    assert parsed["staging_disk_high_water_bytes"] == parsed["staging_bytes_postflight"]


def test_parent_receipt_inclusive_disk_limit_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "final-c-child.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(gate, "DISK_LIMIT", 4)
    receipt = {
        "schema": gate.SCHEMA,
        "resources": {
            "staging_disk_high_water_before_parent_receipt_bytes": 3,
        },
    }
    with pytest.raises(OSError, match="receipt-inclusive"):
        gate._write_fixed_point_receipt(
            tmp_path / "parent-resource-receipt.json", receipt
        )


@pytest.mark.skipif(gate.os.name != "nt", reason="Windows Job Object gate")
def test_observed_sample_gap_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate, "POLL_SECONDS", 0.050)
    with pytest.raises(TimeoutError, match="sample gap"):
        gate.run_monitored(
            [str(gate.PYTHON), "-c", "import time; time.sleep(1)"], tmp_path
        )


def _windows_process_is_active(process_id: int) -> bool:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel.GetExitCodeProcess.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    handle = kernel.OpenProcess(0x1000, False, process_id)
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return exit_code.value == 259
    finally:
        if not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object gate")
def test_injected_monitor_failure_leaves_no_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = tmp_path / "child.pid"
    original_scan = gate._scan_staging

    def fail_after_child_started(root: Path) -> int:
        size = original_scan(root)
        if marker.exists():
            raise RuntimeError("injected monitor failure")
        return size

    monkeypatch.setattr(gate, "_scan_staging", fail_after_child_started)
    child = (
        "import os,pathlib,time; "
        f"pathlib.Path({str(marker)!r}).write_text(str(os.getpid())); "
        "time.sleep(60)"
    )
    with pytest.raises(RuntimeError, match="injected monitor failure"):
        gate.run_monitored([str(gate.PYTHON), "-c", child], tmp_path)
    process_id = int(marker.read_text(encoding="utf-8"))
    assert not _windows_process_is_active(process_id)
