"""Sparse absolute gain events and objective Truth composition."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


MAX_EVENTS = 1_000_000
MAX_SAMPLE_COUNT = (1 << 31) - 1
MIN_GAIN_Q15 = -131072
MAX_GAIN_Q15 = 131071
MAX_INNOVATION_STEP = 1 << 20


@dataclass(frozen=True)
class GainEventLaw:
    """Piecewise-constant signed Q17.15 gain on an absolute sample timeline."""

    positions: np.ndarray
    gains_q15: np.ndarray
    sample_count: int

    def __post_init__(self) -> None:
        positions = np.asarray(self.positions, dtype=np.uint32).copy()
        gains = np.asarray(self.gains_q15, dtype=np.int32).copy()
        if positions.ndim != 1 or gains.ndim != 1:
            raise TypeError("gain event arrays must be one-dimensional")
        if (
            positions.size == 0
            or positions.size != gains.size
            or positions.size > MAX_EVENTS
        ):
            raise ValueError("invalid gain event count")
        if not 0 < self.sample_count <= MAX_SAMPLE_COUNT:
            raise ValueError("invalid gain law sample count")
        if int(positions[0]) != 0 or np.any(np.diff(positions.astype(np.int64)) <= 0):
            raise ValueError("gain positions must start at zero and increase")
        if int(positions[-1]) >= self.sample_count:
            raise ValueError("gain event is outside the sample timeline")
        if np.any(gains < MIN_GAIN_Q15) or np.any(gains > MAX_GAIN_Q15):
            raise ValueError("gain exceeds the Q17.15 profile bound")
        positions.flags.writeable = False
        gains.flags.writeable = False
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "gains_q15", gains)


def compose_truth(
    unity_prediction: np.ndarray,
    gain_law: GainEventLaw,
    *,
    output_start: int = 0,
    innovation_q: np.ndarray | None = None,
    innovation_step: int = 1,
) -> np.ndarray:
    """Apply sparse gains and optional objective Innovation to one slice."""

    unity = np.asarray(unity_prediction)
    if unity.dtype != np.int16 or unity.ndim != 1:
        raise TypeError("unity prediction must be mono int16")
    if output_start < 0 or output_start + unity.size > gain_law.sample_count:
        raise ValueError("composition slice is outside the gain law")
    if innovation_q is None:
        innovation = np.zeros(unity.size, dtype=np.int64)
    else:
        innovation = np.asarray(innovation_q)
        if innovation.dtype != np.int64 or innovation.shape != unity.shape:
            raise TypeError("Innovation must be an int64 vector matching output")
        if not 1 <= innovation_step <= MAX_INNOVATION_STEP:
            raise ValueError("Innovation step exceeds the profile bound")

    absolute = output_start + np.arange(unity.size, dtype=np.uint32)
    event_indices = np.searchsorted(
        gain_law.positions,
        absolute,
        side="right",
    ) - 1
    gains = gain_law.gains_q15[event_indices].astype(np.int64)
    scaled = np.floor_divide(
        unity.astype(np.int64) * gains + 16384,
        32768,
    )
    combined = scaled + innovation.astype(np.int64) * (
        innovation_step if innovation_q is not None else 0
    )
    return np.clip(combined, -32768, 32767).astype(np.int16)
