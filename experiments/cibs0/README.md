# CIBS-0 experiment

Status: reference arithmetic prototype; demo model is not trained and not normative.

Current Artifacts:

- `../../reference/cibs0/cibs0.py` — integer materialization kernel;
- `../../tests/test_cibs0.py` - repeatability, hash, adapter, correction and
  type-safety tests.

The first benchmark must compare:

```text
LIFTING_ONLY
RAW_BASIS + waveform residual
CIBS_LATENT + basis correction + waveform residual
```

The next step is the training/export pipeline, which trains analysis/synthesis
model on extracted periodic bases, quantizes weights/latents and checks
export with the same reference integer kernel.

Demo weights serve only to fix arithmetic. Compression claim on them
prohibited.