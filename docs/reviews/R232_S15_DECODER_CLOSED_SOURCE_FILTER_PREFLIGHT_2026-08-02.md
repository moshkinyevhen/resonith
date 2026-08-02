# R-232 S15 decoder-domain source-filter candidate-rescoring preflight

Date: 2026-08-02

Status: **DRAFT FOR INDEPENDENT PRE-CODE AUDIT; CODE NO-GO**

## Problem and measurable objective

S15 asks whether anonymous source-filter excitation and slowly varying stable
resonator/formant state can improve the accepted S12 frontier. The current
R-120 SFT1/EPV1 experiment did not answer that question fairly: its encoder
derives short-term excitation from original source history and ranks fixed-
codebook candidates in the excitation domain, while its independent decoder
predicts from reconstructed output history and measures quality only after the
choice. Quantization error can therefore be amplified or spectrally reshaped by
the recursive synthesis filter after RDO.

The single R-232 hypothesis is:

> Replacing the R-120 excitation-domain final-candidate choice with exact
> decoder-state output-domain rescoring, without changing syntax, filter
> paths, scalar adaptive laws or candidate families, materially improves
> speech perceptual quality or complete size.

This is an encoder-policy experiment. It claims no new source-filter theory,
physical source recovery, bitstream, decoder, product or version.

## Frozen baselines

- current planning head before this record:
  `bc17697bfa9492172995c65c73d15e4ed85b6894`;
- accepted S12 aggregate SHA-256:
  `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`;
- accepted S12 registered-manifest SHA-256:
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`;
- unchanged pre-S11/direct-Truth producer:
  `ca87decf7d4b255bae11ce980e6f4be6fe3065f0`;
- current source-filter oracle SHA-256:
  `9a69b6d3d6c9fcd8159ef10f6d3306a65ac042087e516ee65c787318137f0abd`;
- current source-filter tests SHA-256:
  `c352f0fd2d55a9f9ad07f93ff1fe2117e05c446043dd0d2211d0d5596ab50c8f`;
- frozen R-232 configuration:
  `experiments/fixtures/r232_s15_frozen_configuration.json`, SHA-256
  `5fea557eb517f0e02f318e87f205ba116b0032e61b852a0dd3a8fe06a194e0fc`;
- pre-S15 `5aff74dbce41d7dece102a10f7ff326d7a700dda` incumbent
  eight-pulse SFT1/EPV1-v3 stream SHA-256 and size:
  `f0c3abf0a71ee7d40bdd4f5c022291264b8e39a40c2e9bdc58f14fd23f87a8a6`,
  12,554 bytes;
- R-120 eight-pulse decoded WAV SHA-256:
  `b105da972c12a373c826a1fee4a6911a1dc63cb08bcfe4b87851b7d3da50d873`.

The R-120 eight-pulse point has STOI 0.908976, ESTOI 0.846112, SNR
7.211959 dB and log-mel RMSE 1.190511. Its 10,294-byte five-pulse point is
smaller but has STOI 0.878153 and ESTOI 0.795882. Both remain rejected.

The accepted S12 direct-Truth results are 18,697 bytes, STOI 0.954079,
ESTOI 0.908387, SNR 20.1347 dB and log-mel RMSE 10.43225 on the 5.855-second
speech item, and 975,280 bytes, STOI 0.953386, ESTOI 0.887884, SNR 20.6356 dB
and log-mel RMSE 7.28469 on the 319.38-second speech item. The fixed official
Opus 1.6.1 anchors are respectively 18,702 and 975,265 bytes, with materially
better STOI, ESTOI and log-mel. No old fast diagnostic is substituted for the
S12 baseline.

The historical 12,548-byte R-120 artifact used EPV1 version 2. Before S15,
commit `5aff74dbce41d7dece102a10f7ff326d7a700dda` already used the bounded
EPV1 version-3 header, which adds three uint16 Basis fields (six bytes) while
decoding this reference to the identical WAV hash above. R-238 exposed the
stale envelope identity before any synthetic control ran. A clean archived
copy of that pre-S15 commit independently reproduced the 12,554-byte stream
and `f0c3ab...` hash, so the incumbent identity is corrected rather than
waived or learned from the S15 implementation.

## Prior art and novelty boundary

Source-filter coding is established prior art. Opus SILK decodes quantized
excitation through a five-tap long-term predictor and order-10/order-16 LPC,
with LTP state per 5 ms and LPC state per 20 ms. It also vector-quantizes and
interpolates LSFs. MPEG-4 HILN combines harmonic tones, individual sinusoidal
lines, LPC-envelope-shaped noise and transients. WORLD decomposes speech into
F0, spectral envelope and aperiodicity. Sinusoidal and harmonic-plus-noise
models likewise predate Resonith.

Primary sources:

- [IETF RFC 6716, Opus codec](https://www.rfc-editor.org/rfc/rfc6716.html);
- [Purnhagen, Low Bit-Rate Audio Coding Using HILN](https://heikopurnhagen.net/sigproc/diss-hp.pdf);
- [Morise et al., WORLD vocoder](https://www.jstage.jst.go.jp/article/transinf/E99.D/7/E99.D_2015EDP7457/_pdf/-char/en);
- [McAulay and Quatieri, sinusoidal speech analysis/synthesis](https://doi.org/10.1109/TASSP.1986.1164910);
- [Wang et al., neural source-filter waveform models](https://arxiv.org/abs/1904.12088).

R-232 therefore makes no novelty claim for LPC, LTP, pulse excitation,
harmonic/noise separation, interpolation or source-filter synthesis. The only
candidate differentiator is the future combination of anonymous long-lived
state, mutually exclusive excitation families, complete serialized-cost RDO,
actual-decoder Truth and unrestricted fallback. This experiment isolates only
decoder-domain final-candidate rescoring. It is not a fully joint decoder-
closed optimization of filter, adaptive pitch, pulse shape, Basis shortlist,
gain and primary-family choice.

## Alternatives and falsification

1. **No change.** This remains the default. It wins if R-232 misses one gate.
2. **Selected: exact decoder-domain final-candidate rescoring in existing
   SFT1/EPV1.** It changes the smallest independently falsifiable cause that
   can explain part of the R-120 quality failure and requires no decoder or
   syntax change. It does not claim to repair target-derived proposal bias.
3. **New SFT2 with five-tap LTP or continuous filter interpolation.** Rejected
   for this generation: it duplicates stronger SILK machinery, changes several
   variables and could indefinitely rescue a failed premise.
4. **Global interval DP over filter, pitch and excitation.** Deferred. The
   current quantized filter path and scalar adaptive law are frozen so R-232
   remains causal and attributable.
5. **Neural source-filter decoder.** Rejected for Main: model bytes, per-sample
   inference, portability and identity risks violate the bounded integer DSP
   target. Encoder-side neural proposals belong to S43/S49 only.
6. **Semantic speech classification.** Rejected. The mechanism receives no
   label and may be proposed for any mono PCM; complete RDO decides.

Mixtures and reverberation make excitation/filter factorization non-unique.
R-232 claims no true speaker, instrument or tract recovery. Existing stable
reflection-coefficient quantization, state order and deterministic tie breaks
remain canonical. Only the lowest complete-cost decoded candidate matters.

## Frozen algorithm

The existing R-120 filter path, filter Basis bank, block size, filter order,
EPV1 scalar adaptive state, PVQ/Basis/stochastic/ZERO families, pulse counts,
gain quantization, rate syntax and independent decoder remain byte-for-byte
unchanged between arms.

Both arms must consume the exact canonical configuration named in Frozen
baselines; command-line overrides are forbidden. It freezes block 128, order
10, parameter lambda 0, 16 filter bases with 8 iterations, 64-sample EPV1,
8 pulses, rate lambda 8192 Q20, quality guard 4096 Q12, adaptive guard 4608
Q12, no excitation Basis, seed `0x5245534f`, all remaining encoder arguments,
runtime identities and one execution thread. The runner seals each source PCM,
configuration and code identity before work. It emits the ordered candidate-
payload-field digest immediately before each winner choice. Within one arm,
the legacy and decoder-domain functionals are evaluated over that same sealed
list. Once a different winner is committed, later arm state and therefore
later realized candidates may causally differ; requiring cross-arm identity
after that point would suppress the recursive behavior under test. No
parameter, seed, candidate family or proposal budget may differ between arms.

The legacy R-120 procedure first chooses its adaptive state and constructs its
PVQ pulse shape, immutable-Basis shortlist and gain, stochastic and ZERO
candidates exactly as before. R-232 freezes that realized candidate set. It
then simulates and re-ranks only those candidates. Adaptive pitch/state and
candidate proposal are not jointly revisited. Consequently, `decoder-domain`
below means exact output simulation for the frozen realized candidate set; it
must never be reported as exact full closed-loop or jointly decoder-closed RDO.

Candidate proposal generation, including `_desired_short_excitation_target`,
adaptive-state search, pulse shape, Basis shortlist, stochastic proposal and
projected gain codes, runs byte-for-byte as in the legacy arm. Original PCM
used by that unchanged proposal is proposal-only and is never committed as
decoder state. For rescoring, every realized candidate starts from clones of
the same committed reconstructed excitation and reconstructed output
histories. Its adaptive-plus-fixed excitation is synthesized sample by sample
with the independent decoder's quantized filter, rounding, saturation and
state order; only candidate reconstructed output feeds later predictor
samples. Source PCM is used only as the distortion reference. Only the
selected candidate's histories are committed.

The legacy arm retains current excitation-domain RDO. The decoder-domain
rescoring arm computes for every realized candidate:

- serialized incremental bits;
- exact output-domain squared error;
- exact clipping count;
- a causal 256-sample, 40-band log-mel error using the committed decoded
  prefix plus candidate output.

The local bank reuses the published evaluation implementation's mel conversion,
triangular-bin construction and `log(E + 1e-10)` floor, configured explicitly
as 256 FFT samples and 40 speech bands. This is a local causal guard, not the
complete R-216 metric: the latter still runs on independently decoded outputs
at its frozen 256/512/1024 multiresolution settings and 512-sample primary FFT.
The 256-sample local window is left-zero-padded at stream start, contains no
future samples and uses one frozen periodic-Hann vector. Let `W(c)` be current-
subframe integer output SSE, `M(c)` the float64 mean squared difference of the
40 local log-mel values, `K(c)` the count of pre-saturation samples outside
int16 and `B(c)` the existing serialized incremental candidate bits. Let `L`
be the legacy-selected candidate. Candidate `c` is eligible exactly when
`K(c) <= K(L)`, `100*W(c) <= 101*W(L)` and `M(c) <= 1.01*M(L)`; when `M(L)` is
zero, `M(c)` must be zero. A non-finite value stops the experiment. `L` is
necessarily eligible.

Define `Dq20(c)` as round-half-to-even of
`2^20 * (W(c)/max(1,W(L)) + M(c)/max(1e-30,M(L))) / 2`. Select the
lexicographic minimum tuple
`(Dq20(c) + rate_lambda_q20*B(c), Dq20(c), B(c), M(c), W(c), mode,
canonical_payload_fields)`. `B(c)` contains only incremental causal bits known
at that choice, never future-stream bits. Complete bytes are evaluated after
full serialization.

The experiment emits both complete legacy and decoder-domain-rescored SFT1
streams.
Both are independently decoded. The accepted S12 stream is a third executed
arm and the fixed official Opus output is comparison context. No result may be
selected from encoder-side reconstruction.

## Truth ownership and complete cost

The source-filter inversion produces one excitation Innovation. Each subframe
uses adaptive prediction plus exactly one primary fixed family: PVQ, immutable
Basis, stochastic or ZERO. Families are alternatives, not stacked full
streams. Dictionaries, filter events, adaptive changes, gains, seeds, mode
bits, Innovation, RSC1/container bytes and padding are charged once.

The encoder records the exact source-minus-decoded result after independent
decode as an evaluation residual. Calling it Truth does not imply that it was
transmitted losslessly. No stochastic or optional perceptual output becomes
future predictor state outside the decoded source-filter stream.

## Claim ledger and minimal evidence

| Claim | Existing evidence reused | New minimal evidence | Failure consequence |
|---|---|---|---|
| original PCM remains proposal-only and never becomes decoder state | SFT1 independent decoder | one proposal-history witness and one committed decoded-prefix identity witness | stop before audio gate |
| realized-candidate synthesis matches decoder | SFT1/EPV1 round-trip tests | candidate-prefix versus complete independent decode | stop |
| local spectral guard is causal and correctly scoped | published mel-bank implementation | future-mutation and prefix invariance witnesses plus complete R-216 execution | stop |
| state never commits on rejected candidate | transactional Core precedent | history hash before/after forced reject | stop |
| known stable source-filter signal is representable | existing typed/source-filter tests | 120-second deterministic stable-AR plus periodic excitation | reject hypothesis |
| hostile unstructured signals do not regress inside the R-120 diagnostic | legacy SFT1 arm | white noise, impulse and two-component synthetic controls | reject rescoring or stop |
| real speech frontier improves | R-120, R-220 and R-221 outputs | long-first paid stream and residual-energy proxy, then short speech | reject hypothesis |

One focused test module and one experiment runner are the maximum new evidence
surface. No private ABI, test-only codec mode, second decoder, harness-testing
harness or recursive audit is allowed.

## Execution order and gates

1. Focused structural tests and the 120-second synthetic positive/negative
   controls. These controls falsify only the R-232 selector relative to the
   legacy SFT1 diagnostic; they cannot satisfy the paid S15 gate or stand in
   for an accepted S12 fallback.
2. Execute the 319.38-second LibriSpeech first.
3. Execute the 5.855-second speech item with the identical sealed
   configuration. No long-item result may alter an arm, parameter, threshold,
   proposal budget or candidate family.
4. If and only if the focused S15 gate passes, S16 executes the complete
   registered R-198/R-118 manifest against unchanged S12 and the fixed official
   maximum-effort Opus 1.6.1 anchors through actual decoders.

The untransmitted model-only diagnostic reports the integer SSE of
`source - independently_decoded_model_output`. On long speech it must reduce
that residual-energy proxy by at least 15% relative to the legacy SFT1 arm
without decoded-metric regression. It is never called bytes, bitrate, Truth
payload or a codec rate, and it is not added to the paid SFT1 stream. Only the
fully serialized independently decoded candidate may pass the paid gate.

The paid decoder-domain-rescored candidate passes focused S15 only if, on both
long and short speech, it satisfies one of these complete-stream alternatives:

1. at least 3% fewer complete bytes than accepted S12, with SNR, STOI and
   ESTOI no lower and log-mel RMSE no higher than S12 beyond
   `1e-12*max(1,abs(S12_value))` on the corresponding axis; or
2. bytes within 0.5% of accepted S12, all of STOI, ESTOI and log-mel improve,
   and SNR loses no more than 0.5 dB.

It must also close at least 10% of the S12-to-Opus gap on at least two of STOI,
ESTOI and log-mel on each speech duration. On synthetic white noise, impulse
and two-component mixtures, the rescored SFT1 diagnostic must be no larger and
must not regress any applicable complete R-216 axis beyond
`1e-12*max(1,abs(legacy_value))`; otherwise R-232 is rejected before real
audio. This is not an S12 comparison or fallback claim. Mozart, registered
noise and registered transient inputs in S16 must execute the exact accepted
S12 fallback when the paid candidate does not independently pass the same
per-file rule; unsupported stereo does not silently become a mono claim.

S16 admission additionally requires every registered item, complete bytes,
actual decoded PCM, all R-216 axes, encode/decode wall and CPU time, peak RSS,
GPU use, state/event/dictionary/correction attribution, hashes, fallbacks and
regressions. A rate-only or quality-only win receives one bounded refinement of
the missing axis inside this generation before freeze.

## Resource and remediation bounds

- focused structural tests: 120 seconds wall, 2 GiB peak RSS, 256 MiB output;
- each synthetic control: 900 seconds wall, 3 GiB peak RSS;
- long speech: 7,200 seconds wall, 4 GiB peak RSS, 4 GiB working storage;
- short speech: 900 seconds wall, 3 GiB peak RSS;
- retained S15 evidence: 8 GiB total;
- one correctness remediation is permitted after audit; a second design or
  resource failure closes R-232 as rejected.

The runner must atomically publish per-input receipts and fail closed on hash,
decoder, ledger, metric, time, memory or storage mismatch. No blind retry,
threshold retuning, extra candidate family or resource-ceiling increase follows
an observed result.

## Required independent decisions

1. A read-only auditor must return binary GO on this exact preflight before
   code.
2. After the one runner and one focused test module exist, an independent
   implementation audit must return GO before long execution.
3. A read-only result audit is mandatory before S15 can pass, fail or advance
   to S16.

Until the first decision is recorded, S15 code and execution remain **NO-GO**.
