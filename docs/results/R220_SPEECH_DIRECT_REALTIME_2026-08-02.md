# R-220 short/long speech direct and real-time diagnostic

Date: 2026-08-02

Status: **DIAGNOSTIC; NOT A CODEC GENERATION OR GENERAL QUALITY CLAIM**

## Scope

This owner-prioritized diagnostic compares the current R-218/S11 Resonith
pipeline directly with the same single fixed official Opus 1.6.1 point used by
R-219. Opus uses true VBR, complexity 10, 20 ms frames, speech application,
zero expected loss, 1000 ms maximum delay, default phase inversion, zero
padding, discarded comments/pictures, and four bitrate-only feedback attempts.
Selection uses complete-byte distance before quality is inspected.

The main R-219 registered-corpus process was suspended as a complete process
tree during this diagnostic so it could not distort real-time measurements.

## Inputs

| Input | Duration | Rate/channels | Provenance |
|---|---:|---:|---|
| Registered short speech | 5.855 s | 16 kHz / mono | `G:/Orkela/comparison/public-benchmark-2026-07-26/speech-original.wav` |
| Long clean speech | 319.380 s | 16 kHz / mono | 40 complete utterances from OpenSLR LibriSpeech `test-clean`, speaker 7127, with deterministic 250 ms inter-utterance silence |

The OpenSLR archive is CC BY 4.0. Its official MD5
`32fa31d27d2e1cad72775fee3f4849a9` passed. The downloaded archive SHA-256 is
`39fde525e59672dc6d1551919b1478f724438a95aa55f874b576be21967e6c23`.
The derived long WAV SHA-256 is
`0191f7d14edfc27ec9f0354adc9cbba77fc2482c5fd09505ffc5463ecb7316c8`;
its PCM16 payload SHA-256 is
`335384eab75a6a092adf5003c732a44b8a0ff9d4e710c3e8897d626f224d1b7f`.

## Equal-size quality results

Lower log-mel RMSE is better. Higher values are better for the other quality
axes.

| Input | Codec | Complete bytes | SNR dB | STOI | ESTOI | Log-mel RMSE | Magnitude cosine |
|---|---|---:|---:|---:|---:|---:|---:|
| Short | Resonith | 18,697 | 20.1347 | 0.954079 | 0.908387 | 10.43225 | not promoted |
| Short | Opus 1.6.1 | 18,702 | 9.3378 | 0.993335 | 0.988931 | 0.62545 | not promoted |
| Long | Resonith | 975,280 | 20.6356 | 0.953386 | 0.887884 | 7.28469 | 0.920089 |
| Long | Opus 1.6.1 | 975,265 | 7.9615 | 0.994818 | 0.986529 | 3.16581 | 0.938424 |

Resonith wins waveform SNR on both inputs. Opus wins speech intelligibility
and spectral/perceptual axes on both inputs. No aggregate speech-quality win is
claimed.

## Real-time results

`realtime x = source duration / measured wall time`; values above 1 satisfy
throughput real time on this host.

| Input | Codec/path | Encode wall | Encode realtime | Decode wall | Decode realtime |
|---|---|---:|---:|---:|---:|
| Short | Resonith | 33.1218 s | 0.1768x | 0.08472 s median | 69.11x |
| Short | Opus 1.6.1 | 0.11091 s | 52.79x | 0.05841 s | 100.24x |
| Long | Resonith | 27.1203 s | 11.78x | 4.48278 s median | 71.25x |
| Long | Opus 1.6.1 | 4.73504 s | 67.45x | 0.88759 s | 359.81x |

The duration-dependent RDO chose `truth-fallback` for the long input. It is
faster than real time, while the short analyzer-rich path is not. Both native
decode paths are comfortably faster than real time.

The public `resonith_decode.exe` currently rejects these S11 experimental
payloads with `bad magic`; decode timing therefore uses the same
`NativeMain0Decoder.decode_lapped` path that produced and hash-verified the
evaluated PCM. This CLI/experimental-stream integration gap is retained as a
product defect rather than hidden.

## Retained evidence

- Short root: `G:/Resonith/artifacts/r220-speech-direct/short-speech`;
  receipt SHA-256
  `e7744c4642261c523437bcb86998900c6da1031cac3ea858006fb24f91ca82f1`.
- Long root: `G:/Resonith/artifacts/r220-speech-direct/long-speech`;
  receipt SHA-256
  `ba164297f985f05b780038583d473a3151759e69c9eaefee618895b9ee542689`.
- Source/provenance root:
  `G:/Resonith/artifacts/corpus/librispeech-r220`.

The encoded Resonith/Opus files, actual decoded WAV files, request seals,
metric receipts, native decode timing records, source archive, derived WAV and
provenance manifest are retained at those paths.
