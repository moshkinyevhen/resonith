# C++23 Production Toolchain Gate

Date: **2026-07-27**
Decisions: **R-114, R-115**
Status: **PASSED**

## Result

Resonith now builds in strict standard C++23 mode with stable Clang 22.1.8,
CMake 4.4.0, and Ninja 1.13.2. The research suite runs on Python 3.14.6.
C++26 remains a non-blocking forward-compatibility check because it does not
yet preserve the required mobile and embedded coverage.

The migration changed neither accepted compressed bytes nor decoded Truth.

## Gates

| Gate | Result |
|---|---:|
| Strict `-std=c++23`, extensions off, warnings as errors | passed |
| Native CTest programs | 10/10 passed |
| Python 3.14.6 and native-Core suite | 181 passed, 4 external skips |
| R-111 heterogeneous corpus | 16/16 streams byte-identical |
| R-111 audio covered | 192.0 seconds |
| R-111 reference stream bytes | 2,471,068 |
| R-111 re-encode wall time | 60.222 seconds |
| Minimum measured encode rate | 2.311x real time |
| Maximum measured encode rate | 6.274x real time |
| Compiler-local C++ runtime dependency | absent |

The C++23 Core DLL SHA-256 is
`a801f0192c81c57b2c97465efa637d0ea4612c6194f9f146a4c93cde6408fab0`.

The exact stream gate covered speech, solo voice, violin, piano, sustained
sine, vibrato gong, cymbal, claves, side drum, pink noise, electronic music,
dense pop, dense orchestra, and two film mixes.

## Defects exposed and fixed

1. `lapped_finite.cpp` used `std::max` without directly including
   `<algorithm>`. The previous environment supplied it transitively. The
   strict C++23 build exposed and removed that portability defect.
2. The initial MinGW CMake binaries depended on compiler-local `libc++.dll`.
   CTest consequently waited on an interactive Windows loader dialog when the
   compiler directory was absent from `PATH`. The Core target now propagates
   static C++ runtime linkage on MinGW. The resulting DLL and executables use
   only Windows system runtime imports.
3. The first Python 3.14 invocation deliberately exposed an invalid local
   environment override that placed CPython 3.12 binary wheels before the
   Python 3.14 site-packages. Removing the override selected the pinned
   Python 3.14 packages and the complete suite passed.

## Reproduction

The compact machine-readable result is
[cpp23_toolchain_regression_2026-07-27.json](../../experiments/results/cpp23_toolchain_regression_2026-07-27.json).
The full local per-clip report is generated under
`artifacts/cpp23-toolchain-regression/report.json`.
