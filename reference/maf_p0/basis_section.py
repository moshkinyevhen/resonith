"""Typed BRAW schema-1 Basis payload."""

from __future__ import annotations

import struct

import numpy as np


HEADER = struct.Struct("<HHI")
MAX_CHANNELS = 8
MAX_ELEMENTS = 8 * 2048


def pack_braw(samples: np.ndarray) -> bytes:
    basis = np.asarray(samples)
    if basis.dtype != np.int16 or basis.ndim != 2:
        raise TypeError("BRAW Basis must be int16 [channels, samples]")
    channels, samples_per_channel = basis.shape
    if (
        not 1 <= channels <= MAX_CHANNELS
        or samples_per_channel < 1
        or basis.size > MAX_ELEMENTS
    ):
        raise ValueError("BRAW Basis exceeds the profile bound")
    return (
        HEADER.pack(channels, 0, samples_per_channel)
        + basis.astype("<i2", copy=False).tobytes(order="C")
    )


def unpack_braw(payload: bytes) -> np.ndarray:
    if len(payload) < HEADER.size:
        raise ValueError("truncated BRAW header")
    channels, flags, samples_per_channel = HEADER.unpack_from(payload)
    elements = channels * samples_per_channel
    if (
        not 1 <= channels <= MAX_CHANNELS
        or samples_per_channel < 1
        or elements > MAX_ELEMENTS
    ):
        raise ValueError("BRAW Basis exceeds the profile bound")
    if flags != 0:
        raise ValueError("unsupported BRAW feature")
    if len(payload) != HEADER.size + elements * 2:
        raise ValueError("BRAW payload size mismatch")
    return np.frombuffer(
        payload,
        dtype="<i2",
        offset=HEADER.size,
        count=elements,
    ).reshape(channels, samples_per_channel).copy()
