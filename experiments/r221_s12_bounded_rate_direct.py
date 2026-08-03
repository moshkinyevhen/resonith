"""R-221 direct comparison with bounded rate-only fixed-Opus calibration."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from dataclasses import asdict, dataclass
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
RUN_SCHEMA = "resonith-r221-s12-bounded-rate-run-index-1"
RECEIPT_SCHEMA = "resonith-r221-s12-bounded-rate-item-receipt-1"
RUNNER_SCHEMA = "resonith-r221-s12-bounded-rate-runner-1"
WORK_SCHEMA = "resonith-r221-s12-bounded-rate-work-request-1"
GIB = 1024**3
SHORT_S11_SECONDS = 900.0
SHORT_WORKER_SECONDS = 1200.0
LONG_S11_SECONDS = 1200.0
LONG_WORKER_SECONDS = 2100.0

EXPECTED_SOURCE_REVISION = "1c45376eebe7daa49904acae885c47d6d571cf87"
EXPECTED_R216_SHA256 = "316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3"
EXPECTED_HELPER_SHA256 = r216.EXPECTED_HELPER_SHA256
EXPECTED_PREFLIGHT_SHA256 = "a97c1da031e905e4ac55d16f13f069f12cc330a2a657951e7824eadf1ca2c755"
EXPECTED_ANALYZER_SHA256 = "c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c"
EXPECTED_PREDICTOR_SHA256 = "583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec"
EXPECTED_OBJECTIVE_SHA256 = "284e27fca406775e90f0c0db075808b5203c9075600ccebf090e0065cb1c9bc5"
EXPECTED_MANIFEST_SHA256 = "551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0"
EXPECTED_CORE_SHA256 = r216.EXPECTED_CORE_SHA256
EXPECTED_OPUSENC_SHA256 = r216.EXPECTED_OPUSENC_SHA256
EXPECTED_OPUSDEC_SHA256 = r216.EXPECTED_OPUSDEC_SHA256
EXPECTED_PYTHON_SHA256 = "03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38"
EXPECTED_HOST_IDENTITY = {
    "implementation": "CPython",
    "machine": "AMD64",
    "release": "11",
    "system": "Windows",
    "version": "10.0.22631",
    "windows": {
        "build": 22631, "major": 10, "minor": 0,
        "platform": 2, "service_pack": "",
    },
}
MAXIMUM_RATE_ATTEMPTS = 12


@dataclass(frozen=True)
class Authority:
    """One immutable input plus the directory root whose identity contains it."""

    path: Path
    sha256: str
    containment_root: Path


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _normal_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _is_reparse(path: Path) -> bool:
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & 0x400)


def _assert_regular_authority(authority: Authority) -> None:
    path = authority.path.resolve()
    root = authority.containment_root.resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"authority escapes containment root: {path}") from error
    if not path.is_file() or path.is_symlink() or _is_reparse(path):
        raise RuntimeError(f"authority is missing, non-regular, or reparse: {path}")
    cursor = path.parent
    stop = root.parent
    while True:
        if not cursor.is_dir() or cursor.is_symlink() or _is_reparse(cursor):
            raise RuntimeError(f"authority ancestor is missing or reparse: {cursor}")
        if cursor == stop:
            break
        if cursor == cursor.parent:
            raise RuntimeError(f"containment ancestor walk escaped root: {path}")
        cursor = cursor.parent


def _authority_rows(authorities: list[Authority]) -> list[dict[str, str]]:
    merged: dict[str, Authority] = {}
    for authority in authorities:
        key = _normal_path(authority.path)
        previous = merged.get(key)
        if previous is not None and previous.sha256 != authority.sha256:
            raise RuntimeError(f"conflicting expected authority hash: {authority.path}")
        merged[key] = authority
    return [
        {"path": str(merged[key].path.resolve()), "sha256": merged[key].sha256}
        for key in sorted(merged)
    ]


def _authority_digest(authorities: list[Authority]) -> str:
    return _canonical_sha256(_authority_rows(authorities))


def _git_reference_authorities() -> list[Authority]:
    listing = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", EXPECTED_SOURCE_REVISION, "--", "reference"],
        cwd=REPOSITORY, check=True, capture_output=True,
    ).stdout
    authorities: list[Authority] = []
    for raw in listing.split(b"\0"):
        if not raw:
            continue
        header, raw_path = raw.split(b"\t", 1)
        mode, kind, _object = header.decode("ascii").split(" ")
        relative = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise RuntimeError(f"unsupported committed reference entry: {relative}")
        content = subprocess.run(
            ["git", "show", f"{EXPECTED_SOURCE_REVISION}:{relative}"],
            cwd=REPOSITORY, check=True, capture_output=True,
        ).stdout
        authorities.append(Authority(
            REPOSITORY / relative,
            hashlib.sha256(content).hexdigest(),
            REPOSITORY,
        ))
    if not authorities:
        raise RuntimeError("frozen revision contains no reference authorities")
    return authorities


def _write_canonical_json_fsynced(path: Path, value: object) -> bytes:
    payload = _canonical_json_bytes(value)
    r216.write_fsynced(path, payload)
    return payload


if os.name == "nt":
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _CreateFileW = _kernel32.CreateFileW
    _CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    )
    _CreateFileW.restype = wintypes.HANDLE
    _CloseHandle = _kernel32.CloseHandle
    _CloseHandle.argtypes = (wintypes.HANDLE,)
    _CloseHandle.restype = wintypes.BOOL
else:
    _CreateFileW = None
    _CloseHandle = None


def _open_deny_write_delete(path: Path, directory: bool) -> int:
    if os.name != "nt" or _CreateFileW is None:
        raise RuntimeError("R-221 immutable execution is Windows-only")
    desired = 0x00000081 if directory else 0x80000000
    flags = 0x02000000 if directory else 0x00000080
    handle = _CreateFileW(str(path.resolve()), desired, 0x00000001, None, 3, flags, None)
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        raise ctypes.WinError(ctypes.get_last_error())
    return int(handle)


@contextmanager
def _locked_authorities(authorities: list[Authority]):
    """Hold directory then file handles over one observed immutable interval."""
    if os.name != "nt":
        raise RuntimeError("R-221 immutable execution is Windows-only")
    unique: dict[str, Authority] = {}
    for authority in authorities:
        _assert_regular_authority(authority)
        key = _normal_path(authority.path)
        prior = unique.get(key)
        if prior is not None and prior.sha256 != authority.sha256:
            raise RuntimeError(f"conflicting authority hash: {authority.path}")
        unique[key] = authority
    directories: dict[str, Path] = {}
    for authority in unique.values():
        cursor = authority.path.resolve().parent
        stop = authority.containment_root.resolve().parent
        while True:
            directories[_normal_path(cursor)] = cursor
            if cursor == stop:
                break
            cursor = cursor.parent
    handles: list[int] = []
    try:
        for key in sorted(directories):
            handles.append(_open_deny_write_delete(directories[key], True))
        for key in sorted(unique):
            handles.append(_open_deny_write_delete(unique[key].path, False))
        observed = _authority_rows(list(unique.values()))
        for row in observed:
            if r216.sha256_file(Path(row["path"])) != row["sha256"]:
                raise RuntimeError(f"under-lock authority mismatch: {row['path']}")
        yield observed
        for row in observed:
            if r216.sha256_file(Path(row["path"])) != row["sha256"]:
                raise RuntimeError(f"postflight authority drift: {row['path']}")
    finally:
        errors = []
        while handles:
            handle = handles.pop()
            if not _CloseHandle(wintypes.HANDLE(handle)):
                errors.append(ctypes.get_last_error())
        if errors and sys.exc_info()[0] is None:
            raise RuntimeError(f"authority handle close failure: {errors}")


def dependency_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": metadata.version("scipy"),
        "pystoi": metadata.version("pystoi"),
    }


def host_identity() -> dict[str, object]:
    if os.name != "nt":
        raise RuntimeError("R-221 host identity is Windows-only")
    version = sys.getwindowsversion()
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "implementation": platform.python_implementation(),
        "windows": {
            "major": version.major,
            "minor": version.minor,
            "build": version.build,
            "platform": version.platform,
            "service_pack": version.service_pack,
        },
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
    records: list[dict[str, object]] = []
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

    # R-219's four points remain byte-for-byte first. R-221 may only bisect a
    # directly observed sign-changing bitrate bracket; it never extrapolates,
    # changes an Opus control, or consults decoded quality.
    previous_width: int | None = None
    while len(records) < MAXIMUM_RATE_ATTEMPTS:
        _canonical_rate_observations(records)
        if select_byte_match(records, target) is not None:
            break
        bracket = _tightest_legal_bracket(records, target)
        if bracket is None:
            break
        lower, upper = bracket
        width = int(upper["q5"]) - int(lower["q5"])
        if previous_width is not None and width >= previous_width:
            break
        q_mid = int(lower["q5"]) + width // 2
        observed_q5 = {int(row["q5"]) for row in records}
        if not int(lower["q5"]) < q_mid < int(upper["q5"]):
            break
        if q_mid in observed_q5:
            break
        previous_width = width
        output = temporary / f"feedback-{uuid.uuid4().hex}.opus"
        remaining = min(timeout, deadline - time.perf_counter())
        if remaining <= 0:
            raise TimeoutError("fixed Opus item wall ceiling exceeded")
        record = _encode_point_closed(
            opusenc, source, output, manifest_digest, item_id, config, q_mid,
            remaining, rss_limit, disk_root, disk_limit,
        )
        record["attempt"] = len(records)
        r216.append_jsonl_fsynced(
            ledger, {"record_kind": "bounded-rate-bisection", **record}
        )
        output.unlink()
        records.append(record)
    return records


def fixed_opus_config(categories: list[str]) -> r216.OpusConfig:
    """Return the sole R-221 anchor; only exact registered `speech` is special."""
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


def _canonical_rate_observations(
    attempts: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Collapse deterministic duplicate q5 points for bracket construction."""
    earliest: dict[int, dict[str, object]] = {}
    for position, attempt in enumerate(attempts):
        q5 = int(attempt["q5"])
        current = dict(attempt)
        current.setdefault("attempt", position)
        prior = earliest.get(q5)
        if prior is None:
            earliest[q5] = current
            continue
        if (
            int(prior["bytes"]) != int(current["bytes"])
            or str(prior["normalized_sha256"])
            != str(current["normalized_sha256"])
        ):
            raise RuntimeError("fixed Opus repeated-q5 determinism failure")
        if int(current["attempt"]) < int(prior["attempt"]):
            earliest[q5] = current
    return [earliest[q5] for q5 in sorted(earliest)]


def _tightest_legal_bracket(
    attempts: list[dict[str, object]], target: int,
) -> tuple[dict[str, object], dict[str, object]] | None:
    """Return the frozen minimum-span observed bitrate bracket, if one exists."""
    tolerance = max(64, target // 1000)
    observations = _canonical_rate_observations(attempts)
    candidates = []
    for lower in observations:
        for upper in observations:
            if (
                int(lower["q5"]) < int(upper["q5"])
                and int(lower["bytes"]) < target - tolerance
                and int(upper["bytes"]) > target + tolerance
            ):
                candidates.append((lower, upper))
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda pair: (
            int(pair[1]["q5"]) - int(pair[0]["q5"]),
            int(pair[0]["q5"]),
            int(pair[1]["q5"]),
            int(pair[0]["attempt"]),
            int(pair[1]["attempt"]),
        ),
    )


def select_nearest_rate_point(
    attempts: list[dict[str, object]], target: int,
) -> dict[str, object]:
    """Select the nearest observed bytes without reading any quality field."""
    if not attempts:
        raise ValueError("at least one fixed Opus observation is required")
    candidates = []
    for position, attempt in enumerate(attempts):
        candidate = dict(attempt)
        candidate["byte_delta"] = int(candidate["bytes"]) - target
        candidate["selection_position"] = position
        candidates.append(candidate)
    return min(
        candidates,
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
        "analyzer": r216.sha256_file(
            REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py"
        ),
        "predictor": r216.sha256_file(
            REPOSITORY / "reference/maf_p0/persistent_partial_field.py"
        ),
        "objective_metrics": r216.sha256_file(
            REPOSITORY / "experiments/objective_audio_metrics.py"
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
        raise RuntimeError("R-221 worker identity mismatch")
    if dependency_versions() != request.get("dependency_versions"):
        raise RuntimeError("R-221 worker dependency-version mismatch")
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
        raise RuntimeError("R-221 S11 report/stream identity mismatch")
    decoded_rate, decoded = r216.read_pcm16_channels(decoded_path)
    if decoded_rate != expected_rate or decoded.shape != expected_shape:
        raise RuntimeError("R-221 S11 actual decode shape/rate mismatch")
    if report["decoded_pcm16le_sha256"] != r216.pcm_sha256(decoded):
        raise RuntimeError("R-221 S11 report/decode identity mismatch")
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
        ledger, {"record_kind": "selected-fixed-measurement", **record}
    )
    with destination_ogg.open("r+b") as output:
        os.fsync(output.fileno())
    with destination_wav.open("r+b") as output:
        os.fsync(output.fileno())
    return record


def _retained_manifest(staging: Path) -> list[dict[str, object]]:
    """Bind every retained item file except the self-referential receipt."""
    rows = []
    for path in sorted(candidate for candidate in staging.rglob("*") if candidate.is_file()):
        if path.name == "receipt.json":
            continue
        rows.append({
            "path": path.relative_to(staging).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": r216.sha256_file(path),
        })
    return rows


def _run_worker(request_path: Path, expected_request_sha256: str) -> int:
    started_wall = time.perf_counter()
    request_bytes = request_path.read_bytes()
    observed_request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    if observed_request_sha256 != expected_request_sha256:
        raise RuntimeError("R-221 work-request seal mismatch")
    request = json.loads(request_bytes)
    if _canonical_json_bytes(request) != request_bytes:
        raise RuntimeError("R-221 work-request is not canonical")
    if request.get("schema") != WORK_SCHEMA:
        raise RuntimeError("invalid R-221 work-request schema")
    staging = request_path.parent
    item = request["item"]
    if _canonical_sha256(item) != request.get("manifest_item_sha256"):
        raise RuntimeError("R-221 manifest-item seal mismatch")
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
        raise RuntimeError("R-221 worker source identity mismatch")

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
    comparison_status = "STRICT_MATCH"
    if selected is None:
        selected = select_nearest_rate_point(attempts, target)
        comparison_status = "UNMATCHED_NEAREST"
    selected = dict(selected)
    selected["comparison_status"] = comparison_status
    selected["rate_delta_percent"] = (
        100.0 * int(selected["byte_delta"]) / target
    )
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
        raise RuntimeError("R-221 worker identity changed during execution")
    final_rate, final_source = r216.read_pcm16_channels(source)
    if (
        final_rate != rate
        or final_source.shape != samples.shape
        or r216.pcm_sha256(final_source)
        != item["source"]["pcm16_payload_sha256"]
    ):
        raise RuntimeError("R-221 source PCM changed during execution")
    if r216._tree_bytes(staging) > disk_limit:
        raise RuntimeError("R-221 staging exceeded final disk ceiling")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "PASS",
        "comparison_status": comparison_status,
        "rate_attempt_count": len(attempts),
        "run_identity": request["run_identity"],
        "item_id": item["id"],
        "work_request_sha256": observed_request_sha256,
        "work_request_bytes": len(request_bytes),
        "manifest_item_sha256": request["manifest_item_sha256"],
        "base_authority_set_sha256": request["base_authority_set_sha256"],
        "item_authority_set_sha256": request["item_authority_set_sha256"],
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
            "attempt_count": len(attempts),
            "attempts": attempts,
            "selected": opus,
            "comparison_status": comparison_status,
            "signed_complete_byte_delta": int(opus["byte_delta"]),
            "signed_rate_delta_percent": float(opus["rate_delta_percent"]),
        },
        "worker_self_wall_seconds": time.perf_counter() - started_wall,
        "retained_files": _retained_manifest(staging),
    }
    r216.write_json_fsynced(staging / "receipt.json", receipt)
    return 0


def _identity_files(arguments: argparse.Namespace) -> dict[str, Path]:
    return {
        "runner": Path(__file__).resolve(),
        "r216_import": Path(r216.__file__).resolve(),
        "metric_helper": REPOSITORY / "experiments/r216_s12_metrics.py",
        "preflight": REPOSITORY / "docs/reviews/R221_S12_BOUNDED_RATE_MATCH_PREFLIGHT_2026-08-02.md",
        "analyzer": REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py",
        "predictor": REPOSITORY / "reference/maf_p0/persistent_partial_field.py",
        "objective_metrics": REPOSITORY / "experiments/objective_audio_metrics.py",
        "registered_manifest": arguments.manifest,
        "native_core": arguments.native_core,
        "opusenc": arguments.opusenc,
        "opusdec": arguments.opusdec,
        "python_executable": Path(sys.executable).resolve(),
        "r117_complete_report": arguments.r117_complete_report,
        "r117_r111_report": arguments.r117_r111_report,
        "prepared_manifest": arguments.prepared_root / "prepared-manifest.json",
        "real_music_corpus": REPOSITORY / "experiments/real_music_corpus.json",
    }


def _expected_identity_hashes(arguments: argparse.Namespace) -> dict[str, str]:
    return {
        "runner": arguments.audited_runner_sha256,
        "r216_import": EXPECTED_R216_SHA256,
        "metric_helper": EXPECTED_HELPER_SHA256,
        "preflight": EXPECTED_PREFLIGHT_SHA256,
        "analyzer": EXPECTED_ANALYZER_SHA256,
        "predictor": EXPECTED_PREDICTOR_SHA256,
        "objective_metrics": EXPECTED_OBJECTIVE_SHA256,
        "registered_manifest": EXPECTED_MANIFEST_SHA256,
        "native_core": EXPECTED_CORE_SHA256,
        "opusenc": EXPECTED_OPUSENC_SHA256,
        "opusdec": EXPECTED_OPUSDEC_SHA256,
        "python_executable": EXPECTED_PYTHON_SHA256,
        "r117_complete_report": "cc906ac76c0bbd8acb3d4303818071c608e187eb0d152e075dd0986acfd98665",
        "r117_r111_report": "51709d0e18184f9d86b9397e8e282e1315ca6aa50304c3d86dffa719ca492fe8",
        "prepared_manifest": "2af905648ec33b092d172fb8868abcdb4f09db91615a9e675cacd4ddc54930f3",
        "real_music_corpus": "6eb7e6e6e330cf7d3890688ab5d67a0180c8be0403589e44dfe221b118f1ab9b",
    }


def _containment_root(path: Path, arguments: argparse.Namespace) -> Path:
    resolved = path.resolve()
    candidates = [
        REPOSITORY.resolve(),
        arguments.public_benchmark_root.resolve(),
        arguments.emotional_piano_root.resolve(),
        arguments.prepared_root.resolve(),
        arguments.native_core.resolve().parent,
        arguments.opusenc.resolve().parent,
        arguments.opusdec.resolve().parent,
        Path(sys.executable).resolve().parent,
        arguments.r117_complete_report.resolve().parent,
        arguments.r117_r111_report.resolve().parent,
    ]
    containing = []
    for candidate in candidates:
        try:
            resolved.relative_to(candidate)
            containing.append(candidate)
        except ValueError:
            pass
    if not containing:
        raise RuntimeError(f"no declared containment root for authority: {resolved}")
    return max(containing, key=lambda candidate: len(candidate.parts))


def _expected_base_authorities(
    arguments: argparse.Namespace,
) -> tuple[list[Authority], dict[str, str]]:
    files = _identity_files(arguments)
    identities = _expected_identity_hashes(arguments)
    if set(files) != set(identities):
        raise RuntimeError("R-221 identity file/hash key drift")
    authorities = [
        Authority(path.resolve(), identities[name], _containment_root(path, arguments))
        for name, path in files.items()
    ]
    authorities.extend(_git_reference_authorities())
    _authority_rows(authorities)
    return authorities, identities


def _validate_environment_locked(arguments: argparse.Namespace) -> None:
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
    if host_identity() != EXPECTED_HOST_IDENTITY:
        raise RuntimeError(f"frozen host identity mismatch: {host_identity()}")


def _load_manifest_metadata_locked(
    path: Path, roots: dict[str, Path],
) -> tuple[dict, dict[str, Path]]:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("registered manifest hash mismatch")
    manifest = json.loads(payload)
    items = manifest.get("items", [])
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("item_count") != 19
        or len(items) != 19
        or [row.get("order") for row in items] != list(range(1, 20))
        or len({row.get("id") for row in items}) != 19
        or items[0].get("id") != "mozart-full"
    ):
        raise RuntimeError("registered manifest structure/order mismatch")
    sources: dict[str, Path] = {}
    for item in items:
        source = r216._resolve_source(item, roots)
        logical_root = item["source"]["path"].split("/", 1)[0]
        try:
            source.relative_to(roots[logical_root].resolve())
        except (KeyError, ValueError) as error:
            raise RuntimeError(f"source escapes registered root: {item['id']}") from error
        sources[item["id"]] = source
    return manifest, sources


def _source_authority(
    item: dict, source: Path, roots: dict[str, Path],
) -> Authority:
    logical_root = item["source"]["path"].split("/", 1)[0]
    return Authority(
        source.resolve(), item["source"]["file_sha256"], roots[logical_root].resolve()
    )


def _validate_observed_rows(
    observed: list[dict[str, str]], expected_authorities: list[Authority], label: str,
) -> None:
    if observed != _authority_rows(expected_authorities):
        raise RuntimeError(f"under-lock {label} authority-set drift")


@contextmanager
def _locked_request(path: Path, expected_sha256: str):
    """Lock only the request file so the worker can still create sibling outputs."""
    handle = _open_deny_write_delete(path, False)
    try:
        if r216.sha256_file(path) != expected_sha256:
            raise RuntimeError("R-221 request drift before worker launch")
        yield
        if r216.sha256_file(path) != expected_sha256:
            raise RuntimeError("R-221 request drift after worker exit")
    finally:
        if not _CloseHandle(wintypes.HANDLE(handle)) and sys.exc_info()[0] is None:
            raise RuntimeError("R-221 request handle close failure")


def _assert_reparse_free_tree(root: Path) -> None:
    if not root.is_dir() or root.is_symlink() or _is_reparse(root):
        raise RuntimeError("R-221 output root is missing, non-directory, or reparse")
    for path in root.rglob("*"):
        if path.is_symlink() or _is_reparse(path):
            raise RuntimeError(f"R-221 output contains a reparse point: {path}")


def _quarantine_and_stop(path: Path, root: Path, reason: str) -> None:
    destination = root / f"quarantine-{path.name}-{uuid.uuid4().hex}"
    os.replace(path, destination)
    raise RuntimeError(f"{reason}; quarantined as {destination.name}")


def _validate_resume_index(
    index: dict, run_identity: str, material: dict,
    base_digest: str, item_digests: dict[str, str],
    manifest_item_digests: dict[str, str], manifest_item_ids: list[str],
) -> None:
    if (
        index.get("schema") != RUN_SCHEMA
        or index.get("run_identity") != run_identity
        or index.get("run_material_sha256") != _canonical_sha256(material)
        or index.get("base_authority_set_sha256") != base_digest
        or index.get("item_authority_set_sha256") != item_digests
        or index.get("manifest_item_sha256") != manifest_item_digests
    ):
        raise RuntimeError("R-221 output belongs to a different or stale run")
    completed = index.get("completed_item_ids")
    if (
        not isinstance(completed, list)
        or completed != manifest_item_ids[:len(completed)]
        or len(completed) != len(set(completed))
        or not isinstance(index.get("run_started_unix"), (int, float))
    ):
        raise RuntimeError("R-221 resume completion prefix is malformed")
    completed_set = set(completed)
    for field in ("worker_resources", "work_request_sha256", "receipt_sha256"):
        rows = index.get(field)
        if not isinstance(rows, dict) or set(rows) != completed_set:
            raise RuntimeError(f"R-221 resume {field} key set is malformed")


def _validate_runner_material(material: dict) -> None:
    if material.get("schema") != RUNNER_SCHEMA:
        raise RuntimeError("invalid R-221 runner material schema")


def _load_resume_index(
    root: Path, run_identity: str, material: dict,
    base_digest: str, item_digests: dict[str, str],
    manifest_item_digests: dict[str, str], manifest_item_ids: list[str],
) -> dict:
    index_path = root / "run-index.json"
    if not root.exists() or not index_path.is_file():
        raise RuntimeError("explicit R-221 resume requires an existing run index")
    _assert_reparse_free_tree(root)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    _validate_resume_index(
        index, run_identity, material, base_digest, item_digests,
        manifest_item_digests, manifest_item_ids,
    )
    return index


def _create_fresh_root(root: Path) -> None:
    if root.exists():
        raise RuntimeError("first R-221 launch requires a nonexistent output root")
    root.mkdir(parents=True)
    _assert_reparse_free_tree(root)


def _build_work_request(
    *, run_identity: str, item: dict, source: Path,
    arguments: argparse.Namespace, identities: dict[str, str],
    base_digest: str, item_digest: str,
) -> dict[str, object]:
    return {
        "schema": WORK_SCHEMA,
        "run_identity": run_identity,
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_item_sha256": _canonical_sha256(item),
        "base_authority_set_sha256": base_digest,
        "item_authority_set_sha256": item_digest,
        "item": item,
        "source_path": str(source.resolve()),
        "native_core": str(arguments.native_core.resolve()),
        "opusenc": str(arguments.opusenc.resolve()),
        "opusdec": str(arguments.opusdec.resolve()),
        "worker_identities": {
            "runner": identities["runner"],
            "r216_import": identities["r216_import"],
            "metric_helper": identities["metric_helper"],
            "analyzer": identities["analyzer"],
            "predictor": identities["predictor"],
            "objective_metrics": identities["objective_metrics"],
            "python_executable": identities["python_executable"],
            "source_file": item["source"]["file_sha256"],
            "native_core": identities["native_core"],
            "opusenc": identities["opusenc"],
            "opusdec": identities["opusdec"],
        },
        "dependency_versions": dependency_versions(),
    }


def _verify_receipt(
    final: Path, run_identity: str, item: dict,
    expected_receipt_sha256: str | None = None,
    *, expected_request_bytes: bytes | None = None,
    expected_base_digest: str | None = None,
    expected_item_digest: str | None = None,
) -> dict:
    receipt_path = final / "receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("final R-221 item has no receipt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt.get("schema") != RECEIPT_SCHEMA
        or receipt.get("status") != "PASS"
        or receipt.get("run_identity") != run_identity
        or receipt.get("item_id") != item["id"]
    ):
        raise RuntimeError("stale, unmatched, or corrupt R-221 receipt")
    comparison_status = receipt.get("comparison_status")
    opus = receipt.get("opus", {})
    selected = opus.get("selected", {}) if isinstance(opus, dict) else {}
    target = opus.get("target_complete_bytes") if isinstance(opus, dict) else None
    attempts = opus.get("attempts") if isinstance(opus, dict) else None
    if (
        comparison_status not in {"STRICT_MATCH", "UNMATCHED_NEAREST"}
        or opus.get("comparison_status") != comparison_status
        or selected.get("comparison_status") != comparison_status
        or not isinstance(target, int)
        or selected.get("byte_delta") != selected.get("bytes", 0) - target
        or opus.get("signed_complete_byte_delta") != selected.get("byte_delta")
        or opus.get("signed_rate_delta_percent")
        != 100.0 * selected.get("byte_delta", 0) / target
        or selected.get("rate_delta_percent")
        != opus.get("signed_rate_delta_percent")
        or not isinstance(attempts, list)
        or not 4 <= len(attempts) <= MAXIMUM_RATE_ATTEMPTS
        or opus.get("attempt_count") != len(attempts)
        or receipt.get("rate_attempt_count") != len(attempts)
        or [row.get("attempt") for row in attempts] != list(range(len(attempts)))
        or any(row.get("config") != opus.get("configuration") for row in attempts)
    ):
        raise RuntimeError("R-221 comparison-status/rate evidence mismatch")
    _canonical_rate_observations(attempts)
    expected_selected = (
        select_byte_match(attempts, target)
        if comparison_status == "STRICT_MATCH"
        else select_nearest_rate_point(attempts, target)
    )
    if expected_selected is None or any(
        selected.get(key) != expected_selected.get(key)
        for key in (
            "q5", "bytes", "attempt", "raw_sha256", "normalized_sha256",
            "byte_delta", "selection_position",
        )
    ):
        raise RuntimeError("R-221 selected point is not the byte-only observation")
    tolerance = int(opus.get("strict_tolerance_bytes", -1))
    if (
        (comparison_status == "STRICT_MATCH" and abs(selected["byte_delta"]) > tolerance)
        or (
            comparison_status == "UNMATCHED_NEAREST"
            and abs(selected["byte_delta"]) <= tolerance
        )
    ):
        raise RuntimeError("R-221 strict/unmatched classification mismatch")
    receipt_sha256 = r216.sha256_file(receipt_path)
    if (
        expected_receipt_sha256 is not None
        and receipt_sha256 != expected_receipt_sha256
    ):
        raise RuntimeError("R-221 receipt authority hash drift")
    request_path = final / "work-request.json"
    if not request_path.is_file():
        raise RuntimeError("R-221 retained work request is missing")
    request_bytes = request_path.read_bytes()
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    if expected_request_bytes is not None and request_bytes != expected_request_bytes:
        raise RuntimeError("R-221 retained work-request bytes drift")
    if (
        receipt.get("work_request_sha256") != request_sha256
        or receipt.get("work_request_bytes") != len(request_bytes)
        or receipt.get("manifest_item_sha256") != _canonical_sha256(item)
        or (
            expected_base_digest is not None
            and receipt.get("base_authority_set_sha256") != expected_base_digest
        )
        or (
            expected_item_digest is not None
            and receipt.get("item_authority_set_sha256") != expected_item_digest
        )
    ):
        raise RuntimeError("R-221 receipt/request authority mismatch")
    expected = {row["path"]: row for row in receipt["retained_files"]}
    actual = {
        path.relative_to(final).as_posix(): path
        for path in final.rglob("*")
        if path.is_file() and path.name != "receipt.json"
    }
    if set(expected) != set(actual):
        raise RuntimeError("R-221 retained evidence file-set drift")
    for name, row in expected.items():
        path = actual[name]
        if path.stat().st_size != row["bytes"] or r216.sha256_file(path) != row["sha256"]:
            raise RuntimeError("R-221 retained evidence drift")
    return receipt


def _aggregate(
    root: Path, manifest: dict, run_identity: str, material: dict,
    receipt_hashes: dict[str, str],
    request_bytes: dict[str, bytes], base_digest: str,
    item_digests: dict[str, str],
) -> None:
    receipts = [
        _verify_receipt(
            root / item["id"], run_identity, item,
            receipt_hashes.get(item["id"]),
            expected_request_bytes=request_bytes[item["id"]],
            expected_base_digest=base_digest,
            expected_item_digest=item_digests[item["id"]],
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
            "comparison_status": receipt["opus"]["comparison_status"],
            "attempt_count": receipt["opus"]["attempt_count"],
            "resonith_bytes": receipt["resonith"]["complete_bytes"],
            "opus_bytes": receipt["opus"]["selected"]["bytes"],
            "byte_delta": receipt["opus"]["selected"]["byte_delta"],
            "rate_delta_percent": receipt["opus"]["selected"]["rate_delta_percent"],
            "resonith_snr_db": rm["waveform"]["snr_db"],
            "opus_snr_db": om["waveform"]["snr_db"],
            "resonith_log_mel_rmse": rm["spectral"]["log_mel_rmse"],
            "opus_log_mel_rmse": om["spectral"]["log_mel_rmse"],
            "resonith_magnitude_cosine": rm["spectral"]["magnitude_cosine_similarity"],
            "opus_magnitude_cosine": om["spectral"]["magnitude_cosine_similarity"],
        })
    strict_rows = [row for row in rows if row["comparison_status"] == "STRICT_MATCH"]
    unmatched_rows = [
        row for row in rows if row["comparison_status"] == "UNMATCHED_NEAREST"
    ]
    aggregate = {
        "schema": "resonith-r221-s12-bounded-rate-aggregate-1",
        "status": "PASS",
        "comparison_status": (
            "CONTAINS_RATE_MISMATCH" if unmatched_rows else "ALL_STRICT_MATCH"
        ),
        "scope": "current S11 Resonith versus fixed official Opus 1.6.1 direct anchor at maximum complexity; not an Opus frontier",
        "run_identity": run_identity,
        "run_material": material,
        "receipt_sha256": receipt_hashes,
        "item_count": len(rows),
        "strict_match_count": len(strict_rows),
        "unmatched_count": len(unmatched_rows),
        "equal_rate_item_ids": [row["id"] for row in strict_rows],
        "equal_rate_excluded_item_ids": [row["id"] for row in unmatched_rows],
        "equal_rate_statistics_policy": (
            "Only STRICT_MATCH rows may enter any equal-rate count, average, "
            "win, or claim. UNMATCHED_NEAREST rows are evidence at actual rates."
        ),
        "rows": rows,
    }
    r216.replace_json_fsynced(root / "aggregate.json", aggregate)
    lines = [
        "# R-221 S12 bounded-rate fixed Opus direct comparison", "",
        "Status: **PASS**", "",
        f"Run identity: `{run_identity}`", "",
        "This is a direct comparison with one fixed maximum-complexity official Opus 1.6.1 anchor. Only integer requested bitrate is calibrated. It is not an Opus frontier and makes no general better-than-Opus claim.", "",
        f"Comparison status: **{aggregate['comparison_status']}**; strict rows: {len(strict_rows)}; unmatched rows: {len(unmatched_rows)}.", "",
        "| Item | App | Rate status | Attempts | Resonith bytes | Opus bytes | Opus delta | Delta % | Resonith SNR | Opus SNR | Resonith log-mel | Opus log-mel |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['application']} | {row['comparison_status']} | {row['attempt_count']} | {row['resonith_bytes']} | "
            f"{row['opus_bytes']} | {row['byte_delta']} | "
            f"{row['rate_delta_percent']:.6f}% | "
            f"{row['resonith_snr_db']:.4f} | {row['opus_snr_db']:.4f} | "
            f"{row['resonith_log_mel_rmse']:.5f} | {row['opus_log_mel_rmse']:.5f} |"
        )
    lines.extend((
        "",
        "All metrics use actual decoder PCM from identical registered source PCM.",
        "UNMATCHED_NEAREST rows are excluded from every equal-rate statistic or claim.",
        "",
    ))
    temporary = root / f".report.{uuid.uuid4().hex}.tmp"
    r216.write_fsynced(temporary, "\n".join(lines).encode("utf-8"))
    os.replace(temporary, root / "REPORT.md")


def _run_controller(arguments: argparse.Namespace) -> int:
    if os.name != "nt":
        raise RuntimeError("R-221 immutable comparison controller is Windows-only")
    if shutil.disk_usage("G:\\").free < 10 * GIB:
        raise RuntimeError("R-221 requires at least 10 GiB free on G:")
    roots = {
        "orkela-public-benchmark": arguments.public_benchmark_root,
        "orkela-emotional-piano-8s": arguments.emotional_piano_root,
        "prepared-r111": arguments.prepared_root,
    }

    # Freeze the complete static authority before trusting manifest metadata.
    base_authorities, identities = _expected_base_authorities(arguments)
    base_rows = _authority_rows(base_authorities)
    base_digest = _authority_digest(base_authorities)
    with _locked_authorities(base_authorities) as observed_base:
        _validate_observed_rows(observed_base, base_authorities, "base")
        _validate_environment_locked(arguments)
        manifest, sources = _load_manifest_metadata_locked(arguments.manifest, roots)

    item_authorities: dict[str, list[Authority]] = {}
    item_digests: dict[str, str] = {}
    manifest_item_digests: dict[str, str] = {}
    for item in manifest["items"]:
        current = base_authorities + [
            _source_authority(item, sources[item["id"]], roots)
        ]
        item_authorities[item["id"]] = current
        item_digests[item["id"]] = _authority_digest(current)
        manifest_item_digests[item["id"]] = _canonical_sha256(item)

    material = {
        "schema": RUNNER_SCHEMA,
        "manifest_sha256": MANIFEST_SHA256,
        "identities": identities,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "base_authority_rows": base_rows,
        "base_authority_set_sha256": base_digest,
        "item_authority_set_sha256": item_digests,
        "manifest_item_sha256": manifest_item_digests,
        "dependency_versions": dependency_versions(),
        "host_identity": host_identity(),
        "python_executable": str(Path(sys.executable).resolve()),
        "configuration": "R-221 bounded rate-only fixed official Opus 1.6.1 direct anchor",
        "opus_policy": {
            "mode": "vbr", "complexity": 10, "frame_us": 20000,
            "phase_inversion": True, "maximum_attempts": MAXIMUM_RATE_ATTEMPTS,
            "calibrated_coordinate": "integer requested bitrate only",
            "application_rule": "speech iff exact registered token speech; otherwise music",
        },
        "host_assumption": (
            "Declared project/tool/input authorities are byte-locked; Windows, "
            "kernel, drivers, standard library and complete site-packages are "
            "version-pinned frozen-host assumptions, not byte-locked authorities."
        ),
    }
    _validate_runner_material(material)
    run_identity = _canonical_sha256(material)
    manifest_item_ids = [item["id"] for item in manifest["items"]]
    expected_requests = {
        item["id"]: _canonical_json_bytes(_build_work_request(
            run_identity=run_identity,
            item=item,
            source=sources[item["id"]],
            arguments=arguments,
            identities=identities,
            base_digest=base_digest,
            item_digest=item_digests[item["id"]],
        ))
        for item in manifest["items"]
    }
    expected_request_hashes = {
        item_id: hashlib.sha256(payload).hexdigest()
        for item_id, payload in expected_requests.items()
    }

    root = arguments.output.resolve()
    if root.drive.upper() != "G:":
        raise RuntimeError("R-221 output must be on G:")
    index_path = root / "run-index.json"
    if arguments.resume_existing_run:
        index = _load_resume_index(
            root, run_identity, material, base_digest,
            item_digests, manifest_item_digests, manifest_item_ids,
        )
    else:
        _create_fresh_root(root)
        index = {
            "schema": RUN_SCHEMA,
            "run_identity": run_identity,
            "run_material_sha256": _canonical_sha256(material),
            "base_authority_set_sha256": base_digest,
            "item_authority_set_sha256": item_digests,
            "manifest_item_sha256": manifest_item_digests,
            "completed_item_ids": [],
            "worker_resources": {},
            "work_request_sha256": {},
            "receipt_sha256": {},
            "run_started_unix": time.time(),
        }
        r216.replace_json_fsynced(index_path, index)

    leftovers = list(root.glob(".*.staging.*"))
    if leftovers:
        for staging in leftovers:
            os.replace(staging, root / f"quarantine-{staging.name[1:]}-{uuid.uuid4().hex}")
        raise RuntimeError("leftover R-221 staging quarantined")

    for item in manifest["items"]:
        remaining = 8 * 3600 - (time.time() - index["run_started_unix"])
        if remaining <= 0:
            raise TimeoutError("complete R-221 wall ceiling exceeded")
        if r216._tree_bytes(root) > 24 * GIB:
            raise RuntimeError("retained R-221 root ceiling exceeded")
        final = root / item["id"]
        if final.exists():
            if item["id"] not in index["completed_item_ids"]:
                _quarantine_and_stop(
                    final, root, "unindexed rename-before-index R-221 item"
                )
            expected_receipt = index.get("receipt_sha256", {}).get(item["id"])
            expected_request = index.get("work_request_sha256", {}).get(item["id"])
            if not expected_receipt or expected_request != expected_request_hashes[item["id"]]:
                raise RuntimeError("completed R-221 item lacks receipt authority hash")
            with _locked_authorities(item_authorities[item["id"]]) as observed:
                _validate_observed_rows(
                    observed, item_authorities[item["id"]], f"item {item['id']}"
                )
                _verify_receipt(
                    final, run_identity, item, expected_receipt,
                    expected_request_bytes=expected_requests[item["id"]],
                    expected_base_digest=base_digest,
                    expected_item_digest=item_digests[item["id"]],
                )
            continue
        if item["id"] in index["completed_item_ids"]:
            raise RuntimeError("R-221 index references a missing item")
        staging = root / f".{item['id']}.staging.{uuid.uuid4().hex}"
        staging.mkdir()
        request_path = staging / "work-request.json"
        long_item = item["id"] == "mozart-full"
        ceiling = 8 * GIB if long_item else 2 * GIB
        with _locked_authorities(item_authorities[item["id"]]) as observed:
            _validate_observed_rows(
                observed, item_authorities[item["id"]], f"item {item['id']}"
            )
            request = _build_work_request(
                run_identity=run_identity,
                item=item,
                source=sources[item["id"]],
                arguments=arguments,
                identities=identities,
                base_digest=base_digest,
                item_digest=item_digests[item["id"]],
            )
            request_bytes = _write_canonical_json_fsynced(request_path, request)
            request_sha256 = hashlib.sha256(request_bytes).hexdigest()
            if (
                request_bytes != expected_requests[item["id"]]
                or request_sha256 != expected_request_hashes[item["id"]]
            ):
                raise RuntimeError("R-221 deterministic request construction drift")
            with _locked_request(request_path, request_sha256):
                resources = r216.run_bounded(
                    [
                        sys.executable, str(Path(__file__).resolve()),
                        "--worker-request", str(request_path),
                        "--worker-request-sha256", request_sha256,
                    ],
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
                    raise RuntimeError(
                        f"R-221 item failed closed: {receipt.get('status')}"
                    )
                receipt["worker_resources"] = resources
                receipt["retained_item_bytes"] = r216._tree_bytes(staging)
                receipt["item_disk_limit_bytes"] = ceiling
                r216.replace_json_fsynced(receipt_path, receipt)
                _verify_receipt(
                    staging, run_identity, item,
                    expected_request_bytes=request_bytes,
                    expected_base_digest=base_digest,
                    expected_item_digest=item_digests[item["id"]],
                )
                if r216._tree_bytes(staging) > ceiling:
                    raise RuntimeError("R-221 item exceeded post-worker disk ceiling")

        os.replace(staging, final)
        receipt_sha256 = r216.sha256_file(final / "receipt.json")
        index["completed_item_ids"].append(item["id"])
        index["worker_resources"][item["id"]] = resources
        index.setdefault("work_request_sha256", {})[item["id"]] = request_sha256
        index.setdefault("receipt_sha256", {})[item["id"]] = receipt_sha256
        r216.replace_json_fsynced(index_path, index)
    _aggregate(
        root, manifest, run_identity, material,
        dict(index.get("receipt_sha256", {})),
        expected_requests, base_digest, item_digests,
    )
    if r216._tree_bytes(root) > 24 * GIB:
        raise RuntimeError("retained R-221 root ceiling exceeded after aggregate")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-request", type=Path)
    parser.add_argument("--worker-request-sha256")
    parser.add_argument("--resume-existing-run", action="store_true")
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
        if not arguments.worker_request_sha256:
            raise ValueError("worker request SHA-256 is required")
        return _run_worker(
            arguments.worker_request.resolve(), arguments.worker_request_sha256
        )
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
