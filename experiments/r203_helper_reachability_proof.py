"""Executable R-203 proof for one statically unreachable helper invocation.

This verifier is deliberately narrow.  It accepts only the frozen
`bounded_state_arena::create_handle` control-flow shape and fails closed on an
unknown AST construct, exception-model drift, alias, extra write, or cleanup
after the only `parent_acquired = true` assignment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from experiments import r203_dynamic_charge_sites as sites


SCHEMA = "resonith-r203-helper-unreachable-proof-1"
AST_NORMALIZATION_SCHEMA = "resonith-r203-proof-ast-normalization-1"
TARGET_HELPER = "bounded_state_arena::release"
TARGET_FUNCTION = "create_handle"
TARGET_VARIABLE = "parent_acquired"
TARGET_PREDECESSOR = "bounded_state_arena::add_child_reference"
FORBIDDEN_EXCEPTION_FLAGS = frozenset(
    {
        "-fasync-exceptions",
        "-fnon-call-exceptions",
        "-fno-exceptions",
        "-fno-cxx-exceptions",
    }
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _proof_ast(node: object) -> object:
    """Normalize only semantically relevant, deterministic Clang AST fields."""

    if isinstance(node, list):
        return [_proof_ast(value) for value in node]
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
        "value",
    ):
        if key in node:
            result[key] = node[key]
    type_value = node.get("type")
    if isinstance(type_value, dict):
        result["type"] = {
            key: type_value[key]
            for key in ("qualType", "desugaredQualType")
            if key in type_value
        }
    for key in ("referencedDecl", "referencedMemberDecl"):
        referenced = node.get(key)
        if isinstance(referenced, dict):
            result[key] = {
                field: referenced[field]
                for field in ("kind", "name")
                if field in referenced
            }
    range_value = node.get("range")
    if isinstance(range_value, dict):
        normalized_range: dict[str, object] = {}
        for edge in ("begin", "end"):
            value = range_value.get(edge)
            if isinstance(value, dict):
                normalized_range[edge] = {
                    field: value[field]
                    for field in ("offset", "tokLen")
                    if field in value
                }
        result["range"] = normalized_range
    inner = node.get("inner")
    if isinstance(inner, list):
        result["inner"] = [_proof_ast(value) for value in inner]
    return result


def _proof_ast_sha256(node: object) -> str:
    return sha256_bytes(canonical_json_bytes(_proof_ast(node)))


def ast_normalization_configuration_sha256() -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "schema": AST_NORMALIZATION_SCHEMA,
                "scalar_fields": [
                    "kind",
                    "name",
                    "opcode",
                    "castKind",
                    "valueCategory",
                    "isArrow",
                    "value",
                ],
                "type_fields": ["qualType", "desugaredQualType"],
                "reference_fields": ["kind", "name"],
                "range_fields": ["offset", "tokLen"],
                "recursive_field": "inner",
            }
        )
    )


def _range(node: dict[str, object]) -> tuple[int, int]:
    return sites._range_offsets(node)


def _contains(outer: dict[str, object], inner: dict[str, object]) -> bool:
    outer_begin, outer_end = _range(outer)
    inner_begin, inner_end = _range(inner)
    return outer_begin <= inner_begin and inner_end <= outer_end


def _direct_inner(node: dict[str, object]) -> list[dict[str, object]]:
    inner = node.get("inner")
    if not isinstance(inner, list):
        return []
    if not all(isinstance(value, dict) for value in inner):
        raise RuntimeError("proof AST contains a non-object child")
    return inner


def _walk_inner(
    node: object,
    ancestors: tuple[dict[str, object], ...] = (),
):
    """Walk only the executable/declaration AST `inner` tree."""

    if isinstance(node, list):
        for child in node:
            yield from _walk_inner(child, ancestors)
        return
    if not isinstance(node, dict):
        return
    yield node, ancestors
    inner = node.get("inner")
    if isinstance(inner, list):
        for child in inner:
            yield from _walk_inner(child, (*ancestors, node))


def _references(node: object, name: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for value, _ in _walk_inner(node):
        referenced = value.get("referencedDecl")
        if (
            value.get("kind") == "DeclRefExpr"
            and isinstance(referenced, dict)
            and referenced.get("name") == name
        ):
            result.append(value)
    return result


def _literal_bool(node: object, expected: bool) -> bool:
    literals = [
        value
        for value, _ in _walk_inner(node)
        if value.get("kind") == "CXXBoolLiteralExpr"
    ]
    return (
        len(literals) == 1
        and literals[0].get("value") is expected
        and not any(
            value.get("kind") in sites.CALL_KINDS
            for value, _ in _walk_inner(node)
        )
    )


def _extract_cfg(
    compiler: str,
    arguments: list[str],
    source: Path,
) -> tuple[str, dict[str, str]]:
    completed = subprocess.run(
        [
            compiler,
            *arguments,
            "-Xclang",
            "-analyze",
            "-Xclang",
            "-analyzer-checker=debug.DumpCFG",
            "-fsyntax-only",
            str(source),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Clang CFG extraction failed: {completed.stderr[-2000:]}")
    text = completed.stderr.replace("\r\n", "\n")
    headers = list(
        re.finditer(
            r"(?m)^(?! )[^\n]+\n \[B\d+ \(ENTRY\)\]$",
            text,
        )
    )
    matches: list[str] = []
    for index, match in enumerate(headers):
        if (
            match.group(0).splitlines()[0]
            != "bounded_state_handle create_handle("
            "const bounded_state_node &value)"
        ):
            continue
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        matches.append(text[match.start() : end].rstrip() + "\n")
    if len(matches) != 1:
        raise RuntimeError("proof CFG does not contain exactly one target function")
    cfg = matches[0]
    blocks = {
        block.group("id"): block.group(0)
        for block in re.finditer(
            r"(?ms)^ \[(?P<id>B\d+)(?: \(ENTRY\)| \(EXIT\))?\]\n"
            r".*?(?=^ \[B\d+(?: \(ENTRY\)| \(EXIT\))?\]\n|\Z)",
            cfg,
        )
    }
    if not blocks:
        raise RuntimeError("proof CFG block extraction failed")
    return cfg, blocks


def _exception_model(
    compiler: str,
    arguments: list[str],
) -> dict[str, object]:
    forbidden = sorted(set(arguments).intersection(FORBIDDEN_EXCEPTION_FLAGS))
    if forbidden:
        raise RuntimeError(f"unsupported exception flags: {forbidden}")
    if not any(value == "-std=c++23" for value in arguments):
        raise RuntimeError("proof requires the frozen C++23 dialect")
    completed = subprocess.run(
        [compiler, *arguments, "-dM", "-E", "-x", "c++", "-"],
        input="",
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    if completed.returncode != 0:
        raise RuntimeError("exception-model macro probe failed")
    macros = {
        match.group(1): match.group(2)
        for match in re.finditer(
            r"(?m)^#define (__EXCEPTIONS|__cpp_exceptions) (.+)$",
            completed.stdout,
        )
    }
    if macros != {"__EXCEPTIONS": "1", "__cpp_exceptions": "199711L"}:
        raise RuntimeError("standard C++ exception macros differ")
    triple = subprocess.run(
        [compiler, "-dumpmachine"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    ).stdout.strip()
    return {
        "cxx_dialect": "c++23",
        "target_triple": triple,
        "exception_macros": macros,
        "exception_flags": [
            value
            for value in arguments
            if "exception" in value or "unwind" in value
        ],
        "forbidden_exception_flags_absent": sorted(FORBIDDEN_EXCEPTION_FLAGS),
        "model_scope": "standard-cxx-synchronous-exceptions-only",
        "excluded": [
            "signals",
            "injected-seh-faults",
            "undefined-behavior",
            "nonstandard-asynchronous-exceptions",
        ],
    }


def prove(
    *,
    compiler: str,
    arguments: list[str],
    source: Path,
) -> dict[str, object]:
    roots = sites._ast_for_filter(
        compiler,
        arguments,
        source,
        "bounded_state_arena",
    )
    methods = [
        node
        for root in roots
        for node, _ in _walk_inner(root)
        if node.get("kind") == "CXXMethodDecl"
        and node.get("name") == TARGET_FUNCTION
    ]
    if len(methods) != 1:
        raise RuntimeError("proof requires exactly one create_handle method")
    method = methods[0]

    declarations = [
        node
        for node, _ in _walk_inner(method)
        if node.get("kind") == "VarDecl" and node.get("name") == TARGET_VARIABLE
    ]
    if len(declarations) != 1:
        raise RuntimeError("proof variable declaration is not unique")
    declaration = declarations[0]
    type_value = declaration.get("type")
    if (
        not isinstance(type_value, dict)
        or type_value.get("qualType") != "bool"
        or "volatile" in str(type_value.get("qualType"))
        or not _literal_bool(declaration, False)
    ):
        raise RuntimeError("proof variable is not built-in non-volatile false bool")

    references: list[
        tuple[dict[str, object], tuple[dict[str, object], ...]]
    ] = []
    for node, ancestors in _walk_inner(method):
        referenced = node.get("referencedDecl")
        if (
            node.get("kind") == "DeclRefExpr"
            and isinstance(referenced, dict)
            and referenced.get("name") == TARGET_VARIABLE
        ):
            references.append((node, ancestors))
    if len(references) != 2:
        raise RuntimeError("proof variable is aliased, captured, or referenced extra")

    writes = [
        ancestor
        for _, ancestors in references
        for ancestor in ancestors[-1:]
        if ancestor.get("kind") == "BinaryOperator"
        and ancestor.get("opcode") == "="
    ]
    if len(writes) != 1 or not _literal_bool(writes[0], True):
        raise RuntimeError("proof requires exactly one assignment of true")
    assignment = writes[0]
    assignment_reference = references[0]
    if assignment not in assignment_reference[1]:
        assignment_reference = references[1]
    guard_reference = references[1] if assignment_reference is references[0] else references[0]

    address_taking = [
        ancestor
        for _, ancestors in references
        for ancestor in ancestors
        if ancestor.get("kind") in {
            "LambdaExpr",
            "BlockExpr",
        }
        or (
            ancestor.get("kind") == "UnaryOperator"
            and ancestor.get("opcode") == "&"
        )
    ]
    if address_taking:
        raise RuntimeError("proof variable address/capture escapes")

    target_calls: list[
        tuple[dict[str, object], tuple[dict[str, object], ...]]
    ] = []
    predecessor_calls: list[
        tuple[dict[str, object], tuple[dict[str, object], ...]]
    ] = []
    for node, ancestors in _walk_inner(method):
        if node.get("kind") not in sites.CALL_KINDS:
            continue
        identity = sites._helper_identity(node)
        if identity == TARGET_HELPER:
            target_calls.append((node, ancestors))
        elif identity == TARGET_PREDECESSOR:
            predecessor_calls.append((node, ancestors))
    if len(target_calls) != 1 or len(predecessor_calls) != 1:
        raise RuntimeError("proof helper calls are not unique")
    target_call, target_ancestors = target_calls[0]
    predecessor_call, predecessor_ancestors = predecessor_calls[0]

    try_nodes = [
        ancestor
        for ancestor in target_ancestors
        if ancestor.get("kind") == "CXXTryStmt"
    ]
    catch_nodes = [
        ancestor
        for ancestor in target_ancestors
        if ancestor.get("kind") == "CXXCatchStmt"
    ]
    if len(try_nodes) != 1 or len(catch_nodes) != 1:
        raise RuntimeError("target release is not in one catch")
    try_node = try_nodes[0]
    catch_node = catch_nodes[0]
    catch_children = _direct_inner(catch_node)
    if (
        len(catch_children) != 2
        or catch_children[0].get("id") != "0x0"
        or catch_children[0].get("kind") is not None
        or catch_children[1].get("kind") != "CompoundStmt"
    ):
        raise RuntimeError("proof requires catch-all without exception binding")

    assignment_compounds = [
        ancestor
        for ancestor in assignment_reference[1]
        if ancestor.get("kind") == "CompoundStmt"
        and _contains(ancestor, assignment)
        and _contains(ancestor, predecessor_call)
    ]
    if not assignment_compounds:
        raise RuntimeError("predecessor and assignment do not share a compound")
    assignment_compound = min(
        assignment_compounds,
        key=lambda value: _range(value)[1] - _range(value)[0],
    )
    direct = _direct_inner(assignment_compound)
    if direct != [predecessor_call, assignment]:
        raise RuntimeError(
            "assignment is not the final full-expression immediately after "
            "add_child_reference"
        )
    forbidden_after_call = {
        "ExprWithCleanups",
        "CXXBindTemporaryExpr",
        "MaterializeTemporaryExpr",
        "VarDecl",
    }
    if any(
        node.get("kind") in forbidden_after_call
        for node, _ in _walk_inner(assignment)
    ):
        raise RuntimeError("assignment has an unsupported cleanup construct")

    assignment_if_nodes = [
        ancestor
        for ancestor in assignment_reference[1]
        if ancestor.get("kind") == "IfStmt"
        and _contains(ancestor, assignment_compound)
        and _contains(ancestor, predecessor_call)
    ]
    if len(assignment_if_nodes) != 1:
        raise RuntimeError("proof assignment does not belong to one target if")
    assignment_if = assignment_if_nodes[0]
    try_children = _direct_inner(try_node)
    try_bodies = [
        child for child in try_children if child.get("kind") == "CompoundStmt"
    ]
    if len(try_bodies) != 1:
        raise RuntimeError("proof try does not have one compound body")
    try_body = try_bodies[0]
    try_statements = _direct_inner(try_body)
    if not try_statements or try_statements[-1] is not assignment_if:
        raise RuntimeError("target if is not the final statement in the try")
    assignment_if_children = _direct_inner(assignment_if)
    if (
        len(assignment_if_children) != 2
        or assignment_if_children[1] is not assignment_compound
    ):
        raise RuntimeError("target assignment is not the complete then-body")
    if any(
        node.get("kind") == "VarDecl"
        for node, _ in _walk_inner(try_body)
    ):
        raise RuntimeError(
            "proof rejects automatic objects whose cleanup may cross the write"
        )
    crossing_cleanup_kinds = {
        "ExprWithCleanups",
        "CXXBindTemporaryExpr",
        "MaterializeTemporaryExpr",
    }
    if any(
        ancestor.get("kind") in crossing_cleanup_kinds
        for ancestor in assignment_reference[1]
        if _contains(try_body, ancestor)
    ):
        raise RuntimeError("proof write is enclosed by an unknown cleanup")

    # Conservative forward dataflow over the frozen shape.  Every full
    # expression before the write is allowed to throw; because the variable is
    # still false, each such exceptional edge contributes only false.  The
    # predecessor call is evaluated before the assignment, so its exceptional
    # edge also contributes false.  The only normal path after the write has
    # state true, but the structural checks above prove there is no following
    # expression or cleanup that can enter the catch.
    state_before_write = {False}
    catch_entry_values: set[bool] = set()
    prewrite_statements = try_statements[:-1]
    if prewrite_statements:
        catch_entry_values.update(state_before_write)
    condition = assignment_if_children[0]
    catch_entry_values.update(state_before_write)
    if not _contains(assignment_compound, predecessor_call):
        raise RuntimeError("predecessor call is outside the assignment body")
    catch_entry_values.update(state_before_write)
    state_after_write = {True}
    postwrite_throw_points: list[dict[str, object]] = []
    if try_statements[-1] is not assignment_if or direct[-1] is not assignment:
        postwrite_throw_points.append(assignment_if)
    if postwrite_throw_points:
        catch_entry_values.update(state_after_write)
    if catch_entry_values != {False}:
        raise RuntimeError("catch-entry forward dataflow is not exactly false")
    dataflow_evidence = {
        "schema": "resonith-r203-forward-dataflow-1",
        "initial_values": ["false"],
        "prewrite_statement_count": len(prewrite_statements),
        "target_condition_ast_sha256": _proof_ast_sha256(condition),
        "predecessor_exception_values": ["false"],
        "postwrite_normal_values": ["true"],
        "postwrite_throw_point_count": len(postwrite_throw_points),
        "catch_entry_values": [
            "true" if value else "false"
            for value in sorted(catch_entry_values)
        ],
        "normal_try_exit_values": ["false", "true"],
        "transfer_rule":
            "all-prewrite-full-expressions-may-throw; "
            "no-postwrite-expression-or-cleanup",
    }

    guards = [
        ancestor
        for ancestor in target_ancestors
        if ancestor.get("kind") == "IfStmt"
        and _contains(ancestor, target_call)
    ]
    exact_guards = []
    for guard in guards:
        children = _direct_inner(guard)
        if len(children) != 2 or not _contains(children[1], target_call):
            continue
        condition = children[0]
        condition_type = condition.get("type")
        condition_children = _direct_inner(condition)
        if (
            condition.get("kind") != "ImplicitCastExpr"
            or condition.get("castKind") != "LValueToRValue"
            or not isinstance(condition_type, dict)
            or condition_type.get("qualType") != "bool"
            or len(condition_children) != 1
        ):
            continue
        reference = condition_children[0]
        referenced = reference.get("referencedDecl")
        reference_type = reference.get("type")
        if (
            reference.get("kind") != "DeclRefExpr"
            or reference.get("valueCategory") != "lvalue"
            or not isinstance(referenced, dict)
            or referenced.get("kind") != "VarDecl"
            or referenced.get("name") != TARGET_VARIABLE
            or not isinstance(reference_type, dict)
            or reference_type.get("qualType") != "bool"
            or len(_direct_inner(reference)) != 0
        ):
            continue
        exact_guards.append(guard)
    if len(exact_guards) != 1:
        raise RuntimeError("release is not guarded only by parent_acquired")
    guard = exact_guards[0]
    if guard not in guard_reference[1]:
        raise RuntimeError("the second proof-variable reference is not the guard")

    cfg, cfg_blocks = _extract_cfg(compiler, arguments, source)
    assignment_blocks = [
        (name, text)
        for name, text in cfg_blocks.items()
        if "->add_child_reference" in text
        and "parent_acquired" in text
        and "= [B" in text
    ]
    catch_blocks = [
        (name, text)
        for name, text in cfg_blocks.items()
        if "catch (...):" in text and "parent_acquired" in text
    ]
    release_blocks = [
        (name, text)
        for name, text in cfg_blocks.items()
        if "->release" in text
    ]
    if (
        len(assignment_blocks) != 1
        or len(catch_blocks) != 1
        or len(release_blocks) != 1
    ):
        raise RuntimeError("normalized CFG does not preserve proof blocks")
    assignment_block_name, assignment_block = assignment_blocks[0]
    if assignment_block.find("->add_child_reference") >= assignment_block.find(
        "parent_acquired"
    ):
        raise RuntimeError("CFG does not sequence predecessor before assignment")
    numbered = [
        line.strip()
        for line in assignment_block.splitlines()
        if re.match(r"^\d+:", line.strip())
    ]
    if not numbered or " = " not in numbered[-1]:
        raise RuntimeError("assignment is not the last evaluated CFG expression")

    exception_model = _exception_model(compiler, arguments)
    predicates = {
        "builtin_nonvolatile_bool_initialized_false": True,
        "no_alias_capture_or_address_escape": True,
        "exactly_one_write_assigns_true": True,
        "write_after_predecessor_normal_return": True,
        "assignment_is_final_try_full_expression": True,
        "no_surviving_throwing_cleanup_after_assignment": True,
        "release_guarded_only_by_parent_acquired": True,
        "catch_entry_forward_values": dataflow_evidence["catch_entry_values"],
        "unsupported_ast_or_cfg_rejects": True,
    }
    result = {
        "schema": SCHEMA,
        "status": "proved-unreachable",
        "invocation": {
            "invocation_id": f"{TARGET_HELPER}@{_range(target_call)[0]}",
            "helper": TARGET_HELPER,
            "call_begin": _range(target_call)[0],
            "call_end": _range(target_call)[1],
            "call_ast_sha256": sites._sha256_bytes(
                sites._canonical_json(sites._normalized_ast(target_call))
            ),
            "proof_call_ast_sha256": _proof_ast_sha256(target_call),
        },
        "enclosing": {
            "function": "bounded_state_arena::create_handle",
            "function_ast_sha256": _proof_ast_sha256(method),
            "try_ast_sha256": _proof_ast_sha256(try_node),
            "catch_ast_sha256": _proof_ast_sha256(catch_node),
            "guard_ast_sha256": _proof_ast_sha256(guard),
        "assignment_ast_sha256": _proof_ast_sha256(assignment),
        "assignment_if_ast_sha256": _proof_ast_sha256(assignment_if),
        "try_body_ast_sha256": _proof_ast_sha256(try_body),
            "predecessor_call_ast_sha256": _proof_ast_sha256(predecessor_call),
        },
        "ast_normalization": {
            "schema": AST_NORMALIZATION_SCHEMA,
            "configuration_sha256": ast_normalization_configuration_sha256(),
        },
        "cfg": {
            "schema": "clang-debug-dumpcfg-text-v1",
            "normalized_cfg_sha256": sha256_bytes(cfg.encode("utf-8")),
            "assignment_block": assignment_block_name,
            "catch_block": catch_blocks[0][0],
        },
        "exception_model": exception_model,
        "forward_dataflow": dataflow_evidence,
        "predicates": predicates,
    }
    result["proof_payload_sha256"] = sha256_bytes(canonical_json_bytes(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove the frozen R-203 helper call unreachable.",
    )
    parser.add_argument("--repo", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--compile-database", type=Path, required=True)
    arguments = parser.parse_args()
    repo = arguments.repo.resolve()
    source = repo / "native" / "src" / "partial_graph.cpp"
    _, command = sites._compile_entry(arguments.compile_database, source)
    compiler, analysis_arguments = sites._analysis_arguments(command, source)
    result = prove(
        compiler=compiler,
        arguments=analysis_arguments,
        source=source,
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
