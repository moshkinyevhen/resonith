from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.composition import GainEventLaw, compose_truth  # noqa: E402


class CompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.unity = np.array(
            [-10000, -5000, 0, 5000, 10000, 15000],
            dtype=np.int16,
        )
        self.law = GainEventLaw(
            np.array([0, 2, 5], dtype=np.uint32),
            np.array([32768, 16384, -32768], dtype=np.int32),
            self.unity.size,
        )

    def test_sparse_gain_events_apply_until_the_next_event(self) -> None:
        np.testing.assert_array_equal(
            compose_truth(self.unity, self.law),
            np.array([-10000, -5000, 0, 2500, 5000, -15000], dtype=np.int16),
        )

    def test_innovation_is_exactly_scaled_and_saturated(self) -> None:
        innovation = np.array(
            [-10000, 1, 2, 3, 4, 10000],
            dtype=np.int64,
        )
        np.testing.assert_array_equal(
            compose_truth(
                self.unity,
                self.law,
                innovation_q=innovation,
                innovation_step=4,
            ),
            np.array([-32768, -4996, 8, 2512, 5016, 25000], dtype=np.int16),
        )

    def test_arbitrary_slices_match_full_composition(self) -> None:
        innovation = np.arange(-3, 3, dtype=np.int64)
        full = compose_truth(
            self.unity,
            self.law,
            innovation_q=innovation,
            innovation_step=3,
        )
        parts = [
            compose_truth(
                self.unity[start:end],
                self.law,
                output_start=start,
                innovation_q=innovation[start:end],
                innovation_step=3,
            )
            for start, end in ((0, 1), (1, 4), (4, 6))
        ]
        np.testing.assert_array_equal(np.concatenate(parts), full)

    def test_native_vector_matches_reference(self) -> None:
        source = (
            REPOSITORY_ROOT / "native" / "tests" / "composition_test.cpp"
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

        unity = np.asarray(array("kUnity"), dtype=np.int16)
        innovation = np.asarray(array("kInnovation"), dtype=np.int64)
        law = GainEventLaw(
            np.asarray(array("kGainPositions"), dtype=np.uint32),
            np.asarray(array("kGainsQ15"), dtype=np.int32),
            unity.size,
        )
        expected = np.asarray(array("kExpected"), dtype=np.int16)
        expected_gain = np.asarray(array("kExpectedGainOnly"), dtype=np.int16)
        np.testing.assert_array_equal(
            compose_truth(
                unity,
                law,
                innovation_q=innovation,
                innovation_step=3,
            ),
            expected,
        )
        np.testing.assert_array_equal(compose_truth(unity, law), expected_gain)


if __name__ == "__main__":
    unittest.main()
