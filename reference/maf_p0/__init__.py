"""MAF-P0: first end-to-end periodic audio codec prototype."""

from .additive_oracle import AdditiveOracleResult, run_additive_atom_oracle
from .analytic_oracle import (
    AnalyticOracleResult,
    run_analytic_oscillator_oracle,
)
from .cached_additive_oracle import (
    CachedAdditiveOracleResult,
    pack_registry_model,
    run_cached_additive_oracle,
)
from .codec import DecodeResult, EncodeResult, decode_bytes, encode_samples
from .model import (
    encode_basis_latent,
    load_analysis_model,
    save_analysis_model,
    train_linear_cibs,
)
from .lpc_oracle import (
    LPCOracleResult,
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
    run_lpc_liftpack_oracle,
)
from .main0 import (
    Main0DecodeResult,
    Main0EncodeResult,
    Main0State,
    decode_main0_raw_stream,
    encode_main0_periodic_rdo,
    encode_main0_state_rdo,
    pack_main0_cibs_stream,
    pack_main0_raw_stream,
    pack_main0_lpc_residual_stream,
    pack_main0_residual_stream,
    pack_main0_state_stream,
)
from .multichannel import (
    IndependentChannelDecodeResult,
    IndependentChannelEncodeResult,
    decode_main0_independent_stream,
    encode_main0_independent_rdo,
    pack_main0_independent_stream,
)
from .native_core import (
    NativeMain0Decoder,
    NativeMultichannelDecodeResult,
    NativeMultichannelRequirements,
)
from .periodic import PhaseTrajectory
from .residual import ResidualPacket, decode_liftpack, encode_liftpack
from .segmentation import SegmentationResult, segment_acoustic_states
from .stateful import (
    decode_stateful_bytes,
    encode_stateful_rdo_samples,
    encode_stateful_samples,
)
from .wav_io import (
    read_pcm16_channels,
    read_pcm16_mono,
    write_pcm16_channels,
    write_pcm16_mono,
)

__all__ = [
    "AdditiveOracleResult",
    "AnalyticOracleResult",
    "CachedAdditiveOracleResult",
    "DecodeResult",
    "EncodeResult",
    "Main0DecodeResult",
    "Main0EncodeResult",
    "Main0State",
    "IndependentChannelDecodeResult",
    "IndependentChannelEncodeResult",
    "LPCOracleResult",
    "NativeMain0Decoder",
    "NativeMultichannelDecodeResult",
    "NativeMultichannelRequirements",
    "decode_bytes",
    "decode_main0_raw_stream",
    "decode_main0_independent_stream",
    "encode_main0_periodic_rdo",
    "encode_main0_state_rdo",
    "encode_main0_independent_rdo",
    "encode_samples",
    "pack_main0_cibs_stream",
    "pack_main0_raw_stream",
    "pack_main0_lpc_residual_stream",
    "pack_main0_residual_stream",
    "pack_main0_state_stream",
    "pack_main0_independent_stream",
    "pack_registry_model",
    "decode_stateful_bytes",
    "encode_stateful_samples",
    "encode_stateful_rdo_samples",
    "PhaseTrajectory",
    "ResidualPacket",
    "decode_liftpack",
    "decode_lpc_liftpack_oracle",
    "encode_liftpack",
    "encode_lpc_liftpack_oracle",
    "SegmentationResult",
    "segment_acoustic_states",
    "encode_basis_latent",
    "load_analysis_model",
    "save_analysis_model",
    "train_linear_cibs",
    "read_pcm16_mono",
    "read_pcm16_channels",
    "run_additive_atom_oracle",
    "run_analytic_oscillator_oracle",
    "run_cached_additive_oracle",
    "run_lpc_liftpack_oracle",
    "write_pcm16_mono",
    "write_pcm16_channels",
]
