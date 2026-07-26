"""Bit-exact experimental kernel for Cached Integer Basis Synthesis.

This is the executable semantic prototype for CIBS-0. It intentionally uses
only integer NumPy operations. The demo weights are deterministic placeholders,
not a trained or normative model.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import numpy as np


MAX_LATENT_ELEMENTS = 128
MAX_BASIS_CHANNELS = 8
MAX_BASIS_ELEMENTS = 8 * 2048
MAX_ADAPTER_RANK = 4


class BasisHashMismatch(ValueError):
    """Raised before state commit when the materialized Basis hash differs."""


def _require_dtype(name: str, value: np.ndarray, dtype: np.dtype) -> None:
    if value.dtype != dtype:
        raise TypeError(f"{name} must have dtype {dtype}, got {value.dtype}")


def _round_shift_ties_away(value: np.ndarray, shift: int) -> np.ndarray:
    """Canonical signed right shift, round-to-nearest with ties away from zero."""

    if not 0 <= shift <= 30:
        raise ValueError("shift must be in [0, 30]")
    signed = np.asarray(value, dtype=np.int64)
    if shift == 0:
        return signed
    magnitude = np.abs(signed)
    rounded = (magnitude + (1 << (shift - 1))) >> shift
    return np.where(signed < 0, -rounded, rounded)


def _saturate_int16(value: np.ndarray) -> np.ndarray:
    return np.clip(value, -32768, 32767).astype(np.int16)


def _piecewise_linear(value: np.ndarray) -> np.ndarray:
    """Integer leaky activation: x for x>=0, round(x/8) otherwise."""

    signed = np.asarray(value, dtype=np.int64)
    negative = _round_shift_ties_away(signed, 3)
    return np.where(signed < 0, negative, signed)


@dataclass(frozen=True)
class CIBS0Adapter:
    """Bounded low-rank output delta for the projection stage."""

    u: np.ndarray
    v: np.ndarray
    inner_shift: int
    output_shift: int

    def validate(self, output_elements: int, latent_elements: int) -> None:
        _require_dtype("adapter.u", self.u, np.dtype(np.int8))
        _require_dtype("adapter.v", self.v, np.dtype(np.int8))
        if self.u.ndim != 2 or self.v.ndim != 2:
            raise ValueError("adapter matrices must be rank-2")
        rank = self.u.shape[1]
        if not 1 <= rank <= MAX_ADAPTER_RANK:
            raise ValueError("adapter rank exceeds CIBS-0 limit")
        if self.u.shape != (output_elements, rank):
            raise ValueError("adapter.u shape mismatch")
        if self.v.shape != (rank, latent_elements):
            raise ValueError("adapter.v shape mismatch")
        if not 0 <= self.inner_shift <= 30:
            raise ValueError("adapter inner_shift out of range")
        if not 0 <= self.output_shift <= 30:
            raise ValueError("adapter output_shift out of range")


@dataclass(frozen=True)
class CIBS0Model:
    """Fixed versioned integer synthesis model."""

    model_id: str
    basis_channels: int
    coarse_length: int
    projection: np.ndarray
    projection_bias: np.ndarray
    projection_shift: int
    refinement_kernels: tuple[np.ndarray, ...]
    refinement_shifts: tuple[int, ...]

    @property
    def latent_elements(self) -> int:
        return int(self.projection.shape[1])

    @property
    def coarse_elements(self) -> int:
        return self.basis_channels * self.coarse_length

    @property
    def output_length(self) -> int:
        return self.coarse_length << len(self.refinement_kernels)

    @property
    def output_elements(self) -> int:
        return self.basis_channels * self.output_length

    def validate(self) -> None:
        if not self.model_id or len(self.model_id.encode("utf-8")) > 255:
            raise ValueError("model_id must contain 1..255 UTF-8 bytes")
        if not 1 <= self.basis_channels <= MAX_BASIS_CHANNELS:
            raise ValueError("basis_channels exceeds CIBS-0 limit")
        if self.coarse_length < 1:
            raise ValueError("coarse_length must be positive")
        if self.output_elements > MAX_BASIS_ELEMENTS:
            raise ValueError("output Basis exceeds CIBS-0 limit")

        _require_dtype("projection", self.projection, np.dtype(np.int8))
        _require_dtype(
            "projection_bias", self.projection_bias, np.dtype(np.int32)
        )
        if self.projection.ndim != 2:
            raise ValueError("projection must be rank-2")
        if self.projection.shape[0] != self.coarse_elements:
            raise ValueError("projection output shape mismatch")
        if not 1 <= self.latent_elements <= MAX_LATENT_ELEMENTS:
            raise ValueError("latent size exceeds CIBS-0 limit")
        if self.projection_bias.shape != (self.coarse_elements,):
            raise ValueError("projection_bias shape mismatch")
        if not 0 <= self.projection_shift <= 30:
            raise ValueError("projection_shift out of range")
        if len(self.refinement_kernels) != len(self.refinement_shifts):
            raise ValueError("refinement kernel/shift count mismatch")
        if len(self.refinement_kernels) > 4:
            raise ValueError("too many refinement stages")

        for index, (kernel, shift) in enumerate(
            zip(self.refinement_kernels, self.refinement_shifts, strict=True)
        ):
            _require_dtype(
                f"refinement_kernels[{index}]", kernel, np.dtype(np.int8)
            )
            if kernel.ndim != 2 or kernel.shape[0] != self.basis_channels:
                raise ValueError("refinement kernel channel mismatch")
            if kernel.shape[1] < 1 or kernel.shape[1] > 7:
                raise ValueError("refinement kernel width must be in [1, 7]")
            if kernel.shape[1] % 2 == 0:
                raise ValueError("refinement kernel width must be odd")
            if not 0 <= shift <= 30:
                raise ValueError("refinement shift out of range")


@dataclass(frozen=True)
class MaterializedBasis:
    model_id: str
    samples: np.ndarray
    sha256: str
    integer_macs: int


def _project(
    latent: np.ndarray,
    model: CIBS0Model,
    adapter: CIBS0Adapter | None,
) -> tuple[np.ndarray, int]:
    latent64 = latent.astype(np.int64)
    projection64 = model.projection.astype(np.int64)
    accumulator = projection64 @ latent64
    accumulator += model.projection_bias.astype(np.int64)
    output = _round_shift_ties_away(accumulator, model.projection_shift)
    macs = model.coarse_elements * model.latent_elements

    if adapter is not None:
        adapter.validate(model.coarse_elements, model.latent_elements)
        inner = adapter.v.astype(np.int64) @ latent64
        inner = _round_shift_ties_away(inner, adapter.inner_shift)
        delta = adapter.u.astype(np.int64) @ inner
        delta = _round_shift_ties_away(delta, adapter.output_shift)
        output += delta
        macs += (
            adapter.v.shape[0] * model.latent_elements
            + model.coarse_elements * adapter.u.shape[1]
        )

    activated = _piecewise_linear(output)
    coarse = _saturate_int16(activated)
    return coarse.reshape(model.basis_channels, model.coarse_length), macs


def _refine(
    basis: np.ndarray,
    kernel: np.ndarray,
    shift: int,
) -> tuple[np.ndarray, int]:
    upsampled = np.repeat(basis, 2, axis=1).astype(np.int64)
    kernel64 = kernel.astype(np.int64)
    accumulator = np.zeros_like(upsampled, dtype=np.int64)
    center = kernel.shape[1] // 2

    for tap in range(kernel.shape[1]):
        offset = tap - center
        shifted = np.roll(upsampled, shift=offset, axis=1)
        accumulator += kernel64[:, tap, None] * shifted

    rounded = _round_shift_ties_away(accumulator, shift)
    activated = _piecewise_linear(rounded)
    macs = basis.shape[0] * upsampled.shape[1] * kernel.shape[1]
    return _saturate_int16(activated), macs


def basis_sha256(model_id: str, samples: np.ndarray) -> str:
    """Hash model identity, shape and canonical little-endian int16 samples."""

    _require_dtype("samples", samples, np.dtype(np.int16))
    if samples.ndim != 2:
        raise ValueError("samples must be [channels, length]")
    model_bytes = model_id.encode("utf-8")
    header = struct.pack(
        "<BII", len(model_bytes), int(samples.shape[0]), int(samples.shape[1])
    )
    payload = samples.astype("<i2", copy=False).tobytes(order="C")
    return hashlib.sha256(header + model_bytes + payload).hexdigest()


def materialize_basis(
    latent: np.ndarray,
    model: CIBS0Model,
    *,
    adapter: CIBS0Adapter | None = None,
    correction: np.ndarray | None = None,
    expected_sha256: str | None = None,
) -> MaterializedBasis:
    """Materialize an immutable Basis in staging and verify before commit."""

    model.validate()
    _require_dtype("latent", latent, np.dtype(np.int8))
    if latent.shape != (model.latent_elements,):
        raise ValueError("latent shape mismatch")

    basis, macs = _project(latent, model, adapter)
    for kernel, shift in zip(
        model.refinement_kernels, model.refinement_shifts, strict=True
    ):
        basis, stage_macs = _refine(basis, kernel, shift)
        macs += stage_macs

    if correction is not None:
        if correction.shape != basis.shape:
            raise ValueError("correction shape mismatch")
        if correction.dtype not in (np.dtype(np.int16), np.dtype(np.int32)):
            raise TypeError("correction must be int16 or int32")
        basis = _saturate_int16(
            basis.astype(np.int64) + correction.astype(np.int64)
        )

    digest = basis_sha256(model.model_id, basis)
    if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
        raise BasisHashMismatch(
            f"Basis hash mismatch: expected {expected_sha256}, got {digest}"
        )

    immutable = basis.copy()
    immutable.flags.writeable = False
    return MaterializedBasis(model.model_id, immutable, digest, macs)


def make_demo_model() -> CIBS0Model:
    """Return deterministic non-normative weights for executable tests."""

    channels = 2
    coarse_length = 8
    latent_elements = 8
    output_elements = channels * coarse_length

    projection_values = (
        (np.arange(output_elements * latent_elements, dtype=np.int32) * 17 + 5)
        % 31
    ) - 15
    projection = projection_values.astype(np.int8).reshape(
        output_elements, latent_elements
    )
    bias = (
        (np.arange(output_elements, dtype=np.int32) * 29 + 11) % 97
    ) - 48

    kernel0 = np.array(
        [[1, 2, 10, 2, 1], [1, 3, 8, 3, 1]], dtype=np.int8
    )
    kernel1 = np.array(
        [[1, 6, 1], [1, 6, 1]], dtype=np.int8
    )
    model = CIBS0Model(
        model_id="CIBS0-DEMO-NOT-NORMATIVE",
        basis_channels=channels,
        coarse_length=coarse_length,
        projection=projection,
        projection_bias=bias,
        projection_shift=3,
        refinement_kernels=(kernel0, kernel1),
        refinement_shifts=(4, 3),
    )
    model.validate()
    return model
