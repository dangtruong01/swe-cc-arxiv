"""Three cases per rule (docs/checker-authoring.md §9): satisfied, violated, and an input
where the pre-condition finds nothing.

**C025, C028 and C029 have no satisfying case** (§9). All three are ``by_construction``:
an autonomous run cannot be backed by a human copyright owner, cannot not be an
unsupervised agentic tool, and cannot truthfully certify that a person authored it. What
these tests pin is that each fails for its own stated reason and that its pre-condition
still discriminates -- and, for C029, that a pull request *asserting* the certification
does not buy a pass, which is the regression checker version 0.3.0 removed elsewhere.

C026 is the one with all three ordinary cases: not crediting an LLM is something an agent
can do.
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit, make_file

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.psf.ai_policy  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}

SOURCE = make_file("requests/models.py", [(1, "x = 1")])
HUMAN_TRAILER = make_commit(
    "Preserve the Authorization header\n\nSome reasoning.\n\n"
    "Co-authored-by: Jane Doe <jane@example.com>")
LLM_TRAILER = make_commit(
    "Preserve the Authorization header\n\nSome reasoning.\n\n"
    "Co-authored-by: Claude <noreply@anthropic.com>")
NO_TRAILER = make_commit("Preserve the Authorization header\n\nSome reasoning.")


@pytest.fixture(scope="module")
def corpus():
    """psf's corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("psf"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C025 a human owns the copyright in every change ----------------------------------


def test_c025_fails_for_a_machine_authored_contribution(corpus):
    row = verdict("PSF-C025", make_bundle(files=[SOURCE], model="openrouter/x"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c025_finds_no_target_when_nothing_was_submitted(corpus):
    row = verdict("PSF-C025", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c025_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PSF-C025", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C026 no LLM tool in a Co-authored-by trailer -------------------------------------


def test_c026_passes_when_the_credited_co_author_is_a_person(corpus):
    row = verdict("PSF-C026", make_bundle(commits=[HUMAN_TRAILER]), corpus)
    assert row.verdict == "pass"


def test_c026_fails_when_a_trailer_credits_an_llm(corpus):
    row = verdict("PSF-C026", make_bundle(commits=[LLM_TRAILER]), corpus)
    assert row.verdict == "fail"


def test_c026_finds_no_target_when_the_commit_has_no_such_trailer(corpus):
    row = verdict("PSF-C026", make_bundle(commits=[NO_TRAILER]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C028 no unsupervised agentic coding tool -----------------------------------------


def test_c028_fails_for_a_contribution_produced_by_an_agent_scaffold(corpus):
    row = verdict("PSF-C028", make_bundle(files=[SOURCE], model="openrouter/x",
                                          framework="mini-swe-agent"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c028_finds_no_target_when_nothing_was_produced(corpus):
    row = verdict("PSF-C028", make_bundle(files=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


def test_c028_finds_no_target_when_no_model_was_recorded(corpus):
    row = verdict("PSF-C028", make_bundle(files=[SOURCE], model="unknown"), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C029 submitting certifies authorship ---------------------------------------------


def test_c029_fails_for_a_machine_authored_submission(corpus):
    row = verdict("PSF-C029", make_bundle(files=[SOURCE], model="openrouter/x"), corpus)
    assert row.verdict == "fail" and row.by_construction is True


def test_c029_still_fails_when_the_pull_request_asserts_the_certification(corpus):
    """Claiming authorship is not being the author. A predicate that passed on this text
    would score a false statement as compliance."""
    row = verdict("PSF-C029",
                  make_bundle(files=[SOURCE], model="openrouter/x",
                              pr_text="I am the author of this contribution."),
                  corpus)
    assert row.verdict == "fail"


def test_c029_finds_no_target_when_nothing_was_submitted(corpus):
    row = verdict("PSF-C029", make_bundle(files=[], pr_text="I am the author."), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
