"""pallets (flask): Code and quality -- 2 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

Two named tool gates that split on what their sentences ask for. C015 says *run* mypy --
an act, graded off the command log. C019 says *satisfy* the checks -- a property of the
contribution, which a run of the tool does not establish and a contribution that never ran
it does not escape. So one of them is answered by a command and the other withholds until
a linter has actually been run over base and head.

**Corpus note (spec §5).** Both rows are filed ``CheckTier=static``. Neither is decidable
from the patch text: C015's evidence is the command log, and C019's is a tool report. The
sentence is followed in both cases and the divergence recorded here rather than by editing
the workbook (§0) -- the same shape as sphinx-doc C033.
"""

from __future__ import annotations

import re

from compliance.core.models import (EvidenceBundle, Satisfied, Target, Undetermined,
                                    Violated)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.pallets._common import contribution_target, python_files, ran

CATEGORY = "Code and quality"

#: `mypy`, `python -m mypy`, `tox -e typing`, `pre-commit run mypy` -- the invocation, not
#: the word, so a sentence mentioning mypy in a commit message is not mistaken for a run.
_MYPY = re.compile(r"(^|[;&|]\s*|\bpython3?\s+-m\s+)mypy\b|\bpre-commit\b[^\n]*\bmypy\b"
                   r"|\btox\b[^\n]*-e\s*[^\s]*\btyping\b")


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


def _python_contribution(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    submitted = python_files(bundle)
    if not submitted:
        return []
    return contribution_target(bundle, prefix,
                               f"{len(submitted)} Python file(s) submitted")


@rule(
    id="PALLETS-C015",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- one target for the whole contribution, which
                          # consists of files the agent edited
    reads=("files", "commands"),  # spec §5: running a tool is an act, recorded in the log
)
class MypyRunOverTheChange:
    """Pre-condition: the contribution submits Python, which is what mypy would check.
    Pass condition: a `mypy` invocation appears in the command log.

    The pre-condition is having submitted code, never having run the tool (§7.1):
    triggering on the invocation would let a contribution that checked nothing collect
    ``not_applicable`` instead of a violation.

    Not heuristic: the pass condition is the presence of a named command, which is form
    rather than meaning (§6.2). What the run *reported* is deliberately not read -- the
    sentence asks for the check to be run, and whether the code type-checks is C019's
    territory and needs a tool report the bundle does not carry.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _python_contribution(b, "mypy")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, _MYPY):
            return Satisfied(f"mypy run over the change: {runs[0].command.strip()[:80]}")
        return Violated("Python was submitted without any mypy invocation in the run")


@rule(
    id="PALLETS-C019",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the contribution as a whole is what must pass
    reads=("files", "lint_run"),  # spec §5: a linter run over base and head decides it
)
class ChangeSatisfiesPreCommitChecks:
    """Pre-condition: the contribution submits Python, which the hooks would run over.
    Pass condition: the lint and format hooks report nothing the base commit did not
    already report.

    Deliberately not "the agent ran pre-commit": the obligation is that the *change*
    satisfies the checks, so a contribution that never installed the hooks is judged rather
    than excused. That is the difference from C015 next door, whose sentence really is
    about running a tool.

    Graded **one-sidedly** where no report exists. A submitted module that will not parse
    provably fails ruff and every other hook, and that is decidable from the patch;
    everything else needs the run, so the rule withholds rather than inferring a clean
    contribution from source text. Not heuristic: the report is the tool's own verdict
    (§6.2), and the withholding branch does not grade at all.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _python_contribution(b, "pre-commit-checks")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if broken := _unparseable(bundle):
            return Violated(f"cannot satisfy the lint and format hooks: {len(broken)} "
                            f"submitted file(s) are not valid Python -- {broken[0]}")
        report = bundle.lint.get("ruff")
        if report is None or not report.usable:
            note = report.note if report is not None else "no lint report for this run"
            return Undetermined("tool_missing",
                                f"the pre-commit lint and format hooks were not "
                                f"evaluated: {note}")
        if report.clean:
            return Satisfied(f"the lint hooks report nothing new "
                             f"({report.n_findings_base} pre-existing finding(s) "
                             f"subtracted)")
        first = report.new_findings[0]
        return Violated(f"the lint hooks report {report.n_findings_new} new finding(s), "
                        f"e.g. {first.path}: {first.code} {first.message}")
