# Resonith-0 Bitstream and Decoding Process

Version: 0.0.2
Status: **NORMATIVE-DRAFT**
Architecture: **MAF - Memory-oriented Acoustic Field**

This document defines the semantic spine. Binary packing, entropy tables,
fixed-point precisions and profile limits will be frozen after oracle and
conformance experiments.

## 1. Conformance language

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be
interpreted as described by RFC 2119 and RFC 8174.

## 2. Scope

Resonith-0 defines a self-contained deterministic audio bitstream and a
resource-bounded integer decoding process.

Resonith-0:

- MUST be decodable without a video stream;
- MUST have a universal objective Innovation fallback;
- MUST support CIBS-0 cached integer Basis synthesis;
- MUST support simultaneous mixing of different Basis families;
- MUST NOT require a semantic classifier or per-sample neural inference;
- MUST separate Truth Core from Optional Perceptual Detail;
- MUST allow the Lossless profile to reconstruct exact PCM.

## 3. Canonical signal

\[
\hat x[n]=
Mix\left(
\sum_{i\in Active(n)}
RenderAtom_i(n)
\right)
+ Innovation[n].
\]

Optional Perceptual Detail is applied only after the Core output is generated
and is not included in \(\hat x[n]\) for objective/lossless conformance.

## 4. Timeline

1. A stream MUST define a rational sample timebase and output sample rate.
2. An event timestamp MUST be an exact integer sample index in that timebase.
3. Every Atom parameter law MUST have an absolute origin.
4. A decoder MUST NOT render an Atom by recursively referencing the previous
   output block.
5. Transport packet boundary MUST NOT terminate atom implicitly.
6. Render block size is an implementation choice and MUST NOT change the output.

## 5. State records

### 5.1 `STREAM_CONFIG`

Defines:

- profile/level;
- sample rate and channel/output layout;
- fixed-point precision identifiers;
- entropy configuration;
- resource limits;
- capability flags.

### 5.2 `STATE_RESET(t)`

Atomically clears the Atom namespace, Basis Bank, and dependent filter state.

### 5.3 `BASIS_SET(t, basis_id, family, payload)`

Creates an immutable Basis. Reusing a `basis_id` before reset is prohibited.
`family` MAY identify a waveform/timbre Basis, filter/resonator Basis, or
`CONTROL_BASIS`.

`payload_mode` MUST be:

- `RAW_INT`;
- `LIFTED_INT`;
- `CIBS_LATENT`.

A Main-0 decoder MUST implement all three modes. A CIBS payload MUST contain
`synth_model_id`, target schema, quantized latent, optional bounded adapter,
optional objective correction and expected Basis hash.

### 5.4 `ATOM_SET(t, atom_id, changed_fields, payload)`

Creates an atom or atomically modifies the listed fields. Unspecified fields
retain the same value.

### 5.5 `ATOM_END(t, atom_id)`

Terminates an Atom immediately before sample `t`.

### 5.6 `INNOVATION(t, duration, payload)`

Adds a bounded objective residual. `EXACT_REPLACE` MUST be able to define any
interval completely, independently of model Atoms.

### 5.7 `CHECKPOINT(t)`

Contains a self-contained Core state, or a `STATE_RESET` followed by enough
payload to provide bounded random access.

### 5.8 `PERCEPTUAL(t, duration, payload)`

Defines a discardable enhancement and MUST NOT change Core state.

## 6. Basic families

A Main decoder uses one common operator ISA. Basis families do not have separate
entropy coders or clocks.

### 6.0 CIBS Basis materialization

\[
B =
Clip_{basis}\left(
Synth^{int}_{model}(z,adapter)
+ LIFT^{-1}(q_{correction})
\right).
\]

Decoder MUST:

1. check model/schema/resource limits;
2. execute fixed versioned integer graph in staging;
3. apply correction;
4. calculate the normative Basis hash;
5. commit immutable Basis only if the hash matches.

CIBS MUST be executed only at `BASIS_SET` or materialization checkpoint.
Per-sample CIBS inference is prohibited.

The CIBS-0 Basis hash MUST be SHA-256 over this canonical byte sequence:

```text
u8 model_id_utf8_length
u32le basis_channels
u32le samples_per_channel
model_id_utf8
int16le basis_samples[channel-major]
```

`model_id` MUST occupy 1–255 UTF-8 bytes.

### 6.1 `PERIODIC`

\[
y[n]=A[n]\sum_k a_k[n]B_k(\phi[n]).
\]

- `B_k` MUST be immutable bounded integer periodic tables;
- phase law MUST be absolute fixed-point;
- interpolation and wrapping MUST have canonical rounding;
- an Atom update MUST preserve phase continuity or provide an objective
  correction/crossfade.

### 6.2 `PREDICTIVE`

Uses bounded excitation and short, stable integer FIR/IIR sections.
Allowed coefficients MUST belong to the profile-defined stability domain.

### 6.3 `STOCHASTIC`

Uses a normative counter-based PRNG:

\[
u[n]=PRNG(stream\_key,atom\_id,seed,n).
\]

Shaping MUST use bounded integer operations. Random access to `n` MUST NOT
require generation of samples up to `n`.

### 6.4 `RESONANT`

Uses a bounded bank of stable resonators or a short convolution Basis.
Unbounded convolution and undefined recursive state are prohibited.

### 6.5 `TRANSIENT`

Uses an onset-relative bounded envelope and/or a short inverse-integer-lifting
Basis. Long-window pre-echo MUST have a separate conformance test.

### 6.6 `INNOVATION`

Uses inverse integer lifting, sparse coefficients and exact replacement.
This is a universal fallback, not a separate content classifier.

### 6.7 `SPATIAL`

Defines source routing, gain/delay laws, and a bounded integer mix matrix.
Immersive renderer MAY be profile-specific, but base Core output MUST
remain self-determined.

## 7. Operator ISA

Main Core MAY use only:

- integer add/subtract/multiply/accumulate;
- canonical shift/round/saturate;
- bounded table lookup and interpolation;
- short FIR/IIR/resonator sections;
- counter-based PRNG;
- inverse integer lifting;
- coefficient-law evaluation;
- gain/delay/matrix mix;
- entropy decode.

A CIBS materialization kernel MAY additionally use fixed-integer matrix or 1D
convolution, dyadic upsampling, short FIR, piecewise-linear activation, and a
bounded low-rank adapter. `synth_model_id` selects the normative graph topology
and weights; the bitstream does not define an arbitrary graph.

A bitstream MUST NOT contain executable code, an arbitrary neural graph,
replacement model weights, or an unbounded loop.

## 8. Canonical composition

1. Events with one timestamp are applied in coded order after full verification.
2. Basis/atom update is first built in staging and then committed atomically.
3. Active atoms are grouped by profile-defined dependency level.
4. Independent atoms MAY be calculated in parallel.
5. Accumulation uses profile-defined wide integer accumulator.
6. Saturation and clipping occur only at profile-defined mix boundaries.
7. Result MUST be independent of implementation block size and thread order.

## 9. Parameter tracks

Main-0 MUST support bounded piecewise:

- constant;
- linear;
- quadratic.

The profile defines maximum duration, knot count, coefficient range, and
derivative. A track is evaluated from its absolute event origin.

Atom MAY reference immutable `CONTROL_BASIS`:

\[
\theta_i(t)=s_iQ_r(\tau_i(t))+o_i.
\]

Scale, offset and time mapping MUST be bounded fixed-point. Reference MUST NOT
create cyclic dependency. Shared control evaluation uses the same
parameter-law operators and is not a separate decoder mode.

## 10. Profiles

### 10.1 `Realtime`

Limits lookahead, atom lifetime dependencies, checkpoint interval and
decoder complexity for low-delay speech/general audio.

### 10.2 `Main`

Supports general mono, stereo and profile-defined multichannel output,
including all Core families and normative `CIBS-0`.

### 10.3 `Immersive`

Adds emitters, listener pose, room/resonant state and profile-defined
spatial renderer.

### 10.4 `Perceptual`

Adds discardable learned or generative detail. Perceptual output is never a
Core reference.

### 10.5 `Lossless`

Uses Core predictions, but Innovation MUST provide sample-exact PCM
when declared input format.

Profiles are constraints of a single syntax, rather than independent subcodecs.

## 11. Resource limits

Each level MUST define:

- maximum active atoms;
- maximum basis bytes;
- maximum table taps and interpolation samples;
- maximum filter/resonator order;
- maximum MAC/sample/channel;
- maximum mix sources and channels;
- maximum parameter knots per unit of time;
- maximum checkpoint distance;
- maximum entropy payload;
- maximum state bytes;
- maximum CIBS model ROM, latent, adapter, output elements, MAC/Basis,
  scratch bytes and creations/time;
- accumulator widths and overflow rules.

If a candidate representation exceeds a limit, the encoder MUST use a simpler
representation or `INNOVATION`. A decoder MUST reject a non-conforming stream
deterministically.

## 12. Truth and Perceptual isolation

1. Only Core records MAY change the reference state.
2. `PERCEPTUAL` MUST NOT influence future atom, entropy context, checksum or
   checkpoint.
3. Concealment MUST NOT become a Truth reference.
4. Lossless conformance MUST ignore Perceptual records.
5. Semantic labels MAY appear as non-normative metadata but MUST NOT change
   Core output.

## 13. Random access and loss

1. Random-access point MUST start with validated `CHECKPOINT` or
   `STATE_RESET`.
2. Stochastic samples MUST be counter-addressable.
3. CIBS checkpoint MUST contain self-contained latent+adapter+correction
   or materialized objective Basis.
4. CIBS Basis hash failure MUST NOT commit partial state.
5. Corrupt state event MUST NOT commit partial changes.
6. After integrity failure dependent state MUST be considered invalid until
   next checkpoint.
7. Realtime level MUST limit maximum error propagation.
8. Concealment output MUST be marked and not used as a reference.

## 14. Encoder requirements

An encoder is non-normative, but every conforming bitstream:

- MAY be created by a Live, Studio, or Foundry encoder;
- MUST NOT require a classifier decision for decoding;
- MUST account for all Basis, event, and checkpoint bits;
- MUST provide a Core fallback for every input;
- MUST comply with the declared resource level regardless of encoder quality.

Recommended final selector:

\[
J=R+\lambda D+\mu C+\nu M+\rho L+\kappa P+\eta S.
\]

## 15. Security

Decoder MUST:

- validate all sizes, IDs, and ranges before allocation or commit;
- validate the filter-stability domain;
- prevent integer overflow;
- bound entropy operations;
- never execute code from the bitstream;
- follow a deterministic error path;
- reject any Atom that references an undefined or expired Basis.

## 16. Open items

- binary packing;
- entropy contexts/tables;
- exact PRNG construction;
- exact CIBS-0 graph, weights, quantizers, Basis hash and model package;
- lifting kernels;
- sample formats and channel layouts;
- fixed-point precisions;
- stability domains;
- exact profile/level limits;
- packetization/FEC;
- MUSHRA conformance corpus;
- reference encoder/decoder;
- container mappings.

No open item changes the accepted semantic spine without a new entry in
`docs/06_DECISION_LOG.md`.
