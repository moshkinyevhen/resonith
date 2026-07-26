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
    LPCBlockInfo,
    LPCOracleResult,
    decode_lpc_liftpack_block,
    decode_lpc_liftpack_oracle,
    encode_lpc_liftpack_oracle,
    index_lpc_liftpack_blocks,
    run_lpc_liftpack_oracle,
)
from .lapped_oracle import (
    LappedAnalysis,
    LappedDecodeResult,
    LappedEncodeResult,
    analyze_lapped_source,
    decode_lapped_stream,
    encode_lapped_analysis,
    encode_lapped_stream,
    pack_lapped_selected_grid,
    pack_lapped_selected_payload,
    synthesize_lapped_selected_grid,
)
from .lapped_streaming import (
    LappedPacketDecodeResult,
    LappedPacketEncodeResult,
    LappedPacketStreamInfo,
    LappedPacketView,
    decode_lapped_packet_stream,
    decode_lapped_packet_view,
    encode_lapped_packet_stream,
    encode_lapped_transform_packet_stream,
    index_lapped_packet_stream,
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
from .packet_loss import (
    PacketLossSimulationResult,
    simulate_aligned_packet_loss,
    simulate_lapped_packet_loss,
)
from .opus_anchor import run_opus_multichannel_anchor
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
    "LPCBlockInfo",
    "LappedDecodeResult",
    "LappedEncodeResult",
    "LappedAnalysis",
    "LappedPacketDecodeResult",
    "LappedPacketEncodeResult",
    "LappedPacketStreamInfo",
    "LappedPacketView",
    "NativeMain0Decoder",
    "NativeMultichannelDecodeResult",
    "NativeMultichannelRequirements",
    "PacketLossSimulationResult",
    "analyze_lapped_source",
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
    "decode_lpc_liftpack_block",
    "decode_lapped_stream",
    "decode_lapped_packet_stream",
    "decode_lapped_packet_view",
    "encode_lapped_analysis",
    "encode_liftpack",
    "encode_lpc_liftpack_oracle",
    "encode_lapped_stream",
    "encode_lapped_packet_stream",
    "encode_lapped_transform_packet_stream",
    "index_lapped_packet_stream",
    "pack_lapped_selected_grid",
    "pack_lapped_selected_payload",
    "synthesize_lapped_selected_grid",
    "index_lpc_liftpack_blocks",
    "SegmentationResult",
    "segment_acoustic_states",
    "simulate_aligned_packet_loss",
    "simulate_lapped_packet_loss",
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
    "run_opus_multichannel_anchor",
    "write_pcm16_mono",
    "write_pcm16_channels",
]
