"""Reproducible first MAF-P0 compression benchmark on harmonic material."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import zlib

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.codec import encode_samples  # noqa: E402
from maf_p0.model import (  # noqa: E402
    encode_basis_latent,
    save_analysis_model,
    train_linear_cibs,
)
from maf_p0.periodic import apply_block_gains, render_unity_basis  # noqa: E402
from cibs0 import materialize_basis  # noqa: E402


def harmonic_basis(
    length: int,
    gains: np.ndarray,
    phases: np.ndarray,
    peak: float,
) -> np.ndarray:
    position = np.arange(length, dtype=np.float64) / length
    output = np.zeros(length, dtype=np.float64)
    for index, (gain, phase) in enumerate(
        zip(gains, phases, strict=True),
        start=1,
    ):
        output += gain * np.sin(2.0 * np.pi * index * position + phase)
    output *= peak / max(float(np.max(np.abs(output))), 1.0)
    return np.rint(output).astype(np.int16)


def build_corpus(length: int, count: int, seed: int = 20260726) -> np.ndarray:
    random = np.random.default_rng(seed)
    corpus = []
    for _ in range(count):
        gains = np.array(
            [
                1.0,
                random.uniform(0.05, 0.60),
                random.uniform(0.02, 0.35),
                random.uniform(0.00, 0.20),
                random.uniform(0.00, 0.12),
            ]
        )
        phases = random.uniform(-0.35, 0.35, gains.size)
        corpus.append(
            harmonic_basis(
                length,
                gains,
                phases,
                random.uniform(14_000, 24_000),
            ).reshape(1, -1)
        )
    return np.stack(corpus)


def main() -> None:
    sample_rate = 48_000
    duration_seconds = 10
    sample_count = sample_rate * duration_seconds
    period = 240
    basis_length = 256
    block_size = 1024

    model = train_linear_cibs(
        build_corpus(basis_length, 64),
        latent_elements=16,
        model_id="CIBS0-P0-BENCH",
    )
    target = harmonic_basis(
        basis_length,
        np.array([1.0, 0.34, 0.16, 0.09, 0.04]),
        np.array([0.11, -0.07, 0.18, -0.16, 0.03]),
        19_000,
    )
    unity = render_unity_basis(
        target,
        sample_count,
        int(round((1 << 32) / period)),
    )
    block_count = (sample_count + block_size - 1) // block_size
    time = np.arange(block_count, dtype=np.float64)
    gains = np.rint(
        (
            0.70
            + 0.18 * np.sin(2.0 * np.pi * time / 97.0)
            + 0.04 * np.sin(2.0 * np.pi * time / 17.0)
        )
        * (1 << 15)
    ).astype(np.int32)
    source = apply_block_gains(unity, gains, block_size)

    configurations = {
        "raw_lossless": {
            "basis_mode": "raw",
            "basis_correction_step": 1,
            "residual_step": 1,
        },
        "cibs_lossless": {
            "basis_mode": "cibs",
            "basis_correction_step": 1,
            "residual_step": 1,
        },
        "cibs_lossy_q16": {
            "basis_mode": "cibs",
            "basis_correction_step": 8,
            "residual_step": 16,
        },
    }
    report: dict[str, object] = {
        "corpus": "synthetic harmonic sustained note",
        "duration_seconds": duration_seconds,
        "sample_rate": sample_rate,
        "pcm_bytes": source.nbytes,
        "results": {},
    }
    for name, options in configurations.items():
        result = encode_samples(
            source,
            sample_rate,
            cibs_model=model if options["basis_mode"] == "cibs" else None,
            basis_length=basis_length,
            gain_block_size=block_size,
            period_samples=period,
            **options,
        )
        report["results"][name] = result.report

    # CIBS-specific amortization test over a Basis bank.
    basis_bank = build_corpus(basis_length, 128, seed=20260727)
    raw_bank = basis_bank.astype("<i2", copy=False).tobytes()
    latents = []
    exact_corrections = []
    q8_corrections = []
    for basis in basis_bank:
        latent = encode_basis_latent(basis, model)
        synthesized = materialize_basis(latent, model).samples.astype(np.int32)
        difference = basis.astype(np.int32) - synthesized
        latents.append(latent)
        exact_corrections.append(difference.astype(np.int32))
        quantized = np.where(
            difference < 0,
            -((np.abs(difference) + 4) // 8),
            (difference + 4) // 8,
        )
        q8_corrections.append(quantized.astype(np.int16))
    latent_bytes = np.stack(latents).tobytes()
    exact_bytes = np.stack(exact_corrections).astype("<i4").tobytes()
    q8_bytes = np.stack(q8_corrections).astype("<i2").tobytes()
    raw_compressed = len(zlib.compress(raw_bank, 9))
    exact_compressed = len(zlib.compress(latent_bytes, 9)) + len(
        zlib.compress(exact_bytes, 9)
    )
    q8_compressed = len(zlib.compress(latent_bytes, 9)) + len(
        zlib.compress(q8_bytes, 9)
    )
    report["basis_bank_128"] = {
        "raw_basis_bytes": len(raw_bank),
        "raw_basis_zlib_bytes": raw_compressed,
        "cibs_exact_zlib_bytes": exact_compressed,
        "cibs_q8_zlib_bytes": q8_compressed,
        "cibs_exact_saving_vs_raw_basis": 1.0
        - exact_compressed / raw_compressed,
        "cibs_q8_saving_vs_raw_basis": 1.0 - q8_compressed / raw_compressed,
        "note": "model package excluded; reported separately",
    }

    with tempfile.TemporaryDirectory() as directory:
        model_path = Path(directory) / "cibs0-p0-bench.npz"
        save_analysis_model(model_path, model)
        report["experimental_model_package_bytes"] = model_path.stat().st_size
    print(json.dumps(report, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
