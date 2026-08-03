# R-274 S17 Implementation-Closure Remediation

Date: 2026-08-03  
Status: **V2 PREFLIGHT DELTA; IMPLEMENTATION BLOCKED PENDING INDEPENDENT GO**

## Problem and frozen objective

The first static implementation audit of the R-271 V6 gate returned NO-GO on
gate SHA-256
`15f78a2e97e6e5cfeb53fd2513b6cf0b2b56699ad58c8d19b19c464bf3a97996`.
No long control, registered audio, or Opus execution occurred.

The objective is unchanged: test whether one anonymous persistent inharmonic
modal Basis plus accepted-S12 Truth can reduce complete bytes by at least ten
percent on the auditor-seeded holdout without exceeding any frozen decoded
quality tolerance. This remediation may only make the already audited search,
decoder attribution, selector, and failure behavior executable as specified.
It may not add a codec mode, relax a predicate, increase a resource ceiling,
or create another evidence run.

## Alternatives considered

1. **Run the existing gate and treat defects as reporting issues — rejected.**
   Candidate retention is incomplete and selector ties are not reproducible;
   the result would not test V6.
2. **Freeze the complete import tree of `persistent_partial_field.py` —
   rejected.** The S17 proposer uses only its manifest constants and fixed-row
   conversion, while importing that module also loads unrelated CBF, typed,
   Truth-candidate, and lapped encoder code. Binding that accidental graph
   would enlarge the trusted surface without improving the hypothesis.
3. **Isolate the minimal PCM proposer dependencies — selected.** Reproduce the
   already frozen fixed-row conversion directly inside the S17 gate, construct
   the unchanged observer/path manifests there, and remove the
   `persistent_partial_field.py` import. The reachable proposer closure then
   consists of the gate's declared proposer functions, the frozen complex
   observer, the frozen native/Python path graph, the scalar IMF/IMU model, and
   the exact external SciPy routines used by the observer.
4. **Keep the 32-seed optimization — rejected.** It is absent from V6 and can
   hide a qualifying path. Every one of the at most 64 selected paths must act
   as a seed.
5. **Generate one greedy cluster from every retained candidate — rejected.**
   It is order-duplicative and violates the maximum-eight-Basis stage.
6. **One canonical first-fit clustering pass — selected.** It is finite,
   deterministic, uses every retained candidate, creates at most eight Basis
   clusters, and preserves the subsequent proxy ranking of at most sixteen
   complete candidates.
7. **Use wall time as the selector's decode-cost tie — rejected.** It is not
   deterministic across hosts.
8. **Use exact declared integer work scores derived from parser extents —
   selected.** These are reproducible from the complete pack and do not depend
   on benchmark noise.
9. **Run more controls to compensate for uncertainty — rejected.** Static
   closure must be correct before the single already authorized long gate.

## Exact remediation

### 1. Minimal proposer closure

The gate removes its import of `persistent_partial_field.py`. It locally
performs the frozen conversion from aggregate, phase-usable, locally
resolvable observer rows to fixed path-graph observations. Frequency, phase,
uncertainty, ownership, flags, node value, sort order, and manifest bounds
remain byte-identical to the accepted helper. The three path-family caps use
the inherited exact formula `min(128, maximum_path_records // 3)`, hence 85
for the frozen maximum of 256; no hard-coded 128 replacement is permitted.

One inherited field conversion is deliberately corrected because V6 assigns
it a different physical unit. The observer's
`normalized_detector_amplitude` is channel-normalized but remains in PCM
amplitude units. V6 `normalized_amplitude_q16` is a full-scale ratio. The only
dimensionally valid conversion is

`round_even(normalized_detector_amplitude * 65536 / 32768)`, equivalently
`round_even(normalized_detector_amplitude * 2)`.

Values outside `[1,65536]` are rejected rather than clamped. Reusing the
inherited `amplitude * 2^16` conversion is forbidden: it makes every observed
amplitude above one PCM unit fail V6's full-scale bound and prevents the
holdout proposer from emitting a candidate.

The source-closure receipt lists and hashes every local module containing a
callable reachable from the proposer. It additionally records:

- Python executable hash and version;
- NumPy version;
- SciPy version;
- SHA-256 of the loaded `scipy.signal._peak_finding`,
  `scipy.signal._peak_finding_utils`, and `scipy.signal.windows._windows`
  implementation files;
- native Core and compiler identities.

Before audio, the gate verifies those identities and scans the complete
declared proposer closure for the frozen holdout/freezer/seed tokens. Any
mismatch is a gate failure before P0.

### 2. Complete enumeration and bounded clustering

All at most 64 selected paths remain in canonical path-ID order and every path
acts as a seed. Every size-3-through-16 prefix of its canonical neighborhood is
formed and deduplicated. All admissible prefix candidates are ranked by
`(quantized_fit_error, -support, -mode_count, path_ids)` before retaining at
most 128.

The retained sequence is processed once in that same canonical order. A
candidate joins the first existing Basis cluster for which all of the
following hold:

- the cluster has fewer than 16 instances;
- path IDs are disjoint;
- mode counts agree and every corresponding Q20 ratio differs by at most two;
- the folded phase predicate below passes for every mode;
- packing and exact integer rendering succeed without clipping; and
- the shared-Basis model PCM equals the checked sum of the member model PCM.

If no cluster accepts it and fewer than eight clusters exist, it starts the
next cluster. Otherwise it remains represented only by its original
single-instance candidate. The complete-candidate proxy pool is the at most
128 retained single-instance packs plus only final cluster packs containing at
least two instances. The combined pool is deduplicated by exact pack bytes and
SHA-256 before ranking. It is ranked exactly by `(proxy_residual_SSE,
metadata_bytes, mode_count, pack_SHA256)` and only its first sixteen distinct
candidates reach Truth encoding.

### 3. Folded phase admission

For a candidate mode at the common support start, phase uncertainty is the
exact row's `phase_uncertainty_u31`; when the start lies between two rows, it
is the greater of the two bracketing uncertainties. Missing brackets reject
the original candidate.

For a proposed later instance, mode-zero defines the modulo-Q32 time shift.
For each mode, compute

`folded = basis_phase_q32 + round_even(time_shift_q32 * ratio_q20 / 2^20)`.

Take the signed shortest modulo-Q32 delta from `folded` to the candidate's
first-knot phase. The exact half-turn tie rejects sharing. The absolute delta
must not exceed that candidate mode's carried `phase_uncertainty_u31`; otherwise
the candidate starts a separate Basis when capacity permits or stays single.

### 4. Fail-closed capacity behavior

A profile/work/capacity failure at any point from observation through complete
IMF/IMU inspection, render, Truth inspection, workspace allocation, or native
Truth decode returns the structured byte-identical accepted-S12 fallback.
Model clipping, phase mismatch, and non-profitable candidates remain ordinary
candidate rejections. A required holdout fallback is a holdout failure. N1 may
pass with the byte-identical fallback as already frozen.

This includes `MemoryError` raised during observer/proposer execution, not only
during Truth work. Native IMF/IMU inspection returns `PROFILE_BOUND`, never
`MALFORMED`, when otherwise valid declared `mode_samples` exceeds the frozen
150,000,000 work ceiling. Extent/count disagreement remains `MALFORMED`.

### 5. Reproducible selector fields

For one complete candidate define:

- `model_decode_operations = 2 * (mode_samples + sample_count)`, the exact
  two-pass native model-render budget consumed by the admitted renderer;
- `truth_decode_operations = transform_frame_count * half_window * band_count
  + coefficient_elements + overlap_elements + output_elements`, a frozen
  deterministic LPF1 work score derived from actual native inspection;
- `decode_operations = model_decode_operations + truth_decode_operations`;
- `model_preroll_samples = max(instance_duration)`;
- `truth_preroll_samples = frame_count`, because the current accepted-S12 LPF1
  decoder consumes the complete non-indexed Truth stream and no bounded
  entropy/parser seek contract has been evidenced;
- `preroll_samples = max(model_preroll_samples, truth_preroll_samples)`.

These are selector accounting coordinates, not measured CPU instructions.
The final eligible selector remains exactly `(complete_bytes,
decode_operations, preroll_samples, mode_count, pack_SHA256)`.

## Falsifiable prediction and kill gate

The repaired static implementation must independently audit GO without adding
another control or relaxing V6. After source/binary closure and the one
auditor-seeded holdout creation, exactly one long gate is permitted. Any P0,
holdout, identity, resource, transaction, or required model-on failure ends
S17 and suppresses N1, N2-N5, EBU, S18, and Opus. A pass alone authorizes the
remaining frozen focused completion and then one S18 registered comparison.

## Minimal verification plan

Before the long gate, verification is limited to syntax/static review, the
already required native focused conformance executable, and independent audit
of exact source hashes. Closed alias/order and full-Truth decode predicates are
not expanded with new tests. The final P0 is executed once inside the sealed
long gate; no standalone repeat is permitted.
