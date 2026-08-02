# R-244 independent R-243 Phase-A preclearance audit

Date: 2026-08-02

Status: **DUAL INDEPENDENT GO FOR PHASE A ONLY**

The exact audited preflight is
`docs/reviews/R243_S15_EXACT_LPC_LIFETIME_HOIST_PREFLIGHT_2026-08-02.md`,
SHA-256
`331653006826f705156b467696ba6e49d8e45dea75acaf7774cb6f7bf9be834c`.

Two independent hostile reviews returned binary GO for the Phase-A authority
transaction only. The reviews verified:

- exact success, staging, failure and future-summary path separation;
- one atomic terminal artifact and no receipt self-hash;
- frozen command, environment, CPU/wall/memory/storage and code-size bounds;
- a deterministic 128-case old-source golden generator;
- legal `np.int16` source and `np.int64` committed/excitation domains;
- an encoder-generated nine-law witness at block size 65, subframe size 512
  and subframe index 57;
- numerical Phase-A consistency predicates;
- immutable separation from R-232, R-240, R-198 and any accepted generation.

This GO authorizes only:

1. `experiments/r243_s15_short_baseline.py`, bounded to 600 physical lines and
   64 KiB;
2. `experiments/fixtures/r243_s15_phase_a_authority.json`;
3. one exact bounded pre-change short evidence execution;
4. atomic publication of either the declared success directory or exact
   failure receipt;
5. a subsequent independent read-only result audit.

It does not authorize editing the scalar oracle or tests, implementing the LPC
hoist, retrying R-232, executing any R-232/R-240 control, using long/real audio,
running R-198, changing syntax/decoder/product behavior, or releasing anything.
Phase B remains blocked until the immutable receipt and raw profile receive a
new explicit independent GO.
