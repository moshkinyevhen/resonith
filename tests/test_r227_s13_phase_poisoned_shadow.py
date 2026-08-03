from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np
import pytest

from experiments.r227_s13_phase_poisoned_shadow import (
    PhaseEvidence,
    PhaseEvidenceVault,
    PhaseFreeObservation,
    LanePlan,
    SOURCE_MANIFEST,
    _edge_score,
    _byte_ledger,
    _lane_energy_numerator,
    _lower_lane,
    _phase_coordinates_usable,
    _phase_turn_u32,
    _one_past_position,
    _stereo_delay,
    _validate_tile_centers,
    eligibility_digest,
    enumerate_subsets,
    observe_tiled_phase_shadow,
    phase_free_digest,
    plan_phase_free_lanes,
    run_bounded,
    run_controller,
    seal_phase_evidence,
    sha256_file,
    tile_boundaries,
    track_phase_free,
    validate_source_row,
    validate_synthetic_control,
    write_json_atomic,
)
from reference.maf_p0.complex_partial_analyzer import (
    ComplexPartialAnalyzerManifest,
    PartialResolution,
    observe_complex_partials,
)
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.persistent_partial_field import _evaluate_subset


CORE = os.environ.get("RESONITH_NATIVE_CORE")


def _seal(
    vault: PhaseEvidenceVault,
    eligibility_sha256: str,
    path: Path,
):
    manifest = {
        "schema": "resonith-r227-phase-free-eligibility-test-1",
        "eligibility_sha256": eligibility_sha256,
        "phase_accessed": False,
    }

    def commit(value: dict[str, object]) -> str:
        write_json_atomic(path, value)
        return sha256_file(path)

    return seal_phase_evidence(vault, manifest, commit)


def _row(
    ordinal: int,
    center: int,
    *,
    tile: int = 0,
    tile_end: int = 200_000,
    frequency_q20: int = 440 << 20,
    gain: int = 12000,
    hop: int = 2048,
) -> PhaseFreeObservation:
    return PhaseFreeObservation(
        identity=(8192, hop, center // hop, ordinal % 48),
        ordinal=ordinal,
        tile_id=tile,
        tile_end=tile_end,
        center_sample=center,
        hop_samples=hop,
        frequency_q20=frequency_q20,
        frequency_uncertainty_q20=1 << 18,
        aggregate_gain_q15=gain,
        gain_uncertainty_q15=2,
        channel_gains_q15=(gain,),
        amplitude_lower_confidence_q15=max(0, gain - 4),
        snr_db_q8=40 * 256,
        snr_known=True,
        peak_prominence_db_q8=30 * 256,
        locally_resolvable=True,
        ambiguity_identity=(0, -1, center // hop, ordinal % 48),
        provenance=(0, -1, center // hop, ordinal % 48),
    )


def test_tile_ownership_and_phase_poison_digest(tmp_path: Path) -> None:
    boundaries = tile_boundaries(48000, 19_237_088)
    assert boundaries[:3] == (0, 575488, 1150976)
    assert boundaries[-1] == 19_237_088
    assert all(value % 2048 == 0 for value in boundaries[:-1])

    sample_rate = 8000
    time = np.arange(2 * sample_rate, dtype=np.float64)
    positive = np.rint(
        9000.0 * np.cos(2.0 * np.pi * 437.5 * time / sample_rate)
    ).astype(np.int16)[:, None]
    negative = (-positive).astype(np.int16)
    rows, vault_a, _ = observe_tiled_phase_shadow(positive, sample_rate)
    poisoned_rows, vault_b, _ = observe_tiled_phase_shadow(negative, sample_rate)
    assert rows and poisoned_rows
    with pytest.raises(RuntimeError, match="before eligibility seal"):
        vault_a._read(rows[0].identity, object())
    assert phase_free_digest(rows) == phase_free_digest(poisoned_rows)
    tracks = track_phase_free(rows)
    poisoned_tracks = track_phase_free(poisoned_rows)
    lanes = plan_phase_free_lanes(tracks, positive, sample_rate)
    poisoned_lanes = plan_phase_free_lanes(poisoned_tracks, negative, sample_rate)
    subsets = enumerate_subsets(lanes)
    poisoned_subsets = enumerate_subsets(poisoned_lanes)
    digest = eligibility_digest(rows, tracks, lanes, subsets)
    poisoned_digest = eligibility_digest(
        poisoned_rows, poisoned_tracks, poisoned_lanes, poisoned_subsets
    )
    assert digest == poisoned_digest
    phases_a = _seal(vault_a, digest, tmp_path / "eligibility-a.json")
    phases_b = _seal(vault_b, poisoned_digest, tmp_path / "eligibility-b.json")
    assert phases_a.evidence_sha256 != phases_b.evidence_sha256
    assert eligibility_digest(rows, tracks, lanes, subsets) == eligibility_digest(
        poisoned_rows, poisoned_tracks, poisoned_lanes, poisoned_subsets
    )
    assert tuple(len(track.observations) for track in tracks) == tuple(
        len(track.observations) for track in poisoned_tracks
    )


def test_tile_center_completeness_is_terminal() -> None:
    _validate_tile_centers([0, 512, 1024], [0, 512, 1024], 512)
    with pytest.raises(RuntimeError, match="duplicate"):
        _validate_tile_centers([0, 512, 512], [0, 512], 512)
    with pytest.raises(RuntimeError, match="missing"):
        _validate_tile_centers([0, 1024], [0, 512, 1024], 512)
    with pytest.raises(RuntimeError, match="non-hop"):
        _validate_tile_centers([0, 513], [0, 512], 512)


def test_edge_arithmetic_mutation_and_cross_tile_stop() -> None:
    first = _row(0, 0)
    second = _row(1, 2048, frequency_q20=(441 << 20), gain=12005)
    score = _edge_score(first, second, 7)
    assert score is not None
    assert score[2:] == (7, second.identity)
    assert _edge_score(
        first,
        _row(2, 2048, frequency_q20=500 << 20),
        7,
    ) is None

    different_tile = _row(3, 4096, tile=1)
    tracks = track_phase_free((first, second, different_tile))
    assert sorted(len(track.observations) for track in tracks) == [1, 2]


def test_phase_free_energy_knots_and_subset_identity() -> None:
    sample_rate = 48000
    rows = tuple(_row(index, index * 2048) for index in range(26))
    source_time = np.arange(60_000, dtype=np.float64)
    source = np.rint(
        12000.0 * np.cos(2.0 * np.pi * 440.0 * source_time / sample_rate)
    ).astype(np.int16)[:, None]
    energy = _lane_energy_numerator(rows, 0)
    assert energy > 0
    tracks = track_phase_free(rows)
    lanes = plan_phase_free_lanes(tracks, source, sample_rate)
    assert lanes
    assert lanes[0].track_id == 0
    assert lanes[0].placement_count >= 2
    subsets = enumerate_subsets(lanes[:2])
    assert len(subsets) in {1, 3}
    assert eligibility_digest(rows, tracks, lanes, subsets)


def test_reset_changes_only_positions_and_propagates_splits(tmp_path: Path) -> None:
    sample_rate = 48000
    centers = tuple(index * 4096 for index in range(41))
    rows = tuple(_row(index, center, tile_end=centers[-1] + 4096)
                 for index, center in enumerate(centers))
    plan = LanePlan(
        track_id=4,
        channel=0,
        basis_length=256,
        observations=rows,
        knot_indexes=(0, 20, 40),
        placement_count=5,
        fit_error_q20=0,
        estimated_energy_numerator=_lane_energy_numerator(rows, 0),
    )
    evidence = {
        row.identity: PhaseEvidence(
            (_phase_turn_u32(0.0 if index != 20 else 1.25),),
            (0.01,), (True,)
        )
        for index, row in enumerate(rows)
    }
    phase = _seal(
        PhaseEvidenceVault(evidence), "a" * 64,
        tmp_path / "eligibility-reset.json",
    )
    with pytest.raises(RuntimeError, match="before eligibility seal"):
        PhaseEvidenceVault(evidence)._read(rows[0].identity, object())
    carry = _lower_lane(plan, phase, sample_rate, False)
    reset = _lower_lane(plan, phase, sample_rate, True)
    assert len(carry.instances) == len(reset.instances) == plan.placement_count
    differing_positions = 0
    for left, right in zip(carry.instances, reset.instances):
        assert left.start == right.start
        assert left.sample_count == right.sample_count
        assert left.source_step_q16 == right.source_step_q16
        assert left.end_source_step_q16 == right.end_source_step_q16
        assert left.gain_q15 == right.gain_q15
        assert left.end_gain_q15 == right.end_gain_q15
        differing_positions += left.source_position_q16 != right.source_position_q16
    assert differing_positions >= 2
    retained_starts = {rows[index].center_sample for index in plan.knot_indexes}
    for lane in (carry, reset):
        for previous, current in zip(lane.instances, lane.instances[1:]):
            if current.start in retained_starts:
                continue
            expected = _one_past_position(
                previous.source_position_q16,
                previous.source_step_q16,
                previous.end_source_step_q16 or previous.source_step_q16,
                previous.sample_count,
                plan.basis_length,
            )
            assert current.source_position_q16 == expected
    unusable = dict(evidence)
    unusable[rows[20].identity] = PhaseEvidence(
        evidence[rows[20].identity].channel_phase_turn_u32,
        (3.0,), (False,),
    )
    unusable_access = _seal(
        PhaseEvidenceVault(unusable), "d" * 64,
        tmp_path / "eligibility-unusable.json",
    )
    assert not _phase_coordinates_usable((plan,), unusable_access)


def test_stereo_delay_law_and_zero_energy_applicability() -> None:
    source = np.zeros((4096, 2), dtype=np.int16)
    source[100:200, 0] = 1000
    source[107:207, 1] = 1000
    assert _stereo_delay(source, 8000) == 7
    assert _stereo_delay(np.zeros((100, 2), dtype=np.int16), 8000) is None
    assert _stereo_delay(source[:, :1], 8000) is None


def test_tiled_interior_observation_matches_same_resolution_monolith() -> None:
    sample_rate = 8000
    frames = 13 * sample_rate
    time = np.arange(frames, dtype=np.float64)
    samples = np.rint(
        9000.0 * np.cos(2.0 * np.pi * 437.25 * time / sample_rate)
    ).astype(np.int16)[:, None]
    tiled, _, report = observe_tiled_phase_shadow(samples, sample_rate)
    assert len(report["boundaries"]) == 3
    assert report["tiles"][0]["core"][0] == 0
    assert report["tiles"][-1]["core"][1] == frames
    for row in tiled:
        core_start, core_end = report["tiles"][row.tile_id]["core"]
        assert core_start <= row.center_sample < core_end
    manifest = ComplexPartialAnalyzerManifest(
        resolutions=(PartialResolution(2048, 512),),
    )
    monolithic = observe_complex_partials(samples, sample_rate, manifest=manifest)
    target_center = report["boundaries"][1]
    tiled_rows = [row for row in tiled if row.center_sample == target_center]
    mono_rows = [
        row for row in monolithic.observations
        if row.detector_channel == -1
        and row.center_sample == target_center
        and row.locally_resolvable
        and row.amplitude_lower_confidence > 0.0
    ]
    assert tiled_rows and len(tiled_rows) == len(mono_rows)
    assert [row.frequency_q20 for row in tiled_rows] == [
        int(round(row.frequency_hz * (1 << 20))) for row in mono_rows
    ]


@pytest.mark.skipif(CORE is None, reason="set RESONITH_NATIVE_CORE")
def test_actual_existing_syntax_transport_and_complete_native_decode(
    tmp_path: Path,
) -> None:
    sample_rate = 8000
    frames = 12_000
    time = np.arange(frames, dtype=np.float64)
    samples = np.rint(
        10000.0 * np.cos(2.0 * np.pi * 440.0 * time / sample_rate)
    ).astype(np.int16)[:, None]
    rows = tuple(
        _row(
            index,
            index * 512,
            tile_end=frames,
            frequency_q20=440 << 20,
            gain=10000,
            hop=512,
        )
        for index in range(22)
    )
    plan = LanePlan(
        track_id=0,
        channel=0,
        basis_length=128,
        observations=rows,
        knot_indexes=(0, 21),
        placement_count=2,
        fit_error_q20=0,
        estimated_energy_numerator=_lane_energy_numerator(rows, 0),
    )
    evidence = {
        row.identity: PhaseEvidence((_phase_turn_u32(0.0),), (0.01,), (True,))
        for row in rows
    }
    phase = _seal(
        PhaseEvidenceVault(evidence), "b" * 64,
        tmp_path / "eligibility-native.json",
    )
    lane = _lower_lane(plan, phase, sample_rate, False)
    decoder = NativeMain0Decoder(Path(CORE))
    result = _evaluate_subset(
        samples,
        sample_rate,
        (lane,),
        native_decoder=decoder,
        coefficients_per_frame=64,
        half_window=128,
        band_count=8,
    )
    assert result.predictor_transport_pcm_identity
    assert result.complete_decode_identity
    assert result.s11_record_language_only
    assert result.selected_payload
    ledger = _byte_ledger(result, result.selected_transport)
    assert ledger["complete_bytes"] == (
        ledger["predictor_bytes"] + ledger["residual_bytes"]
        + ledger["container_wrapper_bytes"]
    )


def test_production_s11_bound_rejects_before_output() -> None:
    samples = np.zeros((4_700_000, 1), dtype=np.int16)
    output = None
    with pytest.raises(
        ValueError, match="R-186 observation manifest exceeds its hard bound"
    ):
        output = observe_complex_partials(samples, 48000)
    assert output is None


def test_bounded_runner_fails_closed_on_resource_authority(monkeypatch, tmp_path: Path) -> None:
    import experiments.r227_s13_phase_poisoned_shadow as module

    monkeypatch.setattr(module, "_child_resources", lambda process: (0, 0.0))
    with pytest.raises(RuntimeError, match="resource authority"):
        run_bounded(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            5.0, 1 << 30, Path.cwd(), disk_root=tmp_path,
            disk_limit=1 << 20,
        )


def test_bounded_runner_timeout_is_terminal(monkeypatch, tmp_path: Path) -> None:
    import experiments.r227_s13_phase_poisoned_shadow as module

    monkeypatch.setattr(module, "_child_resources", lambda process: (4096, 0.0))
    with pytest.raises(TimeoutError):
        run_bounded(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            0.05, 1 << 30, Path.cwd(), disk_root=tmp_path,
            disk_limit=1 << 20,
        )


@pytest.mark.parametrize("failure", ["memory", "disk"])
def test_bounded_runner_memory_and_disk_are_terminal(
    monkeypatch, tmp_path: Path, failure: str
) -> None:
    import experiments.r227_s13_phase_poisoned_shadow as module

    monkeypatch.setattr(module, "_child_resources", lambda process: (8192, 0.0))
    if failure == "disk":
        (tmp_path / "oversize.bin").write_bytes(b"x" * 8192)
    exception = MemoryError if failure == "memory" else OSError
    with pytest.raises(exception):
        run_bounded(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            5.0, 4096 if failure == "memory" else 1 << 30,
            Path.cwd(), disk_root=tmp_path,
            disk_limit=4096 if failure == "disk" else 1 << 20,
        )


def test_bounded_runner_records_final_limits(tmp_path: Path) -> None:
    result = run_bounded(
        [sys.executable, "-c", "import time; time.sleep(0.15)"],
        5.0, 1 << 30, Path.cwd(), disk_root=tmp_path,
        disk_limit=1 << 20,
    )
    assert 0 < result["peak_rss_bytes"] <= 1 << 30
    assert 0.0 <= result["wall_seconds"] <= 5.0
    assert result["disk_high_water_bytes"] <= 1 << 20


@pytest.mark.skipif(CORE is None, reason="set RESONITH_NATIVE_CORE")
def test_short_known_phase_innovation_improves_truth_direction(
    tmp_path: Path,
) -> None:
    sample_rate = 8000
    frames = 32_768
    split = frames // 2
    time = np.arange(frames, dtype=np.float64)
    phase = 2.0 * np.pi * 440.0 * time / sample_rate
    phase[split:] += np.pi / 2.0
    samples = np.rint(11000.0 * np.cos(phase)).astype(np.int16)[:, None]
    centers = tuple(range(0, frames, 512))
    rows = tuple(
        _row(
            index, center, tile_end=frames, frequency_q20=440 << 20,
            gain=11000, hop=512,
        )
        for index, center in enumerate(centers)
    )
    plan = LanePlan(
        track_id=0, channel=0, basis_length=128, observations=rows,
        knot_indexes=(0, split // 512, len(rows) - 1),
        placement_count=3, fit_error_q20=0,
        estimated_energy_numerator=_lane_energy_numerator(rows, 0),
    )
    raw_evidence = {
        row.identity: PhaseEvidence(
            (_phase_turn_u32(float(phase[row.center_sample])),),
            (0.01,), (True,),
        )
        for row in rows
    }
    evidence = _seal(
        PhaseEvidenceVault(raw_evidence), "c" * 64,
        tmp_path / "eligibility-innovation.json",
    )
    carry_lane = _lower_lane(plan, evidence, sample_rate, False)
    reset_lane = _lower_lane(plan, evidence, sample_rate, True)
    decoder = NativeMain0Decoder(Path(CORE))
    carry = _evaluate_subset(
        samples, sample_rate, (carry_lane,), native_decoder=decoder,
        coefficients_per_frame=64, half_window=128, band_count=8,
    )
    reset = _evaluate_subset(
        samples, sample_rate, (reset_lane,), native_decoder=decoder,
        coefficients_per_frame=64, half_window=128, band_count=8,
    )
    assert any(
        left.source_position_q16 != right.source_position_q16
        for left, right in zip(carry_lane.instances, reset_lane.instances)
    )
    assert reset.residual_bytes < carry.residual_bytes


@pytest.mark.skipif(CORE is None, reason="set RESONITH_NATIVE_CORE")
def test_frozen_600_placement_control_identity_and_schedule() -> None:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    row = manifest["wav_sources"][3]
    sample_rate, samples = validate_source_row(row)
    assert sample_rate == 48000
    decoder = NativeMain0Decoder(Path(CORE))
    one_eighth_turn = 1 << 29
    evidence = validate_synthetic_control(
        manifest, row, samples, decoder,
        [{
            "track_id": 0,
            "channel": 0,
            "lane_birth_sample": 24 * sample_rate,
            "start_sample": 31 * sample_rate,
            "delta_turn_u32": one_eighth_turn,
        }],
    )
    assert evidence["scheduled_innovation_count"] == 19
    assert evidence["detected_innovation_samples"] == [30 * sample_rate]
    assert evidence["known_phase_innovation_detection_pass"]
    drift_only = validate_synthetic_control(
        manifest, row, samples, decoder,
        [{
            "track_id": 0,
            "channel": 0,
            "lane_birth_sample": 24 * sample_rate,
            "start_sample": 31 * sample_rate,
            "delta_turn_u32": 1 << 24,
        }],
    )
    assert not drift_only["known_phase_innovation_detection_pass"]


@pytest.mark.skipif(CORE is None, reason="set RESONITH_NATIVE_CORE")
def test_controller_authority_drift_publishes_nothing(tmp_path: Path) -> None:
    destination = tmp_path / "run"

    with pytest.raises(RuntimeError, match="runner identity drift"):
        run_controller(
            SOURCE_MANIFEST, destination, Path(CORE), "0" * 64,
            "0" * 40,
        )
    assert not destination.exists()
