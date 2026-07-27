"""R-145 reversible partial-spectrum dictionary research codec."""

from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib

import numpy as np

from .lpc_oracle import (
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
)
from .motif_orbit import _canonical_fingerprint, _fit_gain_shift_q15


MAGIC = b"PSO1"
VERSION = 1
HEADER = struct.Struct("<4sBBHII")
BAND_HEADER = struct.Struct("<IIIIII")
BASIS_HEADER = struct.Struct("<II")
INSTANCE = struct.Struct("<HHIiI")
CHECKSUM = struct.Struct("<I")


@dataclass(frozen=True)
class PartialSpectrumOrbitCandidate:
    """One independently decodable exact R-145 research stream."""

    payload: bytes
    dictionary_payload: bytes
    multiband_truth_payload: bytes
    reconstruction: np.ndarray
    report: dict


def reversible_multiband_analysis(
    values: np.ndarray,
    levels: int,
) -> tuple[tuple[np.ndarray, ...], int]:
    """Split an integer signal with exact average/difference lifting."""

    source = np.asarray(values)
    if source.ndim != 1 or not np.issubdtype(source.dtype, np.signedinteger):
        raise TypeError("R-145 analysis requires one signed integer vector")
    if not 1 <= levels <= 8:
        raise ValueError("R-145 level count exceeds the research bound")
    alignment = 1 << levels
    padded_count = (
        (source.size + alignment - 1) // alignment * alignment
    )
    current = np.zeros(padded_count, dtype=np.int64)
    current[: source.size] = source.astype(np.int64)
    details: list[np.ndarray] = []
    for _ in range(levels):
        even = current[0::2]
        odd = current[1::2]
        difference = odd - even
        average = even + np.floor_divide(difference, 2)
        details.append(difference)
        current = average
    return (current, *reversed(details)), padded_count


def reversible_multiband_synthesis(
    bands: tuple[np.ndarray, ...],
    original_count: int,
) -> np.ndarray:
    """Invert `reversible_multiband_analysis` exactly."""

    if len(bands) < 2:
        raise ValueError("R-145 synthesis requires at least two bands")
    current = np.asarray(bands[0], dtype=np.int64)
    for detail_source in bands[1:]:
        detail = np.asarray(detail_source, dtype=np.int64)
        if detail.size != current.size:
            raise ValueError("R-145 band geometry is inconsistent")
        even = current - np.floor_divide(detail, 2)
        odd = detail + even
        merged = np.empty(current.size * 2, dtype=np.int64)
        merged[0::2] = even
        merged[1::2] = odd
        current = merged
    if not 0 <= original_count <= current.size:
        raise ValueError("R-145 original sample count exceeds synthesis")
    return current[:original_count]


def _render_gain(
    basis: np.ndarray,
    gain_q15: int,
) -> np.ndarray:
    product = np.asarray(basis, dtype=np.int64) * int(gain_q15)
    return np.where(
        product >= 0,
        (product + 16384) // 32768,
        -((-product + 16384) // 32768),
    )


def _discover_band_dictionary(
    source: np.ndarray,
    block_samples: int,
    *,
    maximum_normalized_error: float,
    maximum_bases: int,
    maximum_instances: int,
) -> tuple[
    list[np.ndarray],
    list[tuple[int, int, int, int]],
    np.ndarray,
    dict,
]:
    complete_blocks = source.size // block_samples
    buckets: dict[bytes, list[int]] = {}
    for block_index in range(complete_blocks):
        start = block_index * block_samples
        block = source[start : start + block_samples]
        if int(np.max(np.abs(block))) < 8:
            continue
        buckets.setdefault(_canonical_fingerprint(block), []).append(start)

    proposals: list[
        tuple[int, np.ndarray, list[tuple[int, int, int, float]]]
    ] = []
    remaining_seed_budget = maximum_bases * 8
    for starts in buckets.values():
        remaining = list(starts)
        while len(remaining) >= 2 and remaining_seed_budget > 0:
            remaining_seed_budget -= 1
            basis = source[
                remaining[0] : remaining[0] + block_samples
            ].copy()
            matches: list[tuple[int, int, int, float]] = []
            unmatched: list[int] = []
            for start in remaining:
                gain, source_offset, error = _fit_gain_shift_q15(
                    basis,
                    source[start : start + block_samples],
                )
                if error <= maximum_normalized_error:
                    matches.append((start, gain, source_offset, error))
                else:
                    unmatched.append(start)
            if len(matches) >= 2:
                estimated = (
                    (len(matches) - 1) * block_samples * 2
                    - len(matches) * INSTANCE.size
                    - BASIS_HEADER.size
                )
                if estimated > 0:
                    proposals.append((estimated, basis, matches))
                remaining = unmatched
            else:
                remaining = remaining[1:]
        if remaining_seed_budget == 0:
            break
    proposals.sort(key=lambda item: item[0], reverse=True)

    prediction = np.zeros(source.size, dtype=np.int64)
    occupied = np.zeros(complete_blocks, dtype=np.bool_)
    bases: list[np.ndarray] = []
    instances: list[tuple[int, int, int, int]] = []
    fit_errors: list[float] = []
    for _, basis, matches in proposals:
        available = [
            item
            for item in matches
            if not occupied[item[0] // block_samples]
        ]
        if len(available) < 2 or len(bases) >= maximum_bases:
            continue
        available = available[: maximum_instances - len(instances)]
        if len(available) < 2:
            break
        basis_id = len(bases)
        bases.append(basis)
        for start, gain, source_offset, error in available:
            block_index = start // block_samples
            occupied[block_index] = True
            prediction[start : start + block_samples] = _render_gain(
                np.concatenate(
                    (basis[source_offset:], basis[:source_offset])
                ),
                gain,
            )
            instances.append((basis_id, gain, start, source_offset))
            fit_errors.append(error)
        if len(instances) >= maximum_instances:
            break
    return bases, instances, prediction, {
        "complete_blocks": complete_blocks,
        "covered_blocks": int(np.count_nonzero(occupied)),
        "covered_coefficients": int(
            np.count_nonzero(occupied) * block_samples
        ),
        "mean_normalized_fit_error": (
            float(np.mean(fit_errors)) if fit_errors else None
        ),
    }


def _best_truth(
    values: np.ndarray,
    block_sizes: tuple[int, ...],
) -> tuple[bytes, dict]:
    candidates = [
        encode_lpc_liftpack_oracle(values, block_size=int(size))
        for size in block_sizes
    ]
    return min(
        candidates,
        key=lambda item: (len(item[0]), item[1]["block_size"]),
    )


def _pack_stream(
    bands: tuple[np.ndarray, ...],
    original_count: int,
    padded_count: int,
    *,
    block_samples: int,
    truth_block_sizes: tuple[int, ...],
    enable_dictionary: bool,
    maximum_normalized_error: float,
) -> tuple[bytes, list[dict]]:
    band_payloads: list[bytes] = []
    reports: list[dict] = []
    for band_index, source in enumerate(bands):
        if enable_dictionary and source.size >= 2 * block_samples:
            bases, instances, prediction, discovery = (
                _discover_band_dictionary(
                    source,
                    block_samples,
                    maximum_normalized_error=maximum_normalized_error,
                    maximum_bases=64,
                    maximum_instances=4096,
                )
            )
        else:
            bases = []
            instances = []
            prediction = np.zeros(source.size, dtype=np.int64)
            discovery = {
                "complete_blocks": source.size // block_samples,
                "covered_blocks": 0,
                "covered_coefficients": 0,
                "mean_normalized_fit_error": None,
            }

        basis_parts = []
        for basis in bases:
            encoded, _ = encode_lpc_liftpack_oracle(
                basis,
                block_size=max(16, basis.size),
            )
            basis_parts.append(
                BASIS_HEADER.pack(int(basis.size), len(encoded)) + encoded
            )
        basis_blob = b"".join(basis_parts)
        instance_blob = b"".join(
            INSTANCE.pack(basis_id, 1, source_offset, gain, start)
            for basis_id, gain, start, source_offset in instances
        )
        correction, truth_report = _best_truth(
            source - prediction,
            truth_block_sizes,
        )
        band_header = BAND_HEADER.pack(
            int(source.size),
            int(block_samples),
            len(bases),
            len(instances),
            len(basis_blob),
            len(correction),
        )
        band_payloads.append(
            band_header + basis_blob + instance_blob + correction
        )
        reports.append(
            {
                "band_index": band_index,
                "coefficient_count": int(source.size),
                "basis_count": len(bases),
                "instance_count": len(instances),
                "basis_bytes": len(basis_blob),
                "instance_bytes": len(instance_blob),
                "truth_bytes": len(correction),
                "truth": truth_report,
                "discovery": discovery,
            }
        )
    header = HEADER.pack(
        MAGIC,
        VERSION,
        len(bands) - 1,
        len(bands),
        original_count,
        padded_count,
    )
    body = header + b"".join(band_payloads)
    return body + CHECKSUM.pack(zlib.crc32(body) & 0xFFFF_FFFF), reports


def decode_partial_spectrum_orbit(payload: bytes) -> np.ndarray:
    """Independently decode and validate one exact PSO1 stream."""

    if len(payload) < HEADER.size + CHECKSUM.size:
        raise ValueError("truncated PSO1 stream")
    body = payload[:-CHECKSUM.size]
    if zlib.crc32(body) & 0xFFFF_FFFF != CHECKSUM.unpack_from(
        payload,
        len(body),
    )[0]:
        raise ValueError("PSO1 checksum mismatch")
    magic, version, levels, band_count, original_count, padded_count = (
        HEADER.unpack_from(body)
    )
    if (
        magic != MAGIC
        or version != VERSION
        or levels + 1 != band_count
        or not 1 <= levels <= 8
        or padded_count % (1 << levels) != 0
        or original_count > padded_count
    ):
        raise ValueError("invalid PSO1 header")
    cursor = HEADER.size
    bands: list[np.ndarray] = []
    for _ in range(band_count):
        if len(body) - cursor < BAND_HEADER.size:
            raise ValueError("truncated PSO1 band")
        (
            coefficient_count,
            block_samples,
            basis_count,
            instance_count,
            basis_bytes,
            truth_bytes,
        ) = BAND_HEADER.unpack_from(body, cursor)
        cursor += BAND_HEADER.size
        basis_end = cursor + basis_bytes
        if basis_end > len(body):
            raise ValueError("truncated PSO1 Basis blob")
        bases = []
        for _ in range(basis_count):
            if basis_end - cursor < BASIS_HEADER.size:
                raise ValueError("truncated PSO1 Basis")
            sample_count, encoded_bytes = BASIS_HEADER.unpack_from(
                body,
                cursor,
            )
            cursor += BASIS_HEADER.size
            if encoded_bytes > basis_end - cursor:
                raise ValueError("truncated PSO1 Basis payload")
            basis = decode_lpc_liftpack_oracle(
                body[cursor : cursor + encoded_bytes],
                expected_count=sample_count,
            )
            cursor += encoded_bytes
            bases.append(basis)
        if cursor != basis_end:
            raise ValueError("trailing PSO1 Basis bytes")

        prediction = np.zeros(coefficient_count, dtype=np.int64)
        occupied = np.zeros(coefficient_count, dtype=np.bool_)
        for _ in range(instance_count):
            if len(body) - cursor < INSTANCE.size:
                raise ValueError("truncated PSO1 instance")
            basis_id, flags, source_offset, gain, start = (
                INSTANCE.unpack_from(body, cursor)
            )
            cursor += INSTANCE.size
            if (
                flags != 1
                or basis_id >= len(bases)
                or bases[basis_id].size != block_samples
                or source_offset >= block_samples
                or start > coefficient_count
                or block_samples > coefficient_count - start
                or np.any(occupied[start : start + block_samples])
            ):
                raise ValueError("invalid PSO1 instance")
            prediction[start : start + block_samples] = _render_gain(
                np.concatenate(
                    (
                        bases[basis_id][source_offset:],
                        bases[basis_id][:source_offset],
                    )
                ),
                gain,
            )
            occupied[start : start + block_samples] = True

        if truth_bytes > len(body) - cursor:
            raise ValueError("truncated PSO1 Truth")
        correction = decode_lpc_liftpack_oracle(
            body[cursor : cursor + truth_bytes],
            expected_count=coefficient_count,
        )
        cursor += truth_bytes
        bands.append(prediction + correction)
    if cursor != len(body):
        raise ValueError("trailing PSO1 bytes")
    restored = reversible_multiband_synthesis(
        tuple(bands),
        original_count,
    )
    if restored.size != original_count:
        raise RuntimeError("PSO1 synthesis count mismatch")
    return restored


def encode_partial_spectrum_orbit(
    samples: np.ndarray,
    *,
    levels: int = 3,
    block_samples: int = 64,
    truth_block_sizes: tuple[int, ...] = (1024, 4096, 16384),
    maximum_normalized_error: float = 5.0e-2,
) -> PartialSpectrumOrbitCandidate:
    """Compete semantic-free partial-band reuse with multiband Truth."""

    source_matrix = np.asarray(samples)
    if (
        source_matrix.ndim != 2
        or source_matrix.shape[1] != 1
        or source_matrix.dtype != np.int16
    ):
        raise TypeError("R-145 oracle currently requires mono PCM16")
    source = source_matrix[:, 0].astype(np.int64)
    bands, padded_count = reversible_multiband_analysis(source, levels)
    truth_payload, truth_bands = _pack_stream(
        bands,
        source.size,
        padded_count,
        block_samples=block_samples,
        truth_block_sizes=truth_block_sizes,
        enable_dictionary=False,
        maximum_normalized_error=maximum_normalized_error,
    )
    dictionary_payload, dictionary_bands = _pack_stream(
        bands,
        source.size,
        padded_count,
        block_samples=block_samples,
        truth_block_sizes=truth_block_sizes,
        enable_dictionary=True,
        maximum_normalized_error=maximum_normalized_error,
    )
    decoded_dictionary = decode_partial_spectrum_orbit(dictionary_payload)
    decoded_truth = decode_partial_spectrum_orbit(truth_payload)
    if (
        not np.array_equal(decoded_dictionary, source)
        or not np.array_equal(decoded_truth, source)
    ):
        raise RuntimeError("R-145 exact round trip failed")
    selected_dictionary = len(dictionary_payload) < len(truth_payload)
    selected_payload = dictionary_payload if selected_dictionary else truth_payload
    return PartialSpectrumOrbitCandidate(
        payload=selected_payload,
        dictionary_payload=dictionary_payload,
        multiband_truth_payload=truth_payload,
        reconstruction=source_matrix.copy(),
        report={
            "schema": "resonith-r145-partial-spectrum-orbit-1",
            "status": "lossless research candidate; not a codec claim",
            "levels": levels,
            "block_samples": block_samples,
            "dictionary_bytes": len(dictionary_payload),
            "multiband_truth_bytes": len(truth_payload),
            "selected": (
                "partial-spectrum-dictionary"
                if selected_dictionary
                else "multiband-truth-fallback"
            ),
            "selected_bytes": len(selected_payload),
            "dictionary_bands": dictionary_bands,
            "truth_bands": truth_bands,
        },
    )
