from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from android_device_gate import (  # noqa: E402
    parse_adb_devices,
    parse_battery,
    parse_cpu_frequencies,
    parse_thermal_snapshot,
    select_device,
    summarize_runs,
)


class AndroidDeviceGateTests(unittest.TestCase):
    def test_device_selection_rejects_ambiguous_or_offline_devices(self) -> None:
        devices = parse_adb_devices(
            "List of devices attached\n"
            "alpha device product:p model:Phone device:d\n"
            "beta offline transport_id:2\n"
        )
        self.assertEqual(select_device(devices, None), "alpha")
        with self.assertRaisesRegex(ValueError, "not authorized"):
            select_device(devices, "beta")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            select_device(
                devices
                + [{"serial": "gamma", "state": "device"}],
                None,
            )

    def test_telemetry_parsers_preserve_missing_or_vendor_values(self) -> None:
        thermal = parse_thermal_snapshot(
            "thermal_zone0|cpu-therm|42500\n"
            "thermal_zone1|battery|38\n"
            "thermal_zone2|bad|unavailable\n"
        )
        self.assertEqual(thermal[0]["celsius"], 42.5)
        self.assertEqual(thermal[1]["celsius"], 38.0)
        self.assertEqual(
            parse_cpu_frequencies("cpu0|1800000\ncpu7|2208000\nbad|1\n"),
            {"cpu0": 1800000, "cpu7": 2208000},
        )
        battery = parse_battery(
            "  AC powered: false\n  level: 73\n  technology: Li-ion\n"
        )
        self.assertFalse(battery["ac_powered"])
        self.assertEqual(battery["level"], 73)
        self.assertEqual(battery["technology"], "Li-ion")

    def test_sustained_summary_uses_worst_tail_and_rejects_hash_drift(self) -> None:
        runs = [
            {
                "pcm_fnv1a64": "0123456789abcdef",
                "all_passes_exact": True,
                "deadline_misses": 0,
                "decode_realtime_speed": 10.0,
                "callback_seconds_p99": 0.001,
                "callback_seconds_max": 0.002,
                "caller_workspace_bytes": 30000,
            },
            {
                "pcm_fnv1a64": "0123456789abcdef",
                "all_passes_exact": True,
                "deadline_misses": 1,
                "decode_realtime_speed": 8.0,
                "callback_seconds_p99": 0.003,
                "callback_seconds_max": 0.004,
                "caller_workspace_bytes": 30000,
            },
        ]
        summary = summarize_runs(runs)
        self.assertEqual(summary["deadline_misses_total"], 1)
        self.assertEqual(summary["decode_realtime_speed_minimum"], 8.0)
        self.assertEqual(summary["callback_seconds_p99_worst"], 0.003)
        drifted = [dict(runs[0]), dict(runs[1])]
        drifted[1]["pcm_fnv1a64"] = "fedcba9876543210"
        with self.assertRaisesRegex(ValueError, "PCM hash"):
            summarize_runs(drifted)


if __name__ == "__main__":
    unittest.main()
