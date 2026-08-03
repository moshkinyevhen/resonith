# R-219 direct-comparison implementation audit

Date: 2026-08-02

Status: **INDEPENDENT GO FOR THE EXACT DIRECT COMPARISON**

## Audited identity

- Runner SHA-256:
  `e5f17b7a036cf83b408eebe0b65fb8c21be6da41c3b8343b4d1f2654ab989f54`.
- Focused-test SHA-256:
  `9d441eec34cd8f4a872da26942e941f4d8a1741e679e57808a7d20dadbcbde30`.
- Frozen source revision:
  `64521b19551d4b9688de10fe01c5302607a5beb1`.
- Preflight SHA-256:
  `a651829f324632ae97d07605b75cd46ca307672da8895a4b0da1a04afcb62d57`.

## Independent result

The independent auditor reproduced all 27 focused tests in 2.63 seconds and
issued GO. The prior blocking findings are closed:

- resume accepts only a unique manifest-order completion prefix with exact
  worker-resource, request-seal, and receipt-seal key sets;
- missing or wrong analyzer authority fails closed;
- all four R-217 schemas and the retained actual R-217 output tree fail both
  fresh-start and resume admission;
- Windows authority handles deny cross-process write, file rename/replace,
  and ancestor-directory rename throughout the worker interval;
- request bytes are canonical, independently sealed, retained, and bound to
  the exact manifest item and base-plus-item authority digests;
- the exact Windows host identity is pinned, checked, and retained;
- the emitted aggregate contains only current Resonith and the single fixed
  official Opus 1.6.1 point.

An AST comparison confirmed that the computation-critical S11 verification,
Opus encoding, four-attempt bitrate feedback, fixed configuration, byte-only
selection, official decode, and metric functions are unchanged from R-217
after generation-label normalization.

## Authorization boundary

GO authorizes only the fresh 19-item long-first direct gate using the exact
runner identity above, unchanged registered manifest and unchanged resource
bounds. It does not authorize an Opus-frontier search, a preceding-Resonith
column, S13, promotion, release, commit, or push.
