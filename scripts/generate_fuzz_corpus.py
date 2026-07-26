"""Generate deterministic valid LiftPack seeds for native fuzzing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lpc_oracle import encode_lpc_liftpack_oracle  # noqa: E402
from maf_p0.residual import encode_liftpack  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)

    structured = np.concatenate(
        (
            np.zeros(64, dtype=np.int16),
            np.arange(-32, 32, dtype=np.int16),
            np.tile(np.asarray([32767, -32768], dtype=np.int16), 32),
        )
    )
    (args.output_directory / "liftpack1_structured.rsl").write_bytes(
        encode_liftpack(structured, block_size=64).payload
    )

    index = np.arange(256, dtype=np.float64)
    tonal = np.rint(
        12000.0 * np.sin(2.0 * np.pi * index / 73.0)
    ).astype(np.int16)
    lpc, _ = encode_lpc_liftpack_oracle(
        tonal,
        block_size=256,
        lpc_orders=(4, 8, 12, 16),
    )
    (args.output_directory / "liftpack2_lpc.rsl").write_bytes(lpc)


if __name__ == "__main__":
    main()
