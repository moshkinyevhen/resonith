from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "reference"))

from maf_p0.stream_sections import (  # noqa: E402
    BCIB_HEADER,
    CachedCIBSBasis,
    pack_bcib,
    unpack_bcib,
)


class CachedCIBSBasisSectionTests(unittest.TestCase):
    def test_round_trip_is_exact_and_bounded(self) -> None:
        basis = CachedCIBSBasis(
            model_id="CIBS0-TEST-\N{GREEK SMALL LETTER MU}",
            latent=np.asarray([12, -7, 3, 19, -22, 6], dtype=np.int8),
            channels=1,
            samples_per_channel=256,
            expected_sha256=bytes(range(32)),
        )
        payload = pack_bcib(basis)
        self.assertEqual(BCIB_HEADER.size, 48)
        restored = unpack_bcib(payload)
        self.assertEqual(restored.model_id, basis.model_id)
        self.assertEqual(restored.channels, 1)
        self.assertEqual(restored.samples_per_channel, 256)
        self.assertEqual(restored.expected_sha256, bytes(range(32)))
        np.testing.assert_array_equal(restored.latent, basis.latent)
        self.assertFalse(restored.latent.flags.writeable)

    def test_flags_reserved_utf8_and_lengths_are_rejected(self) -> None:
        basis = CachedCIBSBasis(
            model_id="CIBS0-TEST",
            latent=np.asarray([1, -2], dtype=np.int8),
            channels=1,
            samples_per_channel=8,
            expected_sha256=bytes(32),
        )
        payload = bytearray(pack_bcib(basis))

        flagged = payload.copy()
        flagged[1] = 1
        with self.assertRaisesRegex(ValueError, "feature"):
            unpack_bcib(bytes(flagged))

        reserved = payload.copy()
        reserved[6] = 1
        with self.assertRaisesRegex(ValueError, "reserved"):
            unpack_bcib(bytes(reserved))

        invalid_utf8 = payload.copy()
        invalid_utf8[BCIB_HEADER.size] = 0xFF
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            unpack_bcib(bytes(invalid_utf8))

        with self.assertRaisesRegex(ValueError, "size"):
            unpack_bcib(bytes(payload[:-1]))

    def test_invalid_latent_shape_and_hash_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            CachedCIBSBasis(
                model_id="CIBS0-TEST",
                latent=np.zeros((1, 2), dtype=np.int8),
                channels=1,
                samples_per_channel=8,
                expected_sha256=bytes(32),
            )
        with self.assertRaisesRegex(ValueError, "32 bytes"):
            CachedCIBSBasis(
                model_id="CIBS0-TEST",
                latent=np.zeros(2, dtype=np.int8),
                channels=1,
                samples_per_channel=8,
                expected_sha256=bytes(31),
            )


if __name__ == "__main__":
    unittest.main()
