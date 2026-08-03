# R-212 S10 CI remediation preflight

Date: 2026-08-02

Status: **INDEPENDENT GO FOR ONE BOUNDED REMEDIATION LOOP**

## Problem and frozen baseline

Commit `2ca2fb0` passed the local current-source gate (native CTest 20/20,
Python R-191/R-203 parity 78/78, R-208 CUDA structural evidence, and R-210
ABI obligations) but exposed two CI-only contract defects:

1. Windows x64 and Windows ARM64 both fail only
   `partial_graph_conformance` with `R-203 candidate-rich aggregate evidence
   differs`.
2. The Ubuntu LLVM 18 coverage job rejects the old source SHA before applying
   its otherwise generated current-source report.

The production source is frozen at SHA-256
`ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`.
No codec algorithm, bitstream, decoder output, or public ABI may change in this
remediation.

## Complete objective and costs

Close S10 using the existing gates and the existing R-203 evidence split. The
optimized cost is the smallest source/test/contract change that restores:

- portable semantic identity across toolchains;
- locally exact resource telemetry and bounds on every toolchain;
- current-source 95% line / 90% branch coverage admission;
- one final artifact inventory and independent GO/NO-GO.

Runtime, memory, workflow duration, repository growth, and another CI cycle are
part of the cost. No new harness, private ABI, fixture family, or meta-test is
permitted.

## Alternatives and falsification

### A. Freeze the observed MSVC totals

Rejected. Allocator telemetry and memory-page work are implementation-specific.
Freezing a second MSVC constant would hide the contradiction and create one
golden value per STL/toolchain.

### B. Remove the Windows or coverage jobs

Rejected. It weakens the declared portability and safety gates and cannot close
S10.

### C. Make allocator telemetry normative across implementations

Rejected for this remediation. The accepted Python replay and
`r203_compare_replays.py` already define portable identity independently from
resource telemetry. Changing production allocation accounting would be a new
architecture decision and could affect resource admission.

### D. Reuse the admitted evidence split and rebind coverage

Chosen. The C++ candidate-rich digest will project the same portable evidence
class already used by the independent replay: paths, entries, fingerprints,
semantic report fields, and non-memory work. Full reports still require
twice-run byte identity locally, resource ordering, zero CPU device usage, and
manifest ceilings. The coverage contract will be rebound only to the actual
current LLVM 18 report, existing thresholds, and current proof-guard spans.

### E. Make no change

Rejected because Windows and coverage remain genuine S10 blockers.

## Evidence

- GitHub run `30723181265`: Windows x64 and ARM64 fail at the same aggregate
  assertion while every preceding conformance test passes.
- GitHub run `30723181233`: the coverage artifact was produced successfully;
  rejection reports only the stale source SHA at the first contract check.
- `experiments/r197_partial_graph_native_gate.py` explicitly removes resource
  telemetry from Class-A semantic evidence and retains it as local evidence.
- `experiments/r203_compare_replays.py` compares `IDENTITY_FIELDS` across
  toolchains while reporting resource ranges separately.
- Independent red-team verdict: final S10 remains NO-GO, but this single bounded
  remediation loop is GO under the constraints above.

## Falsifiable prediction and kill gate

Prediction: after the projection/contract correction, Windows x64 and ARM64
produce the same portable R-203 identity as Linux/macOS while retaining valid
local resource telemetry; LLVM 18 reports at least 95% lines and 90% branches;
all existing sanitizer/fuzzer/platform jobs pass.

Kill gate: stop S10 closure if any portable path/entry/fingerprint/non-memory
identity differs, any resource ordering or ceiling fails, coverage falls below
the frozen thresholds, a production source/ABI/output byte changes, or a second
remediation cycle would require another harness or expanded test architecture.

## Verification plan

1. Rebuild and run local native CTest plus the 78-case Python parity gate.
2. Run the downloaded LLVM 18 coverage artifact through the rebound contract.
3. Push one focused remediation commit.
4. Require Windows x64, Windows ARM64, Linux coverage, sanitizer/fuzzer, the
   R-203 four-toolchain comparison, and the aggregate Mobile Core gate.
5. Bind head commit, PR merge SHA/tree, workflow runs, artifacts, hashes, and
   exit status in the final S10 inventory.
6. Obtain an independent final source/result GO/NO-GO before advancing S11.

R-198 is not triggered because this is test/evidence projection only and the
production codec source and decoded output remain unchanged.
