# R-218 S11 output-identical performance preflight

Status: **REVISED PREFLIGHT; CODE CHANGE BLOCKED PENDING RE-AUDIT GO**

## Problem and frozen objective

R-217 is a direct comparison between current Resonith and one fixed official
Opus 1.6.1 maximum-complexity anchor. It is not an Opus-frontier search. The
first full run stopped at the 420-second short-input S11 ceiling. The sole
bounded redesign raised that ceiling to 900 seconds. In the second run,
`ebu-claves` completed in 792.173034 seconds and `ebu-cymbal` exceeded 900
seconds. R-211 forbids another limit increase.

The objective is therefore purely mechanical: reduce S11 analyzer runtime
while preserving the exact candidate language, observation values and order,
native graph, lane lowering, RDO, complete payload bytes, decoded PCM, memory
and disk ceilings, fail-closed behavior, and fixed Opus anchor.

## Baseline and measured profile

- Frozen analyzer SHA-256:
  `29027daf255d368a823f6cd6082b79db7f8d1ddd65251e2855757a3390caa475`.
- Frozen predictor SHA-256:
  `583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec`.
- `ebu-claves` S11 payload: 216,421 bytes, SHA-256
  `9156b28ec67b25c6fc222a52d74431e9cf656f67b7bc01409e94ff4e601927dd`.
- Its decoded WAV SHA-256 is
  `5f3faea4de8c34dd1ee39092e78fce5d075115bb52ebc8215c2a5bfb2fdea596`.
- A replay of all seven frozen focused cases reproduced payload bytes, decoded
  PCM, selected bytes, and selected kind exactly before profiling.
- Focused `cProfile` artifact SHA-256:
  `30751ef297425c498d5eec7f8adc6036f0f76b4de90c203d98b2596286b2b691`.

The 42.579-second instrumented run attributed cumulative time as follows:

| Site | Cumulative seconds | Calls |
|---|---:|---:|
| `observe_complex_partials` | 29.592 | 8 |
| `_candidate_peaks` | 11.921 | 1,464 |
| `_direct_dtft` | 8.120 | 30,440 |
| `_assign_conflict_groups` | 5.488 | 8 |

The current conflict loop evaluates only a narrow time neighborhood, but
`ordered[position + 1:]` first materializes the entire remaining list on every
outer iteration. This creates quadratic reference-copy work unrelated to the
candidate set. The analyzer also executes `source.astype(np.float64)` once per
FFT frame even though the input is immutable.

For the focused 30,440-observation profile, the tail slices copy
463,281,580 references, approximately 3.45 GiB of pointer traffic before list
object overhead, even though the time-window break examines only a small
neighborhood. A 12-second, 44.1 kHz item invokes 5,431 analysis frames. The
current per-frame float64 conversion therefore allocates 45,985,363,200 output
bytes across those conversions before allocator reuse.

Official Python documentation defines list slicing as constructing the slice
sequence and states that `list(existing_list)` returns a copy similar to
`existing_list[:]`:
<https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range>.
NumPy documents that `astype` with its default `copy=True` allocates a converted
array:
<https://numpy.org/doc/stable/reference/generated/numpy.astype.html>.
NumPy also warns that floating-point summation precision can depend on the
reduction route, so a batched matrix multiply or changed summation order is not
an output-identical refactor:
<https://numpy.org/doc/stable/reference/generated/numpy.sum.html>.

## Alternatives and falsification

### A. Remove only the tail-list allocation

Iterate second positions by integer index over the existing sorted list. The
same `second_index` sequence, comparisons, union order, and first time-window
break are retained. This removes no hypothesis and changes no arithmetic.

Risk: an off-by-one or changed break position would alter conflict ownership.
Falsification: dual-execute old and new loops on exhaustive small sets,
randomized boundary cases, every focused observation set, and real prefixes;
require identical parent grouping and final observations.

### B. Hoist immutable PCM conversion

Convert PCM16 to float64 once before the resolution/frame loops and slice the
same values thereafter. Integer values are exactly representable in float64
and the source is not mutated. S11 encoding now states an explicit precondition:
the caller owns a stable PCM16 input and must not mutate it concurrently for
the duration of encoding. Concurrent source mutation was never a supported
deterministic behavior and remains outside the output-identity claim.

Risk: a hidden mutation or layout difference could affect frame construction.
Falsification: require identical dtype/shape/contiguity assumptions, exact
frame arrays at beginning/interior/end padding cases, and exact complete
observation records.

### C. Hoist DTFT constants and per-frame windowed samples

Reuse the same relative-sample vector, window normalization, and exact
`frame * window[:, None]` intermediate while retaining the existing
per-candidate exponential and `np.sum(..., axis=0)` call.

Risk: changing expression grouping, memory layout, or reduction order can
change floating-point phase and downstream tie decisions. Batched BLAS,
matrix multiplication, alternate FFT interpolation, and reordered reductions
are explicitly excluded from an output-identical remediation.

Falsification: compare every complex DTFT result by exact array equality and
bit pattern over deterministic adversarial frames/frequencies before admitting
this candidate.

### D. Native/GPU batch, candidate pruning, or approximate phase

Potentially much faster, but cannot promise identical floating arithmetic,
ordering, or hypotheses. This is a later algorithm/performance generation, not
R-217 evidence remediation. **Rejected here.**

### E. Raise timeouts, skip cymbal, or make no change

Another timeout increase violates R-211. Skipping the item violates the frozen
19-item gate. No change leaves S12 unable to complete. **Rejected.**

## Proposed smallest coherent implementation

Use one mechanical generation with three strictly sequential checkpoints:

1. implement A only and run the complete internal-state identity gate;
2. only after A passes, implement B and rerun the same identity gate;
3. only after B passes, implement C exactly as written and rerun the gate.

No checkpoint may be masked by a later checkpoint. C must literally reuse
`weighted_frame = frame * window[:, None]`, the same `np.exp`, and the same
`np.sum(..., axis=0)` reduction. Batching, `@`, `einsum`, `out`, fast-math,
GPU, alternate FFT interpolation, and any changed reduction order are excluded.
If B or C fails exact identity, revert that checkpoint rather than adding a
tolerance. A-only is not the planned admission because B and C remove separate
measured redundant work needed for useful cymbal margin.

No public syntax, decoder, bitstream, RDO policy, search bound, tie-break,
metric, Opus option, timeout, RSS limit, disk limit, or comparison claim may
change.

## Admission and kill gates

1. Independent auditor gives written binary GO on this revision before any
   production-code change.
2. Before editing the analyzer, retain canonical byte-level fingerprints for
   every one of the seven focused cases, the full incumbent `ebu-claves` item,
   and deterministic active prefixes of both `ebu-claves` and `ebu-cymbal`.
   For each named input, fingerprint the complete
   `ComplexPartialObservationSet`: every integer and Boolean, every float's
   exact IEEE-754 bits, tuple/list/dict order, allocation report, candidate
   IDs, conflict groups and report field. Also fingerprint fixed graph inputs,
   edges, paths, selected path IDs, lowered lanes, every evaluated subset and
   the RDO ledger. A Truth fallback does not waive this requirement. The full
   incumbent cymbal item cannot finish inside the frozen ceiling, so its active
   prefix fingerprints plus the first-principles A/B/C transform proof are the
   explicit honest identity boundary.
3. After each of A, B and C separately, reproduce every internal fingerprint
   for every named input in gate 2. Focused unit tests also prove old/new
   conflict grouping identity at temporal and frequency boundaries. Any
   mismatch kills that checkpoint.
4. For B, exact float64 frames must match at start padding, interior and end
   padding under the stable-input precondition. For C, every complex DTFT value
   must match by real/imaginary IEEE-754 bits. Any mismatch removes the
   checkpoint.
5. All seven focused S11 cases reproduce selected payload SHA-256, decoded PCM
   SHA-256, selected bytes/kind, complete lane/path/subset/RDO evidence and
   parser evidence.
6. `ebu-claves` reproduces payload SHA-256
   `9156b28ec67b25c6fc222a52d74431e9cf656f67b7bc01409e94ff4e601927dd`
   and decoded raw PCM16 SHA-256
   `32a3e399fd6b747aa14f372f1d1447b93290e133cce99e888fba17eb2f6fb96e`
   (retained WAV SHA-256
   `5f3faea4de8c34dd1ee39092e78fce5d075115bb52ebc8215c2a5bfb2fdea596`)
   in at most 475 seconds. More than 475 seconds is remediation failure.
7. An isolated `ebu-cymbal` run at or below 600 seconds passes the remediation
   runtime gate. More than 600 seconds fails remediation; more than 900 also
   trips the unchanged hard timeout.
8. Every real-item checkpoint records peak RSS and temporary/retained disk.
   The existing 8 GiB RSS and 2 GiB per-item disk ceilings must not increase,
   and no resource or fail-closed behavior may regress. The claves reference
   peak RSS is 777,949,184 bytes and retained item size is 4,693,898 bytes;
   deltas must be reported even when within the frozen ceilings.
9. A deterministic repeat of the changed analyzer path must reproduce bytes
   and PCM. Only then may the complete long-first 19-item R-217 run restart
   under a new run identity.
10. R-217 compares only current Resonith with the fixed Opus anchor. No Opus
   frontier search or preceding-Resonith column is reintroduced.

Partial Mozart and claves comparison evidence remains diagnostic until all 19
atomic receipts and the aggregate report pass. S13 remains blocked.

## Closeout evidence amendment after independent audit

The independent closeout audit returned **NO-GO** on the resource-evidence
contract even though all semantic identity, runtime, hash and focused-test
checks passed. The historical baseline/A/B/C real-item JSON files did not
record externally measured disk high-water values, and the later C-repeat
helper asserted `temporary_disk_bytes = 0` instead of measuring it. Those
fields must not be used as resource evidence.

Repeating A and B solely to reconstruct missing resource telemetry would add
about seven minutes of computation without testing a live admission choice.
A and B were sequential proof checkpoints, not separately retained codec
generations. Their exact internal, payload and PCM identities remain valid,
but their resource admission is explicitly withdrawn. Only final C is a live
admission candidate. This amendment supersedes original gate 8 only for the
missing historical A/B resource admission; final C retains every original
runtime, RSS, disk, identity and repeat ceiling.

Before final C can close, a new parent process must run isolated full
`ebu-claves` and `ebu-cymbal` C repeats. On Windows it must create each child
suspended, assign it before resume to a Job Object with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and active-process limit 1, then retain
all process/job handles through postflight. This enforces rather than merely
polls the no-descendant contract. The parent must sample the following at most
every 25 milliseconds:

1. child peak working set obtained from the operating system;
2. staging-tree byte high-water, including the output receipt while it is
   created;
3. staging bytes before launch and after child exit;
4. wall time, child exit code, stdout and stderr;
5. the exact argv vector, with `shell=False`, and SHA-256 identities of the
   Python executable, resource gate, identity helper, analyzer, predictor,
   native core, source file and source PCM both before launch and after exit.

Every run receives a fresh empty resolved staging root on `G:`. Every path from
that root to every monitored or retained file must be contained and reparse-
free. Staging measurement includes the final child JSON and the parent receipt;
the receipt records prelaunch, sampled high-water and postflight bytes. stdout
and stderr must be drained into separately bounded buffers so the child cannot
deadlock or consume unbounded parent memory.

Any Job/process/memory API failure, RSS above 8 GiB, staging high-water above
2 GiB, timeout above 600 seconds, nonzero child exit, descendant creation,
path/reparse violation, bounded-output overflow, or pre/post hash mismatch
fails closed. A normally signaled process observed through its retained handle
is completion, not unreadability; its final peak value and exit code must still
be queried. The helper's constant temporary-disk field must be removed or
explicitly made non-authoritative; only the parent receipt is resource
evidence.

Final C authorities are frozen as follows:

- `ebu-claves.wav`: source-file SHA-256
  `9069b02a7bf39a67c36f634aef759d79ad63241b8b709d08b12f8a6a043959df`,
  source-PCM SHA-256
  `1a8b6faffd774da205898a453deb3fa9d8e42c4da5e20d05aaac2a05e26cd65b`,
  internal SHA-256
  `79c11ca6b160d80330c30944e82d59207b8b7e4157d5984d3b7826f019a34a2b`,
  selected-payload SHA-256
  `9156b28ec67b25c6fc222a52d74431e9cf656f67b7bc01409e94ff4e601927dd`,
  decoded-PCM SHA-256
  `32a3e399fd6b747aa14f372f1d1447b93290e133cce99e888fba17eb2f6fb96e`;
- `ebu-cymbal.wav`: source-file SHA-256
  `4e5fed73eea73f72b9b227591a9a586dbd664d762497aa6a9457920571447b42`,
  source-PCM SHA-256
  `a9513b354efa40700c811f9fae8122f4a1a16196d849f684281263b2bdffd8cd`,
  internal SHA-256
  `30c5bb7d38c254a3ae9159c9377a0e6f132aaf5d4c7ea33ccaba5a6a6d29c34c`,
  selected-payload SHA-256
  `1f149b8ca110f17782b673a9cb7c84903b37b094ccd8301e88ef41bc4265fe5b`,
  decoded-PCM SHA-256
  `782f7cedf6fa10bd4fa5600c605c086e2edca18fd7528706e6d036cb239ae9cb`.

The old R-217 controller also cannot be reused after C: it correctly pins Git
revision `7e2726789ca980177a32e6b36cfcd9f1d90b5463`, rejects a dirty imported
implementation, and does not include `complex_partial_analyzer.py` in its run
identity. After R-218 closes, the selected R-218 files must be committed as one
immutable source revision. A new separately audited direct-comparison run
identity must explicitly hash the analyzer and update only the frozen source
revision and identity material. It must retain the same one-point official
Opus 1.6.1 anchor and all comparison, time and resource bounds. Bypassing the
dirty-tree gate or mutating an existing R-217 run is forbidden.

This amendment authorizes only audit-control implementation after a fresh
written auditor GO. It does not authorize a codec change, another Opus search,
a full corpus run, promotion or a compression claim.
