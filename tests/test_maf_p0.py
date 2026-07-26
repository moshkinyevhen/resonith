from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.codec import decode_bytes, encode_samples  # noqa: E402
from maf_p0.model import (  # noqa: E402
    load_analysis_model,
    save_analysis_model,
    train_linear_cibs,
)
from maf_p0.periodic import (  # noqa: E402
    apply_block_gains,
    render_unity_basis,
)


def make_harmonic_basis(
    length: int,
    *,
    harmonic_gains: list[float],
    phases: list[float],
    peak: float = 20_000.0,
) -> np.ndarray:
    position = np.arange(length, dtype=np.float64) / length
    signal = np.zeros(length, dtype=np.float64)
    for harmonic, (gain, phase) in enumerate(
        zip(harmonic_gains, phases, strict=True),
        start=1,
    ):
        signal += gain * np.sin(2.0 * np.pi * harmonic * position + phase)
    maximum = float(np.max(np.abs(signal)))
    if maximum > 0.0:
        signal *= peak / maximum
    return np.rint(signal).astype(np.int16)


def make_training_bases(length: int = 256, count: int = 40) -> np.ndarray:
    generator = np.random.default_rng(20260726)
    bases = []
    for _ in range(count):
        gains = [
            1.0,
            float(generator.uniform(0.05, 0.55)),
            float(generator.uniform(0.02, 0.35)),
            float(generator.uniform(0.00, 0.20)),
            float(generator.uniform(0.00, 0.12)),
        ]
        phases = [float(generator.uniform(-0.3, 0.3)) for _ in gains]
        bases.append(
            make_harmonic_basis(
                length,
                harmonic_gains=gains,
                phases=phases,
                peak=float(generator.uniform(14_000, 24_000)),
            ).reshape(1, -1)
        )
    return np.stack(bases)


class MAFP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.basis_length = 256
        cls.model = train_linear_cibs(
            make_training_bases(cls.basis_length),
            latent_elements=12,
            model_id="CIBS0-P0-TEST",
        )
        cls.period = 240
        cls.sample_rate = 48_000
        cls.sample_count = 48_000
        cls.block_size = 1024

        target_basis = make_harmonic_basis(
            cls.basis_length,
            harmonic_gains=[1.0, 0.31, 0.17, 0.08, 0.03],
            phases=[0.12, -0.08, 0.21, -0.18, 0.04],
            peak=19_000,
        )
        unity = render_unity_basis(
            target_basis,
            cls.sample_count,
            int(round((1 << 32) / cls.period)),
        )
        block_count = (
            cls.sample_count + cls.block_size - 1
        ) // cls.block_size
        phase = np.linspace(0.0, 2.0 * np.pi, block_count, endpoint=False)
        gains = np.rint((0.72 + 0.20 * np.sin(phase)) * (1 << 15)).astype(
            np.int32
        )
        cls.samples = apply_block_gains(unity, gains, cls.block_size)

    def test_lossless_raw_and_cibs_round_trip(self) -> None:
        for mode in ("raw", "cibs"):
            encoded = encode_samples(
                self.samples,
                self.sample_rate,
                basis_mode=mode,
                cibs_model=self.model if mode == "cibs" else None,
                basis_length=self.basis_length,
                gain_block_size=self.block_size,
                basis_correction_step=1,
                residual_step=1,
                period_samples=self.period,
            )
            decoded = decode_bytes(
                encoded.payload,
                cibs_model=self.model if mode == "cibs" else None,
            )
            np.testing.assert_array_equal(decoded.samples, self.samples)
            self.assertTrue(encoded.report["exact"])
            self.assertTrue(decoded.report["matches_source_hash"])
            self.assertLess(len(encoded.payload), self.samples.nbytes)

    def test_lossy_path_reports_quality(self) -> None:
        encoded = encode_samples(
            self.samples,
            self.sample_rate,
            basis_mode="cibs",
            cibs_model=self.model,
            basis_length=self.basis_length,
            gain_block_size=self.block_size,
            basis_correction_step=8,
            residual_step=16,
            period_samples=self.period,
        )
        decoded = decode_bytes(encoded.payload, cibs_model=self.model)
        self.assertFalse(encoded.report["exact"])
        self.assertLessEqual(encoded.report["max_abs_error"], 8)
        self.assertGreater(encoded.report["snr_db"], 60.0)
        np.testing.assert_array_equal(decoded.samples, encoded.reconstructed)

    def test_model_package_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test-model.npz"
            save_analysis_model(path, self.model)
            loaded = load_analysis_model(path)
            self.assertEqual(loaded.model_id, self.model.model_id)
            np.testing.assert_array_equal(
                loaded.projection, self.model.projection
            )
            np.testing.assert_array_equal(
                loaded.projection_bias, self.model.projection_bias
            )

    def test_corruption_is_rejected(self) -> None:
        encoded = encode_samples(
            self.samples,
            self.sample_rate,
            basis_mode="raw",
            basis_length=self.basis_length,
            gain_block_size=self.block_size,
            residual_step=1,
            period_samples=self.period,
        )
        damaged = bytearray(encoded.payload)
        damaged[-1] ^= 0x80
        with self.assertRaises((ValueError, RuntimeError)):
            decode_bytes(bytes(damaged))


if __name__ == "__main__":
    unittest.main()
