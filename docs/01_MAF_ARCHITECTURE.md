# MAF - Memory-oriented Acoustic Field

Status: architectural core - **ACCEPTED**; specific precisions and tables -
**NORMATIVE-DRAFT**.

## 1. Paradox

The sound wave must physically continue, but the parameters of the stable
There is no need to transmit the oscillations again every 10–20 ms. Resonith separates:

1. long-lived acoustic cause;
2. a rare change in its law;
3. objective innovation, which the model did not explain;
4. optional perceptual detail that is not true.

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+ TruthInnovation_t
+ OptionalPerceptualDetail_t.
\]

Transport remains packet, and DAC issues samples, but neither packet nor
sample block is a unit of long-lived codec state.

The governing MAF causal equation is:

```text
Pressure_c(t) =
  sum_s Route_c,s(Resonator_s(Excitation_s, State_s))
  + Truth_c(t)
```

`Excitation` may be coherent/quasiperiodic, impulsive, or stochastic.
`Resonator` creates harmonic and bounded-inharmonic partial bundles, formants,
decay, modulation, and body/room response. `Route` carries complex phase,
delay, gain, channel covariance, and stable propagation. Each law persists
until a real event changes it.

## 2. Not a classification of a piece, but a superposition

The same interval MAY simultaneously contain:

- `PERIODIC`: note, voiced speech, engine;
- `PREDICTIVE`: excitation and short vocal/formant model;
- `TRANSIENT`: blow, click, attack;
- `STOCHASTIC`: breathing, rain, plate, bow noise;
- `RESONANT`: string, body, room, reverb tail;
- `SPATIAL`: emitter/listener law and mixer;
- `INNOVATION`: everything that is more profitable to convey to objective residual.

These are not seven subcodecs. These are the small common ISA parameters that are mixed
sample-accurately and use one timeline, state grammar and entropy layer.

## 3. Universal notation of the atom

Logical entry:

```text
Atom {
    atom_id
    basis_family
    birth_time
    death_time | open_ended
    source_id
    basis_ref | inline_basis
    changed_fields
    parameter_tracks
    routing
    truth_class
}
```

State is changed only:

```text
RESET(time)
SET(time, atom_id, changed_fields, payload)
END(time, atom_id)
```

`END` is the canonical short form of `SET(alive=0)`. The absence of `SET`
preserves the previous law. A render query reads state without mutating it.

## 4. Coherent field and Timbre Basis

It is unprofitable to transmit thousands of independent sinusoids. Basic coherent atom
uses a cached periodic basis:

\[
C_i(t)=A_i(t)\sum_{k=0}^{K_i-1}
a_{ik}(t)B_{ik}(\phi_i(t)).
\]

Where:

- \(B_{ik}\) — immutable integer wavetable/timbre basis;
- \(\phi_i(t)\) — absolute fixed-point phase law;
- \(A_i(t)\) and \(a_{ik}(t)\) - bounded continuous coefficient tracks.

One `TIMBRE_BASIS` MAY be used by all notes of the part, one
instrument, voice segments, or repeated appearances of the source.
Changing pitch does not require retransmitting the waveform. If basis stopped
explain execution, encoder updates coefficients or selects Innovation.

The normative decoder does not know that the basis belongs to the violin. This is knowledge
used only by the encoder compiler.

## 5. CIBS - Cached Integer Basis Synthesis

**ACCEPTED:** `TIMBRE_BASIS`, `FILTER_BASIS` and `CONTROL_BASIS` MAY
transmitted not only raw/lifting coefficients, but also as:

\[
B=\operatorname{CIBS}_{m}(z,\Delta_m)
+ LIFT^{-1}(q_{\mathrm{basis\ correction}}).
\]

Where:

- \(m\) — profile-defined versioned integer model;
- \(z\) — quantized latent;- \(\Delta_m\) — optional bounded low-rank adapter;
- correction — objective integer correction to the synthesized Basis.

Synthesizer runs only on `BASIS_SET`. After checking the hash result
becomes immutable and the sample loop sees the usual cached Basis. Thus
learned compression reduces Basis payload, but does not transform audio renderer
in neural decoder.

Main prohibits:

- arbitrary graph from bitstream;
- device floating-point behavior;
- external model required for decode;
- change weights after profile publication;
- CIBS inference on each output sample.

Full semantics:
[09_CIBS_NORMATIVE_DESIGN.md](09_CIBS_NORMATIVE_DESIGN.md).

## 6. Excitation–resonator factorization

\[
R_i(t)=\sum_m H_{im}(z;\rho_{im}(t))\,e_i(t),
\]

where \(e_i\) is excitation, and \(H_{im}\) are small stable integers
FIR/IIR/resonator sections.

One excitation MAY excite several resonant modes. One room basis MAY
handle multiple emitters. This allows you to pay for long-lived
structure once, and then pass rare parameter events.

Each IIR section must have normative evidence of bounded stability
for the allowed range of coefficients.

## 7. Shared Control Basis

Many acoustic atoms often obey a single change:

- tempo/rubato of several notes;
- vibrato or pitch bend of the partials group;
- crescendo/dynamics of the ensemble;
- emitter movement;
- change room/microphone law.

There is no need to repeat the same knots in each atom. Immutable
`CONTROL_BASIS` sets scalar/vector parameter law once; atoms refer to
it with bounded scale, offset and time mapping:

\[
\theta_i(t)=s_i\,Q_r(\tau_i(t))+o_i.
\]

The decoder is not required to know that \(Q_r\) means tempo or vibrato. He calculates
regular fixed-point law. Semantic score helps the encoder detect reuse,
but does not become Truth.

## 8. Stochastic field without hidden randomness

\[
N_i[n]=F_{\mathrm{int}}\left(
PRNG(seed_i,n),\Sigma_i(n)
\right).
\]

- PRNG is counter-based: sample \(n\) is calculated independently;
- seed, spectral envelope and filter law are included in bitstream;
- result bit-exact;
- random access does not require playing the entire previous history;
- objective mismatch is transferred to Innovation.

Stochastic atom does not mean "similar noise is equal to original noise". In lossy profile
such a predictor is only allowed after RDO; in Lossless exact residual
restores the original PCM.

## 9. Transient and Innovation

Transient should not be smeared by a long window and create a pre-echo.
Core uses short integer lifting bases with independent onset:

\[
T_i + E = LIFT^{-1}(q_{\mathrm{sparse}}).
\]

`TRANSIENT` has parameterized onset/decay when beneficial.
`INNOVATION` is a universal bounded fallback and MAY be:- short sparse lifting correction;
- band-limited correction;
- full-band exact replacement.

Lossy Innovation is deterministic but quantized. Lossless Innovation is obliged
restore exact input PCM.

## 10. Minimum normative DSP ISA

Main decoder is built from the following operations:

1. periodic table lookup/interpolation with absolute phase;
2. short integer FIR/IIR/resonator;
3. counter-based integer PRNG;
4. inverse integer lifting;
5. coefficient-track evaluation;
6. gain, mix, spatial matrix, add, saturate/clip;
7. single entropy decoder.

CIBS adds a separate update-time kernel from fixed integer
matrix/filter/upsample/nonlinearity operations. It is not included in per-sample hot
loop and has a separate MAC/Basis limit.

No atom executes arbitrary code. No neural graph is required
in Truth Core. Concurrency is determined by dependency levels, not order
random dynamic graph.

## 11. Continuous laws

Phase, amplitude, pitch, filter coefficients and spatial trajectory are specified
piecewise constant/linear/quadratic laws with absolute start time.

Mandatory invariants:

- phase continuity;
- limited derivative jump or crossfade/Innovation;
- canonical fixed-point rounding;
- clip only within normative mix boundaries;
- bounded atom overlap;
- lack of recursive dependence on the previous output block.

Different atoms are updated at different frequencies. A lasting note can live for thousands
render quanta; transient — several samples; ambient law - seconds.

## 12. Truth and Perceptual

`Truth Core` includes deterministic atoms and Innovation and is the only
source of future state/reference.

`Optional Perceptual Detail` MAY synthesize imperceptible microtexture or
upper spectrum, but:

- MUST be discardable;
- MUST NOT change Core state;
- MUST NOT be a predictor/reference;
- MUST have signaling capability;
- MUST NOT be used in objective/lossless claims.

## 13. Where is the advantage?

A revolution is only possible if one persistent atom simultaneously removes:

- retransmission of timbre;
- re-evaluation of pitch/phase on each frame;
- incompatible speech/music codec switching;
- long reverb waveform;
- repeated excitation/resonance structure;
- retransmission of the general modulation trajectory.

If metadata and residual are almost equal to normal transform codec, MAF has no
benefits. Therefore, each basis family is an RDO candidate, and not
mandatory regime.

## 14. What is deliberately not included in Main-0

- mandatory score/MIDI representation;
- names of instruments as decoding truth;- unrestricted/per-sample neural decoder; fixed update-time CIBS enabled;
- Turing-complete acoustic program;
- external cloud dictionary, without which the stream is not decodable;
- unlimited convolution;
- unlimited number of atoms per sample.

R-139 adopts bounded in-stream motif dictionaries for Main development.
External cloud dictionaries and arbitrary motif programs remain excluded.
Every reusable motif is an immutable objective Basis carried by the stream or
materialized through bounded CIBS, and every placement compiles into the same
fixed integer ISA. CIBS adopted decision R-014.

## 15. The operational MAF cell

MAF is not a transform codec followed by optional side models. Its encoder
compiles a bounded acoustic cell:

```text
packet × channel-group × band × lifetime
```

into exactly one primary representation:

```text
HOLD | COHERENT | SOURCE_FILTER | STOCHASTIC
     | TRANSIENT | PVQ | TRUTH
```

`HOLD` is the crucial zero-update event. A Basis, excitation law, filter law,
counter seed law, gain trajectory, routing, and lifetime continue without
being resent merely because another transform interval elapsed. Mutations are
events; render quanta are an implementation detail.

`PVQ` and `TRUTH` are universal exits, not parallel full-rate layers. A model
may receive a bounded Truth correction only when the combined complete cost is
lower than replacing it with Truth. This avoids the failed global PVE
factorization in which the stream paid for both a basis and a complete sparse
correction.

The encoder jointly evaluates:

\[
J_c =
R_{\mathrm{complete},c}
+ \lambda D_c
+ \mu C_{\mathrm{decode},c}
+ \nu M_{\mathrm{state},c}
+ \rho L_c
+ \kappa P_c
+ \eta S_c .
\]

Costs and distortion are conditional on the state left by earlier cells.
Therefore, gains from persistence, source-filter factorization, stochastic
fill, CIBS, motifs, transients, and channel reuse are not independently
additive. The project publishes disable-one ablations and an actual jointly
serialized winner.

## 16. Non-regression and hostile content

The current admitted LPS5/LPS6 stream remains a complete RDO candidate. A MAF
candidate is retained only after serialization, independent decode, and all
applicable objective and subjective gates. A fallback is reported as a
fallback, never as an improvement.

Structured speech and music may contain long-lived causes that MAF can amortize.
Entropy-like noise may contain almost none. A revolutionary structured-content
gain and an honest transform/Truth fallback are therefore compatible parts of
one codec; the latter is not hidden by an aggregate score.

## 17. Source-filter execution contract

The source-filter path is causal and decoder-closed:

```text
adaptive/coherent excitation state
        + fixed/stochastic excitation
        + bounded Innovation
        -> stable synthesis filter
        -> output
```

The encoder searches against reconstructed excitation history, not the
unquantized source history. Excitation pitch/phase, adaptive gain, filter
envelope, stochastic envelope, and fixed-codebook events have separate
lifetimes. A short search subframe is not a mandatory state-update interval.

Filter/timbre vectors may be learned encoder-side, quantized into an immutable
integer Basis bank, and referenced until mutation. The encoder recomputes exact
Innovation after Basis materialization, so the cached state changes rate but
cannot silently change Truth.

The first R-120 diagnostic proved two useful pieces but rejected the complete
candidate. Cached filter Basis reduced the speech parameter envelope from
2,577 to 701 bytes. A 10,294-byte sparse-excitation point was 42.6% smaller
than the 17,942-byte Opus anchor, but its STOI was only 0.878153 and therefore
failed quality. Closed-loop adaptive excitation improved STOI to 0.908976 at
12,548 bytes, but still mutated pitch in 1,134 of 1,464 subframes and remained
well behind Opus. These are one-item fast diagnostics, not admitted results.

The next source-filter experiment must jointly search a compact continuous
pitch/phase trajectory, adaptive gain, and perceptually weighted multi-pulse
Innovation. It must retain MFC1 and the admitted LPS5/LPS6 path as complete
fallbacks and pass R-118 before any promotion.

## 18. Bounded decoder substrate

MAF is a small state machine over a fixed integer DSP, not a program shipped
inside every track. Orkela, the SDK, or a future hardware decoder installs the
operation set once. A stream supplies only bounded Basis data, references,
trajectory and gain events, filter parameters, stochastic seeds, transients,
Innovation, routing, and lifetime mutations.

The portable CPU Core is the semantic reference. Its ordinary mono/stereo
render loop is intentionally small enough for one desktop or mobile CPU thread.
Optional GPU or fixed-function backends target large immersive source counts
and convolution; they cannot change Truth output.

Preparation and rendering are separate:

- preparation verifies the container, hashes, operation identifiers, stable
  filters, references, lifetime ordering, memory requirements, and total
  operation budget, then materializes immutable CIBS Basis outside the callback;
- rendering reads only prepared caller-owned state, absolute time, and a
  bounded command view. It allocates nothing and performs no I/O, discovery,
  logging, locking, or global mutation;
- each output transaction is staged and committed only after every operation
  and budget check succeeds.

This substrate precedes Foundry intelligence. A local model, Gemini-like cloud
service, handcrafted analyzer, or exhaustive GPU search may propose the same
MAF states later, but none becomes a decoder dependency and none can bypass
integer decoder-in-loop RDO.

Provider event times are deliberately lossy hints. Foundry expands each hint
into several local PCM change anchors, searches a bounded neighborhood of each
anchor at individual-source-sample resolution, adds strong locally detected
missed changes, and retains `NO_BOUNDARY` as a complete candidate. Thus a
useful semantic hypothesis survives a poor cloud timestamp, while an
unprofitable or false boundary costs no admitted stream bytes.

## 19. Typed lifetime execution

The first executable prospective lifetime syntax is `MFT1` (R-130). It makes
the memory-oriented claim testable: immutable periodic Basis, filters,
stochastic fields, source excitations, transient shapes, and mix matrices
exist over explicit half-open sample lifetimes instead of being repeated as
transform-frame decisions.

The decoder validates the complete immutable record graph once, prepares
stable integer filters into caller-owned memory, and then renders sequentially
without allocation, file access, network access, logging, or locks. Internal
render slices occur only at a real lifetime boundary. Arbitrary application
callback boundaries do not change PCM or acoustic state.

`MFT1` is deliberately narrow. It does not add semantic labels, arbitrary
graphs, bytecode, decoder-side AI, or a second residual. Deterministic Truth
remains the complete fallback until a typed lifetime candidate wins exact
complete-byte RDO on real evidence.

## 20. Content-defined motif memory

R-139 generalizes persistent memory from periodic timbre to finite acoustic
events. The encoder first finds bit-identical content-defined chunks, then
searches canonical near-duplicates after factoring exact sample alignment,
gain, phase, bounded pitch/time drift, and channel placement. A provider may
suggest that two phrases or notes are related, but only objective
decoder-in-loop correction can admit their reuse.

One immutable motif Basis may serve many one-shot timeline instances. Each
instance is an exact-sample, half-open placement with bounded transform laws;
it does not copy executable code into the stream. The instance is paid only
when:

```text
Basis bytes + all placement bytes + all corrections
    < optimized independent Truth bytes
```

Exact sample reuse is the first implementation because it has unambiguous
identity and a tiny decoder. Gain/phase normalization follows, then bounded
pitch/time laws and overlap. This ordering preserves the simple mechanism
while exposing increasingly common repetitions to the same immutable memory.

## 21. Multiscale minimum-description law

MAF does not assume that one representation explains every signal. Each
region competes under the common causal decomposition:

```text
observed region
    = bounded transform(immutable Basis)
    + counter-addressed stochastic law
    + objective Truth
```

The full proposal union separates coherent harmonic, deterministic
inharmonic, sparse transient, stochastic, and phase/room/channel route lanes.
The lanes may overlap additively in time and frequency but have single
rate-accounting ownership. They are rendered and summed before one final
mixture-domain Truth. This prevents harmonic structure from paying for attacks
or noise and prevents stochastic structure from becoming thousands of
unprofitable sinusoids.

The useful scale is discovered rather than declared semantically. A Basis may
span a few samples, one oscillation, a transient attack, a room resonance, a
phrase, or a complete repeated section. The encoder pays the dictionary,
transform parameters, stochastic parameters, placement, checkpoints,
operation cost, and correction before admitting reuse.

Noise does not invalidate memory. Rain, wind, surf, breath, and applause can
reuse event shapes, resonances, spectral density, modulation, correlation,
and event-rate laws even when their exact PCM realization never repeats. A
seeded realization is objective only when Truth corrects it to the declared
source; without that correction it is non-reference perceptual detail.

The existence of some mathematical mapping between two regions proves
nothing: an arbitrary mapping can be as expensive as the target samples. Main
therefore exposes only a fixed bounded integer transform ISA and always
competes it with optimized independent Truth.

## 22. Latent acoustic tomography

A finished mix supplies changing observations of recurring causes. Foundry may
use those observations to factor:

```text
channel_c(t)
    = sum_i route_ci(t) * transform_i(Basis_i, t)
    + Truth_c(t)
```

This is analogous to reconstructing a persistent surface from differently
occluded views. A source that appears under several gains, positions, filters,
and overlaps can reveal a reusable latent Basis even when no mixed PCM chunk
repeats directly.

The factorization need not recover a semantically or physically named
instrument. It must only synthesize a cheaper objective sum. Sources that
cannot be identified separately may remain one composite Basis. Neural
separation, sparse factorization, cross-occurrence subtraction, and
multi-channel analysis are encoder-side proposers; the decoder only executes
the existing bounded emitter sum. Native synthesis and Truth determine
admission, so a wrong separation cannot silently alter the recording.

## 23. Semantic-free partial-spectrum memory

Dictionary identity is an objective coefficient sequence, not a recognized
sound. A Basis may own only one bounded time-frequency region. Unrelated
simultaneous content in the other regions remains independently represented,
so a recurring high-band texture can be reused under changing bass, speech,
noise, or room content.

The exact model is:

```text
coefficient region
    = bounded_integer_transform(dictionary Basis)
    + exact coefficient Truth
```

Lossless operation requires a reversible integer analysis/synthesis pair.
Magnitude spectra alone are only search hints because sign, phase-equivalent
alignment, overlap state, and rounding affect the waveform. The first R-145
oracle uses exact average/difference lifting to prove the ownership and
correction rule. It is a research decomposition, not the final frequency
tiling.

Every coefficient cell has one owner. A cell selected for a transformed Basis
cannot also be paid as a stochastic, source-filter, transient, or independent
Truth cell; only its correction is transmitted. Complete RDO includes the
analysis mode, support, dictionary, placements, transform parameters,
checkpoints, correction, and bounded decode operations.

## 24. Phase-complete and cross-channel reuse

Power-spectrum similarity only proposes a candidate. Foundry compares complex
cross-spectrum or exact waveform correlation to recover circular
sample-alignment and polarity. Schema-1 `BASIS_INSTANCE` executes that first
phase-complete subset with:

- `CIRCULAR` Basis indexing for exact integer phase/alignment;
- signed gain for polarity and 180-degree counterphase;
- `LINEAR_GAIN` for one exact fade or damping trajectory;
- emitter placement plus the persistent mix matrix for cross-channel reuse.

The dictionary is global across channels and bands. A Basis observed on the
left may be placed on the right, center, or surround with a different delay,
phase, polarity, gain trajectory, and later a bounded short transfer filter.
Each output channel retains independent Truth, and complete RDO competes with
independent channels and reversible channel lifting.

Channel identity is not part of the acoustic Basis. It is one placement and
routing coordinate. This lets one immutable acoustic cause explain panning,
echo, room decay, and correlated microphone observations without duplicating
its waveform.

## 25. Learned search without learned Truth

The combinatorial search over duration, band, channel, phase, gain, pitch/time,
filter, and overlap is an encoder problem. Foundry may use a local
original-PCM representation model and GPU nearest-neighbor index to propose
multiscale related regions. The proposal is label-free; recognized phonemes,
notes, instruments, speakers, and natural-sound classes are unnecessary.

Each proposal is converted into a bounded mathematical candidate by the exact
DSP fitter. Native decoder-in-loop RDO then accepts or rejects the complete
bytes. The local model therefore improves candidate recall but cannot change
Truth, bitstream semantics, or standalone decoding. Cloud models remain
optional coarse proposers under the privacy gate.

For speech, learned similarity search runs beside the causal excitation and
speaker-local vocal-tract filter model. Persistent timbre/filter state,
pitch/phase trajectories, cross-occurrence micro-Basis reuse, and exact
Innovation compete and compose without requiring text recognition.

## 26. Complete GPU Foundry

R-149 separates fast proposal from evidence-grade search. A Foundry run
declares a finite hypothesis language and evaluates every candidate in that
language. A fingerprint, embedding, classifier, or cloud model may change
execution order, but cannot delete a declared candidate. Fast and Live modes
may use top-K search only when their reports say so explicitly.

The first native exhaustive lattice is:

```text
all fixed-lattice blocks
    x all ordered unequal block pairs
    x all circular sample phases
    x signed constant/linear Q1.15 gain laws
```

NVRTC compiles the C++23 kernel at runtime and the CUDA Driver API executes it
in deterministic tiles. An 8 GB device therefore changes batch residency, not
candidate membership. Every result contains exact integer synthesis error and
is checked against a portable CPU reference. The decoder and bitstream do not
depend on CUDA, NVRTC, Python, or a particular GPU vendor.

Completeness is meaningful only relative to explicit bounds. The infinite set
of arbitrary programs is neither searchable nor a useful codec. New pitch,
time, filter, stochastic, partial-band, overlap, and cross-channel laws enter
Foundry as separately bounded families and must pass their own recall, parity,
complete-byte, and decoder-resource gates.

## 27. Scale-parallel hierarchical Basis grammar

R-150 prevents a small discovery from hiding a larger explanation. Foundry
analyzes original PCM independently at every declared duration, band, channel,
and transform family. A discovered micro-Basis does not claim samples and
does not suppress an overlapping direct large-span candidate.

The candidate pool then includes:

- direct candidates found from original PCM at every scale;
- exact or transformed micro-Basis placements;
- adjacent atoms combined under one phase/gain/pitch/time/filter state law;
- compounds built from existing immutable Basis entries;
- larger compounds built from smaller acyclic compounds;
- independent Truth for every uncovered region.

One exact bounded minimum-description chart chooses among them simultaneously.
It charges a dictionary entry once, every placement and state increment in
full, all correction bytes, and declared decode operations. Greedy
first-match ownership is forbidden for Foundry evidence.

The first executable oracle already supports repeated exact atom sequences,
removal of absolute phase/gain state followed by exact increment reuse,
one-time existing-Basis activation, overlapping direct large spans, and a
global chart that rejects locally attractive but globally expensive merges.
The normative decoder grammar remains prospective until its complete-byte
stream gate passes.

## 28. Minimum-description anonymous causal program

The complete encoder object is one bounded causal program, not a sequence of
content labels or a switch among isolated codecs:

```text
program =
    immutable leaf and CompoundBasis memory
    + persistent anonymous emitters
    + excitation / resonator / partial / transient / stochastic laws
    + independently indexed timing / phase / gain / envelope / route state
    + one final mixture Truth
```

For a finite declared language, Foundry minimizes:

```text
actual program bytes
    + actual event, route, and checkpoint bytes
    + actual final-Truth bytes
    + distortion cost
    + bounded decode and seek cost
```

The program may contain several overlapping causes at once. A coherent
partial bundle does not need to impersonate a transient; a transient does not
need to carry stochastic ambience; a stochastic field does not need to become
thousands of deterministic sinusoids. The perfect-reconstruction analysis
domain assigns one primary owner, the bounded renderers are summed, and only
then is the authoritative Truth computed.

Source separation is not an end in itself. A latent emitter exists only when
its immutable memory, state laws, events, routes, and reduced Truth make the
complete program shorter or create an admitted matched-rate quality point.
The factorization may differ from the physically real instruments while the
decoded sum remains objective.

The scalable solver uses column generation and deterministic add/remove/swap
beam RDO; small declared candidate families retain a bounded exact oracle.
Semantic or learned systems can add columns but never remove the
deterministic candidate union or decide admission. This is the R-179 primary
MAF compiler objective.

## 29. Whole-track self-supervised causal Foundry

R-182 makes the complete recording the training set for its own anonymous
causal program. The Foundry learns vector partial shapes, excitation,
resonator state, returns after gaps, hierarchical motifs, and cross-channel
routes over the complete timeline. It is not trained to name a source.

Learning alternates quantized parameter re-estimation with structural
add/remove/split/merge/link/route-share edits. Every proposed frontier edit is
packed, independently decoded, summed, followed by one final Truth, and
charged in full. The decoder sees only the resulting bounded integer program;
training code, gradients, separators, CUDA, and cloud systems remain outside
the bitstream.

This turns file-specific overfitting into a valid compression search without
making model memory free. A learned law wins only when its reusable state
removes more final-Truth bytes than the law, Basis, events, routes, and
checkpoints add. The detailed algorithm and gates are in
[22_PER_TRACK_CAUSAL_FOUNDRY.md](22_PER_TRACK_CAUSAL_FOUNDRY.md).
