# R-219 owner-priority suspension timeout incident

Date: 2026-08-02

Status: **FAIL-CLOSED; RECOVERY AUDIT PENDING**

## Incident

The owner requested an immediate short/long speech and real-time comparison
while the R-219 registered gate was processing `ebu-dense-orchestra`. To avoid
resource contention, the complete R-219 process tree was suspended with native
Windows process suspension, the isolated R-220 speech diagnostic ran, and the
same process tree was resumed.

The existing R-219 S11 timeout uses elapsed wall time. The following
`ebu-dense-pop` worker had already started before suspension, so its unchanged
900-second wall ceiling included the deliberate suspension interval and fired
after resume. The controller stopped fail-closed. This is an operator-induced
wall-clock incident, not codec output or resource evidence.

## Retained state

- Exact run root:
  `G:/Resonith/artifacts/r219-s12-fixed-opus-direct`.
- Exact completed manifest-order prefix:
  `mozart-full`, `ebu-claves`, `ebu-cymbal`, `ebu-dense-orchestra`.
- No Python child survived the fail-closed stop.
- Uncommitted staging:
  `.ebu-dense-pop.staging.8540e78232bc481fab5b2375bf662feb`.
- Staging total: 3,272 bytes.
- `work-request.json`: 2,300 bytes, SHA-256
  `f9b60d12ff4bda9ceca76f11e9bfea767976c4186ab44c15bb2434a003219023`.
- `temporary/s11-request.json`: 972 bytes, SHA-256
  `53ae8ce1062a58a9bedd429d3bf0fbc8d5548df9766aec7c1230f569d76e0615`.
- No challenger stream, decoded WAV, Opus point, receipt, or final item
  directory was produced for `ebu-dense-pop`.

## Proposed bounded recovery

No code, timeout, RSS/disk limit, Opus setting, source, metric, order or run
identity changes. Use the audited controller's existing explicit recovery:

1. first `--resume-existing-run` launch quarantines the leftover staging and
   stops without worker execution;
2. verify quarantine file set/hashes and unchanged run index;
3. second explicit resume verifies the exact completed prefix and reruns
   `ebu-dense-pop` under the original bounds;
4. do not suspend or otherwise interrupt the resumed registered gate.

Recovery remains blocked until an independent auditor issues binary GO.
