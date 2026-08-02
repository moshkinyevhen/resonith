# R-218 S11 output-identical performance result

Date: 2026-08-02

Status: **INDEPENDENT CLOSEOUT PASS; IMMUTABLE COMMIT PREPARATION**

## Scope

R-218 is a mechanical performance remediation for the frozen S11 generation.
It does not alter public syntax, decoder behavior, candidate bounds, search
order, RDO, quality, timeout/resource ceilings, or the fixed R-217 Opus anchor.
R-218 performs no Opus encoding and makes no compression claim. Its purpose is
to make the already authorized direct S12 Resonith-versus-Opus comparison
executable.

Independent pre-code GO authorized only sequential A -> exact gate -> B ->
exact gate -> C -> exact gate under preflight SHA-256
`9900e569df3fd6f33ef637a0d4f0c525196664fb8eee756b1e4c6abb768641b7`.

## Implemented checkpoints

- **A — indexed conflict walk:** replaced the materialized
  `ordered[position + 1:]` tail with an indexed walk over the same elements in
  the same order. The time-window break and union order are unchanged.
- **B — one stable PCM conversion:** converted the immutable PCM16 input to
  exactly representable float64 values once rather than once per FFT frame.
  Concurrent input mutation is explicitly outside the deterministic contract.
- **C — exact DTFT intermediate reuse:** reused the exact
  `frame * window[:, None]` intermediate, relative-sample vector, and window
  normalization. `np.exp`, multiplication order, and `np.sum(..., axis=0)`
  remain unchanged. No batching, BLAS, GPU, fast-math, or approximate phase is
  present.

Final analyzer SHA-256:
`c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c`.

## Exact internal identity

The evidence helper hashes every integer/Boolean, exact IEEE-754 float bits,
container order, ctypes field, ndarray dtype/shape/raw bytes, candidate
allocation report, conflict group, fixed graph input, edge/path, lowered lane,
evaluated subset, and stable RDO ledger. `elapsed_seconds` is the only excluded
non-semantic report field.

All 30 baseline comparisons passed exactly: seven focused cases, active
88,200-frame claves and cymbal prefixes, and full claves, each after A, B, and
C. Every comparison reproduced:

- `combined_internal_sha256`;
- selected payload SHA-256 and complete bytes;
- selected decoded PCM16 SHA-256 and selected kind.

The focused combined identities were:

| Case | Combined internal SHA-256 |
|---|---|
| stable tone | `9914604bf3caae1b80acda30e87e838bd7ef20a1f30e6f63d068728448fa0193` |
| crossing | `13c39d38b0f58d0384ed031d6d3d77f7e956d58b4c67b3fdbc6eba384c69fc30` |
| birth/death | `d9af9d9cd72d09dc9907c740cfeff5ab951f26c7140aca8807f7a9b1a050a9d1` |
| gap/reappearance | `dd036f41319316a4ce2c39116e88b9833c1098ae987c0873489f7eef8dbf43a2` |
| noise | `ae06567980a62471566ded1e0edb6b4d19ff1ee31e32f4d34c9a3afd2f36e9c9` |
| transient | `39406a52ccf7425bd3d1ced8e3784dfd3c8bf879567d94a7d695fa086bba39d4` |
| delayed antiphase stereo | `c8b64b893aee3f93b3cfd753c4f98c81137c774482e47c04ec6f036924d9e944` |

Real-input identities:

| Input | Combined internal SHA-256 | Payload SHA-256 | Decoded PCM16 SHA-256 |
|---|---|---|---|
| claves prefix | `765b9e654662952873299141e6cffef0f8729c93ad3b9253ad141c7b1d3953dc` | identical A/B/C | identical A/B/C |
| cymbal prefix | `770918d470367c5d0695fd72657834faff68be74ce360b8c542261684038dab7` | identical A/B/C | identical A/B/C |
| full claves | `79c11ca6b160d80330c30944e82d59207b8b7e4157d5984d3b7826f019a34a2b` | `9156b28ec67b25c6fc222a52d74431e9cf656f67b7bc01409e94ff4e601927dd` | `32a3e399fd6b747aa14f372f1d1447b93290e133cce99e888fba17eb2f6fb96e` |
| full cymbal repeat | `30c5bb7d38c254a3ae9159c9377a0e6f132aaf5d4c7ea33ccaba5a6a6d29c34c` | `1f149b8ca110f17782b673a9cb7c84903b37b094ccd8301e88ef41bc4265fe5b` | `782f7cedf6fa10bd4fa5600c605c086e2edca18fd7528706e6d036cb239ae9cb` |

The full incumbent cymbal could not complete inside the old 900-second bound,
so no dishonest full pre-change identity is claimed. Its active prefix is
exact across A/B/C, the transformations are operation-order proofs, and the
new full result repeated exactly.

## Runtime

All full timings below are isolated S11 encode wall time; canonical hashing is
outside `encode_seconds`.

| Checkpoint | Full claves seconds | Change |
|---|---:|---:|
| incumbent | 774.105972 | baseline |
| A | 237.670336 | -69.2974% vs incumbent |
| B | 220.386926 | -7.2720% vs A |
| C | 196.590282 | -10.7977% vs B |
| C repeat | 208.920764 | deterministic repeat |

C is 3.9377x faster than the incumbent full claves result (-74.6042%). Both C
claves runs pass the <=475-second gate.

Full cymbal completed in 233.343736 seconds and repeated in 239.125873 seconds.
Both pass the unambiguous <=600-second remediation gate; the old path exceeded
its 900-second hard timeout.

## Resources

The first closeout audit rejected the helper's self-reported temporary-disk
field and the missing historical A/B resource telemetry. A/B remain semantic
identity checkpoints only; their resource admission was withdrawn rather than
reconstructed by redundant reruns. The old 2,724/2,723-byte helper JSON files
are not resource evidence.

Final C was then repeated under independently audited parent gate SHA-256
`3128e5f75dc5bf1955aec9515ba35c1cd8672aced3c86137cd1a84ce9436d198`.
The parent used a suspended active-process-limit-1 Windows Job Object, sampled
operating-system memory and the reparse-free staging tree every 10 ms, failed
above a measured 25 ms gap, and hashed every authority before and after.

| Input | Encode | Parent wall | Peak working set | Job peak memory | Samples | Max gap | Receipt-inclusive disk high-water |
|---|---:|---:|---:|---:|---:|---:|---:|
| full claves final C | 193.272769 s | 256.040667 s | 782,192,640 B | 2,038,001,664 B | 25,598 | 10.6424 ms | 9,995 B |
| full cymbal final C | 229.107934 s | 302.371870 s | 848,003,072 B | 2,104,680,448 B | 30,231 | 11.0230 ms | 9,973 B |

Both remain far below the unchanged 8 GiB RSS and 2 GiB per-item disk ceilings.
The prior R-217 claves product-path peak was 777,949,184 bytes; the final
fingerprint-instrumented claves repeat is 4,243,456 bytes (+0.5455%) above it
while retaining internal objects for evidence. No limit was raised. The new
un-instrumented direct-comparison run must report product-path RSS and disk
again.

## Verification and retained evidence

- analyzer/identity tests: 16/16 passed in 29.13 seconds after C;
- canonical helper tests: 3/3 passed in 1.56 seconds after resource reporting;
- fail-closed parent-resource tests: 13/13 passed in 4.24 seconds, including
  descendant denial, wrong external parent hash, receipt overflow, observed
  sampling overrun, bounded-output overflow, isolated dependency closure and
  orphan cleanup;
- identity helper SHA-256:
  `f8d5a18a725f5331ebd752a0a8a1031c2aecb270afcb5d2889e36cf592c7270d`;
- parent resource gate SHA-256:
  `3128e5f75dc5bf1955aec9515ba35c1cd8672aced3c86137cd1a84ce9436d198`;
- parent resource test SHA-256:
  `f2dda5d4cc7682fa6c17e86f18efc2451c343c920d954b0504363bc9887fb4d8`;
- analyzer-test SHA-256:
  `a7dfe83dda65f50aa0ff4edb8a24185d1687c09f67a4ca41bed0f9d59eecb9f2`;
- identity-test SHA-256:
  `23ed2199beba33d92f8d1fb8c3d713f2fb3dc537449f8894d703337ccf32e59f`;
- authoritative full-claves parent receipt SHA-256:
  `d0a3193b4d3845e6dd15e9bec379902e8dc56a6c64da63a77ef373b0f867ee6b`;
- authoritative full-cymbal parent receipt SHA-256:
  `923f22901a173cfc01a98e7e3ad856b53794fb83adc56786c09c0a48bc5a1527`.

Retained roots:

- `G:/Resonith/artifacts/r218-s11-output-identical-baseline`;
- `G:/Resonith/artifacts/r218-s11-output-identical-checkpoint-a`;
- `G:/Resonith/artifacts/r218-s11-output-identical-checkpoint-b`;
- `G:/Resonith/artifacts/r218-s11-output-identical-checkpoint-c`;
- `G:/Resonith/artifacts/r218-s11-output-identical-checkpoint-c-repeat`;
- `G:/Resonith/artifacts/r218-s11-resource-final-c-claves` (empty retained
  fail-closed launch incident);
- `G:/Resonith/artifacts/r218-s11-resource-final-c-claves-retry1`;
- `G:/Resonith/artifacts/r218-s11-resource-final-c-cymbal`.

## Claim boundary and next action

R-218 demonstrates output-identical mechanical acceleration only. It does not
show a bitrate or quality gain and does not compare against Opus. Independent
closeout recomputed both authoritative receipts and every gate above, then
issued GO only for narrow immutable-commit preparation. S12 remains in
progress. After that commit, a separately audited new direct-comparison run
identity must explicitly hash the analyzer and compare only current Resonith
with the one fixed official Opus 1.6.1 maximum-complexity anchor. S13 remains
blocked until that complete direct report passes.
