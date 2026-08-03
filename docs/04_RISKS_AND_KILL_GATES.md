# Risks and kill-gates Resonith

Status: criteria - **ACCEPTED**; thresholds - **TARGET**.

## 1. Main ways to fail

1. Basis metadata eats up the savings of waveform.
2. The real timbre changes faster than the persistent basis suggests.
3. Source separation creates a remainder of almost the original complexity.
4. Sinusoidal tracks give phasiness/warble.
5. Stochastic predictor changes the recognizable texture.
6. Resonator state complicates seek and packet-loss recovery.
7. Dense polyphony exceeds bounded atom count.
8. Basis switching is audible.
9. Decoder turns out to be larger and heavier than Opus/xHE-AAC without sufficient gain.
10. Learned Perceptual layer is mistaken for objective fidelity.

## 2. Falsification sequence

### Gate A - periodic oracle

Compare:

```text
universal integer lifting residual
vs
TIMBRE_BASIS + absolute PHASE_TRACK + remaining lifting residual
```

If on isolated pitched material the net rate does not decrease by at least 20% when
equal to objective error, coherent hypothesis is frozen.

### Gate B — broad classical

Add multiple bases and Studio global tracking. If matched-MUSHRA gain
below 15% on broad classical after full overhead, do not build musical VM.

### Gate C — transient/stochastic ablation

Each family must give:

- at least 3% broad net gain, or
- minimum 10% on a predetermined significant class,

in the absence of a statistically significant artifact penalty.

### Gate D - small decoder

Main decoder must have bounded state, bounded atoms/sample and predictable
integer DSP workload. If the worst-case profile cannot be implemented on mobile
CPU/DSP without neural accelerator, complexity is reduced to the next gate.

### Gate E - revolution

Continue the standard proposal as frontier codec only if:

- at least 35% bitrate reduction on broad music/classical against the strongest
  applicable anchor when matched MUSHRA;
- competitive result on speech/general audio;
- absence of systematic phase, timbre and transient degradation;
- independent decoder and conformance vectors.

## 3. Metrics that cannot be masked

The report must show:

- share basis/event/innovation/checkpoint/FEC bits;
- active atoms per sample P50/P95/P99/max;
- MAC/sample and state bytes;
- random access cost;
- packet loss propagation;
- algorithmic delay;
- objective and subjective quality;
- each anchor separately;
- failed clips and worst decile, not only mean.

## 4. Rule of simplicity

A new mechanism is not included in Main if it:

- requires a separate entropy coder;
- creates a new incompatible state machine;
- does not compile into the existing acoustic ISA;
- gives only cosmetic gain;
- does not have a universal Innovation fallback;- worsens deterministic random access.

A bad idea is closed rather than saved by additional modes.

## 5. Resource-profile verdicts

One memory, time, GPU, or implementation-size ceiling MUST NOT serve as a
universal verdict on a codec hypothesis.

- Decoder bounds are normative and remain strict, small, deterministic, and
  suitable for the declared profile/level.
- Consumer-encoder bounds are product-tier admission requirements.
- Foundry-encoder bounds may be materially larger, but remain explicit,
  reproducible, fail-closed, and charged in the complete report.

Crossing a resource ceiling before a decodable candidate exists rejects only
that execution profile. A harness failure before codec execution supplies no
algorithm evidence. A hypothesis is closed as algorithm-negative on rate or
quality only after an actual decoded candidate loses its frozen complete-byte
or quality predicate. Correctness, conformance, security, portability,
decoder-work, random-access, clipping, and failure-behavior gates remain
independent reasons for admission rejection and are never weakened by this
resource taxonomy.

A failed transaction is never rerun with a retroactively raised ceiling or a
disclosed seed. Recovery requires a new audited generation. It may optimize
memory layout, stream or batch the same complete search, or use a separately
declared Foundry tier, but MUST NOT silently prune candidates or weaken decoder
bounds. The R-276 recovery map applies this rule to S11-S17.
