"""Freeze the R-271 S17 PCM-only controls before codec implementation.

This evidence generator is never imported by the S17 proposer.  It writes
immutable WAV inputs and a machine manifest; the encoder receives only PCM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import wave

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "corpus" / "r271-s17-controls-v1"
BASIS_MANIFEST = ROOT / "experiments" / "fixtures" / "r215_cosine_basis_family.json"
SAMPLE_RATE = 16_000
MASK32 = (1 << 32) - 1
RATIOS_Q20 = (1_048_576, 1_482_910, 1_816_164, 2_344_686,
              2_774_518, 3_294_198, 3_780_501, 4_323_715)
EXTERNAL_INPUTS = (
    ("ebu-vibrato-gong", ROOT / "artifacts" / "corpus" / "prepared-r111"
     / "ebu-vibrato-gong.wav", "314210d30b03d67e4f923f1584d1bb30f548e39abecf717a63ce837e31b54187"),
    ("ebu-grand-piano", ROOT / "artifacts" / "corpus" / "prepared-r111"
     / "ebu-grand-piano.wav", "7141951e68eac8533d3a78065cc3036cdd2f13025d6c0bcb98b79d804d31629c"),
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def pcm_bytes(samples: np.ndarray) -> bytes:
    return np.ascontiguousarray(samples, dtype="<i2").tobytes()


def pcm16(values: np.ndarray) -> np.ndarray:
    rounded = np.rint(values)
    if np.any(rounded < -32768.0) or np.any(rounded > 32767.0):
        raise RuntimeError("R-271 control generation would clip PCM16")
    return rounded.astype(np.int16)


def div_even(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    increment = remainder > denominator - remainder
    increment |= remainder == denominator - remainder and bool(quotient & 1)
    return sign * (quotient + int(increment))


def write_wav(path: Path, samples: np.ndarray) -> None:
    payload = pcm_bytes(samples)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(payload)


def frozen_basis() -> np.ndarray:
    document = json.loads(BASIS_MANIFEST.read_text(encoding="utf-8"))
    row = next(item for item in document["tables"] if item["length"] == 256)
    basis = np.asarray(row["samples"], dtype=np.int16)
    if sha256(pcm_bytes(basis)) != row["pcm16le_sha256"]:
        raise RuntimeError("R-271 periodic Basis identity mismatch")
    return basis


def periodic_sample(basis: np.ndarray, phase: int) -> int:
    position = (phase & MASK32) * int(basis.size)
    left_index = position >> 32
    fraction = (position >> 16) & 0xFFFF
    right_index = (left_index + 1) % int(basis.size)
    numerator = (int(basis[left_index]) * (65536 - fraction)
                 + int(basis[right_index]) * fraction + 32768)
    return numerator >> 16


def exact_language_control(seconds: int = 12) -> np.ndarray:
    """Scalar integer control using the frozen planned render arithmetic."""

    basis = frozen_basis()
    count = SAMPLE_RATE * seconds
    phases = [0x10203040 + index * 0x13579BDF for index in range(8)]
    base_step = div_even(173 * (1 << 32), SAMPLE_RATE)
    steps = [div_even(base_step * ratio, 1 << 20) for ratio in RATIOS_Q20]
    gains = (4200, 3100, 2500, 1900, 1450, 1100, 820, 610)
    output = np.empty(count, dtype=np.int16)
    for sample in range(count):
        total = 0
        for mode in range(8):
            total += div_even(periodic_sample(basis, phases[mode]) * gains[mode], 1 << 15)
            phases[mode] = (phases[mode] + steps[mode]) & MASK32
        if not -32768 <= total <= 32767:
            raise RuntimeError("P0 exact control exceeded PCM16")
        output[sample] = total
    return output


def add_instance(output: np.ndarray, *, start_s: float, duration_s: float,
                 base_hz: float, gain: float, phase_shift: float,
                 mutation: int = 0, ratios: np.ndarray | None = None,
                 relative: np.ndarray | None = None,
                 decay: np.ndarray | None = None,
                 phase0: np.ndarray | None = None) -> tuple[int, int]:
    start = int(round(start_s * SAMPLE_RATE))
    count = int(round(duration_s * SAMPLE_RATE))
    if start < 0 or count <= 0 or start + count > output.size:
        raise RuntimeError("R-271 instance would be truncated")
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    common_scale = 1.0 + 0.0045 * np.sin(2.0 * np.pi * 0.071 * t)
    common_scale += 0.0018 * (t / max(duration_s, 1e-9)) ** 2
    common_gain = np.sin(np.pi * np.minimum(t / 0.035, 1.0) / 2.0) ** 2
    common_gain *= np.exp(-t / (duration_s * 0.82))
    relative = (np.asarray((1.0, .74, .58, .46, .35, .27, .20, .15))
                if relative is None else relative)
    decay = (np.asarray((28., 23., 19., 16., 13., 11., 9., 7.5))
             if decay is None else decay)
    ratios = (np.asarray(RATIOS_Q20, dtype=np.float64) / (1 << 20)
              if ratios is None else ratios)
    phase0 = (np.asarray((.11, .83, 1.47, 2.21, 2.93, 3.71, 4.49, 5.33))
              if phase0 is None else phase0)
    rendered = np.zeros(count, dtype=np.float64)
    for mode, ratio in enumerate(ratios):
        frequency = base_hz * ratio * common_scale
        phase = phase_shift * ratio + phase0[mode]
        phase += 2.0 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
        local_decay = decay[mode]
        local_phase = phase
        if mutation and mode == 5:
            local_decay *= 0.55
            local_phase = phase + np.pi * mutation
        envelope = relative[mode] * np.exp(-t / local_decay) * common_gain
        rendered += envelope * np.cos(local_phase)
    output[start:start + count] += gain * rendered
    return start, count


def held_out_modal() -> np.ndarray:
    output = np.zeros(SAMPLE_RATE * 180, dtype=np.float64)
    for args in ((0., 54., 171., 5100., .23), (41., 62., 173., 4200., 1.17),
                 (91., 47., 168., 4700., 2.03), (126., 54., 176., 3900., 2.71)):
        add_instance(output, start_s=args[0], duration_s=args[1], base_hz=args[2],
                     gain=args[3], phase_shift=args[4])
    rng = np.random.default_rng(0x271517)
    output += rng.normal(0.0, 13.0, output.size)
    return pcm16(output)


def auditor_holdout(seed: int) -> tuple[np.ndarray, dict]:
    """Generate the single post-proposer-freeze admission control."""

    rng = np.random.default_rng(seed)
    ratios = np.concatenate(([1.0], np.sort(rng.uniform(1.27, 4.63, 7))))
    relative = np.concatenate(([1.0], np.sort(rng.uniform(.12, .82, 7))[::-1]))
    decay = np.sort(rng.uniform(7.0, 31.0, 8))[::-1]
    phase0 = rng.uniform(0.0, 2.0 * np.pi, 8)
    output = np.zeros(SAMPLE_RATE * 180, dtype=np.float64)
    instances = []
    for index in range(4):
        duration = float(rng.uniform(48.0, 55.0))
        start = 41.0 * index
        base = float(rng.uniform(149.0, 211.0))
        gain = float(rng.uniform(1500.0, 2200.0))
        shift = float(rng.uniform(0.0, 2.0 * np.pi))
        effective_start, effective_count = add_instance(
            output, start_s=start, duration_s=duration, base_hz=base,
            gain=gain, phase_shift=shift, ratios=ratios,
            relative=relative, decay=decay, phase0=phase0)
        instances.append({"start_sample": effective_start,
                          "duration_samples": effective_count,
                          "base_hz": base, "gain": gain,
                          "phase_shift": shift})
    noise_bound = float(rng.uniform(9.0, 19.0))
    output += rng.uniform(-noise_bound, noise_bound, output.size)
    metadata = {"seed_u64": seed, "ratios_q20": [int(round(x * (1 << 20))) for x in ratios],
                "instances": instances, "noise_bound": noise_bound}
    return pcm16(output), metadata


def independent_drift() -> np.ndarray:
    count = SAMPLE_RATE * 180
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    ratios = np.asarray(RATIOS_Q20, dtype=np.float64) / (1 << 20)
    output = np.zeros(count, dtype=np.float64)
    for mode, ratio in enumerate(ratios):
        rate = .021 + .013 * mode
        depth = .002 + .0011 * mode
        frequency = 171.0 * ratio * (1.0 + depth * np.sin(2 * np.pi * rate * t + mode))
        phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
        output += (3200.0 / (1.0 + .55 * mode)) * np.cos(phase + .31 * mode)
    return pcm16(output)


def crossing_fields() -> np.ndarray:
    count = SAMPLE_RATE * 12
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    output = np.zeros(count, dtype=np.float64)
    for sign, origin, phase0 in ((1.0, 120.0, .2), (-1.0, 260.0, 1.1)):
        base = origin + sign * 105.0 * t / 12.0
        for mode, ratio in enumerate((1.0, 1.47, 2.19, 2.83)):
            phase = 2 * np.pi * np.cumsum(base * ratio) / SAMPLE_RATE
            output += 1700.0 / (mode + 1) * np.cos(phase + phase0 * ratio)
    return pcm16(output)


def close_beating() -> np.ndarray:
    count = SAMPLE_RATE * 12
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    output = 6500.0 * np.cos(2 * np.pi * 611.0 * t + .23)
    output += 6450.0 * np.cos(2 * np.pi * 612.35 * t + 2.71)
    output += 1800.0 * np.cos(2 * np.pi * 917.2 * t + 1.17)
    return pcm16(output)


def phase_decay_mutation() -> np.ndarray:
    output = np.zeros(SAMPLE_RATE * 12, dtype=np.float64)
    add_instance(output, start_s=0., duration_s=5.8, base_hz=174., gain=4300.,
                 phase_shift=.41)
    add_instance(output, start_s=6., duration_s=6., base_hz=174., gain=4300.,
                 phase_shift=.41, mutation=1)
    return pcm16(output)


def overlap_contamination() -> np.ndarray:
    output = np.zeros(SAMPLE_RATE * 12, dtype=np.float64)
    add_instance(output, start_s=0., duration_s=10., base_hz=169., gain=3600.,
                 phase_shift=.7)
    add_instance(output, start_s=3., duration_s=9., base_hz=233., gain=3100.,
                 phase_shift=2.2)
    rng = np.random.default_rng(0xBAD271)
    output += rng.normal(0.0, 90.0, output.size)
    for second, value in ((1.25, 11000.0), (5.5, -14000.0), (9.75, 9000.0)):
        output[int(round(second * SAMPLE_RATE))] += value
    return pcm16(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--auditor-holdout-seed", type=int)
    arguments = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if arguments.auditor_holdout_seed is not None:
        if not 0 <= arguments.auditor_holdout_seed < (1 << 64):
            raise ValueError("holdout seed must be an unsigned 64-bit integer")
        samples, private = auditor_holdout(arguments.auditor_holdout_seed)
        path = OUTPUT / "p1-auditor-holdout-180s.wav"
        write_wav(path, samples)
        receipt = {"schema": "resonith-r271-s17-auditor-holdout-1",
                   "generator_sha256": sha256(Path(__file__).read_bytes()),
                   "seed_u64": arguments.auditor_holdout_seed,
                   "private_generation_receipt": private,
                   "sample_rate": SAMPLE_RATE, "sample_count": int(samples.size),
                   "pcm16_payload_sha256": sha256(pcm_bytes(samples)),
                   "wav_sha256": sha256(path.read_bytes()), "wav_bytes": path.stat().st_size}
        receipt_path = OUTPUT / "p1-auditor-holdout-180s.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(receipt_path)
        print(sha256(receipt_path.read_bytes()))
        return 0
    external_rows = []
    for input_id, path, expected_wav_sha256 in EXTERNAL_INPUTS:
        payload = path.read_bytes()
        if sha256(payload) != expected_wav_sha256:
            raise RuntimeError(f"R-271 external input identity mismatch: {input_id}")
        with wave.open(str(path), "rb") as handle:
            pcm = handle.readframes(handle.getnframes())
            external_rows.append({"id": input_id, "path": path.as_posix(),
                                  "wav_sha256": expected_wav_sha256,
                                  "pcm_payload_sha256": sha256(pcm),
                                  "sample_rate": handle.getframerate(),
                                  "channels": handle.getnchannels(),
                                  "sample_width": handle.getsampwidth(),
                                  "frames": handle.getnframes(),
                                  "wav_bytes": len(payload)})
    controls = (
        ("p0-exact-language-12s", exact_language_control()),
        ("p1-held-out-modal-180s", held_out_modal()),
        ("n1-independent-drift-180s", independent_drift()),
        ("n2-crossing-fields-12s", crossing_fields()),
        ("n3-close-beating-12s", close_beating()),
        ("n4-phase-decay-mutation-12s", phase_decay_mutation()),
        ("n5-overlap-contamination-12s", overlap_contamination()),
    )
    rows = []
    for control_id, samples in controls:
        path = OUTPUT / f"{control_id}.wav"
        write_wav(path, samples)
        rows.append({"id": control_id, "path": path.as_posix(),
                     "sample_rate": SAMPLE_RATE, "sample_count": int(samples.size),
                     "pcm16_payload_sha256": sha256(pcm_bytes(samples)),
                     "wav_sha256": sha256(path.read_bytes()),
                     "wav_bytes": path.stat().st_size})
    report = {"schema": "resonith-r271-s17-controls-1",
              "generator_sha256": sha256(Path(__file__).read_bytes()),
              "basis_manifest_sha256": sha256(BASIS_MANIFEST.read_bytes()),
              "basis_256_pcm16le_sha256":
                  "da8b1b6cfbb6840806397707bec13084a272d2746628f0e61acd96cd4c372e7c",
              "proposer_input": "PCM-only; this generator and its parameters are forbidden imports",
              "external_inputs": external_rows,
              "controls": rows}
    manifest = OUTPUT / "r271_s17_controls_v1.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(manifest)
    print(sha256(manifest.read_bytes()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
