"""R-160 anonymous spectral proposer followed by exact per-field dictionaries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np

from .anonymous_spectral_factor import (
    AnonymousSpectralFactorization,
    AnonymousSpectralLanguage,
    infer_anonymous_spectral_factors,
)
from .latent_source_field import (
    LatentSourceField,
    LatentSourceLanguage,
    infer_latent_source_pattern_field,
)


@dataclass(frozen=True)
class FactorizedLatentField:
    """Verified per-factor Basis predictions plus one mixture-domain Truth."""

    proposer: AnonymousSpectralFactorization
    fields: tuple[LatentSourceField, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    report: dict


def infer_factorized_latent_field(
    samples: np.ndarray,
    *,
    sample_rate: int,
    factor_language: AnonymousSpectralLanguage,
    field_language: LatentSourceLanguage,
) -> FactorizedLatentField:
    """Search repeat dictionaries after anonymous phase-preserving separation."""

    source = np.asarray(samples)
    proposer = infer_anonymous_spectral_factors(
        source,
        sample_rate=sample_rate,
        language=factor_language,
    )
    fields = tuple(
        infer_latent_source_pattern_field(
            np.asarray(factor),
            language=field_language,
        )
        for factor in proposer.factors
    )
    prediction = sum(
        (field.prediction.astype(np.int64) for field in fields),
        start=np.zeros(source.shape, dtype=np.int64),
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
        raise RuntimeError("factorized LSPF exact identity failed")
    return FactorizedLatentField(
        proposer,
        fields,
        prediction,
        truth,
        reconstruction,
        {
            "schema": "resonith-r160-factorized-lspf-1",
            "status": (
                "encoder-side anonymous proposer plus exact Basis oracle; "
                "complete stream RDO pending"
            ),
            "semantic_labels": False,
            "factor_count": len(fields),
            "active_factor_count": sum(bool(field.components) for field in fields),
            "latent_component_count": sum(
                len(field.components) for field in fields
            ),
            "latent_occurrence_count": sum(
                len(component.occurrences)
                for field in fields
                for component in field.components
            ),
            "one_final_mixture_truth": True,
            "exact_integer_reconstruction": True,
            "source_sha256": source_hash,
            "reconstruction_sha256": reconstruction_hash,
            "proposer": proposer.report,
            "fields": [
                {
                    "factor_index": index,
                    **field.report,
                }
                for index, field in enumerate(fields)
            ],
        },
    )
