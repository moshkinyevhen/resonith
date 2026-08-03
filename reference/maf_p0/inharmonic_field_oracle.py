"""Independent scalar IMF1/IMU1 packer and model decoder for R-271 S17."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import struct

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MASK32 = (1 << 32) - 1

@dataclass(frozen=True)
class Mode:
    ratio_q20: int; phase_q32: int; relative_gain_q15: int; decay_q31: int

@dataclass(frozen=True)
class Knot:
    offset: int; common_step_q32: int; common_gain_q15: int

@dataclass(frozen=True)
class Instance:
    start: int; duration: int; time_shift_q32: int; knots: tuple[Knot, ...]

def div_even(n: int, d: int) -> int:
    sign = -1 if n < 0 else 1; q, r = divmod(abs(n), d)
    return sign * (q + int(r > d - r or (r == d - r and q & 1)))

def frozen_basis() -> np.ndarray:
    path = ROOT / "experiments/fixtures/r215_cosine_basis_family.json"
    row = next(x for x in json.loads(path.read_text(encoding="utf-8"))["tables"] if x["length"] == 256)
    return np.asarray(row["samples"], dtype=np.int16)

def pack_imf(rate: int, sample_count: int, modes: tuple[Mode, ...],
             instances: tuple[Instance, ...], truth: bytes = b"") -> bytes:
    knots = tuple(k for x in instances for k in x.knots); size = 96 + 16 + 16 * len(modes) + 32 * len(instances) + 16 * len(knots) + len(truth)
    out = bytearray(size); struct.pack_into("<4sBBHIIHHHHIIQQQQQQQQ", out, 0, b"IMF1", 1, 0, 96, rate, sample_count, 1,
        len(modes), len(instances), len(knots), len(truth), 0, 96, 112, 112 + 16 * len(modes),
        112 + 16 * len(modes) + 32 * len(instances), size - len(truth), size,
        sum(x.duration * len(modes) for x in instances), 0)
    struct.pack_into("<HHHHQ", out, 96, 0, 0, len(modes), 0, 0)
    for i, m in enumerate(modes): struct.pack_into("<IIHHI", out, 112 + 16 * i, m.ratio_q20, m.phase_q32, m.relative_gain_q15, 0, m.decay_q31)
    ip = 112 + 16 * len(modes); kp = ip + 32 * len(instances); first = 0
    for i, x in enumerate(instances):
        struct.pack_into("<HHHHIIIIQ", out, ip + 32 * i, 0, first, len(x.knots), 0, x.start, x.duration, x.time_shift_q32, 0, 0)
        for k in x.knots: struct.pack_into("<IIHHI", out, kp + 16 * first, k.offset, k.common_step_q32, k.common_gain_q15, 0, 0); first += 1
    if truth: out[-len(truth):] = truth
    return bytes(out)

def expand_imu(payload: bytes) -> bytes:
    h = struct.unpack_from("<4sBBHIIHHHHIIQQQQQQQQ", payload); rate, samples, mode_n, inst_n = h[4], h[5], h[7], h[8]
    mode_off, inst_off, knot_off, truth_off, truth_n = h[13], h[14], h[15], h[16], h[10]
    modes = [struct.unpack_from("<IIHHI", payload, mode_off + 16 * i) for i in range(mode_n)]
    records, knots = [], []
    for i in range(inst_n):
        _, fk, kc, _, start, duration, shift, _, _ = struct.unpack_from("<HHHHIIIIQ", payload, inst_off + 32 * i)
        source_knots = [struct.unpack_from("<IIHHI", payload, knot_off + 16 * (fk + k)) for k in range(kc)]
        for ratio, phase, relative, _, decay in modes:
            first = len(knots); folded = (phase + div_even(shift * ratio, 1 << 20)) & MASK32
            records.append((start, duration, first, kc, relative, 0, folded, decay, 0))
            knots.extend((off, div_even(step * ratio, 1 << 20), gain, 0, 0) for off, step, gain, _, _ in source_knots)
    size = 64 + 32 * len(records) + 16 * len(knots) + truth_n; out = bytearray(size)
    struct.pack_into("<4sBBHIIIIIIQQQQ", out, 0, b"IMU1", 1, 0, 64, rate, samples, len(records), len(knots), truth_n, 0,
                     64, 64 + 32 * len(records), size - truth_n, size)
    for i, row in enumerate(records): struct.pack_into("<IIHHHHIIQ", out, 64 + 32 * i, *row)
    kp = 64 + 32 * len(records)
    for i, row in enumerate(knots): struct.pack_into("<IIHHI", out, kp + 16 * i, *row)
    if truth_n: out[-truth_n:] = payload[truth_off:truth_off + truth_n]
    return bytes(out)

def _periodic(basis: np.ndarray, phase: int) -> int:
    position = (phase & MASK32) * basis.size; left = position >> 32; fraction = (position >> 16) & 65535
    weighted = int(basis[left]) * (65536 - fraction) + int(basis[(left + 1) % basis.size]) * fraction + 32768
    return weighted // 65536 if weighted >= 0 else -((-weighted + 65535) // 65536)

def _phase_advance(length: int, a: int, b: int) -> int:
    n = (b - a) * length * (length - 1); sign = -1 if n < 0 else 1
    return length * a + sign * ((abs(n) + length) // (2 * length))

def _round_away(n: int, d: int) -> int:
    return (-1 if n < 0 else 1) * ((abs(n) + d // 2) // d)

def _views(payload: bytes) -> tuple[int, int, list[tuple], int]:
    direct = payload[:4] == b"IMU1"
    if direct:
        _, _, _, _, rate, samples, count, _, _, _, ro, ko, _, _ = struct.unpack_from("<4sBBHIIIIIIQQQQ", payload)
        return rate, samples, [(*struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[:2],
            struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[2], struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[3],
            1 << 20, struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[6], struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[7],
            struct.unpack_from("<IIHHHHIIQ", payload, ro + 32 * i)[4]) for i in range(count)], ko
    h = struct.unpack_from("<4sBBHIIHHHHIIQQQQQQQQ", payload); rate, samples, modes, instances, mo, io, ko = h[4], h[5], h[7], h[8], h[13], h[14], h[15]
    mode_rows = [struct.unpack_from("<IIHHI", payload, mo + 16 * i) for i in range(modes)]; views=[]
    for i in range(instances):
        _, fk, kc, _, start, duration, shift, _, _ = struct.unpack_from("<HHHHIIIIQ", payload, io + 32 * i)
        for ratio, phase, relative, _, decay in mode_rows: views.append((start, duration, fk, kc, ratio, (phase + div_even(shift * ratio, 1 << 20)) & MASK32, decay, relative))
    return rate, samples, views, ko

def decode_model(payload: bytes, basis: np.ndarray | None = None) -> tuple[int, np.ndarray]:
    basis = frozen_basis() if basis is None else np.asarray(basis, dtype=np.int16); rate, samples, views, ko = _views(payload); output = np.zeros(samples, np.int16)
    state = [[v, 0, v[5], v[7] << 16] for v in views]
    for sample in range(samples):
        total = 0
        for item in state:
            v, interval, origin, decay_state = item; start, duration, first, count, ratio, _, decay, _ = v
            if not start <= sample < start + duration: continue
            local = sample - start
            def knot(i): return struct.unpack_from("<IIHHI", payload, ko + 16 * (first + i))
            while interval + 1 < count - 1 and local >= knot(interval + 1)[0]:
                a, b = knot(interval), knot(interval + 1); sa = a[1] if payload[:4] == b"IMU1" else div_even(a[1] * ratio, 1 << 20); sb = b[1] if payload[:4] == b"IMU1" else div_even(b[1] * ratio, 1 << 20)
                origin = (origin + _phase_advance(b[0] - a[0], sa, sb)) & MASK32; interval += 1
            a, b = knot(interval), knot(interval + 1); sa = a[1] if payload[:4] == b"IMU1" else div_even(a[1] * ratio, 1 << 20); sb = b[1] if payload[:4] == b"IMU1" else div_even(b[1] * ratio, 1 << 20)
            phase = (origin + (local-a[0])*sa + _round_away((sb-sa)*(local-a[0])*(local-a[0]-1), 2*(b[0]-a[0]))) & MASK32
            gain = a[2] + div_even((b[2]-a[2])*(local-a[0]), b[0]-a[0]); total += div_even(_periodic(basis, phase)*decay_state*gain, 1 << 46)
            item[1], item[2], item[3] = interval, origin, div_even(decay_state * decay, 1 << 31)
        if not -32768 <= total <= 32767: raise ValueError("model clipping")
        output[sample] = total
    return rate, output
