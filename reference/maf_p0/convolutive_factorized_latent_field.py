"""R-161 convolutive anonymous fields followed by exact LSPF dictionaries.

The encoder-side CNMF proposer may expose long, overlapping anonymous causes,
but only decoder-verifiable Basis placements contribute to the prediction.
Every remaining sample is retained by one final mixture-domain Truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np

from .convolutive_anonymous_field import (
    ConvolutiveAnonymousField,
    ConvolutiveAnonymousLanguage,
    infer_convolutive_anonymous_fields,
)
from .latent_source_field import (
    LatentSourceField,
    LatentSourceLanguage,
    infer_latent_source_pattern_field,
)


@dataclass(frozen=True)
class ConvolutiveFactorizedLatentField:
    """Verified per-field Basis predictions plus one exact mixture Truth."""

    proposer: ConvolutiveAnonymousField
    fields: tuple[LatentSourceField, ...]
    prediction: np.ndarray
    truth_correction: np.ndarray
    reconstruction: np.ndarray
    report: dict


def infer_convolutive_factorized_latent_field(
    samples: np.ndarray,
    *,
    sample_rate: int,
    factor_language: ConvolutiveAnonymousLanguage,
    field_language: LatentSourceLanguage,
) -> ConvolutiveFactorizedLatentField:
    """Search repeat dictionaries inside finite convolutive anonymous fields."""

    source = np.asarray(samples)
    proposer = infer_convolutive_anonymous_fields(
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
        raise RuntimeError("convolutive factorized LSPF identity failed")
    return ConvolutiveFactorizedLatentField(
        proposer=proposer,
        fields=fields,
        prediction=prediction,
        truth_correction=truth,
        reconstruction=reconstruction,
        report={
            "schema": "resonith-r161-convolutive-factorized-lspf-1",
            "status": (
                "encoder-side convolutive proposer plus exact Basis oracle; "
                "complete stream RDO pending"
            ),
            "semantic_labels": False,
            "factor_count": len(fields),
            "active_factor_count": sum(
                bool(field.components) for field in fields
            ),
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
