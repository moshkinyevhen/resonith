# R-271 S17 Anonymous Inharmonic Modal-Field Preflight

Date: 2026-08-03  
Status: **V6 IMPLEMENTATION-DISCOVERED REMEDIATION; DELTA AUDIT REQUIRED**

## Decision question and early-stop boundary

Can one persistent anonymous modal Basis replace several independently paid
S11 partial trajectories when their explicitly transmitted, non-integer
frequency ratios, relative phase, relative amplitude, and decay remain jointly
predictable, while one accepted-S12 Truth correction closes the decoded result?

S17 and S18 are one algorithm generation. S17 may run one bounded focused gate.
If its long predicate fails, all later controls and S18 are suppressed. If the
focused gate passes, S18 runs the frozen registered comparison once before any
later algorithm change. A rerun that cannot change an already failed
conjunctive predicate is forbidden.

## Frozen predecessor and evidence inputs

- accepted predecessor: S12, result
  `docs/results/R221_S12_FIXED_OPUS_DIRECT_2026-08-02.md`;
- accepted-S12 aggregate SHA-256:
  `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`;
- registered manifest SHA-256:
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`;
- quality-axis implementation SHA-256:
  `ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3`;
- frozen cosine-family manifest SHA-256:
  `9880c8f4ad2ac36e5af5302299a8a6dbbe7416b8243f48c786db3a375c40a87c`;
- length-256 cosine PCM16LE SHA-256:
  `da8b1b6cfbb6840806397707bec13084a272d2746628f0e61acd96cd4c372e7c`;
- control freezer SHA-256:
  `06391680f23c9bb771cb7157f2a0e82641e925201d0a081fe696e1f0af30e389`;
- tracked control manifest SHA-256:
  `86e772496a2f8c1ecbae89df133ca43528701c716acabffdeb90f27ca9939738`;
- generator-emitted manifest SHA-256:
  `c221431154c8d04c6e3f09f164959baa247c85be47c5653cf30f76d27b0c7180`.

The two manifests parse to the same JSON value; their byte hashes differ only
because the tracked repository file uses the checkout's CRLF policy while the
generator emits canonical LF. All field values, ordered arrays, and frozen
input identities must compare equal before a gate starts.

The corrected P0 exact-language PCM16 payload SHA-256 is
`e6d16edaba6b35f0b5c94892c82e749863f1fd8d38f4db50b14c62663b8beec8`;
its WAV SHA-256 is
`ace8cd8c82ab3d3c28216f8ba05b9960ba086dc8c11c90312b0d6f2ce376522c`.
Every non-P0 control and external-input identity is unchanged.

The complete identity-bound observer/path implementation is frozen as:

- `reference/maf_p0/complex_partial_analyzer.py`:
  `c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c`;
- `reference/maf_p0/partial_graph_fixed.py`:
  `8a692d9d5894049277ae543b10e29c93ea1466cb4c2b648befd7349683f982bc`;
- `native/include/resonith/partial_graph.h`:
  `12733d20b54be6209455800f477bfce9b84951d74699972a646dc492b803d49e`;
- `native/src/partial_graph.cpp`:
  `ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.

The proposer receives only PCM16 and declared sample rate. Importing the
control freezer, its manifest, generator constants, expected ratios, expected
boundaries, or output hashes is a gate failure. The runner hashes the proposer
import closure and scans it for forbidden control dependencies before audio
execution.

## Prior art and claim boundary

Sinusoidal tracking, additive synthesis, phase interpolation, HILN individual
lines, damped modal banks, and deterministic-plus-stochastic separation are
established prior art:

- <https://www.ll.mit.edu/r-d/publications/speech-analysissynthesis-based-sinusoidal-representation>;
- <https://www.mpeg.org/standards/MPEG-4/3/>;
- <https://www.mpeg.org/structure/audio-coding/>;
- <https://mtg.upf.edu/static/libsms/doc/index.html>;
- <https://arxiv.org/abs/1901.05044>;
- <https://www.cs.cornell.edu/projects/Sound/modec/>;
- <https://arxiv.org/abs/2309.06649>.

S17 makes no mechanism-novelty or superiority claim. Its sole falsifiable
hypothesis is complete-byte economy from sharing numeric coordinates across
several anonymous partials under a bounded integer decoder and unrestricted
accepted-S12 fallback.

## Alternatives and chosen minimum

1. **No change / S12 only** remains the universal incumbent.
2. **Expanded independent coordinates (`IMU1`)** are the attribution arm. They
   serialize the exact same quantized model PCM as IMF1 but repeat every
   instance law and knot for every mode. This is not an S11 quality comparator;
   it isolates only the bytes saved by IMF1 coordinate sharing.
3. **Harmonic fundamental plus integer indices** is excluded. S17 transmits
   every ratio explicitly and contains no fundamental index, harmonic number,
   harmonic envelope, or implied integer series. S33 may later compress those
   coordinates; S17 has no dependency on an unimplemented S33 serializer.
4. **Arbitrary-ratio shared modal Basis** is selected. It alone tests whether
   shared scale/gain/time coordinates repay Basis and Truth costs.
5. **Physical-object inversion, recursive object simulation, and a learned
   decoder** are rejected: they add non-identifiable or unstable state and
   confound this byte hypothesis. Learned proposers remain S49 work.
6. **Forcing every peak into the field** is rejected. Independent drift,
   crossings, beating, transients, stochastic energy, and false grouping are
   allowed to fall back.

## Exact IMF1 research pack

IMF1 is a private focused-gate envelope, not public Resonith syntax. All
integers are little-endian. Reserved fields must be zero. Offsets are absolute,
strictly increasing, exactly adjacent, and equal the formulas below.

### Header: 96 bytes

| Offset | Type | Field |
|---:|---|---|
| 0 | `char[4]` | magic `IMF1` |
| 4 | `u8` | version `1` |
| 5 | `u8` | flags `0` |
| 6 | `u16` | header bytes `96` |
| 8 | `u32` | sample rate |
| 12 | `u32` | sample count |
| 16 | `u16` | Basis count |
| 18 | `u16` | total mode count |
| 20 | `u16` | instance count |
| 22 | `u16` | total knot count |
| 24 | `u32` | accepted-S12 Truth bytes |
| 28 | `u32` | reserved zero |
| 32 | `u64` | Basis offset, exactly 96 |
| 40 | `u64` | mode offset |
| 48 | `u64` | instance offset |
| 56 | `u64` | knot offset |
| 64 | `u64` | Truth offset |
| 72 | `u64` | complete bytes, exactly input size |
| 80 | `u64` | sum of instance duration times Basis mode count |
| 88 | `u64` | reserved zero |

Offsets equal `96`, then `+16*bases`, `+16*modes`, `+32*instances`,
`+16*knots`, and finally `+truth_bytes`. Overflow rejects the stream.

### Basis record: 16 bytes

`u16 basis_id`, `u16 first_mode`, `u16 mode_count`, `u16 reserved`, and
`u64 reserved`. Basis IDs are contiguous from zero. Mode spans are nonempty,
adjacent, disjoint, and cover every mode exactly once.

### Mode record: 16 bytes

`u32 ratio_q20`, `u32 phase_q32`, `u16 relative_gain_q15`, `u16 reserved`, and
`u32 decay_q31`. Within a Basis, ratios are strictly increasing and the first
is exactly `1<<20`. Relative gain is nonnegative in `[0,32768]`; polarity is
represented only by phase, eliminating the signed-gain/phase-pi degeneracy.
Decay is unsigned in `[0,1<<31]`; `1<<31` is exact unity.

### Instance record: 32 bytes

`u16 basis_id`, `u16 first_knot`, `u16 knot_count`, `u16 reserved`, `u32 start`,
`u32 duration`, `u32 time_shift_q32`, `u32 reserved`, and `u64 reserved`.
Instances are sorted by `(start,basis_id,first_knot)`. Knot spans are adjacent,
disjoint, and cover all knots exactly once. Duration is nonzero. Checked
containment requires `start < sample_count` and
`duration <= sample_count - start`.

### Knot record: 16 bytes

`u32 offset`, `u32 common_step_q32`, `u16 common_gain_q15`, `u16 reserved`, and
`u32 reserved`. Each instance has at least two knots: offsets are strictly
increasing, first is zero, and last equals duration. Common step is below
Nyquist (`<1<<31`); common gain is in `[0,32768]`.

There is no terminator record. Exact `complete_bytes`, exact final Truth extent,
and exhaustion of every declared record terminate parsing. The parser validates
the entire pack and operation budget before any output write. For every mode at
every knot it also derives `mode_step_q32` with the rendering formula and
requires `mode_step_q32 < 1<<31`. It recomputes
`sum(instance.duration * referenced_basis.mode_count)` with checked unsigned
64-bit arithmetic and requires exact equality with the header's declared total
mode-samples.

## Exact integer rendering

All S17-defined divisions below use signed or unsigned nearest integer with
ties to even. Two inherited DSP laws remain unchanged: the
`resonith_phase_prepare` curve division is nearest with half ties away from
zero, and canonical Q16 periodic-Basis interpolation retains its frozen
half-toward-positive-infinity law. Every intermediate is checked before
conversion. The implementation may algebraically cancel and divide factors
before multiplication, but must produce the same unbounded-integer result;
overflow rejects the candidate or stream and never wraps or silently
saturates. Knot span is not an additional syntax bound.

For mode `k` and each common-law knot:

```text
mode_step_q32 = round_even(common_step_q32 * ratio_q20 / 2^20)
mode_phase0 = phase_q32
            + round_even(time_shift_q32 * ratio_q20 / 2^20) mod 2^32.
```

The derived per-mode knot steps feed the existing absolute Q32
`resonith_phase_prepare` law. The frozen 256-sample cosine Basis is rendered by
the existing canonical Q16 interpolation. No `detune` coordinate exists.

At instance-local sample zero:

```text
decay_state_q31 = relative_gain_q15 << 16.
```

For each later sample, after rendering the current sample:

```text
decay_state_q31 = round_even(decay_state_q31 * decay_q31 / 2^31).
```

Thus unity is exact, the recurrence is sample-addressed, and sequential decode
is bit-identical. S17 declares no checkpoints or closed-form exponentiation;
seek requires bounded full preroll from the instance onset and reports that
dependency. Common gain uses piecewise-linear interpolation between knots with
this exact rule. For a local integer sample `p` in
`[offset_i, offset_(i+1))`:

```text
common_gain(p) = gain_i
  + round_even((gain_(i+1) - gain_i) * (p - offset_i)
               / (offset_(i+1) - offset_i)).
```

The first endpoint is exact. The final knot is a boundary at `duration` and is
never itself rendered; its value only controls interpolation through the final
sample. One mode contribution is:

```text
round_even(periodic_pcm16 * decay_state_q31 * common_gain_q15 / 2^46).
```

Each contribution is first narrowed to checked signed 32-bit, then accumulated
in signed 64-bit. At most 64 modes may be simultaneously active. The model is
accepted only when every accumulated sample lies in PCM16; no model clipping is
permitted.

Truth derivation uses signed 32-bit `source_i16 - model_i16`. Any value outside
PCM16 rejects the model. The exact PCM16 residual is encoded by the frozen
accepted-S12 path and decoded independently. Final playback adds model and
decoded residual in signed 32-bit then saturates to PCM16. The gate records the
would-clip count and requires zero for every selected candidate; saturation can
therefore never hide an admitted overflow.

## Bounds

- sample rate: 8,000 through 48,000 Hz;
- sample count: 1 through 28,800,000;
- Bases: 1 through 8; instances: 1 through 16;
- modes per Basis: 3 through 16; total and simultaneously active modes: <=64;
- total knots: <=2,048; knots per instance: 2 through 256;
- total mode-samples: <=150,000,000;
- Truth and complete pack: each <=268,435,456 bytes;
- native decoder: caller-owned output, no allocation, transactional failure,
  explicit monotonically decreasing operation budget.

## Expanded-coordinate attribution pack

`IMU1` is a second private pack rendered only for attribution. Its 64-byte
little-endian header is:

| Offset | Type | Field |
|---:|---|---|
| 0 | `char[4]` | magic `IMU1` |
| 4 | `u8` | version `1` |
| 5 | `u8` | flags `0` |
| 6 | `u16` | header bytes `64` |
| 8 | `u32` | sample rate |
| 12 | `u32` | sample count |
| 16 | `u32` | direct-mode-instance count |
| 20 | `u32` | direct-knot count |
| 24 | `u32` | accepted-S12 Truth bytes |
| 28 | `u32` | reserved zero |
| 32 | `u64` | record offset, exactly `64` |
| 40 | `u64` | knot offset |
| 48 | `u64` | Truth offset |
| 56 | `u64` | complete bytes, exactly input size |

It contains one 32-byte direct-mode-instance record per
`(IMF1 instance, referenced mode)`, one 16-byte direct knot per corresponding
IMF1 knot, then the identical accepted-S12 Truth bytes. A direct record contains
`u32 start`, `u32 duration`, `u16 first_knot`, `u16 knot_count`,
`u16 relative_gain_q15`, `u16 reserved`, `u32 folded_phase_q32`,
`u32 decay_q31`, and `u64 reserved`. A direct knot contains `u32 offset`, the
already-derived `u32 mode_step_q32`, the unchanged `u16 common_gain_q15`,
`u16 reserved`, and `u32 reserved`. `folded_phase_q32` is IMF1 `mode_phase0`.
All reserved values are zero and the same containment, Nyquist, arithmetic,
Truth, operation, and termination checks apply.

Records are emitted in IMF1 instance order, then ascending mode order. Direct
knot spans are nonempty, adjacent, disjoint, and exhaust the declared knot
count. Checked parser recomputation requires direct records to equal
`sum(instance referenced mode_count)`, direct knots to equal
`sum(instance knot_count * referenced mode_count)`, and the direct-knot count
to be <=32,768. Offsets must equal `64`, then `+32*records`, then
`+16*direct_knots`, then `+truth_bytes`; every operation uses checked unsigned
64-bit arithmetic. Exact final Truth extent and exact complete size terminate
the pack; there is no terminator or trailing data.

The gate creates IMU1 mechanically from the already packed IMF1 integer model;
the proposer cannot optimize it separately. Independent scalar and native IMU1
decoders must produce model PCM byte-identical to IMF1. Every model-on selected
candidate must have strictly fewer complete IMF1 bytes than its actual IMU1
pack. This strict inequality is the sole coordinate-sharing attribution gate;
there is no arbitrary percentage and no dependency on S11 or S33.

## Bounded PCM-only proposer

The focused proposer is encoder-only and may use floating analysis, but its
output is re-quantized, packed, independently decoded, and judged only in the
integer domain.

1. Use exactly the four hash-bound complex-partial observer/path files above on
   PCM only; manifests and path bounds remain unchanged. Path entries are
   joined to observations by `observation_id`; no generator metadata is visible.
2. Keep at most 64 native selected paths in canonical path-ID order.
3. Form a grouping neighborhood only when path support overlaps by at least
   half the shorter support. Each seed considers at most 15 nearest-frequency
   neighbors, sorted by overlap descending, median log-ratio error ascending,
   then path ID.
4. Candidate support is the closed integer interval from the maximum first
   observation center to the minimum last observation center. The union of path
   observation centers in that interval, sorted by `(center_sample,path_id)`,
   is the initial common-knot set. The support endpoints are mandatory knots.
   Duplicate centers collapse to one knot. If more than 256 remain, repeatedly
   remove the interior knot with the smallest maximum absolute frequency-Q32
   interpolation error over all paths; ties remove lower center then lower path
   ID until exactly 256 remain. The final removed-knot error is reported but is
   not an eligibility threshold: complete accepted-S12 Truth bytes and frozen
   actual-decoder quality already reject a harmful approximation. An arbitrary
   micro-step threshold would duplicate those gates and create a false negative
   on long, slowly modulated fields.
5. `normalized_amplitude_q16` is an unsigned Q16 full-scale ratio and must be in
   `[0,65536]`; a path with a zero amplitude at its first retained knot is
   rejected. At every retained knot, linearly interpolate each path's integer
   `frequency_hz_q20` and `normalized_amplitude_q16` between its bracketing
   observations using signed round-to-even. A missing bracket rejects the
   candidate. For every observation derive
   `phase_step_u32 = round_even(frequency_hz_q20 * 2^32 /
   (sample_rate * 2^20))`, with checked unsigned arithmetic, and require it in
   `(0,2^31)`. Phase is unwrapped per path: predict the next unwrapped phase as
   `previous_unwrapped + previous derived phase_step_u32 * delta_samples`, choose the
   signed modulo-`2^32` delta from that prediction to the new
   `phase_turn_u32`, reject the exact half-turn `0x80000000` tie, and add the
   remaining delta with checked signed 64-bit arithmetic. Interpolate that
   unwrapped integer phase, then reduce modulo `2^32`. The lowest-frequency
   path is mode zero. Each other
   Q20 ratio is the median, with an even count averaged round-to-even, of
   `round_even(freq_k_q20 * 2^20 / freq_0_q20)` over knots. Ratios are sorted,
   strictly increasing, and the first is exactly `2^20`.
6. At each knot, `common_step_q32` is the median of
   `round_even(observed_step_k_q32 * 2^20 / ratio_k_q20)`; mode-zero breaks an
   even-median tie. At knot `i`, define `peak_i_q16` as the maximum mode
   amplitude. It must be in `[1,65536]`. The exact Q16-to-Q15 conversion is
   `common_gain_i_q15 = round_even(peak_i_q16 * 32768 / 65536)`. For mode `k`,
   define `target_ki_q31 = round_even(amplitude_ki_q16 * 2^31 / peak_i_q16)`.
   Its `relative_gain_q15` is
   `round_even(target_k0_q31 * 32768 / 2^31)` and must be nonzero. Thus common
   gain carries the full-scale envelope while relative gain/decay carry only a
   dimensionless modal ratio; no mixed Q16/Q15 division or clamp is permitted.
7. `phase_q32` is the first-knot observed phase. For a later instance,
   `time_shift_q32` is the modulo-Q32 difference of its mode-zero phase and the
   Basis mode-zero phase. The folded decoder phase of every other mode must be
   within its observer `phase_uncertainty_u31`; otherwise the instance gets a
   separate Basis or is rejected. For decay fitting, run the exact decoder
   recurrence from `relative_gain_q15 << 16`. At every retained knot offset its
   state must be <= `target_ki_q31 + 65535`, where `target_ki_q31` is the modal
   amplitude after division by that knot's `peak_i_q16` and `65535` is the one
   Q15 quantization allowance. The predicate is monotone in `decay_q31`. Test
   `2^31` first and choose it immediately if it passes. Otherwise test zero and
   reject if it fails; then, starting with accepted value zero, test
   `accepted | (1<<bit)` for bits 30 down through zero and retain each passing
   candidate. Those exactly 31 tests choose the largest passing value in
   `[0,2^31-1]`. Common-gain
   interpolation is applied only later by the decoder and is therefore not
   paid a second time in this dimensionless decay predicate. No logarithm or
   unfrozen floating decay fit is used.
8. Generate prefixes of the canonical neighbor order for sizes 3 through 16,
   reject failed integer/phase/Truth bounds, deduplicate by ordered path IDs,
   and retain at most 128 candidates by lower quantized fit error, longer
   support, more modes, then lexicographically lower path IDs.
9. Cluster candidate ratio vectors into at most eight Bases only when every
   Q20 ratio differs by <=2 and the model-PCM re-render remains identical.
   Otherwise instances do not share a Basis.
10. Evaluate at most 16 complete packed candidates, ordered by lower proxy
   residual SSE, lower metadata bytes, fewer modes, then canonical hash.

All median, interpolation, ratio, phase, decay, candidate-order, and tie
operations above are integer operations. The only floating work remains inside
the already hash-bound observer. The proposer source closure, linked native
binary, Python version, NumPy version, and compiler identity are frozen before
admission. Every model-on candidate on every input is independently packed
twice as IMF1 and twice as mechanically expanded IMU1; unequal same-format
SHA-256 values reject S17 before any quality decision. This both-pack predicate
is global and is inherited by P0, holdout, N1-N5, and EBU gong.

Any capacity or work-bound hit returns byte-identical accepted S12. Candidate
enumeration, order, hashes, work units, and peak memory are reported.

## Frozen controls and non-circularity

The immutable PCM-only manifest is
`experiments/fixtures/r271_s17_controls_v1.json`. The freezer generated the PCM
before codec implementation and is a forbidden proposer dependency. P0 tests
only parser/integer closure. The predeclared modal P1 is development-only; it
cannot admit S17. After the proposer source closure and linked binary hashes are
frozen, the independent auditor selects one previously unknown unsigned 64-bit
seed. The freezer is invoked exactly once with `--auditor-holdout-seed`; the
seed, generator hash, PCM/WAV hashes, and private receipt hash are then bound.
The proposer and its dependency closure cannot read the freezer, seed, receipt,
or manifest. A rerun is allowed only after a documented infrastructure failure
that occurred before proposer execution, and uses a new auditor seed.
The generator rejects, rather than clips, any rounded sample outside PCM16.
Every generated instance must fit wholly inside the 180-second array; the
private receipt records effective integer `start_sample` and `duration_samples`
for every instance and the freezer rejects any nominal/effective mismatch.

Order:

1. P0 12-second exact-language conformance (not a compression claim).
2. Auditor-seeded 180-second held-out modal PCM; the frozen P1 is development
   rehearsal only.
3. N1 180-second independent per-mode drift.
4. Only if steps 1-3 pass: N2 crossing fields, N3 phase-sensitive beating, N4
   per-instance phase/decay mutation, N5 overlapping unrelated fields plus
   noise/impulses, then the pinned EBU gong and grand piano.

Development P1 PCM SHA-256 is
`19b3645b577cdd5e2df7e696aa952ece3af803934ef95b07c76c250d230c667c`;
N1 PCM SHA-256 is
`098f32a9c2f13b851850038de86b9a8b8272d4935e07eebed6d9aeb50460d354`.
Every remaining PCM/WAV identity is bound by the frozen manifest. EBU WAVs are
used without resampling or channel conversion: gong is the pinned mono
44.1-kHz file; grand piano is unsupported stereo in S17 and must be exact S12
fallback. This deliberately tests the profile boundary without inventing a
conversion.

## Finite selector and metric tolerances

There is no unfrozen scalar lambda. Resources are hard caps. For each input,
the finite Pareto set contains direct S12 and every complete actual-decoder IMF1
candidate. A candidate is eligible only if all applicable quality axes from the
hash-bound `experiments/r216_s12_metrics.py:quality_axes` remain within these
predecessor-relative tolerances:

| Axis | Maximum regression |
|---|---:|
| SNR / SI-SDR / segmental SNR | 0.05 dB |
| STOI / ESTOI | 0.001 |
| log-mel / multiresolution STFT | 0.01 |
| magnitude cosine | 0.0001 |
| maximum absolute error | 1 sample unit |
| RMS error | 0.5 sample unit |
| log-spectral distance | 0.05 dB |
| mean/worst pre-echo error | 0.1 dB |
| phase MAE or RMSE | 0.001 rad |
| any unlisted numeric axis | `1e-9` in its adverse direction |

Among eligible candidates, lower complete bytes wins; ties use lower decode
operations, lower preroll, fewer modes, then lexicographically lower pack
SHA-256. Metrics only determine eligibility; they are never aggregated into an
unfrozen scalar.

## Hierarchical gates

### Long gate

All must pass:

1. P0 native/scalar PCM identity, parser rejection, transactional failure,
   operation-bound tests, and two-run stable pack hashes pass.
2. The auditor-seeded holdout selects model-on, uses at least six modes, reduces complete bytes by at
   least 10% versus accepted S12, passes every quality tolerance, and has zero
   model/residual/final clip count. Native and scalar IMF1 model PCM are
   byte-identical, native and scalar IMU1 model PCM are byte-identical to them,
   both the IMF1 and mechanically generated IMU1 pack hashes repeat across two
   runs, and actual IMF1 complete bytes are strictly less than actual IMU1
   complete bytes.
3. N1 either selects byte-identical accepted S12 or selects a candidate that
   independently passes the same complete-byte, decoder-identity,
   coordinate-sharing, and quality predicates; mere co-occurrence of peaks
   cannot force grouping.
4. cumulative long phase stays within 2,400 wall seconds, 7,200 CPU seconds,
   2 GiB peak RSS, and 512 MiB retained evidence.

Any failure ends S17 immediately. No short control, EBU input, S18 corpus, or
Opus execution follows.

### Focused completion gate

If long passes:

- N2 preserves both crossing fields or falls back; no track swap may reduce
  complete cost while violating phase/quality tolerances. If model-on, all four
  decoder identities, pack repeatability, and IMF1<IMU1 apply;
- N3 preserves decoder-domain beating or falls back; the same model-on identity
  and attribution predicates apply;
- N4 splits the mutated instance/Basis or falls back; the same predicates apply;
- N5 may model only the profitable modal component; impulse/noise remain Truth,
  all pre-echo/phase tolerances and model-on predicates pass, or the file falls
  back;
- grand piano is byte-identical S12 fallback because stereo is unsupported;
- EBU gong must select model-on, pass all decoder-identity/repeatability/
  IMF1<IMU1 predicates, and create a complete Pareto point beyond the frozen
  tolerances. Without this real-audio point S18 is not authorized;
- cumulative focused completion stays within 3,000 wall seconds, 9,000 CPU
  seconds, 2 GiB peak RSS, and 1 GiB retained evidence.

The executable allowlist is exactly:

- `native/include/resonith/inharmonic_field.h`;
- `native/src/inharmonic_field.cpp`;
- `native/tests/inharmonic_field_test.cpp`;
- `reference/maf_p0/inharmonic_field_oracle.py`;
- `experiments/r271_s17_inharmonic_field_gate.py`;
- `experiments/r271_s17_control_freezer.py`;
- added nonblank lines in `native/CMakeLists.txt`.

The baseline is commit
`e4e2b50c6f43fb26ebf8f9a2f8fa1b174ae61f66`. The freezer currently contributes
265 nonblank lines. New files are counted as nonblank physical lines; CMake is
counted as nonblank added lines from
`git diff --unified=0 <baseline> -- native/CMakeLists.txt` whose first character
is `+`, excluding `+++`. Any executable diff outside the allowlist rejects the
generation. The inclusive total is limited to 1,500 nonblank lines. JSON and
English evidence documents are excluded because they are not executable.
Retained artifacts are exactly manifest, source
inputs by reference, candidate/baseline packs, independently decoded WAVs,
machine JSON, hashes, commands, timing, work, memory, and failure receipts.

## S18 boundary

A focused pass is not an admitted codec improvement. It authorizes one full
19-item registered comparison against accepted S12 and frozen maximum-effort
official Opus 1.6.1 through actual decoders. S18 publishes complete per-file
and aggregate bytes, bitrate, every quality axis, spectral/phase/transient/
channel behavior, encode/decode time, CPU/GPU, peak memory, hashes, fallbacks,
wins, losses, regressions, and retained artifacts. Only S18 can admit S17.

## V1/V2/V3 audit remediation

The independent V1 audit returned NO-GO on SHA-256
`94205721c202f43e765653b5815aab2254ec737367e06cbbae5167782b106d7d`.
V2 resolves its blockers by removing detune/signed gain ambiguity, defining all
fixed-point operations and decay/seek behavior, closing Truth without hidden
clipping, limiting active modes, freezing complete records/offsets/termination,
removing the artificial S11 35% gate and dependency on future S33, freezing a
PCM-only non-exact P1 plus adversarial controls, splitting long/short gates,
bounding proposer enumeration, binding metrics/ties, requiring a real gong
Pareto point, and adopting measured inclusive resource ceilings.

The independent V2 re-audit returned NO-GO on SHA-256
`3a497d5925a82e3543ec45cda4c17be5a9a7215e9a2a714349f56511b644e401`.
V3 adds derived-step Nyquist and instance-containment validation, exact gain
interpolation, exact observer identities and bounded integer fitting, all
model-on decoder identity and stable-pack requirements, the actual IMU1
expanded-coordinate attribution arm, a non-aggregated selector, an
auditor-seeded post-freeze holdout, frozen EBU identities, and an exact
executable line-budget allowlist.

The independent V3 re-audit returned NO-GO on SHA-256
`c2d06ea244c5034baee62d29d19c9353a111c657acfaff8b259a9e5945bc40ee`.
V4 freezes the complete independently parsable IMU1 header and extent formula,
closes Q16/Q15 amplitude dimensions, defines phase unwrapping and decay against
the factored common envelope, forbids holdout clipping/truncation while
recording effective sample extents, and requires repeat hashes for both packs.

The independent V4 re-audit returned NO-GO on SHA-256
`ad8af0cf0bb2bd76e1ad158c4ee374d239125641a8b0933168ebed98f15f5b52`.
V5 derives Q32 phase step directly from Q20 frequency and sample rate, freezes
the inclusive decay endpoint/search procedure, and makes both-pack two-run
stability a global predicate for every model-on input.

During implementation, V5's `2 Q32 step unit` knot-thinning threshold was found
dimensionally disproportionate to a 180-second field and capable of rejecting
the hypothesis before complete Truth RDO. V6 removes only that redundant
eligibility threshold. The deterministic removal order and 256-knot bound are
unchanged; the error is reported, while actual complete bytes and every frozen
decoded-quality tolerance remain authoritative.

Implementation remains blocked until the independent auditor returns GO on the
exact V6 document and frozen manifest. Native parser/renderer work completed
before this finding remains quarantined from execution; proposer and audio
execution stay blocked until delta GO.
