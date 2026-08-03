# R-203 Candidate-Rich Post-Implementation Audit

Date: 2026-07-29

Status: **INDEPENDENT NO-GO; BOUNDED REMEDIATION REQUIRED**

Scope: candidate-rich test and evidence infrastructure only

## Reproduced positive evidence

- the frozen supplement contract hash matches
  `572db682e345bef4f448f049674d2edd62cfe972fc58a1a2ab36c2dd2459dd73`;
- the generated corpus contains exactly 288 cases;
- its topology distribution is `36/144/36/36/36`;
- the saved JSONL SHA-256 is
  `fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7`;
- the corpus contains 936 edges, 1,620 paths and 3,924 entries;
- Authority B has no import or call dependency on the native ABI or the
  R-190/R-191 edge/path oracle.

These facts preserve the corpus as a useful finite test input. They do not
admit it as complete evidence.

## Blocking findings

### Complete typed parity is missing

The replay reduces native output to high-level path records and a report
dictionary. It does not compare every raw path/entry header, offset, reserved
word, report header, termination field, count, resource field or all 22 event
families. Preflight/fill identity is therefore incomplete.

### Authority B is not yet an independent selection judge

Authority B enumerates paths, conflicts and conflict-free subsets, but the
generator does not require its exact conflict relations to equal Authority A
and does not independently maximize the frozen score/tie law over those
subsets. A shared selection defect in Authority A and native could therefore
pass.

### Inventory and replay are not fail-closed

The emitted inventory does not bind every required source and result hash.
The replay accepts an arbitrary or truncated corpus, exposes `--max-cases`,
does not require the frozen schema/count/SHA/contract, and does not compare the
generator inventory SHA with the consumed SHA before success.

### Toolchain and resource replay is incomplete

The executable candidate-rich replay runs in one Linux bridge job, rather
than every admitted toolchain job. Resource fields are reported but not
asserted against the frozen CPU/device laws, and cross-toolchain semantic
hashes are not collected into one immutable comparison.

## Rejected shortcuts

- Keeping the current gate because the corpus itself is deterministic is
  rejected: deterministic incomplete evidence remains incomplete.
- Treating Authority B as sufficient because it enumerates subsets is
  rejected: it must independently judge the selected optimum.
- Using native output to populate the inventory is rejected as circular.
- Editing the frozen contract or changing the 288-case JSONL to hide a gate
  defect is rejected.
- Running one compiler and labelling the result cross-platform is rejected.

## Bounded remediation

1. expose canonical raw logical ABI records and complete preflight/fill
   reports from the bridge;
2. compare every typed field, all 22 event counts, counts, resources,
   fingerprints, payload bytes and repeated calls;
3. make Authority B derive exact conflict relations and independently select
   the maximum score with the frozen path-ID tie law;
4. emit one immutable inventory binding both contracts, generator, Authority
   A, Authority B, runner, JSONL and expected semantic hashes;
5. make replay fail closed on schema, ID, count, SHA and inventory mismatch;
6. run identical replay in GCC, Clang, MSVC, Apple and Android jobs and compare
   canonical semantic hashes before final admission.

## Kill gate

Any typed-field, event, resource, conflict, selected-set, source-hash,
inventory, corpus, replay or toolchain mismatch is unconditional NO-GO.

The remediation remains test/evidence infrastructure and does not trigger the
registered-music/Opus gate. Any production analyzer, encoder, syntax, decoded
PCM or player behavior change remains outside this exception.
