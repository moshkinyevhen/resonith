"""R-150 global hierarchy tests: small matches never blind larger laws."""

from __future__ import annotations

import unittest

from maf_p0.hierarchical_grammar import (
    GrammarSpan,
    StateAtom,
    discover_affine_state_compounds,
    discover_exact_compounds,
    discover_interval_compounds,
    select_minimum_description,
)


class HierarchicalGrammarTests(unittest.TestCase):
    def test_direct_large_span_replaces_discovered_micro_atoms(self) -> None:
        compounds = discover_exact_compounds(
            (1, 2, 1, 2),
            (0, 2, 4, 6, 8),
            maximum_atoms=2,
            placement_bytes=4,
            dictionary_bytes_per_atom=5,
        )
        direct_large = GrammarSpan(0, 8, 12, "direct-large")
        selected = select_minimum_description(
            8,
            (10,) * 8,
            (*compounds.spans, direct_large),
            compounds.basis_activation_bytes,
        )
        self.assertEqual(selected.complete_bytes, 12)
        self.assertEqual(
            tuple(item.label for item in selected.selected_spans),
            ("direct-large",),
        )

    def test_global_chart_avoids_locally_attractive_merge(self) -> None:
        spans = (
            GrammarSpan(0, 4, 1, "local-a", "expensive-basis"),
            GrammarSpan(4, 8, 1, "local-b", "expensive-basis"),
            GrammarSpan(0, 8, 15, "global-direct"),
        )
        selected = select_minimum_description(
            8,
            (10,) * 8,
            spans,
            {"expensive-basis": 20},
        )
        self.assertEqual(selected.complete_bytes, 15)
        self.assertEqual(selected.selected_spans[0].label, "global-direct")

    def test_existing_compound_basis_is_reused_without_activation(self) -> None:
        first = discover_exact_compounds(
            (4, 9, 4, 9),
            (0, 1, 2, 3, 4),
            maximum_atoms=2,
            placement_bytes=2,
            dictionary_bytes_per_atom=20,
        )
        basis_id = next(iter(first.basis_activation_bytes))
        reused = discover_exact_compounds(
            (4, 9, 4, 9),
            (0, 1, 2, 3, 4),
            maximum_atoms=2,
            placement_bytes=2,
            dictionary_bytes_per_atom=20,
            existing_basis_ids=(basis_id,),
        )
        selected = select_minimum_description(
            4,
            (10,) * 4,
            reused.spans,
            reused.basis_activation_bytes,
        )
        self.assertEqual(selected.complete_bytes, 4)
        self.assertEqual(selected.activated_basis_ids, (basis_id,))

    def test_truth_fallback_wins_when_no_merge_is_economic(self) -> None:
        selected = select_minimum_description(
            3,
            (2, 2, 2),
            (GrammarSpan(0, 3, 9, "bad-merge"),),
            {},
        )
        self.assertEqual(selected.complete_bytes, 6)
        self.assertEqual(selected.selected_spans, ())
        self.assertEqual(selected.truth_positions, (0, 1, 2))

    def test_long_sparse_chart_has_no_recursion_or_dense_path_copy(self) -> None:
        selected = select_minimum_description(
            20000,
            (2,) * 20000,
            (GrammarSpan(10003, 14003, 2000, "long-basis"),),
            {},
        )
        self.assertEqual(selected.complete_bytes, 34000)
        self.assertEqual(
            tuple(item.label for item in selected.selected_spans),
            ("long-basis",),
        )
        self.assertNotIn(10003, selected.truth_positions)
        self.assertIn(10002, selected.truth_positions)
        self.assertIn(14003, selected.truth_positions)

    def test_state_increments_unify_different_absolute_placements(self) -> None:
        atoms = (
            StateAtom(1, 5, 100),
            StateAtom(2, 8, 110),
            StateAtom(3, 13, 130),
            StateAtom(1, 50, 200),
            StateAtom(2, 53, 210),
            StateAtom(3, 58, 230),
        )
        compounds = discover_affine_state_compounds(
            atoms,
            tuple(range(7)),
            maximum_atoms=3,
            placement_bytes=3,
            dictionary_bytes_per_atom=2,
            increment_bytes=1,
        )
        selected = select_minimum_description(
            6,
            (10,) * 6,
            compounds.spans,
            compounds.basis_activation_bytes,
        )
        self.assertGreaterEqual(compounds.repeated_sequence_count, 1)
        self.assertEqual(len(selected.selected_spans), 2)
        self.assertLess(selected.complete_bytes, 60)

    def test_arbitrary_interval_paths_form_compounds_without_blindness(
        self,
    ) -> None:
        atoms = (
            GrammarSpan(3, 7, 3, "a@3", "a"),
            GrammarSpan(7, 12, 3, "b@7", "b"),
            GrammarSpan(19, 23, 3, "a@19", "a"),
            GrammarSpan(23, 28, 3, "b@23", "b"),
            # This overlapping alternative must remain in the chart.
            GrammarSpan(3, 12, 7, "direct@3"),
        )
        compounds = discover_interval_compounds(
            atoms,
            minimum_atoms=2,
            maximum_atoms=3,
            placement_bytes=2,
            dictionary_bytes_per_atom=1,
        )
        compound_ranges = {
            (span.start, span.end) for span in compounds.spans
        }
        self.assertIn((3, 12), compound_ranges)
        self.assertIn((19, 28), compound_ranges)
        selected = select_minimum_description(
            32,
            (10,) * 32,
            (*atoms, *compounds.spans),
            {"a": 0, "b": 0, **compounds.basis_activation_bytes},
        )
        selected_ranges = {
            (span.start, span.end) for span in selected.selected_spans
        }
        self.assertIn((3, 12), selected_ranges)
        self.assertIn((19, 28), selected_ranges)
        self.assertLess(selected.complete_bytes, 320)


if __name__ == "__main__":
    unittest.main()
