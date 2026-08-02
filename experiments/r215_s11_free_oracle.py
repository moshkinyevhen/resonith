#!/usr/bin/env python3
"""Reproduce the R-215 in-language persistent-partial lower bound."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

from reference.maf_p0.causal_basis_field import (
    encode_causal_basis_field_from_mft1,
)
from reference.maf_p0.causal_basis_truth_candidate import (
    _pack_complete,
    decode_causal_basis_truth_candidate,
)
from reference.maf_p0.lapped_oracle import encode_lapped_stream
from reference.maf_p0.maf_typed import (
    MafBasis,
    MafBasisWarpInstance,
    MafMix,
    WARP_ONE_Q16,
    _warp_source_position_q16,
    pack_maf_typed,
)
from reference.maf_p0.native_core import NativeMain0Decoder
from reference.maf_p0.wav_io import write_pcm16_channels


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASIS = ROOT / "experiments/fixtures/r215_cosine_basis_family.json"
DEFAULT_NATIVE = ROOT / "build/cpp23-clang22-ninja/libresonith_core_shared.dll"
DEFAULT_OUTPUT = ROOT / "artifacts/r215-s11-free-oracle"
DEFAULT_REPORT = ROOT / "experiments/results/r215_s11_free_oracle_2026-08-02.json"
SAMPLE_RATE = 48_000
TOTAL_FRAMES = 12 * SAMPLE_RATE
MAX_SEGMENT_FRAMES = 60_000

# Fixed-point source laws are the complete free-oracle input. Frequencies are
# Q20 hertz, phases are unsigned turns, and gains are signed Q15 amplitudes.
PATH_LAWS = (
    (0, TOTAL_FRAMES, 220 << 20, 238 << 20, 9000, 7000, 558_345_748),
    (
        SAMPLE_RATE,
        TOTAL_FRAMES - SAMPLE_RATE // 2,
        331 << 20,
        302 << 20,
        6500,
        8200,
        1_589_137_900,
    ),
    (
        2 * SAMPLE_RATE,
        TOTAL_FRAMES,
        447 << 20,
        505 << 20,
        5200,
        3900,
        3_049_426_780,
    ),
    (
        SAMPLE_RATE // 2,
        9 * SAMPLE_RATE,
        733 << 20,
        690 << 20,
        3800,
        2600,
        3_908_420_239,
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _divide_nearest_even(numerator: int, denominator: int) -> int:
    """Round one signed rational to nearest, with exact ties to even."""

    if denominator <= 0:
        raise ValueError("rounding denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    complement = denominator - remainder
    if remainder > complement or (remainder == complement and quotient & 1):
        quotient += 1
    return sign * quotient


def _lerp_integer(start: int, end: int, offset: int, duration: int) -> int:
    return start + _divide_nearest_even((end - start) * offset, duration)


def _frequency_step_q16(frequency_hz_q20: int, basis_samples: int) -> int:
    return _divide_nearest_even(
        frequency_hz_q20 * basis_samples * WARP_ONE_Q16,
        SAMPLE_RATE << 20,
    )


def _phase_position_q16(phase_turn_u32: int, basis_samples: int) -> int:
    return _divide_nearest_even(
        (phase_turn_u32 & 0xFFFF_FFFF) * basis_samples * WARP_ONE_Q16,
        1 << 32,
    ) % (basis_samples * WARP_ONE_Q16)


def _one_past_position_q16(
    start_position_q16: int,
    start_step_q16: int,
    end_step_q16: int,
    sample_count: int,
    basis_period_q16: int,
) -> int:
    """Carry phase after the last rendered sample without adding an anchor."""

    linear = end_step_q16 != start_step_q16
    if not linear:
        result = start_position_q16 + sample_count * start_step_q16
    else:
        last_position = _warp_source_position_q16(
            start_position_q16,
            start_step_q16,
            end_step_q16,
            True,
            sample_count - 1,
            sample_count,
        )
        result = last_position + end_step_q16
    return result % basis_period_q16


def _load_basis(path: Path, basis_length: int) -> tuple[int, ...]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if (
        record.get("schema") != "resonith-r215-cosine-basis-family-1"
        or record.get("length_order") != [16, 32, 64, 128, 256]
    ):
        raise ValueError("unexpected R-215 Basis-family schema")
    matches = tuple(
        row for row in record["tables"]
        if int(row["length"]) == basis_length
    )
    if len(matches) != 1:
        raise ValueError("R-215 Basis length is absent or duplicated")
    table = matches[0]
    samples = tuple(int(value) for value in table["samples"])
    payload = np.asarray(samples, dtype="<i2").tobytes()
    if (
        len(samples) != int(table["length"])
        or _sha256_bytes(payload) != table["pcm16le_sha256"]
    ):
        raise ValueError("R-215 Basis identity mismatch")
    return samples


def _build_predictor(basis: tuple[int, ...]) -> tuple[bytes, int]:
    basis_period_q16 = len(basis) * WARP_ONE_Q16
    instances = []
    for emitter_id, law in enumerate(PATH_LAWS):
        start, end, f0_q20, f1_q20, g0_q15, g1_q15, phase_u32 = law
        duration = end - start
        offset = 0
        source_position = _phase_position_q16(phase_u32, len(basis))
        while offset < duration:
            count = min(MAX_SEGMENT_FRAMES, duration - offset)
            next_offset = offset + count
            start_frequency = _lerp_integer(
                f0_q20, f1_q20, offset, duration
            )
            end_frequency = _lerp_integer(
                f0_q20, f1_q20, next_offset, duration
            )
            start_gain = _lerp_integer(g0_q15, g1_q15, offset, duration)
            end_gain = _lerp_integer(g0_q15, g1_q15, next_offset, duration)
            start_step = _frequency_step_q16(start_frequency, len(basis))
            end_step = _frequency_step_q16(end_frequency, len(basis))
            instances.append(
                MafBasisWarpInstance(
                    emitter_id=emitter_id,
                    basis_id=0,
                    start=start + offset,
                    sample_count=count,
                    source_position_q16=source_position,
                    source_step_q16=start_step,
                    gain_q15=start_gain,
                    circular=True,
                    end_source_step_q16=(
                        end_step if end_step != start_step else None
                    ),
                    end_gain_q15=(end_gain if end_gain != start_gain else None),
                )
            )
            source_position = _one_past_position_q16(
                source_position,
                start_step,
                end_step,
                count,
                basis_period_q16,
            )
            offset = next_offset

    predictor = pack_maf_typed(
        sample_rate=SAMPLE_RATE,
        total_frames=TOTAL_FRAMES,
        render_quantum=4096,
        output_channels=1,
        emitter_count=len(PATH_LAWS),
        mixes=(
            MafMix(
                0,
                TOTAL_FRAMES,
                (tuple(32767 for _ in PATH_LAWS),),
            ),
        ),
        bases=(MafBasis(basis),),
        basis_warp_instances=tuple(instances),
        declared_operations_per_frame=256,
    )
    return predictor, len(instances)


def _artifact(path: Path) -> dict[str, object]:
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-core", type=Path, default=DEFAULT_NATIVE)
    parser.add_argument("--basis", type=Path, default=DEFAULT_BASIS)
    parser.add_argument(
        "--basis-length",
        type=int,
        choices=(16, 32, 64, 128, 256),
        default=16,
    )
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    arguments = parser.parse_args()

    native_path = arguments.native_core.resolve()
    basis_path = arguments.basis.resolve()
    output = arguments.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    basis = _load_basis(basis_path, arguments.basis_length)
    mft1, placement_count = _build_predictor(basis)
    decoder = NativeMain0Decoder(native_path)
    source = decoder.decode_maf_typed(mft1).samples
    zero = np.zeros_like(source)
    lapped_options = {
        "coefficients_per_frame": 64,
        "half_window": 512,
        "band_count": 24,
        "entropy_backend": "bounded",
        "transform_backend": "fixed",
        "density_backend": "adaptive",
        "native_analyzer": decoder,
        "native_decoder": decoder,
    }
    zero_truth = encode_lapped_stream(zero, SAMPLE_RATE, **lapped_options)
    direct_truth = encode_lapped_stream(source, SAMPLE_RATE, **lapped_options)
    transport = encode_causal_basis_field_from_mft1(mft1)
    cbf_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=SAMPLE_RATE,
        predictor_type="CBF1",
        predictor_payload=transport.cbf_payload,
        residual_payload=zero_truth.payload,
    )
    mft1_complete = _pack_complete(
        source_shape=source.shape,
        sample_rate=SAMPLE_RATE,
        predictor_type="MFT1",
        predictor_payload=mft1,
        residual_payload=zero_truth.payload,
    )
    decoded_rate, decoded = decode_causal_basis_truth_candidate(
        cbf_complete,
        native_decoder=decoder,
    )
    if decoded_rate != SAMPLE_RATE or not np.array_equal(source, decoded):
        raise RuntimeError("R-215 free-oracle independent decode differs")

    paths = {
        "basis.pcm16le": np.asarray(basis, dtype="<i2").tobytes(),
        "predictor.mft1": mft1,
        "predictor.cbf1": transport.cbf_payload,
        "zero-truth.mri1": zero_truth.payload,
        "candidate-cbf1.resonith": cbf_complete,
        "candidate-mft1.resonith": mft1_complete,
        "direct-truth.resonith": direct_truth.payload,
    }
    for name, payload in paths.items():
        (output / name).write_bytes(payload)
    write_pcm16_channels(output / "source.wav", SAMPLE_RATE, source)
    write_pcm16_channels(output / "candidate-decoded.wav", SAMPLE_RATE, decoded)
    write_pcm16_channels(
        output / "direct-truth-decoded.wav",
        SAMPLE_RATE,
        direct_truth.reconstruction,
    )

    source_pcm = np.ascontiguousarray(source, dtype="<i2").tobytes()
    decoded_pcm = np.ascontiguousarray(decoded, dtype="<i2").tobytes()
    direct_error = source.astype(np.int64) - direct_truth.reconstruction.astype(
        np.int64
    )
    cbf_container_bytes = (
        len(cbf_complete) - len(transport.cbf_payload) - len(zero_truth.payload)
    )
    mft_container_bytes = len(mft1_complete) - len(mft1) - len(zero_truth.payload)
    command = (
        "python experiments/r215_s11_free_oracle.py "
        "--native-core build/cpp23-clang22-ninja/libresonith_core_shared.dll "
        "--basis experiments/fixtures/r215_cosine_basis_family.json "
        f"--basis-length {arguments.basis_length} "
        "--output-directory artifacts/r215-s11-free-oracle "
        "--report experiments/results/r215_s11_free_oracle_2026-08-02.json"
    )
    report = {
        "schema": "resonith-r215-s11-free-oracle-2",
        "status": "in-language representational lower bound only",
        "command": command,
        "generator": {
            "file": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": _sha256(Path(__file__).resolve()),
        },
        "runtime": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy": np.__version__,
        },
        "native_core": {
            "file": native_path.name,
            "sha256": _sha256(native_path),
        },
        "basis": {
            "manifest_file": str(basis_path.relative_to(ROOT)),
            "manifest_sha256": _sha256(basis_path),
            "sample_count": len(basis),
            "pcm16le_sha256": _sha256_bytes(
                np.asarray(basis, dtype="<i2").tobytes()
            ),
        },
        "fixed_mapping": {
            "rounding": "signed nearest; exact ties to even",
            "frequency_step_q16": (
                f"round_even(freq_hz_q20 * {len(basis)} * 2^16 / "
                "(48000 * 2^20))"
            ),
            "phase_position_q16": (
                f"round_even(phase_turn_u32 * {len(basis)} * 2^16 / "
                f"2^32) mod {len(basis) * WARP_ONE_Q16}"
            ),
            "split_carry": (
                "constant: start+N*step; linear: position(N-1)+end_step; "
                f"Euclidean modulo {len(basis) * WARP_ONE_Q16}"
            ),
        },
        "source_program": {
            "sample_rate": SAMPLE_RATE,
            "frames": TOTAL_FRAMES,
            "duration_seconds": TOTAL_FRAMES / SAMPLE_RATE,
            "path_laws": [list(row) for row in PATH_LAWS],
            "maximum_segment_frames": MAX_SEGMENT_FRAMES,
            "path_count": len(PATH_LAWS),
            "placement_count": placement_count,
            "static_mix_q15": [32767 for _ in PATH_LAWS],
        },
        "byte_ledger": {
            "cbf1_predictor_bytes": len(transport.cbf_payload),
            "mft1_predictor_bytes": len(mft1),
            "zero_truth_bytes": len(zero_truth.payload),
            "cbf1_container_bytes": cbf_container_bytes,
            "mft1_container_bytes": mft_container_bytes,
            "cbf1_complete_bytes": len(cbf_complete),
            "mft1_complete_bytes": len(mft1_complete),
            "direct_truth_bytes": len(direct_truth.payload),
            "cbf1_saving_bytes_vs_direct": (
                len(direct_truth.payload) - len(cbf_complete)
            ),
            "cbf1_ratio_vs_direct": len(cbf_complete) / len(direct_truth.payload),
        },
        "quality": {
            "cbf1_exact": True,
            "source_pcm_sha256": _sha256_bytes(source_pcm),
            "decoded_pcm_sha256": _sha256_bytes(decoded_pcm),
            "direct_truth_sse": int(np.sum(direct_error * direct_error)),
        },
        "transport_selected_kind": transport.selected_kind,
        "artifacts": {
            path.name: _artifact(path)
            for path in sorted(output.iterdir())
            if path.is_file()
        },
        "claim_boundary": (
            "passes only the <=85% exact in-language R-186 structural threshold; "
            "does not prove analyzer recovery, real-audio gain, Opus gain, or novelty"
        ),
    }
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
