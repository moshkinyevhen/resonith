# R-187 Partial-Path Union Adversarial Review

Date: 2026-07-28  
Disposition: accepted for quarantined analyzer work only

## Scope

The review covered the R-186 complex-DTFT observation set, a draft
second-order K-best tracker, and the proposed local-potential ranking. It did
not authorize synthesis, a predictor, bitstream syntax, R-183 transport,
whole-track compression claims, or release integration.

## Frozen counterexamples

The rejected draft followed stable Hann sidelobes through a two-chirp
crossing. It emitted three tracks instead of two in the original audit, with
mean phase error about 0.9168 radians. A weak 2 kHz line at amplitude 50 below
a 12,000-amplitude 440 Hz line appeared in only 4 of 188 observations. White
noise produced 9,072 observations and 95,660 edges in 3.49 seconds, while a
one-second continuation run exceeded 40 seconds. A clean 440.3 Hz tone was the
positive control.

## Rejected claims and alternatives

- A constant artificial value per observation is not a residual-rate model.
- `base + scale * log(amplitude)` is a heuristic potential, not bits.
- Energy-only selection removes weak lines.
- Continuity-only selection can prefer coherent leakage.
- Raising detection thresholds hides the observation error.
- A semantic or neural label cannot authorize partial identity.
- Selecting one representative from a sub-Rayleigh cluster can silently
  collapse two genuine close lines.

## Accepted bounded design

The proposer retains a deterministic union of:

1. continuity-ranked paths;
2. uncertainty/leakage-aware local-potential paths;
3. frequency-stratified protected weak-line paths.

Potential and provisional program bits are separate units. Every path reports
node value, uncertainty/leakage penalty, continuity score, provisional program
cost, phase error, family, and ownership conflicts. Scores are saturating
fixed-point integers with lexicographic tie breaks.

The observation audit found two earlier causal defects:

- Per-band `argmax` fallback manufactured monotonic band boundaries as
  sinusoidal peaks. R-188 replaces it with one plateau-aware full-spectrum
  canonical peak set followed by half-open band allocation.
- A three-bin Hann main-lobe median was treated as noise and rejected its own
  true maximum. R-189 keeps every canonical maximum in the candidate pool and
  applies only the declared finite allocation. Confidence annotates proposals
  but never erases them.

No ambiguity representative is admitted. Genuine sub-Rayleigh maxima remain
an unresolved equivalence group with all members retained.

## Required kill gate

- both crossing chirps survive in the top-K equivalence set;
- sidelobes do not displace them;
- the approximately -47.6 dB line survives a protected family;
- the 440.3 Hz frequency and centered-phase control does not regress;
- white-noise allocation stays within two candidates per band and 48 per
  detector/frame and reports pruning;
- every score component and ownership conflict is public;
- a second audit occurs after native C++23/CUDA parity and before synthesis.

## Final restriction

This audit accepts an analyzer proposer, not a codec. The only authoritative
rate decision remains:

`pack -> native decode -> one final Truth -> actual complete bytes`.
