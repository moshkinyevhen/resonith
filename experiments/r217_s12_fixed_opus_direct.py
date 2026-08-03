"""R-217 direct S11-versus-fixed-Opus comparison over the registered corpus."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid

import numpy as np

from experiments import r216_s12_opus_comparison as r216
from experiments.r216_s12_metrics import compute_metrics


REPOSITORY = Path(__file__).resolve().parents[1]
MANIFEST_SHA256 = r216.MANIFEST_SHA256
MANIFEST_SCHEMA = r216.MANIFEST_SCHEMA
RUN_SCHEMA = "resonith-r217-s12-fixed-opus-run-index-1"
RECEIPT_SCHEMA = "resonith-r217-s12-fixed-opus-item-receipt-1"
RUNNER_SCHEMA = "resonith-r217-s12-fixed-opus-runner-1"
WORK_SCHEMA = "resonith-r217-s12-fixed-opus-work-request-1"
GIB = 1024**3
SHORT_S11_SECONDS = 900.0
SHORT_WORKER_SECONDS = 1200.0
LONG_S11_SECONDS = 1200.0
LONG_WORKER_SECONDS = 2100.0

EXPECTED_SOURCE_REVISION = r216.EXPECTED_SOURCE_REVISION
EXPECTED_R216_SHA256 = "316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3"
EXPECTED_HELPER_SHA256 = r216.EXPECTED_HELPER_SHA256
EXPECTED_PREFLIGHT_SHA256 = "f9e2eb5349c7ed808f35f2e8c459caa7eca9ca4264c4673022c0a4f3b56b655b"
EXPECTED_CORE_SHA256 = r216.EXPECTED_CORE_SHA256
EXPECTED_OPUSENC_SHA256 = r216.EXPECTED_OPUSENC_SHA256
EXPECTED_OPUSDEC_SHA256 = r216.EXPECTED_OPUSDEC_SHA256
EXPECTED_PYTHON_SHA256 = "03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38"


def dependency_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": metadata.version("scipy"),
        "pystoi": metadata.version("pystoi"),
    }


def run_bounded_closed(
    command: list[str], timeout: float, rss_limit: int, disk_root: Path,
    disk_limit: int,
) -> dict[str, object]:
    """Run one child with pre/during/post disk closure and recorded bounds."""
    before = r216._tree_bytes(disk_root)
    if before > disk_limit:
        raise OSError(f"staging already exceeds {disk_limit} bytes")
    result = r216.run_bounded(
        command, timeout, rss_limit, REPOSITORY, disk_root, disk_limit
    )
    after = r216._tree_bytes(disk_root)
    if after > disk_limit:
        raise OSError(f"staging exceeded {disk_limit} bytes after child exit")
    return {
        **result,
        "rss_limit_bytes": rss_limit,
        "disk_limit_bytes": disk_limit,
        "disk_bytes_before": before,
        "disk_bytes_after": after,
    }


def _encode_point_closed(
    opusenc: Path, source: Path, output: Path, manifest_digest: bytes,
    item_id: str, config: r216.OpusConfig, q5: int, timeout: float,
    rss_limit: int, disk_root: Path, disk_limit: int,
) -> dict[str, object]:
    serial = r216.serial_for_point(manifest_digest, item_id, config, q5)
    resources = run_bounded_closed(
        r216._opus_command(opusenc, source, output, config, q5, serial),
        timeout, rss_limit, disk_root, disk_limit,
    )
    normalized_hash, pages = r216.normalized_ogg_sha256(output)
    return {
        "config": asdict(config), "q5": q5, "serial": serial,
        "argv": r216._opus_command(
            opusenc, source, output, config, q5, serial
        )[1:-2] + ["<source>", "<output>"],
        "bytes": output.stat().st_size,
        "raw_sha256": r216.sha256_file(output),
        "normalized_sha256": normalized_hash,
        "ogg_pages": pages,
        "encode_resources": resources,
    }


def _feedback_search_closed(
    opusenc: Path, source: Path, temporary: Path, manifest_digest: bytes,
    item_id: str, config: r216.OpusConfig, target: int, rate: int,
    frames: int, channels: int, timeout: float, deadline: float,
    ledger: Path, rss_limit: int, disk_root: Path, disk_limit: int,
) -> list[dict[str, object]]:
    q5 = r216.initial_q5(target, rate, frames, channels)
    records = []
    for attempt in range(4):
        output = temporary / f"feedback-{uuid.uuid4().hex}.opus"
        remaining = min(timeout, deadline - time.perf_counter())
        if remaining <= 0:
            raise TimeoutError("fixed Opus item wall ceiling exceeded")
        record = _encode_point_closed(
            opusenc, source, output, manifest_digest, item_id, config, q5,
            remaining, rss_limit, disk_root, disk_limit,
        )
        record["attempt"] = attempt
        r216.append_jsonl_fsynced(
            ledger, {"record_kind": "feedback", **record}
        )
        output.unlink()
        records.append(record)
        q5 = r216.feedback_q5(q5, target, int(record["bytes"]), channels)
    return records


def fixed_opus_config(categories: list[str]) -> r216.OpusConfig:
    """Return the sole R-217 anchor; only exact registered `speech` is special."""
    application = "speech" if "speech" in categories else "music"
    return r216.OpusConfig("vbr", application, 20_000, True)


def select_byte_match(
    attempts: list[dict[str, object]], target: int
) -> dict[str, object] | None:
    """Select one strict point without consulting any decoded-quality field."""
    tolerance = max(64, target // 1000)
    eligible = []
    for position, attempt in enumerate(attempts):
        delta = int(attempt["bytes"]) - target
        if abs(delta) <= tolerance:
            candidate = dict(attempt)
            candidate["byte_delta"] = delta
            candidate["selection_position"] = position
            eligible.append(candidate)
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda row: (
            abs(int(row["byte_delta"])),
            int(row["bytes"]),
            int(row["q5"]),
            int(row["attempt"]),
        ),
    )


def _worker_identity_snapshot(
    source: Path, core: Path, opusenc: Path, opusdec: Path,
) -> dict[str, str]:
    return {
        "runner": r216.sha256_file(Path(__file__).resolve()),
        "r216_import": r216.sha256_file(Path(r216.__file__).resolve()),
        "metric_helper": r216.sha256_file(
            REPOSITORY / "experiments/r216_s12_metrics.py"
        ),
        "python_executable": r216.sha256_file(Path(sys.executable).resolve()),
        "source_file": r216.sha256_file(source),
        "native_core": r216.sha256_file(core),
        "opusenc": r216.sha256_file(opusenc),
        "opusdec": r216.sha256_file(opusdec),
    }


def _verify_worker_identities(
    request: dict[str, object], source: Path, core: Path,
    opusenc: Path, opusdec: Path,
) -> dict[str, str]:
    actual = _worker_identity_snapshot(source, core, opusenc, opusdec)
    if actual != request.get("worker_identities"):
        raise RuntimeError("R-217 worker identity mismatch")
    if dependency_versions() != request.get("dependency_versions"):
        raise RuntimeError("R-217 worker dependency-version mismatch")
    return actual


def _load_and_verify_s11(
    s11_root: Path, expected_rate: int, expected_shape: tuple[int, int],
) -> tuple[dict[str, object], np.ndarray]:
    report_path = s11_root / "s11-report.json"
    stream_path = s11_root / "challenger.resonith"
    decoded_path = s11_root / "challenger-decoded.wav"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        stream_path.stat().st_size != int(report["complete_bytes"])
        or r216.sha256_file(stream_path) != report["payload_sha256"]
    ):
        raise RuntimeError("R-217 S11 report/stream identity mismatch")
    decoded_rate, decoded = r216.read_pcm16_channels(decoded_path)
    if decoded_rate != expected_rate or decoded.shape != expected_shape:
        raise RuntimeError("R-217 S11 actual decode shape/rate mismatch")
    if report["decoded_pcm16le_sha256"] != r216.pcm_sha256(decoded):
        raise RuntimeError("R-217 S11 report/decode identity mismatch")
    return report, decoded


def _decode_selected(
    point: dict[str, object], source: Path, destination_ogg: Path,
    destination_wav: Path, manifest_digest: bytes, item_id: str, rate: int,
    expected_shape: tuple[int, int], categories: list[str], opusenc: Path,
    opusdec: Path, deadline: float, ledger: Path, rss_limit: int,
    disk_root: Path, disk_limit: int,
) -> dict[str, object]:
    """Reproduce, retain, decode, and measure exactly the preselected point."""
    config = r216.OpusConfig(**point["config"])
    q5 = int(point["q5"])
    serial = r216.serial_for_point(manifest_digest, item_id, config, q5)
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise TimeoutError("fixed Opus item wall ceiling exceeded")
    encode_resources = run_bounded_closed(
        r216._opus_command(opusenc, source, destination_ogg, config, q5, serial),
        remaining, rss_limit, disk_root, disk_limit,
    )
    if r216.sha256_file(destination_ogg) != point["raw_sha256"]:
        raise RuntimeError("fixed Opus retained-byte determinism failure")
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise TimeoutError("fixed Opus item wall ceiling exceeded")
    decode_resources = run_bounded_closed(
        [str(opusdec), "--quiet", "--rate", str(rate),
         str(destination_ogg), str(destination_wav)],
        remaining, rss_limit, disk_root, disk_limit,
    )
    decoded_rate, decoded = r216.read_pcm16_channels(destination_wav)
    source_rate, reference = r216.read_pcm16_channels(source)
    if (
        decoded_rate != rate
        or source_rate != rate
        or decoded.shape != expected_shape
        or reference.shape != expected_shape
    ):
        raise RuntimeError("fixed Opus decoder PCM shape/rate mismatch")
    if time.perf_counter() > deadline:
        raise TimeoutError("fixed Opus item wall ceiling exceeded before metrics")
    metrics = compute_metrics(reference, decoded, rate, categories)
    if time.perf_counter() > deadline:
        raise TimeoutError("fixed Opus metrics exceeded item wall ceiling")
    record = dict(point)
    record.update({
        "metrics": metrics,
        "repeat_encode_resources": encode_resources,
        "decode_resources": decode_resources,
        "decoded_pcm16le_sha256": r216.pcm_sha256(decoded),
        "retained_ogg": destination_ogg.name,
        "retained_wav": destination_wav.name,
    })
    r216.append_jsonl_fsynced(
        ledger, {"record_kind": "selected-strict-measurement", **record}
    )
    with destination_ogg.open("r+b") as output:
        os.fsync(output.fileno())
    with destination_wav.open("r+b") as output:
        os.fsync(output.fileno())
    return record


def _run_worker(request_path: Path) -> int:
    started_wall = time.perf_counter()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != WORK_SCHEMA:
        raise RuntimeError("invalid R-217 work-request schema")
    staging = request_path.parent
    item = request["item"]
    source = Path(request["source_path"])
    core = Path(request["native_core"])
    opusenc = Path(request["opusenc"])
    opusdec = Path(request["opusdec"])
    initial_identities = _verify_worker_identities(
        request, source, core, opusenc, opusdec
    )
    rate, samples = r216.read_pcm16_channels(source)
    if (
        rate != item["source"]["sample_rate"]
        or list(samples.shape)
        != [item["source"]["frame_count"], item["source"]["channel_count"]]
        or r216.pcm_sha256(samples) != item["source"]["pcm16_payload_sha256"]
    ):
        raise RuntimeError("R-217 worker source identity mismatch")

    s11_root = staging / "resonith"
    opus_root = staging / "opus"
    temporary = staging / "temporary"
    s11_root.mkdir()
    opus_root.mkdir()
    temporary.mkdir()
    s11_request = temporary / "s11-request.json"
    r216.write_json_fsynced(s11_request, {
        "source_path": str(source),
        "budget": int(item["challenger"]["coefficients_per_frame"]),
        "item": item,
        "native_core": str(core),
        "output": str(s11_root),
    })
    duration = float(item["source"]["duration_seconds"])
    long_item = item["id"] == "mozart-full"
    rss_limit = 12 * GIB if long_item else 8 * GIB
    disk_limit = 8 * GIB if long_item else 2 * GIB
    s11_resources = run_bounded_closed(
        [sys.executable, str(Path(r216.__file__).resolve()),
         "--s11-request", str(s11_request)],
        LONG_S11_SECONDS if long_item else SHORT_S11_SECONDS,
        rss_limit, staging, disk_limit,
    )
    s11_request.unlink()
    s11, s11_decoded = _load_and_verify_s11(
        s11_root, rate, samples.shape
    )
    s11["process_resources"] = s11_resources
    s11["metrics"] = compute_metrics(samples, s11_decoded, rate, list(item["categories"]))

    target = int(s11["complete_bytes"])
    tolerance = max(64, target // 1000)
    config = fixed_opus_config(list(item["categories"]))
    ledger = opus_root / "point-ledger.jsonl"
    opus_deadline = time.perf_counter() + (15 * 60 if item["id"] == "mozart-full" else max(120.0, 20.0 * duration))
    attempts = _feedback_search_closed(
        opusenc, source, temporary, bytes.fromhex(request["manifest_sha256"]),
        item["id"], config, target, rate, samples.shape[0], samples.shape[1],
        max(120.0, 2.0 * duration + 30.0), opus_deadline, ledger,
        rss_limit, staging, disk_limit,
    )
    selected = select_byte_match(attempts, target)
    if selected is None:
        failure = {
            "schema": RECEIPT_SCHEMA,
            "status": "UNMATCHED",
            "run_identity": request["run_identity"],
            "item_id": item["id"],
            "target_complete_bytes": target,
            "strict_tolerance_bytes": tolerance,
            "configuration": asdict(config),
            "attempts": attempts,
        }
        r216.write_json_fsynced(staging / "receipt.json", failure)
        return 3
    opus = _decode_selected(
        selected, source, opus_root / "anchor.opus", opus_root / "anchor-decoded.wav",
        bytes.fromhex(request["manifest_sha256"]), item["id"], rate,
        samples.shape, list(item["categories"]), opusenc, opusdec,
        opus_deadline, ledger, rss_limit, staging, disk_limit,
    )
    shutil.rmtree(temporary)
    final_identities = _verify_worker_identities(
        request, source, core, opusenc, opusdec
    )
    if final_identities != initial_identities:
        raise RuntimeError("R-217 worker identity changed during execution")
    final_rate, final_source = r216.read_pcm16_channels(source)
    if (
        final_rate != rate
        or final_source.shape != samples.shape
        or r216.pcm_sha256(final_source)
        != item["source"]["pcm16_payload_sha256"]
    ):
        raise RuntimeError("R-217 source PCM changed during execution")
    if r216._tree_bytes(staging) > disk_limit:
        raise RuntimeError("R-217 staging exceeded final disk ceiling")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "PASS",
        "run_identity": request["run_identity"],
        "item_id": item["id"],
        "order": item["order"],
        "source_logical_path": item["source"]["path"],
        "source_file_sha256": r216.sha256_file(source),
        "source_pcm16_payload_sha256": r216.pcm_sha256(samples),
        "sample_rate": rate,
        "frames": samples.shape[0],
        "channels": samples.shape[1],
        "categories": list(item["categories"]),
        "initial_worker_identities": initial_identities,
        "final_worker_identities": final_identities,
        "dependency_versions": dependency_versions(),
        "resonith": s11,
        "opus": {
            "anchor_name": "fixed official Opus 1.6.1 direct anchor, maximum complexity",
            "configuration": asdict(config),
            "target_complete_bytes": target,
            "strict_tolerance_bytes": tolerance,
            "selection_order": ["absolute_byte_delta", "complete_bytes", "q5", "attempt"],
            "attempts": attempts,
            "selected": opus,
        },
        "worker_self_wall_seconds": time.perf_counter() - started_wall,
        "retained_files": r216._retained_manifest(staging),
    }
    r216.write_json_fsynced(staging / "receipt.json", receipt)
    return 0


def _identity_files(arguments: argparse.Namespace) -> dict[str, Path]:
    return {
        "runner": Path(__file__).resolve(),
        "r216_import": Path(r216.__file__).resolve(),
        "metric_helper": REPOSITORY / "experiments/r216_s12_metrics.py",
        "preflight": REPOSITORY / "docs/reviews/R217_S12_FIXED_OPUS_DIRECT_PREFLIGHT_2026-08-02.md",
        "predictor": REPOSITORY / "reference/maf_p0/persistent_partial_field.py",
        "native_core": arguments.native_core,
        "opusenc": arguments.opusenc,
        "opusdec": arguments.opusdec,
        "python_executable": Path(sys.executable).resolve(),
        "r117_complete_report": arguments.r117_complete_report,
        "r117_r111_report": arguments.r117_r111_report,
        "prepared_manifest": arguments.prepared_root / "prepared-manifest.json",
        "real_music_corpus": REPOSITORY / "experiments/real_music_corpus.json",
    }


def _validate_identities(
    arguments: argparse.Namespace, files: dict[str, Path]
) -> dict[str, str]:
    expected = {
        "runner": arguments.audited_runner_sha256,
        "r216_import": EXPECTED_R216_SHA256,
        "metric_helper": EXPECTED_HELPER_SHA256,
        "preflight": EXPECTED_PREFLIGHT_SHA256,
        "predictor": r216.EXPECTED_PREDICTOR_SHA256,
        "native_core": EXPECTED_CORE_SHA256,
        "opusenc": EXPECTED_OPUSENC_SHA256,
        "opusdec": EXPECTED_OPUSDEC_SHA256,
        "python_executable": EXPECTED_PYTHON_SHA256,
        "r117_complete_report": "cc906ac76c0bbd8acb3d4303818071c608e187eb0d152e075dd0986acfd98665",
        "r117_r111_report": "51709d0e18184f9d86b9397e8e282e1315ca6aa50304c3d86dffa719ca492fe8",
        "prepared_manifest": "2af905648ec33b092d172fb8868abcdb4f09db91615a9e675cacd4ddc54930f3",
        "real_music_corpus": "6eb7e6e6e330cf7d3890688ab5d67a0180c8be0403589e44dfe221b118f1ab9b",
    }
    hashes = {name: r216.sha256_file(path.resolve()) for name, path in files.items()}
    for name, digest in expected.items():
        if hashes.get(name) != digest:
            raise RuntimeError(f"frozen R-217 identity mismatch: {name}")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if revision != EXPECTED_SOURCE_REVISION:
        raise RuntimeError("frozen source revision mismatch")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--",
         "reference/maf_p0", "experiments/objective_audio_metrics.py"],
        cwd=REPOSITORY, capture_output=True, text=True,
    )
    if dirty.returncode or dirty.stdout:
        raise RuntimeError("dirty imported tracked implementation")
    encoder_version = subprocess.run(
        [str(arguments.opusenc), "--version"], check=True,
        capture_output=True, text=True, timeout=15,
    )
    decoder_version = subprocess.run(
        [str(arguments.opusdec), "--version"], check=True,
        capture_output=True, text=True, timeout=15,
    )
    if "libopus 1.6.1" not in encoder_version.stdout + encoder_version.stderr:
        raise RuntimeError("unexpected opusenc version")
    if "libopus 1.6.1" not in decoder_version.stdout + decoder_version.stderr:
        raise RuntimeError("unexpected opusdec version")
    versions = dependency_versions()
    if versions != {
        "python": "3.14.6", "numpy": "2.5.1",
        "scipy": "1.18.0", "pystoi": "0.4.1",
    }:
        raise RuntimeError(f"frozen dependency version mismatch: {versions}")
    return hashes


def _verify_receipt(
    final: Path, run_identity: str, item: dict,
    expected_receipt_sha256: str | None = None,
) -> dict:
    receipt_path = final / "receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("final R-217 item has no receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("schema") != RECEIPT_SCHEMA
        or receipt.get("status") != "PASS"
        or receipt.get("run_identity") != run_identity
        or receipt.get("item_id") != item["id"]
    ):
        raise RuntimeError("stale, unmatched, or corrupt R-217 receipt")
    receipt_sha256 = r216.sha256_file(receipt_path)
    if (
        expected_receipt_sha256 is not None
        and receipt_sha256 != expected_receipt_sha256
    ):
        raise RuntimeError("R-217 receipt authority hash drift")
    expected = {row["path"]: row for row in receipt["retained_files"]}
    actual = {
        path.relative_to(final).as_posix(): path
        for path in final.rglob("*")
        if path.is_file() and path.name not in {"receipt.json", "work-request.json"}
    }
    if set(expected) != set(actual):
        raise RuntimeError("R-217 retained evidence file-set drift")
    for name, row in expected.items():
        path = actual[name]
        if path.stat().st_size != row["bytes"] or r216.sha256_file(path) != row["sha256"]:
            raise RuntimeError("R-217 retained evidence drift")
    return receipt


def _aggregate(
    root: Path, manifest: dict, run_identity: str, material: dict,
    receipt_hashes: dict[str, str],
) -> None:
    receipts = [
        _verify_receipt(
            root / item["id"], run_identity, item,
            receipt_hashes.get(item["id"]),
        )
        for item in manifest["items"]
    ]
    rows = []
    for receipt in receipts:
        rm = receipt["resonith"]["metrics"]
        om = receipt["opus"]["selected"]["metrics"]
        rows.append({
            "id": receipt["item_id"],
            "application": receipt["opus"]["configuration"]["application"],
            "resonith_bytes": receipt["resonith"]["complete_bytes"],
            "opus_bytes": receipt["opus"]["selected"]["bytes"],
            "byte_delta": receipt["opus"]["selected"]["byte_delta"],
            "resonith_snr_db": rm["waveform"]["snr_db"],
            "opus_snr_db": om["waveform"]["snr_db"],
            "resonith_log_mel_rmse": rm["spectral"]["log_mel_rmse"],
            "opus_log_mel_rmse": om["spectral"]["log_mel_rmse"],
            "resonith_magnitude_cosine": rm["spectral"]["magnitude_cosine_similarity"],
            "opus_magnitude_cosine": om["spectral"]["magnitude_cosine_similarity"],
        })
    aggregate = {
        "schema": "resonith-r217-s12-fixed-opus-aggregate-1",
        "status": "PASS",
        "scope": "current S11 Resonith versus fixed official Opus 1.6.1 direct anchor at maximum complexity; not an Opus frontier",
        "run_identity": run_identity,
        "run_material": material,
        "receipt_sha256": receipt_hashes,
        "item_count": len(rows),
        "rows": rows,
    }
    r216.replace_json_fsynced(root / "aggregate.json", aggregate)
    lines = [
        "# R-217 S12 fixed Opus direct comparison", "",
        "Status: **PASS**", "",
        f"Run identity: `{run_identity}`", "",
        "This is a direct comparison with one fixed maximum-complexity official Opus 1.6.1 anchor. It is not a maximum-effort Opus frontier and makes no general better-than-Opus claim.", "",
        "| Item | App | Resonith bytes | Opus bytes | Opus delta | Resonith SNR | Opus SNR | Resonith log-mel | Opus log-mel |", "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['application']} | {row['resonith_bytes']} | "
            f"{row['opus_bytes']} | {row['byte_delta']} | "
            f"{row['resonith_snr_db']:.4f} | {row['opus_snr_db']:.4f} | "
            f"{row['resonith_log_mel_rmse']:.5f} | {row['opus_log_mel_rmse']:.5f} |"
        )
    lines.extend(("", "All metrics use actual decoder PCM from identical registered source PCM.", ""))
    temporary = root / f".report.{uuid.uuid4().hex}.tmp"
    r216.write_fsynced(temporary, "\n".join(lines).encode("utf-8"))
    os.replace(temporary, root / "REPORT.md")


def _run_controller(arguments: argparse.Namespace) -> int:
    if shutil.disk_usage("G:\\").free < 10 * GIB:
        raise RuntimeError("R-217 requires at least 10 GiB free on G:")
    roots = {
        "orkela-public-benchmark": arguments.public_benchmark_root,
        "orkela-emotional-piano-8s": arguments.emotional_piano_root,
        "prepared-r111": arguments.prepared_root,
    }
    manifest, sources = r216.load_and_validate_manifest(arguments.manifest, roots)
    identities = _validate_identities(arguments, _identity_files(arguments))
    material = {
        "schema": RUNNER_SCHEMA,
        "manifest_sha256": MANIFEST_SHA256,
        "identities": identities,
        "dependency_versions": dependency_versions(),
        "python_executable": str(Path(sys.executable).resolve()),
        "configuration": "R-217 fixed official Opus 1.6.1 direct anchor",
        "opus_policy": {
            "mode": "vbr", "complexity": 10, "frame_us": 20000,
            "phase_inversion": True, "attempts": 4,
            "application_rule": "speech iff exact registered token speech; otherwise music",
        },
    }
    run_identity = hashlib.sha256(r216._json_bytes(material)).hexdigest()
    root = arguments.output.resolve()
    if os.name == "nt" and root.drive.upper() != "G:":
        raise RuntimeError("R-217 output must be on G:")
    existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    leftovers = list(root.glob(".*.staging.*"))
    if leftovers:
        for staging in leftovers:
            os.replace(staging, root / f"quarantine-{staging.name[1:]}-{uuid.uuid4().hex}")
        raise RuntimeError("leftover R-217 staging quarantined")
    index_path = root / "run-index.json"
    if existed and not index_path.exists() and any(root.iterdir()):
        raise RuntimeError("nonempty R-217 root has no run index")
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if index.get("schema") != RUN_SCHEMA or index.get("run_identity") != run_identity:
            raise RuntimeError("R-217 output belongs to a different run")
    else:
        index = {
            "schema": RUN_SCHEMA, "run_identity": run_identity,
            "completed_item_ids": [], "worker_resources": {},
            "receipt_sha256": {},
            "run_started_unix": time.time(),
        }
        r216.replace_json_fsynced(index_path, index)
    for item in manifest["items"]:
        remaining = 8 * 3600 - (time.time() - index["run_started_unix"])
        if remaining <= 0:
            raise TimeoutError("complete R-217 wall ceiling exceeded")
        if r216._tree_bytes(root) > 24 * GIB:
            raise RuntimeError("retained R-217 root ceiling exceeded")
        final = root / item["id"]
        if final.exists():
            expected_receipt = index.get("receipt_sha256", {}).get(item["id"])
            if item["id"] in index["completed_item_ids"] and not expected_receipt:
                raise RuntimeError("completed R-217 item lacks receipt authority hash")
            receipt = _verify_receipt(
                final, run_identity, item, expected_receipt
            )
            if item["id"] not in index["completed_item_ids"]:
                index["completed_item_ids"].append(item["id"])
                index["worker_resources"][item["id"]] = receipt["worker_resources"]
                index.setdefault("receipt_sha256", {})[item["id"]] = (
                    r216.sha256_file(final / "receipt.json")
                )
                r216.replace_json_fsynced(index_path, index)
            continue
        if item["id"] in index["completed_item_ids"]:
            raise RuntimeError("R-217 index references a missing item")
        staging = root / f".{item['id']}.staging.{uuid.uuid4().hex}"
        staging.mkdir()
        request_path = staging / "work-request.json"
        r216.write_json_fsynced(request_path, {
            "schema": WORK_SCHEMA,
            "run_identity": run_identity,
            "manifest_sha256": MANIFEST_SHA256,
            "item": item,
            "source_path": str(sources[item["id"]]),
            "native_core": str(arguments.native_core.resolve()),
            "opusenc": str(arguments.opusenc.resolve()),
            "opusdec": str(arguments.opusdec.resolve()),
            "worker_identities": {
                "runner": identities["runner"],
                "r216_import": identities["r216_import"],
                "metric_helper": identities["metric_helper"],
                "python_executable": identities["python_executable"],
                "source_file": item["source"]["file_sha256"],
                "native_core": identities["native_core"],
                "opusenc": identities["opusenc"],
                "opusdec": identities["opusdec"],
            },
            "dependency_versions": dependency_versions(),
        })
        long_item = item["id"] == "mozart-full"
        ceiling = 8 * GIB if long_item else 2 * GIB
        resources = r216.run_bounded(
            [sys.executable, str(Path(__file__).resolve()),
             "--worker-request", str(request_path)],
            min(
                remaining,
                LONG_WORKER_SECONDS if long_item else SHORT_WORKER_SECONDS,
            ),
            12 * GIB if long_item else 8 * GIB,
            REPOSITORY, staging, ceiling,
        )
        receipt_path = staging / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("status") != "PASS":
            raise RuntimeError(f"R-217 item failed closed: {receipt.get('status')}")
        receipt["worker_resources"] = resources
        receipt["retained_item_bytes"] = r216._tree_bytes(staging)
        receipt["item_disk_limit_bytes"] = ceiling
        r216.replace_json_fsynced(receipt_path, receipt)
        _verify_receipt(staging, run_identity, item)
        if r216._tree_bytes(staging) > ceiling:
            raise RuntimeError("R-217 item exceeded post-worker disk ceiling")
        request_path.unlink()
        os.replace(staging, final)
        receipt_sha256 = r216.sha256_file(final / "receipt.json")
        index["completed_item_ids"].append(item["id"])
        index["worker_resources"][item["id"]] = resources
        index.setdefault("receipt_sha256", {})[item["id"]] = receipt_sha256
        r216.replace_json_fsynced(index_path, index)
    _aggregate(
        root, manifest, run_identity, material,
        dict(index.get("receipt_sha256", {})),
    )
    if r216._tree_bytes(root) > 24 * GIB:
        raise RuntimeError("retained R-217 root ceiling exceeded after aggregate")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-request", type=Path)
    parser.add_argument("--manifest", type=Path, default=REPOSITORY / "experiments/fixtures/r216_s12_registered_manifest.json")
    parser.add_argument("--public-benchmark-root", type=Path)
    parser.add_argument("--emotional-piano-root", type=Path)
    parser.add_argument("--prepared-root", type=Path)
    parser.add_argument("--r117-complete-report", type=Path)
    parser.add_argument("--r117-r111-report", type=Path)
    parser.add_argument("--native-core", type=Path)
    parser.add_argument("--opusenc", type=Path)
    parser.add_argument("--opusdec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audited-runner-sha256")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.worker_request is not None:
        return _run_worker(arguments.worker_request.resolve())
    required = (
        "public_benchmark_root", "emotional_piano_root", "prepared_root",
        "r117_complete_report", "r117_r111_report", "native_core",
        "opusenc", "opusdec", "output", "audited_runner_sha256",
    )
    missing = [name for name in required if getattr(arguments, name) is None]
    if missing:
        raise ValueError(f"missing controller arguments: {', '.join(missing)}")
    return _run_controller(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
