# Resonith Changelog

All notable released changes are recorded here. Measured claims link to
reproducible evidence; targets and hypotheses are explicitly labelled.

The format follows Keep a Changelog principles and the project uses Semantic
Versioning for implementation releases. Bitstream syntax has its own declared
version.

## [Unreleased]

### Research

- Predictive and voiced Basis candidates for speech are the next measured
  encoder experiment. No improvement is claimed yet.

## [0.1.0-alpha.1] - 2026-07-26

### Added

- Portable dependency-free C++20 Golden Core and stable C ABI.
- Python analysis-by-synthesis encoder with the prospective LPS5 transport.
- Native bounded `.resonith` decoder utility.
- Cached Integer Basis Synthesis, multi-Basis lifetimes, phase trajectories,
  transient experiments, integer lifting residuals, native decoder-in-loop
  verification, packet and corruption gates.
- Continuous public-reference evidence and release protocol.

### Measured

- The pinned LibriSpeech and full-length Mozart comparison against official
  Opus is the release evidence for this version. The report is published with
  the versioned release; no broad perceptual-superiority claim is made.

### Compatibility

- Implementation version: `0.1.0-alpha.1`.
- Normative-draft specification version: `0.0.8`.
- The public `.resonith` extension currently carries prospective LPS5
  research transport. Stable Main-0 bitstream compatibility is not yet frozen.

[Unreleased]: https://github.com/moshkinyevhen/resonith/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/moshkinyevhen/resonith/releases/tag/v0.1.0-alpha.1
