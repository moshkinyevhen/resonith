from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.periodic import (  # noqa: E402
    MAX_PHASE_KNOT_SPAN,
    PhaseTrajectory,
    constant_phase_trajectory,
    phase_values_q32,
    render_basis_trajectory,
    render_unity_basis,
)


class PhaseTrajectoryTests(unittest.TestCase):
    def setUp(self) -> None:
        position = np.arange(256, dtype=np.float64) / 256.0
        self.basis = np.rint(18000.0 * np.sin(2.0 * np.pi * position)).astype(
            np.int16
        )

    def test_constant_trajectory_matches_p0_renderer(self) -> None:
        sample_count = MAX_PHASE_KNOT_SPAN + 1234
        increment = int(round((1 << 32) / 237.0))
        origin = 0x72A5_193C
        trajectory = constant_phase_trajectory(
            sample_count,
            increment,
            phase_origin_q32=origin,
        )
        expected = render_unity_basis(
            self.basis,
            sample_count,
            increment,
            phase_origin_q32=origin,
        )
        actual = render_basis_trajectory(self.basis, trajectory)
        np.testing.assert_array_equal(actual, expected)

    def test_arbitrary_slices_are_block_size_independent(self) -> None:
        trajectory = PhaseTrajectory(
            positions=np.array([0, 3000, 7000, 12000], dtype=np.int64),
            increments_q32=np.array(
                [
                    int((1 << 32) / 260.0),
                    int((1 << 32) / 220.0),
                    int((1 << 32) / 310.0),
                    int((1 << 32) / 180.0),
                ],
                dtype=np.uint32,
            ),
            phase_origin_q32=0x1234_5678,
        )
        full_phase = phase_values_q32(trajectory)
        full_render = render_basis_trajectory(self.basis, trajectory)
        cuts = [0, 1, 127, 2999, 3000, 4097, 6999, 7000, 11999, 12000]
        phase_parts = []
        render_parts = []
        for start, end in zip(cuts[:-1], cuts[1:], strict=True):
            phase_parts.append(
                phase_values_q32(
                    trajectory,
                    output_start=start,
                    output_count=end - start,
                )
            )
            render_parts.append(
                render_basis_trajectory(
                    self.basis,
                    trajectory,
                    output_start=start,
                    output_count=end - start,
                )
            )
        np.testing.assert_array_equal(np.concatenate(phase_parts), full_phase)
        np.testing.assert_array_equal(np.concatenate(render_parts), full_render)

    def test_invalid_or_unbounded_trajectory_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PhaseTrajectory(
                positions=np.array([0, MAX_PHASE_KNOT_SPAN + 1]),
                increments_q32=np.array([1, 1], dtype=np.uint32),
            )
        with self.assertRaises(ValueError):
            PhaseTrajectory(
                positions=np.array([1, 2]),
                increments_q32=np.array([1, 1], dtype=np.uint32),
            )


if __name__ == "__main__":
    unittest.main()
