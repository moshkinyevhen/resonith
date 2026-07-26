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

## Repository language

- English is the sole language for all public specifications,
  documentation, code comments, commit messages, issue and pull-request
  templates, and GitHub metadata.
- Historical source material in another language must remain outside the
  public repository or be accompanied by a complete English record.

## Validation

After a change, verify:

1. relative links and Markdown structure;
2. the status of every numerical statement;
3. separation of standalone Resonith from the SceneLith AV Bridge;
4. primary-source support for external claims;
5. absence of secrets, unnecessary personal data, and undocumented
   dependencies;
6. zero Cyrillic text in tracked public files;
7. relevant tests, conformance hashes, and cross-platform build checks.
