# R-263 R-262 bounded transactional hostile-gate redesign

Date: 2026-08-03

Status: **PRE-CODE DRAFT; IMPLEMENTATION AND EXECUTION NO-GO PENDING DUAL AUDIT**

## Problem and frozen failure

R-262 V5 is statically coherent, but its first authorized Stage-0 admission
did not complete within the frozen resource contract. The immutable failure
receipt is
`artifacts/r262-s15-focused-admission-v1/run-1.stage-minus1.json`, SHA-256
`9c18f53340a627a2f325e5cc022648ab8f5ce7464800edb8a180f83147880508`.
It records:

- a declared 75-second Stage-0 limit and a 90-second outer-wrapper limit;
- 94 observed wrapper seconds, exit code `124`, and no child exit code;
- empty stdout and stderr, both with SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- exact termination of the two matching R-262 Python processes followed by a
  read-only zero-survivor check;
- empty retained Stage-0 and Stage-1 prefixes; and
- no second invocation.

The prefixes are retained as failure evidence and must not be reused. R-262 is
not admitted. No codec, audio, Opus, player, version, or release claim changed.

Retained timestamps show that hostile-fixture creation began about 119 seconds
after Stage 0 started. The 18-process hostile fan-out is therefore a large
cost, but it cannot alone explain or repair the pre-matrix overrun. Stage 0
also buffers all Stage-1 output until exit and repeats complete authority and
runtime-tree hashing at several nested boundaries. The prior shell wrapper
declared a deadline but did not own a Windows Job Object and therefore did not
enforce it.

## Primary-source check

Microsoft documents that `TerminateJobObject` terminates every process in the
job hierarchy and that `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` terminates all
associated processes when the last job handle closes. These are the required
outer-monitor semantics, not a shell timeout:

- <https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects>
- <https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject>
- <https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information>

Microsoft also states that ordinary Job completion-port process notifications
are not guaranteed. They therefore cannot authenticate a complete lifecycle.
The authoritative survivor proof must use the job's process-list and accounting
queries while the job handle is still held:

- <https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port>
- <https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list>
- <https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects#resource-accounting-for-jobs>

Python 3.14 documents that `PathFinder.invalidate_caches()` calls every cached
finder's invalidator and deletes `None` entries, while `FileFinder` maintains
an internal filesystem cache. The import reference also makes `sys.modules`,
`sys.path_importer_cache`, path hooks and namespace portions independently
mutable. This supports keeping real invalidation outside the reversible
in-process matrix:

- <https://docs.python.org/3.14/library/importlib.html#importlib.machinery.PathFinder.invalidate_caches>
- <https://docs.python.org/3.14/library/importlib.html#importlib.machinery.FileFinder>
- <https://docs.python.org/3.14/reference/import.html#the-module-cache>
- <https://docs.python.org/3.14/reference/import.html#the-path-based-finder>

## Objective and complete cost

The smallest R-263 objective is to preserve every R-257 through R-262 security
claim while making one focused admission finish with observable progress and
an enforced end-to-end process-tree deadline.

The engineering target is at most 68.0 work seconds from Stage-0 child launch
to either normal exit or forced termination. The immutable process-tree
admission ceiling remains 75.0 seconds. The existing 512-MiB per-process
ceiling remains unchanged; the new outer tree receives a 2-GiB aggregate job
ceiling and exact active-process limit of eight, both tighter than the prior
unbounded aggregate of independently monitored children. Each captured stream
remains at most 4 MiB, and
retained working evidence remains at most 64 MiB. The exact 26-test focused
suite, all 18 hostile states, the exact 82 authority bindings after this R-263
record and launcher are added (14 file records, 67 local-import records and
one inline-launcher record), complete non-cache
runtime trees, default-cache identity, namespace ledger, loaded-module
closure, fresh prefixes, and zero-survivor conditions remain mandatory.

R-263 is the one bounded redesign allowed after the first R-211 resource
breach. Splitting, renaming, or moving code does not reset the cumulative
source or remediation budget. The closed R-263 executable change inventory is
exactly one frozen inline pre-verifier plus
`experiments/r257_source_execution_bootstrap.py`,
`experiments/r232_s15_source_filter_gate.py`, and
`tests/test_maf_source_filter_oracle.py`; no new runner or executable helper is
allowed. The canonical inline `python -c` byte string is at most 1,024 UTF-8
bytes, contains no newline, is stored with its SHA-256 in the authority and
counts as one executable source line. The three files may therefore contain at
most 719 added lines in final `git diff --numstat`. The gate file gains an outer
`--r263-focused-admission` role and
reuses its existing Windows Job Object implementation before Stage 0 exists.
Any lines added for that role, progress, transactions or parsing must be
offset by removing the replaced fan-out and duplicate closure code. Final
three-file additions plus the one inline line must remain at or below the
frozen R-262 total of 720, including every executable line regardless of
location. The bootstrap remains at most 240 physical lines and below 40 KiB.
Documentation, JSON authority and machine receipts are non-executable, but
their file identities and sizes remain part of retained evidence.

## Alternatives and falsification

### Repeat R-262 or raise a timeout

Rejected. A blind retry is forbidden by the retained receipt, and a larger
deadline would weaken the frozen public resource claim without identifying
the defect.

### Change only concurrency

Rejected. Eighteen concurrent interpreters amplify disk and memory pressure,
but the hostile matrix began after the old deadline. Serializing or limiting
that same fan-out cannot prove a 75-second total.

### Cache, sample, or shrink authority closure

Rejected. It would weaken source, runtime, import and endpoint drift claims.
The complete closure remains authoritative; only repeated scans of bytes
already protected by a later mandatory boundary may be removed.

### Run all hostile mutations in the admitting interpreter

Rejected. Source drift changes authority-bound bytes; `atexit` behavior
requires real process termination; and `PathFinder.invalidate_caches()` can
alter hidden `FileFinder` caches, namespace epochs and importer state that
cannot be proven exactly reversible from the visible mapping alone.

### Use two isolated temporal processes and restore invalidation in process

Rejected conservatively. The visible cache can be restored, but exact hidden
cache and namespace-epoch identity is not part of the current transactional
snapshot. Claiming equivalence would be stronger than the evidence.

### Combined three-isolate transactional redesign

Selected. Fifteen reversible mutations execute sequentially inside the one
already guarded Stage-1 interpreter. Exactly three claims remain isolated:

1. `source-drift`, because authority-bound source bytes must never change in
   the admitting interpreter;
2. `post-exit-drift`, because only actual process exit exercises receipt and
   `atexit` ordering; and
3. `sentinel-invalidate`, because real importer invalidation mutates hidden
   state outside the current reversible contract.

This is the smallest design accepted by the stricter independent analysis.

## Transactional hostile matrix

The existing hostile test retains one table and one test identity. Before the
first row, every rollback helper and expected diagnostic value is preloaded.
No helper import, formatter initialization, first-use filesystem traversal, or
allocation-heavy diagnostic is permitted while state is corrupt.

One full `_validate_loaded()` runs before the entire matrix and one after it.
The existing monolithic validator is factored only into production helpers
that it itself calls: one file-module/alias validator, one required-module
validator and one namespace-ledger validator. A row calls only the exact
shared production helper responsible for its state; it may never call a
test-only surrogate or repeat the complete loaded-file rehash.

Each of the fifteen reversible rows must:

1. require `ACTIVE_GUARD.stable()` and equality to the matrix baseline digest
   before mutation;
2. snapshot the explicit state schema below using helpers and bound exact
   built-in methods that are all loaded before mutation;
3. prove that exactly one declared mutation changed state and was not a no-op;
4. call `guard.stable()` for launch/cache/hook/finder/sentinel state, the shared
   file-module validator for file/module/loader/alias state, the shared
   required-module validator for required membership, or the shared namespace
   validator for namespace/module/ledger state;
5. require the exact exception class and stable R-257/R-262 error category,
   and prove that post-checkpoint code was not reached;
6. restore all changed state in reverse order inside `finally`;
7. prove exact object-identity, ordered-value and baseline-digest equality;
8. require `guard.stable()`; then call
   `importlib.import_module("json")` only as an explicitly preloaded cache hit
   and prove that it returns the identical module without changing any state;
   and
9. append one local machine-readable row receipt containing the stable label,
   checkpoint, rejection category, mutation witness and restoration digest.

The exact matrix state schema is:

- identities and ordered values of `sys.path`, `sys.path_hooks`,
  `sys.meta_path`, `sys.modules` and `sys.path_importer_cache`;
- exact environment and argument tuples frozen by the Guard;
- Guard object, cache, path, ledger and namespace-baseline identities plus the
  ordered ledger contents and accepted cache snapshot;
- every cached `FileFinder` identity, path, ordered loader table and each
  loader identity;
- the focused test module identity and its `__file__`, `__loader__`, `__spec__`
  identity plus spec name/origin/loader/cached values; and
- every touched namespace module/spec/loader/path identity, ordered path
  values and relevant `sys.modules` membership.

Removal rows snapshot `tuple(mapping.items())` and restore the same dictionary
object with pre-bound exact `dict.clear` and `dict.update`; exact ordered items
must match afterward. This closes ordering for `module-remove`,
`namespace-missing` and `sentinel-readd`, including the loaded-manifest order.
No import, audit-producing operation, formatter initialization or filesystem
operation may occur between mutation and completion of restoration. Receipt
accumulation is a test-local list outside this state schema and is normalized
by stable label only after restoration.

The fifteen in-process rows are `cache-add`, `cached-outside`, `file-none`,
`hook-add`, `finder-table`, `finder-replace`, `local-alias`, `local-redirect`,
`loader-drift`, `module-remove`, `sentinel-readd`, `namespace-missing`,
`namespace-unledgered-alias`, `namespace-ledger-duplicate`, and
`namespace-resolved-alias`.

Every real row already restores through the exception raised by its production
validator; a second injected-validator matrix and a reversed-order replay are
rejected as test-of-test duplication. Mutators are straight-line assignments
or exact-dictionary operations with no user callback. If a mutator itself
raises, the same `finally` restores state, the row records a terminal harness
error rather than a security PASS, and the full admission fails.

## Isolated claims

The three isolated mutants use the same production bootstrap and checkpoint
logic as the admitting process. They execute concurrently as one fixed
three-member group under the outer job's eight-process/2-GiB aggregate limits
and the unchanged 512-MiB per-process limit; changing concurrency after
observing a result is forbidden. Each nested isolated Job Object has active
process limit two because its Stage 0 must create exactly one Stage 1. Existing
single worker jobs retain active-process limit one. No isolated child receives
a reduced authority closure.

- `source-drift` must exit nonzero with no Stage-1 success receipt and no
  accepted Stage-0 receipt.
- `post-exit-drift` may emit exactly one Stage-1 success receipt before its
  registered exit callback changes source, but Stage 0 must reject the
  endpoint and emit no accepted Stage-0 receipt.
- `sentinel-invalidate` must fail at the intended guard checkpoint before its
  after-checkpoint marker and emit no accepted Stage-0 receipt.

Every isolated prefix must be fresh, identity-held, empty, removed on the
expected handled rejection, and absent from subsequent rows. The poison
`PYTHONPATH`, `sitecustomize`, `usercustomize`, and `.pth` side-effect witness
remains mandatory and must remain absent.

## Non-redundant complete closure

R-263 preserves the complete closure at three distinct trust boundaries:

1. Stage 0 validates the authority schema/SHA, bootstrap and target identities,
   interpreter identity, flags, and proposed prefix before launch.
2. Stage 1 performs the complete 82-binding, local-source, runtime-file and
   runtime-tree closure once before any local import. Before its receipt it
   rehashes the authority, all authorized local sources, and the complete
   loaded-module/namespace manifest through the endpoint validator.
3. Stage 0 performs the complete authority, source/runtime closure,
   default-cache comparison, prefix identity and receipt validation after the
   child exits and before accepting evidence.

`_child_state()` changes from path-driven revalidation to an
already-validated-authority dataflow. Stage 0 passes the authority object it
just fully validated. Stage 1 `_install()` stores an immutable
`(resolved_authority_path, authority_sha256, authority_object)` binding;
`worker_child()` accepts a request only when its path and hash exactly match
that active binding. Installation also stores the SHA-256 of canonical UTF-8
JSON serialization with sorted keys and compact separators. Immediately
before and after every `_child_state()` use, the complete in-memory authority
is reserialized and must match that canonical digest; needed scalar values are
copied only after the pre-use check and no user callback occurs before child
creation. Direct calls before `_install()`, mismatched path/hash, in-place
nested mutation, replacement objects and post-use mutation are negative tests.
This removes no pre-launch trust boundary: every call is dominated by the full
validator in its process and every reuse is content-checked, not merely
identity-checked.

The focused positive call to the distinct gate
`r232_s15_source_filter_gate._validate_authority()` remains and must still
execute the complete local and runtime closure once. It is not replaced by a
bootstrap receipt. The Stage-1 endpoint replaces its second full runtime-tree
scan only with authority-byte rehash, all authorized local-source rehashes and
the complete shared loaded-module/namespace validator. No file, tree, import,
namespace, cache or endpoint claim disappears.

## Observable progress and hard deadline

Stage-1 stdout remains private until exit because it carries the sole
authenticated final receipt. Stage 0 is the only writer to the stderr stream
observed by the outer monitor. It owns one strictly increasing relay sequence.
Stage 1 writes bounded records to its own captured pipe as a four-byte
little-endian length followed by canonical UTF-8 JSON. Its one relay function
serializes all main-test and isolate start/end events under a preloaded lock;
ordinary unittest text is captured in a bounded in-memory stream and never
shares the frame pipe. Isolated processes retain separate stdout/stderr files;
their three parent threads call the single Stage-1 relay before launch and
after bounded completion rather than writing child bytes concurrently.

Stage 0 alone reads complete length-framed Stage-1 records, validates their
local contiguous sequence and schema, wraps them with the next Stage-0 relay
sequence, and emits each outer `R263_PROGRESS=` line with one prebuilt
single-call write. It emits its own preflight and endpoint records through the
same writer before and after relaying. Unknown length/schema, partial frames,
ordinary bytes on the frame pipe, duplicate/non-contiguous source sequence or
partial-order violation are terminal. The valid order is Stage-0 preflight,
Stage-1 full closure, tests and the three isolated labels, Stage-1 endpoint,
then Stage-0 endpoint. Progress is telemetry only; truncation cannot
authenticate success, and only the sole final Stage-1 and Stage-0 receipts can.

The exact outer launch begins with the frozen inline pre-verifier under the
authority-bound Python executable. Before any gate byte executes, that inline
code reads and hashes the authority, requires its supplied SHA/schema, verifies
its own exact `sys.orig_argv` code bytes against the authority's launcher
SHA-256, verifies the frozen Python executable path/hash, verifies the exact gate path/hash and
only then compiles and executes those already-read gate bytes with frozen
`__file__`, `__name__` and arguments. Its exact command and inline-code hash are
part of the stage-minus-one receipt. The gate's
`--r263-focused-admission` mode repeats those checks, verifies the bootstrap
path/hash and R-263 record, then uses `_run_monitored()` to create Stage 0
suspended, create a fresh kill-on-close Job Object, assign Stage 0, and only
then resume it. The monotonic clock starts immediately before suspended process
creation; assignment-before-resume and the job limit flags are recorded. The outer job permits
exactly eight simultaneous processes: main Stage 0 and Stage 1 plus either the
three isolated Stage-0/Stage-1 pairs or the existing bounded child groups.
Ninth-process creation is a terminal failure, not a reason to raise the limit.

Ordinary completion-port notifications are explicitly rejected as authority
because Microsoft does not guarantee their delivery. While retaining the Job
handle, the monitor instead queries `JobObjectBasicProcessIdList` with resize-
until-complete semantics and `JobObjectBasicAccountingInformation` at launch,
every progress boundary, immediately before termination and repeatedly after
termination. The receipt retains every observed active PID set plus
`TotalProcesses`, `ActiveProcesses` and `TotalTerminatedProcesses`. A process
that starts or exits between queries remains confined to the same no-breakaway
job and changes authoritative accounting; polling continues until both the
complete process list and `ActiveProcesses` are empty. Short-lived historical
descendants need not remain open because they are not survivors and remain
counted in `TotalProcesses`.

Normal work has a fixed 68.0-second deadline. At that instant the monitor calls
`TerminateJobObject(job, 124)` exactly once and continues bounded process-list
and accounting queries. It waits only until 73.0 seconds for an empty complete
PID list and zero `ActiveProcesses`, and closes the
last job handle no later than 73.5 seconds. Because
kill-on-close is set, this is the final tree-wide termination boundary. A zero
pre-close accounting/list pair is the authoritative zero-survivor proof. If it
is still nonzero at 73.0 seconds, the monitor records that terminal failure,
opens wait handles for the final listed PIDs, closes the job by 73.5, and waits
only until 74.5; any process created after the final query remains in the
no-breakaway job and is covered by kill-on-close. It atomically publishes or flushes the terminal
stage-minus-one receipt by 75.0 seconds. Failure of assignment, termination,
query, close, wait, receipt flush or the zero-survivor check is itself a
terminal Run-1 failure. No second kill attempt or unbounded wait exists.

The receipt binds the last complete relay progress record, every retained job
process-list/accounting observation, every Windows call result, stdout/stderr hashes, prefix identities
and entry counts, authority/source identities, and survivor observations. A
larger 85-second shell/Codex timeout is emergency containment only; closing the
monitor process also closes its last kill-on-close job handle, so it cannot
orphan the Stage-0 tree.

The retained timing model is deliberately falsifiable. R-261 required
29.389544 seconds through a failing SciPy import while performing one
`_child_state()` runtime traversal that R-263 removes. R-255's pre-R-257
focused 18-test module required 22.48 seconds. R-263 therefore freezes phase
ceilings of 24.0 seconds through Stage-1 import, 38.0 seconds for the full
26-test body including the one concurrent three-isolate group, and 6.0 seconds
for both endpoints, totaling the 68.0-second work deadline. A progress phase
crossing its individual ceiling is terminated immediately; unused time from
another phase is not borrowed.

## Exact admission gate

Implementation and execution require two independent binary GO verdicts over
the exact R-263 plan. After implementation, two further independent static GO
verdicts must bind every changed source byte before one Run 1.

Run 1 uses fresh Stage-0/Stage-1 prefixes and must satisfy all of the following:

- all 26 focused tests complete;
- all fifteen transactional and three isolated hostile rows reject at their
  intended production checkpoints and preserve their exact semantics;
- every validator-exception restoration and final-state equality check passes;
- the R-262 positive `scipy._external` namespace appears in both ledger and
  loaded records;
- exactly one schema-bound Stage-1 receipt and one accepted Stage-0 receipt
  exist;
- authority, source/runtime trees, loaded closure, default cache, process
  environment and prefix identities are unchanged at their boundaries;
- no hostile side-effect marker, extra process, reused/nonempty prefix, unknown
  progress record, output overflow or survivor exists;
- normal work is at most 68.0 seconds and every process is terminated and
  evidenced within the absolute 75.0-second monitor deadline; and
- memory, output and retained-storage bounds remain unchanged.

Any failure is terminal for this implementation and suppresses Run 2. There is
no retry, timeout increase, reduced test set, reduced authority, or second
remediation cycle.

Only after Run 1 passes may Run 2 use new fresh prefixes. Its deterministic
progress sequence, test outcomes, manifests and authenticated receipt content
must match Run 1 after excluding only explicitly declared process/file
identity and timing fields; it must also remain within 75.0 seconds.

## Falsifiable prediction and scope

Prediction: eliminating redundant pre-matrix closure scans and replacing
fifteen full interpreter launches with exact targeted transactional rows will
complete the unchanged semantic gate within the 24/38/6-second phase ceilings
and the 68.0-second work deadline, with the process tree closed within the
absolute 75.0-second ceiling twice.

Failure to meet any Run-1 condition closes R-263 and leaves R-253/R-255
unadmitted. It does not authorize another evidence redesign. Success admits
only the evidence boundary needed to measure the already implemented,
output-identical R-253 mechanical hoist. It does not admit a codec generation,
change audio, invoke Opus, update `VERSION`, alter Resonith syntax/decoder, or
release Orkela.
