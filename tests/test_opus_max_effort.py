from __future__ import annotations

import numpy as np

from reference.maf_p0.opus_anchor import OpusAnchorResult, OpusTools
from reference.maf_p0.opus_max_effort import (
    OpusEffortConfig,
    opus_max_effort_configurations,
    run_opus_max_effort_frontier,
)


def test_configuration_lattice_covers_stereo_controls() -> None:
    configs = opus_max_effort_configurations(2)

    assert len(configs) == 108
    assert {config.mode for config in configs} == {
        "vbr",
        "cvbr",
        "hard-cbr",
    }
    assert {config.frame_size_ms for config in configs} == {
        2.5,
        5.0,
        10.0,
        20.0,
        40.0,
        60.0,
    }
    assert {config.phase_inversion for config in configs} == {True, False}


def test_frontier_selects_best_decoded_quality_at_matched_bytes() -> None:
    samples = np.zeros((48000, 2), dtype=np.int16)
    tools = OpusTools(
        opusenc=None,  # type: ignore[arg-type]
        opusdec=None,  # type: ignore[arg-type]
        encoder_version="libopus 1.6.1",
        decoder_version="libopus 1.6.1",
        encoder_sha256="0" * 64,
        decoder_sha256="1" * 64,
    )

    def fake_anchor(_samples, _rate, **kwargs):
        frame_size = float(kwargs["frame_size_ms"])
        bitrate = float(kwargs["bitrate_kbps"])
        stream_bytes = max(1, int(round(bitrate * 125.0)))
        quality = 30.0 if frame_size == 20.0 else 20.0
        return OpusAnchorResult(
            payload=b"x" * stream_bytes,
            reconstructed=np.zeros_like(samples),
            report={"snr_db": quality},
        )

    frontier = run_opus_max_effort_frontier(
        samples,
        48000,
        target_complete_bytes=12000,
        matched_byte_tolerance=64,
        refinement_rounds=2,
        configurations=(
            OpusEffortConfig("vbr", "auto", 10.0, True),
            OpusEffortConfig("vbr", "auto", 20.0, True),
        ),
        tools=tools,
        anchor_runner=fake_anchor,
    )

    assert frontier.selected.config.frame_size_ms == 20.0
    assert frontier.report["complexity"] == 10
    assert frontier.report["configuration_count"] == 2
