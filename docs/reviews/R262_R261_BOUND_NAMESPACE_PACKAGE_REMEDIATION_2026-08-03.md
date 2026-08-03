# R-262 R-261 bound namespace-package remediation

Date: 2026-08-03

Status: **STATIC IMPLEMENTATION CANDIDATE; EXECUTION NO-GO PENDING DUAL AUDIT**

## Frozen failure

The first R-261 focused Stage-0 invocation exited `1` after 29.389544 seconds;
no second invocation was attempted. The immutable evidence is:

- `artifacts/r261-s15-focused-admission-v1/run-1.stage-minus1.json`, SHA-256
  `4acfd1c24a687211356425095da021bad342972ff3fe7690e36f4ade5067b2b6`;
- stdout SHA-256
  `766f8d7e36b5d4bae9f82b749ca22ca68397afd39f4f0afc70233119bff37670`;
- stderr SHA-256
  `1d384fb4c7ce8e0b15c23eb81f17e8e345a711a08cde5d860d7c0a3850553f1d`;
- both exact prefixes absent after exit.

The AST gate and source-module import began successfully. The terminal guard
then rejected `scipy._external`: SciPy 1.18.0 intentionally ships that directory
without `__init__.py`, so CPython returns a namespace-package spec with
`loader is None`, `origin is None`, and one `_NamespacePath` location inside
the already hash-bound site-packages tree.

An isolated source-free probe confirmed that after import the frozen CPython
3.14.6 runtime exposes the same package with exact public
`importlib.machinery.NamespaceLoader`, `origin is None`, `__file__ is None`,
and the same single namespace location. Python's import reference and
`NamespaceLoader` documentation define this as normal namespace-package
behavior:

- <https://docs.python.org/3.14/reference/import.html#namespace-packages>
- <https://docs.python.org/3.14/library/importlib.html#importlib.machinery.NamespaceLoader>

## Alternatives

### Reject all namespace packages

Rejected. It makes the exact frozen SciPy dependency unimportable and confuses
absence of executable `__init__.py` with unauthorized code execution.

### Allow any loader-less or multi-location package

Rejected. Virtual, outside-runtime or merged namespace portions could widen
the search surface.

### Admit one bound runtime namespace form

Selected. A pre-load namespace spec is accepted only when:

1. `loader is None` and `origin is None`;
2. `submodule_search_locations` has the exact frozen CPython `_NamespacePath`
   type;
3. it contains exactly one exact-`str` directory;
4. its absolute lexical spelling is a non-root descendant inside the lexical
   site-packages root;
5. every lexical component from that root through the directory is `lstat()`
   inspected sequentially before resolution, with immediate rejection at the
   first symlink/reparse entry;
6. the directory then strictly resolves inside the independently resolved,
   already authority-hashed site-packages tree;
7. it exists as a directory, not a regular file, and the frozen runtime tree
   remains hash-identical at entry and endpoint.

The Guard records the namespace name and resolved directory in its import
ledger. After loading, validation requires exact module and spec names matching
the ledger key, exact `NamespaceLoader`, `None`
origin/file, identical module/spec loader, identical one-location namespace
path, and the same runtime containment. That evidence is retained in the final
receipt. No namespace directory itself executes code; every descendant source
or extension module still passes the existing exact loader/runtime checks.

The Guard also freezes every exact namespace already present in `sys.modules`
before installation as an explicit baseline. Final validation requires a
bidirectional one-to-one equality: each post-guard namespace ledger entry has
exactly one matching final module, every final namespace not in the baseline
has exactly one ledger entry, and no two names or raw locations alias the same
resolved directory. An unledgered synthetic alias therefore cannot pass merely
because its metadata is structurally valid.

## Falsification matrix and gate

The pre-load table must reject every near miss independently: loader-less spec
with file origin; non-namespace loader; locations `None`, list, tuple, custom
iterable or `_NamespacePath` subclass; zero or multiple portions; the
site-packages root itself; exact
`_NamespacePath` with a non-exact-`str` element; lexical escape; outside or
missing target; regular-file target; direct reparse root; and a child reached
through a reparse ancestor. The namespace branch is selected only for exact
`(loader is None, origin is None, exact _NamespacePath)`; every other spec
continues to the existing exact source/extension branch without fallback.

The post-load table must independently reject: missing module; `__file__`
absent or non-`None` (the frozen contract requires the attribute with exact
`None`); module-name drift; spec-name drift; wrong module loader; wrong spec loader; two non-identical
`NamespaceLoader` instances; origin drift; `__path__` not identical to spec
locations; wrong path type; zero/two entries; non-string entry; lexical escape;
outside, missing, file, direct-reparse or reparse-ancestor location; unledgered
name/alias; duplicate raw location; and duplicate resolved location. The final
receipt must show exact equality of namespace name, loader type, raw location
and strict-resolved location between ledger and loaded records.

One executable negative witness adds an outside second namespace portion
containing a side-effecting descendant, attempts the descendant import, and
proves importer-cache confinement rejects it before the side effect. It then
restores namespace state transactionally. These cases remain table-driven
inside the existing focused suite; they do not create additional full runs.
A separate dangling-junction witness removes the junction target before asking
for a descendant and requires the guard's own reparse `ImportError`, proving
that no later component is accessed after the ancestor is rejected.

The positive witness must show `scipy._external` in the final ledger and loaded
record as a namespace.

The authority binds this R-262 contract as retained evidence. Duplicate raw and
resolved-location predicates receive separate production-helper mutations;
the realizable distinct-raw lexical-alias/same-resolved case also passes through
the complete ledger-plus-loaded final validator.

The next admission restarts as two new Stage-0 invocations with fresh prefixes.
Any failure is terminal and suppresses the second invocation. R-262 changes no
codec algorithm and authorizes no audio/Opus workload.

## Frozen implementation candidate

The candidate is frozen for read-only implementation audit at these identities:

- bootstrap SHA-256
  `eb5f85b301e004ef05135a7abeacea8a1217978193845e17d0592d4c311b45c7`;
- gate SHA-256
  `3df920de431872c906037e489d2adc1d490d64f49c84555a8df3bfef0eef9e2d`;
- focused-test SHA-256
  `6a577db419efee49941de177c6ce121674e02747287a1251ac66e692f92eabd3`;
The bootstrap is exactly `240` physical lines and remains below `40 KiB`.
The cumulative frozen source budget is `720` added lines: `240` bootstrap,
`218` gate, and `262` focused tests, at the `720`-line ceiling. Syntax-only
AST parsing passed. No focused test, controller, codec, audio, or Opus workload
was executed after this implementation; execution remains blocked on two
independent binary implementation decisions.
