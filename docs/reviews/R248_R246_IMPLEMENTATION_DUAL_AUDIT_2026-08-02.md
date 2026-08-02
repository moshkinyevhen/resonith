# R-248 R-246 implementation dual-audit record

Date: 2026-08-02

Status: **DUAL GO FOR AUTHORITY FREEZE; WORKLOAD EXECUTION STILL NO-GO**

## Scope

Two independent auditors reviewed the R-246 Phase-A controller implementation
without editing files or executing the controller, workers, codec or oracle.
This record authorizes only creation of the immutable R-246 authority. It does
not authorize an evidence workload.

## Rejected implementations

- Runner SHA-256
  `2a0aa4381a3f7913d776c8e9cb022b0fe8925172d73f5bac79c811ff62674673`
  was rejected for postownership failure escape, incomplete retained profile
  closure, partial receipt readback, request TOCTOU and weak report semantics.
- Runner SHA-256
  `4c91a18a034f210fea6045c3bcd066b57130a4e61cf6d5c40bd90605f940ba68`
  was rejected because the global deadline was not propagated into an active
  worker, the executing runner path was not bound, and identity types were not
  fully constrained.
- Runner SHA-256
  `3eaf86f04f30fc70b1b0374ebbb6793f2312dfc9378a7c485f917d94ced33c23`
  was rejected because its diagnostic counter map was neither exact nor
  independently reconstructed from the retained canonical encoder report.

No rejected runner was executed.

## Final reviewed implementation

Both auditors returned binary GO for provenance commit for runner SHA-256
`0ad570dcbb081fd88cbfe8a8957cb8d16cfa217000f85b72b6aaacdf431e46b9`,
exactly 640 physical lines and 48,794 bytes. It remains within the frozen
640-line and 64-KiB bounds. The final review confirmed:

- immediate postownership failure handling;
- suspended child to bounded Windows Job assignment before resume;
- effective worker wall limit bounded by remaining controller time;
- exact authority, Git, source, base closure and executing-runner path;
- read-once canonical request plus immutable consumed-marker closure;
- exact retained tree, size/hash identity and canonical receipt closure;
- recomputed timing/profile/golden semantics and report-derived exact counters;
- bounded failure publication and atomic terminal success publication.

## Remaining gate

The authority must bind the published Git commit, exact runner and document
hashes, base authority closure, runtime, native core, source, configuration,
budgets and all terminal paths. Both auditors must then return binary GO over
the exact runner-authority pair before the one authorized Phase-A invocation.

