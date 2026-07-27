# Production Toolchain Baseline

Status: **ACCEPTED — R-114**
Date: 2026-07-27

## 1. Language baseline

Resonith production source uses **C++23**.

C++23 is the newest language mode admitted to the mandatory desktop, mobile,
browser, and embedded portability gates. C++26 may be compiled in a
non-blocking forward-compatibility job, but it is not allowed to reduce
Android, iOS, Apple Clang, WASM, or embedded coverage.

The shipped codec, SDK, command-line tools, and Orkela runtime have no Python
dependency. Python 3.14.6 is the research control plane for oracle models,
RDO policy, metrics, reports, and experiment orchestration. Scaling DSP and
search kernels execute in C++23, portable SIMD, or optional CUDA.

## 2. Pinned Windows research workstation

| Component | Accepted version | Repository-local installation |
|---|---:|---|
| Python | 3.14.6 | `artifacts/tools/python-3.14.6-amd64` |
| LLVM/Clang | 22.1.8 | `artifacts/tools/llvm-mingw-20260616-ucrt-x86_64` |
| CMake | 4.4.0 | `artifacts/tools/cmake-4.4.0-windows-x86_64` |
| Ninja | 1.13.2 | `artifacts/tools/ninja-1.13.2-windows-x86_64` |
| MinGit | 2.55.0.windows.3 | `artifacts/tools/mingit-2.55.0.3-64-bit` |

These are stable releases. Release candidates and nightly builds are not
production defaults.

## 3. Integrity evidence

The local installer and archive hashes are:

| Artifact | SHA-256 |
|---|---|
| `python-3.14.6-amd64.exe` | `14b3e9a710a3fcf0bd9b55ab6b60412bd91227563f813fc49040cabc0209e0bd` |
| `cmake-4.4.0-windows-x86_64.zip` | `156d70eb7625a7b469444df7d0861d2af8d5d0a437fce32c350372b08f5620e8` |
| `ninja-win-1.13.2.zip` | `07fc8261b42b20e71d1720b39068c2e14ffcee6396b76fb7a795fb460b78dc65` |
| `MinGit-2.55.0.3-64-bit.zip` | `f48e2d2dc74a24454adc6d8fd0ac25bf9c2386f19cfb06202b9465aaad4f9f05` |
| installed `clang++.exe` | `a8b7a614eeadd9105f814be3701a7f312cda4cea51751b75b408c16100c94e85` |

Downloaded toolchains and build products are intentionally excluded from Git.
The manifest records the reproducible baseline without committing third-party
binaries.

## 4. Admission gate for an upgrade

A default toolchain change is accepted only when it passes:

1. strict warning-as-error C++23 configure and build;
2. all native tests;
3. the complete Python/native test suite on the pinned Python version;
4. exact compressed-byte and decoded-PCM regression;
5. Android, iOS, desktop, WASM, and embedded compile gates as they become
   available in CI.

Compiler novelty alone is not a codec improvement. A language or library
feature enters decoder-critical code only when it gives a measured safety,
correctness, performance, or maintainability benefit without narrowing
platform support.

## 5. Accepted migration evidence

The first strict C++23 admission gate passed:

- 10 of 10 native tests;
- 181 Python/native tests, with four external integrations skipped;
- all 16 R-111 heterogeneous streams byte-identical across 192 seconds;
- no dependency on a compiler-local C++ runtime in the Windows Core DLL.

The complete evidence is recorded in
[C++23 Production Toolchain Gate](results/CPP23_TOOLCHAIN_GATE_2026-07-27.md).

## 6. Stable external sources

- Python releases: <https://www.python.org/downloads/>
- LLVM-MinGW releases: <https://github.com/mstorsjo/llvm-mingw/releases>
- CMake downloads: <https://cmake.org/download/>
- Ninja releases: <https://github.com/ninja-build/ninja/releases>
