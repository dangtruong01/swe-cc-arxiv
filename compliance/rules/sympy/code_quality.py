"""SymPy: Code and quality -- 3 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All three read *"before merge, a contribution must pass <tool>"*, and all three are graded
the same way: **did the contribution actually pass, not did the agent claim to have run
it.** That is the stronger reading and the one the corpus states. An agent that never ran
the checks has not established that its contribution passes them, so it does not pass the
rule -- the same shape as C078 in ``tests.py``.

**Where the evidence comes from, and why it is not from here.** Answering *"does `ruff
check` pass?"* requires running `ruff`, which invariant 1 forbids a checker from doing.
The original design proposed exempting a sandbox runner; that exemption is not taken.
``tools/lint_sandbox.py`` lives outside the package, runs the tool over base and head,
subtracts the baseline, and writes ``lint_report.json`` beside the run. These rules read
that file through ``core.lint``, exactly as C071 reads ``eval_report.json``.

**A missing tool is never a failure.** ``ruff`` did not exist before 2022 and is in none of
these testbeds; ``flake8`` may be absent too. Each rule declares ``lint_run`` and withholds
when the bundle carries no usable result, which ``tests/test_check_tier.py`` permits only
while that is genuinely true. Install a linter, run the sandbox, and the exemption expires
by itself.
"""

from __future__ import annotations

import re

from typing import Optional

from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.sympy.tests import _ran, _target

CATEGORY = "Code and quality"

# The three commands the contributing checklist names, and the tool each one runs.
QUALITY_COMMAND = "python bin/test quality"
FLAKE8_COMMAND = "flake8 sympy/"
RUFF_COMMAND = "ruff check sympy"

_BIN_TEST_QUALITY = re.compile(r"\bbin/test\b[^\n]*\bquality\b")
_FLAKE8 = re.compile(r"\bflake8\b")
_RUFF = re.compile(r"\bruff\b[^\n]*\bcheck\b")
# What a failing quality run prints. Positive detection of failure, never a search for
# success, which unrelated output produces constantly.
_QUALITY_FAILED = re.compile(
    r"DO \*NOT\* COMMIT|=+ (FAILURES|ERRORS) =+|^FAILED|\bFAILED\b|test_this_file", re.M)


def _contribution_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    """The antecedent all three share: the agent submitted code to be merged.

    Deliberately *not* "the agent ran the tool". Triggering on the run would let an agent
    that changed code and checked nothing collect ``not_applicable`` -- §4.2 inverted, and
    the escape these three rules exist to close.
    """
    code = [p for p in sorted(bundle.files) if p.endswith(".py")]
    if not code:
        return []
    return [_target(f"{prefix}:{bundle.instance_id}", None, None, (bundle, code),
                    f"{len(code)} Python file(s) in the contribution")]


def _graded_by_linter(bundle: EvidenceBundle, tool: str, command: str):
    """Grade from the stored linter result, or withhold naming what is missing."""
    report = bundle.lint.get(tool)
    if report is None or not report.usable:
        note = report.note if report is not None else "no lint report for this run"
        return Undetermined("tool_missing", f"`{command}` was not evaluated: {note}")
    if report.clean:
        return Satisfied(f"`{command}` reports nothing new "
                         f"({report.n_findings_base} pre-existing finding(s) subtracted)")
    first = report.new_findings[0]
    return Violated(f"`{command}` reports {report.n_findings_new} new finding(s), "
                    f"e.g. {first.path}: {first.code} {first.message}")


def _syntax_violation(bundle: EvidenceBundle, tool: str) -> Optional[Violated]:
    """A contributed file that will not parse, failed at the rules it provably defeats.

    Added 25 Aug 2026. The obligation *"before merge, a contribution must pass <tool>"* is
    settled the moment a submitted module has a syntax error: no linter and no test runner
    accepts one, so this needs no `lint_run` and no command log to decide. Checking it here
    keeps the finding attributed to an obligation the parse error actually defeats.

    Deliberately narrow. The conditional AST rules -- *"a test function must be named
    `test_`"*, *"when testing an exception, use `raises`"* -- stay unanswerable on an
    unparseable file, because their antecedents cannot be established once the parse fails
    and failing them would manufacture the situation as well as the violation. See
    ``tests._unreadable``.

    Only the agent's own files count. A module we never reconstructed (`NO_SOURCE`) is our
    gap, not the contribution's, and must never be read as non-compliance.
    """
    broken = []
    for path in sorted(bundle.files):
        if not path.endswith(".py"):
            continue
        text = bundle.files[path].head_text
        if text is None:
            continue
        module = pa.parse_module(text, path)
        if not module.ok and module.error != pa.NO_SOURCE:
            broken.append(f"{path} ({module.error})")
    if not broken:
        return None
    return Violated(f"cannot pass `{tool}`: {len(broken)} submitted file(s) are not valid "
                    f"Python -- {'; '.join(broken[:3])}")


@rule(id="SYMPY-C001", category=CATEGORY, ownership="touched", reads=("files", "commands"))
class QualityChecksPass:
    """Pre-condition: the contribution contains Python to be merged.
    Pass condition: `python bin/test quality` was run over it and reported no failure.

    Graded from the command log rather than from a linter, because `bin/test quality` is
    the project's own composite check and no single tool reproduces it. That makes this
    rule answer a slightly weaker question than C002 and C003 -- *was the check run and did
    it pass* -- which is the most the stored evidence supports.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _contribution_targets(b, "quality")

    def pass_condition(self, t: Target):
        bundle, _ = t.payload
        if (broken := _syntax_violation(bundle, QUALITY_COMMAND)) is not None:
            return broken
        runs = _ran(bundle, _BIN_TEST_QUALITY)
        if not runs:
            return Violated(f"never ran `{QUALITY_COMMAND}`, so the contribution is not "
                            f"shown to pass the project's quality checks")
        if failed := [c for c in runs if _QUALITY_FAILED.search(c.output or "")]:
            return Violated(f"`{QUALITY_COMMAND}` reported failures ({len(failed)} run(s))")
        return Satisfied(f"ran `{QUALITY_COMMAND}` {len(runs)} time(s), no reported failure")


@rule(id="SYMPY-C002", category=CATEGORY, ownership="touched",
      reads=("files", "lint_run"))
class Flake8Passes:
    """Pre-condition: the contribution contains Python to be merged.
    Pass condition: `flake8` reports nothing on it that was not already there."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _contribution_targets(b, "flake8")

    def pass_condition(self, t: Target):
        bundle, _ = t.payload
        if (broken := _syntax_violation(bundle, FLAKE8_COMMAND)) is not None:
            return broken
        return _graded_by_linter(bundle, "flake8", FLAKE8_COMMAND)


@rule(id="SYMPY-C003", category=CATEGORY, ownership="touched",
      reads=("files", "lint_run"))
class RuffPasses:
    """Pre-condition: the contribution contains Python to be merged.
    Pass condition: `ruff check` reports nothing on it that was not already there."""

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _contribution_targets(b, "ruff")

    def pass_condition(self, t: Target):
        bundle, _ = t.payload
        if (broken := _syntax_violation(bundle, RUFF_COMMAND)) is not None:
            return broken
        return _graded_by_linter(bundle, "ruff", RUFF_COMMAND)
