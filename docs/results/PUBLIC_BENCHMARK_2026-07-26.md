# Resonith 0.1.0-alpha.1 Public Reference Benchmark

Date: 2026-07-26  
Status: **MEASURED / PERCEPTUAL VERDICT OPEN**

This is the first versioned run of the continuous evidence gate. It compares
complete playable Resonith and Ogg Opus files made from identical PCM16 input.
The evaluated PCM comes from the actual decoders.

## References and anchors

| Reference | Canonical input | License |
|---|---|---|
| LibriSpeech `1272-128104-0000`, 5.855 s, mono 16 kHz | `speech-original.wav`, 187,404 bytes | CC BY 4.0 |
| Mozart, *Die Zauberflöte*, K. 620 — Overture, Musopen Symphony, 400.773 s, stereo 48 kHz | `mozart-original.wav`, 76,948,396 bytes | Public domain |

Speech comes from [OpenSLR 12](https://www.openslr.org/12/). The complete music
source is the public-domain
[Wikimedia Commons FLAC](https://commons.wikimedia.org/wiki/File:Mozart_-_Die_Zauberfl%C3%B6te,_K620_-_Overture_(Musopen_Symphony).flac).
The Mozart PCM16 input was deterministically derived from the lossless PCM24
FLAC before either codec was run.

The anchor is `opusenc` from opus-tools 0.2 using official libopus 1.6.1,
complexity 10, true VBR, 20 ms frames, and zero expected packet loss. A bounded
search matched complete Ogg bytes rather than nominal bitrate. Speech requested
24.0 kbit/s and music requested 122.5 kbit/s.

## Complete size

| Material | Resonith | Opus | Complete-byte difference |
|---|---:|---:|---:|
| Speech | 17,929 bytes / 24.497 kbit/s | 17,942 bytes / 24.515 kbit/s | Resonith 13 bytes smaller (0.072%) |
| Mozart | 6,508,774 bytes / 129.925 kbit/s | 6,510,191 bytes / 129.953 kbit/s | Resonith 1,417 bytes smaller (0.022%) |

These deliberate near-equal sizes are a quality comparison, not evidence of a
compression-ratio win.

## Speech diagnostics

Higher is better for SNR, SI-SDR, segmental SNR, magnitude cosine, peak
preservation, STOI, and ESTOI. Lower is better for log-spectral distance,
log-mel RMSE, spectral convergence, and error.

| Diagnostic | Resonith | Opus | Better |
|---|---:|---:|---|
| SNR | 19.619 dB | 9.297 dB | Resonith |
| SI-SDR | 19.571 dB | 8.755 dB | Resonith |
| Segmental SNR | 17.646 dB | 12.626 dB | Resonith |
| RMS error | 0.006472 | 0.021237 | Resonith |
| STFT convergence, 512 | 0.08211 | 0.18927 | Resonith |
| Magnitude cosine | 0.98362 | 0.97357 | Resonith |
| Log-spectral distance | 30.492 dB | 11.197 dB | Opus |
| Log-mel RMSE | 3.82491 | 0.60117 | Opus |
| Harmonic-peak preservation | 85.34% | 100.00% | Opus |
| STOI | 0.94989 | 0.99317 | Opus |
| ESTOI | 0.90297 | 0.98805 | Opus |

**Interpretation:** the current generic Resonith transform path stays closer to
the sample waveform, but Opus is decisively better on the speech-intelligibility
and low-energy spectral diagnostics at equal bytes. The next speech milestone
must test voiced/predictive Basis modeling and perceptual RDO. Merely reserving
more coefficients per frame already failed its kill-test.

## Mozart diagnostics

| Diagnostic | Resonith | Opus | Better |
|---|---:|---:|---|
| SNR | 34.588 dB | 21.343 dB | Resonith |
| SI-SDR | 34.586 dB | 21.319 dB | Resonith |
| Segmental SNR | 28.603 dB | 22.669 dB | Resonith |
| RMS error | 0.002060 | 0.009463 | Resonith |
| STFT convergence, 2048 | 0.01262 | 0.04836 | Resonith |
| Magnitude cosine | 0.99948 | 0.99889 | Resonith |
| Log-spectral distance | 21.509 dB | 7.101 dB | Opus |
| Log-mel RMSE | 2.02804 | 0.36641 | Opus |
| Harmonic-peak preservation | 98.41% | 100.00% | Opus |
| Median peak-amplitude error | 0.015 dB | 0.111 dB | Resonith |
| P95 peak-amplitude error | 5.011 dB | 2.755 dB | Opus |

**Interpretation:** Resonith preserves high-energy waveform and spectral
magnitude structure much more closely, while Opus better preserves broad
log-domain and mel detail, especially low-energy components. The diagnostics
do not establish which file sounds better. Controlled blinded listening is
required before a perceptual verdict.

## Timing and decoder provenance

- Resonith speech encode: 3.375 s on the development Xeon host.
- Resonith Mozart encode: 1,356.801 s, or 3.386 times source duration.
- CI-built native Windows x64 decoder SHA-256:
  `8abb937ba9329c04142b5a15c569cda3301a8f9aaf6838ab3683587310572848`.
- Native speech decode: 0.115 s; output hash matched the evaluated PCM.
- Native Mozart decode: 38.163 s, 10.50 times realtime; output hash matched the
  evaluated PCM.
- Prospective LPS5 encoder entry point: commit `5ea3ac1`.
- Native decoder utility: commit `fb2c360`.

Encoding timing is Python research-encoder evidence, not a C++ or GPU speed
limit. Hosted desktop timing is not mobile energy or thermal evidence.

## Artifact hashes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `speech-original.wav` | 187,404 | `799f78ed4beb4de7ceae3a809262d4ce242394342ccd1d58cef7d49dbc2def46` |
| `speech.resonith` | 17,929 | `a85b1308a252714298f9ac5155d29c45b7a763275a28eef88fcc38ffd3042e80` |
| `speech.opus` | 17,942 | `cbfdd8da42cb28a90a336bb162adbf72d3d6129b62ecc1e452a6da10220d67e6` |
| `speech-resonith-decoded.wav` | 187,404 | `eb34cdfb899ce76bf8e20a9d8260c021f6f6ca3d300c16c535eb8b654e5e6ce5` |
| `speech-opus-decoded.wav` | 187,404 | `8125700a4ceab5a34f4259e7168a38a8aac8c8b83bfe1230c2fe2e37e0c72b6a` |
| `mozart-original.wav` | 76,948,396 | `f9bcc829c8c61e850c8a15d7d25ec600a904b2041ed3bb4d9e13131ea30a5a6f` |
| `mozart.resonith` | 6,508,774 | `77eb9751603f4a37fae4ef961ab3423accbc0bef576ee2101f4081b3616edf8b` |
| `mozart.opus` | 6,510,191 | `760b7c1c2986eb7f73d222bfe1c1c3f079e44c950772689f26db259ac3b93d36` |
| `mozart-resonith-decoded.wav` | 76,948,396 | `d3f24bd494cea2e254edde2c07e0c9745e88b4226d5a205038494c664e58ec75` |
| `mozart-opus-decoded.wav` | 76,948,396 | `989c336a861618ea91b2752979e259ac0c785e3669c043f046988a7f803d28da` |

The machine-readable aggregate is
[`public_reference_benchmark_2026-07-26.json`](../../experiments/results/public_reference_benchmark_2026-07-26.json).
Raw per-decoder metric JSON files are attached to the GitHub release.

## Verdict

Resonith 0.1.0-alpha.1 is already a real independently decodable stream and is
competitive enough for meaningful equal-byte experiments. It is not yet
demonstrated to beat Opus perceptually. Speech is the clearer current loss;
music is objectively mixed and must proceed to blinded listening.

This result freezes the next optimization order:

1. voiced/predictive speech Basis;
2. log-domain/perceptual RDO that does not sacrifice Truth determinism;
3. blinded Mozart listening through the exact Orkela release;
4. rerun this unchanged evidence gate before accepting either mechanism.
