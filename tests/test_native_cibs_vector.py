from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from cibs0 import CIBS0Adapter, make_demo_model, materialize_basis  # noqa: E402


class NativeCIBSVectorTests(unittest.TestCase):
    @staticmethod
    def _array(source: str, name: str) -> list[int]:
        match = re.search(
            rf"{name}\s*=\s*\{{(.*?)\}};",
            source,
            re.DOTALL,
        )
        if match is None:
            raise AssertionError(f"missing native array {name}")
        return [
            int(token, 0)
            for token in re.findall(
                r"(?<![A-Za-z0-9_])(-?0x[0-9a-fA-F]+|-?\d+)",
                match.group(1),
            )
        ]

    def test_native_demo_model_and_hashes_match_python(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "cibs_test.cpp"
        ).read_text(encoding="utf-8")
        model = make_demo_model()
        latent = np.asarray(self._array(source, "kLatent"), dtype=np.int8)
        np.testing.assert_array_equal(
            np.asarray(self._array(source, "kProjection"), dtype=np.int8),
            model.projection.reshape(-1),
        )
        np.testing.assert_array_equal(
            np.asarray(self._array(source, "kProjectionBias"), dtype=np.int32),
            model.projection_bias,
        )
        np.testing.assert_array_equal(
            np.asarray(self._array(source, "kKernelZero"), dtype=np.int8),
            model.refinement_kernels[0].reshape(-1),
        )
        np.testing.assert_array_equal(
            np.asarray(self._array(source, "kKernelOne"), dtype=np.int8),
            model.refinement_kernels[1].reshape(-1),
        )

        plain = materialize_basis(latent, model)
        self.assertEqual(
            bytes(self._array(source, "kPlainDigest")).hex(),
            plain.sha256,
        )

        adapter = CIBS0Adapter(
            u=np.asarray(
                self._array(source, "kAdapterU"),
                dtype=np.int8,
            ).reshape(model.coarse_elements, 2),
            v=np.asarray(
                self._array(source, "kAdapterV"),
                dtype=np.int8,
            ).reshape(2, model.latent_elements),
            inner_shift=1,
            output_shift=1,
        )
        adapted = materialize_basis(latent, model, adapter=adapter)
        self.assertEqual(
            bytes(self._array(source, "kAdapterDigest")).hex(),
            adapted.sha256,
        )

        correction = np.full(
            plain.samples.shape,
            100_000,
            dtype=np.int32,
        )
        corrected = materialize_basis(
            latent,
            model,
            correction=correction,
        )
        self.assertEqual(
            bytes(self._array(source, "kCorrectionDigest")).hex(),
            corrected.sha256,
        )


if __name__ == "__main__":
    unittest.main()
