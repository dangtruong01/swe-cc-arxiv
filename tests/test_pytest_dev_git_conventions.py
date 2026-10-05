"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.models import Command
from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])


def cmds(*items):
    return tuple(Command(index=i, command=c[0], output=(c[1] if len(c) > 1 else ""))
                 for i, c in enumerate(items))


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C031 commit only after tests pass ------------------------------------------------


def test_c031_passes_when_a_clean_run_precedes_the_commit(corpus):
    bundle = make_bundle(
        files=[SOURCE], commits=[make_commit("Fix the parser")],
        commands=cmds(("tox -e py313", "12 passed in 3.1s"), ("git commit -a -m x",)))
    assert verdict("PYTEST-DEV-C031", bundle, corpus).verdict == "pass"


def test_c031_fails_when_nothing_was_run_before_committing(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix the parser")],
                         commands=cmds(("git add .",), ("git commit -a -m x",)))
    assert verdict("PYTEST-DEV-C031", bundle, corpus).verdict == "fail"


def test_c031_fails_when_the_run_before_the_commit_failed(corpus):
    bundle = make_bundle(
        files=[SOURCE], commits=[make_commit("Fix the parser")],
        commands=cmds(("tox -e py313", "=== FAILURES ===\n1 failed"),
                      ("git commit -a -m x",)))
    assert verdict("PYTEST-DEV-C031", bundle, corpus).verdict == "fail"


def test_c031_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PYTEST-DEV-C031",
                  make_bundle(files=[SOURCE], commands=cmds(("tox",))), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C036 autoclose keyword -----------------------------------------------------------


def test_c036_passes_when_the_commit_closes_an_issue(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("Fix the parser\n\ncloses #2574")])
    assert verdict("PYTEST-DEV-C036", bundle, corpus).verdict == "pass"


def test_c036_passes_when_the_pull_request_text_carries_it(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix the parser")],
                         pr_text="This fixes #2574 in the parser.")
    assert verdict("PYTEST-DEV-C036", bundle, corpus).verdict == "pass"


def test_c036_fails_when_neither_carries_it(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix the parser")],
                         pr_text="Tidies the parser.")
    assert verdict("PYTEST-DEV-C036", bundle, corpus).verdict == "fail"


def test_c036_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PYTEST-DEV-C036", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
