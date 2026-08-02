# R-221 S12 Fixed-Opus Direct Comparison

Date: 2026-08-02

Status: **COMPLETE; INDEPENDENT GO IN THE DECLARED DIRECT-COMPARISON SCOPE**

## Scope

R-221 compares the current S11 Resonith challenger with one fixed official
Opus 1.6.1 configuration at maximum complexity. Only the requested integer
bitrate is calibrated, without access to decoded quality. This is not an Opus
frontier, not a previous-Resonith comparison, and not a general
better-than-Opus claim.

The frozen run contains 19 registered inputs. Sixteen rows satisfy the strict
complete-byte tolerance. Three rows are retained as `UNMATCHED_NEAREST` and
are mechanically excluded from every equal-rate count and claim:
`ebu-female-speech-en`, `ebu-male-speech-en`, and `ebu-sustained-sine`.

Run identity:
`470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c`

Source revision:
`1c45376eebe7daa49904acae885c47d6d571cf87`

Local evidence root:
`G:\Resonith\artifacts\r221-s12-bounded-rate-direct`

Machine authorities:

- `aggregate.json` SHA-256:
  `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`;
- `REPORT.md` SHA-256:
  `a89dddd2f578712063973024cbcd0da2809f21189f11cf11ce8aa4fcc57ea534`;
- `run-index.json` SHA-256:
  `ed1d8e5505ccf0fe0af4b59725e1f5e1c30fefc67218aff9b3608b9046140ecd`.

## Complete per-item result

Every paired cell is `Resonith/Opus`. Lower is better for log-mel RMSE,
log-spectrum distance, registered channel-0 phase MAE, and pre-echo error.
Higher is better for SNR, magnitude cosine, and STOI. Pre-echo values farther
below zero represent less pre-echo energy. The phase column is explicitly
channel 0 for both mono and stereo inputs; it is not an all-channel aggregate.

| Item | Rate status | Bytes R/O | SNR dB R/O | Log-mel R/O | Log-spectrum dB R/O | Magnitude cosine R/O | Ch0 phase MAE rad R/O | Mean pre-echo dB R/O | STOI R/O |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mozart-full | STRICT_MATCH | 7002776/7002186 | 35.44/21.86 | 4.469/0.629 | 26.76/7.84 | 0.98293/0.99248 | 0.00324/0.03265 | -41.39/-24.70 | - |
| ebu-claves | STRICT_MATCH | 216421/216394 | 39.45/32.24 | 1.066/4.897 | 9.55/11.67 | 0.99609/0.95723 | 0.00315/0.00638 | -42.61/-39.67 | - |
| ebu-cymbal | STRICT_MATCH | 186476/186483 | 29.80/14.33 | 3.130/3.177 | 16.02/10.64 | 0.97579/0.98954 | 0.00583/0.07186 | -37.32/-19.58 | - |
| ebu-dense-orchestra | STRICT_MATCH | 215875/215826 | 44.94/20.19 | 0.581/3.229 | 7.89/12.41 | 0.99999/0.99728 | 0.00136/0.08696 | -47.54/-20.95 | - |
| ebu-dense-pop | STRICT_MATCH | 200033/200091 | 30.84/20.23 | 3.249/2.923 | 21.07/8.52 | 0.99910/0.99797 | 0.00430/0.03717 | -39.16/-25.05 | - |
| ebu-electronic-tune | STRICT_MATCH | 92311/92365 | 36.18/43.51 | 1.149/5.383 | 9.15/12.37 | 0.99996/0.80652 | 0.00194/0.00402 | -44.55/-46.83 | - |
| ebu-female-speech-en | UNMATCHED_NEAREST | 94816/92894 | 31.87/12.57 | 4.540/3.517 | 26.09/7.70 | 0.99195/0.93123 | 0.00377/0.15696 | -38.42/-17.54 | 0.9977/0.9983 |
| ebu-grand-piano | STRICT_MATCH | 181180/181150 | 32.25/29.36 | 1.804/3.257 | 12.93/11.43 | 0.99837/0.97581 | 0.00234/0.01668 | -43.24/-29.63 | - |
| ebu-male-speech-en | UNMATCHED_NEAREST | 95791/93616 | 33.90/14.25 | 4.126/3.570 | 25.17/7.43 | 0.99632/0.90622 | 0.00302/0.15305 | -40.37/-14.72 | 0.9692/0.9973 |
| ebu-pink-noise | STRICT_MATCH | 218382/218402 | 7.92/12.84 | 4.325/3.058 | 28.14/6.79 | 0.90568/0.97097 | 0.24374/0.10691 | -8.71/-13.31 | - |
| ebu-side-drum | STRICT_MATCH | 212211/212196 | 44.29/31.73 | 1.077/4.483 | 9.21/11.30 | 0.99903/0.93659 | 0.00268/0.01662 | -47.82/-35.68 | - |
| ebu-soprano | STRICT_MATCH | 195887/195948 | 40.10/31.13 | 2.756/3.124 | 18.88/9.24 | 0.99977/0.99640 | 0.00226/0.00913 | -43.00/-34.57 | - |
| ebu-sustained-sine | UNMATCHED_NEAREST | 86124/86508 | 37.83/43.85 | 1.608/3.564 | 9.39/15.09 | 0.99981/0.99853 | 0.00186/0.00371 | -41.76/-43.23 | - |
| ebu-vibrato-gong | STRICT_MATCH | 90008/89980 | 42.41/43.02 | 1.176/10.250 | 9.18/15.61 | 0.99933/0.98079 | 0.00221/0.00617 | -42.73/-42.48 | - |
| ebu-violin | STRICT_MATCH | 218630/218764 | 35.07/27.73 | 2.978/3.047 | 23.74/8.22 | 0.99970/0.99785 | 0.00253/0.01124 | -38.44/-32.68 | - |
| xiph-elephants-dream-film-mix | STRICT_MATCH | 214699/214698 | 28.74/22.24 | 4.593/0.376 | 28.25/5.95 | 0.99865/0.99892 | 0.00517/0.03630 | -37.26/-29.59 | - |
| xiph-sintel-film-mix | STRICT_MATCH | 213090/213112 | 37.03/21.62 | 3.928/0.489 | 24.72/7.03 | 0.99978/0.99947 | 0.00244/0.05221 | -43.79/-21.10 | - |
| emotional-piano | STRICT_MATCH | 126191/126203 | 41.01/26.78 | 2.081/1.142 | 12.31/11.15 | 0.99998/0.99969 | 0.00247/0.02182 | -41.83/-27.72 | - |
| speech | STRICT_MATCH | 18697/18702 | 20.13/9.34 | 10.432/0.625 | 57.19/10.63 | 0.81000/0.97200 | 0.02215/0.22742 | -25.16/-13.14 | 0.9541/0.9933 |

The strict short-speech ESTOI result is `0.9084/0.9889`. The two unmatched EBU
speech ESTOI pairs are `0.9862/0.9966` for female speech and `0.9313/0.9924`
for male speech; they are diagnostic only because their rates are not matched.

## Aggregate interpretation

The sixteen strict pairs cover 570.628 seconds. Their complete sizes total
9,602,867 bytes for Resonith and 9,602,500 bytes for Opus, a difference of 367
bytes or about 0.0038%.

Across those sixteen strict pairs, Resonith wins:

- waveform SNR on 13/16;
- registered channel-0 phase MAE on 15/16;
- mean pre-echo on 14/16;
- magnitude cosine on 11/16;
- log-mel RMSE on 9/16.

Opus wins detailed log-spectrum distance on 11/16. The strongest current
Resonith results are structured transients, dense orchestra, piano, and
modulated resonant material. The strongest negative results are pink noise,
short speech, full Mozart, and film mixes in log-domain spectral metrics.

This is a coherent diagnosis, not an admission of general superiority:
Resonith commonly preserves waveform timing, channel-0 phase, channel relation,
and attacks much more accurately, but its present Truth-heavy allocation spends
too few bits on low-energy spectral detail and speech-critical envelopes. S13
and later MAF steps must preserve the first advantage while repairing the
second.

## Runtime and resource evidence

The 19 inputs contain 606.628 seconds of audio. The current research Resonith
pipeline used 3,643.60 seconds of per-item process wall time in aggregate, or
about 0.167 times real-time throughput. Peak observed Resonith process RSS was
2,500,521,984 bytes. These are research-encoder measurements, not decoder or
product targets. The retained Opus selected-point encode/decode times do not
include all bounded rate-calibration attempts and therefore are not presented
as a fair end-to-end speed comparison.

## Independent audit

The independent audit revalidated all 19 receipt/authority chains, regenerated
all Opus PCM with the pinned official decoder, regenerated all Resonith PCM with
`NativeMain0Decoder`, replayed all metrics, and checked every bounded q5
transition. All PCM hashes and reported metrics matched; three ESTOI values
differed only by floating-point rounding from `2.22e-16` to `9.99e-16`.

Verdict: **GO for S12 completion in this narrow direct-comparison scope**.
There is no authorization for an Opus-frontier claim, a full-19 equal-rate
claim, a general better-than-Opus claim, a product release, or a `VERSION`
increment.
