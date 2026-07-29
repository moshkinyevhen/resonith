# R-200 Generation-Safe Arena Design

- Date: 2026-07-29
- Status: **ACCEPTED AND IMPLEMENTED — INDEPENDENT STEP-7 GO**
- Scope: R-191 analyzer state ownership only
- ABI effect: none
- Bitstream effect: none
- Codec algorithm effect: none

## Problem

The analyzer reclaims path-state slots while parent chains, frontier rows,
family reservoirs, and output selection may still refer to them. A bare vector
index has the ABA failure: after release and reuse, an old index can silently
name a different state. A generation-tagged `(index, generation)` rejects that
alias, but the tag alone is insufficient if ownership can be forged, parent
rank is unchecked, or release reservations are not balanced.

## Accepted minimal model

Each occupied slot has:

- a non-zero monotonically increasing generation;
- one checked reference count;
- one parent handle or the sentinel;
- one pre-reserved typed `REFERENCE` release event per live reference;
- no free-list link while occupied.

Only `bounded_state_arena` may manufacture an owning RAII reference:

- `create_owned(value)` creates the initial owner;
- `retain_owned(handle)` creates one checked additional owner;
- the former public raw-handle `adopt` path is removed.

Raw handles are non-owning borrows. They are valid only while an owning
frontier/reservoir reference is alive and every dereference rechecks index,
occupancy, and generation.

## Structural invariants

A root state SHALL satisfy:

```text
parent == sentinel
length == 2
```

A child SHALL validate, before its parent refcount changes:

```text
parent index is in range
parent is occupied
parent generation matches
child.length == parent.length + 1
child.first_observation_id == parent.first_observation_id
child.previous_observation_id == parent.current_observation_id
```

Parent validation and acquire consume exactly one typed `REFERENCE` event.
Refcount and outstanding-release reservation increments occur only after every
fallible check and reservation succeeds.

Release consumes one previously reserved typed event. A zero refcount reclaims
the slot, places it at the deterministic LIFO free-list head, and iteratively
releases its parent. No recursive call stack is used.

Generation wrap, refcount overflow, refcount underflow, stale generation,
invalid rank/linkage, free-list corruption, and reservation mismatch are
checked internal failures. They never wrap, alias, or invoke `terminate`.

## Transaction and destruction order

If owner reservation, parent validation/acquire, or allocation fails, the new
slot and every acquired parent reference are rolled back. A reused free-list
slot is not detached until creation is guaranteed to commit.

Output-union handles are borrows backed by family reservoirs. After staged
output no longer needs them:

1. borrowed output-union records are destroyed;
2. owning family reservoirs are cleared;
3. the arena must report both `live_count == 0` and zero outstanding
   `REFERENCE` reservations.

This production O(1) exit check is complemented by a test-only full audit that
verifies:

- occupied-slot count equals `live_count`;
- sum of occupied refcounts equals outstanding release reservations;
- every parent relation is generation/rank/link valid;
- every free slot occurs exactly once in the acyclic free list;
- no occupied slot occurs in the free list.

## Falsification plan

Focused probes cover:

- multiple-slot release/reuse with exact LIFO order;
- no reuse while a retained owner or child keeps a parent alive;
- old generation rejection after slot reuse;
- parent-child cascade release;
- forged owner path absence;
- RAII move without double ownership;
- root-rank and child-rank/link rejection with unchanged parent count;
- owner-reservation, parent-charge, and parent-reservation exhaustion rollback;
- PMR insertion allocation failure before ownership mutation;
- injected refcount overflow;
- injected generation exhaustion and deterministic recovery;
- double release rejection;
- the complete real solver transition
  `pending/frontier -> reservoir -> borrowed union -> staged output -> empty`.

## Rejected complexity

The arena is local to one synchronous analyzer call. It does not need:

- arena UUIDs in every handle;
- hazard pointers or epoch reclamation;
- `shared_ptr`;
- a lock-free free list;
- a production provenance graph;
- recursive destruction.

Those mechanisms increase code, work, and hardware burden without closing a
counterexample present in this single-threaded bounded ownership model.

## External basis

Generational indices are an established direct defense against ABA slot reuse;
the Resonith design adds bounded typed ownership and rank/link invariants.
AddressSanitizer remains an independent use-after-free/double-free gate, but
does not replace deterministic logical probes:

- [Generational Arena: ABA problem and generation-tagged indices](https://github.com/fitzgen/generational-arena)
- [LLVM AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)

## Independent result

The post-implementation red-team returned **GO for Step 7** with zero blockers
on:

```text
native/src/partial_graph.cpp
SHA-256:
D5E960011F78609AE7B0FA83820DECADCB4AEDF1A9E26BA2AA6BA687E670E413
```

The verdict covers owner construction, parent generation/rank/link validation,
rollback and local reservation accounting, borrowed-before-owner teardown,
empty-arena success, full invariant audit, and the focused multi-step probes.
Memory provenance, broad fuzz/platform coverage, and final R-191 admission
remain Steps 8 through 10.
