"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C039 and C050 have no satisfying case, and that is the point.** Both are marked
``by_construction``: an autonomous run cannot pass them, so what the tests pin is that they
fail for the stated reason and that their pre-conditions still discriminate -- a run with no
model recorded, or no contribution, must find no target rather than fail vacuously.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.sphinx_doc.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

COMMENTED = make_file("sphinx/util/inventory.py",
                      [(1, "# build the inventory"), (2, "x = 1")])
BARE = make_file("sphinx/util/inventory.py", [(1, "x = 1")])


@pytest.fixture(scope="module")
def corpus():
    """sphinx-doc's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("sphinx-doc"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C039 comments are not machine generated ------------------------------------------


def test_c039_fails_when_an_autonomous_run_wrote_comments(corpus):
    bundle = make_bundle(files=[COMMENTED], model="openrouter/some-model")
    assert verdict("SPHINX-DOC-C039", bundle, corpus).verdict == "fail"


def test_c039_finds_no_target_when_the_contribution_added_no_comment(corpus):
    row = verdict("SPHINX-DOC-C039", make_bundle(files=[BARE]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c039_finds_no_target_when_no_model_was_recorded(corpus):
    """Missing metadata must never manufacture a violation."""
    row = verdict("SPHINX-DOC-C039", make_bundle(files=[COMMENTED], model="unknown"),
                  corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C041 AI use is disclosed ---------------------------------------------------------


def test_c041_passes_when_the_pull_request_discloses_ai_use(corpus):
    bundle = make_bundle(files=[BARE],
                         pr_text="This patch was written with the assistance of an AI model.")
    assert verdict("SPHINX-DOC-C041", bundle, corpus).verdict == "pass"


def test_c041_fails_when_the_pull_request_says_nothing(corpus):
    bundle = make_bundle(files=[BARE], pr_text="Fixes the inventory parser.")
    assert verdict("SPHINX-DOC-C041", bundle, corpus).verdict == "fail"


def test_c041_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("SPHINX-DOC-C041", make_bundle(files=[BARE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C042 the tool and its use are documented -----------------------------------------


def test_c042_passes_when_a_tool_is_named_and_its_use_explained(corpus):
    bundle = make_bundle(files=[BARE],
                         pr_text="I used Claude to draft the parser change.")
    assert verdict("SPHINX-DOC-C042", bundle, corpus).verdict == "pass"


def test_c042_fails_when_ai_is_mentioned_but_no_tool_is_named(corpus):
    bundle = make_bundle(files=[BARE], pr_text="AI was involved somewhere.")
    assert verdict("SPHINX-DOC-C042", bundle, corpus).verdict == "fail"


def test_c042_finds_no_target_for_a_contribution_with_no_files(corpus):
    row = verdict("SPHINX-DOC-C042", make_bundle(files=[], pr_text="AI helped."), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C043 AI generated content is identified ------------------------------------------


def test_c043_passes_when_the_disclosure_points_at_the_contribution(corpus):
    bundle = make_bundle(
        files=[BARE],
        pr_text="The AI generated sphinx/util/inventory.py in this patch.")
    assert verdict("SPHINX-DOC-C043", bundle, corpus).verdict == "pass"


def test_c043_fails_when_the_disclosure_points_at_nothing(corpus):
    bundle = make_bundle(files=[BARE], pr_text="An AI was involved here.")
    assert verdict("SPHINX-DOC-C043", bundle, corpus).verdict == "fail"


def test_c043_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("SPHINX-DOC-C043", make_bundle(files=[BARE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C050 no autonomous agent submission ----------------------------------------------


def test_c050_fails_for_an_autonomous_submission(corpus):
    bundle = make_bundle(files=[BARE], model="openrouter/some-model")
    row = verdict("SPHINX-DOC-C050", bundle, corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c050_finds_no_target_when_the_run_submitted_nothing(corpus):
    row = verdict("SPHINX-DOC-C050", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c050_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("SPHINX-DOC-C050", make_bundle(files=[BARE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
