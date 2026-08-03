from __future__ import annotations

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
import zipfile, zipimport

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from maf_p0.maf_source_filter_oracle import (
    _BitWriter,
    FilterLaw,
    PitchLaw,
    _candidate_choice_digest,
    _candidate_output_window,
    _committed_state_identity,
    _decoder_domain_quality_q20,
    _desired_short_excitation_target,
    _local_log_mel_error,
    _local_mel_filter_bank,
    _prepare_short_filter_lpc,
    _round_half_even,
    _select_decoder_domain_candidate,
    _synthesize_short_filter_candidate,
    _synthesize_source_filter,
    _writer_identity,
    analyze_maf_source_filter_source,
    decode_maf_source_filter_stream,
    encode_maf_source_filter_analysis,
)
from r232_s15_source_filter_gate import (
    _MonitoredFailure,
    _claim_prefix_receipt,
    _execute_suite_transaction,
    _filtered_tree_sha256,
    _run_monitored,
    _sha256,
    _trace_alignment,
    _validate_authority,
    _validate_completed_worker,
)


class MafSourceFilterOracleTests(unittest.TestCase):
    @staticmethod
    def _r257_hostile_authority(root: Path, label: str, statement: str) -> tuple[Path, str]:
        base_path = PROJECT_ROOT/"experiments/fixtures/r259_s15_source_execution_authority.json"; authority = json.loads(base_path.read_text(encoding="utf-8")); source = root/f"{label}.py"; source.write_text("import unittest\nclass Hostile(unittest.TestCase):\n def test_mutation(self):\n"+f"  {statement}\n",encoding="utf-8"); relative = source.relative_to(PROJECT_ROOT).as_posix(); record = {"package":False,"path":relative,"sha256":_sha256(source)}; authority["files"]["test_module"] = {"path":relative,"sha256":record["sha256"]}; authority["local_imports"]["test_maf_source_filter_oracle"] = record; authority["source_execution"]["required_local_imports"]["focused"] = ["test_maf_source_filter_oracle"]; authority_path = root/f"{label}-authority.json"; authority_path.write_text(json.dumps(authority,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return authority_path,_sha256(authority_path)

    @staticmethod
    def _source() -> tuple[int, np.ndarray]:
        sample_rate = 16000
        time = np.arange(2048, dtype=np.float64)
        pitch = 125.0 + 8.0 * time / time.size
        phase = np.cumsum(2.0 * np.pi * pitch / sample_rate)
        excitation = (
            7500.0 * np.sin(phase)
            + 2600.0 * np.sin(2.0 * phase)
            + 900.0 * np.sin(3.0 * phase)
        )
        source = np.clip(
            np.rint(excitation),
            -32768,
            32767,
        ).astype(np.int16)
        return sample_rate, source

    def test_prepared_lpc_matches_frozen_scalar_golden(self) -> None:
        fixture = (
            PROJECT_ROOT
            / "tests"
            / "fixtures"
            / "r250_s15_lpc_golden.json.gz"
        )
        compressed = fixture.read_bytes()
        self.assertEqual(len(compressed), 56229)
        self.assertEqual(
            hashlib.sha256(compressed).hexdigest(),
            "793bff4e748435c079668920a5a2a6cc97b932250bb1bca1df69ed2c6958cc35",
        )
        raw = gzip.decompress(compressed)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "8fe390457f9baf5226207f2d3c3ebb71c6ba5ac968921cb7e6e145f9b4e8ccf6",
        )
        payload = json.loads(raw)
        self.assertEqual(payload["schema"], "resonith-r243-golden-1")
        self.assertEqual(payload["case_count"], 128)

        for case in payload["cases"]:
            source_size = case["source_size"]
            block_size = case["block_size"]
            start = case["start"]
            stop = case["stop"]
            law_count = (source_size + block_size - 1) // block_size
            base = tuple(case["law_family"])
            laws = tuple(
                FilterLaw(
                    (
                        -115 + ((base[0] + 115 + 17 * block) % 231),
                        *base[1:],
                    )
                )
                for block in range(law_count)
            )
            alternate = np.where(
                np.arange(source_size) % 2 == 0,
                -32768,
                32767,
            ).astype(np.int16)
            if case["pattern"] == "zero":
                source = np.zeros(source_size, dtype=np.int16)
                committed = np.zeros(source_size, dtype=np.int64)
                raw_excitation = np.zeros(stop - start, dtype=np.int64)
            elif case["pattern"] == "lcg":
                state = 0x00524243
                source = np.empty(source_size, dtype=np.int16)
                for index in range(source_size):
                    state = (1664525 * state + 1013904223) & 0xFFFF_FFFF
                    source[index] = ((state >> 16) & 0xFFFF) - 32768
                committed = source.astype(np.int64)
                raw_excitation = source[start:stop].astype(np.int64)
            else:
                source = alternate
                committed = alternate.astype(np.int64)
                raw_excitation = (
                    np.full(stop - start, 32767, dtype=np.int64)
                    if case["pattern"] == "clipping"
                    else alternate[start:stop].astype(np.int64)
                )
            analysis = SimpleNamespace(
                source=source,
                block_size=block_size,
                filter_laws=laws,
            )
            first_block, prepared = _prepare_short_filter_lpc(
                analysis,
                start,
                stop,
            )
            touched = case["touched_lpc_q14"]
            self.assertEqual(first_block, touched[0]["absolute_block"])
            self.assertEqual(
                prepared,
                tuple(tuple(item["lpc_q14"]) for item in touched),
            )
            desired = _desired_short_excitation_target(
                analysis,
                start,
                stop,
                first_block,
                prepared,
            )
            output, clipping = _synthesize_short_filter_candidate(
                analysis,
                raw_excitation,
                committed,
                start,
                stop,
                first_block,
                prepared,
            )
            np.testing.assert_array_equal(desired, case["desired_excitation"])
            np.testing.assert_array_equal(output, case["candidate_output"])
            self.assertEqual(clipping, case["clipping_count"])

    def test_prepared_lpc_bounds_and_mapping_fail_closed(self) -> None:
        source = np.zeros(513, dtype=np.int16)
        laws = tuple(FilterLaw((0,)) for _ in range(9))
        analysis = SimpleNamespace(
            source=source,
            block_size=64,
            filter_laws=laws,
        )
        first_block, prepared = _prepare_short_filter_lpc(analysis, 1, 513)
        self.assertEqual(first_block, 0)
        self.assertEqual(len(prepared), 9)
        repeated_first, repeated_prepared = _prepare_short_filter_lpc(
            analysis,
            1,
            513,
        )
        self.assertEqual(
            (repeated_first, repeated_prepared),
            (first_block, prepared),
        )
        self.assertIsNot(repeated_prepared, prepared)

        invalid_intervals = ((0, 0), (2, 1), (-1, 1), (1, 514), (0, 513))
        for start, stop in invalid_intervals:
            with self.assertRaises(ValueError):
                _prepare_short_filter_lpc(analysis, start, stop)

        invalid_law_sets = (
            (63, laws),
            (8193, laws),
            (64, laws[:-1]),
            (64, laws + laws[:1]),
        )
        for block_size, filter_laws in invalid_law_sets:
            invalid = SimpleNamespace(
                source=source,
                block_size=block_size,
                filter_laws=filter_laws,
            )
            with self.assertRaises(ValueError):
                _prepare_short_filter_lpc(invalid, 1, 513)

        with self.assertRaises(RuntimeError):
            _desired_short_excitation_target(
                analysis,
                1,
                513,
                first_block + 1,
                prepared,
            )
        with self.assertRaises(RuntimeError):
            _synthesize_short_filter_candidate(
                analysis,
                np.zeros(512, dtype=np.int64),
                np.zeros(513, dtype=np.int64),
                1,
                513,
                first_block + 1,
                prepared,
            )

    def test_persistent_laws_preserve_exact_analysis_identity(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            parameter_lambda=4.0,
            half_window=64,
            band_count=8,
        )

        self.assertEqual(analysis.source.shape, analysis.innovation.shape)
        self.assertEqual(len(analysis.pitch_laws), 8)
        self.assertEqual(len(analysis.filter_laws), 8)
        self.assertGreater(
            analysis.parameter_report["pitch_hold_count"]
            + analysis.parameter_report["filter_hold_count"],
            0,
        )

    def test_complete_source_filter_stream_round_trips(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            parameter_lambda=4.0,
            half_window=64,
            band_count=8,
        )
        first = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        second = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        decoded_rate, decoded = decode_maf_source_filter_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(first.reconstruction, decoded)
        self.assertGreater(first.report["parameter_event_count"], 0)
        self.assertGreater(first.report["maf_cell"]["basis_count"], 0)

    def test_adaptive_excitation_stream_round_trips(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=6,
            parameter_lambda=0.0,
            half_window=64,
            band_count=8,
        )
        encoded = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=16,
            rate_lambda_q20=4096,
            excitation_backend="epvq",
            excitation_subframe_size=64,
            excitation_pulses=4,
            excitation_basis_count=4,
            excitation_basis_pulses=8,
            excitation_basis_correction_pulses=2,
        )
        decoded_rate, decoded = decode_maf_source_filter_stream(
            encoded.payload
        )

        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(encoded.reconstruction, decoded)
        self.assertEqual(encoded.report["excitation_backend"], "epvq")
        self.assertGreater(
            encoded.report["maf_cell"]["pitch_update_count"],
            0,
        )
        self.assertGreater(
            encoded.report["maf_cell"]["basis_count"],
            0,
        )

    def test_decoder_domain_rescoring_is_deterministic_and_decodable(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=6,
            parameter_lambda=0.0,
            filter_basis_count=4,
            filter_basis_iterations=2,
            half_window=64,
            band_count=8,
        )
        arguments = {
            "maximum_pulses_per_frame": 16,
            "rate_lambda_q20": 4096,
            "basis_search_limit": 4,
            "excitation_backend": "epvq",
            "excitation_subframe_size": 64,
            "excitation_pulses": 4,
            "excitation_basis_count": 0,
            "decoder_domain_rescoring": True,
        }
        first = encode_maf_source_filter_analysis(analysis, **arguments)
        second = encode_maf_source_filter_analysis(analysis, **arguments)
        decoded_rate, decoded = decode_maf_source_filter_stream(first.payload)

        self.assertEqual(first.payload, second.payload)
        self.assertEqual(decoded_rate, sample_rate)
        np.testing.assert_array_equal(first.reconstruction, decoded)
        self.assertTrue(first.report["decoder_domain_rescoring"])
        self.assertTrue(first.report["maf_cell"]["decoder_domain_rescoring"])
        self.assertEqual(
            len(first.report["maf_cell"]["candidate_trace_sha256"]),
            64,
        )
        self.assertEqual(
            len(first.report["maf_cell"]["candidate_choice_digests"]),
            first.report["maf_cell"]["subframe_count"],
        )
        self.assertEqual(
            first.report["maf_cell"][
                "decoder_domain_scoring_transaction_checks"
            ],
            first.report["maf_cell"]["subframe_count"],
        )
        self.assertGreater(
            first.report["maf_cell"][
                "decoder_domain_rejected_candidate_evaluations"
            ],
            0,
        )

    @staticmethod
    def _evaluated_candidate(
        name: str,
        *,
        bits: int,
        clipping: int,
        waveform: int,
        mel: float,
        field: int,
    ) -> tuple:
        decoded = np.array([field], dtype=np.int64)
        candidate = (0, bits, name, decoded, (field,))
        return (
            candidate,
            decoded.copy(),
            clipping,
            waveform,
            mel,
            bits,
            name,
            (field,),
        )

    def test_decoder_domain_selector_boundaries_and_ties(self) -> None:
        legacy = self._evaluated_candidate(
            "PVQ", bits=9, clipping=1, waveform=100, mel=1.0, field=1
        )
        exact_boundary = self._evaluated_candidate(
            "BASIS", bits=1, clipping=1, waveform=101, mel=1.01, field=2
        )
        waveform_reject = self._evaluated_candidate(
            "STOCHASTIC",
            bits=0,
            clipping=1,
            waveform=102,
            mel=1.0,
            field=3,
        )
        mel_reject = self._evaluated_candidate(
            "ZERO",
            bits=0,
            clipping=1,
            waveform=100,
            mel=1.0100000001,
            field=4,
        )
        clip_reject = self._evaluated_candidate(
            "ZERO", bits=0, clipping=2, waveform=1, mel=0.0, field=5
        )
        selected = _select_decoder_domain_candidate(
            [legacy, exact_boundary, waveform_reject, mel_reject, clip_reject],
            legacy[0],
            8192,
        )

        self.assertIs(selected[0], exact_boundary[0])
        self.assertEqual(selected[-1], 3)
        self.assertEqual(_round_half_even(0.5), 0)
        self.assertEqual(_round_half_even(1.5), 2)
        self.assertEqual(_round_half_even(2.5), 2)
        self.assertEqual(_decoder_domain_quality_q20(0, 0.0, 0, 0.0), 0)

    def test_candidate_trace_binds_adaptive_and_first_divergence(self) -> None:
        candidate = (
            4,
            5,
            "PVQ",
            np.array([1, -2], dtype=np.int64),
            (3, 4),
        )
        baseline = _candidate_choice_digest(
            7,
            64,
            80,
            np.array([5, 6], dtype=np.int64),
            [candidate],
        )
        changed = _candidate_choice_digest(
            7,
            65,
            80,
            np.array([5, 6], dtype=np.int64),
            [candidate],
        )
        self.assertNotEqual(baseline, changed)
        adaptive_changed = _candidate_choice_digest(
            7,
            64,
            80,
            np.array([5, 7], dtype=np.int64),
            [candidate],
        )
        payload_changed = (
            4,
            5,
            "PVQ",
            np.array([1, -2], dtype=np.int64),
            (3, 5),
        )
        order_changed = _candidate_choice_digest(
            7,
            64,
            80,
            np.array([5, 6], dtype=np.int64),
            [payload_changed, candidate],
        )
        self.assertNotEqual(baseline, adaptive_changed)
        self.assertNotEqual(baseline, order_changed)

        legacy = {
            "maf_cell": {
                "candidate_choice_digests": ["a", "b", "c"],
                "selected_candidate_signatures": ["x", "y", "z"],
            }
        }
        rescored = {
            "maf_cell": {
                "candidate_choice_digests": ["a", "b", "different-later"],
                "selected_candidate_signatures": ["x", "q", "r"],
            }
        }
        aligned = _trace_alignment(legacy, rescored)
        self.assertEqual(aligned["first_divergent_winner_subframe"], 1)
        self.assertEqual(aligned["verified_choice_count"], 2)

        rescored["maf_cell"]["candidate_choice_digests"][1] = "wrong"
        with self.assertRaises(RuntimeError):
            _trace_alignment(legacy, rescored)

    def test_zero_legacy_mel_rejects_any_positive_mel(self) -> None:
        legacy = self._evaluated_candidate(
            "PVQ", bits=4, clipping=0, waveform=0, mel=0.0, field=1
        )
        positive = self._evaluated_candidate(
            "ZERO", bits=0, clipping=0, waveform=0, mel=1.0e-300, field=2
        )
        selected = _select_decoder_domain_candidate(
            [legacy, positive],
            legacy[0],
            8192,
        )

        self.assertIs(selected[0], legacy[0])
        self.assertEqual(selected[-1], 1)
        self.assertEqual(
            _decoder_domain_quality_q20(0, 5.0e-31, 0, 1.0e-40),
            262144,
        )

    def test_candidate_synthesis_counts_both_clip_sites(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=1,
            parameter_lambda=0.0,
            filter_basis_count=1,
            filter_basis_iterations=1,
            half_window=64,
            band_count=8,
        )
        zero_filter = replace(
            analysis,
            filter_laws=tuple(
                FilterLaw((0,)) for _ in analysis.filter_laws
            ),
        )
        raw_clip, raw_count = _synthesize_short_filter_candidate(
            zero_filter,
            np.array([40000], dtype=np.int64),
            np.zeros(source.size, dtype=np.int64),
            0,
            1,
            *_prepare_short_filter_lpc(zero_filter, 0, 1),
        )
        self.assertEqual(int(raw_clip[0]), 32767)
        self.assertEqual(raw_count, 1)

        predictive_filter = replace(
            analysis,
            filter_laws=tuple(
                FilterLaw((115,)) for _ in analysis.filter_laws
            ),
        )
        committed = np.zeros(source.size, dtype=np.int64)
        committed[0] = -32768
        output_clip, output_count = _synthesize_short_filter_candidate(
            predictive_filter,
            np.array([32767], dtype=np.int64),
            committed,
            1,
            2,
            *_prepare_short_filter_lpc(predictive_filter, 1, 2),
        )
        self.assertEqual(int(output_clip[0]), 32767)
        self.assertEqual(output_count, 1)

    def test_live_state_and_complete_writer_identities_detect_mutation(self) -> None:
        writer = _BitWriter()
        writer.write_bits(0b101, 3)
        baseline = _writer_identity(writer)
        for field in ("_bytes", "_current", "_used", "bit_count"):
            probe = _BitWriter()
            probe.write_bits(0b101, 3)
            if field == "_bytes":
                probe._bytes.append(0x7F)
            else:
                setattr(probe, field, getattr(probe, field) + 1)
            self.assertNotEqual(baseline, _writer_identity(probe), field)

        committed = np.arange(128, dtype=np.int64)
        writable_alias = committed.view()
        committed.flags.writeable = False
        before = _committed_state_identity(committed, 128, 64)
        writable_alias[127] += 1
        after = _committed_state_identity(committed, 128, 64)
        self.assertNotEqual(before, after)

        writable_alias[0] += 1
        unreachable = _committed_state_identity(committed, 128, 64)
        self.assertEqual(after, unreachable)

    def test_candidate_synthesis_is_decoder_exact_and_transactional(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=6,
            parameter_lambda=0.0,
            filter_basis_count=4,
            filter_basis_iterations=2,
            half_window=64,
            band_count=8,
        )
        excitation = analysis.innovation.astype(np.int64)
        committed = np.zeros(source.size, dtype=np.int64)
        for start in range(0, source.size, 64):
            stop = min(source.size, start + 64)
            before = committed.copy()
            candidate, _clipping = _synthesize_short_filter_candidate(
                analysis,
                excitation[start:stop],
                committed,
                start,
                stop,
                *_prepare_short_filter_lpc(analysis, start, stop),
            )
            np.testing.assert_array_equal(before, committed)
            committed[start:stop] = candidate
        zeros = tuple(PitchLaw(0, 0) for _ in analysis.pitch_laws)
        independent = _synthesize_source_filter(
            excitation.astype(np.int16),
            analysis.block_size,
            zeros,
            analysis.filter_laws,
        )
        np.testing.assert_array_equal(committed.astype(np.int16), independent)

    def test_local_mel_guard_has_no_future_input(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=128,
            filter_order=6,
            parameter_lambda=0.0,
            filter_basis_count=4,
            filter_basis_iterations=2,
            half_window=64,
            band_count=8,
        )
        committed = np.zeros(source.size, dtype=np.int64)
        candidate = source[:64].astype(np.int64)
        reference, degraded = _candidate_output_window(
            analysis,
            committed,
            candidate,
            0,
            64,
        )
        mutated_source = source.copy()
        mutated_source[64:] = np.int16(12345)
        mutated = replace(analysis, source=mutated_source)
        other_reference, other_degraded = _candidate_output_window(
            mutated,
            committed,
            candidate,
            0,
            64,
        )
        filters = _local_mel_filter_bank(sample_rate)
        indices = np.arange(256, dtype=np.float64)
        window = 0.5 - 0.5 * np.cos(2.0 * np.pi * indices / 256.0)

        np.testing.assert_array_equal(reference, other_reference)
        np.testing.assert_array_equal(degraded, other_degraded)
        self.assertEqual(
            _local_log_mel_error(reference, degraded, filters, window),
            _local_log_mel_error(
                other_reference,
                other_degraded,
                filters,
                window,
            ),
        )

        committed = source.astype(np.int64).copy()
        candidate = source[64:128].astype(np.int64)
        later_reference, later_degraded = _candidate_output_window(
            analysis,
            committed,
            candidate,
            64,
            128,
        )
        future_source = source.copy()
        future_source[128:] = np.int16(-23456)
        future_analysis = replace(analysis, source=future_source)
        future_reference, future_degraded = _candidate_output_window(
            future_analysis,
            committed,
            candidate,
            64,
            128,
        )
        np.testing.assert_array_equal(later_reference, future_reference)
        np.testing.assert_array_equal(later_degraded, future_degraded)
        changed_prefix = committed.copy()
        changed_prefix[63] += 1
        _, prefix_degraded = _candidate_output_window(
            analysis,
            changed_prefix,
            candidate,
            64,
            128,
        )
        self.assertFalse(np.array_equal(later_degraded, prefix_degraded))

    def test_corruption_and_invalid_parameters_are_rejected(self) -> None:
        sample_rate, source = self._source()
        analysis = analyze_maf_source_filter_source(
            source,
            sample_rate,
            block_size=256,
            filter_order=6,
            half_window=64,
            band_count=8,
        )
        encoded = encode_maf_source_filter_analysis(
            analysis,
            maximum_pulses_per_frame=12,
            rate_lambda_q20=4096,
            basis_search_limit=4,
        )
        with self.assertRaises(ValueError):
            decode_maf_source_filter_stream(encoded.payload[:-1])
        corrupted = bytearray(encoded.payload)
        corrupted[-1] ^= 0x20
        with self.assertRaises(ValueError):
            decode_maf_source_filter_stream(bytes(corrupted))
        with self.assertRaises(ValueError):
            analyze_maf_source_filter_source(
                source,
                sample_rate,
                filter_order=17,
            )

    @unittest.skipUnless(os.name == "nt", "R-232 controller is Windows-only")
    def test_bounded_controller_micro_workers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)

            def run_root(name: str) -> Path:
                root = base / name
                root.mkdir()
                return root

            normal = run_root("normal")
            evidence = _run_monitored(
                [sys.executable, "-c", "print('bounded-ok')"],
                normal,
                normal / "child",
                wall_limit=5.0,
                memory_limit=512 << 20,
                retained_limit=16 << 20,
                output_limit=1 << 20,
            )
            self.assertEqual(evidence["exit_code"], 0)

            timeout = run_root("timeout")
            with self.assertRaises(_MonitoredFailure) as timeout_error:
                _run_monitored(
                    [sys.executable, "-c", "import time; time.sleep(5)"],
                    timeout,
                    timeout / "child",
                    wall_limit=0.15,
                    memory_limit=512 << 20,
                    retained_limit=16 << 20,
                    output_limit=1 << 20,
                )
            self.assertGreater(
                timeout_error.exception.evidence["wall_seconds"],
                0.10,
            )

            spawn = run_root("spawn")
            spawn_code = (
                "import subprocess,sys; "
                "subprocess.run([sys.executable,'-c','pass'],check=True)"
            )
            with self.assertRaises(_MonitoredFailure):
                _run_monitored(
                    [sys.executable, "-c", spawn_code],
                    spawn,
                    spawn / "child",
                    wall_limit=5.0,
                    memory_limit=512 << 20,
                    retained_limit=16 << 20,
                    output_limit=1 << 20,
                )

            memory = run_root("memory")
            with self.assertRaises(_MonitoredFailure):
                _run_monitored(
                    [sys.executable, "-c", "x=bytearray(256 << 20)"],
                    memory,
                    memory / "child",
                    wall_limit=5.0,
                    memory_limit=64 << 20,
                    retained_limit=16 << 20,
                    output_limit=1 << 20,
                )

            logs = run_root("logs")
            with self.assertRaises(_MonitoredFailure):
                _run_monitored(
                    [sys.executable, "-c", "print('x' * 16384)"],
                    logs,
                    logs / "child",
                    wall_limit=5.0,
                    memory_limit=512 << 20,
                    retained_limit=16 << 20,
                    output_limit=1024,
                )

            storage = run_root("storage")
            stored = storage / "oversized.bin"
            storage_code = (
                "from pathlib import Path; "
                f"Path({str(stored)!r}).write_bytes(b'x' * 16384)"
            )
            with self.assertRaises(_MonitoredFailure):
                _run_monitored(
                    [sys.executable, "-c", storage_code],
                    storage,
                    storage / "child",
                    wall_limit=5.0,
                    memory_limit=512 << 20,
                    retained_limit=4096,
                    output_limit=1 << 20,
                )

    def test_authority_drift_and_suite_failure_are_fail_closed(self) -> None:
        authority = (
            PROJECT_ROOT
            / "experiments/fixtures/r234_s15_implementation_authority.json"
        )
        authority_sha256 = _sha256(authority)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            drift = root / "authority.json"
            drift.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                _validate_authority(drift, authority_sha256)

            calls = []
            output = root / "suite"
            tasks = [
                {"name": "first"},
                {"name": "fail"},
                {"name": "forbidden-next"},
            ]

            def execute(_staging, _index, task):
                calls.append(task["name"])
                if task["name"] == "fail":
                    raise _MonitoredFailure(
                        "deliberate micro-worker failure",
                        {"request_sha256": "micro", "wall_seconds": 0.0},
                    )
                return {"name": task["name"], "status": "PASS"}

            with self.assertRaises(_MonitoredFailure):
                _execute_suite_transaction(
                    output,
                    authority_sha256,
                    tasks,
                    execute,
                )
            self.assertEqual(calls, ["first", "fail"])
            self.assertFalse(output.exists())
            self.assertFalse(any(root.glob("suite.staging-*")))
            failure = json.loads(
                (root / "suite-failure.json").read_text(encoding="utf-8")
            )
            self.assertEqual(failure["failing_task"]["name"], "fail")
            self.assertEqual(
                failure["resource_evidence"]["request_sha256"],
                "micro",
            )

    @unittest.skipUnless(os.name == "nt", "R-232 controller is Windows-only")
    def test_real_worker_missing_receipt_preserves_resource_evidence(self) -> None:
        authority = (
            PROJECT_ROOT
            / "experiments/fixtures/r259_s15_source_execution_authority.json"
        )
        authority_sha256 = _sha256(authority)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "suite"

            def execute(staging, _index, task):
                run_output = staging / "runs" / "00-real-worker"
                resources = _run_monitored(
                    [sys.executable, "-c", "print('real-worker-complete')"],
                    staging,
                    staging / "logs" / "00-real-worker",
                    context={
                        "request_sha256": "real-worker-request",
                        "task_name": task["name"],
                    },
                    wall_limit=5.0,
                    memory_limit=512 << 20,
                    retained_limit=16 << 20,
                    output_limit=1 << 20,
                )
                return _validate_completed_worker(
                    run_output,
                    resources,
                    authority,
                    authority_sha256,
                    kind="synthetic-control",
                    name=str(task["name"]),
                    request_sha256="real-worker-request",
                )

            with self.assertRaises(_MonitoredFailure):
                _execute_suite_transaction(
                    output,
                    authority_sha256,
                    [{"name": "real-worker-missing-receipt"}],
                    execute,
                )
            failure = json.loads(
                (root / "suite-failure.json").read_text(encoding="utf-8")
            )
            evidence = failure["resource_evidence"]
            self.assertEqual(evidence["exit_code"], 0)
            self.assertEqual(evidence["request_sha256"], "real-worker-request")
            self.assertGreater(evidence["wall_seconds"], 0.0)
            self.assertIn("receipt.json", evidence["post_worker_validation_error"])
            self.assertFalse(output.exists())
            self.assertFalse(any(root.glob("suite.staging-*")))

    def test_authority_closes_local_and_runtime_imports(self) -> None:
        authority = PROJECT_ROOT/"experiments/fixtures/r259_s15_source_execution_authority.json"; os.environ.update({"PYTHONHASHSEED":"0","PYTHONDONTWRITEBYTECODE":"1","OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1","NUMEXPR_NUM_THREADS":"1"})
        parsed, files = _validate_authority(authority, _sha256(authority))
        self.assertEqual(parsed["schema"],"resonith-r257-source-execution-authority-1")
        self.assertEqual(set(files),{"bootstrap","configuration","gate","golden","native_core","r253_preflight","r257_preflight","r260_probe","r260_probe_runner","r260_probe_summary","r260_remediation","r262_remediation","r263_remediation","test_module"}); source = parsed["source_execution"]["r263_launcher_source"]; self.assertEqual((len(parsed["files"]),len(parsed["local_imports"]),len(source.encode()),len(parsed["files"])+len(parsed["local_imports"])+1),(14,67,1014,82)); self.assertNotIn("\n",source); self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),parsed["source_execution"]["r263_launcher_sha256"]); self.assertEqual(Path(parsed["source_execution"]["python_executable_path"]).resolve(strict=True),Path(sys.executable).resolve(strict=True))
        bootstrap = sys.modules["__main__"]
        bootstrap.importlib.import_module("scipy.signal")
        self.assertTrue(any("site-packages" in item.get("cache_key", "").lower() for item in bootstrap.ACTIVE_GUARD.ledger)); self.assertTrue(any(item.get("module") == "scipy._external" and item.get("namespace") for item in bootstrap.ACTIVE_GUARD.ledger))
    def test_r257_bootstrap_budget_and_source_identity(self) -> None:
        bootstrap = sys.modules["__main__"]; source = PROJECT_ROOT / "experiments/r257_source_execution_bootstrap.py"
        self.assertEqual(Path(bootstrap.__file__).resolve(), source.resolve()); self.assertIsNone(bootstrap.__spec__); self.assertEqual(type(bootstrap.__loader__).__name__, "SourceFileLoader")
        self.assertLessEqual(len(source.read_text(encoding="utf-8").splitlines()), 240); self.assertLessEqual(source.stat().st_size, 40 << 10)
        self.assertTrue(sys.dont_write_bytecode and sys.flags.no_site and sys.flags.safe_path)
        self.assertTrue(bootstrap.STARTUP_CACHES and all(Path(path).resolve().is_relative_to(Path(sys.pycache_prefix).resolve()) for path in bootstrap.STARTUP_CACHES))
        owner = bootstrap.ACTIVE_GUARD; raw = str(source.resolve()); self.assertIn(raw, owner.cache); self.assertIsNone(owner.cache[raw]); self.assertNotIn(raw, owner.path); startup = next(item for item in owner.ledger if item.get("startup")); self.assertEqual((startup["cache_key_type"], startup["cache_key"], startup["resolved_target"], startup["value_is_none"]), ("builtins.str", raw, raw, True))
    def test_r257_authority_maps_every_local_source_once(self) -> None:
        authority_path = PROJECT_ROOT / "experiments/fixtures/r259_s15_source_execution_authority.json"; authority = json.loads(authority_path.read_text(encoding="utf-8"))
        mapped = [record["path"] for record in authority["local_imports"].values()]; self.assertEqual(set(authority["local_modules"]), set(mapped) - {"tests/test_maf_source_filter_oracle.py"})
        self.assertEqual(len(mapped), len(set(mapped))); self.assertNotIn("local_bytecode", authority)
        self.assertEqual(authority["source_execution"]["digest"], "resonith-r257-filtered-tree-1"); self.assertEqual(Path(authority["prefix_root"]).resolve(), (PROJECT_ROOT / "artifacts").resolve())
    def test_r257_all_local_modules_use_bound_source_loader(self) -> None:
        authority_path = PROJECT_ROOT / "experiments/fixtures/r259_s15_source_execution_authority.json"; authority = json.loads(authority_path.read_text(encoding="utf-8"))
        prefix = Path(sys.pycache_prefix).resolve(); loaded = 0
        for name, record in authority["local_imports"].items():
            module = sys.modules.get(name)
            if module is None: continue
            loaded += 1; expected = (PROJECT_ROOT / record["path"]).resolve()
            self.assertEqual((type(module.__loader__).__name__, Path(module.__file__).resolve(), Path(module.__spec__.origin).resolve()), ("SourceFileLoader", expected, expected))
            self.assertTrue(Path(module.__spec__.cached).resolve().is_relative_to(prefix)); self.assertEqual(_sha256(expected), record["sha256"])
        self.assertGreaterEqual(loaded, 4); self.assertFalse(any(prefix.iterdir()))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); py_compile = bootstrap.importlib.import_module("py_compile"); names = ("timestamp", "checked", "current", "malformed", "foreign")
            for variant in names:
                source = root / f"probe_{variant}.py"; source.write_text("VALUE='SOURCE'\n", encoding="utf-8"); cache = Path(bootstrap.importlib.util.cache_from_source(str(source))); cache.parent.mkdir(exist_ok=True)
                if variant in {"timestamp", "checked"}:
                    evil = root / f"evil_{variant}.py"; evil.write_text("VALUE='CACHE!'\n", encoding="utf-8"); mode = py_compile.PycInvalidationMode.TIMESTAMP if variant == "timestamp" else py_compile.PycInvalidationMode.CHECKED_HASH; py_compile.compile(str(evil), cfile=str(cache), doraise=True, invalidation_mode=mode)
                    if variant == "timestamp": state = evil.stat(); os.utime(source, ns=(state.st_atime_ns, state.st_mtime_ns))
                    else: payload = bytearray(cache.read_bytes()); payload[8:16] = bootstrap.importlib.util.source_hash(source.read_bytes()); cache.write_bytes(payload)
                elif variant == "current": py_compile.compile(str(source), cfile=str(cache), doraise=True)
                elif variant == "malformed": cache.write_bytes(b"bad")
                else: cache.with_name(f"probe_{variant}.cpython-312.pyc").write_bytes(b"foreign")
            baseline_code = f"import sys;sys.path.insert(0,{str(root)!r});import probe_timestamp,probe_checked;print(probe_timestamp.VALUE,probe_checked.VALUE)"
            baseline = bootstrap.subprocess.run([sys.executable, "-I", "-S", "-B", "-c", baseline_code], capture_output=True, check=False)
            self.assertEqual((baseline.returncode, baseline.stdout.strip()), (0, b"CACHE! CACHE!"), baseline.stderr.decode(errors="replace"))
            alternate = root / "alternate"; alternate.mkdir()
            imports = ",".join(f"probe_{name}" for name in names); execute = f"import sys;sys.path.insert(0,{str(root)!r});import {imports};mods=[{imports}];print(' '.join(m.VALUE for m in mods));print('\\n'.join(m.__cached__ for m in mods))"
            observed = bootstrap.subprocess.run([sys.executable, "-I", "-S", "-B", "-X", f"pycache_prefix={alternate}", "-c", execute], capture_output=True, check=False)
            self.assertEqual(observed.returncode, 0, observed.stderr.decode(errors="replace"))
            lines = observed.stdout.decode().splitlines(); self.assertEqual(lines[0], " ".join("SOURCE" for _name in names)); self.assertTrue(all(Path(path).resolve().is_relative_to(alternate.resolve()) for path in lines[1:]))
            self.assertFalse(any(alternate.iterdir()))
    def test_r257_runtime_digest_ignores_only_cache_descendants(self) -> None:
        bootstrap = sys.modules["__main__"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "module.py").write_text("VALUE = 1\n", encoding="utf-8"); cache = root / "__pycache__"; cache.mkdir()
            (cache / "module.cpython-314.pyc").write_bytes(b"first")
            first = _filtered_tree_sha256(root); first_cache = bootstrap._tree(root, True)
            (cache / "module.cpython-314.pyc").write_bytes(b"second")
            self.assertEqual(_filtered_tree_sha256(root), first); self.assertNotEqual(bootstrap._tree(root, True), first_cache); (root / "legacy.pyc").write_bytes(b"sourceless")
            with self.assertRaises(RuntimeError): _filtered_tree_sha256(root)
            (root / "legacy.pyc").unlink(); (root / "legacy.pyo").write_bytes(b"optimized")
            with self.assertRaises(RuntimeError): _filtered_tree_sha256(root)
    def test_r257_ast_gate_rejects_direct_alias_and_reflective_mutations(self) -> None:
        bootstrap = sys.modules["__main__"]
        statements = ("import sys as s\ns.path = []\n","import sys as s\ncache = s.path_importer_cache\ncache.clear()\n","import sys as s\ngetattr(s, 'path')\n","import sys as s\ns.__dict__['meta_path'] = []\n","import sys\ns = sys\ns.path = []\n","import sys\ns: object = sys\nold = s.path\ns.path = []\ns.path = old\n","import sys\nif (s := sys): s.path = []\n","import sys\n(s,) = (sys,)\ns.path = []\n","from sys import path_hooks\n")
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get("RESONITH_R263_RUN_ROOT",PROJECT_ROOT / "artifacts"))) as temporary:
            source = Path(temporary) / "mutant.py"; relative = source.relative_to(PROJECT_ROOT).as_posix()
            for statement in statements:
                source.write_text(statement, encoding="utf-8"); digest = _sha256(source)
                authority = {"files": {"test_module": {"path": relative, "sha256": digest}}, "local_modules": {relative: digest}}
                with self.assertRaises(RuntimeError): bootstrap._ast_gate(authority)
    def test_r257_guard_rejects_redirected_and_custom_loader_specs(self) -> None:
        bootstrap = sys.modules["__main__"]; authority_path = PROJECT_ROOT / "experiments/fixtures/r259_s15_source_execution_authority.json"; authority = json.loads(authority_path.read_text(encoding="utf-8")); guard = bootstrap._Guard(authority)
        owner = bootstrap.ACTIVE_GUARD; cache_object, path_object = owner.cache, owner.path; raw = str(Path(bootstrap.__file__).resolve()); alias = str(Path(raw).parent / ".." / "experiments" / Path(raw).name)
        mutants = (lambda: cache_object.pop(raw), lambda: cache_object.__setitem__(raw, object()), lambda: (cache_object.pop(raw), cache_object.__setitem__(alias, None)), lambda: cache_object.__setitem__(Path(raw), None), lambda: cache_object.__setitem__(alias, None), lambda: path_object.append(raw))
        for mutate in mutants:
            cache, path = dict(cache_object), list(path_object)
            try: mutate(); self.assertRaises(RuntimeError, bootstrap._Guard, authority)
            finally: cache_object.clear(); cache_object.update(cache); path_object[:] = path; self.assertIs(owner.cache, cache_object); self.assertIs(owner.path, path_object); self.assertEqual(dict(cache_object), cache); self.assertEqual(path_object, path)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); sentinel = root / "executed"; source = root / "body.py"; source.write_text(f"from pathlib import Path;Path({str(sentinel)!r}).write_text('bad')\n", encoding="utf-8")
            legacy = root / "body.pyo"; legacy.write_bytes(b"not-bytecode"); archive = root / "body.zip"
            with zipfile.ZipFile(archive, "w") as output: output.writestr("body.py", source.read_text(encoding="utf-8"))
            class Loader(bootstrap.importlib.machinery.SourceFileLoader):
                def exec_module(self, module): sentinel.write_text("bad", encoding="utf-8")
            external = bootstrap.importlib.import_module("scipy._external"); namespace_type, finder = bootstrap.NAMESPACE_PATH, bootstrap.importlib.machinery.PathFinder._get_spec; valid_raw = next(iter(external.__path__))
            namespace = lambda name, paths: namespace_type(name, paths, finder)
            valid_locations = namespace("r262_valid", [valid_raw]); accepted, record = guard._checked("r262_valid", SimpleNamespace(loader=None, origin=None, submodule_search_locations=valid_locations))
            self.assertIsNone(accepted.loader); self.assertEqual((record["module"], record["loader_type"], record["raw_location"]), ("r262_valid", "NamespaceLoader", valid_raw))
            class NamespaceSubclass(namespace_type): pass
            class StringSubclass(str): pass
            class CustomLocations: __iter__ = lambda self: iter((valid_raw,))
            specs = [SimpleNamespace(loader=object(), origin=str(Path(sys.executable).parent / "Lib/os.py"), submodule_search_locations=()), SimpleNamespace(loader=bootstrap.importlib.machinery.SourceFileLoader("redirected", str(source)), origin=str(source), submodule_search_locations=()), SimpleNamespace(loader=bootstrap.importlib.machinery.SourcelessFileLoader("legacy", str(legacy)), origin=str(legacy), submodule_search_locations=()), SimpleNamespace(loader=zipimport.zipimporter(str(archive)), origin=str(archive) + "\\body.py", submodule_search_locations=()), SimpleNamespace(loader=Loader("subclass", str(Path(sys.executable).parent / "Lib/os.py")), origin=str(Path(sys.executable).parent / "Lib/os.py"), submodule_search_locations=()), SimpleNamespace(loader=None, origin=str(Path(sys.executable).parent / "Lib/os.py"), submodule_search_locations=valid_locations), SimpleNamespace(loader=object(), origin=None, submodule_search_locations=valid_locations)]
            specs.extend(SimpleNamespace(loader=None, origin=None, submodule_search_locations=value) for value in (None, [valid_raw], (valid_raw,), CustomLocations(), NamespaceSubclass("subclass", [valid_raw], finder), namespace("zero", []), namespace("many", [valid_raw, valid_raw]), namespace("non-str", [StringSubclass(valid_raw)])))
            for index, spec in enumerate(specs): self.assertRaises(Exception, guard._checked, f"r257_hostile_{index}", spec)
            site, outside = root / "site", root / "outside"; site.mkdir(); outside.mkdir(); inside, regular, missing = site / "inside", site / "regular", site / "missing"; inside.mkdir(); regular.write_bytes(b"x")
            invalid_paths = [str(site), str(site / ".." / "outside"), str(outside), str(missing), str(regular)]
            child, junction = outside / "child", site / "junction"; child.mkdir(); linked = bootstrap.subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True, check=False); self.assertEqual(linked.returncode, 0, linked.stderr.decode(errors="replace"))
            try:
                for index, value in enumerate([*invalid_paths, str(junction), str(junction / "child")]): self.assertRaises(Exception, bootstrap._namespace, f"r262_path_{index}", namespace("invalid", [value]), site)
                detached = root / "detached"; outside.rename(detached); self.addCleanup(lambda: detached.rename(outside) if detached.exists() else None)
                self.assertRaisesRegex(ImportError, "invalid namespace directory", bootstrap._namespace, "r262_no_descendant_touch", namespace("dangling", [str(junction / "child")]), site); detached.rename(outside)
                self.assertEqual(bootstrap._loaded_namespace("scipy._external", external, guard.site)["resolved_location"], str(Path(valid_raw).resolve()))
                def loaded(locations=valid_locations):
                    loader = external.__loader__; spec = SimpleNamespace(name="r262_loaded", loader=loader, origin=None, submodule_search_locations=locations); return SimpleNamespace(__name__="r262_loaded", __spec__=spec, __loader__=loader, __file__=None, __path__=locations)
                mutations = (lambda module: delattr(module, "__file__"), lambda module: setattr(module, "__file__", "drift"), lambda module: setattr(module, "__name__", "drift"), lambda module: setattr(module.__spec__, "name", "drift"), lambda module: setattr(module, "__loader__", object()), lambda module: setattr(module.__spec__, "loader", object()), lambda module: setattr(module, "__loader__", type(module.__loader__)("other", module.__path__, finder)), lambda module: setattr(module.__spec__, "origin", "drift"), lambda module: setattr(module, "__path__", namespace("other", [valid_raw])))
                for mutate in mutations: module = loaded(); mutate(module); self.assertRaises(Exception, bootstrap._loaded_namespace, "r262_loaded", module, guard.site)
                unique = lambda records,key: len({item[key] for item in records}) == len(records); self.assertFalse(unique(({"module":"a","raw_location":"x","resolved_location":"y"},{"module":"b","raw_location":"x","resolved_location":"z"}), "raw_location")); self.assertTrue(unique(({"module":"a","raw_location":"x","resolved_location":"y"},{"module":"b","raw_location":"z","resolved_location":"w"}), "raw_location")); self.assertFalse(unique(({"module":"a","raw_location":"x","resolved_location":"y"},{"module":"b","raw_location":"z","resolved_location":"y"}), "resolved_location"))
                post_paths = [*invalid_paths, str(junction), str(junction / "child")]
                for index, locations in enumerate((None, [valid_raw], (), (valid_raw,), CustomLocations(), NamespaceSubclass("post-subclass", [valid_raw], finder), namespace("post-zero", []), namespace("post-many", [valid_raw, valid_raw]), namespace("post-nonstr", [StringSubclass(valid_raw)]), *[namespace(f"post-path-{index}", [value]) for index, value in enumerate(post_paths)])): self.assertRaises(Exception, bootstrap._loaded_namespace, f"r262_post_{index}", loaded(locations), site)
            finally: os.rmdir(junction)
            marker, hostile = root / "outside-executed", outside / "r262_hostile.py"; hostile.write_text(f"from pathlib import Path;Path({str(marker)!r}).write_text('executed')\n", encoding="utf-8"); old_path, old_locations, old_cache = external.__path__, external.__spec__.submodule_search_locations, dict(owner.cache); two = namespace("scipy._external", [valid_raw, str(outside)])
            try: external.__path__ = two; external.__spec__.submodule_search_locations = two; self.assertRaises(Exception, bootstrap.importlib.import_module, "scipy._external.r262_hostile")
            finally: external.__path__ = old_path; external.__spec__.submodule_search_locations = old_locations; sys.modules.pop("scipy._external.r262_hostile", None); owner.cache.clear(); owner.cache.update(old_cache)
            self.assertFalse(marker.exists()); owner.stable(); self.assertFalse(sentinel.exists())
        self._assert_r257_guard_mutants_fail_in_isolated_processes()
    def _assert_r257_guard_mutants_fail_in_isolated_processes(self) -> None:
        bootstrap = sys.modules["__main__"]
        guard = bootstrap.ACTIVE_GUARD; authority = bootstrap.ACTIVE_AUTHORITY[2]; prefix = Path(sys.pycache_prefix); root = PROJECT_ROOT; runtime = Path(sys.executable).resolve().parent; paths = bootstrap._path_map(tuple(sys.modules.values()),("G:/outside.pyc",))
        test_module = sys.modules["test_maf_source_filter_oracle"]; test_spec = test_module.__spec__; json_module = sys.modules["json"]
        local = {(root / key).resolve(strict=True): value.lower() for key, value in authority["local_modules"].items()}; test_record = authority["files"]["test_module"]; local[(root / test_record["path"]).resolve(strict=True)] = test_record["sha256"].lower()
        by_name = {name:str((root / record["path"]).resolve(strict=True)) for name,record in authority["local_imports"].items()}; authorized = set(by_name.items()); allowed = (runtime,guard.site)
        external = bootstrap.importlib.import_module("scipy._external"); namespace_records = [bootstrap._loaded_namespace(name,module,guard.site) for name,module in tuple(sys.modules.items()) if type(getattr(getattr(module,"__spec__",None),"loader",None)) is bootstrap.importlib.machinery.NamespaceLoader]; namespace_without_external = [item for item in namespace_records if item["module"] != "scipy._external"]
        alias_name, resolved_name = "r263_unledgered", "r263_resolved_alias"; alias_raw = str(guard.site / "numpy"); resolved_raw = next(iter(external.__path__)) + "\\."
        def namespace(name, raw):
            locations = bootstrap.NAMESPACE_PATH(name,[raw],bootstrap.importlib.machinery.PathFinder._get_spec); loader = bootstrap.importlib.machinery.NamespaceLoader(name,locations,bootstrap.importlib.machinery.PathFinder._get_spec); spec = SimpleNamespace(name=name,loader=loader,origin=None,submodule_search_locations=locations); return SimpleNamespace(__name__=name,__spec__=spec,__loader__=loader,__file__=None,__path__=locations), bootstrap._namespace(name,locations,guard.site)
        alias_module, alias_record = namespace(alias_name,alias_raw); resolved_module, resolved_record = namespace(resolved_name,resolved_raw); finder_key, finder = next((key,value) for key,value in sys.path_importer_cache.items() if type(value) is bootstrap.importlib.machinery.FileFinder); replacement_finder = bootstrap.importlib.machinery.FileFinder(finder_key,*((loader,[suffix]) for suffix,loader in finder._loaders)); drift_loader = object(); hook = bootstrap.importlib.machinery.PathFinder
        labels = ("cache-add","cached-outside","file-none","hook-add","finder-table","finder-replace","local-alias","local-redirect","loader-drift","module-remove","sentinel-readd","namespace-missing","namespace-unledgered-alias","namespace-ledger-duplicate","namespace-resolved-alias")
        def state():
            finders = tuple((id(value),value.path,tuple(value._loaders),tuple(id(loader) for _suffix,loader in value._loaders)) for value in sys.path_importer_cache.values() if type(value) is bootstrap.importlib.machinery.FileFinder)
            namespaces = tuple((name,id(module),id(module.__spec__),id(module.__loader__),id(module.__path__),tuple(module.__path__)) for name,module in sys.modules.items() if type(getattr(getattr(module,"__spec__",None),"loader",None)) is bootstrap.importlib.machinery.NamespaceLoader)
            return ((id(sys.path),tuple(sys.path)),(id(sys.path_hooks),tuple(sys.path_hooks)),(id(sys.meta_path),tuple(sys.meta_path)),(id(sys.modules),tuple(sys.modules.items())),(id(sys.path_importer_cache),tuple(sys.path_importer_cache.items())),tuple(sorted(os.environ.items())),tuple(sys.argv),(id(guard),id(guard.cache),id(guard.path),id(guard.ledger),tuple(tuple(sorted(item.items())) for item in guard.ledger),id(guard.namespace_baseline),guard.namespace_baseline,guard.snapshot,id(guard.cache_paths),tuple(guard.cache_paths.items()),id(guard.path_paths),tuple(guard.path_paths.items())),finders,(id(test_module),test_module.__file__,id(test_module.__loader__),id(test_spec),test_spec.name,test_spec.origin,id(test_spec.loader),test_spec.cached),namespaces)
        bootstrap._validate_loaded(authority,guard,prefix,"focused"); receipts = []; matrix = state(); clear, update, pop, get = dict.clear, dict.update, dict.pop, dict.get; witnesses = {"cache-add":lambda:"G:/forbidden" in sys.path_importer_cache,"cached-outside":lambda:test_spec.cached,"file-none":lambda:test_module.__file__,"hook-add":lambda:(len(sys.path_hooks),sys.path_hooks[-1] is hook),"finder-table":lambda:finder._loaders,"finder-replace":lambda:get(sys.path_importer_cache,finder_key) is replacement_finder,"local-alias":lambda:get(sys.modules,"unauthorized_alias") is test_module,"local-redirect":lambda:(test_module.__file__,test_module.__loader__,test_spec.origin,test_spec.loader,test_spec.cached),"loader-drift":lambda:test_module.__loader__ is drift_loader,"module-remove":lambda:"test_maf_source_filter_oracle" in sys.modules,"sentinel-readd":lambda:guard.bootstrap_raw in sys.path_importer_cache,"namespace-missing":lambda:"scipy._external" in sys.modules,"namespace-unledgered-alias":lambda:get(sys.modules,alias_name) is alias_module,"namespace-ledger-duplicate":lambda:len(guard.ledger),"namespace-resolved-alias":lambda:(get(sys.modules,resolved_name) is resolved_module,len(guard.ledger))}
        for label in labels:
            guard.stable(); before = state(); self.assertEqual(before,matrix); path_items, hook_items, meta_items, module_items, cache_items = tuple(sys.path), tuple(sys.path_hooks), tuple(sys.meta_path), tuple(sys.modules.items()), tuple(sys.path_importer_cache.items()); ledger_items, snapshot = tuple(guard.ledger), guard.snapshot; module_values = (test_module.__file__,test_module.__loader__,test_spec.name,test_spec.origin,test_spec.loader,test_spec.cached); finder_tables = tuple((value,tuple(value._loaders)) for value in sys.path_importer_cache.values() if type(value) is bootstrap.importlib.machinery.FileFinder); failure = observed = mutation_error = None; changed = post_checkpoint = False; witness = witnesses[label]; witness_before = witness()
            try:
                if label == "cache-add": sys.path_importer_cache["G:/forbidden"] = None
                elif label == "cached-outside": test_spec.cached = "G:/outside.pyc"
                elif label == "file-none": test_module.__file__ = None
                elif label == "hook-add": sys.path_hooks.append(hook)
                elif label == "finder-table": finder._loaders = ()
                elif label == "finder-replace": sys.path_importer_cache[finder_key] = replacement_finder
                elif label == "local-alias": sys.modules["unauthorized_alias"] = test_module
                elif label == "local-redirect": test_module.__file__,test_module.__loader__,test_spec.origin,test_spec.loader,test_spec.cached = json_module.__file__,json_module.__loader__,json_module.__spec__.origin,json_module.__spec__.loader,json_module.__spec__.cached
                elif label == "loader-drift": test_module.__loader__ = drift_loader
                elif label == "module-remove": pop(sys.modules,"test_maf_source_filter_oracle")
                elif label == "sentinel-readd": pop(sys.path_importer_cache,guard.bootstrap_raw)
                elif label == "namespace-missing": pop(sys.modules,"scipy._external")
                elif label == "namespace-unledgered-alias": sys.modules[alias_name] = alias_module
                elif label == "namespace-ledger-duplicate": guard.ledger.append(dict(next(item for item in guard.ledger if item.get("namespace"))))
                else: sys.modules[resolved_name] = resolved_module; guard.ledger.append(resolved_record)
                observed = witness(); changed = observed != witness_before
                try:
                    if label in {"cache-add","hook-add","finder-table","finder-replace","sentinel-readd"}: guard.stable()
                    elif label in {"cached-outside","file-none","local-redirect","loader-drift"}: bootstrap._loaded_file("test_maf_source_filter_oracle",test_module,local,by_name,authorized,prefix,allowed,paths)
                    elif label == "local-alias": bootstrap._loaded_file("unauthorized_alias",test_module,local,by_name,authorized,prefix,allowed,paths)
                    elif label == "module-remove": bootstrap._required(authority,guard,"focused",by_name)
                    else: bootstrap._namespaces(guard,namespace_without_external if label == "namespace-missing" else [*namespace_records,*([alias_record] if label == "namespace-unledgered-alias" else [resolved_record] if label == "namespace-resolved-alias" else [])])
                    post_checkpoint = True
                except BaseException as caught: failure = caught
            except BaseException as caught: mutation_error = caught; observed = witness()
            finally:
                sys.path[:] = path_items; sys.path_hooks[:] = hook_items; sys.meta_path[:] = meta_items; clear(sys.modules); update(sys.modules,module_items); clear(sys.path_importer_cache); update(sys.path_importer_cache,cache_items); guard.ledger[:] = ledger_items; guard.snapshot = snapshot; test_module.__file__,test_module.__loader__,test_spec.name,test_spec.origin,test_spec.loader,test_spec.cached = module_values
                for value,table in finder_tables: value._loaders = table
            mutation_error is None or (self.assertEqual(state(),before),receipts.append({"checkpoint":"mutator","exception_category":type(mutation_error).__name__,"label":label,"mutation_witness":hashlib.sha256(repr((witness_before,observed)).encode()).hexdigest(),"restoration_sha256":hashlib.sha256(repr(before).encode()).hexdigest(),"status":"HARNESS_ERROR"}),self.fail(json.dumps(receipts[-1],sort_keys=True,separators=(",",":")))); self.assertTrue(changed); self.assertIs(type(failure),RuntimeError); self.assertTrue(str(failure).startswith(("R-257","R-262"))); self.assertFalse(post_checkpoint); self.assertEqual(state(),before); guard.stable(); self.assertIs(bootstrap.importlib.import_module("json"),json_module); self.assertEqual(state(),before); receipts.append({"checkpoint":"production-validator","label":label,"mutation_witness":hashlib.sha256(repr((witness_before,observed)).encode()).hexdigest(),"rejection_category":str(failure).split()[0],"restoration_sha256":hashlib.sha256(repr(before).encode()).hexdigest(),"status":"REJECTED"}); self.assertEqual(receipts[-1]["label"],label)
        mutants = {"post-exit-drift":"exec(\"import atexit;from pathlib import Path;atexit.register(lambda:Path(__file__).write_text('drift'))\")","source-drift":"exec(\"from pathlib import Path;Path(__file__).write_text('drift')\")","sentinel-invalidate":"exec(\"import importlib,sys;importlib.invalidate_caches();sys.modules['__main__'].ACTIVE_GUARD.stable();print('R260_AFTER_CHECKPOINT')\")"}
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get("RESONITH_R263_RUN_ROOT",PROJECT_ROOT / "artifacts"))) as temporary:
            root = Path(temporary); poison = root / "poison"; poison.mkdir(); sentinel = root / "startup-sentinel"; payload = f"from pathlib import Path;Path({str(sentinel)!r}).write_text('executed')\n"
            (poison / "sitecustomize.py").write_text(payload, encoding="utf-8"); (poison / "usercustomize.py").write_text(payload, encoding="utf-8"); (poison / "hostile.pth").write_text("import sitecustomize\n", encoding="utf-8")
            runs = []; starts = [bootstrap.threading.Event() for _item in mutants]; ends = [bootstrap.threading.Event() for _item in mutants]
            for index, (label, statement) in enumerate(mutants.items()):
                authority, authority_sha = self._r257_hostile_authority(root, label, statement); prefix = PROJECT_ROOT / "artifacts" / f"r257-hostile-{os.getpid()}-{label}-s0"
                command = [sys.executable, "-I", "-S", "-B", "-X", f"pycache_prefix={prefix}", str(Path(bootstrap.__file__)), "--stage0-prefix", str(prefix), "--authority", str(authority), "--expected-authority-sha256", authority_sha, "--role", "focused", "--target"]
                environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("PYTHON") and not key.startswith("RESONITH_R257_PREFIX") and key != "RESONITH_R257_STAGE1"}; environment["PYTHONPATH"] = str(poison); runs.append((index, label, prefix, command, environment))
            def execute(item):
                index, label, prefix, command, environment = item
                index and starts[index-1].wait(); bootstrap._progress("isolated_start",label); starts[index].set()
                try:
                    with self.assertRaises(_MonitoredFailure) as caught: _run_monitored(command, root, root / label, environment=environment, wall_limit=38.0, memory_limit=512 << 20, job_memory_limit=1 << 30, active_process_limit=2, retained_limit=64 << 20, output_limit=4 << 20)
                finally: index and ends[index-1].wait(); bootstrap._progress("isolated_end",label); ends[index].set()
                return label, prefix, caught.exception.evidence
            with ThreadPoolExecutor(max_workers=len(runs)) as pool: outcomes = list(pool.map(execute, runs))
            for label, prefix, evidence in outcomes:
                self.assertNotEqual(evidence["exit_code"], 0); self.assertEqual(evidence["stdout_excerpt"].count("R257_RECEIPT="), int(label == "post-exit-drift")); self.assertNotIn("R257_STAGE0_RECEIPT=",evidence["stdout_excerpt"])
                self.assertNotIn("R260_AFTER_CHECKPOINT", evidence["stdout_excerpt"]); self.assertFalse(prefix.exists()); self.assertFalse(prefix.with_name(prefix.name.removesuffix("-s0") + "-s1").exists())
            self.assertFalse(sentinel.exists())
    def test_r257_owned_prefix_rejects_nonempty_and_reparse(self) -> None:
        bootstrap = sys.modules["__main__"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); plain = root / "plain"; plain.mkdir(); handle, identity = bootstrap._identity(plain)
            try:
                with self.assertRaises(OSError): plain.rename(root / "replacement")
                (plain / "unexpected").write_bytes(b"x"); self.assertRaises(RuntimeError, bootstrap._assert_prefix, plain, identity)
            finally: bootstrap._close(handle)
            owner = bootstrap.ACTIVE_GUARD; path_object = owner.path; original_path = list(path_object); target, junction = Path(bootstrap.__file__).parent, root / "junction"
            command = ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)]; completed = bootstrap.subprocess.run(command, capture_output=True, check=False); self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))
            try:
                with self.assertRaises(RuntimeError): bootstrap._identity(junction)
                self.assertRaises(RuntimeError, _filtered_tree_sha256, junction); self.assertRaises(RuntimeError, bootstrap._tree, junction)
                authority = json.loads((PROJECT_ROOT / "experiments/fixtures/r259_s15_source_execution_authority.json").read_text(encoding="utf-8")); path_object.append(str(junction / Path(bootstrap.__file__).name)); self.assertRaises(RuntimeError, bootstrap._Guard, authority)
            finally:
                path_object[:] = original_path; self.assertIs(owner.path, path_object); self.assertEqual(path_object, original_path); owner.stable()
                os.rmdir(junction)
        authority = PROJECT_ROOT / "experiments/fixtures/r259_s15_source_execution_authority.json"; common = ["--authority", str(authority), "--expected-authority-sha256", _sha256(authority), "--role", "focused", "--target"]; malformed = []
        relative = [sys.executable,"-I","-S","-B","-X","pycache_prefix=relative",str(Path(bootstrap.__file__)),"--stage0-prefix","relative",*common]; malformed.append((relative,None,os.environ.copy())); preexisting = PROJECT_ROOT/"artifacts"/f"r257-preexisting-{os.getpid()}-s0"; preexisting.mkdir(); existing_command = [sys.executable,"-I","-S","-B","-X",f"pycache_prefix={preexisting}",str(Path(bootstrap.__file__)),"--stage0-prefix",str(preexisting),*common]; malformed.append((existing_command,preexisting,os.environ.copy())); missing = PROJECT_ROOT/"artifacts"/f"r257-missing-{os.getpid()}-s1"
        missing_command = [sys.executable, "-S", "-P", "-B", "-X", f"pycache_prefix={missing}", str(Path(bootstrap.__file__)), "--stage1", "--stage0-prefix", str(missing), *common]
        missing_environment = {key:value for key,value in os.environ.items() if key != "RESONITH_R257_STAGE1"}; missing_environment["RESONITH_R257_STAGE1"] = "1"; malformed.append((missing_command,None,missing_environment))
        states = []; flag_root = tempfile.TemporaryDirectory(dir=Path(os.environ.get("RESONITH_R263_RUN_ROOT",PROJECT_ROOT / "artifacts"))); flag_authority, flag_sha = self._r257_hostile_authority(Path(flag_root.name), "valid-flags", "self.assertTrue(True)"); flag_binding = bootstrap._binding(flag_authority,flag_sha,bootstrap._authority(flag_authority,flag_sha)); flag_active = bootstrap.ACTIVE_AUTHORITY; bootstrap.ACTIVE_AUTHORITY = flag_binding; self.addCleanup(setattr,bootstrap,"ACTIVE_AUTHORITY",flag_active); self.addCleanup(flag_root.cleanup)
        mutations = (("remove", "-S"), ("remove", "-P"), ("remove", "-B"), ("insert", "-q"), ("append", "--stage1"), ("set", "PYTHONHASHSEED", "1"), ("set", "PYTHONPATH", str(PROJECT_ROOT)), ("drop", bootstrap.VOLUME), ("set", bootstrap.FINAL_PATH, "G:\\wrong"))
        for index, mutation in enumerate(mutations):
            prefix = PROJECT_ROOT / "artifacts" / f"r257-malformed-{os.getpid()}-{index}-s1"; command, environment, handle, identity = bootstrap._child_state(prefix, flag_authority, flag_sha, "focused", [], flag_binding); command, environment = list(command), dict(environment)
            if mutation[0] == "remove": command.remove(mutation[1])
            elif mutation[0] == "insert": command.insert(1, mutation[1])
            elif mutation[0] == "append": command.append(mutation[1])
            elif mutation[0] == "set": environment[mutation[1]] = mutation[2]
            else: environment.pop(mutation[1])
            states.append((prefix, handle, identity)); malformed.append((command, None, environment))
        try:
            with ThreadPoolExecutor(max_workers=3) as pool: results = list(pool.map(lambda item: bootstrap.subprocess.run(item[0], cwd=PROJECT_ROOT, env=item[2], capture_output=True, check=False, timeout=45), malformed))
            for result in results: self.assertNotEqual(result.returncode,0); self.assertNotIn(b"R257_RECEIPT=",result.stdout)
        finally:
            for prefix, handle, identity in states: bootstrap.finish_child(prefix, handle, identity)
            bootstrap.ACTIVE_AUTHORITY = flag_active; flag_root.cleanup()
            if preexisting.is_dir() and not any(preexisting.iterdir()): preexisting.rmdir()
    def test_r257_worker_prefix_receipts_are_unique_and_exactly_cleaned(self) -> None:
        bootstrap = sys.modules["__main__"]
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get("RESONITH_R263_RUN_ROOT",PROJECT_ROOT / "artifacts"))) as temporary:
            root = Path(temporary); authority_path, _old_sha = self._r257_hostile_authority(root,"passing-test","self.assertTrue(True)"); authority = json.loads(authority_path.read_text(encoding="utf-8")); old_gate = "experiments/r232_s15_source_filter_gate.py"
            gate = root / "synthetic_gate.py"; gate.write_text("def main():\n pass\n", encoding="utf-8")
            gate_relative = gate.relative_to(PROJECT_ROOT).as_posix(); gate_record = {"package": False, "path": gate_relative, "sha256": _sha256(gate)}
            authority["files"]["gate"] = {"path":gate_relative,"sha256":gate_record["sha256"]}; authority["local_modules"].pop(old_gate); authority["local_modules"][gate_relative] = gate_record["sha256"]; authority["local_imports"]["r232_s15_source_filter_gate"] = gate_record
            authority_path.write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8"); authority_sha = _sha256(authority_path); authority = bootstrap._authority(authority_path,authority_sha); binding = bootstrap._binding(authority_path,authority_sha,authority)
            controller = {"file_id": int(os.environ[bootstrap.FILE_ID]), "final_path": os.environ[bootstrap.FINAL_PATH], "path": str(Path(sys.pycache_prefix).resolve()), "role": "focused", "volume": int(os.environ[bootstrap.VOLUME])}; controller["sha256"] = hashlib.sha256(json.dumps(controller, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            states = []; used = set(); receipts = [controller]; old_active = bootstrap.ACTIVE_AUTHORITY; _claim_prefix_receipt(controller, used)
            try:
                self.assertRaises(RuntimeError,bootstrap.worker_child,authority_path,authority_sha,["--marker","mismatch"])
                bootstrap.ACTIVE_AUTHORITY = None
                try:
                    self.assertRaises(RuntimeError,bootstrap.worker_child,authority_path,authority_sha,[])
                finally: bootstrap.ACTIVE_AUTHORITY = binding
                replacement_prefix, rejected_prefix = root/"replacement-rejected-s1", root/"rejected-s1"; replacement_prefix.mkdir(); rejected_prefix.mkdir(); replacement = (binding[0],binding[1],dict(binding[2]),binding[3]); self.assertRaises(RuntimeError,bootstrap._child_state,replacement_prefix,authority_path,authority_sha,"controller",[],replacement); authority["scope"] += "-drift"
                try:
                    self.assertRaises(RuntimeError,bootstrap._child_state,rejected_prefix,authority_path,authority_sha,"controller",[],binding)
                finally: authority["scope"] = binding[2]["scope"].removesuffix("-drift")
                for marker in ("one", "two"): prefix = PROJECT_ROOT / "artifacts" / f"r263-bound-{os.getpid()}-{marker}-s1"; state = bootstrap._child_state(prefix,authority_path,authority_sha,"controller",["--marker",marker],binding); states.append((prefix,state))
                post_prefix = root/"post-use-rejected-s1"; post_prefix.mkdir(); authority["scope"] += "-post"; self.assertRaises(RuntimeError,bootstrap._child_state,post_prefix,authority_path,authority_sha,"controller",[],binding); authority["scope"] = authority["scope"].removesuffix("-post")
                for index, (prefix, (command, environment, _handle, identity)) in enumerate(states):
                    expected = {"authority_sha256": authority_sha, "child_command": command, "file_id": identity[1], "final_path": identity[2], "path": str(prefix), "volume": identity[0]}; expected["sha256"] = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                    _claim_prefix_receipt(expected, used); resources = _run_monitored(command, root, root / f"synthetic-worker-{index}", context={"prefix_receipt": expected}, environment=environment, wall_limit=40.0, memory_limit=512 << 20, retained_limit=16 << 20, output_limit=4 << 20); receipts.append(expected)
                    self.assertEqual(resources["r257_receipt"]["role"], "controller")
                with self.assertRaises(RuntimeError): _claim_prefix_receipt(receipts[0], used)
                claims = {(item["path"],item["volume"],item["file_id"]) for item in receipts}; self.assertEqual(len(claims),3); self.assertEqual(len({item["sha256"] for item in receipts}),3)
            finally:
                bootstrap.ACTIVE_AUTHORITY = old_active; [bootstrap.finish_child(prefix,handle,identity) for prefix,(_command,_environment,handle,identity) in states]
            self.assertTrue(all(not prefix.exists() for prefix, _state in states))
if __name__ == "__main__":
    unittest.main()
