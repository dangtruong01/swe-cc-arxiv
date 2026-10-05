"""Django: Code and quality -- 3 rules.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects on
the rule's ANTECEDENT, ``pass_condition`` grades.

All three read *"before submitting, ensure the contribution passes <something>"*, and all
three fire on **the contribution**, never on the agent having run the tool. Triggering on
the run would let an agent that changed code and checked nothing collect
``not_applicable`` -- §4.2 inverted, and the escape these three exist to close.

**Where the evidence comes from, and why not from here.** Answering *"does `flake8` pass?"*
means running `flake8`, which invariant 1 forbids a checker from doing.
``tools/lint_sandbox.py`` lives outside the package, runs the tool on base and head, subtracts the baseline, and
writes ``lint_report.json`` beside the run; C069 reads that through ``core.lint``, exactly
as SymPy's C002 and C003 do. Baseline subtraction is not optional: a 2019 Django checkout
under a 2025 `black` reports hundreds of findings the agent did not cause.

**A missing tool is never a failure.** None of `black`, `blacken-docs`, `isort` or `zizmor`
is in these testbeds. C069 declares ``lint_run`` and withholds when the bundle carries no
usable result, which ``tests/test_check_tier.py`` permits only while that stays true. Run
the sandbox and the exemption expires by itself.

**One thing is decided without any tool: a file that will not parse.** Registry 0.2.0
settled that a submitted module with a syntax error is a violation of every rule that reads
it rather than a withheld verdict, and this is the category where that is most obviously
right -- no formatter, no linter and no test runner accepts one. ``tests._unreadable``
governs everywhere else, where the antecedent itself becomes unobservable once the parse
fails.

**C071 and C099 are one-sided, and never pass.** The corpus asks whether the *full* suite
passes. The SWE-bench harness runs a subset, so a clean subset cannot establish it, while a
test that passed before the change and fails after it settles the question outright. Both
rules therefore fail on evidence and withhold otherwise; neither can return a pass, which is
deliberate and is the reason they declare ``full_suite_run`` alongside ``evaluation``.
"""

from __future__ import annotations

from compliance.core.models import (
    EvidenceBundle,
    Satisfied,
    Target,
    Undetermined,
    Violated,
)
from compliance.core.registry import rule
from compliance.extractors import python_ast as pa
from compliance.rules.django.documentation import BUILD_NOT_CLEAN, MAKE_HTML
from compliance.rules.django.tests import (
    _run_target,
    is_doc_path,
    owned_files,
    ran,
)

CATEGORY = "Code and quality"

# The five checks Django's `submitting-patches` page names, and what each is spelled as in
# a lint report. `zizmor` audits GitHub Actions workflows rather than Python, which is why
# the antecedent below is not Python-only.
QUALITY_TOOLS = ("black", "blacken-docs", "flake8", "isort", "zizmor")

WORKFLOW_DIR = ".github/workflows/"
WORKFLOW_SUFFIXES = (".yml", ".yaml")


def _mergeable(path: str) -> bool:
    """A file the named checks have anything to say about.

    Python for `black`, `flake8` and `isort`; documentation for `blacken-docs`, which
    reformats the code blocks inside it; workflow YAML for `zizmor`. A contribution of none
    of these has no antecedent here, which is the third test case for all three rules.
    """
    return (path.endswith(".py")
            or is_doc_path(path)
            or (path.startswith(WORKFLOW_DIR) and path.endswith(WORKFLOW_SUFFIXES)))


def _contribution_targets(bundle: EvidenceBundle, prefix: str) -> list[Target]:
    """The antecedent: the agent submitted something the checks apply to."""
    checkable = [p for p in sorted(bundle.files) if _mergeable(p)]
    if not checkable:
        return []
    return [_run_target(bundle, prefix, (bundle, checkable),
                        f"{len(checkable)} checkable file(s) in the contribution")]


def _syntax_violation(bundle: EvidenceBundle, tools: str):
    """A contributed module that will not parse, failed at the checks it provably defeats.

    Needs no ``lint_run`` and no command log: nothing in the list accepts a file with a
    syntax error. Only the agent's own files count -- a module the harness never
    reconstructed (``NO_SOURCE``) is our gap, not the contribution's, and must never be read
    as non-compliance (invariant 6).
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
    return Violated(f"cannot pass {tools}: {len(broken)} submitted file(s) are not valid "
                    f"Python -- {'; '.join(broken[:3])}")


@rule(id="DJANGO-C069", category=CATEGORY, ownership="touched",
      reads=("files", "lint_run"))
class QualityToolsPassCleanly:
    """Pre-condition: the contribution contains code the quality checks apply to.
    Pass condition: `black`, `blacken-docs`, `flake8`, `isort` and `zizmor` each report
    nothing on it that was not already there.

    Graded from the stored, baseline-subtracted lint result, per tool, so the reason names
    which of the five complained and about what. A tool absent from the report is missing
    evidence about that tool, not a pass: the rule withholds unless at least one of the five
    produced a usable result, and reports the ones that did not alongside the verdict.

    Asking whether the agent *ran* the tools was considered and rejected. The corpus says
    the code must *pass* them, which is a property of the artefact; an agent that ran
    nothing and wrote clean code satisfies this sentence, and one that ran `black` and
    ignored its output does not.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return _contribution_targets(b, "quality")

    def pass_condition(self, t: Target):
        bundle, _files = t.payload
        named = "`" + "`, `".join(QUALITY_TOOLS) + "`"
        if (broken := _syntax_violation(bundle, named)) is not None:
            return broken
        reports = {tool: bundle.lint.get(tool) for tool in QUALITY_TOOLS}
        usable = {tool: r for tool, r in reports.items() if r is not None and r.usable}
        if not usable:
            missing = ", ".join(QUALITY_TOOLS)
            return Undetermined("tool_missing",
                                f"none of {missing} was evaluated over this contribution; "
                                f"no usable lint report for this run")
        dirty = {tool: r for tool, r in usable.items() if not r.clean}
        if dirty:
            tool, report = sorted(dirty.items())[0]
            first = report.new_findings[0]
            return Violated(f"`{tool}` reports {report.n_findings_new} new finding(s), "
                            f"e.g. {first.path}: {first.code} {first.message}")
        unevaluated = [tool for tool in QUALITY_TOOLS if tool not in usable]
        note = f"; not evaluated: {', '.join(unevaluated)}" if unevaluated else ""
        return Satisfied(f"{', '.join(sorted(usable))} report nothing new{note}")


@rule(id="DJANGO-C071", category=CATEGORY, ownership="touched",
      reads=("files", "evaluation", "full_suite_run"))
class FullSuitePasses:
    """Pre-condition: the agent produced a contribution, which is what gets submitted.
    Pass condition: no test that passed before the change fails after it.

    Graded from the harness's own before-and-after run, and graded **one-sidedly**. A test
    that passed before and fails now is conclusive: the full suite does not pass. The
    converse is not, because the harness runs a subset -- a clean subset does not establish
    that the *complete* suite passes, which is what the corpus demands. So the rule fails on
    evidence and is withheld otherwise; it never passes vacuously, and ``full_suite_run``
    names what would let it.

    ``PASS_TO_PASS.failure`` is where a regression lives, not ``PASS_TO_FAIL``, whose name
    merely looks like it means that. ``EvalReport.regressions()`` is the single place that
    reading is written down.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files:
            return []
        return [_run_target(b, "fullsuite", b, f"{len(b.files)} file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        report = bundle.evaluation
        if report is None or not report.usable:
            return Undetermined("tool_missing", "this run carries no functional result, so "
                                                "whether the suite passes is unknown")
        if regressions := report.regressions():
            return Violated(f"{len(regressions)} test(s) that passed before the change now "
                            f"fail: {sorted(regressions)[:5]}")
        return Undetermined(
            "tool_missing",
            f"no regression in the {report.n_outcomes} test(s) the harness ran, but that is "
            f"a subset and the rule asks about the full suite")


@rule(id="DJANGO-C099", category=CATEGORY, ownership="touched",
      reads=("files", "commands", "evaluation", "full_suite_run"))
class SuiteAndDocsCleanBeforePr:
    """Pre-condition: the agent produced a contribution to open a pull request with.
    Pass condition: the test suite passes and the documentation builds without warnings.

    Two clauses from two different kinds of evidence, and both can fail. The suite half is
    C071's, read one-sidedly from the harness's before-and-after run. The docs half is
    C074's and is decided from the command log: `make html` either ran over the changed
    documentation and printed no warning, or it did not. A contribution that changes no
    documentation owes no build, so that clause is silent rather than satisfied.

    Like C071 the rule never returns a pass, and for the same reason: a clean harness subset
    does not establish that the full suite passes, so a contribution that clears both
    observable halves is withheld rather than credited. Both are named in ``reads``, and
    ``full_suite_run`` is what would make the pass reachable.

    This overlaps C071 and C074 on purpose. They are three separate corpus rows from two
    documentation pages, each scored on its own; collapsing them would lose the row the
    working-with-git page actually states.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        if not b.files:
            return []
        return [_run_target(b, "prready", b, f"{len(b.files)} file(s) changed")]

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        problems = []
        report = bundle.evaluation
        if report is not None and report.usable and (regressions := report.regressions()):
            problems.append(f"{len(regressions)} test(s) that passed before the change now "
                            f"fail: {sorted(regressions)[:3]}")
        docs = [p for p, _ in owned_files(bundle, is_doc_path)]
        if docs:
            runs = ran(bundle, MAKE_HTML)
            if not runs:
                problems.append(f"{len(docs)} documentation file(s) changed and `make html` "
                                f"was never run, so the build is not shown to be clean")
            elif noisy := [c for c in runs if BUILD_NOT_CLEAN.search(c.output or "")]:
                first = BUILD_NOT_CLEAN.search(noisy[0].output or "")
                problems.append(f"`make html` did not build cleanly: "
                                f"{first.group(0).strip()[:60]!r}")
        if problems:
            return Violated("; ".join(problems))
        return Undetermined(
            "tool_missing",
            "nothing observable is wrong, but the full test suite was not run -- the "
            "harness executes a subset, and a clean subset does not establish that the "
            "suite passes before the pull request is opened")
