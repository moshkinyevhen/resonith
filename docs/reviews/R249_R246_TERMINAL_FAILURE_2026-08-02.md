# R-249 R-246 terminal failure

Date: 2026-08-02

Status: **CLOSED FAIL; NO RETRY**

## Result

The exact authorized R-246 controller ran once and published only
`artifacts/r246-s15-short-baseline-prechange-failure.json`, SHA-256
`9946a43d8456c8a3116429c99093d1f60c7caf101ed40418fd8d100f62974393`.
No success directory or orphan staging directory remains. The transaction
cleaned staging and retained a bounded 4,366-byte failure receipt.

Timing completed successfully inside its resource bounds. The profile worker
completed its expensive encode/profile work but exited while formatting the
retained profile: Python 3.14.6 `pstats.Stats` rejected a `WindowsPath` passed
as a filename. It accepts a filename string or a Profile object. The controller
therefore rejected the generation before any PASS receipt or result promotion.

R-246 did not change codec, oracle, decoder, bitstream or accepted generation.
R-198 was not triggered. R-246 may never be rerun.

## Root cause and evidence

The failing expression was:

```python
pstats.Stats(profile_path, stream=stream)
```

The exception was `TypeError: Cannot create or construct a pstats.Stats object
from WindowsPath(...)`. Python 3.14 documentation defines this constructor in
terms of filename(s) or a Profile instance and demonstrates a string filename:
<https://docs.python.org/3/library/profile.html#pstats.Stats>.

## Next gate

A new transaction may change only the call to
`pstats.Stats(str(profile_path), stream=stream)`, rebind the new runner and Git
commit, and retain all R-246 workload, budgets and terminal semantics. Before
execution it requires a focused regression check and two independent binary GO
verdicts over the exact new runner-authority pair.

