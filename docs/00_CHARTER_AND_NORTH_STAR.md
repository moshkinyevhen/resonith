# Charter and North Star Resonith

Status: basic principles - **ACCEPTED**; numerical targets - **TARGET**.

## 1. Mission

Resonith should standardize more than just another sequence
psychoacoustically quantized waveform frames, and limited compiler
contract for a continuous acoustic field.

Encoder looks for compact signal causes:

- stable periodic/quasi-periodic components;
- changing timbre;
- excitation and resonant response;
- stochastic texture;
- transients;
- emitters, spatial trajectories and room response;
- objective innovation, not explained by the model.

Decoder is not required to understand the words "violin", "note" or "symphony". He must
bit-exact execute physical integer parameters.

## 2. Canonical formula

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+ TruthInnovation_t
+ OptionalPerceptualDetail_t.
\]

For source \(e\):

\[
s_e(t)=C_e(t)+N_e(t)+T_e(t)+E_e(t),
\]

where:

- \(C_e\) — coherent low-rank periodic field;
- \(N_e\) — deterministic stochastic field;
- \(T_e\) — sparse transient field;
- \(E_e\) — objective exact/quantized innovation.

## 3. Main principle

Resonith does not transmit “piece type: speech/music/noise”, but at the same time selects
best representation for each source/time-frequency atom.

In one interval the following can coexist:

- voice predictive/coherent atom;
- drum attack as transient;
- plate as stochastic field;
- reverb as room/resonant field;
- Truth Innovation for the remaining error.

Router offers candidates. The final choice is made by the full RDO:

\[
J=\sum_i R_i+\lambda D(x,\hat x)+\mu C_{\mathrm{decode}}.
\]

## 4. What does it mean to “understand music”

Encoder MAY:

- transcribe score;
- highlight stems and emitters;
- recognize instruments and performers;
- track pitch, onset, articulation, tempo and motifs;
- evaluate room impulse response;
- build per-instrument timbre manifold;
- use foundation models and offline global optimization.

But semantic label MUST NOT replace objective evidence. The note `A4` is not
defines timbre, phase, microdynamics, bow noise, room or interpretation.
Any semantic reconstruction is checked by exact decoder-in-the-loop RDO, and
the error is coded by Truth Innovation.

## 5. Separateness of products

- Resonith is a standalone audio codec.
- SceneLith is a standalone video codec.
- SceneLith AV Bridge is a separate binding that MAY combine timeline,
  entity mapping, trajectories and room/geometry hints.

No standalone bitstream requires a different modality.

## 6. North Star

**TARGET:**

- materially beat Opus, xHE-AAC/USAC and EVS separately in applicable modes;
- perceptually transparent classical stereo with a significantly lower bitrate;
- exact PCM lossless path;- live latency no higher than 20 ms for Realtime profile;
- Main decoder with bounded update-time CIBS, but without per-sample neural inference;
- one bounded atom grammar instead of a set of independent subcodecs;
- software decode on a regular mobile CPU/DSP.