"""Run the reproducible external Opus anchor on a mono PCM16 WAV."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.opus_anchor import run_opus_anchor  # noqa: E402
from maf_p0.wav_io import read_pcm16_mono, write_pcm16_mono  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--bitrate", type=float, action="append", required=True)
    parser.add_argument("--tools", default=os.environ.get("RESONITH_OPUS_TOOLS"))
    parser.add_argument("--mode", choices=("vbr", "cvbr", "hard-cbr"), default="vbr")
    parser.add_argument("--application", choices=("music", "speech", "auto"), default="music")
    parser.add_argument("--decoded-prefix")
    args = parser.parse_args()

    sample_rate, samples = read_pcm16_mono(args.input)
    reports = []
    for bitrate in args.bitrate:
        result = run_opus_anchor(
            samples,
            sample_rate,
            bitrate_kbps=bitrate,
            mode=args.mode,
            application=args.application,
            tools_directory=args.tools,
        )
        reports.append(result.report)
        if args.decoded_prefix:
            output = Path(f"{args.decoded_prefix}.{bitrate:g}k.wav")
            write_pcm16_mono(output, sample_rate, result.reconstructed)
    print(json.dumps(reports, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
