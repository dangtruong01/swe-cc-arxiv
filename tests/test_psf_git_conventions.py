"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C024 the commit message explains why ---------------------------------------------


def test_c024_passes_when_the_message_says_more_than_the_issue(corpus):
    commit = make_commit(
        "Preserve the Authorization header across same-host redirects\n"
        "\n"
        "Stripping it broke proxied auth; scoping the strip to cross-host\n"
        "redirects was ruled out as too permissive.\n"
        "\n"
        "Fixes #5678")
    assert verdict("PSF-C024", make_bundle(commits=[commit]), corpus).verdict == "pass"


def test_c024_fails_on_a_message_that_is_only_an_issue_reference(corpus):
    row = verdict("PSF-C024", make_bundle(commits=[make_commit("Fixes #5678")]), corpus)
    assert row.verdict == "fail"


def test_c024_finds_no_target_when_the_agent_made_no_commit(corpus):
    row = verdict("PSF-C024", make_bundle(commits=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
