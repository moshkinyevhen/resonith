# R-219 post-R-218 fixed-Opus direct comparison identity preflight

Date: 2026-08-02

Status: **REVISED AFTER INDEPENDENT NO-GO; RE-AUDIT REQUIRED**

## Problem and objective

R-218 immutably committed output-identical S11 acceleration at Git revision
`64521b19551d4b9688de10fe01c5302607a5beb1`. The old R-217 controller correctly
pins the preceding revision and omits the now-material
`complex_partial_analyzer.py` from its run identity. Reusing or bypassing that
controller would invalidate the comparison authority.

R-219 must make the smallest identity-only controller generation that can run
the already selected S12 experiment: current Resonith versus one fixed official
Opus 1.6.1 anchor across the unchanged registered 19-item long-first corpus.
It must not search for a better Opus configuration and must not add a preceding
Resonith comparison column.

## Frozen baseline and costs

- source revision:
  `64521b19551d4b9688de10fe01c5302607a5beb1`;
- analyzer SHA-256:
  `c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c`;
- predictor SHA-256:
  `583daeee36190389d98278c2f0927db28e4d3423f0de9252e23c0226e790f1ec`;
- R-216 imported controller SHA-256:
  `316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3`;
- metric helper SHA-256:
  `ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3`;
- registered manifest SHA-256:
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`;
- native core SHA-256:
  `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed`;
- Python executable SHA-256:
  `03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38`;
- official `opusenc`/`opusdec`: unchanged local libopus 1.6.1 authorities
  already frozen by R-216/R-217;
- R-218 authoritative short-item S11 evidence: claves 193.272769 seconds,
  cymbal 229.107934 seconds, unchanged complete payload and PCM identities.

The complete run retains the existing eight-hour controller ceiling, per-item
worker limits, 12/8 GiB RSS limits, 8/2 GiB item staging limits, 24 GiB retained
root limit, atomic receipts and long-first ordering. No limit increases are
authorized.

## Alternatives and falsification

### A. Reuse R-217 unchanged

Rejected. Its source-revision guard must fail on the R-218 commit, and analyzer
identity is absent. Disabling either guard would make the evidence weaker.

### B. Resume partial R-217 output

Rejected. Mozart/claves were produced under an older run identity and cannot be
mixed with post-R-218 receipts. They remain diagnostic only.

### C. Search the Opus frontier again

Rejected by the owner. R-219 uses exactly one fixed official point; it does not
claim an exhaustive optimum over every legal Opus setting.

### D. Identity-only R-219 generation

Selected. Preserve all R-217 encoding, decoding, metric, byte-matching,
ordering, atomicity, resource and comparison behavior; change only generation
schemas/error labels, frozen source/preflight identities, and explicit analyzer
authority.

## Smallest coherent implementation

1. Create `experiments/r219_s12_fixed_opus_direct.py` from the audited R-217
   controller with no algorithmic edits.
2. Give run, receipt, runner and work-request schemas new `r219` identities and
   use R-219 error labels so stale R-217 artifacts cannot validate.
3. Pin `EXPECTED_SOURCE_REVISION` to the exact R-218 commit above.
4. Add `reference/maf_p0/complex_partial_analyzer.py` to `_identity_files`,
   require its exact SHA-256, carry it into controller material and every worker
   request, and reject any pre/post drift.
5. Pin this preflight's final SHA-256 and accept the R-219 runner hash only via
   the existing external `--audited-runner-sha256` authority.
6. Create `tests/test_r219_fixed_opus_direct.py` by preserving all R-217 tests
   and adding negative tests for missing/wrong analyzer identity, old revision,
   old schema/receipt and any attempted preceding-Resonith column or Opus
   frontier path.

## Independent NO-GO and sealed-execution remediation

The first independent audit rejected the model before code for two reasons:

1. a mutable request could preserve `item_id` while changing an algorithmic
   field such as challenger budget or categories;
2. pre/post analyzer hashes could miss a change-use-restore ABA mutation while
   the separately spawned S11 child was running.

The following controls are therefore part of the smallest coherent R-219
generation, not optional follow-up work.

### Exact request seal

The controller serializes one canonical request byte string, writes those exact
bytes, hashes them, and passes the SHA-256 separately in worker argv. The worker
must read the request once as bytes, compare the hash before parsing, and parse
that same retained byte buffer. The receipt carries both the exact request seal
and a canonical frozen-manifest-item SHA-256. The controller verifies both
against its own current manifest item before accepting the receipt and records
both in the run index. A resume may trust neither a self-declared receipt seal
nor `item_id` alone.

### Immutable execution interval

This evidence controller runs on Windows and must fail closed elsewhere. Before
launching each worker, the parent opens deny-write/delete handles that still
permit reads for:

- every file under `reference` named by `git ls-tree -r` at frozen revision
  `64521b19551d4b9688de10fe01c5302607a5beb1`;
- the R-219 runner, imported R-216 controller, metric helper and
  `objective_audio_metrics.py`;
- the native core, pinned Python executable, `opusenc`, `opusdec`, registered
  manifest, corpus/report authorities and the current source WAV.

The expected static rows form `base_authority_set_sha256`; the ordered nineteen
manifest-bound source rows form nineteen expected
`item_authority_set_sha256` values. Run material stores the base digest and the
complete item-ID-to-digest map. Each request and receipt stores that base digest
plus exactly its own item digest. All handles are acquired before the worker is
created, remain held across the nested S11 and Opus work, and are released only
after worker exit, receipt verification and a final hash snapshot. Windows
mandatory sharing denies write and delete, so a different
process cannot perform analyzer or dependency change-use-restore while the
worker uses them. Any missing file, reparse point, lock failure, postflight hash
drift or close failure is fatal. A temporary-file mutant must prove that a
second process cannot write, replace or delete a locked authority during the
interval and can do so only after release.

This locks the declared imported authority set rather than merely the analyzer, avoiding
a false proof in which another Python dependency is substituted instead.

The term used by R-219 is **declared project/tool/input authority set**, not
"full execution set". Python standard-library and installed site-package bytes,
Windows system DLLs, kernel and drivers remain a frozen-host assumption checked
by exact Python/tool hashes plus dependency and OS versions; R-219 does not
claim byte locks over the entire operating system. This limitation is recorded
in run material and the final report.

### Fresh start and explicit resume

The default first launch requires a nonexistent output root; the controller
creates it and verifies every component below it is contained and reparse-free.
Resume requires an explicit `--resume-existing-run` flag plus an existing exact
R-219 run index, identical run/execution identities and complete indexed
receipt seals. Empty existing roots, unindexed item directories, R-217 indices
or receipts, mismatched schemas and mixed run identities fail closed. R-219
never adopts a directory merely because its `item_id` looks current.

### Canonical authority-set construction

One function constructs one sorted base map from normalized absolute path to
SHA-256. It is the only source for static locks, the base authority-set digest,
controller material, worker request and receipt verification. Its inputs are:

1. every exact `_identity_files` authority, explicitly including the R-219
   preflight, analyzer, predictor, `objective_audio_metrics.py`, registered
   manifest and all reports/tools already frozen by R-217;
2. every regular file returned by one `git ls-tree -r --name-only` query for
   `reference` at the frozen committed revision.

Duplicate normalized paths must carry the same expected hash or fail. Missing,
non-regular, reparse or outside-declared-root paths fail. The same sorted rows
are hashed canonically for `base_authority_set_sha256`; no separately
maintained static lock list is permitted.

Each registered manifest item then derives exactly one sorted per-item map by
adding that item's current source WAV row to the unchanged base rows. Its digest
is `item_authority_set_sha256`. Run material stores the base digest and the
ordered map from every registered item ID to its expected per-item digest. Each
request, receipt and index entry stores and verifies both the base digest and
its own per-item digest. No singular digest is permitted to ambiguously mean
both the run-wide base and a current source-specific set.

The run identity and initial run material are computed once before any item
executes, using the frozen expected base rows and all nineteen expected source
hashes from the registered manifest. They are never derived or rewritten from
per-item observations. For each item, the under-lock observed base and per-item
rows/digests must equal those already committed expected values before request
creation; observation cannot redefine run identity.

For every authority file, the parent also opens deny-delete handles on every
resolved ancestor directory through and including its declared containment
root and that root's parent using `FILE_FLAG_BACKUP_SEMANTICS`. File and
directory handles remain live until
postflight verification. This closes the path-swap case in which an old file
handle remains valid while Python later opens a replacement tree by name.

The per-item staging directory is created before authority locks are acquired;
the request file is not. All worker outputs stay within that precreated staging
directory. After verified worker exit, locks are released before the already
verified staging directory is atomically renamed to its final item name.

The acquisition and observation order is normative:

1. derive expected hashes only from frozen constants, committed-tree entries
   and the registered manifest; resolve and validate every path and ancestor;
2. acquire all unique ancestor-directory handles in deterministic sorted order,
   then every base-authority and current-source file handle in deterministic
   sorted order;
3. only while all handles are live, hash every path (or the retained handle),
   compare each value with its expected authority, and construct the canonical
   base and per-item digests from those under-lock observations;
4. only then serialize/write/seal and lock the exact request, launch the worker
   and retain all handles through receipt verification;
5. postflight rehash every authority while all handles remain live and require
   exact equality before release and atomic rename.

A focused synchronization mutant must alter an authority after initial path
enumeration but before its file lock is acquired; the subsequent under-lock
hash comparison must reject it before worker creation. Hash-before-lock evidence
alone is invalid.

### Retained request and crash boundary

`work-request.json` is permanent evidence, not deleted and not excluded from
verification. Its exact bytes, size and SHA-256 are included explicitly in the
receipt and retained-file manifest. Resume recomputes request bytes, canonical
manifest-item hash, base authority digest, item authority digest, receipt hash
and matching index entries before accepting a completed item.

After request bytes are sealed and before worker creation, the parent also
holds a deny-write/delete handle on the request itself through worker exit and
postflight hash verification. It is kept outside the base authority-set digest
to avoid a circular request-hashes-itself definition; its independent argv seal
and retained hash are the authority.

If staging was renamed to a final item but the index update did not commit, the
unindexed directory is quarantined and the controller stops. It is never
adopted, even if its contents are otherwise self-consistent. Recovery requires
separate evidence review rather than automatic trust.

## Fixed comparison point

For every item, Opus remains official libopus 1.6.1 with `opusenc` complexity
10, true VBR, 20 ms frames, zero expected loss, 1000 ms maximum delay, default
phase inversion, zero padding, discarded comments/pictures and deterministic
serial. Only the exact registered `speech` class uses `--speech`; all other
items use `--music`. Four bitrate-feedback encodes adjust only bitrate to match
the complete Resonith byte count; they do not search mode, frame size,
application or another codec option. Selection occurs by complete-byte distance
before quality is inspected. Official `opusdec` and the Resonith Golden Core
produce the compared PCM.

This is a fixed direct anchor, not a claim that every possible Opus parameter
combination was globally optimized.

## Admission and kill gates

1. Independent auditor must issue written GO on this exact preflight before
   controller code is created.
2. Diff from R-217 may contain only: new R-219 schemas/error labels; frozen
   source/preflight/analyzer identities; the one canonical base authority set,
   its digest and the ordered nineteen expected per-item digests; mandatory
   file/ancestor-directory lock lifecycle; sealed and
   retained exact request bytes plus canonical item hash; explicit fresh-start
   versus same-R-219 resume/quarantine behavior; and focused tests for those
   controls. Any codec, Opus command, metric, byte selection, manifest content,
   item order, timeout or resource-limit difference is NO-GO.
3. Focused tests must prove analyzer authority is present in controller material
   and worker requests, wrong/missing analyzer identities fail closed, sealed
   request mutation with unchanged `item_id` fails, base and per-item digests
   have unambiguous membership and change with analyzer/source bytes,
   hash-before-lock mutation is rejected before worker creation,
   deny-write/delete locking prevents an ABA mutation,
   cross-process file and ancestor-directory rename/swap attempts fail while
   handles are held and succeed only after release, an actual R-217
   index/receipt tree cannot start or resume, all four old schemas fail, and no
   preceding-Resonith result or Opus-frontier command is emitted.
4. The final runner and tests receive an independent narrow audit. The literal
   runner SHA-256 must be passed externally.
5. The first-launch output root must not exist and must be distinct from every
   R-216/R-217 diagnostic root. Only explicit same-identity R-219 resume is
   allowed under the sealed rules above; no prior item may seed it.
6. Run all 19 registered items in unchanged long-first order. Each item commits
   atomically only after source, stream, decoded PCM, complete bytes, metrics,
   tool identities and resources validate.
7. Any timeout, RSS/disk breach, identity drift, orphan, invalid receipt,
   unmatched complete-byte point or metric failure is retained and reported;
   no blind retry or bound expansion is allowed.
8. The aggregate report compares only current Resonith with the fixed Opus
   anchor, publishes every per-file win/loss/fallback and makes no general
   superiority claim without the complete gate and later listening evidence.
9. R-219 completion closes S12 evidence only. S13 remains blocked until the
   aggregate direct report passes and receives independent closeout.

This preflight authorizes no code, run, commit, push, promotion or release until
the required independent verdict is recorded.
