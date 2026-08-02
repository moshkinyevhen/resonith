# R-250 pstats filename remediation preflight

Date: 2026-08-02

Status: **RECORDED BEFORE CODE CHANGE; EXECUTION NO-GO**

## Objective and alternatives

Objective: preserve the exact R-246 evidence workload while correcting the
single Python 3.14 API-type mismatch proven by R-249.

1. Convert `profile_path` to `str` at the `pstats.Stats` boundary. Selected:
   it matches the documented filename interface and preserves independent
   reopening of the retained `.prof` file.
2. Pass the live `cProfile.Profile` object. Rejected because it would stop
   proving that the dumped retained profile is readable.
3. Change Python or remove text profile reports. Rejected as unnecessary scope
   expansion and evidence loss.
4. Do nothing. Safe fallback if the focused check or audits fail.

## Falsifiable prediction and kill gate

For a tiny independently dumped profile, `pstats.Stats(Path(...))` reproduces
the observed TypeError while `pstats.Stats(str(Path(...)))` loads and prints
both requested orderings. The codec stream, decoded PCM, encoder report,
timing logic and all identities remain byte-equivalent because the change runs
only after profiling and retained stream generation.

Reject R-250 before execution if the source delta is not exactly the intended
filename conversion plus generation/authority identifiers, if the focused
profile check fails, or if either auditor finds scope or closure regression.
The new transaction is one invocation only; no blind retry.

