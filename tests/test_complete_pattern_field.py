"""R-151 complete multiscale search and global-selection tests."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

import numpy as np

from maf_p0.complete_pattern_field import (
    PatternLanguage,
    PatternLocation,
    PatternMatch,
    PatternRdoCandidate,
    PatternScale,
    assert_cpu_gpu_parity,
    encode_complete_pattern_field_candidate,
    search_complete_pattern_field,
    select_complete_pattern_cover,
)
from maf_p0.foundry_cuda import GainPhaseCudaFoundry
from maf_p0.native_core import NativeMain0Decoder


def _foundry() -> GainPhaseCudaFoundry | None:
    library = os.environ.get("RESONITH_FOUNDRY_LIBRARY")
    nvrtc = os.environ.get("RESONITH_NVRTC_DIRECTORY")
    if not library or not nvrtc:
        return None
    return GainPhaseCudaFoundry(Path(library), Path(nvrtc))


def _decoder() -> NativeMain0Decoder | None:
    library = os.environ.get("RESONITH_NATIVE_CORE")
    return NativeMain0Decoder(Path(library)) if library else None


class CompletePatternFieldTests(unittest.TestCase):
    def test_global_chart_prefers_quality_priced_large_span(self) -> None:
        large = PatternMatch(
            8,
            PatternLocation(0, 8),
            PatternLocation(0, 0),
            0,
            32768,
            None,
            0,
            1,
        )
        micro_a = PatternMatch(
            4,
            PatternLocation(0, 8),
            PatternLocation(0, 0),
            0,
            32768,
            None,
            0,
            1,
        )
        micro_b = PatternMatch(
            4,
            PatternLocation(0, 12),
            PatternLocation(0, 4),
            0,
            32768,
            None,
            0,
            1,
        )
        result = select_complete_pattern_cover(
            8,
            1,
            (4,) * 8,
            (
                PatternRdoCandidate(large, "large", 4, 4),
                PatternRdoCandidate(micro_a, "micro", 20, 1),
                PatternRdoCandidate(micro_b, "micro", 20, 1),
            ),
        )
        self.assertEqual(result.selection.complete_bytes, 8)
        self.assertEqual(result.selection.activated_basis_ids, ("large",))

    def test_cross_channel_reuse_pays_one_activation(self) -> None:
        matches = tuple(
            PatternRdoCandidate(
                PatternMatch(
                    4,
                    PatternLocation(0, 0),
                    PatternLocation(channel, 0),
                    0,
                    32768,
                    None,
                    0,
                    1,
                ),
                "shared",
                6,
                1,
            )
            for channel in (0, 1)
        )
        result = select_complete_pattern_cover(
            4,
            2,
            (3,) * 8,
            matches,
        )
        self.assertEqual(result.selection.complete_bytes, 8)
        self.assertEqual(result.selection.activated_basis_ids, ("shared",))

    def test_dominated_basis_is_rejected_by_safe_upper_bound(self) -> None:
        match = PatternMatch(
            4,
            PatternLocation(0, 4),
            PatternLocation(0, 0),
            0,
            32768,
            None,
            0,
            1,
        )
        result = select_complete_pattern_cover(
            4,
            1,
            (1,) * 4,
            (PatternRdoCandidate(match, "bad", 8, 2),),
        )
        self.assertEqual(result.safely_rejected_basis_count, 1)
        self.assertEqual(result.selection.complete_bytes, 4)

    @unittest.skipUnless(_foundry() is not None, "CUDA Foundry is optional")
    def test_all_scales_origins_channels_and_known_laws_are_recalled(self) -> None:
        foundry = _foundry()
        assert foundry is not None
        base = np.asarray((100, -240, 500, -800), dtype=np.int16)
        channel_zero = np.concatenate(
            (
                base,
                np.rint(base.astype(np.float64) * -0.5).astype(np.int16),
            )
        )
        channel_one = np.concatenate((base[::-1], base))
        source = np.column_stack((channel_zero, channel_one))
        language = PatternLanguage(
            (
                PatternScale(4, 1),
                PatternScale(8, 1),
            ),
            maximum_normalized_error=0.0,
        )
        result = search_complete_pattern_field(
            source,
            language=language,
            foundry=foundry,
            tile_candidates=73,
        )
        expected = 0
        for scale in language.scales:
            blocks = (
                (source.shape[0] - scale.samples) // scale.origin_step + 1
            ) * source.shape[1]
            expected += foundry.candidate_count(blocks, scale.samples)
        self.assertEqual(result.candidate_count, expected)
        self.assertEqual(result.executed_candidate_count, expected)
        self.assertTrue(
            any(
                item.scale_samples == 4
                and item.basis == PatternLocation(0, 0)
                and item.target == PatternLocation(1, 4)
                and item.squared_error == 0
                for item in result.matches
            )
        )
        self.assertEqual(
            assert_cpu_gpu_parity(
                source,
                language=language,
                foundry=foundry,
                tile_candidates=71,
            ),
            expected,
        )

    @unittest.skipUnless(
        _foundry() is not None and _decoder() is not None,
        "CUDA Foundry and native Core are optional",
    )
    def test_actual_mft1_truth_stream_beats_truth_on_exact_orbits(self) -> None:
        foundry = _foundry()
        decoder = _decoder()
        assert foundry is not None and decoder is not None
        rng = np.random.default_rng(151)
        basis = rng.integers(-12000, 12001, size=64, dtype=np.int16)
        blocks = [
            np.roll(basis, -(5 * index % basis.size))
            if index % 3
            else basis[::-1]
            for index in range(12)
        ]
        source = np.concatenate(blocks).astype(np.int16)[:, None]
        search = search_complete_pattern_field(
            source,
            language=PatternLanguage(
                (PatternScale(64, 64),),
                maximum_normalized_error=0.0,
            ),
            foundry=foundry,
            tile_candidates=137,
        )
        candidate = encode_complete_pattern_field_candidate(
            source,
            48000,
            search=search,
            native_decoder=decoder,
            truth_block_sizes=(1024,),
        )
        np.testing.assert_array_equal(candidate.reconstruction, source)
        self.assertEqual(candidate.selected_kind, "complete-pattern-field")
        self.assertLess(
            candidate.report["structured_complete_bytes"],
            candidate.report["independent_truth_bytes"],
        )


if __name__ == "__main__":
    unittest.main()
