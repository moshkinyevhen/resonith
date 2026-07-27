# R-107 Perceptual Gain-Shape Complete Gate

Status: **THREE-FILE ADMISSION PASSED; BREAKTHROUGH FAILED**

Date: 2026-07-27

## Outcome

R-107 improved the preceding Resonith result on all three complete mandatory
references. The declared three-file admission gate passed after exact
complete-file measurement with the release C++20 Golden Core in the loop.

R-107 did not beat Opus speech STOI or ESTOI, and its separate 16-class R-111
gate exposed content-dependent failures. It therefore remains an RDO fallback
and does not become a released universal default.

## Complete-file results

| Reference | Previous Resonith bytes | R-107 bytes | Opus bytes | R-107 vs Opus | Previous SNR | R-107 SNR | Opus SNR | Previous log-mel | R-107 log-mel | Opus log-mel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LibriSpeech | 17,929 | 17,924 | 17,942 | -0.100% | 19.6186 dB | 19.6050 dB | 9.2975 dB | 3.82491 | 3.69027 | 0.60114 |
| Emotional piano | 117,643 | 117,225 | 117,091 | +0.114% | 40.4330 dB | 40.5364 dB | 26.0062 dB | 1.05526 | 0.96367 | 0.44269 |
| Mozart, complete | 6,508,774 | 6,526,665 | 6,510,191 | +0.253% | 34.5878 dB | 34.8509 dB | 21.3430 dB | 2.02804 | 1.89211 | 0.36637 |

All rate differences are within the predeclared ±0.5% complete-container
matching bound.

## Speech gate

| Metric | Previous Resonith | R-107 | Opus 1.6.1 |
|---|---:|---:|---:|
| STOI | 0.949894 | 0.953579 | 0.993172 |
| ESTOI | 0.902969 | 0.905907 | 0.988045 |
| SNR | 19.6186 dB | 19.6050 dB | 9.2975 dB |
| Log-mel RMSE | 3.82491 | 3.69027 | 0.60114 |

R-107 improves both intelligibility metrics and log-mel error over the
preceding Resonith result while staying five bytes smaller. The SNR change is
-0.0136 dB and remains inside the admission bound. Opus still leads speech
intelligibility by a large margin, so the breakthrough target fails.

The optional short-lattice frontier produces 17,790 bytes and improves speech
STOI/ESTOI further, but its SNR regression exceeds the accepted bound. It is
retained as research evidence rather than selected.

## Mozart density frontier

One scalar coefficient budget could not hit the Opus size exactly:

| Budget | Complete bytes | Delta vs Opus | SNR | Log-mel RMSE | Encode wall time |
|---:|---:|---:|---:|---:|---:|
| 71 | 6,452,284 | -0.8895% | 34.6420 dB | 1.91701 | 386.815 s |
| 72 | 6,526,665 | +0.2530% | 34.8509 dB | 1.89211 | 385.976 s |

Budget 71 is a valid lower-rate frontier point but fails the ±0.5% matching
rule. Budget 72 is the selected admission point. A later packet-level RDO may
mix adjacent integer budgets to approach an exact target without new decoder
syntax; that optimization is not credited here.

The selected native-backed research encoder processed 400.773 seconds in
385.976 seconds, or 0.963x source duration (1.038x realtime throughput).
This is measured local research-path timing, not the final SIMD/CUDA encoder
target. The harness briefly held approximately 2.0 GB while source, candidate,
and analysis arrays overlapped; the decoder itself remains bounded, and the
evidence pipeline still requires chunked metrics and packing.

## Cross-content consequence

The [16-class heterogeneous gate](HETEROGENEOUS_GAIN_SHAPE_2026-07-27.md)
prevents the three-file pass from being generalized:

- higher Resonith waveform SNR on 12 of 16 classes;
- lower Resonith log-mel error on only 6 of 16 classes;
- simultaneous strong results on sparse attacks, side drum, grand piano, and
  dense orchestra;
- failures on sustained sine, pink noise, speech envelope, and several mixed
  classes.

The evidence supports R-108: predictive log-energy plus bounded integer PVQ,
with competing stochastic-envelope and transient-pulse operands inside the
same acoustic ISA. It does not support adding R-107 as the only shape law.

## Reproduction and artifacts

- [Selected machine report](../../experiments/results/perceptual_gain_shape_2026-07-27.json)
- [Budget-71 frontier report](../../experiments/results/perceptual_gain_shape_b71_2026-07-27.json)
- [Gate implementation](../../experiments/perceptual_gain_shape_gate.py)
- [Heterogeneous machine report](../../experiments/results/heterogeneous_gain_shape_2026-07-27.json)

Local selected streams and decoded WAV files:

```text
G:\Resonith\artifacts\r107-three-complete-native-b72-corrected-2026-07-27
```

Local budget-71 frontier:

```text
G:\Resonith\artifacts\r107-three-complete-native-2026-07-27
```
