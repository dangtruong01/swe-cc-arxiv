"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

The two rules split the fragment between them, and the no-target cases are what pin the
split: C006's antecedent is the *change*, so a documentation-only contribution finds no
target; C007's antecedent is the *fragment*, so a contribution that adds none does.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pylint_dev.pr_metadata  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
FRAGMENTS = "doc/whatsnew/fragments/"
SOURCE = make_file("pylint/checkers/typecheck.py", [(1, "x = 1")], head_text="x = 1")
DOC = make_file("doc/user_guide/usage.rst", [(1, "Usage")], head_text="Usage")


@pytest.fixture(scope="module")
def corpus():
    """pylint-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pylint-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


def fragment(name, text="Fixed a crash on empty input."):
    return make_file(FRAGMENTS + name, [(1, text)], head_text=text, is_new=True)


# --- C006 a news fragment named for the issue -----------------------------------------


def test_c006_passes_when_a_numbered_fragment_is_added(corpus):
    bundle = make_bundle(files=[SOURCE, fragment("1234.bugfix")])
    assert verdict("PYLINT-DEV-C006", bundle, corpus).verdict == "pass"


def test_c006_fails_when_the_change_ships_no_fragment(corpus):
    row = verdict("PYLINT-DEV-C006", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "fail" and "no news fragment" in row.notes


def test_c006_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PYLINT-DEV-C006", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C007 the fragment's type is one towncrier.toml declares --------------------------


def test_c007_passes_on_a_declared_fragment_type(corpus):
    bundle = make_bundle(files=[SOURCE, fragment("1234.false_positive")])
    assert verdict("PYLINT-DEV-C007", bundle, corpus).verdict == "pass"


def test_c007_fails_on_a_type_outside_the_declared_list(corpus):
    bundle = make_bundle(files=[SOURCE, fragment("1234.enhancement")])
    row = verdict("PYLINT-DEV-C007", bundle, corpus)
    assert row.verdict == "fail" and "enhancement" in row.notes


def test_c007_finds_no_target_when_no_fragment_is_added(corpus):
    row = verdict("PYLINT-DEV-C007", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
