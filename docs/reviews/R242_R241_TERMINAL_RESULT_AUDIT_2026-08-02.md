# R-242 independent R-241 terminal-result audit

Date: 2026-08-02

Status: **GO TO REJECT R-232; NO RETRY OR RESCUE**

The independent read-only audit verified the R-241 result document against
the frozen authority, code and atomic failure receipt. No control was rerun
and no file was edited by the auditor.

Verified terminal identities and observations:

- failure receipt SHA-256:
  `02b32e80fefcb9f64f25a3b3b8551fa3c4d69504801823f955282c8edfb415f3`;
- exactly one completed task: incumbent identity, exit zero, 41.904462 seconds,
  job peak 115,732,480 bytes, process peak 138,473,472 bytes and report SHA-256
  `61820bc40f8c0bc7e269622a407bdb4db9cc0aa02d667dfe381e318fc0a89732`;
- first synthetic task: `stable-ar-periodic`, terminated at 900.046130 seconds,
  job peak 278,114,304 bytes, process peak 290,344,960 bytes and staging
  high-water 7,978,108 bytes;
- reconstructed canonical run-index SHA-256:
  `36d834b894379ae4d09611ef8ae2f050eaa744c75fd0278d77859079f0005dce`;
- no final suite, no matching staging orphan and no execution of white-noise,
  impulse or two-component controls.

The frozen preflight requires rejection before real audio on any synthetic or
resource failure and forbids blind retry, threshold/resource retuning, extra
candidates or a larger ceiling. Because no generation was admitted, S16's
complete R-198/Opus comparison is not due and accepted S12 remains unchanged.
A future S15 attempt requires a new theory and independently audited preflight.
