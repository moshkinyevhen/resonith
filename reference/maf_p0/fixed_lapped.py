"""Deterministic fixed-integer lapped transform research kernel."""

from __future__ import annotations

from functools import lru_cache
import hashlib

import numpy as np


WINDOW_FRACTION_BITS = 15
COSINE_FRACTION_BITS = 14
ANALYSIS_FRACTION_BITS = WINDOW_FRACTION_BITS + COSINE_FRACTION_BITS
MAX_HALF_WINDOW = 1024


def round_shift_signed(values: np.ndarray, shift: int) -> np.ndarray:
    """Round signed int64 values symmetrically, with halves away from zero."""

    source = np.asarray(values, dtype=np.int64)
    if not 0 < shift < 63:
        raise ValueError("fixed lapped shift is outside the int64 bound")
    rounding = np.int64(1 << (shift - 1))
    return np.where(
        source >= 0,
        (source + rounding) >> shift,
        -(((-source) + rounding) >> shift),
    ).astype(np.int64)


@lru_cache(maxsize=8)
def fixed_lapped_tables(
    half_window: int,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Materialize prospective Q15/Q14 ROM and its canonical byte identity."""

    if (
        half_window < 32
        or half_window > MAX_HALF_WINDOW
        or half_window & (half_window - 1)
    ):
        raise ValueError("fixed lapped half-window must be a power of two")
    sample = np.arange(2 * half_window, dtype=np.float64)
    coefficient = np.arange(half_window, dtype=np.float64)
    window_float = np.sin(
        np.pi / (2.0 * half_window) * (sample + 0.5)
    )
    cosine_float = np.cos(
        np.pi
        / half_window
        * np.outer(
            coefficient + 0.5,
            sample + 0.5 + half_window / 2.0,
        )
    )
    window = np.rint(
        window_float * float(1 << WINDOW_FRACTION_BITS)
    ).astype("<i4")
    cosine = np.rint(
        cosine_float * float(1 << COSINE_FRACTION_BITS)
    ).astype("<i4")
    identity = hashlib.sha256(
        window.tobytes(order="C") + cosine.tobytes(order="C")
    ).hexdigest()
    window.flags.writeable = False
    cosine.flags.writeable = False
    return window, cosine, identity


def analyze_fixed_lapped(block: np.ndarray, half_window: int) -> np.ndarray:
    """Analyze one exact two-half-window PCM block into integer coefficients."""

    source = np.asarray(block)
    if (
        source.ndim != 1
        or source.size != 2 * half_window
        or not np.issubdtype(source.dtype, np.signedinteger)
    ):
        raise TypeError("fixed lapped analysis requires one signed PCM block")
    window, cosine, _identity = fixed_lapped_tables(half_window)
    windowed_q15 = source.astype(np.int64) * window.astype(np.int64)
    accumulator_q29 = windowed_q15 @ cosine.astype(np.int64).T
    return round_shift_signed(
        accumulator_q29,
        ANALYSIS_FRACTION_BITS,
    )


def synthesize_fixed_lapped_frame(
    coefficients: np.ndarray,
    half_window: int,
) -> np.ndarray:
    """Return one unrounded Q29 synthesis contribution for overlap-add."""

    source = np.asarray(coefficients)
    if (
        source.ndim != 1
        or source.size != half_window
        or not np.issubdtype(source.dtype, np.signedinteger)
    ):
        raise TypeError("fixed lapped synthesis requires one coefficient row")
    window, cosine, _identity = fixed_lapped_tables(half_window)
    time_q14 = source.astype(np.int64) @ cosine.astype(np.int64)
    return time_q14 * window.astype(np.int64)


def synthesis_output_shift(half_window: int) -> int:
    """Return the Q29 plus inverse 2/N normalization shift."""

    fixed_lapped_tables(half_window)
    return ANALYSIS_FRACTION_BITS + half_window.bit_length() - 2
