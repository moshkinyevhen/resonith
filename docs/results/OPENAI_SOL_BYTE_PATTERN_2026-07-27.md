# GPT-5.6 Sol Byte-Pattern Gate

Date: **2026-07-27**  
Status: **NO MODEL RESULT — OPENAI PROJECT ACCESS BLOCKED**

## Intended fair comparison

`experiments/openai_byte_pattern_gate.py` uses the same PCM16LE hexadecimal
cases, finite transform language, structured-output fields, eligibility
thresholds, and exact local CUDA verifier as the completed Gemini R-152 gate.
The configured OpenAI request is:

- model: `gpt-5.6-sol`;
- API: Responses;
- reasoning effort: `max`;
- reasoning mode: `pro`;
- stored response: disabled.

The Codex application label `Ultra` is not an API `reasoning.effort` value.
This gate records the actual documented API controls rather than silently
mapping a product label to a different parameter.

## Execution result

The OpenAI API returned:

```text
HTTP 403
code: model_not_found
project does not have access to model gpt-5.6-sol
```

The failure occurred before inference. Consequently:

| Metric | GPT-5.6 Sol | Gemini 3.6 Flash |
|---|---:|---:|
| Eligible-relation precision, synthetic | not measured | 66.67% |
| Eligible-relation recall, synthetic | not measured | 33.33% |
| Best-target recall, synthetic | not measured | 100.00% |
| Exact Q1.15 parameter rate, synthetic | not measured | 0.00% |
| Eligible-relation precision, speech | not measured | 25.00% |
| Eligible-relation recall, speech | not measured | 1.744% |
| Best-target recall, speech | not measured | 0.00% |
| Exact Q1.15 parameter rate, speech | not measured | 0.00% |
| Provider inference tokens | 0 | 35,863 total |

This is not an A/B winner. OpenAI has no measured cell until the API project
is granted access. Substituting a realtime model would invalidate the test.

## Reproduction

The secret is read from Windows Credential Manager and is never printed or
stored in the repository:

```powershell
python experiments/openai_byte_pattern_gate.py `
  --foundry-library build/r149-cuda-clang22/libresonith_foundry_cuda.dll `
  --nvrtc-directory artifacts/tools/cuda-nvrtc-13.3.33-clean/cuda_nvrtc-windows-x86_64-13.3.33-archive/bin/x64
```

When access changes, this exact command reruns the frozen comparison. Sol
remains an optional untrusted proposer; exact fixed-point verification and
complete Foundry membership remain local.

## Official API references

- [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [Latest-model reasoning controls](https://developers.openai.com/api/docs/guides/latest-model)
