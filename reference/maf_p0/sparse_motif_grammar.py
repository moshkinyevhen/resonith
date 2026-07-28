"""R-160 exact sparse motif grammar for unnamed component-token events.

The research stream proves signalling economics independently of acoustic
classification. A motif may connect non-adjacent observations; intervening
events remain literal or belong to other motif/layer candidates.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING
import zlib

if TYPE_CHECKING:
    from .latent_source_field import LatentSourceField


FLAT_MAGIC = b"SEV1"
MOTIF_MAGIC = b"SMG1"
PATH_MAGIC = b"SPG1"
BASIS_GROUP_MAGIC = b"BSG1"


@dataclass(frozen=True)
class SparseMotifLanguage:
    """Finite pair-grammar language used by the first exact oracle."""

    minimum_occurrences: int = 3
    maximum_gap_frames: int = 1_048_576
    gap_bucket_frames: int = 256
    maximum_pair_candidates: int = 1 << 18

    def __post_init__(self) -> None:
        if not 2 <= self.minimum_occurrences <= 4096:
            raise ValueError("sparse motif occurrence bound is invalid")
        if not 1 <= self.maximum_gap_frames <= 1 << 30:
            raise ValueError("sparse motif gap bound is invalid")
        if not 1 <= self.gap_bucket_frames <= self.maximum_gap_frames:
            raise ValueError("sparse motif gap bucket is invalid")
        if not 1 <= self.maximum_pair_candidates <= 1 << 24:
            raise ValueError("sparse motif candidate bound is invalid")


@dataclass(frozen=True, order=True)
class ComponentTokenObservation:
    """One verified decoder-domain event in an unnamed additive layer."""

    observation_id: int
    layer_hypothesis_id: int
    token_id: int
    onset_frame: int
    support_frames: int
    channel: int
    gain_q15: int
    phase_q16: int = 0
    source_step_q16: int = 65536

    def __post_init__(self) -> None:
        if (
            self.observation_id < 0
            or self.layer_hypothesis_id < 0
            or self.token_id < 0
            or self.onset_frame < 0
            or self.support_frames <= 0
            or not 0 <= self.channel <= 7
        ):
            raise ValueError("invalid sparse motif observation")


@dataclass(frozen=True)
class SparseMotifDefinition:
    """One two-step gapped motif selected by actual event-stream bytes."""

    first_token_id: int
    second_token_id: int
    first_support_frames: int
    second_support_frames: int
    representative_gap_frames: int
    occurrence_count: int
    law_kinds: tuple[str, ...]


@dataclass(frozen=True)
class SparseMotifCandidate:
    """Exact event stream chosen between literal and motif syntax."""

    selected_kind: str
    definitions: tuple[SparseMotifDefinition, ...]
    packed_stream: bytes
    flat_stream_bytes: int
    motif_stream_bytes: int | None
    decoded_observations: tuple[ComponentTokenObservation, ...]
    report: dict


@dataclass(frozen=True)
class SparsePathLanguage:
    """Finite arbitrary-gap path language for CompoundBasis event macros."""

    minimum_occurrences: int = 3
    minimum_steps: int = 3
    maximum_steps: int = 8
    maximum_gap_frames: int = 1_048_576
    gap_bucket_frames: int = 256
    maximum_successors_per_step: int = 16
    maximum_path_candidates: int = 1 << 20

    def __post_init__(self) -> None:
        if not 2 <= self.minimum_occurrences <= 4096:
            raise ValueError("sparse path occurrence bound is invalid")
        if not 2 <= self.minimum_steps <= self.maximum_steps <= 16:
            raise ValueError("sparse path step bound is invalid")
        if not 1 <= self.maximum_gap_frames <= 1 << 30:
            raise ValueError("sparse path gap bound is invalid")
        if not 1 <= self.gap_bucket_frames <= self.maximum_gap_frames:
            raise ValueError("sparse path gap bucket is invalid")
        if not 1 <= self.maximum_successors_per_step <= 1024:
            raise ValueError("sparse path successor bound is invalid")
        if not 1 <= self.maximum_path_candidates <= 1 << 24:
            raise ValueError("sparse path candidate bound is invalid")


@dataclass(frozen=True)
class SparsePathDefinition:
    """One exact multi-step gapped path selected by serialized byte cost."""

    token_ids: tuple[int, ...]
    support_frames: tuple[int, ...]
    representative_gaps_frames: tuple[int, ...]
    occurrence_count: int
    law_kinds: tuple[str, ...]


@dataclass(frozen=True)
class SparsePathCandidate:
    """Exact event stream selected between literals and one path macro."""

    selected_kind: str
    definitions: tuple[SparsePathDefinition, ...]
    packed_stream: bytes
    flat_stream_bytes: int
    path_stream_bytes: int | None
    decoded_observations: tuple[ComponentTokenObservation, ...]
    report: dict


@dataclass(frozen=True)
class LatentFieldEventLedger:
    """One exact global event ledger derived from verified LSPF occurrences."""

    packed_stream: bytes
    decoded_observations: tuple[ComponentTokenObservation, ...]
    report: dict


def _varuint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned varint cannot encode a negative value")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _varsint(value: int) -> bytes:
    zigzag = (value << 1) if value >= 0 else ((-value << 1) - 1)
    return _varuint(zigzag)


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.cursor = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.cursor + count > len(self.payload):
            raise ValueError("truncated sparse motif stream")
        result = self.payload[self.cursor : self.cursor + count]
        self.cursor += count
        return result

    def varuint(self) -> int:
        value = 0
        shift = 0
        while shift <= 63:
            byte = self.take(1)[0]
            value |= (byte & 0x7F) << shift
            if byte < 0x80:
                return value
            shift += 7
        raise ValueError("sparse motif varint exceeds 64 bits")

    def varsint(self) -> int:
        value = self.varuint()
        return -(value // 2) - 1 if value & 1 else value // 2


def _finish(body: bytes) -> bytes:
    return body + (zlib.crc32(body) & 0xFFFF_FFFF).to_bytes(4, "little")


def _verify(payload: bytes) -> bytes:
    if len(payload) < 8:
        raise ValueError("truncated sparse motif stream")
    body = payload[:-4]
    checksum = int.from_bytes(payload[-4:], "little")
    if zlib.crc32(body) & 0xFFFF_FFFF != checksum:
        raise ValueError("sparse motif checksum mismatch")
    return body


def _event_key(
    item: ComponentTokenObservation,
) -> tuple[int, int, int, int, int, int, int, int]:
    return (
        item.layer_hypothesis_id,
        item.token_id,
        item.onset_frame,
        item.support_frames,
        item.channel,
        item.gain_q15,
        item.phase_q16,
        item.source_step_q16,
    )


def _pack_rows(
    observations: list[ComponentTokenObservation],
) -> bytes:
    ordered = sorted(
        observations,
        key=lambda item: (
            item.onset_frame,
            item.layer_hypothesis_id,
            item.token_id,
            item.channel,
            item.observation_id,
        ),
    )
    output = bytearray(_varuint(len(ordered)))
    previous_onset = 0
    for item in ordered:
        output.extend(_varuint(item.onset_frame - previous_onset))
        previous_onset = item.onset_frame
        output.extend(_varuint(item.layer_hypothesis_id))
        output.extend(_varuint(item.token_id))
        output.extend(_varuint(item.support_frames))
        output.extend(_varuint(item.channel))
        output.extend(_varsint(item.gain_q15))
        output.extend(_varsint(item.phase_q16))
        output.extend(_varsint(item.source_step_q16))
    return bytes(output)


def _unpack_rows(reader: _Reader) -> list[ComponentTokenObservation]:
    count = reader.varuint()
    previous_onset = 0
    result = []
    for observation_id in range(count):
        onset = previous_onset + reader.varuint()
        previous_onset = onset
        result.append(
            ComponentTokenObservation(
                observation_id,
                reader.varuint(),
                reader.varuint(),
                onset,
                reader.varuint(),
                reader.varuint(),
                reader.varsint(),
                reader.varsint(),
                reader.varsint(),
            )
        )
    return result


def pack_flat_observations(
    observations: list[ComponentTokenObservation],
) -> bytes:
    """Serialize one independently decodable literal event ledger."""

    return _finish(FLAT_MAGIC + _pack_rows(observations))


def pack_basis_grouped_observations(
    observations: list[ComponentTokenObservation],
) -> bytes:
    """Serialize persistent per-Basis state without repeating token metadata."""

    groups: dict[
        tuple[int, int],
        list[ComponentTokenObservation],
    ] = {}
    for item in observations:
        groups.setdefault(
            (item.token_id, item.support_frames),
            [],
        ).append(item)
    output = bytearray(BASIS_GROUP_MAGIC)
    output.extend(_varuint(len(groups)))
    for (token_id, support_frames), group in sorted(groups.items()):
        ordered = sorted(group, key=_event_key)
        output.extend(_varuint(token_id))
        output.extend(_varuint(support_frames))
        output.extend(_varuint(len(ordered)))
        fields = (
            [item.onset_frame for item in ordered],
            [item.layer_hypothesis_id for item in ordered],
            [item.channel for item in ordered],
            [item.gain_q15 for item in ordered],
            [item.phase_q16 for item in ordered],
            [item.source_step_q16 for item in ordered],
        )
        for values in fields:
            _append_series(output, values)
    return _finish(bytes(output))


def _pack_series(values: list[int]) -> tuple[str, bytes]:
    if not values:
        raise ValueError("cannot encode an empty sparse motif law")
    literal = bytearray((0,))
    for value in values:
        literal.extend(_varsint(value))
    candidates: list[tuple[str, bytes]] = [("literal", bytes(literal))]

    if all(value == values[0] for value in values):
        candidates.append(("constant", bytes((1,)) + _varsint(values[0])))

    if len(values) >= 2:
        delta = values[1] - values[0]
        if all(
            values[index] == values[0] + index * delta
            for index in range(len(values))
        ):
            candidates.append(
                (
                    "affine",
                    bytes((2,))
                    + _varsint(values[0])
                    + _varsint(delta),
                )
            )

    runs: list[tuple[int, int]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            runs[-1] = (value, runs[-1][1] + 1)
        else:
            runs.append((value, 1))
    run_payload = bytearray((3,))
    run_payload.extend(_varuint(len(runs)))
    for value, count in runs:
        run_payload.extend(_varsint(value))
        run_payload.extend(_varuint(count))
    candidates.append(("run_length", bytes(run_payload)))

    mode = Counter(values).most_common(1)[0][0]
    exceptions = [
        (index, value - mode)
        for index, value in enumerate(values)
        if value != mode
    ]
    sparse = bytearray((4,))
    sparse.extend(_varsint(mode))
    sparse.extend(_varuint(len(exceptions)))
    previous_index = 0
    for exception_index, difference in exceptions:
        sparse.extend(_varuint(exception_index - previous_index))
        sparse.extend(_varsint(difference))
        previous_index = exception_index
    candidates.append(("sparse_exception", bytes(sparse)))
    return min(candidates, key=lambda item: (len(item[1]), item[0]))


def _unpack_series(payload: bytes, count: int) -> list[int]:
    reader = _Reader(payload)
    tag = reader.take(1)[0]
    if tag == 0:
        values = [reader.varsint() for _ in range(count)]
    elif tag == 1:
        values = [reader.varsint()] * count
    elif tag == 2:
        first = reader.varsint()
        delta = reader.varsint()
        values = [first + index * delta for index in range(count)]
    elif tag == 3:
        values = []
        for _ in range(reader.varuint()):
            value = reader.varsint()
            values.extend([value] * reader.varuint())
        if len(values) != count:
            raise ValueError("sparse motif run length count mismatch")
    elif tag == 4:
        mode = reader.varsint()
        values = [mode] * count
        previous_index = 0
        for _ in range(reader.varuint()):
            index = previous_index + reader.varuint()
            if index >= count:
                raise ValueError("sparse motif exception index exceeds count")
            values[index] += reader.varsint()
            previous_index = index
    else:
        raise ValueError("unknown sparse motif law")
    if reader.cursor != len(payload):
        raise ValueError("trailing sparse motif law bytes")
    return values


def _append_series(
    output: bytearray,
    values: list[int],
) -> str:
    kind, payload = _pack_series(values)
    output.extend(_varuint(len(payload)))
    output.extend(payload)
    return kind


def _take_series(reader: _Reader, count: int) -> list[int]:
    return _unpack_series(reader.take(reader.varuint()), count)


def _pack_pair_candidate(
    pairs: list[
        tuple[ComponentTokenObservation, ComponentTokenObservation]
    ],
    literals: list[ComponentTokenObservation],
) -> tuple[bytes, SparseMotifDefinition]:
    first = pairs[0][0]
    second = pairs[0][1]
    output = bytearray(MOTIF_MAGIC)
    output.extend(_varuint(first.token_id))
    output.extend(_varuint(second.token_id))
    output.extend(_varuint(first.support_frames))
    output.extend(_varuint(second.support_frames))
    output.extend(_varuint(len(pairs)))

    fields = [
        [left.onset_frame for left, _right in pairs],
        [left.layer_hypothesis_id for left, _right in pairs],
        [left.channel for left, _right in pairs],
        [left.gain_q15 for left, _right in pairs],
        [left.phase_q16 for left, _right in pairs],
        [left.source_step_q16 for left, _right in pairs],
        [right.onset_frame - left.onset_frame for left, right in pairs],
        [
            right.layer_hypothesis_id - left.layer_hypothesis_id
            for left, right in pairs
        ],
        [right.channel - left.channel for left, right in pairs],
        [right.gain_q15 - left.gain_q15 for left, right in pairs],
        [right.phase_q16 - left.phase_q16 for left, right in pairs],
        [
            right.source_step_q16 - left.source_step_q16
            for left, right in pairs
        ],
    ]
    law_kinds = tuple(_append_series(output, values) for values in fields)
    output.extend(_pack_rows(literals))
    payload = _finish(bytes(output))
    definition = SparseMotifDefinition(
        first.token_id,
        second.token_id,
        first.support_frames,
        second.support_frames,
        fields[6][0],
        len(pairs),
        law_kinds,
    )
    return payload, definition


def decode_sparse_motif_events(
    payload: bytes,
) -> tuple[ComponentTokenObservation, ...]:
    """Decode either exact literal or sparse pair-ledger syntax."""

    reader = _Reader(_verify(payload))
    magic = reader.take(4)
    if magic == FLAT_MAGIC:
        observations = _unpack_rows(reader)
    elif magic == MOTIF_MAGIC:
        first_token = reader.varuint()
        second_token = reader.varuint()
        first_support = reader.varuint()
        second_support = reader.varuint()
        count = reader.varuint()
        fields = [_take_series(reader, count) for _ in range(12)]
        observations = []
        for index in range(count):
            first = ComponentTokenObservation(
                0,
                fields[1][index],
                first_token,
                fields[0][index],
                first_support,
                fields[2][index],
                fields[3][index],
                fields[4][index],
                fields[5][index],
            )
            observations.extend(
                (
                    first,
                    ComponentTokenObservation(
                        0,
                        first.layer_hypothesis_id + fields[7][index],
                        second_token,
                        first.onset_frame + fields[6][index],
                        second_support,
                        first.channel + fields[8][index],
                        first.gain_q15 + fields[9][index],
                        first.phase_q16 + fields[10][index],
                        first.source_step_q16 + fields[11][index],
                    ),
                )
            )
        observations.extend(_unpack_rows(reader))
    elif magic == PATH_MAGIC:
        step_count = reader.varuint()
        if not 2 <= step_count <= 16:
            raise ValueError("sparse path step count exceeds bounds")
        token_ids = [reader.varuint() for _ in range(step_count)]
        supports = [reader.varuint() for _ in range(step_count)]
        count = reader.varuint()
        fields = [
            _take_series(reader, count)
            for _ in range(6 * step_count)
        ]
        observations = []
        for occurrence_index in range(count):
            anchor = ComponentTokenObservation(
                0,
                fields[1][occurrence_index],
                token_ids[0],
                fields[0][occurrence_index],
                supports[0],
                fields[2][occurrence_index],
                fields[3][occurrence_index],
                fields[4][occurrence_index],
                fields[5][occurrence_index],
            )
            observations.append(anchor)
            previous = anchor
            for step_index in range(1, step_count):
                offset = step_index * 6
                current = ComponentTokenObservation(
                    0,
                    previous.layer_hypothesis_id
                        + fields[offset + 1][occurrence_index],
                    token_ids[step_index],
                    previous.onset_frame
                        + fields[offset][occurrence_index],
                    supports[step_index],
                    previous.channel
                        + fields[offset + 2][occurrence_index],
                    previous.gain_q15
                        + fields[offset + 3][occurrence_index],
                    previous.phase_q16
                        + fields[offset + 4][occurrence_index],
                    previous.source_step_q16
                        + fields[offset + 5][occurrence_index],
                )
                observations.append(current)
                previous = current
        observations.extend(_unpack_rows(reader))
    elif magic == BASIS_GROUP_MAGIC:
        observations = []
        for _ in range(reader.varuint()):
            token_id = reader.varuint()
            support_frames = reader.varuint()
            count = reader.varuint()
            fields = [_take_series(reader, count) for _ in range(6)]
            observations.extend(
                ComponentTokenObservation(
                    0,
                    fields[1][index],
                    token_id,
                    fields[0][index],
                    support_frames,
                    fields[2][index],
                    fields[3][index],
                    fields[4][index],
                    fields[5][index],
                )
                for index in range(count)
            )
    else:
        raise ValueError("unknown sparse motif stream magic")
    if reader.cursor != len(reader.payload):
        raise ValueError("trailing sparse motif bytes")
    ordered = sorted(observations, key=_event_key)
    return tuple(
        ComponentTokenObservation(index, *(_event_key(item)))
        for index, item in enumerate(ordered)
    )


def _pack_path_candidate(
    paths: list[tuple[ComponentTokenObservation, ...]],
    literals: list[ComponentTokenObservation],
) -> tuple[bytes, SparsePathDefinition]:
    step_count = len(paths[0])
    if any(len(path) != step_count for path in paths):
        raise ValueError("sparse path occurrences have inconsistent depth")
    tokens = tuple(item.token_id for item in paths[0])
    supports = tuple(item.support_frames for item in paths[0])
    output = bytearray(PATH_MAGIC)
    output.extend(_varuint(step_count))
    for token in tokens:
        output.extend(_varuint(token))
    for support in supports:
        output.extend(_varuint(support))
    output.extend(_varuint(len(paths)))

    fields = [
        [path[0].onset_frame for path in paths],
        [path[0].layer_hypothesis_id for path in paths],
        [path[0].channel for path in paths],
        [path[0].gain_q15 for path in paths],
        [path[0].phase_q16 for path in paths],
        [path[0].source_step_q16 for path in paths],
    ]
    for step_index in range(1, step_count):
        fields.extend(
            (
                [
                    path[step_index].onset_frame
                        - path[step_index - 1].onset_frame
                    for path in paths
                ],
                [
                    path[step_index].layer_hypothesis_id
                        - path[step_index - 1].layer_hypothesis_id
                    for path in paths
                ],
                [
                    path[step_index].channel
                        - path[step_index - 1].channel
                    for path in paths
                ],
                [
                    path[step_index].gain_q15
                        - path[step_index - 1].gain_q15
                    for path in paths
                ],
                [
                    path[step_index].phase_q16
                        - path[step_index - 1].phase_q16
                    for path in paths
                ],
                [
                    path[step_index].source_step_q16
                        - path[step_index - 1].source_step_q16
                    for path in paths
                ],
            )
        )
    law_kinds = tuple(_append_series(output, values) for values in fields)
    output.extend(_pack_rows(literals))
    payload = _finish(bytes(output))
    definition = SparsePathDefinition(
        tokens,
        supports,
        tuple(
            paths[0][index].onset_frame
                - paths[0][index - 1].onset_frame
            for index in range(1, step_count)
        ),
        len(paths),
        law_kinds,
    )
    return payload, definition


def discover_and_pack_sparse_path_motifs(
    observations: list[ComponentTokenObservation],
    *,
    language: SparsePathLanguage,
) -> SparsePathCandidate:
    """Discover a bounded multi-step motif whose steps may skip other events."""

    if len({item.observation_id for item in observations}) != len(observations):
        raise ValueError("sparse path observation IDs must be unique")
    flat = pack_flat_observations(observations)
    ordered = sorted(
        observations,
        key=lambda item: (
            item.layer_hypothesis_id,
            item.onset_frame,
            item.observation_id,
        ),
    )
    order_index = {
        item.observation_id: index for index, item in enumerate(ordered)
    }
    groups: dict[
        tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]],
        list[tuple[ComponentTokenObservation, ...]],
    ] = {}
    candidate_count = 0

    def extend(path: tuple[ComponentTokenObservation, ...]) -> None:
        nonlocal candidate_count
        if candidate_count >= language.maximum_path_candidates:
            return
        if len(path) >= language.minimum_steps:
            key = (
                tuple(item.token_id for item in path),
                tuple(item.support_frames for item in path),
                tuple(
                    (
                        path[index].onset_frame
                        - path[index - 1].onset_frame
                    ) // language.gap_bucket_frames
                    for index in range(1, len(path))
                ),
            )
            groups.setdefault(key, []).append(path)
            candidate_count += 1
        if len(path) >= language.maximum_steps:
            return
        previous = path[-1]
        successor_count = 0
        previous_index = order_index[previous.observation_id]
        for following in ordered[previous_index + 1 :]:
            if following.layer_hypothesis_id != previous.layer_hypothesis_id:
                if following.layer_hypothesis_id > previous.layer_hypothesis_id:
                    break
                continue
            gap = following.onset_frame - previous.onset_frame
            if gap <= 0:
                continue
            if gap > language.maximum_gap_frames:
                break
            extend((*path, following))
            successor_count += 1
            if (
                successor_count >= language.maximum_successors_per_step
                or candidate_count >= language.maximum_path_candidates
            ):
                break

    for observation in ordered:
        extend((observation,))
        if candidate_count >= language.maximum_path_candidates:
            break

    best: tuple[
        bytes,
        SparsePathDefinition,
        list[tuple[ComponentTokenObservation, ...]],
    ] | None = None
    evaluated_group_count = 0
    for group in groups.values():
        used: set[int] = set()
        paths: list[tuple[ComponentTokenObservation, ...]] = []
        for path in sorted(
            group,
            key=lambda item: tuple(event.onset_frame for event in item),
        ):
            ids = {item.observation_id for item in path}
            if len(ids) != len(path) or used & ids:
                continue
            used.update(ids)
            paths.append(path)
        if len(paths) < language.minimum_occurrences:
            continue
        evaluated_group_count += 1
        literals = [
            item for item in observations if item.observation_id not in used
        ]
        payload, definition = _pack_path_candidate(paths, literals)
        if best is None or len(payload) < len(best[0]):
            best = (payload, definition, paths)

    selected_payload = flat
    definitions: tuple[SparsePathDefinition, ...] = ()
    selected_kind = "flat-events"
    path_bytes = None
    selected_path_count = 0
    if best is not None:
        path_bytes = len(best[0])
        if path_bytes < len(flat):
            selected_payload = best[0]
            definitions = (best[1],)
            selected_kind = "sparse-path-motif"
            selected_path_count = len(best[2])

    decoded = decode_sparse_motif_events(selected_payload)
    if [_event_key(item) for item in decoded] != sorted(
        _event_key(item) for item in observations
    ):
        raise RuntimeError("sparse path event identity failed")
    saving = len(flat) - len(selected_payload)
    return SparsePathCandidate(
        selected_kind,
        definitions,
        selected_payload,
        len(flat),
        path_bytes,
        decoded,
        {
            "schema": "resonith-r160-sparse-path-grammar-1",
            "status": "exact event-ledger gate; complete audio RDO pending",
            "observation_count": len(observations),
            "candidate_path_count": candidate_count,
            "evaluated_group_count": evaluated_group_count,
            "selected_path_count": selected_path_count,
            "selected_step_count": (
                len(definitions[0].token_ids) if definitions else 0
            ),
            "flat_stream_bytes": len(flat),
            "path_stream_bytes": path_bytes,
            "selected_stream_bytes": len(selected_payload),
            "saving_bytes": saving,
            "saving_percent": (
                100.0 * saving / len(flat) if flat else 0.0
            ),
            "exact_event_roundtrip": True,
        },
    )


def discover_and_pack_sparse_pair_motifs(
    observations: list[ComponentTokenObservation],
    *,
    language: SparseMotifLanguage,
) -> SparseMotifCandidate:
    """Select one bounded gapped pair grammar by actual serialized bytes."""

    if len({item.observation_id for item in observations}) != len(observations):
        raise ValueError("sparse motif observation IDs must be unique")
    flat = pack_flat_observations(observations)
    ordered = sorted(
        observations,
        key=lambda item: (item.layer_hypothesis_id, item.onset_frame),
    )
    groups: dict[
        tuple[int, int, int, int, int, int],
        list[tuple[ComponentTokenObservation, ComponentTokenObservation]],
    ] = {}
    candidate_count = 0
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            if right.layer_hypothesis_id != left.layer_hypothesis_id:
                if right.layer_hypothesis_id > left.layer_hypothesis_id:
                    break
                continue
            gap = right.onset_frame - left.onset_frame
            if gap <= 0:
                continue
            if gap > language.maximum_gap_frames:
                break
            key = (
                left.layer_hypothesis_id,
                left.token_id,
                right.token_id,
                left.support_frames,
                right.support_frames,
                gap // language.gap_bucket_frames,
            )
            groups.setdefault(key, []).append((left, right))
            candidate_count += 1
            if candidate_count >= language.maximum_pair_candidates:
                break
        if candidate_count >= language.maximum_pair_candidates:
            break

    best: tuple[
        bytes,
        SparseMotifDefinition,
        list[tuple[ComponentTokenObservation, ComponentTokenObservation]],
    ] | None = None
    evaluated_group_count = 0
    for group in groups.values():
        used: set[int] = set()
        pairs = []
        for left, right in sorted(
            group,
            key=lambda item: (
                item[0].onset_frame,
                item[1].onset_frame,
            ),
        ):
            if left.observation_id in used or right.observation_id in used:
                continue
            used.update((left.observation_id, right.observation_id))
            pairs.append((left, right))
        if len(pairs) < language.minimum_occurrences:
            continue
        evaluated_group_count += 1
        literals = [
            item for item in observations if item.observation_id not in used
        ]
        payload, definition = _pack_pair_candidate(pairs, literals)
        if best is None or len(payload) < len(best[0]):
            best = (payload, definition, pairs)

    selected_payload = flat
    definitions: tuple[SparseMotifDefinition, ...] = ()
    selected_kind = "flat-events"
    motif_bytes = None
    selected_pair_count = 0
    if best is not None:
        motif_bytes = len(best[0])
        if motif_bytes < len(flat):
            selected_payload = best[0]
            definitions = (best[1],)
            selected_kind = "sparse-pair-motif"
            selected_pair_count = len(best[2])

    decoded = decode_sparse_motif_events(selected_payload)
    if [_event_key(item) for item in decoded] != sorted(
        _event_key(item) for item in observations
    ):
        raise RuntimeError("sparse motif event identity failed")
    return SparseMotifCandidate(
        selected_kind,
        definitions,
        selected_payload,
        len(flat),
        motif_bytes,
        decoded,
        {
            "schema": "resonith-r160-sparse-motif-grammar-1",
            "status": "exact event-ledger gate; complete audio RDO pending",
            "observation_count": len(observations),
            "candidate_pair_count": candidate_count,
            "evaluated_group_count": evaluated_group_count,
            "selected_pair_count": selected_pair_count,
            "selected_kind": selected_kind,
            "flat_stream_bytes": len(flat),
            "motif_stream_bytes": motif_bytes,
            "selected_stream_bytes": len(selected_payload),
            "saving_percent": (
                100.0 * (len(flat) - len(selected_payload)) / len(flat)
            ),
            "exact_event_roundtrip": True,
            "semantic_labels": False,
            "intervening_events_may_remain_unclaimed": True,
        },
    )


def pack_latent_field_event_ledger(
    field: "LatentSourceField",
    *,
    pair_language: SparseMotifLanguage,
    path_language: SparsePathLanguage,
) -> LatentFieldEventLedger:
    """Replace per-Basis occurrence maps with one exact global grammar ledger.

    The current R-159 oracle has not yet inferred a stable source-group ID, so
    all verified Basis tokens enter one anonymous composition layer. This is a
    signalling experiment only: the audio prediction and final Truth remain
    unchanged.
    """

    observations: list[ComponentTokenObservation] = []
    for component in field.components:
        for occurrence in component.occurrences:
            observations.append(
                ComponentTokenObservation(
                    len(observations),
                    0,
                    component.component_id,
                    occurrence.start,
                    occurrence.sample_count,
                    occurrence.channel,
                    occurrence.gain_q15,
                    occurrence.alignment_lag << 16,
                    65536,
                )
            )
    flat = pack_flat_observations(observations)
    basis_grouped = pack_basis_grouped_observations(observations)
    pair = discover_and_pack_sparse_pair_motifs(
        observations,
        language=pair_language,
    )
    path = discover_and_pack_sparse_path_motifs(
        observations,
        language=path_language,
    )
    choices = (
        ("flat-events", flat),
        ("basis-grouped-events", basis_grouped),
        (pair.selected_kind, pair.packed_stream),
        (path.selected_kind, path.packed_stream),
    )
    selected_kind, selected = min(
        choices,
        key=lambda item: (len(item[1]), item[0]),
    )
    decoded = decode_sparse_motif_events(selected)
    expected = sorted(_event_key(item) for item in observations)
    if [_event_key(item) for item in decoded] != expected:
        raise RuntimeError("latent field event ledger identity failed")
    legacy_bytes = sum(
        len(component.event_map) for component in field.components
    )
    accounted_kind = selected_kind
    accounted_bytes = len(selected)
    if legacy_bytes < accounted_bytes:
        # In a complete Basis record the token, support and checksum are
        # already owned by the surrounding dictionary syntax. The existing
        # per-Basis delta maps are therefore a valid lower-cost accounting
        # candidate even though this standalone research ledger retains its
        # own self-describing stream for independent corruption tests.
        accounted_kind = "basis-coupled-delta-maps"
        accounted_bytes = legacy_bytes
    return LatentFieldEventLedger(
        selected,
        decoded,
        {
            "schema": "resonith-r160-lspf-event-ledger-1",
            "status": "event signalling only; audio payload RDO pending",
            "selected_kind": accounted_kind,
            "standalone_selected_kind": selected_kind,
            "observation_count": len(observations),
            "legacy_component_event_map_bytes": legacy_bytes,
            "flat_global_event_bytes": len(flat),
            "basis_grouped_event_bytes": len(basis_grouped),
            "pair_candidate_bytes": len(pair.packed_stream),
            "path_candidate_bytes": len(path.packed_stream),
            "selected_event_bytes": accounted_bytes,
            "standalone_event_bytes": len(selected),
            "saving_vs_legacy_bytes": legacy_bytes - accounted_bytes,
            "saving_vs_flat_bytes": len(flat) - accounted_bytes,
            "exact_event_roundtrip": True,
        },
    )
