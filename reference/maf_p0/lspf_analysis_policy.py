"""R-162 deterministic short/long LSPF encoder policy.

The policy changes Foundry search resources, never decoder syntax, exact
fallback, quality floors, or corruption bounds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LspfPolicyRequest:
    """Signal and resource facts that may influence encoder search."""

    duration_frames: int
    sample_rate: int
    channels: int
    latency_target_ms: int
    encoder_time_budget_x: float
    encoder_memory_bytes: int
    gpu_memory_bytes: int
    lossless: bool

    def __post_init__(self) -> None:
        if (
            self.duration_frames <= 0
            or not 8000 <= self.sample_rate <= 384000
            or not 1 <= self.channels <= 8
            or not 1 <= self.latency_target_ms <= 60000
            or not 0.1 <= self.encoder_time_budget_x <= 100000.0
            or self.encoder_memory_bytes < 64 << 20
            or self.gpu_memory_bytes < 0
        ):
            raise ValueError("invalid R-162 policy request")


@dataclass(frozen=True)
class LspfAnalysisPlan:
    """Published deterministic analysis plan for one input."""

    schema: str
    duration_class: str
    encoder_level: str
    syntax_family: str
    decoder_profile: str
    scales_samples: tuple[int, ...]
    factor_counts: tuple[int, ...]
    convolution_depths: tuple[int, ...]
    checkpoint_frames: int
    maximum_dictionary_lifetime_frames: int
    candidate_tile_bytes: int
    maximum_parallel_fields: int
    exact_truth_fallback: bool
    quality_floors_required: bool
    duration_pareto_preservation: bool
    incumbent_candidate_required: bool
    skipped_families: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_manifest(self) -> dict:
        """Return one JSON-serializable evidence record."""

        return asdict(self)


def choose_lspf_analysis_plan(request: LspfPolicyRequest) -> LspfAnalysisPlan:
    """Choose one finite search plan without changing the decoder contract."""

    duration_seconds = request.duration_frames / request.sample_rate
    reasons = []
    skipped = []

    if request.latency_target_ms <= 40:
        encoder_level = "Live"
        scales = (64, 128, 256, 512, 1024)
        factors = (2, 3)
        depths = (2, 4)
        checkpoint_seconds = 1
        reasons.append("latency target selects bounded Live search")
    elif request.encoder_time_budget_x >= 10.0:
        encoder_level = "Foundry"
        scales = (64, 128, 256, 512, 2048, 8192, 32768)
        factors = (2, 4, 6, 8)
        depths = (2, 4, 8, 16)
        checkpoint_seconds = 8
        reasons.append("offline time budget admits Foundry search")
    else:
        encoder_level = "Studio"
        scales = (64, 128, 256, 512, 2048, 8192)
        factors = (2, 4, 6)
        depths = (2, 4, 8)
        checkpoint_seconds = 4
        reasons.append("resource budget selects Studio search")

    if duration_seconds < 30.0:
        duration_class = "short"
        scales = tuple(scale for scale in scales if scale <= 8192)
        depths = tuple(depth for depth in depths if depth <= 8)
        lifetime = request.duration_frames
        checkpoint_seconds = min(checkpoint_seconds, 2)
        reasons.append("short input emphasizes local boundaries and transforms")
    elif duration_seconds < 120.0:
        duration_class = "medium"
        lifetime = request.duration_frames
        reasons.append("medium input retains local and track-level candidates")
    else:
        duration_class = "long"
        lifetime = request.duration_frames
        if encoder_level != "Live":
            scales = tuple(sorted(set((*scales, 65536, 131072))))
            depths = tuple(sorted(set((*depths, 16))))
        reasons.append(
            "long input enables amortization, drift, motif, and checkpoint gates"
        )

    available_accelerator_bytes = min(
        request.encoder_memory_bytes,
        request.gpu_memory_bytes or request.encoder_memory_bytes,
    )
    if available_accelerator_bytes < 2 << 30:
        factors = tuple(factor for factor in factors if factor <= 4)
        depths = tuple(depth for depth in depths if depth <= 8)
        skipped.append("large-factor-convolution-lattice")
        reasons.append("memory bound removes only the declared large lattice")
    elif available_accelerator_bytes < 6 << 30:
        factors = tuple(factor for factor in factors if factor <= 6)
        skipped.append("eight-factor-lattice")
        reasons.append("memory bound limits simultaneous factor count")

    longest_scale = max(scales)
    scales = tuple(
        scale
        for scale in scales
        if scale <= request.duration_frames and scale <= request.sample_rate * 8
    )
    if not scales:
        scales = (min(request.duration_frames, longest_scale),)
    checkpoint_frames = min(
        request.duration_frames,
        checkpoint_seconds * request.sample_rate,
    )
    bytes_per_field = max(scales) * request.channels * 2
    maximum_parallel_fields = max(
        1,
        min(
            max(factors),
            available_accelerator_bytes // max(1, bytes_per_field * 8),
        ),
    )
    candidate_tile_bytes = min(
        256 << 20,
        max(16 << 20, available_accelerator_bytes // 8),
    )
    return LspfAnalysisPlan(
        schema="resonith-r162-lspf-analysis-plan-1",
        duration_class=duration_class,
        encoder_level=encoder_level,
        syntax_family="Resonith/MAF",
        decoder_profile="Main-0 bounded integer",
        scales_samples=scales,
        factor_counts=factors,
        convolution_depths=depths,
        checkpoint_frames=checkpoint_frames,
        maximum_dictionary_lifetime_frames=lifetime,
        candidate_tile_bytes=candidate_tile_bytes,
        maximum_parallel_fields=maximum_parallel_fields,
        exact_truth_fallback=True,
        quality_floors_required=True,
        duration_pareto_preservation=True,
        incumbent_candidate_required=True,
        skipped_families=tuple(skipped),
        reasons=tuple(reasons),
    )
