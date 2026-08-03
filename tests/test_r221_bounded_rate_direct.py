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
from experiments import r221_s12_bounded_rate_direct as r221


def _attempt(bytes_: int, q5: int, attempt: int, quality: float = 0.0) -> dict:
    return {
        "bytes": bytes_,
        "q5": q5,
        "attempt": attempt,
        "raw_sha256": f"{attempt:064x}",
        "normalized_sha256": f"{q5:064x}",
        "metrics": {"forbidden_selection_input": quality},
    }


def test_application_rule_uses_only_exact_registered_speech_token() -> None:
    assert r221.fixed_opus_config(["speech", "short"]).application == "speech"
    assert r221.fixed_opus_config(["music", "speech-like"]).application == "music"
    assert r221.fixed_opus_config(["Speech"]).application == "music"


def test_fixed_anchor_closes_all_material_configuration_coordinates() -> None:
    config = r221.fixed_opus_config(["music", "stereo"])
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
    selected = r221.select_byte_match(attempts, 10_000)
    assert selected is not None
    assert selected["attempt"] == 2
    assert selected["byte_delta"] == -1


def test_byte_selection_final_tie_uses_attempt_index() -> None:
    selected = r221.select_byte_match(
        [_attempt(10_001, 1_000_000, 3), _attempt(10_001, 1_000_000, 1)],
        10_000,
    )
    assert selected is not None
    assert selected["attempt"] == 1


def test_unmatched_anchor_returns_none() -> None:
    # At 10,000 bytes the frozen tolerance is 64 bytes.
    assert r221.select_byte_match(
        [_attempt(9_935, 1_000_000, 0), _attempt(10_065, 1_000_001, 1)],
        10_000,
    ) is None


def test_nearest_fallback_ignores_quality_and_uses_frozen_order() -> None:
    selected = r221.select_nearest_rate_point(
        [
            _attempt(9_900, 900, 0, quality=-1e30),
            _attempt(10_100, 800, 1, quality=1e30),
            _attempt(10_100, 700, 2, quality=-1e99),
        ],
        10_000,
    )
    assert selected["attempt"] == 0
    assert selected["byte_delta"] == -100


def test_duplicate_q5_collapses_earliest_or_fails_determinism() -> None:
    duplicate = [_attempt(9_000, 100, 7), _attempt(9_000, 100, 2)]
    observations = r221._canonical_rate_observations(duplicate)
    assert len(observations) == 1
    assert observations[0]["attempt"] == 2
    inconsistent = [dict(duplicate[0]), dict(duplicate[1], bytes=9_001)]
    with pytest.raises(RuntimeError, match="repeated-q5 determinism failure"):
        r221._canonical_rate_observations(inconsistent)
    inconsistent_hash = [
        dict(duplicate[0]), dict(duplicate[1], normalized_sha256="f" * 64)
    ]
    with pytest.raises(RuntimeError, match="repeated-q5 determinism failure"):
        r221._canonical_rate_observations(inconsistent_hash)


def test_tightest_observed_bracket_is_nonmonotone_safe_and_exact() -> None:
    attempts = [
        _attempt(8_000, 100, 0),
        _attempt(12_000, 300, 1),
        _attempt(8_500, 250, 2),
        _attempt(11_000, 280, 3),
        _attempt(7_500, 260, 4),
    ]
    lower, upper = r221._tightest_legal_bracket(attempts, 10_000)
    assert (lower["q5"], upper["q5"]) == (260, 280)
    assert 260 + (280 - 260) // 2 == 270


def test_bounded_search_preserves_four_feedback_points_then_bisects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bytes_by_q5 = {1000: 9000, 2000: 11000, 1500: 9500, 1750: 10500, 1625: 10010}
    feedback = {1000: 2000, 2000: 1500, 1500: 1750, 1750: 1600}
    observed: list[int] = []

    def fake_encode(*args, **kwargs):
        output = args[2]
        q5 = int(args[6])
        output.write_bytes(b"x")
        observed.append(q5)
        return _attempt(bytes_by_q5[q5], q5, len(observed) - 1)

    monkeypatch.setattr(r221, "_encode_point_closed", fake_encode)
    monkeypatch.setattr(r216, "initial_q5", lambda *args: 1000)
    monkeypatch.setattr(r216, "feedback_q5", lambda q5, *args: feedback[q5])
    records = r221._feedback_search_closed(
        Path("opusenc"), tmp_path / "source.wav", tmp_path, bytes(32),
        "fixture", r221.fixed_opus_config(["music"]), 10_000, 48_000,
        48_000, 1, 10.0, time.perf_counter() + 10.0,
        tmp_path / "ledger.jsonl", 1 << 30, tmp_path, 1 << 30,
    )
    assert observed == [1000, 2000, 1500, 1750, 1625]
    assert len(records) == 5
    assert r221.select_byte_match(records, 10_000)["q5"] == 1625


def test_absent_bracket_performs_zero_extra_encodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[int] = []

    def fake_encode(*args, **kwargs):
        output = args[2]
        q5 = int(args[6])
        output.write_bytes(b"x")
        observed.append(q5)
        return _attempt(9_000 - len(observed), q5, len(observed) - 1)

    monkeypatch.setattr(r221, "_encode_point_closed", fake_encode)
    monkeypatch.setattr(r216, "initial_q5", lambda *args: 1000)
    monkeypatch.setattr(r216, "feedback_q5", lambda q5, *args: q5 + 1)
    records = r221._feedback_search_closed(
        Path("opusenc"), tmp_path / "source.wav", tmp_path, bytes(32),
        "fixture", r221.fixed_opus_config(["music"]), 10_000, 48_000,
        48_000, 1, 10.0, time.perf_counter() + 10.0,
        tmp_path / "ledger.jsonl", 1 << 30, tmp_path, 1 << 30,
    )
    assert len(records) == 4
    assert observed == [1000, 1001, 1002, 1003]


def test_complete_opus_argv_has_frozen_container_and_no_hidden_controls(
    tmp_path: Path,
) -> None:
    config = r221.fixed_opus_config(["speech"])
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
    assert r221.RUN_SCHEMA != r216.RUN_SCHEMA
    assert r221.RECEIPT_SCHEMA != r216.RECEIPT_SCHEMA
    assert r221.RUNNER_SCHEMA != r216.RUNNER_SCHEMA
    assert r221.WORK_SCHEMA.startswith("resonith-r221-")


def test_preflight_hash_is_frozen_not_placeholder() -> None:
    assert len(r221.EXPECTED_PREFLIGHT_SHA256) == 64
    assert "TO_BE_FROZEN" not in r221.EXPECTED_PREFLIGHT_SHA256
    assert len(r221.EXPECTED_PYTHON_SHA256) == 64
    assert r221.host_identity() == r221.EXPECTED_HOST_IDENTITY


def test_single_authorized_short_timeout_redesign_is_exact() -> None:
    assert r221.SHORT_S11_SECONDS == 900.0
    assert r221.SHORT_WORKER_SECONDS == 1200.0
    assert r221.LONG_S11_SECONDS == 1200.0
    assert r221.LONG_WORKER_SECONDS == 2100.0
    assert r221.SHORT_S11_SECONDS < r221.SHORT_WORKER_SECONDS


def test_closed_child_records_and_enforces_post_exit_disk_use(
    tmp_path: Path,
) -> None:
    output = tmp_path / "child.bin"
    result = r221.run_bounded_closed(
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
    request.write_bytes(r221._canonical_json_bytes({"fixture": True}))
    config = {"application": "music"}
    attempts = [
        dict(_attempt(bytes_, 100 + attempt, attempt), config=config)
        for attempt, bytes_ in enumerate((100, 200, 200, 200))
    ]
    receipt = {
        "schema": r221.RECEIPT_SCHEMA,
        "status": "PASS",
        "comparison_status": "STRICT_MATCH",
        "rate_attempt_count": 4,
        "run_identity": "run",
        "item_id": "fixture",
        "work_request_sha256": r216.sha256_file(request),
        "work_request_bytes": request.stat().st_size,
        "manifest_item_sha256": r221._canonical_sha256(item),
        "opus": {
            "configuration": config,
            "target_complete_bytes": 100,
            "strict_tolerance_bytes": 64,
            "attempt_count": 4,
            "attempts": attempts,
            "comparison_status": "STRICT_MATCH",
            "signed_complete_byte_delta": 0,
            "signed_rate_delta_percent": 0.0,
            "selected": {
                "bytes": 100, "byte_delta": 0,
                "q5": 100, "attempt": 0, "selection_position": 0,
                "raw_sha256": attempts[0]["raw_sha256"],
                "normalized_sha256": attempts[0]["normalized_sha256"],
                "comparison_status": "STRICT_MATCH",
                "rate_delta_percent": 0.0,
            },
        },
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
    assert r221._verify_receipt(tmp_path, "run", item, authority) == receipt
    receipt["status"] = "PASS"
    receipt["extra_mutation"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    try:
        r221._verify_receipt(tmp_path, "run", item, authority)
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
    loaded, decoded = r221._load_and_verify_s11(tmp_path, 48_000, samples.shape)
    assert loaded == report
    assert np.array_equal(decoded, samples)
    report["complete_bytes"] += 1
    (tmp_path / "s11-report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="report/stream identity mismatch"):
        r221._load_and_verify_s11(tmp_path, 48_000, samples.shape)


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
        "worker_identities": r221._worker_identity_snapshot(
            source, core, opusenc, opusdec
        ),
        "dependency_versions": r221.dependency_versions(),
    }
    r221._verify_worker_identities(request, source, core, opusenc, opusdec)
    source.write_bytes(b"mutated")
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r221._verify_worker_identities(request, source, core, opusenc, opusdec)


def test_worker_identity_rejects_missing_and_wrong_analyzer(tmp_path: Path) -> None:
    paths = []
    for name in ("source.wav", "core.dll", "opusenc.exe", "opusdec.exe"):
        path = tmp_path / name
        path.write_bytes(name.encode("ascii"))
        paths.append(path)
    identities = r221._worker_identity_snapshot(*paths)
    request = {
        "worker_identities": dict(identities),
        "dependency_versions": r221.dependency_versions(),
    }
    request["worker_identities"].pop("analyzer")
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r221._verify_worker_identities(request, *paths)
    request["worker_identities"] = dict(identities, analyzer="0" * 64)
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r221._verify_worker_identities(request, *paths)


def test_closed_child_rejects_post_exit_disk_breach(tmp_path: Path) -> None:
    output = tmp_path / "oversized.bin"
    with pytest.raises(OSError, match="staging exceeded"):
        r221.run_bounded_closed(
            [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'x'*2048)", str(output)],
            20.0, 256 * 1024 * 1024, tmp_path, 1024,
        )


def test_closed_child_enforces_passed_short_rss_limit(
    tmp_path: Path,
) -> None:
    with pytest.raises(MemoryError, match="child RSS exceeded"):
        r221.run_bounded_closed(
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

    monkeypatch.setattr(r221, "run_bounded_closed", fake_run)
    monkeypatch.setattr(r221, "compute_metrics", fake_metrics)
    config = r221.fixed_opus_config(["music"])
    point = {
        "config": r216.asdict(config), "q5": 1_000_000, "attempt": 0,
        "bytes": len(encoded_payload), "byte_delta": 0,
        "raw_sha256": hashlib.sha256(encoded_payload).hexdigest(),
    }
    result = r221._decode_selected(
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
    assert r221.EXPECTED_SOURCE_REVISION == "1c45376eebe7daa49904acae885c47d6d571cf87"
    assert r221.EXPECTED_ANALYZER_SHA256 == r216.sha256_file(
        r221.REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py"
    )
    local = []
    for name in ("source.wav", "core.dll", "opusenc.exe", "opusdec.exe"):
        path = tmp_path / name
        path.write_bytes(name.encode("ascii"))
        local.append(path)
    snapshot = r221._worker_identity_snapshot(*local)
    assert snapshot["analyzer"] == r221.EXPECTED_ANALYZER_SHA256


def test_worker_rejects_mutated_request_before_parsing(tmp_path: Path) -> None:
    original = r221._canonical_json_bytes({"schema": r221.WORK_SCHEMA, "item": {"id": "x"}})
    path = tmp_path / "work-request.json"
    path.write_bytes(original.replace(b'"x"', b'"y"'))
    with pytest.raises(RuntimeError, match="work-request seal mismatch"):
        r221._run_worker(path, hashlib.sha256(original).hexdigest())


def test_base_and_per_item_authority_digests_have_unambiguous_membership(
    tmp_path: Path,
) -> None:
    base = tmp_path / "base.bin"
    source = tmp_path / "source.wav"
    base.write_bytes(b"base")
    source.write_bytes(b"source-a")
    base_rows = [r221.Authority(base, r216.sha256_file(base), tmp_path)]
    first = base_rows + [r221.Authority(source, r216.sha256_file(source), tmp_path)]
    assert r221._authority_digest(base_rows) != r221._authority_digest(first)
    source.write_bytes(b"source-b")
    second = base_rows + [r221.Authority(source, r216.sha256_file(source), tmp_path)]
    assert r221._authority_digest(first) != r221._authority_digest(second)


@pytest.mark.skipif(sys.platform != "win32", reason="R-221 lock contract is Windows-only")
def test_under_lock_hash_rejects_mutation_before_file_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority_path = tmp_path / "authority.bin"
    authority_path.write_bytes(b"frozen")
    authority = r221.Authority(authority_path, r216.sha256_file(authority_path), tmp_path)
    original_open = r221._open_deny_write_delete
    mutated = {"done": False}

    def mutate_before_file_lock(path: Path, directory: bool) -> int:
        if not directory and Path(path).resolve() == authority_path.resolve() and not mutated["done"]:
            authority_path.write_bytes(b"changed")
            mutated["done"] = True
        return original_open(path, directory)

    monkeypatch.setattr(r221, "_open_deny_write_delete", mutate_before_file_lock)
    with pytest.raises(RuntimeError, match="under-lock authority mismatch"):
        with r221._locked_authorities([authority]):
            pass
    assert mutated["done"]


@pytest.mark.skipif(sys.platform != "win32", reason="R-221 lock contract is Windows-only")
def test_file_and_ancestor_locks_deny_cross_process_mutation_until_release(
    tmp_path: Path,
) -> None:
    root = tmp_path / "authority-root"
    root.mkdir()
    target = root / "authority.bin"
    target.write_bytes(b"frozen")
    replacement = root / "replacement.bin"
    replacement.write_bytes(b"replacement")
    authority = r221.Authority(target, r216.sha256_file(target), root)
    mutation = (
        "from pathlib import Path; import os,sys; "
        "p=Path(sys.argv[1]); mode=sys.argv[2]; "
        "(p.write_bytes(b'changed') if mode=='write' else os.replace(p, Path(str(p)+'.moved')))"
    )
    with r221._locked_authorities([authority]):
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
        r221._validate_resume_index(
            {
                "schema": "resonith-r217-s12-fixed-opus-run-index-1",
                "run_identity": "run",
                "run_material_sha256": r221._canonical_sha256(material),
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
        r221._verify_receipt(tmp_path, "run", {"id": "x"})
    old_work = r221._canonical_json_bytes({
        "schema": "resonith-r217-s12-fixed-opus-work-request-1"
    })
    request.write_bytes(old_work)
    with pytest.raises(RuntimeError, match="invalid R-221 work-request schema"):
        r221._run_worker(request, hashlib.sha256(old_work).hexdigest())
    with pytest.raises(RuntimeError, match="invalid R-221 runner material schema"):
        r221._validate_runner_material({
            "schema": "resonith-r217-s12-fixed-opus-runner-1"
        })


def test_resume_index_requires_unique_manifest_order_prefix_and_exact_key_sets() -> None:
    material = {"schema": r221.RUNNER_SCHEMA}
    ids = ["a", "b", "c"]
    base = {
        "schema": r221.RUN_SCHEMA,
        "run_identity": "run",
        "run_material_sha256": r221._canonical_sha256(material),
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
            r221._validate_resume_index(
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
        r221._validate_resume_index(
            valid, "run", material, "base", {name: name for name in ids},
            {name: f"m-{name}" for name in ids}, ids,
        )


def test_actual_r217_tree_cannot_resume_as_r221() -> None:
    root = r221.REPOSITORY / "artifacts/r217-s12-fixed-opus-direct-v2"
    assert (root / "run-index.json").is_file()
    material = {"schema": r221.RUNNER_SCHEMA}
    with pytest.raises(RuntimeError, match="different or stale run"):
        r221._load_resume_index(
            root, "run", material, "base", {"x": "item"},
            {"x": "manifest"}, ["x"],
        )
    with pytest.raises(RuntimeError, match="requires a nonexistent output root"):
        r221._create_fresh_root(root)


def test_r221_exposes_only_direct_two_codec_comparison() -> None:
    source = Path(r221.__file__).read_text(encoding="utf-8")
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
    request_bytes = r221._canonical_json_bytes({"schema": r221.WORK_SCHEMA})
    request = final / "work-request.json"
    request.write_bytes(request_bytes)
    metric = {
        "waveform": {"snr_db": 1.0},
        "spectral": {
            "log_mel_rmse": 2.0,
            "magnitude_cosine_similarity": 0.5,
        },
    }
    config = {"application": "music"}
    attempts = [
        dict(_attempt(101 + attempt, 100 + attempt, attempt), config=config)
        for attempt in range(4)
    ]
    receipt = {
        "schema": r221.RECEIPT_SCHEMA,
        "status": "PASS",
        "comparison_status": "UNMATCHED_NEAREST",
        "rate_attempt_count": 4,
        "run_identity": "run",
        "item_id": "fixture",
        "work_request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "work_request_bytes": len(request_bytes),
        "manifest_item_sha256": r221._canonical_sha256(item),
        "base_authority_set_sha256": "base",
        "item_authority_set_sha256": "item",
        "retained_files": [{
            "path": "work-request.json", "bytes": len(request_bytes),
            "sha256": hashlib.sha256(request_bytes).hexdigest(),
        }],
        "resonith": {"complete_bytes": 100, "metrics": metric},
        "opus": {
            "configuration": config,
            "target_complete_bytes": 100,
            "strict_tolerance_bytes": 0,
            "attempt_count": 4,
            "attempts": attempts,
            "comparison_status": "UNMATCHED_NEAREST",
            "signed_complete_byte_delta": 1,
            "signed_rate_delta_percent": 1.0,
            "selected": {
                "bytes": 101, "byte_delta": 1, "metrics": metric,
                "q5": 100, "attempt": 0, "selection_position": 0,
                "raw_sha256": attempts[0]["raw_sha256"],
                "normalized_sha256": attempts[0]["normalized_sha256"],
                "comparison_status": "UNMATCHED_NEAREST",
                "rate_delta_percent": 1.0,
            },
        },
    }
    r216.write_json_fsynced(final / "receipt.json", receipt)
    receipt_hash = r216.sha256_file(final / "receipt.json")
    r221._aggregate(
        tmp_path, {"items": [item]}, "run", {"schema": r221.RUNNER_SCHEMA},
        {"fixture": receipt_hash}, {"fixture": request_bytes},
        "base", {"fixture": "item"},
    )
    aggregate = json.loads((tmp_path / "aggregate.json").read_text(encoding="utf-8"))
    assert set(aggregate["rows"][0]) == {
        "id", "application", "comparison_status", "attempt_count", "resonith_bytes",
        "opus_bytes", "byte_delta", "rate_delta_percent",
        "resonith_snr_db", "opus_snr_db", "resonith_log_mel_rmse",
        "opus_log_mel_rmse", "resonith_magnitude_cosine",
        "opus_magnitude_cosine",
    }
    assert aggregate["comparison_status"] == "CONTAINS_RATE_MISMATCH"
    assert aggregate["strict_match_count"] == 0
    assert aggregate["unmatched_count"] == 1
    assert aggregate["equal_rate_item_ids"] == []
    assert aggregate["equal_rate_excluded_item_ids"] == ["fixture"]
    report = (tmp_path / "REPORT.md").read_text(encoding="utf-8")
    assert "| Item | App | Rate status | Attempts | Resonith bytes | Opus bytes |" in report
    assert "excluded from every equal-rate statistic" in report
    assert "Previous Resonith" not in report
