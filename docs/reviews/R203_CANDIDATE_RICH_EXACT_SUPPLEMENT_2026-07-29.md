# R-203 Candidate-Rich Exact Supplement

Date: 2026-07-29

Status: **INDEPENDENT PRE-IMPLEMENTATION GO**

Generator ID: `R203-CANDIDATE-RICH-EXACT-1`

Schema: `resonith-r203-candidate-rich-exact-jsonl-1`

## Problem

The immutable R-197 exact-small corpus contains all 9,024 frozen
presentations, but its value alphabet produces zero canonical edges, paths and
entries. It remains necessary negative, ABI, permutation and fingerprint
evidence, but it cannot admit path-family generation or exact selection.

Changing or relabeling R-197 is rejected. This supplement is a second,
conjunctive admission input with its own source, contract, corpus and semantic
hashes.

## Finite domain

All cases use one resolution `{id=0, fft=128, hop=64}`, sample rate 48,000 Hz,
detector zero, constant amplitude, one-Hz frequency uncertainty and positive
node value. Reserved fields are zero.

Five topology profiles are mandatory:

1. `T0 chain-cycle`: three observations at centers `0/64/128`, frequencies
   `440/440/440 Hz`, gap `[1]`, cycles `[-1,0,1]`, neighbours one, jump and
   slope zero. Closed-form expectation: six edges and fifteen directed path
   identities.
2. `T1 diamond`: four observations
   `(center,frequency)=(0,440),(64,439),(64,441),(128,440)`, gap `[1]`,
   cycle `[0]`, neighbours two and jump `1 Hz`. Closed-form expectation: four
   edges and six directed path identities.
3. `T2 boundary-minus`: three observations at centers `0/192/384` and
   frequencies `440/999/1558 Hz`.
4. `T3 boundary-exact`: the same centers and frequencies
   `440/1000/1560 Hz`.
5. `T4 boundary-plus`: the same centers and frequencies
   `440/1001/1562 Hz`.

Profiles T2 through T4 use gap `[3]`, cycle `[0]`, neighbours one, jump
`368 Hz`, and slope `1 Hz/sample`. The exact allowed distance is `560 Hz`;
closed-form edge/path counts are `2/3`, `2/3`, and `0/0`.

Each topology combines:

- ownership `U`: unique component per observation;
- ownership `C`: `[0,0,1]` for three observations and `[0,0,1,0]` for the
  diamond;
- phase `N`: locally resolvable only;
- phase `Z`: locally resolvable plus phase usable, with zero turn and step;
- phase `P`: locally resolvable, phase usable and protected weak, with zero
  step and quarter-turn progression.

Every observation permutation is present. The exact total is:

```text
2 ownerships * 3 phase profiles
* (4 three-observation topologies * 3! + 1 diamond * 4!)
= 288 cases
```

## Frozen path policy

- minimum/maximum observations: `2/4`;
- K value/continuity: `16/16`;
- top-K value/continuity/protected: `20/20/20`;
- protected paths per band: `2`;
- exact-set candidate limit: `20`;
- maximum paths/entries/frontier/states: `64/256/64/128`;
- maximum edges: `64`;
- work and host limits are fixed reviewed ceilings that must admit every case;
- device bytes are zero.

## Independent authorities

Authority A is the existing arbitrary-precision Python R-190/R-191 oracle. It
must receive only generated input fields and may not call native code.

Authority B is a separate graph-theoretic checker. It must not import or call
native code, `enumerate_edges_fixed`, `build_paths_fixed`, or consume a
candidate list emitted by either native or Authority A. It directly:

1. enumerates valid source-target-cycle edges from input fields;
2. enumerates every directed path and edge-ID sequence with at least two
   observations;
3. calculates ownership conflicts and all conflict-free subsets;
4. verifies the closed-form topology and phase/protection invariants.

Native, Authority A and Authority B must agree exactly on canonical edge and
path identity sets. Authority A and native must additionally agree on complete
path records, selection, reports, fingerprints and ledgers.

## Admission invariants

Generation fails unless:

- topology edge/path counts are exactly `6/15`, `4/6`, `2/3`, `2/3`, `0/0`;
- every non-empty `U` case has zero internal conflicts and positive cross-path
  conflicts;
- every non-empty `C` profile has at least one internal-conflict path;
- `N` paths contain no phase evidence;
- `Z` non-empty paths contain phase evidence with zero phase-error sum;
- `P` non-empty paths have positive phase-error sum and at least one protected
  family record;
- every non-empty case exposes between one and twenty selectable candidates
  and uses the exact-small solver;
- all `n!` input presentations produce identical canonical payload,
  fingerprints, report and ledger.

Any mismatch is unconditional NO-GO. The supplement cannot replace any frozen
R-197 case or quantitative campaign.

## Evidence inventory

The final inventory binds:

- frozen R-197 contract SHA-256;
- this contract SHA-256;
- generator, Authority A adapter, and Authority B source SHA-256;
- JSONL SHA-256;
- independent expected semantic SHA-256;
- native semantic hashes for every admitted toolchain.

## R-198 boundary

This supplement is test and evidence infrastructure only. It does not change
codec syntax, encoder selection, bitstreams, decoded PCM, compression or
quality and does not trigger the registered-music/Opus gate.
