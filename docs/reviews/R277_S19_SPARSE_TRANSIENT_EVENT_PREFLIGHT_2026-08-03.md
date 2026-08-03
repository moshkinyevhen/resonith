# R-277 S19 Sparse Transient Event Preflight

Date: 2026-08-03

Status: **PRE-CODE CANDIDATE; IMPLEMENTATION BLOCKED PENDING INDEPENDENT GO**

## Problem and objective

S19 asks whether a bounded, sample-addressed transient event can remove enough
attack-local burden from the accepted S12 lapped Truth stream to reduce complete
bytes while preserving or improving decoded attack quality. The experiment is
not a general transient redesign and makes no novelty claim for short blocks,
wavelets, sparse audio atoms, or temporal noise shaping.

The frozen incumbent is the accepted R-221/S12 direct-Truth generation, run
identity `470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c`,
source revision `1c45376eebe7daa49904acae885c47d6d571cf87`, aggregate SHA-256
`f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`,
and registered-manifest SHA-256
`551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`.
The complete cost is transient section bytes plus the one final S12 Truth
section plus every outer header, length, checksum, configuration, integrity,
and padding byte. Predictor bytes are never compared with residual bytes alone.

## Evidence and alternatives

The following alternatives were considered before code:

1. **No change.** This is the mandatory incumbent and per-file fallback.
2. **R-044 variable LiftPack lifetimes.** This exact partitioning mechanism won
   three of three clips but averaged 2.42%, below its frozen 3% gate. It remains
   historical Pareto evidence and is not reopened as S19.
3. **Opus-like short-window and per-band time-frequency switching.** RFC 6716
   already specifies multiple short MDCTs and per-band time-frequency choices.
   Resonith R-064 found that its 512-sample half-window beat the 128-sample
   all-short oracle on SNR, multiresolution spectral convergence, and mean
   pre-echo for all three clips. Transition state, signalling, and anti-collapse
   behavior are therefore unjustified here.
4. **Temporal Noise Shaping.** Herre and Johnston show that prediction over
   spectral coefficients can shape quantization noise in time and can help
   pitched signals where block switching is inefficient. It is plausible, but
   it changes the lapped-Truth coefficient layer and belongs to a separately
   audited experiment only if S19 exposes a remaining temporal-noise defect.
5. **Existing raw PCM16 transient records.** R-024's forced transient path was
   0.72% larger. Raw samples are retained as a conformance control, not as the
   compression candidate.
6. **Sparse event representations.** Sparse event/time audio models and sparse
   trigonometric dictionaries are established prior art. The selected
   Resonith experiment is narrower: deterministic sample-accurate events,
   bounded integer reconstruction, complete-byte selection, and exactly one
   final mixture-domain Truth.

Primary references:

- [RFC 6716, CELT transient and time-frequency coding](https://www.rfc-editor.org/rfc/rfc6716.html#section-4.3.1)
- [Herre and Johnston, Temporal Noise Shaping](https://www.ee.columbia.edu/~dpwe/papers/HerreJ96-noisesh.pdf)
- [Vinyard, Toward a Sparse and Interpretable Audio Codec](https://arxiv.org/abs/2505.05654)
- [Rebollo-Neira, Trigonometric Dictionary Based Codec](https://arxiv.org/abs/1512.04243)

## Frozen hypothesis

For channel `c`, event `j`, onset `o_j`, and power-of-two support `N_j`, the
prospective decoder constructs a sparse integer Haar-lifting coefficient vector
`q_j`, dequantizes it by the declared power-of-two step `s_j`, and reconstructs

`e_j[n] = InverseHaar(s_j * q_j)[n]` for `0 <= n < N_j`.

Events in one channel cannot overlap. Different channels are paid independently
and share no payload. The predicted signal is accumulated in signed wide
integer arithmetic:

`p_c[t] = sum_j e_j[t - o_j]`.

Exactly one accepted-S12 Truth stream encodes `x - p`. The output is

`y = Saturate16(p + DecodeS12Truth(x - p))`,

with one final saturation. An event contributes exact zero outside its
half-open support. No stochastic tail, resonator, motif reuse, semantic source,
cross-channel transfer, persistent state, or second residual is allowed.

The falsifiable prediction is that attack-local sparse lifting removes a cost
that the incumbent lapped Truth otherwise pays inefficiently. If complete
bytes and onset diagnostics do not pass the frozen gate, this exact S19 model is
closed rather than enlarged.

## Prospective TSE1 grammar

`TSE1` is an experimental, non-normative critical `RSC1` section until the gate
passes. The candidate outer stream uses profile `0`, level `5`, and timebase
equal to the sample rate, exactly like the incumbent. It contains exactly one
`CONF`, one `LPF1`, and one `TSE1` section. The `CONF` payload is byte-identical
to the incumbent; `LPF1` preserves every incumbent codec-setting and invariant
header field while its entropy body encodes the residual. Every derived field
is recomputed canonically: transform `frame_count` equals the incumbent because
the residual has identical dimensions, while `raw_bytes`/entropy-payload length
is the residual payload's actual byte count. All three sections use
schema version `1`, flags `SECTION_CRITICAL`, instance ID zero, and start tick
zero. The `LPF1` section is the one and only accepted-S12 Truth stream,
now applied to the residual. Directory,
section, checksum, hash, alignment, and padding bytes are part of complete
candidate cost. If no event survives the final selector, the encoder emits the
exact complete incumbent two-section RSC1 file; it must not emit an empty
`TSE1` section or a new wrapper.

All multibyte integers are unsigned little-endian unless explicitly described
as signed. The 40-byte `TSE1` payload header is:

| Offset | Bytes | Field | Canonical value or bound |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `TSE1` |
| 4 | 1 | version | `1` |
| 5 | 1 | flags | `0` |
| 6 | 2 | header bytes | `40` |
| 8 | 4 | total frames | equals `CONF` |
| 12 | 4 | sample rate | equals `CONF` |
| 16 | 2 | channels | equals `CONF`, `1..8` |
| 18 | 2 | reserved | `0` |
| 20 | 4 | event count | `1..4096` |
| 24 | 4 | coefficient count | `1..131072` |
| 28 | 4 | support-sample count | `1..2097152` |
| 32 | 4 | payload bytes | exactly `40 + sum(record_bytes)` |
| 36 | 4 | body CRC-32 | IEEE reflected polynomial `0xedb88320`, initial and final XOR `0xffffffff`, over bytes `[40,payload_bytes)` |

Each event begins with this exact 20-byte header:

| Offset | Bytes | Field | Canonical value or bound |
|---:|---:|---|---|
| 0 | 1 | channel | `< channels` |
| 1 | 1 | support log2 | `5..9`; `N = 1 << value` |
| 2 | 1 | step log2 | `0..8`; `s = 1 << value` |
| 3 | 1 | position width | equals support log2 |
| 4 | 4 | onset | absolute sample address; widened checked `uint64(onset) + N <= total_frames` |
| 8 | 2 | coefficient count `K` | `1..min(N,128)` |
| 10 | 2 | position bit count | exactly `K * position_width` |
| 12 | 2 | position byte count | exactly `ceil(position_bit_count / 8)` |
| 14 | 2 | value byte count | exact following canonical ULEB128 length |
| 16 | 2 | record bytes | exactly `20 + position_byte_count + value_byte_count` |
| 18 | 2 | reserved | `0` |

The header is followed first by the `K` raw coefficient positions, strictly
increasing and packed least-significant bit first at exactly `position_width`
bits each. Unused high bits of the last byte are zero. Values then follow in
position order as minimal unsigned LEB128 of ZigZag codes: `2*v` for `v >= 0`
and `-2*v-1` for `v < 0`. Every `v` is non-zero and
`abs(v) <= 8388607`; ULEB128 groups carry seven low bits and use bit 7 only as
the continuation flag. The decoder rejects a fifth value byte and checks the
remaining shift and value bound before every left shift or accumulation.
Overlong, unterminated, or non-minimal ULEB128, trailing payload,
non-zero padding, incorrect lengths or counts, unknown fields, and aggregate
mismatches are malformed.

Every header/record offset, record end, onset end, aggregate count, support
sum, payload length, memory size, and work total is accumulated with checked
64-bit arithmetic before conversion or comparison; overflow is malformed or a
typed profile-bound failure before allocation or output.

Records are strictly ordered by
`(channel, onset, support_log2, step_log2, position-vector, value-vector)`.
Within a channel, `next.onset >= previous.onset + previous.N`; adjacent events
are valid. A second parse-and-pack must reproduce the complete `TSE1` payload
byte for byte.

The sparse coefficient vector `q[0..N)` is signed 64-bit, zero-filled, with the
declared values at the declared positions. Checked multiplication produces
`z[i] = q[i] * s`. Each inverse Haar stage pairs `low,diff` and computes
`even = low - floor(diff / 2)` and `odd = diff + even`, with mathematical floor
for a negative odd `diff`. At most nine stages execute. From the coefficient
and step bounds, the conservative magnitude bound
`2^31 * (3/2)^9 < 2^37` holds, so every operation fits signed 64-bit; an
implementation nevertheless uses checked arithmetic and rejects overflow.
The expanded event is rejected unless every sample fits signed PCM16.

For encoding, each event window is taken from original PCM `x`, never from a
previous proposal. Forward lifting uses the inverse equations' exact reversible
counterpart. Quantization is signed nearest with ties away from zero. For a
fixed window, non-zero coefficients are ranked by descending absolute
quantized value and then ascending coefficient index. Retained counts are
`1,2,4,8,16,32,64,128`, clipped to support and non-zero count. Before invoking
the unchanged S12 encoder, the proposal is rejected unless every sample of
`r = x - p` fits signed PCM16. Decode obtains signed PCM16 Truth `r_hat`, adds
the expanded event in signed 64-bit, and performs the sole final PCM16
saturation. This ranking is a proposer rule; only the complete packed file and
decoded output can admit a candidate.

## Frozen proposal search

The detector observes PCM only and never enters the bitstream:

1. Per channel, compute `d[n] = abs(x[n] - x[n-1])` in signed 64-bit
   arithmetic for every integer `n` from 1 through `total_frames-1`; the index
   of `d[n]` remains the PCM sample index `n`. If `total_frames < 2`, there are
   no peaks and the complete incumbent is returned byte for byte without
   computing a median.
2. Compute the lower median `m` of `d` and lower median absolute deviation
   `a`. The threshold is `max(2048, m + 10 * max(a, 1))`.
3. A threshold candidate satisfies `d[n] >= threshold`. Intersect its inclusive
   neighborhood `[n-8,n+8]` with the valid `d` indices
   `[1,total_frames-1]`; retain `n` iff it is the earliest argmax of `d` in
   that clamped neighborhood.
4. Rank peaks by descending `d`, then channel and sample. Retain at most 4096.
5. For every peak and support `N`, search pre-rolls
   `{0, N/16, N/8, N/4}` and sample offsets
   `{-8, -4, -2, -1, 0, 1, 2, 4, 8}`. Out-of-stream windows are absent, not
   padded. The absolute candidate onset is
   `o = peak_sample - pre_roll + sample_offset`; the window is exactly
   `x[o:o+N, channel]` from original PCM.
6. Evaluate all frozen quantization steps and retained counts. Keep the
   byte/SSE Pareto frontier per `(channel, peak, N)`. The byte axis is the
   exact `record_bytes` of the canonical event. The error axis is
   `sum(n=0..N-1) (int64(x[o+n,channel])-int64(e[n]))^2`, accumulated in
   checked unsigned 64-bit arithmetic. Record A dominates B iff A is no larger
   on either axis and strictly smaller on at least one. Exact equal-axis cases
   use the exact reconstruction-cost score `K + 12*N`, then earlier onset,
   shorter support, smaller
   step, fewer coefficients, then lexicographically smaller packed bytes.
   Enumeration order is peak rank, ascending support, listed pre-roll order,
   listed offset order, ascending step, then listed retained-count order.
   Within each `(channel,peak,N)` group, byte-identical records retain their
   first enumeration tuple before Pareto construction. After all group
   frontiers are formed, byte-identical records are deduplicated globally by
   retaining the lowest peak rank and then the earliest remaining enumeration
   tuple. Candidate and frontier bounds are applied only after that specified
   stage.
7. For a candidate `[o,o+N)`, set the lapped influence halo to one accepted-S12
   half-window `H = 512` on each side. With checked arithmetic, set
   `start = max(0, floor((o-H)/H)*H)` and
   `end = min(total_frames, ceil((o+N+H)/H)*H)`; no padding is permitted. Slice
   `[start,end)` from all channels. Encode two independent complete local RSC1 streams with the exact
   S12 settings: original local PCM and local residual with only this event in
   its channel. The heuristic price is the transient record's exact bytes plus
   residual-local complete bytes minus original-local complete bytes. Local
   restarts and overlapping lapped halos make these prices deliberately
   non-additive; no independence claim is made.
8. One canonical non-overlapping interval dynamic program per channel selects
   the subset minimizing the sum of those frozen heuristic prices; the empty
   set has cost zero. The channel sets are then united. Equal summed prices use
   lower summed reconstruction-cost score `sum(K + 12*N)`, fewer events, then lexicographically
   smaller concatenated records. The united set is applied
   once to original PCM, packed with one whole-stream S12 residual, decoded,
   and compared with the unchanged complete incumbent. Actual whole-stream
   bytes, not the heuristic sum, decide selection and admission.

The frozen grid contains at most `4096 * 5 * 4 * 9 * 9 * 8 = 53,084,160`
raw tuple trials over the globally retained peaks. Invalid windows and
duplicate packed records follow the exact step-6 elimination order. The search
materializes no whole-track PCM copy per proposal. Candidate fields are
streamed; at most 131,072 Pareto proposals and 4096 selected events may be
retained. Enumeration count, deduplicated count, retained count, exact order,
local-encode count, S12-encode count, and every work/memory bound are recorded.
A bound hit produces a typed profile-negative exact complete S12 fallback and
a machine receipt, never silent candidate rejection.

## Decoder and encoder resource profiles

The prospective decoder profile is fixed before code:

- at most 8 channels, 4096 events, 131,072 sparse coefficients, and 2,097,152
  total event-support samples per stream;
- at most 512 support samples and 128 coefficients per event;
- at most 2 MiB immutable transient payload per stream;
- before playback, validation expands supports consecutively in canonical
  record order into a persistent PCM16 event bank of at most 4 MiB and builds
  an absolute-onset index containing channel, onset, support, and bank offset
  at
  most 128 KiB; section payload, expanded bank, and index total at most
  6.125 MiB;
- at most 32 KiB transient scratch while parsing and expanding one event;
- validation derives and charges the canonical resource score `K + 12*N`
  before output for every reconstructed event; this is the selector and
  profile score rather than a claim about literal machine instructions, and no
  trusted work declaration is read from the file;
- no allocation, transform, parsing, or coefficient expansion in the audio
  callback; callback work is bounded PCM16-bank addition only;
- seek and callback entry binary-search the immutable per-channel onset spans;
  they then add only intersecting samples from the consecutive bank and never
  perform inverse lifting or reparse coefficient bytes;
- validation and operation-budget failure leave output, cursor, and state
  unchanged.

The S19 Foundry research profile is distinct from the decoder profile:

- long input: 7,200 seconds wall, 8 GiB peak RSS, and 8 GiB working storage;
- each short input: 1,800 seconds wall, 4 GiB peak RSS, and 2 GiB working
  storage;
- at most 16 CPU threads; GPU use is optional and must not alter candidates,
  order, bytes, or PCM;
- two deterministic executions use identical input, tool, source, and seed
  identities.

The frozen S12 decoder is retained at
`artifacts/r277-s19-authority/s12-baseline-core.dll` and is never rebuilt or
overwritten. Candidate native code is configured and built only in
`build/r277-s19-cpp23-clang22-ninja`; pre/post-build checks rehash the baseline
artifact, and any identity change fails before comparison.

These ceilings are profile gates, not information-theory verdicts. They are
not raised after observing a run. A hit closes this exact S19 generation as
profile-negative and preserves only a separately re-audited streaming
implementation for S47/S48.

## Frozen execution order and corpus

The first real gate is the 319.38-second mono LibriSpeech source
`G:/Resonith/artifacts/corpus/librispeech-r220/librispeech-speaker-long-5min.wav`,
file SHA-256
`0191f7d14edfc27ec9f0354adc9cbba77fc2482c5fd09505ffc5463ecb7316c8`,
PCM16 SHA-256
`335384eab75a6a092adf5003c732a44b8a0ff9d4e710c3e8897d626f224d1b7f`.
If it reaches a terminal codec verdict, the short gate follows:

- positive: registered EBU claves, registered EBU side drum, and licensed
  `patro-de-bateria`;
- negative ownership controls: registered EBU sustained sine and EBU pink
  noise;
- synthetic conformance: impulses at every S12 transform-hop boundary phase,
  positive and negative full-scale limits, adjacent supports, malformed sparse
  counts and positions, callback partitions, and seek before, into, and after
  an event.

No corpus expansion occurs inside this generation. If the focused gate passes,
S20 runs the complete registered 19-item corpus and the preceding Resonith
generation. The retained R-217 direct official Opus 1.6.1 point (true VBR,
complexity 10, 20 ms, zero expected loss, no padding, bitrate-only calibration)
may be reported only as contextual evidence; it is not called maximum effort.
S20 must execute the frozen R-166 maximum-effort frontier over all applicable
lawful Opus controls, including any missing-axis refinement required by the
current comparison policy. Quality never selects an Opus rate.

## Admission and kill gate

All predicates are mandatory:

1. The long input selects at least one event, is strictly smaller than S12 in
   complete bytes, and passes every quality and resource guard. Otherwise the
   exact S19 hypothesis closes before short tuning.
2. At least two of three transient-positive files save at least 3.00% complete
   bytes against S12, and their arithmetic-mean saving is at least 3.00%.
   For a file, saving is the exact rational
   `(S12_complete_bytes-S19_complete_bytes)/S12_complete_bytes`; the 3% test
   uses integer cross-multiplication against `3/100`. The aggregate test sums
   the three exact rationals, divides by exactly three, and compares the result
   to `3/100` without binary floating point. Numerators and denominators are
   published.
3. The complete comparable key set returned by the frozen R-216 `quality_axes`
   function must be identical between S12 and S19. Relative to S12: any SNR,
   SI-SDR, segmental-SNR, channel-SNR, or other decibel axis whose direction is
   `max` may decrease by at most 0.005 dB; log-mel RMSE, log-spectrum distance,
   and every multiresolution-STFT error may increase by at most 0.005;
   magnitude cosine and every per-channel or interchannel circular coherence
   may decrease by at most `0.00001`; phase MAE/RMSE may increase by at most
   `0.001` radian; correlation and mid/side-ratio errors
   may increase by at most `0.00001` and 0.005 dB respectively; speech
   STOI/ESTOI may decrease by at most `0.0005`; maximum absolute waveform error
   may increase by at most one PCM16 sample and RMS error by at most 0.05
   PCM16 sample. Metric applicability and every reliable-bin count must equal
   the incumbent. Every channel and registered stereo diagnostic is tested,
   not only the aggregate.
4. On each positive, mean and worst pre-echo may regress by at most 0.25 dB.
   Mean pre-echo improves by at least 1.00 dB on at least two positives, using
   the exact frozen R-216/R-221 implementation: 3 ms analysis window, half
   analysis-window hop, at most eight onsets, and 10 ms pre-onset and attack
   regions. No 2 ms substitute is used.
5. Sustained sine, pink noise, every no-event result, and every rejected or
   profile-negative result select the exact complete incumbent S12 file byte
   for byte, with no `TSE1` section, and therefore identical decoded PCM.
6. Two runs produce byte-identical streams and PCM. Reference/native and
   scalar/optimized decode are identical; callback partitioning and seek are
   equivalent; malformed input fails closed; decoder memory and work remain
   within the derived profile bounds; no intermediate clipping or unauthorized overlap is
   permitted. Every inner-`TSE1` grammar mutant is re-packed with valid outer
   RSC1 length, CRC, and SHA fields so it reaches the intended inner check; only
   the dedicated TSE1-body-CRC mutant intentionally retains a wrong inner CRC.
7. The report publishes complete bytes, bitrate, all R-198 metrics, onset
   diagnostics, event/support/coefficient counts, encode/decode time, CPU/GPU,
   peak RSS, working storage, operation counts, hashes, fallbacks, wins,
   losses, and every bound hit. Listening files are diagnostic and cannot
   override a failed deterministic gate.

Failure closes this exact candidate. No short-window mode, TNS filter,
stochastic tail, overlap, dictionary, resonator, extra entropy coder, relaxed
tolerance, larger resource ceiling, or second Truth is added to rescue it.

## Ownership boundary

S21 owns stochastic tails and fields; S23 owns reusable event dictionaries;
S33-S36 own persistent phase and cross-channel phase/delay/polarity; S37 owns
resonant decay; S39 owns multi-family global competition; S47/S48 own scalable
full-lattice Foundry execution. S19 pays every transient independently and
compares only `no change` with `bounded sparse transient + one final S12 Truth`.

## Required independent decision

No syntax, source, test, or production behavior may change until an independent
auditor verifies the baseline identities, grammar, arithmetic, complete-byte
closure, resource declarations, corpus, admission predicates, and ownership
boundary and issues an explicit GO. The immutable pre-code authority is
`experiments/fixtures/r277_s19_authority_v1.json`, SHA-256
`873c2e1d8f11288816ab3f1f7af39b8ed81ac903c5296a0238d8bf01e3f2b862`;
it transitively binds the
registered R-221 evidence, current output-identical S12 sources and decoder,
runtime, focused long/short inputs, synthetic vectors, implementation
allowlist, and line cap. After focused implementation tests but before any
real-audio gate, a second sealed execution manifest must bind all new sources,
binaries, commands, dependencies, input/output expectations, and the authority
manifest, and must receive a separate independent GO.
