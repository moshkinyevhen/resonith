"""Adversarial tests for the optional semantic-provider trust boundary."""

from __future__ import annotations

import copy
import unittest

import numpy as np

from maf_p0.semantic_arbiter import (
    ProposalValidationError,
    analyze_proxy_evidence,
    audit_proposals,
    validate_semantic_proposals,
)


def _valid_payload() -> dict:
    return {
        "schema_version": "resonith-semantic-proposal-1",
        "clips": [
            {
                "clip_id": "tone",
                "duration_seconds": 1.0,
                "primary_class": "tonal",
                "sources": [
                    {
                        "source_id": "s0",
                        "source_class": "tonal_instrument",
                        "start_seconds": 0.0,
                        "end_seconds": 1.0,
                        "confidence": 0.9,
                    }
                ],
                "regions": [
                    {
                        "start_seconds": 0.0,
                        "end_seconds": 1.0,
                        "primary_basis": "coherent",
                        "confidence": 0.9,
                        "lifetime_seconds": 1.0,
                        "reason_code": "stable_pitch",
                    }
                ],
                "specialist_tasks": [],
            }
        ],
    }


class SemanticArbiterTests(unittest.TestCase):
    def test_valid_payload_is_canonical(self) -> None:
        result = validate_semantic_proposals(_valid_payload(), {"tone": 1.0})
        self.assertEqual(result["clips"][0]["clip_id"], "tone")

    def test_unknown_field_is_rejected(self) -> None:
        payload = _valid_payload()
        payload["clips"][0]["surprise"] = "not allowed"
        with self.assertRaises(ProposalValidationError):
            validate_semantic_proposals(payload, {"tone": 1.0})

    def test_nonfinite_and_out_of_range_values_are_rejected(self) -> None:
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.subTest(value=value):
                payload = _valid_payload()
                payload["clips"][0]["regions"][0]["confidence"] = value
                with self.assertRaises(ProposalValidationError):
                    validate_semantic_proposals(payload, {"tone": 1.0})

    def test_overlap_amplification_is_rejected(self) -> None:
        payload = _valid_payload()
        region = payload["clips"][0]["regions"][0]
        payload["clips"][0]["regions"] = [copy.deepcopy(region) for _ in range(9)]
        with self.assertRaises(ProposalValidationError):
            validate_semantic_proposals(payload, {"tone": 1.0})

    def test_local_evidence_is_deterministic_and_auditable(self) -> None:
        sample_rate = 16000
        time = np.arange(sample_rate, dtype=np.float64) / sample_rate
        samples = np.rint(np.sin(2.0 * np.pi * 220.0 * time) * 12000.0).astype(
            np.int16
        )
        evidence_a = analyze_proxy_evidence(samples, sample_rate)
        evidence_b = analyze_proxy_evidence(samples, sample_rate)
        np.testing.assert_array_equal(
            evidence_a.periodic_times,
            evidence_b.periodic_times,
        )
        proposal = validate_semantic_proposals(_valid_payload(), {"tone": 1.0})
        audit = audit_proposals(proposal, {"tone": evidence_a})
        self.assertGreater(audit["totals"]["supported"], 0)


if __name__ == "__main__":
    unittest.main()
