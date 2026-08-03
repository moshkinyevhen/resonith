"""Capture the raw CPython source-file startup importer-cache state."""

import sys


INITIAL_CACHE = tuple(
    (
        type(key).__module__,
        type(key).__qualname__,
        key if type(key) is str else repr(key),
        value is None,
        type(value).__module__,
        type(value).__qualname__,
    )
    for key, value in sys.path_importer_cache.items()
)
INITIAL_PATH = tuple(
    (type(item).__module__, type(item).__qualname__, item if type(item) is str else repr(item))
    for item in sys.path
)

import hashlib
import json
import os
from pathlib import Path


def _canonical(raw: str) -> str:
    return os.path.normcase(os.path.abspath(raw or os.getcwd()))


source_lexical = Path(__file__).absolute()
source_spelling = str(source_lexical)
source_chain = (source_lexical, *source_lexical.parents)
source_chain_state = tuple(
    (str(item), getattr(item.lstat(), "st_file_attributes", 0)) for item in source_chain
)
source = source_lexical.resolve(strict=True)
payload = {
    "schema": "resonith-r260-import-cache-startup-probe-1",
    "source": str(source),
    "source_spelling": source_spelling,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_reparse_entries": [
        raw for raw, attributes in source_chain_state if attributes & 0x400
    ],
    "source_chain_state": [
        {"raw_path": raw, "file_attributes": attributes}
        for raw, attributes in source_chain_state
    ],
    "argv": list(sys.argv),
    "orig_argv": list(sys.orig_argv),
    "flags": {
        "isolated": int(sys.flags.isolated),
        "no_site": int(sys.flags.no_site),
        "safe_path": bool(sys.flags.safe_path),
        "dont_write_bytecode": bool(sys.dont_write_bytecode),
        "pycache_prefix": sys.pycache_prefix,
    },
    "initial_cache": [
        {
            "key_type_module": module,
            "key_type_name": name,
            "raw_key": raw,
            "lexical_key": _canonical(raw) if module == "builtins" and name == "str" else None,
            "resolved_target": str(Path(raw).resolve(strict=True))
            if module == "builtins" and name == "str" and raw == source_spelling
            else None,
            "value_is_none": is_none,
            "value_type_module": value_module,
            "value_type_name": value_name,
        }
        for module, name, raw, is_none, value_module, value_name in INITIAL_CACHE
    ],
    "initial_sys_path": [
        {
            "item_type_module": module,
            "item_type_name": name,
            "raw_item": raw,
            "canonical_item": _canonical(raw) if module == "builtins" and name == "str" else None,
        }
        for module, name, raw in INITIAL_PATH
    ],
}
encoded = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
output = Path(sys.argv[1]).resolve(strict=False)
output.write_text(encoded, encoding="utf-8", newline="\n")
print("R260_PROBE=" + json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
