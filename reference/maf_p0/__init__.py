"""MAF-P0: first end-to-end periodic audio codec prototype."""

from .codec import DecodeResult, EncodeResult, decode_bytes, encode_samples
from .model import (
    encode_basis_latent,
    load_analysis_model,
    save_analysis_model,
    train_linear_cibs,
)
from .periodic import PhaseTrajectory
from .stateful import decode_stateful_bytes, encode_stateful_samples
from .wav_io import read_pcm16_mono, write_pcm16_mono

__all__ = [
    "DecodeResult",
    "EncodeResult",
    "decode_bytes",
    "encode_samples",
    "decode_stateful_bytes",
    "encode_stateful_samples",
    "PhaseTrajectory",
    "encode_basis_latent",
    "load_analysis_model",
    "save_analysis_model",
    "train_linear_cibs",
    "read_pcm16_mono",
    "write_pcm16_mono",
]
