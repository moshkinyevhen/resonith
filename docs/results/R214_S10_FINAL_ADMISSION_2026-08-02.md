# R-214 — S10 final admission

Date: 2026-08-02

Status: **INDEPENDENT GO — S10 COMPLETE**

## Bound source and scope

- Audited branch head:
  `1d0f6e86cded81fd156895574150b4f8f8e4d67b`.
- GitHub checked out PR merge commit `ac17114f52e9395b8174a89f8dfea7348f0932cf`.
  Its tree is identical to the audited head tree, so the evidence is
  current-source exact.
- Production `native/src/partial_graph.cpp` SHA-256 remains
  `ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.
- R-213 changed workflow evidence propagation only. Production source,
  reference behavior, ABI, bitstream, decoded PCM, corpus, and admission
  thresholds did not change.

## GitHub results

- [Tests run 30724305949](https://github.com/moshkinyevhen/resonith/actions/runs/30724305949):
  **SUCCESS**.
- [Mobile Core run 30724305951](https://github.com/moshkinyevhen/resonith/actions/runs/30724305951):
  **SUCCESS**, all nine evidence jobs and aggregate gate.

The Tests run passed Windows x64/ARM64, Linux GCC/Clang/ARM64, macOS ARM64,
Android ARM64 compile, native/Python parity, R-203 replay comparison, and the
independent ASan/UBSan/libFuzzer job.

The Mobile Core run passed Android arm64 compile-link, Android x86_64 API-26
runtime, iOS device arm64, iOS simulator arm64/x86_64, macOS ARM64 runtime,
Linux coverage, TSan, sanitizer/fuzz, and the aggregate artifact index.

## R-203 portable replay identity

All five independent replay artifacts are nonempty valid JSON and report:

- 288 cases;
- 1,620 paths;
- 3,924 entries;
- maximum non-memory work: 573,625 units;
- Class-A semantic SHA-256:
  `eb09e5243dd12525da5f35af42c8bbc5e2731689b98fe74155e38c6c9b8ca0c4`;
- packed-output SHA-256:
  `968019ce7e03fcd49d71d613b771b66bd880b70c8d4ad8a99c40087e43f91401`;
- Class-B non-memory SHA-256:
  `1db3a5ded97c1e29c7db6233e54314b9c5d23fe2cd70060a070b7a93de3d7385`;
- valid locally exact resource telemetry.

The cross-toolchain artifact is 3,619 bytes, has
`replay_count=5`, and has SHA-256
`87d982e368c71cf2cbfc5bb607bec8abd855c49e27b361ac92590c9063acd6d5`.
It compares portable identity while preserving toolchain-specific allocator
telemetry as separate evidence.

## Safety and resource evidence

- Sanitized CTest: 20/20.
- Four fixed fuzz shards: exactly 500,000 units each, 2,000,000 total.
- Per-shard duration: 1,743 / 1,741 / 1,721 / 1,739 seconds.
- Coverage: 4,175 / 4,174 / 4,175 / 4,176 edges.
- Features: 14,434 / 14,412 / 14,413 / 14,435.
- Peak RSS: 477 / 470 / 472 / 473 MiB.
- ASan, UBSan, and LSan findings: zero.
- Stateful reachability: all 11 branches, minimum 100 hits.
- Allocation campaign: 2,864 calls, zero terminal live allocations, trace hash
  `56204c224ae7c4c3`.
- TSan: eight threads and 100,000 independent sequences.
- Adjusted LLVM 18 coverage: 96.35119726339795% lines and
  92.47787610619469% branches, exceeding the frozen 95/90 floor.

## Retained evidence

Local evidence root:

`G:\Resonith\artifacts\r213-s10-final`

The root contains the five platform replays, cross-toolchain result, coverage,
TSan, sanitizer logs, Android/iOS/macOS packages, and the successful mobile run
index. The run-index JSON SHA-256 is
`21ee2c00f07922d14836a1bd54a4edfb2e4dd26dd811046ceb67d50d68681978`.

## Independent verdict

The independent auditor returned final **GO**. No platform, sanitizer,
coverage, ABI, replay, artifact-integrity, workflow-integrity, or
source-identity blocker remains in accepted S10 scope.

## Disposition

- S10 is complete.
- S11 is the next and only active panel step.
- S11 must begin with the R-185 evidence-first brainstorm and independent
  red-team before production behavior changes.
- R-198 music/Opus comparison was not triggered by R-213 because no codec
  algorithm, bitstream, or decoded output changed.

