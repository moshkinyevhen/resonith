"""Independent-channel Main-0 transport and complete-byte encoder RDO."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Sequence

import numpy as np

from .codec import _quality_report, _quantize_signed
from .lpc_oracle import (
    STREAM_HEADER as RSL2_HEADER,
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
)
from .rsc1 import (
    SECTION_CRITICAL,
    RSC1Section,
    pack_rsc1,
    parse_rsc1,
)
from .stream_sections import StreamConfig, pack_conf, unpack_conf


MAX_CHANNELS = 8
KNOWN_TYPES = frozenset({b"CONF", b"RSL2"})


@dataclass(frozen=True)
class IndependentChannelDecodeResult:
    """Verified interleaved PCM and transport parameters."""

    sample_rate: int
    samples: np.ndarray
    innovation_step: int
    residual_block_size: int


@dataclass(frozen=True)
class IndependentChannelEncodeResult:
    """Winning complete stream, reconstruction, and RDO evidence."""

    payload: bytes
    reconstruction: np.ndarray
    report: dict


def _validated_innovation_matrix(innovation_q: np.ndarray) -> np.ndarray:
    """Return a canonical signed frames-by-channels Innovation view."""

    innovation = np.asarray(innovation_q)
    if (
        innovation.ndim != 2
        or not np.issubdtype(innovation.dtype, np.signedinteger)
    ):
        raise TypeError(
            "independent-channel Innovation must be a signed 2D matrix"
        )
    if innovation.shape[0] == 0:
        raise ValueError("independent-channel stream must contain frames")
    if not 1 <= innovation.shape[1] <= MAX_CHANNELS:
        raise ValueError("independent-channel stream exceeds eight channels")
    return innovation


def pack_main0_independent_stream(
    *,
    sample_rate: int,
    innovation_q: np.ndarray,
    innovation_step: int,
    residual_block_size: int = 4096,
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> bytes:
    """Pack aligned per-channel RSL2 payloads into one Main-0 RSC1 stream."""

    innovation = _validated_innovation_matrix(innovation_q)
    config = StreamConfig(
        sample_count=int(innovation.shape[0]),
        innovation_step=innovation_step,
        output_channels=int(innovation.shape[1]),
    )
    sections = [RSC1Section("CONF", pack_conf(config))]
    for channel in range(innovation.shape[1]):
        residual, _ = encode_lpc_liftpack_oracle(
            innovation[:, channel],
            block_size=residual_block_size,
            lpc_orders=lpc_orders,
        )
        sections.append(
            RSC1Section(
                "RSL2",
                residual,
                instance_id=channel,
                start_tick=0,
            )
        )
    return pack_rsc1(
        sections,
        profile=0,
        level=0,
        timebase_hz=sample_rate,
    )


def decode_main0_independent_stream(
    payload: bytes,
) -> IndependentChannelDecodeResult:
    """Verify and decode the independent-channel Main-0 subset."""

    info = parse_rsc1(payload)
    if (info.profile, info.level) != (0, 0):
        raise ValueError("unsupported Resonith profile or level")

    config_sections: list[RSC1Section] = []
    residual_sections: list[RSC1Section] = []
    for section in info.sections:
        type_code = bytes(section.type_code)
        if type_code not in KNOWN_TYPES:
            if section.flags & SECTION_CRITICAL:
                raise ValueError(
                    "unknown critical independent-channel section"
                )
            continue
        if section.schema_version != 1:
            raise ValueError(
                "unsupported independent-channel section schema"
            )
        if not section.flags & SECTION_CRITICAL:
            raise ValueError(
                "known independent-channel sections must be critical"
            )
        if type_code == b"CONF":
            config_sections.append(section)
        else:
            residual_sections.append(section)

    if (
        len(config_sections) != 1
        or config_sections[0].instance_id != 0
        or config_sections[0].start_tick != 0
    ):
        raise ValueError("non-canonical independent-channel CONF")
    config = unpack_conf(config_sections[0].payload)
    expected_ids = list(range(config.output_channels))
    if [section.instance_id for section in residual_sections] != expected_ids:
        raise ValueError("non-canonical independent-channel RSL2 instances")
    if any(section.start_tick != 0 for section in residual_sections):
        raise ValueError("independent-channel RSL2 must start at tick zero")

    channels: list[np.ndarray] = []
    common_block_size: int | None = None
    common_block_count: int | None = None
    for section in residual_sections:
        if len(section.payload) < RSL2_HEADER.size:
            raise ValueError("truncated independent-channel RSL2 header")
        (
            _magic,
            _version,
            block_size,
            sample_count,
            block_count,
        ) = RSL2_HEADER.unpack_from(section.payload)
        if sample_count != config.sample_count:
            raise ValueError("independent-channel frame count mismatch")
        if common_block_size is None:
            common_block_size = block_size
            common_block_count = block_count
        elif (
            block_size != common_block_size
            or block_count != common_block_count
        ):
            raise ValueError("independent-channel block partitions differ")
        channels.append(
            decode_lpc_liftpack_oracle(
                section.payload,
                expected_count=config.sample_count,
            )
        )

    innovation = np.stack(channels, axis=1)
    reconstruction = np.clip(
        innovation * np.int64(config.innovation_step),
        -32768,
        32767,
    ).astype(np.int16)
    reconstruction.flags.writeable = False
    return IndependentChannelDecodeResult(
        sample_rate=info.timebase_hz,
        samples=reconstruction,
        innovation_step=config.innovation_step,
        residual_block_size=int(common_block_size),
    )


def encode_main0_independent_rdo(
    samples: np.ndarray,
    sample_rate: int,
    *,
    innovation_step: int = 1,
    residual_block_sizes: Sequence[int] = (4096, 16384, 32768),
    lpc_orders: tuple[int, ...] = (4, 8, 12, 16),
) -> IndependentChannelEncodeResult:
    """Choose one aligned channel partition by minimum complete RSC1 bytes."""

    source = np.asarray(samples)
    if source.dtype != np.int16 or source.ndim != 2:
        raise TypeError("independent-channel input must be 2D int16 PCM")
    if source.shape[0] == 0 or not 1 <= source.shape[1] <= MAX_CHANNELS:
        raise ValueError("invalid independent-channel PCM shape")
    if sample_rate <= 0:
        raise ValueError("sample rate must be positive")
    blocks = tuple(sorted({int(value) for value in residual_block_sizes}))
    if not blocks or blocks[0] < 16 or blocks[-1] > 32768:
        raise ValueError("independent-channel RSL2 block bound exceeded")

    innovation = np.empty(source.shape, dtype=np.int64)
    for channel in range(source.shape[1]):
        innovation[:, channel] = _quantize_signed(
            source[:, channel].astype(np.int64),
            innovation_step,
        )

    candidates: list[tuple[bytes, IndependentChannelDecodeResult, dict]] = []
    for block_size in blocks:
        payload = pack_main0_independent_stream(
            sample_rate=sample_rate,
            innovation_q=innovation,
            innovation_step=innovation_step,
            residual_block_size=block_size,
            lpc_orders=lpc_orders,
        )
        decoded = decode_main0_independent_stream(payload)
        if decoded.samples.shape != source.shape:
            raise RuntimeError("independent-channel decoder shape mismatch")
        info = parse_rsc1(payload)
        residual_bytes = [
            len(section.payload)
            for section in info.sections
            if bytes(section.type_code) == b"RSL2"
        ]
        report = {
            "stream_bytes": len(payload),
            "stream_sha256": hashlib.sha256(payload).hexdigest(),
            "residual_block_size": block_size,
            "channel_residual_bytes": residual_bytes,
            "channel_count": int(source.shape[1]),
            "frame_count": int(source.shape[0]),
            **_quality_report(source.reshape(-1), decoded.samples.reshape(-1)),
        }
        candidates.append((payload, decoded, report))

    payload, decoded, report = min(
        candidates,
        key=lambda item: (
            item[2]["stream_bytes"],
            item[2]["residual_block_size"],
        ),
    )
    final_report = {
        **report,
        "status": "independent-channel Main-0 normative draft",
        "format_profile": "Main-0-independent-channel-RSC1",
        "rdo_objective": "minimum complete aligned multichannel RSC1 bytes",
        "candidates": [candidate[2] for candidate in candidates],
    }
    return IndependentChannelEncodeResult(
        payload,
        decoded.samples,
        final_report,
    )
