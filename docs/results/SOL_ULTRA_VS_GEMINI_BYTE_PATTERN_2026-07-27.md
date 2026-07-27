# Blind Sol Ultra vs Gemini Byte-Pattern Gate

Date: **2026-07-27**  
Status: **MEASURED PROPOSER EVIDENCE; NOT A CODEC CLAIM**

## Question

Can a maximum-effort general reasoning model find reusable mathematical
relations directly in PCM16LE hexadecimal sequences more completely than
Gemini 3.6 Flash, without receiving audio, labels, or the CUDA answer?

The tested Sol execution surface was an isolated Codex sub-agent configured
as `gpt-5.6-sol` with product reasoning effort `Ultra`. This is intentionally
reported separately from the OpenAI Responses API `max`/`pro` gate, which
remains blocked by project model access.

## Blindness and authority

Sol received only:

- the frozen provider-neutral R-152 prompt;
- numbered PCM16LE hexadecimal blocks;
- circular offset plus constant/linear signed Q1.15 gain laws;
- the exact normalized-error threshold.

It was explicitly denied the Gemini output, native/CUDA result, WAV source,
and codec reports. After it finished, the unchanged local fixed-point Foundry
verified every candidate. The later production `reverse` transform was
excluded from this comparison because it is absent from the frozen prompt.

Input SHA-256:
`1a60929b0dafed47bf2431d63073511cfcfb95fdb94ef13be2e53f085e494578`.

Sol proposal SHA-256:
`7b6b18142aa5ad8af1d4f96c7be19fccbe4f1cf186ab2a9da60124dd9f5826d1`.

## Results

### Synthetic exact laws

| Metric | Sol Ultra | Gemini 3.6 Flash | Exact CUDA |
|---|---:|---:|---:|
| Proposals | 42 | 12 | all declared candidates |
| Eligible relations found | 24 | 8 | 24 |
| Relation recall | **100.00%** | 33.33% | 100.00% |
| Best-target recall | **100.00%** | **100.00%** | 100.00% |
| Relation precision | 57.14% | **66.67%** | 100.00% |
| Exact Q1.15 parameter rate | 0.00% | 0.00% | 100.00% |

### Real EBU speech bytes

| Metric | Sol Ultra | Gemini 3.6 Flash | Exact CUDA |
|---|---:|---:|---:|
| Proposals | 292 | 12 | all declared candidates |
| Eligible relations found | **172** | 3 | 172 |
| Relation recall | **100.00%** | 1.744% | 100.00% |
| Best-target recall | **100.00%** | 0.00% | 100.00% |
| Relation precision | **58.90%** | 25.00% | 100.00% |
| Exact Q1.15 parameter rate | **10.465%** | 0.00% | 100.00% |

Native CUDA authority time was approximately `0.21` seconds for the speech
case. Gemini required `129.342` seconds. The Codex sub-agent wall time was not
instrumented by the gate and is therefore not assigned a fabricated numeric
value; observed execution was several minutes.

## Interpretation

Sol Ultra is dramatically better than Gemini 3.6 Flash at high-recall
relationship proposal on this bounded byte task. It found every CUDA-eligible
relation in both cases, including all real-speech targets.

It is not an exact numeric replacement for Foundry:

- 42 synthetic proposals contained only 24 eligible relations;
- 292 speech proposals contained 172 eligible relations;
- only 18 of the 172 eligible speech relations carried the exact native Q1.15
  parameter tuple;
- neither model produced exact parameters on the synthetic case.

The accepted architecture is therefore:

1. Sol Ultra may be used selectively as an expensive high-recall proposer or
   audit tool;
2. the native fitter calculates exact bounded transform parameters;
3. CUDA still evaluates the complete declared lattice and is the only
   eligibility authority;
4. global decoder-in-loop RDO decides whether any verified relationship saves
   complete bytes at the required quality.

Using Sol on every raw byte window would add cost and latency without removing
the GPU search. Its strongest future role is proposing larger transform
families, merge laws, and candidate regions that the deterministic engine then
proves exactly.

## Machine evidence

- `experiments/results/sol_ultra_byte_pattern_r154_2026-07-27.json`
- `experiments/results/sol_ultra_blind_output_r153_2026-07-27.json`
- `experiments/results/gemini_byte_pattern_r152_2026-07-27.json`
- `experiments/score_blind_sol_byte_pattern.py`
