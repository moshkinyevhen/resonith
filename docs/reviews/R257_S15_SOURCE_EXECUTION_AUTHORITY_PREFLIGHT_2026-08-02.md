# R-257 S15 source-execution authority preflight

Date: 2026-08-02

Status: **AMENDED DRAFT V5; IMPLEMENTATION AND EXECUTION NO-GO PENDING DUAL AUDIT**

## Problem and frozen failure

R-255 hashes every existing `.pyc` adjacent to its 66 local source modules.
The pre-commit reproduction proved that this set contains 66 timestamp-based
CPython 3.14 caches plus 18 foreign CPython 3.12 caches. A normal CPython 3.14
import rewrote one stale selectable cache from unchanged source. The focused
module then produced 16 PASS and two authority-only failures. No audio workload
or post-change timing transaction ran.

The exact R-253 oracle, test and compressed-golden hashes did not change. R-234
and R-255 remain immutable historical evidence; neither may be repaired in
place.

## Objective and threat boundary

Create the smallest evidence-only launch and import contract that:

1. executes every project Python module from its authorized source, not a
   mutable source-tree cache or custom loader;
2. rejects pre/post source drift, unknown local imports and redirected,
   sourceless or dynamically removed local modules before trusting evidence;
3. prevents `site`, `.pth`, user customization and inherited Python path state
   from running before authority validation;
4. gives the controller and every worker a distinct fresh empty cache prefix;
5. binds all executed source, extensions, runtime, native and configuration
   bytes without hashing irrelevant caches;
6. changes no codec, syntax, output, workload, metric, product or release law.

This is a reproducibility and accidental/local-tamper authority, not a sandbox
against an already malicious same-user administrator or kernel. Prefix
ownership means exclusive creation plus a continuously held Windows directory
identity that prevents rename/delete, not an unsupported privilege boundary.

## Primary evidence

- [PEP 552](https://peps.python.org/pep-0552/) states that timestamp pycs
  depend on volatile source metadata and are not deterministic functions of
  source bytes.
- The official [Python 3.14 command-line
  documentation](https://docs.python.org/3/using/cmdline.html) defines `-I`,
  `-S`, `-P`, `-B`, `PYTHONHASHSEED`, and `-X pycache_prefix`. `-B` prevents
  writes; it does not establish that an existing cache was not read.
- The official [Python 3.14 `sys`
  documentation](https://docs.python.org/3/library/sys.html) states that a
  non-`None` `sys.pycache_prefix` reads and writes a parallel tree and ignores
  source-tree `__pycache__` directories.
- The frozen runtime currently contains zero `.pyc` or `.pyo` files outside
  `__pycache__`; this must remain an enforced predicate, not an assumption.

## Rejected alternatives

### No change or restore stale bytes

Rejected. Normal cache repair already falsified R-255. Restoring the vanished
`8759a513...` bytes would revive code compiled from the preceding source.

### Source hashes under the default interpreter startup

Rejected. `site`, `.pth`, `PYTHONPATH`, a timestamp-valid cache or a custom
loader may execute before an endpoint source/hash check.

### Checked-hash caches in the project tree

Rejected as larger and still mutable. PEP 552 validates the embedded source
hash, not arbitrary mutation of the remaining pyc body. A sealed checked-hash
deployment prefix may be studied later for startup performance; it is not
needed for this evidence gate.

### Broad cache deletion

Rejected. Source-tree caches are unrelated development state. The selected
design ignores them without deleting or trusting them.

## Selected launch state machine

### Stage -1: explicitly untrusted path proposer

CPython imports file-backed encoding modules before user script code. Therefore
no in-process assignment of `sys.pycache_prefix` can establish startup source
isolation. An external orchestration step proposes one absolute nonce leaf
under the exact authority-declared prefix root but does not create it. Stage -1
is not trusted, contributes no evidence and has no authority to accept a
result. Its only output is the path string; Stage 0 revalidates every property.

For the focused gate, the exact Stage -1 PowerShell command and proposed path
are retained in the receipt. A later post-change runner must define and audit
its own equivalent caller. No reusable Stage -1 project file is added by
R-257.

One new stdlib-only bootstrap,
`experiments/r257_source_execution_bootstrap.py`, has exactly two roles.

### Stage 0: isolated creator and parent

The only admitted outer command uses the exact bound interpreter and receives
the still-nonexistent proposed Stage-0 leaf at interpreter startup:

```text
python.exe -I -S -B -X pycache_prefix=<nonexistent-stage0-leaf> experiments/r257_source_execution_bootstrap.py --stage0-prefix <same-path> ...
```

Stage 0 requires the stage marker to be absent. `-I -S -B` prevents inherited
Python environment, user site, `site` processing and bytecode writes before
the bootstrap source runs. The startup `-X` redirects reads before CPython
loads file-backed `encodings` modules; the nonexistent tree supplies no cache,
and `-B` prevents its creation during startup.

The bootstrap prologue may import only `sys`, `os` and `ntpath`, independently
verified as builtin/frozen in the exact CPython 3.14.6 runtime. It manually
parses the absolute Stage-0 path, asserts `sys.pycache_prefix` resolves to that
same path, proves the leaf does not exist, and performs one exclusive
`os.mkdir`. Only then may it import source-backed stdlib modules such as
`hashlib`, `json`, `pathlib`, `ctypes` or `subprocess` and open the held Windows
identity. Success of the single create operation is the freshness proof.

The Stage-0 leaf and Stage-1 leaf are distinct and receive separate receipts.
After source-only stdlib initialization, Stage 0 verifies the expected
authority SHA, schema, bootstrap self-hash, target identity and interpreter
executable/DLL hashes before launching Stage 1. It also requires the exact
Stage-0 runtime flags (`isolated`, `no_site`, `safe_path`, no bytecode writes,
optimization zero); direct or already-marked Stage-1 entry is never accepted
as evidence.

Stage 0 sanitizes every `PYTHON*` variable. Stage 1 receives only the declared
`PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPYCACHEPREFIX=<absolute-owned-leaf>` and the frozen numeric-thread
variables. `PYTHONHOME`, `PYTHONPATH`, `PYTHONSTARTUP`, `PYTHONINSPECT`,
`PYTHONUSERBASE`, customization hooks and undeclared Python variables are
absent.

For each role, Stage 0 creates one nonce-named direct child under an authority-declared,
already existing staging root by a single create-new operation with no retry.
It rejects any pre-existing leaf. Every existing ancestor and the leaf must be
an ordinary non-reparse directory. A Windows directory handle opened without
delete sharing remains held until Stage 1 exits. Its resolved final path,
volume serial and file ID form the exclusive-creation receipt passed to Stage
1. Controller and worker receipts must be pairwise distinct; a receipt may
never be reused.

Stage 0 holds both its own prefix identity and the Stage-1 directory identity,
launches exactly one Stage-1 child, propagates its exit status, verifies both
identities and both empty leaves after child exit, then removes only those
exact empty leaves. A nonempty, replaced, missing or reparse leaf fails closed
and is retained for diagnosis. Duplicate or already-present stage markers fail
before child launch.

### Stage 1: source-only consumer

The exact Stage 1 interpreter command is:

```text
python.exe -S -P -B -X pycache_prefix=<absolute-owned-leaf> bootstrap.py --stage1 ...
```

Before adding any project or site-packages path, Stage 1 verifies:

- one exact stage marker and no re-exec/argv/environment drift;
- `sys.flags.no_site == 1`, `sys.flags.safe_path == 1`,
  `sys.dont_write_bytecode is True`, `sys.flags.optimize == 0` and the frozen
  hash-seed startup receipt;
- resolved `sys.pycache_prefix` and its held volume/file identity equal the
  Stage 0 receipt;
- the prefix is empty and every path component remains non-reparse;
- no project module is already present in `sys.modules`;
- bootstrap, target, authority, interpreter and non-cache runtime bytes still
  match their prelaunch hashes.

Only after these checks may Stage 1 add the one exact bound `site-packages`
directory. Project roots are never added to `sys.path`, path hooks or importer
caches. The three current `PROJECT_ROOT`, `REFERENCE_ROOT` and
`EXPERIMENT_ROOT` `sys.path.insert` calls in R-232 and the explicit experiments
path insertion in the focused test are authorized for removal. `sys.path`,
`sys.path_hooks` and `sys.path_importer_cache` then remain under the frozen
bootstrap contract. Stage 1 never calls `site.main` and never processes `.pth`
files.

The bootstrap is the sole direct-source entrypoint. Its Stage-0 and Stage-1
`__main__` instances must have the exact authorized argv path and `__file__`,
`__spec__ is None`, exact `SourceFileLoader` type where the frozen interpreter
provides `__loader__`, no cache path, and equal pre/post source hashes. This is
the only explicit exception to the spec-loader rule.

Focused tests are dispatched by importing the authorized test module through
the guard and running its `unittest.TestCase` suite with the stdlib test runner;
no pytest import hook or path mutation is admitted. Controller and worker roles are
dispatched by importing top-level `r232_s15_source_filter_gate` under its one
reserved authorized `SourceFileLoader` identity and calling `main()` with exact bound
arguments. `runpy`, direct target scripts and target `__main__` aliases are
forbidden.

## Pre-execution import authority

Before the first project import, Stage 1 installs one terminal allowlisting
`MetaPathFinder` backed by the authority's exact module-name-to-source and alias
map. For an authorized local name it returns a normal spec whose loader type is
exactly `importlib.machinery.SourceFileLoader`; its loader path and origin are
the authorized `.py`, with exact package search locations where applicable.

For every other name the guard delegates resolution itself to the frozen
standard finders, inspects the prospective spec before returning control, and
raises if any origin or package search location resolves lexically or by an
existing handle under a project root. This rule is name-independent and blocks
unknown top-level aliases as well as package children. Because project roots
are absent from every path surface, an unlisted local file has no later
`PathFinder` fallback.

The finder records every authorized import attempt before execution in an
append-only in-memory ledger. This catches a dynamically imported then removed
module. Stage 1 replaces `sys.meta_path` with an exact immutable tuple headed
by the guard, records every remaining finder identity, and installs a stdlib
audit hook that rejects any import event if this tuple or its first position
has changed. Pre/post checks require the same identities. An AST gate rejects
authorized project source that mutates or assigns `sys.path`, `sys.meta_path`,
`sys.path_hooks` or `sys.path_importer_cache`.

`sys.path` and `sys.path_hooks` retain exact object and value identity.
`sys.path_importer_cache` retains exact object identity, but normal
`PathFinder` resolution may lawfully populate it. The terminal guard owns that
evolution:

1. before every delegated resolution, the cache must equal the guard's last
   accepted snapshot;
2. the guard invokes the frozen `PathFinder` itself;
3. before returning the prospective spec, it diffs the cache against the
   snapshot;
4. every added key must resolve lexically and by existing ancestry inside a
   bound standard-library or exact site-packages search path, never a project,
   prefix, output or unknown path;
5. every value must be `None` or exact `FileFinder` type with the authority-
   approved frozen loader table; a returned spec is still independently
   rejected if it selects sourceless, zip, custom or redirected execution;
6. deletion or replacement of an accepted entry is forbidden;
7. each accepted delta, key, finder type and loader-table identity enters the
   append-only import ledger before the snapshot advances.

At every import audit event, and again after imports and workload, the live
cache must equal the last accepted snapshot. A mutation with no following
import therefore fails at the endpoint; a mutation preceding an import fails
before delegation. These controls add no hook or state to codec modules and
remain outside timed regions.

After imports and after workload, validation requires:

- every ledger name/path pair belongs to the static authority map;
- every loaded local module uses exact `SourceFileLoader` type, loader path,
  `spec.origin` and `__file__` resolving to its authorized `.py`;
- every local `spec.cached`, whether or not it exists, is lexically and by
  resolved existing ancestry contained under the held prefix;
- all required root modules were loaded and no unauthorized local module was
  attempted or loaded;
- all authorized source hashes equal both pre-import and post-work hashes;
- the prefix remains empty.

Built-in and frozen standard-library modules are allowed because the exact
interpreter is bound. Every file-backed loaded module in local, standard-
library and third-party scope must be either:

- exact `SourceFileLoader` over a bound `.py`; or
- exact `ExtensionFileLoader` over a bound `.pyd`/DLL.

Zip, sourceless, custom/subclass, redirected and other file-backed loaders are
rejected. The bootstrap direct-entry exception above is checked separately.
The complete loaded file manifest is retained and rehashed after the workload.

## Canonical runtime closure

The new schema removes `local_bytecode`. Its canonical runtime-tree digest:

1. walks lexical relative paths without following links;
2. rejects symlink/reparse, device, socket and non-regular entries;
3. excludes only descendants of a path component exactly named
   `__pycache__`;
4. rejects any `.pyc` or `.pyo` outside such a directory;
5. hashes, in UTF-8 byte-sorted relative-path order, a versioned type marker,
   relative path length and bytes, file length and SHA-256 for every retained
   regular file.

The authority binds the digest algorithm/version, all 66 local source hashes,
bootstrap and target, all filtered runtime trees, interpreter files, loaded
`.py` and extension/metadata/data files, native core, frozen configuration,
R-253 preflight, test source and compressed golden fixture.

## Controller and worker prefixes

The top-level focused test or controller runs as Stage 1 under its own prefix.
For a worker, the controller uses the same exclusive-creation primitive to
create and hold a new sibling leaf, then launches the exact Stage-1 bootstrap
interpreter directly with the frozen flags and environment. The bootstrap
imports the controller module and calls its worker role in the same process;
there is no nested wrapper process, preserving the worker PID and process
peak-working-set measurement. The controller verifies and removes only that
empty leaf after exit.

Controller, every worker and every sibling must have unequal nonce, path,
volume/file identity and receipt digest. The new authority validates the
bootstrap and prefix helper bytes. Prefix bookkeeping remains outside every
timed encode/decode interval.

## Executable adversarial evidence

Temporary synthetic packages, never project caches, must prove:

1. Stage-0 startup reports every preloaded file-backed `encodings` cache path
   under the proposed alternate prefix, while the default runtime cache-tree
   manifest remains byte-identical and the Stage-0 prefix did not exist before
   the prologue's exclusive creation;
2. a timestamp-valid malicious pyc with spoofed source mtime/size and a normal
   current-source pyc under source-tree `__pycache__` are both ignored; only
   authorized source can set the execution sentinel;
3. checked-hash, foreign-tag and malformed source-tree cache variants likewise
   do not affect source-derived execution;
4. legacy sourceless `.pyc/.pyo`, zip and custom/subclass loaders are rejected
   and their body sentinels remain untouched;
5. missing, duplicate-stage, wrong, relative, pre-existing, nonempty, reused,
   replaced and reparse prefixes fail at the declared boundary;
6. Stage 0 never emits a child missing `-S`, `-P`, `-B`, the exact hash seed,
   sanitized path environment or authenticated receipt. Raw deliberately
   malformed Stage-1 children need prove only that no evidence is accepted,
   because startup payloads can precede child checks. Under the exact
   production command, injected `PYTHONPATH`, `sitecustomize`, `usercustomize`
   and `.pth` sentinels remain unexecuted;
7. source mutation, pre/post source drift, redirected origin, wrong exact
   loader type, outside-prefix `spec.cached` and dynamically removed local
   modules fail closed;
8. Stage-0, controller and at least two worker/sibling receipts are distinct, their
   handles prevent replacement, and every prefix is empty at each boundary;
9. `.pyc/.pyo` outside runtime `__pycache__` is rejected, while cache contents
   below `__pycache__` cannot change the canonical digest.
10. an injected importer-cache key, replaced accepted `FileFinder`, custom path
    hook, forbidden loader-table delta and mutation with no subsequent import
    all fail closed; normal NumPy/SciPy PathFinder cache additions are accepted,
    ledgered and exactly reproducible across both focused runs.

Reparse evidence is mandatory on the frozen Windows host and may use only a
temporary junction created and removed inside its own temporary root. Other
destructive mutants remain confined to temporary roots.

## Scope and budgets

The remediation may change only:

- `experiments/r232_s15_source_filter_gate.py`: at most 220 added physical
  lines and 40 KiB;
- new `experiments/r257_source_execution_bootstrap.py`: at most 240 physical
  lines and 40 KiB;
- `tests/test_maf_source_filter_oracle.py`: at most 260 added physical lines
  and 48 KiB;
- one new source-execution authority JSON; R-234/R-255 remain byte-identical;
- R-256/R-257 decision, audit, index, changelog and checkpoint records.

Total evidence-code growth is at most 720 physical lines and 128 KiB. No
oracle, golden fixture, native core, configuration, codec workload, expected
stream/PCM/report/trace, syntax, decoder or product file may change.

## Admission and kill gate

- At most 26 focused tests and 75 seconds per run on the frozen host.
- Run the focused module twice from separate Stage 0 invocations. Results,
  authority/source/runtime manifests and every output identity must match.
- Prefixes are distinct and empty before import, after imports, after workload
  and after child exit; parent cleanup is exact and narrow.
- All 128 R-253 golden cases, caller/bound/transaction tests and source/native/
  golden hashes remain exact.
- No post-change codec runner executes under R-257.

Any failure is terminal NO-GO for this remediation. Do not restore stale cache
bytes, delete project caches, weaken the loader/origin/prefix checks, reuse a
prefix, skip a hostile case, retry a codec transaction, or hide an untrusted
sentinel.

After two independent pre-code GO verdicts, implement the smallest version and
obtain a separate dual implementation audit. Only then may the bounded R-253
post-change runner and its separate execution authority be created; that
runner still requires another read-only GO before one invocation. R-257 is
evidence infrastructure, not a codec generation, compression improvement,
R-198 corpus exception or release.

## Superseded first draft

The first R-257 draft SHA-256
`e7c1fac944d01f549d97f583749c3215a50f10096574d6c09bee7cc756e2df61`
received two independent NO-GO verdicts. It lacked exact startup isolation,
pre-execution import control, handle-bound prefix ownership, complete runtime
loader closure and executable temp-only mutants. It authorized no code.

The V2 draft SHA-256
`68189aa29d95d6fabfdd7743d7ef1a80b40204589ff0dc098a059ee61e09890e`
also received two independent NO-GO verdicts. It still allowed Stage 0 to read
default caches before isolation, exposed project roots to finder fall-through,
overclaimed pre-startup sentinel nonexecution for malformed flags, and left
target dispatch ambiguous. It authorized no code.

The V3 draft SHA-256
`4df8611a4b02dd9d15db26f1e9e9237ef43c10d479ce2b49b3b334ed192498e9`
also received two independent NO-GO verdicts. It set the Stage-0 cache prefix
after CPython had already imported file-backed encoding modules and named a
nonexistent namespace-package target while leaving four project-path inserts
alive. V4 moves the first prefix into the outer `-X` startup command, treats
the caller as untrusted, reserves the real top-level controller name and
removes every project-path mutation. V3 authorized no code.

The V4 draft SHA-256
`cbd53f3c84e769413531b8c95c299bfeaffca24aa0d0c8fa0f539825e659d99b`
received one independent GO and one independent NO-GO, so it authorized no
code. The blocking audit proved that normal `PathFinder` imports legitimately
populate `sys.path_importer_cache`; literal value immutability was therefore
unexecutable. V5 freezes object identity and permits only guard-owned,
path-bound, exact-finder deltas recorded in the import ledger.
