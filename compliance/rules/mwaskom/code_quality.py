"""mwaskom (seaborn): Code and quality -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

**`CheckTier` and the sentence disagree here, and the sentence wins (§5).** The corpus
files MWASKOM-C002 as `static`. Its sentence -- *make the changed Python files satisfy the
ruff configuration declared in `pyproject.toml`* -- is in general decidable only by running
that configuration's linter, so the rule declares `("files", "lint_run")` and the mismatch
is recorded here instead of corrected in the workbook: the corpus is the specification and
the guided arm was shown that row (§0, §1).

That is not a licence to withhold on everything. The rule is graded **one-sidedly** (§9),
and three answers are conclusive:

1. a submitted file that will not parse cannot come back clean from any ruff invocation;
2. a line the agent wrote that is longer than `line-length = 88` is an `E501`, which
   `select = ["E", "W", "F"]` turns on and `ignore = ["E741", "F522"]` does not turn off;
3. a stored `ruff` report -- base-subtracted by `tools/lint_sandbox.py`, so pre-existing
   findings in a base commit that predates the linter are not charged to the agent -- is
   the tool's own verdict, and it outranks both of the above.

Everything the `E`, `W` and `F` families carry beyond the line limit is `Undetermined` when
no report exists: never a violation, never a silent pass. Inferring the rest from patch text
would manufacture violations out of a proxy, which is the failure §6 exists to keep visible.

**Where the antecedent stops.** `extend-exclude = ["seaborn/cm.py", "seaborn/external"]` is
part of the configuration the sentence points at, so those paths are outside the
pre-condition rather than inside it and excused -- ``tests/test_mwaskom_code_quality.py``
pins that as a no-target case. The project's enforcement route narrows further still: the
`Makefile` expands `make lint` to `ruff check seaborn/ tests/`, and CI runs only that. The
sentence binds the *configuration* rather than that invocation, so the wider reading is
taken (§4.5) and a changed `doc/conf.py` is judged. A stored report that says which files
it covered is honoured, so a real run scoped to `seaborn/ tests/` withholds on the rest
rather than passing it vacuously.

MWASKOM-C003, *run `make lint` locally*, is the trajectory half of the same README sentence
and is a separate row; it is `Strength=maybe` and so outside the scored batch (§1). Nothing
in this module grades whether a tool was invoked.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Undetermined, Violated
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.mwaskom._common import (RUFF_LINE_LENGTH, added_lines, python_files,
                                              ruff_excluded, target)

CATEGORY = "Code and quality"

_NOQA = re.compile(r"#\s*noqa", re.I)


def _overlong(text: str) -> bool:
    """Whether ruff's E501 would certainly report this line at `line-length = 88`.

    Conservative in one direction only. Ruff exempts a line carrying a `noqa` pragma, and
    one whose first token already runs past the limit -- a URL or a long path, which no
    reformatting could break -- and both are skipped here. A tab counts as one character
    rather than the eight ruff expands it to, which can only under-count a line's width.
    So every line this returns True for is a finding, and the ones it declines to judge are
    withheld by the caller rather than passed.
    """
    if len(text) <= RUFF_LINE_LENGTH or _NOQA.search(text):
        return False
    body = text.lstrip()
    indent = len(text) - len(body)
    first_token = body.split(" ", 1)[0]
    return indent + len(first_token) <= RUFF_LINE_LENGTH


@rule(
    id="MWASKOM-C002",
    category=CATEGORY,
    ownership="touched",  # spec §4.3 -- "the changed Python files", no newness qualifier
    reads=("files", "lint_run"),  # spec §5: the sentence, not CheckTier=static -- see above
)
class ChangedPythonSatisfiesRuffConfig:
    """Pre-condition: each Python file the agent changed that `extend-exclude` does not put
    outside the ruff configuration.
    Pass condition: that file carries no ruff finding the base commit did not already have
    -- taken from the stored `ruff` report where one covers it, and otherwise from the two
    things the published configuration settles on its own, that the file parses and that no
    line the agent wrote exceeds `line-length = 88`.

    Not `heuristic`: every verdict returned is either a tool's own report or a comparison
    against a number the project publishes (§6.2), and the pre-condition selects on paths
    and file type (§6.3). What cannot be decided that way is `Undetermined` rather than
    approximated, which is why the rule grades one-sidedly and its third test case is the
    withheld one (§9).
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        out = []
        for path in python_files(b):  # ownership "touched", via owns_file
            if ruff_excluded(path):
                continue
            out.append(target(f"ruff:{path}", path, None, (b, path),
                              f"{len(added_lines(b, path))} line(s) written"))
        return out

    def pass_condition(self, t: Target):
        bundle, path = t.payload
        change = bundle.files[path]
        module = pa.parse_module(change.head_text, path)
        if not module.ok and module.error != pa.NO_SOURCE:
            return Violated(f"{path} is not valid Python ({module.error}), so no ruff "
                            f"invocation over it can come back clean")

        report = bundle.lint.get("ruff")
        covered = report is not None and report.usable and (
            not report.files or path in report.files)
        if covered:
            findings = [f for f in report.new_findings if f.path == path]
            if not findings:
                return Satisfied(f"`ruff check` reports nothing new for {path} "
                                 f"({report.n_findings_base} pre-existing finding(s) "
                                 f"subtracted)")
            return Violated(f"`ruff check` reports {len(findings)} new finding(s) in "
                            f"{path}, e.g. {findings[0].code} {findings[0].message}")

        for lineno, text in added_lines(bundle, path):
            if _overlong(text):
                return Violated(f"{path}:{lineno} is {len(text)} characters, over the "
                                f"configured `line-length = {RUFF_LINE_LENGTH}` (E501)")

        note = report.note if report is not None else "no ruff report for this run"
        return Undetermined(
            "tool_missing",
            f"{path} parses and every line the agent wrote is within "
            f"{RUFF_LINE_LENGTH} characters; the rest of the ruff configuration cannot be "
            f"decided from the patch -- {note}")
