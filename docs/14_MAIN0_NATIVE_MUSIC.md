# First Native Typed-Stream Music Diagnostic

Status: **MEASURED-DIAGNOSTIC — NOT A CODEC VICTORY CLAIM**
Date: 2026-07-26

## 1. What changed

This is the first real-music experiment in which every Resonith candidate was
a complete typed RSC1 stream and had to pass the shared C++20 Golden Core
before RDO. The earlier MAF-P1 report used the generic Python `MAF0` container;
this run uses only `CONF`, `ATOM`, `BRAW`, and `RSL1`.

The source corpus, licenses, URLs, byte counts, and SHA-256 values remain pinned
by [`../experiments/real_music_corpus.json`](../experiments/real_music_corpus.json).
Each clip is a deterministic one-second mono crop at 44.1 kHz. Resonith uses
Innovation step 64, so maximum waveform error is bounded to 32. RDO competes
constant and continuous phase laws at four gain-event granularities.

GitHub Actions run:
[30198613411](https://github.com/moshkinyevhen/resonith/actions/runs/30198613411).
The downloaded raw report SHA-256 is:

```text
371154c136a254e2ad1cce61346a6c91529bbdcef66c99b50c95b0f3211502f4
```

## 2. Measured result

| Clip | Resonith q64 | SNR | Opus 48k actual | SNR | Opus 96k actual | SNR |
|---|---:|---:|---:|---:|---:|---:|
| Corelli realization | 97.22 kbit/s | 24.09 dB | 58.60 kbit/s | 19.31 dB | 117.96 kbit/s | 26.03 dB |
| Recorded piano | 113.34 kbit/s | 47.14 dB | 62.18 kbit/s | 25.81 dB | 118.46 kbit/s | 29.04 dB |
| Recorded drums | 119.59 kbit/s | 40.10 dB | 47.56 kbit/s | 21.92 dB | 99.38 kbit/s | 22.19 dB |

All byte rates include the complete RSC1 or Ogg file. The Opus runner in this
job is the Ubuntu package selected by the workflow; its exact executable
versions and hashes are retained in the raw artifact.

These rows are not perceptually matched. Waveform SNR strongly favors a codec
that preserves objective samples and does not predict listener preference.
The only defensible conclusion is that typed Main-0 is now measurable end to
end and lies in a useful diagnostic range; it does not yet prove superiority
over Opus.

## 3. Complexity evidence

| Clip | Eight-candidate Python encode | Native decode | Host workspace |
|---|---:|---:|---:|
| Corelli realization | 1.689 s | 1.393 ms | 546,220 bytes |
| Recorded piano | 2.190 s | 1.517 ms | 546,220 bytes |
| Recorded drums | 1.801 s | 1.572 ms | 546,220 bytes |

Native timing includes stream inspection, section integrity checks, binding
allocation, and whole one-second decode. It is already hundreds of times
faster than real time on the GitHub runner. The unoptimized Python encoder
evaluates eight complete candidates in roughly 1.7–2.2 times clip duration;
this is an encouraging consumer-encoder baseline, not a Foundry result.

## 4. Architectural signal

Every clip selected `constant-gain-4096`. The winning constant law used only
three endpoint knots, while the continuous candidate used twelve. The
continuous law changed SNR by very little and cost 53–200 extra bytes at the
same gain granularity.

This is useful negative evidence. A global continuous pitch track applied to
an entire polyphonic mix is not the missing revolution. Continuous phase
belongs on isolated long-lived sources; broad mixtures next need multiple
state-local Basis/Atom records and later simultaneous source Atoms. RDO must
remain able to select the constant law.

## 5. Listening artifact

The workflow artifact contains:

- source, Resonith, Opus 48k, and Opus 96k decoded WAVs;
- an opaque `A.wav` through `D.wav` trial directory per clip;
- `manifest.json` without codec identities;
- a separate `answer-key.json`.

The locally downloaded set is under
`artifacts/main0_native_music_ci_eb11b3d/listening`. Listen before opening the
answer key. This is an informal blind set; randomized presentation, trained
listeners, anchors, statistical analysis, and a proper MUSHRA UI remain open.

## 6. Next engineering gate

The next bitstream stage is state-local multi-Basis/multi-Atom partitioning in
typed RSC1. It must beat the one-Atom stream by complete native-decoded bytes
on at least two declared pitched/music clips, while safely falling back on
drums or noise. Only after that gate should simultaneous overlap and stereo
expand the decoder.
