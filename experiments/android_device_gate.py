"""Run the native LPS4 callback benchmark on one physical Android device."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


REMOTE_DIRECTORY = "/data/local/tmp/resonith-device-gate"
REMOTE_BENCHMARK = f"{REMOTE_DIRECTORY}/resonith_lapped_device_bench"
REMOTE_STREAM = f"{REMOTE_DIRECTORY}/input.lps"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_adb_devices(output: str) -> list[dict[str, str]]:
    devices = []
    for line in output.splitlines()[1:]:
        fields = line.strip().split()
        if len(fields) < 2:
            continue
        record = {"serial": fields[0], "state": fields[1]}
        for field in fields[2:]:
            if ":" in field:
                key, value = field.split(":", 1)
                record[key] = value
        devices.append(record)
    return devices


def select_device(
    devices: list[dict[str, str]],
    requested_serial: str | None,
) -> str:
    if requested_serial is not None:
        matches = [
            device for device in devices
            if device["serial"] == requested_serial
        ]
        if len(matches) != 1 or matches[0]["state"] != "device":
            raise ValueError("requested Android device is not authorized online")
        return requested_serial
    online = [
        device["serial"]
        for device in devices
        if device["state"] == "device"
    ]
    if len(online) != 1:
        raise ValueError(
            "connect exactly one authorized Android device or pass --serial"
        )
    return online[0]


def parse_thermal_snapshot(output: str) -> list[dict[str, Any]]:
    zones = []
    for line in output.splitlines():
        fields = line.strip().split("|", 2)
        if len(fields) != 3:
            continue
        zone, sensor_type, raw_text = fields
        try:
            raw = float(raw_text)
        except ValueError:
            continue
        if abs(raw) >= 1000.0:
            celsius = raw / 1000.0
        elif abs(raw) >= 200.0:
            celsius = raw / 10.0
        else:
            celsius = raw
        zones.append(
            {
                "zone": zone,
                "type": sensor_type,
                "raw": raw_text,
                "celsius": (
                    celsius if -50.0 <= celsius <= 200.0 else None
                ),
            }
        )
    return zones


def parse_cpu_frequencies(output: str) -> dict[str, int]:
    frequencies = {}
    for line in output.splitlines():
        fields = line.strip().split("|", 1)
        if len(fields) != 2 or not re.fullmatch(r"cpu[0-9]+", fields[0]):
            continue
        try:
            frequencies[fields[0]] = int(fields[1])
        except ValueError:
            continue
    return frequencies


def parse_battery(output: str) -> dict[str, Any]:
    battery: dict[str, Any] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        normalized = key.lower().replace(" ", "_")
        if re.fullmatch(r"-?[0-9]+", value):
            battery[normalized] = int(value)
        elif value.lower() in {"true", "false"}:
            battery[normalized] = value.lower() == "true"
        else:
            battery[normalized] = value
    return battery


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        raise ValueError("at least one device run is required")
    hashes = {run.get("pcm_fnv1a64") for run in runs}
    if None in hashes or len(hashes) != 1:
        raise ValueError("device runs disagree on decoded PCM hash")
    return {
        "run_count": len(runs),
        "pcm_fnv1a64": next(iter(hashes)),
        "all_passes_exact": all(
            run.get("all_passes_exact") is True for run in runs
        ),
        "deadline_misses_total": sum(
            int(run["deadline_misses"]) for run in runs
        ),
        "decode_realtime_speed_minimum": min(
            float(run["decode_realtime_speed"]) for run in runs
        ),
        "callback_seconds_p99_worst": max(
            float(run["callback_seconds_p99"]) for run in runs
        ),
        "callback_seconds_maximum": max(
            float(run["callback_seconds_max"]) for run in runs
        ),
        "caller_workspace_bytes": max(
            int(run["caller_workspace_bytes"]) for run in runs
        ),
    }


def maximum_temperature(zones: list[dict[str, Any]]) -> float | None:
    values = [
        float(zone["celsius"])
        for zone in zones
        if zone.get("celsius") is not None
    ]
    return max(values) if values else None


class Adb:
    def __init__(self, executable: str, serial: str) -> None:
        self.executable = executable
        self.serial = serial

    def run(
        self,
        *arguments: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.executable, "-s", self.serial, *arguments],
            check=check,
            capture_output=True,
            text=True,
        )

    def shell(self, command: str) -> str:
        return self.run("shell", command).stdout.strip()


def device_property(adb: Adb, name: str) -> str:
    return adb.shell(f"getprop {name}")


def capture_telemetry(adb: Adb) -> dict[str, Any]:
    thermal_script = (
        "for z in /sys/class/thermal/thermal_zone*; do "
        "[ -r \"$z/type\" ] && [ -r \"$z/temp\" ] && "
        "echo \"$(basename \"$z\")|$(cat \"$z/type\")|$(cat \"$z/temp\")\"; "
        "done"
    )
    frequency_script = (
        "for c in /sys/devices/system/cpu/cpu[0-9]*; do "
        "f=\"$c/cpufreq/scaling_cur_freq\"; "
        "[ -r \"$f\" ] && echo \"$(basename \"$c\")|$(cat \"$f\")\"; "
        "done"
    )
    return {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "thermal_zones": parse_thermal_snapshot(adb.shell(thermal_script)),
        "cpu_frequency_khz": parse_cpu_frequencies(
            adb.shell(frequency_script)
        ),
        "battery": parse_battery(adb.shell("dumpsys battery")),
    }


def remote_sha256(adb: Adb, path: str) -> str:
    output = adb.shell(f"sha256sum {path}")
    fields = output.split()
    if len(fields) < 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", fields[0]):
        raise RuntimeError(f"cannot verify device SHA-256 for {path}")
    return fields[0].lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--sustained-runs", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        not args.benchmark.is_file()
        or not args.stream.is_file()
        or args.iterations <= 0
        or args.warmups <= 0
        or args.sustained_runs <= 0
    ):
        raise ValueError("invalid Android device-gate inputs")

    listed = subprocess.run(
        [args.adb, "devices", "-l"],
        check=True,
        capture_output=True,
        text=True,
    )
    serial = select_device(
        parse_adb_devices(listed.stdout),
        args.serial,
    )
    adb = Adb(args.adb, serial)
    local_hashes = {
        "benchmark_sha256": file_sha256(args.benchmark),
        "stream_sha256": file_sha256(args.stream),
    }
    adb.shell(f"mkdir -p {REMOTE_DIRECTORY}")
    adb.run("push", str(args.benchmark), REMOTE_BENCHMARK)
    adb.run("push", str(args.stream), REMOTE_STREAM)
    adb.shell(f"chmod 700 {REMOTE_BENCHMARK}")
    device_hashes = {
        "benchmark_sha256": remote_sha256(adb, REMOTE_BENCHMARK),
        "stream_sha256": remote_sha256(adb, REMOTE_STREAM),
    }
    if device_hashes != local_hashes:
        raise RuntimeError("device-side input hash mismatch")

    device = {
        "serial": serial,
        "manufacturer": device_property(adb, "ro.product.manufacturer"),
        "model": device_property(adb, "ro.product.model"),
        "device": device_property(adb, "ro.product.device"),
        "android_release": device_property(adb, "ro.build.version.release"),
        "sdk": device_property(adb, "ro.build.version.sdk"),
        "abi": device_property(adb, "ro.product.cpu.abi"),
        "fingerprint": device_property(adb, "ro.build.fingerprint"),
    }
    before = capture_telemetry(adb)
    runs = []
    for _index in range(args.sustained_runs):
        completed = adb.run(
            "shell",
            REMOTE_BENCHMARK,
            REMOTE_STREAM,
            str(args.iterations),
            str(args.warmups),
        )
        runs.append(json.loads(completed.stdout))
    after = capture_telemetry(adb)
    summary = summarize_runs(runs)
    before_max = maximum_temperature(before["thermal_zones"])
    after_max = maximum_temperature(after["thermal_zones"])
    report = {
        "schema": "resonith-android-device-gate-1",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "device": device,
        "local_hashes": local_hashes,
        "device_hashes": device_hashes,
        "iterations_per_run": args.iterations,
        "warmups_per_run": args.warmups,
        "telemetry_before": before,
        "runs": runs,
        "telemetry_after": after,
        "summary": {
            **summary,
            "maximum_temperature_celsius_before": before_max,
            "maximum_temperature_celsius_after": after_max,
            "maximum_temperature_delta_celsius": (
                after_max - before_max
                if before_max is not None and after_max is not None
                else None
            ),
            "external_power_measurement_available": False,
        },
        "claim_scope": (
            "Named-device sustained callback timing and available telemetry; "
            "no energy claim without an external power measurement."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
