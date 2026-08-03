from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from maf_p0.maf_source_filter_oracle import (
    _BitWriter,
    FilterLaw,
    PitchLaw,
    _candidate_choice_digest,
    _candidate_output_window,
    _committed_state_identity,
    _decoder_domain_quality_q20,
    _local_log_mel_error,
    _local_mel_filter_bank,
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
    _execute_suite_transaction,
    _run_monitored,
    _sha256,
    _trace_alignment,
    _validate_authority,
    _validate_completed_worker,
)


class MafSourceFilterOracleTests(unittest.TestCase):
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
            / "experiments/fixtures/r234_s15_implementation_authority.json"
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
        authority = (
            PROJECT_ROOT
            / "experiments/fixtures/r234_s15_implementation_authority.json"
        )
        os.environ.update(
            {
                "PYTHONHASHSEED": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
            }
        )
        parsed, files = _validate_authority(authority, _sha256(authority))
        self.assertEqual(
            parsed["schema"],
            "resonith-r232-s15-implementation-authority-2",
        )
        self.assertEqual(set(files), {"configuration", "native_core", "preflight", "test_module"})


if __name__ == "__main__":
    unittest.main()
