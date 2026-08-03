# R-203 Dynamic Charge-Site Mutation Preflight

Date: 2026-07-29

Status: **INDEPENDENT NO-GO FOR IMPLEMENTATION; REVISED CONTRACT PENDING AUDIT**

Parent amendment: `R203-EVIDENCE-SPLIT-1`

Approved parent SHA-256:
`c9f736288e67f69622812149c2ab86e5f54439c9778bcf57068acd8b6585aa74`

Scope: test-only Class-B evidence for the seven dynamic non-`MEMORY_PAGE`
event counters

## Problem and measurable objective

Cross-toolchain equality can reproduce a shared omission. The current replay
compares and hashes the native 21-event non-memory vector, but it does not yet
prove that every dynamic charge site is inventoried, reachable, and capable of
making the gate fail when removed or reclassified.

The objective is a fail-closed, versioned proof that:

1. every production reference to the seven dynamic event counters has exactly
   one inventory record;
2. every helper invocation that can execute an inventoried accounting anchor
   has a frozen reachable witness;
3. exactly one remove mutant and one reclassify mutant per accounting anchor
   compile and are rejected by runtime evidence rather than by an unauthorized
   source hash;
4. production sources, headers, release objects, encoded bytes, and decoded
   PCM remain unchanged.

The complete cost includes manifest size, extraction/build time, 72 current
mutant builds, replay time, CI storage, false-positive maintenance, compiler
portability, and the risk of circular evidence.

## Frozen baseline

| Input | SHA-256 |
|---|---|
| `native/src/partial_graph.cpp` | `ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05` |
| `native/include/resonith/partial_graph.h` | `12733d20b54be6209455800f477bfce9b84951d74699972a646dc492b803d49e` |
| LLVM-MinGW `clang++` 22.1.8 | `a8b7a614eeadd9105f814be3701a7f312cda4cea51751b75b408c16100c94e85` |

The current textual discovery reports 36 dynamic-family references:

| Event | References |
|---|---:|
| `MERGE_COMPARE` | 1 |
| `MERGE_MOVE` | 2 |
| `LOOKUP` | 7 |
| `STATE` | 4 |
| `REFERENCE` | 9 |
| `SELECT` | 11 |
| `RECONSTRUCT` | 2 |

These counts are orientation evidence only. They are not accepted as a
completeness proof. Three merge accounting anchors serve ten separate
`stable_merge_sort_v1` invocation sites, and map/table helpers also serve
multiple operation instances.

## Alternatives considered

### A. Make no change

Rejected. Two toolchains can agree on the same omitted charge.

### B. Grep or line-number inventory

Rejected. Formatting, aliases, helper forwarding, macros, and source movement
can defeat it without changing semantics.

### C. Copy native accounting control flow into Python

Rejected. It creates a second translation of the implementation rather than an
independent test.

### D. Add runtime site IDs or mutation hooks to production

Rejected for this substep. A compiled-out hook still modifies production
source and requires a separate preflight, release-object identity evidence, and
possibly the complete R-198 comparison.

### E. Pinned Clang AST inventory plus isolated source mutants

Selected, subject to independent GO. Clang exposes source-accurate AST and
coverage data derived from the AST and preprocessor, allowing the test
infrastructure to reason about call structure without assigning line numbers
semantic authority. See the official
[Clang AST introduction](https://clang.llvm.org/docs/IntroductionToTheClangAST.html)
and
[source-based coverage documentation](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html).

## Test-only manifest

The versioned manifest SHALL bind:

- schema and amendment ID;
- approved parent-amendment SHA-256;
- production source/header SHA-256 values;
- pinned Clang binary/version/hash;
- normalized compile-command hash;
- normalized AST extraction schema/hash;
- ordinary and hostile witness-corpus hashes;
- every accounting anchor and every helper invocation.

Every accounting-anchor record SHALL contain:

- stable semantic site ID;
- enclosing function or template;
- normalized AST-subtree hash and exact source span;
- event family;
- operation type: `emit`, `reserve`, `cancel`, or `consume`;
- helper invocation/instantiation IDs;
- immutable ordinary and hostile witness IDs;
- finite independent per-loop and aggregate bound expression IDs;
- remove and reclassify mutant IDs;
- expected runtime rejection channel.

The manifest is invalid unless a pinned AST extraction proves a bijection:

- every production dynamic-family reference has one manifest anchor;
- every manifest anchor resolves once;
- every helper invocation resolves and has a witness;
- no alias, macro, nonconstant event argument, duplicate anchor, missing anchor,
  or unexpected anchor exists.

## Independent bounds

Bounds may use only canonical input counts and frozen public manifest ceilings.
They SHALL be declarative expressions evaluated with arbitrary-precision
integers. They SHALL NOT reproduce solver ordering, container state,
reference-ownership state, or selection logic.

Each bound must be finite and useful:

- a global maximum such as the public absolute work ceiling is insufficient;
- each loop or recursion family receives a local bound;
- the aggregate bound is checked against every ordinary and hostile witness;
- a bound breach is NO-GO;
- satisfying a bound does not replace exact Class-B identity or mutation
  sensitivity.

Dynamic native counts remain implementation-conformance evidence, not an
independently predicted closed-form oracle.

## Isolated mutant law

The runner SHALL create temporary source trees under a run-specific build
directory. Tracked production files SHALL remain byte-identical.

For each accounting anchor, exactly two mutants are required:

1. `REMOVE:<site>` removes only the accounting effect. A statement-form
   emission becomes a side-effect-free no-op. A boolean
   `cancel_reserved`/`charge_reserved` expression becomes `true` so that the
   mutant can reach runtime evidence.
2. `RECLASSIFY:<site>` changes only the event argument through the fixed cycle:

```text
MERGE_COMPARE -> MERGE_MOVE -> LOOKUP -> STATE -> REFERENCE ->
SELECT -> RECONSTRUCT -> MERGE_COMPARE
```

Static source/hash rejection is disabled only for the one explicitly
authorized mutant patch. Every mutant must:

- resolve exactly one AST anchor;
- compile successfully;
- execute its frozen witness;
- preserve the intended non-accounting control path;
- be rejected by runtime evidence.

Direct-emission mutants must preserve Class-A status and payload, then fail the
per-case Class-B vector. Reservation, cancel, and consume mutants may instead
fail a typed-ledger, cleanup, reservation, or transactional no-write invariant.

Automatic golden regeneration is forbidden.

## Verification and CI

The smallest coherent implementation consists of:

1. a pinned compile database and AST extractor;
2. one versioned manifest and witness map;
3. a validator proving AST/manifest bijection and independent finite bounds;
4. an isolated mutant generator;
5. focused runtime replay for all mutants;
6. source/object/release identity checks;
7. retained machine-readable per-mutant results.

The focused mutant job is separate from ordinary conformance. CTest fixture
setup/cleanup may orchestrate isolated generated trees, but the evidence runner
must retain its own schema, hashes, and fail-closed result. The full candidate,
hostile, platform, and release non-consumption campaigns remain separate
Step-10 gates.

## Falsifiable predictions

- the pinned AST inventory resolves exactly the frozen production anchors and
  helper invocations;
- the current baseline executes at least one immutable witness per helper
  invocation;
- all current 72 remove/reclassify mutants compile;
- all 72 are rejected by runtime evidence;
- direct-emission mutants retain Class-A output;
- production source/header hashes and release objects remain identical;
- released speech and Mozart bitstreams and decoded PCM remain byte-identical.

## Kill gates

Implementation or admission is unconditional NO-GO on:

- an unmanifested, duplicate, aliased, macro-hidden, nonconstant, or unexpected
  dynamic event reference;
- a missing helper invocation or an invocation without a witness;
- a bound copied from native control flow, a trivial global-only bound, or a
  bound breach;
- a mutant compile failure, unreached witness, surviving mutant, or rejection
  caused only by the ordinary source hash;
- automatic expected-output regeneration;
- a Class-A change from a direct-emission mutant;
- any tracked production source/header change;
- any production object/shared-library difference caused by this substep;
- any released bitstream or decoded-PCM change.

## R-198 and batch boundary

Temporary mutant copies, standalone scripts/tests, and CI artifacts do not
trigger the complete music/Opus gate when production sources and release
objects remain identical.

Any actual charge-site, solver, ledger, resource, cleanup, failure-behavior,
typed-stream, RDO, bitstream, decoded-output, or Orkela change exits this
preflight and receives a separate evidence-first audit plus the applicable
complete R-198 comparison.

The current working tree already contains separately audited R-191 production
remediation relative to `ecfee1a3ed4a2a62848da91c91acc098f873cbd6`.
This test-only substep SHALL NOT retroactively classify those changes as
evidence-only. Final publication must preserve distinct audit provenance and
must not combine machine results from different revisions.

## Audit status

The first independent review returned **NO-GO for immediate implementation**
and selected the AST-inventory/isolated-mutant alternative above. This revised
contract requires a fresh independent binary GO before code is written.
