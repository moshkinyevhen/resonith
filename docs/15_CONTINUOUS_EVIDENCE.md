# Continuous Evidence and Release Protocol

Status: **ACCEPTED**

This protocol turns every material Resonith milestone into a reproducible
compression, quality, portability, and playback experiment. It applies before
an improvement claim, version, tag, or public release.

## 1. Pinned public references

The minimum gate uses:

| Role | Source | Canonical PCM input |
|---|---|---|
| Speech | LibriSpeech `1272-128104-0000`, CC BY 4.0 | mono PCM16, 16 kHz, 5.855 s |
| Long music | Mozart, *Die Zauberflöte*, K. 620 — Overture, Musopen Symphony, public domain | stereo PCM16, 48 kHz, 400.773 s |

Source downloads, deterministic PCM conversion, licenses, URLs, sample counts,
and SHA-256 hashes belong in the benchmark manifest. A milestone MAY add
material but MUST NOT silently replace these references after observing a
result.

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
and Opus. It states wins and losses by metric and material.

- A mechanism that loses its declared gate is removed.
- A mechanism with a narrow or ambiguous result remains explicitly
  experimental and disabled by default.
- Corpus, anchor, alignment, or metrics MUST NOT be changed post hoc to hide a
  loss.
- Perceptual, transparent, or broadly superior claims require controlled
  blinded listening with hidden reference and anchors.

## 5. Published artifacts

Every release publishes:

- the two canonical input WAV files;
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
