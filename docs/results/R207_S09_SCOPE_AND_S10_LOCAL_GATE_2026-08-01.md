# R-207 S09 scope correction and S10 local public-ABI gate

Date: 2026-08-01

Status: **S09 INDEPENDENT GO; S10 LOCAL PASS WITH REMOTE/CAMPAIGN GAPS**

## Scope correction

The unimplemented R-205 private telemetry ABI, record-ID state machine, LPAC
harness, randomized oracle, and recursive authority chain are withdrawn rather
than admitted. Compiled native C/C++ sources contain zero definitions of the
proposed private symbols. Creating that ABI only to test it would not validate
existing production behavior.

All R-205 artifacts remain immutable negative research evidence. This report
makes no private-state, sandbox, anti-hardcoding, codec, compression, quality,
bitstream, PCM, or player claim.

Production `native/src/partial_graph.cpp` remained unchanged at SHA-256
`ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.

## Frozen replay inputs

| Object | Cases/bytes | SHA-256 |
|---|---:|---|
| exact-small JSONL | 9,024 / 55,085,390 | `1bf354dafa223f4350b79719e9e138df2262c52f22ce51a6d028eb4e56d3a306` |
| exact-small inventory | 345 | `31a33f1c7dec75147134b7c3241f67cc9ecc597c0579da61516511aadb69d6bb` |
| candidate-rich JSONL | 288 / 3,111,742 | `fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7` |
| candidate-rich inventory | 2,155 | `ba120afa8b437c476b5548935b210e4406a734e09a80554f67abf615c667c957` |
| Clang 22 shared core | 1,185,792 | `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed` |
| GCC 16 shared core | 1,010,445 | `425a58feefc34cead230dbdc838d1b8c24aa29fecc269b96e4a700c47df784e7` |

## Replay results

Both native binaries replayed every corpus twice through the actual public ABI.

| Evidence | exact-small | candidate-rich | Cross-toolchain |
|---|---:|---:|---|
| cases | 9,024 | 288 | equal |
| paths / entries | 0 / 0 | 1,620 / 3,924 | equal |
| maximum work units | 33,479 | 576,097 | equal |
| maximum host bytes | 2,104 | 25,892 | equal |
| semantic SHA-256 | `cf48eaa...1ec2a` | `d8b4c3aa...9e92b` | equal |
| Class-A semantic SHA-256 | `3448fc97...aa8b7` | `eb09e524...a0c4` | equal |
| Class-A packed SHA-256 | `f1f540a9...014d2` | `968019ce...1401` | equal |
| Class-B non-memory SHA-256 | `00090a1f...4243` | `1db3a5de...7385` | equal |
| resource telemetry locally valid | true | true | yes |

Machine outputs:

- `clang-exact.json`: SHA-256
  `9cac2d5d900ddd341a06c78c70d1f8155e39363a77100ec9fa7063f6fdb7ff53`;
- `gcc-exact.json`: SHA-256
  `0b529aa943104d187f99e63a4f786920626de28550acf7bf0dd4e55209330ea9`;
- `clang-candidate.json`: SHA-256
  `c59877dfa608d684f379bb0c5bfee3025d2ed77ea653117f5d0db3d116326d15`;
- `gcc-candidate.json`: SHA-256
  `6cdebba3c0adefb1fb66081e6040f8431051f4856bb42201d6b82d5e8e01b10d`.

## Existing conformance and oracle gates

- Clang CTest: 20/20 passed in 10.95 seconds; raw SHA-256
  `b41dce641d6e447c39df26f62ee507e78456c133c53308060c54ba130eccf048`.
- GCC partial-graph scope: 5/5 passed in 11.54 seconds; raw SHA-256
  `d2b7f86b001ad8b3d20494395dfd18d2f417fdb661ce8e246677013312f6b581`.
- Independent Python R-191/R-197/R-203 oracle: 78/78 passed in 19.44 seconds;
  raw SHA-256
  `7a5b2982f6ac821cc069c1292bbcaa7036fba92febdf24d390525f5d645061cf`.

The GCC aggregate attempt is retained as rejected evidence, SHA-256
`7b464edd4d2b87ff577672f9b987d72c32da8a8f3ef0024472f79b8e2249e12d`:
six relevant built tests passed, but thirteen unrelated targets were not built,
so the aggregate correctly did not pass. It was replaced only by the declared
partial-graph regex, not reported as a full GCC CTest pass.

## CUDA parity

A clean Clang 22 C++23 CUDA-Foundry target was built without source changes.
Its executable is 1,085,952 bytes, SHA-256
`7a98fccdcf2eb2900a00ec15c9c388680bcec54aa88ab223287978a7e8487778`.

On NVIDIA GeForce RTX 2080 Super, compute capability 7.5, NVRTC 13.3:

- tile sizes: `1/31/32/255/256/1024`;
- randomized partial cases: 32;
- randomized partial edges: 330;
- `cpu_gpu_exact=true`;
- known transform and warp recall: true.

Raw CUDA result SHA-256:
`d2aa69d4acc2dba9bf36ad58fbead575ca3f3a8bc6b348274f10f9a6daaeb177`.

Two earlier invocations passed a DLL path where the API requires its directory;
they failed before CUDA work and are not parity results.

## Released-codec identity

Previously retained baseline/current pairs were rehashed. Speech and Mozart 3 s
bitstreams and decoded WAVs remain byte-identical:

| Object | Bytes | Shared SHA-256 |
|---|---:|---|
| speech `.resonith` | 17,929 | `a85b1308a252714298f9ac5155d29c45b7a763275a28eef88fcc38ffd3042e80` |
| speech decoded WAV | 187,404 | `eb34cdfb899ce76bf8e20a9d8260c021f6f6ca3d300c16c535eb8b654e5e6ce5` |
| Mozart 3 s `.resonith` | 42,115 | `6004642e739bf5043b25be748b0ee1feb54d04df86f98e97cafe4f79eebe449c` |
| Mozart 3 s decoded WAV | 576,044 | `c0f6dcfb0c5466b11dc2bde87b006fed3e88a7e9f2da52965849add032b111aa` |

No algorithm changed, so no new music/Opus quality claim is possible or needed.

## Honest remaining S10 gaps

S10 is not admitted locally. Remaining evidence is:

1. current-source MSVC, ARM64, Android, and Apple replay through CI or native
   platform runners;
2. ASan/UBSan/libFuzzer on a supported non-Windows target; Clang/MinGW reports
   `-fsanitize=fuzzer` unsupported and that attempt is not a sanitizer result;
3. resolve the old proposed 10,000-case CPU plus six 10,000-case CUDA campaign:
   either run a separately audited existing implementation or independently
   supersede the unimplemented numeric target; the current 32-case CUDA gate
   must not be relabeled as 60,000 cases;
4. one independent final source/result GO/NO-GO.

All raw local outputs are retained under
`artifacts/r207-s10-20260801/`.

## Independent audit disposition

The independent result audit returned **NO-GO for closing S10** while accepting
the S09 scope correction and the local public-ABI evidence exactly as bounded
above.

The inherited `10,000` CPU plus six `10,000` CUDA count is superseded. Its
reproducibility did not establish scientific necessity: no power analysis,
coverage-convergence result, mutation-score relation, or defect-detection
rationale justified that number. The 32-case CUDA result remains only a narrow
local pass and is not promoted.

The replacement CUDA gate is one frozen structural parity manifest containing:

- twice-run CPU ABI equality to the frozen canonical union for all 288
  candidate-rich cases;
- twice-run CUDA parity for the 252 cases with `2/4/6` edges at every thread
  value in `1/31/32/255/256/1024`;
- expected `INVALID_ARGUMENT` for the 36 zero-edge cases, because zero work is
  not a positive CUDA invocation;
- public-valid boundary graphs whose complete unions are produced by the CPU
  ABI, covering exact reachable or deterministically selected nearest
  lower/upper counts around `T-1/T/T+1/2T-1/2T/2T+1`, capped at `2049`;
- no-match, single-chain, branch/merge, ownership-conflict, phase, and
  protected profiles;
- negative `threads=0/1025`, output-capacity precedence, malformed inputs, and
  one valid contiguous-candidate-ID permutation;
- twice-run bit-exact CPU/CUDA output and stable hashes;
- a status-reachability registry distinguishing direct, environment-dependent,
  fault-injection-only, and safely unreachable statuses, including the exact
  expected output/evidence mutation law for each exercised failure.

The true resource maximum is deliberately excluded from this structural gate
and remains a separate resource-limit obligation.

S10 also still requires current-source remote MSVC x64, Windows and Linux
ARM64, Linux sanitizer/fuzzer/thread-sanitizer, Apple ARM64, Android ARM64, and
iOS simulator public-ABI evidence; exact platform-independent semantic hashes;
an artifact inventory binding commit, commands, tools, raw outputs, hashes, and
exit codes; and one final independent source/result GO/NO-GO.

No private record/state ABI is required or authorized by this disposition.

## R-208 structural CUDA result

The standalone test-only harness is 18,684 bytes (495 lines), SHA-256
`a7ef8d91ff00202620b12888362094b0394ef9093c9aca7c9f841ed6e4ddc60e`.
The retained machine result is 1,617 bytes, SHA-256
`abd5d67780b3efb87380b65e9e1ed13f80fb3b5f938722e89a231155e8266d81`.

The local run passed in 19.264 seconds. An independent clean rerun passed in
16.557 seconds and reproduced every retained semantic hash:

- 288 CPU/frozen unions, each twice;
- 252 nonzero cases through three projection-audited batches, all six CUDA
  thread counts, each twice;
- 36 zero-edge cases returning `INVALID_ARGUMENT`;
- 33 exact public-CPU-produced boundary pairs through count 2049;
- thread, capacity-precedence, malformed-observation, valid-permutation, and
  output/evidence mutation laws;
- truthful direct, environment-dependent, fault-injection-only, and safely
  unreachable status classification.

Independent verdict: **GO; the R-208 structural CUDA obligation passes**.
The old random-count target remains superseded. Production
`native/src/partial_graph.cpp` remains SHA-256
`ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.

S10 remains open only for current-source remote platform and sanitizer/fuzzer
results, explicit ABI-layout/v2-no-write/fingerprint-mutation/publication-
atomicity evidence, the final bound artifact inventory, and one independent
S10 source/result GO/NO-GO.

## R-209 focused ABI obligation result

No new test code was required. Existing compile-time and executable coverage
was run as a separately named evidence package:

- Clang: 7/7, raw SHA-256
  `de3a9122f7fc907215e058d3de4126335059de44fd248b9d5b7c329877747201`;
- GCC: 7/7, raw SHA-256
  `627a183b1011a612f0084aaaf93b7da75c476e6e57d083c411f210da93fdab15`;
- Python ABI layout bridge: 1/1, raw SHA-256
  `28f78c73388cc9fc22aa2874be8907e82173340b7c13e240cf76b0ae94a10348`.

The independent audit returned **GO** for all four local obligations:

- C/C++/Python size and offset layout agreement;
- exhaustive `2^13 = 8192` retired-v2 no-write combinations;
- missing, stale, and changed-input fingerprint rejection with bounded report
  publication and unchanged caller payload;
- capacity, topology, overlap, manifest, hard-cap, and exception publication
  atomicity plus bit-exact successful replay.

The earlier partial GCC attempt with five `Not Run` executables is rejected
evidence and is not counted.

S10 now remains open only for current-source remote platform and Linux
sanitizer/fuzzer receipts, the final bound artifact inventory, and one final
independent source/result GO/NO-GO.
