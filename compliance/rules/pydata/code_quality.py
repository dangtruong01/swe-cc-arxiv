"""pydata (xarray): Code and quality -- 4 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Three tool gates and one command. The gates grade one-sidedly wherever the tool was not
run: a submitted module that will not parse provably fails all three, and that is decidable
from the patch; beyond it, `ruff check` is graded from the stored lint report when one
exists, formatting from a narrow textual proxy, and `mypy` withholds.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pydata._common import (added_lines, contribution_target,
                                             python_files, ran, target)

CATEGORY = "Code and quality"

_TRAILING_WS = re.compile(r"[ \t]+$")
_TAB_INDENT = re.compile(r"^\t")
_PRE_COMMIT_ALL = re.compile(r"\bpre-commit\b[^\n]*\brun\b[^\n]*(--all-files|-a)\b")


def _unparseable(bundle: EvidenceBundle) -> list[str]:
    """Submitted Python files that do not parse. Only the agent's own files count."""
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
    id="PYDATA-C037",
    category=CATEGORY,
    ownership="touched",  # spec §4.1 -- lines inside files that already existed
    reads=("files",),  # spec §5: decided from the submitted text
    heuristic=True,
)
class RuffFormatReportsNoChanges:
    """Pre-condition: each Python file the agent edited that gained a line.
    Pass condition: none of the lines it wrote carries formatting `ruff format` always
    removes -- trailing whitespace, or a tab in the indentation.

    Heuristic on the **pass condition** (§6.2), and narrow on purpose. A real answer is
    `ruff format --diff`, which nothing in this instrument runs. Everything the formatter
    decides from configuration -- line length, quote style, magic trailing commas -- is
    deliberately not checked, because a proxy that guessed at project settings would report
    violations that are not violations. What is left holds under every configuration.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):
            written = added_lines(b, path)
            if written:
                out.append(target(f"format:{path}", path, None, (path, written),
                                  f"{len(written)} line(s) written"))
        return out

    def pass_condition(self, t: Target):
        path, written = t.payload
        for lineno, text in written:
            if _TRAILING_WS.search(text):
                return Violated(f"{path}:{lineno} has trailing whitespace, which "
                                f"`ruff format` removes")
            if _TAB_INDENT.match(text):
                return Violated(f"{path}:{lineno} is indented with a tab, which "
                                f"`ruff format` converts to spaces")
        return Satisfied(f"{len(written)} written line(s) carry neither trailing "
                         f"whitespace nor tab indentation")


@rule(
    id="PYDATA-C038",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files", "lint_run"),  # spec §5: graded from a tool run over base and head
)
class NoRuffLintViolations:
    """Pre-condition: the agent submitted Python code, which is what gets merged.
    Pass condition: `ruff check` reports no finding the base commit did not already have.

    Deliberately not "the agent ran ruff": the obligation is that the contribution is
    clean, so one that never ran the tool is judged rather than excused.
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
    id="PYDATA-C040",
    category=CATEGORY,
    ownership="touched",  # spec §4.1
    reads=("files", "lint_run"),  # spec §5: needs a tool run; none is collected yet
)
class TypeHintsPassMypy:
    """Pre-condition: the agent submitted Python code.
    Pass condition: `mypy` reports no new error.

    Graded **one-sidedly**. A file that does not parse cannot type-check, and that is
    conclusive. Nothing else is: no mypy run is collected, and inferring a type error from
    source text would manufacture violations out of a proxy no one could defend. So this
    fails on evidence and withholds otherwise, never passing vacuously.

    `lint_run` is declared as the nearest named missing input, the same compromise
    sphinx-doc's C022 makes; a `type_check_run` source would say what is actually absent.
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


@rule(
    id="PYDATA-C091",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running is an act
)
class PreCommitRunOverAllFiles:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a `pre-commit run --all-files` invocation appears in the command log.

    The guide names the whole-repository form specifically, so a staged-files run does not
    satisfy it. The second half of the sentence -- *and commit any changes it makes* -- is
    not separately checkable: a hook's edits are indistinguishable in the diff from the
    agent's own, which is worth saying because the pass condition is narrower than the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "pre-commit-all")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _PRE_COMMIT_ALL):
            return Satisfied(f"pre-commit run over all files: "
                             f"{runs[0].command.strip()[:80]}")
        return Violated("`pre-commit run --all-files` never ran")
