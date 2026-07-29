# Resonith Work-Session Checkpoint — 2026-07-29

## Stop reason

The project owner requested an immediate safe stop so that the workstation
could be shut down. No new implementation work may start from this checkpoint
until the next session.

## Process state

- No running Resonith or Orkela build, test, encoder, decoder, Python, CMake,
  Git, or player process remained at the stop boundary.
- The process inspection matched only the PowerShell process performing the
  inspection itself.
- No process required termination.

## Plan state

- The canonical development plan remains **exactly 63 steps**.
- Steps 1 through 8 are complete.
- Step 9 remains active and incomplete.
- Steps 10 through 63 remain pending.
- The plan must not be shortened, regrouped, renumbered, or removed when work
  resumes.
- The normative dependency order remains in
  `docs/20_LSPF_MASTER_EXECUTION_PLAN.md`.

## Repository state

- Repository: `G:\Resonith`
- Branch: `codex/maf-r193-alpha`
- HEAD: `8edadb3 Fix GCC shadow warning in ABI matrix`
- Working tree contains two modified tracked files:
  - `.github/workflows/mobile.yml`
  - `native/tests/partial_graph_test.cpp`
- `git diff --check` passes.
- A user-owned untracked development-plan directory is present. It must not be
  staged, edited, moved, or deleted.

## Exact uncommitted work

### Coverage workflow

`.github/workflows/mobile.yml` maps `llvm-cov` to the single
`resonith_partial_graph_test` executable. The merged profile still aggregates
all executions. This avoids duplicate coverage mappings that previously
produced false zero counters and LLVM counter underflow.

SHA-256:

`E2B20ED869AF7864EABD1938FC2174468552F39D1E7A1BC59E2B59AEA194ED07`

### Partial-graph ABI tests

`native/tests/partial_graph_test.cpp` adds:

- v3 null-observation/count-zero validation;
- v3 null-edge/count-zero validation;
- a valid-header pairwise-overlap witness;
- an unfinished output-staging high-water witness for the reachable
  line-7861 guard.

SHA-256:

`E61F26165F571CC7790B768BAF10320FA19707AED30059CED52EBF4A077C4FDF`

The staging witness is intentionally uncommitted because it does not pass yet.
Its current protected reservoir is capped by
`stage_path.top_k_protected = 1U`, so it emits only one path and cannot make
staging memory exceed preflight historical memory.

## Resume audit correction

The independent auditor rejected the original single-field resume action.
All 514-observation candidates have a 440 Hz median and enter one protected
band, where `protected_paths_per_band = 1` discards all but one before
`top_k_protected` is applied.

The 128-path corrected experiment produced its exact counts but failed because
historical peak remained above staging. The independently approved final
bounded experiment uses a 4,094-observation shared prefix, 16 intermediate
branches, 256 terminal paths of length 4,096 and exactly 1,048,576 entries.
Both protected limits are 256. Admission requires
`historical_peak < 100,732,928`, exact-peak reproducibility, `PROFILE_BOUND`,
unchanged payload, focused runtime no greater than 10 seconds and RSS no
greater than 512 MiB. Failure kills the fixture without another expansion
unless allocation-ordinal component evidence justifies one.

The resumed experiment failed that gate despite exact counts:
historical peak 116,675,808 bytes versus staging 100,732,928, runtime
1.702 seconds. The final independent allocation audit proved the public
wrapper branch unreachable in the current 64-bit managed implementation:
`historical_peak >= 108E + 272P`, while the later staging expression is only
`96E + 272P`. No larger witness, manufactured failpoint, or coverage-driven
allocation change is authorized. The approved correction is a pure checked
stage-budget helper with direct boundary tests plus a strict source-hash-bound
semantic allowlist for the unreachable wrapper outcome.

After that focused gate, re-run isolated local LLVM coverage, implement the
strict machine-readable semantic allowlist and GitHub coverage gate, and
commit/push only after the independent Step-9 post-audit passes.

## Evidence still pending for Step 9

- direct overflow/exact-limit/over-limit tests of the pure staging-budget
  helper: passed;
- refreshed isolated LLVM coverage: 96.1320% adjusted lines and 92.4779%
  adjusted branches, passed;
- exact semantic branch/line contract with source/helper/proof hashes and
  stale/new-entry rejection: passed;
- Clang and GCC warnings-as-errors focused gates: 5/5 each, passed;
- GitHub Actions platform results;
- independent local-design audit: GO with zero blockers; final same-revision
  platform evidence remains pending;
- English result record and decision-log update.

No codec algorithm generation was changed in this session segment, so the
R-198 full music/Opus corpus gate was not triggered.
