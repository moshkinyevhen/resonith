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
