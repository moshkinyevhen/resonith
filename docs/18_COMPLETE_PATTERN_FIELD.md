# STEP M-151 — Complete Pattern Field

Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**

## 1. Outcome

STEP M-151 makes objective pattern memory the primary MAF experiment. The
encoder searches for reusable acoustic structure without requiring note,
phoneme, speaker, instrument, or environmental labels:

\[
x_j = T(\theta_j)B + r_j
\]

`B` is one immutable Basis, `T` is a bounded deterministic integer transform,
and `r_j` is objective Truth correction. Lossless correction reconstructs the
input PCM exactly. A lossy correction is eligible only under the declared
quality floor.

The project uses the word **complete** only for a published finite search
language. No finite implementation can enumerate every arbitrary mathematical
program that might describe a signal.

## 2. Search language declaration

Every Foundry evidence run records:

- all analyzed time origins and duration scales;
- all frequency cells, including the full-band signal;
- all input channels and output routes;
- all Basis candidates and representation families;
- every discrete phase, alignment, polarity, pitch, time, envelope, filter,
  and composition parameter;
- all analytically fitted parameters and explicitly checked fixed-point
  neighbours;
- maximum grammar depth, state-law length, operations, host memory, device
  memory, and deterministic tile dimensions.

Every candidate inside this declaration is evaluated. Hashes, embeddings, and
AI may change evaluation order but not membership. A fast profile that prunes
candidates is labelled `Fast` or `Live`, never `Foundry`.

## 3. Anti-blindness rules

1. Every declared scale is discovered independently from original PCM.
2. A micro-pattern never owns samples during discovery.
3. Overlapping, nested, cross-band, and cross-channel candidates remain
   available to the final selector.
4. Content-defined exact matching complements the regular multiscale lattice;
   neither is allowed to hide the other.
5. Direct long spans compete with bottom-up CompoundBasis candidates.
6. Repeated parameter increments compete with one persistent state law.
7. Only the global complete-cost selector assigns reconstruction ownership.

## 4. Objective candidate families

| Family | Required search |
|---|---|
| Exact motif | Identical PCM and partial-spectrum cells at every declared scale |
| Basis orbit | Crop, alignment, circular phase, polarity, gain/envelope, pitch/time, fractional phase, spectral envelope, reverse/loop, stable short filtering |
| Persistent source-filter | Excitation and slowly changing filter/pitch/phase laws |
| Stochastic field | Counter-seeded law, spectral envelope, density, modulation, and channel correlation |
| Transient | Independent onset and attack support without long-window pre-echo |
| Cross-channel field | Shared Basis with delay, phase, decay/envelope, and bounded transfer |
| Hierarchical grammar | Direct motifs, transformed instances, CompoundBasis, and reusable state increments |
| Independent Truth | Always-available exact or quality-constrained fallback |

Mixture factorization is objective: the encoder may infer latent recurring
components from changing mixtures, but the stream does not need to name their
physical source.

## 5. Global quality-constrained RDO

The selector prices:

- immutable dictionary payload once;
- every placement, transform parameter, route, and state event;
- entropy state and checkpoints;
- correction payload;
- decoder operations and peak persistent memory;
- the measured distortion of PCM produced by the real decoder.

Bytes alone are insufficient. The lossless profile admits only exact PCM. A
lossy candidate must meet every applicable waveform, log-mel, intelligibility,
transient, and channel/spatial floor before rate comparison. If no structured
candidate wins, independent Truth is selected.

## 6. Implementation checklist

Legend: `DONE` means the complete R-151 seven-part gate has passed. `PARTIAL`
means useful code exists but the row is not complete.

| ID | Mechanism | Current state | Completion evidence |
|---|---|---|---|
| M151-01 | Exact Basis placement, crop, integer/circular phase, polarity, forward/reverse direction, constant/linear gain, exact correction | PARTIAL | Native schema-1 decoder/CUDA lattice and direct Orkela execution pass; final container and full R-118 remain |
| M151-02 | Independent multiscale and all-declared-origin discovery | PARTIAL | Native GPU tiles, CPU parity, overlap and scale recall, declared cardinality pass; frequency cells and full R-118 remain |
| M151-03 | Content-defined exact motif cache | NOT STARTED | Exact hash plus byte verification, variable span syntax, full byte accounting |
| M151-04 | Pitch/time/fractional-phase/spectral-envelope/reverse/loop/filter orbit | PARTIAL | Forward/reverse direction passes; pitch/time, fractional phase, envelope, loop, and filter remain |
| M151-05 | Partial-spectrum Basis ownership and perfect-reconstruction tiling | PARTIAL | Exact research oracle exists; native normative stream and global ownership gate remain |
| M151-06 | Cross-channel global dictionary and transfer/decay laws | PARTIAL | Shared gain/phase research path exists; bounded transfer and multichannel evidence remain |
| M151-07 | Source-filter, stochastic, and transient competition | PARTIAL | Typed decoder records exist; integrated encoder and one-cell RDO remain |
| M151-08 | Objective mixture factorization | NOT STARTED | Latent component candidates, exact synthesis/correction, dense-mix evidence |
| M151-09 | Persistent transform laws and CompoundBasis hierarchy | PARTIAL | Exact bounded Python chart exists; native emitted-stream integration and GPU chart remain |
| M151-10 | Local learned proposer and optional semantic hints | PARTIAL | Provider boundary oracle exists; local objective embeddings and recall union remain |
| M151-11 | Complete-byte, quality-constrained global selector | PARTIAL | Exact bounded chart and actual MFT1 plus whole-channel Truth/fallback pricing pass; standardized composite transport and lossy quality frontier remain |
| M151-12 | Orkela playback and inspection | PARTIAL | Windows/Android direct bounded MFT1 backend, version, changelog, and corruption gate pass; seek/listening/full-platform public pin remain |
| M151-13 | Full original/Resonith/official-Opus evidence | NOT STARTED | Complete R-118 union, reports, hashes, runtime, artifacts, public release |

No row changes to `DONE` until it passes all seven completion clauses in
decision R-151.

## 7. Mandatory corpus gate

Every material generation evaluates:

1. the pinned full speech reference;
2. the complete Emotional piano reference;
3. the complete Mozart reference;
4. all sixteen R-111 heterogeneous classes.

For every item, the report retains the original, actual decoded Resonith, and
actual decoded current official Opus artifacts. Opus is compared at matched
complete bytes and at a quality frontier; one convenient bitrate point is not
a general codec claim.

## 8. Immediate implementation order

1. multiscale/all-origin GPU search with portable CPU parity;
2. global quality-constrained selection with exact Truth fallback;
3. content-defined exact matching and bounded transform expansion;
4. partial-spectrum, channel, stochastic, source-filter, transient, mixture,
   and persistent-law integration;
5. Orkela backend update;
6. full R-118 evidence, versioning, changelog, hashes, and publication.
