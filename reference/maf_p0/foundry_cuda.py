"""Thin Python control plane for the native R-149 exhaustive CUDA backend."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np


class FoundryCudaError(RuntimeError):
    """A native Foundry backend failure with its stable numeric status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"Resonith Foundry status {status}: {message}")
        self.status = status


class _Range(ctypes.Structure):
    _fields_ = [
        ("block_count", ctypes.c_uint32),
        ("block_samples", ctypes.c_uint32),
        ("first_candidate", ctypes.c_uint64),
        ("candidate_count", ctypes.c_uint64),
    ]


class _Result(ctypes.Structure):
    _fields_ = [
        ("basis_index", ctypes.c_uint32),
        ("target_index", ctypes.c_uint32),
        ("source_offset", ctypes.c_uint32),
        ("gain_q15", ctypes.c_int32),
        ("end_gain_q15", ctypes.c_int32),
        ("transform_flags", ctypes.c_uint32),
        ("squared_error", ctypes.c_uint64),
        ("target_energy", ctypes.c_uint64),
    ]


class _Evidence(ctypes.Structure):
    _fields_ = [
        ("nvrtc_major", ctypes.c_uint32),
        ("nvrtc_minor", ctypes.c_uint32),
        ("compute_major", ctypes.c_uint32),
        ("compute_minor", ctypes.c_uint32),
        ("device_memory_bytes", ctypes.c_uint64),
        ("input_bytes", ctypes.c_uint64),
        ("output_bytes", ctypes.c_uint64),
        ("first_candidate", ctypes.c_uint64),
        ("candidate_count", ctypes.c_uint64),
        ("device_name", ctypes.c_char * 128),
    ]


RESULT_DTYPE = np.dtype(
    {
        "names": (
            "basis_index",
            "target_index",
            "source_offset",
            "gain_q15",
            "end_gain_q15",
            "transform_flags",
            "squared_error",
            "target_energy",
        ),
        "formats": (
            "<u4",
            "<u4",
            "<u4",
            "<i4",
            "<i4",
            "<u4",
            "<u8",
            "<u8",
        ),
        "offsets": (0, 4, 8, 12, 16, 20, 24, 32),
        "itemsize": 40,
    }
)


@dataclass(frozen=True)
class FoundryCudaEvidence:
    """Execution identity and exact tile resource accounting."""

    nvrtc: str
    compute_capability: str
    device_name: str
    device_memory_bytes: int
    input_bytes: int
    output_bytes: int
    first_candidate: int
    candidate_count: int


class GainPhaseCudaFoundry:
    """Enumerate every pair x circular-phase candidate in deterministic tiles."""

    def __init__(
        self,
        library: Path,
        nvrtc_library_directory: Path,
    ) -> None:
        self._library_path = Path(library)
        self._nvrtc_directory = Path(nvrtc_library_directory)
        self._dll = ctypes.CDLL(str(self._library_path))
        self._count = self._dll.resonith_foundry_gain_phase_candidate_count
        self._count.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint64),
        ]
        self._count.restype = ctypes.c_int
        self._cuda = self._dll.resonith_foundry_gain_phase_cuda
        self._cuda.argtypes = [
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(_Range),
            ctypes.POINTER(_Result),
            ctypes.c_size_t,
            ctypes.c_char_p,
            ctypes.POINTER(_Evidence),
            ctypes.POINTER(ctypes.c_char),
            ctypes.c_size_t,
        ]
        self._cuda.restype = ctypes.c_int
        self._cpu = self._dll.resonith_foundry_gain_phase_cpu
        self._cpu.argtypes = [
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_size_t,
            ctypes.POINTER(_Range),
            ctypes.POINTER(_Result),
            ctypes.c_size_t,
        ]
        self._cpu.restype = ctypes.c_int

    def candidate_count(self, block_count: int, block_samples: int) -> int:
        """Return `N * (N - 1) * L` with native overflow validation."""

        output = ctypes.c_uint64()
        status = self._count(block_count, block_samples, ctypes.byref(output))
        if status != 0:
            raise FoundryCudaError(status, "invalid candidate lattice")
        return int(output.value)

    def evaluate_tiles(
        self,
        blocks: np.ndarray,
        *,
        tile_candidates: int = 1 << 20,
    ) -> Iterator[tuple[np.ndarray, FoundryCudaEvidence]]:
        """Yield all exact native results without retaining the full lattice."""

        source = np.ascontiguousarray(blocks, dtype=np.int16)
        if source.ndim != 2 or source.shape[0] < 2 or source.shape[1] == 0:
            raise ValueError("Foundry blocks must be a non-empty 2-D PCM16 matrix")
        if tile_candidates <= 0:
            raise ValueError("tile_candidates must be positive")
        block_count, block_samples = source.shape
        total = self.candidate_count(block_count, block_samples)
        directory = str(self._nvrtc_directory).encode("utf-8")
        source_pointer = source.ctypes.data_as(
            ctypes.POINTER(ctypes.c_int16)
        )
        for first in range(0, total, tile_candidates):
            count = min(tile_candidates, total - first)
            output = np.empty(count, dtype=RESULT_DTYPE)
            evidence = _Evidence()
            error = ctypes.create_string_buffer(16384)
            search_range = _Range(
                block_count,
                block_samples,
                first,
                count,
            )
            status = self._cuda(
                source_pointer,
                source.size,
                ctypes.byref(search_range),
                output.ctypes.data_as(ctypes.POINTER(_Result)),
                output.size,
                directory,
                ctypes.byref(evidence),
                error,
                len(error),
            )
            if status != 0:
                raise FoundryCudaError(
                    status,
                    error.value.decode("utf-8", errors="replace"),
                )
            yield output, FoundryCudaEvidence(
                nvrtc=f"{evidence.nvrtc_major}.{evidence.nvrtc_minor}",
                compute_capability=(
                    f"{evidence.compute_major}.{evidence.compute_minor}"
                ),
                device_name=bytes(evidence.device_name).split(
                    b"\0",
                    1,
                )[0].decode("utf-8", errors="replace"),
                device_memory_bytes=int(evidence.device_memory_bytes),
                input_bytes=int(evidence.input_bytes),
                output_bytes=int(evidence.output_bytes),
                first_candidate=int(evidence.first_candidate),
                candidate_count=int(evidence.candidate_count),
            )

    def evaluate_cpu_tiles(
        self,
        blocks: np.ndarray,
        *,
        tile_candidates: int = 1 << 16,
    ) -> Iterator[np.ndarray]:
        """Yield the portable exact reference results for the same lattice."""

        source = np.ascontiguousarray(blocks, dtype=np.int16)
        if source.ndim != 2 or source.shape[0] < 2 or source.shape[1] == 0:
            raise ValueError("Foundry blocks must be a non-empty 2-D PCM16 matrix")
        if tile_candidates <= 0:
            raise ValueError("tile_candidates must be positive")
        block_count, block_samples = source.shape
        total = self.candidate_count(block_count, block_samples)
        source_pointer = source.ctypes.data_as(
            ctypes.POINTER(ctypes.c_int16)
        )
        for first in range(0, total, tile_candidates):
            count = min(tile_candidates, total - first)
            output = np.empty(count, dtype=RESULT_DTYPE)
            search_range = _Range(
                block_count,
                block_samples,
                first,
                count,
            )
            status = self._cpu(
                source_pointer,
                source.size,
                ctypes.byref(search_range),
                output.ctypes.data_as(ctypes.POINTER(_Result)),
                output.size,
            )
            if status != 0:
                raise FoundryCudaError(status, "portable CPU search failed")
            yield output
