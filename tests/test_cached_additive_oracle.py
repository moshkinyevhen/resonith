from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.cached_additive_oracle import (  # noqa: E402
    pack_registry_model,
    run_cached_additive_oracle,
)
from maf_p0.model import train_linear_cibs  # noqa: E402
from maf_p0.rsc1 import parse_rsc1  # noqa: E402


class CachedAdditiveOracleTests(unittest.TestCase):
    @staticmethod
    def _model():
        length = 64
        position = np.arange(length, dtype=np.float64)
        training = np.stack(
            [
                np.rint(
                    20_000.0
                    * np.sin(
                        2.0 * np.pi * position / length + phase
                    )
                ).astype(np.int16)
                for phase in np.linspace(
                    0.0,
                    2.0 * np.pi,
                    12,
                    endpoint=False,
                )
            ]
        )[:, np.newaxis, :]
        return train_linear_cibs(
            training,
            latent_elements=8,
            model_id="CIBS0-CACHED-ORACLE-TEST",
        )

    def test_zero_atom_rsl2_is_a_complete_fallback(self) -> None:
        model = self._model()
        sample_count = 2048
        position = np.arange(sample_count, dtype=np.float64)
        source = np.clip(
            np.rint(
                15_000.0 * np.sin(2.0 * np.pi * position / 64.0)
                + 9_000.0
                * np.sin(2.0 * np.pi * position / 103.0 + 0.3)
            ),
            -32768,
            32767,
        ).astype(np.int16)
        result = run_cached_additive_oracle(
            source,
            48_000,
            model,
            gain_block_size=512,
            innovation_step=64,
            residual_block_sizes=(256, 1024),
            maximum_atoms=1,
            analysis_period_candidates=6,
            period_rdo_shortlist=2,
        )
        self.assertLessEqual(
            result.report["stream_bytes"],
            result.report["zero_atom_bytes"],
        )
        self.assertEqual(result.report["candidate_count"], 2)
        self.assertEqual(
            result.report["registry_model_bytes"],
            len(pack_registry_model(model)),
        )
        self.assertEqual(parse_rsc1(result.selected_payload).level, 1)
        self.assertEqual(result.selected_reconstruction.shape, source.shape)
        self.assertFalse(result.selected_reconstruction.flags.writeable)

    def test_registry_accounting_is_deterministic(self) -> None:
        model = self._model()
        first = pack_registry_model(model)
        second = pack_registry_model(model)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith(b"CRM1"))
        self.assertGreater(len(first), model.output_elements)


if __name__ == "__main__":
    unittest.main()
