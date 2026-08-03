# R-218 final-C resource-gate launch incident

Date: 2026-08-02

Status: **FAIL-CLOSED BEFORE ENCODE; RETRY BLOCKED PENDING AUDIT**

## Frozen event

The independently authorized first `ebu-claves` resource repeat used parent
gate SHA-256
`91d910ff7af42ae86b90549c8196dadc34a68b029ea62c9cdcd40fa8c138e6b5`
and the exact required external hash argument. It failed in 0.9 seconds with
child exit code 1. The fresh staging root
`G:\Resonith\artifacts\r218-s11-resource-final-c-claves` remains empty, and no
pinned Python child survived. No S11 analysis, Opus work, codec output or
comparison was produced.

## Reproduced root cause

The parent invoked the identity helper by absolute script path. With inherited
`PYTHONPATH` absent, Python set its import root to `G:\Resonith\experiments` and
the helper failed before argument processing with:

```text
ModuleNotFoundError: No module named 'experiments'
```

A non-encoding `--help` reproduction returned the same exit code and error.
This is a launch-context defect, not an analyzer timeout or resource failure.

## Alternatives and decision

Rejected:

- setting or inheriting `PYTHONPATH`, because it adds mutable environment
  authority and another value that must be frozen;
- blind retry from the failed root, because the fresh-root contract forbids it;
- weakening import or identity checks.

The first proposed module-only launch was then falsified by a non-encoding test:
the package imports legacy top-level module `cibs0` from the repository's
`reference` directory. `python -m` from repository cwd therefore closes the
`experiments` import but not the complete existing dependency graph.

Selected smallest remediation:

1. use pinned Python with `-I -c` and an argv-recorded bootstrap that inserts
   only the resolved repository and `reference` roots, then executes the same
   hashed helper through `runpy.run_module`;
2. retain the helper file hash in pre/post authority exactly as before;
3. include bounded stdout/stderr digests and excerpts in nonzero-exit errors so
   future fail-closed launch incidents remain diagnosable;
4. add a non-encoding isolated-bootstrap launch test, rerun focused monitor
   tests, obtain a
   new independent code-audit GO, and use a different fresh staging root.

No real retry is authorized by this document. The parent-gate hash changes and
must be re-audited and passed literally through a new external hash argument.
