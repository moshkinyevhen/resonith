"""Deterministic listening-test anchors; never part of codec rate accounting."""

from __future__ import annotations

import numpy as np


def lowpass_anchor(
    samples: np.ndarray,
    sample_rate: int,
    *,
    cutoff_hz: float = 3500.0,
    tap_count: int = 255,
) -> np.ndarray:
    """Return a linear-phase low-pass impairment for listener scale training."""

    source = np.asarray(samples)
    if (
        source.ndim not in (1, 2)
        or source.dtype != np.int16
        or source.size == 0
        or sample_rate <= 0
        or not 0.0 < cutoff_hz < sample_rate / 2.0
        or tap_count < 3
        or tap_count % 2 == 0
    ):
        raise ValueError("invalid low-pass listening-anchor configuration")
    one_dimensional = source.ndim == 1
    channels = source[:, None] if one_dimensional else source
    center = (tap_count - 1) / 2.0
    positions = np.arange(tap_count, dtype=np.float64) - center
    normalized_cutoff = cutoff_hz / sample_rate
    kernel = (
        2.0
        * normalized_cutoff
        * np.sinc(2.0 * normalized_cutoff * positions)
        * np.hamming(tap_count)
    )
    kernel /= np.sum(kernel)
    filtered = np.empty(channels.shape, dtype=np.float64)
    for channel in range(channels.shape[1]):
        filtered[:, channel] = np.convolve(
            channels[:, channel].astype(np.float64),
            kernel,
            mode="same",
        )
    output = np.clip(
        np.rint(filtered),
        np.iinfo(np.int16).min,
        np.iinfo(np.int16).max,
    ).astype(np.int16)
    return output[:, 0] if one_dimensional else output
