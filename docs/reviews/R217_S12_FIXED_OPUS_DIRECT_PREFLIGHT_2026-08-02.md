# R-217 S12 fixed Opus direct comparison preflight

Status: **INDEPENDENT CONDITIONAL GO; ALL FOUR BLOCKERS INCORPORATED**

## Problem and owner-directed scope

The R-216 exhaustive Opus-frontier run was stopped by the project owner during
the first long item. The replacement must compare the current S11 Resonith
generation directly with Opus, without comparing the preceding Resonith
generation and without searching the complete Opus configuration frontier.

The claim is deliberately narrow: **current Resonith S11 versus one fixed
official Opus 1.6.1 direct anchor at maximum `opusenc` complexity**. It is not
a maximum-effort Opus frontier and cannot support a general "better than Opus"
claim.

## Measurable objective and complete cost

For every item in the frozen 19-item long-first registered manifest:

1. encode and actually decode the current S11 Resonith candidate;
2. generate exactly four bitrate-feedback attempts for one frozen Opus
   configuration;
3. choose one attempt without inspecting decoded quality;
4. actually decode and measure exactly that one Opus attempt;
5. retain complete bytes, hashes, decoded PCM identity, metrics, time, RSS,
   disk use, fallback, and failure state.

The run is admitted only if the source, tool, helper, manifest, Golden Core,
runner, encoded-file, and decoded-PCM identities close and all 19 items obtain
a complete-byte match. No previous-Resonith column is produced.

## Alternatives considered

- **Continue R-216 exhaustive frontier:** rejected for this generation by the
  owner. It is more complete but its hundreds of configurations per item do
  not match the requested direct-comparison scope.
- **Reuse the interrupted R-216 staging tree:** rejected. It is quarantined,
  incomplete, used `application=auto` on Mozart, and has no authoritative
  R-217 import receipt.
- **Use one nominal Opus bitrate without byte feedback:** rejected because
  complete Ogg size can differ materially from the request.
- **One fixed configuration plus deterministic byte feedback:** accepted as
  the smallest coherent direct test.
- **No further comparison after the diagnostic Mozart point:** rejected
  because it cannot satisfy the frozen registered-corpus boundary.

## Frozen Opus anchor

- official `opusenc`/`opusdec` 1.6.1 identities remain hash-pinned;
- exact common arguments: `--vbr --comp 10 --framesize 20 --expect-loss 0
  --max-delay 1000 --discard-comments --discard-pictures --padding 0`;
- default phase inversion is retained; `--no-phase-inv` is forbidden;
- add `--speech` only when the immutable registered category list contains the
  exact token `speech`; otherwise add `--music`;
- the category hint is a conservative oracle advantage for Opus and never
  comes from mutable semantic AI;
- deterministic Ogg serial, integer round-half-even q5, one initial attempt
  plus three feedback attempts;
- choose before metrics by `(absolute complete-byte delta, complete bytes,
  q5, attempt index)`;
- strict tolerance is `max(64, target_bytes // 1000)`;
- no strict attempt means `UNMATCHED` and forbids an equal-rate claim.

## Bounds and restart policy

- use a new R-217 schema, run identity, output root, index, staging directory,
  and per-item atomically committed receipt;
- run the full Mozart item first and commit its receipt before item 2;
- do not import R-216 S11 or Opus artifacts; re-encode from the frozen source;
- retain the R-216 proven process-tree termination and repository/output path
  confinement;
- long-item ceiling: 20 minutes for S11 plus 15 minutes for the fixed Opus
  anchor and metrics, 12 GiB RSS, 8 GiB staging;
- short-item ceiling: 20 minutes total, including at most 15 minutes for S11,
  8 GiB RSS, and 2 GiB staging;
- complete run ceiling: 8 hours and 24 GiB retained output;
- a timeout, hash mismatch, source mutation, disk/RSS breach, unmatched size,
  decoder mismatch, or missing receipt fails closed and is not retried blindly.

## Independent red-team

The independent auditor returned NO-GO on the initial wording and conditional
GO after four remediations:

1. narrow the claim from maximum-effort Opus to a fixed maximum-complexity
   direct anchor;
2. select the byte match before metrics using a frozen total order;
3. freeze padding, metadata, application, phase, serial, and exact arguments;
4. create independent R-217 authority and do not inherit partial R-216 state.

All four are incorporated above. Implementation is authorized only inside this
contract. A later general Opus claim still requires the separately defined
frontier protocol.

The first code audit then found six runtime-evidence gaps. The candidate is
not executable until all are closed in the implementation and tests:

1. the short-item 8 GiB child RSS ceiling must reach Opus encode/decode rather
   than exist only on the parent worker;
2. source, runner/import closure, Python executable, Golden Core, and Opus
   binary identities must be checked again inside the worker both before and
   after use, together with frozen dependency versions and source PCM;
3. the run index must retain and verify the final receipt SHA-256 on resume;
4. Python executable identity and dependency versions must be part of the run
   material and therefore the run identity;
5. each child and item must enforce and record pre/during/post disk use, with a
   final retained-root check after aggregation;
6. the fixed Opus deadline must be checked around the in-process metric pass,
   while the outer worker ceiling remains the hard interrupt bound.
7. actual `challenger.resonith` bytes and SHA-256 must equal the S11 report's
   `complete_bytes` and `payload_sha256` before those bytes become the Opus
   rate target.

These are minimal closures of already declared claims, not new test
infrastructure or broader comparison scope.

The first full run then preserved a valid Mozart receipt but failed closed on
the exact 420-second `ebu-claves` S11 ceiling. The evidence and independently
approved one-time bounded redesign are recorded in
`R217_S12_SHORT_TIMEOUT_INCIDENT_2026-08-02.md`. Only the short S11 and outer
worker ceilings change to 900 and 1,200 seconds. A new root and run identity
must redo Mozart; a second budget breach stops this evidence generation.

## Falsifiable prediction and kill gate

The direct runner should reduce Opus work to four encodes and one decode/metric
pass per item while preserving complete-byte fairness and decoder-derived
metrics. Any configuration drift, post-quality anchor selection, partial R-216
authority, second Opus metric pass, or unsupported general Opus claim is a
blocking failure.
