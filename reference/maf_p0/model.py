"""Training, analysis and transport helpers for experimental CIBS models."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from cibs0 import CIBS0Model


def train_linear_cibs(
    bases: np.ndarray,
    *,
    latent_elements: int = 16,
    model_id: str = "CIBS0-P0-LINEAR",
) -> CIBS0Model:
    """Train a small PCA-derived integer CIBS projection.

    Training is floating-point and non-normative. The returned decoder model
    is integer-only and has no refinement stages.
    """

    if bases.dtype != np.int16 or bases.ndim != 3:
        raise TypeError("bases must be int16 [examples, channels, length]")
    examples, channels, length = bases.shape
    features = channels * length
    if examples < 2:
        raise ValueError("at least two Basis examples are required")
    rank = min(latent_elements, examples - 1, features, 128)
    if rank < 1:
        raise ValueError("latent rank is zero")

    matrix = bases.reshape(examples, features).astype(np.float64)
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    _, _, components = np.linalg.svd(centered, full_matrices=False)
    components = components[:rank]
    scores = centered @ components.T

    scale = np.maximum(np.percentile(np.abs(scores), 99.0, axis=0) / 120.0, 1e-6)
    decoder_float = components.T * scale[None, :]
    maximum_weight = float(np.max(np.abs(decoder_float)))
    if maximum_weight == 0.0:
        projection_shift = 0
    else:
        projection_shift = int(
            np.clip(np.floor(np.log2(120.0 / maximum_weight)), 0, 20)
        )
    fixed_scale = float(1 << projection_shift)
    projection = np.clip(
        np.rint(decoder_float * fixed_scale), -127, 127
    ).astype(np.int8)
    bias = np.clip(
        np.rint(mean * fixed_scale),
        np.iinfo(np.int32).min,
        np.iinfo(np.int32).max,
    ).astype(np.int32)

    model = CIBS0Model(
        model_id=model_id,
        basis_channels=channels,
        coarse_length=length,
        projection=projection,
        projection_bias=bias,
        projection_shift=projection_shift,
        refinement_kernels=(),
        refinement_shifts=(),
    )
    model.validate()
    return model


def encode_basis_latent(basis: np.ndarray, model: CIBS0Model) -> np.ndarray:
    """Find a bounded int8 latent for one target Basis."""

    model.validate()
    if basis.dtype != np.int16:
        raise TypeError("basis must be int16")
    if basis.shape != (model.basis_channels, model.output_length):
        raise ValueError("basis shape mismatch")

    target = basis.reshape(-1).astype(np.float64)
    fixed_scale = float(1 << model.projection_shift)
    decoder = model.projection.astype(np.float64) / fixed_scale
    mean = model.projection_bias.astype(np.float64) / fixed_scale
    latent, _, _, _ = np.linalg.lstsq(decoder, target - mean, rcond=None)
    return np.clip(np.rint(latent), -127, 127).astype(np.int8)


def save_analysis_model(path: str | Path, model: CIBS0Model) -> None:
    """Save an experimental model package; not a normative bitstream payload."""

    model.validate()
    kernels = np.empty(len(model.refinement_kernels), dtype=object)
    for index, kernel in enumerate(model.refinement_kernels):
        kernels[index] = kernel
    np.savez_compressed(
        path,
        model_id=np.array(model.model_id),
        basis_channels=np.array(model.basis_channels, dtype=np.int32),
        coarse_length=np.array(model.coarse_length, dtype=np.int32),
        projection=model.projection,
        projection_bias=model.projection_bias,
        projection_shift=np.array(model.projection_shift, dtype=np.int32),
        refinement_count=np.array(len(kernels), dtype=np.int32),
        refinement_shifts=np.asarray(model.refinement_shifts, dtype=np.int32),
        **{
            f"kernel_{index}": kernel
            for index, kernel in enumerate(model.refinement_kernels)
        },
    )


def load_analysis_model(path: str | Path) -> CIBS0Model:
    with np.load(path, allow_pickle=False) as package:
        count = int(package["refinement_count"])
        kernels = tuple(package[f"kernel_{index}"] for index in range(count))
        model = CIBS0Model(
            model_id=str(package["model_id"]),
            basis_channels=int(package["basis_channels"]),
            coarse_length=int(package["coarse_length"]),
            projection=package["projection"].copy(),
            projection_bias=package["projection_bias"].copy(),
            projection_shift=int(package["projection_shift"]),
            refinement_kernels=kernels,
            refinement_shifts=tuple(
                int(value) for value in package["refinement_shifts"]
            ),
        )
    model.validate()
    return model
