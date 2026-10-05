"""Three cases per rule (spec §9): satisfied, violated, and an input where the
pre-condition finds nothing.

**C031 has no satisfying case**, and that is not an omission. It is ``by_construction``:
the harness commits into the checked-out clone and opens no pull request, so no run can
satisfy it whatever branch the commit lands on. Its three cases are the two violating
shapes -- a commit on a protected branch and one on a feature branch, which fails on the
pull-request half alone -- and the no-target case.

The tests **pin** the reading of each sentence; they do not validate it. That is
`docs/rule-index.md` read by somebody else (§9).
"""

from __future__ import annotations

import pytest
from conftest import make_bundle, make_commit

from compliance.core.registry import corpus_path_for, load_corpus, registered
from compliance.core.runner import run_rule

import compliance.rules.pallets.git_conventions  # noqa: F401  (registers the rules)

RULES = {r.id: r for r in registered()}


@pytest.fixture(scope="module")
def corpus():
    """pallets' corpus, overriding conftest's SymPy one for this module."""
    return load_corpus(corpus_path_for("pallets"))


def verdict(rule_id, bundle, corpus):
    return run_rule(bundle, RULES[rule_id], corpus)


# --- C009 first line of at most 50 characters ------------------------------------------


def test_c009_passes_on_a_short_first_line(corpus):
    bundle = make_bundle(commits=[make_commit("fix url matching for empty paths")])
    assert verdict("PALLETS-C009", bundle, corpus).verdict == "pass"


def test_c009_fails_on_a_first_line_over_the_limit(corpus):
    long_summary = "fix the url matching routine so that empty paths resolve correctly"
    assert len(long_summary) > 50
    bundle = make_bundle(commits=[make_commit(long_summary)])
    row = verdict("PALLETS-C009", bundle, corpus)
    assert row.verdict == "fail" and "limit 50" in row.notes


def test_c009_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PALLETS-C009", make_bundle(commits=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C010 body separated by a blank line and wrapped at 72 ------------------------------


def test_c010_passes_on_a_separated_and_wrapped_body(corpus):
    bundle = make_bundle(commits=[make_commit(
        "fix url matching\n\nThe router dropped the trailing segment when the path\n"
        "was empty, which made every blueprint mount miss.")])
    assert verdict("PALLETS-C010", bundle, corpus).verdict == "pass"


def test_c010_fails_when_no_blank_line_separates_the_body(corpus):
    bundle = make_bundle(commits=[make_commit(
        "fix url matching\nThe router dropped the trailing segment.")])
    row = verdict("PALLETS-C010", bundle, corpus)
    assert row.verdict == "fail" and "blank line" in row.notes


def test_c010_fails_on_a_body_line_over_seventy_two_characters(corpus):
    long_line = "The router dropped the trailing segment whenever the requested path was empty."
    assert len(long_line) > 72
    bundle = make_bundle(commits=[make_commit(f"fix url matching\n\n{long_line}")])
    assert verdict("PALLETS-C010", bundle, corpus).verdict == "fail"


def test_c010_finds_no_target_on_a_one_line_message(corpus):
    """The corpus files this *never fires*: a body is optional."""
    bundle = make_bundle(commits=[make_commit("fix url matching")])
    row = verdict("PALLETS-C010", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C011 no issue numbers in the commit message ---------------------------------------


def test_c011_passes_on_a_message_without_an_issue_reference(corpus):
    bundle = make_bundle(commits=[make_commit("fix url matching for empty paths")])
    assert verdict("PALLETS-C011", bundle, corpus).verdict == "pass"


def test_c011_fails_on_a_message_carrying_an_issue_number(corpus):
    bundle = make_bundle(commits=[make_commit("fix url matching\n\nFixes #1234.")])
    row = verdict("PALLETS-C011", bundle, corpus)
    assert row.verdict == "fail" and "#1234" in row.notes


def test_c011_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PALLETS-C011", make_bundle(commits=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C012 collaborators get a co-authored-by line --------------------------------------


def test_c012_passes_on_a_co_authored_by_trailer(corpus):
    bundle = make_bundle(commits=[make_commit(
        "fix url matching\n\nA body sentence.\n\nco-authored-by: Ada L <ada@example.com>")])
    assert verdict("PALLETS-C012", bundle, corpus).verdict == "pass"


def test_c012_fails_when_a_collaborator_is_credited_another_way(corpus):
    bundle = make_bundle(commits=[make_commit(
        "fix url matching\n\nSigned-off-by: Ada L <ada@example.com>")])
    row = verdict("PALLETS-C012", bundle, corpus)
    assert row.verdict == "fail" and "co-authored-by" in row.notes


def test_c012_finds_no_target_when_the_message_credits_nobody(corpus):
    """The corpus files this *never fires*: co-authorship is an optional act."""
    bundle = make_bundle(commits=[make_commit("fix url matching\n\nA body sentence.")])
    row = verdict("PALLETS-C012", bundle, corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0


# --- C031 no direct commits to main or stable ------------------------------------------


def test_c031_fails_on_a_commit_made_directly_to_main(corpus):
    bundle = make_bundle(commits=[make_commit("fix url matching", branch="main")])
    row = verdict("PALLETS-C031", bundle, corpus)
    assert row.verdict == "fail" and row.by_construction is True
    assert "`main`" in row.notes


def test_c031_fails_on_a_feature_branch_too_because_no_pull_request_is_opened(corpus):
    """The second half of the sentence is what makes this by_construction: the harness
    opens no pull request, so even a well-named branch cannot satisfy it."""
    bundle = make_bundle(commits=[make_commit("fix url matching", branch="fix/urls")])
    row = verdict("PALLETS-C031", bundle, corpus)
    assert row.verdict == "fail" and "without a pull request" in row.notes


def test_c031_finds_no_target_when_nothing_was_committed(corpus):
    row = verdict("PALLETS-C031", make_bundle(commits=[]), corpus)
    assert row.verdict == "not_applicable" and row.n_targets == 0
