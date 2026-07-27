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

Repeated motif programs and shared package dictionaries remain **RESEARCH** and
must be compiled into the same ISA. CIBS adopted decision R-014.

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
