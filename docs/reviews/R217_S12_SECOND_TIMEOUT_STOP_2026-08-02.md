# R-217 S12 second timeout and mandatory stop

Status: **R-217 FULL CORPUS STOPPED; LIMIT INCREASE FORBIDDEN**

## Second run

- Output root: `G:/Resonith/artifacts/r217-s12-fixed-opus-direct-v2`.
- Run identity: `68ee12a3560fab4bbe16969dc85488bdddace28913d4330e08770a10f558a6c3`.
- Frozen runner SHA-256:
  `12d615b5401654ed1a498f06464b4da90b539b8fff9252d42682932374a633a3`.
- Full Mozart passed again; receipt SHA-256:
  `5ec009f13100f92130819fb771c150f9383b5a8c7aaa615aafe1dbbbb24236bf`.
- `ebu-claves` passed in 800.877559 seconds; receipt SHA-256:
  `0e953f81b77f19a2087a47fe48817868931c93e5948a999a074aeba5c459324d`.
- `ebu-cymbal` then exceeded the exact redesigned 900-second S11 ceiling.
- The timeout occurred without an RSS/disk breach, stream, receipt, or orphan.
- The controller was not retried and no second ceiling increase is permitted.

## Preserved failed staging

The exact failed staging was atomically renamed inside the v2 root to
`quarantine-ebu-cymbal-timeout-900s-96e5a453e9f04fd9af8a6fe1cfa985a1`.
It contains exactly 3,009 bytes:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `work-request.json` | 2,044 | `11bb92066060f49974c56ce6d828997a5d8fd9ccc8df01aa2a9e5c23a3833475` |
| `temporary/s11-request.json` | 965 | `3aae111308a6f18d94ed9f6f9203cbe16d0cf26bf6c543df332e568c5a96dc65` |

## Evidence disposition

The completed Mozart and claves receipts remain valid direct fixed-Opus
evidence. They do not constitute the complete 19-item S12 gate and do not
authorize S13, promotion, or a general Opus claim.

R-211 now forbids another automatic timeout increase. S12 can resume only
after an independently audited performance redesign that preserves the S11
candidate language, search set, selection, encoded bytes, decoded PCM, and
all resource/security behavior while making the existing 900-second bound
sufficient, or after an explicitly owner-approved scope reduction. A faster
but non-identical search is a new algorithm generation and cannot be hidden as
evidence remediation.
