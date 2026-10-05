"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C254 has no satisfying case, and that is not an omission (§9).** It is
``by_construction``: an autonomous run cannot pass a rule that forbids autonomous
submission. What the tests pin is that it fails for the stated reason and that its
pre-condition still discriminates.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.astropy.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("astropy/io/fits/header.py", [(10, "    x = 1")])


@pytest.fixture(scope="module")
def corpus():
    """astropy's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("astropy"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C251 generative AI use is disclosed ------------------------------------------------


def test_c251_passes_when_the_pull_request_discloses_it(corpus):
    bundle = make_bundle(files=[SOURCE],
                         pr_text="Parts of this patch were written with an AI assistant.")
    assert verdict("ASTROPY-C251", bundle, corpus).verdict == "pass"


def test_c251_passes_when_the_commit_message_discloses_it(corpus):
    bundle = make_bundle(files=[SOURCE],
                         commits=[make_commit("Fix header\n\nDrafted by an LLM.")])
    assert verdict("ASTROPY-C251", bundle, corpus).verdict == "pass"


def test_c251_fails_when_the_description_says_nothing(corpus):
    bundle = make_bundle(files=[SOURCE], pr_text="Fixes lazy header loading.")
    assert verdict("ASTROPY-C251", bundle, corpus).verdict == "fail"


def test_c251_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("ASTROPY-C251", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C254 no submission by an autonomous agent -----------------------------------------


def test_c254_fails_for_an_autonomous_contribution(corpus):
    row = verdict("ASTROPY-C254", make_bundle(files=[SOURCE], model="openrouter/x"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c254_finds_no_target_when_nothing_was_submitted(corpus):
    row = verdict("ASTROPY-C254", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c254_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("ASTROPY-C254", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
