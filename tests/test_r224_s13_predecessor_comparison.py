"""Focused contract tests for the bounded R-224 historical comparison."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import stat
import subprocess
import time
import wave
import zipfile

import numpy as np
import pytest

from experiments import r224_s13_predecessor_comparison as r224


def _zip(path: Path, entries: list[tuple[str, bytes, int]]) -> None:
    with zipfile.ZipFile(path, "w") as output:
        for name, payload, mode in entries:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            output.writestr(info, payload)


@pytest.mark.parametrize("name", [
    "../escape.py", "/absolute.py", "C:/drive.py", "file.py:ads",
    "back\\slash.py", "a/../../escape.py", "./alias.py",
])
def test_safe_archive_member_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError):
        r224.safe_archive_member(name)


def test_safe_archive_member_accepts_normal_git_path() -> None:
    assert r224.safe_archive_member("reference/maf_p0/lapped_oracle.py").as_posix() == (
        "reference/maf_p0/lapped_oracle.py"
    )


def test_extract_git_archive_accepts_regular_files(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    _zip(archive, [("reference/test.py", b"value = 1\n", stat.S_IFREG | 0o644)])
    rows = r224.extract_git_archive(archive, tmp_path / "tree")
    assert rows == [{
        "path": "reference/test.py", "kind": "file",
        "mode": stat.S_IFREG | 0o644, "bytes": 10,
        "crc32": rows[0]["crc32"],
        "sha256": r224.sha256_bytes(b"value = 1\n"),
    }]


def test_extract_git_archive_rejects_symlink(tmp_path: Path) -> None:
    archive = tmp_path / "link.zip"
    _zip(archive, [("link", b"target", stat.S_IFLNK | 0o777)])
    with pytest.raises(ValueError, match="non-regular"):
        r224.extract_git_archive(archive, tmp_path / "tree")


def test_extract_git_archive_rejects_case_alias(tmp_path: Path) -> None:
    archive = tmp_path / "alias.zip"
    _zip(archive, [
        ("A.py", b"a", stat.S_IFREG | 0o644),
        ("a.py", b"b", stat.S_IFREG | 0o644),
    ])
    with pytest.raises(ValueError, match="duplicate archive alias"):
        r224.extract_git_archive(archive, tmp_path / "tree")


def test_ancestry_check_does_not_scan_unrelated_siblings(tmp_path: Path) -> None:
    sibling = tmp_path / "unrelated"
    sibling.mkdir()
    (sibling / "opaque.bin").write_bytes(b"not part of the evidence root")
    target_parent = tmp_path / "evidence"
    target_parent.mkdir()
    r224.require_ancestry_reparse_free(target_parent)


@pytest.mark.skipif(r224.os.name != "nt", reason="Windows junction contract")
def test_lexical_ancestry_rejects_actual_junction(tmp_path: Path) -> None:
    target = tmp_path / "clean-target"
    target.mkdir()
    junction = tmp_path / "junction"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        pytest.skip(f"junction creation unavailable: {result.stderr}")
    try:
        with pytest.raises(RuntimeError, match="reparse point"):
            r224.require_ancestry_reparse_free(junction / "evidence")
    finally:
        junction.rmdir()


@pytest.mark.skipif(r224.os.name != "nt", reason="Windows junction contract")
def test_final_root_walk_rejects_nested_actual_junction(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    target = tmp_path / "clean-target"
    root.mkdir()
    target.mkdir()
    junction = root / "nested"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        pytest.skip(f"junction creation unavailable: {result.stderr}")
    try:
        with pytest.raises(RuntimeError, match="reparse point"):
            r224.require_reparse_free(root)
    finally:
        junction.rmdir()


def test_lexical_absolute_rejects_parent_components() -> None:
    with pytest.raises(ValueError, match="relative path component"):
        r224.lexical_absolute(Path("G:/Resonith/../shadow"))


def test_validate_module_origins_accepts_extracted_tree(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    module = root / "reference/maf_p0/module.py"
    module.parent.mkdir(parents=True)
    module.write_text("", encoding="utf-8")
    r224.validate_module_origins({"reference.maf_p0.module": str(module)}, root)


def test_validate_module_origins_rejects_current_or_shadow_module(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    shadow = tmp_path / "shadow.py"
    shadow.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError, match="escaped archive"):
        r224.validate_module_origins({"reference.maf_p0.module": str(shadow)}, root)


def test_historical_inventory_rejects_originless_project_module(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    with pytest.raises(RuntimeError, match="no file origin"):
        r224.validate_historical_module_inventory(
            {"reference.maf_p0.shadow": {"kind": "originless", "origin": None}},
            root,
        )


def test_validate_config_accepts_only_the_frozen_tuple() -> None:
    r224.validate_config(dict(r224.FROZEN_CONFIG))
    mutated = dict(r224.FROZEN_CONFIG)
    mutated["density_backend"] = "fixed"
    with pytest.raises(ValueError, match="configuration drift"):
        r224.validate_config(mutated)


def test_require_bytes_equal_detects_forced_payload_mismatch() -> None:
    r224.require_bytes_equal(b"same", b"same", "payload")
    with pytest.raises(RuntimeError, match="payload mismatch"):
        r224.require_bytes_equal(b"old", b"current", "payload")


def test_require_bytes_equal_detects_forced_pcm_mismatch() -> None:
    with pytest.raises(RuntimeError, match="PCM mismatch"):
        r224.require_bytes_equal(b"\x00\x00", b"\x01\x00", "PCM")


def test_mismatch_retention_always_publishes_both_artifacts(tmp_path: Path) -> None:
    samples = np.array([[1], [-2], [3]], dtype=np.int16)
    rows = r224.retain_mismatch_artifacts(tmp_path, b"historical", 8000, samples)
    assert [row["path"] for row in rows] == [
        "historical.resonith", "historical-decoded.wav"
    ]
    assert all((tmp_path / row["path"]).is_file() for row in rows)
    assert not list(tmp_path.glob("*.tmp"))
    rate, frames, channels, pcm = r224.read_pcm16(tmp_path / "historical-decoded.wav")
    assert (rate, frames, channels, pcm) == (
        8000, 3, 1, samples.astype("<i2").tobytes()
    )


def test_canonical_digest_changes_for_manifest_or_receipt_drift() -> None:
    original = {"manifest": "a", "receipt": "b"}
    changed = json.loads(json.dumps(original))
    changed["receipt"] = "c"
    assert r224.canonical_digest(original) != r224.canonical_digest(changed)


def test_require_frozen_authorities_rejects_dll_drift() -> None:
    snapshot = {
        "manifest_sha256": r224.EXPECTED_MANIFEST_SHA256,
        "r221_index_sha256": r224.EXPECTED_R221_INDEX_SHA256,
        "r221_aggregate_sha256": r224.EXPECTED_R221_AGGREGATE_SHA256,
        "preflight_sha256": r224.EXPECTED_PREFLIGHT_SHA256,
        "native_core_sha256": "0" * 64,
    }
    with pytest.raises(RuntimeError, match="native_core_sha256"):
        r224.require_frozen_authorities(snapshot)


def _write_wav(path: Path, payload: bytes) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(8000)
        output.writeframes(payload)


def _current_item_fixture(tmp_path: Path, monkeypatch) -> tuple[dict, dict, dict[str, Path]]:
    root = tmp_path / "r221"
    item_root = root / "fixture"
    resonith = item_root / "resonith"
    resonith.mkdir(parents=True)
    source_path = tmp_path / "source.wav"
    pcm = b"\x01\x00\x02\x00"
    _write_wav(source_path, pcm)
    stream = resonith / "challenger.resonith"
    stream.write_bytes(b"stream")
    decoded = resonith / "challenger-decoded.wav"
    _write_wav(decoded, pcm)
    item = {
        "id": "fixture",
        "order": 1,
        "categories": ["test"],
        "challenger": {
            "coefficients_per_frame": 1, "half_window": 2, "band_count": 1,
        },
        "source": {
            "sample_rate": 8000, "frame_count": 2, "channel_count": 1,
            "duration_seconds": 0.00025,
            "file_sha256": r224.sha256_file(source_path),
            "pcm16_payload_sha256": r224.sha256_bytes(pcm),
            "path": "fixture.wav",
        },
    }
    request_path = item_root / "work-request.json"
    request_path.write_bytes(r224.json_bytes({
        "schema": "resonith-r221-s12-bounded-rate-work-request-1",
        "run_identity": r224.EXPECTED_R221_RUN_IDENTITY,
        "manifest_sha256": r224.EXPECTED_MANIFEST_SHA256,
        "item": item, "source_path": str(source_path),
    }))
    receipt_path = item_root / "receipt.json"
    receipt_path.write_bytes(r224.json_bytes({
        "status": "PASS",
        "item_id": "fixture",
        "order": 1,
        "resonith": {
            "selected_kind": "truth-fallback",
            "payload_sha256": r224.sha256_file(stream),
            "complete_bytes": stream.stat().st_size,
            "decoded_pcm16le_sha256": r224.sha256_bytes(pcm),
        },
        "retained_files": [
            {"path": "resonith/challenger.resonith", "bytes": stream.stat().st_size, "sha256": r224.sha256_file(stream)},
            {"path": "resonith/challenger-decoded.wav", "bytes": decoded.stat().st_size, "sha256": r224.sha256_file(decoded)},
        ],
    }))
    index = {
        "receipt_sha256": {"fixture": r224.sha256_file(receipt_path)},
        "work_request_sha256": {"fixture": r224.sha256_file(request_path)},
    }
    monkeypatch.setattr(r224, "R221_ROOT", root)
    return item, index, {
        "source": source_path, "stream": stream, "decoded": decoded,
        "receipt": receipt_path, "request": request_path,
    }


def test_current_item_production_validator_accepts_frozen_fixture(
    tmp_path: Path, monkeypatch
) -> None:
    item, index, _ = _current_item_fixture(tmp_path, monkeypatch)
    binding = r224.validate_current_item(item, index)
    assert binding["current_stream_bytes"] == len(b"stream")


@pytest.mark.parametrize("target", ["source", "stream", "decoded", "receipt", "request"])
def test_current_item_production_validator_rejects_authority_drift(
    target: str, tmp_path: Path, monkeypatch
) -> None:
    item, index, paths = _current_item_fixture(tmp_path, monkeypatch)
    paths[target].write_bytes(paths[target].read_bytes() + b"drift")
    with pytest.raises((RuntimeError, ValueError, wave.Error)):
        r224.validate_current_item(item, index)


def test_current_item_production_validator_rejects_source_pcm_drift(
    tmp_path: Path, monkeypatch
) -> None:
    item, index, paths = _current_item_fixture(tmp_path, monkeypatch)
    _write_wav(paths["source"], b"\x03\x00\x04\x00")
    item["source"]["file_sha256"] = r224.sha256_file(paths["source"])
    request = r224.load_json(paths["request"])
    request["item"] = item
    paths["request"].write_bytes(r224.json_bytes(request))
    index["work_request_sha256"]["fixture"] = r224.sha256_file(paths["request"])
    with pytest.raises(RuntimeError, match="source PCM tuple drift"):
        r224.validate_current_item(item, index)


def _valid_worker_receipt() -> tuple[dict, dict]:
    environment = {"SystemRoot": "C:/Windows"}
    execution_argv = ["python.exe", "-I", "worker.py", "--worker", "request.json"]
    request = {
        "item_id": "fixture",
        "source_tuple": [8000, 2, 1, "p" * 64],
        "source_file_sha256": "s" * 64,
        "current_stream_sha256": "b" * 64,
        "current_stream_bytes": 123,
        "current_decoded_pcm16le_sha256": "p" * 64,
        "current_stream_path": "stream",
        "current_decoded_wav_path": "decoded.wav",
        "current_decoded_wav_sha256": "w" * 64,
        "r221_receipt_path": "receipt.json",
        "r221_receipt_sha256": "r" * 64,
        "r221_work_request_path": "request.json",
        "r221_work_request_sha256": "q" * 64,
        "environment": environment,
        "execution_argv": execution_argv,
        "execution_argv_sha256": r224.canonical_digest(execution_argv),
    }
    receipt = {
        "schema": r224.RECEIPT_SCHEMA,
        "status": "PASS",
        "proof_kind": "actual-ca87dec-counterfactual-execution",
        "item_id": "fixture",
        "payload_identity": True,
        "decoded_pcm_identity": True,
        "mismatch_artifacts": [],
        "configuration": dict(r224.FROZEN_CONFIG),
        "source": {
            "sample_rate": 8000, "frames": 2, "channels": 1,
            "pcm16le_sha256": "p" * 64, "file_sha256": "s" * 64,
            "dtype": "int16", "byte_order": "little-endian",
        },
        "historical": {
            "payload_sha256": "b" * 64, "payload_bytes": 123,
            "decoded_pcm16le_sha256": "p" * 64,
        },
        "current": {
            "payload_sha256": "b" * 64, "payload_bytes": 123,
            "decoded_pcm16le_sha256": "p" * 64,
        },
        "references": {
            "current_stream_path": "stream",
            "current_stream_sha256": "b" * 64,
            "current_decoded_wav_path": "decoded.wav",
            "current_decoded_wav_sha256": "w" * 64,
            "r221_receipt_path": "receipt.json",
            "r221_receipt_sha256": "r" * 64,
            "r221_work_request_path": "request.json",
            "r221_work_request_sha256": "q" * 64,
        },
        "runtime": {
            "loaded_native_core": str(r224.NATIVE_CORE.resolve()),
            "loaded_native_core_sha256": r224.EXPECTED_NATIVE_CORE_SHA256,
            "isolated": 1, "no_user_site": 1, "safe_path": True,
            "environment": r224.normalized_environment(environment),
            "execution_argv": execution_argv,
            "execution_argv_sha256": r224.canonical_digest(execution_argv),
        },
    }
    receipt["receipt_material_sha256"] = r224.canonical_digest(receipt)
    return receipt, request


@pytest.mark.parametrize("mutation", [
    "material", "schema", "payload", "pcm", "runtime",
    "argv-receipt", "argv-request",
])
def test_worker_receipt_validator_rejects_decision_drift(mutation: str) -> None:
    receipt, request = _valid_worker_receipt()
    if mutation == "material":
        receipt["receipt_material_sha256"] = "0" * 64
    elif mutation == "schema":
        receipt["schema"] = "shadow"
        receipt["receipt_material_sha256"] = r224.canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_material_sha256"}
        )
    elif mutation == "payload":
        receipt["historical"]["payload_sha256"] = "0" * 64
        receipt["receipt_material_sha256"] = r224.canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_material_sha256"}
        )
    elif mutation == "pcm":
        receipt["decoded_pcm_identity"] = False
        receipt["receipt_material_sha256"] = r224.canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_material_sha256"}
        )
    elif mutation == "runtime":
        receipt["runtime"]["isolated"] = 0
        receipt["receipt_material_sha256"] = r224.canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_material_sha256"}
        )
    elif mutation == "argv-receipt":
        receipt["runtime"]["execution_argv"] = ["shadow.exe"]
        receipt["runtime"]["execution_argv_sha256"] = r224.canonical_digest(
            ["shadow.exe"]
        )
        receipt["receipt_material_sha256"] = r224.canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_material_sha256"}
        )
    else:
        request["execution_argv"] = ["shadow.exe"]
        request["execution_argv_sha256"] = r224.canonical_digest(["shadow.exe"])
    with pytest.raises(RuntimeError):
        r224.validate_worker_receipt(receipt, request)


def test_worker_receipt_validator_accepts_bound_receipt() -> None:
    receipt, request = _valid_worker_receipt()
    r224.validate_worker_receipt(receipt, request)


def test_run_bounded_records_post_exit_lifetime_peak_for_fast_child(
    tmp_path: Path,
) -> None:
    result = r224.run_bounded(
        [str(r224.PYTHON), "-I", "-c", "x=bytearray(32*1024*1024)"],
        timeout=60, rss_limit=r224.GIB, cwd=tmp_path,
        environment=r224.isolated_environment(), disk_root=tmp_path,
        disk_limit=r224.MIB,
    )
    assert result["final_post_exit_sample"] is True
    assert result["final_resource_sample_count"] == 1
    assert result["peak_rss_bytes"] > 16 * r224.MIB


def test_run_bounded_rejects_fast_child_final_lifetime_peak(
    tmp_path: Path, monkeypatch
) -> None:
    calls = 0
    original = r224._final_process_sample

    def counted_final(handle):
        nonlocal calls
        calls += 1
        return original(handle)

    monkeypatch.setattr(r224, "_final_process_sample", counted_final)
    with pytest.raises(MemoryError, match="RSS exceeded"):
        r224.run_bounded(
            [str(r224.PYTHON), "-I", "-c", "x=bytearray(64*1024*1024)"],
            timeout=60, rss_limit=20 * r224.MIB, cwd=tmp_path,
            environment=r224.isolated_environment(), disk_root=tmp_path,
            disk_limit=r224.MIB,
        )
    assert calls == 1


def test_run_bounded_fails_closed_when_post_exit_query_fails(
    tmp_path: Path, monkeypatch
) -> None:
    def fail_final(_handle):
        raise RuntimeError("post-exit counter unavailable")

    monkeypatch.setattr(r224, "_final_process_sample", fail_final)
    with pytest.raises(RuntimeError, match="post-exit counter unavailable"):
        r224.run_bounded(
            [str(r224.PYTHON), "-I", "-c", "pass"],
            timeout=60, rss_limit=r224.GIB, cwd=tmp_path,
            environment=r224.isolated_environment(), disk_root=tmp_path,
            disk_limit=r224.MIB,
        )


def test_aggregate_deadline_and_final_storage_fail_closed() -> None:
    with pytest.raises(TimeoutError, match="30-minute"):
        r224.remaining_deadline(time.perf_counter() - 1.0, 300.0)
    with pytest.raises(RuntimeError, match="retained-storage"):
        r224.require_storage_budget(90, 10, 100)


def test_request_launch_and_aggregate_argv_mutations_fail_closed() -> None:
    _, request = _valid_worker_receipt()
    expected = request["execution_argv"]
    digest = request["execution_argv_sha256"]
    r224.validate_execution_argv(expected, digest, request)
    with pytest.raises(RuntimeError, match="argv"):
        r224.validate_execution_argv([*expected, "shadow"], digest, request)
    bad_request = dict(request)
    bad_request["execution_argv_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="argv"):
        r224.validate_execution_argv(expected, digest, bad_request)
    rows = [{
        "item_id": request["item_id"],
        "execution_argv": expected,
        "execution_argv_sha256": digest,
    }]
    requests = {str(request["item_id"]): request}
    r224.validate_aggregate_argv_rows(rows, requests)
    rows[0]["execution_argv"] = ["shadow.exe"]
    rows[0]["execution_argv_sha256"] = r224.canonical_digest(["shadow.exe"])
    with pytest.raises(RuntimeError, match="argv"):
        r224.validate_aggregate_argv_rows(rows, requests)


@pytest.fixture(scope="module")
def extracted_ca87dec(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("r224-ca87dec")
    archive = root / "ca87dec.zip"
    subprocess.run(
        [str(r224.GIT), "-C", str(r224.REPOSITORY), "archive", "--format=zip",
         f"--output={archive}", r224.EXPECTED_HISTORICAL_COMMIT],
        cwd=r224.REPOSITORY, check=True, capture_output=True, text=True,
    )
    tree = root / "tree"
    r224.extract_git_archive(archive, tree)
    return tree


def _write_pcm_tuple(
    path: Path, rate: int, channels: int, payload: bytes
) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(payload)


@pytest.mark.parametrize(
    ("kind", "expected_payload_identity", "expected_pcm_identity"),
    [("payload-only", False, True), ("pcm-only", True, False)],
)
def test_actual_worker_mismatch_branch_retains_both_artifacts(
    kind: str, expected_payload_identity: bool, expected_pcm_identity: bool,
    extracted_ca87dec: Path, tmp_path: Path,
) -> None:
    sealed_root = r224.R221_ROOT / "speech"
    sealed_request = r224.load_json(sealed_root / "work-request.json")
    item = sealed_request["item"]
    source = item["source"]
    item_root = tmp_path / kind
    item_root.mkdir()
    comparator_stream = item_root / "comparator.resonith"
    comparator_wav = item_root / "comparator.wav"
    shutil.copyfile(sealed_root / "resonith/challenger.resonith", comparator_stream)
    shutil.copyfile(sealed_root / "resonith/challenger-decoded.wav", comparator_wav)
    if kind == "payload-only":
        payload = bytearray(comparator_stream.read_bytes())
        payload[len(payload) // 2] ^= 0x01
        comparator_stream.write_bytes(payload)
    else:
        rate, _, channels, pcm = r224.read_pcm16(comparator_wav)
        changed = bytearray(pcm)
        changed[len(changed) // 2] ^= 0x01
        _write_pcm_tuple(comparator_wav, rate, channels, bytes(changed))
    comparator_rate, comparator_frames, comparator_channels, comparator_pcm = (
        r224.read_pcm16(comparator_wav)
    )
    request_path = item_root / "work-request.json"
    environment = r224.isolated_environment()
    command = [
        str(r224.PYTHON), "-I", "-B", "-X", "utf8",
        str(Path(r224.__file__).resolve()), "--worker", str(request_path),
    ]
    request = {
        "schema": r224.WORK_SCHEMA,
        "item_id": f"speech-{kind}",
        "repository": str(r224.REPOSITORY.resolve()),
        "extracted_root": str(extracted_ca87dec.resolve()),
        "historical_commit": r224.EXPECTED_HISTORICAL_COMMIT,
        "historical_tree": r224.EXPECTED_HISTORICAL_TREE,
        "native_core": str(r224.NATIVE_CORE.resolve()),
        "source_path": sealed_request["source_path"],
        "source_file_sha256": source["file_sha256"],
        "source_tuple": [
            source["sample_rate"], source["frame_count"], source["channel_count"],
            source["pcm16_payload_sha256"],
        ],
        "coefficients_per_frame": item["challenger"]["coefficients_per_frame"],
        "half_window": item["challenger"]["half_window"],
        "band_count": item["challenger"]["band_count"],
        "configuration": dict(r224.FROZEN_CONFIG),
        "current_stream_path": str(comparator_stream),
        "current_stream_sha256": r224.sha256_file(comparator_stream),
        "current_stream_bytes": comparator_stream.stat().st_size,
        "current_decoded_wav_path": str(comparator_wav),
        "current_decoded_wav_sha256": r224.sha256_file(comparator_wav),
        "current_decoded_pcm16le_sha256": r224.sha256_bytes(comparator_pcm),
        "r221_receipt_path": str(sealed_root / "receipt.json"),
        "r221_receipt_sha256": r224.sha256_file(sealed_root / "receipt.json"),
        "r221_work_request_path": str(sealed_root / "work-request.json"),
        "r221_work_request_sha256": r224.sha256_file(
            sealed_root / "work-request.json"
        ),
        "environment": environment,
        "execution_argv": command,
        "execution_argv_sha256": r224.canonical_digest(command),
    }
    assert (comparator_rate, comparator_frames, comparator_channels) == (
        source["sample_rate"], source["frame_count"], source["channel_count"]
    )
    r224.write_json_atomic(request_path, request)
    with pytest.raises(RuntimeError, match="subprocess failed"):
        r224.run_bounded(
            command, timeout=300, rss_limit=4 * r224.GIB,
            cwd=extracted_ca87dec, environment=environment,
            disk_root=item_root, disk_limit=512 * r224.MIB,
        )
    receipt = r224.load_json(item_root / "receipt.json")
    r224.validate_mismatch_receipt(receipt, request, item_root)
    assert receipt["payload_identity"] is expected_payload_identity
    assert receipt["decoded_pcm_identity"] is expected_pcm_identity
    assert (item_root / "historical.resonith").is_file()
    assert (item_root / "historical-decoded.wav").is_file()
    assert not (item_root / "aggregate.json").exists()


def test_runner_exposes_no_mismatch_injection_hook() -> None:
    source = Path(r224.__file__).read_text(encoding="utf-8")
    for forbidden in ("--force-mismatch", "R224_FORCE_MISMATCH", "force_mismatch="):
        assert forbidden not in source


def test_isolated_environment_excludes_pythonpath_and_project_paths() -> None:
    environment = r224.isolated_environment()
    assert "PYTHONPATH" not in environment
    assert "PATH" not in environment
    assert all("Resonith" not in value for value in environment.values())


def test_environment_comparison_is_case_insensitive_on_windows() -> None:
    assert r224.normalized_environment({"SystemRoot": "C:/Windows"}) == {
        "SYSTEMROOT": "C:/Windows"
    }
