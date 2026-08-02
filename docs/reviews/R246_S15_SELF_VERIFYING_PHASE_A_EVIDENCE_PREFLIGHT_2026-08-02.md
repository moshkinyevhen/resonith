# R-246 S15 controller-bounded Phase-A evidence preflight

Date: 2026-08-02

Status: **DESIGN DRAFT; ALL CODE AND EXECUTION NO-GO**

## Problem and frozen objective

R-243 closed without executing because its only permitted runner remediation
still allowed a directly invoked worker to run without proving the controller's
resource sandbox, rehashed only the base-authority JSON rather than its full
closure after workers, and did not reopen retained stream/PCM/report bytes
against declared identities.

R-246 keeps the unchanged S15 objective: retain one honest short pre-change
timing/profile/golden baseline for the current scalar oracle before any LPC
lifetime-hoist edit. It does not change the codec, decoder, bitstream, accepted
generation or R-198 status.

## Alternatives and falsification

1. **Trust controller ancestry or a nonce.** Rejected. Open-source local code
   cannot turn a caller-selected nonce into a cryptographic authority. Parent
   PID is useful replay/context evidence but not proof of resource limits.
2. **Run workers in-process.** Rejected. It removes the hard memory/process-CPU
   containment and makes a profiling failure contaminate timing evidence.
3. **Treat arbitrary same-user invocation as an evidence security boundary.**
   Rejected as the wrong problem. The same user can import the public codec
   oracle or alter a Job directly. R-246 does not claim to sandbox arbitrary
   hostile local code.
4. **Exact controller as the trust and resource boundary.** Selected. Only the
   exact audited controller command is authorized evidence. It creates each
   child suspended, assigns the child to a bounded Job before resume, monitors
   wall/peak working set/staging/log high-water independently, and alone owns
   terminal publication. The worker request/nonce/PID checks prevent accidental
   role confusion and replay; they are explicitly not authentication.
5. **No change.** Safe fallback if this design fails audit. S15 remains at the
   accepted S12 frontier and no R-243/R-246 evidence is claimed.

## Primary platform basis

Microsoft documents that Job Objects manage processes as a unit and enforce
process-tree limits:
<https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects>.

`JOB_OBJECT_LIMIT_PROCESS_TIME` is a per-process user-mode limit in 100-ns
ticks; process/job memory and active-process limits are exposed in
`JOBOBJECT_EXTENDED_LIMIT_INFORMATION`:
<https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information>.

These Job limits do not prove wall, peak working set, disk or log high-water.
The frozen parent monitor measures those independently and terminates the Job
on violation. No Python daemon thread is described as a hard boundary.

## Minimal coherent implementation

Only the existing `experiments/r243_s15_short_baseline.py` may change, and only
one new authority JSON plus evidence/audit/checkpoint/changelog documents may
be created. The runner remains one file, at most 640 physical lines and 64 KiB.
No helper executable source is authorized.

Before any third-party or codec import, a worker validates the hash-bound exact
request, staging/output paths, one-use marker, parent PID and authority. The
controller launches it suspended and assigns the Job before resume. The Job
sets process CPU, active-process, process-memory, job-memory and kill-on-close;
the parent monitor enforces mode wall, 512-MiB peak working set, 32-MiB staging
and both 1-MiB log high-water limits. The worker branch contains no final rename
or external-failure publication code. Direct worker use is unsupported and out
of the resource-containment threat model; regardless, it cannot create trusted
terminal evidence because only the exact controller owns terminal paths and a
valid receipt binds controller commands and monitor evidence.

## Complete authority and retained-byte closure

After each worker and at final precommit, the controller must call the full
R-232 `_validate_authority`, not merely hash its JSON. This re-expands and
rehashes every local module, selectable bytecode file, Python runtime file/tree,
external-package version and required environment. The controller separately
revalidates R-246 authority, runner, Git and source.

Provenance copying must compare each copied preflight/audit/remediation/runner
byte string with its frozen authority hash and `authority.json` with the CLI
authority SHA. The same checks repeat immediately before publication.

Both workers retain stream, decoded PCM and canonical encoder-report bytes.
The controller reopens each file and requires its size/hash to equal the
worker's declared identity. It also requires the profile rescored identity to
equal the timing rescored identity, validates report schemas, and performs the
independent 128-case golden readback already specified by R-243. All retained
stream, PCM, canonical encoder-report and worker-report bytes are reopened and
revalidated again at the final prepublication boundary after receipt creation.

The terminal success tree has this exact file allowlist; missing, extra or
reparse entries are fatal:

```text
timing-request.json                 profile-request.json
timing-request.consumed             profile-request.consumed
timing.stdout.log                   profile.stdout.log
timing.stderr.log                   profile.stderr.log
provenance/authority.json           provenance/preflight.md
provenance/preclearance-audit.md    provenance/remediation.md
provenance/runner.py                receipt.json
timing/legacy.resonith              timing/legacy-decoded.pcm16le
timing/legacy-report.json           timing/rescored.resonith
timing/rescored-decoded.pcm16le     timing/rescored-report.json
timing/golden-vectors.json          timing/report.json
profile/rescored.resonith           profile/rescored-decoded.pcm16le
profile/rescored-encoder-report.json profile/rescored.prof
profile/cumulative.txt              profile/self.txt
profile/report.json
```

The parent exclusively creates and fsyncs each request. Its worker reads that
request once and exclusively creates and fsyncs the matching consumed marker;
afterward neither side modifies, replaces or removes either file before
terminal cleanup/publication. The worker never opens, truncates, renames or
removes parent-owned logs, provenance or sibling-mode output. Parent logs are
created exclusively and held by the monitor; worker outputs are created once
inside the exact mode directory. Temporary atomic-JSON files must be gone
before the worker exits. The only allowed directories are exactly `.`,
`provenance`, `timing` and `profile`; traversal rejects every missing, extra,
empty or reparse directory and every reparse ancestor/component. After
`receipt.json` is fsynced, the controller recomputes the
complete canonical path-sorted manifest excluding only root `receipt.json` and
requires byte-for-byte equality with `receipt.retained_files`. It then repeats
all semantic golden/profile/report/identity checks, the exact path/reparse
allowlist, authority/source/Git closure and controller deadline immediately
before rename.

After atomic staging ownership, every exception publishes exactly one bounded
owner-only external failure receipt and never renames: worker nonzero/Job
termination, timeout, resource violation, missing/malformed report, identity or
predicate failure, final manifest/readback failure and publication-boundary
failure. It retains failing phase, monitor evidence and exit code, completed
resources, observed medians/call counts/ratio when available, initial and last
validated authority/source/Git identities, and staging cleanup result. A
pre-ownership loser or foreign/pre-existing staging refusal neither cleans nor
publishes. No failed staging contents are silently promoted.

## Frozen execution scope and budgets

Input, configuration, runtime, pair order, profile method, 128 golden vectors,
consistency predicates and 300/180/510-second, 512-MiB, 32-MiB and 1-MiB
budgets remain identical to R-243. Exact paths are:

- success: `G:\Resonith\artifacts\r246-s15-short-baseline-prechange`;
- staging: `G:\Resonith\artifacts\r246-s15-short-baseline-prechange.staging`;
- failure: `G:\Resonith\artifacts\r246-s15-short-baseline-prechange-failure.json`;
- future summary: `G:\Resonith\experiments\results\r246_s15_short_baseline_prechange.json`;
- authority: `G:\Resonith\experiments\fixtures\r246_s15_phase_a_authority.json`;
- per mode under staging: `<mode>-request.json`, `<mode>-request.consumed`,
  `<mode>.stdout.log`, `<mode>.stderr.log`, and output directory `<mode>`.

The only authorized public invocation is the R-243 controller command with the
R-246 authority, authority SHA and exact R-246 success path substituted. A
worker command printed in the receipt is evidence of that controller's child,
not a supported public entry point.

No long control, real-audio corpus, Opus comparison, R-198 run or algorithm
change is authorized. No evidence execution has occurred, so pre-execution
audit findings may be resolved within R-246 until the exact runner and
authority receive two independent binary GO verdicts. Once a workload starts,
there is no blind retry; it publishes exactly one success or failure terminal
state.

## Kill gate

R-246 is rejected before execution if either auditor finds any path from the
authorized controller command to unbounded work, false PASS, cross-run cleanup,
authority drift, incomplete retained-byte reconstruction, or scope expansion.
Arbitrary hostile same-user execution of public Python/codec code is explicitly
not claimed as sandboxed and cannot produce a trusted R-246 receipt. A completed Phase-A result
still must satisfy the three R-243 numerical consistency predicates before any
Phase-B design may begin.
