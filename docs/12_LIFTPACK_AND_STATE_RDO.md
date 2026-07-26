# LiftPack-1 and Full-Stream Acoustic-State RDO

Date: 2026-07-26
Status: **IMPLEMENTED / EXPERIMENTAL RESULT**

## 1. Outcome

This phase replaced the temporary zlib-array waveform residual with a native
bounded residual transport and tested automatic acoustic-state boundaries on
licensed PCM music.

Two conclusions survived the kill-test:

1. `LiftPack-1` reduced the complete MAF stream on all three declared clips.
2. Acoustic features may propose boundaries, but only complete-stream RDO may
   commit them.

The feature-only partition was sometimes worse than a fixed lifetime. The
codec therefore retains fixed candidates and is allowed to decide that a
plausible musical boundary is not worth coding.

## 2. LiftPack-1

LiftPack-1 divides quantized objective Innovation into bounded independent
blocks. For every block, the encoder competes:

- `IDENTITY`;
- first-difference lifting;
- second-difference lifting;
- reversible integer Haar lifting.

Each transformed coefficient vector then competes:

- escaped Rice coding with \(k \in [0,20]\);
- fixed-width zigzag packing.

The encoder selects the smallest actual payload. The decoder receives explicit
transform and entropy IDs and performs no classification.

Important properties:

- exact integer round-trip before the outer residual quantizer;
- block-local damage and bounded unary Rice prefix;
- no learned table or floating-point decoder behavior;
- canonical zero padding;
- stream and container checksums;
- a raw/stored container section, avoiding a second zlib layer;
- exact Lossless reconstruction when the residual quantizer equals one.

Reference implementation:
[`../reference/maf_p0/residual.py`](../reference/maf_p0/residual.py).

The first 192-coefficient conformance vector produces 203 bytes with SHA-256:

```text
6d58812162388dfe58c2b602372bf144d36af00f7a19cb39250e0d920609fee6
```

## 3. Acoustic-state candidates

The encoder-only candidate generator extracts:

- log energy;
- zero-crossing rate;
- spectral centroid;
- spectral flatness;
- twelve broad log-spaced spectral bands.

Robustly normalized features enter a bounded dynamic program with minimum and
maximum state lifetimes. This produces plausible half-open intervals but does
not authorize bitstream state.

Reference implementation:
[`../reference/maf_p0/segmentation.py`](../reference/maf_p0/segmentation.py).

## 4. Full-stream boundary RDO

The final compiler competes multiple fixed and adaptive partitions. Every
candidate is completely encoded, including:

- Basis payload and lifetime;
- Atom table;
- pitch/phase knots;
- gain laws;
- transient payload, when enabled;
- LiftPack residual;
- container and hashes.

At one residual quantizer, the smallest complete stream wins. This gives the
desired paradoxical rule:

> Understanding may propose structure, but structure exists in the bitstream
> only when it is cheaper than not understanding.

This is intentionally encoder-asymmetric. A Foundry encoder may search many
partitions; a decoder still executes only the selected state graph.

## 5. Reproducible real-music corpus

The manifest pins URL, byte count, SHA-256, license, credit, and crop:
[`../experiments/real_music_corpus.json`](../experiments/real_music_corpus.json).

Sources:

- [Emotional piano](https://commons.wikimedia.org/wiki/File:Emotional_piano.wav),
  CC0 1.0, credited to triangelx;
- [Patró de bateria](https://commons.wikimedia.org/wiki/File:Patr%C3%B3_de_bateria.wav),
  CC BY-SA 4.0, credited to Escola Superior de Música de Catalunya;
- [Corelli Violin Sonata Op. 5 No. 9](https://commons.wikimedia.org/wiki/File:Corelli_Violin_Sonata_Op_5_No_9.wav),
  public-domain score realization.

The source audio is not committed. The benchmark downloads and verifies it,
then performs a deterministic signed PCM16 mono downmix. Total declared crop
duration is 19.72 seconds.

Command:

```powershell
$env:PYTHONPATH = "$PWD\reference"
python experiments\real_music_benchmark.py `
  --opus-tools $env:RESONITH_OPUS_TOOLS `
  --output experiments\results\maf_p2_real_music_2026-07-26.json
```

## 6. Measured residual ablation

All MAF rows use q64, the same periodic model, transient path disabled, and
complete container bytes.

| Clip | Fixed zlib kbit/s | Fixed LiftPack kbit/s | Byte reduction |
|---|---:|---:|---:|
| Corelli realization | 126.78 | 92.45 | 27.08% |
| Recorded piano | 280.05 | 114.80 | 59.01% |
| Recorded drums | 140.52 | 96.87 | 31.06% |

LiftPack passes the declared kill-test on every clip. This is a result against
the repository's previous zlib residual, not a universal entropy-coder claim.

## 7. Measured segmentation ablation

| Clip | Feature-only vs fixed | Full RDO vs fixed | RDO selection |
|---|---:|---:|---|
| Corelli realization | −0.82% | +2.22% | fixed 2 s, 4 Atoms |
| Recorded piano | +1.12% | +2.38% | fixed 2 s, 4 Atoms |
| Recorded drums | −5.77% | +2.04% | adaptive penalty 800, 2 Atoms |

Positive values mean fewer bytes. Feature-only segmentation is therefore not
accepted as the final decision rule. Complete-stream RDO wins all three
declared comparisons and safely falls back to a simple fixed lifetime twice.

## 8. Diagnostic comparison with Opus

| Clip | Resonith RDO q64 | SNR | Opus 48k actual | SNR | Opus 96k actual | SNR |
|---|---:|---:|---:|---:|---:|---:|
| Corelli realization | 90.41 | 25.82 dB | 53.62 | 21.21 dB | 106.26 | 26.89 dB |
| Recorded piano | 112.07 | 46.24 dB | 59.35 | 25.65 dB | 114.56 | 29.48 dB |
| Recorded drums | 94.90 | 39.68 dB | 42.48 | 19.88 dB | 92.20 | 22.28 dB |

The Opus columns count complete Ogg files. This remains a diagnostic:

- the local official tool is linked with libopus 1.3;
- q64 and Opus do not represent matched perceptual quality;
- waveform SNR does not predict MUSHRA;
- all current MAF results are mono downmixes;
- the corpus is small.

The piano and drum waveform results are promising enough to continue, but they
are not a claim that Resonith already beats modern Opus.

Canonical raw report:
[`../experiments/results/maf_p2_real_music_2026-07-26.json`](../experiments/results/maf_p2_real_music_2026-07-26.json).

Two independent complete runs produced the same canonical report SHA-256:

```text
5996c5591210f041ecd14542bd08453d82ad4f863759e1237a4beccc03981578
```

## 9. Native typed-stream RDO gate

The first executable RSC1 encoder search now competes constant and continuous
phase laws plus multiple sparse gain-event granularities. Every candidate is:

1. packed as complete `CONF`/`ATOM`/`BRAW`/`RSL1` bytes;
2. decoded by the independent Python reference;
3. decoded by the shared C++20 Golden Core through the stable C ABI;
4. rejected unless sample rate and every PCM sample match;
5. ranked by complete stream bytes only after that acceptance gate.

The binding loads only an explicitly named library, asks the native inspector
for exact workspace counts, and rejects allocations above a configured host
ceiling. CI builds the shared Core from the same sources as the static
conformance library and runs this RDO path.

This closes a major validity gap in the earlier `MAF0` experiments: encoder
search can no longer optimize behavior accepted only by the Python oracle.

## 10. Next gates

1. ~~Port LiftPack-1 and whole typed-stream decode to the portable C++20
   Golden Core, then bind it into final candidate RDO.~~ Implemented.
2. Add stereo decorrelation and independently coded channel residuals.
3. Add multi-Atom overlap so a state boundary does not require replacing the
   entire active acoustic field.
4. Add current Opus and xHE-AAC anchors.
5. Generate decoded WAV sets for blinded MUSHRA.
6. Expand the licensed corpus across solo instruments, ensemble, speech,
   ambience, and hostile noise.
