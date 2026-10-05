"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C009 has no satisfying case, and that is the point.** It is ``by_construction``: an
autonomous run cannot pass a rule that requires human review. What the tests pin is that it
fails for the stated reason and that its pre-condition still discriminates -- a run with no
model recorded, or no contribution, must find no target rather than fail vacuously.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pytest_dev.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("src/_pytest/fixtures.py", [(1, "x = 1")])


@pytest.fixture(scope="module")
def corpus():
    """pytest-dev's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pytest-dev"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C009 purely agentic contributions ------------------------------------------------


def test_c009_fails_for_an_autonomous_contribution(corpus):
    row = verdict("PYTEST-DEV-C009",
                  make_bundle(files=[SOURCE], model="openrouter/some-model"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c009_finds_no_target_when_the_run_submitted_nothing(corpus):
    row = verdict("PYTEST-DEV-C009", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c009_finds_no_target_when_no_model_was_recorded(corpus):
    """Missing metadata must never manufacture a violation."""
    row = verdict("PYTEST-DEV-C009", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C062 AI credited in Co-authored-by trailers --------------------------------------


def test_c062_passes_when_the_trailer_names_an_ai(corpus):
    commit = make_commit("Fix the parser\n\nCo-authored-by: Claude <noreply@anthropic.com>")
    bundle = make_bundle(files=[SOURCE], commits=[commit])
    assert verdict("PYTEST-DEV-C062", bundle, corpus).verdict == "pass"


def test_c062_fails_when_no_trailer_credits_anyone(corpus):
    bundle = make_bundle(files=[SOURCE], commits=[make_commit("Fix the parser")])
    assert verdict("PYTEST-DEV-C062", bundle, corpus).verdict == "fail"


def test_c062_fails_when_the_trailer_names_no_ai(corpus):
    commit = make_commit("Fix the parser\n\nCo-authored-by: Jane Roe <jane@example.com>")
    bundle = make_bundle(files=[SOURCE], commits=[commit])
    assert verdict("PYTEST-DEV-C062", bundle, corpus).verdict == "fail"


def test_c062_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PYTEST-DEV-C062", make_bundle(files=[SOURCE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
