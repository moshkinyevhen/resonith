from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

from experiments import r216_s12_opus_comparison as r216
from experiments import r219_s12_fixed_opus_direct as r219


def _attempt(bytes_: int, q5: int, attempt: int, quality: float = 0.0) -> dict:
    return {
        "bytes": bytes_,
        "q5": q5,
        "attempt": attempt,
        "raw_sha256": f"{attempt:064x}",
        "metrics": {"forbidden_selection_input": quality},
    }


def test_application_rule_uses_only_exact_registered_speech_token() -> None:
    assert r219.fixed_opus_config(["speech", "short"]).application == "speech"
    assert r219.fixed_opus_config(["music", "speech-like"]).application == "music"
    assert r219.fixed_opus_config(["Speech"]).application == "music"


def test_fixed_anchor_closes_all_material_configuration_coordinates() -> None:
    config = r219.fixed_opus_config(["music", "stereo"])
    assert config == r216.OpusConfig(
        mode="vbr",
        application="music",
        frame_us=20_000,
        phase_inversion=True,
        bandwidth_request=0,
        bandwidth_value=-1000,
        force_channels=-1000,
    )


def test_byte_selection_ignores_quality_and_uses_frozen_total_order() -> None:
    attempts = [
        _attempt(9_999, 1_000_002, 0, quality=1e9),
        _attempt(10_001, 1_000_000, 1, quality=-1e9),
        _attempt(9_999, 1_000_001, 2, quality=-1e12),
        _attempt(9_998, 999_999, 3, quality=-1e15),
    ]
    selected = r219.select_byte_match(attempts, 10_000)
    assert selected is not None
    assert selected["attempt"] == 2
    assert selected["byte_delta"] == -1


def test_byte_selection_final_tie_uses_attempt_index() -> None:
    selected = r219.select_byte_match(
        [_attempt(10_001, 1_000_000, 3), _attempt(10_001, 1_000_000, 1)],
        10_000,
    )
    assert selected is not None
    assert selected["attempt"] == 1


def test_unmatched_anchor_returns_none() -> None:
    # At 10,000 bytes the frozen tolerance is 64 bytes.
    assert r219.select_byte_match(
        [_attempt(9_935, 1_000_000, 0), _attempt(10_065, 1_000_001, 1)],
        10_000,
    ) is None


def test_complete_opus_argv_has_frozen_container_and_no_hidden_controls(
    tmp_path: Path,
) -> None:
    config = r219.fixed_opus_config(["speech"])
    command = r216._opus_command(
        Path("opusenc"), tmp_path / "input.wav", tmp_path / "output.opus",
        config, 12_345_678, 1234,
    )
    joined = " ".join(map(str, command))
    for required in (
        "--vbr", "--framesize 20", "--comp 10", "--expect-loss 0",
        "--max-delay 1000", "--discard-comments", "--discard-pictures",
        "--padding 0", "--serial 1234", "--speech",
    ):
        assert required in joined
    assert "--no-phase-inv" not in command
    assert "--set-ctl-int" not in command


def test_run_and_receipt_schemas_are_independent_from_r216() -> None:
    assert r219.RUN_SCHEMA != r216.RUN_SCHEMA
    assert r219.RECEIPT_SCHEMA != r216.RECEIPT_SCHEMA
    assert r219.RUNNER_SCHEMA != r216.RUNNER_SCHEMA
    assert r219.WORK_SCHEMA.startswith("resonith-r219-")


def test_preflight_hash_is_frozen_not_placeholder() -> None:
    assert len(r219.EXPECTED_PREFLIGHT_SHA256) == 64
    assert "TO_BE_FROZEN" not in r219.EXPECTED_PREFLIGHT_SHA256
    assert len(r219.EXPECTED_PYTHON_SHA256) == 64
    assert r219.host_identity() == r219.EXPECTED_HOST_IDENTITY


def test_single_authorized_short_timeout_redesign_is_exact() -> None:
    assert r219.SHORT_S11_SECONDS == 900.0
    assert r219.SHORT_WORKER_SECONDS == 1200.0
    assert r219.LONG_S11_SECONDS == 1200.0
    assert r219.LONG_WORKER_SECONDS == 2100.0
    assert r219.SHORT_S11_SECONDS < r219.SHORT_WORKER_SECONDS


def test_closed_child_records_and_enforces_post_exit_disk_use(
    tmp_path: Path,
) -> None:
    output = tmp_path / "child.bin"
    result = r219.run_bounded_closed(
        [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'x'*32)", str(output)],
        20.0, 256 * 1024 * 1024, tmp_path, 1024,
    )
    assert result["disk_bytes_before"] == 0
    assert result["disk_bytes_after"] == 32
    assert result["disk_limit_bytes"] == 1024
    assert result["rss_limit_bytes"] == 256 * 1024 * 1024


def test_receipt_authority_hash_detects_resume_mutation(tmp_path: Path) -> None:
    retained = tmp_path / "anchor.opus"
    retained.write_bytes(b"opus")
    item = {"id": "fixture"}
    request = tmp_path / "work-request.json"
    request.write_bytes(r219._canonical_json_bytes({"fixture": True}))
    receipt = {
        "schema": r219.RECEIPT_SCHEMA,
        "status": "PASS",
        "run_identity": "run",
        "item_id": "fixture",
        "work_request_sha256": r216.sha256_file(request),
        "work_request_bytes": request.stat().st_size,
        "manifest_item_sha256": r219._canonical_sha256(item),
        "retained_files": [
            {"path": "anchor.opus", "bytes": 4,
             "sha256": r216.sha256_file(retained)},
            {"path": "work-request.json", "bytes": request.stat().st_size,
             "sha256": r216.sha256_file(request)},
        ],
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    authority = r216.sha256_file(receipt_path)
    assert r219._verify_receipt(tmp_path, "run", item, authority) == receipt
    receipt["status"] = "PASS"
    receipt["extra_mutation"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    try:
        r219._verify_receipt(tmp_path, "run", item, authority)
    except RuntimeError as error:
        assert "authority hash drift" in str(error)
    else:
        raise AssertionError("receipt mutation was accepted")


def test_s11_stream_size_and_hash_are_cross_checked_against_report(
    tmp_path: Path,
) -> None:
    samples = np.zeros((16, 1), dtype=np.int16)
    stream = tmp_path / "challenger.resonith"
    stream.write_bytes(b"stream")
    r216.write_pcm16_channels(tmp_path / "challenger-decoded.wav", 48_000, samples)
    report = {
        "complete_bytes": stream.stat().st_size,
        "payload_sha256": r216.sha256_file(stream),
        "decoded_pcm16le_sha256": r216.pcm_sha256(samples),
    }
    (tmp_path / "s11-report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    loaded, decoded = r219._load_and_verify_s11(tmp_path, 48_000, samples.shape)
    assert loaded == report
    assert np.array_equal(decoded, samples)
    report["complete_bytes"] += 1
    (tmp_path / "s11-report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="report/stream identity mismatch"):
        r219._load_and_verify_s11(tmp_path, 48_000, samples.shape)


def test_worker_identity_recheck_rejects_source_toctou(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    core = tmp_path / "core.dll"
    opusenc = tmp_path / "opusenc.exe"
    opusdec = tmp_path / "opusdec.exe"
    for path, payload in (
        (source, b"source"), (core, b"core"),
        (opusenc, b"enc"), (opusdec, b"dec"),
    ):
        path.write_bytes(payload)
    request = {
        "worker_identities": r219._worker_identity_snapshot(
            source, core, opusenc, opusdec
        ),
        "dependency_versions": r219.dependency_versions(),
    }
    r219._verify_worker_identities(request, source, core, opusenc, opusdec)
    source.write_bytes(b"mutated")
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r219._verify_worker_identities(request, source, core, opusenc, opusdec)


def test_worker_identity_rejects_missing_and_wrong_analyzer(tmp_path: Path) -> None:
    paths = []
    for name in ("source.wav", "core.dll", "opusenc.exe", "opusdec.exe"):
        path = tmp_path / name
        path.write_bytes(name.encode("ascii"))
        paths.append(path)
    identities = r219._worker_identity_snapshot(*paths)
    request = {
        "worker_identities": dict(identities),
        "dependency_versions": r219.dependency_versions(),
    }
    request["worker_identities"].pop("analyzer")
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r219._verify_worker_identities(request, *paths)
    request["worker_identities"] = dict(identities, analyzer="0" * 64)
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r219._verify_worker_identities(request, *paths)


def test_closed_child_rejects_post_exit_disk_breach(tmp_path: Path) -> None:
    output = tmp_path / "oversized.bin"
    with pytest.raises(OSError, match="staging exceeded"):
        r219.run_bounded_closed(
            [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'x'*2048)", str(output)],
            20.0, 256 * 1024 * 1024, tmp_path, 1024,
        )


def test_closed_child_enforces_passed_short_rss_limit(
    tmp_path: Path,
) -> None:
    with pytest.raises(MemoryError, match="child RSS exceeded"):
        r219.run_bounded_closed(
            [sys.executable, "-c", "x=bytearray(64*1024*1024); import time; time.sleep(0.2)"],
            20.0, 8 * 1024 * 1024, tmp_path, 1024,
        )


def test_selected_opus_executes_exactly_one_metric_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = np.zeros((32, 1), dtype=np.int16)
    source = tmp_path / "source.wav"
    r216.write_pcm16_channels(source, 48_000, reference)
    encoded_payload = b"deterministic-ogg"
    calls = {"metrics": 0}

    def fake_run(command, timeout, rss_limit, disk_root, disk_limit):
        output = Path(command[-1])
        if "opusdec" in Path(command[0]).name:
            r216.write_pcm16_channels(output, 48_000, reference)
        else:
            output.write_bytes(encoded_payload)
        return {
            "wall_seconds": 0.0, "cpu_seconds": 0.0,
            "peak_rss_bytes": 0, "rss_limit_bytes": rss_limit,
            "disk_limit_bytes": disk_limit, "disk_bytes_before": 0,
            "disk_bytes_after": output.stat().st_size,
        }

    def fake_metrics(reference_samples, decoded_samples, rate, categories):
        calls["metrics"] += 1
        assert np.array_equal(reference_samples, decoded_samples)
        return {"single_pass": True}

    monkeypatch.setattr(r219, "run_bounded_closed", fake_run)
    monkeypatch.setattr(r219, "compute_metrics", fake_metrics)
    config = r219.fixed_opus_config(["music"])
    point = {
        "config": r216.asdict(config), "q5": 1_000_000, "attempt": 0,
        "bytes": len(encoded_payload), "byte_delta": 0,
        "raw_sha256": hashlib.sha256(encoded_payload).hexdigest(),
    }
    result = r219._decode_selected(
        point, source, tmp_path / "anchor.opus",
        tmp_path / "anchor-decoded.wav", bytes(32), "fixture", 48_000,
        reference.shape, ["music"], Path("opusenc"), Path("opusdec"),
        time.perf_counter() + 10.0, tmp_path / "ledger.jsonl",
        8 * 1024 * 1024, tmp_path, 1024 * 1024,
    )
    assert calls["metrics"] == 1
    assert result["metrics"] == {"single_pass": True}


def test_r218_analyzer_is_explicit_worker_and_controller_authority(
    tmp_path: Path,
) -> None:
    assert r219.EXPECTED_SOURCE_REVISION == "64521b19551d4b9688de10fe01c5302607a5beb1"
    assert r219.EXPECTED_ANALYZER_SHA256 == r216.sha256_file(
        r219.REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py"
    )
    local = []
    for name in ("source.wav", "core.dll", "opusenc.exe", "opusdec.exe"):
        path = tmp_path / name
        path.write_bytes(name.encode("ascii"))
        local.append(path)
    snapshot = r219._worker_identity_snapshot(*local)
    assert snapshot["analyzer"] == r219.EXPECTED_ANALYZER_SHA256


def test_worker_rejects_mutated_request_before_parsing(tmp_path: Path) -> None:
    original = r219._canonical_json_bytes({"schema": r219.WORK_SCHEMA, "item": {"id": "x"}})
    path = tmp_path / "work-request.json"
    path.write_bytes(original.replace(b'"x"', b'"y"'))
    with pytest.raises(RuntimeError, match="work-request seal mismatch"):
        r219._run_worker(path, hashlib.sha256(original).hexdigest())


def test_base_and_per_item_authority_digests_have_unambiguous_membership(
    tmp_path: Path,
) -> None:
    base = tmp_path / "base.bin"
    source = tmp_path / "source.wav"
    base.write_bytes(b"base")
    source.write_bytes(b"source-a")
    base_rows = [r219.Authority(base, r216.sha256_file(base), tmp_path)]
    first = base_rows + [r219.Authority(source, r216.sha256_file(source), tmp_path)]
    assert r219._authority_digest(base_rows) != r219._authority_digest(first)
    source.write_bytes(b"source-b")
    second = base_rows + [r219.Authority(source, r216.sha256_file(source), tmp_path)]
    assert r219._authority_digest(first) != r219._authority_digest(second)


@pytest.mark.skipif(sys.platform != "win32", reason="R-219 lock contract is Windows-only")
def test_under_lock_hash_rejects_mutation_before_file_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority_path = tmp_path / "authority.bin"
    authority_path.write_bytes(b"frozen")
    authority = r219.Authority(authority_path, r216.sha256_file(authority_path), tmp_path)
    original_open = r219._open_deny_write_delete
    mutated = {"done": False}

    def mutate_before_file_lock(path: Path, directory: bool) -> int:
        if not directory and Path(path).resolve() == authority_path.resolve() and not mutated["done"]:
            authority_path.write_bytes(b"changed")
            mutated["done"] = True
        return original_open(path, directory)

    monkeypatch.setattr(r219, "_open_deny_write_delete", mutate_before_file_lock)
    with pytest.raises(RuntimeError, match="under-lock authority mismatch"):
        with r219._locked_authorities([authority]):
            pass
    assert mutated["done"]


@pytest.mark.skipif(sys.platform != "win32", reason="R-219 lock contract is Windows-only")
def test_file_and_ancestor_locks_deny_cross_process_mutation_until_release(
    tmp_path: Path,
) -> None:
    root = tmp_path / "authority-root"
    root.mkdir()
    target = root / "authority.bin"
    target.write_bytes(b"frozen")
    replacement = root / "replacement.bin"
    replacement.write_bytes(b"replacement")
    authority = r219.Authority(target, r216.sha256_file(target), root)
    mutation = (
        "from pathlib import Path; import os,sys; "
        "p=Path(sys.argv[1]); mode=sys.argv[2]; "
        "(p.write_bytes(b'changed') if mode=='write' else os.replace(p, Path(str(p)+'.moved')))"
    )
    with r219._locked_authorities([authority]):
        denied_write = subprocess.run(
            [sys.executable, "-c", mutation, str(target), "write"],
            capture_output=True,
        )
        denied_rename = subprocess.run(
            [sys.executable, "-c", mutation, str(root), "rename"],
            capture_output=True,
        )
        denied_file_rename = subprocess.run(
            [sys.executable, "-c", mutation, str(target), "rename"],
            capture_output=True,
        )
        denied_replace = subprocess.run(
            [sys.executable, "-c", "import os,sys; os.replace(sys.argv[1],sys.argv[2])",
             str(replacement), str(target)],
            capture_output=True,
        )
        assert denied_write.returncode != 0
        assert denied_rename.returncode != 0
        assert denied_file_rename.returncode != 0
        assert denied_replace.returncode != 0
    target.write_bytes(b"changed")
    os.replace(root, Path(str(root) + ".moved"))


def test_old_r217_run_index_and_receipt_schemas_fail_closed(tmp_path: Path) -> None:
    material = {"generation": 219}
    with pytest.raises(RuntimeError, match="different or stale run"):
        r219._validate_resume_index(
            {
                "schema": "resonith-r217-s12-fixed-opus-run-index-1",
                "run_identity": "run",
                "run_material_sha256": r219._canonical_sha256(material),
                "base_authority_set_sha256": "base",
                "item_authority_set_sha256": {"x": "item"},
                "manifest_item_sha256": {"x": "manifest"},
            },
            "run", material, "base", {"x": "item"}, {"x": "manifest"}, ["x"],
        )
    request = tmp_path / "work-request.json"
    request.write_bytes(b"{}")
    receipt = {
        "schema": "resonith-r217-s12-fixed-opus-item-receipt-1",
        "status": "PASS", "run_identity": "run", "item_id": "x",
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale, unmatched, or corrupt"):
        r219._verify_receipt(tmp_path, "run", {"id": "x"})
    old_work = r219._canonical_json_bytes({
        "schema": "resonith-r217-s12-fixed-opus-work-request-1"
    })
    request.write_bytes(old_work)
    with pytest.raises(RuntimeError, match="invalid R-219 work-request schema"):
        r219._run_worker(request, hashlib.sha256(old_work).hexdigest())
    with pytest.raises(RuntimeError, match="invalid R-219 runner material schema"):
        r219._validate_runner_material({
            "schema": "resonith-r217-s12-fixed-opus-runner-1"
        })


def test_resume_index_requires_unique_manifest_order_prefix_and_exact_key_sets() -> None:
    material = {"schema": r219.RUNNER_SCHEMA}
    ids = ["a", "b", "c"]
    base = {
        "schema": r219.RUN_SCHEMA,
        "run_identity": "run",
        "run_material_sha256": r219._canonical_sha256(material),
        "base_authority_set_sha256": "base",
        "item_authority_set_sha256": {name: name for name in ids},
        "manifest_item_sha256": {name: f"m-{name}" for name in ids},
        "run_started_unix": 1.0,
    }
    for completed in (["b"], ["a", "a"], ["a", "c"]):
        index = dict(base, completed_item_ids=completed)
        index.update({field: {name: {} for name in set(completed)} for field in (
            "worker_resources", "work_request_sha256", "receipt_sha256"
        )})
        with pytest.raises(RuntimeError, match="completion prefix"):
            r219._validate_resume_index(
                index, "run", material, "base",
                {name: name for name in ids},
                {name: f"m-{name}" for name in ids}, ids,
            )
    valid = dict(base, completed_item_ids=["a"])
    valid.update({field: {"a": {}} for field in (
        "worker_resources", "work_request_sha256", "receipt_sha256"
    )})
    valid["receipt_sha256"]["extra"] = {}
    with pytest.raises(RuntimeError, match="receipt_sha256 key set"):
        r219._validate_resume_index(
            valid, "run", material, "base", {name: name for name in ids},
            {name: f"m-{name}" for name in ids}, ids,
        )


def test_actual_r217_tree_cannot_resume_as_r219() -> None:
    root = r219.REPOSITORY / "artifacts/r217-s12-fixed-opus-direct-v2"
    assert (root / "run-index.json").is_file()
    material = {"schema": r219.RUNNER_SCHEMA}
    with pytest.raises(RuntimeError, match="different or stale run"):
        r219._load_resume_index(
            root, "run", material, "base", {"x": "item"},
            {"x": "manifest"}, ["x"],
        )
    with pytest.raises(RuntimeError, match="requires a nonexistent output root"):
        r219._create_fresh_root(root)


def test_r219_exposes_only_direct_two_codec_comparison() -> None:
    source = Path(r219.__file__).read_text(encoding="utf-8")
    assert "previous_resonith" not in source
    assert "preceding_resonith" not in source
    assert "_frontier_search" not in source
    assert "for config in" not in source


def test_emitted_aggregate_contains_only_resonith_and_fixed_opus(
    tmp_path: Path,
) -> None:
    item = {"id": "fixture"}
    final = tmp_path / "fixture"
    final.mkdir()
    request_bytes = r219._canonical_json_bytes({"schema": r219.WORK_SCHEMA})
    request = final / "work-request.json"
    request.write_bytes(request_bytes)
    metric = {
        "waveform": {"snr_db": 1.0},
        "spectral": {
            "log_mel_rmse": 2.0,
            "magnitude_cosine_similarity": 0.5,
        },
    }
    receipt = {
        "schema": r219.RECEIPT_SCHEMA,
        "status": "PASS",
        "run_identity": "run",
        "item_id": "fixture",
        "work_request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "work_request_bytes": len(request_bytes),
        "manifest_item_sha256": r219._canonical_sha256(item),
        "base_authority_set_sha256": "base",
        "item_authority_set_sha256": "item",
        "retained_files": [{
            "path": "work-request.json", "bytes": len(request_bytes),
            "sha256": hashlib.sha256(request_bytes).hexdigest(),
        }],
        "resonith": {"complete_bytes": 100, "metrics": metric},
        "opus": {
            "configuration": {"application": "music"},
            "selected": {"bytes": 101, "byte_delta": 1, "metrics": metric},
        },
    }
    r216.write_json_fsynced(final / "receipt.json", receipt)
    receipt_hash = r216.sha256_file(final / "receipt.json")
    r219._aggregate(
        tmp_path, {"items": [item]}, "run", {"schema": r219.RUNNER_SCHEMA},
        {"fixture": receipt_hash}, {"fixture": request_bytes},
        "base", {"fixture": "item"},
    )
    aggregate = json.loads((tmp_path / "aggregate.json").read_text(encoding="utf-8"))
    assert set(aggregate["rows"][0]) == {
        "id", "application", "resonith_bytes", "opus_bytes", "byte_delta",
        "resonith_snr_db", "opus_snr_db", "resonith_log_mel_rmse",
        "opus_log_mel_rmse", "resonith_magnitude_cosine",
        "opus_magnitude_cosine",
    }
    report = (tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert "| Item | App | Resonith bytes | Opus bytes |" in report
    assert "Previous Resonith" not in report
