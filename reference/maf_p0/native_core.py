"""Explicit ctypes binding for the Resonith Golden Core C ABI."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Sequence

import numpy as np

from cibs0 import CIBS0Model


DEFAULT_MAX_WORKSPACE_BYTES = 512 << 20


class NativeCoreError(RuntimeError):
    """One non-zero `resonith_status` returned by the native Core."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"Resonith native status {status}: {message}")
        self.status = status


class _Requirements(ctypes.Structure):
    _fields_ = [
        ("timebase_hz", ctypes.c_uint32),
        ("sample_count", ctypes.c_uint32),
        ("basis_elements", ctypes.c_uint32),
        ("phase_knot_count", ctypes.c_uint32),
        ("gain_event_count", ctypes.c_uint32),
        ("atom_count", ctypes.c_uint32),
        ("basis_count", ctypes.c_uint32),
        ("render_elements", ctypes.c_uint32),
        ("liftpack_scratch_elements", ctypes.c_size_t),
        ("output_channels", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
    ]


class _Workspace(ctypes.Structure):
    _fields_ = [
        ("basis", ctypes.POINTER(ctypes.c_int16)),
        ("basis_capacity", ctypes.c_size_t),
        ("phase_positions", ctypes.POINTER(ctypes.c_uint32)),
        ("phase_increments_q32", ctypes.POINTER(ctypes.c_uint32)),
        ("phase_origins_q32", ctypes.POINTER(ctypes.c_uint32)),
        ("phase_capacity", ctypes.c_size_t),
        ("gain_positions", ctypes.POINTER(ctypes.c_uint32)),
        ("gains_q15", ctypes.POINTER(ctypes.c_int32)),
        ("gain_capacity", ctypes.c_size_t),
        ("unity_prediction", ctypes.POINTER(ctypes.c_int16)),
        ("unity_capacity", ctypes.c_size_t),
        ("innovation_q", ctypes.POINTER(ctypes.c_int64)),
        ("innovation_capacity", ctypes.c_size_t),
        ("liftpack_scratch", ctypes.POINTER(ctypes.c_int64)),
        ("liftpack_scratch_capacity", ctypes.c_size_t),
    ]


class _PlayerView(ctypes.Structure):
    _fields_ = [
        ("innovation_data", ctypes.POINTER(ctypes.c_uint8)),
        ("innovation_size", ctypes.c_size_t),
        ("timebase_hz", ctypes.c_uint32),
        ("sample_count", ctypes.c_uint32),
        ("innovation_step", ctypes.c_uint32),
        ("block_size", ctypes.c_uint32),
        ("block_count", ctypes.c_uint32),
        ("atom_count", ctypes.c_uint32),
        ("liftpack_scratch_elements", ctypes.c_size_t),
        ("output_channels", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
        ("stream_data", ctypes.POINTER(ctypes.c_uint8)),
        ("stream_size", ctypes.c_size_t),
        ("basis_elements", ctypes.c_uint32),
        ("phase_knot_count", ctypes.c_uint32),
        ("gain_event_count", ctypes.c_uint32),
        ("basis_count", ctypes.c_uint32),
    ]


class _MultichannelRequirements(ctypes.Structure):
    _fields_ = [
        ("timebase_hz", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("block_count", ctypes.c_uint32),
        ("block_size", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("innovation_elements", ctypes.c_size_t),
        ("liftpack_scratch_elements", ctypes.c_size_t),
        ("output_elements", ctypes.c_size_t),
        ("output_block_elements", ctypes.c_size_t),
    ]


class _LappedRequirements(ctypes.Structure):
    _fields_ = [
        ("sample_rate", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("transform_frame_count", ctypes.c_uint32),
        ("half_window", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("coefficients_per_frame", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("scale_elements", ctypes.c_size_t),
        ("count_elements", ctypes.c_size_t),
        ("position_elements", ctypes.c_size_t),
        ("coefficient_elements", ctypes.c_size_t),
        ("overlap_elements", ctypes.c_size_t),
        ("output_elements", ctypes.c_size_t),
    ]


class _LappedWorkspace(ctypes.Structure):
    _fields_ = [
        ("scales", ctypes.POINTER(ctypes.c_uint8)),
        ("scale_capacity", ctypes.c_size_t),
        ("counts", ctypes.POINTER(ctypes.c_uint16)),
        ("count_capacity", ctypes.c_size_t),
        ("positions", ctypes.POINTER(ctypes.c_uint16)),
        ("position_capacity", ctypes.c_size_t),
        ("coefficients", ctypes.POINTER(ctypes.c_int8)),
        ("coefficient_capacity", ctypes.c_size_t),
        ("overlap_q29", ctypes.POINTER(ctypes.c_int64)),
        ("overlap_capacity", ctypes.c_size_t),
    ]


class _LappedAnalysisRequirements(ctypes.Structure):
    _fields_ = [
        ("transform_frame_count", ctypes.c_uint32),
        ("scale_elements", ctypes.c_size_t),
        ("coefficient_elements", ctypes.c_size_t),
        ("score_elements", ctypes.c_size_t),
    ]


class _LappedFiniteRequirements(ctypes.Structure):
    _fields_ = [
        ("transform_frame_count", ctypes.c_uint32),
        ("channels", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("half_window", ctypes.c_uint16),
        ("gap_threshold", ctypes.c_uint16),
        ("scale_elements", ctypes.c_size_t),
        ("count_elements", ctypes.c_size_t),
        ("position_elements", ctypes.c_size_t),
        ("coefficient_elements", ctypes.c_size_t),
    ]


class _LappedPacketRequirements(ctypes.Structure):
    _fields_ = [
        ("sample_rate", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("packet_frames", ctypes.c_uint32),
        ("packet_count", ctypes.c_uint32),
        ("half_window", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
        ("maximum_child", _LappedRequirements),
        ("maximum_child_output_elements", ctypes.c_size_t),
        ("maximum_logical_output_elements", ctypes.c_size_t),
    ]


class _LappedPacketSession(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("data_size", ctypes.c_size_t),
        ("next_offset", ctypes.c_size_t),
        ("next_packet", ctypes.c_uint32),
        ("next_frame", ctypes.c_uint32),
        ("sample_rate", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("packet_frames", ctypes.c_uint32),
        ("packet_count", ctypes.c_uint32),
        ("half_window", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("packet_mode", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
    ]


class _LappedCompactRequirements(ctypes.Structure):
    _fields_ = [
        ("sample_rate", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("packet_frames", ctypes.c_uint32),
        ("packet_count", ctypes.c_uint32),
        ("half_window", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
        ("maximum_current", _LappedRequirements),
        ("maximum_lookahead", _LappedRequirements),
        ("maximum_logical_output_elements", ctypes.c_size_t),
    ]


class _LappedCompactSession(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("data_size", ctypes.c_size_t),
        ("next_offset", ctypes.c_size_t),
        ("next_packet", ctypes.c_uint32),
        ("next_frame", ctypes.c_uint32),
        ("sample_rate", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("packet_frames", ctypes.c_uint32),
        ("packet_count", ctypes.c_uint32),
        ("half_window", ctypes.c_uint16),
        ("band_count", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
    ]


class _MultichannelPlayerView(ctypes.Structure):
    _fields_ = [
        (
            "innovation_data",
            ctypes.POINTER(ctypes.c_uint8) * 8,
        ),
        ("innovation_size", ctypes.c_size_t * 8),
        ("stream_data", ctypes.POINTER(ctypes.c_uint8)),
        ("stream_size", ctypes.c_size_t),
        ("timebase_hz", ctypes.c_uint32),
        ("frame_count", ctypes.c_uint32),
        ("block_count", ctypes.c_uint32),
        ("block_size", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("innovation_step", ctypes.c_uint32),
        ("liftpack_scratch_elements", ctypes.c_size_t),
    ]


class _LiftpackInfo(ctypes.Structure):
    _fields_ = [
        ("sample_count", ctypes.c_uint32),
        ("block_count", ctypes.c_uint32),
        ("block_size", ctypes.c_uint16),
        ("reserved", ctypes.c_uint16),
    ]


class _LiftpackCursor(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("data_size", ctypes.c_size_t),
        ("byte_offset", ctypes.c_size_t),
        ("sample_offset", ctypes.c_uint32),
        ("next_block", ctypes.c_uint32),
        ("info", _LiftpackInfo),
        ("lpc_stream", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 7),
    ]


class _MultichannelSession(ctypes.Structure):
    _fields_ = [
        ("cursors", _LiftpackCursor * 8),
        ("frame_count", ctypes.c_uint32),
        ("block_count", ctypes.c_uint32),
        ("next_block", ctypes.c_uint32),
        ("next_frame", ctypes.c_uint32),
        ("innovation_step", ctypes.c_uint32),
        ("state_tag", ctypes.c_uint32),
        ("block_size", ctypes.c_uint16),
        ("output_channels", ctypes.c_uint16),
        ("liftpack_scratch_elements", ctypes.c_size_t),
    ]


class _CibsRefinementStage(ctypes.Structure):
    _fields_ = [
        ("kernels", ctypes.POINTER(ctypes.c_int8)),
        ("kernel_width", ctypes.c_uint8),
        ("shift", ctypes.c_uint8),
        ("reserved", ctypes.c_uint16),
    ]


class _CibsModel(ctypes.Structure):
    _fields_ = [
        ("model_id", ctypes.POINTER(ctypes.c_uint8)),
        ("model_id_bytes", ctypes.c_size_t),
        ("projection", ctypes.POINTER(ctypes.c_int8)),
        ("projection_bias", ctypes.POINTER(ctypes.c_int32)),
        (
            "refinement_stages",
            ctypes.POINTER(_CibsRefinementStage),
        ),
        ("basis_channels", ctypes.c_uint32),
        ("coarse_length", ctypes.c_uint32),
        ("latent_elements", ctypes.c_uint32),
        ("projection_shift", ctypes.c_uint8),
        ("refinement_stage_count", ctypes.c_uint8),
        ("reserved", ctypes.c_uint16),
    ]


class _CibsRegistry(ctypes.Structure):
    _fields_ = [
        ("models", ctypes.POINTER(_CibsModel)),
        ("model_count", ctypes.c_size_t),
    ]


class _CibsRegistryOwner:
    """Keep every immutable model table alive across one native call."""

    def __init__(self, models: Sequence[CIBS0Model]) -> None:
        self._model_ids: list[ctypes.Array] = []
        self._projections: list[np.ndarray] = []
        self._biases: list[np.ndarray] = []
        self._kernels: list[list[np.ndarray]] = []
        self._stage_arrays: list[ctypes.Array | None] = []
        descriptors: list[_CibsModel] = []
        for model in models:
            model.validate()
            model_id = model.model_id.encode("utf-8")
            model_id_array = (ctypes.c_uint8 * len(model_id))(*model_id)
            projection = np.ascontiguousarray(
                model.projection,
                dtype=np.int8,
            )
            bias = np.ascontiguousarray(
                model.projection_bias,
                dtype=np.int32,
            )
            kernels: list[np.ndarray] = []
            stage_descriptors: list[_CibsRefinementStage] = []
            for kernel, shift in zip(
                model.refinement_kernels,
                model.refinement_shifts,
                strict=True,
            ):
                contiguous = np.ascontiguousarray(kernel, dtype=np.int8)
                kernels.append(contiguous)
                stage_descriptors.append(
                    _CibsRefinementStage(
                        contiguous.ctypes.data_as(
                            ctypes.POINTER(ctypes.c_int8)
                        ),
                        int(contiguous.shape[1]),
                        int(shift),
                        0,
                    )
                )
            stages = (
                (_CibsRefinementStage * len(stage_descriptors))(
                    *stage_descriptors
                )
                if stage_descriptors
                else None
            )
            descriptors.append(
                _CibsModel(
                    model_id_array,
                    len(model_id),
                    projection.ctypes.data_as(
                        ctypes.POINTER(ctypes.c_int8)
                    ),
                    bias.ctypes.data_as(
                        ctypes.POINTER(ctypes.c_int32)
                    ),
                    stages,
                    model.basis_channels,
                    model.coarse_length,
                    model.latent_elements,
                    model.projection_shift,
                    len(stage_descriptors),
                    0,
                )
            )
            self._model_ids.append(model_id_array)
            self._projections.append(projection)
            self._biases.append(bias)
            self._kernels.append(kernels)
            self._stage_arrays.append(stages)
        self._models = (_CibsModel * len(descriptors))(*descriptors)
        self.registry = _CibsRegistry(self._models, len(descriptors))


_Pcm16Callback = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_int16),
    ctypes.c_size_t,
)

_Pcm16InterleavedCallback = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_int16),
    ctypes.c_size_t,
    ctypes.c_uint16,
)


@dataclass(frozen=True)
class NativeMain0Requirements:
    timebase_hz: int
    sample_count: int
    basis_elements: int
    phase_knot_count: int
    gain_event_count: int
    atom_count: int
    basis_count: int
    render_elements: int
    liftpack_scratch_elements: int
    output_channels: int
    workspace_bytes: int


@dataclass(frozen=True)
class NativeMain0DecodeResult:
    samples: np.ndarray
    sample_rate: int
    requirements: NativeMain0Requirements


@dataclass(frozen=True)
class NativeMultichannelRequirements:
    timebase_hz: int
    frame_count: int
    block_count: int
    block_size: int
    output_channels: int
    innovation_elements: int
    liftpack_scratch_elements: int
    output_elements: int
    output_block_elements: int
    workspace_bytes: int


@dataclass(frozen=True)
class NativeMultichannelDecodeResult:
    samples: np.ndarray
    sample_rate: int
    requirements: NativeMultichannelRequirements


@dataclass(frozen=True)
class NativeLappedRequirements:
    sample_rate: int
    frame_count: int
    transform_frame_count: int
    half_window: int
    band_count: int
    coefficients_per_frame: int
    output_channels: int
    scale_elements: int
    count_elements: int
    position_elements: int
    coefficient_elements: int
    overlap_elements: int
    output_elements: int
    workspace_bytes: int


@dataclass(frozen=True)
class NativeLappedDecodeResult:
    samples: np.ndarray
    sample_rate: int
    requirements: NativeLappedRequirements


@dataclass(frozen=True)
class NativeLappedAnalysisResult:
    scales: np.ndarray
    quantized_grid: np.ndarray
    score_grid: np.ndarray
    transform_frame_count: int


@dataclass(frozen=True)
class NativeLappedFiniteResult:
    scales: np.ndarray
    counts: np.ndarray
    positions: np.ndarray
    values: np.ndarray
    gap_threshold: int
    workspace_bytes: int


@dataclass(frozen=True)
class NativeLappedPacketDecodeResult:
    samples: np.ndarray
    sample_rate: int
    packet_frames: int
    packet_count: int
    workspace_bytes: int


class NativeMain0Decoder:
    """Allocation-explicit host wrapper around `resonith_main0_decode`."""

    def __init__(
        self,
        library_path: str | os.PathLike[str] | None = None,
        *,
        max_workspace_bytes: int = DEFAULT_MAX_WORKSPACE_BYTES,
    ) -> None:
        configured = library_path or os.environ.get("RESONITH_NATIVE_CORE")
        if configured is None:
            raise ValueError(
                "provide library_path or set RESONITH_NATIVE_CORE explicitly"
            )
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if max_workspace_bytes <= 0:
            raise ValueError("max_workspace_bytes must be positive")
        self._max_workspace_bytes = int(max_workspace_bytes)
        self._library = ctypes.CDLL(str(path))
        self._configure_abi()

    def _configure_abi(self) -> None:
        byte_pointer = ctypes.POINTER(ctypes.c_uint8)
        self._library.resonith_main0_inspect.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_Requirements),
        ]
        self._library.resonith_main0_inspect.restype = ctypes.c_int
        self._library.resonith_main0_inspect_with_registry.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_CibsRegistry),
            ctypes.POINTER(_Requirements),
        ]
        self._library.resonith_main0_inspect_with_registry.restype = (
            ctypes.c_int
        )
        self._library.resonith_main0_decode.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_Workspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_decode.restype = ctypes.c_int
        self._library.resonith_main0_decode_with_registry.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_CibsRegistry),
            ctypes.POINTER(_Workspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_decode_with_registry.restype = ctypes.c_int
        self._library.resonith_main0_player_open.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_PlayerView),
        ]
        self._library.resonith_main0_player_open.restype = ctypes.c_int
        self._library.resonith_main0_player_open_with_registry.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_CibsRegistry),
            ctypes.POINTER(_PlayerView),
        ]
        self._library.resonith_main0_player_open_with_registry.restype = (
            ctypes.c_int
        )
        self._library.resonith_main0_player_stream.argtypes = [
            ctypes.POINTER(_PlayerView),
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            _Pcm16Callback,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_player_stream.restype = ctypes.c_int
        self._library.resonith_main0_player_stream_complete.argtypes = [
            ctypes.POINTER(_PlayerView),
            ctypes.POINTER(_Workspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            _Pcm16Callback,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_player_stream_complete.restype = (
            ctypes.c_int
        )
        self._library.resonith_main0_player_stream_complete_with_registry.argtypes = [
            ctypes.POINTER(_PlayerView),
            ctypes.POINTER(_CibsRegistry),
            ctypes.POINTER(_Workspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            _Pcm16Callback,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_player_stream_complete_with_registry.restype = (
            ctypes.c_int
        )
        self._library.resonith_multichannel_inspect.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_MultichannelRequirements),
        ]
        self._library.resonith_multichannel_inspect.restype = ctypes.c_int
        self._library.resonith_multichannel_decode.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_multichannel_decode.restype = ctypes.c_int
        self._library.resonith_multichannel_player_open.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_MultichannelPlayerView),
        ]
        self._library.resonith_multichannel_player_open.restype = ctypes.c_int
        self._library.resonith_multichannel_session_open.argtypes = [
            ctypes.POINTER(_MultichannelPlayerView),
            ctypes.POINTER(_MultichannelSession),
        ]
        self._library.resonith_multichannel_session_open.restype = ctypes.c_int
        self._library.resonith_multichannel_session_decode_next.argtypes = [
            ctypes.POINTER(_MultichannelSession),
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_multichannel_session_decode_next.restype = (
            ctypes.c_int
        )
        self._library.resonith_multichannel_player_stream.argtypes = [
            ctypes.POINTER(_MultichannelPlayerView),
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int64),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            _Pcm16InterleavedCallback,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_multichannel_player_stream.restype = (
            ctypes.c_int
        )
        self._library.resonith_lapped_inspect.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_LappedRequirements),
        ]
        self._library.resonith_lapped_inspect.restype = ctypes.c_int
        self._library.resonith_lapped_decode.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_LappedWorkspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_lapped_decode.restype = ctypes.c_int
        self._library.resonith_lapped_analyze_requirements.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.POINTER(_LappedAnalysisRequirements),
        ]
        self._library.resonith_lapped_analyze_requirements.restype = (
            ctypes.c_int
        )
        self._library.resonith_lapped_analyze_pcm16.argtypes = [
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_size_t,
        ]
        self._library.resonith_lapped_analyze_pcm16.restype = ctypes.c_int
        self._library.resonith_lapped_finite_inspect.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.c_uint16,
            ctypes.POINTER(_LappedFiniteRequirements),
        ]
        self._library.resonith_lapped_finite_inspect.restype = ctypes.c_int
        self._library.resonith_lapped_finite_decode.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.c_uint16,
            ctypes.POINTER(_LappedWorkspace),
        ]
        self._library.resonith_lapped_finite_decode.restype = ctypes.c_int
        self._library.resonith_lapped_packet_open.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_LappedPacketSession),
            ctypes.POINTER(_LappedPacketRequirements),
        ]
        self._library.resonith_lapped_packet_open.restype = ctypes.c_int
        self._library.resonith_lapped_packet_decode_next.argtypes = [
            ctypes.POINTER(_LappedPacketSession),
            ctypes.POINTER(_LappedWorkspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_lapped_packet_decode_next.restype = ctypes.c_int
        self._library.resonith_lapped_compact_open.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_LappedCompactSession),
            ctypes.POINTER(_LappedCompactRequirements),
        ]
        self._library.resonith_lapped_compact_open.restype = ctypes.c_int
        self._library.resonith_lapped_compact_decode_next.argtypes = [
            ctypes.POINTER(_LappedCompactSession),
            ctypes.POINTER(_LappedWorkspace),
            ctypes.POINTER(_LappedWorkspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_lapped_compact_decode_next.restype = ctypes.c_int
        self._library.resonith_status_string.argtypes = [ctypes.c_int]
        self._library.resonith_status_string.restype = ctypes.c_char_p

    def _check(self, status: int) -> None:
        if status == 0:
            return
        raw = self._library.resonith_status_string(status)
        message = "unknown status" if raw is None else raw.decode("ascii")
        raise NativeCoreError(status, message)

    @staticmethod
    def _input_buffer(payload: bytes) -> ctypes.Array:
        if not payload:
            raise ValueError("native Main-0 input must not be empty")
        return (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)

    @staticmethod
    def _workspace_bytes(requirements: _Requirements) -> int:
        return (
            int(requirements.basis_elements) * 2
            + int(requirements.phase_knot_count) * 12
            + int(requirements.gain_event_count) * 8
            + int(requirements.render_elements) * 2
            + int(requirements.sample_count) * 10
            + int(requirements.liftpack_scratch_elements) * 8
        )

    def _inspect_native(
        self,
        payload: bytes,
        registry: _CibsRegistryOwner | None,
    ) -> NativeMain0Requirements:
        source = self._input_buffer(payload)
        native = _Requirements()
        if registry is None:
            status = self._library.resonith_main0_inspect(
                source,
                len(payload),
                ctypes.byref(native),
            )
        else:
            status = self._library.resonith_main0_inspect_with_registry(
                source,
                len(payload),
                ctypes.byref(registry.registry),
                ctypes.byref(native),
            )
        self._check(status)
        workspace_bytes = self._workspace_bytes(native)
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native Main-0 workspace exceeds the configured host ceiling"
            )
        return NativeMain0Requirements(
            int(native.timebase_hz),
            int(native.sample_count),
            int(native.basis_elements),
            int(native.phase_knot_count),
            int(native.gain_event_count),
            int(native.atom_count),
            int(native.basis_count),
            int(native.render_elements),
            int(native.liftpack_scratch_elements),
            int(native.output_channels),
            workspace_bytes,
        )

    def inspect(
        self,
        payload: bytes,
        *,
        cibs_models: Sequence[CIBS0Model] = (),
    ) -> NativeMain0Requirements:
        registry = _CibsRegistryOwner(cibs_models) if cibs_models else None
        return self._inspect_native(payload, registry)

    def inspect_multichannel(
        self,
        payload: bytes,
    ) -> NativeMultichannelRequirements:
        """Inspect the independent-channel Main-0 subset."""

        source = self._input_buffer(payload)
        native = _MultichannelRequirements()
        status = self._library.resonith_multichannel_inspect(
            source,
            len(payload),
            ctypes.byref(native),
        )
        self._check(status)
        workspace_bytes = (
            int(native.innovation_elements) * 8
            + int(native.liftpack_scratch_elements) * 8
            + int(native.output_block_elements) * 2
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native multichannel workspace exceeds the host ceiling"
            )
        return NativeMultichannelRequirements(
            int(native.timebase_hz),
            int(native.frame_count),
            int(native.block_count),
            int(native.block_size),
            int(native.output_channels),
            int(native.innovation_elements),
            int(native.liftpack_scratch_elements),
            int(native.output_elements),
            int(native.output_block_elements),
            workspace_bytes,
        )

    def inspect_lapped(self, payload: bytes) -> NativeLappedRequirements:
        """Inspect the prospective fixed/bounded LPF1 research subset."""

        source = self._input_buffer(payload)
        native = _LappedRequirements()
        self._check(
            self._library.resonith_lapped_inspect(
                source,
                len(payload),
                ctypes.byref(native),
            )
        )
        workspace_bytes = (
            int(native.scale_elements)
            + 2 * int(native.count_elements)
            + 2 * int(native.position_elements)
            + int(native.coefficient_elements)
            + 8 * int(native.overlap_elements)
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native lapped workspace exceeds the configured host ceiling"
            )
        return NativeLappedRequirements(
            int(native.sample_rate),
            int(native.frame_count),
            int(native.transform_frame_count),
            int(native.half_window),
            int(native.band_count),
            int(native.coefficients_per_frame),
            int(native.output_channels),
            int(native.scale_elements),
            int(native.count_elements),
            int(native.position_elements),
            int(native.coefficient_elements),
            int(native.overlap_elements),
            int(native.output_elements),
            workspace_bytes,
        )

    def decode_lapped(self, payload: bytes) -> NativeLappedDecodeResult:
        """Decode fixed/bounded LPF1 through the independent native Core."""

        requirements = self.inspect_lapped(payload)
        source = self._input_buffer(payload)
        scales = (ctypes.c_uint8 * requirements.scale_elements)()
        counts = (ctypes.c_uint16 * max(1, requirements.count_elements))()
        positions = (ctypes.c_uint16 * requirements.position_elements)()
        coefficients = (
            ctypes.c_int8 * requirements.coefficient_elements
        )()
        overlap = (ctypes.c_int64 * requirements.overlap_elements)()
        workspace = _LappedWorkspace(
            scales,
            requirements.scale_elements,
            counts,
            requirements.count_elements,
            positions,
            requirements.position_elements,
            coefficients,
            requirements.coefficient_elements,
            overlap,
            requirements.overlap_elements,
        )
        output = (ctypes.c_int16 * requirements.output_elements)()
        frames_written = ctypes.c_size_t()
        self._check(
            self._library.resonith_lapped_decode(
                source,
                len(payload),
                ctypes.byref(workspace),
                output,
                requirements.output_elements,
                ctypes.byref(frames_written),
            )
        )
        if frames_written.value != requirements.frame_count:
            raise RuntimeError("native lapped decoder returned partial PCM")
        samples = np.ctypeslib.as_array(output).reshape(
            requirements.frame_count,
            requirements.output_channels,
        ).copy()
        samples.flags.writeable = False
        return NativeLappedDecodeResult(
            samples,
            requirements.sample_rate,
            requirements,
        )

    def decode_lapped_finite(
        self,
        payload: bytes,
        *,
        half_window: int,
    ) -> NativeLappedFiniteResult:
        """Decode LAF1 fields through the allocation-explicit native oracle."""

        if not 2 <= half_window <= 1024:
            raise ValueError("native LAF1 half-window exceeds the profile")
        source = self._input_buffer(payload)
        requirements = _LappedFiniteRequirements()
        self._check(
            self._library.resonith_lapped_finite_inspect(
                source,
                len(payload),
                half_window,
                ctypes.byref(requirements),
            )
        )
        workspace_bytes = (
            int(requirements.scale_elements)
            + 2 * int(requirements.count_elements)
            + 2 * int(requirements.position_elements)
            + int(requirements.coefficient_elements)
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native LAF1 workspace exceeds the configured host ceiling"
            )
        scales = (
            ctypes.c_uint8 * max(1, int(requirements.scale_elements))
        )()
        counts = (
            ctypes.c_uint16 * max(1, int(requirements.count_elements))
        )()
        positions = (
            ctypes.c_uint16 * max(1, int(requirements.position_elements))
        )()
        values = (
            ctypes.c_int8 * max(1, int(requirements.coefficient_elements))
        )()
        workspace = _LappedWorkspace(
            scales,
            int(requirements.scale_elements),
            counts,
            int(requirements.count_elements),
            positions,
            int(requirements.position_elements),
            values,
            int(requirements.coefficient_elements),
            None,
            0,
        )
        self._check(
            self._library.resonith_lapped_finite_decode(
                source,
                len(payload),
                half_window,
                ctypes.byref(workspace),
            )
        )
        scale_grid = np.ctypeslib.as_array(scales)[
            : int(requirements.scale_elements)
        ].copy().reshape(
            int(requirements.channels),
            int(requirements.transform_frame_count),
            int(requirements.band_count),
        )
        count_grid = np.ctypeslib.as_array(counts)[
            : int(requirements.count_elements)
        ].copy().reshape(
            int(requirements.channels),
            int(requirements.transform_frame_count),
        )
        position_array = np.ctypeslib.as_array(positions)[
            : int(requirements.position_elements)
        ].copy()
        value_array = np.ctypeslib.as_array(values)[
            : int(requirements.coefficient_elements)
        ].copy()
        for array in (scale_grid, count_grid, position_array, value_array):
            array.flags.writeable = False
        return NativeLappedFiniteResult(
            scale_grid,
            count_grid,
            position_array,
            value_array,
            int(requirements.gap_threshold),
            workspace_bytes,
        )

    def analyze_lapped(
        self,
        samples: np.ndarray,
        *,
        half_window: int = 512,
        band_count: int = 24,
    ) -> NativeLappedAnalysisResult:
        """Run the allocation-explicit native fixed lapped analysis."""

        source_view = np.asarray(samples)
        if (
            source_view.dtype != np.int16
            or source_view.ndim != 2
            or source_view.shape[0] == 0
            or not 1 <= source_view.shape[1] <= 8
        ):
            raise TypeError(
                "native lapped analysis requires frame-major PCM16"
            )
        source = np.ascontiguousarray(source_view)
        native = _LappedAnalysisRequirements()
        self._check(
            self._library.resonith_lapped_analyze_requirements(
                source.shape[0],
                source.shape[1],
                half_window,
                band_count,
                ctypes.byref(native),
            )
        )
        workspace_bytes = (
            int(native.scale_elements)
            + 2 * int(native.coefficient_elements)
            + 8 * int(native.score_elements)
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native lapped analysis exceeds the configured host ceiling"
            )
        scales = np.empty(int(native.scale_elements), dtype=np.uint8)
        quantized = np.empty(
            int(native.coefficient_elements),
            dtype=np.int16,
        )
        scores = np.empty(int(native.score_elements), dtype=np.uint64)
        self._check(
            self._library.resonith_lapped_analyze_pcm16(
                source.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                source.size,
                source.shape[0],
                source.shape[1],
                half_window,
                band_count,
                scales.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                scales.size,
                quantized.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                quantized.size,
                scores.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
                scores.size,
            )
        )
        transform_frames = int(native.transform_frame_count)
        shape = (source.shape[1], transform_frames)
        scales = scales.reshape(*shape, band_count)
        quantized = quantized.reshape(*shape, half_window)
        scores = scores.reshape(*shape, half_window)
        scales.flags.writeable = False
        quantized.flags.writeable = False
        scores.flags.writeable = False
        return NativeLappedAnalysisResult(
            scales,
            quantized,
            scores,
            transform_frames,
        )

    def decode_lapped_packets(
        self,
        payload: bytes,
    ) -> NativeLappedPacketDecodeResult:
        """Decode an LPS1 sequence through the bounded native pull session."""

        source = self._input_buffer(payload)
        session = _LappedPacketSession()
        requirements = _LappedPacketRequirements()
        self._check(
            self._library.resonith_lapped_packet_open(
                source,
                len(payload),
                ctypes.byref(session),
                ctypes.byref(requirements),
            )
        )
        child = requirements.maximum_child
        workspace_bytes = (
            int(child.scale_elements)
            + 2 * int(child.count_elements)
            + 2 * int(child.position_elements)
            + int(child.coefficient_elements)
            + 8 * int(child.overlap_elements)
            + 2 * int(requirements.maximum_child_output_elements)
            + 2 * int(requirements.maximum_logical_output_elements)
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native LPS1 workspace exceeds the configured host ceiling"
            )
        scales = (ctypes.c_uint8 * int(child.scale_elements))()
        counts = (ctypes.c_uint16 * max(1, int(child.count_elements)))()
        positions = (
            ctypes.c_uint16 * int(child.position_elements)
        )()
        coefficients = (
            ctypes.c_int8 * int(child.coefficient_elements)
        )()
        overlap = (ctypes.c_int64 * int(child.overlap_elements))()
        workspace = _LappedWorkspace(
            scales,
            int(child.scale_elements),
            counts,
            int(child.count_elements),
            positions,
            int(child.position_elements),
            coefficients,
            int(child.coefficient_elements),
            overlap,
            int(child.overlap_elements),
        )
        child_output = (
            ctypes.c_int16
            * int(requirements.maximum_child_output_elements)
        )()
        logical_output = (
            ctypes.c_int16
            * int(requirements.maximum_logical_output_elements)
        )()
        output = np.empty(
            (
                int(requirements.frame_count),
                int(requirements.output_channels),
            ),
            dtype=np.int16,
        )
        for expected_packet in range(int(requirements.packet_count)):
            logical_start = ctypes.c_uint32()
            frames_written = ctypes.c_size_t()
            self._check(
                self._library.resonith_lapped_packet_decode_next(
                    ctypes.byref(session),
                    ctypes.byref(workspace),
                    child_output,
                    int(requirements.maximum_child_output_elements),
                    logical_output,
                    int(requirements.maximum_logical_output_elements),
                    ctypes.byref(logical_start),
                    ctypes.byref(frames_written),
                )
            )
            if session.next_packet != expected_packet + 1:
                raise RuntimeError("native LPS1 session did not advance once")
            element_count = (
                int(frames_written.value)
                * int(requirements.output_channels)
            )
            block = np.ctypeslib.as_array(logical_output)[:element_count]
            output[
                int(logical_start.value) : (
                    int(logical_start.value) + int(frames_written.value)
                )
            ] = block.reshape(
                int(frames_written.value),
                int(requirements.output_channels),
            )
        if session.next_frame != requirements.frame_count:
            raise RuntimeError("native LPS1 session returned partial PCM")
        output.flags.writeable = False
        return NativeLappedPacketDecodeResult(
            output,
            int(requirements.sample_rate),
            int(requirements.packet_frames),
            int(requirements.packet_count),
            workspace_bytes,
        )

    def decode_lapped_compact_packets(
        self,
        payload: bytes,
    ) -> NativeLappedPacketDecodeResult:
        """Decode LPS4/LPS5 through the bounded two-workspace session."""

        source = self._input_buffer(payload)
        session = _LappedCompactSession()
        requirements = _LappedCompactRequirements()
        self._check(
            self._library.resonith_lapped_compact_open(
                source,
                len(payload),
                ctypes.byref(session),
                ctypes.byref(requirements),
            )
        )
        current = requirements.maximum_current
        lookahead = requirements.maximum_lookahead
        workspace_bytes = (
            int(current.scale_elements)
            + 2 * int(current.count_elements)
            + 2 * int(current.position_elements)
            + int(current.coefficient_elements)
            + 8 * int(current.overlap_elements)
            + int(lookahead.scale_elements)
            + 2 * int(lookahead.count_elements)
            + 2 * int(lookahead.position_elements)
            + int(lookahead.coefficient_elements)
            + 2 * int(requirements.maximum_logical_output_elements)
        )
        if workspace_bytes > self._max_workspace_bytes:
            raise MemoryError(
                "native LPS4 workspace exceeds the configured host ceiling"
            )

        current_scales = (
            ctypes.c_uint8 * max(1, int(current.scale_elements))
        )()
        current_counts = (
            ctypes.c_uint16 * max(1, int(current.count_elements))
        )()
        current_positions = (
            ctypes.c_uint16 * max(1, int(current.position_elements))
        )()
        current_coefficients = (
            ctypes.c_int8 * max(1, int(current.coefficient_elements))
        )()
        current_overlap = (
            ctypes.c_int64 * max(1, int(current.overlap_elements))
        )()
        current_workspace = _LappedWorkspace(
            current_scales,
            int(current.scale_elements),
            current_counts,
            int(current.count_elements),
            current_positions,
            int(current.position_elements),
            current_coefficients,
            int(current.coefficient_elements),
            current_overlap,
            int(current.overlap_elements),
        )

        lookahead_scales = (
            ctypes.c_uint8 * max(1, int(lookahead.scale_elements))
        )()
        lookahead_counts = (
            ctypes.c_uint16 * max(1, int(lookahead.count_elements))
        )()
        lookahead_positions = (
            ctypes.c_uint16 * max(1, int(lookahead.position_elements))
        )()
        lookahead_coefficients = (
            ctypes.c_int8 * max(1, int(lookahead.coefficient_elements))
        )()
        lookahead_workspace = _LappedWorkspace(
            lookahead_scales,
            int(lookahead.scale_elements),
            lookahead_counts,
            int(lookahead.count_elements),
            lookahead_positions,
            int(lookahead.position_elements),
            lookahead_coefficients,
            int(lookahead.coefficient_elements),
            None,
            0,
        )
        logical_output = (
            ctypes.c_int16
            * int(requirements.maximum_logical_output_elements)
        )()
        output = np.empty(
            (
                int(requirements.frame_count),
                int(requirements.output_channels),
            ),
            dtype=np.int16,
        )
        for expected_packet in range(int(requirements.packet_count)):
            logical_start = ctypes.c_uint32()
            frames_written = ctypes.c_size_t()
            self._check(
                self._library.resonith_lapped_compact_decode_next(
                    ctypes.byref(session),
                    ctypes.byref(current_workspace),
                    ctypes.byref(lookahead_workspace),
                    logical_output,
                    int(requirements.maximum_logical_output_elements),
                    ctypes.byref(logical_start),
                    ctypes.byref(frames_written),
                )
            )
            if session.next_packet != expected_packet + 1:
                raise RuntimeError("native LPS4 session did not advance once")
            element_count = (
                int(frames_written.value)
                * int(requirements.output_channels)
            )
            block = np.ctypeslib.as_array(logical_output)[:element_count]
            start = int(logical_start.value)
            end = start + int(frames_written.value)
            output[start:end] = block.reshape(
                int(frames_written.value),
                int(requirements.output_channels),
            )
        if session.next_frame != requirements.frame_count:
            raise RuntimeError("native LPS4 session returned partial PCM")
        output.flags.writeable = False
        return NativeLappedPacketDecodeResult(
            output,
            int(requirements.sample_rate),
            int(requirements.packet_frames),
            int(requirements.packet_count),
            workspace_bytes,
        )

    def decode_multichannel(
        self,
        payload: bytes,
    ) -> NativeMultichannelDecodeResult:
        """Decode independent channels to a frames-by-channels PCM matrix."""

        requirements = self.inspect_multichannel(payload)
        source = self._input_buffer(payload)
        innovation = (
            ctypes.c_int64 * requirements.innovation_elements
        )()
        scratch = (
            ctypes.c_int64 * requirements.liftpack_scratch_elements
        )()
        output = (ctypes.c_int16 * requirements.output_elements)()
        written = ctypes.c_size_t()
        status = self._library.resonith_multichannel_decode(
            source,
            len(payload),
            innovation,
            requirements.innovation_elements,
            scratch,
            requirements.liftpack_scratch_elements,
            output,
            requirements.output_elements,
            ctypes.byref(written),
        )
        self._check(status)
        if written.value != requirements.frame_count:
            raise RuntimeError(
                "native multichannel decoder returned partial PCM"
            )
        samples = np.ctypeslib.as_array(output).reshape(
            requirements.frame_count,
            requirements.output_channels,
        ).copy()
        samples.flags.writeable = False
        return NativeMultichannelDecodeResult(
            samples,
            requirements.timebase_hz,
            requirements,
        )

    def decode_multichannel_streaming(
        self,
        payload: bytes,
    ) -> NativeMultichannelDecodeResult:
        """Decode aligned channel blocks through the interleaved callback."""

        requirements = self.inspect_multichannel(payload)
        source = self._input_buffer(payload)
        player = _MultichannelPlayerView()
        self._check(
            self._library.resonith_multichannel_player_open(
                source,
                len(payload),
                ctypes.byref(player),
            )
        )
        if (
            int(player.frame_count) != requirements.frame_count
            or int(player.output_channels) != requirements.output_channels
        ):
            raise RuntimeError(
                "native multichannel player differs from inspect"
            )

        innovation = (ctypes.c_int64 * requirements.block_size)()
        scratch = (
            ctypes.c_int64 * requirements.liftpack_scratch_elements
        )()
        block_output = (
            ctypes.c_int16 * requirements.output_block_elements
        )()
        result = np.empty(
            (
                requirements.frame_count,
                requirements.output_channels,
            ),
            dtype=np.int16,
        )
        callback_error: list[BaseException] = []

        def collect(
            _user: int,
            frame_offset: int,
            samples: ctypes.POINTER(ctypes.c_int16),
            frame_count: int,
            channels: int,
        ) -> int:
            try:
                start = int(frame_offset)
                count = int(frame_count)
                channel_count = int(channels)
                end = start + count
                if (
                    start < 0
                    or end > result.shape[0]
                    or channel_count != result.shape[1]
                ):
                    raise RuntimeError(
                        "native interleaved callback exceeds PCM extent"
                    )
                block = np.ctypeslib.as_array(
                    samples,
                    shape=(count * channel_count,),
                ).reshape(count, channel_count)
                result[start:end] = block
                return 0
            except BaseException as error:
                callback_error.append(error)
                return 7

        callback = _Pcm16InterleavedCallback(collect)
        emitted = ctypes.c_size_t()
        status = self._library.resonith_multichannel_player_stream(
            ctypes.byref(player),
            innovation,
            requirements.block_size,
            scratch,
            requirements.liftpack_scratch_elements,
            block_output,
            requirements.output_block_elements,
            callback,
            None,
            ctypes.byref(emitted),
        )
        if callback_error:
            raise RuntimeError(
                "native interleaved PCM callback rejected a block"
            ) from callback_error[0]
        self._check(status)
        if emitted.value != requirements.frame_count:
            raise RuntimeError(
                "native multichannel player returned partial PCM"
            )
        result.flags.writeable = False
        return NativeMultichannelDecodeResult(
            result,
            requirements.timebase_hz,
            requirements,
        )

    def decode_multichannel_pull(
        self,
        payload: bytes,
    ) -> NativeMultichannelDecodeResult:
        """Decode one device-sized block at a time through mutable pull state."""

        requirements = self.inspect_multichannel(payload)
        source = self._input_buffer(payload)
        player = _MultichannelPlayerView()
        self._check(
            self._library.resonith_multichannel_player_open(
                source,
                len(payload),
                ctypes.byref(player),
            )
        )
        session = _MultichannelSession()
        self._check(
            self._library.resonith_multichannel_session_open(
                ctypes.byref(player),
                ctypes.byref(session),
            )
        )
        innovation = (ctypes.c_int64 * requirements.block_size)()
        scratch = (
            ctypes.c_int64 * requirements.liftpack_scratch_elements
        )()
        block_output = (
            ctypes.c_int16 * requirements.output_block_elements
        )()
        rejected_offset = ctypes.c_uint32(99)
        rejected_frames = ctypes.c_size_t(99)
        rejected = (
            self._library.resonith_multichannel_session_decode_next(
                ctypes.byref(session),
                innovation,
                requirements.block_size,
                scratch,
                requirements.liftpack_scratch_elements,
                block_output,
                requirements.output_block_elements - 1,
                ctypes.byref(rejected_offset),
                ctypes.byref(rejected_frames),
            )
        )
        if (
            rejected != 8
            or rejected_offset.value != 0
            or rejected_frames.value != 0
            or session.next_block != 0
        ):
            raise RuntimeError(
                "native pull session advanced after rejected output capacity"
            )
        result = np.empty(
            (
                requirements.frame_count,
                requirements.output_channels,
            ),
            dtype=np.int16,
        )
        for expected_block in range(requirements.block_count):
            frame_offset = ctypes.c_uint32()
            frames_written = ctypes.c_size_t()
            status = (
                self._library
                .resonith_multichannel_session_decode_next(
                    ctypes.byref(session),
                    innovation,
                    requirements.block_size,
                    scratch,
                    requirements.liftpack_scratch_elements,
                    block_output,
                    requirements.output_block_elements,
                    ctypes.byref(frame_offset),
                    ctypes.byref(frames_written),
                )
            )
            self._check(status)
            start = int(frame_offset.value)
            count = int(frames_written.value)
            end = start + count
            if (
                int(session.next_block) != expected_block + 1
                or count == 0
                or end > requirements.frame_count
            ):
                raise RuntimeError(
                    "native pull session returned a non-canonical block"
                )
            block = np.ctypeslib.as_array(
                block_output,
                shape=(requirements.output_block_elements,),
            )[: count * requirements.output_channels].reshape(
                count,
                requirements.output_channels,
            )
            result[start:end] = block

        final_offset = ctypes.c_uint32(99)
        final_frames = ctypes.c_size_t(99)
        status = (
            self._library.resonith_multichannel_session_decode_next(
                ctypes.byref(session),
                innovation,
                requirements.block_size,
                scratch,
                requirements.liftpack_scratch_elements,
                block_output,
                requirements.output_block_elements,
                ctypes.byref(final_offset),
                ctypes.byref(final_frames),
            )
        )
        if status != 11 or final_offset.value != 0 or final_frames.value != 0:
            raise RuntimeError(
                "native pull session did not report canonical end-of-stream"
            )
        result.flags.writeable = False
        return NativeMultichannelDecodeResult(
            result,
            requirements.timebase_hz,
            requirements,
        )

    def decode(
        self,
        payload: bytes,
        *,
        cibs_models: Sequence[CIBS0Model] = (),
    ) -> NativeMain0DecodeResult:
        registry = _CibsRegistryOwner(cibs_models) if cibs_models else None
        requirements = self._inspect_native(payload, registry)
        source = self._input_buffer(payload)

        basis = (ctypes.c_int16 * requirements.basis_elements)()
        phase_positions = (
            ctypes.c_uint32 * requirements.phase_knot_count
        )()
        phase_increments = (
            ctypes.c_uint32 * requirements.phase_knot_count
        )()
        phase_origins = (ctypes.c_uint32 * requirements.phase_knot_count)()
        gain_positions = (ctypes.c_uint32 * requirements.gain_event_count)()
        gains = (ctypes.c_int32 * requirements.gain_event_count)()
        unity = (ctypes.c_int16 * requirements.render_elements)()
        innovation = (ctypes.c_int64 * requirements.sample_count)()
        scratch = (
            ctypes.c_int64 * requirements.liftpack_scratch_elements
        )()
        output = (ctypes.c_int16 * requirements.sample_count)()
        workspace = _Workspace(
            basis,
            requirements.basis_elements,
            phase_positions,
            phase_increments,
            phase_origins,
            requirements.phase_knot_count,
            gain_positions,
            gains,
            requirements.gain_event_count,
            unity,
            requirements.render_elements,
            innovation,
            requirements.sample_count,
            scratch,
            requirements.liftpack_scratch_elements,
        )
        written = ctypes.c_size_t()
        if registry is None:
            status = self._library.resonith_main0_decode(
                source,
                len(payload),
                ctypes.byref(workspace),
                output,
                requirements.sample_count,
                ctypes.byref(written),
            )
        else:
            status = self._library.resonith_main0_decode_with_registry(
                source,
                len(payload),
                ctypes.byref(registry.registry),
                ctypes.byref(workspace),
                output,
                requirements.sample_count,
                ctypes.byref(written),
            )
        self._check(status)
        if written.value != requirements.sample_count:
            raise RuntimeError("native decoder returned a partial PCM result")
        samples = np.ctypeslib.as_array(output).copy()
        samples.flags.writeable = False
        return NativeMain0DecodeResult(
            samples,
            requirements.timebase_hz,
            requirements,
        )

    def decode_streaming(
        self,
        payload: bytes,
        *,
        cibs_models: Sequence[CIBS0Model] = (),
    ) -> NativeMain0DecodeResult:
        """Decode complete Main-0 through the one-block callback API."""

        registry = _CibsRegistryOwner(cibs_models) if cibs_models else None
        requirements = self._inspect_native(payload, registry)
        source = self._input_buffer(payload)
        player = _PlayerView()
        if registry is None:
            open_status = self._library.resonith_main0_player_open(
                source,
                len(payload),
                ctypes.byref(player),
            )
        else:
            open_status = (
                self._library.resonith_main0_player_open_with_registry(
                    source,
                    len(payload),
                    ctypes.byref(registry.registry),
                    ctypes.byref(player),
                )
            )
        self._check(open_status)
        if int(player.sample_count) != requirements.sample_count:
            raise RuntimeError("native player metadata differs from inspect")

        basis = (ctypes.c_int16 * requirements.basis_elements)()
        phase_positions = (
            ctypes.c_uint32 * requirements.phase_knot_count
        )()
        phase_increments = (
            ctypes.c_uint32 * requirements.phase_knot_count
        )()
        phase_origins = (
            ctypes.c_uint32 * requirements.phase_knot_count
        )()
        gain_positions = (
            ctypes.c_uint32 * requirements.gain_event_count
        )()
        gains = (ctypes.c_int32 * requirements.gain_event_count)()
        render_elements = min(
            int(player.block_size),
            requirements.render_elements,
        )
        unity = (ctypes.c_int16 * render_elements)()
        innovation = (ctypes.c_int64 * int(player.block_size))()
        scratch = (
            ctypes.c_int64 * int(player.liftpack_scratch_elements)
        )()
        block_output = (ctypes.c_int16 * int(player.block_size))()
        workspace = _Workspace(
            basis,
            requirements.basis_elements,
            phase_positions,
            phase_increments,
            phase_origins,
            requirements.phase_knot_count,
            gain_positions,
            gains,
            requirements.gain_event_count,
            unity,
            render_elements,
            innovation,
            int(player.block_size),
            scratch,
            int(player.liftpack_scratch_elements),
        )
        result = np.empty(requirements.sample_count, dtype=np.int16)
        callback_error: list[BaseException] = []

        def collect(
            _user: int,
            sample_offset: int,
            samples: ctypes.POINTER(ctypes.c_int16),
            sample_count: int,
        ) -> int:
            try:
                start = int(sample_offset)
                count = int(sample_count)
                end = start + count
                if start < 0 or end > result.size:
                    raise RuntimeError("native callback exceeds PCM extent")
                result[start:end] = np.ctypeslib.as_array(
                    samples,
                    shape=(count,),
                )
                return 0
            except BaseException as error:
                callback_error.append(error)
                return 7

        callback = _Pcm16Callback(collect)
        emitted = ctypes.c_size_t()
        if registry is None:
            status = self._library.resonith_main0_player_stream_complete(
                ctypes.byref(player),
                ctypes.byref(workspace),
                block_output,
                int(player.block_size),
                callback,
                None,
                ctypes.byref(emitted),
            )
        else:
            status = (
                self._library
                .resonith_main0_player_stream_complete_with_registry(
                    ctypes.byref(player),
                    ctypes.byref(registry.registry),
                    ctypes.byref(workspace),
                    block_output,
                    int(player.block_size),
                    callback,
                    None,
                    ctypes.byref(emitted),
                )
            )
        if callback_error:
            raise RuntimeError("native PCM callback rejected a block") from (
                callback_error[0]
            )
        self._check(status)
        if emitted.value != requirements.sample_count:
            raise RuntimeError("native player returned a partial PCM result")
        result.flags.writeable = False
        return NativeMain0DecodeResult(
            result,
            requirements.timebase_hz,
            requirements,
        )
