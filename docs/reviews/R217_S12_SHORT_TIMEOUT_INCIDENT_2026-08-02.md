# R-217 S12 short-analyzer timeout incident

Status: **FAILURE PRESERVED; ONE BOUNDED REDESIGN AUTHORIZED**

## Observed run

- Output root: `G:/Resonith/artifacts/r217-s12-fixed-opus-direct`.
- Run identity: `a9a68674d170b2fd5a04b8ba0ecb19201c59a7640edcfb8a1af8dbf419986849`.
- Full Mozart passed and was atomically committed in 356.707504 seconds.
- Mozart receipt SHA-256:
  `99a0fcf1624860554331dfea6119918d77636586bf2b12c1cfa9b5fbe61123ef`.
- The next item, `ebu-claves`, stopped at the exact 420-second S11 child
  ceiling before producing a codec stream or receipt.
- No RSS or disk ceiling fired and no codec process remained alive.
- The controller was not retried with the same limits.

## Preserved failed staging

The exact failed staging directory was atomically renamed inside the old root
to `quarantine-ebu-claves-timeout-420s-425c9ea8a6924a6793c903ff3648e67c`.
It contains exactly 2,998 bytes:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `work-request.json` | 2,040 | `a23709a084173617213ea4853b353582e30126bf32336b02a9a9bcb971afa8b4` |
| `temporary/s11-request.json` | 958 | `b3c10f53827f2b9c3650835761212020a20e5ac6be634cd75eba845d86cc3561` |

## Bounded-redesign evidence

- `ebu-claves` analyzer bound: 782,064 observations.
- Short speech smoke analyzer bound: 92,544 observations and 40.89 seconds.
- Bound ratio: 8.45; linear timing estimate: approximately 346 seconds.
- The 420-second empirical lower bound proves that the original short ceiling
  was insufficient on this host.
- A 900-second S11 ceiling is 2.14 times the observed timeout and about 2.6
  times the linear estimate.
- A 1,200-second outer short-item ceiling leaves 300 seconds for two metric
  passes, four feedback encodes, one deterministic repeat encode, and decode.
- Worst declared schedule is 35 minutes plus 18 times 20 minutes, or 395
  minutes, leaving 85 minutes inside the unchanged eight-hour run ceiling.

## Authorized change and stop rule

The independent auditor authorized exactly one redesign:

- short S11 ceiling: 420 to 900 seconds;
- short outer worker ceiling: 600 to 1,200 seconds;
- all algorithms, Opus configuration, corpus, long-item limits, RSS, disk, and
  complete-run limits remain unchanged;
- use a new output root and run identity; do not import or continue the old
  Mozart receipt.

A second timeout or resource-budget breach in the same claim stops R-217 for
independent redesign. It must not trigger another silent ceiling increase.
