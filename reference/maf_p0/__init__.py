"""MAF-P0: first end-to-end periodic audio codec prototype."""

from .codec import DecodeResult, EncodeResult, decode_bytes, encode_samples
from .model import (
    encode_basis_latent,
    load_analysis_model,
    save_analysis_model,
    train_linear_cibs,
)
from .main0 import (
    Main0DecodeResult,
    Main0EncodeResult,
    decode_main0_raw_stream,
    encode_main0_periodic_rdo,
    pack_main0_raw_stream,
)
from .native_core import NativeMain0Decoder
from .periodic import PhaseTrajectory
from .residual import ResidualPacket, decode_liftpack, encode_liftpack
from .segmentation import SegmentationResult, segment_acoustic_states
from .stateful import (
    decode_stateful_bytes,
    encode_stateful_rdo_samples,
    encode_stateful_samples,
)
from .wav_io import read_pcm16_mono, write_pcm16_mono

__all__ = [
    "DecodeResult",
    "EncodeResult",
    "Main0DecodeResult",
    "Main0EncodeResult",
    "NativeMain0Decoder",
    "decode_bytes",
    "decode_main0_raw_stream",
    "encode_main0_periodic_rdo",
    "encode_samples",
    "pack_main0_raw_stream",
    "decode_stateful_bytes",
    "encode_stateful_samples",
    "encode_stateful_rdo_samples",
    "PhaseTrajectory",
    "ResidualPacket",
    "decode_liftpack",
    "encode_liftpack",
    "SegmentationResult",
    "segment_acoustic_states",
    "encode_basis_latent",
    "load_analysis_model",
    "save_analysis_model",
    "train_linear_cibs",
    "read_pcm16_mono",
    "write_pcm16_mono",
]
