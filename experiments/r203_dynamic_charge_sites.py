"""Clang-AST inventory for R-203 dynamic non-memory accounting sites.

The ordinary production tree is never rewritten by this module.  `probe`
prints a review candidate; `validate` compares the reviewed manifest with a
fresh pinned-Clang token and AST extraction.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


SCHEMA = "resonith-r203-dynamic-charge-site-inventory-1"
EXTRACTOR_SCHEMA = "resonith-r203-clang-ast-extractor-1"
PARENT_AMENDMENT = "R203-EVIDENCE-SPLIT-1"
PARENT_SHA256 = (
    "c9f736288e67f69622812149c2ab86e5f54439c9778bcf57068acd8b6585aa74"
)
HELPER_REACHABILITY_SCHEMA = "resonith-r203-helper-reachability-partition-1"
HELPER_REACHABILITY_PARENT_PREFLIGHT_SHA256 = (
    "253d18a9061560ab05a4650b7b36c305f85904fed114d648462ca3cbe6cb092b"
)
HELPER_REACHABILITY_AMENDMENT_PATH = (
    "docs/reviews/"
    "R203_HELPER_REACHABILITY_AMENDMENT_PREFLIGHT_2026-07-29.md"
)
HELPER_REACHABILITY_AMENDMENT_SHA256 = (
    "ef278c339f6923b1f0051d9cad55ec66780deff8240ab0867cfd8dd996387cbf"
)
DYNAMIC_EVENTS = (
    "RESONITH_PARTIAL_WORK_MERGE_COMPARE",
    "RESONITH_PARTIAL_WORK_MERGE_MOVE",
    "RESONITH_PARTIAL_WORK_LOOKUP",
    "RESONITH_PARTIAL_WORK_STATE",
    "RESONITH_PARTIAL_WORK_REFERENCE",
    "RESONITH_PARTIAL_WORK_SELECT",
    "RESONITH_PARTIAL_WORK_RECONSTRUCT",
)
EVENT_RECLASSIFICATION = {
    left: right
    for left, right in zip(
        DYNAMIC_EVENTS,
        DYNAMIC_EVENTS[1:] + DYNAMIC_EVENTS[:1],
        strict=True,
    )
}
MUTATION_KINDS = ("remove", "reclassify")
AST_FILTERS = (
    "stable_merge_sort_v1",
    "deterministic_resolution_table",
    "valid_observations",
    "valid_path_inputs",
    "bounded_state_arena",
    "deterministic_flat_map",
    "materialize_identity",
    "compare_identity",
    "candidate_better_value",
    "candidate_better_continuity",
    "family_better",
    "compute_paths_bounded",
    "enumerate_edges_stream",
    "input_fingerprint_v3",
    "compute_paths",
    "retain_bounded_state_union",
    "bounded_frequency_band",
    "resonith_partial_graph_edges_cpu",
    "insert_family_reservoir",
    "resonith_partial_graph_paths_cpu_v2_internal",
)
FREE_CHARGED_HELPERS = frozenset(
    {
        "candidate_better_continuity",
        "candidate_better_value",
        "compare_identity",
        "compute_paths_bounded",
        "family_better",
        "materialize_identity",
        "stable_merge_sort_v1",
        "valid_observations",
    }
)
LAMBDA_CHARGED_HELPERS = frozenset(
    {
        "contains_observation",
        "create_birth",
        "create_extension",
        "selection_position",
    }
)
LAMBDA_SITE_HELPERS = {
    65719: "lambda:contains_observation",
    175351: "lambda:create_birth",
    178151: "lambda:create_extension",
    200040: "lambda:selection_position",
}
MEMBER_CHARGED_HELPERS = {
    "bounded_state_arena": frozenset(
        {
            "add_child_reference",
            "add_reference",
            "at",
            "create_handle",
            "release",
        }
    ),
    "deterministic_flat_map": frozenset({"locate"}),
    "deterministic_resolution_table": frozenset({"locate"}),
}
BOUND_FUNCTIONS = frozenset({"ceil_log2", "max", "pow2"})
CALL_KINDS = frozenset(
    {
        "CallExpr",
        "CXXMemberCallExpr",
        "CXXOperatorCallExpr",
    }
)
OPERATION_NAMES = {
    "cancel_reserved": "cancel",
    "charge_reserved": "consume",
    "reserve": "reserve",
    "charge": "emit",
    "charge_work": "emit",
    "sink_": "emit",
}
TOKEN_PATTERN = re.compile(
    r"identifier '(?P<event>RESONITH_PARTIAL_WORK_[A-Z_]+)'.*"
    r"Loc=<(?P<path>.+):(?P<line>\d+):(?P<column>\d+)>$"
)


@dataclass(frozen=True)
class TokenReference:
    event: str
    path: str
    line: int
    column: int
    offset: int


@dataclass(frozen=True)
class AstSite:
    event: str
    operation: str
    helper: str
    offset: int
    call_begin: int
    call_end: int
    call_ast_sha256: str
    ast_filter: str
    call_ast_variants_sha256: tuple[str, ...] = ()
    ast_rank: int = 0

    def evidence(self) -> dict[str, object]:
        return {
            "event": self.event,
            "operation": self.operation,
            "helper": self.helper,
            "offset": self.offset,
            "call_begin": self.call_begin,
            "call_end": self.call_end,
            "call_ast_sha256": self.call_ast_sha256,
            "call_ast_variants_sha256": list(
                self.call_ast_variants_sha256
                or (self.call_ast_sha256,)
            ),
            "ast_filter": self.ast_filter,
        }


@dataclass(frozen=True)
class HelperInvocation:
    helper: str
    offset: int
    call_begin: int
    call_end: int
    call_ast_sha256: str
    ast_filter: str
    call_ast_variants_sha256: tuple[str, ...] = ()
    ast_rank: int = 0

    def evidence(self) -> dict[str, object]:
        return {
            "helper": self.helper,
            "offset": self.offset,
            "call_begin": self.call_begin,
            "call_end": self.call_end,
            "call_ast_sha256": self.call_ast_sha256,
            "call_ast_variants_sha256": list(
                self.call_ast_variants_sha256
                or (self.call_ast_sha256,)
            ),
            "ast_filter": self.ast_filter,
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def extractor_configuration_sha256() -> str:
    return _sha256_bytes(
        _canonical_json(
            {
                "schema": EXTRACTOR_SCHEMA,
                "ast_filters": list(AST_FILTERS),
                "free_charged_helpers": sorted(FREE_CHARGED_HELPERS),
                "lambda_charged_helpers": sorted(LAMBDA_CHARGED_HELPERS),
                "member_charged_helpers": {
                    owner: sorted(methods)
                    for owner, methods in sorted(
                        MEMBER_CHARGED_HELPERS.items()
                    )
                },
                "lambda_site_helpers": {
                    str(offset): helper
                    for offset, helper in sorted(LAMBDA_SITE_HELPERS.items())
                },
            }
        )
    )


def _normalized_path(value: str, repo: Path) -> str:
    text = value.replace("\\", "/")
    root = repo.resolve().as_posix()
    if text.casefold().startswith(root.casefold()):
        return "$REPO" + text[len(root) :]
    return text


def _split_compile_command(command: str) -> list[str]:
    return [part.strip('"') for part in shlex.split(command, posix=False)]


def _compile_entry(
    compile_database: Path,
    source: Path,
) -> tuple[dict[str, str], list[str]]:
    rows = json.loads(compile_database.read_text(encoding="utf-8"))
    matches = [
        row
        for row in rows
        if Path(row["file"]).resolve() == source.resolve()
    ]
    shared = [
        row
        for row in matches
        if "RESONITH_BUILDING_LIBRARY" in row["command"]
        and "RESONITH_SHARED" in row["command"]
    ]
    if len(shared) != 1:
        raise RuntimeError("compile database must contain one shared-core entry")
    row = shared[0]
    return row, _split_compile_command(row["command"])


def _production_compile_entries(
    compile_database: Path,
) -> list[dict[str, str]]:
    rows = json.loads(compile_database.read_text(encoding="utf-8"))
    selected = [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("command"), str)
        and "RESONITH_BUILDING_LIBRARY" in row["command"]
        and "RESONITH_SHARED" in row["command"]
    ]
    by_source: dict[Path, dict[str, str]] = {}
    for row in selected:
        source = Path(row["file"]).resolve()
        if source in by_source:
            raise RuntimeError(
                "production compile database repeats a shared-core source"
            )
        by_source[source] = row
    if not by_source:
        raise RuntimeError("production compile database has no shared-core sources")
    return [by_source[source] for source in sorted(by_source, key=str)]


def _raw_dynamic_references(
    path: Path,
    repo: Path,
) -> list[dict[str, object]]:
    payload = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\b(?:" + "|".join(map(re.escape, DYNAMIC_EVENTS)) + r")\b"
    )
    references: list[dict[str, object]] = []
    for match in pattern.finditer(payload):
        line = payload.count("\n", 0, match.start()) + 1
        line_start = payload.rfind("\n", 0, match.start()) + 1
        references.append(
            {
                "path": _normalized_path(str(path.resolve()), repo),
                "event": match.group(0),
                "line": line,
                "column": match.start() - line_start + 1,
            }
        )
    return references


def production_scope_evidence(
    compile_database: Path,
    repo: Path,
) -> dict[str, object]:
    entries = _production_compile_entries(compile_database)
    translation_units: list[dict[str, object]] = []
    files: dict[Path, dict[str, object]] = {}
    for row in entries:
        source = Path(row["file"]).resolve()
        command = _split_compile_command(row["command"])
        translation_units.append(
            {
                "path": _normalized_path(str(source), repo),
                "sha256": sha256_file(source),
                "compile_command_sha256": normalized_compile_command_sha256(
                    command,
                    source,
                    repo,
                ),
            }
        )
        files[source] = {
            "path": _normalized_path(str(source), repo),
            "sha256": sha256_file(source),
        }
    include_root = repo / "native" / "include"
    for suffix in ("*.h", "*.hpp"):
        for path in include_root.rglob(suffix):
            resolved = path.resolve()
            files[resolved] = {
                "path": _normalized_path(str(resolved), repo),
                "sha256": sha256_file(resolved),
            }
    cmake_file = (repo / "native" / "CMakeLists.txt").resolve()
    files[cmake_file] = {
        "path": _normalized_path(str(cmake_file), repo),
        "sha256": sha256_file(cmake_file),
    }
    file_rows = sorted(files.values(), key=lambda item: str(item["path"]))
    references: list[dict[str, object]] = []
    for path in sorted(files, key=str):
        references.extend(_raw_dynamic_references(path, repo))
    references.sort(
        key=lambda item: (
            str(item["path"]),
            int(item["line"]),
            int(item["column"]),
            str(item["event"]),
        )
    )
    commitment = {
        "translation_unit_count": len(translation_units),
        "file_count": len(file_rows),
        "dynamic_reference_count": len(references),
        "translation_units_sha256": _sha256_bytes(
            _canonical_json(translation_units)
        ),
        "production_files_sha256": _sha256_bytes(_canonical_json(file_rows)),
        "dynamic_references_sha256": _sha256_bytes(
            _canonical_json(references)
        ),
    }
    return {
        "commitment": commitment,
        "translation_units": translation_units,
        "production_files": file_rows,
        "dynamic_references": references,
    }


def _analysis_arguments(
    command: list[str],
    source: Path,
) -> tuple[str, list[str]]:
    if not command:
        raise RuntimeError("empty compile command")
    compiler = command[0]
    arguments: list[str] = []
    skip = False
    for index, value in enumerate(command[1:]):
        if skip:
            skip = False
            continue
        if value == "-o":
            skip = True
            continue
        if value == "-c":
            continue
        if Path(value).resolve() == source.resolve():
            continue
        arguments.append(value)
    return compiler, arguments


def normalized_compile_command_sha256(
    command: list[str],
    source: Path,
    repo: Path,
) -> str:
    compiler, arguments = _analysis_arguments(command, source)
    normalized = [
        _normalized_path(compiler, repo),
        *(_normalized_path(value, repo) for value in arguments),
        "$SOURCE",
    ]
    return _sha256_bytes(_canonical_json(normalized))


def _line_offsets(source_bytes: bytes) -> list[int]:
    starts = [0]
    for index, value in enumerate(source_bytes):
        if value == 0x0A:
            starts.append(index + 1)
    return starts


def _source_offset(starts: list[int], line: int, column: int) -> int:
    if line < 1 or line > len(starts) or column < 1:
        raise RuntimeError("Clang token location is outside the source")
    return starts[line - 1] + column - 1


def scan_dynamic_tokens(
    compiler: str,
    arguments: list[str],
    source: Path,
) -> tuple[list[TokenReference], str]:
    diagnostics: list[str] = []
    process = subprocess.Popen(
        [
            compiler,
            *arguments,
            # Clang's token-dump action does not interpret target pack pragmas
            # even though the ordinary parser does. Keep the frozen compile
            # command and suppress only this extractor-specific diagnostic.
            "-Wno-error=unknown-pragmas",
            "-Xclang",
            "-dump-tokens",
            "-fsyntax-only",
            str(source),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    assert process.stderr is not None
    source_bytes = source.read_bytes()
    starts = _line_offsets(source_bytes)
    references: list[TokenReference] = []
    token_digest = hashlib.sha256()
    for line_text in process.stderr:
        token_digest.update(line_text.encode("utf-8"))
        if "error:" in line_text or "warning:" in line_text:
            diagnostics.append(line_text.rstrip())
        match = TOKEN_PATTERN.search(line_text.rstrip("\r\n"))
        if match is None or match.group("event") not in DYNAMIC_EVENTS:
            continue
        path = match.group("path")
        if Path(path).resolve() != source.resolve():
            continue
        line = int(match.group("line"))
        column = int(match.group("column"))
        references.append(
            TokenReference(
                event=match.group("event"),
                path=path,
                line=line,
                column=column,
                offset=_source_offset(starts, line, column),
            )
        )
    return_code = process.wait()
    if return_code != 0:
        detail = "\n".join(diagnostics[-20:])
        raise RuntimeError(
            f"Clang token extraction failed: {return_code}\n{detail}"
        )
    unique = {(item.offset, item.event) for item in references}
    if len(unique) != len(references):
        raise RuntimeError("Clang token extraction produced duplicate references")
    return references, token_digest.hexdigest()


def _json_documents(payload: str) -> Iterator[dict[str, object]]:
    decoder = json.JSONDecoder()
    offset = 0
    while offset < len(payload):
        while offset < len(payload) and payload[offset].isspace():
            offset += 1
        if offset == len(payload):
            return
        value, offset = decoder.raw_decode(payload, offset)
        if not isinstance(value, dict):
            raise RuntimeError("Clang AST document is not an object")
        yield value


def _normalized_ast(node: object) -> object:
    if isinstance(node, list):
        return [_normalized_ast(value) for value in node]
    if not isinstance(node, dict):
        return node
    result: dict[str, object] = {}
    for key in (
        "kind",
        "name",
        "opcode",
        "castKind",
        "valueCategory",
        "isArrow",
    ):
        if key in node:
            result[key] = node[key]
    referenced = node.get("referencedDecl")
    if isinstance(referenced, dict):
        result["referencedDecl"] = {
            key: referenced[key]
            for key in ("kind", "name")
            if key in referenced
        }
    member = node.get("referencedMemberDecl")
    if isinstance(member, dict):
        result["referencedMemberDecl"] = {
            key: member[key]
            for key in ("kind", "name")
            if key in member
        }
    inner = node.get("inner")
    if isinstance(inner, list):
        result["inner"] = [_normalized_ast(value) for value in inner]
    return result


def _declared_names(node: object) -> set[str]:
    names: set[str] = set()
    stack = [node]
    while stack:
        value = stack.pop()
        if isinstance(value, list):
            stack.extend(value)
            continue
        if not isinstance(value, dict):
            continue
        referenced = value.get("referencedDecl")
        if isinstance(referenced, dict) and isinstance(
            referenced.get("name"),
            str,
        ):
            names.add(referenced["name"])
        if isinstance(value.get("name"), str):
            names.add(value["name"])
        stack.extend(
            child
            for child in value.values()
            if isinstance(child, (dict, list))
        )
    return names


def _surface_nodes(node: object) -> Iterable[dict[str, object]]:
    """Walk one call expression without entering nested call expressions."""

    stack: list[tuple[object, bool]] = [(node, True)]
    while stack:
        value, root = stack.pop()
        if isinstance(value, list):
            stack.extend((child, False) for child in value)
            continue
        if not isinstance(value, dict):
            continue
        if not root and value.get("kind") in CALL_KINDS:
            continue
        yield value
        stack.extend(
            (child, False)
            for child in value.values()
            if isinstance(child, (dict, list))
        )


def _surface_names(node: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for value in _surface_nodes(node):
        referenced = value.get("referencedDecl")
        if isinstance(referenced, dict) and isinstance(
            referenced.get("name"),
            str,
        ):
            names.add(str(referenced["name"]))
        member = value.get("referencedMemberDecl")
        if isinstance(member, dict) and isinstance(member.get("name"), str):
            names.add(str(member["name"]))
        if isinstance(value.get("name"), str):
            names.add(str(value["name"]))
    return names


def _surface_types(node: dict[str, object]) -> tuple[str, ...]:
    types: set[str] = set()
    for value in _surface_nodes(node):
        type_value = value.get("type")
        if not isinstance(type_value, dict):
            continue
        for key in ("qualType", "desugaredQualType"):
            name = type_value.get(key)
            if isinstance(name, str):
                types.add(name)
    return tuple(sorted(types))


def _helper_identity(call: dict[str, object]) -> str | None:
    names = _surface_names(call)
    for helper in sorted(FREE_CHARGED_HELPERS):
        if helper in names:
            return helper
    for helper in sorted(LAMBDA_CHARGED_HELPERS):
        if helper in names:
            return f"lambda:{helper}"
    joined_types = " ".join(_surface_types(call))
    for owner, methods in MEMBER_CHARGED_HELPERS.items():
        if owner not in joined_types:
            continue
        for method in sorted(methods):
            if method in names:
                return f"{owner}::{method}"
    return None


def _enclosing_helper_identity(
    ancestors: tuple[dict[str, object], ...],
    ast_filter: str,
    offset: int,
) -> str:
    explicit_lambda = LAMBDA_SITE_HELPERS.get(offset)
    if explicit_lambda is not None:
        return explicit_lambda
    lambda_name = next(
        (
            str(ancestor["name"])
            for ancestor in reversed(ancestors)
            if ancestor.get("kind") == "VarDecl"
            and ancestor.get("name") in LAMBDA_CHARGED_HELPERS
        ),
        None,
    )
    for ancestor in reversed(ancestors):
        kind = ancestor.get("kind")
        name = ancestor.get("name")
        if kind == "CXXMethodDecl" and name == "operator()" and lambda_name:
            return f"lambda:{lambda_name}"
        if kind == "CXXMethodDecl" and isinstance(name, str):
            for owner, methods in MEMBER_CHARGED_HELPERS.items():
                if name not in methods:
                    continue
                if ast_filter == owner or any(
                    parent.get("kind") == "CXXRecordDecl"
                    and parent.get("name") == owner
                    for parent in ancestors
                ):
                    return f"{owner}::{name}"
        if (
            kind == "FunctionDecl"
            and isinstance(name, str)
            and name in FREE_CHARGED_HELPERS
        ):
            return name
    raise RuntimeError(
        "dynamic event reference has no charged helper identity: "
        f"{ast_filter}@{offset}"
    )


def _call_operation(call: dict[str, object]) -> str:
    names = _declared_names(call)
    for name, operation in OPERATION_NAMES.items():
        if name in names:
            return operation
    raise RuntimeError("dynamic event reference has no recognized operation")


def _range_offsets(node: dict[str, object]) -> tuple[int, int]:
    range_value = node.get("range")
    if not isinstance(range_value, dict):
        raise RuntimeError("AST call has no source range")
    begin = range_value.get("begin")
    end = range_value.get("end")
    if not isinstance(begin, dict) or not isinstance(end, dict):
        raise RuntimeError("AST call range is incomplete")
    if "offset" not in begin or "offset" not in end:
        raise RuntimeError("AST call range has no source offsets")
    call_begin = int(begin["offset"])
    call_end = int(end["offset"]) + int(end.get("tokLen", 0))
    return call_begin, call_end


def _walk_ast(
    node: object,
    ancestors: tuple[dict[str, object], ...] = (),
) -> Iterable[
    tuple[dict[str, object], tuple[dict[str, object], ...]]
]:
    if isinstance(node, list):
        for child in node:
            yield from _walk_ast(child, ancestors)
        return
    if not isinstance(node, dict):
        return
    yield node, ancestors
    next_ancestors = (*ancestors, node)
    for child in node.values():
        if isinstance(child, (dict, list)):
            yield from _walk_ast(child, next_ancestors)


def _nearest_call(
    ancestors: tuple[dict[str, object], ...],
) -> dict[str, object]:
    for ancestor in reversed(ancestors):
        if ancestor.get("kind") in CALL_KINDS:
            return ancestor
    raise RuntimeError("dynamic event reference is not inside a call")


def _call_rank(call: dict[str, object]) -> int:
    return {
        "CallExpr": 0,
        "CXXMemberCallExpr": 1,
        "CXXOperatorCallExpr": 2,
    }.get(str(call.get("kind")), 3)


def _ast_for_filter(
    compiler: str,
    arguments: list[str],
    source: Path,
    ast_filter: str,
) -> list[dict[str, object]]:
    completed = subprocess.run(
        [
            compiler,
            *arguments,
            "-Xclang",
            "-ast-dump=json",
            "-Xclang",
            f"-ast-dump-filter={ast_filter}",
            "-fsyntax-only",
            str(source),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Clang AST extraction failed for {ast_filter}: "
            f"{completed.stderr.strip()}"
        )
    return list(_json_documents(completed.stdout))


def discover_ast_evidence(
    compiler: str,
    arguments: list[str],
    source: Path,
    ast_filters: Iterable[str],
) -> tuple[list[AstSite], list[HelperInvocation]]:
    sites: dict[tuple[int, str], AstSite] = {}
    helpers: dict[tuple[int, str], HelperInvocation] = {}
    for ast_filter in ast_filters:
        roots = _ast_for_filter(
            compiler,
            arguments,
            source,
            ast_filter,
        )
        for root in roots:
            for node, ancestors in _walk_ast(root):
                referenced = node.get("referencedDecl")
                name = (
                    referenced.get("name")
                    if isinstance(referenced, dict)
                    else None
                )
                if name in DYNAMIC_EVENTS:
                    range_value = node.get("range")
                    begin = (
                        range_value.get("begin")
                        if isinstance(range_value, dict)
                        else None
                    )
                    if not isinstance(begin, dict) or "offset" not in begin:
                        raise RuntimeError("dynamic AST reference has no offset")
                    call = _nearest_call(ancestors)
                    call_begin, call_end = _range_offsets(call)
                    evidence = AstSite(
                        event=name,
                        operation=_call_operation(call),
                        helper=_enclosing_helper_identity(
                            ancestors,
                            ast_filter,
                            int(begin["offset"]),
                        ),
                        offset=int(begin["offset"]),
                        call_begin=call_begin,
                        call_end=call_end,
                        call_ast_sha256=_sha256_bytes(
                            _canonical_json(_normalized_ast(call))
                        ),
                        ast_filter=ast_filter,
                        call_ast_variants_sha256=(
                            _sha256_bytes(
                                _canonical_json(_normalized_ast(call))
                            ),
                        ),
                        ast_rank=_call_rank(call),
                    )
                    key = (evidence.offset, evidence.event)
                    prior = sites.get(key)
                    if prior is not None:
                        if (
                            prior.operation != evidence.operation
                            or prior.helper != evidence.helper
                            or prior.call_begin != evidence.call_begin
                            or prior.call_end != evidence.call_end
                        ):
                            raise RuntimeError(
                                "template instantiations disagree on AST "
                                f"evidence for {key}: "
                                f"{prior.ast_filter}/"
                                f"{prior.call_ast_sha256} != "
                                f"{ast_filter}/"
                                f"{evidence.call_ast_sha256}"
                            )
                        variants = tuple(
                            sorted(
                                {
                                    *prior.call_ast_variants_sha256,
                                    *evidence.call_ast_variants_sha256,
                                }
                            )
                        )
                        canonical = min(
                            (prior, evidence),
                            key=lambda item: (
                                item.ast_rank,
                                item.call_ast_sha256,
                            ),
                        )
                        sites[key] = AstSite(
                            event=prior.event,
                            operation=prior.operation,
                            helper=prior.helper,
                            offset=prior.offset,
                            call_begin=prior.call_begin,
                            call_end=prior.call_end,
                            call_ast_sha256=canonical.call_ast_sha256,
                            ast_filter=prior.ast_filter,
                            call_ast_variants_sha256=variants,
                            ast_rank=canonical.ast_rank,
                        )
                    else:
                        sites[key] = evidence
                if node.get("kind") not in CALL_KINDS:
                    continue
                helper_name = _helper_identity(node)
                if helper_name is None:
                    continue
                call_begin, call_end = _range_offsets(node)
                helper = HelperInvocation(
                    helper=helper_name,
                    offset=call_begin,
                    call_begin=call_begin,
                    call_end=call_end,
                    call_ast_sha256=_sha256_bytes(
                        _canonical_json(_normalized_ast(node))
                    ),
                    ast_filter=ast_filter,
                    call_ast_variants_sha256=(
                        _sha256_bytes(
                            _canonical_json(_normalized_ast(node))
                        ),
                    ),
                    ast_rank=_call_rank(node),
                )
                key = (helper.offset, helper.helper)
                prior_helper = helpers.get(key)
                if prior_helper is not None:
                    if (
                        prior_helper.call_begin != helper.call_begin
                        or prior_helper.call_end != helper.call_end
                    ):
                        raise RuntimeError(
                            "helper template instantiations disagree on "
                            f"AST evidence for {key}: "
                            f"{prior_helper.ast_filter}/"
                            f"{prior_helper.call_ast_sha256} != "
                            f"{ast_filter}/"
                            f"{helper.call_ast_sha256}"
                        )
                    variants = tuple(
                        sorted(
                            {
                                *prior_helper.call_ast_variants_sha256,
                                *helper.call_ast_variants_sha256,
                            }
                        )
                    )
                    canonical = min(
                        (prior_helper, helper),
                        key=lambda item: (
                            item.ast_rank,
                            item.call_ast_sha256,
                        ),
                    )
                    helpers[key] = HelperInvocation(
                        helper=prior_helper.helper,
                        offset=prior_helper.offset,
                        call_begin=prior_helper.call_begin,
                        call_end=prior_helper.call_end,
                        call_ast_sha256=canonical.call_ast_sha256,
                        ast_filter=prior_helper.ast_filter,
                        call_ast_variants_sha256=variants,
                        ast_rank=canonical.ast_rank,
                    )
                else:
                    helpers[key] = helper
    return (
        sorted(sites.values(), key=lambda item: (item.offset, item.event)),
        sorted(helpers.values(), key=lambda item: (item.offset, item.helper)),
    )


def _expected_mapping(
    rows: list[dict[str, object]],
    *,
    identifier: str,
) -> dict[tuple[int, str], dict[str, object]]:
    result: dict[tuple[int, str], dict[str, object]] = {}
    for row in rows:
        if identifier not in row or not isinstance(row[identifier], str):
            raise RuntimeError(f"manifest row has no {identifier}")
        event_or_helper = str(row.get("event", row.get("helper", "")))
        key = (int(row["offset"]), event_or_helper)
        if key in result:
            raise RuntimeError("manifest contains a duplicate AST anchor")
        result[key] = row
    return result


def apply_isolated_mutant(
    source: bytes,
    site: dict[str, object],
    mutation_kind: str,
) -> tuple[bytes, dict[str, object]]:
    """Return one temporary-source mutant without touching the input bytes."""

    if mutation_kind not in MUTATION_KINDS:
        raise RuntimeError("unsupported dynamic-site mutation kind")
    event = site.get("event")
    operation = site.get("operation")
    if event not in DYNAMIC_EVENTS or operation not in {
        "emit",
        "reserve",
        "cancel",
        "consume",
    }:
        raise RuntimeError("dynamic-site mutation metadata is invalid")
    event_bytes = str(event).encode("ascii")
    offset = int(site["offset"])
    call_begin = int(site["call_begin"])
    call_end = int(site["call_end"])
    if (
        call_begin < 0
        or call_begin > offset
        or offset + len(event_bytes) > call_end
        or call_end > len(source)
        or source[offset : offset + len(event_bytes)] != event_bytes
    ):
        raise RuntimeError("dynamic-site mutation anchor does not match source")

    if mutation_kind == "reclassify":
        replacement = EVENT_RECLASSIFICATION[str(event)].encode("ascii")
        mutated = (
            source[:offset]
            + replacement
            + source[offset + len(event_bytes) :]
        )
        replaced_begin = offset
        replaced_end = offset + len(event_bytes)
    else:
        replacement = (
            b"true"
            if operation in {"cancel", "consume"}
            else b"static_cast<void>(0)"
        )
        mutated = source[:call_begin] + replacement + source[call_end:]
        replaced_begin = call_begin
        replaced_end = call_end
    if mutated == source:
        raise RuntimeError("dynamic-site mutation did not change source")
    return mutated, {
        "schema": "resonith-r203-dynamic-charge-site-mutant-1",
        "site_id": site.get("site_id"),
        "mutation_kind": mutation_kind,
        "event_before": event,
        "event_after": (
            EVENT_RECLASSIFICATION[str(event)]
            if mutation_kind == "reclassify"
            else None
        ),
        "operation": operation,
        "replaced_begin": replaced_begin,
        "replaced_end": replaced_end,
        "source_before_sha256": _sha256_bytes(source),
        "source_after_sha256": _sha256_bytes(mutated),
        "replacement_sha256": _sha256_bytes(replacement),
    }


def evaluate_bound_expression(
    expression: str,
    variables: dict[str, int],
) -> int:
    """Evaluate one declarative nonnegative integer bound fail-closed."""

    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 128:
        raise RuntimeError("dynamic-site bound expression is too complex")

    def evaluate(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, int) or node.value < 0:
                raise RuntimeError("bound constants must be nonnegative integers")
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise RuntimeError(f"bound variable is missing: {node.id}")
            value = variables[node.id]
            if not isinstance(value, int) or value < 0:
                raise RuntimeError("bound variables must be nonnegative integers")
            return value
        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Sub):
                if right > left:
                    raise RuntimeError("bound subtraction became negative")
                return left - right
            if isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise RuntimeError("bound division by zero")
                return left // right
            raise RuntimeError("bound binary operator is forbidden")
        if isinstance(node, ast.Call):
            if (
                not isinstance(node.func, ast.Name)
                or node.func.id not in BOUND_FUNCTIONS
                or node.keywords
            ):
                raise RuntimeError("bound function is forbidden")
            values = [evaluate(argument) for argument in node.args]
            if node.func.id == "ceil_log2":
                if len(values) != 1:
                    raise RuntimeError("ceil_log2 requires one argument")
                return 0 if values[0] <= 1 else (values[0] - 1).bit_length()
            if node.func.id == "pow2":
                if len(values) != 1 or values[0] > 256:
                    raise RuntimeError("pow2 exponent is outside the frozen bound")
                return 1 << values[0]
            if not values:
                raise RuntimeError("max requires at least one argument")
            return max(values)
        raise RuntimeError("bound syntax is forbidden")

    return evaluate(tree)


def evaluate_declared_bound(
    bound: dict[str, object],
    variables: dict[str, int],
) -> int:
    declared = bound.get("variables")
    expression = bound.get("expression")
    if (
        not isinstance(declared, list)
        or not all(isinstance(value, str) and value for value in declared)
        or not isinstance(expression, str)
        or not expression
    ):
        raise RuntimeError("dynamic-site bound declaration is invalid")
    if set(variables) != set(declared):
        raise RuntimeError("dynamic-site bound variables differ from declaration")
    return evaluate_bound_expression(expression, variables)


def validate_manifest_evidence(
    manifest: dict[str, object],
    *,
    source_sha256: str,
    header_sha256: str,
    clang_sha256: str,
    clang_version: str,
    compile_command_sha256: str,
    token_stream_sha256: str,
    token_references: list[TokenReference],
    sites: list[AstSite],
    helpers: list[HelperInvocation],
    production_scope: dict[str, object] | None = None,
) -> dict[str, object]:
    if manifest.get("schema") != SCHEMA:
        raise RuntimeError("dynamic-site manifest schema is unsupported")
    if manifest.get("parent_amendment") != PARENT_AMENDMENT:
        raise RuntimeError("dynamic-site manifest amendment is wrong")
    if manifest.get("parent_sha256") != PARENT_SHA256:
        raise RuntimeError("dynamic-site parent preflight hash is wrong")
    frozen = manifest.get("frozen_inputs")
    if not isinstance(frozen, dict):
        raise RuntimeError("dynamic-site frozen inputs are missing")
    expected_hashes = {
        "source_sha256": source_sha256,
        "header_sha256": header_sha256,
        "clang_sha256": clang_sha256,
        "compile_command_sha256": compile_command_sha256,
        "token_stream_sha256": token_stream_sha256,
    }
    if any(frozen.get(key) != value for key, value in expected_hashes.items()):
        raise RuntimeError("dynamic-site frozen input hash differs")
    if frozen.get("clang_version") != clang_version:
        raise RuntimeError("dynamic-site pinned Clang version differs")
    if production_scope is not None:
        commitment = production_scope.get("commitment")
        if (
            not isinstance(commitment, dict)
            or manifest.get("production_scope") != commitment
        ):
            raise RuntimeError("production reference scope commitment differs")

    ast_filters = manifest.get("ast_filters")
    if ast_filters != list(AST_FILTERS):
        raise RuntimeError("dynamic-site AST filter set differs")
    extractor = manifest.get("extractor")
    expected_extractor_sha256 = extractor_configuration_sha256()
    if (
        not isinstance(extractor, dict)
        or extractor.get("schema") != EXTRACTOR_SCHEMA
        or extractor.get("configuration_sha256")
        != expected_extractor_sha256
    ):
        raise RuntimeError("dynamic-site AST extractor identity differs")

    token_keys = {(item.offset, item.event) for item in token_references}
    ast_keys = {(item.offset, item.event) for item in sites}
    if token_keys != ast_keys:
        raise RuntimeError("Clang token and AST dynamic-site inventories differ")

    manifest_sites = manifest.get("sites")
    if not isinstance(manifest_sites, list):
        raise RuntimeError("dynamic-site manifest rows are missing")
    expected_site_count = manifest.get("expected_site_count")
    expected_helper_count = manifest.get("expected_helper_invocation_count")
    expected_mutant_count = manifest.get("expected_mutant_count")
    if (
        expected_site_count != len(sites)
        or expected_helper_count != len(helpers)
        or expected_mutant_count != 2 * len(sites)
    ):
        raise RuntimeError("dynamic-site expected inventory counts differ")

    witnesses = manifest.get("witnesses")
    if not isinstance(witnesses, list) or not witnesses:
        raise RuntimeError("dynamic-site immutable witnesses are missing")
    witness_by_id: dict[str, dict[str, object]] = {}
    witness_kinds: dict[str, str] = {}
    for witness in witnesses:
        if not isinstance(witness, dict):
            raise RuntimeError("dynamic-site witness row is invalid")
        witness_id = witness.get("witness_id")
        kind = witness.get("kind")
        if (
            not isinstance(witness_id, str)
            or not witness_id
            or witness_id in witness_by_id
            or kind not in {"ordinary", "hostile", "reachability"}
        ):
            raise RuntimeError("dynamic-site witness identity is invalid")
        for field, value in witness.items():
            if field.endswith("_sha256") and (
                not isinstance(value, str)
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
            ):
                raise RuntimeError("dynamic-site witness hash is invalid")
        witness_by_id[witness_id] = witness
        witness_kinds[witness_id] = str(kind)
    if not {"ordinary", "hostile"}.issubset(witness_kinds.values()):
        raise RuntimeError("ordinary and hostile witnesses are both required")

    bounds = manifest.get("bounds")
    if not isinstance(bounds, list) or not bounds:
        raise RuntimeError("dynamic-site independent bounds are missing")
    bound_ids: set[str] = set()
    for bound in bounds:
        if (
            not isinstance(bound, dict)
            or not isinstance(bound.get("bound_id"), str)
            or not isinstance(bound.get("expression"), str)
            or not isinstance(bound.get("variables"), list)
            or bound.get("expression") in {"maximum_work_units", "absolute"}
            or bound["bound_id"] in bound_ids
        ):
            raise RuntimeError("dynamic-site bound is missing or trivial")
        bound_ids.add(str(bound["bound_id"]))
        evaluate_declared_bound(
            bound,
            {str(name): 1 for name in bound["variables"]},
        )
    if "dynamic-aggregate" not in bound_ids:
        raise RuntimeError("dynamic-site aggregate bound is missing")

    expected_sites = _expected_mapping(manifest_sites, identifier="site_id")
    actual_sites = {
        (item.offset, item.event): item.evidence()
        for item in sites
    }
    site_inventory_sha256 = _sha256_bytes(
        _canonical_json([item.evidence() for item in sites])
    )
    if manifest.get("site_inventory_sha256") != site_inventory_sha256:
        raise RuntimeError("reviewed accounting-site inventory differs")
    if set(expected_sites) != set(actual_sites):
        raise RuntimeError("manifest and AST accounting-anchor sets differ")
    mutant_ids: set[str] = set()
    site_operations: set[str] = set()
    for key, expected in expected_sites.items():
        actual = actual_sites[key]
        for field, value in actual.items():
            if field == "helper":
                continue
            if expected.get(field) != value:
                raise RuntimeError(
                    f"manifest accounting-anchor evidence differs: "
                    f"{expected['site_id']}:{field}"
                )
        if expected.get("reclassify_event") != EVENT_RECLASSIFICATION[key[1]]:
            raise RuntimeError("manifest reclassification cycle differs")
        site_id = expected["site_id"]
        if (
            not isinstance(expected.get("enclosing"), str)
            or not expected["enclosing"]
            or expected["enclosing"] != expected.get("ast_filter")
        ):
            raise RuntimeError("accounting anchor enclosing scope differs")
        if "helper_invocation_ids" in expected:
            raise RuntimeError(
                "accounting anchor uses obsolete helper-invocation authority"
            )
        witness_ids = expected.get("witness_ids")
        if not isinstance(witness_ids, list) or not witness_ids:
            raise RuntimeError("accounting anchor has no immutable witness")
        if (
            any(value not in witness_by_id for value in witness_ids)
            or {witness_kinds[value] for value in witness_ids}
            != {"ordinary", "hostile"}
        ):
            raise RuntimeError("accounting anchor witness coverage differs")
        site_bound_ids = expected.get("bound_ids")
        if (
            not isinstance(site_bound_ids, list)
            or "dynamic-aggregate" not in site_bound_ids
            or any(value not in bound_ids for value in site_bound_ids)
        ):
            raise RuntimeError("accounting anchor bound coverage differs")
        expected_mutants = {
            "remove_mutant_id": f"REMOVE:{site_id}",
            "reclassify_mutant_id": f"RECLASSIFY:{site_id}",
        }
        for mutant_field, expected_mutant in expected_mutants.items():
            mutant_id = expected.get(mutant_field)
            if mutant_id != expected_mutant or mutant_id in mutant_ids:
                raise RuntimeError("accounting anchor mutant ID differs")
            mutant_ids.add(str(mutant_id))
        operation = str(expected.get("operation"))
        site_operations.add(operation)
        expected_rejection = (
            "class-b-ledger-difference"
            if operation == "emit"
            else "typed-ledger-or-transaction-rejection"
        )
        if expected.get("expected_runtime_rejection") != expected_rejection:
            raise RuntimeError("accounting anchor rejection channel differs")

    helper_evidence = [item.evidence() for item in helpers]
    helper_inventory_sha256 = _sha256_bytes(
        _canonical_json(helper_evidence)
    )
    if manifest.get("helper_inventory_sha256") != helper_inventory_sha256:
        raise RuntimeError("reviewed helper-invocation inventory differs")

    helper_reachability = manifest.get("helper_reachability")
    if (
        not isinstance(helper_reachability, dict)
        or helper_reachability.get("schema") != HELPER_REACHABILITY_SCHEMA
        or helper_reachability.get("parent_preflight_sha256")
        != HELPER_REACHABILITY_PARENT_PREFLIGHT_SHA256
        or helper_reachability.get("amendment_path")
        != HELPER_REACHABILITY_AMENDMENT_PATH
        or helper_reachability.get("amendment_sha256")
        != HELPER_REACHABILITY_AMENDMENT_SHA256
        or helper_reachability.get("helper_inventory_sha256")
        != helper_inventory_sha256
    ):
        raise RuntimeError("helper reachability commitment differs")
    expected_reachable_count = helper_reachability.get(
        "expected_reachable_count"
    )
    expected_unreachable_count = helper_reachability.get(
        "expected_proven_unreachable_count"
    )
    if (
        not isinstance(expected_reachable_count, int)
        or not isinstance(expected_unreachable_count, int)
        or expected_reachable_count < 0
        or expected_unreachable_count < 0
        or expected_reachable_count + expected_unreachable_count != len(helpers)
        or (
            len(helpers) == 54
            and (expected_reachable_count, expected_unreachable_count) != (53, 1)
        )
    ):
        raise RuntimeError("helper reachability class counts differ")
    reachable_rows = helper_reachability.get("reachable_helper_invocations")
    unreachable_rows = helper_reachability.get(
        "proven_unreachable_helper_invocations"
    )
    if (
        not isinstance(reachable_rows, list)
        or not isinstance(unreachable_rows, list)
        or len(reachable_rows) != expected_reachable_count
        or len(unreachable_rows) != expected_unreachable_count
        or not all(isinstance(row, dict) for row in reachable_rows)
        or not all(isinstance(row, dict) for row in unreachable_rows)
    ):
        raise RuntimeError("helper reachability class sizes differ")
    reachable_ids = [row.get("invocation_id") for row in reachable_rows]
    unreachable_ids = [row.get("invocation_id") for row in unreachable_rows]
    if (
        any(not isinstance(value, str) for value in reachable_ids)
        or any(not isinstance(value, str) for value in unreachable_ids)
        or len(set(reachable_ids)) != len(reachable_ids)
        or len(set(unreachable_ids)) != len(unreachable_ids)
        or set(reachable_ids).intersection(unreachable_ids)
    ):
        raise RuntimeError("helper reachability classes are not disjoint")
    actual_by_invocation = {
        f"{item.helper}@{item.offset}": item.evidence() for item in helpers
    }
    if (
        set(reachable_ids).union(unreachable_ids)
        != set(actual_by_invocation)
        or (
            len(helpers) == 54
            and unreachable_ids != ["bounded_state_arena::release@134436"]
        )
    ):
        raise RuntimeError("helper reachability partition is incomplete")
    partition_rows: list[dict[str, object]] = []
    for classification, rows in (
        ("reachable", reachable_rows),
        ("proven-unreachable", unreachable_rows),
    ):
        for row in rows:
            invocation_id = str(row["invocation_id"])
            actual = actual_by_invocation[invocation_id]
            expected_identity = {
                "helper": actual["helper"],
                "call_begin": actual["call_begin"],
                "call_end": actual["call_end"],
                "call_ast_sha256": actual["call_ast_sha256"],
            }
            if classification == "reachable":
                if set(row) != {"invocation_id", "witness_ids"}:
                    raise RuntimeError(
                        "reachable helper row contains noncanonical fields"
                    )
            elif any(
                row.get(key) != value for key, value in expected_identity.items()
            ):
                raise RuntimeError("unreachable helper AST identity differs")
            witness_key = (
                "witness_ids"
                if classification == "reachable"
                else "zero_witness_ids"
            )
            witness_ids = row.get(witness_key)
            if (
                not isinstance(witness_ids, list)
                or not witness_ids
                or any(value not in witness_by_id for value in witness_ids)
            ):
                raise RuntimeError("helper reachability witness identity differs")
            partition_rows.append(
                {
                    "invocation_id": invocation_id,
                    **expected_identity,
                    "classification": classification,
                    witness_key: witness_ids,
                }
            )
    partition_rows.sort(key=lambda row: str(row["invocation_id"]))
    partition_sha256 = _sha256_bytes(_canonical_json(partition_rows))
    if helper_reachability.get("partition_sha256") != partition_sha256:
        raise RuntimeError("helper reachability partition digest differs")

    helper_groups = manifest.get("helper_groups")
    if not isinstance(helper_groups, list) or not helper_groups:
        raise RuntimeError("dynamic-site helper groups are missing")
    group_by_id: dict[str, str] = {}
    actual_helper_names = {item.helper for item in helpers}
    for group in helper_groups:
        if not isinstance(group, dict):
            raise RuntimeError("dynamic-site helper group is invalid")
        group_id = group.get("group_id")
        group_helper = group.get("helper")
        witness_ids = group.get("witness_ids")
        helper_bound_ids = group.get("bound_ids")
        if (
            not isinstance(group_id, str)
            or not group_id.startswith("group:")
            or group_id in group_by_id
            or not isinstance(group_helper, str)
            or group_helper not in actual_helper_names
            or not isinstance(witness_ids, list)
            or not witness_ids
            or any(value not in witness_by_id for value in witness_ids)
            or not isinstance(helper_bound_ids, list)
            or "dynamic-aggregate" not in helper_bound_ids
            or any(value not in bound_ids for value in helper_bound_ids)
        ):
            raise RuntimeError("dynamic-site helper group identity differs")
        if group_helper in group_by_id.values():
            raise RuntimeError("charged helper belongs to multiple groups")
        group_by_id[group_id] = group_helper
    if set(group_by_id.values()) != actual_helper_names:
        raise RuntimeError("dynamic-site helper group coverage differs")
    bindings = manifest.get("site_helper_bindings")
    if not isinstance(bindings, list):
        raise RuntimeError("accounting-site helper bindings are missing")
    binding_by_site: dict[str, str] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            raise RuntimeError("accounting-site helper binding is invalid")
        site_id = binding.get("site_id")
        group_id = binding.get("group_id")
        if (
            not isinstance(site_id, str)
            or not isinstance(group_id, str)
            or site_id in binding_by_site
            or group_id not in group_by_id
        ):
            raise RuntimeError("accounting-site helper binding differs")
        binding_by_site[site_id] = group_id
    expected_site_ids = {
        str(expected["site_id"]) for expected in expected_sites.values()
    }
    if set(binding_by_site) != expected_site_ids:
        raise RuntimeError("accounting-site helper binding coverage differs")
    for key, expected in expected_sites.items():
        group_id = binding_by_site[str(expected["site_id"])]
        if group_id not in group_by_id:
            raise RuntimeError("accounting anchor helper binding differs")
        group_helper = group_by_id[group_id]
        if group_helper != actual_sites[key]["helper"]:
            raise RuntimeError("accounting anchor helper identity differs")

    required_operations = manifest.get("required_operations")
    if (
        not isinstance(required_operations, list)
        or set(required_operations) != site_operations
    ):
        raise RuntimeError("dynamic-site operation-family coverage differs")

    return {
        "schema": "resonith-r203-dynamic-charge-site-validation-1",
        "site_count": len(sites),
        "helper_invocation_count": len(helpers),
        "remove_mutant_count": len(sites),
        "reclassify_mutant_count": len(sites),
        "extractor_configuration_sha256": expected_extractor_sha256,
        "token_inventory_sha256": _sha256_bytes(
            _canonical_json(
                [
                    {
                        "event": item.event,
                        "offset": item.offset,
                        "line": item.line,
                        "column": item.column,
                    }
                    for item in token_references
                ]
            )
        ),
        "site_inventory_sha256": _sha256_bytes(
            _canonical_json([item.evidence() for item in sites])
        ),
        "helper_inventory_sha256": _sha256_bytes(
            _canonical_json([item.evidence() for item in helpers])
        ),
        "helper_invocations": [
            {
                "invocation_id": f"{item.helper}@{item.offset}",
                **item.evidence(),
            }
            for item in helpers
        ],
        "helper_reachability_partition_sha256": partition_sha256,
        "reachable_helper_invocation_count": len(reachable_rows),
        "proven_unreachable_helper_invocation_count": len(unreachable_rows),
        "production_scope": (
            production_scope.get("commitment")
            if production_scope is not None
            else None
        ),
    }


def _probe_result(
    *,
    source_sha256: str,
    header_sha256: str,
    clang_sha256: str,
    compile_command_sha256: str,
    token_stream_sha256: str,
    sites: list[AstSite],
    helpers: list[HelperInvocation],
    production_scope: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": "resonith-r203-dynamic-charge-site-probe-1",
        "status": "review-candidate-only",
        "parent_amendment": PARENT_AMENDMENT,
        "parent_sha256": PARENT_SHA256,
        "frozen_inputs": {
            "source_sha256": source_sha256,
            "header_sha256": header_sha256,
            "clang_sha256": clang_sha256,
            "compile_command_sha256": compile_command_sha256,
            "token_stream_sha256": token_stream_sha256,
        },
        "sites": [item.evidence() for item in sites],
        "helper_invocations": [item.evidence() for item in helpers],
        "site_inventory_sha256": _sha256_bytes(
            _canonical_json([item.evidence() for item in sites])
        ),
        "helper_inventory_sha256": _sha256_bytes(
            _canonical_json([item.evidence() for item in helpers])
        ),
        "production_scope": production_scope,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe or validate R-203 dynamic charge sites.",
    )
    parser.add_argument("mode", choices=("probe", "validate"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--compile-database", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    arguments = parser.parse_args()

    repo = arguments.repo.resolve()
    source = repo / "native" / "src" / "partial_graph.cpp"
    header = repo / "native" / "include" / "resonith" / "partial_graph.h"
    row, command = _compile_entry(arguments.compile_database, source)
    compiler, analysis_arguments = _analysis_arguments(command, source)
    clang_path = Path(compiler)
    if not clang_path.is_file():
        raise RuntimeError("pinned Clang compiler does not exist")
    compile_hash = normalized_compile_command_sha256(command, source, repo)
    production_scope = production_scope_evidence(
        arguments.compile_database,
        repo,
    )

    manifest: dict[str, object] | None = None
    if arguments.mode == "validate":
        if arguments.manifest is None:
            raise RuntimeError("validate mode requires --manifest")
        manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
        ast_filters = manifest.get("ast_filters")
        if ast_filters != list(AST_FILTERS):
            raise RuntimeError("manifest AST filters are missing")
    else:
        ast_filters = list(AST_FILTERS)

    tokens, token_stream_hash = scan_dynamic_tokens(
        compiler,
        analysis_arguments,
        source,
    )
    sites, helpers = discover_ast_evidence(
        compiler,
        analysis_arguments,
        source,
        ast_filters,
    )
    source_hash = sha256_file(source)
    header_hash = sha256_file(header)
    clang_hash = sha256_file(clang_path)
    clang_version_process = subprocess.run(
        [compiler, "--version"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    clang_version = clang_version_process.stdout.splitlines()[0].strip()

    if arguments.mode == "probe":
        result = _probe_result(
            source_sha256=source_hash,
            header_sha256=header_hash,
            clang_sha256=clang_hash,
            compile_command_sha256=compile_hash,
            token_stream_sha256=token_stream_hash,
            sites=sites,
            helpers=helpers,
            production_scope=production_scope,
        )
    else:
        assert manifest is not None
        result = validate_manifest_evidence(
            manifest,
            source_sha256=source_hash,
            header_sha256=header_hash,
            clang_sha256=clang_hash,
            clang_version=clang_version,
            compile_command_sha256=compile_hash,
            token_stream_sha256=token_stream_hash,
            token_references=tokens,
            sites=sites,
            helpers=helpers,
            production_scope=production_scope,
        )
        result["compile_database_entry_sha256"] = _sha256_bytes(
            _canonical_json(
                {
                    "directory": _normalized_path(row["directory"], repo),
                    "command": _normalized_path(row["command"], repo),
                    "file": _normalized_path(row["file"], repo),
                    "output": _normalized_path(row["output"], repo),
                }
            )
        )
        result["manifest_sha256"] = sha256_file(arguments.manifest)

    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
