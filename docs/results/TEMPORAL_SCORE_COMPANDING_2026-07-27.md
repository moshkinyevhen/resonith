# R-117 Temporal Score Companding — Complete 19-Item Gate

Date: 2026-07-27
Status: **one narrow encoder-side selection; no default or syntax change**

## Outcome

The candidate applies a frame-energy exponent of `0.02` to the encoder's
global sparse-coefficient score. It uses the existing LPS6 bitstream and
native C++23 decoder. Exact zero remains the preceding R-113 search.

The complete R-118 union was executed: all three complete references and all
16 R-111 heterogeneous classes. Only the pinned LibriSpeech item passed every
complete-byte and quality condition. The other 18 items retained their exact
R-113 streams.

| Item | R-113 bytes | Candidate bytes | SNR delta | Log-mel delta | STOI delta | ESTOI delta | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| LibriSpeech, complete | 17,904 | 17,904 | +0.001986 dB | -0.006628 | +0.000779 | +0.000900 | selected |
| Emotional piano, complete | 117,115 | 117,116 | -0.000439 dB | -0.000241 | — | — | fallback |
| Mozart overture, complete | 6,521,233 | 6,522,140 | -0.010581 dB | -0.003253 | — | — | fallback |
| EBU claves | 182,000 | 183,232 | -0.000674 dB | -0.000008 | — | — | fallback |
| EBU cymbal | 169,405 | 170,380 | -0.020355 dB | -0.027536 | — | — | fallback |
| EBU dense orchestra | 193,566 | 198,382 | -0.001165 dB | -0.000041 | — | — | fallback |
| EBU dense popular mix | 182,726 | 182,763 | -0.004055 dB | -0.003652 | — | — | fallback |
| EBU electronic tune | 86,387 | 87,498 | -0.000045 dB | +0.000059 | — | — | fallback |
| EBU female English speech | 88,427 | 88,450 | -0.002187 dB | -0.006185 | +0.000037 | +0.000408 | fallback |
| EBU grand piano | 164,309 | 166,934 | -0.000011 dB | -0.000572 | — | — | fallback |
| EBU male English speech | 90,217 | 90,231 | -0.003457 dB | -0.003619 | +0.000788 | +0.001246 | fallback |
| EBU pink noise | 206,566 | 214,912 | -0.000917 dB | -0.005109 | — | — | fallback |
| EBU side drum | 180,465 | 182,194 | -0.000296 dB | -0.000214 | — | — | fallback |
| EBU soprano | 175,345 | 176,368 | -0.002934 dB | +0.000744 | — | — | fallback |
| EBU sustained sine | 83,061 | 83,204 | -0.000028 dB | +0.000019 | — | — | fallback |
| EBU vibrato gong | 83,341 | 85,320 | +0.000046 dB | +0.000097 | — | — | fallback |
| EBU violin | 186,405 | 187,817 | +0.002171 dB | +0.000273 | — | — | fallback |
| Xiph Elephants Dream film mix | 200,211 | 202,370 | -0.005170 dB | -0.002365 | — | — | fallback |
| Xiph Sintel film mix | 197,037 | 197,915 | -0.002264 dB | -0.002082 | — | — | fallback |

Lower log-mel delta is better. A fallback is not counted as a candidate
improvement.

## Interpretation

The two additional speech clips show the same direction as LibriSpeech:
slightly better intelligibility and spectral-envelope diagnostics. Their
streams nevertheless grew and their waveform SNR decreased, so the strict
gate correctly rejected them.

The experiment isolates the limitation of a file-global control. A small
score change can help a subset of speech frames but perturbs entropy and
allocation across an entire item. The next architecture experiment therefore
moves representation selection to bounded packets and individual bands.
PVE/PVQ, sparse Truth, transient, and stochastic candidates must compete
locally, with exactly one primary representation per band and the ordinary
R-113 path as a zero-cost fallback.

## Evidence

- [Three complete references](../../experiments/results/temporal_score_companding_complete_2026-07-27.json)
- [Sixteen heterogeneous classes](../../experiments/results/temporal_score_companding_r111_2026-07-27.json)
- [Gate implementation](../../experiments/temporal_score_companding_gate.py)

The final public-revision three-complete run took 263.424 seconds. The
concurrent 16-class run took 119.370 seconds. These wall times include mutual
CPU contention and are not codec throughput claims. All metrics came from
actual decoded PCM at source revision
`e52b0caeefdf601d50acf7e7ba8eec329620c5c4`.
