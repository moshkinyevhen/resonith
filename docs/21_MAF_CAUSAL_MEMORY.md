# MAF Causal Simplicity Memory

Status: **ACCEPTED engineering invariant**  
Decisions: R-168, R-169, R-171 through R-173

## The permanent reminder

Sound is pressure produced by a small number of causes. Resonith must search
those causes before treating audio as unrelated coefficients:

```text
Pressure_c(t) =
  sum_s Route_c,s(Resonator_s(Excitation_s, State_s))
  + Truth_c(t)
```

- `Excitation`: coherent/quasiperiodic, impulsive, or stochastic.
- `Resonator/State`: harmonic and bounded-inharmonic partials, formants, body,
  decay, modulation, and room response.
- `Route`: phase, delay, gain, channel covariance, and propagation.
- `Truth`: only the remaining objective innovation.

Parameters live until a real event changes them. A law, Basis, state, or motif
is paid once and then referenced.

Do not classify an acoustic source as speech, instrument, rain, or any other
semantic category for coding. Such words may identify test files only. Coding
uses unnamed numeric causes and whichever bounded law wins complete RDO.

## Keep causes separate

The representation union has separately owned additive lanes:

1. coherent harmonic bundles;
2. deterministic bounded-inharmonic bundles;
3. sparse transients;
4. stochastic fields;
5. phase/room/channel routes;
6. direct innovation.

The lanes may overlap physically in time and frequency. They must not duplicate
rate ownership or carry separate full residuals. Render and sum them first;
then encode one final mixture-domain Truth.

## Find sequences in causal coordinates

Do not rely only on repeated waveform blocks. Search every declared event
origin and repeated-length interval in canonical:

- gap and onset changes;
- pitch/frequency changes;
- phase changes;
- gain/envelope changes;
- partial/formant/resonator changes;
- route/channel changes.

Normalize absolute pitch, gain, phase, onset, and route where the bounded
transform law permits it. Literal, offset, first-difference, and bounded
second-difference streams all compete. Micro patterns may compose longer
motifs, while direct long patterns remain independent candidates.

Never require every coordinate to repeat before admitting a sequence.
Independently index timing, pitch, phase, gain, envelope, resonator, and route
laws inside each causal lane. A bounded grammar may synchronize the winning
laws later. Unrelated phase, noise realization, or route drift must not erase
an otherwise reusable pattern.

Pay one timeline per causal lane. Numeric law columns reference that timeline;
they do not retransmit it. Omit identity mono routes and constant/default
columns instead of inventing events for them.

## Simplicity filter

Before adding a mechanism, ask:

1. Which repeated payment does it remove?
2. Can the existing bounded ISA express the cause?
3. Is its dictionary + state + events + routes + checkpoints + final Truth
   smaller, or is its matched-rate quality better?
4. Does it keep CPU-only bounded decode and exact fallback?

If these answers are not demonstrated, do not add an opcode. Keep the idea as
an encoder proposer or reject it.

## Evidence order

1. long input first and freeze its frontier;
2. short input second and tune a separate plan;
3. refine the missing rate or quality axis before generation freeze;
4. compare real audio with the previous Resonith and maximum-effort official
   Opus;
5. retain every successful duration-specific Pareto point.
