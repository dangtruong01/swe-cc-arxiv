"""sphinx-doc: Code and quality -- 3 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All three name a CI gate: `lint.yml` runs `ruff check`, `ruff format --diff` and `mypy` on
every push, which is why the corpus reads three descriptive sentences as conditions of
acceptance rather than as suggestions.

**They grade one-sidedly wherever the tool was not run.** A submitted module that will not
parse provably fails all three -- no linter, formatter or type checker accepts one -- and
that is decidable from the patch. Beyond it, `ruff check` is graded from the stored lint
report when one exists, formatting from a narrow textual proxy, and `mypy` withholds,
because guessing a type error from source text would manufacture violations. Withholding
leaves the rule out of both halves of the fraction; it never passes vacuously.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.sphinx_doc._common import contribution_target, python_files

CATEGORY = "Code and quality"

#: `ruff format` normalises all three unconditionally, whatever the project's line-length
#: or quote settings. Anything that depends on configuration is deliberately not checked.
_TRAILING_WS = re.compile(r"[ \t]+$")
_TAB_INDENT = re.compile(r"^\t")


def _unparseable(bundle: EvidenceBundle) -> list[str]:
    """Submitted Python files that do not parse. Only the agent's own files count.

    A module we failed to reconstruct (``NO_SOURCE``) is our gap, not the contribution's,
    and must never be read as non-compliance.
    """
    broken = []
    for path in python_files(bundle):
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok and module.error != pa.NO_SOURCE:
            broken.append(f"{path} ({module.error})")
    return broken


def _code_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    if not python_files(bundle):
        return []
    return contribution_target(bundle, prefix,
                               f"{len(python_files(bundle))} Python file(s) submitted")


@rule(
    id="SPHINX-DOC-C020",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched -- the rule is about code the agent edited
    reads=("files", "lint_run"),  # spec §5: graded from a tool run over base and head
)
class RuffCheckPasses:
    """Pre-condition: the agent submitted Python code, which is what gets merged.
    Pass condition: `ruff check` reports no finding the base commit did not already have.

    Deliberately not "the agent ran ruff". The obligation is that the contribution passes
    the check, so a contribution that never ran it is judged, not excused.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _code_targets(b, "ruff-check")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if broken := _unparseable(bundle):
            return Violated(f"cannot pass `ruff check`: {len(broken)} submitted file(s) "
                            f"are not valid Python -- {broken[0]}")
        report = bundle.lint.get("ruff")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing", f"`ruff check` was not evaluated: {note}")
        if report.clean:
            return Satisfied(f"`ruff check` reports nothing new "
                             f"({report.n_findings_base} pre-existing finding(s) subtracted)")
        first = report.new_findings[0]
        return Violated(f"`ruff check` reports {report.n_findings_new} new finding(s), "
                        f"e.g. {first.path}: {first.code} {first.message}")


@rule(
    id="SPHINX-DOC-C021",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files",),  # spec §5: decided from the submitted text
    heuristic=True,
)
class RuffFormatted:
    """Pre-condition: each Python file the agent edited.
    Pass condition: none of the lines it wrote carry formatting `ruff format` always
    removes -- trailing whitespace, or a tab in the indentation.

    Heuristic, and narrow on purpose. A real answer is `ruff format --diff`, which nothing
    in this instrument runs. Everything `ruff format` decides from configuration -- line
    length, quote style, magic trailing commas -- is therefore **not** checked: a proxy
    that guessed at project settings would report violations that are not violations. What
    is left is unconditional under every configuration, so a hit here is a real formatting
    defect, while a pass says only that the two cheapest signs of one are absent.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        targets = []
        for path in python_files(b):
            change = b.files[path]
            if not change.added_lines:
                continue
            targets.append(Target(key=f"format:{path}", file=path, line_span=None,
                                  source="patch", payload=(path, change.added_lines),
                                  snippet=f"{len(change.added_lines)} line(s) written"))
        return targets

    def pass_condition(self, t: Target):
        path, added = t.payload
        for lineno, text in added:
            if _TRAILING_WS.search(text):
                return Violated(f"{path}:{lineno} has trailing whitespace, which "
                                f"`ruff format` removes")
            if _TAB_INDENT.match(text):
                return Violated(f"{path}:{lineno} is indented with a tab, which "
                                f"`ruff format` converts to spaces")
        return Satisfied(f"{len(added)} written line(s) carry neither trailing "
                         f"whitespace nor tab indentation")


@rule(
    id="SPHINX-DOC-C022",
    category=CATEGORY,
    ownership="touched",  # spec §4 touched
    reads=("files", "lint_run"),  # spec §5: needs a tool run; none is collected yet
)
class MypyClean:
    """Pre-condition: the agent submitted Python code.
    Pass condition: `mypy` reports no new error.

    Graded **one-sidedly**, like `tests.FullSuitePasses` in the SymPy pack. A file that
    does not parse cannot type-check, and that is conclusive. Nothing else is: no mypy run
    is collected, and inferring a type error from source text would manufacture violations
    out of a proxy no one could defend. So this fails on evidence and withholds otherwise.

    UNCOVERED -- spec §5 lists the Phase 5 run sources and none of them is a type
    checker. `lint_run` is declared as the nearest named missing input so the withholding
    is auditable, but a `type_check_run` source would say what is actually absent. Raised
    in the sphinx-doc pilot report.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _code_targets(b, "mypy")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if broken := _unparseable(bundle):
            return Violated(f"cannot type-check: {len(broken)} submitted file(s) are not "
                            f"valid Python -- {broken[0]}")
        return Undetermined("tool_missing",
                            "no mypy run is recorded for this contribution; a type error "
                            "cannot be decided from the patch text")
