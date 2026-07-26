"use strict";

const state = {
  manifest: null,
  manifestSha256: "",
  audioContext: null,
  trialIndex: 0,
  buffers: new Map(),
  sources: [],
  gains: new Map(),
  playing: false,
  offsetSeconds: 0,
  playStartedAt: 0,
  activeCondition: "reference",
  activeStartedAt: 0,
  auditionSeconds: {},
  switchCount: 0,
  completedTrials: [],
  sessionStartedUtc: null,
  animationFrame: null,
};

const byId = (id) => document.getElementById(id);

function hex(bytes) {
  return Array.from(new Uint8Array(bytes))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

function formatTime(seconds) {
  const safe = Math.max(0, Number.isFinite(seconds) ? seconds : 0);
  const minutes = Math.floor(safe / 60);
  return `${minutes}:${(safe % 60).toFixed(1).padStart(4, "0")}`;
}

function trial() {
  return state.manifest.trials[state.trialIndex];
}

function durationSeconds() {
  const values = Array.from(state.buffers.values(), (buffer) => buffer.duration);
  return values.length === 0 ? 0 : Math.min(...values);
}

function currentOffset() {
  const duration = durationSeconds();
  if (!state.playing || duration === 0) {
    return state.offsetSeconds;
  }
  return (
    state.offsetSeconds + state.audioContext.currentTime - state.playStartedAt
  ) % duration;
}

function accountAudition() {
  if (!state.playing) {
    return;
  }
  const now = state.audioContext.currentTime;
  state.auditionSeconds[state.activeCondition] +=
    Math.max(0, now - state.activeStartedAt);
  state.activeStartedAt = now;
}

function setActiveCondition(condition) {
  if (!state.buffers.has(condition)) {
    return;
  }
  if (condition !== state.activeCondition) {
    accountAudition();
    state.activeCondition = condition;
    state.switchCount += 1;
  }
  const now = state.audioContext?.currentTime ?? 0;
  for (const [name, gain] of state.gains.entries()) {
    gain.gain.setValueAtTime(name === condition ? 1 : 0, now);
  }
  byId("reference").classList.toggle("active", condition === "reference");
  document.querySelectorAll(".condition").forEach((button) => {
    button.classList.toggle("active", button.dataset.label === condition);
  });
}

function stopSources() {
  for (const source of state.sources) {
    try {
      source.stop();
    } catch {
      // A source may already have stopped during a trial transition.
    }
  }
  state.sources = [];
  state.gains.clear();
}

function startPlayback() {
  const duration = durationSeconds();
  if (state.playing || duration === 0) {
    return;
  }
  stopSources();
  const when = state.audioContext.currentTime + 0.03;
  const offset = state.offsetSeconds % duration;
  for (const [condition, buffer] of state.buffers.entries()) {
    const source = state.audioContext.createBufferSource();
    const gain = state.audioContext.createGain();
    source.buffer = buffer;
    source.loop = true;
    gain.gain.value = condition === state.activeCondition ? 1 : 0;
    source.connect(gain).connect(state.audioContext.destination);
    source.start(when, offset);
    state.sources.push(source);
    state.gains.set(condition, gain);
  }
  state.playStartedAt = when;
  state.activeStartedAt = when;
  state.playing = true;
  byId("play-pause").textContent = "Pause";
  updateTimeline();
}

function pausePlayback() {
  if (!state.playing) {
    return;
  }
  accountAudition();
  state.offsetSeconds = currentOffset();
  state.playing = false;
  stopSources();
  byId("play-pause").textContent = "Play";
}

function updateTimeline() {
  const duration = durationSeconds();
  const offset = currentOffset();
  byId("elapsed").textContent = formatTime(offset);
  byId("duration").textContent = formatTime(duration);
  byId("playhead").style.width =
    `${duration === 0 ? 0 : (100 * offset) / duration}%`;
  for (const card of document.querySelectorAll(".candidate")) {
    const label = card.dataset.label;
    const listened = state.auditionSeconds[label] ?? 0;
    card.querySelector(".audition").textContent =
      listened >= 0.5 ? `Auditioned ${formatTime(listened)}` : "Not auditioned";
  }
  if (state.playing) {
    state.animationFrame = requestAnimationFrame(updateTimeline);
  }
}

async function decodeAudio(path, expectedSha256) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Cannot load ${path}: HTTP ${response.status}`);
  }
  const payload = await response.arrayBuffer();
  const actualSha256 = hex(await crypto.subtle.digest("SHA-256", payload));
  if (actualSha256 !== expectedSha256) {
    throw new Error(`Audio hash mismatch: ${path}`);
  }
  return state.audioContext.decodeAudioData(payload);
}

function renderCandidates() {
  const container = byId("candidates");
  const template = byId("candidate-template");
  container.replaceChildren();
  for (const candidate of trial().candidates) {
    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector(".candidate");
    const button = fragment.querySelector(".condition");
    const score = fragment.querySelector(".score");
    const output = fragment.querySelector("output");
    card.dataset.label = candidate.label;
    button.dataset.label = candidate.label;
    button.textContent = `Condition ${candidate.label}`;
    button.addEventListener("click", () => {
      setActiveCondition(candidate.label);
      if (!state.playing) {
        startPlayback();
      }
    });
    score.dataset.scored = "false";
    score.addEventListener("input", () => {
      score.dataset.scored = "true";
      output.value = score.value;
      byId("trial-warning").textContent = "";
    });
    container.appendChild(fragment);
  }
}

async function loadTrial() {
  pausePlayback();
  cancelAnimationFrame(state.animationFrame);
  state.offsetSeconds = 0;
  state.activeCondition = "reference";
  state.auditionSeconds = { reference: 0 };
  state.switchCount = 0;
  state.buffers.clear();
  const current = trial();
  for (const candidate of current.candidates) {
    state.auditionSeconds[candidate.label] = 0;
  }
  byId("clip-id").textContent = current.clip_id;
  byId("trial-position").textContent =
    `Trial ${state.trialIndex + 1} of ${state.manifest.trials.length}`;
  byId("trial-warning").textContent = "Loading synchronized candidates…";
  renderCandidates();
  const entries = [
    ["reference", current.reference.path, current.reference.sha256],
    ...current.candidates.map((candidate) => [
      candidate.label,
      candidate.path,
      candidate.sha256,
    ]),
  ];
  const decoded = await Promise.all(
    entries.map(async ([condition, path, sha256]) => [
      condition,
      await decodeAudio(path, sha256),
    ])
  );
  for (const [condition, buffer] of decoded) {
    state.buffers.set(condition, buffer);
  }
  byId("duration").textContent = formatTime(durationSeconds());
  byId("trial-warning").textContent =
    "Audition the reference and every condition, then score every condition.";
  setActiveCondition("reference");
}

function captureTrial() {
  accountAudition();
  const scores = {};
  const artifacts = {};
  const notes = {};
  const missing = [];
  const unauditioned = [];
  for (const card of document.querySelectorAll(".candidate")) {
    const label = card.dataset.label;
    const score = card.querySelector(".score");
    if (score.dataset.scored !== "true") {
      missing.push(label);
    } else {
      scores[label] = Number(score.value);
    }
    artifacts[label] = Array.from(
      card.querySelectorAll('input[type="checkbox"]:checked'),
      (input) => input.value
    );
    notes[label] = card.querySelector(".note").value.trim();
    if ((state.auditionSeconds[label] ?? 0) < 0.5) {
      unauditioned.push(label);
    }
  }
  if ((state.auditionSeconds.reference ?? 0) < 0.5) {
    unauditioned.push("reference");
  }
  if (missing.length > 0 || unauditioned.length > 0) {
    const messages = [];
    if (missing.length > 0) {
      messages.push(`Score ${missing.join(", ")}`);
    }
    if (unauditioned.length > 0) {
      messages.push(`Audition ${unauditioned.join(", ")}`);
    }
    byId("trial-warning").textContent = `${messages.join(". ")}.`;
    return null;
  }
  return {
    clip_id: trial().clip_id,
    scores,
    audition_seconds: Object.fromEntries(
      Object.entries(state.auditionSeconds).map(([label, seconds]) => [
        label,
        Number(seconds.toFixed(3)),
      ])
    ),
    switch_count: state.switchCount,
    artifacts,
    notes,
  };
}

function saveDraft() {
  const key = `resonith-listening:${state.manifestSha256}`;
  localStorage.setItem(
    key,
    JSON.stringify({
      completed_trials: state.completedTrials,
      trial_index: state.trialIndex,
    })
  );
  byId("save-state").textContent = "Stored locally";
}

async function completeTrial() {
  const result = captureTrial();
  if (result === null) {
    return;
  }
  pausePlayback();
  state.completedTrials.push(result);
  state.trialIndex += 1;
  saveDraft();
  if (state.trialIndex < state.manifest.trials.length) {
    await loadTrial();
    return;
  }
  byId("test").classList.add("hidden");
  byId("finish").classList.remove("hidden");
  byId("trial-position").textContent = "All trials complete";
}

function exportResult() {
  const listenerId = byId("listener-id").value.trim();
  const result = {
    schema: "resonith-blind-listening-result-1",
    manifest_sha256: state.manifestSha256,
    listener_id: listenerId,
    playback_setup: byId("playback-setup").value,
    session_started_utc: state.sessionStartedUtc,
    session_completed_utc: new Date().toISOString(),
    trials: state.completedTrials,
  };
  const blob = new Blob(
    [`${JSON.stringify(result, null, 2)}\n`],
    { type: "application/json" }
  );
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `resonith-listening-${listenerId || "anonymous"}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function initialize() {
  try {
    const response = await fetch("manifest.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Manifest HTTP ${response.status}`);
    }
    const bytes = await response.arrayBuffer();
    state.manifestSha256 = hex(await crypto.subtle.digest("SHA-256", bytes));
    state.manifest = JSON.parse(new TextDecoder().decode(bytes));
    if (
      state.manifest.schema !== "resonith-blind-listening-2"
      || !Array.isArray(state.manifest.trials)
      || state.manifest.trials.length === 0
    ) {
      throw new Error("Unsupported or empty listening manifest");
    }
    byId("startup-status").textContent =
      `${state.manifest.trials.length} blinded trials ready.`;
    byId("begin").disabled = false;
  } catch (error) {
    byId("startup-status").textContent =
      `${error.message}. Serve this directory over localhost; do not open `
      + "index.html directly from the filesystem.";
  }
}

byId("begin").addEventListener("click", async () => {
  if (
    byId("listener-id").value.trim() === ""
    || byId("playback-setup").value === ""
  ) {
    byId("startup-status").textContent =
      "Enter an anonymous listener code and playback setup.";
    return;
  }
  state.audioContext = new AudioContext({ latencyHint: "interactive" });
  await state.audioContext.resume();
  state.sessionStartedUtc = new Date().toISOString();
  byId("startup").classList.add("hidden");
  byId("test").classList.remove("hidden");
  await loadTrial();
});

byId("play-pause").addEventListener("click", () => {
  if (state.playing) {
    pausePlayback();
  } else {
    startPlayback();
  }
});
byId("reference").addEventListener("click", () => {
  setActiveCondition("reference");
  if (!state.playing) {
    startPlayback();
  }
});
byId("complete-trial").addEventListener("click", completeTrial);
byId("export").addEventListener("click", exportResult);
window.addEventListener("beforeunload", pausePlayback);

initialize();
