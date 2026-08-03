# LSPF Master Execution Plan

Status: **ACCEPTED execution order / NORMATIVE-DRAFT gates**  
Decision: R-161  
Last update: 2026-07-27

## 1. Mission

Complete the Latent Source Pattern Field before unrelated architecture work:

\[
X_c[n] =
\sum_s Route_{c,s}\left(
Convolve(
Transform(Basis_s,\Theta_s),
Excitation_s
)
+ Stochastic_s
+ Transient_s
\right)
+ Truth_c[n].
\]

The encoder searches anonymous decoder-verifiable fields. It does not need to
identify a speaker, instrument, note, phoneme, or environmental class.

The governing causal interpretation is:

```text
Pressure_c(t) =
  sum_s Route_c,s(Resonator_s(Excitation_s, State_s))
  + Truth_c(t)
```

Excitation may be coherent/quasiperiodic, sparse-transient, or stochastic.
Resonant state carries partial bundles, source-filter/formant laws, decay,
modulation, and short stable body/room responses. Routes carry bounded delay,
gain, phase, channel covariance, and propagation filters. These mechanisms are
identified at micro, meso, and macro scales; semantic source names are not
required.

The project succeeds only when structure lowers complete bytes at the required
decoded quality. Explained energy, separation scores, semantic confidence, and
visual similarity are diagnostics, not admission criteria.

## 2. Frozen invariants

1. One bounded deterministic integer decoder.
2. One final mixture-domain Truth correction.
3. Independent Truth remains available everywhere.
4. Semantic and learned systems are proposer-only.
5. No arbitrary program, graph, shader, or per-sample neural inference in the
   bitstream.
6. Gridless meaning; CUDA/entropy/checkpoint tiles are execution details.
7. Every transform has finite syntax, operation, memory, dependency, and random
   access bounds.
8. Lossless reconstructs exact PCM.
9. A new mechanism cannot make the selected stream larger.
10. Python is a non-shipping experiment controller; scalable kernels are native.

## 3. Work package WP-1 — Convolutive anonymous fields

### Implementation

- Replace stationary `W * H` factor proposals with finite non-negative matrix
  factor deconvolution:

  \[
  V[f,t] \approx \sum_{s,\tau} W_s[f,\tau]H_s[t-\tau].
  \]

- Preserve mixture phase through normalized soft masks.
- Share factor masks across channels while retaining channel phase and route
  evidence.
- Search multiple declared factor counts, convolution depths, FFT sizes, hops,
  initializations, and fixed iteration counts.
- Retain stationary NMF, direct observed channels, reversible lifting bands,
  and independent Truth in the proposer union.
- Feed every anonymous factor into the same gridless multiscale Basis search.

### Tests

- known two-source convolution mixture;
- changing-overlap mixture with no repeated complete mixed block;
- phase cancellation and counterphase stereo;
- boundary shifts at every sample residue;
- exact final-Truth identity;
- stationary-NMF ablation;
- known-stem upper bound versus blind inference.

### Gate

- synthetic complete-stream reduction of at least 15%;
- blind structured bytes within 15% of the known-stem oracle;
- no direct-channel recall regression;
- deterministic result under execution tiling changes.

## 4. Work package WP-2 — Bounded transform orbits

### Decoder laws

- zero-filled integer alignment;
- bounded fractional phase;
- constant and linear gain/envelope;
- constant and linear source step for pitch/time;
- bounded formant/spectral-envelope warp;
- stable short route/filter law;
- polarity, crop, forward/reverse, and loop where separately admitted.

### Encoder

- fit the complete declared local lattice on C++23/CUDA;
- use coarse learned or spectral proposals only to order work;
- verify every retained transform with the normative integer renderer;
- merge repeated parameter deltas into persistent laws;
- compare one transformed Basis plus final correction against independent
  Truth and a new Basis.

### Gate

- exact CPU/GPU parity for every candidate and rendered sample;
- no circular finite-Basis wrap;
- no fractional-phase or formant claim without an independent conformance
  vector;
- lower correction entropy, not merely lower squared error.

## 5. Work package WP-3 — Persistent physical-law competition

Every observed or anonymous field receives one local representation contest:

- transformed immutable Basis;
- coherent harmonic partial bundle;
- deterministic bounded-inharmonic partial bundle;
- persistent source-filter with excitation and vocal-tract/resonator law;
- stochastic field with counter seed, envelope, density, modulation, and
  channel correlation;
- transient event with independent onset support;
- cross-channel route/decay law;
- direct sparse or transform Truth.

Only one primary representation owns a coefficient/sample region. Families do
not stack full residual streams. They may overlap additively in time and
frequency, but selected lanes are summed before one final mixture-domain Truth.
Linear reinforcement and cancellation are reproduced by complex phase and
route laws; unexplained nonlinear interaction remains Truth.

### Gate

- speech: persistent filter and excitation state must beat blockwise LPC/Truth;
- noise and ambience: stochastic law must reduce correction entropy;
- transient corpus: no pre-echo or attack smearing at the quality floor;
- stereo: shared route must beat independent channels by complete bytes.

## 6. Work package WP-4 — Long sparse grammar

### Syntax

- canonical causal event streams over Basis/partial state, arbitrary gap,
  pitch, phase, gain, formant/envelope, decay, and channel route;
- separate ordered ledgers for harmonic, bounded-inharmonic, transient,
  stochastic-law, and route lanes so simultaneous causes never overwrite one
  another;
- one event clock per lane; factorized numeric laws reference shared event
  ordinals/lifetimes and never repeat the same timeline column;
- independent timing, pitch, phase, gain, envelope, resonator, and route
  atlases inside each lane; a mismatch in one law cannot prune repetition in
  another;
- exact suffix-automaton indexes over every event origin for literal,
  constant-offset, first-difference, and bounded second-difference laws;
- every automaton end-position class retains its complete repeated substring
  length interval rather than a few hand-picked motif sizes;
- multiple motif definitions in one stream;
- arbitrary-gap ordered event DAG;
- unrelated and overlapping events remain independent;
- hierarchical `CompoundBasis` references;
- literal, constant, affine, run-length, and sparse-exception laws;
- exact placement, route, gain, phase, source-step, and filter-state series;
- bounded grammar depth and dependency span.

### Selection

- enumerate each declared suffix-automaton interval lazily in global RDO;
- compose independently reusable laws through a bounded synchronized grammar,
  pricing shared lifetime and sparse exceptions instead of requiring one
  all-coordinate token;
- enumerate finite path candidates;
- activate dictionaries and motif definitions globally;
- permit direct long Basis and bottom-up compounds simultaneously;
- solve the bounded small-family chart exactly;
- use column generation/beam ordering only when the exact declared family bound
  is exceeded, with all pruning reported.

### Gate

- every grammar stream independently decodes and corruption-checks;
- every selected macro is cheaper than its expanded event ledger;
- multiple simultaneous definitions beat the best single definition;
- random access remains within the declared checkpoint pre-roll.

## 7. Work package WP-5 — Entropy-driven global RDO

The objective prices:

- immutable Basis payloads;
- transform, route, and law parameters;
- event and motif ledgers;
- persistent state;
- entropy contexts;
- checkpoints and dependency indexes;
- final Truth;
- decoder operations and persistent memory.

Lossless:

\[
J = CompleteBytes,\quad \hat X = X.
\]

Lossy:

\[
J = CompleteBytes + \lambda D,
\]

but rate comparison occurs only among candidates satisfying every applicable
R-118 quality floor.

### Gate

- real lossless median at least 5% below the best Truth/FLAC path before syntax
  promotion;
- first perceptual promotion at no more than 90% of matched-quality Opus bytes;
- research target: 60% of Opus bytes on structured speech and music, never a
  universal guarantee;
- every loss and fallback remains published.

## 8. Work package WP-6 — Native Foundry

### Product boundary

- C++23 portable analysis and exact reference fit;
- CUDA batched convolution, transform, route, and correction-cost kernels;
- unchanged small bounded integer decoder on CPU/mobile DSP;
- Python only declares experiments, invokes native kernels, validates parity,
  and writes reports.

### Resource gate

- Foundry profile: at most 30x track duration and 7 GiB VRAM;
- no candidate loss from GPU tile or host spill boundaries;
- portable CPU parity on bounded conformance cases;
- CPU-only decode;
- seek pre-roll no more than one second for the declared Main profile.

## 9. Work package WP-7 — Evidence-carrying codec generation

Every material generation creates:

```text
comparison/generation-<id>/
  manifest.json
  report.md
  original/
  resonith/
    encoded/*.resonith
    decoded/*.wav
  opus/
    encoded/*.opus
    decoded/*.wav
  previous-resonith/
  metrics/
  hashes/
  tools/
  player/
```

The report records:

- codec and syntax version;
- source revision or dirty-tree identity;
- exact command lines and configuration;
- input, stream, decoded, executable, and report hashes;
- complete bytes and bitrate;
- wall time, realtime factor, CPU, GPU, and peak memory;
- waveform, spectral, log-mel, transient, stereo, and intelligibility metrics;
- ablation and failure rows;
- actual released-decoder outputs;
- links to every local listening file and the exact Orkela executable.

## 10. Mandatory corpus levels

### Simultaneous duration gate

Every work package runs both duration classes in the same generation, in this
fixed execution order:

- **Long first:** continuous inputs of at least 120 seconds for dictionary
  amortization, persistent-law drift, long motifs, checkpoint/index overhead,
  memory growth, throughput, seek, and fallback stability.
- Freeze the long streams, metrics, configuration, hashes, and Pareto frontier.
- **Short second:** focused clips for sample-boundary, phase, onset, transient,
  intelligibility, local transform, low-latency, and ablation diagnosis.
- Tune a short-specialized plan without mutating the frozen long incumbent.

Neither class substitutes for the other. Reports publish per-file rows,
short/long aggregates, and the deterministic automatic analysis plan selected
for each input.

### Fast diagnostic

- constructive synthetic;
- EBU female speech;
- EBU dense orchestra;
- EBU pink noise.
- at least one continuous input of 120 seconds or longer.

Status: never a milestone or general claim.

### Material milestone

- pinned full speech;
- complete Emotional piano;
- complete 400.773-second Mozart overture;
- all sixteen R-111 heterogeneous classes.

Every perceptual milestone includes a current official Opus complete-byte
anchor and the preceding Resonith generation.

### Maximum-effort Opus frontier

The Opus anchor is itself optimized, not represented by one preset:

- current project-pinned official libopus encoder and decoder;
- complexity 10;
- all applicable application, signal, frame-duration, bandwidth,
  VBR/constrained-VBR, channel, and offline file controls;
- bitrate search around the declared complete-byte or quality target;
- official decode, complete container bytes, delay/pre-skip/sample validation,
  hashes, metrics, timing, and retained rejected candidates.

The best eligible decoded Opus point is the anchor. Lossless structural proxies
retain this evidence as context but do not claim a win by directly comparing
lossy Opus bytes with exact-lossless bytes.

## 10.1 Automatic duration and structure adaptation

One syntax and decoder serve all durations. The encoder chooses a deterministic
resource/search policy from:

- duration and sample rate;
- channel count and spatial layout;
- latency target;
- CPU, GPU, memory, and time budget;
- detected stationarity, transient density, repetition horizon, and field
  confidence;
- requested lossless or perceptual quality.

The plan may alter the scale union, factor/convolution depth, candidate
residency, dictionary lifetime, checkpoint cadence, exact-search depth, and
parallel scheduling. It cannot remove independent Truth, quality floors,
decoder bounds, or corruption checks. The complete chosen plan and every
skipped family are recorded in `manifest.json`.

### Duration-Pareto preservation

A proven duration-specialized branch is monotonic project knowledge:

- a long-input win remains in the candidate set while short-input search is
  tuned;
- a short-input win remains in the candidate set while long-input search is
  tuned;
- new tuning adds candidates and cannot silently overwrite an incumbent;
- selection is per input after quality eligibility, complete-byte accounting,
  and bounded decoder cost, never by a cross-duration average;
- the generation manifest records the incumbent, every challenger, rejection
  reason, and selected winner for each duration bucket.

Long-only success is retained and released as a declared capability when its
own complete evidence gate passes. It is not described as a universal win
until the short and medium buckets pass independently.

One duration bucket passes when either:

- complete bytes decrease while every applicable quality floor holds; or
- quality increases inside a predeclared matched-complete-byte tolerance.

Such a point remains in the Pareto set. A bitrate/quality trade-off outside the
equivalence tolerance is retained as an alternative operating point, not
silently chosen as the universal default.

Before freezing a generation, a one-axis winner triggers an immediate bounded
refinement:

- a rate-only win searches for higher quality while preserving the proven rate
  advantage;
- a quality-only win searches for fewer complete bytes while preserving the
  proven quality advantage;
- only a verified two-axis point, or a one-axis point whose declared
  refinement lattice and resource budget are exhausted, may receive a fixed
  generation identifier.

The initial point, all refinement candidates, axis deltas, rejection reasons,
and stop condition are retained. An exhausted one-axis win remains successful
project evidence and an available Pareto operating point.

## 11. Orkela coupling

Orkela is updated after the codec and decoder gate, before release:

- decode the exact promoted `.resonith` syntax;
- open original WAV and official Opus comparison files;
- display active anonymous fields, Basis lifetimes, correction share, routes,
  and fallback regions when present;
- provide `LIVE`, `HISTORY`, and `OVERVIEW` signal views;
- expose generation, stream profile, decoded hash, and verification status;
- pass automated open/play/seek/spectrum/corruption and startup-latency gates;
- package the exact tested executable into the generation directory.

Player UI work that does not unblock a current listening or conformance gate
remains deferred.

## 12. Promotion and stopping rules

A work package is `DONE` only when code, tests, machine report, listening
artifacts, decoder output, hashes, and required corpus rows exist.

A candidate is rejected when:

- it loses complete bytes at the same quality;
- its correction entropy does not amortize metadata;
- it violates decoder/resource/random-access bounds;
- its advantage depends upon semantic labels, unavailable cloud services, or
  non-deterministic normative inference.

The project does not preserve complexity to protect an idea. Failed syntax is
not promoted. Successful mechanisms remain optional RDO candidates until the
full Main profile freezes.

## 13. Final appended gate — persistent phase innovations

After the Orkela-coupled evidence step, run R-193 as the next architecture
gate. It does not bypass the active partial-graph quarantine or create a
parallel predictor.

For every admitted anonymous complex-partial path, compare:

- one absolute bounded integer phase/frequency state;
- denser frequency knots without explicit phase anchors;
- sparse byte-priced phase-innovation anchors distributed through one fixed
  causal correction ramp;
- split/rebirth plus deterministic crossfade;
- direct Truth and the preceding short predictor.

The first pass is a free exact-phase oracle. Syntax work stops unless that
upper bound reduces compressed final Truth by at least 10% in three long
coherent classes. A prospective anchor representation must then beat every
no-anchor, dense-knot, and rebirth alternative by at least 3% complete bytes
in two long real coherent classes at the quality floor.

Stationary sinusoids and exactly representable linear chirps require no
post-onset anchors. A ten-minute bounded-vibrato case permits at most one
anchor per second. Close tones, beating, crossings, cancellation, transients,
noise, reverberation, anti-phase stereo, route changes, random access, callback
partitioning, and lost-event recovery are mandatory counterexamples.

No anchor opcode is admitted until the complete R-118, maximum-effort Opus,
native deterministic synthesis, checkpoint, corruption, and listening gates
pass. The complete adversarial record is
[R-193 Phase-Innovation Anchor Audit](reviews/R193_PHASE_INNOVATION_ANCHOR_AUDIT_2026-07-28.md).

## 14. Continuous completion train through Resonith 1.0

R-194 makes this plan continuous through a public Resonith 1.0 release and its
native Orkela integration. Sections 1 through 13 are architecture checkpoints,
not terminal project states.

The remaining dependency order is:

1. finish R-191 through four separately visible dependency gates:
   - hard maxima, bounded snapshot, no-alias and exact canonical-edge
     verification;
   - transactional count/stage/commit publication for R-190 edges and R-191
     paths without partial caller writes;
   - exact work-law v1 plus generation-safe arena ownership;
   - complete PMR provenance, pre-entry allocation tripwire and separate
     host/device accounting;
   then obtain the required independent post-remediation GO;
   R-199 amends only the impossible absolute ordering between semantic rows
   6–8 and resource row 9: after rows 1–5, the earliest determinable semantic
   failure wins, while exhaustion wins if the caller bound is reached first;
2. admit R-192 only as decoder-domain hypotheses generated from the audited
   anonymous partial graph;
3. execute the R-193 free exact-phase oracle, then implement sparse
   phase-innovation anchors only if its byte/quality kill gates pass;
4. integrate arbitrary-interval gridless multiscale search, CompoundBasis and
   bounded gap laws across time, frequency and channels;
5. integrate immutable transformed-Basis instances with phase, pitch, time,
   envelope, filter and route laws plus one exact or quantized final
   TruthCorrection;
6. assign coherent, bounded-inharmonic, transient, stochastic and route
   structures to separately owned lanes so no energy is paid twice;
7. integrate persistent state/entropy and one global
   byte-quality-decoder-compute RDO over all lanes and direct Truth;
8. move full proposer/search batches to CUDA or another available compute GPU,
   retain a deterministic CPU fallback, and keep normative decoding on the
   bounded integer CPU/DSP core;
9. expose optional Gemini/local-model proposals without allowing semantic
   labels, cloud availability, or AI output to decide syntax;
10. optimize the native C++23 Studio and Foundry encoders, the decoder SDK and
    CLI; retain Python solely as an unshipped oracle/control plane;
11. run long-first generations against the maximum-effort official Opus
    frontier, perform the required missing-axis refinement, then tune short
    material without deleting the long incumbent;
12. freeze Resonith bitstream v1 only after conformance, corruption, random
    access, packet loss, resource, determinism, platform and listening gates;
13. publish Resonith 1.0 with encoder, decoder, SDK, CLI, specification,
    corpus evidence, reproducible reports, listening assets and Orkela
    integration.

Focused validation follows every implementation change. The full R-118,
platform and listening unions execute only at a declared generation,
release-candidate or release boundary unless a focused failure demonstrates
that a broad rerun is required. Passing an intermediate item advances
immediately to the next dependency-ready item.

Every codec algorithm change is a declared evidence generation. Before the next
algorithm change begins, it runs every item in the versioned registered-music
manifest and publishes a detailed per-file and aggregate comparison against
the immediately preceding Resonith generation and the current maximum-effort
official Opus anchor. This music gate is additional to the complete R-118 union
and cannot be replaced by the three principal references.

R-201 completed the fourth implementation dependency above with an independent
Step-8 GO: exact reserved/committed/live host provenance, checked page
transitions, an immutable work ceiling, a pre-entry global-allocation
tripwire, and truthful CPU device zeros. R-202 then completed Step 9 with
independent GO on source revision
`ecfee1a3ed4a2a62848da91c91acc098f873cbd6`: exhaustive 952-ordinal
transactional failure injection, four-seed/two-million-input sanitizer fuzzing,
eight-thread/100,000-sequence TSan, canonical semantic coverage, and the full
Android/Apple/Linux evidence matrix passed. R-191 remains unadmitted until
Step 10 performs the final independent conformance decision.

R-203 candidate-rich replay now has a complete raw typed bridge, an
independent exact-selection judge, fail-closed inventory binding, identical
twice-run packed evidence, and GCC/Clang/MSVC/Apple/Android replay wiring.
The independent complete-ledger audit nevertheless returned NO-GO: the frozen
law does not enumerate every solver operation and still exposes
implementation-dependent container growth through `MEMORY_PAGE` and resource
high-water. A proof-carrying trace plus PMR allocation-site proposal was then
independently rejected before implementation because it could not prove
omitted events or force portable vector capacity without changing failure
behavior. Step 10 now audits the smaller evidence-only correction: preserve
exact cross-toolchain semantic output and 21 non-memory CPU events, while
validating `MEMORY_PAGE` and managed upstream-request telemetry exactly and
fail-closed per toolchain rather than falsely requiring vendor STL allocation
requests to be identical. Production behavior remains frozen unless a
separate audited change triggers the complete registered-music and
maximum-effort Opus comparison required by R-198.

## 15. R-195 integrated MAF-first generation

Before non-blocking Orkela product expansion, build one integrated candidate
union containing all of the following:

- remediated R-191 anonymous multi-partial graph;
- persistent source/resonator/excitation/route lifetimes;
- R-193 continuous/phase-locked oracle alternatives;
- content-defined exact motifs at arbitrary sample boundaries;
- gridless multiscale approximate patterns and cross-channel relationships;
- CompoundBasis with sparse bounded gap laws;
- transformed immutable Basis instances;
- Cached Integer Basis Synthesis for per-file learned immutable atoms;
- separately owned coherent, bounded-inharmonic, transient, stochastic and
  route lanes;
- source-filter/resonator, stochastic-law, transient-event and inter-channel
  route candidates;
- persistent entropy/allocation state;
- one global complete-byte, decoded-quality, decoder-work and memory RDO;
- full GPU proposer/search batching, deterministic CPU fallback, and
  CPU/DSP-only normative decode;
- optional Gemini/local-model proposals and Foundry-to-consumer router
  distillation, neither of which can override exact local RDO.

The generation is measured long-first, then on the complete R-118 union
against the preceding Resonith release, direct Truth and maximum-effort
official Opus. Any one-axis win receives its bounded missing-axis refinement
before the generation freezes. Orkela is changed only as required to decode,
inspect and audition this generation until that evidence is complete.

## 16. R-204 continuous execution and durable 63-step view

The accepted operational view is panel `R204-63-V1`:

- definition:
  [`23_CONTINUOUS_63_STEP_EXECUTION_PANEL.md`](23_CONTINUOUS_63_STEP_EXECUTION_PANEL.md);
- definition SHA-256:
  `6b2d1e21436e22231538d1b362657375c3699892b5290d17843ae025f510684e`;
- mutable resumable state:
  [`execution/R204_CURRENT_CHECKPOINT.md`](execution/R204_CURRENT_CHECKPOINT.md).

The panel contains exactly 63 stable IDs. It is a derived view of this master
plan and accepted decisions, not a competing source of authority. It must not
be silently shortened, regrouped, renumbered, reordered, or reconstructed from
memory. Any amendment receives a new panel ID, an explicit old-to-new mapping,
owner approval, and the evidence-first audit required by R-185/R-196.

While the owner-authorized continuous execution remains active, every passing
subtask is a checkpoint and execution advances to the earliest
dependency-ready, safe, in-scope item. This does not waive or bypass
dependencies, quarantine, immutable evidence, audits, kill gates, safety,
authority, credentials, or separately governed external actions. Every pause,
blocker, or platform-imposed yield updates the durable checkpoint before
control is returned.

Focused risk-based tests follow every implementation edit. One frozen
materially scoped codec-algorithm hypothesis and its tightly coupled edits form
one evidence generation. Before that generation is accepted or another
algorithm generation begins, the complete R-198 registered-music comparison
must run through actual Resonith and official Opus decoders against both the
immediately preceding accepted Resonith generation and the frozen
maximum-effort official Opus anchor.

## 17. R-276 resource-verdict recovery map

Resource limits govern declared execution profiles; they do not silently erase
information-model hypotheses. Historical transactions and their caps remain
immutable, while later independently designed steps may recover mechanisms that
never received a codec byte/quality verdict.

- S11 persistent multi-partial state remains a research substrate for S19,
  S21, S33, S35, and S41. S27 must remove its monolithic observation blind spot
  and S39 must judge it through one global complete-cost RDO.
- The frozen S13 carry/reset experiment is not repeated. Phase-continuous and
  locked alternatives return only within eligible harmonic structures in
  S33-S34 or channel-route structures in S35-S36.
- The R-232 decoder-domain cost idea returns in S39-S40. Its scalable exact
  evaluation belongs to S47-S48. The failed Python form and its timeout are not
  restored.
- R-253 through R-266 remain quarantined. Immutable resonator/LPC-law reuse may
  be reimplemented under new authority in S37-S38 or as an output-identical
  accelerator in S47-S48.
- The R-268 38-Cell candidate is algorithm-negative and does not return. A new
  persistent resonator hypothesis remains possible in S37-S40.
- The R-271 IMF1 generation is terminal for its frozen 2-GiB profile. A new
  inharmonic-resonator derivation belongs to S37-S38; full-lattice streaming or
  batching belongs to S47-S48; optional recall expansion belongs to S49-S50.

The complete classification and independent audit are recorded in
[`reviews/R276_RESOURCE_VERDICT_AND_RECOVERY_AUDIT_2026-08-03.md`](reviews/R276_RESOURCE_VERDICT_AND_RECOVERY_AUDIT_2026-08-03.md).
No stable step is added, removed, renumbered, or reordered.
