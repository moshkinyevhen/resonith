from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.periodic import (  # noqa: E402
    PhaseTrajectory,
    phase_values_q32,
    render_basis_trajectory,
)


class NativeTrajectoryVectorTests(unittest.TestCase):
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
            int(token.rstrip("U"), 0)
            for token in re.findall(
                r"(?<![A-Za-z0-9_])(-?0x[0-9a-fA-F]+U?|-?\d+U?)",
                match.group(1),
            )
        ]

    def test_native_absolute_trajectory_matches_python(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "trajectory_test.cpp"
        ).read_text(encoding="utf-8")
        basis = np.asarray(self._array(source, "kBasis"), dtype=np.int16)
        trajectory = PhaseTrajectory(
            np.asarray(self._array(source, "kPositions"), dtype=np.int64),
            np.asarray(self._array(source, "kIncrements"), dtype=np.uint32),
            0x1234_5678,
        )
        expected_phases = np.asarray(
            self._array(source, "kExpectedPhases"),
            dtype=np.uint32,
        )
        expected_output = np.asarray(
            self._array(source, "kExpectedOutput"),
            dtype=np.int16,
        )
        np.testing.assert_array_equal(
            phase_values_q32(trajectory),
            expected_phases,
        )
        np.testing.assert_array_equal(
            render_basis_trajectory(basis, trajectory),
            expected_output,
        )


if __name__ == "__main__":
    unittest.main()
