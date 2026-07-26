from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from cibs0 import (  # noqa: E402
    BasisHashMismatch,
    CIBS0Adapter,
    make_demo_model,
    materialize_basis,
)


class CIBS0Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = make_demo_model()
        self.latent = np.array([12, -7, 3, 19, -22, 6, 1, -4], dtype=np.int8)

    def test_materialization_is_repeatable_and_immutable(self) -> None:
        first = materialize_basis(self.latent, self.model)
        second = materialize_basis(self.latent.copy(), self.model)

        np.testing.assert_array_equal(first.samples, second.samples)
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(
            first.sha256,
            "2c901e3a32e042a960d06d71dc5961171d7b6304c5e984f892904b34ef80782f",
        )
        self.assertEqual(first.samples.shape, (2, 32))
        self.assertFalse(first.samples.flags.writeable)
        self.assertGreater(first.integer_macs, 0)

    def test_expected_hash_guards_atomic_commit(self) -> None:
        actual = materialize_basis(self.latent, self.model)
        verified = materialize_basis(
            self.latent,
            self.model,
            expected_sha256=actual.sha256,
        )
        self.assertEqual(actual.sha256, verified.sha256)

        with self.assertRaises(BasisHashMismatch):
            materialize_basis(
                self.latent,
                self.model,
                expected_sha256="00" * 32,
            )

    def test_low_rank_adapter_changes_basis_deterministically(self) -> None:
        rank = 2
        output_elements = self.model.coarse_elements
        adapter = CIBS0Adapter(
            u=(
                (np.arange(output_elements * rank, dtype=np.int32) % 7) - 3
            ).astype(np.int8).reshape(output_elements, rank),
            v=np.array(
                [[1, -1, 2, 0, 1, -2, 1, 0],
                 [0, 1, -1, 2, -2, 1, 0, 1]],
                dtype=np.int8,
            ),
            inner_shift=1,
            output_shift=1,
        )
        plain = materialize_basis(self.latent, self.model)
        adapted = materialize_basis(self.latent, self.model, adapter=adapter)

        self.assertNotEqual(plain.sha256, adapted.sha256)
        self.assertEqual(adapted.samples.shape, plain.samples.shape)

    def test_objective_correction_is_saturated(self) -> None:
        plain = materialize_basis(self.latent, self.model)
        correction = np.full(plain.samples.shape, 100_000, dtype=np.int32)
        corrected = materialize_basis(
            self.latent,
            self.model,
            correction=correction,
        )
        self.assertTrue(np.all(corrected.samples == 32767))

    def test_rejects_non_integer_latent(self) -> None:
        with self.assertRaises(TypeError):
            materialize_basis(
                self.latent.astype(np.float32),
                self.model,
            )


if __name__ == "__main__":
    unittest.main()
