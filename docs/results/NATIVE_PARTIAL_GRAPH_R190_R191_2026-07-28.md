# R-190/R-191 Native Partial-Graph Gate

Date: 2026-07-28  
Status: remediated analyzer infrastructure; second post-remediation audit pending

## Result

The immutable R-190 edge contract and separate experimental R-191 path ABI v2
now execute in the C++23 Golden Core. Python and C++ produce bit-exact edge,
path, and CSR path-entry records on the frozen fixture and on 32 deterministic
randomized second-order cases. Observation input permutations produce the same
canonical records.

The edge scorer also executes on the actual RTX 2080 Super through the
optional NVRTC C++23 Foundry backend. CPU and GPU records are bit-exact at
internal tile sizes 1, 31, 32, 255, 256, and 1,024. The tile boundary is
therefore an execution detail rather than a pattern boundary.

| Gate | Measured result |
|---|---:|
| Frozen native edge records | 9 |
| Frozen native K-best path records | 8 |
| Frozen native CSR path entries | 24 |
| Random Python/C++ graph cases | 32 |
| Python/C++ edge/path/entry parity | bit-exact |
| Input-permutation parity | exact |
| CUDA device | NVIDIA GeForce RTX 2080 Super |
| CUDA compute capability | 7.5 |
| NVRTC | 13.3 |
| CPU/GPU tested tile sizes | 1, 31, 32, 255, 256, 1,024 |
| CPU/GPU edge parity | bit-exact |
| Random CUDA graph cases | 32 / 330 edges |
| Combined analyzer/tracker/path Python tests | 45 passed |
| Combined Python wall time | 30.80 s |
| Windows C++23 compilers | Clang 22 and GCC 16 |
| Android targets | ARM64 and x86-64 |
| Physical Android device | Pixel 7 Pro |
| Android ASan/UBSan unit and smoke | passed |
| Android libFuzzer | 10,000 runs, no failure |
| libFuzzer observed coverage | 3,932 |

## Falsification found during the gate

A randomized graph exposed a one-unit Q8 mismatch for a negative odd
continuity score. Python floor division mapped `-833 / 2` to `-417`; C++
truncation mapped it to `-416`. The independent auditor rejected truncation
because it erases a `-1` penalty and rejected nearest-even because it introduces
parity-dependent ties.

R-191 now freezes signed half-score division as floor toward negative infinity.
Boundary tests cover negative and positive odd values and the stored score
domain. The randomized Python/C++ suite passes after the correction.

## Contracts exercised

- edge ABI v1 remains unchanged;
- path output uses a separate fixed path record plus a bounded CSR entry arena;
- preflight reports exact required record counts before the fill call;
- fill is transactional and rejects changed inputs through a diagnostic
  fingerprint;
- supplied edges are re-enumerated through the shared canonical streaming
  scorer and rejected field-for-field when missing, duplicated, permuted, or
  forged;
- path history uses fixed arena records, checked integer parent indices,
  reference-counted reclamation, and collision-free reconstructed identities;
- one bounded PMR resource meters project-managed dynamic payload, while
  environmental allocation failure has a distinct status;
- every finite K or family truncation is reported and sets `PRUNED`;
- exact-small selection uses an unsaturated two-limb positive total and full
  canonical identity sets for ties;
- value, continuity, and protected weak-line families coexist in one union;
- exact-small disjoint selection uses canonical path identities and explicit
  ownership conflicts;
- second-order frequency and amplitude laws use frozen overflow-checked integer
  arithmetic;
- CUDA acceleration scores the same finite candidate set as the CPU reference.

## Reproduction

```powershell
cmake --build build/cpp23-clang22-ninja `
  --target resonith_core_shared resonith_partial_graph_test `
           resonith_partial_graph_fuzz_smoke resonith_c_header_test `
           resonith_foundry_cuda_test -j 8

.\build\cpp23-clang22-ninja\resonith_partial_graph_test.exe
.\build\cpp23-clang22-ninja\resonith_partial_graph_fuzz_smoke.exe
.\build\cpp23-clang22-ninja\resonith_c_header_test.exe
.\build\cpp23-clang22-ninja\resonith_foundry_cuda_test.exe `
  '<nvrtc-runtime-directory>'

$env:PYTHONPATH='.;reference'
$env:RESONITH_NATIVE_CORE=`
  'build\cpp23-clang22-ninja\libresonith_core_shared.dll'
python -m pytest -q `
  tests/test_complex_partial_analyzer.py `
  tests/test_complex_partial_tracker.py `
  tests/test_partial_graph_fixed.py
```

## Evidence

- [Machine report](../../experiments/results/native_partial_graph_r190_r191_2026-07-28.json)
- [Pre-implementation adversarial review](../reviews/R191_PATH_ABI_AUDIT_2026-07-28.md)
- [Decision log](../06_DECISION_LOG.md)
- [C ABI](../../native/include/resonith/partial_graph.h)
- [C++23 implementation](../../native/src/partial_graph.cpp)
- [CUDA Foundry implementation](../../native/src/foundry_cuda.cpp)
- [Independent Python oracle](../../reference/maf_p0/partial_graph_fixed.py)

## Remaining blocker

This result validates bounded graph construction, not an audio predictor.
The first post-implementation R-185 audit found malformed-edge acceptance,
incomplete actual resource accounting, mixed objective domains, invisible
pruning, saturated exact-small totals, and an irregular-gap uncertainty bias.
ABI v2 implements the independently pre-audited remediation package, but its
mandatory second post-remediation audit is still open. Current evidence also
does not include a native Linux sanitizer run or an Apple-SDK iOS compile gate.
No decoder-domain synthesis, syntax, compression, Opus, release, or Orkela
claim is authorized until that audit classifies the remaining platform and
proof gaps.
