# R-215 S11 Persistent Multi-Partial Predictor Preflight

Date: 2026-08-02
Status: **INDEPENDENT GO — FROZEN S11 IMPLEMENTATION AUTHORIZED**

## Decision question

Can the admitted R-191/R-203 anonymous complex-partial path union be lowered
into a small persistent decoder-domain predictor that reduces the one final
Truth enough to repay every predictor, container, state, checkpoint, runtime,
and memory cost?

This is the first codec-algorithm generation after S10. It changes no public
syntax in isolation. Admission requires the complete S12 registered-music
comparison against the immediately preceding accepted Resonith generation and
the frozen maximum-effort official Opus anchor.

## Frozen baseline and authority

- S10 admitted analyzer source commit:
  `1d0f6e86cded81fd156895574150b4f8f8e4d67b`.
- S10 publication commit: `ca87dec`.
- S10 evidence root: `G:\Resonith\artifacts\r213-s10-final`.
- Native R-191 path implementation SHA-256:
  `ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.
- The direct lapped Truth candidate remains a complete incumbent and can be
  selected without executing this predictor.
- R-191 continuity/value/protected scores order proposals only. They never
  authorize a predictor record or a compression claim.

## Measurable objective

For a complete independently decoded candidate (C), minimize

\[
J(C)=R_{container}+R_{basis}+R_{lifetimes}+R_{truth}
     +\lambda D+\mu W_{decode}+\nu M_{seek}.
\]

All rate terms are actual packed bytes. `D` is computed only from actual
decoder PCM. Decoder work, peak memory, startup, and seek dependency are
reported even when their weights are zero in the first research RDO.

An S11 candidate is eligible only if it is a new complete Pareto point against
direct Truth. A proxy-energy, track-recall, or analyzer-score improvement is
not eligibility evidence.

## Sources of truth and prior art

Checked online on 2026-08-02:

1. McAulay and Quatieri describe time-varying sinusoidal amplitude, frequency,
   phase, birth/death, and smooth phase interpolation. This validates the
   signal family but makes clear that sinusoidal tracking itself is not novel:
   <https://www.ll.mit.edu/r-d/publications/speech-analysissynthesis-based-sinusoidal-representation>.
2. Esterer and Depalle formulate global partial tracking with linear
   programming and report better high-noise tracking than the classical greedy
   method. This supports global path selection, not codec-byte benefit:
   <https://arxiv.org/abs/1901.05044>.
3. MPEG-4 parametric audio and HILN establish standardized harmonic,
   independent-line, and shaped-noise decoding. Their existence prevents a
   novelty claim for parametric lines and shows that a parametric vocabulary
   alone does not guarantee dominance:
   <https://www.mpeg.org/structure/audio-coding/>.
4. Serra's spectral-modeling implementation separates stable sinusoidal
   partials from a residual. It supports separate causal ownership rather than
   fitting noise and transients as lines:
   <https://mtg.upf.edu/static/libsms/doc/index.html>.
5. DDSP shows that physical DSP priors can be fitted with learned proposers,
   but it is synthesis/modeling evidence, not proof of small normative model
   bytes, exact reconstruction, or universal codec gain:
   <https://research.google/pubs/ddsp-differentiable-digital-signal-processing/>.
6. Project evidence R-180/R-183 found that a two-second vector-partial fit
   explained about 99.4% of event-domain energy but cost 1,620 raw MFT1
   records and 71,424 predictor bytes. The failure was repeated signaling, not
   lack of analytic fit.
7. R-191/R-203 now supplies deterministic, resource-bounded, permutation-
   invariant anonymous paths with cross-toolchain evidence. It still supplies
   no synthesis or byte RDO.

## Divergent alternatives and falsification

### A. No change: direct Truth only

Retained as the complete incumbent. It is simplest, universally applicable,
and avoids model overhead. It loses only when a persistent law actually repays
its complete cost.

### B. One frame-local fundamental and harmonic envelope

Rejected for S11. It is compact for one stable pitched source but fails under
polyphony, missing fundamentals, crossings, inharmonicity, phase cancellation,
and mixed transients. Harmonic grouping belongs to S33 after independent paths
exist.

### C. New persistent oscillator opcode now

Rejected. Existing bounded MFT1 type-8 Basis-warp instances and CBF1 ledgers
can test the hypothesis without freezing syntax. A new opcode before a real
complete-byte win would make a failed experiment expensive to remove.

### D. Independent anonymous R-191 paths lowered through existing DSP

Retained as the smallest coherent experiment. Each admitted lane has one
birth, one death, an initial phase, and piecewise-linear fixed-point frequency
and gain laws. It is an operational lane, not a claimed physical source.

### E. Joint source-filter, harmonic grouping, low-rank factorization, or
neural decomposition

Deferred. These can reduce shared parameter cost but confound whether
persistent independent paths work at all. Source-filter is S15, inharmonic
specialization S17, latent separation S31, harmonic bundles S33, and learned
proposers S49. Neural inference is encoder-only and cannot decide admission.

### F. Implement every MAF mechanism together

Rejected as non-falsifiable. A loss or regression could not be assigned to a
single causal mechanism, and complete tests would not identify which state or
metadata should be removed.

## Smallest coherent S11 language

For output channel (c):

\[
\hat x_c[n]=\sum_{p=1}^{P_c} a_{c,p}[n]\cos(\phi_{c,p}[n]),
\qquad
\phi_{c,p}[n+1]=\phi_{c,p}[n]+\omega_{c,p}[n].
\]

The finite S11 language contains only:

- native R-191 selected independent complex paths;
- arbitrary-sample birth and death derived from path support;
- piecewise-linear Q16 frequency step;
- piecewise-linear signed Q15 gain;
- one explicit initial phase and uninterrupted integrated phase thereafter;
- one shared immutable periodic integer cosine Basis;
- independent per-channel emitters and a one-hot static mix;
- one final mixture-domain lapped Truth;
- the complete direct-Truth fallback.

It explicitly excludes:

- phase-lock or sparse phase-innovation anchors, owned by S13;
- source-filter excitation, owned by S15;
- inharmonic specialization, owned by S17;
- stochastic and transient paths, owned by S19/S21;
- latent-source separation, owned by S31;
- harmonic grouping, owned by S33;
- cross-channel delay, polarity, or shared-route laws, owned by S35;
- new public syntax or decoder opcodes, owned by S51.

The word `source` in the panel title means a persistent anonymous causal lane.
S11 does not identify a speaker, instrument, note, or physical object.

## Frozen numeric language

S11 uses the frozen signed-PCM16 periodic cosine family with lengths
`{16, 32, 64, 128, 256}`. Complete integer tables, ascending length order, and
per-table PCM16LE hashes are frozen in
[`experiments/fixtures/r215_cosine_basis_family.json`](../../experiments/fixtures/r215_cosine_basis_family.json),
manifest SHA-256
`9880c8f4ad2ac36e5af5302299a8a6dbbe7416b8243f48c786db3a375c40a87c`.
The length-16 hash remains
`11989292026ed130c52b9b3be058460c2de11eece611e5639d410f93a2e96396`.
No table can be tuned after S12 without declaring a new algorithm generation.

The existing type-8 step bound is `abs(step_q16) <= 8 * 2^16`. For each lane,
the encoder chooses exactly once the longest frozen length for which every raw,
phase-corrected, interpolated, split, and tail endpoint step remains inside
that bound. The lane never changes length. A 16-sample period covers the full
Nyquist interval; longer periods reduce interpolation error where their
narrower frequency range permits. Only used tables are packed, deduplicated,
and assigned `basis_id` in ascending-length order. Lengths 512 and 1024 are
explicitly outside S11.

Every mapping uses signed nearest-integer rounding with exact ties to even:

- `frequency_hz_q20 = round_even(frequency_hz * 2^20)`;
- `step_q16 = round_even(frequency_hz_q20 * L * 2^16 /
  (sample_rate * 2^20))`;
- `phase_turn_u32 = round_even(((phase mod 2*pi) / (2*pi)) * 2^32)
  mod 2^32`;
- `source_position_q16 = round_even(phase_turn_u32 * L * 2^16 / 2^32)
  mod (L * 2^16)`;
- `channel_amplitude_q16 = round_even(max(0, amplitude) * 2^16)`;
- `gain_q15 = clamp(round_even(channel_amplitude_q16 / 2^16), 0, 32768)`.

The analyzer's floating values are evidence inputs; all graph and synthesis
records after this boundary are the fixed integers above. A conversion that
exceeds a field bound rejects that proposal rather than saturating silently.

## Lowering and decoder contract

- Every used frozen cosine Basis is stored once; unused family members are not
  transmitted.
- Every piecewise path segment lowers to one existing MFT1 type-8
  `BASIS_WARP_INSTANCE`.
- CBF1 may compress the exact same verified MFT1 event program. CBF1 and MFT1
  must decode to identical PCM.
- MFT1 limits remain authoritative: at most 64 emitters, 4,096 placements,
  65,535 samples per placement, eight output channels, bounded step/gain, and
  declared operations per frame.
- A path is split solely when a law knot or the 65,535-sample limit requires
  it. Every split is charged.
- Aggregate-channel observations are proposal evidence only. Every output
  channel obtains and quantizes its own complex amplitude and phase and pays
  independent emitter, law, and event records. Numerically equal channel laws
  are not shared in S11. The mix is static and one-hot per emitter. The
  authoritative bound is `sum(channel_path_counts) <= 64`;
  `floor(64 / channel_count)` is only the conservative cap when every graph
  path is cloned to every channel.
- Analysis windows, GPU tiles, and graph hops never appear as acoustic
  boundaries. Observation knots may be removed only by decoder-domain error
  and byte RDO.
- Each type-8 instance has absolute onset and closed-form phase, so its DSP
  needs zero acoustic preroll. CBF1 is only a research transport and may
  require bounded full-ledger validation and expansion before playback or
  seek. Expansion remains bounded by 64 emitters and 4,096 placements. S11
  adds zero checkpoint bytes, reports validation/expansion startup time, work,
  and memory in S12, and makes no normative random-access claim.

### Canonical one-past phase carry

Let `N` be the charged segment length, `p0` its Q16 source position, and
`s0`, `s1` its start/end Q16 steps. The next segment starts at:

- constant step: `p_next = (p0 + N * s0) mod (L * 2^16)`;
- linear step (`N >= 3`): compute
  `p_last = MFT_warp_position(p0, s0, s1, N - 1, N)` using the existing
  half-away-from-zero MFT law, then
  `p_next = (p_last + s1) mod (L * 2^16)`.

The modulo is Euclidean. Evaluating the closed law naively at index `N` is
forbidden because it is not the defined final in-range increment. This carry
is a state continuation only; it transmits no phase correction or hidden S13
anchor.

## Encoder algorithm

1. Run the admitted complex-partial observation union.
2. Convert observations into the exact R-191 packed fixed-point domain.
3. Run the admitted native R-191/R-203 graph and selected path union. S11
   eliminates nonzero `cycle_offset` duplicates in the encoder manifest: for
   identical source, target, and gap they alter no topology or phase term and
   only add `log2(1 + abs(offset))` cost. The frozen manifest therefore uses
   `cycle_offsets=(0,)` and a hard `250,000,000` work-unit cap.
4. Recover each path's ordered high-resolution observation evidence without
   changing the native selected identity.
5. Form independent per-channel lane proposals from channel complex values.
6. Thin interior knots with bounded dynamic programming. A removed knot is
   allowed only when the exact integer decoder render satisfies the declared
   error and phase-drift bounds.
7. Rank candidates only to schedule work. Add/remove decisions use actual
   predictor bytes plus the change in final Truth bytes and decoded quality.
8. Repack, independently decode, and recompute one final Truth after every
   retained subset edit.

The semantic path identity consumed by lowering is the canonical ordered
observation-ID sequence, including its fixed channel/resolution evidence. It
is not `candidate_id`, incoming edge ID, `path_id`, rank, or a packed-output
hash across different manifests.
9. Compare CBF1+Truth, MFT1+Truth, and direct Truth as complete files.

S11 starts with deterministic add/remove greedy selection plus exact subset
enumeration when the candidate count is within the existing declared bound.
It does not claim the unrestricted global optimum.

## R-186 free-oracle lower bound

The actual bounded decoder was run with the length-16 family member on a
12-second, 48 kHz changing-overlap
synthetic field with four anonymous partial lifetimes and 34 charged type-8
placements. The source PCM was produced by the same normative integer DSP, so
this is a representational-capacity lower bound, not analyzer evidence.

| Quantity | Measured value |
|---|---:|
| Direct lapped Truth | 119,854 bytes |
| Raw MFT1 predictor | 1,652 bytes |
| CBF1 predictor | 683 bytes |
| Zero final Truth | 3,797 bytes |
| RSC1 container and section overhead | 288 bytes |
| Complete CBF1 + Truth container | 4,768 bytes |
| Complete ratio versus direct Truth | 3.9782% |
| Complete saving versus direct Truth | 115,086 bytes |
| Predictor-plus-Truth decoded PCM | bit-exact |

Source and decoded PCM SHA-256 are both
`b40210aa19a14ad1c2e75345d0412c48ec6eeebf2f44fc894c8288cca682fc1b`.
The machine record is
[`experiments/results/r215_s11_free_oracle_2026-08-02.json`](../../experiments/results/r215_s11_free_oracle_2026-08-02.json).

The retained local artifacts are in
`G:\Resonith\artifacts\r215-s11-free-oracle`. The receipt records every
Basis, MFT1, CBF1, Truth, container, WAV, generator, and native decoder hash.
Its native decoder SHA-256 is
`f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed`.
The deterministic generator is
[`experiments/r215_s11_free_oracle.py`](../../experiments/r215_s11_free_oracle.py),
SHA-256
`9bf6ed3e998a3077d5632555e72710f53f6535572ddb9e2be5d8e25fe3cec8f5`.
The exact reproduction command is:

```powershell
python experiments/r215_s11_free_oracle.py `
  --native-core build/cpp23-clang22-ninja/libresonith_core_shared.dll `
  --basis experiments/fixtures/r215_cosine_basis_family.json `
  --basis-length 16 `
  --output-directory artifacts/r215-s11-free-oracle `
  --report experiments/results/r215_s11_free_oracle_2026-08-02.json
```

The independent predeclared structural threshold was complete bytes at or
below 85% of direct Truth with exact native decode. The measured 3.9782%
passes that threshold.

Two consecutive executions produced the identical machine-receipt SHA-256
`0b86b51d90e1be8c335103bdfb746ea408970706d88654c1452ea407bdd31668`.

This passes only the R-186 question of whether the bounded language can repay
itself on changing overlapping content that lies exactly in the language. It
does not predict path recovery, real-audio activation, Opus gain, or novelty.

## Counterexamples and mandatory behavior

| Case | Required behavior |
|---|---|
| Two unresolved close tones | preserve alternatives or reject to Truth |
| Symmetric crossing | score modulo path permutation; no source-identity claim |
| Abrupt phase reset | end/restart or Truth; S11 cannot smuggle an anchor |
| Fast vibrato beyond linear law | keep knots, split, or reject |
| Attack/transient | reject the line proposal when Truth grows |
| White or pink noise | report bounded proposals and normally fall back |
| Destructive cancellation | use complex channel evidence and final Truth |
| Opposite-polarity stereo | independent per-channel render or fallback |
| Path longer than 65,535 samples | charged continuous split with exact phase carry |
| More than 64 channel-lanes | deterministic cap plus explicit pruning report |
| More than 4,096 placements | fail closed to a smaller subset or direct Truth |
| Short input | charge complete Basis/container overhead; no long-only averaging |
| Corrupt predictor | existing bounded parser rejects before unbounded allocation |

## Falsifiable prediction and kill gates

Prediction: on clean evolving tones and at least one real tonal long input, the
native path-lifetime predictor will reduce final Truth enough to create a new
complete Pareto point. It is expected to fall back on noise and transient-only
inputs.

Kill or revise S11 before S12 if any of the following occurs:

- high-level observations cannot be converted to the admitted R-191 ABI
  deterministically and permutation-invariantly;
- the selected native path identity is altered by the lowering code;
- CBF1 and MFT1 predictor PCM differ;
- segment splitting changes continuous integrated phase;
- Python and native decoder PCM differ;
- a tile, channel order, or input ordering changes the canonical candidate;
- the candidate improves a spectral/energy proxy but enlarges final Truth and
  supplies no separately admitted matched-byte quality Pareto point;
- bounds are enforced by silent truncation rather than reported fallback;
- S11 requires a phase anchor, source label, harmonic grouping, separator,
  stochastic model, or new opcode to pass its base synthetic cases;
- focused synthetic gates find no nontrivial automatically recovered lane whose
  complete candidate beats direct Truth.

S11 remains experimental until S12. S12 rejects default promotion when the
full registered long-first manifest shows no retained Pareto point or an
unresolved quality, resource, portability, or decoder-identity regression.

## Minimal-sufficient claim ledger

| Claim | Existing or smallest test | Failure consequence |
|---|---|---|
| R-191 identity is consumed unchanged | native frozen path fixtures plus one real analyzer conversion | stop before synthesis |
| integrated phase is continuous across charged splits | one long chirp with split-boundary sample comparison | stop lowering |
| polyphony remains independent | two crossing chirps and one birth/death overlap | reject tracker/lowering |
| channel phase is not discarded | opposite-polarity and delayed stereo diagnostics | fall back; no stereo claim |
| CBF1 is transport-only | existing CBF1/MFT1 PCM identity test | reject CBF1 candidate |
| complete decoder loop is authoritative | actual native predictor and final-Truth decode | reject candidate |
| direct Truth cannot regress | existing candidate selector and fallback test | reject generation |
| bounds fail closed | existing MFT1/CBF1 parser/resource tests plus placement/emitter boundaries | reject generation |
| real improvement exists | S12 complete registered manifest and max-effort Opus | no admission |

No private ABI, test-only production hook, harness-of-harness test, or new
platform matrix is proposed. Focused S11 tests reuse the admitted public
research interfaces and native decoder. S12 is the only full music/Opus run
for this frozen generation.

## Evidence budget

- one new research predictor module;
- one focused test module covering the claim ledger without duplicate test
  infrastructure;
- one S11 focused machine report;
- one S12 complete comparison report and retained listening artifacts;
- no new decoder opcode, private C API, or CI workflow;
- one remediation cycle after the independent pre-implementation audit. A
  second design-level failure returns S11 for scope reduction rather than
  growing more tests.

## Independent audit result

The first independent audit returned conditional GO after five closures:
reproducible oracle evidence, frozen numeric language, exact split carry,
independently paid stereo laws, and corrected CBF1 startup/random-access
accounting. The same auditor then returned final **GO with no blockers** for
the frozen S11 implementation after independently checking preflight SHA-256
`4a39de0b053b658182d013272956c966265a34e31ec35171a4bb1274b822fc5a`,
the generator, Basis manifest, receipt, and all ten retained artifact hashes.

The auditor also checked both signed range edges. At 48 kHz, `+24,000 Hz` and
`-24,000 Hz` map exactly to the inclusive type-8 bounds `+524,288` and
`-524,288`; `+/-24,001 Hz` is rejected. The byte ledger independently closes
as `683 + 3,797 + 288 = 4,768` bytes.

Negative evidence is retained rather than hidden: a read-only one-second
997 Hz, amplitude-12,000 diagnostic produced a maximum predictor residual of
727 PCM and RMS 307.74. Actual lapped Truth grew from 572 bytes for zero Truth
to 8,126 bytes and the independent complete decoder consumed that correction.
The 16-point table is therefore only a bounded full-range command language;
its real-audio economics must be decided by complete RDO and S12.

The auditor separately returned conditional GO for the S11-only dominated
cycle-offset elimination. On the frozen crossing smoke, the full five-offset
manifest produced 4,755 edges and 170,645,887 work units; the zero-only
manifest produced 951 edges and 26,757,175 work units while preserving the
same selected 122-observation semantic sequence and selected-path count. This
does not claim packed-ID equality or universal bounded-top-K equivalence:
cycle duplicates can occupy a bounded frontier and change incidental IDs under
saturation or ties. The explicit 250,000,000 cap covers the frozen case and
any cap hit still falls back rather than expanding resources silently.

The first analyzer-recovered clean-tone smoke falsified the 16-only design: at
64 coefficients/frame it produced 3,320 bytes and SSE 943,135 versus direct
Truth 2,729 bytes and SSE 15,728,868; at 128 it produced 4,556 bytes and SSE
942,374 versus 4,229 bytes and SSE 15,724,667. It was a quality Pareto point
but a rate loss caused by interpolation residual.

The independently audited family remediation is therefore frozen before the
focused S11 report. On the same 440.3 Hz source, an actual native one-law
lower bound with the longest admissible length 128 produced 3,719 bytes and
SSE 0 at 128 coefficients/frame, versus direct Truth 4,229 bytes and SSE
15,724,667: 12.06% fewer complete bytes with exact decoded PCM. At 64 it
produced 2,885 bytes and SSE 0 versus 2,729 bytes and SSE 15,728,868, retaining
the useful quality Pareto point while direct fallback protects rate. The
independent verdict is **GO** only with one immutable length per lane, complete
length-parameterized phase math, canonical used-only packing, frozen hashes,
and no 512/1024 expansion.

This GO authorizes only the bounded S11 research generation above. It does not
authorize S13 mechanisms, public syntax, a compression claim, release,
publication, or default promotion.

## Decoder-coordinate phase-fit remediation

The final S11 remediation addresses one measured defect without changing the
selected native observation-ID path: copying noisy endpoint FFT frequencies
made one historical stable analyzer-recovered diagnostic require three
placements. Its reported 4,412-byte/SSE-915,414 result is retained only as
non-authoritative development evidence because the exact input, command, and
artifact identities were not persisted. It is not an admission baseline or a
passed kill gate. A read-only fit over the same ordered phase observations
showed that one uninterrupted type-8 law may be representable; only the current
reproducible focused receipt may decide that claim.

The independently audited implementation contract is:

- unwrap each channel's modulo Basis position only along the unchanged ordered
  native path; frozen measured-frequency prediction selects the integer cycle
  but cannot alter graph topology or path identity;
- reject a cycle when the best and second-best aliases are tied or separated
  by no more than the frozen quantized phase/frequency uncertainty;
- propose `start_step` and `end_step` with a deterministic two-parameter
  weighted integer normal equation for the exact continuous type-8 coordinate
  model
  `D*y = D*k*start_step + k*(k-1)*(end_step-start_step)`, where
  `D = 2*(N-2)`;
- quantize phase weights to unsigned Q12 using a frozen 0.01-radian floor;
  add two weak endpoint-frequency priors with frozen weight one and scale
  `D*N`; use ties-to-even division, a positive canonical denominator, a
  `determinant * 2^20 >= A*C` conditioning gate, and signed 512-bit
  accumulator bounds;
- treat the rational solve only as a proposer: after quantization and the
  existing common phase correction, rescore every observation and every
  split/tail/carry with `_warp_source_position_q16`, including its normative
  half-away-from-zero quadratic rounding;
- retain the previous endpoint fitter on ambiguity, bad conditioning, range
  failure, insufficient distinct times, or any frozen frequency, phase, gain,
  split, or one-past failure; retain direct Truth as the complete RDO fallback;
- transmit one initial phase and uninterrupted type-8 start/end steps only.
  No interior reset, anchor, per-knot phase record, or new opcode is permitted.

The historical conditional threshold above is superseded because it cannot be
reproduced from retained identities. The executable S11 admission gate is the
predeclared structural threshold: at least two of crossing, birth/death, and
gap/reappearance must retain a complete Pareto point; noise and transient must
fall back explicitly; transport/decoder identities must be measured; and an
actually model-active candidate must repeat with identical bytes, decoded PCM,
lane/support/Basis/instance evidence, and metric identity. The frozen one-law
lower bound 3,719 bytes/SSE 0 remains representational evidence, not analyzer
recovery. S11 remains experimental until the complete S12 comparison.

## Boundary-valid paid lifetime

The first implementation measurement exposed a separate deterministic defect:
centered analyzer windows padded beyond the source boundary underestimate edge
gain and must not define a paid synthesis lifetime. The independent auditor
returned **GO** for geometry-only support trimming under these conditions:

- run R-191 once on the complete evidence and preserve its path identity and
  full ordered observation-ID sequence; trimming never reruns or reselects the
  graph;
- an observation is eligible exactly when
  `center >= fft_samples/2` and
  `center + fft_samples/2 <= total_frames`;
- choose one maximal contiguous eligible run by maximum covered sample span,
  then observation count, earliest center, and lexicographic observation IDs;
  never bridge an ineligible interior observation;
- the paid birth/death is the first/last retained center plus a bounded tail
  derived from the last retained hop. Prefix, suffix, and rejected gaps remain
  exclusively final Truth; no edge extrapolation is permitted;
- record full and retained ID sequences separately. No unbiased-gain claim is
  made because leakage, interference, and off-bin bias can remain in otherwise
  valid windows; actual decoded PCM and complete Truth RDO remain decisive.

Permutation identity must cover the full and retained IDs, chosen support,
Basis length, instances, bytes, and decoded hash. This correction changes only
S11 birth/death proposal geometry and does not add syntax, phase anchors, or a
new source model.

## Exact constant-span tail fusion

The independent auditor returned **GO** for one final lowering correction. A
separate tail record may be fused into its immediately preceding constant law
only when the records are adjacent; emitter, Basis, circular mode, and gain are
identical; the preceding step and gain are constant; the combined count is no
greater than 65,535; continuation satisfies the last retained observation's
frozen frequency and all type-8 bounds; the one-past phase at the old boundary
is unchanged; and no rejected gap or boundary-invalid support is crossed.

This is not a byte/PCM-identical refactor: the tail predictor may change, so
Truth and complete RDO must be recomputed. The focused receipt must expose
before/after placement counts, the old-boundary phase identity, complete
predictor/Truth bytes and SSE, CBF1/MFT1 identity, and repeat hashes for a
model-active candidate. If complete RDO does not retain the fused form, direct
Truth or the unfused alternative remains authoritative.
