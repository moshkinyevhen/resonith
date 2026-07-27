"""Run the R-128 Gemini semantic-proposal gate without trusting the provider.

This research control plane creates mono 16 kHz proxies locally, uploads them
through Gemini Files API, requests a strict proposal, deletes every uploaded
object, validates the response, and audits it against independent local DSP.
It is not linked into Resonith Core or any shipped product.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import mimetypes
from pathlib import Path
import sys
import time
from typing import Any, Mapping
import urllib.error
import urllib.request
import wave

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "reference"))

from maf_p0.semantic_arbiter import (  # noqa: E402
    BASIS_FAMILIES,
    PRIMARY_CLASSES,
    REASON_CODES,
    SCHEMA_VERSION,
    SOURCE_CLASSES,
    SPECIALIST_PROVIDERS,
    SPECIALIST_TASKS,
    analyze_proxy_evidence,
    audit_proposals,
    validate_semantic_proposals,
)


API_ROOT = "https://generativelanguage.googleapis.com"
DEFAULT_MODEL = "models/gemini-3.6-flash"
DEFAULT_CREDENTIAL_TARGET = "Resonith/Provider/Gemini/ApiKey"
PROXY_SAMPLE_RATE = 16000
HTTP_TIMEOUT_SECONDS = 180
MAX_RETRIES = 5


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _read_pcm16(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
            raise ValueError(f"{path.name} must be uncompressed PCM16 WAV")
        channels = source.getnchannels()
        sample_rate = source.getframerate()
        frames = source.getnframes()
        payload = source.readframes(frames)
    raw = np.frombuffer(payload, dtype="<i2").reshape(-1, channels)
    return sample_rate, raw


def _create_proxy(source_path: Path, proxy_path: Path) -> dict[str, Any]:
    """Create the least revealing full-duration proxy Gemini can use."""

    sample_rate, channels = _read_pcm16(source_path)
    mono = np.rint(np.mean(channels.astype(np.float64), axis=1))
    duration = mono.size / sample_rate
    output_frames = max(1, round(duration * PROXY_SAMPLE_RATE))
    if sample_rate == PROXY_SAMPLE_RATE:
        proxy = mono
    else:
        source_positions = np.arange(output_frames, dtype=np.float64)
        source_positions *= sample_rate / PROXY_SAMPLE_RATE
        proxy = np.interp(
            source_positions,
            np.arange(mono.size, dtype=np.float64),
            mono,
        )
    proxy_i16 = np.clip(np.rint(proxy), -32768, 32767).astype("<i2")
    proxy_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(proxy_path), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(PROXY_SAMPLE_RATE)
        destination.writeframes(proxy_i16.tobytes())
    return {
        "source_bytes": source_path.stat().st_size,
        "source_sha256": _sha256_file(source_path),
        "source_sample_rate": sample_rate,
        "source_channels": int(channels.shape[1]),
        "duration_seconds": duration,
        "proxy_bytes": proxy_path.stat().st_size,
        "proxy_sha256": _sha256_file(proxy_path),
        "proxy_samples": proxy_i16,
    }


class _FileTime(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", _FileTime),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _read_windows_credential(target: str) -> str:
    """Read one generic secret without exposing it through a child process."""

    if sys.platform != "win32":
        raise RuntimeError("the live credential-store adapter currently requires Windows")
    credential_pointer = ctypes.POINTER(_Credential)()
    advapi32 = ctypes.WinDLL("Advapi32.dll")
    advapi32.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_Credential)),
    ]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [ctypes.c_void_p]
    if not advapi32.CredReadW(target, 1, 0, ctypes.byref(credential_pointer)):
        raise RuntimeError("Gemini credential is unavailable")
    try:
        credential = credential_pointer.contents
        blob = ctypes.string_at(
            credential.CredentialBlob,
            int(credential.CredentialBlobSize),
        )
        try:
            secret = blob.decode("utf-16-le").rstrip("\x00")
        except UnicodeDecodeError:
            secret = blob.decode("utf-8").rstrip("\x00")
        if not secret:
            raise RuntimeError("Gemini credential is empty")
        return secret
    finally:
        advapi32.CredFree(credential_pointer)


def _request(
    request: urllib.request.Request,
    *,
    operation: str,
) -> tuple[bytes, Mapping[str, str]]:
    """Perform a bounded request and report only secret-free error metadata."""

    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(
                request,
                timeout=HTTP_TIMEOUT_SECONDS,
            ) as response:
                return response.read(), dict(response.headers.items())
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code < 600
            if not retryable or attempt + 1 == MAX_RETRIES:
                raise RuntimeError(
                    f"{operation} failed with HTTP {error.code}"
                ) from None
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(60.0, 2.0**attempt)
            time.sleep(max(1.0, delay))
        except urllib.error.URLError:
            if attempt + 1 == MAX_RETRIES:
                raise RuntimeError(f"{operation} network request failed") from None
            time.sleep(min(30.0, 2.0**attempt))
    raise AssertionError("unreachable retry state")


class GeminiFilesClient:
    """Minimal REST client whose API key never leaves request headers."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self.model = model.removeprefix("models/")

    def _headers(self) -> dict[str, str]:
        return {"x-goog-api-key": self._api_key}

    def upload(self, path: Path, display_name: str) -> dict[str, Any]:
        size = path.stat().st_size
        mime_type = mimetypes.guess_type(path.name)[0] or "audio/wav"
        metadata = json.dumps(
            {"file": {"display_name": display_name}},
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            **self._headers(),
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        }
        _, response_headers = _request(
            urllib.request.Request(
                f"{API_ROOT}/upload/v1beta/files",
                data=metadata,
                headers=headers,
                method="POST",
            ),
            operation="Gemini upload start",
        )
        upload_url = next(
            (
                value
                for key, value in response_headers.items()
                if key.lower() == "x-goog-upload-url"
            ),
            None,
        )
        if not upload_url:
            raise RuntimeError("Gemini upload start returned no upload URL")
        body, _ = _request(
            urllib.request.Request(
                upload_url,
                data=path.read_bytes(),
                headers={
                    "Content-Length": str(size),
                    "X-Goog-Upload-Offset": "0",
                    "X-Goog-Upload-Command": "upload, finalize",
                },
                method="POST",
            ),
            operation="Gemini upload finalize",
        )
        result = json.loads(body)
        file_data = result.get("file")
        if not isinstance(file_data, dict):
            raise RuntimeError("Gemini upload returned malformed metadata")
        if not all(isinstance(file_data.get(key), str) for key in ("name", "uri")):
            raise RuntimeError("Gemini upload omitted file identity")
        file_data.setdefault("mimeType", mime_type)
        return file_data

    def delete(self, name: str) -> None:
        _request(
            urllib.request.Request(
                f"{API_ROOT}/v1beta/{name}",
                headers=self._headers(),
                method="DELETE",
            ),
            operation="Gemini file deletion",
        )

    def analyze(
        self,
        uploaded: Mapping[str, Mapping[str, Any]],
        expected_durations: Mapping[str, float],
    ) -> dict[str, Any]:
        inputs: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "Act only as an acoustic-search proposer for Resonith MAF. "
                    "Analyze every labelled audio proxy. Copy each supplied clip_id "
                    "and exact duration_seconds. Return compact physical hypotheses, "
                    "not a transcript, lyrics, names, copyrighted text, codec bytes, "
                    "or final decisions. Regions may overlap only for genuinely "
                    "simultaneous bases. Use truth for unpredictable material. "
                    "Request ElevenLabs only for speech timing, diarization, or voice "
                    "isolation; request Azure only for long/domain speech. Otherwise "
                    "emit no specialist task. Cover each clip's full duration with at "
                    "least one region and use no more than 32 regions."
                ),
            }
        ]
        for clip_id in sorted(uploaded):
            inputs.append(
                {
                    "type": "text",
                    "text": (
                        f"clip_id={clip_id}; "
                        f"duration_seconds={expected_durations[clip_id]:.9f}"
                    ),
                }
            )
            file_data = uploaded[clip_id]
            inputs.append(
                {
                    "type": "audio",
                    "uri": file_data["uri"],
                    "mime_type": file_data.get("mimeType", "audio/wav"),
                }
            )
        request_body = json.dumps(
            {
                "model": self.model,
                "input": inputs,
                "response_format": {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": _response_schema(len(uploaded)),
                },
            },
            separators=(",", ":"),
        ).encode("utf-8")
        body, _ = _request(
            urllib.request.Request(
                f"{API_ROOT}/v1beta/interactions",
                data=request_body,
                headers={**self._headers(), "Content-Type": "application/json"},
                method="POST",
            ),
            operation="Gemini semantic analysis",
        )
        response = json.loads(body)
        outputs = response.get("outputs")
        if not isinstance(outputs, list):
            raise RuntimeError("Gemini interaction returned no outputs")
        text_parts = [
            output.get("text")
            for output in outputs
            if isinstance(output, dict)
            and output.get("type") == "text"
            and isinstance(output.get("text"), str)
        ]
        if len(text_parts) != 1:
            raise RuntimeError("Gemini interaction returned ambiguous text output")
        return {
            "proposal": json.loads(text_parts[0]),
            "usage": _sanitize_usage(response.get("usage")),
            "interaction_id_present": isinstance(response.get("id"), str),
        }


def _sanitize_usage(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        if (
            isinstance(key, str)
            and "token" in key.lower()
            and isinstance(item, int)
            and not isinstance(item, bool)
            and item >= 0
        ):
            result[key] = item
    return result


def _response_schema(clip_count: int) -> dict[str, Any]:
    interval_properties = {
        "start_seconds": {"type": "number", "minimum": 0},
        "end_seconds": {"type": "number", "minimum": 0},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "enum": [SCHEMA_VERSION]},
            "clips": {
                "type": "array",
                "minItems": clip_count,
                "maxItems": clip_count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "clip_id": {"type": "string"},
                        "duration_seconds": {"type": "number", "minimum": 0},
                        "primary_class": {
                            "type": "string",
                            "enum": sorted(PRIMARY_CLASSES),
                        },
                        "sources": {
                            "type": "array",
                            "maxItems": 12,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "source_id": {"type": "string"},
                                    "source_class": {
                                        "type": "string",
                                        "enum": sorted(SOURCE_CLASSES),
                                    },
                                    **interval_properties,
                                },
                                "required": [
                                    "source_id",
                                    "source_class",
                                    "start_seconds",
                                    "end_seconds",
                                    "confidence",
                                ],
                            },
                        },
                        "regions": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 32,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "start_seconds": {"type": "number", "minimum": 0},
                                    "end_seconds": {"type": "number", "minimum": 0},
                                    "primary_basis": {
                                        "type": "string",
                                        "enum": sorted(BASIS_FAMILIES),
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "lifetime_seconds": {
                                        "type": "number",
                                        "minimum": 0,
                                    },
                                    "reason_code": {
                                        "type": "string",
                                        "enum": sorted(REASON_CODES),
                                    },
                                },
                                "required": [
                                    "start_seconds",
                                    "end_seconds",
                                    "primary_basis",
                                    "confidence",
                                    "lifetime_seconds",
                                    "reason_code",
                                ],
                            },
                        },
                        "specialist_tasks": {
                            "type": "array",
                            "maxItems": 8,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "provider": {
                                        "type": "string",
                                        "enum": sorted(SPECIALIST_PROVIDERS),
                                    },
                                    "task": {
                                        "type": "string",
                                        "enum": sorted(SPECIALIST_TASKS),
                                    },
                                    **interval_properties,
                                },
                                "required": [
                                    "provider",
                                    "task",
                                    "start_seconds",
                                    "end_seconds",
                                    "confidence",
                                ],
                            },
                        },
                    },
                    "required": [
                        "clip_id",
                        "duration_seconds",
                        "primary_class",
                        "sources",
                        "regions",
                        "specialist_tasks",
                    ],
                },
            },
        },
        "required": ["schema_version", "clips"],
    }


def _parse_sources(values: list[str] | None) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values or []:
        clip_id, separator, path = value.partition("=")
        if not separator or not clip_id or clip_id in result:
            raise ValueError("--source must be a unique clip-id=path")
        result[clip_id] = Path(path).resolve()
    return result


def _prepared_sources(manifest_path: Path, directory: Path) -> dict[str, Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips = manifest.get("clips")
    if not isinstance(clips, list):
        raise ValueError("prepared manifest has no clips")
    return {
        str(clip["id"]): (directory / str(clip["output_file"])).resolve()
        for clip in clips
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append")
    parser.add_argument("--prepared-manifest", type=Path)
    parser.add_argument("--prepared-directory", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--credential-target", default=DEFAULT_CREDENTIAL_TARGET)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()

    sources = _parse_sources(args.source)
    if args.prepared_manifest is not None:
        if args.prepared_directory is None:
            raise ValueError("--prepared-directory is required with its manifest")
        sources.update(
            _prepared_sources(args.prepared_manifest, args.prepared_directory)
        )
    if not sources:
        raise ValueError("at least one source is required")
    if any(not path.is_file() for path in sources.values()):
        raise FileNotFoundError("one or more source WAV files are missing")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    proxy_directory = args.output_directory / "proxies"
    source_evidence: dict[str, dict[str, Any]] = {}
    local_evidence = {}
    expected_durations: dict[str, float] = {}
    proxy_paths: dict[str, Path] = {}
    started = time.perf_counter()
    for clip_id, source_path in sorted(sources.items()):
        proxy_path = proxy_directory / f"{clip_id}.wav"
        evidence = _create_proxy(source_path, proxy_path)
        proxy_samples = evidence.pop("proxy_samples")
        expected_durations[clip_id] = float(evidence["duration_seconds"])
        local_evidence[clip_id] = analyze_proxy_evidence(
            proxy_samples,
            PROXY_SAMPLE_RATE,
        )
        source_evidence[clip_id] = evidence
        proxy_paths[clip_id] = proxy_path
    proxy_wall_seconds = time.perf_counter() - started

    client = GeminiFilesClient(
        _read_windows_credential(args.credential_target),
        args.model,
    )
    uploaded: dict[str, dict[str, Any]] = {}
    deleted: list[str] = []
    interaction_result: dict[str, Any] | None = None
    live_started = time.perf_counter()
    try:
        for clip_id, proxy_path in sorted(proxy_paths.items()):
            uploaded[clip_id] = client.upload(
                proxy_path,
                f"resonith-r128-{clip_id}",
            )
        interaction_result = client.analyze(uploaded, expected_durations)
    finally:
        for file_data in uploaded.values():
            name = file_data.get("name")
            if isinstance(name, str):
                try:
                    client.delete(name)
                    deleted.append(name)
                except RuntimeError:
                    pass
    live_wall_seconds = time.perf_counter() - live_started
    if interaction_result is None:
        raise RuntimeError("Gemini semantic interaction did not complete")
    if len(deleted) != len(uploaded):
        raise RuntimeError("not every uploaded Gemini file was deleted")

    canonical = validate_semantic_proposals(
        interaction_result["proposal"],
        expected_durations,
    )
    raw_path = args.output_directory / "validated-proposals.json"
    raw_path.write_text(
        json.dumps(canonical, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    audit = audit_proposals(canonical, local_evidence)
    clip_summary = {
        clip["clip_id"]: {
            "primary_class": clip["primary_class"],
            "source_count": clip["source_count"],
            "region_count": clip["region_count"],
            "specialist_task_count": clip["specialist_task_count"],
            "family_evidence": clip["family_evidence"],
        }
        for clip in audit["clips"]
    }
    report = {
        "schema": "resonith-r128-gemini-semantic-arbiter-gate-1",
        "status": "live validated diagnostic; no bitstream or compression change",
        "source_revision": args.source_revision,
        "provider": "Gemini",
        "model": args.model,
        "credential_source": "Windows Credential Manager",
        "credential_recorded": False,
        "uploaded_file_count": len(uploaded),
        "deleted_file_count": len(deleted),
        "all_uploaded_files_deleted": len(deleted) == len(uploaded),
        "interaction_id_present": interaction_result["interaction_id_present"],
        "usage": interaction_result["usage"],
        "proxy_policy": {
            "sample_rate": PROXY_SAMPLE_RATE,
            "channels": 1,
            "full_duration": True,
            "source_audio_recorded": False,
            "transcript_recorded": False,
        },
        "timing": {
            "proxy_and_local_dsp_wall_seconds": proxy_wall_seconds,
            "upload_analysis_delete_wall_seconds": live_wall_seconds,
            "total_wall_seconds": time.perf_counter() - started,
        },
        "sources": source_evidence,
        "proposal_audit": {
            "totals": audit["totals"],
            "clips": clip_summary,
        },
        "admission": {
            "bitstream_changed": False,
            "compression_improvement_claimed": False,
            "quality_improvement_claimed": False,
            "exact_local_rdo_required": True,
            "result": "proposal layer validated; encoder admission pending",
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["proposal_audit"]["totals"], sort_keys=True))
    print(f"report={args.report}")


if __name__ == "__main__":
    main()
