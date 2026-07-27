# R-116 Mobile Core Gate

Date: **2026-07-27**
Status: **PASSED**

## Scope

R-116 makes Windows, Android, and iOS compilation mandatory for promoted
Resonith Core changes. Codec-library evidence remains separate from Orkela
application, audio-device, and lifecycle evidence.

## Installed local Android toolchain

| Component | Version |
|---|---:|
| Temurin JDK | 25.0.3+9 LTS |
| Android Command-line Tools | 22.0 |
| Android SDK Platform | 36 |
| Android Build Tools | 36.1.0 |
| Android Platform Tools | 37.0.0 |
| Android NDK | r29 (`29.0.14206865`) |
| Android Clang | 21.0.0 |
| CMake used for configure | 4.4.0 |
| Ninja used for build | 1.13.2 |

## Local Android results

Both targets compiled in strict C++23 mode with extensions disabled and
warnings treated as errors.

| ABI | ELF machine | Shared bytes | SHA-256 |
|---|---|---:|---|
| `arm64-v8a` | AArch64 | 2,368,272 | `f3a46292262db65519c7a05932b97e6a8d58fdcc6f2c5fe6bbae121a227f8774` |
| `x86_64` | AMD x86-64 | 2,232,608 | `9b05267cf9b1ec6941ebf2c09ebe6621c469dda1dc4bbddb947fe0977efab0e9` |

Each shared object exports the same 66 public `resonith_*` C ABI symbols.
Dynamic dependency inspection found Android system `libm`, `libdl`, and
`libc` only. Neither artifact depends on `libc++_shared.so`.

The unchanged Windows C++23 build also passed 10 of 10 native tests after the
mobile CMake changes.

## GitHub four-target gate

GitHub Actions run
[`30236232478`](https://github.com/moshkinyevhen/resonith/actions/runs/30236232478)
passed from commit `cc917c41e4d848c4c18e847fb5ddc0f448da70d4`.
The checked-in presets exercised:

- stable Xcode 26.4.1 on a `macos-26` runner;
- device ARM64 with `iphoneos`;
- simulator x86-64 with `iphonesimulator`;
- iOS 15 deployment target;
- static Core only, with code signing disabled for the library compile gate.

Both Android jobs and both iOS jobs passed. The GitHub artifact service
reported the following immutable archive evidence:

| Target | Archive bytes | Archive SHA-256 |
|---|---:|---|
| Android ARM64 | 969,149 | `ba815c6f3a24c7716c4c7db60fc1c0c5b811e12bb07bbf3e741f3cf7838ed596` |
| Android x86-64 | 951,841 | `391e36fca5645a080545323ba69d89c74fc3430447c96fd3b1b81e4075907f82` |
| iOS device ARM64 | 67,804 | `53486594eaa627f4aabf17b589230cc79d82ad50e647f60519eca889fffda618` |
| iOS simulator x86-64 | 66,887 | `0cd5f3011ba9d9c650e5bc465a0d17bc1a1e0552111839294146c9d2c9d46b11` |

These hashes identify GitHub's ZIP artifacts, not the enclosed libraries.
The workflow separately verifies that every enclosed library is non-empty,
that Xcode reports the requested iOS architecture, and that Android shared
libraries do not depend on `libc++_shared.so`.

## Machine result

[mobile_core_gate_2026-07-27.json](../../experiments/results/mobile_core_gate_2026-07-27.json)
contains the compact local result.
