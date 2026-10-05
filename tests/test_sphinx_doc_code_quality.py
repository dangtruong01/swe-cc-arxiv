"""Three cases per rule (docs/checker-authoring.md §9): one target that satisfies the pass
condition, one that violates it, and one input where the pre-condition finds nothing.

The third case catches a pre-condition written against the artefact the rule demands
instead of the antecedent that invokes it (§4.2). Do not skip it.

**C022 has no satisfying case, and that is not an omission.** It grades one-sidedly: a file
that will not parse fails, and everything else withholds, because no mypy run is collected.
Its third case is the withheld one.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

PY_PATH = "sphinx/util/inventory.py"
GOOD_PY = make_file(PY_PATH, [(1, "x = 1")], head_text="x = 1\n")
BROKEN_PY = make_file(PY_PATH, [(1, "def (")], head_text="def (\n")
RST = make_file("doc/usage/configuration.rst", [(1, "Some prose.")])


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def clean_ruff():
    return {"ruff": LintReport(shape="report", tool="ruff", n_findings_base=2)}


def dirty_ruff():
    return {"ruff": LintReport(
        shape="report", tool="ruff",
        new_findings=(Finding(PY_PATH, "E501", "line too long"),))}


# --- C020 ruff check ------------------------------------------------------------------


def test_c020_passes_when_ruff_reports_nothing_new(corpus):
    bundle = make_bundle(files=[GOOD_PY], lint=clean_ruff())
    assert verdict("SPHINX-DOC-C020", bundle, corpus).verdict == "pass"


def test_c020_fails_when_ruff_reports_a_new_finding(corpus):
    bundle = make_bundle(files=[GOOD_PY], lint=dirty_ruff())
    assert verdict("SPHINX-DOC-C020", bundle, corpus).verdict == "fail"


def test_c020_fails_on_a_submitted_file_that_does_not_parse(corpus):
    """Conclusive without any lint run: no linter accepts a syntax error."""
    bundle = make_bundle(files=[BROKEN_PY])
    assert verdict("SPHINX-DOC-C020", bundle, corpus).verdict == "fail"


def test_c020_finds_no_target_when_no_python_was_submitted(corpus):
    bundle = make_bundle(files=[RST])
    assert verdict("SPHINX-DOC-C020", bundle, corpus).verdict == "not_applicable"


# --- C021 ruff format -----------------------------------------------------------------


def test_c021_passes_on_lines_ruff_format_would_leave_alone(corpus):
    bundle = make_bundle(files=[make_file(PY_PATH, [(1, "x = 1"), (2, "y = 2")])])
    assert verdict("SPHINX-DOC-C021", bundle, corpus).verdict == "pass"


def test_c021_fails_on_trailing_whitespace(corpus):
    bundle = make_bundle(files=[make_file(PY_PATH, [(1, "x = 1   ")])])
    assert verdict("SPHINX-DOC-C021", bundle, corpus).verdict == "fail"


def test_c021_fails_on_tab_indentation(corpus):
    bundle = make_bundle(files=[make_file(PY_PATH, [(1, "\tx = 1")])])
    assert verdict("SPHINX-DOC-C021", bundle, corpus).verdict == "fail"


def test_c021_finds_no_target_when_no_python_line_was_written(corpus):
    bundle = make_bundle(files=[RST])
    assert verdict("SPHINX-DOC-C021", bundle, corpus).verdict == "not_applicable"


# --- C022 mypy ------------------------------------------------------------------------


def test_c022_fails_on_a_submitted_file_that_does_not_parse(corpus):
    bundle = make_bundle(files=[BROKEN_PY])
    assert verdict("SPHINX-DOC-C022", bundle, corpus).verdict == "fail"


def test_c022_withholds_when_no_type_check_was_run(corpus):
    """The rule applies; the bundle cannot answer it. Never a silent pass."""
    row = verdict("SPHINX-DOC-C022", make_bundle(files=[GOOD_PY]), corpus)
    assert row.verdict == "not_applicable"
    assert row.status != "ok"


def test_c022_finds_no_target_when_no_python_was_submitted(corpus):
    row = verdict("SPHINX-DOC-C022", make_bundle(files=[RST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
