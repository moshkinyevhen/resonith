# Continuous Evidence and Release Protocol

Status: **ACCEPTED**

This protocol turns every material Resonith milestone into a reproducible
compression, quality, portability, and playback experiment. It applies before
an improvement claim, version, tag, or public release.

## 0. Material-step review and acceptance timing

R-196 governs when implementation and full evidence occur.

Before admitted implementation, every independently falsifiable material step
freezes its incumbent, compares materially different alternatives, attempts
falsification, reviews current primary sources and project measurements,
declares byte/quality/resource/compatibility budgets and stopping rules, and
receives a written binary GO from an independent auditor subagent.

Focused tests guide tightly coupled implementation edits inside that one
reviewed experimental generation. The change becomes an accepted improvement
only after the full comparative gate in this document passes and its report is
published. Thus "full test after every improvement" is literal: before that
gate the candidate remains an experiment, not an improvement.

Audit control activity is not recursively audited. Mechanical identical-output
refactors, formatting, typo corrections, invariant tests, and non-normative
documentation receive focused validation only. A normative documentation or
acceptance-semantics change is a material step.

## 1. Mandatory 19-item gate

The long-form portion uses:

| Role | Source | Canonical PCM input |
|---|---|---|
| Speech | LibriSpeech `1272-128104-0000`, CC BY 4.0 | mono PCM16, 16 kHz, 5.855 s |
| Fast music | Emotional piano, CC0 | stereo PCM16, 44.1 kHz, 8 s |
| Long music | Mozart, *Die Zauberflöte*, K. 620 — Overture, Musopen Symphony, public domain | stereo PCM16, 48 kHz, 400.773 s |

Source downloads, deterministic PCM conversion, licenses, URLs, sample counts,
and SHA-256 hashes belong in the benchmark manifest. A milestone MAY add
material but MUST NOT silently replace these references after observing a
result.

The breadth portion is every one of the 16 pinned R-111 heterogeneous classes:
deterministic sustain, stochastic noise, vibrato/resonance, electronic
material, solo tonal instruments, sparse attacks, drums, stochastic
transients, polyphonic piano, solo voice, female speech, male speech, dense
orchestra, dense popular music, and two dialogue/music/effects/ambience film
mixes. Their exact inputs and preparation are fixed by the R-111 manifest.

Fast inner-loop experiments MAY run a subset, but they MUST be labelled
`FAST GATE` or `DIAGNOSTIC`. A material architecture conclusion, default,
version, compression/quality claim, or release MUST encode and decode the
union of all three complete references and all 16 R-111 classes. It must
preserve all three adjacent original/Resonith/Opus listening triplets.

The 19 items are a minimum. Affected changes also run their applicable
packet-loss, seek/reset, transient/pre-echo, stereo/spatial, latency,
corruption, determinism, memory, throughput, mobile, and listening gates.

## 2. Compared streams

Each reference produces:

1. the exact canonical input WAV;
2. the previous released Resonith stream and decoded PCM;
3. the candidate Resonith stream and decoded PCM;
4. a current official Opus stream and decoded PCM.

All codecs receive identical PCM. Size means the complete playable file,
including headers, dictionaries, checkpoints, padding, comments, and container
overhead. Opus is searched to match the candidate by complete Ogg bytes rather
than nominal bitrate. Encoder settings, library versions, source hashes,
executable hashes, and commands are recorded.

## 3. Machine analysis

Reports MUST include:

- duration, channels, sample rate, complete bytes, effective bitrate, encode
  and decode wall time, peak memory where available, and realtime factor;
- sample alignment and decoded duration;
- SNR, SI-SDR, segmental SNR, peak and RMS error;
- multi-resolution STFT error, log-spectral distance, log-mel error, and
  magnitude-spectrum similarity;
- harmonic-peak preservation plus frequency and amplitude error;
- STOI and ESTOI for speech when the reference conditions are valid;
- input, stream, decoded PCM, executable, and report SHA-256 hashes.

Metrics diagnose different failure modes and MUST NOT be collapsed into one
unqualified quality score. Machine analysis does not replace controlled
blinded listening.

## 4. Decision rule

The report compares the candidate against both the previous Resonith version
and Opus. It states wins and losses for every one of the 19 items. A fallback
is labelled as a fallback and is not counted as a candidate improvement.

- A mechanism that loses its declared gate is removed.
- A mechanism with a narrow or ambiguous result remains explicitly
  experimental and disabled by default.
- Corpus, anchor, alignment, or metrics MUST NOT be changed post hoc to hide a
  loss.
- Perceptual, transparent, or broadly superior claims require controlled
  blinded listening with hidden reference and anchors.

## 5. Published artifacts

Every release publishes:

- the three canonical input WAV files;
- candidate `.resonith` and rate-matched `.opus` listening files;
- decoded-PCM hashes and optionally decoded WAV files;
- a human-readable report and machine-readable JSON;
- the source commit, semantic version, bitstream version, tools, commands,
  licenses, and reproduction instructions.

The same versioned artifact set is retained locally and on GitHub. Filenames,
versions, source commit, byte counts, and SHA-256 hashes MUST agree.

## 6. Changelog and versioning

Every released improvement updates `VERSION` and `CHANGELOG.md`. A changelog
entry separates:

- measured improvements;
- regressions and rejected experiments;
- fixes and implementation-only changes;
- normative syntax or decoder behavior;
- open perceptual questions and unmeasured targets.

Normative syntax or decoder behavior changes require an explicit compatibility
statement and appropriate bitstream or ABI version increment. A change without
versioned before/after evidence is research, not a released improvement.

## 7. Orkela playback coupling

The exact Orkela build used for listening is recorded. A player release that
changes decode, playback, or UI behavior must verify:

- short speech and full-length Mozart `.resonith` inputs;
- responsive background validation and decode;
- real play, pause, stop, seek, skip, volume, timeline, and spectrum behavior;
- malformed and truncated input rejection before playback;
- `.resonith`, `.scenelith`, and `.orka` associations;
- high-DPI and constrained-work-area rendering.

Orkela has its own version and changelog. Player regressions cannot be hidden
by a codec release and codec regressions cannot be attributed to the player
without decoder-output evidence.

## 8. Immediate improvement capture

A concrete improvement discovered during implementation or measurement MUST
be written to the decision log immediately with its expected benefit,
invariants, regression risk, and acceptance gate. It is implemented at the
nearest safe boundary of the active reproducible experiment.

Small isolated improvements with existing coverage are tested immediately.
Architectural or bitstream changes first freeze the current baseline and
decision so that mixed changes cannot destroy causal evidence. An active
reproducible run is never discarded merely to apply an unrelated optimization.

Unchanged-algorithm performance work MUST prove exact stream or decoded-PCM
identity as applicable, record complete wall time and realtime factor, and
identify the source revision, compiler, host, and executable hash. A possible
improvement may not remain only in chat or an unmeasured backlog.

## 9. Algorithm-change music gate

Every codec algorithm change is one evidence generation and SHALL complete the
entire versioned registered-music manifest before the next algorithm change
begins. The gate SHALL:

- encode identical source PCM with the challenger, the immediately preceding
  Resonith generation, and the current maximum-effort official Opus anchor;
- decode the codec outputs through their actual decoders;
- publish per-file and aggregate complete bytes/bitrate, objective quality,
  log-spectral, phase, transient and stereo/channel metrics, encode/decode wall
  time, CPU/GPU use, peak memory, hashes, fallbacks, losses and regressions;
- retain the original, encoded files, decoded evaluation signals, commands,
  manifests, versions and machine-readable results;
- identify every win, tie, loss and missing-axis refinement without averaging
  away a failed music class.

The registered-music manifest means every project-pinned music asset available
to the generation across short and long duration, solo, ensemble, dense
orchestra, transient-rich, tonal, stochastic, stereo and multichannel
material. A three-reference subset is never sufficient for this gate.

Only a mechanical refactor with proven identical bitstream and decoded PCM may
use the focused identical-output exception.

## 10. R-204 continuous execution and resumable panel

The accepted derived execution view is panel `R204-63-V1` in
[`23_CONTINUOUS_63_STEP_EXECUTION_PANEL.md`](23_CONTINUOUS_63_STEP_EXECUTION_PANEL.md),
SHA-256
`6b2d1e21436e22231538d1b362657375c3699892b5290d17843ae025f510684e`.
Its mutable state is
[`execution/R204_CURRENT_CHECKPOINT.md`](execution/R204_CURRENT_CHECKPOINT.md).

The panel's 63 stable IDs must not be silently shortened, regrouped,
renumbered, reordered, or reconstructed from memory. The versioned master plan,
accepted decisions, dependencies, quarantines, audits, kill gates, safety, and
authority remain canonical.

While the continuous plan remains owner-authorized, passing an intermediate
item advances execution to the earliest dependency-ready, safe, in-scope item.
Continuation does not imply authority for external publication, release, push,
paid service, credential use, destructive action, production or user-data
mutation, or unrelated work.

Focused risk-based tests follow every implementation edit. Tightly coupled
edits within one frozen material hypothesis remain one evidence generation.
The complete Section 9 comparison runs before that generation is accepted or a
later codec-algorithm generation begins.

Every pause, blocker, or platform-imposed execution boundary updates the
durable checkpoint with all 63 states, repository and worktree identity,
incumbent and Opus identities, completed evidence, hashes, commands, tools,
blocker, clearance authority, invalidation conditions, and next safe action.
Any clear owner stop, pause, wait, reprioritization, supersession, or scope
reduction controls. Missing authority, safety or integrity risk, drift,
irreproducibility, mandatory audit NO-GO, dependency failure, and unavailable
required resources fail closed; they are never bypassed in the name of
continuity.
