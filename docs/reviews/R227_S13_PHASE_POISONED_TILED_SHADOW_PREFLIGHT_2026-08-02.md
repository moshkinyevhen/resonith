# R-227 S13 phase-poisoned tiled-shadow preflight

Date: 2026-08-02

Status: **PRE-CODE CANDIDATE; IMPLEMENTATION AND EXECUTION NO-GO PENDING
INDEPENDENT AUDIT**

## Decision boundary

R-227 is the single permitted amendment to the R-224 Stage-1 experiment. It
tests one question without changing Resonith syntax or decoder behavior:

> On an otherwise phase-blind anonymous partial field, does replacing an
> already charged absolute type-8 start position at sealed knot boundaries
> reduce the complete decoded final-Truth representation by enough to justify
> further phase work?

This is an existing-syntax encoder experiment. It cannot authorize an opcode,
public API, product version, default, release, Opus rerun or quality claim.
Failure completes S13 as a measured no-change result and advances the continuous
panel to S15.

## Claim ledger

| Claim under test | Existing public behavior | Controlled risk | Evidence | Failure consequence |
| --- | --- | --- | --- | --- |
| later phase has causal byte value | complete MFT1/CBF1 decode | a phase-aware search could leak the answer into support | poisoned phase-free eligibility digest plus paired arms | kill S13 |
| the experiment is bounded on long input | no unbounded decoder or parser work | the R-186 monolithic observation cap rejects every declared input | twelve-second target tiles with one fixed resolution and no cross-tile edge | stop the run |
| a reset costs no new syntax width at fixed placement count | type-8 already carries `source_position_q16` | calling an existing field free could hide complete rate | charge actual predictor, wrapper and Truth bytes | reject the rate claim |
| quality comes from actual Resonith decode | native Core is decoder authority | a NumPy render could disagree with shipped arithmetic | decode every complete candidate through the frozen DLL | reject the arm |
| results generalize beyond a synthetic tone | three complete real long inputs | a positive control could satisfy a success count | all three real inputs must independently qualify and pass | kill S13 |

No additional test infrastructure is authorized unless it closes one of these
five observable gaps.

## Sources of truth and negative evidence

The experiment is constrained by the project implementation plus the primary
sources indexed in `docs/REFERENCES.md`:

- McAulay-Quatieri sinusoidal tracks establish amplitude, frequency and phase
  trajectories as prior art;
- Serra-Smith spectral modeling and PARSHL establish deterministic partials
  plus a residual or stochastic component;
- MPEG-4 HILN establishes phase-continuous parametric lines as prior art;
- the fixed Opus comparison is negative evidence that waveform/phase fidelity
  does not by itself imply perceptual spectral efficiency;
- R-215 proves the existing type-8 language and native decode path;
- R-221 proves the current fixed Opus comparison;
- R-224/R-226 prove that every registered S12 Resonith payload was the direct
  lapped-Truth predecessor, not an admitted persistent-partial stream.

The proposal therefore claims no novelty for phase tracking or phase locking.
Its only hypothesis is complete-description economy in this bounded existing
language.

## Alternatives and falsification

### A. No change

Stop phase work and proceed to anonymous multi-source fields. This wins whenever
the paired experiment fails its frozen gate.

### B. Raise the monolithic R-186 cap

Rejected. The four declared upper bounds are 28,405,440, 5,030,688, 46,659,024
and 28,350,336 observations. Raising a cap would hide the memory defect rather
than test phase economy.

### C. Reuse the S11 graph and lowering

Rejected. S11 reads phase uncertainty in edge scoring, reads observed phase
during span fitting and knot thinning, and corrects frequency endpoints to
close phase. Its support is not phase blind.

### D. Fit a free per-sample phase trajectory

Rejected. Phase and frequency obey `omega = d(phi)/dt`; varying phase while
freezing frequency is either a discontinuous reset or an undisclosed frequency
law. An unbounded trajectory is a second signal, not an oracle for one fixed
field.

### E. Tiled phase-poisoned shadow with paired start positions

Selected. It uses identical phase-free support, frequency, gain, Basis, knots,
placements, route, residual coder and native decoder in both arms. Only the
already present absolute position at a sealed retained-knot start differs.

## Frozen repository and tool authorities

The preflight starts from branch `codex/maf-r193-alpha` and parent commit
`6fbc459258dfad4961a5e5ad4011b0e4788f79ae`. The implementation commit and
runner hash must be recorded before execution. The following current inputs are
frozen for the audit:

| Authority | SHA-256 |
| --- | --- |
| `reference/maf_p0/persistent_partial_field.py` | `583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec` |
| `reference/maf_p0/complex_partial_analyzer.py` | `c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c` |
| `reference/maf_p0/partial_graph_fixed.py` | `8a692d9d5894049277ae543b10e29c93ea1466cb4c2b648befd7349683f982bc` |
| `reference/maf_p0/lapped_oracle.py` | `e89cc95a10bf80d8de390807616c678535230aec4736364876dccf7acb1ab908` |
| `reference/maf_p0/maf_typed.py` | `f3cd7fc71f2fff24b3ef07841adf6ffa07a40f83fb82de8370c186b463098fc5` |
| `reference/maf_p0/causal_basis_field.py` | `8c5863a5ea2c2c11f7cdeb3a678f05e0041dd5967da15bf6cb56799c6c3a2b2a` |
| `reference/maf_p0/causal_basis_truth_candidate.py` | `744b1589121d1b8785505b5eee6cf260ced0b7fdada9e641737be15614a97875` |
| `reference/maf_p0/native_core.py` | `32c514e5c9cf4f1beffba61c62d262489f35e2fb0c2e74c3cfdae2a132694045` |
| `experiments/r216_s12_metrics.py` | `ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3` |
| `experiments/objective_audio_metrics.py` | `284e27fca406775e90f0c0db075808b5203c9075600ccebf090e0065cb1c9bc5` |
| frozen native Core DLL | `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed` |

The runtime is the retained CPython 3.14.6 executable used by R-224, with NumPy
2.5.1, SciPy 1.18.0, soundfile 0.14.0 and pystoi 0.4.1. The controller records
the executable and imported-module origins and hashes before and after the run.
Any authority drift is terminal; there is no retry with a changed environment.

## Frozen long-first inputs

Execution order is normative for this experiment.

| Order | Input | File identity | PCM identity | Geometry | Direct-Truth configuration |
| ---: | --- | --- | --- | --- | --- |
| 1 | `G:\Orkela\comparison\public-benchmark-2026-07-26\mozart-original.wav` | 76,948,396 bytes; `f9bcc829c8c61e850c8a15d7d25ec600a904b2041ed3bb4d9e13131ea30a5a6f` | `c63dfcb59c384ef2f74cfb5edada31af9b7f25d3aa8706e0eb2fd41e06f0ae10` | 48 kHz, 2 ch, 19,237,088 frames, 400.772667 s | 72 coefficients, half-window 512, 24 bands |
| 2 | `G:\Resonith\artifacts\corpus\librispeech-r220\librispeech-speaker-long-5min.wav` | 10,220,204 bytes; `0191f7d14edfc27ec9f0354adc9cbba77fc2482c5fd09505ffc5463ecb7316c8` | `335384eab75a6a092adf5003c732a44b8a0ff9d4e710c3e8897d626f224d1b7f` | 16 kHz, 1 ch, 5,110,080 frames, 319.38 s | 68 coefficients, half-window 512, 24 bands |
| 3 | `G:\Resonith\artifacts\corpus\r227-stage1\elephants-dream-full.wav` | 126,397,484 bytes; `1c481a6013aa58d96e9ff00d1b85dd11875b28e7ce46b2a92e480c649362bae3` | `b674b0f66cb5dc58521704bc5fb145b382dbf6cc2906245e40b5a128e15f177b` | 48 kHz, 2 ch, 31,599,360 frames, 658.32 s | 71 coefficients, half-window 512, 24 bands |
| 4 | `G:\Resonith\artifacts\corpus\r227-stage1\synthetic-bounded-vibrato-600s.wav` | 57,600,044 bytes; `c4608c0a77cc073767aa9b56a2e431637e14ad63b131ac3c3138a986d0e940bc` | `592f704ac2a6bcbad28a86cf00577e9c1b61d8c5eef4b2bca9d1123303b83766` | 48 kHz, 1 ch, 28,800,000 frames, 600 s | 72 coefficients, half-window 512, 24 bands |

The local identity manifest is
`G:\Resonith\artifacts\corpus\r227-stage1\source-identities.json`, SHA-256
`173b3c8c773a3152358dbe542bca53aa839999a2813fe3a8dbaeec63ac376f88`.
It is evidence, not a repository dependency.

Every direct and residual Truth call uses `entropy_backend="bounded"`,
`transform_backend="fixed"`, `density_backend="adaptive"`,
`selection_backend="energy"`, `frame_whitening=0.0` and
`band_whitening=0.0`, with the per-input coefficient/window/band tuple above.
The frozen native DLL is passed as both analyzer and decoder.

The synthetic control is actual native MFT1 decode. Its source program has
SHA-256 `c9d8cbdee95b185ef5faca084c2b6945e59a302e23e6aed6d160915325ebf04c`:
a length-256 frozen cosine Basis, 600 one-second type-8 placements, alternating
432-to-448 and 448-to-432 Hz laws, gain Q15 12000, and a one-eighth-cycle
position innovation before every thirtieth placement except zero. It tests
sensitivity only and cannot satisfy a real-input success count.

## Exact tiled observation law

Only one existing R-186 resolution is used:

- sample rates at least 32 kHz: FFT 8192, hop 2048;
- lower sample rates: FFT 2048, hop 512.

Let `H` be the hop, `N` the frame count and `T = 12 * sample_rate`. Target
boundary `k` is round-to-nearest-even(`k*T/H`) times `H`, clamped to `[0,N]`;
duplicate terminal boundaries are removed. Cores are half-open consecutive
intervals `[B_k,B_(k+1))`. A core owns exactly global centers `c` such that
`B_k <= c < B_(k+1)` and `0 <= c < N`.

Each analysis slice is `[max(0,B_k-4096), min(N,B_(k+1)+4096))`. Its start is
rounded down to a hop boundary and its end is rounded up to a hop boundary
before clamping. The 4096-sample halo is at least one half-window for both
resolutions. Local centers are mapped back to global centers; observations
outside the owning core are discarded. Duplicate global identities, a missing
expected center, a non-hop-aligned interior slice or any cross-core edge is a
terminal error.

The existing R-186 peak detector runs with 24 logarithmic bands, two candidates
per band, 48 observations per aggregate-detector frame, 3 dB minimum SNR, 6 dB
phase SNR and 1.5-bin Rayleigh separation. Only aggregate detector
`detector_channel=-1`, locally resolvable observations with positive amplitude
lower confidence enter the shadow. Per-tile `maximum_observations` is the
unchanged 3,500,000 cap; it is never raised.

## Phase-poisoned shadow record

Immediately after observation, each admitted row is split into two immutable
tables. Within each aggregate-detector frame, `candidate_rank` is the zero-based
order emitted by the frozen R-186 analyzer after its own deterministic
frequency ordering. The canonical global observation ID is the four-integer
tuple `(fft_samples, hop_samples, global_center // hop_samples,
candidate_rank)`. Duplicate tuples are terminal. Canonical JSON arrays of these
integers are used in every digest; no local slice observation ID survives.

The **phase-free table** contains only global ID, global center, frame index,
FFT/hop, frequency Q20, frequency-uncertainty Q20, aggregate and per-channel
gain Q15, gain uncertainty Q15, confidence, resolvability, ambiguity identity
and provenance. It contains no aggregate phase, channel phase, phase
uncertainty, `phase_usable` flag or derived phase score.

The separately sealed **phase table** contains global ID, per-channel phase
turn U32, per-channel phase uncertainty and usability. Its object is not passed
to matching, tracking, support, knot selection, Basis selection, lane ranking
or subset enumeration. The phase-free eligibility manifest and SHA-256 are
committed before the phase table is opened. Phase usability may reject a whole
already sealed channel lane; it cannot prune, split, reorder or change it.

Negative tests poison every phase value while requiring byte-identical
eligibility, path, support, knot, Basis, lane-order and subset-enumeration
digests. They also reject direct or indirect phase-table access before sealing.

## Deterministic phase-free tracker

Tracking is adjacent-frame and one-to-one within one tile. It uses no gap and
no cross-tile continuation. Frequency and gain are integer coordinates:

- `frequency_q20 = round_even(frequency_hz * 2^20)`;
- `frequency_uncertainty_q20` uses the same conversion;
- aggregate gain is `min(32768, round_even(max(0,
  normalized_detector_amplitude)))`;
- each channel gain uses the same saturating nonnegative conversion;
- uncertainty is rounded and saturated to the same integer gain domain.

An edge is eligible when:

- frequency error is at most `max(2 Hz, 3 * max(endpoint uncertainty))`;
- aggregate-gain error is at most `max(8, ceil(0.18 * max(endpoint gain,1)),
  3 * max(endpoint gain uncertainty))`.

For an eligible edge let `ef` and `eg` be the integer frequency and gain errors
and `lf` and `lg` their positive limits. Its exact score is
`(round_even((ef << 20) / lf), round_even((eg << 20) / lg),
previous_track_id, target_global_observation_id)`. Eligible edges are sorted by
that tuple. Greedy one-to-one admission in that total order is deterministic.
Track IDs are assigned monotonically in canonical global-observation-ID order
at the first owned frame and at each later unmatched birth. A matched target
keeps its source track ID; an unmatched source ends. No frequency crossing
heuristic, semantic label, phase continuity or future frame changes the order.

A channel track qualifies only if it spans at least one second, contains at
least eight observations and stays inside one tile. Its phase-free energy test
uses channel gains `g_i`, adjacent spans `s_i` and tail length
`t=min(tile_end,last_center+hop)-last_center`:

`lane_energy_numerator = sum(s_i*(g_i^2 + g_i*g_(i+1) + g_(i+1)^2))
                         + 3*t*g_last^2`.

The complete routed-channel denominator is the integer PCM16 sum of squares
`source_energy`. Qualification requires
`1000*lane_energy_numerator >= 6*source_energy`. This is the exact integer test
for at least 0.1% under the frozen linear-gain/cosine mean-energy estimate; no
phase, source label or cross-channel aggregation enters it. This deliberately
makes R-227 a conservative local falsification, not the future gridless S26
field.

## Phase-free knot and Basis law

For each qualifying channel track, Basis lengths are tried in the frozen order
256, 128, 64, 32, 16. A dynamic program minimizes actual charged type-8
placements. A span is feasible only when its linear frequency and gain laws fit
every phase-free retained observation inside the same frequency/gain bounds
used by the tracker and every step stays inside the current type-8 domain.
Ties are broken by total normalized frequency/gain error, earlier predecessor
index, Basis order, track ID and channel.

The `MAX_WARP_INSTANCE_SAMPLES=65535` split law is applied during costing, so
the DP charges every required automatic placement. At most six channel lanes
per complete input enter RDO. Up to four use exhaustive nonempty subset
enumeration; more use the same deterministic energy prefixes as S11. A sealed
subset ID is the lexicographically sorted tuple of
`(track_id, channel, basis_length)` lane identities. Energy, lane order, subset
order, support, knots, gain, frequency, Basis and placement count are sealed in
the phase-free digest.

The phase-blind carry arm alone selects one comparison identity. For each
subset it chooses transport by `(complete_bytes, predictor_transport_id)`, where
CBF1 is ID 0 and MFT1 is ID 1. Across subsets it chooses by
`(complete_bytes, decoded_SSE, sealed_subset_id, predictor_transport_id)`. The
objective-reset arm must use that exact subset and transport; it cannot
reselect either. Other sealed pairs are diagnostic only and cannot satisfy
admission.

Phase usability is opened only after complete lane and subset-enumeration
digests are sealed. If a required knot in the selected comparison subset is
unusable, the complete input is ineligible; phase cannot remove or reorder a
lane or subset.

## Paired existing-syntax arms

For each sealed subset, the two arms differ in one field only.

### Phase-blind carry arm

Observed phase initializes `source_position_q16` only at lane birth. Position
then advances solely through the sealed type-8 frequency law. Every retained
knot and every automatic 65535-sample split starts at the exact prior decoded
one-past position.

### Objective-reset arm

At a sealed retained-knot placement start, `source_position_q16` is replaced by
the exact observed channel phase mapped through the existing Basis period.
Automatic 65535-sample splits still carry the prior decoded one-past position
and create no reset degree of freedom. The only independently changed values
are `source_position_q16` at retained-knot starts. A later automatic split may
differ between arms only as exact one-past propagation of the preceding
retained-knot reset.

Both arms keep identical frequency and gain laws, Basis payloads, channel
routes, support, knot times, placement count, subset order, lapped-Truth
configuration, entropy backend and decoder. Phase reset does not pretend to
keep instantaneous frequency continuous; it is explicitly a discontinuous
absolute-position hypothesis in the existing type-8 record.

## Actual byte and decoder authority

Every predictor is packed as actual MFT1 and decoded by the frozen native Core.
Its PCM must equal the CBF1 predictor rendering sample for sample. The source
minus decoded predictor is encoded with the frozen direct lapped-Truth
configuration and wrapped as an actual complete existing-syntax candidate.
The complete candidate is decoded again through the native Core; the reported
evaluation PCM is that output only.

The ledger records MFT1 bytes, CBF1 predictor bytes, container/wrapper bytes,
compressed final-Truth bytes and complete bytes. Selection uses complete bytes
then decoded SSE then sealed subset identity. The four-byte absolute-position
field is reported for attribution but is never subtracted. Direct Truth is a
real executed arm. Production exact S11 is invoked once per input only as a
deterministic bound check. It must reject before observation allocation under
the unchanged 3,500,000-observation cap. Record the calculated upper bound,
rejection reason and absence of an output payload. This expected bound
rejection has status `NOT_EXECUTABLE_UNDER_FROZEN_BOUND`; it neither stops the
phase-shadow input nor participates in selection or admission. Unexpected S11
success is authority drift. Any decoder mismatch,
unaccounted byte, different placement count between paired arms, or non-native
evaluation PCM stops the input.

## Metrics and tolerances

The exact R-216 zero-lag metric implementation and `quality_axes` directions
are used. This includes waveform SNR/SI-SDR/segmental SNR and error, log-spectrum,
log-mel, multiresolution STFT, transient pre-echo, speech STOI/ESTOI when
applicable, per-channel phase, interchannel phase, correlation and mid/side
error.

For stereo only, interchannel delay is estimated separately for source and
decoded PCM after subtracting each channel mean. Let
`L=min(round_even(0.2*sample_rate), frames-1)`. For lag `d >= 0`, correlate
left `[0,frames-d)` with right `[d,frames)`; for `d < 0`, correlate left
`[-d,frames)` with right `[0,frames+d)`. For every integer lag in `[-L,L]`,
the score is `dot(left,right) / sqrt(dot(left,left)*dot(right,right))`. A zero
denominator makes the axis inapplicable. Select maximum correlation, breaking
exact ties by `(abs(lag), lag)`. The metric is
`delay_error_samples=abs(decoded_lag-source_lag)` with direction `min` and the
same relative `1e-12` tolerance as every other axis. Applicability mismatch is
terminal. The implementation resides in the one R-227 runner and its hash is
sealed at the implementation audit before long execution.

For admission, the objective-reset decoded point must not regress against the
phase-blind decoded point on any applicable axis by more than
`1e-12 * max(1, abs(reference_value))`. The required strict Pareto improvement
is supplied by rate, not by demanding a quality increase from an equal-quality
candidate. It must also produce no new clipping. A metric applicability mismatch
is failure, not an omitted comparison.

## One-shot execution and resource bounds

Each input runs once in its own subprocess, in the frozen long-first order.
There is no blind retry. Candidate arms execute sequentially; source PCM and
candidate payloads are never duplicated merely for parallelism. Each child is
bounded to 4 GiB peak RSS, 8 GiB working storage and wall time
`max(1800, 12 * duration_seconds)` with an 8000-second hard ceiling. The whole
run is bounded to 12 GiB retained evidence and one implementation-remediation
cycle. A second design or resource failure kills S13.

The receipt records CPU and wall time, peak RSS, accelerator use, disk
high-water, all authority hashes, tile/observation/lane counts, eligibility
digest, every rejection, all arm byte ledgers, decoded hashes, metrics and
directional deltas. Atomic output is committed only after the input completes.

## Admission and kill gate

R-227 passes Stage 1 only if **each of the three real long inputs**:

1. has at least one sealed qualifying channel lane;
2. gives the objective-reset arm at least 10% fewer compressed final-Truth
   bytes than the phase-blind arm on the carry-selected subset and transport;
3. produces a complete-byte point no larger than phase blind;
4. passes the decoded quality, channel and clipping rules above; and
5. completes inside every declared resource and identity bound.

The synthetic input must detect its known periodic phase innovations and show
the expected direction of residual-byte improvement, but it never substitutes
for a real pass. Direct Truth remains the executed baseline; production S11 is
reported only as `NOT_EXECUTABLE_UNDER_FROZEN_BOUND`. The
experiment does not claim victory over Opus; the fixed R-221 Opus data are
context only until an admitted algorithm candidate reaches S14.

If any real input is ineligible or fails, S13 closes as rejected/no-change.
Thresholds, tile size, tracker bounds and success counts are not tuned after
results. No second phase mechanism is introduced to rescue the hypothesis.

## Focused contract tests before long execution

One test module is sufficient and must cover:

1. hop-aligned ownership at the first, interior and terminal tile;
2. identical observations for a synthetic partial wholly inside a tile versus
   monolithic analysis at the same single resolution;
3. no duplicate center, global ID, edge or placement across tile boundaries;
4. phase poisoning leaves every phase-free digest byte identical;
5. frequency/gain mutation changes eligibility as expected;
6. a known reset changes no independent field except `source_position_q16`;
   every non-knot position difference must equal exact one-past propagation
   from the preceding retained-knot reset;
7. automatic split positions always carry and never read observed phase;
8. unusable phase rejects a whole lane only after sealing;
9. actual MFT1 and CBF1 predictor PCM identity;
10. actual complete native decode and byte-ledger closure;
11. timeout, memory, authority drift and partial-output fail closed; and
12. the synthetic positive control distinguishes carry from reset.

The test count is structural, not combinatorial. It does not authorize another
harness or private ABI.

## Required independent decisions

1. A read-only independent auditor must return binary GO on this exact
   preflight before code.
2. After the smallest runner and focused test exist, a different or re-used
   independent auditor must return binary GO on implementation conformance
   before the first four-input execution.
3. After execution, an independent result audit is required before S13 is
   accepted, rejected or advanced.

Until the first decision is recorded, implementation and execution remain
**NO-GO**.
