# R-233 S15 source-filter pre-code audit

Date: 2026-08-02

Status: **INDEPENDENT GO FOR THE FROZEN R-232 IMPLEMENTATION ONLY**

## Audited identities

- planning HEAD: `bc17697bfa9492172995c65c73d15e4ed85b6894`;
- R-232 preflight SHA-256:
  `28f5cddd49a9a1c97c50054533ea85c1d7370da6ff7cdf4051b6d57e5ef32310`;
- canonical configuration SHA-256:
  `b89cae2d09c2c45ba1488e573009a7d822e15998ad4816c7bb45d65ad3cf5d24`;
- source-filter oracle baseline SHA-256:
  `9a69b6d3d6c9fcd8159ef10f6d3306a65ac042087e516ee65c787318137f0abd`;
- source-filter test baseline SHA-256:
  `c352f0fd2d55a9f9ad07f93ff1fe2117e05c446043dd0d2211d0d5596ab50c8f`.

## Audit sequence

Two independent hostile reviews rejected earlier R-232 drafts. Their blockers
were resolved in the final identities above:

1. the experiment now states that it re-ranks only the frozen realized
   candidates and is not jointly decoder-closed RDO;
2. proposal-only original PCM is distinguished from committed decoder state;
3. the 256-sample, 40-band causal local guard is distinct from the complete
   R-216 evaluation;
4. the candidate eligibility, clipping rule, float64 mel error, Q20
   normalization, zero cases, half-even rounding and lexicographic winner are
   executable;
5. the exact R-120 parameters, runtime, seed and one-thread environment are
   sealed in one canonical configuration;
6. long and short speech use the identical configuration with no tuning;
7. later cross-arm candidate divergence is permitted only as the causal
   consequence of a previously different committed winner;
8. the former undefined correction-byte claim is replaced by an explicitly
   untransmitted residual-energy proxy;
9. rate and quality admission tolerances, fallbacks, resource bounds and the
   one-remediation kill gate are explicit.

The final independent reviewer returned binary GO on both exact files and
found no remaining contradiction.

## Authorization boundary

This GO authorizes only the smallest R-232 encoder-policy implementation:

- one final-candidate decoder-domain rescoring option in the existing
  experimental SFT1/EPV1 oracle;
- at most one focused test module and one experiment runner;
- no bitstream, decoder, syntax, product, API or version change;
- no SFT2, five-tap LTP, global interval DP, new candidate family, proposal
  budget change or post-result tuning;
- focused structural and synthetic checks only until a separate independent
  implementation audit returns GO.

The 319.38-second input, short speech, full registered corpus, Opus rerun,
promotion and release remain blocked until their respective later gates.
