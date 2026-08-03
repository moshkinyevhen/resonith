# R-227 S13 phase-poisoned tiled-shadow result

Date: 2026-08-02

Status: **INDEPENDENT GO TO REJECT; MEASURED NO-CHANGE**

## Outcome

The only authorized R-227 execution falsified the S13 phase-anchor hypothesis
under its frozen eligibility and resource rules. No Resonith algorithm,
bitstream, decoder, default, version, Opus anchor or product release changes as
a result.

The first two real long inputs produced no eligible phase-free lane. The third
real long input stopped before candidate publication when the existing native
lapped analysis exceeded its configured host ceiling. The synthetic positive
control therefore did not execute. R-227 explicitly requires every real long
input to qualify and pass, forbids threshold or resource retuning after the
result, and permits no second rescue mechanism.

## Frozen authority

- implementation commit:
  `5d720128ccbd77091ac613274df135b503af028c`;
- runner SHA-256:
  `320307dc8fd0c9bead47fd2dd998734f17bbed232632be1615d121db3b02eef6`;
- focused-test SHA-256:
  `50153bfb914069493c5d5a93095f6e5a7ae9e24ecee7fc8ef3c106e3d89af3d9`;
- preflight SHA-256:
  `957c4edd16267893b34cce37e4522eb92bde0017576cf17a901bf112983c627a`;
- source-manifest SHA-256:
  `173b3c8c773a3152358dbe542bca53aa839999a2813fe3a8dbaeec63ac376f88`;
- run-index SHA-256:
  `93e77f87b84b98d46b60fbffd70b1688b117ec974142842f8ddf174be8cb9301`;
- terminal-record SHA-256:
  `75445b6fdbc90d0ae3ded651a0e239dde4bcb8a1f1c9a48c8f438374726b7db5`.

The retained evidence is local at
`G:\Resonith\artifacts\r227-s13-phase-shadow`. The external terminal record is
`G:\Resonith\artifacts\r227-s13-phase-shadow-failure.json`. It records the
fail-closed disposition without modifying either atomically published input
directory.

## Per-input result

| Input | Result | Eligible lanes | Phase read by eligibility | Wall s | CPU s | Peak RSS bytes | Disk high-water bytes |
|---|---|---:|---|---:|---:|---:|---:|
| full Mozart | `INELIGIBLE_NO_PHASE_FREE_LANE` | 0 | no | 2484.973 | 2461.609 | 2,502,889,472 | 212,643,184 |
| long LibriSpeech | `INELIGIBLE_NO_PHASE_FREE_LANE` | 0 | no | 449.103 | 443.797 | 1,136,590,848 | 33,883,255 |
| full *Elephants Dream* | `RESOURCE_FAILURE_BEFORE_CANDIDATE_PUBLICATION` | not reached | not reached | not published | not published | ceiling stop | no retained files |
| bounded-vibrato positive control | `NOT_EXECUTED_AFTER_TERMINAL_RESOURCE_FAILURE` | not applicable | not applicable | not run | not run | not run | not run |

The Mozart eligibility pass inspected 166,259 phase-free observations and
formed 140,211 tracks. Long LibriSpeech inspected 88,845 observations and
formed 81,051 tracks. Neither produced one sealed lane satisfying the frozen
phase-free eligibility law. Consequently neither carry nor reset candidate was
executed, and there is no phase-anchor rate or quality point to compare.

The two atomically published receipt files have SHA-256 values
`415573e6f30bef2d339b36423ed8a3476fa1e7e12c9ff5bf42a07516ad0f7c72`
and
`6ab6c2178193bd03ff3b8c171e14aa5c2435bf1e4cbd685e9c4ab7c710595cea`.
The third input left only an empty staging directory and no final item
directory.

## Failure accounting

An initial shell launch omitted the repository `PYTHONPATH` and failed before
the runner imported, before any input began and before the output root existed.
It is recorded as a pre-main launch incident, not counted as an experiment
execution. The subsequently corrected process used the same frozen runner,
commit, inputs and arguments and is the only R-227 execution.

That process terminated in the existing direct-Truth path with:

```text
MemoryError: native lapped analysis exceeds the configured host ceiling
```

The top-level `index.json` consequently retained its intermediate `RUNNING`
label. This is not interpreted as a resumable run. The terminal record binds
the exact index hash, the two published results, the empty third staging
directory and the fail-closed no-retry disposition.

## Comparison boundary

R-227 produced no admitted Resonith generation and no decodable phase-anchor
candidate on any real input. Therefore rerunning or rate-matching Opus would
not be a codec comparison; the accepted R-221 official Opus 1.6.1
maximum-complexity evidence remains unchanged context. S14, whose purpose is a
full corpus comparison of an admitted S13 generation, is not applicable.

The mandatory independent result audit returned GO with no blocking finding.
The panel transition is therefore to close S13 as rejected/no-change, record
S14 as not applicable, and begin S15 source-filter excitation and slowly
varying resonator/formant laws from the unchanged accepted S12 baseline.

## Claims not made

This result makes no compression, quality, novelty, portability, product or
release improvement claim. It does not authorize new phase syntax, a decoder
change, a resource-ceiling increase, a version change, or reuse of observed
phase in eligibility. The negative result is retained because it prevents a
costly phase mechanism from entering the codec without evidence.
