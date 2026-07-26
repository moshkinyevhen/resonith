from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.perceptual_metrics import (  # noqa: E402
    multiresolution_spectral_error_db,
    transient_pre_echo_error_db,
)


class PerceptualMetricTests(unittest.TestCase):
    @staticmethod
    def _impulses() -> np.ndarray:
        samples = np.zeros((8192, 2), dtype=np.int16)
        samples[2048] = (24000, -18000)
        samples[5000:5010] = (16000, 12000)
        return samples

    def test_exact_signal_has_metric_floor(self) -> None:
        source = self._impulses()
        spectral = multiresolution_spectral_error_db(source, source)
        transient = transient_pre_echo_error_db(source, source, 48000)

        self.assertLess(spectral["mean_spectral_convergence_db"], -250.0)
        self.assertGreater(transient["onset_count"], 0)
        self.assertLess(transient["mean_pre_echo_error_db"], -250.0)

    def test_pre_onset_smear_is_detected(self) -> None:
        source = self._impulses()
        smeared = source.copy()
        smeared[1950:2048] = (3000, -2000)
        clean = transient_pre_echo_error_db(source, source, 48000)
        damaged = transient_pre_echo_error_db(source, smeared, 48000)

        self.assertGreater(
            damaged["mean_pre_echo_error_db"],
            clean["mean_pre_echo_error_db"],
        )


if __name__ == "__main__":
    unittest.main()
