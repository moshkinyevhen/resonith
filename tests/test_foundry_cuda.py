"""Strict CPU/GPU parity coverage for the optional R-149 Foundry backend."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

import numpy as np

from maf_p0.foundry_cuda import GainPhaseCudaFoundry
from maf_p0.gridless_pattern_field import (
    GridlessOriginSet,
    GridlessPatternField,
    discover_gridless_pattern_field,
    encode_gridless_exact_prediction,
)
from maf_p0.gridless_matching import (
    discover_gridless_partial_spectrum,
    discover_gridless_warp_proposals,
)
from maf_p0.motif_orbit import encode_gain_orbit_candidate
from maf_p0.native_core import NativeMain0Decoder
from maf_p0.gridless_truth_rdo import (
    encode_gridless_truth_candidate,
    search_gridless_warp_field,
)


class FoundryCudaTests(unittest.TestCase):
    """Exercise the installed RTX backend when explicit paths are provided."""

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY"),
        "strict Foundry paths are not configured",
    )
    def test_gridless_hash_covers_cross_tile_origins(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        source = (
            (np.arange(96, dtype=np.int64) * 7919) % 30011 - 15000
        ).astype(np.int16)
        source[61:73] = source[13:25]
        hashes = foundry.rolling_hashes(source, window_samples=12)
        self.assertEqual(hashes.size, source.size - 11)
        self.assertEqual(int(hashes[13]), int(hashes[61]))
        # Origin 13 crosses the notional 16-sample tile boundary.
        np.testing.assert_array_equal(source[13:25], source[61:73])
        anchors = foundry.content_defined_anchors(
            hashes,
            selection_window=7,
        )
        self.assertGreater(anchors.size, 0)
        self.assertTrue(np.all(anchors[1:] > anchors[:-1]))

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY")
        and os.environ.get("RESONITH_NATIVE_CORE"),
        "strict Foundry paths are not configured",
    )
    def test_multiscale_field_verifies_arbitrary_cross_channel_span(
        self,
    ) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        position = np.arange(256, dtype=np.int64)
        source = np.column_stack(
            (
                ((position * 7919 + 11) % 30011 - 15000),
                ((position * 3571 + 29) % 28001 - 14000),
            )
        ).astype(np.int16)
        source[151:215, 1] = source[29:93, 0]
        field = discover_gridless_pattern_field(
            source,
            foundry=foundry,
            scales=(16, 64),
            regular_hop_divisor=4,
            anchor_window_divisor=2,
        )
        locations = {
            (item.channel, item.start, item.sample_count)
            for group in field.exact_groups
            for item in group.locations
        }
        self.assertIn((0, 29, 64), locations)
        self.assertIn((1, 151, 64), locations)
        self.assertEqual(field.report["rolling_origin_count"], 868)
        self.assertTrue(field.report["gridless_meaning"])
        prediction = encode_gridless_exact_prediction(
            source,
            48000,
            field,
            native_decoder=NativeMain0Decoder(
                Path(os.environ["RESONITH_NATIVE_CORE"])
            ),
        )
        self.assertGreaterEqual(prediction.report["basis_count"], 1)
        self.assertGreaterEqual(prediction.report["instance_count"], 2)
        np.testing.assert_array_equal(
            prediction.reconstruction[29:93, 0],
            source[29:93, 0],
        )
        np.testing.assert_array_equal(
            prediction.reconstruction[151:215, 1],
            source[151:215, 1],
        )

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY"),
        "strict Foundry paths are not configured",
    )
    def test_gridless_phase_matching_and_partial_bands(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        source = (
            (np.arange(512 * 2, dtype=np.int64) * 3571 + 101)
            % 20011 - 10000
        ).reshape(512, 2).astype(np.int16)
        position = np.arange(64, dtype=np.float64)
        basis = np.rint(
            7000.0 * np.sin(2.0 * np.pi * 5.0 * position / 64.0)
            + 1700.0 * np.sin(2.0 * np.pi * 17.0 * position / 64.0)
        ).astype(np.int16)
        source[13:77, 0] = basis
        source[151:215, 1] = -np.roll(basis, 9)
        field = discover_gridless_pattern_field(
            source,
            foundry=foundry,
            scales=(64,),
            regular_hop_divisor=64,
            anchor_window_divisor=2,
        )
        warped = discover_gridless_warp_proposals(
            source,
            field,
            maximum_normalized_error=0.0,
        )
        relations = {
            (
                item.basis.channel,
                item.basis.start,
                item.target.channel,
                item.target.start,
            )
            for item in warped.proposals
        }
        self.assertIn((0, 13, 1, 151), relations)
        self.assertGreaterEqual(
            warped.report["cross_channel_proposal_count"],
            1,
        )
        partial = discover_gridless_partial_spectrum(
            source,
            foundry=foundry,
            levels=2,
            scales=(16, 32),
        )
        self.assertTrue(partial.report["perfect_reconstruction"])
        self.assertEqual(partial.report["band_count"], 3)

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY"),
        "strict CUDA paths are not configured",
    )
    def test_exhaustive_candidate_cardinality_and_known_transform(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        basis = (
            (np.arange(32, dtype=np.int64) * 7919) % 24001 - 12000
        ).astype(np.int16)
        target = np.roll(basis, -7).astype(np.int64)
        product = target * -16384
        target = np.where(
            product >= 0,
            (product + 16384) // 32768,
            -((-product + 16384) // 32768),
        ).astype(np.int16)
        blocks = np.stack(
            (
                basis,
                target,
                np.arange(32, dtype=np.int16),
                -np.arange(32, dtype=np.int16),
            )
        )
        tiles = list(foundry.evaluate_tiles(blocks, tile_candidates=73))
        results = np.concatenate([tile for tile, _ in tiles])
        self.assertEqual(results.size, 4 * 3 * 32 * 2)
        known = results[
            (results["basis_index"] == 0)
            & (results["target_index"] == 1)
            & (results["source_offset"] == 7)
            & ((results["transform_flags"] & 2) == 0)
        ]
        self.assertEqual(known.size, 1)
        self.assertEqual(int(known["gain_q15"][0]), -16384)
        self.assertEqual(int(known["squared_error"][0]), 0)
        self.assertTrue(all(evidence.nvrtc == "13.3" for _, evidence in tiles))

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY"),
        "strict CUDA paths are not configured",
    )
    def test_r157_fractional_warp_cpu_gpu_parity(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        basis = (
            (np.arange(16, dtype=np.int64) * 5279 + 101) % 22001 - 11000
        ).astype(np.int16)
        blocks = np.stack(
            (
                basis,
                np.roll(basis, -3),
                np.arange(16, dtype=np.int16) * 97 - 700,
            )
        )
        parameters = {
            "phase_subsamples": 4,
            "step_radius": 1,
            "step_increment_q16": 512,
            "end_step_radius": 1,
            "tile_candidates": 4099,
        }
        gpu_tiles = list(foundry.evaluate_warp_tiles(blocks, **parameters))
        cpu_tiles = list(
            foundry.evaluate_warp_cpu_tiles(blocks, **parameters)
        )
        gpu = np.concatenate([item for item, _ in gpu_tiles])
        cpu = np.concatenate(cpu_tiles)
        self.assertEqual(gpu.size, 6912)
        np.testing.assert_array_equal(gpu, cpu)
        self.assertEqual(
            [evidence.candidate_count for _, evidence in gpu_tiles],
            [4099, 2813],
        )
        self.assertTrue(
            all(
                evidence.device_name == "NVIDIA GeForce RTX 2080 SUPER"
                for _, evidence in gpu_tiles
            )
        )

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY")
        and os.environ.get("RESONITH_NATIVE_CORE"),
        "strict CUDA/Core paths are not configured",
    )
    def test_gridless_warp_global_truth_rdo_is_exact(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        decoder = NativeMain0Decoder(
            Path(os.environ["RESONITH_NATIVE_CORE"])
        )
        frames = 640
        sample_count = 64
        starts = (13, 89, 165, 241, 317, 393, 469, 545)
        source = np.zeros((frames, 1), dtype=np.int16)
        basis = (
            (np.arange(sample_count, dtype=np.int64) * 5279 + 101)
            % 22001 - 11000
        ).astype(np.int16)
        for index, start in enumerate(starts):
            source[start : start + sample_count, 0] = np.roll(
                basis,
                -(index * 3 % sample_count),
            )
        field = GridlessPatternField(
            frames,
            1,
            (sample_count,),
            (
                GridlessOriginSet(
                    0,
                    sample_count,
                    frames - sample_count + 1,
                    0,
                    sample_count,
                    0,
                    starts,
                ),
            ),
            (),
            {
                "schema": "test-gridless-field",
                "gridless_meaning": True,
            },
        )
        search = search_gridless_warp_field(
            source,
            field=field,
            foundry=foundry,
            phase_subsamples=1,
            step_radius=0,
            step_increment_q16=512,
            end_step_radius=0,
            maximum_normalized_error=0.0,
            tile_candidates=8192,
        )
        self.assertEqual(
            search.report["candidate_count"],
            8 * 7 * sample_count * 2,
        )
        self.assertEqual(
            search.report["candidate_count"],
            search.report["executed_candidate_count"],
        )
        candidate = encode_gridless_truth_candidate(
            source,
            48000,
            search=search,
            native_decoder=decoder,
            truth_block_sizes=(256, 1024),
        )
        np.testing.assert_array_equal(candidate.reconstruction, source)
        self.assertTrue(candidate.report["exact_pcm"])
        self.assertLessEqual(
            len(candidate.maf_payload) + len(candidate.truth_payload),
            candidate.report["independent_truth_bytes"],
        )

    @unittest.skipUnless(
        os.environ.get("RESONITH_FOUNDRY_CUDA_LIBRARY")
        and os.environ.get("RESONITH_NVRTC_DIRECTORY")
        and os.environ.get("RESONITH_NATIVE_CORE"),
        "strict CUDA/Core paths are not configured",
    )
    def test_complete_foundry_builds_an_exact_basis_stream(self) -> None:
        foundry = GainPhaseCudaFoundry(
            Path(os.environ["RESONITH_FOUNDRY_CUDA_LIBRARY"]),
            Path(os.environ["RESONITH_NVRTC_DIRECTORY"]),
        )
        decoder = NativeMain0Decoder(
            Path(os.environ["RESONITH_NATIVE_CORE"])
        )
        length = 64
        position = np.arange(length, dtype=np.float64)
        basis = np.rint(
            9000.0 * np.sin(2.0 * np.pi * 5.0 * position / length)
            + 2100.0 * np.sin(2.0 * np.pi * 13.0 * position / length)
        ).astype(np.int64)
        blocks = []
        for index, gain in enumerate(
            (32768, 28672, -32768, 24576, 16384, -24576, 20480, 12288)
        ):
            shifted = np.roll(basis, -(3 * index % length))
            product = shifted * gain
            blocks.append(
                np.where(
                    product >= 0,
                    (product + 16384) // 32768,
                    -((-product + 16384) // 32768),
                )
            )
        source = np.concatenate(blocks).astype(np.int16)[:, None]
        candidate = encode_gain_orbit_candidate(
            source,
            48000,
            native_decoder=decoder,
            block_samples=length,
            truth_block_sizes=(1024,),
            maximum_normalized_error=0.0,
            search_mode="foundry",
            foundry=foundry,
            foundry_tile_candidates=64 * 56,
        )
        np.testing.assert_array_equal(candidate.reconstruction, source)
        self.assertEqual(candidate.report["basis_count"], 1)
        self.assertEqual(candidate.report["instance_count"], 8)
        discovery = candidate.report["discovery"]
        self.assertTrue(discovery["complete_hypothesis_language"])
        self.assertEqual(
            discovery["candidate_count"],
            discovery["executed_candidate_count"],
        )


if __name__ == "__main__":
    unittest.main()
