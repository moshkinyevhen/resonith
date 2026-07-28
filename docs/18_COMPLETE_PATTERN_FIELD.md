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

The field is **gridless in meaning and tiled in execution**. Pattern onset,
duration, frequency support, and channel route are independent of transform
frames, entropy pages, checkpoints, render callbacks, and CUDA tile
boundaries. Evidence-grade discovery is the union of rolling exact origins,
content-defined anchors, overlapping regular origins at every declared scale,
cross-band/channel intervals, and direct plus CompoundBasis spans.

## 4. Objective candidate families

| Family | Required search |
|---|---|
| Exact motif | Identical PCM and partial-spectrum cells at every declared scale |
| Basis orbit | Crop, non-circular integer alignment, bounded phase, polarity, gain/envelope, pitch/time, fractional phase, spectral envelope, reverse/loop, stable short filtering |
| Persistent source-filter | Excitation and slowly changing filter/pitch/phase laws |
| Stochastic field | Counter-seeded law, spectral envelope, density, modulation, and channel correlation |
| Transient | Independent onset and attack support without long-window pre-echo |
| Cross-channel field | Shared Basis with delay, phase, decay/envelope, and bounded transfer |
| Hierarchical grammar | Direct motifs, transformed instances, CompoundBasis, and reusable state increments |
| Independent Truth | Always-available exact or quality-constrained fallback |

Mixture factorization is objective: the encoder may infer latent recurring
components from changing mixtures, but the stream does not need to name their
physical source.

The mandatory R-159 **Latent Source Pattern Field** runs the same pattern
search on both observed channels and inferred additive layers. A robust
component seen through different overlaps may become one immutable Basis even
when none of the complete mixed intervals match. Magnitude, phase,
cross-channel transfer, alignment and gain evidence are retained. Layer
counts and factorization laws are finite published candidates; direct mixtures
and independent Truth are never pruned by a separator.

R-160 turns those hypotheses into a **minimum-description anonymous field
grammar**. The target is not the physically true instrument or speaker. It is
the cheapest decoder-verifiable additive explanation:

\[
Y_c[n] =
\sum_s Route_{c,s}\left(
\sum_e T(\theta_e) Basis_{s,k_e}[n-\tau_e]
\right) + Truth_c[n].
\]

An anonymous field owns an immutable multiscale Basis dictionary, persistent
transform and route laws, and an exact sparse event ledger. A motif may connect
events separated by unrelated or overlapping events. Thus `A -> gap -> B` can
be one reusable rule without claiming that the complete mixture inside the gap
repeats.

Long material is represented preferentially as a DAG of smaller Basis and
finite laws rather than copied into a raw long dictionary entry. The initial
law set is deliberately small: literal, constant, affine, run-length, and
sparse-exception series. Partial-spectrum ownership must use
perfect-reconstruction integer lifting, and a single Truth correction is
applied only after all anonymous fields are summed. There is no independent
exact residual for every hypothetical source.

The first exact synthetic proxy reused one 128-sample latent Basis ten times
under changing gains and contamination and reconstructed identical PCM. Its
structured payload was 1,815 bytes versus a 2,491-byte independent lossless
proxy (27.14% smaller). A short uneconomic candidate was rejected at +49
bytes. The first event grammar also preserved a 24-occurrence cross-channel
gapped motif and all unrelated intervening events. These results validate
construction and signalling only; they are not complete Resonith, FLAC, or
Opus claims.

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
| M151-02 | Independent gridless multiscale and all-declared-origin discovery | PARTIAL | Native every-origin rolling hash, canonical content anchors, overlapping arbitrary intervals, cross-channel spans, and boundary-invariant tests pass; normative frequency cells and full R-118 remain |
| M151-03 | Content-defined exact motif cache | PARTIAL | Native rolling hash, byte/sample verification, arbitrary-start type-8 emission, and complete-byte fallback pass; variable-duration grammar and full corpus evidence remain |
| M151-04 | Pitch/time/fractional-phase/spectral-envelope/reverse/loop/filter orbit | PARTIAL | R-157 C++23/CUDA evaluates the complete declared fractional-phase, forward/reverse, constant/linear pitch-time and gain lattice with exact CPU parity; spectral envelope, loop/filter families, and full gate remain |
| M151-05 | Partial-spectrum Basis ownership and perfect-reconstruction tiling | PARTIAL | Exact research oracle exists; native normative stream and global ownership gate remain |
| M151-06 | Cross-channel global dictionary and transfer/decay laws | PARTIAL | Shared gain/phase research path exists; bounded transfer and multichannel evidence remain |
| M151-07 | Source-filter, stochastic, and transient competition | PARTIAL | Typed decoder records exist; integrated encoder and one-cell RDO remain |
| M151-08 | Objective mixture factorization | PARTIAL | R-159 latent changing-overlap oracle and exact cross-channel reconstruction pass; partial-spectrum integration, known-stem bound, native/GPU search, and complete-byte R-118 evidence remain |
| M151-09 | Persistent transform laws and CompoundBasis hierarchy | PARTIAL | R-160 exact sparse pair grammar supports unrelated intervening events and literal/constant/affine/RLE/sparse-exception laws; arbitrary-length DAG grammar, decoder audio integration, global selection, and real corpus evidence remain |
| M151-10 | Local learned proposer and optional semantic hints | PARTIAL | Provider boundary oracle exists; local objective embeddings and recall union remain |
| M151-11 | Complete-byte, quality-constrained global selector | PARTIAL | R-157 actual MFT1 plus whole-channel exact Truth/fallback gate selected 704 B versus 1,156 B independent Truth on the constructive gridless case; standardized composite transport and lossy/full-corpus frontier remain |
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

1. R-159/R-160 anonymous latent hypotheses and the exact sparse event ledger;
2. gridless per-band perfect-reconstruction candidates, non-circular phase/time
   alignment, and cross-channel routing;
3. arbitrary-length gapped motif DAG, persistent laws, and non-greedy
   CompoundBasis activation;
4. R-157 batched CUDA hypothesis evaluation with portable CPU parity and no
   declared-candidate pruning;
5. one global quality-constrained selector over dictionary, events, routes,
   laws, stochastic/source-filter/transient atoms, final Truth and checkpoints;
6. Orkela backend update;
7. full R-118 evidence, versioning, changelog, hashes, and publication.
