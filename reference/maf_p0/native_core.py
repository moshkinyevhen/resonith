"""Explicit ctypes binding for the Resonith Golden Core C ABI."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
from pathlib import Path

import numpy as np


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


@dataclass(frozen=True)
class NativeMain0Requirements:
    timebase_hz: int
    sample_count: int
    basis_elements: int
    phase_knot_count: int
    gain_event_count: int
    liftpack_scratch_elements: int
    output_channels: int
    workspace_bytes: int


@dataclass(frozen=True)
class NativeMain0DecodeResult:
    samples: np.ndarray
    sample_rate: int
    requirements: NativeMain0Requirements


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
        self._library.resonith_main0_decode.argtypes = [
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_Workspace),
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._library.resonith_main0_decode.restype = ctypes.c_int
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
            + int(requirements.sample_count) * 12
            + int(requirements.liftpack_scratch_elements) * 8
        )

    def inspect(self, payload: bytes) -> NativeMain0Requirements:
        source = self._input_buffer(payload)
        native = _Requirements()
        self._check(
            self._library.resonith_main0_inspect(
                source,
                len(payload),
                ctypes.byref(native),
            )
        )
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
            int(native.liftpack_scratch_elements),
            int(native.output_channels),
            workspace_bytes,
        )

    def decode(self, payload: bytes) -> NativeMain0DecodeResult:
        requirements = self.inspect(payload)
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
        unity = (ctypes.c_int16 * requirements.sample_count)()
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
            requirements.sample_count,
            innovation,
            requirements.sample_count,
            scratch,
            requirements.liftpack_scratch_elements,
        )
        written = ctypes.c_size_t()
        self._check(
            self._library.resonith_main0_decode(
                source,
                len(payload),
                ctypes.byref(workspace),
                output,
                requirements.sample_count,
                ctypes.byref(written),
            )
        )
        if written.value != requirements.sample_count:
            raise RuntimeError("native decoder returned a partial PCM result")
        samples = np.ctypeslib.as_array(output).copy()
        samples.flags.writeable = False
        return NativeMain0DecodeResult(
            samples,
            requirements.timebase_hz,
            requirements,
        )
