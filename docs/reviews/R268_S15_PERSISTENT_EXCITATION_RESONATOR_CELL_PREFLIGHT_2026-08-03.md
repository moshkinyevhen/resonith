# R-268 S15 persistent excitation and immutable-resonator Cell preflight

Date: 2026-08-03

Status: **REMEDIATED AND FROZEN FOR FINAL PRE-CODE RE-AUDIT; IMPLEMENTATION NO-GO**

## Audit history and problem

The first exact preflight, SHA-256
`1040fb8133651d68ccb228448804829dc06f660a95d640af6e4d3cb15767a665`,
received two independent NO-GO verdicts. The blockers were:

1. its reflection domain exceeded the frozen Core limit;
2. fixed-knot stability did not prove arbitrary time-varying direct-form
   stability;
3. independently persistent laws could not share one checkpoint cursor;
4. DP, event, parser and cumulative execution bounds were incomplete;
5. signed-PCM16 Truth input was not closed;
6. controls, tolerances and S16 admission were not frozen tightly enough.

This remediation removes the entire checkpoint/seek/reset subsystem from S15,
uses immutable resonators inside bounded overlapping Cells, closes every input
and resource domain, and narrows any possible admission claim to a mono-16-kHz
experimental mode. It does not add a test framework.

## Measurable hypothesis

> A small set of anonymous, phase-continuous excitation Cells with immutable
> stable resonators and persistent event laws can reduce complete bytes or
> improve actual-decoder speech quality against accepted S12. Accepted S12 is
> always a byte-identical whole-file fallback.

The hypothesis is falsified if the selected combined arm fails the frozen
synthetic interaction, long speech, short speech or S16 gates. One mechanical
defect may be corrected without changing the model, controls or thresholds;
one semantic failure closes S15 without rescue complexity.

## Prior art and novelty boundary

Source-filter coding, LPC/LSF interpolation, LTP, pulse/noise excitation and
persistent sinusoidal parameters are established prior art:

- [Schroeder and Atal CELP](https://doi.org/10.1109/ICASSP.1985.1168147);
- [Opus/SILK, RFC 6716](https://www.rfc-editor.org/rfc/rfc6716.html);
- [3GPP EVS TS 26.445](https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1467);
- [MPEG-4 Audio](https://mpeg.chiariglione.org/standards/mpeg-4/audio.html);
- [McAulay-Quatieri sinusoidal coding](https://doi.org/10.1109/TASSP.1986.1164910);
- [HILN](https://heikopurnhagen.net/sigproc/diss-hp.pdf);
- [WORLD](https://www.isc.meiji.ac.jp/~mmorise/world/english/publications.html);
- [DDSP](https://openreview.net/forum?id=B1x1ma4tDr).

R-268 makes no mechanism-novelty or superiority claim. The only testable
engineering contribution is the combined bounded Cell, complete ledger,
actual-decoder Truth RDO and unrestricted fallback contract.

## Frozen authorities and exclusions

- planning head: `8ae7224e5ffaaa371af4e3cf3dfb3d0bce1d8954`;
- accepted S12 result: `docs/results/R221_S12_FIXED_OPUS_DIRECT_2026-08-02.md`;
- accepted S12 aggregate SHA-256:
  `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`;
- registered manifest SHA-256:
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`;
- frozen control manifest:
  `experiments/fixtures/r268_s15_persistent_cell_controls_v1.json`;
- control-manifest SHA-256:
  `9dc52479e60e328789f3015daac05ee2d6c1aeb5bcad0b3051b735506e4b3ddc`;
- accepted active S15 identities are those restored by R-267;
- every R-253 through R-266 executable, fixture, runner, authority and result
  remains quarantined and is a forbidden import or evidence dependency.

The frozen native MAF, trajectory and composition source pairs are:

```text
436e9bf136a782e8d42b2dc0f17aa966c76846726d06e38d24079d09cdeee9a3
c3df8c2248b0be2f6e058dc99195240fd35030c78df521edd66309b57a6f4ee4
d64b1e41d4c2d56968910041fa7b1479c5e71e2e08e771bfdca635b5318e9769
a1a68d4a59b1e0fb77c8d7afd1d043f21db45a541abd53726eed96190b483480
fd4c162514b3b4865dc424d0860d3bf3398f7f7e356134eed9f7ccef87b28ebf
ea874a6f2cc998e2c99b0471a26ec1f53a1b9ec89022c5e46ab62abf78c97374
```

No neural decoder, semantic class, source separator, learned Basis, motif
dictionary, transient lane, stochastic field, cross-channel law, random
access, checkpoint, packet recovery or product syntax is authorized here.

## Selected model and rejected alternatives

Rejected alternatives are no change beyond the fallback, a frame-local CELP
clone, an unproved time-varying direct-form resonator, a second sample-DSP
implementation, a neural decoder and adding later MAF families to rescue S15.

The selected model permits at most two simultaneously active anonymous Cells.
Each Cell has:

- one 64-sample impulse Basis: sample zero is 32767 and the rest are zero;
- explicit Q32 phase and constant or linear phase-step law;
- constant or linear Q15 pulse/noise gain laws;
- one immutable order-10 reflection vector for its complete lifetime;
- private ten-sample filter history initialized to zero;
- one bounded linear fade at birth and death.

Changing a resonator always starts a new Cell. The old and new stable Cells may
overlap for 80 through 1600 samples; their nonnegative Q15 weights sum exactly
to 32767 at every overlap sample. Coefficients never switch inside recursive
state. This replaces the rejected arbitrary time-varying filter with a bounded
crossfade of independently stable filters.

Reflection coefficients satisfy `abs(k_q15) <= 29491`, exactly matching the
frozen Core. Every fixed Cell is Schur-stable in real arithmetic; fixed-point
render remains deterministically bounded by the existing saturating Core. No
claim is made that the latent Cell is a unique physical source.

## Canonical decoder data flow

For every active Cell, the adapter calls only frozen Core arithmetic:

```text
phase       = resonith_phase_prepare(cell_phase_law)
pulse_unity = resonith_maf_periodic_render(fixed_impulse_basis, phase)
pulse       = resonith_maf_compose_truth(pulse_unity, null, pulse_gain)
noise       = resonith_maf_noise_render(seed xor CellSeed(cell_id), 0, 0, noise_gain)
excitation  = resonith_maf_mix_q15([pulse, noise], [32767, 32767])
filter      = resonith_maf_filter_prepare(cell_immutable_reflection_q15)
cell_pcm    = resonith_maf_filter_render(filter, excitation, cell_history)
model       = resonith_maf_mix_q15(active_cell_pcm, crossfade_weights)
truth_i32   = checked_i32(source_pcm16) - checked_i32(model)
truth_pcm16 = checked_exact_narrow_i16(truth_i32)
truth_hat   = DecodeAcceptedS12(EncodeAcceptedS12(truth_pcm16))
output      = resonith_maf_innovation_add(model, widen_i16(truth_hat), 1)
```

If any Truth sample is outside `[-32768,32767]`, that complete Cell candidate
is rejected before S12. Wrapping and clamping are forbidden. Lossy Truth never
feeds Cell history; corruption cannot recursively poison model state. The
decoder performs no search, FFT, floating point, allocation in the sample loop
or neural inference. A second implementation of periodic, noise, gain, filter,
mix or innovation DSP is forbidden.

## Research stream syntax

`SFC2` is a whole-file research stream, not proposed product syntax. It is
little-endian and has no seek, reset or checkpoint. A fallback winner emits the
accepted S12 stream byte-for-byte with no selector wrapper.

The 48-byte `SFC2` header is:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | ASCII `SFC2` |
| 4 | 1 | major `2` |
| 5 | 1 | minor `0` |
| 6 | 2 | flags, zero |
| 8 | 4 | sample rate, exactly 16000 |
| 12 | 4 | sample count |
| 16 | 8 | stream seed |
| 24 | 4 | Cell-record count |
| 28 | 4 | excitation-event count |
| 32 | 4 | resonator-refresh count |
| 36 | 4 | accepted-S12 Truth bytes |
| 40 | 4 | header bytes, exactly 48 |
| 44 | 4 | reserved, zero |

Each 48-byte Cell record is `u16 cell_id`, `u16 reserved=0`, `u32 start`,
`u32 duration`, `u16 fade_in_samples`, `u16 fade_out_samples`, `u32
initial_phase_q32`, `u32 initial_phase_step_q32`, `i16 initial_pulse_gain_q15`,
`i16 initial_noise_gain_q15`, then ten `i16 reflection_q15` values.

Phase step is zero only when pulse gain is zero; otherwise it represents 60
through 400 Hz. Pulse/noise gains are in `[0,32767]` and their sum is at most
32767. `CellSeed(id)` is `id * 0x9e3779b97f4a7c15` modulo 2^64. These domains
are checked before rendering.

Each 24-byte excitation event is `u16 cell_id`, `u16 flags`, `u32 offset_from_
cell_start`, `u32 duration`, `u32 ending_phase_step_q32`, `i16 ending_pulse_
gain_q15`, `i16 ending_noise_gain_q15`, `u32 reserved=0`. Flag bits 0 through 2
select linear phase-step, pulse-gain and noise-gain interpolation; all other
bits are zero. Starting values are the preceding endpoint or the Cell record.
Events are contiguous, ordered and cover the Cell lifetime exactly.

Each 32-byte resonator-refresh record is `u16 cell_id`, `u16 reserved=0`, `u32
offset_from_cell_start`, `u32 duration`, then ten immutable `i16 reflection_
q15` values. It never resets or changes the filter; the decoder rejects a
value differing from the Cell record. It exists only in expanded factorial
arms and is charged as transmitted state.

For every consecutive old/new Cell pair with overlap length `d`, the parser
requires `old.end-new.start == old.fade_out == new.fade_in == d` and
`80 <= d <= 1600`. At overlap sample `p=n-new.start`, where `0 <= p < d`:

```text
new_weight = floor((32767*p + floor((d-1)/2)) / (d-1))
old_weight = 32767 - new_weight
```

Thus both endpoints are exact. The first Cell starts at sample zero with
`fade_in=0`; the last ends at `sample_count` with `fade_out=0`; a single Cell
has both zero. Cells cover the complete signal without gaps and the active
count may never exceed two. Any mismatched window or third overlap is invalid.

Sections are header, Cell records sorted by `(start,cell_id)`, excitation events
sorted by `(absolute_start,cell_id,offset_from_cell_start)`, refresh records
with the same total key, then exactly one complete accepted-S12 Truth stream.
Every Cell's events have exact no-gap/no-overlap coverage. Ties or a record out
of canonical order are invalid. Trailing bytes are forbidden.

For `N=ceil(sample_count/80)`, the profile requires:

- mono 16 kHz and `sample_count <= 9,600,000`;
- at most two active Cells at any sample;
- `cell_count <= min(N+1,65535)` and the exact sum of
  `ceil(cell_duration/80)` over all Cells is at most `2*(N+1)`;
- `excitation_event_count <= 2*(N+1)` and
  `refresh_count <= 2*(N+1)`;
- Cell IDs strictly increase and are never reused;
- every length/offset/count product uses checked unsigned 64-bit arithmetic;
- total `SFC2` bytes, including Truth, do not exceed 268,435,456;
- sequential parsing with storage for two Cells and one record only; event
  arrays may not be allocated from file-declared counts.

Malformed ordering, overlap, fade, reserved bits, count, length, domain or
Truth identity fails before PCM commit.

## Encoder search and exact bounds

Local anonymous proposals occur every 80 samples from one causal 320-sample
window. The encoder estimates periodicity over integer lags 40 through 267,
pulse/noise gains and order-10 reflections. Names such as speech, voice or
instrument never enter the candidate or stream.

The only predecessor durations, lambda values, proxy weights and tie order are
frozen in the control manifest. At endpoint `j`, the segmented DP examines at
most twelve predecessors `i=j-duration`. Its recurrence is:

```text
cost[j] = min_i(cost[i] + serialized_law_bytes(i,j)
                         + lambda_q8 * proxy_error(i,j) / 256)
```

`proxy_error` is the sum over covered controls of squared integer deviations
from the candidate constant/linear phase-step and gain laws and immutable
reflection Cell, after applying the manifest shifts and weights. All sums use
checked unsigned 64-bit saturation-to-invalid, never wrap. The DP stores one
64-bit cost and one 32-bit predecessor per control: at most 1,440,000 edge
evaluations, 11.6 MiB proposal/DP state and four frozen lambda paths at the
profile maximum. No interval outside the twelve durations is searched.

Each of the four paths is synthesized once by native C++23 batched Core calls.
Its checked PCM16 Truth is encoded once by unchanged S12. Final selection uses
actual decoded metrics and complete serialized bytes, never the proxy. Python
may orchestrate reports and run an independent scalar decoder but may not run
per-candidate sample DSP.

## Four-arm persistence attribution

For each selected model path all arms decode to exactly the same model and
Truth; only paid state serialization differs:

| Arm | Excitation state | Resonator state |
|---|---|---|
| A | one event every 5 ms | one refresh every 5 ms |
| B | persistent DP events | one refresh every 5 ms |
| C | one event every 5 ms | immutable Cell record only |
| D | persistent DP events | immutable Cell record only |

D must beat B and C in complete bytes on the interaction control and on both
speech durations at identical decoded PCM. D itself, not B or C, must also
pass every real-speech gate against S12.

## Frozen controls and objective tolerances

The control manifest binds every source, PCM hash, generator parameter, S12
configuration, Opus configuration, DP choice and metric tolerance. The
two-Cell interaction source is generated exactly as follows:

```text
excitation[n] = 4000 when (n-cell_start) mod 64 == 0, otherwise 0
y[n] = sat_i16(excitation[n] - maf_round_shift_q15(k_q15*y[n-1]))
Cell 1: [0,80000), k=-8192
Cell 2: [78400,160000), k=-16384
overlap: the exact 1600-sample endpoint formula defined above
```

The PCM16 payload must hash to the manifest identity before analysis. Impulse,
xorshift32 white and zero negatives are likewise hash-bound. No synthetic
parameter may change after the first result.

Metric comparison uses the manifest tolerance `t`: higher-is-better is
non-regressive when `candidate >= baseline-t`; lower-is-better is
non-regressive when `candidate <= baseline+t`. Improvement requires crossing
the same tolerance in the favorable direction. Gap closure is:

```text
higher better: (candidate-S12)/(Opus-S12)
lower better:  (S12-candidate)/(S12-Opus)
```

and is evaluated only where Opus is better than S12 and the denominator is
positive.

## Focused kill and real-speech gates

Kill before real speech if:

- generated control hashes differ;
- D does not reconstruct the interaction source sample-for-sample with zero
  Truth, beat B and C, and save at least 20% complete bytes versus S12;
- impulse, white or zero selects a Cell candidate that is larger or worse than
  byte-identical S12;
- native/scalar decode, callback partition or C++23 toolchain parity differs;
- any parser ambiguity, unchecked arithmetic, out-of-domain Truth, overlap
  violation, nondeterminism or forbidden dependency appears;
- all focused controls exceed 300 seconds wall, 900 seconds CPU, 1 GiB peak
  RSS or 256 MiB retained storage cumulatively.

If controls pass, run the frozen 319.38-second diagnostic first, then the
registered 5.855-second item. D must beat B and C at identical decoded PCM and,
on each duration, satisfy either:

1. at least 3% fewer complete bytes than S12 with SNR, STOI, ESTOI, log-mel and
   magnitude cosine non-regressive; or
2. bytes within 0.5% of S12, STOI/ESTOI/log-mel all improved, SNR no worse than
   0.5 dB and magnitude cosine non-regressive.

D must also close at least 10% of the S12-to-Opus gap on two axes where Opus is
better. Long plus short execution is capped at 2,400 seconds wall, 7,200
seconds CPU, 2 GiB peak RSS and 4 GiB retained storage. Decoder wall must be no
more than 1.25 times S12. A failure produces an S15 no-change result and no
registered-corpus rerun.

## Complete ledger and minimum implementation

Every candidate charges header, every Cell/event/refresh record, all section
bytes, complete accepted-S12 Truth, parser termination and dual-encode
CPU/wall/memory. The fixed decoder executable is not a per-file byte cost.

New executable/fixture scope is limited to:

1. `native/include/resonith/persistent_cell.h`;
2. `native/src/persistent_cell.cpp`;
3. `native/tests/persistent_cell_test.cpp`;
4. `reference/maf_p0/persistent_cell_oracle.py`;
5. `experiments/r268_s15_persistent_cell_gate.py`;
6. `experiments/fixtures/r268_s15_persistent_cell_controls_v1.json`.

Only `native/CMakeLists.txt`, the decision/checkpoint/index/changelog documents
and those six paths may change. The cumulative executable budget, including
CMake, is 1,500 nonblank lines. Existing R-267 oracle/gate files remain
unchanged. No worker authority, process monitor, test-of-test or private ABI is
authorized.

| Phase | Wall | CPU | Peak RSS | Retained bytes |
|---|---:|---:|---:|---:|
| focused controls | 300 s | 900 s | 1 GiB | 256 MiB total root |
| long then short speech | 2,400 s | 7,200 s | 2 GiB | 4 GiB total root |
| one S16 corpus comparison | 14,400 s | 57,600 s | 3 GiB | 12 GiB total root |
| cumulative through S16 | 17,100 s | 65,700 s | 3 GiB | 12 GiB |

Retained-byte rows are inclusive ceilings for the one cumulative evidence root,
not additive allowances. Later phases reference earlier immutable artifacts in
place and must leave enough headroom under their inclusive ceiling.

## Claim-to-evidence ledger

| Claim or risk | Evidence | Expected | Failure |
|---|---|---|---|
| identical arm synthesis | interaction plus speech hashes | A/B/C/D PCM equal | kill S15 |
| immutable-filter safety | Core domain and two-Cell overlap tests | no illegal state | kill S15 |
| additive Truth isolation | scalar/native corruption probe | model state unchanged | kill S15 |
| persistence economy | complete A/B/C/D ledger | D beats B and C | kill S15 |
| actual speech value | long then short actual decode | frozen dual gate | no change |
| bounded implementation | path/LOC/time/RSS/storage receipt | all caps pass | no change |
| general regression | one S16 registered run | predicate below | narrow/no change |

## S16 admission predicate

A focused pass creates one coherent S15 candidate but no claim. S16 then runs
the existing complete 19-item registered manifest once, long-first, against
accepted S12 and maximum-effort official Opus through actual decoders. It
publishes all required per-file and aggregate bytes, bitrate, quality,
spectral/phase/transient/channel metrics, CPU/wall, GPU, memory, hashes,
fallbacks, wins and regressions.

S16 passes only if:

- D is selected on the registered 16-kHz speech item and passes its focused
  byte/quality/gap gate;
- at least one registered item selects D; all unsupported items are
  byte-identical S12 fallback;
- aggregate complete Resonith bytes do not exceed accepted S12;
- no selected item regresses any axis returned by the hash-bound
  `experiments/r216_s12_metrics.py:quality_axes` policy beyond its manifest
  tolerance; this includes waveform, log-spectrum, multiresolution spectral,
  phase, pre-echo, speech and applicable stereo/channel axes;
- all implementation and cumulative resource caps pass.

Even a pass admits only a **mono-16-kHz S15 experimental mode**. It cannot be
called a general generation, generally better than Opus, product syntax or
standard candidate. A failure preserves useful diagnostic artifacts, records
S15 as no change and advances to S17 without threshold tuning.

## Final audit request

The independent auditors must return binary GO/NO-GO on this exact file and
challenge the Core domains, immutable-Cell stability argument, schema
decodability, PCM16 Truth closure, DP bounds, frozen control identities,
factorial attribution, complete budget and narrow S16 predicate. Every blocker
requires an exact counterexample and the smallest remediation. Implementation
remains forbidden until all blocking findings are resolved in writing.
