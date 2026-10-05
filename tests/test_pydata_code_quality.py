"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C040 has no satisfying case: it grades one-sidedly, failing on a file that cannot parse and
withholding otherwise, because no mypy run is collected. Its third case is the withheld one.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pydata.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
PY_PATH = "xarray/core/dataset.py"
GOOD_PY = make_file(PY_PATH, [(1, "x = 1")], head_text="x = 1\n")
BROKEN_PY = make_file(PY_PATH, [(1, "def (")], head_text="def (\n")
RST = make_file("doc/whats-new.rst", [(1, "- prose")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


@pytest.fixture(scope="module")
def corpus():
    """pydata's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pydata"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C037 ruff format -----------------------------------------------------------------


def test_c037_passes_on_lines_the_formatter_would_leave_alone(corpus):
    bundle = make_bundle(files=[make_file(PY_PATH, [(1, "x = 1"), (2, "y = 2")])])
    assert verdict("PYDATA-C037", bundle, corpus).verdict == "pass"


def test_c037_fails_on_trailing_whitespace(corpus):
    bundle = make_bundle(files=[make_file(PY_PATH, [(1, "x = 1   ")])])
    assert verdict("PYDATA-C037", bundle, corpus).verdict == "fail"


def test_c037_finds_no_target_when_no_python_line_was_written(corpus):
    row = verdict("PYDATA-C037", make_bundle(files=[RST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C038 ruff lint -------------------------------------------------------------------


def test_c038_passes_when_ruff_reports_nothing_new(corpus):
    bundle = make_bundle(files=[GOOD_PY],
                         lint={"ruff": LintReport(shape="report", tool="ruff",
                                                  n_findings_base=2)})
    assert verdict("PYDATA-C038", bundle, corpus).verdict == "pass"


def test_c038_fails_on_a_new_finding(corpus):
    bundle = make_bundle(files=[GOOD_PY], lint={"ruff": LintReport(
        shape="report", tool="ruff",
        new_findings=(Finding(PY_PATH, "F401", "unused import"),))})
    assert verdict("PYDATA-C038", bundle, corpus).verdict == "fail"


def test_c038_fails_on_a_file_that_does_not_parse(corpus):
    assert verdict("PYDATA-C038", make_bundle(files=[BROKEN_PY]), corpus).verdict == "fail"


def test_c038_finds_no_target_without_python(corpus):
    row = verdict("PYDATA-C038", make_bundle(files=[RST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C040 mypy ------------------------------------------------------------------------


def test_c040_fails_on_a_file_that_does_not_parse(corpus):
    assert verdict("PYDATA-C040", make_bundle(files=[BROKEN_PY]), corpus).verdict == "fail"


def test_c040_withholds_when_no_type_check_ran(corpus):
    row = verdict("PYDATA-C040", make_bundle(files=[GOOD_PY]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c040_finds_no_target_without_python(corpus):
    row = verdict("PYDATA-C040", make_bundle(files=[RST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C091 pre-commit over all files ---------------------------------------------------


def test_c091_passes_on_the_all_files_form(corpus):
    bundle = make_bundle(files=[GOOD_PY], commands=cmds("pre-commit run --all-files"))
    assert verdict("PYDATA-C091", bundle, corpus).verdict == "pass"


def test_c091_fails_on_a_staged_files_run(corpus):
    bundle = make_bundle(files=[GOOD_PY], commands=cmds("pre-commit run"))
    assert verdict("PYDATA-C091", bundle, corpus).verdict == "fail"


def test_c091_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYDATA-C091",
                  make_bundle(files=[], commands=cmds("pre-commit run --all-files")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
