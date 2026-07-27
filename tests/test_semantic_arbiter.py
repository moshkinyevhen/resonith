"""Adversarial tests for the optional semantic-provider trust boundary."""

from __future__ import annotations

import copy
import unittest

import numpy as np

from maf_p0.semantic_arbiter import (
    ProposalValidationError,
    align_event_boundaries,
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
                        "acoustic_style": "steady_tonal",
                    }
                ],
                "events": [],
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
        self.assertEqual(audit["totals"]["proposed_boundaries"], 0)

    def test_changing_long_form_clip_requires_event_ledger(self) -> None:
        payload = _valid_payload()
        clip = payload["clips"][0]
        clip["duration_seconds"] = 6.0
        clip["primary_class"] = "music"
        clip["sources"][0]["end_seconds"] = 6.0
        clip["regions"][0]["end_seconds"] = 6.0
        clip["regions"][0]["lifetime_seconds"] = 6.0
        with self.assertRaises(ProposalValidationError):
            validate_semantic_proposals(payload, {"tone": 6.0})

    def test_event_source_reference_is_validated(self) -> None:
        payload = _valid_payload()
        payload["clips"][0]["events"] = [
            {
                "time_seconds": 0.5,
                "event_type": "timbre_change",
                "source_id": "missing",
                "acoustic_style": "transition",
                "primary_basis": "coherent",
                "change_strength": 0.7,
                "confidence": 0.8,
            }
        ]
        with self.assertRaises(ProposalValidationError):
            validate_semantic_proposals(payload, {"tone": 1.0})

    def test_coarse_event_is_aligned_to_millisecond_local_step(self) -> None:
        sample_rate = 16000
        samples = np.zeros(sample_rate, dtype=np.int16)
        exact_boundary = sample_rate // 2 + 7
        samples[exact_boundary:] = 12000
        event = {
            "time_seconds": 0.460,
            "event_type": "source_start",
            "source_id": "s0",
            "primary_basis": "coherent",
        }
        result = align_event_boundaries(samples, sample_rate, [event])
        aligned = result["events"][0]
        self.assertEqual(aligned["aligned_sample"], exact_boundary)
        self.assertIn(exact_boundary, aligned["candidate_samples"])
        self.assertLessEqual(aligned["candidate_count"], 256)
        self.assertTrue(aligned["no_boundary_candidate"])
        self.assertEqual(
            result["summary"]["exact_candidate_resolution_samples"],
            1,
        )
        self.assertTrue(aligned["supported"])

    def test_pitch_change_produces_exact_sample_rdo_neighborhood(self) -> None:
        sample_rate = 48000
        exact_boundary = sample_rate // 2 + 13
        time = np.arange(sample_rate, dtype=np.float64) / sample_rate
        samples = np.rint(np.sin(2.0 * np.pi * 220.0 * time) * 10000.0)
        samples[exact_boundary:] = np.rint(
            np.sin(2.0 * np.pi * 880.0 * time[exact_boundary:]) * 10000.0
        )
        event = {
            "time_seconds": 0.487,
            "event_type": "pitch_regime_change",
            "source_id": "s0",
            "primary_basis": "coherent",
        }
        result = align_event_boundaries(
            samples.astype(np.int16),
            sample_rate,
            [event],
        )
        candidates = result["events"][0]["candidate_samples"]
        self.assertTrue(
            any(abs(candidate - exact_boundary) <= 1 for candidate in candidates)
        )

    def test_none_specialist_placeholder_is_canonicalized_away(self) -> None:
        payload = _valid_payload()
        payload["clips"][0]["specialist_tasks"] = [
            {
                "provider": "none",
                "task": "none",
                "start_seconds": 0.0,
                "end_seconds": 1.0,
                "confidence": 1.0,
            }
        ]
        result = validate_semantic_proposals(payload, {"tone": 1.0})
        self.assertEqual(result["clips"][0]["specialist_tasks"], [])


if __name__ == "__main__":
    unittest.main()
