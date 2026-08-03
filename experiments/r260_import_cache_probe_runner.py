"""Create bounded parent receipts for the R-260 startup-state probe."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve(strict=True).parents[1]
PYTHON = ROOT / "artifacts/tools/python-3.14.6-amd64/python.exe"
PROBE = ROOT / "experiments/r260_import_cache_startup_probe.py"
RESULT = ROOT / "artifacts/r260-import-cache-startup-probe-v4"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(name: str, flags: list[str]) -> dict:
    prefix = RESULT / f"{name}-pycache"
    output = RESULT / f"{name}.json"
    stdout_path = RESULT / f"{name}.stdout.log"
    stderr_path = RESULT / f"{name}.stderr.log"
    receipt_path = RESULT / f"{name}.receipt.json"
    if any(path.exists() for path in (prefix, output, stdout_path, stderr_path, receipt_path)):
        raise FileExistsError(f"R-260 output was not fresh: {name}")
    prefix.mkdir()
    command = [str(PYTHON), *flags, "-X", f"pycache_prefix={prefix}", str(PROBE), str(output)]
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("PYTHON")
        and not key.startswith("RESONITH_R257_PREFIX")
        and key != "RESONITH_R257_STAGE1"
    }
    contract = {
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": str(prefix),
    }
    environment.update(contract)
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            shell=False,
            check=False,
            capture_output=True,
            timeout=20.0,
        )
        exit_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code, stdout, stderr = -1, error.stdout or b"", error.stderr or b""
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    prefix_entries = sorted(str(path.relative_to(prefix)) for path in prefix.rglob("*"))
    observed = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
    source_records = (
        [
            item
            for item in observed["initial_cache"]
            if item["raw_key"] == observed["source_spelling"]
        ]
        if observed
        else []
    )
    receipt = {
        "schema": "resonith-r260-import-cache-probe-parent-receipt-1",
        "name": name,
        "cwd": str(ROOT),
        "command": command,
        "environment_contract": contract,
        "python_sha256": _sha(PYTHON),
        "probe_sha256": _sha(PROBE),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "output_sha256": _sha(output) if output.is_file() else None,
        "prefix_existed_before": False,
        "output_existed_before": False,
        "prefix_entries_after": prefix_entries,
        "source_record_count": len(source_records),
        "source_record": source_records[0] if len(source_records) == 1 else None,
        "source_spelling_matches_bound_probe": bool(
            observed and observed["source_spelling"] == str(PROBE.resolve(strict=True))
        ),
        "source_absent_from_raw_sys_path": bool(
            observed
            and observed["source_spelling"]
            not in [item["raw_item"] for item in observed["initial_sys_path"]]
        ),
        "source_absent_from_resolved_sys_path": bool(
            observed
            and observed["source"]
            not in [
                str(Path(item["raw_item"]).resolve(strict=False))
                for item in observed["initial_sys_path"]
                if item["item_type_module"] == "builtins" and item["item_type_name"] == "str"
            ]
        ),
        "source_reparse_entries": observed["source_reparse_entries"] if observed else None,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if (
        exit_code != 0
        or timed_out
        or prefix_entries
        or len(source_records) != 1
        or source_records[0]["key_type_module"] != "builtins"
        or source_records[0]["key_type_name"] != "str"
        or not source_records[0]["value_is_none"]
        or source_records[0]["resolved_target"] != observed["source"]
        or not receipt["source_spelling_matches_bound_probe"]
        or not receipt["source_absent_from_raw_sys_path"]
        or not receipt["source_absent_from_resolved_sys_path"]
        or receipt["source_reparse_entries"]
    ):
        raise RuntimeError(f"R-260 startup probe failed: {receipt_path}")
    return receipt


def main() -> int:
    if RESULT.exists():
        raise FileExistsError(f"R-260 result root was not fresh: {RESULT}")
    RESULT.mkdir()
    receipts = [_run("isolated", ["-I", "-S", "-B"]), _run("safe-path", ["-S", "-P", "-B"])]
    summary = {"schema": "resonith-r260-import-cache-probe-summary-1", "receipts": receipts}
    (RESULT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
