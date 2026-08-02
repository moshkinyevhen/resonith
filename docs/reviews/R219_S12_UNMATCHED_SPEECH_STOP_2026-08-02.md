# R-219 unmatched female-speech stop

Date: 2026-08-02

Status: **FAIL-CLOSED; R-219 COMPLETE GATE STOPPED**

## Result

After the owner-priority suspension incident was quarantined and the exact
R-219 run resumed, `ebu-dense-pop` and `ebu-electronic-tune` committed under
the original limits. `ebu-female-speech-en` then completed Resonith S11 but
the fixed four-attempt Opus bitrate feedback did not enter the strict
complete-byte tolerance. The worker emitted `UNMATCHED` and exited 3; the
parent stopped without accepting the item.

- Resonith target: 94,816 complete bytes.
- Strict tolerance: 94 bytes.
- Opus attempts `(q5, bytes, delta)`:
  - `(6,321,067, 97,683, +2,867)`;
  - `(6,135,543, 90,267, -4,549)`;
  - `(6,444,743, 99,635, +4,819)`;
  - `(6,133,033, 90,267, -4,549)`.
- Failed receipt SHA-256:
  `9e1d39ba94ebfc32cb129ac4b9398931371fe85a7daea9a7b63f080753fda232`.
- Resonith payload SHA-256:
  `a39f23f452cb9e6f2d3fde0883060412146c1ebe9fe2b160922f05b4a612adf2`.

No Opus point was decoded or quality-scored, no item was committed, and no
limit was expanded. The evidence shows a usable bitrate bracket inside the
same fixed Opus configuration; it does not justify an Opus configuration
frontier.

## Consequence

R-219 remains retained diagnostic evidence and cannot close S12. Repeating the
same four deterministic attempts would reproduce the same stop and is
forbidden as a blind retry. A new audited controller identity is required for
any bounded rate-only matching remediation.
