"""R-150 exact bounded minimum-description grammar selection oracle."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class GrammarSpan:
    """One independently priced reconstruction candidate for a time span."""

    start: int
    end: int
    payload_bytes: int
    label: str
    basis_id: str | None = None

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("grammar spans require a positive ordered range")
        if self.payload_bytes < 0:
            raise ValueError("grammar span bytes cannot be negative")
        if not self.label:
            raise ValueError("grammar spans require a stable label")


@dataclass(frozen=True)
class GrammarSelection:
    """The exact bounded chart result including one-time dictionary costs."""

    complete_bytes: int
    selected_spans: tuple[GrammarSpan, ...]
    truth_positions: tuple[int, ...]
    activated_basis_ids: tuple[str, ...]
    state_count: int


@dataclass(frozen=True)
class CompoundDiscovery:
    """Exact repeated atom sequences offered to the global chart."""

    spans: tuple[GrammarSpan, ...]
    basis_activation_bytes: dict[str, int]
    sequence_candidate_count: int
    repeated_sequence_count: int


@dataclass(frozen=True)
class StateAtom:
    """One label-free micro-Basis observation with exact transform state."""

    symbol: int
    phase: int
    gain_q15: int


def _compound_id(symbols: Sequence[int]) -> str:
    payload = b"".join(
        int(symbol).to_bytes(8, "little", signed=True)
        for symbol in symbols
    )
    return "compound-" + hashlib.blake2s(
        payload,
        digest_size=12,
    ).hexdigest()


def _state_compound_id(
    symbols: Sequence[int],
    phase_increments: Sequence[int],
    gain_increments: Sequence[int],
) -> str:
    values = (
        tuple(int(value) for value in symbols),
        tuple(int(value) for value in phase_increments),
        tuple(int(value) for value in gain_increments),
    )
    payload = repr(values).encode("ascii")
    return "state-compound-" + hashlib.blake2s(
        payload,
        digest_size=12,
    ).hexdigest()


def discover_exact_compounds(
    atom_symbols: Sequence[int],
    atom_boundaries: Sequence[int],
    *,
    minimum_atoms: int = 2,
    maximum_atoms: int = 16,
    placement_bytes: int = 8,
    dictionary_bytes_per_atom: int = 4,
    existing_basis_ids: Iterable[str] = (),
) -> CompoundDiscovery:
    """Enumerate every repeated contiguous atom sequence in declared bounds.

    This discovery is scale-neutral: its candidates do not select or claim
    samples. Direct large-span candidates from original PCM remain free to
    compete in `select_minimum_description`.
    """

    symbols = tuple(int(value) for value in atom_symbols)
    boundaries = tuple(int(value) for value in atom_boundaries)
    if len(boundaries) != len(symbols) + 1:
        raise ValueError("atom boundaries must contain N + 1 positions")
    if (
        any(right <= left for left, right in zip(boundaries, boundaries[1:]))
        or boundaries[0] < 0
    ):
        raise ValueError("atom boundaries must be strictly increasing")
    if minimum_atoms < 2 or maximum_atoms < minimum_atoms:
        raise ValueError("invalid compound atom bounds")
    if placement_bytes < 0 or dictionary_bytes_per_atom < 0:
        raise ValueError("compound byte costs cannot be negative")

    occurrences: dict[tuple[int, ...], list[int]] = {}
    candidate_count = 0
    for length in range(
        minimum_atoms,
        min(maximum_atoms, len(symbols)) + 1,
    ):
        for start in range(0, len(symbols) - length + 1):
            sequence = symbols[start : start + length]
            occurrences.setdefault(sequence, []).append(start)
            candidate_count += 1

    existing = set(existing_basis_ids)
    spans: list[GrammarSpan] = []
    activation: dict[str, int] = {}
    repeated_count = 0
    for sequence, starts in sorted(
        occurrences.items(),
        key=lambda item: (len(item[0]), item[0]),
    ):
        if len(starts) < 2:
            continue
        repeated_count += 1
        basis_id = _compound_id(sequence)
        activation[basis_id] = (
            0
            if basis_id in existing
            else len(sequence) * dictionary_bytes_per_atom
        )
        for start in starts:
            end = start + len(sequence)
            spans.append(
                GrammarSpan(
                    start=boundaries[start],
                    end=boundaries[end],
                    payload_bytes=placement_bytes,
                    label=f"{basis_id}@{boundaries[start]}",
                    basis_id=basis_id,
                )
            )
    return CompoundDiscovery(
        spans=tuple(spans),
        basis_activation_bytes=activation,
        sequence_candidate_count=candidate_count,
        repeated_sequence_count=repeated_count,
    )


def discover_affine_state_compounds(
    atoms: Sequence[StateAtom],
    atom_boundaries: Sequence[int],
    *,
    minimum_atoms: int = 2,
    maximum_atoms: int = 16,
    phase_modulus: int | None = None,
    placement_bytes: int = 12,
    dictionary_bytes_per_atom: int = 4,
    increment_bytes: int = 2,
    existing_basis_ids: Iterable[str] = (),
) -> CompoundDiscovery:
    """Merge sequences equal after removing initial phase/gain state.

    The dictionary pays for symbols and exact state increments once. Each
    placement pays only for its initial state, timing, and correction already
    included by the caller in `placement_bytes`.
    """

    observations = tuple(atoms)
    boundaries = tuple(int(value) for value in atom_boundaries)
    if len(boundaries) != len(observations) + 1:
        raise ValueError("atom boundaries must contain N + 1 positions")
    if (
        any(right <= left for left, right in zip(boundaries, boundaries[1:]))
        or boundaries[0] < 0
    ):
        raise ValueError("atom boundaries must be strictly increasing")
    if minimum_atoms < 2 or maximum_atoms < minimum_atoms:
        raise ValueError("invalid state-compound atom bounds")
    if phase_modulus is not None and phase_modulus <= 0:
        raise ValueError("phase_modulus must be positive")
    if min(placement_bytes, dictionary_bytes_per_atom, increment_bytes) < 0:
        raise ValueError("state-compound byte costs cannot be negative")

    groups: dict[
        tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]],
        list[tuple[int, int]],
    ] = {}
    candidate_count = 0
    for length in range(
        minimum_atoms,
        min(maximum_atoms, len(observations)) + 1,
    ):
        for start in range(0, len(observations) - length + 1):
            window = observations[start : start + length]
            symbols = tuple(int(item.symbol) for item in window)
            phase_increments = []
            gain_increments = []
            for left, right in zip(window, window[1:]):
                phase_delta = int(right.phase) - int(left.phase)
                if phase_modulus is not None:
                    phase_delta %= phase_modulus
                phase_increments.append(phase_delta)
                gain_increments.append(
                    int(right.gain_q15) - int(left.gain_q15)
                )
            key = (
                symbols,
                tuple(phase_increments),
                tuple(gain_increments),
            )
            groups.setdefault(key, []).append(
                (start, int(window[0].phase))
            )
            candidate_count += 1

    existing = set(existing_basis_ids)
    spans: list[GrammarSpan] = []
    activation: dict[str, int] = {}
    repeated_count = 0
    for key, starts in sorted(
        groups.items(),
        key=lambda item: (len(item[0][0]), item[0]),
    ):
        if len(starts) < 2:
            continue
        repeated_count += 1
        symbols, phase_increments, gain_increments = key
        basis_id = _state_compound_id(
            symbols,
            phase_increments,
            gain_increments,
        )
        activation[basis_id] = (
            0
            if basis_id in existing
            else (
                len(symbols) * dictionary_bytes_per_atom
                + (
                    len(phase_increments) + len(gain_increments)
                ) * increment_bytes
            )
        )
        for start, _ in starts:
            end = start + len(symbols)
            spans.append(
                GrammarSpan(
                    start=boundaries[start],
                    end=boundaries[end],
                    payload_bytes=placement_bytes,
                    label=f"{basis_id}@{boundaries[start]}",
                    basis_id=basis_id,
                )
            )
    return CompoundDiscovery(
        spans=tuple(spans),
        basis_activation_bytes=activation,
        sequence_candidate_count=candidate_count,
        repeated_sequence_count=repeated_count,
    )


def select_minimum_description(
    frame_count: int,
    truth_bytes_by_frame: Sequence[int],
    candidates: Iterable[GrammarSpan],
    basis_activation_bytes: Mapping[str, int],
    *,
    maximum_basis_families: int = 20,
) -> GrammarSelection:
    """Solve the bounded global R-150 chart exactly, without greedy ownership."""

    if frame_count < 0 or len(truth_bytes_by_frame) != frame_count:
        raise ValueError("Truth prices must cover every frame exactly")
    truth_costs = tuple(int(value) for value in truth_bytes_by_frame)
    if any(value < 0 for value in truth_costs):
        raise ValueError("Truth prices cannot be negative")

    spans = tuple(candidates)
    by_start: list[list[GrammarSpan]] = [[] for _ in range(frame_count + 1)]
    basis_ids = sorted(
        {
            span.basis_id
            for span in spans
            if span.basis_id is not None
        }
    )
    if len(basis_ids) > maximum_basis_families:
        raise ValueError(
            "bounded exact chart exceeds maximum_basis_families"
        )
    missing_costs = [
        basis_id
        for basis_id in basis_ids
        if basis_id not in basis_activation_bytes
    ]
    if missing_costs:
        raise ValueError("missing one-time Basis activation cost")
    bits = {basis_id: 1 << index for index, basis_id in enumerate(basis_ids)}
    for span in spans:
        if span.end > frame_count:
            raise ValueError("grammar span exceeds the signal")
        by_start[span.start].append(span)
    for bucket in by_start:
        bucket.sort(
            key=lambda span: (
                span.end,
                span.payload_bytes,
                span.label,
            )
        )

    visited_states = 0

    @lru_cache(maxsize=None)
    def solve(
        position: int,
        active_mask: int,
    ) -> tuple[int, tuple[GrammarSpan | None, ...]]:
        nonlocal visited_states
        visited_states += 1
        if position == frame_count:
            return 0, ()

        suffix_cost, suffix_path = solve(position + 1, active_mask)
        best_cost = truth_costs[position] + suffix_cost
        best_path: tuple[GrammarSpan | None, ...] = (None, *suffix_path)
        best_key = (
            best_cost,
            tuple(
                "~truth" if item is None else item.label
                for item in best_path
            ),
        )
        for span in by_start[position]:
            next_mask = active_mask
            activation_cost = 0
            if span.basis_id is not None:
                bit = bits[span.basis_id]
                if active_mask & bit == 0:
                    activation_cost = int(
                        basis_activation_bytes[span.basis_id]
                    )
                    if activation_cost < 0:
                        raise ValueError("Basis activation cannot be negative")
                    next_mask |= bit
            child_cost, child_path = solve(span.end, next_mask)
            complete_cost = (
                span.payload_bytes + activation_cost + child_cost
            )
            path = (span, *child_path)
            key = (
                complete_cost,
                tuple(item.label for item in path if item is not None),
            )
            if key < best_key:
                best_cost = complete_cost
                best_path = path
                best_key = key
        return best_cost, best_path

    complete_bytes, path = solve(0, 0)
    selected = tuple(item for item in path if item is not None)
    truth_positions: list[int] = []
    cursor = 0
    for item in path:
        if item is None:
            truth_positions.append(cursor)
            cursor += 1
        else:
            cursor = item.end
    activated = tuple(
        sorted(
            {
                span.basis_id
                for span in selected
                if span.basis_id is not None
            }
        )
    )
    return GrammarSelection(
        complete_bytes=complete_bytes,
        selected_spans=selected,
        truth_positions=tuple(truth_positions),
        activated_basis_ids=activated,
        state_count=visited_states,
    )
