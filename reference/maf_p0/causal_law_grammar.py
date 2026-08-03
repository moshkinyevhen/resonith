"""Exact byte-priced hierarchical grammar for R-173 causal-law tokens.

The encoder discovers repetition in factorized causal laws. This module turns
one canonical token stream into an independently decodable literal,
dictionary, or bounded RePair-style CompoundBasis ledger. Every accepted rule
must reduce the complete compressed payload at the moment it is admitted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import zlib


WRAPPER_MAGIC = b"CLZ1"
RAW_MAGIC = b"CLR1"
DICTIONARY_MAGIC = b"CLD1"
GRAMMAR_MAGIC = b"CLG1"


@dataclass(frozen=True)
class CausalLawGrammarLanguage:
    """Finite grammar and decoder resource bounds for one evidence run."""

    minimum_pair_occurrences: int = 3
    maximum_rules: int = 64
    maximum_candidate_pairs_per_round: int = 16
    maximum_tokens: int = 1 << 24
    maximum_token_width: int = 64

    def __post_init__(self) -> None:
        if (
            not 2 <= self.minimum_pair_occurrences <= 65535
            or not 0 <= self.maximum_rules <= 4096
            or not 1 <= self.maximum_candidate_pairs_per_round <= 4096
            or not 1 <= self.maximum_tokens <= 1 << 30
            or not 1 <= self.maximum_token_width <= 1024
        ):
            raise ValueError("invalid causal-law grammar language")


@dataclass(frozen=True)
class CausalLawRule:
    """One acyclic CompoundBasis rule over literals or earlier rules."""

    left_symbol: int
    right_symbol: int


@dataclass(frozen=True)
class CausalLawGrammarCandidate:
    """Complete-byte RDO result and exact decoded canonical tokens."""

    selected_kind: str
    packed_stream: bytes
    raw_stream_bytes: int
    dictionary_stream_bytes: int
    grammar_stream_bytes: int | None
    rules: tuple[CausalLawRule, ...]
    decoded_tokens: tuple[tuple[int, ...], ...]
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
            raise ValueError("truncated causal-law grammar stream")
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
        raise ValueError("causal-law varint exceeds 64 bits")

    def varsint(self) -> int:
        value = self.varuint()
        return -(value // 2) - 1 if value & 1 else value // 2


def _wrap(body: bytes) -> bytes:
    checksum = (zlib.crc32(body) & 0xFFFF_FFFF).to_bytes(4, "little")
    return WRAPPER_MAGIC + zlib.compress(body, level=9) + checksum


def _unwrap(payload: bytes) -> bytes:
    if len(payload) < 9 or payload[:4] != WRAPPER_MAGIC:
        raise ValueError("bad causal-law grammar magic")
    try:
        body = zlib.decompress(payload[4:-4])
    except zlib.error as error:
        raise ValueError("invalid causal-law compressed body") from error
    checksum = int.from_bytes(payload[-4:], "little")
    if zlib.crc32(body) & 0xFFFF_FFFF != checksum:
        raise ValueError("causal-law grammar checksum mismatch")
    return body


def _append_token(output: bytearray, token: tuple[int, ...]) -> None:
    output.extend(_varuint(len(token)))
    for value in token:
        output.extend(_varsint(value))


def _take_token(
    reader: _Reader,
    *,
    maximum_width: int,
) -> tuple[int, ...]:
    width = reader.varuint()
    if width > maximum_width:
        raise ValueError("causal-law token width exceeds decoder bound")
    return tuple(reader.varsint() for _ in range(width))


def _pack_raw(tokens: tuple[tuple[int, ...], ...]) -> bytes:
    body = bytearray(RAW_MAGIC)
    body.extend(_varuint(len(tokens)))
    for token in tokens:
        _append_token(body, token)
    return _wrap(bytes(body))


def _vocabulary(
    tokens: tuple[tuple[int, ...], ...],
) -> tuple[tuple[tuple[int, ...], ...], list[int]]:
    index = {}
    vocabulary = []
    sequence = []
    for token in tokens:
        symbol = index.get(token)
        if symbol is None:
            symbol = len(vocabulary)
            index[token] = symbol
            vocabulary.append(token)
        sequence.append(symbol)
    return tuple(vocabulary), sequence


def _pack_symbolic(
    magic: bytes,
    vocabulary: tuple[tuple[int, ...], ...],
    rules: tuple[CausalLawRule, ...],
    sequence: list[int],
) -> bytes:
    body = bytearray(magic)
    body.extend(_varuint(len(vocabulary)))
    for token in vocabulary:
        _append_token(body, token)
    if magic == GRAMMAR_MAGIC:
        body.extend(_varuint(len(rules)))
        for rule in rules:
            body.extend(_varuint(rule.left_symbol))
            body.extend(_varuint(rule.right_symbol))
    body.extend(_varuint(len(sequence)))
    for symbol in sequence:
        body.extend(_varuint(symbol))
    return _wrap(bytes(body))


def _replace_pair(
    sequence: list[int],
    pair: tuple[int, int],
    replacement: int,
) -> tuple[list[int], int]:
    output = []
    index = 0
    replacements = 0
    while index < len(sequence):
        if (
            index + 1 < len(sequence)
            and sequence[index] == pair[0]
            and sequence[index + 1] == pair[1]
        ):
            output.append(replacement)
            index += 2
            replacements += 1
        else:
            output.append(sequence[index])
            index += 1
    return output, replacements


def _top_pairs(
    sequence: list[int],
    language: CausalLawGrammarLanguage,
) -> list[tuple[int, int]]:
    counts = Counter(zip(sequence, sequence[1:]))
    eligible = [
        (pair, count)
        for pair, count in counts.items()
        if count >= language.minimum_pair_occurrences
    ]
    eligible.sort(key=lambda item: (-item[1], item[0]))
    return [
        pair
        for pair, _count in eligible[
            : language.maximum_candidate_pairs_per_round
        ]
    ]


def encode_causal_law_tokens(
    tokens: tuple[tuple[int, ...], ...],
    *,
    language: CausalLawGrammarLanguage = CausalLawGrammarLanguage(),
) -> CausalLawGrammarCandidate:
    """Select an exact literal, dictionary, or hierarchical grammar ledger."""

    if len(tokens) > language.maximum_tokens:
        raise ValueError("causal-law token count exceeds encoder bound")
    if any(len(token) > language.maximum_token_width for token in tokens):
        raise ValueError("causal-law token width exceeds encoder bound")

    raw_stream = _pack_raw(tokens)
    vocabulary, dictionary_sequence = _vocabulary(tokens)
    dictionary_stream = _pack_symbolic(
        DICTIONARY_MAGIC,
        vocabulary,
        (),
        dictionary_sequence,
    )
    rules: tuple[CausalLawRule, ...] = ()
    sequence = dictionary_sequence
    current_stream = dictionary_stream
    evaluated_pair_candidates = 0
    accepted_rules = 0

    for _round in range(language.maximum_rules):
        best = None
        for pair in _top_pairs(sequence, language):
            evaluated_pair_candidates += 1
            replacement = len(vocabulary) + len(rules)
            replaced, count = _replace_pair(
                sequence,
                pair,
                replacement,
            )
            if count < language.minimum_pair_occurrences:
                continue
            proposed_rules = rules + (CausalLawRule(*pair),)
            proposed_stream = _pack_symbolic(
                GRAMMAR_MAGIC,
                vocabulary,
                proposed_rules,
                replaced,
            )
            key = (len(proposed_stream), pair)
            if best is None or key < best[0]:
                best = (
                    key,
                    proposed_rules,
                    replaced,
                    proposed_stream,
                    count,
                )
        if best is None or len(best[3]) >= len(current_stream):
            break
        _key, rules, sequence, current_stream, _count = best
        accepted_rules += 1

    candidates = [
        ("raw", raw_stream, ()),
        ("dictionary", dictionary_stream, ()),
    ]
    grammar_stream = None
    if rules:
        grammar_stream = current_stream
        candidates.append(("grammar", grammar_stream, rules))
    selected_kind, packed_stream, selected_rules = min(
        candidates,
        key=lambda item: (len(item[1]), item[0]),
    )
    decoded = decode_causal_law_tokens(
        packed_stream,
        language=language,
    )
    if decoded != tokens:
        raise RuntimeError("causal-law grammar encoder round-trip failed")
    return CausalLawGrammarCandidate(
        selected_kind=selected_kind,
        packed_stream=packed_stream,
        raw_stream_bytes=len(raw_stream),
        dictionary_stream_bytes=len(dictionary_stream),
        grammar_stream_bytes=(
            len(grammar_stream) if grammar_stream is not None else None
        ),
        rules=tuple(selected_rules),
        decoded_tokens=decoded,
        report={
            "schema": "resonith-r174-causal-law-grammar-1",
            "status": "exact token-ledger RDO; audio integration pending",
            "token_count": len(tokens),
            "token_vocabulary_size": len(vocabulary),
            "evaluated_pair_candidates": evaluated_pair_candidates,
            "accepted_rule_count": accepted_rules,
            "selected_kind": selected_kind,
            "selected_bytes": len(packed_stream),
            "raw_bytes": len(raw_stream),
            "dictionary_bytes": len(dictionary_stream),
            "grammar_bytes": (
                len(grammar_stream)
                if grammar_stream is not None
                else None
            ),
            "exact_token_round_trip": True,
        },
    )


def decode_causal_law_tokens(
    payload: bytes,
    *,
    language: CausalLawGrammarLanguage = CausalLawGrammarLanguage(),
) -> tuple[tuple[int, ...], ...]:
    """Decode one bounded exact causal-law token ledger."""

    reader = _Reader(_unwrap(payload))
    magic = reader.take(4)
    if magic == RAW_MAGIC:
        count = reader.varuint()
        if count > language.maximum_tokens:
            raise ValueError("causal-law raw token count exceeds bound")
        tokens = tuple(
            _take_token(reader, maximum_width=language.maximum_token_width)
            for _ in range(count)
        )
    elif magic in (DICTIONARY_MAGIC, GRAMMAR_MAGIC):
        vocabulary_count = reader.varuint()
        if vocabulary_count > language.maximum_tokens:
            raise ValueError("causal-law vocabulary exceeds bound")
        vocabulary = [
            _take_token(reader, maximum_width=language.maximum_token_width)
            for _ in range(vocabulary_count)
        ]
        rules = []
        if magic == GRAMMAR_MAGIC:
            rule_count = reader.varuint()
            if rule_count > language.maximum_rules:
                raise ValueError("causal-law rule count exceeds bound")
            for rule_index in range(rule_count):
                maximum_reference = vocabulary_count + rule_index
                left = reader.varuint()
                right = reader.varuint()
                if left >= maximum_reference or right >= maximum_reference:
                    raise ValueError("causal-law rule is cyclic or forward")
                rules.append((left, right))
        symbol_count = reader.varuint()
        if symbol_count > language.maximum_tokens:
            raise ValueError("causal-law symbol count exceeds bound")
        symbols = [reader.varuint() for _ in range(symbol_count)]
        maximum_symbol = vocabulary_count + len(rules)
        if any(symbol >= maximum_symbol for symbol in symbols):
            raise ValueError("causal-law symbol is undefined")

        output = []
        stack = list(reversed(symbols))
        while stack:
            symbol = stack.pop()
            if symbol < vocabulary_count:
                output.append(vocabulary[symbol])
                if len(output) > language.maximum_tokens:
                    raise ValueError("causal-law expansion exceeds bound")
                continue
            left, right = rules[symbol - vocabulary_count]
            stack.append(right)
            stack.append(left)
        tokens = tuple(output)
    else:
        raise ValueError("unknown causal-law ledger magic")
    if reader.cursor != len(reader.payload):
        raise ValueError("trailing causal-law ledger bytes")
    return tokens

