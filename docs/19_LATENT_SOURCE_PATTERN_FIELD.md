# Latent Source Pattern Field

Status: **Research architecture / R-159 and R-160 normative draft**  
Last update: 2026-07-27

## 1. Claim

The useful object is not a recognized instrument, phoneme, speaker, or natural
sound. It is the shortest bounded decoder program that explains recurring
structure in the waveform:

\[
X_c[n] =
\sum_s Route_{c,s}\left(
\sum_e T(\theta_e)B_{s,k_e}[n-\tau_e]
\right)
+ R_c[n].
\]

`B` is an immutable multiscale Basis, `T` is a small fixed integer transform,
`Route` transfers an anonymous field between channels, and `R` is the final
Truth correction.

The encoder may use source separation, neural embeddings, pitch trackers,
fingerprints, sparse solvers, or semantic services as proposers. None of them
is trusted. Only decoded quality and complete serialized cost decide.

## 2. What prior work already provides

This direction is a synthesis, not a claim that every ingredient is new:

- blind source separation and MixIT infer latent additive components without
  isolated source labels;
- shift-invariant sparse coding and convolutional dictionaries place learned
  atoms at arbitrary times;
- convolutive NMF and phase-aware factorization model repeated
  time-frequency patterns;
- sinusoidal plus stochastic models separate coherent and noise-like laws;
- long-term prediction, audio mosaicing, REPET, and fingerprints find repeated
  temporal structure;
- MPEG object audio and Structured Audio carry reusable objects or synthesis
  instructions;
- neural audio codecs reuse learned codebooks.

The open combination is a codec with all of the following at once:

1. anonymous rather than semantic fields;
2. a per-track long-lived multiscale dictionary;
3. partial-spectrum and cross-channel reuse with phase;
4. discontinuous motifs whose steps may skip unrelated events;
5. a fixed bounded integer decoder ISA;
6. one final Truth correction;
7. actual complete-stream MDL/RDO against independent Truth.

This combination remains a research candidate. It is not yet a novelty, patent,
or standards claim.

## 3. Why production codecs do not already do this

### 3.1 The decomposition is not unique

For any mixture `x`, infinitely many pairs satisfy `x = u + (x-u)`. Recovering
the physically true sources from one mono or stereo mix is generally
impossible. Resonith avoids that impossible requirement: any anonymous
decomposition is legal if its complete decoder representation is cheaper.

### 3.2 Search is expensive

Selecting a minimum sparse dictionary is combinatorial. Arbitrary gapped
subsequences are exponential without a finite grammar. Conventional codecs use
local blocks and short predictors because they make encoder cost, memory,
latency, random access, and hardware bounds predictable.

### 3.3 A dictionary can cost more than the samples

One second of mono PCM16 at 48 kHz is 96,000 bytes. A long raw Basis only wins
after enough reuse. Therefore a large structure should usually be a grammar/DAG
of short Basis and persistent laws, not a copied minute-long waveform.

### 3.4 Mixtures hide repetitions

The same component under different overlap does not produce equal PCM or equal
magnitude spectra. Phase, channel transfer, time alignment, and the interfering
components must be fitted jointly. A magnitude-only nearest-neighbour search
produces false matches and expensive corrections.

### 3.5 Random access and error containment matter

An unlimited whole-track dependency graph compresses well in theory but is a
poor stream. The final syntax needs bounded checkpoints, dependency spans,
operation counts, memory, and deterministic recovery after corruption.

### 3.6 Modern codecs optimize a different engineering point

Opus, AAC-family codecs, EVS, and current neural codecs primarily optimize
short-delay local prediction or compact frame tokens. Their hardware,
packet-loss, and realtime constraints reward bounded local state. A
track-compiled global grammar permits much more encoder work but needs a new
standard object and decoder memory model.

## 4. Finite LSPF language

### 4.1 Basis

- arbitrary integer onset and duration;
- exact time-domain or perfect-reconstruction frequency-cell payload;
- local or CompoundBasis DAG;
- immutable after activation;
- complete payload and dependency cost charged once.

### 4.2 Transform

The first bounded family contains:

- crop and zero-filled integer alignment;
- polarity and gain/envelope;
- bounded fractional phase and pitch/time laws after normative promotion;
- spectral envelope and stable short filtering;
- forward/reverse/loop only when separately bounded and tested.

Finite Basis alignment never wraps its tail into its head.

### 4.3 Route

One field may feed multiple channels with bounded delay, gain, phase, envelope,
and stable transfer laws. The encoder searches the channel union; it does not
create an independent dictionary by default for every channel.

### 4.4 Sparse motif grammar

A motif is an ordered DAG of event references. Consecutive motif steps need not
be adjacent in the global ledger. Unrelated events and other anonymous fields
may occur in every gap.

The initial exact scalar law competition is:

- literal;
- constant;
- affine;
- run-length;
- modal value plus sparse indexed exceptions.

Longer chains are built only when their definition, occurrences, laws, and
remaining literals cost fewer actual serialized bytes.

### 4.5 Truth

All admitted fields are rendered and summed first. One final correction codes
the remaining waveform. Lossless requires exact PCM; lossy requires the
complete R-118 quality floor. A poor factorization loses automatically.

## 5. Encoder

The Foundry search is gridless in meaning and tiled in execution:

1. create exact perfect-reconstruction time-frequency cells;
2. generate direct and anonymous-layer candidates at overlapping multiscale
   origins;
3. fit finite gain, delay, phase, route, pitch/time, and envelope neighbours;
4. infer robust Basis consensus across differently contaminated occurrences;
5. turn verified occurrences into a sparse event ledger;
6. mine gapped paths and bottom-up CompoundBasis;
7. solve global dictionary activation and interval ownership;
8. render with the real bounded decoder;
9. add final Truth and compare the complete stream against every fallback.

CUDA evaluates large declared candidate lattices. Portable C++23 performs the
same integer fit for parity and shipping. Python remains a non-shipping
experiment/report controller.

## 6. Evidence so far

### Synthetic / Proxy

- changing-overlap anonymous Basis: 1,815 structured bytes versus 2,491
  independent proxy bytes, 27.14% smaller;
- exact SHA-256 reconstruction;
- ten transformed occurrences of one 128-sample Basis;
- one short candidate was correctly rejected at +49 bytes;
- a 24-occurrence cross-channel `0 -> gap -> 7` ledger selected an affine gap
  law while retaining unrelated intervening events;
- six focused tests pass under Python 3.14.6.

This evidence proves construction, exactness, and local signalling economics.
It does not yet prove complete audio compression or superiority over FLAC or
Opus.

## 7. Falsification

The mechanism is rejected or demoted if it cannot meet the R-160 kill gates:

- at least 15% complete-stream gain on controlled changing-overlap mixtures;
- correction no more than 50% of independent covered cost;
- at least 5% benefit over the best direct dictionary;
- blind inference within 15% of a known-stem oracle;
- at least 5% median lossless gain on a heterogeneous real corpus before
  promotion;
- no more than 90% of matched-quality Opus bytes at the first perceptual gate;
- no more than 30x track duration and 7 GiB VRAM for the declared Foundry
  profile;
- bounded CPU decode and no more than one second seek pre-roll.

The long-term 60%-of-Opus target is a research objective for structured
material, not a universal promise. Incompressible or weakly structured signals
must fall back honestly.
