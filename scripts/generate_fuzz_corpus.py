"""Generate deterministic valid decoder seeds for native fuzzing."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.lpc_oracle import encode_lpc_liftpack_oracle  # noqa: E402
from maf_p0.lapped_oracle import encode_lapped_stream  # noqa: E402
from maf_p0.lapped_streaming import (  # noqa: E402
    encode_lapped_compact_packet_stream,
    encode_lapped_packet_stream,
    encode_lapped_transform_packet_stream,
)
from maf_p0.main0 import (  # noqa: E402
    Main0State,
    pack_main0_lpc_residual_stream,
    pack_main0_state_stream,
)
from maf_p0.multichannel import pack_main0_independent_stream  # noqa: E402
from maf_p0.composition import GainEventLaw  # noqa: E402
from maf_p0.periodic import constant_phase_trajectory  # noqa: E402
from maf_p0.residual import encode_liftpack  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    liftpack_directory = args.output_directory / "liftpack"
    main0_directory = args.output_directory / "main0"
    seek_directory = args.output_directory / "seek"
    lapped_directory = args.output_directory / "lapped"
    lapped_compact_directory = args.output_directory / "lapped_compact"
    lapped_packet_directory = args.output_directory / "lapped_packet"
    liftpack_directory.mkdir(parents=True, exist_ok=True)
    main0_directory.mkdir(parents=True, exist_ok=True)
    seek_directory.mkdir(parents=True, exist_ok=True)
    lapped_directory.mkdir(parents=True, exist_ok=True)
    lapped_compact_directory.mkdir(parents=True, exist_ok=True)
    lapped_packet_directory.mkdir(parents=True, exist_ok=True)

    structured = np.concatenate(
        (
            np.zeros(64, dtype=np.int16),
            np.arange(-32, 32, dtype=np.int16),
            np.tile(np.asarray([32767, -32768], dtype=np.int16), 32),
        )
    )
    (liftpack_directory / "liftpack1_structured.rsl").write_bytes(
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
    (liftpack_directory / "liftpack2_lpc.rsl").write_bytes(lpc)

    (main0_directory / "zero_atom_lpc.rsc").write_bytes(
        pack_main0_lpc_residual_stream(
            sample_rate=48_000,
            innovation_q=tonal,
            innovation_step=3,
            residual_block_size=64,
            lpc_orders=(4, 8, 12, 16),
        )
    )
    stereo = np.stack((tonal, np.roll(tonal, 19)), axis=1)
    (main0_directory / "independent_stereo.rsc").write_bytes(
        pack_main0_independent_stream(
            sample_rate=48_000,
            innovation_q=stereo,
            innovation_step=1,
            residual_block_size=64,
            lpc_orders=(4, 8, 12, 16),
        )
    )

    basis_index = np.arange(64, dtype=np.float64)
    basis = np.rint(
        16_000.0 * np.sin(2.0 * np.pi * basis_index / 64.0)
    ).astype(np.int16)
    duration = int(tonal.size)
    state = Main0State(
        basis=basis,
        trajectory=constant_phase_trajectory(duration, 0x0400_0000),
        gain_law=GainEventLaw(
            positions=np.asarray([0, duration // 2], dtype=np.uint32),
            gains_q15=np.asarray([32768, 24576], dtype=np.int32),
            sample_count=duration,
        ),
    )
    (main0_directory / "periodic_atom.rsc").write_bytes(
        pack_main0_state_stream(
            sample_rate=48_000,
            states=(state,),
            innovation_q=np.zeros(duration, dtype=np.int16),
            innovation_step=1,
            residual_block_size=64,
            residual_codec="rsl2",
            lpc_orders=(4,),
        )
    )
    (seek_directory / "canonical_mode.bin").write_bytes(b"\x00")

    lapped_samples = np.stack(
        (tonal[:96], np.roll(tonal[:96], 13)),
        axis=1,
    )
    for density in ("fixed", "adaptive"):
        encoded = encode_lapped_stream(
            lapped_samples,
            48_000,
            coefficients_per_frame=8,
            half_window=32,
            band_count=4,
            entropy_backend="bounded",
            transform_backend="fixed",
            density_backend=density,
        )
        (lapped_directory / f"{density}_density.rsc").write_bytes(
            encoded.payload
        )
        packeted = encode_lapped_packet_stream(
            lapped_samples,
            48_000,
            coefficients_per_frame=8,
            packet_frames=64,
            half_window=32,
            band_count=4,
            density_backend=density,
        )
        (
            lapped_packet_directory / f"{density}_density.lps"
        ).write_bytes(packeted.payload)
    transform_packeted = encode_lapped_transform_packet_stream(
        lapped_samples,
        48_000,
        coefficients_per_frame=8,
        packet_frames=64,
        half_window=32,
        band_count=4,
    )
    (lapped_packet_directory / "transform_boundary.lps").write_bytes(
        transform_packeted.payload
    )
    compact_packeted = encode_lapped_compact_packet_stream(
        lapped_samples,
        48_000,
        coefficients_per_frame=8,
        packet_frames=64,
        half_window=32,
        band_count=4,
    )
    (lapped_compact_directory / "single_owner.lps").write_bytes(
        compact_packeted.payload
    )


if __name__ == "__main__":
    main()
