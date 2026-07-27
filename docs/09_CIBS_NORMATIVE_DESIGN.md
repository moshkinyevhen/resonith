# CIBS - Cached Integer Basis Synthesis

Date: 2026-07-26
Semantic contract status: **ACCEPTED**
Exact graph/weights/precisions: **NORMATIVE-DRAFT**

## 1. Purpose

CIBS reduces the cost of immutable acoustic Basis. Encoder transmits
quantized latent and optional small adapter; fixed integer graph once
synthesizes Basis, after which a regular MAF renderer reuses it.

\[
B^\star =
\operatorname{Clip}_{16}\left(
\operatorname{Synth}_{m}^{int}(z,A)
+ LIFT^{-1}(q_c)
\right).
\]

CIBS compresses the representation rather than generating output audio. Objective
correction \(q_c\) and universal waveform Innovation remain mandatory
fallbacks.

## 2. `CIBS_LATENT` payload

Logical fields:

```text
synth_model_id
target_basis_schema
latent_shape
latent_quantizer_id
latent_payload
adapter_present
adapter_descriptor
adapter_payload
correction_mode
correction_payload
expected_basis_hash
```

All payload bits are counted in the bitrate. `expected_basis_hash` is calculated
after correction and before commit in Basis Bank.

### 2.1 CIBS-0 Basis hash

The first executable contract uses SHA-256 over:

```text
u8 model_id_utf8_length
u32le basis_channels
u32le samples_per_channel
model_id_utf8
int16le basis_samples[channel-major]
```

`model_id` does not exceed 255 UTF-8 bytes. Hash does not replace transport integrity;
it proves that normative materialization gave the expected Basis.

## 3. Normative decoding

1. Check model ID, target shape and level limits.
2. Entropy-decode latent, adapter and correction in staging.
3. Execute fixed integer `Synth_model_id`.
4. Apply normative inverse-lifting correction.
5. Saturate in target Basis precision.
6. Calculate normative Basis hash.
7. If the hash matches, atomically commit immutable Basis.
8. If there is a discrepancy, do not change the state and wait for objective recovery/reset.

Atoms do not have access to latent, intermediate activations or adapter after
commit. They only see the finished Basis.

## 4. Integer graph envelope

Only allowed:

- int8/int16 constants and latents;
- profile-defined int32/int64 accumulators;
- fixed matrix/1D convolution;
- dyadic upsample;
- short FIR;
- fixed piecewise-linear activation;
- canonical right shift/round;
- saturate/clip;
- bounded low-rank adapter;
- inverse integer lifting correction.

Prohibited:

- arbitrary graph from bitstream;
- floating point;
- dynamic loop/recursion;
- attention with data-dependent unbounded memory;
- external/downloaded model;
- device-specific approximate math;
- per-sample CIBS execution.

## 5. Versioning

`synth_model_id` uniquely defines:

- graph topology;
- normative weights/biases;
- tensor shapes;
- quantization scales;
- rounding/saturation;
- output Basis schema;
- maximum operations and scratch memory.

Main-0 decoder MUST support `CIBS-0`. A new model requires a new one
capability/version entry; bitstream cannot silently replace weights.

## 6. Adapter

Adapter MAY set only profile-bounded low-rank delta:

\[
W'=W+UV^\top.
\]Rank, matrices, scale and target layers are limited by level. Adapter:

- included in bitrate;
- valid only during one `BASIS_SET`;
- does not change the global model;
- destroyed after materialization Basis;
- cannot change graph topology.

## 7. Correction and exactness

`correction_mode`:

- `NONE`;
- `LOSSY_LIFTING`;
- `EXACT_LIFTING`.

`EXACT_LIFTING` MUST allow bit-exact target Basis. Even exact Basis is not
provides lossless waveform without conventional waveform Innovation.

RDO selects CIBS only if:

\[
R_z+R_A+R_c+R_{events}
<
R_{\mathrm{raw/lifted\ basis}}
+ \Delta R_{\mathrm{waveform\ residual}}.
\]

## 8. Resource envelope

Each level specifies:

- maximum models;
- model ROM bytes;
- latent elements;
- adapter rank/bytes;
- output Basis elements;
- MAC/Basis;
- scratch bytes;
- correction bytes;
- CIBS creations/time interval;
- startup/checkpoint CIBS budget.

The first experimental target, not normative final:

| Parameter | **TARGET** |
|---|---:|
| Model ROM | no more than 256 KiB |
| Latent | 32–128 int8 elements |
| Output | 1–8 basis channels, 256–2048 int16 samples/channel |
| Graph depth | no more than 4 synthesis stages |
| Kernel width | no more than 7 |
| Compute | 0.25–2 M integer MAC/Basis |
| adapter | rank no more than 4 |

## 9. Random access

Checkpoint MUST either:

- repeat self-contained CIBS payload and materialize Basis; or
- contain objective materialized Basis payload.

The Reference decoder is not required to save CIBS activations between checkpoints.
Realtime profile MAY prohibit CIBS creation between allowed setup
boundaries.

## 10. Training and export

Training pipeline is non-standard and MAY use float, GPUs, large teachers
and arbitrary losses. Export is obliged:

1. quantize graph;
2. perform range analysis;
3. confirm integer kernel;
4. generate model hash;
5. go through cross-platform bit-exact vectors;
6. Measure full bit cost with corrections.

The quality of training can be improved without changing the bitstream only for now
normative `CIBS-0` weights are not frozen. After freeze new weights are obtained
new model ID.

## 11. Kill conditions of a specific model

Syntax CIBS remains, but a specific model version is rejected if:

- broad net gain less than 5%;
- pre-declared specialized gain is less than 12%;
- correction systematically returns more than 70% of raw Basis bits;
- CIBS increases waveform residual more than Basis saves;
- model does not provide bit-exact output;
- startup/ROM/scratch exceed level;
- OOD worst decile is significantly worse than raw/lifting Basis.

## 12. Executable native kernel

The Golden Core now exposes the complete CIBS-0 synthesis envelope through a
C99 ABI implemented in dependency-free C++23:

- immutable caller-owned model-registry descriptors;
- int8 projection and optional rank-1 through rank-4 adapter;
- signed round-to-nearest with ties away from zero;
- the canonical negative one-eighth activation;
- up to four periodic channel-local refinement stages;
- int16 saturation after projection, every refinement, and correction;
- optional int32 objective correction;
- incremental canonical Basis SHA-256;
- atomic output commit only after an expected hash matches;
- exact output, scratch, and integer-MAC accounting.

Two `int64` planes sized to the final Basis plus at most four adapter elements
are sufficient scratch. No allocation, I/O, logging, model loading, or
floating point occurs in materialization.

The first native vector deliberately uses
`CIBS0-DEMO-NOT-NORMATIVE`. Python and C++ independently produce Basis hash:

```text
2c901e3a32e042a960d06d71dc5961171d7b6304c5e984f892904b34ef80782f
```

Adapter and saturating-correction paths have separate cross-language hashes.
This proves the operator implementation; it does not accept the demo weights
as a production model. Model registry entries remain subject to the kill
conditions above.
