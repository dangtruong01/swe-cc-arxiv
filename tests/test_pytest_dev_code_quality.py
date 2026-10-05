"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

C018 carries a fourth: a run of the test environments alone must not satisfy it, or the
coding-style half of `tox -e linting,py313` would be scored by C017 twice.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.code_quality  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])


def cmds(*commands):
    return tuple(Command(index=i, command=c) for i, c in enumerate(commands))


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C015 pre-commit installed --------------------------------------------------------


def test_c015_passes_when_pre_commit_was_installed(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pre-commit install"))
    assert verdict("PYTEST-DEV-C015", bundle, corpus).verdict == "pass"


def test_c015_fails_when_it_was_never_installed(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("pip install -e ."))
    assert verdict("PYTEST-DEV-C015", bundle, corpus).verdict == "fail"


def test_c015_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYTEST-DEV-C015",
                  make_bundle(files=[], commands=cmds("pre-commit install")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C018 the linting environment ran -------------------------------------------------


def test_c018_passes_on_the_combined_invocation(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("tox -e linting,py313"))
    assert verdict("PYTEST-DEV-C018", bundle, corpus).verdict == "pass"


def test_c018_fails_when_only_the_test_environments_ran(corpus):
    bundle = make_bundle(files=[SOURCE], commands=cmds("tox -e py313"))
    assert verdict("PYTEST-DEV-C018", bundle, corpus).verdict == "fail"


def test_c018_finds_no_target_for_an_empty_contribution(corpus):
    row = verdict("PYTEST-DEV-C018",
                  make_bundle(files=[], commands=cmds("tox -e linting")), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
