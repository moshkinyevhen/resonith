# R-254 R-253 Phase-B independent dual audit

Date: 2026-08-02

Status: **DUAL GO FOR EXACT IMPLEMENTATION SCOPE ONLY**

## Reviewed identity

- R-253 preflight SHA-256:
  `38dfc62cd8ac68e912a6b5c83b9bb4323ae523dd37aaaf023fae657947dfc277`;
- repository HEAD and origin before the preflight package:
  `d70d73dd66a7b4a18b18b69368cf03aba1148e78`;
- R-250 receipt SHA-256:
  `b28f8d264d183d34a817f0523ec274cb2ac057df66413235e578d295ffedba8d`.

Two independent auditors inspected the current oracle, all direct target and
candidate-synthesis callers, R-243's prospective Phase-B scope, R-250's
dual-audited evidence, and the revised R-253 record. Neither edited files nor
executed codec workload.

## Withdrawn draft

The initial R-253 draft SHA-256
`f6e8243920765b390d0d6916d758683bd14db0a82f70519e9ac94bbe1a8fb804`
is permanently withdrawn. Self-red-team found that it named only the main
encoder subframe loop and omitted the direct desired-target caller in
`_collect_closed_loop_excitation_targets`. Both auditors treated that draft as
NO-GO. No source edit occurred under it.

## Independent findings

Both auditors returned GO on the revised record and verified:

- both `_desired_short_excitation_target` callers are covered, including the
  nonzero-`basis_count` training path;
- the sole production `_synthesize_short_filter_candidate` caller passes the
  same prepared value to every candidate in a subframe;
- `_lpc_q14` is pure over immutable `FilterLaw.reflection_q7`, while unrelated
  analysis, full synthesis, and frequency-weighting call sites remain outside
  this refactor;
- exact `law_count == ceil(source_size / block_size)`, legal interval and
  profile ranges make absolute-to-local mapping total and fail closed on
  insufficient or excess laws;
- with `length <= 512` and `block_size >= 64`, the touched count is at most
  nine; the frozen 65-sample-block maximum witness reaches nine;
- the tuple-of-tuples helper result is per-call and recursively immutable, with
  no cache or cross-input state;
- deterministic gzip level 9 with `mtime=0` produces 56,229 bytes, SHA-256
  `793bff4e748435c079668920a5a2a6cc97b932250bb1bca1df69ed2c6958cc35`,
  and decompresses to R-250 golden SHA-256
  `8fe390457f9baf5226207f2d3c3ebb71c6ba5ac968921cb7e6e145f9b4e8ccf6`;
- implementation and evidence budgets are conservative and no codec, syntax,
  decoder, native ABI, product, player, version, or release change is allowed.

The implementation audit must distinguish helper observations in Basis
training from those in the main loop and bind peak memory to the inherited
timing-worker process peak working-set metric. These are enforcement details,
not additional gates.

## Verdict

**GO** for the exact R-253 implementation only. The R-198 focused mechanical
exception becomes valid only if the implementation audit proves the authorized
diff, independent frozen expected values, no production/report observer state,
complete pre/post identity, conversion-count law, and all CPU/wall/memory
gates. Any failure is terminal NO-GO for this implementation.
