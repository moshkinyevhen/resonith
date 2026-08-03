# R-213 — S10 workflow evidence-integrity preflight

Date: 2026-08-02  
Scope: `.github/workflows/tests.yml` only  
Production/reference/ABI/corpus impact: none

## Problem and frozen baseline

GitHub Actions run `30723903591`, attempt 2, was reported green at commit
`afbff0b29aa2937391205c456e2b5742d84a1d66`, but the downloaded Linux GCC,
Linux Clang, Linux ARM64, macOS and cross-toolchain JSON evidence files were
zero bytes. The Windows replay was nonempty and valid.

The Unix replay jobs invoked `python ... | tee ...` without Bash `pipefail`.
Their Python environments also omitted the frozen research requirements, while
importing `reference.maf_p0` eagerly requires NumPy/SciPy and related packages.
Python therefore failed, `tee` returned success, and empty artifacts were
uploaded. The cross-toolchain comparator was hidden by the same pipeline
behavior. This is a false-green evidence gate.

## Objective, constraints, and complete cost

Make the existing S10 replay gate fail closed without changing codec behavior,
the replay corpus, semantic comparison rules, or test volume. Cost includes CI
dependency installation time and the risk of hiding a native-process failure on
all supported runners.

## Alternatives considered

1. **Do nothing:** rejected; a green status would not prove replay evidence.
2. **Replace `tee` with plain redirection:** rejected; it removes useful live CI
   output and does not address the missing frozen environment.
3. **Add a new validation harness:** rejected as test recursion; the existing
   Python readers already validate JSON semantics when execution is propagated.
4. **Chosen:** install the existing frozen `requirements-research.txt` in the
   three Unix replay jobs, enable `set -euo pipefail` in every existing Bash
   replay/comparison pipeline, and explicitly reject nonzero native Python exits
   in the Windows PowerShell replay block.

## Falsification and boundary checks

- A missing dependency must fail the producer job rather than create a green
  zero-byte artifact.
- A replay semantic mismatch must fail the cross-toolchain job.
- Windows must not rely on `Tee-Object` behavior to propagate a native exit.
- Existing valid replay counts, hashes and resource ceilings must remain
  unchanged.
- No production source, decoder output, bitstream, corpus or admission threshold
  may change in this remediation.

## Independent audit

The independent red-team auditor returned **conditional GO** for this bounded
workflow-only remediation. It confirmed the eager-import dependency failure and
the `tee` false-success mechanism. Final GO remains blocked until a clean rerun
produces nonempty valid replays for Linux GCC, Linux Clang, Linux ARM64, macOS
and Windows, and the comparison consumes all five.

## Falsifiable prediction and kill gate

Prediction: after the patch, all five replay artifacts are nonempty valid JSON,
their portable semantic digests agree, and the cross-toolchain JSON is nonempty
and records five consumed replays.

Kill gate: any missing/empty/unparseable replay, hidden producer failure, replay
count other than five, semantic mismatch, or changed codec output blocks S10.

## Verification plan

1. Parse the workflow and inspect the exact diff.
2. Run focused local replay/comparison validation with the frozen environment.
3. Push one workflow-only commit and let the triggered jobs finish without
   cancellation or manual substitution.
4. Download the produced artifacts, independently check size/JSON/hashes/counts,
   and request final auditor GO/NO-GO.

R-198 full music/Opus comparison is not triggered because this patch changes no
codec algorithm, bitstream, decoder, source PCM, or quality decision.
