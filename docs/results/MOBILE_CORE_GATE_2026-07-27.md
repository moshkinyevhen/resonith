# R-116 Mobile Core Gate

Date: **2026-07-27**
Status: **ANDROID PASSED; IOS CI PENDING**

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

## iOS gate

The checked-in presets request:

- stable Xcode 26.4.1 on a `macos-26` runner;
- device ARM64 with `iphoneos`;
- simulator x86-64 with `iphonesimulator`;
- iOS 15 deployment target;
- static Core only, with code signing disabled for the library compile gate.

Windows cannot execute this gate because it has no Apple SDK or linker. The
first GitHub macOS run remains pending at this commit and must update this
report with artifact hashes before the R-116 gate is considered complete.

## Machine result

[mobile_core_gate_2026-07-27.json](../../experiments/results/mobile_core_gate_2026-07-27.json)
contains the compact local result.
