"""Tests for the research-only R-135 multi-objective admission guard."""

from __future__ import annotations

import unittest

from experiments.maf_typed_truth_fast_gate import _quality_guard


def _metrics(*, snr: float = 40.0, log_mel: float = 1.0) -> dict:
    return {
        "waveform": {
            "snr_db": snr,
            "si_sdr_db": snr,
        },
        "spectral": {
            "log_mel_rmse": log_mel,
            "magnitude_cosine_similarity": 0.99999,
            "multiresolution_stft": {
                "512": {"spectral_convergence": 0.01},
                "2048": {"spectral_convergence": 0.01},
                "8192": {"spectral_convergence": 0.01},
            },
        },
    }


class MafQualityGuardTests(unittest.TestCase):
    def test_waveform_win_cannot_hide_log_mel_regression(self) -> None:
        baseline = _metrics()
        candidate = _metrics(snr=41.0, log_mel=1.20)
        result = _quality_guard(candidate, baseline)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["log_mel_within_3_percent"])
        self.assertTrue(result["checks"]["snr_non_regression"])

    def test_all_declared_non_regressions_admit(self) -> None:
        result = _quality_guard(_metrics(snr=40.1, log_mel=0.99), _metrics())
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
