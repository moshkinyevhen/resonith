# R-192 Multi-Partial Predictor Preflight

Date: 2026-07-28  
Status: pre-audit design; implementation admission is blocked

## Question

Can the audited R-190/R-191 anonymous partial graph become an effective
decoder-domain predictor without repeating the old HILN limitation, replacing
Truth with a plausible but different synthesis, or forcing a neural network
into the decoder?

## Sources of truth

The preflight uses five independent kinds of evidence:

1. McAulay–Quatieri validates amplitude/frequency/phase partial tracks,
   explicit birth/death, and endpoint-aware smooth phase interpolation.
2. Serra–Smith validates separating deterministic partials from a stochastic
   residual instead of fitting every noisy coefficient as a sinusoid.
3. MPEG-4 HILN proves that harmonic lines, independent lines, and shaped noise
   can form a standardized small parametric decoder; its frame-local model and
   historical quality also show that decomposition alone does not guarantee a
   superior codec.
4. DDSP and differentiable parametric-mixture work show that strong physical
   synthesis priors can be fitted jointly to mixtures and can expose pitch,
   loudness, timbre, transient, and room coordinates. They do not prove exact
   reconstruction, small normative models, stable cross-domain quality, or
   complete-stream compression.
5. Opus demonstrates the strength of decoder-domain prediction plus transform
   correction under a mature entropy and psychoacoustic system. A Resonith
   partial proposal must beat the actual complete Opus anchor, not an
   uncompressed coefficient proxy.

## Alternatives stressed

### A. One frame-local fundamental plus harmonic amplitudes

Rejected as the primary representation. It is compact for a single stable
pitched cause, but it is ambiguous under polyphony, missing fundamentals,
crossing trajectories, inharmonic instruments, phase resets, and mixed
transients. It may return later as an optional grammar over already admitted
independent paths.

### B. A neural latent waveform decoder

Rejected from the normative Core. It can propose useful paths or initialize a
whole-track fit, but model bytes, platform drift, adversarial inputs,
out-of-domain timbre changes, and decoder cost violate the small deterministic
ISA objective. No learned likelihood can replace actual decoded correction
bytes.

### C. Magnitude-only sinusoidal resynthesis

Rejected. It discards the coordinate that determines cancellation,
stereo routing, attacks, and exact waveform continuity. A magnitude fit can
look excellent while increasing final Truth.

### D. One independently corrected residual per inferred source

Rejected. The separation is non-identifiable and per-source corrections pay
for cancellation and leakage repeatedly. Resonith renders all admitted
anonymous fields first and carries one authoritative mixture-domain Truth.

### E. Anonymous complex paths plus decoder-in-loop global admission

Retained. Paths remain independently addressable; grouping is optional and
must prove complete-byte benefit. The actual quantized decoder output, not the
analysis estimate, is subtracted before the single final Truth is encoded.

## Proposed finite model

For output channel \(c\), a coherent proposal is

\[
\hat x_c[n] =
\sum_{p\in A(n)}
\operatorname{Re}\{g_{c,p}[n]z_p[n]\},
\qquad
z_p[n+1]=z_p[n]e^{j\omega_p[n]}.
\]

The research candidate language is finite and contains:

- arbitrary-sample birth and death;
- piecewise constant, linear, and second-order integer frequency laws;
- piecewise scalar amplitude and complex cross-channel route laws;
- two competing phase laws:
  - integrated phase, with no hidden reset;
  - endpoint-locked integer interpolation, with an explicit bounded phase
    correction that reaches the transmitted knot exactly;
- explicit knots at graph observations, with bounded optional knot removal;
- independent-channel and common-oscillator-plus-route candidates;
- direct Truth as an always-present complete candidate.

Analysis frames and CUDA tiles do not appear in this model. They may schedule
work but cannot create a birth, death, knot, or reset.

## Why two phase laws are mandatory

An approximate frequency integrated over a long lifetime accumulates a large
phase error even when instantaneous frequency error is small. Conversely,
blindly forcing every observed phase can introduce discontinuous corrections
and excessive metadata. Integrated and endpoint-locked hypotheses therefore
compete as mutually exclusive representations of the same segment. Neither is
selected by signal label.

## Admission algorithm

1. Generate finite path proposals from the audited graph union.
2. Quantize every law exactly as the prospective decoder will read it.
3. Render every proposal with the portable integer synthesizer.
4. Measure its marginal change in the one final mixture-domain Truth payload,
   objective/perceptual quality, decoder work, memory, and seek dependency.
5. Use bounded exact-small selection and deterministic beam/column generation
   for larger interacting sets.
6. Re-render the complete selected set from a clean decoder state.
7. Pack one final Truth and compare the complete candidate against direct
   Truth and every retained incumbent.

The graph's continuity, value, and protected-line scores may order steps 1–4.
They may not authorize a predictor record.

## Stress cases and kill conditions

| Counterexample | Required response |
|---|---|
| Two unresolved close tones | Preserve alternative/equivalence proposals; never collapse by proxy |
| Crossing chirps | Both identity assignments remain eligible until decoded RDO |
| Beating or destructive cancellation | Fit and render complex phase jointly before one Truth |
| Abrupt attack or phase reset | Birth/death or endpoint-locked knot; no hidden reset |
| Vibrato beyond the declared law | Add bounded knots or reject to Truth |
| Dense orchestra | Bound path count and accept no model unless final Truth falls enough |
| White/pink noise | Reject line overfit; stochastic or Truth remains eligible |
| Stereo delay/anti-phase | Compare shared oscillator plus complex route with independent channels |
| Very long lifetime | Check phase accumulator, seek checkpoint, and cumulative quantization exactly |
| Short clip | Full Basis/law overhead must be priced; long-input wins cannot hide a short loss |

Implementation is killed or revised if any of the following occurs:

- Python/C++/CUDA render or selector mismatch;
- a tile, frame, or input ordering changes the candidate set or decoded PCM;
- the synthesized prediction improves a proxy but enlarges the complete final
  Truth without a declared quality win;
- phase error is hidden by magnitude-only metrics;
- a neural or semantic result becomes necessary for decode;
- bounded resources cannot be declared before allocation;
- direct Truth is not retained bit-for-bit as a complete fallback.

## Scope of the first implementation

The first implementation must be a quarantined research transport, not a new
public bitstream opcode. It includes only independent complex partial paths,
the two phase-law families, integer synthesis, common cross-channel routing,
and one final Truth. Harmonic bundles, resonators, motifs, stochastic fields,
and learned initialization remain competing later proposals and cannot delay
falsification of the base predictor.

No predictor code is admitted until an independent auditor attacks this
preflight and every blocking objection is resolved in the decision log.
