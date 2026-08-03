# R-267 S15 accepted-S12 handoff

Date: 2026-08-03

Status: **DUAL-REVIEWED STATIC HANDOFF; THREE-FILE RESTORE ONLY**

## Problem and objective

R-263 Run 1 terminally failed before tests. R-253 through R-263 therefore
remain negative evidence, but the output-identical R-253 LPC hoist and its
evidence harness still occupy the active oracle, test and gate files on the
published quarantine branch.

The objective is to start a genuinely new S15 hypothesis from the last accepted
S12 behavior without rewriting or deleting negative history. The complete cost
is active-byte identity, preservation of evidence, risk to unrelated dirty
files, repository clarity and future authority reachability. No codec quality,
bitrate or performance claim is made by this handoff.

## Frozen baseline

Commit `d70d73d` published the R-250 pre-change evidence. Commit `20de483`
added only R-253/R-254 planning documents; `git diff d70d73d 20de483` is empty
for the three active files. Therefore `20de483` is used as the convenient exact
accepted-S12 byte source:

- `reference/maf_p0/maf_source_filter_oracle.py`:
  `8a2f27e4357146edd0c1840268ec74bee3b59e43e6ca75a2d18902ef7d325007`;
- `tests/test_maf_source_filter_oracle.py`:
  `75e394bf1e6da57ce692a7747735c51c80559bb3acacb70be88226e057624483`;
- `experiments/r232_s15_source_filter_gate.py`:
  `53af4e1f85341b6d29661003d7e18144d40cc2cf64679463c2da9f20f738670e`.

The handoff branch starts at the immutable published R-266 quarantine commit
`aa25637b78b0b71e79b27168495d427eadb8ecac`.

## Alternatives and falsification

### New worktree at `20de483`

This gives the strongest filesystem isolation, but splits the canonical
`G:\Resonith` workspace, requires selectively transplanting historical
documentation and makes later synchronization easier to misunderstand. It is
safe but unnecessarily operationally complex for three exact tracked files.

### Exact three-file restore on a new branch

This preserves the published quarantine commit, changes only the reachable
oracle/test/gate surface and leaves all documents and fixtures as inert
history. Its principal risk is accidentally retaining a dependency on an
unadmitted bootstrap, probe or authority. The transaction therefore includes
an explicit forbidden-reference scan and requires every future S15 authority
to exclude R253-R266 evidence executables.

### Keep current bytes and label them inactive

Rejected. Documentation cannot change imported behavior or prevent a future
measurement from using the unadmitted hoist.

## Independent review resolution

One auditor preferred a separate worktree because unadmitted research scripts
remain stored under `experiments/`. The other approved the exact three-file
restore if the active files have no reference to those scripts and the new
authority excludes them. Both rejected label-only inactivation and agreed on
the exact target hashes.

The selected three-file transaction resolves the disagreement by defining
*active* as the reachable oracle/test/gate closure, not every preserved research
file in repository history. Stored R253-R266 executables remain quarantine
evidence and must not enter a new runner, import closure or authority.

## Transaction and kill gate

Before change, tracked index and worktree were clean. The unrelated untracked
inventory was frozen as 102 paths, 3,815,069 bytes and aggregate SHA-256
`67b216e41cfe3e1b6e06993fa4073ad512764042128ffd2be6655ce79c488bd6`.

The transaction must:

1. restore exactly the three files above from `20de483` through `apply_patch`;
2. produce exactly their frozen SHA-256 values;
3. show exactly those three tracked active paths changed before documentation;
4. find no R253-R266 authority, fixture, bootstrap or probe reference in the
   restored active files;
5. preserve every tracked R253-R266 evidence path outside the three active
   files byte-identically to `aa25637`;
6. preserve the complete untracked path/size/hash inventory; and
7. commit the restore separately from any new S15 algorithm.

Any target-hash mismatch, extra changed/deleted active path, evidence drift,
untracked-inventory change or retained forbidden dependency is terminal for
this handoff and blocks commit. This is an exact accepted-byte restoration, not
an algorithm improvement, so it does not trigger R-198 or an audio/Opus run.
