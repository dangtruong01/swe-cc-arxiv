"""Three cases per rule (`docs/checker-authoring.md` §9): satisfied, violated, and an
input where the pre-condition finds nothing.

**C103 has no satisfying case, and that is not an omission (§9).** It is
``by_construction``: an autonomous run cannot pass a rule forbidding external AI tooling
from opening the pull request. Its three cases are violated plus two shapes of no-target,
which is what pins that the pre-condition still discriminates.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.matplotlib.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}
SOURCE = make_file("lib/matplotlib/axes/_axes.py", [(10, "    pass")])


@pytest.fixture(scope="module")
def corpus():
    """matplotlib's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("matplotlib"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C103 no direct interaction by external AI tooling ---------------------------------


def test_c103_fails_for_a_pull_request_opened_by_the_model(corpus):
    row = verdict("MATPLOTLIB-C103",
                  make_bundle(files=[SOURCE], model="openrouter/x",
                              pr_text="Fixes the tick locator."), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c103_finds_no_target_when_nothing_was_put_to_the_project(corpus):
    row = verdict("MATPLOTLIB-C103", make_bundle(files=[], pr_text=None), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c103_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("MATPLOTLIB-C103", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C268 AI use is disclosed in the pull-request description --------------------------


def test_c268_passes_when_the_description_says_ai_was_used_and_how(corpus):
    bundle = make_bundle(files=[SOURCE],
                         pr_text="AI Disclosure: this patch was drafted with an LLM.")
    assert verdict("MATPLOTLIB-C268", bundle, corpus).verdict == "pass"


def test_c268_fails_when_the_description_says_nothing_about_ai(corpus):
    bundle = make_bundle(files=[SOURCE], pr_text="Fixes the tick locator. Closes #1.")
    assert verdict("MATPLOTLIB-C268", bundle, corpus).verdict == "fail"


def test_c268_fails_when_there_is_no_description_at_all(corpus):
    assert verdict("MATPLOTLIB-C268", make_bundle(files=[SOURCE]),
                   corpus).verdict == "fail"


def test_c268_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("MATPLOTLIB-C268",
                  make_bundle(files=[SOURCE], model="unknown",
                              pr_text="No AI was used."), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
