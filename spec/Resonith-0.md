# Resonith-0 Bitstream and Decoding Process

Version: 0.0.6
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

### 4.1 Resonith Section Container 1 (`RSC1`)

`RSC1` is the executable Main-0 container candidate. It replaces the
experimental JSON/zlib `MAF0` wrapper. All multi-byte integers are
little-endian.

The fixed 32-byte header contains, in order:

- magic `RSC1`;
- `u8 version_major = 1`, `u8 version_minor = 0`;
- `u8 profile`, `u8 level`;
- `u32 flags`, which is zero in Main-0;
- `u32 timebase_hz`;
- `u32 section_count`;
- `u32 directory_record_bytes = 80`;
- `u32 directory_bytes = section_count * 80`;
- IEEE `u32 directory_crc32` over the directory bytes.

The directory immediately follows the header. Its records are sorted strictly
by the tuple `(type[4], instance_id)` and duplicate keys are prohibited. Each
fixed 80-byte record contains:

- four uppercase ASCII letter/digit bytes `type`;
- `u16 schema_version`, which is non-zero;
- `u16 flags`, where bit zero marks a critical section;
- `u32 instance_id`;
- `u64 start_tick`;
- `u64 payload_offset`;
- `u64 stored_bytes`;
- `u64 raw_bytes`;
- IEEE `u32 payload_crc32`;
- 32 raw bytes of SHA-256 over the stored payload.

Main-0 supports stored self-encoded payloads only, so `stored_bytes` MUST equal
`raw_bytes`. Payloads MUST be tightly packed after the directory in canonical
directory order; the final payload MUST end at the stream boundary. Each
section is limited to 512 MiB, the sum of raw section bytes to 1 GiB, and the
directory to 4,096 records.

A decoder MUST validate the header, directory CRC, strict key order, sizes,
offsets, feature flags, and complete stream coverage before exposing section
views. It MUST validate both section CRC-32 and SHA-256 before passing that
payload to a normative decoder primitive. Unknown critical types MUST cause
profile rejection. Non-critical unknown types MAY be skipped.

#### 4.1.1 Raw Basis section (`BRAW`, schema 1)

The payload contains `u16 channels`, zero `u16 flags`,
`u32 samples_per_channel`, then exactly
`channels * samples_per_channel` channel-major little-endian int16 samples.
Channels are in \([1,8]\), total elements do not exceed 16,384, and trailing
bytes are prohibited. Implementations decode to aligned host-endian Basis
memory before state commit.

#### 4.1.2 Cached CIBS Basis section (`BCIB`, schema 1)

The fixed 48-byte header contains:

| Field | Type | Constraint |
|---|---|---|
| `model_id_bytes` | `u8` | 1 through 255 |
| `flags` | `u8` | zero |
| `latent_elements` | `u16` | 1 through 128 |
| `channels` | `u16` | one in Main-0 |
| `reserved` | `u16` | zero |
| `samples_per_channel` | `u32` | 2 through 2,048 |
| `reserved2` | `u32` | zero |
| `expected_basis_sha256` | 32 bytes | CIBS-0 canonical Basis hash |

The header is followed by exactly `model_id_bytes` UTF-8 bytes and then
`latent_elements` signed int8 values. Trailing bytes are prohibited.

The decoder application supplies an immutable model registry. Exactly one
registered model MUST have a byte-identical model ID. Its latent size, output
channel count, and output length MUST equal the payload declarations. Duplicate
registry IDs, a missing model, or any shape mismatch MUST reject the stream.

Schema 1 has no adapter or objective Basis correction. The decoder runs the
registered CIBS-0 graph once when materializing the immutable Basis, computes
the hash defined in section 6.0, and commits the Basis only when it equals
`expected_basis_sha256`. CIBS staging memory is caller-owned, bounded, and
reported during stream inspection. The executable Main-0 ABI MAY reuse the
LiftPack int64 staging region because residual decoding and Basis
materialization do not overlap; its required capacity is the maximum of the
two exact requirements.

#### 4.1.3 Stream configuration section (`CONF`, schema 1)

The payload is exactly 16 bytes:

| Field | Type | Constraint |
|---|---|---|
| `sample_count` | `u32` | \(1\) through \(2^{31}-1\) |
| `innovation_step` | `u32` | \(1\) through \(2^{20}\) |
| `output_channels` | `u16` | \(1\) through \(8\) |
| `flags` | `u16` | zero |
| `reserved` | `u32` | zero |

`timebase_hz` in the RSC1 header is the PCM sample rate. `sample_count` is the
number of PCM frames; it equals the number of samples only for mono. Every
executable Main-0 subset has profile zero, level zero, and one critical `CONF`
record with instance ID and start tick zero.

#### 4.1.4 Periodic Atom section (`ATOM`, schema 1)

The fixed 24-byte header contains:

| Field | Type | Meaning |
|---|---|---|
| `basis_instance_id` | `u32` | referenced Basis instance |
| `duration_samples` | `u32` | Atom lifetime |
| `phase_origin_q32` | `u32` | absolute phase at local sample zero |
| `phase_knot_count` | `u32` | number of endpoint knots |
| `gain_event_count` | `u32` | number of sparse gain events |
| `flags` | `u32` | zero |

The header is followed by `phase_knot_count` records of
`(u32 position, u32 increment_q32)`, then `gain_event_count` records of
`(u32 position, i32 gain_q15)`. Each record is exactly eight bytes.

Phase positions MUST begin at zero, end exactly at `duration_samples`, increase
strictly, and have no span greater than 32,768 samples. There MUST be between
two and 1,000,000 phase knots. Gain positions MUST begin at zero, increase
strictly, and remain below `duration_samples`; there MUST be between one and
1,000,000 events. Every gain is signed Q17.15 in
\([-131072,131071]\).

The RSC1 record start tick is the Atom lifetime origin. Trajectory and gain
positions remain local to that origin. The referenced `BRAW` or `BCIB` MUST be
mono and contain at least two samples. A referenced Basis record start tick
MUST be no later than the Atom start tick.

#### 4.1.5 First executable Main-0 stream

A profile-zero, level-zero stream contains exactly one critical instance-zero
`CONF`, exactly one critical instance-zero Innovation section (`RSL1` or
`RSL2`), and either no model records or one or more critical `ATOM` plus one or
more critical Basis records (`BRAW` and/or `BCIB`). Both Innovation section
types in one stream are prohibited.
`ATOM` and Basis records MUST be both absent or both present. When present,
Atom instance IDs form one consecutive zero-based sequence. `BRAW` and `BCIB`
share a second consecutive zero-based instance namespace; exactly one of the
two representations MUST exist for every Basis instance ID.

When Atoms are present, they are ordered by instance ID. The first MUST start
at tick zero, every subsequent Atom MUST start exactly where the previous Atom
ends, and the final Atom MUST end at the `CONF` sample count. Simultaneous
overlap is not supported by this executable subset. Any number of Atoms MAY
reference one immutable Basis.

When no Atoms are present, prediction is identically zero and each output
sample is:

\[
\hat{x}[n]=\operatorname{sat}_{16}
\left(\operatorname{Innovation}[n]\cdot innovation\_step\right).
\]

The decoded Innovation sample count MUST equal the `CONF` sample count in both
forms.

Additional unknown non-critical sections MAY be skipped. Unknown critical
sections, unsupported schemas, non-canonical instance IDs, gaps, overlaps, or
non-zero singleton-section start ticks MUST reject this subset.

A decoder MUST verify all required section hashes and all cross-section
lifetimes before rendering. It MUST be able to inspect the stream first,
report the maximum per-Atom Basis, phase, gain, and render workspace plus the
stream-wide Innovation workspace, and then reuse those buffers without hidden
allocation. The zero-Atom form reports zero for every model workspace and
requires only Innovation, LiftPack scratch, and output storage. The CIBS form
additionally reports the maximum CIBS-0 staging requirement across referenced
`BCIB` records.

#### 4.1.6 Independent-channel Main-0 stream

The independent-channel subset carries one through eight residual-only output
channels without a coupled prediction or render graph. It contains exactly one
canonical `CONF` and exactly `output_channels` critical `RSL2` records. No
`RSL1`, `ATOM`, `BRAW`, or `BCIB` record is permitted in this subset.

`RSL2` instance IDs MUST be the consecutive channel indices
\(0,\ldots,output\_channels-1\), and every record start tick MUST be zero.
Every residual MUST declare the `CONF` frame count. All residuals MUST have
identical LiftPack block size and block count. The common partition makes every
decoded block an aligned interval of PCM frames even though each channel
retains independent transform, LPC, and entropy decisions inside that block.

For frame \(n\) and channel \(c\), output is:

\[
\hat{x}[n,c]=\operatorname{sat}_{16}
\left(\operatorname{Innovation}_c[n]\cdot innovation\_step\right).
\]

Canonical channel order is:

| Count | Ordered channels |
| ---: | --- |
| 1 | `MONO` |
| 2 | `FL`, `FR` |
| 3 | `FL`, `FR`, `FC` |
| 4 | `FL`, `FR`, `BL`, `BR` |
| 5 | `FL`, `FR`, `FC`, `BL`, `BR` |
| 6 | `FL`, `FR`, `FC`, `LFE`, `BL`, `BR` |
| 7 | `FL`, `FR`, `FC`, `LFE`, `BC`, `SL`, `SR` |
| 8 | `FL`, `FR`, `FC`, `LFE`, `BL`, `BR`, `SL`, `SR` |

Custom speaker layouts, object metadata, and scene rendering are not part of
this minimum subset. They require a later spatial profile and MUST NOT change
standalone decoding of the base channels.

A whole-stream decoder MUST report one channel-sized Innovation region, the
maximum LiftPack scratch across channels, and
`sample_count * output_channels` interleaved output elements. It MUST validate
and decode every channel before the first whole-stream PCM write. A streaming
decoder MAY reuse one block-sized Innovation region, one maximum scratch
region, and one interleaved block. It emits a callback only after all channels
for that block have reconstructed with equal frame offset and length.

A pull decoder MAY retain one forward LiftPack cursor per channel in
caller-owned state. `decode_next` MUST reconstruct exactly one common block.
It MUST commit every channel cursor, `next_block`, and `next_frame` atomically
only after all channels succeed. A rejected block reports zero output frames
and leaves the session retryable. End-of-stream is reported only after the
declared block and frame counts are both exhausted.

#### 4.1.7 Prospective `LPS1` independent-context packet sequence

`LPS1` is a research candidate and is not yet a mandatory Resonith-0
conformance profile. It provides bounded-memory transport for the prospective
fixed/bounded LPF1 path without cross-packet prediction state.

The little-endian fixed header declares magic, version, zero flags, channel
count, sample rate, total logical frame count, half-window, band count, nominal
packet frames, and packet count. Nominal packet frames MUST be a positive
multiple of the half-window. Packet count MUST equal the canonical ceiling of
total frames divided by nominal packet frames. The header is immediately
followed by its 32-byte SHA-256 digest.

Each packet then contains:

1. `u32 logical_start`, `u32 logical_count`, and `u32 child_bytes`;
2. one complete LPF1/RSC1 child of exactly `child_bytes`;
3. SHA-256 over the packet header and child bytes.

Logical intervals MUST be non-empty, contiguous, ordered, non-overlapping, and
cover the declared output exactly. Each child MUST declare the envelope's
sample rate, channel count, half-window, and band count. Its PCM frame count
MUST equal `logical_count + 2 * half_window`.

The encoder prepends and appends exactly one half-window of source context,
using zeros only outside the logical track. The decoder authenticates and
decodes one child independently, discards the first and final half-window, and
commits only the central logical interval. It MUST NOT use concealment or a
failed child as reference for another packet.

Fixed-density child interiors are required to equal monolithic LPF1
reconstruction for identical coefficient and transform parameters. Adaptive
density is permitted to redistribute its budget independently inside each
child. No whole-file digest is required: header and packet authentication are
independent so a receiver can validate and emit progressively.

#### 4.1.8 Prospective `LPS2` transform-boundary packet sequence

`LPS2` is a research successor to `LPS1` for short independent packets. It
uses the same fixed header, packet index, canonical logical coverage, header
digest, and per-packet digest. Its magic is `LPS2`.

The encoder MUST analyze and select one complete adaptive-density transform
field before packetization. For a half-window-aligned logical interval of
\(m\) half-windows, the packet carries exactly \(m+1\) selected transform
frames. Adjacent packets therefore duplicate exactly their one common boundary
transform frame. A final partial interval carries
`floor(logical_count / half_window) + 1` frames.

The authenticated packet child is the bounded `LSE2` scale, count, position,
and coefficient payload directly. It MUST NOT repeat an RSC1 directory, CONF,
LPF1 header, sample rate, channel count, half-window, or band count. Those
parameters are inherited from the authenticated sequence header. Decoding the
child with any different parameter set is prohibited.

The packet decoder initializes a zero local overlap buffer, synthesizes the
declared transform frames with the unchanged fixed LPF1 kernel, and emits the
central `logical_count` samples. It retains no transform, entropy, or
concealment state for the next packet. Concatenating every decoded packet MUST
equal monolithic synthesis of the globally selected transform field exactly.

Loss MAY create output-only concealment over the absent logical interval.
Concealed samples MUST NOT enter Truth, overlap, density, entropy, or future
packet state. Corrupted packets remain hard errors. `LPS2` is not mandatory
until native parity, hostile-input, resource, and listening gates pass.

#### 4.1.9 Prospective `LPS3` single-owner transform sequence

`LPS3` is a Realtime research alternative to `LPS2`. It uses the same global
analysis, direct LSE2 child grammar, authenticated envelope, packet records,
and canonical logical coverage. Its magic is `LPS3`.

Every selected transform frame MUST occur in exactly one packet. A non-final
packet owns the transform frames whose origins fall within its logical
interval and does not repeat the right boundary frame. The next packet owns
that shared frame. A final packet additionally owns the terminal transform
frame required to finish the track.

The receiver may synthesize most of packet \(k\) immediately, but MUST wait for
the first transform frame of packet \(k+1\) before committing the final
half-window of packet \(k\). This is bounded transform lookahead, not
predictive reference state. Complete uninterrupted LPS3 reconstruction MUST
equal monolithic synthesis of the globally selected field exactly.

If packet \(k\) is absent, its logical interval MAY be concealed. The final
half-window of packet \(k-1\), which awaited packet \(k\)'s first transform
frame, MAY also be concealed. Packet \(k+1\) and every later packet MUST remain
exactly decodable from received Truth fields. Concealment MUST NOT enter any
future codec state.

LPS3 trades strict packet independence for zero boundary-frame duplication,
one-half-window lookahead, and a bounded one-half-window backward loss
extension. It is not mandatory until native scheduling, loss, latency,
hostile-input, and listening gates pass.

#### 4.1.10 Prospective `LPS4` compact transport-framed sequence

`LPS4` retains LPS3 global selection, single ownership, lookahead, loss
containment, and exact reconstruction. Its magic is `LPS4`. It removes fields
that are already determined by the authenticated sequence header and ordered
transport record.

Packet \(k\)'s logical start is `k * packet_frames`; its logical count is the
smaller of `packet_frames` and the remaining declared track frames. The record
contains no repeated logical start, logical count, child byte count, sample
rate, channel count, half-window, band count, transform-frame count, magic, or
version.

Each record begins with this 27-byte little-endian compact entropy descriptor:

| Field | Type |
| --- | --- |
| scale entropy mode and parameter | `u8`, `u8` |
| count entropy mode and parameter | `u8`, `u8` |
| position Rice parameter | `u8` |
| value entropy mode and parameter | `u8`, `u8` |
| selected coefficient count | `u32` |
| scale, count, position, value bit counts | four `u32` |

The four canonical entropy payloads follow in that order, each occupying the
ceiling of its declared bit count divided by eight. A little-endian CRC-32 over
the descriptor and payloads terminates the record. The bit counts therefore
define the record length without another size field. Padding, entropy bounds,
coefficient order, and inherited shape MUST satisfy the unchanged LSE2 rules.

The sequence header retains SHA-256. CRC-32 detects accidental standalone
record corruption but is not cryptographic authentication. A Realtime network
profile using LPS4 MUST obtain replay protection and cryptographic packet
authentication from its transport, such as an authenticated SRTP or QUIC
mapping. A CRC-valid packet from an unauthenticated adversary MUST NOT be
treated as trusted media.

LPS4 remains prospective after passing native parsing, exact pull,
cross-platform, and hostile-input gates. Authenticated transport mapping,
physical-device resource measurements, loss scheduling, and listening still
MUST pass before LPS4 becomes mandatory.

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

### 5.3 `BASIS_SET(t, basis_id, family, lifetime, payload)`

Creates an immutable Basis. Reusing a `basis_id` before reset is prohibited.
`family` MAY identify a waveform/timbre Basis, filter/resonator Basis, or
`CONTROL_BASIS`.

`lifetime` defines a half-open interval beginning at `t` and ending at an
absolute `death_time`, or an open-ended lifetime terminated by `BASIS_END`.
Content-identical Basis payloads MAY be deduplicated by the encoder, but every
normative reference resolves to one explicit immutable Basis ID.

`payload_mode` MUST be:

- `RAW_INT`;
- `LIFTED_INT`;
- `CIBS_LATENT`.

A Main-0 decoder MUST implement all three modes. A CIBS payload MUST contain
`synth_model_id`, target schema, quantized latent, optional bounded adapter,
optional objective correction and expected Basis hash.

### 5.4 `BASIS_END(t, basis_id)`

Terminates a Basis immediately before sample `t`. No live Atom may reference a
Basis at or after its termination time. A decoder MUST validate the complete
mutation before removing the Basis.

### 5.5 `ATOM_SET(t, atom_id, changed_fields, payload)`

Creates an atom or atomically modifies the listed fields. Unspecified fields
retain the same value.

Every Atom that references a Basis MUST have a lifetime fully contained by the
Basis lifetime. An update that violates this invariant MUST be rejected before
state commit.

### 5.6 `ATOM_END(t, atom_id)`

Terminates an Atom immediately before sample `t`.

### 5.7 `INNOVATION(t, duration, payload)`

Adds a bounded objective residual. `EXACT_REPLACE` MUST be able to define any
interval completely, independently of model Atoms.

### 5.8 `CHECKPOINT(t)`

Contains a self-contained Core state, or a `STATE_RESET` followed by enough
payload to provide bounded random access.

### 5.9 `PERCEPTUAL(t, duration, payload)`

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

The first executable phase law uses knots \((p_i,f_i)\), where positions are
absolute local sample indices and \(f_i\) is unsigned Q0.32 cycles/sample.
Positions begin at zero, increase strictly, and no span exceeds 32,768
samples. For interval length \(L=p_{i+1}-p_i\) and local position
\(0\le j<L\):

\[
\phi_i(j)=
\phi_i(0)+j f_i+
RoundAway\left(
\frac{(f_{i+1}-f_i)j(j-1)}{2L}
\right)
\pmod {2^{32}}.
\]

The next knot origin is the same equation evaluated at \(j=L\). A decoder
MUST derive every rendered slice from a prepared knot origin, not a preceding
output sample.

For a Basis of \(N\) int16 samples, the phase lookup position is
\(q=\phi N\). The upper 32 bits select the left sample and bits 16 through 31
define Q16 interpolation fraction \(a\). The output is:

\[
Clip_{16}\left(
\left\lfloor
\frac{B_l(65536-a)+B_{(l+1)\bmod N}a+32768}{65536}
\right\rfloor
\right).
\]

Signed division and negative intermediate behavior MUST follow these equations
explicitly rather than implementation-defined right shift.

The first executable amplitude law is a strictly increasing sequence of
absolute event positions and signed Q17.15 gains. The first position is zero;
each gain remains active until the next event. For unity prediction \(u[n]\)
and active gain \(g[n]\):

\[
p[n]=
\left\lfloor
\frac{u[n]g[n]+16384}{32768}
\right\rfloor.
\]

No periodic gain refresh is required. A constant gain therefore costs one
event for the Atom lifetime.

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

A Main transient event:

- has explicit half-open sample support;
- MUST reconstruct the identity contribution outside that support;
- MUST use a profile-bounded transform length and coefficient count;
- MUST NOT overlap another exact-replacement transient event in the same
  dependency layer;
- MAY be skipped by the encoder when its event, coefficient, and remaining
  Innovation cost is not lower than the universal fallback.

Detection is non-normative. The declared support and transmitted objective
payload, not an inferred onset label, determine decoder output.

### 6.6 `INNOVATION`

Uses inverse integer lifting, sparse coefficients and exact replacement.
This is a universal fallback, not a separate content classifier.

For the first executable scalar composition, a decoded quantized coefficient
\(q[n]\) and positive integer step \(s\) produce:

\[
\hat x[n]=Clip_{16}(p[n]+q[n]s).
\]

Prediction scaling, Innovation dequantization, addition, and saturation use
wide integer intermediates in one pass.

#### 6.6.1 `LiftPack-1`

`LiftPack-1` is the first executable Main draft for a bounded objective
Innovation payload. All multi-byte integers and entropy bits are little-endian.

The stream header contains:

- four-byte magic `RSL1`;
- unsigned eight-bit version `1`;
- unsigned 16-bit `block_size`;
- unsigned 32-bit `sample_count`;
- unsigned 32-bit `block_count`.

Every block contains:

- unsigned 16-bit original sample length;
- unsigned eight-bit transform ID;
- unsigned eight-bit entropy ID;
- unsigned eight-bit entropy parameter;
- unsigned 32-bit entropy bit count;
- the declared entropy payload.

The stream ends with little-endian IEEE CRC-32 over every preceding byte. The
enclosing Resonith section hash remains mandatory; CRC-32 is a local corruption
check and not a cryptographic authenticator.

Transform IDs are:

- `0`: `IDENTITY`;
- `1`: `DELTA1`, where \(y_0=x_0\) and \(y_n=x_n-x_{n-1}\);
- `2`: `DELTA2`, where \(y_0=x_0\), \(y_1=x_1-x_0\), and
  \(y_n=x_n-2x_{n-1}+x_{n-2}\);
- `3`: reversible integer `HAAR`.

For one Haar pair \(e,o\):

\[
d=o-e,\qquad l=e+\left\lfloor\frac{d}{2}\right\rfloor.
\]

The inverse is:

\[
e=l-\left\lfloor\frac{d}{2}\right\rfloor,\qquad o=d+e.
\]

Haar input is zero-padded to the next power of two; the original block length
defines the returned samples. All transforms MUST use profile-bounded wide
integer arithmetic and MUST reconstruct the quantized residual exactly.

A signed coefficient \(c\) maps to unsigned zigzag value:

\[
u(c)=
\begin{cases}
2c, & c\ge 0,\\
-2c-1, & c<0.
\end{cases}
\]

Entropy ID `0` (`RICE`) uses \(k\in[0,20]\). For
\(q=\lfloor u/2^k\rfloor<31\), it codes \(q\) one bits, one zero bit, and the
\(k\)-bit remainder. For \(q\ge31\), it codes 31 one bits, one zero bit, and
the full unsigned value in 64 bits. Entropy ID `1` (`PACKED`) codes every
zigzag value with the declared fixed width in \([1,64]\).

A Main-0 decoder MUST reject:

- a non-canonical block count or block length;
- a block larger than 32,768 samples;
- a Rice parameter above 20;
- more than 96 coded bits per coefficient;
- non-zero final padding bits;
- an inverse result outside the profile sample bound;
- trailing data, checksum failure, or incomplete coverage.

LiftPack blocks are independently reconstructible after their explicit stream
header. The reference encoder competes every transform and entropy mode by
actual payload size, but encoder search is non-normative.

A decoder or player MAY build an out-of-band block index after validating the
LiftPack checksum and every block envelope. Such an index does not alter Truth,
is not required for sequential decode, and MUST identify each block by its
exact byte interval and output-sample interval. LPC blocks are independently
decodable because their first `order` entropy values are literal seed samples.

A sequential decoder SHOULD retain a caller-owned cursor containing the next
byte offset, next output-sample offset, and next block number. It validates the
outer checksum once, advances only after a complete block succeeds, and MUST
reject final byte or sample coverage that differs from the stream header. This
makes callback-sized playback linear in stored bytes with one-block work
memory. Callback partitioning MUST NOT change reconstructed PCM.

An out-of-band or optional serialized index is never required to recover
Truth. Before trusting serialized offsets, a player MUST verify the index
independently and bind it to the exact verified LiftPack payload identity.
Absence or rejection of the index changes seek work only.

#### 6.6.2 `LiftPack-2`

`LiftPack-2` uses section type and payload magic `RSL2`. Version 1 retains the
LiftPack-1 stream header, block header, CRC, transform IDs 0 through 3, and
entropy modes. It additionally defines transform ID `4` (`LPC`).

An LPC block places the following bytes after its regular block header and
before its entropy payload:

- unsigned eight-bit `order` in \([1,16]\);
- unsigned eight-bit `precision`, which MUST equal 12 in Main-0;
- exactly `order` little-endian signed int16 predictor coefficients.

The sum of absolute coefficient values MUST NOT exceed
\(8\cdot2^{12}\). Order MUST be less than the block sample length. The entropy
coefficient count remains equal to the original block length.

Let decoded entropy values be \(e[n]\), Q12 coefficients be \(a_k\), and
reconstructed values be \(x[n]\). For \(n<order\):

\[
x[n]=e[n].
\]

For later samples:

\[
p[n]=RoundAway\left(
\frac{\sum_{k=1}^{order}a_{k-1}x[n-k]}{2^{12}}
\right),\qquad
x[n]=e[n]+p[n].
\]

`RoundAway` rounds to nearest with exact half cases away from zero. The decoder
MUST use a wide signed accumulator, validate coefficient bounds before
inverse prediction, and reject any reconstructed value outside the profile
sample bound. An `RSL1` payload MUST reject transform ID 4. Main-0 permits
exactly one of `RSL1` or `RSL2`, never both.

#### 6.6.3 Optional `RSI1` seek sidecar

`RSI1` is non-Truth metadata bound to one exact complete `RSL1` or `RSL2`
payload. It MAY be stored out of band or in a non-critical RSC1 section with
type `RSI1`, schema version 1, instance ID zero, and start tick zero. Its
absence or rejection MUST NOT prevent sequential Truth decode.

The 64-byte little-endian header contains:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | magic `RSI1` |
| 4 | 1 | version `1` |
| 5 | 1 | flags, zero |
| 6 | 2 | header bytes, `64` |
| 8 | 2 | entry bytes, `32` |
| 10 | 2 | reserved, zero |
| 12 | 4 | block count |
| 16 | 2 | LiftPack block size |
| 18 | 2 | reserved, zero |
| 20 | 4 | source sample count |
| 24 | 8 | complete source payload bytes |
| 32 | 32 | SHA-256 of the complete source payload |

Each fixed 32-byte entry contains:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 8 | block byte offset in the source |
| 8 | 8 | complete block bytes |
| 16 | 4 | output-sample offset |
| 20 | 4 | entropy bit count |
| 24 | 2 | output-sample count |
| 26 | 1 | transform ID |
| 27 | 1 | entropy ID |
| 28 | 1 | entropy parameter |
| 29 | 1 | LPC order, zero for non-LPC |
| 30 | 2 | reserved, zero |

The table ends with CRC-32 followed by SHA-256 over the header and all entries,
for a total size of \(100+32\cdot block\_count\) bytes. Main-0 limits RSI1 to
1,000,000 entries.

Before exposing an entry, a player MUST:

1. validate the RSI1 version, fixed sizes, reserved fields, total length,
   CRC-32, and SHA-256;
2. validate the complete source LiftPack checksum;
3. match source byte length, SHA-256, block size, block count, and sample
   count;
4. parse every source block envelope and require exact equality with its RSI1
   entry;
5. require canonical final source-byte and output-sample coverage.

After those checks, a player MAY use an entry to initialize a block cursor and
decode that independently seeded block without scanning earlier envelopes.
The opened view and both backing byte arrays MUST remain immutable. If a
transport requires RSI1 for its advertised seek behavior, its bytes MUST be
included in that transport's complete-rate accounting.

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

For a piecewise-linear Q32 phase-increment interval of length \(L\), local
offset \(r\), starting phase \(\phi_0\), and endpoint increments
\(\omega_0,\omega_1\), Main-0 uses the absolute law:

\[
\phi(r)=\phi_0+r\omega_0+
RoundAway\left(
\frac{(\omega_1-\omega_0)r(r-1)}{2L}
\right)
\quad(\bmod\ 2^{32}).
\]

The next interval origin is \(\phi(L)\). `RoundAway` rounds to nearest with
ties away from zero. A profile MUST bound \(L\) so that the specified
accumulator cannot overflow. Rendering a full interval, arbitrary slices, or
different implementation block sizes MUST produce identical phases and
samples.

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
- maximum phase-law knot span and accumulator width;
- maximum Basis creations, terminations, and total lifetimes per time unit;
- maximum transient events, support length, transform length, and coefficients
  per time unit;
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

Acoustic feature analysis MAY propose Atom and Basis lifetimes. A proposed
boundary MUST NOT be treated as valuable merely because a classifier or
change-point detector is confident. Studio and Foundry encoders SHOULD compare
the complete resulting streams, including Basis, Atom, trajectory, gain,
Innovation, checkpoint, and container cost. The canonical zero-Atom
Innovation stream from clause 4.1.4 MUST remain an RDO candidate.

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

- final record packing outside LiftPack-1;
- adaptive entropy contexts beyond LiftPack-1;
- exact PRNG construction;
- exact CIBS-0 graph, weights, quantizers, Basis hash and model package;
- additional lifting kernels beyond LiftPack-1;
- sample formats and channel layouts;
- fixed-point precisions;
- stability domains;
- exact profile/level limits;
- promotion of the prospective `LPS1` packet sequence and FEC;
- MUSHRA conformance corpus;
- reference encoder/decoder;
- container mappings.

No open item changes the accepted semantic spine without a new entry in
`docs/06_DECISION_LOG.md`.
