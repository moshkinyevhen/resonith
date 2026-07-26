"""Command-line entry point for MAF-P0 experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .codec import decode_bytes, encode_samples
from .container import unpack_container
from .model import (
    load_analysis_model,
    save_analysis_model,
    train_linear_cibs,
)
from .main0 import decode_main0_raw_stream
from .multichannel import (
    decode_main0_independent_stream,
    encode_main0_independent_rdo,
)
from .periodic import analyze_periodic_basis
from .stateful import (
    decode_stateful_bytes,
    encode_stateful_rdo_samples,
    encode_stateful_samples,
)
from .wav_io import (
    read_pcm16_channels,
    read_pcm16_mono,
    write_pcm16_channels,
    write_pcm16_mono,
)


def _json_default(value):
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    raise TypeError(f"not JSON serializable: {value!r}")


def _train(args: argparse.Namespace) -> None:
    bases: list[np.ndarray] = []
    sample_rate_expected: int | None = None
    for path_text in args.inputs:
        sample_rate, samples = read_pcm16_mono(path_text)
        if sample_rate_expected is None:
            sample_rate_expected = sample_rate
        elif sample_rate != sample_rate_expected:
            raise ValueError("all training WAV files must use one sample rate")
        basis = analyze_periodic_basis(
            samples,
            sample_rate,
            basis_length=args.basis_length,
        ).basis
        bases.append(basis.reshape(1, -1))
    model = train_linear_cibs(
        np.stack(bases),
        latent_elements=args.latent,
        model_id=args.model_id,
    )
    save_analysis_model(args.output, model)
    print(
        json.dumps(
            {
                "model": str(args.output),
                "model_id": model.model_id,
                "training_bases": len(bases),
                "latent_elements": model.latent_elements,
                "basis_length": model.output_length,
                "package_bytes": Path(args.output).stat().st_size,
            },
            indent=2,
        )
    )


def _encode(args: argparse.Namespace) -> None:
    sample_rate, samples = read_pcm16_mono(args.input)
    model = load_analysis_model(args.model) if args.model else None
    common = {
        "basis_mode": args.mode,
        "cibs_model": model,
        "basis_length": args.basis_length,
        "gain_block_size": args.gain_block,
        "basis_correction_step": args.basis_q,
        "residual_step": args.residual_q,
    }
    if args.profile == "p1":
        p1_common = {
            "pitch_knot_samples": args.pitch_knot,
            "residual_codec": args.residual_codec,
            "residual_block_size": args.residual_block,
            "transient_mode": args.transient,
            "transient_quantization_step": args.transient_q,
            "transient_window_size": args.transient_window,
            **common,
        }
        if args.segment_mode == "rdo":
            result = encode_stateful_rdo_samples(
                samples,
                sample_rate,
                segmentation_hop_samples=args.segment_hop,
                minimum_segment_samples=args.segment_min,
                maximum_segment_samples=args.segment_max,
                **p1_common,
            )
        else:
            result = encode_stateful_samples(
                samples,
                sample_rate,
                segment_samples=args.segment_samples,
                segment_mode=args.segment_mode,
                segmentation_hop_samples=args.segment_hop,
                minimum_segment_samples=args.segment_min,
                maximum_segment_samples=args.segment_max,
                segmentation_change_penalty=args.change_penalty,
                **p1_common,
            )
    else:
        result = encode_samples(samples, sample_rate, **common)
    Path(args.output).write_bytes(result.payload)
    print(json.dumps(result.report, indent=2, default=_json_default))


def _decode(args: argparse.Namespace) -> None:
    model = load_analysis_model(args.model) if args.model else None
    payload = Path(args.input).read_bytes()
    metadata, _ = unpack_container(payload)
    result = (
        decode_stateful_bytes(payload, cibs_model=model)
        if metadata.get("format_profile") == "MAF-P1"
        else decode_bytes(payload, cibs_model=model)
    )
    write_pcm16_mono(args.output, result.sample_rate, result.samples)
    print(json.dumps(result.report, indent=2))


def _benchmark(args: argparse.Namespace) -> None:
    sample_rate, samples = read_pcm16_mono(args.input)
    model = load_analysis_model(args.model)
    reports = {}
    for mode in ("raw", "cibs"):
        common = {
            "basis_mode": mode,
            "cibs_model": model if mode == "cibs" else None,
            "basis_length": args.basis_length,
            "gain_block_size": args.gain_block,
            "basis_correction_step": args.basis_q,
            "residual_step": args.residual_q,
        }
        if args.profile == "p1":
            p1_common = {
                "pitch_knot_samples": args.pitch_knot,
                "residual_codec": args.residual_codec,
                "residual_block_size": args.residual_block,
                "transient_mode": args.transient,
                "transient_quantization_step": args.transient_q,
                "transient_window_size": args.transient_window,
                **common,
            }
            if args.segment_mode == "rdo":
                result = encode_stateful_rdo_samples(
                    samples,
                    sample_rate,
                    segmentation_hop_samples=args.segment_hop,
                    minimum_segment_samples=args.segment_min,
                    maximum_segment_samples=args.segment_max,
                    **p1_common,
                )
            else:
                result = encode_stateful_samples(
                    samples,
                    sample_rate,
                    segment_samples=args.segment_samples,
                    segment_mode=args.segment_mode,
                    segmentation_hop_samples=args.segment_hop,
                    minimum_segment_samples=args.segment_min,
                    maximum_segment_samples=args.segment_max,
                    segmentation_change_penalty=args.change_penalty,
                    **p1_common,
                )
        else:
            result = encode_samples(samples, sample_rate, **common)
        reports[mode] = result.report
        if args.output_prefix:
            extension = "maf1" if args.profile == "p1" else "maf0"
            Path(f"{args.output_prefix}.{mode}.{extension}").write_bytes(
                result.payload
            )
    reports["model_package_bytes"] = Path(args.model).stat().st_size
    print(json.dumps(reports, indent=2, default=_json_default))


def _encode_main0(args: argparse.Namespace) -> None:
    """Encode a deployable independent-channel RSC1 stream."""

    sample_rate, samples = read_pcm16_channels(args.input)
    result = encode_main0_independent_rdo(
        samples,
        sample_rate,
        innovation_step=args.innovation_step,
        residual_block_sizes=tuple(args.residual_blocks),
    )
    Path(args.output).write_bytes(result.payload)
    print(json.dumps(result.report, indent=2, default=_json_default))


def _decode_main0(args: argparse.Namespace) -> None:
    """Decode residual-only or mono model-bearing Main-0 to PCM16 WAV."""

    payload = Path(args.input).read_bytes()
    try:
        result = decode_main0_independent_stream(payload)
        sample_rate = result.sample_rate
        samples = result.samples
    except ValueError as independent_error:
        model = load_analysis_model(args.model) if args.model else None
        try:
            mono = decode_main0_raw_stream(
                payload,
                cibs_models=() if model is None else (model,),
            )
        except ValueError:
            raise independent_error
        sample_rate = mono.sample_rate
        samples = mono.samples.reshape(-1, 1)
    write_pcm16_channels(args.output, sample_rate, samples)
    print(
        json.dumps(
            {
                "sample_rate": sample_rate,
                "frame_count": int(samples.shape[0]),
                "output_channels": int(samples.shape[1]),
                "output": str(args.output),
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resonith")
    commands = parser.add_subparsers(dest="command", required=True)

    encode_main0 = commands.add_parser(
        "encode-main0",
        help="encode a 1-8 channel PCM16 WAV to aligned Main-0 RSC1",
    )
    encode_main0.add_argument("input")
    encode_main0.add_argument("output")
    encode_main0.add_argument("--innovation-step", type=int, default=1)
    encode_main0.add_argument(
        "--residual-blocks",
        type=int,
        nargs="+",
        default=(4096, 16384, 32768),
    )
    encode_main0.set_defaults(function=_encode_main0)

    decode_main0 = commands.add_parser(
        "decode-main0",
        help="decode Main-0 RSC1 to a PCM16 WAV",
    )
    decode_main0.add_argument("input")
    decode_main0.add_argument("output")
    decode_main0.add_argument("--model")
    decode_main0.set_defaults(function=_decode_main0)

    train = commands.add_parser("train-model")
    train.add_argument("output")
    train.add_argument("inputs", nargs="+")
    train.add_argument("--basis-length", type=int, default=256)
    train.add_argument("--latent", type=int, default=16)
    train.add_argument("--model-id", default="CIBS0-P0-LINEAR")
    train.set_defaults(function=_train)

    encode = commands.add_parser("encode")
    encode.add_argument("input")
    encode.add_argument("output")
    encode.add_argument("--profile", choices=("p0", "p1"), default="p1")
    encode.add_argument("--mode", choices=("raw", "cibs"), default="cibs")
    encode.add_argument("--model")
    encode.add_argument("--basis-length", type=int, default=256)
    encode.add_argument("--gain-block", type=int, default=1024)
    encode.add_argument("--basis-q", type=int, default=1)
    encode.add_argument("--residual-q", type=int, default=1)
    encode.add_argument(
        "--residual-codec",
        choices=("liftpack", "zlib"),
        default="liftpack",
    )
    encode.add_argument("--residual-block", type=int, default=1024)
    encode.add_argument("--segment-samples", type=int, default=24000)
    encode.add_argument(
        "--segment-mode",
        choices=("fixed", "adaptive", "rdo"),
        default="rdo",
    )
    encode.add_argument("--segment-hop", type=int, default=1024)
    encode.add_argument("--segment-min", type=int, default=4096)
    encode.add_argument("--segment-max", type=int, default=96000)
    encode.add_argument("--change-penalty", type=float, default=200.0)
    encode.add_argument("--pitch-knot", type=int, default=4096)
    encode.add_argument("--transient", choices=("off", "on", "auto"), default="auto")
    encode.add_argument("--transient-q", type=int, default=1)
    encode.add_argument("--transient-window", type=int, default=256)
    encode.set_defaults(function=_encode)

    decode = commands.add_parser("decode")
    decode.add_argument("input")
    decode.add_argument("output")
    decode.add_argument("--model")
    decode.set_defaults(function=_decode)

    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("input")
    benchmark.add_argument("model")
    benchmark.add_argument("--profile", choices=("p0", "p1"), default="p1")
    benchmark.add_argument("--output-prefix")
    benchmark.add_argument("--basis-length", type=int, default=256)
    benchmark.add_argument("--gain-block", type=int, default=1024)
    benchmark.add_argument("--basis-q", type=int, default=1)
    benchmark.add_argument("--residual-q", type=int, default=1)
    benchmark.add_argument(
        "--residual-codec",
        choices=("liftpack", "zlib"),
        default="liftpack",
    )
    benchmark.add_argument("--residual-block", type=int, default=1024)
    benchmark.add_argument("--segment-samples", type=int, default=24000)
    benchmark.add_argument(
        "--segment-mode",
        choices=("fixed", "adaptive", "rdo"),
        default="rdo",
    )
    benchmark.add_argument("--segment-hop", type=int, default=1024)
    benchmark.add_argument("--segment-min", type=int, default=4096)
    benchmark.add_argument("--segment-max", type=int, default=96000)
    benchmark.add_argument("--change-penalty", type=float, default=200.0)
    benchmark.add_argument("--pitch-knot", type=int, default=4096)
    benchmark.add_argument("--transient", choices=("off", "on", "auto"), default="auto")
    benchmark.add_argument("--transient-q", type=int, default=1)
    benchmark.add_argument("--transient-window", type=int, default=256)
    benchmark.set_defaults(function=_benchmark)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
