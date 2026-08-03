# R-224 S13 phase-economy oracle preflight

Date: 2026-08-02

Status: **PRE-CODE; SYNTAX NO-GO; PREDECESSOR RUN CONDITIONALLY AUTHORIZED**

## Decision boundary

S13 does not begin by adding an anchor opcode. It begins by asking one bounded
question:

> With the S11 path, support, amplitude and frequency evidence frozen, can
> otherwise free objective phase evidence reduce the compressed final-Truth
> cost enough to justify any paid phase representation?

The first experiment is an encoder-side upper bound. It cannot change the
decoder, bitstream, public API, product version or release status. Failure is a
valid no-change result and advances the panel to S15.

## Frozen problem and baseline

R-221 is the current S12 evidence baseline. Its nineteen retained Resonith
streams all report `selected_kind=truth-fallback`. Consequently:

- the strong R-221 waveform, phase and transient results belong to direct
  lapped Truth;
- no real R-221 stream demonstrates an active persistent-partial lane;
- those results cannot establish phase-anchor necessity or economy;
- S13 must reduce bytes while preserving incumbent phase quality, not claim
  that incumbent phase is poor.

The exact S11 incumbent is not phase blind. It uses observed phase in the
decoder-coordinate fit and `_phase_corrected_steps`, which perturbs frequency
endpoints to close phase at retained observations. Every existing type-8
placement also carries an absolute `source_position_q16`. Any experiment that
calls this arm merely continuous or unanchored would confound the comparison.

## Sources of truth and prior art

The design is constrained by:

- McAulay and Quatieri sinusoidal analysis/synthesis, including amplitude,
  frequency and phase tracks, line birth/death and cubic phase interpolation;
- MPEG-4 HILN phase-continuous parametric lines;
- PARSHL and deterministic-plus-stochastic spectral modeling;
- the current Opus specification as negative evidence that perceptual spectral
  allocation can matter more than exact waveform phase;
- the R-193 independent prior-art audit;
- actual R-215 and R-221 code, streams, decoder output and receipts.

Phase continuity, endpoint phase interpolation, phase locking and sinusoidal
lines plus residual are prior art. The only research question here is measured
complete-description economy for a bounded anonymous field with one final
Truth.

## Alternatives and falsification

### A. No change

Retain exact S11 and proceed to source-filter S15. This is selected whenever
the free phase upper bound fails. It adds no decoder or checkpoint cost.

### B. Exact S11 incumbent

Preserve every current phase-aware fit, endpoint correction, placement and
actual complete-byte cost. This is the primary paid baseline.

### C. Pure phase-blind continuous law

Only birth phase and phase-blind frequency/gain evidence may be used. Later
observed phase is excluded from path fitting, thinning, knot placement and
selection. This isolates the value of phase evidence.

### D. Denser phase-blind frequency knots

Use additional existing type-8 frequency-law segments without later phase
observations. This tests whether frequency resolution, not phase innovation,
is the missing coordinate.

### E. Existing-syntax triangular frequency bridge

Ramp frequency deviation away from and back to the immutable base law using
two existing type-8 segments. This is the smallest coherent paid correction.

### F. Split or rebirth with deterministic crossfade

End one placement and begin another with an absolute phase. It contains errors
after the boundary but pays another placement and overlap.

### G. Sparse phase-innovation bridge

Correct only phase residual against an immutable non-phase base. This remains
experimental and does not authorize new syntax.

### H. Free exact-phase oracle

Use objective phase observations without charging their representation. Keep
all non-phase evidence frozen and report only final-Truth reduction and decoded
quality. This is an upper bound, never a codec rate point.

No candidate may be rescued by adding another opcode after it loses its frozen
gate.

## Preceding-generation actual comparison

The persistent comparison rule requires the immediately preceding Resonith
generation. R-221 intentionally omitted that column under the owner-directed
narrow comparison then in force. A proposed static derivation was independently
rejected because closing every runtime, import and alias authority would cost
more than executing the real prior producer.

The selected smallest authority is therefore an actual counterfactual
execution of the exact pre-S11 direct-Truth producer on all nineteen frozen
R-221 inputs. It does not rerun Opus and it does not claim that S11 is globally
mechanical on unregistered input.

### Historical source authority

- Resolve short commit `ca87dec` to one full commit SHA and record its tree
  SHA.
- Produce a fresh `git archive` of that exact commit in a nonexistent,
  reparse-free R-224 root. Record archive SHA-256, complete member inventory and
  every extracted-file SHA-256.
- Reject absolute member paths, `..`, NTFS alternate streams, symlinks,
  junctions, hardlinks and every reparse point at the root or below it.
- Extraction is into a new child with no adoption, retry or reuse after an
  ambiguous or partial result.
- The explicit historical producer is
  `reference.maf_p0.lapped_oracle.encode_lapped_stream`. The explicit decoder
  is `reference.maf_p0.native_core.NativeMain0Decoder.decode_lapped` from the
  same extracted tree.

### Isolated runtime authority

- Use exactly
  `G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe` and record its
  SHA-256, `sys.version`, implementation, architecture and isolated-mode flags.
- Start each item in a new isolated subprocess. The environment uses an exact
  allowlist; `PYTHONPATH`, user site, current-directory import and inherited
  project paths are excluded.
- The bootstrap inserts only the extracted commit root and its `reference`
  root. Record CWD and final `sys.path`.
- Record NumPy version and resolved origin plus every loaded module origin.
  Every loaded `reference.maf_p0.*` and `cibs0.*` module must resolve under the
  extracted `ca87dec` root. A current-worktree or shadow module is terminal
  failure.
- Record project-module hashes before and after every child. Standard-library
  behavior is a pinned CPython frozen-host assumption, not a false claim that
  the entire OS is byte locked.

### Native authority

- Use the exact R-221 DLL path and SHA-256. Record the path requested by Python
  and the resolved loaded-module path/hash observed during the child.
- Bind the unchanged native lapped source, public header and ABI identities at
  `ca87dec`, current source and the loaded DLL.
- Record the native wrapper source hash and configured workspace ceiling.
  `analyze_lapped` and `decode_lapped` allocate all call state locally; no
  cross-item decoder session is reused.
- The DLL and all frozen authorities are checked before and after the complete
  run. Any drift is terminal.

### Frozen inputs and configuration

Bind the registered-manifest SHA-256, exactly nineteen unique IDs, their frozen
order, and the exact mapping to every sealed R-221 receipt and selected stream.
For each item bind:

- canonical PCM16 payload SHA-256, file SHA-256, frame count, channel count,
  sample rate, frame-major shape, `int16` dtype and little-endian byte order;
- `coefficients_per_frame`, `half_window`, `band_count`;
- `entropy_backend="bounded"`, `transform_backend="fixed"`,
  `density_backend="adaptive"`, `selection_backend="energy"`;
- `frame_whitening=0.0` and `band_whitening=0.0`.

Before historical execution, independently validate each current receipt,
aggregate/index membership, `truth-fallback` status, stream path/hash/bytes,
current decoded-PCM hash, dimensions and sample rate. Missing, duplicate,
quarantined or unexpected rows fail.

### Execution and comparison

Each historical item runs once in an isolated bounded subprocess with atomic
temporary output, recorded argv/environment, timeout, CPU, wall, peak RSS,
disk high-water and terminal status. There is no blind retry. The worker:

1. reads and validates the frozen PCM tuple;
2. executes the exact historical `encode_lapped_stream` with the frozen full
   configuration;
3. decodes the resulting bytes with the exact historical wrapper and frozen
   R-221 DLL;
4. compares old/current payload bytes, SHA-256 and byte count;
5. compares old/current decoded PCM SHA-256, frame/channel/rate tuple and the
   actual current WAV payload;
6. commits one canonical per-item receipt only after every comparison passes.

When payload and PCM equality pass, the historical stream and WAV are omitted
as content-identical duplicates; the receipt references the existing R-221
artifact by path, bytes and hash. These are receipt references, never symlinks,
hardlinks or filesystem links. If either comparison fails, retain the actual
historical payload and decoded PCM for diagnosis and terminate the aggregate as
NO-GO.

Each row records old/current payload hashes and bytes, old/current PCM hashes
and dimensions, Boolean identities, exact provenance, and
`proof_kind="actual-ca87dec-counterfactual-execution"`. Aggregate success
requires 19/19 committed identities, zero skipped/duplicate/quarantined rows,
unchanged archive/DLL/module authorities before and after, and one reproducible
canonical aggregate hash.

The focused negative suite rejects archive/member or module-origin drift,
manifest/config drift, source-PCM drift, DLL drift, receipt/current-stream
drift, and forced payload and PCM mismatches.

## Stage-1 free-oracle experiment

Inputs execute long first and in this order:

1. full 400.773-second Mozart;
2. 319.38-second single-speaker LibriSpeech;
3. full 658.32-second *Elephants Dream* mix;
4. 600-second synthetic bounded vibrato.

No new audio is acquired for S13. Before the first result, freeze source PCM
hashes, sample rate, channel count, S11 observation/path/support identities,
Basis lengths, gain and frequency laws, lane caps, decoder, direct-Truth
configuration, entropy backend, candidate order and resource ceilings.

For each input compare:

- direct Truth;
- exact S11;
- pure phase-blind continuous prediction;
- free exact-phase prediction.

The oracle may alter only predicted phase on already frozen phase-blind support.
It cannot alter source identity, path identity, frequency support, amplitude,
gain, Basis length, birth/death, channel route, transform, coefficient budget,
Truth coder or decoder. Final Truth is encoded and decoded by the actual
incumbent path.

The oracle reports:

- compressed final-Truth bytes and delta;
- complete non-phase bytes separately, without pretending that phase costs
  zero in a real stream;
- residual SSE, clipping and waveform metrics;
- log-mel, detailed log-spectrum and multiresolution STFT metrics;
- every-channel phase metrics, mid/side error, interchannel phase,
  correlation/delay and antiphase cancellation;
- pre-echo and transient behavior;
- wall/CPU time, peak RSS, accelerator use and retained bytes;
- every fallback, ineligible lane and rejection reason.

## Label-free eligibility

Eligibility is determined before observing oracle savings. An input qualifies
only when phase-blind S11 evidence contains at least one lane that:

- spans at least one second and at least eight retained observations;
- uses only locally resolvable observations with usable phase at evaluated
  endpoints;
- remains above the frozen S11 amplitude/confidence floor outside explicitly
  marked null intervals;
- stays inside the existing Basis, step, gain, placement and work bounds; and
- contributes at least 0.1% of source energy over its support before any phase
  correction.

Input qualification, lane identities and support are frozen before phase-oracle
evaluation. Mozart or a film mix is not called coherent by semantic label.

## Phase gauge and identity rules

- The non-phase base law is immutable after phase fitting begins.
- Real negative gain is canonicalized to nonnegative gain plus a half-cycle
  phase shift before innovations are considered.
- A shortest-turn exact half-cycle tie uses the negative signed half-turn.
- Phase is undefined below the frozen amplitude/confidence floor; no anchor is
  allowed there.
- A close-tone crossing retains competing identities through final RDO. An
  identity swap cannot be repaired by a phase event.
- Gap/reappearance competes with rebirth and fallback.
- Analysis-window origin is frozen in the observation identity.
- Stochastic phase is never predicted by this mechanism.

## Smooth bridge boundary

A possible future smooth bridge is

\[
\phi(r)=\phi_{base}(r)+\Delta(3u^2-2u^3),\qquad u=r/L.
\]

This is cubic phase with quadratic instantaneous-frequency correction. It is
not exactly representable by one or two nondegenerate type-8 linear-frequency
segments. Before any new decoder law, compare:

1. absolute integer evaluation of the cubic reference;
2. the best complete-byte existing type-8 approximation;
3. the two-segment triangular frequency bridge.

No cubic implementation is authorized here. A later proposal must freeze
sample-versus-increment duration, analytic-versus-discrete endpoint conditions,
half-open lane intervals, every interior step bound, portable wide-integer
evaluation and checkpoint state. Compiler-specific `__int128` is not a portable
Windows contract.

## Channel and transport boundary

S13 cannot import S35 shared routes. Each channel pays independently. Encoder-
side selection may be joint only to prevent two local corrections from
destroying delay, polarity, mid/side energy or cancellation.

Existing type-8 placements are absolute records. S13 therefore makes no claim
that losing an event poisons all future phase. New stateful anchor/checkpoint or
packet-loss behavior belongs to S51. Current CBF1/MFT1 parse, complete decode,
callback partition and random-slice identities remain mandatory for any paid
existing-syntax candidate.

## Admission and kill gates

Stage 1 is killed unless the free exact-phase oracle:

- reduces compressed final-Truth bytes by at least 10% on at least three
  qualifying complete inputs;
- produces a decoder-domain quality Pareto point on those inputs;
- preserves all-channel and interchannel metrics within frozen tolerances; and
- produces no increase in residual clipping without a complete decoded Pareto
  win.

Only after Stage 1 passes may one focused existing-syntax experiment compare all
eight arms on stationary tone, linear chirp, one known smooth phase innovation,
close-tone crossing with a null, gap/reappearance, delayed/antiphase stereo and
the strongest qualifying real long input.

The paid generation is killed unless:

- stationary tone and exactly representable linear chirp select zero anchors;
- bounded vibrato uses at most one anchor per second;
- sparse correction beats exact S11, pure continuous, dense-frequency and
  rebirth/crossfade by at least 3% complete bytes at the frozen quality floor on
  at least two long real inputs;
- no correction occurs in a phase-unidentifiable interval;
- every complete decoder and bounded-resource identity passes; and
- no syntax, checkpoint, corruption or portability claim exceeds the actually
  executed existing language.

Failure completes S13 as rejected/no-change. It does not trigger another phase
mechanism or a relaxed threshold.

## Minimal-sufficient evidence budget

Baseline closure is limited to one actual-run controller/worker, one focused
test module, this preflight, one machine aggregate, one result report and one
audit amendment. It should finish within 30 minutes, use less than 4 GiB peak
RSS per child and retain less than 256 MiB when all outputs are identical.
Per-item wall time is `max(300, 3 * duration_seconds)` with a 900-second hard
ceiling; the first timeout, identity ambiguity or authority drift stops the
run. It adds no codec or product code.

If independently authorized, Stage 1 is limited to the four declared inputs,
one runner, one focused contract test, one machine result and one result report.
Per-worker ceilings are `max(900, 15 * duration_seconds)` wall seconds, 4 GiB
peak RSS and 8 GiB retained working storage; the aggregate retained package is
limited to 12 GiB. No Opus search or full registered corpus runs before an
actual S13 algorithm candidate exists. One bounded redesign is permitted after
the first failed execution; a second budget or design failure kills S13.

## Independent red-team verdict

The independent auditor returned **NO-GO for S13 implementation as initially
defined** and **GO only for a frozen free-oracle experiment after baseline and
semantic blockers close**. It then rejected the derived static baseline proof
as under-bound. The revised actual nineteen-item historical execution received
**GO**, conditional on every archive, extraction, runtime, module, DLL,
source/ABI, input/configuration, receipt, process, mismatch-retention and
aggregate field above being frozen before code.

The exact amended preflight hash requires final auditor confirmation before the
actual comparison controller is implemented. Stage-1 oracle code requires a
separate binary GO after the preceding-generation aggregate passes.
