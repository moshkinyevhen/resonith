from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.container import pack_container, unpack_container  # noqa: E402
from maf_p0.model import train_linear_cibs  # noqa: E402
from maf_p0.periodic import (  # noqa: E402
    PhaseTrajectory,
    constant_phase_trajectory,
    render_basis_trajectory,
    render_unity_basis,
)
from maf_p0.stateful import (  # noqa: E402
    decode_stateful_bytes,
    encode_stateful_samples,
)


def sine_basis(length: int, harmonic: int, peak: int = 12000) -> np.ndarray:
    position = np.arange(length, dtype=np.float64) / length
    return np.rint(
        peak * np.sin(2.0 * np.pi * harmonic * position)
    ).astype(np.int16)


class MAFP1Tests(unittest.TestCase):
    sample_rate = 48000
    basis_length = 256
    period = 256
    segment_samples = 8192

    def test_multiple_basis_lifetimes_and_content_reuse(self) -> None:
        basis_a = sine_basis(self.basis_length, 1)
        basis_b = sine_basis(self.basis_length, 3, peak=9000)
        increment = 1 << 24
        segments = [
            render_unity_basis(basis_a, self.segment_samples, increment),
            render_unity_basis(basis_b, self.segment_samples, increment),
            render_unity_basis(basis_a, self.segment_samples, increment),
        ]
        source = np.concatenate(segments)
        trajectories = [
            constant_phase_trajectory(self.segment_samples, increment)
            for _ in segments
        ]
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            segment_samples=self.segment_samples,
            phase_trajectories=trajectories,
            analysis_periods=[self.period] * len(segments),
            gain_block_size=256,
            transient_mode="off",
            residual_step=1,
        )
        decoded = decode_stateful_bytes(encoded.payload)
        np.testing.assert_array_equal(decoded.samples, source)
        self.assertEqual(encoded.report["atom_count"], 3)
        self.assertEqual(encoded.report["basis_count"], 2)
        self.assertEqual(encoded.report["basis_reuses"], 1)
        self.assertEqual(len(encoded.report["stream_sha256"]), 64)

        _, arrays = unpack_container(encoded.payload)
        self.assertEqual(tuple(arrays["BLIF"][0]), (0, source.size))
        self.assertEqual(
            tuple(arrays["BLIF"][1]),
            (self.segment_samples, 2 * self.segment_samples),
        )
        np.testing.assert_array_equal(arrays["ATOM"][:, 2], [0, 1, 0])

    def test_continuous_pitch_trajectory_round_trip(self) -> None:
        sample_count = 12000
        basis = sine_basis(self.basis_length, 1)
        trajectory = PhaseTrajectory(
            positions=np.array([0, 3000, 7000, sample_count], dtype=np.int64),
            increments_q32=np.array(
                [
                    int((1 << 32) / 280.0),
                    int((1 << 32) / 220.0),
                    int((1 << 32) / 340.0),
                    int((1 << 32) / 190.0),
                ],
                dtype=np.uint32,
            ),
            phase_origin_q32=0x1020_3040,
        )
        source = render_basis_trajectory(basis, trajectory)
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            segment_samples=sample_count,
            phase_trajectories=[trajectory],
            analysis_periods=[280],
            gain_block_size=512,
            transient_mode="off",
            residual_step=1,
        )
        decoded = decode_stateful_bytes(encoded.payload)
        np.testing.assert_array_equal(decoded.samples, source)
        self.assertEqual(encoded.report["pitch_knot_count"], 4)
        self.assertTrue(decoded.report["matches_source_hash"])

    def test_multi_basis_cibs_bank_round_trip(self) -> None:
        training = []
        position = np.arange(self.basis_length, dtype=np.float64) / self.basis_length
        for index in range(12):
            signal = (
                np.sin(2.0 * np.pi * position + 0.03 * index)
                + (0.08 + 0.02 * index)
                * np.sin(4.0 * np.pi * position - 0.05 * index)
            )
            signal *= 12000.0 / np.max(np.abs(signal))
            training.append(np.rint(signal).astype(np.int16).reshape(1, -1))
        model = train_linear_cibs(
            np.stack(training),
            latent_elements=6,
            model_id="CIBS0-P1-TEST",
        )
        increment = 1 << 24
        source = np.concatenate(
            [
                render_unity_basis(training[2].reshape(-1), self.segment_samples, increment),
                render_unity_basis(training[8].reshape(-1), self.segment_samples, increment),
            ]
        )
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            basis_mode="cibs",
            cibs_model=model,
            segment_samples=self.segment_samples,
            phase_trajectories=[
                constant_phase_trajectory(self.segment_samples, increment),
                constant_phase_trajectory(self.segment_samples, increment),
            ],
            analysis_periods=[self.period, self.period],
            gain_block_size=256,
            basis_correction_step=1,
            residual_step=1,
            transient_mode="off",
        )
        decoded = decode_stateful_bytes(encoded.payload, cibs_model=model)
        np.testing.assert_array_equal(decoded.samples, source)
        self.assertEqual(encoded.report["basis_mode"], "cibs")
        self.assertEqual(decoded.report["basis_count"], 2)

    def test_transient_path_is_separate_and_lossless(self) -> None:
        sample_count = 16384
        basis = sine_basis(self.basis_length, 1, peak=5000)
        increment = 1 << 24
        source = render_unity_basis(basis, sample_count, increment)
        source[7000:7008] = np.array(
            [28000, -26000, 17000, -9000, 5000, -2000, 500, 0],
            dtype=np.int16,
        )
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            segment_samples=sample_count,
            phase_trajectories=[
                constant_phase_trajectory(sample_count, increment)
            ],
            analysis_periods=[self.period],
            gain_block_size=256,
            transient_mode="on",
            transient_quantization_step=1,
            residual_step=1,
        )
        metadata, arrays = unpack_container(encoded.payload)
        self.assertGreater(metadata["transient_event_count"], 0)
        self.assertIn("TREV", arrays)
        self.assertIn("TRCF", arrays)
        decoded = decode_stateful_bytes(encoded.payload)
        np.testing.assert_array_equal(decoded.samples, source)

    def test_atom_cannot_outlive_its_basis(self) -> None:
        sample_count = 4096
        basis = sine_basis(self.basis_length, 1)
        increment = 1 << 24
        source = render_unity_basis(basis, sample_count, increment)
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            segment_samples=sample_count,
            phase_trajectories=[
                constant_phase_trajectory(sample_count, increment)
            ],
            analysis_periods=[self.period],
            transient_mode="off",
        )
        metadata, arrays = unpack_container(encoded.payload)
        arrays["BLIF"][0, 1] = sample_count - 1
        metadata["bases"][0]["death_sample"] = sample_count - 1
        damaged = pack_container(
            {key: value for key, value in metadata.items() if key != "sections"},
            arrays,
        )
        with self.assertRaisesRegex(ValueError, "outlives"):
            decode_stateful_bytes(damaged)

    def test_silence_uses_universal_periodic_fallback(self) -> None:
        source = np.zeros(12000, dtype=np.int16)
        encoded = encode_stateful_samples(
            source,
            self.sample_rate,
            segment_samples=6000,
            transient_mode="auto",
            residual_step=1,
        )
        decoded = decode_stateful_bytes(encoded.payload)
        np.testing.assert_array_equal(decoded.samples, source)
        self.assertEqual(encoded.report["periodic_fallback_atoms"], 2)
        self.assertEqual(encoded.report["basis_count"], 1)


if __name__ == "__main__":
    unittest.main()
