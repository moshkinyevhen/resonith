"""Reproducible MAF-P1 lifetime/trajectory/transient benchmark with Opus."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.codec import encode_samples  # noqa: E402
from maf_p0.opus_anchor import run_opus_anchor  # noqa: E402
from maf_p0.periodic import (  # noqa: E402
    PhaseTrajectory,
    apply_block_gains,
    render_basis_trajectory,
)
from maf_p0.stateful import encode_stateful_samples  # noqa: E402


def harmonic_basis(
    length: int,
    gains: list[float],
    phases: list[float],
    peak: float,
) -> np.ndarray:
    position = np.arange(length, dtype=np.float64) / length
    output = np.zeros(length, dtype=np.float64)
    for harmonic, (gain, phase) in enumerate(
        zip(gains, phases, strict=True),
        start=1,
    ):
        output += gain * np.sin(2.0 * np.pi * harmonic * position + phase)
    output *= peak / max(float(np.max(np.abs(output))), 1.0)
    return np.rint(output).astype(np.int16)


def trajectory(
    sample_count: int,
    periods: list[float],
    *,
    phase_origin_q32: int,
) -> PhaseTrajectory:
    positions = np.rint(
        np.linspace(0, sample_count, len(periods))
    ).astype(np.int64)
    increments = np.asarray(
        [int(round((1 << 32) / period)) for period in periods],
        dtype=np.uint32,
    )
    return PhaseTrajectory(positions, increments, phase_origin_q32)


def build_signal() -> tuple[int, np.ndarray, list[PhaseTrajectory]]:
    sample_rate = 48000
    segment_samples = sample_rate
    basis_a = harmonic_basis(
        256,
        [1.0, 0.31, 0.14, 0.07],
        [0.10, -0.06, 0.19, -0.12],
        13000.0,
    )
    basis_b = harmonic_basis(
        256,
        [1.0, 0.18, 0.28, 0.11, 0.05],
        [-0.12, 0.08, -0.16, 0.21, -0.03],
        11000.0,
    )
    trajectories = [
        trajectory(
            segment_samples,
            [240.0, 228.0, 214.0, 222.0, 238.0],
            phase_origin_q32=0x0102_0304,
        ),
        trajectory(
            segment_samples,
            [190.0, 205.0, 230.0, 216.0, 184.0],
            phase_origin_q32=0xA010_2040,
        ),
        trajectory(
            segment_samples,
            [238.0, 226.0, 216.0, 224.0, 242.0],
            phase_origin_q32=0x2030_4050,
        ),
    ]
    unity = np.concatenate(
        [
            render_basis_trajectory(basis_a, trajectories[0]),
            render_basis_trajectory(basis_b, trajectories[1]),
            render_basis_trajectory(basis_a, trajectories[2]),
        ]
    )
    block_size = 512
    block_count = (unity.size + block_size - 1) // block_size
    block = np.arange(block_count, dtype=np.float64)
    gains = np.rint(
        (
            0.64
            + 0.20 * np.sin(2.0 * np.pi * block / 137.0)
            + 0.06 * np.sin(2.0 * np.pi * block / 29.0)
        )
        * (1 << 15)
    ).astype(np.int32)
    source = apply_block_gains(unity, gains, block_size)
    for start in (17000, 48000 + 11000, 96000 + 26000):
        source[start : start + 10] = np.array(
            [26000, -23000, 18000, -12000, 8000, -4500, 2200, -900, 250, 0],
            dtype=np.int16,
        )
    return sample_rate, source, trajectories


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--opus-tools",
        default=os.environ.get("RESONITH_OPUS_TOOLS"),
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    sample_rate, source, trajectories = build_signal()
    duration_seconds = source.size / sample_rate
    report: dict[str, object] = {
        "status": "diagnostic experiment, not a codec claim",
        "corpus": "deterministic three-segment harmonic/chirp/transient signal",
        "sample_rate": sample_rate,
        "sample_count": int(source.size),
        "duration_seconds": duration_seconds,
        "pcm_bytes": int(source.nbytes),
        "maf": {},
        "opus": {},
    }

    p0 = encode_samples(
        source,
        sample_rate,
        basis_mode="raw",
        period_samples=240,
        gain_block_size=512,
        residual_step=16,
    )
    report["maf"]["p0_single_basis_q16"] = p0.report

    configurations = [
        ("p1_multi_basis_q16_no_transient", 16, "off"),
        ("p1_multi_basis_q16_transient", 16, "on"),
        ("p1_multi_basis_q16_auto", 16, "auto"),
        ("p1_multi_basis_q64_auto", 64, "auto"),
        ("p1_multi_basis_q256_auto", 256, "auto"),
        ("p1_multi_basis_q1024_auto", 1024, "auto"),
    ]
    for name, residual_step, transient_mode in configurations:
        encoded = encode_stateful_samples(
            source,
            sample_rate,
            basis_mode="raw",
            segment_samples=sample_rate,
            phase_trajectories=trajectories,
            analysis_periods=[240, 190, 238],
            gain_block_size=512,
            residual_step=residual_step,
            transient_mode=transient_mode,
            transient_quantization_step=8,
        )
        encoded.report["effective_bitrate_kbps"] = (
            8.0 * len(encoded.payload) / duration_seconds / 1000.0
        )
        report["maf"][name] = encoded.report

    if args.opus_tools:
        for bitrate in (32.0, 48.0, 64.0, 96.0):
            anchor = run_opus_anchor(
                source,
                sample_rate,
                bitrate_kbps=bitrate,
                tools_directory=args.opus_tools,
            )
            report["opus"][f"{bitrate:g}k_vbr_music"] = anchor.report
    else:
        report["opus"]["status"] = (
            "unavailable; set RESONITH_OPUS_TOOLS or pass --opus-tools"
        )

    serialized = json.dumps(report, indent=2, allow_nan=True)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
