"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C002 is a **one-sidedly graded** rule wherever no `ruff` report was stored, so it gets the
alternative triple as well: it fails on the evidence the published configuration settles by
itself, withholds on everything else -- asserted below as `not_applicable` with a non-`ok`
status, never a silent pass -- and finds no target when the configuration's own
`extend-exclude` puts the changed file outside it.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.lint import Finding, LintReport
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.mwaskom.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
PY_PATH = "seaborn/_core/plot.py"
GOOD_PY = make_file(PY_PATH, [(1, "x = 1")], head_text="x = 1\n")
BROKEN_PY = make_file(PY_PATH, [(1, "def (")], head_text="def (\n")
# 92 characters: over `line-length = 88`, and breakable, so certainly an E501.
LONG_LINE = "    value = " + " + ".join(["variable"] * 8) + "  # x"
RST = make_file("doc/whatsnew/v0.13.0.rst", [(1, "- prose")])


@pytest.fixture(scope="module")
def corpus():
    """seaborn's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("mwaskom"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C002 changed Python satisfies the ruff configuration -----------------------------


def test_c002_passes_when_the_stored_ruff_report_is_clean(corpus):
    bundle = make_bundle(files=[GOOD_PY],
                         lint={"ruff": LintReport(shape="report", tool="ruff",
                                                  n_findings_base=7)})
    assert verdict("MWASKOM-C002", bundle, corpus).verdict == "pass"


def test_c002_fails_on_a_finding_the_base_commit_did_not_have(corpus):
    bundle = make_bundle(files=[GOOD_PY], lint={"ruff": LintReport(
        shape="report", tool="ruff",
        new_findings=(Finding(PY_PATH, "F401", "unused import"),))})
    assert verdict("MWASKOM-C002", bundle, corpus).verdict == "fail"


def test_c002_fails_on_a_written_line_over_the_configured_length(corpus):
    """`line-length = 88` with `select = ["E"]` is E501, decidable without the tool."""
    assert len(LONG_LINE) > 88
    bundle = make_bundle(files=[make_file(PY_PATH, [(3, LONG_LINE)],
                                          head_text=LONG_LINE + "\n")])
    assert verdict("MWASKOM-C002", bundle, corpus).verdict == "fail"


def test_c002_fails_on_a_file_that_does_not_parse(corpus):
    assert verdict("MWASKOM-C002", make_bundle(files=[BROKEN_PY]), corpus).verdict == "fail"


def test_c002_withholds_when_nothing_conclusive_and_no_ruff_ran(corpus):
    row = verdict("MWASKOM-C002", make_bundle(files=[GOOD_PY]), corpus)
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c002_withholds_on_a_file_the_stored_report_did_not_cover(corpus):
    """`make lint` runs ruff over `seaborn/ tests/` only. A report scoped that way must not
    be read as clearing a file it never looked at."""
    bundle = make_bundle(files=[make_file("doc/conf.py", [(1, "x = 1")], head_text="x = 1\n")],
                         lint={"ruff": LintReport(shape="report", tool="ruff",
                                                  files=("seaborn/_core/plot.py",))})
    row = verdict("MWASKOM-C002", bundle, corpus)
    assert row.n_targets == 1
    assert row.verdict == "not_applicable" and row.status != "ok"


def test_c002_finds_no_target_in_a_path_the_ruff_config_excludes(corpus):
    """`extend-exclude = ["seaborn/cm.py", "seaborn/external"]` is part of the
    configuration the rule points at, so a vendored file is outside the antecedent."""
    bundle = make_bundle(files=[make_file("seaborn/external/husl.py", [(1, LONG_LINE)],
                                          head_text=LONG_LINE + "\n")])
    row = verdict("MWASKOM-C002", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c002_finds_no_target_when_no_python_changed(corpus):
    row = verdict("MWASKOM-C002", make_bundle(files=[RST]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
