"""Strict bounded PCM16 WAV I/O for Resonith reference tools."""

from __future__ import annotations

from pathlib import Path
import wave

import numpy as np


def read_pcm16_channels(path: str | Path) -> tuple[int, np.ndarray]:
    """Read canonical frame-major PCM16 with one through eight channels."""

    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        if not 1 <= channels <= 8:
            raise ValueError("Resonith accepts one through eight WAV channels")
        if source.getsampwidth() != 2:
            raise ValueError("Resonith accepts PCM16 WAV only")
        if source.getcomptype() != "NONE":
            raise ValueError("compressed WAV input is not supported")
        sample_rate = source.getframerate()
        frame_count = source.getnframes()
        frame_bytes = source.readframes(frame_count)
    samples = np.frombuffer(frame_bytes, dtype="<i2").astype(
        np.int16,
        copy=True,
    )
    expected_elements = frame_count * channels
    if samples.size != expected_elements:
        raise ValueError("truncated PCM16 WAV frame payload")
    return sample_rate, samples.reshape(frame_count, channels)


def read_pcm16_mono(path: str | Path) -> tuple[int, np.ndarray]:
    sample_rate, channels = read_pcm16_channels(path)
    if channels.shape[1] != 1:
        raise ValueError("this analysis path accepts mono WAV only")
    return sample_rate, channels[:, 0].copy()


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
