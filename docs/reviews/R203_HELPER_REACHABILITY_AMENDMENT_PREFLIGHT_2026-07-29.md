# R-203 helper-reachability amendment preflight

Status: **audit candidate; the 72-mutant campaign remains blocked pending a
fresh independent binary GO**

This document amends only the helper-invocation witness clause of
`R203_DYNAMIC_CHARGE_SITE_MUTATION_PREFLIGHT_2026-07-29.md`. It does not
weaken the requirement to inventory every production charge site, every
static invocation of a charged helper, every mutation, or every independent
work bound.

## Problem

The reviewed Clang 22 AST inventory contains the call
`bounded_state_arena::release@134436` in the exception handler of
`bounded_state_arena::create_handle`.

The call is statically unreachable in the frozen source:

1. `parent_acquired` is initialized to `false`.
2. The only assignment of `true` is sequenced after
   `add_child_reference(value.parent, value)` returns normally.
3. No potentially throwing operation is evaluated between that assignment
   and normal exit from the `try` block.
4. If `add_child_reference` throws, the assignment is not executed.
5. Therefore control can enter the `catch` block only with
   `parent_acquired == false`.

LLVM source-region coverage independently reports zero executions at the
exact AST call position in both the ordinary profile and the disjoint hostile
profile. The old line-based method is not admissible evidence.

Removing the dead branch is a legitimate later cleanup, but it would change
the frozen production source and every following byte offset. It is not
required to determine whether the 36 charge sites are mutation-sensitive.

## Amended classification

Every AST-discovered helper invocation MUST belong to exactly one disjoint
class:

- `reachable_helper_invocations`: the baseline executes at least one declared
  immutable witness at the exact LLVM source region of the call;
- `proven_unreachable_helper_invocations`: the invocation has a reviewed
  source/AST identity, a first-principles control-flow proof, and zero execution
  count in every declared ordinary and hostile profile.

No invocation may be omitted, belong to both classes, or be accepted by source
line count alone.

## Frozen unreachable record

The reviewed manifest record MUST contain:

- invocation ID `bounded_state_arena::release@134436`;
- helper identity `bounded_state_arena::release`;
- call byte span `[134436, 134457)`;
- call AST SHA-256
  `469927c7bad4c4949bc90f88dd9b7d5c9f3de766f14722b36e40a7fe78beedda`;
- enclosing function `bounded_state_arena::create_handle`;
- the source SHA-256 already frozen by the parent preflight;
- a stable proof ID and the SHA-256 of this amendment;
- exact ordinary and hostile LLVM region counts, both zero.

## Fail-closed admission rules

The helper-reachability gate MUST reject if:

1. AST discovery, helper inventory hash, source hash, call span, or call AST
   hash differs;
2. the reachable and proven-unreachable sets are not a complete disjoint
   partition of all 54 discovered helper invocations;
3. any ordinary or hostile profile executes a proven-unreachable invocation;
4. any reachable invocation lacks positive exact-region coverage from its
   declared witness;
5. the zero-count record is generalized to another invocation without a new
   reviewed amendment and independent GO;
6. line-level coverage, a neighboring expression, a crash, or an unrelated
   assertion is used as evidence;
7. the mutation runner treats this helper-call exemption as an exemption for
   any of the 36 charge-site mutants.

If later code makes this invocation reachable, the zero-count gate fails and
the invocation MUST move to the reachable class with a positive immutable
witness before admission.

## Verification

Before the full mutation campaign:

1. the manifest/AST validator proves the 54-call complete inventory;
2. LLVM JSON source regions prove positive coverage for every reachable call;
3. LLVM JSON source regions prove zero coverage for the one frozen unreachable
   call;
4. a negative test changes the invocation class, count, span, or AST hash and
   must fail;
5. an independent auditor issues a binary GO on this amendment and its exact
   SHA-256.

Until all five conditions pass, the 72-mutant campaign remains **NO-GO**.

## Evidence-first decision

Objective: preserve the complete 54-call charged-helper inventory without
pretending that a statically unreachable call executed. The optimized cost is
test authority, not codec output. Production source, bitstream syntax, decoded
PCM, runtime behavior, and the 36 accounting anchors remain frozen.

Considered alternatives:

1. count the containing line or a neighboring expression — rejected because it
   does not execute the call;
2. accept zero merged coverage plus a prose proof — rejected because neither
   proves control flow nor detects source/compiler drift;
3. remove the dead branch — valid cleanup, but rejected for this test-only
   amendment because it changes production source and all following offsets;
4. machine-prove one exact unreachable invocation and require a 53+1 disjoint
   partition — selected because it preserves the frozen production object and
   fails closed on semantic drift;
5. make no change — rejected because the parent preflight would remain
   correctly blocked forever.

Falsifiable prediction: the executable proof and every independent coverage
contributor report the target call unreachable, while the accounting anchor
inside `release` remains positively covered and both of its mutants remain
mandatory. Any contrary observation kills this amendment.

## Executable proof contract

The only accepted verifier is:

- path: `experiments/r203_helper_reachability_proof.py`;
- SHA-256:
  `271f107f398a0a9014a44a63ce71672da3f78e71c76bc680b4381dc667e6c74c`;
- schema: `resonith-r203-helper-unreachable-proof-1`;
- AST normalization schema:
  `resonith-r203-proof-ast-normalization-1`;
- AST-normalization configuration SHA-256:
  `e62be3c9206b9e85125c8c80aa40be9cbf1dbd0af81b9f48e070998b400a290c`.

The reviewed proof artifact is:

- path: `artifacts/r203/r203-helper-unreachable-proof-v1.json`;
- file SHA-256:
  `d02c283e4a1088aa73156dd51e2f6568af78ad81eb61d98f9bd10b9f53ff2151`;
- proof-payload SHA-256:
  `5e88c9c5f3d8ed27f9f9b094bb3ef0f902d696faec76c14b217a3a6281241328`;
- normalized CFG SHA-256:
  `a38b534bedf17a971d272994cbe627d007aa61080ec000216688c7526b0cfce3`.

The runner MUST hash the verifier and artifact, execute the verifier again,
compare the parsed result byte-semantically with the artifact, and bind the
payload to the one unreachable manifest row before building a mutant.

The verifier rejects unless the pinned Clang AST and CFG jointly establish all
of these predicates:

- `parent_acquired` is a built-in non-volatile `bool` initialized to `false`;
- it has exactly two references, is not captured, aliased, or address-taken,
  and has exactly one write;
- the one write assigns literal `true` after normal return from the exact
  `add_child_reference` call;
- the assignment is the final evaluated full-expression in the `try`;
- no cleanup, temporary, declaration, call, or unknown AST construct survives
  after the assignment;
- the target `release` is inside the catch-all handler and only under
  the exact positive built-in lvalue-to-rvalue condition
  `if (parent_acquired)`; negation, comparison, disjunction, conversion, or
  any additional operand rejects;
- forward dataflow at catch entry is exactly `{false}`;
- unsupported AST or CFG structure rejects rather than becoming "unknown but
  accepted".

The forward-dataflow result is computed, not copied into the result: every
pre-write full expression is conservatively permitted to throw and therefore
contributes the current `{false}` state; the predecessor's exceptional edge
also contributes `{false}`; the one write produces `{true}` only on normal
return; the verifier requires the target `if` to be the last statement of the
entire `try`, its assignment to be the last expression of the complete
then-body, and zero post-write expressions or cleanups. Therefore no
post-write exceptional edge can contribute `{true}` to the catch.

Temporary-source adversarial tests move the assignment before the call, insert
a call after it, add a second write, take the variable address, and change the
guard. All five MUST reject; the frozen source MUST pass.

## Compiler and exception model

The proof is limited to the standard synchronous C++ abstract machine:

- Clang executable SHA-256:
  `a8b7a614eeadd9105f814be3701a7f312cda4cea51751b75b408c16100c94e85`;
- version: Clang 22.1.8, LLVM commit
  `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`;
- target triple: `x86_64-w64-windows-gnu`;
- dialect: C++23;
- normalized compile-command SHA-256:
  `b9587d751d78afab682bbbf57d9bd298230ceec8e61c0b4e2275e288b6129c8a`;
- `__EXCEPTIONS == 1`;
- `__cpp_exceptions == 199711L`;
- `-fasync-exceptions`, `-fnon-call-exceptions`, `-fno-exceptions`, and
  `-fno-cxx-exceptions` MUST all be absent.

Signals, injected SEH faults, undefined behavior, and nonstandard asynchronous
exceptions are outside this proof. Any compiler, target, dialect, command,
macro, unwind, exception flag, AST normalization, or CFG drift invalidates the
artifact.

## Frozen 53+1 partition

Parent preflight SHA-256:
`253d18a9061560ab05a4650b7b36c305f85904fed114d648462ca3cbe6cb092b`.

The manifest freezes:

- helper count: 54;
- reachable count: 53;
- proven-unreachable count: 1;
- helper-inventory SHA-256:
  `3f77b61a72fa73b25adee47ed78e498c3f7e1830c18cacf0e50915f87638f481`;
- canonical partition SHA-256:
  `3f133ca10de84da1ffa3f7e4c823cbca7beb667b98a05a1bf99d92c35cda6894`;
- unreachable set exactly
  `{bounded_state_arena::release@134436}`.

The partition digest includes every invocation ID, helper identity, call span,
normalized call-AST hash, classification, and witness IDs. The validator
requires a complete disjoint union of the fresh AST inventory. Group-level
bindings cannot substitute for per-call rows, and the obsolete
`helper_invocation_ids` site field is forbidden.

## Individual coverage contract

Merged coverage alone is insufficient. The final runner keeps and hashes these
separate contributors:

- `ordinary-native`;
- `ordinary-greedy`;
- `hostile-allocation`;
- `hostile-state-arena`;
- `hostile-greedy`;
- the dedicated `legacy` witness for its one explicitly assigned reachable
  invocation.

For the unreachable call, an exact source region MUST exist and have count zero
in every ordinary and hostile contributor. Missing coverage is not zero. Every
reachable call MUST have positive exact-region coverage in its declared suite.
The runner records the raw profile hashes, merge inputs, profdata hashes,
instrumented object hashes, coverage compile database, `llvm-cov` and
`llvm-profdata` paths/versions/hashes, and the exported JSON schema.

The reviewed preflight measured the target at line 4023, column 22:

- `ordinary-native`: 0;
- `ordinary-greedy`: 0;
- `hostile-allocation`: 0;
- `hostile-state-arena`: 0;
- `hostile-greedy`: 0.

The retained full preflight result canonical SHA-256 is
`460274ad324f43e1700689339a9044e4f2e82cff363955b23c9b8c8892975aa5`.
Revalidation with the stricter begin/end exact-region mapper has canonical
SHA-256
`ee81e11366a0407db55fa856d216fff82e814656087034b9b9a4d59ade8b8504`;
every contributor maps call columns 22–42 to the unique active region
`[4023:21, 4023:43)` with count zero. These results are evidence for the
audit, not permission to skip re-emitting and retaining the final campaign
profiles.

## Positive `release` accounting-anchor proof

The unreachable-call classification does not exempt any accounting operation.
The manifest and runner separately bind:

- site: `arena.reference.consume-release`;
- call span: `[137643, 137760)`;
- call-AST SHA-256:
  `f5ae7a372fac8454f95139f28d466d8e3aa877ec7ba6fe2d8c3ea7d6538497d4`;
- reachable caller:
  `bounded_state_arena::release@141958`.

The reviewed preflight measured:

- ordinary merged count: 2,092,851;
- hostile merged count: 164,332;
- hostile state-arena contributor count: 16.

Both the remove and reclassify mutants of
`arena.reference.consume-release` remain among the 72 mandatory mutants and
must retain their declared runtime rejection. The call-site proof cannot
weaken, bypass, or reclassify that charge-site requirement.

## Admission sequence

1. Run the 60 focused manifest/proof tests, including nine temporary-source
   adversarial changes.
2. Recompute the 54-call AST inventory and the 53+1 partition.
3. Run and retain each independent coverage contributor.
4. Obtain a fresh independent binary GO on this exact amendment SHA and its
   bound verifier/artifact/manifest.
5. Only then run all 72 isolated mutants.

No production behavior is changed by this amendment, so the SceneLith-family
audio comparison rule is not triggered here. The first later MAF algorithm
change still requires the full registered-music comparison against both the
preceding Resonith generation and maximum-effort official Opus.
