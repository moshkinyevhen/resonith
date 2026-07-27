# R-107 Gain-Shape on the R-111 Heterogeneous Corpus

Status: **MEASURED DIAGNOSTIC; UNIVERSAL GATE FAILED**

Date: 2026-07-27

## Method

This is the first architecture test on all 16 prepared R-111 content classes.
Every row uses:

- the complete 12-second PCM16 crop;
- prospective complete LPS5 Resonith transport;
- the release C++20 Golden Core for analysis and decoder-in-the-loop
  reconstruction;
- one ordinary energy selector and one R-107 gain-shape selector at the same
  coefficient budget;
- Opus true VBR, complexity 10, 20 ms frames, and music/speech application as
  appropriate;
- a bounded Opus bitrate search selected by actual complete Ogg bytes against
  the complete gain-shape Resonith bytes;
- objective metrics from actual decoded PCM.

The native Core SHA-256 is
`c0728edc95f7aec76ba8724a65f50c37c1f3c8041bc06335903552d263984a28`.
The Opus tools identify as `opus-tools 0.2-39-g9b1ca51` with
`libopus 1.6.1-8-g475cbc5`.

The complete matrix took 474.800 seconds on the local workstation. Timing
includes two Resonith encodes, repeated Opus size search, three decodes,
metrics, and artifact writes per clip; it is not a single-encode throughput
claim.

## Complete-byte-matched results

Log-mel ratio is Resonith error divided by Opus error; lower than `1.0` favors
Resonith. The gain-versus-energy columns isolate the R-107 encoder change from
the Opus comparison.

| Clip | Resonith bytes | Opus bytes | Rate delta | SNR delta vs Opus | Log-mel ratio vs Opus | R-107 bytes vs energy | R-107 log-mel ratio vs energy |
|---|---:|---:|---:|---:|---:|---:|---:|
| EBU claves | 182,000 | 181,997 | +0.002% | +8.925 dB | 0.069x | -1,190 | 0.891x |
| EBU cymbal | 169,405 | 169,410 | -0.003% | +15.311 dB | 2.602x | -10,836 | 0.971x |
| EBU dense orchestra | 193,566 | 193,534 | +0.017% | +24.638 dB | 0.035x | -2,678 | 0.751x |
| EBU dense popular mix | 183,512 | 183,515 | -0.002% | +11.058 dB | 3.110x | -10,215 | 0.971x |
| EBU electronic tune | 86,387 | 86,411 | -0.028% | -7.203 dB | 0.500x | +431 | 1.003x |
| EBU female English speech | 89,069 | 89,112 | -0.048% | +18.874 dB | 2.968x | -4,444 | 0.986x |
| EBU grand piano | 164,309 | 165,232 | -0.559% | +3.869 dB | 0.319x | -4,496 | 0.954x |
| EBU male English speech | 90,389 | 90,435 | -0.051% | +19.376 dB | 2.453x | -3,930 | 0.981x |
| EBU pink noise | 206,566 | 206,574 | -0.004% | -4.888 dB | 2.920x | -6,616 | 0.902x |
| EBU side drum | 180,465 | 180,451 | +0.008% | +13.398 dB | 0.040x | -691 | 0.789x |
| EBU soprano | 175,345 | 175,358 | -0.007% | +9.518 dB | 1.350x | -8,578 | 0.957x |
| EBU sustained sine | 83,061 | 83,060 | +0.001% | -5.562 dB | 1.413x | -214 | 1.001x |
| EBU vibrato gong | 83,341 | 83,341 | 0.000% | -0.610 dB | 0.331x | -51 | 1.004x |
| EBU violin | 186,405 | 186,405 | 0.000% | +7.630 dB | 2.709x | -10,276 | 0.980x |
| Xiph Elephants Dream film mix | 200,211 | 200,245 | -0.017% | +6.772 dB | 5.977x | -8,958 | 0.970x |
| Xiph Sintel film mix | 197,037 | 197,041 | -0.002% | +15.593 dB | 5.418x | -8,669 | 0.976x |

The grand-piano rate difference is 0.559%, just outside the nominal 0.5%
matching band. It is retained and explicitly marked rather than silently
treated as exact matching.

## Speech intelligibility

| Clip | Resonith STOI | Opus STOI | Resonith ESTOI | Opus ESTOI |
|---|---:|---:|---:|---:|
| EBU female English speech | 0.997552 | 0.998060 | 0.985599 | 0.996114 |
| EBU male English speech | 0.968699 | 0.997305 | 0.929854 | 0.992232 |

Resonith retains a very large waveform-SNR lead on both files but does not
beat Opus intelligibility. The male-speech result confirms that the earlier
LibriSpeech gap is structural rather than a one-file anomaly.

## What passed and what failed

- Resonith has higher waveform SNR on 12 of 16 classes.
- Resonith has lower log-mel error on 6 of 16 classes.
- R-107 emits fewer complete bytes than the same-budget energy selector on 15
  of 16 classes.
- Sparse attacks, side drum, grand piano, and dense orchestra are strong
  simultaneous SNR/log-mel results.
- Sustained sine and pink noise lose both headline diagnostics.
- Speech, solo voice, violin, cymbal, dense popular music, and film mixes show
  the existing high-SNR/poor-envelope tradeoff.
- The R-107 universal promotion gate therefore fails. The result does not
  establish perceptual superiority and does not change decoder syntax.

## Architecture consequence

One scalar sparse-shape law is not enough. R-108 must preserve the current
strong Innovation path while competing bounded band-local representations:

1. predictive log-energy plus integer PVQ for coherent shape;
2. transmitted envelope plus counter-based stochastic detail for noise-like
   bands;
3. sparse transient pulses for attacks;
4. the existing R-107 and energy paths as exact fallbacks.

This is one acoustic ISA and one RDO competition, not three separately framed
codecs. The next gate must improve speech intelligibility and the sustained/
noise failures without surrendering the measured transient and dense-orchestra
wins.

## Evidence

- [Machine report](../../experiments/results/heterogeneous_gain_shape_2026-07-27.json)
- [R-111 source manifest](../../experiments/extended_audio_corpus.json)
- [Prepared corpus identities](../../experiments/results/extended_audio_corpus_prepared_2026-07-27.json)
- [Gate implementation](../../experiments/heterogeneous_gain_shape_gate.py)

Local listening and stream artifacts:

```text
G:\Resonith\artifacts\r111-gain-shape-full-2026-07-27
```
