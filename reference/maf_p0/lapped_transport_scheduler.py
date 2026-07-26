"""Bounded playout decisions for authenticated independent LPS4 records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LappedPlayoutDecision:
    packet_index: int
    logical_start: int
    logical_frames: int
    action: str
    exact_frames: int
    concealed_frames: int
    current_record: bytes | None
    lookahead_record: bytes | None


class LappedTransportScheduler:
    """Map bounded authenticated arrivals to exact Core calls or output gaps."""

    def __init__(
        self,
        *,
        frame_count: int,
        packet_frames: int,
        packet_count: int,
        half_window: int,
        maximum_reorder_records: int,
    ) -> None:
        expected_packets = (
            frame_count // packet_frames
            + (1 if frame_count % packet_frames else 0)
            if packet_frames > 0
            else 0
        )
        if (
            frame_count <= 0
            or packet_frames < half_window
            or half_window <= 0
            or packet_frames % half_window != 0
            or packet_count != expected_packets
            or maximum_reorder_records < 1
        ):
            raise ValueError("invalid LPS4 scheduler shape")
        self.frame_count = frame_count
        self.packet_frames = packet_frames
        self.packet_count = packet_count
        self.half_window = half_window
        self.maximum_reorder_records = maximum_reorder_records
        self.next_playout_packet = 0
        self._records: dict[int, bytes] = {}

    @property
    def buffered_record_count(self) -> int:
        return len(self._records)

    @property
    def complete(self) -> bool:
        return self.next_playout_packet == self.packet_count

    def ingest(
        self,
        packet_index: int,
        record: bytes,
        *,
        authenticated: bool,
    ) -> None:
        if not authenticated:
            raise ValueError("record is not transport-authenticated")
        if (
            not isinstance(packet_index, int)
            or isinstance(packet_index, bool)
            or packet_index < 0
            or packet_index >= self.packet_count
        ):
            raise ValueError("record packet index is outside sequence")
        if not isinstance(record, bytes) or not record:
            raise ValueError("record frame must be non-empty immutable bytes")
        if packet_index in self._records:
            raise ValueError("duplicate or replayed record")
        if packet_index < self.next_playout_packet:
            raise ValueError("record arrived after its playout interval")
        if (
            packet_index
            > self.next_playout_packet + self.maximum_reorder_records
        ):
            raise ValueError("record exceeds the bounded reordering window")
        self._records[packet_index] = record

    def decide_and_advance(self) -> LappedPlayoutDecision:
        if self.complete:
            raise LookupError("LPS4 playout is complete")
        packet_index = self.next_playout_packet
        logical_start = packet_index * self.packet_frames
        logical_frames = min(
            self.packet_frames,
            self.frame_count - logical_start,
        )
        final_packet = packet_index + 1 == self.packet_count
        current = self._records.get(packet_index)
        lookahead = self._records.get(packet_index + 1)
        if current is None:
            decision = LappedPlayoutDecision(
                packet_index,
                logical_start,
                logical_frames,
                "conceal",
                0,
                logical_frames,
                None,
                None,
            )
        elif final_packet or lookahead is not None:
            decision = LappedPlayoutDecision(
                packet_index,
                logical_start,
                logical_frames,
                "decode_pair",
                logical_frames,
                0,
                current,
                None if final_packet else lookahead,
            )
        else:
            exact_frames = max(0, logical_frames - self.half_window)
            decision = LappedPlayoutDecision(
                packet_index,
                logical_start,
                logical_frames,
                "decode_prefix",
                exact_frames,
                logical_frames - exact_frames,
                current,
                None,
            )

        self.next_playout_packet += 1
        self._records.pop(packet_index, None)
        return decision
