"""Three cases per rule (spec §9): satisfied, violated, and an input where the
pre-condition finds nothing.

C019 gets the standard triple plus a fourth case. It declares ``lint_run``, which no
stored run collects yet -- but a report is a field of the bundle, so both graded branches
are reachable from a constructed one and are exercised here rather than left dead. The
fourth case is the withhold: with no report at all the row must be ``not_applicable`` with
a non-``ok`` status, never a silent pass, and the test asserts exactly that.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

VALID = make_file("src/flask/app.py", [(1, "def create_app():")],
                  head_text="def create_app():\n    return None\n")
BROKEN = make_file("src/flask/app.py", [(1, "def create_app(:")],
                   head_text="def create_app(:\n    return None\n")
DOC = make_file("docs/quickstart.rst", [(9, "New prose.")])


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C015 run mypy over the change -----------------------------------------------------


def test_c015_passes_when_mypy_was_run(corpus):
    bundle = make_bundle(files=[VALID], commands=["python -m mypy src/flask"])
    assert verdict("PALLETS-C015", bundle, corpus).verdict == "pass"


def test_c015_fails_when_python_was_submitted_without_running_mypy(corpus):
    bundle = make_bundle(files=[VALID], commands=["python -m pytest tests/"])
    row = verdict("PALLETS-C015", bundle, corpus)
    assert row.verdict == "fail" and "mypy" in row.notes


def test_c015_finds_no_target_for_a_documentation_only_contribution(corpus):
    """The pre-condition is submitting Python, not running the tool (§7.1)."""
    row = verdict("PALLETS-C015", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C019 the change satisfies the pre-commit lint and format checks --------------------


def test_c019_passes_when_the_hooks_report_nothing_the_base_did_not(corpus):
    """The satisfying case: the hooks' own verdict, base-subtracted, is clean."""
    bundle = make_bundle(files=[VALID], lint={"ruff": LintReport(
        shape="report", tool="ruff", n_findings_base=7)})
    assert verdict("PALLETS-C019", bundle, corpus).verdict == "pass"


def test_c019_fails_on_a_finding_the_base_commit_did_not_carry(corpus):
    bundle = make_bundle(files=[VALID], lint={"ruff": LintReport(
        shape="report", tool="ruff",
        new_findings=(Finding("src/flask/app.py", "F401", "unused import"),))})
    row = verdict("PALLETS-C019", bundle, corpus)
    assert row.verdict == "fail" and "F401" in row.notes


def test_c019_fails_when_a_submitted_file_will_not_parse(corpus):
    row = verdict("PALLETS-C019", make_bundle(files=[BROKEN]), corpus)
    assert row.verdict == "fail" and "not valid Python" in row.notes


def test_c019_withholds_when_no_linter_was_run(corpus):
    """Never a silent pass: the row leaves both halves of the fraction and says why."""
    row = verdict("PALLETS-C019", make_bundle(files=[VALID]), corpus)
    assert row.verdict == "not_applicable" and row.status == "tool_missing"
    assert row.n_targets == 1


def test_c019_finds_no_target_for_a_documentation_only_contribution(corpus):
    row = verdict("PALLETS-C019", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
