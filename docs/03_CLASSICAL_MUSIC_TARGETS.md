# Classical music: model and goals

The status of all numbers in this document is **HYPOTHESIS / TARGET**, not a result.

## 1. Why the classics are both convenient and difficult

MAF Potential:

- stable pitches and harmonic relations;
- reuse of instrument timbre;
- score/motive structure;
- long resonances and room response;
- offline access to the entire work.

Difficulties:

- dense polyphony and crossing partials;
- vibrato, portamento, microdynamics and expressive timing;
- changing bow/breath/noise excitation;
- attacks without exact repetition;
- long reverberant mix;
- microphone noise and audience;
- timbre depends on the note, volume and articulation.

Therefore, “passing notes instead of waveform” is not enough. Score helps the encoder
find the basis and trajectories, but the precision of execution is ensured by Innovation.

## 2. Working bitrate hypotheses

When matched MUSHRA quality relative to the strongest applicable
Opus/xHE-AAC/USAC anchor:

| Material | Mature Resonith: saving hypothesis | Candidate stereo rate |
|---|---:|---:|
| Solo/pure sustain | 35–60% | 40–72 kbit/s |
| Chamber music | 30–50% | 48–80 kbit/s |
| Orchestra, good hall | 20–40% | 72–112 kbit/s |
| Dense choir/percussion/noisy live | 10–30% | 80–128 kbit/s |
| Broad classical corpus | 25–45% | content-adaptive |

The first working prototype, which gives 10–20% on a limited classical
corpus is considered a good research start. More than 50% on broad
transparent classical - stretch, not a promise.

Extreme Perceptual profile MAY reach 24–48 kbit/s stereo and large
savings, but it does not mix with claims about objective transparency.

## 3. Lossless

In Lossless exact Innovation is obliged to return the original PCM. For mastered
classical microphone/room/noise recordings and microscopic unpredictability
dominate in residual.

**HYPOTHESIS:** 0-15% gain against a strong FLAC-like anchor is realistic;
larger broad lossless gain is unlikely without a new result in
universal entropy modeling.

## 4. Mandatory benchmark contract

Claims are accepted only if:

- anchors are configured by experts and include full overhead;
- comparison is carried out separately with Opus and xHE-AAC/USAC;
- ITU-R BS.1534 MUSHRA, hidden reference and low anchors are used;
- listeners do not know codec;
- corpus includes solo, chamber, orchestra, choir, percussion, organ,
  historical/noisy recordings;
- startup, seek, checkpoint and dictionary bits are taken into account;
- reported confidence intervals and correction for multiple comparisons;- pre-echo, warble, pitch/phase, stereo image, reverb and
  timbre identity;
- objective metrics are secondary to listening tests.

## 5. Revolutionary bar

- less than 15% broad gain: an interesting tool, but not a new standard;
- 15–30%: strong competitor;
- at least 35% broad music/classical with equal MUSHRA and small decoder:
  revolutionary result;
- more than 50% broad transparent: historical stretch, requiring independent
  playback