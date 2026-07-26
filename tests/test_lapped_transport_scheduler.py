from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lapped_transport_scheduler import (  # noqa: E402
    LappedTransportScheduler,
)


def scheduler() -> LappedTransportScheduler:
    return LappedTransportScheduler(
        frame_count=160,
        packet_frames=64,
        packet_count=3,
        half_window=32,
        maximum_reorder_records=2,
    )


class LappedTransportSchedulerTests(unittest.TestCase):
    def test_reversed_arrival_reuses_lookahead_as_next_current(self) -> None:
        value = scheduler()
        value.ingest(1, b"one", authenticated=True)
        value.ingest(0, b"zero", authenticated=True)
        first = value.decide_and_advance()
        self.assertEqual(first.action, "decode_pair")
        self.assertEqual(first.current_record, b"zero")
        self.assertEqual(first.lookahead_record, b"one")
        self.assertEqual(value.buffered_record_count, 1)

        value.ingest(2, b"two", authenticated=True)
        second = value.decide_and_advance()
        third = value.decide_and_advance()
        self.assertEqual(second.action, "decode_pair")
        self.assertEqual(second.current_record, b"one")
        self.assertEqual(second.lookahead_record, b"two")
        self.assertEqual(third.action, "decode_pair")
        self.assertEqual(third.logical_frames, 32)
        self.assertIsNone(third.lookahead_record)
        self.assertTrue(value.complete)

    def test_missing_middle_salvages_prefix_and_future_truth(self) -> None:
        value = scheduler()
        value.ingest(0, b"zero", authenticated=True)
        value.ingest(2, b"two", authenticated=True)
        first = value.decide_and_advance()
        missing = value.decide_and_advance()
        final = value.decide_and_advance()
        self.assertEqual(first.action, "decode_prefix")
        self.assertEqual(first.exact_frames, 32)
        self.assertEqual(first.concealed_frames, 32)
        self.assertEqual(missing.action, "conceal")
        self.assertEqual(missing.concealed_frames, 64)
        self.assertEqual(final.action, "decode_pair")
        self.assertEqual(final.exact_frames, 32)
        self.assertEqual(
            first.exact_frames + missing.exact_frames + final.exact_frames,
            64,
        )

    def test_late_record_can_recover_its_own_interval(self) -> None:
        value = scheduler()
        value.ingest(0, b"zero", authenticated=True)
        value.ingest(2, b"two", authenticated=True)
        first = value.decide_and_advance()
        self.assertEqual(first.action, "decode_prefix")
        value.ingest(1, b"one", authenticated=True)
        recovered = value.decide_and_advance()
        self.assertEqual(recovered.action, "decode_pair")
        self.assertEqual(recovered.current_record, b"one")
        self.assertEqual(recovered.lookahead_record, b"two")

    def test_authentication_replay_late_and_window_bounds(self) -> None:
        value = scheduler()
        with self.assertRaisesRegex(ValueError, "not transport-authenticated"):
            value.ingest(0, b"zero", authenticated=False)
        with self.assertRaisesRegex(ValueError, "outside"):
            value.ingest(3, b"three", authenticated=True)
        value.ingest(0, b"zero", authenticated=True)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            value.ingest(0, b"zero", authenticated=True)
        value.decide_and_advance()
        with self.assertRaisesRegex(ValueError, "after its playout"):
            value.ingest(0, b"zero", authenticated=True)

        late = scheduler()
        late.decide_and_advance()
        with self.assertRaisesRegex(ValueError, "after its playout"):
            late.ingest(0, b"zero", authenticated=True)

        narrow = LappedTransportScheduler(
            frame_count=256,
            packet_frames=64,
            packet_count=4,
            half_window=32,
            maximum_reorder_records=1,
        )
        with self.assertRaisesRegex(ValueError, "reordering window"):
            narrow.ingest(2, b"two", authenticated=True)

    def test_invalid_shape_and_completion_are_explicit(self) -> None:
        with self.assertRaises(ValueError):
            LappedTransportScheduler(
                frame_count=160,
                packet_frames=63,
                packet_count=3,
                half_window=32,
                maximum_reorder_records=2,
            )
        value = scheduler()
        for _packet in range(3):
            value.decide_and_advance()
        with self.assertRaises(LookupError):
            value.decide_and_advance()


if __name__ == "__main__":
    unittest.main()
