# R-243 S15 exact LPC-lifetime hoist preflight

Date: 2026-08-02

Status: **PHASE-A REMEDIATION DRAFT; ALL EXECUTION NO-GO**

## Problem and frozen baseline

R-232 is terminally rejected. Its first 120-second synthetic control reached
the unchanged 900-second worker ceiling before candidate publication. No
codec generation was admitted and S12 remains the accepted frontier.

An earlier unretained 5.855-second diagnostic indicated:

- 15.1562 seconds to source-filter analysis;
- 10.5796 seconds to the legacy EPV1 arm;
- 38.7987 seconds to the decoder-domain-rescored EPV1 arm.

Linear projection of the complete paired control is therefore approximately

```text
120 / 5.855 * (15.1562 + 10.5796 + 38.7987) = 1322.7 seconds.
```

The profile of the rescored arm recorded 90.441 profiled seconds, including
64.652 cumulative seconds in `_synthesize_short_filter_candidate`, 648,120
calls and 55.553 cumulative seconds in `_lpc_q14`, and 30,698,931 calls and
33.650 cumulative seconds in `_round_divide_signed`.

These preliminary, historical, non-gating arithmetic values explain why the implementation was
investigated, but they are not admission evidence because the raw timing and
profile artifacts were not retained. Their derived values are:

```text
k = 120 / 5.855 = 20.4953031596926
Tshort = 15.1562 + 10.5796 + 38.7987 = 64.5345 seconds
P0 = k * Tshort = 1322.65414175918 seconds
Tshort,max(780) = 780 / k = 38.0575 seconds
rescored,max = 38.0575 - 15.1562 - 10.5796 = 12.3217 seconds
required rescored saving = 26.4770 seconds = 68.24198 percent
```

The unfavorable proportional estimate is also historical, non-gating context.
The reported
LPC-conversion share of the profiled path is
`55.553 / 90.441 = 61.42458 percent`. Treating its removal as free estimates a
14.96676-second rescored arm and an approximately 834.21138-second historical
projection. Profiling overhead and overlapping cumulative times prevent this
from being a bound. None of these derived values is an R-243 gate, screen or
authorization; they only explain why the earlier long-run proposal was
rejected. The bounded redundancy is nevertheless large enough to justify one
evidence-closed short mechanical experiment.

The frozen control uses `block_size=128` and `subframe_size=64`. A FilterLaw is
therefore constant for two complete subframes, yet the current implementation
steps its reflection coefficients to Q14 LPC once per sample and once again
for every realized candidate. This is redundant work, not a property of the
codec hypothesis.

## Objective and complete cost

Test one claim only:

> Preparing each persistent FilterLaw once for the bounded subframe region in
> which it is used removes the dominant redundant work while preserving every
> candidate, integer operation, comparison, selected record, stream byte and
> decoded PCM sample.

The cost includes wall and CPU time, peak memory, prepared-law counters, all
existing candidate and transaction evidence, and deterministic stream/report
projections. No quality or byte improvement may be attributed to this
mechanical experiment.

R-243 is **not** a retry, rescue or reopening of R-232. It may admit only an
output-identical mechanical oracle refactor. It does not authorize the R-232
120-second controls. A later S15 work package requires a separate preflight
that structurally removes per-candidate Python synthesis and FFT calls through
bounded batch evaluation before any new long-control attempt.

## Evidence closure before source edits

The earlier timing/profile prose is insufficient. R-243 is split into two
separate authority transactions. Phase A may create only:

- `experiments/r243_s15_short_baseline.py`;
- `experiments/fixtures/r243_s15_phase_a_authority.json`;
- one immutable output rooted at
  `artifacts/r243-s15-short-baseline-prechange`;
- the exact temporary sibling
  `artifacts/r243-s15-short-baseline-prechange.staging` during execution;
- the terminal failure receipt
  `artifacts/r243-s15-short-baseline-prechange-failure.json` instead of a
  successful output;
- the preflight/audit/checkpoint/changelog documents required to bind them.

Phase A may not edit the scalar oracle, tests, R-232/R-240 artifacts, native
code or any product path. Its runner executes the unchanged registered short
speech input in two explicit modes:

1. an unprofiled timing mode that records analysis, legacy and rescored stage
   wall and process-CPU times, process peak memory, payload/PCM/deterministic-
   report identities, candidate/subframe counts and exact command/environment;
2. a cProfile mode that retains the raw `.prof` file plus deterministic text
   statistics sorted by cumulative and self time.

A Phase-A GO authorizes only the path classes above and one exact evidence
execution. It cannot authorize helper, scalar-oracle, focused-test, native or
product edits. The runner is at most 600 physical lines and 64 KiB; no other
new executable source is authorized in Phase A.

The runner uses a controller/worker role, a fresh sibling staging directory,
atomic success rename, stop-on-first-failure and one external atomic failure
receipt. Before launch, the final output, exact failure receipt,
`experiments/results/r243_s15_short_baseline_prechange.json`, the exact staging
sibling, and any unexpected sibling matching
`r243-s15-short-baseline-prechange.staging-*` must all be absent. Only the final
output, failure receipt and staging sibling must resolve with exact parent
`G:\Resonith\artifacts`; the future repository-summary path must resolve with
exact parent `G:\Resonith\experiments\results`, must be absent, and the Phase-A
runner must never open or write it. None of the four exact targets may be a
reparse point. The controller publishes exactly one
terminal state: either the complete artifact directory with an internal
`receipt.json`, or the exact external failure receipt above. A repository
summary may be copied only after the mandatory read-only audit in a separate
documentation transaction. The exact controller invocation is:

```powershell
$env:PYTHONHASHSEED='0'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe `
  G:\Resonith\experiments\r243_s15_short_baseline.py `
  --authority G:\Resonith\experiments\fixtures\r243_s15_phase_a_authority.json `
  --authority-sha256 <frozen-lowercase-sha256> `
  --output G:\Resonith\artifacts\r243-s15-short-baseline-prechange
```

The unprofiled worker has a 300-second wall ceiling, 300-second process-CPU
ceiling and 512-MiB peak-process-memory ceiling. The profile worker has a
180-second wall ceiling, 180-second process-CPU ceiling and the same memory
ceiling. The controller has a 510-second total wall ceiling. Successful
retained output is at most 32 MiB; stdout/stderr and the failure receipt are
each at most 1 MiB. Success uses schema
`resonith-r243-s15-phase-a-receipt-1`; failure uses
`resonith-r243-s15-phase-a-failure-1`. Any timeout, nonzero exit, identity drift, budget failure,
pre-existing output/staging path or malformed receipt is terminal for Phase A
without blind retry. At most one audited runner-only remediation may follow;
no evidence run may be repeated merely to obtain better timing.

On any worker/controller exception, the exact staging directory is removed
only after its resolved containment is revalidated; failure to remove it is
recorded in the external failure receipt. Success atomically renames the
complete staging directory to the final output and writes no other terminal
artifact.

The receipt binds and hashes the 93,680-sample, 16-kHz source, frozen
configuration, Python executable, NumPy version and loaded binary, native Core,
scalar oracle, R-232 runner, test module, baseline runner, Git commit and every
retained file except `receipt.json` itself in a canonical path-sorted manifest.
The read-only audit independently hashes `receipt.json` and may derive a
canonical whole-tree identity. It records `PYTHONHASHSEED`, BLAS thread variables and
`PYTHONDONTWRITEBYTECODE`. Outputs use a fresh never-used path and atomic
publication. No long control or real-audio corpus is run.

The timing worker performs one measured analysis construction followed by one
warm-up pair and three measured counterbalanced arm pairs in order
`legacy/rescored`, `rescored/legacy`, `legacy/rescored`. Median process CPU is
primary and median wall is secondary. The cProfile worker performs one fresh
analysis and profiles exactly one rescored encode. The raw profile is not used
as a timing trial. After all measured timing trials, with all stage timers
inactive, the timing worker emits the 128 golden vectors; their work remains
inside that worker's 300-second wall/CPU and the controller's 510-second
ceilings.

The old-source worker also emits deterministic golden vectors before any
source edit. It uses seed `0x524243`, the four filter-law families
`(-115)`, `(0)`, `(115)`, and
`(-115,103,-91,79,-67,55,-43,31,-19,7,11,-23,35,-47,59,-71)`. The first three
are order-1 laws; the mixed law is order 16. The eight exact interval
specifications are:

```text
(source=2048, block=64,   start=192,   stop=193)
(source=2048, block=64,   start=193,   stop=209)
(source=2048, block=64,   start=255,   stop=319)
(source=2048, block=64,   start=256,   stop=320)
(source=2048, block=64,   start=511,   stop=1022)
(source=40000, block=65,  start=29184, stop=29696) # subframe=512, index=57, nine blocks
(source=300,  block=64,   start=287,   stop=300)   # truncated tail
(source=32768, block=8192, start=16383, stop=16895)
```

For each interval, `law_count = ceil(source / block)`. For base first
coefficient `q` and zero-based absolute block `j`, the sentinel first
coefficient is `-115 + ((q + 115 + 17*j) mod 231)`; remaining coefficients are
unchanged. Blocks are generated in ascending absolute order.

For each of the 32 law/interval pairs, four fixed patterns are evaluated. Every
full `analysis.source` array has dtype `np.int16`; every full
`committed_output` array and sliced `raw_excitation` array has dtype
`np.int64`. Let
`alt[i] = -32768` for even absolute `i` and `32767` otherwise. The LCG starts at
`state=0x00524243`; before each output it advances as
`state=(1664525*state+1013904223) mod 2^32`, then emits
`((state >> 16) & 0xffff) - 32768` in the unsigned-32-bit arithmetic domain.
The emitted mathematical integer is converted to the target dtype only when
assigned. Arrays have exactly the declared source length; raw excitation is
sliced to `[start,stop)` and converted to `np.int64`.

1. zero: source, committed output and raw excitation are all zero;
2. alternating: source and committed output are `alt`, raw excitation is the
   matching `alt[start:stop]`;
3. LCG: source and committed output are the full emitted sequence, raw
   excitation is its `[start:stop]` slice;
4. clipping: source and committed output are `alt`, raw excitation is all
   `32767`.

Cases serialize in interval-list order, then law-family order, then pattern
order. Every case records source size, block size, start, stop, all three dtype
strings and optional
`subframe_size/subframe_index`; the maximum witness records `512/57`. JSON is
UTF-8, sorted keys, two-space indentation, LF newline, finite
decimal mathematical integers independent of NumPy scalar rendering only. The complete 128-case
matrix retains the exact touched `_lpc_q14` tuples, desired excitation,
candidate output and clipping count from the pre-change scalar path. The runner
hash is frozen in Phase-A authority; the generated golden JSON hash is bound by
the atomic receipt and subsequent read-only audit.

After Phase A, an independent read-only audit must verify the receipt, raw
profile, golden-vector count/identities, commands, budgets and immutable
pre-change source. Only a new explicit Phase-B GO may authorize oracle/test
edits. The retained baseline must show median rescored CPU greater than median
legacy CPU, at least 100,000 `_lpc_q14` calls in the profiled rescored encode,
and `cumtime(_lpc_q14) / cumtime(encode_maf_source_filter_analysis) >= 0.50`.
These are Phase-A consistency predicates, not post-edit performance targets.
If any predicate fails, close R-243 and reformulate from retained facts.

## Alternatives and falsification

1. **No change.** Safe, but R-232 remains unexecutable under its declared
   resource limit. Retain if this experiment fails any exactness or projection
   gate.
2. **Raise the 900-second ceiling or shorten controls.** Rejected. Either action
   conceals the already measured resource failure and changes the frozen
   evidence question.
3. **Global `lru_cache` of FilterLaw conversions.** Rejected. Its process-wide
   lifetime, hidden memory growth and cross-input state are unnecessary.
4. **Prepare every law for the entire file.** Rejected. It duplicates up to
   `MAX_BLOCK_COUNT` tuples and increases long-input memory when only a bounded
   current region is required.
5. **Native C++23 candidate-lane batch.** Plausible next option, but deferred.
   It adds an ABI, two-language differential proof and more code before the
   measured redundant conversion has been removed.
6. **CUDA candidate evaluation.** Rejected for this gate. Subframes are causal
   and have a small candidate count; launch/transfer cost and device identity
   add risk without addressing the obvious repeated host conversion.
7. **Approximate statistics, reordered arithmetic or a new source-filter
   model.** Rejected. Rounding, clipping and log-mel thresholds are
   selector-visible; this preflight authorizes no algorithm change.
8. **Bounded exact LPC-lifetime hoist.** Selected provisionally as the smallest
   coherent output-identical refactor, not as a new codec generation.

Current Opus is native C and includes architecture-specific optimized SILK
paths, but that is evidence for later product optimization, not permission to
skip the smaller exact correction here. RFC 6716 also describes SILK LPC/LTP
state as causal synthesis state rather than a quantity to derive repeatedly
for every output candidate. Primary references:

- <https://datatracker.ietf.org/doc/html/rfc6716>;
- <https://opus-codec.org/demo/opus-1.5/>;
- <https://github.com/xiph/opus>.

## Prospective Phase-B implementation scope

This scope is not authorized by a Phase-A audit. Only a later explicit
Phase-B GO after read-only audit of the immutable Phase-A receipt and golden
vectors may authorize these items:

1. Add one private helper that prepares Q14 LPC tuples for exactly the filter
   blocks touched by `[start, stop)`.
2. The first prepared block is `start // block_size`; the last is
   `min(law_count - 1, (stop - 1) // block_size)`. Legal profile bounds imply
   at most nine prepared laws for one subframe (`subframe_size <= 512`,
   `block_size >= 64`).
3. Compute this bounded tuple once per subframe before desired-excitation and
   candidate evaluation.
4. Pass the same immutable prepared tuple to
   `_desired_short_excitation_target` and every
   `_synthesize_short_filter_candidate` call for that subframe.
5. Bind the tuple to `first_block`. Inside each existing sample loop compute
   `absolute = min(law_count - 1, index // block_size)` and
   `offset = absolute - first_block`; fail closed unless
   `0 <= offset < prepared_count`. Do not change coefficient order,
   accumulation order, signed rounding, clipping, FFT/log-mel evaluation,
   candidate order, bit cost, eligibility, tie order, trace construction or
   commit order.

The helper is per-call and bounded. It retains no state across subframes,
encodes or files. No syntax, decoder, public ABI, candidate lattice, threshold,
version, default, product or Orkela behavior changes.

For `L = stop - start`, block size `b`, and `r = start mod b`, the exact bound
is:

```text
touched = floor((stop - 1) / b) - floor(start / b) + 1
        = ceil((r + L) / b)
        <= ceil((L + b - 1) / b)
        <= ceil((512 + 64 - 1) / 64)
        = 9.
```

The helper must require `0 <= start < stop <= source.size`, require
`prepared_count == last_block - first_block + 1`, and fail closed if the count
exceeds nine.

Prepared-law observation uses an external `sys.setprofile` witness in a
separate non-timed counter run. It counts `_lpc_q14` calls by caller and
inspects the private preparation helper's returned `(first_block, tuple)` only
on its return event. The sidecar records each region's `start`, `stop`, touched
count, actual conversion calls and the already-existing candidate-evaluation
count, plus `prepared_regions`, `prepared_entries_total`,
`prepared_entries_peak` and total conversions. It is never active during
timing, never imported or queried by RDO, requires no oracle hook or global
cache, and retains no prepared tuple after the observed return is summarized.
For every region it must prove that conversions equal touched laws before the
candidate loop and do not scale with candidate evaluations.

The exact observation invariant is:

```text
helper-attributed _lpc_q14 calls
    == prepared_entries_total
    == sum(last_block - first_block + 1)
prepared_entries_peak <= 9
```

Every unrelated `_lpc_q14` caller is enumerated separately in the call graph
and excluded from the helper-attributed equality. Instrumented/profiled times
never participate in performance admission.

## Exactness and adversarial gates

Before any Phase-B mechanical admission:

1. Compare the new prepared path against a frozen pre-change scalar test
   oracle that neither calls the new helper nor shares its prepared-block index
   mapping. The finite deterministic matrix uses seed `0x524243` and includes:
   - filter orders 1 and 16;
   - reflection laws `-115`, `0`, `+115`, and one frozen mixed-sign order-16
     vector;
   - block sizes 64 and 8192 plus explicit crossing constructions;
   - offsets 0, 1 and `block_size - 1` at nonzero absolute blocks;
   - lengths 1, 16, 64, 511 and 512 where legal;
   - int16 excitation/output clipping endpoints and negative/positive signed
     division half cases;
   - exact boundaries, one/multiple crossings, a truncated final source, and a
     legal generated witness that reaches all nine blocks;
   - unique sentinel laws on adjacent blocks so an absolute/local addressing
     error cannot alias silently.
2. Run the existing source-filter and R-232 focused tests.
3. On the frozen short diagnostic require exact equality of:
   - ordered candidates and candidate-choice digests;
   - clipping counts, waveform SSE, IEEE-754 mel values and Q20 quality;
   - eligibility, keys, winners, decision changes and transaction evidence;
   - complete legacy and rescored payloads and decoded PCM hashes;
   - a canonical deterministic semantic projection of each report that
     excludes wall/CPU/resource fields, while those fields are retained and
     compared separately by bounds.
4. Measure module/source authority before and after with the same closure rigor
   as R-240, without mutating any R-240 artifact.

Any mismatch is terminal NO-GO for this implementation. It may not be hidden
with a tolerance because the intended change is mechanical and exact.

## Mechanical admission gates

After focused exactness passes, Phase B runs the identical counter and timing
protocol against a fresh post-edit authority. Admit the mechanical refactor
only if:

- every deterministic identity and scalar-oracle comparison passes exactly;
- the median process CPU of neither arm regresses by more than 2 percent and
  at least one improves by 10 percent or more; median wall is corroborating
  evidence and may not regress by more than 10 percent;
- helper-attributed conversions equal `prepared_entries_total`, and each
  region's conversion count remains equal to its touched-law count regardless
  of candidate evaluations;
- `prepared_entries_peak <= 9`;
- a recursive, identity-deduplicated `sys.getsizeof` measurement of the helper
  return value is at most 16 KiB live, and the single identical timing-worker
  peak process memory does not regress by more than 8 MiB;
- no global cache or cross-run prepared state exists.

The deterministic conversion-count reduction is the primary mechanical proof;
timing is corroboration. This short result is not extrapolated to stable-AR or any 120-second control.
Candidate cardinality and stage mix are input-dependent. Any later long-run
screen must use at least two bounded prefixes of the same deterministic control
and then rely on the actual full-control resource result.

The following arithmetic is retained only as historical, non-gating negative
context. The earlier auditor suggestion of both an isolated `4x` hot-function speedup
and a full `<600`-second projection is rejected as internally inconsistent.
With the measured stage times, accelerating only the measured 71.5-percent hot
function by 4x projects approximately 896.233 seconds. Making only that hot
function infinitely fast projects approximately 754.092 seconds. An
infinitely fast *entire* rescored arm would leave the fixed analysis-plus-
legacy projection at approximately 527.463 seconds. None of the 780/896/754
values authorizes or screens any later execution. A later structural-batch
preflight must derive its own same-control-prefix and actual-control gates from
fresh evidence.

## Terminal consequence and S15 continuation

R-243 ends after the bounded short comparison and independent implementation
audit. It never executes the R-240 incumbent/control suite and never changes an
accepted codec generation. Pass or fail, it therefore does not trigger R-198.

If admitted as an exact mechanical refactor, the next action is a new S15
preflight for a bounded exact batch evaluator that structurally eliminates
per-candidate Python synthesis and per-candidate FFT calls. That later suite
must start with incumbent identity followed by the four frozen controls in a
fresh output path, stop on first failure, and require each actual control to
finish within its declared admission bound. Only after all precursor gates may
the full registered long-first R-198 corpus compare the candidate against S12
and maximum-effort official Opus.

The Phase-A authority and receipt remain immutable. Phase B requires a fresh
post-edit authority and an explicit changed-file proof showing that only the
scalar oracle, its focused test, R-243 evidence tooling/results and required
audit/checkpoint/changelog documents changed. The mixed worktree is never
staged wholesale.

## Independent-audit questions

The reviewer must return binary GO/NO-GO and specifically challenge:

1. whether prepared-law reuse can alter any arithmetic or causal state;
2. whether the nine-law bound follows from every legal profile combination;
3. whether the exactness oracle covers boundary-crossing subframes;
4. whether evidence closure and the finite parity matrix are reproducible;
5. whether mechanical admission can be kept separate from any R-232 retry;
6. whether any hidden codec, syntax, decoder or evidence-generation change is
   authorized accidentally.
