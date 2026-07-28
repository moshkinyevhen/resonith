# R-191 Post-Implementation Red-Team Review

Date: 2026-07-28  
Verdict: **NO-GO for predictor admission**

The edge ABI may remain frozen as an analyzer record. Path ABI v1 remains a
quarantined experiment and is not a release contract.

## Confirmed blockers

| Blocker | Falsification | Consequence |
|---|---|---|
| Edge records are trusted | Backward and falsified-delta edges were accepted and produced paths | A caller can inject graph relations that the declared enumerator never generated |
| Resource bounds are incomplete | Historical copied vectors, maps, pair sets, sorting, and fingerprint temporaries are not included in `host_bytes`; work is often charged after work | A valid manifest does not bound actual memory or time |
| Score domains are mixed | Second-order dimensionless curvature is added to `provisional_program_cost_q8` | The field can no longer be interpreted even as a provisional coding-cost estimate |
| Pruning is invisible | The pruning flag is never set for K/top-K discards and discard counts are absent | A truncated search can be reported as complete |
| Exact-small saturates | Set totals silently saturate before lexicographic tie-breaking | Different objective totals can select as a false tie |
| Irregular-gap uncertainty is biased | The denominator is `u0+u1+u2` regardless of `dt12/dt01` | Long extrapolation after a short interval is under-normalized |
| Kill gates are incomplete | Only small CPU graphs and one nine-edge GPU fixture were run | The published evidence does not establish the declared bounds or portability |

## Alternatives considered

### Edge integrity

- **Check only center and frequency deltas:** rejected. It still accepts an
  undeclared gap, cycle, neighbor, or forged score.
- **Trust an input hash:** rejected. The hash is diagnostic, the caller owns
  both data and expected value, and it cannot prove membership in the declared
  finite graph.
- **Re-enumerate and rescore the canonical edge stream:** retained. The path
  call receives the resolution table and compares every supplied edge with the
  shared deterministic enumerator without materializing a second graph.

### Bounded search

- **Lower current limits:** rejected. Smaller numbers do not make uncounted
  allocations or post-charged work bounded.
- **Keep complete vectors but add estimated byte formulas:** rejected.
  Nested vectors and ordered containers have implementation-dependent
  allocations and every extension still copies the complete history.
- **Backpointer arena plus metered allocation/work:** retained. Each state is
  fixed-size and names its parent; a counting memory resource rejects the
  allocation that would exceed peak live bytes, while a work meter is consumed
  before the corresponding operation.

### Exact-small arithmetic

- **Keep saturation and report it:** rejected. Reporting does not restore the
  ordering that saturation destroyed.
- **Portable two-limb arbitrary precision in the production selector:**
  unnecessary for the declared small set.
- **Checked unsaturated totals with manifest-domain proof:** retained. A
  candidate set that cannot be summed exactly returns a profile bound. An
  independent Python integer brute-force oracle remains the test authority.

### Irregular-gap uncertainty

For

\[
r=f_2-(1+q)f_1+qf_0,\qquad q=dt_{12}/dt_{01},
\]

independent bounded observation errors give the conservative L1 scale

\[
u_r=u_2+(1+q)u_1+qu_0.
\]

The implementation will use checked integer ceiling scales for the two
`q`-weighted terms. The fixed sigma floor is applied after propagation.

## Accepted remediation package for audit

1. Factor edge generation into one streaming deterministic enumerator used by
   count, fill, CUDA parity fixtures, and path-input validation.
2. Add the resolution table to the experimental path call and require the
   supplied edge array to equal the complete canonical declared stream.
3. Replace history-copying states with fixed arena nodes and parent
   backpointers; index retained terminal states without scanning all history.
4. Meter peak live allocator bytes and consume deterministic work before each
   charged operation.
5. Advance the experimental path report to v2 with explicit retained,
   deduplicated, discarded, family-pruned, and saturation counters.
6. Remove second-order curvature from provisional-program accumulation.
7. Use ratio-scaled irregular-gap uncertainty and exact integer parity.
8. Prohibit saturation in exact-small totals and compare against a separate
   arbitrary-precision brute-force oracle.
9. Add transactional canaries, malformed-edge mutations, every resource
   boundary, ABI offsets, randomized scalar CPU/CUDA parity, and the four
   platform compile gates.

## Independent pre-code verdict and mandatory clarifications

The independent follow-up auditor returned a **conditional GO to begin
analyzer remediation only**. The following clarifications are part of the
accepted package, not optional implementation details:

- the supplied edge array is required in exact increasing `candidate_id`
  order. Observation arrays may be permuted. Missing, extra, duplicated,
  permuted, or field-mutated edges are rejected by field-for-field comparison
  with the one shared canonical enumerator;
- resolutions, observation/edge counts, canonical ordering policy, graph
  manifest, and path manifest all enter the preflight fingerprint;
- count and fill both stream. Fill completes input, fingerprint, exact count,
  and capacity validation before writing its first semantic record;
- each arena node uses an integer parent index and an explicit sentinel.
  Indices, parents, terminal keys, and maximum representable nodes are checked.
  A secondary `current_observation -> terminal bucket` index prevents scans of
  historical states;
- immutable nodes reachable from neither a retained terminal bucket nor a
  family reservoir are released by reference count. Reusable slots carry no
  semantic identity; canonical identity is reconstructed collision-free from
  observation and incoming-edge sequences;
- path reconstruction, median calculation, ownership construction, and
  canonical identity comparison are metered operations;
- the memory report is named `peak_live_managed_bytes`. It covers every
  dynamic project-controlled allocation through one counting PMR resource,
  but does not claim to measure allocator bookkeeping or process RSS;
- sort work is precharged by a published data-size bound independent of the
  host standard library. Pair tests charge `N*(N-1)/2`, not only discovered
  conflicts. Bucket scans, state creation, traversal, and output
  reconstruction are charged before execution;
- declared profile exhaustion and environmental allocation failure have
  distinct statuses and report termination;
- the experimental path function and records advance to ABI v2 under a new
  symbol. A v2 function never interprets a v1-sized record;
- generated, duplicate, terminal-retained, K-discarded, family-presented,
  family-discarded, deduplicated-output, and bound-rejected counts have
  separate fields. Ordinary K/top-K loss sets `PRUNED` even when the bounded
  run otherwise completes;
- exact-small uses checked, unsaturated stored-objective totals. Overflow is a
  profile bound. Equal totals compare sorted full canonical path identities,
  never output ranks;
- frequency residual uncertainty version 2 is the L1 proxy
  `u2 + u1 + ceil(dt12*(u0+u1)/dt01)`, evaluated by checked
  quotient/remainder arithmetic. The observation fields are estimator
  uncertainty proxies, not asserted statistical absolute radii. Amplitude
  curvature remains explicitly a weighted heuristic until its uncertainty is
  separately propagated.

Additional required tests cover every edge-field mutation, missing/extra and
permuted edges, work/memory `limit-1/limit/limit+1`, injected allocation
failure, deep and reclaimed backpointer chains, parent/index exhaustion,
all-zero and stale fingerprints including resolution changes, exact-small
overflow/equal totals, shared-enumerator randomized CPU/CUDA parity, every
public C/C++ field offset, ASan/UBSan, malformed-input fuzzing, and
MSVC/Clang/GCC/Android/iOS compilation.

No predictor, bitstream syntax, compression claim, Opus comparison, or Orkela
release may consume path output until this package passes another independent
audit.
