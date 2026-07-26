"""Strict PCM16 mono WAV I/O for the first codec prototype."""

from __future__ import annotations

from pathlib import Path
import wave

import numpy as np


def read_pcm16_mono(path: str | Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 1:
            raise ValueError("MAF-P0 accepts mono WAV only")
        if source.getsampwidth() != 2:
            raise ValueError("MAF-P0 accepts PCM16 WAV only")
        if source.getcomptype() != "NONE":
            raise ValueError("compressed WAV input is not supported")
        sample_rate = source.getframerate()
        frames = source.readframes(source.getnframes())
    samples = np.frombuffer(frames, dtype="<i2").astype(np.int16, copy=True)
    return sample_rate, samples


def write_pcm16_mono(
    path: str | Path,
    sample_rate: int,
    samples: np.ndarray,
) -> None:
    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    with wave.open(str(path), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(sample_rate)
        destination.writeframes(samples.astype("<i2", copy=False).tobytes())


def write_pcm16_channels(
    path: str | Path,
    sample_rate: int,
    samples: np.ndarray,
) -> None:
    """Write frame-major PCM16 with a bounded explicit channel count."""

    if (
        samples.dtype != np.int16
        or samples.ndim != 2
        or not 1 <= samples.shape[1] <= 8
    ):
        raise TypeError("samples must be frame-major int16 with 1-8 channels")
    with wave.open(str(path), "wb") as destination:
        destination.setnchannels(int(samples.shape[1]))
        destination.setsampwidth(2)
        destination.setframerate(sample_rate)
        destination.writeframes(samples.astype("<i2", copy=False).tobytes())
