from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.composition import GainEventLaw, compose_truth  # noqa: E402
from maf_p0.main0 import (  # noqa: E402
    Main0State,
    decode_main0_raw_stream,
    pack_main0_raw_stream,
    pack_main0_state_stream,
)
from maf_p0.periodic import PhaseTrajectory, render_basis_trajectory  # noqa: E402
from maf_p0.rsc1 import RSC1Section, pack_rsc1, parse_rsc1  # noqa: E402
from maf_p0.stream_sections import (  # noqa: E402
    PeriodicAtom,
    StreamConfig,
    pack_conf,
    pack_periodic_atom,
    unpack_conf,
    unpack_periodic_atom,
)


class Main0StreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.basis = np.asarray(
            [
                -30000,
                -20000,
                -10000,
                0,
                10000,
                20000,
                30000,
                20000,
                10000,
                0,
                -10000,
                -20000,
                -30000,
                -15000,
                0,
                15000,
            ],
            dtype=np.int16,
        )
        self.trajectory = PhaseTrajectory(
            np.asarray([0, 5, 17, 40], dtype=np.int64),
            np.asarray(
                [0x08000000, 0x10000000, 0x06000000, 0x18000000],
                dtype=np.uint32,
            ),
            0x1234_5678,
        )
        self.gain = GainEventLaw(
            np.asarray([0, 7, 23, 35], dtype=np.uint32),
            np.asarray([32768, 24576, -16384, 49152], dtype=np.int32),
            40,
        )
        self.innovation = np.asarray(
            [
                -7,
                -3,
                0,
                2,
                5,
                9,
                13,
                -4,
                1,
                2,
                -1,
                0,
                4,
                -2,
                8,
                1,
                -3,
                2,
                5,
                -4,
                0,
                7,
                -8,
                6,
                5,
                4,
                3,
                2,
                1,
                0,
                -1,
                -2,
                -3,
                -4,
                -5,
                15,
                -16,
                30,
                -30,
                50,
            ],
            dtype=np.int64,
        )

    def test_typed_sections_round_trip(self) -> None:
        config = StreamConfig(40, 3, 1)
        self.assertEqual(unpack_conf(pack_conf(config)), config)
        atom = PeriodicAtom(7, self.trajectory, self.gain)
        restored = unpack_periodic_atom(pack_periodic_atom(atom))
        self.assertEqual(restored.basis_instance_id, 7)
        np.testing.assert_array_equal(
            restored.trajectory.positions,
            self.trajectory.positions,
        )
        np.testing.assert_array_equal(
            restored.trajectory.increments_q32,
            self.trajectory.increments_q32,
        )
        np.testing.assert_array_equal(
            restored.gain_law.gains_q15,
            self.gain.gains_q15,
        )

    def test_whole_rsc1_decode_matches_direct_truth_path(self) -> None:
        stream = pack_main0_raw_stream(
            sample_rate=48_000,
            basis=self.basis,
            trajectory=self.trajectory,
            gain_law=self.gain,
            innovation_q=self.innovation,
            innovation_step=3,
            residual_block_size=16,
        )
        decoded = decode_main0_raw_stream(stream)
        direct = compose_truth(
            render_basis_trajectory(self.basis, self.trajectory),
            self.gain,
            innovation_q=self.innovation,
            innovation_step=3,
        )
        self.assertEqual(decoded.sample_rate, 48_000)
        np.testing.assert_array_equal(decoded.samples, direct)
        self.assertEqual(
            [bytes(section.type_code) for section in parse_rsc1(stream).sections],
            [b"ATOM", b"BRAW", b"CONF", b"RSL1"],
        )

    def test_state_partition_reuses_one_basis_and_covers_time_exactly(self) -> None:
        first_phase = PhaseTrajectory(
            np.asarray([0, 5, 17], dtype=np.int64),
            self.trajectory.increments_q32[:3],
            self.trajectory.phase_origin_q32,
        )
        second_phase = PhaseTrajectory(
            np.asarray([0, 23], dtype=np.int64),
            np.asarray([0x18000000, 0x18000000], dtype=np.uint32),
            0x7777_0000,
        )
        first_gain = GainEventLaw(
            np.asarray([0, 7], dtype=np.uint32),
            np.asarray([32768, 24576], dtype=np.int32),
            17,
        )
        second_gain = GainEventLaw(
            np.asarray([0, 18], dtype=np.uint32),
            np.asarray([-16384, 49152], dtype=np.int32),
            23,
        )
        stream = pack_main0_state_stream(
            sample_rate=48_000,
            states=(
                Main0State(self.basis, first_phase, first_gain),
                Main0State(self.basis.copy(), second_phase, second_gain),
            ),
            innovation_q=self.innovation,
            innovation_step=3,
            residual_block_size=16,
        )
        parsed = parse_rsc1(stream)
        atoms = [
            section
            for section in parsed.sections
            if bytes(section.type_code) == b"ATOM"
        ]
        bases = [
            section
            for section in parsed.sections
            if bytes(section.type_code) == b"BRAW"
        ]
        self.assertEqual([section.start_tick for section in atoms], [0, 17])
        self.assertEqual(len(bases), 1)
        decoded = decode_main0_raw_stream(stream)
        first = compose_truth(
            render_basis_trajectory(self.basis, first_phase),
            first_gain,
            innovation_q=self.innovation[:17],
            innovation_step=3,
        )
        second = compose_truth(
            render_basis_trajectory(self.basis, second_phase),
            second_gain,
            innovation_q=self.innovation[17:],
            innovation_step=3,
        )
        np.testing.assert_array_equal(
            decoded.samples,
            np.concatenate((first, second)),
        )

    def test_missing_or_unknown_critical_section_is_rejected(self) -> None:
        config_only = pack_rsc1([RSC1Section("CONF", pack_conf(StreamConfig(8, 1)))])
        with self.assertRaisesRegex(ValueError, "missing required"):
            decode_main0_raw_stream(config_only)
        unknown = pack_rsc1([RSC1Section("ZZZZ", b"critical")])
        with self.assertRaisesRegex(ValueError, "unknown critical"):
            decode_main0_raw_stream(unknown)

    def test_corrupt_atom_shape_and_cross_section_lifetime_are_rejected(self) -> None:
        atom = bytearray(
            pack_periodic_atom(PeriodicAtom(0, self.trajectory, self.gain))
        )
        atom[-1] ^= 1
        with self.assertRaises(ValueError):
            unpack_periodic_atom(bytes(atom))

        stream = pack_main0_raw_stream(
            sample_rate=48_000,
            basis=self.basis,
            trajectory=self.trajectory,
            gain_law=self.gain,
            innovation_q=self.innovation,
            innovation_step=3,
            residual_block_size=16,
        )
        parsed = parse_rsc1(stream)
        replaced = [
            RSC1Section(
                section.type_code,
                (
                    pack_conf(StreamConfig(39, 3))
                    if bytes(section.type_code) == b"CONF"
                    else section.payload
                ),
                section.instance_id,
                section.schema_version,
                section.flags,
                section.start_tick,
            )
            for section in parsed.sections
        ]
        with self.assertRaisesRegex(ValueError, "lifetime|sample count"):
            decode_main0_raw_stream(
                pack_rsc1(replaced, timebase_hz=parsed.timebase_hz)
            )


if __name__ == "__main__":
    unittest.main()
