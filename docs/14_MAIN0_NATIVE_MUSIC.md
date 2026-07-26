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

## 6. State-partition kill gate

State-local multi-Basis/multi-Atom partitioning was then implemented in typed
RSC1 and verified through the same native decoder. Both one-second and
long-form runs kept the mandatory one-state fallback on every clip.

Long-form closest competitors:

| Clip | Duration | One state | Closest multi-state | Extra bytes |
|---|---:|---:|---:|---:|
| Corelli realization | 8.00 s | 86,711 | 87,460, adaptive 2-state | +749 |
| Recorded piano | 8.00 s | 107,430 | 108,214, adaptive 2-state | +784 |
| Recorded drums | 3.72 s | 42,801 | 43,495, fixed 2-state | +694 |

Run:
[30199317539](https://github.com/moshkinyevhen/resonith/actions/runs/30199317539).
Raw report SHA-256:

```text
403f1c48141ed730e66196bc9004f97a7109bc11c9b0408dd0feb192329dea4b
```

This gate failed. Sequential states remain a valid bounded syntax and the
native decoder correctly reuses maximum per-state workspace, but the encoder
must not select them on this corpus. The failure also survived Basis
amortization over eight seconds, so denser boundaries are not justified.

## 7. Next engineering gate

The next experiment is an encoder-side additive Atom oracle. It tests
simultaneous long-lived causes by matching pursuit, wide integer mixing, one
final LiftPack Innovation, and complete prospective RSC1 byte accounting.
Normative overlap/mixer syntax is added only if an extra Atom wins on at least
two declared clips.

## 8. Additive raw-Basis kill gate

The R-038 oracle searched autocorrelation fundamentals and subharmonics,
shortlisted candidates by objective residual energy, and ranked the survivors
by complete prospective RSC1 bytes. A two-period synthetic mixture selected
two Atoms and reduced 6,572 bytes to 5,198 bytes, proving that the search can
recover useful concurrent periodic causes.

The licensed one-second clips all selected one Atom:

| Clip | One Atom | Two Atoms | Four Atoms | Best residual change |
|---|---:|---:|---:|---:|
| Corelli realization | 12,042 | 12,857 | 14,340 | -150 bytes |
| Recorded piano | 14,167 | 14,960 | 16,510 | -142 bytes |
| Recorded drums | 14,964 | 15,834 | 17,504 | +92 bytes |

GitHub Actions run:
[30199790029](https://github.com/moshkinyevhen/resonith/actions/runs/30199790029).
The downloaded raw report SHA-256 is:

```text
7c6321d4b7265adfd9a62a5b8e1565a2ecd207393c288a3b916cf55927abd7de
```

This kill gate failed zero of three. Each extra full-lifetime periodic Atom
paid for a new 520-byte `BRAW`, an `ATOM` payload, and two directory records,
while barely changing LiftPack. Main-0 therefore does not gain overlapping
raw-Basis syntax from this experiment.

R-039 tests the narrower remaining explanation: useful tonal structure may
exist, but its representation must be an analytic or cached decoder Basis and
many records must share one directory entry. That experiment remains
encoder-side until its own complete-byte gate passes.

## 9. Analytic oscillator and zero-Atom result

R-039 replaced each 520-byte raw Basis with one verified fixed sine ROM and
batched all prospective oscillator records into one `HBNK` section. The
complete-byte result was:

| Clip | Raw-Basis anchor | Zero Atom | Selected analytic | Result |
|---|---:|---:|---:|---|
| Corelli realization | 12,042 | 11,402 | 11,402, 0 Atoms | oscillator rejected |
| Recorded piano | 14,167 | 13,539 | 13,535, 1 Atom | -4 bytes |
| Recorded drums | 14,964 | 14,207 | 14,207, 0 Atoms | oscillator rejected |

Run:
[30200069831](https://github.com/moshkinyevhen/resonith/actions/runs/30200069831).
Raw report SHA-256:

```text
6919c598e24cb1937617859aea6e75aee395c103ac4b58243290f17ed3d29fac
```

The analytic-bank gate failed one of three and no opcode is promoted. The
simpler result is stronger: an identically zero predictor reduced the complete
stream by 4.4% to 5.3% against the mandatory raw-Basis anchor on every clip.
R-040 therefore makes `CONF` plus `RSL1` with no `ATOM`/`BRAW` a normative
Main-0 form and a mandatory encoder candidate.

## 10. Native zero-Atom and LiftPack block-size RDO

The R-040 decoder path passed GCC, Clang, MSVC, all native conformance targets,
and the Python-to-C++ decoder-in-loop tests in
[run 30200277390](https://github.com/moshkinyevhen/resonith/actions/runs/30200277390).
It reports zero model workspace and reconstructs the q64 Truth stream through
the same native acceptance boundary.

R-041 then evaluated the existing LiftPack-1 block sizes per complete typed
candidate. It selected 32,768 samples for Corelli and piano, but 2,048 for
drums:

| Clip | Selected stream | Bitrate | Reduction vs one-state |
|---|---:|---:|---:|
| Corelli realization | 10,930 bytes | 87.44 kbit/s | 7.45% |
| Recorded piano | 12,740 bytes | 101.92 kbit/s | 6.07% |
| Recorded drums | 14,011 bytes | 112.09 kbit/s | 5.64% |

Run:
[30200401912](https://github.com/moshkinyevhen/resonith/actions/runs/30200401912).
Raw report SHA-256:

```text
85f2d8d72713d434a987e994186fb8b3a0dcbc275a4aaed0f756363578abb7af
```

Every clip selected `residual-only`; the periodic and sequential-state
candidates remain legal but lost RDO. Block-size RDO changes no decoder syntax
and is now the default unrestricted Main-0 encoder search.

## 11. Bounded LPC research gate

R-042 added one prospective integer LPC transform to the residual competition.
It retained the existing LiftPack transforms and entropy coders, fitted LPC
coefficients only in the encoder, quantized them to Q12, and verified exact
prospective decoding before counting complete RSC1 bytes. The gate required a
win beyond the already optimized RSL1 block-size anchor on at least two clips.

| Clip | RSL1 anchor | LPC candidate | Reduction | Selected block |
|---|---:|---:|---:|---:|
| Corelli realization | 10,930 bytes | 10,233 bytes | 6.38% | 16,384 |
| Recorded piano | 12,740 bytes | 11,953 bytes | 6.18% | 32,768 |
| Recorded drums | 14,011 bytes | 12,743 bytes | 9.05% | 4,096 |

Run:
[30200626416](https://github.com/moshkinyevhen/resonith/actions/runs/30200626416).
Raw report SHA-256:

```text
aa28153b943a530697df821f87e1bce05854c65416a49fb36ed8f95e2f49127d
```

The gate passed three of three. Order 16 was never selected in a winning
stream; selected blocks used orders 4, 8, or 12. This is evidence for the
bounded predictor, not for a larger maximum order. R-043 therefore promotes
the exact tested syntax as `LiftPack-2`/`RSL2`; it does not add a second
entropy coder or an open-ended predictor.

Canonical compact evidence:
[`../experiments/results/lpc_liftpack_oracle_2026-07-26_summary.json`](../experiments/results/lpc_liftpack_oracle_2026-07-26_summary.json).

R-043 then passed the independent Python/native bridge, the standalone LPC
rounding vector, and all native conformance targets on GCC, Clang, and MSVC:
[run 30201013628](https://github.com/moshkinyevhen/resonith/actions/runs/30201013628).
The full licensed production-decoder benchmark independently selected RSL2 on
all three clips:
[run 30201094754](https://github.com/moshkinyevhen/resonith/actions/runs/30201094754).
Its raw report SHA-256 is:

```text
4ca6a8f93743ea7725d5ba152f837f79c75af69a18324c599c7b8ab6c1edcb8e
```

The selected complete rates were 81.86 kbit/s for Corelli, 95.62 kbit/s for
piano, and 101.94 kbit/s for drums. Native whole-stream decode remained about
1.35–1.60 ms per one-second clip on the GitHub runner. This verifies the
implementation and earlier byte result; it remains a mono q64 waveform
diagnostic, not a matched-MUSHRA comparison with Opus.

Canonical compact native evidence:
[`../experiments/results/main0_lpc_native_2026-07-26_summary.json`](../experiments/results/main0_lpc_native_2026-07-26_summary.json).

## 12. Variable residual-lifetime gate

R-044 asked whether attacks and state changes need a separate transient
renderer at all. A research stream retained the exact RSL2 transforms, LPC,
entropy, and checksum but allowed encoder byte-RDO to choose variable block
lifetimes on a 512-sample boundary lattice.

| Clip | Fixed RSL2 | Variable lifetime | Reduction |
|---|---:|---:|---:|
| Corelli realization | 10,233 bytes | 10,204 bytes | 0.28% |
| Recorded piano | 11,953 bytes | 11,667 bytes | 2.39% |
| Recorded drums | 12,743 bytes | 12,160 bytes | 4.58% |

All three clips won, but the arithmetic mean was 2.42%, below the declared 3%
broad-corpus promotion gate. No new residual magic, version, or decoder rule
is therefore promoted. The drum result remains useful evidence for a future
attack-heavy class gate, but it does not justify broad Main complexity.

Run:
[30201682126](https://github.com/moshkinyevhen/resonith/actions/runs/30201682126).
Raw report SHA-256:

```text
1af06563bd5b6b666c11d9e0e98f92354085d7a92ddcb7a34ef3d71dcaf0ab0d
```

Canonical compact evidence:
[`../experiments/results/variable_block_oracle_2026-07-26_summary.json`](../experiments/results/variable_block_oracle_2026-07-26_summary.json).

## 13. Whole-stream reversible stereo gate

R-045 returned to the original licensed stereo channels and competed
independent left/right, reversible mid/side, left/side, and right/side maps.
All modes reconstructed the same independently quantized channel Truth.

| Clip | Independent | Selected | Reduction |
|---|---:|---:|---:|
| Corelli realization | 20,654 bytes | 20,654, independent | 0.00% |
| Recorded piano | 24,855 bytes | 24,855, independent | 0.00% |
| Recorded drums | 26,041 bytes | 25,932, left/side | 0.42% |

The 0.14% mean is far below the 12% gate. A global mid/side opcode is not
promoted merely because it is conventional; the next bounded oracle tests the
narrow missing factor of unequal gain and short inter-channel delay.

Run:
[30201931759](https://github.com/moshkinyevhen/resonith/actions/runs/30201931759).
Raw report SHA-256:

```text
7cf7eb825500ecc7c73aca4685cab2486a29ca1cec2742d0d0580d2790009030
```

Canonical compact evidence:
[`../experiments/results/stereo_lifting_oracle_2026-07-26_summary.json`](../experiments/results/stereo_lifting_oracle_2026-07-26_summary.json).

## 14. Cross-channel gain-delay gate

R-046 relaxed global mid/side into a one-MAC Q12 gain plus a signed delay from
-32 through +32 samples. Both channel directions were searched; residual
energy shortlisted four candidates per direction, and only complete bytes
could select one.

No candidate won. The best cross forms were 3.06% larger for Corelli, 6.99%
larger for piano, and 0.02% larger for drums than the R-045 fallback. This
closes simple whole-waveform stereo prediction for Main. R-047 moves the same
reversible question into two frequency-local bands without adding another
entropy coder.

Run:
[30202154571](https://github.com/moshkinyevhen/resonith/actions/runs/30202154571).
Raw report SHA-256:

```text
4486c9841f37410ce77fecf6671f74ebf49864566bae83d198e3ac18216e6df3
```

Canonical compact evidence:
[`../experiments/results/cross_channel_oracle_2026-07-26_summary.json`](../experiments/results/cross_channel_oracle_2026-07-26_summary.json).

## 15. Two-band stereo gate

R-047 applied one exact temporal Haar split per channel, then selected channel
lifting independently in the low and high coefficient bands. Like components
were concatenated into only two unchanged RSL2 streams.

The best research streams were larger than R-045 by 26.20% for Corelli,
43.73% for piano, and 18.94% for drums. The split destroyed substantially more
long-range LPC predictability than the band-local channel maps recovered.
No subband syntax is promoted, and the three simple waveform-domain stereo
families are closed.

Run:
[30202375474](https://github.com/moshkinyevhen/resonith/actions/runs/30202375474).
Raw report SHA-256:

```text
ec11fc6c9f58041f97d005365582c0af76acd54f3261ff4d7f11f6272150380f
```

Canonical compact evidence:
[`../experiments/results/subband_stereo_oracle_2026-07-26_summary.json`](../experiments/results/subband_stereo_oracle_2026-07-26_summary.json).

## 16. Production streaming and malformed-input hardening

R-048 deliberately added no compression syntax. The native Core now exports
canonical LiftPack byte/sample indexes, independent block reconstruction, and
a caller-owned forward cursor. The cursor verifies the residual envelope once,
advances only after successful block reconstruction, and makes complete
callback playback linear in stored bytes with one-block live workspace.

The Main-0 player opens a verified immutable RSC1 view. On the winning
zero-Atom Truth path it can either decode one requested block or stream every
PCM16 block through a C callback. Exact tests compare block, cursor, callback,
whole-native, and Python outputs.

Hardening passed:

- block index and random decode on GCC, Clang, MSVC, and the native Python
  bridge in [run 30202809934](https://github.com/moshkinyevhen/resonith/actions/runs/30202809934);
- the allocation-free player view in
  [run 30202987460](https://github.com/moshkinyevhen/resonith/actions/runs/30202987460);
- separate LiftPack and complete Main-0 ASan/UBSan/libFuzzer smoke targets in
  [run 30203095386](https://github.com/moshkinyevhen/resonith/actions/runs/30203095386);
- the linear cursor and callback player in
  [run 30203223428](https://github.com/moshkinyevhen/resonith/actions/runs/30203223428).

Each fuzz target executed 5,000 bounded mutations from deterministic valid
seeds. These runs are a reproducible hardening checkpoint, not a claim that
the parsers are free of every possible defect.

## 17. Callback playback and ARM portability diagnostic

The Python/native bridge now drives the public one-block callback ABI and
requires its complete PCM to equal the native whole-stream decoder. A repeated
licensed one-second run measured:

| Clip | Whole decode | Callback decode | Callback / real time |
|---|---:|---:|---:|
| Corelli realization | 1.623 ms | 1.685 ms | 0.169% |
| Recorded piano | 1.779 ms | 2.215 ms | 0.221% |
| Recorded drums | 1.817 ms | 2.008 ms | 0.201% |

The callback figures include the Python ctypes boundary and player
inspection/open work. They demonstrate ample desktop-runner headroom for
these one-second mono diagnostics; they are not a mobile deadline guarantee.

Run:
[30203460481](https://github.com/moshkinyevhen/resonith/actions/runs/30203460481).
Raw report SHA-256:

```text
bcb6e461df8488d40697b5ed525b9aa2676b04da363813b0d57a0f027e6fb61b
```

The identical source then passed native Linux ARM64, macOS ARM64, Windows
ARM64, and an Android NDK arm64-v8a build in
[run 30203385185](https://github.com/moshkinyevhen/resonith/actions/runs/30203385185).
This verifies source portability and deterministic conformance on the tested
runners; real phones still require device thermal, deadline, and battery
measurements.

## 18. Optional RSI1 seek sidecar

R-049 persists the already verified block index as a fixed source-bound
sidecar. The mandatory audio payload and sequential cursor remain unchanged.
Opening RSI1 verifies its CRC/SHA, the complete residual identity, and exact
equality between every entry and parsed source block.

For the one-second winners above, the optional table would contain 164 to 452
bytes depending on selected block size. Those bytes are zero for sequential
delivery because the sidecar is absent; a delivery profile that requires it
must count it in its complete rate.

The conformance implementation passed every x64/ARM64/Android target in
[run 30203602697](https://github.com/moshkinyevhen/resonith/actions/runs/30203602697).
Its dedicated 5,000-mutation ASan/UBSan/libFuzzer target passed in
[run 30203691322](https://github.com/moshkinyevhen/resonith/actions/runs/30203691322).

## 19. Model-bearing callback playback

The callback player now covers the complete executable Main-0 subset, not
only the residual-only winner. It keeps one LiftPack block live, prepares only
the maximum state-local Basis, trajectory, and gain arrays reported by
inspection, and divides prediction internally at Atom lifetime boundaries.
The application still receives canonical residual-sized PCM blocks, including
when one block straddles two model states.

The native pipeline vector, Python/native decoder-in-loop tests, and whole
Main-0 fuzzer require callback output to equal whole-stream native and Python
Truth sample-for-sample. A deliberately non-aligned state transition exercises
the cross-boundary path. Linux and Windows x64/ARM64, macOS ARM64, Android
arm64-v8a, GCC, Clang, MSVC, and sanitized fuzzing passed in
[run 30204031294](https://github.com/moshkinyevhen/resonith/actions/runs/30204031294).

This removes state-partition playback from the implementation critical path.
It does not reverse the earlier compression gates: additional raw periodic
Atoms still cost more complete bytes on the licensed clips. The next source
overlap experiment must first eliminate repeated raw Basis transport through
typed CIBS or another already gated shared representation.

## 20. Typed cached CIBS Basis integration

`BCIB` schema 1 closes the executable gap between the existing CIBS-0 kernel
and the production RSC1 path. Its stream payload contains only a registered
model ID, bounded int8 latent, declared mono Basis shape, and the expected
materialized-Basis SHA-256. Projection weights remain versioned decoder
registry state and are not repeated in every stream.

The native Core resolves model IDs without global state, rejects duplicate or
missing registry entries, computes exact resource bounds, and materializes
every cached Basis before the first PCM write or callback. CIBS and LiftPack
reuse one int64 staging allocation because the operations do not overlap. This
preserves the existing Main-0 workspace ABI and uses
`max(CIBS scratch, LiftPack scratch)` rather than their sum.

The Python reference builds a real typed stream from a trained mono CIBS model.
Whole native decode and callback playback reproduce the reference
sample-for-sample. Primitive conformance passed
[run 30204417294](https://github.com/moshkinyevhen/resonith/actions/runs/30204417294);
the integrated path passed Linux/Windows x64 and ARM64, macOS ARM64, Android
arm64-v8a, GCC, Clang, MSVC, native-bridge, and sanitizer gates in
[run 30204865673](https://github.com/moshkinyevhen/resonith/actions/runs/30204865673).

This is implementation evidence, not compression evidence. A fixed model ROM
must be trained without the evaluation segments, versioned, and reported
separately. Simultaneous source syntax remains blocked until cached Basis reuse
beats the complete RSL2 stream on held-out material.

## 21. Held-out cached-Basis overlap result

R-051 trained one fixed mono CIBS-0 model from 120 Basis examples extracted
only after the declared evaluation crops. The serialized registry occupied
5,160 bytes and was frozen before candidate ranking. On each one-second crop,
complete-byte RDO compared zero through four full-lifetime cached periodic
Atoms against the accepted zero-Atom RSL2 fallback.

The fallback won every clip:

| Crop | Zero Atoms | One Atom | RSL2 saving | Complete delta |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 10,233 B | 10,560 B | 57 B | +327 B |
| Piano | 11,953 B | 12,227 B | 78 B | +274 B |
| Drums | 12,743 B | 13,115 B | 12 B | +372 B |

The first Atom paid 88 bytes for `BCIB`, 104 or 136 bytes for `ATOM`, and
160 additional envelope/directory bytes. Later Atoms increased the complete
size further. This is a measured zero-win, 0% selected-mean result, so the
simultaneous mixer remains outside Main-0.

The result does not remove `BCIB`: the typed cached Basis path is executable
and may still serve a future long-lifetime single-cause representation.
It does show that replacing raw Basis bytes with a latent is insufficient by
itself; a future source model must remove substantially more Innovation or
amortize one state record across much longer useful lifetimes before it earns
new decoder syntax. The reproducible compact record is
[`cached_cibs_additive_2026-07-26_summary.json`](../experiments/results/cached_cibs_additive_2026-07-26_summary.json).

## 22. Independent-channel playback

The functional Main-0 fallback now carries one through eight channels without
adding a second codec or coupled transform. One `CONF` declares the frame
count, shared Innovation step, and channel count. Consecutive `RSL2` instances
carry independent channel residuals on one aligned block partition.

The Python encoder selects that common partition by complete aggregate RSC1
bytes. The native whole decoder validates every channel and preflights every
entropy path before writing interleaved PCM. The callback player retains one
channel block, one maximum LiftPack scratch region, and one interleaved output
block; it emits a frame interval only after all channels reconstruct at the
same offset and length.

The conformance bridge generates stereo PCM and requires equality among the
Python decoder, native whole decode, and native interleaved callback. GCC,
Clang, MSVC, Linux ARM64, Windows ARM64, macOS ARM64, Android arm64-v8a,
Python/native parity, and sanitized mutation coverage passed in
[run 30205820034](https://github.com/moshkinyevhen/resonith/actions/runs/30205820034).

This is a deployability result, not a stereo compression claim. Independent
channels are the required fallback because all earlier coupled waveform tools
lost their declared gates. A later source-aware stereo or spatial
representation must beat this executable fallback before replacing it.

## 23. Pull playback and packet-loss containment

The device-facing Core now exposes a caller-owned pull session. It retains one
forward cursor per channel and returns one aligned interleaved block per call.
Cursor advances are staged in local copies and committed only after every
channel succeeds. An undersized-output rejection leaves the session at the
same block; canonical exhaustion returns `NOT_FOUND`. Pull, whole, and
push-callback outputs are sample-identical. The complete cross-platform and
sanitized matrix passed in
[run 30206070812](https://github.com/moshkinyevhen/resonith/actions/runs/30206070812).

R-054 then lost one internal aligned block on each pinned stereo music crop.
Every frame outside that block, including the first following block, returned
to exact Truth. This confirms that block-local LPC seeds contain damage and no
concealment enters future prediction.

Complete-byte Main RDO selected 4,096-frame blocks, making a loss last 92.88 ms
at 44.1 kHz. A Realtime ceiling of 512 frames reduced the interval to 11.61 ms
but increased complete stream bytes by 12.95%, 13.37%, and 9.59% on Corelli,
piano, and drums respectively. The ceiling is therefore a latency/recovery
profile trade-off, not a compression improvement.

The current integer fade concealment is deliberately only a baseline. Its
quality was weak on exposed piano even though damage remained bounded. Future
PLC or FEC must be judged by matched listening and must never become Truth
reference state. The compact evidence is
[`packet_loss_2026-07-26_summary.json`](../experiments/results/packet_loss_2026-07-26_summary.json).

## 24. Stereo Opus frontier

The official Opus anchor now preserves stereo frame shape and reports complete
Ogg bytes plus executable hashes. R-056 swept Resonith scalar Innovation steps
and Opus VBR rates on all three one-second stereo crops, then generated opaque
source/Resonith/Opus listening trials.

At the nearest complete bytes to the Opus 96 kbit/s request:

| Crop | Resonith | Opus | Resonith SNR | Opus SNR |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 14,984 B | 15,356 B | 13.08 dB | 21.20 dB |
| Piano | 14,881 B | 15,552 B | 24.78 dB | 26.46 dB |
| Drums | 12,430 B | 12,599 B | 17.49 dB | 21.80 dB |

Waveform SNR is not perceptual equivalence, but losing all three same-size
sanity checks is enough to reject the residual-only baseline as competitive.
No listening result has yet been claimed. The exact next bottleneck is uniform
waveform quantization: it cannot allocate error by frequency or masking.

R-057 therefore tests one lapped perceptual Innovation path before any more
source-model syntax. RSL2 remains the mandatory fallback and Lossless path;
the transform candidate remains encoder research until complete bytes,
blinded listening, fixed-integer conversion, and independent decode all pass.
The compact R-056 record is
[`stereo_opus_frontier_2026-07-26_summary.json`](../experiments/results/stereo_opus_frontier_2026-07-26_summary.json).

## 25. Lapped Innovation objective sanity gate

The first R-057 oracle replaces uniform waveform quantization with one regular
50%-overlapped sine-window transform, low-frequency-dense band scales, and a
sparse signed coefficient grid. It remains outside Main-0 and uses zlib only
as an explicitly non-normative entropy proxy. The outer `RSC1` container,
transform metadata, band scales, coefficient payload, and checksums are all
counted.

At the nearest complete bytes to the official Opus 96 kbit/s anchor:

| Crop | Lapped | Opus | Lapped SNR | Opus SNR | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Corelli | 15,959 B | 15,356 B | 22.38 dB | 21.20 dB | +1.18 dB |
| Piano | 16,768 B | 15,552 B | 38.32 dB | 26.46 dB | +11.87 dB |
| Drums | 12,714 B | 12,599 B | 25.90 dB | 21.80 dB | +4.09 dB |

This passes the declared objective sanity gate on all three clips with a mean
waveform-SNR delta of +5.71 dB. Waveform SNR is not perceptual equivalence, so
no quality win is claimed. The generated opaque listening trials remain
unscored.

The representation now advances to engineering gates, not to normative
syntax. It must preserve the result after replacing zlib with bounded entropy,
converting analysis and synthesis to deterministic fixed-integer arithmetic,
passing native memory/timing gates, and completing blinded listening. RSL2
remains the exact Lossless and mandatory RDO fallback. The compact record is
[`lapped_opus_gate_2026-07-26_summary.json`](../experiments/results/lapped_opus_gate_2026-07-26_summary.json).

## 26. Bounded entropy and fixed-integer retention gate

R-058 removes the zlib proxy. Each transform frame now carries a fixed count
of sorted coefficient positions. Temporal band-scale deltas and signed values
reuse bounded escaped-Rice/fixed-width coding; coefficient gaps use a bounded
unsigned Rice form reset at every frame. No bitmap, adaptive probability
table, or general decompressor is required.

R-059 replaces decoder floating point with Q15 window and Q14 cosine ROM,
int64 MACs, exact overlap accumulation, and symmetric final rounding. The
prospective table bytes are identified by SHA-256 in the experiment report.

The combined path retained the objective gate:

| Crop | Fixed bounded | Opus | Byte ratio | SNR delta |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 16,395 B | 15,356 B | 1.068x | +4.63 dB |
| Piano | 14,780 B | 15,552 B | 0.950x | +11.87 dB |
| Drums | 12,842 B | 12,599 B | 1.019x | +6.23 dB |

This isolates the result from both zlib and floating-point reconstruction, but
does not promote `LPF1`. The next engineering gate is an allocation-bounded
native independent decoder using compiled reviewed ROM, followed by
cross-decoder PCM equality and measured timing. Blinded listening remains
mandatory because the SNR deltas are only waveform sanity diagnostics.

## 27. Native fixed/bounded lapped decoder

The prospective LPF1 path now has a separate C99 ABI and dependency-free
C++20 implementation. Inspection validates complete RSC1/CONF/LPF1 integrity,
entropy lengths, canonical padding, cross-section dimensions, and exact
caller-owned storage requirements. Decode reconstructs scale deltas, sorted
position gaps, and signed values before its first PCM write.

The synthesis kernel contains no floating point, allocation, lock, mutable
global state, or general decompressor. Two 2,049-entry int32 quarter-wave ROMs
serve every supported power-of-two half-window through symmetry and integer
stride. A conservative per-frame bound rejects any hostile coefficient/scale
combination that could exceed int64 during two-frame overlap.

The Python-authored static vector and dynamic native bridge require exact PCM
equality. GCC, Clang, MSVC, Linux ARM64, Windows ARM64, macOS ARM64, Android
arm64-v8a, and sanitized builds passed in
[run 30207598669](https://github.com/moshkinyevhen/resonith/actions/runs/30207598669).
This closes native feasibility, not perceptual quality or real-device timing.

## 28. Implicit acoustic-state boundaries

R-061 tests a simpler alternative to explicit state-boundary metadata. The
encoder receives one average coefficient budget, ranks quantized transform
coefficients globally across channel, time, and frequency, and transmits the
resulting per-frame count trajectory. Attacks naturally become dense frames;
sustain and silence become sparse frames. Position prediction still resets at
each frame, and zero-count frames are valid.

At closest complete fixed/adaptive bytes:

| Crop | Adaptive | Fixed | Byte difference | Adaptive SNR gain |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 15,844 B | 15,920 B | -76 B | +0.56 dB |
| Piano | 14,616 B | 14,588 B | +28 B | +0.79 dB |
| Drums | 16,810 B | 16,746 B | +64 B | +1.34 dB |

At the nearest Opus-size drum points, adaptive density used 12,514 bytes
versus 12,623 fixed bytes and improved the waveform diagnostic by +0.93 dB.
The original selected average budgets produced frame-count ranges of 0–98,
48–96, and 5–125 on Corelli, piano, and drums respectively.

The count trajectory therefore earns a native implementation gate. It does
not yet justify explicit transient classes or short-window syntax, and it is
not a listening result. The compact record is
[`lapped_density_2026-07-26_summary.json`](../experiments/results/lapped_density_2026-07-26_summary.json).

LSE2 now shares the allocation-explicit native LPF1 path with fixed-density
LSE1. Variable streams add only one caller-owned uint16 count array and one
existing signed entropy field. The parser verifies the decoded count sum
against the declared sparse total before positions or PCM are trusted.
Python/native exact PCM parity and the complete cross-platform matrix passed
in [run 30208161776](https://github.com/moshkinyevhen/resonith/actions/runs/30208161776).

## 29. Short-window kill gate

R-064 added deterministic multi-resolution spectral convergence and
onset-local pre-echo diagnostics, then compared the accepted 512-sample
half-window against an all-short 128-sample half-window at nearest Opus bytes.
Lower pre-echo values indicate less error immediately before strong source
onsets.

| Crop | Long bytes | Short bytes | Long/short SNR | Long/short pre-echo |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 15,409 | 15,828 | 25.59/20.56 dB | -27.60/-22.70 dB |
| Piano | 15,461 | 15,468 | 39.82/36.47 dB | -40.23/-36.38 dB |
| Drums | 12,514 | 11,920 | 28.84/26.64 dB | -25.46/-23.13 dB |

The long path won SNR, spectral convergence, and mean pre-echo on every clip.
On drums it also beat the Opus pre-echo diagnostic (-25.46 versus -19.36 dB)
at 12,514 versus 12,599 bytes. These metrics are not listening equivalence,
but they provide no evidence that short-window switching earns decoder state.
Mixed-window syntax is therefore closed, preserving one regular transform.
The compact record is
[`window_transient_2026-07-26_summary.json`](../experiments/results/window_transient_2026-07-26_summary.json).

## 30. Native host timing gate

The release C++ LPF1 decoder was built and timed in GitHub Actions run
30208323632 on the three pinned one-second stereo crops. Every sample first
passed exact Python/native PCM parity. Timing includes the ctypes call,
caller-array allocation, complete stream inspection and verification, entropy
decode, integer synthesis, interleave, and a NumPy copy.

| Crop | Stream bytes | Median decode | Real-time factor | Workspace |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 15,844 | 58.15 ms | 0.0581x | 397,358 B |
| Piano | 15,257 | 52.02 ms | 0.0520x | 399,968 B |
| Drums | 12,514 | 48.91 ms | 0.0489x | 389,528 B |

This is 17.2x-20.4x one-stream real-time margin on a hosted x64 runner despite
including conservative binding overhead. It clears the first native deadline
gate, but it is not a device-energy claim: physical Android/ARM64 thermal,
battery, concurrency, and hostile-stream worst-case measurements remain open.
The compact record is
[`native_lapped_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_timing_2026-07-26_summary.json).

## 31. Reusable encoder analysis

Lapped RDO normally evaluates several complete streams. The fixed transform,
band scales, quantized grid, and objective coefficient scores are identical
for every density budget, so R-066 makes them one immutable
`LappedAnalysis`. Selection, bounded entropy, complete RSC1 packing,
independent decode, and distortion measurement remain per candidate.

The six-budget fixed-integer adaptive frontier preserved exact payload bytes
for every candidate on all three pinned clips. A single local research-Python
pass measured 1.54x-1.59x end-to-end frontier speedup:

| Crop | Repeated analysis | Shared analysis | Speedup |
| --- | ---: | ---: | ---: |
| Corelli | 6.49 s | 4.21 s | 1.54x |
| Piano | 6.94 s | 4.36 s | 1.59x |
| Drums | 6.99 s | 4.47 s | 1.56x |

This is a development-path measurement, not a production throughput claim.
Its architectural value is larger than the Python number: immutable analysis
is a safe unit for parallel candidate selection and a direct handoff boundary
to a future batched C++/CUDA encoder. The compact record is
[`lapped_frontier_timing_2026-07-26_summary.json`](../experiments/results/lapped_frontier_timing_2026-07-26_summary.json).

## 32. Native forward-analysis boundary

R-067 moves the fixed Q15/Q14 forward transform behind the same stable C99 ABI
as the Golden Decoder. The caller first requests exact array sizes, then
provides interleaved PCM16 and caller-owned output arrays. The kernel returns:

- channel-major per-frame band scales;
- the complete signed quantized coefficient grid;
- exact unsigned squared transform scores for encoder-side selection.

It does not choose a bitrate, density law, entropy mode, or perceptual policy.
Those remain encoder/compiler decisions. This separation gives scalar C++,
SIMD, CUDA, and large teacher encoders one exact output contract without
expanding the player. Promotion requires Python/native parity across every
compiler target before any throughput claim.

That parity gate passed in GitHub Actions run 30209156633 on every supported
compiler/build target. The Python RDO can now explicitly request the native
analysis backend and is required to emit the same complete bytes as its
Python-fixed fallback. Scalar native throughput is deliberately not claimed
yet; SIMD/CUDA specialization must preserve this exact array contract.

## 33. Scalar forward-analysis baseline

GitHub Actions run 30209344885 measured the complete native analysis binding
after exact Python/native array verification. The scalar C++ kernel processed
one second of stereo in 269.80-270.27 ms, so it is already 3.70x real time.
However, NumPy's matrix path needed only 137.08-145.28 ms:

| Crop | Python/NumPy | Scalar native | Native versus Python |
| --- | ---: | ---: | ---: |
| Corelli | 145.28 ms | 269.80 ms | 0.54x |
| Piano | 137.08 ms | 270.27 ms | 0.51x |
| Drums | 143.80 ms | 270.22 ms | 0.53x |

This rejects the assumption that a direct C++ transcription is automatically
faster. The current inner loop repeats zero-padding tests, window lookup, and
window multiplication for every coefficient. Those operations can be hoisted
once per transform frame without changing arithmetic. That exact-preserving
rewrite is the next gate; explicit SIMD and CUDA remain downstream choices.
The compact record is
[`native_lapped_analysis_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_analysis_timing_2026-07-26_summary.json).

## 34. Exact invariant-hoisting result

R-069 materialized the padded, Q15-windowed input once per channel and
transform frame, then reused it across coefficient dot products. Multiplication
order and the Q29 accumulator stayed unchanged. All portability, sanitizer,
frozen-vector, and dynamic parity gates passed.

| Crop | Scalar baseline | Hoisted scalar | Kernel speedup | Versus NumPy |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 269.80 ms | 123.37 ms | 2.19x | 1.19x |
| Piano | 270.27 ms | 123.17 ms | 2.19x | 1.16x |
| Drums | 270.22 ms | 123.25 ms | 2.19x | 1.19x |

The portable scalar path is now approximately 8.1x real time without SIMD.
That changes the next optimization choice: repeated candidate reconstruction,
not forward analysis, dominates the current six-budget Python frontier. RDO
should invoke the already exact native decoder before CPU intrinsics or CUDA
are justified. The compact record is
[`native_lapped_analysis_hoisted_2026-07-26_summary.json`](../experiments/results/native_lapped_analysis_hoisted_2026-07-26_summary.json).

## 35. Production-decoder RDO result

R-070 uses the exact native Golden Decoder to reconstruct each packed
candidate before distortion measurement. The six-budget frontier still keeps
selection and bounded entropy in Python, but native forward analysis and
reconstruction now surround that policy layer.

| Crop | Python frontier | Native-backed frontier | Speedup |
| --- | ---: | ---: | ---: |
| Corelli | 2.68 s | 0.60 s | 4.48x |
| Piano | 2.74 s | 0.53 s | 5.17x |
| Drums | 2.21 s | 0.61 s | 3.60x |

Every candidate stream and every reconstructed PCM sample matched exactly.
Thus a normal hosted x64 CPU evaluates six complete candidates in less than
one second per second of stereo. This does not make Studio/Foundry search
free; it establishes that consumer encoding is already viable without a GPU,
while CUDA can be spent on broader candidate generation and teacher analysis.
The compact record is
[`native_lapped_frontier_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_frontier_timing_2026-07-26_summary.json).

## 36. Independent-context packet gate

`LPS1` divides the logical output into half-window-aligned packets. Each child
contains one half-window of real or zero source context before and after its
logical interval, is encoded as an independently valid LPF1/RSC1 stream, and
is trimmed back to the logical interval after decode. The fixed header and
every packet are authenticated independently, so progressive decode does not
wait for an end-of-file digest.

| Crop | Monolithic bytes | Packet bytes | Overhead | SNR delta |
| --- | ---: | ---: | ---: | ---: |
| Corelli | 46,265 | 49,409 | 6.80% | +0.15 dB |
| Piano | 44,583 | 47,840 | 7.31% | +2.64 dB |
| Drums | 36,170 | 38,675 | 6.93% | -0.26 dB |

All clips pass the declared 8%/−0.5 dB gate. More importantly, fixed-density
packet interiors are exactly equal to monolithic reconstruction, proving that
the context trim itself introduces no transform seam. Adaptive density may
allocate coefficients differently per packet; its waveform and seam-local
metrics are diagnostics, not listening equivalence.

This buys bounded memory, packet-local loss containment, random access, and
parallel decode with one mechanism and no persistent cross-packet state. The
native envelope parser and pull session remain mandatory before promotion.
The compact record is
[`lapped_streaming_2026-07-26_summary.json`](../experiments/results/lapped_streaming_2026-07-26_summary.json).

## 37. Native packet pull and hostile-input gate

The native Core now exposes an allocation-explicit `LPS1` session. Opening a
sequence authenticates its fixed header and every packet, validates each LPF1
child, and reports the largest child workspace and output buffer. Pulling one
packet decodes into caller-owned temporary PCM, copies only its central logical
interval, and commits the four-scalar cursor after the entire operation
succeeds. A rejected packet cannot partially advance playback.

The two-packet C++ conformance vector is exactly equal to monolithic
fixed-density reconstruction. The independent Python/native bridge also
generated an adaptive 8,192-frame sequence and required exact PCM equality.
GitHub Actions run
[30210231145](https://github.com/moshkinyevhen/resonith/actions/runs/30210231145)
passed GCC, Clang, MSVC, C99-header, sanitizer, and bridge jobs. Its dedicated
LPS1 libFuzzer target completed 5,000 mutations from both fixed- and
adaptive-density valid seeds.

This closes the implementation part of the bounded-memory gate, but it does
not yet claim network-loss recovery: `open` intentionally authenticates a
complete available sequence. The next transport experiment must prove that a
missing logical interval can be concealed without changing any later
authenticated packet, and must keep concealment outside Truth reference
state.

## 38. Hosted packet resource result

The release `LPS1` path passed its declared hosted resource gate on all pinned
three-second music crops:

| Crop | Median decode | Real-time speed | Complete workspace |
| --- | ---: | ---: | ---: |
| Corelli | 180.79 ms | 16.59x | 762,194 bytes |
| Piano | 162.07 ms | 18.51x | 764,864 bytes |
| Drums | 139.22 ms | 21.55x | 754,184 bytes |

All outputs matched the Python packet decoder exactly. The timed scope includes
complete-sequence preflight, packet and child authentication, caller-array
allocation, entropy decode, integer synthesis, context trim, interleave, and
the final NumPy copy. Thus packet independence has not introduced a material
hosted-CPU regression relative to the earlier 17x-20x monolithic LPF1 range.
This is not a mobile energy or thermal claim. The compact record is
[`native_lapped_packet_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_packet_timing_2026-07-26_summary.json).

## 39. Packet-loss containment and the short-packet limit

The transport-loss experiment removed one authenticated packet after
demultiplexing, concealed only its output interval, and decoded every later
packet independently. All three clips reproduced uninterrupted Truth exactly
outside the missing interval and from the first later packet onward. Thus
neither overlap, adaptive density, entropy, nor concealment contaminates future
reference state.

The same experiment exposed a rate limit. At 10,752 frames (243.81 ms), full
independent source context cost 23.80% on Corelli, 27.10% on piano, and 28.26%
on drums relative to monolithic LPF1. That is not acceptable as the default
Realtime profile. Approximately one-second packets retain their earlier
6.80%-7.31% file/parallel-decode result.

The next packet experiment must preserve exact containment while reusing one
global transform analysis. It may duplicate only the minimum transform-domain
boundary state, not independently re-analyze and reallocate an entire
contextual source crop. The compact result is
[`lapped_packet_loss_2026-07-26_summary.json`](../experiments/results/lapped_packet_loss_2026-07-26_summary.json).

## 40. Transform-boundary packet result

`LPS2` performs one global transform analysis and coefficient selection. A
logical interval spanning \(m\) half-windows carries only the \(m+1\)
transform frames that overlap its output; adjacent packets duplicate their one
common boundary frame. The authenticated child is direct LSE2 rather than a
repeated RSC1/CONF/LPF1 container.

| Crop | LPS1 context overhead | LPS2 transform overhead | LPS2 exact |
| --- | ---: | ---: | --- |
| Corelli | 23.80% | 7.53% | yes |
| Piano | 27.10% | 7.75% | yes |
| Drums | 28.26% | 7.68% | yes |

These are complete bytes for 243.81 ms packets. LPS2 output equals monolithic
LPF1 reconstruction exactly, and loss remains exactly confined to the missing
logical interval. The improvement changes no transform or sample DSP; it
removes redundant analysis, allocation, and nested headers. The compact record
is
[`lapped_transform_packet_2026-07-26_summary.json`](../experiments/results/lapped_transform_packet_2026-07-26_summary.json).

## 41. Native direct-LSE2 result

The native Core now parses direct packet LSE2 under authenticated envelope
parameters and routes it through the same bounded entropy and fixed synthesis
implementation as complete LPF1. No artificial container is materialized and
no second packet-only transform kernel exists.

The allocation-explicit pull session accepts both LPS1 and LPS2. LPS1 trims
one source-context half-window; LPS2 emits the direct logical reconstruction.
Both commit the cursor only after complete packet success. A frozen two-packet
LPS2 vector equals monolithic adaptive LPF1 exactly, and the dynamic
Python/native bridge confirms exact 8,192-frame parity.

GitHub Actions run
[30211517931](https://github.com/moshkinyevhen/resonith/actions/runs/30211517931)
passed every desktop, ARM64, Android, C99-header, sanitizer, and native-bridge
job. The packet fuzzer completed 5,000 mutations from valid fixed/adaptive
LPS1 and transform-boundary LPS2 seeds.

## 42. Hosted native LPS2 resource result

Thirteen 243.81 ms LPS2 packets preserve essentially the same throughput as
the earlier four approximately one-second LPS1 packets while sharply reducing
the maximum live child:

| Crop | Median decode | Real-time speed | Complete workspace |
| --- | ---: | ---: | ---: |
| Corelli | 179.25 ms | 16.74x | 190,767 bytes |
| Piano | 159.95 ms | 18.76x | 191,565 bytes |
| Drums | 140.63 ms | 21.33x | 195,345 bytes |

All Python/native outputs are exact. LPS1 required 754-765 KB in the comparable
hosted gate, so direct transform packets cut the maximum caller-owned storage
by approximately four times while carrying fewer bytes and shorter logical
intervals. This remains a hosted-CPU result, not a mobile energy claim. The
compact record is
[`native_lapped_transform_packet_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_transform_packet_timing_2026-07-26_summary.json).

## 43. Single-owner boundary result

`LPS3` removes the last duplicated transform state. Each selected frame belongs
to one packet; packet \(k\)'s final half-window becomes ready when packet
\(k+1\)'s first frame arrives. This introduces one half-window of lookahead but
no predictive reference.

| Crop | Independent LPS2 overhead | Single-owner LPS3 overhead |
| --- | ---: | ---: |
| Corelli | 7.53% | 2.98% |
| Piano | 7.75% | 3.67% |
| Drums | 7.68% | 3.10% |

Uninterrupted PCM remains exactly equal to monolithic LPF1. If one packet is
absent, the first later packet still decodes exactly; only the missing logical
interval and the preceding 512-frame half-window may require output-only
concealment. At 44.1 kHz that extension is 11.61 ms.

The result passes the declared 4% rate gate. The next oracle must jointly sweep
packet duration and half-window before LPS3 receives a native scheduler. The
compact record is
[`lapped_chained_packet_2026-07-26_summary.json`](../experiments/results/lapped_chained_packet_2026-07-26_summary.json).

## 44. First Realtime frontier: negative LPS3 result

The joint half-window and packet-duration sweep found no LPS3 point satisfying
the declared 50 ms latency, 15% complete-rate, 1 dB SNR, and 1 dB spectral
limits on every clip.

Shorter transforms paid in objective quality. Around 40 ms packets, H128 lost
1.08-6.37 dB SNR and 1.13-6.95 dB spectral convergence; H256 lost 0.60-3.36 dB
and 0.70-3.79 dB respectively. H512 preserved the anchor reconstruction
exactly at 46.44 ms estimated latency, but repeated per-packet LSE2 shape,
logical headers, and SHA-256 raised complete bytes by 20.63%-25.96%.

This is a useful negative result: transform quality and latency can coexist;
the blocker is repeated administrative data. R-080 therefore retains H512 and
compacts only the transport record. The compact record is
[`lapped_realtime_frontier_lps3_2026-07-26_summary.json`](../experiments/results/lapped_realtime_frontier_lps3_2026-07-26_summary.json).

## 45. Compact LPS4 Realtime candidate

LPS4 removes repeated global transform shape, logical packet fields, child
headers, and per-record SHA-256. Its authenticated sequence header fixes the
global shape, while each transport-framed record carries a 27-byte entropy
descriptor, compact entropy payload, and CRC-32. The record length is derived
from its entropy bit counts.

The unchanged R-079 frontier then found one common diagnostic pass:

| Property | H512 / approximately 40 ms |
|---|---:|
| Actual record duration | 34.83 ms |
| Required half-window lookahead | 11.61 ms |
| Estimated algorithmic latency | 46.44 ms |
| Complete-byte overhead, Corelli | 10.56% |
| Complete-byte overhead, piano | 12.37% |
| Complete-byte overhead, drums | 13.22% |
| SNR delta from monolithic H512 | 0.00 dB |
| Spectral delta from monolithic H512 | 0.00 dB |

This crosses the declared diagnostic threshold without changing transform
reconstruction. It does not yet establish a deployable Realtime profile:
native compact parsing and scheduling, cryptographically authenticated
transport, device energy and thermal measurements, and listening remain open.
CRC-32 detects accidental corruption but is not adversarial authentication.

The compact result is
[`lapped_realtime_frontier_lps4_2026-07-26_summary.json`](../experiments/results/lapped_realtime_frontier_lps4_2026-07-26_summary.json).

## 46. Native compact LPS4 result

The separate allocation-explicit C99 LPS4 API now preflights the complete
sequence, reports maximum current and one-record-lookahead resources, and pulls
one logical interval transactionally. Current and lookahead entropy fields live
in separate caller-owned workspaces; the unchanged integer synthesis kernel
renders their shared transform boundary without duplicating it in the stream.

The frozen vector, long stereo integration stream, every cross-platform build,
and the sanitized parser/entropy/synthesis mutation target pass. A corrupt
lookahead writes no PCM and does not advance the session.

The hosted real-music gate used the R-080 H512 point:

| Crop | Median complete decode | Complete workspace | Exact Python/native |
|---|---:|---:|---:|
| Corelli | 12.83x real-time | 29,810 bytes | yes |
| Piano | 14.39x real-time | 30,218 bytes | yes |
| Drums | 16.39x real-time | 37,976 bytes | yes |

Each 3-second crop contained 87 records of 1536 frames, or 34.83 ms at
44.1 kHz. Timing includes sequence preflight, CRC and entropy validation,
caller-array creation, two-record decode, synthesis, interleave, and NumPy
copy. It is hosted Linux x64 evidence, not mobile energy or thermal evidence.

The compact record is
[`native_lapped_compact_packet_timing_2026-07-26_summary.json`](../experiments/results/native_lapped_compact_packet_timing_2026-07-26_summary.json).
