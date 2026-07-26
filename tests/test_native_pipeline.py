from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.basis_section import unpack_braw  # noqa: E402
from maf_p0.composition import GainEventLaw, compose_truth  # noqa: E402
from maf_p0.periodic import PhaseTrajectory, render_basis_trajectory  # noqa: E402
from maf_p0.residual import decode_liftpack  # noqa: E402


class NativePipelineTests(unittest.TestCase):
    def test_complete_native_vector_matches_python(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "pipeline_test.cpp"
        ).read_text(encoding="utf-8")

        def array(name: str) -> list[int]:
            match = re.search(
                rf"{name}\s*=\s*\{{(.*?)\}};",
                source,
                re.DOTALL,
            )
            if match is None:
                raise AssertionError(f"missing native array {name}")
            return [
                int(token.rstrip("U"), 0)
                for token in re.findall(
                    r"(?<![A-Za-z0-9_])(-?0x[0-9a-fA-F]+U?|-?\d+U?)",
                    match.group(1),
                )
            ]

        basis = unpack_braw(bytes(array("kBrawPayload"))).reshape(-1)
        trajectory = PhaseTrajectory(
            np.asarray(array("kPhasePositions"), dtype=np.int64),
            np.asarray(array("kPhaseIncrements"), dtype=np.uint32),
            0x1234_5678,
        )
        unity = render_basis_trajectory(basis, trajectory)
        innovation = decode_liftpack(
            bytes(array("kInnovationPayload"))
        ).astype(np.int64)
        gain = GainEventLaw(
            np.asarray(array("kGainPositions"), dtype=np.uint32),
            np.asarray(array("kGainsQ15"), dtype=np.int32),
            unity.size,
        )
        output = compose_truth(
            unity,
            gain,
            innovation_q=innovation,
            innovation_step=3,
        )
        np.testing.assert_array_equal(
            output,
            np.asarray(array("kExpectedPcm"), dtype=np.int16),
        )


if __name__ == "__main__":
    unittest.main()
