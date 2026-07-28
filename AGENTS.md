# Instructions for Resonith agents

## Canonical scope

**Resonith** is the final accepted name of the standalone audio codec. It is
not a SceneLith profile and never requires a video stream for decoding. Its
internal architecture is **MAF — Memory-oriented Acoustic Field**.

Joint optimization of Resonith and SceneLith is defined only by the separate
SceneLith AV Bridge specification.

## Statement statuses

- **ACCEPTED** — adopted by the project owner.
- **NORMATIVE-DRAFT** — proposed normative requirement that is not frozen.
- **HYPOTHESIS** — falsifiable technical hypothesis.
- **TARGET** — desired but unmeasured result.
- **RESEARCH** — investigation outside the mandatory Main profile.
- **SUPERSEDED** — historical decision replaced by a newer one.

Never present a **TARGET** or **HYPOTHESIS** as a measured result.

## Immutable invariants

1. The Truth Core is deterministic, resource-bounded, and suitable for
   integer DSP, GPU, embedded, and ASIC implementation.
2. Optional Perceptual Detail is never a reference.
3. The encoder may use semantic and musical understanding, but semantic labels
   are not normative Truth.
4. The normative bitstream carries physically verifiable acoustic fields,
   trajectories, and Innovation rather than mandatory note or instrument
   names.
5. The Lossless profile reconstructs exact PCM.
6. One decoder and bitstream support Live, Studio, and Foundry encoders.
7. Standalone decoding never depends on video.
8. Record every new decision in `docs/06_DECISION_LOG.md` before modifying the
   thematic documents or specification.
9. Main-0 includes CIBS: fixed integer synthesis runs only at `BASIS_SET`, and
   the resulting Basis is immutable.
10. CIBS forbids arbitrary graphs, floating-point normative behavior, and
    per-sample neural inference.
11. Python is a thin research control plane and independent oracle only.
    Scaling DSP/search kernels execute natively, and shipped codec, SDK,
    embedded, command-line, and playback artifacts have no Python runtime
    dependency.
12. Preserve the causal-simplicity invariant: model sound as a small set of
    persistent excitation, resonator/state, transient, stochastic, and
    phase/room/channel-route causes. Keep harmonic, bounded-inharmonic,
    transient, stochastic, and route lanes separately owned, sum them before
    one final Truth, independently index their timing, pitch, phase, gain,
    envelope, resonator, and route laws before bounded composition, and never
    add a mechanism or opcode without a measured complete-description benefit.
13. Apply the R-181 theory-before-syntax protocol to every new material
    mechanism: formal model and limits, current online primary-source review,
    prior art and alternatives, decoder/resource consequences, falsifiable
    byte/quality budget, kill gate, and evidence plan come before code. A
    per-file manual or AI oracle is discovery evidence only until a
    deterministic label-free encoder reproduces it on held-out material.
14. Apply the R-184 causal-analysis order: observe and globally track anonymous
    complex partials before proposing fundamentals or source groupings; keep
    independent partial paths as fallback; admit harmonic, inharmonic,
    resonator, motif, or route grouping only by complete decoder-domain MDL.
15. Apply R-185 before every material change: brainstorm genuinely different
    alternatives, try to falsify each against theory, counterexamples,
    implementations, standards, negative evidence, complete bytes, and
    resource limits; assign an independent red-team subagent; resolve its
    blocking findings in writing; record the decision and kill gates; only
    then implement. Pre-audit exploratory code is non-admitted scratch.

## Repository language

- English is the sole language for all public specifications,
  documentation, code comments, commit messages, issue and pull-request
  templates, and GitHub metadata.
- Historical source material in another language must remain outside the
  public repository or be accompanied by a complete English record.

## Source-comment contract

- Comment intent, invariants, fixed-point and phase rules, ownership, state
  transitions, real-time constraints, security boundaries, and non-obvious
  tradeoffs.
- Divide complex functions into a few named logical phases when this materially
  improves navigation and debugging.
- Do not narrate obvious syntax, comment every line, add decorative banners,
  or leave dead code commented out.
- Public APIs and normative DSP kernels require concise contract comments and
  a link to the relevant specification clause.
- `TODO` and `FIXME` comments require a tracked issue or decision identifier
  and a removal gate.
- Comment drift is a defect: behavior and comments change in the same commit.
- Structured debug traces must be deterministic, optional, and absent from the
  audio callback by default.

## Validation

After a change, verify:

1. relative links and Markdown structure;
2. the status of every numerical statement;
3. separation of standalone Resonith from the SceneLith AV Bridge;
4. primary-source support for external claims;
5. absence of secrets, unnecessary personal data, and undocumented
   dependencies;
6. zero Cyrillic text in tracked public files;
7. relevant tests, conformance hashes, and cross-platform build checks;
8. source comments satisfy the signal-to-noise and debug-readability contract;
9. every material codec milestone reruns the pinned speech, Emotional piano,
   and full-length Mozart evidence gate against the preceding Resonith version
   and a complete-byte-matched current official Opus anchor;
10. evaluated PCM comes from the actual decoders and the machine report,
    listening files, losses, hashes, versions, source commit, and wall times
    are publishable;
11. every released improvement has a semantic version and an English
    `CHANGELOG.md` entry linked to the evidence report, with local and GitHub
    artifacts carrying matching versions and hashes.
12. every material architecture gate runs the non-negotiable R-118 union:
    all three complete references plus all 16 R-111 heterogeneous classes.
    A three-file-only or corpus-only result is a fast diagnostic, never a
    milestone, default, version, or general quality/compression claim.
13. each LSPF generation runs long material first, freezes that duration
    frontier, then tunes short material without removing the long incumbent;
14. a rate-only or quality-only win receives a bounded refinement of the
    missing axis before generation freeze, and real-audio comparisons use the
    maximum-effort official Opus frontier.
