# R-191 Path ABI Red-Team Audit

Status: **independent pre-implementation audit completed**

Date: 2026-07-28

## Scope

R-190 had already frozen and implemented a bit-exact first-order edge ABI.
The proposed next step was the dependent R-187 K-best path-family union. The
audit examined whether path policy should extend the edge ABI, remain implicit
inside C++, or receive a separate versioned C ABI.

The audit did not evaluate a predictor, serialized Resonith syntax, decoded
PCM, compression, or quality.

## Alternatives attacked

### Separate path ABI

Accepted conditionally. Independent edge scoring and dependent frontier search
have different storage, policy, and lifetime. A fixed path record plus one
bounded CSR entry pool can represent arbitrary declared path lengths while
preserving exact capacity checks.

### Edge ABI v2

Rejected. Adding frontier policy to the edge manifest would invalidate the
already frozen edge parity fixtures, conflate independent and dependent work,
and still require a separate variable-length arena.

### Internal C++ defaults

Rejected. Hard-coded K, path lengths, or memory budgets would make pruning
invisible, prevent exact preflight, and permit two implementations to search
different hypothesis languages while claiming the same result.

## Blocking findings

The auditors blocked implementation until the following were normative:

1. a non-floating integer amplitude-log and second-order extrapolation law;
2. an overflow-safe signed temporal scaling and rounding rule;
3. canonical path identity and final tie order;
4. explicit protected-weak eligibility and lifetime;
5. lower-median frequency-band assignment with exact boundary behavior;
6. internal and cross-path ownership rules;
7. the exact-small optimization objective and deterministic large fallback;
8. transactional two-pass mutation and stale-input behavior;
9. separate path, entry, frontier, work, and byte limits;
10. complete reports for saturation, bounds, conflicts, and pruning.

R-191 resolves each blocker in writing. In particular, amplitude prediction
uses signed differences of the already frozen integer Q8 log-ratio, a positive
Q16 floor, nearest-even quotient/remainder scaling, and only the R-190 integer
`log2(1+n/d)` cost.

## Required falsification

Implementation remains rejected unless independent Python and C++23 records
are bit-exact for:

- constant and crossing/linear partials;
- amplitude ramps and irregular time deltas;
- protected weak paths and phase-invalid magnitude evidence;
- odd/even lower medians and exact band edges;
- input permutations and equal-score path sets;
- internal, transitive, and cross-path ownership conflicts;
- exact-small selection against brute force;
- minimum/maximum path and entry-arena boundaries;
- stale preflight, insufficient output, work exhaustion, scalar extrema, and
  every checked count/offset/byte overflow.

Edge ABI v1 bytes and existing parity fixtures must not change. Bound-limited
output must never be called complete, and no path result may be described as a
predictor or compression result before the mandatory second audit.

## Verdict

Proceed only with the separate transactional path ABI specified by R-191.
Any implementation that changes edge ABI v1, hides bounds, uses floating-point
path authority, mixes provisional bits with dimensionless scores, or emits
partial semantic output on failure fails this audit.
