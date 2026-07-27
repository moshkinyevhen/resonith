# Gemini Byte-Pattern A/B Gate — 2026-07-27

Status: **MEASURED PROPOSER EVIDENCE — NOT A CODEC CLAIM**

Decision: R-152.

## Question

Can Gemini 3.6 Flash find exact reusable pattern transformations more
effectively when it receives byte sequences rather than audio?

## Method

Gemini received numbered PCM16LE blocks as hexadecimal text. It received no
audio MIME, transcript, source label, or musical description. The prompt
defined the same first finite language used by native Foundry:

- every ordered unequal block pair;
- every circular source offset;
- signed constant Q1.15 gain;
- signed linearly interpolated Q1.15 start/end gain;
- fixed round-half-away-from-zero synthesis;
- a per-case normalized squared-error ceiling.

The RTX 2080 Super CUDA backend evaluated the complete declared lattice. Every
Gemini proposal was then checked against the native fixed-point result.

## Inputs

| Case | Blocks | Samples per block | SHA-256 |
|---|---:|---:|---|
| synthetic known laws | 6 | 16 | `99625d2ee92ef7418ab76c46f5e6b54d69636a4060b1b5e77a2717360c0daca9` |
| EBU female speech bytes | 12 | 64 | `3d92951c7d9e448ad625e1b02d4321217d71b31c02da592b7382ddbc5390738c` |

The synthetic case contains exact circular phase, counterphase, constant gain,
and linear-envelope relationships. The speech case is an authorized prepared
R-111 corpus excerpt beginning at frame 61,440.

## Results

| Metric | Synthetic | EBU speech |
|---|---:|---:|
| Native eligible relationships | 24 | 172 |
| Gemini proposals | 12 | 12 |
| Gemini valid-index proposals | 12 | 12 |
| Gemini eligible relationships | 8 | 3 |
| Eligible relationship precision | 66.67% | 25.00% |
| Eligible relationship recall | 33.33% | 1.744% |
| Best-target recall | 100.00% | 0.00% |
| Exact Q15 parameter rate on eligible proposals | 0.00% | 0.00% |
| Native CUDA wall time | 0.2559 s | 0.2130 s |

Gemini request totals:

- model: `models/gemini-3.6-flash`;
- request payload: 6,114 bytes;
- input tokens: 3,533;
- output tokens: 2,119;
- thought tokens: 30,211;
- total tokens: 35,863;
- wall time: 129.3420 seconds.

For the real speech case, Gemini was approximately 607 times slower than the
native CUDA evaluation while recalling 1.744% of quality-eligible
relationships and none of the per-target optima.

## Decision

Gemini SHALL NOT be the primary byte-pattern, phase, or fixed-point transform
finder. It is neither complete nor numerically exact on this bounded test.

Gemini remains eligible for:

- coarse structure and change-ledger proposals;
- suggesting useful duration or representation families;
- scheduling complete Foundry tiles;
- proposing a new transform family for a later bounded experiment.

It SHALL NOT:

- establish waveform equality;
- supply trusted fixed-point parameters;
- prune the declared Foundry candidate set;
- replace native decoder-in-loop RDO or Truth correction.

The machine-readable result is
[`experiments/results/gemini_byte_pattern_r152_2026-07-27.json`](../../experiments/results/gemini_byte_pattern_r152_2026-07-27.json).
