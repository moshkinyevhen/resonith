"""R-227 bounded phase-poisoned tiled-shadow experiment.

This is encoder-side research code. It emits only existing MFT1/CBF1 plus
lapped-Truth streams and never changes normative decoder behavior.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Callable
import wave

import numpy as np
from pystoi import stoi as _pystoi_stoi  # Preload complete speech-metric authority.
from scipy import signal

from experiments.r216_s12_metrics import compute_metrics, quality_axes
from experiments.r216_s12_opus_comparison import (
    _child_resources,
    _terminate_tree,
    _tree_bytes,
)
from reference.maf_p0.causal_basis_truth_candidate import (
    decode_causal_basis_truth_candidate,
)
from reference.maf_p0.complex_partial_analyzer import (
    ComplexPartialAnalyzerManifest,
    PartialResolution,
    observe_complex_partials,
)
from reference.maf_p0.lapped_oracle import encode_lapped_stream
from reference.maf_p0.maf_typed import (
    MAX_WARP_INSTANCE_SAMPLES,
    MAX_WARP_STEP_Q16,
    MafBasisWarpInstance,
    parse_maf_typed,
)
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.persistent_partial_field import (
    PersistentPartialLane,
    _evaluate_subset,
    _frequency_step_q16,
    _interpolate_integer,
    _one_past_position,
    _phase_turn_u32,
    _round_ratio_even,
)
from reference.maf_p0.rsc1 import parse_rsc1


REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = Path(
    r"G:\Resonith\artifacts\corpus\r227-stage1\source-identities.json"
)
SOURCE_MANIFEST_SHA256 = (
    "173b3c8c773a3152358dbe542bca53aa839999a2813fe3a8dbaeec63ac376f88"
)
NATIVE_CORE_SHA256 = (
    "f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed"
)
OBSERVATION_LIMIT = 3_500_000
RSS_LIMIT = 4 * 1024**3
ITEM_DISK_LIMIT = 8 * 1024**3
RUN_DISK_LIMIT = 12 * 1024**3
PYTHON_SHA256 = (
    "03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38"
)
FROZEN_AUTHORITIES = {
    "persistent_partial_field": (
        REPOSITORY / "reference/maf_p0/persistent_partial_field.py",
        "583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec",
    ),
    "complex_partial_analyzer": (
        REPOSITORY / "reference/maf_p0/complex_partial_analyzer.py",
        "c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c",
    ),
    "partial_graph_fixed": (
        REPOSITORY / "reference/maf_p0/partial_graph_fixed.py",
        "8a692d9d5894049277ae543b10e29c93ea1466cb4c2b648befd7349683f982bc",
    ),
    "lapped_oracle": (
        REPOSITORY / "reference/maf_p0/lapped_oracle.py",
        "e89cc95a10bf80d8de390807616c678535230aec4736364876dccf7acb1ab908",
    ),
    "maf_typed": (
        REPOSITORY / "reference/maf_p0/maf_typed.py",
        "f3cd7fc71f2fff24b3ef07841adf6ffa07a40f83fb82de8370c186b463098fc5",
    ),
    "causal_basis_field": (
        REPOSITORY / "reference/maf_p0/causal_basis_field.py",
        "8c5863a5ea2c2c11f7cdeb3a678f05e0041dd5967da15bf6cb56799c6c3a2b2a",
    ),
    "causal_basis_truth_candidate": (
        REPOSITORY / "reference/maf_p0/causal_basis_truth_candidate.py",
        "744b1589121d1b8785505b5eee6cf260ced0b7fdada9e641737be15614a97875",
    ),
    "native_core_wrapper": (
        REPOSITORY / "reference/maf_p0/native_core.py",
        "32c514e5c9cf4f1beffba61c62d262489f35e2fb0c2e74c3cfdae2a132694045",
    ),
    "r216_metrics": (
        REPOSITORY / "experiments/r216_s12_metrics.py",
        "ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3",
    ),
    "objective_metrics": (
        REPOSITORY / "experiments/objective_audio_metrics.py",
        "284e27fca406775e90f0c0db075808b5203c9075600ccebf090e0065cb1c9bc5",
    ),
    "rsc1": (
        REPOSITORY / "reference/maf_p0/rsc1.py",
        "20340df2fb0863ae49ce11421698fcce8371f9a852e41bf3fc53691150339e1b",
    ),
    "bounded_process_helper": (
        REPOSITORY / "experiments/r216_s12_opus_comparison.py",
        "316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3",
    ),
}
FROZEN_MODULE_IMPORTS = {
    "persistent_partial_field": "reference.maf_p0.persistent_partial_field",
    "complex_partial_analyzer": "reference.maf_p0.complex_partial_analyzer",
    "partial_graph_fixed": "reference.maf_p0.partial_graph_fixed",
    "lapped_oracle": "reference.maf_p0.lapped_oracle",
    "maf_typed": "reference.maf_p0.maf_typed",
    "causal_basis_field": "reference.maf_p0.causal_basis_field",
    "causal_basis_truth_candidate": "reference.maf_p0.causal_basis_truth_candidate",
    "native_core_wrapper": "reference.maf_p0.native_core",
    "r216_metrics": "experiments.r216_s12_metrics",
    "objective_metrics": "experiments.objective_audio_metrics",
    "rsc1": "reference.maf_p0.rsc1",
    "bounded_process_helper": "experiments.r216_s12_opus_comparison",
}


ObservationId = tuple[int, int, int, int]


@dataclass(frozen=True)
class PhaseFreeObservation:
    """One phase-inaccessible integer observation used by all search logic."""

    identity: ObservationId
    ordinal: int
    tile_id: int
    tile_end: int
    center_sample: int
    hop_samples: int
    frequency_q20: int
    frequency_uncertainty_q20: int
    aggregate_gain_q15: int
    gain_uncertainty_q15: int
    channel_gains_q15: tuple[int, ...]
    amplitude_lower_confidence_q15: int
    snr_db_q8: int
    snr_known: bool
    peak_prominence_db_q8: int
    locally_resolvable: bool
    ambiguity_identity: tuple[int, int, int, int]
    provenance: tuple[int, int, int, int]


@dataclass(frozen=True)
class PhaseEvidence:
    """Sealed objective phase coordinates, never passed to search functions."""

    channel_phase_turn_u32: tuple[int, ...]
    channel_phase_uncertainty_radians: tuple[float, ...]
    channel_usable: tuple[bool, ...]


class PhaseEvidenceAccess:
    """Unforgeable read capability created only by a sealed evidence vault."""

    __slots__ = ("__vault", "__token", "eligibility_sha256",
                 "eligibility_manifest_sha256", "evidence_sha256")

    def __init__(
        self,
        vault: "PhaseEvidenceVault",
        token: object,
        eligibility_sha256: str,
        eligibility_manifest_sha256: str,
        evidence_sha256: str,
    ) -> None:
        self.__vault = vault
        self.__token = token
        self.eligibility_sha256 = eligibility_sha256
        self.eligibility_manifest_sha256 = eligibility_manifest_sha256
        self.evidence_sha256 = evidence_sha256

    def __getitem__(self, identity: ObservationId) -> PhaseEvidence:
        return self.__vault._read(identity, self.__token)


class PhaseEvidenceVault:
    """Phase evidence that rejects every read until durable eligibility seal."""

    __slots__ = ("__evidence", "__token", "__sealed")

    def __init__(self, evidence: dict[ObservationId, PhaseEvidence]) -> None:
        self.__evidence = dict(evidence)
        self.__token = object()
        self.__sealed = False

    def _read(self, identity: ObservationId, token: object) -> PhaseEvidence:
        if not self.__sealed or token is not self.__token:
            raise RuntimeError("R-227 phase access attempted before eligibility seal")
        return self.__evidence[identity]

    def _seal(
        self,
        eligibility_sha256: str,
        committed_manifest_sha256: str,
        expected_manifest_sha256: str,
    ) -> PhaseEvidenceAccess:
        if self.__sealed:
            raise RuntimeError("R-227 phase evidence vault was already sealed")
        if committed_manifest_sha256 != expected_manifest_sha256:
            raise RuntimeError("R-227 eligibility manifest was not durably sealed")
        if len(eligibility_sha256) != 64:
            raise RuntimeError("R-227 invalid eligibility identity")
        material = [
            [
                list(identity), list(row.channel_phase_turn_u32),
                list(row.channel_phase_uncertainty_radians),
                list(row.channel_usable),
            ]
            for identity, row in sorted(self.__evidence.items())
        ]
        evidence_sha256 = sha256(_json_bytes(material)).hexdigest()
        self.__sealed = True
        return PhaseEvidenceAccess(
            self, self.__token, eligibility_sha256,
            committed_manifest_sha256, evidence_sha256,
        )


@dataclass(frozen=True)
class PhaseFreeTrack:
    track_id: int
    observations: tuple[PhaseFreeObservation, ...]


@dataclass(frozen=True)
class LanePlan:
    """A phase-free type-8 lane plan shared by carry and reset arms."""

    track_id: int
    channel: int
    basis_length: int
    observations: tuple[PhaseFreeObservation, ...]
    knot_indexes: tuple[int, ...]
    placement_count: int
    fit_error_q20: int
    estimated_energy_numerator: int

    @property
    def identity(self) -> tuple[int, int, int]:
        return (self.track_id, self.channel, self.basis_length)


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY,
        check=True, capture_output=True, text=True, timeout=30,
    )
    commit = completed.stdout.strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("R-227 invalid Git commit authority")
    return commit


def module_inventory() -> dict[str, dict[str, object]]:
    """Bind the origin and file hash of every loaded Python module."""

    inventory: dict[str, dict[str, object]] = {}
    for name, module in sorted(sys.modules.items()):
        specification = getattr(module, "__spec__", None)
        spec_origin = getattr(specification, "origin", None)
        file_origin = getattr(module, "__file__", None)
        if file_origin is not None:
            resolved = Path(file_origin).resolve()
            if not resolved.is_file():
                raise RuntimeError(f"R-227 loaded module origin is not a file: {name}")
            inventory[name] = {
                "kind": "file",
                "origin": str(resolved),
                "sha256": sha256_file(resolved),
            }
        elif spec_origin in {"built-in", "frozen"}:
            inventory[name] = {
                "kind": str(spec_origin), "origin": str(spec_origin)
            }
        elif spec_origin is None:
            inventory[name] = {"kind": "originless", "origin": None}
        else:
            inventory[name] = {"kind": "logical", "origin": str(spec_origin)}
    return inventory


def validate_authorities(
    core: Path,
    *,
    expected_runner_sha256: str | None = None,
    expected_commit: str | None = None,
) -> dict[str, object]:
    """Fail closed if any frozen implementation or runtime identity drifts."""

    identities = {}
    for name, (path, expected) in FROZEN_AUTHORITIES.items():
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"R-227 authority drift: {name}")
        module_name = FROZEN_MODULE_IMPORTS[name]
        module = sys.modules.get(module_name)
        if module is None or getattr(module, "__file__", None) is None:
            raise RuntimeError(f"R-227 authority module is not loaded: {name}")
        imported_path = Path(module.__file__).resolve()
        if imported_path != path.resolve():
            raise RuntimeError(f"R-227 imported module origin drift: {name}")
        identities[name] = {
            "path": str(path.resolve()), "sha256": actual,
            "module": module_name, "imported_path": str(imported_path),
        }
    python_path = Path(sys.executable).resolve()
    python_hash = sha256_file(python_path)
    if python_hash != PYTHON_SHA256:
        raise RuntimeError("R-227 Python executable drift")
    if sha256_file(core) != NATIVE_CORE_SHA256:
        raise RuntimeError("R-227 native Core drift")
    versions = {
        "numpy": np.__version__,
        "scipy": metadata.version("scipy"),
        "soundfile": metadata.version("soundfile"),
        "pystoi": metadata.version("pystoi"),
    }
    if versions != {
        "numpy": "2.5.1",
        "scipy": "1.18.0",
        "soundfile": "0.14.0",
        "pystoi": "0.4.1",
    }:
        raise RuntimeError("R-227 Python package identity drift")
    runner_path = Path(__file__).resolve()
    runner_hash = sha256_file(runner_path)
    commit = _git_commit()
    if expected_runner_sha256 is not None and runner_hash != expected_runner_sha256:
        raise RuntimeError("R-227 runner identity drift")
    if expected_commit is not None and commit != expected_commit:
        raise RuntimeError("R-227 Git commit identity drift")
    return {
        "files": identities,
        "python": {"path": str(python_path), "sha256": python_hash},
        "native_core": {"path": str(core.resolve()), "sha256": NATIVE_CORE_SHA256},
        "runner": {"path": str(runner_path), "sha256": runner_hash},
        "git_commit": commit,
        "versions": versions,
        "loaded_modules": module_inventory(),
    }


def pcm_sha256(samples: np.ndarray) -> str:
    return sha256(np.ascontiguousarray(samples, dtype="<i2").tobytes()).hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(temporary)
    with temporary.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: object) -> None:
    write_atomic(path, _json_bytes(value) + b"\n")


def run_bounded(
    command: list[str],
    timeout: float,
    rss_limit: int,
    cwd: Path,
    *,
    disk_root: Path,
    disk_limit: int,
) -> dict[str, object]:
    """Run one worker while observing the frozen wall/RSS/disk ceilings."""

    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name != "nt",
    )
    peak_rss = 0.0
    peak_cpu = 0.0
    peak_disk = 0
    observed_resource_sample = False
    while process.poll() is None:
        child_rss, child_cpu = _child_resources(process)
        if child_rss <= 0 or child_cpu < 0.0:
            _terminate_tree(process)
            raise RuntimeError("R-227 child resource authority failed closed")
        observed_resource_sample = True
        peak_rss = max(peak_rss, child_rss)
        peak_cpu = max(peak_cpu, child_cpu)
        peak_disk = max(peak_disk, _tree_bytes(disk_root))
        if peak_rss > rss_limit:
            _terminate_tree(process)
            raise MemoryError(f"R-227 worker RSS exceeded {rss_limit}")
        if peak_disk > disk_limit:
            _terminate_tree(process)
            raise OSError(f"R-227 worker disk exceeded {disk_limit}")
        if time.perf_counter() - started > timeout:
            _terminate_tree(process)
            raise TimeoutError(f"R-227 worker exceeded {timeout} seconds")
        time.sleep(0.025)
    stdout, stderr = process.communicate()
    child_rss, child_cpu = _child_resources(process)
    if child_rss <= 0 or child_cpu < 0.0:
        raise RuntimeError("R-227 final child resource authority failed closed")
    peak_rss = max(peak_rss, child_rss)
    peak_cpu = max(peak_cpu, child_cpu)
    peak_disk = max(peak_disk, _tree_bytes(disk_root))
    elapsed = time.perf_counter() - started
    if not observed_resource_sample or peak_rss <= 0:
        raise RuntimeError("R-227 child resource evidence is absent")
    if peak_rss > rss_limit:
        raise MemoryError(f"R-227 worker RSS exceeded {rss_limit}")
    if peak_disk > disk_limit:
        raise OSError(f"R-227 worker disk exceeded {disk_limit}")
    if elapsed > timeout:
        raise TimeoutError(f"R-227 worker exceeded {timeout} seconds")
    if process.returncode:
        detail = (stderr or stdout).strip()
        raise RuntimeError(f"R-227 worker failed ({process.returncode}): {detail}")
    return {
        "wall_seconds": elapsed,
        "cpu_seconds": peak_cpu,
        "peak_rss_bytes": int(peak_rss),
        "disk_high_water_bytes": peak_disk,
    }


def wav_bytes(sample_rate: int, samples: np.ndarray) -> bytes:
    import io

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(samples.shape[1])
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(np.ascontiguousarray(samples, dtype="<i2").tobytes())
    return buffer.getvalue()


def read_wav(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
            raise ValueError("R-227 source must be uncompressed PCM16 WAV")
        rate = source.getframerate()
        channels = source.getnchannels()
        frames = source.getnframes()
        payload = source.readframes(frames)
        if source.readframes(1):
            raise ValueError("R-227 WAV contains undeclared trailing frames")
    samples = np.frombuffer(payload, dtype="<i2").reshape(frames, channels).copy()
    samples.flags.writeable = False
    return rate, samples


def tile_boundaries(sample_rate: int, frame_count: int) -> tuple[int, ...]:
    """Return hop-aligned twelve-second target cores with one terminal bound."""

    hop = 2048 if sample_rate >= 32000 else 512
    target = 12 * sample_rate
    boundaries = [0]
    index = 1
    while boundaries[-1] < frame_count:
        boundary = min(
            frame_count,
            _round_ratio_even(index * target, hop) * hop,
        )
        if boundary > boundaries[-1]:
            boundaries.append(boundary)
        index += 1
    return tuple(boundaries)


def _saturating_gain(value: float) -> int:
    return min(32768, max(0, int(round(float(value)))))


def _validate_tile_centers(
    available_centers: list[int],
    expected_centers: list[int],
    hop: int,
) -> None:
    if any(center % hop for center in available_centers):
        raise RuntimeError("non-hop R-227 aggregate frame in tile")
    if len(available_centers) != len(set(available_centers)):
        raise RuntimeError("duplicate R-227 aggregate frame in tile")
    if sorted(set(expected_centers) - set(available_centers)):
        raise RuntimeError("missing R-227 expected aggregate frame in tile")


def observe_tiled_phase_shadow(
    samples: np.ndarray,
    sample_rate: int,
) -> tuple[tuple[PhaseFreeObservation, ...], PhaseEvidenceVault, dict]:
    """Observe exact R-186 tiles, then separate phase before any search."""

    fft_samples, hop = ((8192, 2048) if sample_rate >= 32000 else (2048, 512))
    manifest = ComplexPartialAnalyzerManifest(
        resolutions=(PartialResolution(fft_samples, hop),),
        maximum_observations=OBSERVATION_LIMIT,
    )
    boundaries = tile_boundaries(sample_rate, samples.shape[0])
    free_rows: list[PhaseFreeObservation] = []
    phase_rows: dict[ObservationId, PhaseEvidence] = {}
    seen_identities: set[ObservationId] = set()
    tile_reports = []
    ordinal = 0
    for tile_id, (core_start, core_end) in enumerate(
        zip(boundaries, boundaries[1:])
    ):
        slice_start = max(0, core_start - 4096)
        slice_start = (slice_start // hop) * hop
        slice_end = min(samples.shape[0], core_end + 4096)
        slice_end = min(
            samples.shape[0], ((slice_end + hop - 1) // hop) * hop
        )
        if slice_start % hop or (
            slice_end != samples.shape[0] and slice_end % hop
        ):
            raise RuntimeError("R-227 tile slice is not hop aligned")
        observed = observe_complex_partials(
            samples[slice_start:slice_end], sample_rate, manifest=manifest
        )
        allocation_rows = [
            row for row in observed.report["candidate_allocation_reports"]
            if row["detector_channel"] == -1
        ]
        available_centers = [
            slice_start + int(row["frame_index"]) * hop
            for row in allocation_rows
        ]
        expected_centers = list(range(
            ((core_start + hop - 1) // hop) * hop,
            core_end,
            hop,
        ))
        _validate_tile_centers(available_centers, expected_centers, hop)
        rank_by_center: dict[int, int] = {}
        admitted = 0
        for row in observed.observations:
            if row.detector_channel != -1:
                continue
            global_center = slice_start + row.center_sample
            if not core_start <= global_center < core_end:
                continue
            candidate_rank = rank_by_center.get(global_center, 0)
            rank_by_center[global_center] = candidate_rank + 1
            identity = (
                fft_samples,
                hop,
                global_center // hop,
                candidate_rank,
            )
            if identity in seen_identities:
                raise RuntimeError("duplicate R-227 global observation identity")
            seen_identities.add(identity)
            if not row.locally_resolvable or row.amplitude_lower_confidence <= 0.0:
                continue
            free = PhaseFreeObservation(
                identity=identity,
                ordinal=ordinal,
                tile_id=tile_id,
                tile_end=core_end,
                center_sample=global_center,
                hop_samples=hop,
                frequency_q20=int(round(row.frequency_hz * (1 << 20))),
                frequency_uncertainty_q20=max(
                    0, int(round(row.frequency_uncertainty_hz * (1 << 20)))
                ),
                aggregate_gain_q15=_saturating_gain(
                    row.normalized_detector_amplitude
                ),
                gain_uncertainty_q15=_saturating_gain(
                    row.amplitude_uncertainty / math.sqrt(samples.shape[1])
                ),
                channel_gains_q15=tuple(
                    _saturating_gain(value) for value in row.channel_amplitudes
                ),
                amplitude_lower_confidence_q15=_saturating_gain(
                    row.amplitude_lower_confidence
                ),
                snr_db_q8=int(round(row.snr_db * 256.0)),
                snr_known=bool(row.snr_known),
                peak_prominence_db_q8=int(round(row.peak_prominence_db * 256.0)),
                locally_resolvable=bool(row.locally_resolvable),
                ambiguity_identity=(
                    int(row.ambiguity_group[0]), int(row.ambiguity_group[1]),
                    global_center // hop, int(row.ambiguity_group[3]),
                ),
                provenance=(
                    int(row.provenance[0]), int(row.provenance[1]),
                    global_center // hop, int(row.provenance[3]),
                ),
            )
            free_rows.append(free)
            phase_rows[identity] = PhaseEvidence(
                channel_phase_turn_u32=tuple(
                    _phase_turn_u32(value) for value in row.channel_phases
                ),
                channel_phase_uncertainty_radians=tuple(
                    float(row.phase_uncertainty_radians)
                    for _ in row.channel_phases
                ),
                channel_usable=tuple(
                    bool(row.phase_usable) for _ in row.channel_phases
                ),
            )
            ordinal += 1
            admitted += 1
        tile_reports.append({
            "tile_id": tile_id,
            "core": [core_start, core_end],
            "slice": [slice_start, slice_end],
            "emitted_aggregate_frames": len(rank_by_center),
            "expected_aggregate_frames": len(expected_centers),
            "available_aggregate_frames": len(available_centers),
            "admitted_observations": admitted,
            "analyzer_report": observed.report,
        })
    free_rows.sort(key=lambda row: row.identity)
    if len({row.identity for row in free_rows}) != len(free_rows):
        raise RuntimeError("R-227 global observation identities are not unique")
    return tuple(free_rows), PhaseEvidenceVault(phase_rows), {
        "fft_samples": fft_samples,
        "hop_samples": hop,
        "boundaries": list(boundaries),
        "tiles": tile_reports,
    }


def phase_free_digest(rows: tuple[PhaseFreeObservation, ...]) -> str:
    material = [
        [
            list(row.identity), row.ordinal, row.tile_id, row.tile_end,
            row.center_sample, row.hop_samples, row.frequency_q20,
            row.frequency_uncertainty_q20, row.aggregate_gain_q15,
            row.gain_uncertainty_q15, list(row.channel_gains_q15),
            row.amplitude_lower_confidence_q15, row.snr_db_q8,
            row.snr_known, row.peak_prominence_db_q8,
            row.locally_resolvable, list(row.ambiguity_identity),
            list(row.provenance),
        ]
        for row in rows
    ]
    return sha256(_json_bytes(material)).hexdigest()


def _phase_position_from_turn_u32(turn_u32: int, basis_length: int) -> int:
    period = basis_length << 16
    return _round_ratio_even((turn_u32 & 0xFFFFFFFF) * period, 1 << 32) % period


def seal_phase_evidence(
    vault: PhaseEvidenceVault,
    eligibility_manifest: dict[str, object],
    commit_eligibility: Callable[[dict[str, object]], str],
) -> PhaseEvidenceAccess:
    eligibility_sha256 = str(eligibility_manifest.get("eligibility_sha256", ""))
    expected_file_sha256 = sha256(
        _json_bytes(eligibility_manifest) + b"\n"
    ).hexdigest()
    committed_file_sha256 = commit_eligibility(eligibility_manifest)
    return vault._seal(
        eligibility_sha256, committed_file_sha256, expected_file_sha256
    )


def _edge_score(
    previous: PhaseFreeObservation,
    current: PhaseFreeObservation,
    previous_track_id: int,
) -> tuple[int, int, int, ObservationId] | None:
    frequency_error = abs(previous.frequency_q20 - current.frequency_q20)
    frequency_limit = max(
        2 << 20,
        3 * max(
            previous.frequency_uncertainty_q20,
            current.frequency_uncertainty_q20,
        ),
    )
    gain_error = abs(previous.aggregate_gain_q15 - current.aggregate_gain_q15)
    gain_limit = max(
        8,
        (18 * max(
            previous.aggregate_gain_q15, current.aggregate_gain_q15, 1
        ) + 99) // 100,
        3 * max(previous.gain_uncertainty_q15, current.gain_uncertainty_q15),
    )
    if frequency_error > frequency_limit or gain_error > gain_limit:
        return None
    return (
        _round_ratio_even(frequency_error << 20, frequency_limit),
        _round_ratio_even(gain_error << 20, gain_limit),
        previous_track_id,
        current.identity,
    )


def track_phase_free(
    rows: tuple[PhaseFreeObservation, ...],
) -> tuple[PhaseFreeTrack, ...]:
    """Track adjacent aggregate frames without accepting a phase parameter."""

    by_tile: dict[int, dict[int, list[PhaseFreeObservation]]] = {}
    for row in rows:
        by_tile.setdefault(row.tile_id, {}).setdefault(row.center_sample, []).append(row)
    tracks: dict[int, list[PhaseFreeObservation]] = {}
    next_track = 0
    for tile_id in sorted(by_tile):
        active: dict[ObservationId, int] = {}
        previous_rows: list[PhaseFreeObservation] = []
        previous_center: int | None = None
        for center in sorted(by_tile[tile_id]):
            current_rows = sorted(by_tile[tile_id][center], key=lambda row: row.identity)
            if previous_center is None or center - previous_center != current_rows[0].hop_samples:
                active = {}
                previous_rows = []
            edges = []
            for previous in previous_rows:
                for current in current_rows:
                    score = _edge_score(previous, current, active[previous.identity])
                    if score is not None:
                        edges.append((score, previous.identity, current.identity))
            edges.sort(key=lambda item: item[0])
            used_previous: set[ObservationId] = set()
            used_current: set[ObservationId] = set()
            new_active: dict[ObservationId, int] = {}
            current_map = {row.identity: row for row in current_rows}
            for _, previous_id, current_id in edges:
                if previous_id in used_previous or current_id in used_current:
                    continue
                track_id = active[previous_id]
                tracks[track_id].append(current_map[current_id])
                new_active[current_id] = track_id
                used_previous.add(previous_id)
                used_current.add(current_id)
            for current in current_rows:
                if current.identity in used_current:
                    continue
                track_id = next_track
                next_track += 1
                tracks[track_id] = [current]
                new_active[current.identity] = track_id
            active = new_active
            previous_rows = current_rows
            previous_center = center
    return tuple(
        PhaseFreeTrack(track_id, tuple(observations))
        for track_id, observations in sorted(tracks.items())
    )


def _lane_energy_numerator(
    observations: tuple[PhaseFreeObservation, ...], channel: int
) -> int:
    total = 0
    for left, right in zip(observations, observations[1:]):
        span = right.center_sample - left.center_sample
        g0 = left.channel_gains_q15[channel]
        g1 = right.channel_gains_q15[channel]
        total += span * (g0 * g0 + g0 * g1 + g1 * g1)
    last = observations[-1]
    tail = min(last.tile_end, last.center_sample + last.hop_samples) - last.center_sample
    total += 3 * max(0, tail) * last.channel_gains_q15[channel] ** 2
    return total


def _span_fit(
    rows: tuple[PhaseFreeObservation, ...],
    channel: int,
    begin: int,
    end: int,
    basis_length: int,
    sample_rate: int,
) -> tuple[int, int] | None:
    left, right = rows[begin], rows[end]
    span = right.center_sample - left.center_sample
    if span <= 0:
        return None
    try:
        start_step = _frequency_step_q16(
            left.frequency_q20 / float(1 << 20), sample_rate, basis_length
        )
        end_step = _frequency_step_q16(
            right.frequency_q20 / float(1 << 20), sample_rate, basis_length
        )
    except ValueError:
        return None
    if not (
        -MAX_WARP_STEP_Q16 <= start_step <= MAX_WARP_STEP_Q16
        and -MAX_WARP_STEP_Q16 <= end_step <= MAX_WARP_STEP_Q16
    ):
        return None
    error = 0
    for row in rows[begin:end + 1]:
        offset = row.center_sample - left.center_sample
        predicted_frequency = _interpolate_integer(
            left.frequency_q20, right.frequency_q20, offset, span
        )
        actual_gain = row.channel_gains_q15[channel]
        predicted_gain = _interpolate_integer(
            left.channel_gains_q15[channel],
            right.channel_gains_q15[channel],
            offset,
            span,
        )
        frequency_limit = max(
            2 << 20,
            3 * max(
                left.frequency_uncertainty_q20,
                row.frequency_uncertainty_q20,
                right.frequency_uncertainty_q20,
            ),
        )
        gain_limit = max(
            8,
            (18 * max(
                left.channel_gains_q15[channel], actual_gain,
                right.channel_gains_q15[channel], 1,
            ) + 99) // 100,
            3 * max(
                left.gain_uncertainty_q15,
                row.gain_uncertainty_q15,
                right.gain_uncertainty_q15,
            ),
        )
        frequency_error = abs(row.frequency_q20 - predicted_frequency)
        gain_error = abs(actual_gain - predicted_gain)
        if frequency_error > frequency_limit or gain_error > gain_limit:
            return None
        error += _round_ratio_even(frequency_error << 20, frequency_limit)
        error += _round_ratio_even(gain_error << 20, gain_limit)
    return math.ceil(span / MAX_WARP_INSTANCE_SAMPLES), error


def _plan_knots(
    rows: tuple[PhaseFreeObservation, ...],
    channel: int,
    basis_length: int,
    sample_rate: int,
) -> tuple[tuple[int, ...], int, int] | None:
    best: list[tuple[int, int, int] | None] = [None] * len(rows)
    best[0] = (0, 0, -1)
    for end in range(1, len(rows)):
        choice = None
        for begin in range(end):
            if best[begin] is None:
                continue
            fitted = _span_fit(rows, channel, begin, end, basis_length, sample_rate)
            if fitted is None:
                continue
            placements, error = fitted
            candidate = (
                best[begin][0] + placements,
                best[begin][1] + error,
                begin,
            )
            if choice is None or candidate < choice:
                choice = candidate
        best[end] = choice
    if best[-1] is None:
        return None
    knots = [len(rows) - 1]
    cursor = len(rows) - 1
    while cursor:
        cursor = best[cursor][2]
        knots.append(cursor)
    knots.reverse()
    tail = min(
        rows[-1].tile_end,
        rows[-1].center_sample + rows[-1].hop_samples,
    ) - rows[-1].center_sample
    tail_placements = math.ceil(max(0, tail) / MAX_WARP_INSTANCE_SAMPLES)
    return tuple(knots), best[-1][0] + tail_placements, best[-1][1]


def plan_phase_free_lanes(
    tracks: tuple[PhaseFreeTrack, ...],
    samples: np.ndarray,
    sample_rate: int,
) -> tuple[LanePlan, ...]:
    source_energy = tuple(
        int(np.sum(samples[:, channel].astype(np.int64) ** 2))
        for channel in range(samples.shape[1])
    )
    proposals = []
    for track in tracks:
        rows = track.observations
        if (
            len(rows) < 8
            or rows[-1].center_sample - rows[0].center_sample < sample_rate
            or len({row.tile_id for row in rows}) != 1
        ):
            continue
        for channel in range(samples.shape[1]):
            energy = _lane_energy_numerator(rows, channel)
            if 1000 * energy < 6 * source_energy[channel]:
                continue
            basis_choices = []
            for basis_order, basis_length in enumerate((256, 128, 64, 32, 16)):
                planned = _plan_knots(
                    rows, channel, basis_length, sample_rate
                )
                if planned is None:
                    continue
                knots, placements, error = planned
                if placements <= 4096:
                    basis_choices.append(
                        (placements, error, basis_order, basis_length, knots)
                    )
            if not basis_choices:
                continue
            placements, error, _, basis_length, knots = min(basis_choices)
            proposals.append(LanePlan(
                track_id=track.track_id,
                channel=channel,
                basis_length=basis_length,
                observations=rows,
                knot_indexes=knots,
                placement_count=placements,
                fit_error_q20=error,
                estimated_energy_numerator=energy,
            ))
    proposals.sort(key=lambda lane: (
        -lane.estimated_energy_numerator, lane.track_id, lane.channel,
        -lane.basis_length,
    ))
    return tuple(proposals[:6])


def enumerate_subsets(lanes: tuple[LanePlan, ...]) -> tuple[tuple[LanePlan, ...], ...]:
    if len(lanes) <= 4:
        return tuple(
            tuple(lanes[index] for index in indexes)
            for count in range(1, len(lanes) + 1)
            for indexes in itertools.combinations(range(len(lanes)), count)
        )
    return tuple(lanes[:count] for count in range(1, len(lanes) + 1))


def eligibility_digest(
    rows: tuple[PhaseFreeObservation, ...],
    tracks: tuple[PhaseFreeTrack, ...],
    lanes: tuple[LanePlan, ...],
    subsets: tuple[tuple[LanePlan, ...], ...],
) -> str:
    material = {
        "observations": phase_free_digest(rows),
        "tracks": [
            {
                "track_id": track.track_id,
                "observations": [
                    list(row.identity) for row in track.observations
                ],
            }
            for track in tracks
        ],
        "lanes": [
            {
                "identity": list(lane.identity),
                "observations": [list(row.identity) for row in lane.observations],
                "knots": list(lane.knot_indexes),
                "placements": lane.placement_count,
                "fit_error_q20": lane.fit_error_q20,
                "energy": lane.estimated_energy_numerator,
            }
            for lane in lanes
        ],
        "subsets": [
            [list(lane.identity) for lane in subset] for subset in subsets
        ],
    }
    return sha256(_json_bytes(material)).hexdigest()


def _lower_lane(
    plan: LanePlan,
    phase: PhaseEvidenceAccess,
    sample_rate: int,
    reset_knots: bool,
) -> PersistentPartialLane:
    rows = plan.observations
    knots = plan.knot_indexes
    period = plan.basis_length * (1 << 16)
    position = _phase_position_from_turn_u32(
        phase[rows[0].identity].channel_phase_turn_u32[plan.channel],
        plan.basis_length,
    )
    instances = []
    for span_index, (left_index, right_index) in enumerate(zip(knots, knots[1:])):
        left, right = rows[left_index], rows[right_index]
        span = right.center_sample - left.center_sample
        if reset_knots and span_index > 0:
            position = _phase_position_from_turn_u32(
                phase[left.identity].channel_phase_turn_u32[plan.channel],
                plan.basis_length,
            )
        start_step = _frequency_step_q16(
            left.frequency_q20 / float(1 << 20), sample_rate, plan.basis_length
        )
        end_step = _frequency_step_q16(
            right.frequency_q20 / float(1 << 20), sample_rate, plan.basis_length
        )
        start_gain = left.channel_gains_q15[plan.channel]
        end_gain = right.channel_gains_q15[plan.channel]
        consumed = 0
        while consumed < span:
            count = min(MAX_WARP_INSTANCE_SAMPLES, span - consumed)
            piece_start_step = _interpolate_integer(
                start_step, end_step, consumed, span
            )
            piece_end_step = _interpolate_integer(
                start_step, end_step, consumed + count, span
            )
            piece_start_gain = _interpolate_integer(
                start_gain, end_gain, consumed, span
            )
            piece_end_gain = _interpolate_integer(
                start_gain, end_gain, consumed + count, span
            )
            instances.append(MafBasisWarpInstance(
                emitter_id=0,
                basis_id=0,
                start=left.center_sample + consumed,
                sample_count=count,
                source_position_q16=position % period,
                source_step_q16=piece_start_step,
                gain_q15=piece_start_gain,
                circular=True,
                end_source_step_q16=(
                    piece_end_step
                    if count >= 3 and piece_end_step != piece_start_step
                    else None
                ),
                end_gain_q15=(
                    piece_end_gain
                    if count >= 2 and piece_end_gain != piece_start_gain
                    else None
                ),
            ))
            position = _one_past_position(
                position,
                piece_start_step,
                piece_end_step if count >= 3 else piece_start_step,
                count,
                plan.basis_length,
            )
            consumed += count
    last = rows[knots[-1]]
    tail = min(last.tile_end, last.center_sample + last.hop_samples) - last.center_sample
    if tail > 0:
        if reset_knots and len(knots) > 1:
            position = _phase_position_from_turn_u32(
                phase[last.identity].channel_phase_turn_u32[plan.channel],
                plan.basis_length,
            )
        step = _frequency_step_q16(
            last.frequency_q20 / float(1 << 20), sample_rate, plan.basis_length
        )
        instances.append(MafBasisWarpInstance(
            emitter_id=0,
            basis_id=0,
            start=last.center_sample,
            sample_count=tail,
            source_position_q16=position % period,
            source_step_q16=step,
            gain_q15=last.channel_gains_q15[plan.channel],
            circular=True,
        ))
    if len(instances) != plan.placement_count:
        raise RuntimeError("R-227 lowering changed the sealed placement count")
    return PersistentPartialLane(
        path_id=plan.track_id,
        channel=plan.channel,
        basis_length=plan.basis_length,
        native_observation_ids=tuple(row.ordinal for row in rows),
        support_native_observation_ids=tuple(row.ordinal for row in rows),
        retained_native_observation_ids=tuple(rows[index].ordinal for index in knots),
        instances=tuple(instances),
        span_fit_kinds=tuple("phase-free-linear" for _ in zip(knots, knots[1:])),
        estimated_energy=float(plan.estimated_energy_numerator),
        maximum_phase_error_radians=0.0,
        pruned_observation_count=0,
        placement_count_before_tail_fusion=len(instances),
        tail_fused=False,
        tail_boundary_phase_identity=False,
    )


def _fixed_transport_payload(result, transport: str) -> bytes:
    if transport == "cbf1":
        return result.cbf_complete
    if transport == "mft1":
        return result.mft1_complete
    raise ValueError("unknown R-227 transport")


def _byte_ledger(result, transport: str) -> dict[str, int]:
    selected = _fixed_transport_payload(result, transport)
    selected_info = parse_rsc1(selected)
    selected_sections = {
        bytes(section.type_code): section.payload for section in selected_info.sections
    }
    predictor_type = b"CBF1" if transport == "cbf1" else b"MFT1"
    predictor_bytes = len(selected_sections[predictor_type])
    residual_bytes = len(selected_sections[b"MRI1"])

    cbf_sections = {
        bytes(section.type_code): section.payload
        for section in parse_rsc1(result.cbf_complete).sections
    }
    mft_sections = {
        bytes(section.type_code): section.payload
        for section in parse_rsc1(result.mft1_complete).sections
    }
    return {
        "complete_bytes": len(selected),
        "predictor_bytes": predictor_bytes,
        "residual_bytes": residual_bytes,
        "container_wrapper_bytes": len(selected) - predictor_bytes - residual_bytes,
        "cbf1_predictor_bytes": len(cbf_sections[b"CBF1"]),
        "mft1_predictor_bytes": len(mft_sections[b"MFT1"]),
        "cbf1_complete_bytes": len(result.cbf_complete),
        "mft1_complete_bytes": len(result.mft1_complete),
    }


def _turn_distance(left: int, right: int) -> int:
    delta = abs((left & 0xFFFFFFFF) - (right & 0xFFFFFFFF))
    return min(delta, (1 << 32) - delta)


def _phase_reset_events(
    plans: tuple[LanePlan, ...],
    carry_lanes: tuple[PersistentPartialLane, ...],
    reset_lanes: tuple[PersistentPartialLane, ...],
) -> list[dict[str, int]]:
    events: list[dict[str, int]] = []
    for plan, carry_lane, reset_lane in zip(plans, carry_lanes, reset_lanes):
        if len(carry_lane.instances) != len(reset_lane.instances):
            raise RuntimeError("R-227 paired lowering changed placement count")
        retained_starts = {
            plan.observations[index].center_sample
            for index in plan.knot_indexes[1:]
        }
        period = plan.basis_length << 16
        for carry_instance, reset_instance in zip(
            carry_lane.instances, reset_lane.instances
        ):
            if carry_instance.start not in retained_starts:
                continue
            delta_q16 = (
                reset_instance.source_position_q16
                - carry_instance.source_position_q16
            ) % period
            delta_turn_u32 = _round_ratio_even(delta_q16 << 32, period) & 0xFFFFFFFF
            events.append({
                "track_id": plan.track_id,
                "channel": plan.channel,
                "lane_birth_sample": plan.observations[0].center_sample,
                "start_sample": carry_instance.start,
                "delta_turn_u32": delta_turn_u32,
            })
    return events


def _subset_id(subset: tuple[LanePlan, ...]) -> tuple[tuple[int, int, int], ...]:
    return tuple(sorted(lane.identity for lane in subset))


def _stereo_delay(samples: np.ndarray, sample_rate: int) -> int | None:
    if samples.shape[1] != 2:
        return None
    left = samples[:, 0].astype(np.float64)
    right = samples[:, 1].astype(np.float64)
    left -= np.mean(left)
    right -= np.mean(right)
    count = samples.shape[0]
    limit = min(_round_ratio_even(sample_rate, 5), count - 1)
    # Each left sample belongs to one block. A right halo of L samples makes
    # the sum equal to the declared whole-input correlation while bounding FFT
    # workspace independently of track duration.
    correlation = np.zeros(2 * limit + 1, dtype=np.float64)
    block_samples = 1 << 18
    for begin in range(0, count, block_samples):
        end = min(count, begin + block_samples)
        left_block = left[begin:end]
        right_segment = np.zeros((end - begin) + 2 * limit, dtype=np.float64)
        source_begin = max(0, begin - limit)
        source_end = min(count, end + limit)
        destination_begin = source_begin - (begin - limit)
        right_segment[
            destination_begin:destination_begin + source_end - source_begin
        ] = right[source_begin:source_end]
        block_correlation = signal.correlate(
            right_segment, left_block, mode="full", method="fft"
        )
        first = len(left_block) - 1
        correlation += block_correlation[first:first + 2 * limit + 1]
    left_total = float(np.dot(left, left))
    right_total = float(np.dot(right, right))
    candidates = []
    for lag in range(-limit, limit + 1):
        if lag >= 0:
            left_energy = left_total - float(np.dot(left[count - lag:], left[count - lag:]))
            right_energy = right_total - float(np.dot(right[:lag], right[:lag]))
        else:
            offset = -lag
            left_energy = left_total - float(np.dot(left[:offset], left[:offset]))
            right_energy = right_total - float(np.dot(right[count - offset:], right[count - offset:]))
        denominator = math.sqrt(left_energy * right_energy)
        if denominator == 0.0:
            return None
        candidates.append((float(correlation[lag + limit]) / denominator, lag))
    return min(candidates, key=lambda item: (-item[0], abs(item[1]), item[1]))[1]


def _quality_nonregression(
    carry: dict[str, object],
    reset: dict[str, object],
) -> tuple[bool, list[dict[str, object]]]:
    carry_axes = quality_axes(carry)
    reset_axes = quality_axes(reset)
    if set(carry_axes) != set(reset_axes):
        raise RuntimeError("R-227 metric applicability differs")
    comparisons = []
    passed = True
    for name in sorted(carry_axes):
        direction, reference = carry_axes[name]
        reset_direction, value = reset_axes[name]
        if direction != reset_direction:
            raise RuntimeError("R-227 metric direction differs")
        tolerance = 1.0e-12 * max(1.0, abs(reference))
        axis_pass = (
            value + tolerance >= reference
            if direction == "max"
            else value <= reference + tolerance
        )
        passed &= axis_pass
        comparisons.append({
            "axis": name, "direction": direction, "carry": reference,
            "reset": value, "tolerance": tolerance, "pass": axis_pass,
        })
    return passed, comparisons


def _phase_coordinates_usable(
    subset: tuple[LanePlan, ...],
    phase_rows: PhaseEvidenceAccess,
) -> bool:
    return all(
        phase_rows[plan.observations[index].identity].channel_usable[plan.channel]
        for plan in subset for index in plan.knot_indexes
    )


def exact_s11_bound(frame_count: int, channels: int) -> int:
    return sum(
        math.ceil(frame_count / hop) + 1 for hop in (128, 512, 2048)
    ) * (channels + 1) * 48


def evaluate_phase_shadow(
    samples: np.ndarray,
    sample_rate: int,
    *,
    decoder: NativeMain0Decoder,
    coefficients_per_frame: int,
    half_window: int,
    band_count: int,
    categories: tuple[str, ...],
    commit_eligibility: Callable[[dict[str, object]], str],
) -> tuple[dict[str, object], dict[str, bytes], dict[str, np.ndarray]]:
    """Evaluate the complete paired hypothesis on one already validated PCM."""

    direct = encode_lapped_stream(
        samples, sample_rate,
        coefficients_per_frame=coefficients_per_frame,
        half_window=half_window,
        band_count=band_count,
        entropy_backend="bounded",
        transform_backend="fixed",
        density_backend="adaptive",
        selection_backend="energy",
        frame_whitening=0.0,
        band_whitening=0.0,
        native_analyzer=decoder,
        native_decoder=decoder,
    )
    direct_decoded = decoder.decode_lapped(direct.payload)
    if direct_decoded.sample_rate != sample_rate or not np.array_equal(
        direct_decoded.samples, direct.reconstruction
    ):
        raise RuntimeError("R-227 direct native decode differs")
    upper_bound = exact_s11_bound(samples.shape[0], samples.shape[1])
    if upper_bound <= OBSERVATION_LIMIT:
        raise RuntimeError("R-227 exact S11 unexpectedly fits frozen bound")

    production_s11 = {
        "invoked": True,
        "expected_error": "R-186 observation manifest exceeds its hard bound",
        "output_payload_present": False,
    }
    try:
        observe_complex_partials(
            samples, sample_rate, manifest=ComplexPartialAnalyzerManifest()
        )
    except ValueError as error:
        if str(error) != production_s11["expected_error"]:
            raise RuntimeError("R-227 production S11 rejection reason drift") from error
        production_s11["actual_error"] = str(error)
    else:
        raise RuntimeError("R-227 production S11 unexpectedly emitted an observation set")

    direct_metrics = compute_metrics(samples, direct.reconstruction, sample_rate, categories)
    direct_delta = samples.astype(np.int64) - direct.reconstruction.astype(np.int64)
    direct_sse = int(np.sum(direct_delta * direct_delta, dtype=np.int64))
    direct_ledger = {
        "complete_bytes": len(direct.payload),
        "predictor_bytes": 0,
        "residual_bytes": len(direct.payload),
        "container_wrapper_bytes": 0,
    }

    free_rows, phase_vault, observation_report = observe_tiled_phase_shadow(
        samples, sample_rate
    )
    tracks = track_phase_free(free_rows)
    lanes = plan_phase_free_lanes(tracks, samples, sample_rate)
    subsets = enumerate_subsets(lanes)
    for subset in subsets:
        if sum(plan.placement_count for plan in subset) > 4096:
            raise RuntimeError("R-227 sealed subset exceeds the MFT1 placement cap")
    sealed_digest = eligibility_digest(free_rows, tracks, lanes, subsets)
    eligibility_manifest = {
        "schema": "resonith-r227-phase-free-eligibility-1",
        "phase_accessed": False,
        "phase_free_observation_sha256": phase_free_digest(free_rows),
        "eligibility_sha256": sealed_digest,
        "phase_free_observation_count": len(free_rows),
        "track_count": len(tracks),
        "lane_count": len(lanes),
        "subset_count": len(subsets),
    }
    phase_rows = seal_phase_evidence(
        phase_vault, eligibility_manifest, commit_eligibility
    )
    committed_eligibility_sha256 = phase_rows.eligibility_manifest_sha256
    report: dict[str, object] = {
        "schema": "resonith-r227-phase-poisoned-shadow-item-1",
        "direct_truth_bytes": len(direct.payload),
        "direct_truth_pcm_sha256": pcm_sha256(direct.reconstruction),
        "direct_truth": {
            **direct_ledger,
            "sse": direct_sse,
            "payload_sha256": sha256(direct.payload).hexdigest(),
            "decoded_pcm_sha256": pcm_sha256(direct.reconstruction),
            "metrics": direct_metrics,
            "directional_context": "independent lapped Truth baseline; no predictor",
        },
        "exact_s11_status": "NOT_EXECUTABLE_UNDER_FROZEN_BOUND",
        "exact_s11_observation_upper_bound": upper_bound,
        "production_s11_rejection": production_s11,
        "observation": observation_report,
        "phase_free_observation_count": len(free_rows),
        "track_count": len(tracks),
        "lane_count": len(lanes),
        "subset_count": len(subsets),
        "eligibility_sha256": sealed_digest,
        "eligibility_manifest_sha256": committed_eligibility_sha256,
        "eligible": bool(subsets),
    }
    payloads = {"direct": direct.payload}
    decoded = {"direct": direct.reconstruction}
    if not subsets:
        report["status"] = "INELIGIBLE_NO_PHASE_FREE_LANE"
        report["admission_pass"] = False
        return report, payloads, decoded

    carry_results = []
    for subset in subsets:
        lowered = tuple(
            _lower_lane(
                plan, phase_rows, sample_rate, False
            ) for plan in subset
        )
        result = _evaluate_subset(
            samples, sample_rate, lowered, native_decoder=decoder,
            coefficients_per_frame=coefficients_per_frame,
            half_window=half_window, band_count=band_count,
        )
        carry_results.append((_subset_id(subset), subset, lowered, result))
    subset_id, selected_subset, selected_carry_lanes, carry = min(
        carry_results,
        key=lambda item: (
            len(item[3].selected_payload), item[3].sse, item[0],
            0 if item[3].selected_transport == "cbf1" else 1,
        ),
    )
    if not _phase_coordinates_usable(
        selected_subset, phase_rows
    ):
        report.update({
            "status": "INELIGIBLE_SELECTED_PHASE_UNUSABLE",
            "selected_subset_id": [list(value) for value in subset_id],
            "admission_pass": False,
        })
        return report, payloads, decoded

    reset_lanes = tuple(
        _lower_lane(plan, phase_rows, sample_rate, True)
        for plan in selected_subset
    )
    reset = _evaluate_subset(
        samples, sample_rate, reset_lanes, native_decoder=decoder,
        coefficients_per_frame=coefficients_per_frame,
        half_window=half_window, band_count=band_count,
    )
    transport = carry.selected_transport
    carry_payload = _fixed_transport_payload(carry, transport)
    reset_payload = _fixed_transport_payload(reset, transport)
    reset_rate, reset_native = decode_causal_basis_truth_candidate(
        reset_payload, native_decoder=decoder
    )
    if reset_rate != sample_rate or not np.array_equal(
        reset_native, reset.reconstruction
    ):
        raise RuntimeError("R-227 fixed reset transport native decode differs")
    carry_ledger = _byte_ledger(carry, transport)
    reset_ledger = _byte_ledger(reset, transport)
    absolute_position_field_bytes = 4 * sum(
        plan.placement_count for plan in selected_subset
    )
    retained_knot_reset_count = sum(
        len(plan.knot_indexes) - 1 for plan in selected_subset
    )
    phase_reset_events = _phase_reset_events(
        selected_subset, selected_carry_lanes, reset_lanes
    )
    phase_innovation_detected = any(
        event["delta_turn_u32"] != 0 for event in phase_reset_events
    )
    carry_metrics = compute_metrics(
        samples, carry.reconstruction, sample_rate, categories
    )
    reset_metrics = compute_metrics(
        samples, reset.reconstruction, sample_rate, categories
    )
    quality_pass, quality_axes_report = _quality_nonregression(
        carry_metrics, reset_metrics
    )
    source_delay = _stereo_delay(samples, sample_rate)
    carry_delay = _stereo_delay(carry.reconstruction, sample_rate)
    reset_delay = _stereo_delay(reset.reconstruction, sample_rate)
    if (source_delay is None) != (carry_delay is None) or (
        (source_delay is None) != (reset_delay is None)
    ):
        raise RuntimeError("R-227 stereo-delay applicability differs")
    delay_pass = True
    delay_report = None
    if source_delay is not None:
        carry_error = abs(carry_delay - source_delay)
        reset_error = abs(reset_delay - source_delay)
        tolerance = 1.0e-12 * max(1.0, abs(carry_error))
        delay_pass = reset_error <= carry_error + tolerance
        delay_report = {
            "source_lag": source_delay,
            "carry_lag": carry_delay,
            "reset_lag": reset_delay,
            "carry_error_samples": carry_error,
            "reset_error_samples": reset_error,
            "tolerance": tolerance,
            "pass": delay_pass,
        }
    residual_pass = reset.residual_bytes * 10 <= carry.residual_bytes * 9
    residual_direction_pass = reset.residual_bytes < carry.residual_bytes
    complete_pass = len(reset_payload) <= len(carry_payload)
    clipping_pass = reset.residual_clip_count <= carry.residual_clip_count
    admission_pass = bool(
        residual_pass and complete_pass and clipping_pass
        and quality_pass and delay_pass
    )
    report.update({
        "status": "PASS" if admission_pass else "FAIL",
        "selected_subset_id": [list(value) for value in subset_id],
        "selected_transport": transport,
        "carry": {
            **carry_ledger,
            "sse": carry.sse,
            "residual_clip_count": carry.residual_clip_count,
            "payload_sha256": sha256(carry_payload).hexdigest(),
            "decoded_pcm_sha256": pcm_sha256(carry.reconstruction),
            "metrics": carry_metrics,
            "phase_economy_context": {
                "absolute_position_field_bytes": absolute_position_field_bytes,
                "retained_knot_reset_count": 0,
            },
        },
        "reset": {
            **reset_ledger,
            "sse": reset.sse,
            "residual_clip_count": reset.residual_clip_count,
            "payload_sha256": sha256(reset_payload).hexdigest(),
            "decoded_pcm_sha256": pcm_sha256(reset.reconstruction),
            "metrics": reset_metrics,
            "phase_economy_context": {
                "absolute_position_field_bytes": absolute_position_field_bytes,
                "retained_knot_reset_count": retained_knot_reset_count,
            },
        },
        "quality_axes": quality_axes_report,
        "stereo_delay": delay_report,
        "residual_reduction_pass": residual_pass,
        "residual_direction_pass": residual_direction_pass,
        "phase_innovation_detected": phase_innovation_detected,
        "phase_reset_events": phase_reset_events,
        "complete_bytes_pass": complete_pass,
        "clipping_pass": clipping_pass,
        "quality_pass": quality_pass,
        "delay_pass": delay_pass,
        "direct_directional_context": {
            "carry_complete_bytes_minus_direct": (
                len(carry_payload) - len(direct.payload)
            ),
            "reset_complete_bytes_minus_direct": (
                len(reset_payload) - len(direct.payload)
            ),
            "carry_sse_minus_direct": carry.sse - direct_sse,
            "reset_sse_minus_direct": reset.sse - direct_sse,
        },
        "admission_pass": admission_pass,
    })
    payloads.update({"carry": carry_payload, "reset": reset_payload})
    decoded.update({
        "carry": carry.reconstruction,
        "reset": reset.reconstruction,
    })
    return report, payloads, decoded


def validate_source_row(row: dict[str, object]) -> tuple[int, np.ndarray]:
    expected_backends = {
        "entropy_backend": "bounded",
        "transform_backend": "fixed",
        "density_backend": "adaptive",
        "selection_backend": "energy",
        "frame_whitening": 0.0,
        "band_whitening": 0.0,
    }
    if any(row.get(name) != value for name, value in expected_backends.items()):
        raise RuntimeError("R-227 Truth configuration drift")
    path = Path(str(row["path"]))
    if path.stat().st_size != int(row["file_bytes"]):
        raise RuntimeError("R-227 source byte count drift")
    if sha256_file(path) != row["file_sha256"]:
        raise RuntimeError("R-227 source file hash drift")
    rate, samples = read_wav(path)
    if (
        rate != int(row["sample_rate"])
        or samples.shape != (int(row["frames"]), int(row["channels"]))
        or pcm_sha256(samples) != row["pcm16le_sha256"]
    ):
        raise RuntimeError("R-227 source PCM identity drift")
    return rate, samples


def validate_synthetic_control(
    manifest: dict[str, object],
    row: dict[str, object],
    samples: np.ndarray,
    decoder: NativeMain0Decoder,
    phase_reset_events: list[dict[str, int]],
) -> dict[str, object]:
    """Bind the known 600-placement control and classify only scheduled jumps."""

    program = dict(manifest["synthetic_program"])
    path = SOURCE_MANIFEST.parent / "synthetic-bounded-vibrato-600s.mft1"
    payload = path.read_bytes()
    if (
        len(payload) != int(program["mft1_bytes"])
        or sha256(payload).hexdigest() != program["mft1_sha256"]
    ):
        raise RuntimeError("R-227 synthetic MFT1 identity drift")
    info = parse_maf_typed(payload)
    instances = info.basis_warp_instances
    segment_frames = int(program["segment_frames"])
    segment_count = int(program["segments"])
    basis_length = int(program["basis_length"])
    if (
        info.sample_rate != int(program["sample_rate"])
        or info.total_frames != samples.shape[0]
        or info.output_channels != samples.shape[1]
        or len(info.bases) != 1
        or len(info.bases[0].samples) != basis_length
        or len(instances) != segment_count
        or segment_count != 600
    ):
        raise RuntimeError("R-227 synthetic MFT1 geometry drift")
    basis_bytes = np.asarray(info.bases[0].samples, dtype="<i2").tobytes()
    if sha256(basis_bytes).hexdigest() != program["basis_pcm16le_sha256"]:
        raise RuntimeError("R-227 synthetic Basis identity drift")

    period = basis_length << 16
    prior_position = 0
    for index, instance in enumerate(instances):
        if index == 0:
            expected_position = 0
        else:
            expected_position = prior_position
            if index % 30 == 0:
                expected_position = (expected_position + period // 8) % period
        frequency_law = (
            program["frequency_hz_even"]
            if index % 2 == 0 else program["frequency_hz_odd"]
        )
        expected_start_step = _frequency_step_q16(
            float(frequency_law[0]), info.sample_rate, basis_length
        )
        expected_end_step = _frequency_step_q16(
            float(frequency_law[1]), info.sample_rate, basis_length
        )
        if (
            instance.start != index * segment_frames
            or instance.sample_count != segment_frames
            or instance.source_position_q16 != expected_position
            or instance.source_step_q16 != expected_start_step
            or instance.end_source_step_q16 != expected_end_step
            or instance.gain_q15 != int(program["gain_q15"])
            or not instance.circular
        ):
            raise RuntimeError("R-227 synthetic periodic program drift")
        prior_position = _one_past_position(
            instance.source_position_q16,
            instance.source_step_q16,
            instance.end_source_step_q16,
            instance.sample_count,
            basis_length,
        )

    native = decoder.decode_maf_typed(payload)
    native_samples = native.samples.reshape(samples.shape)
    if (
        native.sample_rate != int(row["sample_rate"])
        or not np.array_equal(native_samples, samples)
        or pcm_sha256(native_samples) != row["pcm16le_sha256"]
    ):
        raise RuntimeError("R-227 synthetic native decode identity drift")

    scheduled = tuple(index * segment_frames for index in range(30, 600, 30))
    crossings = []
    detected = []
    one_eighth_turn = 1 << 29
    for event in phase_reset_events:
        crossed = [
            onset for onset in scheduled
            if event["lane_birth_sample"] < onset <= event["start_sample"]
        ]
        if not crossed:
            continue
        expected_turn = (len(crossed) * one_eighth_turn) & 0xFFFFFFFF
        crossings.extend(crossed)
        if _turn_distance(event["delta_turn_u32"], expected_turn) < _turn_distance(
            event["delta_turn_u32"], 0
        ):
            detected.extend(crossed)
    unique_crossings = sorted(set(crossings))
    unique_detected = sorted(set(detected))
    detection_pass = bool(unique_crossings) and unique_detected == unique_crossings
    return {
        "mft1_path": str(path),
        "mft1_bytes": len(payload),
        "mft1_sha256": sha256(payload).hexdigest(),
        "native_pcm16le_sha256": pcm_sha256(native_samples),
        "schedule": "one-eighth cycle before every thirtieth placement except zero",
        "scheduled_innovation_count": len(scheduled),
        "selected_lane_crossing_samples": unique_crossings,
        "detected_innovation_samples": unique_detected,
        "known_phase_innovation_detection_pass": detection_pass,
    }


def run_worker(
    manifest_path: Path,
    row_index: int,
    output: Path,
    core: Path,
    expected_runner_sha256: str,
    expected_commit: str,
) -> None:
    if sha256_file(manifest_path) != SOURCE_MANIFEST_SHA256:
        raise RuntimeError("R-227 source manifest drift")
    authorities_before = validate_authorities(
        core,
        expected_runner_sha256=expected_runner_sha256,
        expected_commit=expected_commit,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["wav_sources"][row_index]
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    started = time.perf_counter()
    rate, samples = validate_source_row(row)
    decoder = NativeMain0Decoder(core)
    categories = ("speech",) if row["id"] == "librispeech-long" else ("music",)
    def commit_eligibility(value: dict[str, object]) -> str:
        path = output / "eligibility.json"
        write_json_atomic(path, value)
        return sha256_file(path)

    report, payloads, decoded = evaluate_phase_shadow(
        samples, rate, decoder=decoder,
        coefficients_per_frame=int(row["coefficients_per_frame"]),
        half_window=int(row["half_window"]),
        band_count=int(row["band_count"]),
        categories=categories,
        commit_eligibility=commit_eligibility,
    )
    if row["id"] == "synthetic-bounded-vibrato":
        synthetic_control = validate_synthetic_control(
            manifest, row, samples, decoder,
            list(report.get("phase_reset_events", [])),
        )
        report["synthetic_control"] = synthetic_control
        report["known_phase_innovation_detection_pass"] = synthetic_control[
            "known_phase_innovation_detection_pass"
        ]
    else:
        report["known_phase_innovation_detection_pass"] = None
    for name, payload in payloads.items():
        write_atomic(output / f"{name}.resonith", payload)
    for name, pcm in decoded.items():
        write_atomic(output / f"{name}-decoded.wav", wav_bytes(rate, pcm))
    report.update({
        "item_id": row["id"],
        "source_file_sha256": row["file_sha256"],
        "source_pcm16le_sha256": row["pcm16le_sha256"],
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "native_core_sha256": NATIVE_CORE_SHA256,
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "implementation_commit": expected_commit,
        "eligibility_manifest_sha256": sha256_file(output / "eligibility.json"),
        "wall_seconds": time.perf_counter() - started,
        "accelerator": {"used": False, "device": "CPU"},
    })
    authorities_after = validate_authorities(
        core,
        expected_runner_sha256=expected_runner_sha256,
        expected_commit=expected_commit,
    )
    if authorities_after != authorities_before:
        raise RuntimeError("R-227 authority changed during worker execution")
    report["authorities"] = authorities_before
    write_json_atomic(output / "receipt.json", report)


def run_controller(
    manifest_path: Path,
    output: Path,
    core: Path,
    expected_runner_sha256: str,
    expected_commit: str,
) -> None:
    if output.exists():
        raise FileExistsError(output)
    if sha256_file(manifest_path) != SOURCE_MANIFEST_SHA256:
        raise RuntimeError("R-227 source manifest drift")
    authorities_before = validate_authorities(
        core,
        expected_runner_sha256=expected_runner_sha256,
        expected_commit=expected_commit,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True)
    index = {
        "schema": "resonith-r227-phase-poisoned-shadow-run-1",
        "status": "RUNNING",
        "items": [],
    }
    write_json_atomic(output / "index.json", index)
    for row_index, row in enumerate(manifest["wav_sources"]):
        staging = output / f".{row['id']}.staging"
        final = output / str(row["id"])
        timeout = min(8000.0, max(1800.0, 12.0 * float(row["duration_seconds"])))
        resources = run_bounded(
            [
                sys.executable, str(Path(__file__).resolve()), "--worker",
                "--manifest", str(manifest_path), "--row-index", str(row_index),
                "--output", str(staging), "--core", str(core),
                "--expected-runner-sha256", expected_runner_sha256,
                "--expected-commit", expected_commit,
            ],
            timeout,
            RSS_LIMIT,
            REPOSITORY,
            disk_root=staging,
            disk_limit=ITEM_DISK_LIMIT,
        )
        receipt_path = staging / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="ascii"))
        retained = _tree_bytes(staging)
        resources["disk_high_water_bytes"] = max(
            int(resources["disk_high_water_bytes"]), retained
        )
        receipt["process_resources"] = resources
        # The receipt accounts for itself. Iterate to the fixed digit width so
        # retained_item_bytes is the complete staged tree, not a pre-write guess.
        for _ in range(4):
            receipt["retained_item_bytes"] = retained
            write_json_atomic(receipt_path, receipt)
            updated = _tree_bytes(staging)
            if updated == retained:
                break
            retained = updated
        else:
            raise RuntimeError("R-227 retained item byte count did not converge")
        if retained > ITEM_DISK_LIMIT:
            raise OSError("R-227 finalized staging item exceeds disk ceiling")
        resources["disk_high_water_bytes"] = max(
            int(resources["disk_high_water_bytes"]), retained
        )
        receipt["process_resources"] = resources
        receipt["retained_item_bytes"] = retained
        write_json_atomic(receipt_path, receipt)
        final_retained = _tree_bytes(staging)
        if final_retained != retained:
            receipt["retained_item_bytes"] = final_retained
            write_json_atomic(receipt_path, receipt)
            if _tree_bytes(staging) != final_retained:
                raise RuntimeError("R-227 final retained item ledger is unstable")
        os.replace(staging, final)
        receipt_path = final / "receipt.json"
        index["items"].append({
            "item_id": row["id"],
            "receipt_sha256": sha256_file(receipt_path),
            "status": receipt["status"],
            "admission_pass": receipt["admission_pass"],
            "residual_direction_pass": receipt.get("residual_direction_pass", False),
            "phase_innovation_detected": receipt.get("phase_innovation_detected", False),
            "known_phase_innovation_detection_pass": receipt.get(
                "known_phase_innovation_detection_pass"
            ),
            "resources": resources,
        })
        write_json_atomic(output / "index.json", index)
        if sum(path.stat().st_size for path in output.rglob("*") if path.is_file()) > RUN_DISK_LIMIT:
            raise OSError("R-227 retained run exceeds disk ceiling")
    real = index["items"][:3]
    synthetic = index["items"][3]
    index["status"] = "PASS" if (
        all(row["admission_pass"] for row in real)
        and synthetic["residual_direction_pass"]
        and synthetic["known_phase_innovation_detection_pass"] is True
    ) else "FAIL"
    authorities_after = validate_authorities(
        core,
        expected_runner_sha256=expected_runner_sha256,
        expected_commit=expected_commit,
    )
    if authorities_after != authorities_before:
        raise RuntimeError("R-227 authority changed during controller execution")
    index["runner_sha256"] = expected_runner_sha256
    index["implementation_commit"] = expected_commit
    index["authorities"] = authorities_before
    index["source_manifest_sha256"] = SOURCE_MANIFEST_SHA256
    index["native_core_sha256"] = NATIVE_CORE_SHA256
    write_json_atomic(output / "index.json", index)
    if _tree_bytes(output) > RUN_DISK_LIMIT:
        raise OSError("R-227 finalized run exceeds disk ceiling")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--manifest", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--row-index", type=int)
    parser.add_argument("--expected-runner-sha256", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--core", type=Path,
        default=REPOSITORY / "build/cpp23-clang22-ninja/libresonith_core_shared.dll",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.worker:
        if arguments.row_index is None:
            raise ValueError("R-227 worker requires --row-index")
        run_worker(
            arguments.manifest, arguments.row_index, arguments.output,
            arguments.core,
            arguments.expected_runner_sha256,
            arguments.expected_commit,
        )
    else:
        if arguments.row_index is not None:
            raise ValueError("R-227 controller rejects --row-index")
        run_controller(
            arguments.manifest, arguments.output, arguments.core,
            arguments.expected_runner_sha256, arguments.expected_commit,
        )


if __name__ == "__main__":
    main()
