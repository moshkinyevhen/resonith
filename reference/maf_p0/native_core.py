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
