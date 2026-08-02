# R-216 S12 Opus-only registered comparison preflight

Date: 2026-08-02
Status: **DRAFT V4 FOR NARROW INDEPENDENT PRE-IMPLEMENTATION AUDIT**
Codec algorithm change: no. This is the evidence boundary for the already
frozen and independently audited R-215 S11 generation.

## Owner-directed scope

The project owner narrowed this run to **R-215 S11 versus official Opus only**.
S12 therefore makes no claim against the preceding Resonith generation and
does not read, decode, select, or republish preceding Resonith streams.

This explicit scope replaces the earlier draft's incumbent work. The complete
registered source corpus, long-first order, actual decoders, full-file byte
accounting, objective metrics, resource measurements, and maximum-effort Opus
search remain mandatory.

## Problem, objective, and complete cost

The focused R-215 gate proves only that the S11 language can recover and price
anonymous persistent partials on bounded synthetic evidence. S12 must measure
whether its actual decoded real-audio streams lie on a useful size/quality
frontier against official Opus.

The primary comparison is decoded quality at strictly matched complete stream
bytes. The complete cost also includes analyzer/encode/decode wall and process
CPU, peak resident memory, temporary and retained storage, declared CPU/GPU
work, deterministic hashes, fallback behavior, and failure containment.
Aggregate results may not hide a failed item.

## Frozen executable manifest

The only registered input manifest is
`experiments/fixtures/r216_s12_registered_manifest.json`, schema
`resonith-r216-s12-opus-only-manifest-2`, SHA-256
`551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`.
The runner rejects any other schema, hash, count, duplicate ID, source file
hash, PCM payload hash, shape, order, or S11 configuration.

It contains exactly 19 unique rows in this order:

1. full Mozart, 400.772667 seconds;
2. all 16 R-111 rows, each 12 seconds, sorted by stable ID;
3. the registered first 8.0 seconds of Emotional Piano;
4. complete pinned speech, 5.855 seconds.

The Emotional Piano origin is 16 seconds, but the accepted
`real_music_corpus.json` pins its first 8.0 seconds. The registered PCM WAV is
SHA-256
`37d28f15c8b3ecb13c2c161049c39d5de18f0c1b7e5f4a832684dd8059afdab5`.
The full Mozart row is the mandatory long gate. Mozart executes and freezes
before any short row. All later rows are duration-descending, then ID-ascending.

The manifest freezes the prepared R-111 manifest, real-music corpus, every
source file and canonical interleaved PCM16 payload hash, rate, channel count,
frame count, duration, categories, and S11 coefficient budget. The R-117
reports are configuration provenance for those coefficient budgets only; no
R-117 stream or metric enters the comparison.

Logical public roots are mapped to local roots only by explicit runner
arguments. Absolute personal paths are not published.

## Frozen R-215 challenger

- source revision:
  `7e2726789ca980177a32e6b36cfcd9f1d90b5463`;
- predictor SHA-256:
  `583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec`;
- native Golden Core SHA-256:
  `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed`;
- Python wrapper SHA-256:
  `32c514e5c9cf4f1beffba61c62d262489f35e2fb0c2e74c3cfdae2a132694045`;
- per-row coefficient budget from the manifest;
- `half_window=512`, `band_count=24`, bounded entropy, fixed transform,
  adaptive density, frozen S11 language and immutable cosine Basis family.

Each row executes the actual lapped Truth encoder, analyzer when within its
frozen bound, native graph, MFT1/CBF1 lowering, complete residual, current
native decoder, and direct-Truth fallback. The encoded payload is decoded
again from bytes through the bounded current decoder; only that PCM is scored.
No S13 mechanism or post-Mozart threshold change is allowed.

### Exact analyzer-bound behavior

Before allocating observations, compute the same bound as
`observe_complex_partials`:

\[
F=\sum_r(\lceil N/h_r\rceil+1),\qquad O=F(C+1)K.
\]

Here \(N\) is source frames, \(C\) channels, \(h_r\) each frozen resolution
hop, and \(K\) observations per detector frame. If \(O\) exceeds
`maximum_observations=3,500,000`, record the count and produce only the S11
direct-Truth candidate without invoking the analyzer. Full Mozart predicts
28,405,440 observations, so this is expected negative evidence, not a reduced
search or crash.

If the analyzer is invoked, only the exact
`ValueError("R-186 observation manifest exceeds its hard bound")` may map to
that explicit fallback. Every other exception, malformed result, native status,
timeout, or resource failure is hard. Broad exception handling is forbidden.

## Maximum-effort official Opus contract

Frozen tools:

- `opusenc` SHA-256
  `0b8d4e8db7697bd8981e9246de1bd8a1df05c2bbb98bba2b2090d7bb585e70f9`;
- `opusdec` SHA-256
  `ea1a553102020f58f0af86eb1cf2377a055ccbc93a2130fa62f77c96f522c8e3`;
- opus-tools `0.2-39-g9b1ca51`, libopus `1.6.1-8-g475cbc5`.

For each S11 complete-byte target, first enumerate every applicable named
public `opusenc --help` coding control:

- VBR, CVBR, and hard CBR;
- auto, music, and speech tuning;
- 2.5, 5, 10, 20, 40, and 60 ms frames;
- phase inversion enabled and disabled for stereo, enabled for mono;
- complexity 10, expected loss 0, maximum container delay 1000 ms,
  discarded comments and pictures, and zero padding.

This base stage gives 108 configurations for stereo and 54 for mono. Channel
downmix is excluded because it changes the registered output-channel contract.
`--channels` is an input mapping override, not a coding-quality choice.

Stable public libopus CTLs exposed by opusenc through `--set-ctl-int` receive a
second bounded stage. From the strict-byte base points, choose the best point
on each of these reference-applicable axes, with byte proximity then canonical
configuration as ties: SNR, SI-SDR, segmental SNR, magnitude cosine, RMS,
maximum error, log-mel, log-spectral distance, phase RMSE, worst transient
error, channel-correlation error, mid/side error, STOI, and ESTOI. Add the
deterministic listening point, deduplicate, and cap the resulting set at 15
seeds; the listed order is the cap order.

For every seed, byte-refine and test all ten bandwidth constraints:

- `OPUS_SET_MAX_BANDWIDTH_REQUEST=4004` with values 1101..1105;
- `OPUS_SET_BANDWIDTH_REQUEST=4008` with values 1101..1105.

For stereo, cross every bandwidth mode, including automatic bandwidth, with
`OPUS_SET_FORCE_CHANNELS_REQUEST=4022` values `OPUS_AUTO=-1000` and mono `1`.
Forced mono preserves the two-channel decoded shape but intentionally removes
stereo information, so channel metrics can reject it. Mono inputs use only
`OPUS_AUTO`. Duplicate canonical tuples are removed before execution.

The maximum is therefore 423 stereo configurations (108 base plus 15 times
21 new CTL combinations) or 204 mono configurations (54 base plus 15 times
10). This is a frozen hierarchical maximum-effort search, not an unbounded
cross-product of private or experimental CTLs. DTX, FEC, expected loss,
prediction disabling, DRED, QEXT, and decoder enhancement controls are
inapplicable to intact offline quality at equal complete bytes and remain at
their official defaults. Every inclusion, exclusion, CTL integer, and argv is
published.

Each configuration gets one initial bitrate and exactly three actual-byte
feedback refinements within 6..256 kbit/s/channel. Bitrate state is an integer
`q5` in units of 0.00001 kbit/s. Compute the initial state by integer
round-half-even of
`target_bytes * 8 * 100000 * sample_rate / (frame_count * 1000)`. Compute each
next state by integer round-half-even of
`previous_q5 * target_bytes / actual_bytes`, then clamp. Pass the CLI exactly
five decimal digits. Retain every actual point in the machine report. The old
one-point-per-configuration filter and any below-target escape are forbidden.

Strict complete-byte tolerance is:

\[
T_b=\max(64,\lfloor target\_bytes/1000\rfloor).
\]

Only points satisfying \(|bytes-target|\le T_b\) are matched. No strict point
means Opus is unmatched for equal-rate language. Score all strict points and
publish the full non-dominated quality Pareto set; no SNR-only winner stands
for Opus.

For one listening artifact, choose deterministically from that set:

- speech rows: highest ESTOI, STOI, lowest log-mel, highest SI-SDR, closest
  bytes, then configuration tuple;
- other rows: lowest log-mel, highest SI-SDR, lowest phase RMSE, lowest
  transient error, closest bytes, then configuration tuple.

The overall report compares S11 against the complete strict Pareto envelope,
not only this convenient listening point.

Every encode receives an exactly derived nonzero uint32 `--serial`. Hash this
byte string with SHA-256:

1. ASCII `resonith-r216-opus-serial-v1` followed by one zero byte;
2. the 32 raw manifest-digest bytes;
3. uint16 little-endian UTF-8 item-ID length and the item-ID bytes;
4. uint8 mode code (`vbr=0`, `cvbr=1`, `hard-cbr=2`);
5. uint8 application code (`auto=0`, `music=1`, `speech=2`);
6. uint32 little-endian frame duration in microseconds;
7. uint8 phase-inversion flag;
8. int32 little-endian bandwidth request (`0`, `4004`, or `4008`) and value
   (`-1000` for automatic, otherwise 1101..1105);
9. int32 little-endian force-channel value (`-1000` or `1`);
10. uint64 little-endian requested bitrate in units of 0.00001 kbit/s, rounded
    once by decimal half-even from the canonical decimal feedback value.

Interpret digest bytes 0..3 as little-endian uint32; map zero to one. No JSON,
locale float, path, attempt number, or wall time enters this domain. Retain raw
Ogg SHA-256 and the existing serial/CRC-normalized SHA-256. Repeating an
identical point must reproduce raw Ogg bytes.

Encode and decode subprocess timeout is \(\max(120,2D+30)\) seconds, where
\(D\) is source duration. A timeout is hard failure, not an unmatched point.

## Metrics and edge cases

All metrics use actual decoder PCM16 with exact source rate, channels, frames,
and zero sample offset. No resampling, delay search, trim, padding, gain
alignment, or cached metric is allowed. Shape or rate mismatch is hard. The
runner does not call the existing CLI `main()` or `_align()` path.

Frozen existing code:

- `experiments/objective_audio_metrics.py`, SHA-256
  `284e27fca406775e90f0c0db075808b5203c9075600ccebf090e0065cb1c9bc5`;
- `reference/maf_p0/perceptual_metrics.py`, SHA-256
  `4c02f3a7d2b04f26a0c51646c567daaeae391f1b1d23ba19974cf5780663c425`;
- Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, pystoi 0.4.1.

Before Mozart, hash and re-audit the runner and at most one new phase/channel
helper. JSON forbids NaN and Infinity.

The evaluation entry path reads canonical interleaved little-endian PCM16 into
frame-major NumPy `int16`. Existing waveform and spectral formulas receive
those raw integer values and cast them directly to float64 exactly as
`_global_metrics` and `_spectral_metrics` do; there is no division by 32768 on
those paths. The transient helper retains its existing internal division by
32768. STOI/ESTOI and the new phase/channel helper explicitly divide float64
PCM by 32768 before analysis.

For non-degenerate input, retain the exact existing formulas for waveform SNR,
SI-SDR, segmental SNR, RMS, maximum error, multi-resolution spectral
convergence, log-magnitude error, log-mel RMSE, log-spectral distance,
magnitude cosine, STOI/ESTOI, and transient pre-echo. Existing transient
parameters remain: 3 ms analysis (minimum 32 samples), half-window hop
(minimum 16), 10 ms region, 20 ms separation, maximum eight events.

Reference-derived applicability is frozen before comparing codecs. A silent
reference makes SNR, SI-SDR, segmental SNR, magnitude cosine, phase, Pearson,
and STOI/ESTOI null with `silent-reference`. No active 20 ms frame makes
segmental SNR null with `no-active-frame`; no reliable phase bin, no transient
onset, zero channel variance, unsupported STOI rate, or insufficient metric
length likewise yields null plus its exact reason. RMS and maximum error remain
finite even for silence. An axis null for the same reference-derived reason is
inapplicable to both codecs and does not vote. Any asymmetric missing value,
unexpected NaN/Infinity, overflow, exception, or non-frozen reason is hard.

The optional helper is limited to:

- Hann STFT 2048 at rates at least 32 kHz, otherwise 512; quarter-window hop;
- reliable phase magnitude at least
  \(\max(10^{-3}\cdot frame\_maximum,10^{-9})\);
- wrapped difference
  \(\operatorname{atan2}(\sin\Delta,\cos\Delta)\);
- magnitude-squared-weighted phase MAE, RMSE, circular coherence, and count per
  channel;
- per-channel SNR with the existing epsilon;
- stereo \(M=(L+R)/2\), \(S=(L-R)/2\), side/mid dB and reference error;
- inter-channel Pearson correlation, null plus reason for zero variance;
- inter-channel phase with the same mask, null plus reason if no reliable bins.

STOI/ESTOI applies only to speech-category rows, after normalized float64
channel averaging, at a pystoi-supported rate. Silence, invalid length, or
library rejection yields null plus reason, never a fabricated score.

Identity, silence, polarity, pi-phase, impulse, channel swap, and shape
mismatch fixtures cover these rules.

## Comparison and one bounded refinement

The initial per-row budget \(B\) always runs and is retained. Official Opus is
strictly byte-matched to that actual S11 payload.

Quality directions are explicit:

- maximize SNR, SI-SDR, segmental SNR, magnitude cosine, STOI and ESTOI;
- minimize RMS, maximum error, spectral convergence, log-magnitude error,
  log-mel RMSE, log-spectral distance, phase MAE/RMSE, transient error,
  channel-correlation error, and mid/side-ratio error.

A point is non-dominated only if no strict-byte Opus point is no worse on
every applicable finite quality axis and better on at least one. Required
missing axes are hard failures; inapplicable null axes do not vote.

If S11 is non-dominated at \(B\), run exactly one lower-budget refinement
\(\max(1,B-8)\), then independently rebuild the strict Opus frontier at the new
actual S11 byte target. This attempts to convert a quality-only result into a
size-and-quality result. If S11 is dominated at \(B\), no refinement is run:
raising both S11 and the matched Opus target cannot establish a compression
advantage and would only lengthen the gate.

Thus each row has at most two S11 candidates. The first long result is never
deleted, and no global setting changes after Mozart. A later global change is
a new generation and new 19-row run.

Claims are per row and per axis. Means never convert mixed wins and losses into
a universal victory. Objective metrics do not prove equal perceived quality or
a 40% Opus win without blinded listening.

## Atomic resume and retained evidence

The controller derives one run identity from all manifest, source, S11,
decoder, Opus tool, runner/helper, metric, dependency, configuration, host, and
command hashes. The output root is new and immutable.

For each row on G::

1. create a unique sibling staging directory with `exist_ok=False`;
2. write files once; close, flush, and `fsync` each;
3. write and `fsync` the receipt last;
4. atomically rename staging to the final item directory;
5. atomically replace a small run index through its own staging file.

Windows lacks portable directory fsync; record that limitation. File payloads
and receipt are fsynced before same-volume rename.

Resume accepts a final item only when receipt schema, run identity, every file,
size, and hash verify. A stale/corrupt final stops without overwrite. A
leftover staging directory is atomically renamed to quarantine and the run
stops for inspection; it is never reused or automatically deleted. Mozart's
valid final receipt and index entry are required before item 2.

Opus execution is strictly streaming. All bitrate-feedback attempts are
encode-only and retain only argv, bytes, serial, raw/normalized hashes, timing,
and resources. After all actual sizes are known, strict points are re-encoded
with the same serial, raw-byte identity is required, and exactly one point at a
time is decoded and measured. Its decoded array and temporary WAV are released
before the next point. The existing in-memory `OpusMaxEffortFrontier` retention
model is forbidden for S12.

Retain every point's machine record, every final strict-Pareto Ogg, the S11
stream and decoded WAV, and only one deterministic Opus listening WAV for each
executed S11 budget. Because at most two S11 budgets run, decoded retained
evidence is bounded to two S11 WAVs plus two Opus WAVs. Non-Pareto Ogg and every
other decoded WAV are discarded only after their hashes, metrics, timings, and
resource records are fsynced. Before materializing Pareto Oggs, sum their known
complete bytes plus the bounded WAV allowance and hard-fail if the staging
ceiling would be exceeded. No loop retains reconstructed PCM for more than one
Opus point.

## Resource and stopping bounds

Require at least 10 GiB free on G:. Ceilings:

- 12 GiB peak RSS for controller or worker;
- 8 GiB Mozart staging, 2 GiB any other item;
- 12 GiB retained S12 root;
- S11 worker wall \(\max(900,30D)\) seconds;
- Opus subprocess wall \(\max(120,2D+30)\) seconds;
- Opus item wall \(\max(1800,60D)\) seconds;
- 12 hours for the complete run.

A wall/RSS/disk ceiling, insufficient space, unexpected process, or hash drift
is hard. Preserve staging for quarantine and start no later row. Temporary
files stay inside item staging. No cache cleanup, source deletion, or unrelated
workspace mutation is authorized.

## Alternatives and kill gates

1. **Do nothing.** Valid: retain S11 as synthetic research only.
2. **Compare to preceding Resonith too.** Removed by current owner direction.
3. **Use only three files.** Rejected by the registered-corpus rule.
4. **Use one Opus mode or SNR-only selection.** Rejected as an understated
   anchor.
5. **Run unbounded or non-checkpointed.** Rejected as non-resumable.
6. **One manifest controller with a bounded self-invoked worker.** Selected as
   the smallest implementation that enforces resources and atomic resume.

S12 closes when all 19 receipts and both reports verify. Preserve S11 as a
real-audio research alternative if at least one row is non-dominated against
the strict official Opus envelope. No such row means negative evidence; do not
add complexity to rescue it. No default or general superiority claim follows
without class coverage and later listening.

S13 remains blocked until an independent auditor verifies exact runner/helper
hashes, focused tests, receipts, aggregate report, human report, and claim
boundary.

## Minimal implementation and test budget

Authorized work:

- one manifest-driven controller that self-invokes one bounded worker;
- at most one phase/channel metric helper;
- immutable per-item receipts/artifacts;
- one aggregate JSON and one English report.

No codec opcode, production C/C++ change, CI/platform/player work, cloud AI, or
recursive test infrastructure is authorized.

Pre-Mozart focused tests are limited to seven claims:

1. manifest schema/hash/count/order/source rejection;
2. actual S11 byte-decode identity;
3. stale/corrupt receipt and output-drift rejection;
4. injected pre-rename failure, quarantine, and atomic resume;
5. two-stage streaming Opus matching, CTL coverage, deterministic raw Ogg,
   and one-live-decoded-point memory bound;
6. metric identity/silence/phase/polarity/channel/shape edges;
7. exact analyzer-bound fallback and resource hard stops.

Cumulative budget: at most two new Python files, 1,400 nonblank source lines,
450 nonblank focused-test lines, 26 tests, 15 minutes focused-test wall,
2 GiB peak RSS, 1 GiB temporary storage, and one remediation cycle.

## Primary-source basis

The frozen control interpretation was checked on 2026-08-02 against:

- Xiph opusenc manual:
  <https://www.opus-codec.org/docs/opus-tools/opusenc.html>;
- official libopus 1.6 `opus_defines.h` request IDs and values:
  <https://www.opus-codec.org/docs/opus_api-1.6/opus__defines_8h_source.html>;
- official libopus 1.6 API manual:
  <https://www.opus-codec.org/docs/opus_api-1.6.pdf>.

The local `opusenc --help` and binary hashes must agree with the recorded
options before any registered encode.

## Independent audit state

The first audit returned NO-GO on the broader previous-generation-plus-Opus
draft. Owner direction removed the incumbent branch. The V3 Opus-only audit
then found four blockers: stable CTL coverage, streaming retention, metric
entry semantics, and raw-Ogg serial canonicalization. V4 closes those four
contracts. No runner behavior is implemented until the same independent
auditor returns binary GO. Exact implementation hashes receive one narrow
re-audit before Mozart starts.
