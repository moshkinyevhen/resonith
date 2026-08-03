"""Reproducible external Opus anchor using the official opus-tools CLI."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np

from .codec import _quality_report
from .wav_io import (
    read_pcm16_channels,
    read_pcm16_mono,
    write_pcm16_channels,
    write_pcm16_mono,
)


@dataclass(frozen=True)
class OpusTools:
    """Resolved encoder/decoder pair with immutable provenance."""

    opusenc: Path
    opusdec: Path
    encoder_version: str
    decoder_version: str
    encoder_sha256: str
    decoder_sha256: str


@dataclass(frozen=True)
class OpusAnchorResult:
    payload: bytes
    reconstructed: np.ndarray
    report: dict


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _tool_version(path: Path) -> str:
    result = subprocess.run(
        [str(path), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    text = (result.stdout + result.stderr).strip()
    return text.splitlines()[0] if text else "unknown"


def _normalized_ogg_sha256(payload: bytes) -> tuple[str, int]:
    """Hash Ogg bytes after zeroing random serial and dependent CRC fields."""

    digest = hashlib.sha256()
    cursor = 0
    page_count = 0
    while cursor < len(payload):
        if cursor + 27 > len(payload) or payload[cursor : cursor + 4] != b"OggS":
            raise RuntimeError("Opus anchor produced an invalid Ogg page")
        segment_count = payload[cursor + 26]
        header_end = cursor + 27 + segment_count
        if header_end > len(payload):
            raise RuntimeError("Opus anchor produced a truncated Ogg segment table")
        body_bytes = sum(payload[cursor + 27 : header_end])
        page_end = header_end + body_bytes
        if page_end > len(payload):
            raise RuntimeError("Opus anchor produced a truncated Ogg page")
        page = bytearray(payload[cursor:page_end])
        page[14:18] = b"\0" * 4
        page[22:26] = b"\0" * 4
        digest.update(page)
        cursor = page_end
        page_count += 1
    return digest.hexdigest(), page_count


def resolve_opus_tools(directory: str | Path | None = None) -> OpusTools:
    """Resolve opus-tools explicitly, from the environment, or from `PATH`."""

    candidates: list[tuple[Path, Path]] = []
    configured = directory or os.environ.get("RESONITH_OPUS_TOOLS")
    if configured:
        root = Path(configured)
        candidates.append((root / "opusenc.exe", root / "opusdec.exe"))
        candidates.append((root / "opusenc", root / "opusdec"))
    path_encoder = shutil.which("opusenc")
    path_decoder = shutil.which("opusdec")
    if path_encoder and path_decoder:
        candidates.append((Path(path_encoder), Path(path_decoder)))

    for encoder, decoder in candidates:
        if encoder.is_file() and decoder.is_file():
            return OpusTools(
                encoder.resolve(),
                decoder.resolve(),
                _tool_version(encoder),
                _tool_version(decoder),
                _file_sha256(encoder),
                _file_sha256(decoder),
            )
    raise FileNotFoundError(
        "opusenc/opusdec were not found; set RESONITH_OPUS_TOOLS or pass a directory"
    )


def _run_checked(command: list[str]) -> None:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Opus anchor command failed: {detail}")


def run_opus_anchor(
    samples: np.ndarray,
    sample_rate: int,
    *,
    bitrate_kbps: float,
    mode: str = "vbr",
    application: str = "music",
    frame_size_ms: float = 20.0,
    phase_inversion: bool = True,
    maximum_container_delay_ms: int = 1000,
    expected_loss_percent: int = 0,
    tools: OpusTools | None = None,
    tools_directory: str | Path | None = None,
) -> OpusAnchorResult:
    """Encode and decode one mono PCM16 signal with full Ogg byte accounting."""

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if samples.size == 0 or sample_rate <= 0:
        raise ValueError("invalid anchor input")
    if not 6.0 <= bitrate_kbps <= 256.0:
        raise ValueError("mono Opus bitrate must be between 6 and 256 kbit/s")
    mode_flags = {
        "vbr": "--vbr",
        "cvbr": "--cvbr",
        "hard-cbr": "--hard-cbr",
    }
    if mode not in mode_flags:
        raise ValueError("Opus mode must be vbr, cvbr or hard-cbr")
    if application not in {"music", "speech", "auto"}:
        raise ValueError("Opus application must be music, speech or auto")
    if frame_size_ms not in {2.5, 5.0, 10.0, 20.0, 40.0, 60.0}:
        raise ValueError("unsupported Opus frame size")
    if not 0 <= maximum_container_delay_ms <= 1000:
        raise ValueError("Opus container delay is outside [0, 1000]")
    if not 0 <= expected_loss_percent <= 100:
        raise ValueError("Opus expected loss is outside [0, 100]")

    resolved = tools or resolve_opus_tools(tools_directory)
    with tempfile.TemporaryDirectory(prefix="resonith-opus-anchor-") as directory:
        root = Path(directory)
        source_path = root / "source.wav"
        payload_path = root / "anchor.opus"
        decoded_path = root / "decoded.wav"
        write_pcm16_mono(source_path, sample_rate, samples)

        command = [
            str(resolved.opusenc),
            "--quiet",
            "--bitrate",
            f"{bitrate_kbps:g}",
            mode_flags[mode],
            "--framesize",
            f"{frame_size_ms:g}",
            "--comp",
            "10",
            "--expect-loss",
            str(expected_loss_percent),
            "--max-delay",
            str(maximum_container_delay_ms),
            "--discard-comments",
            "--padding",
            "0",
        ]
        if application != "auto":
            command.append(f"--{application}")
        if not phase_inversion:
            command.append("--no-phase-inv")
        command.extend((str(source_path), str(payload_path)))
        _run_checked(command)
        _run_checked(
            [
                str(resolved.opusdec),
                "--quiet",
                "--rate",
                str(sample_rate),
                str(payload_path),
                str(decoded_path),
            ]
        )

        payload = payload_path.read_bytes()
        decoded_rate, reconstructed = read_pcm16_mono(decoded_path)
    if decoded_rate != sample_rate:
        raise RuntimeError("Opus decoder changed the requested sample rate")
    if reconstructed.shape != samples.shape:
        raise RuntimeError(
            f"Opus sample count mismatch: {reconstructed.size} != {samples.size}"
        )

    quality = _quality_report(samples, reconstructed)
    duration_seconds = samples.size / sample_rate
    normalized_hash, page_count = _normalized_ogg_sha256(payload)
    report = {
        **quality,
        "codec": "Opus",
        "container": "Ogg Opus",
        "stream_bytes": len(payload),
        "stream_sha256": normalized_hash,
        "stream_hash_normalization": (
            "Ogg stream serial and page CRC fields are zeroed before hashing"
        ),
        "ogg_page_count": page_count,
        "requested_bitrate_kbps": float(bitrate_kbps),
        "effective_bitrate_kbps": 8.0 * len(payload) / duration_seconds / 1000.0,
        "mode": mode,
        "application": application,
        "frame_size_ms": float(frame_size_ms),
        "complexity": 10,
        "phase_inversion": phase_inversion,
        "maximum_container_delay_ms": maximum_container_delay_ms,
        "expected_loss_percent": expected_loss_percent,
        "sample_rate": int(sample_rate),
        "sample_count": int(samples.size),
        "encoder_version": resolved.encoder_version,
        "decoder_version": resolved.decoder_version,
        "encoder_sha256": resolved.encoder_sha256,
        "decoder_sha256": resolved.decoder_sha256,
    }
    return OpusAnchorResult(payload, reconstructed, report)


def run_opus_multichannel_anchor(
    samples: np.ndarray,
    sample_rate: int,
    *,
    bitrate_kbps: float,
    mode: str = "vbr",
    application: str = "music",
    frame_size_ms: float = 20.0,
    phase_inversion: bool = True,
    maximum_container_delay_ms: int = 1000,
    expected_loss_percent: int = 0,
    tools: OpusTools | None = None,
    tools_directory: str | Path | None = None,
) -> OpusAnchorResult:
    """Encode and decode bounded frame-major PCM16 with official opus-tools."""

    if (
        samples.dtype != np.int16
        or samples.ndim != 2
        or not 1 <= samples.shape[1] <= 8
    ):
        raise TypeError("samples must be frame-major PCM16 with 1-8 channels")
    if samples.shape[0] == 0 or sample_rate <= 0:
        raise ValueError("invalid multichannel anchor input")
    if not 6.0 <= bitrate_kbps <= 256.0 * samples.shape[1]:
        raise ValueError("Opus bitrate exceeds the channel-count bound")
    mode_flags = {
        "vbr": "--vbr",
        "cvbr": "--cvbr",
        "hard-cbr": "--hard-cbr",
    }
    if mode not in mode_flags:
        raise ValueError("Opus mode must be vbr, cvbr or hard-cbr")
    if application not in {"music", "speech", "auto"}:
        raise ValueError("Opus application must be music, speech or auto")
    if frame_size_ms not in {2.5, 5.0, 10.0, 20.0, 40.0, 60.0}:
        raise ValueError("unsupported Opus frame size")
    if not 0 <= maximum_container_delay_ms <= 1000:
        raise ValueError("Opus container delay is outside [0, 1000]")
    if not 0 <= expected_loss_percent <= 100:
        raise ValueError("Opus expected loss is outside [0, 100]")

    resolved = tools or resolve_opus_tools(tools_directory)
    with tempfile.TemporaryDirectory(
        prefix="resonith-opus-multichannel-anchor-"
    ) as directory:
        root = Path(directory)
        source_path = root / "source.wav"
        payload_path = root / "anchor.opus"
        decoded_path = root / "decoded.wav"
        write_pcm16_channels(source_path, sample_rate, samples)
        command = [
            str(resolved.opusenc),
            "--quiet",
            "--bitrate",
            f"{bitrate_kbps:g}",
            mode_flags[mode],
            "--framesize",
            f"{frame_size_ms:g}",
            "--comp",
            "10",
            "--expect-loss",
            str(expected_loss_percent),
            "--max-delay",
            str(maximum_container_delay_ms),
            "--discard-comments",
            "--padding",
            "0",
        ]
        if application != "auto":
            command.append(f"--{application}")
        if not phase_inversion:
            command.append("--no-phase-inv")
        command.extend((str(source_path), str(payload_path)))
        _run_checked(command)
        _run_checked(
            [
                str(resolved.opusdec),
                "--quiet",
                "--rate",
                str(sample_rate),
                str(payload_path),
                str(decoded_path),
            ]
        )
        payload = payload_path.read_bytes()
        decoded_rate, reconstructed = read_pcm16_channels(decoded_path)
    if decoded_rate != sample_rate:
        raise RuntimeError("Opus decoder changed the requested sample rate")
    if reconstructed.shape != samples.shape:
        raise RuntimeError(
            "Opus multichannel frame shape differs from the source"
        )

    quality = _quality_report(
        samples.reshape(-1),
        reconstructed.reshape(-1),
    )
    duration_seconds = samples.shape[0] / sample_rate
    normalized_hash, page_count = _normalized_ogg_sha256(payload)
    report = {
        **quality,
        "codec": "Opus",
        "container": "Ogg Opus",
        "stream_bytes": len(payload),
        "stream_sha256": normalized_hash,
        "stream_hash_normalization": (
            "Ogg stream serial and page CRC fields are zeroed before hashing"
        ),
        "ogg_page_count": page_count,
        "requested_bitrate_kbps": float(bitrate_kbps),
        "effective_bitrate_kbps": (
            8.0 * len(payload) / duration_seconds / 1000.0
        ),
        "mode": mode,
        "application": application,
        "frame_size_ms": float(frame_size_ms),
        "complexity": 10,
        "phase_inversion": phase_inversion,
        "maximum_container_delay_ms": maximum_container_delay_ms,
        "expected_loss_percent": expected_loss_percent,
        "sample_rate": int(sample_rate),
        "frame_count": int(samples.shape[0]),
        "channel_count": int(samples.shape[1]),
        "encoder_version": resolved.encoder_version,
        "decoder_version": resolved.decoder_version,
        "encoder_sha256": resolved.encoder_sha256,
        "decoder_sha256": resolved.decoder_sha256,
    }
    return OpusAnchorResult(payload, reconstructed, report)
