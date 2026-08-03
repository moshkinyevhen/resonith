# R-260 R-257 bootstrap cache-sentinel remediation

Date: 2026-08-03

Status: **V3 DRAFT; IMPLEMENTATION AND EXECUTION NO-GO PENDING DUAL RE-AUDIT**

## Frozen failure

The first authorized R-257 focused Stage-0 invocation exited `1` before any
focused test or codec workload ran. The immutable Stage-minus-1 receipt is
`artifacts/r257-s15-focused-admission-v1/run-1.stage-minus1.json`; its stdout
SHA-256 is `b6e14149a3610f459d4988e1bda2ed32855ac5c7d59fc9c30c0f697cd4e6f7c5`
and stderr SHA-256 is
`af77e58973610e9fc001fac91922f6b71b3d555e6809b5ae811a0c50e456b1d5`.
The run took 22.05 seconds, did not time out, and removed both exact empty
Stage-0 and Stage-1 prefixes. A second focused run was not attempted.

The failure occurred while constructing the terminal import guard. A minimal
source-file startup probe under the same CPython 3.14.6 `-S -P -B -X
pycache_prefix=...` mode reproduced one pre-guard cache record whose key was
the exact executed script path and whose value was `None`. It was not a project
directory or a finder. The same probe showed all other cache keys under the
bound runtime. The temporary probe source was removed and wrote no cache.

Python's import reference defines `sys.path_importer_cache` as a path-entry to
finder cache and states that `None` is cached when no path hook accepts an
entry. The command-line documentation defines `-P` as preventing a potentially
unsafe script directory from being prepended to `sys.path`:

- <https://docs.python.org/3.14/reference/import.html#the-path-based-finder>
- <https://docs.python.org/3.14/using/cmdline.html#cmdoption-P>

CPython 3.14.6 source supplies the implementation-level explanation. Its
`pymain_get_importer()` passes the exact run filename to
`PyImport_GetImporter()` before deciding whether it is a path entry. The path
importer implementation caches `None` before trying hooks and retains that
value when no hook accepts the file. `-P` prevents the script directory from
being prepended to `sys.path`; it does not suppress this run-filename probe:

- <https://github.com/python/cpython/blob/v3.14.6/Modules/main.c>
- <https://github.com/python/cpython/blob/v3.14.6/Python/import.c>

The executable observation is the primary host-specific evidence. The source
and documentation explain the frozen runtime; absence of this exact sentinel
on another runtime remains a fail-closed version/host mismatch.

## Reproducible startup evidence

The first audit correctly rejected an unretained ad-hoc observation. R-260 V3
therefore adds the source-only probe
`experiments/r260_import_cache_startup_probe.py`, SHA-256
`63df2cef060307bc8b401b15b840e52438adca8bd249b71455f9b58dd0ba7c4e`.
It snapshots raw key types, spellings and values plus raw `sys.path` before
importing its reporting dependencies. For the source-file record it separately
records lexical spelling, strict `Path.resolve()` target and every reparse
entry in the source/ancestor chain. The parent runner
`experiments/r260_import_cache_probe_runner.py`, SHA-256
`b8c1f1837446f771c32f57c993b7943bb2636be8fd4e9f3f8ad9131721774522`,
created an exclusive fresh result root, sanitized every inherited `PYTHON*`
variable, froze the declared environment contract, and recorded executable,
probe, stdout, stderr and output hashes plus exit/timeout and prefix state.
It executed once under each source-launch family used by R-257:

- `-I -S -B -X pycache_prefix=...`: exit `0`; output SHA-256
  `731e70bf5b7529aa20147aefcda29bc55c425f4f617ccca7b4235e04a124f0a1`;
- `-S -P -B -X pycache_prefix=...`: exit `0`; output SHA-256
  `e5d44a31ee5d95492e3bb11ccc90bf926e5f75ef83524a4c54db4e38a15be3dd`.

Both executions observed exactly one source-file record: its raw key had exact
type `builtins.str`, exact spelling equal to the executed source path, and
value exact `None`. Its canonical target was absent from canonical `sys.path`.
Its strictly resolved target equalled the executed source and the source chain
contained no reparse entry. Both cache prefixes remained empty. The complete
machine-readable parent receipts are frozen in
`experiments/fixtures/r260_import_cache_probe_summary_v1.json`, SHA-256
`3808484165a21a6c798e78ffc4f9162ee2eee8bcbb18c96c67876399ba4aab5a`.

The probe, parent runner, receipt summary and this remediation are bound only
as non-executable `files` evidence by the revised authority. They are not
added to `local_modules`, `local_imports` or `required_local_imports`.

## Alternatives

### Allow project paths generally

Rejected. It would reintroduce finder fall-through into the workspace.

### Delete or ignore the cache entry

Rejected. Mutating interpreter startup state before the guard would destroy
the evidence that the exact entry existed and would make later deletion
indistinguishable from tampering.

### Disable the importer-cache closure

Rejected. The prior hostile matrix proved that injected keys, replaced
finders, loader-table drift and deletion must remain terminal failures.

### Admit one immutable startup sentinel

Selected. The initial snapshot must contain exactly one exceptional record:

1. the raw key has exact type `str`;
2. its raw spelling exactly equals the frozen absolute bootstrap spelling in
   `sys.orig_argv` and the authority record;
3. its independently resolved canonical target equals the authority-bound
   bootstrap source path;
4. its value is exactly `None`;
5. that exact file path is absent from both raw and canonical `sys.path`;
6. the bootstrap source SHA-256 still matches authority;
7. raw type, raw spelling, canonical target and value are retained in the
   initial immutable snapshot, ledger and final receipt;
8. every general importer-cache key also has exact type `str` before any
   canonicalization;
9. removal, replacement, canonical aliasing, duplication or any other
   outside-runtime key remains forbidden;
10. persistent mutation and any mutation crossing a declared guard checkpoint
    are forbidden; checkpoints occur before delegated path import, on the
    import audit hook, and at the endpoint.

This is a direct-entry startup sentinel, not an import search root and not a
new loader permission.

## Falsifiable prediction and kill gate

Under the exact frozen launcher, the positive focused witness observes the
bound bootstrap key once with exact raw type/spelling and value `None`, absent
from raw and canonical `sys.path`. Its final receipt retains the same raw and
canonical identity. Existing outside-key, finder replacement/deletion,
path-hook and loader-table mutants still fail closed.

The focused hostile matrix must additionally construct these temporary,
authority-bound cases and require no success receipt, no post-checkpoint target
side effect and clean prefixes:

1. sentinel absent at guard construction;
2. sentinel value replaced with a non-`None` object;
3. sentinel replaced by an equivalent case/separator/`..` raw alias;
4. non-exact-string or path-like cache key;
5. a second raw key resolving to the same canonical bootstrap target;
6. bootstrap raw or canonical path injected into `sys.path`;
7. sentinel removal through `importlib.invalidate_caches()`;
8. removal after guard installation followed by a mandatory `stable()` or
   import checkpoint and only then attempted exact re-addition; failure must
   occur at the checkpoint, before the re-addition branch.

An assignment of the already present exact key to the already present exact
`None` value is intentionally not claimed as observable: it changes no cache
state and grants no import capability. Likewise, remove-and-restore entirely
between observations is outside the snapshot claim. Instrumenting or replacing
the interpreter-owned mapping solely to report that unobservable history was
rejected as greater attack surface than the startup exception itself.

The positive witness and all eight adversaries must pass in each full focused
invocation. Both full focused invocations then pass within 75 seconds, with
distinct prefixes and normalized equal source/runtime/import evidence.

Any different outside-runtime cache key, non-`None` bootstrap value,
bootstrap key in `sys.path`, missing sentinel, failed hostile mutant, timeout,
prefix residue or receipt mismatch is terminal NO-GO. It may not be rescued by
deleting cache state, widening the path allowlist or running a codec workload.

The failed first invocation remains immutable negative evidence and does not
count toward the required pair. After two independent read-only GO verdicts on
this remediation and its implementation, R-257 restarts with two new Stage-0
focused invocations. No R-253 post-change runner or codec benchmark is
authorized by R-260.
