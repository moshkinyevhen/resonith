"""R-160 perfect-reconstruction partial-spectrum LSPF research oracle."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib

import numpy as np

from .latent_source_field import (
    LatentSourceField,
    LatentSourceLanguage,
    infer_latent_source_pattern_field,
)
from .partial_spectrum_orbit import (
    reversible_multiband_analysis,
    reversible_multiband_synthesis,
)


@dataclass(frozen=True)
class PartialSpectrumBandField:
    """One anonymous field search in an exact lifting coefficient domain."""

    band_index: int
    decimation: int
    normalization_shift: int
    field: LatentSourceField


@dataclass(frozen=True)
class PartialSpectrumLatentField:
    """Time-domain exact result after independently searched frequency fields."""

    bands: tuple[PartialSpectrumBandField, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    report: dict


def _decimations(levels: int) -> tuple[int, ...]:
    return (
        1 << levels,
        *(1 << level for level in range(levels, 0, -1)),
    )


def _normalization_shift(values: np.ndarray) -> int:
    maximum = int(np.max(np.abs(values))) if values.size else 0
    shift = 0
    while maximum > 32767:
        maximum = (maximum + 1) >> 1
        shift += 1
    return shift


def infer_partial_spectrum_latent_field(
    samples: np.ndarray,
    *,
    levels: int,
    language: LatentSourceLanguage,
) -> PartialSpectrumLatentField:
    """Search exact lifting bands and retain one final time-domain Truth.

    Coefficient bands are normalized by a declared power-of-two only for the
    bounded int16 proposer. Discarded low bits are never lost: they remain in
    the final exact time-domain Truth correction.
    """

    source = np.asarray(samples)
    if (
        source.dtype != np.int16
        or source.ndim != 2
        or source.shape[0] == 0
        or not 1 <= source.shape[1] <= 8
    ):
        raise TypeError("partial-spectrum LSPF requires frame-major PCM16")
    channel_bands = [
        reversible_multiband_analysis(source[:, channel], levels)[0]
        for channel in range(source.shape[1])
    ]
    decimations = _decimations(levels)
    band_fields: list[PartialSpectrumBandField] = []
    prediction_bands: list[np.ndarray] = []
    for band_index, decimation in enumerate(decimations):
        exact_band = np.stack(
            [
                channel_bands[channel][band_index]
                for channel in range(source.shape[1])
            ],
            axis=1,
        )
        shift = _normalization_shift(exact_band)
        proposer_band = np.right_shift(exact_band, shift)
        proposer_band = np.clip(
            proposer_band,
            -32768,
            32767,
        ).astype(np.int16)
        scales = tuple(
            sorted(
                {
                    max(16, scale // decimation)
                    for scale in language.scales
                    if max(16, scale // decimation)
                        <= proposer_band.shape[0]
                }
            )
        )
        if not scales:
            prediction_bands.append(np.zeros_like(exact_band))
            continue
        band_language = replace(
            language,
            scales=scales,
            origin_hop=max(1, language.origin_hop // decimation),
            maximum_lag=max(0, language.maximum_lag // decimation),
        )
        field = infer_latent_source_pattern_field(
            proposer_band,
            language=band_language,
        )
        band_fields.append(
            PartialSpectrumBandField(
                band_index,
                decimation,
                shift,
                field,
            )
        )
        prediction_bands.append(
            np.left_shift(field.prediction.astype(np.int64), shift)
        )

    if len(prediction_bands) != len(decimations):
        raise RuntimeError("partial-spectrum prediction geometry is incomplete")
    prediction = np.empty(source.shape, dtype=np.int64)
    prediction_tuple = tuple(prediction_bands)
    for channel in range(source.shape[1]):
        prediction[:, channel] = reversible_multiband_synthesis(
            tuple(band[:, channel] for band in prediction_tuple),
            source.shape[0],
        )
    source64 = source.astype(np.int64)
    truth = source64 - prediction
    reconstruction = prediction + truth
    source_hash = hashlib.sha256(
        np.ascontiguousarray(source, dtype="<i2").tobytes()
    ).hexdigest()
    reconstruction_hash = hashlib.sha256(
        np.ascontiguousarray(reconstruction, dtype="<i2").tobytes()
    ).hexdigest()
    if source_hash != reconstruction_hash:
        raise RuntimeError("partial-spectrum LSPF exact identity failed")
    return PartialSpectrumLatentField(
        tuple(band_fields),
        prediction,
        truth,
        reconstruction,
        {
            "schema": "resonith-r160-partial-spectrum-lspf-1",
            "status": "research oracle; complete stream RDO pending",
            "levels": levels,
            "band_count": len(decimations),
            "active_band_count": sum(
                bool(item.field.components) for item in band_fields
            ),
            "latent_component_count": sum(
                len(item.field.components) for item in band_fields
            ),
            "latent_occurrence_count": sum(
                len(component.occurrences)
                for item in band_fields
                for component in item.field.components
            ),
            "normalization_shifts": [
                item.normalization_shift for item in band_fields
            ],
            "exact_integer_reconstruction": True,
            "source_sha256": source_hash,
            "reconstruction_sha256": reconstruction_hash,
            "one_final_time_domain_truth": True,
        },
    )
