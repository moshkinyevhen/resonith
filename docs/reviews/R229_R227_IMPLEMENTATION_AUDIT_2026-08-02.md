# R-229 R-227 implementation audit and bounded remediation

Date: 2026-08-02

Status: **INITIAL IMPLEMENTATION NO-GO; REMEDIATED CANDIDATE MUST BE COMMITTED
AND RE-AUDITED BEFORE LONG EXECUTION**

## Independent findings

The independent auditor reproduced the focused gate and returned NO-GO twice.
The final rejected snapshot had runner SHA-256
`4968387082287ccc3271103bcb5b38f1cde990aa641128bca186b413091a85e0`,
test SHA-256
`e9286cf0e0cfa874fb5ec9c4a76f5a6e1e97b1fc3a5d101d49ea3b680f95cd18`
and passed 16 focused tests in 22.62 seconds. Three blockers remained:

1. an arbitrary 64-character hexadecimal string could forge phase access;
2. the synthetic gate accepted any phase-position difference instead of the
   frozen every-thirtieth-placement innovations; and
3. runtime authority covered twelve selected modules but not the complete
   loaded-module inventory, while runner and test were absent from the claimed
   implementation commit.

Earlier findings concerning production S11 rejection, direct-Truth evidence,
tile ownership, placement caps, paired arms, byte closure, resources, atomic
publication and four-byte position attribution were cleared.

## Smallest coherent remediation

The candidate now uses a `PhaseEvidenceVault`. It owns the only raw phase
mapping, rejects reads before seal, and creates an unforgeable object-identity
capability only after the canonical eligibility manifest is atomically written,
flushed and returned with its exact file hash. Lowering and usability checks
accept the capability, not a string or raw dictionary.

The frozen 27,024-byte MFT1 positive control is now hashed, independently
parsed and decoded through the native Core. All 600 placements, alternating
frequency laws, one-past position recurrence and exact one-eighth-cycle jump
before every thirtieth placement are checked. A selected reset event counts as
a known detection only when its lane crosses a scheduled jump and its circular
phase delta is closer to the scheduled one-eighth turn than to zero. Aggregate
admission requires at least one crossing and correct classification of every
selected crossing; arbitrary estimator drift cannot satisfy the gate.

Every loaded Python module now contributes kind and origin, and every
file-backed module contributes SHA-256, before and after execution. The speech
metric dependency is preloaded so a legitimate lazy import cannot masquerade
as mid-run authority drift. A fresh-process diagnostic observed 974 modules
before and after synthetic native decode plus speech metrics, with exact
inventory equality.

The remediated focused gate passes 17/17 in 29.91 seconds. Its pre-commit
identities are runner SHA-256
`320307dc8fd0c9bead47fd2dd998734f17bbed232632be1615d121db3b02eef6`
and test SHA-256
`50153bfb914069493c5d5a93095f6e5a7ae9e24ecee7fc8ef3c106e3d89af3d9`.

## Remaining gate

Commit the exact runner, test and this audit record with explicit staging.
Then obtain a fresh independent GO that binds both file hashes to that commit.
The four long inputs remain NO-GO until that verdict. No syntax, decoder,
product version, Opus rerun, promotion or release is authorized.
