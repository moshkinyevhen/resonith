from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pytest

from experiments.r216_s12_metrics import compute_metrics, quality_axes
from experiments import r216_s12_opus_comparison as s12
from reference.maf_p0.opus_anchor import OpusAnchorResult, OpusTools
from reference.maf_p0.opus_max_effort import (
    OpusEffortConfig,
    opus_max_effort_configurations,
    run_opus_max_effort_frontier,
)


def test_configuration_lattice_covers_stereo_controls() -> None:
    configs = opus_max_effort_configurations(2)

    assert len(configs) == 108
    assert {config.mode for config in configs} == {
        "vbr",
        "cvbr",
        "hard-cbr",
    }
    assert {config.frame_size_ms for config in configs} == {
        2.5,
        5.0,
        10.0,
        20.0,
        40.0,
        60.0,
    }
    assert {config.phase_inversion for config in configs} == {True, False}


def test_frontier_selects_best_decoded_quality_at_matched_bytes() -> None:
    samples = np.zeros((48000, 2), dtype=np.int16)
    tools = OpusTools(
        opusenc=None,  # type: ignore[arg-type]
        opusdec=None,  # type: ignore[arg-type]
        encoder_version="libopus 1.6.1",
        decoder_version="libopus 1.6.1",
        encoder_sha256="0" * 64,
        decoder_sha256="1" * 64,
    )

    def fake_anchor(_samples, _rate, **kwargs):
        frame_size = float(kwargs["frame_size_ms"])
        bitrate = float(kwargs["bitrate_kbps"])
        stream_bytes = max(1, int(round(bitrate * 125.0)))
        quality = 30.0 if frame_size == 20.0 else 20.0
        return OpusAnchorResult(
            payload=b"x" * stream_bytes,
            reconstructed=np.zeros_like(samples),
            report={"snr_db": quality},
        )

    frontier = run_opus_max_effort_frontier(
        samples,
        48000,
        target_complete_bytes=12000,
        matched_byte_tolerance=64,
        refinement_rounds=2,
        configurations=(
            OpusEffortConfig("vbr", "auto", 10.0, True),
            OpusEffortConfig("vbr", "auto", 20.0, True),
        ),
        tools=tools,
        anchor_runner=fake_anchor,
    )

    assert frontier.selected.config.frame_size_ms == 20.0
    assert frontier.report["complexity"] == 10
    assert frontier.report["configuration_count"] == 2


def test_r216_exact_q5_serial_and_hierarchical_lattice() -> None:
    stereo = s12.base_configurations(2)
    mono = s12.base_configurations(1)
    assert len(stereo) == 108
    assert len(mono) == 54
    assert len(s12.ctl_configurations(stereo[0], 2)) == 21
    assert len(s12.ctl_configurations(mono[0], 1)) == 10
    assert s12._round_ratio_even(5, 2) == 2
    assert s12._round_ratio_even(7, 2) == 4
    q5 = s12.initial_q5(10_000, 48_000, 480_000, 2)
    assert q5 == 800_000
    serial = s12.serial_for_point(bytes.fromhex("11" * 32), "fixture", stereo[0], q5)
    assert serial == 1_666_260_518
    assert serial == s12.serial_for_point(
        bytes.fromhex("11" * 32), "fixture", stereo[0], q5
    )


def test_r216_analyzer_bound_falls_back_for_full_mozart() -> None:
    assert s12.analyzer_bound(19_237_088, 2) == 28_405_440
    assert s12.analyzer_bound(529_200, 2) < s12.MAXIMUM_OBSERVATIONS


def test_r216_metrics_identity_phase_polarity_channel_and_shape_edges() -> None:
    rate = 48_000
    index = np.arange(rate, dtype=np.float64)
    phase = 2.0 * np.pi * 440.0 * index / rate
    left = np.rint(12_000.0 * np.cos(phase)).astype(np.int16)
    right = np.rint(9_000.0 * np.cos(phase + 0.7)).astype(np.int16)
    source = np.column_stack((left, right))
    identity = compute_metrics(source, source.copy(), rate, ["music"])
    assert identity["waveform"]["rms_error"] == 0.0
    assert identity["phase_channel"]["channels"][0]["phase"]["rmse_radians"] == 0.0
    assert identity["phase_channel"]["stereo"]["interchannel_phase_error"]["rmse_radians"] == 0.0
    assert not any(name.endswith("circular_coherence") for name in quality_axes(identity))
    polarity = compute_metrics(source, -source, rate, ["music"])
    assert polarity["phase_channel"]["channels"][0]["phase"]["rmse_radians"] > 3.0
    swapped = compute_metrics(source, source[:, ::-1].copy(), rate, ["music"])
    assert swapped["phase_channel"]["stereo"]["interchannel_phase_error"]["rmse_radians"] > 1.0
    silence = np.zeros((rate, 2), dtype=np.int16)
    silent = compute_metrics(silence, silence.copy(), rate, ["speech"])
    assert silent["waveform"]["snr_db"] is None
    assert silent["speech"]["stoi"] is None
    with pytest.raises(TypeError, match="equal non-empty"):
        compute_metrics(source, source[:-1], rate, ["music"])


def test_r216_receipt_rejects_payload_and_file_set_drift(tmp_path: Path) -> None:
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"stable")
    receipt = {
        "schema": s12.RECEIPT_SCHEMA, "status": "PASS",
        "run_identity": "run", "item_id": "item",
        "retained_files": [{
            "path": "payload.bin", "bytes": 6,
            "sha256": hashlib.sha256(b"stable").hexdigest(),
        }],
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    assert s12._verify_receipt(tmp_path, "run", {"id": "item"}) == receipt
    payload.write_bytes(b"broken")
    with pytest.raises(RuntimeError, match="drift"):
        s12._verify_receipt(tmp_path, "run", {"id": "item"})
    payload.write_bytes(b"stable")
    (tmp_path / "extra.bin").write_bytes(b"extra")
    with pytest.raises(RuntimeError, match="file set"):
        s12._verify_receipt(tmp_path, "run", {"id": "item"})


def test_r216_atomic_json_replace_and_timeout_hard_stop(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    s12.replace_json_fsynced(path, {"generation": 1})
    s12.replace_json_fsynced(path, {"generation": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"generation": 2}
    with pytest.raises(TimeoutError, match="exceeded"):
        s12.run_bounded(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            0.05, 2 * s12.GIB, tmp_path,
        )
    disk_root = tmp_path / "bounded-disk"
    disk_root.mkdir()
    script = (
        "from pathlib import Path; import time; "
        f"p=Path({str(disk_root / 'growth.bin')!r}); "
        "p.write_bytes(b'x'*1048576); time.sleep(2)"
    )
    with pytest.raises(OSError, match="staging exceeded"):
        s12.run_bounded(
            [sys.executable, "-c", script], 5, 2 * s12.GIB, tmp_path,
            disk_root, 64 * 1024,
        )
    heartbeat = tmp_path / "grandchild-heartbeat.bin"
    grandchild = (
        "from pathlib import Path; import time; "
        f"f=Path({str(heartbeat)!r}).open('ab'); "
        "[(f.write(b'x'),f.flush(),time.sleep(.02)) for _ in range(500)]"
    )
    parent = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{grandchild!r}]); time.sleep(10)"
    )
    with pytest.raises(TimeoutError, match="exceeded"):
        s12.run_bounded([sys.executable, "-c", parent], 0.4, 2 * s12.GIB, tmp_path)
    stopped_size = heartbeat.stat().st_size
    time.sleep(0.25)
    assert heartbeat.stat().st_size == stopped_size


def test_r216_verified_final_can_recover_lost_index_entry(tmp_path: Path) -> None:
    final = tmp_path / "item"
    final.mkdir()
    payload = final / "payload.bin"
    payload.write_bytes(b"stable")
    receipt = {
        "schema": s12.RECEIPT_SCHEMA, "status": "PASS",
        "run_identity": "run", "item_id": "item",
        "worker_resources": {"wall_seconds": 1.0, "cpu_seconds": 0.5,
                             "peak_rss_bytes": 1024},
        "retained_files": [{
            "path": "payload.bin", "bytes": 6,
            "sha256": hashlib.sha256(b"stable").hexdigest(),
        }],
    }
    (final / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    recovered = s12._verify_receipt(final, "run", {"id": "item"})
    index = {"completed_item_ids": [], "worker_resources": {}}
    index["completed_item_ids"].append("item")
    index["worker_resources"]["item"] = recovered["worker_resources"]
    assert index["completed_item_ids"] == ["item"]
    assert index["worker_resources"]["item"]["peak_rss_bytes"] == 1024


def test_r216_manifest_hash_and_order_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = {
        "schema": s12.MANIFEST_SCHEMA, "item_count": 19,
        "items": [
            {"id": f"id-{index}", "order": index + 1,
             "source": {"path": "unknown/file.wav"}}
            for index in range(19)
        ],
    }
    manifest["items"][0]["id"] = "mozart-full"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(s12, "MANIFEST_SHA256", s12.sha256_file(path))
    manifest["items"][1]["order"] = 99
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(s12, "MANIFEST_SHA256", s12.sha256_file(path))
    with pytest.raises(RuntimeError, match="structure/order"):
        s12.load_and_validate_manifest(path, {})
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        s12.load_and_validate_manifest(path, {})


def test_r216_manifest_validates_canonical_source_pcm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root = tmp_path / "root"
    source_root.mkdir()
    source = source_root / "source.wav"
    samples = np.arange(128, dtype=np.int16)[:, None]
    s12.write_pcm16_channels(source, 8_000, samples)
    source_record = {
        "path": "root/source.wav", "file_sha256": s12.sha256_file(source),
        "pcm16_payload_sha256": s12.pcm_sha256(samples),
        "sample_rate": 8_000, "frame_count": 128, "channel_count": 1,
    }
    items = [
        {"id": "mozart-full" if index == 0 else f"item-{index}",
         "order": index + 1, "source": dict(source_record)}
        for index in range(19)
    ]
    manifest = {"schema": s12.MANIFEST_SCHEMA, "item_count": 19, "items": items}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(s12, "MANIFEST_SHA256", s12.sha256_file(path))
    loaded, resolved = s12.load_and_validate_manifest(path, {"root": source_root})
    assert loaded["item_count"] == 19 and len(resolved) == 19
    manifest["items"][3]["source"]["pcm16_payload_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(s12, "MANIFEST_SHA256", s12.sha256_file(path))
    with pytest.raises(RuntimeError, match="source PCM identity"):
        s12.load_and_validate_manifest(path, {"root": source_root})


def test_r216_actual_s11_byte_decode_identity() -> None:
    core = Path("G:/Resonith/build/cpp23-clang22-ninja/libresonith_core_shared.dll")
    if not core.is_file() or s12.sha256_file(core) != s12.EXPECTED_CORE_SHA256:
        pytest.skip("frozen Golden Core is unavailable")
    rate, count = 8_000, 4_096
    phase = 2.0 * np.pi * 440.3 * np.arange(count) / rate
    samples = np.rint(8_000.0 * np.cos(phase)).astype(np.int16)[:, None]
    item = {"challenger": {"half_window": 512, "band_count": 24}}
    payload, decoded, report = s12._encode_s11(samples, rate, 24, item, core)
    assert len(payload) == report["complete_bytes"]
    assert s12.pcm_sha256(decoded) == report["decoded_pcm16le_sha256"]


def test_r216_official_opus_point_is_raw_deterministic(tmp_path: Path) -> None:
    tools = Path("G:/Resonith/artifacts/tools/opus-1.6.1-x64")
    opusenc, opusdec = tools / "opusenc.exe", tools / "opusdec.exe"
    if not opusenc.is_file() or not opusdec.is_file():
        pytest.skip("frozen official Opus tools are unavailable")
    rate = 48_000
    signal = np.rint(
        10_000.0 * np.cos(2.0 * np.pi * 440.0 * np.arange(rate) / rate)
    ).astype(np.int16)[:, None]
    source = tmp_path / "source.wav"
    write_pcm16_channels = s12.write_pcm16_channels
    write_pcm16_channels(source, rate, signal)
    config = s12.OpusConfig("vbr", "music", 20_000, True)
    target = 2_000
    attempts = s12._feedback_search(
        opusenc, source, tmp_path, bytes.fromhex("22" * 32), "opus-test",
        config, target, rate, rate, 1, 120, float("inf"),
        tmp_path / "point-ledger.jsonl",
    )
    point = min(attempts, key=lambda row: abs(row["bytes"] - target))
    point["byte_delta"] = point["bytes"] - target
    measured, encoded = s12._decode_strict_point(
        point, opusenc, opusdec, source, tmp_path, bytes.fromhex("22" * 32),
        "opus-test", rate, signal.shape, ["music"], 120, float("inf"),
        tmp_path / "point-ledger.jsonl",
    )
    assert measured["raw_sha256"] == s12.sha256_file(encoded)
    assert measured["metrics"]["alignment_lag_samples"] == 0
    encoded.unlink()
    ctl = s12.OpusConfig(
        "vbr", "music", 20_000, True, 4004, 1101, 1
    )
    ctl_output = tmp_path / "ctl.opus"
    ctl_record = s12._encode_point(
        opusenc, source, ctl_output, bytes.fromhex("22" * 32),
        "opus-test", ctl, point["q5"], 120,
    )
    assert ctl_record["config"]["bandwidth_request"] == 4004
    assert ctl_record["config"]["force_channels"] == 1
    assert "stdout" not in ctl_record["encode_resources"]
    assert (tmp_path / "point-ledger.jsonl").stat().st_size > 0
