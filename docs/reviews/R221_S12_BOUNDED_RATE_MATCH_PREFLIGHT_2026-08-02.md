# R-221 bounded fixed-Opus rate-match preflight

Date: 2026-08-02

Status: **PRE-CODE; INDEPENDENT GO/NO-GO REQUIRED**

## Problem and objective

R-219 correctly stopped when four bitrate-only attempts for
`ebu-female-speech-en` bracketed but did not match the 94,816-byte Resonith
target. The owner requires direct codec comparison and explicitly rejects
searching for a better Opus configuration.

R-221 must preserve one fixed official Opus 1.6.1 configuration and make the
smallest quality-blind rate-control correction that either reaches the frozen
complete-byte tolerance or emits a transparent nearest-rate comparison without
claiming equal-rate superiority.

## Frozen behavior

R-221 inherits the exact audited R-219 runner, authority locks, request/receipt
seals, fresh/resume/quarantine semantics, registered 19-item long-first order,
S11 algorithm, metrics, decoders, time/RSS/disk limits and aggregate scope.
It retains:

- official libopus 1.6.1;
- true VBR, complexity 10, 20 ms frames;
- zero expected loss and 1000 ms maximum delay;
- default phase inversion, zero padding, discarded comments/pictures;
- speech application only for the exact registered `speech` category;
- no preceding-Resonith column and no Opus mode/frame/application/CTL search;
- complete-byte selection before any decode or quality metric.

## Alternatives and falsification

### A. Repeat R-219 unchanged

Rejected. The four attempts are deterministic and would reproduce the same
unmatched stop.

### B. Accept the first or largest Opus point

Rejected. The choice is rate-biased and could manufacture a quality result.

### C. Search the full Opus frontier

Rejected by the owner and unnecessary. The observed attempts already provide a
monotone bitrate bracket inside the single fixed configuration.

### D. Bounded quality-blind bitrate bisection

Selected. Preserve the first four R-219 attempts exactly. Only when none is in
tolerance, inspect all unique observed `q5` points. A legal bracket is exactly
one observed pair with `q_low < q_high`, lower bytes strictly below
`target - tolerance`, and upper bytes strictly above `target + tolerance`.
Choose the legal pair with minimum integer `q5` span, then by lower `q5`, upper
`q5`, lower attempt and upper attempt. Bisect only that integer coordinate with
the exact positive-integer formula
`q_mid = q_low + (q_high - q_low) // 2`, and encode only when
`q_low < q_mid < q_high`.
After every new sample recompute the legal bracket from all unique observations;
do not assume global VBR monotonicity and never extrapolate. Never inspect
decoded audio or a quality field. Stop on a strict match, after twelve total
attempts, when the midpoint repeats any observed `q5`, or when integer width
cannot shrink.

For bracket construction, repeated observations at an identical `q5` must
have identical complete bytes and identical normalized Ogg SHA-256. Any
disagreement is a determinism failure. Agreeing duplicates collapse to their
earliest attempt for bracket construction, while every attempt remains in the
ledger and in the nearest-point total order.

If the first four attempts contain no legal bracket, perform zero extra
encodes and go directly to the quality-blind nearest fallback.

Every terminal condition without a strict match -- absent bracket, twelve
attempts, repeated midpoint, non-shrinking integer width, or exhausted legal
pair -- performs no further encode and selects the quality-blind nearest from
all observed attempts as `UNMATCHED_NEAREST`.

If no strict match exists after twelve attempts, select the nearest observed
complete-byte point by the frozen total order `(absolute byte delta, complete
bytes, q5, attempt)`, decode it, and label the receipt and aggregate
`UNMATCHED_NEAREST`. Publish byte delta and rate-delta percentage. Such a row
is evidence about the two actual operating points but cannot support an
equal-rate winner claim.

Every row carries `comparison_status`, signed complete-byte delta and signed
`100 * delta / target`. The aggregate carries `strict_match_count` and
`unmatched_count`. If any row is unmatched, the top-level comparison status is
`CONTAINS_RATE_MISMATCH`; unmatched rows are mechanically excluded from every
equal-rate win, count, average and claim rather than merely footnoted.

## Smallest coherent implementation

1. Create an R-221 controller identity from the exact audited R-219 runner.
2. Preserve attempts 0-3 byte-for-byte and command-for-command.
3. Add at most attempts 4-11 using deterministic bracket bisection; repeated
   `q5`, absent legal bracket and non-shrinking integer width stop refinement
   rather than extrapolate or loop.
4. Keep strict selection unchanged. Add one quality-blind nearest selector
   only for the exhausted no-match branch.
5. Decode and metric-score exactly one selected Opus point per item.
6. Record `STRICT_MATCH` or `UNMATCHED_NEAREST`, attempt count, complete byte
   delta and delta percentage in receipt, aggregate and Markdown report.
   Aggregate strict-rate statistics accept only `STRICT_MATCH` rows and expose
   counts/status for every exclusion.
7. Start from a fresh nonexistent R-221 root. R-219 outputs cannot seed it.

## Kill and admission gates

- Any Opus configuration/command coordinate other than integer bitrate change
  is NO-GO.
- Any quality-informed attempt, stopping or selection decision is NO-GO.
- More than twelve attempts, a repeated `q5` loop, changed S11/metric/decoder,
  changed manifest/order/bounds or a preceding-generation column is NO-GO.
- Focused tests must reproduce the original four attempts, prove deterministic
  bracket contraction/termination under monotone and nonmonotone observations,
  prove nearest selection ignores quality, exercise absent/exhausted/duplicate
  brackets, and confirm that emitted unmatched rows cannot enter any equal-rate
  aggregate statistic or claim.
- Computation-critical non-rate-control functions must remain AST-identical to
  R-219 after label normalization.
- Independent binary GO is required before code and again before a real R-221
  corpus/Opus run.
