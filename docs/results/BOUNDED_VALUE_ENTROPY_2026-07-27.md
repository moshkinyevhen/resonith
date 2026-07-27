# R-113 Bounded Value Entropy

Date: 2026-07-27
Status: **passed as an RDO-selectable research mode**

## Outcome

Prospective LPS6 adds one explicit packet-local choice for sparse coefficient
values: bounded signed Rice or fixed-width packing. It retains LPS5 transform,
selection, scale, count, position, packet-reset, integrity, and allocation
rules. Ordinary LPS5 adaptive values remain the exact fallback.

The result is deliberately local rather than universal. LPS6 improved the
complete-byte-constrained speech point, reduced bytes without changing PCM on
complete piano and Mozart, and was selected for three of the 16 heterogeneous
classes. RDO retained LPS5 everywhere else.

## Mandatory complete references

| Reference | LPS5 | Selected | Saved | Budget | SNR change | Log-mel change | STOI change | ESTOI change |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Speech | 17,924 B | 17,904 B | 20 B | 67 → 68 | +0.1234 dB | -0.03925 | +0.000292 | +0.001502 |
| Emotional piano | 117,225 B | 117,115 B | 110 B | 71 | exact PCM | exact PCM | — | — |
| Complete Mozart | 6,526,665 B | 6,521,233 B | 5,432 B | 72 | exact PCM | exact PCM | — | — |

The speech stream passes the declared simultaneous gate:

- SNR: 19.7284 versus 19.6050 dB.
- STOI: 0.953871 versus 0.953579.
- ESTOI: 0.907409 versus 0.905907.
- Log-mel RMSE: 3.6510 versus 3.6903; lower is better.

The selected speech stream SHA-256 is
`86a375eb58d2f03f5a54ebb37297cb9dd527a74807f54e01057a65556ab54dfb`.

## Current Opus anchor

The change does not establish broad superiority over Opus 1.6.1. At the
previously pinned near-complete-byte-matched anchors:

| Reference | Resonith | Opus | Resonith SNR | Opus SNR | Resonith log-mel | Opus log-mel |
|---|---:|---:|---:|---:|---:|---:|
| Speech | 17,904 B | 17,942 B | 19.728 dB | 9.297 dB | 3.651 | 0.601 |
| Emotional piano | 117,115 B | 117,091 B | 40.536 dB | 26.006 dB | 0.964 | 0.443 |
| Complete Mozart | 6,521,233 B | 6,510,191 B | 34.851 dB | 21.343 dB | 1.892 | 0.366 |

For speech, Opus also remains ahead in STOI (0.993172 versus 0.953871) and
ESTOI (0.988045 versus 0.907409). Resonith remains ahead in waveform SNR but
behind in the declared speech-intelligibility and spectral-envelope metrics.

## Heterogeneous 16-class gate

All 16 base-budget LPS6 reconstructions were PCM-identical to LPS5. RDO chose
LPS6 for three classes:

| Class | LPS5 | LPS6 | Saved | PCM |
|---|---:|---:|---:|---|
| Female English speech | 89,069 B | 88,427 B | 642 B | exact |
| Male English speech | 90,389 B | 90,217 B | 172 B | exact |
| Dense pop | 183,512 B | 182,726 B | 786 B | exact |

The remaining 13 classes retained LPS5 because LPS6 was larger. Across the
whole 2,471,068-byte matrix, selected RDO output saved 1,600 bytes (0.0647%)
with no quality regression. This is useful syntax specialization, not a
revolutionary standalone compression gain.

## Native implementation and performance

The accepted LPS6 path is implemented in the allocation-free C++20 Core:

- native bounded entropy selection and serialization are byte-identical to
  the independent Python oracle;
- the native compact parser and decoder match Python PCM exactly;
- malformed entropy parameters, truncation, CRC corruption, and noncanonical
  padding are rejected;
- the first speech encode improved from 1.897 seconds in the Python-only path
  to 0.415 seconds in the native path, with identical stream bytes;
- shared immutable transform analysis reduced the measured two-budget speech
  encode phase from 0.852 to 0.622 seconds (1.37x) while preserving both
  candidate hashes.

The complete mandatory gate took 391.65 wall seconds because it encoded two
full Mozart budgets and ran concurrently with the 16-class gate. It is
evidence time, not a single-encode throughput benchmark. The separately
published single-budget R-112 result remains 155.866 seconds.

Native Core SHA-256:
`e0c95d18a40afecd9369c40f9244acf80f37bc66e8d9c751dd2b7c32b0310307`.

The complete Python/native suite ran 185 tests: 181 passed and four
unavailable external-device or external-tool integrations were skipped. The
strict Clang 22 C++20 build passed with all warning, conversion, pedantic, and
shadow diagnostics promoted to errors.

## Conclusion

LPS6 is accepted only as a prospective RDO-selectable research syntax. It
costs nothing on classes where LPS5 wins, gives a small exact-rate benefit on
some speech and dense material, and buys one higher speech coefficient budget
within the old complete-byte ceiling. The next large-gain work remains
band-local representation RDO rather than further universal entropy tweaks.

Machine-readable evidence:

- [`bounded_value_entropy_mandatory_2026-07-27.json`](../../experiments/results/bounded_value_entropy_mandatory_2026-07-27.json)
- [`bounded_value_entropy_r111_2026-07-27.json`](../../experiments/results/bounded_value_entropy_r111_2026-07-27.json)
