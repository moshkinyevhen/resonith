# Remaining directions and forecast against audio anchors

Date: 2026-07-26
Status of all percentages: **HYPOTHESIS / TARGET**, unmeasured result.

## 1. How to read percentages

\[
Saving=\frac{R_{\mathrm{anchor}}-R_{\mathrm{MAF}}}
{R_{\mathrm{anchor}}}.
\]

Comparison is only valid if:

- the same source code and channel layout;
- matched MUSHRA/ABX quality;
- same algorithmic latency;
- identical packet-loss, random-access and checkpoint constraints;
- full accounting of basis, model, macro, index, FEC and startup bits;
- a separate result against each anchor.

The ranges below are paper forecast architectures. They are needed for selection
experiments and do not constitute a statement of achieved quality.

## 2. Cached learned Basis synthesis - **ACCEPTED as CIBS**

### Mechanism

Instead of directly transmitting all samples, `TIMBRE_BASIS` encoder transmits:

```text
quantized latent
+ optional small adapter
+ exact/quantized basis correction
```

One fixed versioned integer synthesizer runs only on `BASIS_SET`,
builds an immutable basis and caches it. Hot sample loop remains table lookup,
filter and mix.

### Potential gains

| Script | Additional savings on top of MAF Core |
|---|---:|
| Broad general audio | 2–8% |
| Long solo/chamber, sustainable source | 8–18% |
| Repeating timbres/electronic stems | 5–15% |
| Short clips | 0–3% |
| Noise, applause, dense stochastic mix | 0–2%; possible loss |

This is not saving the entire waveform. The mechanism compresses only a fraction of the flow,
occupied Basis. When the basis is already well cushioned on a long track, the effect
the total bitrate decreases quickly.

### Disadvantages

- fixed synthesis model ages along with the standard;
- bit-exact integer inference and conformance are required on all devices;
- startup latency, RAM and silicon area;
- out-of-distribution timbre returns a large basis correction;
- weights and adapters are necessarily included in bitrate/IP analysis;
- the new model version splits the decoder ecosystem.

### Solution

By decision R-014 the mechanism is included in Main-0 under the name
**CIBS - Cached Integer Basis Synthesis**. It is coding mode for
`BASIS_SET`, and not neural rendering of each sample. Interest gates now
determine not the presence of syntax, but the adoption of a specific CIBS model version.

## 3. Motif macros / Acoustic Programs

### Mechanism

Macro does not store the finished waveform, but the recipe for re-creating it already
existing atoms:

```text
PROGRAM_INSTANCE(
    program_ref,
    start_time,
    time_scale,
    pitch_scale,
    gain,
    bounded_overrides
)
```

Ostinato, drum pattern, accompaniment, chorus or game cue are transmitted one
times. Decoder or parser deterministically expands macro into regular
`ATOM_SET/END`; no new DSP operations appear.

### Potential gains

| Script | Additional savings on top of MAF Core |
|---|---:|| Broad music | 1–5% |
| Classics with repeating motifs | 2–8% |
| Pop/electronic/loop-based | 5–20% |
| Game stems, library cues, almost symbolic production | 15–35% |
| Speech, ambience, crowd/noise | about 0% |

MAF already reuses timbre and Control Basis, so macro only saves
the remaining group events, coefficients and repeated innovation patterns. Interest
Basis-synthesis gains cannot be added independently.

### Disadvantages

- live performance is almost never repeated sample-exact;
- microtiming, articulation and mix variation require overrides/Innovation;
- macro complicates seeking, editing, packet recovery and dependency graph;
- unlimited recipe language turns into musical VM;
- program lifetime errors can damage a long interval;
- on broad audio, service IDs may cost more than saved events.

### Solution

Do not prohibit, but keep outside Main-0. Only bounded declarative macro is allowed,
which expands into existing atoms. No loops, branches or
executable score language.

## 4. Generative Detail

### Mechanism

Low bitrate conditioning track controls neural vocoder/generator,
restorative:

- breath/noise and ambience;
- high-frequency texture;
- reverb microdetail;
- speech excitation;
- part of the musical timbre.

### Potential gains

| Script | Additional perceptual savings |
|---|---:|
| Speech at extremely low bitrate | 40–80% |
| Ambience/noise/foley | 30–70% |
| General music | 20–45% |
| Dense music with important timbre identity | 10–35% |
| Objective/lossless reconstruction | 0% gain allowance |

Here `matched quality` means subjective similarity/usefulness, not same
waveform truth. Modern neural papers show very low rates
possible, but use different models, corpora and quality contracts; they are not allowed
directly considered a victory over transparent waveform codecs.

### Disadvantages

- hallucination and voice/instrument changes are possible;
- unknown language, genre, timbre or noise can destroy the quality;
- heavy decoder, model storage, energy and startup;
- model licensing, updating and long-term decodability;
- generative output cannot be lossless or objective reference;
- MUSHRA can hide rare but critical semantic errors.

### Solution

Generative Detail is useful and will be explored, but only as discardable
`Perceptual` layer. It never changes Core state and is never used
in headline Truth-compression percentages.

## 5. Full MAF forecast vs. best standardized anchorsPercentages include accepted MAF Core. Cached synthesis and motifs are taken into account
only on appropriate lines and are not summed separately.

| Script | Basic strong anchor | Against Opus | Against the strongest specified standard anchor |
|---|---|---:|---:|
| Realtime speech, mono | Opus/EVS | 15–35% | 5–20% vs EVS |
| Clean speech/podcast, offline | Opus/xHE-AAC/EVS | 25–50% | 10–30% vs. best xHE-AAC/EVS |
| General mixed stereo | Opus/xHE-AAC | 20–35% | 10–25% vs. xHE-AAC |
| Dense pop/rock | Opus/xHE-AAC | 15–30% | 5–20% vs. xHE-AAC |
| Solo/chamber classical | Opus/xHE-AAC | 35–55% | 20–40% vs. xHE-AAC |
| Orchestra/choir/reverberant classical | Opus/xHE-AAC | 25–45% | 15–30% vs. xHE-AAC |
| Loop-based electronic/game stems | Opus/xHE-AAC | 35–60% | 20–45% vs. xHE-AAC |
| objective ambience/rain/crowd | Opus/xHE-AAC | 0–20% | −5% to +10% vs. xHE-AAC |
| Immersive persistent emitters/room | Opus multistream / IVAS / MPEG-H | 20–40% | 5–20% vs IVAS/MPEG-H |
| Lossless PCM | FLAC | not applicable | 0-15% vs FLAC |

A minus in the ambience line means that MAF MAY will require more bits. This
an important hostile class that cannot be hidden by the average result.

## 6. Frontier neural codecs - a separate league

In 2025–2026, research codecs appeared with very low declared rates:

- FocalCodec reports speech tokens 0.16–0.65 kbit/s;
- LDCodec reports an advantage of 6 kbit/s over Opus 12 kbit/s in the authors' tests;
- TQCodec explores high-fidelity music 32–128 kbit/s;
- other universal neural codecs are also optimized for generation/token
  usefulness, not just waveform transparency.

A direct MAF percentage against them would now be fiction: corpora are different,
latency, model size, packet loss, stereo, metrics and definition of quality.

Correct goals:

- **TARGET:** MAF Core outperforms standardized anchors by significantly
  smaller decoder and better long-term state semantics;
- **TARGET:** against frontier neural codec a comparable MUSHRA is achieved with
  lower model/state/energy or higher objective fidelity;
- ultra-low generative mode is compared only as a separate Perceptual
  profile.

## 7. My priority

1. Implement `TIMBRE_BASIS` oracle and CIBS integer kernel simultaneously.
2. Compare `LIFTING_ONLY`, `RAW_BASIS` and `CIBS_LATENT` with full bitstreams.
3. Measure the share of total bitrate occupied by Basis payloads. If they use
   only 5% of the stream, even ideal Basis compression cannot be revolutionary.
4. Add a motif macro after stable multi-atom tracks appear.
5. Develop the generative layer in parallel, but never mix it with
   Truth benchmarks.

This preserves the maximum potential gain. Decision R-014 includes the small
bounded CIBS kernel in advance; the experiment selects a specific model and
measures its actual value.
