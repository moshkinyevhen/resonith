# R-276 Resource Verdict and Recovery Audit

Date: 2026-08-03

Status: **INDEPENDENT AUDIT COMPLETE; RECOVERY MAP ACCEPTED**

## Question

This audit asks whether S11 through S17 rejected useful codec mechanisms because
of code-size, time, or memory ceilings rather than complete-byte and decoded-
quality evidence. It also resolves why S12 did not admit the S11 persistent
multi-partial mechanism.

Historical frozen experiments remain immutable. A resource failure is not
retroactively converted into a pass, its ceiling is not raised after observing
the run, and a disclosed auditor seed is never reused. Recovery means retaining
the underlying hypothesis in a later independently designed step, not rerunning
or relabelling a failed transaction.

## Verdict taxonomy

For this S11-S17 resource-versus-codec-result audit, the project distinguishes
five outcomes. This taxonomy does not replace any correctness, conformance,
security, portability, decoder-work, random-access, clipping, or failure-
behavior gate:

1. **Algorithm-negative:** an actually decoded candidate loses the declared
   complete-byte or quality gate. The exact candidate is not restored.
2. **Profile-negative:** execution exceeds a declared resource profile before a
   codec candidate can be judged. The profile failed; the algorithm remains
   unmeasured under other profiles.
3. **Harness-negative:** evidence infrastructure fails before codec execution.
   No algorithm conclusion follows, and the failed harness lineage is not
   reused.
4. **Preserved research mechanism:** the mechanism has bounded constructive or
   synthetic evidence but no real-corpus admission. It may enter a later union
   only through that step's complete RDO and comparison gate.
5. **Admission-negative:** a candidate fails a non-rate admission condition,
   including correctness, bounded decoder work, security, portability, random
   access, clipping, or failure containment. Its disposition follows the
   governing gate even if its bytes and objective quality are attractive.

Decoder, consumer-encoder, and Foundry-encoder resource profiles are separate.
The decoder remains strictly small and bounded. A consumer encoder must fit its
declared tier before product admission. A Foundry experiment may use a larger,
still explicit and reproducible host/GPU budget. Failure of one tier never
proves an information model useless, and success in a large tier never proves
consumer suitability.

## S11 and S12

S11 is a preserved research mechanism, not an admitted real-audio improvement.
Its focused gate proved bounded persistent multi-partial representation and one
synthetic delayed/antiphase stereo Pareto win: 14,051 complete bytes versus
15,813 direct-Truth bytes, with lower decoded SSE. That result explicitly did
not authorize a real-corpus claim.

S12 was accepted as a narrow evidence baseline, not as admission of S11. All 19
retained Resonith streams selected `truth-fallback`; R-224 later proved every
payload and decoded PCM output byte-identical to the pre-S11 direct-Truth
generation. Eighteen inputs did invoke the S11 analyzer and selected fallback.
Full Mozart did not invoke it: its 28,405,440-observation upper bound exceeded
the frozen 3,500,000-observation cap. Therefore:

- the current S11 candidate lost complete RDO on the 18 analyzed real inputs;
- S11 value on full Mozart is resource-profile-inconclusive;
- S12 remains a valid baseline, but it is not evidence that S11 improved a real
  stream and not a general better-than-Opus result.

The persistent multi-partial substrate stays available to S19, S21, S33, S35,
and S41. Gridless/streamed discovery in S27 and global RDO in S39 must remove
the monolithic observation blind spot before any renewed real-audio claim.

## S13 phase competition

S13 is dependency-negative rather than purely resource-negative. Full Mozart
and long LibriSpeech produced zero eligible phase-free lanes before the later
resource stop, so the exact carry/reset experiment had no candidate to judge.
The full *Elephants Dream* item then failed its configured host memory ceiling
before candidate publication, and the positive control did not execute.

The frozen S13 formulation is not rerun. Continuous/locked phase economics is
retained only where a later mechanism produces eligible structure: S33/S34 for
harmonic bundles and S35/S36 for cross-channel phase, delay, and polarity.

## S15 source-filter work

The R-232 decoder-domain rescoring form is profile-negative. Its first control
reached the frozen 900-second ceiling because Python performed per-candidate
synthesis and FFT work. No valid codec gate completed. The partial diagnostic
was promising enough to preserve the RDO idea: 12,371 bytes versus 12,554 and
lower decoded waveform SSE, but it is not an admitted result.

R-253 through R-266 are harness-negative. Their intended change was an output-
identical LPC-law reuse optimization, but the terminal run parsed ordinary
stderr as a framed length and failed before codec tests. The executables and
authority lineage remain quarantined; only the immutable-law reuse idea may be
reimplemented from a new minimal authority.

R-268 is algorithm-negative. Its candidate on the 319.38-second input used
995,104 bytes versus accepted-S12 975,280, reduced SNR, STOI, and ESTOI, and
closed only one required Opus gap despite improving log-mel. The frozen 38-Cell
candidate and its two routes are not restored. The broader source-filter/
resonator idea survives through new S37/S38 persistent resonator work and
S39/S40 global RDO, not through an R-268 retry.

## S17 inharmonic modal field

The exact R-271 sealed generation is profile-negative. Its only long run
crossed the frozen 2 GiB peak-RSS ceiling at 2,762,260,480 bytes, 614,776,832
bytes over budget, before producing a result transaction. N1, the registered
corpus, Opus, and S18 did not run. No complete-byte or decoded-quality verdict
exists.

The sealed run remains terminal and is not rerun with a raised ceiling. Source
inspection identifies a falsifiable memory-amplification hypothesis: the
research proposer caches whole-track rendered PCM for many candidate packs and
cluster targets. A later implementation may replace this with bounded
streaming/batched evaluation without reducing the candidate lattice. That work
belongs to S47/S48; the inharmonic resonator representation may be re-derived
under S37/S38, and heuristic recall expansion belongs to S49/S50. None of these
future mappings admits IMF1 today.

## Stable-step recovery map

| Historical mechanism | Classification | Existing recovery steps |
|---|---|---|
| S11 persistent multi-partial Basis | preserved research mechanism | S19, S21, S27, S33, S35, S39, S41 |
| S13 phase carry/reset | dependency-negative plus one resource-inconclusive input | S33-S36 |
| R-232 decoder-domain rescoring | profile-negative | S39-S40, S47-S48 |
| R-253 through R-266 exact LPC hoist | harness-negative; old lineage quarantined | S37-S38 or S47-S48 under new authority |
| R-268 38-Cell source-filter candidate | algorithm-negative | not restored; only a new model in S37-S40 |
| R-271 IMF1 sealed generation | profile-negative | new derivation in S37-S38; streaming/full search in S47-S48; optional proposer recall in S49-S50 |

The accepted 63 stable IDs are not renumbered or expanded. S17 closes as a
terminal no-change for its exact generation, S18 is not applicable, and S19 is
the next dependency-ready step. Recovery work is explicit inside the existing
later IDs above.

## Reproducible evidence ledger

| Finding | Direct evidence |
|---|---|
| R-221/S12 19-input comparison and all selected Truth fallbacks | [`../results/R221_S12_FIXED_OPUS_DIRECT_2026-08-02.md`](../results/R221_S12_FIXED_OPUS_DIRECT_2026-08-02.md); `G:/Resonith/artifacts/r221-s12-bounded-rate-direct` |
| R-224 proof of payload and decoded-PCM identity with pre-S11 | [`../results/R224_S13_PREDECESSOR_COMPARISON_2026-08-02.md`](../results/R224_S13_PREDECESSOR_COMPARISON_2026-08-02.md); `G:/Resonith/artifacts/r224-s13-predecessor-comparison/aggregate.json` |
| R-227 zero eligible phase-free lanes and later host-ceiling failure | [`../results/R227_S13_PHASE_POISONED_SHADOW_RESULT_2026-08-02.md`](../results/R227_S13_PHASE_POISONED_SHADOW_RESULT_2026-08-02.md) |
| R-241 900-second decoder-rescoring termination | [`../results/R241_S15_DECODER_RESCORING_TERMINAL_RESULT_2026-08-02.md`](../results/R241_S15_DECODER_RESCORING_TERMINAL_RESULT_2026-08-02.md) |
| R-266 pre-codec harness failure and quarantine | [`../results/R263_S15_RUN1_TERMINAL_FAILURE_2026-08-03.md`](../results/R263_S15_RUN1_TERMINAL_FAILURE_2026-08-03.md); [`../06_DECISION_LOG.md#r-266--r-263-run-1-terminal-failure-and-quarantine`](../06_DECISION_LOG.md#r-266--r-263-run-1-terminal-failure-and-quarantine) |
| R-270 actual long source-filter byte/quality loss | [`../06_DECISION_LOG.md#r-270--r-268-s15-terminal-long-first-no-change-result`](../06_DECISION_LOG.md#r-270--r-268-s15-terminal-long-first-no-change-result); `G:/Resonith/artifacts/r268-s15-long-speech-valid/speech-result.json` |
| R-271 terminal RSS failure before result publication | `G:/Resonith/artifacts/r271-s17-sealed-long/terminal-resource-failure.json`, SHA-256 `56181ee268516573c0ee5125554c65fb4fec071ece46f90f38be16154ab43170` |

## Independent audit

The independent auditor classified every S11-S17 mechanism, checked the S11
and S12 admission boundary, separated resource and harness failures from real
byte/quality losses, and issued this recovery map with no request to rerun a
frozen experiment. The audit specifically forbids restoring S13 unchanged,
reusing the R-253 through R-266 harness lineage, resurrecting R-268, or raising
the already observed R-271 ceiling.
