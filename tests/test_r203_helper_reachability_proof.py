from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from experiments import r203_dynamic_charge_sites as sites
from experiments.r203_helper_reachability_proof import prove


REPO = Path(__file__).parents[1]
SOURCE = REPO / "native" / "src" / "partial_graph.cpp"
COMPILE_DATABASE = REPO / "build" / "r203-ast-clang22" / "compile_commands.json"


def _compiler_arguments() -> tuple[str, list[str]]:
    _, command = sites._compile_entry(COMPILE_DATABASE, SOURCE)
    return sites._analysis_arguments(command, SOURCE)


def test_frozen_helper_unreachable_proof_passes() -> None:
    compiler, arguments = _compiler_arguments()
    result = prove(
        compiler=compiler,
        arguments=arguments,
        source=SOURCE,
    )
    assert result["status"] == "proved-unreachable"
    assert result["invocation"]["invocation_id"] == (
        "bounded_state_arena::release@134436"
    )
    assert result["predicates"]["catch_entry_forward_values"] == ["false"]


@pytest.mark.parametrize(
    ("old", "new", "expected_error"),
    [
        (
            """                add_child_reference(value.parent, value);
                parent_acquired = true;""",
            """                parent_acquired = true;
                add_child_reference(value.parent, value);""",
            "assignment is not the final full-expression immediately after",
        ),
        (
            """                parent_acquired = true;
            }""",
            """                parent_acquired = true;
                work_->charge(0U, RESONITH_PARTIAL_WORK_REFERENCE);
            }""",
            "assignment is not the final full-expression immediately after",
        ),
        (
            """                parent_acquired = true;
            }
        } catch (...) {""",
            """                parent_acquired = true;
            }
            work_->charge(0U, RESONITH_PARTIAL_WORK_REFERENCE);
        } catch (...) {""",
            "target if is not the final statement in the try",
        ),
        (
            """                parent_acquired = true;
            }""",
            """                parent_acquired = true;
                parent_acquired = false;
            }""",
            "proof variable is aliased, captured, or referenced extra",
        ),
        (
            """                parent_acquired = true;
            }""",
            """                parent_acquired = true;
                static_cast<void>(&parent_acquired);
            }""",
            "proof variable is aliased, captured, or referenced extra",
        ),
        (
            "            if (parent_acquired) {\n"
            "                if (!release(value.parent)) {",
            "            if (parent_acquired && owner_release_reserved) {\n"
            "                if (!release(value.parent)) {",
            "release is not guarded only by parent_acquired",
        ),
        (
            "            if (parent_acquired) {\n"
            "                if (!release(value.parent)) {",
            "            if (!parent_acquired) {\n"
            "                if (!release(value.parent)) {",
            "release is not guarded only by parent_acquired",
        ),
        (
            "            if (parent_acquired) {\n"
            "                if (!release(value.parent)) {",
            "            if (parent_acquired == false) {\n"
            "                if (!release(value.parent)) {",
            "release is not guarded only by parent_acquired",
        ),
        (
            "            if (parent_acquired) {\n"
            "                if (!release(value.parent)) {",
            "            if (parent_acquired || true) {\n"
            "                if (!release(value.parent)) {",
            "release is not guarded only by parent_acquired",
        ),
    ],
    ids=(
        "assignment-before-predecessor",
        "throwing-call-after-assignment",
        "post-if-throwing-call",
        "second-write",
        "address-escape",
        "changed-guard",
        "negated-guard",
        "false-equality-guard",
        "always-true-guard",
    ),
)
def test_temporary_source_adversarial_changes_fail_closed(
    tmp_path: Path,
    old: str,
    new: str,
    expected_error: str,
) -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    assert source_text.count(old) == 1
    temporary_source = tmp_path / "partial_graph.cpp"
    temporary_source.write_text(source_text.replace(old, new), encoding="utf-8")
    shutil.copyfile(
        REPO / "native" / "src" / "partial_graph_stage_budget.hpp",
        tmp_path / "partial_graph_stage_budget.hpp",
    )
    compiler, arguments = _compiler_arguments()
    with pytest.raises(RuntimeError, match=expected_error):
        prove(
            compiler=compiler,
            arguments=arguments,
            source=temporary_source,
        )
