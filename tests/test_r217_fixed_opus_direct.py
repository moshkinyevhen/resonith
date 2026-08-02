from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pytest

from experiments import r216_s12_opus_comparison as r216
from experiments import r217_s12_fixed_opus_direct as r217


def _attempt(bytes_: int, q5: int, attempt: int, quality: float = 0.0) -> dict:
    return {
        "bytes": bytes_,
        "q5": q5,
        "attempt": attempt,
        "raw_sha256": f"{attempt:064x}",
        "metrics": {"forbidden_selection_input": quality},
    }


def test_application_rule_uses_only_exact_registered_speech_token() -> None:
    assert r217.fixed_opus_config(["speech", "short"]).application == "speech"
    assert r217.fixed_opus_config(["music", "speech-like"]).application == "music"
    assert r217.fixed_opus_config(["Speech"]).application == "music"


def test_fixed_anchor_closes_all_material_configuration_coordinates() -> None:
    config = r217.fixed_opus_config(["music", "stereo"])
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
    selected = r217.select_byte_match(attempts, 10_000)
    assert selected is not None
    assert selected["attempt"] == 2
    assert selected["byte_delta"] == -1


def test_byte_selection_final_tie_uses_attempt_index() -> None:
    selected = r217.select_byte_match(
        [_attempt(10_001, 1_000_000, 3), _attempt(10_001, 1_000_000, 1)],
        10_000,
    )
    assert selected is not None
    assert selected["attempt"] == 1


def test_unmatched_anchor_returns_none() -> None:
    # At 10,000 bytes the frozen tolerance is 64 bytes.
    assert r217.select_byte_match(
        [_attempt(9_935, 1_000_000, 0), _attempt(10_065, 1_000_001, 1)],
        10_000,
    ) is None


def test_complete_opus_argv_has_frozen_container_and_no_hidden_controls(
    tmp_path: Path,
) -> None:
    config = r217.fixed_opus_config(["speech"])
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
    assert r217.RUN_SCHEMA != r216.RUN_SCHEMA
    assert r217.RECEIPT_SCHEMA != r216.RECEIPT_SCHEMA
    assert r217.RUNNER_SCHEMA != r216.RUNNER_SCHEMA
    assert r217.WORK_SCHEMA.startswith("resonith-r217-")


def test_preflight_hash_is_frozen_not_placeholder() -> None:
    assert len(r217.EXPECTED_PREFLIGHT_SHA256) == 64
    assert "TO_BE_FROZEN" not in r217.EXPECTED_PREFLIGHT_SHA256
    assert len(r217.EXPECTED_PYTHON_SHA256) == 64


def test_single_authorized_short_timeout_redesign_is_exact() -> None:
    assert r217.SHORT_S11_SECONDS == 900.0
    assert r217.SHORT_WORKER_SECONDS == 1200.0
    assert r217.LONG_S11_SECONDS == 1200.0
    assert r217.LONG_WORKER_SECONDS == 2100.0
    assert r217.SHORT_S11_SECONDS < r217.SHORT_WORKER_SECONDS


def test_closed_child_records_and_enforces_post_exit_disk_use(
    tmp_path: Path,
) -> None:
    output = tmp_path / "child.bin"
    result = r217.run_bounded_closed(
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
    receipt = {
        "schema": r217.RECEIPT_SCHEMA,
        "status": "PASS",
        "run_identity": "run",
        "item_id": "fixture",
        "retained_files": [{
            "path": "anchor.opus", "bytes": 4,
            "sha256": r216.sha256_file(retained),
        }],
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    authority = r216.sha256_file(receipt_path)
    assert r217._verify_receipt(tmp_path, "run", item, authority) == receipt
    receipt["status"] = "PASS"
    receipt["extra_mutation"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    try:
        r217._verify_receipt(tmp_path, "run", item, authority)
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
    loaded, decoded = r217._load_and_verify_s11(tmp_path, 48_000, samples.shape)
    assert loaded == report
    assert np.array_equal(decoded, samples)
    report["complete_bytes"] += 1
    (tmp_path / "s11-report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="report/stream identity mismatch"):
        r217._load_and_verify_s11(tmp_path, 48_000, samples.shape)


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
        "worker_identities": r217._worker_identity_snapshot(
            source, core, opusenc, opusdec
        ),
        "dependency_versions": r217.dependency_versions(),
    }
    r217._verify_worker_identities(request, source, core, opusenc, opusdec)
    source.write_bytes(b"mutated")
    with pytest.raises(RuntimeError, match="worker identity mismatch"):
        r217._verify_worker_identities(request, source, core, opusenc, opusdec)


def test_closed_child_rejects_post_exit_disk_breach(tmp_path: Path) -> None:
    output = tmp_path / "oversized.bin"
    with pytest.raises(OSError, match="staging exceeded"):
        r217.run_bounded_closed(
            [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'x'*2048)", str(output)],
            20.0, 256 * 1024 * 1024, tmp_path, 1024,
        )


def test_closed_child_enforces_passed_short_rss_limit(
    tmp_path: Path,
) -> None:
    with pytest.raises(MemoryError, match="child RSS exceeded"):
        r217.run_bounded_closed(
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

    monkeypatch.setattr(r217, "run_bounded_closed", fake_run)
    monkeypatch.setattr(r217, "compute_metrics", fake_metrics)
    config = r217.fixed_opus_config(["music"])
    point = {
        "config": r216.asdict(config), "q5": 1_000_000, "attempt": 0,
        "bytes": len(encoded_payload), "byte_delta": 0,
        "raw_sha256": hashlib.sha256(encoded_payload).hexdigest(),
    }
    result = r217._decode_selected(
        point, source, tmp_path / "anchor.opus",
        tmp_path / "anchor-decoded.wav", bytes(32), "fixture", 48_000,
        reference.shape, ["music"], Path("opusenc"), Path("opusdec"),
        time.perf_counter() + 10.0, tmp_path / "ledger.jsonl",
        8 * 1024 * 1024, tmp_path, 1024 * 1024,
    )
    assert calls["metrics"] == 1
    assert result["metrics"] == {"single_pass": True}
