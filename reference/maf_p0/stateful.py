"""MAF-P1 stateful prototype: Basis lifetimes, phase laws and transients."""

from __future__ import annotations

import hashlib
import zlib
from typing import Sequence

import numpy as np

from cibs0 import CIBS0Model, materialize_basis

from .codec import (
    DecodeResult,
    EncodeResult,
    _compact_signed,
    _dequantize_signed,
    _quality_report,
    _quantize_signed,
)
from .container import pack_container, unpack_container
from .model import encode_basis_latent
from .periodic import (
    PHASE_SCALE,
    PhaseTrajectory,
    analyze_periodic_basis,
    apply_block_gains,
    constant_phase_trajectory,
    estimate_phase_trajectory,
    fit_block_gains,
    render_basis_trajectory,
)
from .transient import (
    TransientPacket,
    decode_transient_events,
    detect_transients,
    encode_transient_events,
)


PROFILE = "MAF-P1"
MAX_BASES = 4096
MAX_ATOMS = 16384
MAX_PITCH_KNOTS = 1_000_000
MAX_SAMPLE_COUNT = (1 << 31) - 1


def _pcm_sha256(samples: np.ndarray) -> str:
    return hashlib.sha256(
        samples.astype("<i2", copy=False).tobytes()
    ).hexdigest()


def _basis_truth_sha256(basis: np.ndarray) -> str:
    return hashlib.sha256(
        basis.astype("<i2", copy=False).tobytes()
    ).hexdigest()


def _segment_intervals(sample_count: int, segment_samples: int) -> list[tuple[int, int]]:
    if sample_count <= 0 or sample_count > MAX_SAMPLE_COUNT:
        raise ValueError("sample_count is outside the P1 bound")
    if segment_samples < 64:
        raise ValueError("segment_samples must be at least 64")
    intervals = [
        (start, min(sample_count, start + segment_samples))
        for start in range(0, sample_count, segment_samples)
    ]
    if len(intervals) > 1 and intervals[-1][1] - intervals[-1][0] < 64:
        previous_start, _ = intervals[-2]
        intervals[-2] = (previous_start, sample_count)
        intervals.pop()
    if len(intervals) > MAX_ATOMS:
        raise ValueError("atom count exceeds the P1 bound")
    return intervals


def _analysis_period_from_trajectory(trajectory: PhaseTrajectory) -> int:
    increment = int(trajectory.increments_q32[0])
    if increment <= 0:
        raise ValueError("zero-frequency periodic trajectory is unsupported")
    return max(2, int(round(PHASE_SCALE / increment)))


def _compressed_vector_bytes(values: np.ndarray) -> int:
    compact = _compact_signed(values)
    return len(zlib.compress(compact.tobytes(order="C"), level=9))


def _choose_transient_packet(
    samples: np.ndarray,
    periodic_prediction: np.ndarray,
    *,
    mode: str,
    residual_step: int,
    quantization_step: int,
    window_size: int,
) -> tuple[np.ndarray, TransientPacket | None, dict]:
    """Run a full residual-aware transient decision without changing Truth."""

    if mode not in {"off", "on", "auto"}:
        raise ValueError("transient_mode must be off, on or auto")
    baseline_residual = _quantize_signed(
        samples.astype(np.int64) - periodic_prediction.astype(np.int64),
        residual_step,
    )
    baseline_proxy = _compressed_vector_bytes(baseline_residual)
    if mode == "off":
        return periodic_prediction, None, {
            "candidate_events": 0,
            "selected_events": 0,
            "baseline_proxy_bytes": baseline_proxy,
            "candidate_proxy_bytes": baseline_proxy,
        }

    events = detect_transients(samples, window_size=window_size)
    if not events:
        return periodic_prediction, None, {
            "candidate_events": 0,
            "selected_events": 0,
            "baseline_proxy_bytes": baseline_proxy,
            "candidate_proxy_bytes": baseline_proxy,
        }
    packet = encode_transient_events(
        samples,
        events,
        quantization_step=quantization_step,
    )
    transient_prediction, coverage = decode_transient_events(packet, samples.size)
    candidate_prediction = periodic_prediction.copy()
    candidate_prediction[coverage] = transient_prediction[coverage]
    candidate_residual = _quantize_signed(
        samples.astype(np.int64) - candidate_prediction.astype(np.int64),
        residual_step,
    )
    candidate_proxy = (
        _compressed_vector_bytes(candidate_residual)
        + len(zlib.compress(packet.event_table.tobytes(order="C"), level=9))
        + len(
            zlib.compress(
                packet.quantized_coefficients.tobytes(order="C"),
                level=9,
            )
        )
    )
    selected = mode == "on" or candidate_proxy < baseline_proxy
    return (
        candidate_prediction if selected else periodic_prediction,
        packet if selected else None,
        {
            "candidate_events": len(events),
            "selected_events": len(events) if selected else 0,
            "baseline_proxy_bytes": baseline_proxy,
            "candidate_proxy_bytes": candidate_proxy,
        },
    )


def encode_stateful_samples(
    samples: np.ndarray,
    sample_rate: int,
    *,
    basis_mode: str = "raw",
    cibs_model: CIBS0Model | None = None,
    basis_length: int = 256,
    segment_samples: int = 24000,
    pitch_knot_samples: int = 4096,
    phase_trajectories: Sequence[PhaseTrajectory] | None = None,
    analysis_periods: Sequence[int] | None = None,
    gain_block_size: int = 1024,
    basis_correction_step: int = 1,
    residual_step: int = 1,
    transient_mode: str = "auto",
    transient_quantization_step: int = 1,
    transient_window_size: int = 256,
) -> EncodeResult:
    """Encode mono PCM16 into the bounded MAF-P1 research profile.

    State contract:
    - immutable Basis entries are content-deduplicated;
    - each Atom has one half-open lifetime fully contained by its Basis lifetime;
    - phase laws use local absolute sample positions and never depend on render
      block size;
    - transient replacement is objective and any remaining error stays in the
      universal residual.
    """

    if samples.dtype != np.int16 or samples.ndim != 1:
        raise TypeError("samples must be mono int16")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if basis_mode not in {"raw", "cibs"}:
        raise ValueError("basis_mode must be raw or cibs")
    if basis_mode == "cibs":
        if cibs_model is None:
            raise ValueError("CIBS mode requires a model")
        if cibs_model.basis_channels != 1:
            raise ValueError("MAF-P1 requires a one-channel CIBS model")
        if cibs_model.output_length != basis_length:
            raise ValueError("CIBS model Basis length mismatch")

    intervals = _segment_intervals(samples.size, segment_samples)
    if phase_trajectories is not None and len(phase_trajectories) != len(intervals):
        raise ValueError("phase trajectory count does not match Atom count")
    if analysis_periods is not None and len(analysis_periods) != len(intervals):
        raise ValueError("analysis period count does not match Atom count")

    arrays: dict[str, np.ndarray] = {}
    basis_records: list[dict] = []
    basis_payloads: list[dict] = []
    basis_by_truth_hash: dict[str, int] = {}
    atom_rows: list[tuple[int, int, int, int, int, int]] = []
    pitch_positions: list[np.ndarray] = []
    pitch_increments: list[np.ndarray] = []
    unity = np.empty(samples.size, dtype=np.int16)
    pitch_offset = 0
    total_cibs_macs = 0
    periodic_fallback_atoms = 0

    for atom_index, (start, end) in enumerate(intervals):
        atom_samples = samples[start:end]
        automatic_fallback = False
        if phase_trajectories is not None:
            trajectory = phase_trajectories[atom_index]
        else:
            try:
                trajectory = estimate_phase_trajectory(
                    atom_samples,
                    sample_rate,
                    knot_interval=pitch_knot_samples,
                )
            except ValueError:
                # Silence and hostile non-periodic segments remain universally
                # encodable: the model contributes zero and Truth carries them.
                trajectory = constant_phase_trajectory(
                    atom_samples.size,
                    1 << 24,
                )
                automatic_fallback = True
        if trajectory.sample_count != atom_samples.size:
            raise ValueError("phase trajectory duration does not match Atom lifetime")
        period = (
            int(analysis_periods[atom_index])
            if analysis_periods is not None
            else _analysis_period_from_trajectory(trajectory)
        )
        if automatic_fallback:
            target = np.zeros((1, basis_length), dtype=np.int16)
        else:
            try:
                target = analyze_periodic_basis(
                    atom_samples,
                    sample_rate,
                    basis_length=basis_length,
                    period_samples=period,
                ).basis.reshape(1, -1)
            except ValueError:
                if phase_trajectories is not None or analysis_periods is not None:
                    raise
                target = np.zeros((1, basis_length), dtype=np.int16)
                automatic_fallback = True
        if automatic_fallback:
            periodic_fallback_atoms += 1

        payload_record: dict
        if basis_mode == "raw":
            materialized = target.astype(np.int16, copy=True)
            payload_record = {"raw": materialized}
            cibs_hash = None
        else:
            assert cibs_model is not None
            latent = encode_basis_latent(target, cibs_model)
            synthesized = materialize_basis(latent, cibs_model)
            difference = target.astype(np.int64) - synthesized.samples.astype(np.int64)
            correction_q = _quantize_signed(difference, basis_correction_step)
            correction = _dequantize_signed(
                correction_q,
                basis_correction_step,
            ).astype(np.int32)
            verified = materialize_basis(
                latent,
                cibs_model,
                correction=correction,
            )
            materialized = verified.samples
            payload_record = {
                "latent": latent,
                "correction_q": _compact_signed(correction_q),
            }
            cibs_hash = verified.sha256
            total_cibs_macs += synthesized.integer_macs

        truth_hash = _basis_truth_sha256(materialized)
        basis_index = basis_by_truth_hash.get(truth_hash)
        if basis_index is None:
            basis_index = len(basis_records)
            if basis_index >= MAX_BASES:
                raise ValueError("Basis count exceeds the P1 bound")
            basis_by_truth_hash[truth_hash] = basis_index
            basis_records.append(
                {
                    "basis_id": f"basis-{basis_index:06d}",
                    "birth_sample": start,
                    "death_sample": end,
                    "truth_sha256": truth_hash,
                    "cibs_sha256": cibs_hash,
                }
            )
            basis_payloads.append(payload_record)
        else:
            record = basis_records[basis_index]
            record["birth_sample"] = min(int(record["birth_sample"]), start)
            record["death_sample"] = max(int(record["death_sample"]), end)

        unity[start:end] = render_basis_trajectory(materialized.reshape(-1), trajectory)
        knot_count = trajectory.positions.size
        atom_rows.append(
            (
                start,
                end,
                basis_index,
                pitch_offset,
                knot_count,
                int(trajectory.phase_origin_q32),
            )
        )
        pitch_positions.append(trajectory.positions)
        pitch_increments.append(trajectory.increments_q32)
        pitch_offset += knot_count

    if pitch_offset > MAX_PITCH_KNOTS:
        raise ValueError("pitch knot count exceeds the P1 bound")

    if basis_mode == "raw":
        arrays["BASI"] = np.stack(
            [record["raw"] for record in basis_payloads]
        ).astype(np.int16)
    else:
        arrays["LATE"] = np.stack(
            [record["latent"] for record in basis_payloads]
        )
        arrays["BCOR"] = np.stack(
            [record["correction_q"] for record in basis_payloads]
        )
    arrays["BLIF"] = np.asarray(
        [
            (record["birth_sample"], record["death_sample"])
            for record in basis_records
        ],
        dtype=np.int64,
    )
    arrays["ATOM"] = np.asarray(atom_rows, dtype=np.int64)
    arrays["PKPO"] = np.concatenate(pitch_positions).astype(np.int64)
    arrays["PKIN"] = np.concatenate(pitch_increments).astype(np.uint32)

    gains = fit_block_gains(samples, unity, gain_block_size)
    periodic_prediction = apply_block_gains(unity, gains, gain_block_size)
    prediction, transient_packet, transient_report = _choose_transient_packet(
        samples,
        periodic_prediction,
        mode=transient_mode,
        residual_step=residual_step,
        quantization_step=transient_quantization_step,
        window_size=transient_window_size,
    )
    if transient_packet is not None:
        arrays["TREV"] = transient_packet.event_table
        arrays["TRCF"] = transient_packet.quantized_coefficients

    residual_q = _quantize_signed(
        samples.astype(np.int64) - prediction.astype(np.int64),
        residual_step,
    )
    reconstructed = np.clip(
        prediction.astype(np.int64)
        + _dequantize_signed(residual_q, residual_step),
        -32768,
        32767,
    ).astype(np.int16)
    arrays["GAIN"] = gains
    arrays["RESI"] = _compact_signed(residual_q)

    metadata = {
        "format_profile": PROFILE,
        "sample_rate": int(sample_rate),
        "sample_count": int(samples.size),
        "basis_mode": basis_mode,
        "basis_length": int(basis_length),
        "basis_correction_step": int(basis_correction_step),
        "gain_block_size": int(gain_block_size),
        "gain_shift": 15,
        "residual_step": int(residual_step),
        "transient_quantization_step": int(transient_quantization_step),
        "transient_event_count": (
            0
            if transient_packet is None
            else int(transient_packet.event_table.shape[0])
        ),
        "model_id": None if cibs_model is None else cibs_model.model_id,
        "bases": basis_records,
        "pcm_sha256": _pcm_sha256(samples),
    }
    payload = pack_container(metadata, arrays)
    packed_metadata, _ = unpack_container(payload)
    quality = _quality_report(samples, reconstructed)
    report = {
        **quality,
        "format_profile": PROFILE,
        "stream_bytes": len(payload),
        "stream_sha256": hashlib.sha256(payload).hexdigest(),
        "pcm_bytes": int(samples.nbytes),
        "ratio_vs_pcm": len(payload) / samples.nbytes,
        "saving_vs_pcm": 1.0 - len(payload) / samples.nbytes,
        "basis_mode": basis_mode,
        "basis_count": len(basis_records),
        "atom_count": len(atom_rows),
        "basis_reuses": len(atom_rows) - len(basis_records),
        "pitch_knot_count": pitch_offset,
        "periodic_fallback_atoms": periodic_fallback_atoms,
        "transient": transient_report,
        "cibs_integer_macs": total_cibs_macs,
        "section_raw_bytes": {
            name: int(array.nbytes) for name, array in arrays.items()
        },
        "section_compressed_bytes": {
            str(section["name"]): int(section["compressed_bytes"])
            for section in packed_metadata["sections"]
        },
        "container_overhead_bytes": len(payload)
        - sum(
            int(section["compressed_bytes"])
            for section in packed_metadata["sections"]
        ),
    }
    return EncodeResult(payload, reconstructed, report)


def _decode_basis_bank(
    metadata: dict,
    arrays: dict[str, np.ndarray],
    cibs_model: CIBS0Model | None,
) -> list[np.ndarray]:
    records = metadata.get("bases")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_BASES:
        raise ValueError("invalid Basis record count")
    lifetimes = arrays.get("BLIF")
    if lifetimes is None or lifetimes.shape != (len(records), 2):
        raise ValueError("Basis lifetime table shape mismatch")
    if not np.issubdtype(lifetimes.dtype, np.integer):
        raise ValueError("Basis lifetimes must be integers")
    mode = str(metadata["basis_mode"])
    bases: list[np.ndarray] = []

    if mode == "raw":
        payloads = arrays.get("BASI")
        expected_shape = (
            len(records),
            1,
            int(metadata["basis_length"]),
        )
        if (
            payloads is None
            or payloads.dtype != np.int16
            or payloads.shape != expected_shape
        ):
            raise ValueError("raw Basis bank shape mismatch")
        bases = [payloads[index].astype(np.int16) for index in range(len(records))]
    elif mode == "cibs":
        if cibs_model is None:
            raise ValueError("CIBS stream requires a model")
        if cibs_model.model_id != metadata.get("model_id"):
            raise ValueError("CIBS model ID mismatch")
        latents = arrays.get("LATE")
        corrections = arrays.get("BCOR")
        if (
            latents is None
            or corrections is None
            or latents.shape[0] != len(records)
            or corrections.shape[0] != len(records)
        ):
            raise ValueError("CIBS Basis bank shape mismatch")
        for index, record in enumerate(records):
            correction = _dequantize_signed(
                corrections[index],
                int(metadata["basis_correction_step"]),
            ).astype(np.int32)
            materialized = materialize_basis(
                latents[index],
                cibs_model,
                correction=correction,
                expected_sha256=str(record["cibs_sha256"]),
            )
            bases.append(materialized.samples)
    else:
        raise ValueError("unknown Basis mode")

    sample_count = int(metadata["sample_count"])
    for index, (record, basis) in enumerate(zip(records, bases, strict=True)):
        birth, death = (int(value) for value in lifetimes[index])
        if birth < 0 or death <= birth or death > sample_count:
            raise ValueError("Basis lifetime is outside the stream")
        if birth != int(record["birth_sample"]) or death != int(record["death_sample"]):
            raise ValueError("Basis lifetime metadata mismatch")
        if _basis_truth_sha256(basis) != str(record["truth_sha256"]):
            raise ValueError("Basis Truth hash mismatch")
    return bases


def decode_stateful_bytes(
    payload: bytes,
    *,
    cibs_model: CIBS0Model | None = None,
) -> DecodeResult:
    """Decode MAF-P1 after validating the complete bounded state graph."""

    metadata, arrays = unpack_container(payload)
    if metadata.get("format_profile") != PROFILE:
        raise ValueError("not a MAF-P1 stream")
    sample_rate = int(metadata["sample_rate"])
    sample_count = int(metadata["sample_count"])
    if sample_rate <= 0 or not 0 < sample_count <= MAX_SAMPLE_COUNT:
        raise ValueError("invalid stream timebase")

    bases = _decode_basis_bank(metadata, arrays, cibs_model)
    lifetimes = arrays["BLIF"]
    atom_table = arrays.get("ATOM")
    pitch_positions = arrays.get("PKPO")
    pitch_increments = arrays.get("PKIN")
    if atom_table is None or atom_table.ndim != 2 or atom_table.shape[1:] != (6,):
        raise ValueError("invalid Atom table")
    if not np.issubdtype(atom_table.dtype, np.integer):
        raise ValueError("Atom table must contain integers")
    if not 1 <= atom_table.shape[0] <= MAX_ATOMS:
        raise ValueError("Atom count exceeds the P1 bound")
    if pitch_positions is None or pitch_increments is None:
        raise ValueError("missing phase trajectory bank")
    if (
        pitch_positions.ndim != 1
        or pitch_increments.ndim != 1
        or pitch_positions.size != pitch_increments.size
        or pitch_positions.size > MAX_PITCH_KNOTS
    ):
        raise ValueError("invalid phase trajectory bank")
    if not np.issubdtype(pitch_positions.dtype, np.signedinteger):
        raise ValueError("phase positions must be signed integers")
    if pitch_increments.dtype != np.uint32:
        raise ValueError("phase increments must use canonical uint32")

    unity = np.empty(sample_count, dtype=np.int16)
    cursor = 0
    expected_pitch_offset = 0
    for row in atom_table:
        start, end, basis_index, knot_offset, knot_count, phase_origin = (
            int(value) for value in row
        )
        if start != cursor or end <= start or end > sample_count:
            raise ValueError("P1 Atom lifetimes must exactly partition the stream")
        if not 0 <= basis_index < len(bases):
            raise ValueError("Atom references an undefined Basis")
        birth, death = (int(value) for value in lifetimes[basis_index])
        if start < birth or end > death:
            raise ValueError("Atom outlives its Basis")
        if knot_offset != expected_pitch_offset or knot_count < 2:
            raise ValueError("non-canonical phase trajectory offsets")
        knot_end = knot_offset + knot_count
        if knot_end > pitch_positions.size:
            raise ValueError("truncated phase trajectory")
        trajectory = PhaseTrajectory(
            pitch_positions[knot_offset:knot_end],
            pitch_increments[knot_offset:knot_end],
            phase_origin,
        )
        if trajectory.sample_count != end - start:
            raise ValueError("phase trajectory duration mismatch")
        unity[start:end] = render_basis_trajectory(
            bases[basis_index].reshape(-1),
            trajectory,
        )
        cursor = end
        expected_pitch_offset = knot_end
    if cursor != sample_count or expected_pitch_offset != pitch_positions.size:
        raise ValueError("incomplete Atom or phase trajectory coverage")

    prediction = apply_block_gains(
        unity,
        arrays["GAIN"],
        int(metadata["gain_block_size"]),
    )
    transient_count = int(metadata.get("transient_event_count", 0))
    if transient_count:
        if "TREV" not in arrays or "TRCF" not in arrays:
            raise ValueError("missing transient payload")
        if arrays["TREV"].shape[0] != transient_count:
            raise ValueError("transient event count mismatch")
        transient_packet = TransientPacket(
            arrays["TREV"],
            arrays["TRCF"],
            int(metadata["transient_quantization_step"]),
        )
        transient_prediction, coverage = decode_transient_events(
            transient_packet,
            sample_count,
        )
        prediction[coverage] = transient_prediction[coverage]
    elif "TREV" in arrays or "TRCF" in arrays:
        raise ValueError("undeclared transient payload")

    residual = _dequantize_signed(
        arrays["RESI"],
        int(metadata["residual_step"]),
    )
    if residual.shape != (sample_count,):
        raise ValueError("residual length mismatch")
    output = np.clip(
        prediction.astype(np.int64) + residual,
        -32768,
        32767,
    ).astype(np.int16)
    output_hash = _pcm_sha256(output)
    return DecodeResult(
        sample_rate,
        output,
        {
            "format_profile": PROFILE,
            "stream_bytes": len(payload),
            "sample_count": sample_count,
            "basis_mode": str(metadata["basis_mode"]),
            "basis_count": len(bases),
            "atom_count": int(atom_table.shape[0]),
            "transient_event_count": transient_count,
            "pcm_sha256": output_hash,
            "matches_source_hash": output_hash == metadata["pcm_sha256"],
        },
    )
