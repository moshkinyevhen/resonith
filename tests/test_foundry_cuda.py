"""Strict CPU/GPU parity coverage for the optional R-149 Foundry backend."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

import numpy as np

from maf_p0.foundry_cuda import GainPhaseCudaFoundry
from maf_p0.motif_orbit import encode_gain_orbit_candidate
from maf_p0.native_core import NativeMain0Decoder


class FoundryCudaTests(unittest.TestCase):
    """Exercise the installed RTX backend when explicit paths are provided."""

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
