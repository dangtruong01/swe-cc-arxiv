"""pylint-dev: Code and quality -- 3 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All three come from `.github/copilot-instructions.md` and all three are about something the
agent *did*, so all three read the command log (spec §5, `CheckTier=trajectory`). None of
their pre-conditions fires on the tool being run: firing on the invocation would let a
contribution that ran nothing collect ``not_applicable`` instead of a violation (§7.1).

C094 and C097 both name `pylint`, and they are kept apart on the object of the run: C094 is
the standard run over the *changed files* with two named flags, C097 is a run over *sample
code* that exercises the change. A single `pylint --rcfile=pylintrc --fail-on=I` over a
changed module satisfies C094 and not C097, which is the distinction the two sentences draw.
"""

from __future__ import annotations

import re

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.pylint_dev._common import (contribution_target, python_files, ran,
                                                 target)

CATEGORY = "Code and quality"

_PRE_COMMIT_ALL = re.compile(r"\bpre-commit\b[^\n|;&]*\brun\b[^\n|;&]*(-a\b|--all-files\b)")
_GIT_COMMIT = re.compile(r"\bgit\s+(?:-\S+\s+)*commit\b")
_PYLINT = re.compile(r"(^|[\s;|&(])pylint\b")
_RCFILE = re.compile(r"--rcfile[= ]\s*\S*pylintrc\b")
_FAIL_ON_I = re.compile(r"--fail-on[= ]\s*I\b")


def _pylint_arguments(command: str) -> list[str]:
    """Path-like operands of a `pylint` invocation, options and their values removed."""
    tokens = command.replace(";", " ").replace("&&", " ").split()
    if "pylint" not in [t.split("/")[-1] for t in tokens]:
        return []
    index = next(i for i, t in enumerate(tokens) if t.split("/")[-1] == "pylint")
    out = []
    for token in tokens[index + 1:]:
        if token.startswith("-") or "=" in token:
            continue
        if token in {"|", ">", "<", "&&", ";"}:
            break
        out.append(token)
    return out


@rule(
    id="PYLINT-DEV-C093",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- a whole-contribution rule about the checkout
                          # being worked in, not about one artefact
    reads=("commits", "commands"),  # spec §5: the commit fixes the deadline, the log
                                    # records the act
    heuristic=True,
)
class PreCommitRunAllBeforeCommitting:
    """Pre-condition: the agent made at least one commit.
    Pass condition: a `pre-commit run -a` invocation appears in the command log before the
    first `git commit` in it.

    Heuristic on the **pass condition** (§6.2). *Before committing* is read against the
    first `git commit` in the command log, because commits carry no timestamp that lines up
    with command indices; when the log records no `git commit` at all -- the harness having
    committed on the agent's behalf -- the ordering cannot be established and the check
    falls back to whether the hooks were ever run over the whole tree. Sound in the failing
    direction, weaker in the passing one.

    Corpus: Run pre-commit run -a before committing.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.commits:
            return []
        return [target(f"pre-commit-all:{b.instance_id}", None, None, b,
                       f"{len(b.commits)} commit(s)", source="commit")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        runs = ran(bundle, _PRE_COMMIT_ALL)
        if not runs:
            return Violated("committed without ever running `pre-commit run -a`")
        first_commit = next((c.index for c in bundle.commands
                             if _GIT_COMMIT.search(c.command)), None)
        if first_commit is None:
            return Satisfied(f"`pre-commit run -a` was run "
                             f"({runs[0].command.strip()[:60]}); the log records no "
                             f"`git commit` to order it against")
        if runs[0].index < first_commit:
            return Satisfied(f"`pre-commit run -a` at step {runs[0].index}, before the "
                             f"first commit at step {first_commit}")
        return Violated(f"`pre-commit run -a` was only run at step {runs[0].index}, after "
                        f"the first `git commit` at step {first_commit}")


@rule(
    id="PYLINT-DEV-C094",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the antecedent is the changed code
    reads=("files", "commands"),  # spec §5: the files say the rule fired, the log says
                                  # whether the run happened
)
class ChangedFilesLintedWithTheStandardInvocation:
    """Pre-condition: the contribution changes Python files.
    Pass condition: a `pylint` invocation naming both `--rcfile=pylintrc` and
    `--fail-on=I` appears in the command log.

    Not heuristic: the sentence gives the invocation verbatim, the same one the project's
    pre-commit hook and CI job pin, so the pass condition is the presence of something the
    rule names exactly (§6.2). What it does not check is that every changed file was passed
    to it; the sentence's `path/to/your/changes.py` is a placeholder, and treating it as a
    per-file obligation would grade a form the docs do not state.

    Corpus: Lint changed files with pylint --rcfile=pylintrc --fail-on=I.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = python_files(b)
        if not changed:
            return []
        return [target(f"pylint-standard-run:{b.instance_id}", None, None, b,
                       f"{len(changed)} Python file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        for command in ran(bundle, _PYLINT):
            if _RCFILE.search(command.command) and _FAIL_ON_I.search(command.command):
                return Satisfied(f"standard run: {command.command.strip()[:80]}")
        return Violated("no `pylint --rcfile=pylintrc --fail-on=I` run over the changed "
                        "files")


@rule(
    id="PYLINT-DEV-C097",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- the antecedent is the change being validated
    reads=("files", "commands"),  # spec §5
    heuristic=True,
)
class ChangeValidatedOnSampleCode:
    """Pre-condition: the contribution changes Python files.
    Pass condition: a `pylint` invocation names a path that is not one of the changed
    source files -- sample code the change is exercised on.

    Heuristic on the **pass condition** (§6.2). *Sample code that exercises it* is a
    judgement about what the sample contains, and the patch cannot make it: the proxy is
    that the run's object is not itself part of the contribution. A run over a functional
    test file the change added counts, because such a file is exactly the sample pylint is
    pointed at; a run over only the modified checker does not, and that is the case C094
    already grades.

    Corpus: Validate a change by running pylint over sample code that exercises it.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        changed = python_files(b)
        if not changed:
            return []
        return [target(f"pylint-sample-run:{b.instance_id}", None, None, b,
                       f"{len(changed)} Python file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        source = {p for p in python_files(bundle) if not p.startswith("tests")}
        seen = False
        for command in ran(bundle, _PYLINT):
            for argument in _pylint_arguments(command.command):
                seen = True
                if argument.lstrip("./") not in source:
                    return Satisfied(f"pylint run over `{argument}`, which is not one of "
                                     f"the modified source files")
        if not seen:
            return Violated("the change was never validated by running pylint over any "
                            "code")
        return Violated("pylint was only ever run over the modified source files, never "
                        "over sample code exercising the change")
