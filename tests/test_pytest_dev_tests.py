"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

pytest keeps its tests under `testing/`, so the fixtures below do too.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.tests  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])
TEST_FILE = make_file("testing/test_fixtures.py", [(1, "def test_a(): pass")])
DOC = make_file("doc/en/reference.rst", [(1, "Reference")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C017 the suite is run through tox ------------------------------------------------


def test_c017_passes_when_tox_ran(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("tox -e linting,py313"))
    assert verdict("PYTEST-DEV-C017", bundle, corpus).verdict == "pass"


def test_c017_fails_when_the_suite_was_never_run_through_tox(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("python -m pytest testing/"))
    assert verdict("PYTEST-DEV-C017", bundle, corpus).verdict == "fail"


def test_c017_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYTEST-DEV-C017", make_bundle(files=[], commands=cmds("tox")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C058 tests included or updated ---------------------------------------------------


def test_c058_passes_when_testing_changed_alongside_the_code(corpus):
    assert verdict("PYTEST-DEV-C058", make_bundle(files=[SOURCE, TEST_FILE]),
                   corpus).verdict == "pass"


def test_c058_fails_when_source_changed_alone(corpus):
    assert verdict("PYTEST-DEV-C058", make_bundle(files=[SOURCE]),
                   corpus).verdict == "fail"


def test_c058_finds_no_target_for_a_documentation_only_change(corpus):
    row = verdict("PYTEST-DEV-C058", make_bundle(files=[DOC]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
