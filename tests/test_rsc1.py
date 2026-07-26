from __future__ import annotations

from pathlib import Path
import struct
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.rsc1 import (  # noqa: E402
    DIRECTORY_RECORD,
    HEADER,
    RSC1Section,
    pack_rsc1,
    parse_rsc1,
)


class RSC1Tests(unittest.TestCase):
    def test_sections_are_sorted_and_round_trip_exactly(self) -> None:
        payload = pack_rsc1(
            [
                RSC1Section("RSL1", b"residual", instance_id=4, start_tick=9),
                RSC1Section("CONF", b"configuration"),
            ],
            profile=2,
            level=3,
            timebase_hz=96_000,
        )
        info = parse_rsc1(payload)
        self.assertEqual((info.profile, info.level), (2, 3))
        self.assertEqual(info.timebase_hz, 96_000)
        self.assertEqual(
            [section.type_code for section in info.sections],
            [b"CONF", b"RSL1"],
        )
        self.assertEqual(info.sections[1].payload, b"residual")
        self.assertEqual(info.sections[1].start_tick, 9)

    def test_duplicate_keys_and_invalid_types_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            pack_rsc1(
                [
                    RSC1Section("RSL1", b"a", instance_id=1),
                    RSC1Section("RSL1", b"b", instance_id=1),
                ]
            )
        with self.assertRaisesRegex(ValueError, "uppercase"):
            pack_rsc1([RSC1Section("bad!", b"a")])

    def test_directory_and_section_corruption_are_rejected(self) -> None:
        payload = bytearray(pack_rsc1([RSC1Section("RSL1", b"truth")]))
        damaged_directory = bytearray(payload)
        damaged_directory[HEADER.size + 10] ^= 1
        with self.assertRaisesRegex(ValueError, "directory checksum"):
            parse_rsc1(bytes(damaged_directory))

        damaged_section = bytearray(payload)
        damaged_section[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "section checksum"):
            parse_rsc1(bytes(damaged_section))

    def test_noncanonical_offset_and_trailing_bytes_are_rejected(self) -> None:
        payload = bytearray(pack_rsc1([RSC1Section("RSL1", b"truth")]))
        fields = list(DIRECTORY_RECORD.unpack_from(payload, HEADER.size))
        fields[5] += 1
        DIRECTORY_RECORD.pack_into(payload, HEADER.size, *fields)
        header = list(HEADER.unpack_from(payload))
        import zlib

        directory = payload[HEADER.size : HEADER.size + DIRECTORY_RECORD.size]
        header[-1] = zlib.crc32(directory) & 0xFFFF_FFFF
        HEADER.pack_into(payload, 0, *header)
        with self.assertRaisesRegex(ValueError, "offset"):
            parse_rsc1(bytes(payload))

        valid = pack_rsc1([RSC1Section("RSL1", b"truth")])
        with self.assertRaisesRegex(ValueError, "trailing"):
            parse_rsc1(valid + b"\x00")

    def test_header_is_exactly_32_and_record_exactly_80_bytes(self) -> None:
        self.assertEqual(HEADER.size, 32)
        self.assertEqual(DIRECTORY_RECORD.size, 80)
        self.assertEqual(
            struct.calcsize("<4sBBBBIIIIII"),
            HEADER.size,
        )


if __name__ == "__main__":
    unittest.main()
