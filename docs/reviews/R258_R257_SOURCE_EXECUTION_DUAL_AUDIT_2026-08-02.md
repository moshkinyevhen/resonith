# R-258 R-257 source-execution pre-code dual audit

Date: 2026-08-02

Status: **DUAL GO FOR EXACT R-257 V5 REMEDIATION ONLY**

## Reviewed identity

- R-257 V5 SHA-256:
  `4c933257e53fe67605a612403ad0c82f43902a9ec1a21344ebdae9fa655e8538`;
- repository HEAD before this evidence checkpoint:
  `20de483d7ed4dff1187ab48332b69d11b02252ec`;
- unchanged R-253 oracle SHA-256:
  `736292ac28b5a3dcb7ca33db6a4be0c451909a67b96dab0c393b435b5656382e`;
- unchanged R-253 focused test SHA-256:
  `bf409eb3f5f700937f7d31ca8ccdcbc0c3f615794dba412e7a0f763b34bdba2b`;
- immutable R-255 negative authority SHA-256:
  `d275e280f5d1a44048c97e7e6fca42e7e2ecd3a16bdcba7f68d75954c60a8aa3`.

Two independent auditors reviewed V5 without editing files or executing codec
work. Earlier R-257 drafts remain explicit NO-GO history: V1 and V2 each
received two NO-GO verdicts; V3 received two NO-GO verdicts; V4 received one GO
and one blocking NO-GO, therefore no authority.

## Closed findings

The final design closes every blocking finding raised across the five drafts:

- the outer CPython command receives a still-nonexistent Stage-0
  `-X pycache_prefix` before startup encoding imports;
- Stage -1 is explicitly untrusted, while Stage 0 exclusively creates and
  holds the proposed directory identity;
- controller, worker and sibling prefixes are distinct, held, reparse-free,
  empty at every boundary and narrowly removed only by their creator;
- project roots never enter path resolution and all four legacy project-path
  inserts are removed;
- a terminal name-independent finder is the sole local resolver and records
  every attempted local import before execution;
- bootstrap is the sole direct-source exception; focused tests, controller and
  workers use exact normal `SourceFileLoader` identities in the same measured
  process;
- all loaded file-backed Python and extension modules, origins, loaders,
  sources and filtered runtime bytes are bound and rechecked;
- runtime digests exclude only descendants of `__pycache__` and reject
  sourceless bytecode elsewhere;
- `sys.path` and path-hook values and the `sys.meta_path` tuple remain frozen;
- `sys.path_importer_cache` keeps exact object identity and may evolve only by
  deep, guard-owned, bound-path `PathFinder` deltas recorded in the ledger;
- malformed startup can never accept evidence, while correctly authenticated
  startup prevents path/site/customization sentinels from executing;
- all destructive or malicious cache, loader, alias, mutation, reparse and
  lifecycle witnesses are temporary and executable.

Independent exact-runtime probes confirmed both decisive prerequisites:

- `-I -S -B -X pycache_prefix=<nonexistent>` redirects pre-user-code encoding
  cache paths without creating the prefix; and
- normal isolated `pathlib`/`re` imports grow the importer cache from four to
  seven entries through bound-runtime `FileFinder` additions, with no deletion
  or replacement.

## Implementation conditions

The immutable importer-cache snapshot must be structural: every accepted key
records exact value identity/type, canonical path and exact FileFinder loader-
table identities. Existing entries are revalidated at every import event and
endpoint so in-place loader-table mutation cannot evade a shallow comparison.

The finder is terminal for every name. The retained Stage -1 command uses
absolute authority-bound bootstrap and target paths and records CWD, full
command and proposed path. Only Stage 0 may create the Stage-0 leaf.

The implementation is restricted to the three evidence-code surfaces, one new
authority and documentation listed by R-257. R-234, R-255, the oracle, golden
fixture, native core, configuration, codec workload and all expected outputs
remain byte-identical.

## Verdict and boundary

**GO** for the exact R-257 V5 evidence-infrastructure implementation only.

After implementation, the complete focused module must run twice from
separate Stage-0 invocations within 26 tests and 75 seconds per run, with exact
results, manifests, prefixes and all hostile controls. An independent dual
implementation audit remains mandatory afterward.

This GO does not authorize a post-change codec runner, timing transaction,
R-198 exception, algorithm generation, Opus comparison, syntax, decoder,
version, product, promotion or release change.
