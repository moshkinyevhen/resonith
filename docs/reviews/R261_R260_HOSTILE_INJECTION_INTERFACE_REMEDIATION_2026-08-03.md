# R-261 R-260 hostile-injection interface remediation

Date: 2026-08-03

Status: **DRAFT; CODE AND EXECUTION NO-GO PENDING DUAL AUDIT**

## Frozen failure

The first R-260 focused Stage-0 invocation exited `1` after 23.43605 seconds.
No second invocation was attempted. The immutable evidence is:

- `artifacts/r260-s15-focused-admission-v1/run-1.stage-minus1.json`;
- stdout SHA-256
  `935ded1a69165316d4b263345dd7bfc0bd1a07e1914abc7e5b28c5ffd4a6bc23`;
- stderr SHA-256
  `226a2f33902cd8927a2679f316aa3f78e7c5f842582dfe1bb109d9e1c54dd5ca`;
- both exact Stage-0 and Stage-1 prefixes absent after exit.

The failure preceded test execution. The authority-bound AST gate correctly
rejected direct access to `sys.path_importer_cache` and `sys.path` in the test
source. The R-260 constructor mutants and positive witness introduced those
direct expressions, so the test module was rejected before import.

## Alternatives

### Weaken the AST gate

Rejected. Production-authorized source must not receive direct import-state
mutation rights merely so a hostile test can construct adversarial state.

### Hide the access in a dynamic string

Rejected for the constructor matrix. Existing subprocess mutants use dynamic
strings deliberately, but the direct constructor test can use the Guard's
already captured ownership references without creating another reflective
bypass.

### Use Guard-owned references

Selected. The test obtains the exact interpreter-owned mapping and path list
from `ACTIVE_GUARD.cache` and `ACTIVE_GUARD.path`. It mutates/restores those
objects transactionally while constructing a new `_Guard`. The production AST
rule remains unchanged; production bootstrap behavior remains unchanged.

The positive witness also reads `ACTIVE_GUARD.cache` and
`ACTIVE_GUARD.path`. The junction-backed alias test appends through the same
owned list and removes the entry in `finally`.

## Gate

Static audit must prove that the test source contains no direct blocked
`sys.path*` access, every mutation restores the exact original mapping/list,
and no production source changed. The next focused admission restarts as two
entirely new Stage-0 invocations with new prefixes. Any failure is terminal and
the second invocation is not attempted. R-261 authorizes no codec workload.
