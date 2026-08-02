# R-253 S15 bounded exact LPC-lifetime Phase-B preflight

Date: 2026-08-02

Status: **PRE-CODE DRAFT; IMPLEMENTATION NO-GO PENDING DUAL AUDIT**

## Problem, objective, and frozen baseline

S15 remains active from accepted S12. R-250 is the immutable pre-change
measurement at execution commit
`4a74ee485ea0d1e207063920d45001ee6d4564ee`; R-252 admits that evidence only.
Its receipt SHA-256 is
`b28f8d264d183d34a817f0523ec274cb2ac057df66413235e578d295ffedba8d`.

The rescored short arm emits 12,371 bytes and decoded PCM SHA-256
`bcff64e10968a7050e7296f95d5a77491a034f1b47f013edc4e0d940ef5977a8`.
Its median process CPU is 39.03125 seconds. The profile records 648,120 calls
to `_lpc_q14`, 58.5003879 cumulative seconds, and a ratio of
0.6097914076180061 to the 95.9350807-second encode cumulative time.

The frozen configuration has 128-sample FilterLaw blocks and 64-sample
excitation subframes. The law therefore remains constant for two complete
subframes, but `_desired_short_excitation_target` derives the same LPC tuple
once per sample and every `_synthesize_short_filter_candidate` derives it
again for every realized candidate sample.

The single Phase-B objective is:

> Remove only this redundant conversion by preparing the bounded FilterLaw
> region once per subframe, while preserving every selector-visible and
> externally visible value exactly.

The complete cost includes new code and fixture bytes, helper live memory,
conversion counts, CPU, wall, peak memory, all candidate/transaction evidence,
full stream bytes, decoded PCM, and deterministic report identities. Quality
and compression must remain identical; no gain may be attributed to this
mechanical refactor.

## Source-of-truth review

First principles require a pure function of an immutable FilterLaw to produce
the same Q14 tuple wherever that law is reused. Moving that pure computation
earlier cannot change results if coefficient order and every consuming integer
operation remain unchanged.

RFC 6716 makes bit-exact fixed-point operations and rounding part of decoder
conformance and describes Q-format arithmetic explicitly. This forbids an
approximate or reordered implementation:

- <https://datatracker.ietf.org/doc/html/rfc6716>

The current official Xiph Opus implementation passes an already prepared LPC
coefficient vector to its analysis filter and then applies it across a signal
region. It also keeps stability conversion separate from sample filtering.
This is prior art for coefficient lifetime, not a novelty claim for Resonith:

- <https://github.com/xiph/opus/blob/master/silk/LPC_analysis_filter.c>
- <https://github.com/xiph/opus/blob/master/silk/LPC_inv_pred_gain.c>

The decisive source remains Resonith's scalar code plus the audited R-250
profile and 128-case pre-change oracle. External implementations do not prove
output identity for Resonith.

## Alternatives and falsification

1. **No change.** Safest for identity, but retains the measured 648,120-call
   redundancy and blocks a bounded long-control revisit. It remains the
   fallback after any Phase-B failure.
2. **Process-global `functools.cache` or `lru_cache`.** Rejected: hidden
   cross-file lifetime, input-history-dependent memory, and unnecessary
   locking/state violate bounded deterministic ownership.
3. **Precompute every FilterLaw for the complete file.** Rejected: it turns a
   subframe-local need into up to `MAX_BLOCK_COUNT` retained tuples.
4. **Assume one law per subframe.** Rejected: legal 512-sample subframes can
   cross nine 64-sample filter blocks, and arbitrary legal starts need exact
   absolute addressing.
5. **Store derived LPC inside mutable analysis objects.** Rejected: it expands
   object lifetime and risks stale derived state after law replacement in
   tests or research transforms.
6. **Vectorize, approximate, reorder, or use floating point.** Rejected:
   signed rounding, accumulation order, saturation, and selector ties are
   observable.
7. **Native C++23 batch evaluation.** Plausible later S15 work, but it adds an
   ABI and differential proof before removing the directly measured Python
   redundancy.
8. **CUDA evaluation.** Rejected here: small causal candidate sets and host
   state make transfer/launch and device identity additional costs without
   solving the simplest repeated conversion.
9. **Bounded per-subframe immutable preparation.** Selected as the smallest
   coherent, falsifiable, output-identical change.

## Authorized implementation shape

After two independent written GO verdicts, Phase B may:

1. Add one private helper in
   `reference/maf_p0/maf_source_filter_oracle.py`. It validates
   `0 <= start < stop <= source_size`, `64 <= block_size <= 8192`,
   `1 <= stop - start <= 512`, and
   `law_count == ceil(source_size / block_size)`. It returns
   `(first_block, tuple_of_lpc_tuples)`.
2. Compute `first = start // block_size` and
   `last = min(law_count - 1, (stop - 1) // block_size)`. The returned count
   must equal `last - first + 1` and must be in `[1, 9]`.
3. Prepare that value once at the start of every existing subframe in both
   `_collect_closed_loop_excitation_targets` and `_encode_excitation_pvq`.
   This closes both direct `_desired_short_excitation_target` callers, including
   Basis training when `basis_count > 0`.
4. Pass the same immutable value to `_desired_short_excitation_target` and,
   in the main encoder loop, every `_synthesize_short_filter_candidate` call
   for that subframe.
5. In each unchanged sample loop, map
   `absolute = min(law_count - 1, index // block_size)` and
   `offset = absolute - first_block`; fail closed unless the offset is within
   the prepared tuple. Coefficient and sample loops stay in their present
   order.
6. Update only the direct private-function tests and add one deterministic
   gzip fixture generated byte-for-byte from the R-250 golden JSON with
   `gzip.compress(level=9, mtime=0)`. Its required size is 56,229 bytes and
   SHA-256 is
   `793bff4e748435c079668920a5a2a6cc97b932250bb1bca1df69ed2c6958cc35`.
7. Add one bounded post-change evidence runner derived from the already
   audited R-250 transaction. It may add only prepared-law observation and
   exact pre/post identity checks; it may not change audio work, candidate
   lattice, metrics, budgets, or terminal semantics.

No public API, native core, decoder, bitstream, version, default, product,
Orkela, corpus, Opus anchor, or accepted-generation file may change. The
implementation budget is at most 100 changed non-comment oracle lines, 180
test lines, one 56,229-byte compressed fixture, and one runner no larger than
700 physical lines and 72 KiB. Documentation and canonical evidence summaries
do not reset these limits.

## Verification and kill gates

Focused verification, before any timed run, must prove:

- exact decompression SHA-256
  `8fe390457f9baf5226207f2d3c3ebb71c6ba5ac968921cb7e6e145f9b4e8ccf6`
  and all 128 ordered golden cases;
- exact desired excitation, candidate output, clipping count, touched LPC
  tuple and nine-block maximum witnesses;
- existing source-filter and R-232 focused tests;
- invalid empty/reversed/out-of-range intervals, insufficient laws, block
  or region sizes outside profile bounds, insufficient or excess laws, block
  mapping failure, and any prepared-count greater than nine fail closed;
- all direct desired-target callers are exercised, including a nonzero
  `basis_count` path through `_collect_closed_loop_excitation_targets`;
- no global cache or state survives a call.

The post-change transaction then uses the same source, configuration, three
paired timing trials, one cProfile arm, resource bounds, and exact identity
projection as R-250. It additionally records helper returns and caller-attributed
`_lpc_q14` calls using an external, non-timed profile witness.

Mechanical admission requires all of the following:

- legacy and rescored payload, decoded PCM, waveform SSE, candidate order,
  candidate-choice digest, clipping, floating mel values, Q20 quality,
  eligibility, winner, transaction witness, and semantic report identity are
  byte-for-byte or value-for-value equal to R-250;
- helper-attributed conversions equal `prepared_entries_total`, each region's
  conversions equal its touched-law count, and the count does not scale with
  candidate evaluations;
- `prepared_entries_peak <= 9` and recursively deduplicated helper live size is
  at most 16 KiB;
- neither timing arm regresses by more than 2% median process CPU and at least
  one improves by 10% or more; median wall corroborates and may not regress by
  more than 10%; timing-worker peak memory may not grow by more than 8 MiB;
- authority, source, runtime, file set, receipt, logs, staging cleanup, and
  controller/worker resource bounds all pass.

Any deterministic mismatch or bound failure is terminal NO-GO for this
implementation. It cannot be rescued with tolerance, reordered arithmetic,
fewer candidates, a reduced test matrix, larger resource limits, or a second
remediation cycle.

## Consequence

A pass admits only an output-identical research-oracle performance refactor,
so the R-198 full-corpus/Opus gate is not triggered. A later structural batch
evaluator is a new S15 material work package with its own theory and audit.
R-232's rejected long execution is not reopened by this preflight.

Until two independent auditors return binary GO over this exact record,
implementation remains **NO-GO**.
