"""Acquire and prepare the pinned R-111 heterogeneous audio corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import soundfile as sf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "experiments" / "extended_audio_corpus.json"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _require_file_identity(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != expected_bytes:
        raise ValueError(f"unexpected byte count for {path}")
    if _sha256_file(path) != expected_sha256:
        raise ValueError(f"SHA-256 mismatch for {path}")


def _download(url: str, destination: Path) -> None:
    """Download one immutable source without accepting a partial final file."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Resonith-R111-Corpus/1"},
    )
    with urllib.request.urlopen(request) as response, partial.open("wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    partial.replace(destination)


def _prepare_ebu_sources(manifest: dict, cache_root: Path) -> Path:
    """Validate the official archive and extract only manifest-selected FLACs."""

    collection = manifest["collections"]["ebu-sqam-tech3253"]
    root = cache_root / "ebu-sqam"
    archive = root / collection["archive_name"]
    if not archive.is_file():
        _download(collection["download_url"], archive)
    _require_file_identity(
        archive,
        expected_bytes=int(collection["archive_bytes"]),
        expected_sha256=collection["archive_sha256"],
    )

    extracted = root / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)
    selected = {
        clip["source_file"]
        for clip in manifest["clips"]
        if clip["collection"] == "ebu-sqam-tech3253"
    }
    with zipfile.ZipFile(archive) as bundle:
        for name in sorted(selected):
            destination = extracted / name
            if destination.is_file():
                continue
            # Manifest names are flat and immutable; reject any path traversal.
            if Path(name).name != name:
                raise ValueError(f"unsafe EBU member name: {name}")
            with bundle.open(name) as source, destination.open("wb") as out:
                while chunk := source.read(1 << 20):
                    out.write(chunk)
    return extracted


def _prepare_xiph_sources(manifest: dict, cache_root: Path) -> Path:
    root = cache_root / "xiph"
    root.mkdir(parents=True, exist_ok=True)
    for clip in manifest["clips"]:
        if clip["collection"] != "xiph-test-media":
            continue
        destination = root / clip["source_file"]
        if not destination.is_file():
            _download(clip["download_url"], destination)
    return root


def _mono_average(samples: np.ndarray) -> np.ndarray:
    """Return deterministic nearest-even PCM16 mono without gain changes."""

    if samples.shape[1] == 1:
        return samples
    averaged = np.rint(samples.astype(np.float64).mean(axis=1))
    return np.clip(averaged, -32768, 32767).astype(np.int16)[:, None]


def _prepare_clip(
    record: dict,
    source_root: Path,
    output_directory: Path,
) -> dict:
    source_path = source_root / record["source_file"]
    _require_file_identity(
        source_path,
        expected_bytes=int(record["source_bytes"]),
        expected_sha256=record["source_sha256"],
    )

    samples, sample_rate = sf.read(
        source_path,
        dtype="int16",
        always_2d=True,
    )
    start = round(float(record["start_seconds"]) * sample_rate)
    length = round(float(record["duration_seconds"]) * sample_rate)
    end = start + length
    if start < 0 or length <= 0 or end > samples.shape[0]:
        raise ValueError(f"invalid crop for {record['id']}")
    crop = np.ascontiguousarray(samples[start:end])
    if record["channel_policy"] == "mono-average":
        crop = _mono_average(crop)
    elif record["channel_policy"] != "preserve":
        raise ValueError(f"unknown channel policy for {record['id']}")

    output_path = output_directory / record["output_file"]
    sf.write(output_path, crop, sample_rate, subtype="PCM_16", format="WAV")
    return {
        "id": record["id"],
        "categories": record["categories"],
        "source_file": record["source_file"],
        "source_sha256": record["source_sha256"],
        "start_seconds": record["start_seconds"],
        "duration_seconds": record["duration_seconds"],
        "channel_policy": record["channel_policy"],
        "output_file": output_path.name,
        "output_bytes": output_path.stat().st_size,
        "output_sha256": _sha256_file(output_path),
        "sample_rate": int(sample_rate),
        "frames": int(crop.shape[0]),
        "channels": int(crop.shape[1]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema") != "resonith-extended-audio-corpus-1":
        raise ValueError("unsupported extended-corpus manifest")
    ebu_root = _prepare_ebu_sources(manifest, args.cache_root)
    xiph_root = _prepare_xiph_sources(manifest, args.cache_root)
    roots = {
        "ebu-sqam-tech3253": ebu_root,
        "xiph-test-media": xiph_root,
    }

    args.output_directory.mkdir(parents=True, exist_ok=True)
    prepared = [
        _prepare_clip(record, roots[record["collection"]], args.output_directory)
        for record in manifest["clips"]
    ]
    report = {
        "schema": "resonith-prepared-extended-audio-corpus-1",
        "source_manifest": args.manifest.name,
        "source_manifest_sha256": _sha256_file(args.manifest),
        "clips": prepared,
    }
    report_path = args.output_directory / "prepared-manifest.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
