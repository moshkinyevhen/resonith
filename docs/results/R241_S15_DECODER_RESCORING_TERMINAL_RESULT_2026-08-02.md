# R-241 S15 decoder-rescoring terminal result

Date: 2026-08-02

Status: **INDEPENDENT GO-TO-REJECT; NO ADMITTED GENERATION**

## Outcome

The exact independently authorized R-240 suite executed once. The corrected
pre-S15 incumbent identity passed. The first synthetic control,
`stable-ar-periodic`, then reached the frozen 900-second worker ceiling and was
terminated. Stop-on-first-failure prevented `white-noise`, `impulse` and
`two-component` from running.

R-232 is rejected in this Python decoder-domain rescoring form. The ceiling is
not raised, the control duration/candidate lattice is not reduced, and no
result is inferred for the unfinished arm.

## Terminal evidence

- failure receipt:
  `G:\Resonith\artifacts\r240-s15-controls-failure.json`;
- repository copy:
  `experiments/results/r240_s15_control_failure.json`;
- failure receipt SHA-256:
  `02b32e80fefcb9f64f25a3b3b8551fa3c4d69504801823f955282c8edfb415f3`;
- authority SHA-256:
  `bb14ad62772a7fe71530fe2a99ddbf127cd6a095b84a7aa1fc8006e7295cc29e`;
- runner SHA-256:
  `53af4e1f85341b6d29661003d7e18144d40cc2cf64679463c2da9f20f738670e`.

Incumbent identity completed in 41.904462 seconds. Its worker exit code was
zero, job peak memory was 115,732,480 bytes, process peak working set was
138,473,472 bytes, and its report SHA-256 was
`61820bc40f8c0bc7e269622a407bdb4db9cc0aa02d667dfe381e318fc0a89732`.

The rejected first control reached 900.046130 seconds. The monitor recorded
job peak memory of 278,114,304 bytes, process peak working set of 290,344,960
bytes, staging high-water of 7,978,108 bytes, empty stdout/stderr and no
unbounded child process. The failure receipt retained the last run-index hash
`36d834b894379ae4d09611ef8ae2f050eaa744c75fd0278d77859079f0005dce`.

No final suite directory or staging orphan exists. The external atomic failure
receipt is the sole terminal publication.

## Baseline correction retained

The preceding R-238 identity failure was a stale EPV1 envelope fixture, not an
S15 algorithm result. The historical 12,548-byte EPV1-v2 stream SHA-256 is
`8fb84a3a...`; clean pre-S15 commit
`5aff74dbce41d7dece102a10f7ff326d7a700dda` and the rescoring-disabled arm both
produce the 12,554-byte EPV1-v3 stream SHA-256 `f0c3abf0...`. Both decode to
WAV SHA-256 `b105da97...`. The exact six-byte difference is three bounded
uint16 Basis header fields introduced before S15.

## Admission consequence

- no R-232 codec generation is admitted;
- no syntax, decoder, default, version, release or product behavior changes;
- no complete corpus or Opus comparison is run because no algorithm generation
  passed the precursor resource gate;
- the accepted S12 frontier remains the incumbent;
- any new S15 attempt requires a new theory/preflight and must eliminate the
  Python per-candidate synthesis/FFT cost structurally, preferably through a
  bounded native batched implementation rather than a larger time limit.

R-242 independently replayed the terminal receipt, identities, task order,
run-index digest, cleanup state and preflight kill clauses and returned
GO-to-reject with no blocker.
